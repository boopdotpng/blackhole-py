from dataclasses import dataclass, field
from enum import IntEnum
from isa import R, tt_word
from ttk.mop import (
  Mop, MopState, Replay,
)

CFG_BASE = 0xFFEF0000

class Cfg(IntEnum):
  ALU_FORMAT_SPEC_REG = CFG_BASE; ALU = CFG_BASE + 4; ALU_ACC_CTRL = CFG_BASE + 8; ECC_SCRUBBER = CFG_BASE + 0xC
  STATE_RESET_EN = CFG_BASE + 0x10; DEST_OFFSET = CFG_BASE + 0x14; DEST_REGW_BASE = CFG_BASE + 0x18; DEST_SP_BASE = CFG_BASE + 0x1C
  PCK0_ADDR_CTRL_XY_REG_0 = CFG_BASE + 0x30; PCK0_ADDR_CTRL_ZW_REG_0 = CFG_BASE + 0x34; PCK_DEST_RD_CTRL = CFG_BASE + 0x48
  TILE_ROW_SET_MAPPING_0 = CFG_BASE + 0x50; TILE_ROW_SET_MAPPING_1 = CFG_BASE + 0x54
  PCK_EDGE = CFG_BASE + 0x60; PCK_EDGE_SEC1 = CFG_BASE + 0x64
  PACK_COUNTERS_SEC0 = CFG_BASE + 0x70; PACK_COUNTERS_SEC1 = CFG_BASE + 0x74; PACK_COUNTERS_SEC2 = CFG_BASE + 0x78; PACK_COUNTERS_SEC3 = CFG_BASE + 0x7C
  UNP0_ADDR_CTRL_XY_REG_0 = CFG_BASE + 0xB0; UNP0_ADDR_CTRL_ZW_REG_0 = CFG_BASE + 0xB4
  UNP1_ADDR_CTRL_XY_REG_0 = CFG_BASE + 0xB8; UNP1_ADDR_CTRL_ZW_REG_0 = CFG_BASE + 0xBC; UNP0 = CFG_BASE + 0xC8
  UNP0_ADDR_CTRL_XY_REG_1 = CFG_BASE + 0xE0; UNP0_ADDR_CTRL_ZW_REG_1 = CFG_BASE + 0xE4
  UNP1_ADDR_CTRL_XY_REG_1 = CFG_BASE + 0xE8; UNP1_ADDR_CTRL_ZW_REG_1 = CFG_BASE + 0xEC
  THCON_SEC0_REG0_TileDescriptor = CFG_BASE + 0x100; THCON_SEC0_REG0_TileDescriptor_1 = CFG_BASE + 0x104
  THCON_SEC0_REG1 = CFG_BASE + 0x110; THCON_SEC0_REG1_L1_Dest_addr = CFG_BASE + 0x114; THCON_SEC0_REG1_1 = CFG_BASE + 0x118; THCON_SEC0_REG1_2 = CFG_BASE + 0x11C
  THCON_SEC0_REG2 = CFG_BASE + 0x120; THCON_SEC0_REG2_1 = CFG_BASE + 0x124
  THCON_SEC0_REG3_Base_address = CFG_BASE + 0x130; THCON_SEC0_REG3_Base_cntx1_address = CFG_BASE + 0x134
  THCON_SEC0_REG5_Dest_cntx01 = CFG_BASE + 0x150; THCON_SEC0_REG5_Dest_cntx23 = CFG_BASE + 0x154
  THCON_SEC0_REG5_Tile_x_dim_cntx01 = CFG_BASE + 0x158; THCON_SEC0_REG5_Tile_x_dim_cntx23 = CFG_BASE + 0x15C
  THCON_SEC0_REG7_Offset_address = CFG_BASE + 0x170; THCON_SEC0_REG7_Offset_cntx1_address = CFG_BASE + 0x174
  THCON_SEC1_REG0_TileDescriptor = CFG_BASE + 0x1C0; THCON_SEC1_REG0_TileDescriptor_1 = CFG_BASE + 0x1C4
  THCON_SEC1_REG2 = CFG_BASE + 0x1E0; THCON_SEC1_REG2_1 = CFG_BASE + 0x1E4
  THCON_SEC1_REG3_Base_address = CFG_BASE + 0x1F0; THCON_SEC1_REG3_Base_cntx1_address = CFG_BASE + 0x1F4
  THCON_SEC1_REG7_Offset_address = CFG_BASE + 0x230; THCON_SEC1_REG7_Offset_cntx1_address = CFG_BASE + 0x234
  DEST_TARGET_REG_CFG_PACK_SEC0 = CFG_BASE + 0x2D0; DEST_TARGET_REG_CFG_PACK_SEC1 = CFG_BASE + 0x2D4
  DEST_TARGET_REG_CFG_PACK_SEC2 = CFG_BASE + 0x2D8; DEST_TARGET_REG_CFG_PACK_SEC3 = CFG_BASE + 0x2DC; PRNG_SEED = CFG_BASE + 0x2E8
  DEST_ACCESS_CFG = CFG_BASE + 0x370; SRC_ACCESS_CFG = CFG_BASE + 0x374; CHICKEN_BITS = CFG_BASE + 0x378

  @property
  def addr32(self):
    return (int(self) - CFG_BASE) >> 2

