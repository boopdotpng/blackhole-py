from __future__ import annotations

from dsl import Reg, t0, t1, t2, zero


class RiscvMemoryMixin:
  def write32(self, addr: int | Reg, value: int | Reg, *, tmp_addr: Reg = t0, tmp_val: Reg = t1):
    if isinstance(addr, int):
      self.li(tmp_addr, addr)
      addr = tmp_addr
    if isinstance(value, int):
      self.li(tmp_val, value)
      value = tmp_val
    return self.sw(value, addr, 0)

  def read32(self, rd: Reg, addr: int | Reg, *, tmp_addr: Reg = t0):
    if isinstance(addr, int):
      self.li(tmp_addr, addr)
      addr = tmp_addr
    return self.lw(rd, addr, 0)

  def write8(self, addr: int | Reg, value: int | Reg, *, tmp_addr: Reg = t0, tmp_val: Reg = t1):
    if isinstance(addr, int):
      self.li(tmp_addr, addr)
      addr = tmp_addr
    if isinstance(value, int):
      self.li(tmp_val, value)
      value = tmp_val
    return self.sb(value, addr, 0)

  def zero_words(self, addr: int, words: int, *, ptr: Reg = t0, count: Reg = t1):
    self.li(ptr, addr)
    self.li(count, words)
    with self.loop():
      self.break_(count_is_zero(count))
      self.sw(zero, ptr, 0)
      self.addi(ptr, ptr, 4)
      self.addi(count, count, -1)
    return self

  def delay_cycles(self, cycles: int, *, count: Reg = t0):
    self.li(count, cycles)
    with self.loop():
      self.break_(count_is_zero(count))
      self.addi(count, count, -1)
    return self


def count_is_zero(reg: Reg):
  from asm import cond

  return cond(reg, "==", zero)
