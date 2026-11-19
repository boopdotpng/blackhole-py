#!/usr/bin/env python3
"""Per-launch overhead of the real runtime (ops_blackhole + fw/dispatch.c), the way llama runs: a graph of EXECs of
do-nothing kernels, with the dispatcher's own timestamps around every EXEC.

  python3 sims/probes/launch.py --device 1 --output sims/results/<date>-launch-card1.jsonl

Varies the core count (llama's first N cores) and the image size per role (all five roles, a NOP sled ending in the
return jump). Per EXEC: span = dispatcher timestamp at EXEC start -> all cores done; period = start to next start.
Uses its own process and the normal device boot (all worker RISCs reset, CQ and DMA loops started); never resets
the card. Gated on the same smi.py health sample as run.py.
"""
import argparse, json, sys, time
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))
import numpy as np  # noqa: E402
import fw  # noqa: E402
from run import card_ok  # noqa: E402

LLAMA = [(x, y) for y in range(2, 10) for x in (1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13)]
REPS, RUNS = 32, 5


def image(role, size):
  n = max(size // 4 - 1, 0)
  return b"\x13\x00\x00\x00" * n + fw.ret(role)  # addi x0, x0, 0 ... then jalr back to the firmware


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument('--device', type=int, required=True)
  ap.add_argument('--output', required=True)
  a = ap.parse_args()
  good, reason = card_ok(a.device)
  print(f'card {a.device}: {reason}')
  if not good: return 2
  from ops_blackhole import BlackholeDevice, BlackholeComputeQueue, BlackholeGraph, blackhole_build_program
  dev = BlackholeDevice(f'BLACKHOLE:{a.device}')
  try:
    cases = [(n, s) for n in (1, 8, 32, 88) for s in (0, 1024, 4096)] + [(len(dev.workers), 4096)]
    at = dev.alloc_host(16 * (2 * REPS + 2))
    ts = np.ndarray((2 * (2 * REPS + 2),), np.uint64, dev.sysmem.mem, at)
    base = dev.sysmem.noc_addr + at
    for n, size in cases:
      cores = LLAMA[:n] if n <= len(LLAMA) else dev.workers[:n]
      roles = {r: image(r, min(size, fw.CODE_SIZE[r])) for r in fw.ROLES} if size else {}
      prg = blackhole_build_program(dev, {c: roles for c in cores})
      q = BlackholeComputeQueue().timestamp(base)
      for i in range(REPS): q.exec(prg, 0, base + 16 * (1 + 2 * i))
      q.timestamp(base + 16 * (2 * REPS + 1))
      graph = BlackholeGraph(dev, q)
      spans, periods, totals = [], [], []
      for _ in range(RUNS):
        graph(timeout=5.0)
        t = ts.astype(np.int64)
        start = [int(t[2 * (1 + 2 * i) + 1]) for i in range(REPS)]   # slot 1+2i, word 1 (dispatch writes +8)
        end = [int(t[2 * (2 + 2 * i) + 1]) for i in range(REPS)]     # slot 2+2i, word 1 (+24)
        spans += [e - s for s, e in zip(start, end)][2:]
        periods += [b - s for s, b in zip(start, start[1:])][2:]
        totals.append(int(t[2 * (2 * REPS + 1) + 1] - t[1]) / REPS)
      rec = dict(id=f'launch-n{n}-img{size}', cores=n, image_bytes_per_role=size, roles=len(roles),
                 span_median=median(spans), span_min=min(spans), span_max=max(spans),
                 period_median=median(periods), period_min=min(periods), period_max=max(periods),
                 per_exec_total=median(totals), card=a.device, time=time.time())
      print(json.dumps({k: v for k, v in rec.items() if k not in ('card', 'time')}), flush=True)
      with open(a.output, 'a') as f: f.write(json.dumps(rec) + '\n')
  finally:
    dev.close()
  return 0


if __name__ == '__main__':
  sys.exit(main())
