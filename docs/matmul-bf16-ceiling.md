# Blackhole BF16 Matmul Ceiling Notes

Goal: keep the current back-of-envelope BF16 matmul ceiling tied to the
`blackhole-py` matmul implementation and the microbench assumptions.

## Assumptions

- Debug wall clock: `1350 MHz`
- BF16 tile shape: `32x32`
- BF16 tile bytes: `2048`
- One full `32x32 @ 32x32` output tile product is `65536` FLOPs.
- One full tile product decomposes into eight `16x16x16` MVMULs.
- One MVMUL takes `16` cycles.

That gives:

- Tile product math time: `8 * 16 = 128` cycles
- Per-core math rate: `65536 / 128 = 512 FLOP/cycle`
- Per-core BF16 rate at `1350 MHz`: about `0.691 TFLOP/s`

## `384x384x384`

The default `examples/matmul_peak.py` size is `384x384x384`. The current planner
uses a `6x6` grid, or `36` active cores, with:

- `Mt=12 Kt=12 Nt=12`
- `per_core_M=2`
- `per_core_N=2`
- `in0_block_w=6`
- `num_blocks=2`

Each core computes four output tiles across twelve K tiles:

- Cycles per output tile: `12 * 128 = 1536`
- Cycles per core: `4 * 1536 = 6144`
- Ideal math-only time at `1350 MHz`: about `4.55 us`
- Total work: `2 * 384 * 384 * 384 = 113246208` FLOPs
- Current-planner math ceiling: about `24.88 TFLOP/s`

This is not an all-core ceiling. The size has only `12 * 12 = 144` output tiles,
and the current implementation assigns `2x2` output tiles per core.

## Measured Run

Command:

```sh
PYTHONPATH=. python3 examples/matmul_peak.py 384 384 384
```

Result:

- Active cores: `36`
- Available program cores: `118`
- Runtime: `271.6 us`
- Measured throughput: `0.42 TFLOP/s`
- Validation: `PCC=0.999942`, `rel_l2=0.012545`

This is far below the `24.88 TFLOP/s` math-only ceiling above. At this size and
with the current Python/handwritten matmul pipeline, the bottleneck is not raw
MVMUL throughput. The current result includes dataflow overheads such as tile
reads, multicast, unpack/math/pack synchronization, output writeback, and launch
or dispatch timing.

## Larger-Core Ceilings

Using the same `512 FLOP/cycle/core` assumption:

| active cores | BF16 math ceiling |
|---:|---:|
| 36 | `24.88 TFLOP/s` |
| 118 | `81.56 TFLOP/s` |
| 120 | `82.94 TFLOP/s` |
| 138 | `95.39 TFLOP/s` |
| 140 | `96.77 TFLOP/s` |

Fast dispatch reserves two program cores, so a P100a run normally has `118`
program cores and a P150 run normally has `138` program cores.

## DRAM Traffic At This Size

For `384x384x384`, the minimum BF16 traffic for A, B, and C is:

- A: `384 * 384 * 2 = 294912` bytes
- B: `384 * 384 * 2 = 294912` bytes
- C: `384 * 384 * 2 = 294912` bytes
- Total: `884736` bytes, or `0.844 MiB`

At the `36`-core math-only ceiling of `24.88 TFLOP/s`, this only requires about
`194 GB/s` of DRAM bandwidth. So for this exact size, DRAM bandwidth should not
be the first bottleneck if A and B are each streamed once and multicast/reused as
intended. Launch overhead, pack/unpack, mcast, synchronization, and output write
latency are more likely to show up before raw DRAM bandwidth.

For larger square matmuls, the minimum arithmetic intensity is approximately
`S / 3` FLOP/byte for BF16 A/B/C traffic, assuming each input is read once and C
is written once. DRAM traffic is unavoidable, but the matmul can still be
compute-limited once tile reuse and multicast are working well.
