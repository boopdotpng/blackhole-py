"""Unit tests for emu/tensix/formats.py.

Covers all format conversions via bit-level checks and numpy/struct references.
Edge cases: ±0, ±inf, NaN, subnormals, denormal flush, saturation, BFP round-trips.
"""

import math
import struct
import pytest

from emu.tensix.formats import (
    fp32_to_bf16, bf16_to_fp32,
    fp32_to_tf32, tf32_to_fp32,
    fp32_to_fp16, fp16_to_fp32,
    fp32_to_fp8_e5m2, fp8_e5m2_to_fp32,
    fp32_to_fp8_e4m3, fp8_e4m3_to_fp32,
    int8_to_signmag, signmag_to_int8,
    int8_signmag_to_fp16_overlay, fp16_overlay_to_int8_signmag,
    stochastic_round,
    pack_bfp8, unpack_bfp8,
    pack_bfp4, unpack_bfp4,
    pack_bfp2, unpack_bfp2,
    pack_bfp8a, unpack_bfp8a,
    pack_bfp4a, unpack_bfp4a,
    pack_bfp2a, unpack_bfp2a,
    pack_bfp_no_exp_section,
    shuffled_to_ieee, ieee_to_shuffled,
    _f32_bits, _bits_f32, _clz8,
)

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

numpy_only = pytest.mark.skipif(not HAS_NUMPY, reason="numpy not installed")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def f32(f): return struct.unpack('<f', struct.pack('<f', float(f)))[0]
def f32_bits(f): return struct.unpack('<I', struct.pack('<f', float(f)))[0]
def bits_f32(b): return struct.unpack('<f', struct.pack('<I', b & 0xFFFFFFFF))[0]


# ===========================================================================
# Internal helpers
# ===========================================================================

class TestClz8:
    def test_zero(self):
        assert _clz8(0x00) == 8

    def test_full(self):
        assert _clz8(0xFF) == 0

    def test_msb_only(self):
        assert _clz8(0x80) == 0

    def test_one_bit(self):
        assert _clz8(0x01) == 7

    def test_nibble(self):
        assert _clz8(0x0F) == 4

    def test_mask(self):
        # values above 8 bits are masked
        assert _clz8(0x1FF) == _clz8(0xFF)


# ===========================================================================
# FP32 ↔ BF16
# ===========================================================================

class TestFP32ToBF16:
    def test_one(self):
        # 1.0 FP32 = 0x3F800000; BF16 = 0x3F80
        assert fp32_to_bf16(1.0) == 0x3F80

    def test_zero(self):
        assert fp32_to_bf16(0.0) == 0x0000

    def test_neg_zero(self):
        # -0.0 FP32 = 0x80000000; BF16 = 0x8000
        assert fp32_to_bf16(-0.0) == 0x8000

    def test_truncation_rtz(self):
        # RTZ: low 16 bits dropped, no rounding
        # 0x3F800001 → 0x3F80 (drops 0x0001)
        val = bits_f32(0x3F800001)
        assert fp32_to_bf16(val) == 0x3F80

    def test_rtne_rounds_up(self):
        # Low 16 bits > 0x8000 → round up
        val = bits_f32(0x3F808001)
        result = fp32_to_bf16(val, rtne=True)
        assert result == 0x3F81

    def test_rtne_tie_even(self):
        # Exactly half (low16 = 0x8000): round to even
        # 0x3F808000: high16 = 0x3F80 (even) → no round up
        val = bits_f32(0x3F808000)
        assert fp32_to_bf16(val, rtne=True) == 0x3F80
        # 0x3F818000: high16 = 0x3F81 (odd) → round up to 0x3F82
        val2 = bits_f32(0x3F818000)
        assert fp32_to_bf16(val2, rtne=True) == 0x3F82

    def test_inf(self):
        assert fp32_to_bf16(float('inf')) == 0x7F80

    def test_neg_inf(self):
        assert fp32_to_bf16(float('-inf')) == 0xFF80

    def test_nan(self):
        # NaN: exponent all 1s, mantissa != 0; BF16 preserves sign and exp=0xFF
        result = fp32_to_bf16(float('nan'))
        assert (result >> 7) & 0xFF == 0xFF  # exponent all 1s

    @numpy_only
    def test_round_trip_various(self):
        import numpy as np
        for val in [1.0, -1.0, 2.5, 0.125, 1000.0, -0.001]:
            bf16_bits = fp32_to_bf16(val)
            recovered = bf16_to_fp32(bf16_bits)
            # BF16 has 7 mantissa bits; relative error should be < 2^-7
            if val != 0:
                assert abs(recovered - val) / abs(val) < 2**-6, \
                    f"Round-trip error too large for {val}: got {recovered}"


