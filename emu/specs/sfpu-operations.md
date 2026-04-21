# Vector Unit (SFPU) Operations

## Overview

The Vector Unit (SFPU) is a 32-lane SIMD unit inside the Tensix coprocessor. Each lane operates on 32-bit values independently. The SFPU is composed of five sub-units that can operate concurrently when `SFPLOADMACRO` is used, but in the normal case only one sub-unit executes per cycle:

| Sub-unit | Instructions |
|----------|-------------|
| Load     | `SFPLOAD`, `SFPLOADI`, `SFPLOADMACRO`, `SFPNOP` |
| Simple   | Most 1-cycle arithmetic and bit-manipulation instructions |
| MAD      | `SFPMAD`, `SFPADD`, `SFPMUL`, `SFPADDI`, `SFPMULI`, `SFPLUTFP32`, `SFPMUL24` |
| Round    | `SFPSTOCHRND`, `SFPSHFT2` |
| Store    | `SFPSTORE` |

The SFPU clocks at 1.35 GHz on Blackhole A0.

---

## 1. LReg Register File

### 1.1 Register Array

The register file is modelled as:

```c
union { uint32_t u32; int32_t i32; float f32; } LReg[17][32];
```

The `[17]` entries are not all uniform. Only `LReg[0..7]` are general-purpose writable compute registers. The remainder are read-only constants, programmable constants, or special-purpose entries.

### 1.2 Full Register Map

| Index | Alias(es) | Type | Value / Description |
|-------|-----------|------|---------------------|
| 0 | `LREG0` | Read/Write | General-purpose compute register |
| 1 | `LREG1` | Read/Write | General-purpose compute register |
| 2 | `LREG2` | Read/Write | General-purpose compute register |
| 3 | `LREG3` | Read/Write | General-purpose compute register; used as LUT input by `SFPLUTFP32` |
| 4 | `LREG4` | Read/Write | General-purpose compute register |
| 5 | `LREG5` | Read/Write | General-purpose compute register |
| 6 | `LREG6` | Read/Write | General-purpose compute register |
| 7 | `LREG7` | Read/Write | General-purpose compute register; low 4 bits used as indirect register index by `SFPMAD_MOD1_INDIRECT_VA/VD` |
| 8 | `LCONST_0_8373`, `CREG_IDX_0P837300003` | Read-only | All 32 lanes contain `0.8373f` (FP32 bit pattern `0x3F566189`) |
| 9 | `LCONST_0`, `CREG_IDX_0` | Read-only | All 32 lanes contain `0.0f` (all bits zero, universal across all data types) |
| 10 | `LCONST_1`, `CREG_IDX_1` | Read-only | All 32 lanes contain `1.0f` (FP32 bit pattern `0x3F800000`) |
| 11 | `LREG11`, `LCONST_neg1`, `CREG_IDX_NEG_1`, `CREG_IDX_PRGM0` | Programmable constant | Writable only via `SFPCONFIG`. SFPI compiler convention: `-1.0f` (`0xBF800000`) |
| 12 | `LREG12`, `CREG_IDX_PRGM1` | Programmable constant | Writable only via `SFPCONFIG`. `SFPCONFIG` default: `1.0f/512.0f` (`0x3B000000`) |
| 13 | `LREG13`, `CREG_IDX_PRGM2` | Programmable constant | Writable only via `SFPCONFIG`. `SFPCONFIG` default: `-0.67487759f` (`0xBF2CC4C7`) |
| 14 | `LREG14`, `CREG_IDX_PRGM3` | Programmable constant | Writable only via `SFPCONFIG`. `SFPCONFIG` default: `-0.34484843f` (`0xBEB08FF9`) |
| 15 | `LTILEID`, `CREG_IDX_TILEID` | Read-only | Lane `i` contains the integer value `i * 2` (i.e. 0, 2, 4, ..., 62) |
| 16 | _(internal)_ | Special | Writable only by instructions scheduled via `SFPLOADMACRO`; readable only by `SFPSTORE` scheduled via `SFPLOADMACRO` |

**Hardware-fixed constants** (indices 8, 9, 10, 15) are set by silicon and require no initialization.

**Programmable constants** (indices 11–14) are 32-lane registers that are effectively 8-lane: `SFPCONFIG` always takes input from the first 8 lanes of `LReg[0]` and broadcasts them vertically to all 32 lanes. The SFPI compiler initializes `LReg[11]` to `-1.0f` at startup. The firmware function `ex_load_const()` called by BRISC at boot loads any other constants the software stack requires.

### 1.3 Lane Layout

Each `LReg[i]` is 32 lanes of 32 bits. For cross-lane operations it is useful to view those 32 lanes as a 4×8 grid (4 rows, 8 columns):

```
Lane  0  Lane  1  Lane  2  Lane  3  Lane  4  Lane  5  Lane  6  Lane  7   (Row 0)
Lane  8  Lane  9  Lane 10  Lane 11  Lane 12  Lane 13  Lane 14  Lane 15   (Row 1)
Lane 16  Lane 17  Lane 18  Lane 19  Lane 20  Lane 21  Lane 22  Lane 23   (Row 2)
Lane 24  Lane 25  Lane 26  Lane 27  Lane 28  Lane 29  Lane 30  Lane 31   (Row 3)
```

Instructions that operate purely lanewise (the vast majority) do not care about this layout. Instructions involving cross-lane movement (`SFPSHFT2`, `SFPCONFIG`, `SFPTRANSP`) move data horizontally or vertically within this grid.

### 1.4 Data Types

Each `LReg` slot holds 32 bits interpreted as one of:

- **FP32**: IEEE 754 single precision (1 sign, 8 exponent, 23 mantissa). Denormals are flushed to zero on output from arithmetic; arithmetic treats denormal inputs as zero.
- **uint32_t**: Unsigned 32-bit integer.
- **int32_t**: Signed two's complement 32-bit integer.
- **Sign-magnitude int32**: 1 sign bit, 31 magnitude bits (same format as Dst Integer "32"). Non-negative values share the same bit pattern across all three integer types.

Software may bitcast freely between any of these types.

---

## 2. SFPLOAD / SFPSTORE — Dest ↔ LReg Data Movement

### 2.1 Dest Addressing

Dest is a 1024×16 array of 16-bit cells (or 512×16 of 32-bit cells in `Dst32b` mode). `SFPLOAD` and `SFPSTORE` operate on a slice of 4 consecutive rows × 8 columns (even or odd) = 32 elements, matching one full LReg.

The effective address `Addr` is a 10-bit value computed as:

```
Addr = Imm10 + DEST_TARGET_REG_CFG_MATH_Offset
     + RWCs[Thread].Dst + Config.DEST_REGW_BASE_Base
     + (RWCs[Thread].Sp + Config.DEST_SP_BASE_Base) & 3
```

(The `MOD0_FMT_INT32_ALL` mode uses a different formula with the Sp and Dst offsets swapped; it also automatically decrements `RWCs.Sp` on load and increments it on store.)

The address bits determine:
- `Addr[9:2]` — selects an aligned group of 4 rows.
- `Addr[1]` — selects even columns (`0`) or odd columns (`1`).
- `Addr[0]` — unused.

### 2.2 Lane-to-Dest Mapping

For a given `Addr`:

```python
def lane_to_dst(addr, lane):
    row    = (addr & ~3) + (lane // 8)   # 4-row group + which row within group
    col    = (lane & 7) * 2              # even column (0, 2, 4, ..., 14)
    if (addr & 2) or DEST_RD_COL_EXCHANGE:
        col += 1                         # odd column instead
    return row, col
```

A full 16×16 tile in Dest (256 elements) requires **8 SFPLOAD + INCRWC** cycles:

```
SFPLOAD  LReg[x], ..., Addr=0   → loads rows 0-3, even cols → 32 elements
INCRWC   (advances Dst RWC by 1)
SFPLOAD  LReg[x], ..., Addr=0   → loads rows 0-3, odd cols  → 32 elements
INCRWC   (advances Dst RWC by 1)
SFPLOAD  LReg[x], ..., Addr=0   → loads rows 4-7, even cols → 32 elements
...
(8 total SFPLOAD instructions cover the full 16×16 = 256-element tile)
```

### 2.3 SFPLOAD Syntax and Mode Table

```c
TT_SFPLOAD(/* u4 */ VD, /* u4 */ Mod0, /* u3 */ AddrMod, /* u10 */ Imm10)
```

`VD` must be 0–7 for the instruction to have any effect. `AddrMod` selects an address modifier from the address modifier table (see pack/unpack-registers.md).

| `Mod0` | Value | Dst source type | LReg result type | Notes |
|--------|-------|-----------------|------------------|-------|
| `MOD0_FMT_SRCB` | 0 | Resolves based on config | — | Resolves to FP32, BF16, or FP16 depending on `ALU_FORMAT_SPEC_REG` |
| `MOD0_FMT_FP16` | 1 | FP16 (Sign,Man10,Exp5) | FP32 | Rebiases exponent by +112; optionally remaps max to Inf |
| `MOD0_FMT_BF16` | 2 | BF16 (Sign,Man7,Exp8 — shuffled) | FP32 | Unshuffles field order |
| `MOD0_FMT_FP32` | 3 | FP32 or Integer "32" (shuffled) | FP32 or sign-magnitude | Unshuffles field order |
| `MOD0_FMT_INT32` | 4 | Same as FP32 | Same as FP32 | Identical operation to MOD0_FMT_FP32 |
| `MOD0_FMT_INT8` | 5 | Integer "8" (Sign,Mag8,pad5) | Sign-magnitude | Range expanded from ±127 to ±255 vs Wormhole |
| `MOD0_FMT_UINT16` | 6 | Integer "16" (opaque 16b) | Unsigned (zero-extend) | |
| `MOD0_FMT_HI16` | 7 | Integer "16" (opaque 16b) | Unsigned (write to high 16, zero low 16) | |
| `MOD0_FMT_INT16` | 8 | Integer "16" (Sign,Mag15) | Sign-magnitude | |
| `MOD0_FMT_LO16` | 9 | Integer "16" (opaque 16b) | Unsigned (zero-extend) | |
| `MOD0_FMT_INT32_ALL` | 10 | FP32 or Integer "32" | FP32 or sign-magnitude | Special addressing; ignores `LaneEnabled` |
| `MOD0_FMT_ZERO` | 11 | — | Zero | Writes zero to all lanes |
| `MOD0_FMT_INT32_SM` | 12 | FP32 or Integer "32" | Sign-magnitude | Deprecated (no longer converts SM→2C) |
| `MOD0_FMT_INT8_COMP` | 13 | Integer "8" | Sign-magnitude | Deprecated |
| `MOD0_FMT_LO16_ONLY` | 14 | Integer "16" (opaque 16b) | Unsigned (write to low 16, preserve high 16) | |
| `MOD0_FMT_HI16_ONLY` | 15 | Integer "16" (opaque 16b) | Unsigned (write to high 16, preserve low 16) | |

