import functools, itertools, math
from dataclasses import dataclass, field
from .dtype import Invalid, dtypes
from .symbolic import pm_data_invalid, pm_drop_and_clauses, pm_move_where_on_load, pm_remove_invalid, pm_simplify_valid, sym, symbolic
from .uop import (
  BottomUpGate, GroupOp, KernelArg, Ops, ParamArg, PatternMatcher, RangeArg, StageArg, UOp, UPat,
  broadcast_axes, graph_rewrite, identity_element, resolve, simp_sint, sint, smax,
)

def _argsort(xs) -> list[int]: return sorted(range(len(xs)), key=xs.__getitem__)
def _dedup(xs) -> list: return list(dict.fromkeys(xs))
def _all_same(xs) -> bool: return len(xs) <= 1 or all(x == xs[0] for x in xs[1:])
def _partition(xs, pred):
  a, b = [], []
  for x in xs: (a if pred(x) else b).append(x)
  return a, b
def _is_zero_const(u: UOp) -> bool: return u.is_const and not u.is_invalid and type(u.val) is not bool and u.val == 0
_zero = UPat.cvar().or_casted()
def _max_shape(sh: tuple[sint, ...]) -> tuple[int, ...]: return tuple(smax(d) for d in sh)
def _max_numel(sh: tuple[sint, ...]) -> int: return math.prod(_max_shape(sh)) if sh else 1
def _dtype_nbytes(dt) -> int: return max(1, (dt.bits + 7) // 8)
def _slice_nbytes(sh: tuple[sint, ...], dt, axes: list[int] | None = None) -> int:
  dims = [smax(sh[i]) for i in axes] if axes is not None else [smax(d) for d in sh]
  return (math.prod(dims) if dims else 1) * _dtype_nbytes(dt)

# Blackhole 3-tier fusion budgets (per-core L1 SRAM = 1.5 MB; leave headroom for CB double-buffering & code)
L1_STAGE_BUDGET = 256 * 1024       # max per-core slice for partial-axis L1 stages (e.g. per-head scores, DeltaNet state)
L1_PROLOGUE_BUDGET = 64 * 1024     # max buffer size for whole-tensor L1 prologues (e.g. RMSNorm xn, Inkling mix, MoE router)
L1_PROLOGUE_MAX_READ = 256 * 1024  # max DRAM input bytes read by a whole-tensor L1 prologue (blocks replicating heavy matmuls)
MAX_INLINE_BUFFERS = 16            # Blackhole has 32 CBs per core (vs tinygrad's GPU limit of 3)

# ---- movement op lowering on index ranges ----

@functools.cache
def _apply_reshape(in_shape: tuple[sint, ...], out_shape: tuple[sint, ...], urngs: UOp) -> UOp:
  acc: UOp = UOp.const(1)
  axes_in: list[UOp] = []
  for s, src in list(zip(out_shape, urngs.src))[::-1]:
    axes_in.append(acc * src)
    acc = acc * s
  combined = UOp.usum(UOp.const(0), *axes_in) if axes_in else UOp.const(0)
  axes_out: list[UOp] = []
  for s in in_shape[::-1]:
    axes_out.append(combined % s)
    combined = combined // s
  return graph_rewrite(UOp.sink(*axes_out[::-1]), symbolic + pm_simplify_valid + pm_drop_and_clauses)

@functools.cache
def apply_movement_op(op: Ops, in_shape: tuple[sint, ...], arg: tuple, rngs: tuple[UOp, ...]) -> tuple[UOp, ...]:
  match op:
    case Ops.SHRINK:
      return tuple(a if off == 0 else a + off for a, (off, _) in zip(rngs, arg))
    case Ops.PERMUTE:
      return tuple(rngs[p] for p in _argsort(arg))
    case Ops.EXPAND:
      return rngs[len(arg):]
    case Ops.PAD:
      out = []
      for r, sh, (off, sz) in zip(rngs, in_shape, arg):
        if sz == sh and off == 0:
          out.append(r)
        else:
          cond = graph_rewrite((r >= off) & (r < (UOp.const(sh) + off)), symbolic + pm_simplify_valid)
          out.append((r - off).valid(cond))
      return tuple(out)
    case Ops.RESHAPE:
      sink = UOp.sink(*rngs).simplify()
      ordered = sorted(sink.ranges, key=lambda r: (r.arg.axis, r.arg.name))
      sub_ph = {r: r.replace(arg=RangeArg(-1 - i, "_ph")) for i, r in enumerate(ordered)}
      res = _apply_reshape(in_shape, arg, sink.substitute(sub_ph))
      return res.substitute({v: k for k, v in sub_ph.items()}).src
    case _:
      raise RuntimeError(f"{op} is not a MovementOp")

def _valid_of(i: UOp) -> UOp:
  if any(x.is_invalid for x in i.get_idx().backward_slice): i = graph_rewrite(i, symbolic)
  return i.get_valid()

def _mop_index(r: UOp, idx: UOp) -> UOp | None:
  if r.shape is None or r.src[0].shape is None: return None
  idxs, in_shape, arg = idx.src[1:], r.src[0].shape, r.marg
  if partial := (len(idxs) != len(r.shape)):
    src_prefix = len(in_shape) - len(r.shape[len(idxs):])
    if r.op is not Ops.RESHAPE or src_prefix < 0 or in_shape[src_prefix:] != r.shape[len(idxs):]: return None
    in_shape, arg = in_shape[:src_prefix], r.shape[:len(idxs)]
  new_idxs = apply_movement_op(r.op, in_shape, arg, idxs)
  kept = {UOp.const(True)} | {c for i in new_idxs for c in _valid_of(i).split_uop(Ops.AND)}
  dropped = _dedup(c for i in idxs for c in _valid_of(i).split_uop(Ops.AND) if c not in kept)
  ret = r.src[0].index(*new_idxs)
  if partial and ret.shape != idx.shape: return None
  return UOp.uand(*dropped).where(ret, ret.const_like(0)) if dropped else ret

pm_mops = PatternMatcher([
  (UPat(GroupOp.Movement, name="r").index(allow_any_len=True, name="idx"), _mop_index),
  # store through a padded view gates the destination index, not its value
  (UPat.var("a").where(UPat.var("b").where(UPat.var("dst"), UPat.cvar("z")), UPat(Ops.CONST, arg=Invalid)).store(UPat.var("val")),
   lambda a, b, dst, z, val: (a & b).where(dst, dst.const_like(0)).store(val) if _is_zero_const(z) else None),
  (UPat.var("cond").where(UPat.var("buf").index(UPat.var("idx")), UPat.cvar("z")).store(UPat.var("val")),
   lambda cond, buf, idx, z, val: buf.index(idx.valid(cond)).store(val) if _is_zero_const(z) else None),
  # push AFTER inside movement/INDEX on storage
  (UPat(GroupOp.Movement | {Ops.INDEX}, name="r").after(allow_any_len=True, name="a"),
   lambda r, a: UOp(r.op, (a.replace(src=(r.src[0], *a.src[1:])), *r.src[1:]), r.arg)
   if r.storage_base.op in GroupOp.Defines else None),
  (UPat(GroupOp.Movement, name="r").end(allow_any_len=True, name="a"),
   lambda r, a: a.replace(src=(r.src[0], *a.src[1:]))),
])

# ---- reduce simplification & load collapse (ported from tinygrad/codegen/simplify.py) ----

def flatten_range(r: UOp) -> UOp | None:
  rngs = r.src[1:]
  if not rngs or (r.op is Ops.REDUCE and r.arg[1] != 0): return None
  flat = tuple(_dedup(x for s in rngs for x in ((s,) if s.op is Ops.RANGE else sorted(s.ranges, key=lambda rr: rr.arg.axis))))
  if flat == rngs: return None
  return r.src[0] if not flat and r.op is Ops.END else r.replace(src=(r.src[0], *flat))

pm_flatten_range = PatternMatcher([(UPat((Ops.REDUCE, Ops.END), name="r"), flatten_range)])

def no_range(u: UOp) -> bool: return not u.op_in_backward_slice_with_self(Ops.RANGE)

def reduce_unparented(red: UOp) -> UOp | None:
  if red.arg[1] != 0: return None
  if not red.src[1:]: return red.src[0]
  if not all(x.op is Ops.RANGE for x in red.src[1:]): return None
  parented, unparented = _partition(red.src[1:], lambda x: x in red.src[0].ranges)
  if not unparented: return None
  ret = red.replace(src=(red.src[0], *parented)) if parented else red.src[0]
  n = UOp.uprod(*(r.src[0] for r in unparented))
  op = red.arg[0]
  if op is not Ops.MAX and red.dtype is not dtypes.bool:
    if op is Ops.ADD:
      n_val = n.cast(ret.dtype) if ret.dtype not in dtypes.weaks and n.dtype != ret.dtype else n
      ret = ret * n_val
    elif op is Ops.MUL:
      return None
  return (n > 0).where(ret, ret.const_like(identity_element(op, red.dtype)))

pm_reduce_unparented = PatternMatcher([(UPat(Ops.REDUCE, name="red"), reduce_unparented)])

def _collapse_count_lt(r: UOp, val: UOp, z: UOp, upper: UOp | None = None, lower: UOp | None = None) -> UOp | None:
  if not _is_zero_const(z) or not no_range(val): return None
  hi = upper.minimum(r.src[0]) if upper is not None else r.src[0]
  lo = lower.maximum(0) if lower is not None else r.const_like(0)
  cnt = (hi - lo).maximum(0)
  cnt_val = cnt.cast(val.dtype) if val.dtype not in dtypes.weaks and cnt.dtype != val.dtype else cnt
  return cnt_val * val

pm_reduce_collapse = pm_reduce_unparented + PatternMatcher([
  # lift loop-invariant terms out of <
  ((UPat.var("x", dtype=dtypes.swints) + UPat.var("y")) < UPat.var("c"),
   lambda x, y, c: (x < (c - y)) if no_range(y) and no_range(c) and not no_range(x) else None),
  ((UPat.var("x", dtype=dtypes.swints) * UPat.var("y")) < UPat.var("c"),
   lambda x, y, c: (x < ((c + y - 1) // y)) if no_range(y) and no_range(c) and not no_range(x) and y.vmin > 0 else None),
  # closed-form sum over r in [0, N) of [lower <= r < upper] * val
  ((UPat(Ops.RANGE, name="r") < UPat.var("upper")).where(UPat.var("val"), _zero.named("z")).reduce(UPat.var("r"), op=Ops.ADD),
   lambda r, val, z, upper: _collapse_count_lt(r, val, z, upper=upper)),
  ((UPat(Ops.RANGE, name="r") < UPat.var("lower")).where(_zero.named("z"), UPat.var("val")).reduce(UPat.var("r"), op=Ops.ADD),
   lambda r, val, z, lower: _collapse_count_lt(r, val, z, lower=lower)),
  (((UPat(Ops.RANGE, name="r") < UPat.var("lower")).logical_not() & (UPat(Ops.RANGE, name="r") < UPat.var("upper")))
   .where(UPat.var("val"), _zero.named("z")).reduce(UPat.var("r"), op=Ops.ADD),
   lambda r, val, z, lower, upper: _collapse_count_lt(r, val, z, upper=upper, lower=lower)),
  # distribute ADD over REDUCE(ADD)
  ((UPat.var("x") + UPat.var("y")).reduce(op=Ops.ADD, allow_any_len=True, name="r"),
   lambda x, y, r: x.reduce(*r.src[1:], op=Ops.ADD) + y.reduce(*r.src[1:], op=Ops.ADD)),
  # factor loop-invariant bool param out of WHERE gate
  ((UPat(Ops.PARAM, name="x") & UPat.var("y")).where(UPat.var("c"), _zero.named("z")).reduce(op=Ops.ADD, allow_any_len=True, name="r"),
   lambda x, y, c, z, r: y.where(c, z).reduce(*r.src[1:], op=Ops.ADD) * x.cast(r.dtype) if _is_zero_const(z) else None),
  # x * cast(bool) -> where(bool, x, 0)
  (UPat.var("x") * UPat.var("gate", dtype=dtypes.bool).cast(), lambda x, gate: gate.where(x, x.const_like(0))),
]) + symbolic

def _collapse_eq_gather(r: UOp, rc: UOp, idx: UOp, expr: UOp, z: UOp) -> UOp | None:
  if not _is_zero_const(z) or r in idx.ranges or r.overflows(rc.dtype): return None
  ic = idx.cast(r.dtype) if idx.dtype != r.dtype else idx
  v = (ic >= 0) & (ic < r.src[0])
  return v.where(expr.substitute({r: ic.valid(v)}), expr.const_like(0))

pm_reduce_load_collapse = pm_reduce_collapse + PatternMatcher([
  # push CAST into WHERE(..., 0) so upcasted bf16->fp32 sums (e.g. Embedding / MoE gather) match the Kronecker rule
  (UPat(Ops.CAST, src=(UPat.var("cond").where(UPat.var("expr"), _zero.named("z")),), name="u"),
   lambda u, cond, expr, z: cond.where(expr.cast(u.dtype), u.const_like(0)) if _is_zero_const(z) else None),
  # lift x + y == c -> x == c - y
  ((UPat.var("x", dtype=dtypes.wints) + UPat.var("y")).or_casted("a").eq(UPat.var("c", dtype=dtypes.wints)),
   lambda x, y, a, c: x.eq((c.cast(y.dtype) if c.dtype != y.dtype else c) - y)
   if no_range(y) and no_range(c) and not no_range(x) and (a.op is not Ops.CAST or not a.src[0].overflows(a.dtype)) and not c.overflows(y.dtype) else None),
  # Kronecker delta: sum_r where(idx == r, expr(r), 0) -> where(0 <= idx < N, expr(idx), 0)
  (UPat.var("idx", dtype=dtypes.wints).eq(UPat(Ops.RANGE, name="r").or_casted("rc")).where(UPat.var("expr"), _zero.named("z"))
   .reduce(UPat.var("r"), op=Ops.ADD), _collapse_eq_gather),
])

def _temp_var(idx: int, s: UOp) -> UOp:
  return UOp(Ops.PARAM, (), ParamArg(-1, s.dtype, f"_in{idx}", vmin_vmax=(s.vmin, s.vmax)))

def reduce_collapse(red: UOp, u: UOp, pm: PatternMatcher = pm_reduce_collapse) -> UOp | None:
  if red.arg != (Ops.ADD, 0) or not red.src[1:]: return None
  for r in red.src[1:]:
    if r.op is not Ops.RANGE: return None
    included = u.toposort(gate=lambda x: r in x.ranges)
    if not included: return None
    if any(x.op in GroupOp.Effect | {Ops.REDUCE} for x in included): return None
    included_set = set(included)
    replaces: dict[UOp, UOp] = {}
    for node in included:
      for s in node.src:
        if s in included_set or s in replaces or s.op in GroupOp.Defines | {Ops.CONST}: continue
        replaces[s] = _temp_var(len(replaces), s)
    collapse_fxn = u.substitute(replaces).reduce(r, op=Ops.ADD)
    sink = graph_rewrite(collapse_fxn, pm_flatten_range + pm)
    if not no_range(sink): return None
    u = sink.substitute({v: k for k, v in replaces.items()})
  return u

def reduce_load_collapse(red: UOp, u: UOp) -> UOp | None: return reduce_collapse(red, u, pm=pm_reduce_load_collapse)

pm_reduce_simplify = pm_reduce_unparented + PatternMatcher([
  (UPat(Ops.REDUCE, src=(UPat.var("u"),), arg=(Ops.ADD, 0), allow_any_len=True, name="red"), reduce_collapse),
])

def _no_load(u: UOp) -> bool: return not u.op_in_backward_slice_with_self(Ops.INDEX)

pm_load_collapse = PatternMatcher([
  (UPat(Ops.REDUCE, src=(UPat.var("u"), UPat()), arg=(Ops.ADD, 0), name="red"), reduce_load_collapse),
  # avoid doing math on a loaded index (which can overflow)
  ((UPat.var("x", dtype=dtypes.weakint) + UPat.var("y")) < UPat.var("c"),
   lambda x, y, c: x < (c - y) if _no_load(y) and _no_load(c) and not _no_load(x) else None),
  # collapse bf16 -> fp32 -> bf16 roundtrip created by pushing CAST into WHERE during gather collapse
  (UPat(Ops.CAST, src=(UPat.var("cond").where(UPat.var("a"), _zero.named("z")),), name="u"),
   lambda u, cond, a, z: cond.where(a.cast(u.dtype), u.const_like(0)) if _is_zero_const(z) else None),
])

# ---- rangeify: Layer 0 movement/tensor ops -> explicit RANGE + INDEX + STAGE ----

@dataclass
class IndexingContext:
  realize_map: dict[UOp, list[int] | None] = field(default_factory=dict)
  non_removable: dict[UOp, None] = field(default_factory=dict)
  range_map: dict[UOp, tuple[tuple[UOp, ...], tuple[UOp, ...]]] = field(default_factory=dict)
  reduce_ranges: set[UOp] = field(default_factory=set)
  range_idx: itertools.count = field(default_factory=itertools.count)

  def new_range(self, s: sint) -> UOp:
    if isinstance(s, UOp) and s.op is Ops.RANGE: return s
    return UOp.range(s, next(self.range_idx)) if (s != 1 if isinstance(s, int) else resolve(s.ne(1), True)) else UOp.const(0)

ALWAYS_CONTIGUOUS: frozenset[Ops] = GroupOp.Defines | {Ops.AFTER, Ops.CONST, Ops.LOAD, Ops.CALL}

def _needs_snapshot(dest: UOp, src: UOp) -> bool:
  """True if an in-place loop `dest[i] = src[i]` could read an element of dest's buffer after overwriting it."""
  base, stack, seen = dest.storage_base, [(src, True)], set()
  while stack:
    u, pointwise = stack.pop()
    if (u, pointwise) in seen: continue
    seen.add((u, pointwise))
    if pointwise and u is dest: continue  # iteration i reads exactly the element it writes: safe
    if u.op in GroupOp.Defines or u.op is Ops.AFTER:
      if u.storage_base is base: return True
      continue  # don't walk into the stores an AFTER waits on
    stack.extend((s, pointwise and u.op in GroupOp.Elementwise) for s in u.src)
  return False

def _realize_store_after_src(ctx: IndexingContext, dest: UOp, src: UOp) -> None:
  if _needs_snapshot(dest, src): ctx.realize_map[src] = ctx.non_removable[src] = None

def _realize_call_srcs(ctx: IndexingContext, c: UOp) -> None:
  for s in c.src[1:]:
    while s.op is Ops.RESHAPE: s = s.src[0]
    if s.op not in ALWAYS_CONTIGUOUS:
      ctx.realize_map[s] = None
      ctx.non_removable[s] = None

def _realize_user_stage(ctx: IndexingContext, st: UOp) -> None:
  ctx.realize_map[st] = None
  ctx.non_removable[st] = None

def _realize_value_after(ctx: IndexingContext, a: UOp) -> None:
  s = a.src[0]
  if s.op not in ALWAYS_CONTIGUOUS and s.storage_base.op not in GroupOp.Defines:
    ctx.realize_map[s] = None
    ctx.non_removable[s] = None

pm_generate_realize_map = PatternMatcher([
  (UPat(Ops.CALL, src=(UPat((Ops.SINK, Ops.PROGRAM)),), allow_any_len=True, name="c"), _realize_call_srcs),
  (UPat(Ops.STORE, name="tr"), lambda ctx, tr: ctx.realize_map.__setitem__(tr, None)),
  (UPat(Ops.STORE, src=(UPat.var("dest"), UPat.var("src"))), _realize_store_after_src),
  # AFTER wrapping a computed (non-storage) value: materialize src[0] so the dependency attaches to its buffer
  (UPat(Ops.AFTER, name="a"), _realize_value_after),
  # Layer 0 explicit .contiguous() is a STAGE with no StageArg (rangeified STAGEs carry one, even 0-D); keep it non-removable
  (UPat(Ops.STAGE, arg=None, name="st"), _realize_user_stage),
])

def _broadcast_rngs(x: UOp, src: UOp, rngs: tuple[UOp, ...]) -> tuple[UOp, ...]:
  if x.op not in GroupOp.Broadcastable | {Ops.STORE}: return rngs
  if src.shape is None or x.shape is None: return rngs
  baxes, nleft = broadcast_axes(src.shape, x.shape), len(x.shape) - len(src.shape)
  return tuple(UOp.const(0) if j in baxes else r for j, r in enumerate(rngs) if j >= nleft)

def _data_srcs(op: Ops, src: tuple[UOp, ...]) -> tuple[UOp, ...]:
  if op in GroupOp.Defines | {Ops.RANGE, Ops.SPECIAL}: return ()
  if op in GroupOp.Movement | {Ops.INDEX, Ops.STAGE, Ops.REDUCE, Ops.AFTER, Ops.END, Ops.BACKEDGE}: return src[:1]
  if op is Ops.CALL: return src[1:]
  return src

def _create_bufferize_and_index_srcs(ctx: IndexingContext, x: UOp) -> list[UOp]:
  new_srcs: list[UOp] = []
  n_data = len(_data_srcs(x.op, x.src))
  # for CALL, src[0] is body and src[1:] are data args
  start_idx = 1 if x.op is Ops.CALL else 0
  for i, s in enumerate(x.src):
    new_src = s
    in_data = (i >= 1) if x.op is Ops.CALL else (i < n_data)
    src_rngs = _broadcast_rngs(x, s, ctx.range_map[x][0]) if x in ctx.range_map and in_data else ()
    if s.op in GroupOp.Defines | {Ops.AFTER} or (s.op is Ops.STAGE and s.arg is not None):
      if x in ctx.range_map and in_data and not s.is_variable:
        new_src = new_src.index(*src_rngs)
    elif s in ctx.realize_map:
      spec = ctx.realize_map[s]
      if s.op is Ops.STORE:
        end_rngs = [r for r in ctx.range_map[s][1] if r.op is Ops.RANGE]
        new_src = s.end(*end_rngs) if end_rngs else s
        del ctx.realize_map[s]
      else:
        removable = s.op not in ALWAYS_CONTIGUOUS and s not in ctx.non_removable
        if spec is None:
          closed_ranges = ctx.range_map[s][1]
          new_src = UOp(Ops.STAGE, (new_src, *closed_ranges), StageArg(removable=removable, space="dram"))
          if x in ctx.range_map and in_data:
            new_src = new_src.index(*src_rngs)
        else:
          # Partial-axis L1 stage: keep shared outer ranges open, close only `spec` axes into per-core L1
          closed_ranges = tuple(ctx.range_map[s][1][j] for j in spec)
          new_src = UOp(Ops.STAGE, (new_src, *closed_ranges), StageArg(removable=removable, space="l1"))
          if x in ctx.range_map and in_data:
            closed_src_rngs = tuple(src_rngs[j] for j in spec)
            new_src = new_src.index(*closed_src_rngs)
    new_srcs.append(new_src)
  return new_srcs

def _apply_buf_and_idx(ctx: IndexingContext, x: UOp) -> UOp | None:
  if x.op is Ops.STAGE and x.arg is None:
    # unwrap Layer 0 .contiguous() STAGE (its consumer already wrapped it in rangeified STAGE)
    return _create_bufferize_and_index_srcs(ctx, x)[0]
  ns = tuple(_create_bufferize_and_index_srcs(ctx, x))
  return x if ns == x.src else x.replace(src=ns)

def _convert_pad_to_where(ctx: IndexingContext, x: UOp) -> UOp | None:
  if x not in ctx.range_map: return None
  if x.op is Ops.INDEX and len(ctx.range_map[x][0]) == len(ctx.range_map[x][1]): return None
  bx = _apply_buf_and_idx(ctx, x)
  if bx is None or bx.src[0] is x: return None
  valid = UOp.uand(*(r.get_valid() for r in ctx.range_map[x][0]))
  return valid.where(bx.src[0], x.const_like(0))

def _convert_reduce_to_ranges(ctx: IndexingContext, x: UOp) -> UOp | None:
  if x.arg[1] == 0: return None
  if x not in ctx.range_map: raise RuntimeError("REDUCE has no ranges in rangeify")
  bx = _apply_buf_and_idx(ctx, x)
  assert bx is not None
  new_ranges = tuple(r for r in ctx.range_map[x][0][:x.arg[1]] if r.op is Ops.RANGE)
  return UOp(Ops.REDUCE, (bx.src[0], *new_ranges, *bx.src[1:]), (x.arg[0], 0))

def _stack_select(r0: UOp, srcs: list[UOp]) -> UOp:
  if len(srcs) == 1: return srcs[0]
  half = 1 << ((len(srcs) - 1).bit_length() - 1)
  return ((r0 % (2 * half)) < half).where(_stack_select(r0, srcs[:half]), _stack_select(r0, srcs[half:]))

def _convert_stack_to_where(ctx: IndexingContext, x: UOp) -> UOp | None:
  if x not in ctx.range_map: return None
  srcs = _create_bufferize_and_index_srcs(ctx, x)
  return _stack_select(ctx.range_map[x][1][0], srcs)

def _remove_movement_after_rangeify(ctx: IndexingContext, x: UOp) -> UOp | None:
  if x in ctx.range_map or x.src[0].op is Ops.INDEX: return x.src[0]
  return None

pm_apply_rangeify = PatternMatcher([
  (UPat(Ops.REDUCE, name="x"), _convert_reduce_to_ranges),
  (UPat((Ops.PAD, Ops.INDEX), name="x"), _convert_pad_to_where),
  (UPat(Ops.STACK, name="x"), _convert_stack_to_where),
  (UPat(GroupOp.All - {Ops.INDEX}, name="x"), lambda ctx, x: None if (x.op is Ops.STAGE and x.arg is not None) else _apply_buf_and_idx(ctx, x)),
  (UPat(GroupOp.Movement, name="x"), _remove_movement_after_rangeify),
])

def _can_keep_open(r: UOp, reduce_ranges: set[UOp], ended_set: frozenset[UOp]) -> bool:
  rngs = r.get_idx().ranges | r.get_valid().ranges
  return all(rr not in reduce_ranges and rr not in ended_set for rr in rngs)

def run_rangeify(tsink: UOp, *, l1_budget: int = L1_STAGE_BUDGET) -> UOp:
  rctx = IndexingContext()
  graph_rewrite(tsink, pm_generate_realize_map, ctx=rctx)

  tsink_toposort = tsink.toposort()
  consumer_map: dict[UOp, dict[UOp, None]] = {x: {} for x in tsink_toposort}
  for c in tsink_toposort:
    for x in _data_srcs(c.op, c.src):
      if x in consumer_map: consumer_map[x][c] = None

  ended_ranges_map: dict[UOp, frozenset[UOp]] = {}
  for x in reversed(tsink_toposort):
    if x.op in {Ops.CALL, Ops.AFTER, Ops.SINK}: continue
    if x.shape is None: continue

    ended_set: frozenset[UOp] = frozenset().union(*(ended_ranges_map.get(u, frozenset()) for u in consumer_map[x]))
    ended = [rctx.range_map[c][0][i] for c in consumer_map[x] if c in rctx.range_map and c.op in GroupOp.Broadcastable
             for i in broadcast_axes(x.shape, c.shape)]
    broadcast_ended: frozenset[UOp] = frozenset().union(*(r.ranges for r in ended)) if ended else frozenset()
    if x.op is Ops.REDUCE: ended_set = ended_set | broadcast_ended
    ended_ranges_map[x] = ended_set

    consumer_rngs = [_broadcast_rngs(c, x, rctx.range_map[c][0]) for c in consumer_map[x] if c in rctx.range_map]
    if x in rctx.realize_map:
      out_rngs = tuple(rctx.new_range(s) for s in x.shape)
      ended_ranges_map[x] = frozenset()
    elif not consumer_rngs:
      continue
    elif len(consumer_rngs) == 1:
      out_rngs = consumer_rngs[0]
    else:
      rngs_valids = []
      for valid_rngs in zip(*consumer_rngs):
        local_rngs, valids = zip(*[(r.get_idx(), r.get_valid()) for r in valid_rngs])
        rngs_valids.append((local_rngs, valids))
      all_same_rngs = all(_all_same(lr) for lr, _ in rngs_valids)
      if all_same_rngs:
        out_rngs = tuple(graph_rewrite(lr[0].valid(UOp.uor(*vs)), symbolic) for lr, vs in rngs_valids)
      else:
        open_axes: set[int] = set()
        merged_open: dict[int, UOp] = {}
        if l1_budget > 0 and x not in rctx.non_removable:
          for i, (lr, vs) in enumerate(rngs_valids):
            if _all_same(lr):
              m = graph_rewrite(lr[0].valid(UOp.uor(*vs)), symbolic)
              if _can_keep_open(m, rctx.reduce_ranges, ended_set):
                open_axes.add(i)
                merged_open[i] = m
        closed_axes = [i for i in range(len(rngs_valids)) if i not in open_axes]
        if (l1_budget > 0 and any(merged_open[i].ranges for i in open_axes) and
            _slice_nbytes(x.shape, x.dtype, closed_axes) <= l1_budget):
          out_rngs = tuple(merged_open[i] if i in open_axes else rctx.new_range(x.shape[i]) for i in range(len(rngs_valids)))
          rctx.realize_map[x] = closed_axes
        else:
          out_rngs = tuple(rctx.new_range(x.shape[i]) for i in range(len(rngs_valids)))
          rctx.realize_map[x] = None
          ended_ranges_map[x] = frozenset()

    if ended_ranges_map[x] and x.op in GroupOp.Elementwise | {Ops.REDUCE}:
      cur_ended = ended_ranges_map[x]
      ended_ranges_map[x] = frozenset()
      if out_rngs:
        if x not in rctx.realize_map:
          open_axes = {i for i, r in enumerate(out_rngs) if _can_keep_open(r, rctx.reduce_ranges, cur_ended)} if l1_budget > 0 else set()
          closed_axes = [i for i in range(len(out_rngs)) if i not in open_axes]
          has_open_rng = any(out_rngs[i].ranges for i in open_axes)
          if l1_budget > 0 and x not in rctx.non_removable and has_open_rng and not closed_axes and x.op is not Ops.REDUCE:
            # Pure Elementwise with all axes shared/open (e.g. cast/recip on per-head reduce):
            # don't split or create a 0-D L1 stage; propagate cur_ended down to the underlying REDUCE!
            ended_ranges_map[x] = cur_ended
          elif (l1_budget > 0 and x not in rctx.non_removable and has_open_rng and
                _slice_nbytes(x.shape, x.dtype, closed_axes) <= l1_budget):
            out_rngs = tuple(out_rngs[i] if i in open_axes else rctx.new_range(x.shape[i]) for i in range(len(out_rngs)))
            rctx.realize_map[x] = closed_axes
          else:
            rctx.realize_map[x] = None
            out_rngs = tuple(rctx.new_range(x.shape[i]) for i in range(len(out_rngs)))
        elif (prev_closed := rctx.realize_map[x]) is not None:
          # ensure no currently-open axis belongs to cur_ended
          bad = [i for i in range(len(out_rngs)) if i not in prev_closed and not _can_keep_open(out_rngs[i], rctx.reduce_ranges, cur_ended)]
          if bad:
            closed_axes = sorted(set(prev_closed) | set(bad))
            open_axes = {i for i in range(len(out_rngs)) if i not in closed_axes}
            if any(out_rngs[i].ranges for i in open_axes) and _slice_nbytes(x.shape, x.dtype, closed_axes) <= l1_budget:
              out_rngs = tuple(out_rngs[i] if i in open_axes else rctx.new_range(x.shape[i]) for i in range(len(out_rngs)))
              rctx.realize_map[x] = closed_axes
            else:
              rctx.realize_map[x] = None
              out_rngs = tuple(rctx.new_range(x.shape[i]) for i in range(len(out_rngs)))
    ended_ranges_map[x] = ended_ranges_map[x] | broadcast_ended

    rngs = out_rngs
    if x.op in GroupOp.Movement: rngs = apply_movement_op(x.op, x.src[0].shape, x.marg, rngs)
    elif x.op is Ops.STACK: rngs = out_rngs[1:]
    elif x.op is Ops.INDEX and len(x.src) - 1 + len(out_rngs) == len(x.src[0].shape): rngs = x.src[1:] + out_rngs
    if x.op is Ops.EXPAND:
      ended_ranges_map[x] = ended_ranges_map[x] | frozenset().union(*(r.ranges for r in out_rngs[:len(x.marg)]))
    if x.op is Ops.REDUCE:
      red_rngs = tuple(rctx.new_range(s) for s in x.src[0].shape[:x.arg[1]])
      rctx.reduce_ranges.update(r for r in red_rngs if r.op is Ops.RANGE)
      rngs = red_rngs + out_rngs

    rctx.range_map[x] = (rngs, out_rngs)

  return graph_rewrite(tsink, pm_apply_rangeify, ctx=rctx, bottom_up=True)

# ---- stage (bufferize) cleanups ----

def _cleanup_dead_axes(b: UOp) -> UOp | None:
  if len(b.src) <= 1 or not (isinstance(b.arg, StageArg) and b.arg.removable): return None
  if b.src[0].op is Ops.AFTER: return None
  new_rng, reshape = [], []
  for s, rng in zip(b.shape, b.src[1:]):
    if rng.op is Ops.RANGE and rng.src[0].op is not Ops.CONST: return None
    if rng.op is Ops.CONST or (rng.op is Ops.RANGE and rng not in b.src[0].ranges):
      reshape.append(1)
    else:
      reshape.append(s)
      new_rng.append(rng)
  if len(new_rng) != len(reshape):
    return b.replace(src=(b.src[0], *new_rng)).reshape(tuple(reshape)).expand(b.shape)
  return None

_TRIVIAL_INLINE_OPS = frozenset({Ops.CAST, Ops.BITCAST, Ops.NEG, Ops.INDEX, Ops.CONST, Ops.RANGE, Ops.PARAM, Ops.BUFFER, Ops.ALLOC, Ops.AFTER})

def _is_nontrivial_compute(src: UOp) -> bool:
  """True if `src` does real compute (not just a view/cast/load) or reads another STAGE."""
  found = False
  def gate(x: UOp) -> bool:
    nonlocal found
    if found: return False
    if x.op is Ops.STAGE:
      found = True
      return False
    if x.op is Ops.REDUCE or (x.op in GroupOp.ALU and x.op not in _TRIVIAL_INLINE_OPS):
      found = True
      return False
    return True
  src.toposort(gate=gate)
  return found

def _mark_keep_staged(tsink: UOp) -> UOp:
  """Mark nontrivial float compute STAGEs read inside a REDUCE that are loop-invariant wrt an outer range.

  Setting `inline=False` on `StageArg` survives child inlining and prevents e.g. `rmsnorm(x)` from
  inlining into `lm_head`/`SwiGLU`'s `N x K` loop or `exp2(scores - max)` into `attn @ V`'s `d` loop;
  instead they stay staged in L1 once per core.
  """
  keep: set[UOp] = set()
  for n in tsink.toposort(enter_calls=False):
    if n.op is not Ops.REDUCE or n.arg[1] != 0: continue
    red_outer = n.ranges
    if not red_outer: continue
    def gate(x: UOp) -> bool:
      if x.op is Ops.INDEX and x.src[0].op is Ops.STAGE:
        st = x.src[0]
        if isinstance(st.arg, StageArg) and st.arg.removable and st.arg.inline and st.dtype.is_float:
          if (red_outer - x.ranges) and _is_nontrivial_compute(st.src[0]):
            keep.add(st)
        return False
      return x.op is not Ops.STAGE
    n.src[0].toposort(gate=gate)
  if not keep: return tsink
  memo: dict[UOp, UOp] = {}
  for n in tsink.toposort(enter_calls=False):
    ns = tuple(memo.get(s, s) for s in n.src)
    cur = n if ns == n.src else n.replace(src=ns)
    if n in keep:
      cur = cur.replace(arg=StageArg(removable=cur.arg.removable, space=cur.arg.space, inline=False))
    memo[n] = cur
  return memo[tsink]

def _remove_bufferize(src: UOp, buf: UOp, idx: UOp) -> UOp | None:
  if not (isinstance(buf.arg, StageArg) and buf.arg.removable and buf.arg.inline): return None
  if len(buf.src) != len(idx.src): return None
  if not all(x.op in {Ops.RANGE, Ops.CONST} for x in buf.src[1:]): return None

  accessed_buffers: list[UOp] = []
  reduces: list[UOp] = []
  def red_gate(x: UOp) -> bool:
    if x.op is Ops.AFTER:
      accessed_buffers.append(x.storage_base)
      return False
    if x.op is Ops.STAGE:
      if isinstance(x.arg, StageArg) and x.arg.space == "l1":
        return True  # L1 stage stays inside the kernel; inspect its body for reduces/buffers!
      accessed_buffers.append(x)
      return False
    if x.op is Ops.STORE: return False
    if x.op in GroupOp.Defines and not x.is_variable:
      accessed_buffers.append(x)
    if x.op is Ops.REDUCE: reduces.append(x)
    return True
  src.toposort(gate=red_gate)
  if len(_dedup(accessed_buffers)) > MAX_INLINE_BUFFERS: return None

  # don't inline a stage containing a reduce that accesses any buffer
  buf_in_reduce = False
  def buf_gate(x: UOp) -> bool:
    nonlocal buf_in_reduce
    if (x.op in GroupOp.Defines and not x.is_variable) or x.op is Ops.AFTER:
      buf_in_reduce = True
    elif x.op is Ops.STAGE:
      if isinstance(x.arg, StageArg) and x.arg.space == "l1": return True
      buf_in_reduce = True
    return not buf_in_reduce
  if reduces:
    UOp.sink(*(r.src[0] for r in reduces)).toposort(gate=buf_gate)
  if buf_in_reduce: return None

  replaced = {k: v for k, v in zip(buf.src[1:], idx.src[1:]) if k.op is not Ops.CONST and not v.is_invalid}
  return src.substitute(replaced)

def _promote_l1_stages(tsink: UOp, *, prologue_budget: int = L1_PROLOGUE_BUDGET,
                       max_dram_read: int = L1_PROLOGUE_MAX_READ) -> UOp:
  """Promote small, cheap whole-tensor STAGEs (e.g. RMSNorm rms/xn, Inkling mix, MoE router) to per-core L1.

  Heavy weight-reading stages (like SwiGLU/QKV/o_proj/lm_head) exceed `max_dram_read` and stay DRAM
  so their weight reads are never replicated across cores.
  """
  dram_read_cache: dict[UOp, int] = {}

  def stage_dram_read(st: UOp) -> int:
    if st in dram_read_cache: return dram_read_cache[st]
    seen_dram: dict[UOp, None] = {}
    def gate(x: UOp) -> bool:
      if x.op is Ops.STAGE:
        if isinstance(x.arg, StageArg) and x.arg.space == "l1":
          return True  # walk through nested L1 stages to count their underlying DRAM reads
        seen_dram[x] = None
        return False
      if x.op is Ops.AFTER:
        seen_dram[x.storage_base] = None
        return False
      if x.op in GroupOp.Defines and not x.is_variable:
        seen_dram[x] = None
        return False
      return True
    st.src[0].toposort(gate=gate)
    total = sum(_slice_nbytes(b.shape or (), b.dtype) for b in seen_dram)
    dram_read_cache[st] = total
    return total

  # Bottom-up rebuild so promoted children are consistently rewritten inside parent STAGEs
  memo: dict[UOp, UOp] = {}
  for n in tsink.toposort(enter_calls=False):
    ns = tuple(memo.get(s, s) for s in n.src)
    cur = n if ns == n.src else n.replace(src=ns)
    if cur.op is Ops.STAGE and isinstance(cur.arg, StageArg) and cur.arg.removable and cur.arg.space == "dram":
      if _slice_nbytes(cur.shape or (), cur.dtype) <= prologue_budget and stage_dram_read(cur) <= max_dram_read:
        cur = cur.replace(arg=StageArg(removable=True, space="l1"))
    memo[n] = cur
  return memo[tsink]

def _remove_noop_bufferize(idx: UOp, b2: UOp) -> UOp | None:
  if len(b2.src) <= 1 or not b2.arg.removable or idx.src[1:] != b2.src[1:]: return None
  return idx.src[0]._mop(Ops.SHRINK, tuple((0, s) for s in b2.shape))

pm_const_buffer_folding = pm_mops + PatternMatcher([
  (UPat(Ops.STAGE, name="b"), _cleanup_dead_axes),
  (UPat(Ops.INDEX, name="idx").f(Ops.STAGE, allow_any_len=True, name="b2"), _remove_noop_bufferize),
  (UPat.cvar("c").or_casted().f(Ops.STAGE, allow_any_len=True, name="b"), lambda c, b: b.const_like(c.val) if b.arg.removable else None),
  (UPat(Ops.INDEX, src=(UPat.cvar().or_casted("c"),), allow_any_len=True), lambda c: c),
])

pm_remove_bufferize = PatternMatcher([
  (UPat.var("src").f(Ops.STAGE, allow_any_len=True, name="buf").index(allow_any_len=True, name="idx"), _remove_bufferize),
  (UPat.var("x").store(UPat.var("x")), lambda x: UOp.noop()),
])

# ---- STAGE -> ALLOC + STORE + END ----

def _bufferize_to_store(x: UOp) -> UOp | None:
  if len(x.src) == 1 and not isinstance(x.arg, StageArg): return None
  # commit weak dtypes for storage
  dt = dtypes.i32 if x.dtype is dtypes.weakint else dtypes.fp32 if x.dtype is dtypes.weakfloat else x.dtype
  sh = x.shape or ()
  max_sh = _max_shape(sh)
  rngs = sorted([r for r in x.src[1:] if r.op is Ops.RANGE], key=lambda r: r.arg.axis)
  # 0-D scalar stage gets a (1,) backing alloc
  alloc_sh = max_sh if max_sh else (1,)
  idxs = x.src[1:] if max_sh else (UOp.const(0),)
  space = x.arg.space if isinstance(x.arg, StageArg) else "dram"
  buf = UOp.alloc(alloc_sh, dt, space=space)
  val = x.src[0].cast(dt) if x.src[0].dtype != dt else x.src[0]
  st = buf.index(*idxs).store(val)
  do_store = st.end(*rngs) if rngs else st
  ret = buf.after(do_store)
  if not max_sh: ret = ret.reshape(())
  elif max_sh != sh: ret = ret._mop(Ops.SHRINK, tuple((0, s) for s in sh))
  return ret.cast(x.dtype) if dt != x.dtype else ret

def _is_noop_after_dep(x: UOp) -> bool:
  return (x.op is Ops.NOOP and not x.src) or (x.op in (Ops.END, Ops.AFTER) and _is_noop_after_dep(x.src[0]) and all(s.op is Ops.RANGE for s in x.src[1:]))

def _remove_noop_afters(x: UOp) -> UOp | None:
  src = (x.src[0], *(s for s in x.src[1:] if not _is_noop_after_dep(s)))
  return None if len(src) == len(x.src) else (src[0] if len(src) == 1 else x.replace(src=src))

pm_add_buffers = pm_mops + PatternMatcher([
  (UPat(Ops.STAGE, name="x"), _bufferize_to_store),
  (UPat(Ops.INDEX, src=(UPat(Ops.CAST, dtype=dtypes.weaks, src=(UPat.var("buf"),)),), allow_any_len=True, name="u"),
   lambda u, buf: u.replace(src=(buf, *u.src[1:])).cast(u.dtype)),
  (UPat(Ops.STORE, src=(UPat(), UPat(Ops.CONST, arg=Invalid))), lambda: UOp.noop()),
  (UPat(Ops.AFTER, name="x"), _remove_noop_afters),
])

def _strip_zero_shrink(x: UOp) -> UOp:
  return x.src[0] if x.op is Ops.SHRINK and all(o == 0 for o, _ in x.marg) else x

pm_no_indexing_calls = PatternMatcher([
  (UPat(Ops.CALL, name="u"),
   lambda u: u.replace(src=(u.src[0], *(_strip_zero_shrink(s.src[0] if s.op is Ops.INDEX else s) for s in u.src[1:])))),
])

pm_no_views = PatternMatcher([
  (UPat((Ops.RESHAPE, Ops.SHRINK), src=(UPat(GroupOp.Defines | {Ops.AFTER}),), allow_any_len=True, name="v"), lambda v: v.src[0]),
])

# ---- kernel splitting + per-kernel load collapse & Layer 1 LOAD lowering ----

def _is_l1_buf(u: UOp) -> bool:
  return u.op is Ops.ALLOC and u.arg.space == "l1"

def _store_target_buf(x: UOp) -> UOp | None:
  while x.op is Ops.END: x = x.src[0]
  return x.src[0].storage_base if x.op is Ops.STORE else None

@dataclass
class _SplitCtx:
  bufs: dict[UOp, UOp] = field(default_factory=dict)   # DRAM storage base -> arg passed to CALL (may be AFTER)
  l1_bufs: dict[UOp, None] = field(default_factory=dict)  # kernel-local L1 ALLOCs kept inside the kernel
  vars: dict[UOp, None] = field(default_factory=dict)  # symbolic scalar PARAMs referenced
  ranges: dict[RangeArg, None] = field(default_factory=dict)

def _add_buf(ctx: _SplitCtx, buf: UOp) -> None:
  if buf.is_variable:
    ctx.vars[buf] = None
    raise BottomUpGate
  if _is_l1_buf(buf):
    ctx.l1_bufs[buf] = None
    raise BottomUpGate
  if buf not in ctx.bufs: ctx.bufs[buf] = buf
  raise BottomUpGate

def _handle_after(ctx: _SplitCtx, after: UOp) -> UOp | None:
  base = after.storage_base
  if _is_l1_buf(base):
    ctx.l1_bufs[base] = None
    return None  # keep L1 AFTER and its producing L1 STORE/END inside the same kernel
  prev = ctx.bufs.get(base)
  ctx.bufs[base] = after if prev is None or prev is base else base.after(*dict.fromkeys(prev.src[1:] + after.src[1:]))
  return base

pm_to_kernel_bufs = PatternMatcher([
  (UPat((Ops.BUFFER, Ops.ALLOC, Ops.PARAM), name="buf"), _add_buf),
  (UPat(Ops.AFTER, name="after"), _handle_after),
  (UPat(Ops.RANGE, name="r"), lambda ctx, r: ctx.ranges.__setitem__(r.arg, None) or None),
])

def _debuf(slot: int, buf: UOp) -> UOp:
  sh = buf.shape or ()
  max_sh = _max_shape(sh)
  numel = _max_numel(sh)
  p = UOp.param(slot, buf.dtype, shape=(numel,))
  v = p.reshape(max_sh)
  return v._mop(Ops.SHRINK, tuple((0, s) for s in sh)) if max_sh != sh else v

def _lower_kernel_mem(root: UOp) -> UOp:
  """Convert read INDEXes to LOADs and turn Invalid-gated INDEXes into explicit gated LOAD/STORE ops."""
  def rw(u: UOp) -> UOp:
    memo: dict[UOp, UOp] = {}
    for n in u.toposort():
      if n.op is Ops.STORE:
        dst, val = n.src[0], memo[n.src[1]]
        if dst.op is Ops.INDEX:
          base = memo[dst.src[0]]
          idx_raw = memo[dst.src[1]]
          if idx_raw.is_invalid:
            memo[n] = UOp.noop()
          elif idx_raw.op is Ops.WHERE and idx_raw.src[2].is_invalid:
            memo[n] = base.index(idx_raw.src[1]).store(val, gate=idx_raw.src[0])
          else:
            memo[n] = base.index(idx_raw).store(val)
        else:
          memo[n] = memo[dst].store(val)
      elif n.op is Ops.INDEX:
        base = memo[n.src[0]]
        idx_raw = memo[n.src[1]]
        if idx_raw.is_invalid:
          memo[n] = n.const_like(0)
        elif idx_raw.op is Ops.WHERE and idx_raw.src[2].is_invalid:
          memo[n] = base.index(idx_raw.src[1]).load(gate=idx_raw.src[0])
        else:
          memo[n] = base.index(idx_raw).load()
      else:
        ns = tuple(memo[s] for s in n.src)
        memo[n] = n if ns == n.src else n.replace(src=ns)
    return memo[u]
  out = rw(root)
  out = graph_rewrite(out, pm_remove_invalid + symbolic)
  return out

def _renumber_ranges(u: UOp) -> UOp:
  seen: dict[RangeArg, int] = {}
  subs: dict[UOp, UOp] = {}
  for n in u.toposort():
    if n.op is Ops.RANGE:
      idx = seen.setdefault(n.arg, len(seen))
      if n.arg != RangeArg(idx): subs[n] = n.replace(arg=RangeArg(idx))
  return u.substitute(subs)

def _split_store(x: UOp) -> UOp | None:
  if x.ranges: return None
  if (tgt := _store_target_buf(x)) is not None and _is_l1_buf(tgt): return None
  sctx = _SplitCtx()
  ret = graph_rewrite(x, pm_to_kernel_bufs + pm_flatten_range, ctx=sctx, bottom_up=True)

  # map DRAM buffers and symbolic scalar vars to kernel-local PARAM slots; flatten & canonically name L1 ALLOCs
  subs: dict[UOp, UOp] = {}
  call_args: list[UOp] = []
  for b, arg in sctx.bufs.items():
    subs[b] = _debuf(len(call_args), b)
    call_args.append(arg)
  for v in sctx.vars:
    subs[v] = v.param_like(len(call_args), name=v.arg.name)
    call_args.append(v)
  for i, b in enumerate(sctx.l1_bufs):
    sh = b.shape or ()
    max_sh = _max_shape(sh)
    flat = UOp.alloc((_max_numel(sh),), b.dtype, name=f"l{i}", space="l1")
    v = flat.reshape(max_sh)
    subs[b] = v._mop(Ops.SHRINK, tuple((0, s) for s in sh)) if max_sh != sh else v

  ret = _renumber_ranges(ret.substitute(subs))

  # flatten multi-axis INDEX -> 1D linear INDEX, collapse one-hot gathers (Embedding/MoE), and simplify
  ret = graph_rewrite(ret, pm_mops + symbolic)
  ret = graph_rewrite(ret, pm_load_collapse + pm_flatten_range)
  ret = graph_rewrite(ret, sym + pm_move_where_on_load + pm_flatten_range + pm_reduce_unparented)
  ret = _renumber_ranges(_lower_kernel_mem(ret))

  # anonymous KernelArg("") lets structurally identical kernels deduplicate via hash-consing
  return UOp.sink(ret, arg=KernelArg("")).call(*call_args)

def split_wide_max(x):
  # Materialize independent partial maxima so the worker grid can distribute
  # a reduction whose scalar output would otherwise occupy just one worker.
  shape = x.shape
  if shape is None or len(shape) != 1 or not isinstance(n := shape[0], int) or n < 4096: return None
  if not x.dtype.is_float and not (x.dtype.is_int and -(2**24) <= x.vmin <= x.vmax <= 2**24): return None
  width = 256
  blocks = (n + width - 1) // width
  value = x.cast(dtypes.fp32) if x.dtype.is_int else x
  rows = value.pad(((0, -n % width),), value=-math.inf).reshape(blocks, 1, width)
  partials = rows.max(-1, keepdim=True).contiguous()
  return partials.reshape(blocks).max(0).cast(x.dtype).contiguous()


pm_split_wide_max = PatternMatcher([(UPat(Ops.REDUCE, src=(UPat.var("x"),), arg=(Ops.MAX, 1)), split_wide_max)])


@functools.lru_cache(maxsize=128)
def _lower_function_body(body: UOp, l1_budget: int) -> UOp:
  return _lower_one_sink(body, {}, l1_budget=l1_budget)

def _lower_one_sink(tsink: UOp, call_memo: dict[UOp, UOp], *, l1_budget: int = L1_STAGE_BUDGET) -> UOp:
  # recursively lower each unique CALL(SINK, ...) function body once
  def lower_call_body(c: UOp) -> UOp | None:
    body = c.src[0]
    if body.op is not Ops.SINK or isinstance(body.arg, KernelArg): return None
    if (lb := call_memo.get(body)) is None:
      lb = _lower_function_body(body, l1_budget)
      call_memo[body] = call_memo[lb] = lb
    return None if lb is body else c.replace(src=(lb, *c.src[1:]))

  tsink = graph_rewrite(tsink, PatternMatcher([(UPat(Ops.CALL, name="c"), lower_call_body)]))
  tsink = graph_rewrite(tsink, pm_split_wide_max, bottom_up=True)
  tsink = run_rangeify(tsink, l1_budget=l1_budget)
  tsink = graph_rewrite(tsink, symbolic + pm_reduce_simplify + pm_const_buffer_folding)
  if l1_budget > 0: tsink = _mark_keep_staged(tsink)
  tsink = graph_rewrite(tsink, symbolic + pm_reduce_simplify + pm_const_buffer_folding + pm_remove_bufferize)
  if l1_budget > 0: tsink = _promote_l1_stages(tsink)
  tsink = graph_rewrite(tsink, pm_add_buffers, bottom_up=True)
  tsink = graph_rewrite(tsink, pm_no_indexing_calls)
  tsink = graph_rewrite(tsink, PatternMatcher([(UPat((Ops.STORE, Ops.END), name="x"), _split_store)]), bottom_up=True)
  tsink = graph_rewrite(tsink, pm_no_views)
  return tsink

def get_kernel_graph(root: UOp, *, l1_budget: int = L1_STAGE_BUDGET) -> UOp:
  """Lower a simplified Layer 0 UOp (or SINK) into a Layer 1 kernel CALL graph."""
  call_memo: dict[UOp, UOp] = {}
  if root.op is Ops.SINK:
    return _lower_one_sink(root, call_memo, l1_budget=l1_budget)
  # bare tensor value: allocate an output buffer and store into it
  sh = root.shape or ()
  dt = dtypes.i32 if root.dtype is dtypes.weakint else dtypes.fp32 if root.dtype is dtypes.weakfloat else root.dtype
  out = UOp.alloc(_max_shape(sh) if sh else (1,), dt, name="out")
  dst = out.reshape(()) if not sh else (out._mop(Ops.SHRINK, tuple((0, s) for s in sh)) if _max_shape(sh) != sh else out)
  val = root.cast(dt) if root.dtype != dt else root
  return _lower_one_sink(UOp.sink(dst.store(val)), call_memo, l1_budget=l1_budget)
