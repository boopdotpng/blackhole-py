# Tensix kernel timing

[Instruction table](tensix_timing.md) · [machine-readable catalog](tensix_timing.json)
· [raw hardware samples](tensix_measured.jsonl) · [measured summary](tensix_measured.md)

The table classifies all 137 Tensix encoders in `ttko.isa.Tensix`. It separates
result latency, independent issue spacing, and blocking/variable work. It is a
backend scheduling reference, not yet a complete static kernel runtime predictor.
RISC-V instruction timing is outside this work. A kernel can still be delayed by
its RISC-V feeders, NoC/DRAM traffic, or another core supplying its inputs.

## Useful first approximations

| Work | Cycles |
|---|---:|
| Ordinary SFPU integer/bit/move/reciprocal/cast operation, 32 lanes | 1 |
| SFPU add/multiply/MAD/integer multiply, dependent chain | 2 per instruction |
| Same arithmetic, independent destinations | 1 per instruction, plus final pipeline tail |
| SFPU swap or lane shuffle | 2; an explicit following SFPNOP fits inside these 2 |
| FPU MVMUL/elementwise/pool | 1 issue; 5 result latency |
| FPU accumulation repeatedly touching the same dependent Dst block | about 5 per instruction |
| Scalar ALU, immediate or both inputs in same aligned four-GPR bank | 3 |
| Scalar ALU, input GPRs in different banks | 4 |
| Configuration write WRCFG | 1 issue; 2 result latency |
| CFGSHIFTMASK | 2 issue; 2 result latency |
| Semaphore operation, uncontended | 1 |
| Wait | 1 to latch, then actual dependency wait and unblock lag |

At an **assumed** 1.35 GHz, `nanoseconds = cycles / 1.35`; 1,350 cycles is
1 microsecond. Use the actual device clock when converting cycles to time.
The table's source links are pinned to the checked-out manual/LLK revisions.
Blackhole manual values, shared architecture descriptions, Wormhole estimates,
analogy estimates, and unknowns are labelled individually. Reserved TBUFCMD and
undocumented RAREB/TRNSPSRCA/RSTDMA do not have defensible cycle counts.

## FPU/SFPU interleaving and Dst halves

[RMSNorm implementation and measured speedup](rmsnorm_half_pipeline.md).

[Measured investigation](fpu_sfpu_interleave.md): FPU plus SFPU loads/stores
can incur substantial stalls even at different addresses within the same Dst
half. In the tested FP32 configuration, tiles 0–3 and 4–7 are separate access
domains. Opposite-half placement removes the burst penalty; separate threads
then overlap the engines. Batching 32 only amortizes same-half switching cost.
Include half ownership and handoff costs in a kernel estimate, alongside the
aligned-block data hazards below.

## Estimate each physical Tensix core

Keep three ordered instruction streams for each physical worker: T0, T1 and T2
(usually unpack, math, pack, but use what the kernel actually emits). They run
concurrently and share backend resources. They are not three independent copies
of the SFPU/FPU. The frontend can supply one expanded instruction per thread per
cycle; a backend's issue limit applies across all threads using that backend.

1. Expand RISC-controlled loop trip counts, MOP templates and REPLAY sequences
   into **dynamic** Tensix operations. Count separate fidelity phases. A single
   MOP is not a one-cycle matrix multiply. Account for load-only replay setup and
   the one-cycle MOP-to-non-MOP transition where it is not hidden.
2. Track each thread's next issue time, backend availability, operand readiness,
   and ownership of SrcA/SrcB/Dst. For an instruction, use
   `start = max(thread_ready, unit_ready, inputs_ready, waits_satisfied)`.
   Its result becomes ready at `start + latency`; its unit's next issue slot is
   `start + issue_interval`. For ordinary pipelined operations, the thread can
   continue after one slot; nonpipelined scalar work blocks it for its occupancy.
3. Apply scheduling exceptions from the table: Dst hazards are at aligned 8x16
   block granularity, move instructions restrict which operations can follow,
   shuffle/SWAP reserve the next SFPU slot, and configuration writes can require
   spacing. Do not charge a separate extra cycle for an SFPNOP occupying a
   shuffle's already reserved slot. Load-macro sub-ops require their own schedule.
4. Model semaphore/mutex/STALLWAIT conditions as edges to actual producer
   completion. They have no fixed useful upper bound in isolation. A wait's
   block mask affects selected instruction classes; unrelated work can proceed.
   Model source-bank handoffs and Dst ownership similarly.
