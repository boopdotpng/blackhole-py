# Unpack Data Path

## Overview

The Tensix coprocessor has **two unpackers**: Unpacker 0 (moves L1 data to SrcA or directly to Dest) and Unpacker 1 (moves L1 data to SrcB). Both read from L1 memory, perform format conversion, and write into register files. They operate concurrently and are controlled by the `UNPACR` instruction issued from TRISC0 (the unpack thread).

The full pipeline from software perspective:

```
L1 tile bytes
    │
    ▼
[TileDescriptor: InDataFormat, XDim, YDim, ZDim, WDim, blobs_per_xy_plane]
    │
    ▼
[ADC address counters: X0, Y0, Z0, W0 (L1 input), X1, Y1, Z1, W1 (Src output)]
    │
    ▼
[Format conversion: BFP expansion, FP conversion, bit rearrangement]
    │
    ▼
SrcA[bank][row][col]   (19-bit elements, 2 banks × 64 rows × 16 cols)
SrcB[bank][row][col]   (19-bit elements, 2 banks × 64 rows × 16 cols)
Dst[row][col]          (16-bit or 32-bit elements, 1024 rows × 16 cols)
```

The primary instruction is `UNPACR`. Secondary instructions (`UNPACR_NOP`, `SETADC`, `SETADCXY`, `SETADCZW`, `SETADCXX`, `INCADCXY`, `INCADCZW`) configure ADC state, signal bank handoff, and pop overlay stream messages.

Sources:
- `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/UNPACR_Regular.md`
- `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/Unpackers/`
- `tt-llk/tt_llk_blackhole/common/inc/cunpack_common.h`
- `tt-llk/tt_llk_blackhole/llk_lib/llk_unpack_AB.h`, `llk_unpack_A.h`, `llk_unpack_tilize.h`, `llk_unpack_untilize.h`
- `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/cfg_defines.h`

---

## 1. L1 Tile Data Layouts (Per Format)

### 1.1 Non-BFP Formats (FP32, TF32, BF16, FP16, FP8, INT8, UINT8, INT16, INT32)

Non-BFP tiles are **flat packed arrays of elements**. There is no separate exponent section.

Each tile in L1 begins with a **tile header** of `(1 + DigestSize) * 16` bytes. In practice `DigestSize = 0`, so the header is **16 bytes** (one 16-byte block). The header is skipped when computing `InAddr_Datums`; elements begin immediately after.

After the header, elements are laid out in row-major order within each face, then faces are concatenated:

```
[16-byte tile header]
[Face 0: XDim × YDim elements, DatumSizeBytes each]
[Face 1: ...]
...
[Face ZDim-1: ...]
```

For a standard 32×32 BF16 tile (XDim=256, YDim=1, ZDim=4 faces, DatumSizeBytes=2):
- Header: 16 bytes
- Each face: 16 elements × 1 row × 2 bytes = 32 bytes
- Total: 16 + 4 × 32 = 144 bytes (but XDim encodes the full face flat size; for a 16×16 face, XDim=256)

**Critical**: `XDim` is the total number of datums per Z-slice (one "row" of the tile-level iteration). For a 16×16 face: `XDim = 256`, `YDim = 1`, `ZDim = 4` (four faces per tile).

### 1.2 BFP Tile Layout in L1

BFP tiles (BFP8/BFP4/BFP2, both A and B exponent variants) have a richer structure.

For **uncompressed** BFP tiles (`IsUncompressed = true`):

```
[16-byte tile header]
[Exponent section: ceil(NumExponents/16) × 16 bytes, 16-byte aligned]
[Mantissa section: flat array of mantissa bits, DatumSizeBytes each]
```

Where:
- `NumExponents = ceil(NumElements / 16)` — one exponent byte per 16 datums
- `NumElements = XDim × YDim × ZDim × WDim`
- For BFP8: `DatumSizeBytes = 1`; for BFP4: `0.5`; for BFP2: `0.25`

**Exception for BFP4/BFP2**: When `NoBFPExpSection` is set in the tile descriptor (`ConfigDescriptor.NoBFPExpSection = true`), the exponent section is **omitted** and a forced shared exponent (`FORCED_SHARED_EXP_shared_exp`) is used instead. BFP8 always has an exponent section regardless of `NoBFPExpSection`.

The address computation (from UNPACR functional model):

```c
// After tile header:
InAddr = (BaseAddress + 1 + DigestSize) * 16;

// For BFP: exponent section starts here
if (IsBFPFormat(InDataFormat) && !REG2_Force_shared_exp) {
    InAddr_Exponents = InAddr;
    if (InDataFormat == BFP8 || InDataFormat == BFP8a || !NoBFPExpSection) {
        NumElements = XDim * YDim * ZDim * WDim;
        NumExponents = ceil(NumElements / 16.0);
        InAddr += ceil(NumExponents / 16.0) * 16;  // 16-byte aligned
    }
}

// Mantissa/datum section starts here
InAddr_Datums = InAddr;
// Advance by FirstDatum * DatumSizeBytes to reach the starting element
InAddr_Datums += FirstDatum * DatumSizeBytes;
// Exponent pointer also offset by FirstDatum/16 to reach the starting exponent
InAddr_Exponents += FirstDatum / 16.0;
```

**Exponent sharing**: Each exponent byte covers exactly 16 consecutive mantissa datums. The exponent pointer advances by `1/16` per datum (i.e., one new exponent byte every 16 datums). The index into the exponent array is `floor(InAddr_Exponents)` for integer byte access.

**Forced shared exponent** (`REG2_Force_shared_exp = 1`): The exponent section is omitted entirely; all datums use the value in `UNP[n].FORCED_SHARED_EXP_shared_exp`. Useful for INT8→BF16 conversion.

### 1.3 Compressed Tile Layout

For compressed tiles (`IsUncompressed = false`), the layout is:

```
[16-byte tile header]
[Row Start Index (RSI) section: ceil((NumRows+1)*2/16)*16 bytes, 16-byte aligned]
  - Array of uint16_t: RSI[0..NumRows], where RSI[i] = byte offset of row i in datum stream
  - Used to seek to a specific compressed row
[Exponent section: same as uncompressed if BFP format]
[Interleaved datum+delta stream:
  - 32 datums (DatumSizeBytes each)
  - 32 RLE delta nibbles (4 bits each = 16 bytes total)
  - 32 datums
  - 32 RLE delta nibbles
  - ...]
```

Where `NumRows = YDim * ZDim * WDim` for regular tiles, or `BlobsPerXYPlane * ZDim * WDim` when blobs are used.

Each RLE nibble specifies how many zeros to insert after the corresponding datum (0-15).

---

## 2. UNPACR Functional Model

This is the complete functional model of `UNPACR` (Regular mode). See source at `UNPACR_Regular.md`.

### 2.1 Instruction Encoding

```c
TT_OP_UNPACR(
    /* u1 */ WhichUnpacker,        // 0=SrcA/Dst, 1=SrcB
    // 8-bit packed increment field:
    ((/* u2 */ Ch1YInc) << 6) +
    ((/* u2 */ Ch1ZInc) << 4) +
    ((/* u2 */ Ch0YInc) << 2) +
      /* u2 */ Ch0ZInc,
    false,                          // not FlushCache or IncrCtxCounter form
    /* u3 */ ContextNumber,         // which context to use (MultiContextMode only)
    /* u2 */ ContextADC,            // which ADC set to use (MultiContextMode only)
    /* bool */ MultiContextMode,    // enable multi-context
    /* bool */ FlipSrc,             // transfer bank to MatrixUnit and flip
    false,
    /* bool */ AllDatumsAreZero,    // write zeros regardless of L1 content
    /* bool */ UseContextCounter,   // use hardware context counter
    /* bool */ RowSearch,           // BFP blob row search mode
    false,
    false)
```

### 2.2 Phase 1: Context and Config Selection

```python
StateID = ThreadConfig[CurrentThread].CFG_STATE_ID_StateID
ConfigState = Config[StateID]
CurrentUnpacker = Unpackers[WhichUnpacker]

# Determine context
if MultiContextMode:
    if UseContextCounter:
        WhichContext = CurrentUnpacker.ContextCounter[CurrentThread]
    else:
        WhichContext = ContextNumber
    WhichContext += ThreadConfig[CurrentThread].UNPACK_MISC_CFG_CfgContextOffset[WhichUnpacker]
    WhichADC = ContextADC
    # WhichUnpacker==1 requires WhichContext < 2; WhichADC must not be 3
else:
    WhichContext = 0
    WhichADC = CurrentThread

ConfigDescriptor = ConfigState.THCON_SEC[WhichUnpacker].REG0_TileDescriptor

# Determine IsUncompressed
if MultiContextMode:
    IsUncompressed = ConfigState.THCON_SEC[WhichUnpacker].REG2_Disable_zero_compress_cntx[WhichContext]
else:
    IsUncompressed = ConfigDescriptor.IsUncompressed

# Tile dimensions
if MultiContextMode and WhichUnpacker == 0:
    XDim = ConfigState.THCON_SEC[0].REG5_Tile_x_dim_cntx[WhichContext & 3]
else:
    XDim = ConfigDescriptor.XDim
YDim = ConfigDescriptor.YDim
ZDim = max(ConfigDescriptor.ZDim, 1)
WDim = max(ConfigDescriptor.WDim, 1)

# Data format
if MultiContextMode and ConfigState.THCON_SEC[WhichUnpacker].REG2_Ovrd_data_format:
    InDataFormat  = ConfigState.THCON_SEC[WhichUnpacker].REG7_Unpack_data_format_cntx[WhichContext]
    OutDataFormat = ConfigState.THCON_SEC[WhichUnpacker].REG7_Unpack_out_data_format_cntx[WhichContext]
else:
    InDataFormat  = ConfigDescriptor.InDataFormat
    OutDataFormat = ConfigState.THCON_SEC[WhichUnpacker].REG2_Out_data_format
```

