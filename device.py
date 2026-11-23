import collections, concurrent.futures, ctypes, mmap, struct, sys, time
import fw
if sys.platform == "darwin": from pci_macos import Card, HostMemory
else: from pci import Card, HostMemory
from pci import buffer_address

def round_up(x:int, n:int) -> int: return -(-x // n) * n

def dram_read_cap(readers:int) -> int:
  return 2 if readers >= 88 else 8 if readers >= 42 else 0

def dram(offset:int, page:int=fw.DRAM_PAGE_MAX, banks:int=8) -> int:
  if not (0 <= offset < banks * fw.DRAM_BANK_SIZE and 64 <= page <= 16384 and page % 64 == 0):
    raise ValueError(f"invalid DRAM offset {offset} or page size {page}")
  tag = (page.bit_length() - 1) << 56 if page & (page - 1) == 0 else (page // 64 - 1) << 48
  return 1 << 63 | tag | offset

class Signal:
  def __init__(self, dev, offset:int): self.mem, self.offset, self.addr = dev.host.mem, offset, dev.host.noc_addr + offset
  @property
  def value(self) -> int: return struct.unpack_from("<Q", self.mem, self.offset)[0]
  def wait(self, value:int, timeout:float=10.0):
    deadline = time.monotonic() + timeout
    while (v := self.value) < value:
      if time.monotonic() > deadline: raise TimeoutError(f"signal is {v}, waiting for {value}")

class Allocator:
  COPY_THREADS = 4
  def __init__(self, dev:"Device"):
    self.dev, self.top, self.slot, self.slot_done, self.pool = dev, 0, 0, [0, 0], None
    self.pending_pins = []  # in-flight mappings retained after a DMA timeout

  def release_pins(self, reset=False):
    if not self.pending_pins: return
    completed = self.dev.timeline_signal.value
    while self.pending_pins and (reset or self.pending_pins[0][0] <= completed):
      _, va, size, view = self.pending_pins[0]
      self.dev.card.unpin(va, size)
      view.release()
      self.pending_pins.pop(0)

  def alloc(self, size:int, page:int=fw.DRAM_PAGE_MAX) -> int:
    banks = self.dev.dram_banks
    offset = round_up(self.top, banks * page)
    end = round_up(offset + round_up(size, banks * page), banks * fw.DRAM_PAGE_MAX)
    if size < 0 or end > banks * fw.DRAM_BANK_SIZE: raise MemoryError(f"can't allocate {size} bytes of DRAM")
    self.top = end
    return dram(offset, page, banks)

  def _staged(self, size:int, timeout:float):
    dev = self.dev
    for off in range(0, size, dev.stage_size):
      i, self.slot = self.slot, self.slot ^ 1
      dev.timeline_signal.wait(self.slot_done[i], timeout)
      yield off, min(dev.stage_size, size - off), dev.stage_base + i * dev.stage_size, i

  PIN_CHUNK, PIN_DEPTH, COPY_MAX = 64 << 20, 3, 1 << 30

  def _direct(self, dev_addr:int, host:memoryview, to_device:bool, timeout:float) -> bool:
    """DMA between DRAM and the caller's memory with no staging copy. A buffer from Device.pinned() is used as is;
    any other large buffer is pinned 64 MiB at a time, a few chunks ahead of the device, so pinning overlaps the copies.
    False (nothing copied) if the buffer isn't 64-byte aligned or can't be pinned: the NoC can't shift bytes."""
    dev, page, n = self.dev, mmap.PAGESIZE, len(host)
    if (va := buffer_address(host)) % 64: return False
    def copy(at:int, noc:int, size:int) -> int:
      d, h = dev_addr + (at - va), noc
      return dev.dma_copy(d, h, size, timeout) if to_device else dev.dma_copy(h, d, size, timeout)
    if hm := next((h for h in dev.pinned_buffers if h.addr <= va and va + n <= h.addr + h.size), None):
      for at in range(va, va + n, self.COPY_MAX):
        copy(at, hm.noc_addr + (at - hm.addr), min(self.COPY_MAX, va + n - at))
      dev.timeline_signal.wait(dev.timeline_value, timeout)
      return True
    if n < self.PIN_CHUNK // 4 or not hasattr(dev.card, "pin"): return False
    # Pinning and unpinning cost ~2 ms of CPU per 64 MiB, as long as the DMA itself, so both run on the thread pool
    # (ioctl drops the GIL): the next PIN_DEPTH chunks are being pinned while one is copied.
    chunks, at = [], va
    while at < va + n:                     # boundaries after the first are page-aligned, so no two pins share a page
      stop, pin_va = min(va + n, at // page * page + self.PIN_CHUNK), at // page * page
      chunks.append((at, stop, pin_va, round_up(stop, page) - pin_va))
      at = stop
    pool, pin = self._pool(), lambda c: dev.card.pin(c[2], c[3], read_only=to_device)
    pins = collections.deque((c, pool.submit(pin, c)) for c in chunks[:self.PIN_DEPTH])
    copying, unpins = collections.deque(), []
    def retire():
      c, val = copying[0]
      try: dev.timeline_signal.wait(val, timeout)
      except BaseException:
        for chunk, value in copying:
          self.pending_pins.append((value, chunk[2], chunk[3], memoryview(host)))
        copying.clear()
        raise
      copying.popleft()
      unpins.append(pool.submit(dev.card.unpin, c[2], c[3]))
    try:
      for k, c in enumerate(chunks):
        try: noc = pins.popleft()[1].result()
        except OSError:
          if k == 0: return False          # can't pin this buffer at all: let the caller stage it
          raise
        if k + self.PIN_DEPTH < len(chunks): pins.append((nxt := chunks[k + self.PIN_DEPTH], pool.submit(pin, nxt)))
        try: val = copy(c[0], noc + (c[0] - c[2]), c[1] - c[0])
        except BaseException:
          dev.card.unpin(c[2], c[3])
          raise
        copying.append((c, val))
        if len(copying) > self.PIN_DEPTH: retire()
    finally:
      try:
        while copying: retire()
      finally:
        for c, f in pins:                  # pinned ahead of a failure, never copied
          try: f.result()
          except OSError: continue
          unpins.append(pool.submit(dev.card.unpin, c[2], c[3]))
        for f in unpins: f.result()
    return True

  def _pool(self) -> concurrent.futures.ThreadPoolExecutor:
    if self.pool is None: self.pool = concurrent.futures.ThreadPoolExecutor(self.COPY_THREADS)
    return self.pool

  def _memcpy(self, dst:int, src:int, n:int):
    """Host memcpy split over threads: ctypes calls drop the GIL, and one core can't saturate host memory."""
    part = round_up(-(-n // self.COPY_THREADS), 64)
    list(self._pool().map(lambda at: ctypes.memmove(dst + at, src + at, min(part, n - at)), range(0, n, part)))

  def copyin(self, dest:int, src, timeout:float=60.0):
    """Host -> DRAM. Fastest from a Device.pinned() buffer (~56 GB/s on Gen5 x16), then from any other 64-byte aligned
    buffer of 16 MiB or more (pinned on the fly, ~35-50 GB/s); anything else is staged through a memcpy (~24 GB/s)."""
    dev = self.dev
    with memoryview(src).cast("B") as host:
      if self._direct(dest, host, True, timeout): return
      va = buffer_address(host)
      for off, n, buf, slot in self._staged(len(host), timeout):
        self._memcpy(dev.host.addr + buf, va + off, n)
        self.slot_done[slot] = dev.dma_copy(dest + off, dev.host.noc_addr + buf, n, timeout)
    dev.synchronize(timeout)

  def copyout(self, dest, src:int, timeout:float=60.0):
    """DRAM -> host, with the same fast paths as copyin."""
    dev = self.dev
    with memoryview(dest).cast("B") as host:
      if host.readonly: raise ValueError("copyout needs a writable buffer")
      if self._direct(src, host, False, timeout): return
      va = buffer_address(host)
      def drain(off, n, buf, val):
        dev.timeline_signal.wait(val, timeout)
        self._memcpy(va + off, dev.host.addr + buf, n)
      pending = None
      for off, n, buf, slot in self._staged(len(host), timeout):
        self.slot_done[slot] = val = dev.dma_copy(dev.host.noc_addr + buf, src + off, n, timeout)
        if pending: drain(*pending)
        pending = off, n, buf, val
      if pending: drain(*pending)

  def upload(self, blob, page:int=fw.DRAM_PAGE_MAX) -> int:
    self.copyin(addr := self.alloc(len(blob), page), blob)
    return addr

class Device:
  def __init__(self, index:int=0):
    self.card, self.host, self.booted, self.pinned_buffers, self.allocator = Card(index), None, False, [], None
    try:
      self.cols = (self._telemetry(fw.TAG_ENABLED_TENSIX_COL) & 0x3FFF).bit_count()
      if self.cols not in (12, 14): raise RuntimeError(f"unsupported {self.card.name}: {self.cols} Tensix columns")
      self.dram_banks = 7 if self.card.name == "p100a" else 8
      right = 2 + self.cols
      self.dma_core, self.grid = (right, 11), ((1, 2), (right, 11))
      self.worker_rects = (((1, 2), (right - 1, 11)), ((right, 2), (right, 10)))
      self.workers = [(x, y) for x in range(1, right + 1) if x not in (8, 9) for y in range(2, 12) if (x, y) != self.dma_core]
      # Cores are addressed in translated coords (harvested columns moved past the right edge), but BRCST_EXCLUDE is
      # matched against physical coords, so cover() needs each column's physical x. Translation keeps good columns in
      # order, so a translated exclude quadrant maps to the same physical quadrant.
      self.phys_x = {x: self.card.read32((x, 2), fw.NOC_NODE_ID) & 63 for x in sorted({x for x, _ in self.workers})}
      if list(self.phys_x.values()) != sorted(self.phys_x.values()): raise RuntimeError(f"non-monotonic column translation {self.phys_x}")
      self._reset(self.grid)
      self.booted = True
      self.stage_base, self.stage_size = 16 << 20, 8 << 20
      # With the slots in the last 16 MiB of this pin, DMAs from them ran at ~33 GB/s instead of ~56 (p150a, Gen5 x16,
      # repeatable; cause not found). An unused 32 MiB tail keeps them out of it.
      self.host = HostMemory(self.card, self.stage_base + 2 * self.stage_size + (32 << 20))
      self.heap = mmap.PAGESIZE
      self.timeline_signal, self.timeline_value = Signal(self, 0), 0
      self.allocator = Allocator(self)
      self.dma_window = self._boot_dma()
      self.compute_epoch, self.pending_workers = 0, 0
    except BaseException:
      self.close()
      raise

  def dma_copy(self, dst, src, size, timeout=60.0):
    if dst % 64 or src % 64 or not 0 <= size < 1 << 32: raise ValueError("invalid DMA descriptor")
    value = self.timeline_value + 1
    self.timeline_signal.wait(max(0, value - fw.DMA_DEPTH), timeout)
    at = (fw.SVC_PACKETS + (value % fw.DMA_DEPTH) * fw.PACKET) // 4
    for i, word in enumerate((dst & 0xffffffff, dst >> 32, src & 0xffffffff, src >> 32, size, value >> 32)):
      self.dma_window[at + i] = word
    self.dma_window[fw.SVC_WPTR // 4] = value & 0xffffffff
    self.timeline_value = value
    return value

  def synchronize(self, timeout:float=10.0):
    self.timeline_signal.wait(self.timeline_value, timeout)
    self.allocator.release_pins()
    self.wait_workers(timeout)

  def wait_workers(self, timeout=10.0):
    deadline = time.monotonic() + timeout
    while self.pending_workers:
      if self.card.read32(self.workers[0], fw.WORK_DONE) == self.pending_workers:
        self.pending_workers = 0
      elif time.monotonic() > deadline:
        groups = collections.defaultdict(list)
        for xy in self.workers:
          epoch = self.card.read32(xy, fw.SYNC_EPOCH)
          cursors = struct.unpack("<5I", self.card.read(xy, fw.ROLE_PROGRESS, 20))
          groups[(epoch, cursors)].append(xy)
        sample = [(state, len(cores), cores[:2]) for state, cores in groups.items()]
        raise TimeoutError(f"worker epoch {self.compute_epoch} timed out, arrived={self.card.read32(self.workers[0], fw.SYNC_ARRIVED)}, "
                           f"done={self.card.read32(self.workers[0], fw.WORK_DONE)}, epochs and role cursors={sample}")

  def pinned(self, size:int) -> HostMemory:
    """Host memory the device can DMA to and from directly, pinned for the device's lifetime. copyin/copyout from a
    buffer inside one (h.mem or any slice of it) skip both the staging memcpy and per-call pinning. An unused 32 MiB
    tail keeps the usable part out of the pin's last 16 MiB, which was slow for the staging buffer (see __init__)."""
    self.pinned_buffers.append(h := HostMemory(self.card, round_up(size, 2 << 20) + (32 << 20)))
    return h

  def alloc_host(self, size:int, align:int=64) -> int:
    offset = round_up(self.heap, align)
    if offset + size > self.stage_base: raise MemoryError(f"host heap is full: {size} bytes requested")
    self.heap = offset + size
    return offset

  def load(self, image:bytes, role_pcs:dict[str, int]):
    self.synchronize()
    for rect in self.worker_rects: self._reset(rect)
    header = bytearray(fw.CODE_BASE)
    struct.pack_into("<I", header, 0, fw.jal(fw.CODE_BASE))
    struct.pack_into("<I", header, fw.LEADER_COORD, fw.noc(self.workers[0]))
    struct.pack_into("<3I", header, fw.NUM_WORKERS, len(self.workers), self.dram_banks, self.cols)
    struct.pack_into("<4I", header, fw.ROLE_PC, *(role_pcs.get(r, 0) for r in fw.ROLES[1:]))
    for rect in self.worker_rects:
      self.card.write(rect, 0, header + image)
      self.card.write32(rect, fw.SOFT_RESET, fw.RESET_ALL & ~fw.RESET_BRISC)

    deadline = time.monotonic() + 2
    for xy in self.workers:
      while not self.card.read32(xy, fw.WORK_READY):
        if time.monotonic() > deadline: raise TimeoutError(f"worker {xy} failed to boot")

  def cover(self, cores) -> tuple[int, int]:
    """Multicast (rect, exclude) for cores: a translated rectangle, minus at most one corner quadrant."""
    cores = set(cores)
    x0, x1, y0, y1 = min(x for x, _ in cores), max(x for x, _ in cores), min(y for _, y in cores), max(y for _, y in cores)
    box = {(x, y) for x in range(x0, x1 + 1) if x not in (8, 9) for y in range(y0, y1 + 1)}
    rect, missing = fw.noc((x0, y0)) | fw.noc((x1, y1)) << 12, box - cores
    if not missing: return rect, 0
    dx, dy = any(x == x1 for x, _ in missing), any(y == y1 for _, y in missing)
    ax, ay = (min if dx else max)(x for x, _ in missing), (min if dy else max)(y for _, y in missing)
    assert missing == {(x, y) for x, y in box if (x >= ax if dx else x <= ax) and (y >= ay if dy else y <= ay)}, \
      f"{len(cores)} cores are not a rectangle minus one corner"
    return rect, 1 << 22 | dy << 21 | dx << 20 | ay << 14 | self.phys_x[ax] << 8

  def launch(self, args:int=0, args_size:int=0, cores=None, sync:bool=False, timeout:float=10.0) -> int:
    self.synchronize(timeout)
    selected = self.workers if cores is None else list(cores)
    if not selected or len(set(selected)) != len(selected) or not set(selected) <= set(self.workers):
      raise ValueError("invalid worker set")
    offset = args - self.host.noc_addr
    if args_size and not (0 <= offset <= self.host.size - args_size and 0 < args_size <= fw.STEP_ARGS_SIZE):
      raise ValueError("step args must be in the pinned host buffer")
    targets = self.worker_rects if selected == self.workers else selected
    self.card.write32(self.workers[0], fw.WORK_DONE, 0)
    self.compute_epoch = self.compute_epoch % 0xffffffff + 1
    if args_size:
      for rect in targets: self.card.write(rect, fw.STEP_ARGS, self.host.mem[offset:offset + args_size])
    self.pending_workers = len(selected)
    for rect in targets: self.card.write32(rect, fw.STEP_EPOCH, self.compute_epoch)
    if sync: self.wait_workers(timeout)
    return self.compute_epoch

  def close(self):
    if self.card is None: return
    try:
      if self.booted: self._reset(self.grid)
      if self.allocator: self.allocator.release_pins(reset=True)
      for h in self.pinned_buffers: h.close()
      if self.host is not None: self.host.close()
      if self.allocator and self.allocator.pool: self.allocator.pool.shutdown()
    finally:
      self.card.close()
      self.card = None

  def _telemetry(self, tag:int) -> int:
    rd = lambda addr: self.card.read32(fw.ARC, addr)
    table, data = rd(fw.TELEMETRY_PTR), rd(fw.TELEMETRY_DATA)
    assert 0 < (n := rd(table + 4)) <= 256, f"bad ARC telemetry entry count {n}"
    for i in range(n):
      if (e := rd(table + 8 + 4 * i)) & 0xFFFF == tag: return rd(data + 4 * (e >> 16))
    raise RuntimeError(f"ARC telemetry has no tag {tag}")

  def _reset(self, rect): self.card.write32(rect, fw.SOFT_RESET, fw.RESET_ALL)

  def _boot_dma(self):
    core, (brisc, ncrisc) = self.dma_core, fw.service_images(self.dram_banks)
    state = bytearray(fw.SVC_STATE_SIZE)
    struct.pack_into("<Q", state, fw.SVC_SIGNAL - fw.SVC_STATE, self.timeline_signal.addr)
    self.card.write(core, fw.SVC_STATE, state)
    self.card.write(core, fw.SVC_BRISC_BASE, brisc)
    self.card.write(core, fw.SVC_NCRISC_BASE, ncrisc)
    self.card.write32(core, 0, fw.jal(fw.SVC_BRISC_BASE))
    self.card.write32(core, fw.SOFT_RESET, fw.RESET_ALL & ~fw.RESET_BRISC)
    return self.card.window(core)
