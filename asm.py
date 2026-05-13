from __future__ import annotations
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
import dsl
from dsl import Reg, ra, zero

CoreArgs = Callable[[int, int], list[int]]

_ZERO = zero
_RA = ra

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

@dataclass(frozen=True)
class KernelBlob:
  addr: int
  data: bytes
  label: str = ""

@dataclass(frozen=True)
class LoadSegment:
  addr: int
  data: bytes
  label: str = ""

def cond(lhs: Reg, op: str, rhs: Reg | int, *, tmp: Reg | None = None) -> Cond:
  if isinstance(rhs, int) and tmp is None:
    raise ValueError("integer condition rhs needs tmp=Reg(...)")
  return Cond(lhs, op, rhs, tmp)

KERNEL_KINDS = ("brisc", "ncrisc", "trisc0", "trisc1", "trisc2")
FIRMWARE_TEXT_BASE = {
  "brisc": 0x38C0,
  "ncrisc": 0x5AC0,
  "trisc0": 0x64C0,
  "trisc1": 0x6EC0,
  "trisc2": 0x78C0,
}
FIRMWARE_SCRATCH_BASE = {
  "brisc": 0x82B0,
  "ncrisc": 0xA2B0,
  "trisc0": 0xC2B0,
  "trisc1": 0xD2B0,
  "trisc2": 0xE2B0,
}
_FIRMWARE_LOCAL_MEM_SIZE = {
  "brisc": 8 * 1024,
  "ncrisc": 8 * 1024,
  "trisc0": 4 * 1024,
  "trisc1": 4 * 1024,
  "trisc2": 4 * 1024,
}
_FIRMWARE_RESERVED_STACK = {
  "brisc": 256,
  "ncrisc": 256,
  "trisc0": 192,
  "trisc1": 192,
  "trisc2": 256,
}

def _u32(v: int) -> bytes:
  return (v & 0xFFFFFFFF).to_bytes(4, "little")

_FIRMWARE_LOCAL_DATA = {
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
    if not isinstance(item, _Ref):
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
    # Python keywords cannot be method names, so use and_/or_ for those opcodes.
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
    # Round up when bit 11 is set because addi sign-extends the low 12 bits.
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
    rtas: CoreArgs | None = None,
  ):
    if kind not in KERNEL_KINDS:
      raise ValueError(f"unknown kernel kind {kind!r}")
    super().__init__(base=0 if base is None else base)
    self.upload_base = self.base if upload_base is None else upload_base
    self.rtas = rtas
    self.kind = kind
    self.load_segments: list[LoadSegment] = []

  def rta(self, fn: CoreArgs):
    if not callable(fn):
      raise TypeError("rta() expects f(core_x, core_y) -> list[int]")
    self.rtas = fn
    return self

  def segment(self, addr: int, data: bytes, *, label: str = "segment"):
    self.load_segments.append(LoadSegment(addr, bytes(data), label))
    return self

  def compile(self) -> list[KernelBlob]:
    text = self.to_bytes()
    blobs = []
    if text:
      blobs.append(KernelBlob(self.upload_base, text, label="text"))
    for seg in self.load_segments:
      if seg.data:
        blobs.append(KernelBlob(seg.addr, seg.data, label=seg.label))
    return blobs

class Firmware(Kernel):
  def __init__(self, kind: str):
    if kind not in FIRMWARE_TEXT_BASE:
      raise ValueError(f"unknown firmware kind {kind!r}")
    super().__init__(kind=kind, base=FIRMWARE_TEXT_BASE[kind])

  def compile(self) -> list[KernelBlob]:
    blobs = [
      KernelBlob(seg.addr, seg.data, label=f"{self.kind}.{seg.label or 'segment'}")
      for seg in super().compile()
    ]
    local_data = _FIRMWARE_LOCAL_DATA[self.kind]
    local_memsz = max(
      len(local_data),
      _FIRMWARE_LOCAL_MEM_SIZE[self.kind] - _FIRMWARE_RESERVED_STACK[self.kind],
    )
    if local_memsz:
      blobs.append(KernelBlob(
        FIRMWARE_SCRATCH_BASE[self.kind],
        local_data.ljust(local_memsz, b"\0"),
        label=f"{self.kind}.local_data",
      ))
    return blobs
