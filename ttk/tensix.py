from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from dsl import Reg, TTSETC16, TTSETRWC, t0, t1, zero
from ttk._cfg_regs import Cfg, ThreadCfg  # noqa: F401  (re-exported)


class TensixRegs:
  INSTRN_BUF_BASE = 0xFFE40000
  REGFILE_BASE = 0xFFE00000
  PC_BUF_SYNC = 0xFFE80004
  PC_BUF_MOP_SYNC = 0xFFE80008
  PC_BUF_SEM_BASE = 0xFFE80020
  PC_BUF_SEM_STRIDE = 4
  PC_BUF_SEM_COUNT = 8
  PC_UNPACK_SYNC = 0xFFE80034
  MOP_CFG = 0xFFB80000
  CFG_BASE = 0xFFEF0000
  RISCV_IC_INVALIDATE_INVALIDATE_ALL = CFG_BASE + 185 * 4
  RISCV_IC_ALL_MASK = 0x1F
  PRNG_SEED_SEED_VAL_ADDR32 = 186
  ECC_SCRUBBER_ADDR32 = 3
  ECC_SCRUBBER_ENABLE_MASK = 0x1
  ECC_SCRUBBER_SCRUB_ON_ERROR_MASK = 0x2
  ECC_SCRUBBER_DELAY_MASK = 0x3FF8
  ECC_SCRUBBER_DELAY_SHAMT = 3

  @staticmethod
  def pc_buf_sem(sem: int) -> int:
    if not 0 <= sem < TensixRegs.PC_BUF_SEM_COUNT:
      raise ValueError(f"Tensix semaphore index out of range: {sem}")
    return TensixRegs.PC_BUF_SEM_BASE + sem * TensixRegs.PC_BUF_SEM_STRIDE


class TensixSem:
  FPU_SFPU = 0
  MATH_PACK = 1
  UNPACK_TO_DEST = 2
  UNPACK_OPERAND_SYNC = 3
  PACK_DONE = 4
  UNPACK_SYNC = 5
  UNPACK_MATH_DONE = 6
  MATH_DONE = 7

  @staticmethod
  def mask(sem: int) -> int:
    return 1 << sem


class TensixStall:
  TDMA = 0x001
  SYNC = 0x002
  PACK = 0x004
  UNPACK = 0x008
  XMOV = 0x010
  THCON = 0x020
  MATH = 0x040
  CFG = 0x080
  SFPU = 0x100
  THREAD = 0x1FF


class TensixWait:
  THCON = 0x001
  UNPACK0 = 0x002
  UNPACK1 = 0x004
  PACK0 = 0x008
  MATH = 0x010
  SRCA_CLR = 0x020
  SRCB_CLR = 0x040
  SRCA_VLD = 0x080
  SRCB_VLD = 0x100
  XMOV = 0x200
  TRISC_CFG = 0x400
  SFPU = 0x800
  CFGEXU = 0x1000


class TensixSemWait:
  STALL_ON_ZERO = 0x1
  STALL_ON_MAX = 0x2


class TensixL1:
  SIZE = 0x180000
  LAUNCH = 0x70
  GO_MSG = 0x370
  GO_MSG_INDEX = 0x3A0
  KERNEL_CONFIG_BASE = 0x86B0
  BRISC_FIRMWARE_BASE = 0x3840
  MEM_ZEROS_BASE = 0x32E0
  MEM_ZEROS_SIZE = 512
  DATA_BUFFER_SPACE_BASE = 0x37000
  TIMING_CONTROL = 0x9C0

  FW_INIT_SCRATCH_BASE = 0x82B0
  BRISC_INIT_LOCAL_L1_BASE_SCRATCH = 0x82B0
  NCRISC_INIT_LOCAL_L1_BASE_SCRATCH = 0xA2B0
  TRISC0_INIT_LOCAL_L1_BASE_SCRATCH = 0xC2B0
  TRISC1_INIT_LOCAL_L1_BASE_SCRATCH = 0xD2B0
  TRISC2_INIT_LOCAL_L1_BASE_SCRATCH = 0xE2B0
  NCRISC_INIT_IRAM_L1_BASE_SCRATCH = 0xF2B0
  MEM_BANK_TO_NOC_SCRATCH = 0x112B0
  LOGICAL_TO_VIRTUAL_SCRATCH = 0x11AB0


