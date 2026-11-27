import collections, itertools
from typing import Any
from ..dtype import DType, dtypes
from ..uir import render_uir
from ..uop import Ops, PatternMatcher, UOp, graph_rewrite, line_rewrite, linearize

# ---- Tinygrad-style virtual/physical register metadata on UOp.ins ----

def vreg(slot: int, dtype: DType, choices: tuple[UOp, ...], name: str = "vreg") -> tuple[UOp, ...]:
  return UOp.param(slot, dtype, name=name, file=choices[0].arg.file), UOp.stack(*choices)

class IselContext:
  def __init__(self, start: int = 0): self.reg_n = itertools.count(start)
  def vreg(self, dtype: DType, choices: tuple[UOp, ...], name: str = "vreg") -> tuple[UOp, ...]:
    return vreg(next(self.reg_n), dtype, choices, name=name)

def _is_reg(u: UOp) -> bool: return u.op is Ops.PARAM and u.arg.file != "" and u.arg.slot >= 0

def regs(u: UOp) -> tuple[UOp, ...]:
  """Return the register metadata attached to a UOp.ins (from NATIVE.src[0])."""
  if not u.is_ins or not u.body.src: return ()
  s = u.body.src[0]
  return s.src if s.op is Ops.AFTER else (s,)

def vdef(u: UOp) -> UOp | None:
  """Return the primary virtual/physical register defined by u, if any."""
  if u.op in (Ops.AFTER, Ops.BITCAST, Ops.CAST): return vdef(u.src[0])
  if _is_reg(u): return u
  operands = regs(u)
  if operands and _is_reg(operands[0]):
    return operands[0]
  return None

def rdef(u: UOp, ren: "ISARenderer") -> UOp | None:
  return ren.physical_reg(p) if (p := vdef(u)) is not None else None

def register_choices(u: UOp, ren: "ISARenderer") -> dict[UOp, tuple[UOp, ...]]:
  operands = regs(u)
  out: dict[UOp, tuple[UOp, ...]] = {}
  for i, p in enumerate(operands):
    if _is_reg(p):
      if (r := ren.physical_reg(p)) is not None:
        out[p] = (r,)
      elif i + 1 < len(operands) and operands[i + 1].op is Ops.STACK:
        out[p] = operands[i + 1].src
  return out

# ---- Generic ISARenderer & LinearContext (decoupled from x86) ----

class LinearContext:
  def __init__(self, ren: "ISARenderer"):
    self.ren = ren
    self.stack_size = 0
    self.vreg_n = itertools.count(1_000_000)
  def vreg(self, dtype: DType, choices: tuple[UOp, ...], name: str = "vreg") -> tuple[UOp, ...]:
    return vreg(next(self.vreg_n), dtype, choices, name=name)
  def insert_linearized(self, uops: list[UOp]) -> list[UOp]: return uops
  def assign_spill_slot(self, r: UOp) -> int:
    slot = self.stack_size
    self.stack_size += 4
    return slot

class ISARenderer:
  pre_isel_matcher: PatternMatcher = PatternMatcher([])
  isel_matcher: PatternMatcher = PatternMatcher([])
  pre_regalloc_matcher: PatternMatcher = PatternMatcher([])
  post_regalloc_matcher: PatternMatcher = PatternMatcher([])
  linear_ctx_type: type[LinearContext] = LinearContext
  physical_regs: frozenset[UOp] = frozenset()
  scratch_regs: tuple[UOp, ...] = ()

  def physical_reg(self, u: UOp) -> UOp | None:
    if u.op is not Ops.PARAM: return None
    for r in self.physical_regs:
      if r.arg.file == u.arg.file and r.arg.slot == u.arg.slot and r.arg.name == u.arg.name:
        return r
    return None

  def spill_choices(self, choices): return self.scratch_regs

  def is_label(self, u: UOp) -> bool: return False
  def label_key(self, u: UOp) -> UOp | None: return u.src[1] if self.is_label(u) and len(u.src) > 1 else None
  def jump_targets(self, u: UOp) -> tuple[UOp, ...]: return ()
  def falls_through(self, u: UOp) -> bool: return True
  def is_two_address(self, u: UOp) -> bool: return False
  def copy(self, x: UOp, reg: UOp) -> UOp: raise NotImplementedError
  def spill(self, spill_slot: int, x: UOp) -> UOp: raise NotImplementedError
  def fill(self, spill_slot: int, x: UOp, reg: UOp) -> UOp: raise NotImplementedError
  def assemble(self, uops: list[UOp]) -> bytes: raise NotImplementedError

# ---- CFG-aware Graph-Coloring Register Allocator (handles while/polling loops & if/else) ----

