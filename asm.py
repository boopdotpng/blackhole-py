from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
from typing import Literal, Tuple

from isa import R, RV32, Tensix
from ttk.common import Common

_BRANCHES = {"beq", "bne", "blt", "bge", "bltu", "bgeu"}
_INVERT = {"beq": "bne", "bne": "beq", "blt": "bge", "bge": "blt", "bltu": "bgeu", "bgeu": "bltu"}
_CONDS = {"==": ("beq", False), "!=": ("bne", False), "<": ("blt", False), ">=": ("bge", False),
          "<u": ("bltu", False), ">=u": ("bgeu", False), ">": ("blt", True), "<=": ("bge", True),
          ">u": ("bltu", True), "<=u": ("bgeu", True)}
_encode = RV32()

KernelRole = Literal["brisc", "ncrisc", "trisc0", "trisc1", "trisc2"]
KERNEL_ROLES: tuple[KernelRole, ...] = ("brisc", "ncrisc", "trisc0", "trisc1", "trisc2")
Core = Tuple[int, int]  # (x, y)

class LocalMemory:
  BASE = 0xFFB00000
  SIZES = {"brisc": 8192, "ncrisc": 8192, "trisc0": 4096, "trisc1": 4096, "trisc2": 4096}
  # Firmware-local state and TTK's fixed per-role tables occupy the prefix.
  RESERVED_END = {
    "brisc": 0x878,
    "ncrisc": 0x864,
    "trisc0": 0x820,
    "trisc1": 0x140,
    "trisc2": 0x8C0,
  }
  # Match the stack reservations in the Blackhole kernel linker layouts.
  STACK_SIZE = {"brisc": 0x100, "ncrisc": 0x100, "trisc0": 0xC0, "trisc1": 0xC0, "trisc2": 0x100}

  def __init__(self, role: str | None):
    size = self.SIZES.get(role, 0)
    self.start = self.BASE + self.RESERVED_END.get(role, 0)
    self.next = self.start
    self.end = self.BASE + size - self.STACK_SIZE.get(role, 0)
    self.allocations = {}

  def alloc(self, name: str, size=4):
    addr = (self.next + 3) & -4
    if name in self.allocations: raise ValueError(f"duplicate local allocation {name!r}")
    if addr + size > self.end: raise MemoryError("RISC local memory is full")
    self.next = addr + size
    self.allocations[name] = addr
    return addr

@dataclass(frozen=True)
class Fixup:
  op: str
  args: tuple
  label: str

@dataclass(frozen=True)
class Cond:
  lhs: R
  op: str
  rhs: R | int

def _scoped(fn):
  @wraps(fn)
  def wrapped(self, *args, **kwargs):
    with self.scope(): return fn(self, *args, **kwargs)
  return wrapped

