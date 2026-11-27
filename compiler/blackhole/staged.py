"""Compose scalar row stages and elementwise tails in one tile DAG."""
import itertools
from math import prod
from ..dtype import dtypes
from ..uop import Ops, UOp
from .lower import affine, face_bytes, LoweredKernel
from .pipeline import instruction, compile_tile_graph
from .reduction import expression_nodes, close_footprint, reduce_expression, valid_mask
from .specs import Space, NocRead, NocWrite, UnpackOp, PackOp, MoveToDst, SfpLoadOp, SfpStoreOp, SfpBroadcastRows


def address(u):
  if u.op is not Ops.INDEX or len(u.src) != 2: raise NotImplementedError("staged kernel address")
  return u.src[0].without_after, affine(u.src[1])


def lower_staged(kernel, args, max_workers):
  stores = [u for u in kernel.toposort() if u.op is Ops.STORE]
  # A row-vector temporary can be recomputed at each requested column. Keep
  # scalar reductions in L1, but fuse vector stages into their consumers so
  # they do not require a whole-row allocation or a second scheduling pass.
  vector_stages = {}
  for store in stores:
    storage, (offset, index) = address(store.src[0])
    if storage.op is Ops.ALLOC and prod(storage.shape) > 1:
      if offset or len(index) != 1 or next(iter(index.values())) != 1:
        raise NotImplementedError("vector stage address")
      vector_stages[storage] = next(iter(index)), store.src[1]
  def inline(root):
    mapping = {}
    for u in expression_nodes(root):
      if u.op is not Ops.LOAD: continue
      storage, _ = address(u.src[0])
      if storage in vector_stages:
        axis_range, value = vector_stages[storage]
        mapping[u] = inline(value.substitute({axis_range: u.src[0].src[1]}))
    return root.substitute(mapping)
  stores = [store.replace(src=(store.src[0], inline(store.src[1]))) for store in stores
            if address(store.src[0])[0] not in vector_stages]
  if len(stores) == 1:
    from .lower import lower_kernel
    return lower_kernel(UOp.sink(stores[0]), args, max_workers)
  final = stores[-1]
  output, (base, coeff) = address(final.src[0])
  if output.op is not Ops.PARAM or base: raise NotImplementedError("staged kernel output")
  shape = args[output.arg.slot].shape
  n = shape[-1]
  m = shape[-2] if len(shape) > 1 else 1
  batch = prod(shape[:-2]) if len(shape) > 2 else 1
  if batch > 1 and m > 1: raise NotImplementedError("batched multi-row staged output")
  nr = next((r for r, c in coeff.items() if c == 1), None)
  mr = next((r for r, c in coeff.items() if c == n and r is not nr), None)
  if any(r not in (mr, nr) for r in coeff): raise NotImplementedError("staged output indices")
  nf = (n + 15) // 16
  total = batch * ((m + 7) // 8) * nf
  workers = min(max_workers, total)
  wid = UOp.special(workers, "worker_id")
  outer = UOp.range((total + workers - 1 - wid) // workers, 0, "out")
  tile = wid + outer * workers
  row_tile, column_tile = tile // nf, tile % nf
  axis, cb_addrs, stages = itertools.count(1), {}, {}
  next_addr = 0x20000
  def cb(size=4096):
    nonlocal next_addr
    index = len(cb_addrs)
    if index >= 32: raise MemoryError("staged kernel exceeds CB capacity")
    cb_addrs[index] = next_addr
    next_addr += (size + 4095) & ~4095
    if next_addr > 0x180000: raise MemoryError("row stages exceed worker L1")
    return index
  def unpack(source, dtype, cb_id, slot, offset=0):
    value = instruction(UnpackOp(Space.DST if dtype is dtypes.fp32 else Space.SRCA, cb_id,
                                src_dtype=dtype, dst_slot=slot), source, UOp.const(offset) if isinstance(offset, int) else offset)
    return value if dtype is dtypes.fp32 else instruction(MoveToDst(slot), value)
  def load(u, col_range, column, dependency, slot, prefetch=False):
    storage, (offset, index) = address(u.src[0])
    if offset: raise NotImplementedError("offset staged load")
    if storage.op is Ops.ALLOC:
      if index not in ({}, {mr: 1} if mr is not None else {}): raise NotImplementedError("non-scalar L1 stage")
      cb_id, producer = stages[storage]
      return slot, unpack(UOp.noop().after(producer, dependency, column), storage.dtype, cb_id, slot), False
    if storage.op is not Ops.PARAM: raise NotImplementedError("staged load storage")
    param = storage.arg.slot
    dtype = args[param].dtype
    width = args[param].shape[-1]
    normal = {col_range: 1, mr: width} if mr is not None else {col_range: 1}
    broadcast = index == {col_range: 1} and mr is not None
    if index != normal and not broadcast: raise NotImplementedError(f"staged load index {index}")
    face = column if broadcast else row_tile * ((width + 15) // 16) + column
    if prefetch and next_addr + (((width + 15) // 16 * face_bytes(dtype) + 4095) & ~4095) <= 0x160000:
      size, count = face_bytes(dtype), (width + 15) // 16
      cb_id = cb(count * size)
      read = instruction(NocRead(param, cb_id, count * size), ((0 if broadcast else row_tile * count) * size).after(dependency))
      return slot, unpack(read, dtype, cb_id, slot, column * size), broadcast
    cb_id = cb()
    read = instruction(NocRead(param, cb_id, face_bytes(dtype)), (face * face_bytes(dtype)).after(dependency))
    return slot, unpack(read, dtype, cb_id, slot), broadcast
  dependency = outer
  for store in stores:
    storage, _ = address(store.src[0])
    reductions = [u for u in expression_nodes(store.src[1]) if u.op is Ops.REDUCE]
    if reductions:
      if len(reductions) != 1: raise NotImplementedError("nested row reductions in one stage")
      reduction = reductions[0]
      slots = itertools.count(1)
      def reduction_load(u, rk):
        # Keep the whole row resident throughout this reduction's K loop.
        slot, source, broadcast = load(u, reduction.src[1], rk, dependency, next(slots), prefetch=True)
        if broadcast: raise NotImplementedError("broadcast input inside reduction")
        return slot, source
      value = reduce_expression(reduction, store.src[1], dependency, axis, reduction_load,
                                lambda rk: valid_mask(cb(), rk, int(reduction.src[1].src[0].val)))
    else:
      fp = UOp.range(UOp.const(1).after(dependency), next(axis), "fp")
      loads = {u: load(u, nr, column_tile, dependency, slot + 1)
               for slot, u in enumerate(u for u in expression_nodes(store.src[1]) if u.op is Ops.LOAD)}
      output_stores = []
      for sub in (0, 2, 4, 6):
        mapping = {}
        for u, (slot, source, broadcast) in loads.items():
          value = instruction(SfpLoadOp(slot, sub_row=sub % 4 if broadcast else sub), source, fp, dtype=dtypes.fp32)
          mapping[u] = instruction(SfpBroadcastRows(), value, dtype=dtypes.fp32) if broadcast else value
        value = store.src[1].substitute(mapping)
        output_stores.append(instruction(SfpStoreOp(0, sub_row=sub), value, fp))
      value = close_footprint(output_stores, fp)
    out_cb = cb()
    packed = instruction(PackOp(out_cb, dst_dtype=storage.dtype), value)
    if storage.op is Ops.ALLOC:
      stages[storage] = out_cb, packed
      dependency = packed
    elif store is final:
      dependency = instruction(NocWrite(storage.arg.slot, out_cb, face_bytes(storage.dtype)), packed, tile * face_bytes(storage.dtype))
    else: raise NotImplementedError("multiple DRAM outputs")
  return LoweredKernel(compile_tile_graph(UOp.sink(dependency.end(outer)), cb_addrs), workers, (8,) * len(args))
