# The UOp graph core, trimmed from tinygrad (tinygrad/uop/ops.py, revision 7dd8c6f84).
# Copyright (c) 2024, the tiny corp. MIT License: see compiler/LICENSE.tinygrad.
#
# Kept: hash-consed immutable UOps, UPat matching, PatternMatcher, and graph_rewrite's unified driver (top-down and
# bottom-up, fixed point, waitlist instead of spinning). Dropped: compiled patterns, rewrite tracking/viz, CALL bodies,
# spec checks, symbolic folding, the Tensor mixins. Unlike tinygrad, dtype is an explicit field: our ops carry
# hardware formats (BFP8 in L1, FP32 in Dst) that cannot be inferred from their sources.
from __future__ import annotations
import collections, functools, inspect, itertools, weakref
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable, Sequence

# ---- dtypes ----

@dataclass(frozen=True, eq=True)
class DType:
  name: str
  bits: int        # per datum; BFP8 counts the datum only, its shared exponent is per 16 datums
  block: int = 0   # datums sharing one exponent, 0 if none
  def __repr__(self): return f"dtypes.{self.name}"

class dtypes:
  """Only formats our kernels store or compute in. No BFP4: converting NVFP4/MXFP4 checkpoints to it loses too much. FP32 that passes through SrcA/SrcB is truncated to 19 bits (TF32);
  lowering routes FP32 L1 data to Dst with an unpack to Dst instead, so TF32 never appears as a dtype."""
  void = DType("void", 0)
  bool = DType("bool", 1)      # comparison results (SFPU lane conditions)
  int32 = DType("int32", 32)
  uint32 = DType("uint32", 32)
  bf16 = DType("bf16", 16)
  fp32 = DType("fp32", 32)
  bfp8 = DType("bfp8", 8, block=16)
  floats = (bf16, fp32, bfp8)

# ---- ops ----

class Ops(Enum):
  # graph structure
  SINK = auto(); AFTER = auto()   # AFTER: src[0], once the effects in src[1:] (e.g. STOREs) have happened
  # values and storage
  CONST = auto(); PARAM = auto(); DEFINE_VAR = auto()
  # loops
  RANGE = auto(); END = auto()
  # generic math
  ADD = auto(); SUB = auto(); MUL = auto(); DIV = auto(); MAX = auto(); NEG = auto()
  EXP2 = auto(); LOG2 = auto(); SQRT = auto(); RECIP = auto(); RSQRT = auto()
  CAST = auto(); REDUCE = auto(); WHERE = auto(); CMPLT = auto()
  # memory
  INDEX = auto(); LOAD = auto(); STORE = auto()

class GroupOp:
  Unary = {Ops.NEG, Ops.EXP2, Ops.LOG2, Ops.SQRT, Ops.RECIP, Ops.RSQRT}
  Binary = {Ops.ADD, Ops.SUB, Ops.MUL, Ops.DIV, Ops.MAX, Ops.CMPLT}
  Ternary = {Ops.WHERE}
  ALU = Unary | Binary | Ternary
  Commutative = {Ops.ADD, Ops.MUL, Ops.MAX}

# ---- UOp ----

class UOpMetaClass(type):
  ucache: dict[tuple, weakref.ReferenceType[UOp]] = {}
  def __call__(cls, op: Ops, dtype: DType = dtypes.void, src: tuple[UOp, ...] = (), arg: Any = None):
    # type(arg) is in the key: True == 1 and 1 == 1.0 as dict keys, but they are different constants
    if (wret := UOpMetaClass.ucache.get(key := (op, dtype, src, arg, type(arg)))) is not None and (ret := wret()) is not None:
      return ret
    UOpMetaClass.ucache[key] = weakref.ref(created := super().__call__(op, dtype, src, arg))
    return created

