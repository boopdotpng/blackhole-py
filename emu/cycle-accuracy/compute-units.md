# Compute units — cycle timing

Tensix Matrix Unit (FPU) and Vector Unit (SFPU). Both clock at AICLK = 1.35 GHz.

---

## 1. Matrix Unit (FPU)

Primary source: `WormholeB0/TensixTile/TensixCoprocessor/MatrixUnit.md` — Blackhole
inherits the µarch; BH README says the only delta is "higher clock speed." The
BH-specific hazard language is in `BlackholeA0/TensixTile/TensixCoprocessor/Dst.md`.

### Master table

`MatrixUnit.md:22-35`:

| Instruction(s) | IPC (instr/cycle) | Latency (cycles) |
|---|---|---|
| `MVMUL`, `DOTPV`, `GAPOOL`, `ELWMUL` | 1 (†) | 5 |
| `GMPOOL`, `ELWADD`, `ELWSUB` | 1 | 5 |
| `SETRWC`, `INCRWC`, `CLEARDVALID`, `CLREXPHIST`, `GATESRCRST` | 1 | 1 |
| `SHIFTXA`, `ZEROACC`, `ZEROSRC`, `TRNSPSRCB` | 1 | 1 |
| `SHIFTXB` | 0.5 | 2 |
| `MOVD2A` | 1 | 2 (‡) |
| `MOVA2D`, `MOVDBGA2D`, `MOVB2D`, `MOVB2A` | 1 | 4 (‡) |

> (†) If multiple fidelity phases are in use, one instruction per phase — effective IPC
> decreases with phase count.
> (‡) Only certain Matrix Unit instructions can be used to hide this latency; see the
> relevant instruction pages for details.

Matrix Unit accepts **1 instruction/cycle globally** (regardless of thread).

### Dst 4-cycle read-after-write hazard

`BlackholeA0/TensixTile/TensixCoprocessor/Dst.md:96-97`:
> "After issuing an instruction which writes to Dst, then for the next four cycles, the
> aligned 8x16 block of Dst containing that write cannot be read. If a thread presents a
> Matrix Unit (FPU) or PACR instruction which wants to read from that block, then
> hardware will automatically stall the thread for an appropriate number of cycles. In
> particular, for instructions which accumulate onto Dst (such as MVMUL, GAPOOL, DOTPV,
> GMPOOL, ELWMUL), software needs to be looping over at least five distinct 8x16 blocks
> of Dst to avoid being stalled."

**→ To sustain 1 IPC on accumulating instructions, loop over ≥ 5 distinct 8×16 Dst
blocks.**

### Instruction-specific scheduling restrictions

**MOVD2A** (`MOVD2A.md § Instruction scheduling`):
> "If MOVD2A is used, then on the next cycle, the only instructions that the Matrix
> Unit (FPU) can accept are MOVD2A and MOVB2A. If a thread presents any other Matrix
> Unit (FPU) instruction, then hardware will automatically stall the thread for one
> cycle."

**MOVD2B**: "After MOVD2B, the next 3 cycles
only accept another MOVD2B."

**MOVB2D**: "After MOVB2D, avoid reading the
written Dest region for 3 cycles."

**MOVB2A**: "After MOVB2A, the next cycle
only accepts MOVD2A or MOVB2A."

**SHIFTXB**:
> "After SHIFTXB, the Matrix Unit cannot accept any instruction on the next cycle.
> Hardware automatically inserts a 1-cycle stall."

### Operand loads

SrcA / SrcB loads are governed by the unpacker pipeline, not a fixed FPU number. The
Wait Gate blocks the FPU instruction until `SrcA[bank].AllowedClient == MatrixUnit` AND
`SrcB[bank].AllowedClient == MatrixUnit`. MOVD2A is the exception — it has **no
auto-wait**; software must use `STALLWAIT(STALL_MATH, SRCA_VLD)`.

### SETDVALID

Dispatched by the **Miscellaneous Unit**, not the Matrix Unit (confirmed by
`SETDVALID.md` and the absence of a B6/STALL_MATH bit for it in `STALLWAIT.md`).
Effectively 1 cycle; no documented latency from issue to FPU seeing the bank flip.

### Fidelity phases (format-dependent cost)

IPC is always 1 regardless of format; format only changes the **number of fidelity
phases** required. 
| Format | Phases for full precision |
|---|---|
| BF16 (7-bit mantissa) | LoFi=1, HiFi2=2, HiFi3=3, HiFi4=4 |
| TF32 / FP16 (10-bit mantissa) | HiFi4 (4 passes) |
| INT8 (arbitrary) | 4 phases; 2 if inputs massaged to fp form |

