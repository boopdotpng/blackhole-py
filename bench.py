# Decode benchmarks: 64 tokens after the default prompt, and 64 tokens after a 4096-token context.
# The long context skips prefill: the KV caches get random bf16 and decode starts at position 4096 (timing does not
# depend on the cached values). % DRAM is the share of 512 GB/s needed to read weights, LM head and KV once per token.
import json, sys
import numpy as np
from helpers import safe_load
from llama3 import Llama3, ChatTokenizer

TOKENS, CONTEXT, DRAM_BW = 64, 4096, 512e9

def weight_bytes(model) -> int:  # the embedding is read one row per token, unless it doubles as the LM head
  path = model.checkpoint / "model.safetensors.index.json"
  t = safe_load(path if path.exists() else model.checkpoint / "model.safetensors")
  return sum(x.nbytes for n, x in t.items() if not (n.endswith("embed_tokens.weight") and "lm_head.weight" in t))

def bench(key):
  model = Llama3(key)
  try:
    cfg = json.loads((model.checkpoint / "config.json").read_text())
    head_dim = cfg.get("head_dim", cfg["hidden_size"] // cfg["num_attention_heads"])
    kv_per_token = cfg["num_hidden_layers"] * 2 * cfg["num_key_value_heads"] * head_dim * 2
    weights, eos = weight_bytes(model), model.m["eos"]
    model.m["eos"] = []  # always decode TOKENS tokens
    rows = []
    ids = ChatTokenizer(model.checkpoint).chat([{"role": "user", "content": "Write a story about a robot learning to paint."}])
    _, s = model.generate(ids, TOKENS)
    rows.append(("short", len(ids), s["period_us"]))
    caches = [b for b in model.m["uploads"] if b["kind"] == "zeros"]
    rand = (np.random.default_rng(0).standard_normal(max(b["size"] for b in caches) // 2, np.float32).view(np.uint32) >> 16).astype(np.uint16)
    for b in caches: model.dev.allocator._copyin(model.buffer(b), rand[:b["size"] // 2])
    _, s = model.generate(np.random.default_rng(0).integers(0, 128000, CONTEXT + 1).tolist(), TOKENS, start=CONTEXT)
    rows.append(("4K", CONTEXT, s["period_us"]))
    model.m["eos"] = eos
    return [(ctx, us, (weights + kv_per_token * n) / (us * 1e-6) / DRAM_BW) for ctx, n, us in rows]
  finally:
    model.close()

if __name__ == "__main__":
  for key in sys.argv[1:] or ("1b", "8b-fp8", "8b-bf16"):
    for ctx, us, frac in bench(key): print(f"{key:<8} {ctx:<6} {us / 1e3:6.2f} ms/token {1e6 / us:6.1f} tok/s {frac:4.0%} DRAM")
