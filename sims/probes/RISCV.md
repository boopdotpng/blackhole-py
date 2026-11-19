# RISC-V core probes (riscv.py, k_riscv.c)

Status, 2026-11-18: written and checked offline, **not run yet** (the cards were busy). Every case builds for every
role it targets, and the bytes of every timed region match the case's asm exactly (`riscv.py --verify`).
No result in this file comes from hardware yet. Expected values are either old measurements (2026-09-09) or
hypotheses.

## Run

```sh
# everything (1203 cases, ordered old -> l1 -> store/fence/stld -> csr/timer/div -> branch -> mmio)
python3 sims/probes/run.py --device 0 --output sims/results/2026-11-18-riscv-card0.jsonl riscv
# one group at a time (ids carry the group prefix), e.g. the port of the old suite only, or the MMIO targets only
python3 sims/probes/run.py --device 0 --output sims/results/2026-11-18-riscv-card0.jsonl riscv -k -brisc   # one role
python3 sims/probes/run.py --device 0 --output sims/results/2026-11-18-riscv-mmio-card0.jsonl riscv -k mmio_
# offline (no card)
python3 sims/probes/riscv.py --verify [-k id-part]   # build + check that the timed bytes are exactly the asm
python3 sims/probes/riscv.py --disasm bp15-alt-trisc1
python3 sims/probes/riscv.py --summary
```

All cases run on tile (1, 2), one role per launch. Building all 1203 images takes about 12 s the first time;
after that they are cached. The longest kernel (divu_large) runs for about 2 ms, well inside the 0.25 s host
timeout.

## Method (same as the old tests/timing/test_instruction_timing.py)

- A fixed body (normally 16 ops) inside `90: BODY; addi a0,a0,-1; bnez a0,90b`, run at 64/128/256 iterations.
  For each point there is one warmup sample (cold I-cache, discarded) and then 7 measured samples. All 24 samples
  happen inside **one launch**, unlike the old harness, which launched once per sample.
- The timed region, exactly: `fence; lw t1,WALL_CLOCK_L; loop; FINISH; fence; lw t2,WALL_CLOCK_L`.
  FINISH stores the result register to a sink, so the last result must exist before the clock is read.
  `--verify` assembles this text on its own and checks that the image contains exactly those bytes, once. That
  covers all 1203 cases, so the compiler adds nothing to any timed region.
- The slope is the difference of adjacent medians divided by the difference in body ops. `slope` is the mean of the
  two adjacent slopes, and `per_iter = slope * ops`. The loop's own addi/bnez costs 2 cycles per iteration
  (0.125 per op with 16 ops; old `empty`), so a 1-cycle op shows as 1.125.
- Sink: each case declares the value a1 must hold after FINISH for each iteration count (an ALU result, the end of a
  pointer chain, a stored value read back, the count of not-taken branches, ...). It is checked on all 24 samples.
  A mismatch is printed and recorded as `sink_ok: false`.
- Every launch also logs cfg0 (at entry and while measuring), pmacfg0/1, misa and mstatus. `cfg0_ok` checks the
  bits that fw/hw.h `configure_csr` guarantees: DisLowCash (bit 3) clear (the firmware runs with the L0 data cache on since 019f79e); DisBp (bit 1) clear; DisTriscCache (bit 18)
  set on BRISC/NCRISC and clear on TRISCs. It also checks that the case's set/clear bits took effect.
- The cfg0 variants (L0 on, DisBp, DisCsrSync, BpHistSel, DisLdBufByp) apply for the whole launch. cfg0 is
  restored before returning. Writable MMIO words that firmware does not reset (NIU command buffer, overlay register)
  are saved and restored.
- The I-cache knee is above 128 instructions per loop (results/2026-11-18-icache-*). A lint stops any case whose
  loop plus tail exceeds 120 instructions. The largest is about 80 (`st-stride16-gap4`, the MMIO latency triples).
- Bodies use a1-a7, t3-t6, ra and f0-f5. The harness owns t0 (clock), t1/t2 (timestamps), a0 (count) and
  s11 (sink). A lint rejects writes to those registers and any use of sp/gp/tp/s0.

Caveat for every case: the RISCs that are not launched sit in firmware polling L1 (`wait8` with a fence). The old
harness had the same background, so the comparison is fair, but L1 latencies here are "with 1-4 idle pollers".

## Groups

