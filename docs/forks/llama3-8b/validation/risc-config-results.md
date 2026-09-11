# BF16 8B cache/fusion and historical TT-NN comparison

Measured September 9, 2026. **L0 data cache and Tensix instruction fusion are enabled by default** in [`Asm.configure_csr()`](../asm.py). CSR `0x7C0` bits 3 (`DisLowCash`) and 18 (`DisTriscCache`) are cleared. Existing synchronization fences and firmware sizes are preserved. Normal firmware images match the hardware-tested `both` mode by SHA-256 for all five worker RISCs on both cards.

## Same-card comparison with the earlier TT-NN run

Found the requested September 7 Codex conversation, session `01a07e85-f38a-7be3-b96e-03e3b2771030`, beginning “Can you check if Tenstorrent has an official way to run LLaMA 3 8B inference on Blackhole cards?” That conversation produced [`tt-bf16-benchmark`](../../tt-bf16-benchmark/README.md). Its recorded reference is TT-NN 0.78.0 with matching tt-metal release sources, configured for BF16 weights/activations/KV cache, HiFi2 multiplication and FP32 accumulation.

All rows below use physical card 1, original Llama 3 8B Instruct weights, batch-one greedy decode, and the same three prompts. Prompt token IDs were verified equal against the original TT-NN JSON. TT-NN results are the saved September 7 measurements, **not a new TT-NN execution**. Custom measurements are from September 9 with baseline → both enabled → baseline order.

| Prompt | Saved TT-NN tok/s | Current baseline tok/s | Both enabled tok/s | Baseline repeat tok/s | Enabled vs saved TT-NN |
|---|---:|---:|---:|---:|---:|
| Sky | 29.2452 | 29.4366 | 29.6284 | 29.4413 | 1.311% |
| Fibonacci | 29.1874 | 29.4385 | 29.6246 | 29.4378 | 1.498% |
| Ocean | 29.1736 | 29.4431 | 29.6278 | 29.4462 | 1.557% |
| Aggregate | **29.2020** | **29.4394** | **29.6269** | **29.4417** | **1.455%** |

The new enabled result is **1.46% faster than the saved TT-NN run**. The flags themselves improve throughput **0.63%** against the mean of today's baselines. Aggregate baseline drift is 0.008%.

This is a small measured lead for this workload, not a general claim of superiority over tt-metal. The historical reference uses 63 timed decode iterations per prompt after excluding its first decode iteration, while the custom path times all 64 full decode calls including token readback. Both exclude loading, prefill and compilation; custom diagnostic logit readbacks are also excluded. TT-NN/custom arithmetic is not bit-identical: generated prefixes match 64/64, 64/64 and 34/64 tokens. There is no new long-context TT-NN result in this comparison.

## Correctness and longer generation

Both-enabled firmware matches original firmware exactly for every generated token and sampled full-vocabulary BF16 logit hash, on all three prompts at both tested lengths:

| Test | Card | Baseline tok/s | Enabled tok/s | Gain |
|---|---:|---:|---:|---:|
| 64 generated tokens/prompt | 1 | 29.4394 | 29.6269 | 0.637% |
| 256 generated tokens/prompt | 0 | 29.0873 | 29.2663 | 0.615% |

Logits are sampled at the first and last generated token and both sides of each 32-token attention boundary. Generation continues through EOS to keep the measured length fixed. The 64-token baseline repeat also matches exactly. The CPU suite ran 11 tests: 10 passed and one opt-in hardware readback test was skipped. Both hardware inference jobs passed separately.

## Reproduction and raw evidence

From this repository, submit these commands through `tt-device-queue` on the queue matching the selected physical card, with `PYTHONPATH=.` and `OPENBLAS_NUM_THREADS=1`:

```bash
.venv/bin/python scripts/benchmark_risc_config.py --device 1 --steps 64 \
  --modes baseline both baseline --output validation/risc-config-card1-64.json
.venv/bin/python scripts/benchmark_risc_config.py --device 0 --steps 256 \
  --modes baseline both --output validation/risc-config-card0-256.json
```

The script constructs original firmware explicitly for baseline, even with the new defaults. Each mode creates a fresh runtime. All rates aggregate token count divided by summed decode durations, rather than averaging per-prompt rates.

- [64-token measurements](risc-config-card1-64.json), job `d32695ceb54746d7939e62664ec1f02c`.
- [256-token measurements](risc-config-card0-256.json), job `3104634fed174cd492842f2fb6c7d3ab`.
- [Machine-readable comparison](risc-config-ttnn-comparison.json).
- [Queue metadata](risc-config-evidence/runs.json), compressed logs, CPU test output and final source snapshots in `risc-config-evidence/`.
- [Original assembler](risc-config-original-asm.py). Experiment JSON source hashes describe the original assembler; `risc-config-evidence/source/asm.py` is the final enabled default.
- [Saved TT-NN raw data](../../tt-bf16-benchmark/ttnn-64.json) and [original comparison](../../tt-bf16-benchmark/comparison.json) are preserved unchanged.
