# Specialty FPU (Matrix Unit) Operations

Additional Matrix Unit instructions beyond MVMUL, ELWADD/SUB/MUL, GMPOOL, ZEROACC, ZEROSRC, and the MOV* family documented in fpu-operations.md. These are listed in STALLWAIT block B6 (`STALL_MATH`) but are not needed for matmul_peak or add1.


## Status on Wormhole B0 / Blackhole

Several of these instructions are **legacy** — they were functional on Grayskull but were neutered when the architecture moved to Wormhole. The still-functional ones serve niche roles.

| Instruction | Opcode | Status on WH/BH | Notes |
|---|---|---|---|
| CONV3S1 | 0x22 | Neutered: computes `Dst += 0` | Was 3×3 convolution stride 1 |
| CONV3S2 | 0x23 | Neutered: computes `Dst += 0` | Was 3×3 convolution stride 2 |
| APOOL3S1 | 0x25 | Neutered: computes `Dst += 0` | Was 3×3 average pool stride 1 |
| APOOL3S2 | 0x32 | Neutered: computes `Dst += 0` | Was 3×3 average pool stride 2 |
| MPOOL3S1 | 0x24 | Neutered: behaves like GMPOOL on all-zero SrcA | Was 3×3 max pool stride 1 |
| MPOOL3S2 | 0x31 | Neutered: behaves like GMPOOL on all-zero SrcA | Was 3×3 max pool stride 2 |
| DOTPV | 0x29 | Functional: identical to MVMUL without broadcast | Legacy; prefer MVMUL |
| GAPOOL | 0x34 | Functional: 4×16 matmul (half-height MVMUL) | Used in reduce kernels |
| GATESRCRST | 0x35 | Functional: invalidates SrcB operand cache | Used in reduce scalar path |
| CLREXPHIST | 0x21 | Functional: resets packer exponent histograms | For BFP packing |
| SHIFTXA | 0x17 | Functional: shift 16 SrcA rows left/right by 1 lane | Has hardware bug |
| SHIFTXB | 0x18 | Functional: shift/rotate 1 SrcB row left by 1 lane | 0.5 IPC |

All of these are NonContractualBehaviors according to the ISA docs — the neutered opcodes may be repurposed in future architectures.


## Neutered Legacy Instructions

### CONV3S1, CONV3S2, APOOL3S1, APOOL3S2

**Emulator model:** All four behave as `Dst += 0`. They count as Matrix Unit instructions for STALLWAIT purposes and use RWCs/AddrMod, but the actual computation is trivially zero. An emulator can implement them as no-ops that still apply `clear_dvalid` and `apply_addr_mod`.

```python
def CONV3S1(clear_dvalid, rotate_weights, addr_mode, dst):
    # Neutered on WH/BH — just apply side effects
    apply_clear_dvalid(clear_dvalid)
    apply_addr_mod(addr_mode)

# CONV3S2, APOOL3S1, APOOL3S2: identical treatment
```

**Encoding (shared pattern):**
```
[31:24] = opcode (0x22 / 0x23 / 0x25 / 0x32)
[23:22] = clear_dvalid  (2 bits)
[17]    = rotate_weights (CONV only) / index_en (APOOL only)
[15]    = addr_mode      (BH: bit 14)
[13:0]  = dst
```

### MPOOL3S1, MPOOL3S2

Behave like GMPOOL with all-zero SrcA — effectively a no-op that applies side effects and may touch Dst in an uninteresting way. An emulator can treat them identically to the CONV/APOOL neutered instructions.

```python
def MPOOL3S1(clear_dvalid, addr_mode, index_en, dst):
    # Neutered on WH/BH — similar to GMPOOL on zero SrcA
    apply_clear_dvalid(clear_dvalid)
    apply_addr_mod(addr_mode)
```


## DOTPV — Dot Product / Matrix Multiply (opcode 0x29)

Identical to MVMUL with `BroadcastSrcBRow == false`. Prefer MVMUL in all cases. Exists for backward compatibility.

**Encoding:** Same as MVMUL (see fpu-operations.md) but lacks the broadcast bit.

```
[31:24] = 0x29
[23:22] = clear_dvalid  (2 bits)
[21]    = dest_accum_en  (1 bit)
[20:19] = instr_mod19    (2 bits — FlipSrcB:FlipSrcA)
[18:14] = addr_mode      (5 bits)
[13:0]  = dst            (14 bits)
```

