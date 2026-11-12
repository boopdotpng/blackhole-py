import collections, mmap, struct, time
from dataclasses import dataclass
import fw
from fw import Op
from helpers import PAGE, round_up
from system import PCIIface, Sysmem

def dram(offset:int, page:int) -> int:
  assert page in (1024, 2048, 4096) and offset < 1 << 56, (offset, page)
  return 1 << 63 | page.bit_length() - 1 << 56 | offset

def rects(cores) -> list[tuple[tuple[int, int], tuple[int, int]]]:
  gap = lambda x: x - 2 if x >= 10 else x
  left, out = {(gap(x), y) for x, y in cores}, []
  for x, y in sorted(left, key=lambda c: (c[1], c[0])):
    if (x, y) not in left: continue
    x1, y1 = x, y
    while (x1 + 1, y) in left: x1 += 1
    while all((i, y1 + 1) in left for i in range(x, x1 + 1)): y1 += 1
    left -= {(i, j) for i in range(x, x1 + 1) for j in range(y, y1 + 1)}
    out.append(((x + 2 * (x >= 8), y), (x1 + 2 * (x1 >= 8), y1)))
  return out

@dataclass(frozen=True)
class BlackholeProgramData:
  addr:int
  args_size:int

class HWQueue:
  def __init__(self): self.blob = bytearray()
  def q(self, op:int, a:int=0, b:int=0, c:int=0):
    self.blob += struct.pack("<4Q", op, a, b, c)
    return self
  def wait(self, signal:int, value:int, eq:bool=False): return self.q(Op.WAIT, signal, value, int(eq))
  def signal(self, signal:int, value:int): return self.q(Op.STORE, signal, value)
  def timestamp(self, signal:int): return self.q(Op.TIMESTAMP, signal + 8)
  def memory_barrier(self): return self  # every packet finishes before the next starts
  def submit(self, ring:"BlackholeQueueDesc"):
    ring.push(bytes(self.blob))
    return self

class BlackholeComputeQueue(HWQueue):
  def exec(self, prg:BlackholeProgramData, args:int=0, profile:int=0):
    """Copy code to fixed worker slots, launch, and wait for all workers. profile names two 16-byte slots."""
    assert fw.DESCRIPTOR_L1 <= prg.addr < fw.DESCRIPTOR_END
    assert args % 64 == 0 and (args or not prg.args_size)
    assert profile % 16 == 0
    return self.q(Op.EXEC, prg.addr, args, profile)
  def exec_barrier(self): return self  # EXEC waits for every worker before the next packet
  def submit(self, ring:"BlackholeQueueDesc"):  # like AMD's indirect buffer: publish one CALL to the command buffer
    ring.call_host(bytes(self.blob))
    return self

