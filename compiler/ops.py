from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Any, Sequence
import hw
from .uop import DType, Fidelity, GroupOp, Ops, PatternMatcher, Space, UOp, UPat, default_fidelity, dtypes, graph_rewrite

# ---- typed UOp.arg specs (all frozen & hashable; UOp dependencies always live in UOp.src) ----

@dataclass(frozen=True)
class Grid:
  """Worker grid, column-major (10 rows per column on Blackhole, matching device.py and ttrv)."""
  cores: int
  rows: int = 10

  def __post_init__(self):
    if self.cores < 1 or self.rows < 1: raise ValueError(f"invalid grid: cores={self.cores}, rows={self.rows}")

  @property
  def cols(self) -> int: return math.ceil(self.cores / self.rows)

  @classmethod
  def p100a(cls) -> Grid: return cls(119)
  @classmethod
  def p150(cls) -> Grid:  return cls(139)
  @classmethod
  def from_device(cls, dev) -> Grid: return cls(dev.num_workers)


@dataclass(frozen=True)
class KernelArg:
  name: str
  grid: Grid


@dataclass(frozen=True)
class BufferArg:
  name: str
  space: Space
  shape: tuple[int, ...]
  dtype: DType
  addr: int | None = None
  tiles_per_page: int = 1


@dataclass(frozen=True)
class AllocArg:
  name: str
  space: Space
  shape: tuple[int, ...]
  dtype: DType


@dataclass(frozen=True)
class RangeArg:
  axis: int
  name: str = ""


@dataclass(frozen=True)
class ReduceArg:
  op: Ops
  space: Space


@dataclass(frozen=True)
class BarrierArg:
  scope: str | tuple[tuple[int, int], tuple[int, int]] = "all"
  tag: int = 0


@dataclass(frozen=True)
class NocHint:
  depth: int = 2
  stages: int = 1
  cap: int = 0
  port: int | None = None


@dataclass(frozen=True)
class NocArg:
  tiles: int = 1
  nbytes: int | None = None
  hint: NocHint = NocHint()


@dataclass(frozen=True)
class McastArg:
  rect: str | tuple[tuple[int, int], tuple[int, int]]
  include_self: bool = True
  hint: NocHint = NocHint()


@dataclass(frozen=True)
class CollectiveArg:
  group: str | tuple[int, ...]
  count: int = 1
  hint: NocHint = NocHint()


@dataclass(frozen=True)
class UnpackArg:
  dest: Space
  shape: tuple[int, int] = (32, 32)
  transpose: bool = False
  allow_tf32: bool = False


@dataclass(frozen=True)
class MvmulArg:
  tile: tuple[int, int, int] = (32, 32, 32)
  fidelity: Fidelity = Fidelity.HIFI2


@dataclass(frozen=True)
class PackArg:
  shape: tuple[int, int] = (32, 32)
  l1_acc: bool = False


@dataclass(frozen=True)
class ReplayArg:
  insns: tuple[int, ...]
  dest: Space = Space.DST
  name: str = ""


@dataclass(frozen=True)
class MopArg:
  cfg: tuple[int, ...]
  dest: Space = Space.DST
  name: str = ""


# ---- 1. Grid, Specials, Control & Residency ----

def _i32(x: UOp | int) -> UOp:
  return x if isinstance(x, UOp) else UOp.const(dtypes.i32, int(x))


def special(name: str, bound: UOp | int) -> UOp:
  """Hardware coordinate axis with known upper bound (like tinygrad Ops.SPECIAL: core_id, core_x, core_y)."""
  return UOp(Ops.SPECIAL, dtypes.i32, (_i32(bound),), name)


def buffer(
  name: str,
  shape: tuple[int, ...] | int,
  dtype: DType | str,
  space: Space = Space.DRAM,
  addr: int | None = None,
  tiles_per_page: int = 1,
) -> UOp:
  if space not in (Space.DRAM, Space.HOST, Space.L1, Space.SCALAR):
    raise ValueError(f"invalid buffer space {space}")
  dt = dtypes.from_name(dtype)
  sh = (shape,) if isinstance(shape, int) else tuple(shape)
  return UOp(Ops.BUFFER, dt, (), BufferArg(name, space, sh, dt, addr, tiles_per_page))


def dram_buf(name: str, shape: tuple[int, ...] | int, dtype: DType | str, addr: int | None = None, tiles_per_page: int = 1) -> UOp:
  return buffer(name, shape, dtype, Space.DRAM, addr, tiles_per_page)


