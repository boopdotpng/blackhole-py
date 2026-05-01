import ctypes, mmap, os, struct, time
from enum import Enum
from pcie import PCIDevice, TLB_2M_SIZE, TLB_4G_SIZE

Core = tuple[int, int]
PAGE_SIZE = 4096
L1_ALIGN = 16
PCIE_ALIGN = 64

def align_up(value: int, align: int) -> int:
  return (value + align - 1) // align * align

def align_down(value: int, alignment: int) -> tuple[int, int]:
  base = value & ~(alignment - 1)
  return base, value - base

def as_bytes(obj) -> bytes:
  return ctypes.string_at(ctypes.addressof(obj), ctypes.sizeof(obj))

def noc_xy(x: int, y: int) -> int:
  return ((y << 6) | x) & 0xFFFF

class S(ctypes.LittleEndianStructure):
  """Still used by dispatch.py for launch message structs."""
  def __init__(self, **kw):
    super().__init__()
    for k, v in kw.items(): setattr(self, k, v)

class TensixL1:
  SIZE = 0x180000
  LAUNCH = 0x70
  GO_MSG = 0x370
  GO_MSG_INDEX = 0x3A0
  KERNEL_CONFIG_BASE = 0x86B0
  BRISC_FIRMWARE_BASE = 0x3840
  DATA_BUFFER_SPACE_BASE = 0x37000
  TIMING_CONTROL = 0x9C0

  FW_INIT_SCRATCH_BASE = 0x82B0
  BRISC_INIT_LOCAL_L1_BASE_SCRATCH = 0x82B0
  NCRISC_INIT_LOCAL_L1_BASE_SCRATCH = 0xA2B0
  TRISC0_INIT_LOCAL_L1_BASE_SCRATCH = 0xC2B0
  TRISC1_INIT_LOCAL_L1_BASE_SCRATCH = 0xD2B0
  TRISC2_INIT_LOCAL_L1_BASE_SCRATCH = 0xE2B0
  NCRISC_INIT_IRAM_L1_BASE_SCRATCH = 0xF2B0
  MEM_BANK_TO_NOC_SCRATCH = 0x112B0
  LOGICAL_TO_VIRTUAL_SCRATCH = 0x11AB0

  @classmethod
  def firmware_init_scratch(cls) -> dict[str, int]:
    return {
      "brisc": cls.BRISC_INIT_LOCAL_L1_BASE_SCRATCH,
      "ncrisc": cls.NCRISC_INIT_LOCAL_L1_BASE_SCRATCH,
      "trisc0": cls.TRISC0_INIT_LOCAL_L1_BASE_SCRATCH,
      "trisc1": cls.TRISC1_INIT_LOCAL_L1_BASE_SCRATCH,
      "trisc2": cls.TRISC2_INIT_LOCAL_L1_BASE_SCRATCH,
    }

  @classmethod
  def cache_key(cls) -> tuple[tuple[str, int], ...]:
    return tuple(sorted(cls.firmware_init_scratch().items())) + (
      ("bank_to_noc_scratch", cls.MEM_BANK_TO_NOC_SCRATCH),
      ("logical_to_virtual_scratch", cls.LOGICAL_TO_VIRTUAL_SCRATCH),
      ("kernel_config_base", cls.KERNEL_CONFIG_BASE),
      ("brisc_firmware_base", cls.BRISC_FIRMWARE_BASE),
    )

class TensixMMIO:
  LOCAL_RAM_START = 0xFFB00000
  LOCAL_RAM_END = 0xFFB01FFF
  RISCV_DEBUG_REG_SOFT_RESET_0 = 0xFFB121B0
  RISCV_DEBUG_REG_TRISC0_RESET_PC = 0xFFB12228
  RISCV_DEBUG_REG_TRISC1_RESET_PC = 0xFFB1222C
  RISCV_DEBUG_REG_TRISC2_RESET_PC = 0xFFB12230
  RISCV_DEBUG_REG_NCRISC_RESET_PC = 0xFFB12238
  SOFT_RESET_ALL = 0x47800                 # all 5 RISC-V cores
  SOFT_RESET_BRISC_ONLY_RUN = 0x47000      # keep TRISC/NCRISC in reset, release BRISC

class Arc:
  NOC_BASE = 0x80000000
  RESET_UNIT_OFFSET = 0x30000
  SCRATCH_RAM_12 = RESET_UNIT_OFFSET + 0x430
  SCRATCH_RAM_13 = RESET_UNIT_OFFSET + 0x434
  TAG_TENSIX_ENABLED_COL = 34
  DEFAULT_TENSIX_ENABLED = 0x3FFF
  TAG_GDDR_ENABLED = 36
  DEFAULT_GDDR_ENABLED = 0xFF

class Dram:
  BANK_COUNT = 8
  TILES_PER_BANK = 3
  WRITE_OFFSET = 0x40
  BARRIER_BASE = 0x0
  ALIGNMENT = 64
  BARRIER_FLAGS = (0xAA, 0xBB)
  BANK_TILE_YS = {
    0: (0, 1, 11), 1: (2, 3, 10), 2: (4, 8, 9), 3: (5, 6, 7),
    4: (0, 1, 11), 5: (2, 3, 10), 6: (4, 8, 9), 7: (5, 6, 7),
  }
  BANK_X = {b: 0 if b < 4 else 9 for b in range(8)}

