import ctypes, ctypes.util, fcntl, glob, mmap, os, struct, time
from dataclasses import dataclass
from enum import Enum

TT_VENDOR = 0x1E52
BH_DEVICE = 0xB140
PCI_COMMAND = 0x04
PCI_COMMAND_MEMORY = 0x02
PCI_COMMAND_MASTER = 0x04
PCI_VENDOR_ID = 0x00
PCI_CAP_PTR = 0x34
PCI_CAP_ID_EXP = 0x10
PCI_EXP_DEVCTL = 0x08
PCI_EXP_DEVCTL_READRQ = 0x7000
PCI_EXP_DEVCTL_READRQ_4096 = 0x5000
PCI_BRIDGE_CONTROL = 0x3E
PCI_BRIDGE_CTL_BUS_RESET = 1 << 6

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

Core = tuple[int, int]

TELEMETRY_TAGS = {
  "BOARD_ID_HIGH": 1,
  "BOARD_ID_LOW": 2,
  "ENABLED_TENSIX_COL": 34,
  "ENABLED_GDDR": 36,
}

BOARD_UPI_TO_NAME = {
  0x36: "p100", 0x43: "p100a", 0x40: "p150a", 0x41: "p150b", 0x42: "p150c",
  0x44: "p300b", 0x45: "p300a", 0x46: "p300c", 0x18: "n150", 0x14: "n300",
  0x35: "galaxy-wormhole", 0x47: "galaxy-blackhole",
}

# Blackhole harvesting layout matches UMD's HARVESTING_NOC_LOCATIONS.
TENSIX_X_LOCATIONS = (1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14, 15, 16)
HARVESTING_NOC_LOCATIONS = (1, 16, 2, 15, 3, 14, 4, 13, 5, 12, 6, 11, 7, 10)
DEFAULT_TENSIX_ENABLED = (1 << len(TENSIX_X_LOCATIONS)) - 1
DEFAULT_GDDR_ENABLED = 0xFF


def shuffle_tensix_harvesting_mask(physical_mask: int) -> int:
  out = 0
  for pos, noc_x in enumerate(HARVESTING_NOC_LOCATIONS):
    if (physical_mask >> pos) & 1:
      out |= 1 << TENSIX_X_LOCATIONS.index(noc_x)
  return out


def tensix_columns_from_enabled_mask(enabled_mask: int) -> tuple[int, ...]:
  harvesting_mask = shuffle_tensix_harvesting_mask((~enabled_mask) & 0x3FFF)
  return tuple(x for i, x in enumerate(TENSIX_X_LOCATIONS) if not ((harvesting_mask >> i) & 1))


def worker_cores_from_columns(columns: tuple[int, ...]) -> list[Core]:
  return [(x, y) for x in columns for y in range(2, 12)]


@dataclass(frozen=True)
class BoardInfo:
  board_id: int | None
  arch: str
  board: str
  enabled_tensix_col: int
  tensix_columns: tuple[int, ...]
  worker_cores: list[Core]
  program_cores: list[Core]
  enabled_gddr: int
  harvested_dram_bank: int | None
  prefetch_core: Core
  dispatch_core: Core

  @property
  def core_count(self) -> int:
    return len(self.worker_cores)

  @property
  def num_dram_banks(self) -> int:
    return 8 if self.harvested_dram_bank is None else 7

  @property
  def cq_cores(self) -> set[Core]:
    return {self.prefetch_core, self.dispatch_core}

_libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
_libc.mmap.restype = ctypes.c_void_p
_libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_long]
_libc.munmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
_libc.msync.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]

MS_SYNC = 4

def _mlock(addr: int, size: int):
  if _libc.mlock(ctypes.c_void_p(addr), ctypes.c_size_t(size)) != 0:
    raise OSError(ctypes.get_errno(), "mlock failed; run ./setup_python_cap.sh to grant CAP_IPC_LOCK")

def _munlock(addr: int, size: int): _libc.munlock(ctypes.c_void_p(addr), ctypes.c_size_t(size))

def _buffer_addr(buf) -> int:
  return buf.addr if hasattr(buf, "addr") else ctypes.addressof(ctypes.c_char.from_buffer(buf))

def _buffer_size(buf) -> int:
  return buf.size if hasattr(buf, "size") else len(buf)

def _find_bh_devices() -> list[str]:
  result = []
  for path in sorted(glob.glob("/sys/bus/pci/devices/*")):
    vendor = int(open(f"{path}/vendor").read(), 16)
    device = int(open(f"{path}/device").read(), 16)
    if vendor == TT_VENDOR and device == BH_DEVICE: result.append(path)
  return result