def regalloc(ctx: LinearContext, uops: list[UOp], ren: ISARenderer) -> list[UOp]:
  """Allocate virtual registers in a linearized list[UOp] using exact CFG liveness + graph coloring."""
  n = len(uops)
  label_pc: dict[UOp, int] = {}
  for pc, u in enumerate(uops):
    if (k := ren.label_key(u)) is not None:
      label_pc[k] = pc

  # 1. Per-instruction virtual reads, defs, choices, and CFG edges
  defs_at: list[dict[UOp, tuple[UOp, ...]]] = [register_choices(u, ren) for u in uops]
  choices: dict[UOp, tuple[UOp, ...]] = {}
  for d in defs_at: choices.update(d)
  virtuals = {v for v, cs in choices.items() if ren.physical_reg(v) is None}
  if not virtuals: return uops

  reads: list[set[UOp]] = []
  writes: list[set[UOp]] = []
  fixed_reads: list[set[UOp]] = []
  fixed_writes: list[set[UOp]] = []
  succs: list[list[int]] = []
  preds: dict[int, list[int]] = collections.defaultdict(list)

  for pc, u in enumerate(uops):
    rset: set[UOp] = set()
    for s in u.src_without_body:
      if (v := vdef(s)) is not None and v in virtuals: rset.add(v)
    wset = {v for v in defs_at[pc] if v in virtuals}
    reads.append(rset)
    writes.append(wset)
    fixed_reads.append({r for s in u.src_without_body if (r := rdef(s, ren)) is not None})
    fixed_writes.append({r for p in defs_at[pc] if (r := ren.physical_reg(p)) is not None})

    nxt: list[int] = []
    if ren.falls_through(u) and pc + 1 < n: nxt.append(pc + 1)
    for tgt in ren.jump_targets(u):
      if tgt in label_pc: nxt.append(label_pc[tgt])
    succs.append(nxt)
    for s_pc in nxt: preds[s_pc].append(pc)

  # 2. Backward dataflow liveness
  live_in: list[set[UOp]] = [set() for _ in range(n)]
  live_out: list[set[UOp]] = [set() for _ in range(n)]
  fixed_in: list[set[UOp]] = [set() for _ in range(n)]
  fixed_out: list[set[UOp]] = [set() for _ in range(n)]
  work = collections.deque(reversed(range(n)))
  in_work = set(range(n))
  while work:
    pc = work.popleft()
    in_work.discard(pc)
    out_s = set().union(*(live_in[s] for s in succs[pc])) if succs[pc] else set()
    in_s = reads[pc] | (out_s - writes[pc])
    out_fixed = set().union(*(fixed_in[s] for s in succs[pc])) if succs[pc] else set()
    in_fixed = fixed_reads[pc] | (out_fixed - fixed_writes[pc])
    fixed_out[pc] = out_fixed
    live_out[pc] = out_s
    if in_s != live_in[pc] or in_fixed != fixed_in[pc]:
      live_in[pc] = in_s
      fixed_in[pc] = in_fixed
      for p in preds[pc]:
        if p not in in_work:
          in_work.add(p)
          work.append(p)

  # 3. Interference graph (+ physical register clobbers at each def)
  neighbors: dict[UOp, set[UOp]] = {v: set() for v in virtuals}
  fixed_conflict: dict[UOp, set[UOp]] = {v: set() for v in virtuals}
  for pc in range(n):
    live_after = live_out[pc]
    # Explicit physical operands have live ranges too (e.g. SFPTRANSP's
    # L0..L7 outputs). A virtual definition must not overwrite one whose next
    # read is still ahead, even when that physical register has no later def.
    for v in live_after | writes[pc]: fixed_conflict[v].update(fixed_out[pc])
    for w in writes[pc]:
      for other in (live_after | writes[pc]) - {w}:
        neighbors[w].add(other)
        neighbors[other].add(w)
    # Fixed physical defs at pc conflict with any virtual live across pc
    fixed_defs = {ren.physical_reg(p) for p in defs_at[pc] if ren.physical_reg(p) is not None}
    for fd in fixed_defs:
      if fd is not None:
        for v in live_after: fixed_conflict[v].add(fd)

  # 4. Greedy coloring (most constrained first; prefer first choice in pool)
  order = sorted(virtuals, key=lambda v: (len(choices[v]), -len(neighbors[v]), v.arg.slot))

  def try_color(exclude: set[UOp]) -> dict[UOp, UOp | None]:
    col: dict[UOp, UOp | None] = {}
    for v in order:
      used = {col[nb] for nb in neighbors[v] if nb in col and col[nb] is not None} | fixed_conflict[v] | exclude
      col[v] = next((r for r in choices[v] if r not in used), None)
    return col

  colors = try_color(set())
  spills: dict[UOp, int] = {}
  scratch: tuple[UOp, ...] = ()
  if any(r is None for r in colors.values()):
    if len(ren.scratch_regs) < 2:
      raise RuntimeError("register allocation failed: out of registers and no scratch_regs configured for spilling")
    scratch = ren.scratch_regs
    colors = try_color(set(scratch))
    spill_pools: dict[str, list[int]] = collections.defaultdict(list)
    for v in order:
      if colors[v] is None:
        # Non-overlapping spilled values share storage just as they could
        # share a register. This bounds SFPU scratch by peak live pressure,
        # rather than the number of temporaries in a long fused expression.
        occupied = {spills[n] for n in neighbors[v] if n in spills}
        pool = spill_pools[choices[v][0].arg.file]
        slot = next((s for s in pool if s not in occupied), None)
        if slot is None:
          slot = ctx.assign_spill_slot(choices[v][0])
          pool.append(slot)
        spills[v] = slot

  # 5. Rewrite UOps with allocated physical registers (inserting fills/spills for spilled virtuals)
  out_uops: list[UOp] = []
  replaced: dict[UOp, UOp] = {}

  for pc, u in enumerate(uops):
    before: list[UOp] = []
    after: list[UOp] = []
    loaded: dict[UOp, UOp] = {}

    nsrc: list[UOp] = []
    for s in u.src_without_body:
      v = vdef(s)
      if v is not None and v in virtuals:
        if v in spills:
          if v not in loaded:
            if len(loaded) >= len(scratch): raise RuntimeError("instruction needs more spill scratch registers")
            busy = fixed_in[pc] | fixed_out[pc] | {rdef(x, ren) for x in loaded.values()}
            sc = next((r for r in scratch if r not in busy), None)
            if sc is None: raise RuntimeError("no free scratch for spilled operand")
            fill_u = ren.fill(spills[v], s, sc)
            before.append(fill_u)
            loaded[v] = fill_u
          nsrc.append(loaded[v].cast(s.dtype) if loaded[v].dtype != s.dtype else loaded[v])
        else:
          phys = colors[v]
          assert phys is not None
          nsrc.append(phys if phys.dtype == s.dtype else phys.cast(s.dtype))
      else:
        nsrc.append(s if (ren.is_label(u) or s in label_pc) else replaced.get(s, s))

    u_defs = list(defs_at[pc])
    if u.is_ins and u_defs:
      phys_defs: list[UOp] = []
      spilled_def: tuple[UOp, UOp] | None = None
      for v in u_defs:
        if v in virtuals:
          if v in spills:
            sc = rdef(loaded[v], ren) if v in loaded else next(
              (r for r in ren.spill_choices(choices[v]) if r not in fixed_out[pc] | fixed_reads[pc]), None)
            if sc is None: raise RuntimeError("no compatible scratch for spilled definition")
            phys_defs.append(sc)
            spilled_def = (v, sc)
          else:
            p = colors[v]
            assert p is not None
            phys_defs.append(p)
        else:
          phys_defs.append(v)
      role = u.arg.role if hasattr(u.arg, "role") else ""
      nu = UOp.ins(u.ins_op, tuple(nsrc), u.dtype, *phys_defs, role=role)
      if spilled_def is not None:
        after.append(ren.spill(spills[spilled_def[0]], nu))
    elif u.op is Ops.CALL:
      nu = u.replace(src=(u.src[0], *nsrc))
    else:
      nu = u.replace(src=tuple(nsrc))

    replaced[u] = nu
    out_uops.extend(before)
    out_uops.append(nu)
    out_uops.extend(after)

  return out_uops

