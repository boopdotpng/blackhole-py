// Token-boundary kernels: the small ops at the start and end of a decode step,
// plus the RMSNorm statistic used throughout.
//
//   embed         x = embeddings[token]                  (copy, bf16 → fp32)
//   rmsnorm_inv   inv_rms = 1/sqrt(mean(x²)+eps)         (single-block reduce)
//   argmax        next = argmax(logits), two stages      (grid reduce)

#include "kernels_common.cuh"

// x = embeddings[token]
//
// The residual stream x stays fp32 for the whole forward pass so residual
// adds and norm statistics never round.
__global__ void embed_kernel(const bf16* embeddings, int token, float* x, int dim) {
    const int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < dim) x[i] = ld(embeddings, static_cast<size_t>(token) * dim + i);
}

// inv_rms = 1 / sqrt(mean(x²) + eps)
//
// Only the scalar is computed here. The full normalization
//   nx[i] = x[i] * norm_w[i] * inv_rms
// is folded into whatever GEMV reads x next (see kernels_gemv.cu), so the
// normalized vector is never written to memory. One block; each thread
// strides the 2048 floats.
__global__ void rmsnorm_inv_kernel(const float* x, float* inv_out, int dim, float eps) {
    float sum = 0.0f;
    for (int i = threadIdx.x; i < dim; i += blockDim.x) {
        sum += x[i] * x[i];
    }
    const float total = block_sum(sum);
    if (threadIdx.x == 0) {
        *inv_out = rsqrtf(total / static_cast<float>(dim) + eps);
    }
}

// Greedy argmax over the vocabulary, two stages.
// Stage 1: each block reduces a grid-strided slice to one (value, id).
// Stage 2: one block reduces the per-block candidates to the next token.
__global__ void argmax_stage1_kernel(
    const float* logits, float* block_vals, int* block_ids, int vocab_size) {
    const int tid = threadIdx.x;
    float best = NEG_INF;
    int best_id = 0;
    for (int i = blockIdx.x * blockDim.x + tid; i < vocab_size; i += gridDim.x * blockDim.x) {
        if (logits[i] > best) { best = logits[i]; best_id = i; }
    }
    __shared__ float vals[BLOCK];
    __shared__ int ids[BLOCK];
    vals[tid] = best;
    ids[tid] = best_id;
    __syncthreads();
    for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
        if (tid < stride && vals[tid + stride] > vals[tid]) {
            vals[tid] = vals[tid + stride];
            ids[tid] = ids[tid + stride];
        }
        __syncthreads();
    }
    if (tid == 0) {
        block_vals[blockIdx.x] = vals[0];
        block_ids[blockIdx.x] = ids[0];
    }
}

__global__ void argmax_stage2_kernel(
    const float* block_vals, const int* block_ids, int* out_token, int nblocks) {
    const int tid = threadIdx.x;
    float best = NEG_INF;
    int best_id = 0;
    for (int i = tid; i < nblocks; i += blockDim.x) {
        if (block_vals[i] > best) { best = block_vals[i]; best_id = block_ids[i]; }
    }
    __shared__ float vals[BLOCK];
    __shared__ int ids[BLOCK];
    vals[tid] = best;
    ids[tid] = best_id;
    __syncthreads();
    for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
        if (tid < stride && vals[tid + stride] > vals[tid]) {
            vals[tid] = vals[tid + stride];
            ids[tid] = ids[tid + stride];
        }
        __syncthreads();
    }
    if (tid == 0) *out_token = ids[0];
}

// --- launch wrappers ---

void launch_embed(const bf16* embeddings, int token, float* x, int dim) {
    embed_kernel<<<(dim + BLOCK - 1) / BLOCK, BLOCK>>>(embeddings, token, x, dim);
}

void launch_rmsnorm_inv(const float* x, float* inv_out, int dim, float eps) {
    rmsnorm_inv_kernel<<<1, BLOCK>>>(x, inv_out, dim, eps);
}

void launch_argmax(
    const float* logits, float* block_vals, int* block_ids, int* out_token,
    int vocab_size, int arg_blocks) {
    argmax_stage1_kernel<<<arg_blocks, BLOCK>>>(logits, block_vals, block_ids, vocab_size);
    argmax_stage2_kernel<<<1, BLOCK>>>(block_vals, block_ids, out_token, arg_blocks);
}
