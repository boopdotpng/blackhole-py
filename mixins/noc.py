from __future__ import annotations

from dsl import Reg, t0, t1

NCRISC_RESET_PC = 0xFFB12238
TRISC0_RESET_PC = 0xFFB12228
TRISC1_RESET_PC = 0xFFB1222C
TRISC2_RESET_PC = 0xFFB12230
TRISC_RESET_PC_OVERRIDE = 0xFFB12234
NCRISC_RESET_PC_OVERRIDE = 0xFFB1223C
SOFT_RESET_0 = 0xFFB121B0
SOFT_RESET_NONE = 0


class NocMixin:
  def write_reg(self, addr: int | Reg, value: int | Reg, *, tmp_addr: Reg = t0, tmp_val: Reg = t1):
    return self.write32(addr, value, tmp_addr=tmp_addr, tmp_val=tmp_val)

  def read_reg(self, rd: Reg, addr: int | Reg, *, tmp_addr: Reg = t0):
    return self.read32(rd, addr, tmp_addr=tmp_addr)

  def noc_write_reg(self, addr: int | Reg, value: int | Reg, *, tmp_addr: Reg = t0, tmp_val: Reg = t1):
    return self.write_reg(addr, value, tmp_addr=tmp_addr, tmp_val=tmp_val)

  def noc_read_reg(self, rd: Reg, addr: int | Reg, *, tmp_addr: Reg = t0):
    return self.read_reg(rd, addr, tmp_addr=tmp_addr)

  def noc_set_active_instance(self, noc: int):
    self.active_noc = noc
    return self

  def set_subordinate_reset_pcs(self, *, ncrisc: int, trisc0: int, trisc1: int, trisc2: int):
    self.write_reg(NCRISC_RESET_PC, ncrisc)
    self.write_reg(TRISC0_RESET_PC, trisc0)
    self.write_reg(TRISC1_RESET_PC, trisc1)
    self.write_reg(TRISC2_RESET_PC, trisc2)
    self.write_reg(TRISC_RESET_PC_OVERRIDE, 0b111)
    self.write_reg(NCRISC_RESET_PC_OVERRIDE, 1)
    return self

  def deassert_all_riscs(self):
    return self.write_reg(SOFT_RESET_0, SOFT_RESET_NONE)
