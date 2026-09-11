"""Ordered register programs for one core. Tracing only; no lowering.

Register free() is an optional checked lifetime assertion; temporaries need no
manual frees. Dst allocation and CB item release remain explicit. Views are register-relative: bytes for L1,
128-element blocks for Src/Dst. SFPU accesses name a physical position within
one Dst block, never a fictitious contiguous 32-element vector.

cb.read declares a finite DRAM source, item size and capacity in items. Each
next() records one acquisition in program order and returns an L1 allocation.
That order defines the future NoC producer sequence, including enclosing loops.
Read completion before publication and readiness before use are implicit.
free() releases an item after its readers finish; it is not a read barrier.
Producer and consumer threads may advance independently subject to CB capacity.
noc.read(..., resident=True) fetches DRAM into resident L1 storage.

GPR and LREG values are SSA: every definition is fresh. Loops explicitly
connect initial values, body arguments, yields and results. Src/Dst/L1 remain
mutable storage with range effects. Predicated value operations optionally
read a previous value for inactive lanes; they never redefine that value. Hardware synchronization, allocation and encoding are future
passes; trace validation does not prove asynchronous progress or completion.
Named kernel.param values are invocation constants, visible to every thread
that consumes them; no public RISC-V load is needed for launch arguments.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from typing import Literal, NoReturn, ParamSpec, overload

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from enum import Enum, auto
import struct
from math import factorial
import traceback


class Dtype(Enum):
  bf16 = 'bf16'
  f32 = 'f32'
  i32 = 'i32'
  u32 = 'u32'





class RegClass(Enum):
  GPR = auto(); LREG = auto(); SRCA = auto(); SRCB = auto(); DST = auto(); L1 = auto()


class Thread(Enum):
  BRISC = auto(); NCRISC = auto(); UNPACK = auto(); MATH = auto(); PACK = auto()


# Public operand categories. Register class checks refine VReg at trace time:
# GPR offsets, L1 byte ranges, Src/Dst blocks, and 32-lane LREG values.
type Offset = int | VReg | AffineIndex
type RegisterView = VReg | View
type SFPUValue = Vec | int | float
type Operand = AffineIndex | VReg | View | LaneView | BufferRange | StreamRange | int | float
type Item = Inst | Loop | DstScope
P = ParamSpec('P')


# ---------------------------------------------------------------- nodes

@dataclass(eq=False)
class VReg:
  """Virtual register allocation; cls identifies the physical storage family.

  extent is bytes for L1, 128-element blocks for Src/Dst, and one for GPR/LREG.
  Indexing creates an aliasing view, never a copy. free() is an optional checked
  end-of-lifetime assertion except for CB items, whose release returns capacity.
  """
  cls: RegClass
  dtype: Dtype
  extent: int = 1                      # blocks of 128 elements for SRC/DST; 1 for LREG/GPR
  name: str | None = None
  id: int = field(default=-1)
  alignment: int = 1                   # native allocation units, not bytes

  def __repr__(self) -> str: return self.name or f'%{self.id}:{self.cls.name.lower()}'

  def __bool__(self) -> NoReturn: raise TypeError('symbolic values cannot control Python branches')
  def free(self) -> None: _trace().release(self)
  def release(self) -> None:
    """Return an acquired CB item to its stream; unlike register free, not a hint."""
    if self not in _trace().items: raise TypeError('release requires a CB item')
    _trace().release(self)
  def __getitem__(self, key: Offset | slice) -> View: return View(self, 0, self.extent)[key]
  def blocks(self, *, offset: int = 0, count: int) -> View:
    """Select a Src/Dst range measured in 128-element blocks; no data movement."""
    return View(self, 0, self.extent).blocks(offset=offset, count=count)

  def _binary(self, op: str, other: Offset) -> VReg:
    other = _materialize(other)
    if not (type(other) is int or isinstance(other, VReg) and other.cls is RegClass.GPR):
      raise TypeError('offset operand must be an integer or GPR')
    if self.cls is not RegClass.GPR: raise TypeError('offset arithmetic requires GPRs')
    return _trace().record('gpr.' + op, (self, other), cls=RegClass.GPR, dtype=self.dtype)
  def __add__(self, other: Offset) -> Offset:
    _trace().check((self,))
    if self in _trace().induction and type(other) is int: return AffineIndex(self, other)
    return self._binary('add', other)
  def __radd__(self, other: int) -> Offset: return self + other
  def __sub__(self, other: int) -> Offset:
    if type(other) is not int: raise TypeError('index subtraction requires an integer')
    return self + (-other)
  def __mul__(self, other: Offset) -> VReg: return self._binary('mul', other)
  def __floordiv__(self, other: Offset) -> VReg: return self._binary('div', other)
  def __mod__(self, other: Offset) -> VReg: return self._binary('mod', other)



@dataclass(frozen=True)
class AffineIndex:
  """A loop induction variable plus a constant; no GPR add is emitted.

  Dst views retain this expression for counter/immediate lowering. Other scalar
  consumers materialize it only when actual GPR arithmetic is needed.
  """
  index: VReg
  constant: int = 0

  def __repr__(self) -> str:
    if self.constant == 0: return repr(self.index)
    return f'{self.index!r} {"+" if self.constant >= 0 else "-"} {abs(self.constant)}'

  def __bool__(self) -> NoReturn: raise TypeError('symbolic indices cannot control Python branches')
  def __add__(self, other: Offset) -> Offset:
    _trace().check((self,))
    if type(other) is int: return AffineIndex(self.index, self.constant + other)
    return _materialize(self)._binary('add', other)
  def __radd__(self, other: int) -> Offset: return self + other
  def __sub__(self, other: int) -> Offset:
    if type(other) is not int: raise TypeError('index subtraction requires an integer')
    return self + (-other)
  def __mul__(self, other: Offset) -> VReg: return _materialize(self)._binary('mul', other)
  def __floordiv__(self, other: Offset) -> VReg: return _materialize(self)._binary('div', other)
  def __mod__(self, other: Offset) -> VReg: return _materialize(self)._binary('mod', other)


def _materialize(value: Offset) -> int | VReg:
  if isinstance(value, AffineIndex):
    _trace().check((value,))
    if value.constant == 0: return value.index
    return _trace().record('gpr.add', (value.index, value.constant), cls=RegClass.GPR, dtype=value.index.dtype)
  return value


def _dst_index(value: Offset) -> None:
  """Reject Dst addressing that cannot name one induction counter plus an immediate."""
  _trace().check((value,))
  if type(value) is int: return
  base = value.index if isinstance(value, AffineIndex) else value
  if not isinstance(base, VReg) or base not in _trace().induction:
    raise ValueError('Dst index must be a loop induction variable plus an integer constant')
  if isinstance(value, AffineIndex) and type(value.constant) is not int:
    raise TypeError('Dst index offset must be an integer constant')


@dataclass(frozen=True)
class Access:
  """Data/state effect. Views retain their offsets and extent without flattening.

  mask describes physical participating lanes; None means all. A partial write
  does not kill the rest of the allocation in liveness analysis. Allocation is
  distinct from initialization. String targets name implicit engine state.
  """
  target: object
  mask: int | None = None
  partial: bool = False
  alignment: int = 1                   # required alignment of the accessed start


def _accesses(values: Iterable[object]) -> tuple[Access, ...]:
  return tuple(Access(v) for v in values if isinstance(v, (VReg, AffineIndex, View, LaneView, BufferRange, StreamRange)))


def _addresses(values: Iterable[object]) -> tuple[Access, ...]:
  result = []
  for value in values:
    if isinstance(value, LaneView):
      result.extend(_addresses((value.block,)))
      if isinstance(value.position, VReg): result.append(Access(value.position))
    elif isinstance(value, (View, BufferRange, StreamRange)) and isinstance(value.offset, (VReg, AffineIndex)):
      result.append(Access(value.offset.index if isinstance(value.offset, AffineIndex) else value.offset))
  return tuple(result)


@dataclass(eq=False)
class Inst:
  op: str
  ins: tuple[Operand, ...]
  outs: tuple[VReg, ...]
  attrs: dict[str, object] = field(default_factory=dict)
  site: str = ''
  reads: tuple[Access, ...] = ()                    # Access ranges, including address dependencies
  writes: tuple[Access, ...] = ()                   # Access ranges; partial writes preserve other lanes
  allocates: tuple[VReg, ...] = ()
  releases: tuple[VReg, ...] = ()


  def format(self, *, verbose: bool = False) -> str:
    """Compact instruction listing; verbose retains every recorded attribute."""
    lhs = ', '.join(map(repr, self.outs)) + ' = ' if self.outs else ''
    if verbose:
      attrs = ' '.join(f'{k}={v!r}' for k, v in self.attrs.items())
      return f'{lhs}{self.op}({", ".join(map(repr, self.ins))})' + (' ' + attrs if attrs else '')

    def display(value: object) -> str:
      if isinstance(value, Dtype): return value.value
      if isinstance(value, Buffer): return '@' + value.name
      return repr(value)

    visible = dict(self.attrs)
    for key, default in (('predicate', None), ('inactive', 'undefined'), ('mod', 0)):
      if key in visible and visible[key] == default: del visible[key]
    if any(isinstance(value, LaneView) for value in self.ins): visible.pop('position', None)
    implicit_completion = {'noc.read': 'before_use', 'cb.next': 'before_use', 'noc.write': 'before_release'}
    if self.op in implicit_completion and visible.get('completion') == implicit_completion[self.op]:
      visible.pop('completion')
    if self.op == 'cb.next' and visible.get('release') == 'cb.release': visible.pop('release')
    if self.op == 'kernel.param': visible.pop('name', None)  # already named on the left
    op, operands = self.op, ', '.join(map(repr, self.ins))
    if op == 'sfp.const':
      if visible.get('literal') == 'bits':
        op, operands = 'sfp.const_bits', f'0x{visible["bits"]:08x}'
      visible.pop('bits', None)
      visible.pop('literal', None)
    if op == 'sfp.predicate':
      mask = visible.pop('mask')
      operands = 'all' if mask is None else f'0x{mask:08x}'
    if op in ('dst.alloc', 'src.alloc', 'l1.alloc') and self.outs:
      reg = self.outs[0]
      operands = f'{"nbytes" if reg.cls is RegClass.L1 else "blocks"}={reg.extent}, dtype={reg.dtype.value}'
    attrs = ' '.join(f'{key}={f"0x{value:08x}" if key == "predicate" else display(value)}'
                     for key, value in visible.items())
    return f'{lhs}{op}({operands})' + (' ' + attrs if attrs else '')

  def __repr__(self) -> str:
    return self.format()


@dataclass(eq=False)
class Loop:
  count: int | VReg
  index: VReg
  body: list[Item] = field(default_factory=list)
  initial: tuple[VReg, ...] = ()
  arguments: tuple[VReg, ...] = ()
  yields: tuple[VReg, ...] = ()
  results: tuple[VReg, ...] = ()


@dataclass(eq=False)
class DstScope:
  value: VReg
  body: list[Item] = field(default_factory=list)


@dataclass(frozen=True)
class RuntimeParam:
  """Named integer supplied once per invocation, available to every consuming thread.

  value is symbolic during tracing. Future lowering materializes it wherever
  needed; it is not a DRAM read owned by one thread. Runtime values do not
  participate in the trace/compile cache key.
  """
  name: str
  dtype: Dtype
  value: VReg


@dataclass(eq=False)
class Kernel:
  name: str
  buffers: tuple[object, ...]
  body: list[Item]
  params: tuple[RuntimeParam, ...] = ()

  def dump(self, *, effects: bool = False) -> str:
    lines = []
    def walk(items, depth):
      pad = '  ' * depth
      for item in items:
        if isinstance(item, Inst):
          lines.append(pad + item.format(verbose=effects))
          if effects:
            lines.append(pad + f'  # reads={item.reads!r} writes={item.writes!r} allocates={item.allocates!r} releases={item.releases!r}')
        elif isinstance(item, Loop):
          carrying = ' carrying ' + ', '.join(f'{arg!r} = {init!r}' for arg, init in zip(item.arguments, item.initial)) if item.initial else ''
          results = ', '.join(map(repr, item.results)) + ' = ' if item.results else ''
          lines.append(f'{pad}{results}loop {item.index!r} in range({item.count!r}){carrying}:')
          walk(item.body, depth + 1)
        elif isinstance(item, DstScope):
          lines.append(f'{pad}dst {item.value!r} [{item.value.extent} blocks]:'); walk(item.body, depth + 1)
    walk(self.body, 0)
    return '\n'.join(lines)

  def verify(self) -> None:
    """Check SSA uniqueness, dominance, loop edges and immutable scalar writes.

    Storage effects remain mutable. This does not verify hardware schedules,
    numeric initialization, physical addressing legality or CB progress.
    """
    defined: set[VReg] = set()

    def dependencies(value: object) -> set[VReg]:
      if isinstance(value, VReg): return {value}
      if isinstance(value, AffineIndex): return {value.index}
      if isinstance(value, View): return {value.reg} | dependencies(value.offset)
      if isinstance(value, LaneView): return dependencies(value.block) | dependencies(value.position)
      if isinstance(value, (BufferRange, StreamRange)): return dependencies(value.offset)
      return set()

    def require(values: Iterable[object], available: set[VReg]) -> None:
      for value in values:
        for reg in dependencies(value):
          if reg not in available: raise ValueError(f'SSA value does not dominate use: {reg!r}')

    def define(values: tuple[VReg, ...], available: set[VReg]) -> None:
      for reg in values:
        if reg in defined: raise ValueError(f'SSA value defined more than once: {reg!r}')
        defined.add(reg)
        available.add(reg)

    def walk(items: list[Item], incoming: set[VReg]) -> set[VReg]:
      available = set(incoming)
      for index, item in enumerate(items):
        if isinstance(item, Inst):
          require(item.ins, available)
          require((a.target for a in item.reads), available)
          require(item.releases, available)
          for effect in item.writes:
            target = effect.target
            if isinstance(target, VReg) and target.cls in (RegClass.GPR, RegClass.LREG):
              if target not in item.outs: raise ValueError('SSA scalar writes must define an output')
              if effect.partial: raise ValueError('SSA scalar definitions cannot be partial storage writes')
            elif target not in item.outs:
              require((target,), available)
          define(item.outs, available)
          available.difference_update(item.releases)
          if item.op == 'loop.yield' and index != len(items) - 1:
            raise ValueError('loop yield must terminate its body')
        elif isinstance(item, Loop):
          require((item.count, *item.initial), available)
          if not len(item.initial) == len(item.arguments) == len(item.yields) == len(item.results):
            raise ValueError('loop carry arity mismatch')
          for values in zip(item.initial, item.arguments, item.yields, item.results):
            if any(v.cls not in (RegClass.GPR, RegClass.LREG) for v in values):
              raise TypeError('loop carry cannot contain storage')
            if len({(v.cls, v.dtype) for v in values}) != 1: raise TypeError('loop carry type mismatch')
          inside = set(available)
          define((item.index, *item.arguments), inside)
          inside = walk(item.body, inside)
          require(item.yields, inside)
          if item.initial:
            if not item.body or not isinstance(item.body[-1], Inst) or item.body[-1].op != 'loop.yield':
              raise ValueError('missing loop yield terminator')
            if item.body[-1].ins != item.yields: raise ValueError('loop yield edge mismatch')
          define(item.results, available)
        else:
          inside = set(available)
          define((item.value,), inside)
          walk(item.body, inside)
      return available

    walk(self.body, set())

  def insts(self) -> list[Inst]:
    def walk(items):
      for item in items:
        if isinstance(item, Inst): yield item
        else: yield from walk(item.body)
    return list(walk(self.body))


# ---------------------------------------------------------------- op table

@dataclass(frozen=True)
class Sig:
  thread: Thread
  ins: tuple[RegClass | None, ...]     # None = immediate
  outs: tuple[RegClass, ...]
  fixed: tuple[int, ...] = ()          # pre-coloured physical LRegs for outs (SFPTRANSP)
  latency: int = 1

L = RegClass.LREG
OPS = {
  'sfp.const':  Sig(Thread.MATH, (None,), (L,)),            # LOADI pair; rematerialised, never spilled
  'sfp.abs': Sig(Thread.MATH, (L,), (L,)),
  'sfp.arecip': Sig(Thread.MATH, (L,), (L,)),
  'sfp.mov':    Sig(Thread.MATH, (L,), (L,)),
  'sfp.add':    Sig(Thread.MATH, (L, L), (L,), latency=2),
  'sfp.mul':    Sig(Thread.MATH, (L, L), (L,), latency=2),
  'sfp.mad':    Sig(Thread.MATH, (L, L, L), (L,), latency=2),
  'sfp.shft':   Sig(Thread.MATH, (L, None), (L,)),           # SFPSHFT imm12 / mod
  'sfp.shft2':  Sig(Thread.MATH, (L, None), (L,), latency=2),# SFPSHFT2 lane rotate
  'sfp.iadd':   Sig(Thread.MATH, (L, L, None), (L,)),        # SFPIADD with mod
  'sfp.transp': Sig(Thread.MATH, (L, L, L, L), (L, L, L, L), fixed=(0, 1, 2, 3)),
}


# ---------------------------------------------------------------- trace context

class _Trace:
  def __init__(self) -> None:
    self.stack: list[list[Item]] = [[]]
    self.next_id: int = 0
    self.regions: dict[VReg, list[Item]] = {}
    self.freed: set[VReg] = set()
    self.predicate: int | None = None
    self.items: dict[VReg, VReg] = {}
    self.params: dict[str, RuntimeParam] = {}
    self.param_insts: list[Inst] = []
    self.induction: set[VReg] = set()

  def vreg(self, cls: RegClass, dtype: Dtype, extent: int = 1, name: str | None = None) -> VReg:
    v = VReg(cls, dtype, extent, name, self.next_id)
    self.next_id += 1
    self.regions[v] = self.stack[-1]
    return v

  def emit(self, op: str, ins: tuple[Operand, ...], attrs: dict[str, object] | None = None,
           dtype: Dtype = Dtype.f32, previous: VReg | None = None) -> Inst:
    self.check(ins)
    sig = OPS[op]
    if len(ins) != len(sig.ins): raise TypeError(f'{op} expects {len(sig.ins)} operands')
    for operand, cls in zip(ins, sig.ins):
      if cls is None:
        if isinstance(operand, VReg): raise TypeError(f'{op}: immediate expected')
      elif not isinstance(operand, VReg) or operand.cls is not cls:
        raise TypeError(f'{op}: expected {cls.name} operand, got {operand!r}')
    if previous is not None:
      self.check((previous,))
      if len(sig.outs) != 1 or previous.cls is not sig.outs[0] or previous.dtype is not dtype:
        raise TypeError('previous value must match the result type')
    outs = tuple(self.vreg(cls, dtype) for cls in sig.outs)
    attrs = dict(attrs or {})
    attrs['predicate'] = self.predicate
    attrs['inactive'] = 'previous' if previous is not None else 'undefined'
    operands = tuple(ins) + ((previous,) if previous is not None else ())
    site = traceback.extract_stack(limit=4)[0]
    inst = Inst(op, operands, outs, attrs, f'{site.filename}:{site.lineno}')
    inst.reads = _accesses(operands) + (Access('sfpu.predicate'),)
    # SSA defines the whole new value. Inactive lanes come from previous or
    # are undefined; the old value is never partially overwritten.
    inst.writes = _accesses(outs)
    inst.allocates = outs
    self.stack[-1].append(inst)
    return inst

  def check(self, values: Iterable[object]) -> None:
    for value in values:
      if isinstance(value, AffineIndex):
        self.check((value.index,))
      elif isinstance(value, LaneView):
        self.check((value.block, value.position))
      elif isinstance(value, (BufferRange, StreamRange)):
        self.check((value.offset,))
      elif isinstance(value, View):
        self.check((value.reg, value.offset))
      elif isinstance(value, VReg):
        if value not in self.regions: raise ValueError('register belongs to another trace')
        if value in self.freed: raise ValueError(f'use after free: {value!r}')
        if not any(self.regions[value] is region for region in self.stack):
          raise ValueError(f'register escaped its region: {value!r}')

  @overload
  def record(self, op: str, ins: tuple[Operand, ...] = (), *, cls: RegClass,
             **attrs: object) -> VReg: ...

  @overload
  def record(self, op: str, ins: tuple[Operand, ...] = (), *, cls: None = None,
             **attrs: object) -> VReg | None: ...

  def record(self, op: str, ins: tuple[Operand, ...] = (), *, cls: RegClass | None = None,
             dtype: Dtype = Dtype.f32, extent: int = 1, outs: tuple[VReg, ...] | None = None,
             reads: tuple[Access, ...] | None = None, writes: tuple[Access, ...] | None = None,
             allocates: tuple[VReg, ...] | None = None, releases: tuple[VReg, ...] = (),
             **attrs: object) -> VReg | None:
    # Resource/view operations have API-specific checks, not fixed OPS signatures.
    self.check(ins)
    if outs is not None: self.check(outs)
    fresh = outs is None
    if outs is None: outs = () if cls is None else (self.vreg(cls, dtype, extent),)
    site = traceback.extract_stack(limit=3)[0]
    reads = _accesses(ins) if reads is None else tuple(reads)
    writes = _accesses(outs) if writes is None else tuple(writes)
    reads += _addresses(tuple(a.target for a in (*reads, *writes)))
    self.check(tuple(a.target for a in (*reads, *writes)))
    allocations = tuple(outs) if fresh and allocates is None else tuple(allocates or ())
    self.stack[-1].append(Inst(op, tuple(ins), tuple(outs), attrs, f'{site.filename}:{site.lineno}',
                              reads, writes, allocations, tuple(releases)))
    return outs[0] if outs else None

  def release(self, value: VReg) -> None:
    self.check((value,))
    if any(param.value is value for param in self.params.values()):
      raise ValueError('runtime parameters have invocation lifetime and cannot be freed')
    if self.regions[value] is not self.stack[-1]:
      raise ValueError('cannot free an enclosing allocation inside a device loop')
    stream = self.items.get(value)
    if stream is None:
      self.record('reg.free', (value,), reads=(), writes=(), releases=(value,))
    else:
      self.record('cb.release', (value, stream), reads=(), writes=(Access(('cb.credits', stream)),),
                  releases=(value,))
    self.freed.add(value)


_current: ContextVar[_Trace | None] = ContextVar('ttk_trace', default=None)


def _trace() -> _Trace:
  t = _current.get()
  if t is None: raise RuntimeError('ops must be traced inside trace(fn, *buffers)')
  return t


def trace(fn: Callable[P, object], *buffers: P.args, **kwargs: P.kwargs) -> Kernel:
  if _current.get() is not None: raise RuntimeError('nested trace is unsupported')
  t = _Trace()
  token = _current.set(t)
  try:
    fn(*buffers, **kwargs)
    result = Kernel(fn.__name__, tuple(buffers), t.param_insts + t.stack[0], tuple(t.params.values()))
    result.verify()
    return result
  finally:
    _current.reset(token)


class _KernelAPI:
  def param(self, name: str, *, dtype: Dtype = Dtype.u32) -> VReg:
    """Declare or reference a named runtime integer, constant for one invocation.

    Use the result in traced arithmetic, byte offsets or loop(...) bounds.
    It is symbolic: Python if/range cannot inspect its runtime value. The
    caller will supply the value by name when launching; launch binding and
    per-thread materialization are not implemented in this tracing-only model.

    Repeated requests for the same name return the same value and must agree
    on dtype. Declarations belong to the kernel, even when first requested
    inside a loop. Only i32/u32 parameters are currently supported.
    """
    if not isinstance(name, str) or not name: raise ValueError('parameter name must be a nonempty string')
    if dtype not in (Dtype.i32, Dtype.u32): raise TypeError('runtime parameters require i32/u32')
    t = _trace()
    if name in t.params:
      param = t.params[name]
      if param.dtype is not dtype: raise TypeError(f'conflicting dtype for parameter {name!r}')
      return param.value
    value = t.vreg(RegClass.GPR, dtype, name=f'param[{name!r}]')
    t.regions[value] = t.stack[0]
    param = RuntimeParam(name, dtype, value)
    t.params[name] = param
    site = traceback.extract_stack(limit=2)[0]
    t.param_insts.append(Inst('kernel.param', (), (value,), {'name': name, 'dtype': dtype},
                             f'{site.filename}:{site.lineno}', reads=(Access(param),),
                             writes=(Access(value),), allocates=(value,)))
    return value


kernel = _KernelAPI()


def _scalar(value: Vec | VReg) -> VReg:
  value = _materialize(value) if isinstance(value, AffineIndex) else value
  reg = value.reg if isinstance(value, Vec) else value
  if not isinstance(reg, VReg) or reg.cls not in (RegClass.GPR, RegClass.LREG):
    raise TypeError('loop carry requires scalar/SFPU values, not storage')
  _trace().check((reg,))
  return reg


def _value(reg: VReg) -> Vec | VReg:
  return Vec(reg) if reg.cls is RegClass.LREG else reg


def loop(count: Offset, body: Callable[..., object], *,
         carry: Vec | VReg | tuple[Vec | VReg, ...] | None = None,
         name: str = 'i') -> Vec | VReg | tuple[Vec | VReg, ...] | None:
  """Trace body once into a device loop and return the final SSA carry.

  loop(n, body) calls body(index), which must return None.
  loop(n, body, carry=value) calls body(index, value), returning one value.
  loop(n, body, carry=(a, b)) calls body(index, a, b), returning a tuple.
  Carry count and types must be unchanged. Nested loops use this same API.
  Zero iterations return the initial carry; a runtime bound <= 0 runs no
  iterations. Python range unrolls at trace time. No physical allocation or
  scheduling occurs here.
  """
  if not callable(body): raise TypeError('loop body must be callable')
  t = _trace()
  count = _materialize(count)
  if isinstance(count, VReg):
    t.check((count,))
    if count.cls is not RegClass.GPR: raise TypeError('loop count must be a GPR')
  elif type(count) is not int or count < 0:
    raise ValueError('loop count must be a nonnegative int or GPR')
  multiple = isinstance(carry, tuple)
  inputs = () if carry is None else carry if multiple else (carry,)
  initial = tuple(_scalar(v) for v in inputs)
  node = Loop(count, t.vreg(RegClass.GPR, Dtype.i32, name=f'{name}%{t.next_id}'), initial=initial)
  t.regions[node.index] = node.body
  t.induction.add(node.index)
  t.stack[-1].append(node)
  t.stack.append(node.body)
  node.arguments = tuple(t.vreg(v.cls, v.dtype) for v in initial)
  predicate = t.predicate
  try:
    returned = body(node.index, *(_value(v) for v in node.arguments))
    if t.predicate != predicate: raise ValueError('restore SFPU predicate before leaving a loop')
    if carry is None:
      if returned is not None: raise TypeError('a loop without carry must return None')
    else:
      if multiple and not isinstance(returned, tuple): raise TypeError('tuple carry requires a tuple return')
      if not multiple and isinstance(returned, tuple): raise TypeError('scalar carry requires a scalar return')
      outputs = returned if multiple else (returned,)
      if len(outputs) != len(initial): raise ValueError('loop carry arity mismatch')
      node.yields = tuple(_scalar(v) for v in outputs)
      if any((a.cls, a.dtype) != (b.cls, b.dtype) for a, b in zip(initial, node.yields)):
        raise TypeError('loop carry type mismatch')
      t.record('loop.yield', node.yields, writes=())
  finally:
    t.stack.pop()
  node.results = tuple(t.vreg(v.cls, v.dtype) for v in initial)
  results = tuple(_value(v) for v in node.results)
  return None if carry is None else results if multiple else results[0]


def _positive(value: int, name: str) -> int:
  if type(value) is not int or value <= 0: raise ValueError(f'{name} must be a positive int')
  return value


@dataclass(frozen=True)
class View:
  """Aliasing range within a register allocation, using its native offset units."""
  reg: VReg
  offset: Offset
  extent: int

  def blocks(self, *, offset: int = 0, count: int) -> View:
    """Select 128-element blocks relative to this Src/Dst view.

    count and offset are trace-time integers. Use view[index] for a single
    block selected by a loop index. Dst supports only index + constant; other
    register classes may use runtime GPR offsets. L1 views reject this method.
    """
    if self.cls not in (RegClass.SRCA, RegClass.SRCB, RegClass.DST):
      raise TypeError('blocks requires Src/Dst storage; L1 offsets are bytes')
    _positive(count, 'block count')
    if type(offset) is not int: raise TypeError('block range offset must be an integer')
    return self[offset:offset + count]

  @property
  def cls(self) -> RegClass: return self.reg.cls
  @property
  def dtype(self) -> Dtype: return self.reg.dtype
  def __repr__(self) -> str: return f'{self.reg!r}[{self.offset!r}:+{self.extent}]'
  def __getitem__(self, key: Offset | slice) -> View:
    _trace().check((self,))
    if isinstance(key, slice):
      if key.step not in (None, 1): raise ValueError('views must be contiguous')
      start = 0 if key.start is None else key.start
      stop = self.extent if key.stop is None else key.stop
      if type(start) is not int or type(stop) is not int or not 0 <= start < stop <= self.extent:
        raise ValueError('invalid view bounds')
      size = stop - start
    else:
      start, size = key, 1
      if isinstance(start, (VReg, AffineIndex)):
        _trace().check((start,))
        if isinstance(start, VReg) and start.cls is not RegClass.GPR: raise TypeError('offset must be a GPR')
      elif type(start) is not int or not 0 <= start < self.extent:
        raise ValueError('offset outside allocation')
    offset = start if self.offset == 0 else (start + self.offset if isinstance(start, (VReg, AffineIndex)) else self.offset + start)
    if self.cls is RegClass.DST: _dst_index(offset)
    return View(self.reg, offset, size)


class MemorySpace(Enum):
  DRAM = 'dram'


@dataclass(frozen=True)
class BufferRange:
  buffer: 'Buffer'
  offset: Offset
  extent: int                         # bytes


@dataclass(frozen=True)
class StreamRange:
  """DRAM item at offset + cursor * stride; cursor is the stream's implicit index."""
  buffer: 'Buffer'
  offset: Offset
  extent: int
  stride: int
  cursor: VReg


