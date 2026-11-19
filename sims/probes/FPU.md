# FPU (matrix unit) probes

Files: `fpu.py` (cases, setup programs, functional model, analysis), `k_fpu.c` (one generic TRISC kernel),
`fpu.h` (Tensix encodings, bounded fence, RISC Dst window, config RMW). Nothing here has run on hardware yet.

```
python3 sims/probes/run.py --device 1 --output sims/results/<date>-fpu-card1.jsonl fpu --list   # no card
python3 sims/probes/run.py --device 1 --output sims/results/<date>-fpu-card1.jsonl fpu -k tput-mvmul-lofi-bf16   # first
python3 sims/probes/run.py --device 1 --output sims/results/<date>-fpu-card1.jsonl fpu -k tput -k dep -k issue ...
python3 sims/probes/run.py --device 1 --output sims/results/<date>-fpu-card1.jsonl fpu            # everything
python3 sims/probes/fpu.py --list | --build | --disasm <case-id> [--role trisc0]                # no card
```

Suggested order (least to most risky): `tput-nop`, `tput-mvmul-lofi-bf16-dst32` (check its `check: ok`
before trusting anything else), the rest of `tput`, `dep`, `issue`, `data`, `src-flip`/`src-mvmul`, `mt`, and last
`src-handoff` (two threads that hand Src banks to each other; see Risks).

## What the llama kernels use (scope)

From `kernels/llama3-{1b,8b-bf16,8b-fp8}/*/trisc1.S` (math thread), MOP templates and replay records included:

| Instruction | Where | Pattern |
|---|---|---|
| MVMUL | attention only | LoFi (no FidelityIncr in its ADDR_MODs), bf16 Src, fp32 Dst; MOP inner 1/2 with LoopOp=REPLAY(16,8) and LoopOp1=REPLAY(24,8) of MVMULs (addr modes 0,1,2,4,5), EndOp SETRWC (clear_ab_vld 1 or 3) |
| ELWMUL | o, down, gate, lm, qkv | MOP outer 2 x inner 2, HiFi2 via ADDR_MOD FidelityIncr/Clear, last op clear_dvalid=3; fp32 Dst |
| ELWADD | o, down | MOP, dest_accum_en=0, after `Fp32_enabled=0` (16-bit bf16 Dst); EndOp SETRWC clear_ab_vld=3 |
| MOVA2D | gate, lm, qkv, attention (MOP, 8-row, addr_mode 2); argmax (16 direct) | fp8 kernels: FP16-style SrcA (Lf8/e4m3) into fp32 Dst |
| ZEROACC | every math/pack thread | per-face (mode 1, bit 18 set) x4, attention: all (mode 3) |
| SETRWC / INCRWC | everywhere | INCRWC dst+2 inside SFPU replays; SETRWC resets and bank releases |
| STALLWAIT SRCA_VLD/SRCB_VLD, SEMWAIT MATH_PACK | before MOPs / per tile | sync, not covered here (see "Not covered") |

Formats in scope (coordinator): Src bf16, e4m3 fp8 (FP16 style in Src), bfp8, bfp4 (BF16 style in Src); Dst fp32,
and fp16 Dst for the fp8 path. No TF32. The bf16 16-bit Dst appears once (ELWADD epilogue of o/down) and has one case.
Not used by llama, covered only by single throughput cases because the brief asked: GAPOOL, GMPOOL, ELWSUB, MOVB2D,
MOVD2A, MOVD2B, MOVB2A, ZEROSRC, MVMUL HiFi2-4.

## Method

One launch per case on tile (1,2). `k_fpu.c` runs per role:

