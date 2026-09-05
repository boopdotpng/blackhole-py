from isa import Insn, R, VReg, is_reg

RESERVED = {R.ZERO, R.RA, R.SP, R.GP}

def allocate(items, labels, base, branches, defines):
  """Control-flow liveness followed by a no-spill linear scan."""
  count = len(items)

  def uses_defs(item):
    if not isinstance(item, Insn): return set(), set()
    cut = int(item.op in defines)
    defs = {item.args[0]} if cut and item.args and is_reg(item.args[0]) else set()
    return {arg for arg in item.args[cut:] if is_reg(arg)}, defs

  def successors(i):
    item, following = items[i], (i + 1,) if i + 1 < count else ()
    if not isinstance(item, Insn) or item.op not in branches | {"jal"}: return following
    if item.target is None:
      offset = item.args[-1]
      target = i + offset // 4 if isinstance(offset, int) and offset % 4 == 0 else None
    elif isinstance(item.target, str): target = labels.get(item.target)
    else:
      offset = item.target - (base + i * 4)
      target = i + offset // 4 if offset % 4 == 0 else None
    destination = (target,) if target is not None and 0 <= target < count else ()
    return (*following, *destination) if item.op in branches else destination

  ud, succ = [uses_defs(item) for item in items], [successors(i) for i in range(count)]
  live_in = [set() for _ in items]
  changed = True
  while changed:
    changed = False
    for i in range(count - 1, -1, -1):
      uses, defs = ud[i]
      outgoing = set().union(*(live_in[j] for j in succ[i])) if succ[i] else set()
      incoming = uses | (outgoing - defs)
      if incoming != live_in[i]: live_in[i], changed = incoming, True

  points = {}
  for i, ((uses, defs), incoming) in enumerate(zip(ud, live_in)):
    for reg in uses | defs | incoming: points.setdefault(reg, []).append(i)
  intervals = {reg: (min(pos), max(pos)) for reg, pos in points.items() if isinstance(reg, VReg)}
  fixed = {arg for item in items if isinstance(item, Insn) for arg in item.args if isinstance(arg, R)}
  pool = tuple(reg for reg in R if reg not in RESERVED | fixed)
  ranges = sorted((start, end, reg) for reg, (start, end) in intervals.items())

  allocation, active = {}, []
  for start, end, reg in ranges:
    active = [entry for entry in active if entry[0] >= start]
    available = [candidate for candidate in pool if candidate not in {entry[2] for entry in active}]
    if not available:
      live = ", ".join(str(item[1]) for item in sorted(active, key=lambda item: item[1].index))
      raise RuntimeError(f"register allocation failed for {reg} at instruction {start}; {len(active)} virtual registers are live ({live})")
    allocation[reg] = available[0]
    active.append((end, reg, available[0]))
  return allocation
