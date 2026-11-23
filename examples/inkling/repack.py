"""Pack Inkling 2 Mini into BFP8_B device page images for examples/nanbeige/projection.ttrv.

Each matrix W [N, K] (HF layout) is quantized into kn_tiles_32x32_v1 tiles (examples/qwen38_repack.py) and laid out
as the projection kernel reads it: rows of GROUP K tiles, each row NT_PITCH output columns of GROUP tiles, with one
blank column when NT is even so a column's pages rotate over the DRAM banks. Experts are dequantized exactly from
NVFP4/MXFP8 first; their gate and up rows are de-interleaved so w13 outputs [gate | up].

Per layer: q = [wq; gate; wr; sink (padded to 32)] (K 2304), k and v = [wk|wv; dynamic conv taps on full layers],
o (K 3072), e{e}.w13 (K 2304, N 2304), e{e}.w2 (K 1152, N 2304). head.safetensors holds the LM head (200064 rows).
layout.json gives each image's K, N, GROUP, pitch and format.

--experts-bfp4 writes only the experts of the NVFP4 layers, as BFP4_B images, to bfp4/ (examples/inkling.py --bfp4
loads them in place of the BFP8 ones; the MXFP8 layers keep BFP8).

  python examples/inkling/repack.py [--jobs 8]
  python examples/inkling/repack.py --experts-bfp4
"""
import argparse
import json
import multiprocessing as mp
import struct
import sys
import time
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
from reference import DEFAULT, Experts, tensor  # noqa: E402
from qwen38_repack import quantize  # noqa: E402

OUT = DEFAULT.parent / "bfp8"
OUT4 = DEFAULT.parent / "bfp4"
MANT, TILE = {"bfp4_b": 3, "bfp8_b": 7}, {"bfp4_b": 576, "bfp8_b": 1088}


def group_for(k):
  kt = k // 32
  return 8 if kt % 8 == 0 else 4


