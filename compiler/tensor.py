import itertools, json, pathlib, struct, weakref
from collections import OrderedDict
from typing import Any
from .dtype import DType, dtypes
from .mixin import Mixin, _argfix
from .ops import VerifyError, pm_simplify
from .uop import GroupOp, Ops, PatternMatcher, UOp, UPat, _broadcast_shape, graph_rewrite, simp_sint, sint

# BUFFER UOps are immutable and hash-consed, so their contents live beside the graph, keyed by the UOp (weakly, so they die
# together): host bytes already in the buffer's dtype, or a (path, offset, nbytes) file range read at upload
_BUFFER_SOURCE: weakref.WeakKeyDictionary[UOp, bytes | tuple[pathlib.Path, int, int]] = weakref.WeakKeyDictionary()
# every live Tensor, so assign() can point the ones viewing the assigned buffer at the new value
_ALL_TENSORS: weakref.WeakSet["Tensor"] = weakref.WeakSet()
# BUFFERs are hash-consed by name, so two distinct buffers need distinct names
_BUF_ID = itertools.count()

_SAFE_DTYPES: dict[str, DType] = {
  "BOOL": dtypes.bool, "U8": dtypes.u8, "I8": dtypes.u8, "I32": dtypes.i32, "I64": dtypes.i32, "U32": dtypes.u32, "U64": dtypes.u64,
  "BF16": dtypes.bf16, "F16": dtypes.fp32, "F32": dtypes.fp32, "F64": dtypes.fp32, "F8_E4M3": dtypes.e4m3,
}
_STRUCT_FMT = {dtypes.bool: "?", dtypes.u8: "B", dtypes.i32: "i", dtypes.u32: "I", dtypes.u64: "Q", dtypes.fp32: "f", dtypes.bf16: "f"}
_FMT_DTYPE = {"?": dtypes.bool, "B": dtypes.u8, "i": dtypes.i32, "I": dtypes.u32, "Q": dtypes.u64, "f": dtypes.fp32}

def _flatten(data: Any) -> tuple[tuple[int, ...], list]:
  if not isinstance(data, (list, tuple)): return (), [data]
  if not data: return (0,), []
  parts = [_flatten(d) for d in data]
  if any(p[0] != parts[0][0] for p in parts): raise ValueError("ragged nested sequence")
  return (len(data), *parts[0][0]), [x for p in parts for x in p[1]]

def _pack_host(vals: list, dt: DType) -> bytes:
  if (fmt := _STRUCT_FMT.get(dt)) is None: raise TypeError(f"cannot pack host values as {dt}")
  conv = bool if dt is dtypes.bool else float if dt.is_float else int
  raw = struct.pack(f"<{len(vals)}{fmt}", *map(conv, vals))
  if dt is not dtypes.bf16: return raw
  # round-to-nearest-even fp32 -> bf16
  return b"".join(struct.pack("<H", ((u + 0x7FFF + ((u >> 16) & 1)) >> 16) & 0xFFFF) for (u,) in struct.iter_unpack("<I", raw))