def _bind_vfio_pci(sysfs_path: str):
  bdf = os.path.basename(sysfs_path)
  driver_link = f"{sysfs_path}/driver"

  if os.path.islink(driver_link):
    current = os.path.basename(os.readlink(driver_link))
    if current == "vfio-pci": return
    with open(f"{sysfs_path}/driver/unbind", "w") as f:
      f.write(bdf)

  with open(f"{sysfs_path}/driver_override", "w") as f:
    f.write("vfio-pci")
  with open("/sys/bus/pci/drivers_probe", "w") as f:
    f.write(bdf)

  for _ in range(50):
    if os.path.islink(driver_link) and os.path.basename(os.readlink(driver_link)) == "vfio-pci": return
    time.sleep(0.1)

  raise RuntimeError(
    f"failed to bind {bdf} to vfio-pci. Is the vfio-pci module loaded? Try: modprobe vfio-pci")

def _unbind_vfio_pci(sysfs_path: str):
  bdf = os.path.basename(sysfs_path)
  driver_link = f"{sysfs_path}/driver"

  try:
    with open(f"{sysfs_path}/driver_override", "w") as f:
      f.write("\n")
  except OSError:
    pass

  if os.path.islink(driver_link) and os.path.basename(os.readlink(driver_link)) == "vfio-pci":
    with open(f"{sysfs_path}/driver/unbind", "w") as f:
      f.write(bdf)


class _MappedBar:
  def __init__(self, sysfs: str, resource: str, size: int):
    self.fd = os.open(f"{sysfs}/{resource}", os.O_RDWR | os.O_SYNC)
    self.addr = _libc.mmap(None, ctypes.c_size_t(size), mmap.PROT_READ | mmap.PROT_WRITE,
                           mmap.MAP_SHARED, self.fd, 0)
    if self.addr == ctypes.c_void_p(-1).value:
      err = ctypes.get_errno()
      os.close(self.fd)
      self.fd = -1
      raise OSError(err, f"mmap {resource} failed")
    self.size = size
    self.view = memoryview((ctypes.c_ubyte * size).from_address(self.addr)).cast("B")
    self.u32 = self.view.cast("I")
    self.closed = False

  def close(self):
    if self.closed: return
    self.closed = True
    try:
      self.u32.release()
      self.view.release()
    finally:
      if _libc.munmap(ctypes.c_void_p(self.addr), ctypes.c_size_t(self.size)) != 0:
        raise OSError(ctypes.get_errno(), "munmap failed")
      if self.fd >= 0:
        os.close(self.fd)
        self.fd = -1

  def __enter__(self): return self
  def __exit__(self, exc_type, exc, tb): self.close()


class LibCAnonMap:
  def __init__(self, size: int, flags: int | None = None):
    flags = flags if flags is not None else (mmap.MAP_SHARED | mmap.MAP_ANONYMOUS)
    self.addr = _libc.mmap(None, ctypes.c_size_t(size), mmap.PROT_READ | mmap.PROT_WRITE,
                           flags, -1, 0)
    if self.addr == ctypes.c_void_p(-1).value:
      raise OSError(ctypes.get_errno(), "anonymous mmap failed")
    self.size = size
    self.view = memoryview((ctypes.c_ubyte * size).from_address(self.addr)).cast("B")
    self.closed = False

  def __len__(self) -> int:
    return self.size

  def __getitem__(self, key):
    return self.view[key]

  def __setitem__(self, key, value):
    self.view[key] = value

  def flush(self, offset: int = 0, size: int | None = None):
    size = self.size - offset if size is None else size
    if _libc.msync(ctypes.c_void_p(self.addr + offset), ctypes.c_size_t(size), MS_SYNC) != 0:
      raise OSError(ctypes.get_errno(), "msync failed")

  def close(self):
    if self.closed: return
    self.closed = True
    try:
      self.view.release()
    finally:
      if _libc.munmap(ctypes.c_void_p(self.addr), ctypes.c_size_t(self.size)) != 0:
        raise OSError(ctypes.get_errno(), "munmap failed")

  def __enter__(self): return self
  def __exit__(self, exc_type, exc, tb): self.close()


class NocOrdering(Enum):
  RELAXED = 0
  STRICT = 1
  POSTED = 2


class _OffsetView:
  """Wraps a BAR memoryview with a base offset for a configured TLB window."""
  __slots__ = ("_m", "_b", "_s")

  def __init__(self, m, base, size):
    self._m, self._b, self._s = m, base, size

  def __getitem__(self, key):
    if isinstance(key, slice):
      start = (key.start or 0) + self._b
      stop = (key.stop if key.stop is not None else self._s) + self._b
      n = max(0, stop - start)
      data = struct.unpack_from(f"<{n}s", self._m, start)[0]
      return data if key.step in (None, 1) else data[::key.step]
    return struct.unpack_from("B", self._m, self._b + key)[0]

  def __setitem__(self, key, value):
    if isinstance(key, slice):
      if key.step not in (None, 1):
        raise ValueError("MMIO slice assignment does not support steps")
      start = (key.start or 0) + self._b
      stop = (key.stop if key.stop is not None else self._s) + self._b
      data = bytes(value)
      if stop - start != len(data):
        raise IndexError("MMIO slice assignment is wrong size")
      struct.pack_into(f"<{len(data)}s", self._m, start, data)
    else:
      struct.pack_into("B", self._m, self._b + key, value)


