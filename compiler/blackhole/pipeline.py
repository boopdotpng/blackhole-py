"""Allocated tile DAG -> one ordered stream -> synchronization -> five images."""
from ..dtype import dtypes
from ..uop import Ops, UOp, linearize
from ..isa.tensix import split_roles, pack_bundle
from .specs import Space, MoveToDst, SfpLoadOp, SfpStoreOp, UnpackOp, PackOp, SemOp, StallOp, FpuOp, NocRead, NocGather, IndexTile, NocWrite, NocScatter, NocWait, CbOp, DstZero, DstBank
from .recipes import compile_core


def instruction(spec, *src, dtype=dtypes.void):
  return UOp.ins(spec, src, dtype, role=spec.role)


def phase_defines_dst(stream, slots):
  """A bank switch is legal only when this phase defines its own inputs.

  Track even/odd column groups across footprint iterations. A possibly empty
  loop cannot establish definitions for code following its exit.
  """
  defined, entries, writes, footprint = set(), {}, set(), None
  for u in stream:
    if u.op is Ops.RANGE:
      entries[u] = defined.copy()
      if u.arg.name == "fp": footprint = u
      continue
    if u.op is Ops.END:
      for r in u.src[1:]:
        if r is footprint:
          defined.update(writes)
          writes.clear()
          footprint = None
        if r in entries and r.src[0].without_after.vmin < 1: defined.intersection_update(entries[r])
      continue
    if not u.is_ins: continue
    op = u.ins_op
    if isinstance(op, DstZero): defined.update(range(4 * slots))
    elif isinstance(op, (MoveToDst, UnpackOp)) and (isinstance(op, MoveToDst) or op.target is Space.DST):
      defined.update(range(op.dst_slot * 4, (op.dst_slot + 1) * 4))
    elif isinstance(op, (FpuOp, PackOp)):
      rows = range(op.dst_slot * 4, (op.dst_slot + dst_count(op)) * 4)
      if isinstance(op, FpuOp) and not op.accumulate: defined.update(rows)
      elif not defined.issuperset(rows): return False
    elif isinstance(op, (SfpLoadOp, SfpStoreOp)):
      bound = footprint.src[0].without_after if footprint is not None else None
      if bound is None or not bound.is_const: return False
      start = op.dst_slot * 4 + op.sub_row // 2
      rows = range(start, start + int(bound.val))
      if start < 0 or rows.stop > 4 * slots: return False
      if isinstance(op, SfpStoreOp): writes.update(rows)
      elif not defined.issuperset(rows): return False
  return True


