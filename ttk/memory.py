"""Infer finite storage hazards from INDEX/AFTER and operation access modes.

This is verification, not device lowering. Edges refer to abstract operation
completion. No WAIT, CB counter or source-bank synchronization is emitted.
"""
from dataclasses import dataclass, field
from .uop import Ops, UOp, base, is_ring, PackArgs, ParamArg, execution_queue
from .linearize import linearize
from .loops import bounds


@dataclass(frozen=True)
class Item:
  storage: UOp
  sequence: UOp
  offset: tuple[int,int]
  extent: int
  dependencies: tuple[UOp, ...] = ()


def item(index):
  """Decode an occupancy INDEX, optionally followed by a subview INDEX."""
  dependencies = []
  def unwrap(n):
    while n.op is Ops.AFTER:
      dependencies.extend(n.src[1:]); n = n.src[0]
    return n
  index = unwrap(index)
  if index.op is not Ops.INDEX: return None
  root = unwrap(index.src[0])
  if is_ring(root): return Item(root,index.src[1],(0,0),index.arg[0],tuple(dependencies))
  parent = item(root)
  if parent is None: return None
  low,high = bounds(index.src[1])
  return Item(parent.storage,parent.sequence,(parent.offset[0]+low,parent.offset[1]+high),index.arg[0],(*parent.dependencies,*dependencies))


@dataclass(frozen=True)
class Access:
  operation: UOp
  item: Item
  write: bool
  accumulate: bool = False


def accesses(sink):
  result = []
  for op in linearize(sink):
    operands = []
    if op.op is Ops.NOC_READ and len(op.src) >= 3:
      operands = [(op.src[2],True,False)]
    elif op.op is Ops.NOC_WRITE and len(op.src) >= 2:
      operands = [(op.src[0],False,False),(op.src[1],True,False)]
    elif op.op is Ops.UNPACK:
      operands = [(op.src[0],False,False),(op.src[1],True,False)]
    elif op.op is Ops.PACK:
      accumulate = bool(op.arg and isinstance(op.arg[0],PackArgs) and op.arg[0].accumulate)
      operands = [(op.src[1],True,accumulate)]
    elif op.op in (Ops.MOVE,Ops.FPU_ELW,Ops.FPU_MATMUL,Ops.FPU_POOL,Ops.FPU_DOTPV):
      operands = [(s,False,False) for s in op.src[:-1]]
    for index,write,accumulate in operands:
      if (view := item(index)) is not None: result.append(Access(op,view,write,accumulate))
  return result


@dataclass
class Occupancy:
  writes: list[Access] = field(default_factory=list)
  reads: list[Access] = field(default_factory=list)
  credit: UOp | None = None


@dataclass
class Inference:
  edges: dict
  items: dict    # storage DEFINE -> sequence integer -> Occupancy


