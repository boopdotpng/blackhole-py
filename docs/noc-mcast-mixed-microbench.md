# Blackhole NoC Multicast and Mixed-Traffic Microbench

The harness lives in `examples/microbench_noc_mcast_mixed.py`.

## Goal

Measure NoC costs that are missing from `examples/program_timing_model.py`:

- 16 KiB unlinked multicast writes for matmul-like row and column rectangles.
- `noc_semaphore_set_multicast` and `noc_semaphore_inc` atomic handshakes.
- Mixed read + write + multicast traffic using both NoC0 and NoC1.
- Basic congestion or overlap signals from comparing mixed bundles with the
  individual operations.

## Method

The benchmark launches one active BRISC sender plus passive receiver BRISCs.
The sender records wall-clock timestamps into L1 at `0x160000`; the host reads
structured records after launch completion. Receiver L1 is read back after each
case to verify multicast data and semaphore side effects.

For multicast safety, the benchmark uses only unlinked multicast packets and
waits for `NIU_MST_NONPOSTED_WR_REQ_SENT` after every multicast before issuing
the next multicast path reservation. Defaults are deliberately small:
three receivers per rectangle and four timed iterations. Hardware runs should
be wrapped in the Tenstorrent device queue and an outer shell timeout.

The row case chooses the first logical row with enough program cores and
multicasts from the leftmost core to the next cores on that row. The column
case chooses the first logical column with enough program cores and multicasts
from the top core to the next cores in that column, using the same reversed
Y rectangle shape as `matmul_peak.py`.

## How To Run

From `blackhole-py`, through the Tenstorrent device queue:

```sh
timeout 120s /home/boop/tenstorrent/.venv/bin/python3 examples/microbench_noc_mcast_mixed.py --iters 4 --dests 3
```

Queue environment: `PYTHONPATH=.`, `TT_USB=1`, `BLACKHOLE_RUN_TIMEOUT_S=5`.

Useful options:

- `--cases row,column`: choose row and/or column rectangle probes.
- `--dests N`: choose multicast receivers per rectangle.
- `--iters N`: choose timed loop iterations; keep small while exploring.
- `--skip-mixed`: skip the mixed read/write/mcast probes if multicast behavior
  looks unstable.
- `--no-report`: print without appending this document.

## Limitations

This is still a BRISC command-buffer benchmark. It does not use overlay streams,
DRAM, command queue dataflow kernels, or linked multicast chains. The mixed test
is a conservative one-sender signal: it issues one 16 KiB read, one 16 KiB
write, and one 16 KiB multicast before draining, so it can show overlap or
contention in a static model but is not an aggregate fabric saturation test.

If any multicast run times out, treat the device state as suspect, reset or
reboot before continuing, and report the skipped command here rather than
increasing iteration count.

## Run 2026-06-08T13:14:48-04:00

Commands run:

```sh
/home/boop/tenstorrent/.venv/bin/python3 -m py_compile examples/microbench_noc_mcast_mixed.py
/home/boop/tenstorrent/.venv/bin/python3 examples/microbench_noc_mcast_mixed.py --help
```

Hardware commands run through the Tenstorrent device queue:

```sh
timeout 90s /home/boop/tenstorrent/.venv/bin/python3 examples/microbench_noc_mcast_mixed.py --cases row --dests 1 --iters 1 --skip-mixed --no-report
timeout 120s /home/boop/tenstorrent/.venv/bin/python3 examples/microbench_noc_mcast_mixed.py --iters 4 --dests 3
```

Queue environment for both hardware commands: `PYTHONPATH=.`, `TT_USB=1`,
`BLACKHOLE_RUN_TIMEOUT_S=5`.

Command:

```sh
examples/microbench_noc_mcast_mixed.py --iters 4 --dests 3
```

- Tenstorrent queue command:
  `timeout 120s /home/boop/tenstorrent/.venv/bin/python3 examples/microbench_noc_mcast_mixed.py --iters 4 --dests 3`
- Queue environment: `PYTHONPATH=.`, `TT_USB=1`, `BLACKHOLE_RUN_TIMEOUT_S=5`.
- Iterations per timed loop: `4`
- Dispatch path: slow dispatch (`TT_USB=1`); hardware run timeout set by `BLACKHOLE_RUN_TIMEOUT_S`.
- Multicast policy: unlinked multicast writes only, with a nonposted-write-sent flush before the next multicast reservation.
- Mixed policy: issue one read, one write, and one multicast, then drain all three before the next iteration.

### Case `row`

- Source: `1,2`
- Atomic peer: `2,2`
- Receivers: `2,2`, `3,2`, `4,2`

