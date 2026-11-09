import collections, struct, time
from fw import Op, noc
import fw
from helpers import round_up
from system import PCIDevice, Sysmem

def dram(offset:int, page:int) -> int:
  assert page in (1024, 2048, 4096) and offset < 1 << 56, (offset, page)
  return 1 << 63 | page.bit_length() - 1 << 56 | offset

def l1(core, addr:int) -> int: return noc(core) << 32 | addr

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

def _pad(b:bytes, n:int=16) -> bytes: return b.ljust(round_up(len(b), n), b"\0")

class Launch:
  """An immutable dispatcher-local descriptor and its dynamic parameter size."""
  def __init__(self, addr:int, args_size:int): self.addr, self.args_size = addr, args_size

class HWQueue:
  def __init__(self): self.blob = bytearray()
  def q(self, op:int, a:int=0, b:int=0, c:int=0):
    self.blob += struct.pack("<4Q", op, a, b, c)
    return self
  def wait(self, signal:int, value:int, eq:bool=False): return self.q(Op.WAIT, signal, value, int(eq))
  def signal(self, signal:int, value:int): return self.q(Op.STORE, signal, value)
  def timestamp(self, signal:int): return self.q(Op.TIMESTAMP, signal + 8)
  def memory_barrier(self): return self  # every packet finishes before the next starts
  def call(self, graph:"Graph"): return self.q(Op.CALL, graph.addr, 0, graph.size)  # plain HWQueue on the CQ ring only
  def submit(self, ring:"Ring"):
    ring.push(bytes(self.blob))
    return self

class ComputeQueue(HWQueue):
  def exec(self, launch:Launch, args:int=0, profile:int=0):
    """Copy code to fixed worker slots, launch, and wait for all workers. profile names two 16-byte slots."""
    assert fw.DESCRIPTOR_L1 <= launch.addr < fw.DESCRIPTOR_END
    assert args % 64 == 0 and (args or not launch.args_size)
    assert profile % 16 == 0
    return self.q(Op.EXEC, launch.addr, args, profile)
  def exec_barrier(self): return self  # EXEC waits for every worker before the next packet
  def call(self, graph:"Graph"): raise TypeError("CALLs do not nest: a ComputeQueue is itself submitted as a CALL")
  def submit(self, ring:"Ring"):  # the ring gets one CALL to this queue's packets, written to a command buffer
    ring.call_host(bytes(self.blob))
    return self

class Graph:
  """A ComputeQueue's packets, uploaded to DRAM once (Device.capture) and replayed with one CALL (Device.replay).
  Like any EXEC, its programs and args must not change while a replay is in flight."""
  def __init__(self, addr:int, size:int, execs:int): self.addr, self.size, self.execs = addr, size, execs

class CopyQueue(HWQueue):
  def copy(self, dst:int, src:int, size:int):
    """Copy between 64-byte aligned addresses; the byte count need not be aligned."""
    assert dst % 64 == src % 64 == 0, "DMA source and destination must be 64-byte aligned"
    assert 0 <= size < 1 << 32, "DMA byte count must fit u32"
    return self.q(Op.COPY, dst, src, size)

class Ring:
  def __init__(self, dev:PCIDevice, core, sysmem:Sysmem, offset:int, cmdbuf:int=0, cmdbuf_size:int=0):
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
