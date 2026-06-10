// Attention-family kernels: position-dependent work on Q/K/V and the KV cache.
//
//   rope_cache    rotate q,k by position; append k,v to the per-layer cache
//   attention     per-head softmax(q·Kᵀ/√d)·V over cached positions 0..pos
//
// KV cache layout is [kv_head][seq_pos][head_dim], so one head's history is
// contiguous for the attention kernel's time loop.

#include "kernels_common.cuh"

// RoPE rotate q and k, then append k,v at `pos` in the KV cache.
//
// RoPE pairs element i with i+head_dim/2 inside each head and rotates by a
// per-(pos, i) angle from precomputed fp32 cos/sin tables:
//   out[i]      = x[i]*cos − x[i+half]*sin
//   out[i+half] = x[i+half]*cos + x[i]*sin
//
// One flat thread index covers three jobs back to back:
//   [0, q_pairs)                  rotate q in place
//   [q_pairs, q_pairs+k_pairs)    rotate k and write to k_cache[pos]
//   [.., +v_vals)                 copy v to v_cache[pos] (no rotation)
__global__ void rope_cache_kernel(
    bf16* q, const bf16* k_raw, const bf16* v_raw,
    bf16* k_cache, bf16* v_cache,
    const float* cos_table, const float* sin_table,
    int pos, int max_seq, int n_heads, int n_kv_heads, int head_dim) {
    const int half_dim = head_dim / 2;
    const int q_pairs = n_heads * half_dim;
    const int k_pairs = n_kv_heads * half_dim;
    const int v_vals = n_kv_heads * head_dim;
    const int idx = blockIdx.x * blockDim.x + threadIdx.x;
    const float* cos_row = cos_table + static_cast<size_t>(pos) * half_dim;
    const float* sin_row = sin_table + static_cast<size_t>(pos) * half_dim;

    if (idx < q_pairs) {
        const int h = idx / half_dim;
        const int i = idx % half_dim;
        bf16* base = q + h * head_dim;
        const float x1 = ld(base, i);
        const float x2 = ld(base, i + half_dim);
        st(base, i, x1 * cos_row[i] - x2 * sin_row[i]);
        st(base, i + half_dim, x2 * cos_row[i] + x1 * sin_row[i]);
    } else if (idx < q_pairs + k_pairs) {
        const int j = idx - q_pairs;
        const int h = j / half_dim;
        const int i = j % half_dim;
        const bf16* src = k_raw + h * head_dim;
        bf16* dst = k_cache + (static_cast<size_t>(h) * max_seq + pos) * head_dim;
        const float x1 = ld(src, i);
        const float x2 = ld(src, i + half_dim);
        st(dst, i, x1 * cos_row[i] - x2 * sin_row[i]);
        st(dst, i + half_dim, x2 * cos_row[i] + x1 * sin_row[i]);
    } else if (idx < q_pairs + k_pairs + v_vals) {
        const int j = idx - q_pairs - k_pairs;
        const int h = j / head_dim;
        const int d = j % head_dim;
        v_cache[(static_cast<size_t>(h) * max_seq + pos) * head_dim + d] =
            v_raw[h * head_dim + d];
    }
}

// Single-token causal attention, one block per query head.
//
//   scores[t] = (q · K[t]) / sqrt(head_dim)      for t in [0, pos]
//   p         = softmax(scores)                  (max-subtracted, fp32)
//   out       = Σ_t p[t] · V[t]
//
// Causality is free: only positions 0..pos exist in the cache yet.
// GQA is an index map, nothing more: with 32 Q heads over 8 KV heads,
// query head qh reads KV head qh/4.
// Scores spill to global because pos can exceed shared memory.
__global__ void attention_kernel(
    const bf16* q, const bf16* k_cache, const bf16* v_cache, float* scores,
    bf16* out, int pos, int max_seq, int n_heads, int n_kv_heads, int head_dim) {
    const int qh = blockIdx.x;
    if (qh >= n_heads) return;
    const int kvh = qh / (n_heads / n_kv_heads);  // GQA: 4 query heads share a KV head
    const bf16* q_base = q + qh * head_dim;
    const bf16* k_base = k_cache + static_cast<size_t>(kvh) * max_seq * head_dim;
    const bf16* v_base = v_cache + static_cast<size_t>(kvh) * max_seq * head_dim;
    float* score_base = scores + static_cast<size_t>(qh) * max_seq;
    const float scale = rsqrtf(static_cast<float>(head_dim));

    // scores + running max (threads stride over time steps)
    float local_max = NEG_INF;
    for (int t = threadIdx.x; t <= pos; t += blockDim.x) {
        const bf16* kt = k_base + static_cast<size_t>(t) * head_dim;
        float dot = 0.0f;
        for (int d = 0; d < head_dim; ++d) dot += ld(q_base, d) * ld(kt, d);
        const float s = dot * scale;
        score_base[t] = s;
        local_max = fmaxf(local_max, s);
    }
    const float maxv = block_max(local_max);

    // exponentiate in place + sum
    float local_sum = 0.0f;
    for (int t = threadIdx.x; t <= pos; t += blockDim.x) {
        const float e = expf(score_base[t] - maxv);
        score_base[t] = e;
        local_sum += e;
    }
    const float denom = block_sum(local_sum);

    // weighted sum of V (threads stride over head_dim, full pass over time)
    for (int d = threadIdx.x; d < head_dim; d += blockDim.x) {
        float acc = 0.0f;
        for (int t = 0; t <= pos; ++t) {
            acc += (score_base[t] / denom) * ld(v_base, static_cast<size_t>(t) * head_dim + d);
        }
        st(out, qh * head_dim + d, acc);
    }
}

// --- launch wrappers ---

void launch_rope_cache(
    bf16* q, const bf16* k_raw, const bf16* v_raw,
    bf16* k_cache, bf16* v_cache,
    const float* cos_table, const float* sin_table,
    int pos, int max_seq, int n_heads, int n_kv_heads, int head_dim) {
    const int items = n_heads * (head_dim / 2) +     // q pairs
                      n_kv_heads * (head_dim / 2) +  // k pairs
                      n_kv_heads * head_dim;         // v copies
    rope_cache_kernel<<<(items + BLOCK - 1) / BLOCK, BLOCK>>>(
        q, k_raw, v_raw, k_cache, v_cache, cos_table, sin_table,
        pos, max_seq, n_heads, n_kv_heads, head_dim);
}

void launch_attention(
    const bf16* q, const bf16* k_cache, const bf16* v_cache, float* scores,
    bf16* out, int pos, int max_seq, int n_heads, int n_kv_heads, int head_dim) {
    attention_kernel<<<n_heads, BLOCK>>>(
        q, k_cache, v_cache, scores, out, pos, max_seq, n_heads, n_kv_heads, head_dim);
}