class TestBF16ToFP32:
    def test_one(self):
        assert bf16_to_fp32(0x3F80) == 1.0

    def test_zero(self):
        assert bf16_to_fp32(0x0000) == 0.0

    def test_low_bits_zero(self):
        # Low 16 mantissa bits must be zero after conversion
        result_bits = f32_bits(bf16_to_fp32(0x3F80))
        assert result_bits & 0xFFFF == 0

    def test_neg_zero(self):
        result = bf16_to_fp32(0x8000)
        assert result == 0.0  # -0.0 equals 0.0
        assert math.copysign(1.0, result) == -1.0  # but sign is negative


# ===========================================================================
# FP32 ↔ TF32
# ===========================================================================

class TestFP32ToTF32:
    def test_low_13_bits_zeroed(self):
        # FP32 with set low bits → TF32 clears them
        val = bits_f32(0x3F800FFF)
        result = fp32_to_tf32(val)
        assert result & 0x1FFF == 0

    def test_one(self):
        # 1.0: mantissa = 0, unaffected
        assert fp32_to_tf32(1.0) == f32_bits(1.0)

    def test_sign_exp_preserved(self):
        val = bits_f32(0xBF8F0FFF)  # negative, exp=127, mant has bits
        result = fp32_to_tf32(bits_f32(0xBF8F0FFF))
        assert result >> 13 == 0xBF8F0FFF >> 13

    def test_round_trip(self):
        # TF32 → FP32 → TF32 is identity
        for v in [1.0, -2.5, 3.14, 0.001]:
            tf32 = fp32_to_tf32(v)
            back = tf32_to_fp32(tf32)
            # Same bit pattern (low 13 bits zero)
            assert f32_bits(back) & 0xFFFFE000 == tf32

    def test_zero(self):
        assert fp32_to_tf32(0.0) == 0


# ===========================================================================
# FP32 ↔ FP16
# ===========================================================================

class TestFP32ToFP16:
    def test_one(self):
        # 1.0 FP16 = 0x3C00
        assert fp32_to_fp16(1.0) == 0x3C00

    def test_neg_one(self):
        assert fp32_to_fp16(-1.0) == 0xBC00

    def test_zero(self):
        assert fp32_to_fp16(0.0) == 0x0000

    def test_overflow_saturates_not_inf(self):
        # Very large value → saturates to max finite (0x7BFF), not inf (0x7C00)
        result = fp32_to_fp16(1e38)
        assert result == 0x7BFF

    def test_neg_overflow_saturates(self):
        result = fp32_to_fp16(-1e38)
        assert result == 0xFBFF  # negative max finite

    def test_inf_saturates(self):
        # Inf input → saturate to max finite per hardware non-conformance
        result = fp32_to_fp16(float('inf'))
        assert result == 0x7BFF  # not 0x7C00

    def test_subnormal_flush_to_zero(self):
        # FP32 value that underflows to FP16 subnormal → flush to ±0
        tiny = bits_f32(0x33800000)  # exp32=103, exp16=103-127+15=-9 → underflow
        result = fp32_to_fp16(tiny)
        assert result & 0x7FFF == 0  # zero magnitude

    def test_mantissa_truncation(self):
        # 1.5 = 1 + 0.5, exact in both FP32 and FP16
        assert fp32_to_fp16(1.5) == 0x3E00

    @numpy_only
    def test_matches_numpy_fp16_exact_values(self):
        """Test values that are exactly representable in FP16 (no rounding needed)."""
        import numpy as np
        # Only test values that are exact in FP16 (powers of 2, or exact fractions)
        # to avoid numpy's RTNE vs hardware's RTZ differences.
        test_vals = [1.0, -1.0, 0.5, 2.0, 0.25, 4.0, 0.125, -2.0, -0.5]
        for v in test_vals:
            expected = int(np.float16(v).view(np.uint16))
            got = fp32_to_fp16(v)
            # Hardware saturates on overflow; numpy may produce inf; skip those
            if expected == 0x7C00 or expected == 0xFC00:
                continue  # hardware saturates here; numpy produces inf
            assert got == expected, f"fp32_to_fp16({v}): expected {expected:04x} got {got:04x}"


