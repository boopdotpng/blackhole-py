"""Layer-1 scalar kernels to abstract Blackhole face operations."""
from dataclasses import dataclass
from functools import cache
from math import prod
import os
from ..dtype import dtypes
from ..uop import Ops, UOp
from .alloc import TileAllocator
from .pipeline import instruction, compile_tile_graph
from .specs import Space, UnpackOp, PackOp, SfpLoadOp, SfpStoreOp, FpuOp, NocRead, NocWrite, DstZero, MoveToDst


def affine(u, symbolic=False):
  if u.is_const: return int(u.val), {}
  if symbolic and u.is_variable: return u, {}
  if u.op is Ops.RANGE: return 0, {u: 1}
  if u.op is Ops.CAST and u.dtype.is_int: return affine(u.src[0], symbolic)
  if u.op in (Ops.ADD, Ops.SUB):
    a, av = affine(u.src[0], symbolic); b, bv = affine(u.src[1], symbolic)
    sign = -1 if u.op is Ops.SUB else 1
    return a + sign * b, {k: v for k in av.keys() | bv.keys() if (v := av.get(k, 0) + sign * bv.get(k, 0))}
  if u.op is Ops.MUL:
    a, av = affine(u.src[0], symbolic); b, bv = affine(u.src[1], symbolic)
    if not av: return a * b, {k: a * v for k, v in bv.items()}
    if not bv: return a * b, {k: b * v for k, v in av.items()}
  raise NotImplementedError(f"non-affine address: {u.op}")


def access(u):
  if u.op is not Ops.INDEX or len(u.src) != 2 or u.src[0].op is not Ops.PARAM:
    raise NotImplementedError("expected flat PARAM indexing")
  return u.src[0].arg.slot, affine(u.src[1])


def face_bytes(dtype, rows=8):
  if dtype in (dtypes.bfp8, dtypes.bfp4): return 16 + rows * 16 * dtype.bits // 8
  return rows * 16 * dtype.itemsize


@dataclass(frozen=True)
class LoweredKernel:
  program: UOp
  workers: int
  face_rows: tuple[int, ...]
  grid: tuple[int, int] | None = None


def lower_kernel(kernel, args, max_workers=139, grid_shape=(13, 10)):
  if max_workers < 1 or min(grid_shape) < 1: raise ValueError("worker counts and grid dimensions must be positive")
  # Code depends on layout/type/provenance, not on which layer owns its data.
  signature = tuple(arg.param_like(i) if arg.is_variable else UOp.param(i, arg.dtype, shape=arg.shape) for i, arg in enumerate(args))
  return _lower_kernel(kernel, signature, max_workers, grid_shape, os.environ.get("BH_MCAST", "1") != "0",
                       tuple(i for i, arg in enumerate(args) if arg.op is not Ops.ALLOC and not arg.is_variable),
                       max(1, int(os.environ.get("BH_CB_DEPTH", "3"))))


@cache
def _lower_kernel(kernel, args, max_workers, grid_shape, mcast, static_params=(), cb_depth=3):
  from .fpu import match_reductions, MatchedMvmul
  stages = normalize_stages(kernel)
  normalized = UOp.sink(*stages)
  matches = match_reductions(normalized)
  weights = {m.weight for m in matches.values() if isinstance(m, MatchedMvmul)}
  from .fpu import uncast
  weights = {uncast(w) for w in weights}
  written = {s.src[0].src[0].arg.slot for s in stages if s.src[0].src[0].op is Ops.PARAM}
  static_weights = tuple(slot for slot in static_params if slot not in written and all(u in weights for u in normalized.toposort()
                         if u.op is Ops.LOAD and u.src[0].src[0].op is Ops.PARAM and u.src[0].src[0].arg.slot == slot))
  return TileLowerer(stages, args, matches, max_workers, static_weights, grid_shape, mcast, cb_depth).run()


def dimensions(shape):
  return (prod(shape[:-2]) if len(shape) > 2 else 1, shape[-2] if len(shape) > 1 else 1, shape[-1] if shape else 1)