@dataclass(eq=False)
class UOp(metaclass=UOpMetaClass):
  """Immutable and hash-consed: structurally equal UOps are the same object, so equality is identity."""
  op: Ops
  dtype: DType = dtypes.void
  src: tuple[UOp, ...] = ()
  arg: Any = None   # nodes also keep small caches in __dict__ (e.g. the PatternMatcher's set of source ops)

  def __del__(self):
    try: del UOpMetaClass.ucache[(self.op, self.dtype, self.src, self.arg, type(self.arg))]
    except (AttributeError, KeyError): pass
  def __reduce__(self): return UOp, (self.op, self.dtype, self.src, self.arg)
  def replace(self, **kwargs) -> UOp:
    new = (kwargs.pop("op", self.op), kwargs.pop("dtype", self.dtype), kwargs.pop("src", self.src), kwargs.pop("arg", self.arg))
    assert not kwargs, f"unused kwargs in replace {list(kwargs)}"
    return self if new == (self.op, self.dtype, self.src, self.arg) else UOp(*new)

  def toposort(self, gate: Callable[[UOp], bool] | None = None) -> dict[UOp, None]:
    """Every UOp reachable from self, sources before users. gate(u) False stops the walk below u."""
    ret: dict[UOp, None] = {}
    stack: list[tuple[UOp, bool]] = [(self, False)]
    while stack:
      node, visited = stack.pop()
      if node in ret: continue
      if not visited:
        if gate is None or gate(node):
          stack.append((node, True))
          for s in reversed(node.src): stack.append((s, False))
      else: ret[node] = None
    return ret

  # construction helpers
  @staticmethod
  def const(dtype: DType, b: Any) -> UOp: return UOp(Ops.CONST, dtype, arg=b)
  @staticmethod
  def sink(*srcs: UOp, arg=None) -> UOp: return UOp(Ops.SINK, dtypes.void, tuple(srcs), arg)
  def alu(self, op: Ops, *src: UOp) -> UOp:
    dt = dtypes.bool if op is Ops.CMPLT else (src[-1] if op is Ops.WHERE else self).dtype
    return UOp(op, dt, (self,) + src)
  def cast(self, dtype: DType) -> UOp: return self if self.dtype == dtype else UOp(Ops.CAST, dtype, (self,))
  def _ufix(self, x) -> UOp: return x if isinstance(x, UOp) else UOp.const(self.dtype, x)
  def __add__(self, x): return self.alu(Ops.ADD, self._ufix(x))
  def __radd__(self, x): return self._ufix(x).alu(Ops.ADD, self)
  def __sub__(self, x): return self.alu(Ops.SUB, self._ufix(x))
  def __mul__(self, x): return self.alu(Ops.MUL, self._ufix(x))
  def __rmul__(self, x): return self._ufix(x).alu(Ops.MUL, self)
  def __truediv__(self, x): return self.alu(Ops.DIV, self._ufix(x))
  def __neg__(self): return self.alu(Ops.NEG)

  def __repr__(self) -> str: return pretty(self)

def pretty(root: UOp, limit: int = 200) -> str:
  """One line per UOp, sources by index: easier to read than nested reprs once nodes are shared."""
  nodes = list(root.toposort())
  idx = {u: i for i, u in enumerate(nodes)}
  lines = [f"{i:3d} {u.op.name:<10s} {u.dtype.name:<6s} {[idx[s] for s in u.src]!s:<14s} {u.arg!r}" for i, u in enumerate(nodes)]
  return "\n".join(lines if len(lines) <= limit else lines[:limit] + [f"... {len(lines) - limit} more"])

# ---- patterns ----

