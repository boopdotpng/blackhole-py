from __future__ import annotations
import functools
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
import dsl
from dsl import Reg, ra, sp, t0, t1, t2, t3, t4, t5, t6, zero


class _Launch:
  BASE = 0x70
  MSG_SIZE = 96
  KERNEL_CONFIG_BASE = 0
  KERNEL_TEXT_OFFSET = 44
  ENABLES = 76


class _Mailbox:
  SUBORDINATE_SYNC = 0x68
  LAUNCH_MSG_RD_PTR = 0x6C
  GO_SIGNAL = 0x373


class _RunMsg:
  GO = 0x80
  DONE = 0x00

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

_BRANCH_OPS = {"beq", "bne", "blt", "bge", "bltu", "bgeu"}
_INVERT_BRANCH = {
  "beq": "bne",
  "bne": "beq",
  "blt": "bge",
  "bge": "blt",
  "bltu": "bgeu",
  "bgeu": "bltu",
}


class Asm:
  """Pure RISC-V assembler core: instruction emission, register-constant
  tracking, pseudo-ops and structured control flow. Carries no device-role
  helpers — those live in the ttk mixins (Tensix, Noc, Cb, Flow, Debug), which
  concrete kernel classes compose on top of this core."""

  def __init__(self, *, base: int = 0):
    self.base = base
    self.items = []
    self.labels: dict[str, int] = {}
    self._label_id = 0
    self._reg_consts: dict[int, int] = {}
    self.regs = RegAlloc()

  def tmp(self, n: int = 1):
    """Allocate n scratch GPRs into the current @with_scope/`with self.scope()`
    scope; freed when it exits. See RegAlloc."""
    return self.regs.tmp(n)

  def scope(self):
    """`with self.scope():` — manual scratch scope (see @with_scope)."""
    return self.regs.scope()

  def scratch(self, n: int = 1):
    """`with self.scratch(n) as regs:` — scope that frees regs early on exit."""
    return self.regs.scratch(n)

  def reserve_regs(self, *regs):
    """Remove regs from the scratch pool for this kernel's lifetime."""
    return self.regs.reserve(*regs)

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

  def _addr_reg_offset(self, addr: int | Reg, tmp_addr: Reg, *, avoid: tuple[Reg, ...] = ()) -> tuple[Reg, int]:
    if not isinstance(addr, int):
      return addr, 0
    known = self._reg_const(tmp_addr)
    if known is not None:
      delta = addr - known
      if -2048 <= delta <= 2047:
        return tmp_addr, delta
    avoid_regs = {int(reg) for reg in avoid}
    for reg_idx, known in self._reg_consts.items():
      if reg_idx in avoid_regs:
        continue
      delta = addr - known
      if -2048 <= delta <= 2047:
        return Reg(reg_idx), delta
    self.li(tmp_addr, addr)
    return tmp_addr, 0

  def _value_reg(self, value: int | Reg, tmp_val: Reg) -> Reg:
    if not isinstance(value, int):
      return value
    if value == 0:
      return zero
    value &= 0xFFFFFFFF
    if self._reg_const(tmp_val) == value:
      return tmp_val
    for reg_idx, known in self._reg_consts.items():
      if known == value:
        return Reg(reg_idx)
    self.li(tmp_val, value)
    return tmp_val

  def write32(self, addr: int | Reg, value: int | Reg, *, tmp_addr: Reg = t0, tmp_val: Reg = t1):
    avoid = (tmp_val,) if isinstance(value, int) else ()
    addr, offset = self._addr_reg_offset(addr, tmp_addr, avoid=avoid)
    value = self._value_reg(value, tmp_val)
    return self.sw(value, addr, offset)

  def read32(self, dst: Reg, addr: int | Reg, *, tmp_addr: Reg = t0):
    addr, offset = self._addr_reg_offset(addr, tmp_addr)
    return self.lw(dst, addr, offset)

  def write8(self, addr: int | Reg, value: int | Reg, *, tmp_addr: Reg = t0, tmp_val: Reg = t1):
    avoid = (tmp_val,) if isinstance(value, int) else ()
    addr, offset = self._addr_reg_offset(addr, tmp_addr, avoid=avoid)
    value = self._value_reg(value, tmp_val)
    return self.sb(value, addr, offset)

  def read8(self, dst: Reg, addr: int | Reg, *, tmp_addr: Reg = t0):
    addr, offset = self._addr_reg_offset(addr, tmp_addr)
    return self.lbu(dst, addr, offset)

  def read16(self, dst: Reg, addr: int | Reg, *, tmp_addr: Reg = t0):
    addr, offset = self._addr_reg_offset(addr, tmp_addr)
    return self.lhu(dst, addr, offset)

  def zero_words(self, addr: int, words: int, *, ptr: Reg = t0, count: Reg = t1):
    self.li(ptr, addr)
    self.li(count, words)
    with self.loop():
      self.break_(cond(count, "==", zero))
      self.sw(zero, ptr, 0)
      self.addi(ptr, ptr, 4)
      self.addi(count, count, -1)
    return self

  def zero_word_range(self, start: int, end: int, *, ptr: Reg = t0, limit: Reg = t1):
    self.li(ptr, start)
    self.li(limit, end)
    loop = self._new_label("zero_words")
    done = self._new_label("zero_words_done")
    self.label(loop)
    self.bgeu(ptr, limit, done)
    self.sw(zero, ptr, 0)
    self.addi(ptr, ptr, 4)
    self.j(loop)
    self.label(done)
    return self

  def copy_words(self, dst: int | Reg, src: int | Reg, byte_count: int | Reg, *,
                 dst_reg: Reg = t0, src_reg: Reg = t1, value: Reg = t2,
                 count: Reg = t3, word: Reg | None = None):
    if word is not None:
      value = word
    if isinstance(dst, int):
      self.li(dst_reg, dst)
      dst = dst_reg
    if isinstance(src, int):
      self.li(src_reg, src)
      src = src_reg
    if isinstance(byte_count, int):
      self.li(count, byte_count // 4)
      byte_count = count
    else:
      self.srli(byte_count, byte_count, 2)
    loop = self._new_label("copy_words")
    done = self._new_label("copy_done")
    self.label(loop)
    self.beq(byte_count, zero, done)
    self.lw(value, src, 0)
    self.sw(value, dst, 0)
    self.addi(src, src, 4)
    self.addi(dst, dst, 4)
    self.addi(byte_count, byte_count, -1)
    self.j(loop)
    self.label(done)
    return self

  def delay_cycles(self, cycles: int, *, count: Reg = t0):
    self.li(count, cycles)
    with self.loop():
      self.break_(cond(count, "==", zero))
      self.addi(count, count, -1)
    return self

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

  def _relaxed_layout(self) -> tuple[list, dict[int, int]]:
    long_branches: set[int] = set()
    label_index = {name: (pc - self.base) // 4 for name, pc in self.labels.items()}

    while True:
      expanded_before = [0] * (len(self.items) + 1)
      extra = 0
      for idx, item in enumerate(self.items):
        expanded_before[idx] = extra
        if idx in long_branches:
          extra += 1
      expanded_before[len(self.items)] = extra

      def pc_for_index(idx: int) -> int:
        return self.base + 4 * (idx + expanded_before[idx])

      label_pc = {name: pc_for_index(idx) for name, idx in label_index.items()}
      changed = False
      for idx, item in enumerate(self.items):
        if not isinstance(item, Fixup) or item.op not in _BRANCH_OPS or idx in long_branches:
          continue
        if item.label not in label_pc:
          raise ValueError(f"undefined label {item.label!r}")
        imm = label_pc[item.label] - pc_for_index(idx)
        if imm & 1:
          raise ValueError(f"branch target {item.label!r} is misaligned: {imm}")
        if not -(1 << 12) <= imm < (1 << 12):
          long_branches.add(idx)
          changed = True
      if not changed:
        return [idx in long_branches for idx in range(len(self.items))], label_pc

  def instructions(self) -> list:
    long_branch, label_pc = self._relaxed_layout()
    out = []
    pc = self.base
    for idx, item in enumerate(self.items):
      if not isinstance(item, Fixup):
        out.append(item)
        pc += 4
        continue
      if item.label not in label_pc:
        raise ValueError(f"undefined label {item.label!r}")
      imm = label_pc[item.label] - pc
      if item.op == "jal":
        if imm & 1 or not -(1 << 20) <= imm < (1 << 20):
          raise ValueError(f"jal target {item.label!r} out of range: {imm}")
        out.append(dsl.jal(*item.operands, imm))
        pc += 4
        continue
      if item.op in _BRANCH_OPS and long_branch[idx]:
        inv = _INVERT_BRANCH[item.op]
        out.append(getattr(dsl, inv)(*item.operands, 8))
        jal_imm = label_pc[item.label] - (pc + 4)
        if jal_imm & 1 or not -(1 << 20) <= jal_imm < (1 << 20):
          raise ValueError(f"relaxed branch jal target {item.label!r} out of range: {jal_imm}")
        out.append(dsl.jal(zero, jal_imm))
        pc += 8
        continue
      if item.op in _BRANCH_OPS:
        if imm & 1 or not -(1 << 12) <= imm < (1 << 12):
          raise ValueError(f"branch target {item.label!r} out of range: {imm}")
        out.append(getattr(dsl, item.op)(*item.operands, imm))
        pc += 4
        continue
      out.append(self._resolve(item))
      pc += 4
    return out

  def to_bytes(self) -> bytes:
    words = []
    for inst in self.instructions():
      words.append(inst.to_word() if hasattr(inst, "to_word") else int(inst))
    return b"".join((w & 0xFFFFFFFF).to_bytes(4, "little") for w in words)

class KernelBase(Asm):
  """Asm core plus the Program-facing surface (run-time args, extra load
  segments, compilation). Deliberately carries NO role mixins, so role-specific
  kernel classes can compose only the helpers they actually use."""

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

  def read_rta_from(self, rta_ptr_addr: int, regs):
    self.read32(t0, rta_ptr_addr)
    for i, reg in enumerate(regs):
      self.lw(reg, t0, i * 4)
    return self

  def ret_kernel(self):
    self.lw(ra, sp, 12)
    self.addi(sp, sp, 16)
    return self.ret()

  def wait_sync_value(self, addr: int, value_reg: Reg, *, ptr: Reg = t0, actual: Reg = t1):
    done = self._new_label("wait_sync_done")
    loop = self._new_label("wait_sync")
    self.li(ptr, addr)
    self.label(loop)
    self.lw(actual, ptr, 0)
    self.beq(actual, value_reg, done)
    self.fence()
    self.j(loop)
    self.label(done)
    return self.fence()

  def signal_sync(self, addr: int, value_reg: Reg):
    return self.write32(addr, value_reg, tmp_addr=t0, tmp_val=t1)

  def wait8(self, addr: int, value: int, *, ptr: Reg = t0, actual: Reg = t1, expected: Reg = t2):
    self.li(ptr, addr)
    self.li(expected, value)
    start = self._new_label("wait8")
    done = self._new_label("wait8_done")
    self.label(start)
    self.lbu(actual, ptr, 0)
    self.beq(actual, expected, done)
    self.fence()
    self.j(start)
    self.label(done)
    self.fence()
    return self

  def signal8(self, addr: int, value: int):
    return self.write8(addr, value)

  def setup_stack(self, stack_top: int):
    return self.li(sp, stack_top)

  def current_launch_ptr(self, launch: Reg = t0, tmp: Reg = t1):
    self.read32(tmp, _Mailbox.LAUNCH_MSG_RD_PTR, tmp_addr=launch)
    self.andi(tmp, tmp, 7)
    self.li(launch, _Launch.MSG_SIZE)
    self.mul(tmp, tmp, launch)
    self.li(launch, _Launch.BASE)
    return self.add(launch, launch, tmp)

  def configure_csr(self, *, value: Reg = t0):
    self.li(value, 2)
    self.csrrs(zero, value, 0x7C0)
    self.li(value, 1)
    self.slli(value, value, 18)
    self.fence()
    self.csrrs(zero, value, 0x7C0)
    self.li(value, 2)
    self.csrrc(zero, value, 0x7C0)
    self.fence()
    self.fence()
    self.li(value, 8)
    self.csrrs(zero, value, 0x7C0)
    return self

  def wait_go(self):
    return self.wait8(_Mailbox.GO_SIGNAL, _RunMsg.GO)

  def signal_done(self):
    return self.signal8(_Mailbox.GO_SIGNAL, _RunMsg.DONE)

  def signal_subordinate_go(self, role_index: int):
    return self.signal8(_Mailbox.SUBORDINATE_SYNC + role_index - 1, _RunMsg.GO)

  def signal_subordinate_done(self, role_index: int):
    return self.signal8(_Mailbox.SUBORDINATE_SYNC + role_index - 1, _RunMsg.DONE)

  def wait_subordinate_go(self, role_index: int):
    return self.wait8(_Mailbox.SUBORDINATE_SYNC + role_index - 1, _RunMsg.GO)

  def wait_subordinate_done(self, role_index: int):
    return self.wait8(_Mailbox.SUBORDINATE_SYNC + role_index - 1, _RunMsg.DONE)

  def launch_kernel_enabled(self, role_index: int, *, enabled: Reg = t0, mask: Reg = t1):
    self.current_launch_ptr(enabled)
    self.lw(enabled, enabled, _Launch.ENABLES)
    self.li(mask, 1 << role_index)
    return self.and_(enabled, enabled, mask)

  def run_launch_kernel(self, role_index: int, *, launch: Reg = t0, config_base: Reg = t1,
                        offset: Reg = t2, entry: Reg = t3, enabled: Reg = t4):
    skip = self._new_label("skip_kernel")
    self.launch_kernel_enabled(role_index, enabled=enabled, mask=offset)
    self.beq(enabled, zero, skip)
    self.current_launch_ptr(launch)
    self.lw(config_base, launch, _Launch.KERNEL_CONFIG_BASE)
    self.lw(offset, launch, _Launch.KERNEL_TEXT_OFFSET + 4 * role_index)
    self.add(entry, config_base, offset)
    self.jalr(ra, entry, 0)
    self.label(skip)
    return self


def Kernel(*mixins, **kwargs) -> KernelBase:
  """Compose ``KernelBase`` with the given role mixins and instantiate it, so a
  kernel can be built at its definition site without a dedicated empty subclass::

      fw = Kernel(Tensix, Noc, Cb, Debug, base_addr=...)

  ``kwargs`` are forwarded to ``KernelBase.__init__`` (e.g. ``base_addr``)."""
  return type("Kernel", (KernelBase, *mixins), {})(**kwargs)


# --- Scratch-GPR allocator ----------------------------------------------------
#
# Makes register clobbering impossible by construction. The old ttk pattern
# hardcodes physical temporaries::
#
#     iface, received, acked = t6, t5, t4
#
# so two snippets that get concatenated (or fused) can grab the same register
# and clobber a value the other still needs. On a GPU you can't do this; on
# RISC-V you silently corrupt state.
#
# Fix: helpers *request* scratch registers instead of naming them. You do NOT
# wrap every block in ``with`` — you declare scratch use **once per helper** and
# write a flat body::
#
#     @with_scope
#     def cb_reserve_back(self, ...):
#         iface, received, acked = self.tmp(3)    # reads like `= t6, t5, t4`
#         self.lw(received, iface, 24)
#         ...                                      # flat; regs freed on return
#
# Under the hood there is a scope stack. ``@with_scope`` (or ``with self.scope():``)
# pushes a scope; ``self.tmp(n)`` allocates into the current scope; the scope
# frees everything when it pops. Because scopes nest along the call stack, when a
# scoped helper calls another scoped helper the callee only ever sees the
# still-free registers — so composition cannot clobber, with no ``with`` at the
# call site.
#
# Reach for ``with self.scratch(n) as regs:`` ONLY when you want to release
# registers *early*, before the enclosing helper returns (the uncommon case).
#
# Allocation is deterministic (lowest-ranked free register first), so the same
# source always emits the same bytes.
class RegAlloc:
  """A pool of physical scratch GPRs handed out through a stack of scopes."""

  # caller-saved temporaries, in canonical allocation order
  DEFAULT = (t0, t1, t2, t3, t4, t5, t6)

  def __init__(self, pool=DEFAULT):
    self._rank = {int(r): i for i, r in enumerate(pool)}
    self._free = list(pool)
    self._scopes: list[list[Reg]] = []   # stack; each entry = regs to free on pop

  def reserve(self, *regs: Reg):
    """Remove regs from the allocatable pool (e.g. fixed calling-convention
    registers a kernel receives arguments in). Returns self for chaining."""
    self._free = [f for f in self._free if all(int(f) != int(r) for r in regs)]
    return self

  # --- scopes -------------------------------------------------------------
  def push(self):
    self._scopes.append([])

  def pop(self):
    self._give_back(self._scopes.pop())

  def scope(self):
    """`with self.scope():` — a manual scope boundary (what @with_scope adds)."""
    return _Scope(self)

  def tmp(self, n: int = 1):
    """Allocate n disjoint scratch regs into the current scope (freed when it
    pops). Returns a single Reg when n==1, else a tuple. Needs an open scope."""
    if not self._scopes:
      raise RuntimeError(
        "tmp() needs an open scope: decorate the method with @with_scope "
        "or wrap the body in `with self.scope():`")
    regs = self._take(n)
    self._scopes[-1].extend(regs)
    return regs[0] if n == 1 else tuple(regs)

  def scratch(self, n: int = 1):
    """`with self.scratch(n) as regs:` — a self-contained scope that allocates n
    up front and frees them on block exit. For releasing regs early."""
    return _Lease(self, n)

  # --- pool mechanics -----------------------------------------------------
  def _take(self, n: int) -> list[Reg]:
    if len(self._free) < n:
      live = [r for s in self._scopes for r in s]
      raise RuntimeError(
        f"out of scratch GPRs: need {n}, free={len(self._free)} "
        f"({[repr(r) for r in self._free]}), live={[repr(r) for r in live]}")
    regs, self._free = self._free[:n], self._free[n:]
    return regs

  def _give_back(self, regs: list[Reg]):
    self._free = sorted(self._free + regs, key=lambda r: self._rank[int(r)])


class _Scope:
  def __init__(self, alloc: RegAlloc): self._alloc = alloc
  def __enter__(self): self._alloc.push(); return self._alloc
  def __exit__(self, *exc): self._alloc.pop(); return False


class _Lease:
  def __init__(self, alloc: RegAlloc, n: int):
    self._alloc, self._n, self._regs = alloc, n, []
  def __enter__(self):
    self._alloc.push()
    self._regs = self._alloc._take(self._n)
    self._alloc._scopes[-1].extend(self._regs)
    return self._regs[0] if self._n == 1 else tuple(self._regs)
  def __exit__(self, *exc):
    self._alloc.pop(); self._regs = []; return False


def with_scope(fn):
  """Decorator: open a scratch scope for the whole method so its body can call
  ``self.tmp(...)`` flatly; every register is freed when the method returns."""
  @functools.wraps(fn)
  def wrap(self, *a, **k):
    self.regs.push()
    try:
      return fn(self, *a, **k)
    finally:
      self.regs.pop()
  return wrap
