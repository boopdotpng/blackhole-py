import math
from typing import Any
from .dtype import DType, can_lossless_cast, dtypes
from .uop import GroupOp, Ops, PatternMatcher, UOp, UPat, graph_rewrite

# ---- constant folding & algebraic simplification ----

# python value of an ALU op on constants, None if it can't be folded exactly
def exec_alu(op: Ops, dt: DType, *v: Any) -> Any:
  match op, v:
    case Ops.NEG, (a,): return -a
    case Ops.EXP2, (a,): return math.exp2(a)
    case Ops.LOG2, (a,) if a > 0: return math.log2(a)
    case Ops.SIN, (a,): return math.sin(a)
    case Ops.SQRT, (a,) if a >= 0: return math.sqrt(a)
    case Ops.RECIP, (a,) if a != 0: return 1.0 / a
    case Ops.ADD, (a, b): return a + b
    case Ops.SUB, (a, b): return a - b
    case Ops.MUL, (a, b): return a * b
    case Ops.DIV, (a, b) if b != 0: return a / b if dt.is_float else int(a) // int(b)
    case Ops.MOD, (a, b) if b != 0: return a % b
    case Ops.MAX, (a, b): return max(a, b)
    case Ops.CMPLT, (a, b): return a < b
    case Ops.CMPEQ, (a, b): return a == b
    case Ops.CMPNE, (a, b): return a != b
    case Ops.AND, (a, b): return (a and b) if dt is dtypes.bool else int(a) & int(b)
    case Ops.OR, (a, b): return (a or b) if dt is dtypes.bool else int(a) | int(b)
    case Ops.XOR, (a, b): return (a != b) if dt is dtypes.bool else int(a) ^ int(b)
    case Ops.SHL, (a, b): return int(a) << int(b)
    case Ops.SHR, (a, b): return int(a) >> int(b)
    case Ops.WHERE, (c, a, b): return a if c else b
    case Ops.MULACC, (a, b, c): return a * b + c
  return None

def _fold(u: UOp) -> UOp | None:
  if not all(s.is_const for s in u.src): return None
  return None if (v := exec_alu(u.op, u.dtype, *(s.val for s in u.src))) is None else UOp.const(v, u.dtype)

def _is(c: UOp, v: Any) -> bool: return c.is_const and c.val == v and type(c.val) is not bool

def _const_like_op(val: Any, c: UOp) -> UOp:
  return UOp.const(val, None if c.dtype in dtypes.weaks else c.dtype)

def _fold_mul_consts(u: UOp, x: UOp, c1: UOp, c2: UOp) -> UOp | None:
  if not (c1.is_const and c2.is_const): return None
  prod = c1.val * c2.val
  if u.dtype.is_float and (not math.isfinite(prod) or prod == 0): return None
  return x * _const_like_op(prod, c2 if c1.dtype in dtypes.weaks else c1)

def _fold_add_consts(u: UOp, x: UOp, c1: UOp, c2: UOp) -> UOp | None:
  if u.dtype.is_float or not (c1.is_const and c2.is_const): return None
  return x + _const_like_op(c1.val + c2.val, c2 if c1.dtype in dtypes.weaks else c1)

def _fold_div_const(u: UOp, x: UOp, c: UOp) -> UOp | None:
  if not (u.dtype.is_float and c.is_const and c.val != 0 and type(c.val) is not bool): return None
  inv = 1.0 / float(c.val)
  if not math.isfinite(inv): return None
  return x * _const_like_op(inv, c)

def _fold_where(c: UOp, a: UOp, b: UOp) -> UOp | None:
  if a is b: return a
  if c.is_const: return a if c.val else b
  if a.is_const and b.is_const and a.dtype is dtypes.bool and b.dtype is dtypes.bool:
    if a.val is True and b.val is False: return c
    if a.val is False and b.val is True: return ~c
  return None