class TensixMMIO:
  LOCAL_RAM_START = 0xFFB00000
  LOCAL_RAM_END = 0xFFB01FFF
  NCRISC_HALT_RESUME_ADDR = 0x60
  RISCV_DEBUG_REG_SOFT_RESET_0 = 0xFFB121B0
  RISCV_TDMA_REG_CLK_GATE_EN = 0xFFB11024
  RISCV_DEBUG_REG_WALL_CLOCK_L = 0xFFB121F0
  RISCV_DEBUG_REG_WALL_CLOCK_H = 0xFFB121F8
  RISCV_DEBUG_REG_TRISC0_RESET_PC = 0xFFB12228
  RISCV_DEBUG_REG_TRISC1_RESET_PC = 0xFFB1222C
  RISCV_DEBUG_REG_TRISC2_RESET_PC = 0xFFB12230
  RISCV_DEBUG_REG_TRISC_RESET_PC_OVERRIDE = 0xFFB12234
  RISCV_DEBUG_REG_NCRISC_RESET_PC = 0xFFB12238
  RISCV_DEBUG_REG_NCRISC_RESET_PC_OVERRIDE = 0xFFB1223C
  RISCV_DEBUG_REG_DEST_CG_CTRL = 0xFFB12240
  SOFT_RESET_ALL = 0x47800
  SOFT_RESET_BRISC_ONLY_RUN = 0x47000
  SOFT_RESET_NONE = 0


class Launch:
  BASE = 0x70
  MSG_SIZE = 96
  KERNEL_CONFIG_BASE = 0
  SEM_OFFSET = 12
  LOCAL_CB_OFFSET = 18
  REMOTE_CB_OFFSET = 20
  RTA_OFFSET = 22
  MODE = 42
  KERNEL_TEXT_OFFSET = 44
  LOCAL_CB_MASK = 64
  BRISC_NOC_ID = 68
  BRISC_NOC_MODE = 69
  NCRISC_MIN_REMOTE_CB_START_INDEX = 82
  TRISC_MIN_REMOTE_CB_START_INDEX = 70
  ENABLES = 76
  SUB_DEVICE_ORIGIN_X = 92
  SUB_DEVICE_ORIGIN_Y = 93
  PRELOAD = 95


class RunMsg:
  GO = 0x80
  RESET_READ_PTR = 0xC0
  RESET_READ_PTR_FROM_HOST = 0xE0
  REPLAY_TRACE = 0xF0
  DONE = 0x00


class RunSync:
  GO = 0x80
  LOAD = 0x01
  INIT = 0x40
  ALL_INIT = 0x40404040
  INIT_SYNC_REGISTERS = 0x03
  DONE = 0x00


class Mailbox:
  SUBORDINATE_SYNC = 0x68
  LAUNCH_MSG_RD_PTR = 0x6C
  CORE_INFO_ABSOLUTE_LOGICAL_X = 0x940
  CORE_INFO_ABSOLUTE_LOGICAL_Y = 0x941
  GO_SIGNAL = 0x373
  GO_MESSAGES = 0x370
  GO_MESSAGE_INDEX = 0x3A0


# Tensix regfile GPR maps. The regfile (ttsim "tensix_regfile", 0xFFE00000) is
# memory-mapped: each GPR is a 4-byte MMIO word, so these resolve to absolute
# addresses usable directly with write32(), exactly like Cfg.*. ttsim names the
# space but not the slots; slot names + word indices mirror the ckernel p_gpr_*
# maps (tt_llk_blackhole/common/inc/ckernel_gpr_map.h). The word index (address
# - REGFILE_BASE >> 2) is also the gpr_address operand of TTSETDMAREG/TTWRCFG/
# TTSTOREREG.
_RF = 0xFFE00000  # == TensixRegs.REGFILE_BASE