def host_buf(name: str, shape: tuple[int, ...] | int, dtype: DType | str = dtypes.u32, addr: int | None = None) -> UOp:
  return buffer(name, shape, dtype, Space.HOST, addr)


def l1_buf(name: str, shape: tuple[int, ...] | int, dtype: DType | str, addr: int | None = None) -> UOp:
  return buffer(name, shape, dtype, Space.L1, addr)


def from_device_buffer(name: str, buf) -> UOp:
  """Wrap a device.Buffer or device.HostStream as a Layer 1 BUFFER UOp."""
  if hasattr(buf, "data_addr") and hasattr(buf, "capacity"):  # device.HostStream
    return host_buf(name, (buf.capacity,), dtypes.u32, addr=buf.data_addr)
  space = Space.HOST if buf.host else Space.DRAM
  return buffer(name, buf.shape, buf.dtype, space=space, addr=buf.addr)


def alloc(name: str, space: Space, dtype: DType | str, shape: tuple[int, ...] | int = (32, 32)) -> UOp:
  if space not in (Space.DST, Space.L1, Space.SCALAR):
    raise ValueError(f"alloc space must be DST, L1, or SCALAR, got {space}")
  dt = dtypes.from_name(dtype)
  sh = (shape,) if isinstance(shape, int) else tuple(shape)
  return UOp(Ops.ALLOC, dt, (), AllocArg(name, space, sh, dt))


def range_uop(bound: UOp | int, axis: int = 0, name: str = "") -> UOp:
  return UOp(Ops.RANGE, dtypes.i32, (_i32(bound),), RangeArg(axis, name))


def end(effect: UOp, *ranges: UOp) -> UOp:
  if not ranges: raise ValueError("end() requires at least one RANGE")
  return UOp(Ops.END, dtypes.void, (effect, *ranges))


def if_uop(cond: UOp, body: UOp, else_body: UOp | None = None) -> UOp:
  if cond.dtype is not dtypes.bool: raise TypeError(f"if condition must be bool, got {cond.dtype}")
  if else_body is None:
    return UOp(Ops.IF, body.dtype, (cond, body))
  if body.dtype != else_body.dtype:
    raise TypeError(f"if/else dtype mismatch: {body.dtype} vs {else_body.dtype}")
  return UOp(Ops.IF, body.dtype, (cond, body, else_body))


def reduce(val: UOp, *ranges: UOp, op: Ops = Ops.ADD, space: Space | None = None) -> UOp:
  if not ranges: raise ValueError("reduce() requires at least one RANGE")
  if op not in (Ops.ADD, Ops.MUL, Ops.MAX, Ops.MIN):
    raise ValueError(f"unsupported reduce op {op}")
  sp = val.space if space is None else space
  if sp not in (Space.DST, Space.L1, Space.SCALAR):
    raise ValueError(f"reduce residency must be DST, L1, or SCALAR, got {sp}")
  return UOp(Ops.REDUCE, val.dtype, (val, *ranges), ReduceArg(op, sp))


def load(buf: UOp, offset: UOp | int | None = None, *, gate: UOp | None = None) -> UOp:
  if gate is not None:
    src = (buf, _i32(0 if offset is None else offset), gate)
  else:
    src = (buf,) if offset is None else (buf, _i32(offset))
  return UOp(Ops.LOAD, buf.dtype, src)


def store(buf: UOp, val: UOp, offset: UOp | int | None = None, *, gate: UOp | None = None) -> UOp:
  if gate is not None:
    src = (buf, _i32(0 if offset is None else offset), val, gate)
  else:
    src = (buf, val) if offset is None else (buf, _i32(offset), val)
  return UOp(Ops.STORE, dtypes.void, src)


def barrier(scope: str | tuple[tuple[int, int], tuple[int, int]] = "all", tag: int = 0) -> UOp:
  return UOp(Ops.BARRIER, dtypes.void, (), BarrierArg(scope, tag))


# ---- 2. NoC Movement ----

def noc_read(
  buf: UOp,
  offset: UOp | int,
  tiles: int = 1,
  nbytes: int | None = None,
  *,
  gate: UOp | None = None,
  depth: int = 2,
  stages: int = 1,
  cap: int = 0,
  port: int | None = None,
) -> UOp:
  src = (buf, _i32(offset)) if gate is None else (buf, _i32(offset), gate)
  return UOp(Ops.NOC_READ, buf.dtype, src, NocArg(tiles, nbytes, NocHint(depth, stages, cap, port)))


