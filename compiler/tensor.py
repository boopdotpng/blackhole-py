import itertools, json, math, pathlib, weakref
from collections import OrderedDict
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any
import numpy as np
from .dtype import DType, Space, dtypes, least_upper_dtype
from .mixin import Mixin, TopkResult, _argfix
from .ops import VerifyError, pm_simplify
from .uop import (
  GroupOp, Ops, PatternMatcher, UOp, UPat, Variable,
  graph_rewrite, pretty, simp_sint, sint, smax, smin, sprod, substitute_all,
)

@dataclass(frozen=True)
class _DiskSlice:
  path: pathlib.Path
  offset: int
  nbytes: int
  raw_dtype: str
  shape: tuple[int, ...]
  packed_format: str | None = None

@dataclass(frozen=True)
class _FillSpec:
  value: bool | int | float
  shape: tuple[int, ...]
  dtype: DType

# Concrete host arrays, lazy disk slices, and lazy zero/const fills attached to BUFFER UOps (auto-GC'd).
_TENSOR_DATA: weakref.WeakKeyDictionary[UOp, np.ndarray] = weakref.WeakKeyDictionary()
_TENSOR_DISK: weakref.WeakKeyDictionary[UOp, _DiskSlice] = weakref.WeakKeyDictionary()
_TENSOR_FILL: weakref.WeakKeyDictionary[UOp, _FillSpec] = weakref.WeakKeyDictionary()
_ALL_TENSORS: weakref.WeakSet["Tensor"] = weakref.WeakSet()
_BUF_ID = itertools.count()

_SAFE_DTYPES: dict[str, DType] = {
  "BOOL": dtypes.bool, "U8": dtypes.u8, "I8": dtypes.u8,
  "I32": dtypes.i32, "I64": dtypes.i32, "U32": dtypes.u32, "U64": dtypes.u64,
  "BF16": dtypes.bf16, "F16": dtypes.fp32, "F32": dtypes.fp32, "F64": dtypes.fp32,
  "F8_E4M3": dtypes.e4m3,
}
_SAFE_NP: dict[str, str] = {
  "BOOL": "?", "U8": "u1", "I8": "i1", "I16": "<i2", "U16": "<u2",
  "I32": "<i4", "U32": "<u4", "I64": "<i8", "U64": "<u8",
  "F16": "<f2", "F32": "<f4", "F64": "<f8", "BF16": "<u2", "F8_E4M3": "u1",
}

def _decode_f8_e4m3(u: np.ndarray) -> np.ndarray:
  u = u.astype(np.uint32)
  sgn = (u >> 7) & 1
  exp = (u >> 3) & 0xF
  man = u & 0x7
  normal = (sgn << 31) | ((exp + 120) << 23) | (man << 20)
  out = normal.view(np.float32)
  sub = np.where(sgn != 0, -1.0, 1.0).astype(np.float32) * (man.astype(np.float32) * np.float32(2.0 ** -9))
  out = np.where(exp == 0, sub, out)
  return np.where((exp == 15) & (man == 7), np.float32(np.nan), out)

def _read_disk_slice(ds: _DiskSlice, dt: DType) -> np.ndarray:
  if ds.packed_format is not None:
    return np.array(np.memmap(ds.path, dtype="u1", mode="r", offset=ds.offset, shape=ds.shape), copy=True)
  np_dt = _SAFE_NP.get(ds.raw_dtype)
  if np_dt is None: raise ValueError(f"unsupported safetensors dtype {ds.raw_dtype!r}")
  mm = np.memmap(ds.path, dtype=np_dt, mode="r", offset=ds.offset, shape=ds.shape)
  if ds.raw_dtype == "BF16":
    return ((mm.astype(np.uint32) << np.uint32(16)).view(np.float32))
  if ds.raw_dtype == "F8_E4M3":
    return _cast_np(_decode_f8_e4m3(np.asarray(mm)), dt)
  return _cast_np(np.asarray(mm), dt).copy()

def _round_bf16(arr: np.ndarray) -> np.ndarray:
  f32 = np.asarray(arr, dtype=np.float32)
  u = f32.view(np.uint32).astype(np.uint64)
  r = ((u + 0x7FFF + ((u >> 16) & 1)) & ~np.uint64(0xFFFF)).astype(np.uint32)
  return r.view(np.float32)

def _np_dtype(dt: DType) -> np.dtype:
  if dt is dtypes.bool: return np.dtype(np.bool_)
  if dt is dtypes.u8:   return np.dtype(np.uint8)
  if dt is dtypes.i32:  return np.dtype(np.int32)
  if dt is dtypes.u32:  return np.dtype(np.uint32)
  if dt is dtypes.u64:  return np.dtype(np.uint64)
  return np.dtype(np.float32)

def _cast_np(arr: np.ndarray, dt: DType) -> np.ndarray:
  if dt is dtypes.bf16: return _round_bf16(arr)
  if dt is dtypes.bool: return np.asarray(arr, dtype=np.bool_)
  return np.asarray(arr, dtype=_np_dtype(dt))

def _dtype_from_np(arr: np.ndarray) -> DType:
  k, b = arr.dtype.kind, arr.dtype.itemsize
  if k == "b": return dtypes.bool
  if k == "f": return dtypes.fp32
  if k == "u": return {1: dtypes.u8, 4: dtypes.u32, 8: dtypes.u64}.get(b, dtypes.u32)
  if k == "i": return dtypes.i32
  raise TypeError(f"unsupported numpy dtype {arr.dtype}")

# ---- Layer 0 Tensor (inherits shared tinygrad-style Mixin with UOp) ----

