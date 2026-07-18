from isa import R, tt_word
from fw.consts import TensixL1

PARAM_BASE = TensixL1.PARAM_BASE

class Common:
  def risc_barrier(self, addr: int, participants: int, index: int, *, value: int = 1):
    """Join a small software barrier backed by one shared L1 word per RISC."""
    if participants <= 0 or not 0 <= index < participants:
      raise ValueError("barrier index must identify one participant")
    with self.scope():
      ptr, actual, expected = self.reg(3)
      self.write32(addr + index * 4, value); self.fence()
      for participant in range(participants):
        self.wait32(
          addr + participant * 4, value,
          ptr=ptr, actual=actual, expected=expected,
        )
    return self

  def configure_csr(self, *, value: R = R.T0):
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

  def call_fixed_kernel(self, entry: int, *, target: R = R.T0):
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

  def update32(self, addr: int, *, set_bits: int = 0, clear_bits: int = 0,
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
    from ttk.tensix import TensixRegs
    return self.write32(TensixRegs.RISCV_IC_INVALIDATE, TensixRegs.RISCV_IC_ALL_MASK)

  def signal_range(self, base: int, offsets, value: int):
    for offset in offsets:
      self.write8(base + offset, value)
    return self

  def align_up(self, value: R, alignment: int, *, scratch: R = R.T0):
    if type(alignment) is not int or alignment <= 0 or alignment & (alignment - 1):
      raise ValueError("alignment must be a positive power of two")
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

  def wait8(self, addr: int, value: int, *, ptr: R = R.T0,
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

  def wait32(self, addr: int, value: int, *, ptr: R = R.T0,
             actual: R = R.T1, expected: R = R.T2):
    self.li(ptr, addr)
    self.li(expected, value)
    loop = self._new_label("wait32")
    done = self._new_label("wait32_done")
    self.label(loop)
    self.lw(actual, ptr, 0)
    self.beq(actual, expected, done)
    self.fence()
    self.j(loop)
    self.label(done)
    return self.fence()

  def push_tensix_word(self, word: int, *, addr: int = 0xFFE40000):
    if self.role not in ("brisc", "trisc0", "trisc1", "trisc2"):
      raise RuntimeError(f"{self.role} cannot push Tensix instructions")
    if not isinstance(word, int):
      raise TypeError("Tensix instruction must be an int")
    if not 0 <= word <= 0xFFFFFFFF:
      raise ValueError("Tensix instruction must fit in 32 bits")
    return self.write32(addr, word)

  @staticmethod
  def tensix_word(opcode: str, *args, **kwargs) -> int:
    return tt_word(opcode, *args, **kwargs)

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
    self.load(reg, PARAM_BASE + self.param_slots[param] * 4)
    return reg

  def arg(self, index: int):
    """Load one per-core runtime argument from the Program argument table."""
    if type(index) is not int or index < 0:
      raise ValueError("runtime argument index must be a nonnegative integer")
    reg = self.reg()
    self.load(reg, PARAM_BASE + (len(self.param_slots) + index) * 4)
    return reg
