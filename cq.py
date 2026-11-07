# Command queues, shaped like tinygrad's hcq2 HWQueue: a queue is a list of 32-byte [op, a, b, c] packets (fw.Op),
# built by exec / copy / wait / signal / timestamp and pushed to a ring in sysmem with submit().
# A signal is two u64s, [value, timestamp], wherever an address can point: sysmem, DRAM or L1.
#
#   COMPUTE: EXEC on the CQ core (BRISC dispatch, NCRISC prefetch)
#   COPY:    COPY on the DMA core (BRISC + NCRISC)
#   both:    WAIT, STORE (signal), TIMESTAMP
import struct, time
from fw import Op, noc
import fw
from pcie import PCIDevice, round_up

# ---- addresses: what a packet's a / b words hold ----
def dram(offset:int, page:int) -> int:
  """Interleaved DRAM (Device.alloc_dram): page p lives in bank p % banks. A page is a tile, 1024 elements of the dtype.
  1 KB at least, so a DMA_BATCH stays under the 256 requests a transaction id's 8-bit counter can hold."""
  assert page in (1024, 2048, 4096) and offset < 1 << 56, (offset, page)
  return 1 << 63 | page.bit_length() - 1 << 56 | offset

def l1(core, addr:int) -> int: return noc(core) << 32 | addr

def rects(cores) -> list[tuple[tuple[int, int], tuple[int, int]]]:  # greedy cover by multicast rectangles
  left, out = set(cores), []
  for x, y in sorted(cores, key=lambda c: (c[1], c[0])):
    if (x, y) not in left: continue
    x1, y1 = x, y
    while (x1 + 1, y) in left: x1 += 1
    while all((i, y1 + 1) in left for i in range(x, x1 + 1)): y1 += 1
    left -= {(i, j) for i in range(x, x1 + 1) for j in range(y, y1 + 1)}
    out.append(((x, y), (x1, y1)))
  return out

def _pad(b:bytes, n:int=16) -> bytes: return b.ljust(round_up(len(b), n), b"\0")

def program(kernels:dict[str, bytes]) -> tuple[bytes, list[int]]:
  """EXEC's prog blob and its five sizes. kernels[role] is linked at fw.KERNEL[role] and ends with a jump to
  fw.RETURN[role]. A RISC without one gets a single jump back, every RISC must return."""
  segs = [_pad(kernels.get(r) or fw.return_stub(r)) for r in fw.ROLES]
  assert all(len(s) <= fw.KERNEL[r][1] for s, r in zip(segs, fw.ROLES))
  return b"".join(segs), [len(s) for s in segs]

def kernargs(cores, sizes:list[int], params:bytes=b"") -> bytes:
  """EXEC's args blob: the rectangles to launch on and the kernel sizes, then the params, which land at L1_PARAM_BASE."""
  rs = rects(cores)
  assert len(rs) <= fw.ARGS_HEADER // 4 - fw.ARGS_RECTS and len(sizes) == 5 and len(params) <= fw.PARAM_SIZE
  header = struct.pack(f"<{fw.ARGS_RECTS}I{len(rs)}I", len(rs), len(cores), *sizes, *(noc(s) | noc(e) << 12 for s, e in rs))
  return header.ljust(fw.ARGS_HEADER, b"\0") + _pad(params)

# ---- queues ----
class HWQueue:
  def __init__(self): self.blob = bytearray()
  def q(self, op:int, a:int=0, b:int=0, c:int=0):
    self.blob += struct.pack("<4Q", op, a, b, c)
    return self
  def wait(self, signal:int, value:int, eq:bool=False): return self.q(Op.WAIT, signal, value, int(eq))
  def signal(self, signal:int, value:int): return self.q(Op.STORE, signal, value)
  def timestamp(self, signal:int): return self.q(Op.TIMESTAMP, signal + 8)
  def memory_barrier(self): return self  # every packet finishes before the next starts
  def submit(self, ring:"Ring"):
    ring.push(bytes(self.blob))
    return self

class ComputeQueue(HWQueue):
  def exec(self, prog:int, prog_size:int, args:int, args_size:int):
    """Load each kernel of prog (see program()) into its slot and the params on every core args names, GO, wait for all."""
    assert prog_size <= fw.PROG_MAX and fw.ARGS_HEADER <= args_size <= fw.ARGS_MAX and not (prog_size | args_size) % 16
    return self.q(Op.EXEC | prog_size << 32, prog, args, args_size)

class CopyQueue(HWQueue):
  def copy(self, dst:int, src:int, size:int): return self.q(Op.COPY, dst, src, size)

# ---- the rings ----
class Ring:
  def __init__(self, dev:PCIDevice, core, offset:int):
    self.dev, self.core, self.offset, self.put, self.rptr = dev, core, offset, 0, 0
    dev.sysmem.mem[offset:offset + fw.RING_SIZE] = bytes(fw.RING_SIZE)
    addr = dev.sysmem.noc_addr + offset
    dev.write(core, fw.STATE, bytes(fw.STATE_SIZE))
    dev.write(core, fw.RING_LO, struct.pack("<II", addr & 0xFFFFFFFF, addr >> 32))

  def push(self, blob:bytes, timeout=10.0):
    assert len(blob) % fw.PACKET == 0
    for i in range(0, len(blob), fw.RING_SIZE // 2):
      chunk, deadline = blob[i:i + fw.RING_SIZE // 2], time.monotonic() + timeout
      while (self.put + len(chunk) - self.rptr) & 0xFFFFFFFF > fw.RING_SIZE:  # only read RPTR over MMIO when it looks full
        if time.monotonic() > deadline: raise TimeoutError(f"ring on {self.core} did not drain")
        self.rptr = self.dev.read32(self.core, fw.RPTR)
      at, n = self.put % fw.RING_SIZE, len(chunk)
      first = min(n, fw.RING_SIZE - at)
      self.dev.sysmem.mem[self.offset + at:self.offset + at + first] = chunk[:first]
      self.dev.sysmem.mem[self.offset:self.offset + n - first] = chunk[first:]
      self.put = (self.put + n) & 0xFFFFFFFF
      self.dev.write32(self.core, fw.WPTR, self.put)  # sysmem stores are visible before this uncached doorbell
