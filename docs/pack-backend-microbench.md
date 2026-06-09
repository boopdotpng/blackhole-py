# Blackhole Pack Backend Microbench

Goal: measure focused TRISC2 pack backend costs that can feed a static
`Program` timing model for matmul-like kernels.

The harness lives in `examples/microbench_pack_backend.py`.

## Quick Read

Current scope:

- one active TRISC2 role per launch, using slow dispatch (`TT_USB=1`)
- 2x2 output subblocks (`4` BF16 tiles per pack subblock)
- real pack setup and body from `examples/matmul_peak.py`
- experimental standalone CB16/CB24 pack rows, gated behind
  `--allow-standalone-pack`
- safe default empty-loop smoke to validate launch/result plumbing
- real-pipeline constants from `matmul_peak.py` profile counters
- L1 result records at `0x12c000`

The pack body is `matmul_peak.emit_pack_tile_to_cb`, including CB reserve,
destination address programming, pack MOP trigger, per-tile `PC_BUF_SYNC`,
CB push, `TTZEROACC`, and `TTSEMGET`.

## How To Run

From `blackhole-py`:

```sh
PYTHONPATH=. TT_USB=1 /home/boop/tenstorrent/.venv/bin/python3 examples/microbench_pack_backend.py --iters 8
```

When running from Codex or another shared agent, submit the hardware command
through the Tenstorrent device queue.

Useful options:

- `--core X,Y`: choose the logical Tensix core.
- `--only NAME ...`: run a subset; `empty` is added automatically for baseline
  subtraction.
- `--allow-standalone-pack`: opt into the experimental pack-only rows. As of
  the run below, the CB16 pack row still times out without the full producer
  pipeline.
- `--no-report`: print results without appending this file.

## What This Measures

Each experimental standalone pack row builds a tiny one-core program with:

- CB16 and CB24 configured with BF16 tile pages
- pack init from `matmul_peak.MATMUL_PACK_MOP_CFG`
- two initial `TTZEROACC` operations so both destination halves are packable
- `MATH_PACK` initialized to `15`, limiting the default smoke to at most `15`
  iterations because `emit_pack_tile_to_cb` consumes one token per subblock

The table reports baseline-adjusted costs:

- `cyc/subblock adj`: row cycles per iteration minus the empty-loop cycles per
  iteration
- `cyc/tile adj`: adjusted subblock cycles divided by four output tiles
- `us/*`: cycles converted with `AICLK_MHZ = 1350.0`

## L1 Result Layout

| Range | Address | Size | Purpose |
|---|---:|---:|---|
| `pack_backend_microbench_results` | `0x12c000` | `128` bytes | header + one timing record |

Each launched spec writes one fixed header and one fixed-size record. The host
reads that L1 range after each launch and prints/appends the aggregate table.

## Static Model Hook

`examples/program_timing_model.py` currently has a coarse
`TRISC_CYCLES_PER_SUBBLOCK = 924.0`. The real-pipeline profile counters below
show pack alone is already much larger than that placeholder.

A first pack-aware split can use the measured constants as:

```text
partial_pack_cycles =
  cb24_partial_l1acc_off_room2x for block 0 +
  cb24_partial_l1acc_on_room2x for block 1 +
  cb24_partial_l1acc_on_no_reconfig_room2x for later partial blocks

final_pack_cycles =
  cb16_final_l1acc_off_room2x

pack_cycles_per_core =
  partial_subblocks * partial_pack_cycles +
  final_subblocks * final_pack_cycles
```

For the current matmul model, an immediate conservative plug-in is:

```text
TRISC_CYCLES_PER_SUBBLOCK = 6345.0
```

That is the measured average `trisc2_pack_body` cost per 2x2 subblock from the
two-block real matmul run. A more detailed role model should split:

```text
cb16_final_pack_cycles = 5265.0
cb24_partial_pack_l1acc_off_cycles = 7425.0
cb24_partial_pack_l1acc_on_cycles = 5265.0
```

The `cb24_partial_pack_l1acc_on_cycles` value is inferred by subtracting the
one-block and two-block totals from the three-block total, so treat it as a
first calibration point rather than a final invariant.

## Known Limitations

- The standalone pack rows are a producer-side smoke, not a full matmul
  pipeline. TRISC0/TRISC1 and NCRISC consumers are not active.
