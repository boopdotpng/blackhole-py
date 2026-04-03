"""Direct PCIe access to Tenstorrent Blackhole, replacing tt-kmd ioctls."""
import ctypes, ctypes.util, fcntl, glob, mmap, os, struct, time

# ---- PCI constants ----
TT_VENDOR = 0x1E52
BH_DEVICE = 0xB140
PCI_COMMAND = 0x04
PCI_COMMAND_MEMORY = 0x02  # memory space enable
PCI_COMMAND_MASTER = 0x04  # bus mastering bit

# ---- VFIO constants ----
VFIO_TYPE = ord(';')
VFIO_BASE = 100
_VFIO_IO = lambda nr: (VFIO_TYPE << 8) | (VFIO_BASE + nr)

VFIO_GET_API_VERSION     = _VFIO_IO(0)
VFIO_CHECK_EXTENSION     = _VFIO_IO(1)
VFIO_SET_IOMMU           = _VFIO_IO(2)
VFIO_GROUP_GET_STATUS    = _VFIO_IO(3)
VFIO_GROUP_SET_CONTAINER = _VFIO_IO(4)
VFIO_GROUP_GET_DEVICE_FD = _VFIO_IO(6)
VFIO_IOMMU_MAP_DMA       = _VFIO_IO(13)
VFIO_IOMMU_UNMAP_DMA     = _VFIO_IO(14)

VFIO_API_VERSION       = 0
VFIO_TYPE1v2_IOMMU     = 3
VFIO_DMA_MAP_FLAG_READ  = 1
VFIO_DMA_MAP_FLAG_WRITE = 2
VFIO_GROUP_FLAGS_VIABLE = 1

# ---- BAR0 layout ----
BAR0_SIZE         = 1 << 29           # 512 MB
TLB_2M_COUNT      = 202
TLB_4G_COUNT      = 8
TLB_2M_SIZE       = 1 << 21           # 2 MB
TLB_4G_SIZE       = 1 << 32           # 4 GB
TLB_REG_SIZE      = 12                # bytes per TLB config entry
TLB_REGS_START    = 0x1FC00000        # BAR0 offset of TLB config registers
TLB_REGS_LEN      = 0x1000
TLB_STRIDE_OFFSET = (TLB_2M_COUNT + TLB_4G_COUNT) * TLB_REG_SIZE  # 0x9D8

# ---- BAR2 layout (iATU for DMA) ----
IATU_BASE              = 0x1000
IATU_REGION_STRIDE     = 0x200       # stride between outbound regions (2 * 0x100)
IATU_OUTBOUND_REGIONS  = 16
IATU_CTRL1             = 0x00
IATU_CTRL2             = 0x04
IATU_LOWER_BASE        = 0x08
IATU_UPPER_BASE        = 0x0C
IATU_LOWER_LIMIT       = 0x10
IATU_LOWER_TARGET      = 0x14
IATU_UPPER_TARGET      = 0x18
IATU_CTRL3             = 0x1C
IATU_UPPER_LIMIT       = 0x20
IATU_CTRL1_INCREASE    = 1 << 13
IATU_CTRL2_ENABLE      = 1 << 31

# ---- NOC constants ----
NOC_PCIE_OFFSET = 4 << 58            # host memory as seen on NOC

# ---- libc ----
_libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)

def _mlock(addr: int, size: int):
  if _libc.mlock(ctypes.c_void_p(addr), ctypes.c_size_t(size)) != 0:
    raise OSError(ctypes.get_errno(), "mlock failed")

def _munlock(addr: int, size: int):
  _libc.munlock(ctypes.c_void_p(addr), ctypes.c_size_t(size))


def _find_bh_devices() -> list[str]:
  """Find all Blackhole BDF paths in sysfs."""
  result = []
  for path in sorted(glob.glob("/sys/bus/pci/devices/*")):
    try:
      vendor = int(open(f"{path}/vendor").read(), 16)
      device = int(open(f"{path}/device").read(), 16)
      if vendor == TT_VENDOR and device == BH_DEVICE:
        result.append(path)
    except (OSError, ValueError):
      continue
  return result


