import mmap, struct, sys, time
import fw
from fw import Op
if sys.platform == "darwin": from pci_macos import Card, HostMemory
else: from pci import Card, HostMemory

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

class Queue:
  def __init__(self): self.packets = bytearray()
  def q(self, op:Op, a:int=0, b:int=0, c:int=0):
    self.packets += struct.pack("<4Q", op, a, b, c)
    return self
  def launch(self, dev:"Device", cores, args:int=0, args_size:int=0):
    assert 0 <= args_size <= fw.STEP_ARGS_SIZE and args_size % 16 == 0 and args % 64 == 0 and (args or not args_size)
    rect, exclude = dev.cover(cores)
    return self.q(Op.LAUNCH, rect | exclude << 32, args, len(cores) | args_size << 16)
  def copy(self, dst:int, src:int, size:int):
    assert dst % 64 == src % 64 == 0 and 0 <= size < 1 << 32, "DMA needs 64-byte aligned addresses and a u32 size"
    return self.q(Op.COPY, dst, src, size)
  def wait(self, signal:Signal, value:int, exact:bool=False): return self.q(Op.WAIT, signal.addr, value, exact)
  def store(self, addr:int, value:int):
    assert addr % 8 == 0
    return self.q(Op.STORE, addr, value)
  def signal(self, signal:Signal, value:int): return self.store(signal.addr, value)
  def submit(self, dev:"Device", timeout:float=10.0): dev.ring.push(self.packets, timeout)