def infer(sink):
  nodes = linearize(sink)
  storages = [n for n in nodes if is_ring(n)]
  items = {s:{} for s in storages}
  edges = {}
  def require(op,*deps): edges[op] = (*edges.get(op,()),*deps)
  # Validate the DRAM bounds after sequence placeholders and loops are resolved.
  for n in nodes:
    if n.op is Ops.NOC_READ and len(n.src) >= 3:
      desc = base(n.src[0]).arg[0]
      if not isinstance(desc,ParamArg) or desc.scalar: raise ValueError('NOC_READ requires a DRAM buffer')
      low,high = bounds(n.src[1])
      if low < 0 or high+n.arg[0] > desc.nbytes: raise ValueError('stream exhausted / DRAM read out of bounds')
    if n.op is Ops.NOC_WRITE and len(n.src) >= 3 and base(n.src[1]).op is Ops.PARAM:
      desc = base(n.src[1]).arg[0]
      low,high = bounds(n.src[2])
      if desc.scalar or low < 0 or high+n.arg[0] > desc.nbytes: raise ValueError('DRAM write out of bounds')
  records = accesses(sink)
  for access in records:
    view,op = access.item,access.operation
    low,high = bounds(view.sequence)
    if low != high or low < 0: raise ValueError('occupancy sequence must expand to a nonnegative integer')
    spec = view.storage.arg[0]
    if view.offset[0] < 0 or view.extent <= 0 or view.offset[1]+view.extent > spec.item: raise ValueError('item view out of bounds')
    if access.write and (view.offset != (0,0) or view.extent != spec.item): raise ValueError('partial item writes are unsupported')
    occupancy = items[view.storage].setdefault(low,Occupancy())
    (occupancy.writes if access.write else occupancy.reads).append(access)
  # Alias identities share physical occupancy, but a second initializing write
  # cannot masquerade as a handoff. An AFTER dependency exposes the original data.
  aliases = {}
  for storage in storages:
    spec = storage.arg[0]
    if spec.storage is not None: aliases.setdefault(spec.storage,[]).append(storage)
  for group in aliases.values():
    if len(group) > 1 and any(s.arg[0].producer != 'local' for s in group): raise ValueError('aliases require local storage')
    layouts = {(s.arg[0].kind,s.arg[0].item,s.arg[0].depth,s.arg[0].dtype) for s in group}
    if len(layouts) != 1 or next(iter(layouts))[2] != 1: raise ValueError('aliases require matching depth-one layouts')
    shared = {}
    for s in group:
      for seq, occ in items[s].items():
        merged = shared.setdefault(seq,Occupancy())
        merged.writes.extend(occ.writes); merged.reads.extend(occ.reads)
    order = {n:i for i,n in enumerate(nodes)}
    for occ in shared.values():
      occ.writes.sort(key=lambda a:order[a.operation]); occ.reads.sort(key=lambda a:order[a.operation])
    for s in group: items[s] = shared
  checked = set()
  for storage, sequence in items.items():
    if id(sequence) in checked: continue
    checked.add(id(sequence))
    spec = storage.arg[0]
    writers = sorted(seq for seq,occ in sequence.items() if occ.writes)
    readers = sorted(seq for seq,occ in sequence.items() if occ.reads)
    if writers and writers != list(range(len(writers))): raise ValueError('writer sequence must be FIFO 0,1,2,...')
    if readers and readers != list(range(len(readers))): raise ValueError('reader sequence must be FIFO 0,1,2,...')
    for previous,current in zip(writers,writers[1:]):
      require(sequence[current].writes[0].operation,sequence[previous].writes[-1].operation)
    consumers = {}
    for seq in readers:
      for read in sequence[seq].reads:
        thread = read.operation.thread or execution_queue(read.operation.op)
        consumers.setdefault(thread,{}).setdefault(seq,read.operation)
    for reader_items in consumers.values():
      ordered = [reader_items[seq] for seq in sorted(reader_items)]
      for previous,current in zip(ordered,ordered[1:]): require(current,previous)
    for seq,occ in sorted(sequence.items()):
      if spec.producer == 'remote':
        if occ.writes: raise ValueError('remote storage cannot be written locally')
        if not spec.sender: raise ValueError('remote storage requires sender endpoint')
        # Reservation exists only in the private hazard model. It is independent
        # of the remote data completion, so both peers can exchange credits.
        deps = occ.reads[0].item.dependencies
        occ.credit = storage.after(UOp(Ops.CONST,arg=(seq,),dtype='i32'),*deps)
      elif spec.producer == 'peer':
        if occ.reads: raise ValueError('peer destination cannot be read locally')
      elif not occ.writes:
        raise ValueError('read of an item without a producer')
      if occ.writes:
        if occ.writes[0].accumulate: raise ValueError('accumulation requires initialized storage')
        for previous,current in zip(occ.writes,occ.writes[1:]):
          if not current.accumulate: raise ValueError('overlapping item/aliased storage writes')
          require(current.operation,previous.operation)
        # A read sees the most recent writer explicitly named in its dependencies;
        # ordinary single-writer items require that producer completion implicitly.
        for read in occ.reads:
          ancestors = set(read.operation.toposort())
          visible = [w for w in occ.writes if w.operation in ancestors]
          writer = visible[-1] if visible else occ.writes[-1]
          require(read.operation,writer.operation)
        for previous,current in zip(occ.writes,occ.writes[1:]):
          for read in occ.reads:
            if previous.operation in read.operation.toposort() and current.operation not in read.operation.toposort():
              require(current.operation,read.operation)
      if seq >= spec.depth and spec.producer != 'peer':
        previous = sequence.get(seq-spec.depth)
        if previous is None or not previous.reads: raise ValueError('storage capacity would overwrite an unread item')
        target = occ.credit if spec.producer == 'remote' else occ.writes[0].operation
        require(target,*(read.operation for read in previous.reads))
  return Inference(edges,items)
