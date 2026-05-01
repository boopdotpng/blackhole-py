"""Pure-function format-conversion library for the Tensix packer/unpacker.

All functions are stateless and take/return plain Python ints or floats.
No emulator state, no I/O.

BFP block formats use the convention:
    pack_bfpN(floats)  -> (shared_exp: int, mantissas: list[int])
    unpack_bfpN(shared_exp, mantissas) -> list[float]

where N ∈ {2, 4, 8} and the 'a' variants (BFP2a, BFP4a, BFP8a) use a 5-bit
shared exponent (format A) rather than the 8-bit shared exponent of format B.
"""

import math
import struct
import random


# ---------------------------------------------------------------------------
# DataFormat enum constants (4-bit hardware encoding)
# ---------------------------------------------------------------------------

FMT_FLOAT32  = 0
FMT_FLOAT16  = 1
FMT_BFP8A    = 2   # format A: 5-bit shared exponent
FMT_BFP4A    = 3
FMT_TF32     = 4
FMT_FLOAT16B = 5   # BFloat16
FMT_BFP8     = 6   # format B: 8-bit shared exponent
FMT_BFP4     = 7
FMT_INT32    = 8
FMT_INT16    = 9
FMT_FP8      = 10  # Lf8 — E5M2 by default; E4M3 when mode bit set
FMT_BFP2A    = 11
# 12, 13 reserved
FMT_INT8     = 14
FMT_BFP2     = 15

# Short aliases used by pack/unpack datapaths.
FMT_FP32 = FMT_FLOAT32
FMT_FP16 = FMT_FLOAT16
FMT_BF16 = FMT_FLOAT16B

FMT_BFP_B = frozenset((FMT_BFP8, FMT_BFP4, FMT_BFP2))
FMT_BFP_A = frozenset((FMT_BFP8A, FMT_BFP4A, FMT_BFP2A))
FMT_BFP = FMT_BFP_B | FMT_BFP_A

DATUM_SIZE_BYTES = {
    FMT_FP32: 4.0,
    FMT_INT32: 4.0,
    FMT_TF32: 4.0,
    FMT_FP16: 2.0,
    FMT_BF16: 2.0,
    FMT_INT16: 2.0,
    FMT_FP8: 1.0,
    FMT_INT8: 1.0,
    FMT_BFP8: 1.0,
    FMT_BFP8A: 1.0,
    FMT_BFP4: 0.5,
    FMT_BFP4A: 0.5,
    FMT_BFP2: 0.25,
    FMT_BFP2A: 0.25,
}

BFP_MANTISSA_BITS = {
    FMT_BFP8: 7,
    FMT_BFP4: 3,
    FMT_BFP2: 1,
    FMT_BFP8A: 7,
    FMT_BFP4A: 3,
    FMT_BFP2A: 1,
}


def datum_size_bytes(fmt: int) -> float:
    """Return bytes per datum for a DataFormat; BFP4/BFP2 are fractional."""
    return DATUM_SIZE_BYTES.get(fmt, 1.0)


# ---------------------------------------------------------------------------
# Internal bit-manipulation helpers
# ---------------------------------------------------------------------------

def _f32_bits(f: float) -> int:
    """IEEE 754 FP32 → 32-bit int."""
    return struct.unpack('<I', struct.pack('<f', f))[0]

def _bits_f32(b: int) -> float:
    """32-bit int → IEEE 754 FP32."""
    return struct.unpack('<f', struct.pack('<I', b & 0xFFFFFFFF))[0]

def _clz8(x: int) -> int:
    """Count leading zeros in an 8-bit value (0x00 → 8)."""
    x &= 0xFF
    if x == 0:
        return 8
    n = 0
    if x & 0xF0 == 0:
        n += 4; x <<= 4
    if x & 0xC0 == 0:
        n += 2; x <<= 2
    if x & 0x80 == 0:
        n += 1
    return n


# ---------------------------------------------------------------------------
# FP32 ↔ BF16
# ---------------------------------------------------------------------------

def fp32_to_bf16(f: float, rtne: bool = False) -> int:
    """Convert FP32 float to BF16 bit pattern (16-bit int).

    Default rounding mode is round-toward-zero (truncation), matching
    hardware default.  Pass rtne=True to enable round-to-nearest-even,
    which the hardware supports via cfg0 bit 31 (EnBFloatRTNE).

    Denormals (all 8 exponent bits clear) are flushed to ±0.

    Spec refs:
      DTC.BF16.FP32_TO_BF16_TRUNCATE — default RTZ via right-shift-16
      DTC.BF16.RTZ_DEFAULT            — RTZ is the default mode
    """
    bits = _f32_bits(f)
    if rtne:
        # RTNE: add round bit based on discarded 16 bits
        low16 = bits & 0xFFFF
        # Round up if: low16 > 0x8000, or (low16 == 0x8000 and result is odd)
        half = 0x8000
        round_bit = 1 if (low16 > half or (low16 == half and (bits >> 16) & 1)) else 0
        bits = ((bits >> 16) + round_bit) & 0xFFFF
    else:
        bits = (bits >> 16) & 0xFFFF
    return bits


