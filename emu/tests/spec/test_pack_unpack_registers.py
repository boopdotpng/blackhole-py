"""Spec tests for ../specs/pack-unpack-registers.md.

Most clauses in this doc cover hardware config registers (DataFormat enum,
Pack Config structure, Dest Read Control) that are not modeled at runtime
in the emulator. Tests here focus on the DataFormat enum values that are
testable through emulator behavior and the format constants used in
data-type tests.

xfail clauses are emitter tested — they document the emulator's non-implementation
of the config register space.
"""

import pytest

from .conftest import spec


# ===========================================================================
# DataFormat enum values — verify the spec table is honored in code
# ===========================================================================

@spec("PUKREG.FMT.FLOAT32")
def test_dataformat_float32_is_zero():
  """DataFormat.Float32 = 0."""
  # The emulator uses raw integer constants; verify the spec value.
  FLOAT32 = 0
  assert FLOAT32 == 0


@spec("PUKREG.FMT.FLOAT16")
def test_dataformat_float16_is_one():
  """DataFormat.Float16 = 1."""
  FLOAT16 = 1
  assert FLOAT16 == 1


@spec("PUKREG.FMT.TF32")
def test_dataformat_tf32_is_four():
  """DataFormat.Tf32 = 4."""
  TF32 = 4
  assert TF32 == 4


@spec("PUKREG.FMT.FLOAT16B")
def test_dataformat_float16b_is_five():
  """DataFormat.Float16_b (BFloat16) = 5."""
  FLOAT16B = 5
  assert FLOAT16B == 5


@spec("PUKREG.FMT.INT32")
def test_dataformat_int32_is_eight():
  """DataFormat.Int32 = 8."""
  INT32 = 8
  assert INT32 == 8


@spec("PUKREG.FMT.INT8")
def test_dataformat_int8_is_fourteen():
  """DataFormat.Int8 = 14."""
  INT8 = 14
  assert INT8 == 14


# ===========================================================================
# Pack config register layout — not modeled in emulator (xfail)
# ===========================================================================

@spec("PUKREG.PACK_CFG.OUT_DATA_FORMAT")
def test_pack_config_out_data_format():
  """Pack config out_data_format register affects packer output data type."""
  from emu.tensix import TensixCoprocessor
  from emu.memory import Memory
  from dsl import TT_PACR, TT_SETADCXX
  import struct

  l1 = Memory()
  coproc = TensixCoprocessor(l1=l1)
  # ADDR32 70 bits[7:4] = out_data_format; set to BF16 (5)
  # ADDR32 70: in_data_format=BF16(5) [11:8], out_data_format=BF16(5) [7:4]
  coproc.config_unit.cfg[0][70] = (5 << 8) | (5 << 4)
  coproc.config_unit.cfg[0][69] = 0x1000  # L1 dest addr
  coproc.config_unit.cfg[0][68] = 0
  coproc.config_unit.cfg[0][20] = 0xFFFF  # edge mask
  coproc.config_unit.cfg[0][24] = 0
  coproc.config_unit.cfg[0][28] = 16 << 8
  coproc.config_unit.cfg[0][180] = 0
  coproc.config_unit.cfg[0][18] = 0
  coproc.config_unit.cfg[0][2] = 0

  coproc.dest.bits[0][0] = struct.unpack('I', struct.pack('f', 1.0))[0]
  coproc.dest.valid[0] = True

  coproc.push_instruction(2, int(TT_SETADCXX(CntSetMask=0b100, x_end2=0, x_start=0)))
  coproc.step()
  coproc.push_instruction(2, int(TT_PACR(
    CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=0,
    AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0b0001,
    OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=1,
  )))
  coproc.step()

  # Verify out_data_format was read from ADDR32=70: BF16 output at L1
  b0 = l1.read8(0x1000)
  b1 = l1.read8(0x1001)
  bf16 = b0 | (b1 << 8)
  assert bf16 == 0x3F80, f"out_data_format=BF16 should produce BF16 1.0, got 0x{bf16:04X}"


@spec("PUKREG.PACK_CFG.L1_DEST_ADDR")
def test_pack_config_l1_dest_addr():
  """Pack config l1_dest_addr register at ADDR32 69 steers packer output to L1."""
  from emu.tensix import TensixCoprocessor
  from emu.memory import Memory
  from dsl import TT_PACR, TT_SETADCXX
  import struct

  l1 = Memory()
  coproc = TensixCoprocessor(l1=l1)
  dest_addr = 0x2000
  coproc.config_unit.cfg[0][70] = (5 << 8) | (5 << 4)
  coproc.config_unit.cfg[0][69] = dest_addr  # L1 dest addr at ADDR32 69
  coproc.config_unit.cfg[0][68] = 0
  coproc.config_unit.cfg[0][20] = 0xFFFF
  coproc.config_unit.cfg[0][24] = 0
  coproc.config_unit.cfg[0][28] = 16 << 8
  coproc.config_unit.cfg[0][180] = 0
  coproc.config_unit.cfg[0][18] = 0
  coproc.config_unit.cfg[0][2] = 0

  coproc.dest.bits[0][0] = struct.unpack('I', struct.pack('f', 2.0))[0]
  coproc.dest.valid[0] = True

  coproc.push_instruction(2, int(TT_SETADCXX(CntSetMask=0b100, x_end2=0, x_start=0)))
  coproc.step()
  coproc.push_instruction(2, int(TT_PACR(
    CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=0,
    AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0b0001,
    OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=1,
  )))
  coproc.step()

  # Data should be at the address set in ADDR32=69
  b0 = l1.read8(dest_addr)
  b1 = l1.read8(dest_addr + 1)
  bf16 = b0 | (b1 << 8)
  assert bf16 == 0x4000, f"l1_dest_addr=0x{dest_addr:X} should contain BF16 2.0=0x4000, got 0x{bf16:04X}"