### 2.3 Phase 2: Input Address Computation

```python
# Base address (16-byte units)
if MultiContextMode and WhichContext != 0:
    InAddr = ConfigState.THCON_SEC[WhichUnpacker].REG3_Base_cntx[WhichContext].address \
           + (ConfigState.THCON_SEC[WhichUnpacker].REG7_Offset_cntx[WhichContext & 3].address & 0xffff)
else:
    InAddr = ConfigState.THCON_SEC[WhichUnpacker].REG3_Base_address \
           + (ConfigState.THCON_SEC[WhichUnpacker].REG7_Offset_address & 0xffff)

# Skip tile header: (1 + DigestSize) * 16 bytes
InAddr = (InAddr + 1 + ConfigDescriptor.DigestSize) * 16  # now in bytes

# For compressed tiles: RSI section
InAddr_RowStart = None
if not IsUncompressed:
    InAddr_RowStart = InAddr  # pointer to uint16_t RSI array
    if ConfigDescriptor.BlobsPerXYPlane:
        NumBlobs = ConfigDescriptor.BlobsPerXYPlane * ZDim * WDim
        InAddr += ceil_16((NumBlobs + 1) * 2)
    else:
        NumRows = YDim * ZDim * WDim
        InAddr += ceil_16((NumRows + 1) * 2)

# For BFP: exponent section
InAddr_Exponents = None
if IsBFPFormat(InDataFormat) and not ConfigState.THCON_SEC[WhichUnpacker].REG2_Force_shared_exp:
    InAddr_Exponents = InAddr
    if InDataFormat in (BFP8, BFP8a) or not ConfigDescriptor.NoBFPExpSection:
        NumElements = XDim * YDim * ZDim * WDim
        NumExponents = ceil(NumElements / 16.0)
        InAddr += ceil_16(NumExponents)

# Compute FirstDatum and InputNumDatums from ADC
ADC_XY = ADCs[WhichADC].Unpacker[WhichUnpacker].Channel[0]
ADC_ZW = ADCs[CurrentThread].Unpacker[WhichUnpacker].Channel[0]

if IsUncompressed:
    if not RowSearch:
        XPos = ADC_XY.X
        YPos = ADC_XY.Y
        XEnd = ADCs[WhichADC].Unpacker[WhichUnpacker].Channel[1].X + 1
    # (RowSearch/BlobsPerXYPlane path elided for brevity)
    FirstDatum = ((ADC_ZW.W * ZDim + ADC_ZW.Z) * YDim + YPos) * XDim + XPos
    InputNumDatums = XEnd - XPos
else:
    # Compressed: RSI lookup
    InAddr_RowStart += (ADC_ZW.W * ZDim + ADC_ZW.Z) * YDim * 2  # seek to Z/W plane
    FirstDatum = RSI_read(InAddr_RowStart, ADC_XY.Y & 0xff)       # uint16_t lookup
    InputNumDatums = RSI_read(InAddr_RowStart, (ADC_XY.Y & 0xff) + 1) - FirstDatum

# Datum address
InAddr_Datums = InAddr + FirstDatum * DatumSizeBytes

# Exponent pointer offset to match FirstDatum
if InAddr_Exponents is not None:
    InAddr_Exponents += FirstDatum / 16.0

# Circular FIFO wrap
limit  = ConfigState.THCON_SEC[WhichUnpacker].Unpack_limit_address * 16
fifo   = ConfigState.THCON_SEC[WhichUnpacker].Unpack_fifo_size * 16
def WrapAddr(addr):
    if addr > limit:
        addr -= fifo
    return addr
InAddr_Exponents = WrapAddr(InAddr_Exponents) if InAddr_Exponents else None
InAddr_Datums    = WrapAddr(InAddr_Datums)
```

### 2.4 Phase 3: Output Address Computation

```python
ADC_Out = ADCs[CurrentThread].Unpacker[WhichUnpacker].Channel[1]

OutAddr = (ConfigState.UNP[WhichUnpacker].ADDR_BASE_REG_1_Base
         + ADC_Out.Y * ConfigState.UNP[WhichUnpacker].ADDR_CTRL_XY_REG_1_Ystride
         + ADC_Out.Z * ConfigState.UNP[WhichUnpacker].ADDR_CTRL_ZW_REG_1_Zstride
         + ADC_Out.W * ConfigState.UNP[WhichUnpacker].ADDR_CTRL_ZW_REG_1_Wstride)

# Scale OutAddr by element size
if OutDataFormat in (FP32, TF32, INT32):
    OutAddr >>= 2   # 4-byte elements
elif OutDataFormat in (FP16, BF16, INT16):
    OutAddr >>= 1   # 2-byte elements
# else INT8/UINT8: OutAddr is 1-byte units

# Apply per-context dest address offset (MultiContextMode, Unpacker 0 only)
if MultiContextMode and WhichUnpacker == 0:
    CtxOutAddr = ConfigState.THCON_SEC[0].REG5_Dest_cntx[WhichContext & 3].address
    if UnpackToDst or ConfigState.UNP[0].ADD_DEST_ADDR_CNTR_add_dest_addr_cntr:
        OutAddr += CtxOutAddr
    else:
        OutAddr = CtxOutAddr
```

**Dest address for SrcA/SrcB**: `OutAddr` indexes elements (not bytes). `Row = OutAddr / 16`, `Col = OutAddr & 15`.

**SrcA Row offset**: The SrcA register file is indexed as `Row = (OutAddr/16 - 4) + CurrentUnpacker.SrcRow[CurrentThread]`. The `-4` accounts for a fixed 4-row header offset. If `SRCA_SET_SetOvrdWithAddr` is set, the raw row index is used directly (for unpack-to-dest path).

### 2.5 Phase 4: Row Stride (Tilize Mode vs Normal)

```python
DiscontiguousInputRows = ConfigState.THCON_SEC[WhichUnpacker].REG2_Tileize_mode
if DiscontiguousInputRows:
    # RowStride is the stride between input rows in L1 (tilize mode)
    RowStride = ((ConfigState.THCON_SEC[WhichUnpacker].REG2_Shift_amount_cntx[0] <<  4)
              |  (ConfigState.THCON_SEC[WhichUnpacker].REG2_Shift_amount_cntx[1] <<  8)
              |  (ConfigState.THCON_SEC[WhichUnpacker].REG2_Shift_amount_cntx[2] << 12))
    # max RowStride = 65520 bytes (12-bit precision with 4-bit shift)
else:
    RowStride = DatumSizeBytes * 16  # contiguous: advance by one row of 16 elements
```

### 2.6 Phase 5: Main Unpack Loop

```python
for i in range(InputNumDatums):
    # Read datum from L1
    DatumBits = ReadL1(InAddr_Datums, DatumSizeBytes)
    InAddr_Datums += DatumSizeBytes

    # Advance row after every 16 elements
    if (i + 1) % 16 == 0:
        InAddr_Datums -= DatumSizeBytes * 16
        InAddr_Datums += RowStride
        InAddr_Datums = WrapAddr(InAddr_Datums)

    # Read exponent for BFP formats
    ExpBits = 0
    if IsBFPFormat(InDataFormat):
        if REG2_Force_shared_exp:
            ExpBits = UNP[WhichUnpacker].FORCED_SHARED_EXP_shared_exp
        else:
            ExpBits = ReadL1Byte(floor(InAddr_Exponents))
            InAddr_Exponents += 1.0 / 16.0
            if InAddr_Exponents == floor(InAddr_Exponents / 16.0) * 16.0:
                InAddr_Exponents = WrapAddr(InAddr_Exponents)

    # Format conversion
    Datum = FormatConversion(InDataFormat, OutDataFormat, DatumBits, ExpBits,
                             WhichUnpacker, UnpackToDst)

    if AllDatumsAreZero:
        Datum = 0

    # Write to output register file
    Bank = CurrentUnpacker.SrcBank
    Row  = OutAddr // 16
    Col  = OutAddr & 15
    OutAddr += 1

    if WhichUnpacker == 1:
        # SrcB
        while SrcB[Bank].AllowedClient != UNPACKERS: wait
        Row = (Row + CurrentUnpacker.SrcRow[CurrentThread]) & 0x3f
        SrcB[Bank][Row][Col] = Datum

    else:
        # SrcA or Dst
        while SrcA[Bank].AllowedClient != UNPACKERS: wait
        if not UnpackToDst:
            # SrcA path: skip 4 header rows, apply ColShift
            if Row < 4 or Col < ColShift: continue
            Row -= 4
            Col -= ColShift
            if not SRCA_SET_SetOvrdWithAddr:
                Row += CurrentUnpacker.SrcRow[CurrentThread]
            if Transpose:
                RowLowBits = Row & 0xf
                RowLowBits, Col = Col, RowLowBits   # swap
                Row = (Row & ~0xf) | RowLowBits
            SrcA[Bank][Row & 0x3f][Col] = Datum
        else:
            # Unpack-to-Dest path
            Row -= 4
            if SRCA_SET_SetOvrdWithAddr:
                Row &= 0xf
            else:
                Row &= 0x3ff
            if OutDataFormat in (FP32, TF32, INT32):
                Dst32b[Row][Col] = Datum
            else:
                Dst16b[Row][Col] = Datum
```