class GprUnpack(IntEnum):
  """Unpack-thread regfile GPRs (p_gpr_unpack), as absolute MMIO addresses."""

  OPERAND_BASE_ADDR = _RF + 4 * 4
  OPERAND_OFFSET_ADDR = _RF + 5 * 4
  ZERO_0 = _RF + 8 * 4
  ZERO_1 = _RF + 9 * 4
  ZERO_2 = _RF + 10 * 4
  ZERO_3 = _RF + 11 * 4
  TMP0 = _RF + 12 * 4
  TMP1 = _RF + 13 * 4
  TILE_SIZE = _RF + 14 * 4
  TILE_OFFSET = _RF + 15 * 4
  L1_BUFFER_ADDR = _RF + 17 * 4
  TMP_LO = _RF + 18 * 4
  TMP_HI = _RF + 19 * 4
  TILE_SIZE_A = _RF + 36 * 4
  TILE_SIZE_B = _RF + 37 * 4
  KT_DIM = _RF + 38 * 4
  FACE_DIM_16x16 = _RF + 40 * 4  # face 16x16 = 256, packed (256 | 256<<16)
  FACE_DIM_8x16 = _RF + 41 * 4   # 8x16 = 128
  FACE_DIM_4x16 = _RF + 42 * 4   # 4x16 = 64
  FACE_DIM_2x16 = _RF + 43 * 4   # 2x16 = 32
  FACE_DIM_1x16 = _RF + 44 * 4   # 1x16 = 16
  UNPACK_STRIDE = _RF + 52 * 4


class GprMath(IntEnum):
  """Math-thread regfile GPRs (p_gpr_math), as absolute MMIO addresses."""

  DEST_OP0_BASE = _RF + 48 * 4
  DEST_OP1_BASE = _RF + 49 * 4
  DEST_REGW_OFFSET = _RF + 50 * 4
  DEST_REGW_INCR = _RF + 51 * 4
  DEST_REGW_OFFSET2 = _RF + 52 * 4
  DEST_REGW_INCR2 = _RF + 53 * 4
  TMP0 = _RF + 60 * 4
  NUM_DRAM_REQS = _RF + 61 * 4


class GprPack(IntEnum):
  """Pack-thread regfile GPRs (p_gpr_pack), as absolute MMIO addresses."""

  DEST_OFFSET_LO = _RF + 4 * 4
  DEST_OFFSET_HI = _RF + 8 * 4
  OUTPUT_ADDR = _RF + 12 * 4
  TILE_HEADER = _RF + 16 * 4  # 4 words [16..19]: tile ID + tile size
  TILE_HEADER_1 = _RF + 17 * 4
  TILE_HEADER_2 = _RF + 18 * 4
  TILE_HEADER_3 = _RF + 19 * 4
  TEMP_TILE_OFFSET = _RF + 20 * 4
  NUM_MSGS_RECEIVED = _RF + 24 * 4
  ONE_MSG_RECEIVED = _RF + 25 * 4
  HEADER_ADDR = _RF + 26 * 4
  TMP0 = _RF + 28 * 4
  TMP1 = _RF + 29 * 4
  TMP_LO = _RF + 30 * 4
  TMP_HI = _RF + 31 * 4
  PACK_STREAM_SYNC = _RF + 32 * 4
  OUTPUT_ADDR_OFFSET = _RF + 50 * 4
  PERF_PACK_NUM_TILES = _RF + 51 * 4
  EXP0_SEC_SIZE_BFP = _RF + 52 * 4
  EXP1_SEC_SIZE_BFP8 = _RF + 53 * 4
  EXP2_SEC_SIZE_BFP8 = _RF + 54 * 4
  EXP3_SEC_SIZE_BFP8 = _RF + 55 * 4


@dataclass
class MopCfg:
  """Tensix MOP (macro-op) expander template.

  The MOP unit replays a fixed template of up to 7 Tensix instructions, driven
  by two loop counters. ``write_mop_cfg`` stores this into the ``MOP_CFG``
  register block; a later ``TTMOP`` issue triggers the expansion.

  Layout (9 x u32 at ``TensixRegs.MOP_CFG``)::

    [0]     loop_outer   outer loop count
    [1]     loop_inner   inner loop count
    [2..8]  template     7 Tensix instruction slots the expander replays

  ``template`` slots may be ``TTInst`` objects (preferred, self-documenting) or
  raw ``int`` words. Empty/short templates are padded with ``TTNOP``.
  """

  loop_outer: int
  loop_inner: int
  template: list

  TEMPLATE_SLOTS = 7
  NOP = 0x02000000  # TTNOP().raw_word()

  def words(self) -> list[int]:
    if len(self.template) > self.TEMPLATE_SLOTS:
      raise ValueError(f"MopCfg.template holds at most {self.TEMPLATE_SLOTS} slots, got {len(self.template)}")
    slots = [self.NOP if w is None else (w if isinstance(w, int) else w.raw_word()) for w in self.template]
    slots += [self.NOP] * (self.TEMPLATE_SLOTS - len(slots))
    return [self.loop_outer, self.loop_inner, *slots]


