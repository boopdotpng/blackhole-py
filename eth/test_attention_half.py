# Nanbeige GQA attention (head_dim 128, GROUP 7): does KV_HEADS=4 on the first half of q/k/v give the first half of
# the KV_HEADS=8 context? Several positions of random q/k/v so the cache holds more than one row.
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from helpers import rope
from ttrv import Device
d = Device(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
A = ROOT / "examples/llama3/attention.ttrv"
HD, G, CAP, POS = 128, 7, 64, 40
cfg = {"rope_theta": 1e6}
cos, sin = (d.array(t, "bf16") for t in rope(cfg, HD, CAP))
rng = np.random.default_rng(0)
def bf(x): return d.array(x.astype(np.float32), "bf16")
runs = {}
for kv in (8, 4):
  k = d.kernel(A, HEAD_TILES=HD // 32, KV_HEADS=kv, GROUP=G, PACK_CONTEXT=1, MAX_TOKENS=CAP)
  kc, vc = d.zeros(CAP * kv * HD, "bf16"), d.zeros(CAP * kv * HD, "bf16")
  ctx = d.zeros(kv * G * HD, "bf16")
  runs[kv] = (k, kc, vc, ctx)
outs = {8: [], 4: []}
for p in range(POS):
  q, kk, vv = rng.standard_normal(8 * G * HD), rng.standard_normal(8 * HD), rng.standard_normal(8 * HD)
  for kv, (k, kc, vc, ctx) in runs.items():
    k(q_in=bf(q[:kv * G * HD]), k_in=bf(kk[:kv * HD]), v_in=bf(vv[:kv * HD]), cos=cos, sin=sin, key_cache=kc,
      value_cache=vc, context=ctx, start_pos=p)
    outs[kv].append(ctx.numpy().copy())
bad = [p for p in range(POS) if not np.array_equal(outs[8][p][:4 * G * HD], outs[4][p])]
print("all positions match" if not bad else f"mismatch at positions {bad[:10]}")
if bad:
  a, b = outs[8][bad[0]][:4 * G * HD], outs[4][bad[0]]
  diff = np.nonzero(a != b)[0]; print(len(diff), "elements differ, first", diff[:10])