class _OffsetView:
  """Wraps an mmap with a base offset so mm[i] and mm[a:b] address within a TLB window."""
  __slots__ = ('_m', '_b', '_s')
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
        raise IndexError("mmap slice assignment is wrong size")
      struct.pack_into(f"<{len(data)}s", self._m, start, data)
    else:
      struct.pack_into("B", self._m, self._b + key, value)

class NocOrdering(Enum):
  RELAXED = 0
  STRICT = 1
  POSTED = 2

class TLBWindow:
  SIZE_2M = TLB_2M_SIZE
  SIZE_4G = TLB_4G_SIZE

  def __init__(self, dev: PCIDevice, start: Core, end: Core | None = None, addr: int = 0,
               mode: NocOrdering = NocOrdering.STRICT, size: int = SIZE_2M, wc: bool = False):
    self.dev, self.size = dev, size
    self._id = dev.alloc_tlb(size)
    self._bar, self._base = dev.tlb_window(self._id, wc=wc)
    self.mm = _OffsetView(self._bar, self._base, size)
    self.target(start, end, addr=addr, mode=mode)

  def target(self, start: Core, end: Core | None = None, addr: int = 0, mode: NocOrdering = NocOrdering.STRICT):
    end = end or start
    self.dev.configure_tlb(self._id, addr,
      x_start=start[0], y_start=start[1], x_end=end[0], y_end=end[1],
      mcast=int(end != start), ordering=mode.value)

  def read32(self, offset: int) -> int:
    o = self._base + offset
    return self._bar.cast("I")[o // 4]

  def write32(self, offset: int, value: int):
    o = self._base + offset
    self._bar.cast("I")[o // 4] = value & 0xFFFFFFFF

  def write(self, addr: int, data: bytes):
    o = self._base + addr
    struct.pack_into(f"<{len(data)}s", self._bar, o, data)

  def close(self):
    self.dev.free_tlb(self._id)

  def __enter__(self): return self
  def __exit__(self, *_): self.close()

class Sysmem:
  PCIE_NOC_XY = (24 << 6) | 19

  def __init__(self, dev: PCIDevice, size: int = 1 << 30):
    if size > 1 << 30:
      raise ValueError(f"Sysmem size {size} exceeds 1 GiB iATU aperture limit")
    self.dev = dev
    page_size = os.sysconf("SC_PAGE_SIZE")
    self.size = (size + page_size - 1) & ~(page_size - 1)
    self.buf = mmap.mmap(-1, self.size, flags=mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS,
                         prot=mmap.PROT_READ | mmap.PROT_WRITE)
    self.noc_addr = dev.pin_pages(self.buf)

  def close(self):
    self.dev.unpin_pages(self.buf, self.noc_addr)
    self.buf.close()

class TileGrid:
  ARC = (8, 0)

def worker_cores(tensix_x: tuple[int, ...]) -> list[Core]:
  return [(x, y) for x in tensix_x for y in range(2, 12)]

def active_tensix_core_count(enabled_col_mask: int) -> int:
  return (enabled_col_mask & Arc.DEFAULT_TENSIX_ENABLED).bit_count() * 10

USE_USB_DISPATCH = os.environ.get("TT_USB") == "1"

def build_bank_noc_table(harvested_dram_banks: list[int], worker_cores: list[Core]) -> bytes:
  num_dram_banks = Dram.BANK_COUNT - len(harvested_dram_banks)
  num_l1_banks = len(worker_cores)
  NOCS, PORTS = 2, 3
  # per-bank NOC port selection: bank -> [noc0_port, noc1_port]
  BANK_PORT = [[2,1],[0,1],[0,1],[0,1],[2,1],[2,1],[2,1],[2,1]]

  if len(harvested_dram_banks) == 0:
    # P150-style: all 8 banks, straightforward layout
    bank_xy = {}
    for b in range(Dram.BANK_COUNT):
      x = 17 if b < 4 else 18
      bank_xy[b] = (x, 12 + (b % 4) * PORTS)
  elif len(harvested_dram_banks) == 1:
    # P100-style: 7 banks, harvested bank's mirror pushed to last slot
    h = harvested_dram_banks[0]
    half = 4
    mirror = h + half - 1 if h < half else h - half
    if h < half:
      right = list(range(half - 1))
      left = [b for b in range(half - 1, Dram.BANK_COUNT - 1) if b != mirror] + [mirror]
    else:
      left = [b for b in range(half) if b != mirror] + [mirror]
      right = list(range(half, Dram.BANK_COUNT - 1))
    bank_xy = {}
    for i, b in enumerate(right):
      bank_xy[b] = (18, 12 + i * PORTS)
    for i, b in enumerate(left):
      bank_xy[b] = (17, 12 + i * PORTS)
  else:
    raise ValueError(f"unsupported harvested DRAM bank count: {len(harvested_dram_banks)}")

  # DRAM section: noc_xy per (noc, bank), selecting the right port
  dram = []
  for noc in range(NOCS):
    for b in range(num_dram_banks):
      x, y0 = bank_xy[b]
      dram.append(noc_xy(x, y0 + BANK_PORT[b][noc]))

  # L1 section: worker cores in column-major order, same for both NOCs
  cols = sorted({x for x, _ in worker_cores})
  l1 = []
  for _ in range(NOCS):
    for i in range(num_l1_banks):
      l1.append(noc_xy(cols[i % len(cols)], 2 + (i // len(cols)) % 10))

  return struct.pack(f"<{len(dram)}H{len(l1)}H{num_dram_banks + num_l1_banks}i", *dram, *l1, *([0] * (num_dram_banks + num_l1_banks)))
