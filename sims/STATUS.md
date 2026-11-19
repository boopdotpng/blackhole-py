# sims/: what is measured, what is open (2026-11-18)

Goal (`goals.md`): a simulator that predicts ttrv-generated kernels within 3% of the card. Everything below was run on
**card 1** (p150) unless noted. "Done" means hardware data exists, is written up, and the evidence is in `results/`.
`hw.py` has **not** been updated with any of this yet: it still holds the earlier drafts (TODOs, L0 off, old I-cache
values). Updating it is the next step.

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
| Per-core and per-RISC start/end inside a kernel | Kernel time = the slowest core, and cores finish up to 4x apart. To check the arbitration model, need per-core times, not just the span | have ttrv emit a wall-clock stamp at kernel entry and exit (a build flag), rerun `kernels.py` |
| DRAM address-bit map (internal bank / row bits, any XOR hash) | Only if llama's per-core slices fall between the measured conflict cases | `bank.py` align sweep with finer offsets and non-power-of-two strides |
| Attention's MVMUL ADDR_MOD set and gate/qkv's MOVA2D MOP as isolated micro-benchmarks | Covered by the ground truth, but not isolated | `fpu.py` case from the saved listing |
| Other cards: card 0 (partly measured), other p150s, p100; full power cycle | The 3% has to hold on the card the user has | rerun the fw3 suite and `kernels.py` on each card |
| Run-to-run variation of short kernels (1-3.4% per launch from DRAM refresh phase and arbitration) | Sets a floor on per-launch accuracy | compare against the median of ≥ 5 runs (as `KERNELS.md` does) |

## The simulator (not started)

1. Functional execution of the ttrv images (the RV32 subset ttrv emits, 5 RISCs per tile; the Tensix ISA with
   3 threads, MOP expander, REPLAY). `ttsim` in this workspace is a functional Blackhole simulator that could serve as
   the base or as a reference.
2. Timing for each unit from the tables above (put them into `hw.py` first).
3. A packet-level NoC (per-port round-robin, routing order, ~63 B/c per link) and the DRAM bank model.
4. Validation against `KERNELS.md`: per-kernel spans and the step total, within 3% of the median.