### 2.7 Phase 6: Post-instruction Counter Updates

```python
# Context counter increment (MultiContextMode + UseContextCounter)
if MultiContextMode and UseContextCounter:
    IncrementedCounter = WhichContext + 1
    if IncrementedCounter >= (1 << ConfigState.THCON_SEC[WhichUnpacker].Context_count):
        IncrementedCounter = 0
    CurrentUnpacker.ContextCounter[CurrentThread] = IncrementedCounter

# ADC Y and Z increments (from instruction encoding)
for thread in [CurrentThread, WhichADC]:
    ADCs[thread].Unpacker[WhichUnpacker].Channel[0].Y += Ch0YInc
    ADCs[thread].Unpacker[WhichUnpacker].Channel[0].Z += Ch0ZInc
    ADCs[thread].Unpacker[WhichUnpacker].Channel[1].Y += Ch1YInc
    ADCs[thread].Unpacker[WhichUnpacker].Channel[1].Z += Ch1ZInc

# Bank flip / SrcRow reset
SrcRowBase = ThreadConfig[CurrentThread].SRCA_SET_Base << 4  # (or SRCB_SET_Base for unp1)
if FlipSrc:
    # Transfer current bank to MatrixUnit, flip to other bank
    (SrcB if WhichUnpacker else SrcA)[CurrentUnpacker.SrcBank].AllowedClient = MATRIX_UNIT
    CurrentUnpacker.SrcBank ^= 1
    CurrentUnpacker.SrcRow[CurrentThread] = SrcRowBase
elif ConfigState.THCON_SEC[WhichUnpacker].Unpack_Src_Reg_Set_Upd:
    # Advance SrcRow by 16 rows for next unpack
    CurrentUnpacker.SrcRow[CurrentThread] += 16 + SrcRowBase
```

---

## 3. Format Conversion Details

### 3.1 Format Encoding

Data format is a 4-bit field. The canonical encoding is:

```
bits [1:0]: "size class"  bits [3:2]: "exp class"

0b0000 = FP32     0b0100 = TF32    0b1000 = INT32   0b1100 = (unused)
0b0001 = FP16     0b0101 = BF16    0b1001 = INT16   0b1101 = INT8
0b0010 = BFP8a    0b0110 = BFP8    0b1010 = FP8     0b1110 = (unused)
0b0011 = BFP4a    0b0111 = BFP4    0b1011 = BFP2a   0b1111 = BFP2
```

In the ISA docs the same encoding is expressed as:

| | `0b??11` | `0b??10` | `0b??01` | `0b??00` |
|---|---|---|---|---|
| **`0b00??`** | BFP4a | BFP8a | FP16 | FP32 |
| **`0b01??`** | BFP4 | BFP8 | BF16 | TF32 |
| **`0b10??`** | BFP2a | FP8 | INT16 | INT32 |
| **`0b11??`** | BFP2 | INT8 | — | — |

The DataFormat enum values in software (see `pack-unpack-registers.md`):
- `Float32=0, Float16=1, Bfp8a=2, Bfp4a=3, Tf32=4, Float16_b=5, Bfp8=6, Bfp4=7`
- `Int32=8, Int16=9, Fp8_e5m2=10, Bfp2a=11, Int8=14, Bfp2=15, UInt32=24, Fp8_e4m3=26, UInt8=30`

### 3.2 FormatConversion Pseudocode (Complete)

```python
def FormatConversion(InDataFormat, OutDataFormat, DatumBits, ExpBits, WhichUnpacker, UnpackToDst):
    """
    Returns a 19-bit value for SrcA/SrcB, or 16-bit (or 32-bit) value for Dst.
    """
    if InDataFormat == FP32:
        if OutDataFormat == FP32:
            pass  # keep DatumBits as-is (32-bit, only valid for Dst)
        elif OutDataFormat == TF32:
            if UnpackToDst:
                return WriteDstFP32(DatumBits)   # TF32 in Dst = FP32
            else:
                return WriteSrcTF32(DatumBits >> 13)  # drop low 13 bits = 10-bit mantissa
        elif OutDataFormat == BF16:
            # Flush denormals to zero
            if not (DatumBits & 0x7f800000):
                DatumBits &= 0x80000000
            DatumBits >>= 16
            InDataFormat = BF16  # fall through to BF16 path
        elif OutDataFormat == FP16:
            DatumBits = FP32ToFP16(DatumBits)
            InDataFormat = FP16
        else:
            raise UndefinedBehaviour
    else:
        # For all non-FP32 inputs, InDataFormat must equal OutDataFormat
        if InDataFormat != OutDataFormat:
            raise UndefinedBehaviour

        # Normalize to 16-bit or 32-bit
        if InDataFormat == FP8:
            # E5M2: shift left 8 bits to align in FP16 position
            DatumBits <<= 8
            InDataFormat = FP16
        elif InDataFormat == FP8_E4M3:
            # E4M3 mode selected by THCON_SEC[n]_REG1_Unp_LF8_4b_exp
            # Conversion is implementation-specific; treated as FP16
            DatumBits = FP8E4M3ToFP16(DatumBits)
            InDataFormat = FP16
        elif InDataFormat == BFP8:
            DatumBits = BFP8ToBF16(DatumBits, ExpBits)
            InDataFormat = BF16
        elif InDataFormat == BFP4:
            DatumBits = BFP8ToBF16(DatumBits << 4, ExpBits)
            InDataFormat = BF16
        elif InDataFormat == BFP2:
            DatumBits = BFP8ToBF16(DatumBits << 6, ExpBits)
            InDataFormat = BF16
        elif InDataFormat == BFP8a:
            DatumBits = BFP8aToFP16(DatumBits, ExpBits)
            InDataFormat = FP16
        elif InDataFormat == BFP4a:
            DatumBits = BFP8aToFP16(DatumBits << 4, ExpBits)
            InDataFormat = FP16
        elif InDataFormat == BFP2a:
            DatumBits = BFP8aToFP16(DatumBits << 6, ExpBits)
            InDataFormat = FP16
        elif InDataFormat == INT8:
            # INT8 sign-magnitude or UINT8 (selected by ALU_FORMAT_SPEC_REG0_SrcAUnsigned/SrcBUnsigned)
            StateID = ThreadConfig[CurrentThread].CFG_STATE_ID_StateID
            IsUnsigned = ConfigState.ALU_FORMAT_SPEC_REG0_SrcBUnsigned if WhichUnpacker else \
                         ConfigState.ALU_FORMAT_SPEC_REG0_SrcAUnsigned
            Sign = 0 if IsUnsigned else (DatumBits & 0x80)
            DatumBits -= Sign
            if DatumBits:
                DatumBits |= (16 << 10)   # dummy FP16 exponent for Integer "8" overlay
            DatumBits |= (Sign << 8)
            InDataFormat = FP16
        elif InDataFormat == TF32:
            if UnpackToDst:
                return WriteDstFP32(DatumBits)
            else:
                raise UndefinedBehaviour   # TF32 as input only valid for Dst

    # Final bit rearrangement to output format
    if InDataFormat == INT16:
        if UnpackToDst:
            return DatumBits & 0xffff
        else:
            # Rearrange INT16 to SrcA/SrcB layout: (hi<<3) | lo
            return ((DatumBits & 0xff00) << 3) | (DatumBits & 0xff)
    elif InDataFormat == INT32:
        if UnpackToDst:
            return WriteDstFP32(DatumBits)
        else:
            raise UndefinedBehaviour
    elif InDataFormat == FP32:
        if UnpackToDst:
            return WriteDstFP32(DatumBits)
        else:
            raise UndefinedBehaviour
    elif InDataFormat == BF16:
        if UnpackToDst:
            return WriteDstBF16(DatumBits)
        else:
            return WriteSrcBF16(DatumBits)
    elif InDataFormat == FP16:
        if UnpackToDst:
            return WriteDstFP16(DatumBits)
        else:
            return WriteSrcFP16(DatumBits)
```

