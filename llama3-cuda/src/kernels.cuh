#pragma once

#include <cuda_bf16.h>

// All weights, KV cache, and small intermediate vectors are bf16; activations
// and reductions are fp32. Short alias because __nv_bfloat16 ruins signatures.
using bf16 = __nv_bfloat16;

// Launch API for one decode step (one input token → one greedy output token),
// listed in execution order. Steps with the same number reuse a kernel.
// Implementations are split by op class:
//
//   kernels_token.cu      embed, rmsnorm stats, argmax     (copies & reductions)
//   kernels_gemv.cu       all matrix-vector products       (gemv)
//   kernels_attention.cu  rope + kv cache, attention       (position-dependent)
//   kernels_common.cuh    bf16 ld/st, block reductions, precision policy
//
//   step 0   launch_embed            x = embeddings[token]
//   per layer:
//   step 1   launch_rmsnorm_inv      inv_rms = 1/sqrt(mean(x²)+eps)
//   step 2   launch_qkv_gemv_norm    q,k,v = W{q,k,v} @ norm(x)
//   step 3   launch_rope_cache       rotate q,k; append k,v to cache
//   step 4   launch_attention        softmax(q·Kᵀ)·V per head
//   step 5   launch_proj_residual    x += Wo @ attn
//   step 6   = step 1 for the MLP
//   step 7   launch_gate_up_swiglu   tmp = silu(Wg@nx) * (Wu@nx)
//   step 8   = step 5 with Wdown
//   after the last layer:
//   step 9   = step 1 (final norm)
//   step 10  launch_logits_norm      logits = embeddings @ norm(x)
//   step 11  launch_argmax           next = argmax(logits)

void launch_embed(const bf16* embeddings, int token, float* x, int dim);
void launch_rmsnorm_inv(const float* x, float* inv_out, int dim, float eps);
void launch_qkv_gemv_norm(
    const bf16* wq, const bf16* wk, const bf16* wv,
    const float* x, const bf16* norm_w, const float* inv_rms,
    bf16* q, bf16* k, bf16* v, int dim, int kv_dim);
void launch_rope_cache(
    bf16* q, const bf16* k_raw, const bf16* v_raw,
    bf16* k_cache, bf16* v_cache,
    const float* cos_table, const float* sin_table,
    int pos, int max_seq, int n_heads, int n_kv_heads, int head_dim);
void launch_attention(
    const bf16* q, const bf16* k_cache, const bf16* v_cache, float* scores,
    bf16* out, int pos, int max_seq, int n_heads, int n_kv_heads, int head_dim);
void launch_proj_residual(
    const bf16* w, const bf16* in, const float* residual, float* out,
    int out_dim, int in_dim);
void launch_gate_up_swiglu(
    const bf16* wgate, const bf16* wup, const float* x, const bf16* norm_w,
    const float* inv_rms, bf16* tmp, int hidden_dim, int dim);
void launch_logits_norm(
    const bf16* embeddings, const float* x, const bf16* norm_w,
    const float* inv_rms, float* logits, int vocab_size, int dim);
void launch_argmax(
    const float* logits, float* block_vals, int* block_ids, int* out_token,
    int vocab_size, int arg_blocks);
