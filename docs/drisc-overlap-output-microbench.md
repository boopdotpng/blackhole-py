# DRISC Overlap And Output Write Microbench

Date: 2026-06-08

This note records a focused Blackhole run for constants useful to a static
`Program` timing model. The new harness is
`examples/microbench_drisc_overlap_output.py`.

## Commands Run

All hardware-touching commands were run through the Tenstorrent device queue.

```bash
env PYTHONDONTWRITEBYTECODE=1 python3 examples/microbench_drisc_overlap_output.py --timeout 5
env PYTHONDONTWRITEBYTECODE=1 python3 examples/drisc_gddr_dma_poc.py --size 2048 --iters 1024 --timeout 5
env PYTHONDONTWRITEBYTECODE=1 python3 examples/drisc_gddr_dma_poc.py --size 100352 --iters 256 --timeout 5
env PYTHONDONTWRITEBYTECODE=1 python3 examples/drisc_gddr_to_worker_poc.py --mode direct --no-dma --size 65536 --timeout 5
env PYTHONDONTWRITEBYTECODE=1 python3 examples/riscv_dram_noc_bench.py --ops write --nocs 1 --counts 1 --bytes-per-core 131072 --packet-bytes 2048 --stateful --no-report
env PYTHONDONTWRITEBYTECODE=1 python3 examples/riscv_dram_noc_bench.py --ops write --nocs 1 --counts 1 --bytes-per-core 2097152 --packet-bytes 2048 --stateful --no-report
```

Device reset commands were also queued after failed experimental kernels.

## Results

### Validated Harness Default

`microbench_drisc_overlap_output.py --timeout 5` currently routes the validated
`drisc_dma` and `drisc_stage` modes through the existing known-good PoC kernels.

| mode | page B | pages | MiB | cycles | B/cyc | GB/s | ok | note |
|---|---:|---:|---:|---:|---:|---:|---|---|
| `drisc_dma` | 2048 | 32 | 0.06 | 7116 | 9.210 | 12.4 | True | GDDR->DRISC L1 read, repeated 2 KiB descriptor |
| `drisc_stage` | 2048 | 32 | 0.06 | 0 | 0.000 | 0.0 | True | correctness only; source PoC does not stamp cycles |

### DRISC GDDR DMA

| transfer | iters | total bytes | read cycles | read GB/s | write cycles | write GB/s | useful model point |
|---:|---:|---:|---:|---:|---:|---:|---|
| 2048 B | 1024 | 2,097,152 | 213,592 | 13.3 | 105,494 | 26.8 | descriptor-limited tile stream |
| 100,352 B | 256 | 25,690,112 | 583,958 | 59.4 | 542,192 | 64.0 | large-transfer DRISC DMA roof in this harness |

Derived per-tile costs for 2 KiB tiles:

| path | cycles/tile | ns/tile at 1.35 GHz |
|---|---:|---:|
| GDDR -> DRISC L1 read | 208.6 | 154.5 |
| DRISC L1 -> GDDR write | 103.0 | 76.3 |

### Worker Stateful 2 KiB DRAM Writes

This uses `riscv_dram_noc_bench.py --stateful` as a proxy for the NCRISC
matmul C-output writer stateful tile write/barrier pattern.

| tiles | bytes | cycles | cycles/tile | GB/s |
|---:|---:|---:|---:|---:|
| 64 | 131,072 | 2,942 | 46.0 | 60.1 |
| 1024 | 2,097,152 | 38,258 | 37.4 | 74.0 |

The 1024-tile run corresponds to about `28.3 us` for a 2 MiB single-worker
stateful output stream.

## Limitations

- The combined custom DRISC DMA/stage overlap kernels in
  `microbench_drisc_overlap_output.py` are present but still experimental.
  During this run, `dma2`, `serial`, `pipe`, and `pipe2` timed out inside the
  low-level DRISC kernel. The validated default therefore uses the existing PoC
  builders for `drisc_dma` and `drisc_stage`.
- `drisc_stage` is currently a correctness check only because
  `drisc_gddr_to_worker_poc.py` does not stamp cycles around
  `emit_worker_writes`.
- The standalone ncrisc-only output writer path timed out at command-queue
  completion. The stateful worker write numbers above come from the existing
  BRISC NoC benchmark and should be treated as a proxy for NCRISC C-output
  stateful writes until a matmul-shaped NCRISC harness is made launch-clean.
- Single vs two DRISC DMA stream timing remains unresolved in this harness.
  The existing API exposes two TX streams, but the custom two-stream microkernel
  did not produce a valid run today.

## Proposed Program Timing Model Constants

For `examples/program_timing_model.py`:

| constant / model term | proposed value | rationale |
|---|---:|---|
| `DRISC_DMA_GBPS` large-transfer roof | `59.4` | measured GDDR->DRISC L1 read at 100,352 B transfers |
| DRISC 2 KiB read tile cost | `209 cycles/tile` | measured 1024 repeated 2 KiB DMA reads |
| DRISC 2 KiB write tile cost | `103 cycles/tile` | measured 1024 repeated 2 KiB DMA writes |
| stateful output write cost | `37.5 cycles/tile` | 1024-tile worker stateful write proxy |
| single-worker output write GB/s | `74.0` | smoothed 1024-tile stateful write proxy |
| `OUTPUT_TAIL_US` for 1024 C tiles | `28.3 us` | `38,258 / 1350` |

Recommendation: keep `DRAM_WRITE_GBPS = 245.7` as an aggregate-chip constant
for broad DRAM-write roof modeling, but model per-core C-output tail with a
tile-count term near `37.5 cycles/tile` instead of a single fixed tail when the
shape exposes per-core output tile counts.