def _iommu_group_for(sysfs_path: str) -> int:
  """Return the IOMMU group number for a PCI device."""
  link = os.readlink(f"{sysfs_path}/iommu_group")
  return int(os.path.basename(link))


def _bind_vfio_pci(sysfs_path: str):
  """Bind a PCI device to the vfio-pci driver if not already bound."""
  bdf = os.path.basename(sysfs_path)
  driver_link = f"{sysfs_path}/driver"

  if os.path.islink(driver_link):
    current = os.path.basename(os.readlink(driver_link))
    if current == "vfio-pci":
      return
    # unbind from current driver
    with open(f"{sysfs_path}/driver/unbind", "w") as f:
      f.write(bdf)

  # set driver_override so only vfio-pci claims it
  with open(f"{sysfs_path}/driver_override", "w") as f:
    f.write("vfio-pci")

  # probe to trigger bind
  with open("/sys/bus/pci/drivers_probe", "w") as f:
    f.write(bdf)

  # wait for bind
  for i in range(50):
    if os.path.islink(driver_link):
      current = os.path.basename(os.readlink(driver_link))
      if current == "vfio-pci":
        return
    time.sleep(0.1)

  # diagnose failure
  bound_to = None
  if os.path.islink(driver_link):
    bound_to = os.path.basename(os.readlink(driver_link))
  override = ""
  try:
    override = open(f"{sysfs_path}/driver_override").read().strip()
  except OSError:
    pass
  raise RuntimeError(
    f"failed to bind {bdf} to vfio-pci "
    f"(currently bound to: {bound_to!r}, driver_override: {override!r}). "
    f"Is the vfio-pci module loaded? Try: modprobe vfio-pci")