Expected values: **old** = riscv-card0.jsonl / riscv-l0-enabled-card0.jsonl / context-card0.jsonl (card 0,
2026-09-09); **DOC** = tt-isa-documentation BlackholeA0/TensixTile/BabyRISCV/README.md; **HYP** = a hypothesis
this case tests. Each case's `expect` holds the value; `expect_ok` means within 3% (or 0.01).

### old (22 cases x 5 roles): fills hw.py RISCV alu/mul/div/fpu/csr/fence_empty/load_l1/store, and load_local
Ids, bodies and sinks are the old ones, so `case`+`role` matches riscv-card0.jsonl 1:1.

| case | body (x16) | old slope (all roles) | sink |
|---|---|---|---|
| empty | - | 0.125 | 3 |
| addi_dep / add_dep / xor_dep | dependent ALU | 1.125 | 3+16n / 3+16n / 3 |
| mul_dep | `mul a1,a1,a2` | 2.0625 (loop hidden by 1) | 3 |
| mul_ind4 | 4 independent chains | 1.125 | 3 |
| divu_one | `divu a1,a1,1` | 2.125 | 3 |
| divu_large / remu_large | 0xffffffff / 3 | 33.125 | 0x55555555 / 0 |
| fence | `fence` | 4.125 | 3 |
| csr_cycle | `csrrs a1,cycle,x0` | 4.125 | - |
| load_l1_hot_dep / _miss_dep | `lw a1,0(a1)`, ring of 1 / 8 lines | 8.0 / 8.0 | ring head |
| store_l1_same / _coalesced | `sw` same word / 4 words of a line | 1.125 | 3 |
| fadd_dep, fmul_dep, fmadd_dep | dependent `.s`, rne | 2.125 | float(1+16n) / 1.0 / 1.0 |
| fadd_ind4 | 4 chains | 1.125 | float(1+4n) |
| load_l1_{hot,miss}_dep-l0on | L0 data cache on (old TIMING_CLEAR_CFG0_BITS=0x8) | 2.130 / 8.0 | |
| local_load_dep | `lw a1,0(a1)` in own local RAM (old "context" case) | 2.0625 | |

Old medians are in `expect.medians`. Expect the intercept to be lower than the old one: the old harness launched
once per sample, so every sample started with a cold I-cache. The slopes should match. F is enabled on every role
(the old fp sinks were checked on all five). The kernels use `.option arch, +f` because fw builds rv32im_zicsr.

### l1 (38 x 5): fills load_l1 by width, L0 (hw.py RISCV note "L0 data cache is a separate question")
- `l1_ld-{lw,lh,lhu,lb,lbu}-o{off}[-l0on]`: `lX t3,off(a3); add a3,a3,t3` on zeroed memory, so each load's
  address depends on the previous load's data. Offsets: lw 0/4/12, lh 0/2/14, lb 0/1/15. Misaligned offsets are
  left out: with no trap handler a fault would hang the core. HYP: latency + 1 per op, so 9 with L0 off and
  3 with L0 on (DOC latencies 8 and 2), the same for every width.
- `l1_ldtput-{same,lines}[-l0on]`: 16 independent lw into 8 rotating destinations. HYP 1 per load (8 retire slots
  cover the 8-cycle latency).
- `l0_ring-n{N}-s{stride}`: dependent ring over N lines with the L0 on and its periodic flush off.
  DOC capacity is 4 x 16 B, so HYP 2 per load for N <= 4 and 8 for N > 4. Strides 64 and 1024 test the
  set mapping.
- `load_l1_*_dep-l0on-noflush`: the old L0 cases with DisLowCachePeriodicFlush set. HYP: the old 2.13 comes from
  the ~0.8% random flush and drops to 2.0625.
- `l0_store_inval`: `sw a2,4(a1); lw a1,0(a1)`. HYP: the store flushes the line, so every load misses (8).

### store / fence / stld (15 + 9 + 7 cases x 5): fills store, fence_empty, and new store-queue entries
- `st-*`: 16 stores per iteration. The stored value is the iteration count, read back as the sink. DOC model:
  stores that fill whole 16 B blocks run 1/cycle; otherwise one coalesced store every 5 cycles. Coalescing needs
  the same 16 B block and start addresses within +-4. So `seq64`, `rev64`, `seqbyte`, `seqhalf` should be 18
  cycles per iteration; `stride16/64/128` and `alt8` 82; `pairs16` (2 per block) 42. `stride16-gap{1,2,4}` adds
  k ALU ops per store and should stay 5 per store until k >= 5. `local-*`: 1/cycle. `mixed-l1-local`: the local
  stores should hide under the L1 queue.
