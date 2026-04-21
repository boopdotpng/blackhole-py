# FPU (Matrix Unit) Operations

## Overview

The **Matrix Unit (FPU)** is one of the nine shared backend execution units in the Tensix
coprocessor. It accepts one instruction per cycle, dispatched from any of the three frontend
threads (T0/T1/T2). Instructions that require both SrcA and SrcB will stall at the Wait Gate
until both register banks have been handed off by the Unpackers (`AllowedClient == MatrixUnit`).

The FPU reads from two staging register files and accumulates results into the Dest register:

```
SrcA[bank][0..63][0..15]  — 64 rows × 16 cols × 19-bit datums
SrcB[bank][0..63][0..15]  — 64 rows × 16 cols × 19-bit datums
Dst16b[0..1023][0..15]    — 1024 rows × 16 cols × 16-bit datums (or 512×16×32-bit)
```

Each Src file has two banks (0 and 1). The FPU uses one bank while the Unpackers write to
the other — the "ping-pong" double-buffer. A `clear_dvalid` field in many FPU instructions
releases the current bank back to the Unpackers and flips to the other bank.

**Supported data types:**

| Location | Data types |
|----------|-----------|
| SrcA, SrcB | BF16, TF32, FP16, INT8 ("integer 8"), INT16 (opaque transfer only) |
| Dst (16-bit mode) | BF16, FP16, INT8, INT16 |
| Dst (32-bit mode) | FP32, INT32 (sign-magnitude) |

---

## Register-Write Counters (RWCs)

All FPU instructions use RWCs to address their source and destination rows. Each thread has
its own independent RWC set:

```c
struct {
    uint10_t Dst, Dst_Cr;
    uint6_t  SrcA, SrcA_Cr;
    uint6_t  SrcB, SrcB_Cr;
    uint2_t  FidelityPhase;
    uint1_t  ExtraAddrModBit;
} RWCs[3];   // indexed by CurrentThread
```

The `addr_mode` field (2 or 5 bits) in every FPU instruction is an index into a set of
pre-configured ADDR_MOD slots (up to 8 slots). Each slot specifies increments and
carry-reset actions for SrcA, SrcB, Dst, and FidelityPhase. This is the primary mechanism
by which a repeated MVMUL or ELWADD instruction steps through different rows on each
invocation.

**SETRWC** (opcode `0x37`) — explicitly loads RWC values:

```
[31:24] opcode     = 0x37
[23:22] clear_ab   — CLR_A=1, CLR_B=2, CLR_AB=3 (CLear src bank dvalid + flip bank)
[21:18] rwc_cr     (4-bit carry-reset value, applied to set-targets)
[17:14] rwc_d      (4-bit Dst load value)
[13:10] rwc_b      (4-bit SrcB load value)
[9:6]   rwc_a      (4-bit SrcA load value)
[5:0]   BitMask    — which counters to set (SET_A=1, SET_B=2, SET_D=4, SET_F=8, combinations)
```

**INCRWC** (opcode `0x38`) — adds immediate deltas to RWCs:

```
[31:24] opcode     = 0x38
[23:18] rwc_cr     (6-bit increment for carry-reset register)
[17:14] rwc_d      (4-bit Dst increment)
[13:10] rwc_b      (4-bit SrcB increment)
[9:6]   rwc_a      (4-bit SrcA increment)
```

The canonical reset before a matmul tile is:
```c
TTI_SETRWC(CLR_NONE, 0, 0, 0, 0, SET_ABD_F);   // zeros SrcA, SrcB, Dst, FidelityPhase
```

---

## Format Selection: ALU_FORMAT_SPEC

The FPU infers the compute data type from two configuration registers packed into ADDR32 0
and ADDR32 1 of the thread-agnostic `Config` bank. See
[pack-unpack-registers.md §3 ALU Format](pack-unpack-registers.md) for bit assignments.

**ADDR32 0 — auto-infer fields (Blackhole default path):**

| Bits | Field | Description |
|------|-------|-------------|
| [3:0] | `SrcA_val` | Format code when `SrcA_override=1` |
| [4] | `SrcA_override` | 1 = use `SrcA_val` instead of auto-detect |
| [8:5] | `SrcB_val` | Format code when `SrcB_override=1` |
| [9] | `SrcB_override` | 1 = use `SrcB_val` instead of auto-detect |
| [13:10] | `Dstacc_val` | Dest accumulator format code when `Dstacc_override=1` |
| [14] | `Dstacc_override` | 1 = force Dest format |

**ADDR32 1 — explicit format fields (used as override or on Wormhole):**

| Bits | Field | Description |
|------|-------|-------------|
| [20:17] | `ALU_FORMAT_SPEC_REG0_SrcA` | 4-bit format code for SrcA |
| [24:21] | `ALU_FORMAT_SPEC_REG1_SrcB` | 4-bit format code for SrcB |
| [28:25] | `ALU_FORMAT_SPEC_REG2_Dstacc` | 4-bit format code for Dest accumulator |
| [29] | `ALU_ACC_CTRL_Fp32_enabled` | 1 = Dest in FP32 mode (512-row space, 32-bit) |
| [30] | `ALU_ACC_CTRL_SFPU_Fp32_enabled` | 1 = SFPU also sees FP32 Dest |
| [31] | `ALU_ACC_CTRL_INT8_math_enabled` | 1 = INT8 math mode (overrides format fields) |

**Format code table (4-bit values):**

| Code | Format | Style selected |
|------|--------|----------------|
| 0 | Float32 | BF16 style |
| 1 | Float16 | FP16 style |
| 2 | Bfp8 | BF16 style |
| 3 | Bfp4 | BF16 style |
| 4 | Tf32 | TF32 style |
| 5 | Float16_b | BF16 style |
| 6 | Bfp8_b | BF16 style |
| 7 | Bfp4_b | BF16 style |
| 8 | Int32 | BF16 style |
| 9 | UInt16 | BF16 style |
| 10 | Lf8 | FP16 style |
| 11 | Bfp2 | BF16 style |
| 14 | Int8 | FP16 style |
| 15 | Bfp2_b | BF16 style |

**Style-to-operation mapping:**

```python
def compute_style(srca_fmt, int8_enabled, fp16a_force):
    if fp16a_force:
        return "FP16", use_dst32b=False
    if int8_enabled:
        return "INT8", use_dst32b=True
    if srca_fmt in {FP32, BF16, BFP8, BFP4, BFP2, INT32, INT16}:
        return "BF16", use_dst32b=ALU_ACC_CTRL_Fp32_enabled
    if srca_fmt in {FP16, FP8, BFP8a, BFP4a, BFP2a, INT8}:
        return "FP16", use_dst32b=ALU_ACC_CTRL_Fp32_enabled
    if srca_fmt == TF32:
        return "TF32", use_dst32b=ALU_ACC_CTRL_Fp32_enabled
```

