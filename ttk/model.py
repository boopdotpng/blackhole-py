"""Experimental protocol-first kernel frontend; traces only, no device lowering.

Operations and AFTER express data/completion dependencies. INDEX(storage, seq)
names an occupancy; capacity hazards and synchronization are derived from
accesses rather than encoded as ring-management or WAIT nodes. Queue placement
does not add dependencies.
loop() preserves RANGE regions; Python for loops explicitly unroll. Stream reads
issued inside a loop put their producer work in the same region, so producer and
consumer loops always agree on trip count.
No claim of physical bank allocation, deadlock proof or executable code yet.
"""
from contextvars import ContextVar
from dataclasses import dataclass, replace
from enum import Enum
import struct

from .uop import Ops, UOp, Thread, ParamArg, RingSpec, StorageSpec, _intern, is_ring, ISSUES, FPUArgs, PackArgs, PeerGroup, verify


class Dtype(Enum):
  bf16 = 'bf16'; f32 = 'f32'; i32 = 'i32'; u32 = 'u32'


@dataclass(frozen=True)
class Buffer:
  name: str
  dtype: Dtype
  nbytes: int


_current = ContextVar('ttk_trace', default=None)


def _trace():
  t = _current.get()
  if t is None: raise RuntimeError('operation requires trace()')
  return t


