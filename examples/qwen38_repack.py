"""Rewrite a packed Qwen3.8 checkpoint with chosen tensors re-quantized from the BF16 snapshot.

The default moves every mlp.down_proj from bfp4_b to bfp8_b (about Q4_K_M's choice of Q6_K for ffn_down) and copies
every other tensor byte for byte:

  python -I examples/qwen38_repack.py --check   # re-pack the existing bfp4_b down_proj tensors, require identical bytes
  python -I examples/qwen38_repack.py           # write mixed_bfp4mlp_bfp8down_bfp8attn/model.safetensors

Packing follows the kn_tiles_32x32_v1 layout: W^T [K, N] in 32x32 tiles stored [K/32, N/32, tile bytes]; each tile
holds 64 shared exponents (face 0 rows 0-15, faces 1-3) and then sign<<W | magnitude codes face by face, row-major.
An exponent block is 16 consecutive N. Rounding is round-to-nearest-even; a block whose largest value would saturate
takes exponent + 1 when that lowers the block's squared error.
"""

import argparse
import json
import re
import struct
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from helpers import safe_load  # noqa: E402

WEIGHTS = ROOT.parent / "weights/qwen3.8-27b"
SOURCE = WEIGHTS / "mixed_bfp4mlp_bfp8attn/model.safetensors"
OUTPUT = WEIGHTS / "mixed_bfp4mlp_bfp8down_bfp8attn/model.safetensors"
BF16 = WEIGHTS / "bf16"
MANT = {"bfp4_b": 3, "bfp8_b": 7}
TILE = {"bfp4_b": 576, "bfp8_b": 1088}


def quantize(bits, shared, w):
  """bits: fp32 bit patterns [..., 16]; shared: [..., 1] exponents. Returns codes, decoded values, saturated."""
  exp = bits >> 23 & 0xFF
  mant = (bits & 0x7FFFFF | 0x800000) >> np.clip(shared - exp, 0, 31)
  shift = 24 - w
  m = mant >> shift
  rest, tie = mant & ((1 << shift) - 1), 1 << (shift - 1)
  m = m + ((rest > tie) | ((rest == tie) & (m & 1 == 1)))
  over = (m > (1 << w) - 1).any(-1, keepdims=True)
  m = np.where(exp == 0, 0, np.minimum(m, (1 << w) - 1))
  sign = np.where(m == 0, 0, bits >> 31 & 1)
  value = m * np.exp2((shared - 127 - (w - 1)).astype(np.float32))
  return sign << w | m, np.where(sign == 1, -value, value), over


def pack(weight, fmt):
  """weight: HF BF16 bits uint16 [N, K]. Returns uint8 [K/32, N/32, tile bytes]."""
  n, k = weight.shape
  w = MANT[fmt]
  out = np.empty((k // 32, n // 32, TILE[fmt]), np.uint8)
  for first in range(0, k, 1024):
    t = np.ascontiguousarray(weight[:, first : first + 1024].T)  # W^T rows [kk, N]
    kk = t.shape[0]
    bits = (t.astype(np.int64) << 16).reshape(kk, n // 16, 16)
    x = (bits.astype(np.uint32).view(np.float32)).astype(np.float32)
    shared = (bits >> 23 & 0xFF).max(-1, keepdims=True)
    code, value, over = quantize(bits, shared, w)
    retry = over & (shared < 254)
    if retry.any():
      code2, value2, _ = quantize(bits, shared + 1, w)
      better = retry & (((value2 - x) ** 2).sum(-1, keepdims=True) < ((value - x) ** 2).sum(-1, keepdims=True))
      code, shared = np.where(better, code2, code), shared + better
    code = code.astype(np.uint8).reshape(kk // 32, 2, 16, n // 32, 2, 16).transpose(0, 3, 1, 4, 2, 5)
    code = code.reshape(kk // 32, n // 32, 1024)
    e = shared.astype(np.uint8).reshape(kk // 32, 2, 16, n // 32, 2).transpose(0, 3, 1, 4, 2)
    e = e.reshape(kk // 32, n // 32, 64)
    if fmt == "bfp4_b":
      code = code[..., 0::2] & 0xF | (code[..., 1::2] & 0xF) << 4
    out[first // 32 : (first + kk) // 32] = np.concatenate([e, code], -1)
  return out


def bf16_source():
  index = json.loads((BF16 / "model.safetensors.index.json").read_text())["weight_map"]
  shards = {}

  def load(name):
    file = index[name]
    if file not in shards:
      shards[file] = safe_load(BF16 / file)
    return shards[file][name].numpy()

  return load


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--source", type=Path, default=SOURCE)
  parser.add_argument("--output", type=Path, default=OUTPUT)
  parser.add_argument("--pattern", default=r"mlp\.down_proj\.weight$")
  parser.add_argument("--format", default="bfp8_b", choices=MANT)
  parser.add_argument("--check", action="store_true", help="re-pack matching tensors in their stored format; compare")
  args = parser.parse_args()

  with open(args.source, "rb") as f:
    n, = struct.unpack("<Q", f.read(8))
    header = json.loads(f.read(n))
  metadata = header.pop("__metadata__")
  formats = json.loads(metadata["blackhole.formats"])
  chosen = [name for name in formats if re.search(args.pattern, name)]
  if not chosen:
    raise SystemExit(f"no packed tensor matches {args.pattern}")
  load = bf16_source()

  if args.check:
    for name in chosen:
      stored = np.fromfile(args.source, np.uint8, int(np.prod(header[name]["shape"])), offset=8 + n + header[name]["data_offsets"][0])
      packed = pack(load(name), formats[name]).reshape(-1)
      diff = np.count_nonzero(packed != stored)
      print(f"{name} {formats[name]}: {diff} of {stored.size} bytes differ", flush=True)
      if diff:
        raise SystemExit(1)
    return

  # Lay out the new header first so tensors stream straight to disk in the source's order.
  order = sorted(header, key=lambda name: header[name]["data_offsets"][0])
  new, offset = {}, 0
  for name in order:
    h = dict(header[name])
    if name in chosen:
      k, nn = h["shape"][0] * 32, h["shape"][1] * 32
      h["shape"] = [k // 32, nn // 32, TILE[args.format]]
      size = int(np.prod(h["shape"]))
      formats[name] = args.format
    else:
      size = h["data_offsets"][1] - h["data_offsets"][0]
    h["data_offsets"] = [offset, offset + size]
    new[name] = h
    offset += size
  metadata = dict(metadata, **{"blackhole.formats": json.dumps(formats)})
  blob = json.dumps({"__metadata__": metadata, **new}, separators=(",", ":")).encode()
  blob += b" " * (-len(blob) % 8)

  args.output.parent.mkdir(parents=True, exist_ok=True)
  partial = args.output.with_suffix(".partial")
  with open(args.source, "rb") as src, open(partial, "wb") as out:
    out.write(struct.pack("<Q", len(blob)) + blob)
    for i, name in enumerate(order):
      if name in chosen:
        data = pack(load(name), args.format)
        assert data.nbytes == new[name]["data_offsets"][1] - new[name]["data_offsets"][0]
        out.write(data.tobytes())
        print(f"[{i + 1}/{len(order)}] {name} -> {args.format}", flush=True)
      else:
        a, b = header[name]["data_offsets"]
        src.seek(8 + n + a)
        left = b - a
        while left:
          chunk = src.read(min(left, 1 << 26))
          out.write(chunk)
          left -= len(chunk)
  partial.rename(args.output)
  print(f"wrote {args.output} ({offset / 1e9:.2f} GB of tensors)")


if __name__ == "__main__":
  main()
