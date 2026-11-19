# Per-kernel time of one packed-BFP decode step (+ readout), single card vs two-card TP.
# Usage: profile_nanbeige.py CHECKPOINT [POS]
import sys
from collections import Counter
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import fw
from ops_blackhole import BlackholeComputeQueue, BlackholeGraph
from ttrv import Device

def instrument(dev, capture, names_of):
  stamps = dev.zeros((len(capture.launches), 4), "u64", host=True)
  q = BlackholeComputeQueue()
  names = []
  for i, (kernel, _, _) in enumerate(capture.launches):
    q.exec(kernel.program, capture.graph.base + i * fw.PARAM_SIZE, profile=stamps.addr + i * 32)
    names.append(names_of(kernel))
  capture.graph.graph = BlackholeGraph(dev.dev, q)
  def measure():
    t = stamps.numpy().astype(np.int64)
    per = Counter()
    for n, a, b in zip(names, t[:, 1], t[:, 3]): per[n] += (b - a) / fw.AICLK_MHZ
    return per, np.sum(t[1:, 1] - t[:-1, 3]) / fw.AICLK_MHZ, (t[-1, 3] - t[0, 1]) / fw.AICLK_MHZ, len(names)
  return measure

def namer():
  seen = {}
  def name(k):
    ps = list(k.params)
    if "weights" in ps and "x" in ps:
      base = "proj"
    elif "other" in ps: base = "vector"
    elif "partial" in ps: return "allreduce"
    elif "step" in ps: return "pick"
    elif "q_in" in ps: return "attention"
    elif "logits" in ps: return "argmax"
    else: return "embedding"
    if id(k) not in seen: seen[id(k)] = f"{base}{sum(v.startswith(base) for v in seen.values())}"
    return seen[id(k)]
  return name

def report(title, measures):
  tot, gaps, n, per = 0, 0, 0, Counter()
  for m in measures:
    p, g, t, c = m(); per.update(p); gaps += g; tot += t; n += c
  print(f"{title}: {n} launches, {tot / 1000:.2f} ms ({gaps / 1000:.2f} ms between launches)")
  for k, v in per.most_common(): print(f"  {k:12} {v / 1000:7.2f} ms")

if __name__ == "__main__":
  ckpt, pos = Path(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 32
  devs = [Device(0), Device(1)]
  if "--tp-only" not in sys.argv:
    from examples.nanbeige import Nanbeige
    m = Nanbeige(ckpt, devs[0], max_tokens=128)
    nm = namer()
    ms = [instrument(devs[0], m.step, nm), instrument(devs[0], m.readout, nm)]
    for _ in range(3): m.step(pos=pos).wait(); m.readout(pos=pos, write_token=0).wait()
    report("single card", ms)
    del m
  from nanbeige_tp import NanbeigeTP
  from tp import Link
  link = Link(devs)
  t = NanbeigeTP(ckpt, devs, link, max_tokens=128)
  ms = []
  for r in range(2):
    nm = namer()
    ms.append([instrument(devs[r], t.steps[r], nm), instrument(devs[r], t.readouts[r], nm)])
  for _ in range(3):
    t.step(pos); [e.wait(30) for e in t.readout(pos, 0)]
  for r in range(2): report(f"TP card {r}", ms[r])
  link.close()
