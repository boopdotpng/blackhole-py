# Data Types and Format Conversions

## Overview

The Blackhole Tensix coprocessor uses several numeric formats internally. Values move between L1 memory, the SrcA/SrcB register files, the Dest register file, and the SFPU, and each boundary may require format conversion. This document specifies the bit-level representations, the conversion functions the emulator must implement, and the hardware quirks that must be replicated faithfully.

---

## 1. Internal Register Format (Shuffled)

SrcA and SrcB register files store 19-bit values in **shuffled** order:

```
{ sign(1), mantissa(10), exponent(8) }
```

Bit positions within the 19-bit cell:

| Field    | Bits  | Width |
|----------|-------|-------|
| sign     | 18    | 1     |
| mantissa | 17:8  | 10    |
| exponent | 7:0   | 8     |

This is **not** IEEE order. IEEE FP32 uses `{sign(1), exponent(8), mantissa(23)}`. The emulator must convert between the shuffled 19-bit representation and IEEE FP32 bit patterns whenever values cross the SrcA/SrcB boundary.

```python
def shuffled_to_ieee(val_19bit):
    sign = (val_19bit >> 18) & 1
    mantissa = (val_19bit >> 8) & 0x3FF
    exponent = val_19bit & 0xFF
    return (sign << 31) | (exponent << 23) | (mantissa << 13)

def ieee_to_shuffled(ieee_bits):
    sign = (ieee_bits >> 31) & 1
    exponent = (ieee_bits >> 23) & 0xFF
    mantissa = (ieee_bits >> 13) & 0x3FF
    return (sign << 18) | (mantissa << 8) | exponent
```

Note that `shuffled_to_ieee` expands 10 mantissa bits to a 23-bit field by placing them in the top 10 bits (bits 22:13) and zeroing bits 12:0. Conversely, `ieee_to_shuffled` truncates the 23-bit mantissa to its top 10 bits.

### Supported Input Formats Stored in the 19-bit Cell

| Format | Bit layout       | Fit in 19-bit cell                      |
|--------|------------------|-----------------------------------------|
| TF32   | 1 + 10 + 8 = 19  | Native fit, no padding needed           |
| BF16   | 1 + 7 + 8 = 16   | Mantissa zero-padded from 7 to 10 bits  |
| FP16   | 1 + 10 + 5 = 16  | Exponent zero-padded from 5 to 8 bits   |
| INT8   | 1 + 8 + 0 = 9    | Sign-magnitude; stored in sign+mantissa fields |

---

## 2. FP32 <-> BF16

BF16 (Brain Float 16) is the top 16 bits of an IEEE FP32 value. It has the same exponent range as FP32 (8-bit exponent, bias 127) but only 7 mantissa bits instead of 23.

```python
import struct

def fp32_to_bf16(f):
    bits = struct.unpack('<I', struct.pack('<f', f))[0]
    return (bits >> 16) & 0xFFFF

def bf16_to_fp32(bf16):
    bits = bf16 << 16
    return struct.unpack('<f', struct.pack('<I', bits))[0]
```

**Rounding mode:** The default is round-toward-zero (RTZ), implemented by plain truncation (the `>> 16` discards the low 16 mantissa bits without rounding). Firmware can enable round-to-nearest-even (RTNE) by setting `cfg0` bit 31 (`EnBFloatRTNE`). When RTNE is enabled the emulator must add a round bit based on the discarded bits before truncating.

---

## 3. FP32 -> TF32

TF32 (TensorFloat-32) keeps the FP32 sign and full 8-bit exponent but truncates the mantissa from 23 bits to 10 bits. It is a 19-bit logical type that occupies the full 19-bit shuffled cell.

```python
def fp32_to_tf32(f):
    bits = struct.unpack('<I', struct.pack('<f', f))[0]
    return bits & 0xFFFFE000  # zero low 13 mantissa bits
```

The result is stored as an IEEE FP32 bit pattern with the low 13 mantissa bits cleared. When written into a SrcA/SrcB cell it is then passed through `ieee_to_shuffled`.

There is no TF32-to-FP32 conversion: TF32 values in Src are zero-extended in the mantissa when expanded to FP32 by `shuffled_to_ieee`, which is equivalent.

---

## 4. FP32 <-> FP16 (IEEE)

FP16 is standard IEEE 754 half-precision: 1 sign bit, 5 exponent bits (bias 15), 10 mantissa bits.

**Conversion FP32 -> FP16:**

1. Extract sign, exponent, mantissa from the FP32 bit pattern.
2. Rebias the exponent: `exp16 = exp32 - 127 + 15`. If `exp16 <= 0`, the result is a subnormal or zero. If `exp16 >= 31`, the result saturates to the maximum finite FP16 value (Tensix does not produce Inf or NaN on overflow).
3. Truncate mantissa from 23 bits to 10 bits (take bits 22:13).
4. Pack as `{sign(1), exp16(5), mantissa10(10)}`.

