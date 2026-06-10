#include "model_format.h"

#include <cmath>
#include <cstring>
#include <sstream>
#include <stdexcept>

void read_exact(std::ifstream& f, void* dst, size_t n) {
    f.read(reinterpret_cast<char*>(dst), static_cast<std::streamsize>(n));
    if (!f) throw std::runtime_error("unexpected end of file");
}

static int32_t read_i32(std::ifstream& f) {
    int32_t v;
    read_exact(f, &v, sizeof(v));
    return v;
}

static float read_f32(std::ifstream& f) {
    float v;
    read_exact(f, &v, sizeof(v));
    return v;
}

static uint64_t read_u64(std::ifstream& f) {
    uint64_t v;
    read_exact(f, &v, sizeof(v));
    return v;
}

Header read_header(std::ifstream& f) {
    char magic[8];
    read_exact(f, magic, sizeof(magic));
    if (std::memcmp(magic, "L32CU001", 8) != 0) {
        throw std::runtime_error("bad model magic");
    }

    Header h;
    h.version = read_i32(f);
    h.dim = read_i32(f);
    h.hidden_dim = read_i32(f);
    h.n_layers = read_i32(f);
    h.n_heads = read_i32(f);
    h.n_kv_heads = read_i32(f);
    h.vocab_size = read_i32(f);
    h.max_position_embeddings = read_i32(f);
    h.rope_dim = read_i32(f);
    h.norm_eps = read_f32(f);
    h.rope_theta = read_f32(f);
    h.rope_factor = read_f32(f);
    h.rope_low_freq_factor = read_f32(f);
    h.rope_high_freq_factor = read_f32(f);
    h.rope_original_max_pos = read_f32(f);
    h.tensor_bytes = read_u64(f);

    if (h.version != 2) {
        throw std::runtime_error(
            h.version == 1
                ? "model is the old fp16 format (version 1); re-run scripts/download_convert.py for bf16"
                : "unsupported model version");
    }
    if (h.dim <= 0 || h.hidden_dim <= 0 || h.n_layers <= 0 ||
        h.n_heads <= 0 || h.n_kv_heads <= 0 || h.vocab_size <= 0) {
        throw std::runtime_error("invalid model dimensions");
    }
    if (h.dim % h.n_heads != 0) {
        throw std::runtime_error("dim must be divisible by n_heads");
    }
    if (h.rope_dim != h.dim / h.n_heads) {
        throw std::runtime_error("only full-head RoPE is supported");
    }
    return h;
}

size_t tensor_elems_expected(const Header& h) {
    const size_t dim = h.dim;
    const size_t hidden = h.hidden_dim;
    const size_t kv_dim = h.n_kv_heads * h.rope_dim;
    size_t elems = static_cast<size_t>(h.vocab_size) * dim;
    for (int i = 0; i < h.n_layers; ++i) {
        elems += dim;          // input_layernorm.weight
        elems += dim * dim;    // q_proj.weight
        elems += kv_dim * dim; // k_proj.weight
        elems += kv_dim * dim; // v_proj.weight
        elems += dim * dim;    // o_proj.weight
        elems += dim;          // post_attention_layernorm.weight
        elems += hidden * dim; // gate_proj.weight
        elems += hidden * dim; // up_proj.weight
        elems += dim * hidden; // down_proj.weight
    }
    elems += dim;              // final norm
    return elems;
}

ModelPtrs build_ptrs(const Header& h, const bf16* base) {
    ModelPtrs p;
    const size_t dim = h.dim;
    const size_t hidden = h.hidden_dim;
    const size_t kv_dim = h.n_kv_heads * h.rope_dim;

    const bf16* cur = base;
    p.tok_embeddings = cur;
    cur += static_cast<size_t>(h.vocab_size) * dim;
    p.layers.resize(h.n_layers);
    for (int i = 0; i < h.n_layers; ++i) {
        LayerPtrs l;
        l.attn_norm = cur; cur += dim;
        l.wq = cur; cur += dim * dim;
        l.wk = cur; cur += kv_dim * dim;
        l.wv = cur; cur += kv_dim * dim;
        l.wo = cur; cur += dim * dim;
        l.ffn_norm = cur; cur += dim;
        l.wgate = cur; cur += hidden * dim;
        l.wup = cur; cur += hidden * dim;
        l.wdown = cur; cur += dim * hidden;
        p.layers[i] = l;
    }
    p.final_norm = cur;
    return p;
}

std::vector<int> parse_tokens(const std::string& s) {
    std::vector<int> out;
    std::string item;
    std::stringstream ss(s);
    while (std::getline(ss, item, ',')) {
        if (!item.empty()) out.push_back(std::stoi(item));
    }
    return out;
}

std::vector<float> make_rope_table(const Header& h, int max_seq, bool cosine) {
    const int half_dim = h.rope_dim / 2;
    std::vector<float> table(static_cast<size_t>(max_seq) * half_dim);
    for (int i = 0; i < half_dim; ++i) {
        double inv_freq = 1.0 / std::pow(static_cast<double>(h.rope_theta),
                                         static_cast<double>(2 * i) / h.rope_dim);

        // Llama 3 extends context by scaling low-frequency RoPE dimensions more
        // than high-frequency ones. This mirrors HF's llama3 rope_scaling path.
        if (h.rope_factor != 1.0f) {
            const double old_ctx = h.rope_original_max_pos;
            const double low = h.rope_low_freq_factor;
            const double high = h.rope_high_freq_factor;
            const double wavelen = 2.0 * M_PI / inv_freq;
            const double low_wavelen = old_ctx / low;
            const double high_wavelen = old_ctx / high;
            if (wavelen > low_wavelen) {
                inv_freq /= h.rope_factor;
            } else if (wavelen >= high_wavelen) {
                const double smooth =
                    (old_ctx / wavelen - low) / (high - low);
                inv_freq = (1.0 - smooth) * inv_freq / h.rope_factor +
                           smooth * inv_freq;
            }
        }

        for (int pos = 0; pos < max_seq; ++pos) {
            const double angle = static_cast<double>(pos) * inv_freq;
            table[static_cast<size_t>(pos) * half_dim + i] =
                cosine ? static_cast<float>(std::cos(angle))
                       : static_cast<float>(std::sin(angle));
        }
    }
    return table;
}

