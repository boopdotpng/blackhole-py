"""Memory allocators and static lifetime planners for DRAM and per-core L1 SRAM.

`TLSFAllocator` and the lifetime-event arena planner are ported from tinygrad
(`tinygrad/runtime/support/memory.py` and `tinygrad/codegen/memory.py`), adapted to
plan both cross-kernel DRAM buffers (`space="dram"`) and intra-kernel L1 scratchpad
buffers (`space="l1"`).
"""
from __future__ import annotations
import collections, math
from dataclasses import dataclass
from .uop import BufferArg, KernelArg, Ops, UOp, smax

def round_up(x: int, n: int) -> int: return ((x + n - 1) // n) * n if n > 1 else x

def alloc_nbytes(u: UOp) -> int:
  numel = math.prod(smax(d) for d in u.shape) if u.shape else 1
  return numel * max(1, (u.dtype.bits + 7) // 8)

# ---- Allocators (ported from tinygrad/runtime/support/memory.py) ----

class BumpAllocator:
  def __init__(self, size: int, base: int = 0, wrap: bool = False):
    self.size, self.ptr, self.base, self.wrap = size, 0, base, wrap
  def alloc(self, size: int, alignment: int = 1) -> int:
    if round_up(self.ptr, alignment) + size > self.size:
      if not self.wrap: raise MemoryError(f"BumpAllocator out of memory requesting {size} bytes")
      self.ptr = 0
    res = round_up(self.ptr, alignment)
    self.ptr = res + size
    return res + self.base

class TLSFAllocator:
  """Two-Level Segregated Fit allocator with O(1) lookup, splitting, and neighbor coalescing."""

  def __init__(self, size: int, base: int = 0, block_size: int = 16, lv2_cnt: int = 16):
    self.size, self.base, self.block_size, self.l2_cnt = size, base, block_size, lv2_cnt.bit_length()
    self.storage: list[dict[int, list[int]]] = [collections.defaultdict(list) for _ in range(size.bit_length() + 1)]
    self.lv1_entries: list[int] = [0] * len(self.storage)
    self.blocks: dict[int, tuple[int, int | None, int | None, bool]] = {0: (size, None, None, True)}
    if size > 0: self._set_free(0, size, True)

  def lv(self, size: int) -> tuple[int, int]:
    l1 = size.bit_length()
    return l1, (size - (1 << (l1 - 1))) >> max(0, l1 - self.l2_cnt)

  def _set_free(self, start: int, size: int, free: bool) -> TLSFAllocator:
    l1, l2 = self.lv(size)
    if free: self.storage[l1][l2].append(start)
    else: self.storage[l1][l2].remove(start)
    self.lv1_entries[l1] += 1 if free else -1
    self.blocks[start] = (size, start + size, self.blocks[start][2], free)
    return self

  def _split_block(self, start: int, size: int, new_size: int) -> TLSFAllocator:
    _, nxt, prev, is_free = self.blocks[start]
    assert not is_free, "block must be allocated"
    self.blocks[start] = (new_size, start + new_size, prev, False)
    self.blocks[start + new_size] = (size - new_size, nxt, start, False)
    if nxt in self.blocks:
      self.blocks[nxt] = (self.blocks[nxt][0], self.blocks[nxt][1], start + new_size, self.blocks[nxt][3])
    return self

  def alloc(self, req_size: int, align: int = 1) -> int:
    req_size = max(self.block_size, req_size)
    size = max(self.block_size, req_size + align - 1)
    size = round_up(size, 1 << max(0, size.bit_length() - self.l2_cnt))

    size_l1, size_l2 = self.lv(size)
    for l1 in range(size_l1, len(self.storage)):
      if self.lv1_entries[l1] == 0: continue
      for l2 in range(size_l2 if l1 == size_l1 else 0, 1 << self.l2_cnt):
        if self.storage[l1][l2]:
          start = self.storage[l1][l2][0]
          nsize = self.blocks[start][0]
          assert nsize >= size, "block must be larger"
          self._set_free(start, nsize, False)

          if (new_start := round_up(start, align)) != start:
            head_size = new_start - start
            self._split_block(start, nsize, head_size)._set_free(start, head_size, True)
            start, nsize = new_start, nsize - head_size

          if nsize > req_size:
            self._split_block(start, nsize, req_size)._set_free(start + req_size, nsize - req_size, True)
          return start + self.base
    raise MemoryError(f"TLSFAllocator can't allocate {req_size} bytes")

  def free(self, start: int) -> None:
    start -= self.base
    size, nxt, prev, _ = self.blocks[start]
    if nxt in self.blocks and self.blocks[nxt][3]:
      nxt_size = self.blocks[nxt][0]
      self._set_free(nxt, nxt_size, False)
      del self.blocks[nxt]
      size, nxt = size + nxt_size, nxt + nxt_size
    if prev is not None and self.blocks[prev][3]:
      prev_size = self.blocks[prev][0]
      self._set_free(prev, prev_size, False)
      del self.blocks[start]
      start, size = prev, size + prev_size
    if nxt in self.blocks:
      self.blocks[nxt] = (self.blocks[nxt][0], self.blocks[nxt][1], start, self.blocks[nxt][3])
    self._set_free(start, size, True)

# ---- Lifetime Memory Planner (adapted from tinygrad/codegen/memory.py) ----

@dataclass(frozen=True)
class MemoryPlan:
  offsets: dict[UOp, int]
  peak_bytes: int
  orig_bytes: int
  block_size: int
  @property
  def n_allocs(self) -> int: return len(self.offsets)

def _plan_lifetimes(first_use: dict[UOp, int], last_use: dict[UOp, int], block_size: int,
                    physical_nbytes: dict[UOp, int] | None = None) -> MemoryPlan:
  if not first_use:
    return MemoryPlan({}, 0, 0, block_size)
  nbytes = {b: round_up(alloc_nbytes(b) if physical_nbytes is None else physical_nbytes[b], block_size) for b in first_use}
  # Close events (False) sort before open events (True) at the same timestamp so freed memory reuses immediately
  events = sorted(
    [(first_use[b], True, b) for b in first_use] +
    [(last_use[b] + 1, False, b) for b in first_use],
    key=lambda x: (x[0], x[1]),
  )
  total_mem = max(block_size * 4, sum(nbytes.values()) * 2)
  alloc = TLSFAllocator(total_mem, block_size=block_size, lv2_cnt=32)
  offsets: dict[UOp, int] = {}
  peak = 0
  for _, is_open, buf in events:
    if is_open:
      offsets[buf] = alloc.alloc(nbytes[buf])
      peak = max(peak, offsets[buf] + nbytes[buf])
    else:
      alloc.free(offsets[buf])
  return MemoryPlan(offsets, round_up(peak, block_size), sum(nbytes.values()), block_size)

@dataclass(frozen=True)
class ScheduledCall:
  kernel: UOp
  args: tuple[UOp, ...]

def linearize_schedule(root: UOp, *, expand_functions: bool = True) -> list[ScheduledCall]:
  """Flatten a Layer 1 kernel CALL graph into execution order (respecting AFTER chains).

  When `expand_functions=True`, deduplicated `@function` CALLs are expanded with per-call
  storage bindings so transient ALLOC lifetimes across layers can be planned accurately.
  """
  calls: list[ScheduledCall] = []
  call_counter = 0

  def run_scope(scope: UOp, param_map: dict[int, UOp] | None, local_tag: str) -> None:
    nonlocal call_counter
    local_allocs: dict[UOp, UOp] = {}

    def resolve_arg(u: UOp) -> UOp:
      while u.op is Ops.AFTER: u = u.src[0]
      if u.op is Ops.PARAM and param_map is not None and u.arg.slot in param_map:
        return param_map[u.arg.slot]
      if u.op is Ops.ALLOC and local_tag:
        if u not in local_allocs:
          local_allocs[u] = u.replace(arg=BufferArg(f"{u.arg.name}_{local_tag}", u.arg.dtype, u.arg.addr, u.arg.space))
        return local_allocs[u]
      return u

    for u in scope.toposort(enter_calls=False):
      if u.op is not Ops.CALL: continue
      resolved = tuple(resolve_arg(s) for s in u.src[1:])
      body = u.src[0]
      if body.op is Ops.SINK and isinstance(body.arg, KernelArg):
        calls.append(ScheduledCall(body, resolved))
      elif expand_functions and body.op is Ops.SINK:
        call_counter += 1
        run_scope(body, {i: a for i, a in enumerate(resolved)}, f"c{call_counter}")
      else:
        calls.append(ScheduledCall(body, resolved))

  run_scope(root, None, "")
  return calls

def plan_dram_memory(root: UOp, *, block_size: int = 256, keep: set[UOp] | None = None,
                     expand_functions: bool = True) -> MemoryPlan:
  """Plan DRAM offsets for all transient `ALLOC(..., space="dram")` buffers in a kernel graph."""
  keep_set = set(keep) if keep is not None else set()
  # keep named output buffers (e.g. 'out') live outside the transient arena by default
  schedule = linearize_schedule(root, expand_functions=expand_functions)
  first_use: dict[UOp, int] = {}
  last_use: dict[UOp, int] = {}
  for i, sc in enumerate(schedule):
    for a in sc.args:
      if a.op is Ops.ALLOC and a.arg.space == "dram" and a not in keep_set and a.arg.name != "out":
        if a not in first_use: first_use[a] = i
        last_use[a] = i
  return _plan_lifetimes(first_use, last_use, block_size)

def plan_l1_memory(kernel_sink: UOp, *, block_size: int = 64) -> MemoryPlan:
  """Plan per-core L1 scratchpad offsets for all `ALLOC(..., space="l1")` buffers inside one kernel."""
  nodes = kernel_sink.toposort(enter_calls=False)
  first_use: dict[UOp, int] = {}
  last_use: dict[UOp, int] = {}
  # Map each node to the L1 ALLOC(s) it directly produces or consumes (including via AFTER/INDEX)
  for i, n in enumerate(nodes):
    if n.op is Ops.ALLOC and n.arg.space == "l1":
      first_use.setdefault(n, i)
      last_use[n] = i
    elif n.op in (Ops.LOAD, Ops.STORE):
      base = n.src[0].storage_base
      if base.op is Ops.ALLOC and base.arg.space == "l1":
        first_use.setdefault(base, i)
        last_use[base] = i
    elif n.op is Ops.AFTER:
      base = n.storage_base
      if base.op is Ops.ALLOC and base.arg.space == "l1":
        first_use.setdefault(base, i)
        last_use[base] = i
  return _plan_lifetimes(first_use, last_use, block_size)

def apply_memory_plan(root: UOp, plan: MemoryPlan) -> UOp:
  """Attach planned arena byte offsets (`BufferArg.addr`) onto each planned `ALLOC`."""
  if not plan.offsets: return root
  subs = {b: b.replace(arg=BufferArg(b.arg.name, b.arg.dtype, off, b.arg.space)) for b, off in plan.offsets.items()}
  return root.substitute(subs)
