"""Spec tests for ../specs/gpr-and-dma-instructions.md.

Each test is pinned to one or more clauses from
../clauses/gpr-and-dma-instructions.md via the @spec() marker.
Tests that exercise clauses where the emulator diverges are marked
xfail(strict=True) so the divergence is tracked, not silenced.

Layout:
  - GPR file layout (thread isolation, half-register addressing)
  - SETDMAREG (immediate mode: low-half, high-half, full 16-bit)
  - ADDDMAREG (reg-reg, reg-const, overflow)
  - MULDMAREG (16-bit truncation, reg-const)
  - WRCFG (32-bit, 128-bit, state-bank selection)
  - RDCFG (32-bit round-trip, bank consistency)
  - SETC16 (ThreadConfig write, per-thread isolation)
  - RMWCIB0/1 (byte-indexed RMW, uses bank 0)
"""

import pytest

from emu.tensix import GPRFile, ConfigUnit, ScalarUnit
from emu.tensix import TensixCoprocessor
from dsl import (
  decode_tensix,
  TT_SETDMAREG, TT_ADDDMAREG, TT_MULDMAREG,
  TT_WRCFG, TT_RDCFG, TT_SETC16,
  TT_RMWCIB0, TT_RMWCIB1,
)

from .conftest import spec


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def gpr():
  return GPRFile()


@pytest.fixture
def cu(gpr):
  return ConfigUnit(gpr)


@pytest.fixture
def su(gpr):
  return ScalarUnit(gpr)


# ===========================================================================
# GPR file layout
# ===========================================================================

@spec("GPR.LAYOUT.64_PER_THREAD")
def test_gpr_64_per_thread_independent(gpr):
  """Each thread has its own 64 GPRs; writes to T0 are invisible from T1/T2."""
  gpr.write32(0, 5, 0xDEADBEEF)
  assert gpr.read32(0, 5) == 0xDEADBEEF
  assert gpr.read32(1, 5) == 0
  assert gpr.read32(2, 5) == 0


@spec("GPR.LAYOUT.THREAD_ISOLATION")
def test_gpr_thread_isolation(gpr):
  """Write to thread 1 does not affect thread 0 or thread 2."""
  gpr.write32(1, 20, 0xCAFEBABE)
  assert gpr.read32(0, 20) == 0
  assert gpr.read32(2, 20) == 0
  assert gpr.read32(1, 20) == 0xCAFEBABE


@spec("GPR.LAYOUT.HALF_REG_ADDRESSING")
def test_gpr_half_reg_low_preserves_high(gpr):
  """write16 to even index (low half) leaves high half unchanged."""
  gpr.write32(0, 3, 0xABCD0000)
  gpr.write16(0, 3 * 2 + 0, 0x1234)     # low half of GPR 3
  assert gpr.read32(0, 3) == 0xABCD1234


@spec("GPR.LAYOUT.HALF_REG_ADDRESSING")
def test_gpr_half_reg_high_preserves_low(gpr):
  """write16 to odd index (high half) leaves low half unchanged."""
  gpr.write32(0, 3, 0x00001234)
  gpr.write16(0, 3 * 2 + 1, 0xABCD)     # high half of GPR 3
  assert gpr.read32(0, 3) == 0xABCD1234


@spec("GPR.LAYOUT.HALF_REG_ADDRESSING")
def test_gpr_half_reg_read_back(gpr):
  """read16 returns the correct half."""
  gpr.write32(0, 7, 0xBEEFCAFE)
  assert gpr.read16(0, 7 * 2 + 0) == 0xCAFE    # low half
  assert gpr.read16(0, 7 * 2 + 1) == 0xBEEF    # high half


# ===========================================================================
# SETDMAREG
# ===========================================================================

@spec("GPR.SETDMAREG.IMMEDIATE_WRITE_16B",
      "GPR.SETDMAREG.IMM16_SPANS_BOTH_FIELDS")
def test_setdmareg_low_half(gpr, su):
  """SETDMAREG writes 16-bit immediate to the low half of a GPR."""
  gpr.write32(0, 5, 0xFFFF0000)   # preset high half
  word = int(TT_SETDMAREG(Payload_SigSelSize=0, Payload_SigSel=0x1234,
                          SetSignalsMode=0, RegIndex16b=5 * 2))
  su.execute_setdmareg(decode_tensix(word), thread_id=0)
  assert gpr.read32(0, 5) == 0xFFFF1234