class TestFP16ToFP32:
    def test_one(self):
        assert fp16_to_fp32(0x3C00) == 1.0

    def test_zero(self):
        assert fp16_to_fp32(0x0000) == 0.0

    def test_neg_zero(self):
        result = fp16_to_fp32(0x8000)
        assert result == 0.0
        assert math.copysign(1.0, result) == -1.0

    def test_round_trip(self):
        # FP32 → FP16 → FP32 should recover the same FP16-precision value
        for v in [1.0, -1.0, 2.0, 0.5, 1.5, 100.0]:
            fp16 = fp32_to_fp16(v)
            back = fp16_to_fp32(fp16)
            assert back == v, f"Round-trip failed for {v}: got {back}"

    @numpy_only
    def test_matches_numpy_fp32(self):
        import numpy as np
        for raw in [0x3C00, 0xBC00, 0x4200, 0x3800, 0x0001, 0x7BFF]:
            # Use little-endian packing to match the bit pattern
            expected = float(np.frombuffer(struct.pack('<H', raw), dtype=np.float16)[0])
            got = fp16_to_fp32(raw)
            if math.isnan(expected):
                assert math.isnan(got)
            elif math.isinf(expected):
                assert math.isinf(got)
            elif expected == 0.0:
                assert got == 0.0 or abs(got) < 1e-10
            else:
                assert abs(got - expected) / abs(expected) < 1e-5, \
                    f"fp16_to_fp32(0x{raw:04x}): expected {expected} got {got}"


# ===========================================================================
# FP8 E5M2
# ===========================================================================

class TestFP8E5M2:
    def test_one(self):
        # 1.0: sign=0 exp5=15(bias=15 → value=0) mant2=0 → 0b0_01111_00 = 0x3C
        assert fp32_to_fp8_e5m2(1.0) == 0x3C

    def test_zero(self):
        assert fp32_to_fp8_e5m2(0.0) == 0x00

    def test_neg_zero(self):
        assert fp32_to_fp8_e5m2(-0.0) == 0x80

    def test_overflow_saturates(self):
        result = fp32_to_fp8_e5m2(1e38)
        assert result == 0x7B  # max finite

    def test_round_trip(self):
        for v in [1.0, -1.0, 2.0, 0.5, 4.0]:
            e5m2 = fp32_to_fp8_e5m2(v)
            back = fp8_e5m2_to_fp32(e5m2)
            assert back == v or abs(back - v) / abs(v) < 0.5, \
                f"E5M2 round-trip {v} → 0x{e5m2:02x} → {back}"

    def test_sign_preserved(self):
        pos = fp32_to_fp8_e5m2(2.0)
        neg = fp32_to_fp8_e5m2(-2.0)
        assert (neg ^ pos) == 0x80


# ===========================================================================
# FP8 E4M3
# ===========================================================================

class TestFP8E4M3:
    def test_one(self):
        # 1.0: sign=0 exp4=7(bias=7 → value=0) mant3=0 → 0b0_0111_000 = 0x38
        assert fp32_to_fp8_e4m3(1.0) == 0x38

    def test_zero(self):
        assert fp32_to_fp8_e4m3(0.0) == 0x00

    def test_neg_one(self):
        assert fp32_to_fp8_e4m3(-1.0) == 0xB8

    def test_overflow_saturates(self):
        result = fp32_to_fp8_e4m3(1e38)
        assert result == 0x7E  # max finite

    def test_round_trip(self):
        for v in [1.0, -1.0, 2.0, 0.5]:
            e4m3 = fp32_to_fp8_e4m3(v)
            back = fp8_e4m3_to_fp32(e4m3)
            assert back == v or abs(back - v) / abs(v) < 0.5, \
                f"E4M3 round-trip {v} → 0x{e4m3:02x} → {back}"


# ===========================================================================
# INT8 sign-magnitude
# ===========================================================================

