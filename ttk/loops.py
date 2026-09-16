"""Symbolic index bounds and private loop expansion for verification.

The checker expands RANGE regions to reuse the straight-line memory hazard validator.
The authored graph, linearizer and renderer always retain each loop body once.
This is not a loop-unrolling compiler pass or a choice of hardware loop form.
"""
from .uop import Ops, UOp, base, is_storage


def check_range(node):
  if node.op is not Ops.RANGE or len(node.src) not in (1, 2) or node.src[0].dtype not in ('i32', 'u32'):
    raise ValueError('RANGE requires an integer bound in src[0]')
  if len(node.src) == 2 and node.src[1].op is not Ops.RANGE:
    raise ValueError('RANGE nesting requires an outer RANGE in src[1]')
  if node.dtype != 'i32': raise ValueError('RANGE index must be i32')


def trip_count(node):
  check_range(node)
  low, high = bounds(node.src[0])
  if low != high: raise ValueError('runtime RANGE trip counts are not supported by finite expansion')
  if low <= 0: raise ValueError('invalid RANGE trip count')
  return low


def bounds(node):
  if node.op is Ops.AFTER: return bounds(node.src[0])
  if node.op is Ops.CONST and type(node.arg[0]) is int: return node.arg[0], node.arg[0]
  if node.op is Ops.PARAM and node.arg[0].scalar: return node.arg[0].lo, node.arg[0].hi
  if node.op is Ops.RANGE:
    check_range(node)
    low, high = bounds(node.src[0])
    if low < 0 or high <= 0: raise ValueError('invalid RANGE bound')
    return 0, high-1
  if node.op not in (Ops.ADD, Ops.SUB, Ops.MUL, Ops.IDIV, Ops.MOD):
    raise ValueError('index must be a bounded integer expression of RANGE values')
  a,b = bounds(node.src[0]), bounds(node.src[1])
  if node.op is Ops.ADD: return a[0]+b[0], a[1]+b[1]
  if node.op is Ops.SUB: return a[0]-b[1], a[1]-b[0]
  if node.op is Ops.MUL:
    products = [x*y for x in a for y in b]
    return min(products), max(products)
  if b[0] != b[1] or b[0] <= 0: raise ValueError('index divisor must be a positive constant')
  if node.op is Ops.IDIV: return a[0]//b[0], a[1]//b[0]
  return 0, b[0]-1


def expand(sink):
  """Return a straight-line copy of the graph with every RANGE body repeated.

  RANGE values become CONST indices; each END collects only its own terminal
  across iterations in a private SINK. All sibling ENDs close the range together.
  Loop-register loads are threaded to the latest store so uninitialized reads
  are detected. Occupancy sequences become bounded integer expressions; the
  straight-line verifier infers writer/reader pairing and capacity hazards.
  """
  from .linearize import linearize, end_groups
  if not any(n.op is Ops.RANGE for n in sink.toposort()): return sink
  nodes = linearize(sink)          # region-aware: bodies are contiguous, outside deps precede RANGE
  groups = end_groups(nodes)
  ends, stack = {}, []
  for i,n in enumerate(nodes):
    if n.op is Ops.RANGE:
      trip_count(n)
      stack.append(i)
    elif n.op is Ops.END:
      if not stack or n.src[1] is not nodes[stack[-1]]: raise ValueError('improperly nested loop regions')
      if n is groups[n.src[1]][-1]: ends[stack.pop()] = i
  if stack: raise ValueError('unclosed RANGE')
  mapped, output, reg_state = {}, [], {}

  def run(start, stop):
    i = start
    while i < stop:
      n = nodes[i]
      if n.op is Ops.RANGE:
        end = ends[i]
        first_end = end - len(groups[n]) + 1
        completions = {e: [] for e in groups[n]}
        for index in range(trip_count(n)):
          mapped[n] = UOp(Ops.CONST, arg=(index,), dtype='i32')
          run(i+1, first_end)
          for e in groups[n]: completions[e].append(mapped[e.src[0]])
        for e, values in completions.items():
          mapped[e] = UOp(Ops.SINK, tuple(values))
          output.append(mapped[e])
        i = end+1
        continue
      if len(output) >= 200000: raise ValueError('finite loop protocol check exceeds 200000 execution nodes')
      src = tuple(mapped[s] for s in n.src)
      if n.op is Ops.LOAD and is_storage(src[0], 'REG'):
        reg = base(src[0])
        if reg not in reg_state: raise ValueError('load from uninitialized loop register')
        src = (src[0].after(reg_state[reg]),)
      new = UOp(n.op, src, n.arg, n.dtype, n.thread)
      mapped[n] = new; output.append(new)
      if n.op is Ops.STORE and is_storage(src[0], 'REG'): reg_state[base(src[0])] = new
      i += 1

  run(0, len(nodes))
  return UOp(Ops.SINK, tuple(output))
