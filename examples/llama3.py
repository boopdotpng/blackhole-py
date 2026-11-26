from __future__ import annotations
import math, sys
from pathlib import Path
if __name__ == "__main__": sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from compiler import Ops, Tensor, Variable, dtypes, function, load_state_dict, render_uir, safe_load, simplify_tensor, sint

# Llama 3.2 1B config
emb_dim = 2048
n_layers = 16
n_heads = 32
n_kv_heads = 8
head_dim = 64
mlp_size = 8192

vocab_size = 128256
norm_eps = 1e-5
max_seq_len = 8192

# official Llama 3.2 1B RoPE params
rope_theta = 500000.0
rope_factor = 32.0
rope_low_freq_factor = 1.0
rope_high_freq_factor = 4.0
rope_original_max_position_embeddings = 8192

def rope_table() -> tuple[Tensor, Tensor]:
  inv_freq = 1.0 / (rope_theta ** (Tensor.arange(0, head_dim, 2) / head_dim))
  wavelen = 2 * math.pi / inv_freq
  cycles = rope_original_max_position_embeddings / wavelen
  smooth = ((cycles - rope_low_freq_factor) / (rope_high_freq_factor - rope_low_freq_factor)).clip(0.0, 1.0)
  inv_freq = inv_freq * ((1.0 / rope_factor) + smooth * (1.0 - (1.0 / rope_factor)))
  angles = Tensor.arange(max_seq_len).unsqueeze(1) * inv_freq.unsqueeze(0)
  angles = angles.repeat(1, 2)
  return angles.cos().contiguous(), angles.sin().contiguous()

COS, SIN = rope_table()  # both (8192, 64)