FP32 Dst accumulation (`ALU_ACC_CTRL_Fp32_enabled=1`) and INT8 math
(`ALU_ACC_CTRL_INT8_math_enabled=1`) both select Dst32b mode. No per-instruction cycle
cost change is documented for these modes.

### Matrix Unit throttle levels (BH LLK)

`tt-llk/tt_llk_blackhole/llk_lib/llk_math_matmul.h:499-510`:
> "Valid range of THROTTLE_LEVEL is {1,2,3,4,5}. Each value corresponds to:
> Level 1: 73% of max / Level 2: 67% / Level 3: 50% / Level 4: 40% / Level 5: 33%"

Throttling is implemented as `TTI_NOP` insertions between MVMULs in the replay buffer.

### Spec vs. hardware mismatch to be aware of

The emulator pipeline spec lists opcode **0x58** as "MATMUL" (a Matrix Unit op), but
`tt-llk/tt_llk_blackhole/common/inc/ckernel_ops.h:15` maps `0x58 = TT_OP_ADDDMAREG`
(Scalar Unit). No BH ISA doc describes a separate `MATMUL` or `MVMUL_B`. This looks
like a mislabeled row in the emulator's pipeline table. **TRNSPSRCA** also does not
exist — WH/BH have only `TRNSPSRCB`.

### Performance counter to use

`tt-llk/docs/performance_counters/performance_counters.md` has `AVAILABLE_MATH`
(available cycles for math to issue) and a corresponding busy counter. Use these to
measure Dst-hazard stalls and effective IPC.

### Needs microbenching (Matrix Unit)

1. **BH Matrix Unit absolute clock.** TFLOP/s in the docs are normalized to WH's
   1 GHz. Run long MVMUL loop (≥5 distinct Dst blocks) and divide `mcycle` by count
   to confirm 1.35 GHz.
2. **MOVD2A 2-cycle latency — which instructions hide it?** Docs say "certain"
   without listing them. Bench `MOVD2A` → `MVMUL` (dependent) with 0/1/2 NOPs.
3. **MOVD2B 3-cycle post-issue restriction confirmation on BH** (spec derives from
   WH).
4. **ZEROSRC visibility to next-cycle MVMUL** (ZEROSRC is 1-cycle latency in the
   table, but whether SrcA is visibly zero on the next cycle is not stated).
5. **TRNSPSRCA existence / timing** on BH (not in `ckernel_ops.h`; probably doesn't
   exist, but confirm by opcode probe).
6. **Opcode 0x58 (MATMUL vs. ADDDMAREG)** — disambiguate which backend unit fires.
7. **SETDVALID → FPU bank-flip visibility latency.** Minimal loop: SETDVALID → MVMUL;
   count Wait Gate stall cycles.
