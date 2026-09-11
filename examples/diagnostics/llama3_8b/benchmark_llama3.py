"""Benchmark fixed-length decode and optionally compare an original runtime.

Startup, prompt ingestion, and diagnostic logit reads are excluded from timing.
Generation deliberately continues through EOS to keep the workload comparable.
"""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import time

from examples import llama3_8b as llama3


WEIGHT_BYTES_PER_TOKEN = 15_009_857_536
DEFAULT_PROMPTS = (
  "Explain why the sky is blue",
  "Write a Python function that returns the Fibonacci sequence.",
  "What are three interesting facts about the ocean?",
)


def load_reference(path):
  spec = importlib.util.spec_from_file_location("llama3_reference", path)
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module


def benchmark(module, prompts, args):
  runtime = module.Llama3Decode(args.safetensor, args.device, **(
    {"attention_cores": args.attention_cores} if module is llama3 else {}
  ))
  results = []
  try:
    for prompt_ids in prompts:
      if len(prompt_ids) + args.steps > module.ROPE_CACHE_TOKENS:
        raise ValueError("prompt and generation exceed the KV cache")
      runtime.load_tokens(prompt_ids)
      for position in range(len(prompt_ids) - 1):
        runtime.decode(position, logits=False, append=False)
      samples, tokens, logits = [], [], {}
      for step in range(args.steps):
        position = len(prompt_ids) - 1 + step
        started = time.perf_counter_ns()
        token, _ = runtime.decode(position)
        samples.append((time.perf_counter_ns() - started) / 1e3)
        tokens.append(token)
        # Check both sides of attention's 32-token block boundary, as well
        # as the first and final generated token. Readbacks are not timed.
        if step in (0, args.steps - 1) or position % 32 in (0, 31):
          data = runtime.device.read(runtime.logits)
          # Canonical vocabulary order, independent of per-core padding.
          stride = runtime.logits.shape[1] * 2
          logical = b"".join(data[index * stride:index * stride + count * 2]
                             for index, count in enumerate(runtime.lm_weight.item_counts))
          logits[str(position)] = hashlib.sha256(logical).hexdigest()
      rate = len(samples) * 1e6 / sum(samples)
      results.append({
        "prompt_tokens": len(prompt_ids),
        "kernel_launches_per_token": getattr(runtime, "decode_launch_count", None),
        "generated_tokens": tokens,
        "logit_sha256": logits,
        "tok_s": rate,
        "median_us": statistics.median(samples),
        "decode_us": samples,
        "weight_GB_s": rate * WEIGHT_BYTES_PER_TOKEN / 1e9,
      })
      print(f"  context {len(prompt_ids)}..{position + 1}: "
            f"{rate:.2f} tok/s, {statistics.median(samples):.2f} us median",
            flush=True)
  finally:
    runtime.close()
  return results


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--safetensor", default="weights/llama3-8b-bf16")
  parser.add_argument("--tokenizer", default="weights/llama3-8b-bf16")
  parser.add_argument("--device", type=int, default=0)
  parser.add_argument("--attention-cores", type=int, choices=(8, 16, 32), default=32)
  parser.add_argument("--steps", type=int, default=128)
  parser.add_argument("--prompt", action="append")
  parser.add_argument("--reference", type=Path,
                      help="original examples/llama3_8b.py to compare on the same card")
  parser.add_argument("--output", type=Path, help="write detailed JSON results")
  args = parser.parse_args()
  if args.steps < 1:
    parser.error("--steps must be positive")

  from transformers import AutoTokenizer
  tokenizer = AutoTokenizer.from_pretrained(args.tokenizer, local_files_only=True)
  prompts = []
  for prompt in args.prompt or DEFAULT_PROMPTS:
    ids = tokenizer.apply_chat_template(
      [{"role": "user", "content": prompt}],
      tokenize=True, add_generation_prompt=True,
    )
    if not isinstance(ids, list):
      ids = ids["input_ids"]
      if ids and isinstance(ids[0], list): ids = ids[0]
    prompts.append(ids)

  report = {
    "steps": args.steps, "device": args.device, "attention_cores": args.attention_cores,
    "prompts": list(args.prompt or DEFAULT_PROMPTS),
    "weight_bytes_per_token": WEIGHT_BYTES_PER_TOKEN,
    "optimized_source_sha256": hashlib.sha256(Path(llama3.__file__).read_bytes()).hexdigest(),
  }
  if args.reference:
    report["reference_source_sha256"] = hashlib.sha256(args.reference.read_bytes()).hexdigest()
  if args.reference:
    print("Reference", flush=True)
    report["reference"] = benchmark(load_reference(args.reference), prompts, args)
  print("Optimized", flush=True)
  report["optimized"] = benchmark(llama3, prompts, args)
  if args.reference:
    report["exact_match"] = all(
      before["generated_tokens"] == after["generated_tokens"] and
      before["logit_sha256"] == after["logit_sha256"]
      for before, after in zip(report["reference"], report["optimized"])
    )
    print(f"Token IDs and sampled BF16 logits match exactly: {report['exact_match']}")
  if args.output:
    args.output.write_text(json.dumps(report, indent=2) + "\n")
  if args.reference and not report["exact_match"]:
    raise RuntimeError("decode output differs from the reference")


if __name__ == "__main__":
  main()
