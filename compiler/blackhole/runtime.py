"""Execute compiled kernel schedules using face-tiled device buffers."""
import os
import struct
import weakref
from ..uop import Ops, UOp
from ..tensor import _BUFFER_SOURCE, _BUF_ID, PackedSource, lower_tensor
from ..memory import linearize_schedule, _plan_lifetimes
from ..isa.tensix import unpack_bundle
from .lower import lower_kernel, access

_RESIDENT = weakref.WeakKeyDictionary()
_DEFAULT_DEVICE = None


def default_device():
  global _DEFAULT_DEVICE
  if _DEFAULT_DEVICE is None:
    from device import Device
    _DEFAULT_DEVICE = Device(int(os.environ.get("BH_DEVICE", "0")))
  return _DEFAULT_DEVICE


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


def realize(root, device=None):
  device = device or (_RESIDENT[root].device if root in _RESIDENT else default_device())
  if root.op is Ops.BUFFER:
    materialize(root, device)
    return root
  schedule = linearize_schedule(lower_tensor(root))
  compiled = [lower_kernel(sc.kernel, sc.args, len(device.workers), (device.cols - 1, 10)) for sc in schedule]
  if not schedule: raise NotImplementedError("empty kernel schedule")
  from device import FaceBuffer
  # Upload persistent sources before the transient arena. Repeated decode
  # steps then reuse scratch DRAM instead of growing the bump allocator.
  writable, external = set(), {}
  for sc, lowered in zip(schedule, compiled):
    for u in sc.kernel.toposort():
      if u.op is Ops.STORE and u.src[0].src[0].op is Ops.PARAM:
        writable.add(sc.args[u.src[0].src[0].arg.slot])
    for arg, rows in zip(sc.args, lowered.face_rows):
      if arg.is_variable:
        if not arg.is_bound_var: raise ValueError(f"runtime variable {arg.arg.name!r} is not bound")
      elif arg.op is not Ops.ALLOC: external[arg, rows] = None
  for arg, rows in external: materialize(arg, device, rows, writable=arg in writable)
  last = schedule[-1]
  store = next(u for u in reversed(last.kernel.toposort())
               if u.op is Ops.STORE and u.src[0].src[0].op is Ops.PARAM)
  output_slot, _ = access(store.src[0])
  output = last.args[output_slot]
  local = {}
  if output.op is Ops.ALLOC:
    local[output] = FaceBuffer(device, output.shape, output.dtype, compiled[-1].face_rows[output_slot])
  arena_start = device.dram_top
  first, last = {}, {}
  for index, (sc, lowered) in enumerate(zip(schedule, compiled)):
    for arg, rows in zip(sc.args, lowered.face_rows):
      if arg.op is not Ops.ALLOC or arg is output: continue
      if arg not in local: local[arg] = FaceBuffer(device, arg.shape, arg.dtype, rows, address=0)
      if local[arg].rows != rows: raise NotImplementedError("transient buffer layout conversion")
      first.setdefault(arg, index)
      last[arg] = index
  # Face padding can exceed the logical tensor size, so plan with physical
  # byte counts and the runtime's interleaved DRAM allocation alignment.
  plan = _plan_lifetimes(first, last, device.dram_banks * 4096, {arg: local[arg].nbytes for arg in first})
  try:
    if plan.peak_bytes:
      base = device.alloc_dram(plan.peak_bytes)
      for arg, offset in plan.offsets.items(): local[arg].addr = base + offset
    for sc, lowered in zip(schedule, compiled):
      buffers = []
      for arg, rows in zip(sc.args, lowered.face_rows):
        if arg.is_variable:
          buffers.append(arg.arg.val & 0xffffffff)
          continue
        if arg.op is Ops.ALLOC:
          if local[arg].rows != rows: raise NotImplementedError("transient buffer layout conversion")
          buffers.append(local[arg])
        else: buffers.append(materialize(arg, device, rows))
      images = unpack_bundle(lowered.program.src[3].arg)
      device.run(images, data={0x80: struct.pack(f"<{len(buffers)}Q", *(b if isinstance(b, int) else b.addr for b in buffers))},
                 cores=device.worker_grid(*lowered.grid) if lowered.grid else device.workers[:lowered.workers])
    device.synchronize()
  finally: device.dram_top = arena_start
  buffer = local[output] if output in local else _RESIDENT[output]
  result = UOp.buffer(f"realized_{next(_BUF_ID)}", root.shape, root.dtype)
  _RESIDENT[result] = buffer
  return result


def numpy(root, device=None):
  return _RESIDENT[realize(root, device)].numpy().reshape(root.shape)
