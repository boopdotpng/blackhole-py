# Compute-free DRAM bandwidth — Card 1, 2026-09-16

The standalone writer does not reach the 512 GB/s pin-bandwidth specification.
Reads approach it; writes plateau around 330–345 GB/s, with no collapse when
increasing from 32 to 117 workers. This gap exists with compute and CB peer
handshakes removed. These measurements support investigating the write path
before attributing the entire matmul gap to accumulation or L1 partials.
They do not isolate the NIU, NoC routing, DRAM scheduling and acknowledgment
flow control from one another, or establish a hardware write ceiling.

## Method

Physical Card 1 (p150a), serialized through queue 1; ARC AICLK 1350 MHz.
The same standalone transfer emitter runs on BRISC, NCRISC, or both. No
Tensix compute instructions or producer/consumer credit handshakes participate.
Each stream owns its staging ring and a distinct DRAM shard striped across
eight banks. One-RISC cases split workers between NoC0/NoC1. Two-RISC cases
use both networks on every core and split the per-worker byte count equally,
so they transfer the same aggregate volume. Preferred endpoints are used.

One warmup plus five timed launches per case; table entries are medians.
Timing spans the earliest active RISC start to the latest completed end over
all workers, including nonposted write acknowledgments. Launch skew is about
0.23 us at 117 workers. Host upload, download, and compilation are excluded.
GB/s is decimal. Mixed traffic counts read and write bytes once each in one
shared completion interval; 512 GB/s is a shared bandwidth reference, not
512 in each direction simultaneously.

Every write destination is poisoned before warmup and checked in full after
the measured launches. Every reader's retained staging bytes are checked;
earlier overwritten read batches are not retained for host validation.
No performance threshold is asserted. Core subsets use runtime order, not
necessarily matmul's rectangular placement. Transfer order is contiguous
per-worker shards, not matmul's subblock traversal.

## Matmul-scale transfers: 512 KiB per worker, 2 KiB pages, batch 32

At 110 workers this transfers 57.67 MB; at 117, 61.34 MB. These are close to
the physical output volume of the 5000-square FP16-output matmul.

| Workers | BRISC read | NCRISC read | Both read | BRISC write | NCRISC write | Both write |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 196.2 | 193.4 | 216.4 | 192.2 | 192.2 | 179.9 |
| 16 | 342.1 | 344.0 | 371.6 | 294.9 | 292.8 | 278.1 |
| 32 | 427.0 | 432.9 | 471.1 | 327.3 | 327.7 | 343.0 |
| 64 | 443.2 | 445.5 | 482.3 | 325.2 | 323.7 | 345.4 |
| 110 | 449.7 | 446.8 | 481.8 | 329.9 | 328.7 | 340.9 |
| 117 | 457.0 | 456.3 | 480.9 | 327.9 | 331.3 | 343.0 |

All rates GB/s. BRISC and NCRISC behave similarly. Two issue engines per
worker substantially improve reads but only slightly improve writes. Write
bandwidth has already plateaued around 32 workers; adding 85 more workers
does not produce a new collapse.

## Sustained transfers: 4 MiB per worker, 2 KiB pages, batch 32

117 workers transfer 490.73 MB. This removes short-transfer/startup effects.

| Workers | BRISC read | NCRISC read | Both read | BRISC write | NCRISC write | Both write |
|---:|---:|---:|---:|---:|---:|---:|
| 16 | 338.4 | 339.8 | 371.8 | 296.4 | 296.2 | 281.5 |
| 64 | 437.6 | 440.9 | 478.4 | 331.3 | 333.1 | 348.3 |
| 117 | 449.1 | 447.9 | 469.5 | 332.2 | 332.5 | 344.6 |

## Controls at 117 workers

| Configuration | NCRISC write GB/s | Both write GB/s |
|---|---:|---:|
| 2 KiB / batch 8 | 330.4 | 343.5 |
| 2 KiB / batch 32 | 331.3 | 343.0 |
| 2 KiB / batch 128 | 331.2 | 342.9 |
| 16 KiB / batch 16 / 4 MiB per worker | 267.4 | 280.2 |
| 2 KiB / batch 32 / rotated starting bank | 330.5 | 346.9 |

Batch size and starting-bank rotation do not close the write gap. Larger
16 KiB packets are worse in this layout. Their batch is limited to 16 to
fit two independent staging rings in the runtime's usable L1 arena.
Concurrent independent read+write streams with rotated banks reach
377.8 GB/s aggregate.

## Reproduce

From blackhole-py, run every command through queue 1:

```sh
tt-device-queue run --device 1 --cwd "$PWD" -- '../.venv/bin/python tests/movement/bench_dram_bandwidth.py --device 1 --json tests/movement/dram_bandwidth_scaling.json'
```

Use these additional arguments for the other result files:

- Sustained: `--cores 16 64 117 --bytes-per-core 4194304`
- Large packets: `--cores 16 64 117 --pages 16384 --batch 16 --bytes-per-core 4194304`
- Batch controls: `--cores 32 117 --modes ncrisc both --directions write --batch 8` (or 128)
- Starting-bank control: `--cores 32 117 --modes ncrisc both --directions write mixed --bank-rotation`

Supply a different `--json` filename for each. The six companion JSON files
contain 86 completed, validated cases and 430 timed launches. Host copies
are chunked to fit the runtime staging region; staging rings are checked
against available L1 before opening the device. The production matmul kernel
is unchanged by this benchmark.

Reference: [official p150a specifications](https://docs.tenstorrent.com/aibs/blackhole/)
list 512 GB/s memory bandwidth.
