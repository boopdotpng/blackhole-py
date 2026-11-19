"""DRAM read bandwidth over one decode token, aligned with the dispatcher's launch windows."""
import argparse, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import fw
from llama3 import Llama3, ChatTokenizer, MODELS
from observer import Observer, dram_read_targets, bandwidth, clean

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="1b", choices=list(MODELS))
ap.add_argument("--period", type=float, default=1.0, help="sample period, us")
ap.add_argument("--core", default="15,2")
a = ap.parse_args()
m = Llama3(a.model, 0, profile=True)
try:
  ids = ChatTokenizer(m.checkpoint).chat([{"role": "user", "content": "Write a story about a robot learning to paint."}])
  m.generate(ids, 2)
  obs = Observer(m.dev, tuple(map(int, a.core.split(","))), dram_read_targets(), int(a.period * fw.AICLK_MHZ))
  obs.start()
  m.generate(ids, 1, start=len(ids) - 1)
  t, v = obs.stop()
  disp = m.ts[(m.runs - 1) % 2, 1:2 * m.nts:2].astype(np.int64)  # the last run: position len(ids) - 1
  v, bad = clean(v)
  print(f"rejected {bad} of {v.size} counter reads as misreads")
  tm, bw = bandwidth(t, v)
  span = (t[-1] - t[0]) / fw.AICLK_MHZ
  print(f"{len(t)} samples over {span:.0f} us, mean period {span / max(1, len(t) - 1):.2f} us")
  L = len(m.launches); us = 1 / fw.AICLK_MHZ
  g0, g1 = int(disp[0]), int(disp[-1])
  inside = (tm >= g0) & (tm <= g1)
  peak = 514.6
  print(f"token graph {(g1 - g0) * us:.1f} us; mean DRAM read BW inside it {bw[inside].mean():.1f} GB/s ({bw[inside].mean() / peak:.0%} of pin rate)")
  rows = {}
  for k, (name, _) in enumerate(m.launches):
    w0, w1 = int(disp[1 + 2 * k]), int(disp[2 + 2 * k])
    sel = (tm >= w0) & (tm < w1)
    gb = bw[sel].mean() * (w1 - w0) * us * 1e-6 if sel.any() else 0
    ideal = gb / peak * 1e6  # us to move these bytes at pin rate
    r = rows.setdefault(name, [0, 0.0, 0.0, 0.0, []])
    r[0] += 1; r[1] += (w1 - w0) * us; r[2] += gb; r[3] += ideal
    if sel.sum() > 6: r[4].append(bw[sel])
  print(f"\n{'program':<10}{'n':>4}{'us total':>10}{'GB read':>9}{'avg GB/s':>10}{'us @peak':>10}{'lost us':>9}   BW profile over the launch (10 bins, GB/s)")
  for name, (n, tot, gb, ideal, prof) in rows.items():
    bins = ""
    if prof:
      L2 = min(len(p) for p in prof)
      arr = np.array([np.interp(np.linspace(0, len(p) - 1, 10), np.arange(len(p)), p) for p in prof]).mean(0)
      bins = " ".join(f"{x:4.0f}" for x in arr)
    print(f"{name:<10}{n:>4}{tot:>10.1f}{gb:>9.3f}{gb / (tot * 1e-6) if tot else 0:>10.1f}{ideal:>10.1f}{tot - ideal:>9.1f}   {bins}")
  tot_lost = sum(r[1] - r[3] for r in rows.values())
  print(f"\nDRAM-idle time per token: {tot_lost:.0f} us of {(g1 - g0) * us:.0f} us ({tot_lost / ((g1 - g0) * us):.0%}); "
        f"gaps between launches + graph edges: {(g1 - g0) * us - sum(r[1] for r in rows.values()):.0f} us")
  np.savez(HERE / f"dram_timeline_{a.model}.npz", t=t, v=v, disp=disp)
finally:
  m.close()
