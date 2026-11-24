from __future__ import annotations
import collections, inspect, itertools, math, struct, weakref
from dataclasses import dataclass
from enum import Enum, IntEnum, auto
from typing import Any, Callable, Sequence
import hw

# ---- dtypes & memory spaces ----

@dataclass(frozen=True)
class DType:
  name: str
  bits: int
  tile_bytes: int = 0   # bytes per 32x32 (1024-element) tile
  is_float: bool = False
  is_signed: bool = False
  fmt: hw.DataFormat | None = None

  @property
  def itemsize(self) -> int: return self.bits // 8
  @property
  def is_int(self) -> bool: return not self.is_float and self.bits >= 8
  def __repr__(self) -> str: return f"dtypes.{self.name}"


class dtypes:
  void = DType("void", 0)
  bool = DType("bool", 1)
  u8   = DType("u8",   8,  tile_bytes=1024)
  i32  = DType("i32",  32, tile_bytes=4096, is_signed=True, fmt=hw.DataFormat.INT32)
  u32  = DType("u32",  32, tile_bytes=4096)
  u64  = DType("u64",  64, tile_bytes=8192)
  bf16 = DType("bf16", 16, tile_bytes=2048, is_float=True, is_signed=True, fmt=hw.DataFormat.FLOAT16_B)
  fp32 = DType("fp32", 32, tile_bytes=4096, is_float=True, is_signed=True, fmt=hw.DataFormat.FLOAT32)
  bfp8 = DType("bfp8", 8,  tile_bytes=1088, is_float=True, is_signed=True, fmt=hw.DataFormat.BFP8_B)
  e4m3 = DType("e4m3", 8,  tile_bytes=1024, is_float=True, is_signed=True, fmt=hw.DataFormat.LF8)

  floats = (bf16, fp32, bfp8, e4m3)
  ints = (u8, i32, u32, u64)
  _by_name = {d.name: d for d in (void, bool, u8, i32, u32, u64, bf16, fp32, bfp8, e4m3)}

  @classmethod
  def from_name(cls, name: str | DType) -> DType:
    if isinstance(name, DType): return name
    if name not in cls._by_name: raise ValueError(f"unknown dtype {name!r}")
    return cls._by_name[name]


class Space(Enum):
  NONE   = auto()  # void / side effects
  SCALAR = auto()  # RV32 scalar glue & indices
  DRAM   = auto()  # off-chip DRAM
  HOST   = auto()  # pinned host sysmem (HostStream)
  L1     = auto()  # worker L1 SRAM (CBs, persistent slabs, Pack_L1_Acc)
  SRCA   = auto()  # Tensix SrcA register bank
  SRCB   = auto()  # Tensix SrcB register bank
  DST    = auto()  # Tensix Dst register tiles (FPU / SFPU)
  LREG   = auto()  # SFPU 32-lane vector register (L0..L7)

  def __repr__(self) -> str: return f"Space.{self.name}"


class Fidelity(IntEnum):
  """Blackhole FPU math fidelity phases (5-bit SrcA x 7-bit SrcB multiplier per phase)."""
  LOFI  = 1
  HIFI2 = 2
  HIFI3 = 3
  HIFI4 = 4

  def __repr__(self) -> str: return f"Fidelity.{self.name}"


def default_fidelity(a: DType, b: DType) -> Fidelity:
  """Auto-select FPU fidelity phases from operand dtypes (overrideable per op)."""
  if dtypes.fp32 in (a, b): return Fidelity.HIFI4
  if dtypes.bf16 in (a, b): return Fidelity.HIFI2
  return Fidelity.LOFI


# ---- opcodes ----

class Ops(Enum):
  # graph structure & sync
  SINK = auto()
  AFTER = auto()
  BARRIER = auto()

  # grid, control & residency
  CONST = auto()
  SPECIAL = auto()
  BUFFER = auto()
  ALLOC = auto()
  RANGE = auto()
  END = auto()
  IF = auto()
  REDUCE = auto()
  CARRY = auto()
  LOOP = auto()
  GET = auto()
  LOAD = auto()
  STORE = auto()

  # NoC movement
  NOC_READ = auto()
  NOC_WRITE = auto()
  NOC_MCAST = auto()
  NOC_GATHER = auto()
  NOC_ALLGATHER = auto()

  # Tensix engines
  UNPACK = auto()
  MVMUL = auto()
  PACK = auto()

  # escape hatch for explicit Tensix micro-kernels
  REPLAY = auto()
  MOP = auto()

  # ALU (scalar RV32 when operands are SCALAR; SFPU vector when any operand is DST)
  ADD = auto(); SUB = auto(); MUL = auto(); DIV = auto(); MOD = auto()
  MULACC = auto()
  MAX = auto(); MIN = auto(); NEG = auto(); ABS = auto()
  EXP2 = auto(); LOG2 = auto(); SIN = auto(); SQRT = auto(); RSQRT = auto(); RECIP = auto()
  CMPLT = auto(); CMPEQ = auto(); CMPNE = auto(); WHERE = auto()
  AND = auto(); OR = auto(); XOR = auto(); NOT = auto(); SHL = auto(); SHR = auto()
  CAST = auto(); BITCAST = auto()

  # SFPU tile/lane & lowered hardware primitives
  LANE_ID = auto()
  REDUCE_ROW = auto()
  REDUCE_LANES = auto()
  ARGMAX = auto()
  SFPU = auto()


