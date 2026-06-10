#!/usr/bin/env python3
import argparse
import json
import os
import struct
from pathlib import Path

import torch
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer


MAGIC = b"L32CU001"
VERSION = 2  # version 1 = fp16 payload, version 2 = bf16 payload


def as_bf16_bytes(tensor: torch.Tensor) -> bytes:
    # numpy has no bfloat16, so reinterpret the bf16 bits as uint16 in torch.
    arr = tensor.detach().cpu().contiguous().to(torch.bfloat16)
    return arr.view(torch.uint16).numpy().tobytes()


def write_tensor(f, state, name, shape):
    if name not in state:
        raise KeyError(f"missing tensor {name}")
    tensor = state[name]
    if tuple(tensor.shape) != tuple(shape):
        raise ValueError(f"{name} shape {tuple(tensor.shape)} != expected {shape}")
    f.write(as_bf16_bytes(tensor))


def rope_scaling_values(config):
    scaling = getattr(config, "rope_scaling", None) or {}
    rope_type = scaling.get("rope_type") or scaling.get("type")
    if rope_type == "llama3":
        return (
            float(scaling.get("factor", 1.0)),
            float(scaling.get("low_freq_factor", 1.0)),
            float(scaling.get("high_freq_factor", 1.0)),
            float(scaling.get("original_max_position_embeddings", 8192.0)),
        )
    return (1.0, 1.0, 1.0, float(getattr(config, "max_position_embeddings", 0)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", default="meta-llama/Llama-3.2-1B")
    parser.add_argument("--out", required=True)
    parser.add_argument("--tokenizer-out")
    parser.add_argument("--hf-token", default=os.environ.get("HF_TOKEN"))
    parser.add_argument("--revision")
    args = parser.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    config = AutoConfig.from_pretrained(
        args.model_id,
        token=args.hf_token,
        revision=args.revision,
        trust_remote_code=False,
    )

    # Llama 3 checkpoints ship bf16, so loading bf16 and writing bf16 is lossless.
    model = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        dtype=torch.bfloat16,
        token=args.hf_token,
        revision=args.revision,
        trust_remote_code=False,
    )
    model.eval()
    state = model.state_dict()

    dim = int(config.hidden_size)
    hidden_dim = int(config.intermediate_size)
    n_layers = int(config.num_hidden_layers)
    n_heads = int(config.num_attention_heads)
    n_kv_heads = int(config.num_key_value_heads)
    vocab_size = int(config.vocab_size)
    max_pos = int(config.max_position_embeddings)
    rope_dim = dim // n_heads
    norm_eps = float(config.rms_norm_eps)
    rope_theta = float(getattr(config, "rope_theta", 10000.0))
    rope_factor, rope_low, rope_high, rope_orig = rope_scaling_values(config)

    header = struct.pack(
        "<8s9i6fQ",
        MAGIC,
        VERSION,
        dim,
        hidden_dim,
        n_layers,
        n_heads,
        n_kv_heads,
        vocab_size,
        max_pos,
        rope_dim,
        norm_eps,
        rope_theta,
        rope_factor,
        rope_low,
        rope_high,
        rope_orig,
        0,
    )

    with out.open("wb") as f:
        f.write(header)
        write_tensor(f, state, "model.embed_tokens.weight", (vocab_size, dim))
        kv_dim = n_kv_heads * rope_dim
        for layer in range(n_layers):
            prefix = f"model.layers.{layer}"
            write_tensor(f, state, f"{prefix}.input_layernorm.weight", (dim,))
            write_tensor(f, state, f"{prefix}.self_attn.q_proj.weight", (dim, dim))
            write_tensor(f, state, f"{prefix}.self_attn.k_proj.weight", (kv_dim, dim))
            write_tensor(f, state, f"{prefix}.self_attn.v_proj.weight", (kv_dim, dim))
            write_tensor(f, state, f"{prefix}.self_attn.o_proj.weight", (dim, dim))
            write_tensor(f, state, f"{prefix}.post_attention_layernorm.weight", (dim,))
            write_tensor(f, state, f"{prefix}.mlp.gate_proj.weight", (hidden_dim, dim))
            write_tensor(f, state, f"{prefix}.mlp.up_proj.weight", (hidden_dim, dim))
            write_tensor(f, state, f"{prefix}.mlp.down_proj.weight", (dim, hidden_dim))
        write_tensor(f, state, "model.norm.weight", (dim,))

        end = f.tell()
        tensor_bytes = end - len(header)
        f.seek(0)
        f.write(
            struct.pack(
                "<8s9i6fQ",
                MAGIC,
                VERSION,
                dim,
                hidden_dim,
                n_layers,
                n_heads,
                n_kv_heads,
                vocab_size,
                max_pos,
                rope_dim,
                norm_eps,
                rope_theta,
                rope_factor,
                rope_low,
                rope_high,
                rope_orig,
                tensor_bytes,
            )
        )

    meta = {
        "model_id": args.model_id,
        "dim": dim,
        "hidden_dim": hidden_dim,
        "n_layers": n_layers,
        "n_heads": n_heads,
        "n_kv_heads": n_kv_heads,
        "vocab_size": vocab_size,
        "max_position_embeddings": max_pos,
        "rope_dim": rope_dim,
        "norm_eps": norm_eps,
        "rope_theta": rope_theta,
        "rope_factor": rope_factor,
        "rope_low_freq_factor": rope_low,
        "rope_high_freq_factor": rope_high,
        "rope_original_max_position_embeddings": rope_orig,
        "tensor_bytes": tensor_bytes,
    }
    out.with_suffix(out.suffix + ".json").write_text(json.dumps(meta, indent=2) + "\n")

    if args.tokenizer_out:
        tok = AutoTokenizer.from_pretrained(
            args.model_id,
            token=args.hf_token,
            revision=args.revision,
            trust_remote_code=False,
        )
        tok.save_pretrained(args.tokenizer_out)

    print(f"wrote {out} ({tensor_bytes / (1024 ** 3):.2f} GiB bf16 tensors)")


if __name__ == "__main__":
    main()
