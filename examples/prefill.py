"""Chunked prompt projection graphs. Chunks share the decode graph's per-layer KV buffers."""
from pathlib import Path
from time import perf_counter

import numpy as np
from ttrv import Var

HERE = Path(__file__).resolve().parent
MAX_CHUNK = 320
DEFAULT_CHUNK = MAX_CHUNK


def grouped_llama_weights(dev, tensors, cfg):
  """Tile the row-major Llama projections for the prompt matrix unit; retain the original decode buffers."""
  fp8 = "quantization_config" in cfg
  group, bits, dtype = (8, 8, "e4m3") if fp8 else (4, 16, "bf16")
  tables, projections = {}, {}
  for i in range(cfg["num_hidden_layers"]):
    layer = f"model.layers.{i}."
    for names in (("self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj"), ("self_attn.o_proj",),
                  ("mlp.gate_proj", "mlp.up_proj"), ("mlp.down_proj",)):
      mats = [tensors[layer + p + ".weight"].numpy() for p in names]
      widths = [m.shape[0] for m in mats]
      k, n = mats[0].shape[1], sum(widths)
      buf = dev.empty(n * k, dtype, tiles_per_page=group)
      offset = buf.addr
      for col in range(0, k, group * 32):
        for m in mats:
          strip = m[:, col:col + group * 32].reshape(-1, 2, 16, group, 2, 16).transpose(0, 3, 4, 1, 5, 2).copy()
          dev.dev.allocator._copyin(offset, strip)
          offset += strip.nbytes
      table = scales = None
      if fp8:
        def scale(name, kind): return np.float32(tensors[layer + name + "." + kind + "_scale"].numpy()[()])
        inp = scale(names[0], "input")
        if any(scale(p, "input") != inp for p in names):
          raise ValueError("fused FP8 projections require equal activation scales")
        if inp not in tables:
          # Exact map for BF16 input bits: scale, RNE to three fraction bits, saturate, flush subnormals.
          raw = np.arange(65536, dtype=np.uint32) << 16
          with np.errstate(invalid="ignore", over="ignore"):
            x = raw.view(np.float32) * (np.float32(1) / inp)
          u = x.view(np.uint32)
          mag = ((u & 0x7fffffff) + 0x7ffff + ((u >> 20) & 1)) >> 20
          code = np.clip(mag.astype(np.int32) - 120 * 8, 0, 126)
          code[mag < (121 * 8)] = 0
          tables[inp] = dev.array(((u >> 24 & 128) | code).astype(np.uint8), "e4m3")
        table = tables[inp]
        scales = dev.array(np.array([1/inp] + [inp * scale(p, "weight") for p in names] + [0]*(15-len(names)), np.float32))
      second, third = (widths + [0, 0])[1:3]
      projections[layer + names[0] + ".weight"] = (buf, k, n, bits, group, second, third, table, scales)
  return projections


