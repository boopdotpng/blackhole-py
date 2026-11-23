"""Qwen3.8 prompt chunks of up to 320 positions in panel tile layout, on the single-sequence model's state buffers.

A chunk starts on a 32-position block boundary and covers PANELS 32-row panels (an even count, 2 to 10); positions
past the prompt's end pad the last panel and change no state. Activations stay in panel tiles (panel-major 32x32
face-layout tiles) from the embedding to the last residual add:
  projections     two-dimensional SUMMA (prefill/summa_projection.ttrv), gate/up fused with SwiGLU
  RMSNorm, add    prefill/vector.ttrv over all panels
  linear (48)     causal conv + SiLU, gated delta rule and gated RMSNorm (each head's four tiles per panel are one
                  RMSNorm "panel" of prefill/vector.ttrv, then silu(z) times it)
  full (16)       q/k RMSNorm, partial RoPE, KV append and causal attention with its output gate
Conv history, recurrent state and KV caches are the model's (examples/qwen38.py), so decode continues from them.
"""
from pathlib import Path
from time import perf_counter

import numpy as np

from ttrv import hw
from ttrv.runtime import Var
from ttrv.layout import ResidentCapacityError
from ttrv.parse import Error as TtrvError
from examples.prefill import summa_shapes

HERE = Path(__file__).resolve().parent
MAX_PANELS = 10
VH, CHANNELS = 48, 10240


def model_layers(m):
  """The single model's recipe, one dict of launch arguments (and projections in order) per layer."""
  layers, current, adds = [], [], 0
  for launch in m.recipe[1:]:
    current.append(launch)
    adds += m.kinds.get(launch[0]) == "add"
    if adds == 2: layers.append(current); current, adds = [], 0
  assert not current and len(layers) == m.cfg["num_hidden_layers"]
  out = []
  for layer in layers:
    d = {"projections": [(m.projections[k], a["weights"]) for k, a in layer if k in m.projections]}
    for k, a in layer:
      kind = m.kinds.get(k)
      if kind == "rms": d.setdefault("rms", []).append(a["other"])
      elif kind in ("conv", "state", "gated", "attention"): d[kind] = a
    out.append(d)
  return out


