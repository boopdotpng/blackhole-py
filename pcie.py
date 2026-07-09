from __future__ import annotations

import ctypes, ctypes.util, glob, mmap, os, struct
from dataclasses import dataclass
from enum import Enum

TLB_2M_COUNT = 202
TLB_4G_COUNT = 8
TLB_2M_SIZE = 1 << 21
TLB_4G_SIZE = 1 << 32
TLB_REGS_START = 0x1FC00000

NOC_PCIE_OFFSET = 4 << 58
PCIE_NOC_XY = (24 << 6) | 19

Core = tuple[int, int]

TELEMETRY_TAGS = {
  "BOARD_ID_HIGH": 1,
  "BOARD_ID_LOW": 2,
  "ENABLED_GDDR": 36,
}

P150_TENSIX_X = (*range(1, 8), *range(10, 17))
P100_TENSIX_X = (*range(1, 8), *range(10, 15))
DEFAULT_GDDR_ENABLED = 0xFF
BOARD_UPI_TO_NAME = {
  0x43: "p100a", 0x40: "p150a", 0x41: "p150b",
}

_libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
_libc.ioctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_void_p]
_libc.ioctl.restype = ctypes.c_int
_libc.mmap.restype = ctypes.c_void_p
_libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_long]
_libc.munmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
_libc.msync.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]

MS_SYNC = 4

TENSTORRENT_IOCTL_MAGIC = 0xFA
TENSTORRENT_IOCTL_PIN_PAGES = (TENSTORRENT_IOCTL_MAGIC << 8) | 7
TENSTORRENT_IOCTL_UNPIN_PAGES = (TENSTORRENT_IOCTL_MAGIC << 8) | 10
TENSTORRENT_IOCTL_ALLOCATE_TLB = (TENSTORRENT_IOCTL_MAGIC << 8) | 11
TENSTORRENT_IOCTL_FREE_TLB = (TENSTORRENT_IOCTL_MAGIC << 8) | 12
TENSTORRENT_IOCTL_CONFIGURE_TLB = (TENSTORRENT_IOCTL_MAGIC << 8) | 13
TENSTORRENT_IOCTL_SET_POWER_STATE = (TENSTORRENT_IOCTL_MAGIC << 8) | 15

TENSTORRENT_PIN_PAGES_NOC_DMA = 2

TT_POWER_FLAG_MAX_AI_CLK = 1 << 0
TT_POWER_FLAG_MRISC_PHY_WAKEUP = 1 << 1
TT_POWER_FLAG_TENSIX_ENABLE = 1 << 2
TT_POWER_FLAG_L2CPU_ENABLE = 1 << 3
TT_POWER_FLAG_COUNT = 4
TT_POWER_VALIDITY = lambda flags_count, settings_count: ((flags_count & 0xF) << 0) | ((settings_count & 0xF) << 4)


class Structure(ctypes.Structure):
  def __init__(self, **kwargs):
    super().__init__()
    for key, value in kwargs.items():
      setattr(self, key, value)


class tenstorrent_pin_pages_in(Structure):
  _fields_ = [
    ("output_size_bytes", ctypes.c_uint32),
    ("flags", ctypes.c_uint32),
    ("virtual_address", ctypes.c_uint64),
    ("size", ctypes.c_uint64),
  ]


class tenstorrent_pin_pages_out(Structure):
  _fields_ = [("physical_address", ctypes.c_uint64), ("noc_address", ctypes.c_uint64)]


class tenstorrent_pin_pages(Structure):
  _fields_ = [("in_", tenstorrent_pin_pages_in), ("out", tenstorrent_pin_pages_out)]


class tenstorrent_unpin_pages_in(Structure):
  _fields_ = [("virtual_address", ctypes.c_uint64), ("size", ctypes.c_uint64), ("reserved", ctypes.c_uint64)]


class tenstorrent_unpin_pages_out(Structure):
  _fields_ = []


class tenstorrent_unpin_pages(Structure):
  _fields_ = [("in_", tenstorrent_unpin_pages_in), ("out", tenstorrent_unpin_pages_out)]


class tenstorrent_allocate_tlb_in(Structure):
  _fields_ = [("size", ctypes.c_uint64), ("reserved", ctypes.c_uint64)]


