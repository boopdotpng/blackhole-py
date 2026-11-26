import math
from collections.abc import Sequence
from typing import Any, Self, TYPE_CHECKING
from .dtype import DType, dtypes, least_upper_dtype
from . import uop as U  # circular: only touched at call time

if TYPE_CHECKING:
  from .uop import UOp, sint

ConstType = bool | int | float

def _argfix(*x) -> tuple:
  if x and isinstance(x[0], (tuple, list)): return tuple(x[0])
  return tuple(x)

def _axes(axis: int | Sequence[int] | None, ndim: int) -> tuple[int, ...]:
  if axis is None: return tuple(range(ndim))
  out = []
  for a in ((axis,) if isinstance(axis, int) else axis):
    a = a + ndim if a < 0 else a
    if not (0 <= a < ndim): raise IndexError(f"axis {a} out of range for ndim={ndim}")
    out.append(a)
  return tuple(sorted(set(out)))

# float sums accumulate in fp32, bools and narrow ints in i32 (tinygrad's sum_acc_dtype)
def _sum_acc_dtype(dt: DType) -> DType:
  if dt in dtypes.weaks: return dt
  if dt.is_float: return dtypes.fp32
  return dtypes.i32 if dt is dtypes.bool or dt.bits < 32 else dt

class Mixin:
  """The tensor API shared by UOp and Tensor. Every method builds UOps from a few primitives: alu, _mop and REDUCE.
  Broadcasting and dtype promotion are implicit in the graph (a UOp's shape and dtype are derived from its srcs)."""
  __slots__ = ()
  @property
  def _uop(self) -> "UOp": raise NotImplementedError
  @classmethod
  def _wrap_uop(cls, u: "UOp") -> Self: raise NotImplementedError
  def alu(self, op, *src: Self) -> Self: return self._wrap_uop(self._uop.alu(op, *(s._uop for s in src)))
  def _mop(self, op, arg: tuple) -> Self: return self._wrap_uop(self._uop._mop(op, arg))

  # ---- dtype ----

  @property
  def dtype(self) -> DType: return self._uop.dtype
  def cast(self, dtype: DType | str) -> Self:
    dt = dtypes.from_name(dtype)
    return self if self.dtype == dt else self._wrap_uop(U.UOp(U.Ops.CAST, (self._uop,), dt))
  def bitcast(self, dtype: DType | str) -> Self:
    dt = dtypes.from_name(dtype)
    return self if self.dtype == dt else self._wrap_uop(U.UOp(U.Ops.BITCAST, (self._uop,), dt))
  def float(self) -> Self: return self.cast(dtypes.fp32)
  def int(self) -> Self: return self.cast(dtypes.i32)

  # ---- movement ----

  @property
  def shape(self) -> tuple["sint", ...]:
    assert (sh := self._uop.shape) is not None, f"{self._uop.op.name} has no shape"
    return sh
  @property
  def ndim(self) -> int: return len(self.shape)
  @property
  def max_shape(self) -> tuple[int, ...]: return tuple(U.smax(s) for s in self.shape)
  def numel(self) -> "sint": return U.sprod(self.shape)

  def reshape(self, *shape) -> Self:
    sh = tuple(U.simp_sint(x) for x in _argfix(*shape))
    if (neg := [i for i, s in enumerate(sh) if isinstance(s, int) and s == -1]):
      known = U.sprod([s for i, s in enumerate(sh) if i != neg[0]])
      sh = tuple(U.sdiv(self.numel(), known) if i == neg[0] else s for i, s in enumerate(sh))
    return self if self.shape == sh else self._mop(U.Ops.RESHAPE, sh)

  def permute(self, *order) -> Self:
    o = tuple(a + self.ndim if a < 0 else a for a in _argfix(*order))
    return self if o == tuple(range(self.ndim)) else self._mop(U.Ops.PERMUTE, o)
  def transpose(self, dim0: int = 1, dim1: int = 0) -> Self:
    order = list(range(self.ndim))
    order[dim0], order[dim1] = order[dim1], order[dim0]
    return self.permute(order)
  @property
  def T(self) -> Self: return self.permute(tuple(range(self.ndim - 1, -1, -1)))

  # EXPAND only adds dims on the left: squeeze the size-1 dims being expanded, EXPAND them on the left, permute back
  def expand(self, *shape) -> Self:
    new = _argfix(*shape)
    cur = (1,) * (len(new) - self.ndim) + self.shape
    new = tuple(c if n == -1 else U.simp_sint(n) for c, n in zip(cur, new))
    if cur == new: return self.reshape(new)
    if any(c != n and c != 1 for c, n in zip(cur, new)): raise ValueError(f"cannot expand {self.shape} to {new}")
    at = [i for i, (c, n) in enumerate(zip(cur, new)) if c != n]
    kept = [i for i in range(len(new)) if i not in at]
    x = self.reshape(tuple(cur[i] for i in kept))._mop(U.Ops.EXPAND, tuple(new[i] for i in at))
    return x.permute([(at + kept).index(i) for i in range(len(new))])

  # SHRINK/PAD args are (start, end) per axis here; the op stores (offset, size)
  def shrink(self, arg: Sequence[tuple["sint", "sint"] | None]) -> Self:
    b = tuple((0, s) if a is None else (U.simp_sint(a[0]), U.simp_sint(a[1])) for s, a in zip(self.shape, arg, strict=True))
    if b == tuple((0, s) for s in self.shape): return self
    return self._mop(U.Ops.SHRINK, tuple((s, U.simp_sint(e - s)) for s, e in b))

  def pad(self, padding: Sequence[tuple["sint", "sint"] | None], value: ConstType = 0) -> Self:
    p = tuple((0, 0) if x is None else (U.simp_sint(x[0]), U.simp_sint(x[1])) for x in padding)
    if len(p) != self.ndim: raise ValueError(f"pad len {len(p)} != ndim {self.ndim}")
    if all(b == 0 and e == 0 for b, e in p): return self
    padded = self._mop(U.Ops.PAD, tuple((b, U.simp_sint(s + b + e)) for s, (b, e) in zip(self.shape, p)))
    # PAD fills zeros; any other fill selects with a padded all-true mask
    return padded if value == 0 else self.full_like(True, dtypes.bool).pad(p).where(padded, value)

  def squeeze(self, dim: int) -> Self:
    d = dim % self.ndim
    return self if self.shape[d] != 1 else self.reshape(self.shape[:d] + self.shape[d + 1:])
  def unsqueeze(self, dim: int) -> Self:
    d = dim + self.ndim + 1 if dim < 0 else dim
    return self.reshape(self.shape[:d] + (1,) + self.shape[d:])
  def flatten(self, start_dim: int = 0, end_dim: int = -1) -> Self:
    s, e = start_dim % max(self.ndim, 1), end_dim % max(self.ndim, 1)
    return self.reshape(self.shape[:s] + (U.sprod(self.shape[s:e + 1]),) + self.shape[e + 1:])

  def repeat(self, *repeats) -> Self:
    reps = _argfix(*repeats)
    base = self.reshape((1,) * (len(reps) - self.ndim) + self.shape)
    x = base.reshape(tuple(v for s in base.shape for v in (1, s))).expand(tuple(v for r, s in zip(reps, base.shape) for v in (r, s)))
    return x.reshape(tuple(U.simp_sint(r * s) for r, s in zip(reps, base.shape)))
  def repeat_interleave(self, repeats: int, dim: int) -> Self:
    d = dim % self.ndim
    return self.unsqueeze(d + 1).expand(*self.shape[:d + 1], repeats, *self.shape[d + 1:]) \
      .reshape(*self.shape[:d], U.simp_sint(self.shape[d] * repeats), *self.shape[d + 1:])

  # cat is pad-and-add: each input is padded to the full length along dim and the disjoint pieces summed
  def cat(self, *args: Self, dim: int = 0) -> Self:
    ts = [self, *args]
    dt = least_upper_dtype(*(t.dtype for t in ts))
    d = dim % self.ndim
    total = U.simp_sint(sum((t.shape[d] for t in ts[1:]), ts[0].shape[d]))
    out, off = None, 0
    for t in ts:
      p = t.cast(dt).pad(tuple((off, U.simp_sint(total - off - t.shape[d])) if i == d else None for i in range(t.ndim)))
      out = p if out is None else ((out | p) if dt is dtypes.bool else (out + p))
      off = U.simp_sint(off + t.shape[d])
    return out
  def stack(self, *args: Self, dim: int = 0) -> Self:
    return self.unsqueeze(dim).cat(*(t.unsqueeze(dim) for t in args), dim=dim)

  # ---- creation ----

  @classmethod
  def const(cls, v: ConstType, dtype: DType | str | None = None) -> Self: return cls._wrap_uop(U.UOp.const(v, dtype))
  @classmethod
  def full(cls, shape: tuple["sint", ...] | "sint", fill_value: ConstType, dtype: DType | str | None = None) -> Self:
    sh = shape if isinstance(shape, tuple) else (shape,)
    dt = dtypes.from_name(dtype) if dtype is not None else \
      dtypes.bool if isinstance(fill_value, bool) else dtypes.i32 if isinstance(fill_value, int) else dtypes.fp32
    c = cls.const(fill_value, dt)
    return c._mop(U.Ops.EXPAND, sh) if sh else c
  @classmethod
  def zeros(cls, *shape, dtype: DType | str = dtypes.fp32) -> Self: return cls.full(_argfix(*shape), 0, dtype)
  @classmethod
  def ones(cls, *shape, dtype: DType | str = dtypes.fp32) -> Self: return cls.full(_argfix(*shape), 1, dtype)
  def full_like(self, fill_value: ConstType, dtype: DType | str | None = None) -> Self:
    return type(self).full(self.shape, fill_value, self.dtype if dtype is None else dtype)

  # cumsum of a 1D tensor: tile the front-padded input so row i of an (n, 2n) view starts at element i, keep the
  # first n columns (the window ending at i) and sum them
  def _cumsum(self) -> Self:
    n = self.shape[0]
    rows = self.pad(((n - 1, 0),)).repeat(n).pad(((0, n),)).reshape(n, 2 * n).shrink((None, (0, n)))
    return rows.sum(1, dtype=self.dtype)

  # no ARANGE op: a cumsum of `step`s, as in tinygrad
  @classmethod
  def arange(cls, start: int | float, stop: int | float | None = None, step: int | float = 1, dtype: DType | str | None = None) -> Self:
    if stop is None: start, stop = 0, start
    dt = dtypes.from_name(dtype) if dtype is not None else \
      dtypes.fp32 if any(isinstance(v, float) for v in (start, stop, step)) else dtypes.i32
    n = max(0, math.ceil((stop - start) / step))
    return (cls.full((n,), step, dtypes.fp32 if dt.is_float else dtypes.i32)._cumsum() + (start - step)).cast(dt)

  # ---- elementwise ----

  # python constants become weak CONSTs; a Tensor operand lifts a UOp operand to Tensor
  def _ufix(self, x: Any) -> Self:
    if isinstance(x, Mixin): return x if type(x) is type(self) or x._uop is not x else self._wrap_uop(x._uop)  # type: ignore[return-value]
    if isinstance(x, (bool, int, float)): return self._wrap_uop(U.UOp.const(x))
    raise TypeError(f"cannot use {type(x).__name__} as an operand")
  def _broadcasted(self, y: Any, reverse: bool = False) -> tuple[Self, Self]:
    y = self._ufix(y)
    x = y._ufix(self) if type(y) is not type(self) else self
    if reverse: x, y = y, x
    # weak operands don't need a cast: the node's dtype promotes them
    dt = least_upper_dtype(x.dtype, y.dtype)
    return (x if x.dtype in dtypes.weaks else x.cast(dt)), (y if y.dtype in dtypes.weaks else y.cast(dt))
  def _binop(self, op, y: Any, reverse: bool = False) -> Self:
    a, b = self._broadcasted(y, reverse)
    return a.alu(op, b)

  def contiguous(self) -> Self:
    u = self._uop
    return self if u.op is U.Ops.STAGE or u.has_buffer_identity() else self._wrap_uop(U.UOp(U.Ops.STAGE, (u,)))

  def neg(self) -> Self: return self.alu(U.Ops.NEG)
  def exp2(self) -> Self: return self.alu(U.Ops.EXP2)
  def log2(self) -> Self: return self.alu(U.Ops.LOG2)
  def sin(self) -> Self: return self.alu(U.Ops.SIN)
  def sqrt(self) -> Self: return self.alu(U.Ops.SQRT)
  def recip(self) -> Self: return self.alu(U.Ops.RECIP)
  def rsqrt(self) -> Self: return self.sqrt().recip()
  def cos(self) -> Self: return ((math.pi / 2.0) - self).sin()
  def exp(self) -> Self: return (self * (1.0 / math.log(2.0))).exp2()
  def log(self) -> Self: return self.log2() * math.log(2.0)
  def square(self) -> Self: return self * self
  def abs(self) -> Self: return (self < 0).where(-self, self)
  def sigmoid(self) -> Self: return (1.0 + (-self).exp()).recip()
  def silu(self) -> Self: return self * self.sigmoid()
  def relu(self) -> Self: return self.maximum(0.0)

  def add(self, x: Any, reverse: bool = False) -> Self: return self._binop(U.Ops.ADD, x, reverse)
  def sub(self, x: Any, reverse: bool = False) -> Self: return self._binop(U.Ops.SUB, x, reverse)
  def mul(self, x: Any, reverse: bool = False) -> Self: return self._binop(U.Ops.MUL, x, reverse)
  def div(self, x: Any, reverse: bool = False) -> Self:
    a, b = self._broadcasted(x, reverse)
    if not a.dtype.is_float or not b.dtype.is_float: a, b = (a if a.dtype.is_float else a.float()), (b if b.dtype.is_float else b.float())
    return a.alu(U.Ops.DIV, b)
  # x ** y = exp2(y * log2(x)), so x must be positive
  def pow(self, x: Any, reverse: bool = False) -> Self:
    a, b = self._broadcasted(x, reverse)
    return (b * a.log2()).exp2()
  def maximum(self, x: Any) -> Self: return self._binop(U.Ops.MAX, x)
  # no MIN op: max of the inverses (negation for floats, bitwise not for ints)
  def minimum(self, x: Any) -> Self:
    a, b = self._broadcasted(x)
    return -((-a).maximum(-b)) if (a.dtype.is_float or b.dtype.is_float) else ~((~a).maximum(~b))
  def clip(self, min_: Any, max_: Any) -> Self: return self.maximum(min_).minimum(max_)
  def eq(self, x: Any) -> Self: return self._binop(U.Ops.CMPEQ, x)
  def ne(self, x: Any) -> Self: return self._binop(U.Ops.CMPNE, x)

  def where(self, x: Any, y: Any) -> Self:
    cond = self if self.dtype is dtypes.bool else self.ne(0)
    a, b = (x if isinstance(x, Mixin) else self._ufix(x))._broadcasted(y)
    return cond.alu(U.Ops.WHERE, a, b)

  def __neg__(self) -> Self: return self.neg()
  # no NOT op: xor with all-ones
  def __invert__(self) -> Self: return self ^ (True if self.dtype is dtypes.bool else -1)
  def __add__(self, x) -> Self: return self.add(x)
  def __radd__(self, x) -> Self: return self.add(x, True)
  def __sub__(self, x) -> Self: return self.sub(x)
  def __rsub__(self, x) -> Self: return self.sub(x, True)
  def __mul__(self, x) -> Self: return self.mul(x)
  def __rmul__(self, x) -> Self: return self.mul(x, True)
  def __truediv__(self, x) -> Self: return self.div(x)
  def __rtruediv__(self, x) -> Self: return self.div(x, True)
  def __floordiv__(self, x) -> Self:
    if self.dtype.is_float: raise TypeError("// is integer division")
    return self._binop(U.Ops.DIV, x)
  def __mod__(self, x) -> Self: return self._binop(U.Ops.MOD, x)
  def __pow__(self, x) -> Self: return self.pow(x)
  def __rpow__(self, x) -> Self: return self.pow(x, True)
  def __abs__(self) -> Self: return self.abs()
  def __and__(self, x) -> Self: return self._binop(U.Ops.AND, x)
  def __or__(self, x) -> Self: return self._binop(U.Ops.OR, x)
  def __xor__(self, x) -> Self: return self._binop(U.Ops.XOR, x)
  def __lshift__(self, x) -> Self: return self._binop(U.Ops.SHL, x)
  def __rshift__(self, x) -> Self: return self._binop(U.Ops.SHR, x)
  def __lt__(self, x) -> Self: return self._binop(U.Ops.CMPLT, x)
  def __gt__(self, x) -> Self: return self._binop(U.Ops.CMPLT, x, True)
  def __le__(self, x) -> Self: return ~self._binop(U.Ops.CMPLT, x, True)
  def __ge__(self, x) -> Self: return ~self._binop(U.Ops.CMPLT, x)
  # NOTE: __eq__/__ne__ are not overridden here so UOp keeps hash-consing identity

  # ---- reductions ----

  # REDUCE reduces leading axes: permute the reduced axes to the front, reduce, and put back size-1 dims for keepdim
  def _reduce(self, op, axis: int | Sequence[int] | None, keepdim: bool) -> Self:
    axes = _axes(axis, self.ndim)
    if not axes: return self
    x = self.permute(axes + tuple(i for i in range(self.ndim) if i not in axes))
    out = self._wrap_uop(U.UOp(U.Ops.REDUCE, (x._uop,), (op, len(axes))))
    return out.reshape(tuple(1 if i in axes else s for i, s in enumerate(self.shape))) if keepdim else out

  def sum(self, axis: int | Sequence[int] | None = None, keepdim: bool = False, dtype: DType | str | None = None) -> Self:
    out = self.cast(dtypes.from_name(dtype) if dtype is not None else _sum_acc_dtype(self.dtype))._reduce(U.Ops.ADD, axis, keepdim)
    return out.cast(self.dtype) if dtype is None and self.dtype in (dtypes.bf16, dtypes.bfp8, dtypes.bfp4, dtypes.e4m3) else out
  def max(self, axis: int | Sequence[int] | None = None, keepdim: bool = False) -> Self: return self._reduce(U.Ops.MAX, axis, keepdim)
  def min(self, axis: int | Sequence[int] | None = None, keepdim: bool = False) -> Self:
    inv = (lambda t: -t) if self.dtype.is_float else (lambda t: ~t)
    return inv(inv(self)._reduce(U.Ops.MAX, axis, keepdim))
  def mean(self, axis: int | Sequence[int] | None = None, keepdim: bool = False) -> Self:
    n = U.sprod([self.shape[a] for a in _axes(axis, self.ndim)])
    s = (self if self.dtype.is_float else self.float()).sum(axis, keepdim)
    return s * (1.0 / n) if isinstance(n, int) else s / n

  # index of the first maximum: the largest of (n - i) over positions equal to the max
  def argmax(self, axis: int | None = None, keepdim: bool = False) -> Self:
    if axis is None: return self.flatten().argmax(0)
    ax = axis % self.ndim
    n = self.shape[ax]
    rev = type(self).arange(n, 0, -1).reshape(n, *[1] * (self.ndim - ax - 1))
    m = self.eq(self.max(axis=ax, keepdim=True)).where(rev, 0)
    return (n - m.max(axis=ax, keepdim=keepdim)).cast(dtypes.i32)

  def softmax(self, axis: int = -1) -> Self:
    e = (self - self.max(axis=axis, keepdim=True)).exp()
    return e * e.sum(axis=axis, keepdim=True).recip()

  def matmul(self, w: Self, dtype: DType | str | None = None) -> Self:
    if self.ndim < 2 or w.ndim < 2: raise ValueError(f"matmul needs >= 2D operands, got {self.shape} @ {w.shape}")
    if self.shape[-1] != w.shape[-2]: raise ValueError(f"matmul inner dim mismatch: {self.shape} @ {w.shape}")
    xa, wa = self.unsqueeze(-2), w.transpose(-1, -2)
    if wa.ndim >= 3: wa = wa.unsqueeze(-3)  # (..., M, 1, K) * (..., 1, N, K); 2D (N, K) broadcasts directly
    if dtype is not None: xa, wa = xa.cast(dtype), wa.cast(dtype)
    return (xa * wa).sum(axis=-1, dtype=dtype)
  def __matmul__(self, x: Self) -> Self: return self.matmul(x)
