# Applying Dst-half overlap to hybrid RMSNorm

The hybrid RMSNorm can run faster by keeping FPU products in lower-half Dst
tiles 0..3 and SFPU scratch in upper-half tile 7. The new production option is:

```python
emit_rmsnorm(..., half_sync=True)
```

TRISC1 copies x into scratch, publishes a Tensix semaphore, and computes
x*gamma in the other half. TRISC2 waits for scratch, accumulates the square
sum with the existing load macros, and releases scratch after SFPU completion.
The next copy waits for that release. After the last tile, a second semaphore
hands the accumulated sum back to TRISC1 for reduction and normalization.
TRISC2 then packs as before. TRISC0 continues to prefetch inputs.

One scratch buffer suffices for this kernel. Unlike the dependent synthetic
FPU→SFPU pipeline, the FPU product and SFPU square computation are independent
once x has been copied. Both engines can work on the same input tile using
different Dst halves. Alternating scratch across halves reintroduces contention
on some tiles; two upper-half scratch buffers did not materially improve the
macro schedule. The benchmark retains these controls.

## Measurements

2026-09-17, card 0, physical core (1,2), HiFi4 with square macros and unpack
prefetch enabled in both schedules. Median completed cycles from the raw
L1-to-L1 kernel, including semaphore handoffs and output packing:

| Elements | Queued total | Overlap total | Fewer total cycles | Queued compute | Overlap compute |
|---|---:|---:|---:|---:|---:|
| 1024 | 810 | 780.5 | 3.6% | 223 | 190 |
| 2048 | 1051 | 995.5 | 5.3% | 356 | 291 |
| 3072 | 1291 | 1204.5 | 6.7% | 490 | 392 |
| 4096 | 1538.5 | 1423.5 | 7.5% | 624 | 494 |

The compute interval improves 18% at 2048 and 21% at 4096. Totals improve less
because unpacking, reduction, normalization, and packing remain. Host, NoC and
DRAM time are excluded from these numbers; they are not full decode speedups.
The compute interval starts after the first scratch copy, while the total
includes it. Initialization before the established total marker is unchanged
except that semaphore initialization is inside the new timed path.

The [benchmark](test_rmsnorm_half_pipeline.py) compares seven schedules/layouts,
with and without square macros, for 1024/2048/3072/4096 elements. It alternates
execution order, discards two warmups, and retains thirty normal-input samples.
Normal, arange, zero, small, large and per-tile outlier inputs pass the float64
reference tolerance. Every layout/schedule is bitwise identical to its queued
counterpart, with guard bytes and no diagnostic-scale export checked.

The actual [production emitter](../../examples/rmsnorm_hybrid.py) is also
tested through DRAM and circular-buffer transport, including HiFi3/HiFi4,
explicit/MOP ELWMUL, repeated launches, and consecutive 2048-element calls.
Production queued/overlap outputs are bitwise identical in the sequence test.

## RISC-V loops remove the code-size limit

The first implementation unrolled both square accumulation and packing on
TRISC2. Two optimized 4096-element calls needed 5284 bytes, exceeding its
4096-byte text partition (the queued baseline fit at 4020 bytes).

The production overlap path now uses two bounded RISC-V tile loops:

- Square accumulation repeats the same scratch-address instruction body,
  retaining semaphore wait, SFPU drain, and scratch release on every iteration.
- Packing uses the runtime tile index for Dst selection and retains per-tile
  circular-buffer reservation, completion, and publication.

Two optimized calls now use **2196 bytes** on TRISC2 for either 2048 or 4096
input elements. This leaves 1900 bytes in the partition and is smaller than
both queued compositions (2500 and 4020 bytes respectively). Other thread
images also fit. The production sequence regression now executes two calls
at both sizes, repeats launches, checks output guards and numerical accuracy,
and requires bitwise equality against the queued implementation. Existing
HiFi3/HiFi4 and explicit/MOP production checks also exercise the looped path.

`half_sync=True` selects this compact implementation; the existing default
and reference-vs-hybrid decode selection are unchanged. The performance table
above measures the raw kernel's unrolled schedule. It does not measure RISC-V
loop overhead in the updated production emitter; the direct production
measurement below supersedes it for that path.

## Reproduction and evidence

```sh
tt-device-queue run --device 0 --cwd "$PWD" -- \
  'RMS_HALF_OUTPUT=/tmp/rms-half.jsonl ../.venv/bin/python -m pytest tests/timing/test_rmsnorm_half_pipeline.py tests/compute/fpu/test_rmsnorm_hybrid.py --bh-hardware --bh-device=0 --bh-core=0 -q'
```

Use a fresh output path; JSONL output appends. Raw records retain the samples,
source/image hashes and physical coordinates:
[core 0](evidence/rmsnorm_half_pipeline_core0.jsonl),
[core 2](evidence/rmsnorm_half_pipeline_core2.jsonl).
The core-0 run passed 33 cases including existing hybrid regressions; the
core-2 run repeats the ten new timing/production cases. Performance is
reported rather than enforced as a fragile cycle threshold.

## Direct timing of the looped production emitter

The [production timing test](test_rmsnorm_production_timing.py) measures the
actual emitter with inputs ready in its L1 circular buffer, ending after
output packing and Dst release. It excludes DRAM input/output transfer time.
Optional profiler markers do not change the default uninstrumented emission.
Fifty samples follow two warmups with alternating variant order; every launch
checks the reference, output guard and bitwise equality.

Core (1,2), median cycles:

| Elements | Queued L1-to-L1 | Looped overlap L1-to-L1 | Queued compute | Looped compute | Queued pack | Looped pack |
|---|---:|---:|---:|---:|---:|---:|
| 2048 | 1125.5 | 1087 | 356 | 291 | 357 | 382 |
| 4096 | 1686.5 | 1588.5 | 624 | 495 | 651 | 681.5 |

This is 3.4% and 5.8% fewer total cycles. The compute benefit survives the
RISC-V loops, while runtime tile selection/loop control adds some packing
cost. These production totals include CB packing bookkeeping and have a
different start marker than the older raw-kernel totals; compare variants
within this table rather than subtracting values between the two tables.

Evidence: [core 0](evidence/rmsnorm_loop_production_core0.jsonl),
[core 2](evidence/rmsnorm_loop_production_core2.jsonl). Reproduce through
`tt-device-queue` with `tests/timing/test_rmsnorm_production_timing.py`,
`--bh-hardware --bh-device=0 --bh-core=0` and optionally
`RMS_PRODUCTION_OUTPUT=/tmp/rms-loop.jsonl` (appends).
