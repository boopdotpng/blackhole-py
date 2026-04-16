# rvir.py — RISC-V Virtual IR for Tenstorrent Blackhole kernels
from __future__ import annotations
from contextlib import contextmanager
from dataclasses import dataclass
from . import dsl as _dsl
from .dsl import *

# =============================================================================
# Fixup — deferred-resolution primitive
# =============================================================================
class Fixup:
  __slots__ = ('fn', 'desc')
  def __init__(self, fn, desc="fixup"):
    self.fn = fn
    self.desc = desc
  def __repr__(self):
    return f"Fixup({self.desc!r})"

# Internal: zero-width label marker
@dataclass(frozen=True)
class _Label:
  name: str

_BRANCH_ENC = dict(beq=BEQ, bne=BNE, blt=BLT, bge=BGE, bltu=BLTU, bgeu=BGEU)

# =============================================================================
# Loop handle — yielded by loop context managers
# =============================================================================
class Loop:
  __slots__ = ('start', 'end')
  def __init__(self, start, end):
    self.start = start
    self.end = end
  @property
  def brk(self): return self.end

# =============================================================================
# Kernel — the assembler
# =============================================================================
def _align16(n):
  return (n + 15) & ~15

class Kernel:
  def __init__(self, base=0):
    self._items: list = []  # Insn | Fixup | _Label
    self._base = base
    self._uid = 0

  def _gen(self, prefix="L"):
    self._uid += 1
    return f".{prefix}{self._uid}"

  # ── raw emit ──────────────────────────────────────────────────
  def emit(self, *insns):
    for insn in insns:
      if isinstance(insn, TensixInsn):
        self._items.append(TTINSN(int(insn)))
      else:
        self._items.append(insn)
    return self

  # ── labels ────────────────────────────────────────────────────
  def label(self, name):
    self._items.append(_Label(name))
    return self

  # ── fixup (general deferred resolution) ───────────────────────
  def fixup(self, fn, desc="fixup"):
    f = Fixup(fn, desc)
    self._items.append(f)
    return f

  # ── 32-bit immediate load ─────────────────────────────────────
  def li(self, rd, imm):
    imm &= 0xFFFFFFFF
    simm = imm if imm < 0x80000000 else imm - 0x100000000
    if -2048 <= simm <= 2047:
      self.emit(ADDI(rd, zero, simm))
    else:
      upper = (simm + 0x800) & ~0xFFF
      lower = simm - upper
      self.emit(LUI(rd, upper))
      if lower:
        self.emit(ADDI(rd, rd, lower))
    return self

  # ── branches (label str or raw int offset) ────────────────────
  def _br(self, kind, rs1, rs2, target):
    if isinstance(target, str):
      enc = _BRANCH_ENC[kind]
      # capture loop vars explicitly to avoid late-binding closure bugs
      self._items.append(Fixup(
        lambda pc, L, _e=enc, _t=target, _r1=rs1, _r2=rs2:
          int(_e(_r1, _r2, L[_t] - pc)),
        f"{kind} -> {target}"))
    else:
      self.emit(_BRANCH_ENC[kind](rs1, rs2, target))
    return self

  def beq(self, rs1, rs2, t):  return self._br('beq', rs1, rs2, t)
  def bne(self, rs1, rs2, t):  return self._br('bne', rs1, rs2, t)
  def blt(self, rs1, rs2, t):  return self._br('blt', rs1, rs2, t)
  def bge(self, rs1, rs2, t):  return self._br('bge', rs1, rs2, t)
  def bltu(self, rs1, rs2, t): return self._br('bltu', rs1, rs2, t)
  def bgeu(self, rs1, rs2, t): return self._br('bgeu', rs1, rs2, t)
  def beqz(self, rs, t):       return self.beq(rs, zero, t)
  def bnez(self, rs, t):       return self.bne(rs, zero, t)
  def blez(self, rs, t):       return self.bge(zero, rs, t)
  def bgez(self, rs, t):       return self.bge(rs, zero, t)
  def bltz(self, rs, t):       return self.blt(rs, zero, t)
  def bgtz(self, rs, t):       return self.blt(zero, rs, t)

  # ── jumps with label support ──────────────────────────────────
  def j(self, t):
    if isinstance(t, str):
      self._items.append(Fixup(
        lambda pc, L, _t=t: int(JAL(zero, L[_t] - pc)),
        f"j -> {t}"))
    else:
      self.emit(JAL(zero, t))
    return self

  def call(self, t):
    if isinstance(t, str):
      self._items.append(Fixup(
        lambda pc, L, _t=t: int(JAL(ra, L[_t] - pc)),
        f"call -> {t}"))
    else:
      self.emit(JAL(ra, t))
    return self

  # ── Tensix (explicit — though emit() auto-wraps too) ──────────
  def tt(self, tensix_insn):
    return self.emit(TTINSN(int(tensix_insn)))

  # ── convenience ───────────────────────────────────────────────
  def sw_imm(self, val, base, off=0, tmp=t6):
    self.li(tmp, val)
    return self.emit(SW(base, tmp, off))

  def word(self, v):
    return self.emit(RiscVInsn(v & 0xFFFFFFFF))

  # ── countdown loop ────────────────────────────────────────────
  @contextmanager
  def countdown(self, reg, count):
    s, e = self._gen("cd"), self._gen("cd_end")
    if count is not None:
      if count < 0:
        raise ValueError("countdown count must be >= 0 or None")
      self.li(reg, count)
    self.beqz(reg, e)
    self.label(s)
    yield Loop(s, e)
    self.emit(ADDI(reg, reg, -1))
    self.bnez(reg, s)
    self.label(e)

  # ── countup loop ──────────────────────────────────────────────
  @contextmanager
  def countup(self, reg, limit, start=0):
    s, e = self._gen("cu"), self._gen("cu_end")
    if isinstance(start, int):
      self.li(reg, start)
    else:
      self.emit(MV(reg, start))
    self.bge(reg, limit, e)
    self.label(s)
    yield Loop(s, e)
    self.emit(ADDI(reg, reg, 1))
    self.blt(reg, limit, s)
    self.label(e)

  # ── while-true loop ───────────────────────────────────────────
  @contextmanager
  def while_true(self):
    s, e = self._gen("wh"), self._gen("wh_end")
    self.label(s)
    yield Loop(s, e)
    self.j(s)
    self.label(e)

  # ── function frame ────────────────────────────────────────────
  @contextmanager
  def func(self, name=None, saves=()):
    if name:
      self.label(name)
    regs = [ra] + [r for r in saves if r != ra]
    frame = _align16(len(regs) * 4)
    # prologue
    self.emit(ADDI(sp, sp, -frame))
    for i, r in enumerate(regs):
      self.emit(SW(sp, r, frame - 4*(i+1)))
    yield
    # epilogue
    for i, r in enumerate(regs):
      self.emit(LW(r, sp, frame - 4*(i+1)))
    self.emit(ADDI(sp, sp, frame))
    self.emit(RET())

  # ── __getattr__: fall through to dsl ──────────────────────────
  def __getattr__(self, name):
    obj = getattr(_dsl, name.upper(), None)
    if obj is not None and callable(obj):
      def _wrap(*a, **kw):
        return self.emit(obj(*a, **kw))
      return _wrap
    raise AttributeError(f"Kernel has no '{name}'")

  # ── assembly ──────────────────────────────────────────────────
  def assemble(self):
    # pass 1: label byte positions
    labels = {}
    pc = self._base
    for item in self._items:
      if isinstance(item, _Label):
        if item.name in labels:
          raise ValueError(f"duplicate label '{item.name}'")
        labels[item.name] = pc
      else:
        pc += 4

    # pass 2: resolve and encode
    words = []
    pc = self._base
    for item in self._items:
      if isinstance(item, _Label):
        continue
      elif isinstance(item, Fixup):
        w = item.fn(pc, labels)
        if not isinstance(w, int):
          raise TypeError(f"Fixup {item.desc!r} returned {type(w).__name__}, expected int")
        words.append(w)
      else:
        words.append(int(item))
      pc += 4
    return words

  # ── iteration / length ────────────────────────────────────────
  def __len__(self):
    return sum(1 for i in self._items if not isinstance(i, _Label))

  def __iter__(self):
    return iter(self.assemble())

  @property
  def pc(self):
    return self._base + len(self) * 4