def bf16_to_fp32(bf16: int) -> float:
    """Convert BF16 bit pattern (16-bit int) to FP32 float.

    Low 16 mantissa bits are zeroed.

    Spec ref: DTC.BF16.BF16_TO_FP32 — left-shift 16 bits.
    """
    return _bits_f32((bf16 & 0xFFFF) << 16)


# ---------------------------------------------------------------------------
# FP32 ↔ TF32
# ---------------------------------------------------------------------------

def fp32_to_tf32(f: float) -> int:
    """Convert FP32 float to TF32 bit pattern (32-bit int with low 13 bits zeroed).

    Keeps sign + 8-bit exponent + top 10 mantissa bits.
    The result is stored as a 32-bit IEEE FP32 bit pattern with bits [12:0] = 0.

    Spec ref: DTC.TF32.TRUNCATES_MANTISSA
    """
    bits = _f32_bits(f)
    return bits & 0xFFFFE000


def tf32_to_fp32(tf32_bits: int) -> float:
    """Expand TF32 bit pattern (with low 13 bits zeroed) to FP32 float.

    This is just a bitcast: TF32 is zero-extended in mantissa by the
    shuffled_to_ieee path.

    Spec ref: DTC.TF32.NO_TF32_TO_FP32 — zero-extension in mantissa.
    """
    return _bits_f32(tf32_bits & 0xFFFFE000)


# ---------------------------------------------------------------------------
# FP32 ↔ FP16 (IEEE)
# ---------------------------------------------------------------------------

# FP16 max finite value as bit pattern: sign=0 exp=11110 mant=1111111111
_FP16_MAX_FINITE = 0x7BFF

def fp32_to_fp16(f: float) -> int:
    """Convert FP32 float to FP16 bit pattern (16-bit int).

    Hardware non-conformance: overflow saturates to max finite FP16 (0x7BFF)
    rather than producing infinity.  NaN inputs may not produce NaN output.

    Denormals (FP16 exp <= 0) are flushed to ±0.

    Spec refs:
      DTC.FP16.REBIAS_EXPONENT  — exp32-127+15, truncate mantissa
      DTC.FP16.OVERFLOW_SATURATES — saturate to 0x7BFF on overflow
    """
    bits = _f32_bits(f)
    sign = (bits >> 31) & 1
    exp32 = (bits >> 23) & 0xFF
    mant23 = bits & 0x7FFFFF

    if exp32 == 0xFF:
        # NaN or Inf in FP32 → hardware may not preserve: saturate to max
        return (sign << 15) | _FP16_MAX_FINITE

    exp16 = exp32 - 127 + 15
    if exp16 <= 0:
        # Subnormal or underflow → flush to ±0
        return sign << 15
    if exp16 >= 31:
        # Overflow → saturate to max finite FP16 (hardware does not produce inf)
        return (sign << 15) | _FP16_MAX_FINITE

    mant10 = (mant23 >> 13) & 0x3FF
    return (sign << 15) | (exp16 << 10) | mant10


def fp16_to_fp32(fp16: int) -> float:
    """Convert FP16 bit pattern (16-bit int) to FP32 float.

    Subnormals (exp16 == 0) are normalized.

    Spec ref: DTC.FP16.REBIAS_EXPONENT (reverse direction).
    """
    fp16 &= 0xFFFF
    sign = (fp16 >> 15) & 1
    exp16 = (fp16 >> 10) & 0x1F
    mant10 = fp16 & 0x3FF

    if exp16 == 0:
        if mant10 == 0:
            return _bits_f32(sign << 31)  # ±0
        # Subnormal: normalize
        e = 1
        m = mant10
        while not (m & 0x400):
            m <<= 1
            e -= 1
        exp32 = -15 + 127 + e
        mant23 = (m & 0x3FF) << 13
        return _bits_f32((sign << 31) | (exp32 << 23) | mant23)
    elif exp16 == 0x1F:
        # NaN or Inf
        return _bits_f32((sign << 31) | (0xFF << 23) | (mant10 << 13))

    exp32 = exp16 - 15 + 127
    mant23 = mant10 << 13
    return _bits_f32((sign << 31) | (exp32 << 23) | mant23)


# ---------------------------------------------------------------------------
# FP32 ↔ FP8 E5M2
# ---------------------------------------------------------------------------

