"""Schedule policy. This module does not emit executable IR."""
from dataclasses import dataclass, field
from ..dtype import dtypes
from ..uop import Ops, UOp
from .fpu import MatchedMvmul, MatchedRowReduce, uncast


@dataclass(frozen=True)
class Schedule:
  grid: tuple[int, int] | None
  workers: int
  tile_m: int = 1
  tile_n: int = 1
  slab_k: int = 1
  prefetch_k: frozenset[int] = frozenset()
  mcast_axes: dict[UOp, str] = field(default_factory=dict)


def invariant_axis(offset, gcols, grows):
  coordinates = {u.arg for u in offset.toposort() if u.op is Ops.SPECIAL}
  if "worker_x" not in coordinates and gcols > 1: return "x"
  if "worker_y" not in coordinates and grows > 1: return "y"
  return "local"


def select_schedule(matches, args, shape, strides, static_weights, max_workers, grid_shape, allow_mcast):
  from .lower import access, face_bytes, dimensions
  batch, m, n = dimensions(shape)
  mf, nf = (m + 7) // 8, (n + 15) // 16
  strips = {}
  for match in matches.values():
    axis = match.k_axis if isinstance(match, MatchedRowReduce) else match.k_axes[0]
    if not axis.src[0].is_const: continue
    count = (int(axis.src[0].val) + 15) // 16
    operands = match.body.toposort() if isinstance(match, MatchedRowReduce) else (uncast(match.act), uncast(match.weight))
    for u in operands:
      if u.op is not Ops.LOAD or u.src[0].src[0].op is not Ops.PARAM: continue
      slot = u.src[0].src[0].arg.slot
      rows = 16 if isinstance(match, MatchedMvmul) and u is uncast(match.weight) and slot in static_weights else 8
      strips[slot] = max(strips.get(slot, 0), (count * face_bytes(args[slot].dtype, rows) + 4095) & ~4095)
  prefetch, available = set(), 0x140000
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
  slabs, axes = [], {}
  for match in matches.values():
    if len(match.k_axes) != 1: return fallback
    kr, = match.k_axes
    if not kr.src[0].is_const: return fallback
    k = int(kr.src[0].val)
    a, w = uncast(match.act), uncast(match.weight)
    if nr in a.ranges and nr not in w.ranges: a, w = w, a
    if any(u.op is not Ops.LOAD or len(u.src) != 1 for u in (a, w)): return fallback
    try: (ap, ai), (wp, wi) = access(a.src[0]), access(w.src[0])
    except NotImplementedError: return fallback
    if ap == wp or wp not in static_weights or args[ap].dtype is not dtypes.bf16: return fallback
    if ai != (0, {kr: 1, **{r: c // n * k for r, c in strides.items() if r is not nr}}): return fallback
    if wi != (0, {kr: 1, nr: k}) or args[wp].shape != (n, k): return fallback
    if dimensions(args[ap].shape) != (batch, m, k): return fallback
    slabs.append(((k + 15) // 16, bm * face_bytes(args[ap].dtype), bn * face_bytes(args[wp].dtype, 16)))
    axes[a], axes[w] = "x", "y"
  cols = min((nf + bn - 1) // bn, grid_shape[0], max_workers)
  rows = min((mf + bm - 1) // bm, grid_shape[1], max_workers // cols)
  sk = next(s for s in (16, 8, 4, 1) if all(kf % s == 0 and max(a, w) * s <= 65536 for kf, a, w in slabs))
  return Schedule((cols, rows), cols * rows, bm, bn, sk, mcast_axes=axes)
