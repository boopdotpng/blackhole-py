"""Nanbeige4.3-33B decode. A TTRV graph runs one greedy decode step on Blackhole."""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from helpers import safe_load
from ttrv import Device, Var
from examples.prefill import MAX_CHUNK, DEFAULT_CHUNK, PromptChunks

KERNEL = Path(__file__).with_name("nanbeige") / "projection.ttrv"
DEFAULT = ROOT.parent / "weights/nanbeige4.3-33b/mixed_bfp4mlp_bfp8attn/model.safetensors"


class Nanbeige:
  def __init__(self, file, dev, max_tokens=8192):
    self.cfg = json.loads((file.parent / "config.json").read_text())
    tensors = safe_load(file)
    cfg = self.cfg
    if not 1 <= max_tokens <= cfg["max_position_embeddings"]:
      raise ValueError("invalid context length")
    self.max_tokens = max_tokens
    capacity = (max_tokens + 31) // 32 * 32
    weights, projections, kernels = {}, {}, {}
    prompt_weights = {}
    for name, t in tensors.items():
      second = third = 0
      if t.packed_format:
        stem, proj, _ = name.rsplit(".", 2)
        if proj in ("k_proj", "v_proj", "up_proj"): continue
        parts = [t]
        if proj == "q_proj": parts += [tensors[f"{stem}.{v}_proj.weight"] for v in ("k", "v")]
        if proj == "gate_proj": parts.append(tensors[f"{stem}.up_proj.weight"])
        widths = [part.logical_shape[0] for part in parts]
        n, k = sum(widths), t.logical_shape[1]
        second, third = (widths + [0, 0])[1:3]
        bits = {"bfp4_b": 4, "bfp8_b": 8}[t.packed_format]
        group = 16 if bits == 4 else 8
        tiles = [part.numpy() for part in parts]
        row_bytes = n // 32 * t.shape[-1]
        buf = dev.empty(k // 32 * row_bytes, f"bfp{bits}", tiles_per_page=group)
        # Keep the file's native tile bytes. Each DRAM page streams one output column over group K tiles.
        for first in range(0, k // 32, group):
          offset = buf.addr + first * row_bytes
          for matrix in tiles:
            strip = np.ascontiguousarray(matrix[first:first + group].swapaxes(0, 1))
            dev.dev.allocator._copyin(offset, strip)
            offset += strip.nbytes
      elif name == "lm_head.weight":
        n, k = t.shape
        bits, group = 16, 4
        buf = dev.empty(n * k, "bf16", tiles_per_page=group)
        w = t.numpy()
        for col in range(0, k, group * 32):
          strip = w[:, col:col + group * 32].reshape(n//32, 2, 16, group, 2, 16)
          strip = strip.transpose(0, 3, 4, 1, 5, 2).copy()
          dev.dev.allocator._copyin(buf.addr + col * n * 2, strip)
      else:
        weights[name] = dev.array(t)
        continue
      key = k, n, bits, second, third
      if key not in kernels:
        workers = 96 if second or bits == 16 else 112
        kernels[key] = dev.kernel(KERNEL, K=k, N=n, BITS=bits, GROUP=group, SECOND=second, THIRD=third,
                                  WORKERS=min(n // 32, workers, len(dev.dev.workers)))
      projections[name] = kernels[key], buf
      if t.packed_format: prompt_weights[name] = (buf, k, n, bits, group, second, third, None, None)

    dim, mlp, vocab = cfg["hidden_size"], cfg["intermediate_size"], cfg["vocab_size"]
    d, kv = cfg["head_dim"], cfg["num_key_value_heads"]
    group = cfg["num_attention_heads"] // kv
    vector = KERNEL.with_name("vector.ttrv")
    rms = dev.kernel(vector, DIM=dim, RMS=1, EPS=cfg["rms_norm_eps"])
    swiglu = dev.kernel(vector, DIM=mlp, SWIGLU=1)
    add = dev.kernel(vector, DIM=dim)
    llama = KERNEL.parent.parent / "llama3"
    embed = dev.kernel(llama / "embedding.ttrv", EMBED_TILES=dim // 1024)
    argmax = dev.kernel(llama / "argmax.ttrv", VOCAB=vocab, MAX_TOKENS=capacity)
    attend = dev.kernel(llama / "attention.ttrv", HEAD_TILES=d // 32, KV_HEADS=kv, GROUP=group,
                        PACK_CONTEXT=1, MAX_TOKENS=capacity)
    inv = cfg["rope_theta"] ** (-np.arange(0, d, 2, dtype=np.float32) / d)
    angle = np.tile(np.arange(capacity, dtype=np.float32)[:, None] * inv, 2)
    cos = dev.array(np.cos(angle), "bf16")
    sin = dev.array(np.sin(angle) * np.repeat(np.float32([-1, 1]), d//2), "bf16")
    self.history = dev.zeros(capacity, "u32")
    self.tokens = dev.zeros((capacity + 1, 4), "u32", host=True)
    x, norm, q, ctx = (dev.empty(dim, "bf16") for _ in range(4))
    k, v = (dev.empty(kv*d, "bf16") for _ in range(2))
    gate, up, hidden = (dev.empty(mlp, "bf16") for _ in range(3))
    logits = dev.empty(vocab, "bf16")
    def project(name, src, dst, **outputs):
      kernel, matrix = projections[name + ".weight"]
      kernel(x=src, weights=matrix, output=dst, **outputs)

    pos = Var("pos")
    caches = []
    with dev.graph() as self.step:
      embed(history=self.history, weights=weights["model.embed_tokens.weight"], output=x, token_pos=pos)
      for i in range(cfg["num_hidden_layers"]):
        layer = f"model.layers.{i}."
        rms(x=x, other=weights[layer + "input_layernorm.weight"], output=norm)
        project(layer + "self_attn.q_proj", norm, q, output2=k, output3=v)
        keys, values = (dev.zeros(capacity * kv * d, "bf16") for _ in range(2))
        caches.append((keys, values))
        attend(q_in=q, k_in=k, v_in=v, cos=cos, sin=sin, key_cache=keys, value_cache=values,
               context=ctx, start_pos=pos)
        project(layer + "self_attn.o_proj", ctx, norm)
        add(x=norm, other=x, output=x)
        rms(x=x, other=weights[layer + "post_attention_layernorm.weight"], output=norm)
        project(layer + "mlp.gate_proj", norm, gate, output2=up)
        swiglu(x=gate, other=up, output=hidden)
        project(layer + "mlp.down_proj", hidden, norm)
        add(x=norm, other=x, output=x)
    with dev.graph() as self.readout:
      rms(x=x, other=weights["model.norm.weight"], output=norm)
      project("lm_head", norm, logits)
      argmax(logits=logits, history=self.history, tokens=self.tokens, start_pos=pos, write_token=Var("write_token"))

    self.prompt = None
    self.make_prompt = lambda: PromptChunks(dev, cfg, capacity, weights, prompt_weights, caches, self.history, cos, sin)

  def generate(self, ids, tokens, *, chunked=True, chunk_size=DEFAULT_CHUNK):
    end = len(ids) + tokens - 1
    if not ids or tokens < 1 or end > self.max_tokens:
      raise ValueError("expected a nonempty prompt and positive generation length within the allocated context")
    self.history.copy_from(np.pad(np.uint32(ids), (0, self.history.shape[0] - len(ids))))
    out = self.tokens.numpy()
    prefix = len(ids) - 1 if chunked and len(ids) > 2 else 0
    if prefix:
      if self.prompt is None: self.prompt = self.make_prompt()
      self.prompt.run(prefix, chunk_size)
    for pos in range(prefix, end):
      generating = pos >= len(ids) - 1
      done = self.step(pos=pos)
      if not generating:
        done.wait()
        continue
      self.readout(pos=pos, write_token=int(pos + 1 < end)).wait()
      token = int(out[pos + 1, 0])
      if token == self.cfg["eos_token_id"]: return
      yield token


if __name__ == "__main__":
  from tokenizers import Tokenizer
  ap = argparse.ArgumentParser(description=__doc__)
  ap.add_argument("--checkpoint", type=Path, default=DEFAULT)
  ap.add_argument("--device", type=int, default=0)
  ap.add_argument("--prompt", default="The capital of France is")
  ap.add_argument("--tokens", type=int, default=8)
  ap.add_argument("--timing", action="store_true", help="report warm-path prefill and decode throughput")
  ap.add_argument("--prefill-chunk", type=int, choices=range(1, MAX_CHUNK + 1), metavar="1..320", default=DEFAULT_CHUNK)
  a = ap.parse_args()
  tok = Tokenizer.from_file(str(a.checkpoint.parent / "tokenizer.json"))
  ids = tok.encode(a.prompt, add_special_tokens=False).ids
  dev = Device(a.device)
  try:
    model = Nanbeige(a.checkpoint, dev, max_tokens=len(ids) + a.tokens - 1)
    generated = []
    for token in model.generate(ids, a.tokens, chunk_size=a.prefill_chunk):
      last = time.perf_counter()
      if not generated: start = last
      generated.append(token)
    elapsed = last - start if len(generated) > 1 else 0
    print(tok.decode(generated))
    if a.timing and model.prompt:
      print(f"{len(ids)-1} cached prompt tokens in {model.prompt.elapsed:.3f}s, "
            f"{(len(ids)-1)/model.prompt.elapsed:.2f} prefill tok/s", file=sys.stderr)
    if a.timing and elapsed:
      print(f"{len(generated) - 1} decode steps in {elapsed:.3f}s, {(len(generated) - 1) / elapsed:.2f} tok/s", file=sys.stderr)
  finally:
    dev.close()
