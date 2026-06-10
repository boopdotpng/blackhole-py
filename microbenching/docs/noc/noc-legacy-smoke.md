# Legacy NoC/DRAM Smoke Run

Goal: cautiously exercise the stable NoC and DRAM microbenches with the smallest
safe hardware runs, through the shared `tt-device-queue` owner only.

## Run 2026-06-09

Health checks were taken before the suite, between benchmarks, and after the
final multicast smoke. The device stayed healthy throughout:

- Board: `p100a`
- Tensix cores: `120`
- AICLK: `800 MHz`
- PCIe: `32.0 GT/s PCIe x16`
- GDDR enabled mask: `0xf7`
- GDDR corrected/uncorrected error counters: all `0`

All hardware commands were queued with an outer `timeout 30` and no benchmark
was run directly outside the queue. `microbenching/noc/riscv_noc_hop_sweep.py` and pointer-chase
style probes were not run.

| bench | queue job | smoke command shape | result |
|---|---|---|---|
| `microbenching/noc/riscv_noc_bench.py` | `652ee11f` | `--target local --iters 1 --no-report` | pass |
| `microbenching/noc/riscv_noc_aggregate.py` | `670cfa88` | `--noc 0 --bytes 16384 --counts 1 --no-report` | pass |
| `microbenching/noc/riscv_noc_dual_aggregate.py` | `9f1e5493` | `--bytes-per-noc 16384 --counts 1 --no-report` | pass |
| `microbenching/noc/riscv_noc_dual_dm_aggregate.py` | `e9bfeb1d` | `--bytes-per-noc 16384 --counts 1 --no-report` | pass |
| `microbenching/noc/riscv_noc_stream_sweep.py` | `b9a5f6fd` | `--mode all-to-one --nocs 0 --max-sources 1 --bytes 16384 --repeats 1 --no-report` | pass |
| `microbenching/noc/riscv_noc_write_observe.py` | `fa473879` | `--noc 0 --source 1,2 --target 2,2 --bytes 16384` | pass |
| `microbenching/noc/riscv_dram_noc_bench.py` | `6a3d0709` | `--ops read --nocs 0 --counts 1 --bytes-per-core 2048 --packet-bytes 2048 --no-report` | pass |
| `microbenching/noc/microbench_noc_mcast_mixed.py` | `2dd6db0e` | `--cases row --dests 1 --iters 1 --skip-mixed --no-report` | pass |

## Result Notes

- `microbenching/noc/riscv_noc_bench.py`: local one-iteration smoke completed on both NoCs. The
  local 4-byte read flush rows were `105` cycles on NoC0 and NoC1; local 4-byte
  write barrier rows were `95` cycles on both NoCs. Every active row reported
  counter delta `1` and sink `0xa5000000`.
- `microbenching/noc/riscv_noc_aggregate.py`: one NoC0 adjacent pair, one 16 KiB write, sender
  window `503` cycles, receiver window `365` cycles, bad ack rows `0`, bad
  sentinel rows `0`.
- `microbenching/noc/riscv_noc_dual_aggregate.py`: one adjacent pair, 16 KiB per NoC, sender
  window `523` cycles, receiver window `526` cycles, bad ack rows `0`, bad
  sentinel rows `0`.
- `microbenching/noc/riscv_noc_dual_dm_aggregate.py`: one adjacent pair, BRISC NoC0 plus NCRISC
  NoC1, 16 KiB per NoC, sender window `510` cycles, receiver window `504`
  cycles, bad ack rows `0`, bad sentinel rows `0`.
- `microbenching/noc/riscv_noc_stream_sweep.py`: one all-to-one self stream on NoC0, 16 KiB,
  read `324` cycles / `50.568 B/cyc`, write `321` cycles / `51.040 B/cyc`,
  sinks `0xa5000000`.
- `microbenching/noc/riscv_noc_write_observe.py`: adjacent NoC0 16 KiB write, sender barrier
  delta `503` cycles, receiver sentinel delta `366` cycles, observed-minus-ack
  `-137` cycles, ack counter delta `1`, sentinel `0xa5003ffc`.
- `microbenching/noc/riscv_dram_noc_bench.py`: one-core NoC0 DRAM read, one 2 KiB packet,
  window `559` cycles, `3.664 B/cyc`, bad counter rows `0`.
- `microbenching/noc/microbench_noc_mcast_mixed.py`: documented safest row multicast smoke passed
  with one destination and mixed traffic skipped. NoC0 16 KiB multicast was
  `351` cycles / `51.040 B/cyc`; NoC1 16 KiB multicast was `559` cycles /
  `30.972 B/cyc`. Validation showed source `1,2` and receiver `2,2` final words
  `0xa5003ffc`, with semaphore values `1` and `2`.

No candidate in this list was skipped: each had a clearly tiny, bounded smoke
configuration. No timeouts, ARC-not-ready failures, hung cores, bad health
checks, or unexpected validation failures were observed.
