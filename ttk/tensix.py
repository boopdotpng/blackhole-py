from dataclasses import dataclass, field
from enum import IntEnum
from isa import R, Tensix as TT
from ttk.mop import Mop, MopState

CFG_BASE = 0xFFEF0000
_CFG_STATE_ID = 0
_ECC_SCRUBBER = CFG_BASE + 0xC
_ALU_CONFIG = CFG_BASE + 4

def cfg_addr32(register): return (int(register) - CFG_BASE) >> 2

def push_tensix_word(kernel, word: int, addr=0xFFE40000):
  if kernel.role not in ("brisc", "trisc0", "trisc1", "trisc2"):
    raise RuntimeError(f"{kernel.role} cannot push Tensix instructions")
  if not isinstance(word, int): raise TypeError("Tensix instruction must be an int")
  if not 0 <= word <= 0xFFFFFFFF: raise ValueError("Tensix instruction must fit in 32 bits")
  return kernel.write32(addr, word)

class TensixStall(IntEnum):
  TDMA, SYNC, PACK, UNPACK, XMOV, THCON, MATH, CFG, SFPU = (1 << x for x in range(9))
  THREAD = 0x1FF

class TensixWait(IntEnum):
  THCON, UNPACK0, UNPACK1, PACK0, MATH, SRCA_CLR, SRCB_CLR, SRCA_VLD, SRCB_VLD, XMOV, TRISC_CFG, SFPU, CFGEXU = (1 << x for x in range(13))

class TensixSemWait(IntEnum):
  STALL_ON_ZERO, STALL_ON_MAX = 1, 2

class TensixRegs:
  INSTRN_BUF_BASE = 0xFFE40000; REGFILE_BASE = 0xFFE00000
  PC_BUF_SYNC = 0xFFE80004; PC_BUF_MOP_SYNC = 0xFFE80008
  PRNG_SEED_SEED_VAL = CFG_BASE + 186 * 4; RISCV_IC_INVALIDATE = CFG_BASE + 185 * 4
  RISCV_IC_ALL_MASK = 0x1F; CFG_RESET_WORDS = 256
  ECC_SCRUBBER_ENABLE_MASK = 1; ECC_SCRUBBER_SCRUB_ON_ERROR_MASK = 2; ECC_SCRUBBER_DELAY_SHAMT = 3

class TensixSem:
  FPU_SFPU, MATH_PACK, UNPACK_TO_DEST, UNPACK_OPERAND_SYNC = range(4)
  PACK_DONE, UNPACK_SYNC, UNPACK_MATH_DONE, MATH_DONE = range(4, 8)

  @staticmethod
  def mask(index: int):
    if not 0 <= index < 8:
      raise ValueError(f"Tensix semaphore index out of range: {index}")
    return 1 << index

@dataclass
class TensixState:
  contexts: list[dict[int, int]] = field(default_factory=lambda: [{}, {}])
  selected_context: list[int] = field(default_factory=lambda: [0, 0, 0])
  thread_cfg: list[dict[int, int]] = field(default_factory=lambda: [{}, {}, {}])
  mop: list[MopState] = field(default_factory=lambda: [MopState(), MopState(), MopState()])
  sfpu_lane_config: int | None = None

  def set_context(self, pipe: int, context: int):
    self.selected_context[pipe] = context

  def cfg(self, pipe: int, register: int):
    return self.contexts[self.selected_context[pipe]].get(int(register), 0)

  def set_cfg(self, pipe: int, register: int, value: int):
    shadow = self.contexts[self.selected_context[pipe]]
    value &= 0xFFFFFFFF
    previous = shadow.get(int(register), 0)
    shadow[int(register)] = value
    return previous != value

  def set_thread_cfg(self, pipe: int, register: int, value: int):
    shadow = self.thread_cfg[pipe]
    value &= 0xFFFF

    previous = shadow.get(int(register))
    shadow[int(register)] = value
    return previous != value

