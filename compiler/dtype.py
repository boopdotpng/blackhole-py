from dataclasses import dataclass
from enum import Enum, IntEnum, auto
from hw import cfg

@dataclass(frozen=True)
class DType:
  name: str
  bits: int
  tile_bytes: int = 0   # bytes per 32x32 (1024-element) tile
  is_float: bool = False
  is_signed: bool = False
  fmt: cfg.DataFormat | None = None
  host: str = ""        # numpy type the host sees; bf16, bfp8 and e4m3 are raw bits there

  @property
  def itemsize(self) -> int: return self.bits // 8
  @property
  def is_int(self) -> bool: return not self.is_float and self.bits >= 8
  def __repr__(self) -> str: return f"dtypes.{self.name}"

class dtypes:
  void = DType("void", 0)
  bool = DType("bool", 1)
  u8   = DType("u8",   8,  tile_bytes=1024, host="uint8")
  i32  = DType("i32",  32, tile_bytes=4096, is_signed=True, fmt=cfg.DataFormat.INT32, host="int32")
  u32  = DType("u32",  32, tile_bytes=4096, host="uint32")
  u64  = DType("u64",  64, tile_bytes=8192, host="uint64")
  bf16 = DType("bf16", 16, tile_bytes=2048, is_float=True, is_signed=True, fmt=cfg.DataFormat.FLOAT16_B, host="uint16")
  fp32 = DType("fp32", 32, tile_bytes=4096, is_float=True, is_signed=True, fmt=cfg.DataFormat.FLOAT32, host="float32")
  bfp8 = DType("bfp8", 8,  tile_bytes=1088, is_float=True, is_signed=True, fmt=cfg.DataFormat.BFP8_B, host="uint8")
  bfp4 = DType("bfp4", 4,  tile_bytes=576,  is_float=True, is_signed=True, fmt=cfg.DataFormat.BFP4_B, host="uint8")
  e4m3 = DType("e4m3", 8,  tile_bytes=1024, is_float=True, is_signed=True, fmt=cfg.DataFormat.LF8, host="uint8")

  # tinygrad-compatible aliases
  float32 = float = fp32
  bfloat16 = bf16
  int32 = int = i32
  uint32 = u32
  uint64 = u64
  uint8 = u8

  floats = (bfp4, bfp8, e4m3, bf16, fp32)
  ints = (u8, i32, u32, u64)
  sints = (i32,)
  uints = (u8, u32, u64)

  _by_name = {d.name: d for d in (void, bool, u8, i32, u32, u64, bf16, fp32, bfp8, bfp4, e4m3)}
  _aliases = {"float32": fp32, "float": fp32, "bfloat16": bf16, "int32": i32, "int": i32, "uint32": u32, "uint64": u64, "uint8": u8}

  @classmethod
  def from_name(cls, name: str | DType) -> DType:
    if isinstance(name, DType): return name
    if name in cls._by_name: return cls._by_name[name]
    if name in cls._aliases: return cls._aliases[name]
    raise ValueError(f"unknown dtype {name!r}")

  @classmethod
  def from_host(cls, name: str) -> DType | None:
    # the dtype a numpy array of this type uploads as, if it holds real values rather than raw bits
    return next((d for d in cls._by_name.values() if d.host == name and d.is_float == name.startswith("float")), None)

_DTYPE_RANK = {
  dtypes.bool: 0, dtypes.u8: 1, dtypes.i32: 2, dtypes.u32: 3, dtypes.u64: 4,
  dtypes.bfp4: 5, dtypes.bfp8: 6, dtypes.e4m3: 7, dtypes.bf16: 8, dtypes.fp32: 9,
}

def least_upper_dtype(*dts: DType) -> DType:
  dt = dts[0]
  for other in dts[1:]:
    if other == dt: continue
    if dt.is_float and other.is_float:
      if {dt, other} <= {dtypes.bfp4, dtypes.bfp8, dtypes.e4m3}: dt = dtypes.bf16
      else: dt = dt if _DTYPE_RANK[dt] >= _DTYPE_RANK[other] else other
    elif dt.is_float or other.is_float:
      flt = dt if dt.is_float else other
      dt = flt if flt in (dtypes.bf16, dtypes.fp32) else dtypes.fp32
    else:
      dt = dt if _DTYPE_RANK[dt] >= _DTYPE_RANK[other] else other
  return dt

class Space(Enum):
  NONE   = auto()  # void / side effects
  TENSOR = auto()  # Layer 0 whole-chip logical tensor (before sharding / engine selection)
  SCALAR = auto()  # RV32 scalar glue & indices
  REG    = auto()  # ISA virtual/physical register (RV32 x0..x31)
  DRAM   = auto()  # off-chip DRAM
  HOST   = auto()  # pinned host sysmem
  L1     = auto()  # worker L1 SRAM (CBs, persistent slabs, Pack_L1_Acc)
  SRCA   = auto()  # Tensix SrcA register bank
  SRCB   = auto()  # Tensix SrcB register bank
  DST    = auto()  # Tensix Dst register tiles (FPU / SFPU)
  LREG   = auto()  # SFPU 32-lane vector register (L0..L7, L8..L15)

  def __repr__(self) -> str: return f"Space.{self.name}"

# each phase multiplies 5 bits of SrcA by 7 bits of SrcB
class Fidelity(IntEnum):
  LOFI  = 1
  HIFI2 = 2
  HIFI3 = 3
  HIFI4 = 4

  def __repr__(self) -> str: return f"Fidelity.{self.name}"

def default_fidelity(a: DType, b: DType) -> Fidelity:
  if dtypes.fp32 in (a, b): return Fidelity.HIFI4
  if dtypes.bf16 in (a, b): return Fidelity.HIFI2
  return Fidelity.LOFI
