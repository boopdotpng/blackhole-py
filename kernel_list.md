# Llama 3.2 1B Kernel List

This is a bringup list for the tinygrad model in `/home/boop/ml/llama3-tinygrad/main.py`.
It assumes Llama-family decoder shapes with a hardcoded Llama 3.2 1B configuration
for the first target. The goal is not a maintainable compiler path; the goal is to
generate or steal enough kernel structure from TT-Lang / TTNN / TT-Metal to avoid
hand-writing every instruction blind.

## Fixed Model Shape

- Batch: `B = 1`
- Hidden size: `2048`
- Layers: `16`
- Attention heads: `32`
- KV heads: `8`
- GQA repeat: `4`
- Head dim: `64`
- MLP hidden: `8192`
- Vocab: `128256`
- Max sequence/cache length: `8192`
- Weights/cache dtype: bf16
- Matmuls: default target is bf16 inputs/weights and bf16 outputs with f32/f32acc
  accumulation. `examples/matmul_peak.py` is the expected template for this path,
  but it is not there yet: `python examples/matmul_peak.py 5000 5000 5000`
  currently runs the bf16/non-f32-DST default path (`FP32_DEST_ACC=False`,
  `INTERMEDIATE_DTYPE=Float16_b`). Enabling `fp32_dest_acc=True` does not plan
  for 5000^3 today (`No valid matmul plan for Mt=157 Kt=157 Nt=157`). Fix the
  fp32 DST accumulator planner/kernel path before treating this as the Llama
  matmul baseline.

## On-Device Rule

All model work should happen on device:

- No host-generated RoPE tables in the intended path.
- No host-side mask construction.
- No CPU argmax for the intended path.
- No host-side GQA duplication.
- No host-side layout conversion during generation.

The host may load raw weight/tokenizer files, allocate buffers, enqueue launches, and
read the final token id. Debug readbacks are fine for tests, but they are not part of
the model path.

This list is "generic enough" to support variable prompt length `S`, decode position
`start_pos`, and available attention length `T = start_pos + S`, while still assuming
the fixed 1B hidden/head dimensions above.

## Required F32 Paths

Use f32 or f32 destination accumulation here. These are not polish items; they are
expected to matter for correctness/stability.

- **RMSNorm reduction:** square, sum/mean, eps add, and rsqrt scale should be f32.
  The final normalized output can be packed back to bf16.
- **Attention score matmul:** `Q @ K.T` must use f32 accumulation. Apply the
  `1 / sqrt(64) = 0.125` scale in f32.
- **Score/mask buffer:** if softmax is split from score matmul, store scores and
  mask bias as f32. The mask kernel should write f32 `-inf` for invalid positions.
- **Softmax:** row max, subtract, exp input, row sum, reciprocal, and probability
  normalization should be f32. The final probabilities may be packed to bf16 for
  the value matmul.
- **Attention value matmul:** prefer f32 accumulation for `softmax @ V`; if this is
  too expensive, it is a controlled approximation to revisit after the f32 path works.
- **Output projection after attention:** use f32 accumulation for `attn_out @ o_proj`,
  then add the residual before packing if the epilogue supports it.
- **Final logits / argmax:** use f32 accumulation for `hidden @ embedding.T`.
  Argmax compares f32 logits or f32 shard maxima.

Do not intentionally build bf16-acc matmuls for Llama. If a bringup kernel temporarily
falls back to bf16 accumulation, treat that as a known gap, not the target behavior.

Likely acceptable without extra f32 scalar work beyond f32acc:

- Q/K/V projection matmuls: bf16 input/weight/output, f32acc.
- MLP gate/up/down projection matmuls: bf16 input/weight/output, f32acc.
- Residual adds and elementwise multiplies after f32-sensitive reductions.

If output quality is poor after the required f32 paths work, promote the remaining
projection/MLP matmuls to f32acc one at a time.

## Existing Starting Points

- Embedding gather: `examples/llama3/embedding.py`
- Matmul/projections: `examples/matmul_peak.py`
- MLP composition and SiLU: `examples/llama3/mlp.py`
- Staged RMSNorm: `examples/llama3/rmsnorm.py`
- RoPE table/upload experiments: `examples/llama3/rope.py`
- Generic small eltwise template: `examples/add1.py`

