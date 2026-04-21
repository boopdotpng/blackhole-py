# PACR — Packer Data Path Specification (Blackhole)

This document covers the full data path of the `PACR` instruction: from reading Dest register file
values through all transformation stages, to writing formatted bytes into L1. It is the companion
to `pack-unpack-registers.md` (register field maps) and `dest-srca-srcb-registers.md` (Dest layout).

Sources:
- `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/PACR.md`
- `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/Packers/` (all sub-pages)
- `tt-llk/tt_llk_blackhole/common/inc/cpack_common.h`
- `tt-llk/tt_llk_blackhole/llk_lib/llk_pack.h`
- `tt-llk/tt_llk_blackhole/llk_lib/llk_pack_common.h`
- `tt-llk/tt_llk_blackhole/common/inc/ckernel_ops.h` (instruction encoding)
- `tt-llk/tt_llk_blackhole/common/inc/ckernel_instr_params.h` (constants)
- `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/cfg_defines.h` (register map)

---

## 1. Overview of the Pack Pipeline

The Tensix coprocessor has **four packers** (numbered 0–3). The `PACR` instruction directs
between 1 and 4 of them simultaneously. The pipeline for each packer is:

```
Dst register file
       │
       ▼
[Input Address Generator]  ← ADC Channel 0 (X,Y,Z,W), DEST_TARGET offsets
       │
       ▼
[Early Format Conversion]  ← PCK_DEST_RD_CTRL, ALU_FORMAT_SPEC_REG2
       │
       ▼
[Edge Masking]             ← PCK_EDGE_OFFSET_SEC[0:3], TILE_ROW_SET_MAPPING
       │
       ▼
[ReLU / Activation]        ← STACC_RELU_{ApplyRelu,ReluThreshold}
       │
       ▼
[Exponent Histogram]       ← ENABLE_ACC_STATS (side channel, non-blocking)
       │
       ▼
[Exponent Thresholding]    ← Exp_threshold_en, Exp_threshold
       │
       ▼
[Downsampling]             ← Downsample_mask
       │
       ▼
[BFP Shared Exponent Assembly / Late Format Conversion]
       │              ← In_data_format (LateFrom), Out_data_format (LateTo)
       ▼
[Zero Compression]         ← Disable_zero_compress
       │
       ▼
[Output Address Generator] ← ADC Channel 1 (Y,Z,W), L1_Dest_addr, Sub/Add offsets
       │
       ▼
L1 (16-byte aligned writes)
```

In tt-metal, all four packers are typically fired at once (`PackerMask = 0b1111`). For a
standard 32×32 BF16 tile (4 faces × 16×16 = 1024 datums), each packer handles one face
(256 datums). Packer 0 reads face 0, packer 1 reads face 1, etc.

---

## 2. PACR Instruction Encoding

Opcode: `0x41`. 32-bit word format:

```
Bit 31..24  23..23  22..21      20..18      17          16..15    14..13         12
──────────  ──────  ──────────  ──────────  ──────────  ────────  ─────────────  ──────────
 opcode     (rsvd)  CfgContext  RowPadZero  DstAccMode  AddrMode  AddrCntContext ZeroWrite

Bit 11..8       7            6..4    3..2       1      0
──────────  ──────────────  ──────  ─────────  ─────  ────
ReadIntfSel OvrdThreadId   Concat  CtxtCtrl   Flush  Last
```

From `ckernel_ops.h`:
```c
TT_OP_PACR(CfgContext, RowPadZero, DstAccessMode, AddrMode, AddrCntContext,
           ZeroWrite, ReadIntfSel, OvrdThreadId, Concat, CtxtCtrl, Flush, Last)
// opcode 0x41
// CfgContext [22:21] — config state (0=state 0, 1=state 1)
// RowPadZero [20:18] — pad zero behaviour
// DstAccessMode [17] — 0=normal, 1=strided
// AddrMode [16:15] — selects ADDR_MOD_PACK_SEC[0:3]
// AddrCntContext [14:13] — ADC index if OvrdThreadId set
// ZeroWrite [12] — if 1, reads from /dev/null (outputs all zeros)
// ReadIntfSel [11:8] — PackerMask: which packers are active
// OvrdThreadId [7] — if 1, use Addr_cnt_context from per-packer config
// Concat [6:4] — compression row continuation
// CtxtCtrl [3:2] — context control flops
// Flush [1] — flush output buffers (sets NeedsNewAddress for next PACR)
// Last [0] — flush output buffers (sets NeedsNewAddress for next PACR)
```

Important: `PackerMask = 0b0000` is a special case that maps to `0b0001` (packer 0 only).

From `p_pacr` constants:
```c
ALL_INTF_ACTIVE      = 0b0000   // special: only packer 0
ALL_INTF_ACTIVE_ONES = 0b1111   // all 4 packers
SINGLE_INTF_ACTIVE   = 0b0001   // packer 0
TWO_INTFS_ACTIVE     = 0b0011   // packers 0+1
THREE_INTFS_ACTIVE   = 0b0111   // packers 0+1+2
_0th_AND_2nd_INTF    = 0b0101   // packers 0+2 (tilize)
_1st_AND_3rd_INTF    = 0b1010   // packers 1+3 (tilize)
```

---

## 3. Dest Read Mechanics (Input Address Generator)

### 3.1 ADC-based Address Computation

The packer reads from Dst (or L1) using ADC (Auto-incrementing address counter) counters.
There are three ADCs (indexed 0, 1, 2 — one per Tensix thread). Each ADC has two channels
(Channel 0 and Channel 1), and each channel has four counters: X, Y, Z, W.

For the packer input address generator, **Channel 0** is used:

```python
# Pseudocode for input address computation (from ISA doc)
WhichADC = CurrentThread  # 0, 1, or 2
if OvrdThreadId:
    WhichADC = Packers[i].Config[StateID].Addr_cnt_context
    if WhichADC == 3: WhichADC = 0

ADC = ADCs[WhichADC].Packers.Channel[0]

Addr = ConfigState.PCK0_ADDR_BASE_REG_0_Base  # ADDR32 16
    + ADC.X * (ConfigState.PCK0_ADDR_CTRL_XY_REG_0_Xstride & 0xf)   # ADDR32 12 [15:0]
    + ADC.Y * ConfigState.PCK0_ADDR_CTRL_XY_REG_0_Ystride             # ADDR32 12 [31:16]
    + ADC.Z * ConfigState.PCK0_ADDR_CTRL_ZW_REG_0_Zstride             # ADDR32 13 [15:0]
    + ADC.W * ConfigState.PCK0_ADDR_CTRL_ZW_REG_0_Wstride             # ADDR32 13 [31:16]
```

The number of datums to read:
```python
# Channel[1].X is x_end2 (set by SETADCXX), Channel[0].X is x_start
InputNumDatums = ADCs[WhichADC].Packers.Channel[1].X - ADC.X + 1
# (0 if Flush=1)
```

After the address is computed, Channel 0 Y and Z are updated by `AddrMod` (Y/Z src increments,
clears, and carry-restore from `ADDR_MOD_PACK_SEC[AddrMode]`).

### 3.2 Dst Address Interpretation

When reading from Dst (the normal case):
```python
# BytesPerDatum depends on In_data_format (the LateFrom format)
# In_data_format bits [1:0]:
#   0b00 → 4 bytes (FP32, TF32, INT32)
#   0b01 → 2 bytes (FP16, BF16, INT16)
#   other → 1 byte  (all 8-bit formats)

ADC_X_Mask = {4: 0x3, 2: 0x7, 1: 0xf}[BytesPerDatum]

# Final datum index into Dst:
DatumIndex = ((Addr / BytesPerDatum) & ~ADC_X_Mask) + (ADC.X & ADC_X_Mask)
# Add per-packer Dest offset:
DatumIndex += Config.DEST_TARGET_REG_CFG_PACK_SEC[i].Offset << 4  # ADDR32 180-183
# The datum index is: row = DatumIndex >> 4, col = DatumIndex & 0xf
```

