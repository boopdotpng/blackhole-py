# Llama decode without weight tilization

`examples/llama3.py` now uploads every BF16 model weight in its original
checkpoint shape and byte order. Projection matrices use exact global storage;
117-core row ownership is metadata, with no padded per-core weight copies.
Embedding and LM head share one allocation. Norm weights and RoPE tables also
remain row-major. Upload staging copies the original bytes directly.

The launch graph, double-buffered weight reads, FPU multiply, SFPU reduction,
compact output ownership, and resident trace are preserved. Both operands of a
projection use the same raw 1024-element page order. The ordinary unpacker
applies the same permutation to both operands, so the dot product needs no
host or device weight tilize operation. RMSNorm has the same property.
Residual gathers and output scatters, attention context writes, and MLP dense
writes now address raw dense vectors correctly.

This is a weight-storage rewrite of the working decoder. Existing compact
activations, transient packed compute fragments, and attention/cache layouts
remain in use. It does not implement the separate all-buffer/82-launch plan in
`llama3-decode-row-major.md`.

## Card 1 results

Measured September 7, 2026 on card 1, P150A, 8 DRAM banks and 117 workers.
Both versions ran sequentially on that card, with original BF16 weights and
HiFi2 arithmetic. Timings include the complete decode call and token readback;
startup, prompt ingestion, and diagnostic logit reads are excluded.

| Workload | Tilized reference | Raw weights | Difference |
|---|---:|---:|---:|
| 64 generated tokens, context 42–105 | 138.76 tok/s | 138.16 tok/s | −0.43% |
| 512 generated tokens, context 42–553 | 135.37 tok/s | 134.74 tok/s | −0.47% |
| 512 tokens, reference history supplied to raw version | 135.38 tok/s | 134.74 tok/s | −0.47% |

The 128-token sweep covers three prompts: sky explanation, Fibonacci code,
and ocean facts. All 384 generated token IDs match. See its complete
[timings and sampled numerical errors](benchmarks/llama3_no_tilize_card1_128.json).

Outputs are **not bit-identical**. Changing page order changes FP32 reduction
order; BF16 rounding can amplify small differences through subsequent layers.
A stage-by-stage comparison starts with one Q value differing by 0.000061035
in layer 0. In unconstrained generation the 512-token run first chooses a
different token at generated token 137; later logits are therefore conditioned
on different text and should not be compared numerically.

With the same reference token history supplied to both versions, the 512-token
run has 506/512 matching top-1 predictions, minimum sampled logit cosine
similarity **0.9992849**, and maximum sampled relative RMS logit error
**3.8428%**. This passes the explicit 5% numerical tolerance, not an exact-output
test. The 128-token sweep has maximum sampled relative RMS error **3.4818%**.
These checks establish comparable behavior for these workloads; they are not
a perplexity or downstream task-quality evaluation.

Reports retain both the [free-generation divergence](benchmarks/llama3_no_tilize_card1_512.json)
and the [comparison with identical history](benchmarks/llama3_no_tilize_card1_teacher_512.json).
The benchmark defaults to exact comparison; tolerant comparison is opt-in and
reports exact agreement separately.

## Validation

- CPU tests check exact weight allocation size, shared embedding/LM storage,
  byte-preserving host staging, and complete lowering/L1 residency on all three
  supported DRAM/core configurations.
- Opt-in hardware tests compare randomized 2048- and 8192-wide GEMVs and RMSNorm
  to NumPy. Both raw and tilized GEMVs have the same approximately 0.66–0.68%
  relative RMS error from existing HiFi2 arithmetic and BF16 truncation, and
  match each other bit for bit for these fixed test inputs.
- Hardware readback confirms the raw projection matrices contain exactly the
  original uploaded bytes.

Before measurement, the original decoder also timed out on an empty launch at
worker `(1, 4)`. A reset targeted only `/dev/tenstorrent/1` cleared that state;
no runtime workaround or firmware change was needed.

## Reproduce

The reference is the decoder snapshot captured before this rewrite, including
pre-existing local optimizations. Its SHA-256 is
`096c9dc975e1ddc02f9c73ed8a564b2b99a06c52d9b5c49ef2c77444f60ba437`.
The session snapshot is `/tmp/llama3-before-no-tilize.py`; use an archived copy
of that source after the temporary file is removed. Reports also record source
hashes.

```sh
LLAMA_TEST_DEVICE=1 python3 -m unittest discover -s tests -v

python3 -m examples.benchmark_llama3 --device 1 \
  --reference /tmp/llama3-before-no-tilize.py \
  --steps 128 --logit-rms-tolerance 0.04 --output comparison-128.json

python3 -m examples.benchmark_llama3 --device 1 \
  --reference /tmp/llama3-before-no-tilize.py \
  --prompt 'Explain why the sky is blue' --steps 512 \
  --teacher-force-reference --logit-rms-tolerance 0.05 \
  --output comparison-512.json
```

Without `LLAMA_TEST_DEVICE`, unit tests perform CPU checks and skip hardware.