## Launch Skeleton

For prefill:

1. Embed prompt token ids into activation buffer.
2. For each of 16 layers:
   - RMSNorm input.
   - QKV projections.
   - Apply RoPE to Q and K.
   - Store K/V into layer KV cache.
   - Attention score matmul.
   - Apply causal mask and softmax.
   - Attention value matmul.
   - Output projection and residual add.
   - RMSNorm post-attention.
   - MLP.
   - Residual add.
3. Final RMSNorm.
4. Tied embedding logits matmul for last token only.
5. Argmax.

For decode:

1. Embed one token.
2. Same layer loop, but `S = 1`.
3. Run the same mask interface in decode/pass-through mode or skip by launch flag.
4. Softmax length is `T = start_pos + 1`.
5. Final RMSNorm, last-token logits, on-device argmax.

## Required Kernels

### 1. Weight Load / Layout Preparation

Host-side file loading is fine. Tensor layout preparation should be on device or
done once before generation by explicit preprocessing kernels.

- Load safetensors weights into DRAM.
- Convert/transpack weights into the exact tiled layouts expected by matmul kernels.
- Prepare per-layer pointers/offset tables for:
  - `q_proj`, `k_proj`, `v_proj`, `o_proj`
  - `gate_proj`, `up_proj`, `down_proj`
  - `input_layernorm.weight`
  - `post_attention_layernorm.weight`
  - final `norm.weight`
  - tied `embed_tokens.weight`

Do not make this fully general. Hardcode hidden/head dimensions, but keep layer id,
source pointer, destination pointer, and tile counts as runtime args where that makes
the same kernel reusable.

### 2. Token Embedding Gather

Status: basically implemented. `examples/llama3/embedding.py` is close to what
the production kernel should look like: BRISC-only NOC gather from token ids in DRAM,
source embedding rows in tilized DRAM, and tiled activation output split across cores.

Input:

- Token ids `(S)` or one decode token.
- Embedding weight `(128256, 2048)`.

Output:

- Activation `(S, 2048)` tiled bf16.

Likely implementation:

- BRISC/NOC gather from DRAM offsets based on token id.
- For prefill, gather `S` rows.
- For decode, gather one row.

Reference:

- `examples/llama3/embedding.py`

Remaining integration work:

- Raise or tile around its current `MAX_SEQ_LEN = 1024` limit for the full `8192`
  cache/RoPE target.
- Wire it to the real `embed_tokens.weight` allocation and generation token buffer.
- Keep the core column partitioning model; it is already the right shape for this
  bringup.

### 3. RoPE Table Generation

Output:

- `cos[8192, 64]`
- `sin[8192, 64]`

Implementation:

- Generate on device once at startup.
- Use the constants from tinygrad:
  - `theta = 500000.0`
  - `factor = 32.0`
  - `low_freq_factor = 1.0`
  - `high_freq_factor = 4.0`
  - `original_max_position_embeddings = 8192`
- Output bf16 tables are probably enough for first bringup, but keep f32 temporaries
  if the SFPU path makes that easy.

This can be a slow one-time kernel. Correctness matters more than speed here.

### 4. RMSNorm F32

Input:

- Activation `(S, 2048)` bf16.
- Weight `(2048)` bf16.

Output:

- Normalized activation `(S, 2048)` bf16.

Math:

```text
xf = x.float()
scale = rsqrt(mean(xf * xf, axis=-1) + 1e-5)
out = bf16(xf * scale) * weight
```

Bringup version:

- Keep the existing staged implementation:
  1. square
  2. reduce/mean
  3. eps + rsqrt
  4. broadcast multiply
  5. weight multiply

Fusion target:

- One multi-stage kernel per row block if realistic.
- Keep f32 accumulation for the reduction.
- Required f32: square/reduce/mean/eps/rsqrt. Pack normalized output to bf16.

References:

- `examples/llama3/rmsnorm.py`
- TT-Lang `test_layernorm.py` for multi-pass normalization structure.

### 5. QKV Projection

Input:

- RMSNorm output `(S, 2048)`.
- `q_proj.weight (2048, 2048)`
- `k_proj.weight (512, 2048)`
- `v_proj.weight (512, 2048)`

Output:

- Q `(32, S, 64)` or equivalent tiled layout.
- K `(8, S, 64)`.
- V `(8, S, 64)`.

Bringup version:

- Three separate matmul launches.
- Required accumulation: bf16 input/weight/output with f32acc.

Fusion target:

- Fuse Q/K/V projections if the matmul planner can share activation reads.
- It is acceptable to hardcode the three output address regions.

References:

- `examples/matmul_peak.py`
- TT-Lang `examples/test_transformer_block.py::norm_qkv_kernel`

### 6. Apply RoPE to Q and K

Input:

- Q `(32, S, 64)`
- K `(8, S, 64)`
- `cos[start_pos:start_pos+S, 64]`
- `sin[start_pos:start_pos+S, 64]`

Output:

- Rotated Q and K.

Math from tinygrad:

```text
x1 = x[..., :32]
x2 = x[..., 32:]
rotated = concat(-x2, x1)
out = x * cos + rotated * sin
```

Important: this model uses first-half/second-half rotation, not adjacent even/odd
rotation.

Bringup version:

- Separate Q RoPE and K RoPE kernels.

Fusion target:

- Fuse Q/K RoPE with KV cache store for K.
- Potentially fuse Q RoPE into score matmul reader if that keeps layout simpler.

References:

- TTNN/TT-Metal `rotary_embedding_llama` cache/artifacts.
- TT-Lang transformer example only has a simplified multiply-by-cos placeholder;
  do not copy it literally.

### 7. KV Cache Store

Input:

- Rotated K `(8, S, 64)`.
- V `(8, S, 64)`.
- `start_pos`.

Output:

- Layer-local cache:
  - K cache `(8, 8192, 64)` bf16.
  - V cache `(8, 8192, 64)` bf16.

Bringup version:

- Dedicated data-movement kernel after RoPE.

Fusion target:

- Fuse with K RoPE and raw V projection writeout.

No GQA duplication should be stored. Duplicate logically in readers by mapping
query head `h` to KV head `h // 4`.

### 8. Attention Score Matmul

Input:

- Q `(32, S, 64)`.
- K cache `(8, T, 64)`, where `T = start_pos + S`.

Output:

- Scores `(32, S, T)` f32 storage with f32 accumulation.

Math:

```text
scores[h, q, k] = dot(q[h, q, :], k[h // 4, k, :]) * 0.125
```

Bringup version:

- One hardcoded batched/headed matmul path.
- Do not materialize repeated K heads.
- Decode path has `S = 1`, which is a simpler matvec per head.
- Required f32: dot-product accumulator and scale multiply.

Fusion target:

- Fuse scale multiply into score output.
- For prefill, optionally fold causal mask into score write.

References:

- TTNN/TT-Metal `sdpa` and `sdpa_flash_decode`.
- TT-Lang attention example for high-level dataflow.

### 9. Attention Mask / Score Bias

This should be a real reusable device kernel, not a host-created tensor. It handles
causal prefill, chunked prefill, decode/pass-through, and optional padding/window
rules later.

Input:

- Scores `(32, S, T)`.
- `start_pos`.
- `S`.
- `T`.
- Optional `valid_q_len` / `valid_k_len` for padded prompt tiles.
- Optional `window_left` for sliding-window variants later.
- Mode:
  - `CAUSAL`
  - `DECODE_PASSTHROUGH`
  - `PADDING`
  - `CAUSAL_AND_PADDING`

Output:

- Masked scores, or a compact mask/bias tile buffer consumed by softmax.

Rule:

```text
absolute_q = start_pos + q_index
causal_invalid = k_index > absolute_q
padding_invalid = q_index >= valid_q_len or k_index >= valid_k_len
window_invalid = window_left >= 0 and k_index < absolute_q - window_left

if causal_invalid or padding_invalid or window_invalid:
  score = -inf
```

Bringup version:

- Separate mask kernel that writes `-inf` into invalid score positions.
- Works over tiled score pages.
- Accepts runtime `S`, `T`, `start_pos`, and mode.
- For decode, mode can be `DECODE_PASSTHROUGH` and simply copy scores or return
  without touching them.
