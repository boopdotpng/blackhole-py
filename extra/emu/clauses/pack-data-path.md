# pack-data-path

**Source:** [`pack-data-path.md`](../specs/pack-data-path.md) · **Emulator:** `blackhole-py/extra/emu/tensix/trisc2.py`

## PACR Encoding

### `PACK.ENCODING.OPCODE`
§2 PACR Instruction Encoding / opcode

> PACR opcode is 0x41.

### `PACK.ENCODING.PACKERMASK`
§2 PACR Instruction Encoding / ReadIntfSel

> ReadIntfSel [11:8] = PackerMask: which packers are active. PackerMask=0b0000 is special: maps to 0b0001 (packer 0 only).

### `PACK.ENCODING.LAST_FLAG`
§2 PACR Instruction Encoding / Last

> Last [0] = flush output buffers and signal tile pack complete.

### `PACK.ENCODING.FLUSH_FLAG`
§2 PACR Instruction Encoding / Flush

> Flush [1] = flush output buffers (sets NeedsNewAddress for next PACR).

### `PACK.ENCODING.ZERO_WRITE`
§2 PACR Instruction Encoding / ZeroWrite

> ZeroWrite [12] = if 1, reads from /dev/null (outputs all zeros instead of Dest).

## Dest Read (Input Address)

### `PACK.DEST_READ.ADC_CHANNEL0`
§3.1 ADC-based Address Computation

> The packer reads from Dest using ADC Channel 0 for the input address. Addr = PCK0_ADDR_BASE_REG_0_Base + ADC.X * Xstride + ADC.Y * Ystride
>        + ADC.Z * Zstride + ADC.W * Wstride.

### `PACK.DEST_READ.INPUT_NUM_DATUMS`
§3.1 ADC-based Address Computation / InputNumDatums

> InputNumDatums = ADC.Channel[1].X - ADC.Channel[0].X + 1 (0 if Flush=1).

### `PACK.DEST_READ.BYTES_PER_DATUM`
§3.2 Dst Address Interpretation / BytesPerDatum

> In_data_format bits [1:0]: 0b00 → 4 bytes (FP32/TF32/INT32), 0b01 → 2 bytes (FP16/BF16/INT16), other → 1 byte (8-bit formats).

### `PACK.DEST_READ.DEST_TARGET_OFFSET`
§3.2 Dst Address Interpretation / DatumIndex

> DatumIndex += Config.DEST_TARGET_REG_CFG_PACK_SEC[i].Offset << 4 to select which Dest tile to pack from (double-buffering support).

### `PACK.DEST_READ.L1_SOURCE_MODE`
§3.4 L1 Source Mode (Packer 0 only)

> When Source_interface_selection=1 in packer 0's config, packer 0 reads from L1 instead of Dest. Early format conversion is skipped.

## ADC / Counter Mechanics

### `PACK.ADC.SETADCXX_X_RANGE`
§4.2 SETADCXX — Packer X Range

> SETADCXX sets Channel[1].X (x_end2) and Channel[0].X (x_start). InputNumDatums = Channel[1].X - Channel[0].X + 1.

### `PACK.ADC.CHANNEL_ASSIGNMENT`
§4.3 Channel Assignment

> Channel 0 = input (Dest) address generation (Y/Z updated by AddrMod after PACR). Channel 1 = output (L1) address generation; x_end2 stored in Channel[1].X.

### `PACK.ADC.ADDR_MOD_POST_PACR`
§4.6 AddrMod — Post-PACR Counter Updates

> After each PACR, AddrMod[AddrMode] updates Channel[0].Y/Z (src increments/clears) and Channel[1].Y/Z (dst increments/clears).

## Early Format Conversion

### `PACK.EARLY_FMT.FORMAT_ENCODING`
§5.1 What It Does / format table

> 4-bit format encoding: 0=FP32, 1=FP16, 2=BFP8a, 3=BFP4a, 4=TF32, 5=BF16, 6=BFP8, 7=BFP4, 8=INT32, 9=INT16, 10=FP8, 14=INT8, 15=BFP2.

### `PACK.EARLY_FMT.FP32_TO_BF16`
§5.2 Common Conversion Paths / FP32 Dest, BF16 output

