"""Spec tests for ../specs/pack-data-path.md.

All pack (PACR) behavior clauses are xfail(strict=True) because PACR is a
structural no-op in trisc2.py::TRISC2Decoder._pacr (documented pass statement).

The xfail list below represents the full emulator PACR roadmap:

UNIMPLEMENTED (xfail):
  PACK.ENCODING.PACKERMASK        — PackerMask field not decoded
  PACK.ENCODING.LAST_FLAG         — Last flag not checked
  PACK.ENCODING.FLUSH_FLAG        — Flush flag not checked
  PACK.ENCODING.ZERO_WRITE        — ZeroWrite not decoded
  PACK.DEST_READ.ADC_CHANNEL0     — ADC not consulted
  PACK.DEST_READ.INPUT_NUM_DATUMS — InputNumDatums not computed
  PACK.DEST_READ.BYTES_PER_DATUM  — format bytes-per-datum not decoded
  PACK.DEST_READ.DEST_TARGET_OFFSET — packer Dest offset not applied
  PACK.DEST_READ.L1_SOURCE_MODE   — L1 source mode not implemented
  PACK.ADC.ADDR_MOD_POST_PACR     — AddrMod not applied after PACR
  PACK.ADC.CHANNEL_ASSIGNMENT     — channels not consumed by PACR
  PACK.EARLY_FMT.*                — all early format conversion paths
  PACK.LATE_FMT.*                 — all BFP shared-exp assembly paths
  PACK.RELU.*                     — all ReLU activation modes
  PACK.EXP_THRESH.*               — exponent thresholding
  PACK.L1_OUTPUT.*                — no L1 writes occur at all
  PACK.MULTI_PACKER.*             — no multi-packer dispatch

PARTIALLY IMPLEMENTED (pass):
  PACK.ENCODING.OPCODE            — dispatch reaches trisc2 (though body is pass)
  PACK.ADC.SETADCXX_X_RANGE       — SETADCXX itself is implemented; xend consumed
"""

import pytest

from emu.tensix import TensixCoprocessor
from emu.dsl import (
  TT_PACR, TT_UNPACR, TT_SETADCXX,
)

from .conftest import spec


# Local fixtures

@pytest.fixture
def coproc():
  """Minimal TensixCoprocessor for pack/ADC tests."""
  return TensixCoprocessor()


def _push_step(coproc, word, n=1):
  """Push one instruction and step n times."""
  coproc.push_instruction(2, int(word))   # thread 2 = trisc2 (pack thread)
  for _ in range(n):
    coproc.step()


def _push_step_t0(coproc, word, n=1):
  """Push to thread 0 (trisc0 = unpack thread) and step."""
  coproc.push_instruction(0, int(word))
  for _ in range(n):
    coproc.step()


# ===========================================================================
# PACR encoding dispatch
# ===========================================================================

@spec("PACK.ENCODING.OPCODE")
def test_pacr_opcode_dispatches_without_exception(coproc):
  """PACR (0x41) must reach TRISC2Decoder without raising — even though it is a no-op."""
  word = TT_PACR(
    CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=0,
    AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0b1111,
    OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=0,
  )
  # Must not raise.
  _push_step(coproc, word)


@spec("PACK.ENCODING.PACKERMASK")
def test_pacr_packermask_zero_maps_to_packer0(coproc):
  """PackerMask=0b0000 is a special case that activates packer 0 only (not all four)."""
  # With a real implementation: packing with mask=0 and mask=1 would produce
  # the same output (one face packed). With mask=0b1111 all four faces are packed.
  # Here we just assert that PackerMask=0 does not write four faces' worth of data.
  # Since PACR is a no-op this assertion trivially passes — but the xfail fires
  # because the test author must prove correct mask decoding, not a no-op result.
  raise AssertionError("PackerMask decoding not implemented")


@spec("PACK.ENCODING.LAST_FLAG")
def test_pacr_last_flag_signals_tile_complete(coproc):
  """PACR with Last=1 must flush packer buffers and signal tile-pack complete."""
  raise AssertionError("Last flag not implemented")


@spec("PACK.ENCODING.FLUSH_FLAG")
def test_pacr_flush_flag_sets_needs_new_address(coproc):
  """PACR with Flush=1 must set NeedsNewAddress for the next PACR."""
  raise AssertionError("Flush flag not implemented")