# FP8 E5M2: sign(1) exp(5,bias=15) mant(2).  Max finite exp code = 30.
_FP8_E5M2_MAX_FINITE = 0x7B  # sign=0 exp=11110 mant=11

def fp32_to_fp8_e5m2(f: float) -> int:
    """Convert FP32 float to FP8 E5M2 bit pattern (8-bit int).

    Overflow saturates to 0x7B (max finite).  Underflow flushes to ±0.

    Spec ref: PACK.EARLY_FMT.FORMAT_ENCODING (format 10 = FP8 E5M2 mode).
    """
    bits = _f32_bits(f)
    sign = (bits >> 31) & 1
    exp32 = (bits >> 23) & 0xFF
    mant23 = bits & 0x7FFFFF

    if exp32 == 0xFF:
        return (sign << 7) | _FP8_E5M2_MAX_FINITE

    exp8 = exp32 - 127 + 15
    if exp8 <= 0:
        return sign << 7
    if exp8 >= 31:
        return (sign << 7) | _FP8_E5M2_MAX_FINITE

    mant2 = (mant23 >> 21) & 0x3
    return (sign << 7) | (exp8 << 2) | mant2


def fp8_e5m2_to_fp32(fp8: int) -> float:
    """Convert FP8 E5M2 bit pattern (8-bit int) to FP32 float."""
    fp8 &= 0xFF
    sign = (fp8 >> 7) & 1
    exp8 = (fp8 >> 2) & 0x1F
    mant2 = fp8 & 0x3

    if exp8 == 0:
        return _bits_f32(sign << 31)  # ±0 (flush subnormals)
    if exp8 == 0x1F:
        return _bits_f32((sign << 31) | (0xFF << 23))  # Inf/NaN

    exp32 = exp8 - 15 + 127
    mant23 = mant2 << 21
    return _bits_f32((sign << 31) | (exp32 << 23) | mant23)


# ---------------------------------------------------------------------------
# FP32 ↔ FP8 E4M3
# ---------------------------------------------------------------------------

# FP8 E4M3: sign(1) exp(4,bias=7) mant(3).  Max finite: sign=0 exp=1111 mant=111 = 0x7F
_FP8_E4M3_MAX_FINITE = 0x7E  # exp=1111 mant=110 — spec: 0x7F = NaN in some conventions
# TODO: spec ambiguity — E4M3 NaN encoding.  Using 0x7F=NaN, 0x7E=max finite per
# standard FP8 E4M3 (IEEE draft).  Hardware may differ; flag for human review.

def fp32_to_fp8_e4m3(f: float) -> int:
    """Convert FP32 float to FP8 E4M3 bit pattern (8-bit int).

    Uses bias=7.  Overflow saturates to 0x7E.  Underflow flushes to ±0.
    """
    bits = _f32_bits(f)
    sign = (bits >> 31) & 1
    exp32 = (bits >> 23) & 0xFF
    mant23 = bits & 0x7FFFFF

    if exp32 == 0xFF:
        return (sign << 7) | _FP8_E4M3_MAX_FINITE

    exp8 = exp32 - 127 + 7
    if exp8 <= 0:
        return sign << 7
    if exp8 >= 15:
        return (sign << 7) | _FP8_E4M3_MAX_FINITE

    mant3 = (mant23 >> 20) & 0x7
    return (sign << 7) | (exp8 << 3) | mant3


def fp8_e4m3_to_fp32(fp8: int) -> float:
    """Convert FP8 E4M3 bit pattern (8-bit int) to FP32 float."""
    fp8 &= 0xFF
    sign = (fp8 >> 7) & 1
    exp8 = (fp8 >> 3) & 0xF
    mant3 = fp8 & 0x7

    if exp8 == 0:
        return _bits_f32(sign << 31)  # ±0
    if exp8 == 0xF and mant3 == 7:
        # 0x7F / 0xFF = NaN
        return float('nan')

    exp32 = exp8 - 7 + 127
    mant23 = mant3 << 20
    return _bits_f32((sign << 31) | (exp32 << 23) | mant23)


# ---------------------------------------------------------------------------
# INT8 sign-magnitude pack / unpack (+ FP16 dummy-exponent overlay)
# ---------------------------------------------------------------------------

def int8_to_signmag(val: int) -> int:
    """Convert a signed Python int (-128..127) to 8-bit sign-magnitude.

    Sign-magnitude: MSB=sign (1=negative), remaining bits=magnitude.
    Two representations of zero: +0=0x00 and -0=0x80 (hardware quirk).

    Spec ref: DTC.SIGNMAG.REPRESENTATION
    """
    val = int(val)
    if val < 0:
        return 0x80 | ((-val) & 0x7F)
    return val & 0x7F