def noc_write(
  buf: UOp,
  offset: UOp | int,
  val: UOp,
  tiles: int = 1,
  nbytes: int | None = None,
  *,
  gate: UOp | None = None,
  depth: int = 2,
  stages: int = 1,
  cap: int = 0,
  port: int | None = None,
) -> UOp:
  src = (buf, _i32(offset), val) if gate is None else (buf, _i32(offset), val, gate)
  return UOp(Ops.NOC_WRITE, dtypes.void, src, NocArg(tiles, nbytes, NocHint(depth, stages, cap, port)))


def noc_mcast(
  val: UOp,
  rect: str | tuple[tuple[int, int], tuple[int, int]],
  sender: UOp | int,
  include_self: bool = True,
  *,
  depth: int = 2,
  stages: int = 1,
  cap: int = 0,
  port: int | None = None,
) -> UOp:
  return UOp(Ops.NOC_MCAST, val.dtype, (val, _i32(sender)), McastArg(rect, include_self, NocHint(depth, stages, cap, port)))


def noc_gather(
  val: UOp,
  group: str | tuple[int, ...],
  root: UOp | int,
  count: int = 1,
  *,
  depth: int = 2,
  stages: int = 1,
  cap: int = 0,
  port: int | None = None,
) -> UOp:
  return UOp(Ops.NOC_GATHER, val.dtype, (val, _i32(root)), CollectiveArg(group, count, NocHint(depth, stages, cap, port)))


def noc_allgather(
  val: UOp,
  group: str | tuple[int, ...],
  count: int = 1,
  *,
  depth: int = 2,
  stages: int = 1,
  cap: int = 0,
  port: int | None = None,
) -> UOp:
  return UOp(Ops.NOC_ALLGATHER, val.dtype, (val,), CollectiveArg(group, count, NocHint(depth, stages, cap, port)))


# ---- 3. Unpack ----

def unpack(
  l1_val: UOp,
  dest: Space = Space.DST,
  dtype: DType | str | None = None,
  shape: tuple[int, int] = (32, 32),
  transpose: bool = False,
  allow_tf32: bool = False,
) -> UOp:
  if dest not in (Space.SRCA, Space.SRCB, Space.DST):
    raise ValueError(f"unpack dest must be SRCA, SRCB, or DST, got {dest}")
  dt = (dtypes.fp32 if dest is Space.DST else l1_val.dtype) if dtype is None else dtypes.from_name(dtype)
  return UOp(Ops.UNPACK, dt, (l1_val,), UnpackArg(dest, shape, transpose, allow_tf32))


# ---- 4. FPU Contraction (elementwise FPU ops use +, -, *, maximum on SRCA/SRCB directly) ----

def mvmul(
  srcb: UOp,
  srca: UOp,
  tile: tuple[int, int, int] = (32, 32, 32),
  fidelity: Fidelity | int | None = None,
  dtype: DType | str = dtypes.fp32,
) -> UOp:
  f = default_fidelity(srcb.dtype, srca.dtype) if fidelity is None else Fidelity(fidelity)
  return UOp(Ops.MVMUL, dtypes.from_name(dtype), (srcb, srca), MvmulArg(tile, f))


# ---- 5. SFPU lane primitives ----

def lane_id(dtype: DType | str = dtypes.i32) -> UOp:
  return UOp(Ops.LANE_ID, dtypes.from_name(dtype), ())


def reduce_row(x: UOp, op: Ops = Ops.ADD) -> UOp: return x.reduce_row(op)
def argmax(x: UOp) -> UOp: return x.argmax()


# ---- 6. Pack ----

def pack(
  dst_val: UOp,
  dtype: DType | str = dtypes.bf16,
  shape: tuple[int, int] = (32, 32),
  l1_acc: bool = False,
) -> UOp:
  return UOp(Ops.PACK, dtypes.from_name(dtype), (dst_val,), PackArg(shape, l1_acc))


# ---- Escape Hatch: Explicit REPLAY / MOP ----

def replay(
  insns: Sequence[int],
  *deps: UOp,
  dtype: DType | str = dtypes.fp32,
  dest: Space = Space.DST,
  name: str = "",
) -> UOp:
  """Explicit Tensix REPLAY block carrying ordered raw instruction words in arg and live dataflow edges in src."""
  return UOp(Ops.REPLAY, dtypes.from_name(dtype), deps, ReplayArg(tuple(int(w) for w in insns), dest, name))


