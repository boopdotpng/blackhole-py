"""Qwen3.8-27B text decoder (Qwen3_5ForConditionalGeneration text_config), prefill and decode.

64 layers: every 4th is gated full attention (q/k RMSNorm, partial RoPE on the first 64 of 256 head dims, sigmoid output
gate, GQA 24:4), the other 48 are Gated DeltaNet linear attention (a causal depthwise conv over q/k/v, then per value head
a 128x128 fp32 memory updated by the gated delta rule, gated RMSNorm with silu(z)). SwiGLU MLP, untied lm_head. For
text the interleaved MRoPE sections all see the same position, so it is plain RoPE over the rotated dims.

Decode runs the delta rule one token at a time. Prefill runs it chunked (the WY form, as in FLA and HF's
torch_chunk_gated_delta_rule): within each 64-token chunk everything is matmuls, with the unit lower-triangular solve done
by recursive block inversion (log2(64) = 6 levels of batched matmuls), and only one state update per chunk is sequential.

Precision: weights are bf16; activations, matmul accumulations and outputs, the residual stream, the DeltaNet state and
conv state are fp32, and the KV cache is cache_dtype. Norm weights of the QwenRMSNorms are offsets from 1. The DeltaNet
conv state and memory are read and rewritten in place each call, so they must start zeroed.
"""
from __future__ import annotations
import math, sys
from pathlib import Path
if __name__ == "__main__": sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from compiler import Ops, Tensor, Variable, dtypes, function, render_uir, simplify_tensor, sint

# Qwen3.8-27B text_config
emb_dim = 5120
n_layers = 64
mlp_size = 17408
vocab_size = 248320
norm_eps = 1e-6
full_attention_interval = 4  # layers 3, 7, ..., 63

n_heads = 24
n_kv_heads = 4
head_dim = 256
rope_theta = 10000000.0
rotary_dim = 64  # partial_rotary_factor 0.25

lin_k_heads = 16
lin_v_heads = 48
lin_k_dim = 128
lin_v_dim = 128
conv_size = 4
chunk_size = 64

max_seq_len = 8192  # the checkpoint allows 262144; the RoPE table and KV cache are sized to this
cache_dtype = dtypes.float32

lin_key = lin_k_heads * lin_k_dim  # 2048
lin_value = lin_v_heads * lin_v_dim  # 6144
lin_conv = 2 * lin_key + lin_value  # 10240: q, k, v

def rms(x: Tensor, eps: float = norm_eps) -> Tensor:
  xf = x.float()
  return xf * (xf.square().mean(axis=-1, keepdim=True) + eps).rsqrt()

def l2norm(x: Tensor, eps: float = 1e-6) -> Tensor: return x * (x.square().sum(-1, keepdim=True) + eps).rsqrt()

# fp32 activations against bf16 weights, accumulated and returned in fp32
def mm(x: Tensor, weight: Tensor) -> Tensor: return x.float().matmul(weight.T, dtype=dtypes.float32)

def f32mm(a: Tensor, b: Tensor) -> Tensor: return a.matmul(b, dtype=dtypes.float32)

def rope_table() -> tuple[Tensor, Tensor]:
  inv_freq = 1.0 / (rope_theta ** (Tensor.arange(0, rotary_dim, 2) / rotary_dim))
  angles = Tensor.arange(max_seq_len).unsqueeze(1) * inv_freq.unsqueeze(0)
  angles = angles.repeat(1, 2)
  return angles.cos().contiguous(), angles.sin().contiguous()

COS, SIN = rope_table()  # both (8192, 64) fp32

