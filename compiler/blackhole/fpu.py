"""Declarative compute matching, independent of addresses and scheduling."""
from dataclasses import dataclass
from typing import Callable
from ..dtype import DType, dtypes
from ..uop import Ops, UOp


@dataclass(frozen=True)
class FpuRule:
  op: str
  tile: tuple[int, int, int]
  dtypes_in: tuple[DType, ...]
  dtype_out: DType
  fidelity: Callable[[DType], int]


def fidelity(dtype): return 1 if dtype is dtypes.bfp4 else 2 if dtype is dtypes.bfp8 else 3


MVMUL = FpuRule("MVMUL", (16, 8, 16), (dtypes.bf16, dtypes.bfp8, dtypes.bfp4, dtypes.fp32), dtypes.fp32, fidelity)
FPU_RULES = (MVMUL,)


def uncast(u):
  while u.op is Ops.CAST: u = u.src[0]
  return u


@dataclass(frozen=True)
class MatchedMvmul:
  reduce_uop: UOp
  act: UOp
  weight: UOp
  m_axes: tuple[UOp, ...]
  n_axes: tuple[UOp, ...]
  k_axes: tuple[UOp, ...]
  batch_axes: tuple[UOp, ...]
  rule: FpuRule = MVMUL


@dataclass(frozen=True)
class MatchedRowReduce:
  reduce_uop: UOp
  op: Ops
  k_axis: UOp
  body: UOp
  nested_deps: tuple[UOp, ...]


def match_reductions(kernel):
  """Classify every reduction bottom-up using only operand range membership.

  Storage casts are unwrapped for dtype checks, never for address analysis.
  Broadcast-only batch dimensions remain free output axes; physical axis
  placement is the later address classifier's responsibility.
  """
  nodes = kernel.toposort()
  order = {u: i for i, u in enumerate(nodes)}
  def ordered(ranges): return tuple(sorted(ranges, key=order.__getitem__))
  matches = {}
  for red in nodes:
    if red.op is not Ops.REDUCE: continue
    body, reduced = red.src[0], frozenset(red.src[1:])
    dot = uncast(body)
    if red.arg[0] is Ops.ADD and dot.op is Ops.MUL:
      a, b = dot.src
      common = a.ranges & b.ranges
      k = reduced & common
      m, n = a.ranges - b.ranges - reduced, b.ranges - a.ranges - reduced
      if k and (m or n):
        if k != reduced or any(uncast(v).dtype not in MVMUL.dtypes_in for v in (a, b)):
          raise NotImplementedError(f"unsupported MVMUL reduction {red}")
        if not n: a, b, m, n = b, a, n, m
        matches[red] = MatchedMvmul(red, a, b, ordered(m), ordered(n), ordered(k), ordered(common - reduced))
        continue
    if red.arg[0] in (Ops.ADD, Ops.MAX) and len(reduced) == 1:
      kr, = red.src[1:]
      bound = kr.src[0]
      if bound.is_const or bound.is_variable:
        nested = tuple(u for u in body.toposort() if u.op is Ops.REDUCE)
        if all(u in matches for u in nested):
          matches[red] = MatchedRowReduce(red, red.arg[0], kr, body, nested)
          continue
    raise NotImplementedError(f"unmatched reduction {red.arg[0].name} over {red.src[1:]}")
  return matches