class tenstorrent_allocate_tlb_out(Structure):
  _fields_ = [
    ("id", ctypes.c_uint32),
    ("reserved0", ctypes.c_uint32),
    ("mmap_offset_uc", ctypes.c_uint64),
    ("mmap_offset_wc", ctypes.c_uint64),
    ("reserved1", ctypes.c_uint64),
  ]


class tenstorrent_allocate_tlb(Structure):
  _fields_ = [("in_", tenstorrent_allocate_tlb_in), ("out", tenstorrent_allocate_tlb_out)]


class tenstorrent_free_tlb_in(Structure):
  _fields_ = [("id", ctypes.c_uint32)]


class tenstorrent_free_tlb_out(Structure):
  _fields_ = []


class tenstorrent_free_tlb(Structure):
  _fields_ = [("in_", tenstorrent_free_tlb_in), ("out", tenstorrent_free_tlb_out)]


class tenstorrent_noc_tlb_config(Structure):
  _fields_ = [
    ("addr", ctypes.c_uint64),
    ("x_end", ctypes.c_uint16),
    ("y_end", ctypes.c_uint16),
    ("x_start", ctypes.c_uint16),
    ("y_start", ctypes.c_uint16),
    ("noc", ctypes.c_uint8),
    ("mcast", ctypes.c_uint8),
    ("ordering", ctypes.c_uint8),
    ("linked", ctypes.c_uint8),
    ("static_vc", ctypes.c_uint8),
    ("reserved0", ctypes.c_uint8 * 3),
    ("reserved1", ctypes.c_uint32 * 2),
  ]


class tenstorrent_configure_tlb_in(Structure):
  _fields_ = [("id", ctypes.c_uint32), ("reserved", ctypes.c_uint32), ("config", tenstorrent_noc_tlb_config)]


class tenstorrent_configure_tlb_out(Structure):
  _fields_ = [("reserved", ctypes.c_uint64)]


class tenstorrent_configure_tlb(Structure):
  _fields_ = [("in_", tenstorrent_configure_tlb_in), ("out", tenstorrent_configure_tlb_out)]


class tenstorrent_power_state(Structure):
  _fields_ = [
    ("argsz", ctypes.c_uint32),
    ("flags", ctypes.c_uint32),
    ("reserved0", ctypes.c_uint8),
    ("validity", ctypes.c_uint8),
    ("power_flags", ctypes.c_uint16),
    ("power_settings", ctypes.c_uint16 * 14),
  ]


def _ioctl(fd: int, request: int, data: ctypes.Structure):
  if _libc.ioctl(fd, request, ctypes.byref(data)) != 0:
    raise OSError(ctypes.get_errno(), f"ioctl 0x{request:x} failed")


def _buffer_addr(buf) -> int:
  return buf.addr if hasattr(buf, "addr") else ctypes.addressof(ctypes.c_char.from_buffer(buf))


def _buffer_size(buf) -> int:
  return buf.size if hasattr(buf, "size") else memoryview(buf).nbytes


def _tenstorrent_devices() -> list[str]:
  return sorted(glob.glob("/dev/tenstorrent/[0-9]*"), key=lambda p: int(os.path.basename(p)))


def _devnode(index: int) -> str:
  return f"/dev/tenstorrent/{index}"


@dataclass(frozen=True)
class BoardInfo:
  board: str
  worker_cores: list[Core]
  program_cores: list[Core]
  dram_tiles: list[tuple[int, int, int]]
  prefetch_core: Core
  dispatch_core: Core
  harvested_dram_bank: int | None

  @property
  def core_count(self) -> int:
    return len(self.program_cores)

  @property
  def cq_cores(self) -> set[Core]:
    return {self.prefetch_core, self.dispatch_core}


