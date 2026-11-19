# Row-parallel (K-split) projection error vs a float64 reference, against the single-card projection's error.
# Real Nanbeige layer-0 o_proj (BFP8) and down_proj (BFP4); activations in the projection's face-packed layout.
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT.parent / "weights/nanbeige4.3-33b/scripts"))
import numpy as np, torch
from bfp import unpack_tiles
from helpers import safe_load
from ttrv import Device
d = Device(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
P = ROOT / "examples/nanbeige/projection.ttrv"
T = safe_load(ROOT.parent / "weights/nanbeige4.3-33b/mixed_bfp4mlp_bfp8attn/model.safetensors")
rng = np.random.default_rng(0)
f32 = lambda b: (b.astype(np.uint32) << 16).view(np.float32)
def bf16(x):
  u = np.asarray(x, np.float32).view(np.uint32).astype(np.uint64); return ((u + 0x7FFF + (u >> 16 & 1)) >> 16).astype(np.uint16)
def face(v):  # logical -> face-packed activation layout (whole 512 blocks)
  out = np.empty_like(v); b = v.reshape(-1, 16, 2, 16)
  out.reshape(-1, 2, 16, 16)[:, 0] = b[:, :, 0]; out.reshape(-1, 2, 16, 16)[:, 1] = b[:, :, 1]
  return out
def project(m, bits, x):
  group = 16 if bits == 4 else 8
  kt, nt, nb = m.shape
  buf = d.empty(kt * nt * nb, f"bfp{bits}", tiles_per_page=group)
  for first in range(0, kt, group):
    d.dev.allocator._copyin(buf.addr + first * nt * nb, np.ascontiguousarray(m[first:first + group].swapaxes(0, 1)))
  k = d.kernel(P, K=kt * 32, N=nt * 32, BITS=bits, GROUP=group, BATCH=16 if kt % 16 == 0 else 8, WORKERS=112)
  y = d.zeros(nt * 32, "bf16"); k(x=d.empty(x.size, "bf16").copy_from(x), weights=buf, output=y)
  return f32(y.numpy())
for name, bits in (("self_attn.o_proj", 8), ("mlp.down_proj", 4)):
  m = T[f"model.layers.0.{name}.weight"].numpy()
  K = m.shape[0] * 32
  v = f32(bf16(rng.standard_normal(K)))                      # the activation as the device holds it
  W = unpack_tiles(torch.from_numpy(np.ascontiguousarray(m)), "bfp8_b" if bits == 8 else "bfp4_b").double().numpy()
  ref = v.astype(np.float64) @ W
  xd = bf16(face(v)) if K % 512 == 0 else None
  full = project(m, bits, xd)
  h = m.shape[0] // 2
  if (h * 32) % 512: print(name, "half K is not whole blocks; skipped"); continue
  p0 = project(np.ascontiguousarray(m[:h]), bits, xd[:h * 32])
  p1 = project(np.ascontiguousarray(m[h:]), bits, xd[h * 32:])
  tp = f32(bf16(p0 + p1))
  rms = lambda e: float(np.sqrt(np.mean(e ** 2)) / np.sqrt(np.mean(ref ** 2)))
  print(f"{name}: single-card rel. error {rms(full - ref):.2e}, TP rel. error {rms(tp - ref):.2e}, "
        f"TP vs single {rms(tp - full):.2e}, bf16 half-ulp ~{2 ** -9:.1e}")
