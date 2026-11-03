# FPU/SFPU interleaving: the Dst half matters

Measured on 2026-09-17, Blackhole card 0, physical cores (1,2) and (1,4).
The slowdown follows **Dst half placement**, rather than being a general
RISC-V context switch between FPU and SFPU instructions. Register-only SFPU
arithmetic does not show it. Different addresses within the same half do.

Our best explanation is coarse Dst-half ownership/hazard arbitration with a
pipeline drain or turnaround when the accessing engine changes. Independent
halves permit overlap. This explains the measurements; the exact circuitry,
port layout, and drain conditions are not established by these tests.

## Boundary experiment

In the tested FP32 configuration, Dst tiles 0–3 occupy one half and 4–7 the
other. FPU destination and SFPU scratch always use different tiles:

| FPU tile | SFPU tile | Burst switching penalty |
|---|---|---|
| 0 | 1 or 3 | Yes |
| 0 | 4 or 7 | No |
| 4 | 1 | No |
| 4 | 5 or 7 | Yes |

This boundary holds with ELWMUL + SFPLOAD and ELWMUL + SFPLOAD/SFPMAD,
on both physical cores. Separate threads eliminate repeated same-thread
switching overhead but still contend when accessing the same half.

Approximate steady cycles per work item (one ELWMUL plus the indicated SFPU
work), measured using slopes over increasing loop lengths:

| SFPU work | One thread, same half, batch 1 | One thread, opposite halves | Separate threads, same half | Separate threads, opposite halves |
|---|---:|---:|---:|---:|
| SFPLOAD | 8 | 2 | 2 | 1 |
| SFPLOAD + SFPMAD | 14 | 3.03 | 3 | 2 |
| Register-only SFPMAD | 2 | — | 1 | — |

The 3.03 includes two loop overhead cycles per 64 work items. Counts describe
completed work, not just instruction enqueue time. Thread results include
global earliest-start/latest-completion timing, alongside local durations.

## Why batches of 32 help

With both engines addressing the same half, a burst of `b` FPU instructions
followed by `b` SFPU work items gives:

| Batch b | 1 | 2 | 4 | 8 | 16 | 32 | 64 |
|---|---:|---:|---:|---:|---:|---:|---:|
| MVMUL/ELWMUL + SFPLOAD or SFPSTORE | 8 | 8 | 5 | 3.5 | 2.75 | 2.375 | 2.1875 |
| MVMUL/ELWMUL + SFPLOAD/SFPMAD | 14 | 8.5 | 5.75 | 4.375 | 3.6875 | 3.34375 | 3.171875 |

The first row fits `2 + 12/b` for b >= 2; b=1 is an exception. The second
fits `3 + 11/b`. These are empirical fits for these streams, not universal
instruction latencies. Batch 32 amortizes the overhead; it does not eliminate
it, and 64 improves it further.

At batch 8, inserting up to five TTNOPs after the FPU burst or seven after
the SFPU burst costs no additional time in the ELWMUL/SFPLOAD probe. Larger
gaps increase time. This supports a hidden turnaround/drain budget, but does
not establish a universal five- or seven-cycle switch latency.

Controls narrow the explanation:

- Register-only SFPNOP, SFPLOADI, independent SFPADDI and SFPMAD streams stay
  near two cycles per FPU/SFPU pair at every batch size.
- REPLAY reproduces the same-half penalty: inline instruction fetching or
  fusion is not required for the effect.
- SFPLOAD mode 11, which produces zero in the functional model, still shows
  the penalty. This suggests instruction/address resource arbitration; it
  does not prove that the physical memory port is unused in this mode.
- SETRWC, INCRWC and CLREXPHIST with SFPLOAD do not reproduce the penalty.
  Shared row counters alone are insufficient to explain it.
- Separate Dst addresses and exact output checks rule out an intended
  same-address data dependency in these probes.

## Half synchronization and thread costs