class GroupOp:
  Unary = frozenset({Ops.NEG, Ops.ABS, Ops.NOT, Ops.EXP2, Ops.LOG2, Ops.SIN, Ops.SQRT, Ops.RSQRT, Ops.RECIP})
  Binary = frozenset({
    Ops.ADD, Ops.SUB, Ops.MUL, Ops.DIV, Ops.MOD, Ops.MAX, Ops.MIN,
    Ops.CMPLT, Ops.CMPEQ, Ops.CMPNE, Ops.AND, Ops.OR, Ops.XOR, Ops.SHL, Ops.SHR,
  })
  Ternary = frozenset({Ops.WHERE, Ops.MULACC})
  ALU = Unary | Binary | Ternary
  Comparison = frozenset({Ops.CMPLT, Ops.CMPEQ, Ops.CMPNE})
  Commutative = frozenset({Ops.ADD, Ops.MUL, Ops.MAX, Ops.MIN, Ops.CMPEQ, Ops.CMPNE, Ops.AND, Ops.OR, Ops.XOR})
  NoC = frozenset({Ops.NOC_READ, Ops.NOC_WRITE, Ops.NOC_MCAST, Ops.NOC_GATHER, Ops.NOC_ALLGATHER})
  Effect = frozenset({Ops.STORE, Ops.NOC_WRITE, Ops.BARRIER, Ops.END})


# ---- typed UOp.arg specs (all frozen & hashable; UOp dependencies always live in UOp.src) ----

@dataclass(frozen=True)
class KernelArg:
  """SINK arg of a kernel: it runs on the first `cores` workers, numbered column-major (hw.WORKER_ROWS per column)."""
  name: str
  cores: int


@dataclass(frozen=True)
class BufferArg:
  name: str
  space: Space
  shape: tuple[int, ...]
  dtype: DType
  addr: int | None = None
  tiles_per_page: int = 1


@dataclass(frozen=True)
class AllocArg:
  name: str
  space: Space
  shape: tuple[int, ...]
  dtype: DType


@dataclass(frozen=True)
class RangeArg:
  axis: int
  name: str = ""


@dataclass(frozen=True)
class ReduceArg:
  op: Ops
  space: Space


@dataclass(frozen=True)
class CarryArg:
  index: int
  space: Space
  name: str = ""


@dataclass(frozen=True)
class BarrierArg:
  scope: str | tuple[tuple[int, int], tuple[int, int]] = "all"
  tag: int = 0


@dataclass(frozen=True)
class NocHint:
  depth: int = 2
  stages: int = 1
  cap: int = 0
  port: int | None = None


@dataclass(frozen=True)
class NocArg:
  tiles: int = 1
  nbytes: int | None = None
  hint: NocHint = NocHint()


@dataclass(frozen=True)
class McastArg:
  rect: str | tuple[tuple[int, int], tuple[int, int]]
  include_self: bool = True
  hint: NocHint = NocHint()


@dataclass(frozen=True)
class CollectiveArg:
  group: str | tuple[int, ...]
  count: int = 1
  hint: NocHint = NocHint()


@dataclass(frozen=True)
class UnpackArg:
  dest: Space
  shape: tuple[int, int] = (32, 32)
  transpose: bool = False
  allow_tf32: bool = False


@dataclass(frozen=True)
class MvmulArg:
  tile: tuple[int, int, int] = (32, 32, 32)
  fidelity: Fidelity = Fidelity.HIFI2


@dataclass(frozen=True)
class PackArg:
  shape: tuple[int, int] = (32, 32)
  l1_acc: bool = False


@dataclass(frozen=True)
class ReplayArg:
  insns: tuple[int, ...]
  dest: Space = Space.DST
  name: str = ""


@dataclass(frozen=True)
class MopArg:
  cfg: tuple[int, ...]
  dest: Space = Space.DST
  name: str = ""


# ---- hash-consed UOp ----

def _arg_key(arg: Any) -> Any:
  # Distinguish bool/int/float and preserve -0.0 / NaN bit patterns in the hash-cons table.
  t = type(arg)
  if t is float: return (float, struct.pack("<d", arg))
  return (t, arg)


class _UOpMeta(type):
  _pool: weakref.WeakValueDictionary[tuple, UOp] = weakref.WeakValueDictionary()

  def __call__(cls, op: Ops, dtype: DType = dtypes.void, src: tuple[UOp, ...] = (), arg: Any = None) -> UOp:
    if not isinstance(src, tuple): src = tuple(src)
    key = (op, dtype, src, _arg_key(arg))
    if (hit := cls._pool.get(key)) is not None: return hit
    obj = super().__call__(op, dtype, src, arg)
    cls._pool[key] = obj
    return obj


_VOID_OPS = frozenset({Ops.SINK, Ops.END, Ops.LOOP, Ops.STORE, Ops.NOC_WRITE, Ops.BARRIER})
_SCALAR_OPS = frozenset({Ops.CONST, Ops.SPECIAL, Ops.RANGE})
_L1_OPS = frozenset({Ops.NOC_READ, Ops.NOC_MCAST, Ops.NOC_GATHER, Ops.NOC_ALLGATHER, Ops.PACK})
_DST_OPS = frozenset({Ops.MVMUL, Ops.LANE_ID, Ops.REDUCE_ROW, Ops.ARGMAX})
_SRC_BANKS = frozenset({Space.SRCA, Space.SRCB})
_TENSIX_VAL_SPACES = frozenset({Space.DST, Space.SRCA, Space.SRCB})


