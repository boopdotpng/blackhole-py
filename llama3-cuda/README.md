# llama3-cuda

Correctness-first CUDA decode path for Llama 3.2 1B-style models.

This stores model weights as bf16 on the GPU (the checkpoint's native dtype),
accumulates everything in fp32, and keeps the kernel set intentionally small:

- embedding lookup
- RMSNorm inverse-RMS reduction
- normalized Q/K/V GEMV
- RoPE + KV cache write
- fused GQA attention
- projection + residual GEMV
- normalized gate/up GEMV + SwiGLU
- normalized logits GEMV + greedy argmax

It is deliberately slow for batch-1 decode. The point is to make the required
LLM ops and dataflow easy to read before porting the same ideas elsewhere.

## How The Inference Loop Works

This project is written for someone who already understands CUDA kernels,
global memory, reductions, and GEMV, but has not implemented an LLM before.

Llama 3.2 1B is a decoder-only transformer. "Decoder-only" means inference is
a loop where the model reads all tokens seen so far, predicts one next token,
then feeds that predicted token back into the same model. In this repo, prefill
and decode are intentionally the same path: every prompt token is processed one
at a time and appended to the KV cache.

The main activation is `x`, a 2048-wide vector for batch size 1. Each token
goes through:

```text
x = embedding[token]

for each layer:
  x = x + attention(rmsnorm(x))
  x = x + mlp(rmsnorm(x))

logits = embedding @ rmsnorm(x)
next_token = argmax(logits)
```

The attention block expands `x` into query, key, and value vectors:

```text
q = Wq @ rmsnorm(x)       // 32 heads * 64 = 2048 values
k = Wk @ rmsnorm(x)       //  8 heads * 64 =  512 values
v = Wv @ rmsnorm(x)       //  8 heads * 64 =  512 values
```

RoPE rotates pairs of Q/K values based on token position. K and V are then
stored in the KV cache. The cache is the reason decode does not recompute old
tokens from scratch: for the current query, attention only needs old K/V
vectors, not all old layer activations.

GQA means there are fewer K/V heads than Q heads. Llama 3.2 1B has 32 query
heads and 8 key/value heads, so query head `qh` reads KV head `qh / 4`.

The MLP block is two input projections and one output projection:

```text
tmp = silu(Wgate @ rmsnorm(x)) * (Wup @ rmsnorm(x))
x = x + Wdown @ tmp
```

For a CUDA reader, the important observation is that most of this model is
memory-streaming GEMV. Batch-1 decode repeatedly reads large bf16 weight
matrices, accumulates in fp32, and writes small activation vectors. The kernels
here are intentionally simple row-parallel GEMVs: one block computes one output
row.

Precision contract (the same one a Tenstorrent port should keep): bf16 is a
storage format only — weights, KV cache, and small intermediate vectors. Every
accumulation (dots, softmax, residual stream, RMS stats, logits) is fp32.

The code is split by responsibility:

- [src/main.cu](src/main.cu): CLI, model upload, buffer allocation, and the
  readable layer-by-layer decode loop.
- [src/kernels.cuh](src/kernels.cuh): the launch API plus a step-by-step map of
  one decode step.
- [src/kernels_common.cuh](src/kernels_common.cuh): precision policy, bf16
  load/store helpers, and the shared block reductions.
- [src/kernels_gemv.cu](src/kernels_gemv.cu): every matrix-vector product
  (QKV, output/down projections, gate/up + SwiGLU, logits).
- [src/kernels_attention.cu](src/kernels_attention.cu): RoPE + KV-cache append
  and the per-head causal attention.
- [src/kernels_token.cu](src/kernels_token.cu): embedding lookup, RMSNorm
  statistic, and the two-stage argmax.
- [src/model_format.cpp](src/model_format.cpp): `.l3cu` header parsing, tensor
  size checks, pointer layout, token-id parsing, and RoPE table generation.
- [src/model_format.h](src/model_format.h): the model header and layer pointer
  structs.

## Build

```bash
make
```

## Convert/download weights

The converter uses Hugging Face `transformers` and downloads through the normal
HF cache. Meta Llama weights usually require accepting the license and having
`HF_TOKEN` set.

```bash
python3 -m pip install torch transformers safetensors huggingface_hub numpy

python3 scripts/download_convert.py \
  --model-id meta-llama/Llama-3.2-1B-Instruct \
  --out models/llama3.2-1b-instruct-bf16.l3cu \
  --tokenizer-out models/llama3.2-1b-instruct-tokenizer
```

Llama 3 checkpoints ship in bf16, so this is a re-layout, not a dtype
conversion: the `.l3cu` payload holds the exact checkpoint bits. fp32 sources
get rounded to bf16.
If you do not have access to the gated Meta repo, a public mirror with the same
Llama 3.2 1B architecture can be converted the same way:

```bash
python3 scripts/download_convert.py \
  --model-id unsloth/Llama-3.2-1B-Instruct \
  --out models/llama3.2-1b-instruct-bf16.l3cu \
  --tokenizer-out models/llama3.2-1b-instruct-tokenizer
```

## Run with token ids

```bash
./build/llama3_cuda \
  --model models/llama3.2-1b-instruct-bf16.l3cu \
  --tokens 128000,9906,11 \
  --steps 16 \
  --max-seq 2048 \
  --timings
```

The binary prints the full prompt plus generated token ids as `TOKENS: ...`.

## Run with a prompt

This wrapper tokenizes/decodes in Python and runs the CUDA binary for the model
math.

```bash
python3 scripts/run_prompt.py \
  --bin ./build/llama3_cuda \
  --weights models/llama3.2-1b-instruct-bf16.l3cu \
  --tokenizer models/llama3.2-1b-instruct-tokenizer \
  --prompt "what is the meaning of life" --chat \
  --steps 16
```

## Compare against Transformers

```bash
python3 scripts/compare_transformers.py \
  --model-id unsloth/Llama-3.2-1B-Instruct \
  --bin ./build/llama3_cuda \
  --weights models/llama3.2-1b-instruct-bf16.l3cu \
  --tokenizer models/llama3.2-1b-instruct-tokenizer \
  --prompt "Why is the sky blue?" \
  --steps 4
```

This runs greedy decode in both implementations and fails on the first token id
mismatch.

## Benchmark

```bash
python3 scripts/benchmark.py \
  --model-id unsloth/Llama-3.2-1B-Instruct \
  --bin ./build/llama3_cuda \
  --weights models/llama3.2-1b-instruct-bf16.l3cu \
  --tokenizer models/llama3.2-1b-instruct-tokenizer \
  --prompt "Why is the sky blue?" \
  --steps 16
```

The script reports whether PyTorch sees CUDA. On this machine, the installed
PyTorch build is CPU-only, so the Transformers timing is a CPU baseline rather
than an optimized CUDA baseline.

## Notes

- Only greedy decoding is implemented.
- Batch size is fixed at 1.
- Prefill is intentionally implemented by repeatedly running the decode path.
- RoPE implements the Llama 3 frequency scaling parameters from the HF config.
- The KV cache is allocated for `--max-seq`; keep it modest while debugging.
