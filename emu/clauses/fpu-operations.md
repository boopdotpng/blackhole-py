# fpu-operations

**Source:** [`fpu-operations.md`](../specs/fpu-operations.md) · **Emulator:** `blackhole-py/emu/tensix/fpu.py`

## 19-bit float format

### `FPU.FMT.19BIT_LAYOUT`
§Internal Register Format / Shuffled

> SrcA/SrcB store 19-bit values in shuffled order: {sign(1), mantissa(10), exponent(8)}.

### `FPU.FMT.19BIT_TO_FLOAT`
_§Internal Register Format / shuffled_to_ieee_

> shuffled_to_ieee: sign=bit18, mantissa=bits[17:8], exponent=bits[7:0]; maps to fp32 as (sign<<31)|(exp<<23)|(mant<<13).

### `FPU.FMT.FLOAT_TO_19BIT`
_§Internal Register Format / ieee_to_shuffled_

> ieee_to_shuffled: truncates fp32 mantissa to top 10 bits; stores as (sign<<18)|(mant<<8)|exp.

### `FPU.FMT.19BIT_NEG_INF`
_§ZEROSRC / write_mode=1_

> Negative-infinity in 19-bit format: sign=1, mant=0, exp=0xFF.

### `FPU.ZEROACC.CLR_SPECIFIC`
_§ZEROACC / clear_mode=0_

> clear_mode=0: clears DstRowValid for a single specific row (addressed by where).

### `FPU.ZEROACC.CLR_16`
_§ZEROACC / clear_mode=1_

> clear_mode=1: clears DstRowValid for 16 consecutive rows starting at where.

### `FPU.ZEROACC.CLR_HALF`
_§ZEROACC / clear_mode=2_

> clear_mode=2: clears low half (rows 0-511) if where bit0=0, high half if bit0=1.

### `FPU.ZEROACC.CLR_ALL`
_§ZEROACC / clear_mode=3_

> clear_mode=3: clears all 1024 DstRowValid bits.

### `FPU.ZEROACC.CLEARS_VALID_NOT_BITS`
§ZEROACC / Summary

> ZEROACC clears DstRowValid bits; it does NOT write zeroes into DstBits.

### `FPU.ZEROACC.CLR_HALF_NO_ADDRMOD`
_§ZEROACC / CLR_HALF and CLR_ALL_

> CLR_HALF and CLR_ALL do not apply the ADDR_MOD; only CLR_SPECIFIC and CLR_16 update RWCs.

## ZEROSRC

### `FPU.ZEROSRC.CLR_SRCA_ZERO`
_§ZEROSRC / write_mode=0 src_mask=1_

> ZEROSRC with src_mask&1 and write_mode=0: fills all 64×16 cells of the FPU SrcA bank with 0.

### `FPU.ZEROSRC.CLR_SRCA_NEG_INF`
_§ZEROSRC / write_mode=1_

> ZEROSRC with src_mask&1 and write_mode=1: fills SrcA bank with negative-infinity (19-bit).

### `FPU.ZEROSRC.CLR_SRCB_ZERO`
_§ZEROSRC / src_mask&2_

> ZEROSRC with src_mask&2: fills SrcB bank with 0 (never -inf).

### `FPU.MVMUL.DST_EQUALS_SRCB_AT_SRCA`
§MVMUL / Summary

> MVMUL computes Dst += SrcB @ SrcA; 8 rows of SrcB × 16-row SrcA → 8×16 result into Dst.

### `FPU.MVMUL.ACCUMULATES_INTO_DEST`
§MVMUL / Behavioral Model

> When dest row is valid, MVMUL accumulates: Dst[row][col] += sum_k(SrcB[k][col] * SrcA[k][col]). When dest row is invalid, MVMUL initializes: treats prior value as 0.

### `FPU.MVMUL.SETS_DEST_VALID`
§MVMUL / Behavioral Model

> MVMUL marks dest rows valid after writing.

### `FPU.MVMUL.RWC_ADDRESSING`
§MVMUL / Behavioral Model / Row addressing

> MVMUL: dst_base = d.dst + rwc.d*16; srca_base = rwc.a*16; srcb_base = rwc.b*8.

### `FPU.ELWADD.ELEMENT_WISE_ADD`
§ELWADD / Summary

> ELWADD computes Dst = SrcA + SrcB (or Dst += SrcA + SrcB when dest_accum_en=1), 16 rows × 16 cols.

### `FPU.ELWADD.DEST_ACCUM_EN`
_§ELWADD / dest_accum_en_

> dest_accum_en=1: if dest row is valid, add prior Dst value to the result.

### `FPU.ELWADD.SETS_DEST_VALID`
§ELWADD / Behavioral Model

> ELWADD marks all written dest rows valid.

### `FPU.ELWADD.RWC_ADDRESSING`
§ELWADD / Behavioral Model