### 3.3 Register Layout Transforms

The SrcA/SrcB register files store data in a specific bit layout different from the L1 representation. These transforms rearrange floating-point bits:

```python
# === SrcA / SrcB (19-bit elements) ===

def WriteSrcTF32(x: int) -> int:
    """TF32: 1 sign + 8 exp + 10 mant → 19-bit Src field: Sign,Mant,Exp"""
    # Input: bits [18]=Sign [17:8]=Exp [7:0]=Mant (10 bits)
    Sign = x & 0x40000   # bit 18
    Exp  = x & 0x3fc00   # bits 17:8 (8 bits)
    Man  = x & 0x003ff   # bits 7:0  (10 bits)
    return Sign | (Man << 8) | (Exp >> 10)
    # Output: [18]=Sign [17:8]=Man [7:0]=Exp

def WriteSrcBF16(x: int) -> int:
    """BF16 → TF32 Src layout (zero-extends mantissa)"""
    return WriteSrcTF32(x << 3)
    # Shifts 16-bit BF16 left by 3 to produce 19-bit TF32

def WriteSrcFP16(x: int) -> int:
    """FP16 → TF32 Src layout"""
    # FP16: Sign[15], Exp[14:10], Man[9:0] → expand to 19-bit TF32 form
    return WriteSrcTF32(((x & 0x8000) << 3) | (x & 0x7fff))

# === Dest register (16-bit or 32-bit elements) ===

def WriteDstFP16(x: int) -> int:
    """FP16 → Dst layout: Sign,Man,Exp (fields swapped)"""
    Sign = x & 0x8000
    Exp  = x & 0x7c00
    Man  = x & 0x03ff
    return Sign | (Man << 5) | (Exp >> 10)

def WriteDstBF16(x: int) -> int:
    """BF16 → Dst layout: Sign,Man,Exp (fields swapped)"""
    Sign = x & 0x8000
    Exp  = x & 0x7f80
    Man  = x & 0x007f
    return Sign | (Man << 8) | (Exp >> 7)

def WriteDstFP32(x: int) -> int:
    """FP32 → Dst layout: WriteDstBF16 applied to high 16 bits, low 16 unchanged"""
    Hi = WriteDstBF16(x >> 16)
    Lo = x & 0xffff
    return (Hi << 16) | Lo
```

### 3.4 BFP to Floating-Point Conversion

```python
def BFP8ToBF16(DatumBits: int, ExpBits: int) -> int:
    """BFP8 (B-exponent) → BF16"""
    Sign = DatumBits >> 7          # 1 bit
    Mag  = (DatumBits & 0x7f) << 1 # 7-bit magnitude, shift left by 1 = 8 bits
    if Mag == 0:
        return 0xff80 if Sign else 0   # ±Infinity / ±0
    LZ = count_leading_zeros_8bit(Mag)
    Mag = (Mag << LZ) & 0xff
    ExpBits -= LZ
    return (Sign << 15) | (ExpBits << 7) | (Mag & 0x7e)

def BFP8aToFP16(DatumBits: int, ExpBits: int) -> int:
    """BFP8a (A-exponent, 5-bit exponent field) → FP16"""
    Sign = DatumBits >> 7
    Mag  = (DatumBits & 0x7f) << 1
    if Mag == 0:
        return 0xfc00 if Sign else 0
    LZ = count_leading_zeros_8bit(Mag)
    Mag = (Mag << LZ) & 0xff
    ExpBits -= LZ
    # ExpBits must fit in 5 bits (no bits in 0xe0 range)
    assert not (ExpBits & 0xe0), "ExpBits overflow"
    return (Sign << 15) | (ExpBits << 10) | ((Mag & 0x7e) << 3)

# BFP4/BFP2 use the same routines with pre-shifted DatumBits:
# BFP4→BF16:  BFP8ToBF16(DatumBits << 4, ExpBits)
# BFP2→BF16:  BFP8ToBF16(DatumBits << 6, ExpBits)
# BFP4a→FP16: BFP8aToFP16(DatumBits << 4, ExpBits)
# BFP2a→FP16: BFP8aToFP16(DatumBits << 6, ExpBits)
```

### 3.5 Format Conversion Table (Summary)

| L1 Input | Config (In=Out unless noted) | SrcA/SrcB output | Dst output |
|---|---|---|---|
| FP32 | `FP32→TF32` | TF32 (19-bit) | FP32 (32-bit) |
| FP32 | `FP32→BF16` | BF16 in TF32 (19-bit) | BF16 (16-bit) |
| FP32 | `FP32→FP16` | FP16 in TF32 (19-bit) | FP16 (16-bit) |
| TF32 | `FP32→TF32` | TF32 (same) | FP32 (32-bit) |
| BF16 | `BF16` | BF16 in TF32 | BF16 (16-bit) |
| BFP8 | `BFP8` | BFP8→BF16 in TF32 | BFP8→BF16 (16-bit) |
| BFP4 | `BFP4` | BFP4→BF16 in TF32 | BFP4→BF16 (16-bit) |
| BFP2 | `BFP2` | BFP2→BF16 in TF32 | BFP2→BF16 (16-bit) |
| BFP8a | `BFP8a` | BFP8a→FP16 in TF32 | BFP8a→FP16 (16-bit) |
| BFP4a | `BFP4a` | BFP4a→FP16 in TF32 | BFP4a→FP16 (16-bit) |
| BFP2a | `BFP2a` | BFP2a→FP16 in TF32 | BFP2a→FP16 (16-bit) |
| FP16 | `FP16` | FP16 in TF32 | FP16 (16-bit) |
| FP8 E5M2 | `FP8` | FP8→FP16 in TF32 | FP8→FP16 (16-bit) |
| INT8 (s-mag) | `BFP8` + Force_shared_exp | INT8→BF16 in TF32 | INT8→BF16 |
| INT8 | `INT8` | Int8 overlay on FP16 | Int8 (16-bit) |
| UINT8 | `INT8` (SrcAUnsigned=1) | UInt8 overlay | UInt8 (16-bit) |
| INT16 | `INT16` | Opaque 16-bit rearranged | INT16 (16-bit) |
| INT32 | `INT32` | Not possible | INT32 (32-bit) |

---

## 4. ADC Counter Mechanics

### 4.1 ADC State Structure

Each of 3 Tensix threads has its own ADC state. Each ADC has entries for Unpacker 0, Unpacker 1, and Packers, each with 2 channels:

```c
struct {
    struct {
        struct {
            uint18_t X, X_Cr;   // X counter and checkpoint
            uint13_t Y, Y_Cr;   // Y counter and checkpoint
            uint8_t  Z, Z_Cr;   // Z counter and checkpoint
            uint8_t  W, W_Cr;   // W counter and checkpoint
        } Channel[2];
    } Unpacker[2], Packers;
} ADCs[3];  // one per thread
```

Checkpoint values (`_Cr`) are used by `ADDRCRZW`/`ADDRCRXY` for ADC reset operations.

### 4.2 Channel Usage

| Counter | Channel 0 | Channel 1 |
|---------|-----------|-----------|
| X | L1 input position within current row | End-of-row boundary (XEnd - 1) |
| Y | L1 row position within Z-face | Output Y position (Ystride multiplier) |
| Z | L1 Z-face (face index within tile) | Output Z position (Zstride multiplier) |
| W | L1 W-face | Output W position (Wstride multiplier) |

**Channel 0** drives the L1 read address: which face (Z), which row (Y), which element within the row (X).

**Channel 1** drives the Src/Dst write address:
- `X1` = end of row (= face_r_dim × face_c_dim − 1); the number of elements to write
- `Y1, Z1, W1` = output face/row position (combined with strides to form byte offset)

### 4.3 Instructions

#### SETADC — Set one counter
```c
TT_SETADC(target_mask,   // bits: PK=bit2, U1=bit1, U0=bit0
          channel,        // 0 or 1
          xyzw,           // 0=X, 1=Y, 2=Z, 3=W
          new_value)      // 18-bit; bits[17:16] = ThreadOverride
```

Sets the specified counter and its checkpoint (`X_Cr`, `Y_Cr`, etc.).

ThreadOverride (bits [17:16] of new_value):
- `0` = CurrentThread
- `1..3` = thread 0..2

#### SETADCXY — Set X and Y counters together
```c
TT_SETADCXY(target_mask,
            Y1Val, X1Val, Y0Val, X0Val,   // 3-bit each
            bit_mask)  // bits: Y1=3, X1=2, Y0=1, X0=0 — which to update
```

#### SETADCZW — Set Z and W counters together
```c
TT_SETADCZW(target_mask,
            W1Val, Z1Val, W0Val, Z0Val,   // 3-bit each
            bit_mask)  // bits: W1=3, Z1=2, W0=1, Z0=0
```

#### SETADCXX — Set both X counters (wider range)
```c
TT_SETADCXX(target_mask,
            X1Val,   // 10-bit: end-of-row for channel 1 (XEnd-1)
            X0Val)   // 10-bit: start-of-row for channel 0
```

