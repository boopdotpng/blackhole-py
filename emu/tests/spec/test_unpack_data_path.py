"""Spec tests for ../specs/unpack-data-path.md.

IMPLEMENTED (passes):
  UNPACK.ENCODING.OPCODE          — UNPACR (0x42) dispatched to TRISC0
  UNPACK.ENCODING.WHICH_UNPACKER  — Unpack_block_selection decoded
  UNPACK.ENCODING.SET_DAT_VALID   — SetDatValid decoded and acted on
  UNPACK.BANK_FLIP.SRCA_FLIP      — srca.flip_to_fpu() called when unp0+SetDatValid=1
  UNPACK.BANK_FLIP.SRCB_FLIP      — srcb.flip_to_fpu() called when unp1+SetDatValid=1
  UNPACK.BANK_FLIP.NO_FLIP_WITHOUT_SET_DAT_VALID — no-flip when SetDatValid=0
  UNPACK.NOP.SET_DVALID_FLIP      — UNPACR_NOP Set_Dvalid flip
  UNPACK.NOP.CLEAR_SRCA_BANK      — UNPACR_NOP Src_ClrVal_Ctrl bit 0 zeroes SrcA bank
  UNPACK.NOP.CLEAR_SRCB_BANK      — UNPACR_NOP Src_ClrVal_Ctrl bit 1 zeroes SrcB bank
  UNPACK.ADC.STRUCTURE            — ADCState structure (packers / unpackers / channels)
  UNPACK.ADC.CHANNEL0_INPUT_CHANNEL1_OUTPUT — channel roles are invariant

UNIMPLEMENTED (xfail):
  All format-conversion, L1-read, address-generation, and data-movement clauses.
"""

import struct
import pytest

from emu.tensix import TensixCoprocessor
from dsl import TT_UNPACR, TT_UNPACR_NOP, TT_SETADCXY, TT_SETADCZW

from .conftest import spec


# Helpers

def _bf16_bits(f: float) -> int:
  """Pack a Python float as bfloat16 (big-endian bits 16..31 of IEEE 754 FP32)."""
  return struct.unpack('>H', struct.pack('>f', f)[:2])[0]


def _make_unpacr_word(which_unpacker: int, set_dat_valid: int) -> int:
  """Minimal UNPACR instruction with only WhichUnpacker and SetDatValid set."""
  return int(TT_UNPACR(
    Unpack_block_selection=which_unpacker,
    AddrMode=0,
    CfgContextCntInc=0,
    CfgContextId=0,
    AddrCntContextId=0,
    OvrdThreadId=0,
    SetDatValid=set_dat_valid,
    srcb_bcast=0,
    ZeroWrite2=0,
    AutoIncContextID=0,
    RowSearch=0,
    SearchCacheFlush=0,
    Last=0,
  ))


def _make_unpacr_nop_word(unpacker_select: int, set_dvalid: int,
                           src_clr_val_ctrl: int) -> int:
  """Minimal UNPACR_NOP instruction."""
  return int(TT_UNPACR_NOP(
    Unpacker_Select=unpacker_select,
    Stream_Id=0,
    Msg_Clr_Cnt=0,
    Set_Dvalid=set_dvalid,
    Clr_to1_fmt_Ctrl=0,
    Stall_Clr_Cntrl=0,
    Bank_Clr_Ctrl=0,
    Src_ClrVal_Ctrl=src_clr_val_ctrl,
    Unpack_Pop=0,
  ))


@pytest.fixture
def coproc():
  """Minimal TensixCoprocessor for unpack tests."""
  return TensixCoprocessor()


def _push_step(coproc, word, thread=0, n=1):
  """Push instruction to thread (default 0 = unpack thread) and step n times."""
  coproc.push_instruction(thread, int(word))
  for _ in range(n):
    coproc.step()


# ===========================================================================
# Encoding dispatch
# ===========================================================================

@spec("UNPACK.ENCODING.OPCODE")
def test_unpacr_opcode_dispatches_without_exception(coproc):
  """UNPACR (0x42) must reach TRISC0Decoder without raising."""
  word = _make_unpacr_word(0, 0)
  _push_step(coproc, word)  # must not raise