class Tensor(Mixin):
  __slots__ = ("uop", "__weakref__")

  @property
  def _uop(self) -> UOp: return self.uop
  @classmethod
  def _wrap_uop(cls, u: UOp) -> "Tensor": return cls.from_uop(u)

  def __init__(self, data: Any, dtype: DType | str | None = None, *, name: str | None = None):
    dt = dtypes.from_name(dtype) if dtype is not None else None
    if isinstance(data, (Tensor, UOp)):
      u = data.uop if isinstance(data, Tensor) else data
      self.uop = u if dt is None else u.cast(dt)
    elif isinstance(data, pathlib.Path):
      self.uop = Tensor.from_disk(data, dtype=dtypes.u8 if dt is None else dt, name=name).uop
    elif isinstance(data, (bool, int, float)):
      self.uop = UOp.const(data, dt)
    else:
      if isinstance(data, (list, tuple)):
        shape, vals = _flatten(data)
        src_dt = dtypes.fp32 if any(isinstance(v, float) for v in vals) else dtypes.bool if vals and all(isinstance(v, bool) for v in vals) else dtypes.i32
        raw = None
      else:  # anything exposing the buffer protocol (bytes, array.array, numpy arrays, ...)
        mv = memoryview(data)
        if (src_dt := _FMT_DTYPE.get(mv.format.lstrip("<=@"))) is None: raise TypeError(f"unsupported host buffer format {mv.format!r}")
        shape, vals, raw = tuple(mv.shape), None, mv.tobytes()
      target_dt = src_dt if dt is None else dt
      if raw is None or target_dt is not src_dt:
        if vals is None: vals = _flatten(mv.tolist())[1]
        raw = _pack_host(vals, target_dt)
      self.uop = UOp.buffer(f"t{next(_BUF_ID)}" if name is None else name, shape, target_dt)
      _BUFFER_SOURCE[self.uop] = raw
    _ALL_TENSORS.add(self)

  @staticmethod
  def from_uop(u: UOp) -> "Tensor":
    t = Tensor.__new__(Tensor)
    t.uop = u
    _ALL_TENSORS.add(t)
    return t

  @staticmethod
  def from_disk(path: str | pathlib.Path, *, shape: tuple[int, ...] | None = None, dtype: DType | str = dtypes.u8, offset: int = 0,
                nbytes: int | None = None, name: str | None = None) -> "Tensor":
    p, dt = pathlib.Path(path), dtypes.from_name(dtype)
    size = p.stat().st_size - offset if nbytes is None else nbytes
    u = UOp.buffer(f"disk_{p.name}_{next(_BUF_ID)}" if name is None else name,
                   (size // max(1, dt.bits // 8),) if shape is None else tuple(shape), dt)
    _BUFFER_SOURCE[u] = (p, int(offset), int(size))
    return Tensor.from_uop(u)

  @staticmethod
  def buffer(name: str, shape: tuple[int, ...] | int, dtype: DType | str = dtypes.fp32, *, addr: int | None = None) -> "Tensor":
    return Tensor.from_uop(UOp.buffer(name, shape, dtype, addr=addr))
  @staticmethod
  def empty(*shape, dtype: DType | str = dtypes.fp32, name: str | None = None) -> "Tensor":
    return Tensor.buffer(f"t{next(_BUF_ID)}" if name is None else name, _argfix(*shape), dtype=dtype)

  # ---- python protocol ----

  def variables(self) -> list[UOp]: return self.uop.variables()
  def unbind_all(self) -> tuple["Tensor", dict[UOp, int]]:
    u, vals = self.uop.unbind_all()
    return Tensor.from_uop(u), vals
  def __len__(self) -> int:
    if self.ndim == 0 or not isinstance(self.shape[0], int): raise TypeError("len() of a 0-d or symbolic tensor")
    return self.shape[0]
  def __hash__(self) -> int: return id(self)
  def __bool__(self) -> bool: raise TypeError("__bool__ on Tensor is not defined")
  def __repr__(self) -> str: return f"<Tensor {self.shape} {self.dtype.name} {self.uop.op.name}>"
  def __eq__(self, x) -> "Tensor": return self.eq(x)  # type: ignore[override]
  def __ne__(self, x) -> "Tensor": return self.ne(x)  # type: ignore[override]
  def _ufix(self, x: Any) -> "Tensor":
    return x if isinstance(x, Tensor) else Tensor(x) if isinstance(x, (list, tuple)) else super()._ufix(x)

  def realize(self) -> "Tensor":
    if self.uop.op is Ops.BUFFER: return self
    lower_tensor(self.uop)
    raise AssertionError("unreachable")

  # ---- assign: a STORE into the (view of the) buffer, plus AFTER so readers see the new value ----

  def assign(self, x: "Tensor | bool | int | float") -> "Tensor":
    val = (x if isinstance(x, Tensor) else Tensor.full(self.shape, x, dtype=self.dtype)).expand(self.shape).cast(self.dtype)
    if self.uop is val.uop: return self
    views = [self.uop]
    while views[-1].op in GroupOp.Movement or views[-1].op is Ops.BITCAST: views.append(views[-1].src[0])
    assigned_to = views[-1].storage_base
    live = list(_ALL_TENSORS)
    held = {t.uop for t in live}
    # assigning to a pending (non-buffer) tensor that views no other live tensor just rebinds it
    if not assigned_to.has_buffer_identity() and not any(u in held for u in views[1:]):
      self.uop = val.uop
      return self
    ib = next((u for u in reversed(views) if u.has_buffer_identity(after_ok=True) and (u is self.uop or u in held)),
              next((u for u in views[1:] if u in held), views[-1]))
    after = ib.after((ib if ib is self.uop else self.uop).store(val.uop))
    for t in live:
      if t.uop is ib or t.uop.storage_base is assigned_to: t.uop = t.uop.substitute({ib: after})
    return self

  # ---- indexing: ints, slices (positive step) and None; tensor indexing is a one-hot mask in user code ----

  def __getitem__(self, indices: Any) -> "Tensor":
    idx = list(indices) if isinstance(indices, tuple) else [indices]
    if (ell := [k for k, i in enumerate(idx) if i is Ellipsis]):
      n_real = sum(1 for i in idx if i is not None and i is not Ellipsis)
      idx = idx[:ell[0]] + [slice(None)] * (self.ndim - n_real) + idx[ell[0] + 1:]
    if (n_real := sum(1 for i in idx if i is not None)) > self.ndim: raise IndexError(f"too many indices for ndim {self.ndim}")
    idx.extend([slice(None)] * (self.ndim - n_real))
    x, d = self, 0
    for item in idx:
      if item is None:
        x, d = x.unsqueeze(d), d + 1
      elif isinstance(item, (int, UOp)):
        n = x.shape[d]
        i: sint = simp_sint(n + item) if isinstance(item, int) and item < 0 else item
        if isinstance(n, int) and isinstance(i, int) and not (0 <= i < n): raise IndexError(f"index {item} out of bounds for size {n}")
        x = x.shrink(tuple((i, simp_sint(i + 1)) if k == d else None for k in range(x.ndim))).squeeze(d)
      elif isinstance(item, slice):
        x, d = x._slice(d, item), d + 1
      else:
        raise TypeError(f"unsupported index type {type(item).__name__} (index with a one-hot mask instead)")
    return x

  def _slice(self, d: int, s: slice) -> "Tensor":
    n, step = self.shape[d], 1 if s.step is None else s.step
    if step <= 0: raise NotImplementedError("slices need a positive step")
    if isinstance(n, int) and all(v is None or isinstance(v, int) for v in (s.start, s.stop)):
      start, stop, _ = s.indices(n)
      stop = max(start, stop)
    else:
      if step != 1: raise NotImplementedError("symbolic slices need step 1")
      fix = lambda v, dflt: dflt if v is None else simp_sint(n + v) if isinstance(v, int) and v < 0 else simp_sint(v)
      start, stop = fix(s.start, 0), fix(s.stop, n)
    x = self.shrink(tuple((start, stop) if k == d else None for k in range(self.ndim)))
    if step == 1 or (length := x.shape[d]) == 0: return x
    # strided: pad to a multiple of step, split the axis into (blocks, step) and keep column 0
    x = x.pad(tuple((0, -length % step) if k == d else None for k in range(self.ndim)))
    sh = x.shape
    x = x.reshape(*sh[:d], sh[d] // step, step, *sh[d + 1:]).shrink(tuple((0, 1) if k == d + 1 else None for k in range(x.ndim + 1)))
    return x.reshape(*sh[:d], sh[d] // step, *sh[d + 1:])

# ---- safetensors & state dicts ----

def safe_load(path: str | pathlib.Path) -> dict[str, Tensor]:
  """lazily load a .safetensors file, a sharded .index.json, or a directory into disk-backed Tensors"""
  p = pathlib.Path(path)
  if p.is_dir():
    if (idx := p / "model.safetensors.index.json").exists(): p = idx
    elif (single := p / "model.safetensors").exists(): p = single
    else: raise FileNotFoundError(f"no safetensors or index.json in {p}")
  if p.suffix == ".json":
    out: dict[str, Tensor] = {}
    for shard in sorted(set(json.loads(p.read_text())["weight_map"].values())): out.update(safe_load(p.parent / shard))
    return out
  with open(p, "rb") as f:
    header_len = int.from_bytes(f.read(8), "little")
    header = json.loads(f.read(header_len).decode("utf-8"))
  tensors: dict[str, Tensor] = {}
  for name, info in header.items():
    if name == "__metadata__": continue
    if (dt := _SAFE_DTYPES.get(info["dtype"])) is None: raise ValueError(f"unsupported safetensors dtype {info['dtype']!r} for {name!r}")
    start, end = info["data_offsets"]
    tensors[name] = Tensor.from_disk(p, shape=tuple(info["shape"]), dtype=dt, offset=8 + header_len + start, nbytes=end - start, name=name)
  return tensors

def get_state_dict(obj: Any, prefix: str = "") -> dict[str, Tensor]:
  state: dict[str, Tensor] = OrderedDict()
  if isinstance(obj, Tensor): state[prefix.rstrip(".")] = obj
  elif hasattr(obj, "__dict__"):
    for k, v in obj.__dict__.items():
      if not k.startswith("_") and v is not None: state.update(get_state_dict(v, f"{prefix}{k}."))
  elif isinstance(obj, (list, tuple)):
    for i, v in enumerate(obj): state.update(get_state_dict(v, f"{prefix}{i}."))
  elif isinstance(obj, dict):
    for k, v in obj.items(): state.update(get_state_dict(v, f"{prefix}{k}."))
  return state

def load_state_dict(model: Any, state_dict: dict[str, Tensor], strict: bool = True) -> list[str]:
  model_sd = get_state_dict(model)
  missing, unexpected = [k for k in model_sd if k not in state_dict], [k for k in state_dict if k not in model_sd]
  if strict and (missing or unexpected): raise KeyError(f"state_dict mismatch: missing={missing[:5]}, unexpected={unexpected[:5]}")
  loaded: list[str] = []
  for k, dst in model_sd.items():
    if k not in state_dict: continue
    if dst.shape != (src := state_dict[k]).shape: raise ValueError(f"shape mismatch for {k!r}: {dst.shape} vs {src.shape}")
    dst.uop = src.uop
    loaded.append(k)
  return loaded

# ---- Layer 0 verifier & frontend rewrites (tinygrad-style mop_cleanup + symbolic) ----

def verify_tensor(root: Tensor | UOp) -> None:
  for u in (root.uop if isinstance(root, Tensor) else root).toposort(enter_calls=True):
    if u.op in GroupOp.Kernel or (u.op is Ops.REDUCE and len(u.src) > 1):
      raise VerifyError(f"Layer 1 op {u.op.name} is not valid in a Layer 0 tensor graph")
    if u.op is Ops.STORE:
      if len(u.src) != 2 or u.src[0].shape is None or u.src[0].shape != u.src[1].shape:
        raise VerifyError(f"Layer 0 STORE requires (view, val) with matching shapes, got {[s.shape for s in u.src]}")
    elif u.op not in (Ops.SINK, Ops.STACK, Ops.CALL) and u.shape is None:
      raise VerifyError(f"Layer 0 UOp {u.op.name} has no tensor shape")

def _is_unit(s: sint) -> bool: return isinstance(s, int) and s == 1

def _permute_as_reshape(u: UOp, x: UOp) -> UOp | None:
  if (xs := x.shape) is None: return None
  non_unit = [i for i in u.marg if not _is_unit(xs[i])]
  return x.reshape(u.shape) if non_unit == sorted(non_unit) else None

def _shrink_past_reshape(s: UOp, r: UOp, x: UOp) -> UOp | None:
  if (xs := x.shape) is None or (rs := r.shape) is None: return None
  x_non1 = [i for i, d in enumerate(xs) if not _is_unit(d)]
  r_non1 = [i for i, d in enumerate(rs) if not _is_unit(d)]
  if len(x_non1) != len(r_non1) or any(xs[i] != rs[j] for i, j in zip(x_non1, r_non1)): return None
  sm = s.marg
  if any(sm[i] != (0, 1) for i in range(len(rs)) if _is_unit(rs[i])): return None
  x_marg: list[tuple[sint, sint]] = [(0, d) for d in xs]
  for xi, ri in zip(x_non1, r_non1): x_marg[xi] = sm[ri]
  return x._mop(Ops.SHRINK, tuple(x_marg)).reshape(s.shape)

def _drop_broadcast_views(u: UOp) -> UOp | None:
  if (us := u.shape) is None: return None
  new_src, changed = list(u.src), False
  for i, s in enumerate(u.src):
    cand_x: UOp | None = None
    if s.op is Ops.RESHAPE and (xs := s.src[0].shape) is not None:
      k = len(s.shape) - len(xs)
      if k > 0 and s.shape == (1,) * k + xs: cand_x = s.src[0]
    elif s.op is Ops.EXPAND and s.src[0].is_const:
      cand_x = s.src[0]
    if cand_x is not None:
      shapes = tuple(cand_x.shape if j == i else a.shape for j, a in enumerate(new_src))
      if all(sh is not None for sh in shapes) and _broadcast_shape(*shapes) == us:
        new_src[i], changed = cand_x, True
  return u.replace(src=tuple(new_src)) if changed else None

def _simplify_call_body(ctx: dict[UOp, UOp] | None, c: UOp) -> UOp | None:
  if c.src[0].op is not Ops.SINK: return None
  if ctx is None: ctx = {}
  if (nb := ctx.get(c.src[0])) is None:
    nb = graph_rewrite(c.src[0], pm_frontend, ctx=ctx)
    ctx[c.src[0]] = ctx[nb] = nb
  return None if nb is c.src[0] else c.replace(src=(nb, *c.src[1:]))

pm_frontend = pm_simplify + PatternMatcher([
  # remove noop movement ops
  (UPat(Ops.RESHAPE, src=(UPat.var("x"), UPat()), name="u"), lambda u, x: x if x.shape == u.shape else None),
  (UPat(Ops.PERMUTE, src=(UPat.var("x"), UPat()), name="u"), _permute_as_reshape),
  (UPat(Ops.EXPAND, src=(UPat.var("x"), UPat()), name="u"), lambda u, x: x if x.shape == u.shape else None),
  (UPat(Ops.SHRINK, src=(UPat.var("x"), UPat(), UPat()), name="u"),
   lambda u, x: x if x.shape == u.shape and all(o == 0 for o, _ in u.marg) else None),
  (UPat(Ops.PAD, src=(UPat.var("x"), UPat(), UPat()), name="u"),
   lambda u, x: x if x.shape == u.shape and all(o == 0 for o, _ in u.marg) else None),

  # merge chains of the same movement op
  (UPat(Ops.RESHAPE, src=(UPat(Ops.RESHAPE, src=(UPat.var("x"), UPat())), UPat()), name="u"), lambda u, x: x.reshape(u.marg)),
  (UPat(Ops.PERMUTE, src=(UPat(Ops.PERMUTE, src=(UPat.var("x"), UPat()), name="p1"), UPat()), name="p2"),
   lambda x, p1, p2: x.permute(tuple(p1.marg[i] for i in p2.marg))),
  (UPat(Ops.EXPAND, src=(UPat(Ops.EXPAND, src=(UPat.var("x"), UPat()), name="e1"), UPat()), name="e2"),
   lambda x, e1, e2: x._mop(Ops.EXPAND, tuple(e2.marg) + tuple(e1.marg))),
  (UPat(Ops.SHRINK, src=(UPat(Ops.SHRINK, src=(UPat.var("x"), UPat(), UPat()), name="s1"), UPat(), UPat()), name="s2"),
   lambda x, s1, s2: x._mop(Ops.SHRINK, tuple((simp_sint(o1 + o2), n2) for (o1, _), (o2, n2) in zip(s1.marg, s2.marg)))),
  (UPat(Ops.PAD, src=(UPat(Ops.PAD, src=(UPat.var("x"), UPat(), UPat()), name="p1"), UPat(), UPat()), name="p2"),
   lambda x, p1, p2: x._mop(Ops.PAD, tuple((simp_sint(o1 + o2), n2) for (o1, _), (o2, n2) in zip(p1.marg, p2.marg)))),

  # push SHRINK past pure squeeze/unsqueeze RESHAPE so adjacent SHRINKs merge
  (UPat(Ops.SHRINK, src=(UPat(Ops.RESHAPE, src=(UPat.var("x"), UPat()), name="r"), UPat(), UPat()), name="s"), _shrink_past_reshape),

  # drop redundant leading-1 RESHAPEs and EXPAND(const) under implicit broadcast ops
  (UPat(GroupOp.Broadcastable, name="u"), _drop_broadcast_views),

  # fold movement / cast on expanded constants
  (UPat((Ops.RESHAPE, Ops.PERMUTE), src=(UPat(Ops.EXPAND, src=(UPat.var("c"), UPat())), UPat()), name="u"),
   lambda u, c: (c._mop(Ops.EXPAND, u.shape) if u.shape else c) if c.is_const else None),
  (UPat(Ops.SHRINK, src=(UPat(Ops.EXPAND, src=(UPat.var("c"), UPat())), UPat(), UPat()), name="u"),
   lambda u, c: (c._mop(Ops.EXPAND, u.shape) if u.shape else c) if c.is_const else None),
  (UPat(Ops.CAST, src=(UPat(Ops.EXPAND, src=(UPat.var("c"), UPat()), name="e"),), name="u"),
   lambda u, c, e: c.cast(u.dtype)._mop(Ops.EXPAND, e.marg) if c.is_const else None),

  # trivial reduce & stage
  (UPat(Ops.REDUCE, src=(UPat.var("x"),), name="u"), lambda u, x: x if u.arg[1] == 0 else None),
  (UPat(Ops.STAGE, src=(UPat((Ops.STAGE, Ops.BUFFER), name="x"),)), lambda x: x),

  # simplify each unique CALL(SINK, ...) function body once
  (UPat(Ops.CALL, name="c"), _simplify_call_body),
])

def simplify_tensor(root: Tensor | UOp) -> Tensor | UOp:
  ctx: dict[UOp, UOp] = {}
  if isinstance(root, Tensor): return Tensor.from_uop(graph_rewrite(root.uop, pm_frontend, ctx=ctx))
  return graph_rewrite(root, pm_frontend, ctx=ctx)

# ---- Layer 0 -> Layer 1 lowering ----

def lower_tensor(root: Tensor | UOp) -> UOp:
  """lower a Layer 0 tensor graph to Layer 1 kernel SINKs"""
  u = root.uop if isinstance(root, Tensor) else root
  u = simplify_tensor(u)
  verify_tensor(u)
  from .rangeify import get_kernel_graph
  return get_kernel_graph(u)