def expression_nodes(root):
  out, seen = [], set()
  def walk(u):
    if u in seen: return
    seen.add(u)
    if u.op not in (Ops.LOAD, Ops.REDUCE):
      for source in u.src_without_body: walk(source)
    out.append(u)
  walk(root)
  return out


def normalize_stages(kernel):
  stores = [u for u in kernel.toposort() if u.op is Ops.STORE]
  vectors = {}
  for store in stores:
    storage = store.src[0].src[0].without_after
    if storage.op is not Ops.ALLOC or prod(storage.shape) <= 1: continue
    if any(u.op is Ops.REDUCE for u in expression_nodes(store.src[1])): continue
    base, coeff = affine(store.src[0].src[1])
    if base == 0 and len(coeff) == 1 and next(iter(coeff.values())) == 1:
      vectors[storage] = next(iter(coeff)), store.src[1]
  def inline(value):
    mapping = {}
    for u in expression_nodes(value):
      if u.op is Ops.REDUCE:
        mapping[u] = u.replace(src=(inline(u.src[0]), *u.src[1:]))
      if u.op is Ops.LOAD and u.src[0].src[0].without_after in vectors:
        axis, body = vectors[u.src[0].src[0].without_after]
        mapping[u] = inline(body.substitute({axis: u.src[0].src[1]}))
    return value.substitute(mapping)
  return tuple(store.replace(src=(store.src[0], inline(store.src[1]))) for store in stores
               if store.src[0].src[0].without_after not in vectors)


