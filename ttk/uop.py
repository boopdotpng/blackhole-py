"""Data/effect graph. No device encoding or synchronization lowering.

Pure nodes are shared within a trace; issues, loads and loop regions
have occurrence identity: two identical issues are two executions. State and
completion edges are explicit. Verification here is structural, not a hardware
safety proof. AFTER requires operation results; concrete synchronization belongs
to later lowering passes.
"""
from dataclasses import dataclass
from contextvars import ContextVar
import struct
from enum import Enum, auto


class Ops(Enum):
  SINK = auto()
  CONST = auto(); PARAM = auto()
  DEFINE = auto()
  INDEX = auto(); AFTER = auto(); RANGE = auto(); END = auto()
  ADD = auto(); SUB = auto(); MUL = auto(); MULACC = auto(); IDIV = auto(); MOD = auto()
  SHFT = auto(); IADD = auto(); SHFT2 = auto(); TRANSP = auto(); GEP = auto()
  NOC_READ = auto(); NOC_WRITE = auto(); UNPACK = auto(); PACK = auto(); MOVE = auto()
  FPU_ELW = auto(); FPU_MATMUL = auto()
  FPU_POOL = auto(); FPU_DOTPV = auto()
  LOAD = auto(); STORE = auto()
  MACRO_DEFINE = auto(); MACRO_RUN = auto()
  REPLAY_DEFINE = auto(); REPLAY_RUN = auto(); MOP_DEFINE = auto(); MOP_RUN = auto()
  CFG_REQUIRE = auto(); CFG_WRITE = auto()


class Thread(Enum):
  BRISC = auto(); NCRISC = auto(); UNPACK = auto(); MATH = auto(); PACK = auto()


@dataclass(frozen=True)
class ParamArg:
  """Invocation-independent argument description; slot is the launch ABI order."""
  slot: int
  name: str
  dtype: str
  nbytes: int = 0
  lo: int | None = None
  hi: int | None = None

  @property
  def scalar(self): return self.lo is not None

  def __post_init__(self):
    if self.scalar:
      limits = {'i32': (-2**31, 2**31-1), 'u32': (0, 2**32-1)}
      if self.dtype not in limits or type(self.lo) is not int or type(self.hi) is not int:
        raise ValueError('scalar PARAM requires integer bounds and dtype')
      low, high = limits[self.dtype]
      if self.nbytes or not low <= self.lo <= self.hi <= high: raise ValueError('invalid scalar bounds')
    elif self.hi is not None or type(self.nbytes) is not int or self.nbytes <= 0:
      raise ValueError('buffer PARAM requires positive size')


@dataclass(frozen=True)
class RingSpec:
  kind: str                 # L1 bytes, SRCA/SRCB 128-element blocks per item
  item: int
  depth: int
  dtype: str
  slot: int | None = None
  producer: str = 'local'  # local storage, remote producer, or peer destination
  storage: str | None = None
  identity: int = 0         # logical allocation identity within a trace
  sender: tuple = ()       # remote sender xy: constants or bounded ParamArg descriptors
  receiver_thread: Thread | None = None

  def __post_init__(self):
    if self.sender:
      if self.producer != 'remote' or not isinstance(self.sender,tuple) or len(self.sender) != 2: raise ValueError('invalid sender endpoint')
      for coord in self.sender:
        low,high = (coord.lo,coord.hi) if isinstance(coord,ParamArg) and coord.scalar else (coord,coord)
        if type(low) is not int or type(high) is not int or not 0 <= low <= high < 64: raise ValueError('sender coordinate out of range')
    if self.receiver_thread is not None and not isinstance(self.receiver_thread,Thread): raise ValueError('invalid receiver thread')
    if self.producer not in ('local', 'remote', 'peer'): raise ValueError('invalid ring producer')
    if self.slot is not None and (type(self.slot) is not int or not 0 <= self.slot < 32): raise ValueError('invalid CB slot')
    if self.producer != 'local' and (self.kind != 'L1' or self.slot is None):
      raise ValueError('remote rings require L1 and a stable CB slot')
    if self.storage is not None and (self.kind != 'L1' or not isinstance(self.storage, str) or not self.storage):
      raise ValueError('storage identity requires L1 and a name')
    if self.kind not in ('L1', 'SRCA', 'SRCB'): raise ValueError('invalid ring kind')
    if type(self.item) is not int or self.item <= 0: raise ValueError('invalid ring item size')
    if type(self.depth) is not int or self.depth <= 0: raise ValueError('invalid ring depth')
    if self.kind != 'L1' and (self.depth != 2 or self.item > 8):
      raise ValueError('source rings require depth 2 and at most eight blocks per item')