Used to program `Channel[1].X = face_r_dim * face_c_dim - 1` (the datum count boundary).

#### INCADCXY / INCADCZW — Increment counters
```c
TT_INCADCXY(target_mask, Y1Inc, X1Inc, Y0Inc, X0Inc)
TT_INCADCZW(target_mask, W1Inc, Z1Inc, W0Inc, Z0Inc)
```

Adds the increment to the current counter value. Used during untilize to advance Y pointer row-by-row.

#### ADDRCRXY / ADDRCRZW — Restore checkpoint values
```c
TT_ADDRCRZW(target_mask, W1, Z1, W0, Z0, bit_mask)
```

Restores selected counters from their checkpoint (`_Cr`) values. Used in untilize mode to reset the Z counter back to its starting face after completing each row.

### 4.4 How ADC Drives Tile Traversal

Standard face-by-face unpacking of a 32×32 tile (4 faces of 16×16):

```
Init:
  SETADCZW(UNP_AB, 0,0,0,0, 0b1111)  // Z0=0, W0=0, Z1=0, W1=0
  SETADCXY(UNP_AB, 0,0,0,0, 0b1011)  // X0=0, Y0=0, Y1=0 (X1 already set by SETADCXX)
  SETADCXX(UNP_A, face_r_dim*16-1, 0)  // X1 = 255 for 16-row face

Per UNPACR (Ch1ZInc=1 advances to next face in SrcA):
  - UNPACR reads XDim=256 datums starting at Z0*face, writes to SrcA starting at SrcRow
  - Ch0ZInc=1: Z0 increments after each UNPACR, selecting next face in L1
  - Ch1ZInc=1: Z1 increments, selecting next output row group in SrcA
```

For tilize mode, Y0 advances via `INCADCXY` to move to the next L1 row, while Z0 is reset with `ADDRCRZW`.

---

## 5. Tilize Mode

### 5.1 What Tilize Does

**Tilize** converts **row-major** input data (a normal 2D array in L1) into the tile layout expected by SrcA. The input data is NOT in tile format — it is laid out as a contiguous 2D array where each row has `block_c_dim` elements.

`tileize_mode = 1` in `unpack_config_t` enables tilize. The unpacker reads one row of 16 elements at a time from L1 (one 1×16 sub-row of a face), then jumps by `RowStride` bytes to the next row in L1.

`RowStride` is computed from `Shift_amount_cntx[0..2]` fields and equals `block_c_dim * DatumSizeBytes`. This is the byte distance between adjacent rows in the L1 row-major layout.

### 5.2 Tilize Configuration

```c
// From _llk_unpack_tilize_init_():
config.f.tileize_mode = 1;
config.f.shift_amount = (SCALE_DATUM_SIZE(src_format, block_c_dim)) >> 4;
// shift_amount = (block_c_dim * bytes_per_datum) / 16
// RowStride = shift_amount << 4 = block_c_dim * bytes_per_datum

// Tile x_dim set to cover entire tile row (all faces in X direction):
Tile_x_dim = face_r_dim * num_faces * FACE_C_DIM;
// z_dim = 1 (the entire tile is treated as one Z-slice)
Tile_z_dim = 1;

// ADC: X end covers entire tile row
SETADCXX(UNP0, Tile_x_dim - 1, 0);
```

Each UNPACR call in tilize mode reads `Tile_x_dim` elements, skipping `RowStride` bytes between each 16-element sub-row. The result is that 16-element rows spaced throughout the L1 block get concatenated into a single SrcA row, effectively assembling the tile face-by-face.

### 5.3 TilizeA+B

The `_llk_unpack_tilizeA_B_` variant unpacks SrcA one 1×16 row at a time (with `UNPACR CH1_Y+=1` to advance the SrcA destination row). For each face:
- SrcB is loaded once for the entire face
- SrcA rows are loaded individually using a replay buffer

Face layout in L1 for tilizeA+B:
```
Face 0 top-left:  base_address + tile_index * datum_size
Face 0 top-right: base_address + tile_index * datum_size + face_c_dim * datum_size
Face 1 top-left:  base_address + block_c_dim * tile_height * datum_size + ...
Face 1 top-right: ...
```

---

## 6. Untilize Mode

**Untilize** reads SrcA-style tiled data from L1 and writes it row-major to SrcA (in the sense of presenting it row by row for math operations). It is the inverse of tilize.

The untilize loop reads 1×16 element rows from L1, using:
- `INCADCXY(UNP0, CH1_Y+=1, CH0_Z+=1)` to advance both the L1 Z-pointer and SrcA Y-pointer
- `ADDRCRZW(CH0_Z)` to reset Z back to its start when a new L1 face column starts
- `WRCFG` to update the L1 tile offset register (`THCON_SEC0_REG7_Offset_address`) for the next tile

The `_llk_unpack_untilize_pass_` function iterates over `FACE_HEIGHT=16` rows, with an inner loop over tiles in the row. The MOP contains:

```c
DMANOP;
UNPACR(SrcA, CH1_Y+=1, CH0_Z+=1);   // unpack 2 adjacent 1x16 rows
UNPACR(SrcA, CH1_Y+=1, CH0_Z+=1);
ADDDMAREG(TILE_OFFSET, TILE_OFFSET, TILE_SIZE);  // advance to next tile
STALLWAIT(STALL_CFG, THCON);
ADDRCRZW(CH0_Z);                     // reset Z counter to checkpoint
```

---

## 7. Unpack-to-Dest Mode

### 7.1 When Used

Unpacker 0 can write directly to Dest instead of SrcA. This is used for:
- 32-bit data types (FP32, INT32, UInt32) — only writable via unpack-to-dest
- Tilize with FP32 input
- Reducing latency by bypassing the SrcA→math→Dest path

### 7.2 Control Bits

Mode is selected by:
- **Non-MultiContextMode**: `REG2_Unpack_If_Sel` (bit 11 in ADDR32 72)
- **MultiContextMode**: `REG2_Unpack_if_sel_cntx[WhichContext]` (bits in ADDR32 73)

### 7.3 UNPACK_TO_DEST Semaphore Protocol

Semaphore `UNPACK_TO_DEST` (semaphore index defined in `ckernel_defs.h`) synchronizes the unpack-to-dest path with the math thread:

```c
// TRISC0 (unpack thread) before starting unpack-to-dest:
wait_for_dest_available():
    t6_semaphore_wait_on_max<STALL_UNPACK>(semaphore::UNPACK_TO_DEST)
    // Blocks until UNPACK_TO_DEST count is < max (Dest is not currently occupied)

// TRISC0 after unpack-to-dest tile done:
unpack_to_dest_tile_done(context_id):
    t6_semaphore_post<UNPACK0>(semaphore::UNPACK_TO_DEST)
    // Signals Dest has been written
    // Also restores stride and context config
```

The math thread (TRISC1) signals when Dest processing is complete, allowing the unpack thread to write the next tile.

### 7.4 Dest Address Setup

```c
// From set_dst_write_addr():
dst_byte_addr = 16 * (4 + mailbox_read(ThreadId::MathThreadId))
// MathThreadId is a value in [0, 7] selecting which 16-row block of Dest to write

TTI_SETC16(SRCA_SET_Base_ADDR32, 0x0)  // disable address bit swizzle for Dest
// Program per-context dest address:
cfg[THCON_SEC0_REG5_Dest_cntx[ctx]_address] = dst_byte_addr
// Set Unpack_if_sel_cntx[ctx] = 1
cfg_reg_rmw(THCON_SEC0_REG2_Unpack_if_sel_cntxN_RMW, 1)
```

The `Dest_cntx_address` field programs the starting byte offset in Dest. This is combined with `OutAddr` (from ADC Channel 1) using the `ADD_DEST_ADDR_CNTR` enable bit.

### 7.5 Destination Write Order

In unpack-to-dest mode, `OutAddr` directly indexes Dest rows and columns:

```python
# In the unpack loop:
Row = (OutAddr // 16 - 4) & 0x3ff  # subtract 4-row header offset, mask to 10-bit
Col = OutAddr & 15

if OutDataFormat in (FP32, TF32, INT32):
    Dst32b[Row][Col] = Datum   # 32-bit write
else:
    Dst16b[Row][Col] = Datum   # 16-bit write
```

The `-4` row offset is fixed hardware behavior. The `OutAddr` is initialized from `CtxOutAddr` (Dest_cntx address) rather than the Src row tracking used in SrcA writes.

---

## 8. UNPACR_NOP Functional Model

`UNPACR_NOP` is a family of side-channel instructions that operate within the unpacker pipeline, sequenced after previous UNPACR instructions. They share the same execution unit as UNPACR.

### 8.1 Mode Encoding

