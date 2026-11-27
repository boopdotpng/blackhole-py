"""Face maps, including indexed views and broadcasting through NoC gathers."""
from math import prod
from ..dtype import dtypes
from ..uop import Ops, UOp
from .lower import affine, face_bytes, LoweredKernel
from .pipeline import instruction, compile_tile_graph
from .specs import Space, NocRead, NocGather, IndexTile, NocWrite, NocScatter, UnpackOp, MoveToDst, SfpLoadOp, SfpStoreOp, PackOp


def dimensions(shape):
  return (prod(shape[:-2]) if len(shape) > 2 else 1,
          shape[-2] if len(shape) > 1 else 1, shape[-1] if shape else 1)


def lower_map(kernel, args, max_workers):
  nodes = kernel.toposort()
  store, = [u for u in nodes if u.op is Ops.STORE]
  output = store.src[0].src[0].arg.slot
  base, coeff = affine(store.src[0].src[1], symbolic=True)
  axes = sorted(coeff, key=coeff.get, reverse=True)
  domain = tuple(int(r.src[0].val) for r in axes)
  strides = {r: prod(domain[i + 1:]) for i, r in enumerate(axes)}
  full = isinstance(base, int) and base == 0 and coeff == strides and prod(domain) == prod(args[output].shape)
  batch, m, n = dimensions(args[output].shape if full else domain)
  nf, mf = (n + 15) // 16, (m + 7) // 8
  total = batch * mf * nf
  workers = min(total, max_workers)
  wid = UOp.special(workers, "worker_id")
  outer = UOp.range((total + workers - 1 - wid) // workers, 0, "out")
  tile = wid + outer * workers
  lane = UOp.special(128, "gather_lane")
  row = (tile // nf) % mf * 8 + lane // 16
  col = tile % nf * 16 + lane % 16
  logical = (tile // (mf * nf) * m + row) * n + col
  valid = (row < m) & (col < n)
  indices = {r: logical // stride % int(r.src[0].val) for r, stride in strides.items()}
  cb_addrs = {}
  def cb():
    index = len(cb_addrs)
    if index >= 32: raise MemoryError("map exceeds CB capacity")
    cb_addrs[index] = 0x20000 + index * 0x1000
    return index
  fp = UOp.range(UOp.const(4).after(outer), 1, "fp")
  mapping = {}
  def unpack(read, dtype, cb_id, slot):
    direct = dtype is dtypes.fp32 or dtype.is_int
    loaded = instruction(UnpackOp(Space.DST if direct else Space.SRCA, cb_id, src_dtype=dtype, dst_slot=slot), read)
    source = loaded if direct else instruction(MoveToDst(slot), loaded)
    return instruction(SfpLoadOp(slot, fmt="i32" if dtype.is_int else "fp32"), source, fp,
                       dtype=dtypes.i32 if dtype.is_int else dtypes.fp32)
  from .reduction import expression_nodes
  for u in expression_nodes(store.src[1]):
    if u.op is not Ops.LOAD: continue
    address = u.src[0]
    if address.op is not Ops.INDEX or address.src[0].op is not Ops.PARAM: raise NotImplementedError("map load storage")
    param = address.src[0].arg.slot
    dtype = args[param].dtype
    if dtype not in (dtypes.fp32, dtypes.bf16, dtypes.i32, dtypes.u32): raise NotImplementedError(f"map input {dtype}")
    slot, cb_id = len(mapping), cb()
    if full and len(u.src) == 1 and address.src[1] is store.src[0].src[1] and dimensions(args[param].shape) == (batch, m, n):
      read = instruction(NocRead(param, cb_id, face_bytes(dtype)), tile * face_bytes(dtype))
    else:
      _, sm, sn = dimensions(args[param].shape)
      index = address.src[1].substitute(indices)
      sr, sc = index // sn % sm, index % sn
      face = ((index // (sm * sn)) * ((sm + 7) // 8) + sr // 8) * ((sn + 15) // 16) + sc // 16
      offset = (face * 128 + sr % 8 * 16 + sc % 16) * dtype.itemsize
      predicate = valid & (index >= 0) & (index < prod(args[param].shape))
      if len(u.src) > 1:
        if not u.src[1].is_const or u.src[1].val != 0: raise NotImplementedError("nonzero masked load default")
        predicate = predicate & u.src[2].substitute(indices)
      index_layouts = []
      for inner in address.src[1].toposort():
        if inner.op is not Ops.LOAD: continue
        source = inner.src[0].src[0]
        if source.op is not Ops.PARAM or not inner.dtype.is_int: raise NotImplementedError("non-integer indirect index")
        source_slot = source.arg.slot
        _, im, inn = dimensions(args[source_slot].shape)
        index_layouts.append((source_slot, prod(args[source_slot].shape), im, inn, args[source_slot].dtype.itemsize))
      read = instruction(NocGather(param, cb_id, dtype.itemsize, tuple(index_layouts)), offset, predicate)
    mapping[u] = unpack(read, dtype, cb_id, slot)
  index_expressions = set()
  def collect(u):
    if u.op is Ops.LOAD: return
    descendants = u.toposort()
    if (u.dtype.is_int or u.dtype is dtypes.bool) and any(n.op is Ops.RANGE or n.is_variable for n in descendants):
      if all(n.op is not Ops.LOAD and (n.op is not Ops.RANGE or n in indices) for n in descendants):
        index_expressions.add(u)
        return
    for source in u.src_without_body: collect(source)
  collect(store.src[1])
  for r in sorted(index_expressions, key=lambda u: nodes.index(u)):
    cb_id, slot = cb(), len(mapping)
    read = instruction(IndexTile(cb_id), r.substitute(indices).cast(dtypes.i32), valid)
    loaded = unpack(read, dtypes.i32, cb_id, slot)
    mapping[r] = loaded.bitcast(dtypes.bool) if r.dtype is dtypes.bool else loaded
  expression = store.src[1].substitute(mapping)
  value = instruction(SfpStoreOp(0, fmt="i32" if args[output].dtype.is_int else "fp32"), expression, fp).end(fp)
  out_cb = cb()
  packed = instruction(PackOp(out_cb, dst_dtype=args[output].dtype), value)
  if full:
    written = instruction(NocWrite(output, out_cb, face_bytes(args[output].dtype)), packed, tile * face_bytes(args[output].dtype))
  else:
    _, om, onn = dimensions(args[output].shape)
    index = store.src[0].src[1].substitute(indices)
    rr, cc = index // onn % om, index % onn
    face = (index // (om * onn) * ((om + 7) // 8) + rr // 8) * ((onn + 15) // 16) + cc // 16
    offset = (face * 128 + rr % 8 * 16 + cc % 16) * args[output].dtype.itemsize
    written = instruction(NocScatter(output, out_cb, args[output].dtype.itemsize), packed, offset, valid)
  program = compile_tile_graph(UOp.sink(written.end(outer)), cb_addrs)
  return LoweredKernel(program, workers, (8,) * len(args))
