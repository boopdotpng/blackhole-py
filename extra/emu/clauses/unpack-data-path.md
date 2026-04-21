# unpack-data-path

**Source:** [`unpack-data-path.md`](../specs/unpack-data-path.md) · **Emulator:** `blackhole-py/extra/emu/tensix/trisc0.py`

## UNPACR encoding

### `UNPACK.ENCODING.OPCODE`
§2.1 Instruction Encoding

> UNPACR opcode is 0x42.

### `UNPACK.ENCODING.WHICH_UNPACKER`
_§2.1 Instruction Encoding / Unpack_block_selection_

> Unpack_block_selection [23]: 0=SrcA/Dst (Unpacker 0), 1=SrcB (Unpacker 1).

### `UNPACK.ENCODING.SET_DAT_VALID`
§2.1 Instruction Encoding / SetDatValid (FlipSrc)

> SetDatValid [6]=1 (FlipSrc): flip the SrcA/SrcB bank — transfer current unpack bank to the MatrixUnit and begin writing to the other bank.

### `UNPACK.BANK_FLIP.SRCA_FLIP`
§2.6 Phase 5 / FlipSrc / SrcA

> UNPACR with Unpack_block_selection=0, SetDatValid=1: calls srca.flip_to_fpu(), transferring the unpack bank to 'matrix_unit' and advancing the unpack_bank pointer.

### `UNPACK.BANK_FLIP.SRCB_FLIP`
§2.6 Phase 5 / FlipSrc / SrcB

> UNPACR with Unpack_block_selection=1, SetDatValid=1: calls srcb.flip_to_fpu().

### `UNPACK.BANK_FLIP.NO_FLIP_WITHOUT_SET_DAT_VALID`
§2.6 Phase 5 / FlipSrc (conditional)

> UNPACR with SetDatValid=0: bank ownership is not changed.

### `UNPACK.NOP.SET_DVALID_FLIP`
_§UNPACR_NOP / Set_Dvalid_

> UNPACR_NOP (0x43) with Set_Dvalid & 1 != 0: performs bank flip for the selected unpacker (Unpacker_Select field).

### `UNPACK.NOP.CLEAR_SRCA_BANK`
_§UNPACR_NOP / Src_ClrVal_Ctrl bit 0_

> UNPACR_NOP with Src_ClrVal_Ctrl & 1 != 0: zeros all 64 rows × 16 cols of the SrcA unpack bank.

### `UNPACK.NOP.CLEAR_SRCB_BANK`
_§UNPACR_NOP / Src_ClrVal_Ctrl bit 1_

> UNPACR_NOP with Src_ClrVal_Ctrl & 2 != 0: zeros all 64 rows × 16 cols of the SrcB unpack bank.

### `UNPACK.TILE_LAYOUT.HEADER_16B`
§1.1 Non-BFP Formats / tile header

> Non-BFP tiles begin with a 16-byte tile header (DigestSize=0) which is skipped when computing InAddr_Datums.

### `UNPACK.TILE_LAYOUT.NON_BFP_ROW_MAJOR`
§1.1 Non-BFP Formats

> Non-BFP tile data is stored row-major within each face; faces are concatenated: [header][Face0: XDim×DatumSizeBytes][Face1: ...]...

### `UNPACK.TILE_LAYOUT.BFP_EXP_SECTION`
§1.2 BFP Tile Layout in L1

> Uncompressed BFP tiles: [16-byte header][exponent section: ceil(NumExponents/16)*16 bytes, 16-byte aligned][mantissa section]. NumExponents = ceil(NumElements/16) — one exponent byte per 16 datums.

### `UNPACK.TILE_LAYOUT.BFP_NO_EXP_SECTION`
§1.2 BFP Tile Layout / NoBFPExpSection

> BFP4/BFP2 tiles: when NoBFPExpSection=true in the tile descriptor, the exponent section is omitted and FORCED_SHARED_EXP_shared_exp is used instead. BFP8 always has an exponent section regardless of NoBFPExpSection.

