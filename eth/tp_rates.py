"""Warm batch-one decode on two p150a cards (tensor parallel over TT-link), measured like sims/probes/model_rates.py:
a fixed 320-token prefix, then the 32 streamed tokens after the first output; median of three warm runs. The prefix
runs one token at a time through the decode graph (two-card chunked prefill is not implemented), so only decode is
reported.      python eth/tp_rates.py 8b-bfp8"""
import argparse, sys
from pathlib import Path
from statistics import median
from time import perf_counter
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from ttrv import Device
from tp import Link

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("model", choices=("1b", "8b-bf16", "8b-bfp8", "nanbeige"))
a = ap.parse_args()
prefix, steps = 320, 32
ids = np.random.default_rng(42).integers(100, 32000, size=prefix + 1).tolist()
devs = [Device(0), Device(1)]
link = Link(devs)
weights = HERE.parent / "weights"
if a.model in ("1b", "8b-bf16"):
  from llama3_tp import Llama3TP
  model = Llama3TP(weights / f"llama3-{a.model}", devs, link)
else:
  from nanbeige_tp import NanbeigeTP, DEFAULT
  ckpt = DEFAULT if a.model == "nanbeige" else weights / "llama3-8b-bfp8" / "model.safetensors"
  model = NanbeigeTP(ckpt, devs, link, max_tokens=prefix + steps + 1)
model.eos = set()
decode = []
for _ in range(4):
  stream = model.generate(ids, steps + 1)
  next(stream)
  start = perf_counter()
  count = sum(1 for _ in stream)
  decode.append(perf_counter() - start)
  if count != steps: raise RuntimeError(f"expected {steps} decode steps, received {count}")
print(f"{a.model}  2x p150a decode {steps / median(decode[1:]):.1f} tok/s")
link.close()