This gives a datum index into Dst (0–16383 for 16-bit mode, 0–8191 for 32-bit mode).
Datums are then fetched from consecutive addresses: `DatumIndex + j` for `j` in
`range(InputNumDatums)`.

### 3.3 PCK_DEST_RD_CTRL Modes

Register `PCK_DEST_RD_CTRL` (ADDR32 18):

| Field | Bit | Effect on Dest read |
|-------|-----|---------------------|
| `Read_32b_data` | [0] | 1 = read 32-bit rows (FP32/INT32 dest, or FP32 acc mode). 0 = read 16-bit rows. |
| `Read_unsigned` | [1] | 1 = treat as unsigned for INT8→UINT8 path |
| `Read_int8` | [2] | In ISA: this is `Read_raw`. 1 = bypass early-conversion rounding/shifting (identity or bitcast). 0 = apply rounding/shifting. |
| `Round_10b_mant` | [3] | 1 = round to 10-bit mantissa (used for FP32→TF32 early conv, or FP32 acc + Float16 src → FP8-E4M3 output) |

The LLK sets these as follows (from `set_packer_config`):
```python
Read_32b_data  = (pack_src_format in {Float32, Int32, UInt32}) or is_fp32_dest_acc_en
Read_int8      = not (is_fp32_dest_acc_en or is_32b_format) and (pack_src_format in {Int8, UInt8})
Read_unsigned  = (pack_dst_format == UInt8)
Round_10b_mant = (is_fp32_dest_acc_en and pack_src_format == Float16) or \
                 (not IS_A_FORMAT(pack_src_format) and pack_dst_format == Fp8_e4m3)
```

### 3.4 L1 Source Mode (Packer 0 only)

When `Source_interface_selection = 1` in packer 0's config (ADDR32 70, bit 16), packer 0 reads
from L1 instead of Dst. The address uses `L1_source_addr` (ADDR32 70, bits [31:24]) for the
high bits. In this mode the early format conversion is skipped; datums come from L1 bytes directly.
The shared exponent for BFP formats is taken as zero in this mode.

### 3.5 Typical Stride Configuration

From `set_packer_strides` in `cpack_common.h`:
```python
x_stride = {Float32: 4, Float16: 2, otherwise: 1}[pack_src_format & 0x3]
y_stride = FACE_C_DIM * x_stride          # = 16 * x_stride
z_stride = FACE_R_DIM * y_stride          # = 16 * y_stride (or 2× for untilize)
w_stride = TILE_NUM_FACES * FACE_C_DIM * FACE_R_DIM * x_stride  # = 4 * 16 * 16 * x_stride

# Written to:
# PCK0_ADDR_CTRL_XY_REG_0 (ADDR32 12): Xstride=0, Ystride=y_stride
# PCK0_ADDR_CTRL_ZW_REG_0 (ADDR32 13): Zstride=z_stride, Wstride=w_stride
```

X-stride is effectively 0 because ADC.X is used modulo the face width directly as an index
into the row. Y-stride advances by a full row (16 datums × bytes-per-datum = 32B for BF16).
Z-stride jumps by one face (16 rows × 16 cols). W-stride jumps by one full tile.

---

## 4. ADC Counter Mechanics for Pack

### 4.1 ADC Instructions

The ADC counters are set/manipulated by several instructions:

| Instruction | Encoding | Effect |
|-------------|----------|--------|
| `SETADC` | `0x50` | Set one counter of one channel to a value |
| `SETADCXX` | `0x5e` | Set Channel[1].X (x_end2) and Channel[0].X (x_start) for packer |
| `SETADCXY` | `0x51` | Set Y and X counters for channels 0 and 1 |
| `SETADCZW` | `0x52` | Set Z and W counters for channels 0 and 1 |
| `INCADCXY` | — | Increment XY counters |
| `INCADCZW` | — | Increment ZW counters |
| `ADDRCRXY` | `0x00` | Set carry-restore registers for Y/X |
| `ADDRCRZW` | `0x01` | Set carry-restore registers for Z/W |

The `CntSetMask` selects which ADC to target: bit 0 = unpack ADC 0, bit 1 = unpack ADC 1,
bit 2 = pack ADC. `p_setadc::PAC = 0b100`.

### 4.2 SETADCXX — Packer X Range

```c
TTI_SETADCXX(p_setadc::PAC, FACE_C_DIM - 1, 0x0);
// Sets Channel[1].X = 15 (x_end2, 0-indexed), Channel[0].X = 0 (x_start)
// InputNumDatums = Channel[1].X - Channel[0].X + 1 = 15 - 0 + 1 = 16
```

This means each PACR instruction reads exactly 16 datums (one row of a face).

### 4.3 Channel Assignment

- **Channel 0** is used for **input** (Dst) address generation. Y and Z are updated by AddrMod
  after each PACR (src Y/Z increments). X stays fixed between PACRs (set by SETADCXX x_start).
- **Channel 1** is used for **output** (L1) address generation. Y and Z updated by AddrMod
  (dst Y/Z increments). W is typically fixed. X is used as x_end2 for InputNumDatums.

### 4.4 SETADC for Tile Index

The `set_dst_write_addr` function uses:
```c
TT_SETADC(p_setadc::PAC, p_setadc::CH_0, p_setadc::SET_W, tile_index);
```
This sets Channel 0 W = tile_index, which multiplies by W-stride (= full tile size) to select
which tile in Dest to read from (for SyncFull double-buffering).

### 4.5 Counter Reset Sequence

At the end of each tile, Z counters are reset:
```c
TTI_SETADCZW(p_setadc::PAC, 0, 0, 0, 0, 0b0101); // reset ch0_z=0, ch1_z=0
```

At init (`packer_addr_counter_init`):
```c
TTI_SETADCXY(0b100, 0, 0, 0, 0, 0b1011);  // ch1_y=0, ch0_y=0, ch0_x=0 (not ch1_x)
TTI_SETADCZW(0b100, 0, 0, 0, 0, 0b1111);  // all Z,W counters = 0
```

### 4.6 AddrMod — Post-PACR Counter Updates

`AddrMod` is an index 0–3 into `ADDR_MOD_PACK_SEC[0:3]` (ADDR32 37–40). Each entry is one
32-bit word encoding:

| Bits | Field | Effect |
|------|-------|--------|
| [3:0] | `YsrcIncr` | Add to ADC Channel[0].Y after PACR |
| [4] | `YsrcCR` | Use carry-restore: Y += Y_Cr; Y = Y_Cr |
| [5] | `YsrcClear` | Clear: Y=0, Y_Cr=0 |
| [9:6] | `YdstIncr` | Add to ADC Channel[1].Y after PACR |
| [10] | `YdstCR` | Use carry-restore for dst Y |
| [11] | `YdstClear` | Clear dst Y |
| [12] | `ZsrcIncr` | Add 1 to ADC Channel[0].Z |
| [13] | `ZsrcClear` | Clear Channel[0].Z |
| [14] | `ZdstIncr` | Add 1 to ADC Channel[1].Z |
| [15] | `ZdstClear` | Clear Channel[1].Z |

Typical AddrMod configuration for standard (non-untilize) packing:
```c
// ADDR_MOD_0: advance by 4 rows (pack 4 rows per PACR call with 4 interfaces)
addr_mod_pack_t { .y_src = {.incr = 4}, .y_dst = {.incr = 4} }.set(ADDR_MOD_0);

// ADDR_MOD_1: clear Y (between faces), clear Z src
addr_mod_pack_t { .y_src = {.clr = 1}, .y_dst = {.clr = 1},
                  .z_src = {.clr = 1} }.set(ADDR_MOD_1);

// ADDR_MOD_2: clear Y, advance Z src (next face)
addr_mod_pack_t { .y_src = {.clr = 1}, .y_dst = {.incr = 4},
                  .z_src = {.incr = 1} }.set(ADDR_MOD_2);
```

---

## 5. Early Format Conversion

### 5.1 What It Does

The early conversion reads datums from Dst and converts them to an intermediate floating-point
or integer format. The intermediate format is given by `IntermediateFormat` (from
`ALU_FORMAT_SPEC_REG2_Dstacc` or `ALU_FORMAT_SPEC_REG_Dstacc_val` if override is set).

