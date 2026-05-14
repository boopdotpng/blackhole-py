from __future__ import annotations

from dsl import Reg, t0


class TensixSetupMixin:
  def push_tensix_word(self, instrn_buf: int | Reg, word: int, *, tmp: Reg = t0):
    self.li(tmp, word)
    return self.write32(instrn_buf, tmp)

  def set_cfg_reg(self, cfg_base: int, offset_words: int, value: int):
    return self.write32(cfg_base + offset_words * 4, value)

  def reset_cfg_state_id(self, addr: int):
    return self.write32(addr, 0)