class Graph:
  """Immutable command buffers in DRAM. Patches are (u64 byte offset, increment per instance)."""
  def __init__(self, dev, queue:BlackholeComputeQueue, count:int=1, patches=()):
    import numpy as np
    assert count > 0 and queue.blob and len(queue.blob) % fw.PACKET == 0
    self.dev, self.count, self.size = dev, count, len(queue.blob)
    self.stride = round_up(self.size, 64)
    self.ops = collections.Counter(Op(op).name for op, *_ in struct.iter_unpack("<4Q", queue.blob))
    assert not (self.ops.keys() & {"CALL", "COPY"}), "compute graphs cannot nest or run DMA packets"
    rows = np.zeros((count, self.stride // 8), dtype="<u8")
    rows[:, :self.size // 8] = np.frombuffer(queue.blob, dtype="<u8")
    for offset, step in patches:
      assert offset % 8 == 0 and 0 <= offset < self.size and offset % fw.PACKET != 0
      rows[:, offset // 8] += np.arange(count, dtype=np.uint64) * np.uint64(step)
    self.addr = dev.upload(rows.tobytes())

  def replay(self, start:int=0, count:int=1, timeout=10.0) -> int:
    """Submit consecutive instances and wait once. Return host submission time in ns."""
    assert 0 <= start < self.count and 0 < count <= self.count - start
    t = time.perf_counter_ns()
    q = HWQueue()
    for i in range(start, start + count): q.q(Op.CALL, self.addr + i * self.stride, 0, self.size)
    self.dev.graph_timeline += 1
    q.signal(self.dev.signal(253), self.dev.graph_timeline).submit(self.dev.compute_queue)
    elapsed = time.perf_counter_ns() - t
    self.dev.wait(253, self.dev.graph_timeline, timeout)
    return elapsed

class BlackholeDMAQueue(HWQueue):
  def copy(self, dst:int, src:int, size:int):
    """Copy between 64-byte aligned addresses; the byte count need not be aligned."""
    assert dst % 64 == src % 64 == 0, "DMA source and destination must be 64-byte aligned"
    assert 0 <= size < 1 << 32, "DMA byte count must fit u32"
    return self.q(Op.COPY, dst, src, size)

class BlackholeQueueDesc:
  def __init__(self, dev:PCIIface, core, sysmem:Sysmem, offset:int, cmdbuf:int=0, cmdbuf_size:int=0):
    self.core, self.sysmem, self.offset, self.put, self.rptr = core, sysmem, offset, 0, 0
    self.l1 = dev.window(core)
    self.addr = sysmem.noc_addr + offset
    sysmem.mem[offset:offset + fw.RING_SIZE] = bytes(fw.RING_SIZE)
    self.cmdbuf, self.cmdbuf_size, self.cmdbuf_put, self.inflight = cmdbuf, cmdbuf_size, 0, collections.deque()
    self.ops = collections.Counter()  # packets pushed, by op name

  def _wait_rptr(self, value:int, deadline:float):  # until the firmware has retired the ring up to value
    while (self.rptr - value) & 0x80000000:
      if time.monotonic() > deadline: raise TimeoutError(f"ring on {self.core} did not drain")
      self.rptr = self.l1[fw.RPTR // 4]

  def push(self, blob:bytes, timeout=10.0):
    assert len(blob) % fw.PACKET == 0
    self.ops.update(Op(blob[i]).name for i in range(0, len(blob), fw.PACKET))
    for i in range(0, len(blob), fw.RING_SIZE // 2):
      chunk = blob[i:i + fw.RING_SIZE // 2]
      self._wait_rptr(self.put + len(chunk) - fw.RING_SIZE, time.monotonic() + timeout)
      at, n = self.put % fw.RING_SIZE, len(chunk)
      first = min(n, fw.RING_SIZE - at)
      self.sysmem.mem[self.offset + at:self.offset + at + first] = chunk[:first]
      self.sysmem.mem[self.offset:self.offset + n - first] = chunk[first:]
      self.put = (self.put + n) & 0xFFFFFFFF
      self.l1[fw.WPTR // 4] = self.put  # sysmem stores are visible before this uncached doorbell

  def call(self, addr:int, size:int):
    """Run size bytes of packets at addr (a command buffer in DRAM or host memory). They cannot CALL."""
    assert size % fw.PACKET == 0
    self.push(struct.pack("<4Q", Op.CALL, addr, 0, size))

  def call_host(self, blob:bytes, timeout=10.0):
    """CALL blob from the command buffer area, a ring of its own: space is reused once the CALL that used it retired."""
    n, size = round_up(len(blob), 64), self.cmdbuf_size
    assert n <= size, f"command buffer of {len(blob)} bytes is larger than the area"
    if (at := self.cmdbuf_put % size) + n > size: self.cmdbuf_put, at = self.cmdbuf_put + size - at, 0
    deadline = time.monotonic() + timeout
    while self.inflight and self.inflight[0][0] < self.cmdbuf_put + n - size:
      self._wait_rptr(self.inflight[0][1], deadline)
      self.inflight.popleft()
    self.sysmem.mem[self.cmdbuf + at:self.cmdbuf + at + len(blob)] = blob
    self.call(self.sysmem.noc_addr + self.cmdbuf + at, len(blob))
    self.inflight.append((self.cmdbuf_put, self.put))
    self.cmdbuf_put += n

def blackhole_build_program(dev, images:dict, args_size:int=0) -> BlackholeProgramData:
  # Pack code in DRAM and immutable multicast geometry in dispatcher L1; EXEC supplies dynamic args.
  assert images and set(images) <= set(dev.workers)
  assert 0 <= args_size <= fw.PARAM_SIZE and args_size % 16 == 0
  groups = {}
  for core, roles in images.items():
    for role, image in roles.items():
      assert role in fw.ROLES and 0 < len(image) <= fw.CODE_SIZE[role] and len(image) % 4 == 0
      groups.setdefault((fw.CODE[role], image), []).append(core)
    mask = sum(1 << fw.ROLES.index(r) for r in roles)
    groups.setdefault((fw.LAUNCH, struct.pack('<I', mask)), []).append(core)
  payload, transfers = bytearray(), []
  encode = lambda cores: [fw.noc(s) | fw.noc(e) << 12 for s, e in rects(cores)]
  for (addr, image), cores in groups.items():
    payload.extend(bytes(-len(payload) % 64))
    rs = encode(cores)
    transfers.extend([len(payload), addr, len(image), len(rs), *rs])
    payload.extend(image)
  payload.extend(bytes(-len(payload) % 64))
  assert len(payload) <= fw.STAGE_SIZE, f"program payload too large: {len(payload)}"
  rs = encode(images)
  size = 4 * (8 + len(rs) + len(transfers))
  at = dev.descriptor_top
  if at + size > fw.DESCRIPTOR_END: raise MemoryError("dispatcher descriptor arena full")
  addr = dev.upload(bytes(payload))
  words = [len(images), len(rs), args_size, len(payload), addr & 0xFFFFFFFF, addr >> 32, len(groups), 0, *rs, *transfers]
  dev.iface.write(dev.cq_core, at, struct.pack(f'<{len(words)}I', *words))
  dev.descriptor_top = round_up(at + size, 64)
  return BlackholeProgramData(at, args_size)

class BlackholeAllocator:
  def __init__(self, dev):
    self.dev, self.dram_top = dev, 0
    self.transfers, self.stage_next, self.stage_done = 0, 0, [0, 0]

  def _alloc(self, size:int) -> int:
    offset, end = self.dram_top, self.dram_top + round_up(size, fw.DRAM_BANKS * fw.DRAM_PAGE_MAX)
    if end > (total := fw.DRAM_BANKS * fw.DRAM_BANK_SIZE):
      raise MemoryError(f"DRAM is full: {size} bytes requested, {total - offset} left")
    self.dram_top = end
    return offset

  def _stage(self, timeout):
    i = self.stage_next
    self.dev.wait(255, self.stage_done[i], timeout)
    self.stage_next ^= 1
    return self.dev.arena_size + i * self.dev.stage_size

  def _submit(self, dst, src, size, buf):
    self.transfers += 1
    try: BlackholeDMAQueue().copy(dst, src, size).signal(self.dev.signal(255), self.transfers).submit(self.dev.dma_queue)
    except BaseException:
      self.dev.close()  # a partial submission may still reference the staging slot
      raise
    self.stage_done[(buf - self.dev.arena_size) // self.dev.stage_size] = self.transfers

  def _copyin(self, dest:int, src, timeout=60.0):
    with memoryview(src).cast("B") as host:
      for off in range(0, len(host), self.dev.stage_size):
        buf, n = self._stage(timeout), min(self.dev.stage_size, len(host) - off)
        self.dev.sysmem.mem[buf:buf + n] = host[off:off + n]
        self._submit(dest + off, self.dev.addr(buf), n, buf)
    self.dev.wait(255, self.transfers, timeout)

  def _copyout(self, dest, src:int, timeout=60.0):
    with memoryview(dest).cast("B") as host:
      for off in range(0, len(host), self.dev.stage_size):
        buf, n = self._stage(timeout), min(self.dev.stage_size, len(host) - off)
        self._submit(self.dev.addr(buf), src + off, n, buf)
        self.dev.wait(255, self.transfers, timeout)
        host[off:off + n] = self.dev.sysmem.mem[buf:buf + n]

  def load(self, sources):
    # mmap keeps safetensors offsets unaligned; only the two pinned DMA staging slots need alignment.
    for dst, path, offset, size in sources:
      if not size: continue
      with open(path, 'rb') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm, memoryview(mm) as view:
        with view[offset:offset + size] as data:
          if len(data) != size: raise ValueError(f"file ended before {offset + size}: {path}")
          self._copyin(dst, data)

class BlackholeDevice:
  def __init__(self, device:str="BLACKHOLE"):
    self.device = device
    self.iface = PCIIface(int(device.split(":")[1]) if ":" in device else 0)
    self.sysmem, self.all = None, None
    try:
      cols = (self._telemetry(fw.TAG_ENABLED_TENSIX_COL) & 0x3FFF).bit_count()
      if cols not in (12, 14): raise RuntimeError(f"unsupported {self.iface.card}: {cols} Tensix columns enabled")
      right = 2 + cols
      self.all = ((1, 2), (right, 11))
      self.cq_core, self.dma_core = (right, 2), (right, 3)  # the top of the rightmost column
      self.workers = [(x, y) for x in range(1, right + 1) if x not in (8, 9) for y in range(2, 12)
                      if (x, y) not in (self.cq_core, self.dma_core)]
      self._boot()
      # one pinned buffer: [arena (rings, signals, heap) | stage 0 | stage 1]
      self.arena_size, self.stage_size = 16 << 20, 8 << 20
      self.sysmem = Sysmem(self.iface.fd, self.arena_size + 2 * self.stage_size)
      self.signals = 2 * fw.RING_SIZE
      self.heap = self.signals + PAGE
      self.allocator = BlackholeAllocator(self)
      self.sysmem.mem[self.signals:self.heap] = bytes(self.heap - self.signals)
      self.compute_queue = self.create_queue(self.cq_core, 0, "dispatch", cmdbuf_size=1 << 20)
      self.dma_queue = self.create_queue(self.dma_core, fw.RING_SIZE, "dma")
      self.descriptor_top, self.graph_timeline = fw.DESCRIPTOR_L1, 0
      self.run(fw.images()["init"], self.workers)
    except BaseException:
      self.close()
      raise

  def close(self):
    if self.iface is None: return
    try:
      if self.all is not None: self._reset()  # stop service loops before unpinning their rings
      if self.sysmem is not None: self.sysmem.close()
    finally:
      self.iface.close()
      self.iface = None

  def _telemetry(self, tag:int) -> int:
    dev = self.iface
    table = dev.read32(fw.ARC, fw.TELEMETRY_PTR)
    n = dev.read32(fw.ARC, table + 4)
    assert 0 < n <= 256, f"bad ARC telemetry entry count {n}"
    for i in range(n):
      if (e := dev.read32(fw.ARC, table + 8 + 4 * i)) & 0xFFFF == tag: return dev.read32(fw.ARC, table + 8 + 4 * n + 4 * (e >> 16))
    raise RuntimeError(f"ARC telemetry has no tag {tag}")

  def _reset(self): self.iface.write32(self.all, fw.SOFT_RESET, fw.RESET_ALL)  # every RISC of every worker core

  def _boot(self):
    dev, images = self.iface, fw.images()
    self._reset()
    dev.write32(self.all, fw.GO_SIGNAL, 0)
    for role in fw.ROLES: dev.write(self.all, fw.FW[role][0], images[f"worker_{role}"])
    dev.write32(self.all, 0, fw.jal(fw.FW["brisc"][0]))  # BRISC always starts at 0
    dev.write32(self.all, fw.SOFT_RESET, fw.RESET_ALL & ~fw.RESET_BRISC)

  def create_queue(self, core, offset:int, loop:str, cmdbuf_size:int=0) -> BlackholeQueueDesc:
    ring, dev = BlackholeQueueDesc(self.iface, core, self.sysmem, offset, self.alloc(cmdbuf_size), cmdbuf_size), self.iface
    dev.write(core, fw.STATE, bytes(fw.STATE_SIZE))
    dev.write(core, fw.RING_LO, struct.pack("<II", ring.addr & 0xFFFFFFFF, ring.addr >> 32))
    prog = fw.images()[loop]  # a service loop is an ordinary program, started directly
    for role, image in prog.items(): dev.write(core, fw.CODE[role], image)
    dev.write32(core, fw.LAUNCH, sum(1 << fw.ROLES.index(r) for r in prog))
    dev.write32(core, fw.GO_SIGNAL, 0x80)
    return ring

  def alloc(self, size:int, align:int=64) -> int:
    offset = round_up(self.heap, align)
    if offset + size > self.arena_size:
      raise MemoryError(f"arena is full: {size} bytes requested, {self.arena_size - offset} left")
    self.heap = offset + size
    return offset
  def addr(self, offset:int) -> int: return self.sysmem.noc_addr + offset

  def signal(self, i:int) -> int: return self.addr(self.signals + 16 * i)
  def read_signal(self, i:int) -> tuple[int, int]: return struct.unpack_from("<QQ", self.sysmem.mem, self.signals + 16 * i)
  def wait(self, i:int, value:int, timeout=10.0) -> int:
    deadline = time.monotonic() + timeout
    while (v := self.read_signal(i))[0] < value:
      if time.monotonic() > deadline: raise TimeoutError(f"signal {i} is {v[0]}, waiting for {value}")
    return v[1]

  def run(self, prog:dict[str, bytes], cores, params:bytes=b"", timeout=10.0):
    """Bind a program, run it once, and wait. For setup, not the hot path."""
    params = params.ljust(round_up(len(params), 16), b'\0')
    launch = blackhole_build_program(self, {tuple(c): prog for c in cores}, len(params))
    q = BlackholeComputeQueue().exec(launch, self.upload(params) if params else 0)
    self.runs = getattr(self, "runs", 0) + 1
    q.signal(self.signal(254), self.runs).submit(self.compute_queue)
    self.wait(254, self.runs, timeout)

  def upload(self, blob:bytes) -> int:
    addr = dram(self.allocator._alloc(len(blob)), fw.DRAM_PAGE_MAX)
    self.allocator._copyin(addr, blob)
    return addr
