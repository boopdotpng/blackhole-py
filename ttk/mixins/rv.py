from __future__ import annotations

from dsl import Reg, t0, t1, t2, t3, zero


class RvMixin:
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
    from asm import cond

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
    from asm import cond

    self.li(count, cycles)
    with self.loop():
      self.break_(cond(count, "==", zero))
      self.addi(count, count, -1)
    return self