@spec("PACK.ENCODING.ZERO_WRITE")
def test_pacr_zero_write_outputs_zeros(coproc):
  """ZeroWrite=1: packer must write zeros to L1 regardless of Dest contents."""
  raise AssertionError("ZeroWrite not implemented")


# ===========================================================================
# ADC — SETADCXX is implemented; verify it sets the x_range correctly
# ===========================================================================

@spec("PACK.ADC.SETADCXX_X_RANGE")
def test_setadcxx_sets_x_start_and_x_end(coproc):
  """SETADCXX(PAC, x_end2=15, x_start=0): verify packer ADC X state updated."""
  # p_setadc::PAC = 0b100 = 4
  word = TT_SETADCXX(CntSetMask=0b100, x_end2=15, x_start=0)
  # Issue from thread 2; ADC is per-thread (thread 2 = trisc2 pack thread).
  coproc.push_instruction(2, int(word))
  coproc.step()
  # The packer ADC is adc[2].packers.
  # execute_setadcxx sets ch.x.val = x_start for both channels,
  # and ch.x.cr = x_end2 for both channels.
  pck_unit = coproc.adc[2].packers
  assert pck_unit.channels[0].x.val == 0    # x_start
  assert pck_unit.channels[0].x.cr  == 15   # x_end2
  assert pck_unit.channels[1].x.val == 0    # x_start (same per execute_setadcxx)
  assert pck_unit.channels[1].x.cr  == 15   # x_end2


# ===========================================================================
# Dest → L1 data movement (all xfail — PACR is no-op)
# ===========================================================================

@spec("PACK.DEST_READ.ADC_CHANNEL0")
def test_pacr_reads_dest_using_adc_channel0(coproc):
  """PACR must read Dest at the address computed from ADC Channel 0 counters."""
  raise AssertionError("Dest read via ADC not implemented")


@spec("PACK.DEST_READ.INPUT_NUM_DATUMS")
def test_pacr_input_num_datums_from_adc_x_range(coproc):
  """InputNumDatums = Channel[1].X - Channel[0].X + 1."""
  raise AssertionError("InputNumDatums computation not implemented")


@spec("PACK.DEST_READ.BYTES_PER_DATUM")
def test_pacr_bytes_per_datum_from_in_data_format(coproc):
  """In_data_format bits [1:0] determine BytesPerDatum (4/2/1)."""
  raise AssertionError("BytesPerDatum not implemented")


@spec("PACK.DEST_READ.DEST_TARGET_OFFSET")
def test_pacr_dest_target_reg_offset_selects_tile(coproc):
  """DEST_TARGET_REG_CFG_PACK_SEC[i].Offset << 4 must be added to DatumIndex."""
  raise AssertionError("Dest target offset not implemented")


@spec("PACK.DEST_READ.L1_SOURCE_MODE")
def test_pacr_l1_source_mode_skips_early_conversion(coproc):
  """Source_interface_selection=1: packer 0 reads from L1, skipping early format conversion."""
  raise AssertionError("L1 source mode not implemented")


# ===========================================================================
# Early format conversion (all xfail)
# ===========================================================================

@spec("PACK.EARLY_FMT.FORMAT_ENCODING")
def test_pacr_early_format_encoding_table(coproc):
  """4-bit In_data_format must decode to the correct format (0=FP32, 5=BF16, etc.)."""
  raise AssertionError("Early format encoding not implemented")


@spec("PACK.EARLY_FMT.FP32_TO_BF16")
def test_pacr_fp32_to_bf16_truncates_mantissa_and_flushes_denormals(coproc):
  """FP32 Dest → BF16 early conv: drop low 16 bits; denormals → ±0."""
  raise AssertionError("Early FP32→BF16 conversion not implemented")


@spec("PACK.EARLY_FMT.READ_RAW_BYPASS")
def test_pacr_read_raw_bypasses_early_conversion(coproc):
  """Read_raw=1: identity/bitcast path — no rounding or shifting applied."""
  raise AssertionError("Read_raw bypass not implemented")


@spec("PACK.EARLY_FMT.READ_32B_DATA")
def test_pacr_read_32b_data_flag_selects_dest_word_width(coproc):
  """Read_32b_data=1: read 32-bit rows from Dest; =0: read 16-bit rows."""
  raise AssertionError("Read_32b_data not implemented")


# ===========================================================================
# Late format conversion / BFP shared exponent assembly (all xfail)
# ===========================================================================

