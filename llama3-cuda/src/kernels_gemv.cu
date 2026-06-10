// GEMV-family kernels: every matrix-vector product in the model.
//
// All four share the same shape: one block owns one output row, BLOCK threads
// stride the input vector, partial products tree-reduce in shared memory.
// Three of them fold RMSNorm into the weight read (nx = x * norm_w * inv_rms),
// so the normalized vector is never materialized.
//
//   qkv_gemv_norm     q,k,v  = W{q,k,v} @ rmsnorm(x)
//   proj_residual     out    = residual + W @ in       (Wo and Wdown)
//   gate_up_swiglu    tmp    = silu(Wg @ nx) * (Wu @ nx)
//   logits_norm       logits = embeddings @ rmsnorm(x) (tied output head)

#include "kernels_common.cuh"

// q,k,v = Wq @ nx, Wk @ nx, Wv @ nx
//
// Wq, Wk, Wv are concatenated into one launch so QKV is one grid of
// dim + 2*kv_dim blocks; block index picks which matrix and row it owns.
// Llama 3.2 1B: 2048 + 512 + 512 rows, each a 2048-long dot product.
__global__ void qkv_gemv_norm_kernel(
    const bf16* wq, const bf16* wk, const bf16* wv,
    const float* x, const bf16* norm_w, const float* inv_rms,
    bf16* q, bf16* k, bf16* v,
    int dim, int kv_dim) {
    const int row = blockIdx.x;
    if (row >= dim + 2 * kv_dim) return;

    // rows [0,dim) → Q, [dim,dim+kv_dim) → K, rest → V
    const bf16* w;
    int local_row = row;
    if (row < dim) {
        w = wq + static_cast<size_t>(row) * dim;
    } else if (row < dim + kv_dim) {
        local_row = row - dim;
        w = wk + static_cast<size_t>(local_row) * dim;
    } else {
        local_row = row - dim - kv_dim;
        w = wv + static_cast<size_t>(local_row) * dim;
    }

    const float inv = *inv_rms;
    float acc = 0.0f;
    for (int i = threadIdx.x; i < dim; i += blockDim.x) {
        const float nx = x[i] * ld(norm_w, i) * inv;  // folded RMSNorm
        acc += ld(w, i) * nx;
    }
    const float dot = block_sum(acc);
    if (threadIdx.x == 0) {
        if (row < dim) st(q, row, dot);
        else if (row < dim + kv_dim) st(k, local_row, dot);
        else st(v, local_row, dot);
    }
}

// out = residual + W @ in
//
// The only generic GEMV. Closes both halves of a layer:
//   attention: x = x + Wo    @ attn   (2048×2048)
//   MLP:       x = x + Wdown @ tmp    (2048×8192)
// in is bf16, residual/out are the fp32 stream.
__global__ void proj_residual_kernel(
    const bf16* w, const bf16* in, const float* residual, float* out,
    int out_dim, int in_dim) {
    const int row = blockIdx.x;
    if (row >= out_dim) return;
    const bf16* wr = w + static_cast<size_t>(row) * in_dim;
    float acc = 0.0f;
    for (int i = threadIdx.x; i < in_dim; i += blockDim.x) {
        acc += ld(wr, i) * ld(in, i);
    }
    const float dot = block_sum(acc);
    if (threadIdx.x == 0) out[row] = residual[row] + dot;
}

// tmp = silu(Wgate @ nx) * (Wup @ nx)   (nx = rmsnorm(x), folded)
//
// One block per hidden row; both dots share each loaded nx value. Only the
// 8192-wide tmp is materialized — Wdown consumes it next.
// silu(g) = g * sigmoid(g) in fp32.
__global__ void gate_up_swiglu_kernel(
    const bf16* wgate, const bf16* wup, const float* x, const bf16* norm_w,
    const float* inv_rms, bf16* tmp, int hidden_dim, int dim) {
    const int row = blockIdx.x;
    if (row >= hidden_dim) return;
    const bf16* wg = wgate + static_cast<size_t>(row) * dim;
    const bf16* wu = wup + static_cast<size_t>(row) * dim;
    const float inv = *inv_rms;
    float gate = 0.0f, up = 0.0f;
    for (int i = threadIdx.x; i < dim; i += blockDim.x) {
        const float nx = x[i] * ld(norm_w, i) * inv;  // folded RMSNorm
        gate += ld(wg, i) * nx;
        up += ld(wu, i) * nx;
    }
    const float g = block_sum(gate);
    const float u = block_sum(up);
    if (threadIdx.x == 0) {
        st(tmp, row, (g / (1.0f + expf(-g))) * u);
    }
}

// logits[v] = embeddings[v] · rmsnorm(x)   for all 128,256 rows
//
// Tied output head: the embedding matrix is reused as the unembedding.
// Structurally identical to qkv_gemv_norm with vocab_size rows; logits stay
// fp32 for the argmax.
__global__ void logits_norm_kernel(
    const bf16* embeddings, const float* x, const bf16* norm_w, const float* inv_rms,
    float* logits, int vocab_size, int dim) {
    const int row = blockIdx.x;
    if (row >= vocab_size) return;
    const bf16* wr = embeddings + static_cast<size_t>(row) * dim;
    const float inv = *inv_rms;
    float acc = 0.0f;
    for (int i = threadIdx.x; i < dim; i += blockDim.x) {
        acc += ld(wr, i) * (x[i] * ld(norm_w, i) * inv);
    }
    const float dot = block_sum(acc);
    if (threadIdx.x == 0) logits[row] = dot;
}

// --- launch wrappers ---

void launch_qkv_gemv_norm(
    const bf16* wq, const bf16* wk, const bf16* wv,
    const float* x, const bf16* norm_w, const float* inv_rms,
    bf16* q, bf16* k, bf16* v, int dim, int kv_dim) {
    qkv_gemv_norm_kernel<<<dim + 2 * kv_dim, BLOCK>>>(
        wq, wk, wv, x, norm_w, inv_rms, q, k, v, dim, kv_dim);
}

void launch_proj_residual(
    const bf16* w, const bf16* in, const float* residual, float* out,
    int out_dim, int in_dim) {
    proj_residual_kernel<<<out_dim, BLOCK>>>(w, in, residual, out, out_dim, in_dim);
}

void launch_gate_up_swiglu(
    const bf16* wgate, const bf16* wup, const float* x, const bf16* norm_w,
    const float* inv_rms, bf16* tmp, int hidden_dim, int dim) {
    gate_up_swiglu_kernel<<<hidden_dim, BLOCK>>>(
        wgate, wup, x, norm_w, inv_rms, tmp, hidden_dim, dim);
}

void launch_logits_norm(
    const bf16* embeddings, const float* x, const bf16* norm_w,
    const float* inv_rms, float* logits, int vocab_size, int dim) {
    logits_norm_kernel<<<vocab_size, BLOCK>>>(
        embeddings, x, norm_w, inv_rms, logits, vocab_size, dim);
}
