import math
from collections.abc import Sequence
from typing import Any, NamedTuple, Self, TYPE_CHECKING
from .dtype import DType, Space, dtypes, least_upper_dtype

if TYPE_CHECKING:
  from .uop import UOp, sint

def _argfix(*x) -> tuple:
  if x and isinstance(x[0], (tuple, list)): return tuple(x[0])
  return tuple(x)

def _canonicalize_axes(axis: int | Sequence[int] | None, ndim: int) -> tuple[int, ...]:
  if axis is None: return tuple(range(ndim))
  axes = (axis,) if isinstance(axis, int) else tuple(axis)
  out = []
  for a in axes:
    a = a + ndim if a < 0 else a
    if not (0 <= a < ndim): raise IndexError(f"axis {a} out of range for ndim={ndim}")
    out.append(a)
  return tuple(sorted(set(out)))

class TopkResult(NamedTuple):
  values: Any
  indices: Any

class DTypeMixin:
  __slots__ = ()
  @property
  def _uop(self) -> "UOp": raise NotImplementedError
  @classmethod
  def _wrap_uop(cls, u: "UOp") -> Self: raise NotImplementedError

  @property
  def dtype(self) -> DType: return self._uop.dtype
  def element_size(self) -> int: return max(1, self.dtype.bits // 8)
  def is_floating_point(self) -> bool: return self.dtype.is_float

  def cast(self, dtype: DType | str) -> Self:
    from .uop import Ops, UOp
    dt = dtypes.from_name(dtype)
    return self if self.dtype == dt else self._wrap_uop(UOp(Ops.CAST, dt, (self._uop,)))

  def bitcast(self, dtype: DType | str) -> Self:
    from .uop import Ops, UOp
    dt = dtypes.from_name(dtype)
    return self if self.dtype == dt else self._wrap_uop(UOp(Ops.BITCAST, dt, (self._uop,)))

  def float(self) -> Self: return self.cast(dtypes.fp32)
  def fp32(self) -> Self: return self.cast(dtypes.fp32)
  def bfloat16(self) -> Self: return self.cast(dtypes.bf16)
  def bf16(self) -> Self: return self.cast(dtypes.bf16)
  def int(self) -> Self: return self.cast(dtypes.i32)
  def i32(self) -> Self: return self.cast(dtypes.i32)
  def u32(self) -> Self: return self.cast(dtypes.u32)
  def u8(self) -> Self: return self.cast(dtypes.u8)
  def bool(self) -> Self: return self.cast(dtypes.bool)

class MovementMixin(DTypeMixin):
  __slots__ = ()
  @property
  def shape(self) -> tuple["sint", ...]:
    sh = self._uop.shape
    assert sh is not None, f"{self._uop.op.name} has no shape"
    return sh

  @property
  def max_shape(self) -> tuple[int, ...]:
    from .uop import smax
    return tuple(smax(s) for s in self.shape)

  @property
  def ndim(self) -> int: return len(self.shape)

  def numel(self) -> "sint":
    from .uop import sprod
    return sprod(self.shape)

  def nbytes(self) -> int:
    from .uop import smax
    return (smax(self.numel()) * self.dtype.bits + 7) // 8

  def size(self, dim: int | None = None) -> "sint | tuple[sint, ...]":
    return self.shape if dim is None else self.shape[dim]

  def reshape(self, *shape) -> Self:
    from .uop import Ops, UOp, sdiv, simp_sint, sprod
    sh = tuple(simp_sint(x) for x in _argfix(*shape))
    neg = [i for i, s in enumerate(sh) if isinstance(s, int) and s == -1]
    if neg:
      if len(neg) > 1: raise ValueError(f"only one -1 allowed in reshape {sh}")
      known = sprod([s for i, s in enumerate(sh) if i != neg[0]])
      inferred = sdiv(self.numel(), known)
      sh = tuple(inferred if i == neg[0] else s for i, s in enumerate(sh))
    u = self._uop
    return self if u.shape == sh else self._wrap_uop(UOp(Ops.RESHAPE, u.dtype, (u,), sh))

  view = reshape

  def expand(self, *shape) -> Self:
    from .uop import Ops, UOp, simp_sint
    sh = tuple(simp_sint(x) for x in _argfix(*shape))
    if len(sh) < self.ndim: raise ValueError(f"cannot expand {self.shape} to fewer dims {sh}")
    cur = self.reshape((1,) * (len(sh) - self.ndim) + self.shape) if len(sh) > self.ndim else self
    target = tuple(s if (isinstance(e, int) and e == -1) else e for s, e in zip(cur.shape, sh))
    u = cur._uop
    return cur if u.shape == target else self._wrap_uop(UOp(Ops.EXPAND, u.dtype, (u,), target))

  def permute(self, *order) -> Self:
    from .uop import Ops, UOp
    ord_ = tuple(int(a + self.ndim if a < 0 else a) for a in _argfix(*order))
    u = self._uop
    return self if u.shape is not None and ord_ == tuple(range(len(u.shape))) else self._wrap_uop(UOp(Ops.PERMUTE, u.dtype, (u,), ord_))

  def transpose(self, dim0: int = 1, dim1: int = 0) -> Self:
    order = list(range(self.ndim))
    order[dim0], order[dim1] = order[dim1], order[dim0]
    return self.permute(order)

  @property
  def T(self) -> Self: return self.permute(tuple(range(self.ndim - 1, -1, -1)))

  @property
  def mT(self) -> Self: return self.transpose(-2, -1)

  def flip(self, axis: int | Sequence[int] | Sequence[bool], *args) -> Self:
    from .uop import Ops, UOp
    if not args and isinstance(axis, tuple) and axis and all(type(x) is bool for x in axis):
      mask = axis
    else:
      axes = _canonicalize_axes((axis, *args) if args else axis, self.ndim)
      mask = tuple(i in axes for i in range(self.ndim))
    u = self._uop
    return self if not any(mask) else self._wrap_uop(UOp(Ops.FLIP, u.dtype, (u,), mask))

  def shrink(self, arg: Sequence[tuple["sint", "sint"] | None]) -> Self:
    from .uop import Ops, UOp, simp_sint
    if len(arg) != self.ndim: raise ValueError(f"shrink arg len {len(arg)} != ndim {self.ndim}")
    bounds = tuple((0, s) if a is None else (simp_sint(a[0]), simp_sint(a[1])) for s, a in zip(self.shape, arg))
    u = self._uop
    if u.shape is not None and bounds == tuple((0, s) for s in u.shape): return self
    return self._wrap_uop(UOp(Ops.SHRINK, u.dtype, (u,), bounds))

  def pad(self, padding: Sequence[int] | Sequence[tuple["sint", "sint"] | None], mode: str = "constant",
          value: bool | int | float = 0.0) -> Self:
    from .uop import Ops, UOp, simp_sint
    if mode != "constant": raise NotImplementedError(f"pad mode {mode!r} not implemented")
    if padding and all(isinstance(p, int) for p in padding):
      if len(padding) % 2 != 0: raise ValueError(f"flat pad must have even length, got {padding}")
      pairs = [(int(padding[i]), int(padding[i + 1])) for i in range(0, len(padding), 2)][::-1]
      pads = ((0, 0),) * (self.ndim - len(pairs)) + tuple(pairs)
    else:
      if len(padding) != self.ndim: raise ValueError(f"pad len {len(padding)} != ndim {self.ndim}")
      pads = tuple((0, 0) if p is None else (simp_sint(p[0]), simp_sint(p[1])) for p in padding)
    if all(b == 0 and e == 0 for b, e in pads): return self
    padded = self._wrap_uop(UOp(Ops.PAD, self.dtype, (self._uop,), pads))
    if value == 0 or value is False: return padded
    c_true = UOp.const(dtypes.bool, True)
    ones = c_true if not self.shape else c_true.reshape((1,) * self.ndim).expand(self.shape)
    mask = self._wrap_uop(ones).pad(pads)
    return mask.where(padded, value)

  def pad_to(self, *shape) -> Self:
    from .uop import simp_sint
    sh = _argfix(*shape)
    return self.pad(tuple((0, simp_sint(e - s)) for s, e in zip(self.shape, sh)))

  def shrink_to(self, *shape) -> Self:
    sh = _argfix(*shape)
    return self.shrink(tuple((0, e) for e in sh))

  def squeeze(self, dim: int | None = None) -> Self:
    if dim is None: return self.reshape(tuple(s for s in self.shape if s != 1))
    d = dim + self.ndim if dim < 0 else dim
    if not (0 <= d < self.ndim): raise IndexError(f"squeeze dim {dim} out of range for {self.shape}")
    return self if self.shape[d] != 1 else self.reshape(self.shape[:d] + self.shape[d + 1:])

  def unsqueeze(self, dim: int) -> Self:
    d = dim + self.ndim + 1 if dim < 0 else dim
    if not (0 <= d <= self.ndim): raise IndexError(f"unsqueeze dim {dim} out of range for {self.shape}")
    return self.reshape(self.shape[:d] + (1,) + self.shape[d:])

  def flatten(self, start_dim: int = 0, end_dim: int = -1) -> Self:
    from .uop import sprod
    s = start_dim + self.ndim if start_dim < 0 else start_dim
    e = end_dim + self.ndim if end_dim < 0 else end_dim
    return self.reshape(self.shape[:s] + (sprod(self.shape[s:e + 1]),) + self.shape[e + 1:])

  def unflatten(self, dim: int, sizes: tuple["sint", ...]) -> Self:
    d = dim + self.ndim if dim < 0 else dim
    return self.reshape(self.shape[:d] + tuple(sizes) + self.shape[d + 1:])

  def repeat(self, *repeats) -> Self:
    from .uop import simp_sint
    reps = _argfix(*repeats)
    base = self.reshape((1,) * (len(reps) - self.ndim) + self.shape) if len(reps) > self.ndim else self
    unsqueezed = base.reshape(tuple(x for s in base.shape for x in (1, s)))
    expanded = unsqueezed.expand(tuple(x for r, s in zip(reps, base.shape) for x in (r, s)))
    return expanded.reshape(tuple(simp_sint(r * s) for r, s in zip(reps, base.shape)))

  def repeat_interleave(self, repeats: int, dim: int | None = None) -> Self:
    from .uop import simp_sint
    x = self.flatten() if dim is None else self
    d = 0 if dim is None else (dim + x.ndim if dim < 0 else dim)
    return x.unsqueeze(d + 1).expand(*x.shape[:d + 1], repeats, *x.shape[d + 1:]).reshape(
      *x.shape[:d], simp_sint(x.shape[d] * repeats), *x.shape[d + 1:]
    )

  def split(self, sizes: int | Sequence[int], dim: int = 0) -> tuple[Self, ...]:
    d = dim + self.ndim if dim < 0 else dim
    total = self.shape[d]
    if isinstance(sizes, int):
      lens = [sizes] * (total // sizes) + ([total % sizes] if total % sizes else [])
    else:
      lens = list(sizes)
      if sum(lens) != total: raise ValueError(f"split sizes {lens} do not sum to {total}")
    out, off = [], 0
    for n in lens:
      out.append(self.shrink(tuple((off, off + n) if i == d else None for i in range(self.ndim))))
      off += n
    return tuple(out)

  def chunk(self, chunks: int, dim: int = 0) -> tuple[Self, ...]:
    d = dim + self.ndim if dim < 0 else dim
    size = math.ceil(self.shape[d] / chunks)
    return self.split(size, dim=d)

  def unfold(self, dim: int, size: int, step: int) -> Self:
    from .uop import UOp
    d = dim + self.ndim if dim < 0 else dim
    L = self.shape[d]
    if size > L: raise ValueError(f"unfold size {size} > dim {L}")
    n_win = (L - size) // step + 1
    idx = self._wrap_uop(UOp.arange(0, n_win, 1, dtypes.i32)).reshape(n_win, 1) * step + \
          self._wrap_uop(UOp.arange(0, size, 1, dtypes.i32)).reshape(1, size)
    out = self.take(idx, dim=d)
    perm = list(range(out.ndim))
    perm.append(perm.pop(d + 1))
    return out.permute(perm)

  def roll(self, shifts: int | Sequence[int], dims: int | Sequence[int] | None = None) -> Self:
    if dims is None: return self.flatten().roll(shifts, 0).reshape(self.shape)
    shs = (shifts,) if isinstance(shifts, int) else tuple(shifts)
    dms = (dims,) if isinstance(dims, int) else tuple(dims)
    x = self
    for sh, d in zip(shs, dms):
      d = d + x.ndim if d < 0 else d
      n = x.shape[d]
      k = (-sh) % n
      if k == 0: continue
      a = x.shrink(tuple((k, n) if i == d else None for i in range(x.ndim)))
      b = x.shrink(tuple((0, k) if i == d else None for i in range(x.ndim)))
      x = a.cat(b, dim=d)
    return x

  @classmethod
  def _cat_list(cls, tensors: Sequence[Self], dim: int = 0) -> Self:
    from .uop import simp_sint
    if not tensors: raise ValueError("cat requires at least one tensor")
    if len(tensors) == 1: return tensors[0]
    dt = least_upper_dtype(*(t.dtype for t in tensors))
    ts = [t.cast(dt) for t in tensors]
    d = dim + ts[0].ndim if dim < 0 else dim
    total: sint = 0
    for t in ts: total = simp_sint(total + t.shape[d])
    off: sint = 0
    parts: list[Self] = []
    for t in ts:
      n = t.shape[d]
      pads = tuple((off, simp_sint(total - off - n)) if i == d else (0, 0) for i in range(t.ndim))
      parts.append(t.pad(pads))
      off = simp_sint(off + n)
    acc = parts[0]
    for p in parts[1:]:
      acc = (acc | p) if dt is dtypes.bool else (acc + p)
    return acc

  def cat(self, *args: Self, dim: int = 0) -> Self:
    if isinstance(self, (list, tuple)): return type(self[0])._cat_list(self, dim=dim)  # type: ignore[arg-type]
    return type(self)._cat_list([self, *args], dim=dim)

  def stack(self, *args: Self, dim: int = 0) -> Self:
    ts = list(self) if isinstance(self, (list, tuple)) else [self, *args]
    return type(ts[0])._cat_list([t.unsqueeze(dim) for t in ts], dim=dim)

  def take(self, index: Any, dim: int = 0) -> Self:
    from .uop import Ops, UOp
    d = dim + self.ndim if dim < 0 else dim
    idx = index._uop if isinstance(index, DTypeMixin) else UOp.const(dtypes.i32, index)
    return self._wrap_uop(UOp(Ops.TAKE, self.dtype, (self._uop, idx), int(d)))

  def gather(self, dim: int, index: Any) -> Self:
    from .uop import Ops, UOp
    d = dim + self.ndim if dim < 0 else dim
    idx = index._uop if isinstance(index, DTypeMixin) else UOp.const(dtypes.i32, index)
    return self._wrap_uop(UOp(Ops.GATHER, self.dtype, (self._uop, idx), int(d)))

  def scatter_update(self, dim: int, index: Any, value: Any) -> Self:
    from .uop import Ops, UOp
    d = dim + self.ndim if dim < 0 else dim
    idx = index._uop if isinstance(index, DTypeMixin) else UOp.const(dtypes.i32, index)
    val = value._uop if isinstance(value, DTypeMixin) else UOp.const(self.dtype, value)
    return self._wrap_uop(UOp(Ops.SCATTER, self.dtype, (self._uop, idx, val.cast(self.dtype)), int(d)))

class ElementwiseMixin(MovementMixin):
  __slots__ = ()
  def _coerce_other(self, y: Any) -> Self:
    from .uop import UOp
    if isinstance(y, DTypeMixin):
      # If self is UOp and y is Tensor, lift to Tensor; otherwise wrap into type(self)
      if type(y) is not type(self) and y._uop is not y: return y  # type: ignore[return-value]
      return self._wrap_uop(y._uop)
    if isinstance(y, bool): return self._wrap_uop(UOp.const(dtypes.bool, y))
    if isinstance(y, int):
      dt = self.dtype if (self.dtype.is_int or self.dtype.is_float) else dtypes.i32
      return self._wrap_uop(UOp.const(dt, y))
    if isinstance(y, float):
      dt = self.dtype if self.dtype.is_float else dtypes.fp32
      return self._wrap_uop(UOp.const(dt, y))
    raise TypeError(f"cannot coerce {type(y).__name__} to {type(self).__name__}")

  def _broadcasted(self, y: Any, reverse: bool = False) -> tuple[Self, Self]:
    from .uop import sbcast, _SRC_BANKS
    x, other = self, self._coerce_other(y)
    if type(other) is not type(x) and other._uop is not other:
      x = other._wrap_uop(x._uop)
    if reverse: x, other = other, x
    xu, yu = x._uop, other._uop
    # Layer 1 / unshaped UOps (Dst, LReg, SrcA/SrcB, scalar): preserve strict dtype check & FPU fidelity
    if xu.space is not Space.TENSOR and yu.space is not Space.TENSOR and (xu.shape is None or yu.shape is None or (xu.shape == () and yu.shape == ())):
      if xu.dtype != yu.dtype:
        if xu.space in _SRC_BANKS and yu.space in _SRC_BANKS and xu.dtype.is_float and yu.dtype.is_float:
          return x, other
        if isinstance(y, (bool, int, float)):
          other = x._wrap_uop(xu._coerce(y)) if not reverse else other
          x = other._wrap_uop(yu._coerce(y)) if reverse else x
          return x, other
        raise TypeError(f"dtype mismatch: {xu.dtype} vs {yu.dtype} (use explicit .cast())")
      return x, other
    dt = least_upper_dtype(x.dtype, other.dtype)
    x, other = x.cast(dt), other.cast(dt)
    xs, ys = x.shape, other.shape
    if xs == ys: return x, other
    nd = max(len(xs), len(ys))
    xs = (1,) * (nd - len(xs)) + xs
    ys = (1,) * (nd - len(ys)) + ys
    sh = tuple(sbcast(a, b) for a, b in zip(xs, ys))
    return x.reshape(xs).expand(sh), other.reshape(ys).expand(sh)

  def _binop(self, op, y: Any, reverse: bool = False) -> Self:
    a, b = self._broadcasted(y, reverse=reverse)
    return a._wrap_uop(a._uop.alu(op, b._uop))

  def contiguous(self) -> Self:
    from .uop import Ops, UOp
    u = self._uop
    return self if u.op is Ops.CONTIGUOUS else self._wrap_uop(UOp(Ops.CONTIGUOUS, u.dtype, (u,)))

  def neg(self) -> Self:
    from .uop import Ops
    return self._wrap_uop(self._uop.alu(Ops.NEG))

  def abs(self) -> Self:
    from .uop import Ops
    return self._wrap_uop(self._uop.alu(Ops.ABS))

  def logical_not(self) -> Self:
    from .uop import Ops
    return self._wrap_uop(self.cast(dtypes.bool)._uop.alu(Ops.NOT))

  def bitwise_not(self) -> Self:
    from .uop import Ops
    return self._wrap_uop(self._uop.alu(Ops.NOT))

  def exp2(self) -> Self:
    from .uop import Ops
    return self._wrap_uop(self._uop.alu(Ops.EXP2))

  def log2(self) -> Self:
    from .uop import Ops
    return self._wrap_uop(self._uop.alu(Ops.LOG2))

  def sin(self) -> Self:
    from .uop import Ops
    return self._wrap_uop(self._uop.alu(Ops.SIN))

  def cos(self) -> Self: return ((math.pi / 2.0) - self).sin()

  def sqrt(self) -> Self:
    from .uop import Ops
    return self._wrap_uop(self._uop.alu(Ops.SQRT))

  def rsqrt(self) -> Self:
    from .uop import Ops
    return self._wrap_uop(self._uop.alu(Ops.RSQRT))

  def reciprocal(self) -> Self:
    from .uop import Ops
    return self._wrap_uop(self._uop.alu(Ops.RECIP))
  recip = reciprocal

  def exp(self) -> Self: return (self * (1.0 / math.log(2.0))).exp2()
  def log(self) -> Self: return self.log2() * math.log(2.0)
  def square(self) -> Self: return self * self
  def sign(self) -> Self: return (self > 0).cast(self.dtype) - (self < 0).cast(self.dtype)

  def add(self, x: Any, reverse: bool = False) -> Self:
    from .uop import Ops
    return self._binop(Ops.ADD, x, reverse)

  def sub(self, x: Any, reverse: bool = False) -> Self:
    from .uop import Ops
    return self._binop(Ops.SUB, x, reverse)

  def mul(self, x: Any, reverse: bool = False) -> Self:
    from .uop import Ops
    return self._binop(Ops.MUL, x, reverse)

  def div(self, x: Any, reverse: bool = False) -> Self:
    from .uop import Ops
    a, b = self._broadcasted(x, reverse=reverse)
    if a.dtype.is_int:
      if a._uop.space is Space.TENSOR or a._uop is not a:
        a, b = a.cast(dtypes.fp32), b.cast(dtypes.fp32)
      else:
        raise TypeError("use // for integer division")
    return a._wrap_uop(a._uop.alu(Ops.DIV, b._uop))

  def pow(self, x: Any, reverse: bool = False) -> Self:
    if not reverse and isinstance(x, int) and x == 2: return self * self
    if not reverse and isinstance(x, float) and x == 0.5: return self.sqrt()
    if not reverse and isinstance(x, float) and x == -0.5: return self.rsqrt()
    if not reverse and isinstance(x, (int, float)) and x == -1: return self.recip()
    a, b = self._broadcasted(x, reverse=reverse)
    if not a.dtype.is_float: a, b = a.cast(dtypes.fp32), b.cast(dtypes.fp32)
    return (b * a.log2()).exp2()

  def maximum(self, x: Any) -> Self:
    from .uop import Ops
    return self._binop(Ops.MAX, x)

  def minimum(self, x: Any) -> Self:
    from .uop import Ops
    return self._binop(Ops.MIN, x)

  def clamp(self, min_: Any = None, max_: Any = None) -> Self:
    x = self
    if min_ is not None: x = x.maximum(min_)
    if max_ is not None: x = x.minimum(max_)
    return x
  clip = clamp

  def where(self, x: Any, y: Any) -> Self:
    from .uop import Ops, UOp, sbcast
    if self._uop.shape is None or (self._uop.space is not Space.TENSOR and self._uop is self):
      a = x._uop if isinstance(x, DTypeMixin) else None
      b = y._uop if isinstance(y, DTypeMixin) else None
      if a is not None and b is None: b = a._coerce(y)
      elif b is not None and a is None: a = b._coerce(x)
      if a is None or b is None: raise TypeError("at least one branch of where() must be a UOp")
      return self._wrap_uop(self._uop.alu(Ops.WHERE, a, b))
    if isinstance(x, DTypeMixin): a_m, b_m = self._wrap_uop(x._uop)._broadcasted(y)
    elif isinstance(y, DTypeMixin): a_m, b_m = self._wrap_uop(y._uop)._broadcasted(x, reverse=True)
    else: a_m, b_m = self._coerce_other(x)._broadcasted(y)
    cond = self.cast(dtypes.bool)
    nd = max(cond.ndim, a_m.ndim)
    cs = (1,) * (nd - cond.ndim) + cond.shape
    bs = (1,) * (nd - a_m.ndim) + a_m.shape
    out_sh = tuple(sbcast(u, v) for u, v in zip(cs, bs))
    cond = cond.reshape(cs).expand(out_sh)
    a_m = a_m.reshape(bs).expand(out_sh)
    b_m = b_m.reshape(bs).expand(out_sh)
    return self._wrap_uop(cond._uop.alu(Ops.WHERE, a_m._uop, b_m._uop))

  def masked_fill(self, mask: Self, value: Any) -> Self: return mask.where(value, self)

  def trunc(self) -> Self:
    return self if self.dtype.is_int else self.cast(dtypes.i32).cast(self.dtype)

  def floor(self) -> Self:
    if self.dtype.is_int: return self
    t = self.trunc()
    return (self < t).where(t - 1.0, t)

  def ceil(self) -> Self:
    if self.dtype.is_int: return self
    t = self.trunc()
    return (self > t).where(t + 1.0, t)

  def round(self) -> Self:
    if self.dtype.is_int: return self
    return (self + (self >= 0.0).where(0.5, -0.5)).trunc()

  def relu(self) -> Self: return self.maximum(0.0)
  def sigmoid(self) -> Self: return (1.0 + (-self).exp()).recip()
  def silu(self) -> Self: return self * self.sigmoid()
  swish = silu
  def tanh(self) -> Self:
    e = (self * 2.0).exp()
    return (e - 1.0) * (e + 1.0).recip()
  def gelu(self) -> Self:
    c = math.sqrt(2.0 / math.pi)
    return 0.5 * self * (1.0 + (c * (self + 0.044715 * self * self * self)).tanh())
  def softplus(self, beta: float = 1.0) -> Self:
    x = self if beta == 1.0 else self * beta
    out = x.maximum(0.0) + (1.0 + (-x.abs()).exp()).log()
    return out if beta == 1.0 else out * (1.0 / beta)

  def eq(self, x: Any) -> Self:
    from .uop import Ops
    return self._binop(Ops.CMPEQ, x)

  def ne(self, x: Any) -> Self:
    from .uop import Ops
    return self._binop(Ops.CMPNE, x)

  # ---- Python operators (NOTE: __eq__/__ne__ are NOT overridden here so UOp keeps hash-consing identity!) ----

  def __neg__(self) -> Self: return self.neg()
  def __pos__(self) -> Self: return self
  def __abs__(self) -> Self: return self.abs()
  def __invert__(self) -> Self: return self.bitwise_not()

  def __add__(self, x) -> Self: return self.add(x)
  def __radd__(self, x) -> Self: return self.add(x, True)
  def __sub__(self, x) -> Self: return self.sub(x)
  def __rsub__(self, x) -> Self: return self.sub(x, True)
  def __mul__(self, x) -> Self: return self.mul(x)
  def __rmul__(self, x) -> Self: return self.mul(x, True)
  def __truediv__(self, x) -> Self: return self.div(x)
  def __rtruediv__(self, x) -> Self: return self.div(x, True)
  def __floordiv__(self, x) -> Self:
    from .uop import Ops
    if self.dtype.is_int: return self._binop(Ops.DIV, x)
    if self._uop.space is not Space.TENSOR and self._uop is self: raise TypeError("use / for float division")
    return self.div(x).floor()
  def __rfloordiv__(self, x) -> Self:
    from .uop import Ops
    if self.dtype.is_int: return self._binop(Ops.DIV, x, True)
    if self._uop.space is not Space.TENSOR and self._uop is self: raise TypeError("use / for float division")
    return self.div(x, True).floor()
  def __mod__(self, x) -> Self:
    from .uop import Ops
    return self._binop(Ops.MOD, x)
  def __rmod__(self, x) -> Self:
    from .uop import Ops
    return self._binop(Ops.MOD, x, True)
  def __pow__(self, x) -> Self: return self.pow(x)
  def __rpow__(self, x) -> Self: return self.pow(x, True)

  def __and__(self, x) -> Self:
    from .uop import Ops
    return self._binop(Ops.AND, x)
  def __rand__(self, x) -> Self:
    from .uop import Ops
    return self._binop(Ops.AND, x, True)
  def __or__(self, x) -> Self:
    from .uop import Ops
    return self._binop(Ops.OR, x)
  def __ror__(self, x) -> Self:
    from .uop import Ops
    return self._binop(Ops.OR, x, True)
  def __xor__(self, x) -> Self:
    from .uop import Ops
    return self._binop(Ops.XOR, x)
  def __rxor__(self, x) -> Self:
    from .uop import Ops
    return self._binop(Ops.XOR, x, True)
  def __lshift__(self, x) -> Self:
    from .uop import Ops
    return self._binop(Ops.SHL, x)
  def __rshift__(self, x) -> Self:
    from .uop import Ops
    return self._binop(Ops.SHR, x)

  def __lt__(self, x) -> Self:
    from .uop import Ops
    return self._binop(Ops.CMPLT, x)
  def __gt__(self, x) -> Self:
    from .uop import Ops
    return self._binop(Ops.CMPLT, x, True)
  def __le__(self, x) -> Self:
    from .uop import Ops
    return ~self._binop(Ops.CMPLT, x, True)
  def __ge__(self, x) -> Self:
    from .uop import Ops
    return ~self._binop(Ops.CMPLT, x)

class ReduceMixin(ElementwiseMixin):
  __slots__ = ()
  def _reduce(self, op, axis: int | Sequence[int] | None = None, keepdim: bool = False) -> Self:
    axes = _canonicalize_axes(axis, self.ndim)
    out = self._wrap_uop(self._uop.reduce_axis(op, axes))
    if keepdim: return out
    return out.reshape(tuple(s for i, s in enumerate(out.shape) if i not in axes))

  def sum(self, axis: int | Sequence[int] | None = None, keepdim: bool = False, dtype: DType | str | None = None) -> Self:
    from .uop import Ops
    x = self.cast(dtypes.from_name(dtype)) if dtype is not None else (self.cast(dtypes.i32) if self.dtype is dtypes.bool else self)
    return x._reduce(Ops.ADD, axis, keepdim)

  def prod(self, axis: int | Sequence[int] | None = None, keepdim: bool = False, dtype: DType | str | None = None) -> Self:
    from .uop import Ops
    x = self.cast(dtypes.from_name(dtype)) if dtype is not None else self
    return x._reduce(Ops.MUL, axis, keepdim)

  def max(self, axis: int | Sequence[int] | None = None, keepdim: bool = False) -> Self:
    from .uop import Ops
    return self._reduce(Ops.MAX, axis, keepdim)

  def min(self, axis: int | Sequence[int] | None = None, keepdim: bool = False) -> Self:
    from .uop import Ops
    return self._reduce(Ops.MIN, axis, keepdim)

  def mean(self, axis: int | Sequence[int] | None = None, keepdim: bool = False, dtype: DType | str | None = None) -> Self:
    from .uop import sprod
    axes = _canonicalize_axes(axis, self.ndim)
    denom = sprod([self.shape[a] for a in axes])
    out_dt = dtypes.from_name(dtype) if dtype is not None else (self.dtype if self.dtype.is_float else dtypes.fp32)
    s = self.cast(out_dt).sum(axes, keepdim=keepdim)
    if isinstance(denom, int): return s * (1.0 / denom)
    return s * self._wrap_uop(denom).cast(out_dt).recip()

  def var(self, axis: int | Sequence[int] | None = None, keepdim: bool = False, correction: int = 1) -> Self:
    axes = _canonicalize_axes(axis, self.ndim)
    n = math.prod(self.shape[a] for a in axes)
    diff = self - self.mean(axes, keepdim=True)
    return diff.square().sum(axes, keepdim=keepdim) * (1.0 / max(1, n - correction))

  def std(self, axis: int | Sequence[int] | None = None, keepdim: bool = False, correction: int = 1) -> Self:
    return self.var(axis, keepdim=keepdim, correction=correction).sqrt()

  def any(self, axis: int | Sequence[int] | None = None, keepdim: bool = False) -> Self:
    return self.cast(dtypes.bool).cast(dtypes.i32).max(axis, keepdim=keepdim).cast(dtypes.bool)

  def all(self, axis: int | Sequence[int] | None = None, keepdim: bool = False) -> Self:
    return self.cast(dtypes.bool).cast(dtypes.i32).min(axis, keepdim=keepdim).cast(dtypes.bool)

  def argmax(self, axis: int | None = None, keepdim: bool = False) -> Self:
    from .uop import Ops, UOp
    # Layer 1 Dst tile argmax (no shape)
    if self._uop.shape is None:
      return self._wrap_uop(UOp(Ops.ARGMAX, dtypes.i32, (self._uop,), axis))
    if axis is None:
      return self._wrap_uop(UOp(Ops.ARGMAX, dtypes.i32, (self.flatten()._uop,), 0)).reshape(())
    ax = axis + self.ndim if axis < 0 else axis
    out = self._wrap_uop(UOp(Ops.ARGMAX, dtypes.i32, (self._uop,), ax))
    return out if keepdim else out.squeeze(ax)

  def argmin(self, axis: int | None = None, keepdim: bool = False) -> Self:
    return (-self).argmax(axis=axis, keepdim=keepdim)

  def topk(self, k: int, dim: int = -1, largest: bool = True, sorted_: bool = True) -> TopkResult:
    from .uop import Ops, TopkArg, UOp
    d = dim + self.ndim if dim < 0 else dim
    vals = self._wrap_uop(UOp(Ops.TOPK, self.dtype, (self._uop,), TopkArg(int(k), int(d), bool(largest), bool(sorted_), False)))
    idxs = self._wrap_uop(UOp(Ops.TOPK, dtypes.i32, (self._uop,), TopkArg(int(k), int(d), bool(largest), bool(sorted_), True)))
    return TopkResult(vals, idxs)

  def dot(self, w: Self, dtype: DType | str | None = None) -> Self:
    from .uop import sbcast
    x = self
    n1, n2 = x.ndim, w.ndim
    if n1 == 0 or n2 == 0: raise ValueError(f"both arguments to dot/matmul must be >= 1D, got {x.shape} and {w.shape}")
    if n1 == 1: x = x.reshape(1, x.shape[0])
    if n2 == 1: w = w.reshape(w.shape[0], 1)
    if x.shape[-1] != w.shape[-2]: raise ValueError(f"matmul inner dim mismatch: {self.shape} @ {w.shape}")
    xb, wb = x.shape[:-2], w.shape[:-2]
    nb = max(len(xb), len(wb))
    xb_pad = (1,) * (nb - len(xb)) + xb
    wb_pad = (1,) * (nb - len(wb)) + wb
    batch = tuple(sbcast(a, b) for a, b in zip(xb_pad, wb_pad))
    M, K, N = x.shape[-2], x.shape[-1], w.shape[-1]
    acc_dt = dtypes.from_name(dtype) if dtype is not None else least_upper_dtype(x.dtype, w.dtype)
    xa = x.reshape(*xb_pad, M, 1, K).expand(*batch, M, N, K).cast(acc_dt)
    wa = w.transpose(-1, -2).reshape(*wb_pad, 1, N, K).expand(*batch, M, N, K).cast(acc_dt)
    out = (xa * wa).sum(axis=-1)
    if n1 == 1 and n2 == 1: return out.reshape(())
    if n1 == 1: return out.reshape(*batch, N)
    if n2 == 1: return out.reshape(*batch, M)
    return out

  def matmul(self, x: Self, reverse: bool = False, dtype: DType | str | None = None) -> Self:
    return x.dot(self, dtype=dtype) if reverse else self.dot(x, dtype=dtype)

  def __matmul__(self, x: Self) -> Self: return self.matmul(x)
  def __rmatmul__(self, x: Self) -> Self: return self.matmul(x, True)

  def linear(self, weight: Self, bias: Self | None = None, dtype: DType | str | None = None) -> Self:
    out = self.dot(weight.T if weight.ndim == 2 else weight, dtype=dtype)
    return out if bias is None else out + bias

  def outer(self, other: Self) -> Self:
    return self.flatten().unsqueeze(1) * other.flatten().unsqueeze(0)

  @classmethod
  def _tri(cls, r: "sint", c: "sint", diagonal: "sint" = 0) -> Self:
    from .uop import UOp
    return cls._wrap_uop(UOp.arange(0, c, 1, dtypes.i32)).reshape(1, c) - \
           cls._wrap_uop(UOp.arange(0, r, 1, dtypes.i32)).reshape(r, 1) >= diagonal

  def triu(self, diagonal: "sint" = 0) -> Self:
    return type(self)._tri(self.shape[-2], self.shape[-1], diagonal).where(self, 0)

  def tril(self, diagonal: "sint" = 0) -> Self:
    return type(self)._tri(self.shape[-2], self.shape[-1], diagonal + 1).where(0, self)

  def _softmax(self, axis: int = -1, dtype: DType | str | None = None) -> tuple[Self, Self, Self]:
    x = self.cast(dtypes.from_name(dtype)) if dtype is not None else self
    m = x - x.max(axis=axis, keepdim=True)
    e = m.exp()
    return m, e, e.sum(axis=axis, keepdim=True)

  def softmax(self, axis: int = -1, dtype: DType | str | None = None) -> Self:
    _, e, ss = self._softmax(axis, dtype)
    return e * ss.recip()

  def log_softmax(self, axis: int = -1, dtype: DType | str | None = None) -> Self:
    m, _, ss = self._softmax(axis, dtype)
    return m - ss.log()

  def logsumexp(self, axis: int | Sequence[int] | None = None, keepdim: bool = False) -> Self:
    m = self.max(axis=axis, keepdim=True)
    out = (self - m).exp().sum(axis=axis, keepdim=keepdim).log()
    return out + (m if keepdim else m.reshape(out.shape))

  def rms_norm(self, weight: Self | None = None, eps: float = 1e-6) -> Self:
    y = self * (self.square().mean(axis=-1, keepdim=True) + eps).rsqrt()
    return y if weight is None else y * weight

  def layernorm(self, axis: int | Sequence[int] = -1, eps: float = 1e-5) -> Self:
    y = self - self.mean(axis=axis, keepdim=True)
    return y * (y.square().mean(axis=axis, keepdim=True) + eps).rsqrt()

  def scaled_dot_product_attention(
    self,
    key: Self,
    value: Self,
    attn_mask: Self | None = None,
    is_causal: bool = False,
    scale: float | None = None,
    enable_gqa: bool = False,
  ) -> Self:
    q, k, v = self, key, value
    if enable_gqa and q.shape[-3] != k.shape[-3]:
      rep = q.shape[-3] // k.shape[-3]
      k = k.repeat_interleave(rep, dim=-3)
      v = v.repeat_interleave(rep, dim=-3)
    sc = (1.0 / math.sqrt(q.shape[-1])) if scale is None else scale
    scores = q.matmul(k.mT) * sc
    if is_causal:
      L, S = q.shape[-2], k.shape[-2]
      causal = type(self)._tri(L, S, diagonal=S - L + 1)
      scores = causal.where(-math.inf, scores)
    if attn_mask is not None:
      scores = scores + (attn_mask.where(0.0, -math.inf) if attn_mask.dtype is dtypes.bool else attn_mask)
    return scores.softmax(axis=-1).matmul(v)

Mixin = ReduceMixin
