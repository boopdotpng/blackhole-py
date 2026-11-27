"""Worker-local resource lifetimes. Dst spill slots are never allocatable.

Release resources only after all consuming loops have ended. CB identifiers
retain their address/size when reused because recipes configure them statically.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class CbAllocation:
  cb_id: int
  address: int
  size: int


class TileAllocator:
  def __init__(self, deferred=False):
    self.deferred = deferred
    self.cb_addrs = {}
    self.cb_sizes = {}
    self._cbs = {}
    self._live_cbs = set()
    self._dst = {}
    self.next_addr = 0x20000

  def cb(self, size=4096):
    if size <= 0: raise ValueError("CB size must be positive")
    size = (size + 4095) & ~4095
    for cb_id, allocation in self._cbs.items():
      if cb_id not in self._live_cbs and allocation.size >= size:
        self._live_cbs.add(cb_id)
        return cb_id
    cb_id = len(self._cbs)
    if cb_id == 32 and not self.deferred: raise MemoryError("kernel exceeds 32 live CB streams")
    if self.next_addr + size > 0x180000 and not self.deferred: raise MemoryError("kernel exceeds worker L1 capacity")
    self._cbs[cb_id] = CbAllocation(cb_id, self.next_addr, size)
    self.cb_sizes[cb_id] = size
    self.cb_addrs[cb_id] = self.next_addr
    self.next_addr += size
    self._live_cbs.add(cb_id)
    return cb_id

  def release_cb(self, cb_id):
    if cb_id not in self._live_cbs: raise ValueError(f"CB {cb_id} is not live")
    self._live_cbs.remove(cb_id)

  def dst(self, count=1):
    if count <= 0: raise ValueError("Dst allocation must be positive")
    for start in range(57 - count):
      if all(start + count <= base or start >= base + size for base, size in self._dst.items()):
        self._dst[start] = count
        return start
    required = sum(self._dst.values()) + count
    raise MemoryError(f"kernel requires {required} Dst slots, limit 56 (contiguous request {count})")

  def release_dst(self, slot):
    if slot not in self._dst: raise ValueError(f"Dst allocation {slot} is not live")
    del self._dst[slot]


def allocate_cb_stream(stream, sizes, default_depth=3):
  """Allocate physical CBs and multi-page ring depths after synchronization.

  Streaming CBs (brisc->trisc0 and trisc2->ncrisc) inside loops default to
  `default_depth` pages so producer and consumer overlap across iterations,
  stepping down automatically when worker L1 capacity is tight. Lifetime
  coloring (single-page aliases) is only applied when logical CBs exceed
  32 streams or worker L1 capacity. Multicast rings keep dedicated allocations
  because their protocol is separate.
  """
  from dataclasses import replace
  from collections import defaultdict
  from ..uop import Ops
  from .specs import CbOp, NocMcastRead, NocMcastForward, McastRelease
  from .pipeline import instruction
  uses, producers, consumers, rings, push_scopes = defaultdict(list), defaultdict(set), defaultdict(set), set(), defaultdict(list)
  stack, scopes = [], {}
  for i, u in enumerate(stream):
    if u.op is Ops.RANGE:
      stack.append(u)
      continue
    if u.op is Ops.END:
      for r in u.src[1:]: stack.remove(r)
      continue
    if not u.is_ins: continue
    spec = u.ins_op
    if isinstance(spec, (NocMcastForward, McastRelease)): spec = spec.stream
    if hasattr(spec, 'cb_id'):
      uses[spec.cb_id].append(i)
      scopes[i] = tuple(stack)
    if isinstance(spec, NocMcastRead): rings.add(spec.cb_id)
    if isinstance(spec, CbOp):
      if spec.kind == 'push':
        producers[spec.cb_id].add(spec.role)
        push_scopes[spec.cb_id].append(tuple(stack))
      if spec.kind == 'pop': consumers[spec.cb_id].add(spec.role)

  def page_align(n): return (n + 4095) & ~4095

  def desired_depth(cb):
    if default_depth <= 1 or cb in rings: return 1
    if (frozenset(producers[cb]), frozenset(consumers[cb])) not in (
        (frozenset({"brisc"}), frozenset({"trisc0"})),
        (frozenset({"trisc2"}), frozenset({"ncrisc"})),
    ): return 1
    total = 0
    for scope in push_scopes[cb]:
      iters = 1
      for r in scope:
        bound = r.src[0].without_after
        if bound.is_const: hi = max(0, int(bound.val))
        elif isinstance(bound.vmax, int): hi = max(0, bound.vmax)
        else: return default_depth
        iters *= hi
        if iters >= default_depth: return default_depth
      total += max(1, iters)
      if total >= default_depth: return default_depth
    return max(1, total)

  ordered = sorted(uses.items(), key=lambda item: item[1][0])
  need_alias = len(ordered) > 32 or sum(page_align(sizes[cb]) for cb, _ in ordered) > 0x160000
  mapping, physical, members = {}, [], []
  for cb, refs in ordered:
    key = (frozenset(producers[cb]), frozenset(consumers[cb])) if cb not in rings else ('ring', cb)
    # Queues without a complete protocol (e.g. external L1 test inputs) do
    # not have a proven lifetime and must remain dedicated.
    # A single-page reserve waits for the previous pop. Aliases can share
    # that barrier when producer and consumer traverse the same sequence of
    # queue lifetimes, including the backedge of their common owning loop.
    scope = scopes[refs[0]]
    protocol = stream[refs[0]].ins_op, stream[refs[-1]].ins_op
    if (len(producers[cb]) != 1 or len(consumers[cb]) != 1 or scopes[refs[-1]] != scope or
        not all(isinstance(op, CbOp) and op.kind == kind for op, kind in zip(protocol, ("reserve", "pop"))) or
        any(scopes[i][:len(scope)] != scope for i in refs)):
      key = ('dedicated', cb)
    else: key = (*key, scope)
    if need_alias:
      slot = next((j for j, (end, _, owner) in enumerate(physical) if end < refs[0] and owner == key), len(physical))
    else:
      slot = len(physical)
    size = page_align(sizes[cb])
    if slot == len(physical):
      physical.append((refs[-1], size, key))
      members.append([cb])
    else:
      physical[slot] = refs[-1], max(size, physical[slot][1]), key
      members[slot].append(cb)
    mapping[cb] = slot

  budget = 0x160000
  depths = [desired_depth(cbs[0]) if len(cbs) == 1 else 1 for cbs in members]
  pages = [size for _, size, _ in physical]
  while sum(p * d for p, d in zip(pages, depths)) > budget:
    candidates = [i for i, d in enumerate(depths) if d > 1]
    if not candidates: break
    # Step down the largest page first so smaller weight/output queues keep full ring depth.
    victim = max(candidates, key=lambda i: (pages[i], depths[i]))
    depths[victim] -= 1

  alloc = TileAllocator()
  cb_depths, cb_pages = {}, {}
  for slot, (page, depth) in enumerate(zip(pages, depths)):
    alloc.cb(page * depth)
    cb_depths[slot] = depth
    cb_pages[slot] = page
  rewritten, replacements = [], {}
  for u in stream:
    value = u.replace(src=tuple(replacements.get(s, s) for s in u.src))
    if value.is_ins:
      spec = value.ins_op
      if isinstance(spec, (NocMcastForward, McastRelease)):
        spec = replace(spec, stream=replace(spec.stream, cb_id=mapping[spec.stream.cb_id]))
      elif hasattr(spec, 'cb_id'): spec = replace(spec, cb_id=mapping[spec.cb_id])
      value = instruction(spec, *value.src_without_body, dtype=value.dtype)
    replacements[u] = value
    rewritten.append(value)
  return rewritten, alloc.cb_addrs, cb_depths, cb_pages