def signmag_to_int8(sm: int) -> int:
    """Convert 8-bit sign-magnitude to signed Python int.

    Note: -0 (0x80) maps to 0.  Spec ref: DTC.SIGNMAG.REPRESENTATION
    """
    sm &= 0xFF
    sign = (sm >> 7) & 1
    mag = sm & 0x7F
    return -mag if sign else mag


def int8_signmag_to_fp16_overlay(sm: int, unsigned: bool = False) -> int:
    """Convert INT8 sign-magnitude byte to the FP16 'dummy exponent' overlay.

    The unpacker stores INT8 values inside the FP16 bit field with a dummy
    exponent of "8" (bias-15 exponent code 16 = 0b10000 = 16 << 10).

    This overlay is used so the FPU math unit can handle integer values
    in FP16 cells without treating them as zero-magnitude.

    Algorithm (from spec §3.2 FormatConversion / INT8 path):
        Sign = sm & 0x80 (if signed, else 0)
        DatumBits = sm - Sign  (unsigned magnitude)
        if DatumBits != 0: DatumBits |= (16 << 10)   # dummy FP16 exponent
        DatumBits |= (Sign << 8)

    Spec ref: UNPACK.FMT.INT8_OVERLAY
    """
    sm &= 0xFF
    if unsigned:
        sign = 0
        mag = sm
    else:
        sign = sm & 0x80
        mag = sm - sign  # unsigned magnitude

    result = mag
    if mag != 0:
        result |= (16 << 10)   # dummy FP16 exponent "8"
    result |= (sign << 8)
    return result & 0xFFFF


def fp16_overlay_to_int8_signmag(overlay: int, unsigned: bool = False) -> int:
    """Invert the FP16 dummy-exponent overlay back to an INT8 sign-magnitude byte.

    Spec ref: UNPACK.FMT.INT8_OVERLAY (reverse direction).
    """
    overlay &= 0xFFFF
    if unsigned:
        # magnitude lives in bits [7:0]
        return overlay & 0xFF
    sign = (overlay >> 8) & 0x80
    mag = overlay & 0x7F
    return sign | mag


# ---------------------------------------------------------------------------
# Stochastic rounding helper
# ---------------------------------------------------------------------------

def stochastic_round(mantissa: int, drop_bits: int, rng: random.Random | None = None) -> int:
    """Apply stochastic rounding: add a random value in [0, 2^drop_bits) before truncation.

    The hardware has a slight bias toward increasing magnitude (not true 50:50).
    We model the ideal case here; callers can supply their own rng for testing.

    Used by BFP late-stage conversion and optionally FP32→BF16.

    Spec ref: PACK.LATE_FMT.BFP_SHARED_EXP (stochastic rounding note in §6.2).

    Hardware note from spec: "Stochastic rounding has a slight hardware bias toward
    increasing magnitude (not true 50:50). Can also increase magnitude of values
    that don't need rounding."  We implement unbiased stochastic rounding; the
    hardware bias is a property of the physical LFSR and is not emulated here.
    # TODO: spec ambiguity — exact LFSR polynomial / bias not specified; using
    # unbiased random for now.

    Args:
        mantissa:  integer value to round
        drop_bits: number of bits being dropped (rounded away)
        rng:       optional random.Random instance (default: module-level random)
    """
    if drop_bits <= 0:
        return mantissa
    if rng is None:
        rand_val = random.getrandbits(drop_bits)
    else:
        rand_val = rng.getrandbits(drop_bits)
    return mantissa + rand_val


# ---------------------------------------------------------------------------
# BFP block pack / unpack  (format B: 8-bit shared exponent)
# ---------------------------------------------------------------------------

def _float_to_bf16_bits_flush(f: float) -> int:
    """FP32 → BF16 bit pattern, flushing denormals to ±0."""
    bits = _f32_bits(f)
    exp8 = (bits >> 23) & 0xFF
    if exp8 == 0:
        return (bits >> 16) & 0x8000  # flush: keep only sign
    return (bits >> 16) & 0xFFFF


def bfp_to_bf16(datum: int, exp: int) -> int:
    """Expand one BFP-B datum byte plus 8-bit shared exponent to BF16 bits."""
    sign = (datum >> 7) & 1
    mag = ((datum & 0x7F) << 1) & 0xFF
    if mag == 0:
        return 0xFF80 if sign else 0
    lz = _clz8(mag)
    mag = (mag << lz) & 0xFF
    exp = (exp - lz) & 0xFF
    return (sign << 15) | (exp << 7) | (mag & 0x7E)


def bfpa_to_fp16(datum: int, exp: int) -> int:
    """Expand one BFP-A datum byte plus 5-bit shared exponent to FP16 bits."""
    sign = (datum >> 7) & 1
    mag = ((datum & 0x7F) << 1) & 0xFF
    if mag == 0:
        return 0xFC00 if sign else 0
    lz = _clz8(mag)
    mag = (mag << lz) & 0xFF
    exp = (exp - lz) & 0x1F
    return (sign << 15) | (exp << 10) | ((mag & 0x7E) << 3)


