# FP8 matmul with FP32 accumulation — Card 1, 2026-09-16

Implemented an opt-in FP32 mode in `examples/matmul_peak.py`:

```sh
~/.local/bin/tt-device-queue run --device 1 --cwd "$PWD" -- '../.venv/bin/python examples/matmul_peak.py --dtype fp8 --accumulation fp32 --device 1 --run --profile --runs 9'
```

**This first implementation produces FP32 output.** It does not yet support
FP32 accumulation followed by FP16 output. Existing FP8/FP16 and BF16 defaults
are unchanged. All hardware work used physical Card 1 through queue 1.

## Implementation

- FP8 E4M3 storage still expands to FP16 source registers and uses one matrix
  fidelity phase. FP32 changes destination accumulation, not the input format.
- Enables the hardware FP32 Dst accumulator. Each double-buffered Dst half now
  contains four tiles, with half bases 0/256 instead of 0/512. Default subblock
  changes from 2×4 to 1×4; larger-than-four-tile FP32 subblocks are rejected.
- Packs partials to 4096-byte FP32 tiles and performs subsequent K-block
  accumulation in FP32 L1 storage. The last block also uses packer L1
  accumulation. This avoids the old final-block reload through SrcA/MOVA2D,
  which would not preserve full FP32 partials.
- Updates packer strides, half offsets, Dst invalidation, output allocation,
  NoC tile addresses, host decoding, and L1 capacity planning for FP32.
- Block zero overwrites the partial buffer on each invocation; later blocks
  add. Completion and CB ownership remain explicit. The final output aliases
  the partial buffer, avoiding a second full output-sized L1 allocation.
- FP32 numerical validation requires relative L2 error ≤0.001, stricter than
  the existing 16-bit path's limit. This is the hardware's FP32 accumulation
  mode, not a claim of bitwise IEEE FP32 GEMM equivalence.

## Performance and error

5000×5000×5000, 110 compute cores, split NoCs with the earlier preferred-port
fix. Nine timed repetitions per run after warmup. Logical (unpadded) TFLOP/s:

| Input / accumulation / output | Subblock | K block | Mean µs | TFLOP/s | Relative L2 |
|---|---|---:|---:|---:|---:|
| FP8 / FP16 / FP16 (default) | 2×4 | 10 | 737.04 | 339.20 | 0.005204 |
| FP8 / FP32 / FP32 (new default) | 1×4 | 4 | 1280.41 | 195.25 | 0.000076 |
| FP8 / FP32 / FP32 | 2×2 | 4 | 1283.87 | 194.72 | 0.000076 |
| FP8 / FP16 / FP16 (matched blocking) | 1×4 | 4 | 977.98 | 255.63 | 0.003754 |
| BF16 / BF16 / BF16 (default regression) | 2×4 | 6 | 1369.56 | 182.54 | 0.010349 |

An earlier FP32 run measured 1280.05 µs / 195.30 TFLOP/s. The result is
repeatable, but the table is not an isolated measurement of FPU FP32 cost:
FP32 output doubles DRAM write traffic, FP32 partials double output L1 storage
and packing traffic, and the default plan fits K block 4 instead of 10.
The matched-blocking row separates some of the planning effect, but still
changes partial/output precision and final-block accumulation strategy.

Last-run maximum per-role intervals for the new default: math 982.46 µs,
packer 983.25 µs, output writer 337.97 µs. The FP16 default had math 616.31 µs,
packer 616.75 µs, writer 175.86 µs. These intervals overlap and must not be added.

The error is relative to the decoded, quantized FP8 inputs. It does not include
input quantization error versus original unquantized values or establish
model-level inference accuracy. Large-matrix validation samples output values;
the dedicated small correctness cases compare the full logical output.

## Correctness

Ten hardware tests pass, each executing its program twice to check reuse:

- K=32/64/96/257 with one-tile K blocks, 1×4 and 2×2 subblocks, M=65/N=129.
  These cover one, two, three and nine K blocks, both Dst halves, CB wrapping,
  and M/N/K fringes. Full outputs have relative L2 error below 0.0003.
- Exactly representable FP8 cancellation:
  `2048 + 2048*(1/64)^2 - 2048 = 0.5` across 24 K blocks.
  FP32 returns exactly 0.5 in every output; the FP16 comparison loses at least
  0.25. This checks partial-sum preservation, not just FP32 output encoding.
- `64 * 448 * 448 = 12,845,056`, beyond FP16's finite range, is exact and finite.

Also validated the multicore 128³ single-block case, irregular
M=1025/N=769/K=513, and the default 5000³ benchmark.

```sh
~/.local/bin/tt-device-queue run --device 1 --cwd "$PWD" -- '../.venv/bin/python -m pytest tests/compute/fpu/test_matmul_peak_fp32.py --bh-hardware --bh-device=1 -q'
```

Queue logs: comparison `0e34c2f765bb4a5e930e9fffb946a53c`, matched blocking
`22c0950fae7840a0905d0235b01bc80a`, tests `44da7a212fb5476f98b976e9ab8acf7d`.
