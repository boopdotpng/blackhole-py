# rvir.py — RISC-V Virtual IR for Tenstorrent Blackhole kernels
from __future__ import annotations
import struct
from contextlib import contextmanager
from dataclasses import dataclass
from . import dsl as _dsl
from .dsl import *

# Default LDM virtual base — Blackhole architectural constant
LDM_BASE = 0xFFB00000

# =============================================================================
# Fixup — deferred-resolution primitive (text section)
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

# Data-section item markers
@dataclass(frozen=True)
class _DataLabel:
  name: str

class _DataWord:
  __slots__ = ('val',)
  def __init__(self, v): self.val = v & 0xFFFFFFFF

class _DataFixup:
  __slots__ = ('fn', 'desc')
  def __init__(self, fn, desc="data_fixup"):
    self.fn = fn
    self.desc = desc

class _DataBytes:
  __slots__ = ('b',)
  def __init__(self, b): self.b = bytes(b)

_BRANCH_ENC = dict(beq=BEQ, bne=BNE, blt=BLT, bge=BGE, bltu=BLTU, bgeu=BGEU)

# Condition → inverted-branch helper, arity (1=zero-arg rs2, 2=rs1+rs2)
_IF_INV = {
  'eq': ('bne', 2),   'ne':  ('beq', 2),
  'lt': ('bge', 2),   'ge':  ('blt', 2),
  'ltu':('bgeu',2),   'geu': ('bltu',2),
  'eqz':('bnez',1),   'nez': ('beqz',1),
  'lez':('bgtz',1),   'gez': ('bltz',1),
  'ltz':('bgez',1),   'gtz': ('blez',1),
}

def _split_hi_lo(addr):
  """RISC-V lui+addi split: returns (upper_for_lui, lower_for_addi)."""
  addr &= 0xFFFFFFFF
  simm = addr if addr < 0x80000000 else addr - 0x100000000
  upper = (simm + 0x800) & ~0xFFF
  lower = simm - upper
  return upper, lower

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
# If/else — yielded by if_()
# =============================================================================
class _IfCtx:
  __slots__ = ('k', 'else_lbl', 'end_lbl', '_has_else')
  def __init__(self, k, else_lbl, end_lbl):
    self.k = k
    self.else_lbl = else_lbl
    self.end_lbl = end_lbl
    self._has_else = False

  @contextmanager
  def else_(self):
    if self._has_else:
      raise RuntimeError("else_ already used on this if_")
    self._has_else = True
    self.k.j(self.end_lbl)
    self.k.label(self.else_lbl)
    yield

# =============================================================================
# Jumptable — yielded by jumptable()
# =============================================================================
class _JumpTable:
  __slots__ = ('k', 'cases', 'n', 'default', 'fn_base', 'tbl', 'end')
  def __init__(self, k, n, default, fn_base, tbl, end):
    self.k = k
    self.cases = {}  # idx -> case label name
    self.n = n
    self.default = default
    self.fn_base = fn_base
    self.tbl = tbl
    self.end = end

  @contextmanager
  def case(self, *idxs):
    if not idxs:
      raise ValueError("case() requires at least one index")
    for i in idxs:
      if i in self.cases:
        raise ValueError(f"duplicate jumptable case {i}")
      if not (0 <= i < self.n):
        raise ValueError(f"jumptable case {i} out of range [0,{self.n})")
    lbl = self.k._gen("case")
    for i in idxs: self.cases[i] = lbl
    self.k.label(lbl)
    yield
    self.k.j(self.end)

# =============================================================================
# Kernel — the assembler
# =============================================================================
def _align16(n):
  return (n + 15) & ~15

