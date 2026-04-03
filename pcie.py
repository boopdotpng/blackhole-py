"""Direct PCIe access to Tenstorrent Blackhole via VFIO."""
import ctypes, ctypes.util, fcntl, glob, mmap, os, struct, time

TT_VENDOR = 0x1E52
BH_DEVICE = 0xB140
PCI_COMMAND = 0x04
PCI_COMMAND_MEMORY = 0x02
PCI_COMMAND_MASTER = 0x04

# VFIO ioctl numbers
VFIO_TYPE = ord(';')
_VFIO_IO = lambda nr: (VFIO_TYPE << 8) | (100 + nr)
VFIO_GET_API_VERSION     = _VFIO_IO(0)
VFIO_CHECK_EXTENSION     = _VFIO_IO(1)
VFIO_SET_IOMMU           = _VFIO_IO(2)
VFIO_GROUP_GET_STATUS    = _VFIO_IO(3)
VFIO_GROUP_SET_CONTAINER = _VFIO_IO(4)
VFIO_GROUP_GET_DEVICE_FD = _VFIO_IO(6)
VFIO_IOMMU_MAP_DMA       = _VFIO_IO(13)
VFIO_IOMMU_UNMAP_DMA     = _VFIO_IO(14)
VFIO_TYPE1v2_IOMMU     = 3
VFIO_DMA_MAP_FLAG_READ  = 1
VFIO_DMA_MAP_FLAG_WRITE = 2
VFIO_GROUP_FLAGS_VIABLE = 1

# BAR0 layout
BAR0_SIZE         = 1 << 29           # 512 MB
TLB_2M_COUNT      = 202
TLB_4G_COUNT      = 8
TLB_2M_SIZE       = 1 << 21
TLB_4G_SIZE       = 1 << 32
TLB_REG_SIZE      = 12
TLB_REGS_START    = 0x1FC00000
TLB_REGS_LEN      = 0x1000
TLB_STRIDE_OFFSET = (TLB_2M_COUNT + TLB_4G_COUNT) * TLB_REG_SIZE

# BAR2 layout (iATU for DMA)
IATU_BASE              = 0x1000
IATU_REGION_STRIDE     = 0x200
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

NOC_PCIE_OFFSET = 4 << 58

_libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)

def _mlock(addr: int, size: int):
  if _libc.mlock(ctypes.c_void_p(addr), ctypes.c_size_t(size)) != 0:
    raise OSError(ctypes.get_errno(), "mlock failed — run setup_python_cap.sh to grant CAP_IPC_LOCK")

def _munlock(addr: int, size: int):
  _libc.munlock(ctypes.c_void_p(addr), ctypes.c_size_t(size))


def _find_bh_devices() -> list[str]:
  result = []
  for path in sorted(glob.glob("/sys/bus/pci/devices/*")):
    vendor = int(open(f"{path}/vendor").read(), 16)
    device = int(open(f"{path}/device").read(), 16)
    if vendor == TT_VENDOR and device == BH_DEVICE:
      result.append(path)
  return result


def _bind_vfio_pci(sysfs_path: str):
  bdf = os.path.basename(sysfs_path)
  driver_link = f"{sysfs_path}/driver"

  if os.path.islink(driver_link):
    current = os.path.basename(os.readlink(driver_link))
    if current == "vfio-pci":
      return
    with open(f"{sysfs_path}/driver/unbind", "w") as f:
      f.write(bdf)

  with open(f"{sysfs_path}/driver_override", "w") as f:
    f.write("vfio-pci")
  with open("/sys/bus/pci/drivers_probe", "w") as f:
    f.write(bdf)

  for _ in range(50):
    if os.path.islink(driver_link) and os.path.basename(os.readlink(driver_link)) == "vfio-pci":
      return
    time.sleep(0.1)

  raise RuntimeError(
    f"failed to bind {bdf} to vfio-pci. Is the vfio-pci module loaded? Try: modprobe vfio-pci")