class UPat:
  __slots__ = ("op", "match_dtype", "arg", "name", "src", "is_any", "strict_length", "required_len", "early_reject")
  def __init__(self, op: Ops | tuple[Ops, ...] | set[Ops] | None = None, dtype: DType | tuple[DType, ...] | None = None,
               src: tuple[UPat, ...] | list[UPat] | UPat | None = None, arg: Any = None, name: str | None = None,
               allow_any_len: bool = False, is_any: bool = False):
    self.op = (op,) if isinstance(op, Ops) else (tuple(op) if isinstance(op, set) else op)
    self.match_dtype = (dtype,) if isinstance(dtype, DType) else dtype
    self.arg, self.name, self.is_any = arg, name, is_any
    assert name != "ctx", "UPat can't be named ctx"
    # a list matches any permutation of its sources, a tuple exactly, a single UPat every source
    if isinstance(src, list): self.src = list(itertools.permutations(src))
    elif isinstance(src, tuple): self.src = [src]
    elif isinstance(src, UPat): self.src = [itertools.repeat(src)]
    else: self.src = None
    self.strict_length = not (allow_any_len or isinstance(src, UPat) or src is None)
    self.required_len = 0 if isinstance(src, UPat) or src is None else len(src)
    first = [src] if isinstance(src, UPat) else ([] if src is None else self.src[0])
    self.early_reject = {p.op[0] for p in first if p.op is not None and len(p.op) == 1}

  @staticmethod
  def any(*src: UPat) -> UPat: return UPat(src=src, is_any=True)
  @staticmethod
  def var(name: str | None = None, dtype=None) -> UPat: return UPat(dtype=dtype, name=name)
  @staticmethod
  def cvar(name: str | None = None, dtype=None, arg=None) -> UPat: return UPat(Ops.CONST, dtype, name=name, arg=arg)
  def named(self, name: str) -> UPat:
    p = UPat.__new__(UPat)
    for k in UPat.__slots__: setattr(p, k, getattr(self, k))
    p.name = name
    return p

  def match(self, uop: UOp, store: dict[str, UOp]) -> list[dict[str, UOp]]:
    if self.is_any: return [m for x in self.src[0] for m in x.match(uop, store.copy())]
    if (self.op is not None and uop.op not in self.op) or \
       (self.name is not None and store.setdefault(self.name, uop) is not uop) or \
       (self.match_dtype is not None and uop.dtype not in self.match_dtype) or \
       (self.arg is not None and self.arg != uop.arg) or \
       len(uop.src) < self.required_len or (self.strict_length and len(uop.src) != self.required_len): return []
    if self.src is None: return [store]
    res: list[dict[str, UOp]] = []
    for vp in self.src:
      stores = [store.copy()]
      for uu, vv in zip(uop.src, vp): stores = [m for s in stores for m in vv.match(uu, s)]
      res.extend(stores)
    return res

  def __repr__(self): return f"UPat({self.op}, name={self.name!r})"

def _interpret(p: UPat, fxn: Callable) -> Callable:
  if "ctx" in inspect.signature(fxn).parameters:
    return lambda uop, ctx: next((r for m in p.match(uop, {}) if (r := fxn(ctx=ctx, **m)) is not None), None)
  return lambda uop, _: next((r for m in p.match(uop, {}) if (r := fxn(**m)) is not None), None)

class PatternMatcher:
  def __init__(self, patterns: Sequence[tuple[UPat, Callable]]):
    self.patterns = list(patterns)
    self.pdict: dict[Ops, list[tuple[Callable, set[Ops]]]] = {}
    for p, fxn in self.patterns:
      assert p.op is not None, "the top UPat of a pattern must name its op(s)"
      for op in p.op: self.pdict.setdefault(op, []).append((_interpret(p, fxn), p.early_reject))
  def __add__(self, more: PatternMatcher) -> PatternMatcher: return PatternMatcher(self.patterns + more.patterns)

  def rewrite(self, uop: UOp, ctx=None) -> UOp | None:
    if pats := self.pdict.get(uop.op):
      if (src_ops := uop.__dict__.get("_src_ops")) is None: src_ops = uop.__dict__["_src_ops"] = {u.op for u in uop.src}
      for match, early_reject in pats:
        if not early_reject <= src_ops: continue
        if (ret := match(uop, ctx)) is not None and ret is not uop: return ret
    return None

