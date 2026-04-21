"""Spec tests for ../specs/dest-srca-srcb-registers.md.

Each test is pinned to one or more clauses from
../clauses/dest-srca-srcb-registers.md via the @spec() marker.

Layout:
  - DestRegFile layout and valid-bit semantics
  - ZEROACC clear modes (via regfile API)
  - SrcRegFile layout and AllowedClient
  - Bank flip protocol (flip_to_fpu / release_from_fpu)
  - UNPACR / UNPACR_NOP dispatcher via TRISC0
  - TRNSPSRCB on SrcB rows 16-31
"""

import pytest
from dsl import decode_tensix
from emu.tensix import TensixCoprocessor
from emu.tensix import SrcRegFile, DestRegFile

from .conftest import spec


# ===========================================================================
# DestRegFile layout
# ===========================================================================

@spec("DEST.LAYOUT.1024_ROWS")
def test_dest_has_1024_rows():
  """Dest has ROWS=1024 and COLS=16."""
  dest = DestRegFile()
  assert dest.ROWS == 1024
  assert dest.COLS == 16


@spec("DEST.LAYOUT.VALID_BITS")
def test_dest_valid_bits_init_false():
  """All 1024 valid bits start False."""
  dest = DestRegFile()
  assert len(dest.valid) == 1024
  assert not any(dest.valid)


@spec("DEST.ZEROACC.CLR_VALID_NOT_BITS")
def test_dest_clear_valid_leaves_bits():
  """clear_valid clears the valid bit but does not wipe the data bits."""
  dest = DestRegFile()
  dest.bits[10][3] = 0xABCD
  dest.valid[10] = True
  dest.clear_valid(10)
  assert not dest.valid[10]
  assert dest.bits[10][3] == 0xABCD   # data untouched


@spec("DEST.ZEROACC.CLEAR_SPECIFIC_ROW")
def test_dest_clear_valid_specific():
  """clear_valid clears exactly one row."""
  dest = DestRegFile()
  dest.valid[5] = True
  dest.valid[6] = True
  dest.clear_valid(5)
  assert not dest.valid[5]
  assert dest.valid[6]   # unaffected


@spec("DEST.ZEROACC.CLEAR_RANGE_16")
def test_dest_clear_range_16():
  """clear_range(start, 16) clears 16 consecutive rows."""
  dest = DestRegFile()
  for r in range(1024):
    dest.valid[r] = True
  dest.clear_range(10, 16)
  for r in range(10, 26):
    assert not dest.valid[r]
  assert dest.valid[9]    # just before range
  assert dest.valid[26]   # just after range


@spec("DEST.ZEROACC.CLEAR_HALF")
def test_dest_clear_half_low():
  """clear_half(0) clears rows 0-511."""
  dest = DestRegFile()
  for r in range(1024):
    dest.valid[r] = True
  dest.clear_half(0)
  assert not any(dest.valid[:512])
  assert all(dest.valid[512:])


@spec("DEST.ZEROACC.CLEAR_HALF")
def test_dest_clear_half_high():
  """clear_half(1) clears rows 512-1023."""
  dest = DestRegFile()
  for r in range(1024):
    dest.valid[r] = True
  dest.clear_half(1)
  assert all(dest.valid[:512])
  assert not any(dest.valid[512:])


@spec("DEST.ZEROACC.CLEAR_ALL")
def test_dest_clear_all():
  """clear_all() clears all 1024 valid bits."""
  dest = DestRegFile()
  for r in range(1024):
    dest.valid[r] = True
  dest.clear_all()
  assert not any(dest.valid)


# ===========================================================================
# SrcRegFile layout
# ===========================================================================

@spec("SRC.LAYOUT.TWO_BANKS")
def test_src_has_two_banks():
  """SrcRegFile has 2 banks, each with 64 rows × 16 cols."""
  src = SrcRegFile("SrcA")
  assert len(src.banks) == 2
  assert len(src.banks[0].rows) == 64
  assert len(src.banks[0].rows[0]) == 16


@spec("SRC.BANK.INITIAL_STATE")
def test_src_bank_initial_allowed_client():
  """Both banks start with allowed_client='unpackers'."""
  src = SrcRegFile("SrcA")
  assert src.banks[0].allowed_client == "unpackers"
  assert src.banks[1].allowed_client == "unpackers"


@spec("SRC.BANK.ALLOWED_CLIENT")
def test_src_bank_allowed_client_values():
  """AllowedClient can only be 'unpackers' or 'matrix_unit'."""
  src = SrcRegFile("SrcA")
  src.flip_to_fpu()
  assert src.banks[0].allowed_client == "matrix_unit"
  src.release_from_fpu()
  assert src.banks[0].allowed_client == "unpackers"


# ===========================================================================
# Bank flip protocol
# ===========================================================================

@spec("SRC.FLIP_TO_FPU.SETS_MATRIX_UNIT")
def test_flip_to_fpu_sets_matrix_unit():
  """flip_to_fpu(): sets bank0 allowed_client='matrix_unit', flips unpack_bank to 1."""
  src = SrcRegFile("SrcA")
  assert src.unpack_bank == 0
  src.flip_to_fpu()
  assert src.banks[0].allowed_client == "matrix_unit"
  assert src.unpack_bank == 1


