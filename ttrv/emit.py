"""Resolve PC-relative branches and produce a source-mapped disassembly."""

import struct
import fw
from .isa import rv, rv_decode, outline, tensix_decode
from .parse import Error

INVERSE = dict(beq="bne", bne="beq", bltu="bgeu", bgeu="bltu")


class Emitter:
  def __init__(self, role):
    self.notes = {}
    self.role, self.items, self.labels, self.loc = role, [], {}, None

  def word(self, w):
    self.items.append((w, self.loc))

  def rv(self, op, rd=0, a=0, b=0, imm=0):
    self.word(rv(op, rd, a, b, imm))

  def mark(self, label):
    self.labels[label] = len(self.items)

  def branch(self, op, a, b, target):
    self.items.append(((op, a, b, target), self.loc))

  def jump(self, target, link=0):
    self.branch("jal", link, 0, target)

  def finish(self):
    long = set()
    while True:
      offsets = [0]
      for i, (item, _) in enumerate(self.items):
        offsets.append(offsets[-1] + (0 if item is None else 8 if i in long else 4))
      changed = False
      for i, (item, _) in enumerate(self.items):
        if isinstance(item, tuple) and item[0] != "jal" and i not in long:
          delta = offsets[self.labels[item[-1]]] - offsets[i]
          if not -4096 <= delta < 4096:
            long.add(i)
            changed = True
      if not changed:
        break
    self.offsets = offsets
    words, lines = [], []
    for i, (item, loc) in enumerate(self.items):
      if item is None:
        continue
      if isinstance(item, int):
        seq = [item]
      else:
        op, a, b, label = item
        d = offsets[self.labels[label]] - offsets[i]
        if op == "jal":
          seq = [rv(op, a, imm=d)]
        elif i in long:
          seq = [rv(INVERSE[op], rs1=a, rs2=b, imm=8), rv("jal", imm=d - 4)]
        else:
          seq = [rv(op, rs1=a, rs2=b, imm=d)]
      for w in seq:
        op, fields = (rv_decode(w) if w & 3 == 3 else tensix_decode(outline(w))) or ("?", {})
        note = " ".join(self.notes.get(i, ()))
        lines.append(f"{len(words) * 4:04x}  {w:08x}  {op} {fields}  {loc} {note}")
        words.append(w)
    return struct.pack(f"<{len(words)}I", *words), "\n".join(lines)
