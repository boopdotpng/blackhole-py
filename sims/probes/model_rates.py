"""Measure warm batch-one prefill and streaming decode at a fixed context."""
import argparse
from pathlib import Path
from statistics import median
import sys
from time import perf_counter

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from examples.llama3 import ROOT, load
from examples.nanbeige import DEFAULT, Nanbeige
from examples.qwen38 import DEFAULT as QWEN_CHECKPOINT, METADATA as QWEN_METADATA, Qwen38
from ttrv import Device


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("model", choices=("1b", "8b-bf16", "8b-bfp8", "nanbeige", "qwen38"))
  parser.add_argument("--device", type=int, default=0)
  args = parser.parse_args()
  prefix, steps = 320, 32
  ids = np.random.default_rng(42).integers(100, 32000, size=prefix + 1).tolist()
  dev = Device(args.device)
  try:
    # Disable early stopping so each model executes the same number of steps.
    if args.model == "nanbeige":
      model = Nanbeige(DEFAULT, dev, prefix + steps + 1)
      model.eos = set()
    elif args.model == "qwen38":
      model = Qwen38(QWEN_CHECKPOINT, QWEN_METADATA, dev, prefix + steps + 1)
      model.eos = set()
    else:
      model = load(ROOT / "weights" / ("llama3-" + args.model), dev)
      model.eos = set()

    prefill, decode = [], []
    for _ in range(4):
      stream = model.generate(ids, steps + 1)
      next(stream)
      start = perf_counter()
      count = sum(1 for _ in stream)
      decode.append(perf_counter() - start)
      prefill.append(model.prompt.elapsed)
      if count != steps:
        raise RuntimeError(f"expected {steps} decode steps, received {count}")
    print(f"{args.model}  prefill {prefix / median(prefill[1:]):,.0f} tok/s  "
          f"decode {steps / median(decode[1:]):.1f} tok/s")
  finally:
    dev.close()


if __name__ == "__main__":
  main()
