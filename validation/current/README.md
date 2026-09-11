# Consolidation validation — 2026-09-11

All runs below used code and checkpoints in the main `blackhole-py` directory.
Device commands ran through `tt-device-queue`, with both cards reserved for
TP2. Python 3.14.3, NumPy 2.4.6, and Transformers 5.5.1 were used.

## Requested configurations

| Runner | Cards | Result | Short-run decode rate |
| --- | --- | --- | --- |
| `examples.llama3_1b` | 0 | “The capital of France is Paris.” | 153.72 tok/s |
| `examples.llama3_8b` | 1 | “The capital of France is Paris.” | 29.59 tok/s |
| `examples.llama3_8b_fp8` | 0 | “The capital of France is Paris.” | 48.48 tok/s |
| `examples.llama3_tp2` | 0 + 1 | “Paris, which is located in the north-central part of the country…” | 66.21 tok/s |

Single-card smoke runs used `--steps 16 --profile` and the prompt
“What is the capital of France? Answer in one short sentence.” They stop at
EOS; these short-run rates exclude weight loading and prompt ingestion and
are not broad performance benchmarks. The TP2 smoke run used its default raw
completion prompt and 16 generation steps. The associated logs and TP2 JSON
are in this directory.

## Longer TP2 comparison and known numerical limit

`tp2-comparison.json` records three prompts with 64 generated tokens each,
feeding the same history to single-card mixed FP8 and TP2. All **250/250**
greedy decisions matched, including prompt positions. Aggregate generation
rates were **48.11 tok/s** single-card and **66.29 tok/s** TP2 (1.378×).

The benchmark exits nonzero: maximum relative logit RMS error is **0.12350148**,
above its 0.05 limit; minimum sampled PCC is **0.99295585**. This is a preserved
pre-existing limitation, not a passing numerical-quality test. The historical
`docs/forks/llama3-8b-fp8-tp2/validation/tp2-comparison-pack.json` has exactly the
same per-position decisions and error metrics. All 21 saved single-card
reference logit arrays are also bitwise identical to the pre-port arrays.
`port-regression.json` records that comparison. No tolerance was loosened.

Reproduce the benchmark under a reservation of both cards:

```sh
.venv/bin/python -m scripts.llama3_8b_fp8.benchmark_tp2 --steps 64 \
  --output validation/current/tp2-comparison.json
```

Then check port preservation independently of the unchanged quality limit:

```sh
.venv/bin/python -m scripts.check_port_regression
```

The checker uses the archived report and per-array hashes inside this repo;
it does not need the sibling forks. The large current `.npz` arrays remain
local and ignored; rerunning the benchmark recreates them.

## Prefill, speculation, firmware, and runtime

- `prefill.json`: 8B BF16 prompts of lengths 1, 4, 5, and 17 with chunk size 4.
  Logits were bitwise equal to sequential ingestion, and the first token plus
  two continuation tokens matched in every case. Prefill was slower for these
  short prompts; it remains opt-in. `prefill-cli.log` verifies `--prefill` also
  generates the Paris answer through the main runner.
- `speculative.json`: 32-token, minimum-ngram-1 run matched ordinary greedy
  tokens exactly. Nine proposals were rejected; this checks rejection recovery,
  not a speedup claim. The CPU suite also covers verifier construction.
- `runtime-hardware.log`: **62 passed**. Includes raw external transfers and
  CB operations, live cache/fusion/prefetch checks, all 24 parameter slots in
  resident replay, and BF16/FP8/F32 device-layout conversion. Layout readback
  matched an independent face-layout oracle and left the source unchanged.
- `firmware-images.json`: all four CQ service image hashes match the unchanged
  reference for both P100 and P150. Worker images use the approved larger ABI
  and central's protected prefetch/cache/fusion settings.
- `cpu-tests.log`: **150 passed, 1,204 hardware tests skipped, 797 subtests
  passed**. Covers the original central tests plus the imported model tests.
  Later focused checks covered the final layout oracle and path defaults.

The combined hardware suite initially exposed fixture ownership: model tests
closed their own devices after the raw session fixture had booted. Model tests
now run before that shared fixture; the corrected combined run passed. This
was test ordering, not a firmware or model execution failure.

Main commands used for the additional checks, each under the matching queue:

```sh
.venv/bin/python -m scripts.llama3_8b.validate_prefill --device 1 \
  --lengths 1 4 5 17 --decode-steps 2 --output validation/current/prefill.json
.venv/bin/python -m examples.llama3_speculative --device 0 --steps 32 \
  --benchmark --min-ngram 1 --output validation/current/speculative.json
PYTHONPATH=. .venv/bin/python -m pytest -q tests/timing/test_firmware_cache.py \
  tests/models/test_runtime.py tests/operation_pocs/runtime \
  --bh-hardware --bh-device=0 -x
```