**Dst bit-field shuffling:** Dst stores FP32 and BF16 with the sign and exponent fields swapped relative to IEEE 754 order. `SFPLOAD` unshuffles them. `SFPSTORE` re-shuffles them. The unshuffled form is:

```c
// Dst BF16 storage: Sign,Man(7b),Exp(8b)  →  LReg: Sign,Exp(8b),Man(7b)
// Dst FP32 storage: Sign,ManHi(7b),Exp(8b),ManLo(16b)  →  LReg: Sign,Exp(8b),ManHi(7b),ManLo(16b)
```

### 2.4 SFPSTORE Syntax and Mode Table

```c
TT_SFPSTORE(/* u4 */ VD, /* u4 */ Mod0, /* u3 */ AddrMod, /* u10 */ Imm10)
```

`VD` can be 0–11 (or 0–7 with `DISABLE_BACKDOOR_LOAD` false for values 8–11 which write to `LoadMacroConfig`). The mode table mirrors `SFPLOAD` but with conversions reversed:

| `Mod0` | Value | LReg source type | Dst result type | Notes |
|--------|-------|-----------------|-----------------|-------|
| `MOD0_FMT_SRCB` | 0 | Resolves | — | Same resolution as SFPLOAD |
| `MOD0_FMT_FP16` | 1 | FP32 (no NaN) | FP16 (shuffled) | Large values → Inf; denormals → ±0; NaN → Inf |
| `MOD0_FMT_BF16` | 2 | FP32 | BF16 (shuffled) | Truncates mantissa toward zero; flushes denormals |
| `MOD0_FMT_FP32` | 3 | FP32 | FP32 (shuffled) | Denormals flushed to signed zero (new in Blackhole) |
| `MOD0_FMT_INT32` | 4 | FP32 or sign-magnitude | FP32 or Integer "32" | Raw shuffle, no conversion |
| `MOD0_FMT_INT8` | 5 | Sign-magnitude ±1023 | Integer "8" | Uses fixed exponent of 16 in FP16 field |
| `MOD0_FMT_UINT16` | 6 | Unsigned (low 16b) | Integer "16" | |
| `MOD0_FMT_HI16` | 7 | Unsigned | Opaque 32b | High 16 written to full 32b Dst cell |
| `MOD0_FMT_INT16` | 8 | Sign-magnitude ±32767 | Integer "16" | |
| `MOD0_FMT_LO16` | 9 | Unsigned (rotate left 16) | Opaque 32b | |
| `MOD0_FMT_INT32_ALL` | 10 | FP32 or sign-magnitude | FP32 or Integer "32" | Special addressing; ignores `LaneEnabled` |
| `MOD0_FMT_ZERO` | 11 | — | Zero | |
| `MOD0_FMT_INT32_SM` | 12 | Sign-magnitude | Integer "32" | Deprecated (no longer converts 2C→SM) |
| `MOD0_FMT_INT8_COMP` | 13 | Sign-magnitude ±1023 | Integer "8" | Deprecated |
| `MOD0_FMT_LO16_ONLY` | 14 | Unsigned (low 16b) | Integer "16" | |
| `MOD0_FMT_HI16_ONLY` | 15 | Unsigned (high 16b) | Integer "16" | |

### 2.5 Instruction Scheduling for SFPLOAD/SFPSTORE

A minimum of **3 unrelated Tensix instructions** must execute between a Matrix Unit (FPU) instruction that writes to Dest and an `SFPLOAD` that reads that same region. If no useful instructions are available, any Tensix NOP works. `STALLWAIT` with block bit B8 and condition C7 also works but is not recommended.

---

## 3. Per-Instruction Semantics

The notation `lanewise { ... }` means the body executes independently for each of the 32 lanes. `LaneEnabled` is the per-lane predication result (see Section 4). Instructions that set `LaneFlags` do so regardless of whether the lane is enabled, unless otherwise noted.

### 3.1 SFPMAD — Multiply-Add

```c
TT_SFPMAD(/* u4 */ VA, /* u4 */ VB, /* u4 */ VC, /* u4 */ VD, /* u4 */ Mod1)
```

**Latency:** 2 cycles. **IPC:** 1.

Computes `VD = ±(VA * VB) ± VC` in FP32, lanewise.

```python
def sfpmad(VA, VB, VC, VD, Mod1, LReg):
    for lane in range(32):
        if not lane_enabled(lane): continue
        va = (LReg[7][lane] & 15) if (Mod1 & SFPMAD_MOD1_INDIRECT_VA) else VA
        a = LReg[va][lane]
        b = LReg[VB][lane]
        c = LReg[VC][lane]
        if Mod1 & SFPMAD_MOD1_NEGATE_VA: a ^= 0x80000000
        if Mod1 & SFPMAD_MOD1_NEGATE_VC: c ^= 0x80000000
        d = fma_fp32(a, b, c)  # partially fused, round-to-nearest-even
        vd = (LReg[7][lane] & 15) if ((Mod1 & SFPMAD_MOD1_INDIRECT_VD) and VD != 16) else VD
        if vd < 8 or vd == 16:
            LReg[vd][lane] = d
```

| `Mod1` bit | Name | Effect |
|-----------|------|--------|
| 0 | `SFPMAD_MOD1_NEGATE_VA` | Negate `VA` (flip sign bit) before multiply |
| 1 | `SFPMAD_MOD1_NEGATE_VC` | Negate `VC` (flip sign bit) before add |
| 2 | `SFPMAD_MOD1_INDIRECT_VA` | Use `LReg[7] & 0xF` as `VA` index (per lane) |
| 3 | `SFPMAD_MOD1_INDIRECT_VD` | Use `LReg[7] & 0xF` as `VD` index (per lane) |

**IEEE 754 notes:** Denormal inputs treated as zero. NaN/Inf propagate normally. If a NaN is emitted, it is always the canonical NaN `0x7FC00000`. Rounding is round-to-nearest-ties-to-even. Denormal output is flushed to sign-preserved zero.

**Auto-stalling:** Hardware automatically stalls the next instruction by 1 cycle if it reads a register written by `SFPMAD`. Exceptions: `SFPAND` with `SFPAND_MOD1_USE_VB`, `SFPOR` with `SFPOR_MOD1_USE_VB`, `SFPIADD` (does not detect VD read), `SFPSHFT` (does not detect VD read), `SFPCONFIG` (does not detect LReg[0] read), `SFPSWAP` (does not detect 1st-cycle reads), and certain modes of `SFPSHFT2` require manual `SFPNOP` insertion.

### 3.2 SFPADD — Floating-Point Add

```c
TT_SFPADD(/* u4 */ VA, /* u4 */ VB, /* u4 */ VC, /* u4 */ VD, /* u4 */ Mod1)
```

**Latency:** 2 cycles. **IPC:** 1.

Semantically identical to `SFPMAD`. Convention: set `VA = 10` (`LCONST_1`) so the computation is `VD = ±(1.0 * VB) ± VC`. Shares the same mode table and auto-stalling rules as `SFPMAD`.

### 3.3 SFPMUL — Floating-Point Multiply

```c
TT_SFPMUL(/* u4 */ VA, /* u4 */ VB, /* u4 */ VC, /* u4 */ VD, /* u4 */ Mod1)
```

**Latency:** 2 cycles. **IPC:** 1.

Semantically identical to `SFPMAD`. Convention: set `VC = 9` (`LCONST_0`) so the computation is `VD = ±(VA * VB) + 0`. To preserve the sign of negative zero products, use `SFPMAD_MOD1_NEGATE_VC` so the addend is `-0` rather than `+0`. Shares the same mode table and auto-stalling rules as `SFPMAD`.

### 3.4 SFPADDI — Add BF16 Immediate

```c
TT_SFPADDI(/* u16 */ Imm16, /* u4 */ VD, /* u4 */ Mod1)
```

**Latency:** 2 cycles. **IPC:** 1.

Computes `VD = BF16ToFP32(Imm16) + ±VD`. The source register is implicitly `VC = VD` (the destination is also read as an input).

```python
def bf16_to_fp32(imm16):
    return struct.unpack('f', struct.pack('I', imm16 << 16))[0]

# VD = BF16ToFP32(Imm16) * 1.0 + (±VC_old)
# where VC = VD initially
```

Supports `SFPMAD_MOD1_NEGATE_VC` (bit 1) to negate `VD` before adding, and `SFPMAD_MOD1_INDIRECT_VD` (bit 3) for indirect destination. Latency and auto-stalling as per `SFPMAD`.

### 3.5 SFPMULI — Multiply by BF16 Immediate

```c
TT_SFPMULI(/* u16 */ Imm16, /* u4 */ VD, /* u4 */ Mod1)
```

**Latency:** 2 cycles. **IPC:** 1.

