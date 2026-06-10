# Blackhole XMOV / TDMA Mover Microbench

Goal: measure the Tensix internal mover path used by Dest<->Src transfers and
DMA-register operations. This is the backend bandwidth that can gate math/SFPU
handoffs, transpose-like movement, and pack/unpack address-register plumbing.

The harness lives in `microbenching/tensix/microbench_xmov.py`.

## Scope

- one active TRISC role on one Tensix core, defaulting to `trisc1`
- one fresh device launch per measured row, because isolated Tensix backend rows
  can wedge when internal valid state is reused too aggressively
- result records in L1 at `0x12a000`
- raw instruction FIFO pushes via `sw word, 0(INSTRN_BUF_BASE)`
- completion via raw `TTSTALLWAIT(SYNC, XMOV)` followed by `PC_BUF_SYNC`
- three rows per op:
  - issue cost: push a batch of ops, timestamp, then drain outside the timed
    window
  - completion latency: push one op and drain inside the timed window
  - steady-state throughput: push a batch of ops and drain once inside the
    timed window
- internal move ops: `TTMOVD2A`, `TTMOVA2D`, `TTMOVD2B`, `TTMOVDBGA2D`,
  `TTMOVDBGB2D`
- DMA-register ops: `TTSETDMAREG`, `TTSHIFTDMAREG`, `TTRSTDMA`, `TTDMANOP`

Hardware-touching runs from Codex must go through the Tenstorrent
`tt-device-queue` MCP. Do not run this benchmark directly with plain Python when
it will open `Device()`.

## Quarantine

Direct internal mover and debug-readback rows are quarantined until explicitly
cleared:

- `TTMOVA2D` / `ttmova2d_latency`
- `TTMOVD2B`
- `TTMOVD2A` issue and steady-state rows
- `TTMOVDBGA2D`, `TTMOVDBGB2D`
- `dest_readback_probe`

Reason: `ttmova2d_latency` job `18ce9062` timed out waiting for core `(1,2)`.
After host-crash investigation this is treated as a hardware-wedge risk, not
as an ordinary benchmark timeout. Keep the completed DMA-register rows; do not
queue direct mover/readback rows until the avoid list is explicitly lifted.

## How To Run

From `blackhole-py`, through the device queue:

```sh
PYTHONPATH=. TT_USB=1 python3 microbenching/tensix/microbench_xmov.py --iters 4 --batch 4 --tests empty,sync_empty,ttdmanop_issue,ttdmanop_latency,ttdmanop_throughput --no-readback-probe
PYTHONPATH=. TT_USB=1 python3 microbenching/tensix/microbench_xmov.py --iters 4 --batch 4 --tests empty,sync_empty,ttsetdmareg_issue,ttsetdmareg_latency,ttsetdmareg_throughput,ttshiftdmareg_issue,ttshiftdmareg_latency,ttshiftdmareg_throughput,ttrstdma_issue,ttrstdma_latency,ttrstdma_throughput --no-readback-probe
```

Do not use the full default spec set while the quarantine is active; it includes
direct mover and readback rows.

Useful options:

- `--role trisc0|trisc1|trisc2`: choose the issuing TRISC role.
- `--core X,Y`: choose the logical Tensix core.
- `--iters N`: raise only after smoke rows complete; isolated mover rows are
  intentionally kept small.
- `--batch N`: number of ops in issue/throughput rows, max 8.
- `--tests a,b,c`: run a small subset while bisecting hangs.
- `--no-readback-probe`: skip the provisional `DEST_CG_CTRL`/`TTMOVDBGA2D`
  probe row.
- `--no-report`: print without appending this document.

Non-device validation is safe with plain Python:

```sh
PYTHONPATH=. python3 -m py_compile microbenching/tensix/microbench_xmov.py
PYTHONPATH=. python3 - <<'PY'
import microbenching.microbench_xmov as x
x.SPECS = x.make_specs(4, True)
x.build_program("trisc1", 1)
print(len(x.SPECS), x.result_size())
PY
```

## Interpretation

The summary table reports the three numbers per op:

- `issue cyc/op`: RISC-side cost to push raw Tensix words into the instruction
  FIFO. This is not engine retirement.
- `latency cyc`: one op plus `TTSTALLWAIT(SYNC, XMOV)` and `PC_BUF_SYNC`.
- `steady cyc/op`: batch of ops plus one completion edge, divided by batch.
- `steady engine cyc/op`: same throughput row after subtracting the empty sync
  edge. This is the best first-order estimate of internal mover throughput.

