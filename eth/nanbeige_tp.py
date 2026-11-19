"""Packed-BFP Llama-architecture decode (Nanbeige4.3-33B, Llama 3 8B BFP8) split over two Blackhole cards joined by
TT-link. Each card holds half the query/KV heads, half the MLP and half the vocabulary; o_proj and down_proj write
partial sums that a cross-card all-reduce adds to the residual; the two argmax winners are exchanged.
      python eth/nanbeige_tp.py --checkpoint ../weights/nanbeige4.3-33b/mixed_bfp4mlp_bfp8attn/model.safetensors"""
import argparse, json, sys, time
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
from helpers import rope, safe_load
from ttrv import Device, Var
from tp import Link, allreduce_kernel, pick_kernel

KERNELS = ROOT / "examples" / "nanbeige"
LLAMA = ROOT / "examples" / "llama3"
DEFAULT = ROOT.parent / "weights/nanbeige4.3-33b/mixed_bfp4mlp_bfp8attn/model.safetensors"


def half(a, rank, axis):
  n = a.shape[axis] // 2
  return a[n * rank:n * (rank + 1)] if axis == 0 else a[:, n * rank:n * (rank + 1)]


class NanbeigeTP:
  def __init__(self, file, devs, link, max_tokens=8192):
    cfg = self.cfg = json.loads((file.parent / "config.json").read_text())
    generation = file.parent / "generation_config.json"
    eos = json.loads(generation.read_text())["eos_token_id"] if generation.exists() else cfg["eos_token_id"]
    self.eos = set(np.atleast_1d(eos).tolist())
    self.devs, self.link, self.max_tokens = devs, link, max_tokens
    tensors = safe_load(file)
    capacity = (max_tokens + 31) // 32 * 32
    L = cfg["num_hidden_layers"]
    dim, mlp, vocab = cfg["hidden_size"], cfg["intermediate_size"] // 2, cfg["vocab_size"] // 2
    d, kv = cfg.get("head_dim", dim // cfg["num_attention_heads"]), cfg["num_key_value_heads"] // 2
    group = cfg["num_attention_heads"] // cfg["num_key_value_heads"]
    self.steps, self.readouts, self.history, self.tokens, self.ops = [], [], [], [], 1
    pos, step, write_token = Var("pos"), Var("step"), Var("write_token")
    for r, dev in enumerate(devs):
      weights, projections, kernels = {}, {}, {}
      for name, t in tensors.items():
        second = third = 0
        if t.packed_format:
          stem, _, proj = name.removesuffix(".weight").rpartition(".")
          if proj in ("k_proj", "v_proj", "up_proj"): continue
          parts = [t]
          if proj == "q_proj": parts += [tensors[f"{stem}.{v}_proj.weight"] for v in ("k", "v")]
          if proj == "gate_proj": parts.append(tensors[f"{stem}.up_proj.weight"])
          # [K/32, N/32, tile bytes]: column-parallel projections take half of each part's N, row-parallel half of K
          axis = 0 if proj in ("o_proj", "down_proj") else 1   # lm_head: half the vocabulary (N)
          tiles = [np.ascontiguousarray(half(part.numpy(), r, axis)) for part in parts]
          widths = [m.shape[1] * 32 for m in tiles]
          n, k = sum(widths), tiles[0].shape[0] * 32
          second, third = (widths + [0, 0])[1:3]
          bits = {"bfp4_b": 4, "bfp8_b": 8}[t.packed_format]
          batch = 16 if (k // 32) % 16 == 0 else 8
          group_tiles = min(16 if bits == 4 else 8, batch)
          row_bytes = n // 32 * t.shape[-1]
          buf = dev.empty(k // 32 * row_bytes, f"bfp{bits}", tiles_per_page=group_tiles)
          for first in range(0, k // 32, group_tiles):
            offset = buf.addr + first * row_bytes
            for matrix in tiles:
              strip = np.ascontiguousarray(matrix[first:first + group_tiles].swapaxes(0, 1))
              dev.dev.allocator._copyin(offset, strip)
              offset += strip.nbytes
        elif name == "lm_head.weight":
          w = half(t.numpy(), r, 0)
          n, k = w.shape
          bits, group_tiles, batch = 16, 4, 16
          buf = dev.empty(n * k, "bf16", tiles_per_page=group_tiles)
          for col in range(0, k, group_tiles * 32):
            strip = w[:, col:col + group_tiles * 32].reshape(n // 32, 2, 16, group_tiles, 2, 16)
            dev.dev.allocator._copyin(buf.addr + col * n * 2, strip.transpose(0, 3, 4, 1, 5, 2).copy())
        else:
          weights[name] = dev.array(t)
          continue
        key = k, n, bits, second, third, group_tiles, batch
        if key not in kernels:
          workers = 96 if second or bits == 16 else 112
          kernels[key] = dev.kernel(KERNELS / "projection.ttrv", K=k, N=n, BITS=bits, GROUP=group_tiles, BATCH=batch,
                                    SECOND=second, THIRD=third, WORKERS=min(n // 32, workers, len(dev.dev.workers)))
        projections[name] = kernels[key], buf

      vector = KERNELS / "vector.ttrv"
      rms = dev.kernel(vector, DIM=dim, RMS=1, EPS=cfg["rms_norm_eps"])
      swiglu = dev.kernel(vector, DIM=mlp, SWIGLU=1)
      embed = dev.kernel(LLAMA / "embedding.ttrv", EMBED_TILES=dim // 1024)
      argmax = dev.kernel(LLAMA / "argmax.ttrv", VOCAB=vocab, MAX_TOKENS=capacity, TP=1, VOCAB_BASE=r * vocab)
      attend = dev.kernel(LLAMA / "attention.ttrv", HEAD_TILES=d // 32, KV_HEADS=kv, GROUP=group, PACK_CONTEXT=1,
                          MAX_TOKENS=capacity)
      reduce = allreduce_kernel(dev, link, dim=dim, rank=r, nslot=1)
      pick = pick_kernel(dev, link, rank=r, nslot=1)
      cos, sin = (dev.array(table, "bf16") for table in rope(cfg, d, capacity))
      history, tokens = dev.zeros(capacity, "u32"), dev.zeros((capacity + 1, 4), "u32", host=True)
      x, norm, part = (dev.empty(dim, "bf16") for _ in range(3))
      q, ctx = dev.empty(kv * group * d, "bf16"), dev.empty(kv * group * d, "bf16")
      k_, v_ = (dev.empty(kv * d, "bf16") for _ in range(2))
      # hidden is face-packed for down_proj: Nanbeige's 11008 per card ends in a half block, stored as a whole one
      gate, up, hidden = dev.empty(mlp, "bf16"), dev.empty(mlp, "bf16"), dev.empty((mlp + 511) // 512 * 512, "bf16")
      logits, winner = dev.empty(vocab, "bf16"), dev.zeros(1024, "u32")
      def project(name, src, dst, **outputs):
        kernel, matrix = projections[name + ".weight"]
        kernel(x=src, weights=matrix, output=dst, **outputs)
      with dev.graph() as g:
        embed(history=history, weights=weights["model.embed_tokens.weight"], output=x, token_pos=pos)
        for i in range(L):
          layer = f"model.layers.{i}."
          rms(x=x, other=weights[layer + "input_layernorm.weight"], output=norm)
          project(layer + "self_attn.q_proj", norm, q, output2=k_, output3=v_)
          keys, values = (dev.zeros(capacity * kv * d, "bf16") for _ in range(2))
          attend(q_in=q, k_in=k_, v_in=v_, cos=cos, sin=sin, key_cache=keys, value_cache=values, context=ctx, start_pos=pos)
          project(layer + "self_attn.o_proj", ctx, part)
          reduce(partial=part, residual=x, output=x, step=step, slot=2 * i)
          rms(x=x, other=weights[layer + "post_attention_layernorm.weight"], output=norm)
          project(layer + "mlp.gate_proj", norm, gate, output2=up)
          swiglu(x=gate, other=up, output=hidden)
          project(layer + "mlp.down_proj", hidden, part)
          reduce(partial=part, residual=x, output=x, step=step, slot=2 * i + 1)
      with dev.graph() as ro:
        rms(x=x, other=weights["model.norm.weight"], output=norm)
        project("lm_head", norm, logits)
        argmax(logits=logits, history=history, tokens=tokens, start_pos=pos, write_token=write_token, winner=winner)
        pick(winner=winner, history=history, tokens=tokens, start_pos=pos, write_token=write_token, step=step, slot=0)
      self.steps.append(g); self.readouts.append(ro); self.history.append(history); self.tokens.append(tokens)
    self.per_step = 2 * L

  # Every all-reduce gets the next tag, so consecutive ones alternate buffers on both cards.
  def step(self, pos):
    base, self.ops = self.ops, self.ops + self.per_step
    return [g(pos=pos, step=base) for g in self.steps]

  def readout(self, pos, write):
    base, self.ops = self.ops, self.ops + 1
    return [g(pos=pos, step=base, write_token=write) for g in self.readouts]

  def generate(self, ids, n):
    end = len(ids) + n - 1
    if not ids or n < 1 or end > self.max_tokens: raise ValueError("invalid prompt or generation length")
    for h in self.history: h.copy_from(np.pad(np.uint32(ids), (0, h.shape[0] - len(ids))))
    out = [t.numpy() for t in self.tokens]
    for p in range(end):
      self.step(p)
      if p < len(ids) - 1: continue
      for e in self.readout(p, int(p + 1 < end)): e.wait(30)
      a, b = int(out[0][p + 1, 0]), int(out[1][p + 1, 0])
      if a != b: raise RuntimeError(f"cards disagree at position {p + 1}: {a} vs {b}")
      if a in self.eos: return
      yield a


if __name__ == "__main__":
  from tokenizers import Tokenizer
  ap = argparse.ArgumentParser(description=__doc__)
  ap.add_argument("--checkpoint", type=Path, default=DEFAULT)
  ap.add_argument("--prompt", default="The capital of France is")
  ap.add_argument("--tokens", type=int, default=32)
  a = ap.parse_args()
  tok = Tokenizer.from_file(str(a.checkpoint.parent / "tokenizer.json"))
  ids = tok.encode(a.prompt, add_special_tokens=False).ids
  devs = [Device(0), Device(1)]
  link = Link(devs)
  t = time.perf_counter()
  model = NanbeigeTP(a.checkpoint, devs, link, max_tokens=len(ids) + a.tokens - 1)
  print(f"loaded in {time.perf_counter() - t:.1f} s", file=sys.stderr)
  out = []
  for token in model.generate(ids, a.tokens):
    last = time.perf_counter()
    if not out: start = last
    out.append(token)
  print(tok.decode(out))
  print("ids", out[:16], file=sys.stderr)
  if len(out) > 1: print(f"{len(out) - 1} decode steps in {last - start:.3f}s, {(len(out) - 1) / (last - start):.2f} tok/s", file=sys.stderr)
  link.close()
