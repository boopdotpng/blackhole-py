# Blackhole Math Backend Microbench

Goal: measure TRISC1 math backend costs that can feed a static Program timing
model, using the matmul MOP/replay sequence from `examples/matmul_peak.py`.

The harness lives in `microbenching/tensix/microbench_math_backend.py`.

## Scope

- one active TRISC1 role on one Tensix core
- one fresh device launch per measured row, because isolated MVMUL state is not
  reusable across rows
- result records in L1 at `0x129000`
- BF16 matmul math initialization copied from `matmul_peak.py`
- unthrottled and `MATMUL_THROTTLE0` MOP/replay templates, measured as
  one-shot rows from fresh/reset device state
- rows for math init, MOP programming, and one output-tile K step

Hardware-touching runs from Codex should go through the Tenstorrent device
queue.

## How To Run

From `blackhole-py`:

```sh
PYTHONPATH=. TT_USB=1 /home/boop/tenstorrent/.venv/bin/python3 microbenching/tensix/microbench_math_backend.py --iters 100
PYTHONPATH=. TT_USB=1 /home/boop/tenstorrent/.venv/bin/python3 microbenching/tensix/microbench_math_backend.py --iters 1 --tests empty,mop_tile_unthrottled
PYTHONPATH=. TT_USB=1 /home/boop/tenstorrent/.venv/bin/python3 microbenching/tensix/microbench_math_backend.py --iters 1 --tests empty,mop_tile_throttle0
```

Run the MOP tile commands from a fresh/reset device state. In Codex, use the
Tenstorrent device queue reset between those commands.

Useful options:

- `--core X,Y`: choose the logical Tensix core.
- `--iters N`: raise for safe rows after a smoke run completes; backend MOP rows
  are one-shot.
- `--no-report`: print without appending this document.

## Interpretation

The timing table subtracts the `empty` loop row from each row and reports:

- adjusted cycles and microseconds per iteration
- adjusted cycles per MOP trigger for MOP-bearing rows
- adjusted cycles per output-tile-K step for one-tile rows
- derived cycles per 2x2 output subblock in the proposed constants table

The isolated rows prepare source/dest state with `TTZEROSRC`, `TTZEROACC`, and
`TTSETRWC`, then drain with `PC_BUF_SYNC` and
`TTSTALLWAIT(SYNC, MATH|SFPU)`. They intentionally avoid pack/unpack CB traffic.

A true four-tile subblock with one source prep currently does not drain without
TRISC0/unpack participation; source-valid state is not reusable enough in this
isolated setup. A second isolated output-tile K step in the same launch also
hangs, including loop iterations inside one launch. The benchmark therefore
keeps only the minimal known-good isolated smoke: one matmul output-tile K step
per launch, with realistic math init and completion/drain. Backend-mutating rows
are capped to one iteration even when `--iters` is larger.
A full true-subblock fallback should come from `examples/matmul_peak.py` profile
counters and must document that it includes its dependencies.

## Proposed Timing-Model Mapping

For `microbenching/models/program_timing_model.py`, the most direct constant is:

- `TRISC_CYCLES_PER_SUBBLOCK`: use `4 * mop_tile_unthrottled` for the current
  2x2 subblock model until a true multi-tile isolated row can be made to drain.

The one-output-tile rows are useful for future finer models:

- per output-tile-K, unthrottled: `mop_tile_unthrottled` cycles/tile-K
- per output-tile-K, throttle0: `mop_tile_throttle0` cycles/tile-K

## Run 2026-06-08T13:18:21-04:00

- Command: `PYTHONPATH=. TT_USB=1 /home/boop/tenstorrent/.venv/bin/python3 microbenching/tensix/microbench_math_backend.py --iters 20`
- Core: logical `1,2`
- Iterations per test: `20`
- Dispatch path: slow dispatch (`TT_USB=1`), one active TRISC1 role
- Drain marker: `PC_BUF_SYNC` plus `TTSTALLWAIT(SYNC, MATH|SFPU)` for math rows
- Math sequence: `examples/matmul_peak.py` matmul MOP cfg/replay payloads