def _infer_space(op: Ops, src: tuple[UOp, ...], arg: Any) -> Space:
  if op in _VOID_OPS: return Space.NONE
  if op in _SCALAR_OPS: return Space.SCALAR
  if op in _L1_OPS: return Space.L1
  if op in _DST_OPS: return Space.DST
  if op in (Ops.BUFFER, Ops.ALLOC, Ops.CARRY): return arg.space
  if op in (Ops.UNPACK, Ops.REPLAY, Ops.MOP): return arg.dest
  if op is Ops.REDUCE: return arg.space
  if op is Ops.GET: return src[0].src[1 + 2 * arg].space
  if op is Ops.REDUCE_LANES: return src[0].space
  if op is Ops.AFTER: return src[0].space
  if op is Ops.IF: return src[1].space if len(src) >= 2 else Space.NONE
  if op is Ops.LOAD:
    s = src[0].space
    return Space.SCALAR if s in (Space.DRAM, Space.HOST, Space.SCALAR) else s
  if op is Ops.SFPU:
    if (sp := getattr(arg, "space", None)) is not None: return sp
    if any(s.space in _TENSIX_VAL_SPACES for s in src): return Space.DST
    if any(s.space is Space.LREG for s in src): return Space.LREG
    return Space.DST
  if op in GroupOp.ALU or op in (Ops.CAST, Ops.BITCAST):
    if any(s.space in _TENSIX_VAL_SPACES for s in src): return Space.DST
    if any(s.space is Space.LREG for s in src): return Space.LREG
    return Space.SCALAR
  raise ValueError(f"cannot infer space for {op}")