class _Trace:
  def __init__(self):
    self.nodes, self.resources, self.params = [], [], {}
    self.seen, self.allocation_count = set(), 0
    self.regions, self.scopes = [], {}
    self.sequence_events, self.replacements = {}, {}

  def param(self, name, dtype, nbytes):
    if not isinstance(name, str) or not name: raise ValueError('parameter requires a name')
    if not isinstance(dtype, Dtype): raise TypeError('parameter requires a Dtype')
    if type(nbytes) is not int or nbytes <= 0: raise ValueError('buffer size must be positive')
    if name in self.params:
      node = self.params[name]
      if node.arg[0] != ParamArg(node.arg[0].slot, name, dtype.value, nbytes):
        raise ValueError(f'conflicting declarations for parameter {name!r}')
      return node
    desc = ParamArg(len(self.params), name, dtype.value, nbytes)
    node = UOp(Ops.PARAM, arg=(desc,), dtype='u32')
    self.params[name] = node
    self.nodes.append(node)
    return node

  def scalar(self, param):
    desc = ParamArg(len(self.params), param.name, param.dtype.value, lo=param.lo, hi=param.hi)
    if param.name in self.params:
      node = self.params[param.name]
      if node.arg[0] != ParamArg(node.arg[0].slot, param.name, param.dtype.value, lo=param.lo, hi=param.hi):
        raise ValueError(f'conflicting declarations for parameter {param.name!r}')
      return node
    node = UOp(Ops.PARAM, arg=(desc,), dtype=desc.dtype)
    self.params[param.name] = node; self.nodes.append(node)
    return node

  def scope(self, node):
    if node not in self.scopes:
      for n in node.toposort():
        if n in self.scopes: continue
        ranges = set().union(*(self.scopes[s] for s in n.src))
        if n.op is Ops.RANGE: ranges.add(n)
        if n.op is Ops.END: ranges.discard(n.src[1])
        self.scopes[n] = frozenset(ranges)
    return self.scopes[node]

  def define(self, spec, dtype='void'):
    spec = replace(spec, identity=self.allocation_count)
    self.allocation_count += 1
    return self.emit(Ops.DEFINE, arg=(spec,), dtype=dtype)

  def emit(self, op, src=(), arg=(), dtype='void', thread=None, queue=None):
    """Record data/effect dependencies only. Queue placement adds no edges."""
    parents = tuple(src)
    if self.regions and op is not Ops.DEFINE:
      region = self.regions[-1]
      if not any(region in self.scope(s) for s in parents):
        # Anchor only independent work, through AFTER so operand arity stays fixed.
        if op is Ops.RANGE: parents = (*parents, region)  # bound stays in src[0]
        else: parents = (parents[0].after(region), *parents[1:]) if parents else (region,)
    node = UOp(op, parents, tuple(arg), dtype, thread)
    if node not in self.seen:
      self.nodes.append(node); self.seen.add(node)
    self.scope(node)
    return node

  def record_effect(self, operation, views=(), writes=None):
    # AFTER names the operation whose result is needed; completion mechanisms
    # (waits, bank handoffs, CB counters, NoC semaphores) belong to lowering.
    writes = views if writes is None else writes
    for view in views:
      # Item readers share the producer version. Capacity inference sees every
      # read separately; it does not need a read-to-read storage-state chain.
      if view in writes or view.root.kind == 'DST': view.root.state = operation
      view.root.last_effect = operation
    return operation

  def issue(self, op, views, arg=(), thread=None):
    for v in views:
      v.check()
    pending = self.emit(op, tuple(v.index() for v in views), arg, 'void', thread)
    return self.record_effect(pending, views, writes=views[-1:])

  def sequence(self, ring):
    # A private construction placeholder, replaced by bounded arithmetic before
    # the graph is returned. It must not alias an ordinary CONST in the cache.
    token = _intern.set(None)
    try: seq = UOp(Ops.CONST, arg=(0,), dtype='i32')
    finally: _intern.reset(token)
    self.scopes[seq] = tuple(self.regions)
    self.sequence_events.setdefault(ring, []).append((seq, tuple(self.regions)))
    return seq

  def finish(self):
    from .loops import trip_count
    def product(path):
      result = 1
      for r in path: result *= trip_count(r)
      return result
    def const(n): return UOp(Ops.CONST, arg=(n,), dtype='i32')
    # Mixed-radix occupancy numbering handles multiple items per iteration,
    # nested loops and straight-line work before/after them without new ops.
    for events in self.sequence_events.values():
      for i, (placeholder, path) in enumerate(events):
        offset = 0
        for _, previous in events[:i]:
          common = 0
          while common < min(len(path),len(previous)) and path[common] is previous[common]: common += 1
          offset += product(previous[common:])
        seq = const(offset)
        for depth, r in enumerate(path):
          prefix = path[:depth+1]
          stride = sum(product(p[depth+1:]) for _,p in events if p[:depth+1] == prefix)
          term = r if stride == 1 else UOp(Ops.MUL,(r,const(stride)),dtype='i32')
          seq = UOp(Ops.ADD,(seq,term),dtype='i32')
        self.replacements[placeholder] = seq
    provisional = UOp(Ops.SINK, tuple(self.nodes))
    referenced = {s for n in provisional.toposort() if n is not provisional for s in n.src}
    sink = UOp(Ops.SINK, tuple(n for n in self.nodes if n not in referenced))
    mapped = {}
    for n in sink.toposort():
      if n in self.replacements: mapped[n] = self.replacements[n]; continue
      src = tuple(mapped[s] for s in n.src)
      mapped[n] = n if src == n.src else UOp(n.op,src,n.arg,n.dtype,n.thread)
    return mapped[sink], tuple(self.params.values())


@dataclass
class Kernel:
  sink: UOp
  params: tuple[UOp, ...] = ()

  def bind(self, **values):
    """Bind all launch arguments without specializing or modifying this graph."""
    names = {node.arg[0].name for node in self.params}
    if values.keys() != names:
      raise ValueError(f'argument mismatch: missing={sorted(names-values.keys())}, extra={sorted(values.keys()-names)}')
    ordered = []
    for node in self.params:
      desc = node.arg[0]; value = values[desc.name]
      low, high = (desc.lo, desc.hi) if desc.scalar else (0, 2**32-1)
      if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{desc.name} requires an integer in [{low}, {high}]')
      ordered.append(value)
    return BoundKernel(self, tuple(ordered))

  def dump(self, **kwargs): return self.sink.dump()
  def verify(self): verify(self.sink)
  def render(self, *, per_thread=False):
    from .render import FakeRenderer
    from .linearize import linearize
    return FakeRenderer().render(linearize(self.sink), per_thread=per_thread)


@dataclass(frozen=True)
class BoundKernel:
  """One invocation's values, ordered by PARAM slot. No launcher implemented yet."""
  kernel: Kernel
  args: tuple

  def bind(self, **changes):
    values = {node.arg[0].name: value for node, value in zip(self.kernel.params, self.args)}
    values.update(changes)
    return self.kernel.bind(**values)