| Mode bits [4:0] | Operation |
|-----------------|-----------|
| `0b00000` (0x0) | OverlayClear (pop stream message, using `NOC_OVERLAY_MSG_CLEAR_StreamId`) |
| `0b00001` (0x1) | ZEROSRC — zero out a SrcA/SrcB bank |
| `0b00010` (0x2) | Nop — occupy unpacker for one cycle |
| `0b00011` (0x3) | OverlayClear with explicit stream + count |
| `0b00100` (0x4) | SETREG — MMIO register write |
| `0b00111` (0x7) | SETDVALID — transfer bank to MatrixUnit |

### 8.2 SETDVALID (0x7)

```c
TT_UNPACR_NOP(WhichUnpacker, 0x7)
```

Functionally equivalent to SETDVALID but sequenced through the unpacker pipeline:

```python
if WhichUnpacker == 0:
    SrcA[Unpackers[0].SrcBank].AllowedClient = MatrixUnit
    Unpackers[0].SrcBank ^= 1
    Unpackers[0].SrcRow[CurrentThread] = ThreadConfig[CurrentThread].SRCA_SET_Base << 4
else:
    SrcB[Unpackers[1].SrcBank].AllowedClient = MatrixUnit
    Unpackers[1].SrcBank ^= 1
    Unpackers[1].SrcRow[CurrentThread] = ThreadConfig[CurrentThread].SRCB_SET_Base << 4
```

Does **not** automatically wait for `AllowedClient == Unpackers`. Use `STALLWAIT` before if needed (block B3, condition C10 or C11).

### 8.3 ZEROSRC (0x1)

```c
TT_UNPACR_NOP(WhichUnpacker,
              ((WaitLikeUnpacr) << 4) +
              ((BothBanks)      << 3) +
              ((NegativeInfSrcA)<< 2) +
              0x1)
```

Clears SrcA or SrcB to zeros (or negative infinity for SrcA):

```python
UnpackBank = Unpackers[WhichUnpacker].SrcBank

# Wait for bank access (either unpack bank or math bank)
if WhichUnpacker == 0:
    target_bank = UnpackBank if WaitLikeUnpacr else MatrixUnit.SrcABank
    while SrcA[target_bank].AllowedClient != Unpackers: wait
else:
    target_bank = UnpackBank if WaitLikeUnpacr else MatrixUnit.SrcBBank
    while SrcB[target_bank].AllowedClient != Unpackers: wait

# Clear
for bank in range(2):
    if BothBanks or bank == UnpackBank:
        ClearVal = ~0 if (WhichUnpacker == 0 and NegativeInfSrcA) else 0
        for row in range(64):
            for col in range(16):
                (SrcA if WhichUnpacker == 0 else SrcB)[bank][row][col] = ClearVal
```

### 8.4 OverlayClear (0x0 and 0x3)

Pops a message from a NoC Overlay stream. Used in the unpack thread to acknowledge CB message consumption:

```python
# Mode 0x0: use StreamId from ThreadConfig
StreamId = ThreadConfig[CurrentThread].NOC_OVERLAY_MSG_CLEAR_StreamId[WhichUnpacker]
NOC_STREAM_WRITE_REG(StreamId, STREAM_MSG_DATA_CLEAR_REG_INDEX, 1)

# Mode 0x3: explicit stream and count
TT_UNPACR_NOP(WhichUnpacker,
              ((WhichStream) << 16) + ((ClearCount) << 4) + 0x3)
# Clears 'ClearCount' messages from 'WhichStream'
```

### 8.5 SETREG (0x4)

Writes a value to an MMIO register once previous UNPACR L1 reads complete:

```python
Addr = 0xFFB00000 + Unpackers.SetRegBase[AddrSel] + (AddrMid << 12)
if Accumulate:
    AccValue = Unpackers[WhichUnpacker].SetRegAcc
    if Value11 == 0:
        AccValue = 0
    else:
        AccValue = (AccValue + Value11) & 0x1ffff
        write32(Addr, AccValue)
    Unpackers[WhichUnpacker].SetRegAcc = AccValue
else:
    write32(Addr, Value11)
```

Used for stream consumer count updates and similar MMIO side effects synchronized with unpack.

---

## 9. Config Context Switching

### 9.1 Why Double-Buffered Config?

The Tensix unpacker uses a **double-buffered configuration** to allow TRISC0 to set up the next tile's config while the previous tile is still being unpacked. This is necessary because UNPACR reads tile config registers (base address, format, XDim, etc.) when it executes, but TRISC0 must write those registers before issuing the UNPACR.

The hardware supports **8 contexts** (for Unpacker 0; only 2 for Unpacker 1). In practice, software uses 2 contexts (a ping-pong pair).

### 9.2 Config Ping-Pong Protocol

State tracked in software: `unp_cfg_context` (global in `ckernel_globals.h`, 0 or 1).

```
Context 0:
  THCON_SEC0_REG3_Base_address         = tile_A_address (context 0)
  THCON_SEC0_REG7_Offset_address       = tile_A_offset  (context 0)

Context 1:
  THCON_SEC0_REG3_Base_cntx1_address   = tile_B_address (context 1)
  THCON_SEC0_REG7_Offset_cntx1_address = tile_B_offset  (context 1)
```

The `THCON_SEC0_REG5_Dest_cntx[N]_address` and `THCON_SEC0_REG5_Tile_x_dim_cntx[N]` registers hold per-context values for Unpacker 0. Unpacker 1 only uses contexts 0 and 1 for its base addresses.

### 9.3 CfgContextOffset (ADDR32 41)

`UNPACK_MISC_CFG` at ADDR32 41 selects which config context the unpacker accesses:

| Bits | Field | Description |
|------|-------|-------------|
| [3:0] | `CfgContextOffset_0` | Context offset for Unpacker 0 |
| [4] | `CfgContextCntReset_0` | Reset context counter (Unpacker 0) |
| [5] | `CfgContextCntInc_0` | Increment context counter each UNPACR (Unpacker 0) |
| [11:8] | `CfgContextOffset_1` | Context offset for Unpacker 1 |
| [12] | `CfgContextCntReset_1` | Reset context counter (Unpacker 1) |
| [13] | `CfgContextCntInc_1` | Increment context counter (Unpacker 1) |

These are written with `SETC16` at ADDR32 41:

```c
// Context 0 active (both unpackers):
TTI_SETC16(UNPACK_MISC_CFG_CfgContextOffset_0_ADDR32, 0x0000)
// Encoding: [7:0]=offset0=0, [15:8]=offset1=0

// Context 1 active (both unpackers):
TTI_SETC16(UNPACK_MISC_CFG_CfgContextOffset_0_ADDR32, 0x0101)
// Encoding: [7:0]=offset0=1, [15:8]=offset1=1

// During unpacker_iteration_cleanup (ping-pong):
// context=1: TTI_SETC16(addr, 0x0104)  ← offset0=4, offset1=1
// context=0: TTI_SETC16(addr, 0x0000)  ← offset0=0, offset1=0

// At wrapup (reset both to non-overlapping):
TTI_SETC16(addr, 0x1010)   // unusual cleanup state
```

### 9.4 Switch Sequence

From `switch_config_context()`:

```c
void switch_config_context(uint32_t &unp_cfg_context) {
    unp_cfg_context = 1 - unp_cfg_context;
    if (unp_cfg_context == 0) {
        TTI_SETC16(UNPACK_MISC_CFG_CfgContextOffset_0_ADDR32, 0x0000);
    } else {
        TTI_SETC16(UNPACK_MISC_CFG_CfgContextOffset_0_ADDR32, 0x0101);
    }
}
```

### 9.5 Full Double-Buffer Sequence (Per Tile)

```
TRISC0 (unpack loop per tile):
  1. wait_for_next_context(2)
        → spins until semaphore::UNPACK_SYNC < 2
        (ensures at most 2 contexts are "in flight")
  2. Write tile address to cfg:
        if unp_cfg_context == 0:
            cfg[THCON_SEC0_REG3_Base_address] = L1_addr_A
            cfg[THCON_SEC1_REG3_Base_address] = L1_addr_B
        else:
            cfg[THCON_SEC0_REG3_Base_cntx1_address] = L1_addr_A
            cfg[THCON_SEC1_REG3_Base_cntx1_address] = L1_addr_B
  3. semaphore_post(UNPACK_SYNC)  ← "I have a context ready"
  4. TTI_STALLWAIT(STALL_UNPACK, TRISC_CFG)  ← wait for CFG writes to propagate
  5. Execute MOP (UNPACR instructions)
  6. t6_semaphore_get(UNPACK_SYNC)  ← "context is consumed"
  7. switch_config_context(unp_cfg_context)
```

The T6 `semaphore_get` happens within the MOP/UNPACR instruction itself (the `FlipSrc` flag or UNPACR_NOP_SETDVALID transfers ownership and implicitly synchronizes). The TRISC0 `t6_semaphore_get` in step 6 acknowledges context release from the coprocessor side.

---

## 10. UNPACR Instruction Context Counter Mode

When `UseContextCounter = true` and `MultiContextMode = true`:

```python
# Before UNPACR executes:
WhichContext = CurrentUnpacker.ContextCounter[CurrentThread]
WhichContext += ThreadConfig[CurrentThread].UNPACK_MISC_CFG_CfgContextOffset[WhichUnpacker]

# After UNPACR executes:
IncrementedCounter = WhichContext + 1
if IncrementedCounter >= (1 << Context_count):
    IncrementedCounter = 0
CurrentUnpacker.ContextCounter[CurrentThread] = IncrementedCounter
```

The context counter automatically cycles through 0..(`2^Context_count - 1`), where `Context_count` is a 2-bit field (0=max 1 context, 1=2, 2=4, 3=8 contexts).

The `UNPACR (Increment context counter)` instruction variant just increments the counter without performing any unpack:

```c
TT_OP_UNPACR(WhichUnpacker, 0, true, 0, 0, false, false, false, false, false, false, false)
```

---

## 11. Real Instruction Sequences (Annotated)

### 11.1 Initialization Sequence (from add1/matmul TRISC0)

This sequence runs once at startup to initialize the unpack configuration. Observed in both `add1_trisc0.S` and `matmul_trisc0.S`:

```asm
; === ADC reset ===
5f48:  ttsetadcxy  3,0,0,0,0,11    ; SETADCXY(UNP_AB, Y1=0,X1=0,Y0=0,X0=0, mask=0b1011)
                                    ; Resets X0, Y0, Y1 for both unpackers (bit 0=X0, 1=Y0, 3=Y1)
5f4c:  ttsetadczw  3,0,0,0,0,15    ; SETADCZW(UNP_AB, W1=0,Z1=0,W0=0,Z0=0, mask=0b1111)
                                    ; Resets all Z/W counters

; === Config register writes via instrn_buffer ===
; (These are stores to 0xFFE40000 = __instrn_buffer, raw 32-bit instruction words)
5f70:  ttatgetm  0                 ; Acquire mutex 0 (REG_RMW mutex)

; Store ALU format/config words via buffer:
5f7c:  sw a4, 0(a0)  → 0xb3ff0... ; WRCFG: ALU_FORMAT_SPEC_REG (ADDR32=0)
5f84:  sw a4, 0(a0)  → 0xb47f0... ; WRCFG: ADDR32=1 (ALU_FORMAT_SPEC_REG + rounding)
5f8c:  sw a4, 0(a0)  → 0xb3070001 ; WRCFG+1b: Disable zero compress flags
5f98:  sw a4, 0(a0)  → 0xb4800001 ; WRCFG: another format spec
5fa4:  sw a4, 0(a0)  → 0xb5010001 ; WRCFG: THCON_SEC0/1 config
5fb0:  sw a4, 0(a0)  → 0xb6600001 ; WRCFG: more config
5fb8:  sw a4, 0(a0)  → 0xb3010002 ; WRCFG: out_data_format + throttle

5fc8:  ttatrelm  0                 ; Release mutex 0

; === Address stride config ===
; (Direct memory writes to instrn_buffer region at various offsets)
; UNP0_ADDR_CTRL_ZW_REG_1_Zstride (ADDR32=57): z-stride for output channel
; UNP1_ADDR_CTRL_ZW_REG_1_Zstride (ADDR32=59): z-stride for SrcB output channel

; === Tile descriptor writes ===
; (Writes to THCON_SEC0_REG0_TileDescriptor at ADDR32=64)

; === Per-context dim config ===
; THCON_SEC0_REG5_Tile_x_dim_cntx0 (ADDR32=86)
; THCON_SEC0_REG5_Dest_cntx0_address (ADDR32=84)

; === ADC x_end ===
60c0:  ttsetadcxx  1,255,0         ; SETADCXX(UNP_A, X1=255, X0=0)
                                    ; X1=255 = face_r_dim*face_c_dim-1 = 16*16-1

; === Context reset ===
6074:  ttsetc16  5,4               ; SETC16 at ADDR32=5 (SRCA_SET_Base), value=4
                                    ; Sets SrcA base row = 4 (skip 4-row header)
6088:  ttsetc16  41,0              ; SETC16 at ADDR32=41 (UNPACK_MISC_CFG), value=0
                                    ; Reset config context to 0
```

### 11.2 Per-Tile Unpack Loop (add1)

The add1 kernel unpacks one tile of SrcA and one tile of SrcB per iteration:

```asm
; === Wait for idle (previous contexts consumed) ===
; (Busy-wait loop checking semaphore::UNPACK_SYNC)

61c4:  ttsetadczw  3,0,0,0,0,15   ; Reset Z/W counters for both unpackers

; === Write tile addresses to config ===
; (RISC-V stores to THCON_SEC0_REG3_Base_address and THCON_SEC1_REG3_Base_address)

61e0:  sw zero, 52(a3)             ; Clear instrn_buffer+0x34 (busy flag / semaphore reg)

; === Issue UNPACR + MOP ===
61e4:  ttstallwait  8,1024         ; STALLWAIT(STALL_UNPACK, TRISC_CFG)
                                    ; Block unpacker until TRISC CFG writes complete
                                    ; (condition 1024 = TRISC_CFG, block 8 = STALL_UNPACK)

61e8:  ttmop  1,0,0                ; Execute MOP program
                                    ; The MOP contains UNPACR instructions for SrcA+SrcB

61ec:  ttsemget  32                ; t6_semaphore_get(semaphore::UNPACK_SYNC)
                                    ; Context released (coprocessor acknowledges)

61f4:  ttsetc16  41,257            ; SETC16 UNPACK_MISC_CFG=0x0101
                                    ; Switch to context 1 (CfgContextOffset_0=1, _1=1)
```

### 11.3 Matmul Unpack SrcB (with per-tile address accumulation)

The matmul kernel increments SrcB tile addresses using SETREG-style RDCFG/ADDDMAREG/WRCFG:

```asm
; Replay buffer programs SrcB address update per face:
611c:  ttreplay  0,12,0,1          ; Execute replay buffer len=12 from position 0

; Replay buffer contents:
6120:  ttunpacr  1,0,0,0,0,1,1,0,0,0,0,0,1   ; UNPACR SrcB: Ch0ZInc=0, FlipSrc=1
                                               ; (WhichUnpacker=1, Ch1YInc=0, Ch1ZInc=0,
                                               ;  Ch0YInc=0, Ch0ZInc=0, no FlushCache,
                                               ;  ContextNum=0, ContextADC=0,
                                               ;  MultiContextMode=1, FlipSrc=1,
                                               ;  no extra flags)

6124:  ttrdcfg  12,124             ; RDCFG r12, ADDR32=124 (THCON_SEC1_REG3_Base_address)
                                    ; Read SrcB base address into register r12

6128:  ttadddmareg  0,12,12,18     ; ADDDMAREG r12 = r12 + r18
                                    ; r18 = tile_size_B (preloaded)
                                    ; Advance base address by one tile

612c:  ttstallwait  128,1          ; STALLWAIT(STALL_CFG, UNPACK1)
                                    ; Wait for unpacker 1 to be idle before writing config

6130:  ttwrcfg  12,0,124           ; WRCFG ADDR32=124, r12
                                    ; Write updated SrcB address back

6134:  ttnop

6138:  ttunpacr  1,...              ; Next SrcB face
6140+: ; Repeat for second context (cntx1_address ADDR32=125)
```

### 11.4 Matmul Unpack SrcA (single face per UNPACR)

```asm
; Inside tile loop:
62ac:  ttstallwait  8,1024         ; Wait for TRISC_CFG writes to propagate
62b0:  ttunpacr  0,0,0,0,0,1,1,0,0,0,0,0,1
       ; UNPACR(SrcA, Ch1ZInc=0,Ch1YInc=0,Ch0ZInc=0,Ch0YInc=0,
       ;        no_flush_cache, ctx_num=0, ctx_adc=0,
       ;        MultiContextMode=1, FlipSrc=1, ...)
       ; Unpacks one face from L1 to SrcA, then flips bank to MatrixUnit

62c0:  ttsemget  32                ; Release context semaphore

62d0:  ttsetc16  41,0              ; Switch config context back to 0
```

### 11.5 Config Context Switch Pattern

The observed binary pattern in both kernels:

```asm
; Context 0→1:
ttsetc16  41, 257    ; 257 = 0x101 → UNPACK_MISC_CFG offset0=1, offset1=1

; Context 1→0:
ttsetc16  41, 0      ; 0 = 0x000 → UNPACK_MISC_CFG offset0=0, offset1=0
```

---

## 12. Upsampling Mode

Controlled by `upsample_rate` (2-bit) and `upsample_and_interleave` (1-bit) in `unpack_config_t`:

| `upsample_rate` | `upsample_and_interleave` | Effect |
|---|---|---|
| 0 | Any | No upsampling |
| 1 | false | Insert 1 zero after every datum |
| 2 | false | Insert 2 zeros after every datum |
| 3 | false | Insert 4 zeros after every datum |
| 1 | true | Skip 1 output position after every datum |
| 2 | true | Skip 2 output positions after every datum |
| 3 | true | Skip 4 output positions after every datum |