@dataclass(frozen=True)
class LaneView:
  """One physical 32-lane access position in a single 128-element Dst block."""
  block: View
  position: int | VReg

  def __repr__(self) -> str: return f'{self.block!r}.lanes({self.position!r})'


@dataclass(frozen=True)
class Buffer:
  """Symbolic external parameter. All addressing is in bytes; no tensor layout."""
  name: str
  dtype: Dtype
  nbytes: int
  space: MemorySpace = MemorySpace.DRAM

  def __post_init__(self) -> None:
    _positive(self.nbytes, 'nbytes')
    if self.space is not MemorySpace.DRAM: raise ValueError('external buffers currently require DRAM')


def _memory(value: RegisterView, cls: RegClass) -> RegisterView:
  _trace().check((value,))
  if not isinstance(value, (VReg, View)) or value.cls is not cls:
    raise TypeError(f'expected {cls.name} register or offset view')
  if cls is RegClass.DST and isinstance(value, View): _dst_index(value.offset)
  return value


class _Dst:
  def alloc(self, blocks: int, *, dtype: Dtype = Dtype.f32) -> VReg:
    """Allocate blocks * 128 Dst elements, initially undefined; does not zero them.

    A block always counts 128 elements. BF16 uses 256 bytes per block and FP32
    uses 512 bytes; physical Dst addressing must account for that difference.
    SrcA pair alignment for MVMUL is a separate operand constraint.
    """
    return _trace().record('dst.alloc', cls=RegClass.DST, dtype=dtype, extent=_positive(blocks, 'blocks'), writes=())

  @contextmanager
  def __call__(self, blocks: int, *, dtype: Dtype = Dtype.f32) -> Iterator[VReg]:
    """Compatibility convenience; new kernels use alloc/free explicitly."""
    value = self.alloc(blocks, dtype=dtype)
    try: yield value
    finally: value.free()


