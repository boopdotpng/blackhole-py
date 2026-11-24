from collections import defaultdict, deque
from dataclasses import dataclass
from hw import isa

LOCAL_BASE_REG = 3                   # x3 points at the middle of the RISC's local memory block
SPILL_FRAME, SPILL_SLOTS = 0xFFB00200, 384


class RegAllocError(RuntimeError):
  pass


@dataclass(frozen=True)
class Instruction:
  op: str
  rd: int
  a: int
  b: int
  imm: int


def allocate(g):
  # Virtual registers are unique across functions, so calls and returns are just CFG edges.
  returns = defaultdict(list)
  for pc, (item, _) in enumerate(g.items):
    if isinstance(item, tuple) and item[0] == "jal" and item[1]:
      returns[g.ends[item[3]]].append(pc + 1)
  reads, writes, successors = [], [], []
  preds = defaultdict(list)
  for pc, (item, _) in enumerate(g.items):
    rd, a, b = 0, 0, 0
    next_pc = [pc + 1] if pc + 1 < len(g.items) else []
    if isinstance(item, Instruction):
      rd, a, b = item.rd, item.a, item.b
      if item.op == "jalr":
        next_pc = returns[pc]
    elif isinstance(item, tuple):
      op, a, b, label = item
      if op == "jal":
        rd, a = a, 0
        next_pc = [g.labels[label]]
      else:
        next_pc.append(g.labels[label])
    reads.append({v for v in (a, b) if v >= 32})
    writes.append(rd)
    successors.append(next_pc)
    for n in next_pc:
      preds[n].append(pc)

  live = [set() for _ in g.items]
  todo = deque(reversed(range(len(live))))
  while todo:
    pc = todo.popleft()
    after = set().union(*(live[n] for n in successors[pc]))
    before = reads[pc] | (after - {writes[pc]})
    if before != live[pc]:
      live[pc] = before
      todo.extend(preds[pc])

  neighbors = defaultdict(set)
  for pc, rd in enumerate(writes):
    if rd < 32:
      continue
    overlap = set().union(*(live[n] for n in successors[pc])) - {rd}
    neighbors[rd].update(overlap)
    for r in overlap:
      neighbors[r].add(rd)

  links = {link for _, _, link in g.functions.values() if link}
  order = sorted(neighbors, key=lambda r: (r not in links, -len(neighbors[r]), r))
  available = sorted(set(range(1, 32)) - g.base.keys())

  def color(pool):
    colors = {}
    for r in order:
      occupied = {colors[n] for n in neighbors[r] if n in colors}
      colors[r] = next((p for p in pool if p not in occupied), None)
    return colors

  colors = color(available)
  slots = {}
  if None in colors.values():
    # Two scratch registers: at most two spilled sources per instruction; the destination reuses the first.
    scratch = available[-2:]
    colors = color(available[:-2])
    for r in order:
      if colors[r] is not None:
        continue
      occupied = {slots[n] for n in neighbors[r] if n in slots}
      slot = next(i for i in range(len(occupied) + 1) if i not in occupied)
      if slot >= SPILL_SLOTS or r in links:
        raise RegAllocError("static spill frame exceeds private memory or link registers")
      slots[r] = slot

  frame = SPILL_FRAME - g.base[LOCAL_BASE_REG]

  old_items, g.items = g.items, []
  offsets = []
  for item, loc in old_items:
    offsets.append(len(g.items))
    loaded = {}

    def physical(r):
      if r < 32:
        return r
      if r not in slots:
        return colors[r]
      if r not in loaded:
        p = loaded[r] = scratch[len(loaded)]
        g.items.append((isa.rv("lw", p, LOCAL_BASE_REG, imm=frame + 4 * slots[r]), loc))
      return loaded[r]

    if isinstance(item, Instruction):
      a, b = physical(item.a), physical(item.b)
      d = scratch[0] if item.rd in slots else physical(item.rd)
      if item.op != "addi" or item.imm or d != a:
        g.items.append((isa.rv(item.op, d, a, b, item.imm), loc))
      if item.rd in slots:
        g.items.append((isa.rv("sw", 0, LOCAL_BASE_REG, d, frame + 4 * slots[item.rd]), loc))
    elif isinstance(item, tuple):
      op, a, b, target = item
      g.items.append(((op, physical(a), physical(b), target), loc))
    else:
      g.items.append((item, loc))
  offsets.append(len(g.items))
  g.labels = {label: offsets[pc] for label, pc in g.labels.items()}
  for pc, r, name in g.allocations:
    where = f"spill[{slots[r]}]" if r in slots else f"x{colors[r]}" if r in colors else "unused"
    g.notes.setdefault(offsets[pc], []).append(f"{name}={where}")