def _mmap_bar(sysfs, resource, size):
  fd = os.open(f"{sysfs}/{resource}", os.O_RDWR | os.O_SYNC)
  mm = mmap.mmap(fd, size, flags=mmap.MAP_SHARED, prot=mmap.PROT_READ | mmap.PROT_WRITE)
  return fd, mm


class PCIDevice:
  def __init__(self, index: int = 0):
    devices = _find_bh_devices()
    if index >= len(devices):
      raise RuntimeError(f"Blackhole device {index} not found (found {len(devices)})")
    self.sysfs = devices[index]
    self.bdf = os.path.basename(self.sysfs)

    # Enable PCI device, memory space, bus mastering
    with open(f"{self.sysfs}/enable", "r+") as f:
      if f.read().strip() != "1":
        f.seek(0); f.write("1"); f.truncate()
    fd = os.open(f"{self.sysfs}/config", os.O_RDWR)
    os.lseek(fd, PCI_COMMAND, os.SEEK_SET)
    cmd = struct.unpack("<H", os.read(fd, 2))[0]
    want = PCI_COMMAND_MEMORY | PCI_COMMAND_MASTER
    if (cmd & want) != want:
      os.lseek(fd, PCI_COMMAND, os.SEEK_SET)
      os.write(fd, struct.pack("<H", cmd | want))
    os.close(fd)

    # Bind to vfio-pci
    self._setup_vfio()

    # mmap BARs
    self._bar0_fd, self.bar0 = _mmap_bar(self.sysfs, "resource0", BAR0_SIZE)
    self._bar0_wc_fd, self.bar0_wc = _mmap_bar(self.sysfs, "resource0_wc", BAR0_SIZE)
    self._bar2_fd, self.bar2 = _mmap_bar(self.sysfs, "resource2", 1 << 20)

    self._bar4_fd = os.open(f"{self.sysfs}/resource4", os.O_RDWR | os.O_SYNC)
    bar4_size = os.fstat(self._bar4_fd).st_size
    self._bar4_4g_count = min(TLB_4G_COUNT, bar4_size // TLB_4G_SIZE) if bar4_size else 0
    if bar4_size:
      self.bar4 = mmap.mmap(self._bar4_fd, bar4_size, flags=mmap.MAP_SHARED,
                            prot=mmap.PROT_READ | mmap.PROT_WRITE)
      self._bar4_wc_fd = os.open(f"{self.sysfs}/resource4_wc", os.O_RDWR | os.O_SYNC)
      self.bar4_wc = mmap.mmap(self._bar4_wc_fd, bar4_size, flags=mmap.MAP_SHARED,
                               prot=mmap.PROT_READ | mmap.PROT_WRITE)
    else:
      self.bar4 = self.bar4_wc = None
      self._bar4_wc_fd = -1

    # TLB allocation bitmaps
    self._tlb_2m = [False] * TLB_2M_COUNT
    self._tlb_2m[TLB_2M_COUNT - 1] = True  # reserve index 201
    self._tlb_4g = [False] * self._bar4_4g_count

    # iATU region allocation
    self._iatu_regions = [False] * IATU_OUTBOUND_REGIONS

    # DMA pinning state
    self._pinnings: dict[int, dict] = {}
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
    with open(f"/sys/bus/pci/devices/{bdf}/reset", "w") as f:
      f.write("1\n")

  def _setup_vfio(self):
    _bind_vfio_pci(self.sysfs)
    self._vfio_container = os.open("/dev/vfio/vfio", os.O_RDWR)
    assert fcntl.ioctl(self._vfio_container, VFIO_GET_API_VERSION, 0) == 0

    group_id = int(os.path.basename(os.readlink(f"{self.sysfs}/iommu_group")))
    self._vfio_group = os.open(f"/dev/vfio/{group_id}", os.O_RDWR)

    status = bytearray(struct.pack("=II", 8, 0))
    fcntl.ioctl(self._vfio_group, VFIO_GROUP_GET_STATUS, status)
    _, flags = struct.unpack("=II", status)
    if not (flags & VFIO_GROUP_FLAGS_VIABLE):
      raise RuntimeError(f"VFIO group {group_id} not viable — all devices must be bound to vfio-pci")

    fcntl.ioctl(self._vfio_group, VFIO_GROUP_SET_CONTAINER,
                struct.pack("=i", self._vfio_container))
    fcntl.ioctl(self._vfio_container, VFIO_SET_IOMMU, VFIO_TYPE1v2_IOMMU)

    bdf_bytes = bytearray(self.bdf.encode() + b'\x00')
    self._vfio_device = fcntl.ioctl(self._vfio_group, VFIO_GROUP_GET_DEVICE_FD, bdf_bytes, True)

  def _bring_device_to_a0(self):
    """Bring ASIC from A3 to A0 if ARC is running."""
    deadline = time.monotonic() + 0.5
    while time.monotonic() < deadline:
      boot_status = self.read_arc_apb32(self.SCRATCH_RAM_2)
      if (boot_status & self.ARC_BOOT_STATUS_STARTED_MASK) == self.ARC_BOOT_STATUS_STARTED_VALUE:
        self.arc_msg(0xA0, timeout_ms=200)
        try: self.arc_msg(self.MSG_SET_WDT_TIMEOUT, arg0=60_000, timeout_ms=200)
        except Exception: pass
        return
      time.sleep(0.00001)

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
      self.configure_tlb(tlb, base, *self.ARC_TILE, *self.ARC_TILE, ordering=1)
      bar, bar_off = self.tlb_window(tlb)
      return struct.unpack_from("<I", bar, bar_off + (addr - base))[0]
    finally:
      if owns_tlb:
        self.free_tlb(tlb)

  def telemetry_layout(self) -> dict:
    if self._telemetry_layout is not None:
      return self._telemetry_layout

    table_base = self.read_arc_apb32(self.SCRATCH_RAM_13)
    data_base = self.read_arc_apb32(self.SCRATCH_RAM_12)
    if table_base in (0, 0xFFFFFFFF) or data_base in (0, 0xFFFFFFFF):
      raise RuntimeError(f"invalid ARC telemetry pointers table=0x{table_base:x} data=0x{data_base:x}")

    tlb = self.alloc_tlb(TLB_2M_SIZE)
    try:
      version = self._read_arc_noc32(table_base, tlb=tlb)
      entry_count = self._read_arc_noc32(table_base + 4, tlb=tlb)
      tag_to_offset = {}
      for i in range(entry_count):
        tag_offset = self._read_arc_noc32(table_base + 8 + i * 4, tlb=tlb)
        tag_to_offset[tag_offset & 0xFFFF] = (tag_offset >> 16) & 0xFFFF
    finally:
      self.free_tlb(tlb)

    self._telemetry_layout = {
      "version": version, "table_base": table_base, "data_base": data_base,
      "entry_count": entry_count, "tag_to_offset": tag_to_offset,
    }
    return self._telemetry_layout

  def telemetry_tags(self) -> list[int]:
    return sorted(self.telemetry_layout()["tag_to_offset"])

  def has_telemetry_tag(self, tag: int) -> bool:
    return tag in self.telemetry_layout()["tag_to_offset"]

  def read_telemetry_entry(self, tag: int) -> int:
    layout = self.telemetry_layout()
    return self._read_arc_noc32(layout["data_base"] + 4 * layout["tag_to_offset"][tag])

  def write_arc_apb32(self, offset: int, value: int):
    tlb = self.alloc_tlb(TLB_2M_SIZE)
    try:
      self.configure_tlb(tlb, self.ARC_NOC_BASE, *self.ARC_TILE, *self.ARC_TILE, ordering=1)
      bar, bar_off = self.tlb_window(tlb)
      struct.pack_into("<I", bar, bar_off + offset, value & 0xFFFFFFFF)
    finally:
      self.free_tlb(tlb)

  # ---- TLB allocation ----

  def alloc_tlb(self, size: int) -> int:
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
    raise ValueError(f"invalid TLB size: {size}")

  def free_tlb(self, index: int):
    if index < TLB_2M_COUNT:
      self._tlb_2m[index] = False
    else:
      self._tlb_4g[index - TLB_2M_COUNT] = False

  # ---- TLB configuration ----

  def configure_tlb(self, index: int, addr: int, x_start: int, y_start: int,
                    x_end: int, y_end: int, noc: int = 0, mcast: int = 0,
                    ordering: int = 1, linked: int = 0, static_vc: int = 0):
    reg_offset = TLB_REGS_START + index * TLB_REG_SIZE

    if index < TLB_2M_COUNT:
      local_offset = addr >> 21
      val = (local_offset
             | (x_end    << 43) | (y_end    << 49)
             | (x_start  << 55) | (y_start  << 61)
             | (noc      << 67) | (mcast    << 69)
             | (ordering << 70) | (linked   << 72) | (static_vc << 73))
    else:
      local_offset = addr >> 32
      val = (local_offset
             | (x_end    << 32) | (y_end    << 38)
             | (x_start  << 44) | (y_start  << 50)
             | (noc      << 56) | (mcast    << 58)
             | (ordering << 59) | (linked   << 61) | (static_vc << 62))

    self.bar0[reg_offset:reg_offset+4] = struct.pack("<I", val & 0xFFFFFFFF)
    self.bar0[reg_offset+4:reg_offset+8] = struct.pack("<I", (val >> 32) & 0xFFFFFFFF)
    self.bar0[reg_offset+8:reg_offset+12] = struct.pack("<I", (val >> 64) & 0xFFFFFFFF)

    if index < 32:
      stride_off = TLB_REGS_START + TLB_STRIDE_OFFSET + index * 4
      self.bar0[stride_off:stride_off+4] = b'\x00\x00\x00\x00'

  def tlb_window(self, index: int, wc: bool = False) -> tuple[mmap.mmap, int]:
    if index < TLB_2M_COUNT:
      return (self.bar0_wc if wc else self.bar0), index * TLB_2M_SIZE
    bar = self.bar4_wc if wc else self.bar4
    if bar is None:
      raise RuntimeError("BAR4 not available")
    return bar, (index - TLB_2M_COUNT) * TLB_4G_SIZE

  # ---- DMA / page pinning via VFIO IOMMU ----

  def pin_pages(self, buf: mmap.mmap) -> int:
    """Pin a buffer and set up IOMMU + iATU for device DMA. Returns the NOC address."""
    va = ctypes.addressof(ctypes.c_char.from_buffer(buf))
    size = len(buf)
    _mlock(va, size)

    iova = self._next_iova
    self._next_iova += size

    dma_map = struct.pack("=IIQQQ", 32,
      VFIO_DMA_MAP_FLAG_READ | VFIO_DMA_MAP_FLAG_WRITE, va, iova, size)
    fcntl.ioctl(self._vfio_container, VFIO_IOMMU_MAP_DMA, dma_map)

    region = self._alloc_iatu_region()
    noc_base = region * (1 << 30)
    self._configure_iatu(region, noc_base, noc_base + size - 1, iova)

    noc_addr = NOC_PCIE_OFFSET | noc_base
    self._pinnings[noc_addr] = {"iova": iova, "size": size, "iatu_region": region}
    return noc_addr

  def unpin_pages(self, buf: mmap.mmap, noc_addr: int):
    va = ctypes.addressof(ctypes.c_char.from_buffer(buf))
    pin = self._pinnings.pop(noc_addr)
    self._disable_iatu(pin["iatu_region"])
    self._iatu_regions[pin["iatu_region"]] = False
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
    return IATU_BASE + (2 * region) * (IATU_REGION_STRIDE // 2) + reg

  def _configure_iatu(self, region: int, base: int, limit: int, target: int):
    def w32(reg, val):
      off = self._iatu_reg(region, reg)
      self.bar2[off:off+4] = struct.pack("<I", val & 0xFFFFFFFF)
    w32(IATU_LOWER_BASE,   base & 0xFFFFFFFF)
    w32(IATU_UPPER_BASE,   base >> 32)
    w32(IATU_LOWER_TARGET, target & 0xFFFFFFFF)
    w32(IATU_UPPER_TARGET, target >> 32)
    w32(IATU_LOWER_LIMIT,  limit & 0xFFFFFFFF)
    w32(IATU_UPPER_LIMIT,  limit >> 32)
    w32(IATU_CTRL1,        IATU_CTRL1_INCREASE)
    w32(IATU_CTRL3,        0)
    w32(IATU_CTRL2,        IATU_CTRL2_ENABLE)

  def _disable_iatu(self, region: int):
    off = self._iatu_reg(region, IATU_CTRL2)
    self.bar2[off:off+4] = b'\x00\x00\x00\x00'

  # ---- ARC messaging ----

  ARC_TILE     = (8, 0)
  ARC_NOC_BASE = 0x80000000
  SCRATCH_RAM_2  = 0x30408
  SCRATCH_RAM_11 = 0x3042C
  SCRATCH_RAM_12 = 0x30430
  SCRATCH_RAM_13 = 0x30434
  ARC_MISC_CNTL  = 0x30100
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
        self.configure_tlb(tlb, base, *self.ARC_TILE, *self.ARC_TILE, ordering=1)
        bar, bar_off = self.tlb_window(tlb)
        return struct.unpack_from("<I", bar, bar_off + (noc_addr - base))[0]

      def _write32(noc_addr, val):
        base = noc_addr & ~(TLB_2M_SIZE - 1)
        self.configure_tlb(tlb, base, *self.ARC_TILE, *self.ARC_TILE, ordering=1)
        bar, bar_off = self.tlb_window(tlb)
        struct.pack_into("<I", bar, bar_off + (noc_addr - base), val)

      boot_status = self.read_arc_apb32(self.SCRATCH_RAM_2)
      if boot_status in (0, 0xFFFFFFFF) or not (boot_status & self.ARC_BOOT_STATUS_READY_FOR_MSG):
        raise RuntimeError(f"ARC not ready (boot_status=0x{boot_status:x})")

      qcb_ptr = self.read_arc_apb32(self.SCRATCH_RAM_11)
      queue_base = _read32(qcb_ptr)
      msg_queue_size = _read32(qcb_ptr + 4) & 0xFF
      msg_queue_pointer_wrap = 2 * msg_queue_size
      q = queue_base

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
          raise RuntimeError(f"ARC fw error 0x{status:x} for message 0x{msg:x}")
        time.sleep(0.001)
      raise TimeoutError(f"arc_msg timeout ({timeout_ms} ms) -- try tt-smi -r")
    finally:
      self.free_tlb(tlb)

  def set_power_state(self, busy: bool):
    if busy:
      self.arc_msg(self.MSG_AICLK_GO_BUSY)
    else:
      try: self.arc_msg(self.MSG_AICLK_GO_LONG_IDLE)
      except (TimeoutError, RuntimeError): pass

  def close(self):
    self.bar0.close(); self.bar0_wc.close(); self.bar2.close()
    if self.bar4: self.bar4.close()
    if self.bar4_wc: self.bar4_wc.close()
    os.close(self._bar0_fd); os.close(self._bar0_wc_fd)
    os.close(self._bar2_fd); os.close(self._bar4_fd)
    if self._bar4_wc_fd >= 0: os.close(self._bar4_wc_fd)
    os.close(self._vfio_device); os.close(self._vfio_group); os.close(self._vfio_container)

  def __enter__(self): return self
  def __exit__(self, *_): self.close()
