# Llama SFPU argmax integration — card 0

The shared Llama argmax now uses SFPU to scan BF16 logits for 1B BF16,
8B BF16 and 8B FP8. BRISC reduces 32 candidates per core and the cross-core
winners, then publishes the token and updates history/runtime state.
Padding is masked to negative infinity; equal values retain the first index.

## Complete argmax kernel

Reducer BRISC entry-to-exit cycles, including DRAM reads, padding, unpack,
SFPU scan, packing, candidate/global reduction, host publication, token-history
write and runtime-state multicast. Excludes firmware/dispatch before entry.
The original scalar method and new method ran alternately on identical seeded
128,256-logit inputs using the actual model buffer layouts. Medians of eight
samples after one warmup per variant. Full samples: [JSON](llama_argmax_results.json).

| Model | Cores | Scalar cycles | SFPU cycles | Speedup |
|---|---:|---:|---:|---:|
| 1B BF16 | 117 | 48,195 | 12,605 | 3.82× |
| 8B BF16 | 88 | 68,042 | 18,317.5 | 3.71× |
| 8B FP8 | 96 | 62,174 | 17,249.5 | 3.60× |

## Generation

Prompt: `Explain why the sky is blue in detail.`; 128 generated tokens,
normal decode, default model settings, card 0. The baseline restores only the
original `decode_argmax` method in the same workspace; other code is identical.
One run per variant, so these small differences should not be overinterpreted.
The entire generated text matched before/after for each model.

| Model | Scalar tok/s | SFPU tok/s | Device/CQ µs saved per token |
|---|---:|---:|---:|
| 1B BF16 | 152.33 | 152.90 | 25.65 |
| 8B BF16 | 29.43 | 29.47 | 37.74 |
| 8B FP8 | 47.67 | 47.78 | 41.72 |

Argmax is a small portion of total decode time; its kernel speedup produces
only a small end-to-end throughput improvement. Longer generation also changes
the context length relative to shorter benchmarks.

## Validation

42 hardware tests passed, including all three models at all six supported core
counts, negative/positive ties, signed zeros, infinities, subnormals, poisoned
padding, last-token winners, host publication, complete token-history contents,
append disabled, page boundaries, runtime-state multicast and repeated resident
trace replay. The standalone SFPU tests and 250k-vocabulary tests also passed.

```sh
tt-device-queue run --device 0 --cwd "$PWD" -- '../.venv/bin/python -m pytest -q tests/compute/sfpu/test_llama_argmax.py tests/compute/sfpu/test_argmax.py tests/compute/sfpu/test_argmax_vocab.py --bh-hardware --bh-device 0'
```

An additional 8B BF16 chunked-prefill + 8-token generation smoke test passed.
Queue jobs: tests `b0c18dd7ddf84399b1640cd3f1b0b070`, kernel timings
`c830a52ee31f46fe957e1f188583c1fd`, generation
`65a6492fa8414a57a2c8a40a9af671cb`, prefill
`cb05b5771709485c8fc604ee49e73511`.
