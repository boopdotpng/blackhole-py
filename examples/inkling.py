"""Inkling 2 Mini text decoder (thinkingmachines/Inkling-2-Mini, inkling2_loop), prefill and decode.

Follows blackhole-py-archive/examples/inkling/reference.py and llama.cpp's inkling2 graph: normed embedding, 24 layers in
blocks of 6 with block attention residuals (each layer's attention and MoE inputs are learned mixes over the earlier block
states), layers 6-17 run three passes (each with its own KV and conv caches; passes 2-3 merge messages from the previous
pass through rank-64 gates), relative-bias attention with sinks and output gates and no RoPE, four short causal convs per
layer, sigmoid-routed top-8 MoE with softcapped SwiGLU, a final mix and softcapped logits.

Precision follows the fp32 reference: weights are bf16 (the checkpoint is NVFP4/MXFP8), every activation, matmul
accumulation and output, the residual stream and the conv histories are fp32, and the KV cache dtype is cache_dtype. The
sliding-window layers keep a full-length KV cache and mask
keys older than the window. Each conv keeps a per-position history of its inputs, like the KV cache, whose first
conv_size - 1 rows are the zero history before position 0.
"""
from __future__ import annotations
import math, sys
from pathlib import Path
if __name__ == "__main__": sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from compiler import Ops, Tensor, Variable, dtypes, function, render_uir, simplify_tensor, sint

# Inkling 2 Mini text_config
emb_dim = 2304
n_layers = 24
n_heads = 24
n_kv_heads = 8
head_dim = 128
d_rel = 16
rel_extent = 1024
vocab_size = 201024  # padded embedding/unembedding rows
unpadded_vocab_size = 200058
norm_eps = 1e-6
qk_clip = 22.627416997969522
rel_clip = 8.0
log_scaling_alpha = 0.1
log_scaling_n_floor = 8192
full_layers = {5, 11, 17, 23}  # every other layer is sliding-window (local_layer_ids)
sliding_window = 1024
conv_size = 4
block_size = 6  # n_layers_per_attn_res_block
n_experts = 128
n_experts_per_tok = 8
expert_size = 1152
gate_softcap = 4.0
up_softcap = 25.0
route_scale = 8.0
logit_softcap = 30.0
loop_start, loop_end, n_passes, gate_rank = 6, 18, 3, 64
max_seq_len = 8192
cache_dtype = dtypes.float32  # KV cache; the reference keeps fp32 keys and values

n_loop = loop_end - loop_start

def rms(x: Tensor, eps: float = norm_eps) -> Tensor:
  xf = x.float()
  return xf * (xf.square().mean(axis=-1, keepdim=True) + eps).rsqrt()

def l2clip(x: Tensor, threshold: float) -> Tensor:
  x = x.float()
  return x * (threshold / (x.square().sum(-1, keepdim=True).sqrt() + 1e-6)).minimum(1.0)

# fp32 activations against bf16 weights, accumulated and returned in fp32
def mm(x: Tensor, weight: Tensor) -> Tensor: return x.float().matmul(weight.T, dtype=dtypes.float32)

def skew(x: Tensor) -> Tensor:
  """(..., S, E) -> (..., S, S + E - 1) with out[s, s + j] = x[s, j] and zeros elsewhere: pad each row by S, flatten,
  drop the last S and refold, so row s lands s columns further right."""
  *lead, S, E = x.shape
  y = x.pad(tuple(None for _ in lead) + (None, (0, S))).reshape(*lead, S * (E + S))
  return y[..., :S * (E + S - 1)].reshape(*lead, S, E + S - 1)

def mix(blocks: list[Tensor], cur: Tensor, queries: Tensor) -> list[Tensor]:
  """Block attention residual: for each of the nq queries, a softmax mix over the RMS-normalized blocks and cur."""
  D = cur.shape[-1]
  s = rms(cur.unsqueeze(-2) if not blocks else blocks[0].stack(*blocks[1:], cur, dim=-2))  # (B, S, n, D)
  p = (mm(s, queries.reshape(-1, D)) / math.sqrt(D)).softmax(-2)  # (B, S, n, nq)
  out = p.transpose(-1, -2).matmul(s, dtype=dtypes.float32)  # (B, S, nq, D)
  return [out[:, :, j] for j in range(out.shape[2])]

