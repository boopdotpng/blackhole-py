# Blackhole 1024-element sum: FPU versus SFPU finish

Measured 2026-09-05 on device 0, `p150a`, PCI `0000:01:00.0`.
Worker indices 1 and 2 (NoC coordinates `(1,3)` and `(1,4)`) reproduced the
same reduction and finish timings. The fastest tested sequence was the FPU
row-dot finish, at 95 cycles versus 104 cycles for the SFPU finish. This is
not a proof of a globally optimal reduction kernel.

## Reproduce

From the `blackhole-py` repository:

```bash
python3 -m pytest tests/compute/fpu/test_sum_finish.py --bh-hardware --bh-core=1 -s -q
python3 -m pytest tests/compute/fpu/test_sum_finish.py --bh-hardware --bh-core=2 -s -q
```

Both runs passed all 9 parameterized tests. Raw logs:

- [Worker 1](sum-finish-core1.log)
- [Worker 2](sum-finish-core2.log)
- [Worker 1, repeat with the final test](sum-finish-core1-repeat.log)
- [Original mean benchmark](mean-baseline-cycles.log): 8 tests passed before
  the experimental sequences, including the SFPU-only alternative.

## What is timed

The input is `arange(1024)`, materialized as FP32 in L1 and unpacked to TF32
in SrcA. All input integers are exactly representable at the selected
precision. SrcB contains sixteen ones in its first row, with other entries
zero except for the row-dot path's extra weight column in scratch rows
16–31. All paths transfer the same 4096-byte weight buffer.

The first stage runs four 16x16 SrcA blocks in each of two fidelity phases:
eight GAPOOL or MVMUL instructions, accumulating sixteen column sums into
the same FP32 Dst row. Address-modifier and replay setup, initial Dst clear,
and initial operand unpacking are outside the **reduction** measurement.
Preparing the second-stage operands is inside it.

Each variant has one unmeasured warmup followed by eleven timed launches.
Every launch checks the scalar result and a guard after the packed output.
An additional run with an internal marker measures just the finish after
draining the first stage. Do not add its instrumented reduction time to or
substitute it for the uninstrumented reduction time: the extra marker and
drain change the schedule.

Timings use the Tensix wall-clock low register through `tests/profiler.py`.
The paired empty markers measure 12 cycles. Results below are **raw**
intervals, including marker overhead and the completion synchronization
inside each region. Subtracting 12 gives an approximate overhead-adjusted
comparison, not an exact instruction latency. Host dispatch, compilation,
and profiler readback are excluded. The L1-to-L1 interval additionally
includes operand unpacking, packing, and the associated handshakes, but
still excludes initial kernel configuration and host-to-L1 initialization.

## Results

All reduction and finish samples had min = median = max on both workers.
L1-to-L1 timings varied by one or two cycles.

| First stage | Finish | Whole reduction | Finish alone | L1-to-L1 median |
|---|---|---:|---:|---:|
| GAPOOL | SFPU | 104 | 56 | 227 |
| MVMUL | SFPU | 104 | 56 | 227 |
| GAPOOL | FPU transpose | 97 | 50 | 220 |
| MVMUL | FPU transpose | 97 | 50 | 220 |
| GAPOOL | FPU row dot | **95** | **48** | **218** |
| MVMUL | FPU row dot | **95** | **48** | **218** |

The row-dot path saves 9 raw cycles (8.7%) over SFPU for the whole reduction.
MVMUL's extra output rows are zeros in this construction, so its greater
arithmetic throughput produces no speedup.

### The three finishes

- **SFPU, 18 issued Tensix instructions:** wait for math; two loads for the
  even and odd columns; add them; three register copies, seven one-lane
  rotations and three additions for an eight-lane reduction; one store.
  FP32 column sums stay in Dst/SFPU throughout.
- **FPU transpose, 13 instructions:** reset counters; move the partial row
  to SrcB scratch; gate/reset and transpose it; four MOVB2A instructions
  move the transposed block into SrcA; clear Dst; two more pool instructions
  at phases 0 and 1. The original SrcB row of ones is reused. This follows
  the arrangement in Blackhole LLK's scalar reduction.