def trace(fn, *args, **kwargs):
  if _current.get() is not None: raise RuntimeError('nested trace is unsupported')
  t = _Trace(); token = _current.set(t); intern_token = _intern.set({})
  try:
    # Reserve slots in supplied argument order, before tracing their uses.
    for value in (*args, *kwargs.values()):
      if isinstance(value, Buffer): t.param(value.name, value.dtype, value.nbytes)
      elif isinstance(value, Param): t.scalar(value)
    fn(*args, **kwargs)
    for resource in t.resources:
      if not resource.closed and not getattr(resource, "retain", False): resource.release()
    result = Kernel(*t.finish())
  finally:
    _current.reset(token); _intern.reset(intern_token)
  result.verify()
  return result


class Vec:
  def __init__(self, node): self.node = node
  def __bool__(self): raise TypeError('symbolic values cannot control Python branches')
  def binary(self, op, other):
    _vec(self)
    other = _vec(other)
    dtype = next((d for d in (self.node.dtype, other.node.dtype) if '.vec(' in d),
                 'f32' if 'f32' in (self.node.dtype, other.node.dtype) else self.node.dtype)
    return Vec(_trace().emit(op, (self.node, other.node), dtype=dtype))
  def __add__(self, other): return self.binary(Ops.ADD, other)
  __radd__ = __add__
  def __sub__(self, other): return self.binary(Ops.SUB, other)
  def __rsub__(self, other): return _vec(other) - self
  def __mul__(self, other): return self.binary(Ops.MUL, other)
  __rmul__ = __mul__
  def __floordiv__(self, other): return self.binary(Ops.IDIV, other)
  def __mod__(self, other): return self.binary(Ops.MOD, other)
  def __neg__(self): return self * -1


@dataclass(frozen=True)
class Param:
  name: str
  dtype: Dtype
  lo: int
  hi: int

  def __post_init__(self):
    if not isinstance(self.name, str) or not self.name: raise ValueError('parameter requires a name')
    if not isinstance(self.dtype, Dtype): raise TypeError('parameter requires a Dtype')
    ParamArg(0, self.name, self.dtype.value, lo=self.lo, hi=self.hi)

  @property
  def node(self): return _trace().scalar(self)
  def __bool__(self): raise TypeError('symbolic values cannot control Python branches')
  def __add__(self, other): return _vec(self) + other
  __radd__ = __add__
  def __sub__(self, other): return _vec(self) - other
  def __rsub__(self, other): return _vec(other) - _vec(self)
  def __mul__(self, other): return _vec(self) * other
  __rmul__ = __mul__
  def __floordiv__(self, other): return _vec(self) // other
  def __mod__(self, other): return _vec(self) % other


def _vec(value):
  if isinstance(value, Param): value = Vec(value.node)
  if isinstance(value, Vec):
    t = _trace()
    if any(r not in t.regions for r in t.scopes.get(value.node, ())):
      raise ValueError('loop-local value escaped its region')
    return value
  if type(value) not in (int, float): raise TypeError('expected symbolic value or number')
  return Vec(UOp(Ops.CONST, arg=(value,), dtype='i32' if type(value) is int else 'f32'))


def _bounds(value):
  from .loops import bounds
  if type(value) is int: return value, value
  if isinstance(value, Param): value = _vec(value)
  if not isinstance(value, Vec): raise TypeError('index must be an integer or symbolic loop index')
  return bounds(_vec(value).node)


