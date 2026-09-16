"""Text-only renderer of an already globally topologically sorted UOp graph.

Thread placement follows the supplied global order. No rewriting, priority
scheduling, or instruction encoding.
Thread views are projections of the supplied order, never independent sorts.
Cross-thread references remain visible; they are NOT implemented synchronization.
"""
from .uop import Ops, Thread, UOp, base
from .linearize import end_groups


_DEFAULTS = {
  Ops.NOC_READ: Thread.BRISC, Ops.NOC_WRITE: Thread.NCRISC,
  Ops.UNPACK: Thread.UNPACK, Ops.PACK: Thread.PACK,
  **dict.fromkeys((Ops.MOVE, Ops.FPU_ELW,
                  Ops.FPU_MATMUL, Ops.FPU_POOL, Ops.FPU_DOTPV,
                  Ops.LOAD, Ops.STORE, Ops.MULACC, Ops.SHFT, Ops.IADD,
                  Ops.SHFT2, Ops.TRANSP), Thread.MATH),
}


def assign_threads(uops):
  """Return placed copies in the supplied order; do not mutate the authored graph.

  Placement is derived from operation kind and explicit thread requests;
  generic arithmetic follows its first placed operand. AFTER expresses a
  dependency, not a hardware wait or a thread handoff.
  Explicit `thread=` requests are preserved. More detailed placement awaits
  actual instruction lowering.
  """
  placed = {}
  for node in uops:
    src = tuple(placed[s] for s in node.src)
    thread = node.thread
    if thread is None:
      if node.op in (Ops.ADD, Ops.SUB, Ops.MUL, Ops.IDIV, Ops.MOD, Ops.GEP):
        # GEP's first operand is the producing operation/completion.
        thread = next((s.thread for s in src[:2] if s.thread is not None), None)
      else: thread = _DEFAULTS.get(node.op)
    placed[node] = UOp(node.op, src, node.arg, node.dtype, thread)
  return tuple(placed.values())


class FakeRenderer:
  def render(self, uops, *, per_thread=False):
    nodes = tuple(uops)
    ids = {}
    for i, node in enumerate(nodes):
      if not isinstance(node, UOp): raise TypeError('expected UOps')
      if node in ids: raise ValueError('duplicate UOp occurrence in linear order')
      if any(src not in ids for src in node.src):
        raise ValueError(f'node {i} ({node.op.name}) precedes a dependency; globally toposort first')
      ids[node] = i

    nodes = assign_threads(nodes)
    ids = {node: i for i, node in enumerate(nodes)}

    def ref(node): return f'%{ids[node]}'

    def statement(node):
      operands = ', '.join(ref(s) for s in node.src)
      attrs = f' arg={node.arg!r}' if node.arg else ''
      # AFTER exposes state/region requirements separately from value operands.
      text = f'{ref(node)}: {node.op.name.lower()}({operands}){attrs} -> {node.dtype}'
      if node.op is Ops.RANGE: text += f'  // for {ref(node)} in range({ref(node.src[0])})'
      if node.op is Ops.END and node is region_ends[node.src[1]][-1]: text += f'  // end {ref(node.src[1])}'
      return text

    def owner(node): return node.thread.name.lower() if node.thread is not None else 'unassigned'

    region_ends = end_groups(nodes)
    scopes, participants, closing, stack = {}, {}, {}, []
    for node in nodes:
      if node.op is Ops.RANGE:
        scopes[node] = tuple(stack)
        participants[node] = set()
        stack.append(node)
      elif node.op is Ops.END:
        if not stack or stack[-1] is not node.src[1]: raise ValueError('improperly nested loop regions')
        closing[node] = stack[-1]
        scopes[node] = tuple(stack[:-1])
        if node is region_ends[node.src[1]][-1]: stack.pop()
      else:
        scopes[node] = tuple(stack)
        for region in stack: participants[region].add(owner(node))
    if stack: raise ValueError('unclosed loop region')
    owner_order = tuple(dict.fromkeys(owner(node) for node in nodes))

    lines = ['// RAW UOP GRAPH — review only; not executable',
             '// IDs are global order. All src edges shown; no optimization.',
             '// unassigned includes symbolic nodes and work without a selected thread.']
    if not per_thread:
      lines += [f'{owner(node):10} ' + '  '*len(scopes[node]) + statement(node) for node in nodes]
    else:
      # Insertion-ordered groups preserve first appearance and global node IDs.
      groups = {}
      for node in nodes:
        region = node if node.op is Ops.RANGE else closing.get(node)
        targets = participants[region] if region is not None else {owner(node)}
        if not targets: targets = {'unassigned'}
        for name in owner_order:
          if name in targets: groups.setdefault(name, []).append(node)
      for name, group in groups.items():
        lines.append(f'\n{name} {{')
        for node in group:
          external = [s for s in node.src if owner(s) != name]
          lines.append('  '*(1+len(scopes[node])) + statement(node))
          if external:
            lines.append('    // external deps: ' + ', '.join(f'{ref(s)}@{owner(s)}' for s in external))
        lines.append('}')
    return '\n'.join(lines) + '\n'