class Tensix:
  def tt_raw(self, inst) -> int:
    return inst.raw_word() if hasattr(inst, "raw_word") else int(inst) & 0xFFFFFFFF

  def push_tensix(self, word: int | object, *, tmp_addr: Reg = t0, tmp_val: Reg = t1):
    # Push a Tensix instruction to the instruction buffer at runtime via MMIO.
    # Takes a raw Tensix word; needed when the word is built at runtime. For a
    # word known at build time, prefer emit() which embeds it inline (rotated).
    return self.write32(TensixRegs.INSTRN_BUF_BASE, self.tt_raw(word), tmp_addr=tmp_addr, tmp_val=tmp_val)

  def setc16(self, reg: int, value: int):
    # Set a thread-cfg register (ThreadCfg.*). SETC16 is the ONLY way to write
    # this write-only, per-thread config space (no MMIO address, no read-back).
    # Build-time emit; for a runtime write use push_tensix(TTSETC16(reg, value)).
    return self.emit(TTSETC16(int(reg), value))

  def mop_sync(self, trisc_id: int = 0, *, tmp: Reg = t0):
    self.write32(TensixRegs.PC_BUF_MOP_SYNC, 0, tmp_addr=t0, tmp_val=t1)
    self.read32(tmp, TensixRegs.PC_BUF_MOP_SYNC, tmp_addr=t1)
    return self.and_(zero, zero, tmp)

  def write_mop_cfg(self, cfg: MopCfg | list[int] | tuple[int, ...], trisc_id: int = 0, *, ptr: Reg = t0, tmp: Reg = t1):
    words = cfg.words() if isinstance(cfg, MopCfg) else list(cfg)
    self.mop_sync(trisc_id, tmp=tmp)
    self.li(ptr, TensixRegs.MOP_CFG)
    for i, word in enumerate(words):
      self.li(tmp, word)
      self.sw(tmp, ptr, i * 4)
    return self

  def tensix_sync(self, trisc_id: int = 0, *, tmp: Reg = t0):
    self.write32(TensixRegs.PC_BUF_SYNC, 0, tmp_addr=t0, tmp_val=t1)
    self.read32(tmp, TensixRegs.PC_BUF_SYNC, tmp_addr=t1)
    return self.and_(zero, zero, tmp)

  def write_repeated_bytes(self, addr: int, value: int, count_words: int, *, ptr: Reg = t0, tmp: Reg = t1):
    byte = value & 0xFF
    self.li(ptr, addr)
    self.li(tmp, byte | (byte << 8) | (byte << 16) | (byte << 24))
    for i in range(count_words):
      self.sw(tmp, ptr, i * 4)
    return self

  def wait_mmio_low_byte_zero(self, addr: int, *, ptr: Reg = t0, tmp: Reg = t1):
    done = self._new_label("wait_mmio_zero_done")
    loop = self._new_label("wait_mmio_zero")
    self.li(ptr, addr)
    self.label(loop)
    self.lw(tmp, ptr, 0)
    self.andi(tmp, tmp, 0xFF)
    self.beq(tmp, zero, done)
    self.fence()
    self.j(loop)
    self.label(done)
    return self

  def math_direct_mova2d_init(self):
    self.setc16(ThreadCfg.ADDR_MOD_AB_SEC3_Src, 0)
    self.setc16(ThreadCfg.ADDR_MOD_DST_SEC3, 0)
    self.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC3_Bias, 0)
    self.setc16(ThreadCfg.ADDR_MOD_AB_SEC0_Src, 1)
    self.setc16(ThreadCfg.ADDR_MOD_DST_SEC0, 1)
    self.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC0_Bias, 0)
    self.setc16(ThreadCfg.ADDR_MOD_AB_SEC2_Src, 8)
    self.setc16(ThreadCfg.ADDR_MOD_DST_SEC2, 8)
    self.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC2_Bias, 0)
    self.setc16(ThreadCfg.CLR_DVALID_Src, 0)
    return self.emit(TTSETRWC(0, 0, 0, 0, 0, 15))

  def push_tensix_word(self, instrn_buf: int | Reg, word: int, *, tmp: Reg = t0, tmp_addr: Reg = t1):
    self.li(tmp, word)
    return self.write32(instrn_buf, tmp, tmp_addr=tmp_addr)