**Conversion FP16 -> FP32:**

1. Extract sign, 5-bit exponent, 10-bit mantissa.
2. Rebias exponent: `exp32 = exp16 - 15 + 127`. Handle subnormals (exp16 == 0) by normalizing.
3. Zero-extend mantissa from 10 to 23 bits.
4. Pack as IEEE FP32.

**Hardware non-conformance:** The Tensix FP16 implementation does not conform to IEEE 754 in edge cases. Overflow saturates to the maximum finite FP16 value rather than producing infinity. NaN inputs may not produce NaN outputs. The emulator should replicate this saturating behavior rather than IEEE-correct behavior.

---

## 5. Sign-Magnitude Integers

Tensix uses **sign-magnitude** representation for integers in Dest and in the SFPU. This differs from the two's complement used by general-purpose CPUs.

In sign-magnitude:
- The most-significant bit is the sign (1 = negative).
- The remaining bits are the absolute value (magnitude).
- There are two representations of zero: +0 (`0x00000000`) and -0 (`0x80000000`).

```python
def int_to_signmag(val, bits=32):
    if val < 0:
        return (1 << (bits-1)) | (-val & ((1 << (bits-1)) - 1))
    return val

def signmag_to_int(val, bits=32):
    sign = (val >> (bits-1)) & 1
    mag = val & ((1 << (bits-1)) - 1)
    return -mag if sign else mag
```

