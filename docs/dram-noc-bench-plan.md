# Blackhole DRAM NoC Benchmark Plan

Goal: measure device-side DRAM-to-L1 and L1-to-DRAM bandwidth through the NoC,
without mixing in host PCIe/sysmem transfer time.

The existing `Device.dram_write` and `Device.dram_read` paths are useful for
host transfers, and `fw/dram.py` has fast-dispatch sysmem fill/drain kernels.
Those are not pure DRAM NoC benchmarks: they include PCIe/sysmem on one side.

## What To Measure

Start with unicast, non-multicast paths that should not trip the multicast
router issue.

1. DRAM read into L1
   - Worker issues `noc_read` from a DRAM bank address to a local L1 buffer.
   - Completion is `noc_reads_flushed`.
   - Measure single-core, per-bank, and aggregate runs.

2. L1 write to DRAM
   - Worker writes from a local L1 buffer to a DRAM bank address.
   - Completion is `noc_write_barrier`.
   - Measure posted and nonposted variants if both are useful.

3. Bank contention
   - Spread workers evenly across all enabled banks.
   - Then force many workers to one bank.
   - Compare per-bank saturation and all-bank aggregate bandwidth.

4. NoC selection
   - NoC0 read path, matching the A-reader style in `matmul_peak.py`.
   - NoC1 read path, matching the B-reader style in `matmul_peak.py`.
   - NoC1 write path, matching output writeback in `matmul_peak.py`.

5. Dual data-movement pressure
   - BRISC reads/writes over NoC0 while NCRISC reads/writes over NoC1.
   - Keep source and destination regions separate.
   - Treat this as a pressure test, not a headline fabric peak unless routing
     directions and bank assignment are controlled.

## Harness Shape

Add an `examples/riscv_dram_noc_bench.py` style harness:

- Allocate a large DRAM buffer with `Device.dram.alloc`.
- Seed it from the host only before timing.
- Run only device kernels during the measured window.
- Use wall-clock timestamps on the worker cores.
- Use NoC counters for read responses and write acknowledgements.
- Use payload sizes much larger than one tile, e.g. `1 MiB` to `16 MiB` per
  active core, split into legal NoC bursts.
- Record both per-core bandwidth and aggregate bandwidth.

The initial harness now lives in `examples/riscv_dram_noc_bench.py`. It uses
BF16 tile-sized `2048 B` transfers because that is the path used by
`examples/matmul_peak.py`: one NoC command per tile, with DRAM bank selection
coming from the firmware DRAM-bank-to-NoC table. It supports both bank-spread
and single-bank pressure modes.

On P100a, the usable configuration is seven `4 GiB` DRAM banks/controllers, for
`28 GiB` total. Each controller has three DRAM NoC tile endpoints. The first
version of the harness uses the firmware bank table, which selects the same
endpoint convention as the existing matmul kernels. A separate endpoint sweep
can directly target each of the three DRAM tiles per controller if we want to
check whether endpoint choice changes bandwidth or routing behavior.

Endpoint sweep modes in `examples/riscv_dram_noc_bench.py`:

| mode | meaning |
|---|---|
| `preferred` | use the firmware DRAM-bank-to-NoC table |
| `0`, `1`, `2` | bypass the table and directly target that endpoint of each selected bank |
| `split3` | bypass the table and stripe workers over endpoints `0`, `1`, and `2` |

Useful run axes:

| axis | values |
|---|---|
| op | `read`, `write`, `read_write` |
| NoC | `0`, `1` |
| banks | `spread`, `single-bank`, explicit bank id |
| cores | `1`, `2`, `4`, `8`, `16`, `32`, all |
| bytes/core | `1 MiB`, `4 MiB`, `16 MiB` |
| packet bytes | `2048`, `4096`, `8192`, `16384` |
| address pattern | contiguous per bank, tiled/interleaved tensor pages |

## Expected Matmul Relevance

`examples/matmul_peak.py` currently uses:

- BRISC/NoC0 to read A tiles from DRAM, then multicast A across columns.
- NCRISC/NoC1 to read B tiles from DRAM, then multicast B across rows.
- NCRISC/NoC1 to write C tiles back to DRAM.

So the most relevant DRAM microbenchmarks are DRAM-to-L1 reads on both NoCs,
plus L1-to-DRAM writes on NoC1. NoC-to-DRAM writes are already less mysterious
than the read/feed side, but output writeback is still worth measuring as part
of the matmul budget.