class UOp(metaclass=_UOpMeta):
  """Immutable, hash-consed SSA graph node. Structurally equal nodes are identical objects."""
  __slots__ = ("op", "dtype", "src", "arg", "space", "_src_ops", "__weakref__")

  def __init__(self, op: Ops, dtype: DType = dtypes.void, src: tuple[UOp, ...] = (), arg: Any = None):
    object.__setattr__(self, "op", op)
    object.__setattr__(self, "dtype", dtype)
    object.__setattr__(self, "src", src)
    object.__setattr__(self, "arg", arg)
    object.__setattr__(self, "space", _infer_space(op, src, arg))
    object.__setattr__(self, "_src_ops", None)

  def __setattr__(self, name: str, value: Any):
    raise AttributeError("UOp is immutable")

  def __reduce__(self): return UOp, (self.op, self.dtype, self.src, self.arg)

  def replace(self, **kwargs) -> UOp:
    op = kwargs.pop("op", self.op)
    dtype = kwargs.pop("dtype", self.dtype)
    src = kwargs.pop("src", self.src)
    arg = kwargs.pop("arg", self.arg)
    if kwargs: raise TypeError(f"unexpected replace kwargs: {list(kwargs)}")
    if not isinstance(src, tuple): src = tuple(src)
    return self if (op is self.op and dtype == self.dtype and src == self.src and _arg_key(arg) == _arg_key(self.arg)) else UOp(op, dtype, src, arg)

  def toposort(self, gate: Callable[[UOp], bool] | None = None) -> list[UOp]:
    """Post-order traversal (sources before users). gate(u) == False skips u and its subtree."""
    order: list[UOp] = []
    seen: set[UOp] = set()
    stack: list[tuple[UOp, bool]] = [(self, False)]
    while stack:
      node, expanded = stack.pop()
      if node in seen: continue
      if expanded:
        seen.add(node)
        order.append(node)
      elif gate is None or gate(node):
        stack.append((node, True))
        for s in reversed(node.src):
          if s not in seen: stack.append((s, False))
    return order

  def substitute(self, mapping: dict[UOp, UOp]) -> UOp:
    if not mapping: return self
    return substitute(self, mapping)

  # ---- construction helpers ----

  @staticmethod
  def const(dtype: DType, val: Any) -> UOp:
    if dtype is dtypes.bool: val = bool(val)
    elif dtype.is_float: val = float(val)
    elif dtype.is_int: val = int(val)
    return UOp(Ops.CONST, dtype, (), val)

  @staticmethod
  def sink(*srcs: UOp, arg: Any = None) -> UOp: return UOp(Ops.SINK, dtypes.void, srcs, arg)

  def after(self, *deps: UOp) -> UOp: return UOp(Ops.AFTER, self.dtype, (self, *deps)) if deps else self
  def cast(self, dtype: DType) -> UOp: return self if self.dtype == dtype else UOp(Ops.CAST, dtype, (self,))
  def bitcast(self, dtype: DType) -> UOp: return self if self.dtype == dtype else UOp(Ops.BITCAST, dtype, (self,))

  def _coerce(self, other: Any) -> UOp:
    if isinstance(other, UOp):
      if other.dtype != self.dtype:
        # FPU SrcA/SrcB banks have independent formats (e.g. bf16 * bfp8) -> promote to wider float.
        if self.space in _SRC_BANKS and other.space in _SRC_BANKS and self.dtype.is_float and other.dtype.is_float:
          return other
        raise TypeError(f"dtype mismatch: {self.dtype} vs {other.dtype} (use explicit .cast())")
      return other
    if isinstance(other, (bool, int, float)): return UOp.const(self.dtype, other)
    raise TypeError(f"cannot coerce {type(other).__name__} to UOp")

  def alu(self, op: Ops, *rest: UOp) -> UOp:
    if op in GroupOp.Comparison:
      return UOp(op, dtypes.bool, (self, *rest))
    if op is Ops.WHERE:
      if self.dtype is not dtypes.bool: raise TypeError(f"WHERE condition must be bool, got {self.dtype}")
      a, b = rest
      if a.dtype != b.dtype: raise TypeError(f"WHERE branch dtype mismatch: {a.dtype} vs {b.dtype}")
      return UOp(op, a.dtype, (self, a, b))
    srcs = (self, *rest)
    arg, out_dt = None, self.dtype
    if any(s.space in _SRC_BANKS for s in srcs):
      # Auto-populate FPU math fidelity from operand dtypes when operating on SrcA/SrcB.
      if len(srcs) == 2:
        arg = default_fidelity(srcs[0].dtype, srcs[1].dtype)
        out_dt = max((srcs[0].dtype, srcs[1].dtype), key=lambda d: d.bits)
      else:
        arg = Fidelity.LOFI
    return UOp(op, out_dt, srcs, arg)

  @property
  def is_fpu(self) -> bool:
    """True if this UOp executes on the Matrix Unit (FPU): MVMUL or any op reading SrcA/SrcB."""
    return self.op is Ops.MVMUL or any(s.space in _SRC_BANKS for s in self.src)

  @property
  def fidelity(self) -> Fidelity | None:
    if self.op is Ops.MVMUL: return self.arg.fidelity
    if isinstance(self.arg, Fidelity): return self.arg
    return None

  def with_fidelity(self, fidelity: Fidelity | int) -> UOp:
    """Override FPU fidelity (LoFi/HiFi2/HiFi3/HiFi4) on an FPU UOp."""
    f = Fidelity(fidelity)
    if not self.is_fpu: raise ValueError(f"with_fidelity() only applies to FPU ops, got {self.op.name} ({self.space})")
    if self.op is Ops.MVMUL:
      from dataclasses import replace
      return self.replace(arg=replace(self.arg, fidelity=f))
    return self.replace(arg=f)

  # ---- Python operators (NOTE: == and != stay identity for hash-consing!) ----

  def __add__(self, x):  return self.alu(Ops.ADD, self._coerce(x))
  def __radd__(self, x): return self._coerce(x).alu(Ops.ADD, self)
  def __sub__(self, x):  return self.alu(Ops.SUB, self._coerce(x))
  def __rsub__(self, x): return self._coerce(x).alu(Ops.SUB, self)
  def __mul__(self, x):  return self.alu(Ops.MUL, self._coerce(x))
  def __rmul__(self, x): return self._coerce(x).alu(Ops.MUL, self)
  def __truediv__(self, x):
    if not self.dtype.is_float: raise TypeError("use // for integer division")
    return self.alu(Ops.DIV, self._coerce(x))
  def __rtruediv__(self, x): return self._coerce(x).__truediv__(self)
  def __floordiv__(self, x):
    if not self.dtype.is_int: raise TypeError("use / for float division")
    return self.alu(Ops.DIV, self._coerce(x))
  def __rfloordiv__(self, x): return self._coerce(x).__floordiv__(self)
  def __mod__(self, x):  return self.alu(Ops.MOD, self._coerce(x))
  def __rmod__(self, x): return self._coerce(x).alu(Ops.MOD, self)
  def __neg__(self):     return self.alu(Ops.NEG)
  def __abs__(self):     return self.alu(Ops.ABS)
  def __invert__(self):  return self.alu(Ops.NOT)
  def __and__(self, x):  return self.alu(Ops.AND, self._coerce(x))
  def __rand__(self, x): return self._coerce(x).alu(Ops.AND, self)
  def __or__(self, x):   return self.alu(Ops.OR, self._coerce(x))
  def __ror__(self, x):  return self._coerce(x).alu(Ops.OR, self)
  def __xor__(self, x):  return self.alu(Ops.XOR, self._coerce(x))
  def __rxor__(self, x): return self._coerce(x).alu(Ops.XOR, self)
  def __lshift__(self, x): return self.alu(Ops.SHL, self._coerce(x))
  def __rshift__(self, x): return self.alu(Ops.SHR, self._coerce(x))

  def __lt__(self, x): return self.alu(Ops.CMPLT, self._coerce(x))
  def __gt__(self, x): return self._coerce(x).alu(Ops.CMPLT, self)
  def __le__(self, x): return ~self._coerce(x).alu(Ops.CMPLT, self)
  def __ge__(self, x): return ~self.alu(Ops.CMPLT, self._coerce(x))
  def eq(self, x) -> UOp: return self.alu(Ops.CMPEQ, self._coerce(x))
  def ne(self, x) -> UOp: return self.alu(Ops.CMPNE, self._coerce(x))

  # ---- math & SFPU conveniences ----

  def maximum(self, x) -> UOp: return self.alu(Ops.MAX, self._coerce(x))
  def minimum(self, x) -> UOp: return self.alu(Ops.MIN, self._coerce(x))
  def exp2(self) -> UOp:  return self.alu(Ops.EXP2)
  def log2(self) -> UOp:  return self.alu(Ops.LOG2)
  def sin(self) -> UOp:   return self.alu(Ops.SIN)
  def sqrt(self) -> UOp:  return self.alu(Ops.SQRT)
  def rsqrt(self) -> UOp: return self.alu(Ops.RSQRT)
  def recip(self) -> UOp: return self.alu(Ops.RECIP)
  def exp(self) -> UOp:   return (self * (1.0 / math.log(2.0))).exp2()
  def log(self) -> UOp:   return self.log2() * math.log(2.0)
  def relu(self) -> UOp:  return self.maximum(0.0)
  def sigmoid(self) -> UOp: return (1.0 + (-self).exp()).recip()
  def silu(self) -> UOp:  return self * self.sigmoid()
  def tanh(self) -> UOp:
    e = (self * 2.0).exp()
    return (e - 1.0) * (e + 1.0).recip()
  def gelu(self) -> UOp:
    # Hendrycks tanh approximation: 0.5 * x * (1 + tanh(sqrt(2/pi) * (x + 0.044715 * x^3)))
    c = math.sqrt(2.0 / math.pi)
    return 0.5 * self * (1.0 + (c * (self + 0.044715 * self * self * self)).tanh())

  def where(self, a, b) -> UOp:
    if isinstance(a, UOp) and not isinstance(b, UOp): b = a._coerce(b)
    elif isinstance(b, UOp) and not isinstance(a, UOp): a = b._coerce(a)
    if not (isinstance(a, UOp) and isinstance(b, UOp)):
      raise TypeError("at least one branch of where() must be a UOp")
    return self.alu(Ops.WHERE, a, b)

  def reduce_row(self, op: Ops = Ops.ADD) -> UOp:
    if op not in (Ops.ADD, Ops.MAX): raise ValueError(f"reduce_row supports ADD or MAX, got {op}")
    return UOp(Ops.REDUCE_ROW, self.dtype, (self,), op)

  def reduce_lanes(self, op: Ops = Ops.ADD, scope: str = "all") -> UOp:
    if op not in (Ops.ADD, Ops.MAX, Ops.MIN): raise ValueError(f"reduce_lanes supports ADD/MAX/MIN, got {op}")
    if scope not in ("all", "row8"): raise ValueError(f"reduce_lanes scope must be 'all' or 'row8', got {scope!r}")
    return UOp(Ops.REDUCE_LANES, self.dtype, (self,), (op, scope))

  def argmax(self) -> UOp:
    return UOp(Ops.ARGMAX, dtypes.i32, (self,))

  # ---- builders: kernels are built bottom-up from SPECIAL / RANGE / BUFFER leaves and wrapped in a SINK last ----

  @staticmethod
  def _i32(x: UOp | int) -> UOp: return x if isinstance(x, UOp) else UOp.const(dtypes.i32, int(x))

  @staticmethod
  def special(end: UOp | int, name: str) -> UOp:
    """Hardware coordinate with a known bound: core_id, core_x (column) or core_y (row, < hw.WORKER_ROWS)."""
    return UOp(Ops.SPECIAL, dtypes.i32, (UOp._i32(end),), name)

  @staticmethod
  def range(end: UOp | int, axis: int, name: str = "") -> UOp:
    return UOp(Ops.RANGE, dtypes.i32, (UOp._i32(end),), RangeArg(axis, name))

  @staticmethod
  def buffer(name: str, shape: tuple[int, ...] | int, dtype: DType | str, space: Space = Space.DRAM,
             addr: int | None = None, tiles_per_page: int = 1) -> UOp:
    if space not in (Space.DRAM, Space.HOST, Space.L1, Space.SCALAR): raise ValueError(f"invalid buffer space {space}")
    dt = dtypes.from_name(dtype)
    return UOp(Ops.BUFFER, dt, (), BufferArg(name, space, (shape,) if isinstance(shape, int) else tuple(shape), dt, addr, tiles_per_page))

  @staticmethod
  def alloc(name: str, space: Space, dtype: DType | str, shape: tuple[int, ...] | int = (32, 32)) -> UOp:
    if space not in (Space.DST, Space.LREG, Space.L1, Space.SCALAR):
      raise ValueError(f"alloc space must be DST, LREG, L1, or SCALAR, got {space}")
    dt = dtypes.from_name(dtype)
    return UOp(Ops.ALLOC, dt, (), AllocArg(name, space, (shape,) if isinstance(shape, int) else tuple(shape), dt))

  @staticmethod
  def barrier(scope: str | tuple[tuple[int, int], tuple[int, int]] = "all", tag: int = 0) -> UOp:
    return UOp(Ops.BARRIER, dtypes.void, (), BarrierArg(scope, tag))

  @staticmethod
  def lane_id(dtype: DType | str = dtypes.i32) -> UOp: return UOp(Ops.LANE_ID, dtypes.from_name(dtype), ())

  @staticmethod
  def replay(insns: Sequence[int], *deps: UOp, dtype: DType | str = dtypes.fp32, dest: Space = Space.DST, name: str = "") -> UOp:
    """Explicit Tensix REPLAY block carrying ordered raw instruction words in arg and live dataflow edges in src."""
    return UOp(Ops.REPLAY, dtypes.from_name(dtype), deps, ReplayArg(tuple(int(w) for w in insns), dest, name))

  @staticmethod
  def mop(cfg: Sequence[int], *deps: UOp, dtype: DType | str = dtypes.fp32, dest: Space = Space.DST, name: str = "") -> UOp:
    """Explicit Tensix MOP config (9 words) carrying live dataflow edges in src."""
    return UOp(Ops.MOP, dtypes.from_name(dtype), deps, MopArg(tuple(int(w) for w in cfg), dest, name))

  def end(self, *ranges: UOp) -> UOp:
    if not ranges: raise ValueError("end() requires at least one RANGE")
    return UOp(Ops.END, dtypes.void, (self, *ranges))

  def if_(self, body: UOp, else_body: UOp | None = None) -> UOp:
    if self.dtype is not dtypes.bool: raise TypeError(f"if condition must be bool, got {self.dtype}")
    if else_body is None: return UOp(Ops.IF, body.dtype, (self, body))
    if body.dtype != else_body.dtype: raise TypeError(f"if/else dtype mismatch: {body.dtype} vs {else_body.dtype}")
    return UOp(Ops.IF, body.dtype, (self, body, else_body))

  def reduce(self, *ranges: UOp, op: Ops = Ops.ADD, space: Space | None = None) -> UOp:
    if not ranges: raise ValueError("reduce() requires at least one RANGE")
    if op not in (Ops.ADD, Ops.MUL, Ops.MAX, Ops.MIN): raise ValueError(f"unsupported reduce op {op}")
    sp = self.space if space is None else space
    if sp not in (Space.DST, Space.LREG, Space.L1, Space.SCALAR):
      raise ValueError(f"reduce residency must be DST, LREG, L1, or SCALAR, got {sp}")
    return UOp(Ops.REDUCE, self.dtype, (self, *ranges), ReduceArg(op, sp))

  def carry(self, rng: UOp, index: int = 0, *, space: Space | None = None, name: str = "") -> UOp:
    """Loop-carried state placeholder (SSA iter_arg) for `rng`, initialized by self before the loop."""
    if rng.op is not Ops.RANGE: raise TypeError(f"carry() requires a RANGE, got {rng.op.name}")
    sp = self.space if space is None else space
    if sp not in (Space.DST, Space.LREG, Space.L1, Space.SCALAR):
      raise ValueError(f"carry residency must be DST, LREG, L1, or SCALAR, got {sp}")
    return UOp(Ops.CARRY, self.dtype, (self, rng), CarryArg(index, sp, name))

  def loop(self, inits: Sequence[UOp], body, *, spaces: Sequence[Space | None] | None = None,
           names: Sequence[str] | None = None) -> tuple[UOp, ...]:
    """Loop over this RANGE with explicit carried values; body(*carries) yields their next values.
    Returns the final post-loop values (Ops.GET), one per carried state."""
    if self.op is not Ops.RANGE: raise TypeError(f"loop() requires a RANGE, got {self.op.name}")
    if not inits: raise ValueError("loop() requires at least one initial carried value")
    sps = [None] * len(inits) if spaces is None else list(spaces)
    nms = [""] * len(inits) if names is None else list(names)
    if len(sps) != len(inits) or len(nms) != len(inits): raise ValueError("loop() spaces/names length must match inits")
    carries = tuple(init.carry(self, i, space=sp, name=nm) for i, (init, sp, nm) in enumerate(zip(inits, sps, nms)))
    res = body(*carries)
    next_vals = (res,) if isinstance(res, UOp) else tuple(res)
    if len(next_vals) != len(carries): raise ValueError(f"loop() body yielded {len(next_vals)} values, expected {len(carries)}")
    lp = UOp(Ops.LOOP, dtypes.void, (self, *(x for pair in zip(carries, next_vals) for x in pair)))
    return tuple(UOp(Ops.GET, c.dtype, (lp,), i) for i, c in enumerate(carries))

  def load(self, offset: UOp | int | None = None, *, gate: UOp | None = None) -> UOp:
    if gate is not None: return UOp(Ops.LOAD, self.dtype, (self, UOp._i32(0 if offset is None else offset), gate))
    return UOp(Ops.LOAD, self.dtype, (self,) if offset is None else (self, UOp._i32(offset)))

  def store(self, val: UOp, offset: UOp | int | None = None, *, gate: UOp | None = None) -> UOp:
    if gate is not None: return UOp(Ops.STORE, dtypes.void, (self, UOp._i32(0 if offset is None else offset), val, gate))
    return UOp(Ops.STORE, dtypes.void, (self, val) if offset is None else (self, UOp._i32(offset), val))

  def noc_read(self, offset: UOp | int, tiles: int = 1, nbytes: int | None = None, *, gate: UOp | None = None,
               depth: int = 2, stages: int = 1, cap: int = 0, port: int | None = None) -> UOp:
    src = (self, UOp._i32(offset)) if gate is None else (self, UOp._i32(offset), gate)
    return UOp(Ops.NOC_READ, self.dtype, src, NocArg(tiles, nbytes, NocHint(depth, stages, cap, port)))

  def noc_write(self, offset: UOp | int, val: UOp, tiles: int = 1, nbytes: int | None = None, *, gate: UOp | None = None,
                depth: int = 2, stages: int = 1, cap: int = 0, port: int | None = None) -> UOp:
    src = (self, UOp._i32(offset), val) if gate is None else (self, UOp._i32(offset), val, gate)
    return UOp(Ops.NOC_WRITE, dtypes.void, src, NocArg(tiles, nbytes, NocHint(depth, stages, cap, port)))

  def noc_mcast(self, rect: str | tuple[tuple[int, int], tuple[int, int]], sender: UOp | int, include_self: bool = True, *,
                depth: int = 2, stages: int = 1, cap: int = 0, port: int | None = None) -> UOp:
    return UOp(Ops.NOC_MCAST, self.dtype, (self, UOp._i32(sender)), McastArg(rect, include_self, NocHint(depth, stages, cap, port)))

  def noc_gather(self, group: str | tuple[int, ...], root: UOp | int, count: int = 1, *,
                 depth: int = 2, stages: int = 1, cap: int = 0, port: int | None = None) -> UOp:
    return UOp(Ops.NOC_GATHER, self.dtype, (self, UOp._i32(root)), CollectiveArg(group, count, NocHint(depth, stages, cap, port)))

  def noc_allgather(self, group: str | tuple[int, ...], count: int = 1, *,
                    depth: int = 2, stages: int = 1, cap: int = 0, port: int | None = None) -> UOp:
    return UOp(Ops.NOC_ALLGATHER, self.dtype, (self,), CollectiveArg(group, count, NocHint(depth, stages, cap, port)))

  def unpack(self, dest: Space = Space.DST, dtype: DType | str | None = None, shape: tuple[int, int] = (32, 32),
             transpose: bool = False, allow_tf32: bool = False) -> UOp:
    if dest not in (Space.SRCA, Space.SRCB, Space.DST): raise ValueError(f"unpack dest must be SRCA, SRCB, or DST, got {dest}")
    dt = (dtypes.fp32 if dest is Space.DST else self.dtype) if dtype is None else dtypes.from_name(dtype)
    return UOp(Ops.UNPACK, dt, (self,), UnpackArg(dest, shape, transpose, allow_tf32))

  def mvmul(self, srca: UOp, tile: tuple[int, int, int] = (32, 32, 32), fidelity: Fidelity | int | None = None,
            dtype: DType | str = dtypes.fp32) -> UOp:
    """FPU matmul with self as SrcB. Elementwise FPU ops use +, -, *, maximum on SRCA/SRCB values directly."""
    f = default_fidelity(self.dtype, srca.dtype) if fidelity is None else Fidelity(fidelity)
    return UOp(Ops.MVMUL, dtypes.from_name(dtype), (self, srca), MvmulArg(tile, f))

  def pack(self, dtype: DType | str = dtypes.bf16, shape: tuple[int, int] = (32, 32), l1_acc: bool = False) -> UOp:
    return UOp(Ops.PACK, dtypes.from_name(dtype), (self,), PackArg(shape, l1_acc))

  def __repr__(self) -> str: return pretty(self)


