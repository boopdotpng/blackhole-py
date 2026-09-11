# Llama 3 8B Instruct on card 1

Measured September 7, 2026. P150A, eight DRAM banks, stock 120-core topology
(117 application workers after reserving three command-queue service cores).
Full BF16 weights and the original projection arithmetic; no quantization.

## Final sustained generation

| Workload | Throughput |
|---|---:|
| Three prompts, 64 tokens each | **29.37 tok/s** |
| Three prompts, 512 tokens each | **28.54 tok/s** |
| Initial 117-worker / 16-attention-worker runtime | approximately 28.9–29.0 tok/s |
| Best fixed teacher-forced tuning sample | 29.42 tok/s |

The final default is **88 evenly placed projection workers and 32 attention
workers**, with 163 resident launches per token. All projection matrices are
stored contiguously in global DRAM; per-core views partition output rows without
padding the stored weights. Peak allocated device memory is
17.141 GB, including the full 8,192-token cache.

Timings include full decode calls and token readback. They exclude weight loading,
prompt ingestion, and diagnostic logit reads. Fixed-length benchmarks continue
through EOS. The interactive `examples/llama3.py` command stops at EOS normally.

The model reads approximately 15.010 GB of useful
weights per token. At the supplied 512 GB/s peak, its weight-only ceiling is
34.11 tok/s. The short benchmark reaches **86.1%** of that ceiling,
or 440.8 GB/s of useful weight traffic. This exceeds
the approximately 75% efficiency reported for the 1B run, but **does not reach
the requested 32–34 tok/s target**. These percentages express bandwidth-ceiling
efficiency; compute-unit occupancy was not measured.

Raw results: [final generation and CPU checks](validation/card1-final.json).

## Core count and transfer tuning

The projections already used all 117 available application workers at baseline.
The 8B workload improves relative efficiency because more useful weight traffic
is handled per launch. Additional physical workers were not available on this
card's current firmware topology.

| Evenly placed projection workers, global weights, 32 attention workers | Fixed-context tok/s |
|---|---:|
| 117 | 29.10 |
| 112 | 25.03 |
| 104 | 28.99 |
| 96 | 29.31 |
| 88 | **29.42** |
| 80 | 28.80 |

Core count changes row lengths, bank starting positions, and contention as well
as available arithmetic. More workers did not monotonically increase throughput.
The 64-worker experiment timed out and was excluded; card 1 was recovered with
a targeted ASIC warm reset before subsequent successful tests. No firmware or
clock settings were changed.

The spatial NoC split inherited from 1B was best among the tested splits.
Distributing extra rows evenly and dividing NoC work by worker index did not
improve on the selected layout. Reusing fixed NIU command fields preserved exact
results but did not improve throughput. Those experimental implementations are
not enabled in the final runtime. All successful worker-layout comparisons
matched every teacher-forced predicted token and sampled full vocabulary logits
exactly against the baseline.

The [initial kernel profile](validation/card1-initial-profile.json) attributed
approximately 24.3 ms of a 34.45-ms decode to gate/up and down projections,
6.5 ms to QKV/output projections, 2.2 ms to the LM head, and 1.35 ms to attention
at context 32. Further progress toward 32 tok/s requires more projection/DRAM
throughput; host overhead is only tens of microseconds per token.

Other raw measurements:
[NoC/attention sweep](validation/card1-tuning.json),
[worker-count sweep](validation/card1-worker-tuning.json),
[shard distribution sweep](validation/card1-shard-tuning.json), and
[global-weight layout comparison](validation/card1-global-weights.json).

## Correctness and preparation

- Downloaded and validated all 291 BF16 tensors in four pinned checkpoint shards.
  SHA-256 digests and nine card-free lowering configurations are in
  [preflight results](validation/preflight.json).
- The CPU Instruct reference answered “The capital of France is Paris.”
- The first card test exposed a padded LM-head upload that shifted higher token
  IDs. Uploading the separate output matrix through its contiguous storage view
  fixed it. All eight teacher-forced answer tokens, including EOS, then matched
  the CPU reference, with logit correlation above 0.9995.
- The final configuration passed 15 additional CPU logit comparisons at positions
  0, 1, 7, 8, 15, 16, 31, 32, 63, 64, 127, 128, 255, 256, and 511. Correlations
  ranged from 0.997997 to 0.999962.
  Fourteen of 15 greedy predictions matched; position 0 differed. This is not
  bit-exact equivalence to Transformers: the inherited device arithmetic rounds
  several intermediates differently.
- All five CPU tests pass, including all nine topology/attention combinations.
- Final generation benchmarks cover 1,728 generated tokens across six runs.
  Hardware validation covers contexts through approximately 540 tokens; the full
  8,192-token cache is allocated but that maximum context has not been exercised.

## Reproduce

```sh
PYTHONPATH=. .venv/bin/python scripts/validate_card.py --device 1
PYTHONPATH=. .venv/bin/python examples/llama3.py \
  --device 1 --steps 32 --prompt 'Explain why the sky is blue' --profile
```

The original source snapshot is the repository's first commit. The validated
117-worker 8B baseline is commit `da98c4e`; this report describes the tuned working
revision. Checkpoint provenance and license details are in [MODEL.md](MODEL.md).

## September 9 firmware update

L0 cache and Tensix instruction fusion are now enabled. The [validation and
TT-NN comparison](validation/risc-config-results.md) measured **29.63 tok/s**
for three 64-token prompts on card 1, **1.46% above** the saved September 7
BF16 TT-NN result. The firmware change contributes about
**0.63%** versus today's baseline, with exact token and
sampled-logit matches at 64 and 256 generated tokens.
