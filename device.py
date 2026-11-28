from __future__ import annotations

import atexit, collections, concurrent.futures, ctypes, math, mmap, struct, time
import numpy as np
import fw
from compiler.uop import DType, dtypes
from hw import isa
from pci import buffer_address, open_card

TAG_ENABLED_TENSIX_COL = 34
DRAM_BANK_SIZE, DRAM_PAGE_MAX = 0xFF000000, 4096
NOC_MAX_BURST = 0x4000
HOST_DTYPES = {dtypes.bool: "bool", dtypes.u8: "uint8", dtypes.i32: "int32", dtypes.u32: "uint32",
               dtypes.u64: "uint64", dtypes.bf16: "uint16", dtypes.fp32: "float32",
               dtypes.bfp8: "uint8", dtypes.bfp4: "uint8", dtypes.e4m3: "uint8"}

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
  def __init__(self, device: Device, shape, dtype: str | DType, host: bool = False, page: int = DRAM_PAGE_MAX):
    self.device, self.shape, self.dtype, self.host = device, tuple(shape), dtypes.from_name(dtype), host
    if self.dtype not in HOST_DTYPES: raise ValueError(f"{self.dtype} has no host representation")
    if self.dtype in (dtypes.bfp8, dtypes.bfp4): raise ValueError(f"{self.dtype} requires FaceBuffer")
    self.numpy_type = np.dtype(HOST_DTYPES[self.dtype])
    self.nbytes = math.prod(self.shape) * self.numpy_type.itemsize
    if not 64 <= page <= NOC_MAX_BURST or page % 64: raise ValueError("invalid DRAM page size")
    if host:
      self.offset = device.alloc_host(max(self.nbytes, 64))
      self.addr = device.host.noc_addr + self.offset
    else:
      self.addr = device.alloc_dram(self.nbytes, page)

  def numpy(self) -> np.ndarray:
    # Host buffers return a live view: no copy and no synchronization with the device.
    if self.host: return np.ndarray(self.shape, self.numpy_type, self.device.host.mem, self.offset)
    self.device.synchronize()
    out = np.empty(self.shape, self.numpy_type)
    if self.nbytes: self.device.dma.copyout(out, self.addr)
    return out

  def copy_from(self, x):
    self.device.synchronize()
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
    self._launch_layouts = {}
    try:
      self.cols = (self.card.telemetry(TAG_ENABLED_TENSIX_COL) & 0x3FFF).bit_count()
      if self.cols not in (12, 14): raise RuntimeError(f"unsupported {self.card.name}: {self.cols} Tensix columns")
      self.dram_banks = 7 if self.card.name == "p100a" else 8
      right = 2 + self.cols
      self.dma_core, self.cp_core, self.grid = (right, 11), (right, 10), ((1, 2), (right, 11))
      self.worker_rects = (((1, 2), (7, 11)), ((10, 2), (right - 1, 11)), ((right, 2), (right, 9)))
      self.workers = [(x, y) for x in range(1, right + 1) if x not in (8, 9) for y in range(2, 12)
                      if (x, y) not in (self.dma_core, self.cp_core)]
      self._reset(self.grid)
      self.booted = True
      # Host memory: [signal page | heap for host buffers/cmdbufs/progs | 2 DMA staging slots | unused 32 MiB tail].
      # DMA from the last 16 MiB of a pin runs at ~33 GB/s instead of ~56 (cause unknown), so nothing lives there.
      stage_base, stage_size = 16 << 20, 8 << 20
      self.host = self.card.alloc_host(stage_base + 2 * stage_size + (32 << 20))
      # NoC short writes require matching source/destination offsets within a 16-byte word.
      self.kernel_signal, self.kernel_sequence = Signal(self.host, 16), 0
      self.heap, self.heap_end, self.dram_top = mmap.PAGESIZE, stage_base, 0
      self.dram_limit = self.dram_banks * DRAM_BANK_SIZE
      self._arena_addr, self._arena_size, self._arena_gen = 0, 0, 0
      self._linked_schedules: dict = {}
      self.dma = DMA(self.card, self.host, stage_base, stage_size)
      self._prog_cache: dict[int, tuple[int, int]] = {}
      self._cp_window, self._cp_submitted = None, 0
      self._run_ring_off = self.alloc_host(fw.CP_DEPTH * (256 + 128), align=64)
      self._run_ring_seq = [0] * fw.CP_DEPTH
      self._boot_dma()
      self._boot_cp()
      self._boot_workers()
    except BaseException:
      self.close()
      raise
    atexit.register(self.close)

  def empty(self, shape, dtype:str|DType, host:bool=False, *, page:int=DRAM_PAGE_MAX) -> Buffer:
    return Buffer(self, (shape,) if isinstance(shape, int) else shape, dtype, host, page)

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
    dtype = dtype or {"bool": dtypes.bool, "uint8": dtypes.u8, "int32": dtypes.i32, "uint32": dtypes.u32,
                      "uint64": dtypes.u64, "float32": dtypes.fp32}.get(x.dtype.name)
    if dtype is None: raise TypeError(f"no runtime type for {x.dtype}; pass dtype=")
    return self.empty(x.shape, dtype).copy_from(x)

  def read_l1(self, core:int|tuple[int, int], addr:int, size:int) -> bytes:
    return self.card.read(self.workers[core] if isinstance(core, int) else core, addr, size)

  def worker_grid(self, gcols:int, grows:int) -> list[tuple[int, int]]:
    if not (1 <= gcols <= self.cols - 1 and 1 <= grows <= 10): raise ValueError("invalid worker grid")
    return [(wx + (3 if wx >= 7 else 1), wy + 2) for wx in range(gcols) for wy in range(grows)]

  def synchronize(self, timeout:float=10.0):
    self.dma.synchronize(timeout)
    self.kernel_signal.wait(self.kernel_sequence, timeout)

  def stop(self):
    for rect in self.worker_rects: self._reset(rect)

  def alloc_dram(self, size:int, page:int=DRAM_PAGE_MAX) -> int:
    # bump allocator; every allocation is interleaved page by page across all banks
    banks = self.dram_banks
    offset = round_up(self.dram_top, banks * page)
    end = round_up(offset + round_up(size, banks * page), banks * DRAM_PAGE_MAX)
    if size < 0 or end > self.dram_limit: raise MemoryError(f"can't allocate {size} bytes of DRAM")
    self.dram_top = end
    return dram(offset, page, banks)

  def ensure_arena(self, size:int, page:int=DRAM_PAGE_MAX) -> int:
    """Reusable transient DRAM arena carved from the top of DRAM so it never collides with persistent allocs."""
    if size <= 0: return 0
    if size <= self._arena_size: return self._arena_addr
    if self._arena_size: self.synchronize()
    banks = self.dram_banks
    aligned = round_up(size, banks * DRAM_PAGE_MAX)
    new_limit = (self.dram_banks * DRAM_BANK_SIZE - aligned) // (banks * DRAM_PAGE_MAX) * (banks * DRAM_PAGE_MAX)
    if new_limit < self.dram_top: raise MemoryError(f"can't allocate {size}-byte DRAM arena")
    self.dram_limit = new_limit
    self._arena_size = aligned
    self._arena_addr = dram(new_limit, page, banks)
    self._arena_gen += 1
    return self._arena_addr

  def alloc_host(self, size:int, align:int=64) -> int:
    offset = round_up(self.heap, align)
    if offset + size > self.heap_end: raise MemoryError(f"host heap is full: {size} bytes requested")
    self.heap = offset + size
    return offset

  def upload_program(self, images:dict[str, bytes], cb_mask:int=0xFFFFFFFF) -> tuple[int, int, int]:
    """Upload a packed kernel binary once to pinned host memory; CP caches it in worker L1."""
    blob, key = fw.pack_kernel(images, cb_mask)
    if key not in self._prog_cache:
      off = self.alloc_host(len(blob), align=64)
      self.host.mem[off:off + len(blob)] = blob
      self._prog_cache[key] = (self.host.noc_addr + off, len(blob))
    addr, nbytes = self._prog_cache[key]
    return addr, nbytes, key

  def submit_cp(self, cmdbuf_addr:int, cmdbuf_bytes:int, timeout:float=10.0) -> int:
    """Enqueue one Indirect Buffer (cmdbuf_addr, cmdbuf_bytes) on the Command Processor ring."""
    if cmdbuf_addr % 64 or cmdbuf_bytes % fw.CP_PKT_BYTES: raise ValueError("unaligned CP command buffer")
    seq = self._cp_submitted + 1
    deadline = time.monotonic() + timeout
    while seq - self._cp_window[fw.CP_RPTR // 4] > fw.CP_DEPTH:
      if time.monotonic() > deadline: raise TimeoutError("CP ring full")
    at = (fw.CP_RING + (seq % fw.CP_DEPTH) * fw.CP_IB_BYTES) // 4
    self._cp_window[at + 0] = cmdbuf_addr & 0xFFFFFFFF
    self._cp_window[at + 1] = cmdbuf_addr >> 32
    self._cp_window[at + 2] = cmdbuf_bytes
    self._cp_window[at + 3] = 0
    self._cp_window[fw.CP_WPTR // 4] = seq & 0xFFFFFFFF
    self._cp_submitted = seq
    return seq

  def _launch_layout(self, cores):
    targets = self.worker_rects if cores is None else tuple(cores)
    key = tuple(tuple(t) if isinstance(t[0], int) else (tuple(t[0]), tuple(t[1])) for t in targets)
    if key in self._launch_layouts: return self._launch_layouts[key]
    def covers(target, core):
      if isinstance(target[0], int): return tuple(target) == core
      (x0, y0), (x1, y1) = target
      return x0 <= core[0] <= x1 and y0 <= core[1] <= y1
    if all(isinstance(target[0], int) for target in targets):
      selected = {tuple(target) for target in targets}
      workers = [core for core in self.workers if core in selected]
    else:
      workers = [core for core in self.workers if any(covers(t, core) for t in targets)]
    if not workers: raise ValueError("kernel launch needs at least one worker")
    # Identical code and arguments can be multicast to rectangular runs of
    # selected cores. Keep every rectangle inside the requested worker set.
    rectangles, previous = [], {}
    for x in sorted({x for x, _ in workers}):
      ys = sorted(y for cx, y in workers if cx == x)
      runs = []
      for y in ys:
        if runs and runs[-1][1] + 1 == y: runs[-1] = (runs[-1][0], y)
        else: runs.append((y, y))
      for y0, y1 in runs:
        index = previous.get((y0, y1))
        if index is not None and rectangles[index][1][0] == x - 1:
          rectangles[index] = (rectangles[index][0], (x, y1))
        else:
          previous[y0, y1] = len(rectangles)
          rectangles.append(((x, y0), (x, y1)))
    self._launch_layouts[key] = workers, rectangles
    return workers, rectangles

  def run(self, images:dict[str, bytes], data:dict[int, bytes]|None=None, cores=None) -> int:
    # Single-kernel dispatch through the resident HCQ2 Command Processor (no SOFT_RESET,
    # no per-launch firmware/code upload on L1 cache hits). Preserves full compatibility
    # with tests passing arbitrary L1 `data={addr: blob}` staging blocks.
    from compiler.blackhole.hcq import pack_phys_rect
    workers, targets = self._launch_layout(cores)
    prog_addr, prog_bytes, prog_key = self.upload_program(images)

    arg_blob = b""
    extra = None
    if data:
      if list(data.keys()) == [fw.ARG_BASE] and len(data[fw.ARG_BASE]) <= 128:
        arg_blob = data[fw.ARG_BASE]
      else:
        extra = {}
        for addr, blob in data.items():
          if addr == fw.ARG_BASE and len(blob) <= 128: arg_blob = blob
          else: extra[addr] = blob
    if extra:
      self.synchronize()
      for target in targets:
        for addr, blob in extra.items(): self.card.write(target, addr, blob)

    slot = self.kernel_sequence % fw.CP_DEPTH
    if prev := self._run_ring_seq[slot]: self.kernel_signal.wait(prev)
    base_off = self._run_ring_off + slot * (256 + 128)
    cmd_off, args_off = base_off, base_off + 256
    args_addr, args_bytes = 0, 0
    if arg_blob:
      buf = bytearray(128)
      buf[:len(arg_blob)] = arg_blob
      self.host.mem[args_off:args_off + 128] = buf
      args_addr, args_bytes = self.host.noc_addr + args_off, 128

    rects = [pack_phys_rect(t) for t in targets]
    sequence = self.kernel_sequence + 1
    pkts = bytearray(128)
    struct.pack_into(
      "<16I", pkts, 0,
      fw.PKT_EXEC, fw.FLAG_CLEAR_MCAST,
      prog_addr & 0xFFFFFFFF, prog_addr >> 32,
      prog_bytes, prog_key & 0xFFFFFFFF,
      args_addr & 0xFFFFFFFF, args_addr >> 32,
      len(workers), (args_bytes << 8) | len(rects),
      *rects, *(0,) * (6 - len(rects)),
    )
    struct.pack_into(
      "<16I", pkts, 64,
      fw.PKT_SIGNAL, 0,
      self.kernel_signal.addr & 0xFFFFFFFF, self.kernel_signal.addr >> 32,
      sequence & 0xFFFFFFFF, sequence >> 32,
      *(0,) * 10,
    )
    self.host.mem[cmd_off:cmd_off + 128] = pkts
    self.kernel_sequence = sequence
    self._run_ring_seq[slot] = sequence
    self.submit_cp(self.host.noc_addr + cmd_off, 128)
    return fw.CODE_CACHE_BASE + prog_bytes - fw.PROG_HDR_BYTES

  def close(self):
    if self.card is None: return
    try:
      if self.booted: self._reset(self.grid)
      if self.dma: self.dma.close()
      if self.host is not None: self.host.close()
    finally:
      self.card.close()
      self.card = None

  def _reset(self, rect):
    # Reset source ownership while every RISC is held, avoiding the unsafe
    # asynchronous CLEARDVALID(reset=1) instruction in running Tensix code.
    self.card.write32(rect, fw.SOFT_RESET, fw.RESET_ALL | (1 << 15) | (1 << 16))

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

  def _boot_cp(self):
    from compiler.blackhole.hcq import pack_phys_rect
    core, image = self.cp_core, fw.cp_image(self.dram_banks)
    state = bytearray(fw.CP_STATE_SIZE)
    rects = [pack_phys_rect(r) for r in self.worker_rects]
    struct.pack_into("<I", state, fw.CP_ALL_NRECTS - fw.CP_STATE, len(rects))
    for i, r in enumerate(rects):
      struct.pack_into("<I", state, fw.CP_ALL_RECTS - fw.CP_STATE + 4 * i, r)
    self.card.write(core, fw.CP_STATE, state)
    self.card.write(core, fw.CP_BRISC_BASE, image)
    self.card.write32(core, 0, isa.jal(imm=fw.CP_BRISC_BASE))
    self.card.write32(core, fw.SOFT_RESET, fw.RESET_ALL & ~fw.RESET_BRISC)
    self._cp_window = self.card.window(core)
    deadline = time.monotonic() + 5.0
    while self._cp_window[fw.CP_READY // 4] != 1:
      if time.monotonic() > deadline: raise TimeoutError("CP core failed to boot")

  def _boot_workers(self):
    image, pcs = fw.worker_images(self.dram_banks)
    header = bytearray(fw.WORKER_FW_BASE)
    struct.pack_into("<I", header, 0, isa.jal(imm=pcs["brisc"]))
    struct.pack_into("<I", header, fw.LEADER_COORD, coord(*self.cp_core))
    struct.pack_into("<3I", header, fw.NUM_WORKERS, len(self.workers), self.dram_banks, self.cols)
    struct.pack_into("<4I", header, fw.ROLE_PC, *(pcs[r] for r in fw.ROLES[1:]))
    payload = bytes(header) + image
    for rect in self.worker_rects:
      self.card.write(rect, 0, payload)
    for rect in self.worker_rects:
      self.card.write32(rect, fw.SOFT_RESET, fw.RESET_ALL & ~fw.RESET_BRISC)
    deadline = time.monotonic() + 5.0
    for core in self.workers:
      while self.card.read32(core, fw.WORK_READY) != 1:
        if time.monotonic() > deadline: raise TimeoutError(f"worker {core} failed to boot")


class FaceBuffer:
  """Device tensor storage; pad/tilize and crop/untilize only at the host boundary."""
  def __init__(self, device, shape, dtype, rows=8, *, address=None):
    self.device, self.shape, self.dtype, self.rows = device, tuple(shape), dtype, rows
    self.packed = dtype in (dtypes.bfp8, dtypes.bfp4)
    if dtype not in (dtypes.fp32, dtypes.bf16, dtypes.i32, dtypes.u32, dtypes.bfp8, dtypes.bfp4):
      raise NotImplementedError(f"host face staging for {dtype}")
    if self.packed and rows != 16: raise NotImplementedError("packed activation staging")
    self.host_dtype = np.dtype(HOST_DTYPES[dtype])
    self.m, self.n = (1, 1) if not self.shape else (1, self.shape[0]) if len(self.shape) == 1 else self.shape[-2:]
    self.batch = math.prod(self.shape[:-2]) if len(self.shape) > 2 else 1
    self.mr, self.nc = round_up(self.m, rows) // rows, round_up(self.n, 16) // 16
    self.face_bytes = 16 + 256 * dtype.bits // 8 if self.packed else rows * 16 * self.host_dtype.itemsize
    self.nbytes = self.batch * self.mr * self.nc * self.face_bytes
    self.addr = device.alloc_dram(self.nbytes) if address is None else address

  def copy_from_raw(self, data):
    if self.packed: raise ValueError("packed tensors require packed checkpoint staging")
    values = np.frombuffer(data, self.host_dtype).reshape(self.batch, self.m, self.n)
    stage = np.zeros((self.batch, self.mr * self.rows, self.nc * 16), self.host_dtype)
    stage[:, :self.m, :self.n] = values
    faces = stage.reshape(self.batch, self.mr, self.rows, self.nc, 16).transpose(0, 1, 3, 2, 4)
    # Weight faces are consumed by MVMUL as [K_inner, N_inner]. This also
    # preserves the checkpoint's shared exponent groups without requantizing.
    if self.rows == 16: faces = faces.swapaxes(-1, -2)
    faces = faces.copy()
    self.device.dma.copyin(self.addr, faces)
    return self

  def copy_from_packed_kn(self, path, offset, shape):
    if not self.packed or self.shape != (shape[1] * 32, shape[0] * 32): raise ValueError("packed checkpoint shape mismatch")
    source = np.memmap(path, dtype=np.uint8, mode="r", offset=offset, shape=shape)
    mantissa_bytes = self.face_bytes - 16
    # Adapt the old on-disk envelope at the host boundary only. Exponents and
    # mantissas are copied verbatim into [N/16, K/16, 16x16 face bytes].
    for first in range(0, shape[1], 32):
      part = source[:, first:first + 32]
      exps = part[..., :64].reshape(shape[0], part.shape[1], 4, 16)
      mant = part[..., 64:].reshape(shape[0], part.shape[1], 4, mantissa_bytes)
      faces = np.concatenate((exps, mant), axis=-1).reshape(shape[0], part.shape[1], 2, 2, self.face_bytes)
      faces = faces.transpose(1, 3, 0, 2, 4).copy()
      self.device.dma.copyin(self.addr + first * 2 * self.nc * self.face_bytes, faces)
    return self

  def numpy(self):
    self.device.synchronize()
    if self.packed:
      raw = np.empty((self.batch, self.mr, self.nc, self.face_bytes), np.uint8)
      self.device.dma.copyout(raw, self.addr)
      code = raw[..., 16:]
      if self.dtype is dtypes.bfp4: code = np.stack((code & 15, code >> 4), axis=-1).reshape(*raw.shape[:-1], 256)
      code = code.reshape(*raw.shape[:-1], 16, 16)
      sign_bit = 1 << (self.dtype.bits - 1)
      magnitude = (code & (sign_bit - 1)).astype(np.float32)
      scale = np.exp2(raw[..., :16].astype(np.float32)[..., None] - 127 - (self.dtype.bits - 2))
      sign = np.where((code & sign_bit) != 0, np.float32(-1), np.float32(1))
      faces = sign * magnitude * scale
      faces = np.where(code == sign_bit, -np.inf, faces)
    else:
      faces = np.empty((self.batch, self.mr, self.nc, self.rows, 16), self.host_dtype)
      self.device.dma.copyout(faces, self.addr)
    if self.rows == 16: faces = faces.swapaxes(-1, -2)
    values = faces.transpose(0, 1, 3, 2, 4).reshape(self.batch, self.mr * self.rows, self.nc * 16)
    values = values[:, :self.m, :self.n].copy().reshape(self.shape)
    if self.dtype is dtypes.bf16: values = (values.astype(np.uint32) << 16).view(np.float32)
    return values
