#pragma once

// Shared device-side helpers for all kernel translation units.
//
// Precision policy (uniform across every kernel):
//   - Everything in HBM that is 16-bit is bf16: weights, KV cache, and the
//     small q/k/v/attn/tmp scratch vectors.
//   - Every scalar that ever accumulates is fp32: dot products, softmax,
//     residual stream, RMS statistics, logits.
//   - bf16 is therefore *only* a storage format. Values are widened to fp32
//     on load and rounded back on the final store. That is the same contract
//     a Tenstorrent port wants: bf16 tiles in DRAM, fp32 accumulation in FPU.
//
// Grid convention: every GEMV-like kernel launches one block per output
// element with BLOCK threads striding the input vector, then tree-reduces in
// shared memory. attention launches one block per query head. There is no
// tiling and no tensor-core use — the design goal is readable dataflow, not
// peak throughput.

#include "kernels.cuh"

constexpr float NEG_INF = -3.4028234663852886e38f;
constexpr int BLOCK = 256;  // threads per block; all reductions assume power of 2

// Load/store helpers so the bf16<->fp32 boundary is explicit and grep-able.
__inline__ __device__ float ld(const bf16* p, size_t i) { return __bfloat162float(p[i]); }
__inline__ __device__ void st(bf16* p, size_t i, float v) { p[i] = __float2bfloat16(v); }

// Block-wide sum/max over each thread's partial value (tree reduction in
// shared memory). Every kernel that produces one scalar per block ends here.
__inline__ __device__ float block_sum(float v) {
    __shared__ float scratch[BLOCK];
    scratch[threadIdx.x] = v;
    __syncthreads();
    for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
        if (threadIdx.x < stride) scratch[threadIdx.x] += scratch[threadIdx.x + stride];
        __syncthreads();
    }
    return scratch[0];
}

__inline__ __device__ float block_max(float v) {
    __shared__ float scratch[BLOCK];
    scratch[threadIdx.x] = v;
    __syncthreads();
    for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
        if (threadIdx.x < stride) scratch[threadIdx.x] = fmaxf(scratch[threadIdx.x], scratch[threadIdx.x + stride]);
        __syncthreads();
    }
    return scratch[0];
}