The 4-bit encoding of format names (same encoding for `IntermediateFormat`, `In_data_format`,
and `Out_data_format`). The ISA doc notation and the LLK `DataFormat` enum use different names
for the same hardware values:

| 4b value | ISA name | LLK DataFormat name | Notes |
|---------:|----------|---------------------|-------|
| 0 | FP32 | `Float32` | e8m23 |
| 4 | TF32 | `Tf32` | e8m10 |
| 5 | BF16 | `Float16_b` | e8m7 |
| 1 | FP16 | `Float16` | e5m10 |
| 10 | FP8 | `Lf8` | e5m2 (E5M2 mode); also `Fp8_e4m3` = Lf8 + extra mode bit |
| 6 | BFP8 | `Bfp8_b` | "B": 8-bit shared exponent, e8m6 per-datum; shared exp in LateConv |
| 7 | BFP4 | `Bfp4_b` | "B": 8-bit shared exponent |
| 15 | BFP2 | `Bfp2_b` | "B": 8-bit shared exponent |
| 2 | BFP8a | `Bfp8` | "A": 5-bit shared exponent, e5m7 per-datum |
| 3 | BFP4a | `Bfp4` | "A": 5-bit shared exponent |
| 11 | BFP2a | `Bfp2` | "A": 5-bit shared exponent |
| 8 | INT32 | `Int32` | sign-magnitude |
| 9 | INT16 | `UInt16` | sign-magnitude (note: LLK name is UInt16) |
| 14 | INT8 | `Int8` | sign-magnitude |
| 13 | UINT8 | `UInt8` | unsigned (note: LLK `UInt8=30`, masked to 14=INT8 in HW) |

Note: `UInt8` (LLK value 30) has bits [3:0] = `0b1110` = 14 = INT8. The distinction between
signed INT8 and unsigned UINT8 is carried by `PCK_DEST_RD_CTRL_Read_unsigned`.
`UInt32` (LLK value 24) has bits [3:0] = 8 = INT32; treated identically in hardware.

### 5.2 Common Conversion Paths

**FP32/INT32 Dest (Read_32b_data=1):**

| Desired intermediate | Read_raw | Round_10b_mant | IntermediateFormat |
|----------------------|----------|----------------|-------------------|
| FP32 (identity) | any | 0 | FP32 or INT32 |
| TF32 (round mantissa to 10b) | 0 | 0 | TF32 |
| TF32 (round mantissa to 10b) | 0 | 1 | FP32 |
| BF16 (round) | 0 | 0 | BF16 |
| BF16 (truncate) | 1 | 0 | BF16 or BFP8 |
| E8M6 | 0 | 0 | BFP8 |
| INT8 (shift+saturate) | 0 | 0 | INT8, Read_unsigned=0 |
| UINT8 (shift+saturate) | 0 | 0 | INT8, Read_unsigned=1 |
| INT8 (bit extract) | 1 | 0 | INT8, Read_unsigned=0 |

**BF16 Dest (Read_32b_data=0):**

| Desired intermediate | Read_raw | IntermediateFormat |
|----------------------|----------|--------------------|
| BF16 (identity, denormals/NaN preserved) | 1 | BF16 or BFP8 |
| BF16 (flush denormals/NaN) | 0 | BF16 |
| E8M6 | 0 | BFP8 |
| INT8 sign-bit only | 1 | INT8 |

**FP16 Dest (Read_32b_data=0):**

| Desired intermediate | Read_raw | IntermediateFormat |
|----------------------|----------|--------------------|
| FP16 (identity) | 1 | FP16 |
| FP16 (flush denormals) | 0 | FP16 |
| E5M7 | 1 | BFP8a |
| E5M6 | 0 | BFP8a |
| FP8 (e5m2) | 1 | FP8 |

### 5.3 Denormal and NaN Handling in Early Conversion

- **Identity/bitcast**: denormals and NaN preserved
- **Rounding**: denormals flushed to zero; if exponent is 8 bits wide, NaN becomes infinity
- **Truncation**: denormals may become zero; NaN may become infinity

---

## 6. Late Format Conversion and BFP Shared Exponent Assembly

### 6.1 Overview

The late format conversion takes the intermediate datum and converts it to the final L1 output
format. This is configured via `In_data_format` (`LateFromFormat`) and `Out_data_format`
(`LateToFormat`), both from the per-packer config (ADDR32 70 for packer 0, ADDR32 98 for packer 1).

### 6.2 BFP Formats in the Late Conversion

For BFP output formats (`Out_data_format` in {BFP8, BFP4, BFP2, BFP8a, BFP4a, BFP2a}), the
late conversion computes **one shared exponent per group of 16 datums** and stores the mantissas
separately.

**BFP8/BFP4/BFP2 (format B, 8-bit exponent):**
1. Convert intermediate format to BF16 (if not already — truncate mantissa if narrowing, saturate not applicable)
2. Find maximum 8-bit exponent across the group of 16 BF16 datums → this is the shared exponent
3. Each datum's mantissa is right-shifted to align with the shared exponent:
   - `shift = shared_exp - datum_exp`
   - `mantissa_with_implicit_1 = (1 << 7) | datum_mantissa`
   - `aligned_mantissa = (mantissa_with_implicit_1 >> shift) | sign_bit`
4. For BFP8: keep 7 mantissa bits + 1 sign bit = 8 bits total
5. For BFP4: keep 3 mantissa bits + 1 sign bit = 4 bits total
6. For BFP2: keep 1 mantissa bit + 1 sign bit = 2 bits total
7. Round to nearest when truncating (can be stochastic with HW bias noted below)

**BFP8a/BFP4a/BFP2a (format A, 5-bit exponent):**
1. Convert intermediate to E5M7 (i.e., FP16-like with 5-bit exponent, 7-bit mantissa)
   — saturate if exponent narrows, truncate mantissa
2. Find maximum 5-bit exponent across 16 datums → shared exponent (zero-extended to 8 bits for storage)
3. Align mantissas to shared exponent as above
4. BFP8a: 7 mantissa + 1 sign = 8 bits; BFP4a: 3 mantissa + 1 sign = 4 bits; BFP2a: 1 mantissa + 1 sign = 2 bits

**Hardware note:** Stochastic rounding has a slight hardware bias toward increasing magnitude
(not true 50:50). Can also increase magnitude of values that don't need rounding.

### 6.3 Dis_shared_exp_assembler

When `Dis_shared_exp_assembler = 1` (ADDR32 70, bit 12), the shared exponent assembly step is
disabled. The hardware treats each datum's individual exponent as if it were the shared exponent
(i.e., no normalization across the group). This effectively disables the BFP compression for
groups that don't benefit from it.

When disabled, the output format degenerates: each BFP8 datum becomes a sign bit + 7 mantissa
bits with a separate per-datum exponent field written — but since only one exponent is written per
16 datums in the tile format, the result is undefined unless software manages the exponent section
separately.

**In practice**: `Dis_shared_exp_assembler` is left at 0 (enabled) for all BFP outputs. It is
only set when packing to a non-BFP format (or when performing a non-standard exponent operation).

### 6.4 Late Conversion Table Summary

| LateFrom → LateTo | Action |
|-------------------|--------|
| FP32 → FP32 | Identity |
| FP32 → BF16 | Truncate mantissa (round if enabled) |
| FP32 → TF32 | Not supported; use early conversion |
| Any float → FP16 | Saturate exponent, truncate mantissa |
| Any float → FP8 | Saturate exponent, truncate mantissa |
| Any float → BFP8 | Via BF16 → shared exp assembly (see §6.2) |
| Any float → BFP4/2 | Via BFP8 → further truncate mantissa |
| Any float → BFP8a | Via E5M7 → shared exp assembly |
| Any float → BFP4a/2a | Via BFP8a → further truncate |
| INT32 → INT32 | Identity |
| INT16 → INT16 | Identity |
| INT8 → INT8 | Identity or bitcast |
| INT8 → UINT8 | Bitcast |