def apply_rope(x: Tensor, pos: sint) -> Tensor:
  S = x.shape[2]
  cos = COS[pos:pos + S].cast(x.dtype).reshape(1, 1, S, head_dim)
  sin = SIN[pos:pos + S].cast(x.dtype).reshape(1, 1, S, head_dim)
  x1 = x[..., :head_dim // 2]
  x2 = x[..., head_dim // 2:]
  rotated = (-x2).cat(x1, dim=-1)
  return x * cos + rotated * sin

class Linear:
  def __init__(self, in_features: int, out_features: int, bias: bool = False):
    self.weight = Tensor.empty(out_features, in_features, dtype=dtypes.bfloat16)
    self.bias = Tensor.empty(out_features, dtype=dtypes.bfloat16) if bias else None
  def __call__(self, x: Tensor) -> Tensor:
    out = x @ self.weight.T
    return out if self.bias is None else out + self.bias

class Embedding:
  def __init__(self, vocab: int, dim: int):
    self.weight = Tensor.empty(vocab, dim, dtype=dtypes.bfloat16)
  # one-hot rows selected by a masked sum over the vocab axis
  def __call__(self, idx: Tensor) -> Tensor:
    vocab, dim = self.weight.shape
    hot = idx.unsqueeze(-1).eq(Tensor.arange(vocab)).unsqueeze(-1)  # (..., vocab, 1)
    return hot.where(self.weight, 0.0).sum(-2)

class RMSNorm:
  def __init__(self, dim: int, eps: float = norm_eps):
    self.eps = eps
    self.weight = Tensor.empty(dim, dtype=dtypes.bfloat16)
  def __call__(self, x: Tensor) -> Tensor:
    dtype = x.dtype
    xf = x.float()
    x = (xf * (xf.square().mean(axis=-1, keepdim=True) + self.eps).rsqrt()).cast(dtype)
    return x * self.weight

class MLP:
  def __init__(self):
    self.gate_proj = Linear(emb_dim, mlp_size, bias=False)
    self.up_proj = Linear(emb_dim, mlp_size, bias=False)
    self.down_proj = Linear(mlp_size, emb_dim, bias=False)
  def __call__(self, x: Tensor) -> Tensor:
    gate = self.gate_proj(x)
    up = self.up_proj(x)
    hidden = gate.silu() * up
    return self.down_proj(hidden)

class Attention:
  def __init__(self):
    self.q_proj = Linear(emb_dim, head_dim * n_heads, bias=False)
    self.k_proj = Linear(emb_dim, head_dim * n_kv_heads, bias=False)
    self.v_proj = Linear(emb_dim, head_dim * n_kv_heads, bias=False)
    self.o_proj = Linear(n_heads * head_dim, emb_dim, bias=False)
    self.kv_cache: Tensor | None = None

  def _init_cache(self) -> None:
    if self.kv_cache is None:
      self.kv_cache = Tensor.empty(2, 1, n_kv_heads, max_seq_len, head_dim, dtype=dtypes.bfloat16)

  def __call__(self, x: Tensor, start_pos: sint = 0) -> Tensor:
    B, S, _ = x.shape
    q = self.q_proj(x).reshape(B, S, n_heads, head_dim).transpose(1, 2)
    k = self.k_proj(x).reshape(B, S, n_kv_heads, head_dim).transpose(1, 2)
    v = self.v_proj(x).reshape(B, S, n_kv_heads, head_dim).transpose(1, 2)

    q = apply_rope(q, start_pos)
    k = apply_rope(k, start_pos)

    self._init_cache()
    assert self.kv_cache is not None
    st_k = self.kv_cache[0, :B, :, start_pos:start_pos + S, :].uop.store(k.cast(dtypes.bfloat16).uop)
    st_v = self.kv_cache[1, :B, :, start_pos:start_pos + S, :].uop.store(v.cast(dtypes.bfloat16).uop)
    kv = Tensor.from_uop(self.kv_cache.uop.after(st_k, st_v))

    k = kv[0, :B, :, :start_pos + S, :]
    v = kv[1, :B, :, :start_pos + S, :]

    k = k.repeat_interleave(n_heads // n_kv_heads, 1)
    v = v.repeat_interleave(n_heads // n_kv_heads, 1)

    scores = q.matmul(k.transpose(-2, -1), dtype=dtypes.float32)
    scores = scores * (head_dim ** -0.5)

    T = start_pos + S
    if S != 1:
      # key t is visible to query s iff t <= start_pos + s
      future = (Tensor.arange(T).reshape(1, T) - Tensor.arange(S).reshape(S, 1)) > start_pos
      scores = future.where(float("-inf"), scores)

    attn = scores.cast(q.dtype).softmax(-1)
    out = attn @ v
    out = out.transpose(1, 2).reshape(B, S, n_heads * head_dim)
    return self.o_proj(out)

class Block:
  def __init__(self):
    self.mlp = MLP()
    self.post_attention_layernorm = RMSNorm(emb_dim, eps=norm_eps)
    self.input_layernorm = RMSNorm(emb_dim, eps=norm_eps)
    self.self_attn = Attention()

  def __call__(self, x: Tensor, start_pos: sint = 0) -> Tensor:
    self.self_attn._init_cache()
    @function(allow_implicit=True)
    def _block(x: Tensor, start_pos: sint) -> Tensor:
      x = x + self.self_attn(self.input_layernorm(x), start_pos)
      x = x + self.mlp(self.post_attention_layernorm(x))
      return x
    return _block(x, start_pos)

class Model:
  def __init__(self, layers: int = n_layers):
    self.embed_tokens = Embedding(vocab_size, emb_dim)
    self.layers = [Block() for _ in range(layers)]
    self.norm = RMSNorm(emb_dim, eps=norm_eps)

  def reset_cache(self) -> None:
    for layer in self.layers:
      if layer.self_attn.kv_cache is not None:
        layer.self_attn.kv_cache.uop = layer.self_attn.kv_cache.uop.storage_base

  def forward(self, x: Tensor, start_pos: sint = 0) -> Tensor:
    x = self.embed_tokens(x)
    for layer in self.layers: x = layer(x, start_pos)
    x = self.norm(x[:, -1:])
    logits = x @ self.embed_tokens.weight.T
    return logits.flatten().argmax()

  def __call__(self, x: Tensor, start_pos: sint = 0) -> Tensor:
    if x.shape[1] == 1 and isinstance(start_pos, int) and start_pos != 0:
      sp = Variable("start_pos", 1, max_seq_len - 1).bind(start_pos)
      return self.forward(x.contiguous(), sp)
    return self.forward(x, start_pos)

def convert_from_huggingface_for_this_model(weights: dict[str, Tensor]) -> dict[str, Tensor]:
  return {
    (k[len("model."):] if k.startswith("model.") else k): v
    for k, v in weights.items()
    if k != "lm_head.weight"
  }

def load_llama3(checkpoint: str | Path = "/Users/boop/code/ml/llama3-tinygrad/model.safetensors",
                layers: int = n_layers) -> Model:
  weights = convert_from_huggingface_for_this_model(safe_load(checkpoint))
  model = Model(layers=layers)
  load_state_dict(model, weights, strict=False)
  return model

if __name__ == "__main__":
  mode = sys.argv[1] if len(sys.argv) > 1 else "decode"
  m = Model()
  if mode in ("prefill", "prefill-body"):
    g = simplify_tensor(m(Tensor([[128000, 15339, 11, 1268, 527, 499]], dtype=dtypes.i32), start_pos=0))
  elif mode in ("decode", "body"):
    sp = Variable("start_pos", 1, max_seq_len - 1)
    g = simplify_tensor(m(Tensor.buffer("tok", (1, 1), dtypes.i32), start_pos=sp))
  else:
    raise SystemExit(f"usage: {sys.argv[0]} [decode|prefill|body|prefill-body]")
  root = next(u.body for u in g.uop.toposort() if u.op is Ops.CALL) if "body" in mode else g.uop
  print(render_uir(root, color=sys.stdout.isatty()))
