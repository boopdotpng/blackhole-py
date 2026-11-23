"""Inkling 2 Mini text decoder on the CPU in fp32, one token per step, from the original NVFP4/MXFP8 checkpoint.

Follows transformers' inkling2_loop (add-inkling2-mini branch): normed embedding, 24 layers in blocks of 6 with block
attention residuals, layers 6-17 run three passes (each with its own KV and conv caches; passes 2-3 merge messages
from the previous pass through rank-64 gates), relative-bias attention with sinks and output gates, four short
convolutions per layer, sigmoid-routed top-8 MoE with softcapped SwiGLU, final mix, softcapped logits.

  python examples/inkling/reference.py --prompt "The capital of France is" --tokens 8
"""
import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from helpers import safe_load  # noqa: E402

DEFAULT = ROOT.parent / "weights/inkling-2-mini/nvfp4"
E2M1 = torch.tensor([0, .5, 1, 1.5, 2, 3, 4, 6, -0., -.5, -1, -1.5, -2, -3, -4, -6])
BYTE = torch.stack([E2M1[torch.arange(256) & 15], E2M1[torch.arange(256) >> 4]], -1)  # [256, 2], low nibble first


def tensor(t):
  """fp32 torch tensor of a checkpoint tensor (BF16 and F8_E4M3 decoded)."""
  a = np.asarray(t.numpy())
  if t.dtype == "BF16": return torch.from_numpy(a.view(np.int16).copy()).view(torch.bfloat16).float()
  if t.dtype == "F8_E4M3": return torch.from_numpy(a.copy()).view(torch.float8_e4m3fn).float()
  return torch.from_numpy(a.copy()).float()


def rms(x, w=None, eps=1e-6):
  x = x * torch.rsqrt(x.square().mean(-1, keepdim=True) + eps)
  return x if w is None else x * w


def l2clip(x, threshold):
  return x * (threshold / (torch.linalg.vector_norm(x, dim=-1, keepdim=True) + 1e-6)).clamp(max=1.0)


def mix(blocks, cur, queries):
  """Block attention residual: [nq, D] mixes of the RMS-normalized earlier block states and cur."""
  s = rms(torch.stack(blocks + [cur]))
  p = torch.softmax(queries.view(-1, s.shape[-1]) @ s.T / math.sqrt(s.shape[-1]), -1)
  return p @ s


def swiglu(g, u, gc, uc):
  return torch.tanh(g / gc) * gc * torch.sigmoid(g) * torch.tanh(u / uc) * uc


class Experts:
  """Expert weights of one layer, dequantized on use."""

  def __init__(self, T, layer):
    p = f"model.llm.layers.{layer}.mlp.experts."
    self.t = {n: T[p + n] for n in ("w13_weight", "w13_weight_scale", "w2_weight", "w2_weight_scale")}
    self.nvfp4 = self.t["w13_weight"].dtype == "U8"
    if self.nvfp4:
      self.g = {n: tensor(T[p + n + "_weight_amax"]) / tensor(T[p + n + "_weight_outer_scale_denominator"])
                for n in ("w13", "w2")}

  def weight(self, name, e):
    w = np.asarray(self.t[name + "_weight"].numpy()[e])
    s = tensor_rows(self.t[name + "_weight_scale"], e)
    if self.nvfp4:
      v = BYTE[torch.from_numpy(w.astype(np.int64))].view(w.shape[0], -1, 16)
      return (v * s[..., None] * self.g[name][e]).view(w.shape[0], -1)
    v = torch.from_numpy(w.copy()).view(torch.float8_e4m3fn).float().view(w.shape[0], -1, 32)
    return (v * torch.exp2(s - 127)[..., None]).view(w.shape[0], -1)


def tensor_rows(t, e):
  a = np.asarray(t.numpy()[e])
  if t.dtype == "F8_E4M3": return torch.from_numpy(a.copy()).view(torch.float8_e4m3fn).float()
  return torch.from_numpy(a.astype(np.float32))