dst = _Dst()


class _L1:
  def alloc(self, nbytes: int, *, dtype: Dtype = Dtype.bf16) -> VReg:
    return _trace().record('l1.alloc', cls=RegClass.L1, dtype=dtype, extent=_positive(nbytes, 'nbytes'), writes=())

  def read(self, source: Buffer, *, offset: Offset = 0, nbytes: int | None = None) -> VReg:
    """Compatibility alias for noc.read(..., resident=True)."""
    return noc.read(source, offset=offset, nbytes=nbytes, resident=True)


l1 = _L1()


def _transfer(source: Buffer, offset: Offset, size: int) -> None:
  if not isinstance(source, Buffer): raise TypeError('expected symbolic Buffer')
  _positive(size, 'transfer bytes')
  if isinstance(offset, VReg):
    _memory(offset, RegClass.GPR)
  elif type(offset) is not int or offset < 0 or offset + size > source.nbytes:
    raise ValueError('transfer outside buffer')


@dataclass(eq=False)
class Stream:
  reg: VReg
  source: Buffer
  item_bytes: int
  depth: int
  count: int
  offset: Offset
  stride: int

  def next(self) -> VReg:
    """Acquire one item; release() returns capacity after its readers finish.

    free() remains a compatibility spelling for item release. The stream cursor
    advances once per dynamic execution of this instruction, in program order.
    """
    t = _trace()
    item = t.record('cb.next', (self.reg,), cls=RegClass.L1,
                    dtype=self.source.dtype, extent=self.item_bytes,
                    reads=(Access(self.reg), Access(StreamRange(self.source, self.offset,
                           self.item_bytes, self.stride, self.reg)), Access(('cb.cursor', self.reg))),
                    completion='before_use', release='cb.release')
    inst = t.stack[-1][-1]
    inst.writes += (Access(('cb.cursor', self.reg)),)
    t.items[item] = self.reg
    return item

  def free(self) -> None: self.reg.free()