def apply_rope(x: Tensor, pos: sint) -> Tensor:
  """rotate_half RoPE on the first rotary_dim dims of x (B, H, S, head_dim); the rest pass through."""
  S = x.shape[2]
  cos = COS[pos:pos + S].reshape(1, 1, S, rotary_dim)
  sin = SIN[pos:pos + S].reshape(1, 1, S, rotary_dim)
  x_rot, x_pass = x[..., :rotary_dim], x[..., rotary_dim:]
  rotated = (-x_rot[..., rotary_dim // 2:]).cat(x_rot[..., :rotary_dim // 2], dim=-1)
  return (x_rot * cos + rotated * sin).cat(x_pass, dim=-1)

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

class QwenRMSNorm:
  """RMSNorm whose weight is stored as an offset from 1."""
  def __init__(self, dim: int):
    self.weight = Tensor.empty(dim, dtype=dtypes.bfloat16)
  def __call__(self, x: Tensor) -> Tensor: return rms(x) * (1.0 + self.weight.float())

class GatedRMSNorm:
  """Per-head RMSNorm with a plain weight, gated by silu(z)."""
  def __init__(self, dim: int):
    self.weight = Tensor.empty(dim, dtype=dtypes.bfloat16)
  def __call__(self, x: Tensor, z: Tensor) -> Tensor: return rms(x) * self.weight * z.float().silu()

class MLP:
  def __init__(self):
    self.gate_proj = Linear(emb_dim, mlp_size)
    self.up_proj = Linear(emb_dim, mlp_size)
    self.down_proj = Linear(mlp_size, emb_dim)
  def __call__(self, x: Tensor) -> Tensor: return self.down_proj(self.gate_proj(x).silu() * self.up_proj(x))

class SelfAttention:
  def __init__(self):
    self.q_proj = Linear(emb_dim, n_heads * head_dim * 2)  # per head: query, then output gate
    self.k_proj = Linear(emb_dim, n_kv_heads * head_dim)
    self.v_proj = Linear(emb_dim, n_kv_heads * head_dim)
    self.o_proj = Linear(n_heads * head_dim, emb_dim)
    self.q_norm = QwenRMSNorm(head_dim)
    self.k_norm = QwenRMSNorm(head_dim)
    self.kv_cache = Tensor.empty(2, 1, n_kv_heads, max_seq_len, head_dim, dtype=cache_dtype)

  def __call__(self, x: Tensor, start_pos: sint) -> Tensor:
    B, S, _ = x.shape
    qg = self.q_proj(x).reshape(B, S, n_heads, 2 * head_dim)
    q, gate = qg[..., :head_dim], qg[..., head_dim:]
    k = self.k_proj(x).reshape(B, S, n_kv_heads, head_dim)
    v = self.v_proj(x).reshape(B, S, n_kv_heads, head_dim)

    q = apply_rope(self.q_norm(q).transpose(1, 2), start_pos)
    k = apply_rope(self.k_norm(k).transpose(1, 2), start_pos)
    v = v.transpose(1, 2)

    st_k = self.kv_cache[0, :B, :, start_pos:start_pos + S, :].uop.store(k.cast(cache_dtype).uop)
    st_v = self.kv_cache[1, :B, :, start_pos:start_pos + S, :].uop.store(v.cast(cache_dtype).uop)
    kv = Tensor.from_uop(self.kv_cache.uop.after(st_k, st_v))
    T = start_pos + S
    k = kv[0, :B, :, :T, :].repeat_interleave(n_heads // n_kv_heads, 1)
    v = kv[1, :B, :, :T, :].repeat_interleave(n_heads // n_kv_heads, 1)

    scores = f32mm(q, k.transpose(-2, -1)) / math.sqrt(head_dim)  # (B, H, S, T)
    if S != 1:
      # key t is visible to query s iff t <= start_pos + s
      future = (Tensor.arange(max_seq_len)[:T].reshape(1, T) - Tensor.arange(S).reshape(S, 1)) > start_pos
      scores = future.where(float("-inf"), scores)
    out = f32mm(scores.softmax(-1), v).transpose(1, 2)  # (B, S, H, head_dim)
    out = (out * gate.sigmoid()).reshape(B, S, n_heads * head_dim)
    return self.o_proj(out)

def tril_inverse(m: Tensor) -> Tensor:
  """(I + m)^-1 for strictly lower-triangular m (..., C, C), C a power of two, by recursive block inversion: the inverse
  of [[A, 0], [M, D]] is [[A^-1, 0], [-D^-1 M A^-1, D^-1]]. Each level merges pairs of inverted diagonal blocks, all of
  them in one batched matmul, so C = 64 takes 6 levels."""
  *lead, C, _ = m.shape
  inv = Tensor.ones(*lead, C, 1, 1)  # C inverted 1x1 diagonal blocks of I + m
  b = 1
  while b < C:
    n = C // (2 * b)
    # the lower-left b x b block of each 2b x 2b diagonal block of m: (row half 1, col half 0) on the block diagonal
    blocks = m.reshape(*lead, n, 2, b, n, 2, b)[..., :, 1, :, :, 0, :]  # (..., n, b, n, b)
    blocks = blocks.permute(*range(len(lead)), len(lead), len(lead) + 2, len(lead) + 1, len(lead) + 3)  # (..., n, n, b, b)
    off = blocks.reshape(*lead, n * n, b, b)[..., ::n + 1, :, :]  # diagonal (i, i) pairs, (..., n, b, b)
    pair = inv.reshape(*lead, n, 2, b, b)
    a, d = pair[..., 0, :, :], pair[..., 1, :, :]
    low = -f32mm(f32mm(d, off), a)
    top = a.pad(tuple(None for _ in range(len(lead) + 2)) + ((0, b),))
    inv = top.cat(low.cat(d, dim=-1), dim=-2)  # (..., n, 2b, 2b)
    b *= 2
  return inv.reshape(*lead, C, C)

def delta_rule_step(q: Tensor, k: Tensor, v: Tensor, g: Tensor, beta: Tensor, state: Tensor) -> tuple[Tensor, Tensor]:
  """One token: q, k (B, H, dk), v (B, H, dv), log-decay g and beta (B, H), state (B, H, dk, dv)."""
  state = state * g.exp().unsqueeze(-1).unsqueeze(-1)  # forget
  recall = f32mm(k.unsqueeze(-2), state).squeeze(-2)  # what the memory returns for k
  delta = (v - recall) * beta.unsqueeze(-1)  # delta rule: write only the error
  state = state + k.unsqueeze(-1) * delta.unsqueeze(-2)  # rank-1 update
  return f32mm(q.unsqueeze(-2), state).squeeze(-2), state

def delta_rule_chunked(q: Tensor, k: Tensor, v: Tensor, g: Tensor, beta: Tensor, state: Tensor) -> tuple[Tensor, Tensor]:
  """S tokens in chunks of chunk_size: q, k (B, H, S, dk), v (B, H, S, dv), g, beta (B, H, S), state (B, H, dk, dv).
  Padding tokens (k = v = 0, beta = 0, g = 0) at the end leave the outputs and the state unchanged."""
  B, H, S, dk = q.shape
  dv = v.shape[-1]
  C = chunk_size
  N = -(-S // C)
  pad = N * C - S
  def chunks(x: Tensor) -> Tensor:
    if pad: x = x.pad((None, None, (0, pad)) + tuple(None for _ in range(x.ndim - 3)))
    return x.reshape(B, H, N, C, *x.shape[3:])
  q, k, v, g, beta = chunks(q), chunks(k), chunks(v), chunks(g), chunks(beta)

  i = Tensor.arange(C)
  incl = i.reshape(C, 1) >= i.reshape(1, C)  # j <= i
  strict = i.reshape(C, 1) > i.reshape(1, C)  # j < i
  gc = incl.where(g.unsqueeze(-2), 0.0).sum(-1)  # cumulative log-decay within each chunk, (B, H, N, C)
  # decay from key j to query i (i >= j). Above the diagonal the exponent is positive and can overflow; clamping it to 0
  # keeps inf out even if the mask is lowered to a multiply
  decay = incl.where((gc.unsqueeze(-1) - gc.unsqueeze(-2)).minimum(0.0).exp(), 0.0)  # (B, H, N, C, C)

  kb, vb = k * beta.unsqueeze(-1), v * beta.unsqueeze(-1)
  t = tril_inverse(strict.where(f32mm(kb, k.transpose(-1, -2)) * decay, 0.0))  # WY: (I + strict(beta K K^T * decay))^-1
  u = f32mm(t, vb)  # (B, H, N, C, dv), the chunk's values with its own writes applied
  w = f32mm(t, kb * gc.exp().unsqueeze(-1))  # (B, H, N, C, dk), how much of the incoming state each row reads
  qg = q * gc.exp().unsqueeze(-1)  # queries reading the incoming state, decayed to their position
  intra = incl.where(f32mm(q, k.transpose(-1, -2)) * decay, 0.0)  # (B, H, N, C, C), causal within the chunk
  last = gc[..., -1:]  # (B, H, N, 1), the chunk's total log-decay
  kd = k * (last - gc).exp().unsqueeze(-1)  # keys decayed to the chunk end

  outs = []
  for n in range(N):  # one state update per chunk is the only sequential part
    v_new = u[:, :, n] - f32mm(w[:, :, n], state)
    outs.append(f32mm(qg[:, :, n], state) + f32mm(intra[:, :, n], v_new))
    state = state * last[:, :, n].exp().unsqueeze(-1) + f32mm(kd[:, :, n].transpose(-1, -2), v_new)
  o = outs[0].stack(*outs[1:], dim=2).reshape(B, H, N * C, dv)[:, :, :S]
  return o, state

class DepthwiseConv:
  """Causal depthwise conv1d weight (channels, 1, conv_size); tap conv_size - 1 is the current token."""
  def __init__(self, channels: int):
    self.weight = Tensor.empty(channels, 1, conv_size, dtype=dtypes.bfloat16)

class LinearAttention:
  """Gated DeltaNet."""
  def __init__(self):
    self.in_proj_qkv = Linear(emb_dim, lin_conv)
    self.in_proj_z = Linear(emb_dim, lin_value)
    self.in_proj_b = Linear(emb_dim, lin_v_heads)
    self.in_proj_a = Linear(emb_dim, lin_v_heads)
    self.conv1d = DepthwiseConv(lin_conv)
    self.A_log = Tensor.empty(lin_v_heads, dtype=dtypes.float32)
    self.dt_bias = Tensor.empty(lin_v_heads, dtype=dtypes.bfloat16)
    self.norm = GatedRMSNorm(lin_v_dim)
    self.out_proj = Linear(lin_value, emb_dim)
    self.conv_state = Tensor.empty(1, conv_size - 1, lin_conv, dtype=dtypes.float32)  # the last 3 pre-conv inputs
    self.state = Tensor.empty(1, lin_v_heads, lin_k_dim, lin_v_dim, dtype=dtypes.float32)

  def __call__(self, x: Tensor) -> Tensor:
    B, S, _ = x.shape
    qkv = self.in_proj_qkv(x)  # (B, S, lin_conv)
    z = self.in_proj_z(x).reshape(B, S, lin_v_heads, lin_v_dim)
    beta = self.in_proj_b(x).sigmoid()  # (B, S, Hv): how strongly each token writes
    # log-decay per token and head: -exp(A_log) * softplus(a + dt_bias), so the decay exp(g) is in (0, 1]
    g = -self.A_log.exp() * (self.in_proj_a(x) + self.dt_bias.float()).softplus()

    # causal depthwise conv over [3 previous inputs, this call's inputs], then silu
    window = self.conv_state[:B].cat(qkv, dim=1)  # (B, 3 + S, lin_conv)
    st_conv = self.conv_state[:B].uop.store(window[:, S:].uop)
    w = self.conv1d.weight.reshape(lin_conv, conv_size)
    qkv = sum((window[:, j:j + S] * w[:, j] for j in range(1, conv_size)), window[:, :S] * w[:, 0]).silu()

    q = qkv[..., :lin_key].reshape(B, S, lin_k_heads, lin_k_dim)
    k = qkv[..., lin_key:2 * lin_key].reshape(B, S, lin_k_heads, lin_k_dim)
    v = qkv[..., 2 * lin_key:].reshape(B, S, lin_v_heads, lin_v_dim)
    # unit keys (so a write at k reads back exactly at k), queries also get the attention 1/sqrt(dk)
    q = l2norm(q) / math.sqrt(lin_k_dim)
    k = l2norm(k)
    # each q/k head serves lin_v_heads // lin_k_heads consecutive value heads
    q = q.repeat_interleave(lin_v_heads // lin_k_heads, 2)
    k = k.repeat_interleave(lin_v_heads // lin_k_heads, 2)

    state = self.state[:B]
    if S == 1:
      o, state = delta_rule_step(q[:, 0], k[:, 0], v[:, 0], g[:, 0], beta[:, 0], state)
      o = o.unsqueeze(1)  # (B, 1, Hv, dv)
    else:
      o, state = delta_rule_chunked(q.transpose(1, 2), k.transpose(1, 2), v.transpose(1, 2),
                                    g.transpose(1, 2), beta.transpose(1, 2), state)
      o = o.transpose(1, 2)  # (B, S, Hv, dv)
    st_state = self.state[:B].uop.store(state.uop)

    o = self.norm(o, z).reshape(B, S, lin_value)
    # the output carries the conv and memory writes, so they're ordered before anything that uses this layer
    return Tensor.from_uop(self.out_proj(o).uop.after(st_conv, st_state))

class Block:
  def __init__(self, i: int):
    self.full = (i + 1) % full_attention_interval == 0
    self.input_layernorm = QwenRMSNorm(emb_dim)
    self.post_attention_layernorm = QwenRMSNorm(emb_dim)
    if self.full: self.self_attn = SelfAttention()
    else: self.linear_attn = LinearAttention()
    self.mlp = MLP()

  def __call__(self, x: Tensor, start_pos: sint = 0) -> Tensor:
    @function(allow_implicit=True)
    def _block(x: Tensor, start_pos: sint) -> Tensor:
      h = self.input_layernorm(x)
      x = x + (self.self_attn(h, start_pos) if self.full else self.linear_attn(h))
      return x + self.mlp(self.post_attention_layernorm(x))
    return _block(x, start_pos)

class LanguageModel:
  def __init__(self, layers: int = n_layers):
    self.embed_tokens = Embedding(vocab_size, emb_dim)
    self.layers = [Block(i) for i in range(layers)]
    self.norm = QwenRMSNorm(emb_dim)

class Model:
  def __init__(self, layers: int = n_layers):
    self.language_model = LanguageModel(layers)
    self.lm_head = Linear(emb_dim, vocab_size)

  def forward(self, tokens: Tensor, start_pos: sint = 0) -> Tensor:
    lm = self.language_model
    x = lm.embed_tokens(tokens).float()
    for layer in lm.layers: x = layer(x, start_pos)
    logits = self.lm_head(lm.norm(x[:, -1:]))
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
    g = simplify_tensor(m(Tensor([[248044, 785, 6722, 315, 9625, 374]], dtype=dtypes.i32), start_pos=0))
  elif mode in ("decode", "body"):
    sp = Variable("start_pos", 1, max_seq_len - 1)
    g = simplify_tensor(m(Tensor.buffer("tok", (1, 1), dtypes.i32), start_pos=sp))
  else:
    raise SystemExit(f"usage: {sys.argv[0]} [decode|prefill|body|prefill-body]")
  root = next(u.body for u in g.uop.toposort() if u.op is Ops.CALL) if "body" in mode else g.uop
  print(render_uir(root, color=sys.stdout.isatty()))
