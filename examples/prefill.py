"""Chunked prompt projection graphs. Chunks share the decode graph's per-layer KV buffers."""
from pathlib import Path
from time import perf_counter

from ttrv import Var, hw
from ttrv.layout import ResidentCapacityError
from ttrv.parse import Error as TtrvError

HERE = Path(__file__).resolve().parent
MAX_CHUNK = 320
DEFAULT_CHUNK = MAX_CHUNK
# Rows of the whole-panel chunk graphs. 160 (five panels) gives non-finite logits; 640 (twenty panels) hangs in the
# fused gate/up SUMMA projection.
TILED_SHAPES = (64, 320)


def summa_shapes(k, n, bits, group, panels, swiglu, budget):
  """Shapes for prefill/summa_projection.ttrv, best first; empty where the kernel does not apply. ILEAVE=1 reads each
  activation once but gives every worker its column's other segments' weight buffers too; a slab must keep the
  matrix unit busy for at least 512 cycles per block (the packer adds each block's partial to L1 once per slab).
  budget: bytes of L1 for its buffers (the kernel's scratch starts about 97 KB in)."""
  # Five-panel SwiGLU runs as fast on projection.ttrv (the half-empty third block row costs the most there).
  if not 2 <= panels <= 20 or swiglu and panels % 2: return []
  halves = 2 if swiglu else 1
  if n % (64 * halves): return []
  segments = 10 // ((panels + 1) // 2)             # logical columns per physical one
  units = -(-(n // 64 // halves) // (13 * segments))
  blocks, kt, tile = units * halves, k // 32, {4: 576, 8: 1088, 16: 2048}[bits]
  shapes = []
  for ileave in (1, 0):
    copies = segments if ileave and panels > 2 else 1
    for sg in (8, 4, 16):
      if kt % sg or kt // sg < 2 or sg % group and group % sg or sg * tile > 16384 or sg * (32 if bits == 4 else 64) < 256:
        continue
      for slots in (4, 3, 2):
        if slots * (sg * 4096 + copies * blocks * 2 * sg * tile) + blocks * 16384 + units * 8192 <= budget:
          shapes.append(dict(SG=sg, NSLOT=slots, ILEAVE=ileave))
  return shapes


class PromptChunks:
  def __init__(self, dev, cfg, capacity, weights, projections, caches, history, cos, sin):
    self.graphs = {}
    self.target = caches, history  # retarget() switches the caches and history a chunk fills
    # phase: if set, each chunk shape's kernels and graphs live in their own worker L1 image (phase (phase, shape)),
    # so many shapes fit; switching images costs a few milliseconds.
    self.phase = None
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
    packed = dev.empty(max(dim, mlp) * MAX_CHUNK, "bf16")
    vector = HERE / "nanbeige/vector.ttrv"
    shared = HERE / "shared"
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
        if ("rows", size) not in attention:
          attention["rows", size] = dev.kernel(shared / "attention.ttrv", HEAD_TILES=d//32, KV_HEADS=kv,
                                               GROUP=heads//kv, MAX_TOKENS=capacity, PARTITIONS=1 if size > 1 else 8, PROMPT_ROWS=size)
        attention["rows", size](q_in=q[1][first], k_in=k[1][first], v_in=v[1][first], cos=cos, sin=sin,
                                key_cache=keys, value_cache=values, context=ctx[1][first], start_pos=positions[first])
    pack, kernels = {}, {}

    self.device = dev
    self.width = mlp

    def capture(rows, tiled):
      if tiled: return capture_tiled(rows)
      tile_rows = 16 if rows <= 16 else 32
      short = int(rows <= 8)
      panels = max(1, rows // 32)
      if rows > 32 and rows not in (64, 160, 320):
        raise ValueError("multicast groups contain two, five or ten full prompt panels")
      for width in (dim, mlp):
        if (width, tile_rows, panels) not in pack:
          pack_workers = min(panels * (width // 128), embedding_lanes)
          pack[width, tile_rows, panels] = dev.kernel(HERE / "prefill/pack.ttrv", K=width, WORKERS=pack_workers,
                                                       TILE_ROWS=tile_rows, PANELS=panels)
      for _, width, n, bits, group, second, third, *pad in projections.values():
        key = width, n, bits, group, second, third, tile_rows, short, panels, (pad or [0])[0]
        if key not in kernels:
          limit = embedding_lanes
          if panels < 5:
            limit = min(128 if panels == 2 and bits in (4, 8) else 96, embedding_lanes)
          workers = min(n // 32, limit // panels) * panels
          kernels[key] = dev.kernel(HERE / "nanbeige/projection.ttrv", K=width, N=n, BITS=bits, GROUP=group,
                                    SECOND=second, THIRD=third, WORKERS=workers, PREFILL=1, PAD=key[-1],
                                    TILE_ROWS=tile_rows, SHORT_M=short, SHARE_A=1, PANELS=panels)
      def project(layer, name, src, dst, **outs):
        w, width, n, bits, group, second, third, *pad = projections[layer + name + ".weight"]
        panel_rows = min(rows, 32)
        pack[width, tile_rows, panels](x=src[0], output=packed, rows=panel_rows)
        kernel = kernels[width, n, bits, group, second, third, tile_rows, short, panels, (pad or [0])[0]]
        outputs = {name: matrix[0] for name, matrix in outs.items()}
        kernel(x=packed, weights=w, output=dst[0], rows=panel_rows, **outputs)
      self.offsets[rows] = sorted(set(range(0, rows, embedding_lanes)) | set(range(0, rows, attention_lanes)))
      positions = {offset: Var(f"p{offset}") for offset in self.offsets[rows]}
      with dev.graph() as graph:
        for first in range(0, rows, embedding_lanes):
          size = min(rows - first, embedding_lanes)
          if size not in embeds:
            embeds[size] = dev.kernel(shared / "embedding.ttrv", EMBED_TILES=dim//1024, ROW_LANES=size)
          embeds[size](history=self.target[1], weights=weights["model.embed_tokens.weight"], output=x[1][first], token_pos=positions[first])
        for i, (keys, values) in enumerate(self.target[0]):
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

    # Whole 32-row panels from a 32-token block boundary: activations stay in panel tile layout (panel-major
    # 32x32 face-layout tiles), so projections read and write whole tiles, vector ops cover every row in one
    # launch, and attention runs once per layer over cache blocks.
    tile_kernels, gammas, tables = {}, {}, {}
    self.kernel_caches = vectors, embeds, attention, pack, kernels, tile_kernels  # per phase: cleared on a switch
    q_tiles = dev.empty(heads * (MAX_CHUNK // 32) * d * 32, "bf16")
    def tiled(width): return dev.empty(MAX_CHUNK * width, "bf16")
    xt, normt, ctxt, outt = tiled(dim), tiled(dim), tiled(heads * d), tiled(dim)
    qt, kt, vt = tiled(heads * d), tiled(kv * d), tiled(kv * d)
    hiddent = tiled(mlp)
    def tile_kernel(path, **defines):
      key = path, tuple(sorted(defines.items()))
      if key not in tile_kernels: tile_kernels[key] = dev.kernel(HERE / path, **defines)
      return tile_kernels[key]
    def to_tiles(src, width, stride, panels, block=128):  # row-major rows -> panel tiles, on the device
      out = dev.empty(panels * 32 * width, "bf16")
      tile_kernel("prefill/pack.ttrv", K=width, STRIDE=stride, BLOCK=block, PANELS=panels, TILE_ROWS=32,
                  WORKERS=min(panels * (width // block), embedding_lanes))(x=src, output=out, rows=32)
      return out
    def gamma(name):  # 32 identical rows: the norm weight as one panel of tiles
      if name not in gammas: gammas[name] = to_tiles(weights[name], dim, 0, 1)
      return gammas[name]
    def vector_tiles(op, x, other, out, width, panels):
      kt_ = width // 32
      if op == 2:
        peers = min(16, embedding_lanes // panels, kt_)
        workers = panels * peers
      else:
        peers, workers = 1, min(embedding_lanes, panels * kt_)
      tile_kernel("prefill/vector.ttrv", OP=op, PANELS=panels, KT=kt_, PEERS=peers, WORKERS=workers,
                  EPS=cfg["rms_norm_eps"])(x=x, other=other, output=out)

    def projection_shape(k, n, bits, panels):
      # Column groups of `panels` workers (one physical column each); blocks of 32 K tiles where they divide K, and
      # as many staged blocks as L1 holds next to the 32-row activation panel.
      # STAGES must be at least 3 (two staged blocks give run-to-run differences; see prefill/projection.ttrv).
      kt, tile = k // 32, {4: 576, 8: 1088, 16: 2048}[bits]
      batch = next(b for b in (32, 16, 8) if kt % b == 0)
      free = hw.L1_SIZE - dev.top - 64 * k - 2 * batch * tile - 8192   # L1 after the 32-row panel, the ring and the results
      while batch > 8 and free < 3 * batch * tile: batch //= 2; free = hw.L1_SIZE - dev.top - 64 * k - 2 * batch * tile - 8192
      stages = min(6, free // (batch * tile))
      if stages < 3: raise ResidentCapacityError(f"no room for three staged weight blocks at K={k}")
      return dict(WORKERS=min(n // 32, embedding_lanes // panels) * panels, BATCH=batch, STAGES=stages)  # n: output columns

    def capture_tiled(rows):
      panels = rows // 32
      if panels not in (1, 2, 5, 10):
        raise ValueError("multicast groups contain one, two, five or ten full prompt panels")
      if "cos" not in tables:  # one-time device tilizing, outside every graph
        tables["cos"], tables["sin"] = (to_tiles(t, d, d, capacity // 32, block=d) for t in (cos, sin))
        for i in range(len(caches)):
          for norm in ("input_layernorm", "post_attention_layernorm"): gamma(f"model.layers.{i}.{norm}.weight")
      def project(layer, name, src, dst, residual=None, swiglu=False, **outs):
        w, width, n, bits, group, second, third, *pad = projections[layer + name + ".weight"]
        epilogue = dict(SWIGLU=1) if swiglu else dict(SECOND=second, THIRD=third)
        if residual is not None: epilogue["RESIDUAL"], outs["residual"] = 1, residual
        # Two or more panels: 64x64 output blocks over a 2D grid (prefill/summa_projection.ttrv), with the largest
        # slab buffers that install next to the kernels already resident; else one output tile per worker and panel.
        for shape in summa_shapes(width, n, bits, group, panels, swiglu, hw.L1_SIZE - dev.top) if residual is None else ():
          try:
            kernel = tile_kernel("prefill/summa_projection.ttrv", K=width, N=n, BITS=bits, GROUP=group,
                                 PAD=(pad or [0])[0], PANELS=panels, **epilogue, **shape)
            break
          except (MemoryError, ValueError, TtrvError) as e:  # L1 taken by resident kernels' persistent storage: smaller slabs
            if isinstance(e, TtrvError) and e.id != "storage.overflow": raise
        else:
          kernel = tile_kernel("prefill/projection.ttrv", K=width, N=n, BITS=bits, GROUP=group, PAD=(pad or [0])[0],
                               PANELS=panels, **epilogue, **projection_shape(width, n // (2 if swiglu else 1), bits, panels))
        kernel(x=src, weights=w, output=dst, **outs)
      shape = dict(HEAD_TILES=d // 32, KV_HEADS=kv, GROUP=heads // kv, MAX_TOKENS=capacity, TILES_Q=panels)
      rope = tile_kernel("shared/prompt_rope.ttrv", WORKERS=min(embedding_lanes, panels * (heads + 2 * kv)), **shape)
      attend = tile_kernel("shared/prompt_attention.ttrv", WORKERS=min(embedding_lanes, panels * heads), **shape)
      self.offsets[rows] = list(range(0, rows, embedding_lanes))
      positions = {offset: Var(f"p{offset}") for offset in self.offsets[rows]}
      start = positions[0]
      with dev.graph() as graph:
        for first in range(0, rows, embedding_lanes):
          size = min(rows - first, embedding_lanes)
          if size not in embeds:
            embeds[size] = dev.kernel(shared / "embedding.ttrv", EMBED_TILES=dim//1024, ROW_LANES=size)
          embeds[size](history=self.target[1], weights=weights["model.embed_tokens.weight"], output=x[1][first], token_pos=positions[first])
        stride = (dim + 1023) // 1024 * 1024
        tile_kernel("prefill/pack.ttrv", K=dim, STRIDE=stride, BLOCK=128, PANELS=panels, TILE_ROWS=32,
                    WORKERS=min(panels * (dim // 128), embedding_lanes))(x=x[0], output=xt, rows=32)
        for i, (keys, values) in enumerate(self.target[0]):
          layer = f"model.layers.{i}."
          vector_tiles(2, xt, gamma(layer + "input_layernorm.weight"), normt, dim, panels)
          project(layer, "self_attn.q_proj", normt, qt, output2=kt, output3=vt)
          rope(q_in=qt, k_in=kt, v_in=vt, cos_tiles=tables["cos"], sin_tiles=tables["sin"], key_cache=keys,
               value_cache=values, q_tiles=q_tiles, start_pos=start)
          attend(q_tiles=q_tiles, key_cache=keys, value_cache=values, context=ctxt, start_pos=start)
          # The projection's RESIDUAL epilogue races with few staged blocks (see prefill/projection.ttrv); add apart.
          project(layer, "self_attn.o_proj", ctxt, outt)
          vector_tiles(0, outt, xt, xt, dim, panels)
          vector_tiles(2, xt, gamma(layer + "post_attention_layernorm.weight"), normt, dim, panels)
          project(layer, "mlp.gate_proj", normt, hiddent, swiglu=True)      # silu(gate) * up
          project(layer, "mlp.down_proj", hiddent, outt)
          vector_tiles(0, outt, xt, xt, dim, panels)
      return graph
    self.capture = capture

  def retarget(self, caches, history):
    """Fill these per-layer (keys, values) caches, laid out as the originals, and read tokens from this history.
    Graphs are captured once per target, so targets should be long-lived buffers."""
    self.target = caches, history

  def run(self, length, chunk_size=DEFAULT_CHUNK, start=0, serial_step=None, pad_to=None):
    """Process positions start .. length - 1; the caches already hold positions before start.
    pad_to: with the capacity of the caches, run whole tiled panels only: start from the 32-position block holding
    start (recomputing cached positions) and round the last chunk up, writing unused cache positions past length
    (decode overwrites each position before any query reads it; histories must be zero there)."""
    if not 1 <= chunk_size <= MAX_CHUNK:
      raise ValueError(f"prefill chunk size must be between 1 and {MAX_CHUNK}")
    self.elapsed = 0.0
    if pad_to is not None: start -= start % 32
    while start < length:
      rows = min(chunk_size, length-start)
      if pad_to is not None:
        # multi-panel shapes: a single 32-row panel's widest projection does not fit next to resident code, and
        # five panels (160 rows) give non-finite logits
        fits = [size for size in TILED_SHAPES if size <= min(chunk_size, pad_to - start)]
        if fits: rows = next((size for size in fits if size >= rows), fits[-1])
      if start % 32: rows = min(rows, 32 - start % 32)  # reach a block boundary, then whole panels
      elif rows > 32:
        rows = next(size for size in sorted(TILED_SHAPES + (32,), reverse=True) if size <= rows)
      # Partial panels stage 32 rows of the widest activation, which does not fit next to resident code: use 16.
      if rows % 32 and rows > 16: rows = 16
      key = rows, start % 32 == 0 and rows % 32 == 0
      target = key, id(self.target[0])
      if self.phase is not None and self.device.phase_name != (self.phase, key):
        self.device.activate((self.phase, key))
        for cache in self.kernel_caches: cache.clear()   # dev.kernel keeps each phase's kernels
      if target not in self.graphs:
        try:
          # A single output panel stages 32 BF16 rows of the widest activation.
          if rows == 32 and 64 * self.width >= hw.L1_SIZE - self.device.top:
            raise ResidentCapacityError("32-row projection panel exceeds worker scratch")
          self.graphs[target] = self.capture(*key)
        except (ResidentCapacityError, TtrvError) as e:
          if isinstance(e, TtrvError) and e.id != "storage.overflow": raise
          if rows > 1:
            chunk_size = min(16, rows // 2)
            continue
          if serial_step is None: raise
          begin = perf_counter()
          for pos in range(start, length): serial_step(pos=pos).wait()
          self.elapsed += perf_counter() - begin
          return
      begin = perf_counter()
      graph = self.graphs[key, id(self.target[0])]
      graph(**{name: start + int(name[1:]) for name in graph.graph.vars}).wait()  # p<offset> = position of that row
      self.elapsed += perf_counter() - begin
      start += rows