### 6.5 Exp_section_size

The `Exp_section_size` field (ADDR32 68, bits [31:16]) tells the output address generator how
many 16-byte words to reserve for the exponent stream at the start of the tile. For BFP formats,
this is set to `num_faces` (1, 2, or 4) — one 16-byte exponent block per face (16 datums per
group × num_groups_per_face blocks, packed as one exponent byte each). For non-BFP formats like
FP8 and INT8, it is set to 0 (no separate exponent section).

```python
# From set_packer_config:
if pack_dst_format in {Lf8, Int8}:
    exp_section_size = 0
else:
    exp_section_size = num_faces  # 1, 2, or 4
```

---

## 7. Exponent Thresholding

Applied after ReLU, before downsampling.

```python
def apply_exponent_thresholding(d, packer_config):
    if not packer_config.Exp_threshold_en:
        return d
    threshold = packer_config.Exp_threshold  # 8-bit value
    data_format = packer_config.In_data_format
    if data_format in {FP32, TF32, BF16, BFP8, BFP4}:
        # 8-bit exponent comparison
        if d.exponent < threshold:
            return 0.0
    elif data_format in {FP16, FP8, BFP8a, BFP4a}:
        # 5-bit exponent, zero-extended before comparison
        if d.exponent < threshold:
            return 0.0
    elif data_format == BFP2a:
        pass  # HW bug: undefined behaviour
    return d
```

**Primary use case:** FP32 Dest → BFPxA output. The FP32 exponent uses bias 127 (e8), but
BFP-A formats use bias 15 (e5). Values with FP32 exponent < 113 cannot be represented in BFP-A
(since 113 − 127 = −14 = min exponent for e5). Setting `Exp_threshold_en=1, Exp_threshold=113`
forces these values to zero before the late conversion tries (and fails) to represent them.

From `reconfigure_exp_threshold` in `cpack_common.h`:
```c
if (is_fp32_dest_acc_en && IS_BFP_A_FORMAT(pack_dst_format)) {
    enable = true;
    threshold = 113;
}
```

---

## 8. ReLU / Activation

Applied after the early format conversion, before exponent histogram. Operates on the intermediate
floating-point value.

```python
def relu_stage(x, config):
    mode = config.STACC_RELU_ApplyRelu & 3

    # Threshold interpretation depends on intermediate format
    if IntermediateFormat in {FP16, FP8, BFP8a, BFP4a, BFP2a}:
        threshold = parse_fp16(config.STACC_RELU_ReluThreshold)
    else:
        threshold = parse_bf16(config.STACC_RELU_ReluThreshold)

    if mode == 0:   # NO_RELU
        return x
    elif mode == 1: # ZERO_RELU (standard ReLU)
        return 0.0 if x <= 0 else x
    elif mode == 2: # MIN_THRESHOLD_RELU
        # threshold must be >= 0 (else undefined)
        return 0.0 if x <= threshold else x
    elif mode == 3: # MAX_THRESHOLD_RELU
        # threshold must be >= 0 (else undefined)
        if x <= 0: return 0.0
        elif x > threshold: return threshold
        else: return x
```

`STACC_RELU_ApplyRelu` is a 4-bit field at ADDR32 2, bits [5:2].
`STACC_RELU_ReluThreshold` is a 16-bit field at ADDR32 2, bits [21:6].

For integer formats, `ApplyRelu` should be 0 (no-op) or 1 (zero-out negatives).

---

## 9. Edge Masking

Edge masking replaces selected datums with 0 or −∞ based on their column position within the
face row, using a 16-bit column mask.

### 9.1 How the Mask is Selected

Each packer has an internal **Tile Position Generator** (TPG) that tracks X, Y, Z within the face
being packed. For each datum, the mask is selected as follows:

```python
# Determine which TILE_ROW_SET_MAPPING index to use for this packer (b):
if PCK_EDGE_TILE_FACE_SET_SELECT_enable:  # ADDR32 19, bit 8
    Z = DEST_TARGET_REG_CFG_PACK_SEC[packer_index].ZOffset + TPG.Z
    a = (PCK_EDGE_TILE_FACE_SET_SELECT_select >> (2 * packer_index)) & 3
    b = TILE_FACE_SET_MAPPING[a].face_set_mapping[Z & 0xf]  # 2 bits
else:
    b = (PCK_EDGE_TILE_ROW_SET_SELECT_select >> (2 * packer_index)) & 3

# Map face row Y to which PCK_EDGE_OFFSET_SEC to use (c):
c = TILE_ROW_SET_MAPPING[b].row_set_mapping[TPG.Y & 0xf]  # 2 bits

# Get the 16-bit column mask:
edge_mask = PCK_EDGE_OFFSET_SEC[c].mask  # 16 bits, one bit per column
```

Then for each datum at column `col`:
- If `edge_mask & (1 << col)` is set: pass datum through normally (apply early format conversion)
- If the bit is clear:
  - If `PCK_EDGE_MODE_mode = 1`: replace datum with −∞
  - If `PCK_EDGE_MODE_mode = 0`: replace datum with 0

### 9.2 Tile Position Generator

```python
class TilePositionGenerator:
    X = Y = Z = 0

    def advance(self, packer_index):
        self.X += 1
        if self.X == 16:
            self.X = 0
            if PACK_COUNTERS_SEC[packer_index].pack_yz_transposed:
                self.Z += 1
                if self.Z == PACK_COUNTERS_SEC[packer_index].pack_reads_per_xy_plane:
                    self.Z = 0
                    self.Y += 1
            else:
                self.Y += 1
                if self.Y == PACK_COUNTERS_SEC[packer_index].pack_reads_per_xy_plane:
                    self.Y = 0
                    self.Z += 1
```

`pack_reads_per_xy_plane` (ADDR32 28+i, bits [15:8]) is set to `face_r_dim` (= 16 for normal
tiles). This controls when Y wraps and Z increments.

### 9.3 Default Configuration

In tt-metal, edge masking is disabled for normal tiles:
```c
pck_edge_offset.f.mask = 0xffff;  // all columns enabled
cfg[PCK_EDGE_OFFSET_SEC0_mask_ADDR32] = pck_edge_offset.val;
cfg[TILE_ROW_SET_MAPPING_0_row_set_mapping_0_ADDR32] = 0x0;  // all rows → mapping 0 → mask SEC0
```

For reduced-dimension outputs (e.g., row-reduce), the mask is partially cleared:
```python
# Example: pack only 8 columns (narrow tile)
edge_mask = 0x00FF  # columns 0-7 pass, columns 8-15 replaced with 0
```

---

## 10. Downsampling

When `Downsample_mask` (ADDR32 71 for packer 0, bits [15:0]) is neither 0 nor 0xFFFF, a
vector-compress is performed on each group of 16 input datums:

```python
mask = Downsample_mask
if mask == 0: mask = 0xFFFF  # 0 means "all pass"

for datum in input_datums:
    if mask & 1:
        emit(datum)    # keep this datum
    else:
        pass           # discard silently
    mask = rotate_right(mask, 1)  # next bit
```

`Downsample_rate` (bits [18:16] of ADDR32 71) is unused in this path (it's for the shift count
in a different mode).

This is used for operations like extracting every other row, or sampling specific elements. For
more aggressive downsampling than 16:1, multiple consecutive PACRs without flushing are issued.

---

## 11. Zero Compression

### 11.1 Algorithm

Zero compression augments each datum with a 4-bit counter that counts consecutive zeros
**after** that datum. Zero datums can be elided from the data stream.

- The first and last datum in each "compression row" are **never** elided (to allow seeking)
- A `PACR` instruction with `Concat=0` starts a new compression row
- A `PACR` instruction with `Concat!=0` continues the current row

The `PerformingCompression` flag:
```python
PerformingCompression = not (
    THCON_SEC0_REG1_All_pack_disable_zero_compress_ovrd
        ? THCON_SEC0_REG1_All_pack_disable_zero_compress.Bit[i]
        : PackerIConfig.Disable_zero_compress
)
```

### 11.2 Output Layout When Compressed

