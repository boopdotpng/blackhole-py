# SFPLOADMACRO and SFPTRANSP

Two SFPU instructions that are mentioned in the existing sfpu-operations.md but lack full functional models there. SFPLOADMACRO enables concurrent sub-unit execution (IPC > 1); SFPTRANSP performs cross-lane data movement for row-wise reduction and transpose operations.


## SFPLOADMACRO — Load from Dst + Schedule Pipelined Ops (opcode 0x93)

### Overview

SFPLOADMACRO is the **only mechanism** for achieving IPC > 1 on the Vector Unit (SFPU). It first executes an SFPLOAD (Dst → LReg), then schedules up to four additional instructions — one per sub-unit (Simple, MAD, Round, Store) — at configurable future cycle delays. The scheduled instructions and their timing are programmed ahead of time into a per-lane `LoadMacroConfig` table via SFPCONFIG.

Used in high-throughput SFPU kernels: fast exponential, reciprocal, typecast/format conversion, reduce, and SDPA. Appears 60 times across 747 Blackhole ELFs.

### Encoding

```
[31:24] = 0x93
[23:20] = lreg_ind       (4 bits — VDHi[1] : MacroIndex[2] : VDLo[2], packed)
[19:16] = instr_mod0      (4 bits — Mod0, passed to scheduled SFPSTORE)
[15:13] = sfpu_addr_mode  (3 bits — AddrMod, BH; 2 bits on WH at [15:14])
[12:0]  = dest_reg_addr   (13 bits — Imm9[9] : VDHi[1], packed; BH; 14 bits on WH)
```

```c
// Blackhole
#define TT_OP_SFPLOADMACRO(lreg_ind, instr_mod0, sfpu_addr_mode, dest_reg_addr) \
    TT_OP(0x93, (((lreg_ind) << 20) + ((instr_mod0) << 16) + \
                  ((sfpu_addr_mode) << 13) + ((dest_reg_addr) << 0)))
```

**Blackhole vs Wormhole encoding difference:** `sfpu_addr_mode` is 3 bits at bit 13 on Blackhole, 2 bits at bit 14 on Wormhole. `dest_reg_addr` is correspondingly 13 bits (BH) vs 14 bits (WH).

### Syntax

The macro arguments pack multiple logical fields:

```c
TT_SFPLOADMACRO(
    ((MacroIndex << 2) | VDLo),     // lreg_ind: macro selector + low 2 bits of VD
    Mod0,                            // instr_mod0: passed through to scheduled SFPSTORE
    AddrMod,                         // sfpu_addr_mode: address mode for SFPLOAD part
    ((Imm9 << 1) | VDHi)            // dest_reg_addr: Dst row address + high bit of VD
)
```

Where `VD = (VDHi << 2) | VDLo` selects the destination LReg (0–7 for LReg[0..7]).

### LoadMacroConfig State

Programmed via SFPCONFIG before SFPLOADMACRO is used. Per-lane state:

```python
class LoadMacroConfig:
    class Misc:
        StoreMod0: int           # 4 bits — default Mod0 for SFPSTORE
        UsesLoadMod0ForStore: int  # 4 bits — 1 bit per macro index
        UnitDelayKind: int       # 4 bits — 1 bit per sub-unit

    Sequence: list[int]          # 4 entries (one per macro index), 32 bits each
                                 # = 8 bits per sub-unit: [7] VB/VC select,
                                 #   [6] use LReg[16], [5:3] delay, [2:0] instruction selector

    InstructionTemplate: list[int]  # 4 arbitrary SFPU instruction words
```

### Sub-Unit Scheduling

SFPLOADMACRO can schedule one instruction per sub-unit:

| Sub-unit | Eligible instructions |
|----------|----------------------|
| Simple | SFPABS, SFPAND, SFPARECIP, SFPCAST, SFPCOMPC, SFPCONFIG, SFPDIVP2, SFPENCC, SFPEXEXP, SFPEXMAN, SFPGT, SFPIADD, SFPLE, SFPLZ, SFPMOV, SFPNOP, SFPNOT, SFPOR, SFPPOPC, SFPPUSHC, SFPSETCC, SFPSETEXP, SFPSETMAN, SFPSETSGN, SFPSHFT, SFPSWAP, SFPTRANSP, SFPXOR |
| MAD | SFPADD, SFPADDI, SFPLUT, SFPLUTFP32, SFPMAD, SFPMUL, SFPMULI, SFPMUL24, SFPNOP |
| Round | SFPNOP, SFPSHFT2, SFPSTOCHRND |
| Store | SFPSTORE |

### Functional Model

```python
def SFPLOADMACRO(macro_index, vd, mod0, addr_mod, imm9):
    # 1. Execute SFPLOAD: move Dst → LReg[vd]
    SFPLOAD(vd, mod0=0, addr_mod=addr_mod, imm10=(imm9 << 1) | (vd >> 2))

    # 2. For each sub-unit, schedule a future instruction
    for i, sub_unit in enumerate([Simple, MAD, Round, Store]):
        seq_bits = LoadMacroConfig[Lane].Sequence[macro_index] >> (i * 8)
        seq_byte = seq_bits & 0xFF
        delay = (seq_byte >> 3) & 7
        selector = seq_byte & 7

        if selector == 0:
            continue                # no instruction for this sub-unit
        elif selector == 2:
            insn = SFPNOP
        elif selector == 3:
            insn = SFPSTORE(vd=0)
        elif selector in (4, 5, 6, 7):
            insn = parse(LoadMacroConfig[Lane].InstructionTemplate[selector - 4])
        else:
            raise UndefinedBehaviour()

        # Override VD, VB/VC based on sequence bits [7:6]
        if i != 3:  # Simple, MAD, Round
            if seq_byte & 0x80:
                insn.VB = vd        # input comes from just-loaded LReg
            else:
                insn.VC = vd
            insn.VD = 16 if (seq_byte & 0x40) else vd  # LReg[16] is macro-only
        else:       # Store
            if seq_byte & 0x40:
                insn.VD = 16        # read from LReg[16]
            elif not (seq_byte & 0x80):
                insn.VD = vd
            # Store uses Mod0 from SFPLOADMACRO or from Misc.StoreMod0
            if LoadMacroConfig[Lane].Misc.UsesLoadMod0ForStore & (1 << macro_index):
                insn.Mod0 = mod0
            else:
                insn.Mod0 = LoadMacroConfig[Lane].Misc.StoreMod0

        # Forget any pre-existing scheduled instruction at this delay slot
        if delay != 7:
            sub_unit.forget_future_instruction(delay)

        # Schedule for future execution
        delay_kind = (WaitForElapsedInstructions
                      if LoadMacroConfig[Lane].Misc.UnitDelayKind & (1 << i)
                      else WaitForElapsedCycles)
        sub_unit.schedule(insn, delay, delay_kind)
```

### LReg[16] — Macro-Only Bonus Register

`LReg[16]` is a 17th LReg accessible only through SFPLOADMACRO:
- **Writable** only by instructions scheduled via SFPLOADMACRO (when `seq_byte & 0x40` sets `VD = 16`)
- **Readable** only by SFPSTORE scheduled via SFPLOADMACRO (when `seq_byte & 0x40` sets `VD = 16`)

This enables pipeline-style computations where an intermediate result is stored in LReg[16] and consumed by a later SFPSTORE, without conflicting with general-purpose LReg[0..7].

### Delay Counting