class Inkling:
  def __init__(self, path=DEFAULT):
    cfg = json.loads((path / "config.json").read_text())["text_config"]
    self.cfg = cfg
    T = safe_load(path / "model-00001-of-00001.safetensors")
    self.T = T
    W = lambda n: tensor(T["model.llm." + n])  # noqa: E731
    self.W = W
    self.D, self.H, self.KV, self.HD = cfg["hidden_size"], cfg["num_attention_heads"], cfg["num_key_value_heads"], cfg["head_dim"]
    self.n_layers = cfg["num_hidden_layers"]
    lc = cfg["loop_config"]
    self.loop = range(lc["core_start"], lc["core_end"])
    self.passes = lc["num_passes"]
    self.block = cfg["n_layers_per_attn_res_block"]
    self.sliding = [i in cfg["local_layer_ids"] for i in range(self.n_layers)]
    self.window = cfg["sliding_window_size"]
    self.embed = T["model.llm.embed.weight"]
    self.embed_norm, self.norm = W("embed_norm.weight"), W("norm.weight")
    self.unembed = W("unembed.weight")[: cfg["unpadded_vocab_size"]]
    self.output_query = W("attn_res.output_query")
    q, kvq = W("middle_cycle_cross_pass_queries").view(-1, 2, self.D), W("middle_cycle_cross_pass_kv_queries").view(-1, 2, self.D)
    self.message_queries = torch.cat([q[:, :1], kvq, q[:, 1:]], 1)  # [loop layer, (q, k, v, mlp), D]
    self.layers = []
    for i in range(self.n_layers):
      p = f"layers.{i}."
      L = {n: W(p + n) for n in (
        "attn.wq_du.weight", "attn.wk_dv.weight", "attn.wv_dv.weight", "attn.wr_du.weight", "attn.wo_ud.weight",
        "attn.gate_attn.weight", "attn.attn_sink_proj.weight", "attn.q_l2_clip.scale", "attn.rel_l2_clip.scale",
        "attn.rel_logits_proj.proj", "mlp_norm.weight", "mlp.gate.weight", "mlp.gate.bias")}
      L["attn_conv"] = W(p + "attn_sconv.weight")[:, 0]  # [C, 4], tap 3 is the current token
      L["mlp_conv"] = W(p + "mlp_sconv.weight")[:, 0]
      if self.sliding[i]:
        L["attn_norm"] = W(p + "attn_norm.weight")
        L["k_conv"], L["v_conv"] = W(p + "attn.k_sconv.weight")[:, 0], W(p + "attn.v_sconv.weight")[:, 0]
      else:
        for n in "qkv": L[n + "_norm"] = W(p + f"{n}_input_norm.weight")
        for n in "kv":
          L[n + "_static"] = W(p + f"attn.{n}_sconv.static_w")  # [4, C], row 0 is the current token
          L[n + "_dyn"] = W(p + f"attn.{n}_sconv.weight_proj")  # [KV * 4, D]
      if i > 0: L["attn_query"] = W(f"attn_res.attn_queries.{i - 1}")
      L["mlp_query"] = W(f"attn_res.mlp_queries.{i}")
      if i in self.loop:
        for n in ("attn", "k", "v", "mlp"):
          L["gate_" + n] = tuple(W(p + f"controllers.{n}.{m}_weight") for m in ("down", "forget", "gain"))
      L["experts"] = Experts(T, i)
      self.layers.append(L)
    self.reset()

  def reset(self):
    self.caches = {}

  def cache(self, i, p):
    key = (i, p)
    if key not in self.caches:
      kv = self.KV * self.HD
      self.caches[key] = {"k": [], "v": [], "kc": torch.zeros(3, kv), "vc": torch.zeros(3, kv),
                          "ac": torch.zeros(3, self.D), "mc": torch.zeros(3, self.D)}
    return self.caches[key]

  @staticmethod
  def conv(x, c, name, w):
    """Static depthwise conv over [3 past, x] with torch conv1d taps (tap 3 = current), plus scaled residual."""
    window = torch.cat([c[name], x[None]])
    c[name] = window[1:]
    return ((window * w.T).sum(0) + x) / math.sqrt(5)

  def dconv(self, x, c, name, static, dyn):
    """Depthwise conv whose taps are static per channel plus per-token, per-KV-head dynamic taps dyn [KV * 4]."""
    window = torch.cat([c[name], x[None]])
    c[name] = window[1:]
    lags = window.flip(0)  # lags[l] is the input l steps back
    weights = static.T.reshape(self.KV, self.HD, 4) + dyn.view(self.KV, 1, 4)
    out = (lags.T.reshape(self.KV, self.HD, 4) * weights).sum(-1).reshape(-1)
    return (out + x) / math.sqrt(9)

  # Weight matmuls: the device version overrides these.
  def project_q(self, i, hq):
    """(q [H*HD], output gate [H*HD], relative states [H*d_rel], sink logits [H]) from the query input."""
    L = self.layers[i]
    return tuple(L[n] @ hq for n in ("attn.wq_du.weight", "attn.gate_attn.weight", "attn.wr_du.weight", "attn.attn_sink_proj.weight"))

  def project_kv(self, i, h, n):
    """(k or v [KV*HD], dynamic conv taps [KV*4] or None) for n in 'kv'."""
    L = self.layers[i]
    return L[f"attn.w{n}_dv.weight"] @ h, (L[n + "_dyn"] @ h if not self.sliding[i] else None)

  def project_qkv(self, i, hq, hk, hv):
    return self.project_q(i, hq), self.project_kv(i, hk, "k"), self.project_kv(i, hv, "v")

  def project_o(self, i, x):
    return self.layers[i]["attn.wo_ud.weight"] @ x

  def experts(self, i, h, idx):
    """Each selected expert's down-projection input from h: the softcapped SwiGLU of its gate and up projections."""
    E, gc, uc = self.layers[i]["experts"], self.cfg["mlp_gate_softcap"], self.cfg["mlp_up_softcap"]
    out = []
    for e in idx:
      gu = E.weight("w13", e) @ h
      out.append(E.weight("w2", e) @ swiglu(gu[0::2], gu[1::2], gc, uc))
    return out

  def logits(self, h):
    return self.unembed @ h

  def attention(self, L, c, i, hq, hk, hv, pos):
    cfg, H, KV, HD = self.cfg, self.H, self.KV, self.HD
    full = not self.sliding[i]
    tau = 1 + cfg["log_scaling_alpha"] * math.log(max((pos + 1) / cfg["log_scaling_n_floor"], 1.0)) if full else 1.0
    (q, gate, r, sink), (k, kdyn), (v, vdyn) = self.project_qkv(i, hq, hk, hv)
    q = l2clip(q.view(H, HD) * L["attn.q_l2_clip.scale"], cfg["qk_l2_clip_threshold"]) * tau
    if full:
      k, v = self.dconv(k, c, "kc", L["k_static"], kdyn), self.dconv(v, c, "vc", L["v_static"], vdyn)
    else:
      k, v = self.conv(k, c, "kc", L["k_conv"]), self.conv(v, c, "vc", L["v_conv"])
    c["k"].append(l2clip(k.view(KV, HD), cfg["qk_l2_clip_threshold"]))
    c["v"].append(rms(v.view(KV, HD), eps=cfg["rms_norm_eps"]))
    r = l2clip(r.view(H, -1) * L["attn.rel_l2_clip.scale"], cfg["rel_l2_clip_threshold"]) * tau
    rel = r @ L["attn.rel_logits_proj.proj"]  # [H, extent]
    n = len(c["k"])
    first = max(0, n - self.window) if not full else 0
    K, V = torch.stack(c["k"][first:]), torch.stack(c["v"][first:])  # [n, KV, HD]
    dist = (n - 1) - torch.arange(first, n)  # pos - t for the keys in the window
    bias = torch.where(dist < rel.shape[1], rel[:, dist.clamp(max=rel.shape[1] - 1)], torch.zeros(()))
    group = H // KV
    scores = torch.einsum("khd,nkd->khn", q.view(KV, group, HD), K).reshape(H, -1) / math.sqrt(HD) + bias
    p = torch.softmax(torch.cat([scores, sink[:, None]], 1), 1)[:, :-1]
    out = torch.einsum("khn,nkd->khd", p.view(KV, group, -1), V).reshape(-1)
    return self.project_o(i, out * torch.sigmoid(gate))

  def moe(self, i, h):
    L, cfg = self.layers[i], self.cfg
    scores = torch.sigmoid(L["mlp.gate.weight"] @ h)
    idx = torch.topk(scores + L["mlp.gate.bias"], cfg["num_experts_per_tok"]).indices
    w = scores[idx]
    w = w / (w.sum() + 1e-20) * cfg["route_scale"]
    return sum(we * y for we, y in zip(w, self.experts(i, h, idx.tolist())))

  @staticmethod
  def message_gate(weights, h, m):
    down, forget, gain = weights
    g = down @ torch.cat([rms(h), rms(m)])
    return (1 - torch.tanh(forget @ g)) * h + torch.tanh(gain @ g) * m

  def layer(self, i, x, blocks, pos, p=0, messages=None):
    L, c = self.layers[i], self.cache(i, p)
    residual_in = x
    if self.sliding[i]:
      h = mix(blocks, x, L["attn_query"])[0] if i > 0 else x
      if messages is None:
        hq = hk = hv = rms(h, L["attn_norm"])
      else:
        hq, hk, hv = (rms(self.message_gate(L["gate_" + n], h, messages[j]), L["attn_norm"])
                      for j, n in enumerate(("attn", "k", "v")))
    else:
      hs = list(mix(blocks, x, L["attn_query"])) if i > 0 else [x, x, x]
      if messages is not None:
        hs = [self.message_gate(L["gate_" + n], hs[j], messages[j]) for j, n in enumerate(("attn", "k", "v"))]
      hq, hk, hv = (rms(h, L[n + "_norm"]) for h, n in zip(hs, "qkv"))
    a = self.conv(self.attention(L, c, i, hq, hk, hv, pos), c, "ac", L["attn_conv"])
    if i % self.block == 0:
      blocks = blocks + [residual_in]
      residual = a
    else:
      residual = residual_in + a
    h = mix(blocks, residual, L["mlp_query"])[0]
    if messages is not None: h = self.message_gate(L["gate_mlp"], h, messages[3])
    h = self.moe(i, rms(h, L["mlp_norm.weight"]))
    return residual + self.conv(h, c, "mc", L["mlp_conv"])

  @torch.no_grad()
  def step(self, token, pos):
    """Logits [unpadded vocab] after feeding token at pos."""
    row = np.asarray(self.embed.numpy()[token]).view(np.int16).copy()
    x = rms(torch.from_numpy(row).view(torch.bfloat16).float(), self.embed_norm)
    blocks = []

    def run(i, x, blocks, p=0, messages=None):
      y = self.layer(i, x, blocks, pos, p, messages)
      return y, blocks + [x] if i % self.block == 0 else blocks

    for i in range(self.loop.start):
      x, blocks = run(i, x, blocks)
    pre_x, pre_blocks = x, blocks
    for i in self.loop:
      x, blocks = run(i, x, blocks)
    for p in range(1, self.passes):
      prev_blocks, prev_x = blocks[len(pre_blocks) + 1:], x
      x, blocks = pre_x, pre_blocks
      for j, i in enumerate(self.loop):
        messages = mix(prev_blocks, prev_x, self.message_queries[j])
        x, blocks = run(i, x, blocks, p, messages)
    for i in range(self.loop.stop, self.n_layers):
      x, blocks = run(i, x, blocks)
    h = rms(mix(blocks, x, self.output_query)[0], self.norm)
    logits = self.logits(h)
    cap = self.cfg["final_logit_softcapping"]
    return torch.tanh(logits / cap) * cap


