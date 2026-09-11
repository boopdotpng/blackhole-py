# Decode performance

Measured on September 4, 2026: P150A, eight DRAM banks, 117 worker cores,
Llama 3.2 1B Instruct, batch one, original BF16 weights and HiFi2 arithmetic.
Reference: commit `cce3e77f3a245dadfaa4a29ae3a0dda499b53708`.

The measurements below describe the initial projection optimizations.
A subsequent attention fix raises short-context generation to **138.7 tok/s**;
see [the bottleneck analysis and follow-up results](decode-bottlenecks.md).

## Results

The benchmark times complete `decode()` calls, including trace submission and
token readback. It excludes initialization, prompt ingestion, text streaming,
and diagnostic logit reads. Generation runs for a fixed number of steps even
after EOS. Both versions run sequentially on the same card with the same prompts.

| Workload | Reference | Optimized |
|---|---:|---:|
| Three prompts, 64 generated tokens each, contexts 42–108 | 113.13 tok/s | 132.19 tok/s |
| Three prompts, 128 generated tokens each, contexts 42–172 | 110.60–110.82 tok/s | 128.76–129.04 tok/s |
| One prompt, 512 generated tokens, contexts 42–553 | 98.21 tok/s | 112.28 tok/s |

The short-context improvement is **16.9%**. Detailed short-context timings,
token IDs, and logit hashes are in
[the benchmark results](benchmarks/llama3_decode_p150a.json).

All 1,088 generated token IDs across these runs matched the reference exactly.
Sampled full BF16 logit buffers also matched exactly, including both sides of
32-token attention block boundaries. Separate randomized projection comparisons
passed bit for bit for 2048- and 8192-element inputs.

## Changes

- Split projection readers between NoC 0 and NoC 1 according to worker column;
  use the opposite NIU for each writer to keep transaction IDs independent.
- Specialize eight-bank weight reads by each shard's starting bank. Unroll one
  bank period to avoid repeated bank division, modulo, and endpoint selection.
- Configure invariant unpack formats and multiply state outside row loops.
  Issue SFPU replay directly so reduction and multiplication do not repeatedly
  replace the shared MOP configuration. Preserve the original reduction order.
- Fuse gate/up projections into one launch, sharing the activation load.
- Retain a compact generic reader on seven-bank devices. CPU tests lower the
  complete model and check kernel/template residency for all supported topologies.

## Remaining limit

The matrices contain approximately 2.471 GB of weights read per token. At the
supplied 512 GB/s peak, the weight-only ceiling is approximately 207 tok/s.
132.19 tok/s corresponds to about 327 GB/s of useful weight traffic, excluding
activation, padding, KV-cache, and command traffic.

Individual resident-kernel measurements at a one-block context show:

| Projection | Approximate latency | Useful weight bandwidth |
|---|---:|---:|
| Fused gate/up | 143.84 µs | 467 GB/s |
| Down | 78.69 µs | 426 GB/s |
| LM head | 1053.87 µs | 498 GB/s |

These timings include amortized trace/launch overhead. Large projections are
close to the bandwidth ceiling; smaller projections, attention, data movement,
and launches still limit end-to-end generation. Performance on seven-bank or
140-core firmware topologies has not been measured on hardware.

## Reproduce

```sh
git show cce3e77f3a245dadfaa4a29ae3a0dda499b53708:examples/llama3.py > /tmp/llama3-reference.py
PYTHONPATH=. python3 examples/benchmark_llama3.py \
  --reference /tmp/llama3-reference.py --steps 64 --output result.json
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

Use `--steps 512 --prompt "Explain why the sky is blue"` for the longer comparison.