See `tt-isa-documentation/WormholeB0/.../Packers/Compression.md` for the full format. Summary:

1. Row Start Index (RSI) array: one 16-bit entry per row + 1. `RSI[i+1] - RSI[i]` = augmented
   datum count for row `i`. RSI[0] = 0. Stored in the RSI stream (addressed by `Row_start_section_size`).
2. Padding to 16-byte boundary.
3. If BFP format: exponent array (one byte per 16 augmented datums), padded to 16-byte boundary.
4. Data groups of 32 augmented datums each:
   - 32 datums (4/8/16/32 bits each)
   - 32 four-bit counters (16 bytes total = 128 bits), one per datum

The `Row_start_section_size` field (ADDR32 68, bits [15:0]) reserves space for the RSI array
at the start of the output tile.

### 11.3 Disable_zero_compress

When `Disable_zero_compress = 1` (ADDR32 70, bit 0), compression is disabled for this packer.
The `uncompress` field in `pack_config_t` accomplishes the same thing (in LLK it's always set to 1
= disable compression, i.e., `uncompress = true`).

```c
config.f.uncompress = 1;  // always set in tt-metal kernels
```

### 11.4 disable_pack_zero_flag

When `Disable_pack_zero_flags = 1` (ADDR32 70, bit 2), the packer does not set zero-flags
even if all datums in a face are zero. This is required for L1 accumulation mode because
accumulating with existing L1 data may produce non-zero results even from a zero Dest input.

---

## 12. L1 Output Addressing

### 12.1 Base Address Computation

For each packer `i`, the L1 write address is computed at instruction start:

```python
# Packer 0 initial address:
Packer0Addr = PackerIConfig.L1_Dest_addr + (not PackerIConfig.Sub_l1_tile_header_size)

# For packers 1-3, if packer 0 addr has bit 31 set (relative mode):
if i > 0 and Packer0Addr.bit31:
    Addr = Packer0Addr + relative_offset_for_packer_i
else:
    Addr = PackerIConfig.L1_Dest_addr + (not PackerIConfig.Sub_l1_tile_header_size)

# Output ADC Channel 1 YZW contribution:
YZW_Addr = PCK0_ADDR_BASE_REG_1_Base        # ADDR32 17
    + ADC.Channel1.Y * PCK0_ADDR_CTRL_XY_REG_1_Ystride  # ADDR32 14 [31:16]
    + ADC.Channel1.Z * PCK0_ADDR_CTRL_ZW_REG_1_Zstride  # ADDR32 15 [15:0]
    + ADC.Channel1.W * PCK0_ADDR_CTRL_ZW_REG_1_Wstride  # ADDR32 15 [31:16]

Addr += (YZW_Addr & ~0xf)  # only 256-byte aligned adjustments from ADC
```

### 12.2 l1_dest_addr_offset

If `Add_l1_dest_addr_offset = 1` (ADDR32 70, bit 1), an additional offset is added:
```python
if PackerIConfig.Add_l1_dest_addr_offset:
    Addr += Packer[i].l1_dest_addr_offset  # 16-bit field set by TDMA-RISC
```

This allows the TDMA-RISC coprocessor to program different offsets for streaming output.

### 12.3 FIFO Wraparound

If `Addr > Pack_limit_address * 2 + 1`, the address wraps:
```python
if Addr > Pack_limit_address * 2 + 1:
    Addr -= Pack_fifo_size * 2
```
`Pack_limit_address` and `Pack_fifo_size` are in THCON_SEC0_REG9 (ADDR32 100-103).

### 12.4 Stream Addresses

The output address generator manages three streams:

1. **RSI stream** (`RSIStream`): addresses for row-start indices (compression metadata)
2. **Exponent stream** (`ExponentStream`): addresses for BFP shared exponents
3. **Data stream** (`DataStream`): addresses for the actual datum values

When `NeedsNewAddress = True` for a stream, its `ByteAddress` is computed fresh from `Addr`.
Otherwise, output is appended to the previous address (buffers persist between PACRs).

```python
if PerformingCompression and RSIStream.NeedsNewAddress:
    RSIStream.ByteAddress = (Addr & 0x1ffff) << 4  # 21-bit L1 byte address × 16
    RSIStream.NeedsNewAddress = False
    Addr += Row_start_section_size  # reserve space

if OutputFormatLessThan16Bits and ExponentStream.NeedsNewAddress:
    # OutputFormatLessThan16Bits = (Out_data_format & 2) != 0
    # This catches all BFP formats, FP8, INT8 — even though FP8/INT8 don't actually
    # produce exponents. For FP8/INT8, Exp_section_size = 0 so Addr doesn't advance.
    ExponentStream.ByteAddress = (Addr & 0x1ffff) << 4
    ExponentStream.NeedsNewAddress = False
    Addr += Exp_section_size  # advance past exponent section

if DataStream.NeedsNewAddress:
    DataStream.ByteAddress = (Addr & 0x1ffff) << 4
    DataStream.NeedsNewAddress = False
```

On `Last=1` or `Flush=1`, all three `NeedsNewAddress` flags are set to True (for the next PACR).

### 12.5 16-Byte Write Alignment

All L1 output is via **aligned 16-byte writes**. Individual datums are buffered at the end of
the pipeline. Once 16 bytes accumulate, they are written to `ByteAddress` and `ByteAddress += 16`.
If the pipeline is flushed before 16 bytes accumulate, the buffer is **padded with zeros** and
written. This means partial-row output is always zero-padded to a 16-byte boundary.

### 12.6 program_packer_destination

The typical sequence for programming the L1 destination in tt-metal:
```c
// From program_packer_destination in cpack_common.h:
uint32_t new_l1_addr = (1 << 31) | addr;  // set bit 31 = relative mode for packers 1-3
// Store L1 base addr (low 32b) and new_l1_addr (high 32b of the combined 64b "reg"):
TT_SETDMAREG(0, LOWER_HALFWORD(addr), 0, LO_16(p_gpr_pack::OUTPUT_ADDR));
TT_SETDMAREG(0, UPPER_HALFWORD(new_l1_addr), 0, HI_16(p_gpr_pack::OUTPUT_ADDR));
TTI_STALLWAIT(p_stall::STALL_CFG, p_stall::THCON);
TTI_WRCFG(p_gpr_pack::OUTPUT_ADDR, 0, THCON_SEC0_REG1_L1_Dest_addr_ADDR32);
// Reset high bits:
TT_SETDMAREG(0, UPPER_HALFWORD(addr), 0, HI_16(p_gpr_pack::OUTPUT_ADDR));
TTI_DMANOP;
```

The bit-31 trick encodes "packer 1, 2, 3 addresses are relative to packer 0" — they read
their `L1_Dest_addr` and, if packer 0's address has bit 31 set, add that to their own address
for the final output byte address. In practice, for a 4-face tile, all four packers write
sequentially within the same tile buffer, so packer N's output starts where packer N-1's ends.

---

## 13. L1 Accumulation Mode

When `Pack_L1_Acc = 1` (ADDR32 71, bit 19), instead of overwriting L1, the packer performs
a read-modify-write: it reads the existing L1 value, adds the new datum, and writes back.

```python
# Conceptual model (hardware does this atomically per datum):
if Pack_L1_Acc:
    existing = read_l1(output_address)
    result = existing + new_datum
    write_l1(output_address, result)
else:
    write_l1(output_address, new_datum)
```

From `reconfigure_packer_l1_acc`:
```c
cfg_reg_rmw_tensix<THCON_SEC0_REG1_Disable_pack_zero_flags_RMW>(pack_l1_acc);
cfg_reg_rmw_tensix<THCON_SEC0_REG1_Pack_L1_Acc_RMW>(pack_l1_acc);
```

Note that `Disable_pack_zero_flags` is also set when L1 acc is enabled, because even if all
Dest datums are zero, the accumulation result might not be zero.

**Data format**: L1 accumulation is performed in the same format as the output format. The
existing L1 data is assumed to be in `Out_data_format`. The accumulation arithmetic is integer
(for INT formats) or floating-point (for float formats) as appropriate.

