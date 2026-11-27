"""Execute compiled kernel schedules via HCQ2 command buffers, cached rangeify, and face-tiled buffers."""
from dataclasses import dataclass
from functools import lru_cache
import os
import weakref
from ..uop import Ops, UOp
from ..tensor import _BUFFER_SOURCE, _BUF_ID, PackedSource, lower_tensor
from ..memory import MemoryPlan, linearize_schedule, _plan_lifetimes
from ..isa.tensix import unpack_bundle
from .hcq import ComputeQueue, CommandBuffer, pack_phys_rect
from .lower import LoweredKernel, lower_kernel, access

_RESIDENT = weakref.WeakKeyDictionary()
_DEFAULT_DEVICE = None


def default_device():
  global _DEFAULT_DEVICE
  if _DEFAULT_DEVICE is None:
    from device import Device
    _DEFAULT_DEVICE = Device(int(os.environ.get("BH_DEVICE", "0")))
  return _DEFAULT_DEVICE


def canonicalize_graph(root: UOp) -> tuple[UOp, tuple[UOp, ...], dict[UOp, int]]:
  """Unbind Variables and replace external BUFFER leaves with positional placeholders so rangeify caches across calls."""
  unbound, var_vals = root.unbind_all()
  ext_bufs: list[UOp] = []
  mapping: dict[UOp, UOp] = {}
  for u in unbound.toposort():
    if u.op is Ops.BUFFER and u not in mapping:
      idx = len(ext_bufs)
      ext_bufs.append(u)
      mapping[u] = UOp.buffer(f"__ext_{idx}", u.shape, u.dtype, addr=u.arg.addr, space=u.arg.space)
  canon = unbound.substitute(mapping) if mapping else unbound
  return canon, tuple(ext_bufs), var_vals


@dataclass(frozen=True)
class CompiledSchedule:
  compiled: tuple[LoweredKernel, ...]
  arg_plans: tuple[tuple[tuple, ...], ...]   # per kernel, per arg slot: ("var", u) | ("ext", i, rows) | ("out", rows) | ("arena", off)
  ext_specs: tuple[tuple[int, int, bool], ...]  # (ext_idx, rows, writable)
  output_is_alloc: bool
  output_ext_idx: int | None
  output_shape: tuple[int, ...]
  output_dtype: object
  output_rows: int
  plan: MemoryPlan


