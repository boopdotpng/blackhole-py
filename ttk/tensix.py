from __future__ import annotations

from dsl import Reg, t0, t1


class TensixRegs:
  INSTRN_BUF_BASE = 0xFFE40000
  REGFILE_BASE = 0xFFE00000
  PC_BUF_SYNC = 0xFFE80004
  CFG_BASE = 0xFFEF0000
  RISCV_IC_INVALIDATE_INVALIDATE_ALL = CFG_BASE + 185 * 4
  RISCV_IC_ALL_MASK = 0x1F
  PRNG_SEED_SEED_VAL_ADDR32 = 186


class TensixSem:
  MATH_PACK = 1
  UNPACK_TO_DEST = 2
  MATH_DONE = 7


class Tensix:
  def tensix_push_word(self, instrn_buf: int | Reg, word: int, *, tmp: Reg = t0, tmp_addr: Reg = t1):
    self.li(tmp, word)
    return self.write32(instrn_buf, tmp, tmp_addr=tmp_addr)

  def push_tensix_word(self, instrn_buf: int | Reg, word: int, *, tmp: Reg = t0, tmp_addr: Reg = t1):
    return self.tensix_push_word(instrn_buf, word, tmp=tmp, tmp_addr=tmp_addr)

  def tensix_set_cfg_reg(self, cfg_base: int, offset_words: int, value: int):
    return self.write32(cfg_base + offset_words * 4, value)

  def set_cfg_reg(self, cfg_base: int, offset_words: int, value: int):
    return self.tensix_set_cfg_reg(cfg_base, offset_words, value)

  def tensix_reset_cfg_state_id(self, addr: int):
    return self.write32(addr, 0)

  def reset_cfg_state_id(self, addr: int):
    return self.tensix_reset_cfg_state_id(addr)