class Asm(RV32, Tensix):
  def __init_subclass__(cls):
    super().__init_subclass__()
    for name, fn in tuple(vars(cls).items()):
      if not name.startswith("_") and hasattr(fn, "__code__"): setattr(cls, name, _scoped(fn))

  def __init__(self, role: str | None = None):
    self.items, self.labels = [], {}
    # The resident firmware calls kernels through RA and establishes SP and GP.
    # TP is also runtime-owned. None of these are scratch registers.
    reserved = {R.ZERO, R.RA, R.SP, R.GP, R.TP}
    self._free, self._scopes = [reg for reg in R if reg not in reserved], []
    self._label_id, self._breaks = 0, []
    self.role = role
    self.local = LocalMemory(role)

  def _emit(self, word: int):
    self.items.append(word)
    return self

  def reg(self, n: int = 1, *, exclude=()):
    if not self._scopes: raise RuntimeError("reg() requires a register scope")
    excluded = {exclude} if isinstance(exclude, R) else set(exclude)
    available = [reg for reg in self._free if reg not in excluded]
    if n < 1 or n > len(available):
      raise RuntimeError(f"need {n} registers, {len(available)} available")
    regs = available[:n]
    self._free = [reg for reg in self._free if reg not in regs]
    self._scopes[-1] += regs
    return regs[0] if n == 1 else tuple(regs)

  @contextmanager
  def scope(self):
    self._scopes.append([])
    try: yield self
    finally: self._free = sorted(self._free + self._scopes.pop(), key=int)

  def _new_label(self, prefix="label"):
    self._label_id += 1
    return f".{prefix}_{self._label_id}"

  def label(self, name: str):
    if name in self.labels: raise ValueError(f"duplicate label {name!r}")
    self.labels[name] = len(self.items)
    return self

  def _fixup(self, op: str, args: tuple, target: str | int):
    if isinstance(target, str): self.items.append(Fixup(op, args, target))
    else: self._emit(getattr(_encode, op)(*args, target))
    return self

  def beq(self, a: R, b: R, target: str | int): return self._fixup("beq", (a, b), target)
  def bne(self, a: R, b: R, target: str | int): return self._fixup("bne", (a, b), target)
  def blt(self, a: R, b: R, target: str | int): return self._fixup("blt", (a, b), target)
  def bge(self, a: R, b: R, target: str | int): return self._fixup("bge", (a, b), target)
  def bltu(self, a: R, b: R, target: str | int): return self._fixup("bltu", (a, b), target)
  def bgeu(self, a: R, b: R, target: str | int): return self._fixup("bgeu", (a, b), target)
  def jal(self, rd: R, target: str | int): return self._fixup("jal", (rd,), target)

  def li(self, rd: R, value: int):
    value &= 0xFFFFFFFF
    signed = value - 0x100000000 if value & 0x80000000 else value
    if -2048 <= signed <= 2047: return self.addi(rd, R.ZERO, signed)
    hi, lo = (signed + 0x800) >> 12, signed - (((signed + 0x800) >> 12) << 12)
    self.lui(rd, hi << 12)
    return self.addi(rd, rd, lo) if lo else self

  def mv(self, rd: R, rs: R): return self.addi(rd, rs, 0)
  def nop(self): return self.addi(R.ZERO, R.ZERO, 0)
  def j(self, label: str): return self.jal(R.ZERO, label)

  def _branch_cond(self, c: Cond, label: str, invert=False):
    if c.op not in _CONDS: raise ValueError(f"unknown condition {c.op!r}")
    op, swap = _CONDS[c.op]
    if invert: op = _INVERT[op]
    if isinstance(c.rhs, R):
      a, b = c.lhs, c.rhs
      return getattr(self, op)(b, a, label) if swap else getattr(self, op)(a, b, label)
    if c.rhs == 0: return self._branch_cond(Cond(c.lhs, c.op, R.X0), label, invert)
    with self.scope():
      rhs = self.reg()
      self.li(rhs, c.rhs)
      return self._branch_cond(Cond(c.lhs, c.op, rhs), label, invert)

  @contextmanager
  def loop(self, condition: Cond | None = None):
    start, end = self._new_label("loop"), self._new_label("endloop")
    self.label(start)
    if condition is not None: self._branch_cond(condition, end, invert=True)
    self._breaks.append(end)
    try: yield
    finally: self._breaks.pop()
    self.j(start)
    self.label(end)

  def while_(self, condition: Cond | None = None):
    """Readable alias for a conditional assembly loop."""
    return self.loop(condition)

  @contextmanager
  def if_(self, condition: Cond):
    """Emit a guarded block with no else branch."""
    end = self._new_label("endif")
    self._branch_cond(condition, end, invert=True)
    yield
    self.label(end)

  def switch(self, value: R, cases: dict[int, str], default: str):
    """Branch to a label selected by an integer register value."""
    with self.scope():
      expected = self.reg(exclude=value)
      for literal, label in cases.items():
        self.li(expected, literal)
        self.beq(value, expected, label)
    return self.j(default)

  def break_(self, condition: Cond | None = None):
    if not self._breaks: raise RuntimeError("break_() used outside loop()")
    return self.j(self._breaks[-1]) if condition is None else self._branch_cond(condition, self._breaks[-1])

  def _layout(self):
    long = set()
    while True:
      extra, before = 0, []
      for i in range(len(self.items) + 1):
        before.append(extra)
        if i in long: extra += 1
      pc = lambda i: 4 * (i + before[i])
      targets = {name: pc(index) for name, index in self.labels.items()}
      changed = False
      for i, item in enumerate(self.items):
        if isinstance(item, Fixup) and item.op in _BRANCHES and i not in long:
          if item.label not in targets: raise ValueError(f"undefined label {item.label!r}")
          if not -4096 <= targets[item.label] - pc(i) < 4096: long.add(i); changed = True
      if not changed: return long, targets

  def instructions(self):
    long, targets = self._layout()
    out, pc = [], 0
    for i, item in enumerate(self.items):
      if not isinstance(item, Fixup): out.append(item); pc += 4; continue
      if item.label not in targets: raise ValueError(f"undefined label {item.label!r}")
      offset = targets[item.label] - pc
      if offset & 1: raise ValueError(f"misaligned target {item.label!r}")
      if i in long:
        out.append(getattr(_encode, _INVERT[item.op])(*item.args, 8))
        offset = targets[item.label] - (pc + 4)
        if not -(1 << 20) <= offset < 1 << 20: raise ValueError(f"target {item.label!r} is out of range")
        out.append(_encode.jal(R.ZERO, offset)); pc += 8
      else:
        limit = 1 << (20 if item.op == "jal" else 12)
        if not -limit <= offset < limit: raise ValueError(f"target {item.label!r} is out of range")
        out.append(getattr(_encode, item.op)(*item.args, offset)); pc += 4
    return out

  def assemble(self): return b"".join(word.to_bytes(4, "little") for word in self.instructions())

