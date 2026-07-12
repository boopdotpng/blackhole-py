from isa import R, Tensix as TensixISA
from fw.consts import TensixL1

PARAM_BASE = TensixL1.PARAM_BASE

class Common:
  """Memory and DRAM buffer parameter helpers shared by all kernel roles."""

  def configure_csr(self, *, value: R = R.T0):
    """Configure the Blackhole RISC-V control/status register for firmware."""
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
    """Set the resident firmware stack pointer."""
    if type(stack_top) is not int: raise TypeError("stack_top must be an integer")
    return self.li(R.SP, stack_top)

  def call_fixed_kernel(self, entry: int, *, target: R = R.T0):
    """Call a worker kernel uploaded at a fixed local-L1 address."""
    if type(entry) is not int or entry < 0:
      raise ValueError("kernel entry must be a non-negative integer")
    self.li(target, entry)
    return self.jalr(R.RA, target, 0)

  def delay_cycles(self, cycles: int):
    """Emit a small deterministic delay loop for firmware bring-up."""
    if type(cycles) is not int or cycles < 0: raise ValueError("cycles must be non-negative")
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
    """Emit a compact runtime loop that clears ``count`` MMIO/L1 words."""
    if type(addr) is not int or type(count) is not int:
      raise TypeError("zero_words requires Python integer arguments")
    if count < 0: raise ValueError("zero_words count cannot be negative")
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
    """Write one 32-bit word to an immediate or register MMIO address."""
    return self.store(addr, value, bytes=4)

  def update32(self, addr: int, *, set_bits: int = 0, clear_bits: int = 0,
               value: R = R.T0):
    """Read-modify-write an MMIO word while preserving unrelated fields."""
    if any(type(item) is not int for item in (addr, set_bits, clear_bits)):
      raise TypeError("update32 arguments must be Python integers")
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
    """Invalidate instruction caches for BRISC, NCRISC, and all TRISCs."""
    from ttk.tensix import TensixRegs
    return self.write32(TensixRegs.RISCV_IC_INVALIDATE, TensixRegs.RISCV_IC_ALL_MASK)

  def signal_range(self, base: int, offsets, value: int):
    """Write one fixed synchronization value to several byte offsets."""
    for offset in offsets:
      self.write8(base + offset, value)
    return self

  def align_up(self, value: R, alignment: int, *, scratch: R = R.T0):
    """Round an unsigned register value up to a power-of-two alignment."""
    if type(alignment) is not int or alignment <= 0 or alignment & (alignment - 1):
      raise ValueError("alignment must be a positive power of two")
    self.li(scratch, alignment - 1)
    self.add(value, value, scratch)
    self.li(scratch, -alignment)
    return self.and_(value, value, scratch)

  def read32(self, rd: R, addr: int | R):
    """Read one 32-bit word from an immediate or register MMIO address."""
    return self.load(rd, addr, bytes=4)

  def write8(self, addr: int | R, value: int | R):
    """Write one byte to an immediate or register MMIO address."""
    return self.store(addr, value, bytes=1)

  def signal8(self, addr: int | R, value: int):
    return self.write8(addr, value)

  def wait8(self, addr: int, value: int, *, ptr: R = R.T0,
            actual: R = R.T1, expected: R = R.T2):
    """Emit a fenced polling loop until an L1 byte equals ``value``."""
    if type(addr) is not int or not isinstance(value, int) or not 0 <= int(value) <= 0xFF:
      raise ValueError("wait8 address/value are invalid")
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
    """Emit a fenced polling loop until an L1 word equals ``value``."""
    if type(addr) is not int or type(value) is not int:
      raise TypeError("wait32 address/value must be integers")
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

  def push_tensix_word(self, word: int | object, *, addr: int = 0xFFE40000):
    """Append a Tensix instruction through the instruction-buffer MMIO port.

    ``word`` may be an integer or an instruction object exposing
    ``raw_word()``.  The instruction is deliberately written as data; callers
    must not invoke an instruction-builder method on the kernel itself because
    that would append the word directly to the RISC-V stream.
    """
    if hasattr(word, "raw_word"):
      word = word.raw_word()
    if type(word) is not int:
      raise TypeError("Tensix instruction must be an int or expose raw_word()")
    if not 0 <= word <= 0xFFFFFFFF:
      raise ValueError("Tensix instruction must fit in 32 bits")
    return self.write32(addr, word)

  @staticmethod
  def tensix_word(opcode: str, *args, **kwargs) -> int:
    """Build a raw Tensix word without appending it to a kernel.

    This is primarily for TTK implementation code.  Public kernel code should
    use named engine methods instead.
    """
    builder = TensixISA()
    method = getattr(builder, opcode)
    # isa.Tensix returns the rotated representation used when embedding a
    # Tensix instruction directly in the RISC-V stream.  MMIO instruction
    # buffer writes and MOP slots consume the architectural/raw word instead.
    encoded = method(*args, **kwargs)
    return ((encoded >> 2) | (encoded << 30)) & 0xFFFFFFFF

  def load(self, rd: R, addr: int | R, bytes=4):
    """Load 1, 2, or 4 bytes from an immediate or register address."""
    op = {1: self.lbu, 2: self.lhu, 4: self.lw}[bytes]
    if isinstance(addr, R): return op(rd, addr)
    with self.scope():
      base = self.reg(exclude=rd)
      self.li(base, addr)
      return op(rd, base)

  def store(self, addr: int | R, value: int | R, bytes=4):
    """Store 1, 2, or 4 bytes to an immediate or register address."""
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
    """Allocate a register and load a declared DRAM buffer parameter address."""
    if param not in self.param_slots: raise ValueError(f"undeclared parameter {getattr(param, 'name', param)!r}")
    reg = self.reg()
    self.load(reg, PARAM_BASE + self.param_slots[param] * 4)
    return reg