class Ring:
  def __init__(self, dev:"Device"):
    self.mem, self.addr, self.l1 = dev.host.mem[:fw.RING_SIZE], dev.host.noc_addr, dev.card.window(dev.service_core)
    self.wptr = self.rptr = 0

  def push(self, blob:bytes, timeout:float=10.0):
    for i in range(0, len(blob), fw.RING_SIZE // 2):
      chunk, deadline = blob[i:i + fw.RING_SIZE // 2], time.monotonic() + timeout
      while (self.wptr - self.rptr) % 2**32 + len(chunk) > fw.RING_SIZE:
        if time.monotonic() > deadline: raise TimeoutError("service ring did not drain")
        self.rptr = self.l1[fw.SVC_RPTR // 4]
      at = self.wptr % fw.RING_SIZE
      first = min(len(chunk), fw.RING_SIZE - at)
      self.mem[at:at + first], self.mem[:len(chunk) - first] = chunk[:first], chunk[first:]
      self.wptr = (self.wptr + len(chunk)) % 2**32
      self.l1[fw.SVC_WPTR // 4] = self.wptr

class Allocator:
  def __init__(self, dev:"Device"): self.dev, self.top, self.slot, self.slot_done = dev, 0, 0, [0, 0]

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
      self.slot_done[i] = dev.next_timeline()
      yield off, min(dev.stage_size, size - off), dev.stage_base + i * dev.stage_size, self.slot_done[i]

  def copyin(self, dest:int, src, timeout:float=60.0):
    dev = self.dev
    with memoryview(src).cast("B") as host:
      for off, n, buf, val in self._staged(len(host), timeout):
        dev.host.mem[buf:buf + n] = host[off:off + n]
        Queue().copy(dest + off, dev.host.noc_addr + buf, n).signal(dev.timeline_signal, val).submit(dev, timeout)
    dev.synchronize(timeout)

  def copyout(self, dest, src:int, timeout:float=60.0):
    dev = self.dev
    with memoryview(dest).cast("B") as host:
      def drain(off, n, buf, val):
        dev.timeline_signal.wait(val, timeout)
        host[off:off + n] = dev.host.mem[buf:buf + n]
      pending = None
      for off, n, buf, val in self._staged(len(host), timeout):
        Queue().copy(dev.host.noc_addr + buf, src + off, n).signal(dev.timeline_signal, val).submit(dev, timeout)
        if pending: drain(*pending)
        pending = off, n, buf, val
      if pending: drain(*pending)

  def upload(self, blob, page:int=fw.DRAM_PAGE_MAX) -> int:
    self.copyin(addr := self.alloc(len(blob), page), blob)
    return addr

class Device:
  def __init__(self, index:int=0):
    self.card, self.host, self.booted = Card(index), None, False
    try:
      self.cols = (self._telemetry(fw.TAG_ENABLED_TENSIX_COL) & 0x3FFF).bit_count()
      if self.cols not in (12, 14): raise RuntimeError(f"unsupported {self.card.name}: {self.cols} Tensix columns")
      self.dram_banks = 7 if self.card.name == "p100a" else 8
      right = 2 + self.cols
      self.service_core, self.grid = (right, 11), ((1, 2), (right, 11))
      self.worker_rects = (((1, 2), (right - 1, 11)), ((right, 2), (right, 10)))
      self.workers = [(x, y) for x in range(1, right + 1) if x not in (8, 9) for y in range(2, 12) if (x, y) != self.service_core]
      # Cores are addressed in translated coords (harvested columns moved past the right edge), but BRCST_EXCLUDE is
      # matched against physical coords, so cover() needs each column's physical x. Translation keeps good columns in
      # order, so a translated exclude quadrant maps to the same physical quadrant.
      self.phys_x = {x: self.card.read32((x, 2), fw.NOC_NODE_ID) & 63 for x in sorted({x for x, _ in self.workers})}
      if list(self.phys_x.values()) != sorted(self.phys_x.values()): raise RuntimeError(f"non-monotonic column translation {self.phys_x}")
      self._reset(self.grid)
      self.booted = True
      self.stage_base, self.stage_size = 16 << 20, 8 << 20
      self.host = HostMemory(self.card, self.stage_base + 2 * self.stage_size)
      self.heap = fw.RING_SIZE + mmap.PAGESIZE
      self.timeline_signal, self.timeline_value = Signal(self, fw.RING_SIZE), 0
      self.allocator = Allocator(self)
      self.ring = self._boot_service()
    except BaseException:
      self.close()
      raise

  def next_timeline(self) -> int:
    self.timeline_value += 1
    return self.timeline_value

  def synchronize(self, timeout:float=10.0): self.timeline_signal.wait(self.timeline_value, timeout)

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
    struct.pack_into("<I", header, fw.SERVICE_COORD, fw.noc(self.service_core))
    struct.pack_into("<3I", header, fw.NUM_WORKERS, len(self.workers), self.dram_banks, self.cols)
    struct.pack_into("<4I", header, fw.ROLE_PC, *(role_pcs.get(r, 0) for r in fw.ROLES[1:]))
    for rect in self.worker_rects:
      self.card.write(rect, 0, header + image)
      self.card.write32(rect, fw.SOFT_RESET, fw.RESET_ALL & ~fw.RESET_BRISC)

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
    val = self.next_timeline()
    Queue().launch(self, cores or self.workers, args, args_size).signal(self.timeline_signal, val).submit(self, timeout)
    if sync: self.timeline_signal.wait(val, timeout)
    return val

  def close(self):
    if self.card is None: return
    try:
      if self.booted: self._reset(self.grid)
      if self.host is not None: self.host.close()
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

  def _boot_service(self) -> Ring:
    core, (brisc, ncrisc), ring = self.service_core, fw.service_images(self.dram_banks), Ring(self)
    state = bytearray(fw.SVC_STATE_SIZE)
    struct.pack_into("<Q", state, fw.SVC_RING_LO - fw.SVC_STATE, ring.addr)
    self.card.write(core, fw.SVC_STATE, state)
    self.card.write(core, fw.SVC_BRISC_BASE, brisc)
    self.card.write(core, fw.SVC_NCRISC_BASE, ncrisc)
    self.card.write32(core, 0, fw.jal(fw.SVC_BRISC_BASE))
    self.card.write32(core, fw.SOFT_RESET, fw.RESET_ALL & ~fw.RESET_BRISC)
    return ring