pm_simplify = PatternMatcher([
  # constant folding (a CONST is weak; CAST(CONST) is a typed constant)
  (UPat(GroupOp.ALU, name="u"), _fold),
  (UPat(Ops.CAST, src=(UPat(Ops.CAST, src=(UPat(Ops.CONST, name="c"),), name="mid"),), name="u"),
   lambda u, mid, c: UOp.const(c.arg, u.dtype) if can_lossless_cast(mid.dtype, u.dtype) or mid.dtype in dtypes.weaks else None),
  (UPat((Ops.CAST, Ops.BITCAST), src=(UPat.var("x"),), name="u"), lambda u, x: x if u.dtype == x.dtype else None),
  (UPat(Ops.CAST, src=(UPat(Ops.CAST, src=(UPat.var("x"),), name="mid"),), name="u"),
   lambda u, mid, x: x if u.dtype == x.dtype and can_lossless_cast(x.dtype, mid.dtype) else None),
  (UPat(Ops.BITCAST, src=(UPat(Ops.BITCAST, src=(UPat.var("x"),)),), name="u"), lambda u, x: x.bitcast(u.dtype)),

  # identities (float x * 0 is not folded because of NaN/Inf)
  (UPat((Ops.ADD, Ops.SUB, Ops.OR, Ops.XOR, Ops.SHL, Ops.SHR), src=(UPat.var("x"), UPat.var("c"))), lambda x, c: x if _is(c, 0) else None),
  (UPat((Ops.ADD, Ops.OR, Ops.XOR), src=(UPat.var("c"), UPat.var("x"))), lambda x, c: x if _is(c, 0) else None),
  (UPat(Ops.SUB, src=(UPat.var("c"), UPat.var("x"))), lambda c, x: -x if _is(c, 0) else None),
  (UPat(Ops.MUL, src=[UPat.var("x"), UPat.var("c")]), lambda x, c: x if _is(c, 1) else None),
  (UPat(Ops.MUL, src=[UPat.var("x"), UPat.var("c")], name="u"),
   lambda u, x, c: -x if _is(c, -1) and u.dtype.is_signed else (UOp.const(0, u.dtype) if _is(c, 0) and not u.dtype.is_float else None)),
  (UPat(Ops.AND, src=[UPat.var("x"), UPat.var("c")], name="u"), lambda u, x, c: UOp.const(0, u.dtype) if _is(c, 0) else None),
  (UPat(Ops.DIV, src=(UPat.var("x"), UPat.var("c")), name="u"),
   lambda u, x, c: x if _is(c, 1) else (-x if _is(c, -1) and u.dtype.is_int and u.dtype.is_signed else _fold_div_const(u, x, c))),
  (UPat(Ops.DIV, src=(UPat.var("c"), UPat.var("x")), name="u"), lambda u, c, x: x.recip() if u.dtype.is_float and _is(c, 1) else None),

  # self-folding & signs
  (UPat(GroupOp.Idempotent, src=(UPat.var("x"), UPat.var("x"))), lambda x: x),
  (UPat((Ops.SUB, Ops.XOR, Ops.MOD), src=(UPat.var("x"), UPat.var("x")), name="u"),
   lambda u, x: UOp.const(0, u.dtype) if not u.dtype.is_float else None),
  (UPat(Ops.NEG, src=(UPat(Ops.NEG, src=(UPat.var("x"),)),)), lambda x: x),
  (UPat(Ops.XOR, src=[UPat(Ops.XOR, src=[UPat.var("x"), UPat.var("y")]), UPat.var("y")]), lambda x, y: x),
  (UPat(Ops.ADD, src=[UPat.var("a"), UPat(Ops.NEG, src=(UPat.var("b"),))]), lambda a, b: a - b),
  (UPat(Ops.SUB, src=(UPat.var("a"), UPat(Ops.NEG, src=(UPat.var("b"),)))), lambda a, b: a + b),
  (UPat(Ops.MUL, src=(UPat(Ops.NEG, src=(UPat.var("x"),)), UPat(Ops.NEG, src=(UPat.var("y"),)))), lambda x, y: x * y),
  (UPat(Ops.MUL, src=[UPat(Ops.NEG, src=(UPat.var("x"),)), UPat.var("c")]),
   lambda x, c: x * _const_like_op(-c.val, c) if c.is_const and type(c.val) is not bool else None),

  # two-stage constant folding
  (UPat(Ops.MUL, src=[UPat(Ops.MUL, src=[UPat.var("x"), UPat.var("c1")]), UPat.var("c2")], name="u"), _fold_mul_consts),
  (UPat(Ops.ADD, src=[UPat(Ops.ADD, src=[UPat.var("x"), UPat.var("c1")]), UPat.var("c2")], name="u"), _fold_add_consts),

  # bool & control
  (UPat(Ops.AND, dtype=dtypes.bool, src=[UPat.var("x"), UPat.var("c")]), lambda x, c: (x if c.val else c) if c.is_const else None),
  (UPat(Ops.OR, dtype=dtypes.bool, src=[UPat.var("x"), UPat.var("c")]), lambda x, c: (c if c.val else x) if c.is_const else None),
  (UPat(Ops.CMPEQ, src=[UPat.var("x", dtype=dtypes.bool), UPat.var("c")]), lambda x, c: x if c.is_const and c.val is True else None),
  (UPat(Ops.WHERE, src=(UPat.var("c"), UPat.var("a"), UPat.var("b"))), _fold_where),
  (UPat(Ops.IF, src=(UPat.var("c"), UPat.var("body")), allow_any_len=True, name="u"),
   lambda u, c, body: (body if c.val else (u.src[2] if len(u.src) == 3 else None)) if c.is_const else None),
])

