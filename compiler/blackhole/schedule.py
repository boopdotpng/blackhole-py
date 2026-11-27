"""Schedule policy. This module does not emit executable IR."""
from dataclasses import dataclass, replace
from math import prod
from fw import L1_SIZE
from .layout import access, affine, dimensions, expression_nodes, face_bytes
from ..dtype import dtypes
from ..uop import Ops, UOp
from .fpu import MatchedMvmul, MatchedRowReduce


@dataclass(frozen=True)
class Schedule:
  grid: tuple[int, int] | None
  workers: int
  tile_m: int = 1
  tile_n: int = 1
  slab_k: int = 1
  prefetch_k: frozenset[int] = frozenset()


CB_BASE = 0x20000
CB_CAPACITY = L1_SIZE - CB_BASE


def page_bytes(size): return (size + 4095) & ~4095


def direct_weight(load, nr, k_axes, args):
  if len(k_axes) != 1 or load.op is not Ops.LOAD or len(load.src) != 1: return False
  k, = k_axes
  if not k.src[0].is_const: return False
  extent = int(k.src[0].val)
  try: slot, index = access(load.src[0])
  except NotImplementedError: return False
  rows = int(nr.src[0].val) if nr is not None else 1
  return index == (0, {k: 1, **({nr: extent} if nr is not None else {})}) and args[slot].shape == (rows, extent)


def plan_operands(matches, stores, args, static_params, columns, strides):
  oriented, weights, ordinary = {}, set(), set()

  def visit(expr, nr, axes):
    for u in expression_nodes(expr):
      if u.op is Ops.LOAD:
        ordinary.update(v for v in u.toposort() if v.op is Ops.LOAD)
      if u.op is not Ops.REDUCE: continue
      match = matches[u]
      if isinstance(match, MatchedRowReduce):
        visit(match.body, match.k_axis, (axes - {nr}) | {match.k_axis})
        continue
      a, w = match.act, match.weight
      if ((nr in a.ranges and nr not in w.ranges) or
          (nr is None and not a.ranges & axes and w.ranges & axes)):
        match = replace(match, act=match.weight, weight=match.act, m_axes=match.n_axes, n_axes=match.m_axes)
        a, w = w, a
      if u in oriented and oriented[u] != match: raise NotImplementedError("incompatible contraction domains")
      oriented[u] = match
      ordinary.update(v for v in a.toposort() if v.op is Ops.LOAD)
      if direct_weight(w, nr, match.k_axes, args): weights.add(w)
      else: ordinary.update(v for v in w.toposort() if v.op is Ops.LOAD)

  for store in stores:
    storage = store.src[0].src[0].without_after
    axis = columns
    if storage.op is Ops.ALLOC and prod(storage.shape) > 1 and storage.shape[-1] != 1:
      _, terms = affine(store.src[0].src[1])
      if len(terms) != 1: raise NotImplementedError("L1 vector stage requires one output axis")
      axis = next(iter(terms))
    visit(store.src[1], axis, (set(strides) - {columns}) | ({axis} if axis is not None else set()))

  def slots(loads):
    return {v.src[0].src[0].arg.slot for v in loads if v.src[0].src[0].op is Ops.PARAM}
  written = {s.src[0].src[0].arg.slot for s in stores if s.src[0].src[0].op is Ops.PARAM}
  return matches | oriented, (slots(weights) & set(static_params)) - written - slots(ordinary)


def invariant_axis(offset, gcols, grows):
  coordinates = {u.arg for u in offset.toposort() if u.op is Ops.SPECIAL}
  if "worker_x" not in coordinates and gcols > 1: return "x"
  if "worker_y" not in coordinates and grows > 1: return "y"
  return "local"


def select_schedule(matches, args, shape, strides, static_weights, max_workers, grid_shape, allow_mcast):
  batch, m, n = dimensions(shape)
  mf, nf = (m + 7) // 8, (n + 15) // 16
  strips = {}
  for match in matches.values():
    axis = match.k_axis if isinstance(match, MatchedRowReduce) else match.k_axes[0]
    if not axis.src[0].is_const: continue
    count = (int(axis.src[0].val) + 15) // 16
    operands = match.body.toposort() if isinstance(match, MatchedRowReduce) else (match.act, match.weight)
    for u in operands:
      if u.op is not Ops.LOAD or u.src[0].src[0].op is not Ops.PARAM: continue
      slot = u.src[0].src[0].arg.slot
      rows = 16 if isinstance(match, MatchedMvmul) and u is match.weight and slot in static_weights else 8
      strips[slot] = max(strips.get(slot, 0), page_bytes(count * face_bytes(args[slot].dtype, rows)))
  prefetch, available = set(), CB_CAPACITY
  for slot, size in sorted(strips.items()):
    if size <= available:
      prefetch.add(slot)
      available -= size
  fallback = Schedule(None, min(batch * mf * nf, max_workers), prefetch_k=frozenset(prefetch))
  if not allow_mcast or mf < 2 or nf < 2 or not 1 <= len(matches) <= 2: return fallback
  if not all(isinstance(match, MatchedMvmul) for match in matches.values()): return fallback
  nr = next((r for r, c in strides.items() if c == 1), None)
  mr = next((r for r, c in strides.items() if c == n and r is not nr), None)
  if mr is None or nr is None: return fallback
  bm, bn = (4 if mf >= 4 else 2), (4 if nf >= 4 else 2)
  slabs = []
  for match in matches.values():
    if len(match.k_axes) != 1: return fallback
    kr, = match.k_axes
    if not kr.src[0].is_const: return fallback
    k = int(kr.src[0].val)
    a, w = match.act, match.weight
    if any(u.op is not Ops.LOAD or len(u.src) != 1 for u in (a, w)): return fallback
    try: (ap, ai), (wp, wi) = access(a.src[0]), access(w.src[0])
    except NotImplementedError: return fallback
    if ap == wp or wp not in static_weights or args[ap].dtype is not dtypes.bf16: return fallback
    if ai != (0, {kr: 1, **{r: c // n * k for r, c in strides.items() if r is not nr}}): return fallback
    if wi != (0, {kr: 1, nr: k}) or args[wp].shape != (n, k): return fallback
    if dimensions(args[ap].shape) != (batch, m, k): return fallback
    slabs.append(((k + 15) // 16, bm * face_bytes(args[ap].dtype), bn * face_bytes(args[wp].dtype, 16)))
  cols = min((nf + bn - 1) // bn, grid_shape[0], max_workers)
  rows = min((mf + bm - 1) // bm, grid_shape[1], max_workers // cols)
  sk = next(s for s in (16, 8, 4, 1) if all(kf % s == 0 and max(a, w) * s <= 65536 for kf, a, w in slabs))
  return Schedule((cols, rows), cols * rows, bm, bn, sk)
