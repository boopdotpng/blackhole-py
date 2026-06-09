# Blackhole NoC Microbench

Goal: measure a small, reliable slice of BRISC-driven NoC command behavior on
Blackhole Tensix tiles without touching the known-risk multicast cases.

The harness lives in `examples/riscv_noc_bench.py`.

## Submission Path Notes

`blackhole-py` and TT-Metal's normal dataflow APIs submit NoC packets through
the same command-buffer register path: poll `NOC_CMD_CTRL`, program target /
return address registers plus `NOC_CTRL` and `NOC_AT_LEN_BE`, then write
`NOC_CMD_CTRL = 1`. TT-Metal adds wrappers such as `noc_async_read`,
`noc_async_write`, stateful variants, inline writes, atomics, and semaphores,
but those still sit on this command-buffer mechanism. The real alternate path
found in TT-Metal is the stream / NoC overlay block, which needs more setup and
is less directly comparable to this benchmark.

## What This Measures

The harness can run local L1-to-L1 traffic, peer-tile L1 unicast traffic, or
both in the same launch. In peer mode, one source BRISC records results while a
second same-row tile is launched as a passive receiver so its L1 can be targeted
by NoC read/write commands.

- Force slow dispatch with `TT_USB=1`.
- Run one active BRISC; peer mode launches a passive BRISC `ret` kernel on the
  second tile. NCRISC and TRISCs are empty kernels.
- Time inside the BRISC kernel using `WALL_CLOCK_L/H`.
- Store structured records in an L1 debug range at `0x130000`; host-side code
  reads them through a TLB window after the launch completes.
- Cover NoC0 and NoC1 with the same local or peer coordinate when both
  instances accept the command stream.
- Include 4-byte command probes plus 16/64/256-byte read-flush and write-barrier
  sweeps.
- Seed peer scratch L1 from the host and perform untimed peer-write readback so
  the result sink verifies remote L1 traffic landed.

## Limitations

This is not yet a fabric topology benchmark. It compares local L1 and one
same-row peer-tile pair, but it does not sweep hop distance, routing effects,
congestion, multicast, DRAM paths, or end-to-end bandwidth across multiple
active senders.

Multicast is intentionally excluded from the default harness because Blackhole
path reservation / linked-multicast behavior has known hang risk. Keep that as a
separate diagnostic repro.

`*_cmd` rows time command issue loops and then flush or barrier after the timed
window so the following probe starts cleanly. `*_flush` and `*_barrier` rows
include the read response flush or write acknowledgement wait inside every
iteration.

## How To Run

From `blackhole-py`:

```sh
PYTHONPATH=. TT_USB=1 /home/boop/tenstorrent/.venv/bin/python3 examples/riscv_noc_bench.py --iters 1000
```

Useful options:

- `--core X,Y`: choose the logical Tensix core.
- `--peer-core X,Y`: choose a same-row peer for `--target peer` or `both`.
- `--target local|peer|both`: choose local L1, peer-tile L1 unicast, or both.
- `--iters N`: choose iterations per timed loop.
- `--no-report`: print results without appending this file.

## L1 Result Layout

| Range | Address | Size | Purpose |
|---|---:|---:|---|
| `riscv_noc_bench_results` | `0x130000` | mode-dependent | timing records |
| `riscv_noc_bench_scratch` | `0x134000` | `8192` bytes | source and destination L1 buffers |

The result range starts with a 16-word header, followed by one 16-word record
per probe. Each record stores the probe id, NoC instance, operation kind, byte
count, start/end wall-clock timestamps, sink word, and the relevant NoC status
counter before and after cleanup.

## Run 2026-06-06T23:16:36-04:00

- Source core: logical `1,2`
- Peer core: logical `2,2`
- Target mode: `both`
- Iterations per test: `100`
- Dispatch path: slow dispatch (`TT_USB=1`), BRISC only
- Traffic: local L1 and/or peer-tile L1 unicast; no DRAM writes and no multicast

Debug L1 ranges:
- `riscv_noc_bench_results` at `0x130000` (2688 bytes)
- `riscv_noc_bench_scratch` at `0x134000` (8192 bytes)