class PCIDevice:
  def __init__(self, index: int = 0):
    devices = _find_bh_devices()
    if index >= len(devices):
      raise RuntimeError(f"Blackhole device {index} not found (found {len(devices)})")
    self.sysfs = devices[index]
    self.bdf = os.path.basename(self.sysfs)

    print(f"  pcie: found {self.bdf} at {self.sysfs}")

    # Enable device before binding to vfio-pci
    self._enable_device()
    self._enable_memory_and_bus_master()
    print(f"  pcie: device enabled, memory space + bus mastering enabled")

    # Bind to vfio-pci and set up IOMMU container
    self._setup_vfio()
    print(f"  pcie: bound to vfio-pci, IOMMU container ready")

    # mmap BAR0: full 512MB for TLB windows
    self._bar0_fd = os.open(f"{self.sysfs}/resource0", os.O_RDWR | os.O_SYNC)
    self.bar0 = mmap.mmap(self._bar0_fd, BAR0_SIZE, flags=mmap.MAP_SHARED,
                          prot=mmap.PROT_READ | mmap.PROT_WRITE)

    # mmap BAR0 write-combining (for bulk transfers)
    self._bar0_wc_fd = os.open(f"{self.sysfs}/resource0_wc", os.O_RDWR | os.O_SYNC)
    self.bar0_wc = mmap.mmap(self._bar0_wc_fd, BAR0_SIZE, flags=mmap.MAP_SHARED,
                             prot=mmap.PROT_READ | mmap.PROT_WRITE)

    # mmap BAR2: iATU registers (1MB)
    self._bar2_fd = os.open(f"{self.sysfs}/resource2", os.O_RDWR | os.O_SYNC)
    self.bar2 = mmap.mmap(self._bar2_fd, 1 << 20, flags=mmap.MAP_SHARED,
                          prot=mmap.PROT_READ | mmap.PROT_WRITE)

    # mmap BAR4: 4G TLB windows (UC + WC)
    self._bar4_fd = os.open(f"{self.sysfs}/resource4", os.O_RDWR | os.O_SYNC)
    bar4_size = os.fstat(self._bar4_fd).st_size
    self._bar4_4g_count = min(TLB_4G_COUNT, bar4_size // TLB_4G_SIZE) if bar4_size else 0
    self.bar4 = mmap.mmap(self._bar4_fd, bar4_size, flags=mmap.MAP_SHARED,
                          prot=mmap.PROT_READ | mmap.PROT_WRITE) if bar4_size else None

    self._bar4_wc_fd = os.open(f"{self.sysfs}/resource4_wc", os.O_RDWR | os.O_SYNC) if bar4_size else -1
    self.bar4_wc = mmap.mmap(self._bar4_wc_fd, bar4_size, flags=mmap.MAP_SHARED,
                             prot=mmap.PROT_READ | mmap.PROT_WRITE) if bar4_size else None

    print(f"  pcie: BAR0={BAR0_SIZE>>20}MB  BAR2={1}MB  BAR4={bar4_size>>30}GB ({self._bar4_4g_count} 4G windows)")

    # TLB allocation bitmap: False = free, True = allocated
    self._tlb_2m = [False] * TLB_2M_COUNT
    self._tlb_2m[TLB_2M_COUNT - 1] = True  # reserve index 201 (kernel-style)

    self._tlb_4g = [False] * self._bar4_4g_count

    # iATU region allocation
    self._iatu_regions = [False] * IATU_OUTBOUND_REGIONS

    # VFIO DMA pinning state: noc_addr -> {iova, size, iatu_region}
    self._pinnings: dict[int, dict] = {}
    # Simple IOVA bump allocator (start at 1GB to avoid IOVA 0)
    self._next_iova = 1 << 30

    self._telemetry_layout = None

    self._bring_device_to_a0()

  @staticmethod
  def list_devices() -> list[str]:
    return _find_bh_devices()

  @classmethod
  def reset_index(cls, index: int = 0):
    devices = cls.list_devices()
    if index >= len(devices):
      raise RuntimeError(f"Blackhole device {index} not found (found {len(devices)})")
    cls.reset_bdf(os.path.basename(devices[index]))

  @staticmethod
  def reset_bdf(bdf: str):
    reset_path = f"/sys/bus/pci/devices/{bdf}/reset"
    try:
      with open(reset_path, "w") as f:
        f.write("1\n")
    except OSError as e:
      raise OSError(e.errno, f"failed to reset PCI device via {reset_path}: {e.strerror}") from e

  def _enable_device(self):
    """Best-effort sysfs equivalent of pci_enable_device()."""
    enable_path = f"{self.sysfs}/enable"
    try:
      with open(enable_path, "r+") as f:
        value = f.read().strip()
        if value != "1":
          f.seek(0)
          f.write("1")
          f.truncate()
    except OSError as e:
      raise OSError(e.errno, f"failed to enable PCI device via {enable_path}: {e.strerror}") from e

  def _enable_memory_and_bus_master(self):
    """Set PCI memory-space and bus-master bits in the command register."""
    config_path = f"{self.sysfs}/config"
    fd = os.open(config_path, os.O_RDWR)
    try:
      os.lseek(fd, PCI_COMMAND, os.SEEK_SET)
      cmd = struct.unpack("<H", os.read(fd, 2))[0]
      want = PCI_COMMAND_MEMORY | PCI_COMMAND_MASTER
      if (cmd & want) != want:
        os.lseek(fd, PCI_COMMAND, os.SEEK_SET)
        os.write(fd, struct.pack("<H", cmd | want))
    finally:
      os.close(fd)

  def _setup_vfio(self):
    """Bind device to vfio-pci and set up the IOMMU container for DMA mapping."""
    _bind_vfio_pci(self.sysfs)

    # open VFIO container
    self._vfio_container = os.open("/dev/vfio/vfio", os.O_RDWR)
    api = fcntl.ioctl(self._vfio_container, VFIO_GET_API_VERSION, 0)
    if api != VFIO_API_VERSION:
      raise RuntimeError(f"VFIO API version mismatch: got {api}, expected {VFIO_API_VERSION}")

    # open IOMMU group
    group_id = _iommu_group_for(self.sysfs)
    self._vfio_group = os.open(f"/dev/vfio/{group_id}", os.O_RDWR)

    # check group is viable
    status = bytearray(struct.pack("=II", 8, 0))
    fcntl.ioctl(self._vfio_group, VFIO_GROUP_GET_STATUS, status)
    _, flags = struct.unpack("=II", status)
    if not (flags & VFIO_GROUP_FLAGS_VIABLE):
      raise RuntimeError(
        f"VFIO group {group_id} is not viable — all devices in the group must be "
        "bound to vfio-pci or have no driver")

    # attach group to container
    fcntl.ioctl(self._vfio_group, VFIO_GROUP_SET_CONTAINER,
                struct.pack("=i", self._vfio_container))

    # set IOMMU type
    fcntl.ioctl(self._vfio_container, VFIO_SET_IOMMU, VFIO_TYPE1v2_IOMMU)

    # get device fd (needed for VFIO to fully own the device)
    # GET_DEVICE_FD returns the fd as the ioctl return value when passed a mutable buffer
    bdf_bytes = bytearray(self.bdf.encode() + b'\x00')
    self._vfio_device = fcntl.ioctl(self._vfio_group, VFIO_GROUP_GET_DEVICE_FD, bdf_bytes, True)

  def _bring_device_to_a0(self):
    """Match the driver's init_hardware path after a module unload put the ASIC into A3."""
    try:
      self._wait_arc_core_start(timeout_ms=500)
      rc = self.arc_msg(0xA0, timeout_ms=200)
      print(f"  arc: ASIC_STATE0 acknowledged (rc=0x{rc:x})")
      try:
        self.arc_msg(self.MSG_SET_WDT_TIMEOUT, arg0=60_000, timeout_ms=200)
      except Exception:
        pass
    except Exception as e:
      print(f"  arc: ASIC_STATE0 bring-up skipped ({e})")

  def _wait_arc_core_start(self, timeout_ms: int = 500):
    deadline = time.monotonic() + timeout_ms / 1000
    boot_status = 0
    while time.monotonic() < deadline:
      boot_status = self.read_arc_apb32(self.SCRATCH_RAM_2)
      if (boot_status & self.ARC_BOOT_STATUS_STARTED_MASK) == self.ARC_BOOT_STATUS_STARTED_VALUE:
        return
      time.sleep(0.00001)
    raise TimeoutError(f"ARC core did not start (boot_status=0x{boot_status:x})")

  def read_arc_apb32(self, offset: int) -> int:
    tlb = self.alloc_tlb(TLB_2M_SIZE)
    try:
      self.configure_tlb(tlb, self.ARC_NOC_BASE, *self.ARC_TILE, *self.ARC_TILE, ordering=1)
      bar, bar_off = self.tlb_window(tlb)
      return struct.unpack_from("<I", bar, bar_off + offset)[0]
    finally:
      self.free_tlb(tlb)

  def _read_arc_noc32(self, addr: int, tlb: int | None = None) -> int:
    owns_tlb = tlb is None
    if owns_tlb:
      tlb = self.alloc_tlb(TLB_2M_SIZE)
    try:
      base = addr & ~(TLB_2M_SIZE - 1)
      off = addr - base
      self.configure_tlb(tlb, base, *self.ARC_TILE, *self.ARC_TILE, ordering=1)
      bar, bar_off = self.tlb_window(tlb)
      return struct.unpack_from("<I", bar, bar_off + off)[0]
    finally:
      if owns_tlb:
        self.free_tlb(tlb)

  def telemetry_layout(self) -> dict:
    if self._telemetry_layout is not None:
      return self._telemetry_layout

    table_base = self.read_arc_apb32(self.SCRATCH_RAM_13)
    data_base = self.read_arc_apb32(self.SCRATCH_RAM_12)
    if table_base in (0, 0xFFFFFFFF) or data_base in (0, 0xFFFFFFFF):
      raise RuntimeError(
        f"invalid ARC telemetry pointers table=0x{table_base:x} data=0x{data_base:x}"
      )

    tlb = self.alloc_tlb(TLB_2M_SIZE)
    try:
      version = self._read_arc_noc32(table_base, tlb=tlb)
      entry_count = self._read_arc_noc32(table_base + 4, tlb=tlb)
      if entry_count in (0, 0xFFFFFFFF) or entry_count > 4096:
        raise RuntimeError(f"invalid ARC telemetry entry_count 0x{entry_count:x} at 0x{table_base:x}")

      tag_to_offset = {}
      for i in range(entry_count):
        tag_offset = self._read_arc_noc32(table_base + 8 + i * 4, tlb=tlb)
        tag_to_offset[tag_offset & 0xFFFF] = (tag_offset >> 16) & 0xFFFF
    finally:
      self.free_tlb(tlb)

    self._telemetry_layout = {
      "version": version,
      "table_base": table_base,
      "data_base": data_base,
      "entry_count": entry_count,
      "tag_to_offset": tag_to_offset,
    }
    return self._telemetry_layout

  def telemetry_tags(self) -> list[int]:
    return sorted(self.telemetry_layout()["tag_to_offset"])

  def has_telemetry_tag(self, tag: int) -> bool:
    return tag in self.telemetry_layout()["tag_to_offset"]

  def read_telemetry_entry(self, tag: int) -> int:
    layout = self.telemetry_layout()
    if tag not in layout["tag_to_offset"]:
      raise KeyError(f"telemetry tag {tag} not available")
    return self._read_arc_noc32(layout["data_base"] + 4 * layout["tag_to_offset"][tag])

  def write_arc_apb32(self, offset: int, value: int):
    tlb = self.alloc_tlb(TLB_2M_SIZE)
    try:
      self.configure_tlb(tlb, self.ARC_NOC_BASE, *self.ARC_TILE, *self.ARC_TILE, ordering=1)
      bar, bar_off = self.tlb_window(tlb)
      struct.pack_into("<I", bar, bar_off + offset, value & 0xFFFFFFFF)
    finally:
      self.free_tlb(tlb)

  # ---- TLB allocation (replaces TENSTORRENT_IOCTL_ALLOCATE_TLB) ----

  def alloc_tlb(self, size: int) -> int:
    """Allocate a TLB slot. Returns the TLB index."""
    if size == TLB_2M_SIZE:
      for i, used in enumerate(self._tlb_2m):
        if not used:
          self._tlb_2m[i] = True
          return i
      raise RuntimeError("no free 2M TLB slots")
    elif size == TLB_4G_SIZE:
      for i, used in enumerate(self._tlb_4g):
        if not used:
          self._tlb_4g[i] = True
          return TLB_2M_COUNT + i
      raise RuntimeError("no free 4G TLB slots")
    else:
      raise ValueError(f"invalid TLB size: {size}")

  def free_tlb(self, index: int):
    """Free a TLB slot."""
    if index < TLB_2M_COUNT:
      self._tlb_2m[index] = False
    else:
      self._tlb_4g[index - TLB_2M_COUNT] = False

  # ---- TLB configuration (replaces TENSTORRENT_IOCTL_CONFIGURE_TLB) ----

  def configure_tlb(self, index: int, addr: int, x_start: int, y_start: int,
                    x_end: int, y_end: int, noc: int = 0, mcast: int = 0,
                    ordering: int = 1, linked: int = 0, static_vc: int = 0):
    """Write TLB configuration registers directly to BAR0."""
    reg_offset = TLB_REGS_START + index * TLB_REG_SIZE

    if index < TLB_2M_COUNT:
      # 2M TLB: 96-bit register
      assert addr & (TLB_2M_SIZE - 1) == 0, f"addr 0x{addr:x} not 2M-aligned"
      local_offset = addr >> 21
      val = (local_offset
             | (x_end    << 43)
             | (y_end    << 49)
             | (x_start  << 55)
             | (y_start  << 61)
             | (noc      << 67)
             | (mcast    << 69)
             | (ordering << 70)
             | (linked   << 72)
             | (static_vc << 73))
    else:
      # 4G TLB: 96-bit register
      assert addr & (TLB_4G_SIZE - 1) == 0, f"addr 0x{addr:x} not 4G-aligned"
      local_offset = addr >> 32
      val = (local_offset
             | (x_end    << 32)
             | (y_end    << 38)
             | (x_start  << 44)
             | (y_start  << 50)
             | (noc      << 56)
             | (mcast    << 58)
             | (ordering << 59)
             | (linked   << 61)
             | (static_vc << 62))

    low32  = val & 0xFFFFFFFF
    mid32  = (val >> 32) & 0xFFFFFFFF
    high32 = (val >> 64) & 0xFFFFFFFF
    self.bar0[reg_offset:reg_offset + 4] = struct.pack("<I", low32)
    self.bar0[reg_offset + 4:reg_offset + 8] = struct.pack("<I", mid32)
    self.bar0[reg_offset + 8:reg_offset + 12] = struct.pack("<I", high32)

    # clear strided register for first 32 2M TLBs
    if index < 32:
      stride_off = TLB_REGS_START + TLB_STRIDE_OFFSET + index * 4
      self.bar0[stride_off:stride_off + 4] = b'\x00\x00\x00\x00'

  def tlb_window(self, index: int, wc: bool = False) -> tuple[mmap.mmap, int]:
    """Return (bar_mmap, base_offset) for a TLB aperture window.
    UC for register access / strict ordering. WC for bulk data transfers."""
    if index < TLB_2M_COUNT:
      bar = self.bar0_wc if wc else self.bar0
      return bar, index * TLB_2M_SIZE
    else:
      bar = self.bar4_wc if wc else self.bar4
      if bar is None:
        raise RuntimeError("BAR4 not available")
      return bar, (index - TLB_2M_COUNT) * TLB_4G_SIZE

  # ---- DMA / page pinning via VFIO IOMMU ----

  def pin_pages(self, buf: mmap.mmap) -> int:
    """Pin a buffer and set up IOMMU + iATU so the device can DMA to it.
    The IOMMU maps scattered physical pages as a contiguous IOVA range,
    then one iATU outbound region maps a NOC address window to that IOVA.
    Returns the NOC address the device should use."""
    va = ctypes.addressof(ctypes.c_char.from_buffer(buf))
    size = len(buf)

    # pin physical pages in RAM
    _mlock(va, size)

    # allocate a contiguous IOVA range
    iova = self._next_iova
    self._next_iova += size

    # map via VFIO IOMMU: the IOMMU builds the page table that translates
    # this contiguous IOVA range to the scattered physical pages
    #   struct vfio_iommu_type1_dma_map { u32 argsz, u32 flags, u64 vaddr, u64 iova, u64 size }
    dma_map = struct.pack("=IIQQQ",
      32,  # argsz
      VFIO_DMA_MAP_FLAG_READ | VFIO_DMA_MAP_FLAG_WRITE,
      va, iova, size)
    fcntl.ioctl(self._vfio_container, VFIO_IOMMU_MAP_DMA, dma_map)

    # allocate an iATU outbound region
    region = self._alloc_iatu_region()

    # choose a NOC-side base address for this mapping
    noc_base = region * (1 << 30)

    # program iATU: NOC address range -> IOVA (not physical!)
    # the IOMMU hardware translates IOVA -> physical on every PCIe TLP
    self._configure_iatu(region, noc_base, noc_base + size - 1, iova)

    noc_addr = NOC_PCIE_OFFSET | noc_base
    self._pinnings[noc_addr] = {"iova": iova, "size": size, "iatu_region": region}
    return noc_addr

  def unpin_pages(self, buf: mmap.mmap, noc_addr: int):
    """Unpin a buffer, tear down IOMMU mapping and iATU region."""
    va = ctypes.addressof(ctypes.c_char.from_buffer(buf))
    pin = self._pinnings.pop(noc_addr)

    # disable iATU region
    self._disable_iatu(pin["iatu_region"])
    self._iatu_regions[pin["iatu_region"]] = False

    # unmap from IOMMU
    #   struct vfio_iommu_type1_dma_unmap { u32 argsz, u32 flags, u64 iova, u64 size }
    dma_unmap = struct.pack("=IIQQ", 24, 0, pin["iova"], pin["size"])
    fcntl.ioctl(self._vfio_container, VFIO_IOMMU_UNMAP_DMA, dma_unmap)

    _munlock(va, pin["size"])

  def _alloc_iatu_region(self) -> int:
    for i, used in enumerate(self._iatu_regions):
      if not used:
        self._iatu_regions[i] = True
        return i
    raise RuntimeError("no free iATU regions")

  def _iatu_reg(self, region: int, reg: int) -> int:
    """Byte offset in BAR2 for an outbound iATU register."""
    return IATU_BASE + (2 * region) * (IATU_REGION_STRIDE // 2) + reg

  def _configure_iatu(self, region: int, base: int, limit: int, target: int):
    """Program one iATU outbound region in BAR2."""
    def w32(reg, val):
      off = self._iatu_reg(region, reg)
      self.bar2[off:off + 4] = struct.pack("<I", val & 0xFFFFFFFF)

    w32(IATU_LOWER_BASE,   base & 0xFFFFFFFF)
    w32(IATU_UPPER_BASE,   base >> 32)
    w32(IATU_LOWER_TARGET, target & 0xFFFFFFFF)
    w32(IATU_UPPER_TARGET, target >> 32)
    w32(IATU_LOWER_LIMIT,  limit & 0xFFFFFFFF)
    w32(IATU_UPPER_LIMIT,  limit >> 32)
    w32(IATU_CTRL1,        IATU_CTRL1_INCREASE)
    w32(IATU_CTRL3,        0)
    w32(IATU_CTRL2,        IATU_CTRL2_ENABLE)  # enable last

  def _disable_iatu(self, region: int):
    off = self._iatu_reg(region, IATU_CTRL2)
    self.bar2[off:off + 4] = b'\x00\x00\x00\x00'

  # ---- ARC messaging (ported from old arc_msg that worked before ioctl switch) ----

  ARC_TILE     = (8, 0)
  ARC_NOC_BASE = 0x80000000
  SCRATCH_RAM_2  = 0x30408   # offset from ARC_NOC_BASE
  SCRATCH_RAM_11 = 0x3042C   # offset from ARC_NOC_BASE
  SCRATCH_RAM_12 = 0x30430   # offset from ARC_NOC_BASE
  SCRATCH_RAM_13 = 0x30434   # offset from ARC_NOC_BASE
  ARC_MISC_CNTL  = 0x30100   # offset from ARC_NOC_BASE
  IRQ0_TRIG      = 1 << 16
  ARC_BOOT_STATUS_READY_FOR_MSG = 0x1
  ARC_BOOT_STATUS_STARTED_MASK  = 0x7
  ARC_BOOT_STATUS_STARTED_VALUE = 0x5
  MSG_AICLK_GO_BUSY      = 0x52
  MSG_AICLK_GO_LONG_IDLE = 0x54
  MSG_SET_WDT_TIMEOUT    = 0xC1
  ARC_MSG_RESPONSE_OK_LIMIT = 240

  def arc_msg(self, msg: int, arg0: int = 0, arg1: int = 0, timeout_ms: int = 1000) -> int:
    REQUEST_MSG_LEN, RESPONSE_MSG_LEN = 8, 8
    HEADER_BYTES = 8 * 4
    REQUEST_BYTES, RESPONSE_BYTES = REQUEST_MSG_LEN * 4, RESPONSE_MSG_LEN * 4
    REQUEST_WPTR_OFF = 0
    RESPONSE_RPTR_OFF = 4
    RESPONSE_WPTR_OFF = 20

    tlb = self.alloc_tlb(TLB_2M_SIZE)
    try:
      def _read32(noc_addr):
        base = noc_addr & ~(TLB_2M_SIZE - 1)
        off = noc_addr - base
        self.configure_tlb(tlb, base, *self.ARC_TILE, *self.ARC_TILE, ordering=1)
        bar, bar_off = self.tlb_window(tlb)
        return struct.unpack_from("<I", bar, bar_off + off)[0]

      def _write32(noc_addr, val):
        base = noc_addr & ~(TLB_2M_SIZE - 1)
        off = noc_addr - base
        self.configure_tlb(tlb, base, *self.ARC_TILE, *self.ARC_TILE, ordering=1)
        bar, bar_off = self.tlb_window(tlb)
        struct.pack_into("<I", bar, bar_off + off, val)

      boot_status = self.read_arc_apb32(self.SCRATCH_RAM_2)
      if boot_status in (0, 0xFFFFFFFF) or not (boot_status & self.ARC_BOOT_STATUS_READY_FOR_MSG):
        raise RuntimeError(f"ARC not ready for messages (boot_status=0x{boot_status:x})")

      qcb_ptr = self.read_arc_apb32(self.SCRATCH_RAM_11)
      if qcb_ptr in (0, 0xFFFFFFFF):
        raise RuntimeError(f"msgqueue control block unavailable (SCRATCH_RAM_11=0x{qcb_ptr:x})")

      queue_base = _read32(qcb_ptr)
      queue_info = _read32(qcb_ptr + 4)
      msg_queue_size = queue_info & 0xFF
      if msg_queue_size in (0, 0xFF):
        raise RuntimeError(f"invalid ARC msg queue size 0x{msg_queue_size:x} (qcb=0x{qcb_ptr:x})")
      msg_queue_pointer_wrap = 2 * msg_queue_size
      q = queue_base  # application queue 0

      # read wptr, write request message
      wptr = _read32(q + REQUEST_WPTR_OFF)
      req = q + HEADER_BYTES + (wptr % msg_queue_size) * REQUEST_BYTES
      words = [msg & 0xFF, arg0 & 0xFFFFFFFF, arg1 & 0xFFFFFFFF] + [0] * (REQUEST_MSG_LEN - 3)
      for i, w in enumerate(words):
        _write32(req + i * 4, w)
      _write32(q + REQUEST_WPTR_OFF, (wptr + 1) % msg_queue_pointer_wrap)

      # trigger ARC IRQ0
      misc = self.read_arc_apb32(self.ARC_MISC_CNTL)
      self.write_arc_apb32(self.ARC_MISC_CNTL, misc | self.IRQ0_TRIG)

      # poll for response
      rptr = _read32(q + RESPONSE_RPTR_OFF)
      deadline = time.monotonic() + timeout_ms / 1000
      while time.monotonic() < deadline:
        if _read32(q + RESPONSE_WPTR_OFF) != rptr:
          resp = q + HEADER_BYTES + msg_queue_size * REQUEST_BYTES + (rptr % msg_queue_size) * RESPONSE_BYTES
          out = [_read32(resp + i * 4) for i in range(RESPONSE_MSG_LEN)]
          _write32(q + RESPONSE_RPTR_OFF, (rptr + 1) % msg_queue_pointer_wrap)
          status = out[0] & 0xFF
          if status < self.ARC_MSG_RESPONSE_OK_LIMIT:
            return (out[0] >> 16) & 0xFFFFFFFF
          if status == 0xFF:
            raise RuntimeError(f"ARC fw did not recognize message 0x{msg:x}")
          raise RuntimeError(f"ARC fw returned error status 0x{status:x} for message 0x{msg:x}")
        time.sleep(0.001)
      raise TimeoutError(f"arc_msg timeout ({timeout_ms} ms) -- try tt-smi -r")
    finally:
      self.free_tlb(tlb)

  def set_power_state(self, busy: bool):
    if busy:
      self.arc_msg(self.MSG_AICLK_GO_BUSY)
    else:
      try:
        self.arc_msg(self.MSG_AICLK_GO_LONG_IDLE)
      except (TimeoutError, RuntimeError):
        pass

  def close(self):
    self.bar0.close()
    self.bar0_wc.close()
    self.bar2.close()
    if self.bar4:
      self.bar4.close()
    if self.bar4_wc:
      self.bar4_wc.close()
    os.close(self._bar0_fd)
    os.close(self._bar0_wc_fd)
    os.close(self._bar2_fd)
    os.close(self._bar4_fd)
    if self._bar4_wc_fd >= 0:
      os.close(self._bar4_wc_fd)
    # VFIO cleanup
    if hasattr(self, '_vfio_device') and self._vfio_device >= 0:
      os.close(self._vfio_device)
    if hasattr(self, '_vfio_group') and self._vfio_group >= 0:
      os.close(self._vfio_group)
    if hasattr(self, '_vfio_container') and self._vfio_container >= 0:
      os.close(self._vfio_container)

  def __enter__(self): return self
  def __exit__(self, *_): self.close()
