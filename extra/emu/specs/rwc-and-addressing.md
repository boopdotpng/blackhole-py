# RWC and Addressing — Blackhole Tensix Coprocessor

This document specifies how the Tensix coprocessor tracks position within tiles during
computation, covering Read-Write Counters (RWC), Address Mode descriptors (AddrMod), and
Address Counters (ADC).

---

## 1. Overview

Math and SFPU instructions (MVMUL, ELWADD, SFPLOAD, SFPSTORE, …) do not accept absolute
register-file addresses in their instruction words — the instruction word's `dst` field is
only a small offset. The actual addressing is driven by two complementary counter systems:

| System | Users | What it counts |
|--------|-------|----------------|
| **RWC** | Matrix Unit (FPU), Vector Unit (SFPU) | Rows in SrcA, SrcB, Dst register files |
| **ADC** | Unpackers, Packers | X/Y/Z/W tile coordinates → L1 address and Dst datum index |

Both systems follow the same pattern: an instruction *reads* the current counter value to form
its address, then *advances* the counter via a post-instruction update specified by an **AddrMod**
descriptor (for RWCs) or an explicit increment (for ADCs).

---

## 2. RWC — Read-Write Counters

### 2.1 State

Each of the three Tensix threads has its own independent RWC state. There is no cross-thread
access.

```c
struct {
    uint10_t Dst,     Dst_Cr;    // 10-bit; Dest register row index
    uint6_t  SrcA,    SrcA_Cr;  //  6-bit; SrcA register row index
    uint6_t  SrcB,    SrcB_Cr;  //  6-bit; SrcB register row index
    uint2_t  FidelityPhase;     //  2-bit; 0..3 multiplication fidelity phase
    uint1_t  ExtraAddrModBit;   //  1-bit; selects upper AddrMod bank
} RWCs[3];  // indexed by CurrentThread
```

The `_Cr` ("Column Register") variants are checkpointed copies of the main counters. They
serve as the base for CR-mode increments and clears (see §4 AddrMod).

**Bit widths and valid ranges:**

| Counter | Width | Max value | Meaning of 1 unit |
|---------|-------|-----------|--------------------|
| `SrcA`  | 6 bits | 63 | 1 row of SrcA (16 elements × 19 bits each) |
| `SrcB`  | 6 bits | 63 | 1 row of SrcB |
| `Dst`   | 10 bits | 1023 | 1 row of Dst16b (16 elements × 16 bits) |
| `FidelityPhase` | 2 bits | 3 | Selects mantissa bits for multiply |

SrcA and SrcB each hold 2 banks of 64 rows × 16 columns. Dst holds 1024 rows × 16 columns
in 16-bit mode (512 rows in 32-bit mode).

### 2.2 How Instructions Use RWC

**MVMUL** (`Dst += SrcB @ SrcA`) reads:

```c
uint6_t SrcARow = RWCs[CurrentThread].SrcA & 0x38;  // aligned to 8-row block
uint6_t SrcBRow = RWCs[CurrentThread].SrcB & 0x38;  // aligned to 8-row block
uint10_t DstRow = RWCs[CurrentThread].Dst + ConfigState.DEST_REGW_BASE_Base
                + DstField + ThreadConfig[CurrentThread].DEST_TARGET_REG_CFG_MATH_Offset;
DstRow &= ~7;  // aligned to 8-row block
```

MVMUL consumes 16 rows from SrcA (rows `SrcARow` through `SrcARow+15`) and 8 rows from SrcB
(rows `SrcBRow` through `SrcBRow+7`), writes an 8×16 result to Dst rows `DstRow` through
`DstRow+7`.

**ELWADD** (`Dst = SrcA + SrcB` or `Dst += SrcA + SrcB`) reads in the same pattern but
uses 8 rows from each source and destination:

```c
uint6_t SrcARow = RWCs[CurrentThread].SrcA & 0x38;
uint6_t SrcBRow = RWCs[CurrentThread].SrcB & (broadcast ? 0x3f : 0x38);
uint10_t DstRow = (RWCs[CurrentThread].Dst + ... ) & 0x3f8;  // aligned to 8
```

**SFPLOAD / SFPSTORE** read Dst at a 4-row-aligned address:

```c
uint10_t Addr = Imm10 + DEST_TARGET_REG_CFG_MATH_Offset
              + RWCs[CurrentThread].Dst + ConfigState.DEST_REGW_BASE_Base;
uint10_t Row    = (Addr & ~3) + (Lane / 8);  // 4-row aligned group
uint4_t  Column = (Lane & 7) * 2;            // even column; bit 1 of Addr selects odd
```

Lane 0..7 map to row `Addr & ~3`, lanes 8..15 to `+1`, 16..23 to `+2`, 24..31 to `+3`.
The `Imm10` field of SFPLOAD/SFPSTORE is `dest_reg_addr`, added directly to `RWC_D + base`.

