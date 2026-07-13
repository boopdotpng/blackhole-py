import ctypes, fcntl, os
import ctypes.util
from pathlib import Path
from typing import Tuple

libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_long]
libc.mmap.restype = ctypes.c_void_p
libc.munmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
libc.munmap.restype = ctypes.c_int
libc.msync.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
libc.msync.restype = ctypes.c_int

IOCTL_MAGIC = 0xFA

def _TT_IOCTL(nr, payload_type, result=None, **defaults):
  def call(fd, **kwargs):
    payload = payload_type(**(defaults | kwargs))
    fcntl.ioctl(fd, (IOCTL_MAGIC << 8) | nr, payload)
    return getattr(payload, result) if result else None
  return call

class PinPagesIn(ctypes.Structure):
  _fields_ = [
    ("_output_size_bytes", ctypes.c_uint32),
    ("_flags", ctypes.c_uint32),
    ("virtual_address", ctypes.c_uint64),
    ("size", ctypes.c_uint64),
  ]

class PinPagesOut(ctypes.Structure):
  _fields_ = [("_physical_address", ctypes.c_uint64), ("noc_address", ctypes.c_uint64)]

class PinPagesPayload(ctypes.Structure):
  _anonymous_ = ("in_", "out")
  _fields_ = [("in_", PinPagesIn), ("out", PinPagesOut)]

class UnpinPagesIn(ctypes.Structure):
  _fields_ = [("virtual_address", ctypes.c_uint64), ("size", ctypes.c_uint64), ("_reserved", ctypes.c_uint64)]

class UnpinPagesPayload(ctypes.Structure):
  _anonymous_ = ("in_",)
  _fields_ = [("in_", UnpinPagesIn)]

class AllocateTlbIn(ctypes.Structure):
  _fields_ = [("_size", ctypes.c_uint64), ("_reserved", ctypes.c_uint64)]

class AllocateTlbOut(ctypes.Structure):
  _fields_ = [
    ("id", ctypes.c_uint32),
    ("_reserved0", ctypes.c_uint32),
    ("mmap_offset_uc", ctypes.c_uint64),
    ("_mmap_offset_wc", ctypes.c_uint64),
    ("_reserved1", ctypes.c_uint64),
  ]

class AllocateTlbPayload(ctypes.Structure):
  _anonymous_ = ("in_", "out")
  _fields_ = [("in_", AllocateTlbIn), ("out", AllocateTlbOut)]

class FreeTlbIn(ctypes.Structure):
  _fields_ = [("id", ctypes.c_uint32)]

class FreeTlbPayload(ctypes.Structure):
  _anonymous_ = ("in_",)
  _fields_ = [("in_", FreeTlbIn)]

class NocTlbConfig(ctypes.Structure):
  _fields_ = [
    ("addr", ctypes.c_uint64),
    ("x_end", ctypes.c_uint16),
    ("y_end", ctypes.c_uint16),
    ("x_start", ctypes.c_uint16),
    ("y_start", ctypes.c_uint16),
    ("_noc_mcast", ctypes.c_uint8 * 2),
    ("_ordering", ctypes.c_uint8),
    ("_unused", ctypes.c_uint8 * 5),
    ("_reserved", ctypes.c_uint32 * 2),
  ]

class ConfigureTlbIn(ctypes.Structure):
  _anonymous_ = ("config",)
  _fields_ = [("id", ctypes.c_uint32), ("_reserved", ctypes.c_uint32), ("config", NocTlbConfig)]

class ConfigureTlbPayload(ctypes.Structure):
  _anonymous_ = ("in_",)
  _fields_ = [("in_", ConfigureTlbIn), ("_out_reserved", ctypes.c_uint64)]

  def __init__(self, id, addr, start, end=None):
    end = start if end is None else end
    super().__init__(in_=ConfigureTlbIn(id=id, config=NocTlbConfig(
      addr=addr, x_end=end[0], y_end=end[1], x_start=start[0], y_start=start[1],
      _noc_mcast=(ctypes.c_uint8 * 2)(0, start != end), _ordering=1)))

