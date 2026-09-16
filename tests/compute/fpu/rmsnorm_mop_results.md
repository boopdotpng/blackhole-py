# Optimized hybrid RMSNorm: explicit ELWMUL versus MOP

Card 1, worker index 2 (`(1, 4)`), BF16 inputs/output and FP32 intermediates.
Both variants retain the optimized square and final-scale SFPU macros.

The untouched optimized hybrid was benchmarked first: the existing fair
2048-element comparison reported 1073.5 median L1-to-L1 cycles, compute
380.5, and pack 305.5 (queue job `38128e50c44a4dfeba75467e56f557ec`).

The more controlled before/after test alternates the explicit and MOP variants,
discards two warmups per variant, and measures 100 samples of each:

| Elements | Explicit ELWMUL, median cycles (range) | ELWMUL MOP, median cycles (range) | MOP change |
| --- | ---: | ---: | ---: |
| 2048 | 1055 (1031–1072) | 1102 (1077–1115) | 4.45% slower |
| 4096 | 1547.5 (1523–1561) | 1595 (1570–1608) | 3.07% slower |

The compute interval increased from 356 to 403 cycles at 2048 elements and
from 624 to 671 at 4096. Median packing was unchanged: 305 and 529 cycles,
respectively. Job: `fa8629306e0c4e369b0ad808e5f5dec1`.

These are L1-to-L1 measurements in the optimized raw harness, excluding initial
math/SFPU configuration, DRAM/NoC, and host launch overhead. All new MOP setup,
destination updates, and dispatch are inside the measured interval. The compute
interval starts after the first scratch copy, and includes staging later tiles.
Do not compare these totals directly against `rmsnorm_blog_results.md`, whose
total also includes initial math configuration and uses explicit SFPU math.

## Implementation

`emit_rmsnorm(..., elwmul_mop=True)` selects a native loop MOP with four outer
iterations (fidelity phases) and eight inner iterations (128-element blocks).
One TTMOP per tile replaces 32 explicitly issued ELWMUL instructions; the
hardware still executes all 32 multiplications. No replay is used.

Address modifiers advance Dst by eight rows between blocks, reset it at phase
boundaries, and advance/clear fidelity as in the explicit version. The template
is configured once, then its three ELWMUL destination operands are updated for
subsequent tiles. The SFPU scratch addressing and arithmetic order are preserved.
The initial implementation reconfigured all nine words each tile; it was slower
still (1105 versus 1052 cycles at 2048; 1609 versus 1547.5 at 4096).

MOP reduces instructions issued by TRISC1 but adds setup and loop-control work.
The measurements show no latency benefit here, so explicit ELWMUL remains the
default. This does not establish performance for longer or differently scheduled
kernels.

## Validation and reproduction

The raw comparison checks normal, increasing, small, zero, outlier, and large
inputs with signed nonconstant weights and different per-tile magnitudes.
Both variants produced bit-identical BF16 outputs; maximum relative error against
the float64 reference was 0.385858% (2048) and 0.386656% (4096). Output guards and
the unused scale-export region remained intact.

The actual `emit_rmsnorm` production path also passed at both sizes with DRAM
and circular-buffer transport, and explicit/MOP outputs matched bitwise
(job `0a25bbc4cbd84ccdb55ebf5b5a4ac0da`).

```sh
tt-device-queue run --device 1 --cwd "$PWD" -- \
  '../.venv/bin/python -m pytest -xq -s tests/compute/fpu/test_rmsnorm_hybrid.py -k elwmul_mop --bh-hardware --bh-device=1 --bh-core=2'
```
