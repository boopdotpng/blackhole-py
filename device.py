import atexit, collections, concurrent.futures, ctypes, math, mmap, struct, time
import numpy as np
import fw
from compiler.uop import DType, dtypes
from hw import isa
from pci import buffer_address, open_card

TAG_ENABLED_TENSIX_COL = 34
DRAM_BANK_SIZE, DRAM_PAGE_MAX = 0xFF000000, 4096
NOC_MAX_BURST = 0x4000

def coord(x:int, y:int) -> int: return y << 6 | x

def round_up(x:int, n:int) -> int: return -(-x // n) * n

def dram(offset:int, page:int=DRAM_PAGE_MAX, banks:int=8) -> int:
  if not (0 <= offset < banks * DRAM_BANK_SIZE and 64 <= page <= 16384 and page % 64 == 0):
    raise ValueError(f"invalid DRAM offset {offset} or page size {page}")
  tag = (page.bit_length() - 1) << 56 if page & (page - 1) == 0 else (page // 64 - 1) << 48
  return 1 << 63 | tag | offset

class Signal:
  # a u64 counter in pinned host memory that the device writes over PCIe
  def __init__(self, host, offset:int): self.mem, self.offset, self.addr = host.mem, offset, host.noc_addr + offset
  @property
  def value(self) -> int: return struct.unpack_from("<Q", self.mem, self.offset)[0]
  def wait(self, value:int, timeout:float=10.0):
    deadline = time.monotonic() + timeout
    while (v := self.value) < value:
      if time.monotonic() > deadline: raise TimeoutError(f"signal is {v}, waiting for {value}")

class DMA:
  # Copies through the DMA core: the host writes descriptors into a ring in its L1, and the core bumps `signal` in host
  # memory as each one completes. Buffers go zero-copy when they can be pinned, otherwise through two staging slots.
  COPY_THREADS = 4
  PIN_CHUNK, PIN_DEPTH = 64 << 20, 3

  def __init__(self, card, host, stage_base:int, stage_size:int):
    self.card, self.host, self.stage_base, self.stage_size = card, host, stage_base, stage_size
    self.signal, self.submitted, self.window = Signal(host, 0), 0, None
    self.slot, self.slot_done, self.pool = 0, [0, 0], None
    self.pending_pins = []  # still mapped after a DMA timeout; unpinned once the device catches up

  def submit(self, dst:int, src:int, size:int, timeout:float=60.0) -> int:
    # queue one copy between 64-aligned NoC addresses; returns the signal value that marks it done
    if dst % 64 or src % 64 or not 0 <= size < 1 << 32: raise ValueError("invalid DMA descriptor")
    value = self.submitted + 1
    self.signal.wait(max(0, value - fw.DMA_DEPTH), timeout)
    at = (fw.DMA_PACKETS + (value % fw.DMA_DEPTH) * fw.PACKET) // 4
    for i, word in enumerate((dst & 0xffffffff, dst >> 32, src & 0xffffffff, src >> 32, size, value >> 32)):
      self.window[at + i] = word
    self.window[fw.DMA_WPTR // 4] = value & 0xffffffff
    self.submitted = value
    return value

  def synchronize(self, timeout:float=10.0):
    self.signal.wait(self.submitted, timeout)
    self.release_pins()

  def release_pins(self, reset=False):
    if not self.pending_pins: return
    completed = self.signal.value
    while self.pending_pins and (reset or self.pending_pins[0][0] <= completed):
      _, va, size, view = self.pending_pins[0]
      self.card.unpin(va, size)
      view.release()
      self.pending_pins.pop(0)

  def close(self):
    self.release_pins(reset=True)
    if self.pool: self.pool.shutdown()

  def _staged(self, size:int, timeout:float):
    for off in range(0, size, self.stage_size):
      i, self.slot = self.slot, self.slot ^ 1
      self.signal.wait(self.slot_done[i], timeout)
      yield off, min(self.stage_size, size - off), self.stage_base + i * self.stage_size, i

  def _direct(self, dev_addr:int, host:memoryview, to_device:bool, timeout:float) -> bool:
    # Zero-copy DMA. Returns False (nothing copied) if the buffer is unaligned or unpinnable, so the caller stages it.
    page, n = mmap.PAGESIZE, len(host)
    if (va := buffer_address(host)) % 64: return False
    def copy(at:int, noc:int, size:int) -> int:
      d, h = dev_addr + (at - va), noc
      return self.submit(d, h, size, timeout) if to_device else self.submit(h, d, size, timeout)
    if n < self.PIN_CHUNK // 4 or not self.card.can_pin: return False
    # Pinning costs about as much as the DMA, so the next PIN_DEPTH chunks are pinned on the pool while one copies.
    chunks, at = [], va
    while at < va + n:
      stop, pin_va = min(va + n, at // page * page + self.PIN_CHUNK), at // page * page
      chunks.append((at, stop, pin_va, round_up(stop, page) - pin_va))
      at = stop
    pool, pin = self._pool(), lambda c: self.card.pin(c[2], c[3], read_only=to_device)
    pins = collections.deque((c, pool.submit(pin, c)) for c in chunks[:self.PIN_DEPTH])
    copying, unpins = collections.deque(), []
    def retire():
      c, val = copying[0]
      try: self.signal.wait(val, timeout)
      except BaseException:
        for chunk, value in copying:
          self.pending_pins.append((value, chunk[2], chunk[3], memoryview(host)))
        copying.clear()
        raise
      copying.popleft()
      unpins.append(pool.submit(self.card.unpin, c[2], c[3]))
    try:
      for k, c in enumerate(chunks):
        try: noc = pins.popleft()[1].result()
        except OSError:
          if k == 0: return False
          raise
        if k + self.PIN_DEPTH < len(chunks): pins.append((nxt := chunks[k + self.PIN_DEPTH], pool.submit(pin, nxt)))
        try: val = copy(c[0], noc + (c[0] - c[2]), c[1] - c[0])
        except BaseException:
          self.card.unpin(c[2], c[3])
          raise
        copying.append((c, val))
        if len(copying) > self.PIN_DEPTH: retire()
    finally:
      try:
        while copying: retire()
      finally:
        for c, f in pins:
          try: f.result()
          except OSError: continue
          unpins.append(pool.submit(self.card.unpin, c[2], c[3]))
        for f in unpins: f.result()
    return True

  def _pool(self) -> concurrent.futures.ThreadPoolExecutor:
    if self.pool is None: self.pool = concurrent.futures.ThreadPoolExecutor(self.COPY_THREADS)
    return self.pool

  def _memcpy(self, dst:int, src:int, n:int):
    part = round_up(-(-n // self.COPY_THREADS), 64)
    list(self._pool().map(lambda at: ctypes.memmove(dst + at, src + at, min(part, n - at)), range(0, n, part)))

  def copyin(self, dest:int, src, timeout:float=60.0):
    with memoryview(src).cast("B") as host:
      if self._direct(dest, host, True, timeout): return
      va = buffer_address(host)
      for off, n, buf, slot in self._staged(len(host), timeout):
        self._memcpy(self.host.addr + buf, va + off, n)
        self.slot_done[slot] = self.submit(dest + off, self.host.noc_addr + buf, n, timeout)
    self.synchronize(timeout)

  def copyout(self, dest, src:int, timeout:float=60.0):
    with memoryview(dest).cast("B") as host:
      if host.readonly: raise ValueError("copyout needs a writable buffer")
      if self._direct(src, host, False, timeout): return
      va = buffer_address(host)
      def drain(off, n, buf, val):
        self.signal.wait(val, timeout)
        self._memcpy(va + off, self.host.addr + buf, n)
      pending = None
      for off, n, buf, slot in self._staged(len(host), timeout):
        self.slot_done[slot] = val = self.submit(self.host.noc_addr + buf, src + off, n, timeout)
        if pending: drain(*pending)
        pending = off, n, buf, val
      if pending: drain(*pending)

class Buffer:
  def __init__(self, device: Device, shape, dtype: str | DType, host: bool = False, tiles_per_page: int = 1):
    self.device, self.shape, self.dtype, self.host = device, tuple(shape), dtypes.from_name(dtype), host
    if not self.dtype.host: raise ValueError(f"{self.dtype} has no host representation")
    self.numpy_type = np.dtype(self.dtype.host)
    self.nbytes = math.prod(self.shape) * self.numpy_type.itemsize
    if tiles_per_page < 1 or tiles_per_page * self.dtype.tile_bytes > NOC_MAX_BURST or (host and tiles_per_page != 1):
      raise ValueError("invalid tiles_per_page")
    if host:
      self.offset = device.alloc_host(max(self.nbytes, 64))
      self.addr = device.host.noc_addr + self.offset
    else:
      self.addr = device.alloc_dram(self.nbytes, tiles_per_page * self.dtype.tile_bytes)

  def numpy(self) -> np.ndarray:
    # Host buffers return a live view: no copy and no synchronization with the device.
    if self.host: return np.ndarray(self.shape, self.numpy_type, self.device.host.mem, self.offset)
    out = np.empty(self.shape, self.numpy_type)
    if self.nbytes: self.device.dma.copyout(out, self.addr)
    return out

  def copy_from(self, x):
    if self.host:
      self.numpy().reshape(-1).view(np.uint8)[:] = np.frombuffer(np.ascontiguousarray(x), np.uint8)
      return self
    data = memoryview(np.ascontiguousarray(x)).cast("B")
    if len(data) != self.nbytes: raise ValueError(f"{len(data)} bytes into a {self.nbytes}-byte buffer")
    self.device.dma.copyin(self.addr, data)
    return self

  def __repr__(self): return f"Buffer({self.shape}, {self.dtype}{', host' if self.host else ''})"

class Device:
  def __init__(self, index:int=0):
    self.card, self.host, self.booted, self.dma = open_card(index), None, False, None
    try:
      self.cols = (self.card.telemetry(TAG_ENABLED_TENSIX_COL) & 0x3FFF).bit_count()
      if self.cols not in (12, 14): raise RuntimeError(f"unsupported {self.card.name}: {self.cols} Tensix columns")
      self.dram_banks = 7 if self.card.name == "p100a" else 8
      right = 2 + self.cols
      self.dma_core, self.grid = (right, 11), ((1, 2), (right, 11))
      self.worker_rects = (((1, 2), (right - 1, 11)), ((right, 2), (right, 10)))
      self.workers = [(x, y) for x in range(1, right + 1) if x not in (8, 9) for y in range(2, 12) if (x, y) != self.dma_core]
      self._reset(self.grid)
      self.booted = True
      # Host memory: [signal page | heap for host buffers | 2 DMA staging slots | unused 32 MiB tail]. DMA from the
      # last 16 MiB of a pin runs at ~33 GB/s instead of ~56 (cause unknown), so nothing lives there.
      stage_base, stage_size = 16 << 20, 8 << 20
      self.host = self.card.alloc_host(stage_base + 2 * stage_size + (32 << 20))
      self.heap, self.heap_end, self.dram_top = mmap.PAGESIZE, stage_base, 0
      self.dma = DMA(self.card, self.host, stage_base, stage_size)
      self._boot_dma()
    except BaseException:
      self.close()
      raise
    atexit.register(self.close)

  def empty(self, shape, dtype:str|DType, host:bool=False, *, tiles_per_page:int=1) -> Buffer:
    return Buffer(self, (shape,) if isinstance(shape, int) else shape, dtype, host, tiles_per_page)

  def zeros(self, shape, dtype:str|DType, host:bool=False) -> Buffer:
    b = self.empty(shape, dtype, host)
    if host:
      b.numpy().fill(0)
      return b
    chunk = bytes(min(b.nbytes, 16 << 20))
    for off in range(0, b.nbytes, len(chunk) or 1):
      self.dma.copyin(b.addr + off, memoryview(chunk)[:min(len(chunk), b.nbytes - off)])
    return b

  def array(self, x, dtype:str|DType|None=None) -> Buffer:
    x = np.asarray(x)
    dtype = None if dtype is None else dtypes.from_name(dtype)
    if dtype is dtypes.bf16 and x.dtype.kind == "f":
      u = x.astype(np.float32).view(np.uint32).astype(np.uint64)
      x = ((u + 0x7FFF + (u >> 16 & 1)) >> 16).astype(np.uint16)
    dtype = dtype or dtypes.from_host(x.dtype.name)
    if dtype is None: raise TypeError(f"no runtime type for {x.dtype}; pass dtype=")
    return self.empty(x.shape, dtype).copy_from(x)

  def read_l1(self, core:int|tuple[int, int], addr:int, size:int) -> bytes:
    return self.card.read(self.workers[core] if isinstance(core, int) else core, addr, size)

  def synchronize(self, timeout:float=10.0): self.dma.synchronize(timeout)

  def stop(self):
    for rect in self.worker_rects: self._reset(rect)

  def alloc_dram(self, size:int, page:int=DRAM_PAGE_MAX) -> int:
    # bump allocator; every allocation is interleaved page by page across all banks
    banks = self.dram_banks
    offset = round_up(self.dram_top, banks * page)
    end = round_up(offset + round_up(size, banks * page), banks * DRAM_PAGE_MAX)
    if size < 0 or end > banks * DRAM_BANK_SIZE: raise MemoryError(f"can't allocate {size} bytes of DRAM")
    self.dram_top = end
    return dram(offset, page, banks)

  def alloc_host(self, size:int, align:int=64) -> int:
    offset = round_up(self.heap, align)
    if offset + size > self.heap_end: raise MemoryError(f"host heap is full: {size} bytes requested")
    self.heap = offset + size
    return offset

  def run(self, images:dict[str, bytes], data:dict[int, bytes]|None=None, cores=None) -> int:
    # Launch one kernel body per RISC role on every worker (or `cores`), with `data` written to L1 first.
    # Returns the 64-aligned end of code in L1.
    image, role_pcs, code_end = fw.pack_megakernel(images)
    self.synchronize()
    self.stop()
    header = bytearray(fw.CODE_BASE)
    struct.pack_into("<I", header, 0, isa.jal(imm=fw.CODE_BASE))
    struct.pack_into("<I", header, fw.LEADER_COORD, coord(*self.workers[0]))
    struct.pack_into("<3I", header, fw.NUM_WORKERS, len(self.workers), self.dram_banks, self.cols)
    struct.pack_into("<4I", header, fw.ROLE_PC, *(role_pcs.get(r, 0) for r in fw.ROLES[1:]))
    targets = self.worker_rects if cores is None else list(cores)
    payload = bytes(header) + image
    for target in targets:
      self.card.write(target, 0, payload)
      if data:
        for addr, blob in data.items(): self.card.write(target, addr, blob)
      self.card.write32(target, fw.SOFT_RESET, fw.RESET_ALL & ~fw.RESET_BRISC)
    return code_end

  def close(self):
    if self.card is None: return
    try:
      if self.booted: self._reset(self.grid)
      if self.dma: self.dma.close()
      if self.host is not None: self.host.close()
    finally:
      self.card.close()
      self.card = None

  def _reset(self, rect): self.card.write32(rect, fw.SOFT_RESET, fw.RESET_ALL)

  def _boot_dma(self):
    core, (brisc, ncrisc) = self.dma_core, fw.dma_images(self.dram_banks)
    state = bytearray(fw.DMA_STATE_SIZE)
    struct.pack_into("<Q", state, fw.DMA_SIGNAL - fw.DMA_STATE, self.dma.signal.addr)
    self.card.write(core, fw.DMA_STATE, state)
    self.card.write(core, fw.DMA_BRISC_BASE, brisc)
    self.card.write(core, fw.DMA_NCRISC_BASE, ncrisc)
    self.card.write32(core, 0, isa.jal(imm=fw.DMA_BRISC_BASE))
    self.card.write32(core, fw.SOFT_RESET, fw.RESET_ALL & ~fw.RESET_BRISC)
    self.dma.window = self.card.window(core)