Compare latency against steady throughput to infer occupancy. A low steady
cycles/op with a higher single-op latency means the mover is accepting multiple
ops in flight. Similar latency and throughput means the path is effectively
serialized at this granularity.

The move rows run a small untimed setup (`math_direct_mova2d_init`,
`TTZEROSRC`, `TTZEROACC`, `TTSETRWC`) before timing. The DMA-register rows skip
that setup. Address fields are varied across a batch so the issue/throughput
rows are less likely to collide on the same internal row.

## Readback Status

The benchmark includes a provisional `dest_readback_probe` row unless
`--no-readback-probe` is passed. It writes `RISCV_DEBUG_REG_DEST_CG_CTRL`, emits
`TTMOVDBGA2D`, drains with the XMOV completion edge, and stores the before/after
debug-control values in the result record. This is a hook for the desired
Dest-readback validation path, not yet a trusted numerical validation. The debug
move semantics still need to be cross-checked against a known matmul Dest value
before using it to assert data correctness.

## Current Caveats

- The only clock is the issuing RISC `WALL_CLOCK`, so all numbers are
  RISC-observed cycles.
- The completion edge is inferred from `TTSTALLWAIT(SYNC, XMOV)` plus
  `PC_BUF_SYNC`; it is not a direct hardware retirement counter.
- Isolated Dest/Src rows can hang if valid state is reused too aggressively.
  Prefer one fresh launch per row and small `--iters` while characterizing.
- Readback may perturb Dest clock-gating state through `DEST_CG_CTRL`; measure
  timing rows with and without the probe before treating the probe as free.

## Current Summary 2026-06-09

Cycle counts are primary. New `us/op` conversions use the rebooted card's
current `AICLK=800 MHz`; earlier appended run blocks were generated before that
constant was changed.

| op | issue cyc/op | latency cyc | steady cyc/op | steady engine cyc/op | status |
|---|---:|---:|---:|---:|---|
| `TTMOVD2A` | paused | 12.000 | paused |  | one-shot latency completed; remaining direct-mover rows paused |
| `TTMOVA2D` | paused | hang | paused |  | avoid list; isolated latency timed out, job `18ce9062` |
| `TTMOVD2B` | paused | paused | paused |  | avoid list; do not run until explicitly cleared |
| `TTMOVDBGA2D` | paused | paused | paused |  | direct debug-move/readback path paused |
| `TTMOVDBGB2D` | paused | paused | paused |  | direct debug-move/readback path paused |
| `TTSETDMAREG` | 1.750 | 14.000 | 4.062 | 1.000 | completed |
| `TTSHIFTDMAREG` | 1.938 | 15.250 | 6.125 | 3.062 | completed |
| `TTRSTDMA` | 1.312 | 14.250 | 4.062 | 1.000 | completed |
| `TTDMANOP` | 1.938 | 15.500 | 4.312 | 1.250 | completed |
| `dest_readback_probe` | paused | paused | paused |  | avoid list; do not run until explicitly cleared |

## Safe DMA-Reg Summary

These rows completed before the direct-mover quarantine and remain the usable
XMOV-thread result set:

| op | issue cyc/op | latency cyc | steady cyc/op | steady engine cyc/op | read |
|---|---:|---:|---:|---:|---|
| `TTSETDMAREG` | 1.750 | 14.000 | 4.062 | 1.000 | register set itself is about one engine cycle/op in steady state |
| `TTSHIFTDMAREG` | 1.938 | 15.250 | 6.125 | 3.062 | shift is the expensive DMA-reg ALU op in this set |
| `TTRSTDMA` | 1.312 | 14.250 | 4.062 | 1.000 | reset drains like the one-cycle DMA-reg ops |
| `TTDMANOP` | 1.938 | 15.500 | 4.312 | 1.250 | no-op is close to the one-cycle path after sync removal |

Interpretation: the single-op latency numbers are dominated by the completion
edge (`TTSTALLWAIT(SYNC, XMOV)` plus `PC_BUF_SYNC`). Steady-state engine cycles
are the useful comparison: SET/NOP/RST cluster around 1.0-1.25 cycles/op, while
`TTSHIFTDMAREG` is roughly 3 cycles/op.

## Hardware Status 2026-06-09

Queued smoke runs completed for `TTDMANOP`, `TTSETDMAREG`, `TTSHIFTDMAREG`,
`TTRSTDMA`, and one-shot `TTMOVD2A` latency. After the shared card was rebooted
and reported healthy again, isolated `TTMOVA2D` latency was retried as queued
job `18ce9062`:

```text
timeout waiting for core (1, 2)
```

Per the stop-on-first-failure rule, no further hardware rows were attempted in
that resume pass. The older `boot_status=0xffffffff` / ARC-not-ready state is
historical and is not used to explain this current `TTMOVA2D` timeout.

Fresh queue attempt after the card was reported healthy again:

- Job `f4babaf4`, intended row `ttmovd2a_issue`, failed before benchmark launch
  in `Device()` with `boot_status=0xffffffff`.
- MCP reset job `18be0511` also failed with ARC not ready after the PCIe
  secondary-bus reset.

Because no XMOV row reached execution in that fresh attempt, it is treated as a
device-level blocker, not a measured XMOV result.

Safety pause: after host-crash investigation, direct XMOV mover/readback rows
are paused because `ttmova2d_latency` job `18ce9062` timed out waiting for core
`(1,2)` and is considered hardware-wedge risk. Do not queue `ttmova2d_latency`,
`TTMOVD2B`, or `dest_readback_probe` hardware runs until explicitly cleared.
The DMA-register rows above remain the safe completed result set.

## Run 2026-06-09T00:45:34-04:00

- Command: `PYTHONPATH=. TT_USB=1 /usr/local/bin/python3 microbenching/tensix/microbench_xmov.py --role trisc1 --iters 4 --batch 4 --tests empty,sync_empty,ttdmanop_issue,ttdmanop_latency,ttdmanop_throughput --no-readback-probe`
- Core: logical `1,2`
- Active role: `trisc1`
- Iterations per row: `4`
- Batch size for issue/throughput rows: `4` ops
- Dispatch path: slow dispatch (`TT_USB=1`), one active TRISC role per launch
- Timed issue path: raw `sw word, 0(INSTRN_BUF_BASE)` pushes
- Completion edge: raw `TTSTALLWAIT(SYNC, XMOV)` followed by `PC_BUF_SYNC` write/read

| op | issue cyc/op | latency cyc | steady cyc/op | steady engine cyc/op |
|---|---:|---:|---:|---:|
| `ttmovd2a` |  |  |  |  |
| `ttmova2d` |  |  |  |  |
| `ttmovd2b` |  |  |  |  |
| `ttmovdbga2d` |  |  |  |  |
| `ttmovdbgb2d` |  |  |  |  |
| `ttsetdmareg` |  |  |  |  |
| `ttshiftdmareg` |  |  |  |  |
| `ttrstdma` |  |  |  |  |
| `ttdmanop` | 1.938 | 15.500 | 4.312 | 1.250 |

| role | test | op | mode | ops/iter | cycles/iter | adj cycles | cycles/op | engine cycles/op | us/op | check |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| trisc1 | empty | empty | baseline | 0 | 8.500 | 0.000 |  |  |  |  |
| trisc1 | sync_empty | sync_empty | sync | 0 | 20.750 | 12.250 |  |  |  |  |
| trisc1 | ttdmanop_issue | ttdmanop | issue | 4 | 16.250 | 7.750 | 1.938 |  | 0.00144 |  |
| trisc1 | ttdmanop_latency | ttdmanop | latency | 1 | 24.000 | 15.500 | 15.500 | 3.250 | 0.01148 |  |
| trisc1 | ttdmanop_throughput | ttdmanop | throughput | 4 | 25.750 | 17.250 | 4.312 | 1.250 | 0.00319 |  |

## Run 2026-06-09T00:45:46-04:00

- Command: `PYTHONPATH=. TT_USB=1 /usr/local/bin/python3 microbenching/tensix/microbench_xmov.py --role trisc1 --iters 4 --batch 4 --tests empty,sync_empty,ttsetdmareg_issue,ttsetdmareg_latency,ttsetdmareg_throughput,ttshiftdmareg_issue,ttshiftdmareg_latency,ttshiftdmareg_throughput,ttrstdma_issue,ttrstdma_latency,ttrstdma_throughput --no-readback-probe`
- Core: logical `1,2`
- Active role: `trisc1`
- Iterations per row: `4`
- Batch size for issue/throughput rows: `4` ops
- Dispatch path: slow dispatch (`TT_USB=1`), one active TRISC role per launch
- Timed issue path: raw `sw word, 0(INSTRN_BUF_BASE)` pushes
- Completion edge: raw `TTSTALLWAIT(SYNC, XMOV)` followed by `PC_BUF_SYNC` write/read