| case | test | noc | op | bytes | dests | cycles | adj cyc/op | effective dest B/cyc | counter delta | aux0 | aux1 | sink |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| row | empty |  | empty | 0 | 3 | 39 | 0.000 | 0.000 | 0 | 0 | 0 | 0x00000000 |
| row | mcast_write_noc0_16k | 0 | mcast_write | 16384 | 3 | 1442 | 350.750 | 140.134 | 4 | 0 | 0 | 0x00000000 |
| row | mcast_write_noc1_16k | 1 | mcast_write | 16384 | 3 | 2170 | 532.750 | 92.261 | 4 | 0 | 0 | 0x00000000 |
| row | sem_mcast_set_noc0 | 0 | sem_mcast_set | 16 | 3 | 262 | 55.750 | 0.861 | 4 | 0 | 0 | 0x00000000 |
| row | sem_mcast_set_noc1 | 1 | sem_mcast_set | 16 | 3 | 612 | 143.250 | 0.335 | 4 | 0 | 0 | 0x00000000 |
| row | atomic_inc_noc0 | 0 | atomic_inc | 4 | 3 | 970 | 232.750 | 0.052 | 4 | 0 | 0 | 0x00000000 |
| row | atomic_inc_noc1 | 1 | atomic_inc | 4 | 3 | 970 | 232.750 | 0.052 | 4 | 0 | 0 | 0x00000000 |
| row | read_peer_noc0_16k | 0 | read_16k | 16384 | 3 | 1962 | 480.750 | 102.240 | 4 | 0 | 0 | 0xa5000000 |
| row | write_peer_noc1_16k | 1 | write_16k | 16384 | 3 | 1946 | 476.750 | 103.098 | 4 | 0 | 0 | 0xa5000000 |
| row | mixed_read0_write1_mcast0_16k | 0 | mixed_read_write_mcast | 16384 | 3 | 2772 | 683.250 | 71.939 | 4 | 4 | 4 | 0xa5000000 |
| row | mixed_read1_write0_mcast1_16k | 1 | mixed_read_write_mcast | 16384 | 3 | 2378 | 584.750 | 84.056 | 4 | 4 | 4 | 0xa5000000 |

Validation readback:

| case | core | first word | last word | sem0 |
|---|---|---:|---:|---:|
| row | `1,2` | 0xa5000000 | 0xa5003ffc | 1 |
| row | `2,2` | 0xa5000000 | 0xa5003ffc | 7 |
| row | `3,2` | 0xa5000000 | 0xa5003ffc | 1 |
| row | `4,2` | 0xa5000000 | 0xa5003ffc | 1 |

### Case `column`

- Source: `1,2`
- Atomic peer: `1,3`
- Receivers: `1,3`, `1,4`, `1,5`

| case | test | noc | op | bytes | dests | cycles | adj cyc/op | effective dest B/cyc | counter delta | aux0 | aux1 | sink |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| column | empty |  | empty | 0 | 3 | 39 | 0.000 | 0.000 | 0 | 0 | 0 | 0x00000000 |
| column | mcast_write_noc0_16k | 0 | mcast_write | 16384 | 3 | 1887 | 462.000 | 106.390 | 4 | 0 | 0 | 0x00000000 |
| column | mcast_write_noc1_16k | 1 | mcast_write | 16384 | 3 | 1887 | 462.000 | 106.390 | 4 | 0 | 0 | 0x00000000 |
| column | sem_mcast_set_noc0 | 0 | sem_mcast_set | 16 | 3 | 468 | 107.250 | 0.448 | 4 | 0 | 0 | 0x00000000 |
| column | sem_mcast_set_noc1 | 1 | sem_mcast_set | 16 | 3 | 468 | 107.250 | 0.448 | 4 | 0 | 0 | 0x00000000 |
| column | atomic_inc_noc0 | 0 | atomic_inc | 4 | 3 | 818 | 194.750 | 0.062 | 4 | 0 | 0 | 0x00000000 |
| column | atomic_inc_noc1 | 1 | atomic_inc | 4 | 3 | 818 | 194.750 | 0.062 | 4 | 0 | 0 | 0x00000000 |
| column | read_peer_noc0_16k | 0 | read_16k | 16384 | 3 | 1798 | 439.750 | 111.773 | 4 | 0 | 0 | 0xa5000000 |
| column | write_peer_noc1_16k | 1 | write_16k | 16384 | 3 | 1786 | 436.750 | 112.540 | 4 | 0 | 0 | 0xa5000000 |
| column | mixed_read0_write1_mcast0_16k | 0 | mixed_read_write_mcast | 16384 | 3 | 2620 | 645.250 | 76.175 | 4 | 4 | 4 | 0xa5000000 |
| column | mixed_read1_write0_mcast1_16k | 1 | mixed_read_write_mcast | 16384 | 3 | 2108 | 517.250 | 95.026 | 4 | 4 | 4 | 0xa5000000 |

Validation readback:

| case | core | first word | last word | sem0 |
|---|---|---:|---:|---:|
| column | `1,2` | 0xa5000000 | 0xa5003ffc | 1 |
| column | `1,3` | 0xa5000000 | 0xa5003ffc | 7 |
| column | `1,4` | 0xa5000000 | 0xa5003ffc | 1 |
| column | `1,5` | 0xa5000000 | 0xa5003ffc | 1 |

### Proposed Constants

The appended run table above reports effective destination bytes per cycle for
multicast rows. For `examples/program_timing_model.py`, charge multicast as
source bytes sent once, matching the existing matmul traffic accounting.

| constant | proposed value | note |
|---|---:|---|
| `NOC_MCAST_16K_BPC` | 30.752 | min observed source-bytes/cycle for safe unlinked row/column multicast: 16 KiB / 532.750 cyc |
| `NOC_SEM_MCAST_CYCLES` | 103.375 | mean BRISC issue + nonposted flush for `noc_semaphore_set_multicast` |
| `NOC_SEM_INC_ACK_CYCLES` | 213.750 | mean `noc_semaphore_inc` plus atomic response wait |
| `NOC_MIXED_RWM_16K_CYCLES` | 607.625 | mean read+write+mcast safe-loop bundle, one 16KiB packet each |

Mixed overlap signal: the four mixed bundles average `607.625` cycles. The
corresponding individual read + write + mcast source-byte operations average
about `925.813` cycles, so this conservative one-sender pattern shows roughly
`1.52x` overlap versus serialized static charging.
