import functools
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar, overload
from .tensor import Tensor
from .uop import Ops, PatternMatcher, UOp, UPat, graph_rewrite

@dataclass
class _CaptureCtx:
  args: list[UOp]
  seen: dict[UOp, int]

def _capture(ctx: _CaptureCtx, x: UOp) -> UOp:
  if (slot := ctx.seen.get(x)) is None:
    slot = ctx.seen[x] = len(ctx.args)
    ctx.args.append(x)
  return x.param_like(slot)

def _has_param(x: UOp) -> bool:
  return any(u.op is Ops.PARAM and u.arg.slot >= 0 for u in x.toposort())

pm_capture = PatternMatcher([
  (UPat((Ops.AFTER, Ops.STAGE), name="x"), lambda ctx, x: _capture(ctx, x) if not _has_param(x) else None),
  (UPat((Ops.BUFFER, Ops.ALLOC), name="x"), _capture),
  (UPat(Ops.PARAM, name="x"), lambda ctx, x: _capture(ctx, x) if x.is_variable and x.arg.slot == -1 else None),
])

def _collect_args(obj: Any, out: list[UOp]) -> None:
  if isinstance(obj, Tensor): out.append(obj.uop)
  elif isinstance(obj, UOp): out.append(obj)
  elif isinstance(obj, (list, tuple)):
    for x in obj: _collect_args(x, out)
  elif isinstance(obj, dict):
    for x in obj.values(): _collect_args(x, out)

F = TypeVar("F", bound=Callable)
@overload
def function(fxn: F, *, allow_implicit: bool = False) -> F: ...
@overload
def function(fxn: None = None, *, allow_implicit: bool = False) -> Callable[[F], F]: ...
def function(fxn=None, *, allow_implicit: bool = False):
  """Trace `fxn` into a CALL(SINK(STORE(out_param, val)), *args) with slotted PARAMs so identical bodies deduplicate."""
  if fxn is None: return functools.partial(function, allow_implicit=allow_implicit)
  name = getattr(fxn, "__name__", "")

  @functools.wraps(fxn)
  def call(*args, **kwargs):
    raw_args: list[UOp] = []
    _collect_args((args, kwargs), raw_args)
    call_uops: list[UOp] = list(dict.fromkeys(raw_args))

    ret = fxn(*args, **kwargs)
    is_tuple = isinstance(ret, tuple)
    rets = ret if is_tuple else (ret,)
    if not all(isinstance(x, Tensor) for x in rets):
      raise TypeError(f"function {name!r} must return Tensor or tuple[Tensor, ...]")

    uret = UOp.sink(*(x.uop for x in rets)) if is_tuple else rets[0].uop
    seen = {x: i for i, x in enumerate(call_uops)}
    uret = uret.substitute({x: x.param_like(i) for x, i in seen.items()})

    n_explicit = len(call_uops)
    uret = graph_rewrite(uret, pm_capture, ctx=_CaptureCtx(call_uops, seen), bottom_up=True)

    if not allow_implicit and len(call_uops) > n_explicit:
      implicit = call_uops[n_explicit:]
      raise RuntimeError(f"function {name!r} captured {len(implicit)} implicit input(s) with allow_implicit=False")

    vals = uret.src if is_tuple else (uret,)
    outs = UOp.call_with_outputs(vals, *call_uops, name=name)
    return tuple(Tensor.from_uop(o) for o in outs) if is_tuple else Tensor.from_uop(outs[0])
  return call
