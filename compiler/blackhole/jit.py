"""Minimal tinygrad-style TinyJit: captures one HCQ2 CommandBuffer on call 1, replays in 1 doorbell on call 2+."""
from dataclasses import dataclass
from typing import Any, Callable
from ..tensor import Tensor, _BUFFER_SOURCE, _BUF_ID
from ..uop import Ops, UOp
from .runtime import LinkedSchedule, _RESIDENT, canonicalize_graph, default_device, get_linked_schedule, materialize, realize


def _extract_inputs(args, kwargs) -> tuple[list[Tensor], dict[UOp, int]]:
  tensors: list[Tensor] = []
  var_vals: dict[UOp, int] = {}
  def visit(x):
    if isinstance(x, Tensor):
      tensors.append(x)
      _, vs = x.uop.unbind_all()
      var_vals.update(vs)
    elif isinstance(x, UOp) and x.is_bound_var:
      var_vals[x.unbound()] = x.arg.val
    elif isinstance(x, (list, tuple)):
      for item in x: visit(item)
    elif isinstance(x, dict):
      for item in x.values(): visit(item)
  visit(args)
  visit(kwargs)
  return tensors, var_vals


@dataclass
class _Captured:
  device: Any
  linked: LinkedSchedule
  ext_bufs: list[UOp]
  input_slots: list[tuple[int, int, Any]]  # (arg_idx, ext_idx, persistent FaceBuffer for host copies)
  input_sig: tuple[tuple[tuple[int, ...], Any], ...]
  var_keys: tuple[UOp, ...]
  output_buf: Any
  output_shape: tuple[int, ...]
  output_dtype: Any


class TinyJit:
  """Capture and replay a Blackhole tensor function with zero Python tracing or rangeify overhead.

  Call 0: warmup (materializes persistent weights/caches).
  Call 1: captures the graph into a linked HCQ2 CommandBuffer with reusable input/output FaceBuffers.
  Call 2+: updates only dynamic input bytes + bound Variables and rings CP_WPTR once.
  """
  def __init__(self, fxn: Callable, *, device=None):
    self.fxn = fxn
    self.device = device
    self.cnt = 0
    self.captured: _Captured | None = None

  def reset(self):
    self.cnt = 0
    self.captured = None

  def __call__(self, *args, **kwargs) -> Tensor:
    in_tensors, in_vars = _extract_inputs(args, kwargs)
    if self.cnt == 0:
      self.cnt = 1
      ret = self.fxn(*args, **kwargs)
      if not isinstance(ret, Tensor): raise TypeError("TinyJit expects a Tensor return value")
      return ret.realize(device=self.device)

    if self.cnt == 1:
      # Capture: materialize any non-buffer input expressions so inputs are clean BUFFER leaves.
      for t in in_tensors:
        if t.uop.op is not Ops.BUFFER: t.realize(device=self.device)
      ret = self.fxn(*args, **kwargs)
      if not isinstance(ret, Tensor): raise TypeError("TinyJit expects a Tensor return value")
      if ret.uop.op is Ops.BUFFER:
        self.cnt = 2
        return ret
      dev = self.device or default_device()
      canon_root, ext_bufs, var_vals = canonicalize_graph(ret.uop)
      linked = get_linked_schedule(canon_root, dev)
      ext_index = {b: i for i, b in enumerate(ext_bufs)}
      rows_by_ext = {idx: rows for idx, rows, _ in linked.cs.ext_specs}
      input_slots = []
      for arg_i, t in enumerate(in_tensors):
        if t.uop in ext_index:
          idx = ext_index[t.uop]
          rows = rows_by_ext.get(idx, 8)
          fb = materialize(t.uop, dev, rows)
          input_slots.append((arg_i, idx, fb))
      out_buf = linked.run(ext_bufs, var_vals)
      self.captured = _Captured(
        device=dev, linked=linked, ext_bufs=list(ext_bufs), input_slots=input_slots,
        input_sig=tuple((t.shape, t.dtype) for t in in_tensors),
        var_keys=tuple(var_vals.keys()), output_buf=out_buf,
        output_shape=ret.shape, output_dtype=ret.dtype,
      )
      self.cnt = 2
      res = UOp.buffer(f"jit_{next(_BUF_ID)}", ret.shape, ret.dtype)
      _RESIDENT[res] = out_buf
      return Tensor.from_uop(res)

    cap = self.captured
    assert cap is not None
    sig = tuple((t.shape, t.dtype) for t in in_tensors)
    if sig != cap.input_sig:
      raise ValueError(f"TinyJit input signature changed: expected {cap.input_sig}, got {sig}")

    ext_bufs = list(cap.ext_bufs)
    for arg_i, ext_idx, persistent_fb in cap.input_slots:
      u = in_tensors[arg_i].uop
      if u in _RESIDENT:
        ext_bufs[ext_idx] = u
      elif u in _BUFFER_SOURCE and isinstance(_BUFFER_SOURCE[u], bytes):
        cap.linked.cmdbuf.wait_previous()
        persistent_fb.copy_from_raw(_BUFFER_SOURCE[u])
      else:
        in_tensors[arg_i].realize(device=cap.device)
        ext_bufs[ext_idx] = in_tensors[arg_i].uop

    out_buf = cap.linked.run(tuple(ext_bufs), in_vars, output_buf=cap.output_buf)
    res = UOp.buffer(f"jit_{next(_BUF_ID)}", cap.output_shape, cap.output_dtype)
    _RESIDENT[res] = out_buf
    return Tensor.from_uop(res)
