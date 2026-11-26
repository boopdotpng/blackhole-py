import collections, heapq, inspect, itertools, math, struct, weakref
from dataclasses import dataclass
from enum import Enum, auto
from collections.abc import Callable, Sequence
from typing import Any, Union
from .dtype import DType, Fidelity, Space, default_fidelity, dtypes, least_upper_dtype
from .mixin import Mixin, TopkResult

# ---- opcodes ----

class Ops(Enum):
  # graph structure & sync
  SINK = auto()
  AFTER = auto()
  BARRIER = auto()
  NOOP = auto()

  # grid, control & residency
  CONST = auto()
  DEFINE_VAR = auto()
  SPECIAL = auto()
  PARAM = auto()
  BUFFER = auto()
  ALLOC = auto()
  STACK = auto()
  INDEX = auto()
  RANGE = auto()
  END = auto()
  BACKEDGE = auto()
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

  # Tensix engines
  UNPACK = auto()
  MVMUL = auto()
  PACK = auto()
  REPLAY = auto()
  MOP = auto()

  # ALU (scalar RV32 when operands are SCALAR; FPU on SRCA/SRCB; SFPU vector on DST/LREG)
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

  # Layer 0 whole-chip tensor ops (movement, axis reduction, indexing)
  RESHAPE = auto()
  EXPAND = auto()
  PERMUTE = auto()
  PAD = auto()
  SHRINK = auto()
  FLIP = auto()
  REDUCE_AXIS = auto()
  CONTIGUOUS = auto()
  ARANGE = auto()
  TAKE = auto()
  GATHER = auto()
  SCATTER = auto()
  TOPK = auto()

  # Bottom-layer ISA & program representation (tinygrad UOp.ins = CALL(NATIVE, ...))
  NATIVE = auto()
  CALL = auto()
  LINEAR = auto()
  SOURCE = auto()
  BINARY = auto()
  PROGRAM = auto()

class GroupOp:
  Unary = frozenset({Ops.NEG, Ops.ABS, Ops.NOT, Ops.EXP2, Ops.LOG2, Ops.SIN, Ops.SQRT, Ops.RSQRT, Ops.RECIP})
  Binary = frozenset({
    Ops.ADD, Ops.SUB, Ops.MUL, Ops.DIV, Ops.MOD, Ops.MAX, Ops.MIN,
    Ops.CMPLT, Ops.CMPEQ, Ops.CMPNE, Ops.AND, Ops.OR, Ops.XOR, Ops.SHL, Ops.SHR,
  })
  Ternary = frozenset({Ops.WHERE, Ops.MULACC})
  ALU = Unary | Binary | Ternary
  Comparison = frozenset({Ops.CMPLT, Ops.CMPEQ, Ops.CMPNE})
  Movement = frozenset({Ops.RESHAPE, Ops.EXPAND, Ops.PERMUTE, Ops.PAD, Ops.SHRINK, Ops.FLIP})
  TensorOnly = Movement | frozenset({
    Ops.REDUCE_AXIS, Ops.CONTIGUOUS, Ops.ARANGE, Ops.TAKE, Ops.GATHER, Ops.SCATTER, Ops.TOPK,
  })

  # tinygrad-style structural groups
  Defines = frozenset({Ops.PARAM, Ops.BUFFER, Ops.ALLOC})
  Irreducible = frozenset({Ops.CONST, Ops.DEFINE_VAR, Ops.SPECIAL, Ops.RANGE, Ops.PARAM})
  Control = frozenset({Ops.RANGE, Ops.END, Ops.BACKEDGE, Ops.IF, Ops.LOOP, Ops.GET, Ops.CARRY, Ops.BARRIER})
  Program = frozenset({Ops.NATIVE, Ops.CALL, Ops.LINEAR, Ops.SOURCE, Ops.BINARY, Ops.PROGRAM})

  # Blackhole-specific hardware engine groups
  NoC = frozenset({Ops.NOC_READ, Ops.NOC_WRITE, Ops.NOC_MCAST})
  Tensix = frozenset({Ops.UNPACK, Ops.MVMUL, Ops.PACK, Ops.REPLAY, Ops.MOP})
  FPU = frozenset({Ops.ADD, Ops.SUB, Ops.MUL, Ops.MVMUL})
  SFPU = frozenset({
    Ops.SFPU, Ops.LANE_ID, Ops.REDUCE_ROW, Ops.REDUCE_LANES, Ops.ARGMAX,
    Ops.MULACC, Ops.MAX, Ops.MIN, Ops.NEG, Ops.ABS,
    Ops.EXP2, Ops.LOG2, Ops.SIN, Ops.SQRT, Ops.RSQRT, Ops.RECIP, Ops.WHERE,
  })
  Memory = frozenset({Ops.LOAD, Ops.STORE, Ops.INDEX}) | NoC
  Blackhole = NoC | Tensix | frozenset({Ops.SFPU, Ops.LANE_ID, Ops.REDUCE_ROW, Ops.REDUCE_LANES, Ops.ARGMAX})

# ---- typed UOp.arg specs (all frozen & hashable; UOp dependencies always live in UOp.src) ----

# runs on the first `cores` workers, numbered column-major, 10 per column
@dataclass(frozen=True)
class KernelArg:
  name: str
  cores: int

@dataclass(frozen=True)
class ParamArg:
  slot: int
  name: str = ""
  space: Space = Space.REG
  shape: tuple[int, ...] = ()

@dataclass(frozen=True)
class NativeInfo:
  code: Any
  fmt: bool = False

@dataclass(frozen=True)
class CallInfo:
  role: str = ""  # core tag: "brisc" | "ncrisc" | "trisc0" | "trisc1" | "trisc2" | ""

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

@dataclass(frozen=True)
class ArangeArg:
  start: int | float | UOp
  stop: int | float | UOp
  step: int | float | UOp

@dataclass(frozen=True)
class TopkArg:
  k: int
  dim: int
  largest: bool = True
  sorted: bool = True
  indices: bool = False

@dataclass(frozen=True)
class VarArg:
  name: str
  vmin: int
  vmax: int
  val: int | None = None

# ---- symbolic integer (sint = int | UOp) algebra & bounds ----

sint = Union[int, "UOp"]

