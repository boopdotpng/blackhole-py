# FP8 input / FP16 accumulation profile

2026-09-16, physical Card 1 (p150a), queue 1. ARC AICLK telemetry
reported 1350 MHz after each measured launch. No device instructions were
added: the profiler reads the existing per-core timestamps after completion.

Reproduce from blackhole-py:

```sh
tt-device-queue run --device 1 --cwd /home/boop/tenstorrent/blackhole-py -- '../.venv/bin/python tests/movement/profile_matmul_fp8.py --device 1 --runs 9 --json tests/movement/matmul_fp8_profile.json'
```

## Measurement

5000 x 5000 x 5000; FP8 E4M3FN inputs, FP16 accumulator, partials and output.
110 workers (10 x 11), 2 x 4 output subblocks, K block 10. Compute padding:
5040 x 5008 x 5104. Nine launches after warmup; normal output validation passed:
PCC 0.999999, relative L2 0.005204. Fusion enabled on every TRISC.

| Metric | Mean |
|---|---:|
| Completion-inclusive kernel | 737.34 us |
| Logical throughput | 339.06 TFLOPS |
| Padded throughput | 349.43 TFLOPS |
| Math controller finished, relative to earliest BRISC start | 617.57 us |
| Pack controller finished, same origin | 618.02 us |
| Output tail after all pack controllers finish | 119.32 us |
| Longest per-core input-reader phase | 561.05 us |
| Longest per-core output-writer phase | 176.52 us |

Kernel range: 735.56–739.15 us. Phase durations overlap and must not be
summed. Input duration includes compute backpressure; it is not an isolated
DRAM bandwidth measurement. Output phase includes waiting for final packed
results. The unhidden output tail is 16.18% of kernel time, while the whole
output phase is 23.94%. These numbers do not isolate NoC contention from
writer instruction overhead or DRAM service time.

## Peak check

[Official card specifications](https://docs.tenstorrent.com/aibs/blackhole/)
list 120 Tensix cores, up to 1.35 GHz and 664 TFLOPS **BLOCKFP8**. This kernel
uses E4M3FN storage expanded to FP16 and one matrix fidelity phase, so the
applicable arithmetic ceiling is also the one-phase matrix engine ceiling;
the advertised format should not be confused with the kernel's storage format.

At 4096 FLOPs per core-cycle (multiply + add counted as two FLOPs):

- 120 physical cores: 663.552 TFLOPS.
- 117 workers after reserving three runtime cores: 646.963 TFLOPS.
- This kernel's 110-core rectangular grid: 608.256 TFLOPS.

The instruction throughput and fidelity model are documented in the
[Matrix Unit ISA](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/MatrixUnit.md).
The per-core rate and official Blackhole product specification agree.

This shape executes 257.653 GFLOPs for 250 logical GFLOPs. Even at perfect
arithmetic utilization, padding lowers the logical ceiling to **590.19
TFLOPS**, requiring 423.59 us of arithmetic. This excludes all pipeline and
memory overhead.

The observed start-to-pack-completion interval is 618.02 us, about 68.54%
of that arithmetic ceiling. Keeping that interval fixed while eliminating
the entire remaining output tail would yield **404.52 logical TFLOPS**.
This is a timing counterfactual, not a tested optimization or a bound on
all possible writer changes (which could also reduce earlier backpressure).

Consequently, approximately 600 TFLOPS is a sensible compute-peak target,
but output optimization alone does not explain the current gap. The next
profiling target is unpack/math/pack synchronization and partial-result
traffic during the compute interval. Existing fine-grained accumulated
counter hooks in kernel.py are no-ops; this report does not claim to measure
matrix busy cycles or individual semaphore stalls.

Raw timestamps for every core and launch are in matmul_fp8_profile.json.
The companion profile_matmul_fp8.py preserves the production kernel.