def mop(
  cfg: Sequence[int],
  *deps: UOp,
  dtype: DType | str = dtypes.fp32,
  dest: Space = Space.DST,
  name: str = "",
) -> UOp:
  """Explicit Tensix MOP config (9 words) carrying live dataflow edges in src."""
  return UOp(Ops.MOP, dtypes.from_name(dtype), deps, MopArg(tuple(int(w) for w in cfg), dest, name))


# ---- Kernel builder ----

class Kernel:
  """Lightweight Layer 1 builder; exposes core_id / core_x / core_y as bounded Ops.SPECIAL nodes."""
  def __init__(self, name: str = "kernel", grid: Grid | int | None = None):
    self.name = name
    self.grid = Grid(grid) if isinstance(grid, int) else (grid or Grid.p100a())
    self.core_id = special("core_id", self.grid.cores)
    self.core_x  = special("core_x",  self.grid.cols)
    self.core_y  = special("core_y",  self.grid.rows)
    self._next_axis = 0
    self.effects: list[UOp] = []

  def range(self, bound: UOp | int, name: str = "") -> UOp:
    axis = self._next_axis
    self._next_axis += 1
    return range_uop(bound, axis=axis, name=name)

  def emit(self, *effects: UOp):
    self.effects.extend(effects)

  def build(self, *, do_simplify: bool = True, do_verify: bool = True) -> UOp:
    sink = UOp.sink(*self.effects, arg=KernelArg(self.name, self.grid))
    if do_simplify: sink = simplify(sink)
    if do_verify: verify(sink)
    return sink


# ---- Minimal algebraic simplification & constant folding ----

def _eval_const_unary(op: Ops, dt: DType, a: Any) -> UOp | None:
  if op is Ops.NEG:   return UOp.const(dt, -a)
  if op is Ops.ABS:   return UOp.const(dt, abs(a))
  if op is Ops.NOT:   return UOp.const(dt, (not a) if dt is dtypes.bool else ~a)
  if op is Ops.EXP2:  return UOp.const(dt, math.exp2(a))
  if op is Ops.LOG2 and a > 0:  return UOp.const(dt, math.log2(a))
  if op is Ops.SIN:   return UOp.const(dt, math.sin(a))
  if op is Ops.SQRT and a >= 0: return UOp.const(dt, math.sqrt(a))
  if op is Ops.RSQRT and a > 0: return UOp.const(dt, 1.0 / math.sqrt(a))
  if op is Ops.RECIP and a != 0: return UOp.const(dt, 1.0 / a)
  return None


