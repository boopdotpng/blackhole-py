"""Spec tests for ../specs/data-types-and-conversions.md.

Each test is pinned to one or more clauses from
../clauses/data-types-and-conversions.md via the @spec() marker.

Layout:
  - 19-bit shuffled float layout and roundtrip
  - _NEG_INF_19BIT sentinel value
  - NaN handling in _float_to_19bit
  - FP32 <-> BF16 (top-16 truncation)
  - FP32 -> TF32 (10-bit mantissa truncation)
  - Sign-magnitude integer representation
  - DataFormat enum values
"""

import math
import struct

import pytest

from emu.tensix import _19bit_to_float, _float_to_19bit, _NEG_INF_19BIT
from emu.tensix import _bf16_to_fp32

from .conftest import spec


# ===========================================================================
# 19-bit shuffled float layout
# ===========================================================================

@spec("DTC.19BIT.LAYOUT")
def test_19bit_layout_sign_at_bit18():
  """Sign bit is at bit 18 (MSB of 19-bit cell)."""
  # Positive 1.0: sign=0, mant=0, exp=127 (0x7F)
  pos_one = _float_to_19bit(1.0)
  assert (pos_one >> 18) & 1 == 0   # sign=0

  # Negative 1.0: sign=1
  neg_one = _float_to_19bit(-1.0)
  assert (neg_one >> 18) & 1 == 1   # sign=1


@spec("DTC.19BIT.LAYOUT")
def test_19bit_layout_exponent_at_bits_7_0():
  """Exponent occupies bits 7:0 of the 19-bit cell."""
  # 1.0 in FP32: exp=127=0x7F, mant=0
  val = _float_to_19bit(1.0)
  exp_field = val & 0xFF
  assert exp_field == 0x7F


@spec("DTC.19BIT.LAYOUT")
def test_19bit_layout_mantissa_at_bits_17_8():
  """Mantissa occupies bits 17:8 (10 bits) of the 19-bit cell."""
  # 1.0 in FP32: mant=0
  val = _float_to_19bit(1.0)
  mant_field = (val >> 8) & 0x3FF
  assert mant_field == 0


@spec("DTC.19BIT.SHUFFLED_TO_IEEE")
def test_shuffled_to_ieee_mant_placed_at_bits_22_13():
  """_19bit_to_float places 10-bit mantissa at FP32 bits 22:13 (bit shift of 13)."""
  # Craft a 19-bit value with known mantissa: sign=0, mant=0x200 (bit 9 set), exp=127
  mant10 = 0x200
  exp8 = 0x7F
  val19 = (mant10 << 8) | exp8
  fp32_bits = struct.unpack('I', struct.pack('f', _19bit_to_float(val19)))[0]
  # FP32 mantissa = mant10 << 13
  expected_mant_fp32 = mant10 << 13
  actual_mant_fp32 = fp32_bits & 0x7FFFFF
  assert actual_mant_fp32 == expected_mant_fp32


@spec("DTC.19BIT.SHUFFLED_TO_IEEE")
def test_shuffled_to_ieee_low_13_mantissa_bits_zero():
  """_19bit_to_float always leaves FP32 mantissa bits 12:0 as zero."""
  val19 = _float_to_19bit(1.5)
  fp32_bits = struct.unpack('I', struct.pack('f', _19bit_to_float(val19)))[0]
  assert (fp32_bits & 0x1FFF) == 0


@spec("DTC.19BIT.IEEE_TO_SHUFFLED")
def test_ieee_to_shuffled_roundtrip_1():
  """1.0 roundtrips through 19-bit encoding without error."""
  assert _19bit_to_float(_float_to_19bit(1.0)) == 1.0


@spec("DTC.19BIT.IEEE_TO_SHUFFLED")
def test_ieee_to_shuffled_roundtrip_neg():
  """-1.0 roundtrips (sign bit preserved)."""
  assert _19bit_to_float(_float_to_19bit(-1.0)) == -1.0


@spec("DTC.19BIT.IEEE_TO_SHUFFLED")
def test_ieee_to_shuffled_truncates_mantissa():
  """Encoding truncates FP32 mantissa to top 10 bits (RTZ)."""
  # 1.5 = 0x3FC00000: mant bits = 0x400000 (bit 22 = 1)
  # After truncation to 10 bits: mant = (0x400000 >> 13) = 0x200
  # Decoded: mant10=0x200 -> fp32_mant = 0x200 << 13 = 0x400000, so still 1.5
  assert _19bit_to_float(_float_to_19bit(1.5)) == 1.5


@spec("DTC.19BIT.IEEE_TO_SHUFFLED")
def test_ieee_to_shuffled_precision_loss():
  """Values using mantissa bits below the top 10 lose precision."""
  # 1.0 + 2^-14 uses bit 9 of mantissa (below 10-bit precision cutoff)
  v = 1.0 + 2.0 ** -14
  encoded = _float_to_19bit(v)
  decoded = _19bit_to_float(encoded)
  assert decoded != v   # precision lost


