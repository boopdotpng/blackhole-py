from __future__ import annotations
import sys
from pathlib import Path
if __name__ == "__main__": sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from compiler import Ops, Tensor, Variable, dtypes, function, load_state_dict, render_uir, safe_load, simplify_tensor, sint

# Nanbeige4.3-33B config (a plain Llama: LlamaForCausalLM, untied lm_head, no rope scaling)
emb_dim = 7168
n_layers = 52
n_heads = 56
n_kv_heads = 8
head_dim = 128
mlp_size = 22016

vocab_size = 166912
norm_eps = 1e-5
max_seq_len = 8192  # the checkpoint allows 524288; the RoPE table and KV cache are sized to this

rope_theta = 120000000.0

def rope_table() -> tuple[Tensor, Tensor]:
  inv_freq = 1.0 / (rope_theta ** (Tensor.arange(0, head_dim, 2) / head_dim))
  angles = Tensor.arange(max_seq_len).unsqueeze(1) * inv_freq.unsqueeze(0)
  angles = angles.repeat(1, 2)
  return angles.cos().contiguous(), angles.sin().contiguous()

COS, SIN = rope_table()  # both (8192, 128)

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
    self.materialize = False
  def __call__(self, x: Tensor) -> Tensor:
    out = (x.contiguous() if self.materialize else x) @ self.weight.T
    out = out if self.bias is None else out + self.bias
    return out.contiguous() if self.materialize else out

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
    self.materialize = False

  def _init_cache(self) -> None:
    if self.kv_cache is None:
      self.kv_cache = Tensor.empty(2, 1, n_kv_heads, max_seq_len, head_dim, dtype=dtypes.bfloat16)

  def __call__(self, x: Tensor, start_pos: sint = 0) -> Tensor:
    def boundary(value): return value.contiguous() if self.materialize else value
    B, S, _ = x.shape
    q = self.q_proj(x).reshape(B, S, n_heads, head_dim).transpose(1, 2)
    k = self.k_proj(x).reshape(B, S, n_kv_heads, head_dim).transpose(1, 2)
    v = self.v_proj(x).reshape(B, S, n_kv_heads, head_dim).transpose(1, 2)

    q = boundary(apply_rope(q, start_pos))
    k = boundary(apply_rope(k, start_pos))

    self._init_cache()
    assert self.kv_cache is not None
    st_k = self.kv_cache[0, :B, :, start_pos:start_pos + S, :].uop.store(k.cast(dtypes.bfloat16).uop)
    st_v = self.kv_cache[1, :B, :, start_pos:start_pos + S, :].uop.store(v.cast(dtypes.bfloat16).uop)
    kv = Tensor.from_uop(self.kv_cache.uop.after(st_k, st_v))

    fixed_decode = self.materialize and not isinstance(start_pos, int) and S == 1
    T = start_pos.vmax + 1 if fixed_decode else start_pos + S
    k = kv[0, :B, :, :T, :]
    v = kv[1, :B, :, :T, :]
    if fixed_decode:
      # A fixed extent lets all decode positions share native code. Mask the
      # unused cache before either matmul, including uninitialized V entries.
      valid = (Tensor.arange(T) < start_pos + S).reshape(1, 1, T, 1)
      k, v = valid.where(k, 0), valid.where(v, 0)

    k = boundary(k.repeat_interleave(n_heads // n_kv_heads, 1))
    v = boundary(v.repeat_interleave(n_heads // n_kv_heads, 1))

    scores = boundary(q.matmul(k.transpose(-2, -1), dtype=dtypes.float32))
    scores = scores * (head_dim ** -0.5)

    if S != 1 or fixed_decode:
      # key t is visible to query s iff t <= start_pos + s
      future = (Tensor.arange(T).reshape(1, T) - Tensor.arange(S).reshape(S, 1)) > start_pos
      scores = boundary(future.where(float("-inf"), scores))

    attn = boundary(scores.cast(q.dtype).softmax(-1))
    out = boundary(attn @ v)
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
  def __init__(self, layers: int = n_layers, *, materialize: bool = False):
    self.embed_tokens = Embedding(vocab_size, emb_dim)
    self.layers = [Block() for _ in range(layers)]
    self.norm = RMSNorm(emb_dim, eps=norm_eps)
    self.lm_head = Linear(emb_dim, vocab_size, bias=False)
    self._decode_graph = None
    # The native execution path currently materializes projection and
    # attention boundaries. Keep the fully fused graph available for IR work.
    self.lm_head.materialize = materialize
    for layer in self.layers:
      layer.self_attn.materialize = materialize
      for module in (layer.self_attn, layer.mlp):
        for value in vars(module).values():
          if isinstance(value, Linear): value.materialize = materialize

  def reset_cache(self) -> None:
    self._decode_graph = None
    for layer in self.layers:
      if layer.self_attn.kv_cache is not None:
        layer.self_attn.kv_cache.uop = layer.self_attn.kv_cache.uop.storage_base

  def hidden(self, x: Tensor, start_pos: sint = 0) -> Tensor:
    x = self.embed_tokens(x)
    for layer in self.layers: x = layer(x, start_pos)
    return x

  def logits(self, x: Tensor, start_pos: sint = 0) -> Tensor:
    x = self.hidden(x, start_pos)
    x = self.norm(x[:, -1:])
    return self.lm_head(x)

  def forward(self, x: Tensor, start_pos: sint = 0) -> Tensor:
    return self.logits(x, start_pos).flatten().argmax()

  def __call__(self, x: Tensor, start_pos: sint = 0) -> Tensor:
    if x.shape[1] == 1 and isinstance(start_pos, int) and start_pos != 0:
      # Reuse code for a face-sized position bucket without reading the
      # entire context capacity during early decode.
      first = max(1, start_pos // 16 * 16)
      last = min(max_seq_len, (start_pos // 16 + 1) * 16) - 1
      sp = Variable("start_pos", first, last)
      if self.lm_head.materialize:
        key = x.shape, x.dtype, first, last
        if self._decode_graph is None or self._decode_graph[0] != key:
          tokens = Tensor.buffer(f"decode_tokens_{id(self)}", x.shape, x.dtype)
          self._decode_graph = key, tokens.uop, self.forward(tokens.contiguous(), sp).uop
        _, tokens, graph = self._decode_graph
        return Tensor.from_uop(graph.substitute({tokens: x.uop, sp: sp.bind(start_pos)}))
      return self.forward(x.contiguous(), sp.bind(start_pos))
    return self.forward(x, start_pos)

def convert_from_huggingface_for_this_model(weights: dict[str, Tensor]) -> dict[str, Tensor]:
  return {
    (k[len("model."):] if k.startswith("model.") else k): v
    for k, v in weights.items()
  }

def load_nanbeige(checkpoint: str | Path, layers: int = n_layers, *, materialize: bool = True) -> Model:
  weights = convert_from_huggingface_for_this_model(safe_load(checkpoint))
  model = Model(layers=layers, materialize=materialize)
  load_state_dict(model, weights, strict=False)
  return model

def main():
  import argparse
  import json
  import time
  from tokenizers import Tokenizer
  from device import Device
  global max_seq_len, COS, SIN
  # Keep the IR inspection entry points available alongside inference.
  if len(sys.argv) > 1 and sys.argv[1] in ("decode", "prefill", "body", "prefill-body"):
    mode = sys.argv[1]
    model = Model()
    if mode in ("prefill", "prefill-body"):
      graph = simplify_tensor(model(Tensor([[166100, 1782, 6722, 315, 9625, 374]], dtype=dtypes.i32), start_pos=0))
    else:
      graph = simplify_tensor(model(Tensor.buffer("tok", (1, 1), dtypes.i32), start_pos=Variable("start_pos", 1, max_seq_len - 1)))
    root = next(u.body for u in graph.uop.toposort() if u.op is Ops.CALL) if "body" in mode else graph.uop
    print(render_uir(root, color=sys.stdout.isatty()))
    return
  parser = argparse.ArgumentParser(description="Run the mixed-precision Nanbeige checkpoint with the native Blackhole compiler.")
  parser.add_argument("--checkpoint", type=Path, default=Path(__file__).resolve().parents[2] / "weights/nanbeige4.3-33b/mixed_bfp4mlp_bfp8attn/model.safetensors")
  parser.add_argument("--device", type=int, choices=(0, 1), default=0)
  parser.add_argument("--prompt", default="The capital of France is")
  parser.add_argument("--input-ids", type=int, nargs="+")
  parser.add_argument("--tokens", type=int, default=8)
  parser.add_argument("--layers", type=int, default=n_layers, help="use fewer layers for compiler validation")
  parser.add_argument("--context", type=int, help="KV capacity; defaults to the next power of two covering this run")
  parser.add_argument("--timing", action="store_true")
  parser.add_argument("--json", action="store_true", help="emit token IDs and timings as JSON")
  args = parser.parse_args()
  if args.tokens < 1 or not 1 <= args.layers <= n_layers: parser.error("tokens must be positive and layers must be in 1..52")
  tokenizer = Tokenizer.from_file(str(args.checkpoint.parent / "tokenizer.json"))
  ids = args.input_ids or tokenizer.encode(args.prompt, add_special_tokens=False).ids
  if not ids or any(not 0 <= token < vocab_size for token in ids): parser.error("expected nonempty, in-vocabulary input IDs")
  needed = len(ids) + args.tokens - 1
  max_seq_len = args.context or max(32, 1 << (needed - 1).bit_length())
  if not needed <= max_seq_len <= 8192: parser.error("context must cover the run and be at most 8192")
  COS, SIN = rope_table()
  generation = args.checkpoint.parent / "generation_config.json"
  eos = json.loads(generation.read_text()).get("eos_token_id", []) if generation.exists() else []
  eos = set(eos if isinstance(eos, list) else [eos])
  model = load_nanbeige(args.checkpoint, layers=args.layers)
  dev = Device(args.device)
  generated, timings = [], []
  started = time.perf_counter()
  try:
    COS.realize(device=dev)
    SIN.realize(device=dev)
    for position, token in enumerate(ids[:-1]):
      model.hidden(Tensor([[token]], dtype=dtypes.i32), position).realize(device=dev)
    token = ids[-1]
    for position in range(len(ids) - 1, needed):
      before = time.perf_counter()
      token = int(model(Tensor([[token]], dtype=dtypes.i32), position).numpy(device=dev).item())
      timings.append(time.perf_counter() - before)
      generated.append(token)
      if args.timing: print(f"token {len(generated)}: {timings[-1]:.3f}s", file=sys.stderr, flush=True)
      if token in eos: break
    elapsed = time.perf_counter() - started
    text = tokenizer.decode(generated)
    warm = (len(timings) - 1) / sum(timings[1:]) if len(timings) > 1 else None
    if args.json:
      print(json.dumps(dict(input_ids=ids, generated_ids=generated, text=text, layers=args.layers, device=args.device,
                            context=max_seq_len, step_seconds=timings, total_seconds=elapsed, warm_tokens_per_second=warm)))
    else:
      print(text)
      if args.timing and warm is not None: print(f"{warm:.2f} warm tokens/s; {elapsed:.2f}s total", file=sys.stderr)
  finally: dev.close()


if __name__ == "__main__": main()