class ThreadCfg(IntEnum):
  CFG_STATE_ID, DEST_TARGET_REG_CFG_MATH, DISABLE_IMPLIED_SRCA_FMT, DISABLE_IMPLIED_SRCB_FMT = range(4)
  SFPU_DEST_FMT, SRCA_SET, SRCB_SET, CLR_DVALID = range(4, 8)
  SCBD_BANK_MASK_32B, PACK_SCBD_BANK_MASK_32B, UNPACK_SCBD_BANK_MASK_32B, FIDELITY_BASE = range(8, 12)
  ADDR_MOD_AB_SEC0, ADDR_MOD_AB_SEC1, ADDR_MOD_AB_SEC2, ADDR_MOD_AB_SEC3, ADDR_MOD_AB_SEC4, ADDR_MOD_AB_SEC5, ADDR_MOD_AB_SEC6, ADDR_MOD_AB_SEC7 = range(12, 20)
  ADDR_MOD_AB2_SEC0, ADDR_MOD_AB2_SEC1, ADDR_MOD_AB2_SEC2, ADDR_MOD_AB2_SEC3, ADDR_MOD_AB2_SEC4, ADDR_MOD_AB2_SEC5, ADDR_MOD_AB2_SEC6, ADDR_MOD_AB2_SEC7 = range(20, 28)
  ADDR_MOD_DST_SEC0, ADDR_MOD_DST_SEC1, ADDR_MOD_DST_SEC2, ADDR_MOD_DST_SEC3, ADDR_MOD_DST_SEC4, ADDR_MOD_DST_SEC5, ADDR_MOD_DST_SEC6, ADDR_MOD_DST_SEC7 = range(28, 36)
  SFPU_STACK, ADDR_MOD_PACK_SEC0, ADDR_MOD_PACK_SEC1, ADDR_MOD_PACK_SEC2, ADDR_MOD_PACK_SEC3, UNPACK_MISC_CFG = range(36, 42)
  ADDR_MOD_BIAS_SEC0, ADDR_MOD_BIAS_SEC1, ADDR_MOD_BIAS_SEC2, ADDR_MOD_BIAS_SEC3, ADDR_MOD_BIAS_SEC4, ADDR_MOD_BIAS_SEC5, ADDR_MOD_BIAS_SEC6, ADDR_MOD_BIAS_SEC7 = range(47, 55)

class TensixStall(IntEnum):
  TDMA, SYNC, PACK, UNPACK, XMOV, THCON, MATH, CFG, SFPU = (1 << x for x in range(9))
  THREAD = 0x1FF

class TensixWait(IntEnum):
  THCON, UNPACK0, UNPACK1, PACK0, MATH, SRCA_CLR, SRCB_CLR, SRCA_VLD, SRCB_VLD, XMOV, TRISC_CFG, SFPU, CFGEXU = (1 << x for x in range(13))

class TensixSemWait(IntEnum):
  STALL_ON_ZERO, STALL_ON_MAX = 1, 2

class TensixRegs:
  INSTRN_BUF_BASE = 0xFFE40000; REGFILE_BASE = 0xFFE00000; MOP_CFG = 0xFFB80000
  PC_BUF_SYNC = 0xFFE80004; PC_BUF_MOP_SYNC = 0xFFE80008; PC_UNPACK_SYNC = 0xFFE80034
  CFG_BASE = CFG_BASE; PRNG_SEED_SEED_VAL = CFG_BASE + 186 * 4; RISCV_IC_INVALIDATE = CFG_BASE + 185 * 4
  RISCV_IC_ALL_MASK = 0x1F; CFG_RESET_WORDS = 256
  ECC_SCRUBBER_ENABLE_MASK = 1; ECC_SCRUBBER_SCRUB_ON_ERROR_MASK = 2; ECC_SCRUBBER_DELAY_MASK = 0x3FF8; ECC_SCRUBBER_DELAY_SHAMT = 3

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

  def cfg(self, pipe: int, register: Cfg):
    return self.contexts[self.selected_context[pipe]].get(int(register), 0)

  def set_cfg(self, pipe: int, register: Cfg, value: int):
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