class View:
  def __init__(self, root, offset, extent): self.root, self.offset, self.extent = root, offset, extent
  @property
  def dtype(self): return self.root.dtype
  def __bool__(self): raise TypeError('symbolic values cannot control Python branches')
  def check(self):
    if self.root.owner is not _trace(): raise ValueError('resource belongs to another trace')
    if self.root.closed: raise ValueError('use after release')
  def index(self, *dependencies):
    self.check()
    if isinstance(self.root, RingItem) and self.root.sequence is None: raise ValueError('ring item has not been written')
    root = self.root.node
    states = (*((self.root.state,) if self.root.state is not root else ()), *dependencies)
    if states: root = root.after(*dict.fromkeys(states))
    if isinstance(self.root,RingItem):
      item = UOp(Ops.INDEX,(root,self.root.sequence),(self.root.extent,))
      if type(self.offset) is int and self.offset == 0 and self.extent == self.root.extent: return item
      root = item
    return UOp(Ops.INDEX,(root,_vec(self.offset).node),(self.extent,))
  def __getitem__(self, key):
    if isinstance(key, slice):
      if key.step not in (None, 1): raise ValueError('strided views are unsupported')
      start, stop = 0 if key.start is None else key.start, self.extent if key.stop is None else key.stop
      if type(start) is not int or type(stop) is not int: raise TypeError('use blocks(offset=..., count=...) for symbolic slices')
      return self.blocks(offset=start, count=stop-start)
    return self.blocks(offset=key, count=1)
  def blocks(self, *, offset=0, count):
    self.check()
    if type(count) is not int or count <= 0: raise ValueError('view count must be positive')
    low, high = _bounds(offset)
    if low < 0 or high + count > self.extent: raise ValueError('view out of bounds')
    return View(self.root, self.offset + offset, count)
  def release(self):
    if self is not self.root: raise ValueError('release the allocation, not an alias')
    self.check()
    if isinstance(self.root, RingItem):
      self.root.finish_release()
      return
    if _trace().regions: raise ValueError('release Dst outside loops')
    self.root.closed = True

  def free(self): self.release()  # compatibility: checked lifetime assertion


class Allocation(View):
  def __init__(self, extent, dtype):
    if type(extent) is not int or extent <= 0: raise ValueError('extent must be positive')
    if _trace().regions: raise ValueError('allocate Dst outside the loop')
    self.owner = _trace(); self.kind = 'DST'; self._dtype = dtype
    self.node = self.owner.define(StorageSpec('DST', extent, dtype.value))
    self.state = self.node; self.last_effect = None; self.closed = False
    super().__init__(self, 0, extent)
    self.owner.resources.append(self)
  @property
  def dtype(self): return self._dtype


# ---------------------------------------------------------------- rings

class Ring:
  """Storage contract. Items are INDEX(storage, sequence), not protocol nodes."""
  def __init__(self, kind, item, depth, dtype, *, slot=None, producer='local', storage=None):
    t = _trace()
    if t.regions: raise ValueError('declare rings outside loops')
    self.owner, self.dtype = t, dtype
    self.spec = RingSpec(kind,item,depth,dtype.value,slot,producer,storage)
    if slot is not None and producer != 'peer' and any(is_ring(n) and n.arg[0].slot == slot
        and n.arg[0].producer != 'peer' for n in t.nodes): raise ValueError('duplicate local CB slot')
    self.node = t.define(self.spec); self.spec = self.node.arg[0]

  def receive(self, *, sender, thread=None, after=None):
    if self.spec.producer != 'remote': raise ValueError('receive requires a remote producer')
    if len(sender) != 2: raise ValueError('receive requires sender xy')
    coordinates = []
    for coord in sender:
      low, high = _bounds(coord)
      if not 0 <= low <= high < 64: raise ValueError('sender coordinate out of range')
      n = _vec(coord).node
      if n.op not in (Ops.CONST,Ops.PARAM): raise ValueError('sender xy requires constants or scalar parameters')
      coordinates.append(n.arg[0])
    if self.spec.sender and (self.spec.sender != tuple(coordinates) or self.spec.receiver_thread != thread):
      raise ValueError('conflicting sender endpoint')
    self.spec = replace(self.spec,sender=tuple(coordinates),receiver_thread=thread)
    self.owner.replacements[self.node] = UOp(Ops.DEFINE,arg=(self.spec,))
    if after is not None and (after not in self.owner.nodes or after.op not in (*ISSUES, Ops.LOAD, Ops.END)):
      raise ValueError('receive ordering requires a completion from this trace')
    item = self.acquire(); item.begin()
    item.ready = True
    if after is not None: item.state = after
    return item

  def acquire(self):
    if self.spec.producer == 'peer': raise ValueError('cannot acquire peer storage locally')
    if self.owner is not _trace(): raise ValueError('ring belongs to another trace')
    return RingItem(self)