LLK's `DstSync::SyncHalf` implements a two-section producer/consumer protocol:
math initializes the semaphore for two outstanding sections rather than one,
and flips the destination offset. Pack waits for its work, clears its half,
releases the section, and flips its offset. This enables ping-pong ownership,
so one engine can work on one half while another uses the other half.
It is not simply a half-mask option on STALLWAIT, and does not remove the
need to synchronize actual dependencies.

Relevant local sources:

- [Math synchronization](../../../tt-llk/tt_llk_blackhole/llk_lib/llk_math_common.h)
  (in the sibling checkout; see `_llk_math_pack_sync_init_`).
- [Pack section release](../../../tt-llk/tt_llk_blackhole/llk_lib/llk_pack_common.h).
- [Existing Dst bandwidth tests](../compute/fpu/test_dst_bandwidth.py) and
  [matmul half-buffer discussion](../compute/fpu/matmul_fp32_results.md).

For a concrete synchronization comparison, these are median completed cycles
on core (1,2), batch 32, ELWMUL + SFPLOAD/SFPMAD:

| Placement / schedule | 64 work items | 128 | 256 |
|---|---:|---:|---:|
| Same half, one thread | 236 | 450 | 878 |
| Same half, FPU T1 / SFPU T0 | 318 | 521 | 901 |
| Opposite halves, one thread | 235 | 433 | 821 |
| Opposite halves, FPU T1 / SFPU T0 | 294 | 431 | 685 |
| Opposite halves, per-burst semaphore roundtrip | 362 | 593 | 1055 |

The split schedule has one start/finish rendezvous; the roundtrip schedule
deliberately synchronizes every burst and serializes it. It is a cost control,
not an optimized half-buffer pipeline. Small jobs can lose all overlap benefit
to synchronization. A production pipeline needs independent work on alternate
halves and handoffs only at actual dependency boundaries.

## Original RMSNorm reproduction

### Follow-up: actual half-buffer producer/consumer synchronization

The earlier independent-stream and roundtrip tests did **not** implement the
alternating half-buffer protocol. The follow-up
[dependent pipeline test](test_dst_half_pipeline.py) does: FPU T1 produces
tiles 0 and 4 alternately, and SFPU T0 loads and accumulates squares of each
completed section. A semaphore counts outstanding sections. Capacity 1
serializes production and consumption; capacity 2 permits FPU to produce the
other half while SFPU consumes the first. Both variants use identical work
and addresses. Producer waits on maximum before writing and publishes after
MATH completion; consumer waits on nonzero and releases after SFPU completion.

This is the SyncHalf ownership protocol adapted to FPU→SFPU, using explicit
half addresses rather than LLK destination-offset flips. It is not a direct
invocation of the math→pack helper, nor a selective STALLWAIT mask. No half
clear is needed: this test deliberately accumulates across rounds and checks
the expected cumulative values.

Completed steady cycles per ELWMUL + SFPLOAD/SFPMAD work item, including
semaphore operations and drains (core 0, slope over the larger loop lengths):

| Work items per section | Capacity 1 | Capacity 2 / half buffering |
|---|---:|---:|
| 8 | 5.26 | 3.26 |
| 16 | 4.13 | 2.62 |
| 32 | 3.5625 | 2.3125 |
| 64 | 3.28125 | 2.15625 |
| 128 | 3.140625 | 2.078125 |

Thus half buffering preserves useful overlap despite synchronization. At
batch 32 the measured steady cost drops 35%; it approaches the SFPU's two
instructions per item as sections grow. This establishes feasibility for a
dependent pipeline, not an end-to-end RMSNorm speedup: that kernel still needs
its real reduction and data-lifetime constraints respected.

All ten cases passed on each of physical cores (1,2) and (1,4), with exact
checks of both final FPU tiles, SFPU sums over every produced section, and
output guards. Each case measures 4/16/64 pairs of sections, discards one
warmup, and retains five samples. Evidence includes local thread durations
and the global span: [core 0](evidence/dst_half_pipeline_core0.jsonl),
[core 2](evidence/dst_half_pipeline_core2.jsonl).