class KernelBuilder(Asm, Common):
  """Assemble one role-configured kernel using TTK helpers."""

  def __init__(self, role: KernelRole, core: Core | None,
               param_slots: dict[object, int] | None = None, *,
               standalone: bool = False):
    if role not in KERNEL_ROLES: raise ValueError(f"unknown kernel role {role!r}")
    if core is None and not standalone:
      raise TypeError("ordinary kernels require a compile-time core")
    if core is not None and (not isinstance(core, tuple) or len(core) != 2 or
        any(type(coordinate) is not int for coordinate in core)):
      raise TypeError("core must be an (x, y) tuple of Python integers")
    super().__init__(role)
    self.core: Core | None = core
    self.param_slots = {} if param_slots is None else param_slots
    self.is_standalone = bool(standalone)
    self._lowered = False
    self._return_addr = None
    if not self.is_standalone:
      self._return_addr = self.local.alloc("kernel_return_addr")
      self.store(self._return_addr, R.RA)

  @classmethod
  def standalone(cls, role: KernelRole):
    """Build an entry-point image with no generated call/return convention.

    Standalone images have no compile-time core, return-address save, local
    return slot, or implicit epilogue.  They are suitable for resident
    firmware and any other image entered directly by hardware.
    """
    return cls(role, None, standalone=True)

  def noc(self, index: int):
    """Select NoC 0 or 1 for a BRISC or NCRISC kernel."""
    if self.role not in ("brisc", "ncrisc"):
      raise RuntimeError(f"{self.role} cannot access a NoC")
    from ttk.noc import NoC
    return NoC(self, index)

  def lower(self):
    """Assemble an ordinary callable kernel or a standalone entry point."""
    if self._lowered: raise RuntimeError("kernel has already been lowered")
    if not self.is_standalone:
      with self.scope():
        return_addr = self.reg()
        self.load(return_addr, self._return_addr)
        self.jalr(R.ZERO, return_addr)
    self._lowered = True
    image = self.assemble()
    return image