@spec("SRC.FLIP_TO_FPU.SETS_MATRIX_UNIT")
def test_flip_to_fpu_second_flip():
  """Second flip_to_fpu(): bank1 becomes matrix_unit, unpack_bank flips back to 0."""
  src = SrcRegFile("SrcA")
  src.flip_to_fpu()  # bank0->matrix_unit, unpack_bank=1
  src.flip_to_fpu()  # bank1->matrix_unit, unpack_bank=0
  assert src.banks[1].allowed_client == "matrix_unit"
  assert src.unpack_bank == 0


@spec("SRC.RELEASE_FROM_FPU.RESTORES_UNPACKERS")
def test_release_from_fpu_restores_unpackers():
  """release_from_fpu(): restores bank to 'unpackers' and flips fpu_bank."""
  src = SrcRegFile("SrcA")
  src.flip_to_fpu()
  assert src.fpu_bank == 0
  assert src.banks[0].allowed_client == "matrix_unit"
  src.release_from_fpu()
  assert src.banks[0].allowed_client == "unpackers"
  assert src.fpu_bank == 1


@spec("SRC.RELEASE_FROM_FPU.RESTORES_UNPACKERS")
def test_flip_release_cycle():
  """Full flip-then-release cycle restores ownership."""
  src = SrcRegFile("SrcA")
  src.flip_to_fpu()
  src.release_from_fpu()
  assert src.banks[0].allowed_client == "unpackers"
  assert src.banks[1].allowed_client == "unpackers"


# ===========================================================================
# UNPACR / UNPACR_NOP dispatcher via TRISC0
# ===========================================================================

@spec("SRC.UNPACR_NOP.BANK_FLIP")
def test_unpacr_nop_bank_flip_srca():
  """UNPACR_NOP with unpacker_sel=0 and set_dvalid=1 flips SrcA bank to matrix_unit."""
  c = TensixCoprocessor()
  assert c.srca.banks[0].allowed_client == "unpackers"
  # UNPACR_NOP: unpacker_sel=0 (SrcA), set_dvalid=1
  word = (0x43 << 24) | (0 << 23) | (1 << 8)
  c.push_instruction(0, word)
  c.step()
  assert c.srca.banks[0].allowed_client == "matrix_unit"


@spec("SRC.UNPACR_NOP.BANK_FLIP")
def test_unpacr_nop_bank_flip_srcb():
  """UNPACR_NOP with unpacker_sel=1 and set_dvalid=1 flips SrcB bank to matrix_unit."""
  c = TensixCoprocessor()
  assert c.srcb.banks[0].allowed_client == "unpackers"
  # UNPACR_NOP: unpacker_sel=1 (SrcB), set_dvalid=1
  word = (0x43 << 24) | (1 << 23) | (1 << 8)
  c.push_instruction(0, word)
  c.step()
  assert c.srcb.banks[0].allowed_client == "matrix_unit"


@spec("SRC.UNPACR.BANK_FLIP")
def test_unpacr_bank_flip_srca():
  """UNPACR with block_sel=0 (SrcA) and set_dvalid=1 flips SrcA to matrix_unit."""
  c = TensixCoprocessor()
  # UNPACR: block_sel=0 (SrcA), set_dvalid bit
  word = (0x42 << 24) | (0 << 23) | (1 << 6)
  c.push_instruction(0, word)
  c.step()
  assert c.srca.banks[0].allowed_client == "matrix_unit"


@spec("SRC.UNPACR.BANK_FLIP")
def test_unpacr_bank_flip_srcb():
  """UNPACR with block_sel=1 (SrcB) and set_dvalid=1 flips SrcB to matrix_unit."""
  c = TensixCoprocessor()
  word = (0x42 << 24) | (1 << 23) | (1 << 6)
  c.push_instruction(0, word)
  c.step()
  assert c.srcb.banks[0].allowed_client == "matrix_unit"


# ===========================================================================
# TRNSPSRCB on rows 16-31
# ===========================================================================

@spec("SRC.TRNSPSRCB.ROWS_16_31")
def test_trnspsrcb_transposes_rows_16_31():
  """TRNSPSRCB transposes the 16×16 block in SrcB rows 16-31."""
  c = TensixCoprocessor()
  bank = c.srcb.banks[c.srcb.fpu_bank]
  for r in range(16):
    for col in range(16):
      bank.rows[16 + r][col] = r * 16 + col
  word = (0x16 << 24)
  c.push_instruction(1, word)
  c.step()
  for r in range(16):
    for col in range(16):
      assert bank.rows[16 + r][col] == col * 16 + r


@spec("SRC.TRNSPSRCB.ROWS_16_31")
def test_trnspsrcb_rows_0_15_unchanged():
  """TRNSPSRCB does not touch SrcB rows 0-15."""
  c = TensixCoprocessor()
  bank = c.srcb.banks[c.srcb.fpu_bank]
  sentinel = 0xBEEF
  for r in range(16):
    for col in range(16):
      bank.rows[r][col] = sentinel
  word = (0x16 << 24)
  c.push_instruction(1, word)
  c.step()
  for r in range(16):
    for col in range(16):
      assert bank.rows[r][col] == sentinel
