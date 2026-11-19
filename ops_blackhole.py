import struct, time
from dataclasses import dataclass
import numpy as np
import fw
from fw import Op
from helpers import PAGE, round_up
from system import PCIIface, Sysmem

def dram(offset:int, page:int=fw.DRAM_PAGE_MAX) -> int:  # a DRAM address, page-interleaved over the 8 banks
  if not (0 <= offset < fw.DRAM_BANKS * fw.DRAM_BANK_SIZE and 64 <= page <= 16384 and page % 64 == 0):
    raise ValueError(f"invalid DRAM offset {offset} or page size {page}")
  tag = (page.bit_length() - 1) << 56 if page & (page - 1) == 0 else (page // 64 - 1) << 48
  return 1 << 63 | tag | offset

def cover(cores) -> tuple[int, int]:
  """One multicast to exactly these cores: (start | end << 12, NoC0 BRCST_EXCLUDE). The rectangle is the bounding box
  (columns 8 and 9 have no Tensix cores, so spanning them is free) and the exclusion word carves off one corner
  quadrant: enough for a column-major grid, which is full columns then a partial one filled from the top, with the
  CQ and DMA cores at the bottom of the last column. Measured on p150: bits 8-13 anchor x, 14-19 anchor y,
  20 x >= anchor (else <=), 21 y >= anchor (else <=), 22 enable. The anchor itself is excluded."""
  cores = set(cores)
  x0, x1, y0, y1 = min(x for x, _ in cores), max(x for x, _ in cores), min(y for _, y in cores), max(y for _, y in cores)
  box = {(x, y) for x in range(x0, x1 + 1) if x not in (8, 9) for y in range(y0, y1 + 1)}
  rect, missing = fw.noc((x0, y0)) | fw.noc((x1, y1)) << 12, box - cores
  if not missing: return rect, 0
  dx, dy = any(x == x1 for x, _ in missing), any(y == y1 for _, y in missing)
  ax, ay = (min if dx else max)(x for x, _ in missing), (min if dy else max)(y for _, y in missing)
  assert missing == {(x, y) for x, y in box if (x >= ax if dx else x <= ax) and (y >= ay if dy else y <= ay)}, \
    f"{len(cores)} cores are not a rectangle minus one corner"
  return rect, 1 << 22 | dy << 21 | dx << 20 | ay << 14 | ax << 8

class BlackholeSignal:  # 16 bytes of pinned host memory: [value, timestamp]
  def __init__(self, dev, offset:int): self.mem, self.offset, self.addr = dev.sysmem.mem, offset, dev.sysmem.noc_addr + offset
  @property
  def value(self) -> int: return struct.unpack_from("<Q", self.mem, self.offset)[0]
  def wait(self, value:int, timeout=10.0):
    deadline = time.monotonic() + timeout
    while (v := self.value) < value:
      if time.monotonic() > deadline: raise TimeoutError(f"signal is {v}, waiting for {value}")

class HWQueue:  # 32-byte packets, run in order: each finishes before the next starts
  def __init__(self): self._q = bytearray()
  def q(self, op:Op, a:int=0, b:int=0, c:int=0):
    self._q += struct.pack("<4Q", op, a, b, c)
    return self
  def wait(self, signal:BlackholeSignal, value:int): return self.q(Op.WAIT, signal.addr, value)
  def store(self, addr:int, value:int):
    """Write 8 bytes to an 8-byte aligned NoC address once every earlier packet has finished, like cuStreamWriteValue64.
    Used for signals and for argument words that change between graph runs."""
    assert addr % 8 == 0 and 0 <= value < 1 << 64
    return self.q(Op.STORE, addr, value)
  def signal(self, signal:BlackholeSignal, value:int): return self.store(signal.addr, value)
  def timestamp(self, addr:int): return self.q(Op.TIMESTAMP, addr + 8)  # same [value, timestamp] layout as a signal

class BlackholeComputeQueue(HWQueue):
  def exec(self, prg:"BlackholeProgramData", args:int=0, profile:int=0):
    """Copy code to the workers, launch, and wait for all of them. profile names two 16-byte timestamp slots."""
    assert args % 64 == 0 and (args or not prg.args_size) and profile % 16 == 0
    return self.q(Op.EXEC, prg.addr, args, profile)
  def call(self, addr:int, size:int, count:int=1, stride:int=0):
    """Run count command buffers at addr + i * stride. Each buffer contains size bytes of packets."""
    assert 0 < count < 1 << 32 and 0 <= stride < 1 << 32 and (count == 1 or stride >= size and stride % 64 == 0)
    return self.q(Op.CALL, addr, count | stride << 32, size)
  def submit(self, dev, timeout=10.0): dev.compute_queue.push(bytes(self._q), timeout=timeout)

class BlackholeDMAQueue(HWQueue):
  def copy(self, dst:int, src:int, size:int):
    assert dst % 64 == src % 64 == 0 and 0 <= size < 1 << 32, "DMA needs 64-byte aligned addresses and a u32 size"
    return self.q(Op.COPY, dst, src, size)
  def submit(self, dev): dev.dma_queue.push(bytes(self._q))

class BlackholeGraph:
  """count instances of a compute queue in DRAM, run with CALL. patches are (byte offset, increment per instance)."""
  def __init__(self, dev, q:BlackholeComputeQueue, count:int=1, patches=()):
    assert not {Op.CALL, Op.COPY} & {p[0] for p in struct.iter_unpack("<4Q", q._q)}, "graphs cannot nest or copy"
    self.dev, self.count, self.size, self.stride = dev, count, len(q._q), round_up(len(q._q), 64)
    rows = np.zeros((count, self.stride // 8), dtype="<u8")
    rows[:, :self.size // 8] = np.frombuffer(q._q, dtype="<u8")
    for offset, step in patches: rows[:, offset // 8] += np.arange(count, dtype=np.uint64) * np.uint64(step)
    self.addr = dev.allocator.upload(rows.tobytes())

  def submit(self, start:int=0, count:int=1, timeout=10.0, before:BlackholeComputeQueue|None=None) -> tuple[int, int]:
    """Queue instances start..start+count without waiting, after the packets in before (say STOREs of argument
    words that change between runs). Returns (timeline value that marks them retired, submit ns)."""
    assert 0 <= start and 0 < count and start + count <= self.count
    t = time.perf_counter_ns()
    q = BlackholeComputeQueue()
    if before is not None: q._q += before._q
    q.call(self.addr + start * self.stride, self.size, count, self.stride)
    # Honor the execution timeout if earlier work is still occupying the ring.
    q.signal(self.dev.timeline_signal, value := self.dev.next_timeline()).submit(self.dev, timeout=timeout)
    return value, time.perf_counter_ns() - t

  def __call__(self, start:int=0, count:int=1, timeout=10.0) -> int:
    """Run instances start..start+count and wait. Returns the host submission time in ns."""
    _, elapsed = self.submit(start, count, timeout)
    self.dev.synchronize(timeout)
    return elapsed

class BlackholeQueueDesc:  # a ring in pinned host memory; the firmware reads it and publishes its read pointer in L1
  def __init__(self, dev, core, offset:int):
    self.ring, self.put_value, self.read_value = dev.sysmem.mem[offset:offset + fw.RING_SIZE], 0, 0
    self.l1, self.addr = dev.iface.window(core), dev.sysmem.noc_addr + offset

  def push(self, blob:bytes, timeout=10.0):
    for i in range(0, len(blob), fw.RING_SIZE // 2):
      chunk = blob[i:i + fw.RING_SIZE // 2]
      deadline = time.monotonic() + timeout
      while (self.read_value - (self.put_value + len(chunk) - fw.RING_SIZE)) & 0x80000000:  # wait for room
        if time.monotonic() > deadline: raise TimeoutError("ring did not drain")
        self.read_value = self.l1[fw.RPTR // 4]
      at = self.put_value % fw.RING_SIZE
      first = min(len(chunk), fw.RING_SIZE - at)
      self.ring[at:at + first], self.ring[:len(chunk) - first] = chunk[:first], chunk[first:]
      self.put_value = (self.put_value + len(chunk)) & 0xFFFFFFFF
      self.l1[fw.WPTR // 4] = self.put_value  # sysmem stores are visible before this uncached doorbell

@dataclass(frozen=True)
class BlackholeProgramData:
  addr:int  # descriptor in dispatcher L1
  args_size:int

def blackhole_build_program(dev, images:dict, args_size:int=0) -> BlackholeProgramData:
  """images: {core: {role: code}}. Code goes to DRAM, multicast geometry to dispatcher L1; EXEC supplies the args."""
  assert images and set(images) <= set(dev.workers) and 0 <= args_size <= fw.PARAM_SIZE and args_size % 16 == 0
  groups = {}
  for core, roles in images.items():
    for role, image in roles.items():
      assert 0 < len(image) <= fw.CODE_SIZE[role] and len(image) % 4 == 0
      groups.setdefault((fw.CODE[role], image), []).append(core)
    groups.setdefault((fw.LAUNCH, struct.pack('<I', sum(1 << fw.ROLES.index(r) for r in roles))), []).append(core)
  return _install_program(dev, images, groups, args_size)

def blackhole_build_grid_program(dev, grid:int, roles:dict, args_size:int=0) -> BlackholeProgramData:
  """Multicast one set of role images to the first grid workers."""
  if not 1 <= grid <= len(dev.workers): raise ValueError(f"invalid worker count {grid}")
  workers = dev.workers[:grid]
  groups = {(fw.CODE[r], image): workers for r,image in roles.items()}
  mask = sum(1 << fw.ROLES.index(r) for r in roles)
  groups[fw.LAUNCH, struct.pack("<I", mask)] = workers
  return _install_program(dev, workers, groups, args_size)

def _install_program(dev, workers, groups, args_size):
  payload, transfers = bytearray(), []
  for (addr, image), cores in groups.items():
    payload += bytes(-len(payload) % 64)
    transfers += [len(payload), addr, len(image), *cover(cores)]
    payload += image
  payload += bytes(-len(payload) % 64)
  assert len(payload) <= fw.STAGE_SIZE, f"program payload too large: {len(payload)}"
  code, (rect, exclude) = dev.allocator.upload(payload), cover(workers)
  words = [len(workers), rect, args_size, len(payload), code & 0xFFFFFFFF, code >> 32, len(groups), exclude, *transfers]
  if (at := dev.descriptor_top) + 4 * len(words) > fw.DESCRIPTOR_END: raise MemoryError("dispatcher descriptor arena full")
  dev.iface.write(dev.cq_core, at, struct.pack(f'<{len(words)}I', *words))
  dev.descriptor_top = round_up(at + 4 * len(words), 64)
  return BlackholeProgramData(at, args_size)

class BlackholeAllocator:
  """DRAM is a bump allocator (allocations live until close). Copies stream through two pinned staging slots."""
  def __init__(self, dev): self.dev, self.dram_top, self.stage_next, self.stage_done = dev, 0, 0, [0, 0]

  def _alloc(self, size:int, page:int=fw.DRAM_PAGE_MAX) -> int:
    stripe = fw.DRAM_BANKS * page
    if size < 0 or page <= 0: raise ValueError("invalid allocation")
    offset = round_up(self.dram_top, stripe)
    end = round_up(offset + round_up(size, stripe), fw.DRAM_BANKS * fw.DRAM_PAGE_MAX)
    if end > fw.DRAM_BANKS * fw.DRAM_BANK_SIZE: raise MemoryError(f"DRAM is full: {size} bytes requested")
    addr = dram(offset, page)
    self.dram_top = end
    return addr

  def _stage(self, timeout) -> tuple[int, int]:  # the next staging slot, once the copy that last used it is done
    i, self.stage_next = self.stage_next, self.stage_next ^ 1
    self.dev.timeline_signal.wait(self.stage_done[i], timeout)
    return i, self.dev.stage_base + i * self.dev.stage_size

  def _copy(self, i:int, dst:int, src:int, size:int):
    dev = self.dev
    BlackholeDMAQueue().copy(dst, src, size).signal(dev.timeline_signal, value := dev.next_timeline()).submit(dev)
    self.stage_done[i] = value

  def _copyin(self, dest:int, src, timeout=60.0):
    dev = self.dev
    with memoryview(src).cast("B") as host:
      for off in range(0, len(host), dev.stage_size):
        (i, buf), n = self._stage(timeout), min(dev.stage_size, len(host) - off)
        dev.sysmem.mem[buf:buf + n] = host[off:off + n]
        self._copy(i, dest + off, dev.sysmem.noc_addr + buf, n)
    dev.synchronize(timeout)

  def _copyout(self, dest, src:int, timeout=60.0):
    dev = self.dev
    with memoryview(dest).cast("B") as host:
      for off in range(0, len(host), dev.stage_size):
        (i, buf), n = self._stage(timeout), min(dev.stage_size, len(host) - off)
        self._copy(i, dev.sysmem.noc_addr + buf, src + off, n)
        dev.synchronize(timeout)
        host[off:off + n] = dev.sysmem.mem[buf:buf + n]

  def upload(self, blob) -> int:
    self._copyin(addr := self._alloc(len(blob)), blob)
    return addr

class BlackholeDevice:
  def __init__(self, device:str="BLACKHOLE"):
    self.iface, self.sysmem, self.booted = PCIIface(int(device.split(":")[1]) if ":" in device else 0), None, False
    try:
      cols = (self._telemetry(fw.TAG_ENABLED_TENSIX_COL) & 0x3FFF).bit_count()
      if cols not in (12, 14): raise RuntimeError(f"unsupported {self.iface.card}: {cols} Tensix columns enabled")
      right = 2 + cols
      self.all, self.cq_core, self.dma_core = ((1, 2), (right, 11)), (right, 10), (right, 11)  # CQ, DMA: bottom of the last column
      self.workers = [(x, y) for x in range(1, right + 1) if x not in (8, 9) for y in range(2, 12)
                      if (x, y) not in (self.cq_core, self.dma_core)]
      self._boot()
      # one pinned buffer: [compute ring | dma ring | signals | host heap ... | stage 0 | stage 1]
      self.stage_base, self.stage_size = 16 << 20, 8 << 20
      self.sysmem = Sysmem(self.iface.fd, self.stage_base + 2 * self.stage_size)
      self.heap = 2 * fw.RING_SIZE + PAGE
      self.timeline_signal, self.timeline_value = BlackholeSignal(self, 2 * fw.RING_SIZE), 1
      self.ttrv_keep_base, self.ttrv_scratch_end = 0x180000, fw.DATA_BASE
      self.allocator, self.descriptor_top = BlackholeAllocator(self), fw.DESCRIPTOR_L1
      self.compute_queue = self._create_queue(self.cq_core, 0, "dispatch")
      self.dma_queue = self._create_queue(self.dma_core, fw.RING_SIZE, "dma")
      init = blackhole_build_program(self, {c: fw.images()["init"] for c in self.workers})
      BlackholeComputeQueue().exec(init).signal(self.timeline_signal, self.next_timeline()).submit(self)
      self.synchronize()
    except BaseException:
      self.close()
      raise

  # one timeline for both queues: every submitter waits for its work, so signals land in order
  def next_timeline(self) -> int:
    self.timeline_value += 1
    return self.timeline_value - 1
  def synchronize(self, timeout=10.0): self.timeline_signal.wait(self.timeline_value - 1, timeout)

  def alloc_host(self, size:int, align:int=64) -> int:  # offset of pinned host memory the device can write
    offset = round_up(self.heap, align)
    if offset + size > self.stage_base: raise MemoryError(f"host heap is full: {size} bytes requested")
    self.heap = offset + size
    return offset

  def close(self):
    if self.iface is None: return
    try:
      if self.booted: self._reset()  # stop the queue loops before unpinning their rings
      if self.sysmem is not None: self.sysmem.close()
    finally:
      self.iface.close()
      self.iface = None

  def _telemetry(self, tag:int) -> int:
    rd = lambda addr: self.iface.read32(fw.ARC, addr)
    table = rd(fw.TELEMETRY_PTR)
    assert 0 < (n := rd(table + 4)) <= 256, f"bad ARC telemetry entry count {n}"
    for i in range(n):
      if (e := rd(table + 8 + 4 * i)) & 0xFFFF == tag: return rd(table + 8 + 4 * n + 4 * (e >> 16))
    raise RuntimeError(f"ARC telemetry has no tag {tag}")

  def _reset(self): self.iface.write32(self.all, fw.SOFT_RESET, fw.RESET_ALL)  # every RISC of every worker core

  def _boot(self):
    iface, images = self.iface, fw.images()
    self._reset()
    self.booted = True
    iface.write32(self.all, fw.GO_SIGNAL, 0)
    for role in fw.ROLES: iface.write(self.all, fw.FW[role][0], images[f"worker_{role}"])
    iface.write32(self.all, 0, fw.jal(fw.FW["brisc"][0]))  # BRISC always starts at 0
    iface.write32(self.all, fw.SOFT_RESET, fw.RESET_ALL & ~fw.RESET_BRISC)

  def _create_queue(self, core, offset:int, loop:str) -> BlackholeQueueDesc:
    ring, iface, prog = BlackholeQueueDesc(self, core, offset), self.iface, fw.images()[loop]
    iface.write(core, fw.STATE, bytes(fw.STATE_SIZE))
    iface.write(core, fw.RING_LO, struct.pack("<Q", ring.addr))
    for role, image in prog.items(): iface.write(core, fw.CODE[role], image)  # the queue loop is a program, started directly
    iface.write32(core, fw.LAUNCH, sum(1 << fw.ROLES.index(r) for r in prog))
    iface.write32(core, fw.GO_SIGNAL, 0x80)
    return ring
