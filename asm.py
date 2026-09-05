from fw.consts import Firmware, KernelRole, TensixL1, TensixMMIO
from isa import Insn, R, RV32, Reg, TensixWord, VReg, is_reg
from pcie import Allocator
from regalloc import allocate

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

class Asm:
  _BRANCHES = {"beq": "bne", "bne": "beq", "blt": "bge", "bge": "blt", "bltu": "bgeu", "bgeu": "bltu"}
  _DEFINES = {
    "add", "sub", "mul", "divu", "remu", "sltu", "min", "and_", "or_", "xor",
    "addi", "sltiu", "andi", "ori", "xori", "slli", "srli", "srai",
    "lw", "lbu", "lhu", "lui", "auipc", "jal", "jalr", "csrrs", "csrrc",
  }

  def __init__(self, role: KernelRole, firmware: bool = False):
    self.items, self.labels, self._prologue = [], {}, []

    self._vreg_id = self._label_id = 0
    self.role = role
    self.is_firmware = bool(firmware)
    self.base = Firmware.TEXT[role][0] if firmware else TensixL1.WORKER_TEXT_BASE[role]
    self._lowered = False
    self.local = Allocator(*Firmware.LOCAL_MEMORY.get(role, (0, 0)), 4)

  @classmethod
  def firmware(cls, role: KernelRole): return cls(role, firmware=True)

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

  def read(self, rd: Reg, addr: int | Reg, bytes=4):
    op = {1: self.lbu, 2: self.lhu, 4: self.lw}[bytes]
    if is_reg(addr): return op(rd, addr)
    base = self.reg()
    self.li(base, addr)
    return op(rd, base)

  def write(self, addr: int | Reg, value: int | Reg, bytes=4):
    op = {1: self.sb, 2: self.sh, 4: self.sw}[bytes]
    if not is_reg(addr):
      self.li(base := self.reg(), addr)
    else: base = addr
    if not is_reg(value): self.li(src := self.reg(), value)
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

  def _ins(self, op: str, *args): return self._emit(Insn(op, args))

  def __getattr__(self, op):
    if op not in _SYMBOLIC_OPS: raise AttributeError(op)
    return lambda *args: self._ins(op, *args)

  def reg(self, n: int = 1):
    if n < 1: raise ValueError("register count must be positive")
    regs = tuple(VReg(self._vreg_id + i) for i in range(n))
    self._vreg_id += n
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

  def range(self, count: int | Reg):
    index, limit = self.reg(2)
    self.li(index, 0)
    if is_reg(count): self.mv(limit, count)
    else: self.li(limit, count)
    start, end = self._new_label("loop"), self._new_label("endloop")
    self.label(start)
    self.bgeu(index, limit, end)
    yield index
    self.addi(index, index, 1)
    self.j(start)
    self.label(end)

  def _allocate_registers(self):
    return allocate(self.items, self.labels, self.base, self._BRANCHES.keys(), self._DEFINES)

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
    allocation = self._allocate_registers()
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
