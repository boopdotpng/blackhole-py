# Blackhole Tensix Instruction Buffer Microbench

Goal: measure the small, focused path from a RISC thread to the Tensix
instruction buffer before adding heavier backend kernels.

The initial harness lives in `examples/tensix_instr_bench.py`.

## Quick Read

Current scope:

- run one active TRISC role per launch, defaulting to `trisc1`
- write a header and fixed-size timing records into L1 at `0x128000`
- read those records on the host through a TLB window
- append this markdown report after each non-`--no-report` run
- time the runtime FIFO push path as repeated `sw raw_word, 0(INSTRN_BUF_BASE)`
- separately time issue-plus-drain rows using `PC_BUF_SYNC`

The first probes use safe Tensix instructions:

- `TTNOP`
- `TTSTALLWAIT(0, 0)`, a zero-mask stall/wait instruction
- `TTSEMINIT` for `MATH_PACK`, with `init_value=0` and `max_value=1`
- a short `TTSEMINIT` / `TTSTALLWAIT(0, 0)` mixed sequence

## How To Run

From `blackhole-py`:

```sh
PYTHONPATH=. TT_USB=1 /home/boop/tenstorrent/.venv/bin/python3 examples/tensix_instr_bench.py --iters 10000
```

Useful options:

- `--roles trisc0 trisc1 trisc2`: compare all three TRISC issue paths.
- `--core X,Y`: choose the logical Tensix core.
- `--no-report`: print results without appending this file.

Hardware runs should go through the shared `tt-device-queue` tooling when run
from Codex or another agent.

## What This Measures

Each timed loop preloads:

- `INSTRN_BUF_BASE` into a RISC register
- `PC_BUF_SYNC` into a RISC register
- raw Tensix instruction words into RISC registers

The `*_issue*` rows time only repeated stores into the Tensix instruction
buffer. After the timestamp is taken, the harness performs one untimed
`PC_BUF_SYNC` drain so the next row starts cleanly.

The `*_sync*` rows push the same instruction sequence and then write/read
`PC_BUF_SYNC` inside every timed iteration. These rows include issue cost,
fixed sync-marker cost, and any backend drain/completion cost that was not
hidden by issue.

The table reports:

- `adj cyc/push`: `(row cyc/iter - empty cyc/iter) / pushes_per_iter`
- `sync extra/push`: for sync rows, subtracts the matching issue row and the
  `sync_empty` fixed marker cost before dividing by pushes per iteration

That split is the important part: use `*_issue*` rows for instruction-buffer
enqueue cost, and use `sync extra/push` as the first-order completion/drain
signal.

## L1 Result Layout

| Range | Address | Size | Purpose |
|---|---:|---:|---|
| `tensix_instr_bench_results` | `0x128000` | `544` bytes | header + timing records |

The result range starts with a fixed header, followed by one record per probe.
Each record includes the role id, test id, iteration count, pushes per
iteration, raw start/end wall-clock values, a sink word, and a drain flag.

## MVMUL Next Step

This first version does not include an MVMUL smoke. A single bare `TTMVMUL`
would not be a meaningful or reliable measurement because matmul needs more
state than just the math instruction word.

The minimal known-good setup should be borrowed from `examples/matmul_peak.py`
instead of hand-waved. In particular, an MVMUL microbenchmark needs:

- math thread destination and address-modifier setup
- valid SrcA/SrcB data in the expected source registers
- `TTSETRWC` state matching the selected address modes
- semaphore and sync setup consistent with the math backend
- replay or MOP setup if using the throttled matmul path
- a drain/completion marker that waits for math/SFPU completion without mixing
  in unpack/pack traffic unless intentionally measured

Once that is isolated, it should be added as a tiny smoke row with its own
setup section and clearly separate issue and completion timing.

## Run 2026-06-06T23:07:16-04:00

- Core: logical `1,2`
- Iterations per test: `100`
- Dispatch path: slow dispatch (`TT_USB=1`), one active TRISC role per launch
- Timed issue path: preloaded `sw raw_word, 0(INSTRN_BUF_BASE)` stores
- Drain marker: `PC_BUF_SYNC` write/read after each timed sequence for `*_sync*` rows

Debug L1 ranges:
- `tensix_instr_bench_results` at `0x128000` (544 bytes)

| role | test | mode | pushes/iter | cycles | cyc/iter | adj cyc/push | sync extra/push | sink |
|---|---|---|---:|---:|---:|---:|---:|---:|
| trisc1 | empty | baseline | 0 | 326 | 3.260 |  |  | 0x71000000 |
| trisc1 | sync_empty | sync-only | 0 | 924 | 9.240 |  |  | 0x70cb087f |
| trisc1 | ttnop_issue8 | issue | 8 | 1122 | 11.220 | 0.995 |  | 0x70cb087f |
| trisc1 | ttnop_sync8 | issue+sync | 8 | 1925 | 19.250 | 1.999 | 0.256 | 0x70cb087f |
| trisc1 | stallwait_none_issue8 | issue | 8 | 1560 | 15.600 | 1.542 |  | 0x70cb087f |
| trisc1 | stallwait_none_sync8 | issue+sync | 8 | 2625 | 26.250 | 2.874 | 0.584 | 0x70cb087f |
| trisc1 | seminit_issue4 | issue | 4 | 722 | 7.220 | 0.990 |  | 0x70cb087f |
| trisc1 | seminit_sync4 | issue+sync | 4 | 1525 | 15.250 | 2.998 | 0.513 | 0x70cb087f |
| trisc1 | seminit_stallwait_issue4 | issue | 4 | 722 | 7.220 | 0.990 |  | 0x70cb087f |
| trisc1 | seminit_stallwait_sync4 | issue+sync | 4 | 1525 | 15.250 | 2.998 | 0.513 | 0x70cb087f |
