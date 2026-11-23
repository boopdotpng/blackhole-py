"""Nanbeige4.3-33B decode on one Blackhole card."""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from helpers import rope, safe_load
from ttrv import Device, Var
from examples.prefill import MAX_CHUNK, DEFAULT_CHUNK, PromptChunks

KERNEL = Path(__file__).with_name("nanbeige") / "projection.ttrv"
DEFAULT = ROOT.parent / "weights/nanbeige4.3-33b/mixed_bfp4mlp_bfp8attn/model.safetensors"


def load_checkpoint(file, dev):
  """Load a Llama-architecture checkpoint with BFP-packed projections onto dev. Returns (cfg, eos ids, weights, packed):
  weights maps the unpacked tensors (embeddings, norms) to Buffers; packed maps each projection, with k/v fused into
  q_proj and up into gate_proj, to (buffer, K, N, bits, group, second width, third width, pad)."""
  cfg = json.loads((file.parent / "config.json").read_text())
  generation = file.parent / "generation_config.json"
  eos = json.loads(generation.read_text())["eos_token_id"] if generation.exists() else cfg["eos_token_id"]
  tensors = safe_load(file)
  weights, packed = {}, {}
  for name, t in tensors.items():
    if not t.packed_format:
      weights[name] = dev.array(t)
      continue
    stem, _, proj = name.removesuffix(".weight").rpartition(".")
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
    # Keep the file's native tile bytes. Each DRAM page streams one output column over group K tiles. Rows of
    # pages (one per k group) are padded to an odd page count so a column's pages rotate over the DRAM banks.
    pitch = n // 32 + (n // 32 + 1) % 2
    row_bytes = pitch * group * t.shape[-1]
    buf = dev.empty(k // 32 // group * row_bytes, f"bfp{bits}", tiles_per_page=group)  # packed sizes are bytes
    for first in range(0, k // 32, group):
      offset = buf.addr + first // group * row_bytes
      for matrix in tiles:
        strip = np.ascontiguousarray(matrix[first:first + group].swapaxes(0, 1))
        dev.dev.allocator.copyin(offset, strip)
        offset += strip.nbytes
    packed[name] = (buf, k, n, bits, group, second, third, 1)
  return cfg, set(np.atleast_1d(eos).tolist()), weights, packed


class Nanbeige:
  def __init__(self, file, dev, max_tokens=8192, loaded=None):
    cfg, self.eos, weights, packed = loaded or load_checkpoint(file, dev)
    self.cfg = cfg
    if not 1 <= max_tokens <= cfg["max_position_embeddings"]:
      raise ValueError("invalid context length")
    self.max_tokens = max_tokens
    capacity = (max_tokens + 31) // 32 * 32
    projections, kernels = {}, {}
    packed_shard = dev.local(2048)
    prompt_weights = {name: p for name, p in packed.items() if name != "lm_head.weight"}
    for name, (buf, k, n, bits, group, second, third, _) in packed.items():
      source = 0 if name.endswith("self_attn.o_proj.weight") else packed_shard
      key = k, n, bits, second, third, source
      if key not in kernels:
        workers = 96 if second else 112
        kernels[key] = dev.kernel(KERNEL, PACKED_SHARD=source, K=k, N=n, BITS=bits, GROUP=group, SECOND=second, THIRD=third, PAD=1,
                                  WORKERS=min(n // 32, workers, len(dev.dev.workers)))
      projections[name] = kernels[key], buf

    dim, mlp, vocab = cfg["hidden_size"], cfg["intermediate_size"], cfg["vocab_size"]
    d, kv = cfg.get("head_dim", dim // cfg["num_attention_heads"]), cfg["num_key_value_heads"]
    group = cfg["num_attention_heads"] // kv
    vector = KERNEL.with_name("vector.ttrv")
    residual_l1 = dev.local(2048)
    rms = dev.kernel(vector, DIM=dim, RESIDUAL=residual_l1, PACKED_SHARD=packed_shard, RMS=1, EPS=cfg["rms_norm_eps"])
    swiglu = dev.kernel(vector, DIM=mlp, PACKED_SHARD=packed_shard, SWIGLU=1)
    add = dev.kernel(vector, DIM=dim, RESIDUAL=residual_l1)
    shared = KERNEL.parent.parent / "shared"
    embed = dev.kernel(shared / "embedding.ttrv", EMBED_TILES=dim // 1024, RESIDUAL=residual_l1)
    argmax = dev.kernel(shared / "argmax.ttrv", VOCAB=vocab, MAX_TOKENS=capacity)
    attend = dev.kernel(shared / "attention.ttrv", HEAD_TILES=d // 32, KV_HEADS=kv, GROUP=group,
                        PACK_CONTEXT=1, MAX_TOKENS=capacity)
    cos, sin = (dev.array(table, "bf16") for table in rope(cfg, d, capacity))
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
    with dev.graph() as self.decode:
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
      readout_start = len(self.decode.launches)
      rms(x=x, other=weights["model.norm.weight"], output=norm)
      project("lm_head", norm, logits)
      argmax(logits=logits, history=self.history, tokens=self.tokens, start_pos=pos, write_token=Var("write_token"))

    self.step, self.readout = self.decode.split(readout_start)
    self.prompt = None
    self.make_prompt = lambda: PromptChunks(dev, cfg, capacity, weights, prompt_weights, caches, self.history, cos, sin)
    # Prompt and decode use the same per-layer KV buffers.
    self.capacity, self.weights, self.prompt_weights, self.caches, self.cos, self.sin = \
      capacity, weights, prompt_weights, caches, cos, sin
    self.lm_head, self.logits = packed["lm_head.weight"], logits

  def generate(self, ids, tokens, *, chunked=True, chunk_size=DEFAULT_CHUNK):
    end = len(ids) + tokens - 1
    if not ids or tokens < 1 or end > self.max_tokens:
      raise ValueError("expected a nonempty prompt and positive generation length within the allocated context")
    self.history.copy_from(np.pad(np.uint32(ids), (0, self.history.shape[0] - len(ids))))
    out = self.tokens.numpy()
    prefix = len(ids) - 1 if chunked and len(ids) > 2 else 0
    if prefix:
      with self.history.device.phase("nanbeige-prefill"):
        if self.prompt is None: self.prompt = self.make_prompt()
        self.prompt.run(prefix, chunk_size, serial_step=self.step)
    for pos in range(prefix, end):
      generating = pos >= len(ids) - 1
      if not generating:
        self.step(pos=pos).wait()
        continue
      self.decode(pos=pos, write_token=int(pos + 1 < end)).wait()
      token = int(out[pos + 1, 0])
      if token in self.eos: return
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