@dataclass(frozen=True)
class StorageSpec:
  kind: str
  item: int
  dtype: str
  identity: int = 0

  def __post_init__(self):
    if self.kind not in ('DST', 'REG'): raise ValueError('invalid storage kind')
    if type(self.item) is not int or self.item <= 0: raise ValueError('invalid storage extent')


def base(node):
  while node.op is Ops.AFTER: node = node.src[0]
  return node


def is_storage(node, kind):
  node = base(node)
  return node.op is Ops.DEFINE and node.arg[0].kind == kind


def is_ring(node):
  return node.op is Ops.DEFINE and isinstance(node.arg[0], RingSpec)


@dataclass(frozen=True)
class PeerGroup:
  name: str
  receivers: int

  def __post_init__(self):
    if not self.name or type(self.receivers) is not int or self.receivers <= 0:
      raise ValueError('peer group requires a name and positive receiver count')


@dataclass(frozen=True)
class PackArgs:
  accumulate: bool = False


@dataclass(frozen=True)
class FPUArgs:
  kind: str
  accumulate: bool = False
  modifiers: tuple = ()
  shape: tuple[int, int, int] = (32, 32, 32)

  def __post_init__(self):
    if len(self.shape) != 3 or any(type(v) is not int or not 1 <= v <= 32 for v in self.shape):
      raise ValueError('matmul shape requires (m, n, k) extents in [1, 32]')


def execution_queue(op):
  if op is Ops.NOC_READ: return 'reader'
  if op is Ops.NOC_WRITE: return 'writer'
  if op is Ops.UNPACK: return 'unpack'
  if op is Ops.PACK: return 'pack'
  if op in (Ops.MOVE, Ops.FPU_ELW, Ops.FPU_MATMUL,
            Ops.FPU_POOL, Ops.FPU_DOTPV, Ops.LOAD,
            Ops.STORE, Ops.ADD, Ops.SUB, Ops.MUL, Ops.MULACC, Ops.IDIV,
            Ops.MOD, Ops.SHFT, Ops.IADD, Ops.SHFT2, Ops.TRANSP, Ops.GEP): return 'math'
  return None


# A trace owns the cache. Verification expansion and separate participants must
# retain independent allocation/execution identities. LOAD is never pure.
_intern = ContextVar('ttk_pure_nodes', default=None)
PURE = frozenset({Ops.CONST, Ops.PARAM, Ops.DEFINE, Ops.INDEX, Ops.AFTER,
                  Ops.ADD, Ops.SUB, Ops.MUL, Ops.MULACC, Ops.IDIV, Ops.MOD,
                  Ops.SHFT, Ops.IADD, Ops.SHFT2, Ops.TRANSP, Ops.GEP})


class _UOpMeta(type):
  def __call__(cls, op, src=(), arg=(), dtype='void', thread=None):
    cache = _intern.get()
    if cache is None or op not in PURE: return super().__call__(op, src, arg, dtype, thread)
    # Only integer identities: float +0 is not equivalent for signed zero/NaN.
    if op in (Ops.ADD, Ops.SUB) and dtype in ('i32', 'u32') and len(src) == 2 and not arg and thread is None:
      if src[1].op is Ops.CONST and src[1].arg == (0,) and src[0].dtype == dtype: return src[0]
      if op is Ops.ADD and src[0].op is Ops.CONST and src[0].arg == (0,) and src[1].dtype == dtype: return src[1]
    key_arg = tuple((type(v), struct.pack('!d', v) if type(v) is float else v) for v in arg)
    key = op, src, key_arg, dtype, thread
    if key not in cache: cache[key] = super().__call__(op, src, arg, dtype, thread)
    return cache[key]