@spec("UNPACK.ENCODING.WHICH_UNPACKER")
def test_unpacr_which_unpacker_0_targets_srca(coproc):
  """Unpack_block_selection=0 targets SrcA; flip must affect coproc.srca."""
  old_unpack_bank = coproc.srca.unpack_bank
  word = _make_unpacr_word(which_unpacker=0, set_dat_valid=1)
  _push_step(coproc, word)
  # Bank has been flipped → unpack_bank changed.
  assert coproc.srca.unpack_bank != old_unpack_bank


@spec("UNPACK.ENCODING.WHICH_UNPACKER")
def test_unpacr_which_unpacker_1_targets_srcb(coproc):
  """Unpack_block_selection=1 targets SrcB; flip must affect coproc.srcb."""
  old_unpack_bank = coproc.srcb.unpack_bank
  word = _make_unpacr_word(which_unpacker=1, set_dat_valid=1)
  _push_step(coproc, word)
  assert coproc.srcb.unpack_bank != old_unpack_bank


@spec("UNPACK.ENCODING.SET_DAT_VALID")
def test_unpacr_set_dat_valid_1_flips_bank(coproc):
  """SetDatValid=1 triggers bank flip; SetDatValid=0 does not."""
  word_flip = _make_unpacr_word(0, set_dat_valid=1)
  word_noop = _make_unpacr_word(0, set_dat_valid=0)
  old_unpack_bank = coproc.srca.unpack_bank

  _push_step(coproc, word_flip)
  assert coproc.srca.unpack_bank != old_unpack_bank   # flip happened

  after_flip = coproc.srca.unpack_bank
  _push_step(coproc, word_noop)
  assert coproc.srca.unpack_bank == after_flip         # no flip


# ===========================================================================
# Bank flip handshake — IMPLEMENTED
# ===========================================================================

@spec("UNPACK.BANK_FLIP.SRCA_FLIP")
def test_unpacr_srca_flip_transfers_bank_to_matrix_unit(coproc):
  """UNPACR unp0+SetDatValid=1: old unpack bank → 'matrix_unit', unpack_bank advances."""
  old_unpack_bank = coproc.srca.unpack_bank
  word = _make_unpacr_word(which_unpacker=0, set_dat_valid=1)
  _push_step(coproc, word)

  # Old unpack bank is now owned by the matrix unit.
  assert coproc.srca.banks[old_unpack_bank].allowed_client == "matrix_unit"
  # New unpack bank is the other one.
  assert coproc.srca.unpack_bank == old_unpack_bank ^ 1


@spec("UNPACK.BANK_FLIP.SRCB_FLIP")
def test_unpacr_srcb_flip_transfers_bank_to_matrix_unit(coproc):
  """UNPACR unp1+SetDatValid=1: old SrcB unpack bank → 'matrix_unit'."""
  old_unpack_bank = coproc.srcb.unpack_bank
  word = _make_unpacr_word(which_unpacker=1, set_dat_valid=1)
  _push_step(coproc, word)

  assert coproc.srcb.banks[old_unpack_bank].allowed_client == "matrix_unit"
  assert coproc.srcb.unpack_bank == old_unpack_bank ^ 1


@spec("UNPACK.BANK_FLIP.NO_FLIP_WITHOUT_SET_DAT_VALID")
def test_unpacr_no_flip_when_set_dat_valid_zero(coproc):
  """SetDatValid=0: both SrcA banks remain 'unpackers'; unpack_bank unchanged."""
  word = _make_unpacr_word(which_unpacker=0, set_dat_valid=0)
  _push_step(coproc, word)

  for bank in coproc.srca.banks:
    assert bank.allowed_client == "unpackers"
  assert coproc.srca.unpack_bank == 0   # unchanged from initial value


@spec("UNPACK.BANK_FLIP.SRCA_FLIP",
      "UNPACK.BANK_FLIP.SRCB_FLIP")