def tiles(w, fmt):
  """fp32 W [N, K] -> uint8 [K/32, N/32, tile bytes]."""
  n, k = w.shape
  mant = MANT[fmt]
  out = np.empty((k // 32, n // 32, TILE[fmt]), np.uint8)
  for first in range(0, k, 512):
    x = np.ascontiguousarray(w[:, first:first + 512].T, np.float32)  # W^T rows [kk, N]
    kk = x.shape[0]
    bits = x.view(np.uint32).astype(np.int64).reshape(kk, n // 16, 16)
    xb = x.reshape(bits.shape)
    shared = (bits >> 23 & 0xFF).max(-1, keepdims=True)
    code, value, over = quantize(bits, shared, mant)
    retry = over & (shared < 254)
    if retry.any():
      code2, value2, _ = quantize(bits, shared + 1, mant)
      better = retry & (((value2 - xb) ** 2).sum(-1, keepdims=True) < ((value - xb) ** 2).sum(-1, keepdims=True))
      code, shared = np.where(better, code2, code), shared + better
    code = code.astype(np.uint8).reshape(kk // 32, 2, 16, n // 32, 2, 16).transpose(0, 3, 1, 4, 2, 5)
    code = code.reshape(kk // 32, n // 32, 1024)
    e = shared.astype(np.uint8).reshape(kk // 32, 2, 16, n // 32, 2).transpose(0, 3, 1, 4, 2).reshape(kk // 32, n // 32, 64)
    if fmt == "bfp4_b": code = code[..., 0::2] & 0xF | (code[..., 1::2] & 0xF) << 4
    out[first // 32:(first + kk) // 32] = np.concatenate([e, code], -1)
  return out


def image(w, fmt="bfp8_b"):
  """(device image bytes, layout) of fp32 W [N, K]."""
  w = np.asarray(w, np.float32)
  n, k = w.shape
  if n % 32: w, n = np.concatenate([w, np.zeros((32 - n % 32, k), np.float32)]), n + 32 - n % 32
  t = tiles(w, fmt)
  kt, nt, tb = t.shape
  g = group_for(k)
  pitch = nt + (nt + 1) % 2
  img = np.zeros((kt // g, pitch, g, tb), np.uint8)
  img[:, :nt] = t.reshape(kt // g, g, nt, tb).swapaxes(1, 2)
  return img.reshape(-1), {"K": k, "N": n, "GROUP": g, "pitch": pitch, "format": fmt}


def write(path, arrays):
  header, offset = {}, 0
  for name, a in arrays.items():
    header[name] = {"dtype": "U8", "shape": [a.nbytes], "data_offsets": [offset, offset + a.nbytes]}
    offset += a.nbytes
  h = json.dumps(header).encode()
  h += b" " * (-len(h) % 8)
  tmp = path.with_suffix(".tmp")
  with open(tmp, "wb") as f:
    f.write(struct.pack("<Q", len(h)) + h)
    for a in arrays.values(): f.write(a.tobytes())
  tmp.rename(path)


def experts4(i):
  """BFP4_B images of layer i's experts, or None when the layer's experts are not NVFP4."""
  from helpers import safe_load
  T = safe_load(DEFAULT / "model-00001-of-00001.safetensors")
  cfg = json.loads((DEFAULT / "config.json").read_text())["text_config"]
  E = Experts(T, i)
  if not E.nvfp4: return i, None
  arrays, layout = {}, {}
  for e in range(cfg["n_routed_experts"]):
    w13 = E.weight("w13", e).numpy()
    arrays[f"e{e}.w13"], layout[f"e{e}.w13"] = image(np.concatenate([w13[0::2], w13[1::2]]), "bfp4_b")
    arrays[f"e{e}.w2"], layout[f"e{e}.w2"] = image(E.weight("w2", e).numpy(), "bfp4_b")
  write(OUT4 / f"layer{i:02d}.safetensors", arrays)
  return i, layout


def layer(i):
  from helpers import safe_load
  T = safe_load(DEFAULT / "model-00001-of-00001.safetensors")
  W = lambda n: tensor(T[f"model.llm.layers.{i}." + n]).numpy()  # noqa: E731
  cfg = json.loads((DEFAULT / "config.json").read_text())["text_config"]
  full = i not in cfg["local_layer_ids"]
  arrays, layout = {}, {}

  def add(name, w):
    arrays[name], layout[name] = image(w)

  add("q", np.concatenate([W("attn.wq_du.weight"), W("attn.gate_attn.weight"), W("attn.wr_du.weight"),
                           W("attn.attn_sink_proj.weight")]))
  for n in "kv":
    parts = [W(f"attn.w{n}_dv.weight")] + ([W(f"attn.{n}_sconv.weight_proj")] if full else [])
    add(n, np.concatenate(parts))
  add("o", W("attn.wo_ud.weight"))
  E = Experts(T, i)
  for e in range(cfg["n_routed_experts"]):
    w13 = E.weight("w13", e).numpy()
    add(f"e{e}.w13", np.concatenate([w13[0::2], w13[1::2]]))
    add(f"e{e}.w2", E.weight("w2", e).numpy())
  write(OUT / f"layer{i:02d}.safetensors", arrays)
  return i, layout


def head():
  from helpers import safe_load
  T = safe_load(DEFAULT / "model-00001-of-00001.safetensors")
  cfg = json.loads((DEFAULT / "config.json").read_text())["text_config"]
  arrays, layout = {}, {}
  arrays["lm_head"], layout["lm_head"] = image(tensor(T["model.llm.unembed.weight"]).numpy()[:cfg["unpadded_vocab_size"]])
  write(OUT / "head.safetensors", arrays)
  return "head", layout


def job(i):
  torch.set_num_threads(1)
  t0 = time.time()
  r = head() if i == "head" else experts4(i[1]) if isinstance(i, tuple) else layer(i)
  print(f"{i}: {time.time() - t0:.0f}s", flush=True)
  return r


if __name__ == "__main__":
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument("--jobs", type=int, default=8)
  ap.add_argument("--layers", type=int, nargs="*", help="only these layers (layout.json is still merged)")
  ap.add_argument("--experts-bfp4", action="store_true", help="BFP4_B expert images of the NVFP4 layers, to bfp4/")
  a = ap.parse_args()
  if a.experts_bfp4:
    OUT4.mkdir(parents=True, exist_ok=True)
    path, layout = OUT4 / "layout.json", {}
    with mp.get_context("spawn").Pool(a.jobs) as pool:
      for i, lay in pool.imap_unordered(job, [("e4", i) for i in (a.layers or range(24))]):
        if lay is not None: layout[str(i)] = lay
    path.write_text(json.dumps(layout))
    sys.exit()
  OUT.mkdir(parents=True, exist_ok=True)
  path = OUT / "layout.json"
  layout = json.loads(path.read_text()) if path.exists() else {}
  todo = ["head"] + list(range(24)) if a.layers is None else a.layers
  with mp.get_context("spawn").Pool(a.jobs) as pool:
    for name, lay in pool.imap_unordered(job, todo):
      layout[str(name)] = lay
      path.write_text(json.dumps(layout))
