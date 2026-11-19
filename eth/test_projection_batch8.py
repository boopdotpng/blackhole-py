# Does projection.ttrv give the same result with K = 344 tiles (BATCH = GROUP = 8) as with the same weights
# zero-padded to 352 tiles (BATCH = GROUP = 16)? BFP4, real Nanbeige down_proj tiles.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from ttrv import Device
KERNEL = Path(__file__).resolve().parents[1] / "examples/nanbeige/projection.ttrv"
dev = Device(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
rng = np.random.default_rng(1)
KT, NT, PAD = 344, 224, 352
def upload(m, group):
  kt, nt, b = m.shape
  buf = dev.empty(kt * nt * b, "bfp4", tiles_per_page=group)
  row = nt * b
  for first in range(0, kt, group):
    dev.dev.allocator._copyin(buf.addr + first * row, np.ascontiguousarray(m[first:first + group].swapaxes(0, 1)))
  return buf
from helpers import safe_load
real = safe_load(Path(__file__).resolve().parents[2] / "weights/nanbeige4.3-33b/mixed_bfp4mlp_bfp8attn/model.safetensors")
real = real["model.layers.0.mlp.down_proj.weight"].numpy()   # [688, 224, 576]: card 0 holds K tiles [0, 344)
NT = real.shape[1]
w = np.zeros((PAD, NT, 576), np.uint8)
w[:KT] = real[:KT]          # padding tiles: all-zero bytes, so zero exponents and mantissas
x = rng.standard_normal(PAD * 32).astype(np.float32); x[KT * 32:] = 0
xb = dev.array(x, "bf16")
outs = []
for kt, batch in ((KT, 8), (PAD, 16)):
  k = dev.kernel(KERNEL, K=kt * 32, N=NT * 32, BITS=4, GROUP=batch, BATCH=batch, WORKERS=112)
  y = dev.zeros(NT * 32, "bf16")
  k(x=xb, weights=upload(np.ascontiguousarray(w[:kt]), batch), output=y)
  outs.append(y.numpy())
a, b = outs
print("equal" if np.array_equal(a, b) else f"DIFFER: {np.count_nonzero(a != b)} of {a.size}", a[:6], b[:6])