| test | variant | group | cycles/iter | adj cycles | adj us | cycles/MOP | cycles/tile-K | cycles/subblock |
|---|---|---|---:|---:|---:|---:|---:|---:|
| empty | unthrottled | baseline | 5.30 | 0.00 | 0.0000 |  |  |  |
| sync_empty | unthrottled | sync | 13.25 | 7.95 | 0.0059 |  |  |  |
| prep_src | unthrottled | prep | 21.70 | 16.40 | 0.0121 |  |  |  |
| math_init_unthrottled | unthrottled | init | 271.00 | 265.70 | 0.1968 |  |  |  |
| program_mop_unthrottled | unthrottled | program_mop | 106.00 | 100.70 | 0.0746 |  |  |  |
| math_init_throttle0 | throttle0 | init | 290.00 | 284.70 | 0.2109 |  |  |  |
| program_mop_throttle0 | throttle0 | program_mop | 115.00 | 109.70 | 0.0813 |  |  |  |

Proposed constants:

| constant | cycles | us @ 1.35 GHz |
|---|---:|---:|

## Run 2026-06-08T13:18:44-04:00

- Command: `PYTHONPATH=. TT_USB=1 /home/boop/tenstorrent/.venv/bin/python3 microbenching/tensix/microbench_math_backend.py --iters 1 --tests empty,mop_tile_unthrottled`
- Core: logical `1,2`
- Iterations per test: `1`
- Dispatch path: slow dispatch (`TT_USB=1`), one active TRISC1 role
- Drain marker: `PC_BUF_SYNC` plus `TTSTALLWAIT(SYNC, MATH|SFPU)` for math rows
- Math sequence: `examples/matmul_peak.py` matmul MOP cfg/replay payloads

| test | variant | group | cycles/iter | adj cycles | adj us | cycles/MOP | cycles/tile-K | cycles/subblock |
|---|---|---|---:|---:|---:|---:|---:|---:|
| empty | unthrottled | baseline | 26.00 | 0.00 | 0.0000 |  |  |  |
| mop_tile_unthrottled | unthrottled | mop_tile | 80.00 | 54.00 | 0.0400 | 27.00 | 54.00 |  |

Proposed constants:

| constant | cycles | us @ 1.35 GHz |
|---|---:|---:|
| `mop_tile_unthrottled_cycles_per_output_tile_k` | 54.00 | 0.0400 |
| `program_timing_model_TRISC_CYCLES_PER_SUBBLOCK` | 216.00 | 0.1600 |

## Run 2026-06-08T13:19:01-04:00

- Command: `PYTHONPATH=. TT_USB=1 /home/boop/tenstorrent/.venv/bin/python3 microbenching/tensix/microbench_math_backend.py --iters 1 --tests empty,mop_tile_throttle0`
- Core: logical `1,2`
- Iterations per test: `1`
- Dispatch path: slow dispatch (`TT_USB=1`), one active TRISC1 role
- Drain marker: `PC_BUF_SYNC` plus `TTSTALLWAIT(SYNC, MATH|SFPU)` for math rows
- Math sequence: `examples/matmul_peak.py` matmul MOP cfg/replay payloads

| test | variant | group | cycles/iter | adj cycles | adj us | cycles/MOP | cycles/tile-K | cycles/subblock |
|---|---|---|---:|---:|---:|---:|---:|---:|
| empty | unthrottled | baseline | 26.00 | 0.00 | 0.0000 |  |  |  |
| mop_tile_throttle0 | throttle0 | mop_tile | 75.00 | 49.00 | 0.0363 | 49.00 | 49.00 |  |

Proposed constants:

| constant | cycles | us @ 1.35 GHz |
|---|---:|---:|
| `mop_tile_throttle0_cycles_per_output_tile_k` | 49.00 | 0.0363 |