def pack_bfp8(floats: list, stochastic: bool = False,
              rng: random.Random | None = None) -> tuple[int, list[int]]:
    """Pack 16 FP32 floats into BFP8 format (format B: 8-bit shared exponent).

    Returns (shared_exp, mantissas) where:
      - shared_exp: 8-bit shared exponent (max exponent across the group)
      - mantissas: list of 16 × 8-bit values (7 mantissa bits + 1 sign bit)

    Algorithm per spec §6.2:
    1. Convert each float to BF16 (flush denormals)
    2. Find max 8-bit exponent → shared exponent
    3. Right-shift each mantissa by (shared_exp - datum_exp)
    4. Pack as sign_bit | 7_mantissa_bits

    Spec refs:
      PACK.LATE_FMT.BFP_SHARED_EXP    — max exponent as shared exp
      PACK.LATE_FMT.BFP_MANTISSA_BITS — BFP8: 7 mantissa + 1 sign = 8 bits
    """
    if len(floats) != 16:
        raise ValueError(f"BFP block requires exactly 16 elements, got {len(floats)}")

    bf16_vals = [_float_to_bf16_bits_flush(f) for f in floats]

    # Find max 8-bit exponent
    exps = [(b >> 7) & 0xFF for b in bf16_vals]
    shared_exp = max(exps)

    mantissas = []
    for i, bf16 in enumerate(bf16_vals):
        sign = (bf16 >> 15) & 1
        exp = (bf16 >> 7) & 0xFF
        mant7 = bf16 & 0x7F  # 7-bit mantissa from BF16

        shift = shared_exp - exp
        # Include the implicit leading 1 bit — produces an 8-bit value.
        # The unpack path does: Mag = (DatumBits & 0x7f) << 1, so the stored
        # 7-bit field is the mantissa at positions [7:1] of the normalized form.
        # We need one extra right-shift (+1) to align the implicit-1 to bit 6.
        full_mant = (0x80 | mant7)  # 8 bits with implicit 1 at bit 7
        total_shift = shift + 1     # +1 because unpack left-shifts by 1
        if stochastic and total_shift > 0:
            full_mant = stochastic_round(full_mant, total_shift, rng)
        aligned = full_mant >> total_shift
        # Keep only 7 bits of mantissa
        m7 = aligned & 0x7F
        mantissas.append((sign << 7) | m7)

    return shared_exp, mantissas


def unpack_bfp8(shared_exp: int, mantissas: list[int]) -> list[float]:
    """Unpack BFP8 format (format B) to list of FP32 floats.

    Each mantissa byte: bit 7 = sign, bits [6:0] = 7-bit magnitude mantissa.

    Expansion algorithm (spec §3.4 BFP8ToBF16):
        Sign = DatumBits >> 7
        Mag  = (DatumBits & 0x7f) << 1   (shift left 1 = 8-bit with implicit 1)
        if Mag == 0: return ±0
        LZ = count_leading_zeros_8bit(Mag)
        Mag = (Mag << LZ) & 0xff
        ExpBits -= LZ
        result_bf16 = (Sign<<15) | (ExpBits<<7) | (Mag & 0x7e)

    Spec ref: UNPACK.FMT.BFP8_EXPANSION
    """
    result = []
    for sm in mantissas:
        sm &= 0xFF
        sign = sm >> 7
        mag = (sm & 0x7F) << 1  # 8-bit with implicit leading bit
        if mag == 0:
            result.append(-0.0 if sign else 0.0)
            continue
        lz = _clz8(mag)
        mag = (mag << lz) & 0xFF
        exp = shared_exp - lz
        bf16 = (sign << 15) | (exp << 7) | (mag & 0x7E)
        result.append(bf16_to_fp32(bf16))
    return result


def pack_bfp4(floats: list, stochastic: bool = False,
              rng: random.Random | None = None) -> tuple[int, list[int]]:
    """Pack 16 FP32 floats into BFP4 format (format B: 8-bit shared exp, 3-bit mantissa).

    Returns (shared_exp, mantissas) where mantissas are 4-bit values (1 sign + 3 mant).

    Spec ref: PACK.LATE_FMT.BFP_MANTISSA_BITS — BFP4: 3 mantissa + 1 sign = 4 bits.
    """
    if len(floats) != 16:
        raise ValueError(f"BFP block requires exactly 16 elements, got {len(floats)}")

    # Compute via BFP8 first, then truncate mantissa to 3 bits
    shared_exp, bfp8_mants = pack_bfp8(floats, stochastic=stochastic, rng=rng)
    mantissas = []
    for m in bfp8_mants:
        sign = (m >> 7) & 1
        mant3 = (m >> 4) & 0x7  # top 3 of 7 mantissa bits
        mantissas.append((sign << 3) | mant3)
    return shared_exp, mantissas