**Known hardware quirk — `SFPCAST` mode 3 (sign-magnitude to two's complement):**

When `SFPCAST` is invoked in mode 3, it converts a sign-magnitude INT32 to two's complement INT32. Because sign-magnitude has `-0` while two's complement instead has `-2^31`, the hardware maps sign-magnitude -0 (`0x80000000`) to the most-negative INT32 (`0x80000000` in two's complement, i.e., -2147483648) instead of zero. The emulator must replicate this behavior.

The correct conversion of sign-magnitude -0 to two's complement would be 0. Any conforming implementation would handle this as a special case, but the hardware does not.

---

## 6. DataFormat Enum

The hardware uses a 4-bit field to identify numeric formats in tile descriptors and configuration registers. The encoding is:

| Value | Name       | Notes                                                  |
|-------|------------|--------------------------------------------------------|
| 0     | Float32    | IEEE FP32                                              |
| 1     | Float16    | IEEE FP16                                              |
| 2     | Bfp8       | Block floating point, 8-bit mantissa, format A exponent |
| 3     | Bfp4       | Block floating point, 4-bit mantissa, format A exponent |
| 4     | Tf32       | TensorFloat-32 (19-bit logical)                        |
| 5     | Float16_b  | BFloat16                                               |
| 6     | Bfp8_b     | Block floating point, 8-bit mantissa, format B exponent |
| 7     | Bfp4_b     | Block floating point, 4-bit mantissa, format B exponent |
| 8     | Int32      | Sign-magnitude 32-bit integer                          |
| 9     | UInt16 (a.k.a. INT16 in ISA pack/unpack tables) | Unsigned 16-bit integer                                |
| 10    | Lf8 (a.k.a. FP8 in ISA pack/unpack tables)     | FP8 E5M2 (or E4M3 depending on mode bit; see below)    |
| 11    | Bfp2       | Block floating point, 2-bit mantissa, format A         |
| 12    | (reserved) |                                                        |
| 13    | (reserved) |                                                        |
| 14    | Int8       | Sign-magnitude 8-bit integer                           |
| 15    | Bfp2_b     | Block floating point, 2-bit mantissa, format B         |

**`_b` suffix:** The "bfloat" variant of each BFP format. Format A and Format B differ in how shared exponents are scoped — see section 7.

**FP8 dual-mode encoding:** The value 10 (`Lf8`) encodes two different FP8 formats selected by a separate mode bit:
- `Pac_LF8_4b_exp = 0` / `Unp_LF8_4b_exp = 0`: E5M2 (5 exponent bits, 2 mantissa bits)
- `Pac_LF8_4b_exp = 1` / `Unp_LF8_4b_exp = 1`: E4M3 (4 exponent bits, 3 mantissa bits)

The mode bit is in separate packer/unpacker configuration registers and is not part of the 4-bit DataFormat field itself.

---

## 7. BFP (Block Floating Point)

BFP formats compress data by sharing a single exponent across a group of elements. Each element stores only its mantissa; the exponent is stored once per group and applied to all elements in that group during unpacking.

### Tile Layout

A 32x32 BFP tile in L1 stores data and exponents as separate sections:

| Format      | Data bytes (mantissa only) | Exponent bytes | Total    |
|-------------|---------------------------|----------------|----------|
| Bfp8 / Bfp8_b | 1024 (8 bits per element)  | 64             | 1088     |
| Bfp4 / Bfp4_b | 512 (4 bits per element)   | 64             | 576      |
| Bfp2 / Bfp2_b | 256 (2 bits per element)   | 64             | 320      |

The 64 exponent bytes encode 4 faces x 16 shared exponents = 64 exponent values. Each exponent is 1 byte.

### Format A vs Format B

Both format variants store 64 exponents per tile (4 faces, 16 exponents per face). The difference is in which elements share a given exponent:

- **Format A:** 1 shared exponent per face row. A face is 16x16 elements. Each of the 16 rows within a face gets its own shared exponent. All 16 elements in that row share that exponent.
- **Format B:** Same structural layout (16 exponents per face) but uses a different derivation rule for the shared exponent value. The exact derivation depends on packer configuration (typically the maximum exponent in the group).

The unpacker applies: `element_value = mantissa * 2^(shared_exponent - bias)`.

---

## 8. Tile Byte Sizes

Total bytes per 32x32 tile in L1, including any exponent sections but excluding the tile header (16 bytes):

| Format                                    | Bytes per 32x32 tile |
|-------------------------------------------|----------------------|
| Float32 / Int32 / UInt32                  | 4096                 |
| Float16 / Float16_b / UInt16              | 2048                 |
| Bfp8 / Bfp8_b                             | 1088                 |
| Bfp4 / Bfp4_b                             | 576                  |
| Bfp2 / Bfp2_b                             | 320                  |
| UInt8 / Int8 / Lf8 / Fp8_e4m3            | 1024                 |

These sizes assume a full 32x32 tile (1024 elements). The tile header (16 bytes) is in addition to these values and is read by the unpacker's header parser before element data begins.

---

## 9. Dest Register Data Views

The Dest register file provides two different logical views over the same physical 1024x16 storage of 16-bit cells.

### Physical Storage

The underlying physical array is:

```
Dest_physical[1024 rows][16 cols] of 16-bit cells
```

Total: 1024 * 16 * 2 = 32768 bytes = 32 KB.

### Dst16b View (16-bit mode)

When `ALU_ACC_CTRL_Fp32_enabled = 0`:

```
Dst16b[1024 rows][16 cols] of 16-bit values
```

Each element maps directly to one physical cell. Used for BF16, FP16, INT16, and UINT16 accumulation.

### Dst32b View (32-bit mode)

When `ALU_ACC_CTRL_Fp32_enabled = 1`:

```
Dst32b[512 rows][16 cols] of 32-bit values
```

Each 32-bit value is split across **two physical rows that are 8 apart**:
- Low 16 bits: physical row `r`
- High 16 bits: physical row `r + 8`

For logical row `n` in Dst32b:
- The low half is at physical row `n % 8 + (n / 8) * 16`
- The high half is at physical row `n % 8 + (n / 8) * 16 + 8`

Used for FP32 and INT32 accumulation.

The emulator must implement both views and apply the correct mapping based on the `ALU_ACC_CTRL_Fp32_enabled` bit when reading or writing Dest.

---

## Source References

| Source | Path | Relevant Content |
|--------|------|-----------------|
| Unpackers overview | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/Unpackers/` | Shuffled format, format conversion pipeline, BFP expansion |
| UNPACR.md | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/UNPACR_Regular.md` | Unpacker instruction, TileDescriptor fields, DataFormat encoding |
| Dst.md | `tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/Dst.md` | Dest register layout, Dst16b/Dst32b views, row interleaving |
| SFPCAST.md | `tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPCAST*.md` | SFPCAST mode 3 sign-magnitude to two's complement, `-0` ↔ `-2^31` mapping; mode 2 INT32 ABS quirk |
| cfg_defines.h | `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/cfg_defines.h` | `ALU_ACC_CTRL_Fp32_enabled`, `EnBFloatRTNE`, `Pac_LF8_4b_exp`, `Unp_LF8_4b_exp` bit positions |
| cpack_common.h | `tt-llk/tt_llk_blackhole/common/inc/cpack_common.h` | BFP exponent assembly, tile byte size computations |
| cunpack_common.h | `tt-llk/tt_llk_blackhole/common/inc/cunpack_common.h` | DataFormat enum values, BFP exponent consumption |
| ckernel_instr_params.h | `tt-llk/tt_llk_blackhole/common/inc/ckernel_instr_params.h` | Format constants and identifiers |
| pack-data-path.md | `emu-specs/pack-data-path.md` | Packer format conversion stages, BFP shared exponent assembly |
| unpack-data-path.md | `emu-specs/unpack-data-path.md` | Unpacker format conversion, L1 tile layouts, BFP expansion |
| dest-srca-srcb-registers.md | `emu-specs/dest-srca-srcb-registers.md` | Detailed SrcA/SrcB/Dest register file structure |