### `UNPACK.TILE_LAYOUT.COMPRESSED_RSI`
§1.3 Compressed Tile Layout / RSI section

> Compressed tiles have a Row Start Index (RSI) section after the header: ceil((NumRows+1)*2/16)*16 bytes of uint16_t offsets. RSI[i] = byte offset of row i in the interleaved datum+delta stream.

### `UNPACK.TILE_LAYOUT.COMPRESSED_RLE_DELTA`
§1.3 Compressed Tile Layout / datum+delta stream

> Compressed datum stream is interleaved: [32 datums][32 RLE nibbles (4 bits each)]... Each nibble specifies how many zeros to insert after the corresponding datum (0-15).

## Input address computation

### `UNPACK.INPUT_ADDR.BASE_PLUS_OFFSET`
§2.3 Phase 2: Input Address Computation

> InAddr = THCON_SEC[n].REG3_Base_address + (REG7_Offset_address & 0xffff). Then skip tile header: InAddr = (InAddr + 1 + DigestSize) * 16.

### `UNPACK.INPUT_ADDR.FIRST_DATUM`
§2.3 Phase 2 / FirstDatum

> FirstDatum = ((ADC_ZW.W * ZDim + ADC_ZW.Z) * YDim + YPos) * XDim + XPos for uncompressed tiles. InputNumDatums = XEnd - XPos.

### `UNPACK.INPUT_ADDR.FIFO_WRAP`
§2.3 Phase 2 / Circular FIFO wrap

> If InAddr_Datums > Unpack_limit_address*16, subtract Unpack_fifo_size*16 to wrap. Same wrap applies to InAddr_Exponents.

## Output address computation

### `UNPACK.OUTPUT_ADDR.STRIDE_FORMULA`
§2.4 Phase 3: Output Address Computation

> OutAddr = UNP[n].ADDR_BASE_REG_1_Base + ADC_Out.Y * Ystride
>          + ADC_Out.Z * Zstride + ADC_Out.W * Wstride.
> Scaled by element size: FP32/TF32/INT32 → >>2; FP16/BF16/INT16 → >>1.

### `UNPACK.OUTPUT_ADDR.ROW_COL_FROM_OUT_ADDR`
§2.4 Phase 3 / Row, Col

> Row = OutAddr / 16; Col = OutAddr & 15. Dest address: Row=SrcA/SrcB row index.

## Main unpack loop

### `UNPACK.LOOP.DATUM_READ`
§2.6 Phase 5: Main Unpack Loop / datum read

> Each loop iteration reads DatumSizeBytes from L1 at InAddr_Datums, increments InAddr_Datums by DatumSizeBytes.

### `UNPACK.LOOP.ROW_STRIDE_ADVANCE`
§2.6 Phase 5: Main Unpack Loop / row stride

> After every 16 elements, advance InAddr_Datums by RowStride instead of DatumSizeBytes (to skip to next row). Apply FIFO wrap after advance.

### `UNPACK.LOOP.BFP_EXP_READ`
§2.6 Phase 5: Main Unpack Loop / BFP exponent

> For BFP formats (unless Force_shared_exp=1): read one exponent byte per 16 datums from InAddr_Exponents; InAddr_Exponents advances by 1/16 per datum.

### `UNPACK.LOOP.ALL_DATUMS_ZERO`
§2.6 Phase 5: Main Unpack Loop / AllDatumsAreZero

> If AllDatumsAreZero=1, each datum is forced to 0 regardless of L1 content.

### `UNPACK.LOOP.WRITE_TO_SRCA`
§2.6 Phase 5 / SrcA path

> Unpacker 0 (SrcA path): skip 4 header rows; apply ColShift; apply SrcRow offset (unless SRCA_SET_SetOvrdWithAddr). Optionally transpose low 4 bits of Row and Col.

### `UNPACK.LOOP.WRITE_TO_SRCB`
§2.6 Phase 5 / SrcB path