def history(cache: Tensor, x: Tensor, start_pos: sint) -> Tensor:
  """Store x (B, S, C) at its positions in cache (1, conv_size - 1 + max_seq_len, C), return the window of the last
  conv_size - 1 + S inputs ending at x."""
  B, S, _ = x.shape
  st = cache[:B, start_pos + conv_size - 1:start_pos + conv_size - 1 + S].uop.store(x.cast(cache.dtype).uop)
  return Tensor.from_uop(cache.uop.after(st))[:B, start_pos:start_pos + conv_size - 1 + S]

class Linear:
  def __init__(self, in_features: int, out_features: int):
    self.weight = Tensor.empty(out_features, in_features, dtype=dtypes.bfloat16)
  def __call__(self, x: Tensor) -> Tensor: return mm(x, self.weight)

class Embedding:
  def __init__(self, vocab: int, dim: int):
    self.weight = Tensor.empty(vocab, dim, dtype=dtypes.bfloat16)
  # one-hot rows selected by a masked sum over the vocab axis
  def __call__(self, idx: Tensor) -> Tensor:
    vocab, dim = self.weight.shape
    hot = idx.unsqueeze(-1).eq(Tensor.arange(vocab)).unsqueeze(-1)  # (..., vocab, 1)
    return hot.where(self.weight, 0.0).sum(-2)

class RMSNorm:
  def __init__(self, dim: int):
    self.weight = Tensor.empty(dim, dtype=dtypes.bfloat16)
  def __call__(self, x: Tensor) -> Tensor: return rms(x) * self.weight

class Holder:
  """A named parameter group, so attribute paths match the checkpoint (e.g. attn.q_l2_clip.scale)."""
  def __init__(self, **shapes: tuple[int, ...]):
    for name, shape in shapes.items(): setattr(self, name, Tensor.empty(*shape, dtype=dtypes.bfloat16))

class ShortConv:
  """Depthwise causal conv over the last conv_size inputs (tap conv_size - 1 is the current one), plus a scaled residual."""
  def __init__(self, channels: int):
    self.weight = Tensor.empty(channels, 1, conv_size, dtype=dtypes.bfloat16)
  def __call__(self, x: Tensor, window: Tensor) -> Tensor:
    S, w = x.shape[1], self.weight.reshape(-1, conv_size)
    out = sum((window[:, j:j + S] * w[:, j] for j in range(1, conv_size)), window[:, :S] * w[:, 0])
    return (out + x) / math.sqrt(conv_size + 1)

class DynamicConv:
  """Depthwise causal conv whose taps are static per channel plus dynamic per token and KV head (projected from h)."""
  def __init__(self):
    self.static_w = Tensor.empty(conv_size, n_kv_heads * head_dim, dtype=dtypes.bfloat16)  # row lag 0 is the current input
    self.weight_proj = Tensor.empty(n_kv_heads * conv_size, emb_dim, dtype=dtypes.bfloat16)
  def __call__(self, x: Tensor, window: Tensor, h: Tensor) -> Tensor:
    B, S, C = x.shape
    dyn = mm(h, self.weight_proj).reshape(B, S, n_kv_heads, conv_size)
    out: Tensor | None = None
    for lag in range(conv_size):
      past = window[:, conv_size - 1 - lag:conv_size - 1 - lag + S].reshape(B, S, n_kv_heads, head_dim)
      term = past * (self.static_w[lag].reshape(n_kv_heads, head_dim) + dyn[..., lag].unsqueeze(-1))
      out = term if out is None else out + term
    assert out is not None
    return (out.reshape(B, S, C) + x) / math.sqrt(2 * conv_size + 1)

class Controller:
  """Cross-pass message gate: (1 - tanh(forget)) * h + tanh(gain) * m, both from a rank-64 projection of [rms(h), rms(m)]."""
  def __init__(self):
    self.down_weight = Tensor.empty(gate_rank, 2 * emb_dim, dtype=dtypes.bfloat16)
    self.forget_weight = Tensor.empty(emb_dim, gate_rank, dtype=dtypes.bfloat16)
    self.gain_weight = Tensor.empty(emb_dim, gate_rank, dtype=dtypes.bfloat16)
  def __call__(self, h: Tensor, m: Tensor) -> Tensor:
    g = mm(rms(h).cat(rms(m), dim=-1), self.down_weight)
    return (1.0 - mm(g, self.forget_weight).tanh()) * h.float() + mm(g, self.gain_weight).tanh() * m.float()