SFPLOAD/SFPSTORE apply `ApplyPartialAddrMod` (§4) after execution — they advance Dst/SrcA/SrcB
RWCs but do **not** update FidelityPhase.

**PACR** (packer) uses ADC counters, not RWC directly (see §5).

### 2.3 SETRWC Instruction

```c
TT_SETRWC(clear_ab_vld, rwc_cr, rwc_d, rwc_b, rwc_a, BitMask)
```

**Encoding** (6-bit opcode 0x37, full word left-shifted 2 when in instruction stream):

| Bits [29:24] | Bits [23:22] | Bits [21:18] | Bits [17:14] | Bits [13:10] | Bits [9:6] | Bits [5:0] |
|---|---|---|---|---|---|---|
| opcode=0x37 | clear_ab_vld | rwc_cr (4b) | rwc_d (4b) | rwc_b (4b) | rwc_a (4b) | BitMask (6b) |

**BitMask** selects which counters receive the new values (using `p_setrwc` constants):

| Mask | Meaning |
|------|---------|
| `SET_A` = 0x1 | Set SrcA |
| `SET_B` = 0x2 | Set SrcB |
| `SET_D` = 0x4 | Set Dst |
| `SET_F` = 0x8 | Set Fidelity (always clears to 0) |
| Combinations | `SET_AB`=0x3, `SET_ABD`=0x7, `SET_ABD_F`=0xf, etc. |

**CR modifier** in `rwc_cr` field (4-bit field):

| Bit | Meaning |
|-----|---------|
| `CR_A`=0x1 | SrcA: add `rwc_a` to existing `SrcA_Cr` |
| `CR_B`=0x2 | SrcB: add `rwc_b` to existing `SrcB_Cr` |
| `CR_D`=0x4 | Dst: add `rwc_d` to existing `Dst_Cr` |
| `C_TO_CR_MODE`=0x8 | Dst: add `rwc_d` to current `Dst` (not `Dst_Cr`) then checkpoint |

**clear_ab_vld** (2-bit): optionally flip SrcA/SrcB bank and release bank back to unpackers.

**Functional model:**

```c
auto& RWC = RWCs[CurrentThread];
if (BitMask & SET_A) {
    if (rwc_cr & CR_A) rwc_a += RWC.SrcA_Cr;
    RWC.SrcA = rwc_a;  RWC.SrcA_Cr = rwc_a;
}
if (BitMask & SET_B) {
    if (rwc_cr & CR_B) rwc_b += RWC.SrcB_Cr;
    RWC.SrcB = rwc_b;  RWC.SrcB_Cr = rwc_b;
}
if (BitMask & (SET_D | C_TO_CR_MODE)) {
    if (rwc_cr & C_TO_CR_MODE) rwc_d += RWC.Dst;       // base = current C
    else if (rwc_cr & CR_D)    rwc_d += RWC.Dst_Cr;    // base = checkpoint
    RWC.Dst = rwc_d;  RWC.Dst_Cr = rwc_d;
}
if (BitMask & SET_F) RWC.FidelityPhase = 0;
if (clear_ab_vld & 1) { release_srca_bank(); flip_srca_bank(); }
if (clear_ab_vld & 2) { release_srcb_bank(); flip_srcb_bank(); }
```

The most common usage is `SETRWC(CLR_NONE, 0, 0, 0, 0, SET_ABD_F)` to reset all counters to
zero at the start of a tile computation.

### 2.4 INCRWC Instruction

```c
TT_INCRWC(rwc_cr, rwc_d, rwc_b, rwc_a)
```

**Encoding** (opcode 0x38):

| Bits [23:18] | Bits [17:14] | Bits [13:10] | Bits [9:6] |
|---|---|---|---|
| rwc_cr (3b CR flags, 3b padding) | rwc_d (4b) | rwc_b (4b) | rwc_a (4b) |

**Functional model:**

```c
auto& RWC = RWCs[CurrentThread];
if (rwc_cr & SrcACr) { RWC.SrcA_Cr += rwc_a; RWC.SrcA = RWC.SrcA_Cr; }
else                 { RWC.SrcA += rwc_a; }
if (rwc_cr & SrcBCr) { RWC.SrcB_Cr += rwc_b; RWC.SrcB = RWC.SrcB_Cr; }
else                 { RWC.SrcB += rwc_b; }
if (rwc_cr & DstCr)  { RWC.Dst_Cr  += rwc_d; RWC.Dst  = RWC.Dst_Cr; }
else                 { RWC.Dst  += rwc_d; }
```

INCRWC does not touch FidelityPhase. It is useful for fine-grained manual counter control
outside of the AddrMod mechanism.

---

## 3. AddrMod — Address Mode Descriptors

### 3.1 Purpose

Every math/SFPU instruction has a 2-bit `addr_mode` field (called `AddrMod` in ISA docs).
This selects one of up to 8 pre-configured descriptor entries that specify how to update the
RWC counters *after* the instruction executes. This avoids encoding large increment values
directly in the (narrow) instruction word.

