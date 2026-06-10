#!/usr/bin/env python3
import argparse
import re
import subprocess
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def parse_timing(stdout):
    match = re.search(
        r"^TIMING load_ms=([0-9.]+) decode_ms=([0-9.]+) model_forwards=([0-9]+) forwards_per_s=([0-9.]+)",
        stdout,
        re.MULTILINE,
    )
    if not match:
        raise RuntimeError(f"missing TIMING line:\n{stdout}")
    return {
        "load_ms": float(match.group(1)),
        "decode_ms": float(match.group(2)),
        "model_forwards": int(match.group(3)),
        "forwards_per_s": float(match.group(4)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", default="d-matrix/Llama-3.2-1B")
    parser.add_argument("--weights", required=True)
    parser.add_argument("--tokenizer", required=True)
    parser.add_argument("--bin", default="./build/llama3_cuda")
    parser.add_argument("--prompt", default="Why is the sky blue?")
    parser.add_argument("--steps", type=int, default=16)
    parser.add_argument("--max-seq", type=int, default=256)
    parser.add_argument("--dtype", choices=["bf16", "fp16", "fp32"], default="bf16")
    args = parser.parse_args()

    tok = AutoTokenizer.from_pretrained(args.tokenizer, trust_remote_code=False)
    ids = [tok.bos_token_id] + tok.encode(args.prompt, add_special_tokens=False)

    cmd = [
        args.bin,
        "--model",
        args.weights,
        "--tokens",
        ",".join(str(x) for x in ids),
        "--steps",
        str(args.steps),
        "--max-seq",
        str(args.max_seq),
        "--timings",
    ]
    cuda_start = time.perf_counter()
    cuda_proc = subprocess.run(cmd, text=True, capture_output=True, check=True)
    cuda_wall = time.perf_counter() - cuda_start
    cuda_t = parse_timing(cuda_proc.stdout)

    dtype = {"bf16": torch.bfloat16, "fp16": torch.float16, "fp32": torch.float32}[args.dtype]
    load_start = time.perf_counter()
    model = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        dtype=dtype,
        trust_remote_code=False,
    )
    model.eval()
    load_s = time.perf_counter() - load_start

    input_ids = torch.tensor([ids], dtype=torch.long)
    gen_start = time.perf_counter()
    with torch.no_grad():
        out = model.generate(
            input_ids,
            max_new_tokens=args.steps,
            do_sample=False,
            pad_token_id=tok.eos_token_id,
            use_cache=True,
        )
    gen_s = time.perf_counter() - gen_start

    # One forward per prompt token, then one per requested generated token. The
    # CUDA path intentionally pre-fills token-by-token, so this is its natural
    # unit of work. Transformers prefill is vectorized, so this comparison is a
    # practical wall-clock comparison rather than a kernel-for-kernel matchup.
    forwards = len(ids) + args.steps

    print("CUDA_STDOUT:")
    print(cuda_proc.stdout, end="")
    print(f"TRANSFORMERS_TOKENS: {' '.join(str(x) for x in out[0].tolist())}")
    print()
    print(f"torch_cuda_available={torch.cuda.is_available()}")
    print(f"transformers_dtype={args.dtype}")
    print(f"prompt_tokens={len(ids)} generated_tokens={args.steps} model_forwards={forwards}")
    print(f"cuda_load_upload_s={cuda_t['load_ms'] / 1000.0:.3f}")
    print(f"cuda_decode_s={cuda_t['decode_ms'] / 1000.0:.3f}")
    print(f"cuda_end_to_end_s={cuda_wall:.3f}")
    print(f"transformers_load_s={load_s:.3f}")
    print(f"transformers_generate_s={gen_s:.3f}")
    print(f"cuda_decode_forwards_per_s={cuda_t['forwards_per_s']:.3f}")
    print(f"transformers_effective_forwards_per_s={forwards / gen_s:.3f}")
    print(f"cuda_decode_vs_transformers_generate_ratio={(cuda_t['decode_ms'] / 1000.0) / gen_s:.3f}")


if __name__ == "__main__":
    main()