class RingItem(View):
  """Frontend lifetime handle for one occupancy. release() emits nothing."""
  def __init__(self, ring):
    self.ring, self.owner, self.kind, self._dtype = ring, ring.owner, ring.spec.kind, ring.dtype
    self.region = tuple(self.owner.regions)
    self.node = ring.node; self.state = ring.node; self.last_effect = None
    self.sequence = None; self.ready = False
    self.closed = False; self.retain = False
    super().__init__(self,0,ring.spec.item)
    self.owner.resources.append(self)

  @property
  def dtype(self): return self._dtype

  def check(self):
    super().check()
    if any(r not in self.owner.regions for r in self.region): raise ValueError('ring item escaped its loop')

  def begin(self):
    self.check()
    if self.sequence is None:
      if tuple(self.owner.regions) != self.region: raise ValueError('first write must occur in the item region')
      self.sequence = self.owner.sequence(self.ring)

  def consume(self, queue=None, thread=None):
    self.check()
    if not self.ready: raise ValueError('ring item is not written')
    return self

  def handoff(self, ring):
    self.check()
    a,b = self.ring.spec,ring.spec
    if ring.owner is not self.owner or ring is self.ring or a.storage is None or a.storage != b.storage:
      raise ValueError('handoff requires distinct aliases of the same storage')
    if a.producer != 'local' or b.producer != 'local' or a.depth != 1 or b.depth != 1 or (a.item,a.dtype) != (b.item,b.dtype):
      raise ValueError('handoff requires matching local depth-one layouts')
    self.consume()
    item = ring.acquire(); item.begin()
    item.state = item.last_effect = self.last_effect; item.ready = True
    self.release()
    return item

  def finish_release(self):
    self.closed = True


class Stream(Ring):
  """DRAM item stream. Offsets and occupancy use the same bounded sequence."""
  def __init__(self, buffer, item_size, capacity, resident=False):
    if type(item_size) is not int or item_size <= 0 or buffer.nbytes % item_size:
      raise ValueError('invalid stream dimensions')
    self.buffer, self.item_size, self.resident = buffer,item_size,resident
    self.count = buffer.nbytes//item_size
    super().__init__('L1',item_size,self.count if resident else capacity,buffer.dtype)

  def next(self, *, queue='unpack', thread=None):
    item = self.acquire(); item.begin()
    noc.read(self.buffer,into=item,offset=Vec(item.sequence)*self.item_size,nbytes=self.item_size,
             resident=self.resident,thread=thread)
    return item


class _Storage:
  def __init__(self, kind): self.kind = kind
  def alloc(self, extent, *, dtype=Dtype.f32):
    if self.kind == 'DST': return Allocation(extent, dtype)
    # Compatibility convenience: scratch is a depth-one ring; source storage
    # is a hardware depth-two ring. No separate L1/Src allocation UOps.
    return Ring(self.kind, extent, 1 if self.kind == 'L1' else 2, dtype).acquire()


dst = _Storage('DST'); l1 = _Storage('L1')
srca = _Storage('SRCA'); srcb = _Storage('SRCB')


def _dram(buffer):
  if not isinstance(buffer, Buffer): raise TypeError('expected Buffer')
  return _trace().param(buffer.name, buffer.dtype, buffer.nbytes)


def _write_slot(view, queue, thread=None):
  view.check()
  if isinstance(view.root, RingItem) and view.root.ring.spec.producer != "local":
    raise ValueError("cannot write a remote producer ring locally")
  if not isinstance(view.root, RingItem): raise TypeError('expected a ring item')
  if view is not view.root: raise ValueError('partial item writes are not implemented')
  if view.root.ready: raise ValueError('cannot overwrite a written item; use accumulate')
  view.root.begin()


def _read_slot(view, queue, thread=None):
  if not isinstance(view.root, RingItem): raise TypeError('expected a ring item')
  view.root.consume(queue, thread)