@dataclass(frozen=True, eq=False)
class UOp(metaclass=_UOpMeta):
  op: Ops
  src: tuple['UOp', ...] = ()
  arg: tuple = ()
  dtype: str = 'void'
  thread: Thread | None = None

  def __post_init__(self):
    if not isinstance(self.op, Ops): raise TypeError('op must be Ops')
    if not isinstance(self.src, tuple) or any(not isinstance(x, UOp) for x in self.src):
      raise TypeError('src must be a tuple of UOps')
    if not isinstance(self.arg, tuple): raise TypeError('arg must be an immutable tuple')
    hash(self.arg)

  def after(self, *dependencies):
    """Forward this value/storage after dependencies; AFTER itself does not wait."""
    if not dependencies: return self
    root = self
    while root.op is Ops.AFTER:
      dependencies = (*root.src[1:], *dependencies)
      root = root.src[0]
    return UOp(Ops.AFTER, (root, *dict.fromkeys(dependencies)), dtype=self.dtype)

  def end(self, range_):
    """Close one structured RANGE after this body completes."""
    return UOp(Ops.END, (self, range_))

  def __bool__(self): raise TypeError('symbolic values cannot control Python branches')

  def toposort(self):
    result, visited, active = [], set(), set()
    stack = [(self, False)]
    while stack:
      node, finish = stack.pop()
      if finish:
        active.remove(node); visited.add(node); result.append(node)
      elif node not in visited:
        if node in active: raise ValueError('cyclic UOp graph')
        active.add(node); stack.append((node, True))
        stack.extend((x, False) for x in reversed(node.src))
    return result

  def __repr__(self): return self.pretty()

  def pretty(self):
    """Nested expression with shared-node bindings, like tinygrad's pretty_print.

    Iterative walks avoid Python's recursion limit on long protocol chains.
    This displays the authored graph; it neither sorts nor rewrites it.
    """
    counts, ids, visited = {}, {}, set()
    stack = [self]
    while stack:
      node = stack.pop()
      if node in visited: continue
      visited.add(node)
      ids.setdefault(node, len(ids))
      for src in node.src:
        counts[src] = counts.get(src, 0) + 1
        ids.setdefault(src, len(ids))
      stack.extend(reversed(node.src))

    lines, shown = [], set()
    stack = [('node', self, 0, '')]
    while stack:
      kind, node, depth, suffix = stack.pop()
      indent = ' ' * depth
      if kind == 'close':
        lines.append(indent + '))' + suffix)
        continue
      if node in shown:
        lines.append(indent + f'x{ids[node]}' + suffix)
        continue
      shown.add(node)
      binding = f'x{ids[node]}:=' if counts.get(node, 0) > 1 else ''
      thread = f', thread=Thread.{node.thread.name}' if node.thread is not None else ''
      dtype = f', dtype={node.dtype!r}' if node.dtype != 'void' else ''
      header = f'{indent}{binding}UOp(Ops.{node.op.name}{dtype}, arg={node.arg!r}{thread}, src=('
      if not node.src:
        lines.append(header + '))' + suffix)
      else:
        lines.append(header)
        stack.append(('close', node, depth, suffix))
        stack.extend(('node', src, depth + 2, ',') for src in reversed(node.src))
    return '\n'.join(lines)

  def dump(self):
    nodes = self.toposort(); ids = {n: i for i, n in enumerate(nodes)}
    return '\n'.join(f'%{ids[n]} = {n.op.name}(' + ', '.join(f'%{ids[s]}' for s in n.src)
                     + f') {n.arg!r} : {n.dtype}'
                     + (f' @{n.thread.name}' if n.thread else '') for n in nodes)


ISSUES = frozenset({Ops.NOC_READ, Ops.NOC_WRITE, Ops.UNPACK, Ops.PACK, Ops.MOVE,
                   Ops.FPU_ELW, Ops.FPU_MATMUL,
                   Ops.FPU_POOL, Ops.FPU_DOTPV,
                   Ops.STORE, Ops.MACRO_RUN,
                   Ops.REPLAY_RUN, Ops.MOP_RUN})


def _acyclic(root, extra):
  """Depth-first check that src edges plus `extra` wait-for edges form a DAG."""
  done, active, stack = set(), set(), [(root, False)]
  while stack:
    node, finish = stack.pop()
    if finish: active.remove(node); done.add(node); continue
    if node in done: continue
    if node in active: return False
    active.add(node); stack.append((node, True))
    stack.extend((d, False) for d in (*node.src, *extra.get(node, ())))
  return True


