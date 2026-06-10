# Blackhole Semaphore and Circular-Buffer Microbench

Goal: measure focused semaphore and circular-buffer control costs that are
useful as constants for `microbenching/models/program_timing_model.py`.

The harness lives in `microbenching/tensix/microbench_sem_cb.py`.

## Quick Read

Current scope:

- one measured BRISC path for ready and lightly-contended RISC control helpers
- one measured TRISC2 path for Tensix-facing CB helper variants and Tensix
  semaphore instruction sequences
- one NCRISC releaser that updates L1 state after a small delay for blocking
  rows
- fixed-size records in L1 at `0x130000`, read back by the host through a TLB
  window
- optional markdown append after each run

## How To Run

From `blackhole-py`, through the Tenstorrent device queue:

```sh
PYTHONPATH=. TT_USB=1 /home/boop/tenstorrent/.venv/bin/python3 microbenching/tensix/microbench_sem_cb.py --iters 1000 --release-delay 64
```

Useful options:

- `--core X,Y`: choose the logical Tensix core.
- `--iters N`: change loop iterations.
- `--release-delay N`: change the NCRISC delay before releasing blocking rows.
- `--skip-noc`: skip RISC NOC semaphore rows if the NOC atomic path is not
  healthy on the current device.
- `--no-report`: print results without appending this file.

## What This Measures

Ready rows subtract the role-local empty-loop cost and report adjusted
cycles/op. These rows are the best source for static model constants.

Blocking rows deliberately include the BRISC request stores and the NCRISC
release path. They are useful for "light contention is present" scale, not as
pure primitive latency.

The TRISC Tensix semaphore rows use a per-iteration `PC_BUF_SYNC` drain. The
`TTSEMPOST` and `TTSEMGET` rows are paired to avoid exhausting the semaphore;
the proposed constant uses half of the adjusted pair cost.

## Limitations

- The benchmark does not isolate a pure blocking `TTSEMWAIT` release from
  another Tensix thread yet. The current `TTSEMWAIT` row is a ready-path
  `STALL_ON_MAX` measurement with a sync drain.
- Blocking CB and RISC semaphore rows include L1 protocol overhead for the
  releaser request.
- `noc_sem_inc_wait` measures a local NOC atomic increment plus atomic response
  wait; it is not separated into command issue and fabric/response components.
- The Tensix CB received/ack rows include the existing helper's Tensix
  instruction-buffer writes and stalls, matching the helper path used by
  matmul-style kernels rather than a theoretical minimum.

## Proposed Constants

Use ready adjusted rows for first-order constants in
`microbenching/models/program_timing_model.py`. Blocking rows should remain separate model
terms until a real producer/consumer dependency is represented explicitly.

## Run 2026-06-08T13:15:13-04:00

Command:

```sh
PYTHONPATH=. TT_USB=1 /home/boop/tenstorrent/.venv/bin/python3 microbenching/tensix/microbench_sem_cb.py --iters 1000 --release-delay 64
```

- Core: logical `1,2`
- Iterations per test: `1000`
- Light contention release delay loop: `64` NCRISC decrement iterations
- NOC semaphore rows skipped: `False`
- Dispatch path: slow dispatch (`TT_USB=1`), one worker core

Debug L1 ranges:
- `sem_cb_microbench_results` at `0x130000` (928 bytes)
- `sem_cb_microbench_control` at `0x134000` (512 bytes)

| role | test | group | mode | ops/iter | cycles | cyc/iter | adj cyc/op | sink |
|---|---|---|---|---:|---:|---:|---:|---:|
| brisc | empty | baseline | baseline | 0 | 4026 | 4.026 |  | 0x5c0b03e8 |
| brisc | release_signal | control | control | 1 | 291051 | 291.051 | 287.025 | 0x5c0b0001 |
| brisc | cb_wait_front_ready | cb | ready | 1 | 26028 | 26.028 | 22.002 | 0x5c0b0002 |
| brisc | cb_wait_front_block | cb | blocking | 1 | 324029 | 324.029 | 320.003 | 0x5c0b0003 |
| brisc | cb_reserve_back_ready | cb | ready | 1 | 27028 | 27.028 | 23.002 | 0x5c0b0004 |
| brisc | cb_reserve_back_block | cb | blocking | 1 | 328047 | 328.047 | 324.021 | 0x5c0b0005 |
| brisc | cb_push_back | cb | ready | 1 | 35041 | 35.041 | 31.015 | 0x5c0b0006 |
| brisc | cb_pop_front | cb | ready | 1 | 35541 | 35.541 | 31.515 | 0x5c0b0007 |
| brisc | noc_sem_set | noc_sem | ready | 1 | 16023 | 16.023 | 11.997 | 0x5c0b0008 |
| brisc | noc_sem_wait_ready | noc_sem | ready | 1 | 23107 | 23.107 | 19.081 | 0x5c0b0009 |
| brisc | noc_sem_wait_block | noc_sem | blocking | 1 | 312044 | 312.044 | 308.018 | 0x5c0b000a |
| brisc | noc_sem_inc_wait | noc_sem | ready | 1 | 103022 | 103.022 | 98.996 | 0x5c0b000b |
| trisc2 | trisc_empty | baseline | baseline | 0 | 4022 | 4.022 |  | 0x5c0b03f4 |
| trisc2 | cb_push_back_tensix_received | cb_tensix | ready | 1 | 45046 | 45.046 | 41.024 | 0x5c0b000d |
| trisc2 | cb_pop_front_tensix_ack | cb_tensix | ready | 1 | 45540 | 45.540 | 41.518 | 0x5c0b000e |
| trisc2 | ttsemwait_ready_sync | ttsem | ready | 1 | 12024 | 12.024 | 8.002 | 0x4cb0fb5e |
| trisc2 | ttsempost_get_pair_sync | ttsem | ready | 2 | 13024 | 13.024 | 4.501 | 0x4cb0fb5e |
| trisc2 | ttsemget_post_pair_sync | ttsem | ready | 2 | 13024 | 13.024 | 4.501 | 0x4cb0fb5e |

Proposed constants for `microbenching/models/program_timing_model.py`:

| constant | cycles | basis |
|---|---:|---|
| `CB_WAIT_FRONT_READY_CYCLES` | 22.0 | BRISC ready helper |
| `CB_RESERVE_BACK_READY_CYCLES` | 23.0 | BRISC ready helper |
| `CB_PUSH_BACK_CYCLES` | 31.0 | BRISC helper |
| `CB_POP_FRONT_CYCLES` | 31.5 | BRISC helper |
| `NOC_SEM_SET_CYCLES` | 12.0 | local RISC helper |
| `NOC_SEM_WAIT_READY_CYCLES` | 19.1 | local RISC helper |
| `NOC_SEM_INC_WAIT_CYCLES` | 99.0 | local NOC atomic inc plus response wait |
| `CB_PUSH_BACK_TENSIX_RECEIVED_CYCLES` | 41.0 | TRISC helper including Tensix received path |
| `CB_POP_FRONT_TENSIX_ACK_CYCLES` | 41.5 | TRISC helper including Tensix ack path |
| `TTSEMWAIT_READY_SYNC_CYCLES` | 8.0 | TTSEMWAIT plus per-iter PC_BUF_SYNC |
| `TTSEMPOST_OR_GET_SYNC_PAIR_HALF_CYCLES` | 2.3 | half of TTSEMPOST+TTSEMGET pair with per-iter sync |