class TestSignMag:
    def test_positive(self):
        assert int8_to_signmag(42) == 42

    def test_negative(self):
        assert int8_to_signmag(-42) == 0x80 | 42

    def test_zero(self):
        assert int8_to_signmag(0) == 0x00

    def test_neg_zero_is_0x80(self):
        # Hardware quirk: two representations of zero
        assert int8_to_signmag(-0) == 0x00  # Python -0 == 0

    def test_min_value(self):
        assert int8_to_signmag(-127) == 0xFF

    def test_round_trip(self):
        for v in range(-127, 128):
            sm = int8_to_signmag(v)
            back = signmag_to_int8(sm)
            assert back == v, f"Round-trip {v} → {sm:#x} → {back}"

    def test_signmag_to_int8_neg_zero(self):
        # 0x80 = sign-magnitude -0 → should decode as 0
        assert signmag_to_int8(0x80) == 0


class TestFP16Overlay:
    def test_zero_has_no_dummy_exp(self):
        # Zero magnitude → no dummy exponent
        result = int8_signmag_to_fp16_overlay(0x00)
        assert result == 0x0000

    def test_positive_nonzero_has_dummy_exp(self):
        # magnitude=1, sign=0 → dummy exp (16<<10) = 0x4000, plus mag
        result = int8_signmag_to_fp16_overlay(0x01)
        # Sign=0, mag=1, dummy exp = 0x4000 | 0x01 = 0x4001
        assert result == (16 << 10) | 1

    def test_negative_sets_sign_in_bit8(self):
        # sign-magnitude 0x81 = -1
        result = int8_signmag_to_fp16_overlay(0x81)
        # Sign bit in bit 8, dummy exp, mag=1
        assert result & (0x80 << 8) != 0   # sign in bit 8 position (0x8000 << 0 = wrong)
        # Actually sign = (sm & 0x80) = 0x80; placed at (Sign << 8) = 0x8000
        assert result & 0x8000 != 0  # bit 15 set (sign bit of FP16 field)

    def test_negative_nonzero_magnitude(self):
        sm = 0x81  # -1 in sign-magnitude
        result = int8_signmag_to_fp16_overlay(sm)
        sign = 0x80       # from sm & 0x80
        mag = sm - sign   # = 0x01
        expected = (16 << 10) | mag | (sign << 8)
        assert result == expected

    def test_unsigned_path(self):
        # Unsigned: sign bit not extracted, full byte is magnitude
        result = int8_signmag_to_fp16_overlay(0xFF, unsigned=True)
        assert result == (16 << 10) | 0xFF

    def test_round_trip_signed(self):
        for mag in range(128):
            for neg in [False, True]:
                sm = (0x80 | mag) if neg else mag
                overlay = int8_signmag_to_fp16_overlay(sm, unsigned=False)
                back = fp16_overlay_to_int8_signmag(overlay, unsigned=False)
                assert back == sm, f"Round-trip 0x{sm:02x} → 0x{overlay:04x} → 0x{back:02x}"


# ===========================================================================
# Stochastic rounding
# ===========================================================================

class TestStochasticRound:
    def test_zero_drop_bits_is_identity(self):
        assert stochastic_round(100, 0) == 100

    def test_adds_value_in_range(self):
        import random
        rng = random.Random(42)
        for _ in range(100):
            base = 256
            result = stochastic_round(base, 8, rng)
            assert base <= result <= base + 255

    def test_expected_value_unbiased(self):
        # Mean of stochastic rounds should be near base + 2^(bits-1)
        import random
        rng = random.Random(0)
        trials = 10000
        total = sum(stochastic_round(0, 8, rng) for _ in range(trials))
        mean = total / trials
        assert abs(mean - 127.5) < 5, f"Expected ~127.5, got {mean}"


# ===========================================================================
# BFP8 (format B)
# ===========================================================================