Computes `VD = BF16ToFP32(Imm16) * ±VD + 0.0`. The embedded `+ 0.0` means negative zero results become positive zero. Supports `SFPMAD_MOD1_NEGATE_VC` (bit 1) and `SFPMAD_MOD1_INDIRECT_VD` (bit 3). Latency and auto-stalling as per `SFPMAD`.

**BF16-to-FP32 conversion:** The 16-bit immediate is interpreted as a BF16 value and expanded to FP32 by appending 16 zero bits in the low position. That is, `BF16ToFP32(x) = bitcast<float>(x << 16)`. There is no rounding, no denormal handling — it is a pure bit-position shift.

### 3.6 SFPDIVP2 — Adjust FP32 Exponent

```c
TT_SFPDIVP2(/* u8 */ Imm8, /* u4 */ VC, /* u4 */ VD, /* u4 */ Mod1)
```

**Latency:** 1 cycle. **IPC:** 1.

Adjusts the 8-bit exponent field of a FP32 value, leaving sign and mantissa unchanged.

```python
def sfpdivp2(Imm8, VC, VD, Mod1, LReg):
    for lane in range(32):
        if not lane_enabled(lane): continue
        c = LReg[VC][lane]
        Sign = c >> 31
        Exp  = (c >> 23) & 0xFF
        Man  = c & 0x7FFFFF
        if Mod1 & SFPDIVP2_MOD1_ADD:
            if Exp == 255:
                pass  # Inf and NaN left unchanged
            else:
                Exp = (Exp + Imm8) & 0xFF  # wrapping 8-bit addition
        else:
            Exp = Imm8  # replace exponent
        LReg[VD][lane] = (Sign << 31) | (Exp << 23) | Man
```

| `Mod1` bit | Name | Effect |
|-----------|------|--------|
| 0 | `SFPDIVP2_MOD1_ADD` | Add `Imm8` to exponent (wrapping); if clear, replace exponent with `Imm8` |

**Exponent wrapping:** When adding, the 8-bit addition wraps around modulo 256. Infinity and NaN (exponent = 255) are left unchanged when adding. Use `SFPMULI` instead if saturation behavior is needed.

### 3.7 SFPEXEXP — Extract FP32 Exponent

```c
TT_SFPEXEXP(0, /* u4 */ VC, /* u4 */ VD, /* u4 */ Mod1)
```

**Latency:** 1 cycle. **IPC:** 1.

Extracts the 8-bit exponent field of FP32 and deposits it as a 32-bit integer, optionally subtracting the bias 127.

```python
def sfpexexp(VC, VD, Mod1, LReg):
    Bias = 0 if (Mod1 & SFPEXEXP_MOD1_NODEBIAS) else 127
    for lane in range(32):
        if not lane_enabled(lane): continue
        Exp = (LReg[VC][lane] >> 23) & 0xFF
        LReg[VD][lane] = Exp - Bias  # two's complement integer result
        if VD < 8:
            if Mod1 & SFPEXEXP_MOD1_SET_CC_SGN_EXP:
                LaneFlags[lane] = (LReg[VD][lane] < 0)
            if Mod1 & SFPEXEXP_MOD1_SET_CC_COMP_EXP:
                LaneFlags[lane] = not LaneFlags[lane]
```

| `Mod1` bit | Name | Effect |
|-----------|------|--------|
| 0 | `SFPEXEXP_MOD1_NODEBIAS` | Do not subtract bias; result is raw biased exponent 0–255 |
| 1 | `SFPEXEXP_MOD1_SET_CC_SGN_EXP` | Set `LaneFlags` based on sign of result (negative means biased exp < 127, i.e. `|x| < 1.0`) |
| 3 | `SFPEXEXP_MOD1_SET_CC_COMP_EXP` | Complement (invert) the flag set by bit 1 |

With bias removal (default, `NODEBIAS` clear): result is in the range -127 (denormal/zero) through +128 (NaN/Inf), as a two's complement `int32_t`.

Without bias removal (`NODEBIAS` set): result is the raw biased exponent 0–255 as a `uint32_t`.

### 3.8 SFPEXMAN — Extract FP32 Mantissa

```c
TT_SFPEXMAN(0, /* u4 */ VC, /* u4 */ VD, /* u4 */ Mod1)
```

**Latency:** 1 cycle. **IPC:** 1.

Extracts the 23-bit mantissa field, deposits it in bits [22:0], and sets bit 23 to either 0 or 1.

```python
def sfpexman(VC, VD, Mod1, LReg):
    HiddenBit = 0 if (Mod1 & SFPEXMAN_MOD1_PAD9) else (1 << 23)
    for lane in range(32):
        if not lane_enabled(lane): continue
        Man = LReg[VC][lane] & 0x7FFFFF
        LReg[VD][lane] = HiddenBit + Man
```

| `Mod1` bit | Name | Result bit 23 |
|-----------|------|---------------|
| 0 (clear) | `SFPEXMAN_MOD1_PAD8` | 1 (the implicit leading 1 of a normalized mantissa) |
| 0 (set) | `SFPEXMAN_MOD1_PAD9` | 0 (only the raw 23-bit mantissa field) |

Bits [31:24] are always zero in the result.

### 3.9 SFPIADD — Integer Add/Subtract

```c
TT_SFPIADD(/* i12 */ (Imm12 & 0xFFF), /* u4 */ VC, /* u4 */ VD, /* u4 */ Mod1)
```

**Latency:** 1 cycle. **IPC:** 1.

Performs integer addition or subtraction. The result is written to `VD`. Lane flags may optionally be set based on the sign of the result.

```python
def sfpiadd(Imm12, VC, VD, Mod1, LReg):
    VB = VD  # destination also acts as second source in reg-reg mode
    for lane in range(32):
        if not lane_enabled(lane): continue
        if Mod1 & SFPIADD_MOD1_ARG_IMM:
            LReg[VD][lane] = LReg[VC][lane] + sign_extend_12(Imm12)
        elif Mod1 & SFPIADD_MOD1_ARG_2SCOMP_LREG_DST:
            LReg[VD][lane] = LReg[VC][lane] - LReg[VB][lane]
        else:
            LReg[VD][lane] = LReg[VC][lane] + LReg[VB][lane]
        # Truncate to 32 bits (unsigned wrapping)
        LReg[VD][lane] &= 0xFFFFFFFF
        if VD < 8:
            if not (Mod1 & SFPIADD_MOD1_CC_NONE):
                LaneFlags[lane] = (as_signed_32(LReg[VD][lane]) < 0)
            if Mod1 & SFPIADD_MOD1_CC_GTE0:
                LaneFlags[lane] = not LaneFlags[lane]
```

| `Mod1` value | Name | Effect |
|-------------|------|--------|
| 0 | `SFPIADD_MOD1_ARG_LREG_DST` | `VD = VC + VD` (reg-reg add) |
| 1 | `SFPIADD_MOD1_ARG_IMM` | `VD = VC + SignExt(Imm12)` (reg-immediate add) |
| 2 | `SFPIADD_MOD1_ARG_2SCOMP_LREG_DST` | `VD = VC - VD` (reg-reg subtract) |
| — | `SFPIADD_MOD1_CC_LT0` (= 0) | Set `LaneFlags = (result < 0)` |
| 4 | `SFPIADD_MOD1_CC_NONE` | Do not modify `LaneFlags` |
| 8 | `SFPIADD_MOD1_CC_GTE0` | Set `LaneFlags = (result >= 0)` |

Note: the `CC_NONE` and `CC_GTE0` bits can combine with the `ARG_*` bits. The Imm12 field is sign-extended to 32 bits.

**Hardware bug:** The auto-stalling logic does not detect that `SFPIADD` reads `VD`. If a preceding 2-cycle instruction (`SFPMAD` etc.) writes to `VD`, software must insert a manual `SFPNOP`.

### 3.10 SFPSETCC — Set Condition Codes

```c
TT_SFPSETCC(/* u1 */ Imm1, /* u4 */ VC, /* u4 */ VD, /* u4 */ Mod1)
```

**Latency:** 1 cycle. **IPC:** 1.

Sets `LaneFlags` per lane based on a comparison of `VC` against zero, or from an immediate bit, or clears it.

```python
def sfpsetcc(Imm1, VC, VD, Mod1, LReg):
    for lane in range(32):
        if not lane_enabled(lane): continue
        if not UseLaneFlagsForLaneEnable[lane]:
            LaneFlags[lane] = False
        elif Mod1 & SFPSETCC_MOD1_CLEAR:
            LaneFlags[lane] = False
        elif Mod1 & SFPSETCC_MOD1_IMM_BIT0:
            LaneFlags[lane] = bool(Imm1)
        else:
            c = as_signed_32(LReg[VC][lane])
            if   (Mod1 & 7) == SFPSETCC_MOD1_LREG_LT0:  LaneFlags[lane] = (c < 0)
            elif (Mod1 & 7) == SFPSETCC_MOD1_LREG_NE0:  LaneFlags[lane] = (c != 0)
            elif (Mod1 & 7) == SFPSETCC_MOD1_LREG_GTE0: LaneFlags[lane] = (c >= 0)
            elif (Mod1 & 7) == SFPSETCC_MOD1_LREG_EQ0:  LaneFlags[lane] = (c == 0)
```

| `Mod1` value | Name | Effect |
|-------------|------|--------|
| 0 | `SFPSETCC_MOD1_LREG_LT0` | `LaneFlags = (VC < 0)` (sign bit check) |
| 1 | `SFPSETCC_MOD1_IMM_BIT0` | `LaneFlags = bool(Imm1)` — set or clear all lanes from immediate |
| 2 | `SFPSETCC_MOD1_LREG_NE0` | `LaneFlags = (VC != 0)` |
| 4 | `SFPSETCC_MOD1_LREG_GTE0` | `LaneFlags = (VC >= 0)` |
| 6 | `SFPSETCC_MOD1_LREG_EQ0` | `LaneFlags = (VC == 0)` |
| 8 | `SFPSETCC_MOD1_CLEAR` | `LaneFlags = false` unconditionally |