class PowerState(ctypes.Structure):
  _fields_ = [
    ("_argsz", ctypes.c_uint32),
    ("_unused", ctypes.c_uint8 * 5),
    ("_validity", ctypes.c_uint8),
    ("power_flags", ctypes.c_uint16),
    ("_power_settings", ctypes.c_uint16 * 14),
  ]

PinPages = _TT_IOCTL(
  7, PinPagesPayload, "out", _output_size_bytes=ctypes.sizeof(PinPagesOut),
  _flags=2,
)
UnpinPages = _TT_IOCTL(10, UnpinPagesPayload)
AllocateTlb = _TT_IOCTL(11, AllocateTlbPayload, "out", _size=1 << 21)
ConfigureTlb = _TT_IOCTL(13, ConfigureTlbPayload)
FreeTlb = _TT_IOCTL(12, FreeTlbPayload)
SetPowerState = _TT_IOCTL(15, PowerState, _argsz=ctypes.sizeof(PowerState), _validity=4)

class Allocator:
  def __init__(self, start: int, end: int, alignment: int = 1):
    self.next, self.end, self.alignment = start, end, alignment
    self.allocations = {}

  def alloc(self, size: int, alignment: int | None = None, name=None):
    alignment = self.alignment if alignment is None else alignment
    offset = (self.next + alignment - 1) & -alignment
    if size < 0 or offset + size > self.end: raise MemoryError("allocator is out of memory")
    self.next = offset + size
    if name is not None: self.allocations[name] = (offset, size)
    return offset

class Sysmem:
  PAGE_SIZE = os.sysconf("SC_PAGE_SIZE")

  def __init__(self, fd: int, size: int = 1 << 30):
    self.fd = fd
    self.size = (size + self.PAGE_SIZE - 1) & -self.PAGE_SIZE
    self.allocator = Allocator(0, self.size, self.PAGE_SIZE)
    self.addr = libc.mmap(None, self.size, 3, 0x21, -1, 0)
    if self.addr == ctypes.c_void_p(-1).value:
      raise OSError(ctypes.get_errno(), "mmap sysmem failed")
    try:
      self.noc_addr = PinPages(fd, virtual_address=self.addr, size=self.size).noc_address
    except Exception:
      libc.munmap(self.addr, self.size)
      self.addr = None
      raise

  def alloc(self, size: int, alignment: int | None = None, name=None): return self.allocator.alloc(size, alignment, name)

  def read(self, offset: int, size: int) -> bytes: return ctypes.string_at(self.addr + offset, size)

  def write(self, offset: int, data: bytes): ctypes.memmove(self.addr + offset, data, len(data))

  def flush(self):
    if libc.msync(self.addr, self.size, 4) != 0: raise OSError(ctypes.get_errno(), "msync sysmem failed")

  def close(self):
    if self.noc_addr is not None:
      UnpinPages(self.fd, virtual_address=self.addr, size=self.size)
      self.noc_addr = None
    if self.addr is not None:
      if libc.munmap(self.addr, self.size) != 0:
        raise OSError(ctypes.get_errno(), "munmap sysmem failed")
      self.addr = None