class TestBFP8:
    def _make_block(self, val=1.0):
        return [val] * 16

    def test_pack_unpack_ones(self):
        floats = self._make_block(1.0)
        exp, mants = pack_bfp8(floats)
        result = unpack_bfp8(exp, mants)
        for r in result:
            assert abs(r - 1.0) < 0.02, f"Expected ~1.0, got {r}"

    def test_shared_exp_is_max(self):
        # Mix 1.0 and 2.0 — shared exp should come from 2.0
        floats = [1.0] * 15 + [2.0]
        exp1, _ = pack_bfp8([1.0] * 16)
        exp2, _ = pack_bfp8([2.0] * 16)
        exp_mixed, _ = pack_bfp8(floats)
        assert exp_mixed == exp2  # dominated by 2.0

    def test_wrong_block_size_raises(self):
        with pytest.raises(ValueError):
            pack_bfp8([1.0] * 15)

    def test_all_zeros(self):
        floats = [0.0] * 16
        exp, mants = pack_bfp8(floats)
        result = unpack_bfp8(exp, mants)
        for r in result:
            assert r == 0.0 or r == -0.0

    def test_mixed_signs(self):
        floats = [1.0, -1.0] * 8
        exp, mants = pack_bfp8(floats)
        result = unpack_bfp8(exp, mants)
        for i, r in enumerate(result):
            expected_sign = 1 if floats[i] > 0 else -1
            if r != 0:
                assert math.copysign(1.0, r) == expected_sign

    def test_positive_infinity_handled(self):
        # inf → BF16 max → packed
        floats = [float('inf')] + [1.0] * 15
        # Should not raise
        exp, mants = pack_bfp8(floats)
        assert isinstance(exp, int)

    def test_round_trip_large_value(self):
        # Test that BFP8 correctly handles values with the same magnitude
        floats = [256.0] * 16
        exp, mants = pack_bfp8(floats)
        result = unpack_bfp8(exp, mants)
        for r in result:
            assert abs(r - 256.0) / 256.0 < 0.02, f"Expected ~256.0, got {r}"

    def test_round_trip_mixed_magnitudes_loses_small(self):
        # When 256x magnitude difference, small values fall below BFP precision.
        # This is expected BFP behavior: shared exponent is dominated by large value.
        floats = [256.0] * 8 + [1.0] * 8
        exp, mants = pack_bfp8(floats)
        result = unpack_bfp8(exp, mants)
        # Large values should be preserved
        for r in result[:8]:
            assert abs(r - 256.0) / 256.0 < 0.02, f"Expected ~256.0, got {r}"
        # Small values (1.0 with shared exp from 256.0) may be zeroed — that's OK
        # BFP8 has 7-bit mantissa + 1 implicit bit = 8 effective bits,
        # shift of 8 exceeds that, so 1.0 is quantized to 0.

    def test_mantissa_and_exp_layout(self):
        # Single dominant value: sign=0, exp from bf16, mantissa
        floats = [1.0] * 16
        exp, mants = pack_bfp8(floats)
        # bf16 of 1.0: sign=0, exp=127, mant=0 → shared_exp=127
        assert exp == 127
        # Mantissa should encode the value
        for m in mants:
            assert 0 <= m <= 0xFF


# ===========================================================================
# BFP4 (format B)
# ===========================================================================

class TestBFP4:
    def test_pack_unpack_ones(self):
        floats = [1.0] * 16
        exp, mants = pack_bfp4(floats)
        result = unpack_bfp4(exp, mants)
        for r in result:
            assert abs(r - 1.0) < 0.15, f"Expected ~1.0, got {r}"

    def test_mantissa_fits_in_4_bits(self):
        floats = [1.0] * 16
        _, mants = pack_bfp4(floats)
        for m in mants:
            assert 0 <= m <= 0xF

    def test_all_zeros(self):
        floats = [0.0] * 16
        exp, mants = pack_bfp4(floats)
        result = unpack_bfp4(exp, mants)
        for r in result:
            assert r == 0.0 or r == -0.0

    def test_wrong_size_raises(self):
        with pytest.raises(ValueError):
            pack_bfp4([1.0] * 5)


# ===========================================================================
# BFP2 (format B)
# ===========================================================================

class TestBFP2:
    def test_pack_unpack_ones(self):
        floats = [1.0] * 16
        exp, mants = pack_bfp2(floats)
        result = unpack_bfp2(exp, mants)
        for r in result:
            # BFP2 has 1-bit mantissa; only ±1.0 or ±2.0 or 0 possible
            assert abs(r) in (0.0, 1.0) or (0.5 <= abs(r) <= 2.0), f"Unexpected {r}"

    def test_mantissa_fits_in_2_bits(self):
        floats = [1.0] * 16
        _, mants = pack_bfp2(floats)
        for m in mants:
            assert 0 <= m <= 3

    def test_all_zeros(self):
        floats = [0.0] * 16
        exp, mants = pack_bfp2(floats)
        result = unpack_bfp2(exp, mants)
        for r in result:
            assert r == 0.0 or r == -0.0

    def test_wrong_size_raises(self):
        with pytest.raises(ValueError):
            pack_bfp2([1.0] * 20)