> Unpacker 1 (SrcB path): Row = (Row + CurrentUnpacker.SrcRow[CurrentThread]) & 0x3f. Write Datum to SrcB[Bank][Row][Col].

## Post-instruction counter updates

### `UNPACK.POST.ADC_INCREMENT`
§2.7 Phase 6: Post-instruction Counter Updates / ADC Y and Z

> After UNPACR, increment ADC.Channel[0].Y by Ch0YInc, .Z by Ch0ZInc, ADC.Channel[1].Y by Ch1YInc, .Z by Ch1ZInc (from instruction encoding).

### `UNPACK.POST.SRC_ROW_ADVANCE`
_§2.7 Phase 6 / Unpack_Src_Reg_Set_Upd_

> When Unpack_Src_Reg_Set_Upd=1 and FlipSrc=0: advance SrcRow by 16 + SrcRowBase to prepare for the next unpack into the same bank.

## Format conversion

### `UNPACK.FMT.BF16_TO_SRCA`
§3.2 FormatConversion / BF16

> BF16 input → SrcA/SrcB: call WriteSrcBF16(DatumBits), which is WriteSrcTF32(DatumBits << 3), storing a 19-bit TF32-layout value.

### `UNPACK.FMT.FP32_TO_BF16_FLUSH_DENORMAL`
§3.2 FormatConversion / FP32 → BF16

> FP32 → BF16 conversion: if no exponent bits are set (denormal), flush to ±0 (clear low 23 bits, keep sign). Then DatumBits >>= 16.

### `UNPACK.FMT.BFP8_EXPANSION`
§3.4 BFP to Floating-Point Conversion / BFP8ToBF16

> BFP8→BF16: Sign = DatumBits >> 7; Mag = (DatumBits & 0x7f) << 1. Count leading zeros of Mag; shift Mag left by LZ; subtract LZ from ExpBits. Result = (Sign<<15) | (ExpBits<<7) | (Mag & 0x7e).

### `UNPACK.FMT.BFP8A_EXPANSION`
§3.4 BFP to Floating-Point Conversion / BFP8aToFP16

> BFP8a→FP16: same normalize-and-align as BFP8ToBF16, but ExpBits is 5-bit (no bits in 0xe0 range valid). Result uses 5-bit exponent field in FP16.

### `UNPACK.FMT.INT8_OVERLAY`
§3.2 FormatConversion / INT8

> INT8 sign-magnitude: Sign = DatumBits & 0x80; DatumBits -= Sign (unsigned mag). If Mag != 0: DatumBits |= (16<<10) (dummy FP16 exponent "8"). DatumBits |= (Sign<<8). Treated as FP16 in Src layout.

### `UNPACK.FMT.REGISTER_LAYOUT_TRANSFORMS`
§3.3 Register Layout Transforms

> WriteSrcTF32: rearranges 19-bit TF32 as [Sign:1][Man:10][Exp:8]. WriteSrcBF16: WriteSrcTF32(x<<3). WriteSrcFP16: WriteSrcTF32(expanded 19-bit). WriteDstFP16: [Sign:1][Man:10][Exp:5]. WriteDstBF16: [Sign:1][Man:7][Exp:8]. WriteDstFP32: WriteDstBF16(high16) | low16.

## ADC state structure

### `UNPACK.ADC.STRUCTURE`
§4.1 ADC State Structure

> Each of 3 threads has its own ADC. Each ADC has Unpacker[2] and Packers entries, each with 2 channels (X,X_Cr,Y,Y_Cr,Z,Z_Cr,W,W_Cr).

### `UNPACK.ADC.CHANNEL0_INPUT_CHANNEL1_OUTPUT`
§4.2 Channel Usage

> Channel 0 drives L1 read address (face Z, row Y, element X). Channel 1 drives Src/Dst write address (Y1,Z1,W1 as stride multipliers; X1 = end of row boundary).