**LLK usage**: Reset accumulation at the start of each tile, enable it during accumulation
iterations, then disable and write final result.

---

## 14. Output Tile Byte Layout

### 14.1 FP32 / TF32

No exponent section. Direct 4 bytes per datum, row-major within each face.

```
[face 0 data: 256 datums × 4 bytes = 1024 bytes]
[face 1 data: 256 × 4 = 1024 bytes]
[face 2 data: 256 × 4 = 1024 bytes]
[face 3 data: 256 × 4 = 1024 bytes]
Total = 4096 bytes
```

TF32 is stored as 4 bytes per datum but with the low 13 bits always zero.

### 14.2 BF16 / FP16

2 bytes per datum, 4 faces:
```
[face 0: 256 × 2 = 512 bytes]
[face 1: 512 bytes]
[face 2: 512 bytes]
[face 3: 512 bytes]
Total = 2048 bytes
```

### 14.3 FP8 (E5M2)

No exponent section (Exp_section_size = 0). 1 byte per datum:
```
[face 0: 256 × 1 = 256 bytes]
[face 1: 256 bytes]
[face 2: 256 bytes]
[face 3: 256 bytes]
Total = 1024 bytes
```

### 14.4 INT8 / UINT8

Same as FP8: 1 byte per datum, no exponent section, 1024 bytes total.

### 14.5 BFP8 (B format, 8-bit shared exponent)

```
[exponent section: num_faces × 16 bytes]
   [face 0 exponents: 16 datums/group × 1 byte/exponent = 16 bytes]
   [face 1 exponents: 16 bytes]
   [face 2 exponents: 16 bytes]
   [face 3 exponents: 16 bytes]
[data section: 4 faces × 256 datums × 1 byte = 1024 bytes]
   [face 0 data: 256 bytes]
   ...
```

Each exponent byte is the maximum 8-bit biased exponent for a group of 16 datums.
Total = 64 + 1024 = 1088 bytes (for 4 faces).

### 14.6 BFP4 (B format)

```
[exponent section: 4 × 16 = 64 bytes]
[data section: 4 faces × 256 datums × 0.5 bytes = 512 bytes]
   (two 4-bit values packed per byte, little-endian: datum[2k] in low nibble, datum[2k+1] in high nibble)
Total = 576 bytes
```

### 14.7 BFP2 (B format)

```
[exponent section: 64 bytes]
[data section: 4 × 256 × 0.25 = 256 bytes]
   (four 2-bit values per byte)
Total = 320 bytes
```

### 14.8 BFP8a / BFP4a / BFP2a (A format, 5-bit exponent)

Same layout as B variants, but the shared exponent is 5-bit zero-extended to 8 bits for storage.
The meaning of the exponent bits follows FP16 biasing (bias = 15).

### 14.9 INT16 (UInt16)

2 bytes per datum, sign-magnitude format (sign in MSB, 15-bit magnitude). 2048 bytes total.

### 14.10 Tile Header (optional)

When `Sub_l1_tile_header_size = 0` (i.e., the flag is **not** set), the output address is
advanced by 1 word (4 bytes) to leave space for a tile header. When `Add_tile_header_size = 1`,
a 16-byte tile header is written before the data.

**In tt-metal, tile headers are not used.** `sub_l1_tile_header_size` is set to 1 in all
standard kernels, meaning no header space is reserved. The tile size GPR (`p_gpr_pack::TILE_HEADER`)
is set to the tile data size (without header).

---

## 15. Config Context Switching for Pack

The config register space has two banks (state 0 and state 1). For the packer:
- `Config[0].Packers[0]` = `THCON_SEC0_REG1` (ADDR32 68–71 in state 0)
- `Config[0].Packers[1]` = `THCON_SEC0_REG8` (ADDR32 96–99 in state 0)
- `Config[0].Packers[2]` = `THCON_SEC1_REG1` (ADDR32 116–119 in state 0)
- `Config[0].Packers[3]` = `THCON_SEC1_REG8` (ADDR32 144–147 in state 0)

The `CfgContext` field in PACR (bits [22:21]) selects which of up to 4 config contexts to use.
In Blackhole, the context switching mechanism uses `CFG_STATE_ID_StateID` from `ThreadConfig`.

In practice, tt-metal uses only `CfgContext = 0` (`CFG_CTXT_0`) for normal operation. The
`OvrdThreadId` flag and `Addr_cnt_context` field in per-packer config allow per-packer ADC
selection independent of thread.

The per-packer `Addr_cnt_context` field (ADDR32 70, bits [X:X]) selects which ADC (0, 1, or 2)
this packer uses when `OvrdThreadId = 1`. Value 3 maps to ADC 0.

---

## 16. SEMWAIT / SEMGET Synchronization Around Pack

From `llk_pack_common.h`:

```c
// Wait for math to finish producing data in Dest:
TTI_SEMWAIT(p_stall::STALL_TDMA, semaphore::t6_sem(semaphore::MATH_PACK), p_stall::STALL_ON_ZERO);

// ... do WRCFG to set L1 destination, run MOP (PACR sequence) ...

// Wait for pack to write L1:
TTI_STALLWAIT(p_stall::STALL_MATH, p_stall::PACK);

// Clear Dest (for SyncFull) or half-Dest (for SyncHalf):
TTI_ZEROACC(p_zeroacc::CLR_ALL, is_fp32_dest_acc_en, 0, ADDR_MOD_1, 0);

// Signal math that Dest is free to write again:
t6_semaphore_get<p_stall::NONE>(semaphore::MATH_PACK);
```

This is the standard math→pack→math semaphore protocol. The packer thread (TRISC2) also manages:
- `flip_packer_dest_offset_id()` — toggles between DEST_OFFSET_LO and DEST_OFFSET_HI GPRs
- `select_packer_dest_registers<Dst>()` — writes the chosen offset to `DEST_TARGET_REG_CFG_PACK_SEC0`
  using WRCFG (128-bit write to program all 4 packer sections at once)

---

## 17. Real Instruction Sequences from Disassembly

### 17.1 add1 kernel — TRISC2 pack thread

From `/home/boop/tenstorrent/blackhole-py/disasms/add1/add1_trisc2.S`:

```asm
# ── Config init ─────────────────────────────────────────────────────────────
# Set addr_mod for pack (ttsetc16 writes to ThreadConfig):
7010: c8940412    ttsetc16  37, 260      # ADDR_MOD_PACK_SEC0 ← 260 = incr4 for Y src+dst
7014: c898a082    ttsetc16  38, 10272   # ADDR_MOD_PACK_SEC1 ← clear Y src+dst, clear Z src
7018: c89c4482    ttsetc16  39, 4384    # ADDR_MOD_PACK_SEC2 ← clear Y, incr Z src

# Write packer strides to config:
# (sw instructions write to TENSIX_CFG_BASE + offset for XY/ZW stride registers)
ffb80000: sw t3,0(a5)   # PCK0_ADDR_CTRL_XY_REG_0 = 4 (x_stride+y_stride for BF16)
...

# ── ADC init ─────────────────────────────────────────────────────────────────
70e4: 4600002d    ttsetadcxy  4, 0,0,0,0, 0b1011  # pac: ch1_y=0, ch0_y=0, ch0_x=0
70e8: 5200003d    ttsetadczw  4, 0,0,0,0, 0b1111  # pac: all Z/W = 0

# ── Per-tile pack loop ───────────────────────────────────────────────────────
# SEMWAIT: wait for math to post MATH_PACK semaphore
7174: 98020026    ttsemwait  1, 2, 1    # stall until MATH_PACK sem > 0

# Compute L1 dest address (RISC-V code)...
# Write L1_Dest_addr to THCON_SEC0_REG1_L1_Dest_addr_ADDR32:
71b8: 89000026    ttstallwait  128, 9   # STALL_CFG, wait for THCON
71bc: c0300116    ttwrcfg  12, 0, 69   # WRCFG reg12→ADDR32 69 (L1_Dest_addr)

# Run MOP (expands to sequence of 4 PACR instructions):
71c8: 80000001    ttdmanop               # NOP before MOP
71cc: 06000000    ttmop  1, 0, 0        # MOP: expands replayer buffer → PACR sequence

# The MOP program (not visible in disassembly) expands to approximately:
# PACR(CFG_CTXT_0, NO_PAD, NORMAL, ADDR_MOD_0, ADC_0, NO_ZERO, ALL_INTF, 0, 0, 0, 0, 0)
# PACR(CFG_CTXT_0, NO_PAD, NORMAL, ADDR_MOD_0, ADC_0, NO_ZERO, ALL_INTF, 0, 0, 0, 0, 0)
# PACR(CFG_CTXT_0, NO_PAD, NORMAL, ADDR_MOD_0, ADC_0, NO_ZERO, ALL_INTF, 0, 0, 0, 0, 0)
# PACR(CFG_CTXT_0, NO_PAD, NORMAL, ADDR_MOD_1, ADC_0, NO_ZERO, ALL_INTF, 0, 0, 0, 0, 1) ← Last=1

# After MOP completes:
7204: 88400022    ttstallwait  32, 8    # STALL_MATH, wait for PACK
720c: 88800022    ttstallwait  64, 8    # STALL_THCON, wait for PACK
7218: 94000022    ttsemget  2           # Get MATH_PACK semaphore (signal math can write)
```