**Note:** On Blackhole, the unpacker writes the data format into the SrcA/SrcB tile headers,
and the FPU can auto-detect from there without needing explicit format register writes.
The `ALU_FORMAT_SPEC_REG0_SrcA` / `ALU_FORMAT_SPEC_REG1_SrcB` fields in ADDR32 1 serve
as the authoritative value used by the Wormhole functional model, and Blackhole LLK code
generally does not write them explicitly (the comment in `llk_math_common.h` states:
"do not need to program ALU_FORMAT_SPEC_REG0_SrcA/ALU_FORMAT_SPEC_REG1_SrcB for blackhole
since ALU format is inferred").

---

## MVMUL — Matrix-Vector Multiply (opcode `0x26`)

### Summary

Computes `Dst += SrcB @ SrcA` where:
- SrcB contributes an aligned **8×16** matrix (8 rows × 16 columns)
- SrcA contributes a **16×16** matrix (16 rows × 16 columns)
- The result is an **8×16** matrix accumulated into Dst

This is one invocation of the underlying hardware multiplier array. A complete 32×32 tile
matmul requires **16 MVMUL instructions** (4 faces × 4 MVMUL per face for a 32×32 tile,
or a different pattern for non-square tiles — see §Full Tile Matmul below).

### Instruction Encoding

```
[31:24] opcode       = 0x26
[23:22] clear_dvalid  (2 bits) — CLR_NONE=0, CLR_A=1, CLR_B=2, CLR_AB=3
[21:19] instr_mod19   (3 bits) — broadcast / math mode flags
[18:14] addr_mode     (5 bits) — ADDR_MOD index (0–7 after ExtraAddrModBit expansion)
[13:0]  dst           (14 bits) — explicit Dst row offset added to RWC
```

In practice only the low 2 bits of `addr_mode` are used for the ADDR_MOD index (bits 15:14),
and `instr_mod19` is typically 0 for standard matmul.

### Data Flow

```
SrcB[bank][SrcBRow .. SrcBRow+7][0..15]   (8 rows, aligned to 8-row boundary)
SrcA[bank][SrcARow .. SrcARow+15][0..15]  (16 rows, aligned to 16-row boundary)
                     |
                     v
         dot product: for each output (i,j):
           Dst[DstRow+i][j] += sum_k( SrcB[SrcBRow+i][k] * SrcA[SrcARow+k][j] )
```

The operation is a row-of-SrcB dotted against a column-of-SrcA, producing one element.
Eight rows of SrcB are consumed simultaneously (producing 8 rows of output). The full
16×16 SrcA matrix is consumed against all 8 SrcB rows.

```
          SrcA  (16×16)
         ┌──────────────┐
    row0 │              │
    ...  │  16 rows     │
   row15 │              │
         └──────────────┘
              ×
          SrcB  (8×16)
         ┌──────────────┐
    row0 │              │
    ...  │   8 rows     │
    row7 │              │
         └──────────────┘
              =
          Dst  (8×16) accumulated
         ┌──────────────┐
    row0 │  Dst +=      │
    ...  │   8 rows     │
    row7 │              │
         └──────────────┘
```

### Behavioral Model (Python pseudocode)

```python
def MVMUL(clear_dvalid, instr_mod19, addr_mode, dst_field):
    # --- Format determination ---
    style, use_dst32b = compute_style(SrcA_format, INT8_math, FP16A_force)

    # --- Row addressing ---
    srca_row = RWC.SrcA & 0x38     # aligned to 8-row boundary  (mask 0x38 = bits 5:3)
    srcb_row = RWC.SrcB & 0x38     # aligned to 8-row boundary  (mask 0x38 = bits 5:3)
    dst_row  = dst_field
    dst_row += ThreadConfig.DEST_TARGET_REG_CFG_MATH_Offset
    dst_row += RWC.Dst + Config.DEST_REGW_BASE_Base
    dst_row &= 0x3F8               # align to 8-row boundary

    # --- Fidelity phase ---
    fidelity = (RWC.FidelityPhase + ThreadConfig.FIDELITY_BASE_Phase) & 3

    # --- Matrix multiply and accumulate ---
    for i in range(8):             # 8 output rows from SrcB
        for j in range(16):        # 16 output columns
            acc = 0.0
            for k in range(16):    # inner dimension (SrcA rows = SrcB columns)
                a = src_a_fidelity_bits(SrcA[bank][srca_row + k][j], fidelity, style)
                b = src_b_fidelity_bits(SrcB[bank][srcb_row + i][k], fidelity, style)
                acc += a * b
            if use_dst32b:
                Dst32b[dst_row + i][j] += float_fp32(acc)
            else:
                Dst16b[dst_row + i][j] = round_to_format(
                    read_dst(dst_row+i, j, style) + acc, style)

    # --- Clear dvalid (release Src banks) ---
    if clear_dvalid & CLR_A:
        if not CLR_DVALID_SrcA_Disable:
            SrcA[MatrixUnit.SrcABank].AllowedClient = Unpackers
        MatrixUnit.SrcABank ^= 1
    if clear_dvalid & CLR_B:
        if not CLR_DVALID_SrcB_Disable:
            SrcB[MatrixUnit.SrcBBank].AllowedClient = Unpackers
        MatrixUnit.SrcBBank ^= 1

    # --- Advance RWCs ---
    apply_addr_mod(addr_mode)
```

### `clear_dvalid` Field

| Value | Name | Effect |
|-------|------|--------|
| 0 | `CLR_NONE` | Keep both Src banks, don't flip |
| 1 | `CLR_A` | Release SrcA bank to Unpackers, flip SrcA bank pointer |
| 2 | `CLR_B` | Release SrcB bank to Unpackers, flip SrcB bank pointer |
| 3 | `CLR_AB` | Release both banks, flip both pointers |

When cleared, the `AllowedClient` flag of the old bank changes from `MatrixUnit` back to
`Unpackers`. The Unpackers were blocked from writing to the in-use bank, so releasing it
lets them begin filling it with data for the next tile.

### `instr_mod19` Field

| Value | Effect |
|-------|--------|
| 0 | Standard matmul (no broadcast) |
| 1 | Broadcast SrcB row 0: accumulates 7 rows (NumRows=7), iterating SrcB rows 0,2,4,6 (i+=2 loop). Results are written to Dst rows 0,2,4,6,8,10,12 (even positions only); odd Dst rows are not written and retain their prior contents. |
| Others | Reserved / hardware-specific modes |

### Dst Address Calculation

The effective Dst row for output row `i` is:

```
effective_dst = (dst_field + DEST_TARGET_REG_CFG_MATH_Offset + RWC.Dst + DEST_REGW_BASE_Base) & 0x3F8
output_row_i  = effective_dst + i          (i = 0..7)
```

`DEST_REGW_BASE_Base` is typically 0 (first half of Dest) or 512 (second half), controlled
by the double-buffer flip. `DEST_TARGET_REG_CFG_MATH_Offset` is set by the kernel before
calling the math inner loop.

---

## Full 32×32 Tile Matmul — MVMUL Sequence

A 32×32 tile is subdivided into **four 16×16 faces**: F0 (top-left), F1 (top-right),
F2 (bottom-left), F3 (bottom-right). The input matrix (loaded to SrcA) is 32×32 stored
as four 16×16 faces; the weight matrix (loaded to SrcB) is similarly 32×32 stored as four
faces.

The operation `Dst = SrcB @ SrcA` for a full 32×32 × 32×32 → 32×32 matmul decomposes as:

```
Dst[F0]  = SrcB[F0] @ SrcA[F0]  +  SrcB[F1] @ SrcA[F2]
Dst[F1]  = SrcB[F0] @ SrcA[F1]  +  SrcB[F1] @ SrcA[F3]
Dst[F2]  = SrcB[F2] @ SrcA[F0]  +  SrcB[F3] @ SrcA[F2]
Dst[F3]  = SrcB[F2] @ SrcA[F1]  +  SrcB[F3] @ SrcA[F3]
```

Each `@` above is one MVMUL (SrcB face is 8×16 after the 16→8 split per half-face; the
SrcA face remains 16×16). For the standard 32×32 tile, 16 MVMUL instructions produce
one complete output tile.

The LLK programs 16 MVMUL instructions into the **Replay buffer** using
`matmul_configure_mop()`. The MOP template runs this replay sequence for each input tile
pair. Between MVMUL instructions, ADDR_MOD selectors step the RWCs:

### Real MVMUL Sequence (from `matmul_peak` TRISC1 disassembly, LoFi 32×32)

The following 16-instruction replay buffer was extracted from
`blackhole-py/disasms/matmul_peak/matmul_trisc1_pt_load.txt`:

```
; ADDR_MOD_0: SrcA unchanged, SrcB += 8 rows, Dst += 8 rows
; ADDR_MOD_1: SrcA += 16 rows, SrcB CR (carry-reset back to face start), Dst += 8 rows
; ADDR_MOD_2: SrcA CR (reset to 0), SrcB += 32 rows (next face), Dst += 8 rows
; ADDR_MOD_4: SrcA += 32 rows, SrcB CR + 48 (next face after wrap), Dst CR (reset to 0)
; ADDR_MOD_5: all clear+CR (reset), FidelityPhase += 1 (or 0 in LoFi)

[0]  MVMUL CLR_NONE ADDR_MOD_0  ; B0A0: srcb row 0-7  @ srca rows 0-15  -> dest rows 0-7
[1]  MVMUL CLR_NONE ADDR_MOD_1  ; B0A0: srcb row 8-15 @ srca rows 0-15  -> dest rows 8-15   (SrcB CR resets)
[2]  MVMUL CLR_NONE ADDR_MOD_0  ; B0A1: srcb row 0-7  @ srca rows 16-31 -> dest rows 16-23
[3]  MVMUL CLR_NONE ADDR_MOD_2  ; B0A1: srcb row 8-15 @ srca rows 16-31 -> dest rows 24-31  (SrcA CR resets; SrcB += 32)
[4]  MVMUL CLR_NONE ADDR_MOD_0  ; B2A0: srcb row 32-39 @ srca rows 0-15 -> dest rows 32-39
[5]  MVMUL CLR_NONE ADDR_MOD_1  ; B2A0: srcb row 40-47 @ srca rows 0-15 -> dest rows 40-47  (SrcB CR resets)
[6]  MVMUL CLR_NONE ADDR_MOD_0  ; B2A1: srcb row 32-39 @ srca rows 16-31-> dest rows 48-55
[7]  MVMUL CLR_NONE ADDR_MOD_4  ; B2A1: srcb row 40-47 @ srca rows 16-31-> dest rows 56-63  (Dst CR resets)
[8]  MVMUL CLR_NONE ADDR_MOD_0  ; B1A2: srcb face 1   @ srca face 2     -> dest rows 0-7
[9]  MVMUL CLR_NONE ADDR_MOD_1  ; ...
[10] MVMUL CLR_NONE ADDR_MOD_0  ;
[11] MVMUL CLR_NONE ADDR_MOD_2  ;
[12] MVMUL CLR_NONE ADDR_MOD_0  ; B3A2: srcb face 3 @ srca face 2 -> dest rows 32-39
[13] MVMUL CLR_NONE ADDR_MOD_1  ; ...
[14] MVMUL CLR_NONE ADDR_MOD_0  ;
[15] MVMUL CLR_NONE ADDR_MOD_5  ; final: reset all RWCs (FidelityPhase unchanged in LoFi)
```

The last instruction in the replay uses ADDR_MOD_5 to reset SrcA, SrcB, and Dst RWCs.
In LoFi mode, `SETRWC(CLR_B, 0, 0, 0, 0, SET_ABD_F)` clears SrcB and resets all
counters at the end of the MOP outer loop.

### How a Full Matmul Works

```python
# Init (once per kernel configuration):
ZEROACC(CLR_ALL, use_32b=False, addr_mode=0, where=0)    # clear all Dest
SETRWC(CLR_NONE, 0, 0, 0, 0, SET_ABD_F)                  # reset all RWCs

# Per tile-pair:
set_dst_write_addr(dst_index)     # sets DEST_TARGET_REG_CFG_MATH_Offset
# Unpackers have loaded SrcA (weight tile) and SrcB (activation tile)
ckernel_template.run()            # runs MOP -> emits 16 MVMUL via Replay

# After tile pair:
# clear_dvalid on last MVMUL or separate SETRWC releases Src banks
```

---

## Fidelity Phases

The FPU multiplier array is physically **5-bit × 7-bit** (SrcA × SrcB). For full-precision
BF16 (7-bit mantissa) × BF16 multiplication, four passes are required — each pass consuming
a different slice of the mantissa bits.

### Fidelity Level Definitions

| Level | Enum value | Passes | Performance |
|-------|-----------|--------|-------------|
| LoFi | 0 | 1 (phase 0 only) | 4 TFLOPS |
| HiFi2 | 2 | 2 (phases 0+1) | 2 TFLOPS |
| HiFi3 | 3 | 3 (phases 0+1+2) | 1.33 TFLOPS |
| HiFi4 | 4 | 4 (phases 0+1+2+3) | 1 TFLOPS |

The underlying type is `uint8_t`. `is_high_fidelity(f)` returns `f != LoFi`.
For a HiFi level, `to_underlying(f)` gives the number of fidelity phase passes.

### BF16 Mantissa Bit Allocation per Phase

For BF16 data (7-bit explicit mantissa, 1 implicit leading bit = 8 bits total):

| Phase | SrcA bits consumed | SrcB bits consumed |
|-------|-------------------|-------------------|
| 0 | implicit 1 + top 4 mantissa bits [6:3] | implicit 1 + top 6 mantissa bits [6:1] |
| 1 | remaining 3 mantissa bits [2:0] | implicit 1 + top 6 mantissa bits [6:1] |
| 2 | implicit 1 + top 4 mantissa bits [6:3] | remaining 1 mantissa bit [0] |
| 3 | remaining 3 mantissa bits [2:0] | remaining 1 mantissa bit [0] |

For TF32/FP16 data (10-bit explicit mantissa, 1 implicit):

| Phase | SrcA bits consumed | SrcB bits consumed |
|-------|-------------------|-------------------|
| 0 | implicit 1 + top 4 mantissa bits [9:6] | implicit 1 + top 6 mantissa bits [9:4] |
| 1 | next 5 mantissa bits [5:1] | implicit 1 + top 6 mantissa bits [9:4] |
| 2 | implicit 1 + top 4 mantissa bits [9:6] | remaining 4 mantissa bits [3:0] |
| 3 | next 5 mantissa bits [5:1] | remaining 4 mantissa bits [3:0] |

Note: For SrcA TF32/FP16, bit [0] of the mantissa is never consumed by any phase.

### Multi-Pass Accumulation Mechanics

The FPU accumulates across phases using the **same Dst rows**. Each pass adds the partial
product (scaled by the appropriate power of 2 implicit in the mantissa position) to the
running Dst accumulator. The accumulator must be FP32 (or wide BF16) to preserve precision
across passes.

The LLK implements multi-pass via ADDR_MOD_5 which increments `FidelityPhase` by 1 at the
end of each replay sequence:

```python
# HiFi4: 4 passes over the same SrcA/SrcB into the same Dst
for phase in range(4):                # outer MOP loop count = to_underlying(math_fidelity)
    for mvmul in range(16):           # inner replay buffer (16 MVMUL)
        # FidelityPhase = phase during all 16 MVMULs
        MVMUL(CLR_NONE, ADDR_MOD_0_to_4)
    # ADDR_MOD_5 at replay end increments FidelityPhase
# Final SETRWC(CLR_A or CLR_B) resets FidelityPhase to 0 and releases Src
```

In LoFi, ADDR_MOD_5 has `FidelityIncr=0`, so there is only one pass per tile pair and the
FidelityPhase stays at 0. In HiFi4, ADDR_MOD_5 has `FidelityIncr=1`, and the MOP outer
loop runs 4 times.

### Fidelity and Precision Recommendations

| Data type | Recommended fidelity |
|-----------|---------------------|
| BFP4, BFP2, FP8 | LoFi (phase 0 already full precision) |
| BFP8 / BFP8a | LoFi for minimal, HiFi2 for full |
| BF16 | LoFi for draft, HiFi2/3 for "good", HiFi4 for full |
| TF32, FP16 | HiFi4 for near-full (bit [0] of SrcA not reachable) |

---

## ELWADD — Element-wise Add (opcode `0x28`)

### Summary

Computes `Dst = SrcA + SrcB` (or `Dst += SrcA + SrcB` with `dest_accum_en=1`), operating
on aligned 8×16 blocks. Broadcasting of a single SrcB row or column 0 is supported.

### Instruction Encoding

```
[31:24] opcode        = 0x28
[23:22] clear_dvalid   (2 bits) — same semantics as MVMUL
[21]    dest_accum_en  (1 bit)  — 0=overwrite Dst, 1=accumulate into Dst
[20:19] instr_mod19    (2 bits) — broadcast mode for SrcB
[18:14] addr_mode      (5 bits) — ADDR_MOD index
[13:0]  dst            (14 bits) — explicit Dst row offset
```

### `instr_mod19` / `dest_accum_en` Broadcast Modes

The `instr_mod19` field encodes which columns/rows of SrcB to broadcast:

| `instr_mod19` | Name | Effect |
|--------------|------|--------|
| 0 | `SRCB_NO_BCAST` | Normal element-wise, no broadcast |
| 1 | `SRCB_BCAST_COL` | Column 0 of each SrcB row broadcasts to all 16 columns |
| 2 | `SRCB_BCAST_ROW` | Row 0 of SrcB broadcasts to all 8 rows |
| 3 | `SRCB_BCAST_ALL` | Single SrcB scalar [row0][col0] broadcasts to all 8×16 |

### Data Flow

```
SrcA[bank][SrcARow .. SrcARow+7][0..15]  (8 rows, aligned to 8)
SrcB[bank][SrcBRow .. SrcBRow+7][0..15]  (8 rows, aligned to 8, or broadcast)
                    |
                    v
          element-wise addition:
          for i in 0..7, j in 0..15:
            result = SrcA[SrcARow+i][j] + SrcB[SrcBRow+bcast(i)][bcast(j)]
            if dest_accum_en:
                Dst[DstRow+i][j] += result
            else:
                Dst[DstRow+i][j]  = result
```

### Behavioral Model (Python pseudocode)

```python
def ELWADD(clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst_field):
    style, use_dst32b = compute_style(SrcA_format, INT8_math, FP16A_force)
    bcast_row = (instr_mod19 & 2) != 0    # row broadcast
    bcast_col = (instr_mod19 & 1) != 0    # column broadcast

    srca_row = RWC.SrcA & 0x38
    srcb_row = RWC.SrcB & (0x3F if bcast_row else 0x38)
    dst_row  = (dst_field + DEST_TARGET_REG_CFG_MATH_Offset + RWC.Dst + DEST_REGW_BASE_Base) & 0x3F8

    # Fidelity: ELWADD is not a multiply op — FidelityPhase is read but only
    # affects the result if non-zero (applies nonsensical /32 or /128 scaling).
    # Software must ensure FidelityPhase == 0 for ELWADD.
    fidelity = (RWC.FidelityPhase + ThreadConfig.FIDELITY_BASE_Phase) & 3

    for i in range(8):
        for j in range(16):
            ai = srca_row + i
            bi = srcb_row + (0 if bcast_row else i)
            bj = 0 if bcast_col else j
            a = read_src(SrcA[bank][ai][j], style)
            b = read_src(SrcB[bank][bi][bj], style)
            result = a + b
            # Fidelity scaling (only relevant if fidelity != 0; avoid this)
            if fidelity & 1: result /= 32.0
            if fidelity & 2: result /= 128.0
            if dest_accum_en:
                result += read_dst(dst_row + i, j, style, use_dst32b)
            write_dst(dst_row + i, j, result, style, use_dst32b)

    apply_clear_dvalid(clear_dvalid)
    apply_addr_mod(addr_mode)
```

### Typical LLK Usage

```c
// Standard eltwise add of two tiles into Dst:
TTI_ELWADD(p_setrwc::CLR_AB, 0, p_elwise::SRCB_NO_BCAST, ADDR_MOD_0, 0)
// The MOP outer loop repeats this for each 8-row block of the tile (4 times for 32-row tile)
// At the end: SETRWC(CLR_AB, ...) resets RWCs
```

The LLK `eltwise_binary_configure_addrmod<ELWADD>()` sets ADDR_MOD_0 with
`SrcA.incr=8, SrcB.incr=8, Dst.incr=8` (no broadcast) or `SrcB.incr=0` (COL broadcast).
ADDR_MOD_3 resets with `Dst.incr=8, c_to_cr=1` for the last instruction.

---

## ELWSUB — Element-wise Subtract (opcode `0x30`)

Identical to ELWADD but computes `result = SrcA[i][j] - SrcB[bi][bj]`.

All fields (`clear_dvalid`, `dest_accum_en`, `instr_mod19`, `addr_mode`, `dst`) have
identical encoding and semantics to ELWADD. The only difference is the subtraction instead
of addition.

**Supported data types:** same combinations as ELWADD. For INT8: saturating subtract.

**Note:** The opcode `0x30` vs `0x28` (ELWADD) and `0x27` (ELWMUL) — ELWSUB does not
share opcode `0x29` as sometimes documented; the Blackhole LLK uses `0x30`.

---

## ELWMUL — Element-wise Multiply (opcode `0x27`)

### Summary

Computes `Dst += SrcA * SrcB` element-wise, operating on aligned 8×16 blocks. Uses the
same fidelity phase mechanism as MVMUL since it also uses the 5×7 multiplier hardware.

### Instruction Encoding

Same field layout as ELWADD/ELWSUB with `dest_accum_en=0` (always accumulates into Dst;
to overwrite use ZEROACC first):

```
[31:24] opcode        = 0x27
[23:22] clear_dvalid   (2 bits)
[21]    dest_accum_en  (1 bit)  — always 0 for ELWMUL (accumulates unconditionally)
[20:19] instr_mod19    (2 bits) — broadcast mode for SrcB (same as ELWADD)
[18:14] addr_mode      (5 bits)
[13:0]  dst            (14 bits)
```

### Behavioral Model (Python pseudocode)

```python
def ELWMUL(clear_dvalid, instr_mod19, addr_mode, dst_field):
    style, use_dst32b = compute_style(SrcA_format, INT8_math, FP16A_force)
    bcast_row = (instr_mod19 & 2) != 0
    bcast_col = (instr_mod19 & 1) != 0
    fidelity = (RWC.FidelityPhase + ThreadConfig.FIDELITY_BASE_Phase) & 3

    srca_row = RWC.SrcA & 0x38
    srcb_row = RWC.SrcB & (0x3F if bcast_row else 0x38)
    dst_row  = (dst_field + DEST_TARGET_REG_CFG_MATH_Offset + RWC.Dst + DEST_REGW_BASE_Base) & 0x3F8

    for i in range(8):
        for j in range(16):
            bi = srcb_row + (0 if bcast_row else i)
            bj = 0 if bcast_col else j
            a = src_a_fidelity_bits(SrcA[bank][srca_row+i][j], fidelity, style)
            b = src_b_fidelity_bits(SrcB[bank][bi][bj], fidelity, style)
            result = a * b
            result += read_dst(dst_row + i, j, style, use_dst32b)
            write_dst(dst_row + i, j, result, style, use_dst32b)

    apply_clear_dvalid(clear_dvalid)
    apply_addr_mod(addr_mode)
```

### Fidelity for ELWMUL

ELWMUL uses the same 5×7 multiplier as MVMUL. For BF16 inputs requiring full precision,
the LLK programs 4 fidelity phases. The `eltwise_binary_configure_mop_standard` function
for HiFi ELWMUL uses:

```c
ckernel_template tmp(to_underlying(math_fidelity), innerloop,
                     TT_OP_ELWMUL(..., ADDR_MOD_0, 0));
tmp.set_last_inner_loop_instr(TT_OP_ELWMUL(..., ADDR_MOD_2, 0)); // advance fidelity
tmp.set_last_outer_loop_instr(TT_OP_ELWMUL(CLR_AB, ..., ADDR_MOD_3, 0)); // reset+clear
```

ADDR_MOD_2 increments `FidelityPhase` by 1 while clearing SrcA/SrcB RWCs.
ADDR_MOD_3 resets fidelity to 0 and applies `c_to_cr` on Dst to advance to the next face.

**LoFi ELWADD/ELWSUB:** These never use fidelity phases — the hardware still reads the
FidelityPhase counter but addition does not apply mantissa masking, so the only (bad) effect
of non-zero FidelityPhase is a nonsensical division by 32 or 128. Always ensure
FidelityPhase is 0 before issuing ELWADD/ELWSUB.

---

## GMPOOL — Global Max Pool (opcode `0x33`)

### Summary

Reduces a 16×16 block of SrcA to a single row by taking the column-wise maximum, then
element-wise-max accumulates that row into one row of Dst. SrcB provides per-row scaling
exponents (multiplied before comparison). Optionally tracks the argmax index.

### Instruction Encoding

```
[31:24] opcode           = 0x33
[23:22] clear_dvalid      (2 bits) — same as MVMUL
[21:19] instr_mod19       (3 bits) — 0=normal; pool/argmax mode flags
[18:15] pool_addr_mode    (4 bits) — encodes addressing and SrcB enable
[14]    max_pool_index_en (1 bit)  — 1=return argmax index in Dst low bits
[13:0]  dst               (14 bits) — Dst row offset
```

The `pool_addr_mode` field encodes both an address mode (low 2 bits) and SrcB enable flags
(upper bits). Typical calls use `pool_addr_mode = DIM_16X16` (p_gpool::DIM_16X16 = 1) to
reduce a full 16×16 block.

### Data Flow

```
SrcB[bank][SrcBRow][0..15]   (1 row of scaling exponents, aligned to 8-row boundary)
SrcA[bank][SrcARow..+15][0..15]  (16 rows, aligned to 16-row boundary)
                     |
                     v
For each column j:
  scale_j = exp2(floor(log2(abs(SrcB[SrcBRow][j]))))
  for each row i in 0..15:
    scaled_a[i][j] = SrcA[SrcARow+i][j] * scale_j    (exponent-only scale)
  col_max[j] = max(scaled_a[0..15][j])                (column-wise max)
  Dst[DstRow][j] = max(col_max[j], Dst[DstRow][j])    (accumulate max)
```

The output lands in **one row** of Dst (the top row of a 4-row aligned block). The other
3 rows of the block are zeroed.

### Behavioral Model (Python pseudocode)

```python
def GMPOOL(clear_dvalid, instr_mod19, pool_addr_mode, max_pool_index_en, dst_field):
    style, use_dst32b = compute_style(SrcA_format, INT8_math, FP16A_force)
    argmax = max_pool_index_en

    srca_row = RWC.SrcA & 0x30       # aligned to 16-row boundary
    srcb_row = RWC.SrcB & 0x38       # aligned to 8-row boundary
    dst_row  = (dst_field + DEST_TARGET_REG_CFG_MATH_Offset + RWC.Dst + DEST_REGW_BASE_Base) & 0x3FC  # 4-row aligned

    for j in range(16):              # iterate over columns
        # Read current Dst value as initial maximum
        dst_val = read_dst32b(dst_row, j) if use_dst32b else (read_dst16b(dst_row, j) << 16)
        cur_max = decode_dst_as_datum(dst_val, style)
        max_index = dst_val & 0xFF
        index_phase = (dst_val + 0x100) & 0xF00

        # Read SrcB column for scaling exponent (transposed: SrcB row 0 col j -> scale for SrcA col j)
        scale_exp = SrcB[bank][srcb_row][j]

        for i_ in range(16):
            i = (i_ ^ 4) if i_ < 8 else i_   # non-linear visit order for argmax tie-breaking
            srca_val = SrcA[bank][srca_row + i][j]
            scaled = read_and_scale_src(srca_val, style, scale_exp)
            if as_comparable(scaled) >= as_comparable(cur_max):
                cur_max = scaled
                if i < 8:
                    NONLINEAR = [0, 3, 6, 1, 4, 7, 2, 5]
                    max_index = (index_phase >> 4) + NONLINEAR[i]

        # Write result back
        result = encode_datum(cur_max, style)
        if argmax:
            index_result = index_phase | max_index
            write_dst32b(dst_row, j, result | index_result)
        else:
            write_dst(dst_row, j, result, style, use_dst32b)

        # Zero the other 3 rows of the 4-row block
        for i in range(1, 4):
            write_dst(dst_row + i, j, 0, style, use_dst32b)

    apply_clear_dvalid(clear_dvalid)
    apply_addr_mod(pool_addr_mode & 3)
```

### `max_pool_index_en` (Argmax mode)

When `max_pool_index_en=1`:
- `Dst` must be in 32-bit mode (`ALU_ACC_CTRL_Fp32_enabled=1`)
- The index of the maximum element within the first 8 rows of each column is returned in
  the low 16 bits of `Dst32b`
- A non-linear transform is applied to the index — software must reverse it
- For BF16/FP16 data: the max value is returned in the high 16 bits simultaneously

### `pool_addr_mode` Constants

```c
p_gpool::DIM_1X16  = 0   // pool a 1×16 row (no SrcA column reduction)
p_gpool::DIM_16X16 = 1   // pool a 16×16 block (standard global max pool)
```

### Usage Pattern for Max Pooling

```c
// Initialize Dest to -infinity via ZEROACC + ZEROSRC (SrcA = -inf)
// Then for each input block:
STALLWAIT(SRCA_VLD | SRCB_VLD, MATH)    // wait for unpack to finish
TTI_GMPOOL(CLR_AB, 0, p_gpool::DIM_16X16, 0, 0)  // accumulate max
```

---

## ZEROACC — Zero the Accumulator / Mark Dst Invalid (opcode `0x10`)

### Summary

Marks rows of Dst as "undefined" (invalid). Subsequent FPU reads treat undefined rows as
the identity element (0 for MVMUL/ELWADD/ELWMUL, −∞ for GMPOOL). Packers treat undefined
rows as 0.

### Instruction Encoding

```
[31:24] opcode           = 0x10
[23:19] clear_mode        (5 bits) — which rows to clear (see modes table)
[18]    use_32_bit_mode   (1 bit)  — 0=16-bit row indexing, 1=32-bit row indexing
[17]    clear_zero_flags  (1 bit)  — 1=also reset zero-detect flags
[16:14] addr_mode         (3 bits) — ADDR_MOD index (only for CLR_SPECIFIC/CLR_16)
[13:0]  where             (14 bits) — row address or bank index
```

### `clear_mode` Values

| `clear_mode` | `p_zeroacc` constant | Effect |
|-------------|---------------------|--------|
| 0b000 (0) | `CLR_SPECIFIC` | Clear 1 specific row (addressed by `where` + RWC offset) |
| 0b001 (1) | `CLR_16` | Clear 16 consecutive rows starting at `where` × 16 (or ×32 in 32-bit mode) |
| 0b010 (2) | `CLR_HALF` | Clear low half (rows 0–511) if `where` bit0=0, high half if bit0=1 |
| 0b011 (3) | `CLR_ALL` | Clear all 1024 rows (or all 512 32-bit rows) |
| 0b110 (6) | `CLR_HALF_32B` | Alias for CLR_HALF with 32-bit mode |
| 0b111 (7) | `CLR_ALL_32B` | Alias for CLR_ALL with 32-bit mode |

### Behavioral Model

```python
def ZEROACC(clear_mode, use_32_bit_mode, clear_zero_flags, addr_mode, where):
    if clear_mode == CLR_SPECIFIC:                   # single row
        row = where
        row += DEST_TARGET_REG_CFG_MATH_Offset
        row += RWC.Dst + DEST_REGW_BASE_Base
        if Fp32_enabled or INT8_math or DBG_FEATURE_DISABLE[11]:
            DstRowValid[Adj32(row)] = False
        else:
            DstRowValid[row] = False
        apply_addr_mod(addr_mode)

    elif clear_mode == CLR_16:                       # 16-row block
        if use_32_bit_mode:
            # block address `where` selects a 16-row group in 32-bit layout
            for i in range(16):
                DstRowValid[where*32 + (i & 8)*2 + (i & 7)] = False
        else:
            for i in range(16):
                DstRowValid[where * 16 + i] = False
        apply_addr_mod(addr_mode)

    elif clear_mode == CLR_HALF:                     # half Dest
        start = 512 if (where & 1) else 0
        for row in range(start, start + 512):
            DstRowValid[row] = False
        # No addr_mod applied

    elif clear_mode == CLR_ALL:                      # all of Dest
        for row in range(1024):
            DstRowValid[row] = False
        # No addr_mod applied
```

### Common Usage

```c
// Before matmul: clear entire Dest
TTI_ZEROACC(p_zeroacc::CLR_ALL, 0, 0, ADDR_MOD_1, 0);
// Encodes to: 0x10184000 (from matmul_peak TRISC1):
// clear_mode=3 (CLR_ALL), use_32b=0, clr_zf=0, addr_mode=1, where=0

// Before eltwise into specific tile slot:
TTI_ZEROACC(p_zeroacc::CLR_16, 0, 0, ADDR_MOD_0, tile_index * 2);
// Clears 16 rows starting at tile_index*32 in 16-bit mode
```

**Note:** `CLR_HALF` and `CLR_ALL` do not apply the ADDR_MOD; they are "bulk" operations.
Only `CLR_SPECIFIC` and `CLR_16` update RWCs via ADDR_MOD.

**Trick:** `ZEROACC(CLR_16, where=0xFF)` does nothing (out-of-range is a NOP in silicon)
but still applies ADDR_MOD. This is occasionally used to advance RWCs without any
side effects on Dst.

---

## ZEROSRC — Zero SrcA and/or SrcB (opcode `0x11`)

### Summary

Fills all 64 rows × 16 columns of one or both banks of SrcA and/or SrcB with zero
(or negative infinity for SrcA).

### Instruction Encoding

```
[31:24] opcode     = 0x11
[23:4]  zero_val   (20 bits) — value to write (usually 0; for NegInf pattern this is ~0)
[3]     write_mode (1 bit)   — 0=write zero, 1=write zero_val pattern
[2]     bank_mask  (1 bit)   — 0=clear Unpacker bank, 1=clear MatrixUnit bank
[1:0]   src_mask   (2 bits)  — CLR_A=1, CLR_B=2, CLR_AB=3
```

The `write_mode`, `bank_mask`, `src_mask` names in the LLK macros map to the Wormhole
functional model fields `SingleBankMatrixUnit`, `BothBanks`, and `ClearSrcA`/`ClearSrcB`.

### Behavioral Model

```python
def ZEROSRC(zero_val, write_mode, bank_mask, src_mask):
    clear_srca = (src_mask & 1) != 0
    clear_srcb = (src_mask & 2) != 0
    neg_inf_srca = (write_mode == 1) and (zero_val != 0)

    clear_a_banks = [False, False]
    clear_b_banks = [False, False]

    if clear_srca:
        if bank_mask == 1:       # both banks
            clear_a_banks = [True, True]
        elif bank_mask == 0:     # Unpacker's current bank (default)
            clear_a_banks[Unpackers[0].SrcBank] = True
        # bank_mask with SingleBankMatrixUnit: FPU's current bank
        # (controlled by write_mode bit in Wormhole encoding)

    if clear_srcb:
        if bank_mask == 1:       # both banks
            clear_b_banks = [True, True]
        else:
            clear_b_banks[Unpackers[1].SrcBank] = True

    for bank in range(2):
        for row in range(64):
            for col in range(16):
                if clear_a_banks[bank]:
                    SrcA[bank][row][col] = 0x7FFFF if neg_inf_srca else 0
                if clear_b_banks[bank]:
                    SrcB[bank][row][col] = 0
```

### Common Patterns

```c
// Clear both banks of SrcA and SrcB (used between kernels):
TTI_ZEROSRC(0, 0, 1, p_zerosrc::CLR_AB);   // bank_mask=1 clears both banks

// Clear just the Unpacker's write bank of SrcA (used in unpack kernel):
TTI_ZEROSRC(0, 0, 0, p_zerosrc::CLR_A);

// Fill SrcA with negative infinity (for pooling init):
// Issued as UNPACR_NOP with UNP_CLRSRC_NEGINF, not directly ZEROSRC
```

**Scheduling note:** When clearing a single bank, use STALLWAIT with condition codes
`SRCA_CLR` (C8) or `SRCB_CLR` (C9) to wait for the clear to complete before issuing
FPU instructions that read from SrcA or SrcB.

---

## MOVB2D — Move SrcB to Dest (opcode `0x13`)

### Summary

Copies 1, 4, or 8 rows from SrcB to Dst, with optional broadcasting and format conversion.
Does not require SrcA. Useful for loading bias vectors or pre-computed values directly into
the accumulator.

### Instruction Encoding

```
[31:24] opcode           = 0x13
[23]    dest_32b_lo       (1 bit) — write to low 16 bits of Dst32b
[22:17] src               (6 bits) — explicit SrcB row, added to RWC.SrcB
[16:14] addr_mode         (3 bits) — ADDR_MOD index
[13:11] movb2d_instr_mod  (3 bits) — transfer mode
[10:0]  dst               (11 bits) — Dst row offset
```

### `movb2d_instr_mod` Transfer Modes

```c
p_movb2d::MOV_1_ROW          = 0   // copy 1 row
p_movb2d::MOV_1_ROW_D0_BRCST = 1   // copy row, broadcast col 0 to all columns
p_movb2d::MOV_8_ROW_BRCST    = 2   // broadcast 1 SrcB row to 8 Dst rows
p_movb2d::MOV_8_ROW_BRCST_D0_BRCST = 3  // broadcast 1 row + col 0
p_movb2d::MOV_4_ROWS          = 4   // copy 4 aligned rows
p_movb2d::MOV_4_ROWS_D0_BRCST = 5   // copy 4 rows, col 0 broadcast
```

### Data Flow

SrcB data types (BF16, TF32) are narrowed to fit Dst16b or expanded to Dst32b depending
on the ALU format configuration:

- BF16 in SrcB → Dst16b: strip low 3 mantissa bits (already zero in BF16)
- TF32 in SrcB → Dst32b (FP32): high 16 bits to Dst16b upper, low 3 mantissa bits reconstructed
- FP16/INT8 in SrcB → Dst16b: pass through (strip high exponent bits)

### Latency

After MOVB2D completes, software must avoid reading the written Dst region for 3 cycles.
The hardware automatically inserts 1 stall cycle if certain FPU instructions immediately follow.

---

## MOVD2A — Move Dest to SrcA (opcode `0x08`)

### Summary

Copies 1 or 4 aligned rows from Dst back to SrcA. Used for SFPU-assisted operations that
need to write results back to SrcA for a subsequent MVMUL.

### Instruction Encoding

```
[31:24] opcode       = 0x08
[23]    dest_32b_lo   (1 bit) — read from low 16 bits of Dst32b
[22:17] src           (6 bits) — explicit SrcA destination row, added to RWC.SrcA
[16:14] addr_mode     (3 bits) — ADDR_MOD index
[13:12] instr_mod     (2 bits) — p_movd2a::MOV_1_ROW=0, MOV_4_ROWS=2
[11:0]  dst           (12 bits) — Dst source row offset
```

### Format Conversion (Dst → SrcA)

| Dst format (16-bit mode) | SrcA format | Conversion |
|--------------------------|-------------|-----------|
| BF16 | BF16 | ShuffleBF16: sign/exp preserved, mantissa bits reordered |
| FP16 | FP16 | ShuffleFP16: high 3 exponent bits zeroed |
| INT8 | INT8 | ShuffleFP16 (INT8 overlaid on FP16) |

| Dst format (32-bit mode) | SrcA format | Conversion |
|--------------------------|-------------|-----------|
| FP32 | BF16 | Truncate to 16-bit BF16, ShuffleBF16 |
| FP32 | TF32 | Convert FP32 → TF32: keep top 10 mantissa bits |
| FP32 | FP16 | Truncate high 16 bits, ShuffleFP16 |

### Latency and Scheduling

MOVD2A does **not** automatically wait for SrcA bank ownership. Software must issue:

```c
TTI_STALLWAIT(p_stall::STALL_MATH, p_stall::SRCA_CLR);  // wait until SrcA bank is ready
TTI_MOVD2A(0, src_row, ADDR_MOD_0, p_movd2a::MOV_1_ROW, dst_row);
```

After MOVD2A, the Matrix Unit can only accept another MOVD2A or MOVB2A on the next cycle.
Any other FPU instruction forces a 1-cycle hardware stall.

---

## MOVD2B — Move Dest to SrcB (opcode `0x0A`)

Identical in structure and semantics to MOVD2A but writes to SrcB instead of SrcA.

```
[31:24] opcode       = 0x0A
[23]    dest_32b_lo   (1 bit)
[22:17] src           (6 bits) — SrcB destination row
[16:14] addr_mode     (3 bits)
[13:12] instr_mod     (2 bits) — MOV_1_ROW=0, MOV_4_ROWS=2
[11:0]  dst           (12 bits) — Dst source row
```

The format conversion `ShuffleBF16`, `ShuffleFP16`, `ShuffleTF32` functions are identical
to MOVD2A but target SrcB layout conventions. Latency: 3 cycles before Dst region can be
read again; hardware stalls 1 cycle before most FPU instructions that follow.

---

## Dst Address Space and Double-Buffering

The Dest register is 1024 rows × 16 columns of 16-bit data (or 512×16 of 32-bit).
It is split into two halves for double-buffering between the math and pack threads:

```
Rows 0–511:   "Low half"  — used by T1 while T2 packs the other half
Rows 512–1023: "High half" — used by T1 while T2 packs the first half
```

The active half is selected by `DEST_REGW_BASE_Base` (0 or 512), flipped by
`dest_section_flip()` at the end of each compute phase. `DEST_TARGET_REG_CFG_MATH_Offset`
provides an additional per-tile offset within the active half, set by
`math::set_dst_write_addr()`.

In FP32 mode (`Fp32_enabled=1`), the logical 512-row space maps to a different physical
interleaving via `Adj32(row)`:

```c
// Dst32b[Row][Col] reads:
uint32_t hi = DstBits[Adj32(Row)][Col];      // high 16 bits
uint32_t lo = DstBits[Adj32(Row) + 8][Col];  // low 16 bits
result = (hi << 16) | lo;
```

The `Adj32` swizzle means that **FP32 mode uses half as many tiles** as FP16/BF16 mode.

---

## Instruction Scheduling Constraints Summary

| Instruction | Wait Gate condition | Post-issue stall |
|-------------|---------------------|-----------------|
| MVMUL | SrcA.AllowedClient==FPU && SrcB.AllowedClient==FPU | None |
| ELWADD/ELWSUB/ELWMUL | Same as MVMUL | None |
| GMPOOL | Same as MVMUL | None |
| MOVB2D | SrcB.AllowedClient==FPU | 3 cycles before reading written Dst; 1 auto-stall before matmul ops |
| MOVD2A | Must use STALLWAIT(SRCA_CLR) first | 1 cycle before other FPU ops |
| MOVD2B | Must use STALLWAIT(SRCB_CLR) first | 1 cycle before other FPU ops |
| ZEROACC | None | None |
| ZEROSRC | None | Use STALLWAIT(SRCA_CLR/SRCB_CLR) before reading cleared bank |

---

## Complete Matmul Initialization Sequence (Annotated)

From `blackhole-py/disasms/matmul_peak/matmul_trisc1.S` (decoded):

```asm
; --- TRISC1 math kernel init ---
; 1. Push ZEROACC (CLR_ALL) to clear all of Dest
;    0x10184000: opcode=0x10, clear_mode=3 (CLR_ALL), use_32b=0, addr_mode=1, where=0
sw t0, 0(a5)          ; push ZEROACC(CLR_ALL, 0, 0, ADDR_MOD_1, 0) to instrn_buf

; 2. Push SETRWC to reset all RWCs (SrcA, SrcB, Dst, FidelityPhase)
;    SETRWC(CLR_NONE, 0, 0, 0, 0, SET_ABD_F) = 0x3700000f
sw t0, 0(a5)          ; push SETRWC reset

; 3. Configure ADDR_MOD slots via SETC16 (ThreadConfig writes)
;    ADDR_MOD_0: SrcA.incr=0, SrcB.incr=8, Dst.incr=8  (inner face step)
;    ADDR_MOD_1: SrcA.incr=16, SrcB.cr, Dst.incr=8     (SrcA face advance)
;    ADDR_MOD_2: SrcA.cr, SrcB.incr=32, Dst.incr=8     (SrcB face advance)
;    ADDR_MOD_4: SrcA.incr=32, SrcB.cr+48, Dst.cr      (wrap to next quad)
;    ADDR_MOD_5: all.clr+cr, Fidelity.incr=0 (LoFi)    (final reset)

; 4. Load replay buffer with 16 MVMUL instructions (via load_replay_buf)
;    Bytes in PT_LOAD at 0x6400:
;    98000000 98010000 98000000 98020000  -> MVMUL * 4 (addr_modes 0,1,0,2)
;    98000000 98010000 98000000 98040000  -> MVMUL * 4 (addr_modes 0,1,0,4)
;    98000000 98010000 98000000 98020000  -> MVMUL * 4 (addr_modes 0,1,0,2)
;    98000000 98010000 98000000 98050000  -> MVMUL * 4 (addr_modes 0,1,0,5)

; 5. Program MOP template (ckernel_template):
;    OuterCount=1, InnerCount=1 (LoFi: single pass)
;    LoopOp = REPLAY(buf_offset, 16)
;    EndOp  = SETRWC(CLR_B, 0, 0, 0, 0, SET_ABD_F)  [clear SrcB, reset counters]

; --- Per-tile execution ---
; set_dst_write_addr(tile_idx):  writes DEST_TARGET_REG_CFG_MATH_Offset
; MOP_RUN: expands to REPLAY -> 16 MVMUL instructions
;   Each MVMUL reads 8 rows of SrcB and 16 rows of SrcA, accumulates into 8 rows Dst
; After 16 MVMULs: SETRWC(CLR_B) releases SrcB, resets all RWCs
```

---

## Source References

| Source | Path | What it documents |
|--------|------|-------------------|
| MVMUL ISA (Wormhole, closely matches Blackhole) | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/MVMUL.md` | Full functional model, fidelity, SrcA/SrcB bank semantics |
| ELWADD ISA | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/ELWADD.md` | ELWADD functional model |
| ELWMUL ISA | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/ELWMUL.md` | ELWMUL functional model, fidelity bit tables |
| GMPOOL ISA | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/GMPOOL.md` | Pool + argmax functional model |
| ZEROACC ISA | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/ZEROACC.md` | All clear modes |
| ZEROSRC ISA | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/ZEROSRC.md` | Bank clearing |
| MOVB2D ISA | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/MOVB2D.md` | SrcB→Dst format conversion |
| MOVD2A ISA | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/MOVD2A.md` | Dst→SrcA format conversion |
| MOVD2B ISA | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/MOVD2B.md` | Dst→SrcB format conversion |
| SrcA/SrcB register spec | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/SrcASrcB.md` | Data types, fidelity phase tables |
| Dst register spec | `tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/Dst.md` | Dst layout, Adj16/Adj32, 32b mode |
| RWC documentation | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/RWCs.md` | ApplyAddrMod, SETRWC/INCRWC |
| Matmul LLK | `tt-llk/tt_llk_blackhole/llk_lib/llk_math_matmul.h` | MOP/replay programming, addrmod config |
| Eltwise binary LLK | `tt-llk/tt_llk_blackhole/llk_lib/llk_math_eltwise_binary.h` | ELWADD/ELWSUB/ELWMUL MOP programming |
| Common math LLK | `tt-llk/tt_llk_blackhole/llk_lib/llk_math_common.h` | set_fp32_dest_acc, hw_configure |
| Instruction params | `tt-llk/tt_llk_blackhole/common/inc/ckernel_instr_params.h` | p_zeroacc, p_zerosrc, p_setrwc, p_elwise, p_gpool |
| Instruction macros | `tt-llk/tt_llk_blackhole/common/inc/ckernel_ops.h` | TT_OP_MVMUL, TT_OP_ELWADD, etc. (bit positions) |
| Config register defs | `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/cfg_defines.h` | ALU_FORMAT_SPEC, ALU_ACC_CTRL ADDR32 positions |
| Matmul peak disassembly | `blackhole-py/disasms/matmul_peak/matmul_trisc1.S` | Real MVMUL instruction sequence |
| Matrix engine tech report | `tt-metal/tech_reports/matrix_engine/matrix_engine.md` | TFLOPS, fidelity phase mantissa mapping |
| Backend configuration | `tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/BackendConfiguration.md` | Config/ThreadConfig architecture |