class _CB:
  def read(self, source: Buffer, *, item_bytes: int, depth: int = 2, offset: Offset = 0,
           count: int | None = None, stride: int | None = None) -> Stream:
    """Declare a finite DRAM stream; next() returns one acquired L1 item.

    item_bytes is the size of each item; depth counts buffered items. offset
    and stride are bytes. count is the number of items, inferred from buffer
    capacity for a constant offset or supplied explicitly for a dynamic one.
    Acquisitions determine producer order. Release each item to recycle space.
    """
    offset = _materialize(offset)
    _positive(item_bytes, 'item_bytes'); _positive(depth, 'depth')
    stride = item_bytes if stride is None else _positive(stride, 'stride')
    if count is None:
      if type(offset) is not int: raise ValueError('dynamic offset requires explicit count')
      count = (source.nbytes - offset - item_bytes) // stride + 1
    _positive(count, 'count')
    _transfer(source, offset, (count - 1) * stride + item_bytes)
    reg = _trace().record('cb.read', (offset,), cls=RegClass.L1, dtype=source.dtype,
                          extent=item_bytes * depth, source=source, item_bytes=item_bytes,
                          depth=depth, count=count, stride=stride, reads=_accesses((offset,)), writes=())
    _trace().stack[-1][-1].writes = (Access(('cb.cursor', reg)), Access(('cb.credits', reg)))
    return Stream(reg, source, item_bytes, depth, count, offset, stride)