### 17.2 Typical Normal PACR MOP expansion

For a 32×32 BF16 tile (4 faces, 16 rows × 16 cols each), with 4 packers active, each PACR
reads one face row (16 datums × 4 packers = 64 datums per PACR call). 16 rows per face → 4
PACR calls per tile (since 4 faces × 16 rows / (4 rows per PACR) = 16, but outer loop = 4 faces,
inner = 4 PACR calls per face).

Typical MOP for non-untilize, normal mode:
```
Outer loop: num_faces = 4 iterations
  Inner loop: face_r_dim / 4 = 4 iterations
    Main body: PACR(AddrMod=ADDR_MOD_0, Last=0)  ← advance Y by 4
  Last inner:  PACR(AddrMod=ADDR_MOD_2, Last=0)  ← advance Y by 4, incr Z  
Last outer:  PACR(AddrMod=ADDR_MOD_1, Last=1)   ← clear Y, clear Z, Last=1 flushes
```

### 17.3 matmul kernel — TRISC2

From `/home/boop/tenstorrent/blackhole-py/disasms/matmul_peak/matmul_trisc2.S`:
Very similar structure. The key difference is the outer matmul accumulation loop — SEMWAIT
waits once per output tile, then MOP fires once. The pack thread loops over output tiles.

```asm
71fc: 98020026    ttsemwait  1, 2, 1    # wait for math to finish one matmul
...
7258: 89000026    ttstallwait  128, 9   # STALL_CFG, THCON
725c: c0300116    ttwrcfg  12, 0, 69   # write L1_Dest_addr
...
7274: 80000001    ttdmanop
7278: 06000000    ttmop  1, 0, 0        # expand PACR sequence
...
7294: 88800022    ttstallwait  64, 8    # wait for pack completion
...
72a0: 94000022    ttsemget  2           # signal math
```

---

## 18. Emulator Implementation Notes

### 18.1 Data Structure Recommendations

```python
class PackerState:
    # Per-packer state (instantiate 4)
    input_source: InputSource  # DST or L1 or DEV_NULL
    input_source_addr: int     # datum index into Dst, or byte addr in L1
    input_source_stride: int   # 1 for Dst (datums), bytes for L1
    input_num_datums: int      # datums to read per PACR

    # Output streams
    rsi_stream: OutputStream   # row start indices
    exp_stream: OutputStream   # exponent section
    data_stream: OutputStream  # actual data

    # Tile position generator (for edge masking)
    tpg_x: int = 0
    tpg_y: int = 0
    tpg_z: int = 0

    # L1 accumulation
    pack_l1_acc: bool = False

class OutputStream:
    needs_new_address: bool = True
    byte_address: int = 0      # L1 byte address (16-byte aligned)
    buffer: bytearray          # up to 15 bytes pending write
```

### 18.2 Simplified PACR Pseudocode

```python
def execute_PACR(instr, config, adcs, packers, dst, l1):
    """Execute one PACR instruction."""
    state_id = ThreadConfig[current_thread].CFG_STATE_ID_StateID
    cfg = Config[state_id]

    # --- Input address generator ---
    for i in range(4):
        if not instr.PackerMask & (1 << i):
            continue
        pck = packers[i]
        pck_cfg = cfg.Packers[i]  # THCON_SEC0_REG{1,8}/THCON_SEC1_REG{1,8}

        which_adc = current_thread
        if instr.OvrdThreadId:
            which_adc = pck_cfg.Addr_cnt_context
            if which_adc == 3: which_adc = 0
        adc_ch0 = adcs[which_adc].packer_channel0
        adc_ch1 = adcs[which_adc].packer_channel1

        # Compute base address
        addr = cfg.PCK0_ADDR_BASE_REG_0
        addr += adc_ch0.X * (cfg.PCK0_ADDR_CTRL_XY_REG_0_Xstride & 0xf)
        addr += adc_ch0.Y * cfg.PCK0_ADDR_CTRL_XY_REG_0_Ystride
        addr += adc_ch0.Z * cfg.PCK0_ADDR_CTRL_ZW_REG_0_Zstride
        addr += adc_ch0.W * cfg.PCK0_ADDR_CTRL_ZW_REG_0_Wstride

        # Number of datums
        if instr.Flush:
            pck.input_num_datums = 0
        else:
            pck.input_num_datums = adc_ch1.X - adc_ch0.X + 1  # = 16 typically

        # Source routing
        if instr.ZeroWrite or instr.Flush:
            pck.input_source = DEV_NULL
        elif i == 0 and pck_cfg.Source_interface_selection == 1:
            # L1 source mode
            pck.input_source = L1
            # ... (L1 addressing, not covered here)
        else:
            bytes_per_datum = datum_size(pck_cfg.In_data_format)
            adc_x_mask = {4: 0x3, 2: 0x7, 1: 0xf}[bytes_per_datum]
            datum_addr = ((addr // bytes_per_datum) & ~adc_x_mask) + (adc_ch0.X & adc_x_mask)
            datum_addr += cfg.DEST_TARGET_REG_CFG_PACK_SEC[i].Offset << 4
            pck.input_source = DST
            pck.input_source_addr = datum_addr & 0x3fff

    # --- ADC updates (input side) ---
    addr_mod = ThreadConfig[current_thread].ADDR_MOD_PACK_SEC[instr.AddrMode]
    for adc in used_adcs:
        ch0 = adc.packer_channel0
        if addr_mod.YsrcClear:
            ch0.Y = ch0.Y_Cr = 0
        elif addr_mod.YsrcCR:
            ch0.Y_Cr += addr_mod.YsrcIncr
            ch0.Y = ch0.Y_Cr
        else:
            ch0.Y += addr_mod.YsrcIncr

        if addr_mod.ZsrcClear:
            ch0.Z = ch0.Z_Cr = 0
        else:
            ch0.Z += addr_mod.ZsrcIncr

    # --- Output address generator (also runs at instruction start) ---
    # ... (see §12 for details) ...

    # --- Data pipeline (per packer, per datum) ---
    for i in range(4):
        if not instr.PackerMask & (1 << i):
            continue
        pck = packers[i]
        pck_cfg = cfg.Packers[i]

        bfp_group = []  # accumulate 16 datums for BFP shared exp

        for j in range(pck.input_num_datums):
            # 1. Fetch from source
            if pck.input_source == DST:
                raw = dst_read(pck.input_source_addr + j)
            elif pck.input_source == DEV_NULL:
                raw = 0
            else:
                raw = l1_read_datum(pck.input_source_addr + j * pck.input_source_stride)

            # 2. Early format conversion (Dst → intermediate)
            datum = early_format_convert(raw, pck_cfg.In_data_format,
                                          cfg.PCK_DEST_RD_CTRL)

            # 3. Edge masking
            datum = edge_mask_apply(datum, pck, j, i, cfg)

            # 4. ReLU
            datum = relu_stage(datum, cfg.STACC_RELU_ApplyRelu,
                                cfg.STACC_RELU_ReluThreshold,
                                cfg.IntermediateFormat)

            # 5. Exponent histogram update (side effect, non-blocking)
            exp_histogram_update(datum, i)

            # 6. Exponent thresholding
            datum = apply_exponent_thresholding(datum, pck_cfg)

            # 7. Downsampling
            if not downsample_pass(j, pck_cfg.Downsample_mask):
                continue

            # 8. Late format conversion (BFP shared exp assembly, or direct)
            if is_bfp_format(pck_cfg.Out_data_format):
                bfp_group.append(datum)
                if len(bfp_group) == 16:
                    # Compute shared exponent and emit 16 mantissas + 1 exponent
                    emit_bfp_group(bfp_group, pck_cfg.Out_data_format,
                                   pck.exp_stream, pck.data_stream, l1)
                    bfp_group = []
            else:
                # Direct conversion
                out_bytes = late_format_convert(datum, pck_cfg.In_data_format,
                                                pck_cfg.Out_data_format)
                emit_datum(out_bytes, pck.data_stream, l1, pck_cfg.Pack_L1_Acc)

        # Flush any remaining BFP group (padding with zeros)
        if bfp_group:
            bfp_group.extend([0.0] * (16 - len(bfp_group)))
            emit_bfp_group(bfp_group, pck_cfg.Out_data_format,
                           pck.exp_stream, pck.data_stream, l1)

    # --- Last/Flush: flush output buffers ---
    if instr.Last or instr.Flush:
        for i in range(4):
            flush_buffer_to_l1(packers[i].data_stream, l1)
            flush_buffer_to_l1(packers[i].exp_stream, l1)
            if PerformingCompression:
                flush_buffer_to_l1(packers[i].rsi_stream, l1)
            packers[i].data_stream.needs_new_address = True
            packers[i].exp_stream.needs_new_address = True
            packers[i].rsi_stream.needs_new_address = True
```