- `fe-*`: a fence with work outstanding, `ops` = fences per iteration. One L1 store, 4 coalescible stores,
  4 strided stores, a local store, a NIU register store, a Tensix cfg store, an outstanding L1 load, and an
  outstanding wall-clock load. HYP: 4 plus the drain of whatever is outstanding. cfg0 StMergeTimer = 16 (bit 17
  set) may add up to 16 after an L1 store. `fence-nosync` sets DisCsrSync.
- `stld-bypass` / `-sameline`: a non-overlapping store before a dependent pointer-chase load. DOC: the load
  bypasses the store queue, so 8. `stld-overlap[-local]`: an overlapping store forces a drain.
  `ldbuf_bypass_off`: the bypass case with DisLdBufByp set.
- `amo_dep` (`amoadd.w a1,zero,(a1)` chain; DOC >= 12) and `amo_tput`. Kernels don't use AMOs, but they are
  cheap to measure.

### csr / timer / div (11 + 5 + 24 cases x 5): fills csr, div (operand-dependent model), and the timer overhead
- `csr_*`: reads of instret, mcycle, cfg0, misa, mhartid, fcsr, and tt_cfg_qstatus (TRISC only). Writes:
  `csrw_cfg1`, `csrrwi_cfg1` (0x7c3 is a scratch CSR). HYP 4 each, as the old csr_cycle. `csr_cycle-nosync`:
  DisCsrSync, HYP 1. `csr_cycle_alu`: does an ALU op after a CSR wait for the CSR to retire?
- `tm-pair-{none,dep,fence,csr}`: two wall-clock reads with nothing, a data dependency, a fence, or a CSR read
  between them. No loop; `median` is cycles. `tm-pair-dep` gives the wall-clock load latency directly (DOC >= 7
  for tile control). The load-use form is `mmio_lat-wallclock` and the back-to-back throughput is
  `mmio_ldtput-wallclock`. `tm-cycle_ratio`: mcycle over the wall clock (HYP 1.0).
- `divu_mag-b{k}`: dividend 2^k - 1, divisor 3. HYP max(6, k + 1); the old b32 = 33. `divu_dvsr-b{k}`: dividend
  0xffffffff with a varying divisor (HYP: no effect). Specials: divide by 0, INT_MIN/-1 (DOC 2), -1/3,
  (INT_MIN+1)/3, rem. `mulhu_dep` (HYP as mul).

### branch (70 x 5): fills branch_taken_ok, mispredict, and the hw.py TODO "branch predictor model"
- Straight-line forms, 16 per iteration: `br_taken_skip` (beq over one instruction), `br_taken_next`
  (taken to pc+4), `br_nottaken`, `jal_skip`, `jal_next`, `jalr_next` / `jalr_skip` (auipc + jalr). The skipped
  instruction is `addi a6,1`, so the sink counts not-taken paths. DOC: 1 cycle each when predicted, so 18 per
  iteration.
- `*-disbp` and `empty-disbp`: the same with cfg0 DisBp. HYP: static not-taken, so +4 per taken branch, the loop
  branch included. **This is the direct check of the DOC +4 mispredict penalty.** `empty-disbp` - `empty` = the
  penalty of one mispredicted loop branch.
- Direction patterns: `rori a5,a5,31` once per iteration, then `bltz a5` over an `addi a6`. Patterns: always,
  never, alt (period 2), p4, p4_1 (1 of 4 taken), p8, p8_1, p16, p32, p32_1, p32_31, rand32.
  `bp15-*` has 15 such branches per iteration, all seeing the same direction. `bp1-*` has one, plus 14 addi, so
  each mispredict shows as +4 per iteration directly. Expect = perfect prediction (18 + 15z or 18 + z cycles, z =
  not-taken fraction). The excess over expect / 4 = mispredicts per iteration. `bp1-{always,never,alt,p4}-disbp`
  and `bp15-{alt,p4,p8,rand32}-histsel{1,2,3}` (cfg0 BpHistSel, undocumented field) probe how history is used.
- `bp_inner-L{1,2,3,4,6,8,16}`: an inner loop of L iterations inside the timed loop. HYP: its exit is mispredicted
  once per entry (+4) unless the predictor learns the trip count.