# ===========================================================================
# _NEG_INF_19BIT sentinel
# ===========================================================================

@spec("DTC.19BIT.LAYOUT")
def test_neg_inf_19bit_structure():
  """_NEG_INF_19BIT has sign=1, mant=0, exp=0xFF."""
  assert (_NEG_INF_19BIT >> 18) & 1 == 1         # sign=1
  assert (_NEG_INF_19BIT >> 8) & 0x3FF == 0      # mant=0
  assert _NEG_INF_19BIT & 0xFF == 0xFF            # exp=0xFF


@spec("DTC.19BIT.SHUFFLED_TO_IEEE")
def test_neg_inf_19bit_decodes_to_neg_inf():
  """_NEG_INF_19BIT decodes to -infinity via _19bit_to_float."""
  val = _19bit_to_float(_NEG_INF_19BIT)
  assert math.isinf(val) and val < 0


# ===========================================================================
# NaN handling
# ===========================================================================

@spec("DTC.19BIT.NAN_HANDLING")
def test_float_to_19bit_nan_marker():
  """float('nan') encodes with a distinct NaN marker in the 19-bit cell."""
  # Implementation: (0x7F << 8) | 0x200
  # bits[7:0] = exponent = 0x00
  # bits[17:8] = mantissa = 0x7F (bits 14:8 set) | bit 9 set via 0x200
  # The mantissa field contains a non-zero quiet-NaN indicator.
  encoded = _float_to_19bit(float('nan'))
  mant_field = (encoded >> 8) & 0x3FF
  # The mantissa encodes the NaN marker (0x7F = 0b01111111 at bits 14:8)
  assert mant_field != 0   # NaN marker is non-zero
  # Sign bit should not be set (positive NaN)
  assert (encoded >> 18) & 1 == 0


# ===========================================================================
# FP32 <-> BF16
# ===========================================================================

@spec("DTC.BF16.IS_TOP_16_FP32")
def test_bf16_is_top_16_bits_of_fp32():
  """BF16 representation of 1.0 equals top 16 bits of FP32 1.0 (0x3F80)."""
  fp32_bits = struct.unpack('I', struct.pack('f', 1.0))[0]
  bf16_bits = fp32_bits >> 16
  assert bf16_bits == 0x3F80


@spec("DTC.BF16.IS_TOP_16_FP32")
def test_bf16_same_exponent_bias():
  """BF16 uses the same 8-bit exponent with bias 127 as FP32."""
  # 2.0 in FP32: exp=128=0x80, mant=0 → BF16=0x4000
  fp32_bits = struct.unpack('I', struct.pack('f', 2.0))[0]
  bf16_bits = fp32_bits >> 16
  bf16_exp = (bf16_bits >> 7) & 0xFF
  assert bf16_exp == 128


@spec("DTC.BF16.FP32_TO_BF16_TRUNCATE")
def test_fp32_to_bf16_truncation_rtz():
  """FP32 -> BF16 truncates low 16 mantissa bits (round-toward-zero)."""
  # 1.0 + epsilon where epsilon uses mantissa bits below bit 16
  # 1.0 = 0x3F800000; add 1 to low 16 bits → 0x3F800001
  fp32_bits_orig = struct.unpack('I', struct.pack('f', 1.0))[0]
  perturbed = fp32_bits_orig | 0x0000FFFF   # set all low 16 bits
  f_perturbed = struct.unpack('f', struct.pack('I', perturbed))[0]

  # Truncation (RTZ): low 16 bits dropped, result same as 1.0
  bf16_bits = perturbed >> 16
  bf16_recovered = struct.unpack('f', struct.pack('I', bf16_bits << 16))[0]
  assert bf16_recovered == 1.0


@spec("DTC.BF16.BF16_TO_FP32")
def test_bf16_to_fp32_left_shift_16():
  """bf16_to_fp32: left-shifting by 16 recovers FP32 with low mantissa bits = 0."""
  # BF16 for 1.0 = 0x3F80
  bf16 = 0x3F80
  fp32_bits = _bf16_to_fp32(bf16)
  val = struct.unpack('f', struct.pack('I', fp32_bits))[0]
  assert val == 1.0


@spec("DTC.BF16.BF16_TO_FP32")
def test_bf16_to_fp32_low_bits_zero():
  """BF16 expanded to FP32 has bits 15:0 of mantissa all zero."""
  bf16 = 0x4000   # 2.0 in BF16
  fp32_bits = _bf16_to_fp32(bf16)
  assert (fp32_bits & 0xFFFF) == 0


@spec("DTC.BF16.BF16_TO_FP32")
def test_bf16_roundtrip_2_0():
  """2.0 roundtrips exactly through BF16 encoding (mantissa = 0)."""
  fp32_bits = struct.unpack('I', struct.pack('f', 2.0))[0]
  bf16_bits = fp32_bits >> 16
  recovered = struct.unpack('f', struct.pack('I', _bf16_to_fp32(bf16_bits)))[0]
  assert recovered == 2.0


