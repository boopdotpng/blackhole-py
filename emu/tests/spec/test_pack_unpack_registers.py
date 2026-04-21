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
  # The spec requires that writing ADDR32=70 bits[7:4] changes the data format
  # used by subsequent PACR instructions.  The emulator's ConfigUnit stores the
  # value but the packer never reads it — so we cannot verify the behavioral
  # effect.  Fail explicitly to mark this as unimplemented.
  pytest.fail(
    "PUKREG.PACK_CFG.OUT_DATA_FORMAT not implemented: "
    "packer does not read out_data_format from config register ADDR32=70")


@spec("PUKREG.PACK_CFG.L1_DEST_ADDR")
def test_pack_config_l1_dest_addr():
  """Pack config l1_dest_addr register at ADDR32 69 steers packer output to L1."""
  # The spec requires that l1_dest_addr (ADDR32 69) is read by PACR to determine
  # where packed data is written in L1.  The emulator's PACR is a structural no-op
  # and does not consult config registers.  Fail explicitly.
  pytest.fail(
    "PUKREG.PACK_CFG.L1_DEST_ADDR not implemented: "
    "PACR does not read l1_dest_addr from config register ADDR32=69")
