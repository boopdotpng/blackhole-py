import pytest

from asm import Asm
from isa import R, RV32, VReg


def test_regs_are_virtual_and_reused_when_dead():
  k = Asm.firmware("brisc")
  first, second = k.reg(2)
  assert isinstance(first, VReg) and not hasattr(k, "scope")
  k.li(first, 1); k.li(second, 2)
  allocation = k._allocate_registers()
  assert allocation[first] == allocation[second] == R.X4


def test_overlapping_regs_encode_after_allocation():
  k = Asm.firmware("brisc")
  first, second = k.reg(2)
  k.li(first, 1); k.li(second, 2); k.add(first, first, second)
  assert k.instructions() == [
    RV32().addi(R.X4, R.ZERO, 1),
    RV32().addi(R.X5, R.ZERO, 2),
    RV32().add(R.X4, R.X4, R.X5),
  ]


def test_loop_backedge_keeps_values_live():
  k = Asm.firmware("brisc")
  pointer, remaining, scratch = k.reg(3)
  k.li(pointer, 0x1000); k.li(remaining, 4)
  loop = k._new_label("loop"); k.label(loop)
  k.sw(R.ZERO, pointer); k.addi(pointer, pointer, 4)
  k.li(scratch, 99); k.addi(remaining, remaining, -1); k.bne(remaining, R.ZERO, loop)
  allocation = k._allocate_registers()
  assert allocation[pointer] != allocation[scratch]


def test_pressure_fails_at_lowering_not_reg_creation():
  k = Asm.firmware("brisc")
  regs = k.reg(29)
  for index, reg in enumerate(regs): k.li(reg, index)
  for index, reg in enumerate(regs): k.sw(reg, R.SP, index * 4)
  with pytest.raises(RuntimeError, match="register allocation failed"): k.lower()