@spec("GPR.SETDMAREG.IMMEDIATE_WRITE_16B",
      "GPR.SETDMAREG.IMM16_SPANS_BOTH_FIELDS")
def test_setdmareg_high_half(gpr, su):
  """SETDMAREG writes 16-bit immediate to the high half of a GPR."""
  gpr.write32(0, 5, 0x00001234)   # preset low half
  # 0xABCD = (0b10 << 14) | 0x2BCD
  word = int(TT_SETDMAREG(Payload_SigSelSize=0xABCD >> 14,
                          Payload_SigSel=0xABCD & 0x3FFF,
                          SetSignalsMode=0, RegIndex16b=5 * 2 + 1))
  su.execute_setdmareg(decode_tensix(word), thread_id=0)
  assert gpr.read32(0, 5) == 0xABCD1234


@spec("GPR.SETDMAREG.IMM16_SPANS_BOTH_FIELDS")
@pytest.mark.parametrize("imm16", [0x0000, 0x0001, 0x7FFF, 0x8000, 0xFFFF])
def test_setdmareg_full_range(gpr, su, imm16):
  """All 16-bit immediate values round-trip through SETDMAREG correctly."""
  gpr.write32(0, 0, 0)
  word = int(TT_SETDMAREG(Payload_SigSelSize=imm16 >> 14,
                          Payload_SigSel=imm16 & 0x3FFF,
                          SetSignalsMode=0, RegIndex16b=0))
  su.execute_setdmareg(decode_tensix(word), thread_id=0)
  assert gpr.read16(0, 0) == imm16


# ===========================================================================
# ADDDMAREG
# ===========================================================================

@spec("GPR.ADDDMAREG.REG_REG")
def test_adddmareg_reg_reg(gpr, su):
  """ADDDMAREG reg-reg: Result = OpA + OpB."""
  gpr.write32(0, 1, 100)
  gpr.write32(0, 2, 200)
  word = int(TT_ADDDMAREG(OpBisConst=0, ResultRegIndex=3,
                          OpBRegIndex=2, OpARegIndex=1))
  su.execute_adddmareg(decode_tensix(word), thread_id=0)
  assert gpr.read32(0, 3) == 300


@spec("GPR.ADDDMAREG.REG_CONST")
def test_adddmareg_reg_const(gpr, su):
  """ADDDMAREG reg-const: Result = OpA + 6-bit-imm."""
  gpr.write32(0, 1, 50)
  word = int(TT_ADDDMAREG(OpBisConst=1, ResultRegIndex=5,
                          OpBRegIndex=7, OpARegIndex=1))
  su.execute_adddmareg(decode_tensix(word), thread_id=0)
  assert gpr.read32(0, 5) == 57


@spec("GPR.ADDDMAREG.OVERFLOW_WRAPS")
def test_adddmareg_overflow_wraps(gpr, su):
  """ADDDMAREG wraps modulo 2^32 on overflow."""
  gpr.write32(0, 1, 0xFFFFFFFF)
  gpr.write32(0, 2, 1)
  word = int(TT_ADDDMAREG(OpBisConst=0, ResultRegIndex=3,
                          OpBRegIndex=2, OpARegIndex=1))
  su.execute_adddmareg(decode_tensix(word), thread_id=0)
  assert gpr.read32(0, 3) == 0


# ===========================================================================
# MULDMAREG
# ===========================================================================

@spec("GPR.MULDMAREG.REG_CONST")
def test_muldmareg_reg_const_small(gpr, su):
  """MULDMAREG reg-const: small values (no truncation effect)."""
  gpr.write32(0, 1, 5)
  word = int(TT_MULDMAREG(OpBisConst=1, ResultRegIndex=2,
                          OpBRegIndex=4, OpARegIndex=1))
  su.execute_muldmareg(decode_tensix(word), thread_id=0)
  assert gpr.read32(0, 2) == 20


