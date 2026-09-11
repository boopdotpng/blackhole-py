"""Benchmark fixed-length decode and optionally compare an original runtime.

Startup, prompt ingestion, and diagnostic logit reads are excluded from timing.
Generation deliberately continues through EOS to keep the workload comparable.
"""

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import statistics
import time

import numpy as np

from examples import llama3_8b as llama3


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


def benchmark(module, prompts, args, *, logit_samples=None, teacher_tokens=None):
  runtime = module.Llama3Decode(args.safetensor, args.device)
  results = []
  weights = [runtime.lm_weight] + [w for layer in runtime.layers for w in layer["weights"].values() if len(w.shape) == 2]
  weight_bytes = sum(math.prod(w.shape) * w.dtype.itemsize for w in weights)
  try:
    for prompt_ids in prompts:
      if len(prompt_ids) + args.steps > module.ROPE_CACHE_TOKENS:
        raise ValueError("prompt and generation exceed the KV cache")
      continuation = [] if teacher_tokens is None else teacher_tokens[len(results)]
      runtime.load_tokens([*prompt_ids, *continuation])
      for position in range(len(prompt_ids) - 1):
        runtime.decode(position, logits=False, append=False)
      samples, tokens, logits = [], [], {}
      for step in range(args.steps):
        position = len(prompt_ids) - 1 + step
        started = time.perf_counter_ns()
        token, _ = runtime.decode(position, append=teacher_tokens is None)
        samples.append((time.perf_counter_ns() - started) / 1e3)
        tokens.append(token)
        # Check both sides of attention's 32-token block boundary, as well
        # as the first and final generated token. Readbacks are not timed.
        if step in (0, args.steps - 1) or position % 32 in (0, 31):
          data = runtime.device.read(runtime.logits)
          logits[str(position)] = hashlib.sha256(data).hexdigest()
          if logit_samples is not None:
            logit_samples[len(results), position] = runtime.logits.to_numpy(data)
      rate = len(samples) * 1e6 / sum(samples)
      results.append({
        "weight_bytes_per_token": weight_bytes,
        "startup": runtime.profile,
        "prompt_tokens": len(prompt_ids),
        "generated_tokens": tokens,
        "logit_sha256": logits,
        "tok_s": rate,
        "median_us": statistics.median(samples),
        "decode_us": samples,
        "weight_GB_s": rate * weight_bytes / 1e9,
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
  parser.add_argument("--steps", type=int, default=128)
  parser.add_argument("--prompt", action="append")
  parser.add_argument("--reference", type=Path,
                      help="original examples/llama3_8b.py to compare on the same card")
  parser.add_argument("--output", type=Path, help="write detailed JSON results")
  parser.add_argument("--logit-rms-tolerance", type=float, default=0.0,
                      help="allow relative RMS logit error while requiring identical tokens; default requires exact hashes")
  parser.add_argument("--teacher-force-reference", action="store_true",
                      help="feed reference tokens to both models so numerical comparisons use identical histories")
  args = parser.parse_args()
  if args.steps < 1:
    parser.error("--steps must be positive")
  if not np.isfinite(args.logit_rms_tolerance) or args.logit_rms_tolerance < 0:
    parser.error("--logit-rms-tolerance must be finite and non-negative")
  if args.logit_rms_tolerance and not args.reference:
    parser.error("--logit-rms-tolerance requires --reference")
  if args.teacher_force_reference and not (args.reference and args.logit_rms_tolerance):
    parser.error("--teacher-force-reference requires --reference and --logit-rms-tolerance")

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
    "steps": args.steps, "device": args.device,
    "prompts": list(args.prompt or DEFAULT_PROMPTS),
    "optimized_source_sha256": hashlib.sha256(Path(llama3.__file__).read_bytes()).hexdigest(),
  }
  if args.reference:
    report["reference_source_sha256"] = hashlib.sha256(args.reference.read_bytes()).hexdigest()
  reference_samples = {} if args.logit_rms_tolerance else None
  optimized_samples = {} if args.logit_rms_tolerance else None
  if args.reference:
    print("Reference", flush=True)
    report["reference"] = benchmark(
      load_reference(args.reference), prompts, args, logit_samples=reference_samples,
    )
  print("Optimized", flush=True)
  teacher_tokens = (
    [entry["generated_tokens"] for entry in report["reference"]]
    if args.teacher_force_reference else None
  )
  report["teacher_forced"] = args.teacher_force_reference
  report["optimized"] = benchmark(
    llama3, prompts, args, logit_samples=optimized_samples, teacher_tokens=teacher_tokens,
  )
  if args.reference:
    report["exact_match"] = all(
      before["generated_tokens"] == after["generated_tokens"] and
      before["logit_sha256"] == after["logit_sha256"]
      for before, after in zip(report["reference"], report["optimized"])
    )
    print(f"Token IDs and sampled BF16 logits match exactly: {report['exact_match']}")
    report["accepted"] = report["exact_match"]
    if args.logit_rms_tolerance:
      report["tokens_match"] = all(
        before["generated_tokens"] == after["generated_tokens"]
        for before, after in zip(report["reference"], report["optimized"])
      )
      errors = []
      for key, expected in reference_samples.items():
        actual = optimized_samples[key]
        delta = actual.astype(np.float64) - expected
        errors.append({
          "prompt": key[0], "position": key[1],
          "relative_rms": float(np.linalg.norm(delta) / max(np.linalg.norm(expected.astype(np.float64)), 1e-30)),
          "max_absolute": float(np.max(np.abs(delta))),
          "cosine_similarity": float(np.dot(actual.ravel().astype(np.float64), expected.ravel().astype(np.float64)) /
                                     max(np.linalg.norm(actual.astype(np.float64)) * np.linalg.norm(expected.astype(np.float64)), 1e-30)),
        })
      report["logit_errors"] = errors
      report["logit_rms_tolerance"] = args.logit_rms_tolerance
      report["top1_agreement"] = float(np.mean([
        left == right
        for before, after in zip(report["reference"], report["optimized"])
        for left, right in zip(before["generated_tokens"], after["generated_tokens"])
      ]))
      report["accepted"] = (args.teacher_force_reference or report["tokens_match"]) and all(
        np.isfinite(error["relative_rms"]) and error["relative_rms"] <= args.logit_rms_tolerance
        for error in errors
      )
      print(f"Tokens match: {report['tokens_match']}; max relative RMS logit error: "
            f"{max(e['relative_rms'] for e in errors):.6g}; accepted: {report['accepted']}")
  if args.output:
    args.output.write_text(json.dumps(report, indent=2) + "\n")
  if args.reference and not report["accepted"]:
    raise RuntimeError("decode output differs from the reference")


if __name__ == "__main__":
  main()
