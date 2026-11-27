"""Row reductions with FP32 Dst accumulators and ordinary SFPU expression DAGs."""
from ..dtype import dtypes
from ..uop import Ops, UOp
from .specs import Space, UnpackOp, PackOp, SfpLoadOp, SfpStoreOp, SfpReduceRows, MoveToDst, NocRead, NocWrite, IndexTile
from .pipeline import instruction, compile_tile_graph
from .lower import access, face_bytes, LoweredKernel
from math import prod


def close_footprint(stores, fp): return UOp.noop().after(*stores).end(fp)


def expression_nodes(root):
  out, seen = [], set()
  def walk(u):
    if u in seen: return
    seen.add(u)
    if u.op is not Ops.LOAD:
      for source in u.src_without_body: walk(source)
    out.append(u)
  walk(root)
  return out


def valid_mask(cb_id, rk, n):
  lane = UOp.special(128, "gather_lane")
  read = instruction(IndexTile(cb_id), (rk * 16 + lane % 16 < n).cast(dtypes.i32), UOp.const(True))
  return 55, instruction(UnpackOp(Space.DST, cb_id, src_dtype=dtypes.i32, dst_slot=55), read)


def reduce_expression(reduction, tail, dependency, axis, load, mask_load=None):
  if len(reduction.src) != 2 or reduction.arg[0] not in (Ops.ADD, Ops.MAX): raise NotImplementedError("row reduction kind")
  n = int(reduction.src[1].src[0].val)
  if n % 16 and mask_load is None: raise NotImplementedError("masked row reduction tail")
  kind = "add" if reduction.arg[0] is Ops.ADD else "max"
  identity = 0. if kind == "add" else -float("inf")
  def combine(a, b): return a + b if kind == "add" else a.maximum(b)
  init_fp = UOp.range(UOp.const(1).after(dependency), next(axis), "fp")
  initialized = close_footprint([instruction(SfpStoreOp(0, sub_row=sub), UOp.const(identity, dtypes.fp32), init_fp)
                                 for sub in (0, 2, 4, 6)], init_fp)
  rk = UOp.range(UOp.const((n + 15) // 16).after(initialized), next(axis), "k")
  fp = UOp.range(UOp.const(1).after(rk), next(axis), "fp")
  loads = {u: load(u, rk) for u in expression_nodes(reduction.src[0]) if u.op is Ops.LOAD}
  mask = mask_load(rk) if n % 16 else None
  stores = []
  for sub in (0, 4):
    parts = []
    for parity in (0, 2):
      mapping = {u: instruction(SfpLoadOp(slot, sub_row=sub + parity, fmt="i32" if u.dtype.is_int else "fp32"), source, fp,
                                dtype=dtypes.i32 if u.dtype.is_int else dtypes.fp32)
                 for u, (slot, source) in loads.items()}
      value = reduction.src[0].substitute(mapping)
      if mask is not None:
        slot, source = mask
        predicate = instruction(SfpLoadOp(slot, sub_row=sub + parity, fmt="i32"), source, fp, dtype=dtypes.bool)
        value = predicate.where(value, UOp.const(identity, dtypes.fp32))
      parts.append(value)
    partial = instruction(SfpReduceRows(kind), combine(*parts), dtype=dtypes.fp32)
    previous = instruction(SfpLoadOp(0, sub_row=sub), fp, dtype=dtypes.fp32)
    result = combine(previous, partial)
    stores.extend(instruction(SfpStoreOp(0, sub_row=sub + p), result, fp) for p in (0, 2))
  accumulated = close_footprint(stores, fp).end(rk)
  tail_fp = UOp.range(UOp.const(1).after(accumulated), next(axis), "fp")
  stores = []
  for sub in (0, 4):
    value = instruction(SfpLoadOp(0, sub_row=sub), tail_fp, dtype=dtypes.fp32)
    result = tail.substitute({reduction: value})
    stores.extend(instruction(SfpStoreOp(0, sub_row=sub + p, fmt="i32" if tail.dtype.is_int else "fp32"), result, tail_fp)
                  for p in (0, 2))
  return close_footprint(stores, tail_fp)


def lower_row_reduction(kernel, args, max_workers):
  import itertools
  nodes = kernel.toposort()
  store, = [u for u in nodes if u.op is Ops.STORE]
  reduction, = [u for u in nodes if u.op is Ops.REDUCE]
  output, (base, coeff) = access(store.src[0])
  shape = args[output].shape
  if not shape or shape[-1] != 1 or base: raise NotImplementedError("row reduction output shape")
  m = shape[-2] if len(shape) > 1 else 1
  batch = prod(shape[:-2]) if len(shape) > 2 else 1
  if len(coeff) > 1 or any(c != 1 for c in coeff.values()): raise NotImplementedError("row reduction output indices")
  mr = next(iter(coeff), None)
  kr = reduction.src[1]
  n = int(kr.src[0].val)
  total = batch * ((m + 7) // 8)
  workers = min(total, max_workers)
  wid = UOp.special(workers, "worker_id")
  outer = UOp.range((total + workers - 1 - wid) // workers, 0, "out")
  row_tile = wid + outer * workers
  cb_addrs = {}
  def load(u, rk):
    param, index = access(u.src[0])
    expected = (0, {kr: 1, mr: n} if mr is not None else {kr: 1})
    if index != expected: raise NotImplementedError("row reduction load mapping")
    dtype = args[param].dtype
    cb, slot = len(cb_addrs), len(cb_addrs) + 1
    cb_addrs[cb] = 0x20000 + cb * 0x1000
    read = instruction(NocRead(param, cb, face_bytes(dtype)), (row_tile * ((n + 15) // 16) + rk) * face_bytes(dtype))
    unpack = instruction(UnpackOp(Space.DST if dtype is dtypes.fp32 else Space.SRCA, cb, src_dtype=dtype,
                                 dst_slot=slot), read)
    return slot, unpack if dtype is dtypes.fp32 else instruction(MoveToDst(slot), unpack)
  def mask_load(rk):
    cb = len(cb_addrs); cb_addrs[cb] = 0x20000 + cb * 0x1000
    return valid_mask(cb, rk, n)
  result = reduce_expression(reduction, store.src[1], outer, itertools.count(1), load, mask_load)
  out_cb = len(cb_addrs)
  cb_addrs[out_cb] = 0x20000 + out_cb * 0x1000
  packed = instruction(PackOp(out_cb, dst_dtype=args[output].dtype), result)
  write = instruction(NocWrite(output, out_cb, face_bytes(args[output].dtype)), packed, row_tile * face_bytes(args[output].dtype))
  program = compile_tile_graph(UOp.sink(write.end(outer)), cb_addrs)
  return LoweredKernel(program, workers, (8,) * len(args))