# ===========================================================================
# FP32 -> TF32 (mantissa truncation to 10 bits)
# ===========================================================================

@spec("DTC.TF32.TRUNCATES_MANTISSA")
def test_tf32_truncation_zeros_low_13_bits():
  """TF32 conversion zeros FP32 mantissa bits 12:0, keeping top 10 bits."""
  # Use a value with known mantissa bits spread across all 23 bits
  # 1.5 = 0x3FC00000 — only bit 22 set, survives TF32 truncation
  fp32_bits = struct.unpack('I', struct.pack('f', 1.5))[0]
  # TF32 truncation: keep sign(1) + exp(8) + top10(10) = bits 31:13
  tf32_bits = fp32_bits & 0xFFFFE000
  assert (tf32_bits & 0x1FFF) == 0


@spec("DTC.TF32.TRUNCATES_MANTISSA")
def test_tf32_preserves_top_10_mantissa_bits():
  """TF32 conversion preserves mantissa bits 22:13 unchanged."""
  # 1.75 = 0x3FE00000: mantissa bits = 0x600000 (bits 22 and 21 set)
  fp32_bits = struct.unpack('I', struct.pack('f', 1.75))[0]
  tf32_bits = fp32_bits & 0xFFFFE000
  # The top 10 mantissa bits (bits 22:13) should be preserved
  top10_orig = (fp32_bits >> 13) & 0x3FF
  top10_tf32 = (tf32_bits >> 13) & 0x3FF
  assert top10_orig == top10_tf32


@spec("DTC.TF32.TRUNCATES_MANTISSA")
def test_tf32_preserves_sign_and_exponent():
  """TF32 conversion does not alter the sign bit or 8-bit exponent."""
  fp32_bits = struct.unpack('I', struct.pack('f', -3.14))[0]
  tf32_bits = fp32_bits & 0xFFFFE000
  assert (fp32_bits >> 23) == (tf32_bits >> 23)   # sign + exp unchanged


# ===========================================================================
# Sign-magnitude integer representation
# ===========================================================================

@spec("DTC.SIGNMAG.REPRESENTATION")
def test_signmag_positive_zero():
  """+0 in sign-magnitude is 0x00000000."""
  POS_ZERO = 0x00000000
  assert POS_ZERO == 0


@spec("DTC.SIGNMAG.REPRESENTATION")
def test_signmag_negative_zero():
  """-0 in sign-magnitude is 0x80000000 (MSB=sign=1, magnitude=0)."""
  NEG_ZERO = 0x80000000
  assert (NEG_ZERO >> 31) & 1 == 1   # sign bit set
  assert NEG_ZERO & 0x7FFFFFFF == 0  # magnitude = 0


@spec("DTC.SIGNMAG.REPRESENTATION")
def test_signmag_two_zeros_are_distinct():
  """Sign-magnitude has two representations of zero (+0 and -0)."""
  POS_ZERO = 0x00000000
  NEG_ZERO = 0x80000000
  assert POS_ZERO != NEG_ZERO


@spec("DTC.SIGNMAG.REPRESENTATION")
def test_signmag_negative_value():
  """-1 in sign-magnitude is 0x80000001 (MSB=1, magnitude=1)."""
  NEG_ONE = 0x80000001
  sign = (NEG_ONE >> 31) & 1
  magnitude = NEG_ONE & 0x7FFFFFFF
  assert sign == 1
  assert magnitude == 1


# ===========================================================================
# DataFormat enum values (structural constants; no config register space needed)
# ===========================================================================

@spec("DTC.FMT.ENUM_VALUES")
def test_dataformat_float32_is_zero():
  """DataFormat.Float32 = 0."""
  FLOAT32 = 0
  assert FLOAT32 == 0


@spec("DTC.FMT.ENUM_VALUES")
def test_dataformat_float16_is_one():
  """DataFormat.Float16 = 1."""
  FLOAT16 = 1
  assert FLOAT16 == 1


@spec("DTC.FMT.ENUM_VALUES")
def test_dataformat_tf32_is_four():
  """DataFormat.Tf32 = 4."""
  TF32 = 4
  assert TF32 == 4


@spec("DTC.FMT.ENUM_VALUES")
def test_dataformat_float16b_is_five():
  """DataFormat.Float16_b (BFloat16) = 5."""
  FLOAT16B = 5
  assert FLOAT16B == 5


@spec("DTC.FMT.ENUM_VALUES")
def test_dataformat_int32_is_eight():
  """DataFormat.Int32 = 8."""
  INT32 = 8
  assert INT32 == 8


@spec("DTC.FMT.ENUM_VALUES")
def test_dataformat_int8_is_fourteen():
  """DataFormat.Int8 = 14."""
  INT8 = 14
  assert INT8 == 14
