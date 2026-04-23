# dest-srca-srcb-registers

**Source:** [`dest-srca-srcb-registers.md`](../specs/dest-srca-srcb-registers.md)

## DestRegFile layout

### `DEST.LAYOUT.1024_ROWS`
§1.1 Physical Storage

> Dest is 1024 rows × 16 columns of 16-bit cells, with one valid bit per row.

### `DEST.LAYOUT.VALID_BITS`
§1.1 Physical Storage

> Each of the 1024 rows has an associated DstRowValid bool.

### `DEST.ZEROACC.CLR_VALID_NOT_BITS`
§1.6 ZEROACC

> ZEROACC clears DstRowValid bits; it does not overwrite DstBits storage.

### `DEST.ZEROACC.CLEAR_SPECIFIC_ROW`
§1.6 / ClearRow

> clear_mode=ClearRow: clears the valid bit for one specific row.

### `DEST.ZEROACC.CLEAR_RANGE_16`
§1.6 / Clear16Rows

> clear_mode=Clear16Rows: clears valid bits for 16 consecutive rows starting at start.

### `DEST.ZEROACC.CLEAR_HALF`
§1.6 / ClearHalf

> clear_mode=ClearHalf with which=0: clears rows 0–511; which=1: clears rows 512–1023.

### `DEST.ZEROACC.CLEAR_ALL`
§1.6 / ClearFull

> clear_mode=ClearFull: clears all 1024 valid bits.

### `DEST.DOUBLE_BUFFER.LOW_HIGH_HALF`
§1.5 Half-Dest Double-Buffering

> Dest is split into two halves: rows 0-511 (low) and rows 512-1023 (high) for double-buffering between math and pack threads.

### `DEST.DOUBLE_BUFFER.MATH_PACK_SEM`
_§1.5 / MATH_PACK semaphore_

> MATH_PACK semaphore (index 1) coordinates ownership: SEMPOST from math, SEMGET from pack.

## SrcRegFile layout

### `SRC.LAYOUT.TWO_BANKS`
§2.1 Physical Storage

> SrcA and SrcB each have 2 banks, each bank has 64 rows × 16 columns of 19-bit data.

### `SRC.BANK.ALLOWED_CLIENT`
§2.3 Bank Tracking State

> Each bank has an AllowedClient: 'unpackers' (initial) or 'matrix_unit'.

### `SRC.BANK.INITIAL_STATE`
§2.3 Bank Tracking State

> Both banks start with allowed_client='unpackers'.

### `SRC.FLIP_TO_FPU.SETS_MATRIX_UNIT`
_§2.4 Double-Buffering / flip_to_fpu_

> flip_to_fpu(): sets allowed_client='matrix_unit' on the unpack_bank, then flips unpack_bank to the other index.

### `SRC.RELEASE_FROM_FPU.RESTORES_UNPACKERS`
_§2.4 Double-Buffering / release_from_fpu_

> release_from_fpu(): sets allowed_client='unpackers' on the fpu_bank, then flips fpu_bank to the other index.

### `SRC.UNPACR.BANK_FLIP`
_§trisc0.py::TRISC0Decoder._unpacr_

> UNPACR with SetDatValid=1 calls flip_to_fpu() on the target SrcRegFile.

### `SRC.UNPACR_NOP.BANK_FLIP`
_§trisc0.py::TRISC0Decoder._unpacr_nop_

> UNPACR_NOP with Set_Dvalid&1 calls flip_to_fpu() on the selected SrcRegFile.

### `SRC.SRCA_VS_SRCB.UNPACKER`
§3.7 SrcA vs SrcB Differences

> SrcA is filled by Unpacker 0; SrcB is filled by Unpacker 1. No X/Y transposition for SrcB.

### `SRC.SRCA_VS_SRCB.MVMUL_ROLES`
§3.7 SrcA vs SrcB Differences

> In MVMUL, SrcA is the right-hand 16×16 matrix; SrcB is the left-hand 8×16 matrix.

### `SRC.TRNSPSRCB.ROWS_16_31`
§3.6 TRNSPSRCB

> TRNSPSRCB transposes the 16×16 matrix stored in SrcB rows 16–31 of the current FPU bank.
