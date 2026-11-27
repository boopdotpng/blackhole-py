"""Allocated tile DAG -> one ordered stream -> synchronization -> five images."""
from ..dtype import dtypes
from ..uop import Ops, UOp, linearize
from ..isa.tensix import split_roles, pack_bundle
from .specs import Space, MoveToDst, SfpLoadOp, SfpStoreOp, UnpackOp, PackOp, SemOp, StallOp, FpuOp, NocRead, NocGather, IndexTile, NocWrite, NocScatter, NocWait, CbOp, DstZero
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
  # A converted input can remain live across several SFPU phases. Returning
  # sem 0 after MOVA2D is necessary for the next unpack to use the shared
  # write port, but must not let trisc0 start the next loop iteration early.
  # Fence the owning loop, independently of the per-unpack port handshake.
  protected = set()
  for i, u in enumerate(stream):
    if not (spec_at(i, MoveToDst) or spec_at(i, UnpackOp) and u.ins_op.target is Space.DST): continue
    scope = active[i]
    if not scope: continue  # sem 4 protects an unlooped ownership window
    slot = u.ins_op.dst_slot
    if any(spec_at(j, SfpLoadOp) and stream[j].ins_op.dst_slot == slot
           for j in range(i + 1, ends[scope[-1]])):
      protected.add(scope[-1])
  for start in sorted(protected):
    add(before, ends[start], instruction(StallOp("math", "trisc1")), sem("post", 5, "trisc1"),
        sem("wait", 5, "trisc0"), sem("get", 5, "trisc0"))
  pops = {}
  def consumer_end(i):
    for j in range(i + 1, len(stream)):
      if footprint(j): return ends[j]
      if spec_at(j, FpuOp): return j
    raise ValueError("unpack without a consuming phase")
  def pop_after(i, cb_id, role):
    pops.setdefault(i, []).append(instruction(CbOp("pop", cb_id, role)))
  readers = {u.ins_op.cb_id: i for i, u in enumerate(stream) if u.is_ins and isinstance(u.ins_op, (NocRead, NocGather, IndexTile))}
  writers = {u.ins_op.cb_id for u in stream if u.is_ins and isinstance(u.ins_op, (NocWrite, NocScatter))}
  producers = {u.ins_op.cb_id: i for i, u in enumerate(stream) if u.is_ins and isinstance(u.ins_op, PackOp)}
  static = set(producers) - writers
  for cb_id in static:
    consumers = [i for i, u in enumerate(stream) if u.is_ins and isinstance(u.ins_op, UnpackOp) and u.ins_op.cb_id == cb_id]
    if not consumers: continue
    producer = producers[cb_id]
    producer_loops = [r for r in active[producer] if all(r not in active[i] for i in consumers)]
    reserve = min(producer_loops) if producer_loops else producer
    push = ends[reserve] if producer_loops else producer
    add(before, reserve, instruction(CbOp("reserve", cb_id, "trisc2")))
    add(after, push, instruction(CbOp("push", cb_id, "trisc2")))
    for i in consumers:
      inner = [r for r in active[i] if r not in active[producer]]
      add(before, min(inner) if inner else i, instruction(CbOp("wait", cb_id, "trisc0")))
    last = consumers[-1]
    consumer = consumer_end(last)
    inner = [r for r in active[last] if r not in active[producer]]
    if inner: last = ends[min(inner)]
    pop_after(max(last, consumer), cb_id, "trisc0")
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
      pop_after(ends[min(inner)] if inner else consumer_end(i), spec.cb_id, spec.role)
    elif isinstance(spec, PackOp) and spec.cb_id in writers:
      add(before, i, cb("reserve")); add(after, i, cb("push"))
  for at, operations in pops.items():
    # UNPACR is asynchronous. A queue cannot become reusable until math has
    # consumed its input; an RV-side pop immediately after issuing unpack
    # lets a later producer overwrite L1 before the engine has read it.
    add(after, at, instruction(StallOp("math", "trisc1")), sem("post", 7, "trisc1"),
        sem("wait", 7, "trisc0"), sem("get", 7, "trisc0"), *operations)
  return [item for i, u in enumerate(stream) for item in (*before.get(i, ()), u, *after.get(i, ()))]


def verify_tile_stream(stream):
  """Check lexical credit conservation before projecting onto concurrent cores.

  Waits observe CB readiness without consuming it: static stages can have
  several waits for one push/pop. Semaphore gets, in contrast, consume credit.
  This verifies counts and loop scopes, not arbitrary cross-core deadlocks.
  """
  from collections import Counter, defaultdict
  stack, semaphores, buffers = [], defaultdict(Counter), defaultdict(Counter)
  for u in stream:
    if u.op is Ops.RANGE:
      stack.append(u)
      continue
    if u.op is Ops.END:
      for r in u.src[1:]:
        if not stack or stack[-1] is not r: raise ValueError("unbalanced tile loop")
        stack.pop()
      continue
    if not u.is_ins: continue
    spec = u.ins_op
    scope = tuple(stack)
    if isinstance(spec, SemOp):
      if spec.kind not in ("wait", "get", "post"): raise ValueError("unknown semaphore operation")
      semaphores[scope, spec.sem_id][spec.kind] += 1
    elif isinstance(spec, CbOp):
      if spec.kind not in ("reserve", "push", "wait", "pop"): raise ValueError("unknown CB operation")
      buffers[scope, spec.cb_id][spec.kind] += 1
    if isinstance(spec, (UnpackOp, PackOp, MoveToDst, SfpLoadOp, SfpStoreOp, FpuOp)):
      count = spec.blocks if isinstance(spec, PackOp) else spec.m_blocks * spec.n_blocks if isinstance(spec, FpuOp) else 1
      if spec.dst_slot < 0 or spec.dst_slot + count > 56: raise MemoryError("tile stream exceeds 56 Dst slots")
  if stack: raise ValueError("unterminated tile loop")
  for (_, sem_id), counts in semaphores.items():
    if not counts["wait"] == counts["get"] == counts["post"]:
      raise ValueError(f"unbalanced semaphore {sem_id} in loop scope: {dict(counts)}")
  for (_, cb_id), counts in buffers.items():
    if not counts["reserve"] == counts["push"] == counts["pop"] or counts["wait"] < counts["pop"]:
      raise ValueError(f"unbalanced CB {cb_id} in loop scope: {dict(counts)}")


def compile_tile_graph(sink, cb_addrs, cb_sizes=None):
  joint = linearize(sink)
  synced = insert_syncs(joint)
  verify_tile_stream(synced)
  if cb_sizes is not None:
    from .alloc import allocate_cb_stream
    synced, cb_addrs = allocate_cb_stream(synced, cb_sizes)
    verify_tile_stream(synced)
  cores = split_roles(synced)
  compiled, images = [], {}
  for core in cores.src:
    code, binary = compile_core(list(core.src), core.arg, cb_addrs)
    compiled.append(UOp.linear(*code, arg=core.arg))
    images[core.arg] = binary
  return UOp.program(sink, UOp.linear(*compiled, arg="blackhole"), UOp.source(""), UOp.binary(pack_bundle(images)))