cb = _CB()


def unpack(source: RegisterView, *, into: RegisterView) -> None:
  """Record a transfer to an explicitly allocated Src/Dst register range."""
  _memory(source, RegClass.L1)
  if into.cls not in (RegClass.SRCA, RegClass.SRCB, RegClass.DST): raise TypeError('invalid unpack target')
  _memory(into, into.cls)
  size = 2 if source.dtype is Dtype.bf16 else 4
  if source.extent != into.extent * 128 * size: raise ValueError('unpack extent mismatch')
  _trace().record('unpack', (source, into), reads=(Access(source),), writes=(Access(into),))


def pack(source: RegisterView, *, into: RegisterView) -> None:
  _memory(source, RegClass.DST); _memory(into, RegClass.L1)
  size = 2 if into.dtype is Dtype.bf16 else 4
  if into.extent != source.extent * 128 * size: raise ValueError('pack extent mismatch')
  _trace().record('pack', (source, into), reads=(Access(source),), writes=(Access(into),))


class _NoC:
  def read(self, source: Buffer, *, offset: Offset = 0, nbytes: int | None = None,
           resident: Literal[True] = True) -> VReg:
    """Read DRAM bytes into resident L1 storage; return an L1 VReg, not a scalar.

    source is an external DRAM Buffer. offset is a byte offset, either a Python
    integer or a runtime GPR expression. nbytes is a trace-time byte count;
    when omitted it defaults to source.nbytes, not the remaining suffix.
    Specify nbytes for a subrange or runtime gather.

    The returned allocation holds nbytes bytes in source.dtype. Its views feed
    unpack or noc.write; they are not arithmetic values. Read completion before
    the first consumer is implicit. The data stays resident rather than being
    refilled. Use cb.read for streaming, or kernel.param for invocation-supplied integers
    used in address arithmetic. This method records IR; it does no host read.
    """
    if resident is not True: raise ValueError('use cb.read for streaming storage')
    offset = _materialize(offset)
    size = source.nbytes if nbytes is None else nbytes
    _transfer(source, offset, size)
    return _trace().record('noc.read', (offset,), cls=RegClass.L1, dtype=source.dtype,
                           extent=size, source=source, completion='before_use',
                           reads=(Access(BufferRange(source, offset, size)),))

  def write(self, source: RegisterView, target: Buffer, *, offset: Offset = 0) -> None:
    """Write an L1 byte range to DRAM at a constant or runtime byte offset.

    source.extent determines the transfer size. Completion must precede reuse
    of its storage; no scalar GPR store or dtype conversion is implied.
    """
    _memory(source, RegClass.L1)
    offset = _materialize(offset)
    _transfer(target, offset, source.extent)
    _trace().record('noc.write', (source, offset), target=target, completion='before_release',
                    reads=(Access(source),), writes=(Access(BufferRange(target, offset, source.extent)),))