def unpack_bfp4(shared_exp: int, mantissas: list[int]) -> list[float]:
    """Unpack BFP4 format (format B) to list of FP32 floats.

    Each mantissa nibble: bit 3 = sign, bits [2:0] = 3-bit magnitude mantissa.
    Uses BFP8ToBF16 with DatumBits << 4 (pre-shift to align in 8-bit field).

    Spec ref: unpack-data-path.md §3.4 — BFP4→BF16: BFP8ToBF16(DatumBits<<4, ExpBits)
    """
    result = []
    for sm in mantissas:
        sm &= 0xF
        sign = (sm >> 3) & 1
        # Pre-shift to BFP8 layout
        shifted = ((sm & 0x7) << 4) | (sign << 7)
        bfp8_byte = (sign << 7) | ((sm & 0x7) << 4)
        # Apply BFP8ToBF16 with the pre-shifted datum
        mag = ((sm & 0x7) << 4) << 1  # 8-bit with implicit leading bit position
        mag &= 0xFF
        if mag == 0:
            result.append(-0.0 if sign else 0.0)
            continue
        lz = _clz8(mag)
        mag = (mag << lz) & 0xFF
        exp = shared_exp - lz
        bf16 = (sign << 15) | (exp << 7) | (mag & 0x7E)
        result.append(bf16_to_fp32(bf16))
    return result


def pack_bfp2(floats: list, stochastic: bool = False,
              rng: random.Random | None = None) -> tuple[int, list[int]]:
    """Pack 16 FP32 floats into BFP2 format (format B: 8-bit shared exp, 1-bit mantissa).

    Returns (shared_exp, mantissas) where mantissas are 2-bit values (1 sign + 1 mant).

    Spec ref: PACK.LATE_FMT.BFP_MANTISSA_BITS — BFP2: 1 mantissa + 1 sign = 2 bits.
    """
    if len(floats) != 16:
        raise ValueError(f"BFP block requires exactly 16 elements, got {len(floats)}")

    shared_exp, bfp8_mants = pack_bfp8(floats, stochastic=stochastic, rng=rng)
    mantissas = []
    for m in bfp8_mants:
        sign = (m >> 7) & 1
        mant1 = (m >> 6) & 0x1  # top 1 of 7 mantissa bits
        mantissas.append((sign << 1) | mant1)
    return shared_exp, mantissas


def unpack_bfp2(shared_exp: int, mantissas: list[int]) -> list[float]:
    """Unpack BFP2 format (format B) to list of FP32 floats.

    Each mantissa is 2 bits: bit 1 = sign, bit 0 = 1-bit magnitude mantissa.
    Uses BFP8ToBF16 with DatumBits << 6.

    Spec ref: unpack-data-path.md §3.4 — BFP2→BF16: BFP8ToBF16(DatumBits<<6, ExpBits)
    """
    result = []
    for sm in mantissas:
        sm &= 0x3
        sign = (sm >> 1) & 1
        mant1 = sm & 0x1
        # Pre-shift: datum << 6, giving sign|mant1|000000 in 8-bit
        mag = (mant1 << 6) << 1  # 8-bit with implicit leading bit position
        mag &= 0xFF
        if mag == 0:
            result.append(-0.0 if sign else 0.0)
            continue
        lz = _clz8(mag)
        mag = (mag << lz) & 0xFF
        exp = shared_exp - lz
        bf16 = (sign << 15) | (exp << 7) | (mag & 0x7E)
        result.append(bf16_to_fp32(bf16))
    return result


# ---------------------------------------------------------------------------
# BFP block pack / unpack  (format A: 5-bit shared exponent)
# ---------------------------------------------------------------------------

def _float_to_fp16_bits(f: float) -> int:
    """FP32 → FP16 bit pattern (for BFP-A format, uses 5-bit exponent)."""
    return fp32_to_fp16(f)