**Note on FP32 values:** FP32 sign bit is at bit 31, same position as integer sign, so `LREG_LT0` tests the FP32 sign bit directly. However, negative zero (`0x80000000`) and NaN have sign bit set even though they are not "less than zero" in the IEEE sense. Software should flush negative zero before using `SFPSETCC` on FP32 data.

### 3.11 SFPMOV — Vector Register Move

```c
TT_SFPMOV(0, /* u4 */ VC, /* u4 */ VD, /* u4 */ Mod1)
```

**Latency:** 1 cycle. **IPC:** 1.

Moves data from `VC` to `VD`, with optional negation, all-lanes-enabled override, or special source selection.

```python
def sfpmov(VC, VD, Mod1, LReg):
    for lane in range(32):
        if not (lane_enabled(lane) or (Mod1 == SFPMOV_MOD1_ALL_LANES_ENABLED)):
            continue
        if Mod1 & SFPMOV_MOD1_FROM_SPECIAL:
            # VC selects which configuration register to read
            if   VC in (0,1,2,3): x = LoadMacroConfig[lane].InstructionTemplate[VC]
            elif VC in (4,5,6,7): x = LoadMacroConfig[lane].Sequence[VC-4]
            elif VC == 8:         x = LoadMacroConfig[lane].Misc
            elif VC == 9:         x = advance_prng(lane)
            elif VC == 15:        x = LaneConfig[lane]
            else:                 x = 0
        else:
            x = LReg[VC][lane]
            if Mod1 & SFPMOV_MOD1_NEGATE:
                x ^= 0x80000000  # flip sign bit (FP32 or sign-magnitude)
        if VD < 8 or VD == 16:
            LReg[VD][lane] = x
```

| `Mod1` value | Name | Effect |
|-------------|------|--------|
| 0 | — | Plain move: `VD = VC` (respects `LaneEnabled`) |
| 1 | `SFPMOV_MOD1_NEGATE` | `VD = -VC` (flip sign bit — FP32 or sign-magnitude) |
| 2 | `SFPMOV_MOD1_ALL_LANES_ENABLED` | Move ignores predication — all 32 lanes always write |
| 8 | `SFPMOV_MOD1_FROM_SPECIAL` | Read from configuration registers or PRNG (source determined by `VC`) |

When `SFPMOV_MOD1_FROM_SPECIAL` with `VC = 9`: advances the per-lane PRNG and returns the previous state (useful for seeding or reading random bits directly).

### 3.12 SFPLUTFP32 — Piecewise Linear LUT Evaluation

```c
TT_SFPLUTFP32(/* u4 */ VD, /* u4 */ Mod1)
```

**Latency:** 2 cycles. **IPC:** 1.

Evaluates a piecewise linear function of `Abs(LReg[3])`. The input is always taken from `LReg[3]`. The piece is selected by comparing the magnitude against fixed breakpoints. All computations use the FP32 MAD unit.

**Piece index selection:**

```python
def select_piece(b):
    # b = abs(LReg[3][lane])
    if b < 1.0:  return 0  # LReg[0] / LReg[4]
    if b < 2.0:  return 1  # LReg[1] / LReg[5]
    return 2               # LReg[2] / LReg[6]
```

The four table modes:

| `Mod1` value | Name | Breakpoints | Coefficient source |
|-------------|------|-------------|-------------------|
| 0 | `SFPLUTFP32_MOD1_FP32_3ENTRY_TABLE` | 1.0, 2.0 | `a = LReg[i]`, `c = LReg[4+i]` (full FP32) |
| 2 | `SFPLUTFP32_MOD1_FP16_6ENTRY_TABLE1` | 0.5, 1.0, 1.5, 2.0, 3.0 | `a`, `c` packed as FP16 pairs in `LReg[i]`, `LReg[4+i]`; final breakpoint at 3.0 |
| 3 | `SFPLUTFP32_MOD1_FP16_6ENTRY_TABLE2` | 0.5, 1.0, 1.5, 2.0, 4.0 | Same as TABLE1 but final breakpoint at 4.0 |
| 10 | `SFPLUTFP32_MOD1_FP16_3ENTRY_TABLE` | 1.0, 2.0 | Coefficients packed as FP16 pairs in `LReg[i]` only (slope in high 16b, intercept in low 16b). **Hardware bug:** writes to `LReg[LReg[7] & 15]`, not `LReg[VD]` |

Additional modifier bits:

| `Mod1` bit | Name | Effect |
|-----------|------|--------|
| 2 | `SFPLUTFP32_MOD1_SGN_RETAIN` | Copy sign of `LReg[3]` onto result (makes function odd) |
| 3 | `SFPLUTFP32_MOD1_INDIRECT_VD` | Use `LReg[7] & 0xF` as destination index |

**`Lut16ToFp32` conversion:** The 16-bit FP16-like values are decoded as `(1 + Man/2^10) * 2^(Exp-15)`. Crucially, exponent 31 (which would be Inf/NaN in IEEE FP16) maps to +0 or -0 instead, and exponent 0 (which would be denormal in IEEE FP16) is treated as a normalized number.

**Computation:** `d = a * Abs(LReg[3]) + c`, with MAD semantics as per `SFPMAD`.

### 3.13 SFPSTOCHRND — Stochastic Rounding

This instruction has three distinct flavors selected by `Mod1`:

```c
TT_SFP_STOCH_RND(/* u2 */ RoundingMode, 0, /* u4 */ VC, /* u4 */ VC, /* u4 */ VD, /* u3 */ Mod1)
```

**Note:** `VC` appears twice to work around a false-dependency bug in the auto-stalling logic. In the encoding, set `VB = VC`.

**Latency:** 1 cycle. **IPC:** 1. **Sub-unit:** Round.

#### Rounding Mode Field

| `RoundingMode` | Name | PRNG usage |
|---------------|------|------------|
| 0 | `SFPSTOCHRND_RND_NEAREST` | `PRNGBits` set to `0x400000` (round to nearest, ties away from zero) |
| 1 | `SFPSTOCHRND_RND_STOCH` | `PRNGBits` from PRNG (stochastic rounding) |
| 2 | `SFPSTOCHRND_RND_ZERO` | `PRNGBits` set to `0x7FFFFF` (round toward zero) |

**Known hardware bugs in stochastic mode:** Slight bias toward increasing magnitude (comparison uses `>=` instead of `>`), and can increase magnitude of values that don't require rounding.

#### Flavor A: FP32 → Reduced-precision FP32

| `Mod1` | Name | Mantissa bits kept | Discarded bits |
|--------|------|--------------------|----------------|
| 0 | `SFPSTOCHRND_MOD1_FP32_TO_FP16A` | 10 bits | Low 13 bits used for rounding |
| 1 | `SFPSTOCHRND_MOD1_FP32_TO_FP16B` | 7 bits | Low 16 bits used for rounding |

Result is FP32 with reduced mantissa precision, suitable for lossless `SFPSTORE MOD0_FMT_FP16A` or `MOD0_FMT_BF16`.

Special cases: denormals → `+0`; negative zero → `+0`; `-NaN` → `-Inf`; `+NaN` → `+Inf`.

#### Flavor B: FP32 → Bounded Sign-Magnitude Integer

| `Mod1` | Name | Output range | Sign preserved |
|--------|------|--------------|----------------|
| 2 | `SFPSTOCHRND_MOD1_FP32_TO_UINT8` | 0–255 | No (absolute value) |
| 3 | `SFPSTOCHRND_MOD1_FP32_TO_INT8` | ±127 | Yes |
| 6 | `SFPSTOCHRND_MOD1_FP32_TO_UINT16` | 0–65535 | No (absolute value) |
| 7 | `SFPSTOCHRND_MOD1_FP32_TO_INT16` | ±32767 | Yes |

Input `|x| < 0.5` always rounds to zero (even in stochastic mode — bug). Input `|x| ≥ 2^16` or NaN clamps to `MaxMagnitude`.

#### Flavor C: Sign-Magnitude Integer → Reduced-range Sign-Magnitude Integer

| `Mod1` | Name | Output range | Sign preserved |
|--------|------|--------------|----------------|
| 4 | `SFPSTOCHRND_MOD1_INT32_TO_UINT8` | 0–255 | No |
| 5 | `SFPSTOCHRND_MOD1_INT32_TO_INT8` | ±127 | Yes |

The magnitude is shifted right by `Imm5` (or by `VB & 31` if `UseImm5` is false). Discarded bits are used for rounding against PRNG. This is the integer equivalent of Flavor A.

### 3.14 SFPCAST — Type Conversion

```c
TT_SFPCAST(/* u4 */ VC, /* u4 */ VD, /* u4 */ Mod1)
```

**Latency:** 1 cycle. **IPC:** 1.

| `Mod1 & 3` | Name | Operation |
|-----------|------|-----------|
| 0 | `SFPCAST_MOD1_SM32_TO_FP32_RNE` | Sign-magnitude int32 → FP32, round-to-nearest-ties-to-even |
| 1 | `SFPCAST_MOD1_SM32_TO_FP32_RNS` | Sign-magnitude int32 → FP32, stochastic rounding (7 PRNG bits) |
| 2 | `SFPCAST_MOD1_INT32_ABS` | Two's complement int32 → two's complement absolute value (hardware bug makes it do ABS instead of its intended operation) |
| 3 | `SFPCAST_MOD1_INT32_SM32` | Bidirectional: sign-magnitude ↔ two's complement (same implementation works both ways; `-0` maps to `-2^31` and vice versa) |

**Modes 0 and 1 — SM32 to FP32:** Exact for `|x| ≤ 2^24`. Larger values are rounded. The conversion uses `lzcnt` of the magnitude to find the leading 1 bit and builds an FP32 result.

**Mode 3 — format conversion:** The hardware computes `Sign | (Sign ? -c : c)` which converts two's complement to sign-magnitude and sign-magnitude to two's complement identically.

