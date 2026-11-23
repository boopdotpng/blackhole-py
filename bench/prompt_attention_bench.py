"""Times a causal prompt-attention kernel on Nanbeige shapes (56 query heads, 8 KV heads, head_dim 128) and checks it
against numpy. Kernel interface: examples/shared/prompt_attention.ttrv (q_tiles, key_cache, value_cache, context,
start_pos; panel tile layouts as prompt_rope.ttrv writes them).

  PYTHONPATH=. python3 bench/prompt_attention_bench.py [kernel.ttrv] [--device 0] [--panels 10] [--start 0 3200]
"""
import argparse, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ttrv import Device

ap = argparse.ArgumentParser()
ap.add_argument("kernel", nargs="?", default="examples/shared/prompt_attention.ttrv")
ap.add_argument("--device", type=int, default=0)
ap.add_argument("--panels", type=int, default=10)
ap.add_argument("--start", type=int, nargs="+", default=[0, 3200])
ap.add_argument("--workers", type=int, default=139)
ap.add_argument("--check", action="store_true", help="compare against numpy (slow on the host at long contexts)")
a = ap.parse_args()

KV, G, D, CAP = 8, 7, 128, 4096
HT, TQ = D // 32, a.panels
def bf16(x): u = np.asarray(x, np.float32).view(np.uint32); return ((u + 0x7FFF + (u >> 16 & 1)) >> 16).astype(np.uint16)
def f32(u): return (np.asarray(u, np.uint32) << 16).view(np.float32)
def tiles(m):  # [32k, 32n] -> face-layout tiles, row-major tile order
  r, c = m.shape
  t = m.reshape(r // 32, 2, 16, c // 32, 2, 16).transpose(0, 3, 1, 4, 2, 5)
  return t.reshape(-1)
def untile(v, r, c):
  return v.reshape(r // 32, c // 32, 2, 2, 16, 16).transpose(0, 2, 4, 1, 3, 5).reshape(r, c)

rng = np.random.default_rng(0)
dev = Device(a.device)
try:
  k = dev.kernel(Path(a.kernel), HEAD_TILES=HT, KV_HEADS=KV, GROUP=G, MAX_TOKENS=CAP, TILES_Q=TQ, WORKERS=a.workers)
  q = rng.standard_normal((KV * G, TQ * 32, D)).astype(np.float32)
  keys = rng.standard_normal((KV, CAP, D)).astype(np.float32)
  vals = rng.standard_normal((KV, CAP, D)).astype(np.float32)
  # q_tiles: per head, per panel, HEAD_TILES tiles; caches: per KV head, 32-position blocks of HEAD_TILES tiles
  qt = np.concatenate([tiles(q[h, j * 32:(j + 1) * 32]) for h in range(KV * G) for j in range(TQ)])
  kc = np.concatenate([tiles(keys[g, b * 32:(b + 1) * 32]) for g in range(KV) for b in range(CAP // 32)])
  vc = np.concatenate([tiles(vals[g, b * 32:(b + 1) * 32]) for g in range(KV) for b in range(CAP // 32)])
  qb, kb, vb = dev.array(bf16(qt), "bf16"), dev.array(bf16(kc), "bf16"), dev.array(bf16(vc), "bf16")
  ctx = dev.zeros(TQ * 32 * KV * G * D, "bf16")
  for start in a.start:
    run = lambda: k(q_tiles=qb, key_cache=kb, value_cache=vb, context=ctx, start_pos=start).wait(60)
    run()
    t0 = time.perf_counter()
    for _ in range(5): run()
    dt = (time.perf_counter() - t0) / 5
    blocks = sum(start // 32 + j + 1 for j in range(TQ)) * KV * G
    flop = 4 * D * 32 * 32 * blocks
    line = (f"start {start:5d}, {TQ} panels: {dt * 1e3:7.3f} ms  {flop / dt / 1e12:6.1f} TFLOP/s  "
            f"{dt * 1.35e9 * a.workers / blocks:6.0f} core-cycles per (head, 32x32 block)")
    if a.check:
      out = f32(ctx.numpy())   # [panel][head][HEAD_TILES tiles]
      err = 0.0
      Q, K_, V_ = f32(bf16(q)), f32(bf16(keys)), f32(bf16(vals))
      for h in range(0, KV * G, 9):
        for j in range(TQ):
          rows = start + j * 32 + np.arange(32)
          s = Q[h, j * 32:(j + 1) * 32] @ K_[h // G, :rows[-1] + 1].T / np.sqrt(D)
          s[np.arange(len(rows))[:, None] < np.arange(rows[-1] + 1)[None, :] - rows[:, None] + np.arange(len(rows))[:, None]] += 0
          s = np.where(np.arange(rows[-1] + 1)[None, :] > rows[:, None], -np.inf, s)
          p = np.exp(s - s.max(1, keepdims=True)); ref = (p / p.sum(1, keepdims=True)) @ V_[h // G, :rows[-1] + 1]
          at = (j * KV * G + h) * HT * 1024
          got = untile(out[at:at + HT * 1024], 32, D)
          err = max(err, float(np.abs(got - ref).max()))
      line += f"  max |err| {err:.4f}"
    print(line)
finally:
  dev.close()
