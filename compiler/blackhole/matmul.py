"""Batched BF16 matmul with device-side gathers for runtime weight faces."""
from math import prod
from ..dtype import dtypes
from ..uop import Ops, UOp
from .lower import access, affine, face_bytes, LoweredKernel
from .map import dimensions
from .pipeline import instruction, compile_tile_graph
from .specs import Space, NocRead, NocGather, NocWrite, UnpackOp, DstZero, FpuOp, PackOp


def lower_batched_matmul(kernel, args, max_workers):
  nodes = kernel.toposort()
  store, = [u for u in nodes if u.op is Ops.STORE]
  reduction, = [u for u in nodes if u.op is Ops.REDUCE]
  output, (base, coeff) = access(store.src[0])
  if base or reduction.arg[0] is not Ops.ADD: raise NotImplementedError("batched matmul output")
  batch, m, n = dimensions(args[output].shape)
  kr, = reduction.src[1:]
  k = int(kr.src[0].val)
  dot = reduction.src[0]
  while dot.op is Ops.CAST: dot = dot.src[0]
  if dot.op is not Ops.MUL: raise NotImplementedError("batched dot product")
  operands = []
  for operand in dot.src:
    while operand.op is Ops.CAST: operand = operand.src[0]
    if operand.op is not Ops.LOAD or len(operand.src) != 1: raise NotImplementedError("batched matmul operand")
    operands.append(operand)
  nr = next((r for r, stride in coeff.items() if stride == 1), None)
  activation = next((u for u in operands if nr not in access(u.src[0])[1][1]), None)
  if activation is None: raise NotImplementedError("batched matmul activation")
  weight = operands[1] if operands[0] is activation else operands[0]
  a_slot, a_index = access(activation.src[0])
  w_slot, _ = access(weight.src[0])
  if any(args[slot].dtype is not dtypes.bf16 for slot in (a_slot, w_slot)):
    raise NotImplementedError("batched matmul requires BF16 inputs")
  tail = store.src[1]
  while tail.op is Ops.CAST: tail = tail.src[0]
  if tail is not reduction: raise NotImplementedError("batched matmul epilogue")
  nf, mf, kf = (n + 15) // 16, (m + 7) // 8, (k + 15) // 16
  total = batch * mf * nf
  workers = min(max_workers, total)
  wid = UOp.special(workers, "worker_id")
  outer = UOp.range((total + workers - 1 - wid) // workers, 0, "out")
  tile = wid + outer * workers
  batch_id, row_tile, column_tile = tile // (mf * nf), tile // nf % mf, tile % nf
  zero = instruction(DstZero(), outer)
  rk = UOp.range(UOp.const(kf).after(zero), 1, "k")
  cb_addrs = {0: 0x20000, 1: 0x21000, 2: 0x22000}
  def gather(operand, cb_id, rows, row, column, kval, valid):
    slot = operand.src[0].src[0].arg.slot
    logical = (batch_id * m + row) * n + column
    indices = {r: logical // stride % int(r.src[0].val) for r, stride in coeff.items()}
    indices[kr] = kval
    index = operand.src[0].src[1].substitute(indices)
    _, sm, sn = dimensions(args[slot].shape)
    sr, sc = index // sn % sm, index % sn
    face = (index // (sm * sn) * ((sm + 7) // 8) + sr // 8) * ((sn + 15) // 16) + sc // 16
    offset = (face * 128 + sr % 8 * 16 + sc % 16) * 2
    return instruction(NocGather(slot, cb_id, 2, lanes=rows * 16), offset,
                       valid & (index >= 0) & (index < prod(args[slot].shape)))
  expected_a = (0, {kr: 1, **{r: stride // n * k for r, stride in coeff.items() if r is not nr}})
  if a_index == expected_a and dimensions(args[a_slot].shape) == (batch, m, k):
    a_read = instruction(NocRead(a_slot, 0, face_bytes(dtypes.bf16)), ((batch_id * mf + row_tile) * kf + rk) * face_bytes(dtypes.bf16))
  else:
    lane = UOp.special(128, "gather_lane")
    row, kval = row_tile * 8 + lane // 16, rk * 16 + lane % 16
    a_read = gather(activation, 0, 8, row, UOp.const(0), kval, (row < m) & (kval < k))
  lane = UOp.special(256, "gather_lane")
  column, kval = column_tile * 16 + lane % 16, rk * 16 + lane // 16
  w_read = gather(weight, 1, 16, UOp.const(0), column, kval, (column < n) & (kval < k))
  a = instruction(UnpackOp(Space.SRCB, 0, src_dtype=dtypes.bf16), a_read)
  w = instruction(UnpackOp(Space.SRCA, 1, src_dtype=dtypes.bf16, rows=16), w_read)
  product = instruction(FpuOp("MVMUL", fidelity=3, src_dtype=dtypes.bf16, accumulate=True), a, w, dtype=dtypes.fp32).end(rk)
  packed = instruction(PackOp(2, dst_dtype=args[output].dtype), product)
  write = instruction(NocWrite(output, 2, face_bytes(args[output].dtype)), packed, tile * face_bytes(args[output].dtype))
  return LoweredKernel(compile_tile_graph(UOp.sink(write.end(outer)), cb_addrs), workers, (8,) * len(args))