noc = _NoC()


# ---------------------------------------------------------------- SFPU values

def _bits(value: int | float) -> int: return struct.unpack('<I', struct.pack('<f', float(value)))[0]


@dataclass(frozen=True)
class Vec:
  """An immutable SSA SFPU value; physical LReg reuse is an allocation decision."""
  reg: VReg

  def free(self) -> None: self.reg.free()

  def _bin(self, op: str, other: SFPUValue, swap: bool = False) -> Vec:
    other = _vec(other)
    a, b = (other, self) if swap else (self, other)
    return Vec(_trace().emit(op, (a.reg, b.reg)).outs[0])

  def __add__(self, o: SFPUValue) -> Vec: return self._bin('sfp.add', o)
  def __radd__(self, o: SFPUValue) -> Vec: return self._bin('sfp.add', o, swap=True)
  def __mul__(self, o: SFPUValue) -> Vec: return self._bin('sfp.mul', o)
  def __rmul__(self, o: SFPUValue) -> Vec: return self._bin('sfp.mul', o, swap=True)
  def __neg__(self) -> Vec: return Vec(_trace().emit('sfp.mov', (self.reg,), {'mod': 1}).outs[0])
  def __sub__(self, o: SFPUValue) -> Vec: return self + (-_vec(o))
  def __bool__(self) -> NoReturn: raise TypeError('symbolic values cannot control Python branches')