> For FP32 Dest with BF16 intermediate, early conversion truncates the FP32 mantissa to 7 bits (drop low 16 bits). Denormals are flushed to zero.

### `PACK.EARLY_FMT.READ_RAW_BYPASS`
_§3.3 PCK_DEST_RD_CTRL Modes / Read_raw_

> PCK_DEST_RD_CTRL.Read_int8=1 (Read_raw): bypass early-conversion rounding/shifting (identity or bitcast).

### `PACK.EARLY_FMT.READ_32B_DATA`
_§3.3 PCK_DEST_RD_CTRL Modes / Read_32b_data_

> PCK_DEST_RD_CTRL.Read_32b_data=1: read 32-bit rows from Dest (FP32/INT32 dest, or FP32 acc mode). Otherwise 16-bit rows.

## Late Format Conversion / BFP

### `PACK.LATE_FMT.BFP_SHARED_EXP`
§6.2 BFP Formats in the Late Conversion

> For BFP output, late conversion finds the maximum 8-bit exponent across 16 datums, then right-shifts each mantissa to align. One shared exponent per group of 16 datums is written to the L1 exponent section.

### `PACK.LATE_FMT.BFP_MANTISSA_BITS`
§6.2 BFP Formats in the Late Conversion / mantissa widths

> BFP8: 7 mantissa bits + 1 sign bit = 8 bits. BFP4: 3 mantissa bits + 1 sign bit = 4 bits. BFP2: 1 mantissa bit + 1 sign bit = 2 bits.

### `PACK.LATE_FMT.EXP_SECTION_SIZE`
_§6.5 Exp_section_size_

> Exp_section_size is set to num_faces for BFP outputs (one exponent block per face), and 0 for FP8/INT8 (no separate exponent section).

### `PACK.LATE_FMT.DIS_SHARED_EXP_ASSEMBLER`
_§6.3 Dis_shared_exp_assembler_

> Dis_shared_exp_assembler=1 disables shared-exponent normalization across the group of 16 datums; each datum's individual exponent is used as-is.

## ReLU Stage

### `PACK.RELU.NO_RELU`
§8 ReLU / Activation / mode=0

> STACC_RELU_ApplyRelu=0: identity (no activation applied).

### `PACK.RELU.ZERO_RELU`
§8 ReLU / Activation / mode=1

> STACC_RELU_ApplyRelu=1 (ZERO_RELU): return 0 if x <= 0.

### `PACK.RELU.MIN_THRESHOLD_RELU`
§8 ReLU / Activation / mode=2

> STACC_RELU_ApplyRelu=2 (MIN_THRESHOLD_RELU): return 0 if x <= threshold; threshold must be >= 0.

### `PACK.RELU.MAX_THRESHOLD_RELU`
§8 ReLU / Activation / mode=3

> STACC_RELU_ApplyRelu=3 (MAX_THRESHOLD_RELU): clamp x to [0, threshold].

## Exponent Thresholding

### `PACK.EXP_THRESH.ZEROES_BELOW_THRESHOLD`
§7 Exponent Thresholding

> When Exp_threshold_en=1, datums with exponent < Exp_threshold are zeroed before late conversion.

## L1 Output

### `PACK.L1_OUTPUT.ALIGNED_WRITES`
§1 Overview of the Pack Pipeline / L1 (16-byte aligned writes)

> All L1 output writes from the packer are 16-byte aligned.

### `PACK.L1_OUTPUT.OUTPUT_ADC_CHANNEL1`
§4.3 Channel Assignment / Channel 1

> Channel 1 of the packer ADC drives the L1 output address: Y/Z updated by AddrMod dst increments; W typically fixed.

### `PACK.L1_OUTPUT.ZERO_COMPRESSION`
§1 Overview / Zero Compression stage

> Zero compression (Disable_zero_compress=0) compresses runs of zeros in the output datum stream before writing to L1.

### `PACK.L1_OUTPUT.TILE_HEADER`
§1 Overview / output tile layout

> The packer writes a 16-byte tile header at the destination L1 address before any datum bytes.

## Four-Packer Model

### `PACK.MULTI_PACKER.FOUR_PACKERS`
§1 Overview of the Pack Pipeline

> Tensix has four packers (0-3). PACR with PackerMask=0b1111 fires all four simultaneously. Packer i reads Dest face i.

