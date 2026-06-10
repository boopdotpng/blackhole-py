#!/usr/bin/env python3
import argparse
import re
import subprocess

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def cuda_tokens(binary, weights, token_ids, steps, max_seq):
    cmd = [
        binary,
        "--model",
        weights,
        "--tokens",
        ",".join(str(x) for x in token_ids),
        "--steps",
        str(steps),
        "--max-seq",
        str(max_seq),
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True, check=True)
    match = re.search(r"^TOKENS:\s*(.*)$", proc.stdout, re.MULTILINE)
    if not match:
        raise RuntimeError(f"missing TOKENS line:\n{proc.stdout}\n{proc.stderr}")
    return [int(x) for x in match.group(1).strip().split()], proc.stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", default="d-matrix/Llama-3.2-1B")
    parser.add_argument("--weights", required=True)
    parser.add_argument("--tokenizer", required=True)
    parser.add_argument("--bin", default="./build/llama3_cuda")
    parser.add_argument("--prompt", default="Why is the sky blue?")
    parser.add_argument("--steps", type=int, default=4)
    parser.add_argument("--max-seq", type=int, default=2048)
    parser.add_argument("--dtype", choices=["bf16", "fp16", "fp32"], default="bf16")
    parser.add_argument("--no-bos", action="store_true")
    args = parser.parse_args()

    tok = AutoTokenizer.from_pretrained(args.tokenizer, trust_remote_code=False)
    input_ids = tok.encode(args.prompt, add_special_tokens=False)
    if not args.no_bos and tok.bos_token_id is not None:
        input_ids = [tok.bos_token_id] + input_ids

    ours, stdout = cuda_tokens(args.bin, args.weights, input_ids, args.steps, args.max_seq)

    dtype = {"bf16": torch.bfloat16, "fp16": torch.float16, "fp32": torch.float32}[args.dtype]
    model = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        dtype=dtype,
        trust_remote_code=False,
    )
    model.eval()
    with torch.no_grad():
        ref = model.generate(
            torch.tensor([input_ids], dtype=torch.long),
            max_new_tokens=args.steps,
            do_sample=False,
            pad_token_id=tok.eos_token_id,
            use_cache=True,
        )[0].tolist()

    print(stdout, end="")
    print("REF_TOKENS:", " ".join(str(x) for x in ref))
    print("\nCUDA_TEXT:")
    print(tok.decode(ours, skip_special_tokens=False))
    print("\nREF_TEXT:")
    print(tok.decode(ref, skip_special_tokens=False))

    if ours != ref:
        for i, (a, b) in enumerate(zip(ours, ref)):
            if a != b:
                raise SystemExit(f"mismatch at position {i}: cuda={a}, transformers={b}")
        raise SystemExit(f"length mismatch: cuda={len(ours)}, transformers={len(ref)}")
    print("\nMATCH")


if __name__ == "__main__":
    main()