class TLBWindow:
  SIZE_2M = TLB_2M_SIZE
  SIZE_4G = TLB_4G_SIZE

  def __init__(self, dev, start: Core, end: Core | None = None, addr: int = 0,
               mode: NocOrdering = NocOrdering.STRICT, size: int = SIZE_2M, wc: bool = False):
    self.dev, self.size = dev, size
    self._id = dev.alloc_tlb(size)
    self._bar, self._base = dev.tlb_window(self._id, wc=wc)
    self.mm = _OffsetView(self._bar, self._base, size)
    self.target(start, end, addr=addr, mode=mode)

  def target(self, start: Core, end: Core | None = None, addr: int = 0,
             mode: NocOrdering = NocOrdering.STRICT):
    end = end or start
    self.dev.configure_tlb(
      self._id, addr,
      x_start=start[0], y_start=start[1], x_end=end[0], y_end=end[1],
      mcast=int(end != start), ordering=mode.value,
    )

  def read32(self, offset: int) -> int:
    return struct.unpack_from("<I", self._bar, self._base + offset)[0]

  def write32(self, offset: int, value: int):
    struct.pack_into("<I", self._bar, self._base + offset, value & 0xFFFFFFFF)

  def write(self, addr: int, data: bytes):
    struct.pack_into(f"<{len(data)}s", self._bar, self._base + addr, data)

  def close(self):
    self.dev.free_tlb(self._id)

  def __enter__(self): return self
  def __exit__(self, exc_type, exc, tb): self.close()

def _config_path(sysfs_path: str) -> str: return f"{sysfs_path}/config"


def _read_config(path: str, size: int, offset: int) -> bytes:
  fd = os.open(path, os.O_RDONLY | os.O_SYNC)
  try:
    return os.pread(fd, size, offset)
  finally:
    os.close(fd)


def _write_config(path: str, data: bytes, offset: int):
  fd = os.open(path, os.O_RDWR | os.O_SYNC)
  try:
    os.pwrite(fd, data, offset)
  finally:
    os.close(fd)

def _read_config_u16(path: str, offset: int) -> int: return struct.unpack("<H", _read_config(path, 2, offset))[0]


def _write_config_u16(path: str, offset: int, value: int): _write_config(path, struct.pack("<H", value & 0xFFFF), offset)


def _read_vendor_id(sysfs_path: str) -> int | None:
  try:
    return _read_config_u16(_config_path(sysfs_path), PCI_VENDOR_ID)
  except OSError: return None

def _find_pcie_cap(cfg: bytes) -> int | None:
  if len(cfg) <= PCI_CAP_PTR: return None
  ptr = cfg[PCI_CAP_PTR] & 0xFC
  seen = set()
  while ptr and ptr + 1 < len(cfg) and ptr not in seen:
    seen.add(ptr)
    if cfg[ptr] == PCI_CAP_ID_EXP: return ptr
    ptr = cfg[ptr + 1] & 0xFC
  return None


def _find_upstream_bridge_sysfs(sysfs_path: str) -> str | None:
  cur = os.path.realpath(sysfs_path)
  parent = os.path.dirname(cur)
  while parent and parent != "/" and os.path.exists(os.path.join(parent, "config")):
    class_path = os.path.join(parent, "class")
    try:
      dev_class = int(open(class_path).read().strip(), 16)
      if (dev_class >> 8) == 0x0604: return parent
    except OSError: pass
    parent = os.path.dirname(parent)
  return None


def _wait_for_vendor_id(sysfs_path: str, timeout_s: float = 10.0) -> bool:
  deadline = time.monotonic() + timeout_s
  while time.monotonic() < deadline:
    if _read_vendor_id(sysfs_path) == TT_VENDOR: return True
    time.sleep(0.1)
  return False


def _restore_endpoint_config(config_path: str, saved: bytes, pcie_cap: int | None, saved_devctl: int | None):
  # Mirror the tt-kmd post-reset subset, avoiding PCI status because it is write-1-to-clear.
  _write_config(config_path, saved[0x04:0x06], 0x04)
  _write_config(config_path, saved[0x0C:0x0E], 0x0C)
  _write_config(config_path, saved[0x10:0x28], 0x10)
  _write_config(config_path, saved[0x3C:0x40], 0x3C)

  if pcie_cap is not None and saved_devctl is not None:
    devctl = (saved_devctl & ~PCI_EXP_DEVCTL_READRQ) | PCI_EXP_DEVCTL_READRQ_4096
    _write_config(config_path, struct.pack("<H", devctl), pcie_cap + PCI_EXP_DEVCTL)

  cmd = _read_config_u16(config_path, PCI_COMMAND)
  want = PCI_COMMAND_MEMORY | PCI_COMMAND_MASTER
  if (cmd & want) != want:
    _write_config_u16(config_path, PCI_COMMAND, cmd | want)