def _build_board_info(board: str, effective_gddr: int, fast_dispatch: bool) -> BoardInfo:
  columns = P100_TENSIX_X if board == "p100a" else P150_TENSIX_X
  workers = [(x, y) for x in columns for y in range(2, 12)]
  rightmost_x = columns[-1]
  prefetch_core = (rightmost_x, 2)
  dispatch_core = (rightmost_x, 3)
  cq_cores = {prefetch_core, dispatch_core}
  program_cores = [core for core in workers if not fast_dispatch or core not in cq_cores]
  harvested = [bank for bank in range(8) if ((effective_gddr >> bank) & 1) == 0]
  if len(harvested) > 1:
    raise RuntimeError(f"unsupported harvested DRAM banks: {harvested}")
  bank_ys = (
    (0, 1, 11), (2, 3, 10), (4, 8, 9), (5, 6, 7),
    (0, 1, 11), (2, 3, 10), (4, 8, 9), (5, 6, 7),
  )
  return BoardInfo(
    board=board,
    worker_cores=workers,
    program_cores=program_cores,
    dram_tiles=[
      (bank, 0 if bank < 4 else 9, y)
      for bank in range(8)
      if (effective_gddr >> bank) & 1
      for y in bank_ys[bank]
    ],
    prefetch_core=prefetch_core,
    dispatch_core=dispatch_core,
    harvested_dram_bank=harvested[0] if harvested else None,
  )


class Mapping:
  def __init__(self, size: int, offset: int = 0, flags: int | None = None, fd: int = -1):
    if offset & (mmap.PAGESIZE - 1):
      raise ValueError(f"mmap offset must be page-aligned, got 0x{offset:x}")
    self.fd = fd
    if flags is None:
      flags = mmap.MAP_SHARED if self.fd >= 0 else (mmap.MAP_SHARED | mmap.MAP_ANONYMOUS)
    self.addr = _libc.mmap(None, ctypes.c_size_t(size), mmap.PROT_READ | mmap.PROT_WRITE, flags, self.fd, offset)
    if self.addr == ctypes.c_void_p(-1).value:
      raise OSError(ctypes.get_errno(), f"mmap {fd if fd >= 0 else 'anon'} failed")
    self.size, self.offset = size, offset
    self.view = memoryview((ctypes.c_ubyte * size).from_address(self.addr)).cast("B")
    self.closed = False

  def __len__(self) -> int:
    return self.size

  def _check_range(self, offset: int, size: int):
    if offset < 0 or size < 0 or offset + size > self.size:
      raise ValueError(f"mapping range out of bounds: offset=0x{offset:x} size=0x{size:x} mapping_size=0x{self.size:x}")

  def view_at(self, offset: int = 0, size: int | None = None) -> memoryview:
    size = self.size - offset if size is None else size
    self._check_range(offset, size)
    return self.view[offset:offset + size]

  def read(self, offset: int, size: int) -> bytes:
    self._check_range(offset, size)
    return bytes(self.view[offset:offset + size])

  def write(self, offset: int, data):
    self.copy_from(offset, data)

  def copy_from(self, offset: int, src, size: int | None = None) -> int:
    view = memoryview(src)
    size = view.nbytes if size is None else size
    self._check_range(offset, size)
    if size > view.nbytes:
      raise ValueError(f"source buffer too small: need {size} bytes, have {view.nbytes}")
    if not view.c_contiguous:
      raise ValueError("source buffer must be C-contiguous")
    if view.readonly:
      self.view[offset:offset + size] = view.cast("B")[:size]
    else:
      src_addr = ctypes.addressof(ctypes.c_char.from_buffer(view))
      ctypes.memmove(ctypes.c_void_p(self.addr + offset), ctypes.c_void_p(src_addr), ctypes.c_size_t(size))
    return size

  def copy_to(self, offset: int, dst, size: int | None = None) -> int:
    view = memoryview(dst)
    size = view.nbytes if size is None else size
    self._check_range(offset, size)
    if view.readonly:
      raise ValueError("destination buffer must be writable")
    if size > view.nbytes:
      raise ValueError(f"destination buffer too small: need {size} bytes, have {view.nbytes}")
    if not view.c_contiguous:
      raise ValueError("destination buffer must be C-contiguous")
    dst_addr = ctypes.addressof(ctypes.c_char.from_buffer(view))
    ctypes.memmove(ctypes.c_void_p(dst_addr), ctypes.c_void_p(self.addr + offset), ctypes.c_size_t(size))
    return size

  def flush(self, offset: int = 0, size: int | None = None):
    size = self.size - offset if size is None else size
    if _libc.msync(ctypes.c_void_p(self.addr + offset), ctypes.c_size_t(size), MS_SYNC) != 0:
      raise OSError(ctypes.get_errno(), "msync failed")

  def close(self):
    if self.closed:
      return
    self.closed = True
    try:
      self.view.release()
    finally:
      if _libc.munmap(ctypes.c_void_p(self.addr), ctypes.c_size_t(self.size)) != 0:
        raise OSError(ctypes.get_errno(), "munmap failed")