def _face_nbytes(shape, dtype, rows=8) -> int:
  import math
  from ..dtype import dtypes
  packed = dtype in (dtypes.bfp8, dtypes.bfp4)
  m, n = (1, 1) if not shape else (1, shape[0]) if len(shape) == 1 else shape[-2:]
  batch = math.prod(shape[:-2]) if len(shape) > 2 else 1
  mr, nc = -(-m // rows), -(-n // 16)
  fb = 16 + 256 * dtype.bits // 8 if packed else rows * 16 * dtype.itemsize
  return batch * mr * nc * fb


@lru_cache(maxsize=256)
def compile_schedule(canon_root: UOp, max_workers: int, grid_shape: tuple[int, int], dram_banks: int) -> CompiledSchedule:
  """Lower (rangeify) + compile + lifetime-plan a canonical graph ONCE and cache the result."""
  schedule = linearize_schedule(lower_tensor(canon_root))
  if not schedule: raise NotImplementedError("empty kernel schedule")
  compiled = tuple(lower_kernel(sc.kernel, sc.args, max_workers, grid_shape) for sc in schedule)

  # Map canonical placeholder BUFFERs back to their positional ext_idx.
  canon_to_idx: dict[UOp, int] = {}
  for sc in schedule:
    for arg in sc.args:
      if arg.op is Ops.BUFFER and arg not in canon_to_idx and arg.arg.name.startswith("__ext_"):
        canon_to_idx[arg] = int(arg.arg.name[6:])

  writable: set[int] = set()
  ext_rows: dict[int, int] = {}
  for sc, lowered in zip(schedule, compiled):
    for u in sc.kernel.toposort():
      if u.op is Ops.STORE and u.src[0].src[0].op is Ops.PARAM:
        target = sc.args[u.src[0].src[0].arg.slot]
        if target in canon_to_idx: writable.add(canon_to_idx[target])
    for arg, rows in zip(sc.args, lowered.face_rows):
      if arg.is_variable or arg.op is Ops.ALLOC: continue
      idx = canon_to_idx[arg]
      if idx in ext_rows and ext_rows[idx] != rows: raise NotImplementedError("buffer device/layout conversion")
      ext_rows[idx] = rows

  last = schedule[-1]
  store = next(u for u in reversed(last.kernel.toposort())
               if u.op is Ops.STORE and u.src[0].src[0].op is Ops.PARAM)
  output_slot, _ = access(store.src[0])
  output = last.args[output_slot]
  output_rows = compiled[-1].face_rows[output_slot]
  output_is_alloc = output.op is Ops.ALLOC
  output_ext_idx = None if output_is_alloc else canon_to_idx[output]

  first: dict[UOp, int] = {}
  last_use: dict[UOp, int] = {}
  alloc_rows: dict[UOp, int] = {}
  for index, (sc, lowered) in enumerate(zip(schedule, compiled)):
    for arg, rows in zip(sc.args, lowered.face_rows):
      if arg.op is not Ops.ALLOC or arg is output: continue
      if arg in alloc_rows and alloc_rows[arg] != rows: raise NotImplementedError("transient buffer layout conversion")
      alloc_rows[arg] = rows
      first.setdefault(arg, index)
      last_use[arg] = index

  phys_bytes = {arg: _face_nbytes(arg.shape, arg.dtype, alloc_rows[arg]) for arg in first}
  plan = _plan_lifetimes(first, last_use, dram_banks * 4096, phys_bytes)

  arg_plans = []
  for sc, lowered in zip(schedule, compiled):
    kplan = []
    for arg, rows in zip(sc.args, lowered.face_rows):
      if arg.is_variable:
        kplan.append(("var", arg.unbound() if arg.is_bound_var else arg))
      elif arg.op is Ops.ALLOC:
        if arg is output: kplan.append(("out", rows))
        else: kplan.append(("arena", plan.offsets[arg]))
      else:
        kplan.append(("ext", canon_to_idx[arg], rows))
    arg_plans.append(tuple(kplan))

  ext_specs = tuple((idx, rows, idx in writable) for idx, rows in ext_rows.items())
  return CompiledSchedule(
    compiled=compiled, arg_plans=tuple(arg_plans), ext_specs=ext_specs,
    output_is_alloc=output_is_alloc, output_ext_idx=output_ext_idx,
    output_shape=tuple(output.shape), output_dtype=output.dtype, output_rows=output_rows,
    plan=plan,
  )


class LinkedSchedule:
  """Device-linked HCQ2 CommandBuffer for a CompiledSchedule; replays all kernels with 1 CP doorbell."""
  def __init__(self, device, cs: CompiledSchedule):
    self.device = device
    self.cs = cs
    self.ext_patches: list[tuple[int, int]] = []      # (rel_arg_off, ext_idx)
    self.var_patches: list[tuple[int, UOp]] = []      # (rel_arg_off, unbound_var)
    self.out_patches: list[int] = []                  # rel_arg_off
    self.arena_patches: list[tuple[int, int]] = []    # (rel_arg_off, arena_byte_off)
    self.last_ext_addrs: dict[int, int] = {}
    self.last_out_addr: int = -1

    q = ComputeQueue()
    for lowered, kplan in zip(cs.compiled, cs.arg_plans):
      images = unpack_bundle(lowered.program.src[3].arg)
      prog_addr, prog_bytes, prog_key = device.upload_program(images)
      cores = device.worker_grid(*lowered.grid) if lowered.grid else device.workers[:lowered.workers]
      workers, targets = device._launch_layout(cores)
      rects = [pack_phys_rect(t) for t in targets]
      args_rel = q.alloc_args()
      for slot, kind in enumerate(kplan):
        rel = args_rel + slot * 8
        tag = kind[0]
        if tag == "ext": self.ext_patches.append((rel, kind[1]))
        elif tag == "var": self.var_patches.append((rel, kind[1]))
        elif tag == "out": self.out_patches.append(rel)
        elif tag == "arena": self.arena_patches.append((rel, kind[1]))
      q.exec(prog_addr, prog_bytes, prog_key, rects, len(workers), args_rel)
    q.signal(device.kernel_signal.addr, 0)
    self.cmdbuf: CommandBuffer = q.build(device)
    self.arena_gen = -1
    self._bind_arena()

  def _bind_arena(self):
    if not self.cs.plan.peak_bytes: return
    base = self.device.ensure_arena(self.cs.plan.peak_bytes)
    if self.arena_gen != self.device._arena_gen:
      self.cmdbuf.wait_previous()
      for rel, off in self.arena_patches:
        self.cmdbuf.patch_arg_u64(rel, base + off)
      self.arena_gen = self.device._arena_gen

  def run(self, ext_bufs: tuple[UOp, ...], var_vals: dict[UOp, int], *, output_buf=None):
    from device import FaceBuffer
    cs = self.cs
    # Materialize external inputs before ensuring the arena (persistent uploads go first).
    ext_addrs: dict[int, int] = {}
    for idx, rows, is_writable in cs.ext_specs:
      ext_addrs[idx] = materialize(ext_bufs[idx], self.device, rows, writable=is_writable).addr

    if cs.output_is_alloc:
      out_buf = output_buf if output_buf is not None else FaceBuffer(self.device, cs.output_shape, cs.output_dtype, cs.output_rows)
    else:
      out_buf = _RESIDENT[ext_bufs[cs.output_ext_idx]]

    # Wait only if a previous run of this same CommandBuffer is still in flight.
    self.cmdbuf.wait_previous()
    self._bind_arena()

    # Patch only external buffer addresses that actually changed since the previous run.
    for rel, idx in self.ext_patches:
      addr = ext_addrs[idx]
      if self.last_ext_addrs.get(idx) != addr:
        self.cmdbuf.patch_arg_u64(rel, addr)
    self.last_ext_addrs = ext_addrs

    for rel, var in self.var_patches:
      if var not in var_vals: raise ValueError(f"runtime variable {var.arg.name!r} is not bound")
      self.cmdbuf.patch_arg_u32(rel, var_vals[var])

    if cs.output_is_alloc and out_buf.addr != self.last_out_addr:
      for rel in self.out_patches:
        self.cmdbuf.patch_arg_u64(rel, out_buf.addr)
      self.last_out_addr = out_buf.addr

    self.cmdbuf.submit()
    return out_buf


def materialize(u, device, rows=8, *, writable=False):
  from device import FaceBuffer
  if u in _RESIDENT:
    buffer = _RESIDENT[u]
    if buffer.device is not device or buffer.rows != rows: raise NotImplementedError("buffer device/layout conversion")
    return buffer
  buffer = FaceBuffer(device, u.shape, u.dtype, rows)
  if u in _BUFFER_SOURCE:
    source = _BUFFER_SOURCE[u]
    if isinstance(source, PackedSource):
      buffer.copy_from_packed_kn(source.path, source.offset, source.shape)
      _RESIDENT[u] = buffer
      return buffer
    if isinstance(source, tuple):
      path, offset, size = source
      with open(path, "rb") as f:
        f.seek(offset)
        data = f.read(size)
      if len(data) != size: raise ValueError(f"short tensor read: {path}")
    else: data = source
    buffer.copy_from_raw(data)
  elif u.op is not Ops.ALLOC and not writable:
    raise ValueError(f"buffer {u.arg.name!r} has no host or device data")
  _RESIDENT[u] = buffer
  return buffer


def get_linked_schedule(canon_root: UOp, device) -> LinkedSchedule:
  linked = device._linked_schedules.get(canon_root)
  if linked is None:
    cs = compile_schedule(canon_root, len(device.workers), (device.cols - 1, 10), device.dram_banks)
    linked = LinkedSchedule(device, cs)
    device._linked_schedules[canon_root] = linked
  return linked


def realize(root, device=None, *, output_buf=None):
  device = device or (_RESIDENT[root].device if root in _RESIDENT else default_device())
  if root.op is Ops.BUFFER:
    materialize(root, device)
    return root
  canon_root, ext_bufs, var_vals = canonicalize_graph(root)
  linked = get_linked_schedule(canon_root, device)
  buffer = linked.run(ext_bufs, var_vals, output_buf=output_buf)
  result = UOp.buffer(f"realized_{next(_BUF_ID)}", root.shape, root.dtype)
  _RESIDENT[result] = buffer
  return result


def numpy(root, device=None):
  return _RESIDENT[realize(root, device)].numpy().reshape(root.shape)