- `call_ret_shared` (16 call sites to one leaf; its ret has 16 targets) vs `call_ret_private` (16 leaves, each with
  one target) vs `call_ret_one`. The Wormhole docs say there is no return-address stack, so HYP shared = 7 per
  call and private = 3.
- `bd_taken-k{1,2,4,8}` / `bd_nottaken-k*`: k of 16 slots are branches, the rest addi. Tests whether
  taken-branch density costs fetch bubbles (DOC: no).

### mmio (45 x roles where mapped): fills the hw.py TODO "MMIO load/store latency to CONFIG/PC_BUFFER/NOC regs"
Targets and DOC load latency:

| target | address | roles | DOC |
|---|---|---|---|
| wallclock | 0xFFB121F0 | all | >= 7 |
| niu0_id, niu1_id, niu0_status | NIU NODE_ID (NoC0/1), NIU_MST counter 0 | all | >= 7 |
| niu0_cmdbuf | NoC0 cmd buffer 3 TARG_LO (restored) | all | >= 7 |
| overlay | stream 39 reg 8 (a CB counter; restored, fw resets it) | all | >= 7 |
| tdma | 0xFFB11024 | B, T | >= 4 |
| cfg | Tensix config word 100 (fw zeroes it per launch) | B, T | >= 4 |
| gpr | Tensix GPR 63 (B: thread 0's) | B, T | >= 4 |
| pcbuf_sync, mop_sync | 0xFFE80004/8 (Manual TTSync, thread idle) | T | >= 3 |
| sem | Tensix semaphore 0 | T | >= 3 |
| local, local_slow | own local RAM fast / slow alias | all | 2 / >= 8 |
| l1 | scratch | all | 8 |

Forms:
- `mmio_lat-*`: `lw t3,0(a3); andi t4,t3,0; add a3,a3,t4`, so the next address depends on the data. Per op =
  latency + 2. Calibrate with `-local` (2 + 2) and `-l1` (8 + 2).
- `mmio_ldtput-*`: 16 independent loads. HYP max(1, latency/8) per load.
- `mmio_st-*`: 16 stores, read back after. DOC: 1/cycle outside L1. Also `mmio_st-instrn_buf` (TRISC `sw` of
  Tensix NOP), `mmio_st-ttinsn` (the same as fused `.ttinsn`), `mmio_st-instrn_buf-drain` (timed until the thread
  has executed them), and `mmio_st-pcbuf_sync` (discarded stores). The Tensix thread is drained before every
  sample.
- `mmio_rw-*`: `sw a1; lw a1; addi a1,1`, the write-then-readback pattern. The sink proves the readback saw the
  write.

## Not ported or not measured, and why
- The old **SFPU** half of test_instruction_timing.py and test_icache.py belong to other probes.
- **PCBuf B side, mailboxes, PCBuf FIFO pops on TRISC.** These loads block inside the memory subsystem until
  another core acts, so no WAIT_UNTIL can bound them. A missed partner would hang the tile. A two-role case would
  need the OverrideEn escape hatch to be safe.
- **Bursts of PC_BUF / semaphore loads.** The ISA documents a hang when a TRISC starts a second such load before the
  first returns. Those targets only have the dependent (`mmio_lat`) form.
- **Misaligned loads and stores.** No trap handler; behaviour is undocumented.
- **BRISC pushing to INSTRN_BUF.** It would push into thread T0 while TRISC0 sits in firmware. TRISC pushes cover
  the store path.
- **The TRISC2 vector unit.** Out of scope for the Llama kernels.
- **Load latency under L1 contention from NoC/unpack.** That needs a second agent's traffic; it stays a TODO in
  hw.py.
- Old-harness details that changed: one launch per case instead of per sample; the per-role scratch replaces the
  fixed SINK 0x70000; TIMING_CLEAR_CFG0_BITS became per-case `cfg0_set`/`cfg0_clear`; the "context" firmware hash
  became the cfg0/misa/mstatus header on every case.

## Reading results
Each jsonl line has `slope`, `per_iter`, `adjacent_slopes`, `points[].raw_cycles` (7 samples), `points[].warmup`,
`sink_ok`, `cfg0_ok`, `expect`, `expect_ok`, `loop_addr`, `image_sha256`, and the asm itself (`asm`), so each
record is its own experiment. Pair cases report `median` in cycles.