def _vec(value: SFPUValue) -> Vec:
  if isinstance(value, Vec): return value
  if type(value) in (int, float): return sfpu.const(value)
  raise TypeError(f'not an SFPU value: {value!r}')


class _SFPU:
  def const(self, value: int | float) -> Vec:
    return Vec(_trace().emit('sfp.const', (float(value),), {'bits': _bits(value)}).outs[0])

  def const_bits(self, bits: int) -> Vec:
    if type(bits) is not int or not 0 <= bits < 2**32: raise ValueError('bits must be uint32')
    return Vec(_trace().emit('sfp.const', (0.0,), {'bits': bits, 'literal': 'bits'}).outs[0])

  @staticmethod
  def lane_element(position: int, lane: int) -> int:
    """Physical FP32 Dst mapping within a 128-element block."""
    if type(position) is not int or not 0 <= position < 4: raise ValueError('position must be 0..3')
    if type(lane) is not int or not 0 <= lane < 32: raise ValueError('lane must be 0..31')
    return (position // 2) * 64 + (lane // 8) * 16 + (lane % 8) * 2 + position % 2

  def predicate(self, mask: int | None = None) -> None:
    """Bit i enables physical lane i; None enables all lanes. Explicit state."""
    if mask is not None and (type(mask) is not int or not 0 <= mask < 2**32):
      raise ValueError('predicate must be a uint32 mask or None')
    _trace().record('sfp.predicate', (), mask=mask, writes=(Access('sfpu.predicate'),))
    _trace().predicate = mask

  def lanes(self, block: RegisterView) -> tuple[LaneView, ...]:
    """Trace-time iteration over the four physical positions; emits no ops itself."""
    block = self._lane_view(block, 0).block
    return tuple(LaneView(block, position) for position in range(4))

  def _lane_view(self, view: RegisterView | LaneView, position: Offset | None = None) -> LaneView:
    if isinstance(view, LaneView):
      if position is not None: raise ValueError('lane view already specifies a position')
      _trace().check((view,))
      _dst_index(view.block.offset)
      return view
    _memory(view, RegClass.DST)
    if view.dtype is not Dtype.f32: raise TypeError('SFPU Dst mapping currently requires f32')
    # Bare registers retain the old first-block shorthand; range views must be exact.
    if isinstance(view, VReg): view = view[0]
    if view.extent != 1: raise ValueError('SFPU access requires exactly one Dst block')
    position = 0 if position is None else position
    if isinstance(position, VReg): _memory(position, RegClass.GPR)
    elif type(position) is not int or not 0 <= position < 4: raise ValueError('position must be 0..3')
    return LaneView(view, position)

  def load(self, view: RegisterView | LaneView, *, position: Offset | None = None,
           previous: Vec | None = None) -> Vec:
    """Create a fresh value; masked-off lanes come from previous or are undefined."""
    lane = self._lane_view(view, position)
    old = () if previous is None else (previous.reg,)
    if previous is not None:
      _memory(previous.reg, RegClass.LREG)
      if previous.reg.dtype is not Dtype.f32: raise TypeError('previous load value must be f32')
    t = _trace()
    reads = (Access(lane, t.predicate), Access('sfpu.predicate')) + _accesses(old)
    reg = t.record('sfp.load', (lane, *old), cls=RegClass.LREG,
                   reads=reads, position=lane.position, predicate=t.predicate,
                   inactive='previous' if previous is not None else 'undefined')
    return Vec(reg)

  def store(self, value: SFPUValue, view: RegisterView | LaneView, *, position: Offset | None = None) -> None:
    lane = self._lane_view(view, position)
    reg, mask = _vec(value).reg, _trace().predicate
    _trace().record('sfp.store', (reg, lane), position=lane.position,
                    predicate=mask, inactive='preserve',
                    reads=(Access(reg, mask), Access('sfpu.predicate')),
                    writes=(Access(lane, mask, True),))

  def mul(self, a: SFPUValue, b: SFPUValue, *, mod: int = 0) -> Vec:
    return Vec(_trace().emit('sfp.mul', (_vec(a).reg, _vec(b).reg), {'mod': mod} if mod else None).outs[0])

  def mad(self, a: SFPUValue, b: SFPUValue, c: SFPUValue, *,
          previous: Vec | None = None, mod: int = 0) -> Vec:
    """Explicit fused arithmetic with a fresh result, never an in-place update.

    Under predication, previous supplies inactive lanes independently of c.
    """
    return Vec(_trace().emit('sfp.mad', (_vec(a).reg, _vec(b).reg, _vec(c).reg),
                            {'mod': mod} if mod else None,
                            previous=None if previous is None else previous.reg).outs[0])

  def abs(self, value: SFPUValue) -> Vec:
    return Vec(_trace().emit('sfp.abs', (_vec(value).reg,), {'mod': 1}).outs[0])

  def reciprocal_native(self, value: SFPUValue) -> Vec:
    return Vec(_trace().emit('sfp.arecip', (_vec(value).reg,), {'mod': 0}).outs[0])

  def shft(self, v: SFPUValue, imm: int, mod: int) -> Vec:
    return Vec(_trace().emit('sfp.shft', (_vec(v).reg, imm), {'mod': mod}).outs[0])

  def shft2(self, v: SFPUValue, mod: int) -> Vec:
    return Vec(_trace().emit('sfp.shft2', (_vec(v).reg, 0), {'mod': mod}).outs[0])

  def iadd(self, a: SFPUValue, b: SFPUValue, mod: int) -> Vec:
    return Vec(_trace().emit('sfp.iadd', (_vec(a).reg, _vec(b).reg, 0), {'mod': mod}).outs[0])

  def transp(self, a: SFPUValue, b: SFPUValue, c: SFPUValue, d: SFPUValue) -> tuple[Vec, Vec, Vec, Vec]:
    """SFPTRANSP: 4x(8-lane row) transpose. Fixed registers L0..L3 (pre-coloured)."""
    ins = tuple(_vec(v).reg for v in (a, b, c, d))
    if len(set(ins)) != 4:
      # Distinct physical registers are required; copy duplicates first.
      seen, copies = set(), []
      for r in ins:
        if r in seen: r = _trace().emit('sfp.mov', (r,)).outs[0]
        seen.add(r); copies.append(r)
      ins = tuple(copies)
    return tuple(Vec(r) for r in _trace().emit('sfp.transp', ins).outs)


  def lane_sum(self, v: SFPUValue) -> Vec:
    """Sum across all 32 lanes; result broadcast to every lane.

    Three rotate+add rounds reduce each 8-lane row, SFPTRANSP turns the four
    row sums into columns, three adds combine them.
    """
    v = _vec(v)
    for rotations in (4, 2, 1):
      t = v
      for _ in range(rotations): t = sfpu.shft2(t, 3)
      v = v + t
    a, b, c, d = sfpu.transp(v, v, v, v)
    return a + b + c + d


  def rsqrt(self, x: SFPUValue) -> Vec:
    """Reciprocal square root for finite positive FP32 (Blackhole magic + one Newton step).

    Transcribed from llama3_row_major._append_rms_rsqrt.
    """
    x = _vec(x)
    y = sfpu.shft(x, 0xfff, 1)                        # exponent field >> 1
    y = sfpu.iadd(sfpu.const_bits(0x5f1110a0), y, 6)  # magic - y
    t = x * y
    t = sfpu.mul(y, t, mod=1)                         # -(x*y)*y
    c2 = sfpu.const(2.2533049) + t
    t = sfpu.mad(t, c2, sfpu.const(2.2825186))
    y = y * t
    t = x * y
    t = sfpu.mul(y, t, mod=1)
    t = 1.0 + t
    half = y * 0.5
    return sfpu.mad(t, half, y)

sfpu = _SFPU()


class _Src:
  def __init__(self, cls: RegClass) -> None: self.cls = cls

  def alloc(self, blocks: int, *, dtype: Dtype = Dtype.bf16) -> VReg:
    return _trace().record('src.alloc', cls=self.cls, dtype=dtype, extent=_positive(blocks, 'blocks'), writes=())


srca, srcb = _Src(RegClass.SRCA), _Src(RegClass.SRCB)


class _FPU:
  def op(self, op: Literal['add', 'sub', 'mul', 'mvmul', 'gapool', 'gmpool'],
         a: RegisterView, b: RegisterView, *, into: RegisterView,
         accumulate: bool = False, **modifiers: object) -> None:
    """Record a machine operation with explicit SrcA, SrcB and Dst operands.

    MVMUL/GAPOOL/GMPOOL read an aligned SrcA pair (two 128-element blocks).
    For example a.blocks(offset=0, count=2) is legal, while offset=1 is not.
    The even-start constraint belongs to SrcA, not to the Dst view. Dynamic
    starts carry an alignment requirement that future lowering must prove.
    Full output-footprint and fidelity legality checks remain future work.
    """
    if op not in ('add', 'sub', 'mul', 'mvmul', 'gapool', 'gmpool'):
      raise ValueError('unknown FPU operation')
    _memory(a, RegClass.SRCA); _memory(b, RegClass.SRCB); _memory(into, RegClass.DST)
    paired = op in ('mvmul', 'gapool', 'gmpool')
    if paired:
      if a.extent != 2: raise ValueError(f'{op} requires two SrcA blocks')
      start = a.offset if isinstance(a, View) else 0
      if type(start) is int and start % 2: raise ValueError('SrcA pair must start at an even block')
      allocation = a.reg if isinstance(a, View) else a
      allocation.alignment = max(allocation.alignment, 2)
    _trace().record('fpu.' + op, (a, b, into), accumulate=accumulate,
                    reads=(Access(a, alignment=2 if paired else 1), Access(b)) + ((Access(into),) if accumulate else ()),
                    writes=(Access(into),), **modifiers)


fpu = _FPU()


# First-party compositions expand into ordinary register instructions. Numerical
# recipes come from tests/operation_pocs/sfpu_math/emit.py; these are hardware
# approximations, not promises of IEEE special-case handling or correct rounding.

def reciprocal(x: SFPUValue, *, mode: Literal['native', 'refined'] = 'refined') -> Vec:
  """Native approximate reciprocal, optionally with two Newton refinements.

  Refined mode targets finite nonzero inputs whose intermediate products remain
  representable. Zero, infinities and NaNs have no refined-mode guarantee.
  """
  if mode not in ('native', 'refined'): raise ValueError('invalid reciprocal mode')
  x = _vec(x)
  y = sfpu.reciprocal_native(x)
  if mode == 'refined':
    for _ in range(2):
      correction = sfpu.mad(x, y, 2.0, mod=1)  # 2 - x*y
      y = y * correction
  return y


def exp(x: SFPUValue) -> Vec:
  """Degree-8 Taylor exp(x/256), squared eight times; PoC refined recipe.

  Intended for finite x approximately in [-88, 88]. No exceptional-value or
  correctly-rounded guarantee. Preserve the incoming physical lane predicate.
  """
  scaled = _vec(x) * (1.0 / 256)
  y = sfpu.const(1.0 / factorial(8))
  for degree in range(7, -1, -1):
    y = sfpu.mad(y, scaled, 1.0 / factorial(degree))
  for _ in range(8): y = y * y
  return y


def sigmoid(x: SFPUValue) -> Vec:
  """Composition 1/(1+exp(-x)); inherits exp/reciprocal domain limits."""
  return reciprocal(1.0 + exp(-_vec(x)))


def silu(x: SFPUValue) -> Vec:
  """SiLU on the finite domain supported by sigmoid."""
  x = _vec(x)
  return x * sigmoid(x)


def swiglu(gate: SFPUValue, up: SFPUValue) -> Vec:
  """SiLU(gate) * up, as ordinary SFPU instructions."""
  return silu(gate) * _vec(up)