def insert_syncs(stream, double_buffer=True):
  """Match input credits and Dst ownership in the one joint ordered stream.

  Math acquires a destination bank and pack releases it. Source operands use
  hardware valid bits. Direct unpack writes to Dst also need a grant from
  math because the two engines share the same write port.
  """
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
  # Rows above the tile footprint in each half are available for SFPU spills.
  # All participants derive bank parity from the same dynamic phase ordinal.
  scope = active[packs[0]]
  slots = max(u.ins_op.dst_slot + dst_count(u.ins_op) for u in stream if u.is_ins and hasattr(u.ins_op, "dst_slot"))
  rectangular = all(not stream[r].src[0].without_after.ranges for r in scope[1:])
  repeated = len(groups) > 1 or any(stream[r].src[0].without_after.vmax > 1 for r in scope)
  banked = double_buffer and slots <= 32 and repeated and rectangular and all(active[p] == scope for p in packs)
  previous = -1
  for phase, group in enumerate(groups):
    first, last = group[0], group[-1]
    work = [i for i in range(previous + 1, first) if footprint(i) or spec_at(i, (UnpackOp, FpuOp, DstZero, MoveToDst))]
    if not work: raise ValueError("pack without a producing phase")
    begin = work[0]
    inner = [r for r in active[begin] if r not in active[first]]
    if inner: begin = min(inner)
    add(before, begin, sem("wait", 4, "trisc1"), sem("get", 4, "trisc1"))
    if banked and (active[begin] != scope or not phase_defines_dst(stream[begin:last+1], slots)):
      return insert_syncs(stream, double_buffer=False)
    if banked:
      ordinal = UOp.const(0)
      for r in scope: ordinal = ordinal * stream[r].src[0].without_after + stream[r]
      bank = (ordinal * len(groups) + phase) & 1
      for role in ("trisc1", "trisc2", "trisc0"):
        if role == "trisc0" and not any(spec_at(j, UnpackOp) and stream[j].ins_op.target is Space.DST for j in work): continue
        add(before, first if role == "trisc2" else begin, instruction(DstBank(role, slots), bank))
    pending = []
    for i in work:
      if spec_at(i, UnpackOp): pending.append(i)
      elif pending and (footprint(i) or spec_at(i, (FpuOp, MoveToDst))):
        if spec_at(i, (FpuOp, MoveToDst)) and all(stream[j].ins_op.target is not Space.DST for j in pending):
          # Src bank valid/clear handshakes are hardware double buffered.
          pending.clear()
          continue
        # Grant the shared write port at the next unpack, after all math
        # preceding that write (also on the loop backedge) has retired.
        add(before, pending[0], instruction(StallOp("math", "trisc1")), sem("post", 0, "trisc1"),
            sem("wait", 0, "trisc0"), sem("get", 0, "trisc0"))
        add(after, pending[-1], instruction(StallOp("unpack", "trisc0")), sem("post", 2, "trisc0"))
        add(before, i, sem("wait", 2, "trisc1"), sem("get", 2, "trisc1"))
        pending.clear()
    if pending: raise ValueError("unpack without consuming math")
    add(before, first, instruction(StallOp("math", "trisc1")), sem("post", 1, "trisc1"),
                       sem("wait", 1, "trisc2"), sem("get", 1, "trisc2"))
    add(after, last, instruction(StallOp("pack", "trisc2")), sem("post", 4, "trisc2"))
    previous = last
  pops = {}
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
    inner = [r for r in active[last] if r not in active[producer]]
    if inner: last = ends[min(inner)]
    pop_after(last, cb_id, "trisc0")
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
      pop_after(ends[min(inner)] if inner else i, spec.cb_id, spec.role)
    elif isinstance(spec, PackOp) and spec.cb_id in writers:
      add(before, i, cb("reserve")); add(after, i, cb("push"))
  for at, operations in pops.items():
    # Each unpack recipe drains UNPACR locally before releasing its L1 page.
    add(after, at, *operations)
  return [item for i, u in enumerate(stream) for item in (*before.get(i, ()), u, *after.get(i, ()))]


def dst_count(spec):
  if isinstance(spec, PackOp): return spec.blocks
  if isinstance(spec, FpuOp): return spec.m_blocks * spec.n_blocks
  return 1


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
      count = dst_count(spec)
      if spec.dst_slot < 0 or spec.dst_slot + count > 56: raise MemoryError("tile stream exceeds 56 Dst slots")
  if stack: raise ValueError("unterminated tile loop")
  for (_, sem_id), counts in semaphores.items():
    if not counts["wait"] == counts["get"] == counts["post"]:
      raise ValueError(f"unbalanced semaphore {sem_id} in loop scope: {dict(counts)}")
  for (_, cb_id), counts in buffers.items():
    if not counts["reserve"] == counts["push"] == counts["pop"] or counts["wait"] < counts["pop"]:
      raise ValueError(f"unbalanced CB {cb_id} in loop scope: {dict(counts)}")


def compile_tile_graph(sink, cb_addrs, cb_sizes=None, cb_depth=3, cb_depths=None, cb_pages=None):
  joint = linearize(sink)
  from .sfpu import SpillCapacityError
  try: return compile_stream(sink, insert_syncs(joint), cb_addrs, cb_sizes, cb_depth, cb_depths, cb_pages)
  except SpillCapacityError:
    return compile_stream(sink, insert_syncs(joint, double_buffer=False), cb_addrs, cb_sizes, cb_depth, cb_depths, cb_pages)


def compile_stream(sink, synced, cb_addrs, cb_sizes, cb_depth, cb_depths, cb_pages):
  verify_tile_stream(synced)
  if cb_sizes is not None:
    from .alloc import allocate_cb_stream
    synced, cb_addrs, cb_depths, cb_pages = allocate_cb_stream(synced, cb_sizes, default_depth=cb_depth)
    verify_tile_stream(synced)
  cores = split_roles(synced)
  compiled, images = [], {}
  for core in cores.src:
    code, binary = compile_core(list(core.src), core.arg, cb_addrs, cb_depths, cb_pages)
    compiled.append(UOp.linear(*code, arg=core.arg))
    images[core.arg] = binary
  return UOp.program(sink, UOp.linear(*compiled, arg="blackhole"), UOp.source(""), UOp.binary(pack_bundle(images)))
