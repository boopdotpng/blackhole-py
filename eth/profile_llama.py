# Per-kernel time of one Llama decode step, single card vs two-card TP. Usage: profile_llama.py MODEL [POS]
import sys
from collections import Counter
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import fw
from ops_blackhole import BlackholeComputeQueue, BlackholeGraph
from ttrv import Device

def instrument(dev, capture):
  stamps = dev.zeros((len(capture.launches), 4), "u64", host=True)
  q = BlackholeComputeQueue()
  names, seen = [], {}
  KIND = {"step": "pick", "winner": "argmax", "history": "embedding", "q_in": "attention", "partial": "allreduce", "logits": "argmax", "gamma": "gate"}
  for i, (kernel, _, _) in enumerate(capture.launches):
    q.exec(kernel.program, capture.graph.base + i * fw.PARAM_SIZE, profile=stamps.addr + i * 32)
    ps = list(kernel.params)
    name = "lm" if "wlm" in ps else "qkv" if "wq" in ps else "allreduce" if "partial" in ps else next((v for k, v in KIND.items() if k in ps), None)
    if name is None:  # o and down share a kernel source; tell them apart by order of first use
      if id(kernel) not in seen: seen[id(kernel)] = ("o", "down")[len(seen)]
      name = seen[id(kernel)]
    names.append(name)
  capture.graph.graph = BlackholeGraph(dev.dev, q)
  def measure():
    t = stamps.numpy().astype(np.int64)
    us = lambda c: c / fw.AICLK_MHZ
    per = Counter()
    for n, (a, b) in zip(names, zip(t[:, 1], t[:, 3])): per[n] += us(b - a)
    gaps = us(np.sum(t[1:, 1] - t[:-1, 3]))
    return per, gaps, us(t[-1, 3] - t[0, 1]), len(names)
  return measure

def report(title, measure):
  per, gaps, total, n = measure()
  print(f"{title}: {n} launches, {total / 1000:.2f} ms ({gaps / 1000:.2f} ms between launches)")
  for k, v in per.most_common(): print(f"  {k:12} {v / 1000:7.2f} ms")

if __name__ == "__main__":
  model, pos = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 32
  path = HERE.parent / "weights" / f"llama3-{model}"
  import examples.llama3 as single
  from llama3_tp import Llama3TP
  from tp import Link
  devs = [Device(0), Device(1)]
  m = single.Llama3(path, devs[0])
  meas = instrument(devs[0], m.step)
  for _ in range(3): m.step(pos=pos, write_token=0).wait()
  report(f"{model} single card, pos {pos}", meas)
  del m
  link = Link(devs)
  t = Llama3TP(path, devs, link)
  ms = [instrument(d, g) for d, g in zip(devs, t.steps)]
  for _ in range(3):
    for e in t.run(pos, 0): e.wait()
  for r in range(2): report(f"{model} TP card {r}, pos {pos}", ms[r])
  link.close()