### 3.15 SFPABS — Absolute Value

```c
TT_SFPABS(0, /* u4 */ VC, /* u4 */ VD, /* u4 */ Mod1)
```

**Latency:** 1 cycle. **IPC:** 1.

| `Mod1` | Name | Operation |
|--------|------|-----------|
| 0 | `SFPABS_MOD1_INT` | Two's complement absolute value: `VD = (VC < 0) ? -VC : VC`. If `VC = -2^31`, leaves unchanged. |
| 1 | `SFPABS_MOD1_FLOAT` | FP32 absolute value: clears sign bit. Exception: `-NaN` is left as `-NaN` (sign bit preserved for NaN). |

For sign-magnitude integer absolute value (which also works for FP32 without NaN exception handling), use `SFPSETSGN` with `SFPSETSGN_MOD1_ARG_IMM` and `Imm1 = 0`.

### 3.16 SFPAND, SFPOR, SFPXOR, SFPNOT — Bitwise Logic

All operate lanewise on 32-bit values, respecting `LaneEnabled`. Latency: 1 cycle.

**SFPAND:**
```c
TT_SFPAND(/* u4 */ VB, /* u4 */ VC, /* u4 */ VD, /* u4 */ Mod1)
```
- `Mod1 = 0`: `VD = VD & VC`
- `Mod1 = 1` (`SFPAND_MOD1_USE_VB`): `VD = VB & VC`

Hardware bug: auto-stalling logic ignores `SFPAND_MOD1_USE_VB` and thinks `VD` is always the second operand.

**SFPOR:**
```c
TT_SFPOR(/* u4 */ VB, /* u4 */ VC, /* u4 */ VD, /* u4 */ Mod1)
```
- `Mod1 = 0`: `VD = VD | VC`
- `Mod1 = 1` (`SFPOR_MOD1_USE_VB`): `VD = VB | VC`

Hardware bug: same as `SFPAND`.

**SFPXOR:**
```c
TT_SFPXOR(0, /* u4 */ VC, /* u4 */ VD, 0)
```
- Always: `VD = VD ^ VC` (destination is also second source)

**SFPNOT:**
```c
TT_SFPNOT(0, /* u4 */ VC, /* u4 */ VD, 0)
```
- Always: `VD = ~VC` (bitwise NOT)

### 3.17 SFPLZ — Count Leading Zeros

```c
TT_SFPLZ(0, /* u4 */ VC, /* u4 */ VD, /* u4 */ Mod1)
```

**Latency:** 1 cycle. **IPC:** 1.

Counts leading zero bits in `VC`. Optionally masks the sign bit first (for sign-magnitude integers). Also optionally sets `LaneFlags` based on whether `VC` was zero.

```python
def sfplz(VC, VD, Mod1, LReg):
    for lane in range(32):
        if not lane_enabled(lane): continue
        c = LReg[VC][lane]
        if Mod1 & SFPLZ_MOD1_NOSGN_MASK:
            c &= 0x7FFFFFFF  # mask sign bit
        LReg[VD][lane] = count_leading_zeros_32(c)  # 32 if c == 0
        if VD < 8:
            if Mod1 & SFPLZ_MOD1_CC_NE0:
                LaneFlags[lane] = (c != 0)
            if Mod1 & SFPLZ_MOD1_CC_COMP:
                LaneFlags[lane] = not LaneFlags[lane]
```

| `Mod1` bit | Name | Effect |
|-----------|------|--------|
| 1 | `SFPLZ_MOD1_CC_NE0` | Set `LaneFlags = (VC != 0)` (after optional sign mask) |
| 2 | `SFPLZ_MOD1_NOSGN_MASK` | Mask off the sign (bit 31) before counting |
| 3 | `SFPLZ_MOD1_CC_COMP` | Complement the flag (making it `CC_EQ0` or `CC_NE0` inverted) |

### 3.18 SFPSETEXP — Set FP32 Exponent

```c
TT_SFPSETEXP(/* u8 */ Imm8, /* u4 */ VC, /* u4 */ VD, /* u4 */ Mod1)
```

**Latency:** 1 cycle. **IPC:** 1.

Combines sign and mantissa from `VC` with an exponent from one of three sources:

| `Mod1` | Source of new exponent | Notes |
|--------|----------------------|-------|
| 0 | Low 8 bits of `VD` | `VD` acts as both source of exponent and destination |
| 1 (`SFPSETEXP_MOD1_ARG_IMM`) | `Imm8` field | Immediate replaces exponent |
| 2 (`SFPSETEXP_MOD1_ARG_EXPONENT`) | Exponent field of `VD` | Copies exponent from one FP32 to another |

Result: `{VC.Sign, new_exp, VC.Man}` — sign and mantissa from `VC`, exponent from selected source.

### 3.19 SFPSETSGN — Set FP32 Sign Bit

```c
TT_SFPSETSGN(/* u1 */ Imm1, /* u4 */ VC, /* u4 */ VD, /* u4 */ Mod1)
```

**Latency:** 1 cycle. **IPC:** 1.

Combines exponent and mantissa from `VC` with a sign bit from one of two sources:

| `Mod1` | Source of new sign bit |
|--------|----------------------|
| 0 | Sign bit of `VD` (current destination) |
| 1 (`SFPSETSGN_MOD1_ARG_IMM`) | `Imm1` field (0 = positive, 1 = negative) |

Result: `{new_sign, VC.Exp, VC.Man}`.

Use cases:
- `Imm1 = 0, Mod1 = 1`: `VD = Abs(VC)` (clear sign bit — for FP32 or sign-magnitude)
- `Imm1 = 1, Mod1 = 1`: `VD = -Abs(VC)` (force negative)

### 3.20 SFPGT — Greater-Than Comparison

```c
TT_SFPGT(0, /* u4 */ VC, /* u4 */ VD, /* u4 */ Mod1)
```

**Latency:** 1 cycle. **IPC:** 1. **New in Blackhole.**

Tests `VD > VC` (where `VB = VD` internally). The comparison uses sign-magnitude ordering, which is equivalent to IEEE 754 total order for FP32 (treating -NaN < -Inf < ... < -0 < +0 < ... < +Inf < +NaN).

The result can be written to three destinations simultaneously:

| `Mod1` bit | Name | Effect |
|-----------|------|--------|
| 0 | `SFPGT_MOD1_SET_CC` | Set `LaneFlags = IsVdGreaterThanVc` |
| 1 | `SFPGT_MOD1_MUTATE_STACK` | AND or OR result into top of `FlagStack` (no `LaneEnabled` check) |
| 2 | `SFPGT_MOD1_MUTATE_OR` | When mutating stack, use OR instead of AND |
| 3 | `SFPGT_MOD1_SET_VD` | Write `-1` (int) if true, `0` if false to `VD` (respects `LaneEnabled`) |

`SFPLE` is the exact inverse: tests `VD <= VC`.

### 3.21 SFPARECIP — Approximate Reciprocal or Exponential

```c
TT_SFPARECIP(/* u4 */ VB, /* u4 */ VC, /* u4 */ VD, /* u4 */ Mod1)
```

**Latency:** 1 cycle. **IPC:** 1. **New in Blackhole.**

| `Mod1` | Name | Operation |
|--------|------|-----------|
| 0 | `SFPARECIP_MOD1_RECIP` | `VD = ±ApproxRecip(Abs(VC))` (sign from VC restored) |
| 1 | `SFPARECIP_MOD1_COND_RECIP` | `VD = ApproxRecip(Abs(VC))` if `VB < 0` (signed), else `VD = VC` (sign NOT restored) |
| 2 | `SFPARECIP_MOD1_EXP` | `VD = ±ApproxExp(Abs(VC))` (sign from VC restored) |

**Accuracy:**
- `ApproxRecip(x)`: for `2^-126 ≤ x < 2^126`, error bound is `0.9944 / x < result < 1.0054 / x`. At `x = 1.0`, gives `0.99609375`.
- `ApproxExp(x)`: for `0 ≤ x < 2`, error bound is `0.9922 * e^x < result < 1.016 * e^x`. For `x ≥ 2`, result is not useful.

Both functions use a hardware lookup table (128 entries for reciprocal, 896 entries for exponential). The sign removal-and-restore means `SFPARECIP_MOD1_RECIP` computes `sign(VC) / |VC|` and `SFPARECIP_MOD1_EXP` computes `sign(VC) * e^|VC|`, which is not the usual mathematical definition.

### 3.22 SFPSWAP — Swap, Min+Max

```c
TT_SFPSWAP(0, /* u4 */ VC, /* u4 */ VD, /* u4 */ Mod1)
```

**Latency:** 2 cycles. **IPC:** ≤1.

Conditionally or unconditionally swaps the contents of `VC` and `VD`.

| `Mod1` | Name | Description |
|--------|------|-------------|
| 0 | `SFPSWAP_MOD1_SWAP` | Unconditional swap of all lanes of `VC` and `VD` |
| 1 | `SFPSWAP_MOD1_VEC_MIN_MAX` | All lanes: `VD = min(VC, VD)`, `VC = max(VC, VD)` |
| 2 | `SFPSWAP_MOD1_SUBVEC_MIN01_MAX23` | Lanes 0–15: VD gets min; lanes 16–31: VD gets max |
| 3 | `SFPSWAP_MOD1_SUBVEC_MIN02_MAX13` | |
| 4 | `SFPSWAP_MOD1_SUBVEC_MIN03_MAX12` | |
| 5 | `SFPSWAP_MOD1_SUBVEC_MIN0_MAX123` | Lanes 0–7: VD gets min; lanes 8–31: VD gets max |
| 6 | `SFPSWAP_MOD1_SUBVEC_MIN1_MAX023` | Lanes 8–15: VD gets min |
| 7 | `SFPSWAP_MOD1_SUBVEC_MIN2_MAX013` | Lanes 16–23: VD gets min |
| 8 | `SFPSWAP_MOD1_SUBVEC_MIN3_MAX012` | Lanes 24–31: VD gets min |
| 9 | _(no name)_ | All lanes: VD gets max (inverse of mode 1) |