| op | issue cyc/op | latency cyc | steady cyc/op | steady engine cyc/op |
|---|---:|---:|---:|---:|
| `ttmovd2a` |  |  |  |  |
| `ttmova2d` |  |  |  |  |
| `ttmovd2b` |  |  |  |  |
| `ttmovdbga2d` |  |  |  |  |
| `ttmovdbgb2d` |  |  |  |  |
| `ttsetdmareg` | 1.750 | 14.000 | 4.062 | 1.000 |
| `ttshiftdmareg` | 1.938 | 15.250 | 6.125 | 3.062 |
| `ttrstdma` | 1.312 | 14.250 | 4.062 | 1.000 |
| `ttdmanop` |  |  |  |  |

| role | test | op | mode | ops/iter | cycles/iter | adj cycles | cycles/op | engine cycles/op | us/op | check |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| trisc1 | empty | empty | baseline | 0 | 8.500 | 0.000 |  |  |  |  |
| trisc1 | sync_empty | sync_empty | sync | 0 | 20.750 | 12.250 |  |  |  |  |
| trisc1 | ttsetdmareg_issue | ttsetdmareg | issue | 4 | 15.500 | 7.000 | 1.750 |  | 0.00130 |  |
| trisc1 | ttsetdmareg_latency | ttsetdmareg | latency | 1 | 22.500 | 14.000 | 14.000 | 1.750 | 0.01037 |  |
| trisc1 | ttsetdmareg_throughput | ttsetdmareg | throughput | 4 | 24.750 | 16.250 | 4.062 | 1.000 | 0.00301 |  |
| trisc1 | ttshiftdmareg_issue | ttshiftdmareg | issue | 4 | 16.250 | 7.750 | 1.938 |  | 0.00144 |  |
| trisc1 | ttshiftdmareg_latency | ttshiftdmareg | latency | 1 | 23.750 | 15.250 | 15.250 | 3.000 | 0.01130 |  |
| trisc1 | ttshiftdmareg_throughput | ttshiftdmareg | throughput | 4 | 33.000 | 24.500 | 6.125 | 3.062 | 0.00454 |  |
| trisc1 | ttrstdma_issue | ttrstdma | issue | 4 | 13.750 | 5.250 | 1.312 |  | 0.00097 |  |
| trisc1 | ttrstdma_latency | ttrstdma | latency | 1 | 22.750 | 14.250 | 14.250 | 2.000 | 0.01056 |  |
| trisc1 | ttrstdma_throughput | ttrstdma | throughput | 4 | 24.750 | 16.250 | 4.062 | 1.000 | 0.00301 |  |

## Run 2026-06-09T00:46:29-04:00

- Command: `PYTHONPATH=. TT_USB=1 /usr/local/bin/python3 microbenching/tensix/microbench_xmov.py --role trisc1 --iters 1 --batch 1 --tests empty,sync_empty,ttmovd2a_latency --no-readback-probe`
- Core: logical `1,2`
- Active role: `trisc1`
- Iterations per row: `1`
- Batch size for issue/throughput rows: `1` ops
- Dispatch path: slow dispatch (`TT_USB=1`), one active TRISC role per launch
- Timed issue path: raw `sw word, 0(INSTRN_BUF_BASE)` pushes
- Completion edge: raw `TTSTALLWAIT(SYNC, XMOV)` followed by `PC_BUF_SYNC` write/read

| op | issue cyc/op | latency cyc | steady cyc/op | steady engine cyc/op |
|---|---:|---:|---:|---:|
| `ttmovd2a` |  | 12.000 |  |  |
| `ttmova2d` |  |  |  |  |
| `ttmovd2b` |  |  |  |  |
| `ttmovdbga2d` |  |  |  |  |
| `ttmovdbgb2d` |  |  |  |  |
| `ttsetdmareg` |  |  |  |  |
| `ttshiftdmareg` |  |  |  |  |
| `ttrstdma` |  |  |  |  |
| `ttdmanop` |  |  |  |  |

| role | test | op | mode | ops/iter | cycles/iter | adj cycles | cycles/op | engine cycles/op | us/op | check |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| trisc1 | empty | empty | baseline | 0 | 29.000 | 0.000 |  |  |  |  |
| trisc1 | sync_empty | sync_empty | sync | 0 | 46.000 | 17.000 |  |  |  |  |
| trisc1 | ttmovd2a_latency | ttmovd2a | latency | 1 | 41.000 | 12.000 | 12.000 | -5.000 | 0.00889 |  |