def _as_linear(x: sint) -> tuple[dict[UOp, int], int] | None:
  """Represent affine integer UOp expressions as ({term: coeff}, const) for exact cancellation."""
  if isinstance(x, int): return {}, x
  if x.op is Ops.CONST and x.dtype.is_int: return {}, int(x.arg)
  if x.op is Ops.DEFINE_VAR: return {x: 1}, 0
  if x.op is Ops.NEG:
    if (a := _as_linear(x.src[0])) is None: return None
    return ({k: -v for k, v in a[0].items()}, -a[1])
  if x.op in (Ops.ADD, Ops.SUB):
    a, b = _as_linear(x.src[0]), _as_linear(x.src[1])
    if a is None or b is None: return None
    sign = 1 if x.op is Ops.ADD else -1
    terms = dict(a[0])
    for k, v in b[0].items():
      nv = terms.get(k, 0) + sign * v
      if nv == 0: terms.pop(k, None)
      else: terms[k] = nv
    return terms, a[1] + sign * b[1]
  if x.op is Ops.MUL:
    a, b = _as_linear(x.src[0]), _as_linear(x.src[1])
    if a is None or b is None: return None
    if not a[0]: return ({k: v * a[1] for k, v in b[0].items() if v * a[1] != 0}, b[1] * a[1])
    if not b[0]: return ({k: v * b[1] for k, v in a[0].items() if v * b[1] != 0}, a[1] * b[1])
  return None

def _from_linear(terms: dict[UOp, int], const: int) -> sint:
  if not terms: return int(const)
  ordered = sorted(terms.items(), key=lambda kv: (kv[0].arg.name if kv[0].op is Ops.DEFINE_VAR else "", id(kv[0])))
  acc: UOp | None = None
  for v, c in ordered:
    piece = v if c == 1 else (-v if c == -1 else v * c)
    acc = piece if acc is None else (acc + piece)
  assert acc is not None
  if const > 0: return acc + const
  if const < 0: return acc - (-const)
  return acc

def simp_sint(x: sint) -> sint:
  if isinstance(x, int): return x
  if x.op is Ops.CONST and x.dtype.is_int: return int(x.arg)
  if (lin := _as_linear(x)) is not None: return _from_linear(*lin)
  return x

def smin(x: sint) -> int:
  if isinstance(x, int): return x
  match x.op:
    case Ops.CONST: return int(x.arg)
    case Ops.DEFINE_VAR: return x.arg.vmin
    case Ops.NEG: return -smax(x.src[0])
    case Ops.ADD: return smin(x.src[0]) + smin(x.src[1])
    case Ops.SUB: return smin(x.src[0]) - smax(x.src[1])
    case Ops.MUL:
      a0, a1, b0, b1 = smin(x.src[0]), smax(x.src[0]), smin(x.src[1]), smax(x.src[1])
      return min(a0 * b0, a0 * b1, a1 * b0, a1 * b1)
    case Ops.DIV if smin(x.src[1]) > 0: return smin(x.src[0]) // smax(x.src[1])
    case Ops.MAX: return max(smin(x.src[0]), smin(x.src[1]))
    case Ops.MIN: return min(smin(x.src[0]), smin(x.src[1]))
    case _: raise ValueError(f"cannot bound symbolic int {x.op}")

def smax(x: sint) -> int:
  if isinstance(x, int): return x
  match x.op:
    case Ops.CONST: return int(x.arg)
    case Ops.DEFINE_VAR: return x.arg.vmax
    case Ops.NEG: return -smin(x.src[0])
    case Ops.ADD: return smax(x.src[0]) + smax(x.src[1])
    case Ops.SUB: return smax(x.src[0]) - smin(x.src[1])
    case Ops.MUL:
      a0, a1, b0, b1 = smin(x.src[0]), smax(x.src[0]), smin(x.src[1]), smax(x.src[1])
      return max(a0 * b0, a0 * b1, a1 * b0, a1 * b1)
    case Ops.DIV if smin(x.src[1]) > 0: return smax(x.src[0]) // smin(x.src[1])
    case Ops.MAX: return max(smax(x.src[0]), smax(x.src[1]))
    case Ops.MIN: return min(smax(x.src[0]), smax(x.src[1]))
    case _: raise ValueError(f"cannot bound symbolic int {x.op}")

def sprod(xs: Sequence[sint]) -> sint:
  c = 1
  sym: list[UOp] = []
  for x in xs:
    sx = simp_sint(x)
    if isinstance(sx, int): c *= sx
    else: sym.append(sx)
  if c == 0 or not sym: return c
  acc: UOp = sym[0]
  for s in sym[1:]: acc = acc * s
  return simp_sint(acc if c == 1 else acc * c)

