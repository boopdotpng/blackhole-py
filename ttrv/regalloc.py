"""Allocate virtual RV32 registers after all scalar and device recipes have been emitted."""

from collections import defaultdict, deque
from dataclasses import dataclass
from . import hw, isa
from .parse import Error


@dataclass(frozen=True)
class Instruction:
  op: str
  rd: int
  a: int
  b: int
  imm: int


def allocate(g):
  # Connect calls to their targets and each return to the possible continuations.
  # Virtual registers are unique across functions, including links and arguments.
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
    # Two simultaneous source loads suffice. A spilled destination can reuse
    # the first scratch register once its source has been consumed.
    scratch = available[-2:]
    colors = color(available[:-2])
    for r in order:
      if colors[r] is not None:
        continue
      occupied = {slots[n] for n in neighbors[r] if n in slots}
      slot = next(i for i in range(len(occupied) + 1) if i not in occupied)
      # The spill frame sits between the CB cursors and the firmware's half of LOCAL_MEM (hw.py, TTRV ABI).
      if slot >= hw.SPILL_SLOTS or r in links:
        raise Error(g.loc, "register.full", "static spill frame exceeds private memory or link registers")
      slots[r] = slot

  frame = hw.SPILL_FRAME - g.base[hw.LOCAL_BASE_REG]  # spill slot offsets from the local base register

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
        g.items.append((isa.rv("lw", p, hw.LOCAL_BASE_REG, imm=frame + 4 * slots[r]), loc))
      return loaded[r]

    if isinstance(item, Instruction):
      a, b = physical(item.a), physical(item.b)
      d = scratch[0] if item.rd in slots else physical(item.rd)
      if item.op != "addi" or item.imm or d != a:
        g.items.append((isa.rv(item.op, d, a, b, item.imm), loc))
      if item.rd in slots:
        g.items.append((isa.rv("sw", 0, hw.LOCAL_BASE_REG, d, frame + 4 * slots[item.rd]), loc))
    elif isinstance(item, tuple):
      op, a, b, target = item
      g.items.append(((op, physical(a), physical(b), target), loc))
    else:
      g.items.append((item, loc))
  offsets.append(len(g.items))
  g.labels = {label: offsets[pc] for label, pc in g.labels.items()}
  g.shared_marks = [
    (offsets[pc], name, ("x", colors[r]) if colors.get(r) is not None else ("mem", hw.SPILL_FRAME + 4 * slots[r]))
    for pc, r, name in g.shared_marks
    if colors.get(r) is not None or r in slots
  ]
  for pc, r, name in g.allocations:
    where = f"spill[{slots[r]}]" if r in slots else f"x{colors[r]}" if r in colors else "unused"
    g.notes.setdefault(offsets[pc], []).append(f"{name}={where}")