- For prefill, mode is `CAUSAL` with `valid_q_len = S`, `valid_k_len = T`.
- Required f32: write f32 `-inf` when operating on the score buffer.

Fusion target:

- Fold into softmax or score matmul.
- Best long-term path: softmax consumes mask predicates during max/sum and writes
  zero probability for invalid lanes.

Mask storage choices:

- **Score-bias in place:** simplest. Mutate score tiles to contain `-inf`.
- **Compact predicate mask:** better for fusion. One bit/byte per score element or
  tile-local predicate generated on the fly.
- **Bias tile buffer:** useful if generated once per `(S, T, start_pos)` and reused
  by every head/layer in prefill.

Start with score-bias in place, then move the predicate into softmax once the mask
kernel is trusted.

### 10. F32 Softmax

Input:

- Scores `(32, S, T)`.
- Optional mask/bias input from the attention mask kernel.

Output:

- Attention probabilities `(32, S, T)` bf16.

Math per `(head, query)` row:

```text
m = max(scores)
e = exp(scores - m)
sum_e = sum(e)
prob = e / sum_e
```

Bringup version:

- Multi-pass row softmax:
  1. reduce max
  2. apply mask/bias, subtract max, and exp
  3. reduce sum
  4. reciprocal and multiply
- Required f32: max/sub/exp/sum/recip/mul. Pack output probabilities to bf16 only
  after normalization.

Fusion target:

- Fuse mask predicates with max/exp passes.
- Decode can use a separate `S = 1` streaming softmax over `T`.

References:

- TT-Lang `test/python/softmax_compiler_allocated_dfb.py`
- TTNN/TT-Metal `sdpa` and `sdpa_flash_decode`
- `ttk/sfpu.py` for exp/recip primitives.

This is the highest-risk new kernel.

### 11. Attention Value Matmul

Input:

- Attention probabilities `(32, S, T)`.
- V cache `(8, T, 64)`.

Output:

- Attention output `(S, 2048)`.

Math:

```text
out[h, q, d] = sum_k prob[h, q, k] * v[h // 4, k, d]
```

Bringup version:

- Separate matmul after softmax.
- Logical GQA only in the V reader.
- Required f32: use f32 accumulation for the probability-weighted sum at least until
  we have a measured reason to relax it.

Fusion target:

- Eventually fuse softmax and value matmul for decode, but not necessary first.

### 12. Output Projection + Residual Add

Input:

- Attention output `(S, 2048)`.
- Residual activation `(S, 2048)`.
- `o_proj.weight (2048, 2048)`.

Output:

- Post-attention activation `(S, 2048)`.

Bringup version:

- Matmul.
- Separate residual add.
- Required f32: matmul accumulation. Prefer residual add in f32 before final pack.

Fusion target:

- Fuse residual add into matmul epilogue.

Reference:

- TT-Lang `proj_residual_kernel`.

### 13. MLP Gate and Up Projections

Input:

- Post-attention RMSNorm output `(S, 2048)`.
- `gate_proj.weight (8192, 2048)`.
- `up_proj.weight (8192, 2048)`.

Output:

- Gate `(S, 8192)`.
- Up `(S, 8192)`.

Bringup version:

- Two separate matmuls.
- Required accumulation: bf16 input/weight/output with f32acc.

Fusion target:

- Fuse gate/up projection reads if easy.

### 14. SwiGLU / SiLU Multiply

Input:

- Gate `(S, 8192)`.
- Up `(S, 8192)`.

Output:

- Hidden `(S, 8192)`.

Math:

```text
hidden = silu(gate) * up
silu(x) = x * sigmoid(x)
```

Bringup version:

- One eltwise SFPU kernel.

Fusion target:

- Fuse with down projection reader only if the hidden materialization becomes a
  bandwidth bottleneck.

References:

- `examples/llama3/mlp.py`
- `ttk/sfpu.py`

### 15. Down Projection + Residual Add

Input:

- Hidden `(S, 8192)`.
- Residual post-attention activation `(S, 2048)`.
- `down_proj.weight (2048, 8192)`.

Output:

- Layer output `(S, 2048)`.

Bringup version:

- Matmul.
- Separate residual add.
- Required accumulation: bf16 input/weight/output with f32acc.

Fusion target:

- Fuse residual add into matmul epilogue.

### 16. Final RMSNorm

Same kernel as layer RMSNorm, using `model.norm.weight`.

Input:

- Final layer activation `(S, 2048)`.

Output:

- Final normalized activation `(S, 2048)`.

Only the last token is needed for logits, so decode and prefill can eventually normalize
only the last row if earlier rows are not needed after prefill.

### 17. Logits Matmul

Input:

- Last token hidden `(1, 2048)`.
- Tied embedding weight transposed logically: `(2048, 128256)`.

Output:

- Logits `(128256)`.

Bringup version:

- Matmul/vector-matrix path producing full vocab logits.
- Required f32: matmul accumulation and logit comparison path.

Fusion target:

- Fuse partial argmax across vocab tiles and reduce only max value/index. This avoids
  storing the full logits vector.

### 18. Argmax

Input:

- Logits `(128256)`.

Output:

- Next token id.

Bringup version:

- On-device argmax over full logits or over fused logits shards.
- Host may read the final token id only.
- Required f32: compare f32 logits or f32 local maxima.

Implementation:

- Per-core local max over vocab shard.
- Global reduction of `(value, index)` pairs.
- Return one token id.

## Likely Fusion Boundaries

Reasonable early fusions:

- QKV projection as one launch, if activation reread is expensive.
- K RoPE + KV cache store.
- Score scale + attention mask + softmax.
- Output projection + residual add.
- Down projection + residual add.

Reasonable later fusions:

- RMSNorm + QKV projection. This is attractive but only after standalone f32 RMSNorm
  is trusted.
- RMSNorm + MLP gate/up projection.
- Decode softmax + attention value matmul.
- Logits + argmax.

Avoid early:

- Full attention as one huge fused kernel for prefill.
- Full transformer block fusion.
- Fully general dynamic model shapes.
- General GQA duplication.
- Host-side masks.

## TT-Lang / TTNN Mining Targets

Generate or inspect these first:

1. F32-ish RMSNorm/layernorm reduction and broadcast.
2. Standalone attention mask / where / select / fill-with-`-inf` kernels.
3. Softmax with compiler-allocated intermediate DFBs.
4. Matmul with fused eltwise epilogue.
5. Rotary embedding llama kernel from TTNN/TT-Metal cache.
6. SDPA prefill and SDPA decode kernels from TTNN/TT-Metal cache.
7. Binary/ternary eltwise SFPU kernels for SiLU, multiply, add, where/select.

Useful commands:

```sh
cd /home/boop/tenstorrent/tt-lang
source build-gcc/env/activate
TTLANG_COMPILE_ONLY=1 \
TTLANG_INITIAL_MLIR=/tmp/ttlang_initial.mlir \
TTLANG_FINAL_MLIR=/tmp/ttlang_final.mlir \
python test/python/softmax_compiler_allocated_dfb.py
```

Generated TT-Lang kernel C++ is written under `/tmp/boop/ttlang_kernel_*.cpp`.

For TT-Metal cached ELFs, inspect existing cache entries such as `sdpa`,
`sdpa_flash_decode`, `rotary_embedding_llama`, `layernorm`, and `bmm_large_block_zm`,
then disassemble with the bundled `riscv-tt-elf-objdump`.

## Suggested Bringup Order

1. Embedding for one token and short prompt.
2. Reuse matmul for one projection and validate with a debug readback test.
3. Q/K/V projections with correct layouts.
4. RoPE apply for Q/K, including first-half/second-half rotation.
5. KV cache store and readback.
6. Standalone attention mask kernel over a fake score buffer.
7. Decode attention (`S = 1`, mask pass-through mode).
8. F32 softmax for decode.
9. Attention value matmul.
10. Output projection + residual.
11. RMSNorm correctness with f32 accumulation.
12. MLP path.
13. One full decode layer.
14. All 16 decode layers.
15. Final norm + logits + on-device argmax.
16. Prefill attention with real causal masking.

This order gets a one-token decode path working while still building the real mask
kernel early enough that prefill does not become a separate science project.
