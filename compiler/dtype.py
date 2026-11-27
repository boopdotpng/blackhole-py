import math
from dataclasses import dataclass
from typing import ClassVar

class InvalidType:
  _instance: ClassVar["InvalidType | None"] = None
  def __new__(cls):
    if cls._instance is None: cls._instance = super().__new__(cls)
    return cls._instance
  def __eq__(self, other): return self is other if isinstance(other, InvalidType) else NotImplemented
  def __hash__(self): return hash("Invalid")
  def __repr__(self): return "Invalid"
  def __reduce__(self): return (InvalidType, ())

Invalid = InvalidType()

@dataclass(frozen=True)
class DType:
  name: str
  bits: int
  is_float: bool = False
  is_signed: bool = False

  @property
  def itemsize(self) -> int: return self.bits // 8
  @property
  def is_int(self) -> bool: return not self.is_float and self.bits >= 8
  @property
  def min(self):
    if self is dtypes.bool: return False
    if self.is_float: return -math.inf
    if self is dtypes.weakint: return -(1 << 63)
    return -(1 << (self.bits - 1)) if self.is_signed else 0
  @property
  def max(self):
    if self is dtypes.bool: return True
    if self.is_float: return math.inf
    if self is dtypes.weakint: return (1 << 63) - 1
    return (1 << (self.bits - 1)) - 1 if self.is_signed else (1 << self.bits) - 1
  def const(self, v):
    if v is Invalid: return Invalid
    return bool(v) if self is dtypes.bool else float(v) if self.is_float else int(v)
  def __repr__(self) -> str: return f"dtypes.{self.name}"

class dtypes:
  void = DType("void", 0)
  bool = DType("bool", 1)
  u8   = DType("u8",   8)
  i32  = DType("i32",  32, is_signed=True)
  u32  = DType("u32",  32)
  u64  = DType("u64",  64)
  bf16 = DType("bf16", 16, is_float=True, is_signed=True)
  fp32 = DType("fp32", 32, is_float=True, is_signed=True)
  bfp8 = DType("bfp8", 8,  is_float=True, is_signed=True)
  bfp4 = DType("bfp4", 4,  is_float=True, is_signed=True)
  e4m3 = DType("e4m3", 8,  is_float=True, is_signed=True)
  # python constants: they take the dtype of whatever they meet (32-bit if they reach codegen alone)
  weakint = DType("weakint", 32, is_signed=True)
  weakfloat = DType("weakfloat", 32, is_float=True, is_signed=True)
  weaks = (weakint, weakfloat)

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
  wints = (u8, i32, u32, u64, weakint)
  swints = (i32, weakint)

  _by_name = {d.name: d for d in (void, bool, u8, i32, u32, u64, bf16, fp32, bfp8, bfp4, e4m3, weakint, weakfloat)}
  _aliases = {"float32": fp32, "float": fp32, "bfloat16": bf16, "int32": i32, "int": i32, "uint32": u32, "uint64": u64, "uint8": u8}

  @classmethod
  def from_name(cls, name: str | DType) -> DType:
    if isinstance(name, DType): return name
    if name in cls._by_name: return cls._by_name[name]
    if name in cls._aliases: return cls._aliases[name]
    raise ValueError(f"unknown dtype {name!r}")

  @staticmethod
  def from_py(v) -> DType:
    if isinstance(v, (list, tuple)): return least_upper_dtype(*(dtypes.from_py(x) for x in v)) if v else dtypes.weakfloat
    if v is Invalid: return dtypes.bool
    return dtypes.bool if isinstance(v, bool) else dtypes.weakint if isinstance(v, int) else dtypes.weakfloat

_DTYPE_RANK = {
  dtypes.bool: 0, dtypes.u8: 1, dtypes.i32: 2, dtypes.u32: 3, dtypes.u64: 4,
  dtypes.bfp4: 5, dtypes.bfp8: 6, dtypes.e4m3: 7, dtypes.bf16: 8, dtypes.fp32: 9,
}

# a weak dtype gives way to any real dtype of its kind: weakint + bf16 = bf16, weakfloat + i32 = fp32, weakint + weakfloat = weakfloat
def _join(dt: DType, other: DType) -> DType:
  if dt.name.startswith("weak") or other.name.startswith("weak"):
    weak, real = (dt, other) if dt.name.startswith("weak") else (other, dt)
    if real.name.startswith("weak") or real is dtypes.bool: return dtypes.weakfloat if dtypes.weakfloat in (dt, other) else weak
    return real if (real.is_float or weak is dtypes.weakint) else dtypes.fp32
  return least_upper_dtype(dt, other)

def least_upper_dtype(*dts: DType) -> DType:
  dt = dts[0]
  for other in dts[1:]:
    if other == dt: continue
    if any(d.name.startswith("weak") for d in (dt, other)):
      dt = _join(dt, other)
      continue
    if dt.is_float and other.is_float:
      if {dt, other} <= {dtypes.bfp4, dtypes.bfp8, dtypes.e4m3}: dt = dtypes.bf16
      else: dt = dt if _DTYPE_RANK[dt] >= _DTYPE_RANK[other] else other
    elif dt.is_float or other.is_float:
      flt = dt if dt.is_float else other
      dt = flt if flt in (dtypes.bf16, dtypes.fp32) else dtypes.fp32
    else:
      dt = dt if _DTYPE_RANK[dt] >= _DTYPE_RANK[other] else other
  return dt

def can_lossless_cast(dt0: DType, dt1: DType) -> bool:
  if dt0 == dt1: return True
  if dt0 in dtypes.weaks or dt1 in dtypes.weaks or dt0 is dtypes.void or dt1 is dtypes.void: return False
  if dt0 is dtypes.bool: return True
  if dt0 is dtypes.u8: return dt1 in (dtypes.i32, dtypes.u32, dtypes.u64, dtypes.bf16, dtypes.fp32)
  if dt0 is dtypes.u32: return dt1 is dtypes.u64
  if dt0 is dtypes.bfp4: return dt1 in (dtypes.bfp8, dtypes.bf16, dtypes.fp32)
  if dt0 is dtypes.bfp8: return dt1 in (dtypes.bf16, dtypes.fp32)
  if dt0 is dtypes.e4m3: return dt1 in (dtypes.bf16, dtypes.fp32)
  if dt0 is dtypes.bf16: return dt1 is dtypes.fp32
  return False