> ELWADD: dst_base = d.dst + rwc.d*16; srca_base = rwc.a*16; srcb_base = rwc.b*16.

### `FPU.GMPOOL.COLUMN_WISE_MAX`
§GMPOOL / Summary

> GMPOOL: for each column j, compute column-wise max over 16 SrcA rows, accumulate into one Dst row.

### `FPU.GMPOOL.ACCUMULATES_MAX`
§GMPOOL / Behavioral Model

> When dest row is valid, GMPOOL keeps max(SrcA_col_max, prior Dst value).

### `FPU.GMPOOL.INITIALIZES_ON_INVALID`
§GMPOOL / Behavioral Model

> When dest row is invalid, GMPOOL initializes with the SrcA column max (no prior Dst value).

### `FPU.GMPOOL.SETS_DEST_VALID`
§GMPOOL / Behavioral Model

> GMPOOL marks dest rows valid after writing.

### `FPU.MOVB2D.MOV_1_ROW`
_§MOVB2D / movb2d_instr_mod=0_

> movb2d_instr_mod=0: copy 1 SrcB row to Dest.

### `FPU.MOVB2D.MOV_4_ROWS`
_§MOVB2D / movb2d_instr_mod=1_

> movb2d_instr_mod=1: copy 4 SrcB rows to Dest.

### `FPU.MOVB2D.MOV_8_ROWS`
_§MOVB2D / movb2d_instr_mod=2_

> movb2d_instr_mod=2: copy 8 SrcB rows to Dest.

### `FPU.MOVB2D.CONVERTS_19BIT_TO_DEST`
§MOVB2D / Data Flow

> MOVB2D converts 19-bit SrcB values to FP32 Dest format.

### `FPU.MOVB2D.SETS_DEST_VALID`
§MOVB2D / Behavioral Model

> MOVB2D marks all written dest rows valid.

### `FPU.MOVD2A.MOV_1_ROW`
_§MOVD2A / instr_mod=0_

> instr_mod=0: copy 1 Dest row to SrcA.

### `FPU.MOVD2A.MOV_4_ROWS`
_§MOVD2A / instr_mod!=0_

> instr_mod!=0 (e.g. instr_mod=2): copy 4 Dest rows to SrcA.

### `FPU.MOVD2A.CONVERTS_DEST_TO_19BIT`
§MOVD2A / Format Conversion

> MOVD2A reads FP32 from Dest and writes as 19-bit shuffled value to SrcA.

### `FPU.MOVD2A.READS_ZERO_WHEN_INVALID`
§MOVD2A / Behavioral Model

> MOVD2A reads 0.0 from invalid dest rows.

### `FPU.MOVD2B.MOVES_TO_SRCB`
§MOVD2B / Summary

> MOVD2B: identical behavior to MOVD2A but writes to SrcB instead of SrcA.

### `FPU.CLEARDVALID.RELEASES_SRCA`
_§CLEARDVALID / clear_dvalid&1_

> CLEARDVALID with bit 0 set: calls srca.release_from_fpu() — flips bank back to unpackers.

### `FPU.CLEARDVALID.RELEASES_SRCB`
_§CLEARDVALID / clear_dvalid&2_

> CLEARDVALID with bit 1 set: calls srcb.release_from_fpu().

### `FPU.TRNSPSRCB.TRANSPOSES_ROWS_16_31`
§TRNSPSRCB / SrcB rows 16-31

> TRNSPSRCB transposes the 16×16 matrix in SrcB rows 16–31 in place.

### `FPU.TRNSPSRCB.ROWS_0_15_UNCHANGED`
§TRNSPSRCB / Effect

> TRNSPSRCB does not touch SrcB rows 0–15.

### `FPU.SETRWC.DISPATCHED_BY_TRISC1`
trisc1.py::TRISC1Decoder.dispatch

> SETRWC instruction is dispatched by TRISC1 to rwc.execute_setrwc().

### `FPU.INCRWC.DISPATCHED_BY_TRISC1`
trisc1.py::TRISC1Decoder.dispatch

> INCRWC instruction is dispatched by TRISC1 to rwc.execute_incrwc().

### `FPU.MVMUL.DISPATCHED_BY_TRISC1`
trisc1.py::TRISC1Decoder.dispatch

> MVMUL instruction is dispatched by TRISC1 to fpu.mvmul().

### `FPU.ELWADD.DISPATCHED_BY_TRISC1`
trisc1.py::TRISC1Decoder.dispatch

> ELWADD instruction is dispatched by TRISC1 to fpu.elwadd().

### `FPU.GMPOOL.DISPATCHED_BY_TRISC1`
trisc1.py::TRISC1Decoder.dispatch

> GMPOOL instruction is dispatched by TRISC1 to fpu.gmpool().