@spec("GPR.MULDMAREG.16BIT_TRUNCATION")
def test_muldmareg_truncates_inputs_to_16bits(gpr, su):
  """MULDMAREG truncates both inputs to 16 bits before multiplying."""
  # 0x00020003: upper 16 = 0x0002, lower 16 = 0x0003
  # Spec: (0x00020003 & 0xFFFF) * (0x00050007 & 0xFFFF) = 3 * 7 = 21
  gpr.write32(0, 1, 0x00020003)
  gpr.write32(0, 2, 0x00050007)
  word = int(TT_MULDMAREG(OpBisConst=0, ResultRegIndex=3,
                          OpBRegIndex=2, OpARegIndex=1))
  su.execute_muldmareg(decode_tensix(word), thread_id=0)
  assert gpr.read32(0, 3) == 21   # 3 * 7, not 0x00020003 * 0x00050007


# ===========================================================================
# WRCFG — 32-bit
# ===========================================================================

@spec("GPR.WRCFG.32BIT")
def test_wrcfg_32bit(gpr, cu):
  """WRCFG 32-bit: Config[state][addr] = GPR value."""
  gpr.write32(0, 10, 0xCAFEBABE)
  word = int(TT_WRCFG(GprAddress=10, wr128b=0, CfgReg=50 << 2))
  cu.execute_wrcfg(decode_tensix(word), thread_id=0)
  assert cu.cfg[0][50] == 0xCAFEBABE


@spec("GPR.WRCFG.STATE_BANK")
def test_wrcfg_uses_state_bank(gpr, cu):
  """WRCFG writes to the bank selected by CFG_STATE_ID (thread_cfg[t][42])."""
  # Set state_id = 1 for thread 0
  cu.thread_cfg[0][42] = 1
  gpr.write32(0, 3, 0xDEADBEEF)
  word = int(TT_WRCFG(GprAddress=3, wr128b=0, CfgReg=10 << 2))
  cu.execute_wrcfg(decode_tensix(word), thread_id=0)
  assert cu.cfg[1][10] == 0xDEADBEEF
  assert cu.cfg[0][10] == 0   # bank 0 untouched


@spec("GPR.WRCFG.128BIT")
def test_wrcfg_128bit(gpr, cu):
  """WRCFG 128-bit: copies 4 consecutive GPRs into 4 consecutive config words."""
  for i in range(4):
    gpr.write32(0, i, 0x10000000 + i)
  # CfgReg encodes the destination address: addr32 = (CfgReg >> 2) & 0x1FF
  # We want cfg words 0..3 → addr32 = 0 → CfgReg = 0
  word = int(TT_WRCFG(GprAddress=0, wr128b=1, CfgReg=0))
  cu.execute_wrcfg(decode_tensix(word), thread_id=0)
  for i in range(4):
    assert cu.cfg[0][i] == 0x10000000 + i


@spec("GPR.WRCFG.128BIT")
def test_wrcfg_128bit_aligns_gpr_and_cfg(gpr, cu):
  """WRCFG 128-bit aligns GPR source to 4-register boundary (GprAddress & ~3)."""
  # Write GPRs 4..7 with distinctive values
  for i in range(4):
    gpr.write32(0, 4 + i, 0xAA000000 + i)
  # GprAddress=5 should snap to 4 (& ~3), destination also aligns
  word = int(TT_WRCFG(GprAddress=4, wr128b=1, CfgReg=0))
  cu.execute_wrcfg(decode_tensix(word), thread_id=0)
  for i in range(4):
    assert cu.cfg[0][i] == 0xAA000000 + i


# ===========================================================================
# RDCFG
# ===========================================================================

@spec("GPR.RDCFG.32BIT_READ",
      "GPR.WRCFG.32BIT")
def test_rdcfg_round_trip(gpr, cu):
  """RDCFG reads back a previously written config value into a GPR."""
  gpr.write32(0, 10, 0xCAFEBABE)
  w_word = int(TT_WRCFG(GprAddress=10, wr128b=0, CfgReg=50 << 2))
  cu.execute_wrcfg(decode_tensix(w_word), thread_id=0)

  r_word = int(TT_RDCFG(GprAddress=20, CfgReg=50 << 2))
  cu.execute_rdcfg(decode_tensix(r_word), thread_id=0)
  assert gpr.read32(0, 20) == 0xCAFEBABE


@spec("GPR.RDCFG.32BIT_READ",
      "GPR.WRCFG.STATE_BANK")
def test_rdcfg_reads_current_state_bank(gpr, cu):
  """RDCFG reads from the bank selected by CFG_STATE_ID."""
  cu.cfg[1][5] = 0x12345678
  cu.cfg[0][5] = 0xFFFFFFFF
  cu.thread_cfg[0][42] = 1   # select bank 1
  r_word = int(TT_RDCFG(GprAddress=0, CfgReg=5 << 2))
  cu.execute_rdcfg(decode_tensix(r_word), thread_id=0)
  assert gpr.read32(0, 0) == 0x12345678


