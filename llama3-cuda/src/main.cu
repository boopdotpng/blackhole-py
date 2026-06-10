#include "cuda_utils.cuh"
#include "kernels.cuh"
#include "model_format.h"

#include <cuda_runtime.h>

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

// This file is the "LLM control flow" part. It intentionally reads like the
// pseudocode for a decoder-only transformer and delegates the CUDA details to
// kernels.cu. If you know CUDA but not LLMs, think of each generated token as:
//
//   1. Load a 2048-float activation vector for the current token.
//   2. Run 16 identical layers. Each layer is mostly several GEMVs plus a small
//      attention reduction over the KV cache.
//   3. Project the final vector against every vocab embedding row and argmax.
//
// Batch size is fixed at 1, so all matrix multiplications are matrix-vector
// products. That keeps the shape of the math visible at the cost of speed.

struct Args {
    std::string model;
    std::string tokens;
    int steps = 16;
    int max_seq = 2048;
    bool timings = false;
};

static Args parse_args(int argc, char** argv) {
    Args a;
    for (int i = 1; i < argc; ++i) {
        std::string key = argv[i];
        auto need = [&](const char* name) -> std::string {
            if (i + 1 >= argc) throw std::runtime_error(std::string("missing value for ") + name);
            return argv[++i];
        };
        if (key == "--model") a.model = need("--model");
        else if (key == "--tokens") a.tokens = need("--tokens");
        else if (key == "--steps") a.steps = std::stoi(need("--steps"));
        else if (key == "--max-seq") a.max_seq = std::stoi(need("--max-seq"));
        else if (key == "--timings") a.timings = true;
        else if (key == "--help") {
            std::cout << "usage: llama3_cuda --model model.l3cu --tokens 1,2,3 [--steps N] [--max-seq N] [--timings]\n";
            std::exit(0);
        } else {
            throw std::runtime_error("unknown argument: " + key);
        }
    }
    if (a.model.empty()) throw std::runtime_error("--model is required");
    if (a.tokens.empty()) throw std::runtime_error("--tokens is required");
    return a;
}