@spec("PACK.LATE_FMT.BFP_SHARED_EXP")
def test_pacr_bfp_shared_exp_is_max_across_16_datums(coproc):
  """BFP late conversion: shared exponent = max(individual exponents) in group of 16."""
  raise AssertionError("BFP shared-exponent assembly not implemented")


@spec("PACK.LATE_FMT.BFP_MANTISSA_BITS")
def test_pacr_bfp8_has_7_mantissa_bits_plus_sign(coproc):
  """BFP8: 7 mantissa + 1 sign = 8 bits per datum."""
  raise AssertionError("BFP mantissa bits not implemented")


@spec("PACK.LATE_FMT.EXP_SECTION_SIZE")
def test_pacr_bfp_writes_exp_section_before_mantissa(coproc):
  """BFP formats: Exp_section_size=num_faces exponent blocks precede the datum bytes in L1."""
  raise AssertionError("Exp_section_size not implemented")


@spec("PACK.LATE_FMT.DIS_SHARED_EXP_ASSEMBLER")
def test_pacr_dis_shared_exp_assembler_disables_normalization(coproc):
  """Dis_shared_exp_assembler=1: each datum's own exponent used, no group normalization."""
  raise AssertionError("Dis_shared_exp_assembler not implemented")


# ===========================================================================
# ReLU activation (all xfail)
# ===========================================================================

@spec("PACK.RELU.NO_RELU")
def test_pacr_relu_mode0_identity(coproc):
  """ApplyRelu=0: no activation; all values pass through unchanged."""
  raise AssertionError("ReLU not implemented")


@spec("PACK.RELU.ZERO_RELU")
def test_pacr_relu_mode1_zeros_negatives(coproc):
  """ApplyRelu=1 (ZERO_RELU): x <= 0 → 0; positive values pass."""
  raise AssertionError("ZERO_RELU not implemented")


@spec("PACK.RELU.MIN_THRESHOLD_RELU")
def test_pacr_relu_mode2_min_threshold(coproc):
  """ApplyRelu=2: x <= threshold → 0 (threshold >= 0)."""
  raise AssertionError("MIN_THRESHOLD_RELU not implemented")


@spec("PACK.RELU.MAX_THRESHOLD_RELU")
def test_pacr_relu_mode3_max_threshold_clamp(coproc):
  """ApplyRelu=3: clamp x to [0, threshold]."""
  raise AssertionError("MAX_THRESHOLD_RELU not implemented")


# ===========================================================================
# Exponent thresholding (xfail)
# ===========================================================================

@spec("PACK.EXP_THRESH.ZEROES_BELOW_THRESHOLD")
def test_pacr_exp_threshold_zeroes_small_exponents(coproc):
  """Exp_threshold_en=1, Exp_threshold=113: FP32 values with exponent < 113 → 0."""
  raise AssertionError("Exp_threshold_en not implemented")


# ===========================================================================
# L1 output (all xfail — no L1 writes occur)
# ===========================================================================

@spec("PACK.L1_OUTPUT.ALIGNED_WRITES")
def test_pacr_l1_output_is_16b_aligned(coproc):
  """All packer L1 output addresses must be multiples of 16."""
  raise AssertionError("L1 writes not implemented")


@spec("PACK.L1_OUTPUT.OUTPUT_ADC_CHANNEL1")
def test_pacr_l1_output_address_from_adc_channel1(coproc):
  """ADC Channel 1 Y/Z/W drive the L1 output address."""
  raise AssertionError("L1 output ADC not implemented")


@spec("PACK.L1_OUTPUT.ZERO_COMPRESSION")
def test_pacr_zero_compression_elides_zero_runs(coproc):
  """Disable_zero_compress=0: zero runs in output are compressed before L1 write."""
  raise AssertionError("Zero compression not implemented")


@spec("PACK.L1_OUTPUT.TILE_HEADER")
def test_pacr_writes_16b_tile_header_first(coproc):
  """Packer must write a 16-byte tile header at L1_Dest_addr before any datum bytes."""
  raise AssertionError("Tile header write not implemented")


# ===========================================================================
# Multi-packer model (xfail)
# ===========================================================================

@spec("PACK.MULTI_PACKER.FOUR_PACKERS")
def test_pacr_packermask_1111_fires_all_four_packers(coproc):
  """PackerMask=0b1111: all four packers fire in parallel, each handling one Dest face."""
  raise AssertionError("Multi-packer dispatch not implemented")
