"""Measure warm, end-to-end KV-cache construction at the same context for each chunk size."""
import argparse
from pathlib import Path
from statistics import median
import sys
from time import perf_counter

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from examples.llama3 import Llama3, ROOT, MAX_TOKENS
from examples.nanbeige import Nanbeige, DEFAULT
from examples.prefill import MAX_CHUNK, DEFAULT_CHUNK
from examples.qwen38 import Qwen38, DEFAULT as QWEN_CHECKPOINT, METADATA as QWEN_METADATA
from examples.qwen38_prefill import CHUNK as QWEN_CHUNK
from ttrv import Device


def main():
  ap = argparse.ArgumentParser(description=__doc__)
  ap.add_argument("model", choices=("nanbeige", "qwen38", "1b", "8b-bf16", "8b-fp8"))
  ap.add_argument("--device", type=int, default=0)
  ap.add_argument("--length", type=int, default=128)
  ap.add_argument("--chunks", nargs="+", type=int)
  ap.add_argument("--reps", type=int, default=3)
  args = ap.parse_args()
  limit = QWEN_CHUNK if args.model == "qwen38" else MAX_CHUNK
  chunks = args.chunks or [QWEN_CHUNK if args.model == "qwen38" else DEFAULT_CHUNK]
  if args.reps < 1 or args.length < 1 or any(not 1 <= size <= limit for size in chunks):
    ap.error("expected positive length and repetitions and a supported chunk size")
  if args.model in ("1b", "8b-bf16", "8b-fp8") and args.length > MAX_TOKENS: ap.error("prompt exceeds Llama context")
  dev = Device(args.device)
  try:
    if args.model == "qwen38":
      model = Qwen38(QWEN_CHECKPOINT, QWEN_METADATA, dev, args.length)
    elif args.model == "nanbeige":
      model = Nanbeige(DEFAULT, dev, args.length)
    else:
      model = Llama3(ROOT / "weights" / ("llama3-" + args.model), dev)
    history = np.zeros(model.history.shape, dtype=np.uint32)
    history[:args.length] = np.random.default_rng(42).integers(100, 32000, size=args.length)
    model.history.copy_from(history)
    prompt = model.make_prompt()
    for chunk in chunks:
      prompt.run(args.length, chunk)
      samples = []
      for _ in range(args.reps):
        start = perf_counter()
        prompt.run(args.length, chunk)
        samples.append(perf_counter() - start)
      print(f"{args.model}  {args.length} prompt tokens  chunk {chunk}  "
            f"{median(samples):.4f} s  {args.length / median(samples):.2f} tok/s", flush=True)
  finally:
    dev.close()


if __name__ == "__main__":
  main()
