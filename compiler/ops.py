import math
from typing import Any
from hw import isa
from .uop import CarryArg, DType, GroupOp, Ops, PatternMatcher, ReduceArg, Space, UOp, UPat, dtypes, graph_rewrite

# ---- REDUCE -> LOOP lowering ----

def _reduce_identity(op: Ops, dt: DType) -> UOp:
  match op:
    case Ops.ADD: return UOp.const(dt, 0.0 if dt.is_float else 0)
    case Ops.MUL: return UOp.const(dt, 1.0 if dt.is_float else 1)
    case Ops.MAX:
      if dt.is_float: return UOp.const(dt, -math.inf)
      return UOp.const(dt, -(1 << (dt.bits - 1)) if dt.is_signed else 0)
    case Ops.MIN:
      if dt.is_float: return UOp.const(dt, math.inf)
      return UOp.const(dt, (1 << (dt.bits - 1)) - 1 if dt.is_signed else (1 << dt.bits) - 1)
    case _: raise ValueError(f"unsupported reduce op {op}")


def _reduce_combine(op: Ops, acc: UOp, val: UOp) -> UOp:
  match op:
    case Ops.ADD: return acc + val
    case Ops.MUL: return acc * val
    case Ops.MAX: return acc.maximum(val)
    case Ops.MIN: return acc.minimum(val)
    case _: raise ValueError(f"unsupported reduce op {op}")


def _lower_reduce_node(u: UOp) -> UOp | None:
  arg = u.arg
  if arg.space is Space.L1: return None  # Pack_L1_Acc stays a hardware L1 reduction
  val, *ranges = u.src
  init = _reduce_identity(arg.op, u.dtype)
  def wrap(idx: int, cur_init: UOp) -> UOp:
    r = ranges[idx]
    if idx == len(ranges) - 1:
      (out,) = r.loop((cur_init,), lambda acc: _reduce_combine(arg.op, acc, val), spaces=(arg.space,))
      return out
    (out,) = r.loop((cur_init,), lambda acc: wrap(idx + 1, acc), spaces=(arg.space,))
    return out
  return wrap(0, init)


pm_lower_reduce = PatternMatcher([
  (UPat(Ops.REDUCE, name="u"), _lower_reduce_node),
])


def lower_reduce_to_loop(root: UOp) -> UOp:
  return graph_rewrite(root, pm_lower_reduce)


# ---- Minimal algebraic simplification & constant folding ----

def _eval_const_unary(op: Ops, dt: DType, a: Any) -> UOp | None:
  match op:
    case Ops.NEG: return UOp.const(dt, -a)
    case Ops.ABS: return UOp.const(dt, abs(a))
    case Ops.NOT: return UOp.const(dt, (not a) if dt is dtypes.bool else ~a)
    case Ops.EXP2: return UOp.const(dt, math.exp2(a))
    case Ops.LOG2 if a > 0: return UOp.const(dt, math.log2(a))
    case Ops.SIN: return UOp.const(dt, math.sin(a))
    case Ops.SQRT if a >= 0: return UOp.const(dt, math.sqrt(a))
    case Ops.RSQRT if a > 0: return UOp.const(dt, 1.0 / math.sqrt(a))
    case Ops.RECIP if a != 0: return UOp.const(dt, 1.0 / a)
  return None


