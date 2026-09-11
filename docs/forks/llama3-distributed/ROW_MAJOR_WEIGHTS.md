# Row-major model weights

All decoder weights use exact global row-major storage: embedding, LM head,
Q/K/V/O, gate/up/down, and norm scales. RoPE tables and dense projection inputs
also use raw pages. Worker row ownership is metadata and does not add padded
per-worker copies. The 1B decoder shares embedding/LM storage; 8B retains its
independent LM head.

Model staging checks the layout and byte count, then writes physical bytes
directly. It never calls the NumPy tilizer. The generic Buffer API retains its
layout support for compute fragments and diagnostic tests. Dtype conversions
(BF16/FP8, scaling and hardware format handling) are unchanged.

GEMV and RMSNorm consume matching raw operand order with ordinary unpack/pack
operations. Gather/scatter addresses in residuals, SwiGLU, RoPE and attention
were adjusted for raw dense vectors. Compact outputs and attention caches
retain their internal compute layouts; no weight tilize/untilize operation was
added to the unpacker or packer. The standalone row-major K0 example also
explicitly allocates raw weights.

## Validation

```sh
python3 -m unittest discover -s tests -v
LLAMA_TEST_DEVICE=1 python3 -m unittest discover -s tests -p test_llama3_row_major_weights.py -v
```

The tests cover allocation sizes, row ownership, embedding/LM sharing,
byte-preserving staging (with NumPy layout entry points disabled), rejection
of tiled model uploads, and optional physical device readback. The existing
lowering tests cover supported bank/core topologies and resident L1 limits.

To compare a saved pre-change decoder on the same card and token history:

```sh
python3 -m examples.benchmark_row_major --device 1 \
  --reference /path/to/pre-change-llama3.py --steps 64 \
  --prompt 'Explain why the sky is blue' --teacher-force-reference \
  --logit-rms-tolerance 0.05 --output row-major-comparison.json
```

Add `--safetensor weights-published-fp8` for the published FP8 checkpoint.
The reference must retain this fork's model dimensions and tuning. Reordering
reductions can change rounded logits and occasionally token choices; exact
agreement and numerical error are reported separately. The 5% tolerance is a
workload comparison, not a downstream accuracy evaluation.

## Measured results (September 7, 2026)

Card 0, 64 generated tokens with identical reference history:
152.33 tok/s tiled, 152.24 tok/s raw (-0.06%).
All token choices matched; maximum sampled logit relative RMS error was
2.76438%. See [report](validation/row-major-weights.json).
