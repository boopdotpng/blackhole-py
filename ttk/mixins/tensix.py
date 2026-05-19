from __future__ import annotations

from dsl import Reg, t0


class TensixMixin:
  def tensix_push_word(self, instrn_buf: int | Reg, word: int, *, tmp: Reg = t0):
    self.li(tmp, word)
    return self.write32(instrn_buf, tmp)

  def push_tensix_word(self, instrn_buf: int | Reg, word: int, *, tmp: Reg = t0):
    return self.tensix_push_word(instrn_buf, word, tmp=tmp)

  def tensix_set_cfg_reg(self, cfg_base: int, offset_words: int, value: int):
    return self.write32(cfg_base + offset_words * 4, value)

  def set_cfg_reg(self, cfg_base: int, offset_words: int, value: int):
    return self.tensix_set_cfg_reg(cfg_base, offset_words, value)

  def tensix_reset_cfg_state_id(self, addr: int):
    return self.write32(addr, 0)

  def reset_cfg_state_id(self, addr: int):
    return self.tensix_reset_cfg_state_id(addr)
