"""Late scalar selection within an already ordered per-core instruction stream."""
from ..uop import Ops, UOp, UPat, PatternMatcher, graph_rewrite
from ..isa import IselContext, vdef
from ..isa.rv32 import RV32Renderer, RVOps, RVGroupOp, X0


def strength_reduce(u):
  if not u.dtype.is_int: return None
  divisor = u.src[1]
  if not divisor.is_const or not isinstance(divisor.val, int) or divisor.val <= 0: return None
  value = divisor.val
  if value & (value - 1): return None
  if u.op is Ops.MUL: return u.src[0] << (value.bit_length() - 1)
  # RISC-V signed division truncates toward zero. A shift/mask is equivalent
  # only for an unsigned or proven nonnegative dividend.
  if u.src[0].dtype.is_signed and u.src[0].vmin < 0: return None
  return u.src[0] >> (value.bit_length() - 1) if u.op is Ops.DIV else u.src[0] & (value - 1)


def select_scalar(stream):
  # Rewrite the container without scheduling it. New instruction operands are
  # expanded locally, preserving every original effect and loop boundary.
  # Effects are already present at their ordered positions. Drop scheduling
  # dependencies from scalar operands so their abstract producers are not
  # recursively selected again. NATIVE register metadata is not traversed.
  dependencies = PatternMatcher([(UPat(Ops.AFTER, name="u"), lambda u: u.src[0]),
                                 (UPat((Ops.DIV, Ops.MOD, Ops.MUL), name="u"), strength_reduce)])
  ordered = graph_rewrite(UOp.linear(*stream), dependencies, bottom_up=True)
  renderer = RV32Renderer()
  rewritten = graph_rewrite(ordered, renderer.isel_matcher, ctx=IselContext(), bottom_up=True)
  # Shared constants must be defined even when their first sender branch is
  # skipped. Only virtual pure materializations move; fixed ABI writes stay.
  constant_ops = {RVOps.LI, RVOps.LUI, RVOps.ADDI, RVOps.SLLI, RVOps.ORI, RVOps.XORI, RVOps.ANDI}
  constant_cache = {}
  def constant(u):
    if u not in constant_cache:
      constant_cache[u] = u.is_const or u is X0 or (u.is_ins and u.ins_op in constant_ops and
                         (vdef(u) is None or renderer.physical_reg(vdef(u)) is None) and
                         all(constant(s) for s in u.src_without_body))
    return constant_cache[u]
  def header_load(u):
    return (u.is_ins and u.ins_op is RVOps.LW and u.src_without_body[0] is X0 and
            u.src_without_body[1].is_const and
            (u.src_without_body[1].val in (0x20, 0x24, 0x28) or 0x80 <= u.src_without_body[1].val < 0x100))
  hoisted = [u for u in rewritten.toposort() if u.is_ins and (constant(u) or header_load(u))]
  hoisted_set = set(hoisted)
  rewritten = UOp.linear(*hoisted, *(u for u in rewritten.src if u not in hoisted_set))
  roots = set(rewritten.src)
  pure_ops = RVGroupOp.RType | RVGroupOp.IType | RVGroupOp.ShiftImm | {RVOps.LI, RVOps.LUI}
  def movable(u):
    return u.is_ins and (u.ins_op in pure_ops or header_load(u)) and (vdef(u) is None or renderer.physical_reg(vdef(u)) is None)
  emitted, out = set(), []
  def dependencies(u):
    for s in u.src_without_body:
      if s in emitted or s in roots and not movable(s): continue
      dependencies(s)
      if s.is_ins:
        out.append(s)
        emitted.add(s)
  for u in rewritten.src:
    if u in emitted and movable(u): continue
    dependencies(u)
    out.append(u)
    emitted.add(u)
  return out