int main(int argc, char** argv) {
    try {
        const Args args = parse_args(argc, argv);
        const auto load_start = std::chrono::steady_clock::now();
        std::vector<int> tokens = parse_tokens(args.tokens);
        if (tokens.empty()) throw std::runtime_error("no input tokens");

        std::ifstream f(args.model, std::ios::binary);
        if (!f) throw std::runtime_error("failed to open model file");
        Header h = read_header(f);
        if (args.max_seq <= 0 || args.max_seq > h.max_position_embeddings) {
            throw std::runtime_error("--max-seq must be positive and <= model max_position_embeddings");
        }
        if (static_cast<int>(tokens.size()) + args.steps > args.max_seq) {
            throw std::runtime_error("prompt length + steps exceeds --max-seq");
        }

        const size_t expected_elems = tensor_elems_expected(h);
        const size_t expected_bytes = expected_elems * sizeof(uint16_t);
        if (h.tensor_bytes != expected_bytes) {
            throw std::runtime_error("model tensor byte count does not match header dimensions");
        }

        std::vector<uint16_t> host_weights(expected_elems);
        read_exact(f, host_weights.data(), expected_bytes);

        // Upload the entire bf16 checkpoint once. There is no CUDA-side object
        // format: ModelPtrs is just a set of typed offsets into this allocation.
        bf16* d_weights = nullptr;
        CUDA_CHECK(cudaMalloc(&d_weights, expected_bytes));
        CUDA_CHECK(cudaMemcpy(d_weights, host_weights.data(), expected_bytes, cudaMemcpyHostToDevice));
        ModelPtrs mp = build_ptrs(h, d_weights);

        std::vector<float> cos_h = make_rope_table(h, args.max_seq, true);
        std::vector<float> sin_h = make_rope_table(h, args.max_seq, false);
        float* d_cos = nullptr;
        float* d_sin = nullptr;
        CUDA_CHECK(cudaMalloc(&d_cos, cos_h.size() * sizeof(float)));
        CUDA_CHECK(cudaMalloc(&d_sin, sin_h.size() * sizeof(float)));
        CUDA_CHECK(cudaMemcpy(d_cos, cos_h.data(), cos_h.size() * sizeof(float), cudaMemcpyHostToDevice));
        CUDA_CHECK(cudaMemcpy(d_sin, sin_h.data(), sin_h.size() * sizeof(float), cudaMemcpyHostToDevice));

        float *d_x = nullptr, *d_y = nullptr, *d_inv = nullptr, *d_logits = nullptr;
        bf16 *d_q = nullptr, *d_k = nullptr, *d_v = nullptr, *d_attn = nullptr, *d_tmp = nullptr;
        bf16 *d_k_cache = nullptr, *d_v_cache = nullptr;
        float *d_scores = nullptr, *d_block_vals = nullptr;
        int *d_block_ids = nullptr, *d_next = nullptr;

        const int dim = h.dim;
        const int head_dim = h.rope_dim;
        const int kv_dim = h.n_kv_heads * head_dim;
        const size_t cache_elems =
            static_cast<size_t>(h.n_layers) * h.n_kv_heads * args.max_seq * head_dim;
        const int arg_blocks = 256;

        CUDA_CHECK(cudaMalloc(&d_x, dim * sizeof(float)));
        CUDA_CHECK(cudaMalloc(&d_y, dim * sizeof(float)));
        CUDA_CHECK(cudaMalloc(&d_inv, sizeof(float)));
        CUDA_CHECK(cudaMalloc(&d_q, dim * sizeof(bf16)));
        CUDA_CHECK(cudaMalloc(&d_k, kv_dim * sizeof(bf16)));
        CUDA_CHECK(cudaMalloc(&d_v, kv_dim * sizeof(bf16)));
        CUDA_CHECK(cudaMalloc(&d_attn, dim * sizeof(bf16)));
        CUDA_CHECK(cudaMalloc(&d_tmp, static_cast<size_t>(h.hidden_dim) * sizeof(bf16)));
        CUDA_CHECK(cudaMalloc(&d_k_cache, cache_elems * sizeof(bf16)));
        CUDA_CHECK(cudaMalloc(&d_v_cache, cache_elems * sizeof(bf16)));
        CUDA_CHECK(cudaMalloc(&d_scores, static_cast<size_t>(h.n_heads) * args.max_seq * sizeof(float)));
        CUDA_CHECK(cudaMalloc(&d_logits, static_cast<size_t>(h.vocab_size) * sizeof(float)));
        CUDA_CHECK(cudaMalloc(&d_block_vals, arg_blocks * sizeof(float)));
        CUDA_CHECK(cudaMalloc(&d_block_ids, arg_blocks * sizeof(int)));
        CUDA_CHECK(cudaMalloc(&d_next, sizeof(int)));
        CUDA_CHECK(cudaDeviceSynchronize());
        const auto decode_start = std::chrono::steady_clock::now();

        auto run_token = [&](int token, int pos) -> int {
            if (token < 0 || token >= h.vocab_size) throw std::runtime_error("token out of vocabulary");

            // One decode step consumes one input token, appends one K/V entry
            // per layer at position pos, then returns the greedy next-token id.
            // Prompt "prefill" uses this exact same path for every prompt token.
            launch_embed(mp.tok_embeddings, token, d_x, dim);

            for (int layer = 0; layer < h.n_layers; ++layer) {
                const LayerPtrs& lp = mp.layers[layer];
                bf16* layer_k_cache =
                    d_k_cache + static_cast<size_t>(layer) * h.n_kv_heads * args.max_seq * head_dim;
                bf16* layer_v_cache =
                    d_v_cache + static_cast<size_t>(layer) * h.n_kv_heads * args.max_seq * head_dim;

                // Attention block:
                //   h = rmsnorm(x)
                //   q,k,v = Wq/Wk/Wv @ h
                //   q,k = rope(q,k,pos); cache[pos] = k,v
                //   a = causal_gqa_attention(q, cache[0..pos])
                //   x = x + Wo @ a
                launch_rmsnorm_inv(d_x, d_inv, dim, h.norm_eps);
                launch_qkv_gemv_norm(
                    lp.wq, lp.wk, lp.wv, d_x, lp.attn_norm, d_inv,
                    d_q, d_k, d_v, dim, kv_dim);
                launch_rope_cache(
                    d_q, d_k, d_v, layer_k_cache, layer_v_cache,
                    d_cos, d_sin, pos, args.max_seq, h.n_heads, h.n_kv_heads, head_dim);
                launch_attention(
                    d_q, layer_k_cache, layer_v_cache, d_scores, d_attn,
                    pos, args.max_seq, h.n_heads, h.n_kv_heads, head_dim);
                launch_proj_residual(lp.wo, d_attn, d_x, d_y, dim, dim);
                std::swap(d_x, d_y);

                // MLP block:
                //   h = rmsnorm(x)
                //   tmp = silu(Wgate @ h) * (Wup @ h)
                //   x = x + Wdown @ tmp
                launch_rmsnorm_inv(d_x, d_inv, dim, h.norm_eps);
                launch_gate_up_swiglu(
                    lp.wgate, lp.wup, d_x, lp.ffn_norm, d_inv, d_tmp, h.hidden_dim, dim);
                launch_proj_residual(lp.wdown, d_tmp, d_x, d_y, dim, h.hidden_dim);
                std::swap(d_x, d_y);
            }

            // Final tied output head:
            //   logits = token_embedding @ final_rmsnorm(x)
            //   next = argmax(logits)
            launch_rmsnorm_inv(d_x, d_inv, dim, h.norm_eps);
            launch_logits_norm(
                mp.tok_embeddings, d_x, mp.final_norm, d_inv, d_logits, h.vocab_size, dim);
            launch_argmax(d_logits, d_block_vals, d_block_ids, d_next, h.vocab_size, arg_blocks);
            CUDA_CHECK(cudaGetLastError());

            int next = 0;
            CUDA_CHECK(cudaMemcpy(&next, d_next, sizeof(int), cudaMemcpyDeviceToHost));
            return next;
        };

        std::vector<int> all_tokens = tokens;
        int next = 0;
        for (size_t i = 0; i < tokens.size(); ++i) {
            next = run_token(tokens[i], static_cast<int>(i));
        }
        for (int i = 0; i < args.steps; ++i) {
            all_tokens.push_back(next);
            if (static_cast<int>(all_tokens.size()) >= args.max_seq) break;
            next = run_token(next, static_cast<int>(all_tokens.size()) - 1);
        }

        CUDA_CHECK(cudaDeviceSynchronize());
        const auto decode_end = std::chrono::steady_clock::now();
        std::cout << "TOKENS:";
        for (int t : all_tokens) std::cout << ' ' << t;
        std::cout << "\n";
        if (args.timings) {
            const double load_ms =
                std::chrono::duration<double, std::milli>(decode_start - load_start).count();
            const double decode_ms =
                std::chrono::duration<double, std::milli>(decode_end - decode_start).count();
            const int model_forwards = static_cast<int>(tokens.size()) + args.steps;
            std::cout << "TIMING load_ms=" << load_ms
                      << " decode_ms=" << decode_ms
                      << " model_forwards=" << model_forwards
                      << " forwards_per_s=" << (1000.0 * model_forwards / decode_ms)
                      << "\n";
        }

        cudaFree(d_weights);
        cudaFree(d_cos);
        cudaFree(d_sin);
        cudaFree(d_x);
        cudaFree(d_y);
        cudaFree(d_inv);
        cudaFree(d_q);
        cudaFree(d_k);
        cudaFree(d_v);
        cudaFree(d_attn);
        cudaFree(d_tmp);
        cudaFree(d_k_cache);
        cudaFree(d_v_cache);
        cudaFree(d_scores);
        cudaFree(d_logits);
        cudaFree(d_block_vals);
        cudaFree(d_block_ids);
        cudaFree(d_next);
    } catch (const std::exception& e) {
        std::cerr << "error: " << e.what() << "\n";
        return 1;
    }
    return 0;
}