class Tensix:
  def __init__(self, kernel, pipe: int, state: TensixState | None = None):
    self.k, self.pipe = kernel, pipe
    self.state = state if state is not None else TensixState()
    self.mop = Mop(self)

  def issue(self, word):
    self.k._emit(word)
    return self

  @staticmethod
  def init(kernel):
    kernel.zero_words(TensixRegs.REGFILE_BASE, 64)
    return kernel

  @staticmethod
  def reset_hardware(kernel):
    kernel.zero_words(CFG_BASE, TensixRegs.CFG_RESET_WORDS)
    push = kernel.push_tensix_word
    word = kernel.tensix_word
    push(word("TTZEROACC", 3, 0, 0, 0, 0))
    push(word("TTSFPENCC", 3, 0, 0, 10))
    push(word("TTNOP"))
    push(word("TTSFPLOADI", 0, 0, 0xBF80))
    push(word("TTSFPCONFIG", 0, 11, 0))

    kernel.write32(Cfg.ECC_SCRUBBER, (
      TensixRegs.ECC_SCRUBBER_ENABLE_MASK |
      TensixRegs.ECC_SCRUBBER_SCRUB_ON_ERROR_MASK |
      (0x100 << TensixRegs.ECC_SCRUBBER_DELAY_SHAMT)
    ))
    for sem in (TensixSem.MATH_PACK, TensixSem.UNPACK_TO_DEST, TensixSem.MATH_DONE):
      push(word("TTSEMINIT", 1, 0, 1 << sem))
    return kernel

  def write_cfg(self, register: Cfg, value: int):
    if self.state.set_cfg(self.pipe, register, value):
      self.k.write32(int(register), value)
    return self

  def rmw_cfg_byte(self, register: Cfg, byte: int, mask: int, data: int):
    if not isinstance(register, Cfg):
      raise TypeError("CFG RMW register must be a Cfg value")
    if type(byte) is not int or not 0 <= byte < 4:
      raise ValueError("CFG byte index must be in range 0..3")
    if any(type(value) is not int or not 0 <= value < 256 for value in (mask, data)):
      raise ValueError("CFG RMW mask and data must fit in one byte")
    data &= mask
    shift = byte * 8
    current = self.state.cfg(self.pipe, register)
    updated = (current & ~(mask << shift)) | data << shift
    if updated != current:
      self.issue(tt_word(f"TTRMWCIB{byte}", mask, data, register.addr32))
      self.state.set_cfg(self.pipe, register, updated)
    return self

  def set_thread_cfg(self, register: int | IntEnum, value: int):
    value = int(value)
    if int(register) == int(ThreadCfg.CFG_STATE_ID):
      self.state.set_context(self.pipe, value & 1)
    if self.state.set_thread_cfg(self.pipe, int(register), value):
      self.issue(self.k.tensix_word("TTSETC16", int(register), value))
    return self

  def configure_mop(self, template):
    self.mop.configure(template)
    return self

  def load_replay(self, words, start=0):
    self.mop.load(Replay(start, words))
    return self

  def run_mop(self, *, loop_count: int = 0, zmask: int = 0, mop_type: int = 1):
    self.issue(self.k.tensix_word("TTMOP", mop_type, loop_count, zmask))
    return self

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

  def wait_unpack_config_idle(self):
    with self.k.scope():
      pointer, value = self.k.reg(2)
      self.k.li(pointer, TensixRegs.PC_UNPACK_SYNC)
      again = self.k._new_label("unpack_cfg_idle")
      done = self.k._new_label("unpack_cfg_ready")
      self.k.label(again)
      self.k.lw(value, pointer, 0)
      self.k.andi(value, value, 0xFE)
      self.k.beq(value, R.ZERO, done)
      self.k.fence()
      self.k.j(again)
      self.k.label(done)
    return self

  def commit_unpack_config(self, register: Cfg):
    with self.k.scope():
      observed = self.k.reg()
      self.k.read32(observed, int(register))
      self.k.write32(TensixRegs.PC_UNPACK_SYNC, 0)
    return self

  def stall(self, resources: int, wait_for: int):
    self.issue(self.k.tensix_word("TTSTALLWAIT", int(resources), int(wait_for)))
    return self

  def set_dma_reg16(self, half_register: int, value: int):
    self.issue(self.k.tensix_word("TTSETDMAREG", value >> 14, value & 0x3FFF, 0, half_register))
    return self

  def set_dma_reg16_from_reg(self, half_register: int, value: R):
    with self.k.scope():
      instruction, mask, base = self.k.reg(3, exclude=value)
      self.k.slli(instruction, value, 8)
      self.k.li(mask, 0x00FFFF00); self.k.and_(instruction, instruction, mask)
      self.k.li(base, self.k.tensix_word("TTSETDMAREG", 0, 0, 0, half_register))
      self.k.or_(instruction, instruction, base)
      self.k.write32(TensixRegs.INSTRN_BUF_BASE, instruction)
    return self

  def write_cfg_from_gpr(self, gpr_word: int, register: Cfg, *, wide=False):
    self.issue(self.k.tensix_word("TTWRCFG", gpr_word, int(bool(wide)), register.addr32))
    return self

  def dma_nop(self):
    self.issue(self.k.tensix_word("TTDMANOP"))
    return self

  def semaphore_wait(self, semaphore: int, condition: TensixSemWait, *, stall: int):
    self.issue(self.k.tensix_word(
      "TTSEMWAIT", int(stall), TensixSem.mask(semaphore), int(condition),
    ))
    return self

  def semaphore_post(self, semaphore: int):
    self.issue(self.k.tensix_word("TTSEMPOST", TensixSem.mask(semaphore)))
    return self

  def semaphore_get(self, semaphore: int):
    self.issue(self.k.tensix_word("TTSEMGET", TensixSem.mask(semaphore)))
    return self
