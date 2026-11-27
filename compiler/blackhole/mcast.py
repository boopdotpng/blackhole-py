"""2D register tiling and address-invariant, credit-ring operand distribution."""
from math import prod

from ..dtype import dtypes
from ..uop import Ops, UOp
from .lower import access, face_bytes, LoweredKernel
from .pipeline import instruction, compile_tile_graph
from .specs import (Space, DstZero, UnpackOp, FpuOp, PackOp, NocRead, NocWrite, MoveToDst,
                    SfpLoadOp, SfpStoreOp, NocMcastRead, NocMcastForward, McastWait, McastConsumed, McastRelease)


def invariant_axis(offset, gcols, grows):
  coordinates = {u.arg for u in offset.toposort() if u.op is Ops.SPECIAL}
  if "worker_x" not in coordinates and gcols > 1: return "x"
  if "worker_y" not in coordinates and grows > 1: return "y"
  return "local"


def lower_mcast(kernel, args, grid_shape, max_workers):
  nodes = kernel.toposort()
  store, = [u for u in nodes if u.op is Ops.STORE]
  output, output_index = access(store.src[0])
  shape = args[output].shape
  if len(shape) < 2: return None
  batch, m, n = prod(shape[:-2]), *shape[-2:]
  mf, nf = (m + 7) // 8, (n + 15) // 16
  if mf < 2 or nf < 2: return None
  reductions = [u for u in nodes if u.op is Ops.REDUCE]
  if not 1 <= len(reductions) <= 2: return None
  base, coeff = output_index
  nr = next((r for r, c in coeff.items() if c == 1), None)
  mr = next((r for r, c in coeff.items() if c == n and r is not nr), None)
  batch_coeff = {r: c for r, c in coeff.items() if r not in (mr, nr)}
  if base or mr is None or nr is None or any(c % (m * n) for c in batch_coeff.values()): return None
  products = []
  for red in reductions:
    if len(red.src) != 2 or red.arg[0] is not Ops.ADD: return None
    kr, dot = red.src[1], red.src[0]
    while dot.op is Ops.CAST: dot = dot.src[0]
    if dot.op is not Ops.MUL: return None
    k = int(kr.src[0].val)
    a = w = None
    weight_batched = False
    for operand in dot.src:
      while operand.op is Ops.CAST: operand = operand.src[0]
      if operand.op is not Ops.LOAD: return None
      slot, (const, terms) = access(operand.src[0])
      if const: return None
      if terms == {kr: 1, mr: k, **{r: c // n * k for r, c in batch_coeff.items()}}: a = slot
      if terms == {kr: 1, nr: k}: w = slot
      elif batch_coeff and terms == {kr: 1, nr: k, **{r: c // (m * n) * n * k for r, c in batch_coeff.items()}}:
        w, weight_batched = slot, True
    if a is None or w is None or args[a].dtype is not dtypes.bf16: return None
    if args[a].shape[-2:] != (m, k) or prod(args[a].shape[:-2]) != batch: return None
    if args[w].shape[-2:] != (n, k) or prod(args[w].shape[:-2]) != (batch if weight_batched else 1): return None
    products.append((a, w, (k + 15) // 16, weight_batched))
  bm, bn = (4 if mf >= 4 else 2), (4 if nf >= 4 else 2)
  cols = min((nf + bn - 1) // bn, grid_shape[0], max_workers)
  rows = min((mf + bm - 1) // bm, grid_shape[1], max_workers // cols)
  om_count, on_count = (mf + bm * rows - 1) // (bm * rows), (nf + bn * cols - 1) // (bn * cols)
  wx, wy = UOp.special(cols, "worker_x"), UOp.special(rows, "worker_y")
  batch_id = UOp.range(batch, 30, "batch") if batch > 1 else UOp.const(0)
  om = UOp.range(UOp.const(om_count).after(batch_id) if batch > 1 else om_count, 0, "om")
  on = UOp.range(UOp.const(on_count).after(om), 1, "on")
  row, col = (wy + om * rows) * bm, (wx + on * cols) * bn
  layouts = [8] * len(args)
  cbs, next_addr = {}, 0x20000
  def cb(size):
    nonlocal next_addr
    index = len(cbs)
    if index >= 32: raise MemoryError("multicast kernel exceeds CB capacity")
    cbs[index] = next_addr
    next_addr += (size + 4095) & ~4095
    if next_addr > 0x180000: raise MemoryError("multicast stages exceed worker L1")
    return index
  dependency = instruction(DstZero(), om, on)
  for rid, (a, w, kf, weight_batched) in enumerate(products):
    layouts[w] = 16
    sk = next(s for s in (16, 8, 4, 1) if kf % s == 0 and
              max(bm * s * face_bytes(args[a].dtype), bn * s * face_bytes(args[w].dtype, 16)) <= 65536)
    slabs = kf // sk
    s = UOp.range(UOp.const(slabs).after(dependency), 2 + rid * 2, "slab")
    seq = ((batch_id * om_count + om) * on_count + on) * slabs + s
    kl = UOp.range(sk, 3 + rid * 2, "k")
    unpacks, streams = [], []
    for which, (slot, first_face, max_faces, blocks, height, target) in enumerate(
        ((a, row, mf, bm, 8, Space.SRCB), (w, col, nf, bn, 16, Space.SRCA))):
      dtype = args[slot].dtype
      size = face_bytes(dtype, height)
      batch_face = batch_id * max_faces if which == 0 or weight_batched else UOp.const(0)
      offset = ((batch_face + first_face) * kf + s * sk) * size
      axis = invariant_axis(offset, cols, rows)
      stride = (blocks * sk * size + 63) & ~63
      index = cb(stride * 2)
      ctrl_id = 2 * rid + which
      if ctrl_id >= 4: raise MemoryError("multicast kernel exceeds control slot capacity")
      spec = NocMcastRead(slot, index, axis, cols, rows, blocks, sk * size, kf * size,
                          stride, ctrl_id, batch * om_count * on_count * slabs, tid_mcast=3 if axis == "y" else 2)
      read = instruction(spec, offset, first_face, UOp.const(max_faces), seq)
      if axis == "y": read = instruction(NocMcastForward(spec), read, seq)
      ready = instruction(McastWait(spec.ctrl_id), read, seq)
      unpacks.append(instruction(UnpackOp(target, index, src_dtype=dtype, rows=height, faces=blocks,
                                          face_stride=sk * size), ready, (seq % 2) * stride + kl * size))
      streams.append(spec)
    dtype = args[w].dtype
    value = instruction(FpuOp("MVMUL", m_blocks=bm, n_blocks=bn, fidelity=1 if dtype is dtypes.bfp4 else 2 if dtype is dtypes.bfp8 else 3,
                              dst_slot=rid * bm * bn, src_dtype=dtype, accumulate=True), *unpacks).end(kl)
    for spec in streams:
      consumed = instruction(McastConsumed(spec.ctrl_id), value, seq)
      value = instruction(McastRelease(spec), consumed, seq)
    dependency = value.end(s)
  tail = store.src[1]
  while tail.op is Ops.CAST: tail = tail.src[0]
  if len(reductions) != 1 or tail is not reductions[0]:
    from .reduction import expression_nodes
    epilogue = store.src[1]
    inputs = [u for u in expression_nodes(epilogue) if u.op is Ops.LOAD and not any(u in r.toposort() for r in reductions)]
    for u in inputs:
      slot, index = access(u.src[0])
      if index != output_index or prod(args[slot].shape) != batch * m * n: raise NotImplementedError("broadcast multicast epilogue")
    for r in range(bm):
      for c in range(bn):
        block = r * bn + c
        fp = UOp.range(UOp.const(4).after(dependency), 10 + block, "fp")
        mapped = {red: instruction(SfpLoadOp(rid * bm * bn + block), fp, dtype=dtypes.fp32) for rid, red in enumerate(reductions)}
        for j, u in enumerate(inputs):
          slot, _ = access(u.src[0])
          dst = len(reductions) * bm * bn + j
          if dst >= 56: raise MemoryError("multicast epilogue exceeds Dst")
          index = cb(face_bytes(args[slot].dtype))
          offset = ((row + r < mf) & (col + c < nf)).where(((batch_id * mf + row + r) * nf + col + c) * face_bytes(args[slot].dtype), 0)
          read = instruction(NocRead(slot, index, face_bytes(args[slot].dtype)), offset.after(dependency))
          srca = args[slot].dtype is not dtypes.fp32
          loaded = instruction(UnpackOp(Space.SRCA if srca else Space.DST, index, src_dtype=args[slot].dtype, dst_slot=dst), read)
          if srca: loaded = instruction(MoveToDst(dst), loaded)
          mapped[u] = instruction(SfpLoadOp(dst), loaded, fp, dtype=dtypes.fp32)
        expression = epilogue.substitute(mapped)
        dependency = instruction(SfpStoreOp(block), expression, fp).end(fp)
  dtype = args[output].dtype
  index = cb(bm * bn * face_bytes(dtype))
  packed = instruction(PackOp(index, dst_dtype=dtype, blocks=bm * bn), dependency)
  written = instruction(NocWrite(output, index, face_bytes(dtype), blocks=(bm, bn), shape_faces=(mf, nf)), packed, row, col, batch_id)
  result = written.end(on).end(om)
  if batch > 1: result = result.end(batch_id)
  return LoweredKernel(compile_tile_graph(UOp.sink(result), cbs), cols * rows, tuple(layouts), (cols, rows))