class TileLowerer:
  """One expression walker for maps, reductions, contractions, and L1 stages."""
  def __init__(self, stores, args, matches, max_workers, static_weights, grid_shape, mcast, cb_depth=3):
    import itertools
    self.args, self.matches, self.stores, self.cb_depth = args, matches, stores, cb_depth
    self.alloc, self.axis, self.stages = TileAllocator(deferred=True), itertools.count(1), {}
    self.layouts = [8] * len(args)
    self.static_weights = static_weights
    final = next(s for s in reversed(stores) if s.src[0].src[0].without_after.op is Ops.PARAM)
    self.output = final.src[0].src[0].arg.slot
    base, coeff = affine(final.src[0].src[1], symbolic=True)
    axes = sorted(coeff, key=coeff.get, reverse=True)
    domain = tuple(int(r.src[0].val) for r in axes)
    self.strides = {r: prod(domain[i + 1:]) for i, r in enumerate(axes)}
    self.full = isinstance(base, int) and base == 0 and coeff == self.strides and prod(domain) == prod(args[self.output].shape)
    self.batch, self.m, self.n = dimensions(args[self.output].shape if self.full else domain)
    self.mf, self.nf = (self.m + 7) // 8, (self.n + 15) // 16
    for store in stores:
      if store.src[0].src[0].without_after.op is Ops.PARAM and store is not final:
        if store.src[0].src[1] is not final.src[0].src[1] or args[store.src[0].src[0].arg.slot].shape != args[self.output].shape:
          raise NotImplementedError("incompatible multi-output domains")
    total = self.batch * self.mf * self.nf
    self.workers = min(total, max_workers)
    wid = UOp.special(self.workers, "worker_id")
    self.outer = UOp.range((total + self.workers - 1 - wid) // self.workers, 0, "out")
    self.tile = wid + self.outer * self.workers
    from .schedule import select_schedule
    self.schedule = select_schedule(matches, args, args[self.output].shape, self.strides, static_weights,
                                    max_workers, grid_shape, mcast and self.full and len(stores) == 1)
    self.block_index = 0
    if self.schedule.grid:
      cols, rows = self.schedule.grid
      bm, bn = self.schedule.tile_m, self.schedule.tile_n
      self.om_count, self.on_count = (self.mf + bm * rows - 1) // (bm * rows), (self.nf + bn * cols - 1) // (bn * cols)
      self.batch_id = UOp.range(self.batch, next(self.axis), "batch") if self.batch > 1 else UOp.const(0)
      self.om = UOp.range(UOp.const(self.om_count).after(self.batch_id), next(self.axis), "om")
      self.on = UOp.range(UOp.const(self.on_count).after(self.om), next(self.axis), "on")
      self.row = (UOp.special(rows, "worker_y") + self.om * rows) * bm
      self.col = (UOp.special(cols, "worker_x") + self.on * cols) * bn
      self.tile = (self.batch_id * self.mf + self.row) * self.nf + self.col
      self.outer = self.on
      self.workers = self.schedule.workers
    self.dependency = self.outer
    self.bound = {}
    self.context, self.broadcast = None, set()

  def coordinates(self, lane=None):
    lane = UOp.special(128, "gather_lane") if lane is None else lane
    row = self.tile // self.nf % self.mf * 8 + lane // 16
    col = self.tile % self.nf * 16 + lane % 16
    logical = (self.tile // (self.mf * self.nf) * self.m + row) * self.n + col % self.n
    indices = {r: logical // stride % int(r.src[0].val) for r, stride in self.strides.items()}
    return indices, (row < self.m) & (col < self.n)

  def to_space(self, source, cb, dtype, target=Space.DST, slot=None, rows=8, faces=1, face_stride=0, offset=None):
    """Shared L1 -> Src / Dst transitions; machine instructions stay in recipes."""
    operands = (source,) if offset is None else (source, offset)
    if target is not Space.DST:
      return instruction(UnpackOp(target, cb, src_dtype=dtype, rows=rows, faces=faces, face_stride=face_stride), *operands)
    slot = self.alloc.dst() if slot is None else slot
    direct = dtype is dtypes.fp32 or dtype.is_int
    unpack = instruction(UnpackOp(Space.DST if direct else Space.SRCA, cb, src_dtype=dtype, dst_slot=slot), *operands)
    return slot, unpack if direct else instruction(MoveToDst(slot), unpack)

  def gather(self, u, indices, valid, cb, lanes=128):
    from .specs import NocGather
    address = u.src[0]
    storage = address.src[0].without_after
    if storage.op is not Ops.PARAM: raise NotImplementedError("non-DRAM gather")
    param, dtype = storage.arg.slot, storage.dtype
    if dtype not in (dtypes.bf16, dtypes.fp32, dtypes.i32, dtypes.u32): raise NotImplementedError(f"gather dtype {dtype}")
    _, sm, sn = dimensions(self.args[param].shape)
    index = address.src[1].substitute(indices)
    sr, sc = index // sn % sm, index % sn
    face = (index // (sm * sn) * ((sm + 7) // 8) + sr // 8) * ((sn + 15) // 16) + sc // 16
    offset = (face * 128 + sr % 8 * 16 + sc % 16) * dtype.itemsize
    predicate = valid & (index >= 0) & (index < prod(self.args[param].shape))
    if len(u.src) > 1:
      if not u.src[1].is_const or u.src[1].val != 0: raise NotImplementedError("nonzero masked load default")
      predicate = predicate & u.src[2].substitute(indices)
    layouts = []
    for inner in address.src[1].toposort():
      if inner.op is not Ops.LOAD: continue
      source = inner.src[0].src[0]
      if source.op is not Ops.PARAM or not inner.dtype.is_int: raise NotImplementedError("non-integer indirect index")
      _, im, inn = dimensions(self.args[source.arg.slot].shape)
      layouts.append((source.arg.slot, prod(source.shape), im, inn, source.dtype.itemsize))
    return instruction(NocGather(param, cb, dtype.itemsize, tuple(layouts), lanes=lanes), offset.after(self.dependency), predicate)

  def load(self, u, indices, valid):
    storage = u.src[0].src[0].without_after
    if storage.op is Ops.ALLOC:
      cb, producer, width = self.stages[storage]
      offset = None
      if width > 1:
        scalar_indices, _ = self.coordinates(UOp.const(0))
        if self.context is not None:
          axis, column, _ = self.context
          scalar_indices[axis] = column * 16
        index = u.src[0].src[1].substitute(scalar_indices)
        offset = index // 16 * face_bytes(storage.dtype)
      return self.to_space(UOp.noop().after(producer, self.dependency, *indices.values()), cb, storage.dtype, offset=offset)
    param, dtype = storage.arg.slot, storage.dtype
    try: index = access(u.src[0])[1]
    except NotImplementedError: index = None
    nr = next((r for r, stride in self.strides.items() if stride == 1 and int(r.src[0].val) == self.n), None)
    cr, column, width = self.context if self.context else (nr, self.tile % self.nf, self.n)
    row_terms = {r: stride // self.n * width for r, stride in self.strides.items() if r is not nr}
    normal = (0, {**row_terms, **({cr: 1} if cr is not None else {})})
    broadcast = cr is not None and index == (0, {cr: 1}) and dimensions(self.args[param].shape) == (1, 1, width)
    direct = index == normal and dimensions(self.args[param].shape) == (self.batch, self.m, width)
    if len(u.src) == 1 and (direct or broadcast):
      size, count = face_bytes(dtype), (width + 15) // 16
      row = UOp.const(0) if broadcast else self.tile // self.nf
      # Burst transfers belong outside the K loop, with local face selection.
      prefetch = self.context is not None and param in self.schedule.prefetch_k and self.alloc.next_addr + ((count * size + 4095) & ~4095) <= 0x160000
      cb = self.alloc.cb(size * (count if prefetch else 1))
      offset = row * count * size if prefetch else (row * count + column) * size
      if self.schedule.grid: offset = (self.tile < self.batch * self.mf * self.nf).where(offset, 0)
      read = instruction(NocRead(param, cb, size * (count if prefetch else 1)),
                         offset.after(self.reduction_init if prefetch else self.dependency))
      slot, producer = self.to_space(read, cb, dtype, offset=column * size if prefetch else UOp.const(0))
      if broadcast: self.broadcast.add(slot)
      return slot, producer
    cb = self.alloc.cb(face_bytes(dtype))
    return self.to_space(self.gather(u, indices, valid, cb), cb, dtype)

  def sfpu(self, expression, indices, valid, fp, sub, loaded):
    from .specs import IndexTile
    mapping = {}
    for u in expression_nodes(expression):
      if u.op is Ops.REDUCE:
        slot, producer = self.bound[u]
        from .fpu import MatchedMvmul
        if isinstance(self.matches[u], MatchedMvmul): slot += self.block_index
        value = instruction(SfpLoadOp(slot, sub_row=sub), producer, fp, dtype=dtypes.fp32)
        mapping[u] = value.cast(u.dtype) if u.dtype.is_int else value
      elif u.op is Ops.LOAD:
        if u not in loaded: loaded[u] = self.load(u, indices, valid)
        slot, producer = loaded[u]
        value = instruction(SfpLoadOp(slot, sub_row=sub % 4 if slot in self.broadcast else sub, fmt="i32" if u.dtype.is_int else "fp32"), producer, fp,
                            dtype=dtypes.i32 if u.dtype.is_int else dtypes.fp32)
        if slot in self.broadcast:
          from .specs import SfpBroadcastRows
          value = instruction(SfpBroadcastRows(), value, dtype=value.dtype)
        mapping[u] = value
    def collect(u):
      if u.op in (Ops.LOAD, Ops.REDUCE): return
      descendants = u.toposort()
      if (u.dtype.is_int or u.dtype is dtypes.bool) and any(n.op is Ops.RANGE or n.is_variable for n in descendants):
        if all(n.op not in (Ops.LOAD, Ops.REDUCE) and (n.op is not Ops.RANGE or n in indices) for n in descendants):
          if u not in loaded:
            cb = self.alloc.cb()
            read = instruction(IndexTile(cb), u.substitute(indices).cast(dtypes.i32).after(self.dependency), valid)
            loaded[u] = self.to_space(read, cb, dtypes.i32)
          slot, producer = loaded[u]
          value = instruction(SfpLoadOp(slot, sub_row=sub, fmt="i32"), producer, fp, dtype=dtypes.i32)
          mapping[u] = value.bitcast(dtypes.bool) if u.dtype is dtypes.bool else value
          return
      for source in u.src_without_body: collect(source)
    collect(expression)
    return expression.substitute(mapping)

  def reduce(self, match):
    from .specs import SfpReduceRows, IndexTile
    red = match.reduce_uop
    if red in self.bound: return
    from .fpu import MatchedMvmul
    if isinstance(match, MatchedMvmul): return self.mvmul(match)
    kr = match.k_axis
    dependent = []
    for nested in expression_nodes(red.src[0]):
      if nested.op is not Ops.REDUCE: continue
      if kr in nested.ranges:
        if not isinstance(self.matches[nested], MatchedMvmul):
          raise NotImplementedError("dependent nested row reduction requires a tile transpose")
        dependent.append(nested)
      else: self.reduce(self.matches[nested])
    extent = kr.src[0]
    width = int(extent.val if extent.is_const else extent.vmax)
    if red.dtype.is_int:
      lo, hi = red.src[0].vmin, red.src[0].vmax
      bound = max(abs(lo), abs(hi)) * (width if match.op is Ops.ADD else 1)
      if bound > 2**24: raise NotImplementedError("integer reduction exceeds exact fp32 range")
    slot = self.alloc.dst()
    identity = 0. if match.op is Ops.ADD else -float("inf")
    def combine(a, b): return a + b if match.op is Ops.ADD else a.maximum(b)
    def close(stores, fp): return UOp.noop().after(*stores).end(fp)
    fp = UOp.range(UOp.const(1).after(self.dependency), next(self.axis), "fp")
    init = close([instruction(SfpStoreOp(slot, sub_row=sub), UOp.const(identity, dtypes.fp32), fp) for sub in (0, 2, 4, 6)], fp)
    rk = UOp.range(UOp.const((width + 15) // 16).after(init), next(self.axis), "k")
    self.dependency = rk
    self.context, self.reduction_init = (kr, rk, width), init
    dependent_slots = []
    for nested in dependent:
      old_n, old_nf, old_tile, old_strides = self.n, self.nf, self.tile, self.strides
      nr = next((r for r, stride in old_strides.items() if stride == 1 and int(r.src[0].val) == old_n), None)
      self.n, self.nf = width, (width + 15) // 16
      self.tile = old_tile // old_nf * self.nf + rk
      self.strides = {**{r: stride // old_n * width for r, stride in old_strides.items() if r is not nr}, kr: 1}
      previous_bindings = set(self.bound)
      self.reduce(self.matches[nested])
      dependent_slots.extend(u for u in self.bound if u not in previous_bindings)
      self.n, self.nf, self.tile, self.strides = old_n, old_nf, old_tile, old_strides
    self.context, self.reduction_init = (kr, rk, width), init
    indices, valid = self.coordinates()
    indices[kr] = rk * 16 + UOp.special(128, "gather_lane") % 16
    # Output-column padding is irrelevant while traversing a reduction row.
    valid = indices[kr] < extent
    fp = UOp.range(UOp.const(1).after(self.dependency), next(self.axis), "fp")
    loaded, stores = {}, []
    mask = None
    if width % 16 or not extent.is_const:
      cb = self.alloc.cb()
      mask = self.to_space(instruction(IndexTile(cb), valid.cast(dtypes.i32), UOp.const(True)), cb, dtypes.i32)
    for sub in (0, 4):
      parts = []
      for parity in (0, 2):
        value = self.sfpu(red.src[0], indices, valid, fp, sub + parity, loaded).cast(dtypes.fp32)
        if mask:
          mask_slot, producer = mask
          gate = instruction(SfpLoadOp(mask_slot, sub_row=sub + parity, fmt="i32"), producer, fp, dtype=dtypes.bool)
          value = gate.where(value, UOp.const(identity, dtypes.fp32))
        parts.append(value)
      partial = instruction(SfpReduceRows("add" if match.op is Ops.ADD else "max"), combine(*parts), dtype=dtypes.fp32)
      previous = instruction(SfpLoadOp(slot, sub_row=sub), fp, dtype=dtypes.fp32)
      result = combine(previous, partial)
      stores.extend(instruction(SfpStoreOp(slot, sub_row=sub + p), result, fp) for p in (0, 2))
    self.dependency = close(stores, fp).end(rk)
    self.bound[red] = slot, self.dependency
    for scratch, _ in loaded.values(): self.alloc.release_dst(scratch)
    if mask: self.alloc.release_dst(mask[0])
    for nested in dependent_slots:
      self.alloc.release_dst(self.bound.pop(nested)[0])
    self.context = None
    self.broadcast.clear()

  def mvmul(self, match):
    if self.schedule.grid: return self.mcast_mvmul(match)
    from .fpu import uncast
    if len(match.k_axes) != 1: raise NotImplementedError("multi-axis MVMUL")
    kr, = match.k_axes
    extent = kr.src[0]
    k = int(extent.val if extent.is_const else extent.vmax)
    kf = (k + 15) // 16
    act, weight = uncast(match.act), uncast(match.weight)
    nr = next((r for r, stride in self.strides.items() if stride == 1 and int(r.src[0].val) == self.n), None)
    if nr in act.ranges and nr not in weight.ranges: act, weight = weight, act
    elif nr is None and not (act.ranges & self.strides.keys()) and weight.ranges & self.strides.keys():
      act, weight = weight, act
    if any(u.op is not Ops.LOAD or u.src[0].src[0].op is not Ops.PARAM for u in (act, weight)):
      raise NotImplementedError("fused MVMUL prologue")
    a_slot, w_slot = act.src[0].src[0].arg.slot, weight.src[0].src[0].arg.slot
    a_dtype, w_dtype = self.args[a_slot].dtype, self.args[w_slot].dtype
    if dtypes.fp32 in (a_dtype, w_dtype): raise NotImplementedError("MVMUL fp32 operands require conversion; TF32 unpack is not enabled")
    slot = self.alloc.dst()
    if self.dependency is self.outer: zero = instruction(DstZero(), self.outer)
    else:
      fp = UOp.range(UOp.const(4).after(self.dependency), next(self.axis), "fp")
      zero = instruction(SfpStoreOp(slot), UOp.const(0., dtypes.fp32), fp).end(fp)
    self.dependency = zero
    rk = UOp.range(UOp.const(kf).after(zero), next(self.axis), "k")
    expected_a = (0, {kr: 1, **{r: stride // self.n * k for r, stride in self.strides.items() if r is not nr}})
    try: direct_a = access(act.src[0])[1] == expected_a and dimensions(self.args[a_slot].shape) == (self.batch, self.m, k)
    except NotImplementedError: direct_a = False
    try: direct_w = (w_slot in self.static_weights and access(weight.src[0])[1] == (0, {kr: 1, **({nr: k} if nr else {})})
                     and self.args[w_slot].shape == (self.n, k))
    except NotImplementedError: direct_w = False
    if not extent.is_const: direct_a = direct_w = False
    if direct_w: self.layouts[w_slot] = 16
    inputs = []
    for operand, param, dtype, rows, direct, target in ((act, a_slot, a_dtype, 8, direct_a, Space.SRCB),
                                                       (weight, w_slot, w_dtype, 16, direct_w, Space.SRCA)):
      size = face_bytes(dtype, rows)
      if direct:
        face_row = self.tile // self.nf if rows == 8 else self.tile % self.nf
        prefetch = param in self.schedule.prefetch_k and self.alloc.next_addr + ((kf * size + 4095) & ~4095) <= 0x160000
        cb = self.alloc.cb(size * (kf if prefetch else 1))
        offset = face_row * kf * size if prefetch else (face_row * kf + rk) * size
        read = instruction(NocRead(param, cb, size * (kf if prefetch else 1)), offset.after(zero))
        unpack = self.to_space(read, cb, dtype, target, rows=rows, offset=rk * size if prefetch else UOp.const(0))
      else:
        cb = self.alloc.cb(size)
        lane = UOp.special(rows * 16, "gather_lane")
        indices, _ = self.coordinates(lane if rows == 8 else lane % 16)
        kval = rk * 16 + (lane % 16 if rows == 8 else lane // 16)
        indices[kr] = kval
        row = self.tile // self.nf % self.mf * 8 + lane // 16
        col = self.tile % self.nf * 16 + lane % 16
        valid = (kval < extent) & ((row < self.m) if rows == 8 else (col < self.n))
        read = self.gather(operand, indices, valid, cb, rows * 16)
        unpack = self.to_space(read, cb, dtype, target, rows=rows)
      inputs.append(unpack)
    value = instruction(FpuOp("MVMUL", fidelity=match.rule.fidelity(w_dtype), dst_slot=slot, src_dtype=w_dtype, accumulate=True),
                        *inputs, dtype=dtypes.fp32).end(rk)
    self.dependency = value
    self.bound[match.reduce_uop] = slot, value


  def mcast_mvmul(self, match):
    from .fpu import uncast
    from .schedule import invariant_axis
    from .specs import NocMcastRead, NocMcastForward, McastWait, McastConsumed, McastRelease
    act, weight = uncast(match.act), uncast(match.weight)
    nr = next(r for r, stride in self.strides.items() if stride == 1)
    if nr in act.ranges and nr not in weight.ranges: act, weight = weight, act
    a, w = act.src[0].src[0].arg.slot, weight.src[0].src[0].arg.slot
    kf = (int(match.k_axes[0].src[0].val) + 15) // 16
    cols, rows = self.schedule.grid
    bm, bn, sk = self.schedule.tile_m, self.schedule.tile_n, self.schedule.slab_k
    slot = self.alloc.dst(bm * bn)
    rid = len(self.bound)
    self.layouts[w] = 16
    if rid == 0: zero = instruction(DstZero(), self.dependency)
    else: zero = self.dependency  # DstZero initialized all accumulator blocks
    slabs = kf // sk
    slab = UOp.range(UOp.const(slabs).after(zero), next(self.axis), "slab")
    seq = ((self.batch_id * self.om_count + self.om) * self.on_count + self.on) * slabs + slab
    kl = UOp.range(sk, next(self.axis), "k")
    inputs, streams = [], []
    for which, (param, first, max_faces, blocks, height, target) in enumerate(
        ((a, self.row, self.mf, bm, 8, Space.SRCB), (w, self.col, self.nf, bn, 16, Space.SRCA))):
      dtype = self.args[param].dtype
      size = face_bytes(dtype, height)
      batch_face = self.batch_id * max_faces if which == 0 else UOp.const(0)
      offset = ((batch_face + first) * kf + slab * sk) * size
      axis = invariant_axis(offset, cols, rows)
      stride = (blocks * sk * size + 63) & ~63
      cb = self.alloc.cb(stride * 2)
      spec = NocMcastRead(param, cb, axis, cols, rows, blocks, sk * size, kf * size,
                          stride, 2 * rid + which, self.batch * self.om_count * self.on_count * slabs,
                          tid_mcast=3 if axis == "y" else 2)
      read = instruction(spec, offset, first, UOp.const(max_faces), seq)
      if axis == "y": read = instruction(NocMcastForward(spec), read, seq)
      ready = instruction(McastWait(spec.ctrl_id), read, seq)
      inputs.append(self.to_space(ready, cb, dtype, target, rows=height, faces=blocks, face_stride=sk * size,
                                  offset=(seq % 2) * stride + kl * size))
      streams.append(spec)
    value = instruction(FpuOp("MVMUL", m_blocks=bm, n_blocks=bn, fidelity=match.rule.fidelity(self.args[w].dtype),
                              dst_slot=slot, src_dtype=self.args[w].dtype, accumulate=True), *inputs).end(kl)
    for spec in streams:
      value = instruction(McastRelease(spec), instruction(McastConsumed(spec.ctrl_id), value, seq), seq)
    self.dependency = value.end(slab)
    self.bound[match.reduce_uop] = slot, self.dependency

  def run(self):
    from .specs import NocScatter
    for store in self.stores:
      storage = store.src[0].src[0].without_after
      vector_stage = storage.op is Ops.ALLOC and prod(storage.shape) > 1 and storage.shape[-1] != 1
      stage_loop = None
      width = 1
      if vector_stage:
        base, terms = affine(store.src[0].src[1])
        if base or len(terms) != 1 or next(iter(terms.values())) != 1:
          raise NotImplementedError("L1 vector stage requires contiguous row indexing")
        stage_axis = next(iter(terms))
        width = int(stage_axis.src[0].val)
        saved = self.n, self.nf, self.tile, self.strides
        nr = next((r for r, stride in self.strides.items() if stride == 1 and int(r.src[0].val) == self.n), None)
        self.strides = {**{r: stride // self.n * width for r, stride in self.strides.items() if r is not nr}, stage_axis: 1}
        row_tile = self.tile // self.nf
        self.n, self.nf = width, (width + 15) // 16
        stage_loop = UOp.range(UOp.const(self.nf).after(self.dependency), next(self.axis), "stage")
        self.tile, self.dependency = row_tile * self.nf + stage_loop, stage_loop
      self.bound = {}
      self.broadcast.clear()
      for u in expression_nodes(store.src[1]):
        if u.op is Ops.REDUCE: self.reduce(self.matches[u])
      from .fpu import uncast
      bm, bn = self.schedule.tile_m, self.schedule.tile_n
      tail = uncast(store.src[1])
      loaded = {}
      if tail in self.bound and not tail.dtype.is_int:
        out_slot, result = self.bound[tail]
      else:
        out_slot = self.alloc.dst(bm * bn)
        base_tile = self.tile
        for r in range(bm):
          for c in range(bn):
            self.block_index = r * bn + c
            self.tile = base_tile + r * self.nf + c
            indices, valid = self.coordinates()
            results, block_loads = [], {}
            fp = UOp.range(UOp.const(1).after(self.dependency), next(self.axis), "fp")
            for sub in (0, 2, 4, 6):
              value = self.sfpu(store.src[1], indices, valid, fp, sub, block_loads)
              results.append(instruction(SfpStoreOp(out_slot + self.block_index, sub_row=sub,
                                                   fmt="i32" if store.src[1].dtype.is_int else "fp32"), value, fp))
            self.dependency = UOp.noop().after(*results).end(fp)
            for scratch, _ in block_loads.values(): self.alloc.release_dst(scratch)
            self.broadcast.clear()
        self.tile, self.block_index = base_tile, 0
        result = self.dependency
      indices, valid = self.coordinates()
      storage = store.src[0].src[0].without_after
      cb = self.alloc.cb((self.nf if vector_stage else bm * bn) * face_bytes(storage.dtype))
      pack_src = (result, stage_loop * face_bytes(storage.dtype)) if vector_stage else (result,)
      packed = instruction(PackOp(cb, dst_dtype=storage.dtype, dst_slot=out_slot, blocks=bm * bn), *pack_src)
      self.dependency = packed
      if storage.op is Ops.ALLOC:
        if vector_stage:
          self.dependency = packed.end(stage_loop)
          self.n, self.nf, self.tile, self.strides = saved
        self.stages[storage] = cb, self.dependency, width
      elif self.schedule.grid:
        self.dependency = instruction(NocWrite(storage.arg.slot, cb, face_bytes(storage.dtype), blocks=(bm, bn), shape_faces=(self.mf, self.nf)),
                                      packed, self.row, self.col, self.batch_id)
      elif self.full:
        self.dependency = instruction(NocWrite(storage.arg.slot, cb, face_bytes(storage.dtype)), packed, self.tile * face_bytes(storage.dtype))
      else:
        _, om, onn = dimensions(self.args[storage.arg.slot].shape)
        index = store.src[0].src[1].substitute(indices)
        rr, cc = index // onn % om, index % onn
        face = (index // (om * onn) * ((om + 7) // 8) + rr // 8) * ((onn + 15) // 16) + cc // 16
        offset = (face * 128 + rr % 8 * 16 + cc % 16) * storage.dtype.itemsize
        self.dependency = instruction(NocScatter(storage.arg.slot, cb, storage.dtype.itemsize), packed, offset, valid)
      for slot in {out_slot, *(v[0] for v in self.bound.values()), *(v[0] for v in loaded.values())}: self.alloc.release_dst(slot)
    result = self.dependency.end(self.outer)
    if self.schedule.grid:
      result = result.end(self.om)
      if self.batch > 1: result = result.end(self.batch_id)
    return LoweredKernel(compile_tile_graph(UOp.sink(result), self.alloc.cb_addrs, self.alloc.cb_sizes, cb_depth=self.cb_depth),
                         self.workers, tuple(self.layouts), self.schedule.grid)
