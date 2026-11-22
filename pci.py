import ctypes, ctypes.util, fcntl, mmap, os, struct
from pathlib import Path

TLB_SIZE = 1 << 21
SUPPORTED = ("p100a", "p150a", "p150b")

libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int64]
libc.mmap.restype = ctypes.c_void_p
libc.munmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t]

def view_at(addr:int, n:int) -> memoryview: return memoryview((ctypes.c_uint8 * n).from_address(addr)).cast("B")

def map_memory(size:int, fd:int=-1, offset:int=0, flags:int=mmap.MAP_SHARED) -> int:
  if fd == -1: flags |= mmap.MAP_ANONYMOUS
  if (addr := libc.mmap(None, size, mmap.PROT_READ | mmap.PROT_WRITE, flags, fd, offset)) in (None, 2**64 - 1):
    raise OSError(ctypes.get_errno(), f"mmap of {size} bytes failed: {os.strerror(ctypes.get_errno())}")
  return addr

def ioctl(fd, nr, fmt, *args):
  data = bytearray(struct.pack("<" + fmt, *args))
  fcntl.ioctl(fd, 0xFA00 | nr, data)
  return struct.unpack("<" + fmt, data)

class HostMemory:
  def __init__(self, card:"Card", size:int):
    assert size % mmap.PAGESIZE == 0
    self.fd, self.size, self.addr = card.fd, size, map_memory(size, flags=mmap.MAP_PRIVATE)
    try:
      self.mem = view_at(self.addr, size)
      self.noc_addr = ioctl(self.fd, 7, "IIQQQQ", 16, 2, self.addr, size, 0, 0)[-1]
    except BaseException:
      libc.munmap(self.addr, size)
      raise

  def close(self):
    if self.addr is None: return
    try: ioctl(self.fd, 10, "QQQ", self.addr, self.size, 0)
    finally:
      libc.munmap(self.addr, self.size)
      self.addr = None

class Card:
  def __init__(self, index:int=0):
    sysfs = Path(f"/sys/class/tenstorrent/tenstorrent!{index}")
    if not (iommu := sysfs / "device/iommu_group/type").exists() or not iommu.read_text().startswith("DMA"):
      raise RuntimeError("enable iommu")
    if (name := (sysfs / "tt_card_type").read_text().strip()) not in SUPPORTED:
      raise RuntimeError(f"unsupported card {name}, expected one of {SUPPORTED}")
    self.name, self.fd = name, os.open(f"/dev/tenstorrent/{index}", os.O_RDWR | os.O_CLOEXEC | os.O_APPEND)
    try:
      if not ioctl(self.fd, 8, "IIB3xB3x", 4, 0, 20, 0)[-1]:
        raise RuntimeError(f"/dev/tenstorrent/{index} is in use by another process")
    except BaseException:
      os.close(self.fd)
      raise
    self.windows, self.tlb_cfg = [], None
    try:
      self.power(7)
      self.tlb_id, tlb_addr = self._window()
    except BaseException:
      self.close()
      raise
    self.tlb = view_at(tlb_addr, TLB_SIZE)
    self.tlb32 = self.tlb.cast("I")

  def close(self):
    if self.fd is None: return
    for addr in self.windows: libc.munmap(addr, TLB_SIZE)
    self.windows = []
    try: self.power(0)
    finally:
      os.close(self.fd)
      self.fd = None

  def power(self, flags:int):
    ioctl(self.fd, 15, "IIBBH28x", 40, 0, 0, 15, flags)

  def _window(self) -> tuple[int, int]:
    _, _, tlb, _, offset, _, _ = ioctl(self.fd, 11, "QQIIQQQ", TLB_SIZE, 0, 0, 0, 0, 0, 0)
    self.windows.append(addr := map_memory(TLB_SIZE, self.fd, offset))
    return tlb, addr

  def _configure(self, tlb, core, addr):
    mcast = isinstance(core[0], tuple)
    (x0, y0), (x1, y1) = core if mcast else (core, core)
    ioctl(self.fd, 13, "IIQ4HBBB21x", tlb, 0, addr, x1, y1, x0, y0, 0, mcast, 1)

  def window(self, core) -> memoryview:
    tlb, addr = self._window()
    self._configure(tlb, core, 0)
    return view_at(addr, TLB_SIZE).cast("I")

  def _target(self, core, addr) -> int:
    base = addr & -TLB_SIZE
    if self.tlb_cfg != (core, base):
      self._configure(self.tlb_id, core, base)
      self.tlb_cfg = (core, base)
    return addr - base

  def write(self, core, addr, data):
    data = memoryview(data).cast("B")
    while len(data):
      off = self._target(core, addr)
      n = min(len(data), TLB_SIZE - off)
      self.tlb[off:off + n], addr, data = data[:n], addr + n, data[n:]

  def read(self, core, addr, n) -> bytes:
    out = bytearray()
    while len(out) < n:
      off = self._target(core, addr + len(out))
      out += self.tlb[off:off + min(n - len(out), TLB_SIZE - off)]
    return bytes(out)

  def write32(self, core, addr, v): self.tlb32[self._target(core, addr) // 4] = v
  def read32(self, core, addr): return self.tlb32[self._target(core, addr) // 4]