def test_unpacr_double_flip_restores_ownership(coproc):
  """Two consecutive SetDatValid=1 flips cycle back to the original bank owner pattern."""
  # After 2 flips, unpack_bank should return to 0.
  word = _make_unpacr_word(which_unpacker=0, set_dat_valid=1)
  _push_step(coproc, word)
  assert coproc.srca.unpack_bank == 1

  # Release the first bank so the second flip can proceed cleanly.
  coproc.srca.release_from_fpu()
  _push_step(coproc, word)
  assert coproc.srca.unpack_bank == 0


# ===========================================================================
# UNPACR_NOP side effects — IMPLEMENTED
# ===========================================================================

@spec("UNPACK.NOP.SET_DVALID_FLIP")
def test_unpacr_nop_set_dvalid_flips_srca(coproc):
  """UNPACR_NOP with Set_Dvalid & 1 != 0: flips SrcA bank."""
  old_unpack_bank = coproc.srca.unpack_bank
  word = _make_unpacr_nop_word(unpacker_select=0, set_dvalid=0b0001, src_clr_val_ctrl=0)
  _push_step(coproc, word)
  assert coproc.srca.unpack_bank != old_unpack_bank
  assert coproc.srca.banks[old_unpack_bank].allowed_client == "matrix_unit"


@spec("UNPACK.NOP.SET_DVALID_FLIP")
def test_unpacr_nop_set_dvalid_flips_srcb(coproc):
  """UNPACR_NOP with Unpacker_Select=1 and Set_Dvalid & 1 != 0: flips SrcB bank."""
  old_unpack_bank = coproc.srcb.unpack_bank
  word = _make_unpacr_nop_word(unpacker_select=1, set_dvalid=0b0001, src_clr_val_ctrl=0)
  _push_step(coproc, word)
  assert coproc.srcb.unpack_bank != old_unpack_bank


@spec("UNPACK.NOP.CLEAR_SRCA_BANK")
def test_unpacr_nop_src_clr_val_ctrl_bit0_zeroes_srca(coproc):
  """UNPACR_NOP Src_ClrVal_Ctrl & 1: all SrcA unpack_bank rows become 0."""
  # Pre-seed the SrcA unpack bank with non-zero values.
  bank = coproc.srca.banks[coproc.srca.unpack_bank]
  for r in range(64):
    bank.rows[r] = [0xABCD] * 16

  word = _make_unpacr_nop_word(unpacker_select=0, set_dvalid=0, src_clr_val_ctrl=0b01)
  _push_step(coproc, word)

  # All rows in the unpack bank must be zero.
  for r in range(64):
    assert bank.rows[r] == [0] * 16, f"Row {r} not cleared"


@spec("UNPACK.NOP.CLEAR_SRCB_BANK")
def test_unpacr_nop_src_clr_val_ctrl_bit1_zeroes_srcb(coproc):
  """UNPACR_NOP Src_ClrVal_Ctrl & 2: all SrcB unpack_bank rows become 0."""
  bank = coproc.srcb.banks[coproc.srcb.unpack_bank]
  for r in range(64):
    bank.rows[r] = [0x1234] * 16

  word = _make_unpacr_nop_word(unpacker_select=0, set_dvalid=0, src_clr_val_ctrl=0b10)
  _push_step(coproc, word)

  for r in range(64):
    assert bank.rows[r] == [0] * 16, f"Row {r} not cleared"


@spec("UNPACK.NOP.CLEAR_SRCA_BANK",
      "UNPACK.NOP.CLEAR_SRCB_BANK")
def test_unpacr_nop_src_clr_val_ctrl_both_zeroes_both_banks(coproc):
  """Src_ClrVal_Ctrl=0b11: both SrcA and SrcB unpack banks are cleared."""
  srca_bank = coproc.srca.banks[coproc.srca.unpack_bank]
  srcb_bank = coproc.srcb.banks[coproc.srcb.unpack_bank]
  for r in range(64):
    srca_bank.rows[r] = [0xFF] * 16
    srcb_bank.rows[r] = [0xAA] * 16

  word = _make_unpacr_nop_word(unpacker_select=0, set_dvalid=0, src_clr_val_ctrl=0b11)
  _push_step(coproc, word)

  for r in range(64):
    assert srca_bank.rows[r] == [0] * 16
    assert srcb_bank.rows[r] == [0] * 16


