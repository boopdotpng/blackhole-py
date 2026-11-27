"""Global argmax: maximum value, then maximum reverse index for stable ties."""
import itertools
from math import prod
from ..dtype import dtypes
from ..uop import Ops, UOp
from .lower import access, affine, face_bytes, LoweredKernel
from .pipeline import instruction, compile_tile_graph
from .reduction import reduce_expression, valid_mask
from .specs import Space, NocRead, NocWrite, IndexTile, UnpackOp, MoveToDst, PackOp


def lower_argmax(kernel, args):
  store, = [u for u in kernel.toposort() if u.op is Ops.STORE]
  output, output_index = access(store.src[0])
  tail = store.src[1]
  if prod(args[output].shape) != 1 or output_index != (0, {}) or tail.op is not Ops.SUB or not tail.src[0].is_const:
    raise NotImplementedError("global argmax output")
  n, ranked = int(tail.src[0].val), tail.src[1]
  if n > 2**24 or ranked.op is not Ops.REDUCE or ranked.arg[0] is not Ops.MAX:
    raise NotImplementedError("global argmax index reduction")
  where, kr = ranked.src
  if where.op is not Ops.WHERE or not where.src[2].is_const or where.src[2].val != 0 or affine(where.src[1]) != (n, {kr: -1}):
    raise NotImplementedError("global argmax tie breaking")
  compare = where.src[0]
  if compare.op is not Ops.CMPEQ: raise NotImplementedError("global argmax comparison")
  value = next((u for u in compare.src if u.op is Ops.LOAD), None)
  maximum = next((u for u in compare.src if u.op is Ops.REDUCE), None)
  if value is None or maximum is None or maximum.arg[0] is not Ops.MAX:
    raise NotImplementedError("global argmax maximum")
  param, index = access(value.src[0])
  inner, inner_range = maximum.src
  if (index != (0, {kr: 1}) or inner.op is not Ops.LOAD or access(inner.src[0]) != (param, (0, {inner_range: 1}))
      or int(kr.src[0].val) != n or int(inner_range.src[0].val) != n):
    raise NotImplementedError("global argmax input")
  dtype = args[param].dtype
  if dtype not in (dtypes.fp32, dtypes.bf16): raise NotImplementedError("global argmax dtype")
  cb_addrs, axis = {}, itertools.count(1)
  def cb():
    index = len(cb_addrs); cb_addrs[index] = 0x20000 + index * 0x1000
    return index
  def unpack(read, cb_id, dtype, slot):
    direct = dtype is dtypes.fp32 or dtype.is_int
    loaded = instruction(UnpackOp(Space.DST if direct else Space.SRCA, cb_id, src_dtype=dtype, dst_slot=slot), read)
    return loaded if direct else instruction(MoveToDst(slot), loaded)
  outer = UOp.range(1, 0, "out")
  def load_value(u, rk):
    cb_id = cb()
    read = instruction(NocRead(param, cb_id, face_bytes(dtype)), rk * face_bytes(dtype))
    return 1, unpack(read, cb_id, dtype, 1)
  first = inner.cast(dtypes.fp32).reduce(inner_range, op=Ops.MAX)
  result = reduce_expression(first, first, outer, axis, load_value, lambda rk: valid_mask(cb(), rk, n))
  scalar_cb = cb()
  packed = instruction(PackOp(scalar_cb), result)
  scalar = UOp.param(1000, dtypes.fp32, shape=1).index(0).load()
  reverse_index = UOp.param(1001, dtypes.i32, shape=n).index(kr).load()
  ranked_float = value.cast(dtypes.fp32).eq(scalar).where(reverse_index.cast(dtypes.fp32), 0.).reduce(kr, op=Ops.MAX)
  def load_rank(u, rk):
    if u is scalar:
      return 2, unpack(UOp.noop().after(packed, rk), scalar_cb, dtypes.fp32, 2)
    if u is reverse_index:
      cb_id = cb()
      lane = UOp.special(128, "gather_lane")
      index = n - (rk * 16 + lane % 16)
      read = instruction(IndexTile(cb_id), index.cast(dtypes.i32), UOp.const(True))
      return 3, unpack(read, cb_id, dtypes.i32, 3)
    return load_value(u, rk)
  result = reduce_expression(ranked_float, (UOp.const(float(n), dtypes.fp32) - ranked_float).cast(dtypes.i32), packed, axis, load_rank,
                             lambda rk: valid_mask(cb(), rk, n))
  output_cb = cb()
  packed_output = instruction(PackOp(output_cb, dst_dtype=dtypes.i32), result)
  write = instruction(NocWrite(output, output_cb, face_bytes(dtypes.i32)), packed_output, UOp.const(0))
  return LoweredKernel(compile_tile_graph(UOp.sink(write.end(outer)), cb_addrs), 1, (8,) * len(args))
