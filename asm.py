from contextlib import contextmanager
from dataclasses import dataclass
from typing import ClassVar
from fw.consts import Firmware, KernelRole, TensixL1, TensixMMIO
from isa import R, RV32, TensixWord
from pcie import Allocator

_rv32 = RV32()

def _li_words(rd: R, value: int):
  value &= 0xFFFFFFFF
  signed = value - 0x100000000 if value & 0x80000000 else value
  if -2048 <= signed <= 2047: return [_rv32.addi(rd, R.ZERO, signed)]
  hi, lo = (signed + 0x800) >> 12, signed - (((signed + 0x800) >> 12) << 12)
  words = [_rv32.lui(rd, hi << 12)]
  if lo: words.append(_rv32.addi(rd, rd, lo))
  return words

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
  BRANCHES: ClassVar[set[str]] = {"beq", "bne", "blt", "bge", "bltu", "bgeu"}
  OPS: ClassVar[dict[str, tuple[str, bool]]] = {
    "==": ("beq", False), "!=": ("bne", False), "<": ("blt", False), ">=": ("bge", False),
    "<u": ("bltu", False), ">=u": ("bgeu", False), ">": ("blt", True), "<=": ("bge", True),
    ">u": ("bltu", True), "<=u": ("bgeu", True),
  }

  def branch(self, invert=False):
    op, swap = self.OPS[self.op]
    if invert: op = self.inverse(op)
    return op, swap

  @classmethod
  def inverse(cls, op):
    return {"beq": "bne", "bne": "beq", "blt": "bge", "bge": "blt", "bltu": "bgeu", "bgeu": "bltu"}[op]