8. **FP32 Dst (Dst32b) vs. BF16 Dst per-instruction cost** — confirm no change.
9. **INT8 fidelity-phase behavior on BH** (confirm WH's 4 / 2 phase rule inherits).
10. **GAPOOL 4-row vs. 8-row Dst hazard.** Two back-to-back GAPOOLs writing different
    4-row halves of the same 8-row block — does the 4-cycle blackout fire?

---

## 2. Vector Unit (SFPU)

Source: `BlackholeA0/TensixTile/TensixCoprocessor/VectorUnit.md:13-103`.
Clock: **1.35 GHz** explicitly (`VectorUnit.md:6`: "It also clocks at 1.35 GHz rather
than 1 GHz").

All SFPU instructions: **IPC = 1**. Latency splits into two groups.

### 2-cycle latency (MAD sub-unit)

| Instruction | Notes |
|---|---|
| `SFPADDI`, `SFPADD`, `SFPMAD`, `SFPMUL`, `SFPMULI` | |
| `SFPLUT`, `SFPLUTFP32` | |
| `SFPMUL24` (all modes) | BH-only |
| `SFPSWAP` (min/max, rotate/shift-lane) | IPC ≤ 1 |
| `SFPSHFT2` (rotate / shift-lane append modes) | IPC ≤ 1 |

`SFPMAD.md:70` hazard:
> "hardware will ensure that on the next cycle, the Vector Unit (SFPU) does not execute
> an instruction which reads from any location written to by the SFPMAD ... hardware
> will automatically stall the thread for one cycle."

### 1-cycle latency (everything else)

`SFPMOV`, `SFPSETSGN`, `SFPABS`, `SFPARECIP`, `SFPGT`, `SFPLE`, `SFPLZ`, `SFPSETCC`,
`SFPDIVP2`, `SFPSETEXP`, `SFPSETMAN`, `SFPEXMAN`, `SFPEXEXP`, `SFPIADD`, all `SFPSTOCHRND`
variants, all `SFPCAST` variants, `SFPLOADI`, `SFPLOAD`, `SFPSTORE`, `SFPAND`, `SFPOR`,
`SFPXOR`, `SFPNOT`, `SFPSHFT` (lanewise), `SFPSHFT2` (shift-4-LReg), `SFPENCC`, `SFPPUSHC`,
`SFPCOMPC`, `SFPPOPC`, `SFPCONFIG` (LReg-write mode), `SFPTRANSP`, `SFPNOP`.

**`SFPLOADMACRO`**: latency listed as **"Complex"** in the table (see § 2.3).
**`SFPCONFIG`** in LaneConfig / LoadMacroConfig mode: latency ≤ 2 (see control-plane doc).

### SFPLOAD vs. FPU Dst read hazard

`SFPLOAD.md:216`:
> "At least three unrelated Tensix instructions need to execute after a Matrix Unit
> (FPU) instruction which writes (or accumulates) to Dst and an SFPLOAD instruction
> which wants to read that same region of Dst."

Same 3-instruction rule applies to SFPLOADMACRO.


### GCC scheduler classification (cross-check)

`sfpi/gcc/gcc/config/riscv/tt/rvtt.md` has an `xtt_delay_bh` attribute per SFPU
instruction:

| `xtt_delay_bh` | Meaning | Examples |
|---|---|---|
| `"dynamic"` | Insert 1 NOP only if next op reads the written LReg | `SFPMUL`, `SFPADD`, `SFPMAD`, `SFPADDI`, `SFPMULI`, `SFPLUT`, `SFPLUTFP32_*`, `SFPMUL24` (BH-only) |
| `"static"` | Always insert 1 NOP after | `SFPSWAP` (all variants), `SFPSHFT2` sub-vec modes |
| `"none"` (default) | No NOP needed | `SFPNOP`, `SFPLOAD`, `SFPSTORE`, `SFPLOADI`, `SFPIADD`, `SFPMOV`, unary ops, logical ops, `SFPSTOCHRND_v`, `SFPCONFIG` (most), `SFPARECIP`, `SFPGT`, `SFPLE` |

Consistent with the ISA table: "dynamic" = 2-cycle latency (1 NOP if dependent);
"none" = 1-cycle.

### SFPLOADMACRO sub-unit structure

`SFPLOADMACRO.md:3-13`:
> "The Vector Unit (SFPU) is capable of executing up to five instructions per cycle:
> one load-style instruction (SFPLOAD or SFPLOADI or SFPLOADMACRO or SFPNOP), and then
> one instruction from each of the above four columns."

Sub-units: **Load, Simple, MAD, Round, Store**. When SFPLOADMACRO fires, all four of
Simple/MAD/Round/Store can retire in parallel with the Load. Auto-stalling is
disabled during a macro sequence; 
> "None of the SFPU auto-stalling applies to instructions executed as part of an
> SFPLOADMACRO sequence; programmer must ensure correct ordering via delays."

### Needs microbenching (SFPU)

1. **Hardware behavior on back-to-back dependent 2-cycle op.** GCC always inserts the
   NOP. Does hardware auto-stall, silently corrupt, or trap if the NOP is omitted?
   (Important — determines whether the emulator must silently insert stalls.)
2. **SFPCONFIG LaneConfig exact cycles** (1 or 2 — spec says ≤ 2). Bench: write
   config then read-back dependent.
3. **SFPSWAP cross-sub-unit blocking in macro context.** `SFPLOADMACRO.md` says if
   SFPSWAP is scheduled to Simple, then Simple+Round need idle/NOP on the next cycle.
   Quantify this as cycle delta.
4. **LReg read/write port count and bypass network.** Not published — matters for
   modeling SFPMAD back-to-back. Probably needs RTL review, not a microbench.
5. **SFPARECIP truly 1-cycle?** Surprising for an approximate-reciprocal unit;
   confirm.
6. **SFPLOADMACRO sequence timing.** ISA marks it "Complex" with no number. Measure
   macro issue → write-back visible latency for typical macros.
