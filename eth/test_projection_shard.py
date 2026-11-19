# Column-parallel packed projections: does card 0's half (first half of each fused part's N) give the first half of
# each full output? Real Nanbeige layer-0 q/k/v and gate/up weights, random activations.
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from helpers import safe_load
from ttrv import Device
d = Device(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
P = ROOT / "examples/nanbeige/projection.ttrv"
T = safe_load(ROOT.parent / "weights/nanbeige4.3-33b/mixed_bfp4mlp_bfp8attn/model.safetensors")
rng = np.random.default_rng(0)
def upload(tiles, bits, group):
  n = sum(m.shape[1] for m in tiles) * 32
  row = n // 32 * tiles[0].shape[2]
  kt = tiles[0].shape[0]
  buf = d.empty(kt * row, f"bfp{bits}", tiles_per_page=group)
  for first in range(0, kt, group):
    off = buf.addr + first * row
    for m in tiles:
      s = np.ascontiguousarray(m[first:first + group].swapaxes(0, 1)); d.dev.allocator._copyin(off, s); off += s.nbytes
  return buf, n
def run(names, bits, half):
  parts = [T[f"model.layers.0.{n}.weight"].numpy() for n in names]
  if half: parts = [np.ascontiguousarray(m[:, :m.shape[1] // 2]) for m in parts]
  widths = [m.shape[1] * 32 for m in parts]
  group = 16 if bits == 4 else 8
  buf, n = upload(parts, bits, group)
  second, third = (widths + [0, 0])[1:3]
  k = d.kernel(P, K=7168, N=n, BITS=bits, GROUP=group, SECOND=second, THIRD=third, WORKERS=min(n // 32, 96 if second else 112))
  outs = [d.zeros(w, "bf16") for w in widths]
  args = dict(x=x, weights=buf, output=outs[0])
  if second: args["output2"] = outs[1]
  if third: args["output3"] = outs[2]
  k(**args)
  return [o.numpy() for o in outs]
x = d.array(rng.standard_normal(7168).astype(np.float32), "bf16")
for names, bits in ((["self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj"], 8), (["mlp.gate_proj", "mlp.up_proj"], 4)):
  full, half = run(names, bits, False), run(names, bits, True)
  for nm, f, h in zip(names, full, half):
    ok = np.array_equal(f[:len(h)], h)
    print(f"{nm}: {'match' if ok else f'DIFFER {np.count_nonzero(f[:len(h)] != h)} of {len(h)}, first {np.nonzero(f[:len(h)] != h)[0][:6]}'}")
