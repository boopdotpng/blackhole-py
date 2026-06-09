# Unpack Backend Microbenchmark

Focused Blackhole TRISC0 unpack-backend timing for static `Program` timing models.

## Commands

All hardware-touching commands were run through the Tenstorrent device queue from `/home/boop/tenstorrent/blackhole-py` with:

```bash
PYTHONDONTWRITEBYTECODE=1 TT_USB=1 /home/boop/tenstorrent/.venv/bin/python3 examples/microbench_unpack_backend.py ...
```

Successful measurement commands:

```bash
/home/boop/tenstorrent/.venv/bin/python3 examples/microbench_unpack_backend.py --iters 10 --bw 1 --no-reload --only matmul_2x2_bw1 --no-report
/home/boop/tenstorrent/.venv/bin/python3 examples/microbench_unpack_backend.py --iters 10 --bw 2 --no-reload --only matmul_2x2_bw2 --no-report
/home/boop/tenstorrent/.venv/bin/python3 examples/microbench_unpack_backend.py --iters 10 --bw 3 --no-reload --only matmul_2x2_bw3 --no-report
/home/boop/tenstorrent/.venv/bin/python3 examples/microbench_unpack_backend.py --iters 10 --bw 4 --no-reload --only matmul_2x2_bw4 --no-report
/home/boop/tenstorrent/.venv/bin/python3 examples/microbench_unpack_backend.py --iters 10 --bw 5 --no-reload --only matmul_2x2_bw5 --no-report
/home/boop/tenstorrent/.venv/bin/python3 examples/microbench_unpack_backend.py --iters 5 --bw 6 --no-reload --only matmul_2x2_bw6 --no-report
/home/boop/tenstorrent/.venv/bin/python3 examples/microbench_unpack_backend.py --iters 10 --bw 1 --only reload_recfg_2x2 --no-report
/home/boop/tenstorrent/.venv/bin/python3 examples/microbench_unpack_backend.py --iters 10 --bw 1 --no-reload --only matmul_unpack_row --no-report
/home/boop/tenstorrent/.venv/bin/python3 examples/microbench_unpack_backend.py --iters 10 --bw 1 --no-reload --only pc_unpack_sync_poll,pc_unpack_sync_write,cfg_context_flip_setc16,stallwait_unpack_trisc_cfg --no-report
```

Device resets were queued after timeout experiments before continuing measurement.

## Setup

- Core: logical `(1,2)`.
- AICLK conversion: `1350 MHz`, so `us = cycles / 1350`.
- Timed role: TRISC0.
- Companion role: TRISC1 runs an untimed `TTSETRWC(clear_ab_vld=3, BitMask=3)` loop until TRISC0 writes a done flag. This substitutes for math-side SRCA/SRCB consumption so isolated unpack rows do not backpressure forever.
- Empty BRISC, NCRISC, and TRISC2 kernels.
- Unpack setup reuses `examples/matmul_peak.py` constants: `MATMUL_UNPACK_AB_MOP_CFG`, replay slots `0` and `6`, `MATMUL_UNPACK_REPLAY{0,1}_LOAD`, `MATMUL_UNPACK_SRCB_LOAD`, `PC_UNPACK_SYNC`, and `UNPACK_MISC_CFG_CfgContext`.

## Control Costs

| test | cycles/iter | adjusted cycles | us/iter | note |
|---|---:|---:|---:|---|
| `pc_unpack_sync_poll` | 10.80 | 4.20 | 0.0031 | Poll `PC_UNPACK_SYNC` and mask off bit 0. |
| `pc_unpack_sync_write` | 6.20 | -0.40 | -0.0003 | Loop noise; treat as ~0 by itself. |
| `cfg_context_flip_setc16` | 16.10 | 9.50 | 0.0070 | Local context word toggle plus `SETC16`. |
| `stallwait_unpack_trisc_cfg` | 6.20 | -0.40 | -0.0003 | Loop noise when no pending cfg transaction. |

Standalone direct stores to unpack cfg registers outside the full `PC_UNPACK_SYNC`/`TTSTALLWAIT`/unpack protocol timed out, so cfg base-register stores are measured as part of the row/subblock path below.

## Unpack Rows And Subblocks