@spec("UNPACK.NOP.CLEAR_SRCA_BANK")
def test_unpacr_nop_clear_does_not_affect_other_bank(coproc):
  """Src_ClrVal_Ctrl=0b01: only the current unpack_bank is cleared; FPU bank untouched."""
  unpack_bank_idx = coproc.srca.unpack_bank
  fpu_bank_idx = 1 - unpack_bank_idx  # the other bank

  # Pre-seed both banks.
  for r in range(64):
    coproc.srca.banks[unpack_bank_idx].rows[r] = [0xBEEF] * 16
    coproc.srca.banks[fpu_bank_idx].rows[r]    = [0xDEAD] * 16

  word = _make_unpacr_nop_word(unpacker_select=0, set_dvalid=0, src_clr_val_ctrl=0b01)
  _push_step(coproc, word)

  # Unpack bank cleared.
  for r in range(64):
    assert coproc.srca.banks[unpack_bank_idx].rows[r] == [0] * 16
  # FPU bank unchanged.
  for r in range(64):
    assert coproc.srca.banks[fpu_bank_idx].rows[r] == [0xDEAD] * 16


# ===========================================================================
# ADC structure — IMPLEMENTED
# ===========================================================================

@spec("UNPACK.ADC.STRUCTURE")
def test_adc_structure_has_unpackers_and_packers(coproc):
  """ADCState has unpackers[0], unpackers[1], and packers with 2 channels each."""
  adc = coproc.adc[0]
  assert len(adc.unpackers) == 2
  for unit in adc.unpackers:
    assert len(unit.channels) == 2
  assert len(adc.packers.channels) == 2


@spec("UNPACK.ADC.STRUCTURE")
def test_adc_setadcxy_updates_unpacker0_channel0(coproc):
  """SETADCXY CntSetMask=1 (UNP0): sets Channel[0].X,Y and Channel[1].X,Y."""
  word = TT_SETADCXY(CntSetMask=0b001, Ch1_Y=3, Ch1_X=2, Ch0_Y=7, Ch0_X=5, BitMask=0b1111)
  _push_step(coproc, word)
  unit = coproc.adc[0].unpackers[0]
  assert unit.channels[0].x.val == 5
  assert unit.channels[0].y.val == 7
  assert unit.channels[1].x.val == 2
  assert unit.channels[1].y.val == 3


@spec("UNPACK.ADC.CHANNEL0_INPUT_CHANNEL1_OUTPUT")
def test_adc_channel0_and_channel1_are_independent(coproc):
  """Channel 0 and Channel 1 counters are independently addressable."""
  # Ch1_X and Ch0_X are 3-bit fields (max 7); use small values.
  word_c0 = TT_SETADCXY(CntSetMask=0b001, Ch1_Y=0, Ch1_X=0, Ch0_Y=6, Ch0_X=4, BitMask=0b0011)
  word_c1 = TT_SETADCXY(CntSetMask=0b001, Ch1_Y=5, Ch1_X=3, Ch0_Y=0, Ch0_X=0, BitMask=0b1100)
  _push_step(coproc, word_c0)
  _push_step(coproc, word_c1)
  unit = coproc.adc[0].unpackers[0]
  assert unit.channels[0].x.val == 4
  assert unit.channels[0].y.val == 6
  assert unit.channels[1].x.val == 3
  assert unit.channels[1].y.val == 5


# ===========================================================================
# Unimplemented: L1 tile layout and data path (all xfail)
# ===========================================================================

@spec("UNPACK.TILE_LAYOUT.HEADER_16B")
def test_unpacr_skips_16b_tile_header(coproc):
  """First datum of a non-BFP tile must be read from L1_base + 16, not L1_base."""
  raise AssertionError("L1 read / tile header skip not implemented")


