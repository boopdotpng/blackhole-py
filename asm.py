from __future__ import annotations
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
import dsl
from dsl import Reg, ra, zero
from ttk.mixins import CbMixin, FlowMixin, NocMixin, RvMixin, TensixMixin

CoreArgs = Callable[[int, int], list[int]]

@dataclass(frozen=True)
class Fixup:
  op: str
  operands: tuple
  label: str
  pc: int

@dataclass(frozen=True)
class Cond:
  lhs: Reg
  op: str
  rhs: Reg | int
  tmp: Reg | None = None

@dataclass(frozen=True)
class Segment:
  addr: int
  data: bytes
  label: str = ""

def cond(lhs: Reg, op: str, rhs: Reg | int, *, tmp: Reg | None = None) -> Cond:
  if isinstance(rhs, int) and tmp is None:
    raise ValueError("integer condition rhs needs tmp=Reg(...)")
  return Cond(lhs, op, rhs, tmp)

def boot_jal(target: int) -> bytes:
  return dsl.jal(zero, target).to_bytes()

class Asm(TensixMixin, NocMixin, CbMixin, FlowMixin, RvMixin):
  def __init__(self, *, base: int = 0):
    self.base = base
    self.items = []
    self.labels: dict[str, int] = {}
    self._label_id = 0
    self._reg_consts: dict[int, int] = {}

  @property
  def pc(self) -> int:
    return self.base + 4 * len(self.items)

  def _new_label(self, prefix: str) -> str:
    self._label_id += 1
    return f".L{prefix}_{self._label_id}"

  def emit(self, *insns):
    for insn in insns:
      self.items.append(insn)
      self._track_emit(insn)
    return self

  def _clear_reg_consts(self):
    self._reg_consts.clear()

  def _set_reg_const(self, reg: Reg, value: int):
    if int(reg) == int(zero):
      return
    self._reg_consts[int(reg)] = value & 0xFFFFFFFF

  def _kill_reg_const(self, reg: Reg):
    if int(reg) != int(zero):
      self._reg_consts.pop(int(reg), None)

  def _reg_const(self, reg: Reg) -> int | None:
    return self._reg_consts.get(int(reg))

  def _const_delta(self, target: int, base: int) -> int | None:
    delta = (target - base) & 0xFFFFFFFF
    if delta & 0x80000000:
      delta -= 0x100000000
    return delta if -2048 <= delta <= 2047 else None

  def _track_emit(self, insn):
    name = getattr(insn, "name", None)
    if name is None:
      self._clear_reg_consts()
      return

    if name == "lui":
      self._set_reg_const(insn.rd, insn.imm << 12)
      return

    if name == "addi":
      base = self._reg_const(insn.rs1)
      if base is not None:
        self._set_reg_const(insn.rd, base + insn.imm)
      else:
        self._kill_reg_const(insn.rd)
      return

    if name in {"ori", "andi", "xori", "slli", "srli"}:
      base = self._reg_const(insn.rs1)
      if base is not None:
        match name:
          case "ori":
            self._set_reg_const(insn.rd, base | insn.imm)
          case "andi":
            self._set_reg_const(insn.rd, base & insn.imm)
          case "xori":
            self._set_reg_const(insn.rd, base ^ insn.imm)
          case "slli":
            self._set_reg_const(insn.rd, base << (insn.imm & 0x1F))
          case "srli":
            self._set_reg_const(insn.rd, (base & 0xFFFFFFFF) >> (insn.imm & 0x1F))
      else:
        self._kill_reg_const(insn.rd)
      return

    if name in {"add", "sub", "or", "and"}:
      lhs, rhs = self._reg_const(insn.rs1), self._reg_const(insn.rs2)
      if lhs is not None and rhs is not None:
        match name:
          case "add":
            self._set_reg_const(insn.rd, lhs + rhs)
          case "sub":
            self._set_reg_const(insn.rd, lhs - rhs)
          case "or":
            self._set_reg_const(insn.rd, lhs | rhs)
          case "and":
            self._set_reg_const(insn.rd, lhs & rhs)
      else:
        self._kill_reg_const(insn.rd)
      return

    if name in {"lw", "lbu", "lhu", "jal", "jalr", "csrrs", "csrrc"}:
      self._kill_reg_const(insn.rd)
      if name in {"jal", "jalr"}:
        self._clear_reg_consts()
      return

    if name in {"beq", "bne", "blt", "bge", "bltu", "bgeu"}:
      return

  def __repr__(self) -> str:
    labels_by_pc: dict[int, list[str]] = {}
    for name, pc in self.labels.items():
      labels_by_pc.setdefault(pc, []).append(name)

    lines = []
    for idx, item in enumerate(self.items):
      pc = self.base + 4 * idx
      for label in sorted(labels_by_pc.get(pc, [])):
        lines.append(f"{label}:")
      lines.append(f"  {pc:08x}: {self._repr_item(item)}")
    for label in sorted(labels_by_pc.get(self.pc, [])):
      lines.append(f"{label}:")
    return "\n".join(lines)

  def _repr_item(self, item) -> str:
    if not isinstance(item, Fixup):
      return repr(item)
    args = ", ".join(repr(arg) for arg in item.operands)
    if args:
      args += ", "
    try:
      resolved = self._resolve(item)
      return f"{item.op}({args}{item.label})  # {resolved!r}"
    except ValueError:
      return f"{item.op}({args}{item.label})"

  def label(self, name: str):
    if name in self.labels:
      raise ValueError(f"duplicate label {name!r}")
    self._clear_reg_consts()
    self.labels[name] = self.pc
    return self

  def _ref(self, op: str, operands: tuple, label: str):
    self.items.append(Fixup(op, operands, label, self.pc))
    if op == "jal":
      self._clear_reg_consts()
    return self

  def _rv_emit(self, name: str, *args):
    if name in {"beq", "bne", "blt", "bge", "bltu", "bgeu", "jal"} and args and isinstance(args[-1], str):
      return self._ref(name, args[:-1], args[-1])
    return self.emit(getattr(dsl, name)(*args))

  def __getattr__(self, name: str):
    if hasattr(dsl, name) and callable(getattr(dsl, name)):
      return lambda *args: self._rv_emit(name, *args)
    raise AttributeError(name)

  # Pseudo-instructions.
  def li(self, rd: Reg, imm: int):
    imm32 = imm & 0xFFFFFFFF
    if self._reg_const(rd) == imm32:
      return self
    for reg_idx in (int(rd), *self._reg_consts.keys()):
      known = self._reg_consts.get(reg_idx)
      if known is None:
        continue
      delta = self._const_delta(imm32, known)
      if delta is not None:
        return self.addi(rd, Reg(reg_idx), delta)
    if -2048 <= imm <= 2047:
      return self.addi(rd, zero, imm)
    signed = imm32 - 0x100000000 if imm32 & 0x80000000 else imm32
    # Round up when bit 11 is set because addi sign-extends the low 12 bits.
    hi = (signed + 0x800) >> 12
    lo = signed - (hi << 12)
    self.lui(rd, (hi & 0xFFFFF) << 12)
    if lo:
      self.addi(rd, rd, lo)
    return self

  def mv(self, rd: Reg, rs: Reg): return self.addi(rd, rs, 0)
  def nop(self): return self.addi(zero, zero, 0)
  def j(self, label: str): return self._ref("jal", (zero,), label)
  def call(self, label: str): return self._ref("jal", (ra,), label)
  def ret(self): return self.jalr(zero, ra, 0)

  def _cond_regs(self, c: Cond) -> tuple[Reg, Reg]:
    if isinstance(c.rhs, Reg):
      return c.lhs, c.rhs
    if c.tmp is None:
      raise ValueError("integer condition rhs needs tmp=Reg(...)")
    self.li(c.tmp, c.rhs)
    return c.lhs, c.tmp

  def branch_if(self, c: Cond, label: str):
    lhs, rhs = self._cond_regs(c)
    match c.op:
      case "==": return self.beq(lhs, rhs, label)
      case "!=": return self.bne(lhs, rhs, label)
      case "<": return self.blt(lhs, rhs, label)
      case ">=": return self.bge(lhs, rhs, label)
      case "<u": return self.bltu(lhs, rhs, label)
      case ">=u": return self.bgeu(lhs, rhs, label)
      case ">": return self.blt(rhs, lhs, label)
      case "<=": return self.bge(rhs, lhs, label)
      case ">u": return self.bltu(rhs, lhs, label)
      case "<=u": return self.bgeu(rhs, lhs, label)
      case _: raise ValueError(f"unknown condition op {c.op!r}")

  def branch_unless(self, c: Cond, label: str):
    inverse = {"==": "!=", "!=": "==", "<": ">=", ">=": "<", "<u": ">=u", ">=u": "<u",
               ">": "<=", "<=": ">", ">u": "<=u", "<=u": ">u"}
    if c.op not in inverse:
      raise ValueError(f"unknown condition op {c.op!r}")
    return self.branch_if(Cond(c.lhs, inverse[c.op], c.rhs, c.tmp), label)

  @contextmanager
  def if_(self, c: Cond) -> Iterator[None]:
    end = self._new_label("endif")
    self.branch_unless(c, end)
    yield
    self.label(end)

  @contextmanager
  def while_(self, c: Cond) -> Iterator[None]:
    start, end = self._new_label("while"), self._new_label("endwhile")
    self.label(start)
    self.branch_unless(c, end)
    yield
    self.j(start)
    self.label(end)

  def break_(self, c: Cond | None = None):
    if not hasattr(self, "_break_labels") or not self._break_labels:
      raise RuntimeError("break_() used outside loop()")
    end = self._break_labels[-1]
    return self.j(end) if c is None else self.branch_if(c, end)

  @contextmanager
  def loop(self) -> Iterator[None]:
    start, end = self._new_label("loop"), self._new_label("endloop")
    if not hasattr(self, "_break_labels"):
      self._break_labels = []
    self._break_labels.append(end)
    self.label(start)
    try:
      yield
    finally:
      self._break_labels.pop()
    self.j(start)
    self.label(end)

  @contextmanager
  def for_range(self, reg: Reg, start: int, stop: Reg | int, *, step: int = 1, tmp: Reg | None = None) -> Iterator[None]:
    limit = stop
    self.li(reg, start)
    if isinstance(stop, int):
      if tmp is None:
        raise ValueError("integer for_range stop needs tmp=Reg(...)")
      self.li(tmp, stop)
      limit = tmp
    start_label, end_label = self._new_label("for"), self._new_label("endfor")
    self.label(start_label)
    self.branch_unless(Cond(reg, "<", limit), end_label)
    yield
    self.addi(reg, reg, step)
    self.j(start_label)
    self.label(end_label)

  def _resolve(self, item):
    if not isinstance(item, Fixup):
      return item
    if item.label not in self.labels:
      raise ValueError(f"undefined label {item.label!r}")
    imm = self.labels[item.label] - item.pc
    if item.op == "jal":
      if imm & 1 or not -(1 << 20) <= imm < (1 << 20):
        raise ValueError(f"jal target {item.label!r} out of range: {imm}")
    else:
      if imm & 1 or not -(1 << 12) <= imm < (1 << 12):
        raise ValueError(f"branch target {item.label!r} out of range: {imm}")
    return getattr(dsl, item.op)(*item.operands, imm)

  def instructions(self) -> list:
    return [self._resolve(item) for item in self.items]

  def to_bytes(self) -> bytes:
    words = []
    for inst in self.instructions():
      words.append(inst.to_word() if hasattr(inst, "to_word") else int(inst))
    return b"".join((w & 0xFFFFFFFF).to_bytes(4, "little") for w in words)

class Kernel(Asm):
  def __init__(
    self, *, base_addr: int = 0, rtas: CoreArgs | None = None,
  ):
    super().__init__(base=base_addr)
    self.rtas = rtas
    self.load_segments: list[Segment] = []

  def rta(self, fn: CoreArgs):
    if not callable(fn):
      raise TypeError("rta() expects f(core_x, core_y) -> list[int]")
    self.rtas = fn
    return self

  def segment(self, addr: int, data: bytes, *, label: str = "segment"):
    self.load_segments.append(Segment(addr, bytes(data), label))
    return self

  def compile(self) -> list[Segment]:
    text = self.to_bytes()
    blobs = []
    if text:
      blobs.append(Segment(self.base, text, label="text"))
    for seg in self.load_segments:
      if seg.data:
        blobs.append(Segment(seg.addr, seg.data, label=seg.label))
    return blobs