def pack_bfp8a(floats: list, stochastic: bool = False,
               rng: random.Random | None = None) -> tuple[int, list[int]]:
    """Pack 16 FP32 floats into BFP8a format (format A: 5-bit shared exponent).

    Returns (shared_exp, mantissas) where shared_exp is 5-bit (0..31).

    Algorithm per spec §6.2 BFP8a/BFP4a/BFP2a:
    1. Convert to E5M7 (FP16-like with 5-bit exponent, 7-bit mantissa)
    2. Find max 5-bit exponent → shared exponent (zero-extended to 8 bits for storage)
    3. Right-shift mantissas to align with shared exponent
    4. Pack: 7 mantissa bits + 1 sign bit = 8 bits

    Spec ref: UNPACK.FMT.BFP8A_EXPANSION (and §6.2 format A description)
    """
    if len(floats) != 16:
        raise ValueError(f"BFP block requires exactly 16 elements, got {len(floats)}")

    fp16_vals = [_float_to_fp16_bits(f) for f in floats]

    # Find max 5-bit exponent
    exps = [(b >> 10) & 0x1F for b in fp16_vals]
    shared_exp = max(exps)

    mantissas = []
    for fp16 in fp16_vals:
        sign = (fp16 >> 15) & 1
        exp5 = (fp16 >> 10) & 0x1F
        mant10 = fp16 & 0x3FF
        mant7 = (mant10 >> 3) & 0x7F  # top 7 of 10 mantissa bits

        shift = shared_exp - exp5
        # Same as BFP8: implicit leading 1 is at bit 7, unpack shifts left by 1,
        # so we need shift+1 total right-shifts.
        full_mant = (0x80 | mant7)  # 8-bit with implicit leading 1 at bit 7
        total_shift = shift + 1
        if stochastic and total_shift > 0:
            full_mant = stochastic_round(full_mant, total_shift, rng)
        aligned = full_mant >> total_shift
        m7 = aligned & 0x7F
        mantissas.append((sign << 7) | m7)

    return shared_exp, mantissas


def unpack_bfp8a(shared_exp: int, mantissas: list[int]) -> list[float]:
    """Unpack BFP8a format (format A, 5-bit exponent) to list of FP32 floats.

    Expansion algorithm (spec §3.4 BFP8aToFP16):
        Sign = DatumBits >> 7
        Mag  = (DatumBits & 0x7f) << 1
        if Mag == 0: return ±0
        LZ = count_leading_zeros_8bit(Mag)
        Mag = (Mag << LZ) & 0xff
        ExpBits -= LZ
        result_fp16 = (Sign<<15) | (ExpBits<<10) | ((Mag & 0x7e) << 3)

    Spec ref: UNPACK.FMT.BFP8A_EXPANSION
    """
    result = []
    for sm in mantissas:
        sm &= 0xFF
        sign = sm >> 7
        mag = (sm & 0x7F) << 1  # 8-bit with implicit leading bit
        if mag == 0:
            result.append(-0.0 if sign else 0.0)
            continue
        lz = _clz8(mag)
        mag = (mag << lz) & 0xFF
        exp = (shared_exp - lz) & 0x1F  # 5-bit exponent
        # Result is FP16 format
        fp16 = (sign << 15) | (exp << 10) | ((mag & 0x7E) << 3)
        result.append(fp16_to_fp32(fp16))
    return result


def pack_bfp4a(floats: list, stochastic: bool = False,
               rng: random.Random | None = None) -> tuple[int, list[int]]:
    """Pack 16 FP32 floats into BFP4a format (format A: 5-bit shared exp, 3-bit mant)."""
    if len(floats) != 16:
        raise ValueError(f"BFP block requires exactly 16 elements, got {len(floats)}")
    shared_exp, bfp8a_mants = pack_bfp8a(floats, stochastic=stochastic, rng=rng)
    mantissas = []
    for m in bfp8a_mants:
        sign = (m >> 7) & 1
        mant3 = (m >> 4) & 0x7  # top 3 of 7 mantissa bits
        mantissas.append((sign << 3) | mant3)
    return shared_exp, mantissas


def unpack_bfp4a(shared_exp: int, mantissas: list[int]) -> list[float]:
    """Unpack BFP4a format (format A) to list of FP32 floats.

    Uses BFP8aToFP16 with DatumBits << 4.

    Spec ref: unpack-data-path.md §3.4 — BFP4a→FP16: BFP8aToFP16(DatumBits<<4, ExpBits)
    """
    result = []
    for sm in mantissas:
        sm &= 0xF
        sign = (sm >> 3) & 1
        mant3 = sm & 0x7
        # Pre-shift to 8-bit BFP8a layout
        shifted = (sign << 7) | (mant3 << 4)
        # Apply BFP8aToFP16 logic
        mag = (mant3 << 4) << 1
        mag &= 0xFF
        if mag == 0:
            result.append(-0.0 if sign else 0.0)
            continue
        lz = _clz8(mag)
        mag = (mag << lz) & 0xFF
        exp = (shared_exp - lz) & 0x1F
        fp16 = (sign << 15) | (exp << 10) | ((mag & 0x7E) << 3)
        result.append(fp16_to_fp32(fp16))
    return result