class NocOrdering(Enum):
  RELAXED = 0
  STRICT = 1
  POSTED = 2


class TLBWindow:
  SIZE_2M = TLB_2M_SIZE
  SIZE_4G = TLB_4G_SIZE

  def __init__(self, dev, start: Core, end: Core | None = None, addr: int = 0,
               mode: NocOrdering = NocOrdering.STRICT, size: int = SIZE_2M, wc: bool = False):
    self.dev, self.size = dev, size
    self._id = dev.alloc_tlb(size)
    self.mm = dev.tlb_window(self._id, wc=wc)
    self.target(start, end, addr=addr, mode=mode)

  def target(self, start: Core, end: Core | None = None, addr: int = 0,
             mode: NocOrdering = NocOrdering.STRICT):
    end = end or start
    self.dev.configure_tlb(
      self._id, addr,
      x_start=start[0], y_start=start[1], x_end=end[0], y_end=end[1],
      mcast=int(end != start), ordering=mode.value,
    )

  def read(self, offset: int, size: int) -> bytes:
    return self.mm.read(offset, size)

  def write(self, offset: int, data: bytes):
    self.mm.write(offset, data)

  def close(self):
    try:
      self.mm.close()
    finally:
      self.dev.free_tlb(self._id)

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc, tb):
    self.close()