# ---- graph_rewrite ----

_SENTINEL = object()

class RewriteContext:
  def __init__(self, pm: PatternMatcher | None, bpm: PatternMatcher | None, ctx=None):
    self.pm, self.bpm, self.ctx = pm, bpm, ctx
    self.bpm_cache: dict[UOp, UOp | None] = {}
    self.replace: dict[UOp, UOp] = {}

  def cached_bpm_rewrite(self, x: UOp) -> UOp | None:
    if (ret := self.bpm_cache.get(x, _SENTINEL)) is not _SENTINEL: return ret
    ret = self.bpm_cache[x] = self.bpm.rewrite(x, self.ctx)
    return ret

  def unified_rewrite(self, root: UOp, limit: int = 250000) -> UOp:
    # stage 0: bottom-up rewrite to a fixed point, then queue the sources. stage 1: once every source is rewritten,
    # rebuild the node or run the top-down rewrite. stage 2: link the rewritten replacement back to the original node.
    stack: collections.deque[tuple[UOp, int, UOp]] = collections.deque([(root, 0, root)])
    on_stack = {root}
    waitlist: dict[UOp, list[tuple[UOp, int, UOp]]] = {}
    while stack:
      if len(stack) > limit: raise RuntimeError("infinite loop in graph_rewrite (stack too big)")
      n, stage, new_n = stack.pop()
      if n in self.replace: continue
      if stage == 0:
        if self.bpm is not None:
          test_n, seen = n, set()
          while test_n is not None:
            if test_n in seen: raise RuntimeError("infinite loop in fixed_point_rewrite")
            seen.add(test_n)
            new_n, test_n = test_n, self.cached_bpm_rewrite(test_n)
        stack.append((n, 1, new_n))
        for x in reversed(new_n.src):
          if x in on_stack: continue
          stack.append((x, 0, x))
          on_stack.add(x)
      elif stage == 1:
        tmp = []
        for x in new_n.src:
          if (rx := self.replace.get(x, _SENTINEL)) is _SENTINEL:
            waitlist.setdefault(x, []).append((n, 1, new_n))
            break
          tmp.append(rx)
        else:
          if (new_src := tuple(tmp)) == new_n.src:
            if self.pm is None or (new_src_n := self.pm.rewrite(new_n, self.ctx)) is None:
              self.replace[n] = new_n
              if n in waitlist: stack.extend(waitlist.pop(n))
              continue
          else: new_src_n = UOp(new_n.op, new_n.dtype, new_src, new_n.arg)
          stack.append((n, 2, new_src_n))
          stack.append((new_src_n, 0, new_src_n))
      else:
        if (replaced := self.replace.get(new_n, _SENTINEL)) is _SENTINEL: waitlist.setdefault(new_n, []).append((n, 2, new_n))
        else:
          self.replace[n] = replaced
          if n in waitlist: stack.extend(waitlist.pop(n))
    if root not in self.replace: raise RuntimeError("graph_rewrite stalled: a replacement depends on the node being rewritten")
    return self.replace[root]

def graph_rewrite(sink: UOp, pm: PatternMatcher, ctx=None, bottom_up: bool = False, bpm: PatternMatcher | None = None) -> UOp:
  """Rewrite every UOp under sink with pm until nothing matches. Top-down by default (sources first, then the node);
  bottom_up=True rewrites a node before its sources. bpm adds a bottom-up matcher alongside a top-down pm."""
  return RewriteContext(None if bottom_up else pm, pm if bottom_up else bpm, ctx).unified_rewrite(sink)

def substitute(root: UOp, mapping: dict[UOp, UOp]) -> UOp:
  return graph_rewrite(root, PatternMatcher([(UPat(tuple(Ops), name="x"), lambda ctx, x: ctx.get(x))]), ctx=mapping)