**Functional model:** Exactly the same as MVMUL's functional model (see fpu-operations.md §MVMUL), but `BroadcastSrcBRow` is always `false`.

**Performance:** 1 IPC, 5-cycle latency. 4.096 TFLOP/s at 1 fidelity phase (same as MVMUL without broadcast).


## GAPOOL — Global Average Pool / Half-Height Matmul (opcode 0x34)

Almost identical to MVMUL, but operates on a **4×16** SrcB/Dst region instead of 8×16. The SrcB alignment is the same as MVMUL (aligned to 8-row boundary), so GAPOOL uses only the top 4 rows. Dst alignment is relaxed to 4-row boundaries.

Achieves half the throughput of MVMUL (2.048 TFLOP/s vs 4.096 TFLOP/s at 1 fidelity phase). Software is encouraged to use MVMUL when possible, but GAPOOL has niche uses in reduction kernels where 4×16 granularity is needed.

**Encoding:**
```
[31:24] = 0x34
[23:22] = clear_dvalid      (2 bits)
[21:19] = instr_mod19        (3 bits — FlipSrcB:FlipSrcA)
[18:15] = pool_addr_mode     (4 bits — encodes addr_mode + pool config)
[14]    = max_pool_index_en  (1 bit)
[13:0]  = dst                (14 bits)
```

```c
#define TT_OP_GAPOOL(clear_dvalid, instr_mod19, addr_mode, max_pool_index_en, dst) \
    TT_OP(0x34, (((clear_dvalid) << 22) + ((instr_mod19) << 19) + ((addr_mode) << 15) \
               + ((max_pool_index_en) << 14) + ((dst) << 0)))
```

**Functional model:**

```python
def GAPOOL(clear_dvalid, instr_mod19, addr_mode, max_pool_index_en, dst_field):
    # Same as MVMUL but:
    # - BroadcastSrcBRow is always false
    # - NumRows = 4 (not 8)
    # - Dst alignment mask is 0x3FC (4-row aligned) not 0x3F8 (8-row aligned)

    style, use_dst32b = compute_style(SrcA_format, INT8_math, FP16A_force)
    fidelity = (RWC.FidelityPhase + ThreadConfig.FIDELITY_BASE_Phase) & 3

    srca_row = RWC.SrcA & 0x30     # aligned to 16-row boundary
    srcb_row = RWC.SrcB & 0x38     # aligned to 8-row boundary (uses top 4 rows)
    dst_row  = (dst_field + DEST_TARGET_REG_CFG_MATH_Offset
                + RWC.Dst + DEST_REGW_BASE_Base) & 0x3FC  # 4-row aligned

    for i in range(4):             # 4 output rows (not 8)
        for j in range(16):
            acc = 0.0
            for k in range(16):
                a = src_a_fidelity_bits(SrcA[bank][srca_row + k][j], fidelity, style)
                b = src_b_fidelity_bits(SrcB[bank][srcb_row + i][k], fidelity, style)
                acc += a * b
            if use_dst32b:
                Dst32b[dst_row + i][j] += float_fp32(acc)
            else:
                Dst16b[dst_row + i][j] = round_to_format(
                    read_dst(dst_row+i, j, style) + acc, style)

    apply_clear_dvalid(clear_dvalid)
    apply_addr_mod(addr_mode & 3)
```

**LLK usage:** Primary instruction for `ReducePool::Sum` and `ReducePool::Average` operations:
```c
// From llk_math_reduce.h
TTI_GAPOOL(clear_mode, p_gpool::DIM_16X16, ADDR_MOD_0, p_gpool::INDEX_DIS, index)
```

**Performance:** 1 IPC, 5-cycle latency.


## GATESRCRST — Invalidate SrcB Operand Cache (opcode 0x35)

There is a one-slot operand cache between SrcB and the Matrix Unit (FPU). GATESRCRST forcibly invalidates it. The ISA documentation states this "should only be required if there are hardware bugs in the cache invalidation logic" — but in practice it is used in the reduce scalar path after MOVD2B/TRNSPSRCB sequences.

**Encoding:**
```
[31:24] = 0x35
[1]     = reset_srcb_gate_control  (1 bit — invalidate SrcB cache)
[0]     = reset_srca_gate_control  (1 bit — reserved / no known effect)
```