def _eval_const_binary(op: Ops, dt: DType, a: Any, b: Any) -> UOp | None:
  match op:
    case Ops.ADD: return UOp.const(dt, a + b)
    case Ops.SUB: return UOp.const(dt, a - b)
    case Ops.MUL: return UOp.const(dt, a * b)
    case Ops.DIV:
      if b == 0: return None
      return UOp.const(dt, a / b if dt.is_float else a // b)
    case Ops.MOD:
      if b == 0: return None
      return UOp.const(dt, a % b)
    case Ops.MAX: return UOp.const(dt, max(a, b))
    case Ops.MIN: return UOp.const(dt, min(a, b))
    case Ops.CMPLT: return UOp.const(dtypes.bool, a < b)
    case Ops.CMPEQ: return UOp.const(dtypes.bool, a == b)
    case Ops.CMPNE: return UOp.const(dtypes.bool, a != b)
    case Ops.AND: return UOp.const(dt, (a and b) if dt is dtypes.bool else (a & b))
    case Ops.OR: return UOp.const(dt, (a or b) if dt is dtypes.bool else (a | b))
    case Ops.XOR: return UOp.const(dt, (a != b) if dt is dtypes.bool else (a ^ b))
    case Ops.SHL: return UOp.const(dt, a << b)
    case Ops.SHR: return UOp.const(dt, a >> b)
  return None


pm_simplify = PatternMatcher([
  # constant folding
  (UPat(GroupOp.Unary, src=(UPat.const("a"),), name="u"), lambda u, a: _eval_const_unary(u.op, u.dtype, a.arg)),
  (UPat(GroupOp.Binary, src=(UPat.const("a"), UPat.const("b")), name="u"), lambda u, a, b: _eval_const_binary(u.op, u.dtype, a.arg, b.arg)),
  (UPat(Ops.CAST, src=(UPat.const("a"),), name="u"), lambda u, a: UOp.const(u.dtype, a.arg) if u.dtype != dtypes.void else None),
  (UPat(Ops.CAST, src=(UPat.var("x"),), name="u"), lambda u, x: x if u.dtype == x.dtype else None),

  # basic identities (float x * 0.0 is NOT folded because of NaN/Inf)
  (UPat(Ops.ADD, src=[UPat.var("x"), UPat.const(arg=0)]), lambda x: x),
  (UPat(Ops.ADD, src=[UPat.var("x"), UPat.const(arg=0.0)]), lambda x: x),
  (UPat(Ops.SUB, src=(UPat.var("x"), UPat.const(arg=0))), lambda x: x),
  (UPat(Ops.SUB, src=(UPat.var("x"), UPat.const(arg=0.0))), lambda x: x),
  (UPat(Ops.SUB, src=(UPat.var("x"), UPat.var("x"))), lambda x: UOp.const(x.dtype, 0) if x.dtype.is_int else None),
  (UPat(Ops.MUL, src=[UPat.var("x"), UPat.const(arg=1)]), lambda x: x),
  (UPat(Ops.MUL, src=[UPat.var("x"), UPat.const(arg=1.0)]), lambda x: x),
  (UPat(Ops.MUL, src=[UPat.var("x"), UPat.const(arg=0)]), lambda x: UOp.const(x.dtype, 0) if x.dtype.is_int else None),
  (UPat(Ops.DIV, src=(UPat.var("x"), UPat.const(arg=1))), lambda x: x),
  (UPat(Ops.DIV, src=(UPat.var("x"), UPat.const(arg=1.0))), lambda x: x),
  (UPat(Ops.MOD, src=(UPat.var("x"), UPat.const(arg=1))), lambda x: UOp.const(x.dtype, 0) if x.dtype.is_int else None),
  (UPat(Ops.NEG, src=(UPat(Ops.NEG, src=(UPat.var("x"),)),)), lambda x: x),
  (UPat(Ops.NOT, src=(UPat(Ops.NOT, src=(UPat.var("x"),)),)), lambda x: x),
  (UPat(Ops.CMPLT, src=(UPat.var("x"), UPat.var("x"))), lambda x: UOp.const(dtypes.bool, False) if x.dtype.is_int else None),

  # where / if folding
  (UPat(Ops.WHERE, src=(UPat.const(arg=True), UPat.var("a"), UPat.var())), lambda a: a),
  (UPat(Ops.WHERE, src=(UPat.const(arg=False), UPat.var(), UPat.var("b"))), lambda b: b),
  (UPat(Ops.WHERE, src=(UPat.var(), UPat.var("a"), UPat.var("a"))), lambda a: a),
  (UPat(Ops.IF, src=(UPat.const(arg=True), UPat.var("body"))), lambda body: body),
  (UPat(Ops.IF, src=(UPat.const(arg=True), UPat.var("body"), UPat.var())), lambda body: body),
  (UPat(Ops.IF, src=(UPat.const(arg=False), UPat.var(), UPat.var("else_body"))), lambda else_body: else_body),
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
      case Ops.LOOP:
        r = u.src[0]
        closed = frozenset({r}) if r.op is Ops.RANGE else frozenset()
        body_ranges = frozenset().union(*(active[s] for s in u.src[1:])) if len(u.src) > 1 else frozenset()
        bound_ranges = active[r.src[0]] if r.op is Ops.RANGE else frozenset()
        active[u] = (body_ranges - closed) | bound_ranges
      case _:
        active[u] = frozenset().union(*(active[s] for s in u.src)) if u.src else frozenset()
  return active


def special_axes(root: UOp) -> set[str]:
  return {u.arg for u in root.toposort() if u.op is Ops.SPECIAL}


# ---- Hardware invariant verifier ----

class VerifyError(ValueError):
  pass


_FPU_ELW_OPS = frozenset({Ops.ADD, Ops.SUB, Ops.MUL, Ops.MAX})


def _check_gate(gate: UOp, op_name: str):
  if gate.dtype is not dtypes.bool or gate.space is not Space.SCALAR:
    raise VerifyError(f"{op_name} gate must be scalar bool, got ({gate.space}, {gate.dtype})")


def verify(root: UOp) -> None:
  nodes = root.toposort()
  active = open_ranges(root)

  for u in nodes:
    op, src, arg = u.op, u.src, u.arg

    match op:
      case Ops.SINK:
        if active[u]:
          names = [r.arg.name or f"axis{r.arg.axis}" for r in active[u]]
          raise VerifyError(f"unclosed RANGE(s) leaked into SINK: {names}")

      case Ops.RANGE | Ops.SPECIAL:
        if len(src) != 1 or src[0].space is not Space.SCALAR or not src[0].dtype.is_int:
          raise VerifyError(f"{op.name} bound must be scalar int, got {src}")

      case Ops.END | Ops.REDUCE:
        if len(src) < 2: raise VerifyError(f"{op.name} requires a value/effect and at least one RANGE")
        for r in src[1:]:
          if r.op is not Ops.RANGE:
            raise VerifyError(f"{op.name} axis argument must be RANGE, got {r.op.name}")
        if op is Ops.REDUCE:
          if not isinstance(arg, ReduceArg): raise VerifyError("REDUCE arg must be ReduceArg")
          if arg.space is Space.L1 and src[0].op is Ops.PACK and not src[0].arg.l1_acc:
            raise VerifyError("L1 REDUCE over PACK requires pack(..., l1_acc=True)")

      case Ops.CARRY:
        if len(src) != 2 or not isinstance(arg, CarryArg) or src[1].op is not Ops.RANGE:
          raise VerifyError(f"CARRY expects (init, RANGE) with CarryArg, got {src}, {arg}")
        if src[1] in active[src[0]]:
          raise VerifyError("CARRY initial value cannot depend on its own RANGE")
        if arg.space not in (Space.DST, Space.LREG, Space.L1, Space.SCALAR):
          raise VerifyError(f"CARRY residency must be DST/LREG/L1/SCALAR, got {arg.space}")

      case Ops.LOOP:
        if len(src) < 3 or (len(src) - 1) % 2 != 0 or src[0].op is not Ops.RANGE:
          raise VerifyError("LOOP expects (RANGE, carry0, next0, ...)")
        r = src[0]
        for i in range(1, len(src), 2):
          c, nxt = src[i], src[i + 1]
          if c.op is not Ops.CARRY or c.src[1] is not r:
            raise VerifyError(f"LOOP carry {i // 2} must be a CARRY bound to the loop RANGE")
          if nxt.dtype != c.dtype:
            raise VerifyError(f"LOOP carry {i // 2} dtype mismatch: {c.dtype} vs {nxt.dtype}")
          ok_space = (
            nxt.space is c.space
            or (c.space is Space.LREG and nxt.space in (Space.DST, Space.SCALAR))
            or (c.space is Space.DST and nxt.space in (Space.LREG, Space.SCALAR))
          )
          if not ok_space:
            raise VerifyError(f"LOOP carry {i // 2} space mismatch: {c.space} vs {nxt.space}")

      case Ops.GET:
        if len(src) != 1 or src[0].op is not Ops.LOOP or not isinstance(arg, int):
          raise VerifyError(f"GET expects (LOOP,) with int index, got {src}, {arg}")
        n_carries = (len(src[0].src) - 1) // 2
        if not (0 <= arg < n_carries):
          raise VerifyError(f"GET index {arg} out of range for LOOP with {n_carries} carries")

      case Ops.IF:
        if len(src) not in (2, 3): raise VerifyError(f"IF expects 2 or 3 srcs, got {len(src)}")
        _check_gate(src[0], "IF")

      case Ops.NOC_READ:
        if len(src) not in (2, 3): raise VerifyError("NOC_READ expects (buf, offset[, gate])")
        if src[0].op not in (Ops.BUFFER, Ops.ALLOC) or src[0].space not in (Space.DRAM, Space.HOST, Space.L1):
          raise VerifyError(f"NOC_READ source must be DRAM/HOST/L1 buffer, got {src[0].op.name} in {src[0].space}")
        if src[1].space is not Space.SCALAR or not src[1].dtype.is_int:
          raise VerifyError(f"NOC_READ offset must be scalar int, got ({src[1].space}, {src[1].dtype})")
        if len(src) == 3: _check_gate(src[2], "NOC_READ")

      case Ops.NOC_WRITE:
        if len(src) not in (3, 4): raise VerifyError("NOC_WRITE expects (buf, offset, val[, gate])")
        if src[0].op not in (Ops.BUFFER, Ops.ALLOC) or src[0].space not in (Space.DRAM, Space.HOST, Space.L1):
          raise VerifyError(f"NOC_WRITE dest must be DRAM/HOST/L1 buffer, got {src[0].op.name} in {src[0].space}")
        if src[1].space is not Space.SCALAR or not src[1].dtype.is_int:
          raise VerifyError(f"NOC_WRITE offset must be scalar int, got ({src[1].space}, {src[1].dtype})")
        if src[2].space not in (Space.L1, Space.SCALAR):
          raise VerifyError(f"NOC_WRITE value must be in L1 or SCALAR, got {src[2].space}")
        if len(src) == 4: _check_gate(src[3], "NOC_WRITE")

      case Ops.NOC_MCAST:
        if len(src) != 2: raise VerifyError("NOC_MCAST expects (val, sender)")
        if src[0].space is not Space.L1:
          raise VerifyError(f"NOC_MCAST value must be in L1, got {src[0].space}")
        if src[1].space is not Space.SCALAR or not (src[1].dtype.is_int or src[1].dtype is dtypes.bool):
          raise VerifyError(f"NOC_MCAST sender must be scalar int/bool, got ({src[1].space}, {src[1].dtype})")

      case Ops.NOC_GATHER | Ops.NOC_ALLGATHER:
        if src[0].space is not Space.L1:
          raise VerifyError(f"{op.name} value must be in L1, got {src[0].space}")

      case Ops.UNPACK:
        if len(src) != 1 or src[0].space is not Space.L1:
          raise VerifyError(f"UNPACK source must be in L1, got {src[0].space if src else None}")
        if arg.dest not in (Space.SRCA, Space.SRCB, Space.DST):
          raise VerifyError(f"UNPACK dest must be SRCA, SRCB, or DST, got {arg.dest}")
        if src[0].dtype is dtypes.fp32 and arg.dest in (Space.SRCA, Space.SRCB) and not arg.allow_tf32:
          raise VerifyError("UNPACK fp32 -> SrcA/SrcB truncates to 19-bit TF32; unpack to Space.DST or set allow_tf32=True")

      case Ops.MVMUL:
        if len(src) != 2: raise VerifyError("MVMUL expects (srcb, srca)")
        if src[0].space is not Space.SRCB or src[1].space is not Space.SRCA:
          raise VerifyError(f"MVMUL expects (SRCB, SRCA), got ({src[0].space}, {src[1].space})")

      case Ops.PACK:
        if len(src) != 1 or src[0].space is not Space.DST:
          raise VerifyError(f"PACK source must be in DST, got {src[0].space if src else None}")

      case Ops.REPLAY:
        if not (1 <= len(arg.insns) <= 32):
          raise VerifyError(f"REPLAY holds 1..32 Tensix instructions, got {len(arg.insns)}")

      case Ops.MOP:
        if len(arg.cfg) != isa.MOP_CFG_WORDS:
          raise VerifyError(f"MOP config requires {isa.MOP_CFG_WORDS} words, got {len(arg.cfg)}")

      case Ops.REDUCE_ROW | Ops.ARGMAX:
        if len(src) != 1 or src[0].space is not Space.DST:
          raise VerifyError(f"{op.name} operand must be in DST, got {src[0].space if src else None}")

      case Ops.REDUCE_LANES:
        if len(src) != 1 or src[0].space not in (Space.DST, Space.LREG):
          raise VerifyError(f"REDUCE_LANES operand must be in DST or LREG, got {src[0].space if src else None}")
        if not (isinstance(arg, tuple) and len(arg) == 2 and arg[0] in (Ops.ADD, Ops.MAX, Ops.MIN) and arg[1] in ("all", "row8")):
          raise VerifyError(f"invalid REDUCE_LANES arg {arg!r}")

      case Ops.SFPU:
        for s in src:
          if s.space not in (Space.DST, Space.LREG, Space.SCALAR):
            raise VerifyError(f"SFPU primitive operand must be in DST/LREG/SCALAR, got {s.space}")

      case _ if op in GroupOp.ALU or op in (Ops.CAST, Ops.BITCAST):
        uses_src_bank = any(s.space in (Space.SRCA, Space.SRCB) for s in src)
        for s in src:
          if s.space not in (Space.DST, Space.LREG, Space.SRCA, Space.SRCB, Space.SCALAR):
            raise VerifyError(f"{op.name} operand must be in DST/LREG/SRCA/SRCB/SCALAR, got {s.space} (missing unpack()?)")
        if uses_src_bank and op not in _FPU_ELW_OPS:
          raise VerifyError(f"SRCA/SRCB operands only support FPU elementwise {_FPU_ELW_OPS}, got {op.name}")
        if op is Ops.WHERE and src[0].dtype is not dtypes.bool:
          raise VerifyError(f"WHERE condition must be bool, got {src[0].dtype}")

      case Ops.LOAD:
        if len(src) not in (1, 2, 3) or src[0].op not in (Ops.BUFFER, Ops.ALLOC):
          raise VerifyError(f"LOAD target must be BUFFER or ALLOC, got {src}")
        if len(src) >= 2 and (src[1].space is not Space.SCALAR or not src[1].dtype.is_int):
          raise VerifyError(f"LOAD offset must be scalar int, got ({src[1].space}, {src[1].dtype})")
        if len(src) == 3: _check_gate(src[2], "LOAD")

      case Ops.STORE:
        if len(src) not in (2, 3, 4) or src[0].op not in (Ops.BUFFER, Ops.ALLOC):
          raise VerifyError(f"STORE target must be BUFFER or ALLOC, got {src}")
        val = src[1] if len(src) == 2 else src[2]
        if len(src) >= 3 and (src[1].space is not Space.SCALAR or not src[1].dtype.is_int):
          raise VerifyError(f"STORE offset must be scalar int, got ({src[1].space}, {src[1].dtype})")
        if len(src) == 4: _check_gate(src[3], "STORE")
        if src[0].space in (Space.DST, Space.LREG, Space.L1, Space.SCALAR) and val.space is not src[0].space:
          raise VerifyError(f"STORE into {src[0].space} requires value in {src[0].space}, got {val.space}")