class TLBWindow:
  SIZE = 1 << 21
  USER_ID_LIMIT = 201

  def __init__(self, fd: int, core: Tuple[int, int]):
    tlb = AllocateTlb(fd)
    self.fd, self.id, self.core = fd, tlb.id, core
    if self.id >= self.USER_ID_LIMIT:
      FreeTlb(fd, id=self.id)
      raise RuntimeError(f"driver returned reserved TLB id {self.id}")
    self.addr = libc.mmap(None, self.SIZE, 3, 1, fd, tlb.mmap_offset_uc)
    if self.addr == ctypes.c_void_p(-1).value:
      error = OSError(ctypes.get_errno(), "mmap TLB failed")
      FreeTlb(fd, id=self.id)
      self.id, self.addr = None, None
      raise error

  def target(self, addr: int, start=None, end=None):
    ConfigureTlb(self.fd, id=self.id, addr=addr, start=self.core if start is None else start, end=end)

  def read(self, offset: int, bytes=4): return ctypes.string_at(self.addr + offset, bytes)

  def write(self, offset: int, value, bytes=4):
    data = value.to_bytes(bytes, "little") if isinstance(value, int) else value
    ctypes.memmove(self.addr + offset, data, len(data))

  def close(self):
    if self.addr is not None:
      if libc.munmap(self.addr, self.SIZE) != 0:
        raise OSError(ctypes.get_errno(), "munmap TLB failed")
      self.addr = None
    if self.id is not None:
      FreeTlb(self.fd, id=self.id)
      self.id = None

  def __enter__(self): return self

  def __exit__(self, exc_type, exc, tb): self.close()

class PCIDevice:
  ARC_CORE = (8, 0)
  ARC_NOC_BASE = 0x80000000
  SCRATCH_RAM_12 = 0x30430
  SCRATCH_RAM_13 = 0x30434
  ENABLED_GDDR_TAG = 36
  P100A_X = (*range(1, 8), *range(10, 15))
  prefetch_core = (14, 2)
  dispatch_core = (14, 3)

  def __init__(self, index=0, sysmem_size=1 << 30):
    card_type = Path(f"/sys/class/tenstorrent/tenstorrent!{index}/tt_card_type").read_text().strip()
    if card_type != "p100a": raise RuntimeError(f"unsupported Blackhole card {card_type}; only p100a is supported")

    self.fd = os.open(f"/dev/tenstorrent/{index}", os.O_RDWR | os.O_CLOEXEC | os.O_APPEND)
    SetPowerState(self.fd, power_flags=0b1111)
    enabled_gddr = self._read_enabled_gddr() & 0xFF
    harvested = [bank for bank in range(8) if not enabled_gddr >> bank & 1]
    if len(harvested) != 1:
      raise RuntimeError(f"P100A requires exactly one harvested DRAM bank, got {harvested}")
    self.harvested_dram_bank = harvested[0]
    cq_cores = {self.prefetch_core, self.dispatch_core}
    self.cores = [(x, y) for x in self.P100A_X for y in range(2, 12) if (x, y) not in cq_cores]
    self.sysmem = Sysmem(self.fd, sysmem_size)

  def _read_enabled_gddr(self):
    with TLBWindow(self.fd, self.ARC_CORE) as win:
      win.target(self.ARC_NOC_BASE)
      table_base = int.from_bytes(win.read(self.SCRATCH_RAM_13), "little")
      data_base = int.from_bytes(win.read(self.SCRATCH_RAM_12), "little")
      if table_base in (0, 0xFFFFFFFF) or data_base in (0, 0xFFFFFFFF):
        raise RuntimeError(f"invalid ARC telemetry pointers table=0x{table_base:x} data=0x{data_base:x}")

      table_window = table_base & -win.SIZE
      win.target(table_window)
      entry_count = int.from_bytes(win.read(table_base + 4 - table_window), "little")
      if entry_count in (0, 0xFFFFFFFF) or entry_count > 4096:
        raise RuntimeError(f"invalid ARC telemetry entry count: {entry_count}")
      for i in range(entry_count):
        entry = int.from_bytes(win.read(table_base + 8 + i * 4 - table_window), "little")
        if entry & 0xFFFF == self.ENABLED_GDDR_TAG:
          data_window = data_base & -win.SIZE
          win.target(data_window)
          return int.from_bytes(win.read(data_base + (entry >> 16) * 4 - data_window), "little")
      raise RuntimeError("missing enabled_gddr ARC telemetry tag")

  def close(self):
    if self.fd >= 0:
      self.sysmem.close()
      SetPowerState(self.fd, power_flags=0)
      os.close(self.fd)
      self.fd = -1