- The standalone CB16 row timed out even after adding math destination setup;
  the useful constants below therefore come from full `matmul_peak.py` profile
  counters.
- Output-CB pressure is represented by configured CB room. The smoke avoids
  intentional reserve stalls because there is no live consumer to release space.
- Destination contents are seeded by `TTZEROACC`, not by real math output.
- The loop does not measure the preceding `TTSEMWAIT`; it starts from a state
  equivalent to "math has made pack data available".
- The default iteration count is intentionally small to avoid semaphore
  underflow in this minimal harness.

## Run 2026-06-08T13:15:37-04:00

- Command: `examples/microbench_pack_backend.py --iters 8`
- Core: logical `1,2`
- Iterations per pack row: `8`
- Dispatch path: slow dispatch (`TT_USB=1`), one active TRISC2 role per launch
- Pack body: `matmul_peak.emit_pack_tile_to_cb`, 2x2 output subblock, BF16 tiles
- Baseline subtraction: adjusted rows subtract the `empty` loop cycles per iteration

Debug L1 ranges:
- `pack_backend_microbench_results` at `0x12c000` (128 bytes)

| test | mode | iters | cb pages | cycles | cyc/subblock adj | cyc/tile adj | us/subblock | us/tile | sink |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| empty | baseline | 8 | 4 | 58 | 0.0 | 0.0 | 0.000 | 0.000 | 0x50420008 |

## Standalone Pack Attempt 2026-06-08

Command through the Tenstorrent queue:

```sh
PYTHONPATH=. TT_USB=1 BLACKHOLE_RUN_TIMEOUT_S=5 \
  /home/boop/tenstorrent/.venv/bin/python3 examples/microbench_pack_backend.py \
  --iters 1 --only cb16_final_l1acc_off_room2x --no-report --allow-standalone-pack
```

Result: timed out waiting for core `(1,2)`. The empty row above proves the
launch/result path is working; the timeout is isolated to standalone pack
backend state. I left the pack-only rows implemented but opt-in.

## Real Pipeline Profile 2026-06-08

These commands ran through the Tenstorrent device queue with environment
variables supplied through the queue API:

```sh
PYTHONPATH=. TT_USB=1 MATMUL_PROFILE=1 MATMUL_PROFILE_DETAIL=1 \
  /home/boop/tenstorrent/.venv/bin/python3 examples/matmul_peak.py 256 256 128

PYTHONPATH=. TT_USB=1 MATMUL_PROFILE=1 MATMUL_PROFILE_DETAIL=1 \
  /home/boop/tenstorrent/.venv/bin/python3 examples/matmul_peak.py 384 384 384

PYTHONPATH=. TT_USB=1 MATMUL_PROFILE=1 MATMUL_PROFILE_DETAIL=1 \
  /home/boop/tenstorrent/.venv/bin/python3 examples/matmul_peak.py 384 384 576
```

All three runs printed profile counters, then failed validation on non-finite
padded outputs. The profile data was emitted before validation, so it is still
usable for timing-model calibration, but validation remains a gap.

| shape | blocks | pack path | `trisc2_pack_body` min us | avg us | max us | avg cycles total | avg cycles/subblock | avg cycles/tile |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| `256 256 128` | 1 | CB16 final, L1 acc off | 3.8 | 3.9 | 4.3 | 5265 | 5265 | 1316 |
| `384 384 384` | 2 | CB24 partial off + CB16 final | 8.5 | 9.4 | 9.9 | 12690 | 6345 | 1586 |
| `384 384 576` | 3 | CB24 partial off + CB24 partial on + CB16 final | 12.8 | 13.3 | 13.8 | 17955 | 5985 | 1496 |

Derived constants:

| constant | source | us/subblock | cycles/subblock | cycles/tile |
|---|---|---:|---:|---:|
| CB16 final pack, L1 acc off | one-block total | 3.9 | 5265 | 1316 |
| CB24 partial pack, L1 acc off | two-block total minus one-block total | 5.5 | 7425 | 1856 |
| CB24 partial pack, L1 acc on | three-block total minus two-block total | 3.9 | 5265 | 1316 |
| Generic pack body for coarse model | two-block average | 4.7 | 6345 | 1586 |