def pretty(root: UOp, limit: int = 200) -> str:
  nodes = root.toposort()
  idx = {u: i for i, u in enumerate(nodes)}
  lines = [
    f"{i:3d} {u.op.name:<13s} {u.space.name:<6s} {u.dtype.name:<5s} {[idx[s] for s in u.src]!s:<14s} {u.arg!r}"
    for i, u in enumerate(nodes)
  ]
  return "\n".join(lines if len(lines) <= limit else lines[:limit] + [f"... ({len(lines) - limit} more)"])


# ---- pattern matching ----

def _as_tuple(x, cls) -> tuple | None:
  if x is None: return None
  return (x,) if isinstance(x, cls) else tuple(x)


class UPat:
  __slots__ = ("op", "dtype", "space", "arg", "name", "src_mode", "src", "allow_any_len", "is_any", "req_ops")

  def __init__(
    self,
    op: Ops | Sequence[Ops] | set[Ops] | frozenset[Ops] | None = None,
    dtype: DType | Sequence[DType] | None = None,
    src: tuple[UPat, ...] | list[UPat] | UPat | None = None,
    arg: Any = None,
    name: str | None = None,
    space: Space | Sequence[Space] | None = None,
    allow_any_len: bool = False,
    is_any: bool = False,
  ):
    if name == "ctx": raise ValueError("UPat cannot be named 'ctx'")
    self.op = _as_tuple(op, Ops)
    self.dtype = _as_tuple(dtype, DType)
    self.space = _as_tuple(space, Space)
    self.arg, self.name, self.allow_any_len, self.is_any = arg, name, allow_any_len, is_any

    if is_any:
      self.src_mode, self.src = "any", tuple(src or ())
      self.req_ops: frozenset[Ops] = frozenset()
    elif src is None:
      self.src_mode, self.src = "none", ()
      self.req_ops = frozenset()
    elif isinstance(src, UPat):
      self.src_mode, self.src = "repeat", (src,)
      self.req_ops = frozenset()
    elif isinstance(src, list):
      self.src_mode, self.src = "perm", tuple(src)
      self.req_ops = frozenset(p.op[0] for p in src if p.op is not None and len(p.op) == 1)
    elif isinstance(src, tuple):
      self.src_mode, self.src = "exact", src
      self.req_ops = frozenset(p.op[0] for p in src if p.op is not None and len(p.op) == 1)
    else:
      raise TypeError(f"invalid UPat src: {type(src).__name__}")

  @staticmethod
  def any(*pats: UPat) -> UPat: return UPat(src=pats, is_any=True)
  @staticmethod
  def var(name: str | None = None, dtype=None, space=None) -> UPat: return UPat(dtype=dtype, space=space, name=name)
  @staticmethod
  def const(name: str | None = None, dtype=None, arg=None) -> UPat: return UPat(Ops.CONST, dtype=dtype, arg=arg, name=name)

  def named(self, name: str) -> UPat:
    if name == "ctx": raise ValueError("UPat cannot be named 'ctx'")
    out = UPat.__new__(UPat)
    for slot in UPat.__slots__: setattr(out, slot, getattr(self, slot))
    out.name = name
    return out

  def __add__(self, x: UPat) -> UPat: return UPat(Ops.ADD, src=[self, x])
  def __sub__(self, x: UPat) -> UPat: return UPat(Ops.SUB, src=(self, x))
  def __mul__(self, x: UPat) -> UPat: return UPat(Ops.MUL, src=[self, x])
  def __neg__(self) -> UPat:          return UPat(Ops.NEG, src=(self,))

  def match(self, u: UOp, binds: dict[str, UOp]) -> list[dict[str, UOp]]:
    if self.name is not None:
      prev = binds.get(self.name)
      if prev is not None and prev is not u: return []
      binds[self.name] = u
    if self.is_any:
      out: list[dict[str, UOp]] = []
      for alt in self.src: out.extend(alt.match(u, binds.copy()))
      return out
    if self.op is not None and u.op not in self.op: return []
    if self.dtype is not None and u.dtype not in self.dtype: return []
    if self.space is not None and u.space not in self.space: return []
    if self.arg is not None:
      if callable(self.arg):
        if not self.arg(u.arg): return []
      elif _arg_key(self.arg) != _arg_key(u.arg):
        return []

    if self.src_mode == "none": return [binds]
    if self.src_mode == "repeat":
      pat = self.src[0]
      states = [binds]
      for s in u.src:
        states = [m for st in states for m in pat.match(s, st.copy())]
        if not states: return []
      return states

    need = len(self.src)
    if len(u.src) < need or (not self.allow_any_len and len(u.src) != need): return []
    candidates = itertools.permutations(self.src) if self.src_mode == "perm" else (self.src,)
    results: list[dict[str, UOp]] = []
    for pat_tuple in candidates:
      states = [binds.copy()]
      for su, sp in zip(u.src, pat_tuple):
        states = [m for st in states for m in sp.match(su, st)]
        if not states: break
      results.extend(states)
    return results


