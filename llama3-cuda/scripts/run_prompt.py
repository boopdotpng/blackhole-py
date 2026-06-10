#!/usr/bin/env python3
import argparse
import re
import subprocess

from transformers import AutoTokenizer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bin", default="./build/llama3_cuda")
    parser.add_argument("--weights", required=True)
    parser.add_argument("--tokenizer", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--steps", type=int, default=32)
    parser.add_argument("--max-seq", type=int, default=2048)
    parser.add_argument("--no-bos", action="store_true")
    parser.add_argument(
        "--chat", action="store_true",
        help="wrap the prompt in the tokenizer's chat template (use for Instruct models)")
    args = parser.parse_args()

    tok = AutoTokenizer.from_pretrained(args.tokenizer, trust_remote_code=False)
    if args.chat:
        ids = tok.apply_chat_template(
            [{"role": "user", "content": args.prompt}],
            add_generation_prompt=True, return_dict=False)
    else:
        ids = tok.encode(args.prompt, add_special_tokens=False)
        if not args.no_bos and tok.bos_token_id is not None:
            ids = [tok.bos_token_id] + ids

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
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True, check=True)
    print(proc.stdout, end="")

    match = re.search(r"^TOKENS:\s*(.*)$", proc.stdout, re.MULTILINE)
    if not match:
        raise RuntimeError("CUDA runner did not print a TOKENS line")
    out_ids = [int(x) for x in match.group(1).strip().split()]

    # The CUDA binary always generates --steps tokens; trim at the first
    # end-of-turn/eos token after the prompt so chat output reads cleanly.
    stop_ids = {tok.eos_token_id, tok.convert_tokens_to_ids("<|eot_id|>")}
    gen = out_ids[len(ids):]
    for i, t in enumerate(gen):
        if t in stop_ids:
            gen = gen[:i]
            break
    print("\nTEXT:")
    print(tok.decode(out_ids[:len(ids)] + gen, skip_special_tokens=False))


if __name__ == "__main__":
    main()