def _eval_const_binary(op: Ops, dt: DType, a: Any, b: Any) -> UOp | None:
  if op is Ops.ADD:   return UOp.const(dt, a + b)
  if op is Ops.SUB:   return UOp.const(dt, a - b)
  if op is Ops.MUL:   return UOp.const(dt, a * b)
  if op is Ops.DIV:
    if b == 0: return None
    return UOp.const(dt, a / b if dt.is_float else a // b)
  if op is Ops.MOD:
    if b == 0: return None
    return UOp.const(dt, a % b)
  if op is Ops.MAX:   return UOp.const(dt, max(a, b))
  if op is Ops.MIN:   return UOp.const(dt, min(a, b))
  if op is Ops.CMPLT: return UOp.const(dtypes.bool, a < b)
  if op is Ops.CMPEQ: return UOp.const(dtypes.bool, a == b)
  if op is Ops.CMPNE: return UOp.const(dtypes.bool, a != b)
  if op is Ops.AND:   return UOp.const(dt, (a and b) if dt is dtypes.bool else (a & b))
  if op is Ops.OR:    return UOp.const(dt, (a or b) if dt is dtypes.bool else (a | b))
  if op is Ops.XOR:   return UOp.const(dt, (a != b) if dt is dtypes.bool else (a ^ b))
  if op is Ops.SHL:   return UOp.const(dt, a << b)
  if op is Ops.SHR:   return UOp.const(dt, a >> b)
  return None


pm_simplify = PatternMatcher([
  # constant folding
  (UPat(GroupOp.Unary, src=(UPat.const("a"),), name="u"), lambda u, a: _eval_const_unary(u.op, u.dtype, a.arg)),
  (UPat(GroupOp.Binary, src=(UPat.const("a"), UPat.const("b")), name="u"), lambda u, a, b: _eval_const_binary(u.op, u.dtype, a.arg, b.arg)),
  (UPat(Ops.CAST, src=(UPat.const("a"),), name="u"), lambda u, a: UOp.const(u.dtype, a.arg) if u.dtype != dtypes.void else None),
  (UPat(Ops.CAST, src=(UPat.var("x"),), name="u"), lambda u, x: x if u.dtype == x.dtype else None),

  # basic identities (float x * 0.0 is NOT folded because of NaN/Inf)
  (UPat(Ops.ADD, src=[UPat.var("x"), UPat.const(arg=0)]), lambda x: x),
  (UPat(Ops.ADD, src=[UPat.var("x"), UPat.const(arg=0.0)]), lambda x: x),
  (UPat(Ops.SUB, src=(UPat.var("x"), UPat.const(arg=0))), lambda x: x),
  (UPat(Ops.SUB, src=(UPat.var("x"), UPat.const(arg=0.0))), lambda x: x),
  (UPat(Ops.SUB, src=(UPat.var("x"), UPat.var("x"))), lambda x: UOp.const(x.dtype, 0) if x.dtype.is_int else None),
  (UPat(Ops.MUL, src=[UPat.var("x"), UPat.const(arg=1)]), lambda x: x),
  (UPat(Ops.MUL, src=[UPat.var("x"), UPat.const(arg=1.0)]), lambda x: x),
  (UPat(Ops.MUL, src=[UPat.var("x"), UPat.const(arg=0)]), lambda x: UOp.const(x.dtype, 0) if x.dtype.is_int else None),
  (UPat(Ops.DIV, src=(UPat.var("x"), UPat.const(arg=1))), lambda x: x),
  (UPat(Ops.DIV, src=(UPat.var("x"), UPat.const(arg=1.0))), lambda x: x),
  (UPat(Ops.MOD, src=(UPat.var("x"), UPat.const(arg=1))), lambda x: UOp.const(x.dtype, 0) if x.dtype.is_int else None),
  (UPat(Ops.NEG, src=(UPat(Ops.NEG, src=(UPat.var("x"),)),)), lambda x: x),
  (UPat(Ops.NOT, src=(UPat(Ops.NOT, src=(UPat.var("x"),)),)), lambda x: x),
  (UPat(Ops.CMPLT, src=(UPat.var("x"), UPat.var("x"))), lambda x: UOp.const(dtypes.bool, False) if x.dtype.is_int else None),

  # where / if folding
  (UPat(Ops.WHERE, src=(UPat.const(arg=True), UPat.var("a"), UPat.var())), lambda a: a),
  (UPat(Ops.WHERE, src=(UPat.const(arg=False), UPat.var(), UPat.var("b"))), lambda b: b),
  (UPat(Ops.WHERE, src=(UPat.var(), UPat.var("a"), UPat.var("a"))), lambda a: a),
  (UPat(Ops.IF, src=(UPat.const(arg=True), UPat.var("body"))), lambda body: body),
  (UPat(Ops.IF, src=(UPat.const(arg=True), UPat.var("body"), UPat.var())), lambda body: body),
  (UPat(Ops.IF, src=(UPat.const(arg=False), UPat.var(), UPat.var("else_body"))), lambda else_body: else_body),
])


def simplify(root: UOp) -> UOp:
  return graph_rewrite(root, pm_simplify)


# ---- Analysis helpers ----

def open_ranges(root: UOp) -> dict[UOp, frozenset[UOp]]:
  """Compute the set of active RANGE nodes at every UOp reachable from root."""
  active: dict[UOp, frozenset[UOp]] = {}
  for u in root.toposort():
    if u.op is Ops.RANGE:
      active[u] = frozenset({u}) | active[u.src[0]]
    elif u.op in (Ops.END, Ops.REDUCE):
      closed = frozenset(u.src[1:])
      active[u] = (active[u.src[0]] - closed) | frozenset().union(*(active[r.src[0]] for r in u.src[1:] if r.op is Ops.RANGE))
    else:
      active[u] = frozenset().union(*(active[s] for s in u.src)) if u.src else frozenset()
  return active


def special_axes(root: UOp) -> set[str]:
  """Return the set of Ops.SPECIAL names (e.g. 'core_id', 'core_x', 'core_y') that root depends on."""
  return {u.arg for u in root.toposort() if u.op is Ops.SPECIAL}


# ---- Hardware invariant verifier ----

class VerifyError(ValueError):
  pass


_FPU_ELW_OPS = frozenset({Ops.ADD, Ops.SUB, Ops.MUL, Ops.MAX})


def _check_gate(gate: UOp, op_name: str):
  if gate.dtype is not dtypes.bool or gate.space is not Space.SCALAR:
    raise VerifyError(f"{op_name} gate must be scalar bool, got ({gate.space}, {gate.dtype})")


def verify(root: UOp) -> None:
  """Validate Layer 1 structural, dtype, memory-space, Blackhole hardware, and RANGE-scoping invariants."""
  nodes = root.toposort()
  active = open_ranges(root)

  for u in nodes:
    op, src, arg = u.op, u.src, u.arg

    if op is Ops.SINK:
      if active[u]:
        names = [r.arg.name or f"axis{r.arg.axis}" for r in active[u]]
        raise VerifyError(f"unclosed RANGE(s) leaked into SINK: {names}")

    elif op in (Ops.RANGE, Ops.SPECIAL):
      if len(src) != 1 or src[0].space is not Space.SCALAR or not src[0].dtype.is_int:
        raise VerifyError(f"{op.name} bound must be scalar int, got {src}")

    elif op in (Ops.END, Ops.REDUCE):
      if len(src) < 2: raise VerifyError(f"{op.name} requires a value/effect and at least one RANGE")
      for r in src[1:]:
        if r.op is not Ops.RANGE:
          raise VerifyError(f"{op.name} axis argument must be RANGE, got {r.op.name}")
      if op is Ops.REDUCE:
        if not isinstance(arg, ReduceArg): raise VerifyError("REDUCE arg must be ReduceArg")
        if arg.space is Space.L1 and src[0].op is Ops.PACK and not src[0].arg.l1_acc:
          raise VerifyError("L1 REDUCE over PACK requires pack(..., l1_acc=True)")

    elif op is Ops.IF:
      if len(src) not in (2, 3): raise VerifyError(f"IF expects 2 or 3 srcs, got {len(src)}")
      _check_gate(src[0], "IF")

    elif op is Ops.NOC_READ:
      if len(src) not in (2, 3): raise VerifyError("NOC_READ expects (buf, offset[, gate])")
      if src[0].op not in (Ops.BUFFER, Ops.ALLOC) or src[0].space not in (Space.DRAM, Space.HOST, Space.L1):
        raise VerifyError(f"NOC_READ source must be DRAM/HOST/L1 buffer, got {src[0].op.name} in {src[0].space}")
      if src[1].space is not Space.SCALAR or not src[1].dtype.is_int:
        raise VerifyError(f"NOC_READ offset must be scalar int, got ({src[1].space}, {src[1].dtype})")
      if len(src) == 3: _check_gate(src[2], "NOC_READ")

    elif op is Ops.NOC_WRITE:
      if len(src) not in (3, 4): raise VerifyError("NOC_WRITE expects (buf, offset, val[, gate])")
      if src[0].op not in (Ops.BUFFER, Ops.ALLOC) or src[0].space not in (Space.DRAM, Space.HOST, Space.L1):
        raise VerifyError(f"NOC_WRITE dest must be DRAM/HOST/L1 buffer, got {src[0].op.name} in {src[0].space}")
      if src[1].space is not Space.SCALAR or not src[1].dtype.is_int:
        raise VerifyError(f"NOC_WRITE offset must be scalar int, got ({src[1].space}, {src[1].dtype})")
      if src[2].space not in (Space.L1, Space.SCALAR):
        raise VerifyError(f"NOC_WRITE value must be in L1 or SCALAR, got {src[2].space}")
      if len(src) == 4: _check_gate(src[3], "NOC_WRITE")

    elif op is Ops.NOC_MCAST:
      if len(src) != 2: raise VerifyError("NOC_MCAST expects (val, sender)")
      if src[0].space is not Space.L1:
        raise VerifyError(f"NOC_MCAST value must be in L1, got {src[0].space}")
      if src[1].space is not Space.SCALAR or not (src[1].dtype.is_int or src[1].dtype is dtypes.bool):
        raise VerifyError(f"NOC_MCAST sender must be scalar int/bool, got ({src[1].space}, {src[1].dtype})")

    elif op in (Ops.NOC_GATHER, Ops.NOC_ALLGATHER):
      if src[0].space is not Space.L1:
        raise VerifyError(f"{op.name} value must be in L1, got {src[0].space}")

    elif op is Ops.UNPACK:
      if len(src) != 1 or src[0].space is not Space.L1:
        raise VerifyError(f"UNPACK source must be in L1, got {src[0].space if src else None}")
      if arg.dest not in (Space.SRCA, Space.SRCB, Space.DST):
        raise VerifyError(f"UNPACK dest must be SRCA, SRCB, or DST, got {arg.dest}")
      if src[0].dtype is dtypes.fp32 and arg.dest in (Space.SRCA, Space.SRCB) and not arg.allow_tf32:
        raise VerifyError("UNPACK fp32 -> SrcA/SrcB truncates to 19-bit TF32; unpack to Space.DST or set allow_tf32=True")

    elif op is Ops.MVMUL:
      if len(src) != 2: raise VerifyError("MVMUL expects (srcb, srca)")
      if src[0].space is not Space.SRCB or src[1].space is not Space.SRCA:
        raise VerifyError(f"MVMUL expects (SRCB, SRCA), got ({src[0].space}, {src[1].space})")

    elif op is Ops.PACK:
      if len(src) != 1 or src[0].space is not Space.DST:
        raise VerifyError(f"PACK source must be in DST, got {src[0].space if src else None}")

    elif op is Ops.REPLAY:
      if not (1 <= len(arg.insns) <= 32):
        raise VerifyError(f"REPLAY holds 1..32 Tensix instructions, got {len(arg.insns)}")

    elif op is Ops.MOP:
      if len(arg.cfg) != hw.MOP_CFG_WORDS:
        raise VerifyError(f"MOP config requires {hw.MOP_CFG_WORDS} words, got {len(arg.cfg)}")

    elif op in (Ops.REDUCE_ROW, Ops.ARGMAX):
      if len(src) != 1 or src[0].space is not Space.DST:
        raise VerifyError(f"{op.name} operand must be in DST, got {src[0].space if src else None}")

    elif op is Ops.SFPU:
      for s in src:
        if s.space not in (Space.DST, Space.SCALAR):
          raise VerifyError(f"SFPU primitive operand must be in DST/SCALAR, got {s.space}")

    elif op in GroupOp.ALU or op in (Ops.CAST, Ops.BITCAST):
      uses_src_bank = any(s.space in (Space.SRCA, Space.SRCB) for s in src)
      for s in src:
        if s.space not in (Space.DST, Space.SRCA, Space.SRCB, Space.SCALAR):
          raise VerifyError(f"{op.name} operand must be in DST/SRCA/SRCB/SCALAR, got {s.space} (missing unpack()?)")
      if uses_src_bank and op not in _FPU_ELW_OPS:
        raise VerifyError(f"SRCA/SRCB operands only support FPU elementwise {_FPU_ELW_OPS}, got {op.name}")
      if op is Ops.WHERE and src[0].dtype is not dtypes.bool:
        raise VerifyError(f"WHERE condition must be bool, got {src[0].dtype}")

    elif op is Ops.LOAD:
      if len(src) not in (1, 2, 3) or src[0].op not in (Ops.BUFFER, Ops.ALLOC):
        raise VerifyError(f"LOAD target must be BUFFER or ALLOC, got {src}")
      if len(src) >= 2 and (src[1].space is not Space.SCALAR or not src[1].dtype.is_int):
        raise VerifyError(f"LOAD offset must be scalar int, got ({src[1].space}, {src[1].dtype})")
      if len(src) == 3: _check_gate(src[2], "LOAD")

    elif op is Ops.STORE:
      if len(src) not in (2, 3, 4) or src[0].op not in (Ops.BUFFER, Ops.ALLOC):
        raise VerifyError(f"STORE target must be BUFFER or ALLOC, got {src}")
      val = src[1] if len(src) == 2 else src[2]
      if len(src) >= 3 and (src[1].space is not Space.SCALAR or not src[1].dtype.is_int):
        raise VerifyError(f"STORE offset must be scalar int, got ({src[1].space}, {src[1].dtype})")
      if len(src) == 4: _check_gate(src[3], "STORE")
      if src[0].space in (Space.DST, Space.L1, Space.SCALAR) and val.space is not src[0].space:
        raise VerifyError(f"STORE into {src[0].space} requires value in {src[0].space}, got {val.space}")