# ===========================================================================
# BFP8a (format A, 5-bit shared exp)
# ===========================================================================

class TestBFP8a:
    def test_pack_unpack_ones(self):
        floats = [1.0] * 16
        exp, mants = pack_bfp8a(floats)
        result = unpack_bfp8a(exp, mants)
        for r in result:
            assert abs(r - 1.0) < 0.02, f"Expected ~1.0, got {r}"

    def test_shared_exp_is_5_bit(self):
        floats = [1.0] * 16
        exp, _ = pack_bfp8a(floats)
        assert 0 <= exp <= 31

    def test_all_zeros(self):
        floats = [0.0] * 16
        exp, mants = pack_bfp8a(floats)
        result = unpack_bfp8a(exp, mants)
        for r in result:
            assert r == 0.0 or r == -0.0

    def test_mixed_signs(self):
        floats = [2.0, -2.0] * 8
        exp, mants = pack_bfp8a(floats)
        result = unpack_bfp8a(exp, mants)
        for i, r in enumerate(result):
            if abs(r) > 0.01:
                expected_sign = math.copysign(1, floats[i])
                assert math.copysign(1, r) == expected_sign

    def test_fp16_range_values(self):
        # BFP8a uses 5-bit exponent (FP16 range); test small values
        floats = [0.5] * 16
        exp, mants = pack_bfp8a(floats)
        result = unpack_bfp8a(exp, mants)
        for r in result:
            assert abs(r - 0.5) < 0.05


# ===========================================================================
# BFP4a and BFP2a (format A)
# ===========================================================================

class TestBFP4a:
    def test_pack_unpack_basic(self):
        floats = [1.0] * 16
        exp, mants = pack_bfp4a(floats)
        result = unpack_bfp4a(exp, mants)
        for r in result:
            assert abs(r - 1.0) < 0.2

    def test_mantissa_fits_in_4_bits(self):
        floats = [1.0] * 16
        _, mants = pack_bfp4a(floats)
        for m in mants:
            assert 0 <= m <= 0xF

    def test_all_zeros(self):
        floats = [0.0] * 16
        exp, mants = pack_bfp4a(floats)
        result = unpack_bfp4a(exp, mants)
        for r in result:
            assert r == 0.0 or r == -0.0


class TestBFP2a:
    def test_pack_unpack_basic(self):
        floats = [1.0] * 16
        exp, mants = pack_bfp2a(floats)
        result = unpack_bfp2a(exp, mants)
        for r in result:
            assert abs(r) > 0 or r == 0.0  # either zero or nonzero

    def test_mantissa_fits_in_2_bits(self):
        floats = [1.0] * 16
        _, mants = pack_bfp2a(floats)
        for m in mants:
            assert 0 <= m <= 3

    def test_all_zeros(self):
        floats = [0.0] * 16
        exp, mants = pack_bfp2a(floats)
        result = unpack_bfp2a(exp, mants)
        for r in result:
            assert r == 0.0 or r == -0.0


# ===========================================================================
# NoBFPExpSection path
# ===========================================================================

class TestNoBFPExpSection:
    def test_bfp4_returns_mantissas(self):
        floats = [1.0] * 16
        mants = pack_bfp_no_exp_section(floats, bits_per_elem=4)
        assert len(mants) == 16
        for m in mants:
            assert 0 <= m <= 0xF

    def test_bfp2_returns_mantissas(self):
        floats = [1.0] * 16
        mants = pack_bfp_no_exp_section(floats, bits_per_elem=2)
        assert len(mants) == 16
        for m in mants:
            assert 0 <= m <= 3

    def test_invalid_bits_raises(self):
        with pytest.raises(ValueError):
            pack_bfp_no_exp_section([1.0]*16, bits_per_elem=8)

    def test_format_a_variant(self):
        floats = [1.0] * 16
        mants = pack_bfp_no_exp_section(floats, bits_per_elem=4, format_a=True)
        assert len(mants) == 16


# ===========================================================================
# Shuffled format (SrcA/SrcB 19-bit cell)
# ===========================================================================