class Kernel:
  def __init__(self, base=0, data_base=LDM_BASE):
    self._items: list = []  # Insn | Fixup | _Label
    self._data: list = []   # _DataWord | _DataFixup | _DataLabel | _DataBytes
    self._base = base
    self._data_base = data_base
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

  # ── load absolute address of a label (text or data) ──────────
  def la(self, rd, name):
    def fh(pc, L, _rd=rd, _n=name):
      upper, _ = _split_hi_lo(L[_n])
      return int(LUI(_rd, upper))
    def fl(pc, L, _rd=rd, _n=name):
      _, lower = _split_hi_lo(L[_n])
      return int(ADDI(_rd, _rd, lower))
    self._items.append(Fixup(fh, f"la hi {name}"))
    self._items.append(Fixup(fl, f"la lo {name}"))
    return self

  # ── data section ─────────────────────────────────────────────
  def data_word(self, v):
    self._data.append(_DataWord(v))
    return self

  def data_words(self, *vs):
    for v in vs: self._data.append(_DataWord(v))
    return self

  def data_label(self, name):
    self._data.append(_DataLabel(name))
    return self

  def data_fixup(self, fn, desc="data_fixup"):
    self._data.append(_DataFixup(fn, desc))
    return self

  def data_bytes(self, b):
    b = bytes(b)
    if len(b) & 3:
      b += b'\x00' * (4 - (len(b) & 3))
    self._data.append(_DataBytes(b))
    return self

  # ── if / else ────────────────────────────────────────────────
  @contextmanager
  def if_(self, cond, rs1, rs2=None):
    """Conditional block. cond ∈ {eq,ne,lt,ge,ltu,geu,eqz,nez,lez,gez,ltz,gtz}.
       Zero-arg conditions (*z) ignore rs2."""
    if cond not in _IF_INV:
      raise ValueError(f"unknown condition {cond!r}")
    inv, arity = _IF_INV[cond]
    else_lbl = self._gen("else")
    end_lbl  = self._gen("endif")
    branch = getattr(self, inv)
    if arity == 1:
      branch(rs1, else_lbl)
    else:
      if rs2 is None:
        raise ValueError(f"cond {cond!r} requires rs2")
      branch(rs1, rs2, else_lbl)
    ifc = _IfCtx(self, else_lbl, end_lbl)
    yield ifc
    if not ifc._has_else:
      self.label(else_lbl)
    self.label(end_lbl)

  # ── jumptable (PIC-style, table in .data) ─────────────────────
  @contextmanager
  def jumptable(self, reg, n, default=None, bias=0, zext_b=False,
                tmp1=t0, tmp2=t1):
    """Emits a jump-table dispatch on `reg`.
       Table (n entries, target-fn_base offsets) is placed in .data.
       - bias:   subtract from reg before indexing (ADDI -bias)
       - zext_b: ANDI 0xFF after bias (byte-index clamp)
       - default: label name used for unfilled slots (required if any gap)
    """
    fn_base = self._gen("fnbase")
    tbl     = self._gen("jtbl")
    end     = self._gen("jtend")

    if bias != 0:
      self.emit(ADDI(reg, reg, -bias))
    if zext_b:
      self.emit(ANDI(reg, reg, 0xFF))

    # fn_base anchors the PC from which table offsets are measured
    self.label(fn_base)
    self.la(tmp1, tbl)
    self.emit(SH2ADD(tmp2, reg, tmp1))
    self.emit(LW(tmp2, tmp2, 0))
    self.la(tmp1, fn_base)
    self.emit(ADD(tmp2, tmp2, tmp1))
    self.emit(JR(tmp2))

    jt = _JumpTable(self, n, default, fn_base, tbl, end)
    yield jt

    # End-of-dispatch label (cases fall through j here)
    self.label(end)

    # Table in .data
    self.data_label(tbl)
    for i in range(n):
      target = jt.cases.get(i, default)
      if target is None:
        raise ValueError(f"jumptable slot {i} not emitted and no default set")
      self.data_fixup(
        lambda L, _t=target, _b=fn_base: (L[_t] - L[_b]) & 0xFFFFFFFF,
        f"jt[{i}] = {target} - {fn_base}")

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
  def _resolve_labels(self):
    """Pass 1: compute absolute addresses for all text and data labels."""
    labels = {}
    pc = self._base
    for item in self._items:
      if isinstance(item, _Label):
        if item.name in labels:
          raise ValueError(f"duplicate label '{item.name}'")
        labels[item.name] = pc
      else:
        pc += 4
    off = 0
    for item in self._data:
      if isinstance(item, _DataLabel):
        if item.name in labels:
          raise ValueError(f"duplicate label '{item.name}'")
        labels[item.name] = self._data_base + off
      elif isinstance(item, _DataBytes):
        off += len(item.b)
      else:
        off += 4
    return labels

  def assemble(self):
    labels = self._resolve_labels()
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

  def data(self):
    """Encode the .data section as bytes (empty if no data items)."""
    if not self._data:
      return b''
    labels = self._resolve_labels()
    out = bytearray()
    for item in self._data:
      if isinstance(item, _DataLabel):
        continue
      elif isinstance(item, _DataWord):
        out += struct.pack('<I', item.val)
      elif isinstance(item, _DataFixup):
        v = item.fn(labels)
        if not isinstance(v, int):
          raise TypeError(f"Data fixup {item.desc!r} returned {type(v).__name__}, expected int")
        out += struct.pack('<I', v & 0xFFFFFFFF)
      elif isinstance(item, _DataBytes):
        out += item.b
    return bytes(out)

  def assemble_full(self):
    """Return (text_words, data_bytes)."""
    return self.assemble(), self.data()

  # ── iteration / length ────────────────────────────────────────
  def __len__(self):
    return sum(1 for i in self._items if not isinstance(i, _Label))

  def __iter__(self):
    return iter(self.assemble())

  @property
  def pc(self):
    return self._base + len(self) * 4