### 18.3 Format Conversion Implementation Notes

**BF16 → BF16 (identity after ReLU):**
```python
def early_conv_bf16_to_bf16(raw16, read_raw):
    if read_raw:
        return struct.unpack('f', struct.pack('HH', 0, raw16))[0]  # bitcast to float
    else:
        # Flush denormals, NaN→inf
        f = bf16_to_float(raw16)
        if math.isnan(f): f = math.inf * math.copysign(1, f)
        if abs(f) < 2**-127: f = 0.0  # flush denormals
        return f
```

**BFP8 shared exponent assembly:**
```python
def emit_bfp8_group(datums, exp_stream, data_stream, l1):
    # Convert to BF16 first
    bf16_vals = [to_bf16(d) for d in datums]
    # Find max exponent
    exponents = [(v >> 7) & 0xff for v in bf16_vals]  # 8-bit biased exp
    shared_exp = max(exponents)
    # Emit one exponent byte
    exp_stream.emit_byte(shared_exp, l1)
    # Emit 16 mantissa bytes
    for bf16 in bf16_vals:
        sign = (bf16 >> 15) & 1
        exp = (bf16 >> 7) & 0xff
        mant = bf16 & 0x7f
        # Add implicit 1
        mant_full = (1 << 7) | mant
        shift = shared_exp - exp
        if shift >= 8:
            mant_aligned = 0
        else:
            mant_aligned = mant_full >> shift
            # Round to nearest (truncate remaining bits)
        data_stream.emit_byte((sign << 7) | (mant_aligned & 0x7f), l1)
```

### 18.4 Key Implementation Pitfalls

1. **Output buffering**: Don't emit 16-byte writes immediately. Accumulate in a 16-byte buffer
   and only write when full. `Last=1` or `Flush=1` zero-pads and flushes.

2. **NeedsNewAddress persistence**: The stream addresses carry over between consecutive PACR
   instructions. Only reset on `Last=1`, `Flush=1`, or hardware reset.

3. **Exp_section_size vs actual exponents**: For FP8 and INT8, `Exp_section_size = 0` even
   though `OutputFormatLessThan16Bits` might be true. The address generator still runs the
   exponent stream logic, but since `Exp_section_size = 0`, no space is reserved and no address
   is updated.

4. **BFP group boundaries**: The 16-datum group is counted on the **output side** (after downsampling).
   Groups do not reset between PACR instructions within a compression row.

5. **Packer 0 bit-31 relative mode**: When `L1_Dest_addr.bit31 = 1`, packers 1–3 interpret
   their own `L1_Dest_addr` as an offset from packer 0's address. In emulation, resolve this
   at address generator time.

6. **ADC X range**: `SETADCXX` sets `Channel[1].X = x_end2` and `Channel[0].X = x_start`.
   `InputNumDatums = x_end2 - x_start + 1`. For standard 16-column faces: `x_end2=15, x_start=0`.

7. **PACR arguments vs ISA**: The LLK `TT_OP_PACR` argument order is:
   `(CfgContext, RowPadZero, DstAccessMode, AddrMode, AddrCntContext, ZeroWrite, ReadIntfSel, OvrdThreadId, Concat, CtxtCtrl, Flush, Last)`.
   `ReadIntfSel` is the PackerMask (which packers are active). `ZeroWrite` is the dev/null flag.

---

## 19. Source References

| Source | Location | What's documented |
|--------|----------|-------------------|
| PACR ISA | `tt-isa-documentation/WormholeB0/.../PACR.md` | Instruction encoding, functional model |
| Packer pipeline | `tt-isa-documentation/WormholeB0/.../Packers/README.md` | Pipeline overview |
| Input address gen | `tt-isa-documentation/WormholeB0/.../Packers/InputAddressGenerator.md` | ADC-based input addressing |
| Output address gen | `tt-isa-documentation/WormholeB0/.../Packers/OutputAddressGenerator.md` | Stream addressing, NeedsNewAddress |
| Format conversion | `tt-isa-documentation/WormholeB0/.../Packers/FormatConversion.md` | Early/late conversions, BFP assembly |
| Compression | `tt-isa-documentation/WormholeB0/.../Packers/Compression.md` | Zero compression format |
| ReLU | `tt-isa-documentation/WormholeB0/.../Packers/ReLU.md` | ReLU modes and threshold |
| Edge masking | `tt-isa-documentation/WormholeB0/.../Packers/EdgeMasking.md` | Column mask algorithm, TPG |
| Exp thresholding | `tt-isa-documentation/WormholeB0/.../Packers/ExponentThresholding.md` | Threshold algorithm |
| Downsampling | `tt-isa-documentation/WormholeB0/.../Packers/Downsampling.md` | Vector-compress |
| Exp histogram | `tt-isa-documentation/WormholeB0/.../Packers/ExponentHistogram.md` | Max exponent tracking |
| LLK pack core | `tt-llk/tt_llk_blackhole/common/inc/cpack_common.h` | Pack config structs, init, strides |
| LLK pack ops | `tt-llk/tt_llk_blackhole/llk_lib/llk_pack.h` | MOP setup, addrmod config, _llk_pack_ |
| LLK pack common | `tt-llk/tt_llk_blackhole/llk_lib/llk_pack_common.h` | Semaphore wait/post, dest offset, relu |
| PACR encoding | `tt-llk/tt_llk_blackhole/common/inc/ckernel_ops.h` | TT_OP_PACR macro |
| ADC constants | `tt-llk/tt_llk_blackhole/common/inc/ckernel_instr_params.h` | p_pacr, p_setadc constants |
| GPR map | `tt-llk/tt_llk_blackhole/common/inc/ckernel_gpr_map.h` | p_gpr_pack register assignments |
| Register map | `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/cfg_defines.h` | All ADDR32/SHAMT/MASK values |
| Disasm: add1 pack | `blackhole-py/disasms/add1/add1_trisc2.S` | Real TRISC2 pack thread code |
| Disasm: matmul pack | `blackhole-py/disasms/matmul_peak/matmul_trisc2.S` | Real TRISC2 matmul pack code |
