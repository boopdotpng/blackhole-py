"""Batched prompt projections with per-layer Qwen recurrent and KV state shared with decode."""

from collections import Counter
from functools import lru_cache
from pathlib import Path
from time import perf_counter

from ttrv import hw
from examples.prefill import summa_shapes
from ttrv.runtime import Var
from ttrv.layout import ResidentCapacityError
from ttrv.parse import Error as TtrvError

HERE = Path(__file__).resolve().parent
CHUNK = 64


class QwenPrompt:
  def __init__(self, dev, scratch, recipe, projections, kinds, eps, capacity, profiler=None):
    # Each matrix row starts on a DRAM page. Projections with multiple outputs
    # use the logical width of each output (the QKV buffer serves two layer types).
    self.graphs, self.measure = {}, {}
    labels = {}
    buffers = {v: dev.empty(CHUNK * ((v.shape[0] + 1023) // 1024) * 1024, "bf16") for v in scratch}
    mlp_tiles = dev.empty(CHUNK * max(v.shape[0] for v in scratch), "bf16")
    packed = dev.empty(CHUNK * max(v.shape[0] for v in scratch), "bf16")
    self.unavailable = set()
    prompt_projections = {k for k, _ in recipe if k in projections}
    output_widths = []
    for k in prompt_projections:
      _, total, _, _, second, third = projections[k]
      output_widths.append((total - second - third, second, third))
    tile_outputs = [dev.empty(CHUNK * max(widths), "bf16") for widths in zip(*output_widths)]
    workers = len(dev.dev.workers)

    @lru_cache(None)
    def compile_kernel(phase, path, options):
      compiled = dev.kernel(HERE / path, **dict(options))
      labels[compiled] = Path(path).stem
      return compiled

    def kernel(path, **options):
      return compile_kernel(dev.phase_name, path, tuple(options.items()))

    self.dev = dev

    # Projection outputs have independent page-aligned row pitches, including the padded 128-element ab row.
    head_rows = {
      "gated": {"x": 6144, "z": 6144, "output": 6144},
      "attention": {"q_in": 12288, "k_in": 1024, "v_in": 1024, "context": 6144},
    }
    labels.update({original: kind for original, kind in kinds.items()})

    def capture(rows):
      panels = max(1, rows // 32)
      tile_rows = 16 if rows <= 16 else 32
      with dev.graph() as graph:
        tiled_input = None
        fused_output = None
        last_packed = None
        for index, (original, args) in enumerate(recipe):
          args = {name: buffers.get(v, v) for name, v in args.items()}
          if original in projections:
            width, n, bits, group, second, third = projections[original]
            source = args.pop("x")
            source_tiles = packed
            if source is tiled_input:
              source_tiles, tiled_input = mlp_tiles, None
            elif source is not last_packed:
              kernel("prefill/pack.ttrv", K=width, WORKERS=min(panels * width // 128, workers), PANELS=panels, TILE_ROWS=tile_rows)(
                x=source, output=packed, rows=min(rows, 32)
              )
              last_packed = source
            fuse = rows % 32 == 0 and index + 1 < len(recipe) and kinds.get(recipe[index + 1][0]) == "swiglu"
            if panels > 1:
              for shape in summa_shapes(width, n, bits, group, panels, fuse, hw.L1_SIZE - dev.top):
                try:
                  project = kernel("prefill/summa_projection.ttrv", K=width, N=n, GROUP=group, BITS=bits,
                                   PAD=0, PANELS=panels, SWIGLU=int(fuse), SECOND=0 if fuse else second,
                                   THIRD=0 if fuse else third, **shape)
                except (ResidentCapacityError, TtrvError) as exc:
                  if isinstance(exc, TtrvError) and exc.id != "storage.overflow": raise
                  continue
                if fuse:
                  project(x=source_tiles, weights=args["weights"], output=mlp_tiles)
                  fused_output = recipe[index + 1][1]["output"]
                else:
                  widths = (n - second - third, second, third)
                  outputs = [(key, w, tmp) for key, w, tmp in
                             zip(("output", "output2", "output3"), widths, tile_outputs) if w]
                  project(x=source_tiles, weights=args["weights"], **{key: tmp for key, _, tmp in outputs})
                  for key, w, tmp in outputs:
                    block = 128 if w % 128 == 0 else 32
                    kernel("prefill/unpack.ttrv", N=w, PANELS=panels, BLOCK=block,
                           WORKERS=min(workers, panels * w // block))(x=tmp, output=args[key])
                break
              else: project = None
              if project is not None: continue
            if fuse:
              kernel("prefill/projection.ttrv", K=width, N=n, BITS=bits, GROUP=group, PANELS=panels,
                     WORKERS=min(n // 64, workers // panels) * panels, SWIGLU=1, STAGES=4, BATCH=32)(
                x=source_tiles, weights=args["weights"], output=mlp_tiles)
              fused_output = recipe[index + 1][1]["output"]
              continue
            kernel(
              "nanbeige/projection.ttrv",
              K=width,
              N=n,
              BITS=bits,
              GROUP=group,
              SECOND=second,
              THIRD=third,
              PANELS=panels, WORKERS=min(n // 32, 96 // panels) * panels,
              PREFILL=1,
              TILE_ROWS=tile_rows,
              SHORT_M=int(rows <= 8),
              SHARE_A=1,
            )(x=source_tiles, rows=min(rows, 32), **args)
            continue
          kind = kinds[original]
          last_packed = None
          if kind == "swiglu" and fused_output is not None:
            tiled_input, fused_output = buffers[fused_output], None
            continue
          if kind == "embed":
            dim = args["output"].shape[0] // CHUNK
            for first in range(0, rows, workers):
              size = min(workers, rows-first)
              call = dict(args, token_pos=Var(f"row_{first}"), output=args["output"].page_view(
                2 * first * dim, size * dim))
              kernel("shared/embedding.ttrv", EMBED_TILES=dim // 1024, ROW_LANES=size)(**call)
          elif kind in ("conv", "state"):
            kernel("qwen38/gdn_" + kind + ".ttrv", ROWS=rows)(**args)
          elif kind == "gated":
            lanes = workers // 6
            for first in range(0, rows, lanes):
              size = min(lanes, rows - first)
              batch = {name: args[name].page_view(2 * first * width, size * width)
                       for name, width in head_rows[kind].items()}
              kernel("qwen38/gdn_out.ttrv", PACKED=0, ROWS=size)(**batch, gamma=args["gamma"])
          elif kind == "attention":
            lanes = min(16, workers // 8)
            for first in range(0, rows, lanes):
              size = min(lanes, rows - first)
              call = args.copy()
              for name, width in head_rows[kind].items():
                call[name] = args[name].page_view(2 * first * width, size * width)
              call["start_pos"] = Var(f"row_{first}")
              kernel("qwen38/attention.ttrv", MAX_TOKENS=capacity, PACK_CONTEXT=0, KV_HEADS=4,
                     PARTITIONS=1, PROMPT_ROWS=size)(**call)
          else:
            dim = original.compiled.program.consts["DIM"]
            stride = (dim + 1023) // 1024 * 1024
            lanes = min(rows, workers // (stride // 1024))
            for first in range(0, rows, lanes):
              size = min(rows - first, lanes)
              batch = {
                name: v if kind == "rms" and name == "other" else v.page_view(2 * first * stride, size * stride)
                for name, v in args.items()
              }
              kernel(
                "nanbeige/vector.ttrv",
                DIM=dim,
                RMS=int(kind == "rms"),
                SWIGLU=int(kind == "swiglu"),
                EPS=eps,
                PACKED=0,
                ROW_LANES=size,
              )(**batch)
      if profiler:
        self.measure[rows] = profiler(dev, graph, labels)
      return graph

    self.capture = capture

  def prepare(self, rows):
    self.dev.activate(("qwen-prefill", rows))
    if rows not in self.graphs:
      self.graphs[rows] = self.capture(rows)

  def submit(self, start, rows, **extra):
    graph = self.graphs[rows]
    return graph(**{v: start if v == "pos" else start + int(v[4:]) for v in graph.graph.vars}, **extra)

  def run(self, length, chunk_size=CHUNK, serial_step=None, start=0):
    """Process positions start .. length - 1; the state already holds positions before start."""
    if not 1 <= chunk_size <= CHUNK:
      raise ValueError("chunk size outside the allocated panel capacity")
    self.elapsed = 0.0
    self.timings = Counter()
    while start < length:
      rows = min(chunk_size, length - start)
      if 32 < rows < CHUNK: rows = 32
      if rows in self.unavailable:
        chunk_size = rows // 2
        continue
      try:
        self.prepare(rows)
      except (ResidentCapacityError, TtrvError) as e:
        if isinstance(e, TtrvError) and e.id != "storage.overflow": raise
        if rows > 1:
          self.unavailable.add(rows)
          chunk_size = rows // 2
          continue
        if serial_step is None: raise
        start_time = perf_counter()
        for pos in range(start, length): serial_step(pos=pos).wait()
        self.elapsed += perf_counter() - start_time
        return
      start_time = perf_counter()
      # Causal attention scans the growing prefix for each query row.
      timeout = max(15, rows * (start + rows) / 1000)
      self.submit(start, rows).wait(timeout)
      self.elapsed += perf_counter() - start_time
      if rows in self.measure:
        self.timings.update(self.measure[rows]())
      start += rows