```c
#define TT_OP_GATESRCRST(reset_srcb_gate_control, reset_srca_gate_control) \
    TT_OP(0x35, (((reset_srcb_gate_control) << 1) + ((reset_srca_gate_control) << 0)))
```

**Functional model:**
```python
def GATESRCRST(invalidate_srcb_cache, invalidate_srca):
    if invalidate_srcb_cache:
        MatrixUnit.SrcBOperandCache.invalidate()
    # invalidate_srca: no documented effect, but the bit exists
```

**Emulator note:** If the emulator does not model the SrcB operand cache (most won't), GATESRCRST is a no-op. It should still be decoded and counted as a Matrix Unit instruction for STALLWAIT purposes.

**LLK usage:** Always called as `TTI_GATESRCRST(0b1, 0b1)` — both bits set.

**Performance:** 1 IPC, 1-cycle latency.


## CLREXPHIST — Clear Exponent Histograms (opcode 0x21)

Resets the exponent histogram of all four packers. The exponent histogram is used during BFP (Block Floating Point) packing to determine the shared exponent for a group of values.

**Encoding:**
```
[31:24] = 0x21
[23:0]  = (unused, must be 0)
```

```c
#define TT_OP_CLREXPHIST TT_OP(0x21, 0)
```

**Functional model:**
```python
def CLREXPHIST():
    for packer_id in range(4):
        Packers[packer_id].ExponentHistogram.reset()
```

**Emulator note:** Only relevant if the emulator models BFP packing with exponent histograms. If not, this is a no-op that still counts as a Matrix Unit instruction for STALLWAIT.

**Performance:** 1 IPC, 1-cycle latency.


## SHIFTXA — Shift 16 SrcA Rows by One Lane (opcode 0x17)

Shifts an aligned block of 16 rows of SrcA left or right by one lane (column position), filling the vacant lane with zero. The output is always written to rows 0–15 of SrcA.

**Encoding:**
```
[31:24] = 0x17
[1:0]   = Direction  (2 bits)
```

```c
#define TT_OP_SHIFTXA(log2_amount2, shift_mode) \
    TT_OP(0x17, (((log2_amount2) << 2) + ((shift_mode) << 0)))
```

**Direction values:**
| Value | Name | Effect |
|-------|------|--------|
| 2 | `DIRECTION_RIGHT` | Shift right toward column 15; column 0 filled with zero |
| 3 | `DIRECTION_LEFT` | Shift left toward column 0; column 15 filled with zero |

**Hardware bug:** SHIFTXA cannot specify which aligned block of 16 rows to use as input. The input row block is whatever the most recent MVMUL, ELWADD, ELWSUB, ELWMUL, DOTPV, GMPOOL, GAPOOL, MOVA2D, MOVB2D, MOVD2A, MOVD2B, MOVB2A, or any legacy instruction computed as its starting SrcA row address. This is a NonContractualBehavior.

**Functional model:**
```python
def SHIFTXA(direction):
    # Wait for SrcA bank ownership
    while SrcA[MatrixUnit.SrcABank].AllowedClient != MatrixUnit:
        wait()

    in_row = HARDWARE_BUG_LAST_SRCA_ROW & 0x30  # aligned to 16-row boundary
    bank = MatrixUnit.SrcABank

    for i in range(16):
        if direction == DIRECTION_RIGHT:   # 2
            for col in range(15, 0, -1):
                SrcA[bank][i][col] = SrcA[bank][in_row + i][col - 1]
            SrcA[bank][i][0] = 0
        elif direction == DIRECTION_LEFT:  # 3
            for col in range(15):
                SrcA[bank][i][col] = SrcA[bank][in_row + i][col + 1]
            SrcA[bank][i][15] = 0
```

**Performance:** 1 IPC, 1-cycle latency.


## SHIFTXB — Shift/Rotate One SrcB Row by One Lane (opcode 0x18)

Shifts or rotates one row of SrcB left by one lane. If `ShiftInZero` is true, the rightmost lane is filled with zero; otherwise, the leftmost value wraps around (rotate).

**Encoding:**
```
[31:24] = 0x18
[15]    = addr_mode   (BH: bit 14)
[10]    = ShiftInZero (rot_shift — 0=rotate, 1=shift with zero fill)
[9:0]   = SrcRow      (10 bits, but only low 6 used: row index added to RWC.SrcB)
```

```c
#define TT_OP_SHIFTXB(addr_mode, rot_shift, shift_row) \
    TT_OP(0x18, (((addr_mode) << 15) + ((rot_shift) << 10) + ((shift_row) << 0)))
```

**Functional model:**
```python
def SHIFTXB(addr_mode, shift_in_zero, src_row):
    # Wait for SrcB bank ownership
    while SrcB[MatrixUnit.SrcBBank].AllowedClient != MatrixUnit:
        wait()

    row = (src_row + RWC[CurrentThread].SrcB) & 0x3F
    bank = MatrixUnit.SrcBBank

    col0 = SrcB[bank][row][0]
    for col in range(15):
        SrcB[bank][row][col] = SrcB[bank][row][col + 1]
    SrcB[bank][row][15] = 0 if shift_in_zero else col0

    apply_addr_mod(addr_mode)
```

**Scheduling hazard:** After SHIFTXB, the Matrix Unit cannot accept any instruction on the next cycle. Hardware automatically inserts a 1-cycle stall.

**LLK usage:** Used primarily for debug — latching SrcB values to make them readable via the debug bus:
```c
// From ckernel_debug.h
TTI_SHIFTXB(ADDR_MOD_0, 0, row_addr >> 1);
```

**Performance:** 0.5 IPC, 2-cycle latency.


## Encoding Quick Reference

| Instruction | Opcode | Key Fields | Backend | IPC | Latency |
|---|---|---|---|---|---|
| CONV3S1 | 0x22 | clear_dvalid, rotate_weights, addr_mode, dst | Matrix Unit | 1 | 5 |
| CONV3S2 | 0x23 | (same as CONV3S1) | Matrix Unit | 1 | 5 |
| MPOOL3S1 | 0x24 | clear_dvalid, addr_mode, index_en, dst | Matrix Unit | 1 | 5 |
| APOOL3S1 | 0x25 | (same as MPOOL3S1) | Matrix Unit | 1 | 5 |
| DOTPV | 0x29 | clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst | Matrix Unit | 1 | 5 |
| MPOOL3S2 | 0x31 | (same as MPOOL3S1) | Matrix Unit | 1 | 5 |
| APOOL3S2 | 0x32 | (same as MPOOL3S1) | Matrix Unit | 1 | 5 |
| GAPOOL | 0x34 | clear_dvalid, instr_mod19, pool_addr_mode, max_pool_index_en, dst | Matrix Unit | 1 | 5 |
| GATESRCRST | 0x35 | reset_srcb_gate_control, reset_srca_gate_control | Matrix Unit | 1 | 1 |
| CLREXPHIST | 0x21 | (none) | Matrix Unit | 1 | 1 |
| SHIFTXA | 0x17 | Direction | Matrix Unit | 1 | 1 |
| SHIFTXB | 0x18 | addr_mode, ShiftInZero, SrcRow | Matrix Unit | 0.5 | 2 |


## Source References

| Source | Path |
|--------|------|
| MatrixUnit overview (WH) | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/MatrixUnit.md` |
| DOTPV ISA | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/DOTPV.md` |
| GAPOOL ISA | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/GAPOOL.md` |
| GATESRCRST ISA | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/GATESRCRST.md` |
| CLREXPHIST ISA | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/CLREXPHIST.md` |
| SHIFTXA ISA | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/SHIFTXA.md` |
| SHIFTXB ISA | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/SHIFTXB.md` |
| Blackhole C macros | `tt-llk/tt_llk_blackhole/common/inc/ckernel_ops.h` |
| Blackhole assembly YAML | `tt-llk/tt_llk_blackhole/instructions/assembly.yaml` |
| Reduce LLK (GAPOOL usage) | `tt-llk/tt_llk_blackhole/llk_lib/llk_math_reduce.h` |
| GAPOOL golden generator | `tt-llk/tests/python_tests/helpers/golden_generators.py` (ReduceGapoolGolden) |
| Python instruction encoders | `tt-exalens/ttexalens/hardware/blackhole/tensix_ops.py` |
| Instruction frequency data | `boop-docs/llk-sfpi/instruction-frequency-report.md` |
| Instruction set analysis | `boop-docs/llk-sfpi/blackhole-instruction-set-analysis.md` |
