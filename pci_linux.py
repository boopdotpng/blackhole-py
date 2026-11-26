import fcntl, mmap, os, struct
from pathlib import Path
from pci import ARC, SUPPORTED, TLB_SIZE, Card, Monitor, libc, map_memory, rect, view_at

# tt-kmd ioctls (ioctl.h)
RESET_DEVICE, PIN_PAGES, LOCK_CTL, UNPIN_PAGES, ALLOCATE_TLB, CONFIGURE_TLB, SET_POWER_STATE, NOC_READ = 6, 7, 8, 10, 11, 13, 15, 18
RESET_PCIE_LINK, RESET_ASIC, RESET_ASIC_DMC, RESET_POST = 1, 4, 5, 6  # RESET_DEVICE flags
LOCK_TEST, LOCK_ACQUIRE, CHIP_IN_USE = 2, 0, 20                        # LOCK_CTL flag, lock index

def ioctl(fd, nr, fmt, *args):
  data = bytearray(struct.pack("<" + fmt, *args))
  fcntl.ioctl(fd, 0xFA00 | nr, data)
  return struct.unpack("<" + fmt, data)

def open_dev(index:int) -> int: return os.open(f"/dev/tenstorrent/{index}", os.O_RDWR | os.O_CLOEXEC | os.O_APPEND)
def set_power(fd:int, flags:int): ioctl(fd, SET_POWER_STATE, "IIBBH28x", 40, 0, 0, 15, flags)

class HostMemory:
  def __init__(self, card:"LinuxCard", size:int):
    assert size % mmap.PAGESIZE == 0
    self.card, self.size, self.addr = card, size, map_memory(size, flags=mmap.MAP_PRIVATE)
    try:
      self.mem = view_at(self.addr, size)
      self.noc_addr = card.pin(self.addr, size)
    except BaseException:
      libc.munmap(self.addr, size)
      raise

  def close(self):
    if self.addr is None: return
    try: self.card.unpin(self.addr, self.size)
    finally:
      libc.munmap(self.addr, self.size)
      self.addr = None

class LinuxCard(Card):
  can_pin = True

  def __init__(self, index:int=0):
    sysfs = Path(f"/sys/class/tenstorrent/tenstorrent!{index}")
    if not (iommu := sysfs / "device/iommu_group/type").exists() or not iommu.read_text().startswith("DMA"):
      raise RuntimeError("enable iommu")
    if (name := (sysfs / "tt_card_type").read_text().strip()) not in SUPPORTED:
      raise RuntimeError(f"unsupported card {name}, expected one of {SUPPORTED}")
    self.name, self.fd = name, open_dev(index)
    try:
      if not ioctl(self.fd, LOCK_CTL, "IIB3xB3x", 4, LOCK_ACQUIRE, CHIP_IN_USE, 0)[-1]:
        raise RuntimeError(f"/dev/tenstorrent/{index} is in use by another process")
    except BaseException:
      os.close(self.fd)
      raise
    self.windows = []
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

  def power(self, flags:int): set_power(self.fd, flags)
  def alloc_host(self, size:int) -> HostMemory: return HostMemory(self, size)
  def pin(self, va:int, size:int, read_only:bool=False) -> int:
    return ioctl(self.fd, PIN_PAGES, "IIQQQQ", 16, 2 | (8 if read_only else 0), va, size, 0, 0)[-1]
  def unpin(self, va:int, size:int): ioctl(self.fd, UNPIN_PAGES, "QQQ", va, size, 0)

  def _window(self) -> tuple[int, int]:
    _, _, tlb, _, offset, _, _ = ioctl(self.fd, ALLOCATE_TLB, "QQIIQQQ", TLB_SIZE, 0, 0, 0, 0, 0, 0)
    self.windows.append(addr := map_memory(TLB_SIZE, self.fd, offset))
    return tlb, addr

  def window(self, core) -> memoryview:
    tlb, addr = self._window()
    self._configure(tlb, core, 0)
    return view_at(addr, TLB_SIZE).cast("I")

  def _configure(self, tlb, core, addr):
    x0, y0, x1, y1, mcast = rect(core)
    ioctl(self.fd, CONFIGURE_TLB, "IIQ4HBBB21x", tlb, 0, addr, x1, y1, x0, y0, 0, mcast, 1)

  def _wread(self, off, n): return self.tlb[off:off + n]
  def _wwrite(self, off, data): self.tlb[off:off + len(data)] = data
  def _wread32(self, off): return self.tlb32[off // 4]
  def _wwrite32(self, off, v): self.tlb32[off // 4] = v

class LinuxMonitor(Monitor):
  # Read-only access through tt-kmd's NOC_READ: no lock and no power vote, so it works while another process owns the card.
  def __init__(self, index:int): self.fd = open_dev(index)
  def noc_read(self, addr:int, xy=ARC) -> int: return ioctl(self.fd, NOC_READ, "IIHHBB2xQQ", 32, 0, *xy, 0, 4, addr, 0)[-1]
  def in_use(self) -> bool: return bool(ioctl(self.fd, LOCK_CTL, "IIB3xB3x", 4, LOCK_TEST, CHIP_IN_USE, 0)[-1] & 2)
  def reset(self, flag:int) -> bool: return ioctl(self.fd, RESET_DEVICE, "IIII", 8, flag, 0, 0)[-1] == 0
  def vote_idle(self): set_power(self.fd, 0)
  def close(self): os.close(self.fd)
