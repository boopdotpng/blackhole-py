"""Logical tile coordinates and physical face layout."""
from collections.abc import Mapping
from dataclasses import dataclass
from math import prod
from types import MappingProxyType
from ..dtype import dtypes
from ..uop import Ops, UOp


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


def dimensions(shape):
  return (prod(shape[:-2]) if len(shape) > 2 else 1, shape[-2] if len(shape) > 1 else 1, shape[-1] if shape else 1)


def expression_nodes(root):
  out, seen = [], set()
  def walk(u):
    if u in seen: return
    seen.add(u)
    if u.op not in (Ops.LOAD, Ops.REDUCE):
      for source in u.src_without_body: walk(source)
    out.append(u)
  walk(root)
  return out


def column_axis(width, strides):
  return next((r for r, stride in strides.items() if stride == 1 and int(r.src[0].val) == width), None)


@dataclass(frozen=True)
class TileView:
  n: int
  strides: Mapping[UOp, int]
  tile: UOp
  block_index: int = 0

  def __post_init__(self): object.__setattr__(self, "strides", MappingProxyType(dict(self.strides)))

  @property
  def nf(self): return (self.n + 15) // 16

  @property
  def column(self):
    return column_axis(self.n, self.strides)

  def reindex(self, axis, width, column):
    strides = {r: stride // self.n * width for r, stride in self.strides.items() if r is not self.column}
    return TileView(width, {**strides, axis: 1}, self.tile // self.nf * ((width + 15) // 16) + column)
