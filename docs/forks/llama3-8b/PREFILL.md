# BS=1 BF16 prefill

`examples/llama3.py` now runs chunked prefill before BS=1 decode. The runtime
keeps the full BF16 Llama 3 8B weights resident and uses the same KV caches for
both phases. Existing uncommitted row-major weight and firmware changes are
preserved.

```sh
PYTHONPATH=. .venv/bin/python examples/llama3.py \
  --device 1 --safetensor weights --tokenizer weights \
  --prompt 'What is the capital of France? Answer in one short sentence.' \
  --steps 12 --prefill-chunk-size 4 --profile
```

The chunk size is a number of prompt tokens, **not a request batch size**. It
supports 1–8 tokens (default 4), with an exact-size kernel for the final partial
chunk. The prompt can contain 1–8191 tokens; it need not be tile-aligned. Kernel
variants and bounded activation scratch are created lazily on the first call.
The chunk size stays fixed for that runtime.

```python
from examples.llama3 import Llama3Decode

runtime = Llama3Decode("weights", device_index=1)
try:
    first_token, prefill_us = runtime.prefill(prompt_ids, chunk_size=4)
    # first_token is already written at token_history[len(prompt_ids)].
    second_token, decode_us = runtime.decode(len(prompt_ids))
finally:
    runtime.close()
```

Each `prefill` starts a new sequence at position zero. A new, shorter prompt
can reuse the same runtime: only valid cache positions participate in attention.
`append=False` returns the first greedy token without writing it into token
history. In that mode, upload the intended continuation before decoding it.
Empty prompts, invalid token IDs, non-integer IDs, and BS>1 inputs are rejected.
`load_tokens` and the original single-token `decode` API remain available for
reference comparisons and teacher forcing.

## Kernels and scheduling

`examples/llama3_prefill.py` implements:

- Grouped QKV and gate/up projections with local RMSNorm. Each core loads its
  chunk of activations once and reads each weight row once for all chunk tokens.
  The unpacker retains the buffered weight row until every token has used it.
  Dot products preserve the existing FP32 accumulation and BF16 rounding.
- A fused SwiGLU and compact-to-dense scatter kernel.
- Bank-aligned token scratch slabs whose per-token views exactly match the
  decode activation layouts, including compact per-worker projection fragments.
- A layer-major chunk scheduler. Each chunk completes all 32 layers before the
  next chunk. Existing RoPE/cache-append/online-GQA kernels process positions in
  causal order, followed by O and down projections with residuals. Only the
  final prompt token runs the final norm, LM head, and greedy argmax.

Prefill reuses resident decode kernels through small jump trampolines. New
kernel variants use the DRAM command-record cache, keeping the existing decode
trace and resident kernel arena intact. Host synchronization is bounded to one
layer at a time. No activation arithmetic or attention runs on the CPU.

This is a functional prefill baseline, **not yet an optimized tiled-GEMM or
multi-query attention implementation**. The retained-weight kernel still uses
the decode dot-product math. Full request batching and FP8/mixed weights are
not implemented. The separated sequence storage and projection entry points
provide places to add those implementations later.

## Validation and current performance

```sh
# CPU layout/lowering, validation, and existing decode regression checks.
PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -v

# Small hardware tests: standalone and grouped/RMSNorm projections must match
# decode byte for byte for 1, 3, 4, and 8 tokens. No model weights needed.
PYTHONPATH=. LLAMA_PREFILL_DEVICE=1 .venv/bin/python \
  -m unittest discover -s tests -p test_llama3_prefill.py -v

# Full model: compare prompt logits and four subsequent decode tokens.
PYTHONPATH=. .venv/bin/python scripts/validate_prefill.py \
  --device 1 --output validation/prefill-card1.json
```

[Card-1 results](validation/prefill-card1.json), September 9, 2026, chunk size 4:
all eight tested prompt lengths (1, 4, 5, 31, 32, 33, 65, then 3) produce
**byte-identical logits** and identical four-token continuations relative to
sequential decode ingestion. These cases exercise partial chunks, both sides of
32-token cache blocks, and shorter-prompt reuse after a longer prompt. CPU
lowering checks cover seven- and eight-bank topologies; full-model hardware
validation is on card 1.

The [CLI smoke test](validation/prefill-cli-card1.txt) also ran an eight-token
chunk configuration on a 23-token chat prompt, answered “The capital of France
is Paris.”, and continued at **29.75 decode tok/s**.

| Prompt tokens | Sequential ingestion | Prefill |
| --- | ---: | ---: |
| 32 | 1.075 s | 1.406 s |
| 33 | 1.109 s | 1.396 s |
| 65 | 2.189 s | 2.812 s |

These warm measurements exclude model startup. Prefill timing includes prompt
upload; sequential timing starts after upload. The first prefill also builds
and caches its variants (about 0.61 s total for the one-token case in this run).
The validation JSON separates execution time from preparation. The CLI reports
prompt time separately from subsequent decode throughput; a one-token generation
has no subsequent decode sample.

Prefill is currently slower than the highly tuned sequential path despite
reusing QKV/MLP weight rows. Next performance work should target tiled GEMM,
attention across multiple query rows, and launch/dispatch overhead. The saved
numbers are validation measurements, not a claim of improved prefill throughput.
