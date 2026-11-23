"""Device helpers for Inkling 2 Mini: BFP page images in DRAM and the decode projection kernel.

The decode projection (examples/nanbeige/projection.ttrv) reads x face-packed (in each 512-element block, the low 16
values of every 32-element group, then the high 16), padded to a multiple of 512, and writes y = W x as a plain BF16
row. K is consumed in BATCH-tile blocks; Inkling's K = 2304 and 1152 are not multiples of 16 tiles, so BATCH is set
to GROUP for them.

  python examples/inkling/projections.py   # projection test at Inkling's shapes against numpy
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from ttrv import Device  # noqa: E402

KERNEL = ROOT / "examples/nanbeige/projection.ttrv"


def pack_x(x):
  """float vector -> face-packed BF16 bits, padded to a multiple of 512."""
  x = np.asarray(x, np.float32).reshape(-1)
  x = np.pad(x, (0, -len(x) % 512))
  u = x.view(np.uint32).astype(np.uint64)
  b = ((u + 0x7FFF + (u >> 16 & 1)) >> 16).astype(np.uint16)
  return np.ascontiguousarray(b.reshape(-1, 16, 2, 16).transpose(0, 2, 1, 3)).reshape(-1)


def floats(bits):
  return (np.asarray(bits).astype(np.uint32) << 16).view(np.float32)


def bf16_bits(x):
  u = np.asarray(x, np.float32).view(np.uint32).astype(np.uint64)
  return ((u + 0x7FFF + (u >> 16 & 1)) >> 16).astype(np.uint16)


def bf16_image(w, group=8):
  """(BF16 page image, layout) of fp32 W [N, K] in the projection's page order (as repack.image, BF16 tiles)."""
  w = np.asarray(w, np.float32)
  n, k = w.shape
  if n % 32: w, n = np.concatenate([w, np.zeros((32 - n % 32, k), np.float32)]), n + 32 - n % 32
  t = bf16_bits(w.T).reshape(k // 32, 2, 16, n // 32, 2, 16).transpose(0, 3, 1, 4, 2, 5).reshape(k // 32, n // 32, 1024)
  kt, nt = k // 32, n // 32
  pitch = nt + (nt + 1) % 2
  img = np.zeros((kt // group, pitch, group, 1024), np.uint16)
  img[:, :nt] = t.reshape(kt // group, group, nt, 1024).swapaxes(1, 2)
  return img.reshape(-1), {"K": k, "N": n, "GROUP": group, "pitch": pitch, "format": "bf16"}


def upload_experts(dev, data, tensors, layout, name):
  """One DRAM buffer holding every expert's `name` image (e{e}.name) back to back, from a layer file's bytes."""
  lay = layout[f"e0.{name}"]
  count = sum(1 for n in tensors if n.endswith("." + name))
  size = tensors[f"e0.{name}"].nbytes
  buf = dev.empty(count * size, "bfp4" if lay["format"] == "bfp4_b" else "bfp8", tiles_per_page=lay["GROUP"])
  for e in range(count):
    t = tensors[f"e{e}.{name}"]
    dev.dev.allocator.copyin(buf.addr + e * size, memoryview(data[t.offset:t.offset + t.nbytes]))
  return buf, lay


class Projections:
  """Compiled projection kernels by shape, plus per-shape input/output buffers."""

  def __init__(self, dev):
    self.dev, self.kernels = dev, {}

  def kernel(self, lay):
    key = lay["K"], lay["N"], lay["GROUP"]
    if key not in self.kernels:
      k, n, g = key
      kt = k // 32
      batch = 16 if kt % 16 == 0 else g
      workers = min(n // 32, 112, len(self.dev.dev.workers))
      self.kernels[key] = self.dev.kernel(KERNEL, K=k, N=n, BITS=8, GROUP=g, BATCH=batch, PAD=1, WORKERS=workers)
    return self.kernels[key]

  def upload(self, img, lay):
    buf = self.dev.empty(img.nbytes, "bfp8", tiles_per_page=lay["GROUP"])
    buf.copy_from(img)
    return buf

  def upload_tensor(self, t, lay):
    """A safetensors Tensor holding a page image, copied through mmap."""
    buf = self.dev.empty(t.nbytes, "bfp8", tiles_per_page=lay["GROUP"])
    buf.copy_from(t)
    return buf

  def x(self, k):
    return self.dev.empty(k + (-k % 512), "bf16")


if __name__ == "__main__":
  sys.path.insert(0, str(HERE))
  sys.path.insert(0, str(HERE.parent))
  from repack import image, tiles  # noqa: F401
  from qwen38_repack import quantize  # noqa: F401
  rng = np.random.default_rng(0)
  dev = Device(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
  P = Projections(dev)
  ok = True
  for k, n in ((2304, 2304), (1152, 2304), (3072, 2304), (2304, 6560), (2304, 1056)):
    w = (rng.standard_normal((n, k)) * 0.02).astype(np.float32)
    x = rng.standard_normal(k).astype(np.float32)
    img, lay = image(w)
    buf = P.upload(img, lay)
    xb, y = P.x(k), dev.empty(lay["N"], "bf16")
    xb.copy_from(pack_x(x))
    P.kernel(lay)(x=xb, weights=buf, output=y)
    got = floats(y.numpy())[:n]
    want = w @ floats(pack_x(x).reshape(-1, 2, 16, 16).transpose(0, 2, 1, 3).reshape(-1))[:k]
    err = np.abs(got - want).max() / np.abs(want).max()
    ok &= err < 2e-2
    print(f"K {k} N {n} GROUP {lay['GROUP']}: max error {err:.2e} of max {np.abs(want).max():.3g}")
  dev.close()
  print("PASS" if ok else "FAIL")