def chat(path, prompt):
  import jinja2
  env = jinja2.Environment(trim_blocks=True, lstrip_blocks=True)
  env.globals["raise_exception"] = lambda m: (_ for _ in ()).throw(ValueError(m))
  import re
  source = re.sub(r"{%-?\s*(end)?generation\s*-?%}", "", (path / "chat_template.jinja").read_text())
  return env.from_string(source).render(
    messages=[{"role": "user", "content": prompt}], add_generation_prompt=True, reasoning_effort="none")


if __name__ == "__main__":
  from tokenizers import Tokenizer
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument("--checkpoint", type=Path, default=DEFAULT)
  ap.add_argument("--prompt", default="The capital of France is")
  ap.add_argument("--tokens", type=int, default=8)
  ap.add_argument("--chat", action="store_true", help="wrap the prompt in the chat template (thinking effort 0)")
  ap.add_argument("--threads", type=int, default=12)
  ap.add_argument("--dump", type=Path, help="save prompt ids, generated ids and per-step logits (.npz)")
  a = ap.parse_args()
  torch.set_num_threads(a.threads)
  tok = Tokenizer.from_file(str(a.checkpoint / "tokenizer.json"))
  ids = tok.encode(chat(a.checkpoint, a.prompt) if a.chat else a.prompt, add_special_tokens=False).ids
  t0 = time.time()
  model = Inkling(a.checkpoint)
  print(f"loaded in {time.time() - t0:.1f}s; prompt {len(ids)} tokens", file=sys.stderr)
  out, all_logits, seq = [], [], list(ids)
  for pos in range(len(ids) + a.tokens - 1):
    t0 = time.time()
    logits = model.step(seq[pos], pos)
    all_logits.append(logits.numpy())
    if pos >= len(ids) - 1:
      nxt = int(logits.argmax())
      seq.append(nxt)
      out.append(nxt)
      print(f"pos {pos}: {nxt} {tok.decode([nxt])!r} ({time.time() - t0:.1f}s)", file=sys.stderr, flush=True)
  print(tok.decode(out, skip_special_tokens=False))
  if a.dump: np.savez(a.dump, prompt=np.array(ids), generated=np.array(out), logits=np.stack(all_logits))