- **FPU row dot, 11 instructions:** reset counters; move the partial row
  to SrcB row zero; four MOVB2A instructions copy the preloaded column of
  ones from SrcB scratch into SrcA; clear Dst; two pool instructions at
  phases 0 and 2. This avoids the transpose and one gate/reset instruction.

Instruction counts include the gates/waits inside the finish and exclude
the common terminal drain and profiling instructions. Counts alone do not
predict elapsed cycles because dependent operations stall.

## Precision is different

All variants pass the exact integer ramp, ones, signed pattern, and sparse
boundary probes. The input below is also exactly representable by the
first-stage multiplier, but its partial sum is not preserved on the FPU
round trip:

| Input | Exact sum / SFPU result | Both FPU finishes |
|---|---:|---:|
| 1024 ones, with `1/512` added to element zero | 1024.001953125 | 1024.0 |
| Each of 64 rows has `+1,-1,0,...`, with `1/512` added to element zero | 0.001953125 | 0.0 |

MOVD2B narrows FP32 partial sums to TF32 in this configuration. The
transpose variant also puts those partials through the SrcA multiplier's
precision restrictions; the row-dot variant puts them on SrcB. Extra
fidelity phases cannot restore bits already discarded during the move.
Use the SFPU finish when preserving the FP32 partial sums matters.
Neither variant makes the initial TF32 stage a general full-FP32 reduction.

## Are the timing docs sufficient?

They are sufficient to identify bottlenecks and choose candidates, but not
to certify the best end-to-end schedule without measurement:

- [Matrix Unit instruction table](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/MatrixUnit.md)
  lists GAPOOL and MVMUL at one instruction per cycle with five-cycle
  latency. Both have the same issue rate; MVMUL does more arithmetic per
  instruction, not more input-A blocks.
- [Blackhole Dst scheduling](https://github.com/tenstorrent/tt-isa-documentation/blob/main/BlackholeA0/TensixTile/TensixCoprocessor/Dst.md#instruction-scheduling)
  explicitly documents the four following cycles during which the same
  aligned 8x16 destination block cannot be read. Our eight first-stage
  instructions all depend on that block, so peak issue rate is unavailable.
- [Vector Unit timings](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/VectorUnit.md)
  list two-cycle SFPADD and lane-rotation latency, and one-cycle SFPLOAD /
  SFPSTORE latency. The seven rotations in this SFPU implementation matter.
- [MOVD2B scheduling](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/MOVD2B.md#instruction-scheduling)
  documents the three following cycles restricted to other MOVD2B
  instructions, plus format and bank-ownership caveats.
- [MOVB2A scheduling](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/MOVB2A.md#instruction-scheduling)
  documents its next-cycle restriction. The four moves can be issued
  together, then the consumer needs the appropriate separation.

Some instruction descriptions are shared with Wormhole and contain
Blackhole-specific exceptions. Scalar instruction issue, replay, pipeline
drains, source operand caches, and state initialization also affect the
observed cycles. Splitting accumulation across independent Dst blocks,
altering the SFPU shuffle schedule, replaying the finish, or processing
several tensors together are other candidates that this test does not
exhaustively search. Reduced-fidelity inputs also change the comparison.

## Worker-zero limitation

Worker index 0 initially passed the original benchmark and the first
transpose comparison, but later experimental sequences exposed persistent
incorrect results across fresh harness launches. The original unmodified
mean benchmark also failed its first GAPOOL case in that state. Explicit
counter, lane-config, and source-cache initialization in the new test did
not resolve this. The root cause is not established; no hardware-defect or
firmware-bug diagnosis is claimed. Failed worker-zero results are excluded
from performance claims. The final test passes on workers 1 and 2, with
matching times and the expected precision differences. This is why the
reproduction commands select those workers explicitly.
An [intermediate worker-zero failure log](sum-finish-core0-failure.log)
records this limitation; it predates the final three-path test.
