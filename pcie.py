import ctypes, fcntl, os
import ctypes.util

libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_long]
libc.mmap.restype = ctypes.c_void_p
libc.munmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
libc.munmap.restype = ctypes.c_int

IOCTL_MAGIC = 0xFA
TENSIX_X = (*range(1, 8), *range(10, 15))


def dram_tiles(enabled):
  """Return the translated tile used for each enabled DRAM bank."""
  enabled &= 0xFF
  banks = enabled.bit_count()
  if banks not in (7, 8):
    raise RuntimeError(f"unsupported Blackhole DRAM mask {enabled:#x}")

  missing = next((bank for bank in range(8) if not enabled >> bank & 1), 8)
  tiles = []
  for bank in range(banks):
    if banks == 8:
      x, slot = (17 if bank < 4 else 18), bank & 3
    elif missing < 4 and bank < 3:
      x, slot = 18, bank
    elif missing >= 4 and bank >= 4:
      x, slot = 18, bank - 4
    else:
      mirror = missing + 3 if missing < 4 else missing - 4
      order = range(3, 7) if missing < 4 else range(4)
      order = (*[candidate for candidate in order if candidate != mirror], mirror)
      x, slot = 17, order.index(bank)
    y = 12 + slot * 3
    # BRISC transfers even banks over NoC 0; NCRISC transfers odd banks over NoC 1.
    port = (2 if bank == 0 or bank >= 4 else 0) if bank % 2 == 0 else 1
    tiles.append((x, y + port))
  return tuple(tiles)

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

  def alloc(self, size: int, alignment: int | None = None):
    alignment = self.alignment if alignment is None else alignment
    offset = (self.next + alignment - 1) & -alignment
    if size < 0 or offset + size > self.end: raise MemoryError("allocator is out of memory")
    self.next = offset + size
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

  def alloc(self, size: int, alignment: int | None = None): return self.allocator.alloc(size, alignment)

  def read(self, offset: int, size: int) -> bytes: return ctypes.string_at(self.addr + offset, size)

  def write(self, offset: int, data: bytes): ctypes.memmove(self.addr + offset, data, len(data))

  def view(self, offset: int, size: int):
    return memoryview((ctypes.c_ubyte * size).from_address(self.addr + offset)).cast("B")

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

  def __init__(self, fd: int, core: tuple[int, int]):
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

  def mcast(self, addr: int, value, start, end, bytes=4):
    base = addr & -self.SIZE
    self.target(base, start, end)
    self.write(addr - base, value, bytes)

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
  SERVICE_CORES = ((14, 2), (14, 3), (14, 4))
  TENSIX_COUNT = 120
  COMPUTE_CORE_COUNT = TENSIX_COUNT - len(SERVICE_CORES)

  def __init__(self, index=0, sysmem_size=1 << 30):
    self.fd = os.open(f"/dev/tenstorrent/{index}", os.O_RDWR | os.O_CLOEXEC | os.O_APPEND)
    self.sysmem = None
    self.powered = False
    try:
      services = self.SERVICE_CORES
      self.tensix_cores = tuple(
        (x, y) for x in TENSIX_X for y in range(2, 12)
      )
      self.cores = [
        core for core in self.tensix_cores if core not in services
      ]
      assert len(self.tensix_cores) == self.TENSIX_COUNT
      assert len(self.cores) == self.COMPUTE_CORE_COUNT
      self.prefetch_core, self.dispatch_core, self.dma_core = services
      self.dram_tiles = dram_tiles(self._read_gddr_enabled())
      SetPowerState(self.fd, power_flags=0b1111)
      self.powered = True
      self.sysmem = Sysmem(self.fd, sysmem_size)
    except Exception:
      if self.powered:
        try: SetPowerState(self.fd, power_flags=0)
        except OSError: pass
      os.close(self.fd)
      self.fd = -1
      raise

  def _arc_telemetry(self):
    with TLBWindow(self.fd, (8, 0)) as window:
      window.target(0x80000000, (8, 0))
      pointer = int.from_bytes(window.read(0x30434, 4), "little")
      base, offset = pointer & -window.SIZE, pointer % window.SIZE
      window.target(base, (8, 0))
      return window.read(offset, 4096)

  def _read_gddr_enabled(self):
    telemetry = self._arc_telemetry()
    entry_count = int.from_bytes(telemetry[4:8], "little")
    if not 0 < entry_count <= 256:
      raise RuntimeError(f"invalid ARC telemetry entry count {entry_count}")
    for index in range(entry_count):
      entry = int.from_bytes(telemetry[8 + index * 4:12 + index * 4], "little")
      if entry & 0xFFFF == 36:
        data = 8 + entry_count * 4 + (entry >> 16) * 4
        return int.from_bytes(telemetry[data:data + 4], "little") & 0xFF
    raise RuntimeError("ARC telemetry is missing enabled GDDR banks")

  def close(self):
    if self.fd >= 0:
      if self.sysmem is not None: self.sysmem.close()
      if self.powered:
        SetPowerState(self.fd, power_flags=0)
        self.powered = False
      os.close(self.fd)
      self.fd = -1
