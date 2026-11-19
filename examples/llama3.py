"""Llama 3 on a Blackhole card: load a safetensors checkpoint onto the device, compile the kernels in llama3/, capture
one decode step as a graph and replay it once per position. BFP8 checkpoints run on the packed projection graph in
nanbeige.py.      python examples/llama3.py --model 1b"""
import argparse, json, sys, time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from helpers import rope, safe_load, tokenizer
from ttrv import Device, Var
from examples.prefill import MAX_CHUNK, DEFAULT_CHUNK, PromptChunks, grouped_llama_weights

KERNELS, MAX_TOKENS = Path(__file__).resolve().parent / "llama3", 8192  # the kernels' default context length

class Llama3:
  def __init__(self, path, dev):
    cfg, eos = (json.loads((path / f).read_text()) for f in ("config.json", "generation_config.json"))
    self.eos = set(np.atleast_1d(eos["eos_token_id"]).tolist())
    tensors = safe_load(path)
    w = {name: dev.array(t) for name, t in tensors.items()}
    dim, mlp_dim, head_dim = cfg["hidden_size"], cfg["intermediate_size"], cfg["hidden_size"] // cfg["num_attention_heads"]
    kv_dim, embed_tiles = cfg["num_key_value_heads"] * head_dim, dim // 1024
    def kernel(name, **defines): return dev.kernel(KERNELS / f"{name}.ttrv", **defines)
    qkv, o, lm = (kernel(name, EMBED_TILES=embed_tiles) for name in ("qkv", "o", "lm"))
    gate = kernel("gate", EMBED_TILES=embed_tiles, MLP_TILES=mlp_dim // 1024)
    down = dev.kernel(KERNELS / "o.ttrv", name="down", EMBED_TILES=embed_tiles, INPUT_TILES=mlp_dim // 1024)
    embedding, attention = kernel("embedding", EMBED_TILES=embed_tiles), kernel("attention", HEAD_TILES=head_dim // 32)
    argmax = kernel("argmax")

    x, x2, q, context = (dev.empty(dim, "bf16") for _ in range(4))
    k, v, hidden, logits = (dev.empty(n, "bf16") for n in (kv_dim, kv_dim, mlp_dim, cfg["vocab_size"]))
    cos, sin = (dev.array(table, "bf16") for table in rope(cfg, head_dim, MAX_TOKENS))
    self.history, self.tokens = dev.zeros(MAX_TOKENS, "u32"), dev.zeros((MAX_TOKENS + 1, 4), "u32", host=True)
    pos = Var("pos")
    caches = []
    with dev.graph() as self.step:  # one position: embed its token, run the layers, then argmax appends the next token
      embedding(history=self.history, weights=w["model.embed_tokens.weight"], output=x, token_pos=pos)
      for i in range(cfg["num_hidden_layers"]):
        W = lambda name: w[f"model.layers.{i}.{name}.weight"]
        qkv(x=x, norm=W("input_layernorm"), wq=W("self_attn.q_proj"), wk=W("self_attn.k_proj"), wv=W("self_attn.v_proj"),
            q_out=q, k_out=k, v_out=v)
        keys, values = (dev.zeros(MAX_TOKENS * kv_dim, "bf16") for _ in range(2))
        caches.append((keys, values))
        attention(q_in=q, k_in=k, v_in=v, cos=cos, sin=sin, key_cache=keys, value_cache=values, context=context, start_pos=pos)
        o(context=context, matrix=W("self_attn.o_proj"), output=x2, residual=x)
        gate(x=x2, gamma=W("post_attention_layernorm"), hidden=hidden, gate_w=W("mlp.gate_proj"), up_w=W("mlp.up_proj"))
        down(context=hidden, matrix=W("mlp.down_proj"), output=x, residual=x2)
      lm(x=x, norm=w["model.norm.weight"], wlm=w.get("lm_head.weight", w["model.embed_tokens.weight"]), logits=logits)
      argmax(logits=logits, history=self.history, tokens=self.tokens, start_pos=pos, write_token=Var("write_token"))

    self.prompt = None
    self.make_prompt = lambda: PromptChunks(dev, cfg, MAX_TOKENS, w, grouped_llama_weights(dev, tensors, cfg),
                                             caches, self.history, cos, sin)

  def generate(self, ids, n, *, chunked=True, chunk_size=DEFAULT_CHUNK):
    """Yield up to n tokens after the prompt, until EOS. Two runs are in flight: p + 1 reads its token on the device."""
    if not ids or n < 1 or len(ids) + n - 1 > MAX_TOKENS: raise ValueError("invalid prompt or generation length")
    self.history.copy_from(np.pad(np.uint32(ids), (0, MAX_TOKENS - len(ids))))
    run, end = lambda p: self.step(pos=p, write_token=int(len(ids) - 1 <= p < end - 1)), len(ids) - 1 + n
    prefix = len(ids) - 1 if chunked and len(ids) > 2 else 0
    if prefix:
      if self.prompt is None: self.prompt = self.make_prompt()
      self.prompt.run(prefix, chunk_size)
    tokens, done = self.tokens.numpy(), run(prefix)
    for p in range(prefix, end):
      after = run(p + 1) if p + 1 < end else None
      done.wait()
      if p >= len(ids) - 1:
        if (token := int(tokens[p + 1, 0])) in self.eos: return
        yield token
      done = after

def load(path, dev):
  """BF16 checkpoints run on the row-major Llama kernels; BFP8 checkpoints on the packed projection graph."""
  if (path / "model.safetensors").exists() and any(t.packed_format for t in safe_load(path).values()):
    from examples.nanbeige import Nanbeige
    return Nanbeige(path / "model.safetensors", dev, max_tokens=MAX_TOKENS)
  return Llama3(path, dev)

if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--model", default="1b", choices=["1b", "8b-bf16", "8b-bfp8"])
  ap.add_argument("--prompt", default="Write a story about a robot learning to paint.")
  ap.add_argument("--tokens", type=int, default=256)
  ap.add_argument("--device", type=int, default=0)
  ap.add_argument("--prefill-chunk", type=int, choices=range(1, MAX_CHUNK + 1), metavar="1..320", default=DEFAULT_CHUNK)
  a = ap.parse_args()
  enc = tokenizer(path := ROOT / "weights" / f"llama3-{a.model}")
  ids = enc.encode(f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{a.prompt}<|eot_id|>"
                   "<|start_header_id|>assistant<|end_header_id|>\n\n", allowed_special="all")
  dev = Device(a.device)
  try:
    model = load(path, dev)
    count = 0
    for token in model.generate(ids, a.tokens, chunk_size=a.prefill_chunk):
      if count == 0: start = time.perf_counter()
      count += 1
      sys.stdout.buffer.write(enc.decode_single_token_bytes(token))
      sys.stdout.flush()
    if model.prompt:
      print(f"\n{len(ids)-1} cached prompt tokens, {(len(ids)-1)/model.prompt.elapsed:.1f} prefill tok/s")
    if count > 1: print(f"{count} generated tokens, {(count-1)/(time.perf_counter()-start):.1f} decode tok/s")
  finally:
    dev.close()