class Tensor(Mixin):
  __slots__ = ("uop", "__weakref__")

  @property
  def _uop(self) -> UOp: return self.uop

  @classmethod
  def _wrap_uop(cls, u: UOp) -> "Tensor": return cls.from_uop(u)

  def __init__(
    self,
    data: Any,
    dtype: DType | str | None = None,
    *,
    name: str | None = None,
    space: Space = Space.TENSOR,
    device: str | None = None,
  ):
    del device
    dt = dtypes.from_name(dtype) if dtype is not None else None
    if isinstance(data, Tensor):
      u = data.uop
      self.uop = u if (dt is None or u.dtype == dt) else u.cast(dt)
    elif isinstance(data, UOp):
      self.uop = data if (dt is None or data.dtype == dt) else data.cast(dt)
    elif isinstance(data, pathlib.Path):
      self.uop = Tensor.from_disk(data, dtype=dtypes.u8 if dt is None else dt, name=name).uop
    elif isinstance(data, (bytes, bytearray, memoryview)):
      arr = np.frombuffer(data, dtype=np.uint8).copy()
      target_dt = dtypes.u8 if dt is None else dt
      buf_name = f"t{next(_BUF_ID)}" if name is None else name
      u = UOp.buffer(buf_name, (int(arr.size),), target_dt, space=space)
      _TENSOR_DATA[u] = _cast_np(arr, target_dt).copy()
      self.uop = u
    elif isinstance(data, bool):
      self.uop = UOp.const(dtypes.bool if dt is None else dt, data)
    elif isinstance(data, int):
      self.uop = UOp.const(dtypes.i32 if dt is None else dt, data)
    elif isinstance(data, float):
      self.uop = UOp.const(dtypes.fp32 if dt is None else dt, data)
    else:
      arr = np.asarray(data)
      target_dt = _dtype_from_np(arr) if dt is None else dt
      if arr.ndim == 0 and name is None and space is Space.TENSOR:
        val = arr.item()
        self.uop = UOp.const(target_dt, bool(val) if target_dt is dtypes.bool else (int(val) if target_dt.is_int else float(val)))
      else:
        buf_name = f"t{next(_BUF_ID)}" if name is None else name
        u = UOp.buffer(buf_name, tuple(int(s) for s in arr.shape), target_dt, space=space)
        _TENSOR_DATA[u] = _cast_np(arr, target_dt).copy()
        self.uop = u
    _ALL_TENSORS.add(self)

  @staticmethod
  def from_uop(u: UOp) -> "Tensor":
    t = Tensor.__new__(Tensor)
    t.uop = u
    _ALL_TENSORS.add(t)
    return t

  @staticmethod
  def from_disk(
    path: str | pathlib.Path,
    *,
    shape: tuple[int, ...] | None = None,
    dtype: DType | str = dtypes.u8,
    offset: int = 0,
    nbytes: int | None = None,
    raw_dtype: str | None = None,
    name: str | None = None,
    space: Space = Space.DRAM,
    packed_format: str | None = None,
  ) -> "Tensor":
    p = pathlib.Path(path)
    dt = dtypes.from_name(dtype)
    size = p.stat().st_size - offset if nbytes is None else nbytes
    sh = (size // max(1, dt.bits // 8),) if shape is None else tuple(int(s) for s in shape)
    raw = raw_dtype or {
      dtypes.u8: "U8", dtypes.bool: "BOOL", dtypes.i32: "I32", dtypes.u32: "U32",
      dtypes.u64: "U64", dtypes.bf16: "BF16", dtypes.fp32: "F32", dtypes.e4m3: "F8_E4M3",
    }.get(dt, "U8")
    buf_name = f"disk_{p.name}_{next(_BUF_ID)}" if name is None else name
    u = UOp.buffer(buf_name, sh, dt, space=space)
    _TENSOR_DISK[u] = _DiskSlice(p, int(offset), int(size), raw, sh, packed_format)
    return Tensor.from_uop(u)

  # ---- metadata & python protocol ----

  @property
  def device(self) -> str: return "BLACKHOLE"
  def variables(self) -> list[UOp]: return self.uop.variables()
  def unbind_all(self) -> tuple["Tensor", dict[UOp, int]]:
    u, vals = self.uop.unbind_all()
    return Tensor.from_uop(u), vals

  def __len__(self) -> int:
    if self.ndim == 0: raise TypeError("len() of a 0-d tensor")
    if not isinstance(self.shape[0], int): raise TypeError(f"len() of symbolic dim {self.shape[0]}")
    return self.shape[0]

  def __hash__(self) -> int: return id(self)
  def __bool__(self) -> bool: raise TypeError("__bool__ on Tensor is not defined")
  def __repr__(self) -> str: return f"<Tensor {self.shape} {self.dtype.name} {self.uop.op.name}>"
  def pretty(self, limit: int = 200) -> str: return pretty(self.uop, limit=limit)

  def _coerce_other(self, y: Any) -> "Tensor":
    try: return super()._coerce_other(y)
    except TypeError: return Tensor(y)

  def __eq__(self, x) -> "Tensor": return self.eq(x)  # type: ignore[override]
  def __ne__(self, x) -> "Tensor": return self.ne(x)  # type: ignore[override]

  # ---- realization / host evaluation ----

  def numpy(self, buffers: dict[str, np.ndarray] | None = None,
            var_vals: dict[UOp | str, int] | None = None) -> np.ndarray:
    return eval_tensor(self.uop, buffers, var_vals=var_vals)

  def data(self, buffers: dict[str, np.ndarray] | None = None,
           var_vals: dict[UOp | str, int] | None = None) -> memoryview:
    u = self.uop
    if u.op is Ops.SHRINK and u.src[0].op is Ops.BUFFER and u.src[0] in _TENSOR_DISK and u.dtype is dtypes.u8:
      ds = _TENSOR_DISK[u.src[0]]
      if len(u.arg) == 1 and isinstance(u.arg[0][0], int) and isinstance(u.arg[0][1], int):
        b, e = u.arg[0]
        with open(ds.path, "rb") as f:
          f.seek(ds.offset + b)
          return memoryview(f.read(e - b))
    if u.op is Ops.BUFFER and u in _TENSOR_DISK and u.dtype is dtypes.u8:
      ds = _TENSOR_DISK[u]
      with open(ds.path, "rb") as f:
        f.seek(ds.offset)
        return memoryview(f.read(ds.nbytes))
    return memoryview(np.ascontiguousarray(self.numpy(buffers, var_vals=var_vals)).tobytes())

  def realize(self, buffers: dict[str, np.ndarray] | None = None, *, name: str | None = None,
              var_vals: dict[UOp | str, int] | None = None) -> "Tensor":
    u = self.uop
    if buffers is None and var_vals is None:
      if u.op is Ops.BUFFER: return self
      if (cv := _const_val(u)) is not None and all(isinstance(s, int) for s in self.shape):
        buf_name = f"buf_{next(_BUF_ID)}" if name is None else name
        buf = UOp.buffer(buf_name, self.shape, self.dtype, space=Space.DRAM)
        _TENSOR_FILL[buf] = _FillSpec(cv, self.shape, self.dtype)
        return Tensor.from_uop(buf)
    return Tensor(self.numpy(buffers, var_vals=var_vals), dtype=self.dtype, name=name, space=Space.DRAM)

  def item(self, buffers: dict[str, np.ndarray] | None = None,
           var_vals: dict[UOp | str, int] | None = None) -> Any:
    if self.numel() != 1: raise ValueError(f"item() requires 1 element, got shape {self.shape}")
    return self.numpy(buffers, var_vals=var_vals).item()

  def tolist(self, buffers: dict[str, np.ndarray] | None = None,
             var_vals: dict[UOp | str, int] | None = None) -> Any:
    return self.numpy(buffers, var_vals=var_vals).tolist()

  # ---- creation helpers ----

  @staticmethod
  def buffer(
    name: str,
    shape: tuple[int, ...] | int,
    dtype: DType | str = dtypes.fp32,
    *,
    space: Space = Space.DRAM,
    addr: int | None = None,
    tiles_per_page: int = 1,
  ) -> "Tensor":
    return Tensor.from_uop(UOp.buffer(name, shape, dtype, space=space, addr=addr, tiles_per_page=tiles_per_page))

  @staticmethod
  def empty(*shape, dtype: DType | str = dtypes.fp32, name: str | None = None, space: Space = Space.DRAM,
            device: str | None = None) -> "Tensor":
    del device
    sh = _argfix(*shape)
    return Tensor.buffer(f"t{next(_BUF_ID)}" if name is None else name, sh, dtype=dtype, space=space)

  def empty_like(self, dtype: DType | str | None = None, **kwargs) -> "Tensor":
    return Tensor.empty(*self.shape, dtype=self.dtype if dtype is None else dtype, **kwargs)

  @staticmethod
  def full(shape: tuple[sint, ...] | sint, fill_value: bool | int | float, dtype: DType | str | None = None,
           *, device: str | None = None, buffer: bool = False) -> "Tensor":
    del device, buffer
    sh = (shape,) if not isinstance(shape, tuple) else shape
    if dtype is None:
      dt = dtypes.bool if isinstance(fill_value, bool) else (dtypes.i32 if isinstance(fill_value, int) else dtypes.fp32)
    else:
      dt = dtypes.from_name(dtype)
    c = UOp.const(dt, fill_value)
    return Tensor.from_uop(c if not sh else c.reshape((1,) * len(sh)).expand(sh))

  @staticmethod
  def zeros(*shape, dtype: DType | str = dtypes.fp32, device: str | None = None) -> "Tensor":
    return Tensor.full(_argfix(*shape), 0, dtype=dtype, device=device)

  @staticmethod
  def ones(*shape, dtype: DType | str = dtypes.fp32, device: str | None = None) -> "Tensor":
    return Tensor.full(_argfix(*shape), 1, dtype=dtype, device=device)

  def full_like(self, fill_value: bool | int | float, dtype: DType | str | None = None) -> "Tensor":
    return Tensor.full(self.shape, fill_value, dtype=self.dtype if dtype is None else dtype)

  def zeros_like(self, dtype: DType | str | None = None) -> "Tensor": return self.full_like(0, dtype=dtype)
  def ones_like(self, dtype: DType | str | None = None) -> "Tensor": return self.full_like(1, dtype=dtype)

  @staticmethod
  def arange(start: int | float, stop: int | float | None = None, step: int | float = 1,
             dtype: DType | str | None = None) -> "Tensor":
    if stop is None: start, stop = 0, start
    if dtype is None:
      dt = dtypes.fp32 if any(isinstance(v, float) for v in (start, stop, step)) else dtypes.i32
    else:
      dt = dtypes.from_name(dtype)
    return Tensor.from_uop(UOp.arange(start, stop, step, dtype=dt))

  @staticmethod
  def linspace(start: int | float, stop: int | float, steps: int, dtype: DType | str = dtypes.fp32) -> "Tensor":
    dt = dtypes.from_name(dtype)
    if steps == 0: return Tensor.arange(0, 0, 1, dtype=dt)
    if steps == 1: return Tensor.full((1,), float(start), dtype=dt)
    return (Tensor.full((1,), float(start), dtype=dt) +
            Tensor.arange(0, steps, 1, dtype=dt) * ((float(stop) - float(start)) / (steps - 1))).cast(dt)

  @staticmethod
  def eye(n: int, m: int | None = None, dtype: DType | str = dtypes.fp32) -> "Tensor":
    m = n if m is None else m
    return (Tensor.arange(n).reshape(n, 1) == Tensor.arange(m).reshape(1, m)).cast(dtypes.from_name(dtype))

  @staticmethod
  def einsum(formula: str, *operands: "Tensor | Sequence[Tensor]", dtype: DType | str | None = None) -> "Tensor":
    ops: list[Tensor] = list(operands[0]) if len(operands) == 1 and isinstance(operands[0], (list, tuple)) else list(operands)  # type: ignore[arg-type]
    lhs, rhs = (p.strip() for p in formula.replace(" ", "").split("->"))
    in_subs = lhs.split(",")
    if len(in_subs) != len(ops): raise ValueError(f"einsum expected {len(in_subs)} operands, got {len(ops)}")
    sizes: dict[str, int] = {}
    for sub, t in zip(in_subs, ops):
      if len(sub) != t.ndim: raise ValueError(f"einsum subscript {sub!r} does not match shape {t.shape}")
      for ch, sz in zip(sub, t.shape):
        if ch in sizes and sizes[ch] != sz: raise ValueError(f"einsum dim mismatch for {ch!r}: {sizes[ch]} vs {sz}")
        sizes[ch] = sz
    all_letters = list(rhs) + [ch for ch in sizes if ch not in rhs]
    target_shape = tuple(sizes[ch] for ch in all_letters)
    acc_dt = dtypes.from_name(dtype) if dtype is not None else least_upper_dtype(*(t.dtype for t in ops))
    aligned: list[Tensor] = []
    for sub, t in zip(in_subs, ops):
      present = [ch for ch in all_letters if ch in sub]
      t = t.permute([sub.index(ch) for ch in present])
      sh = tuple(sizes[ch] if ch in present else 1 for ch in all_letters)
      aligned.append(t.reshape(sh).expand(target_shape).cast(acc_dt))
    prod = aligned[0]
    for a in aligned[1:]: prod = prod * a
    red_axes = tuple(range(len(rhs), len(all_letters)))
    return prod.sum(axis=red_axes) if red_axes else prod

  # ---- tinygrad-style assign (builds STORE + AFTER automatically and updates live views) ----

  def assign(self, x: "Tensor | bool | int | float") -> "Tensor":
    val = (x if isinstance(x, Tensor) else Tensor.full(self.shape, x, dtype=self.dtype)).expand(self.shape).cast(self.dtype)
    if self.uop is val.uop: return self
    views = [self.uop]
    while views[-1].op in GroupOp.Movement or views[-1].op is Ops.BITCAST:
      views.append(views[-1].src[0])
    assigned_to = views[-1].storage_base
    live = list(_ALL_TENSORS)
    held = {t.uop for t in live}
    # Assigning to a non-buffer pending tensor that views no other live tensor just rebinds it (no partial view write).
    if not assigned_to.has_buffer_identity() and not any(u in held for u in views[1:]):
      self.uop = val.uop
      return self
    ib = next((u for u in reversed(views) if u.has_buffer_identity(after_ok=True) and (u is self.uop or u in held)),
              next((u for u in views[1:] if u in held), views[-1]))
    if ib is self.uop:
      after = ib.after(ib.store(val.uop))
    else:
      after = ib.after(self.uop.store(val.uop))
    for t in live:
      if t.uop is ib or t.uop.storage_base is assigned_to:
        t.uop = substitute_all(t.uop, {ib: after})
    return self

  # ---- indexing & slicing ----

  def take(self, index: Any, dim: int = 0) -> "Tensor":
    idx = index if isinstance(index, Tensor) else Tensor(index, dtype=dtypes.i32)
    return super().take(idx, dim=dim)

  def gather(self, dim: int, index: Any) -> "Tensor":
    idx = index if isinstance(index, Tensor) else Tensor(index, dtype=dtypes.i32)
    return super().gather(dim, idx)

  def scatter_update(self, dim: int, index: Any, value: Any) -> "Tensor":
    idx = index if isinstance(index, Tensor) else Tensor(index, dtype=dtypes.i32)
    val = value if isinstance(value, Tensor) else Tensor(value, dtype=self.dtype)
    return super().scatter_update(dim, idx, val)

  @staticmethod
  def _resolve_slice(slc: slice, n: sint) -> tuple[sint, sint, int]:
    if (isinstance(n, int)
        and (slc.start is None or isinstance(slc.start, int))
        and (slc.stop is None or isinstance(slc.stop, int))
        and (slc.step is None or isinstance(slc.step, int))):
      return slc.indices(n)
    step = 1 if slc.step is None else int(slc.step)
    if step != 1: raise NotImplementedError(f"symbolic slice requires step=1, got {slc}")
    start: sint = 0 if slc.start is None else (
      simp_sint(n + slc.start) if isinstance(slc.start, int) and slc.start < 0 else simp_sint(slc.start))
    stop: sint = n if slc.stop is None else (
      simp_sint(n + slc.stop) if isinstance(slc.stop, int) and slc.stop < 0 else simp_sint(slc.stop))
    return start, stop, 1

  def _slice_step(self, dim: int, start: sint, stop: sint, step: int) -> "Tensor":
    n = self.shape[dim]
    if isinstance(start, UOp) or isinstance(stop, UOp) or isinstance(n, UOp):
      if step != 1: raise NotImplementedError("symbolic slice requires step=1")
      return self.shrink(tuple((start, stop) if i == dim else None for i in range(self.ndim)))
    if step < 0:
      start_f = n - 1 - start
      stop_f = n - 1 - stop
      return self.flip(dim)._slice_step(dim, start_f, stop_f, -step)
    start = max(0, min(n, start))
    stop = max(start, min(n, stop))
    sub = self.shrink(tuple((start, stop) if i == dim else None for i in range(self.ndim)))
    if step == 1: return sub
    length = sub.shape[dim]
    if length == 0: return sub
    pad_amt = (-length) % step
    if pad_amt:
      sub = sub.pad(tuple((0, pad_amt) if i == dim else (0, 0) for i in range(sub.ndim)))
    n_blocks = (length + pad_amt) // step
    sh = sub.shape
    sub = sub.reshape(*sh[:dim], n_blocks, step, *sh[dim + 1:])
    sub = sub.shrink(tuple((0, 1) if i == dim + 1 else None for i in range(sub.ndim)))
    return sub.reshape(*sh[:dim], n_blocks, *sh[dim + 1:])

  def _normalize_indices(self, indices: Any) -> list[Any]:
    idx = list(indices) if isinstance(indices, tuple) else [indices]
    ell = [k for k, i in enumerate(idx) if i is Ellipsis]
    if len(ell) > 1: raise IndexError("an index can only have a single ellipsis")
    if ell:
      pos = ell[0]
      n_real = sum(1 for i in idx if i is not None and i is not Ellipsis)
      idx = idx[:pos] + [slice(None)] * (self.ndim - n_real) + idx[pos + 1:]
    n_real = sum(1 for i in idx if i is not None)
    if n_real > self.ndim: raise IndexError(f"too many indices ({n_real}) for tensor of ndim {self.ndim}")
    idx.extend([slice(None)] * (self.ndim - n_real))
    return idx

  def __getitem__(self, indices: Any) -> "Tensor":
    idx = self._normalize_indices(indices)
    x = self
    cur_dim = 0
    tensor_axes: list[tuple[int, Tensor]] = []
    for item in idx:
      if item is None:
        x = x.unsqueeze(cur_dim)
        cur_dim += 1
      elif isinstance(item, int):
        n = x.shape[cur_dim]
        i: sint = simp_sint(n + item) if item < 0 else item
        if isinstance(n, int) and isinstance(i, int) and not (0 <= i < n):
          raise IndexError(f"index {item} out of bounds for dim {cur_dim} of size {n}")
        x = x.shrink(tuple((i, simp_sint(i + 1)) if d == cur_dim else None for d in range(x.ndim))).squeeze(cur_dim)
      elif isinstance(item, slice):
        start, stop, step = Tensor._resolve_slice(item, x.shape[cur_dim])
        x = x._slice_step(cur_dim, start, stop, step)
        cur_dim += 1
      elif isinstance(item, (Tensor, list, np.ndarray)):
        t = item if isinstance(item, Tensor) else Tensor(item, dtype=dtypes.i32)
        tensor_axes.append((cur_dim, t))
        cur_dim += 1
      else:
        raise TypeError(f"unsupported index type {type(item).__name__}")

    if not tensor_axes: return x
    if len(tensor_axes) == 1:
      d, t = tensor_axes[0]
      return x.take(t, dim=d)

    dims = [d for d, _ in tensor_axes]
    ts = [t for _, t in tensor_axes]
    bshape: tuple[int, ...] = ()
    for t in ts:
      nd = max(len(bshape), t.ndim)
      a = (1,) * (nd - len(bshape)) + bshape
      b = (1,) * (nd - t.ndim) + t.shape
      bshape = tuple(max(u, v) for u, v in zip(a, b))
    ts = [t.expand(bshape).cast(dtypes.i32) for t in ts]

    contiguous_dims = dims == list(range(dims[0], dims[0] + len(dims)))
    other_dims = [d for d in range(x.ndim) if d not in dims]
    if contiguous_dims:
      flat_dim = dims[0]
    else:
      flat_dim = 0
      x = x.permute(dims + other_dims)
    sizes = [x.shape[flat_dim + i] for i in range(len(dims))]
    flat_idx = ts[0]
    for sz, t in zip(sizes[1:], ts[1:]):
      flat_idx = flat_idx * sz + t
    x = x.reshape(*x.shape[:flat_dim], math.prod(sizes), *x.shape[flat_dim + len(dims):])
    return x.take(flat_idx, dim=flat_dim)

  def __setitem__(self, indices: Any, v: Any) -> None:
    idx = self._normalize_indices(indices)
    non_full = [(d, item) for d, item in enumerate(idx) if not (isinstance(item, slice) and item == slice(None))]
    if len(non_full) == 1:
      d, item = non_full[0]
      if isinstance(item, int):
        i = item + self.shape[d] if item < 0 else item
        val = (v if isinstance(v, Tensor) else Tensor.full(self.shape[:d] + self.shape[d + 1:], v, dtype=self.dtype)).cast(self.dtype)
        self.assign(self.scatter_update(d, Tensor(i, dtype=dtypes.i32), val))
        return
      if isinstance(item, Tensor):
        target_sh = self.shape[:d] + item.shape + self.shape[d + 1:]
        val = (v if isinstance(v, Tensor) else Tensor.full(target_sh, v, dtype=self.dtype)).expand(target_sh).cast(self.dtype)
        self.assign(self.scatter_update(d, item, val))
        return
      if isinstance(item, slice):
        start, stop, step = item.indices(self.shape[d])
        idx_t = Tensor.arange(start, stop, step, dtype=dtypes.i32)
        target_sh = self.shape[:d] + idx_t.shape + self.shape[d + 1:]
        val = (v if isinstance(v, Tensor) else Tensor.full(target_sh, v, dtype=self.dtype)).expand(target_sh).cast(self.dtype)
        self.assign(self.scatter_update(d, idx_t, val))
        return
    # Contiguous slice/int indexing: delegate directly to view.assign(v) (STORE + AFTER)
    self[indices].assign(v)

# ---- Safetensors & State Dict Loading ----

def safe_load(path: str | pathlib.Path) -> dict[str, Tensor]:
  """Lazily load a .safetensors file, sharded .index.json, or directory into disk-backed Tensors."""
  p = pathlib.Path(path)
  if p.is_dir():
    idx = p / "model.safetensors.index.json"
    if idx.exists(): p = idx
    elif (single := p / "model.safetensors").exists(): p = single
    else: raise FileNotFoundError(f"no safetensors or index.json in {p}")
  if p.suffix == ".json":
    data = json.loads(p.read_text())
    out: dict[str, Tensor] = {}
    for shard in sorted(set(data["weight_map"].values())):
      out.update(safe_load(p.parent / shard))
    return out
  with open(p, "rb") as f:
    header_len = int.from_bytes(f.read(8), "little")
    header = json.loads(f.read(header_len).decode("utf-8"))
  base_off = 8 + header_len
  metadata = header.get("__metadata__", {})
  packed = json.loads(metadata["blackhole.packed_tensors"]) if "blackhole.packed_tensors" in metadata else {}
  if packed and (metadata.get("blackhole.layout") != "kn_tiles_32x32_v1" or not packed.keys() <= header.keys()):
    raise ValueError(f"unsupported packed safetensors metadata in {p}")
  tensors: dict[str, Tensor] = {}
  for name, info in header.items():
    if name == "__metadata__": continue
    start, end = info["data_offsets"]
    raw_dt = info["dtype"]
    shape = tuple(int(s) for s in info["shape"])
    if name in packed:
      dt = dtypes.from_name(packed[name]["format"])
      tensors[name] = Tensor.from_disk(
        p, shape=shape, dtype=dt, offset=base_off + start, nbytes=end - start,
        raw_dtype=raw_dt, name=name, packed_format=packed[name]["format"],
      )
    else:
      dt = _SAFE_DTYPES.get(raw_dt)
      if dt is None: raise ValueError(f"unsupported safetensors dtype {raw_dt!r} for {name!r}")
      tensors[name] = Tensor.from_disk(
        p, shape=shape, dtype=dt, offset=base_off + start, nbytes=end - start, raw_dtype=raw_dt, name=name,
      )
  return tensors

def get_state_dict(obj: Any, prefix: str = "") -> dict[str, Tensor]:
  state: dict[str, Tensor] = OrderedDict()
  if isinstance(obj, Tensor):
    state[prefix.rstrip(".")] = obj
  elif hasattr(obj, "__dict__"):
    for k, v in obj.__dict__.items():
      if k.startswith("_") or v is None: continue
      state.update(get_state_dict(v, f"{prefix}{k}."))
  elif isinstance(obj, (list, tuple)):
    for i, v in enumerate(obj): state.update(get_state_dict(v, f"{prefix}{i}."))
  elif isinstance(obj, dict):
    for k, v in obj.items(): state.update(get_state_dict(v, f"{prefix}{k}."))
  return state

def load_state_dict(model: Any, state_dict: dict[str, Tensor], strict: bool = True) -> list[str]:
  model_sd = get_state_dict(model)
  missing = [k for k in model_sd if k not in state_dict]
  unexpected = [k for k in state_dict if k not in model_sd]
  if strict and (missing or unexpected):
    raise KeyError(f"state_dict mismatch: missing={missing[:5]}, unexpected={unexpected[:5]}")
  loaded: list[str] = []
  for k, dst in model_sd.items():
    if k not in state_dict: continue
    src = state_dict[k]
    if dst.shape != src.shape:
      raise ValueError(f"shape mismatch for {k!r}: model expects {dst.shape}, checkpoint has {src.shape}")
    dst.uop = src.uop
    loaded.append(k)
  return loaded

# ---- Layer 0 Verifier & Frontend PatternMatchers (tinygrad-style mop_cleanup + symbolic) ----

_LAYER1_ONLY_OPS = frozenset({
  Ops.SPECIAL, Ops.RANGE, Ops.END, Ops.BACKEDGE, Ops.IF, Ops.REDUCE, Ops.CARRY, Ops.LOOP, Ops.GET,
  Ops.LOAD, Ops.NOC_READ, Ops.NOC_WRITE, Ops.NOC_MCAST, Ops.BARRIER,
  Ops.UNPACK, Ops.MVMUL, Ops.PACK, Ops.REPLAY, Ops.MOP, Ops.LANE_ID, Ops.REDUCE_ROW, Ops.REDUCE_LANES, Ops.SFPU,
})

def verify_tensor(root: Tensor | UOp) -> None:
  u_root = root.uop if isinstance(root, Tensor) else root
  for u in u_root.toposort():
    if u.op in _LAYER1_ONLY_OPS:
      raise VerifyError(f"Layer 1 hardware op {u.op.name} is not valid in a Layer 0 tensor graph")
    if u.op is Ops.STORE:
      if len(u.src) != 2 or u.src[0].shape is None or u.src[0].shape != u.src[1].shape:
        raise VerifyError(f"Layer 0 STORE requires (view, val) with matching shapes, got {[s.shape for s in u.src]}")
      continue
    if u.op is not Ops.SINK and u.shape is None:
      raise VerifyError(f"Layer 0 UOp {u.op.name} ({u.space}) has no tensor shape")
    if u.op is Ops.ARGMAX and not isinstance(u.arg, int):
      raise VerifyError(f"Layer 0 ARGMAX requires int axis arg, got {u.arg!r}")

def _const_val(u: UOp) -> Any | None:
  cur = u
  while cur.op in (Ops.EXPAND, Ops.RESHAPE, Ops.PERMUTE, Ops.SHRINK, Ops.FLIP):
    cur = cur.src[0]
  return cur.arg if cur.op is Ops.CONST else None

def _const_shaped(dt: DType, val: Any, shape: tuple[sint, ...]) -> UOp:
  c = UOp.const(dt, val)
  return c if not shape else c.reshape((1,) * len(shape)).expand(shape)

def _is_canonical_const(u: UOp) -> bool:
  if u.op is Ops.CONST: return True
  if u.op is Ops.EXPAND and u.src[0].op is Ops.RESHAPE and u.src[0].src[0].op is Ops.CONST:
    return u.src[0].shape == (1,) * len(u.shape)
  return False

def _eval_const_unary_val(op: Ops, dt: DType, a: Any) -> Any | None:
  match op:
    case Ops.NEG: return -a
    case Ops.ABS: return abs(a)
    case Ops.NOT: return (not a) if dt is dtypes.bool else ~int(a)
    case Ops.EXP2: return math.exp2(a)
    case Ops.LOG2 if a > 0: return math.log2(a)
    case Ops.SIN: return math.sin(a)
    case Ops.SQRT if a >= 0: return math.sqrt(a)
    case Ops.RSQRT if a > 0: return 1.0 / math.sqrt(a)
    case Ops.RECIP if a != 0: return 1.0 / a
  return None

def _eval_const_binary_val(op: Ops, dt: DType, a: Any, b: Any) -> Any | None:
  match op:
    case Ops.ADD: return a + b
    case Ops.SUB: return a - b
    case Ops.MUL: return a * b
    case Ops.DIV:
      if b == 0: return None
      return (a / b) if dt.is_float else (int(a) // int(b))
    case Ops.MOD:
      if b == 0: return None
      return a % b
    case Ops.MAX: return max(a, b)
    case Ops.MIN: return min(a, b)
    case Ops.CMPLT: return a < b
    case Ops.CMPEQ: return a == b
    case Ops.CMPNE: return a != b
    case Ops.AND: return (a and b) if dt is dtypes.bool else (int(a) & int(b))
    case Ops.OR:  return (a or b) if dt is dtypes.bool else (int(a) | int(b))
    case Ops.XOR: return (a != b) if dt is dtypes.bool else (int(a) ^ int(b))
    case Ops.SHL: return int(a) << int(b)
    case Ops.SHR: return int(a) >> int(b)
  return None

def _fold_shaped_unary(u: UOp) -> UOp | None:
  if (a := _const_val(u.src[0])) is None: return None
  if (v := _eval_const_unary_val(u.op, u.dtype, a)) is None: return None
  return _const_shaped(u.dtype, v, u.shape)

def _fold_shaped_binary(u: UOp) -> UOp | None:
  a, b = _const_val(u.src[0]), _const_val(u.src[1])
  if a is None or b is None: return None
  if (v := _eval_const_binary_val(u.op, u.dtype, a, b)) is None: return None
  return _const_shaped(u.dtype, v, u.shape)

def _shrink_expand(x: UOp, s: UOp) -> UOp | None:
  if _const_val(x) is not None: return None
  x_sh = x.shape
  clamped = tuple((0, 1) if xs == 1 else (b, e) for xs, (b, e) in zip(x_sh, s.arg))
  return x.shrink(clamped).expand(s.shape)

def _shrink_pad(x: UOp, p: UOp, s: UOp) -> UOp | None:
  for xs, (pb, _), (sb, se) in zip(x.shape, p.arg, s.arg):
    if smax(se) <= smin(pb) or smin(sb) >= smax(simp_sint(pb + xs)):
      return _const_shaped(s.dtype, False if s.dtype is dtypes.bool else 0, s.shape)
  if all(smin(simp_sint(sb - pb)) >= 0 and smax(simp_sint(se - pb)) <= smin(xs)
         for xs, (pb, _), (sb, se) in zip(x.shape, p.arg, s.arg)):
    return x.shrink(tuple((simp_sint(sb - pb), simp_sint(se - pb)) for (pb, _), (sb, se) in zip(p.arg, s.arg)))
  return None

def _pad_disjoint_from_shrink(u: UOp, bounds: tuple[tuple[sint, sint], ...]) -> bool:
  if u.op is Ops.PAD:
    return any(smax(se) <= smin(pb) or smin(sb) >= smax(simp_sint(pb + xs))
               for xs, (pb, _), (sb, se) in zip(u.src[0].shape, u.arg, bounds))
  if u.op in (Ops.ADD, Ops.OR):
    return _pad_disjoint_from_shrink(u.src[0], bounds) and _pad_disjoint_from_shrink(u.src[1], bounds)
  return False

def _shrink_cat_add(a: UOp, b: UOp, s: UOp) -> UOp | None:
  if _pad_disjoint_from_shrink(a, s.arg): return b.shrink(s.arg)
  if _pad_disjoint_from_shrink(b, s.arg): return a.shrink(s.arg)
  return None

def _fold_reduce_axis(u: UOp) -> UOp | None:
  x = u.src[0]
  red_op, axes = u.arg
  real_axes = tuple(a for a in axes if x.shape[a] != 1)
  if not real_axes: return x
  if real_axes != axes: return x.reduce_axis(red_op, real_axes)
  if x.op is Ops.REDUCE_AXIS and x.arg[0] is red_op:
    return x.src[0].reduce_axis(red_op, tuple(sorted(set(x.arg[1]) | set(real_axes))))
  if (val := _const_val(x)) is not None:
    count = sprod([x.shape[a] for a in real_axes])
    if red_op is Ops.ADD and isinstance(count, int): return _const_shaped(u.dtype, val * count, u.shape)
    if red_op in (Ops.MAX, Ops.MIN): return _const_shaped(u.dtype, val, u.shape)
  return None

def _fold_mul_consts(x: UOp, c1: UOp, c2: UOp) -> UOp | None:
  v1, v2 = _const_val(c1), _const_val(c2)
  if v1 is None or v2 is None: return None
  return x * _const_shaped(x.dtype, v1 * v2, x.shape)

pm_frontend = pm_simplify + PatternMatcher([
  (UPat(Ops.RESHAPE, src=(UPat(Ops.RESHAPE, src=(UPat.var("x"),)),), name="u"), lambda u, x: x.reshape(u.arg)),
  (UPat(Ops.EXPAND, src=(UPat(Ops.EXPAND, src=(UPat.var("x"),)),), name="u"), lambda u, x: x.expand(u.arg)),
  (UPat(Ops.PERMUTE, src=(UPat(Ops.PERMUTE, src=(UPat.var("x"),)).named("p1"),), name="p2"),
   lambda x, p1, p2: x.permute(tuple(p1.arg[i] for i in p2.arg))),
  (UPat(Ops.PAD, src=(UPat(Ops.PAD, src=(UPat.var("x"),)).named("p1"),), name="p2"),
   lambda x, p1, p2: x.pad(tuple((simp_sint(b1 + b2), simp_sint(e1 + e2)) for (b1, e1), (b2, e2) in zip(p1.arg, p2.arg)))),
  (UPat(Ops.SHRINK, src=(UPat(Ops.SHRINK, src=(UPat.var("x"),)).named("s1"),), name="s2"),
   lambda x, s1, s2: x.shrink(tuple((simp_sint(b1 + b2), simp_sint(b1 + e2)) for (b1, _), (b2, e2) in zip(s1.arg, s2.arg)))),
  (UPat(Ops.FLIP, src=(UPat(Ops.FLIP, src=(UPat.var("x"),)).named("f1"),), name="f2"),
   lambda x, f1, f2: x.flip(tuple(a ^ b for a, b in zip(f1.arg, f2.arg)))),
  (UPat(Ops.CONTIGUOUS, src=(UPat(Ops.CONTIGUOUS, src=(UPat.var("x"),)),)), lambda x: x.contiguous()),
  (UPat(Ops.CONTIGUOUS, src=(UPat(Ops.BUFFER, name="x"),)), lambda x: x),
  (UPat(Ops.CONTIGUOUS, src=(UPat.var("x"),)), lambda x: x if _const_val(x) is not None else None),

  (UPat((Ops.RESHAPE, Ops.EXPAND, Ops.PERMUTE, Ops.SHRINK, Ops.FLIP), src=(UPat.var("x"),), name="u"),
   lambda u, x: _const_shaped(u.dtype, v, u.shape) if (not _is_canonical_const(u) and (v := _const_val(x)) is not None
                and not (u.op is Ops.RESHAPE and x.op is Ops.CONST and u.shape == (1,) * len(u.shape))) else None),
  (UPat(Ops.PAD, src=(UPat.var("x"),), name="u"),
   lambda u, x: _const_shaped(u.dtype, False if u.dtype is dtypes.bool else 0, u.shape)
                if ((v := _const_val(x)) is not None and v == 0) else None),
  (UPat(Ops.CAST, src=(UPat.var("x"),), name="u"),
   lambda u, x: _const_shaped(u.dtype, v, u.shape) if (u.shape is not None and (v := _const_val(x)) is not None) else None),

  (UPat(Ops.SHRINK, src=(UPat(Ops.EXPAND, src=(UPat.var("x"),)),), name="s"), _shrink_expand),
  (UPat(Ops.SHRINK, src=(UPat(Ops.PAD, src=(UPat.var("x"),)).named("p"),), name="s"), _shrink_pad),
  (UPat(Ops.SHRINK, src=(UPat(Ops.CAST, src=(UPat.var("x"),)).named("c"),), name="s"),
   lambda x, c, s: x.shrink(s.arg).cast(c.dtype)),
  (UPat(Ops.SHRINK, src=(UPat((Ops.ADD, Ops.OR), src=(UPat.var("a"), UPat.var("b"))),), name="s"), _shrink_cat_add),

  (UPat(Ops.REDUCE_AXIS, name="u"), _fold_reduce_axis),

  (UPat(Ops.CAST, dtype=dtypes.bf16, src=(UPat(Ops.CAST, dtype=dtypes.fp32, src=(UPat.var("x", dtype=dtypes.bf16),)),)),
   lambda x: x),
  (UPat(Ops.BITCAST, src=(UPat(Ops.BITCAST, src=(UPat.var("x"),)),), name="u"),
   lambda u, x: x if u.dtype == x.dtype else None),

  (UPat(GroupOp.Unary, space=Space.TENSOR, name="u"), _fold_shaped_unary),
  (UPat(GroupOp.Binary, space=Space.TENSOR, name="u"), _fold_shaped_binary),
  (UPat(Ops.ADD, space=Space.TENSOR, src=[UPat.var("x"), UPat.var("c")]),
   lambda x, c: x if ((v := _const_val(c)) is not None and v == 0) else None),
  (UPat(Ops.SUB, space=Space.TENSOR, src=(UPat.var("x"), UPat.var("c"))),
   lambda x, c: x if ((v := _const_val(c)) is not None and v == 0) else None),
  (UPat(Ops.MUL, space=Space.TENSOR, src=[UPat.var("x"), UPat.var("c")]),
   lambda x, c: x if ((v := _const_val(c)) is not None and v == 1) else (c if (v == 0 and x.dtype.is_int) else None)),
  (UPat(Ops.DIV, space=Space.TENSOR, src=(UPat.var("x"), UPat.var("c"))),
   lambda x, c: x if ((v := _const_val(c)) is not None and v == 1) else (
     x * _const_shaped(x.dtype, 1.0 / v, x.shape) if (v is not None and x.dtype.is_float and v != 0 and math.isfinite(v)) else None)),
  (UPat(Ops.MUL, space=Space.TENSOR, src=[UPat(Ops.MUL, src=[UPat.var("x"), UPat.var("c1")]), UPat.var("c2")]), _fold_mul_consts),
  (UPat(Ops.ADD, space=Space.TENSOR, src=[UPat.var("a"), UPat(Ops.NEG, src=(UPat.var("b"),))]), lambda a, b: a - b),
  (UPat(Ops.SUB, space=Space.TENSOR, src=(UPat.var("a"), UPat(Ops.NEG, src=(UPat.var("b"),)))), lambda a, b: a + b),
  (UPat(Ops.WHERE, space=Space.TENSOR, src=(UPat.var("cond"), UPat.var("a"), UPat.var("b"))),
   lambda cond, a, b: (a if v else b) if ((v := _const_val(cond)) is not None) else (
     cond if (_const_val(a) is True and _const_val(b) is False) else (
     ~cond if (_const_val(a) is False and _const_val(b) is True) else None))),
])

pm_tensor_simplify = pm_frontend

def simplify_tensor(root: Tensor | UOp) -> Tensor | UOp:
  if isinstance(root, Tensor): return Tensor.from_uop(graph_rewrite(root.uop, pm_frontend))
  return graph_rewrite(root, pm_frontend)

# ---- Layer 0 Reference CPU Evaluator ----

def _strip_cast_expand(u: UOp) -> tuple[UOp, DType | None, tuple[int, ...] | None]:
  cast_dt: DType | None = None
  cur = u
  if cur.op is Ops.CAST:
    cast_dt = cur.dtype
    cur = cur.src[0]
  if cur.op is Ops.EXPAND:
    return cur.src[0], cast_dt, cur.src[0].shape
  return u, None, u.shape

def _view_store_target(u: UOp, ev) -> tuple[UOp, np.ndarray, np.ndarray]:
  """Trace movement views (SHRINK/RESHAPE/PERMUTE/FLIP) back to a root copy and mutable NumPy view."""
  if u.op is Ops.SHRINK:
    base, root, view = _view_store_target(u.src[0], ev)
    return base, root, view[tuple(slice(b, e) for b, e in u.arg)]
  if u.op is Ops.RESHAPE:
    base, root, view = _view_store_target(u.src[0], ev)
    return base, root, view.reshape(u.arg)
  if u.op is Ops.PERMUTE:
    base, root, view = _view_store_target(u.src[0], ev)
    return base, root, view.transpose(u.arg)
  if u.op is Ops.FLIP:
    base, root, view = _view_store_target(u.src[0], ev)
    axes = tuple(i for i, f in enumerate(u.arg) if f)
    return base, root, np.flip(view, axis=axes) if axes else view
  root = ev(u).copy()
  return u, root, root

def eval_tensor(
  root: Tensor | UOp,
  buffers: dict[str, np.ndarray] | None = None,
  *,
  var_vals: dict[UOp | str, int] | None = None,
) -> np.ndarray:
  u_root = root.uop if isinstance(root, Tensor) else root
  verify_tensor(u_root)
  u_root, bound_vals = u_root.unbind_all()
  merged: dict[UOp | str, int | UOp] = {v.arg.name: val for v, val in bound_vals.items()}
  if var_vals:
    for k, val in var_vals.items():
      merged[k.arg.name if isinstance(k, UOp) else k] = int(val)
  if merged:
    u_root = u_root.substitute_vars(merged)
  if (rem := u_root.variables()):
    raise ValueError(f"unbound symbolic variable(s) in eval_tensor: {[v.arg.name for v in rem]}")
  buf_map: dict[str, np.ndarray] = dict(buffers) if buffers else {}
  cache: dict[UOp, np.ndarray] = {}

  def apply_store(st: UOp) -> tuple[UOp, np.ndarray]:
    base, root, view = _view_store_target(st.src[0], ev)
    view[...] = _cast_np(ev(st.src[1]), base.dtype)
    return base, root

  def ev(u: UOp) -> np.ndarray:
    if u in cache: return cache[u]
    op, src, arg, dt = u.op, u.src, u.arg, u.dtype

    match op:
      case Ops.CONST:
        res = _cast_np(np.array(arg), dt)
      case Ops.BUFFER:
        if arg.name in buf_map:
          arr = _cast_np(buf_map[arg.name], dt)
          if arr.shape != arg.shape: arr = arr.reshape(arg.shape)
          res = arr
        elif u in _TENSOR_DATA:
          res = _TENSOR_DATA[u]
        elif u in _TENSOR_DISK:
          res = _read_disk_slice(_TENSOR_DISK[u], dt)
        elif u in _TENSOR_FILL:
          spec = _TENSOR_FILL[u]
          res = _cast_np(np.full(spec.shape, spec.value, dtype=_np_dtype(spec.dtype)), dt)
        else:
          raise KeyError(f"missing buffer {arg.name!r} for Layer 0 evaluation")
      case Ops.ARANGE:
        res = _cast_np(np.arange(arg.start, arg.stop, arg.step), dt)
      case Ops.RESHAPE:
        res = np.reshape(ev(src[0]), arg)
      case Ops.EXPAND:
        res = np.broadcast_to(ev(src[0]), arg)
      case Ops.PERMUTE:
        res = np.transpose(ev(src[0]), arg)
      case Ops.PAD:
        res = np.pad(ev(src[0]), arg, mode="constant", constant_values=0)
      case Ops.SHRINK:
        res = ev(src[0])[tuple(slice(b, e) for b, e in arg)]
      case Ops.FLIP:
        axes = tuple(i for i, f in enumerate(arg) if f)
        res = np.flip(ev(src[0]), axis=axes) if axes else ev(src[0])
      case Ops.CONTIGUOUS:
        res = np.ascontiguousarray(ev(src[0]))
      case Ops.STORE:
        base, arr = apply_store(u)
        if base.op is Ops.BUFFER:
          if base.arg.name in buf_map: buf_map[base.arg.name] = arr
          elif base in _TENSOR_DATA: _TENSOR_DATA[base] = arr
        res = arr
      case Ops.AFTER:
        updated: dict[UOp, np.ndarray] = {}
        for dep in src[1:]:
          if dep.op is Ops.STORE:
            base, arr = apply_store(dep)
            updated[base] = arr
          else:
            ev(dep)
        res = updated[src[0]] if src[0] in updated else ev(src[0])
      case Ops.TAKE:
        res = np.take(ev(src[0]), ev(src[1]).astype(np.int64), axis=arg)
      case Ops.GATHER:
        res = np.take_along_axis(ev(src[0]), ev(src[1]).astype(np.int64), axis=arg)
      case Ops.SCATTER:
        out = ev(src[0]).copy()
        idx = ev(src[1]).astype(np.int64)
        val = _cast_np(ev(src[2]), dt)
        slc = [slice(None)] * out.ndim
        slc[arg] = idx
        out[tuple(slc)] = val
        res = out
      case Ops.REDUCE_AXIS:
        red_op, axes = arg
        if red_op is Ops.ADD and src[0].op is Ops.MUL and dt.is_float:
          m = src[0]
          a_u, a_dt, a_sh = _strip_cast_expand(m.src[0])
          b_u, b_dt, b_sh = _strip_cast_expand(m.src[1])
          if a_sh is not None and b_sh is not None and (a_sh != m.shape or b_sh != m.shape):
            nd = len(m.shape)
            a_keep = [i for i in range(nd) if a_sh[i] == m.shape[i] or a_sh[i] != 1]
            b_keep = [i for i in range(nd) if b_sh[i] == m.shape[i] or b_sh[i] != 1]
            if len(set(a_keep) | set(b_keep)) == nd:
              a_arr = _cast_np(ev(a_u), a_dt) if a_dt is not None else ev(a_u)
              b_arr = _cast_np(ev(b_u), b_dt) if b_dt is not None else ev(b_u)
              a_sq = a_arr.reshape(tuple(a_sh[i] for i in a_keep))
              b_sq = b_arr.reshape(tuple(b_sh[i] for i in b_keep))
              out_idx = [i for i in range(nd) if i not in axes]
              raw = np.einsum(a_sq, a_keep, b_sq, b_keep, out_idx, optimize=True)
              res = _cast_np(raw.reshape(u.shape), dt)
              cache[u] = res
              return res
        x = ev(src[0])
        if red_op is Ops.ADD:   res = _cast_np(np.sum(x, axis=axes, keepdims=True), dt)
        elif red_op is Ops.MUL: res = _cast_np(np.prod(x, axis=axes, keepdims=True), dt)
        elif red_op is Ops.MAX: res = _cast_np(np.max(x, axis=axes, keepdims=True), dt)
        elif red_op is Ops.MIN: res = _cast_np(np.min(x, axis=axes, keepdims=True), dt)
        else: raise ValueError(f"unsupported REDUCE_AXIS {red_op}")
      case Ops.ARGMAX:
        res = np.argmax(ev(src[0]), axis=arg, keepdims=True).astype(np.int32)
      case Ops.TOPK:
        x = ev(src[0])
        key = -x if arg.largest else x
        order = np.argsort(key, axis=arg.dim, kind="stable")
        slc = [slice(None)] * x.ndim
        slc[arg.dim] = slice(0, arg.k)
        idx = order[tuple(slc)]
        res = idx.astype(np.int32) if arg.indices else _cast_np(np.take_along_axis(x, idx, axis=arg.dim), dt)
      case Ops.CAST:
        res = _cast_np(ev(src[0]), dt)
      case Ops.BITCAST:
        res = ev(src[0]).view(_np_dtype(dt))
      case Ops.SINK:
        for s in src: ev(s)
        res = np.array(0, dtype=np.int32)
      case _ if op in GroupOp.ALU:
        vals = [ev(s) for s in src]
        match op:
          case Ops.NEG:    res = -vals[0]
          case Ops.ABS:    res = np.abs(vals[0])
          case Ops.NOT:    res = np.logical_not(vals[0]) if dt is dtypes.bool else np.bitwise_not(vals[0])
          case Ops.EXP2:   res = np.exp2(vals[0])
          case Ops.LOG2:   res = np.log2(vals[0])
          case Ops.SIN:    res = np.sin(vals[0])
          case Ops.SQRT:   res = np.sqrt(vals[0])
          case Ops.RSQRT:  res = np.float32(1.0) / np.sqrt(vals[0])
          case Ops.RECIP:  res = np.float32(1.0) / vals[0]
          case Ops.ADD:    res = vals[0] + vals[1]
          case Ops.SUB:    res = vals[0] - vals[1]
          case Ops.MUL:    res = vals[0] * vals[1]
          case Ops.DIV:    res = (vals[0] / vals[1]) if dt.is_float else (vals[0] // vals[1])
          case Ops.MOD:    res = vals[0] % vals[1]
          case Ops.MAX:    res = np.maximum(vals[0], vals[1])
          case Ops.MIN:    res = np.minimum(vals[0], vals[1])
          case Ops.CMPLT:  res = vals[0] < vals[1]
          case Ops.CMPEQ:  res = vals[0] == vals[1]
          case Ops.CMPNE:  res = vals[0] != vals[1]
          case Ops.AND:    res = np.logical_and(vals[0], vals[1]) if dt is dtypes.bool else np.bitwise_and(vals[0], vals[1])
          case Ops.OR:     res = np.logical_or(vals[0], vals[1]) if dt is dtypes.bool else np.bitwise_or(vals[0], vals[1])
          case Ops.XOR:    res = np.logical_xor(vals[0], vals[1]) if dt is dtypes.bool else np.bitwise_xor(vals[0], vals[1])
          case Ops.SHL:    res = np.left_shift(vals[0], vals[1])
          case Ops.SHR:    res = np.right_shift(vals[0], vals[1])
          case Ops.WHERE:  res = np.where(vals[0], vals[1], vals[2])
          case Ops.MULACC:
            ab = vals[0] * vals[1]
            if arg and arg[0]: ab = -ab
            c = -vals[2] if (arg and arg[1]) else vals[2]
            res = ab + c
          case _: raise NotImplementedError(f"Layer 0 eval missing ALU op {op}")
        res = _cast_np(res, dt)
      case _:
        raise NotImplementedError(f"Layer 0 eval missing op {op}")

    cache[u] = res
    return res

  return ev(u_root)
