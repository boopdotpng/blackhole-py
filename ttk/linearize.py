"""Global ordering that keeps loop regions contiguous. Thread assignment belongs to the renderer.

A node is inside region r when RANGE r is among its ancestors and END r is
not. Each region is ordered as one block: RANGE, its body (recursively), then
all ENDs for that range. Closing markers are coalesced by range, without new UOps.
Dependencies of the body that live outside the region are emitted before the
RANGE. Within a block the order is a deterministic topological sort with the
authored discovery order as tie-break. No priorities, wait sinking or
optimization; those are later passes over this structure.
"""
from .uop import Ops


def linearize(sink):
  from .loops import check_range
  topo = sink.toposort()
  index = {n: i for i, n in enumerate(topo)}
  # Ancestor sets as bitmasks over discovery order.
  anc = {}
  for n in topo:
    mask = 0
    for s in n.src: mask |= anc[s] | (1 << index[s])
    anc[n] = mask
  ends = {}
  for n in topo:
    if n.op is not Ops.END: continue
    if len(n.src) != 2 or n.src[1].op is not Ops.RANGE or n.dtype != 'void':
      raise ValueError('END requires a body and one RANGE')
    ends.setdefault(n.src[1], []).append(n)
  ranges = [n for n in topo if n.op is Ops.RANGE]
  for r in ranges:
    check_range(r)
    if r not in ends: raise ValueError('unclosed RANGE')

  def inside(node, r):
    return bool(anc[node] >> index[r] & 1) and not any(anc[node] >> index[e] & 1 or node is e for e in ends[r])

  scope = {}
  for n in topo:
    regions = [r for r in ranges if n is not r and inside(n, r)]
    regions.sort(key=lambda r: index[r])          # outer regions are discovered before inner
    scope[n] = tuple(regions)
  for r in ranges:
    for end in ends[r]: scope[end] = scope[r]

  members = {}                                      # scope tuple -> nodes at exactly that level
  for n in topo:
    if n.op is Ops.END: continue
    members.setdefault(scope[n], []).append(n)

  def item_of(node, level):
    """Map a dependency to the block item at `level` that contains it, or None if emitted earlier."""
    s = scope[node]
    if node.op is Ops.END: return node.src[1] if scope[node] == level else item_of(node.src[1], level)
    if len(s) < len(level) or s[:len(level)] != level: return None
    if len(s) == len(level): return node
    return s[len(level)]                            # the sub-block at this level containing node

  out = []

  def emit_block(level):
    items = members.get(level, [])
    deps = {}
    for it in items:
      if it.op is Ops.RANGE:
        inner = [n for n in topo if scope[n][:len(level)+1] == (*level, it) and n is not it]
        raw = {s for n in (*inner, *ends[it]) for s in n.src}
      else: raw = set(it.src)
      deps[it] = {d for d in (item_of(s, level) for s in raw) if d is not None and d is not it}
    done, active = set(), set()

    def visit(it):
      if it in done: return
      if it in active: raise ValueError('cyclic dependency between loop regions')
      active.add(it)
      for d in sorted(deps[it], key=lambda n: index[n]): visit(d)
      active.remove(it); done.add(it)
      if it.op is Ops.RANGE:
        out.append(it); emit_block((*level, it)); out.extend(ends[it])
      else: out.append(it)

    for it in items: visit(it)

  emit_block(())
  return tuple(out)


def end_groups(nodes):
  """Coalesce closing markers by RANGE without adding GROUP/SINK graph nodes."""
  groups = {}
  for node in nodes:
    if node.op is Ops.END: groups.setdefault(node.src[1], []).append(node)
  return {r: tuple(ends) for r, ends in groups.items()}