```python
UpsampleZeroes = (1 << upsample_rate) - 1  # 0, 1, 2, or 4 zeros to insert

for j in range(UpsampleZeroes + 1):
    datum_to_write = Datum if j == 0 else 0
    if upsample_and_interleave and j != 0:
        OutAddr += 1   # skip position (don't write)
        continue
    write_to_output(OutAddr, datum_to_write)
    OutAddr += 1
```

---

## 13. Performance Characteristics

### L1 Bandwidth

Each unpacker has three speed tiers:
- **x1**: Up to 16 bytes/cycle
- **x2**: Up to 32 bytes/cycle
- **x4**: Up to 64 bytes/cycle

Configured by `Throttle_mode` field (0=x1, 1=x2, 2=x4). Default in LLK code: `throttle_mode = 2` (x4).

When both unpackers are active simultaneously, they share L1 bandwidth per the interference table in the ISA docs (see `UNPACR_Regular.md`).

### Forced Speed Constraints

Certain modes force lower bandwidth:
- `DiscontiguousInputRows` (tilize): always x4
- `!IsUncompressed` (compressed data): always x1
- `UpsampleZeroes == 3` (4 zeros per datum): always x1
- `BFP2 / BFP2a`: always x1
- `UpsampleZeroes == 1` (2 zeros): x1 or x2

### Initial Latency

Every UNPACR instruction incurs at least 2 cycles of address computation before L1 reads begin. During these cycles, no other thread can issue UNPACR (shared frontend resource). Compressed data incurs additional cycles.

---

## 14. Emulator Implementation Notes

### 14.1 State to Track

```python
class UnpackerState:
    SrcBank: int                # 0 or 1, current write bank
    SrcRow: list[int]           # [thread0_row, thread1_row, thread2_row]
    ContextCounter: list[int]   # [thread0_ctx, thread1_ctx, thread2_ctx]
    SetRegAcc: int              # Accumulated SETREG value

class ADCChannel:
    X: int;  X_Cr: int
    Y: int;  Y_Cr: int
    Z: int;  Z_Cr: int
    W: int;  W_Cr: int

class ADCEntry:
    Channel: list[ADCChannel]   # [channel0, channel1]

class ADCState:
    Unpacker: list[ADCEntry]    # [unpacker0, unpacker1]
    Packers: ADCEntry

ADCs: list[ADCState]            # [thread0, thread1, thread2]
Unpackers: list[UnpackerState]  # [unpacker0, unpacker1]
```

### 14.2 Key Emulation Points

1. **L1 Circular Buffer**: Implement `WrapAddr(addr)` using `limit_addr` and `fifo_size` from config. The wrapping is used for both data and exponent pointers.

2. **19-bit SrcA/SrcB storage**: Values are stored in the rearranged bit layout (Sign,Mantissa,Exponent rather than Sign,Exponent,Mantissa). Always apply `WriteSrcTF32()` / `WriteSrcBF16()` / `WriteSrcFP16()` before storing.

3. **Row offset in SrcA**: The SrcA register file conceptually starts at row 0, but the unpacker computes `Row = (OutAddr/16 - 4) + SrcRow[thread]`. The `-4` is a hardware-fixed offset. Rows 0-3 of the output address space are skipped/header.

4. **SrcRow tracking**: `SrcRow` advances by 16 after each UNPACR (when `Unpack_Src_Reg_Set_Upd = 1`) and resets to `SRCA_SET_Base << 4` on bank flip. In the typical 4-face tile unpack (4 UNPACR calls before `FlipSrc`), `SrcRow` advances 0, 16, 32, 48, then resets on flip.

5. **Bank ownership**: Before any write, check `SrcA[bank].AllowedClient == UNPACKERS`. The bank starts owned by Unpackers, is transferred to MatrixUnit on `FlipSrc` or `UNPACR_NOP_SETDVALID`, and returns to Unpackers after math processes it (via `CLEARDVALID` or equivalent).

6. **ColShift**: In non-tilize, non-SrcB mode, `ColShift = Shift_amount_cntx[WhichContext & 3]`. Skip elements where `Col < ColShift`. Used for partial-row unpacking.

7. **Exponent pointer alignment**: The exponent pointer uses fractional arithmetic (advances by 1/16 per datum). In practice, use integer counters: maintain an exponent index `exp_idx` that increments by 1 every 16 datums, starting at `FirstDatum / 16`.

8. **Compressed data**: The RSI (row start index) array is a sequence of `uint16_t` values in L1. RSI[i] gives the byte offset (from the start of the datum stream) of compressed row i. The decompressor uses RLE nibbles interleaved 32-per-block.

9. **FP8 E4M3 mode**: Enabled by `THCON_SEC[n]_REG1_Unp_LF8_4b_exp`. When set, FP8 input is interpreted as E4M3 instead of E5M2. The conversion to FP16 differs significantly.

10. **Context counter wrap**: `Context_count` is a 2-bit field; the counter wraps at `2^Context_count` (i.e., 1, 2, 4, or 8).

### 14.3 Simplified UNPACR Dispatch Logic

```python
def emulate_UNPACR(WhichUnpacker, Ch0YInc, Ch0ZInc, Ch1YInc, Ch1ZInc,
                   ContextNumber, ContextADC, MultiContextMode, FlipSrc,
                   AllDatumsAreZero, UseContextCounter, RowSearch):
    """Core UNPACR emulation."""
    cfg = get_config_for_current_thread()

    # 1. Context selection
    ctx = select_context(WhichUnpacker, MultiContextMode, UseContextCounter,
                         ContextNumber, ContextADC)

    # 2. Read tile descriptor and config
    td  = get_tile_descriptor(WhichUnpacker, ctx)
    fmt = get_data_format(WhichUnpacker, ctx, td)

    # 3. Compute addresses
    in_addr  = compute_input_address(WhichUnpacker, ctx, td, fmt)
    out_addr = compute_output_address(WhichUnpacker, ctx, fmt)

    # 4. Main loop
    for datum in read_datums(in_addr, td, fmt):
        out_val = format_convert(datum.bits, datum.exp, fmt, WhichUnpacker)
        if AllDatumsAreZero:
            out_val = 0
        write_to_register(WhichUnpacker, out_addr, out_val, ctx)
        out_addr += 1

    # 5. Post-update
    update_context_counter(WhichUnpacker, ctx, MultiContextMode, UseContextCounter)
    update_ADC_increments(WhichUnpacker, Ch0YInc, Ch0ZInc, Ch1YInc, Ch1ZInc, ContextADC)
    if FlipSrc:
        flip_bank(WhichUnpacker)
```

---

## 15. Source References

| File | Contents |
|------|----------|
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/UNPACR_Regular.md` | Complete UNPACR functional model and encoding |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/Unpackers/README.md` | Unpacker overview, decompression, upsampling |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/Unpackers/FormatConversion.md` | Format conversion table and configuration |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/FloatBitPatterns.md` | BFP/FP16/BF16/TF32/FP32 bit pattern semantics |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/ADCs.md` | ADC counter structure and usage |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/SETADC.md` | SETADC functional model |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/SETADCXY.md` | SETADCXY functional model |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/SETADCZW.md` | SETADCZW functional model |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/SETADCXX.md` | SETADCXX functional model |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/INCADCXY.md` | INCADCXY functional model |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/INCADCZW.md` | INCADCZW functional model |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/UNPACR_NOP_SETDVALID.md` | SETDVALID NOP functional model |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/UNPACR_NOP_ZEROSRC.md` | ZEROSRC NOP functional model |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/UNPACR_NOP_SETREG.md` | SETREG NOP functional model |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/UNPACR_NOP_OverlayClear.md` | OverlayClear NOP functional model |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/UNPACR_IncrementContextCounter.md` | Context counter increment instruction |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/UNPACR_FlushCache.md` | Flush decompression cache instruction |
| `tt-llk/tt_llk_blackhole/common/inc/cunpack_common.h` | `unpack_tile_descriptor_t`, `unpack_config_t`, core unpack functions |
| `tt-llk/tt_llk_blackhole/llk_lib/llk_unpack_AB.h` | Dual-operand unpack: MOP config, init, execute |
| `tt-llk/tt_llk_blackhole/llk_lib/llk_unpack_A.h` | Single-operand unpack: MOP config, init, execute |
| `tt-llk/tt_llk_blackhole/llk_lib/llk_unpack_tilize.h` | Tilize and TilizeA+B implementations |
| `tt-llk/tt_llk_blackhole/llk_lib/llk_unpack_untilize.h` | Untilize implementation |
| `tt-llk/tt_llk_blackhole/llk_lib/llk_unpack_common.h` | `_llk_unpack_hw_configure_`, address validation |
| `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/cfg_defines.h` | All ADDR32 register positions and bit masks |
| `blackhole-py/disasms/add1/add1_trisc0.S` | Eltwise add kernel unpack disassembly |
| `blackhole-py/disasms/matmul_peak/matmul_trisc0.S` | Matmul kernel unpack disassembly |
