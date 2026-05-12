from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass

import dsl
from dsl import Reg

CoreArgs = Callable[[int, int], list[int]]

_ZERO = Reg(0)
_RA = Reg(1)


@dataclass(frozen=True)
class Segment:
  addr: int
  data: bytes
  label: str = ""


@dataclass(frozen=True)
class _Ref:
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


def cond(lhs: Reg, op: str, rhs: Reg | int, *, tmp: Reg | None = None) -> Cond:
  return Cond(lhs, op, rhs, tmp)


def _u32(v):
  return (v & 0xFFFFFFFF).to_bytes(4, "little")


_LOCAL_DATA = {
  "brisc": b"",
  "ncrisc": b"\0" * 40,
  "trisc0": b"\0" * 4,
  "trisc1": bytes([4]) * 32 + _u32(5) * 32 + _u32(5) * 32,
  "trisc2": bytes([16]) * 32 + bytes([4]) * 32 + b"\0" * 32 + bytes([5]) * 32 + bytes([5]) * 32,
}


class Asm:
  def __init__(self, *, base: int = 0):
    self.base = base
    self.items = []
    self.labels: dict[str, int] = {}
    self._label_id = 0

  @property
  def pc(self) -> int:
    return self.base + 4 * len(self.items)

  def _new_label(self, prefix: str) -> str:
    self._label_id += 1
    return f".L{prefix}_{self._label_id}"

  def emit(self, *insns):
    self.items.extend(insns)
    return self

  def label(self, name: str):
    if name in self.labels:
      raise ValueError(f"duplicate label {name!r}")
    self.labels[name] = self.pc
    return self

  def _ref(self, op: str, operands: tuple, label: str):
    self.items.append(_Ref(op, operands, label, self.pc))
    return self

  def _rv_emit(self, name: str, *args):
    if name in {"beq", "bne", "blt", "bge", "bltu", "bgeu", "jal"} and args and isinstance(args[-1], str):
      return self._ref(name, args[:-1], args[-1])
    return self.emit(getattr(dsl, name)(*args))

  def __getattr__(self, name: str):
    opname = {"and_": "and", "or_": "or"}.get(name, name)
    if hasattr(dsl, opname) and callable(getattr(dsl, opname)):
      return lambda *args: self._rv_emit(opname, *args)
    raise AttributeError(name)

  # Pseudo-instructions.
  def li(self, rd: Reg, imm: int):
    if -2048 <= imm <= 2047:
      return self.addi(rd, _ZERO, imm)
    imm32 = imm & 0xFFFFFFFF
    signed = imm32 - 0x100000000 if imm32 & 0x80000000 else imm32
    hi = (signed + 0x800) >> 12
    lo = signed - (hi << 12)
    self.lui(rd, (hi & 0xFFFFF) << 12)
    if lo:
      self.addi(rd, rd, lo)
    return self

  def mv(self, rd: Reg, rs: Reg): return self.addi(rd, rs, 0)
  def nop(self): return self.addi(_ZERO, _ZERO, 0)
  def j(self, label: str): return self._ref("jal", (_ZERO,), label)
  def call(self, label: str): return self._ref("jal", (_RA,), label)
  def ret(self): return self.jalr(_ZERO, _RA, 0)

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
    if not isinstance(item, _Ref):
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
    self, *, kind: str, base: int | None = None, upload_base: int | None = None,
    rtas: CoreArgs | None = None, crtas: list[int] | None = None,
    local_data=None,
  ):
    if kind not in _LOCAL_DATA:
      raise ValueError(f"unknown kernel kind {kind!r}")
    super().__init__(base=0 if base is None else base)
    self.upload_base = self.base if upload_base is None else upload_base
    self.rtas = rtas
    self.crtas = [] if crtas is None else crtas
    self.kind = kind
    self.local_data = local_data

  def rta(self, fn: CoreArgs):
    if not callable(fn):
      raise TypeError("rta() expects f(core_x, core_y) -> list[int]")
    self.rtas = fn
    return self

  def crta(self, *values):
    self.crtas = list(values[0]) if len(values) == 1 and isinstance(values[0], (list, tuple)) else list(values)
    return self

  def _local_data(self) -> bytes:
    if self.local_data is not None:
      return bytes(self.local_data)
    return _LOCAL_DATA[self.kind]

  def compile(self) -> list[Segment]:
    text = self.to_bytes()
    local_data = self._local_data()
    segments = []
    if text:
      segments.append(Segment(self.upload_base, text, label="text"))
    if local_data:
      segments.append(Segment(self.upload_base + len(text), local_data, label="local_data"))
    return segments


__all__ = ["Asm", "Cond", "Kernel", "Reg", "Segment", "cond"]