Comparison uses sign-magnitude ordering (identical to `SFPGT`). When `LaneConfig.ENABLE_DEST_INDEX` is true, performs argmin+argmax across `LReg[0..3]` and `LReg[4..7]` simultaneously.

**Scheduling:** Hardware auto-stalls the next instruction by 1 cycle after `SFPSWAP`. If software inserts an explicit `SFPNOP`, the `SFPSWAP + SFPNOP` pair takes 2 cycles total rather than 3. Hardware bug: auto-stalling does not detect 1st-cycle reads of `VC` and `VD`.

### 3.23 SFPSHFT — Bitwise Shift

```c
TT_SFPSHFT(/* i12 */ (Imm12 & 0xFFF), /* u4 */ VC, /* u4 */ VD, /* u4 */ Mod1)
```

**Latency:** 1 cycle. **IPC:** 1.

Shifts `VD` (or `VC` if `SFPSHFT_MOD1_ARG_IMM_USE_VC` is set) by a signed shift amount.

```python
def sfpshft(Imm12, VC, VD, Mod1, LReg):
    VB = VD  # second source
    for lane in range(32):
        if not lane_enabled(lane): continue
        x = LReg[VB][lane]
        shift = as_signed_32(LReg[VC][lane])
        if Mod1 & SFPSHFT_MOD1_ARG_IMM:
            if Mod1 & SFPSHFT_MOD1_ARG_IMM_USE_VC:
                x = LReg[VC][lane]
            shift = sign_extend_12(Imm12)
        if shift >= 0:
            LReg[VD][lane] = x << (shift & 31)
        elif Mod1 & SFPSHFT_MOD1_ARITHMETIC:
            LReg[VD][lane] = as_signed_32(x) >> ((-shift) & 31)
        else:
            LReg[VD][lane] = x >> ((-shift) & 31)
```

| `Mod1` bit | Name | Effect |
|-----------|------|--------|
| 0 | `SFPSHFT_MOD1_ARG_IMM` | Use sign-extended `Imm12` as shift amount instead of `VC` |
| 1 | `SFPSHFT_MOD1_ARITHMETIC` | Negative shift amounts do arithmetic (sign-extending) right shift |
| 2 | `SFPSHFT_MOD1_ARG_IMM_USE_VC` | When also using immediate: shift `VC` into `VD` instead of `VD` into `VD` |

Hardware bug: auto-stalling does not detect that `SFPSHFT` reads `VD`.

### 3.24 SFPSHFT2 — Vector Shuffle or Bitwise Shift

```c
TT_SFPSHFT2(/* u4 */ VB, /* u4 */ VC, /* u4 */ VD, /* u4 */ Mod1)
```

**Latency:** 1 or 2 cycles (see table). **Sub-unit:** Round.

Performs cross-lane shuffles of `LReg[0..3]` or bitwise shifts.

| `Mod1` | Name | Latency | Description |
|--------|------|---------|-------------|
| 0 | `SFPSHFT2_MOD1_COPY4` | 1 cycle | Within each lane: `L0←L1, L1←L2, L2←L3, L3←0` |
| 1 | `SFPSHFT2_MOD1_SUBVEC_CHAINED_COPY4` | 1 cycle | Same as COPY4 but `L3 ← shift-left-by-8-lanes(old L0)` |
| 2 | `SFPSHFT2_MOD1_SUBVEC_SHFLROR1_AND_COPY4` | 2 cycles | COPY4 + within each 8-lane group, rotate `VC` right by 1 lane → `L3` |
| 3 | `SFPSHFT2_MOD1_SUBVEC_SHFLROR1` | 2 cycles | Within each 8-lane group, rotate `VC` right by 1 lane → `VD` |
| 4 | `SFPSHFT2_MOD1_SUBVEC_SHFLSHR1` | 2 cycles | Within each 8-lane group, shift `VC` right by 1 lane → `VD` (first lane of each group becomes 0) |
| 5 | `SFPSHFT2_MOD1_SHFT_LREG` | 1 cycle | `VD = VB << (VC & 31)` if `VC ≥ 0`, else `VD = VB >> ((-VC) & 31)` |
| 6 | `SFPSHFT2_MOD1_SHFT_IMM` | 1 cycle | `VD = LReg[Imm12 & 0xF] << (Imm12 & 31)` or right shift if `Imm12 < 0` |

**Scheduling:** Modes 2, 3, 4 require the next instruction to be `SFPNOP` (auto-stall applies, but explicit NOP makes the pair cost 2 cycles instead of 3).

Hardware bugs: auto-stalling does not detect reads for modes 2–4, and thinks modes 5–6 read from `VD` instead of `VB`.

### 3.25 SFPMUL24 — 23-bit Integer Multiply

```c
TT_SFPMUL24(/* u4 */ VA, /* u4 */ VB, /* u4 */ VC, /* u4 */ VD, /* u4 */ Mod1)
```

**Latency:** 2 cycles. **IPC:** 1. **New in Blackhole.**

Multiplies two 23-bit integers (the low 23 bits of `VA` and `VB`), returning either the low or high 23 bits of the 46-bit product.

| `Mod1` bit | Name | Effect |
|-----------|------|--------|
| 0 | `SFPMUL24_MOD1_UPPER` | Return high 23 bits (`(VA & 0x7FFFFF) * (VB & 0x7FFFFF)) >> 23`) |
| 0 (clear) | `SFPMUL24_MOD1_LOWER` | Return low 23 bits (`(VA * VB) & 0x7FFFFF`) |
| 2 | `SFPMUL24_MOD1_INDIRECT_VA` | Use `LReg[7] & 0xF` as `VA` index |
| 3 | `SFPMUL24_MOD1_INDIRECT_VD` | Use `LReg[7] & 0xF` as `VD` index |

**Important:** Always set `VC = 9` (`LCONST_0`). If `VC` is non-zero, a non-contractual shift/add adjustment is applied to the result via reuse of the FP32 datapath.

Latency and auto-stalling rules are the same as `SFPMAD`.

### 3.26 SFPSETMAN — Set FP32 Mantissa

```c
TT_SFPSETMAN(/* u12 */ Imm12, /* u4 */ VC, /* u4 */ VD, /* u4 */ Mod1)
```

**Latency:** 1 cycle. **IPC:** 1.

| `Mod1` | Source of mantissa | Notes |
|--------|-------------------|-------|
| 0 | Low bits of `VD` | `{VC.Sign, VC.Exp, VD.Man}` |
| 1 (`SFPSETMAN_MOD1_ARG_IMM`) | `Imm12 << 11` | `{VC.Sign, VC.Exp, Imm12 << 11}` |

### 3.27 SFPLOADI — Load Immediate

```c
TT_SFPLOADI(/* u4 */ VD, /* u4 */ Mod0, /* u16 */ Imm16)
```

**Latency:** 1 cycle. **IPC:** 1. **Sub-unit:** Load.

Writes a 16-bit or 32-bit constant to all lanes of `VD` (must be 0–7). Does not affect the programmable constant registers (LReg[11..14]); use `SFPCONFIG` for those.

| `Mod0` | Name | Operation |
|--------|------|-----------|
| 0 | `SFPLOADI_MOD0_FLOATB` | `VD = BF16ToFP32(Imm16)` — BF16 immediate expanded to FP32 |
| 1 | `SFPLOADI_MOD0_FLOATA` | `VD = FP16ToFP32(Imm16)` — FP16 immediate, no denormal/NaN handling |
| 2 | `SFPLOADI_MOD0_USHORT` | `VD = ZeroExtend(Imm16)` — zero-extended to 32 bits |
| 4 | `SFPLOADI_MOD0_SHORT` | `VD = SignExtend(Imm16)` — sign-extended to 32 bits |
| 8 | `SFPLOADI_MOD0_UPPER` | `VD.High16 = Imm16`, low 16 bits preserved |
| 10 | `SFPLOADI_MOD0_LOWER` | `VD.Low16 = Imm16`, high 16 bits preserved |

To write an arbitrary 32-bit value, use `SFPLOADI_MOD0_UPPER` followed by `SFPLOADI_MOD0_LOWER`.

### 3.28 SFPCONFIG — Write Configuration / Programmable Constants

```c
TT_SFPCONFIG(/* u16 */ Imm16, /* u4 */ VD, /* u4 */ Mod1)
```

**Latency:** ≤2 cycles. **IPC:** 1.

Writes to `LReg[11..14]` (programmable constants), `LaneConfig`, or `LoadMacroConfig`. Input always comes from the first 8 lanes of `LReg[0]` (broadcast to all 32 lanes), or from `Imm16` when `MOD1_IMM16_IS_VALUE` is set.

**`VD` destination selector:**

| `VD` range | Destination |
|-----------|-------------|
| 0–3 | `LoadMacroConfig.InstructionTemplate[VD]` — always from `LReg[0]`, ignores `MOD1_IMM16_IS_VALUE` |
| 4–7 | `LoadMacroConfig.Sequence[VD-4]` |
| 8 | `LoadMacroConfig.Misc` (12-bit value) |
| 11 | `LReg[11]` — when `MOD1_IMM16_IS_VALUE`, writes `-1.0f` (`0xBF800000`) |
| 12 | `LReg[12]` — when `MOD1_IMM16_IS_VALUE`, writes `1.0f/512.0f` (`0x3B000000`) |
| 13 | `LReg[13]` — when `MOD1_IMM16_IS_VALUE`, writes `-0.67487759f` (`0xBF2CC4C7`) |
| 14 | `LReg[14]` — when `MOD1_IMM16_IS_VALUE`, writes `-0.34484843f` (`0xBEB08FF9`) |
| 15 | `LaneConfig` — per-lane control register (18 bits) |