5. Use data volumes and configured paths for unpack/pack/mover work. UNPACR
   uncompressed address setup is at least 2 cycles, followed by at least
   `ceil(input_bytes / effective_bytes_per_cycle)` transfer work and a pipeline
   tail. The documented L1 rates are 16/32/64 B/cycle, subject to mode and
   contention. A 512-byte BF16 face at x4 has an 8-cycle transfer lower bound,
   not an 8-cycle completed UNPACR. PACR similarly needs payload, conversion,
   active packers, flush behavior and L1 contention; it has no universal fixed
   completed-instruction cost.
6. Record completion of every stream and asynchronous backend tail on that
   core. The core finishes at their maximum **on this common schedule**, after
   required completion waits. Report each physical core separately, including
   coordinates and dynamic work counts. For kernels with inter-core transfers,
   the producer/consumer edges must connect their schedules.

For simultaneous starts, `kernel_cycles = max(core_completion_cycles)`.
With launch skew, use
`max(core_start + core_duration) - min(core_start)`.
Summing isolated stream durations overestimates overlap; taking their isolated
maximum underestimates dependencies and shared-unit contention.

An approximate steady tile pipeline with disjoint resources is
`U + M + P + (tiles-1)*max(U,M,P)`, where U/M/P are per-tile unpack/math/pack
service times and sufficient buffers are available. For U=40, M=64, P=32 and
10 tiles, that gives 712 cycles before handoff overhead. A core with 12 tiles
would take 840; report both, with 840 as the kernel estimate. This is an
illustration, not a measured kernel or a rule for stages sharing the same unit.

For a simpler arithmetic example, 100 independent MVMULs with ready inputs and
enough distinct Dst blocks take approximately `100 + 4 = 104` backend cycles.
100 accumulations on one dependent Dst block take approximately 500 cycles.
Existing [resident-source MVMUL measurements](../compute/fpu/matmul_compute_only.md)
record 571,893 completed cycles for 571,851 MVMULs on one core, supporting the
one-cycle independent issue approximation. That benchmark also records multicore
start skew; its durations are not measurements of unpacking or packing.

## Hardware evidence and rerunning

The committed samples were taken on physical card 0, core index 0, separately on T0/T1/T2 on
2026-09-17. They measure three loop lengths (1,024 / 2,048 / 4,096 body operations),
one warmup and seven samples each. Adjacent median slopes remove fixed launch,
timestamp and drain overhead; loop instructions and feed/backend interaction
remain. No empty-loop subtraction is applied because that work can overlap.
SFPU cases establish completion/timing, with arithmetic behavior checked by
separate conformance tests. The new scalar cases also check the final GPR value.

The original SFPU probe accidentally appended an SFPNOP to `dma_nop` because
it selected padding with `case.endswith('_nop')`. That measured a two-instruction
pair as one body operation and incorrectly suggested 2 cycles per DMANOP.
Padding is now restricted to `swap_nop`/`shuffle_nop`; the committed evidence
uses the corrected probe. Those two padded cases count a pair as one body
operation intentionally, to establish that padding fits in the reserved slot.

```sh
# From blackhole-py. Use a new result file; TIMING_OUTPUT appends.
tt-device-queue run --device 0 --cwd "$PWD" -- \
  'TIMING_OUTPUT=/tmp/tensix-sfpu.jsonl ../.venv/bin/python -m pytest tests/timing/test_instruction_timing.py -k sfpu --bh-hardware --bh-device=0 -q'
tt-device-queue run --device 0 --cwd "$PWD" -- \
  'TIMING_OUTPUT=/tmp/tensix-control.jsonl ../.venv/bin/python -m pytest tests/timing/test_tensix_control_timing.py --bh-hardware --bh-device=0 -q'

# Offline regeneration and coverage checks; no device access.
../.venv/bin/python -m tests.timing.tensix_catalog
```

Use `--bh-core=N` to repeat on another physical core. The evidence contains exact
coordinates, samples, body sizes, image hashes and probe source hashes. These are
single-core isolated measurements; they do not establish all-core contention
costs. For an actual kernel, place profiler markers on each active core and
stream, with backend completion waits **inside** the measured interval, and
retain per-core records rather than only their maximum. Distinguish local stream
duration from a global earliest-start/latest-completion interval.

The next work for automatic prediction is dynamic loop/MOP expansion, resource
and operand dependency tracking, calibrated pack/unpack service models, and
per-core handoff edges. RISC-V feeder and memory timing can then be added to this
Tensix model. The viewer shows per-instruction timing but does not claim a kernel
total before those dependencies are modelled.