Each matmul-style unpack row performs the path from `examples/matmul_peak.py`: poll `PC_UNPACK_SYNC`, compute two L1 tile base addresses, write THCON sec0/sec1 cfg base registers for the active context, write `PC_UNPACK_SYNC`, issue `TTSTALLWAIT(UNPACK, TRISC_CFG)`, issue `TTUNPACR`, issue `TTMOP` to replay the two in1 `TTREPLAY` payloads, `TTSEMGET(UNPACK_SYNC)`, then flip cfg context.

For a 2x2 output subblock, rows per subblock are `2 * bw`, and unpack tiles per row are counted as 3: one in0 tile via explicit `TTUNPACR`, plus two in1 tiles through replay.

| test | iters | bw | cycles/subblock | cycles/row | cycles/unpack tile | us/subblock |
|---|---:|---:|---:|---:|---:|---:|
| `matmul_2x2_bw1` | 10 | 1 | 74.60 | 37.30 | 12.43 | 0.0553 |
| `matmul_2x2_bw2` | 10 | 2 | 149.90 | 37.48 | 12.49 | 0.1110 |
| `matmul_2x2_bw3` | 10 | 3 | 224.50 | 37.42 | 12.47 | 0.1663 |
| `matmul_2x2_bw4` | 10 | 4 | 300.00 | 37.50 | 12.50 | 0.2222 |
| `matmul_2x2_bw5` | 10 | 5 | 375.40 | 37.54 | 12.51 | 0.2781 |
| `matmul_2x2_bw6` | 5 | 6 | 487.40 | 40.62 | 13.54 | 0.3610 |

The standalone single-row test measured `51.30` adjusted cycles/row (`0.0380 us`). For throughput modeling, the subblock-derived row cost is more useful because it reflects the steady path inside the unrolled 2x2 subblock body.

## Reload-Unpack

| test | iters | cycles/2x2 reload | cycles/reload tile | us/2x2 reload | note |
|---|---:|---:|---:|---:|---|
| `reload_recfg_2x2` | 10 | 273.90 | 68.47 | 0.2029 | Includes reload MOP config, four reload tiles, `tensix_sync`, and restore to AB MOP. |

This is a control-path proxy for the reload path in `examples/matmul_peak.py`; no real cb24 producer is active.

## Proposed Constants

For `examples/program_timing_model.py`, split the current single TRISC estimate into unpack/backend pieces:

| constant | value | use |
|---|---:|---|
| `UNPACK_BACKEND_STEADY_ROW_CYCLES` | 37.5 | Throughput row cost inside 2x2 subblocks for bw 1..5. |
| `UNPACK_BACKEND_STANDALONE_ROW_CYCLES` | 51.3 | Conservative standalone row cost for non-amortized paths. |
| `UNPACK_BACKEND_2X2_BW4_CYCLES` | 300.0 | Direct measured 2x2 subblock cost for the common bw=4 case. |
| `UNPACK_BACKEND_RELOAD_2X2_CYCLES` | 273.9 | Last-K reload-unpack 2x2 proxy, including MOP reconfig/restore. |
| `UNPACK_BACKEND_CONTEXT_FLIP_CYCLES` | 9.5 | Local context toggle and `SETC16`, if modeled separately. |
| `UNPACK_BACKEND_PC_SYNC_POLL_CYCLES` | 4.2 | Ready-poll loop when the backend is already ready. |

Suggested model formula for the current fixed 2x2 subblock matmul path:

```text
unpack_cycles_per_2x2_subblock(bw) = 37.5 * (2 * bw)
reload_cycles_per_last_k_subblock = 273.9
```

For bw=6, the direct measurement was higher (`487.4 cycles`) than the linear formula (`450 cycles`); use the direct table value if modeling bw=6 specifically.

## Stability Notes

- Combined sweeps such as `--iters 100 --bw 1 2 3 4 5 6 --no-reload` and `--iters 5 --bw 1 2 3 4 5 6 --no-reload` timed out in the isolated setup.
- `bw=6` at 10 iterations timed out; the reported bw=6 number uses 5 iterations.
- The isolated benchmark needs the TRISC1 clear-valid companion. Without it, repeated unpack rows eventually backpressure because there is no real math thread consuming SRCA/SRCB.
- This excludes BRISC/NCRISC feed timing, CB wait/pop traffic, math MOP overlap, pack pressure, and DRAM/NOC effects.
- Tile data are synthetic L1 scratch addresses; this measures unpack backend/control cost, not input delivery.