class PromptChunks:
  def __init__(self, dev, cfg, capacity, weights, projections, caches, history, cos, sin):
    self.graphs = {}
    self.offsets = {}
    self.elapsed = 0.0
    dim, mlp = cfg["hidden_size"], cfg["intermediate_size"]
    kv, heads = cfg["num_key_value_heads"], cfg["num_attention_heads"]
    d = cfg.get("head_dim", dim // heads)
    def matrix(width):
      stride = (width + 1023) // 1024 * 1024
      buf = dev.empty(MAX_CHUNK * stride, "bf16")
      return buf, [buf.page_view(2 * row * stride, (MAX_CHUNK - row) * stride) for row in range(MAX_CHUNK)]

    x, norm, q, ctx = [matrix(dim) for _ in range(4)]
    k, v = matrix(kv * d), matrix(kv * d)
    gate, up, hidden = [matrix(mlp) for _ in range(3)]
    fp8 = "quantization_config" in cfg
    packed = dev.empty(max(dim, mlp) * MAX_CHUNK, "e4m3" if fp8 else "bf16")
    vector = HERE / "nanbeige/vector.ttrv"
    llama = HERE / "llama3"
    vectors, embeds = {}, {}
    def vector_rows(kind, src, other, dst, rows):
      width = mlp if kind == "swiglu" else dim
      lanes = min(rows, len(dev.dev.workers) // ((width + 1023) // 1024))
      for first in range(0, rows, lanes):
        size = min(rows - first, lanes)
        if (kind, size) not in vectors:
          vectors[kind, size] = dev.kernel(vector, DIM=width, RMS=int(kind == "rms"), EPS=cfg["rms_norm_eps"],
                                            SWIGLU=int(kind == "swiglu"), PACKED=0, ROW_LANES=size)
        vectors[kind, size](x=src[1][first], other=other if kind == "rms" else other[1][first], output=dst[1][first])
    attention = {}
    embedding_lanes = len(dev.dev.workers)
    attention_lanes = min(16, embedding_lanes // kv)
    def attend_rows(q, k, v, ctx, keys, values, positions, rows):
      for first in range(0, rows, attention_lanes):
        size = min(attention_lanes, rows - first)
        if size not in attention:
          attention[size] = dev.kernel(llama / "attention.ttrv", HEAD_TILES=d//32, KV_HEADS=kv, GROUP=heads//kv,
                                       MAX_TOKENS=capacity, PARTITIONS=1 if size > 1 else 8, PROMPT_ROWS=size)
        attention[size](q_in=q[1][first], k_in=k[1][first], v_in=v[1][first], cos=cos, sin=sin,
                        key_cache=keys, value_cache=values, context=ctx[1][first], start_pos=positions[first])
    pack, kernels = {}, {}

    def capture(rows):
      tile_rows = 16 if rows <= 16 else 32
      short = int(rows <= 8)
      panels = max(1, rows // 32)
      if rows > 32 and rows not in (64, 160, 320):
        raise ValueError("multicast groups contain two, five or ten full prompt panels")
      for width in (dim, mlp):
        if (width, tile_rows, panels) not in pack:
          pack_workers = min(panels * (width // 128), embedding_lanes)
          pack[width, tile_rows, panels] = dev.kernel(HERE / "prefill/pack.ttrv", K=width, WORKERS=pack_workers,
                                                       TILE_ROWS=tile_rows, FP8=int(fp8), PANELS=panels)
      for _, width, n, bits, group, second, third, _, _ in projections.values():
        key = width, n, bits, group, second, third, tile_rows, short, panels
        if key not in kernels:
          limit = embedding_lanes
          if panels < 5:
            limit = min(128 if panels == 2 and bits in (4, 8) and not fp8 else 96, embedding_lanes)
          workers = min(n // 32, limit // panels) * panels
          kernels[key] = dev.kernel(HERE / "nanbeige/projection.ttrv", K=width, N=n, BITS=bits, GROUP=group,
                                    SECOND=second, THIRD=third, WORKERS=workers, PREFILL=1, FP8=int(fp8),
                                    TILE_ROWS=tile_rows, SHORT_M=short, SHARE_A=1, PANELS=panels)
      def project(layer, name, src, dst, **outs):
        w, width, n, bits, group, second, third, table, scales = projections[layer + name + ".weight"]
        panel_rows = min(rows, 32)
        pack[width, tile_rows, panels](x=src[0], output=packed, rows=panel_rows, **({"quant": table} if fp8 else {}))
        kernel = kernels[width, n, bits, group, second, third, tile_rows, short, panels]
        outputs = {name: matrix[0] for name, matrix in outs.items()}
        kernel(x=packed, weights=w, output=dst[0], rows=panel_rows, **outputs, **({"scales": scales} if fp8 else {}))
      self.offsets[rows] = sorted(set(range(0, rows, embedding_lanes)) | set(range(0, rows, attention_lanes)))
      positions = {offset: Var(f"p{offset}") for offset in self.offsets[rows]}
      with dev.graph() as graph:
        for first in range(0, rows, embedding_lanes):
          size = min(rows - first, embedding_lanes)
          if size not in embeds:
            embeds[size] = dev.kernel(llama / "embedding.ttrv", EMBED_TILES=dim//1024, ROW_LANES=size)
          embeds[size](history=history, weights=weights["model.embed_tokens.weight"], output=x[1][first], token_pos=positions[first])
        for i, (keys, values) in enumerate(caches):
          layer = f"model.layers.{i}."
          vector_rows("rms", x, weights[layer+"input_layernorm.weight"], norm, rows)
          project(layer, "self_attn.q_proj", norm, q, output2=k, output3=v)
          attend_rows(q, k, v, ctx, keys, values, positions, rows)
          project(layer, "self_attn.o_proj", ctx, norm)
          vector_rows("add", norm, x, x, rows)
          vector_rows("rms", x, weights[layer+"post_attention_layernorm.weight"], norm, rows)
          project(layer, "mlp.gate_proj", norm, gate, output2=up)
          vector_rows("swiglu", gate, up, hidden, rows)
          project(layer, "mlp.down_proj", hidden, norm)
          vector_rows("add", norm, x, x, rows)
      return graph
    self.capture = capture

  def run(self, length, chunk_size=DEFAULT_CHUNK):
    if not 1 <= chunk_size <= MAX_CHUNK:
      raise ValueError(f"prefill chunk size must be between 1 and {MAX_CHUNK}")
    self.elapsed = 0.0
    start = 0
    while start < length:
      rows = min(chunk_size, length-start)
      if rows > 32:
        rows = next(size for size in (320, 160, 64, 32) if size <= rows)
      if rows not in self.graphs: self.graphs[rows] = self.capture(rows)
      begin = perf_counter()
      self.graphs[rows](**{f"p{r}":start+r for r in self.offsets[rows]}).wait()
      self.elapsed += perf_counter() - begin
      start += rows
