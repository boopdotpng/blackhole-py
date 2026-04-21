# data-types-and-conversions

**Source:** [`data-types-and-conversions.md`](../specs/data-types-and-conversions.md) · **Emulator:** `blackhole-py/emu/tensix/fpu.py`

## 19-bit shuffled format

### `DTC.19BIT.LAYOUT`
§1 Internal Register Format / Shuffled

> SrcA/SrcB store 19-bit values as {sign(1 bit 18), mantissa(10 bits 17:8), exponent(8 bits 7:0)}.

### `DTC.19BIT.SHUFFLED_TO_IEEE`
_§1 / shuffled_to_ieee_

> shuffled_to_ieee: expands 10 mantissa bits to top 10 of FP32 mantissa field (bits 22:13), zeros bits 12:0.

### `DTC.19BIT.IEEE_TO_SHUFFLED`
_§1 / ieee_to_shuffled_

> ieee_to_shuffled: truncates 23-bit FP32 mantissa to top 10 bits, packs into 19-bit cell.

### `DTC.19BIT.BF16_ZERO_PAD`
§1 / Supported Input Formats

> BF16 stored in 19-bit cell: 7-bit mantissa zero-padded to 10 bits (low 3 bits = 0).

### `DTC.19BIT.FP16_EXP_PAD`
§1 / Supported Input Formats

> FP16 stored in 19-bit cell: 5-bit exponent zero-padded to 8 bits.

### `DTC.19BIT.NAN_HANDLING`
§1 / NaN

> NaN in FP32 → 19-bit: encoded as exp=0x7F in bits[7:0], quiet-NaN bit set in bits[17:8].

### `DTC.BF16.IS_TOP_16_FP32`
§2 FP32 <-> BF16

> BF16 is the top 16 bits of an IEEE FP32 value: same 8-bit exponent (bias 127), only 7 mantissa bits.

### `DTC.BF16.FP32_TO_BF16_TRUNCATE`
_§2 / fp32_to_bf16_

> fp32_to_bf16: truncates via right-shift-16 (round-toward-zero by default).

### `DTC.BF16.BF16_TO_FP32`
_§2 / bf16_to_fp32_

> bf16_to_fp32: left-shifts 16 bits to recover FP32 (low 16 mantissa bits = 0).

### `DTC.BF16.RTZ_DEFAULT`
§2 / Rounding mode

> Default rounding is round-toward-zero (truncation). RTNE enabled by cfg0 bit 31 (EnBFloatRTNE).

## FP32 -> TF32

### `DTC.TF32.TRUNCATES_MANTISSA`
§3 FP32 -> TF32

> fp32_to_tf32: keeps sign + 8-bit exponent + top 10 mantissa bits; zeros low 13 mantissa bits.

### `DTC.TF32.NO_TF32_TO_FP32`
§3 / no conversion back

> There is no TF32-to-FP32 conversion step; TF32 in Src is zero-extended in mantissa by shuffled_to_ieee.

## FP32 <-> FP16

### `DTC.FP16.OVERFLOW_SATURATES`
§4 / Hardware non-conformance

> Tensix FP16 overflow saturates to max finite FP16 value (not inf); NaN inputs may not produce NaN outputs.

### `DTC.FP16.REBIAS_EXPONENT`
§4 / FP32 -> FP16

> FP32->FP16: rebias exponent (exp32-127+15); truncate mantissa to top 10 bits.

## Sign-magnitude integers

### `DTC.SIGNMAG.REPRESENTATION`
§5 Sign-Magnitude Integers

> Tensix uses sign-magnitude for integers: MSB=sign (1=negative), remaining bits=magnitude. Two representations of zero: +0=0x00000000 and -0=0x80000000.

### `DTC.SIGNMAG.NEG_ZERO_TO_TWOSCOMP`
§5 / Known hardware quirk

> SFPCAST mode 3 (sign-magnitude to two's complement): hardware maps sign-magnitude -0 (0x80000000) to most-negative INT32 (0x80000000 in two's complement), not 0.

## DataFormat enum

### `DTC.FMT.ENUM_VALUES`
§6 DataFormat Enum

> 4-bit DataFormat encoding: 0=Float32, 1=Float16, 2=Bfp8, 3=Bfp4, 4=Tf32, 5=Float16_b, 6=Bfp8_b, 7=Bfp4_b, 8=Int32, 9=UInt16, 10=Lf8, 11=Bfp2, 14=Int8, 15=Bfp2_b.

### `DTC.FMT.FP8_DUAL_MODE`
§6 / FP8 dual-mode

> DataFormat 10 (Lf8) encodes two FP8 formats: E5M2 (Pac_LF8_4b_exp=0) or E4M3 (=1).

## BFP

### `DTC.BFP.SHARED_EXPONENT`
§7 BFP / Format A

> BFP Format A: 1 shared exponent per face row (16 elements per row share one exponent).

### `DTC.BFP.TILE_LAYOUT`
§7 / Tile Layout

> A 32x32 BFP8 tile: 1024 data bytes + 64 exponent bytes = 1088 bytes total.

## Dest views

### `DTC.DEST.DST16B_VIEW`
§9 / Dst16b View

> Dst16b view: 1024 rows × 16 cols of 16-bit values; used for BF16/FP16/INT16 accumulation.

### `DTC.DEST.DST32B_VIEW`
§9 / Dst32b View

> Dst32b view: 512 rows × 16 cols of 32-bit values. For logical row n: low 16 bits at physical row n%8+(n/8)*16; high 16 bits at that row + 8.