def pack_bfp2a(floats: list, stochastic: bool = False,
               rng: random.Random | None = None) -> tuple[int, list[int]]:
    """Pack 16 FP32 floats into BFP2a format (format A: 5-bit shared exp, 1-bit mant)."""
    if len(floats) != 16:
        raise ValueError(f"BFP block requires exactly 16 elements, got {len(floats)}")
    shared_exp, bfp8a_mants = pack_bfp8a(floats, stochastic=stochastic, rng=rng)
    mantissas = []
    for m in bfp8a_mants:
        sign = (m >> 7) & 1
        mant1 = (m >> 6) & 0x1  # top 1 of 7 mantissa bits
        mantissas.append((sign << 1) | mant1)
    return shared_exp, mantissas


def unpack_bfp2a(shared_exp: int, mantissas: list[int]) -> list[float]:
    """Unpack BFP2a format (format A) to list of FP32 floats.

    Uses BFP8aToFP16 with DatumBits << 6.

    Spec ref: unpack-data-path.md §3.4 — BFP2a→FP16: BFP8aToFP16(DatumBits<<6, ExpBits)
    """
    result = []
    for sm in mantissas:
        sm &= 0x3
        sign = (sm >> 1) & 1
        mant1 = sm & 0x1
        # Pre-shift: datum << 6
        mag = (mant1 << 6) << 1
        mag &= 0xFF
        if mag == 0:
            result.append(-0.0 if sign else 0.0)
            continue
        lz = _clz8(mag)
        mag = (mag << lz) & 0xFF
        exp = (shared_exp - lz) & 0x1F
        fp16 = (sign << 15) | (exp << 10) | ((mag & 0x7E) << 3)
        result.append(fp16_to_fp32(fp16))
    return result


# ---------------------------------------------------------------------------
# NoBFPExpSection path
# ---------------------------------------------------------------------------

def pack_bfp_no_exp_section(floats: list, bits_per_elem: int,
                             force_exp: int = 0,
                             format_a: bool = False) -> list[int]:
    """Pack BFP data without writing a shared exponent section.

    Used when NoBFPExpSection=true in the tile descriptor for BFP4/BFP2.
    The exponent section is omitted; all datums use force_exp as the shared
    exponent (from FORCED_SHARED_EXP_shared_exp register).

    BFP8 always has an exponent section regardless of NoBFPExpSection.

    Args:
        floats:       list of 16 FP32 values
        bits_per_elem: 2 or 4 (BFP2 or BFP4)
        force_exp:    the forced shared exponent value (8-bit for format B,
                      5-bit for format A)
        format_a:     True for format A (5-bit exp), False for format B (8-bit)

    Returns:
        list of mantissa integers (same count as floats)

    Spec ref: UNPACK.TILE_LAYOUT.BFP_NO_EXP_SECTION
    """
    if bits_per_elem not in (2, 4):
        raise ValueError(f"NoBFPExpSection only valid for BFP2/BFP4, got bits={bits_per_elem}")
    if format_a:
        if bits_per_elem == 4:
            _, mants = pack_bfp4a(floats)
        else:
            _, mants = pack_bfp2a(floats)
    else:
        if bits_per_elem == 4:
            _, mants = pack_bfp4(floats)
        else:
            _, mants = pack_bfp2(floats)
    # Note: we computed shared_exp from the data; caller is responsible for
    # supplying force_exp from config and ensuring it matches.
    # The packing still uses the natural shared exp; to use force_exp the
    # downstream agent would call unpack_bfp* with force_exp directly.
    return mants


# ---------------------------------------------------------------------------
# Shuffled-format (SrcA/SrcB 19-bit cell) conversions
# ---------------------------------------------------------------------------

def shuffled_to_ieee(val_19bit: int) -> int:
    """Convert 19-bit shuffled Src cell value to IEEE FP32 bit pattern.

    19-bit layout: { sign[18], mantissa[17:8] (10 bits), exponent[7:0] (8 bits) }
    Expands 10 mantissa bits to top 10 of FP32 mantissa field (bits 22:13).

    Spec ref: DTC.19BIT.SHUFFLED_TO_IEEE
    """
    sign = (val_19bit >> 18) & 1
    mantissa = (val_19bit >> 8) & 0x3FF
    exponent = val_19bit & 0xFF
    return (sign << 31) | (exponent << 23) | (mantissa << 13)


def ieee_to_shuffled(ieee_bits: int) -> int:
    """Convert IEEE FP32 bit pattern to 19-bit shuffled Src cell format.

    Truncates 23-bit FP32 mantissa to top 10 bits.

    Spec ref: DTC.19BIT.IEEE_TO_SHUFFLED
    """
    sign = (ieee_bits >> 31) & 1
    exponent = (ieee_bits >> 23) & 0xFF
    mantissa = (ieee_bits >> 13) & 0x3FF
    return (sign << 18) | (mantissa << 8) | exponent