| `Mod1` bit | Name | Effect |
|-----------|------|--------|
| 0 | `MOD1_IMM16_IS_VALUE` | Use `Imm16` as value (otherwise use `LReg[0][Lane & 7]`) |
| 1 | `MOD1_BITWISE_OR` | OR value into destination instead of replacing |
| 2 | `MOD1_BITWISE_AND` | AND value into destination |
| 3 | `MOD1_BITWISE_XOR` | XOR value into destination |
| 3 | `MOD1_IMM16_IS_LANE_MASK` | Use `Imm16` as a lane enable bitmask (even bits of low 16 bits) |

**Scheduling:** If `SFPCONFIG` changes `LaneConfig.DISABLE_BACKDOOR_LOAD`, insert an `SFPNOP` immediately after to ensure the new value is seen by the next SFPU instruction.

### 3.29 SFPNOP — No Operation

```c
TTI_SFPNOP
```

**Latency:** 1 cycle. **IPC:** 1. **Sub-unit:** Load (or whichever sub-unit `SFPLOADMACRO` schedules it on).

Occupies the Vector Unit for one cycle with no observable effect. Used to fill dependency gaps.

---

## 4. SIMT Predication

The SFPU implements per-lane conditional execution through a two-level system: per-lane `LaneFlags` booleans and a stack-based scope mechanism.

### 4.1 Predication State

```c
// Per-lane state (32 independent instances):
bool LaneFlags[32];                    // current condition flag
bool UseLaneFlagsForLaneEnable[32];    // is predication active?

struct FlagStackEntry {
    bool LaneFlags;
    bool UseLaneFlagsForLaneEnable;
};
Stack<FlagStackEntry> FlagStack[32];   // depth limit: 8 entries
```

`LaneFlags` and `UseLaneFlagsForLaneEnable` both initialize to `false`.

### 4.2 Lane Enable Logic

```python
def is_lane_enabled(lane):
    # ROW_MASK in LaneConfig always takes priority
    if LaneConfig[lane & 7].ROW_MASK.bit[lane // 8]:
        return False
    # Then per-lane flag predication
    if UseLaneFlagsForLaneEnable[lane]:
        return LaneFlags[lane]
    # Otherwise all lanes enabled
    return True
```

When `UseLaneFlagsForLaneEnable` is `false` (the initial state), all lanes execute every instruction (subject only to `ROW_MASK`). Once set to `true` by `SFPENCC`, `LaneFlags` gates every instruction write.

### 4.3 Effect of Predication

When a lane is disabled (`LaneEnabled = false`):
- The lane's `LReg` entries are **not written** — they preserve their previous values.
- The lane's `LaneFlags` state **is still updated** by comparison instructions (`SFPSETCC`, `SFPGT`, `SFPLE`, `SFPLZ`, `SFPIADD`, `SFPEXEXP`) because these must set the flag for disabled lanes too (otherwise the lane could never re-enable itself).

### 4.4 SFPENCC — Enable Conditional Execution

```c
TT_SFPENCC(/* u2 */ Imm2, 0, /* u4 */ VD, /* u4 */ Mod1)
```

Controls `UseLaneFlagsForLaneEnable` and optionally sets `LaneFlags`.

```python
def sfpencc(Imm2, VD, Mod1):
    for lane in range(32):
        if not lane_enabled(lane): continue
        if Mod1 & SFPENCC_MOD1_EI:
            UseLaneFlagsForLaneEnable[lane] = bool(Imm2 & SFPENCC_IMM2_E)
        elif Mod1 & SFPENCC_MOD1_EC:
            UseLaneFlagsForLaneEnable[lane] = not UseLaneFlagsForLaneEnable[lane]
        # else: leave UseLaneFlagsForLaneEnable unchanged

        if Mod1 & SFPENCC_MOD1_RI:
            LaneFlags[lane] = bool(Imm2 & SFPENCC_IMM2_R)
        else:
            LaneFlags[lane] = True
```

| `Mod1` | Constant | Effect on `UseLaneFlagsForLaneEnable` | Effect on `LaneFlags` |
|--------|----------|--------------------------------------|-----------------------|
| 0 | `SFPENCC_MOD1_EU_R1` | Unchanged | Set to `true` |
| 1 | `SFPENCC_MOD1_EC_R1` | Toggled | Set to `true` |
| 2 | `SFPENCC_MOD1_EI_R1` | Set from `Imm2 & 1` | Set to `true` |
| 8 | `SFPENCC_MOD1_EU_RI` | Unchanged | Set from `Imm2 & 2` |
| 9 | `SFPENCC_MOD1_EC_RI` | Toggled | Set from `Imm2 & 2` |
| 10 | `SFPENCC_MOD1_EI_RI` | Set from `Imm2 & 1` | Set from `Imm2 & 2` |

**Common pattern to enable predication:**
```c
TT_SFPENCC(3, 0, VD, SFPENCC_MOD1_EI_RI);  // Imm2=3: enable=1, flags=1 → all lanes active
```

### 4.5 SFPPUSHC — Push Condition Stack

```c
TT_SFPPUSHC(0, 0, /* u4 */ VD, /* u4 */ Mod1)
```

**Stack depth limit: 8.**

- `Mod1 = 0`: **Push** — copies current `{LaneFlags, UseLaneFlagsForLaneEnable}` onto the stack. Stack must not be full.
- `Mod1 = 1..12`: **Mutate top** — does not push; instead replaces the top's `UseLaneFlagsForLaneEnable` with current and applies a boolean operation to the top's `LaneFlags` (see `BooleanOp` table below).
- `Mod1 = 13`: Inverts current `LaneFlags`, then replaces stack top with inverted state.
- `Mod1 = 14`: Replaces stack top with `{true, true}`.
- `Mod1 = 15`: Replaces stack top with `{true, false}`.

### 4.6 SFPPOPC — Pop Condition Stack

```c
TT_SFPPOPC(0, 0, /* u4 */ VD, /* u4 */ Mod1)
```

- `Mod1 = 0`: **Pop** — restores `LaneFlags` and `UseLaneFlagsForLaneEnable` from the top of stack. Stack must not be empty.
- `Mod1 = 1..12`: **Peek and mutate** — does not pop; reads top of stack and applies a boolean operation to current `LaneFlags`.
- `Mod1 = 13`: Inverts current `LaneFlags` (no stack access).
- `Mod1 = 14`: Sets `{UseLaneFlagsForLaneEnable = true, LaneFlags = true}`.
- `Mod1 = 15`: Sets `{UseLaneFlagsForLaneEnable = true, LaneFlags = false}`.

### 4.7 SFPCOMPC — Complement (Implement `else`)

```c
TT_SFPCOMPC(0, 0, /* u4 */ VD, 0)
```

Implements the `else` branch of a SIMT if/else. Uses the top of the flag stack to determine which lanes were active in the `if` branch, then sets `LaneFlags` to select only those lanes that were **not** active during `if`.

```python
def sfpcompc(VD):
    for lane in range(32):
        if not lane_enabled_or_backdoor(lane, VD): continue
        Top = FlagStack[lane].top() if not FlagStack[lane].empty() else {True, True}
        if Top.UseLaneFlagsForLaneEnable and UseLaneFlagsForLaneEnable[lane]:
            LaneFlags[lane] = Top.LaneFlags and not LaneFlags[lane]
        else:
            LaneFlags[lane] = False
```

### 4.8 BooleanOp Table (used by SFPPUSHC / SFPPOPC with Mod1 1..12)

Let `A = existing top-of-stack LaneFlags`, `B = current LaneFlags`:

| `Mod1` | Result |
|--------|--------|
| 1 | `B` |
| 2 | `NOT B` |
| 3 | `A AND B` |
| 4 | `A OR B` |
| 5 | `A AND NOT B` |
| 6 | `A OR NOT B` |
| 7 | `NOT A AND B` |
| 8 | `NOT A OR B` |
| 9 | `NOT A AND NOT B` |
| 10 | `NOT A OR NOT B` |
| 11 | `A XOR B` |
| 12 | `A XNOR B` |

### 4.9 SIMT if/else/endif Pattern

```c
// Idiomatic SIMT branching (compiler convention):
SFPENCC  3, VD, EI_RI       // enable predication, all lanes start active
SFPPUSHC 0, VD, 0           // push initial state onto stack
// --- condition setup: sets LaneFlags to select "if" lanes ---
SFPSETCC ...                 // or SFPGT, SFPIADD, etc.
// --- if body: only lanes with LaneFlags=true execute ---
<instructions>
SFPCOMPC 0, VD, 0           // flip to "else" lanes
// --- else body ---
<instructions>
SFPPOPC  0, VD, 0           // restore flags from before the if
```

---

## 5. Pipeline and Latency

### 5.1 Instruction Latency Summary

| Latency | Instructions |
|---------|-------------|
| **1 cycle** | `SFPMOV`, `SFPSETSGN`, `SFPABS`, `SFPARECIP`, `SFPGT`, `SFPLE`, `SFPLZ`, `SFPSETCC`, `SFPDIVP2`, `SFPSETEXP`, `SFPSETMAN`, `SFPEXMAN`, `SFPEXEXP`, `SFPIADD`, `SFPCAST`, `SFPAND`, `SFPOR`, `SFPXOR`, `SFPNOT`, `SFPSHFT`, `SFPENCC`, `SFPPUSHC`, `SFPPOPC`, `SFPCOMPC`, `SFPCONFIG`, `SFPTRANSP`, `SFPNOP`, `SFPLOAD`, `SFPSTORE`, `SFPLOADI` |
| **2 cycles** | `SFPMAD`, `SFPADD`, `SFPMUL`, `SFPADDI`, `SFPMULI`, `SFPLUTFP32`, `SFPMUL24`, `SFPSWAP`, `SFPSHFT2` (modes ROR1, SHR1, ROR1_AND_COPY4) |
| **2 cycles + auto-stall** | `SFPSTOCHRND` (round sub-unit; 1-cycle execution but causes stall if followed immediately by dependent instruction) |

