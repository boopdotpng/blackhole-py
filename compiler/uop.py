import collections, functools, heapq, inspect, itertools, math, operator, struct, weakref
from dataclasses import dataclass
from enum import Enum, auto
from collections.abc import Callable, Iterator, Sequence
from typing import Any, Union
from .dtype import DType, Invalid, InvalidType, dtypes, least_upper_dtype
from .mixin import Mixin

# ---- opcodes ----

class Ops(Enum):
  # graph structure & sync
  SINK = auto(); AFTER = auto(); BARRIER = auto(); NOOP = auto()

  # values, kernel control & local memory
  CONST = auto(); SPECIAL = auto(); PARAM = auto(); BUFFER = auto(); ALLOC = auto(); STACK = auto(); INDEX = auto()
  RANGE = auto(); END = auto(); BACKEDGE = auto(); IF = auto(); REDUCE = auto(); LOAD = auto(); STORE = auto()

  # ALU
  ADD = auto(); SUB = auto(); MUL = auto(); DIV = auto(); MOD = auto(); MULACC = auto(); MAX = auto(); NEG = auto()
  EXP2 = auto(); LOG2 = auto(); SIN = auto(); SQRT = auto(); RECIP = auto()
  CMPLT = auto(); CMPEQ = auto(); CMPNE = auto(); WHERE = auto()
  AND = auto(); OR = auto(); XOR = auto(); SHL = auto(); SHR = auto()
  CAST = auto(); BITCAST = auto()

  # Layer 0 movement & materialization
  RESHAPE = auto(); EXPAND = auto(); PERMUTE = auto(); PAD = auto(); SHRINK = auto(); STAGE = auto()

  # Bottom-layer ISA & program representation (tinygrad UOp.ins = CALL(NATIVE, ...))
  NATIVE = auto(); CALL = auto(); LINEAR = auto(); SOURCE = auto(); BINARY = auto(); PROGRAM = auto()

class GroupOp:
  All = frozenset(Ops)
  Unary = frozenset({Ops.NEG, Ops.EXP2, Ops.LOG2, Ops.SIN, Ops.SQRT, Ops.RECIP})
  Binary = frozenset({Ops.ADD, Ops.SUB, Ops.MUL, Ops.DIV, Ops.MOD, Ops.MAX, Ops.CMPLT, Ops.CMPEQ, Ops.CMPNE,
                      Ops.AND, Ops.OR, Ops.XOR, Ops.SHL, Ops.SHR})
  Ternary = frozenset({Ops.WHERE, Ops.MULACC})
  ALU = Unary | Binary | Ternary
  Broadcastable = Binary | Ternary
  Elementwise = ALU | frozenset({Ops.CAST, Ops.BITCAST})
  Comparison = frozenset({Ops.CMPLT, Ops.CMPEQ, Ops.CMPNE})
  Associative = frozenset({Ops.ADD, Ops.MUL, Ops.AND, Ops.OR, Ops.XOR, Ops.MAX})
  Commutative = frozenset({Ops.ADD, Ops.MUL, Ops.MAX, Ops.CMPEQ, Ops.CMPNE, Ops.AND, Ops.OR, Ops.XOR})
  Idempotent = frozenset({Ops.AND, Ops.OR, Ops.MAX})
  Irreducible = frozenset({Ops.CONST, Ops.PARAM, Ops.SPECIAL, Ops.RANGE})
  Effect = frozenset({Ops.STORE, Ops.BARRIER, Ops.CALL})
  Movement = frozenset({Ops.RESHAPE, Ops.EXPAND, Ops.PERMUTE, Ops.PAD, Ops.SHRINK})
  Defines = frozenset({Ops.BUFFER, Ops.ALLOC, Ops.PARAM})
  Program = frozenset({Ops.NATIVE, Ops.CALL, Ops.LINEAR, Ops.SOURCE, Ops.BINARY, Ops.PROGRAM})
  Kernel = frozenset({Ops.SPECIAL, Ops.RANGE, Ops.END, Ops.BACKEDGE, Ops.IF, Ops.LOAD, Ops.BARRIER})
  PassthroughDType = Movement | frozenset({Ops.NEG, Ops.REDUCE, Ops.AFTER, Ops.STAGE, Ops.RANGE, Ops.SPECIAL, Ops.LOAD, Ops.INDEX, Ops.CALL})
  PromoteDType = (Binary - Comparison - {Ops.SHL, Ops.SHR}) | {Ops.MULACC}

# ---- typed UOp.arg specs (frozen & hashable; UOp dependencies, including shapes, always live in UOp.src) ----

@dataclass(frozen=True)
class KernelArg:
  name: str
  cores: int = 1

# slot -1 is "no register"; file is "gpr" / "lreg" for ISA registers; a Variable is a PARAM with vmin_vmax (val once bound)
@dataclass(frozen=True)
class ParamArg:
  slot: int
  dtype: DType
  name: str = ""
  file: str = ""
  vmin_vmax: tuple[int, int] | None = None
  val: int | None = None

@dataclass(frozen=True)
class NativeInfo:
  code: Any
  fmt: bool = False

@dataclass(frozen=True)
class CallInfo:
  role: str = ""  # optional core tag for ISA instructions
  name: str = ""  # optional function name

# a BUFFER's / ALLOC's shape is its src
@dataclass(frozen=True)
class BufferArg:
  name: str
  dtype: DType
  addr: int | None = None
  space: str = "dram"

@dataclass(frozen=True)
class RangeArg:
  axis: int
  name: str = ""

@dataclass(frozen=True)
class StageArg:
  removable: bool = True
  space: str = "dram"
  inline: bool = True

_ALLOC_ID = itertools.count()

# ---- dtype & shape: derived from (op, src, arg), computed on first use and cached ----

class recursive_property:
  """a cached property computed in post order, iteratively, so deep graphs don't hit the recursion limit"""
  def __init__(self, fxn):
    self.fxn, self.nm = fxn, fxn.__name__
  def __get__(self, x, owner=None):
    if x is None: return self
    nm, stack = self.nm, [x]
    while stack:
      if nm in (d := (node := stack[-1]).__dict__): stack.pop()
      elif missing := [s for s in node.src if nm not in s.__dict__]: stack.extend(reversed(missing))
      else:
        d[nm] = self.fxn(node)
        stack.pop()
    return x.__dict__[nm]

def _promo(src: Sequence["UOp"]) -> DType: return least_upper_dtype(*(s.dtype for s in src))

