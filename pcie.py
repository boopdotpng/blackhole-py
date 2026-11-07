import ctypes, fcntl, mmap, os, struct
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

def ioctl(fd, nr, fmt, *args, out=""):
  buf = bytearray(struct.pack("<" + fmt, *args) + bytes(struct.calcsize("<" + out)))
  fcntl.ioctl(fd, 0xFA00 | nr, buf)
  return struct.unpack_from("<" + out, buf, struct.calcsize("<" + fmt))

PIN_PAGES, UNPIN_PAGES, ALLOCATE_TLB, CONFIGURE_TLB, SET_POWER_STATE = 7, 10, 11, 13, 15

PAGE = mmap.PAGESIZE
def round_up(x:int, n:int) -> int: return -(-x // n) * n
def addressof(buf) -> int:
  """Host address of a writable buffer (bytearray, mmap, numpy array, memoryview...)."""
  buf = memoryview(buf).cast("B")
  return ctypes.addressof((ctypes.c_char * len(buf)).from_buffer(buf))

# Page-aligned host memory -> its NoC address (flags 2 = NOC_DMA). Needs the IOMMU on, holds one of the card's 16 windows
# to host memory until unpin. The KMD pins one range at a time per fd.
def _pin(fd, addr, size): return ioctl(fd, PIN_PAGES, "IIQQ", 16, 2, addr, size, out="QQ")[1]
def _unpin(fd, addr, size): ioctl(fd, UNPIN_PAGES, "QQQ", addr, size, 0)

# pinned() pins host memory CHUNK bytes at a time on PINNERS extra fds (so pins overlap), with up to WINDOWS chunks pinned
# at once. Of the 16 windows, sysmem holds one and the rest are left for pin().
CHUNK, PINNERS, WINDOWS = 32 << 20, 2, 6

CORES = [(x, y) for x in (*range(1, 8), *range(10, 15)) for y in range(2, 12)]
ALL = ((1, 2), (14, 11))  # multicast to every core
# NoC 0 port per bank. The harvested bank is always translated to the last slot, so p100a = DRAM[:7].
DRAM = ((17, 14), (17, 15), (17, 18), (17, 21), (18, 14), (18, 17), (18, 20), (18, 23))

SOFT_RESET = 0xFFB121B0
RESET_BIT = {"brisc": 1 << 11, "trisc0": 1 << 12, "trisc1": 1 << 13, "trisc2": 1 << 14, "ncrisc": 1 << 18}
RESET_ALL = sum(RESET_BIT.values())
RESET_PC = {"trisc0": 0xFFB12228, "trisc1": 0xFFB1222C, "trisc2": 0xFFB12230, "ncrisc": 0xFFB12238}
TRISC_PC_OVERRIDE, NCRISC_PC_OVERRIDE = 0xFFB12234, 0xFFB1223C

def jal(offset):
  return ((offset >> 20 & 1) << 31 | (offset >> 1 & 0x3FF) << 21 | (offset >> 11 & 1) << 20 | (offset >> 12 & 0xFF) << 12 | 0x6F)

class TLB:
  SIZE = 1 << 21
  def __init__(self, fd):
    self.fd, self.cfg = fd, None
    self.id, _, mmap_offset_uc, _, _ = ioctl(fd, ALLOCATE_TLB, "QQ", self.SIZE, 0, out="IIQQQ")
    self.mem = mmap.mmap(fd, self.SIZE, offset=mmap_offset_uc)
    self.u32 = memoryview(self.mem).cast("I")  # single 32-bit accesses for registers

  def target(self, core, addr=0):
    ((x, y), (xe, ye)), base = core if core == ALL else (core, core), addr & -self.SIZE
    if self.cfg != (core, base):
      ioctl(self.fd, CONFIGURE_TLB, "IIQHHHHBBBBB11x", self.id, 0, base, xe, ye, x, y, 0, core == ALL, 1, 0, 0, out="Q")
      self.cfg = (core, base)
    return addr - base

class Sysmem:
  def __init__(self, fd, size):
    assert size % mmap.PAGESIZE == 0
    self.fd, self.size, self.mem = fd, size, mmap.mmap(-1, size)
    self.addr = addressof(self.mem)
    self.noc_addr = _pin(fd, self.addr, size)

  def close(self):
    _unpin(self.fd, self.addr, self.size)
    self.mem.close()

class PCIDevice:
  def __init__(self, index=0, sysmem_size=256 << 20):
    iommu = Path(f"/sys/class/tenstorrent/tenstorrent!{index}/device/iommu_group/type")
    if not iommu.exists() or not iommu.read_text().startswith("DMA"):
      raise RuntimeError("the card reaches host memory through the IOMMU, which is off or in passthrough mode: "
                         "enable it (amd_iommu=on / intel_iommu=on, no iommu=pt) and reboot")
    self.card = Path(f"/sys/class/tenstorrent/tenstorrent!{index}/tt_card_type").read_text().strip()
    assert self.card in ("p100a", "p150a", "p150b", "p150c"), self.card
    self.dram = DRAM[:7] if self.card == "p100a" else DRAM
    self.fd = os.open(f"/dev/tenstorrent/{index}", os.O_RDWR | os.O_CLOEXEC)
    ioctl(self.fd, SET_POWER_STATE, "IIBBH28x", 40, 0, 0, 4, 0b1111)  # aiclk, dram phy, tensix, l2cpu
    self.sysmem = Sysmem(self.fd, sysmem_size)
    self.tlb = TLB(self.fd)
    self.pinners = [(os.open(f"/dev/tenstorrent/{index}", os.O_RDWR | os.O_CLOEXEC), ThreadPoolExecutor(1)) for _ in range(PINNERS)]

  def close(self):
    for fd, ex in self.pinners:
      ex.shutdown()
      os.close(fd)
    self.sysmem.close()
    self.tlb.u32.release()
    self.tlb.mem.close()
    os.close(self.fd)
  def __enter__(self): return self
  def __exit__(self, *exc): self.close()

  # ---- host memory the card reads and writes in place ----
  def pin(self, addr:int, size:int) -> int: return _pin(self.fd, addr, size)  # page-aligned; holds a window until unpin
  def unpin(self, addr:int, size:int): _unpin(self.fd, addr, size)

  def pinned(self, addr:int, size:int, release):
    """Pin [addr, addr + size) chunk by chunk, yielding (host_addr, noc_addr, n) for each piece of the range in order.
    Up to WINDOWS chunks are pinned ahead on the pinner threads. After yielding chunk i, calls release(i - 1), which must
    block until the card is done with that chunk, then unpins it and starts pinning the next one."""
    if not size: return
    start, end = addr & -PAGE, round_up(addr + size, PAGE)
    chunks = [(s, min(s + CHUNK, end)) for s in range(start, end, CHUNK)]
    pins, unpins = {}, []
    def begin(i):
      (fd, ex), (s, e) = self.pinners[i % PINNERS], chunks[i]
      pins[i] = ex.submit(_pin, fd, s, e - s)
    def finish(i):
      release(i)
      (fd, ex), (s, e) = self.pinners[i % PINNERS], chunks[i]
      unpins.append(ex.submit(_unpin, fd, s, e - s))
    try:
      for i in range(min(WINDOWS, len(chunks))): begin(i)
      for i, (s, e) in enumerate(chunks):
        noc, lo, hi = pins[i].result(), max(s, addr), min(e, addr + size)
        yield lo, noc + lo - s, hi - lo
        if i:
          finish(i - 1)
          if i - 1 + WINDOWS < len(chunks): begin(i - 1 + WINDOWS)
      finish(len(chunks) - 1)
    finally:
      for u in unpins: u.result()

  def reset(self, core=ALL): self.write32(core, SOFT_RESET, RESET_ALL)  # every RISC of core (or ALL) into soft reset

  def write(self, core, addr, data):
    data = memoryview(data).cast("B")
    while len(data):
      off = self.tlb.target(core, addr)
      n = min(len(data), TLB.SIZE - off)
      self.tlb.mem[off:off+n], addr, data = data[:n], addr + n, data[n:]

  def read(self, core, addr, n):
    out = bytearray()
    while len(out) < n:
      off = self.tlb.target(core, addr + len(out))
      out += self.tlb.mem[off:off + min(n - len(out), TLB.SIZE - off)]
    return bytes(out)

  def write32(self, core, addr, v): self.tlb.u32[self.tlb.target(core, addr) // 4] = v
  def read32(self, core, addr): return self.tlb.u32[self.tlb.target(core, addr) // 4]

  # images: {core or ALL: {risc: (addr, code)}}. A core's own entry overrides ALL's; RISCs with no image stay in reset.
  def boot(self, images):
    images = dict(sorted(images.items(), key=lambda kv: kv[0] != ALL))
    self.reset()
    for core, riscs in images.items():
      for risc, (addr, code) in riscs.items():
        self.write(core, addr, code)
        self.write32(core, *((0, jal(addr)) if risc == "brisc" else (RESET_PC[risc], addr)))
    self.write32(ALL, TRISC_PC_OVERRIDE, 0b111)
    self.write32(ALL, NCRISC_PC_OVERRIDE, 1)
    for core, riscs in images.items():
      self.write32(core, SOFT_RESET, RESET_ALL & ~sum(RESET_BIT[r] for r in {*images.get(ALL, ()), *riscs}))
