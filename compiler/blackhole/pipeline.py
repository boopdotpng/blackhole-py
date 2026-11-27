"""Allocated tile DAG -> one ordered stream -> synchronization -> five images."""
from ..dtype import dtypes
from ..uop import Ops, UOp, linearize
from ..isa.tensix import split_roles, pack_bundle
from .specs import UnpackOp, PackOp, SemOp, StallOp, FpuOp, NocRead, NocGather, IndexTile, NocWrite, NocScatter, NocWait, CbOp, DstZero
from .recipes import compile_core


def instruction(spec, *src, dtype=dtypes.void):
  return UOp.ins(spec, src, dtype, role=spec.role)


def insert_syncs(stream):
  """Match input credits and Dst ownership in the one joint ordered stream.

  An output phase owns Dst until pack completes. Within it, each unpack/math
  step returns its input credit independently, allowing K/reduction loops to
  reuse scratch tiles without releasing the accumulated destination.
  """
  from .specs import MoveToDst
  before, after = {}, {}
  def add(table, at, *ops): table.setdefault(at, []).extend(ops)
  def sem(kind, index, role): return instruction(SemOp(kind, index, role))
  active, stack, ends = {}, [], {}
  for i, u in enumerate(stream):
    active[i] = tuple(stack)
    if u.op is Ops.RANGE: stack.append(i)
    elif u.op is Ops.END:
      for r in u.src[1:]:
        start = next(j for j in reversed(stack) if stream[j] is r)
        ends[start] = i
        stack.remove(start)
  def spec_at(i, cls): return stream[i].is_ins and isinstance(stream[i].ins_op, cls)
  def footprint(i): return stream[i].op is Ops.RANGE and stream[i].arg.name == "fp"
  packs = [i for i in range(len(stream)) if spec_at(i, PackOp)]
  if not packs: raise NotImplementedError("tile kernel requires an output pack")
  # Consecutive packs of a single destination group share the same ownership.
  groups = []
  for i in packs:
    if groups and not any(footprint(j) or spec_at(j, (UnpackOp, FpuOp, DstZero, MoveToDst))
                          for j in range(groups[-1][-1] + 1, i)):
      groups[-1].append(i)
    else: groups.append([i])
  previous = -1
  for group in groups:
    first, last = group[0], group[-1]
    work = [i for i in range(previous + 1, first) if footprint(i) or spec_at(i, (UnpackOp, FpuOp, DstZero, MoveToDst))]
    if not work: raise ValueError("pack without a producing phase")
    begin = work[0]
    inner = [r for r in active[begin] if r not in active[first]]
    if inner: begin = min(inner)
    initializes = footprint(work[0]) and any(spec_at(i, UnpackOp) for i in work)
    add(before, begin, sem("wait", 4, "trisc0"), sem("get", 4, "trisc0"))
    if initializes:
      add(before, begin, sem("wait", 0, "trisc0"), sem("get", 0, "trisc0"))
      add(after, ends[work[0]], instruction(StallOp("math", "trisc1")), sem("post", 0, "trisc1"))
    add(before, begin, sem("post", 6, "trisc0"),
                       sem("wait", 6, "trisc1"), sem("get", 6, "trisc1"))
    pending = []
    for wi, i in enumerate(work):
      if spec_at(i, UnpackOp): pending.append(i)
      elif footprint(i) or spec_at(i, (FpuOp, MoveToDst)):
        if pending:
          add(before, pending[0], sem("wait", 0, "trisc0"), sem("get", 0, "trisc0"))
          add(after, pending[-1], sem("post", 2, "trisc0"))
          add(before, i, sem("wait", 2, "trisc1"), sem("get", 2, "trisc1"))
          release = ends[i] if footprint(i) else i
          # MOVA2D and an unpack to Dst share a write port, even for disjoint
          # rows. Order each conversion before the next unpack. For the last
          # conversion, retain its credit through the SFPU consumer so the
          # following K iteration cannot overwrite that input prematurely.
          if spec_at(i, MoveToDst) and wi + 1 < len(work) and footprint(work[wi + 1]):
            release = ends[work[wi + 1]]
          add(after, release, instruction(StallOp("math", "trisc1")), sem("post", 0, "trisc1"))
          pending.clear()
    if pending: raise ValueError("unpack without consuming math")
    add(before, first, instruction(StallOp("math", "trisc1")), sem("post", 1, "trisc1"),
                       sem("wait", 1, "trisc2"), sem("get", 1, "trisc2"))
    add(after, last, instruction(StallOp("pack", "trisc2")), sem("post", 4, "trisc2"))
    previous = last
  readers = {u.ins_op.cb_id: i for i, u in enumerate(stream) if u.is_ins and isinstance(u.ins_op, (NocRead, NocGather, IndexTile))}
  writers = {u.ins_op.cb_id for u in stream if u.is_ins and isinstance(u.ins_op, (NocWrite, NocScatter))}
  producers = {u.ins_op.cb_id: i for i, u in enumerate(stream) if u.is_ins and isinstance(u.ins_op, PackOp)}
  static = set(producers) - writers
  for cb_id in static:
    consumers = [i for i, u in enumerate(stream) if u.is_ins and isinstance(u.ins_op, UnpackOp) and u.ins_op.cb_id == cb_id]
    if not consumers: continue
    producer = producers[cb_id]
    add(before, producer, instruction(CbOp("reserve", cb_id, "trisc2")))
    add(after, producer, instruction(CbOp("push", cb_id, "trisc2")))
    for i in consumers:
      inner = [r for r in active[i] if r not in active[producer]]
      add(before, min(inner) if inner else i, instruction(CbOp("wait", cb_id, "trisc0")))
    last = consumers[-1]
    inner = [r for r in active[last] if r not in active[producer]]
    if inner: last = ends[min(inner)]
    add(after, last, instruction(CbOp("pop", cb_id, "trisc0")))
  for i, u in enumerate(stream):
    if not u.is_ins: continue
    spec = u.ins_op
    def cb(kind): return instruction(CbOp(kind, spec.cb_id, spec.role))
    if isinstance(spec, IndexTile):
      add(before, i, cb("reserve")); add(after, i, cb("push"))
    elif isinstance(spec, (NocRead, NocGather, NocWrite, NocScatter)):
      add(before, i, cb("reserve" if isinstance(spec, (NocRead, NocGather, IndexTile)) else "wait"))
      add(after, i, instruction(NocWait(spec.tid, True, spec.role)), cb("push" if isinstance(spec, (NocRead, NocGather, IndexTile)) else "pop"))
    elif isinstance(spec, UnpackOp) and spec.cb_id in readers:
      inner = [r for r in active[i] if r not in active[readers[spec.cb_id]]]
      add(before, min(inner) if inner else i, cb("wait"))
      add(after, ends[min(inner)] if inner else i, cb("pop"))
    elif isinstance(spec, PackOp) and spec.cb_id in writers:
      add(before, i, cb("reserve")); add(after, i, cb("push"))
  return [item for i, u in enumerate(stream) for item in (*before.get(i, ()), u, *after.get(i, ()))]


def compile_tile_graph(sink, cb_addrs):
  joint = linearize(sink)
  synced = insert_syncs(joint)
  cores = split_roles(synced)
  compiled, images = [], {}
  for core in cores.src:
    code, binary = compile_core(list(core.src), core.arg, cb_addrs)
    compiled.append(UOp.linear(*code, arg=core.arg))
    images[core.arg] = binary
  return UOp.program(sink, UOp.linear(*compiled, arg="blackhole"), UOp.source(""), UOp.binary(pack_bundle(images)))