def sdiv(total: sint, known: sint) -> sint:
  t, k = simp_sint(total), simp_sint(known)
  if isinstance(t, int) and isinstance(k, int):
    if k == 0 or t % k != 0: raise ValueError(f"cannot divide {t} by {k}")
    return t // k
  if isinstance(k, int) and k != 0 and (lin := _as_linear(t)) is not None:
    terms, c = lin
    if c % k == 0 and all(v % k == 0 for v in terms.values()):
      return _from_linear({u: v // k for u, v in terms.items()}, c // k)
  if t == k: return 1
  raise ValueError(f"cannot symbolically divide {t} by {k}")

def sbcast(a: sint, b: sint) -> sint:
  if a == b: return a
  if a == 1: return b
  if b == 1: return a
  raise ValueError(f"cannot broadcast dimensions {a} and {b}")

def _fmt_sint(x: Any) -> str:
  if isinstance(x, UOp):
    if x.op is Ops.DEFINE_VAR:
      return f"{x.arg.name}={x.arg.val}" if x.arg.val is not None else x.arg.name
    if x.op is Ops.CONST: return repr(x.arg)
    if x.op is Ops.ADD: return f"({_fmt_sint(x.src[0])}+{_fmt_sint(x.src[1])})"
    if x.op is Ops.SUB: return f"({_fmt_sint(x.src[0])}-{_fmt_sint(x.src[1])})"
    if x.op is Ops.MUL: return f"({_fmt_sint(x.src[0])}*{_fmt_sint(x.src[1])})"
    if x.op is Ops.NEG: return f"(-{_fmt_sint(x.src[0])})"
    return f"<{x.op.name}>"
  if isinstance(x, tuple): return "(" + ", ".join(_fmt_sint(e) for e in x) + ("," if len(x) == 1 else "") + ")"
  if isinstance(x, ArangeArg): return f"ArangeArg({_fmt_sint(x.start)}, {_fmt_sint(x.stop)}, {_fmt_sint(x.step)})"
  return repr(x)

def _iter_arg_uops(arg: Any):
  if isinstance(arg, UOp):
    yield arg
  elif isinstance(arg, tuple):
    for e in arg: yield from _iter_arg_uops(e)
  elif isinstance(arg, ArangeArg):
    for e in (arg.start, arg.stop, arg.step):
      if isinstance(e, UOp): yield e

def _map_arg_uops(arg: Any, fn: Callable[[UOp], UOp]) -> Any:
  if isinstance(arg, UOp): return simp_sint(fn(arg))
  if isinstance(arg, tuple):
    mapped = tuple(_map_arg_uops(e, fn) for e in arg)
    return arg if mapped == arg else mapped
  if isinstance(arg, ArangeArg):
    st = _map_arg_uops(arg.start, fn) if isinstance(arg.start, UOp) else arg.start
    sp = _map_arg_uops(arg.stop, fn) if isinstance(arg.stop, UOp) else arg.stop
    step = _map_arg_uops(arg.step, fn) if isinstance(arg.step, UOp) else arg.step
    return arg if (st == arg.start and sp == arg.stop and step == arg.step) else ArangeArg(st, sp, step)
  return arg

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

_SRC_BANKS = frozenset({Space.SRCA, Space.SRCB})
_TENSIX_VAL_SPACES = frozenset({Space.DST, Space.SRCA, Space.SRCB})

def _infer_space(op: Ops, src: tuple[UOp, ...], arg: Any) -> Space:
  match op:
    case Ops.SINK | Ops.END | Ops.LOOP | Ops.STORE | Ops.NOC_WRITE | Ops.BARRIER | Ops.NOOP | Ops.LINEAR | Ops.SOURCE | Ops.BINARY | Ops.PROGRAM:
      return Space.NONE
    case Ops.CONST | Ops.DEFINE_VAR | Ops.SPECIAL | Ops.RANGE: return Space.SCALAR
    case Ops.NOC_READ | Ops.NOC_MCAST | Ops.PACK: return Space.L1
    case Ops.MVMUL | Ops.LANE_ID | Ops.REDUCE_ROW: return Space.DST
    case Ops.ARGMAX:
      if arg is not None or (src and (src[0].space is Space.TENSOR or (src[0].op is Ops.BUFFER and src[0].space is not Space.SCALAR))):
        return Space.TENSOR
      return Space.DST
    case _ if op in GroupOp.TensorOnly: return Space.TENSOR
    case Ops.PARAM | Ops.BUFFER | Ops.ALLOC | Ops.CARRY | Ops.REDUCE: return arg.space
    case Ops.UNPACK | Ops.REPLAY | Ops.MOP: return arg.dest
    case Ops.GET: return src[0].src[1 + 2 * arg].space
    case Ops.REDUCE_LANES | Ops.AFTER | Ops.INDEX | Ops.BACKEDGE: return src[0].space
    case Ops.STACK | Ops.NATIVE | Ops.CALL: return src[0].space if src else Space.NONE
    case Ops.IF: return src[1].space if len(src) >= 2 else Space.NONE
    case Ops.LOAD:
      s = src[0].space
      return Space.SCALAR if s in (Space.DRAM, Space.HOST, Space.SCALAR) else s
    case Ops.SFPU if (sp := getattr(arg, "space", None)) is not None: return sp
    case Ops.SFPU | Ops.CAST | Ops.BITCAST: pass
    case _ if op in GroupOp.ALU: pass
    case _: raise ValueError(f"cannot infer space for {op}")
  # Layer 0 tensor ALU / casts stay in Space.TENSOR.
  if op is not Ops.SFPU and any(s.space is Space.TENSOR or (s.op is Ops.BUFFER and s.space is not Space.SCALAR) for s in src):
    return Space.TENSOR
  # SFPU primitives and ALU ops take their operands' space; an SFPU primitive on scalars still runs in Dst.
  if any(s.space in _TENSIX_VAL_SPACES for s in src): return Space.DST
  if any(s.space is Space.LREG for s in src): return Space.LREG
  if any(s.space is Space.REG for s in src): return Space.REG
  return Space.DST if op is Ops.SFPU else Space.SCALAR

def _infer_shape(op: Ops, src: tuple[UOp, ...], arg: Any, space: Space) -> tuple[sint, ...] | None:
  match op:
    case Ops.BUFFER | Ops.ALLOC: return arg.shape
    case Ops.PARAM: return arg.shape if arg.shape else None
    case Ops.CONST | Ops.DEFINE_VAR: return ()
    case Ops.ARANGE:
      if isinstance(arg.start, int) and isinstance(arg.stop, int) and isinstance(arg.step, int):
        n: sint = len(range(arg.start, arg.stop, arg.step))
      elif isinstance(arg.start, UOp) or isinstance(arg.stop, UOp) or isinstance(arg.step, UOp):
        if arg.step != 1: raise ValueError(f"symbolic ARANGE currently requires step=1, got {arg.step}")
        n = simp_sint(arg.stop - arg.start)
      else:
        n = max(0, math.ceil((arg.stop - arg.start) / arg.step))
      return (n,)
    case Ops.RESHAPE:
      s0 = src[0].shape
      if s0 is None: raise ValueError("RESHAPE requires shaped source")
      if sprod(s0) != sprod(arg): raise ValueError(f"cannot reshape {s0} to {arg}")
      return arg
    case Ops.EXPAND:
      s0 = src[0].shape
      if s0 is None or len(s0) != len(arg): raise ValueError(f"EXPAND rank mismatch: {s0} -> {arg}")
      for a, b in zip(s0, arg):
        if a != b and a != 1: raise ValueError(f"cannot expand {s0} to {arg}")
      return arg
    case Ops.PERMUTE:
      s0 = src[0].shape
      if s0 is None or sorted(arg) != list(range(len(s0))): raise ValueError(f"invalid PERMUTE {arg} for {s0}")
      return tuple(s0[i] for i in arg)
    case Ops.PAD:
      s0 = src[0].shape
      if s0 is None or len(s0) != len(arg): raise ValueError(f"invalid PAD {arg} for {s0}")
      if any(smin(b) < 0 or smin(e) < 0 for b, e in arg): raise ValueError(f"negative PAD {arg}")
      return tuple(simp_sint(s + b + e) for s, (b, e) in zip(s0, arg))
    case Ops.SHRINK:
      s0 = src[0].shape
      if s0 is None or len(s0) != len(arg): raise ValueError(f"invalid SHRINK {arg} for {s0}")
      for s, (b, e) in zip(s0, arg):
        if smin(b) < 0 or smax(e) > smax(s) or smin(simp_sint(e - b)) < 0:
          raise ValueError(f"SHRINK {_fmt_sint(arg)} out of bounds for {_fmt_sint(s0)}")
      return tuple(simp_sint(e - b) for b, e in arg)
    case Ops.FLIP:
      s0 = src[0].shape
      if s0 is None or len(s0) != len(arg): raise ValueError(f"invalid FLIP {arg} for {s0}")
      return s0
    case Ops.REDUCE_AXIS:
      s0 = src[0].shape
      red_op, axes = arg
      if s0 is None: raise ValueError("REDUCE_AXIS requires shaped source")
      if red_op not in (Ops.ADD, Ops.MUL, Ops.MAX, Ops.MIN): raise ValueError(f"unsupported REDUCE_AXIS op {red_op}")
      if any(not (0 <= ax < len(s0)) for ax in axes): raise ValueError(f"REDUCE_AXIS axes {axes} out of range for {s0}")
      return tuple(1 if i in axes else s for i, s in enumerate(s0))
    case Ops.ARGMAX if space is Space.TENSOR:
      s0 = src[0].shape
      if s0 is None or not (0 <= arg < len(s0)): raise ValueError(f"ARGMAX axis {arg} out of range for {s0}")
      return tuple(1 if i == arg else s for i, s in enumerate(s0))
    case Ops.TOPK:
      s0 = src[0].shape
      if s0 is None or not (0 <= arg.dim < len(s0)): raise ValueError(f"TOPK dim {arg.dim} out of range for {s0}")
      if not (0 <= arg.k <= smin(s0[arg.dim])): raise ValueError(f"TOPK k={arg.k} out of range for dim size {s0[arg.dim]}")
      return tuple(arg.k if i == arg.dim else s for i, s in enumerate(s0))
    case Ops.TAKE:
      s0, s1 = src[0].shape, src[1].shape
      if s0 is None or s1 is None or not (0 <= arg < len(s0)): raise ValueError(f"invalid TAKE dim={arg} for {s0}, {s1}")
      return s0[:arg] + s1 + s0[arg + 1:]
    case Ops.GATHER:
      s0, s1 = src[0].shape, src[1].shape
      if s0 is None or s1 is None or len(s0) != len(s1) or not (0 <= arg < len(s0)):
        raise ValueError(f"invalid GATHER dim={arg} for {s0}, {s1}")
      return s1
    case Ops.SCATTER:
      s0, s1, s2 = src[0].shape, src[1].shape, src[2].shape
      if s0 is None or s1 is None or s2 is None or not (0 <= arg < len(s0)):
        raise ValueError(f"invalid SCATTER dim={arg} for {s0}, {s1}, {s2}")
      expected = s0[:arg] + s1 + s0[arg + 1:]
      if s2 != expected: raise ValueError(f"SCATTER value shape {s2} != expected {expected}")
      return s0
    case Ops.CONTIGUOUS | Ops.AFTER:
      return src[0].shape
    case Ops.CAST | Ops.BITCAST:
      if space is Space.TENSOR: return src[0].shape
      return () if (space is Space.SCALAR and src[0].shape == ()) else None
    case _ if op in GroupOp.ALU:
      if space is Space.TENSOR:
        shapes = [s.shape for s in src if s.shape is not None and s.shape != ()]
        if not shapes: return ()
        if any(sh != shapes[0] for sh in shapes[1:]):
          raise ValueError(f"{op.name} tensor shape mismatch: {[s.shape for s in src]}")
        return shapes[0]
      if space is Space.SCALAR and src and all(s.shape == () for s in src): return ()
      return None
    case _:
      return None

# hash-consed: structurally equal UOps are the same object
class UOp(Mixin, metaclass=_UOpMeta):
  __slots__ = ("op", "dtype", "src", "arg", "space", "shape", "_src_ops", "__weakref__")

  @property
  def _uop(self) -> "UOp": return self
  @classmethod
  def _wrap_uop(cls, u: "UOp") -> "UOp": return u

  def __init__(self, op: Ops, dtype: DType = dtypes.void, src: tuple[UOp, ...] = (), arg: Any = None):
    space = _infer_space(op, src, arg)
    shape = _infer_shape(op, src, arg, space)
    object.__setattr__(self, "op", op)
    object.__setattr__(self, "dtype", dtype)
    object.__setattr__(self, "src", src)
    object.__setattr__(self, "arg", arg)
    object.__setattr__(self, "space", space)
    object.__setattr__(self, "shape", shape)
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

  # ---- structural properties (tinygrad-compatible) ----

  @property
  def body(self) -> UOp:
    if self.op is not Ops.CALL: raise ValueError(f"body is only defined on CALL, got {self.op.name}")
    return self.src[0]

  @property
  def src_without_body(self) -> tuple[UOp, ...]:
    return self.src[1:] if self.op is Ops.CALL else self.src

  @property
  def without_after(self) -> UOp:
    return self.src[0].without_after if self.op is Ops.AFTER else self

  @property
  def storage_base(self) -> UOp:
    u = self
    while u.op in GroupOp.Movement or u.op in (Ops.BITCAST, Ops.AFTER, Ops.INDEX):
      u = u.src[0]
    return u

  def has_buffer_identity(self, after_ok: bool = True) -> bool:
    u = self.without_after if after_ok else self
    return u.op in (Ops.BUFFER, Ops.ALLOC)

  @property
  def is_ins(self) -> bool:
    return self.op is Ops.CALL and len(self.src) >= 1 and self.src[0].op is Ops.NATIVE

  @property
  def ins_op(self) -> Any:
    return self.src[0].arg.code if self.is_ins else None

  # sources before users; gate(u) == False skips u and its subtree
  def toposort(self, gate: Callable[[UOp], bool] | None = None, enter_calls: bool = False) -> list[UOp]:
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
        srcs = node.src if enter_calls else node.src_without_body
        for s in reversed(srcs):
          if s not in seen: stack.append((s, False))
    return order

  def substitute(self, mapping: dict[UOp, UOp]) -> UOp:
    if not mapping: return self
    return substitute(self, mapping)

  # ---- construction helpers ----

  @staticmethod
  def noop() -> UOp: return UOp(Ops.NOOP, dtypes.void)

  @staticmethod
  def const(dtype: DType, val: Any) -> UOp:
    if dtype is dtypes.bool: val = bool(val)
    elif dtype.is_float: val = float(val)
    elif dtype.is_int: val = int(val)
    return UOp(Ops.CONST, dtype, (), val)

  @staticmethod
  def sink(*srcs: UOp, arg: Any = None) -> UOp: return UOp(Ops.SINK, dtypes.void, srcs, arg)

  @staticmethod
  def param(slot: int, dtype: DType = dtypes.void, name: str = "", space: Space = Space.REG,
            shape: tuple[int, ...] = ()) -> UOp:
    return UOp(Ops.PARAM, dtype, (), ParamArg(slot, name, space, shape))

  @staticmethod
  def stack(*srcs: UOp) -> UOp:
    dt = srcs[0].dtype if srcs else dtypes.void
    return UOp(Ops.STACK, dt, srcs)

  @staticmethod
  def native(code: Any, src: UOp | None = None, dtype: DType | None = None, fmt: bool = False) -> UOp:
    if dtype is not None:
      assert src is None, f"native takes either src or dtype, not both"
      src = UOp.param(-1, dtype, space=Space.REG if dtype is not dtypes.void else Space.NONE)
    dt = src.dtype if src is not None else dtypes.void
    return UOp(Ops.NATIVE, dt, (src,) if src is not None else (), NativeInfo(code, fmt))

  def call(self, *srcs: UOp, role: str = "") -> UOp:
    return UOp(Ops.CALL, self.dtype, (self, *srcs), CallInfo(role))

  @staticmethod
  def ins(op: Any, src: tuple[UOp, ...] = (), dtype: DType = dtypes.void, *regs: UOp, role: str = "") -> UOp:
    """Tinygrad-style machine instruction UOp: CALL(NATIVE(op, regs), *src)."""
    if regs:
      params = [UOp.param(r.arg.slot, dtype, name=r.arg.name, space=r.space)
                if r.op is Ops.PARAM and r.dtype != dtype and dtype is not dtypes.void else r for r in regs]
      native_src = params[0].after(*params[1:])
    else:
      native_src = UOp.param(-1, dtype, space=Space.REG if dtype is not dtypes.void else Space.NONE)
    return UOp.native(op, native_src).call(*src, role=role)

  @staticmethod
  def linear(*uops: UOp, arg: Any = "") -> UOp: return UOp(Ops.LINEAR, dtypes.void, uops, arg)

  @staticmethod
  def source(text: str) -> UOp: return UOp(Ops.SOURCE, dtypes.void, (), text)

  @staticmethod
  def binary(data: bytes) -> UOp: return UOp(Ops.BINARY, dtypes.u8, (), data)

  @staticmethod
  def program(*srcs: UOp, arg: Any = None) -> UOp: return UOp(Ops.PROGRAM, dtypes.void, srcs, arg)

  def after(self, *deps: UOp) -> UOp: return UOp(Ops.AFTER, self.dtype, (self, *deps)) if deps else self
  def index(self, idx: UOp | int) -> UOp: return UOp(Ops.INDEX, self.dtype, (self, UOp._i32(idx)))
  def backedge(self, loop: UOp, cond: UOp) -> UOp: return UOp(Ops.BACKEDGE, self.dtype, (self, loop, cond))

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
      if len(srcs) == 2:
        arg = default_fidelity(srcs[0].dtype, srcs[1].dtype)
        out_dt = max((srcs[0].dtype, srcs[1].dtype), key=lambda d: d.bits)
      else:
        arg = Fidelity.LOFI
    return UOp(op, out_dt, srcs, arg)

  @property
  def is_fpu(self) -> bool:
    return self.op is Ops.MVMUL or any(s.space in _SRC_BANKS for s in self.src)

  @property
  def fidelity(self) -> Fidelity | None:
    if self.op is Ops.MVMUL: return self.arg.fidelity
    if isinstance(self.arg, Fidelity): return self.arg
    return None

  def with_fidelity(self, fidelity: Fidelity | int) -> UOp:
    f = Fidelity(fidelity)
    if not self.is_fpu: raise ValueError(f"with_fidelity() only applies to FPU ops, got {self.op.name} ({self.space})")
    if self.op is Ops.MVMUL:
      from dataclasses import replace
      return self.replace(arg=replace(self.arg, fidelity=f))
    return self.replace(arg=f)

  # ---- SFPU tile/lane reductions (Layer 1) ----

  def reduce_row(self, op: Ops = Ops.ADD) -> UOp:
    if op not in (Ops.ADD, Ops.MAX): raise ValueError(f"reduce_row supports ADD or MAX, got {op}")
    return UOp(Ops.REDUCE_ROW, self.dtype, (self,), op)

  def reduce_lanes(self, op: Ops = Ops.ADD, scope: str = "all") -> UOp:
    if op not in (Ops.ADD, Ops.MAX, Ops.MIN): raise ValueError(f"reduce_lanes supports ADD/MAX/MIN, got {op}")
    if scope not in ("all", "row8"): raise ValueError(f"reduce_lanes scope must be 'all' or 'row8', got {scope!r}")
    return UOp(Ops.REDUCE_LANES, self.dtype, (self,), (op, scope))

  # ---- symbolic Variable helpers (tinygrad-compatible) ----

  @staticmethod
  def variable(name: str, min_val: int, max_val: int, dtype: DType | str = dtypes.i32) -> UOp:
    if min_val > max_val: raise ValueError(f"Variable {name!r}: min_val ({min_val}) > max_val ({max_val})")
    return UOp(Ops.DEFINE_VAR, dtypes.from_name(dtype), (), VarArg(name, int(min_val), int(max_val)))

  @property
  def is_variable(self) -> bool: return self.op is Ops.DEFINE_VAR
  @property
  def is_bound_var(self) -> bool: return self.op is Ops.DEFINE_VAR and self.arg.val is not None
  @property
  def vmin(self) -> int: return smin(self)
  @property
  def vmax(self) -> int: return smax(self)

  def bind(self, val: int) -> UOp:
    if self.op is not Ops.DEFINE_VAR or self.arg.val is not None:
      raise ValueError(f"bind() requires an unbound DEFINE_VAR, got {self.op.name}")
    v = int(val)
    if not (self.arg.vmin <= v <= self.arg.vmax):
      raise ValueError(f"bind({v}) out of range [{self.arg.vmin}, {self.arg.vmax}] for {self.arg.name!r}")
    return self.replace(arg=VarArg(self.arg.name, self.arg.vmin, self.arg.vmax, v))

  def unbound(self) -> UOp:
    if self.op is not Ops.DEFINE_VAR: raise ValueError(f"unbound() requires DEFINE_VAR, got {self.op.name}")
    return self if self.arg.val is None else self.replace(arg=VarArg(self.arg.name, self.arg.vmin, self.arg.vmax, None))

  def unbind(self) -> tuple[UOp, int]:
    if not self.is_bound_var: raise ValueError("unbind() requires a bound DEFINE_VAR")
    return self.unbound(), self.arg.val

  def variables(self) -> list[UOp]:
    seen: set[UOp] = set()
    vars_: set[UOp] = set()
    stack = [self]
    while stack:
      u = stack.pop()
      if u in seen: continue
      seen.add(u)
      if u.op is Ops.DEFINE_VAR: vars_.add(u.unbound())
      stack.extend(u.src)
      stack.extend(_iter_arg_uops(u.arg))
    return sorted(vars_, key=lambda v: v.arg.name)

  def unbind_all(self) -> tuple[UOp, dict[UOp, int]]:
    bound: dict[UOp, UOp] = {}
    vals: dict[UOp, int] = {}
    seen: set[UOp] = set()
    stack = [self]
    while stack:
      u = stack.pop()
      if u in seen: continue
      seen.add(u)
      if u.is_bound_var:
        ub = u.unbound()
        if ub in vals and vals[ub] != u.arg.val:
          raise ValueError(f"conflicting bound values for {ub.arg.name!r}: {vals[ub]} vs {u.arg.val}")
        bound[u] = ub
        vals[ub] = u.arg.val
      stack.extend(u.src)
      stack.extend(_iter_arg_uops(u.arg))
    return (substitute_all(self, bound) if bound else self), vals

  def substitute_vars(self, var_vals: dict[UOp | str, int | UOp]) -> UOp:
    if not var_vals: return self
    by_name: dict[str, UOp] = {}
    by_uop: dict[UOp, UOp] = {}
    for k, v in var_vals.items():
      repl = v if isinstance(v, UOp) else UOp.const(dtypes.i32, int(v))
      if isinstance(k, str): by_name[k] = repl
      else: by_uop[k.unbound() if k.is_bound_var else k] = repl
    mapping: dict[UOp, UOp] = {}
    seen: set[UOp] = set()
    stack = [self]
    while stack:
      u = stack.pop()
      if u in seen: continue
      seen.add(u)
      if u.op is Ops.DEFINE_VAR:
        ub = u.unbound()
        if ub in by_uop: mapping[u] = by_uop[ub]
        elif ub.arg.name in by_name: mapping[u] = by_name[ub.arg.name]
      stack.extend(u.src)
      stack.extend(_iter_arg_uops(u.arg))
    return substitute_all(self, mapping) if mapping else self

  # ---- Layer 0 axis reduction & scatter primitives ----

  def reduce_axis(self, op: Ops, axes: tuple[int, ...]) -> UOp:
    axes = tuple(sorted(set(int(a) for a in axes)))
    return self if not axes else UOp(Ops.REDUCE_AXIS, self.dtype, (self,), (op, axes))

  def scatter(self, dim: int, index: UOp, val: UOp) -> UOp:
    if val.dtype != self.dtype: raise TypeError(f"SCATTER dtype mismatch: {self.dtype} vs {val.dtype}")
    return UOp(Ops.SCATTER, self.dtype, (self, index, val), int(dim))

  @staticmethod
  def arange(start: int | float | UOp, stop: int | float | UOp, step: int | float | UOp = 1,
             dtype: DType | str = dtypes.i32) -> UOp:
    dt = dtypes.from_name(dtype)
    if dt.is_int:
      start = simp_sint(start) if isinstance(start, (int, UOp)) else int(start)
      stop = simp_sint(stop) if isinstance(stop, (int, UOp)) else int(stop)
      step = simp_sint(step) if isinstance(step, (int, UOp)) else int(step)
    elif dt.is_float:
      if not isinstance(start, UOp): start = float(start)
      if not isinstance(stop, UOp): stop = float(stop)
      if not isinstance(step, UOp): step = float(step)
    return UOp(Ops.ARANGE, dt, (), ArangeArg(start, stop, step))

  # ---- kernel builders ----

  @staticmethod
  def _i32(x: UOp | int) -> UOp: return x if isinstance(x, UOp) else UOp.const(dtypes.i32, int(x))

  @staticmethod
  def special(end: UOp | int, name: str) -> UOp:
    return UOp(Ops.SPECIAL, dtypes.i32, (UOp._i32(end),), name)

  @staticmethod
  def range(end: UOp | int, axis: int, name: str = "") -> UOp:
    return UOp(Ops.RANGE, dtypes.i32, (UOp._i32(end),), RangeArg(axis, name))

  @staticmethod
  def loop_range(axis: int = 0, name: str = "") -> UOp:
    """Unbounded loop RANGE (paired with BACKEDGE for while/polling loops)."""
    return UOp(Ops.RANGE, dtypes.void, (UOp.noop(),), RangeArg(axis, name))

  @staticmethod
  def buffer(name: str, shape: tuple[int, ...] | int, dtype: DType | str, space: Space = Space.DRAM,
             addr: int | None = None, tiles_per_page: int = 1) -> UOp:
    if space not in (Space.TENSOR, Space.DRAM, Space.HOST, Space.L1, Space.SCALAR): raise ValueError(f"invalid buffer space {space}")
    dt = dtypes.from_name(dtype)
    return UOp(Ops.BUFFER, dt, (), BufferArg(name, space, (shape,) if isinstance(shape, int) else tuple(shape), dt, addr, tiles_per_page))

  @staticmethod
  def alloc(name: str, space: Space, dtype: DType | str, shape: tuple[int, ...] | int = (32, 32)) -> UOp:
    if space not in (Space.DST, Space.LREG, Space.L1, Space.SCALAR, Space.REG):
      raise ValueError(f"alloc space must be DST, LREG, L1, SCALAR, or REG, got {space}")
    dt = dtypes.from_name(dtype)
    return UOp(Ops.ALLOC, dt, (), AllocArg(name, space, (shape,) if isinstance(shape, int) else tuple(shape), dt))

  @staticmethod
  def barrier(scope: str | tuple[tuple[int, int], tuple[int, int]] = "all", tag: int = 0) -> UOp:
    return UOp(Ops.BARRIER, dtypes.void, (), BarrierArg(scope, tag))

  @staticmethod
  def lane_id(dtype: DType | str = dtypes.i32) -> UOp: return UOp(Ops.LANE_ID, dtypes.from_name(dtype), ())

  @staticmethod
  def replay(insns: Sequence[int], *deps: UOp, dtype: DType | str = dtypes.fp32, dest: Space = Space.DST, name: str = "") -> UOp:
    return UOp(Ops.REPLAY, dtypes.from_name(dtype), deps, ReplayArg(tuple(int(w) for w in insns), dest, name))

  @staticmethod
  def mop(cfg: Sequence[int], *deps: UOp, dtype: DType | str = dtypes.fp32, dest: Space = Space.DST, name: str = "") -> UOp:
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
    if rng.op is not Ops.RANGE: raise TypeError(f"carry() requires a RANGE, got {rng.op.name}")
    sp = self.space if space is None else space
    if sp not in (Space.DST, Space.LREG, Space.L1, Space.SCALAR):
      raise ValueError(f"carry residency must be DST, LREG, L1, or SCALAR, got {sp}")
    return UOp(Ops.CARRY, self.dtype, (self, rng), CarryArg(index, sp, name))

  def loop(self, inits: Sequence[UOp], body, *, spaces: Sequence[Space | None] | None = None,
           names: Sequence[str] | None = None) -> tuple[UOp, ...]:
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

  def unpack(self, dest: Space = Space.DST, dtype: DType | str | None = None, shape: tuple[int, int] = (32, 32),
             transpose: bool = False, allow_tf32: bool = False) -> UOp:
    if dest not in (Space.SRCA, Space.SRCB, Space.DST): raise ValueError(f"unpack dest must be SRCA, SRCB, or DST, got {dest}")
    dt = (dtypes.fp32 if dest is Space.DST else self.dtype) if dtype is None else dtypes.from_name(dtype)
    return UOp(Ops.UNPACK, dt, (self,), UnpackArg(dest, shape, transpose, allow_tf32))

  # self is SrcB, srca is SrcA
  def mvmul(self, srca: UOp, tile: tuple[int, int, int] = (32, 32, 32), fidelity: Fidelity | int | None = None,
            dtype: DType | str = dtypes.fp32) -> UOp:
    f = default_fidelity(self.dtype, srca.dtype) if fidelity is None else Fidelity(fidelity)
    return UOp(Ops.MVMUL, dtypes.from_name(dtype), (self, srca), MvmulArg(tile, f))

  def pack(self, dtype: DType | str = dtypes.bf16, shape: tuple[int, int] = (32, 32), l1_acc: bool = False) -> UOp:
    return UOp(Ops.PACK, dtypes.from_name(dtype), (self,), PackArg(shape, l1_acc))

  def __repr__(self) -> str: return pretty(self)

Variable = UOp.variable

def _fmt_ins_regs(u: UOp) -> str:
  if not u.is_ins or not u.body.src: return ""
  s = u.body.src[0]
  rs = s.src if s.op is Ops.AFTER else (s,)
  parts = []
  for r in rs:
    if r.op is Ops.PARAM and r.arg.slot >= 0:
      parts.append(r.arg.name or f"r{r.arg.slot}")
  return "[" + ",".join(parts) + "]" if parts else ""

def pretty(root: UOp | Sequence[UOp], limit: int = 200) -> str:
  if isinstance(root, UOp) and root.op is Ops.LINEAR:
    if root.src and all(s.op is Ops.LINEAR for s in root.src):
      return "\n".join(f"--- {s.arg or f'core{i}'} ---\n{pretty(s, limit=limit)}" for i, s in enumerate(root.src))
    nodes = list(root.src)
  elif isinstance(root, UOp):
    nodes = root.toposort()
  else:
    nodes = list(root)
  idx = {u: i for i, u in enumerate(nodes)}
  has_tensor = any(u.space is Space.TENSOR for u in nodes)
  lines = []
  for i, u in enumerate(nodes):
    srcs = [idx[s] if s in idx else (_fmt_sint(s.arg) if s.op is Ops.CONST else f"<{s.op.name}>") for s in u.src_without_body]
    if u.is_ins:
      code = u.ins_op
      op_str = f"INS:{code.name}" if isinstance(code, Enum) else f"INS:{code!r}"
      reg_str = _fmt_ins_regs(u)
      role = f" @{u.arg.role}" if isinstance(u.arg, CallInfo) and u.arg.role else ""
      lines.append(f"{i:3d} {op_str:<22s} {u.space.name:<6s} {u.dtype.name:<5s} {reg_str:<10s} {srcs!s:<18s}{role}")
    elif has_tensor:
      lines.append(f"{i:3d} {u.op.name:<13s} {u.space.name:<6s} {u.dtype.name:<5s} {(_fmt_sint(u.shape) if u.shape is not None else ''):<22s} {srcs!s:<14s} {_fmt_sint(u.arg)}")
    else:
      lines.append(f"{i:3d} {u.op.name:<13s} {u.space.name:<6s} {u.dtype.name:<5s} {srcs!s:<14s} {_fmt_sint(u.arg)}")
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

    self.req_ops: frozenset[Ops] = frozenset()
    match src:
      case _ if is_any: self.src_mode, self.src = "any", tuple(src or ())
      case None: self.src_mode, self.src = "none", ()
      case UPat(): self.src_mode, self.src = "repeat", (src,)
      case list(): self.src_mode, self.src = "perm", tuple(src)
      case tuple(): self.src_mode, self.src = "exact", src
      case _: raise TypeError(f"invalid UPat src: {type(src).__name__}")
    if self.src_mode in ("perm", "exact"):
      self.req_ops = frozenset(p.op[0] for p in self.src if p.op is not None and len(p.op) == 1)

  @staticmethod
  def any(*pats: UPat) -> UPat: return UPat(src=pats, is_any=True)
  @staticmethod
  def var(name: str | None = None, dtype=None, space=None) -> UPat: return UPat(dtype=dtype, space=space, name=name)
  @staticmethod
  def const(name: str | None = None, dtype=None, arg=None) -> UPat: return UPat(Ops.CONST, dtype=dtype, arg=arg, name=name)

  @staticmethod
  def ins(code: Any = None, src: tuple[UPat, ...] | None = None, dtype=None, name: str | None = None,
          allow_any_len: bool = False) -> UPat:
    if code is None:
      body = UPat(Ops.NATIVE)
    elif isinstance(code, (set, frozenset, tuple, list)):
      codes = frozenset(code)
      body = UPat(Ops.NATIVE, arg=lambda a: isinstance(a, NativeInfo) and a.code in codes)
    elif callable(code):
      body = UPat(Ops.NATIVE, arg=lambda a: isinstance(a, NativeInfo) and code(a.code))
    else:
      body = UPat(Ops.NATIVE, arg=lambda a: isinstance(a, NativeInfo) and a.code == code)
    if src is None:
      return UPat(Ops.CALL, dtype=dtype, src=(body,), allow_any_len=True, name=name)
    return UPat(Ops.CALL, dtype=dtype, src=(body, *src), allow_any_len=allow_any_len, name=name)

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
      def run(u: UOp, ctx: Any) -> Any:
        for binds in pat.match(u, {}):
          if (res := fn(ctx=ctx, **binds)) is not None: return res
        return None
    else:
      def run(u: UOp, _ctx: Any) -> Any:
        for binds in pat.match(u, {}):
          if (res := fn(**binds)) is not None: return res
        return None
    return run

  def __add__(self, other: PatternMatcher) -> PatternMatcher:
    return PatternMatcher(self.rules + other.rules)

  def rewrite(self, u: UOp, ctx: Any = None) -> Any:
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

# ---- iterative graph rewriter, linearizer, and line_rewrite ----

def graph_rewrite(
  root: UOp,
  pm: PatternMatcher,
  ctx: Any = None,
  bottom_up: bool = False,
  bpm: PatternMatcher | None = None,
  limit: int = 250_000,
) -> UOp:
  """Rewrite every reachable UOp under root to a fixed point."""
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

    match phase:
      case 0:
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
        for s in reversed(cur.src_without_body):
          if s not in memo and s not in started:
            started.add(s)
            stack.append((s, 0, s))

      case 1:
        body_prefix = (cur.src[0],) if cur.op is Ops.CALL else ()
        new_src: list[UOp] = list(body_prefix)
        blocked: UOp | None = None
        for s in cur.src_without_body:
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

      case _:
        if (res := memo.get(cur)) is not None:
          finish(orig, res)
        else:
          waiting[cur].append((orig, 2, cur))

  if root not in memo:
    raise RuntimeError("graph_rewrite stalled: cyclic dependency between rewritten nodes")
  return memo[root]

def line_rewrite(lst: list[UOp], pm: PatternMatcher, ctx: Any = None) -> list[UOp]:
  """Rewrite a linearized list[UOp] in order; each rule returns (replacement_uop, [emitted_uops])."""
  newlst: list[UOp] = []
  replaced: dict[UOp, UOp] = {}
  for u in lst:
    if u.op is Ops.CALL:
      nu = u.replace(src=(u.src[0], *(replaced.get(x, x) for x in u.src[1:])))
    else:
      nu = u.replace(src=tuple(replaced.get(x, x) for x in u.src))
    ret: tuple[UOp, list[UOp]] | None = pm.rewrite(nu, ctx)
    if ret is None:
      replaced[u] = nu
      newlst.append(nu)
    else:
      replaced[u] = ret[0]
      newlst.extend(ret[1])
  return newlst

def _open_ranges_for_lin(nodes: list[UOp]) -> dict[UOp, frozenset[UOp]]:
  active: dict[UOp, frozenset[UOp]] = {}
  for u in nodes:
    match u.op:
      case Ops.RANGE:
        active[u] = frozenset({u}) | (active[u.src[0]] if u.src else frozenset())
      case Ops.END | Ops.REDUCE:
        closed = frozenset(u.src[1:])
        active[u] = (active[u.src[0]] - closed) | frozenset().union(*(active[r.src[0]] for r in u.src[1:] if r.op is Ops.RANGE and r.src))
      case Ops.BACKEDGE:
        active[u] = (active[u.src[0]] | active[u.src[2]]) - frozenset({u.src[1]})
      case _:
        active[u] = frozenset().union(*(active[s] for s in u.src_without_body)) if u.src_without_body else frozenset()
  return active

def linearize(sink: UOp) -> list[UOp]:
  """Priority toposort of a UOp DAG into a flat list[UOp], preserving loop nesting."""
  lst = sink.toposort()
  ranges = _open_ranges_for_lin(lst)
  out_degree: collections.defaultdict[UOp, int] = collections.defaultdict(int)
  priorities: dict[UOp, tuple[int, int, int]] = {}

  for pos, u in enumerate(lst):
    for s in u.src_without_body: out_degree[s] += 1
    match u.op:
      case Ops.PARAM: prio = -20
      case Ops.BUFFER | Ops.ALLOC: prio = -18
      case Ops.LOAD: prio = -1
      case Ops.STORE: prio = 1
      case Ops.RANGE: prio = 5
      case Ops.END | Ops.BACKEDGE: prio = -5
      case _: prio = 0
    priorities[u] = (len(ranges[u]), prio, pos)

  nkey = {u: i for i, u in enumerate(sorted(lst, key=lambda x: priorities[x]))}
  heap = [(-nkey[sink], sink)]
  newlst: list[UOp] = []
  while heap:
    u = heapq.heappop(heap)[1]
    newlst.append(u)
    for v in u.src_without_body:
      out_degree[v] -= 1
      if out_degree[v] == 0: heapq.heappush(heap, (-nkey[v], v))
  return newlst[::-1]

def substitute(root: UOp, mapping: dict[UOp, UOp]) -> UOp:
  if not mapping: return root
  if root in mapping: return mapping[root]
  memo: dict[UOp, UOp] = {}
  for u in root.toposort(gate=lambda n: n not in mapping):
    if u.op is Ops.CALL:
      new_src = (u.src[0], *(mapping.get(s, memo.get(s, s)) for s in u.src[1:]))
    else:
      new_src = tuple(mapping.get(s, memo.get(s, s)) for s in u.src)
    memo[u] = u if new_src == u.src else UOp(u.op, u.dtype, new_src, u.arg)
  return memo[root]

def substitute_all(root: UOp, mapping: dict[UOp, UOp]) -> UOp:
  """Like substitute(), but also substitutes UOps embedded inside symbolic shape/slice args."""
  if not mapping: return root
  memo: dict[UOp, UOp] = {}

  def walk(u: UOp) -> UOp:
    if u in mapping: return mapping[u]
    if u in memo: return memo[u]
    new_src = (u.src[0], *(walk(s) for s in u.src[1:])) if u.op is Ops.CALL else tuple(walk(s) for s in u.src)
    new_arg = _map_arg_uops(u.arg, walk)
    if new_src == u.src and _arg_key(new_arg) == _arg_key(u.arg):
      res = u
    else:
      res = UOp(u.op, u.dtype, new_src, new_arg)
    memo[u] = res
    return res

  return walk(root)