@spec("UNPACK.TILE_LAYOUT.NON_BFP_ROW_MAJOR")
def test_unpacr_non_bfp_tile_layout_row_major(coproc):
  """Non-BFP tile data is row-major within each face; faces concatenated after header."""
  raise AssertionError("L1 read not implemented")


@spec("UNPACK.TILE_LAYOUT.BFP_EXP_SECTION")
def test_unpacr_bfp_tile_has_exponent_section(coproc):
  """Uncompressed BFP tile: exponent section (ceil(NumExponents/16)*16 B) precedes mantissa."""
  raise AssertionError("BFP tile layout not implemented")


@spec("UNPACK.TILE_LAYOUT.BFP_NO_EXP_SECTION")
def test_unpacr_bfp4_no_exp_section_uses_forced_shared_exp(coproc):
  """BFP4/BFP2 with NoBFPExpSection=1: exponent section omitted; FORCED_SHARED_EXP used."""
  raise AssertionError("Force_shared_exp path not implemented")


@spec("UNPACK.TILE_LAYOUT.COMPRESSED_RSI")
def test_unpacr_compressed_tile_rsi_section(coproc):
  """Compressed tile: RSI section = ceil((NumRows+1)*2/16)*16 bytes of uint16_t offsets."""
  raise AssertionError("Compressed tile RSI not implemented")


@spec("UNPACK.TILE_LAYOUT.COMPRESSED_RLE_DELTA")
def test_unpacr_compressed_tile_rle_delta_interleave(coproc):
  """Compressed stream: [32 datums][32 RLE nibbles] alternating. Nibble = zeros to insert."""
  raise AssertionError("Compressed RLE delta not implemented")


# Input address computation --------

@spec("UNPACK.INPUT_ADDR.BASE_PLUS_OFFSET")
def test_unpacr_input_addr_base_plus_offset_plus_header(coproc):
  """InAddr = (REG3_Base_address + REG7_Offset_address) * 16 + 16 (skip header)."""
  raise AssertionError("Input address computation not implemented")


@spec("UNPACK.INPUT_ADDR.FIRST_DATUM")
def test_unpacr_first_datum_from_adc_counters(coproc):
  """FirstDatum = ((W*ZDim + Z)*YDim + Y)*XDim + X."""
  raise AssertionError("FirstDatum computation not implemented")


@spec("UNPACK.INPUT_ADDR.FIFO_WRAP")
def test_unpacr_input_addr_fifo_wraps_at_limit(coproc):
  """If InAddr_Datums > limit, subtract fifo_size to wrap."""
  raise AssertionError("FIFO wrap not implemented")


# Output address computation --------

@spec("UNPACK.OUTPUT_ADDR.STRIDE_FORMULA")
def test_unpacr_output_addr_stride_formula(coproc):
  """OutAddr = ADDR_BASE_REG_1 + Y1*Ystride + Z1*Zstride + W1*Wstride."""
  raise AssertionError("Output address stride computation not implemented")


@spec("UNPACK.OUTPUT_ADDR.ROW_COL_FROM_OUT_ADDR")
def test_unpacr_row_col_from_output_addr(coproc):
  """Row = OutAddr / 16; Col = OutAddr & 15 → SrcA/SrcB[bank][Row][Col]."""
  raise AssertionError("Row/Col from OutAddr not implemented")


# Main unpack loop --------

@spec("UNPACK.LOOP.DATUM_READ")
def test_unpacr_reads_datum_bytes_from_l1(coproc):
  """Each loop iteration reads DatumSizeBytes from L1 at InAddr_Datums."""
  raise AssertionError("L1 datum read not implemented")


@spec("UNPACK.LOOP.ROW_STRIDE_ADVANCE")
def test_unpacr_advances_by_row_stride_every_16_elements(coproc):
  """After every 16 elements, advance L1 pointer by RowStride (not DatumSizeBytes)."""
  raise AssertionError("RowStride advancement not implemented")