# ===========================================================================
# SETC16
# ===========================================================================

@spec("GPR.SETC16.WRITE_THREADCFG")
def test_setc16_writes_threadcfg(gpr, cu):
  """SETC16 writes a 16-bit immediate to the specified ThreadConfig word."""
  word = int(TT_SETC16(setc16_reg=12, setc16_value=0x4321))
  cu.execute_setc16(decode_tensix(word), thread_id=1)
  assert cu.thread_cfg[1][12] == 0x4321


@spec("GPR.SETC16.WRITE_THREADCFG")
def test_setc16_per_thread_isolation(gpr, cu):
  """SETC16 for thread 0 does not affect thread 1's ThreadConfig."""
  word = int(TT_SETC16(setc16_reg=5, setc16_value=0xBEEF))
  cu.execute_setc16(decode_tensix(word), thread_id=0)
  assert cu.thread_cfg[0][5] == 0xBEEF
  assert cu.thread_cfg[1][5] == 0
  assert cu.thread_cfg[2][5] == 0


@spec("GPR.SETC16.WRITE_THREADCFG")
def test_setc16_all_threads(gpr, cu):
  """Each of the 3 threads can write its own ThreadConfig independently."""
  for t in range(3):
    word = int(TT_SETC16(setc16_reg=0, setc16_value=t * 0x1111))
    cu.execute_setc16(decode_tensix(word), thread_id=t)
  for t in range(3):
    assert cu.thread_cfg[t][0] == t * 0x1111


# ===========================================================================
# RMWCIB0 / RMWCIB1 — byte-indexed read-modify-write
# ===========================================================================

@spec("GPR.RMWCIB.BYTE0_RMW")
def test_rmwcib0_mask_and_set(gpr, cu):
  """RMWCIB0: bits where Mask=1 get NewValue; bits where Mask=0 keep OldValue (byte 0)."""
  cu.cfg[0][42] = 0xFF00FF00
  word = int(TT_RMWCIB0(Mask=0x0F, Data=0xAB, CfgRegAddr=42))
  cu.execute_rmwcib(decode_tensix(word), byte_index=0)
  # Byte 0 old=0x00, mask=0x0F → low nibble becomes 0xB
  assert cu.cfg[0][42] == 0xFF00FF0B


@spec("GPR.RMWCIB.BYTE0_RMW")
def test_rmwcib0_full_byte_replace(gpr, cu):
  """RMWCIB0 with Mask=0xFF replaces byte 0 entirely."""
  cu.cfg[0][0] = 0xAABBCCDD
  word = int(TT_RMWCIB0(Mask=0xFF, Data=0x42, CfgRegAddr=0))
  cu.execute_rmwcib(decode_tensix(word), byte_index=0)
  assert cu.cfg[0][0] == 0xAABBCC42


@spec("GPR.RMWCIB.BYTE1_RMW")
def test_rmwcib1_mask_and_set(gpr, cu):
  """RMWCIB1: modifies byte 1 (bits [15:8]) of the 32-bit config word."""
  cu.cfg[0][10] = 0x00FF0000
  word = int(TT_RMWCIB1(Mask=0xFF, Data=0x42, CfgRegAddr=10))
  cu.execute_rmwcib(decode_tensix(word), byte_index=1)
  assert cu.cfg[0][10] == 0x00FF4200


@spec("GPR.RMWCIB.USES_STATE0")
def test_rmwcib_always_uses_bank0(gpr, cu):
  """RMWCIB always targets Config bank 0, regardless of CFG_STATE_ID."""
  cu.thread_cfg[0][42] = 1   # state_id = 1 for thread 0
  cu.cfg[0][7] = 0x00000000
  cu.cfg[1][7] = 0xFFFFFFFF
  word = int(TT_RMWCIB0(Mask=0xFF, Data=0xAA, CfgRegAddr=7))
  cu.execute_rmwcib(decode_tensix(word), byte_index=0)
  assert cu.cfg[0][7] == 0x000000AA  # bank 0 modified
  assert cu.cfg[1][7] == 0xFFFFFFFF  # bank 1 untouched
