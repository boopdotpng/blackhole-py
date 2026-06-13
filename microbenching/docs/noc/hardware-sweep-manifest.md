# NoC Hardware Sweep Manifest

This directory is intended to make the NoC scheduler/microbench results
self-contained when the repo is zipped and analyzed without hardware access.

Start here:

- `noc-scheduler-model.md`: current scheduler interpretation and remaining
  unknowns.
- `hardware-logs/*.txt`: raw `tt-device-queue` stdout for the hardware jobs
  listed below.
- The other markdown files in this directory contain curated report tables for
  the major successful sweeps.

## Raw Hardware Logs

| job | status | coverage | curated doc | raw output |
|---|---|---|---|---|
| `3373c44a` | PASS | packet latency, read/write, NoC0/1, 4..16 KiB, auto 1D/2D routes | `noc-scheduler-model.md` summary | `hardware-logs/3373c44a.txt` |
| `62d0798e` | PASS | same-target arbitration, K=2/3/4/6/8, 4 KiB and 16 KiB | `noc-arbitration.md` and scheduler summary | `hardware-logs/62d0798e.txt` |
| `055589e4` | PASS | DRAM spread preferred endpoint, 1..118 cores | `dram-noc-bench.md` | `hardware-logs/055589e4.txt` |
| `dca60895` | PASS | DRAM spread split3 endpoint, 1..118 cores | `dram-noc-bench.md` | `hardware-logs/dca60895.txt` |
| `4a4b3479` | PASS | mixed read/write overlap, distinct source cores, NoC0 | `noc-mixed-rw-overlap.md` | `hardware-logs/4a4b3479.txt` |
| `acf58a23` | PASS | mixed read/write overlap, distinct source cores, NoC1 | `noc-mixed-rw-overlap.md` | `hardware-logs/acf58a23.txt` |
| `b262e02b` | PASS | multicast one-way row/column/rect, NoC0/1, x/y majors | scheduler summary and raw log | `hardware-logs/b262e02b.txt` |
| `2eb05465` | FAIL | full multicast throughput matrix timed out on receiver `(10,4)` | scheduler known-failures section | `hardware-logs/2eb05465.txt` |
| `3bede304` | PASS | multicast throughput split run, NoC0/x, counts 1/2/4 | scheduler summary and raw log | `hardware-logs/3bede304.txt` |
| `f72a1914` | PASS | multicast throughput split run, NoC1/y, counts 1/2/4 | scheduler summary and raw log | `hardware-logs/f72a1914.txt` |
| `31528b9a` | PASS | multicast `VC_LINKED`, NoC0/1, x/y, depths 1/2/4 | scheduler summary and raw log | `hardware-logs/31528b9a.txt` |
| `d5ea13a3` | PASS | dual multicast solo/disjoint/shared-columns, NoC0/1, x/y | scheduler summary and raw log | `hardware-logs/d5ea13a3.txt` |
| `b7ce0d93` | PASS | overlapping multicast rectangles, NoC0/1, x/y | scheduler summary and raw log | `hardware-logs/b7ce0d93.txt` |
| `6e08eedc` | PASS | competing matmul-style multicast rectangles | scheduler summary and raw log | `hardware-logs/6e08eedc.txt` |
| `8ac84663` | FAIL | old multicast rect default hit unmapped harvested coordinate | scheduler known-failures section | `hardware-logs/8ac84663.txt` |
| `3052ebb0` | PASS | multicast rect sweep after harvested-coordinate fix | `noc-scheduler-model.md` summary | `hardware-logs/3052ebb0.txt` |
| `27b58305` | PASS | topology experiments C/D | `noc-topology.md` | `hardware-logs/27b58305.txt` |
| `1c04b1f3` | PASS | row stream sweep, NoC0/1, <=8 hops, 1 MiB streams | `noc-stream-sweep.md` | `hardware-logs/1c04b1f3.txt` |
| `9bc25ff5` | PASS | packet latency, read/write, NoC0/1, 4..16 KiB, 1D/2D routes | `noc-packet-latency.md` | `hardware-logs/9bc25ff5.txt` |
| `6e017354` | PASS | same-target arbitration, K=2..8, 16 KiB | `noc-arbitration.md` | `hardware-logs/6e017354.txt` |
| `3e59ab0d` | PASS | DRAM bank/endpoint matrix, banks 0..6, endpoints 0..2 | `noc-dram-endpoint-matrix.md` | `hardware-logs/3e59ab0d.txt` |
| `17d0478d` | PASS | same BRISC active read+write, NoC0/1, separate targets | `noc-same-initiator-active.md` | `hardware-logs/17d0478d.txt` |
| `bbc60434` | PASS | same BRISC active read+write, same remote target smoke | `noc-same-initiator-active.md` | `hardware-logs/bbc60434.txt` |
| `19680ec3` | FAIL | two-RISC BRISC+NCRISC same-core mixed read/write, old same-target shape | scheduler known-failures section | `hardware-logs/19680ec3.txt` |
| `2211ee7d` | FAIL | two-RISC BRISC+NCRISC same-core mixed read/write, distinct target shape | scheduler known-failures section | `hardware-logs/2211ee7d.txt` |

## Notes For Offline Analysis

- The raw logs are stdout only. They do not include queue metadata beyond the
  job id encoded in the filename.
- `noc-scheduler-model.md` is the best single-file summary of conclusions.
- `noc-packet-latency.md`, `noc-arbitration.md`,
  `noc-dram-endpoint-matrix.md`, and `noc-same-initiator-active.md` contain the
  most scheduler-relevant detailed tables from the latest focused sweeps.
- Multicast detail is currently mostly in raw logs plus the scheduler summary.
  The runs passed, but the conversion from measurements to compact scheduler
  constants is still pending.
