import ctypes, fcntl, mmap, os, struct
from pathlib import Path

def ioctl(fd, nr, fmt, *args, out=""):
  buf = bytearray(struct.pack("<" + fmt, *args) + bytes(struct.calcsize("<" + out)))
  fcntl.ioctl(fd, 0xFA00 | nr, buf)
  return struct.unpack_from("<" + out, buf, struct.calcsize("<" + fmt))

PIN_PAGES, ALLOCATE_TLB, CONFIGURE_TLB, SET_POWER_STATE = 7, 11, 13, 15

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
    self.mem = mmap.mmap(-1, size)
    self.addr = ctypes.addressof(ctypes.c_char.from_buffer(self.mem))
    _, self.noc_addr = ioctl(fd, PIN_PAGES, "IIQQ", 16, 2, self.addr, size, out="QQ")

class PCIDevice:
  def __init__(self, index=0, sysmem_size=256 << 20):
    self.card = Path(f"/sys/class/tenstorrent/tenstorrent!{index}/tt_card_type").read_text().strip()
    assert self.card in ("p100a", "p150a", "p150b", "p150c"), self.card
    self.dram = DRAM[:7] if self.card == "p100a" else DRAM
    self.fd = os.open(f"/dev/tenstorrent/{index}", os.O_RDWR | os.O_CLOEXEC)
    ioctl(self.fd, SET_POWER_STATE, "IIBBH28x", 40, 0, 0, 4, 0b1111)  # aiclk, dram phy, tensix, l2cpu
    self.sysmem = Sysmem(self.fd, sysmem_size)
    self.tlb = TLB(self.fd)

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
    self.write32(ALL, SOFT_RESET, RESET_ALL)
    for core, riscs in images.items():
      for risc, (addr, code) in riscs.items():
        self.write(core, addr, code)
        self.write32(core, *((0, jal(addr)) if risc == "brisc" else (RESET_PC[risc], addr)))
    self.write32(ALL, TRISC_PC_OVERRIDE, 0b111)
    self.write32(ALL, NCRISC_PC_OVERRIDE, 1)
    for core, riscs in images.items():
      self.write32(core, SOFT_RESET, RESET_ALL & ~sum(RESET_BIT[r] for r in {*images.get(ALL, ()), *riscs}))