def dtype_from_uop(op: Ops, src: tuple["UOp", ...], arg: Any) -> DType:
  if op in GroupOp.PassthroughDType: return src[0].dtype
  if op in GroupOp.PromoteDType: return _promo(src)
  match op:
    case Ops.CONST: return dtypes.from_py(arg)
    case Ops.CAST | Ops.BITCAST: return arg
    case Ops.BUFFER | Ops.ALLOC | Ops.PARAM: return arg.dtype
    case Ops.CMPLT | Ops.CMPEQ | Ops.CMPNE: return dtypes.bool
    case Ops.EXP2 | Ops.LOG2 | Ops.SIN | Ops.SQRT | Ops.RECIP:
      dt = src[0].dtype
      return dt if dt.is_float else dtypes.weakfloat if dt is dtypes.weakint else dtypes.fp32
    case Ops.WHERE:
      if src[0].dtype is not dtypes.bool: raise TypeError(f"WHERE condition must be bool, got {src[0].dtype}")
      if src[1].is_invalid: return src[2].dtype
      if src[2].is_invalid: return src[1].dtype
      return _promo(src[1:])
    case Ops.SHL | Ops.SHR: return src[0].dtype
    case Ops.STACK: return _promo(src) if src else dtypes.void
    case Ops.IF: return src[1].dtype
    case Ops.NATIVE: return src[0].dtype if src else dtypes.void
    case Ops.BINARY: return dtypes.u8
  return dtypes.void

def _broadcast_shape(*shapes: tuple["sint", ...]) -> tuple["sint", ...]:
  if all(s == shapes[0] for s in shapes): return shapes[0]
  # right-aligned; per dim, sizes of 1 broadcast to the others, which must agree
  nd = max(len(s) for s in shapes)
  ret = []
  for sizes in zip(*((1,) * (nd - len(s)) + tuple(s) for s in shapes)):
    rest = list(dict.fromkeys(s for s in sizes if isinstance(s, UOp) or s != 1))
    if len(rest) > 1: raise ValueError(f"shapes cannot be broadcast: {shapes}")
    ret.append(rest[0] if rest else 1)
  return tuple(ret)

def shape_from_uop(u: "UOp") -> tuple["sint", ...] | None:
  op, src = u.op, u.src
  if op in GroupOp.Unary or op in (Ops.CAST, Ops.BITCAST, Ops.AFTER): return src[0].shape
  if op in GroupOp.Broadcastable:
    shapes = [s.shape for s in src]
    # shapeless (Layer 1 tile) operands make the result shapeless
    return None if any(s is None for s in shapes) else _broadcast_shape(*shapes)
  match op:
    case Ops.CONST | Ops.RANGE | Ops.SPECIAL: return ()
    case Ops.PARAM: return src[0].as_shape if src else (() if u.arg.vmin_vmax is not None else None)
    case Ops.BUFFER | Ops.ALLOC: return src[0].as_shape
    case Ops.STACK: return (len(src),) + src[0].shape if src else ()
    case Ops.INDEX:
      ps = src[0].shape
      if ps is None: return None
      return tuple(d for s in src[1:] for d in (s.shape or ())) + ps[len(src) - 1:]
    case Ops.STAGE:
      if len(src) == 1: return src[0].shape
      ext = tuple((r.src[0].arg if r.src[0].op is Ops.CONST else simp_sint(r.src[0])) if r.op is Ops.RANGE else 1 for r in src[1:])
      return ext + (src[0].shape or ())
    case Ops.LOAD: return src[0].shape if len(src) == 1 else ()
    case Ops.STORE: return src[0].shape if len(src) == 2 else ()
    case Ops.END: return src[0].shape
    case Ops.REDUCE:
      ps = src[0].shape
      if ps is None: return None
      if (n := u.arg[1]) > len(ps): raise ValueError(f"REDUCE of {n} axes on shape {ps}")
      return ps[n:]
    case _ if op in GroupOp.Movement:
      ps, m = src[0].shape, u.marg
      if ps is None: raise ValueError(f"{op.name} requires a shaped source")
      match op:
        case Ops.RESHAPE:
          if sprod(ps) != sprod(m): raise ValueError(f"cannot reshape {_fmt_sint(ps)} to {_fmt_sint(m)}")
          return m
        case Ops.EXPAND: return tuple(m) + ps   # EXPAND only adds dims on the left
        case Ops.PERMUTE:
          if sorted(m) != list(range(len(ps))): raise ValueError(f"invalid permutation {m} of {ps}")
          return tuple(ps[i] for i in m)
        case Ops.PAD:
          if len(m) != len(ps) or any(smin(o) < 0 or smin(simp_sint(sz - o - s)) < 0 for s, (o, sz) in zip(ps, m)):
            raise ValueError(f"invalid pad {_fmt_sint(m)} for {_fmt_sint(ps)}")
          return tuple(sz for _, sz in m)
        case Ops.SHRINK:
          if len(m) != len(ps) or any(smin(o) < 0 or smin(sz) < 0 or smax(simp_sint(o + sz)) > smax(s) for s, (o, sz) in zip(ps, m)):
            raise ValueError(f"invalid shrink {_fmt_sint(m)} for {_fmt_sint(ps)}")
          return tuple(sz for _, sz in m)
  return None

# a shape-like arg as src: one value is itself, several are a STACK
def shape_src(arg: Sequence["sint"]) -> "UOp":
  src = tuple(x if isinstance(x, UOp) else UOp.const(int(x)) for x in arg)
  return src[0] if len(src) == 1 else UOp(Ops.STACK, src)

# ---- symbolic integer (sint = int | UOp) algebra & bounds ----

sint = Union[int, "UOp"]

def _is_var(x: "UOp") -> bool: return x.op is Ops.PARAM and x.arg.vmin_vmax is not None

def _as_linear(x: sint) -> tuple[dict["UOp", int], int] | None:
  """affine integer expressions as ({term: coeff}, const) for exact cancellation"""
  if isinstance(x, int): return {}, x
  if x.op is Ops.CONST and isinstance(x.arg, int) and not isinstance(x.arg, bool): return {}, x.arg
  if _is_var(x): return {x: 1}, 0
  if x.op is Ops.NEG:
    if (a := _as_linear(x.src[0])) is None: return None
    return {k: -v for k, v in a[0].items()}, -a[1]
  if x.op in (Ops.ADD, Ops.SUB):
    a, b = _as_linear(x.src[0]), _as_linear(x.src[1])
    if a is None or b is None: return None
    sign, terms = (1 if x.op is Ops.ADD else -1), dict(a[0])
    for k, v in b[0].items():
      if (nv := terms.get(k, 0) + sign * v) == 0: terms.pop(k, None)
      else: terms[k] = nv
    return terms, a[1] + sign * b[1]
  if x.op is Ops.MUL:
    a, b = _as_linear(x.src[0]), _as_linear(x.src[1])
    if a is None or b is None: return None
    if not a[0]: return {k: v * a[1] for k, v in b[0].items() if v * a[1] != 0}, b[1] * a[1]
    if not b[0]: return {k: v * b[1] for k, v in a[0].items() if v * b[1] != 0}, a[1] * b[1]
  return None

def _from_linear(terms: dict["UOp", int], const: int) -> sint:
  acc: UOp | None = None
  for v, c in sorted(terms.items(), key=lambda kv: kv[0].arg.name):
    piece = v if c == 1 else (-v if c == -1 else v * c)
    acc = piece if acc is None else acc + piece
  if acc is None: return int(const)
  return acc + const if const > 0 else acc - (-const) if const < 0 else acc

def simp_sint(x: sint) -> sint:
  if isinstance(x, int): return x
  if (lin := _as_linear(x)) is not None: return _from_linear(*lin)
  return x