```sh
tt-device-queue run --device 0 --cwd "$PWD" -- \
  'DST_HALF_OUTPUT=/tmp/half-pipeline.jsonl ../.venv/bin/python -m pytest tests/timing/test_dst_half_pipeline.py --bh-hardware --bh-device=0 --bh-core=0 -q'
```

The subsequent [RMSNorm implementation](rmsnorm_half_pipeline.md) applies this
resource separation to the full kernel and measures end-to-end improvement.

## RMSNorm placement results

The hybrid kernel now accepts `scratch_tile` (default remains 0). Moving
scratch alone from tile 0 to tile 7 keeps the product tiles in the opposite
half for n=1024 and n=2048. Prefetch and load macros are disabled equally for
all schedules in this comparison.

Median cycles on core (1,4), scratch tile 0 → tile 7:

| Elements | Schedule | Compute | L1 to L1 |
|---|---|---:|---:|
| 1024 | Queued | 245 → 242 | 836 → 836 |
| 1024 | Interleaved | 586 → 283 | 1177 → 858 |
| 1024 | FPU T1 / SFPU T0 | 300 → 285 | 891 → 875 |
| 1024 | FPU T1 / SFPU T2 | 301 → 285 | 893 → 873 |
| 2048 | Queued | 459 → 454 | 1162 → 1157 |
| 2048 | Interleaved | 1141 → 472 | 1842 → 1179 |
| 2048 | FPU T1 / SFPU T0 | 576 → 547 | 1282 → 1251 |
| 2048 | FPU T1 / SFPU T2 | 577 → 548 | 1268 → 1240 |

Outputs are bitwise identical between placements within each schedule.
Normal, arange, zero and outlier inputs also pass a float64 reference check
with BF16 tolerance and output guards. The 2048-element interleaved compute
interval drops 59%, but queued execution remains competitive and splitting
threads still loses here. At n=4096, product tile 4 enters the upper half;
scratch tile 7 would no longer separate all products from scratch.

## Evidence and reproduction

[Microbenchmark](test_fpu_sfpu_interleave.py) contains 315 cases including an
offline instruction-order check. [RMSNorm comparison](test_rmsnorm_dst_halves.py)
adds two cases. The final runs passed 315 cases on core 0 and 321 on core 2
(the latter includes four existing RMSNorm cases).

Raw evidence: [core 0](evidence/fpu_sfpu_core0.jsonl),
[core 2](evidence/fpu_sfpu_core2.jsonl),
[RMSNorm](evidence/rmsnorm_dst_halves.jsonl). Records retain samples,
coordinates, work counts and source/image hashes. Microbenchmarks discard one
warmup and retain five samples per loop length; RMSNorm retains fifteen.
Both use completion waits inside timed work; setup and observation packing
are outside the microbenchmark interval. No empty-loop subtraction or fragile
performance threshold assertion is used. Loop overhead can overlap engine
work and is intentionally retained.

```sh
# From blackhole-py; use fresh output paths because evidence is appended.
tt-device-queue run --device 0 --cwd "$PWD" -- \
  'INTERLEAVE_OUTPUT=/tmp/interleave.jsonl RMSNORM_HALVES_OUTPUT=/tmp/halves.jsonl ../.venv/bin/python -m pytest tests/timing/test_fpu_sfpu_interleave.py tests/timing/test_rmsnorm_dst_halves.py --bh-hardware --bh-device=0 --bh-core=0 -q'
```

These results cover two cores on one card, FP32 Dst with the configured
address mapping. Other formats, remapping, load macros, packing contention,
and dependent producer/consumer schedules need their own calibration.
For kernel prediction, model Dst-half resource sharing as well as aligned
block data dependencies; do not simply sum independent instruction costs.
