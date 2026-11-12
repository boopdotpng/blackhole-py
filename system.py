import fcntl, mmap, os, struct
from pathlib import Path
from helpers import PAGE, libc_mmap, libc_munmap, view_at

TLB_SIZE = 1 << 21

def ioctl(fd, nr, fmt, *args):
  data = bytearray(struct.pack('<' + fmt, *args))
  fcntl.ioctl(fd, 0xFA00 | nr, data)
  return struct.unpack('<' + fmt, data)

class Sysmem:
  def __init__(self, fd, size):
    assert size % PAGE == 0
    self.fd, self.size, self.addr = fd, size, libc_mmap(size, flags=mmap.MAP_PRIVATE)
    try:
      self.mem = view_at(self.addr, size)
      self.noc_addr = ioctl(fd, 7, "IIQQQQ", 16, 2, self.addr, size, 0, 0)[-1]  # PIN_PAGES, NOC_DMA
    except BaseException:
      libc_munmap(self.addr, size)
      raise

  def close(self):
    ioctl(self.fd, 10, "QQQ", self.addr, self.size, 0)  # UNPIN_PAGES
    libc_munmap(self.addr, self.size)

class PCIIface:
  def __init__(self, index=0):
    iommu = Path(f"/sys/class/tenstorrent/tenstorrent!{index}/device/iommu_group/type")
    if not iommu.exists() or not iommu.read_text().startswith("DMA"):
      raise RuntimeError("enable iommu")
    self.card = Path(f"/sys/class/tenstorrent/tenstorrent!{index}/tt_card_type").read_text().strip()
    if self.card not in ("p150a", "p150b"): raise RuntimeError(f"unsupported card {self.card}, only p150 for now")
    self.fd = os.open(f"/dev/tenstorrent/{index}", os.O_RDWR | os.O_CLOEXEC | os.O_APPEND)
    try:
      if not ioctl(self.fd, 8, "IIB3xB3x", 4, 0, 20, 0)[-1]:  # LOCK_CTL: acquire UMD's CHIP_IN_USE lock; fd close releases
        raise RuntimeError(f"/dev/tenstorrent/{index} is in use by another process (tt-metal or another blackhole-py)")
    except BaseException:
      os.close(self.fd)
      raise
    self.windows, self.tlb_cfg = [], None
    try:
      self.power(7)  # max AI clock, DRAM PHY awake, Tensix enabled
      self.tlb_id, tlb_addr = self._window()
    except BaseException:
      self.close()
      raise
    self.tlb = view_at(tlb_addr, TLB_SIZE)
    self.tlb32 = self.tlb.cast("I")

  def close(self):
    for addr in self.windows: libc_munmap(addr, TLB_SIZE)
    try: self.power(0)
    finally: os.close(self.fd)

  def power(self, flags):  # SET_POWER_STATE: validity is a count (15 flags, 0 settings), not a mask
    ioctl(self.fd, 15, "IIBBH28x", 40, 0, 0, 15, flags)

  def _window(self):
    _, _, tlb, _, offset, _, _ = ioctl(self.fd, 11, "QQIIQQQ", TLB_SIZE, 0, 0, 0, 0, 0, 0)
    self.windows.append(addr := libc_mmap(TLB_SIZE, self.fd, offset))
    return tlb, addr

  def _configure(self, tlb, core, addr):
    mcast = isinstance(core[0], tuple)
    (x0, y0), (x1, y1) = core if mcast else (core, core)
    # CONFIGURE_TLB: id, reserved, addr, end/start xy, noc, mcast, strict ordering, reserved, output
    ioctl(self.fd, 13, "IIQ4HBBB21x", tlb, 0, addr, x1, y1, x0, y0, 0, mcast, 1)

  def window(self, core) -> memoryview:
    tlb, addr = self._window()
    self._configure(tlb, core, 0)
    return view_at(addr, TLB_SIZE).cast("I")

  def _target(self, core, addr):
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
      self.tlb[off:off+n], addr, data = data[:n], addr + n, data[n:]

  def read(self, core, addr, n):
    out = bytearray()
    while len(out) < n:
      off = self._target(core, addr + len(out))
      out += self.tlb[off:off + min(n - len(out), TLB_SIZE - off)]
    return bytes(out)

  def write32(self, core, addr, v): self.tlb32[self._target(core, addr) // 4] = v
  def read32(self, core, addr): return self.tlb32[self._target(core, addr) // 4]