class PatternMatcher:
  def __init__(self, rules: Sequence[tuple[UPat, Callable]]):
    self.rules = list(rules)
    self._by_op: dict[Ops | None, list[tuple[Callable, frozenset[Ops]]]] = collections.defaultdict(list)
    for pat, fn in self.rules:
      has_ctx = "ctx" in inspect.signature(fn).parameters
      runner = self._wrap(pat, fn, has_ctx)
      if pat.op is None:
        self._by_op[None].append((runner, pat.req_ops))
      else:
        for op in pat.op: self._by_op[op].append((runner, pat.req_ops))

  @staticmethod
  def _wrap(pat: UPat, fn: Callable, has_ctx: bool) -> Callable:
    if has_ctx:
      def run(u: UOp, ctx: Any) -> UOp | None:
        for binds in pat.match(u, {}):
          if (res := fn(ctx=ctx, **binds)) is not None: return res
        return None
    else:
      def run(u: UOp, _ctx: Any) -> UOp | None:
        for binds in pat.match(u, {}):
          if (res := fn(**binds)) is not None: return res
        return None
    return run

  def __add__(self, other: PatternMatcher) -> PatternMatcher:
    return PatternMatcher(self.rules + other.rules)

  def rewrite(self, u: UOp, ctx: Any = None) -> UOp | None:
    buckets = (self._by_op.get(u.op), self._by_op.get(None))
    if not buckets[0] and not buckets[1]: return None
    src_ops = u._src_ops
    if src_ops is None:
      src_ops = frozenset(s.op for s in u.src)
      object.__setattr__(u, "_src_ops", src_ops)
    for bucket in buckets:
      if not bucket: continue
      for run, req in bucket:
        if req and not req <= src_ops: continue
        if (res := run(u, ctx)) is not None and res is not u: return res
    return None