### 3.2 Index Calculation

```c
void ApplyAddrMod(uint2_t AddrMod, bool UpdateFidelityPhase = true) {
    auto& RWC = RWCs[CurrentThread];
    uint3_t Index = AddrMod;  // 2-bit field from instruction
    if (RWC.ExtraAddrModBit || ThreadConfig[CurrentThread].ADDR_MOD_SET_Base) {
        Index += 4;  // use upper bank (sections 4..7)
    }
    // ... apply descriptor at Index
}
```

Instructions with a 2-bit `addr_mode` field select entries 0..3 in the lower bank, or
4..7 in the upper bank (when ExtraAddrModBit or ADDR_MOD_SET_Base is set). The Bias
sub-descriptor can flip ExtraAddrModBit, enabling context switching between the two banks
within a single instruction sequence.

SFPLOAD and SFPSTORE use `ApplyPartialAddrMod` — same as `ApplyAddrMod` but
`UpdateFidelityPhase = false`.

### 3.3 Config Register Layout

The 8 descriptors are stored in `ThreadConfig[CurrentThread]` (per-thread configuration,
written via `SETC16` instruction). There are three sub-descriptors per section:

**AB sub-descriptor** (SrcA/SrcB update), `ADDR32 = 12 + section_index`:

| Bits | Field | Description |
|------|-------|-------------|
| [5:0] | `SrcAIncr` | Unsigned addend to SrcA (6-bit) |
| [6]   | `SrcACR`   | 1 = add to SrcA_Cr checkpoint then assign |
| [7]   | `SrcAClear` | 1 = SrcA = 0, SrcA_Cr = 0 |
| [13:8] | `SrcBIncr` | Unsigned addend to SrcB (6-bit) |
| [14]  | `SrcBCR`   | 1 = add to SrcB_Cr checkpoint then assign |
| [15]  | `SrcBClear` | 1 = SrcB = 0, SrcB_Cr = 0 |

**DST sub-descriptor** (Dst / Fidelity update), `ADDR32 = 28 + section_index`:

| Bits | Field | Description |
|------|-------|-------------|
| [9:0] | `DestIncr` | Signed addend to Dst (10-bit, two's complement) |
| [10]  | `DestCR`   | 1 = add to Dst_Cr checkpoint then assign |
| [11]  | `DestClear` | 1 = Dst = 0, Dst_Cr = 0 |
| [12]  | `DestCToCR` | 1 = add DestIncr to current Dst (C), then checkpoint |
| [14:13] | `FidelityIncr` | 2-bit unsigned addend to FidelityPhase |
| [15]  | `FidelityClear` | 1 = FidelityPhase = 0 |

**BIAS sub-descriptor** (ExtraAddrModBit control), `ADDR32 = 47 + section_index`:

| Bits | Field | Description |
|------|-------|-------------|
| [3:0] | `BiasIncr` | If bits [1:0] != 0: ExtraAddrModBit += 1 |
| [4]   | `BiasClear` | 1 = ExtraAddrModBit = 0 |

**PACK sub-descriptor** (packer ADC Y/Z update), `ADDR32 = 37 + section_index` (only 4 sections):

| Bits | Field | Description |
|------|-------|-------------|
| [3:0] | `YsrcIncr` | ADC Y increment for pack input (Dst row) |
| [4]   | `YsrcCR`   | CR-mode for YsrcIncr |
| [5]   | `YsrcClear` | Clear Y for pack input |
| [9:6] | `YdstIncr` | ADC Y increment for pack output (L1 addr) |
| [10]  | `YdstCR`   | CR-mode for YdstIncr |
| [11]  | `YdstClear` | Clear Y for pack output |
| [12]  | `ZsrcIncr` | 1-bit Z increment for pack input |
| [13]  | `ZsrcClear` | Clear Z for pack input |
| [14]  | `ZdstIncr` | 1-bit Z increment for pack output |
| [15]  | `ZdstClear` | Clear Z for pack output |

### 3.4 Complete ApplyAddrMod Pseudocode

```c
void ApplyAddrMod(uint2_t AddrMod, bool UpdateFidelityPhase) {
    auto& RWC = RWCs[CurrentThread];
    uint3_t Index = AddrMod;
    if (RWC.ExtraAddrModBit || ThreadConfig[CurrentThread].ADDR_MOD_SET_Base)
        Index += 4;
    auto& AB   = ThreadConfig[CurrentThread].ADDR_MOD_AB_SEC[Index];
    auto& Dst  = ThreadConfig[CurrentThread].ADDR_MOD_DST_SEC[Index];
    auto& Bias = ThreadConfig[CurrentThread].ADDR_MOD_BIAS_SEC[Index];

    // SrcA update
    if (AB.SrcAClear)       { RWC.SrcA = 0; RWC.SrcA_Cr = 0; }
    else if (AB.SrcACR)     { RWC.SrcA_Cr += AB.SrcAIncr; RWC.SrcA = RWC.SrcA_Cr; }
    else                    { RWC.SrcA += AB.SrcAIncr; }

    // SrcB update
    if (AB.SrcBClear)       { RWC.SrcB = 0; RWC.SrcB_Cr = 0; }
    else if (AB.SrcBCR)     { RWC.SrcB_Cr += AB.SrcBIncr; RWC.SrcB = RWC.SrcB_Cr; }
    else                    { RWC.SrcB += AB.SrcBIncr; }

    // Dst update
    if (Dst.DestClear)      { RWC.Dst = 0; RWC.Dst_Cr = 0; }
    else if (Dst.DestCToCR) { RWC.Dst += Dst.DestIncr; RWC.Dst_Cr = RWC.Dst; }
    else if (Dst.DestCR)    { RWC.Dst_Cr += Dst.DestIncr; RWC.Dst = RWC.Dst_Cr; }
    else                    { RWC.Dst += Dst.DestIncr; }

    // Fidelity update
    if (UpdateFidelityPhase) {
        if (Dst.FidelityClear)   RWC.FidelityPhase = 0;
        else                     RWC.FidelityPhase += Dst.FidelityIncr;
    }

    // ExtraAddrModBit update
    if (Bias.BiasClear)     RWC.ExtraAddrModBit = 0;
    else if (Bias.BiasIncr & 3) RWC.ExtraAddrModBit += 1;
}
```

---

## 4. Matmul Kernel — Concrete AddrMod Examples

### 4.1 Configuration Setup (from `matmul_trisc1.S`)

The peak matmul kernel (standard 32×32 tile, no transpose, single fidelity) configures five
addr_mod sections via `SETC16` before the compute loop. Decoded from the observed
`ttsetc16` instructions at 0x63c4–0x63fc:

| Section | SrcA | SrcB | Dst | Fidelity | Purpose |
|---------|------|------|-----|----------|---------|
| **ADDR_MOD_0** | incr=0 | incr=8 | incr=8 | - | Step both SrcB and Dst by 8 rows; SrcA holds |
| **ADDR_MOD_1** | incr=16 | cr+0 (reset to checkpoint) | incr=8 | - | Advance SrcA by 16 rows, restore SrcB to CR |
| **ADDR_MOD_2** | cr+0 (reset to checkpoint) | cr+32 | incr=8 | - | Restore SrcA to CR, advance SrcB CR by 32 |
| **ADDR_MOD_4** | cr+32 | cr+48 | cr+0 (reset to checkpoint) | - | Advance SrcA CR by 32, SrcB CR by 48, restore Dst |
| **ADDR_MOD_5** | clr | clr | clr | incr=1 | Reset all counters, increment fidelity phase |

The `cr` in `cr+N` means "add N to the checkpoint register and assign to the active counter".
With 6-bit unsigned arithmetic, cr+48 from a checkpoint of 32 yields `(32+48) & 0x3f = 16`,
which is how the SrcB counter wraps from face 2 back to face 1 (row 16).

### 4.2 RWC Trace: Standard 32×32 Tile Computation

A 32×32 tile uses two 16×16 SrcA faces and two 16×16 SrcB faces. The FPU computes
`Dst[8,16] += SrcB[8,16] @ SrcA[16,16]` per MVMUL. One complete tile (single fidelity
phase) requires 16 MVMULs covering all B-face/A-face combinations.

SrcA layout in register file: face 0 at rows 0–15, face 1 at rows 16–31, face 2 at
rows 32–47, face 3 at rows 48–63. SrcB identical. Dst: face 0 rows 0–7, face 1 rows 8–15,
face 2 rows 16–23, face 3 rows 24–31 (repeating with 32-row period per accumulation pass).

Initial state: `rwc_a=0(cr=0)  rwc_b=0(cr=0)  rwc_d=0(cr=0)`.

```
Insn  AddrMod  Reads [SrcB, SrcA → Dst]     After: rwc_a  rwc_b  rwc_d
  1   MOD_0    SrcB[0..7], SrcA[0..15]→Dst[0..7]   0(cr=0)  8(cr=0)  8(cr=0)
  2   MOD_1    SrcB[8..15], SrcA[0..15]→Dst[8..15] 16(cr=0) 0(cr=0) 16(cr=0)
  3   MOD_0    SrcB[0..7], SrcA[16..31]→Dst[16..23] 16(cr=0) 8(cr=0) 24(cr=0)
  4   MOD_2    SrcB[8..15], SrcA[16..31]→Dst[24..31] 0(cr=0) 32(cr=32) 32(cr=0)
  5   MOD_0    SrcB[32..39], SrcA[0..15]→Dst[32..39] 0(cr=0) 40(cr=32) 40(cr=0)
  6   MOD_1    SrcB[40..47], SrcA[0..15]→Dst[40..47] 16(cr=0) 32(cr=32) 48(cr=0)
  7   MOD_0    SrcB[32..39], SrcA[16..31]→Dst[48..55] 16(cr=0) 40(cr=32) 56(cr=0)
  8   MOD_4    SrcB[40..47], SrcA[16..31]→Dst[56..63] 32(cr=32) 16(cr=16) 0(cr=0)
  9   MOD_0    SrcB[16..23], SrcA[32..47]→Dst[0..7]   32(cr=32) 24(cr=16) 8(cr=0)
 10   MOD_1    SrcB[24..31], SrcA[32..47]→Dst[8..15]  48(cr=32) 16(cr=16) 16(cr=0)
 11   MOD_0    SrcB[16..23], SrcA[48..63]→Dst[16..23] 48(cr=32) 24(cr=16) 24(cr=0)
 12   MOD_2    SrcB[24..31], SrcA[48..63]→Dst[24..31] 32(cr=32) 48(cr=48) 32(cr=0)
 13   MOD_0    SrcB[48..55], SrcA[32..47]→Dst[32..39] 32(cr=32) 56(cr=48) 40(cr=0)
 14   MOD_1    SrcB[56..63], SrcA[32..47]→Dst[40..47] 48(cr=32) 48(cr=48) 48(cr=0)
 15   MOD_0    SrcB[48..55], SrcA[48..63]→Dst[48..55] 48(cr=32) 56(cr=48) 56(cr=0)
 16   MOD_5    SrcB[56..63], SrcA[48..63]→Dst[56..63] 0(cr=0)   0(cr=0)   0(cr=0)  fidelity+=1
```

MVMUL reads SrcA aligned to 16-row blocks (`rwc_a & 0x38`), so the register-file rows
consumed equal the table values. For Dst the hardware aligns to 8-row blocks.

After MVMUL 16, all counters reset to 0 and FidelityPhase increments to 1. The outer MOP
loop re-executes the 16-MVMUL replay buffer for fidelity phases 1, 2, 3 if high-fidelity
is enabled; `SETRWC(CLR_A, 0, 0, 0, 0, SET_ABD_F)` (or CLR_B) resets all and clears
FidelityPhase=0 at the end of the last phase.

### 4.3 Actual Instruction Stream (matmul_trisc1.S, replay buffer at 0x6404)

```asm
6404:  98000000   ttmvmul  0,0,0,0    ; clear_dvalid=0, addr_mode=0, dst=0
6408:  98010000   ttmvmul  0,0,1,0    ; addr_mode=1
640c:  98000000   ttmvmul  0,0,0,0    ; addr_mode=0
6410:  98020000   ttmvmul  0,0,2,0    ; addr_mode=2
6414:  98000000   ttmvmul  0,0,0,0
6418:  98010000   ttmvmul  0,0,1,0
641c:  98000000   ttmvmul  0,0,0,0
6420:  98040000   ttmvmul  0,0,4,0    ; addr_mode=4
6424:  98000000   ttmvmul  0,0,0,0
6428:  98010000   ttmvmul  0,0,1,0
642c:  98000000   ttmvmul  0,0,0,0
6430:  98020000   ttmvmul  0,0,2,0
6434:  98000000   ttmvmul  0,0,0,0
6438:  98010000   ttmvmul  0,0,1,0
643c:  98000000   ttmvmul  0,0,0,0
6440:  98050000   ttmvmul  0,0,5,0    ; addr_mode=5: reset + fidelity increment
```

This replay buffer (16 instructions) is loaded via `ttreplay 16,16,0,1` at 0x6400. The MOP
wrapper executes it once per fidelity phase (`inner_loops = to_underlying(MathFidelity)`).

Note on encoding: All TTI_ (inline) Tensix instructions appear in the instruction stream
left-shifted by 2 bits relative to the TT_OP() encoding. That is, if `TT_OP(opcode, params)`
yields a 32-bit word W, then the instruction stream contains `W << 2`. The `opcode` field
sits in bits [29:24] of TT_OP, and lands in bits [31:26] of the physical instruction word.

The disassembled opcode byte (0x98 for `ttmvmul`) is therefore `0x26 << 2 = 0x98`, and
0xdc for `ttsetrwc` is `0x37 << 2 = 0xdc`.

### 4.4 SETRWC at Loop Boundary (matmul_trisc1.S, 0x64a0)

```asm
64a0:  dc00003c   ttsetrwc  0,0,0,0,0,15
```

Decoded: `SETRWC(clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=0xf)`

BitMask `0xf = SET_ABD_F` — sets SrcA=0, SrcB=0, Dst=0, Fidelity=0. All checkpoints
also reset to 0 (new values are written to both main counter and `_Cr`). This resets all
RWC state before the inner tile computation begins.

---

## 5. ADC — Address Counters

### 5.1 State

```c
struct {
    struct {
        struct {
            uint18_t X, X_Cr;
            uint13_t Y, Y_Cr;
            uint8_t  Z, Z_Cr;
            uint8_t  W, W_Cr;
        } Channel[2];
    } Unpacker[2], Packers;
} ADCs[3];  // indexed by CurrentThread (or overridden)
```

ADCs are used by unpackers and packers. The RWC system is entirely separate.

**Per unit:**

| Unit | What it addresses |
|------|------------------|
| `Unpacker[0]` | SrcA data in L1 (UNP0) |
| `Unpacker[1]` | SrcB data in L1 (UNP1) |
| `Packers` | Dst→L1 (all 4 packers share one set) |

### 5.2 Channel Semantics

For **unpackers**, `Channel[0]` drives the input (L1 read) path and `Channel[1]` drives the
output (register write) path:

| Counter | Channel 0 | Channel 1 |
|---------|-----------|-----------|
| X | L1 input address generation; part of datum count | Upper limit of datum count |
| Y | Decompressor — seeks to row within L1 | Output address to Dst (UNP0) or SrcB (UNP1) |
| Z | Decompressor (BFP exponent section) | Output address (continued) |
| W | Decompressor | Output address (continued) |

For **packers**, `Channel[0]` drives the input (Dst read) path and `Channel[1]` drives the
output (L1 write) path:

| Counter | Channel 0 | Channel 1 |
|---------|-----------|-----------|
| X | Dst row/column address; datum count start | Datum count end |
| Y | Dst address offset | L1 output address offset |
| Z | Dst address offset | L1 output address offset |
| W | Dst address offset | L1 output address offset |

The packer's Dst input address is:

```c
uint32_t Addr = PCK0_ADDR_BASE_REG_0_Base
    + ADC.X * (PCK0_ADDR_CTRL_XY_REG_0_Xstride & 0xf)
    + ADC.Y * PCK0_ADDR_CTRL_XY_REG_0_Ystride
    + ADC.Z * PCK0_ADDR_CTRL_ZW_REG_0_Zstride
    + ADC.W * PCK0_ADDR_CTRL_ZW_REG_0_Wstride;
// Then: Addr_datum = (Addr / BytesPerDatum) & ~ADC_X_Mask) + (ADC.X & ADC_X_Mask)
//       + DEST_TARGET_REG_CFG_PACK_SEC[i].Offset << 4;
```

The packer L1 output address is computed from `PCK0_ADDR_BASE_REG_1_Base` plus `Channel[1].Y/Z/W`
weighted by the corresponding stride registers, aligned to 16 bytes.

### 5.3 ADC Instructions

All ADC instructions execute on the **Miscellaneous Unit**.

**CntSetMask** (3-bit) selects which counters to modify:

| CntSetMask | Constant | Units affected |
|-----------|----------|----------------|
| 0b001 | `UNP0` / `UNP_A` | Unpacker 0 (SrcA) |
| 0b010 | `UNP1` / `UNP_B` | Unpacker 1 (SrcB) |
| 0b011 | `UNP_AB` | Both unpackers |
| 0b100 | `PAC` | Packers |

**SETADC** — set one dimension of one channel:

```c
TT_SETADC(CntSetMask, Channel, XYZW, NewValue)
// Sets ADC.Channel[Channel].{X|Y|Z|W} = NewValue (and its _Cr)
// NewValue bits[17:16] = ThreadOverride (0 = use CurrentThread)
```

**SETADCXY** — set X and Y of both channels simultaneously:

```c
TT_SETADCXY(CntSetMask, Y1Val, X1Val, Y0Val, X0Val, BitMask)
// BitMask bits: X0(0), Y0(1), X1(2), Y1(3) — select which to update
// Values are 3-bit (for small tile face indices)
```

**SETADCZW** — set Z and W of both channels simultaneously:

```c
TT_SETADCZW(CntSetMask, W1Val, Z1Val, W0Val, Z0Val, BitMask)
// BitMask: Z0(0), W0(1), Z1(2), W1(3)
```

**SETADCXX** — set X of both channels from 10-bit values:

```c
TT_SETADCXX(CntSetMask, X1Val, X0Val)
// X0Val (10b): Channel[0].X and Channel[0].X_Cr
// X1Val (10b): Channel[1].X and Channel[1].X_Cr
// (No ThreadOverride; always uses CurrentThread)
```

**INCADCXY** — increment X and Y of both channels:

```c
TT_INCADCXY(CntSetMask, Y1Inc, X1Inc, Y0Inc, X0Inc)
// All increments are 3-bit; adds directly to X/Y (not _Cr)
```

**INCADCZW** — increment Z and W of both channels:

```c
TT_INCADCZW(CntSetMask, W1Inc, Z1Inc, W0Inc, Z0Inc)
```

**X wrapping via SETADCXX:** The `SETADCXX` instruction sets both `Channel[0].X` (the
starting X counter) and `Channel[1].X` (the ending X counter used for datum count). The
datum count passed to the unpacker/packer is `Channel[1].X - Channel[0].X + 1`. Wrapping
or stopping conditions are handled externally by software resetting these via SETADCXX or
SETADC before the next UNPACR/PACR.

### 5.4 ADC Usage in the Matmul Kernel (matmul_trisc2.S)

The pack thread (TRISC2) sets up ADC for the packers:

```asm
7114:  4600002d   ttsetadcxy  4,0,0,0,0,11    ; PAC, Y1=0,X1=0,Y0=0,X0=0, mask=0b1011 (X0,Y0,Y1)
7118:  5200003d   ttsetadczw  4,0,0,0,0,15    ; PAC, all Z/W = 0
```

This initializes the packer ADC to position (X=0, Y=0, Z=0, W=0) in both channels,
targeting the beginning of the Dst tile and the L1 destination address.

The TRISC0 (unpack) thread similarly initializes Unpacker ADCs before each UNPACR sequence
using SETADCXY/SETADCZW to position at the correct tile face within L1.

---

## 6. Functional Model (Python)

```python
class RWCState:
    def __init__(self):
        self.srca = self.srca_cr = 0
        self.srcb = self.srcb_cr = 0
        self.dst  = self.dst_cr  = 0
        self.fidelity = 0
        self.extra_addr_mod_bit = 0
    SRCA_MASK = 0x3F
    SRCB_MASK = 0x3F
    DST_MASK  = 0x3FF
    FIDELITY_MASK = 0x3

def apply_addr_mod(rwc: RWCState, ab, dst_d, bias, update_fidelity=True):
    """Apply one AddrMod descriptor entry to RWC state."""
    # SrcA
    if ab['srca_clr']:
        rwc.srca = rwc.srca_cr = 0
    elif ab['srca_cr']:
        rwc.srca_cr = (rwc.srca_cr + ab['srca_incr']) & rwc.SRCA_MASK
        rwc.srca = rwc.srca_cr
    else:
        rwc.srca = (rwc.srca + ab['srca_incr']) & rwc.SRCA_MASK

    # SrcB
    if ab['srcb_clr']:
        rwc.srcb = rwc.srcb_cr = 0
    elif ab['srcb_cr']:
        rwc.srcb_cr = (rwc.srcb_cr + ab['srcb_incr']) & rwc.SRCB_MASK
        rwc.srcb = rwc.srcb_cr
    else:
        rwc.srcb = (rwc.srcb + ab['srcb_incr']) & rwc.SRCB_MASK

    # Dst
    if dst_d['dest_clr']:
        rwc.dst = rwc.dst_cr = 0
    elif dst_d['dest_c2cr']:     # CtoCR: add to C, checkpoint
        rwc.dst = (rwc.dst + dst_d['dest_incr']) & rwc.DST_MASK
        rwc.dst_cr = rwc.dst
    elif dst_d['dest_cr']:        # CR: add to checkpoint, assign
        rwc.dst_cr = (rwc.dst_cr + dst_d['dest_incr']) & rwc.DST_MASK
        rwc.dst = rwc.dst_cr
    else:
        rwc.dst = (rwc.dst + dst_d['dest_incr']) & rwc.DST_MASK

    # Fidelity
    if update_fidelity:
        if dst_d['fidelity_clr']:
            rwc.fidelity = 0
        else:
            rwc.fidelity = (rwc.fidelity + dst_d['fidelity_incr']) & rwc.FIDELITY_MASK

    # ExtraAddrModBit
    if bias['bias_clr']:
        rwc.extra_addr_mod_bit = 0
    elif bias['bias_incr'] & 3:
        rwc.extra_addr_mod_bit = min(1, rwc.extra_addr_mod_bit + 1)


def setrwc(rwc: RWCState, rwc_a=0, rwc_b=0, rwc_d=0, rwc_cr=0, bitmask=0,
           clear_srca_bank=False, clear_srcb_bank=False):
    """Execute SETRWC instruction."""
    SET_A, SET_B, SET_D, SET_F = 1, 2, 4, 8
    CR_A, CR_B, CR_D, C_TO_CR = 1, 2, 4, 8
    if bitmask & SET_A:
        base = rwc.srca_cr if (rwc_cr & CR_A) else 0
        rwc.srca = rwc.srca_cr = (base + rwc_a) & RWCState.SRCA_MASK
    if bitmask & SET_B:
        base = rwc.srcb_cr if (rwc_cr & CR_B) else 0
        rwc.srcb = rwc.srcb_cr = (base + rwc_b) & RWCState.SRCB_MASK
    if bitmask & (SET_D | C_TO_CR):
        if rwc_cr & C_TO_CR:   base = rwc.dst
        elif rwc_cr & CR_D:    base = rwc.dst_cr
        else:                  base = 0
        rwc.dst = rwc.dst_cr = (base + rwc_d) & RWCState.DST_MASK
    if bitmask & SET_F:
        rwc.fidelity = 0
    # Bank flip (clear_dvalid) handled separately by hardware


def incrwc(rwc: RWCState, rwc_a=0, rwc_b=0, rwc_d=0, rwc_cr=0):
    """Execute INCRWC instruction."""
    CR_A, CR_B, CR_D = 1, 2, 4
    if rwc_cr & CR_A:
        rwc.srca_cr = (rwc.srca_cr + rwc_a) & RWCState.SRCA_MASK
        rwc.srca = rwc.srca_cr
    else:
        rwc.srca = (rwc.srca + rwc_a) & RWCState.SRCA_MASK
    if rwc_cr & CR_B:
        rwc.srcb_cr = (rwc.srcb_cr + rwc_b) & RWCState.SRCB_MASK
        rwc.srcb = rwc.srcb_cr
    else:
        rwc.srcb = (rwc.srcb + rwc_b) & RWCState.SRCB_MASK
    if rwc_cr & CR_D:
        rwc.dst_cr = (rwc.dst_cr + rwc_d) & RWCState.DST_MASK
        rwc.dst = rwc.dst_cr
    else:
        rwc.dst = (rwc.dst + rwc_d) & RWCState.DST_MASK


def mvmul_dst_row(rwc: RWCState, dst_field=0, dest_target_offset=0, dest_regw_base=0):
    """Compute the Dst row used by MVMUL."""
    row = dst_field + dest_target_offset + rwc.dst + dest_regw_base
    return row & ~7  # align to 8-row block, masked to 10 bits

def sfpload_row_column(rwc: RWCState, imm10=0, dest_target_offset=0,
                        dest_regw_base=0, lane=0, addr_bit1_exchange=False):
    """Compute the Dst row and column accessed by SFPLOAD/SFPSTORE for a given lane."""
    addr = (imm10 + dest_target_offset + rwc.dst + dest_regw_base) & 0x3FF
    row    = (addr & ~3) + (lane // 8)
    column = (lane & 7) * 2
    if (addr & 2) or addr_bit1_exchange:
        column += 1
    return row & 0x3FF, column & 0xF
```

---

## 7. Source References

| File | Content |
|------|---------|
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/RWCs.md` | RWC state definition, `ApplyAddrMod` pseudocode, instruction list |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/SETRWC.md` | SETRWC encoding and functional model |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/INCRWC.md` | INCRWC encoding and functional model |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/MVMUL.md` | MVMUL functional model (RWC consumption) |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/ELWADD.md` | ELWADD functional model |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/SFPLOAD.md` | SFPLOAD — Dst addressing, ApplyPartialAddrMod |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/SFPSTORE.md` | SFPSTORE — Dst addressing |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/ADCs.md` | ADC state definition and channel usage table |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/SETADC.md` | SETADC instruction |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/SETADCXY.md` | SETADCXY instruction |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/SETADCZW.md` | SETADCZW instruction |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/SETADCXX.md` | SETADCXX instruction |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/INCADCXY.md` | INCADCXY instruction |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/INCADCZW.md` | INCADCZW instruction |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/Packers/InputAddressGenerator.md` | Packer Dst→L1 address computation using ADCs |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/Packers/OutputAddressGenerator.md` | Packer L1 output address computation |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/Dst.md` | Dst register file layout, 16-bit vs 32-bit rows |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/SrcASrcB.md` | SrcA/SrcB register file layout and fidelity phase details |
| `tt-llk/tt_llk_blackhole/common/inc/ckernel_addrmod.h` | `addr_mod_t` struct, field layout, SETC16 config register addresses |
| `tt-llk/tt_llk_blackhole/common/inc/ckernel_instr_params.h` | `p_setrwc`, `p_setadc` constant definitions |
| `tt-llk/tt_llk_blackhole/common/inc/ckernel_ops.h` | TT_OP_SETRWC, TT_OP_INCRWC, TT_OP_SETADC, TT_OP_SETADCXY, etc. macros |
| `tt-llk/tt_llk_blackhole/llk_lib/llk_math_matmul.h` | `matmul_configure_addrmod()` — actual addr_mod setup for all tile shapes |
| `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/cfg_defines.h` | ADDR_MOD_AB_SEC[0..7]_*, ADDR_MOD_DST_SEC[0..7]_*, ADDR_MOD_BIAS_SEC[0..7]_*, ADDR_MOD_PACK_SEC[0..3]_* ADDR32 offsets |
| `blackhole-py/disasms/matmul_peak/matmul_trisc1.S` | TRISC1 (math) disassembly: SETC16 addr_mod config + MVMUL replay buffer |
| `blackhole-py/disasms/matmul_peak/matmul_trisc2.S` | TRISC2 (pack) disassembly: SETADCXY/SETADCZW for packer ADC init |
| `blackhole-py/dsl.py` | TensixOp definitions with opcode values; encoding note: TTI_ instructions appear in stream left-shifted by 2 bits |