# ---- End-to-end ISARenderer driver (mini to_program) ----

def compile_linear(lst: list[UOp], ren: ISARenderer, *, name: str = "") -> tuple[list[UOp], bytes]:
  lin_ctx = ren.linear_ctx_type(ren)
  lst = line_rewrite(lst, ren.pre_regalloc_matcher, lin_ctx)
  lst = regalloc(lin_ctx, lst, ren)
  lst = lin_ctx.insert_linearized(lst)
  lst = line_rewrite(lst, ren.post_regalloc_matcher, lin_ctx)
  return lst, ren.assemble(lst)

def to_program(sink: UOp, ren: ISARenderer) -> UOp:
  """Compile a UOp SINK through pre_isel -> isel -> linearize -> regalloc -> assemble -> PROGRAM."""
  s = graph_rewrite(sink, ren.pre_isel_matcher, ctx=itertools.count(-1, -1), bottom_up=True)
  s = graph_rewrite(s, ren.isel_matcher, ctx=IselContext(), bottom_up=True)
  lst = linearize(s)
  lst, binary = compile_linear(lst, ren)
  lin = UOp.linear(*lst, arg=sink.arg.name if hasattr(sink.arg, "name") else "")
  return UOp.program(sink, lin, UOp.source(render_uir(lst)), UOp.binary(binary), arg=sink.arg)