class _NoC:
  def read(self, buffer, *, into=None, offset=0, nbytes=None, resident=False, thread=None):
    size = (into.extent if into is not None else buffer.nbytes) if nbytes is None else nbytes
    low, high = _bounds(offset)
    if low < 0 or high + size > buffer.nbytes: raise ValueError('read out of bounds')
    if into is None:
      # A one-item resident read, still represented by exactly the same ring.
      into = Ring('L1', size, 1, buffer.dtype).acquire()
    into.root.retain = resident
    if into.root.kind != 'L1' or into.extent != size: raise ValueError('read requires a matching L1 ring slot')
    _write_slot(into, 'reader', thread)
    t = _trace()
    p = t.emit(Ops.NOC_READ, (_dram(buffer), _vec(offset).node, into.index()), (size,), 'void', thread)
    done = t.record_effect(p, (into,))
    into.root.ready = True
    return into

  def multicast(self, value, peer, *, thread=None):
    if not isinstance(peer, PeerEndpoint) or peer.ring.owner is not _trace(): raise ValueError('invalid peer endpoint')
    if value.root.kind != 'L1' or value.extent != peer.ring.spec.item or value.dtype != peer.ring.dtype:
      raise ValueError('multicast requires matching L1 item layout')
    value.check()
    value.root.consume()
    if value.root.ring.spec.slot != peer.ring.spec.slot or value.root.ring.spec.depth != peer.ring.spec.depth:
      raise ValueError('multicast requires matching source and peer CB slot/depth')
    target = UOp(Ops.INDEX, (peer.ring.node, value.root.sequence), (value.extent,))
    t = _trace()
    issue = t.emit(Ops.NOC_WRITE, (value.index(), target, *(_vec(v).node for v in peer.coordinates)),
                   (peer.group,), thread=thread)
    return t.record_effect(issue, (value,), writes=())

  def write(self, value, buffer, *, offset=0, thread=None, after=None, noc=1):
    if noc not in (0, 1): raise ValueError('invalid output NoC')
    if after is not None and (not isinstance(after, UOp) or after not in _trace().nodes or after.op not in (*ISSUES, Ops.LOAD, Ops.END)):
      raise ValueError('ordering dependency must be a completion from this trace')
    low, high = _bounds(offset)
    if low < 0 or high + value.extent > buffer.nbytes: raise ValueError('write out of bounds')
    _read_slot(value, 'writer', thread)
    t = _trace()
    p = t.emit(Ops.NOC_WRITE, (value.index(*((after,) if after is not None else ())), _dram(buffer), _vec(offset).node), (value.extent, noc), 'void', thread)
    done = t.record_effect(p, (value,), writes=())
    value.root.release()
    return done


noc = _NoC()


def unpack(item, *, into, thread=None):
  if item.root.kind != 'L1': raise TypeError('unpack requires L1 input')
  if into.root.kind not in ('DST', 'SRCA', 'SRCB'): raise TypeError('invalid unpack target')
  source = into.root.kind in ('SRCA', 'SRCB')
  _read_slot(item, 'unpack', thread)
  if source: _write_slot(into, 'unpack', thread)
  done = _trace().issue(Ops.UNPACK, (item, into), thread=thread)
  if source: into.root.ready = True
  return done


def pack(value, *, into, accumulate=False, thread=None):
  if value.root.kind != 'DST' or into.root.kind != 'L1': raise TypeError('pack requires Dst to L1')
  if accumulate:
    if into.root.ring.spec.depth != 1 or into.root.ring.spec.producer != 'local':
      raise ValueError('pack accumulation requires a local depth-one ring')
    _read_slot(into, 'pack', thread)
    done = _trace().issue(Ops.PACK, (value, into), (PackArgs(True),), thread)
    previous = into
    into = RingItem(previous.ring)
    into.sequence = previous.sequence
    into.state = into.last_effect = done
    previous.release()
  else:
    _write_slot(into, 'pack', thread)
    done = _trace().issue(Ops.PACK, (value, into), (PackArgs(False),), thread=thread)
  into.root.ready = True
  return into if accumulate else done