- Delay of 0: executes on the cycle immediately after SFPLOADMACRO
- Delay > 0: counts down, executes one cycle after reaching 0
- `WaitForElapsedCycles`: delay decrements every cycle
- `WaitForElapsedInstructions`: delay decrements each time any thread issues an SFPU instruction (all sub-units' delays decrement together)

### Scheduling Constraints

1. At least **3 unrelated Tensix instructions** must execute between a Matrix Unit (FPU) write to Dst and an SFPLOADMACRO that reads the same Dst region. Use NOPs or STALLWAIT(B8, C7) if needed.
2. **None of the SFPU auto-stalling** applies to instructions executed as part of an SFPLOADMACRO sequence. The programmer must ensure correct ordering via delays.
3. If a scheduled instruction arrives at a sub-unit on the same cycle as a regular SFPU instruction, the scheduled instruction takes priority and the regular instruction is silently discarded.

### Real Usage Example (fast reciprocal)

```c
// From ckernel_sfpu_recip.h — _calculate_reciprocal_fast_7b_
// Sequence[0] schedules: SFPARECIP (Simple) + SFPSTORE (Store), both at delay 0
// Result: 1 cycle per 32 lanes for approximate reciprocal

TTI_SFPLOADMACRO((0 << 2) | 0, 0, ADDR_MOD_6, 0);  // load row 0, macro 0
TTI_SFPLOADMACRO((0 << 2) | 1, 0, ADDR_MOD_6, 0);  // load row 1, macro 0
// ... 8 calls total to process all rows
```

### Performance

Latency: 1 cycle for the load itself. The scheduled instructions execute at their programmed delays. When properly pipelined, SFPLOADMACRO achieves the highest SFPU throughput — e.g., 1 cycle per 32-element row for reciprocal, vs. 4+ cycles with serial SFPLOAD/SFPARECIP/SFPSTORE.


## SFPTRANSP — Cross-Lane Transpose (opcode 0x8C)

### Overview

SFPTRANSP performs a 4×4 transpose within the lane layout of LRegs. It operates on two independent groups: LReg[0..3] and LReg[4..7]. Each group of 4 registers is stacked vertically to form a 16×8 grid, then within each of the 8 columns, the 16 values are reshaped to a 4×4 matrix and transposed.

This is **not** a simple 2D matrix transpose. It swaps the two leftmost axes of a 4×4×8 tensor (the register index axis and the row-within-register axis), leaving the column axis unchanged.

Used in reduce, cumsum, topk, reshuffle, EMA, and Welford's kernels. Appears 546 times across Wormhole ELFs.

### Encoding

```
[31:24] = 0x8C
[15:12] = imm12_math  (overlaps, typically 0)
[11:8]  = lreg_c      (typically 0)
[7:4]   = lreg_dest   (VD — must be < 12 or DISABLE_BACKDOOR_LOAD must be set)
[3:0]   = instr_mod1  (typically 0)
```

```c
#define TT_OP_SFPTRANSP(imm12_math, lreg_c, lreg_dest, instr_mod1) \
    TT_OP(0x8c, (((imm12_math) << 12) + ((lreg_c) << 8) + \
                  ((lreg_dest) << 4) + ((instr_mod1) << 0)))
```

**Typical invocation:** `TTI_SFPTRANSP(0, 0, 0, 0)` — all arguments zero.

### Functional Model

```python
def SFPTRANSP(VD):
    if VD < 12 or LaneConfig.DISABLE_BACKDOOR_LOAD:
        Transpose4(0)   # transpose LReg[0..3]
        Transpose4(4)   # transpose LReg[4..7]

def Transpose4(base):
    """Within each of the 8 columns, treat the 4 registers as a 4×4 matrix and transpose it."""
    for column in range(8):
        for i in range(4):
            for j in range(i):
                # Lane indices: register `base+i`, lane `j*8 + column`
                #           and register `base+j`, lane `i*8 + column`
                ij = LReg[base + i][j * 8 + column]
                ji = LReg[base + j][i * 8 + column]
                if LaneEnabled[j * 8 + column]:
                    LReg[base + i][j * 8 + column] = ji
                if LaneEnabled[i * 8 + column]:
                    LReg[base + j][i * 8 + column] = ij
```

### Data Movement Diagram

Each LReg has 32 lanes, viewed as a 4×8 grid (4 rows × 8 columns):

```
Before SFPTRANSP:               After SFPTRANSP:
LReg[0]: row0 of each column    LReg[0]: col0 of the 4×4 from each column
LReg[1]: row1 of each column    LReg[1]: col1
LReg[2]: row2 of each column    LReg[2]: col2
LReg[3]: row3 of each column    LReg[3]: col3

(same for LReg[4..7], independently)
```

Concretely, for column `c` (0–7), the 4 values at `LReg[0..3][row * 8 + c]` form a 4-element vector `[v0, v1, v2, v3]`. SFPTRANSP swaps `LReg[i][j*8+c]` with `LReg[j][i*8+c]` for all `i > j`, which is the standard 4×4 in-place transpose.

### Usage Pattern: Double-Transpose Idiom

SFPTRANSP is typically called in pairs — transpose in, do row-wise operations, transpose back:

```c
// From ckernel_sfpu_reduce.h
TTI_SFPTRANSP(0, 0, 0, 0);     // Transpose: now each LReg holds one "column" of the original layout
lltt::replay(0, replay_len);    // Row-wise operations (e.g., column-wise sum via row adds)
TTI_SFPTRANSP(0, 0, 0, 0);     // Transpose back to original register layout
lltt::replay(0, replay_len);    // Continue with row-wise layout
```

### SFPI High-Level API

The SFPI C++ library wraps SFPTRANSP as `subvec_transp`:

```cpp
// From sfpi/include/sfpi_lib.h
sfpi_inline void subvec_transp(vFloat& a, vFloat& b, vFloat& c, vFloat& d) {
    auto r = __builtin_rvtt_sfptransp(a.get(), b.get(), c.get(), d.get());
    a = vFloat(__builtin_rvtt_sfpselect4(r, 0));
    b = vFloat(__builtin_rvtt_sfpselect4(r, 1));
    c = vFloat(__builtin_rvtt_sfpselect4(r, 2));
    d = vFloat(__builtin_rvtt_sfpselect4(r, 3));
}
```

### Emulator Implementation

SFPTRANSP is straightforward to emulate — it is a pure in-place data shuffle with no arithmetic:

```python
def emulate_sfptransp(lregs):
    for base in (0, 4):
        for col in range(8):
            for i in range(4):
                for j in range(i):
                    lane_ij = j * 8 + col
                    lane_ji = i * 8 + col
                    lregs[base + i][lane_ij], lregs[base + j][lane_ji] = \
                        lregs[base + j][lane_ji], lregs[base + i][lane_ij]
```

### Performance

Latency: 1 cycle. Throughput: 1 IPC. Sub-unit: Simple.


## Source References

| Source | Path |
|--------|------|
| SFPLOADMACRO ISA (BH) | `tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPLOADMACRO.md` |
| SFPLOADMACRO ISA (WH) | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/SFPLOADMACRO.md` |
| SFPTRANSP ISA (BH) | `tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPTRANSP.md` |
| SFPTRANSP ISA (WH) | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/SFPTRANSP.md` |
| SFPI library | `sfpi/include/sfpi_lib.h` |
| SFPI MLIR dialect | `tt-mlir/include/ttmlir/Dialect/SFPI/IR/SFPIOps.td` |
| Blackhole C macros | `tt-llk/tt_llk_blackhole/common/inc/ckernel_ops.h` |
| Fast exp kernel | `tt-llk/tt_llk_blackhole/common/inc/sfpu/ckernel_sfpu_exp.h` |
| Fast reciprocal kernel | `tt-llk/tt_llk_blackhole/common/inc/sfpu/ckernel_sfpu_recip.h` |
| Typecast kernel | `tt-llk/tt_llk_blackhole/common/inc/sfpu/ckernel_sfpu_typecast.h` |
| Reduce kernel | `tt-llk/tt_llk_blackhole/common/inc/sfpu/ckernel_sfpu_reduce.h` |
| Cumsum kernel | `tt-llk/tt_llk_blackhole/common/inc/sfpu/ckernel_sfpu_cumsum.h` |
| SFPI test (SFPTRANSP) | `tinygrad/.../ckernel_sfpi.h` (test15) |
