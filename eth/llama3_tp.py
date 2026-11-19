"""Llama 3 (BF16) decode split over two Blackhole cards joined by TT-link, Megatron style: each card owns half the
query/KV heads and half the MLP; o_proj and down_proj produce partial sums that a cross-card all-reduce adds to the
residual. Embedding and norms are replicated; the LM head is split by vocabulary and the two cards'
argmax winners are exchanged, so both append the same token.
      python eth/llama3_tp.py --model 1b --tokens 64"""
import argparse, json, sys, time
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
from helpers import rope, safe_load, tokenizer
from ttrv import Device, Var
from tp import Link, allreduce_kernel, pick_kernel

KERNELS, MAX_TOKENS = ROOT / "examples" / "llama3", 8192


def shard(t, rank, axis):
  a = t.numpy()
  n = a.shape[axis] // 2
  return np.ascontiguousarray(a[n * rank:n * (rank + 1)] if axis == 0 else a[:, n * rank:n * (rank + 1)])


class Llama3TP:
  def __init__(self, path, devs, link):
    cfg, eos = (json.loads((path / f).read_text()) for f in ("config.json", "generation_config.json"))
    self.eos = set(np.atleast_1d(eos["eos_token_id"]).tolist())
    self.devs, self.link = devs, link
    tensors = safe_load(path)
    L = cfg["num_hidden_layers"]
    dim, mlp_dim, heads, kv_heads = cfg["hidden_size"], cfg["intermediate_size"], cfg["num_attention_heads"], cfg["num_key_value_heads"]
    head_dim = dim // heads
    q_dim, kv_dim, mlp = dim // 2, kv_heads * head_dim // 2, mlp_dim // 2  # per card
    et = dim // 1024
    self.history, self.tokens, self.steps, self.replays = [], [], [], 0
    pos, step, write_token = Var("pos"), Var("step"), Var("write_token")
    for r, dev in enumerate(devs):
      def up(name, axis):  # this card's half of a row-major BF16 matrix, split along axis
        a = shard(tensors[name], r, axis)
        return dev.empty(a.size, "bf16").copy_from(a)
      def kernel(name, **defines): return dev.kernel(KERNELS / f"{name}.ttrv", **defines)
      qkv = kernel("qkv", EMBED_TILES=et, Q_DIM=q_dim, KV_DIM=kv_dim)
      o = kernel("o", EMBED_TILES=et, INPUT_TILES=q_dim // 1024 or 1)
      if q_dim % 1024: raise ValueError("o_proj input must be whole 1024-element tiles per card")
      gate = kernel("gate", EMBED_TILES=et, MLP_TILES=mlp // 1024)
      down = dev.kernel(KERNELS / "o.ttrv", name="down", EMBED_TILES=et, INPUT_TILES=mlp // 1024, BATCH_TILES=mlp // 1024)
      vocab = cfg["vocab_size"] // 2
      lm = kernel("lm", EMBED_TILES=et, VOCAB=vocab)
      argmax = kernel("argmax", TP=1, VOCAB=vocab, VOCAB_BASE=r * vocab)
      pick = pick_kernel(dev, link, rank=r, nslot=2 * L + 1)
      embedding, attention = kernel("embedding", EMBED_TILES=et), kernel("attention", HEAD_TILES=head_dim // 32, KV_HEADS=kv_heads // 2)
      reduce = allreduce_kernel(dev, link, dim=dim, rank=r, nslot=2 * L + 1)

      embed = dev.array(tensors["model.embed_tokens.weight"])
      lm_w = up("lm_head.weight" if "lm_head.weight" in tensors else "model.embed_tokens.weight", 0)
      winner = dev.zeros(1024, "u32")
      final_norm = dev.array(tensors["model.norm.weight"])
      x, x2, part, zero, context = dev.empty(dim, "bf16"), dev.empty(dim, "bf16"), dev.empty(dim, "bf16"), dev.zeros(dim, "bf16"), dev.empty(q_dim, "bf16")
      q, k, v, hidden, logits = (dev.empty(n, "bf16") for n in (q_dim, kv_dim, kv_dim, mlp, vocab))
      cos, sin = (dev.array(table, "bf16") for table in rope(cfg, head_dim, MAX_TOKENS))
      history, tokens = dev.zeros(MAX_TOKENS, "u32"), dev.zeros((MAX_TOKENS + 1, 4), "u32", host=True)
      layers = []
      for i in range(L):
        p = f"model.layers.{i}."
        layers.append(dict(
          ln1=dev.array(tensors[p + "input_layernorm.weight"]), ln2=dev.array(tensors[p + "post_attention_layernorm.weight"]),
          wq=up(p + "self_attn.q_proj.weight", 0), wk=up(p + "self_attn.k_proj.weight", 0), wv=up(p + "self_attn.v_proj.weight", 0),
          wo=up(p + "self_attn.o_proj.weight", 1), wg=up(p + "mlp.gate_proj.weight", 0), wu=up(p + "mlp.up_proj.weight", 0),
          wd=up(p + "mlp.down_proj.weight", 1),
          keys=dev.zeros(MAX_TOKENS * kv_dim, "bf16"), values=dev.zeros(MAX_TOKENS * kv_dim, "bf16")))
      with dev.graph() as g:
        embedding(history=history, weights=embed, output=x, token_pos=pos)
        for i, W in enumerate(layers):
          qkv(x=x, norm=W["ln1"], wq=W["wq"], wk=W["wk"], wv=W["wv"], q_out=q, k_out=k, v_out=v)
          attention(q_in=q, k_in=k, v_in=v, cos=cos, sin=sin, key_cache=W["keys"], value_cache=W["values"], context=context, start_pos=pos)
          o(context=context, matrix=W["wo"], output=part, residual=zero)
          reduce(partial=part, residual=x, output=x2, step=step, slot=2 * i)
          gate(x=x2, gamma=W["ln2"], hidden=hidden, gate_w=W["wg"], up_w=W["wu"])
          down(context=hidden, matrix=W["wd"], output=part, residual=zero)
          reduce(partial=part, residual=x2, output=x, step=step, slot=2 * i + 1)
        lm(x=x, norm=final_norm, wlm=lm_w, logits=logits)
        argmax(logits=logits, history=history, tokens=tokens, start_pos=pos, write_token=write_token, winner=winner)
        pick(winner=winner, history=history, tokens=tokens, start_pos=pos, write_token=write_token, step=step, slot=2 * L)
      self.steps.append(g); self.history.append(history); self.tokens.append(tokens)

  def run(self, p, write):
    self.replays += 1
    return [g(pos=p, step=self.replays, write_token=write) for g in self.steps]

  def generate(self, ids, n):
    if not ids or n < 1 or len(ids) + n - 1 > MAX_TOKENS: raise ValueError("invalid prompt or generation length")
    for h in self.history: h.copy_from(np.pad(np.uint32(ids), (0, MAX_TOKENS - len(ids))))
    end = len(ids) - 1 + n
    tokens = [t.numpy() for t in self.tokens]
    done = self.run(0, int(0 >= len(ids) - 1))
    for p in range(end):
      after = self.run(p + 1, int(len(ids) - 1 <= p + 1 < end)) if p + 1 < end else None
      for e in done: e.wait(10)
      if p >= len(ids) - 1:
        a, b = int(tokens[0][p + 1, 0]), int(tokens[1][p + 1, 0])
        if a != b: raise RuntimeError(f"cards disagree at position {p + 1}: {a} vs {b}")
        if a in self.eos: return
        yield a
      done = after


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--model", default="1b", choices=["1b", "8b-bf16"])
  ap.add_argument("--prompt", default="Write a story about a robot learning to paint.")
  ap.add_argument("--tokens", type=int, default=64)
  a = ap.parse_args()
  path = ROOT / "weights" / f"llama3-{a.model}"
  enc = tokenizer(path)
  ids = enc.encode(f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{a.prompt}<|eot_id|>"
                   "<|start_header_id|>assistant<|end_header_id|>\n\n", allowed_special="all")
  devs = [Device(0), Device(1)]
  link = Link(devs)
  t = time.perf_counter()
  model = Llama3TP(path, devs, link)
  print(f"loaded in {time.perf_counter() - t:.1f} s", file=sys.stderr)
  count, out = 0, []
  for token in model.generate(ids, a.tokens):
    if count == 0: start = time.perf_counter()
    count += 1
    out.append(token)
    sys.stdout.buffer.write(enc.decode_single_token_bytes(token)); sys.stdout.flush()
  if count > 1: print(f"\n{count} generated tokens, {(count - 1) / (time.perf_counter() - start):.1f} decode tok/s")
  print("ids", out[:16], file=sys.stderr)
  link.close()