def _secondary_bus_reset(sysfs_path: str):
  bridge_sysfs = _find_upstream_bridge_sysfs(sysfs_path)
  if bridge_sysfs is None:
    raise RuntimeError(f"could not find upstream PCIe bridge for {os.path.basename(sysfs_path)}")

  bridge_bdf = os.path.basename(bridge_sysfs)
  bridge_config = _config_path(bridge_sysfs)
  ctrl = _read_config_u16(bridge_config, PCI_BRIDGE_CONTROL)
  print(f"  resetting PCIe secondary bus via bridge {bridge_bdf}")
  _write_config_u16(bridge_config, PCI_BRIDGE_CONTROL, ctrl | PCI_BRIDGE_CTL_BUS_RESET)
  time.sleep(0.002)
  _write_config_u16(bridge_config, PCI_BRIDGE_CONTROL, ctrl)
  time.sleep(0.5)

  if not _wait_for_vendor_id(sysfs_path, timeout_s=10.0):
    raise RuntimeError(f"PCIe link did not come back for {os.path.basename(sysfs_path)}")


class PCIDevice:
  def __init__(self, index: int = 0, use_vfio: bool = True):
    devices = _find_bh_devices()
    if index >= len(devices):
      raise RuntimeError(f"Blackhole device {index} not found (found {len(devices)})")
    self.sysfs = devices[index]
    self.bdf = os.path.basename(self.sysfs)
    self._closed = False
    self._has_vfio = False
    self._vfio_container = -1
    self._vfio_group = -1
    self._vfio_device = -1
    self._unbind_vfio_on_close = False
    self._bar0_fd = -1
    self._bar0_wc_fd = -1
    self._bar2_fd = -1
    self._bar4_fd = -1
    self._bar4_wc_fd = -1
    self._bar_mmaps: list[_MappedBar] = []
    self.bar0 = None
    self.bar0_wc = None
    self.bar2 = None
    self.bar4 = None
    self.bar4_wc = None
    self.bar0_u32 = None
    self.bar2_u32 = None

    # Enable PCI device, memory space, bus mastering
    driver_link = f"{self.sysfs}/driver"
    already_vfio = (os.path.islink(driver_link)
                    and os.path.basename(os.readlink(driver_link)) == "vfio-pci")
    if not already_vfio:
      with open(f"{self.sysfs}/enable", "r+") as f:
        if int(f.read().strip()) == 0:
          f.seek(0); f.write("1")
      fd = os.open(f"{self.sysfs}/config", os.O_RDWR)
      os.lseek(fd, PCI_COMMAND, os.SEEK_SET)
      cmd = struct.unpack("<H", os.read(fd, 2))[0]
      want = PCI_COMMAND_MEMORY | PCI_COMMAND_MASTER
      if (cmd & want) != want:
        os.lseek(fd, PCI_COMMAND, os.SEEK_SET)
        os.write(fd, struct.pack("<H", cmd | want))
      os.close(fd)

    # Bind to vfio-pci only for fast dispatch DMA/sysmem pinning.
    self._has_vfio = use_vfio
    if self._has_vfio:
      self._setup_vfio()
      self._unbind_vfio_on_close = True

    # mmap Linux BAR resources. TLBWindow chooses a UC or WC mapping at construction.
    bar = _MappedBar(self.sysfs, "resource0", BAR0_SIZE)
    self._bar_mmaps.append(bar); self._bar0_fd, self.bar0, self.bar0_u32 = bar.fd, bar.view, bar.u32
    bar = _MappedBar(self.sysfs, "resource0_wc", BAR0_SIZE)
    self._bar_mmaps.append(bar); self._bar0_wc_fd, self.bar0_wc = bar.fd, bar.view
    bar = _MappedBar(self.sysfs, "resource2", 1 << 20)
    self._bar_mmaps.append(bar); self._bar2_fd, self.bar2, self.bar2_u32 = bar.fd, bar.view, bar.u32

    bar4_probe_fd = os.open(f"{self.sysfs}/resource4", os.O_RDWR | os.O_SYNC)
    bar4_size = os.fstat(bar4_probe_fd).st_size
    os.close(bar4_probe_fd)
    self._bar4_4g_count = min(TLB_4G_COUNT, bar4_size // TLB_4G_SIZE) if bar4_size else 0
    if bar4_size:
      bar = _MappedBar(self.sysfs, "resource4", bar4_size)
      self._bar_mmaps.append(bar); self._bar4_fd, self.bar4 = bar.fd, bar.view
      bar = _MappedBar(self.sysfs, "resource4_wc", bar4_size)
      self._bar_mmaps.append(bar); self._bar4_wc_fd, self.bar4_wc = bar.fd, bar.view
    else:
      self.bar4 = self.bar4_wc = None
      self._bar4_fd = -1
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

    self._bring_device_to_a0()

  @staticmethod
  def list_devices() -> list[str]: return _find_bh_devices()

  def telemetry_layout(self) -> dict:
    table_base = self.read_arc_apb32(self.SCRATCH_RAM_13)
    data_base = self.read_arc_apb32(self.SCRATCH_RAM_12)
    if table_base in (0, 0xFFFFFFFF) or data_base in (0, 0xFFFFFFFF):
      raise RuntimeError(f"invalid ARC telemetry pointers table=0x{table_base:x} data=0x{data_base:x}")
    tlb = self.alloc_tlb(TLB_2M_SIZE)
    try:
      version = self._read_arc_noc32(table_base, tlb)
      entry_count = self._read_arc_noc32(table_base + 4, tlb)
      if entry_count in (0, 0xFFFFFFFF) or entry_count > 4096:
        raise RuntimeError(f"invalid ARC telemetry entry_count 0x{entry_count:x} at 0x{table_base:x}")
      tag_to_offset = {}
      for i in range(entry_count):
        tag_offset = self._read_arc_noc32(table_base + 8 + i * 4, tlb)
        tag_to_offset[tag_offset & 0xFFFF] = (tag_offset >> 16) & 0xFFFF
    finally:
      self.free_tlb(tlb)
    return {
      "version": version,
      "table_base": table_base,
      "data_base": data_base,
      "entry_count": entry_count,
      "tag_to_offset": tag_to_offset,
    }

  def telemetry_tag(self, layout: dict, tag: str | int) -> int | None:
    tag_id = TELEMETRY_TAGS[tag] if isinstance(tag, str) else tag
    offset = layout["tag_to_offset"].get(tag_id)
    if offset is None:
      return None
    return self._read_arc_noc32(layout["data_base"] + 4 * offset)

  def board_info(self, layout: dict | None = None, fast_dispatch: bool = False) -> BoardInfo:
    layout = layout or self.telemetry_layout()
    bid_hi = self.telemetry_tag(layout, "BOARD_ID_HIGH")
    bid_lo = self.telemetry_tag(layout, "BOARD_ID_LOW")
    board_id = ((bid_hi & 0xFFFFFFFF) << 32 | (bid_lo & 0xFFFFFFFF)) if bid_hi is not None and bid_lo is not None else None
    arch = BOARD_UPI_TO_NAME.get((board_id >> 36) & 0xFFFFF, "unknown") if board_id is not None else "unknown"
    if arch.startswith("p100"):
      board = "p100"
    elif arch.startswith("p150"):
      board = "p150"
    else:
      board = arch

    enabled_tensix = self.telemetry_tag(layout, "ENABLED_TENSIX_COL")
    if enabled_tensix is None:
      enabled_tensix = DEFAULT_TENSIX_ENABLED
    enabled_gddr = self.telemetry_tag(layout, "ENABLED_GDDR")
    if enabled_gddr is None:
      enabled_gddr = DEFAULT_GDDR_ENABLED

    columns = tensix_columns_from_enabled_mask(enabled_tensix)
    workers = worker_cores_from_columns(columns)
    if not columns:
      raise RuntimeError(f"no enabled Tensix columns in ARC telemetry mask 0x{enabled_tensix:x}")
    rightmost_x = columns[-1]
    prefetch_core = (rightmost_x, 2)
    dispatch_core = (rightmost_x, 3)
    cq_cores = {prefetch_core, dispatch_core}
    program_cores = [core for core in workers if not fast_dispatch or core not in cq_cores]
    harvested_dram_banks = [bank for bank in range(8) if ((enabled_gddr >> bank) & 1) == 0]
    if len(harvested_dram_banks) > 1:
      raise RuntimeError(f"unsupported harvested DRAM banks: {harvested_dram_banks}")
    harvested_dram_bank = harvested_dram_banks[0] if harvested_dram_banks else None
    return BoardInfo(
      board_id=board_id,
      arch=arch,
      board=board,
      enabled_tensix_col=enabled_tensix,
      tensix_columns=columns,
      worker_cores=workers,
      program_cores=program_cores,
      enabled_gddr=enabled_gddr,
      harvested_dram_bank=harvested_dram_bank,
      prefetch_core=prefetch_core,
      dispatch_core=dispatch_core,
    )

  @classmethod
  def reset_index(cls, index: int = 0):
    devices = cls.list_devices()
    if index >= len(devices):
      raise RuntimeError(f"Blackhole device {index} not found (found {len(devices)})")
    cls.reset_bdf(os.path.basename(devices[index]))

  @staticmethod
  def reset_bdf(bdf: str):
    """Blackhole reset matching tt-smi/UMD's non-Galaxy default as closely as possible.

    1. Save PCI config space and PCIe Device Control (MPS/MRRS)
    2. Do a PCIe secondary bus reset through the upstream bridge
    3. Restore endpoint PCI config and enable memory/bus-master
    4. Read PCIe NoC X from BAR0 (for post-reset DBI restore)
    5. Set reset marker (PCI_COMMAND_PARITY)
    6. Fire interface timer (extended config 0x930/0x934)
    7. Poll for completion (parity bit clears)
    8. Wait for the device to settle/reappear
    9. Restore PCI config, DBI MPS, and MRRS
    10. Send ARC A0 + watchdog on the next open

    Falls back to PCIe FLR if extended config space is unavailable.
    """
    sysfs = f"/sys/bus/pci/devices/{bdf}"
    config_path = f"{sysfs}/config"

    # PCI config offsets / bits
    _PCI_COMMAND         = 0x04
    _PCI_COMMAND_MEMORY  = 0x02
    _PCI_COMMAND_MASTER  = 0x04
    _PCI_COMMAND_PARITY  = 0x40   # bit 6 — used as reset marker
    # BH interface timer (PCIe extended config space)
    _TIMER_CONTROL       = 0x930
    _TIMER_TARGET        = 0x934
    # BAR0 offsets for NOC ID detection
    _NOC2AXI_CFG_START   = 0x1FD00000
    _NOC_ID_OFFSET       = 0x4044
    # PCIe DBI address (NoC space) and Device Control offset
    _PCIE_DBI_ADDR       = 0xF800000000000000
    _DBI_DEVCTL          = 0x78

    # --- Pre-reset: save state ---
    fd = os.open(config_path, os.O_RDWR | os.O_SYNC)
    try:
      config_size = os.fstat(fd).st_size
      if config_size <= _TIMER_TARGET + 4:
        # Extended config space not reachable: fall back to sysfs FLR
        os.close(fd); fd = -1
        print(f"  extended config space unavailable, falling back to PCIe FLR")
        with open(f"{sysfs}/reset", "w") as f:
          f.write("1\n")
        return

      saved = os.pread(fd, 256, 0)
      if len(saved) < 64:
        raise RuntimeError(f"could not read PCI config for {bdf}")

      # Find PCIe capability and save Device Control (contains MPS)
      pcie_cap = _find_pcie_cap(saved)
      saved_devctl = None
      if pcie_cap is not None:
        raw = os.pread(fd, 2, pcie_cap + PCI_EXP_DEVCTL)
        saved_devctl = struct.unpack("<H", raw)[0]
    finally:
      if fd >= 0:
        os.close(fd)

    # --- Match tt-smi/UMD default for non-Galaxy BH: reset/retrain PCIe link first. ---
    _secondary_bus_reset(sysfs)
    _restore_endpoint_config(config_path, saved, pcie_cap, saved_devctl)

    # Read PCIe NoC X from BAR0 for post-reset MPS restore via DBI
    pcie_noc_x = None
    try:
      with _MappedBar(sysfs, "resource0", BAR0_SIZE) as bar0:
        noc_id_off = _NOC2AXI_CFG_START + _NOC_ID_OFFSET
        x = struct.unpack_from("<I", bar0.view, noc_id_off)[0] & 0x3F
        if x in (2, 11):
          pcie_noc_x = x
    except Exception:
      pass  # will skip DBI restore

    fd = os.open(config_path, os.O_RDWR | os.O_SYNC)
    try:
      # --- Step 1: Set reset marker ---
      cmd = struct.unpack_from("<H", saved, _PCI_COMMAND)[0]
      os.pwrite(fd, struct.pack("<H", cmd | _PCI_COMMAND_PARITY), _PCI_COMMAND)

      # --- Step 2: Fire interface timer (in-place ASIC reset) ---
      os.pwrite(fd, struct.pack("<I", 0x1), _TIMER_TARGET)    # target = 1
      os.pwrite(fd, struct.pack("<I", 0x11), _TIMER_CONTROL)  # enable | force_pending

      # --- Step 3: Poll for reset completion ---
      deadline = time.monotonic() + 10.0
      while time.monotonic() < deadline:
        raw = os.pread(fd, 2, _PCI_COMMAND)
        if not (struct.unpack("<H", raw)[0] & _PCI_COMMAND_PARITY):
          break
        time.sleep(0.01)
      else:
        raise RuntimeError(f"ASIC reset timeout for {bdf} — parity bit did not clear")
    finally:
      if fd >= 0:
        os.close(fd)

    # UMD waits at least 2s after ASIC reset before POST_RESET.
    time.sleep(2.0)
    if not _wait_for_vendor_id(sysfs, timeout_s=10.0):
      raise RuntimeError(f"device {bdf} did not respond after ASIC reset")

    # --- Step 4: Restore PCI config space / MRRS ---
    _restore_endpoint_config(config_path, saved, pcie_cap, saved_devctl)

    # --- Step 5: Restore MPS via NoC write to PCIe DBI register ---
    if pcie_noc_x is not None and saved_devctl is not None:
      try:
        with _MappedBar(sysfs, "resource0", BAR0_SIZE) as bar0_map:
          bar0 = bar0_map.view
          # Use the last 2M TLB (index 201) to reach PCIE_DBI_ADDR + 0x78
          dbi_addr = _PCIE_DBI_ADDR + _DBI_DEVCTL
          tlb_idx = TLB_2M_COUNT - 1
          local_offset = dbi_addr >> 21
          y = 0
          val = (local_offset
                 | (pcie_noc_x << 43) | (y << 49)
                 | (pcie_noc_x << 55) | (y << 61)
                 | (0 << 67)           # noc=0
                 | (0 << 69)           # mcast=0
                 | (1 << 70)           # ordering=strict
                 | (0 << 72)           # linked=0
                 | (0 << 73))          # static_vc=0
          reg_off = TLB_REGS_START + tlb_idx * TLB_REG_SIZE
          bar0_u32 = bar0_map.u32
          reg_word = reg_off // 4
          bar0_u32[reg_word] = val & 0xFFFFFFFF
          bar0_u32[reg_word + 1] = (val >> 32) & 0xFFFFFFFF
          bar0_u32[reg_word + 2] = (val >> 64) & 0xFFFFFFFF

          bar_off = tlb_idx * TLB_2M_SIZE + (int(dbi_addr) & (TLB_2M_SIZE - 1))
          cur = struct.unpack_from("<I", bar0, bar_off)[0]
          # Clear MPS field (bits 7:5) and restore saved value
          mps_bits = (saved_devctl >> 5) & 0x7
          cur = (cur & ~(0x7 << 5)) | (mps_bits << 5)
          cur = (cur & ~PCI_EXP_DEVCTL_READRQ) | PCI_EXP_DEVCTL_READRQ_4096
          bar0_u32[bar_off // 4] = cur
      except Exception as e:
        print(f"  warning: could not restore MPS via DBI: {e}")

    # ARC init (A0 + watchdog) happens in PCIDevice.__init__ → _bring_device_to_a0()
    # on the next open, so nothing more to do here.

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
    arc_ready_timeout_s = float(os.environ.get("TT_ARC_BOOT_TIMEOUT", "2.0"))
    deadline = time.monotonic() + arc_ready_timeout_s
    boot_status = 0
    while time.monotonic() < deadline:
      boot_status = self.read_arc_apb32(self.SCRATCH_RAM_2)
      if (boot_status & self.ARC_BOOT_STATUS_STARTED_MASK) == self.ARC_BOOT_STATUS_STARTED_VALUE:
        self.arc_msg(0xA0, timeout_ms=200)
        try: self.arc_msg(self.MSG_SET_WDT_TIMEOUT, arg0=60_000, timeout_ms=200)
        except Exception: pass
        return
      time.sleep(0.00001)
    raise RuntimeError(
      f"ARC not ready after {arc_ready_timeout_s:.1f}s (boot_status=0x{boot_status:x}) — device may be in A3, try tt-smi -r")

  def read_arc_apb32(self, offset: int) -> int:
    tlb = self.alloc_tlb(TLB_2M_SIZE)
    try:
      arc_x, arc_y = self.ARC_TILE
      self.configure_tlb(tlb, self.ARC_NOC_BASE, arc_x, arc_y, arc_x, arc_y, ordering=1)
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
      arc_x, arc_y = self.ARC_TILE
      self.configure_tlb(tlb, base, arc_x, arc_y, arc_x, arc_y, ordering=1)
      bar, bar_off = self.tlb_window(tlb)
      return struct.unpack_from("<I", bar, bar_off + (addr - base))[0]
    finally:
      if owns_tlb:
        self.free_tlb(tlb)

  def write_arc_apb32(self, offset: int, value: int):
    tlb = self.alloc_tlb(TLB_2M_SIZE)
    try:
      arc_x, arc_y = self.ARC_TILE
      self.configure_tlb(tlb, self.ARC_NOC_BASE, arc_x, arc_y, arc_x, arc_y, ordering=1)
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
    if index < TLB_2M_COUNT: self._tlb_2m[index] = False
    else: self._tlb_4g[index - TLB_2M_COUNT] = False

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

    reg_word = reg_offset // 4
    self.bar0_u32[reg_word] = val & 0xFFFFFFFF
    self.bar0_u32[reg_word + 1] = (val >> 32) & 0xFFFFFFFF
    self.bar0_u32[reg_word + 2] = (val >> 64) & 0xFFFFFFFF

    if index < 32:
      stride_off = TLB_REGS_START + TLB_STRIDE_OFFSET + index * 4
      self.bar0_u32[stride_off // 4] = 0

  def tlb_window(self, index: int, wc: bool = False) -> tuple[memoryview, int]:
    if index < TLB_2M_COUNT: return (self.bar0_wc if wc else self.bar0), index * TLB_2M_SIZE
    bar = self.bar4_wc if wc else self.bar4
    if bar is None: raise RuntimeError("BAR4 not available")
    return bar, (index - TLB_2M_COUNT) * TLB_4G_SIZE

  # ---- DMA / page pinning via VFIO IOMMU ----

  def pin_pages(self, buf) -> int:
    """Pin a buffer and set up IOMMU + iATU for device DMA. Returns the NOC address."""
    va = _buffer_addr(buf)
    size = _buffer_size(buf)
    cleanup = []
    try:
      _mlock(va, size)
      cleanup.append(lambda: _munlock(va, size))

      iova = self._next_iova
      self._next_iova += size

      dma_map = struct.pack("=IIQQQ", 32,
        VFIO_DMA_MAP_FLAG_READ | VFIO_DMA_MAP_FLAG_WRITE, va, iova, size)
      fcntl.ioctl(self._vfio_container, VFIO_IOMMU_MAP_DMA, dma_map)
      cleanup.append(lambda: fcntl.ioctl(self._vfio_container, VFIO_IOMMU_UNMAP_DMA,
        struct.pack("=IIQQ", 24, 0, iova, size)))

      region = self._alloc_iatu_region()
      cleanup.append(lambda: self._free_iatu_region(region))

      noc_base = region * (1 << 30)
      self._configure_iatu(region, noc_base, noc_base + size - 1, iova)
    except:
      for fn in reversed(cleanup):
        fn()
      raise

    noc_addr = NOC_PCIE_OFFSET | noc_base
    self._pinnings[noc_addr] = {"iova": iova, "size": size, "iatu_region": region}
    return noc_addr

  def unpin_pages(self, buf, noc_addr: int):
    va = _buffer_addr(buf)
    pin = self._pinnings[noc_addr]
    self._disable_iatu(pin["iatu_region"])
    self._free_iatu_region(pin["iatu_region"])
    dma_unmap = struct.pack("=IIQQ", 24, 0, pin["iova"], pin["size"])
    fcntl.ioctl(self._vfio_container, VFIO_IOMMU_UNMAP_DMA, dma_unmap)
    _munlock(va, pin["size"])
    del self._pinnings[noc_addr]

  def _alloc_iatu_region(self) -> int:
    for i, used in enumerate(self._iatu_regions):
      if not used:
        self._iatu_regions[i] = True
        return i
    raise RuntimeError("no free iATU regions")

  def _free_iatu_region(self, region: int): self._iatu_regions[region] = False

  def _iatu_reg(self, region: int, reg: int) -> int: return IATU_BASE + (2 * region) * (IATU_REGION_STRIDE // 2) + reg

  def _configure_iatu(self, region: int, base: int, limit: int, target: int):
    def w32(reg, val):
      off = self._iatu_reg(region, reg)
      self.bar2_u32[off // 4] = val & 0xFFFFFFFF
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
    self.bar2_u32[off // 4] = 0

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
        arc_x, arc_y = self.ARC_TILE
        self.configure_tlb(tlb, base, arc_x, arc_y, arc_x, arc_y, ordering=1)
        bar, bar_off = self.tlb_window(tlb)
        return struct.unpack_from("<I", bar, bar_off + (noc_addr - base))[0]

      def _write32(noc_addr, val):
        base = noc_addr & ~(TLB_2M_SIZE - 1)
        arc_x, arc_y = self.ARC_TILE
        self.configure_tlb(tlb, base, arc_x, arc_y, arc_x, arc_y, ordering=1)
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
    if busy: self.arc_msg(self.MSG_AICLK_GO_BUSY)
    else:
      try: self.arc_msg(self.MSG_AICLK_GO_LONG_IDLE)
      except (TimeoutError, RuntimeError): pass

  def close(self):
    if self._closed: return
    self._closed = True
    for bar_map in reversed(self._bar_mmaps):
      try: bar_map.close()
      except Exception: pass
    for bar_name in ["bar0", "bar0_wc", "bar2", "bar4", "bar4_wc", "bar0_u32", "bar2_u32"]:
      setattr(self, bar_name, None)
    self._bar_mmaps.clear()
    for fd_name in ["_bar0_fd", "_bar0_wc_fd", "_bar2_fd", "_bar4_fd", "_bar4_wc_fd"]:
      setattr(self, fd_name, -1)
    if self._has_vfio:
      for fd_name in ["_vfio_device", "_vfio_group", "_vfio_container"]:
        fd = getattr(self, fd_name, -1)
        if fd < 0: continue
        try: os.close(fd)
        except Exception: pass
        setattr(self, fd_name, -1)
    if self._unbind_vfio_on_close:
      try: _unbind_vfio_pci(self.sysfs)
      except Exception: pass
      self._unbind_vfio_on_close = False

  def __enter__(self): return self
  def __exit__(self, exc_type, exc, tb): self.close()