class PCIDevice:
  def __new__(cls, *args, **kwargs):
    if cls is PCIDevice and os.environ.get("EMU") == "1":
      os.environ["TT_USB"] = "1"
      from emu_pcie import EmuPCIDevice
      return object.__new__(EmuPCIDevice)
    return object.__new__(cls)

  def __init__(self, index: int = 0):
    self.index = index
    self.path = _devnode(index)
    if not os.path.exists(self.path):
      raise RuntimeError(f"Tenstorrent device {index} not found at {self.path}")
    self.fd = os.open(self.path, os.O_RDWR | os.O_CLOEXEC)
    self._closed = False
    self._tlbs: dict[int, tuple[int, int]] = {}
    self._pinnings: dict[int, tuple[int, int]] = {}

  @staticmethod
  def list_devices() -> list[str]:
    if os.environ.get("EMU") == "1":
      return ["emu:0000:00.0"]
    return _tenstorrent_devices()

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
    if bid_hi is None or bid_lo is None:
      raise RuntimeError("BOARD_ID telemetry is unavailable")
    board_id = (bid_hi & 0xFFFFFFFF) << 32 | (bid_lo & 0xFFFFFFFF)
    board_upi = (board_id >> 36) & 0xFFFFF
    board = BOARD_UPI_TO_NAME.get(board_upi)
    if board is None:
      raise RuntimeError(
        f"unsupported Blackhole board UPI 0x{board_upi:x}; supported boards are {', '.join(sorted(BOARD_UPI_TO_NAME.values()))}")

    enabled_gddr = self.telemetry_tag(layout, "ENABLED_GDDR")
    if enabled_gddr is None:
      raise RuntimeError("ENABLED_GDDR telemetry is unavailable")

    return _build_board_info(board, enabled_gddr & DEFAULT_GDDR_ENABLED, fast_dispatch)

  ARC_TILE = (8, 0)
  ARC_NOC_BASE = 0x80000000
  SCRATCH_RAM_2 = 0x30408
  SCRATCH_RAM_12 = 0x30430
  SCRATCH_RAM_13 = 0x30434

  def _arc_noc32(self, addr: int, value: int | None = None, tlb: int | None = None) -> int | None:
    owns_tlb = tlb is None
    tlb = self.alloc_tlb(TLB_2M_SIZE) if owns_tlb else tlb
    try:
      base = addr & ~(TLB_2M_SIZE - 1)
      arc_x, arc_y = self.ARC_TILE
      self.configure_tlb(tlb, base, arc_x, arc_y, arc_x, arc_y, ordering=1)
      win = self.tlb_window(tlb)
      try:
        off = addr - base
        if value is None:
          return struct.unpack("<I", win.read(off, 4))[0]
        win.write(off, struct.pack("<I", value & 0xFFFFFFFF))
      finally:
        win.close()
    finally:
      if owns_tlb:
        self.free_tlb(tlb)

  def read_arc_apb32(self, offset: int) -> int:
    return self._arc_noc32(self.ARC_NOC_BASE + offset)

  def _read_arc_noc32(self, addr: int, tlb: int | None = None) -> int:
    return self._arc_noc32(addr, tlb=tlb)

  def alloc_tlb(self, size: int) -> int:
    data = tenstorrent_allocate_tlb()
    data.in_.size = size
    _ioctl(self.fd, TENSTORRENT_IOCTL_ALLOCATE_TLB, data)
    self._tlbs[data.out.id] = (data.out.mmap_offset_uc, data.out.mmap_offset_wc)
    return data.out.id

  def free_tlb(self, index: int):
    data = tenstorrent_free_tlb()
    data.in_.id = index
    _ioctl(self.fd, TENSTORRENT_IOCTL_FREE_TLB, data)
    self._tlbs.pop(index, None)

  def configure_tlb(self, index: int, addr: int, x_start: int, y_start: int,
                    x_end: int, y_end: int, noc: int = 0, mcast: int = 0,
                    ordering: int = 1, linked: int = 0, static_vc: int = 0):
    data = tenstorrent_configure_tlb()
    data.in_.id = index
    data.in_.config = tenstorrent_noc_tlb_config(
      addr=addr, x_end=x_end, y_end=y_end, x_start=x_start, y_start=y_start,
      noc=noc, mcast=mcast, ordering=ordering, linked=linked, static_vc=static_vc,
    )
    _ioctl(self.fd, TENSTORRENT_IOCTL_CONFIGURE_TLB, data)

  def tlb_window(self, index: int, wc: bool = False) -> Mapping:
    if index not in self._tlbs:
      raise RuntimeError(f"TLB {index} is not allocated by this device fd")
    offset = self._tlbs[index][1 if wc else 0]
    size = TLB_4G_SIZE if index >= TLB_2M_COUNT else TLB_2M_SIZE
    return Mapping(size, fd=self.fd, offset=offset)

  def pin_pages(self, buf, preferred_iatu_region: int | None = None) -> int:
    va = _buffer_addr(buf)
    size = _buffer_size(buf)
    if va % mmap.PAGESIZE or size % mmap.PAGESIZE:
      raise ValueError("PIN_PAGES requires page-aligned address and page-sized mapping")
    data = tenstorrent_pin_pages()
    data.in_.output_size_bytes = ctypes.sizeof(data.out)
    data.in_.flags = TENSTORRENT_PIN_PAGES_NOC_DMA
    data.in_.virtual_address = va
    data.in_.size = size
    _ioctl(self.fd, TENSTORRENT_IOCTL_PIN_PAGES, data)
    self._pinnings[data.out.noc_address] = (va, size)
    return data.out.noc_address

  def unpin_pages(self, buf, noc_addr: int):
    va, size = self._pinnings.pop(noc_addr)
    data = tenstorrent_unpin_pages()
    data.in_.virtual_address = va
    data.in_.size = size
    _ioctl(self.fd, TENSTORRENT_IOCTL_UNPIN_PAGES, data)

  def set_power_state(self, busy: bool):
    if getattr(self, "_power_busy", None) == busy:
      return
    self._power_busy = busy
    data = tenstorrent_power_state()
    data.argsz = ctypes.sizeof(data)
    data.validity = TT_POWER_VALIDITY(TT_POWER_FLAG_COUNT, 0)
    if busy:
      data.power_flags = (
        TT_POWER_FLAG_MRISC_PHY_WAKEUP |
        TT_POWER_FLAG_TENSIX_ENABLE |
        TT_POWER_FLAG_L2CPU_ENABLE
      )
    _ioctl(self.fd, TENSTORRENT_IOCTL_SET_POWER_STATE, data)

  def close(self):
    if self._closed:
      return
    self._closed = True
    for tlb in list(self._tlbs):
      try:
        self.free_tlb(tlb)
      except Exception:
        pass
    if self.fd >= 0:
      os.close(self.fd)
      self.fd = -1

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc, tb):
    self.close()