def _verify_execution(sink):
  """Validate shapes and infer finite RAW/WAR/capacity edges from memory accesses.

  INDEX sequences identify occupancies; AFTER records required operation results.
  Inferred edges are private to verification, not authored synchronization ops.
  """
  from .linearize import linearize
  nodes = linearize(sink)
  for node in nodes:
    if node.op in ISSUES and node.dtype != 'void':
      raise ValueError(f'{node.op.name} is a void operation')
    if node.op in (Ops.END, Ops.SINK) and node.dtype != 'void':
      raise ValueError(f'{node.op.name} is a void operation')
    if node.op is Ops.PARAM:
      if len(node.arg) != 1 or not isinstance(node.arg[0], ParamArg): raise ValueError('PARAM requires ParamArg')
      desc = node.arg[0]
      if node.dtype != (desc.dtype if desc.scalar else 'u32'): raise ValueError('incorrect PARAM dtype')
    if node.dtype in ('pending', 'done', 'slot', 'item', 'dram_addr', 'tuple'):
      raise ValueError('dtype must describe an element type, not a protocol role')
    if node.op is Ops.LOAD and (not node.src or node.dtype != (node.src[0].dtype if is_storage(node.src[0], 'REG') else 'f32.vec(32)')):
      raise ValueError('LOAD has incorrect value dtype')
    if node.op in (Ops.ADD, Ops.SUB, Ops.MUL, Ops.IDIV, Ops.MOD) and len(node.src) != 2:
      raise ValueError('binary arithmetic requires two operands')
    if node.op is Ops.MULACC and len(node.src) != 3: raise ValueError('MULACC requires three operands')
    if node.op is Ops.LOAD and len(node.src) != 1: raise ValueError('LOAD requires one source; use AFTER for state')
    if node.op is Ops.GEP:
      if not node.src or node.src[0].op is not Ops.TRANSP or len(node.arg) != 1 or type(node.arg[0]) is not int or not 0 <= node.arg[0] < 4:
        raise ValueError('GEP requires a transpose result and an index in [0, 4)')
    if node.op is Ops.INDEX:
      if len(node.src) != 2 or node.src[1].dtype not in ('i32', 'u32') or len(node.arg) != 1 or type(node.arg[0]) is not int or node.arg[0] <= 0:
        raise ValueError('INDEX requires root and integer offset')
    if node.op is Ops.END:
      if len(node.src) != 2 or node.src[1].op is not Ops.RANGE:
        raise ValueError('END requires a body and one RANGE')
    if node.op is Ops.AFTER:
      if len(node.src) < 2 or node.dtype != node.src[0].dtype:
        raise ValueError('AFTER requires a value and dependencies, preserving the value dtype')
    if node.op is Ops.DEFINE:
      if node.src or len(node.arg) != 1 or not isinstance(node.arg[0], (RingSpec, StorageSpec)):
        raise ValueError('DEFINE requires a storage spec and no sources')
      if node.dtype != (node.arg[0].dtype if is_storage(node, 'REG') else 'void'):
        raise ValueError('incorrect DEFINE dtype')
    if node.op is Ops.NOC_WRITE and node.arg and isinstance(node.arg[0], PeerGroup):
      if len(node.src) < 8 or any(base(s).op is not Ops.INDEX for s in node.src[:2]): raise ValueError('invalid peer write operands')
      target = base(base(node.src[1]).src[0])
      if not is_ring(target) or target.arg[0].producer != 'peer': raise ValueError('peer write requires peer storage')
  from .memory import infer
  extra = infer(sink).edges
  if not _acyclic(sink, extra): raise ValueError('storage capacity/order creates a dependency cycle')
  return extra


def verify(sink):
  from .loops import expand
  _verify_execution(expand(sink))


@dataclass(frozen=True)
class UPat:
  op: Ops | None = None
  name: str | None = None
  src: tuple['UPat', ...] | None = None

  def match(self, node, bindings=None):
    bindings = {} if bindings is None else dict(bindings)
    if self.op is not None and node.op is not self.op: return None
    if self.name:
      if self.name in bindings and bindings[self.name] is not node: return None
      bindings[self.name] = node
    if self.src is not None:
      if len(self.src) != len(node.src): return None
      for pattern, value in zip(self.src, node.src):
        bindings = pattern.match(value, bindings)
        if bindings is None: return None
    return bindings


class PatternMatcher:
  def __init__(self, rules): self.rules = tuple(rules)

  def rewrite(self, node):
    for pattern, callback in self.rules:
      match = pattern.match(node)
      if match is not None:
        result = callback(**match)
        if result is not None: return result
    return node


def graph_rewrite(sink, matcher):
  """One bottom-up rewrite sweep; shared occurrences remain shared."""
  mapped = {}
  for node in sink.toposort():
    src = tuple(mapped[s] for s in node.src)
    rebuilt = node if all(a is b for a, b in zip(src, node.src)) else UOp(node.op, src, node.arg, node.dtype, node.thread)
    mapped[node] = matcher.rewrite(rebuilt)
  return mapped[sink]