| test | noc | op | bytes | cycles | cyc/iter | adj cyc/op | bytes/cyc | counter delta | sink |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| empty |  | empty | 0 | 426 | 4.260 |  |  | 0 | 0x00000000 |
| local_noc0_read_4_cmd | 0 | read_cmd | 4 | 2923 | 29.230 | 24.970 | 0.160 | 100 | 0xa5000000 |
| local_noc0_read_4_flush | 0 | read_flush | 4 | 8322 | 83.220 | 78.960 | 0.051 | 100 | 0xa5000000 |
| local_noc0_write_4_cmd | 0 | write_cmd | 4 | 2724 | 27.240 | 22.980 | 0.174 | 100 | 0xa5000000 |
| local_noc0_write_4_barrier | 0 | write_barrier | 4 | 7322 | 73.220 | 68.960 | 0.058 | 100 | 0xa5000000 |
| local_noc0_read_16_flush | 0 | read_flush | 16 | 7522 | 75.220 | 70.960 | 0.225 | 100 | 0xa5000000 |
| local_noc0_read_64_flush | 0 | read_flush | 64 | 7522 | 75.220 | 70.960 | 0.902 | 100 | 0xa5000000 |
| local_noc0_read_256_flush | 0 | read_flush | 256 | 8322 | 83.220 | 78.960 | 3.242 | 100 | 0xa5000000 |
| local_noc0_write_16_barrier | 0 | write_barrier | 16 | 7322 | 73.220 | 68.960 | 0.232 | 100 | 0xa5000000 |
| local_noc0_write_64_barrier | 0 | write_barrier | 64 | 7322 | 73.220 | 68.960 | 0.928 | 100 | 0xa5000000 |
| local_noc0_write_256_barrier | 0 | write_barrier | 256 | 7322 | 73.220 | 68.960 | 3.712 | 100 | 0xa5000000 |
| local_noc1_read_4_cmd | 1 | read_cmd | 4 | 2923 | 29.230 | 24.970 | 0.160 | 100 | 0xa5000000 |
| local_noc1_read_4_flush | 1 | read_flush | 4 | 8322 | 83.220 | 78.960 | 0.051 | 100 | 0xa5000000 |
| local_noc1_write_4_cmd | 1 | write_cmd | 4 | 2723 | 27.230 | 22.970 | 0.174 | 100 | 0xa5000000 |
| local_noc1_write_4_barrier | 1 | write_barrier | 4 | 7322 | 73.220 | 68.960 | 0.058 | 100 | 0xa5000000 |
| local_noc1_read_16_flush | 1 | read_flush | 16 | 7522 | 75.220 | 70.960 | 0.225 | 100 | 0xa5000000 |
| local_noc1_read_64_flush | 1 | read_flush | 64 | 7522 | 75.220 | 70.960 | 0.902 | 100 | 0xa5000000 |
| local_noc1_read_256_flush | 1 | read_flush | 256 | 8322 | 83.220 | 78.960 | 3.242 | 100 | 0xa5000000 |
| local_noc1_write_16_barrier | 1 | write_barrier | 16 | 7322 | 73.220 | 68.960 | 0.232 | 100 | 0xa5000000 |
| local_noc1_write_64_barrier | 1 | write_barrier | 64 | 7327 | 73.270 | 69.010 | 0.927 | 100 | 0xa5000000 |
| local_noc1_write_256_barrier | 1 | write_barrier | 256 | 7322 | 73.220 | 68.960 | 3.712 | 100 | 0xa5000000 |
| peer_noc0_read_4_cmd | 0 | read_cmd | 4 | 2923 | 29.230 | 24.970 | 0.160 | 100 | 0xa5000000 |
| peer_noc0_read_4_flush | 0 | read_flush | 4 | 23522 | 235.220 | 230.960 | 0.017 | 100 | 0xa5000000 |
| peer_noc0_write_4_cmd | 0 | write_cmd | 4 | 2723 | 27.230 | 22.970 | 0.174 | 100 | 0xa5000000 |
| peer_noc0_write_4_barrier | 0 | write_barrier | 4 | 23322 | 233.220 | 228.960 | 0.017 | 100 | 0xa5000000 |
| peer_noc0_read_16_flush | 0 | read_flush | 16 | 22722 | 227.220 | 222.960 | 0.072 | 100 | 0xa5000000 |
| peer_noc0_read_64_flush | 0 | read_flush | 64 | 22722 | 227.220 | 222.960 | 0.287 | 100 | 0xa5000000 |
| peer_noc0_read_256_flush | 0 | read_flush | 256 | 23522 | 235.220 | 230.960 | 1.108 | 100 | 0xa5000000 |
| peer_noc0_write_16_barrier | 0 | write_barrier | 16 | 22522 | 225.220 | 220.960 | 0.072 | 100 | 0xa5000000 |
| peer_noc0_write_64_barrier | 0 | write_barrier | 64 | 22533 | 225.330 | 221.070 | 0.290 | 100 | 0xa5000000 |
| peer_noc0_write_256_barrier | 0 | write_barrier | 256 | 22538 | 225.380 | 221.120 | 1.158 | 100 | 0xa5000000 |
| peer_noc1_read_4_cmd | 1 | read_cmd | 4 | 2923 | 29.230 | 24.970 | 0.160 | 100 | 0xa5000000 |
| peer_noc1_read_4_flush | 1 | read_flush | 4 | 23522 | 235.220 | 230.960 | 0.017 | 100 | 0xa5000000 |
| peer_noc1_write_4_cmd | 1 | write_cmd | 4 | 2723 | 27.230 | 22.970 | 0.174 | 100 | 0xa5000000 |
| peer_noc1_write_4_barrier | 1 | write_barrier | 4 | 23322 | 233.220 | 228.960 | 0.017 | 100 | 0xa5000000 |
| peer_noc1_read_16_flush | 1 | read_flush | 16 | 22722 | 227.220 | 222.960 | 0.072 | 100 | 0xa5000000 |
| peer_noc1_read_64_flush | 1 | read_flush | 64 | 22722 | 227.220 | 222.960 | 0.287 | 100 | 0xa5000000 |
| peer_noc1_read_256_flush | 1 | read_flush | 256 | 23522 | 235.220 | 230.960 | 1.108 | 100 | 0xa5000000 |
| peer_noc1_write_16_barrier | 1 | write_barrier | 16 | 22522 | 225.220 | 220.960 | 0.072 | 100 | 0xa5000000 |
| peer_noc1_write_64_barrier | 1 | write_barrier | 64 | 22533 | 225.330 | 221.070 | 0.290 | 100 | 0xa5000000 |
| peer_noc1_write_256_barrier | 1 | write_barrier | 256 | 22522 | 225.220 | 220.960 | 1.159 | 100 | 0xa5000000 |