def identity_element(op: Ops, dt: DType) -> Any:
  return dt.const({Ops.ADD: 0, Ops.MUL: 1, Ops.MAX: dt.min}[op])

def _wrapped(dt: DType, lo: Any, hi: Any) -> tuple[Any, Any]:
  return (lo, hi) if (not dt.is_int or dt.is_signed or (0 <= lo and hi <= dt.max)) else (dt.min, dt.max)

def _uop_min_max(u: "UOp") -> tuple[Any, Any]:
  op, src, dt = u.op, u.src, u.dtype
  if op is Ops.CONST:
    v = u.arg
    if v is not Invalid and not (isinstance(v, float) and math.isnan(v)): return v, v
    return dt.min, dt.max
  if op is Ops.PARAM and _is_var(u): return u.arg.vmin_vmax
  if op in (Ops.RANGE, Ops.SPECIAL):
    if dt is dtypes.void or not src or src[0].op is Ops.NOOP: return dt.min, dt.max
    return 0, src[0].vmax - 1
  if op is Ops.NEG:
    lo, hi = src[0]._min_max
    return (-hi, -lo) if dt.is_float else _wrapped(dt, -hi, -lo)
  if op in GroupOp.Binary and not dt.is_float:
    cmp_dt = _promo(src) if op in GroupOp.Comparison else dt
    (s0_vmin, s0_vmax), (s1_vmin, s1_vmax) = src[0]._min_max, src[1]._min_max
    if op is Ops.ADD: return _wrapped(dt, s0_vmin + s1_vmin, s0_vmax + s1_vmax)
    if op is Ops.SUB: return _wrapped(dt, s0_vmin - s1_vmax, s0_vmax - s1_vmin)
    if op is Ops.MUL:
      vals = (s0_vmin * s1_vmin, s0_vmin * s1_vmax, s0_vmax * s1_vmin, s0_vmax * s1_vmax)
      return _wrapped(dt, min(vals), max(vals))
    if op is Ops.SHL and s1_vmin == s1_vmax and isinstance(s0_vmin, int) and isinstance(s1_vmin, int) and s1_vmin >= 0:
      return _wrapped(dt, s0_vmin << s1_vmin, s0_vmax << s1_vmin)
    if op is Ops.SHR and s1_vmin == s1_vmax and isinstance(s0_vmin, int) and isinstance(s1_vmin, int) and s1_vmin >= 0:
      return s0_vmin >> s1_vmin, s0_vmax >> s1_vmin
    if op is Ops.DIV and isinstance(s0_vmin, int) and isinstance(s0_vmax, int) and isinstance(s1_vmin, int) and isinstance(s1_vmax, int):
      if s0_vmin > s0_vmax: return 0, 0
      if s1_vmin * s1_vmax > 0:
        vals = (s0_vmin // s1_vmin, s0_vmin // s1_vmax, s0_vmax // s1_vmin, s0_vmax // s1_vmax)
        return min(vals), max(vals)
    if op is Ops.MOD and isinstance(s0_vmin, int) and isinstance(s0_vmax, int) and isinstance(s1_vmin, int) and isinstance(s1_vmax, int):
      if s0_vmin > s0_vmax: return 0, 0
      if (c := s1_vmin) == s1_vmax > 0: return (s0_vmin % c, s0_vmax % c) if s0_vmin // c == s0_vmax // c else (0, c - 1)
      if (c := s1_vmin) == s1_vmax < 0: return (s0_vmin % c, s0_vmax % c) if s0_vmin // c == s0_vmax // c else (c + 1, 0)
      if s1_vmin > 0: return 0, s1_vmax - 1
      if s1_vmax < 0: return s1_vmin + 1, 0
    if op is Ops.MAX: return max(s0_vmin, s1_vmin), max(s0_vmax, s1_vmax)
    if op is Ops.CMPLT: return (s0_vmax < s1_vmin and not cmp_dt.is_float, s0_vmin < s1_vmax)
    if op is Ops.CMPEQ:
      return (s0_vmin == s0_vmax == s1_vmin == s1_vmax and not cmp_dt.is_float, not ((s0_vmax < s1_vmin) or (s1_vmax < s0_vmin)))
    if op is Ops.CMPNE:
      return ((s0_vmax < s1_vmin or s1_vmax < s0_vmin) and not cmp_dt.is_float, not (s0_vmin == s0_vmax == s1_vmin == s1_vmax and not cmp_dt.is_float))
    if dt is dtypes.bool:
      if op is Ops.AND: return bool(s0_vmin and s1_vmin), bool(s0_vmax and s1_vmax)
      if op is Ops.OR: return bool(s0_vmin or s1_vmin), bool(s0_vmax or s1_vmax)
      if op is Ops.XOR:
        if s1_vmin == s1_vmax: return (not s0_vmax, not s0_vmin) if s1_vmin else (bool(s0_vmin), bool(s0_vmax))
        if s0_vmin == s0_vmax: return (not s1_vmax, not s1_vmin) if s0_vmin else (bool(s1_vmin), bool(s1_vmax))
        return False, True
    if op is Ops.AND and dt.is_int and s1_vmin == s1_vmax and (s0_vmin >= 0 or s1_vmax >= 0):
      return 0, s1_vmax if s0_vmin < 0 else min(s0_vmax, int(s1_vmax) & ((1 << int(s0_vmax).bit_length()) - 1))
    if op is Ops.XOR and s1_vmin == s1_vmax == -1 and isinstance(s0_vmin, int) and isinstance(s0_vmax, int):
      return _wrapped(dt, ~int(s0_vmax), ~int(s0_vmin))
    if op in (Ops.OR, Ops.XOR) and dt.is_int and s0_vmin >= 0 and s1_vmin >= 0:
      return 0, (1 << int(max(s0_vmax, s1_vmax)).bit_length()) - 1
  if op is Ops.WHERE:
    if src[2].is_invalid: return src[1]._min_max
    if src[1].is_invalid: return src[2]._min_max
    if dt.is_int and src[0].op is Ops.CMPLT and src[0].src == src[1:]:
      return min(src[1].vmin, src[2].vmin), min(src[1].vmax, src[2].vmax)
    return min(src[1].vmin, src[2].vmin), max(src[1].vmax, src[2].vmax)
  if op is Ops.STACK and src: return min(x.vmin for x in src), max(x.vmax for x in src)
  if op is Ops.PAD or (op is Ops.INDEX and not all(c.get_valid().op is Ops.CONST and c.get_valid().arg is True for c in src[1:])):
    return min(src[0].vmin, 0), max(src[0].vmax, 0)
  if op in GroupOp.Movement or op in (Ops.INDEX, Ops.STAGE, Ops.AFTER): return src[0]._min_max
  if op is Ops.CAST:
    s0_vmin, s0_vmax = src[0]._min_max
    if dt.is_float:
      if not (isinstance(s0_vmin, float) and math.isnan(s0_vmin)) and not (isinstance(s0_vmax, float) and math.isnan(s0_vmax)):
        return float(s0_vmin), float(s0_vmax)
    elif dt.is_int:
      if isinstance(s0_vmin, (int, float)) and isinstance(s0_vmax, (int, float)) and math.isfinite(s0_vmin) and math.isfinite(s0_vmax):
        lo, hi = int(math.trunc(s0_vmin)), int(math.trunc(s0_vmax))
        if dt.min <= lo and hi <= dt.max: return lo, hi
    elif dt is dtypes.bool:
      return bool(s0_vmin != 0 and s0_vmax != 0 if s0_vmin == s0_vmax else False), bool(not (s0_vmin == 0 and s0_vmax == 0))
  return dt.min, dt.max

def smin(x: sint) -> int: return x if isinstance(x, int) else int(x.vmin)
def smax(x: sint) -> int: return x if isinstance(x, int) else int(x.vmax)

def resolve(x: "UOp | bool", default: bool = True) -> bool:
  if isinstance(x, bool): return x
  assert x.dtype is dtypes.bool, f"resolve expects bool UOp, got {x.dtype}"
  sx = x.simplify()
  return bool(sx.vmin) if sx.vmin == sx.vmax else default

def broadcast_axes(src_shape: tuple[sint, ...], out_shape: tuple[sint, ...]) -> tuple[int, ...]:
  if (nleft := len(out_shape) - len(src_shape)) < 0: raise RuntimeError(f"cannot broadcast {src_shape} into {out_shape}")
  return tuple(range(nleft)) + tuple(
    nleft + i for i, s in enumerate(src_shape)
    if (s == 1 if isinstance(s, int) else resolve(s.eq(1), False)) and (out_shape[nleft + i] != 1 if isinstance(out_shape[nleft + i], int) else resolve(out_shape[nleft + i].ne(1), True))
  )

def sprod(xs: Sequence[sint]) -> sint:
  c, sym = 1, []
  for x in xs:
    if isinstance(sx := simp_sint(x), int): c *= sx
    else: sym.append(sx)
  if c == 0 or not sym: return c
  acc = sym[0]
  for s in sym[1:]: acc = acc * s
  return simp_sint(acc if c == 1 else acc * c)

def sdiv(total: sint, known: sint) -> sint:
  t, k = simp_sint(total), simp_sint(known)
  if isinstance(t, int) and isinstance(k, int):
    if k == 0 or t % k != 0: raise ValueError(f"cannot divide {t} by {k}")
    return t // k
  if isinstance(k, int) and k != 0 and (lin := _as_linear(t)) is not None:
    terms, c = lin
    if c % k == 0 and all(v % k == 0 for v in terms.values()): return _from_linear({u: v // k for u, v in terms.items()}, c // k)
  if t is k: return 1
  raise ValueError(f"cannot symbolically divide {t} by {k}")

def _fmt_sint(x: Any) -> str:
  if isinstance(x, UOp):
    if _is_var(x):
      nm = x.arg.name or f"p{x.arg.slot}"
      return f"{nm}={x.arg.val}" if x.arg.val is not None else nm
    if x.op is Ops.CONST: return repr(x.arg)
    sym = {Ops.ADD: "+", Ops.SUB: "-", Ops.MUL: "*", Ops.DIV: "//"}
    if x.op in sym: return f"({_fmt_sint(x.src[0])}{sym[x.op]}{_fmt_sint(x.src[1])})"
    if x.op is Ops.NEG: return f"(-{_fmt_sint(x.src[0])})"
    return f"<{x.op.name}>"
  if isinstance(x, tuple): return "(" + ", ".join(_fmt_sint(e) for e in x) + ("," if len(x) == 1 else "") + ")"
  return repr(x)

# ---- hash-consed UOp ----

def _arg_key(arg: Any) -> Any:
  # distinguish bool/int/float and keep -0.0 / NaN bit patterns apart in the hash-cons table
  t = type(arg)
  if t is float: return (float, struct.pack("<d", arg))
  return (t, arg)

class _UOpMeta(type):
  _pool: weakref.WeakValueDictionary[tuple, "UOp"] = weakref.WeakValueDictionary()
  def __call__(cls, op: Ops, src: tuple["UOp", ...] = (), arg: Any = None) -> "UOp":
    if not isinstance(src, tuple): src = tuple(src)
    key = (op, src, _arg_key(arg))
    if (hit := cls._pool.get(key)) is not None: return hit
    obj = super().__call__(op, src, arg)
    cls._pool[key] = obj
    return obj

# hash-consed: structurally equal UOps are the same object
class UOp(Mixin, metaclass=_UOpMeta):
  __slots__ = ("op", "src", "arg", "__dict__", "__weakref__")

  @property
  def _uop(self) -> "UOp": return self
  @classmethod
  def _wrap_uop(cls, u: "UOp") -> "UOp": return u

  def __init__(self, op: Ops, src: tuple["UOp", ...] = (), arg: Any = None):
    object.__setattr__(self, "op", op)
    object.__setattr__(self, "src", src)
    object.__setattr__(self, "arg", arg)
  def __setattr__(self, name: str, value: Any): raise AttributeError("UOp is immutable")
  def __reduce__(self): return UOp, (self.op, self.src, self.arg)

  @recursive_property
  def dtype(self) -> DType: return dtype_from_uop(self.op, self.src, self.arg)
  # None for UOps without a tensor shape (Layer 1 tiles, effects, ISA)
  @recursive_property
  def shape(self) -> tuple[sint, ...] | None: return shape_from_uop(self)
  @recursive_property
  def _min_max(self) -> tuple[Any, Any]: return _uop_min_max(self)
  @recursive_property
  def ranges(self) -> frozenset["UOp"]:
    match self.op:
      case Ops.RANGE:
        return frozenset({self}) | (self.src[0].ranges if self.src else frozenset())
      case Ops.END | Ops.REDUCE | Ops.STAGE:
        ended = self.src[1:]
        if not ended: return self.src[0].ranges
        closed = frozenset(r for s in ended for r in ((s,) if s.op is Ops.RANGE else s.ranges))
        bound = frozenset().union(*(r.src[0].ranges for r in closed if r.src)) if closed else frozenset()
        return (self.src[0].ranges - closed) | bound
      case Ops.BACKEDGE:
        return (self.src[0].ranges | self.src[2].ranges) - frozenset({self.src[1]})
      case Ops.CALL:
        return frozenset().union(*(s.ranges for s in self.src[1:])) if len(self.src) > 1 else frozenset()
      case _:
        return frozenset().union(*(s.ranges for s in self.src)) if self.src else frozenset()
  @recursive_property
  def tuplize(self) -> tuple:
    # CONST sorts last so commutative canonicalization puts constants on the right (src[1])
    return (1 if self.op is Ops.CONST else 0, self.op.value, repr(self.arg), self.dtype.name, *(x.tuplize for x in self.src))

  @property
  def ended_ranges(self) -> tuple["UOp", ...]:
    return self.src[1:] if self.op in (Ops.END, Ops.REDUCE, Ops.STAGE) else ()

  def replace(self, **kwargs) -> "UOp":
    op, src, arg = kwargs.pop("op", self.op), kwargs.pop("src", self.src), kwargs.pop("arg", self.arg)
    if kwargs: raise TypeError(f"unexpected replace kwargs: {list(kwargs)}")
    src = tuple(src)
    return self if (op is self.op and src == self.src and _arg_key(arg) == _arg_key(self.arg)) else UOp(op, src, arg)

  # ---- shape-like srcs ----

  @property
  def as_shape(self) -> tuple[sint, ...]:
    if self.op is Ops.CONST: return (self.arg,)
    if self.op is not Ops.STACK: return (simp_sint(self),)
    return tuple(s.arg if s.op is Ops.CONST else simp_sint(s) for s in self.src)

  # the movement arg, read back from src
  @property
  def marg(self) -> tuple:
    match self.op:
      case Ops.RESHAPE | Ops.EXPAND | Ops.PERMUTE: return self.src[1].as_shape
      case Ops.PAD | Ops.SHRINK: return tuple(zip(self.src[1].as_shape, self.src[2].as_shape))
    raise ValueError(f"{self.op} is not a movement op")

  # value of a CONST, or of a CAST(CONST) (a typed constant)
  @property
  def val(self) -> Any:
    if self.op is Ops.CONST: return self.arg
    if self.op is Ops.CAST and self.src[0].op is Ops.CONST: return self.dtype.const(self.src[0].arg)
    raise ValueError(f"val is only for constants, got {self.op}")
  @property
  def is_const(self) -> bool: return self.op is Ops.CONST or (self.op is Ops.CAST and self.src[0].op is Ops.CONST)
  @property
  def is_invalid(self) -> bool: return self.op is Ops.CONST and self.arg is Invalid

  # ---- structure ----

  @property
  def body(self) -> "UOp":
    if self.op is not Ops.CALL: raise ValueError(f"body is only defined on CALL, got {self.op.name}")
    return self.src[0]
  @property
  def src_without_body(self) -> tuple["UOp", ...]: return self.src[1:] if self.op is Ops.CALL else self.src
  @property
  def without_after(self) -> "UOp": return self.src[0].without_after if self.op is Ops.AFTER else self
  @property
  def storage_base(self) -> "UOp":
    u = self
    while u.op in GroupOp.Movement or u.op in (Ops.BITCAST, Ops.AFTER, Ops.INDEX): u = u.src[0]
    return u
  def has_buffer_identity(self, after_ok: bool = True) -> bool:
    return (self.without_after if after_ok else self).op in (Ops.BUFFER, Ops.ALLOC)
  @property
  def is_ins(self) -> bool: return self.op is Ops.CALL and len(self.src) >= 1 and self.src[0].op is Ops.NATIVE
  @property
  def ins_op(self) -> Any: return self.src[0].arg.code if self.is_ins else None
  @property
  def backward_slice(self) -> list["UOp"]:
    res = self.toposort()
    res.pop()
    return res
  def op_in_backward_slice_with_self(self, *ops: Ops) -> bool:
    seen, stack = set(), [self]
    while stack:
      if (x := stack.pop()) in seen: continue
      if x.op in ops: return True
      seen.add(x)
      stack.extend(x.src_without_body)
    return False

  # sources before users; gate(u) == False skips u and its subtree
  def toposort(self, gate: Callable[["UOp"], bool] | None = None, enter_calls: bool = False) -> list["UOp"]:
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
        for s in reversed(node.src if enter_calls else node.src_without_body):
          if s not in seen: stack.append((s, False))
    return order

  def substitute(self, mapping: dict["UOp", "UOp"]) -> "UOp": return substitute(self, mapping)

  # ---- construction ----

  @staticmethod
  def const(val: Any, dtype: DType | str | None = None) -> "UOp":
    """a weak CONST, or CAST(CONST) when dtype is given and isn't the value's own python dtype"""
    if isinstance(val, UOp): return val if dtype is None else val.cast(dtype)
    if val is Invalid: return UOp(Ops.CONST, (), Invalid)
    c = UOp(Ops.CONST, (), val)
    if dtype is None or (dt := dtypes.from_name(dtype)) is c.dtype: return c
    return UOp(Ops.CAST, (UOp(Ops.CONST, (), dt.const(val)),), dt)
  def const_like(self, val: Any, dtype: DType | str | None = None) -> "UOp":
    if val is Invalid: return UOp.invalid()
    dt = self.dtype if dtype is None else dtypes.from_name(dtype)
    return UOp.const(val, None if dt in dtypes.weaks else dt)
  @staticmethod
  def invalid() -> "UOp": return UOp(Ops.CONST, (), Invalid)
  def valid(self, cond: "UOp") -> "UOp": return cond.where(self, UOp.invalid())
  def get_idx(self) -> "UOp":
    if self.op is Ops.STACK: return UOp.stack(*(x.get_idx() for x in self.src))
    return self.src[1] if self.op is Ops.WHERE and self.src[2].is_invalid else self
  def get_valid(self) -> "UOp":
    if self.op is Ops.STACK: return UOp.stack(*(x.get_valid() for x in self.src))
    return self.src[0] if self.op is Ops.WHERE and self.src[2].is_invalid else UOp.const(not self.is_invalid)
  def logical_not(self) -> "UOp": return self ^ True
  def overflows(self, dt: DType) -> bool: return self.vmin < dt.min or dt.max < self.vmax

  def split_uop(self, sep: Ops) -> Iterator["UOp"]:
    stack = [self]
    while stack:
      if (u := stack.pop()).op is sep: stack.extend(reversed(u.src))
      else: yield u
  def pop_const(self, op: Ops = Ops.ADD) -> tuple["UOp", Any]:
    if self.op is op and self.src[1].op is Ops.CONST and not self.src[1].is_invalid: return self.src[0], self.src[1].arg
    return self, identity_element(op, self.dtype)
  def const_factor(self) -> int:
    if self.op is Ops.CONST and isinstance(self.arg, int) and not isinstance(self.arg, bool): return self.arg
    if self.op is Ops.ADD: return math.gcd(self.src[0].const_factor(), self.src[1].const_factor())
    if self.op is Ops.MUL:
      if self.src[0].op is Ops.CONST and isinstance(self.src[0].arg, int): return self.src[0].arg
      if self.src[1].op is Ops.CONST and isinstance(self.src[1].arg, int): return self.src[1].arg
    if self.op is Ops.NEG: return self.src[0].const_factor()
    return 1
  def divides(self, v: int) -> "UOp | None":
    if v == 1: return self
    if self.op is Ops.CONST and isinstance(self.arg, int) and not isinstance(self.arg, bool):
      return self.const_like(self.arg // v) if self.arg % v == 0 else None
    if self.op is Ops.NEG:
      return -d if (d := self.src[0].divides(v)) is not None else None
    if self.op is Ops.ADD:
      return d0 + d1 if (d0 := self.src[0].divides(v)) is not None and (d1 := self.src[1].divides(v)) is not None else None
    if self.op is Ops.MUL:
      if (d0 := self.src[0].divides(v)) is not None: return d0 * self.src[1]
      if (d1 := self.src[1].divides(v)) is not None: return self.src[0] * d1
    return None
  @staticmethod
  def gcd(*uops: "UOp") -> "UOp":
    terms, factors = zip(*(u.pop_const(Ops.MUL) for u in uops))
    count = functools.reduce(operator.and_, [collections.Counter(t.split_uop(Ops.MUL)) for t in terms])
    if not count: factors = tuple(u.const_factor() for u in uops)
    return math.prod(count.elements(), start=uops[0].const_like(math.gcd(*factors)))
  def divide_exact(self, v: "UOp") -> "UOp | None":
    if self is v: return self.const_like(1)
    if v.op is Ops.CONST and isinstance(v.arg, int) and not isinstance(v.arg, bool): return self.divides(v.arg)
    if self.op is Ops.ADD:
      return None if (s0 := self.src[0].divide_exact(v)) is None or (s1 := self.src[1].divide_exact(v)) is None else s0 + s1
    if self.op is Ops.MUL:
      (fac, const), (div_fac, div_const) = self.pop_const(Ops.MUL), v.pop_const(Ops.MUL)
      new_count = collections.Counter(fac.split_uop(Ops.MUL))
      new_count.subtract(div_fac.split_uop(Ops.MUL))
      if div_const != 0 and const % div_const == 0 and all(cnt >= 0 for cnt in new_count.values()):
        return math.prod(new_count.elements(), start=self.const_like(const // div_const))
    return None
  @staticmethod
  def usum(*uops: "UOp") -> "UOp": return functools.reduce(operator.add, uops)
  @staticmethod
  def uprod(*uops: "UOp") -> "UOp": return functools.reduce(operator.mul, uops)
  @staticmethod
  def uand(*uops: "UOp") -> "UOp": return functools.reduce(operator.and_, uops) if uops else UOp.const(True)
  @staticmethod
  def uor(*uops: "UOp") -> "UOp": return functools.reduce(operator.or_, uops) if uops else UOp.const(False)
  def simplify(self) -> "UOp":
    if self.op is Ops.CONST: return self
    from .symbolic import symbolic
    return graph_rewrite(self, symbolic)
  def ssimplify(self) -> Any:
    ret = self.simplify()
    if ret.op is Ops.CONST: return ret.arg
    if ret.op is Ops.CAST and ret.src[0].op is Ops.CONST: return ret.dtype.const(ret.src[0].arg)
    return ret

  @staticmethod
  def noop() -> "UOp": return UOp(Ops.NOOP)
  @staticmethod
  def sink(*srcs: "UOp", arg: Any = None) -> "UOp": return UOp(Ops.SINK, srcs, arg)
  @staticmethod
  def param(slot: int, dtype: DType = dtypes.void, name: str = "", file: str = "", shape: tuple[sint, ...] | int | None = None) -> "UOp":
    if shape is None: return UOp(Ops.PARAM, (), ParamArg(slot, dtype, name, file))
    sh = (shape,) if isinstance(shape, int) else tuple(shape)
    return UOp(Ops.PARAM, (shape_src(sh) if sh else UOp.stack(),), ParamArg(slot, dtype, name, file))
  def param_like(self, slot: int, name: str = "") -> "UOp":
    if self.is_variable:
      return UOp(Ops.PARAM, (), ParamArg(slot, self.dtype, name, vmin_vmax=self.arg.vmin_vmax))
    return UOp.param(slot, self.dtype, name=name, shape=self.shape)
  @staticmethod
  def stack(*srcs: "UOp") -> "UOp": return UOp(Ops.STACK, srcs)
  @staticmethod
  def native(code: Any, src: "UOp | None" = None, dtype: DType | None = None, fmt: bool = False) -> "UOp":
    if dtype is not None:
      assert src is None, "native takes either src or dtype, not both"
      src = UOp.param(-1, dtype)
    return UOp(Ops.NATIVE, (src,) if src is not None else (), NativeInfo(code, fmt))
  def call(self, *srcs: "UOp", role: str = "", name: str = "") -> "UOp": return UOp(Ops.CALL, (self, *srcs), CallInfo(role, name))

  @staticmethod
  def call_with_outputs(values: tuple["UOp", ...], *srcs: "UOp", name: str = "") -> tuple["UOp", ...]:
    """Call a body producing `values`: body stores into trailing output PARAMs, caller passes fresh ALLOCs."""
    slot_to_src = {i: s for i, s in enumerate(srcs)}
    def caller_shape(sh: tuple[sint, ...]) -> tuple[sint, ...]:
      out: list[sint] = []
      for d in sh:
        if isinstance(d, UOp):
          subs = {u: slot_to_src[u.arg.slot] for u in d.toposort() if u.op is Ops.PARAM and u.arg.slot in slot_to_src}
          out.append(simp_sint(d.substitute(subs)) if subs else d)
        else:
          out.append(d)
      return tuple(out)
    allocs = tuple(UOp.alloc(caller_shape(v.shape), v.dtype) for v in values)
    out_params = tuple(v.param_like(len(srcs) + i) for i, v in enumerate(values))
    body = UOp.sink(*(p.store(v) for p, v in zip(out_params, values)))
    call = body.call(*srcs, *allocs, name=name)
    return tuple(a.after(call) for a in allocs)
  def call_with_output(self, *srcs: "UOp", name: str = "") -> "UOp": return UOp.call_with_outputs((self,), *srcs, name=name)[0]

  @staticmethod
  def ins(op: Any, src: tuple["UOp", ...] = (), dtype: DType = dtypes.void, *regs: "UOp", role: str = "") -> "UOp":
    """tinygrad-style machine instruction UOp: CALL(NATIVE(op, regs), *src); its dtype is its first register's"""
    if regs:
      params = [UOp.param(r.arg.slot, dtype, r.arg.name, r.arg.file) if r.op is Ops.PARAM and r.dtype != dtype and dtype is not dtypes.void
                else r for r in regs]
      native_src = params[0].after(*params[1:])
    else:
      native_src = UOp.param(-1, dtype)
    return UOp.native(op, native_src).call(*src, role=role)

  @staticmethod
  def linear(*uops: "UOp", arg: Any = "") -> "UOp": return UOp(Ops.LINEAR, uops, arg)
  @staticmethod
  def source(text: str) -> "UOp": return UOp(Ops.SOURCE, (), text)
  @staticmethod
  def binary(data: bytes) -> "UOp": return UOp(Ops.BINARY, (), data)
  @staticmethod
  def program(*srcs: "UOp", arg: Any = None) -> "UOp": return UOp(Ops.PROGRAM, srcs, arg)

  def after(self, *deps: "UOp") -> "UOp": return UOp(Ops.AFTER, (self, *deps)) if deps else self
  def index(self, *idxs: "UOp | int") -> "UOp": return UOp(Ops.INDEX, (self, *(UOp.const(i) for i in idxs)))
  def stage(self, *ranges: "UOp", removable: bool = True) -> "UOp":
    return UOp(Ops.STAGE, (self, *ranges), StageArg(removable=removable) if ranges else None)
  def backedge(self, loop: "UOp", cond: "UOp") -> "UOp": return UOp(Ops.BACKEDGE, (self, loop, cond))

  # Mixin hooks
  def alu(self, op: Ops, *src: "UOp") -> "UOp": return UOp(op, (self, *src))
  def _mop(self, op: Ops, arg: tuple) -> "UOp":
    if op in (Ops.PAD, Ops.SHRINK): return UOp(op, (self, shape_src([o for o, _ in arg]), shape_src([s for _, s in arg])))
    return UOp(op, (self, shape_src(arg)))

  # ---- symbolic Variables (scalar PARAMs with a value range) ----

  @staticmethod
  def variable(name: str, min_val: int, max_val: int, dtype: DType | str = dtypes.weakint) -> "UOp":
    if min_val > max_val: raise ValueError(f"Variable {name!r}: min_val ({min_val}) > max_val ({max_val})")
    return UOp(Ops.PARAM, (), ParamArg(-1, dtypes.from_name(dtype), name, vmin_vmax=(int(min_val), int(max_val))))
  @property
  def is_variable(self) -> bool: return _is_var(self)
  @property
  def is_bound_var(self) -> bool: return _is_var(self) and self.arg.val is not None
  @property
  def vmin(self) -> Any: return self._min_max[0]
  @property
  def vmax(self) -> Any: return self._min_max[1]
  def bind(self, val: int) -> "UOp":
    if not self.is_variable or self.is_bound_var: raise ValueError("bind() requires an unbound Variable")
    lo, hi = self.arg.vmin_vmax
    if not (lo <= int(val) <= hi): raise ValueError(f"bind({val}) out of range [{lo}, {hi}] for {self.arg.name!r}")
    return self.replace(arg=ParamArg(**{**self.arg.__dict__, "val": int(val)}))
  def unbound(self) -> "UOp": return self.replace(arg=ParamArg(**{**self.arg.__dict__, "val": None}))
  def unbind(self) -> tuple["UOp", int]:
    if not self.is_bound_var: raise ValueError("unbind() requires a bound Variable")
    return self.unbound(), self.arg.val
  def variables(self) -> list["UOp"]:
    return sorted({u.unbound() for u in self.toposort() if _is_var(u)}, key=lambda v: v.arg.name)
  def unbind_all(self) -> tuple["UOp", dict["UOp", int]]:
    bound = {u: u.unbound() for u in self.toposort() if u.is_bound_var}
    vals: dict[UOp, int] = {}
    for u, ub in bound.items():
      if vals.setdefault(ub, u.arg.val) != u.arg.val: raise ValueError(f"conflicting bound values for {ub.arg.name!r}")
    return self.substitute(bound), vals

  # ---- Layer 1 kernel builders ----

  @staticmethod
  def special(end: "UOp | int", name: str) -> "UOp": return UOp(Ops.SPECIAL, (UOp.const(end),), name)
  @staticmethod
  def range(end: "UOp | int", axis: int, name: str = "") -> "UOp": return UOp(Ops.RANGE, (UOp.const(end),), RangeArg(axis, name))
  @staticmethod
  def loop_range(axis: int = 0, name: str = "") -> "UOp":
    """unbounded loop RANGE (paired with BACKEDGE for while/polling loops)"""
    return UOp(Ops.RANGE, (UOp.noop(),), RangeArg(axis, name))
  @staticmethod
  def buffer(name: str, shape: tuple[sint, ...] | int, dtype: DType | str, addr: int | None = None, *, space: str = "dram") -> "UOp":
    sh = (shape,) if isinstance(shape, int) else tuple(shape)
    return UOp(Ops.BUFFER, (shape_src(sh) if sh else UOp.stack(),), BufferArg(name, dtypes.from_name(dtype), addr, space))
  @staticmethod
  def alloc(shape: tuple[sint, ...] | int, dtype: DType | str, name: str | None = None, *,
            addr: int | None = None, space: str = "dram") -> "UOp":
    sh = (shape,) if isinstance(shape, int) else tuple(shape)
    return UOp(Ops.ALLOC, (shape_src(sh) if sh else UOp.stack(),),
               BufferArg(f"a{next(_ALLOC_ID)}" if name is None else name, dtypes.from_name(dtype), addr, space))
  @staticmethod
  def barrier(arg: Any = None) -> "UOp": return UOp(Ops.BARRIER, (), arg)

  def end(self, *ranges: "UOp") -> "UOp":
    if not ranges: raise ValueError("end() requires at least one RANGE")
    return UOp(Ops.END, (self, *ranges))
  def if_(self, body: "UOp", else_body: "UOp | None" = None) -> "UOp":
    if self.dtype is not dtypes.bool: raise TypeError(f"if condition must be bool, got {self.dtype}")
    return UOp(Ops.IF, (self, body) if else_body is None else (self, body, else_body))
  # REDUCE over RANGEs (Layer 1); the Layer 0 form reduces leading axes instead, see Mixin._reduce
  def reduce(self, *ranges: "UOp", op: Ops = Ops.ADD) -> "UOp":
    if not ranges: raise ValueError("reduce() requires at least one RANGE")
    return UOp(Ops.REDUCE, (self, *ranges), (op, 0))

  def load(self, offset: "UOp | int | None" = None, *, gate: "UOp | None" = None) -> "UOp":
    if gate is not None: return UOp(Ops.LOAD, (self, UOp.const(0 if offset is None else offset), gate))
    return UOp(Ops.LOAD, (self,) if offset is None else (self, UOp.const(offset)))
  def store(self, val: "UOp", offset: "UOp | int | None" = None, *, gate: "UOp | None" = None) -> "UOp":
    if gate is not None: return UOp(Ops.STORE, (self, UOp.const(0 if offset is None else offset), val, gate))
    return UOp(Ops.STORE, (self, val) if offset is None else (self, UOp.const(offset), val))

  def __repr__(self) -> str:
    from .uir import render_uir
    return render_uir(self)

Variable = UOp.variable

# ---- pattern matching ----

def _as_tuple(x, cls) -> tuple | None:
  if x is None: return None
  return (x,) if isinstance(x, cls) else tuple(x)

class UPat:
  __slots__ = ("op", "dtype", "arg", "name", "src_mode", "src", "allow_any_len", "is_any", "req_ops")

  def __init__(
    self,
    op: Ops | Sequence[Ops] | set[Ops] | frozenset[Ops] | None = None,
    dtype: DType | Sequence[DType] | None = None,
    src: tuple[UPat, ...] | list[UPat] | UPat | None = None,
    arg: Any = None,
    name: str | None = None,
    allow_any_len: bool = False,
    is_any: bool = False,
  ):
    if name == "ctx": raise ValueError("UPat cannot be named 'ctx'")
    self.op = _as_tuple(op, Ops)
    self.dtype = _as_tuple(dtype, DType)
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
  def var(name: str | None = None, dtype=None) -> UPat: return UPat(dtype=dtype, name=name)
  @staticmethod
  def const(name: str | None = None, dtype=None, arg=None) -> UPat: return UPat(Ops.CONST, dtype=dtype, arg=arg, name=name)
  @staticmethod
  def cvar(name: str | None = None, dtype=None, arg=None) -> UPat:
    return UPat(Ops.CONST, dtype=dtype, arg=(lambda a: a is not Invalid) if arg is None else arg, name=name)
  @staticmethod
  def cval(val: Any, dtype=None, name: str | None = None) -> UPat: return UPat(Ops.CONST, dtype=dtype, arg=val, name=name)
  @staticmethod
  def _p(x: Any) -> UPat: return x if isinstance(x, UPat) else UPat(Ops.CONST, arg=x)

  def or_casted(self, name: str | None = None) -> UPat:
    return UPat.any(self if name is None else self.named(name), UPat(Ops.CAST, src=(self,), name=name))
  def f(self, op: Ops, **kwargs) -> UPat: return UPat(op, src=(self,), **kwargs)
  def cast(self, dtype=None, name: str | None = None) -> UPat: return UPat(Ops.CAST, dtype=dtype, src=(self,), name=name)
  def where(self, a: Any, b: Any, name: str | None = None) -> UPat: return UPat(Ops.WHERE, src=(self, UPat._p(a), UPat._p(b)), name=name)
  def eq(self, x: Any, name: str | None = None) -> UPat: return UPat(Ops.CMPEQ, src=[self, UPat._p(x)], name=name)
  def ne(self, x: Any, name: str | None = None) -> UPat: return UPat(Ops.CMPNE, src=[self, UPat._p(x)], name=name)
  def logical_not(self) -> UPat: return UPat(Ops.XOR, dtype=dtypes.bool, src=[self, UPat.cval(True)])
  def maximum(self, x: Any, name: str | None = None) -> UPat: return UPat(Ops.MAX, src=[self, UPat._p(x)], name=name)
  def reduce(self, *ranges: UPat, op: Ops | None = None, allow_any_len: bool = False, name: str | None = None) -> UPat:
    return UPat(Ops.REDUCE, src=(self, *ranges), arg=(op, 0) if op is not None else None, allow_any_len=allow_any_len, name=name)
  def index(self, *idxs: UPat, allow_any_len: bool = False, name: str | None = None) -> UPat:
    return UPat(Ops.INDEX, src=(self, *idxs), allow_any_len=allow_any_len, name=name)
  def load(self, name: str | None = None, allow_any_len: bool = False) -> UPat:
    return UPat(Ops.LOAD, src=(self,), allow_any_len=allow_any_len, name=name)
  def store(self, val: Any, name: str | None = None) -> UPat: return UPat(Ops.STORE, src=(self, UPat._p(val)), name=name)
  def after(self, *deps: UPat, allow_any_len: bool = False, name: str | None = None) -> UPat:
    return UPat(Ops.AFTER, src=(self, *deps), allow_any_len=allow_any_len, name=name)
  def end(self, *ranges: UPat, allow_any_len: bool = False, name: str | None = None) -> UPat:
    return UPat(Ops.END, src=(self, *ranges), allow_any_len=allow_any_len, name=name)

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

  def __add__(self, x: Any) -> UPat:       return UPat(Ops.ADD, src=[self, UPat._p(x)])
  def __radd__(self, x: Any) -> UPat:      return UPat(Ops.ADD, src=[UPat._p(x), self])
  def __sub__(self, x: Any) -> UPat:       return UPat(Ops.SUB, src=(self, UPat._p(x)))
  def __rsub__(self, x: Any) -> UPat:      return UPat(Ops.SUB, src=(UPat._p(x), self))
  def __mul__(self, x: Any) -> UPat:       return UPat(Ops.MUL, src=[self, UPat._p(x)])
  def __rmul__(self, x: Any) -> UPat:      return UPat(Ops.MUL, src=[UPat._p(x), self])
  def __floordiv__(self, x: Any) -> UPat:  return UPat(Ops.DIV, src=(self, UPat._p(x)))
  def __mod__(self, x: Any) -> UPat:       return UPat(Ops.MOD, src=(self, UPat._p(x)))
  def __lt__(self, x: Any) -> UPat:        return UPat(Ops.CMPLT, src=(self, UPat._p(x)))
  def __and__(self, x: Any) -> UPat:       return UPat(Ops.AND, src=[self, UPat._p(x)])
  def __or__(self, x: Any) -> UPat:        return UPat(Ops.OR, src=[self, UPat._p(x)])
  def __xor__(self, x: Any) -> UPat:       return UPat(Ops.XOR, src=[self, UPat._p(x)])
  def __lshift__(self, x: Any) -> UPat:    return UPat(Ops.SHL, src=(self, UPat._p(x)))
  def __rshift__(self, x: Any) -> UPat:    return UPat(Ops.SHR, src=(self, UPat._p(x)))
  def __neg__(self) -> UPat:               return UPat(Ops.NEG, src=(self,))
  def __invert__(self) -> UPat:            return self.logical_not()

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

class BottomUpGate(Exception):
  """Raised by a bottom-up PatternMatcher rule to stop descending into the current node's srcs."""

class PatternMatcher:
  def __init__(self, rules: Sequence[tuple[UPat, Callable]]):
    self.rules = list(rules)
    self._by_op: dict[Ops | None, list[tuple[Callable, frozenset[Ops]]]] = collections.defaultdict(list)
    for pat, fn in self.rules:
      has_ctx = "ctx" in inspect.signature(fn).parameters
      runner = self._wrap(pat, fn, has_ctx)
      ops = pat.op
      if ops is None and pat.is_any and pat.src and all(a.op is not None for a in pat.src):
        ops = tuple(dict.fromkeys(o for a in pat.src for o in a.op))
      if ops is None:
        self._by_op[None].append((runner, pat.req_ops))
      else:
        for op in ops: self._by_op[op].append((runner, pat.req_ops))

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
    combined = PatternMatcher.__new__(PatternMatcher)
    combined.rules = self.rules + other.rules
    combined._by_op = collections.defaultdict(list, {
      op: self._by_op.get(op, []) + other._by_op.get(op, []) for op in self._by_op.keys() | other._by_op.keys()})
    return combined

  def rewrite(self, u: UOp, ctx: Any = None) -> Any:
    buckets = (self._by_op.get(u.op), self._by_op.get(None))
    if not buckets[0] and not buckets[1]: return None
    if (src_ops := u.__dict__.get("_src_ops")) is None: src_ops = u.__dict__["_src_ops"] = frozenset(s.op for s in u.src)
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
          gated = False
          while nxt is not None:
            if nxt in seen: raise RuntimeError(f"bottom-up rewrite cycle at {nxt.op}")
            seen.add(nxt)
            cur = nxt
            if cur in bot_cache: nxt = bot_cache[cur]
            else:
              try:
                nxt = bot_cache[cur] = bot_pm.rewrite(cur, ctx)
              except BottomUpGate:
                gated = True
                break
          if gated:
            finish(orig, cur)
            continue
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
          nxt = UOp(cur.op, new_src_t, cur.arg)
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
  priorities: dict[UOp, tuple[tuple[int, ...], int, int]] = {}
  range_order = {u: i for i, u in enumerate(lst) if u.op is Ops.RANGE}

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
    priorities[u] = (tuple(sorted(range_order[r] for r in ranges[u])), prio, pos)

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
    memo[u] = u if new_src == u.src else UOp(u.op, new_src, u.arg)
  return memo[root]