### 5.2 Dependency Handling

The SFPU implements **automatic stalling** for most 2-cycle instructions: if the instruction immediately following reads a register written by the 2-cycle instruction, hardware inserts a 1-cycle bubble automatically. This covers `SFPMAD`, `SFPADD`, `SFPMUL`, `SFPADDI`, `SFPMULI`, `SFPLUTFP32`, `SFPMUL24`, `SFPSWAP`, and the slower modes of `SFPSHFT2`.

**Exceptions requiring manual `SFPNOP` insertion** (hardware bug — auto-stalling does not detect):

1. `SFPAND` with `SFPAND_MOD1_USE_VB` reading a VB written by 2-cycle instruction
2. `SFPOR` with `SFPOR_MOD1_USE_VB` reading a VB written by 2-cycle instruction
3. `SFPIADD` reading `VD` (the implicit second source) written by 2-cycle instruction
4. `SFPSHFT` reading `VD` (the implicit second source) written by 2-cycle instruction
5. `SFPCONFIG` reading `LReg[0]` written by 2-cycle instruction
6. `SFPSWAP` (all modes except `SFPSWAP_MOD1_SWAP`) reading `VC` or `VD` on the 1st cycle

**`SFPLOADMACRO` caution:** None of the auto-stalling applies to instructions executed as part of an `SFPLOADMACRO` sequence. Software is entirely responsible for correct scheduling within those sequences.

### 5.3 SFPU ↔ FPU (Matrix Unit) Ordering

Reading Dest after the Matrix Unit has written it requires a gap before `SFPLOAD`:

- **Minimum 3 unrelated Tensix instructions** between the FPU write and the `SFPLOAD`.
- Alternatively, `STALLWAIT` with block bit B8 and condition C7.
- The 3-instruction gap is preferred in practice; `STALLWAIT` is a fallback.

Writing Dest from the SFPU (`SFPSTORE`) and then reading it with the FPU similarly requires ordering (handled by the same `STALLWAIT` mechanisms described in tensix-coprocessor-pipeline.md).

### 5.4 PRNG

The hardware PRNG used by `SFPSTOCHRND` and `SFPMOV_MOD1_FROM_SPECIAL` (VC=9) is a per-lane 32-bit LFSR:

```python
def advance_prng(lane, State):
    result = State[lane]
    taps = popcount(result & 0x80200003)
    State[lane] = ((~taps & 1) << 31) | (result >> 1)
    return result
```

The statistical quality of this PRNG is poor. Software requiring high-quality randomness should implement its own PRNG in LRegs.

---

## 6. Emulator Implementation Notes

### 6.1 Register File Initialization

At reset:
```python
# Hardware-fixed read-only constants — initialize once at reset
LReg[8]  = [0x3F566189] * 32   # 0.8373f
LReg[9]  = [0x00000000] * 32   # 0.0
LReg[10] = [0x3F800000] * 32   # 1.0f
LReg[15] = [i * 2 for i in range(32)]  # 0, 2, 4, ..., 62

# PRNG state — arbitrary initial value (firmware sets this before use)
PRNG_State = [0] * 32

# Predication state
LaneFlags                = [False] * 32
UseLaneFlagsForLaneEnable = [False] * 32
FlagStack                = [[] for _ in range(32)]  # max depth 8

# LaneConfig — all zero by default
LaneConfig = [0] * 32  # 18-bit field per lane
```

The programmable constants `LReg[11..14]` are written by firmware (typically via `SFPCONFIG` in `ex_load_const()` called at boot by BRISC). The emulator should not assume any particular value at reset; wait for the `SFPCONFIG` instruction to write them.

### 6.2 LReg Write Guards

Only `LReg[0..7]` and `LReg[16]` are writable by regular instructions. Write to indices 8–10, 15 must be silently ignored (read-only hardware). Write to indices 11–14 must be rejected unless the instruction is `SFPCONFIG`.

### 6.3 FP32 Conformance

The SFPU is "closer to" but not fully IEEE 754 compliant. Key deviations:

- Denormal inputs to arithmetic operations are treated as zero (flush-to-zero input).
- Denormal results are flushed to sign-preserved zero.
- Canonical NaN output is always `0x7FC00000` regardless of input NaN payload.
- The FMA (`SFPMAD`) is partially fused: the product is kept in higher precision than FP32 but not infinite precision.
- Rounding mode is always round-to-nearest-ties-to-even (for arithmetic); there is no way to change it per-instruction.

### 6.4 Instruction Dispatch by Sub-unit

In the emulator, each SFPU instruction maps to a specific sub-unit for latency modeling:

```python
LOAD_SUBUNIT  = {"SFPLOAD", "SFPLOADI", "SFPNOP"}
SIMPLE_SUBUNIT = {"SFPMOV", "SFPABS", "SFPAND", "SFPOR", "SFPXOR", "SFPNOT",
                  "SFPSHFT", "SFPLZ", "SFPEXEXP", "SFPEXMAN", "SFPDIVP2",
                  "SFPSETEXP", "SFPSETSGN", "SFPSETMAN", "SFPIADD",
                  "SFPCAST", "SFPSETCC", "SFPENCC", "SFPPUSHC", "SFPPOPC",
                  "SFPCOMPC", "SFPARECIP", "SFPGT", "SFPLE", "SFPCONFIG"}
MAD_SUBUNIT   = {"SFPMAD", "SFPADD", "SFPMUL", "SFPADDI", "SFPMULI",
                  "SFPLUTFP32", "SFPMUL24", "SFPSWAP"}
ROUND_SUBUNIT = {"SFPSTOCHRND", "SFPSHFT2"}
STORE_SUBUNIT = {"SFPSTORE"}
```

---

## Source References

| Source | Path | Relevance |
|--------|------|-----------|
| VectorUnit.md | `tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/VectorUnit.md` | Overall instruction table, latency, lane predication model, PRNG |
| LReg.md | `tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/LReg.md` | Register file structure, constant values, lane layout |
| SFPLOAD.md | `tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPLOAD.md` | Load functional model, Mod0 table, bit-shuffle helpers |
| SFPSTORE.md | `tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPSTORE.md` | Store functional model, Mod0 table |
| SFPMAD.md | `tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPMAD.md` | MAD functional model, Mod1 flags, IEEE divergences, auto-stalling bugs |
| SFPADD.md, SFPMUL.md | `...TensixCoprocessor/SFPADD.md` etc. | Aliases to SFPMAD |
| SFPADDI.md, SFPMULI.md | `...TensixCoprocessor/SFPADDI.md` etc. | Immediate variants |
| SFPDIVP2.md | `...TensixCoprocessor/SFPDIVP2.md` | Exponent adjustment |
| SFPEXEXP.md, SFPEXMAN.md | `...TensixCoprocessor/SFPEXEXP.md` etc. | Field extraction |
| SFPIADD.md | `...TensixCoprocessor/SFPIADD.md` | Integer add, CC setting |
| SFPSETCC.md | `...TensixCoprocessor/SFPSETCC.md` | Condition code setting |
| SFPMOV.md | `...TensixCoprocessor/SFPMOV.md` | Move, negate, PRNG, config read |
| SFPLUTFP32.md | `...TensixCoprocessor/SFPLUTFP32.md` | Piecewise LUT, Lut16ToFp32 |
| SFPSTOCHRND*.md | `...TensixCoprocessor/SFPSTOCHRND*.md` | All three stochastic rounding flavors |
| SFPCAST*.md | `...TensixCoprocessor/SFPCAST*.md` | All three type conversion flavors |
| SFPABS.md | `...TensixCoprocessor/SFPABS.md` | Absolute value (int and float modes) |
| SFPAND.md, SFPOR.md, SFPXOR.md, SFPNOT.md | `...TensixCoprocessor/SFPAND.md` etc. | Bitwise logic |
| SFPLZ.md | `...TensixCoprocessor/SFPLZ.md` | Leading zero count |
| SFPSETEXP.md, SFPSETSGN.md, SFPSETMAN.md | `...TensixCoprocessor/SFPSETEXP.md` etc. | Field-level FP manipulation |
| SFPGT.md, SFPLE.md | `...TensixCoprocessor/SFPGT.md` etc. | Comparison instructions (new in Blackhole) |
| SFPARECIP.md | `...TensixCoprocessor/SFPARECIP.md` | Approximate reciprocal/exp (new in Blackhole) |
| SFPSWAP.md | `...TensixCoprocessor/SFPSWAP.md` | Swap / min+max / argmin+argmax |
| SFPSHFT.md, SFPSHFT2.md | `...TensixCoprocessor/SFPSHFT.md` etc. | Shift instructions |
| SFPMUL24.md | `...TensixCoprocessor/SFPMUL24.md` | 23-bit integer multiply (new in Blackhole) |
| SFPCONFIG.md | `...TensixCoprocessor/SFPCONFIG.md` | Configuration writes, LaneConfig table |
| SFPENCC.md, SFPPUSHC.md, SFPPOPC.md, SFPCOMPC.md | `...TensixCoprocessor/SFPENCC.md` etc. | Predication control |
| SFPLOADI.md | `...TensixCoprocessor/SFPLOADI.md` | Immediate load |
| SFPNOP.md | `...TensixCoprocessor/SFPNOP.md` | No-op |
| Dst.md | `...TensixCoprocessor/Dst.md` | Dest register layout, data types |
| sfpi_constants.h | `sfpi/include/sfpi_constants.h` | All `CREG_IDX_*`, `SFPLOAD_MOD0_*`, `SFPCAST_MOD1_*`, `SFPSTOCHRND_*` constants |
| ckernel_instr_params.h | `tt-llk/tt_llk_blackhole/common/inc/ckernel_instr_params.h` | `p_sfpu::LCONST_*`, `LREG*`, `LTILEID` names |
