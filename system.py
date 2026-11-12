import ctypes, fcntl, functools, mmap, os
from ctypes import c_uint8 as u8, c_uint16 as u16, c_uint32 as u32, c_uint64 as u64
from pathlib import Path
from helpers import PAGE, libc_mmap, libc_munmap, view_at

TENSTORRENT_IOCTL_MAGIC = 0xFA
TENSTORRENT_PIN_PAGES_NOC_DMA = 2 # map to outbound iatu
# power state flags
TT_POWER_FLAG_MAX_AI_CLK = 1 << 0
TT_POWER_FLAG_MRISC_PHY_WAKEUP = 1 << 1 # need for dram
TT_POWER_FLAG_TENSIX_ENABLE = 1 << 2
TT_POWER_VALIDITY = 15 | 0 << 4 # (flag count, settings count), not a mask. kmd treats flags past the count as ON
TT_NOC_ORDERING_STRICT = 1 # full AXI ordering. important for doorbells

def _do_ioctl(nr, typ, fd, **kwargs):
  fcntl.ioctl(fd, TENSTORRENT_IOCTL_MAGIC << 8 | nr, out := typ(**kwargs))
  return out
def ioctl(nr):
  def wrap(cls):
    fields = cls.__annotations__
    typ = type(cls.__name__, (ctypes.Structure,), {"_fields_": list(fields.items())})
    return functools.partial(_do_ioctl, nr, typ, **{k: v for k, v in vars(cls).items() if k in fields})
  return wrap

TLB_SIZE = 1 << 21  # the one 2 MiB window into the NoC, retargeted on demand

@ioctl(7)
class PIN_PAGES:
  output_size_bytes: u32 = 16
  flags: u32 = TENSTORRENT_PIN_PAGES_NOC_DMA
  virtual_address: u64
  size: u64
  # out
  physical_address: u64
  noc_address: u64

TENSTORRENT_LOCK_CTL_ACQUIRE = 0  # non-blocking, out value 1 = acquired
CHIP_IN_USE = 20  # UMD's per-card lock index, held while tt-metal has the chip started; kmd drops it on fd close

@ioctl(8)
class LOCK_CTL:
  output_size_bytes: u32 = 4
  flags: u32 = TENSTORRENT_LOCK_CTL_ACQUIRE
  index: u8
  reserved: u8 * 3
  # out
  value: u8
  out_reserved: u8 * 3

@ioctl(10)
class UNPIN_PAGES:
  virtual_address: u64
  size: u64
  reserved: u64

@ioctl(11)
class ALLOCATE_TLB:
  size: u64 = TLB_SIZE
  reserved: u64
  # out
  id: u32
  reserved0: u32
  mmap_offset_uc: u64
  mmap_offset_wc: u64
  reserved1: u64

@ioctl(13)
class CONFIGURE_TLB:
  id: u32
  reserved: u32
  addr: u64
  x_end: u16
  y_end: u16
  x_start: u16
  y_start: u16
  noc: u8 = 0
  mcast: u8
  ordering: u8 = TT_NOC_ORDERING_STRICT
  linked: u8 = 0
  static_vc: u8 = 0
  reserved0: u8 * 3
  reserved1: u32 * 2
  # out
  out_reserved: u64

@ioctl(15)
class SET_POWER_STATE:
  argsz: u32 = 40
  flags: u32 = 0
  reserved0: u8 = 0
  validity: u8 = TT_POWER_VALIDITY
  power_flags: u16
  power_settings: u16 * 14

def _pin(fd, addr, size): return PIN_PAGES(fd, virtual_address=addr, size=size).noc_address
def _unpin(fd, addr, size): UNPIN_PAGES(fd, virtual_address=addr, size=size)

class Sysmem:
  def __init__(self, fd, size):
    assert size % PAGE == 0
    self.fd, self.size, self.addr = fd, size, libc_mmap(size, flags=mmap.MAP_PRIVATE)
    try:
      self.mem = view_at(self.addr, size)
      self.noc_addr = _pin(fd, self.addr, size)
    except BaseException:
      libc_munmap(self.addr, size)
      raise

  def close(self):
    _unpin(self.fd, self.addr, self.size)
    libc_munmap(self.addr, self.size)

class PCIDevice:
  def __init__(self, index=0):
    iommu = Path(f"/sys/class/tenstorrent/tenstorrent!{index}/device/iommu_group/type")
    if not iommu.exists() or not iommu.read_text().startswith("DMA"):
      raise RuntimeError("enable iommu")
    self.card = Path(f"/sys/class/tenstorrent/tenstorrent!{index}/tt_card_type").read_text().strip()
    if self.card not in ("p150a", "p150b"): raise RuntimeError(f"unsupported card {self.card}, only p150 for now")
    self.fd = os.open(f"/dev/tenstorrent/{index}", os.O_RDWR | os.O_CLOEXEC | os.O_APPEND)
    try:
      if not LOCK_CTL(self.fd, index=CHIP_IN_USE).value:
        raise RuntimeError(f"/dev/tenstorrent/{index} is in use by another process (tt-metal or another blackhole-py)")
    except BaseException:
      os.close(self.fd)
      raise
    try:
      SET_POWER_STATE(self.fd, power_flags=TT_POWER_FLAG_MAX_AI_CLK |
                      TT_POWER_FLAG_MRISC_PHY_WAKEUP | TT_POWER_FLAG_TENSIX_ENABLE)
      tlb = ALLOCATE_TLB(self.fd)
      self.tlb_id, self.tlb_cfg, self.tlb_addr = tlb.id, None, libc_mmap(TLB_SIZE, self.fd, tlb.mmap_offset_uc)
    except BaseException:
      try: self.power_off()
      finally: os.close(self.fd)
      raise
    self.tlb = view_at(self.tlb_addr, TLB_SIZE)
    self.tlb32 = self.tlb.cast("I")
    self.windows = []

  def close(self):
    for addr in self.windows: libc_munmap(addr, TLB_SIZE)
    libc_munmap(self.tlb_addr, TLB_SIZE)
    try: self.power_off()
    finally: os.close(self.fd)

  def power_off(self): SET_POWER_STATE(self.fd, power_flags=0)

  def pin(self, addr:int, size:int) -> int: return _pin(self.fd, addr, size)
  def unpin(self, addr:int, size:int): _unpin(self.fd, addr, size)

  def window(self, core) -> memoryview:
    """u32 view of core's L1 through a TLB of its own, so polling it never retargets the shared one."""
    tlb = ALLOCATE_TLB(self.fd)
    CONFIGURE_TLB(self.fd, id=tlb.id, addr=0, x_start=core[0], y_start=core[1], x_end=core[0], y_end=core[1])
    self.windows.append(addr := libc_mmap(TLB_SIZE, self.fd, tlb.mmap_offset_uc))
    return view_at(addr, TLB_SIZE).cast("I")

  def _target(self, core, addr):
    base = addr & -TLB_SIZE
    if self.tlb_cfg != (core, base):
      mcast = isinstance(core[0], tuple)
      (x0, y0), (x1, y1) = core if mcast else (core, core)
      CONFIGURE_TLB(self.fd, id=self.tlb_id, addr=base, x_start=x0, y_start=y0, x_end=x1, y_end=y1, mcast=mcast)
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