class Asm(RV32):
  def __init__(self, role: KernelRole, param_slots: dict[object, int] | None = None,
               firmware: bool = False):
    self.items, self.labels, self._prologue = [], {}, []

    reserved = {R.ZERO, R.RA, R.SP, R.GP, R.TP}
    self._free, self._scopes = [reg for reg in R if reg not in reserved], []
    self._label_id, self._breaks = 0, []
    self.role = role
    self.param_slots = {} if param_slots is None else param_slots
    self.is_firmware = bool(firmware)
    self._lowered = False
    self.local = Allocator(*Firmware.LOCAL_MEMORY.get(role, (0, 0)), 4)
    if not self.is_firmware:
      self._return_addr = self.local.alloc(4)
      self.store(self._return_addr, R.RA)
    self._body_start = len(self.items)

  @classmethod
  def firmware(cls, role: KernelRole): return cls(role, firmware=True)

  def configure_csr(self, value: R = R.T0):
    self.li(value, 2)
    self.csrrs(R.ZERO, value, 0x7C0)
    self.li(value, 1)
    self.slli(value, value, 18)
    self.fence()
    self.csrrs(R.ZERO, value, 0x7C0)
    self.li(value, 2)
    self.csrrc(R.ZERO, value, 0x7C0)
    self.fence()
    self.fence()
    self.li(value, 8)
    self.csrrs(R.ZERO, value, 0x7C0)
    return self

  def setup_stack(self, stack_top: int):
    return self.li(R.SP, stack_top)

  def call_fixed_kernel(self, entry: int, target: R = R.T0):
    self.li(target, entry)
    return self.jalr(R.RA, target, 0)

  def delay_cycles(self, cycles: int):
    if cycles == 0: return self
    with self.scope():
      counter = self.reg()
      self.li(counter, cycles)
      loop = self._new_label("delay")
      self.label(loop)
      self.addi(counter, counter, -1)
      self.bne(counter, R.ZERO, loop)
    return self

  def zero_words(self, addr: int, count: int):
    if count == 0: return self
    with self.scope():
      ptr, remaining = self.reg(2)
      self.li(ptr, addr)
      self.li(remaining, count)
      loop = self._new_label("zero_words")
      done = self._new_label("zero_words_done")
      self.label(loop)
      self.beq(remaining, R.ZERO, done)
      self.sw(R.ZERO, ptr, 0)
      self.addi(ptr, ptr, 4)
      self.addi(remaining, remaining, -1)
      self.j(loop)
      self.label(done)
    return self

  def write32(self, addr: int | R, value: int | R):
    return self.store(addr, value, bytes=4)

  def update32(self, addr: int, set_bits: int = 0, clear_bits: int = 0,
               value: R = R.T0):
    self.read32(value, addr)
    if clear_bits:
      with self.scope():
        mask = self.reg(exclude=value)
        self.li(mask, ~clear_bits)
        self.and_(value, value, mask)
    if set_bits:
      with self.scope():
        bits = self.reg(exclude=value)
        self.li(bits, set_bits)
        self.or_(value, value, bits)
    return self.write32(addr, value)

  def invalidate_risc_caches(self):
    return self.write32(TensixMMIO.RISCV_IC_INVALIDATE, TensixMMIO.RISCV_IC_ALL_MASK)

  def signal_range(self, base: int, offsets, value: int):
    for offset in offsets:
      self.write8(base + offset, value)
    return self

  def align_up(self, value: R, alignment: int, scratch: R = R.T0):
    self.li(scratch, alignment - 1)
    self.add(value, value, scratch)
    self.li(scratch, -alignment)
    return self.and_(value, value, scratch)

  def read32(self, rd: R, addr: int | R):
    return self.load(rd, addr, bytes=4)

  def write8(self, addr: int | R, value: int | R):
    return self.store(addr, value, bytes=1)

  def signal8(self, addr: int | R, value: int):
    return self.write8(addr, value)

  def wait8(self, addr: int, value: int, ptr: R = R.T0,
            actual: R = R.T1, expected: R = R.T2):
    value = int(value)
    self.li(ptr, addr)
    self.li(expected, value)
    loop = self._new_label("wait8")
    done = self._new_label("wait8_done")
    self.label(loop)
    self.lbu(actual, ptr, 0)
    self.beq(actual, expected, done)
    self.fence()
    self.j(loop)
    self.label(done)
    return self.fence()

  def load(self, rd: R, addr: int | R, bytes=4):
    op = {1: self.lbu, 2: self.lhu, 4: self.lw}[bytes]
    if isinstance(addr, R): return op(rd, addr)
    with self.scope():
      base = self.reg(exclude=rd)
      self.li(base, addr)
      return op(rd, base)

  def store(self, addr: int | R, value: int | R, bytes=4):
    op = {1: self.sb, 2: self.sh, 4: self.sw}[bytes]
    with self.scope():
      if not isinstance(addr, R):
        excluded = value if isinstance(value, R) else ()
        self.li(base := self.reg(exclude=excluded), addr)
      else: base = addr
      if not isinstance(value, R): self.li(src := self.reg(exclude=base), value)
      else: src = value
      return op(src, base)

  def param(self, param):
    reg = self.reg()
    self.load(reg, TensixL1.PARAM_BASE + self.param_slots[param] * 4)
    return reg

  @property
  def noc(self):
    if self.role not in ("brisc", "ncrisc"):
      raise RuntimeError(f"{self.role} cannot access a NoC")
    return self.noc_at(0 if self.role == "brisc" else 1)

  def noc_at(self, index: int):
    if self.role not in ("brisc", "ncrisc"):
      raise RuntimeError(f"{self.role} cannot access a NoC")
    from ttk.noc import NoC
    return NoC(self, index)

  def _emit(self, word: int):
    if self._lowered: raise RuntimeError("kernel has already been lowered")
    if isinstance(word, TensixWord):
      if self.role == "brisc":
        return self.write32(TensixMMIO.INSTRN_BUF_BASE, int(word))
      if self.role == "ncrisc": raise RuntimeError("ncrisc cannot emit Tensix instructions")
      if self.role not in ("trisc0", "trisc1", "trisc2"):
        raise RuntimeError(f"{self.role} cannot emit Tensix instructions")
    self.items.append(word)
    return self

  def emit(self, word: int): return self._emit(word)

  def reg(self, n: int = 1, exclude=()):
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
    else: self._emit(getattr(_rv32, op)(*args, target))
    return self

  def beq(self, a: R, b: R, target: str | int): return self._fixup("beq", (a, b), target)
  def bne(self, a: R, b: R, target: str | int): return self._fixup("bne", (a, b), target)
  def blt(self, a: R, b: R, target: str | int): return self._fixup("blt", (a, b), target)
  def bge(self, a: R, b: R, target: str | int): return self._fixup("bge", (a, b), target)
  def bltu(self, a: R, b: R, target: str | int): return self._fixup("bltu", (a, b), target)
  def bgeu(self, a: R, b: R, target: str | int): return self._fixup("bgeu", (a, b), target)
  def jal(self, rd: R, target: str | int): return self._fixup("jal", (rd,), target)

  def li(self, rd: R, value: int):
    for word in _li_words(rd, value): self._emit(word)
    return self

  def initialize_local(self, addr: int, value: int):
    self._prologue += _li_words(R.T0, addr)
    source = R.ZERO
    if value:
      self._prologue += _li_words(R.T1, value)
      source = R.T1
    self._prologue.append(_rv32.sw(source, R.T0, 0))
    return self

  def initialize_tensix(self, *words):
    if self._lowered: raise RuntimeError("kernel has already been lowered")
    if self.role not in ("trisc0", "trisc1", "trisc2"):
      raise RuntimeError(f"{self.role} cannot initialize Tensix instructions")
    if any(not isinstance(word, TensixWord) for word in words):
      raise TypeError("Tensix initialization requires Tensix instructions")
    self._prologue.extend(words)
    return self

  def mv(self, rd: R, rs: R): return self.addi(rd, rs, 0)
  def nop(self): return self.addi(R.ZERO, R.ZERO, 0)
  def j(self, label: str): return self.jal(R.ZERO, label)

  def _branch_cond(self, c: Cond, label: str, invert=False):
    op, swap = c.branch(invert)
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

  def range(self, count: int | R):
    with self.scope():
      index, limit = self.reg(2, exclude=count if isinstance(count, R) else ())
      self.li(index, 0)
      if isinstance(count, R): self.mv(limit, count)
      else: self.li(limit, count)
      with self.loop(Cond(index, "<u", limit)):
        yield index
        self.addi(index, index, 1)

  @contextmanager
  def if_(self, condition: Cond):
    end = self._new_label("endif")
    self._branch_cond(condition, end, invert=True)
    yield
    self.label(end)

  def switch(self, value: R, cases: dict[int, str], default: str):
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
        if isinstance(item, Fixup) and item.op in Cond.BRANCHES and i not in long:
          if item.label not in targets: raise ValueError(f"undefined label {item.label!r}")
          if not -4096 <= targets[item.label] - pc(i) < 4096: long.add(i); changed = True
      if not changed: return long, targets

  def instructions(self):
    long, targets = self._layout()
    out, pc = [], 0
    for i, item in enumerate(self.items):
      if not isinstance(item, Fixup):
        # Only Tensix words inline in the RISC-V stream rotate by two. Words
        # embedded in MMIO writes or MOP config are ordinary, unrotated data.
        word = ((item << 2) | (item >> 30)) & 0xFFFFFFFF if isinstance(item, TensixWord) else item
        out.append(word); pc += 4; continue
      if item.label not in targets: raise ValueError(f"undefined label {item.label!r}")
      offset = targets[item.label] - pc
      if offset & 1: raise ValueError(f"misaligned target {item.label!r}")
      if i in long:
        out.append(getattr(_rv32, Cond.inverse(item.op))(*item.args, 8))
        offset = targets[item.label] - (pc + 4)
        if not -(1 << 20) <= offset < 1 << 20: raise ValueError(f"target {item.label!r} is out of range")
        out.append(_rv32.jal(R.ZERO, offset)); pc += 8
      else:
        limit = 1 << (20 if item.op == "jal" else 12)
        if not -limit <= offset < limit: raise ValueError(f"target {item.label!r} is out of range")
        out.append(getattr(_rv32, item.op)(*item.args, offset)); pc += 4
    return out

  def assemble(self): return b"".join(word.to_bytes(4, "little") for word in self.instructions())

  def lower(self):
    if self._lowered: raise RuntimeError("kernel has already been lowered")
    if self._prologue:
      count = len(self._prologue)
      self.items[self._body_start:self._body_start] = self._prologue
      self.labels = {
        name: index + count if index >= self._body_start else index
        for name, index in self.labels.items()
      }
      self._prologue = []
    if not self.is_firmware:
      with self.scope():
        return_addr = self.reg()
        self.load(return_addr, self._return_addr)
        self.jalr(R.ZERO, return_addr)
    self._lowered = True
    return self.assemble()