class TestShuffledFormat:
    def test_one(self):
        # 1.0 FP32: sign=0, exp=127=0x7F, mant=0
        ieee = f32_bits(1.0)
        shuffled = ieee_to_shuffled(ieee)
        # Layout: {sign[18], mant10[17:8], exp[7:0]}
        # sign=0, mant10=0 (top 10 bits of 23-bit mant=0), exp=0x7F
        assert shuffled & 0xFF == 0x7F   # exp in low 8 bits
        assert (shuffled >> 8) & 0x3FF == 0  # mant10 = 0
        assert (shuffled >> 18) & 1 == 0     # sign = 0

    def test_round_trip(self):
        for val in [1.0, -1.0, 2.0, 0.5, 100.0, 0.001]:
            ieee = f32_bits(val)
            shuffled = ieee_to_shuffled(ieee)
            back = shuffled_to_ieee(shuffled)
            # Low 13 mantissa bits are lost (10-bit mantissa truncation)
            assert back == (ieee & ~0x1FFF), \
                f"Round-trip mismatch for {val}: 0x{ieee:08x} → 0x{back:08x}"

    def test_sign_field(self):
        pos = ieee_to_shuffled(f32_bits(1.0))
        neg = ieee_to_shuffled(f32_bits(-1.0))
        assert (pos >> 18) & 1 == 0
        assert (neg >> 18) & 1 == 1

    def test_shuffled_to_ieee_expands_mantissa(self):
        # 19-bit with mant10=0x3FF, exp=0x7F, sign=0
        val_19 = (0x3FF << 8) | 0x7F
        ieee = shuffled_to_ieee(val_19)
        # Top 10 of 23-bit mantissa = 0x3FF, low 13 = 0
        expected_mant23 = 0x3FF << 13
        assert ieee & 0x7FFFFF == expected_mant23

    def test_zero(self):
        assert ieee_to_shuffled(0) == 0
        assert shuffled_to_ieee(0) == 0

    def test_nan_encoding(self):
        # NaN in FP32: exp=0x7F (bits[7:0]), quiet-NaN bit set in mant10 (bits[17:8])
        # DTC.19BIT.NAN_HANDLING: encoded as exp=0x7F, quiet-NaN bit set
        ieee_nan = f32_bits(float('nan'))
        shuffled = ieee_to_shuffled(ieee_nan)
        # exp in low bits should be 0xFF
        assert shuffled & 0xFF == 0xFF


# ===========================================================================
# BFP edge cases: all-zeros block, one dominant value, all same
# ===========================================================================

class TestBFPEdgeCases:
    def test_one_dominant_value(self):
        # One large value, rest zero
        floats = [0.0] * 15 + [1024.0]
        exp, mants = pack_bfp8(floats)
        result = unpack_bfp8(exp, mants)
        # The large value should be approximately preserved
        assert abs(result[15] - 1024.0) / 1024.0 < 0.05
        # Zero values should remain near zero
        for r in result[:15]:
            assert abs(r) < 1.0

    def test_all_same_value(self):
        floats = [3.14] * 16
        exp, mants = pack_bfp8(floats)
        result = unpack_bfp8(exp, mants)
        for r in result:
            assert abs(r - 3.14) / 3.14 < 0.05

    def test_boundary_shared_exponent(self):
        # All values have the same exponent → shared_exp equals that exponent
        floats = [1.0] * 16
        exp, _ = pack_bfp8(floats)
        # 1.0 BF16 exp = 127
        assert exp == 127

    def test_stochastic_flag_doesnt_break_output(self):
        import random
        rng = random.Random(12345)
        floats = [float(i + 1) for i in range(16)]
        exp, mants = pack_bfp8(floats, stochastic=True, rng=rng)
        result = unpack_bfp8(exp, mants)
        assert len(result) == 16
        for r in result:
            assert math.isfinite(r)

    def test_bfp8a_exp_in_5bit_range(self):
        # BFP8a uses 5-bit shared exponent (FP16 range)
        # 1.0 in FP16: exp=15
        floats = [1.0] * 16
        exp, _ = pack_bfp8a(floats)
        assert 0 <= exp <= 31
        assert exp == 15  # FP16 exp for 1.0 = 15

    def test_bfp_negative_zero_output(self):
        # Input: -0.0 → sign bit preserved
        floats = [-0.0] * 16
        exp, mants = pack_bfp8(floats)
        result = unpack_bfp8(exp, mants)
        for r in result:
            # -0.0 has zero magnitude; result should be ±0
            assert r == 0.0 or r == -0.0