def simplify(root: UOp) -> UOp:
  return graph_rewrite(root, pm_simplify)

# ---- Analysis helpers ----

def open_ranges(root: UOp) -> dict[UOp, frozenset[UOp]]:
  active: dict[UOp, frozenset[UOp]] = {}
  for u in root.toposort():
    match u.op:
      case Ops.RANGE:
        active[u] = frozenset({u}) | active[u.src[0]]
      case Ops.END | Ops.REDUCE:
        closed = frozenset(u.src[1:])
        active[u] = (active[u.src[0]] - closed) | frozenset().union(*(active[r.src[0]] for r in u.src[1:] if r.op is Ops.RANGE))
      case _:
        active[u] = frozenset().union(*(active[s] for s in u.src)) if u.src else frozenset()
  return active

def special_axes(root: UOp) -> set[str]:
  return {u.arg for u in root.toposort() if u.op is Ops.SPECIAL}

# ---- Layer 1 verifier (generic loop/kernel IR structure) ----

class VerifyError(ValueError):
  pass

def _check_gate(gate: UOp, op_name: str):
  if gate.dtype is not dtypes.bool: raise VerifyError(f"{op_name} gate must be bool, got {gate.dtype}")

def _check_int(u: UOp, what: str):
  if not u.dtype.is_int: raise VerifyError(f"{what} must be an integer, got {u.dtype}")

def verify(root: UOp) -> None:
  active = open_ranges(root)
  for u in root.toposort():
    op, src = u.op, u.src
    if op in GroupOp.Movement or op is Ops.STAGE or (op is Ops.REDUCE and len(src) == 1):
      raise VerifyError(f"Layer 0 tensor op {op.name} must be lowered before Layer 1 verify()")
    if op not in (Ops.BUFFER, Ops.ALLOC, Ops.STACK, Ops.PARAM) and u.shape not in (None, ()):
      raise VerifyError(f"Layer 0 tensor value {op.name} {u.shape} must be lowered before Layer 1 verify()")
    match op:
      case Ops.SINK:
        if active[u]: raise VerifyError(f"unclosed RANGE(s) leaked into SINK: {[r.arg.name or f'axis{r.arg.axis}' for r in active[u]]}")
      case Ops.RANGE | Ops.SPECIAL:
        if len(src) != 1: raise VerifyError(f"{op.name} takes one bound")
        _check_int(src[0], f"{op.name} bound")
      case Ops.END | Ops.REDUCE:
        if len(src) < 2 or any(r.op is not Ops.RANGE for r in src[1:]):
          raise VerifyError(f"{op.name} requires a value/effect followed by RANGEs")
      case Ops.IF:
        if len(src) not in (2, 3): raise VerifyError(f"IF expects 2 or 3 srcs, got {len(src)}")
        _check_gate(src[0], "IF")
      case Ops.WHERE:
        if src[0].dtype is not dtypes.bool: raise VerifyError(f"WHERE condition must be bool, got {src[0].dtype}")
      case Ops.LOAD | Ops.STORE:
        if src[0].op not in (Ops.BUFFER, Ops.ALLOC, Ops.PARAM, Ops.INDEX):
          raise VerifyError(f"{op.name} target must be BUFFER, ALLOC, PARAM or INDEX, got {src[0].op.name}")
        if op is Ops.LOAD and len(src) >= 2: _check_int(src[1], "LOAD offset")
        if op is Ops.LOAD and len(src) == 3: _check_gate(src[2], "LOAD")
        if op is Ops.STORE and len(src) >= 3: _check_int(src[1], "STORE offset")
        if op is Ops.STORE and len(src) == 4: _check_gate(src[3], "STORE")