1. **Setup program** (records in L1 at the role's LOG+0xC000, interpreted by the kernel, pushes with plain `sw`):
   bounded fence; config by RISC read-modify-write (ALU_FORMAT_SPEC Src A/B value+override, REG0/1/2, SFPU fp32,
   unpacker Out_data_format, the thread's RISC Dst-window format, `Zero_Flag_disabled_dst` during the fill);
   `DISABLE_IMPLIED_SRCA/B_FMT=1`; the RISC writes A into Dst16b rows 512..575 and B into 576..639 through the RISC Dst
   window (0xFFBD8000, Dst.md "RISCV access"); `UNPACR_NOP(zero, SetDvalid, WaitLikeUnpacr)` gives each Src bank to
   the matrix unit (one or both banks); `STALLWAIT(B6, C7|C8)`; 16 x MOVD2A + 16 x MOVD2B (4 rows each) copy A/B into
   SrcA/SrcB (second bank: flip with CLR_DVALID disabled, fill again, flip back); fence; switch to the case's Dst
   mode (fp32 or 16-bit); ADDR_MODs (slot 0 = no increments; 1 Dst+8; 2 Dst clear; 3 fidelity+1; 4 fidelity clear,
   unless the case overrides); SETRWC all; RISC zero-fills accumulator rows 0..127; MOP template / replay load; fence.
   The Src operands never come from the unpacker probes.
2. **Timed loop**: for n in (64, 128, 256), 8 samples (first = warmup): `t0 = now(); body_loop(n); t1 =
   tt_fence_time()`. `body_loop` is `for (;n;n--) { BODY }`, BODY = the case's words as inline `.ttinsn`
   (`-DBODY=TTINSN(..);...`), so the timed region is exactly those words plus `addi/bnez` (checked with
   `fpu.py --disasm`). `tt_fence_time` pushes `STALLWAIT(B1, C1|C2|C4|C11)` + `SEMPOST`, polls the semaphore from the
   RISC (bounded) and reads the wall clock as soon as it is seen. Fixed costs cancel in the slope.
3. **Check program**: fence, zero the accumulators, SETRWC, run the body `CHECK_ITERS=2` times, fence, read rows
   0,8,..,120 (cols 0 and 15) through the RISC Dst window. `fpu.py`'s functional model (Dst += 16ab per MVMUL with
   SrcA/SrcBFidelityBits per phase, ELW*, GAPOOL/GMPOOL, MOVA2D/MOVB2D, RWCs and ADDR_MODs, MOP and REPLAY expansion)
   predicts them. `check` = ok / MISMATCH / none; a mismatch is recorded, not raised.

Result record: per role `samples` (cycles per sample, by n), `medians` (warmup dropped), `slopes` (adjacent counts) and
`slope` (64 -> 256) in cycles per `unit` (the counted operation; stated per case), `dst`, `expected`, `check`;
`median` = trisc1 slope (what run.py prints). Two-thread cases add `union` (earliest start to latest end per sample).

Data: bf16 cases use A = 1 + 2^-5 (fidelity phase-1 bit) and B = 1 + 2^-7 (phase-2 bit), so the read-back shows which
phases ran (LoFi 16/op, HiFi2 16.5, HiFi3 16.625, HiFi4 16.62890625 per MVMUL); fp8 (FP16 style) 1.125 x 1.25 (0.125 x
0.125 for the fp16 Dst so 3584 accumulations stay finite); bfp8/bfp4 1.5 x 1.25.

## Case groups (103)

| Group | n | What | hw.py entries it fills |
|---|---|---|---|
| tput | 35 | 16 ops/iteration over 8 distinct 8x16 blocks (no Dst RAW), direct push: MVMUL LoFi x {bf16, bfp8, bfp4, fp8} fp32 Dst, fp8 fp16 Dst, HiFi2/3/4 phase-outer; ELWMUL LoFi bf16/fp8, HiFi2; ELWADD (=, +=, 16-bit Dst), ELWSUB; GAPOOL, GMPOOL; MOVA2D 8-row bf16/fp8->fp32/fp8->fp16, 1-row; MOVB2D 4-row, bcast8; MOVD2A, MOVD2B, MOVB2A; ZEROACC face/all/half/row; ZEROSRC; SETRWC, INCRWC, SETRWC bank flip; TT NOP | new `FPU_ISSUE[op]`; `FPU_LATENCY` (issue part) |
| dep | 36 | Same-block chains MVMUL n=1,2,3,4,5,6,8 blocks, ELWMUL 1,2,3,6, ELWADD+= 1,2,6, GAPOOL/GMPOOL 1; HiFi2/3/4 phase-inner; MOVA2D->MVMUL same/other rows; FPU->SFPLOAD same rows with g TTNOPs (MVMUL g=0,1,2,3,4,6; ELWMUL, MOVA2D g=0,3) with value check (row 256 = last SFPLOAD's L0); MVMUL+SFPLOAD other half; SFPSTORE->MVMUL same block (value) / other half; batch-8 MVMUL+SFPLOAD same/other half | `FPU_LATENCY` (=chain slope at n=1, or 6/n), new `FPU_DST_RAW`, `FPU_TO_SFPLOAD_GAP` (MVMUL, MOVA2D), `DST_HALF_SAME/OTHER` for MVMUL, new `SFPU_TO_FPU` |
| issue | 17 | One expanded stream S = 8 x MVMUL(Dst+8) + SETRWC issued as: direct, REPLAY(9), REPLAY len 1/2/4/8, MOP(inner 8, EndOp SETRWC), MOP then direct S (transition), MOP-of-REPLAY, MOP-of-REPLAY then direct, MOP alternating two REPLAYs (attention shape), the exact llama-o HiFi2 ELWMUL MOP + ADDR_MODs; loop overhead with 1,2,4,8,16 NOPs per iteration | `FRONTEND.mop_transition` (HINT -> MEAS), new `REPLAY_ISSUE`, `FRONTEND.loop_overhead_hidden` (small bodies) |
| src | 7 | MVMUL then SETRWC flip with data in both banks (k=1,4), MVMUL clear_dvalid=3 every op; two-thread handoff stream (trisc1 k MVMUL + SETRWC release, trisc0 UNPACR_NOP give, k=1,4,16); single-shot handoff latency (trisc0 gives 2000 cycles after trisc1 blocked; control = bank present) | new `SRC_FLIP`, `SRC_HANDOFF` (give -> dependent MVMUL done), cost of a release+give round trip |
| mt | 4 | trisc1 MVMUL stream + trisc0 SFPLOAD other half / same half / register SFPMAD / MVMUL (second thread on the FPU) | new `FPU_TWO_THREAD`, DST_HALF two-thread TODO |
| data | 4 | MVMUL / ELWMUL with zero Src (no MOVD2A) and pseudo-random bf16 Src vs the constant-data tput cases | data-independence assumption |

## Hypotheses and expected values

| Quantity | Expected | Source |
|---|---|---|
| MVMUL, ELWMUL, ELWADD/SUB, GAPOOL, GMPOOL independent issue | 1.0 cycle/op (per fidelity phase) | DOC MatrixUnit.md table; HINT boop-docs compute-only peak: 571,893 cycles for 571,851 fp16 MVMUL over 32 rotating blocks |
| Same 8x16 block, accumulate after accumulate | dependent op waits; chain slope ~6 at n=1, max(1, 6/n), 1.0 from n>=6 | DOC Dst.md ("next five cycles cannot be read ... at least six distinct blocks"); hw.py FPU_LATENCY=5 (DOC) |
| HiFi-n, phases inner on one block | ~ chain n=1 cost per op; phases outer: 1.0/op | DOC Dst.md (fidelity loop should be outer) |
| bf16 vs bfp8/bfp4 vs fp8 Src, fp32 vs fp16 Dst | no difference | assumption (Src style only changes the multiplier datapath) |
| MOVA2D/MOVB2D | 1.0/op; next MVMUL/ELWMUL/MOVD2x auto-stalls ~3 cycles regardless of rows | DOC MOVA2D.md / MOVB2D.md, MatrixUnit.md latency 4 |
| MOVD2A / MOVD2B streams | 1.0/op (only MOVD2A/B may follow within 2 / 3 cycles) | DOC MOVD2A.md, MOVD2B.md |
| ZEROACC, ZEROSRC, SETRWC, INCRWC | 1.0/op | DOC MatrixUnit.md |
| FPU -> SFPLOAD same rows | ELWMUL measured 8 cycles/pair at gap 0 and the load sees the new value (interlocked, not the ISA's 3 gap instructions); MVMUL expected the same | MEAS results/2026-11-18-sfpu-dst-card1.jsonl; hw.py FPU_TO_SFPLOAD_GAP, DST_HALF_SAME |
| FPU + SFPLOAD other half | 2.0/pair | MEAS DST_HALF_OTHER |
| batch 8 MVMUL + 8 SFPLOAD same half | 2 + 12/8 = 3.5/pair; other half 2/pair | MEAS (ELWMUL) DST_HALF_SAME formula; HINT fpu-sfpu-interleave.md says MVMUL behaves like ELWMUL |
| MOP -> non-MOP | +1 cycle per transition; none with a REPLAY inside the MOP, none MOP->MOP | DOC MOPExpander.md; hw.py FRONTEND.mop_transition HINT |
| REPLAY | 1/cycle out, no transition cost; short replays limited by RISC push rate (1 REPLAY per .ttinsn) | DOC REPLAY.md |
| Loop overhead | hidden once the body has >= ~4 ttinsn at 1 cycle each (fusion pushes 4/cycle); 1-2 NOP bodies show addi/bnez | MEAS hw.py loop_overhead_hidden (16 NOPs -> 1.000) |
| Src bank flip with data present | ~0 extra beyond the SETRWC issue slot | assumption |
| Two threads on the FPU | combined <= 1 op/cycle | DOC STALLWAIT C4 note (FPU shared) |
| zeros vs random Src | identical | assumption to test (power gating / zero skipping) |

## Risks (what could wedge the Tensix, and why it should not)

All RISC-side waits are bounded (`WAIT_UNTIL`, BUDGET polls): fences, barriers, handoff flags. A bounded wait that
gives up returns to firmware with `KernelTimeout` and its site; but if the Tensix thread itself is wedged, the
firmware's `tensix_drain` on return and any further push block for good, so the run stops with a HostTimeout and the
card needs a look (`smi.py -d`, reset by hand). No case uses SEMWAIT. The only Tensix-side blocking points are:

- **MVMUL/ELW*/GAPOOL/GMPOOL/MOVA2D/MOVB2D wait for Src dvalid.** In single-thread cases both operands were given
  by UNPACR_NOP in setup and are never released (CLR_DVALID disabled where the body flips), so the wait always holds.
  `STALLWAIT(B6, C7|C8)` in setup waits for the same give.
- **UNPACR_NOP waits for its bank to be Unpacker-owned.** `UNP_GIVE` sets WaitLikeUnpacr (Stall_Clr_Cntrl) so it waits
  on the unpacker's own bank (BH UNPACR_NOP.md). The old hardware-verified recipe had it clear and gave only one bank;
  with it clear, giving the second bank would wait on the matrix unit's (already given) bank, i.e. forever.
  **This bit setting is the least proven piece of setup; run `tput-setrwc-flip-noclear` (banks=2) early.**
- **src-handoff-* (two threads).** trisc1 releases banks (SETRWC clear_ab_vld=3) and blocks in MVMUL until trisc0
  gives a bank; trisc0's UNPACR_NOP blocks until trisc1 releases. Gives and releases are equal per sample by
  construction and both roles run the same sample schedule with a barrier per sample. If one role dies early (e.g. a
  bounded wait gives up), the other thread's Tensix stays blocked: hard failure. Run these last.
- **MOVB2A** 3 cycles after an arithmetic op is UB that corrupts the FPU queue (MOVB2A.md). Its case has no arithmetic,
  and setup ends with a fence.
- **Unpackers[0].WroteDst** (SrcA hand-over bug) carries across launches if an earlier kernel unpacked to Dst; the
  BH UNPACR_NOP form that clears and gives in one instruction avoids it (SrcASrcB.md).
- **REPLAY load** is pushed with plain `sw` (interpreter), never fused `.ttinsn` (PushTensixInstruction.md).
- Config is written by the RISC only after a fence; word 3 (ECC scrubber + RISC Dst window) and word 2 are
  read-modify-written. reset_tensix/reset_thread restore everything for the next launch.
- `Zero_Flag_disabled_dst` is set only while MOVD2A/B copy the RISC-written rows (so it works whether or not RISC
  writes set the Dst valid bits); the first move after the change is issued twice.
- MOVA2D fp8 into fp32 Dst: the value check may report MISMATCH (BH treats moved FP16 as TF32 per an old note); that
  is information about the conversion, not a broken setup.

## Not covered (follow-ups)

- Real unpacker-fed handoff (UNPACR latency, the unpacker probes' area); STALLWAIT C7/C8 and SEMWAIT MATH_PACK costs
  per tile; SETC16/RMWCIB + STALLWAIT(CFG) cost before each MOP; MOP_CFG writes + PC_BUF_MOP_SYNC from the RISC;
  DEST_TARGET_REG_CFG_MATH_Offset switches between tiles (gate/attention do one per tile).
- The attention MVMUL ADDR_MOD set (SrcA CR / +32, Dst CR) and its real SrcA layout; only its MOP/REPLAY shape is
  timed (`issue-mop-alt-replay`).
- The exact llama gate/qkv MOVA2D MOP (outer/inner counts) and SFPU replays driven by MOP (INCRWC in replay): SFPU agent.
- Packer-side fp16 Dst reads (fp8 output path): the packer probes.
- DOTPV, broadcast modes (ELW* SrcB row/col broadcast, MVMUL row broadcast), INT8 math.