@spec("UNPACK.LOOP.BFP_EXP_READ")
def test_unpacr_reads_one_bfp_exponent_byte_per_16_datums(coproc):
  """BFP: exponent byte advances by 1/16 per datum (one byte per 16 datums)."""
  raise AssertionError("BFP exponent read not implemented")


@spec("UNPACK.LOOP.ALL_DATUMS_ZERO")
def test_unpacr_all_datums_zero_writes_zeros_regardless_of_l1(coproc):
  """AllDatumsAreZero=1: each datum written to Src is 0 regardless of L1 content."""
  raise AssertionError("AllDatumsAreZero not implemented")


@spec("UNPACK.LOOP.WRITE_TO_SRCA")
def test_unpacr_unp0_writes_datums_to_srca_rows(coproc):
  """Unpacker 0 must write formatted datums into SrcA[bank][Row][Col] (skip 4 header rows)."""
  raise AssertionError("SrcA datum write not implemented")


@spec("UNPACK.LOOP.WRITE_TO_SRCB")
def test_unpacr_unp1_writes_datums_to_srcb_rows(coproc):
  """Unpacker 1 must write formatted datums into SrcB[bank][Row & 0x3f][Col]."""
  raise AssertionError("SrcB datum write not implemented")


# Post-instruction counter updates --------

@spec("UNPACK.POST.ADC_INCREMENT")
def test_unpacr_increments_adc_yz_after_instruction(coproc):
  """Post-UNPACR: Channel[0].Y += Ch0YInc, .Z += Ch0ZInc; Channel[1].Y += Ch1YInc."""
  raise AssertionError("ADC post-increment not implemented")


@spec("UNPACK.POST.SRC_ROW_ADVANCE")
def test_unpacr_advances_src_row_when_upd_flag_set(coproc):
  """Unpack_Src_Reg_Set_Upd=1: SrcRow += 16 + SrcRowBase after unpack (no flip)."""
  raise AssertionError("SrcRow advance not implemented")


# ===========================================================================
# Format conversion (all xfail)
# ===========================================================================

@spec("UNPACK.FMT.BF16_TO_SRCA")
def test_unpacr_bf16_to_srca_write_src_bf16_layout(coproc):
  """BF16 → SrcA: WriteSrcBF16(datum) = WriteSrcTF32(datum<<3), 19-bit TF32 layout."""
  raise AssertionError("BF16→SrcA format conversion not implemented")


@spec("UNPACK.FMT.FP32_TO_BF16_FLUSH_DENORMAL")
def test_unpacr_fp32_to_bf16_flushes_denormals_to_zero(coproc):
  """FP32→BF16 path: denormal inputs (no exponent bits) are flushed to ±0."""
  raise AssertionError("FP32→BF16 denormal flush not implemented")


@spec("UNPACK.FMT.BFP8_EXPANSION")
def test_unpacr_bfp8_to_bf16_expansion(coproc):
  """BFP8→BF16: normalize mantissa against shared exponent; sign-magnitude to BF16."""
  raise AssertionError("BFP8→BF16 expansion not implemented")


@spec("UNPACK.FMT.BFP8A_EXPANSION")
def test_unpacr_bfp8a_to_fp16_expansion(coproc):
  """BFP8a→FP16: 5-bit exponent; normalize mantissa; result in FP16."""
  raise AssertionError("BFP8a→FP16 expansion not implemented")


@spec("UNPACK.FMT.INT8_OVERLAY")
def test_unpacr_int8_sign_magnitude_overlay(coproc):
  """INT8 sign-magnitude: sign bit extracted; magnitude with dummy FP16 exponent 8."""
  raise AssertionError("INT8 overlay conversion not implemented")


@spec("UNPACK.FMT.REGISTER_LAYOUT_TRANSFORMS")
def test_unpacr_register_layout_transforms_rearrange_fields(coproc):
  """WriteSrcTF32/WriteSrcBF16/WriteDstBF16 etc. rearrange IEEE fields into HW layout."""
  raise AssertionError("Register layout transforms not implemented")
