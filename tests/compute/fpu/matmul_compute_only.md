# Resident-source MVMUL throughput — Card 1, 2026-09-16

**607.85 TFLOPS on matmul_peak's 110-core grid**, measured on physical Card 1
at an ARC-reported 1350 MHz. 117 workers reach **646.56 TFLOPS**.

| Active cores | MVMUL instructions per core | Median completed interval | Arithmetic TFLOPS |
|---:|---:|---:|---:|
| 1 | 571,851 | 423.624 us | 5.5292 |
| 110 | 571,851 | 423.879 us | 607.847 |
| 117 | 571,851 | 423.859 us | 646.557 |

Seven measured launches after warmup. The global interval spans the earliest
math start through latest completed math end. Single-core duration is 571,893
cycles for 571,851 MVMUL instructions: essentially one instruction per cycle.
The multicore interval includes roughly 0.25 us of start skew.

## What this measures

The current 5000^3 FP8/FP16 matmul computes padded extents 5040 x 5008 x 5104
on 110 cores. Each core owns 504 x 464 outputs. A one-phase MVMUL performs
8 x 16 x 16 multiply-adds, or 4096 FLOPs, so the required arithmetic count is:

```
2 * 504 * 464 * 5008 / 4096 = 571,851 MVMUL instructions per core
```

FP8 E4M3FN operands are loaded once into SrcA/SrcB and expanded to FP16 before
timing. The timed kernel reuses those resident values, rotating across 32
independent 8x16 Dst regions with FP16 accumulation. It runs exactly the above
instruction count through replay/MOP, then drains math before the end stamp.
Packing to L1 for validation happens after timing. BRISC and NCRISC perform
no benchmark data movement. No DRAM traffic, input unpacking, output packing,
CB waits, or producer/consumer handoffs occur inside the timed interval.
Small replay dispatch, tail setup, and timestamp/completion overhead remain.

This preserves the **MVMUL operation count and accumulation precision**, not
the production kernel's complete instruction schedule, source-bank changes,
edge addressing, or intermediate-result handling. It is not a numerical
5000^3 GEMM, and does not claim the production kernel currently delivers this
throughput during its math-controller interval.

## Validation

Inputs are FP8-encoded 1/64; each MVMUL adds 1/256 to its 128 destination
values. Every output on every active core is checked after every measured
launch. Short workloads of 512, 8192, and 16384 instructions verify exact
unsaturated accumulation and multiple MOP groups. The long run reaches the
expected FP16 rounding plateau of 8; that check alone is not an exact dynamic
instruction counter. The instruction construction and measured cycle count
provide additional evidence for the long operation count.

All 12 configurations (four instruction counts x three core counts) passed,
84 measured launches. MOP inner counts are limited to 256 in the emitter;
a larger initial template silently truncated during bring-up and failed
validation. The corrected benchmark issues multiple groups and an exact tail.

## Relation to the full kernel

The 110-core arithmetic ceiling is 608.256 TFLOPS. Measured arithmetic
throughput is 99.93% of it. Counting only the original 250 GFLOPs, rather
than 257.653 GFLOPs including padding, gives **589.79 logical TFLOPS**.

The earlier full-kernel profile finishes compute/packing around 618.02 us,
then finishes output around 737.34 us. Compared with this arithmetic-only
423.88 us, approximately 194 us precedes pack completion outside the minimum
arithmetic time, followed by a 119 us output tail. This comparison identifies
headroom; it does not separately attribute those 194 us to unpack, scheduling,
partial-result traffic, synchronization, or input starvation. FP16 MVMUL
execution itself is capable of the expected rate.

## Reproduce

From blackhole-py:

```sh
tt-device-queue run --device 1 --cwd "$PWD" -- '../.venv/bin/python tests/compute/fpu/bench_matmul_compute_only.py --device 1 --counts 512 8192 16384 571851 --json tests/compute/fpu/matmul_compute_only.json'
```

Raw results: `matmul_compute_only.json`. Production kernel unchanged.
