"""Shared RISC-V/Tensix assembler with virtual or scoped physical registers."""

from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
from typing import ClassVar
from firmware.consts import Firmware, KernelRole, TensixL1, TensixMMIO
from ttko.isa import Insn, R, RV32, Reg, TensixWord, VReg, is_reg
from pcie import Allocator

_rv32 = RV32()
_SYMBOLIC_OPS = """add sub mul divu remu sltu min and_ or_ xor addi sltiu andi ori xori
  slli srli srai lw lbu lhu sb sh sw lui auipc jalr csrrs csrrc fence""".split()

def _li_words(rd: Reg, value: int):
  value &= 0xFFFFFFFF
  signed = value - 0x100000000 if value & 0x80000000 else value
  if -2048 <= signed <= 2047: return [Insn("addi", (rd, R.ZERO, signed))]
  hi, lo = (signed + 0x800) >> 12, signed - (((signed + 0x800) >> 12) << 12)
  words = [Insn("lui", (rd, hi << 12))]
  if lo: words.append(Insn("addi", (rd, rd, lo)))
  return words

def scoped(fn):
  @wraps(fn)
  def wrapped(asm, *args, **kwargs):
    with asm.scope(): return fn(asm, *args, **kwargs)
  return wrapped

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

class Asm:
  """Use virtual registers by default; physical_regs preserves fixed schedules.

  Both policies share symbolic instructions, branch relaxation and encoding.
  """
  _BRANCHES = {"beq": "bne", "bne": "beq", "blt": "bge", "bge": "blt", "bltu": "bgeu", "bgeu": "bltu"}
  _DEFINES = {
    "add", "sub", "mul", "divu", "remu", "sltu", "min", "and_", "or_", "xor",
    "addi", "sltiu", "andi", "ori", "xori", "slli", "srli", "srai",
    "lw", "lbu", "lhu", "lui", "auipc", "jal", "jalr", "csrrs", "csrrc",
  }

  def __init__(self, role: KernelRole, firmware: bool = False, *,
               param_slots=None, physical_regs=False):
    self.items, self.labels, self._prologue = [], {}, []

    self.physical_regs = physical_regs
    self.param_slots = {} if param_slots is None else param_slots
    self._free = [r for r in R if r not in {R.ZERO, R.RA, R.SP, R.GP}]
    self._scopes, self._breaks = [], []
    self._vreg_id = self._label_id = 0
    self.role = role
    self.is_firmware = bool(firmware)
    self.base = Firmware.TEXT[role][0] if firmware else TensixL1.WORKER_TEXT_BASE[role]
    self._lowered = False
    self.local = Allocator(*Firmware.LOCAL_MEMORY.get(role, (0, 0)), 4)

  @classmethod
  def firmware(cls, role: KernelRole): return cls(role, firmware=True)

  @scoped
  def wait(self, addr: int, value: int, bytes=1):
    ptr, actual, expected = self.reg(3)
    self.li(ptr, addr)
    self.li(expected, int(value))
    loop = self._new_label("wait")
    done = self._new_label("wait_done")
    self.label(loop)
    self.read(actual, ptr, bytes=bytes)
    self.beq(actual, expected, done)
    self.fence()
    self.j(loop)
    self.label(done)
    return self.fence()

  @scoped
  def read(self, rd: R, addr: int | R, bytes=4, *, tmp_addr: R | None = None):
    op = {1: self.lbu, 2: self.lhu, 4: self.lw}[bytes]
    if is_reg(addr): return op(rd, addr)
    base = self.reg(exclude=rd) if tmp_addr is None else tmp_addr
    self.li(base, addr)
    return op(rd, base)

  @scoped
  def write(self, addr: int | R, value: int | R, bytes=4, *, tmp_addr: R | None = None, tmp_val: R | None = None):
    op = {1: self.sb, 2: self.sh, 4: self.sw}[bytes]
    if not is_reg(addr):
      excluded = value if is_reg(value) else ()
      base = self.reg(exclude=excluded) if tmp_addr is None else tmp_addr
      self.li(base, addr)
    else: base = addr
    if not is_reg(value):
      src = self.reg(exclude=base) if tmp_val is None else tmp_val
      self.li(src, value)
    else: src = value
    return op(src, base)

  def _emit(self, word: int):
    if self._lowered: raise RuntimeError("kernel has already been lowered")
    if isinstance(word, TensixWord):
      if self.role == "brisc":
        return self.write(TensixMMIO.INSTRN_BUF_BASE, int(word))
      if self.role == "ncrisc": raise RuntimeError("ncrisc cannot emit Tensix instructions")
      if self.role not in ("trisc0", "trisc1", "trisc2"):
        raise RuntimeError(f"{self.role} cannot emit Tensix instructions")
    self.items.append(word)
    return self

  def emit(self, word: int): return self._emit(word)

  def _ins(self, op: str, *args):
    # Physical operands are final; avoid building a symbolic node for each
    # ordinary instruction. Label fixups still use the shared lowering path.
    return self._emit(getattr(_rv32, op)(*args) if self.physical_regs else Insn(op, args))

  def __getattr__(self, op):
    if op not in _SYMBOLIC_OPS: raise AttributeError(op)
    return lambda *args: self._ins(op, *args)

  def reg(self, n: int = 1, exclude=()):
    if not self.physical_regs:
      if n < 1: raise ValueError("register count must be positive")
      regs = tuple(VReg(self._vreg_id + i) for i in range(n))
      self._vreg_id += n
      return regs[0] if n == 1 else tuple(regs)
    if not self._scopes: raise RuntimeError("reg() requires a register scope")
    excluded = {exclude} if isinstance(exclude, R) else set(exclude)
    available = [reg for reg in self._free if reg not in excluded]
    if n < 1 or n > len(available):
      raise RuntimeError(f"need {n} registers, {len(available)} available")
    regs = available[:n]
    self._free = [reg for reg in self._free if reg not in regs]
    self._scopes[-1] += regs
    return regs[0] if n == 1 else tuple(regs)

  def _new_label(self, prefix="label"):
    self._label_id += 1
    return f".{prefix}_{self._label_id}"

  def label(self, name: str):
    if name in self.labels: raise ValueError(f"duplicate label {name!r}")
    self.labels[name] = len(self.items)
    return self

  def _fixup(self, op: str, args: tuple, target: str | int):
    self._emit(Insn(op, args, target) if isinstance(target, str) else Insn(op, (*args, target)))
    return self

  def beq(self, a: Reg, b: Reg, target: str | int): return self._fixup("beq", (a, b), target)
  def bne(self, a: Reg, b: Reg, target: str | int): return self._fixup("bne", (a, b), target)
  def blt(self, a: Reg, b: Reg, target: str | int): return self._fixup("blt", (a, b), target)
  def bge(self, a: Reg, b: Reg, target: str | int): return self._fixup("bge", (a, b), target)
  def bltu(self, a: Reg, b: Reg, target: str | int): return self._fixup("bltu", (a, b), target)
  def bgeu(self, a: Reg, b: Reg, target: str | int): return self._fixup("bgeu", (a, b), target)
  def jal(self, rd: Reg, target: str | int): return self._fixup("jal", (rd,), target)

  def li(self, rd: Reg, value: int):
    for word in _li_words(rd, value): self._emit(word)
    return self

  @scoped
  def initialize_local(self, addr: int, value: int):
    address, source = self.reg(2)
    self._prologue += _li_words(address, addr)
    if value: self._prologue += _li_words(source, value)
    else: source = R.ZERO
    self._prologue.append(Insn("sw", (source, address, 0)))
    return self

  def mv(self, rd: Reg, rs: Reg): return self.addi(rd, rs, 0)
  def j(self, target: str | int):
    if isinstance(target, str): return self.jal(R.ZERO, target)
    self.items.append(Insn("jal", (R.ZERO,), target)); return self

  def range(self, count: int | R):
    with self.scope():
      index, limit = self.reg(2, exclude=count if is_reg(count) else ())
      self.li(index, 0)
      if is_reg(count): self.mv(limit, count)
      else: self.li(limit, count)
      with self.loop(Cond(index, "<u", limit)):
        yield index
        self.addi(index, index, 1)

  def _allocate_registers(self):
    """Control-flow liveness followed by a no-spill linear scan."""
    items, labels, base = self.items, self.labels, self.base
    branches, defines = self._BRANCHES.keys(), self._DEFINES
    count = len(items)

    def uses_defs(item):
      if not isinstance(item, Insn): return set(), set()
      cut = int(item.op in defines)
      defs = {item.args[0]} if cut and item.args and is_reg(item.args[0]) else set()
      return {arg for arg in item.args[cut:] if is_reg(arg)}, defs

    def successors(i):
      item, following = items[i], (i + 1,) if i + 1 < count else ()
      if not isinstance(item, Insn) or item.op not in branches | {"jal"}: return following
      if item.target is None:
        offset = item.args[-1]
        target = i + offset // 4 if isinstance(offset, int) and offset % 4 == 0 else None
      elif isinstance(item.target, str): target = labels.get(item.target)
      else:
        offset = item.target - (base + i * 4)
        target = i + offset // 4 if offset % 4 == 0 else None
      destination = (target,) if target is not None and 0 <= target < count else ()
      return (*following, *destination) if item.op in branches else destination

    ud, succ = [uses_defs(item) for item in items], [successors(i) for i in range(count)]
    live_in = [set() for _ in items]
    changed = True
    while changed:
      changed = False
      for i in range(count - 1, -1, -1):
        uses, defs = ud[i]
        outgoing = set().union(*(live_in[j] for j in succ[i])) if succ[i] else set()
        incoming = uses | (outgoing - defs)
        if incoming != live_in[i]: live_in[i], changed = incoming, True

    points = {}
    for i, ((uses, defs), incoming) in enumerate(zip(ud, live_in)):
      for reg in uses | defs | incoming: points.setdefault(reg, []).append(i)
    intervals = {reg: (min(pos), max(pos)) for reg, pos in points.items() if isinstance(reg, VReg)}
    fixed = {arg for item in items if isinstance(item, Insn) for arg in item.args if isinstance(arg, R)}
    pool = tuple(reg for reg in R if reg not in {R.ZERO, R.RA, R.SP, R.GP} | fixed)
    ranges = sorted((start, end, reg) for reg, (start, end) in intervals.items())

    allocation, active = {}, []
    for start, end, reg in ranges:
      active = [entry for entry in active if entry[0] >= start]
      available = [candidate for candidate in pool if candidate not in {entry[2] for entry in active}]
      if not available:
        live = ", ".join(str(item[1]) for item in sorted(active, key=lambda item: item[1].index))
        raise RuntimeError(f"register allocation failed for {reg} at instruction {start}; {len(active)} virtual registers are live ({live})")
      allocation[reg] = available[0]
      active.append((end, reg, available[0]))
    return allocation

  @staticmethod
  def _resolve(args, allocation):
    return tuple(allocation.get(arg, arg) if isinstance(arg, VReg) else arg for arg in args)

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
        if isinstance(item, Insn) and item.target is not None and item.op in self._BRANCHES.keys() and i not in long:
          if item.target not in targets: raise ValueError(f"undefined label {item.target!r}")
          if not -4096 <= targets[item.target] - pc(i) < 4096: long.add(i); changed = True
      if not changed: return long, targets

  def instructions(self):
    allocation = {} if self.physical_regs else self._allocate_registers()
    long, targets = self._layout()
    out, pc = [], 0
    for i, item in enumerate(self.items):
      if not isinstance(item, Insn):
        # Only Tensix words inline in the RISC-V stream rotate by two. Words
        # embedded in MMIO writes or MOP config are ordinary, unrotated data.
        word = ((item << 2) | (item >> 30)) & 0xFFFFFFFF if isinstance(item, TensixWord) else item
        out.append(word); pc += 4; continue
      args = self._resolve(item.args, allocation)
      if item.target is None:
        out.append(getattr(_rv32, item.op)(*args)); pc += 4; continue
      if isinstance(item.target, str):
        if item.target not in targets: raise ValueError(f"undefined label {item.target!r}")
        offset = targets[item.target] - pc
      else: offset = item.target - (self.base + pc)
      if offset & 1: raise ValueError(f"misaligned target {item.target!r}")
      if i in long:
        out.append(getattr(_rv32, self._BRANCHES[item.op])(*args, 8))
        offset = targets[item.target] - (pc + 4)
        if not -(1 << 20) <= offset < 1 << 20: raise ValueError(f"target {item.target!r} is out of range")
        out.append(_rv32.jal(R.ZERO, offset)); pc += 8
      else:
        limit = 1 << (20 if item.op == "jal" else 12)
        if not -limit <= offset < limit: raise ValueError(f"target {item.target!r} is out of range")
        out.append(getattr(_rv32, item.op)(*args, offset)); pc += 4
    return out

  def assemble(self): return b"".join(word.to_bytes(4, "little") for word in self.instructions())

  def lower(self):
    if self._lowered: raise RuntimeError("kernel has already been lowered")
    if not self.is_firmware: self.j(Firmware.TEXT[self.role][0])
    if self._prologue:
      count = len(self._prologue)
      self.items[:0] = self._prologue
      self.labels = {
        name: index + count
        for name, index in self.labels.items()
      }
      self._prologue = []
    self._lowered = True
    return self.assemble()

  @contextmanager
  def scope(self):
    self._scopes.append([])
    try: yield self
    finally: self._free = sorted(self._free + self._scopes.pop(), key=int)

  @scoped
  def configure_csr(self):
    value = self.reg()
    self.li(value, 2)
    self.csrrs(R.ZERO, value, 0x7C0)
    self.li(value, 1)
    self.slli(value, value, 18)
    self.fence()
    # DisTriscCache only controls fusion on TRISCs.
    if self.role.startswith("trisc"):
      self.csrrc(R.ZERO, value, 0x7C0)
    else:
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

  @scoped
  def zero_words(self, addr: int, count: int):
    if count == 0: return self
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

  def invalidate_risc_caches(self):
    return self.write(TensixMMIO.RISCV_IC_INVALIDATE, TensixMMIO.RISCV_IC_ALL_MASK)

  @scoped
  def align_up(self, value: R, alignment: int):
    scratch = self.reg(exclude=value)
    self.li(scratch, alignment - 1)
    self.add(value, value, scratch)
    self.li(scratch, -alignment)
    return self.and_(value, value, scratch)

  def read32(self, dst, address, *, tmp_addr=R.T0): return self.read(dst, address, tmp_addr=tmp_addr)

  def read8(self, dst, address, *, tmp_addr=R.T0): return self.read(dst, address, bytes=1, tmp_addr=tmp_addr)

  def write32(self, address, value, *, tmp_addr=R.T0, tmp_val=R.T1):
    return self.write(address, value, tmp_addr=tmp_addr, tmp_val=tmp_val)

  def write8(self, address, value, *, tmp_addr=R.T0, tmp_val=R.T1):
    return self.write(address, value, bytes=1, tmp_addr=tmp_addr, tmp_val=tmp_val)

  def wait_sync_value(self, address, value_reg, *, ptr=R.T0, actual=R.T1):
    self.li(ptr, address)
    loop = self._new_label('sync')
    self.label(loop); self.fence(); self.lw(actual, ptr, 0); self.bne(actual, value_reg, loop)
    return self.fence()

  def wait8(self, address, value, *, ptr=R.T0, actual=R.T1, expected=R.T2):
    self.li(ptr, address); self.li(expected, value)
    loop = self._new_label('wait8')
    self.label(loop); self.fence(); self.lbu(actual, ptr, 0); self.bne(actual, expected, loop)
    return self.fence()

  @property
  def noc(self):
    if self.role not in ("brisc", "ncrisc"):
      raise RuntimeError(f"{self.role} cannot access a NoC")
    return self.noc_at(0 if self.role == "brisc" else 1)

  def noc_at(self, index: int):
    if self.role not in ("brisc", "ncrisc"):
      raise RuntimeError(f"{self.role} cannot access a NoC")
    from ttko.noc import NoC
    return NoC(self, index)

  def initialize_tensix(self, *words):
    if self._lowered: raise RuntimeError("kernel has already been lowered")
    if self.role not in ("trisc0", "trisc1", "trisc2"):
      raise RuntimeError(f"{self.role} cannot initialize Tensix instructions")
    if any(not isinstance(word, TensixWord) for word in words):
      raise TypeError("Tensix initialization requires Tensix instructions")
    self._prologue.extend(words)
    return self

  def _branch_cond(self, c: Cond, label: str, invert=False):
    op, swap = c.branch(invert)
    if is_reg(c.rhs):
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

  @scoped
  def switch(self, value: R, cases: dict[int, str], default: str):
    expected = self.reg(exclude=value)
    for literal, label in cases.items():
      self.li(expected, literal)
      self.beq(value, expected, label)
    return self.j(default)

  def break_(self, condition: Cond | None = None):
    if not self._breaks: raise RuntimeError("break_() used outside loop()")
    return self.j(self._breaks[-1]) if condition is None else self._branch_cond(condition, self._breaks[-1])