class _FPU:
  def move(self, value, *, into, thread=None):
    """Copy a held Src item to Dst without releasing its bank."""
    if value.root.kind not in ('SRCA', 'SRCB') or into.root.kind != 'DST':
      raise TypeError('FPU move requires SrcA/SrcB to Dst')
    if value.extent != into.extent: raise ValueError('move extents must match')
    _read_slot(value, 'math', thread)
    return _trace().issue(Ops.MOVE, (value, into), thread=thread)

  def op(self, op, a, b, *, into, accumulate=False, shape=(32, 32, 32), thread=None, **modifiers):
    opcode = {'add': Ops.FPU_ELW, 'sub': Ops.FPU_ELW, 'mul': Ops.FPU_ELW,
              'mvmul': Ops.FPU_MATMUL, 'gapool': Ops.FPU_POOL, 'gmpool': Ops.FPU_POOL}[op]
    if a.root.kind != 'SRCA' or b.root.kind != 'SRCB' or into.root.kind != 'DST':
      raise TypeError('FPU requires SrcA, SrcB and Dst')
    for bank in (a, b): _read_slot(bank, 'math', thread)
    return _trace().issue(opcode, (a, b, into), (FPUArgs(op, accumulate, tuple(sorted(modifiers.items())), shape),), thread)


fpu = _FPU()


class _SFPU:
  def const(self, value): return Vec(UOp(Ops.CONST, arg=(float(value),), dtype='f32.vec(32)'))
  def const_bits(self, bits): return _vec(struct.unpack('<f', struct.pack('<I', bits))[0])
  def lanes(self, view):
    if view.extent != 1: raise ValueError('lanes requires one 128-element block')
    return tuple((view, p) for p in range(4))
  def load(self, lanes):
    view, position = lanes
    if view.root.kind != 'DST': raise TypeError('SFPU load requires Dst')
    load = _trace().emit(Ops.LOAD, (view.index(),), (position,), 'f32.vec(32)')
    view.root.state = view.root.last_effect = load
    return Vec(load)
  def store(self, value, lanes):
    view, position = lanes
    if view.root.kind != 'DST': raise TypeError('SFPU store requires Dst')
    # The value is an explicit dependency of the issue, not only program order.
    t = _trace(); view.check()
    p = t.emit(Ops.STORE, (_vec(value).node, view.index()), (position,), 'void', None)
    return t.record_effect(p, (view,))
  def mul(self, a, b, *, mod=0): return Vec(_trace().emit(Ops.MUL, (_vec(a).node, _vec(b).node), (mod,), 'f32.vec(32)', None))
  def mad(self, a, b, c, *, mod=0): return Vec(_trace().emit(Ops.MULACC, tuple(_vec(x).node for x in (a,b,c)), (mod,), 'f32.vec(32)', None))
  def shft(self, x, imm, mod): return Vec(_trace().emit(Ops.SHFT, (_vec(x).node,), (imm,mod), 'f32.vec(32)', None))
  def iadd(self, a, b, mod): return Vec(_trace().emit(Ops.IADD, (_vec(a).node, _vec(b).node), (mod,), 'f32.vec(32)', None))
  def shft2(self, x, mod): return Vec(_trace().emit(Ops.SHFT2, (_vec(x).node,), (mod,), 'f32.vec(32)', None))
  def transp(self, *values):
    if len(values) != 4: raise ValueError('transpose requires four vectors')
    node = _trace().emit(Ops.TRANSP, tuple(_vec(v).node for v in values), dtype='f32.vec(32)', thread=None)
    return tuple(Vec(_trace().emit(Ops.GEP, (node,), (i,), 'f32.vec(32)')) for i in range(4))
  def lane_sum(self, value):
    for count in (4,2,1):
      other = value
      for _ in range(count): other = self.shft2(other, 3)
      value = value + other
    a,b,c,d = self.transp(value,value,value,value)
    return a+b+c+d
  def rsqrt(self, x):
    y = self.iadd(self.const_bits(0x5f1110a0), self.shft(x, 0xfff, 1), 6)
    t = self.mul(y, x*y, mod=1)
    y = y*self.mad(t, 2.2533049+t, 2.2825186)
    t = 1.0+self.mul(y, x*y, mod=1)
    return self.mad(t, y*0.5, y)


