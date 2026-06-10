#pragma once

#include "kernels.cuh"  // for the bf16 alias

#include <cstddef>
#include <cstdint>
#include <fstream>
#include <string>
#include <vector>

// Flat on-disk format written by scripts/download_convert.py.
//
// All tensors are stored as row-major bf16, with no per-tensor metadata. The
// fixed tensor order makes the CUDA runtime simple: read one contiguous blob,
// upload it once, and recover typed layer pointers by walking known shapes.
//
// version 1 = fp16 payload (no longer supported), version 2 = bf16 payload.
struct Header {
    int32_t version = 0;
    int32_t dim = 0;
    int32_t hidden_dim = 0;
    int32_t n_layers = 0;
    int32_t n_heads = 0;
    int32_t n_kv_heads = 0;
    int32_t vocab_size = 0;
    int32_t max_position_embeddings = 0;
    int32_t rope_dim = 0;
    float norm_eps = 0.0f;
    float rope_theta = 0.0f;
    float rope_factor = 1.0f;
    float rope_low_freq_factor = 1.0f;
    float rope_high_freq_factor = 1.0f;
    float rope_original_max_pos = 0.0f;
    uint64_t tensor_bytes = 0;
};

struct LayerPtrs {
    const bf16* attn_norm;
    const bf16* wq;
    const bf16* wk;
    const bf16* wv;
    const bf16* wo;
    const bf16* ffn_norm;
    const bf16* wgate;
    const bf16* wup;
    const bf16* wdown;
};

struct ModelPtrs {
    const bf16* tok_embeddings;
    std::vector<LayerPtrs> layers;
    const bf16* final_norm;
};

void read_exact(std::ifstream& f, void* dst, size_t n);
Header read_header(std::ifstream& f);
size_t tensor_elems_expected(const Header& h);
ModelPtrs build_ptrs(const Header& h, const bf16* base);
std::vector<int> parse_tokens(const std::string& s);
std::vector<float> make_rope_table(const Header& h, int max_seq, bool cosine);