class Cache:
  """The KV cache and conv input histories of one (layer, pass)."""
  def __init__(self):
    self.kv = Tensor.empty(2, 1, n_kv_heads, max_seq_len, head_dim, dtype=cache_dtype)
    rows = conv_size - 1 + max_seq_len
    self.k_conv = Tensor.empty(1, rows, n_kv_heads * head_dim, dtype=dtypes.float32)
    self.v_conv = Tensor.empty(1, rows, n_kv_heads * head_dim, dtype=dtypes.float32)
    self.attn_conv = Tensor.empty(1, rows, emb_dim, dtype=dtypes.float32)
    self.mlp_conv = Tensor.empty(1, rows, emb_dim, dtype=dtypes.float32)

class Attention:
  def __init__(self, full: bool):
    self.full = full
    self.wq_du = Linear(emb_dim, n_heads * head_dim)
    self.gate_attn = Linear(emb_dim, n_heads * head_dim)
    self.wr_du = Linear(emb_dim, n_heads * d_rel)
    self.attn_sink_proj = Linear(emb_dim, n_heads)
    self.wk_dv = Linear(emb_dim, n_kv_heads * head_dim)
    self.wv_dv = Linear(emb_dim, n_kv_heads * head_dim)
    self.wo_ud = Linear(n_heads * head_dim, emb_dim)
    self.q_l2_clip = Holder(scale=(n_heads, head_dim))
    self.rel_l2_clip = Holder(scale=(n_heads, d_rel))
    # stored flipped along the extent: column j is distance rel_extent - 1 - j (flip the checkpoint's proj at load), so a
    # skew of r @ proj lays the bias out by key position with no gather
    self.rel_logits_proj = Holder(proj=(d_rel, rel_extent))
    self.k_sconv = DynamicConv() if full else ShortConv(n_kv_heads * head_dim)
    self.v_sconv = DynamicConv() if full else ShortConv(n_kv_heads * head_dim)

  def __call__(self, hq: Tensor, hk: Tensor, hv: Tensor, cache: Cache, start_pos: sint) -> Tensor:
    B, S, _ = hq.shape
    T = start_pos + S
    pos = Tensor.arange(S) + start_pos  # query positions

    q = l2clip(self.wq_du(hq).reshape(B, S, n_heads, head_dim) * self.q_l2_clip.scale, qk_clip)
    r = l2clip(self.wr_du(hq).reshape(B, S, n_heads, d_rel) * self.rel_l2_clip.scale, rel_clip)
    if self.full:
      # log-scaled positions: 1 + alpha * log(max(1, (pos + 1) / floor))
      tau = 1.0 + log_scaling_alpha * ((pos.float() + 1.0) * (1.0 / log_scaling_n_floor)).maximum(1.0).log()
      q, r = q * tau.reshape(1, S, 1, 1), r * tau.reshape(1, S, 1, 1)

    k, v = self.wk_dv(hk), self.wv_dv(hv)
    if self.full:
      k = self.k_sconv(k, history(cache.k_conv, k, start_pos), hk)
      v = self.v_sconv(v, history(cache.v_conv, v, start_pos), hv)
    else:
      k = self.k_sconv(k, history(cache.k_conv, k, start_pos))
      v = self.v_sconv(v, history(cache.v_conv, v, start_pos))
    k = l2clip(k.reshape(B, S, n_kv_heads, head_dim), qk_clip).transpose(1, 2)
    v = rms(v.reshape(B, S, n_kv_heads, head_dim)).transpose(1, 2)

    st_k = cache.kv[0, :B, :, start_pos:start_pos + S, :].uop.store(k.cast(cache_dtype).uop)
    st_v = cache.kv[1, :B, :, start_pos:start_pos + S, :].uop.store(v.cast(cache_dtype).uop)
    kv = Tensor.from_uop(cache.kv.uop.after(st_k, st_v))
    k, v = kv[0, :B, :, :T, :], kv[1, :B, :, :T, :]

    # relative bias band: band[s, c] is the bias of query s for key start_pos - (E - 1) + c, c in [0, S + E - 1)
    E = rel_extent
    q, r = q.transpose(1, 2), r.transpose(1, 2)  # (B, H, S, .)
    band = skew(mm(r, self.rel_logits_proj.proj.T))  # (B, H, S, S + E - 1)

    if self.full:
      # every key up to T: the band left-padded by start_pos + 1 and cut at E covers keys [0, T), zero beyond the extent
      bias = band.pad((None, None, None, (start_pos + 1, 0)))[..., E:]
      t = Tensor.arange(max_seq_len)[:T]
    else:
      # only the window's keys, [start_pos - (W - 1), T), left-padded with zero keys (masked) before position 0
      assert sliding_window == E, "the band is the window when the window equals the relative extent"
      pad = (None, None, (sliding_window - 1, 0), None)
      k, v = k.pad(pad)[:, :, start_pos:], v.pad(pad)[:, :, start_pos:]
      bias = band
      t = Tensor.arange(S + sliding_window - 1) + (start_pos - (sliding_window - 1))
    dist = pos.reshape(S, 1) - t.reshape(1, -1)  # (S, keys)
    hidden = dist < 0
    if not self.full: hidden = hidden | (dist >= sliding_window) | (t < 0).reshape(1, -1)

    k = k.repeat_interleave(n_heads // n_kv_heads, 1)
    v = v.repeat_interleave(n_heads // n_kv_heads, 1)
    scores = q.matmul(k.transpose(-2, -1), dtype=dtypes.float32) / math.sqrt(head_dim) + bias  # (B, H, S, keys)
    scores = hidden.where(float("-inf"), scores)

    # attention sink: one extra per-head, per-query logit that takes probability mass but has no value
    sink = self.attn_sink_proj(hq).transpose(1, 2).unsqueeze(-1)  # (B, H, S, 1)
    n_keys = scores.shape[-1]
    attn = scores.cat(sink, dim=-1).softmax(-1)[..., :n_keys]
    out = attn.matmul(v, dtype=dtypes.float32).transpose(1, 2).reshape(B, S, n_heads * head_dim)
    return self.wo_ud(out * self.gate_attn(hq).sigmoid())

class MoE:
  def __init__(self):
    self.gate = Holder(weight=(n_experts, emb_dim), bias=(n_experts,))
    self.experts = Holder(w13_weight=(n_experts, 2 * expert_size, emb_dim), w2_weight=(n_experts, emb_dim, expert_size))

  def __call__(self, h: Tensor) -> Tensor:
    B, S, D = h.shape
    k = n_experts_per_tok
    scores = mm(h, self.gate.weight).sigmoid()  # (B, S, E)

    # top-k of the biased scores: k rounds of argmax, masking each pick
    sel, picks = scores + self.gate.bias.float(), []
    for _ in range(k):
      hot = sel.argmax(-1, keepdim=True).eq(Tensor.arange(n_experts))  # (B, S, E)
      picks.append(hot)
      sel = hot.where(float("-inf"), sel)
    hot = picks[0].stack(*picks[1:], dim=-2)  # (B, S, k, E)

    w = hot.where(scores.unsqueeze(-2), 0.0).sum(-1)  # unbiased scores of the picks, (B, S, k)
    w = w / (w.sum(-1, keepdim=True) + 1e-20) * route_scale

    if B * S * k < n_experts:
      # few tokens (decode): gather only the picked experts' weights, one-hot masked sums over the expert axis (exact)
      sel_w = hot.reshape(B, S, k, n_experts, 1, 1)
      w13 = sel_w.where(self.experts.w13_weight, 0.0).sum(-3)  # (B, S, k, 2I, D)
      w2 = sel_w.where(self.experts.w2_weight, 0.0).sum(-3)  # (B, S, k, D, I)
      gu = (h.float().reshape(B, S, 1, 1, D) * w13.float()).sum(-1).reshape(B, S, k, expert_size, 2)
      y = (self._act(gu).reshape(B, S, k, 1, expert_size) * w2.float()).sum(-1)  # (B, S, k, D)
      return (y * w.unsqueeze(-1)).sum(-2)

    # many tokens (prefill): every expert as one batched GEMM over all tokens, so each expert's weights are read once,
    # weighted by the routing weight (exactly zero for experts a token didn't pick)
    dense_w = hot.where(w.unsqueeze(-1), 0.0).sum(-2)  # (B, S, E)
    x = h.float().reshape(B, 1, S, D)
    gu = x.matmul(self.experts.w13_weight.transpose(-1, -2), dtype=dtypes.float32)  # (B, E, S, 2I)
    gu = gu.reshape(B, n_experts, S, expert_size, 2)
    y = self._act(gu).matmul(self.experts.w2_weight.transpose(-1, -2), dtype=dtypes.float32)  # (B, E, S, D)
    return (y * dense_w.permute(0, 2, 1).unsqueeze(-1)).sum(1)

  @staticmethod
  def _act(gu: Tensor) -> Tensor:
    """softcapped SwiGLU of interleaved (gate, up) pairs on the last axis"""
    g, u = gu[..., 0], gu[..., 1]
    return (g / gate_softcap).tanh() * gate_softcap * g.sigmoid() * (u / up_softcap).tanh() * up_softcap

class Layer:
  def __init__(self, i: int):
    self.i, self.full = i, i in full_layers
    if self.full:
      self.q_input_norm, self.k_input_norm, self.v_input_norm = RMSNorm(emb_dim), RMSNorm(emb_dim), RMSNorm(emb_dim)
    else:
      self.attn_norm = RMSNorm(emb_dim)
    self.attn = Attention(self.full)
    self.attn_sconv = ShortConv(emb_dim)
    self.mlp_norm = RMSNorm(emb_dim)
    self.mlp = MoE()
    self.mlp_sconv = ShortConv(emb_dim)
    looped = loop_start <= i < loop_end
    self.controllers = Holder() if looped else None
    if looped:
      for n in ("attn", "k", "v", "mlp"): setattr(self.controllers, n, Controller())
    self.caches = [Cache() for _ in range(n_passes if looped else 1)]

  def __call__(self, x: Tensor, blocks: list[Tensor], start_pos: sint, attn_query: Tensor | None, mlp_query: Tensor,
               p: int = 0, messages: list[Tensor] | None = None) -> Tensor:
    cache = self.caches[p]
    @function(allow_implicit=True)
    def _layer(x: Tensor, blocks: list[Tensor], start_pos: sint, messages: list[Tensor] | None) -> Tensor:
      ctrl = self.controllers
      # attention inputs: sliding layers mix one, full layers one each for q, k and v
      hs = mix(blocks, x, attn_query) if attn_query is not None else [x]
      hs = hs * 3 if len(hs) == 1 else hs
      if messages is not None:
        assert ctrl is not None
        hs = [getattr(ctrl, n)(h, m) for h, m, n in zip(hs, messages, ("attn", "k", "v"))]
      if self.full:
        hq, hk, hv = self.q_input_norm(hs[0]), self.k_input_norm(hs[1]), self.v_input_norm(hs[2])
      elif messages is None:
        hq = hk = hv = self.attn_norm(hs[0])
      else:
        hq, hk, hv = (self.attn_norm(h) for h in hs)

      a = self.attn(hq, hk, hv, cache, start_pos)
      a = self.attn_sconv(a, history(cache.attn_conv, a, start_pos))

      # the first layer of each block starts a new residual stream; its input joins the mixed blocks
      if self.i % block_size == 0: blocks, residual = blocks + [x], a
      else: residual = x + a

      h = mix(blocks, residual, mlp_query)[0]
      if messages is not None:
        assert ctrl is not None
        h = ctrl.mlp(h, messages[3])
      h = self.mlp(self.mlp_norm(h))
      return residual + self.mlp_sconv(h, history(cache.mlp_conv, h, start_pos))
    return _layer(x, blocks, start_pos, messages)

class Model:
  def __init__(self):
    self.embed = Embedding(vocab_size, emb_dim)
    self.embed_norm = RMSNorm(emb_dim)
    self.layers = [Layer(i) for i in range(n_layers)]
    self.attn_res = Holder(output_query=(emb_dim,))
    self.attn_res.attn_queries = [Tensor.empty(3 if i in full_layers else 1, emb_dim, dtype=dtypes.bfloat16) for i in range(1, n_layers)]
    self.attn_res.mlp_queries = [Tensor.empty(emb_dim, dtype=dtypes.bfloat16) for _ in range(n_layers)]
    self.middle_cycle_cross_pass_queries = Tensor.empty(n_loop, 2, emb_dim, dtype=dtypes.bfloat16)  # (attn, mlp)
    self.middle_cycle_cross_pass_kv_queries = Tensor.empty(n_loop, 2, emb_dim, dtype=dtypes.bfloat16)  # (k, v)
    self.norm = RMSNorm(emb_dim)
    self.unembed = Linear(emb_dim, vocab_size)

  def run(self, i: int, x: Tensor, blocks: list[Tensor], start_pos: sint, p: int = 0,
          messages: list[Tensor] | None = None) -> tuple[Tensor, list[Tensor]]:
    attn_query = self.attn_res.attn_queries[i - 1] if i > 0 else None
    y = self.layers[i](x, blocks, start_pos, attn_query, self.attn_res.mlp_queries[i], p, messages)
    return y, blocks + [x] if i % block_size == 0 else blocks

  def forward(self, tokens: Tensor, start_pos: sint = 0) -> Tensor:
    x = self.embed_norm(self.embed(tokens))
    blocks: list[Tensor] = []
    for i in range(loop_start): x, blocks = self.run(i, x, blocks, start_pos)
    pre_x, pre_blocks = x, blocks
    for i in range(loop_start, loop_end): x, blocks = self.run(i, x, blocks, start_pos)

    # passes 2..n rerun the loop from its input, each layer gated by messages mixed from the previous pass's states
    q, kvq = self.middle_cycle_cross_pass_queries, self.middle_cycle_cross_pass_kv_queries
    message_queries = q[:, :1].cat(kvq, q[:, 1:], dim=1)  # (loop layer, (attn, k, v, mlp), D)
    for p in range(1, n_passes):
      prev_blocks, prev_x = blocks[len(pre_blocks) + 1:], x
      x, blocks = pre_x, pre_blocks
      for j, i in enumerate(range(loop_start, loop_end)):
        x, blocks = self.run(i, x, blocks, start_pos, p, mix(prev_blocks, prev_x, message_queries[j]))

    for i in range(loop_end, n_layers): x, blocks = self.run(i, x, blocks, start_pos)

    h = self.norm(mix([b[:, -1:] for b in blocks], x[:, -1:], self.attn_res.output_query)[0])
    logits = mm(h, self.unembed.weight[:unpadded_vocab_size])  # the padded vocab rows are never scored
    logits = (logits / logit_softcap).tanh() * logit_softcap
    return logits.flatten().argmax()

  def __call__(self, x: Tensor, start_pos: sint = 0) -> Tensor:
    if x.shape[1] == 1 and isinstance(start_pos, int) and start_pos != 0:
      sp = Variable("start_pos", 1, max_seq_len - 1).bind(start_pos)
      return self.forward(x.contiguous(), sp)
    return self.forward(x, start_pos)

if __name__ == "__main__":
  mode = sys.argv[1] if len(sys.argv) > 1 else "decode"
  m = Model()
  if mode in ("prefill", "prefill-body"):
    g = simplify_tensor(m(Tensor([[200005, 791, 9029, 328, 10128, 382]], dtype=dtypes.i32), start_pos=0))
  elif mode in ("decode", "body"):
    sp = Variable("start_pos", 1, max_seq_len - 1)
    g = simplify_tensor(m(Tensor.buffer("tok", (1, 1), dtypes.i32), start_pos=sp))
  else:
    raise SystemExit(f"usage: {sys.argv[0]} [decode|prefill|body|prefill-body]")
  root = next(u.body for u in g.uop.toposort() if u.op is Ops.CALL) if "body" in mode else g.uop
  print(render_uir(root, color=sys.stdout.isatty()))