class QwenChunks:
  def __init__(self, model, timing=False):
    m, dev = model, model.history.device
    self.model, self.dev, self.timing = m, dev, timing
    self.layers = model_layers(m)
    cfg = m.cfg
    self.cfg, self.capacity = cfg, m.capacity
    dim, mlp = cfg["hidden_size"], cfg["intermediate_size"]
    heads, kv = cfg["num_attention_heads"], cfg["num_key_value_heads"]
    rows = 32 * MAX_PANELS
    self.dims = dim, mlp, heads, kv
    tiles = lambda width: dev.empty(rows * width, "bf16")
    def matrix(width): return dev.empty(rows * ((width + 1023) // 1024 * 1024), "bf16")
    self.x = matrix(dim)
    self.xt, self.normt, self.outt = tiles(dim), tiles(dim), tiles(dim)
    self.wide, self.zt, self.kt, self.vt, self.abt = tiles(heads * 512), tiles(VH * 128), tiles(1024), tiles(1024), tiles(128)
    self.mixedt, self.normedt, self.ctxt, self.hiddent = tiles(VH * 128), tiles(VH * 128), tiles(VH * 128), tiles(mlp)
    # row-major operands of the row kernels
    self.rows = {w: matrix(w) for w in (CHANNELS, 1024, VH * 128, heads * 512)}
    self.conv_rows, self.k_rows, self.v_rows = matrix(CHANNELS), matrix(1024), matrix(1024)
    self.graphs, self.kernels, self.gammas, self.measure = {}, {}, {}, {}
    self.elapsed = 0.0

  def kernel(self, path, **defines):
    key = self.dev.phase_name, path, tuple(sorted(defines.items()))
    if key not in self.kernels: self.kernels[key] = self.dev.kernel(HERE / path, **defines)
    return self.kernels[key]

  def capture(self, panels):
    dev, cfg, m = self.dev, self.cfg, self.model
    dim, mlp, heads, kv = self.dims
    rows = 32 * panels
    workers = len(dev.dev.workers)
    kernel = self.kernel
    def to_tiles(src, dst, width, row_stride, n=panels):
      kernel("prefill/pack.ttrv", K=width, STRIDE=row_stride, BLOCK=128, PANELS=n, TILE_ROWS=32,
             WORKERS=min(n * width // 128, workers))(x=src, output=dst, rows=32)
    def to_rows(src, dst, width):
      block = 128 if width % 128 == 0 else 32
      kernel("prefill/unpack.ttrv", N=width, PANELS=panels, BLOCK=block,
             WORKERS=min(workers, panels * width // block))(x=src, output=dst)
    def gamma(buf, width=dim):  # one panel of identical rows: the norm multiplier
      if (id(buf), dev.phase_name) not in self.gammas:
        t = dev.empty(32 * width, "bf16")
        to_tiles(buf, t, width, 0, 1)
        self.gammas[id(buf), dev.phase_name] = t
      return self.gammas[id(buf), dev.phase_name]
    def vector(op, a, b, out, width, n=panels):
      kt = width // 32
      if op == 2: peers = min(16, workers // n, kt); count = n * peers
      else: peers, count = 1, min(workers, n * kt)
      kernel("prefill/vector.ttrv", OP=op, PANELS=n, KT=kt, PEERS=peers, WORKERS=count, EPS=cfg["rms_norm_eps"])(
        x=a, other=b, output=out)
    def tiled(spec, weights, src, outputs, swiglu=False):
      k_, n, bits, group, second, third = spec
      epilogue = dict(SWIGLU=1) if swiglu else dict(SECOND=second, THIRD=third)
      for shape in summa_shapes(k_, n, bits, group, panels, swiglu, hw.L1_SIZE - dev.top - (96 << 10)):
        try:
          project = kernel("prefill/summa_projection.ttrv", K=k_, N=n, BITS=bits, GROUP=group, PAD=0, PANELS=panels,
                           **epilogue, **shape)
          break
        except (ResidentCapacityError, TtrvError) as e:
          if isinstance(e, TtrvError) and e.id != "storage.overflow": raise
      else: raise ResidentCapacityError(f"no SUMMA shape fits for {k_}x{n}")
      project(x=src, weights=weights, **dict(zip(("output", "output2", "output3"), outputs)))

    start = Var("start")
    lanes = min(rows, workers)
    for layer in self.layers:
      for g in layer["rms"]: gamma(g)
      if "gated" in layer: gamma(layer["gated"]["gamma"], 128)
    dev.synchronize()
    with dev.graph() as graph:
      for first in range(0, rows, lanes):
        size = min(lanes, rows - first)
        kernel("shared/embedding.ttrv", EMBED_TILES=dim // 1024, ROW_LANES=size)(
          history=m.history, weights=m.embedding, output=self.x.page_view(2 * first * dim, size * dim),
          token_pos=Var(f"row_{first}"))
      to_tiles(self.x, self.xt, dim, dim)
      for layer in self.layers:
        proj = layer["projections"]
        vector(2, self.xt, gamma(layer["rms"][0]), self.normt, dim)
        if "state" in layer:
          (qkvz, wq), (abspec, wab) = proj[:2]
          tiled(qkvz, wq, self.normt, [self.wide, self.zt])
          tiled(abspec, wab, self.normt, [self.abt])
          self.recurrent(layer, panels, start)
          # gated RMSNorm: per head and panel, four tiles normalized together, then silu(z) times them
          heads_panels = panels * VH
          per = min(workers, heads_panels)
          for first in range(0, heads_panels, per):
            n = min(per, heads_panels - first)
            view = lambda t: t.page_view(2 * first * 4 * 1024, n * 4 * 1024)
            vector(2, view(self.mixedt), gamma(layer["gated"]["gamma"], 128), view(self.normedt), 128, n)
          vector(1, self.zt, self.normedt, self.ctxt, VH * 128)
        else:
          spec, wq = proj[0]
          tiled(spec, wq, self.normt, [self.wide, self.kt, self.vt])
          self.attention(layer, panels, start)
        (ospec, wo), (upspec, wup), (downspec, wdown) = proj[-3:]
        tiled(ospec, wo, self.ctxt, [self.outt])
        vector(0, self.outt, self.xt, self.xt, dim)
        vector(2, self.xt, gamma(layer["rms"][1]), self.normt, dim)
        tiled(upspec, wup, self.normt, [self.hiddent], swiglu=True)
        tiled(downspec, wdown, self.hiddent, [self.outt])
        vector(0, self.outt, self.xt, self.xt, dim)
    self.to_tiles, self.to_rows = to_tiles, to_rows
    if self.timing:
      timings = graph.graph.enable_timing()
      def measure():
        from collections import Counter
        totals = Counter()
        for launch, ms in zip(graph.launches, timings()): totals[launch[0].name] += ms
        return totals
      self.measure[panels] = measure
    return graph

  # ---- the row-kernel paths (examples/qwen38_prefill.py's), panel tiles unpacked around them
  def recurrent(self, layer, panels, start):
    rows, workers = 32 * panels, len(self.dev.dev.workers)
    def to_rows(src, dst, width):
      block = 128 if width % 128 == 0 else 32
      self.kernel("prefill/unpack.ttrv", N=width, PANELS=panels, BLOCK=block,
                  WORKERS=min(workers, panels * width // block))(x=src, output=dst)
    qkv, ab, mixed = self.rows[CHANNELS], self.rows[1024], self.rows[VH * 128]
    to_rows(self.wide, qkv, CHANNELS)
    to_rows(self.abt, ab, 128)
    c, s = layer["conv"], layer["state"]
    self.kernel("qwen38/gdn_conv.ttrv", ROWS=rows)(qkv=qkv, taps=c["taps"], history=c["history"], output=self.conv_rows,
                                                   pos=start)
    self.kernel("qwen38/gdn_state.ttrv", ROWS=rows)(conv=self.conv_rows, ab=ab, dynamics=s["dynamics"], state=s["state"],
                                                    output=mixed, pos=start)
    self.kernel("prefill/pack.ttrv", K=VH * 128, STRIDE=VH * 128, BLOCK=128, PANELS=panels, TILE_ROWS=32,
                WORKERS=min(panels * VH, workers))(x=mixed, output=self.mixedt, rows=32)

  def attention(self, layer, panels, start):
    rows, workers = 32 * panels, len(self.dev.dev.workers)
    def to_rows(src, dst, width):
      block = 128 if width % 128 == 0 else 32
      self.kernel("prefill/unpack.ttrv", N=width, PANELS=panels, BLOCK=block,
                  WORKERS=min(workers, panels * width // block))(x=src, output=dst)
    q, ctx = self.rows[self.dims[2] * 512], self.rows[VH * 128]
    to_rows(self.wide, q, self.dims[2] * 512)
    to_rows(self.kt, self.k_rows, 1024)
    to_rows(self.vt, self.v_rows, 1024)
    a = layer["attention"]
    lanes = min(16, workers // 8)
    widths = {"q_in": 12288, "k_in": 1024, "v_in": 1024, "context": 6144}
    for first in range(0, rows, lanes):
      size = min(lanes, rows - first)
      call = dict(a, q_in=q, k_in=self.k_rows, v_in=self.v_rows, context=ctx)
      for name, width in widths.items():
        call[name] = call[name].page_view(2 * first * width, size * width)
      call["start_pos"] = Var(f"row_{first}")
      self.kernel("qwen38/attention.ttrv", MAX_TOKENS=self.capacity, PACK_CONTEXT=0, KV_HEADS=4, PARTITIONS=1,
                  PROMPT_ROWS=size)(**call)
    self.kernel("prefill/pack.ttrv", K=VH * 128, STRIDE=VH * 128, BLOCK=128, PANELS=panels, TILE_ROWS=32,
                WORKERS=min(panels * VH, workers))(x=ctx, output=self.ctxt, rows=32)

  # ---- running
  def chunk(self, start, panels):
    """Positions start .. start + 32 * panels - 1 (start a multiple of 32)."""
    key = panels
    with self.dev.phase(("qwen-chunks", panels)):
      if key not in self.graphs: self.graphs[key] = self.capture(panels)
      graph = self.graphs[key]
      values = {v: start if v == "start" else start + int(v[4:]) for v in graph.graph.vars}
      t0 = perf_counter()
      graph(**values).wait(120)
      self.elapsed += perf_counter() - t0
      if panels in self.measure: self.last_timing = self.measure[panels]()

  def run(self, start, end):
    """Process positions start .. end - 1 in whole-panel chunks; start must be a multiple of 32 and end - start a
    multiple of 32 (for now)."""
    assert start % 32 == 0 and (end - start) % 32 == 0
    self.elapsed = 0.0
    while start < end:
      panels = min(MAX_PANELS, (end - start) // 32)
      if panels % 2: panels = panels - 1 if panels > 1 else 2
      self.chunk(start, panels)
      start += 32 * panels