# ---- iterative graph rewriter ----

def graph_rewrite(
  root: UOp,
  pm: PatternMatcher,
  ctx: Any = None,
  bottom_up: bool = False,
  bpm: PatternMatcher | None = None,
  limit: int = 250_000,
) -> UOp:
  """Rewrite every reachable UOp under root to a fixed point.
  By default runs top-down (children rewritten before parent). Pass bottom_up=True to rewrite parent before children,
  or provide bpm alongside pm for a combined single-pass rewrite."""
  top_pm = None if bottom_up else pm
  bot_pm = pm if bottom_up else bpm

  memo: dict[UOp, UOp] = {}
  bot_cache: dict[UOp, UOp | None] = {}
  started: set[UOp] = {root}
  waiting: dict[UOp, list[tuple[UOp, int, UOp]]] = collections.defaultdict(list)
  stack: list[tuple[UOp, int, UOp]] = [(root, 0, root)]
  steps = 0

  def finish(orig: UOp, result: UOp):
    memo[orig] = result
    if orig in waiting: stack.extend(waiting.pop(orig))

  while stack:
    steps += 1
    if steps > limit: raise RuntimeError("graph_rewrite exceeded step limit (possible rewrite loop)")
    orig, phase, cur = stack.pop()
    if orig in memo: continue

    if phase == 0:
      if bot_pm is not None:
        seen: set[UOp] = set()
        nxt: UOp | None = cur
        while nxt is not None:
          if nxt in seen: raise RuntimeError(f"bottom-up rewrite cycle at {nxt.op}")
          seen.add(nxt)
          cur = nxt
          if cur in bot_cache: nxt = bot_cache[cur]
          else: nxt = bot_cache[cur] = bot_pm.rewrite(cur, ctx)
      if cur is not orig:
        stack.append((orig, 2, cur))
        if cur not in memo and cur not in started:
          started.add(cur)
          stack.append((cur, 0, cur))
        continue
      stack.append((orig, 1, cur))
      for s in reversed(cur.src):
        if s not in memo and s not in started:
          started.add(s)
          stack.append((s, 0, s))

    elif phase == 1:
      new_src: list[UOp] = []
      blocked: UOp | None = None
      for s in cur.src:
        if (rs := memo.get(s)) is None:
          blocked = s
          break
        new_src.append(rs)
      if blocked is not None:
        waiting[blocked].append((orig, 1, cur))
        continue

      new_src_t = tuple(new_src)
      if new_src_t != cur.src:
        nxt = UOp(cur.op, cur.dtype, new_src_t, cur.arg)
      else:
        nxt = top_pm.rewrite(cur, ctx) if top_pm is not None else None
        if nxt is None or nxt is cur:
          finish(orig, cur)
          continue
      stack.append((orig, 2, nxt))
      if nxt not in memo and nxt not in started:
        started.add(nxt)
        stack.append((nxt, 0, nxt))

    else:  # phase == 2: forward orig -> memo[cur]
      if (res := memo.get(cur)) is not None:
        finish(orig, res)
      else:
        waiting[cur].append((orig, 2, cur))

  if root not in memo:
    raise RuntimeError("graph_rewrite stalled: cyclic dependency between rewritten nodes")
  return memo[root]


def substitute(root: UOp, mapping: dict[UOp, UOp]) -> UOp:
  if not mapping: return root
  if root in mapping: return mapping[root]
  # Fast single-pass bottom-up replacement (does not recurse into substituted subtrees).
  memo: dict[UOp, UOp] = {}
  for u in root.toposort(gate=lambda n: n not in mapping):
    new_src = tuple(mapping.get(s, memo.get(s, s)) for s in u.src)
    memo[u] = u if new_src == u.src else UOp(u.op, u.dtype, new_src, u.arg)
  return memo[root]
