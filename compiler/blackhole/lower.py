"""Layer-1 scalar kernels to abstract Blackhole face operations."""
from dataclasses import dataclass
from functools import cache
from math import prod
import os
from ..dtype import dtypes
from ..uop import GroupOp, Ops, UOp
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
  # Code depends on argument layout/type, not on which layer owns its data.
  signature = tuple(arg.param_like(i) if arg.is_variable else UOp.param(i, arg.dtype, shape=arg.shape) for i, arg in enumerate(args))
  return _lower_kernel(kernel, signature, max_workers, grid_shape, os.environ.get("BH_MCAST", "1") != "0")


@cache
def _lower_kernel(kernel, args, max_workers, grid_shape, mcast):
  nodes = kernel.toposort()
  stores = [u for u in nodes if u.op is Ops.STORE]
  if len(stores) != 1:
    from .staged import lower_staged
    return lower_staged(kernel, args, max_workers)
  if not any(u.op is Ops.REDUCE for u in nodes):
    from .map import lower_map
    return lower_map(kernel, args, max_workers)
  store = stores[0]
  output_slot, output_index = access(store.src[0])
  shape = args[output_slot].shape
  if args[output_slot].dtype.is_int and prod(shape) == 1 and sum(u.op is Ops.REDUCE for u in nodes) == 2:
    from .argmax import lower_argmax
    return lower_argmax(kernel, args)
  # Leading singleton batch axes do not change the physical face layout.
  while len(shape) > 2 and shape[0] == 1: shape = shape[1:]
  if shape and shape[-1] == 1 and sum(u.op is Ops.REDUCE for u in nodes) == 1:
    from .reduction import lower_row_reduction
    return lower_row_reduction(kernel, args, max_workers)
  if mcast and len(shape) >= 2 and shape[-2] > 8 and shape[-1] > 16:
    from .mcast import lower_mcast
    if (lowered := lower_mcast(kernel, args, grid_shape, max_workers)) is not None: return lowered
  if len(shape) > 2:
    from .matmul import lower_batched_matmul
    return lower_batched_matmul(kernel, args, max_workers)
  if not shape or len(shape) > 2 or not all(isinstance(s, int) for s in shape):
    raise NotImplementedError(f"output shape {shape}")
  m, n = (1, shape[0]) if len(shape) == 1 else shape
  nf, mf = (n + 15) // 16, (m + 7) // 8
  total = nf * mf
  workers = min(total, max_workers)
  wid = UOp.special(workers, "worker_id")
  outer = UOp.range((total + workers - 1 - wid) // workers, 0, "out")
  tile = wid + outer * workers
  layouts = [8] * len(args)
  cb_addrs, next_cb, next_addr = {}, 0, 0x20000
  def cb(size):
    nonlocal next_cb, next_addr
    index = next_cb; next_cb += 1
    if next_cb > 32: raise MemoryError("kernel exceeds 32 CB streams")
    cb_addrs[index] = next_addr
    next_addr += (size + 0xFFF) & ~0xFFF
    if next_addr > 0x180000: raise MemoryError("matmul stages exceed worker L1")
    return index
  def load(slot, offset, target, dst_slot=0, rows=8, transpose=False):
    dtype = args[slot].dtype
    index = cb(face_bytes(dtype, rows))
    read = instruction(NocRead(slot, index, face_bytes(dtype, rows)), offset)
    via_srca = target is Space.DST and dtype is not dtypes.fp32
    unpack = instruction(UnpackOp(Space.SRCA if via_srca else target, index, src_dtype=dtype,
                                   dst_dtype=dtype if target is not Space.DST else dtypes.fp32,
                                   rows=rows, dst_slot=dst_slot, transpose=transpose), read)
    return instruction(MoveToDst(dst_slot), unpack) if via_srca else unpack
  def prefetch(slot, offset, target, rows, count, dependency, rk):
    dtype = args[slot].dtype
    size = face_bytes(dtype, rows)
    index = cb(count * size)
    read = instruction(NocRead(slot, index, count * size), offset.after(dependency))
    return instruction(UnpackOp(target, index, src_dtype=dtype, dst_dtype=dtype, rows=rows), read, rk * size)
  reductions = [u for u in nodes if u.op is Ops.REDUCE]
  out_const, out_coeff = output_index
  nr = next((r for r, c in out_coeff.items() if c == 1), None)
  mr = next((r for r, c in out_coeff.items() if c == n and r is not nr), None)
  if out_const or any(r not in (mr, nr) for r in out_coeff): raise NotImplementedError("batched matmul")
  if len(reductions) > 56: raise MemoryError("too many matmul accumulators")
  dependency = instruction(DstZero(), outer)
  mapped = {}
  for dst_slot, reduction in enumerate(reductions):
    if len(reduction.src) != 2 or reduction.arg[0] is not Ops.ADD: raise NotImplementedError("non-dot reduction")
    kr = reduction.src[1]
    dot = reduction.src[0]
    while dot.op is Ops.CAST: dot = dot.src[0]
    if dot.op is not Ops.MUL: raise NotImplementedError("non-matmul reduction")
    operands = []
    for source in dot.src:
      while source.op is Ops.CAST: source = source.src[0]
      if source.op is not Ops.LOAD: raise NotImplementedError("non-matmul operand")
      operands.append(source)
    k = int(kr.src[0].val)
    activation, weight = None, None
    for operand in operands:
      param, (const, coeff) = access(operand.src[0])
      if const: raise NotImplementedError("offset matmul")
      if coeff == ({kr: 1, mr: k} if mr is not None else {kr: 1}): activation = param
      elif coeff == ({kr: 1, nr: k} if nr is not None else {kr: 1}): weight = param
    if activation is None or weight is None: raise NotImplementedError("unrecognized matmul index mapping")
    layouts[weight] = 16
    kf = (k + 15) // 16
    rk = UOp.range(UOp.const(kf).after(dependency), dst_slot + 1, "k")
    # Bring the whole K strip into L1 with burst NoC transfers. The unpack
    # loop selects faces locally; its CB credit remains held through K.
    sizes = [face_bytes(args[activation].dtype), face_bytes(args[weight].dtype, 16)]
    if next_addr + sum((kf * size + 4095) & ~4095 for size in sizes) <= 0x160000:
      a = prefetch(activation, (tile // nf) * kf * sizes[0], Space.SRCB, 8, kf, dependency, rk)
      w = prefetch(weight, (tile % nf) * kf * sizes[1], Space.SRCA, 16, kf, dependency, rk)
    else:
      a = load(activation, ((tile // nf) * kf + rk) * sizes[0], Space.SRCB)
      w = load(weight, ((tile % nf) * kf + rk) * sizes[1], Space.SRCA, rows=16)
    dtype = args[weight].dtype
    phases = 1 if dtype is dtypes.bfp4 else 2 if dtype is dtypes.bfp8 else 3
    product = instruction(FpuOp("MVMUL", fidelity=phases, dst_slot=dst_slot, src_dtype=dtype, accumulate=True),
                          a, w, dtype=dtypes.fp32)
    dependency = product.end(rk)
    mapped[reduction] = dst_slot
  tail = store.src[1]
  while tail.op is Ops.CAST: tail = tail.src[0]
  if len(reductions) == 1 and tail is reductions[0]: value = dependency
  else:
    fp = UOp.range(UOp.const(4).after(dependency), len(reductions) + 1, "fp")
    expression = store.src[1].substitute({r: instruction(SfpLoadOp(slot), fp, dtype=dtypes.fp32) for r, slot in mapped.items()})
    from .reduction import expression_nodes
    epilogue_inputs = {}
    for u in expression_nodes(expression):
      if u.op is not Ops.LOAD: continue
      param, index = access(u.src[0])
      if index != output_index or prod(args[param].shape) != m * n:
        raise NotImplementedError("broadcast matmul epilogue input")
      slot = len(reductions) + len(epilogue_inputs)
      if slot >= 56: raise MemoryError("matmul epilogue exceeds Dst capacity")
      source = load(param, (tile * face_bytes(u.dtype)).after(dependency), Space.DST, slot)
      epilogue_inputs[u] = instruction(SfpLoadOp(slot), source, fp, dtype=dtypes.fp32)
    expression = expression.substitute(epilogue_inputs)
    value = instruction(SfpStoreOp(0), expression, fp).end(fp)
  dtype = args[output_slot].dtype
  out_cb = cb(face_bytes(dtype))
  packed = instruction(PackOp(out_cb, dst_dtype=dtype), value)
  written = instruction(NocWrite(output_slot, out_cb, face_bytes(dtype)), packed, tile * face_bytes(dtype))
  program = compile_tile_graph(UOp.sink(written.end(outer)), cb_addrs)
  return LoweredKernel(program, workers, tuple(layouts))
