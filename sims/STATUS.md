# Blackhole timing measurements and validation (2026-11-19)

The target is ±3% for each tile and participating RISC. Current validation uses card 0, the boot-only Tensix reset firmware, and hardware medians. The simulator reports the interval from kernel entry through its firmware return. [Checkpoint-backed results](#card-0-checkpoint-backed-decode-intervals)

## Simulator speed: poll sleeping and trip-count sampling

The timing rules are unchanged. Three changes make the simulator cheaper to run:

- **RISC run-ahead.** A RISC executes register and private-memory instructions ahead of the global clock. It waits for the clock only at an L1, MMIO or semaphore access. Tensix pushes carry the cycle they were issued, so a TRISC waits for the clock only when its FIFO may be full.
- **Poll sleeping.** A loop iteration that stores nothing and leaves every register unchanged is a poll. The RISC sleeps until the NoC counter, CB register or semaphore it read changes. It is then charged the skipped iterations at the measured loop period.
- **Trip-count sampling.** The compiler records the `shared` values that bound runtime loops and where each role's prelude leaves them (`Kernel.timing`). For long kernels the simulator runs twice in parallel, with those counts scaled to about 32 and 64 iterations. It then extrapolates each tile and RISC linearly to the real count.

On the unsampled 1B kernels, the two engines differ by a median 0.4–0.5% per interval, from event tie order and the arbitration random stream. In the stamped-push and semaphore-wake changes, results were identical bit for bit. Sampled and full runs of 8B BF16 gate differ by a median 0.32% (worst 1.64%). LM head has 528/528 intervals within 3% either way.

Card 0 decode captures, kernels rebuilt from source (images identical to the capture, argmax uses the captured image). Wall times use one process per kernel and two for the sampled runs. The previous column is from [the replay timing table](results/2026-11-19-ttrv-replay-time.md), which ran nine jobs at once on a loaded host. Sequential runs of the old engine took 10 s for 1B O and 16 s for QKV.

| Kernel | 1B before | 1B now | 1B within 3% | 8B BF16 before | 8B BF16 now | 8B BF16 within 3% |
|---|---:|---:|---:|---:|---:|---:|
| embedding | 0.1 s | 0.0 s | 2/2 | 0.1 s | 0.0 s | 2/2 |
| qkv | 31 s | 11 s | 143/528 | 2 min 09 s | 39 s | 422/528 |
| attention | 1.1 s | 0.3 s | 188/384 | 1.7 s | 0.5 s | 170/384 |
| o | 20 s | 7.2 s | 269/528 | 1 min 17 s | 25 s | 447/528 |
| gate | 2 min 19 s | 39 s | 474/528 | 6 min 50 s | 46 s (sampled) | 258/528 |
| down | 1 min 20 s | 24 s | 198/528 | 3 min 53 s | 82 s | 510/528 |
| lm | > 15 min | 20 s (sampled) | 528/528 | > 15 min | 36 s (sampled) | 528/528 |
| argmax | 1.5 s | 0.6 s | 242/440 | 1.5 s | 0.6 s | 236/440 |

What remains is the cost of simulating each Tensix instruction in the iterations that do run (about 2 µs each in CPython). That cost bounds gate and down, whose trip counts (93 to 163) are too short to sample much.

## Where the remaining error is (card 0, 2026-11-19)

In the DRAM-bound projections all five RISCs on a tile share one error, so the error lies in when the weight reads complete. It varies with the tile's row. On 1B QKV it runs from −7.7% (row 3) to +3.2% (row 11). 8B gate is +6–8% on rows 2–6 and about 0 on rows 7–11.

The stream probe (`probes/stream.py`) isolates that read stream, with BRISC only and the projections' addressing:

| Probe | Hardware vs simulator |
|---|---|
| 1 to 88 readers on one bank (`bank0-N`) | aggregate rate and per-tile medians within about 1% (46.5 vs 46.2 B/c at 88). The bank model is right. |
| 88 workers × 48 rows, 4 KiB rows | 84/88 within 3%, median −0.5% |
| 88 workers × 16 / 8 / 4 rows | −2.5% / −8.5% / −11.7% median. Hardware is slower by about 1,000 cycles at 4–8 rows, 440 at 16 and 215 at 48. |
| 88 workers × 1 row | median right, but column x = 10 is 25% slow in the model and columns 1–4 are fast |

When every worker starts on the same bank pair, hardware pays a start-up cost the model lacks, and pays it most on rows 2–5. None of these closes that gap without breaking the cases that already pass: router buffer size, random against fixed round-robin restart, route-ordered bank queues for reads, endpoint credits, or bank rate (`probes/fit_noc.py`). Separating DRAM row and address conflicts from head-of-line blocking in the request network needs further probes. For example, the 4-row stream with the start bank staggered per worker, and the same with addresses offset by odd multiples of 256 B. [Streams](results/2026-11-19-stream-card0.jsonl.gz) · [Rows sweep](results/2026-11-19-stream-rows-card0.jsonl.gz) · [Bank fan-in](results/2026-11-19-bank-fanin-card0.jsonl.gz)

The bunching on a few banks came from the kernels, not the hardware. Weight pages are dealt over the 8 banks in order, `split()` gives each worker a contiguous block of rows, and each row's pages were issued front to back. With 2-page rows (1B), every worker therefore started on bank 0, 2, 4 or 6. With 4-page rows (8B) it started on 0 or 4. 1B down's 8-page rows put all 88 workers on bank 0 at the start of every row. The `noc.read`/`noc.write` lowering now starts a transfer of a constant number of whole pages (two or more) at page `core.id % pages` and wraps around. Each page still lands at its own L1 address. Card 0, 1B decode, first binding of each kernel, 9 repetitions, against the earlier 21-repetition capture:

| Kernel | Slowest tile | Tile spread | Model within 3% (before → after) |
|---|---|---|---|
| qkv | 50,511 → 50,352 | 24.9% → 22.3% | 143 → 223 / 528 |
| o | 33,139 → 32,022 (−3.4%) | 27.0% → 20.9% | 269 → 288 / 528 |
| gate | 194,092 → 192,173 (−1.0%) | 6.8% → 5.7% | 474 → 456 / 528 |
| down | 120,524 → 111,055 (−7.9%) | 35.3% → 28.2% | 198 → 125 / 528 |
| lm | unchanged | 0.5% | 528 / 528 |

Greedy 1B output is identical, and decode measured 165.3 against 162.1 tok/s in one run each. The setup costs about 12 cycles per multi-page transfer, which shows on a lone worker (embedding +30 cycles). Down now has the right median (−0.1%) but splits by row: the model is 3–5% fast on rows 2–6 and 7–9% slow on rows 8–11. Down reads part of its weights on NoC1, whose y-first routes are the next thing to check. [Rotated 1B capture](results/2026-11-19-decode-1b-rotated-card0.jsonl.gz)

Attention workers that exit early run 85–180 cycles. The TRISCs measure 6–10 cycles longer than modelled, while BRISC matches exactly. Their hardware range across repetitions is wider than ±3% on most tiles.

The initial microbenchmark inventory below was collected on card 1 (p150) unless indicated. “Done” in that inventory means hardware data exists in `results/`. The kernel predictor uses `ttrv/cycles.py`, `ttrv/cycle_noc.py`, and `ttrv/cycle_tensix.py`.

## Data on the card

| category | status | where |
|---|---|---|
| RISC-V ALU/mul/div/CSR/FP | **done**. div = 2 + 4 x ceil(bits/4), capped at 33 | `probes/RISCV.md` Results |
| RISC-V loads, L0 data cache, MMIO latencies and throughput | **done** | `probes/RISCV.md` Results |
| RISC-V stores, store queue, fences, store→load, AMO | **done** (measured table; the drain cases are tabulated, not reduced to a formula) | `probes/RISCV.md` Results |
| Branch predictor | **done**: 1 bit of last outcome per branch, 4-cycle penalty, jalr = last target, shared `ret` 7.75. Also found a `DisBp` stale-state artifact in the probes | `probes/RISCV.md`, `results/*-bpfit-card1`, `*-branch-isolated-card1` |
| I-cache / fetch | **done** under the current firmware: 1.00 per instruction up to 512, cold first pass ≈ 24-33 + 0.1 n | `probes/SFPU.md` Status |
| SFPU issue, latency, hazards, LOADMACRO, Dst interlocks | **done** (model in `hw.py` already, replay test `test_sfpu_model.py`) | `probes/SFPU.md` |
| FPU (matrix unit) throughput, latency, issue (MOP/REPLAY), Src handoff, two threads | **done**. Two value mismatches recorded (MOVA2D fp8→fp32 conversion; SFPSTORE→MVMUL same rows) | `probes/FPU.md` Results |
| Math-thread per-tile overhead (STALLWAIT, drain, SEMWAIT, SETC16 Dst offset, a whole llama-o pass) | **done** | `probes/FPU.md` (`ovh`) |
| Unpacker rates, ttrv `move` cost per pattern, dvalid handoff, extra ops, throttle, NoC contention | **done** | `probes/UNPACK.md` |
| Packer rates per format, llama per-tile sequence, visibility, math→pack handoff and pipeline, contention | **done** | `probes/PACK.md` |
| Sync between Tensix threads (credits, SEMWAIT, STALLWAIT costs) | **done** (unpack `extra`/`handoff`, pack `handoff`, FPU `ovh`, `riscsync` semaphores) | as above |
| Handshakes between RISCs (L1 flag, CB stream registers, Tensix semaphores) | **done**: 29 / 27.5 / 24 cycles one way | `probes/RISCSYNC.md` |
| RISC L1 loads and fetch under NoC and unpacker traffic | **done**: ≤ 2% (negligible) | `probes/RISCSYNC.md` |
| Unpacker/packer under NoC traffic | **done** | `noc_findings.md` Still open item 2, UNPACK/PACK |
| NoC: issue, latency, routing, link capacity, arbitration (round-robin per input port) | **done** | `noc_findings.md` |
| DRAM: latency, refresh (period, per-bank phase), per-bank server model, address conflicts | **done**, apart from the bit-level address map | `noc_findings.md` |
| Dispatch: launch cost, multicast, overlap of the next install | **done** | `noc_findings.md`, `KERNELS.md` |
| Tile clock offsets; stable across a card reset | **done** (reset: max change 1.25 cycles) | `clocks.md` |
| **Ground truth: every Llama 3 kernel (1b, 8b-bf16, 8b-fp8) timed on the card, with the exact images** | **done** (dispatcher-side span per launch; whole step to 0.01-0.16% between runs) | `KERNELS.md`, `results/2026-11-18-kernels-*` |

## Still open

| item | why it matters | how to get it |
|---|---|---|
| Per-tile and per-RISC accuracy | The isolated-launch probe now records both intervals. Congested NoC paths miss the 3% target on card 0 | `probes/role_cycles.py --device 0 --grid 88 --full-projection --traffic-sweep --check` |
| DRAM address-bit map (internal bank / row bits, any XOR hash) | Only if llama's per-core slices fall between the measured conflict cases | `bank.py` align sweep with finer offsets and non-power-of-two strides |
| Attention's MVMUL ADDR_MOD set and gate/qkv's MOVA2D MOP as isolated micro-benchmarks | Covered by the ground truth, but not isolated | `fpu.py` case from the saved listing |
| Other cards: card 0 (partly measured), other p150s, p100; full power cycle | The 3% has to hold on the card the user has | rerun the fw3 suite and `kernels.py` on each card |
| Run-to-run variation of short kernels (1-3.4% per launch from DRAM refresh phase and arbitration) | Sets a floor on per-launch accuracy | compare against the median of ≥ 5 runs (as `KERNELS.md` does) |

## Offline simulator, 2026-11-19

`python3 -m ttrv build FILE --cycles` executes one launch in an event queue. The report contains one interval per tile and one per participating RISC. It models both NoC routes, shared links and DRAM banks, scalar instruction issue and dependencies, Tensix instruction queues, MOP, REPLAY, semaphores, and pack/unpack service. Its accuracy depends on the launch shape and interference. Tensix numerical outputs, several ISA extensions, controller scheduling, router buffer depths, fetch timing and exact stall attribution remain incomplete.

`probes/role_cycles.py` stamps machine-code entry and exit on each RISC and subtracts the measured empty-image stamping overhead. Tile comparisons use timestamps from the same local clock. The probe preserves raw repetitions, compiled image hashes, arguments and signed errors when run with `--output`. Its read/write sweep can reverse the mapping between worker IDs and pages while preserving transfer size. The shipped startup offsets are scoped to the worker firmware fingerprint and can be remeasured with `--startup-only`. Usage is in the [repository README](../README.md).

### Card 0 acceptance run

The 2026-11-19 run compares 21 hardware repetitions with five simulated phase trials. On one tile, all four workloads passed for both the tile and every active RISC. The worst RISC error was 2.10%. The one-tile O projection used eight output rows and one input tile. The 88-worker O projection used the full 1B dimensions. The embedding contention case gathered 88 rows.

| 88-tile launch | Tiles within 3% | Active RISCs within 3% | Median absolute RISC error | Worst absolute RISC error |
|---|---:|---:|---:|---:|
| Scalar loop | 88 / 88 | 440 / 440 | 0.67% | 1.32% |
| Concurrent DRAM reads and writes | 34 / 88 | 56 / 176 | 4.09% | 36.99% |
| Embedding gather | 16 / 88 | 16 / 88 | 10.34% | 114.93% |
| Llama 1B O projection | 6 / 88 | 33 / 440 | 8.79% | 23.48% |
| Llama 1B argmax | 7 / 88 | 74 / 352 | 6.87% | 57.10% |

Each error uses the median for that same coordinate and role. A model that estimates aggregate bandwidth accurately can still assign a congested link to the wrong worker at the wrong time. The simulator assumes 512 bytes of intermediate buffering per hop and approximates DRAM input arbitration. The chain-sharing regression exercises per-port round robin; multi-bank contention and data-dependent computation remain open accuracy problems. [Raw role and tile samples](results/2026-11-19-role-cycles-card0.jsonl.gz) · [Card 0 latency and clock calibration](results/2026-11-19-noc-calibration-card0.jsonl.gz)

### Card 0 after the boot-only Tensix reset

On firmware with the boot-only reset (c11c57b), 31 launches on 88 tiles gave median BRISC-relative entry offsets of 112 cycles for NCRISC and 30, 31 and 32 for TRISC0, TRISC1 and TRISC2. The old TRISC offsets were 605, 606 and 609. NCRISC still polls the subordinate sync word with WAIT_SLOW. The simulator selects the new calibration by firmware fingerprint.

The table compares each prediction with the median of 21 hardware repetitions for the same tile or RISC. Five simulated phase trials were used. All four one-tile workloads passed on the tile and every active RISC (worst RISC 2.15%, worst tile 2.86%).

| 88-tile launch | Tiles within 3% | RISCs within 3% | Median absolute RISC error | Worst absolute RISC error |
|---|---:|---:|---:|---:|
| Scalar loop | 66 / 88 | 440 / 440 | 0.85% | 1.23% |
| Concurrent DRAM reads and writes | 32 / 88 | 53 / 176 | 4.18% | 36.49% |
| Embedding gather | 13 / 88 | 13 / 88 | 11.23% | 117.13% |
| Llama 1B O projection | 5 / 88 | 27 / 440 | 8.86% | 23.27% |
| Llama 1B argmax | 7 / 88 | 116 / 352 | 4.79% | 29.44% |

In a separate 88-worker BRISC-only embedding sweep, the median simulated/hardware cycles across workers were 1,218/1,148 for the 64-byte history read, 3,983/4,016.5 through the shared 4 KiB weight read, 2,121/2,082 through a different weight row per worker, and 5,120/5,577 for the common-row kernel including its write. These are medians of full intervals for each variant. The common-row read prefix had a 7.47% median absolute per-worker error and an 84.86% worst error even with that close grid median. The tests isolate contention and completion order as a problem before any writes or Tensix work. They do not distinguish router buffering from endpoint arbitration. Reproduce the variants with the probe's `--embedding-sweep` option.

[Raw acceptance samples and tile counters](results/2026-11-19-role-cycles-card0-boot-reset.jsonl.gz) · [Raw embedding prefix samples](results/2026-11-19-embedding-isolation-card0-boot-reset.jsonl.gz) · [Entry calibration](results/2026-11-19-startup-card0-boot-reset.json)

### Card 0 checkpoint-backed decode intervals

These captures use the boot-only reset firmware, the installed kernel images, actual launch arguments and fresh graph state for every repetition. Llama 1B used 21 repetitions at position zero. Llama 8B BF16, Llama 8B BFP8 and Nanbeige used seven. Coverage is the first binding of each distinct image. The four captures measured each launch separately with entry/return stamps and a blank-image overhead correction. Offline replay uses zero-initialized numerical buffers. The embedding tile and BRISC both passed on all four models.

[1B](results/2026-11-19-decode-1b-card0.jsonl.gz) · [8B BF16](results/2026-11-19-decode-8b-bf16-card0.jsonl.gz) · [8B BFP8](results/2026-11-19-decode-8b-bfp8-card0.jsonl.gz) · [Nanbeige](results/2026-11-19-decode-nanbeige-card0.jsonl.gz)

| Card 0 probe | Observation | Consequence for the model |
|---|---|---|
| Single NIU status load | Busy at issue distances 1–4, ready at 5 on both measured roles | Five-cycle acceptance. All ten single-worker BF16 read/write transfer tests pass across 64 B to 16 KiB. |
| Simultaneous same-address reads | Groups of eight completions. At 48 workers, groups are spaced about 118 cycles for 64 B and 136 for 512 B | Eight effective read credits per NoC and endpoint. For 88 workers reading 64 B, median absolute error dropped from 15.30% to 1.03%. Worst error is 27.96%. At 2 KiB the median is 7.35%. |
| Remote atomic tickets | Requests to (11,9) from 88 BRISCs arrive in a different order depending on whether their path wraps | Separating dateline virtual channels lowered mean absolute rank error from 23.1 places to 7.3. The original 88-way embedding gather still has 12.81% median error, up from 11.23%. |
| Unpacker and instruction fetch | 16 unpack operations of 256 BF16 values measured 304 unpacker-busy cycles. A 512-instruction NCRISC add chain measured 639 cycles | The busy-interval model reports 304 cycles and the cold-fetch model reports 641. Concurrent fetches by several roles still differ from isolated fetches. |

[Command acceptance](results/2026-11-19-cmd-accept-card0.jsonl.gz) · [Read bursts](results/2026-11-19-noc-burst-card0.jsonl.gz) · [Atomic arrival order](results/2026-11-19-atomic-order-card0.jsonl.gz) · [Unit counters](results/2026-11-19-unit-busy-card0.jsonl.gz) · [Instruction fetch](results/2026-11-19-instruction-fetch-card0.jsonl.gz)

Repeatability limits per-launch predictions. In 21 reconstructions of the 1B graph, argmax TRISC0 at (6,4) took 1,095 cycles on the third-fastest run and 1,365 on the third-slowest. Their ±3% bands are disjoint. The acceptance check therefore scores the median of the repeated hardware interval for **each individual coordinate and role**. Per-role errors remain even against that median. On argmax, packed candidate values drive scalar branches. The numerical scan described below supplies those values. The short attention exit paths also show errors on workers that skip the numerical work.

The firmware change removed most TRISC launch skew. In the 201-launch, 138-worker calibration, subtracting the measured wall-clock offset on each tile puts its median BRISC entry within one cycle of the dispatcher's nine-cycle-per-hop GO model. Median relative NCRISC / TRISC0 / TRISC1 / TRISC2 entries were 96 / 29 / 30 / 32 cycles. The sampled timing mode preserves correlated NCRISC poll phases across tiles. [Role entry samples](results/2026-11-19-role-entry-samples-card0.json.gz) · [Calibration](results/2026-11-19-joint-startup-card0.json)

First-pass jumps to distant instruction addresses cost about 15 cycles per jump in the cold-branch probe. Repetition changes that timing substantially at some alignments. For instance, a chain of 24 BRISC jumps spaced 33 words apart measured 380 cycles in an early timed run, then 125–130 cycles on later runs, including stamps. The model now charges a direct cold fetch for distant redirects. With the current model, 63 of 64 BRISC and all 64 NCRISC intervals in position-zero Llama 1B attention fall inside 3%. TRISC and tile intervals still miss. [Jump sweep](results/2026-11-19-branch-fetch-card0.jsonl.gz) · [Additional spacings](results/2026-11-19-branch-fetch-holdout-card0.jsonl.gz)

| Llama 1B decode before the short-write update, one simulated trial | Tile and RISC intervals within 3% | Median absolute error | Worst absolute error |
|---|---:|---:|---:|
| Embedding | 2 / 2 | 0.06% | 0.06% |
| QKV | 211 / 528 | 3.84% | 18.86% |
| Attention | 188 / 384 | 3.53% | 18.18% |
| O | 255 / 528 | 3.30% | 12.60% |
| Gate | 464 / 528 | 1.27% | 5.35% |
| Down | 211 / 528 | 3.49% | 15.47% |
| Argmax | 258 / 440 | 2.43% | 21.29% |
| LM head | 528 / 528 | 0.08% | 0.21% |

The four-row 1B prefill projection at graph index 17 passed on 64 of 576 intervals (9.27% median, 32.48% worst). On tile (1,5), BRISC measured 30,484 cycles against 20,583 simulated. On tile (11,10), NCRISC measured 31,740 cycles against 40,810 simulated. These opposite signed errors matter to completion order. This capture used three fresh graph prefixes with only the final launch stamped. [Projection samples](results/2026-11-19-prefill-1b-projection-card0.jsonl.gz)

Before the short-write update, across the eight 1B images, 359 of 593 tile predictions and 1,758 of 2,873 RISC predictions fell within ±3% of their hardware medians. In the same runs, 525 tile or RISC intervals had disjoint ±3% bands between their third-fastest and third-slowest hardware repetitions. Of those, 251 were in attention, 137 in argmax, 125 in down and 12 in O. The replay option `--by-role` displays this repeatability check alongside the worst signed error and coordinate for each role.

The Qwen projection at decode graph index 43 passed 187 / 672 tile and RISC intervals over five independently rebuilt graph prefixes. Its median absolute error was 5.98%, with a worst BRISC prediction of 80,819 cycles against 55,314 on (11,3), +46.11%. In these checkpoint graphs the original four-instruction timestamp sequence sometimes produced TRISC entry words that decoded as instructions. A fenced second clock read gave valid intervals for both projection probes. The capture checks each interval against the wall time of the entire graph. [Qwen projection samples](results/2026-11-19-qwen-projection-card0.jsonl.gz)

The argmax input probe keeps its code, addresses and 88-worker placement fixed. It runs zero logits, seeded random logits, then zeros again, checking the winning token and saving all 32 packed (key, index) pairs per worker. When the packer supplied zero words for every tile, the simulated BRISC median signed error on the first zero-input case was −12.45%. Supplying the measured candidate words reduced it to −1.93%. The simulator now calculates those words from simulated L1 when the unpacker reads the page and writes them when the packer runs. It reproduced every packed word on all 88 tiles for both input patterns. All instruction, network and wait times are still simulated. The separately captured 1B decode argmax improved from 170 to 258 of 440 intervals within 3%. [Numerical and timing measurements](results/2026-11-19-argmax-inputs-card0.jsonl.gz)

All 11 distinct images in four-row 1B prefill were captured and replayed. They include two pack images using different worker grids. The 16-worker pack passed 10 / 32 intervals, while the 64-worker pack passed 14 / 128, with worst errors of 14.27% and 41.02%. Prefill attention passed 0 / 192 intervals with 19.28% median absolute error and 27.25% worst error. [Four-row prefill corpus](results/2026-11-19-prefill-1b-four-rows-card0.jsonl.gz)

In the 1B decode attention launch, all 48 intervals on the eight workers with tile durations above 1,000 cycles passed, with worst error 0.58%. The other 56 workers took short exit paths. Of their 336 intervals, 140 passed. Across all attention workers, 122 predictions missed 3% throughout the individual distribution-free 95% confidence interval for the hardware median.

A targeted Qwen decode probe stamps the final 64-byte NCRISC write at PC `0x44c` of graph 0, launch 43. Over three fresh prefixes, the median marker-to-return interval across 112 tiles was 415 cycles. Individual tile medians ranged from 306 to 428 cycles, including the marker suffix. Two coordinates with total NCRISC errors above 20,000 cycles, (7,11) and (11,3), measured 418 and 421 cycles from marker to return. The model charges roughly 1,000 cycles on each. Most of the discrepancy therefore arises earlier in this kernel. [Write marker samples](results/2026-11-19-qwen-writer-tail-card0.jsonl.gz)

In a controlled 96-worker NCRISC burst writing 64 bytes at a 16 KiB stride, hardware took 453–458 cycles per worker. The previous 18-cycle minimum DRAM service interval produced a 67.54% median absolute error. Removing the minimum for pipelined writes reduced the median to 0.88% and the maximum to 2.63%. At 88 BRISCs and a 32 KiB stride, the 64-byte holdout has 1.40% median absolute error and 14.23% maximum. The 512-byte holdout has 12.75% median and 28.41% maximum. The 96-worker 16 KiB write burst still has 49.95% median absolute error. Short write throughput and long write completion order need separate checks. [NCRISC bursts](results/2026-11-19-ncrisc-state-burst-card0.jsonl.gz) · [BRISC holdout](results/2026-11-19-small-write-holdout-card0.jsonl.gz)

Card 0 also maps BF16 negative zero and both signs of subnormal values to positive zero in the argmax scan. The simulator now reproduces all 32 captured key/index pairs on all 88 workers for each of ten input patterns, including signed infinities and NaNs. A separate nine-repetition argmax capture includes the 256,512 bytes of real checkpoint logits for offline replay. [Edge cases](results/2026-11-19-argmax-edge-card0.jsonl.gz) · [Checkpoint logits and timings](results/2026-11-19-argmax-live-logits-card0.jsonl.gz)

On the read path, moving 88 BRISCs from a common address to distinct rows of one bank raised the 64-byte median absolute error from 1.03% to 9.95%. Distributing the distinct addresses among eight banks reduced it to 1.26%. The respective worst errors for the two distinct-address cases were 39.23% and 15.96%. The fixed-address credit probe alone does not characterize DRAM row and bank arbitration. [Same bank](results/2026-11-19-burst-samebank-distinct-card0.jsonl.gz) · [Eight banks](results/2026-11-19-burst-eightbank-distinct-card0.jsonl.gz)

Stamping the fence at PC `0x250`, immediately after the six activation reads have completed, splits the Qwen projection again. Approximate measured entry-to-fence time is the corrected NCRISC duration minus the marker-to-return interval for the same repetition. The median is 25,966 cycles at (7,11) and 20,286 at (11,3), versus 15,164 and 26,540 predicted. From the fence to return, hardware medians are 50,355 and 41,426 cycles, versus 41,608 and 56,644 predicted. Across 112 tiles, median absolute errors in the two phases are 4,404 and 2,174 cycles. This localizes error to both concurrent activation reads and downstream work, which includes waiting for packed output. The measurements use separate, instrumented graph repetitions. [Read barrier samples](results/2026-11-19-qwen-read-barrier-card0.jsonl.gz)

On the full 1B QKV image, the pipelined short-write update lowered worst absolute error from 18.86% to 11.33% while reducing the number inside ±3% from 211 to 133 of 528. Removing an isolated write error can expose other errors that had compensated for it.