sfpu = _SFPU()


def loop(count, body, *, carry=None, name=None):
  """Trace once. Repetition form is left to future hardware lowering."""
  if type(count) is not int or count < 0: raise ValueError('loop requires a nonnegative static count')
  if count == 0: return carry
  t = _trace()
  reg = initial = None
  if carry is not None:
    carry = _vec(carry)
    reg = t.define(StorageSpec('REG', 32, carry.node.dtype), dtype=carry.node.dtype)
    initial = t.emit(Ops.STORE, (reg, carry.node), dtype='void')
  before_states = {v: (v.state, v.last_effect) for v in t.resources}
  start = len(t.nodes)
  r = t.emit(Ops.RANGE, (_vec(count).node,), arg=(name,), dtype='i32', queue=None)
  t.regions.append(r)
  t.scopes[r] = tuple(t.regions)
  try:
    if carry is None: body(Vec(r))
    else:
      incoming = Vec(t.emit(Ops.LOAD, (reg.after(initial),), dtype=carry.node.dtype))
      out = _vec(body(Vec(r), incoming))
      if out.node.dtype != carry.node.dtype: raise TypeError('loop carry dtype changed')
      carry_store = t.emit(Ops.STORE, (reg, out.node), dtype='void')
    for resource in t.resources:
      if isinstance(resource, RingItem) and r in resource.region and not resource.closed and not resource.retain:
        resource.finish_release()
  finally:
    t.regions.pop()
  body_nodes = tuple(t.nodes[start+1:])
  referenced = {s for n in body_nodes for ancestor in n.toposort() for s in ancestor.src}
  terminals = [n for n in body_nodes if n not in referenced]
  changed = [v for v,(state,effect) in before_states.items() if v.state is not state or v.last_effect is not effect]
  # Expose both the producer version and final reader effect as needed. A held
  # read-only item keeps its writer version while its last effect closes here.
  effects = [node for v in changed for node,previous in zip((v.state,v.last_effect),before_states[v]) if node is not previous]
  targets = list(dict.fromkeys([*terminals, *effects,
                               *((carry_store,) if carry is not None else ())]))
  ends = {}
  for target in targets:
    ends[target] = target.end(r)
    t.scope(ends[target])
  t.nodes[start:] = list(ends.values())
  for resource in changed:
    state,effect = before_states[resource]
    if resource.state is not state: resource.state = ends[resource.state]
    if resource.last_effect is not effect: resource.last_effect = ends[resource.last_effect]
  if carry is not None:
    return Vec(t.emit(Ops.LOAD, (reg.after(ends[carry_store]),), dtype=carry.node.dtype))
  return None



@dataclass(frozen=True)
class PeerEndpoint:
  ring: Ring
  group: PeerGroup
  coordinates: tuple  # x0, y0, x1, y1, sender_x, sender_y


class _CB:
  def read(self, buffer, *, item_size=None, capacity=3, resident=False):
    item_size = 1024 * (2 if buffer.dtype is Dtype.bf16 else 4) if item_size is None else item_size
    return Stream(buffer, item_size, capacity, resident)

  def peer(self, name, *, receivers, coordinates, slot, item_size=2048, capacity=3, dtype=Dtype.bf16):
    if len(coordinates) != 6: raise ValueError('peer coordinates require rectangle and sender xy')
    for value in coordinates:
      low, high = _bounds(value)
      if not 0 <= low <= high < 64: raise ValueError('peer coordinates out of range')
    return PeerEndpoint(self.alloc(slot=slot, producer='peer', item_size=item_size, capacity=capacity, dtype=dtype),
                        PeerGroup(name, receivers), tuple(coordinates))

  def alloc(self, *, kind='L1', item_size=None, capacity=None, dtype=Dtype.bf16, slot=None, producer='local', storage=None):
    if item_size is None: item_size = (1024 * (2 if dtype is Dtype.bf16 else 4)) if kind == 'L1' else 8
    return Ring(kind, item_size, (3 if kind == 'L1' else 2) if capacity is None else capacity, dtype,
                slot=slot, producer=producer, storage=storage)


cb = _CB()
