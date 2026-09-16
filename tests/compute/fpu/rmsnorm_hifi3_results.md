# HiFi3 and aligned RMSNorm timings

HiFi3 exists in Blackhole's LLK `MathFidelity` enum. For BF16 it executes
phases 0, 1, and 2, omitting phase 3 (SrcA's low three significand bits times
SrcB's lowest significand bit). ELWMUL count drops from 32 to 24 per tile.
The SFPU square sum, reduction, and reciprocal square root are unchanged.

The production emitter accepts `fidelity=3`; default remains 4. Both explicit
and MOP issuance support it. Production transport/output checks passed for
both fidelities, both issuance modes, and both 2048/4096 elements.

## Same timing boundary for all implementations

The previously quoted 1055 optimized cycles excluded initial math/SFPU setup,
whereas the article benchmark's 1306 included it. They were not directly
comparable. The explicit/MOP pair (1055/1102) did share identical boundaries.

`test_matched_optimized_comparison` now starts each total before initial math
configuration and ends after BF16 output is packed into L1. It includes setup,
unpack, moves, math, synchronization, and packing; excludes host/firmware launch
and DRAM/NoC. All variants use identical input data, card 1/core index 2,
two warmups and 100 measured runs, reversing execution order every round.

| 2048-element kernel | Median cycles | Min–max |
| --- | ---: | ---: |
| Article SFPU | 1508.5 | 1450–1566 |
| Article hybrid HiFi4 | 1330 | 1292–1378 |
| Optimized hybrid HiFi4 | 1111 | 1083–1145 |
| Optimized hybrid HiFi3 | 1083 | 1060–1098 |
| Optimized hybrid HiFi4 + ELWMUL MOP | 1146 | 1123–1162 |

Use this table for comparisons across implementations. These totals describe
the full measured implementations, including their different internal
synchronization/instrumentation; they do not isolate the cost of a single
instruction optimization. Min/max ranges show run variation, not confidence
intervals. Job: `8faa719cec244b2cb8015bd9c38cd891`.

## Controlled HiFi4/HiFi3 comparison

Using the original optimized harness boundary (initial math setup excluded):

| Elements | HiFi4 median | HiFi3 median | Fewer cycles |
| --- | ---: | ---: | ---: |
| 2048 | 1056.5 | 1030.5 | 2.46% |
| 4096 | 1547 | 1513.5 | 2.17% |

These also use two warmups, 100 samples and alternating order. Cutting 25% of
ELWMUL instructions saves much less than 25% of the entire kernel.

Accuracy checks cover normal, small, large and zero inputs, and all 16,384
BF16 significand pairs in [1,2), divided across vectors. References use float64
on BF16-quantized inputs. All output and unused-scale guards passed.

| Metric | 2048 | 4096 |
| --- | ---: | ---: |
| Worst output relative error, HiFi4 | 0.388026% | 0.386037% |
| Worst output relative error, HiFi3 | 0.406132% | 0.408827% |
| Changed BF16 outputs on normal case | 28/2048 | 51/4096 |
| Normal relative L2 error, HiFi4 | 0.158556% | 0.167536% |
| Normal relative L2 error, HiFi3 | 0.159092% | 0.167774% |
| Normal relative L2 difference between outputs | 0.069454% | 0.057102% |

A small intermediate error can cross a BF16 rounding boundary: the largest
observed elementwise HiFi3–HiFi4 delta divided by the reference was about
0.7782%. No model-level inference quality evaluation was performed.
Job: `ebd0c70baea24a0180c0944e67c485c6`.

## Reproduce

```sh
tt-device-queue run --device 1 --cwd "$PWD" -- \
  '../.venv/bin/python -m pytest -xq -s tests/compute/fpu/test_rmsnorm_blog.py -k matched --bh-hardware --bh-device=1 --bh-core=2'
tt-device-queue run --device 1 --cwd "$PWD" -- \
  '../.venv/bin/python -m pytest -xq -s tests/compute/fpu/test_rmsnorm_hybrid.py -k "hifi3 or elwmul_mop_production" --bh-hardware --bh-device=1 --bh-core=2'
```

References: [Blackhole LLK enum](https://github.com/tenstorrent/tt-llk/blob/main/tt_llk_blackhole/llk_lib/llk_defs.h),
[BF16 fidelity phase table](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/SrcASrcB.md#fidelity-phases-floating-point).