class TensixPipe:
  def __init__(self, kernel, pipe: int, state: TensixState | None = None):
    self.k, self.pipe = kernel, pipe
    self.state = state if state is not None else TensixState()
    self.mop = Mop(self)

  def issue(self, word):
    self.k.emit(word)
    return self

  @staticmethod
  def init(kernel):
    kernel.zero_words(TensixRegs.REGFILE_BASE, 64)
    return kernel

  @staticmethod
  def reset_hardware(kernel):
    kernel.zero_words(CFG_BASE, TensixRegs.CFG_RESET_WORDS)
    push = lambda word: push_tensix_word(kernel, word)
    push(TT.TTZEROACC(3, 0, 0, 0, 0))
    push(TT.TTSFPENCC(3, 0, 0, 10))
    push(TT.TTNOP())
    push(TT.TTSFPLOADI(0, 0, 0xBF80))
    push(TT.TTSFPCONFIG(0, 11, 0))

    kernel.write32(_ECC_SCRUBBER, (
      TensixRegs.ECC_SCRUBBER_ENABLE_MASK |
      TensixRegs.ECC_SCRUBBER_SCRUB_ON_ERROR_MASK |
      (0x100 << TensixRegs.ECC_SCRUBBER_DELAY_SHAMT)
    ))
    for sem in (TensixSem.MATH_PACK, TensixSem.UNPACK_TO_DEST, TensixSem.MATH_DONE):
      push(TT.TTSEMINIT(1, 0, 1 << sem))
    return kernel

  def write_cfg(self, register: int, value: int):
    if self.state.set_cfg(self.pipe, register, value):
      self.k.write32(int(register), value)
    return self

  def rmw_cfg_byte(self, register: int, byte: int, mask: int, data: int):
    if type(byte) is not int or not 0 <= byte < 4:
      raise ValueError("CFG byte index must be in range 0..3")
    if any(type(value) is not int or not 0 <= value < 256 for value in (mask, data)):
      raise ValueError("CFG RMW mask and data must fit in one byte")
    data &= mask
    shift = byte * 8
    current = self.state.cfg(self.pipe, register)
    updated = (current & ~(mask << shift)) | data << shift
    if updated != current:
      self.issue((TT.TTRMWCIB0, TT.TTRMWCIB1, TT.TTRMWCIB2, TT.TTRMWCIB3)[byte](
        mask, data, cfg_addr32(register),
      ))
      self.state.set_cfg(self.pipe, register, updated)
    return self

  def set_thread_cfg(self, register: int | IntEnum, value: int):
    value = int(value)
    if self.state.set_thread_cfg(self.pipe, int(register), value):
      self.issue(TT.TTSETC16(int(register), value))
    return self

  def select_config(self, context=0):
    self.state.set_context(self.pipe, context & 1)
    return self.set_thread_cfg(_CFG_STATE_ID, context)

  def replay(self, start: int, length: int):
    self.mop._replay(start, length)
    return self

  def _sync(self, addr):
    with self.k.scope():
      pointer, value = self.k.reg(2); self.k.li(pointer, addr); self.k.sw(R.ZERO, pointer, 0); self.k.lw(value, pointer, 0)
      self.k.and_(R.ZERO, R.ZERO, value)
    return self

  def sync(self): return self._sync(TensixRegs.PC_BUF_SYNC)
  def mop_sync(self): return self._sync(TensixRegs.PC_BUF_MOP_SYNC)

  def stall(self, resources: int, wait_for: int):
    self.issue(TT.TTSTALLWAIT(int(resources), int(wait_for)))
    return self

  def semaphore_wait(self, semaphore: int, condition: TensixSemWait, stall: int):
    self.issue(TT.TTSEMWAIT(int(stall), TensixSem.mask(semaphore), int(condition)))
    return self

  def semaphore_post(self, semaphore: int):
    self.issue(TT.TTSEMPOST(TensixSem.mask(semaphore)))
    return self

  def semaphore_get(self, semaphore: int):
    self.issue(TT.TTSEMGET(TensixSem.mask(semaphore)))
    return self

# The ALU word is shared, but this bit controls only the FPU's Dst width.
def set_fpu_fp32_destination(fpu, enabled=True):
  fpu.stall(TensixStall.CFG, TensixWait.MATH)
  fpu.rmw_cfg_byte(_ALU_CONFIG, 3, 0x20, 0x20 if enabled else 0)
  return fpu
