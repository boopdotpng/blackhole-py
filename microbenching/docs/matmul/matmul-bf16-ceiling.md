# Blackhole BF16 Matmul Ceiling Notes

Goal: keep the current back-of-envelope BF16 matmul ceiling tied to the
`blackhole-py` matmul implementation and the microbench assumptions.

## Assumptions

- AICLK under load: `1350 MHz` (telemetry confirms boost from 800 MHz idle)
- BF16 tile shape: `32x32`
- BF16 tile bytes: `2048`
- One full `32x32 @ 32x32` output tile product is `65536` FLOPs.
- The throttle0 replay payload encodes `16` `TTMVMUL` slots per output-tile
  K step; at LoFi the FPU retires one encoded slot per cycle
  (`8x16x16 = 2048` MACs/cycle).

That gives:

- Tile product math time at LoFi: `16` cycles
- Per-core math rate at LoFi: `65536 / 16 = 4096 FLOP/cycle`
- Per-core BF16 LoFi rate at `1350 MHz`: about `5.53 TFLOP/s`
- HiFi2 doubles the fidelity phases: `32` cycles/tile, `2048 FLOP/cycle`,
  about `2.76 TFLOP/s` per core. HiFi4 halves that again.

Cross-check: `140 cores * 4096 FLOP/cycle * 1.35 GHz = 774 TFLOP/s`, which
matches Tenstorrent's published p150 FP8 (LoFi) figure, so `4096
FLOP/cycle/core` is the right per-core constant.

The original version of this note assumed one architectural `16x16x16` MVMUL
takes `16` cycles (`128` cycles/tile, `512 FLOP/cycle/core`, `0.691
TFLOP/s/core`). That is `8x` too low: measured end-to-end DRISC runs exceed
that ceiling by `~4x`. See `math-mvmul.md` for the
encoded-slot-vs-architectural-MVMUL unit reconciliation; numbers below that
were derived from the `512 FLOP/cycle` model carry a `[stale 8x-low]` tag.

## `384x384x384`

The default `examples/matmul_peak.py` size is `384x384x384`. The current planner
uses a `6x6` grid, or `36` active cores, with:

- `Mt=12 Kt=12 Nt=12`
- `per_core_M=2`
- `per_core_N=2`
- `in0_block_w=6`
- `num_blocks=2`

Each core computes four output tiles across twelve K tiles (LoFi):

- Cycles per output tile: `12 * 16 = 192`
- Cycles per core: `4 * 192 = 768`
- Ideal math-only time at `1350 MHz`: about `0.57 us`
- Total work: `2 * 384 * 384 * 384 = 113246208` FLOPs
- Current-planner LoFi math ceiling: about `199 TFLOP/s` (HiFi2: `99.5`)
- At this size launch overhead dominates; the ceiling is unreachable.

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

This is far below the math-only ceiling above. At this size and
with the current Python/handwritten matmul pipeline, the bottleneck is not raw
MVMUL throughput. The current result includes dataflow overheads such as tile
reads, multicast, unpack/math/pack synchronization, output writeback, and launch
or dispatch timing.

## Larger-Core Ceilings

Using `4096 FLOP/cycle/core` (LoFi) at `1350 MHz`; HiFi2 is half of each row:

| active cores | BF16 LoFi math ceiling | BF16 HiFi2 |
|---:|---:|---:|
| 36 | `199 TFLOP/s` | `99.5 TFLOP/s` |
| 110 | `608 TFLOP/s` | `304 TFLOP/s` |
| 118 | `652 TFLOP/s` | `326 TFLOP/s` |
| 120 | `663 TFLOP/s` | `332 TFLOP/s` |
| 138 | `763 TFLOP/s` | `381 TFLOP/s` |
| 140 | `774 TFLOP/s` | `387 TFLOP/s` |

The `110`-core row is the DRISC fixed-5000 worker rectangle; the measured
`~300 TFLOP/s` LoFi run is about `49%` of that LoFi ceiling.

Fast dispatch reserves two program cores, so a P100a run normally has `118`
program cores and a P150 run normally has `138` program cores.

## DRAM Traffic At This Size

For `384x384x384`, the minimum BF16 traffic for A, B, and C is:

- A: `384 * 384 * 2 = 294912` bytes
- B: `384 * 384 * 2 = 294912` bytes
- C: `384 * 384 * 2 = 294912` bytes
- Total: `884736` bytes, or `0.844 MiB`

At the `36`-core LoFi math-only ceiling of `199 TFLOP/s`, this requires about
`1.5 TB/s` of DRAM bandwidth, far above the card. The real limit at this size
is launch overhead, not DRAM. So for this exact size, DRAM bandwidth should not
be the first bottleneck if A and B are each streamed once and multicast/reused as
intended. Launch overhead, pack/unpack, mcast, synchronization, and output write
latency are more likely to show up before raw DRAM bandwidth.

For larger square matmuls, the minimum arithmetic intensity is approximately
`S / 3` FLOP/byte for BF16 A/B/C traffic, assuming each input is read once and C
is written once. DRAM traffic is unavoidable, but the matmul can still be
compute-limited once tile reuse and multicast are working well.
