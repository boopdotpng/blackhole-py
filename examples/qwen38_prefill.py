"""Batched prompt projections with per-layer Qwen recurrent and KV state shared with decode."""

from collections import Counter
from functools import lru_cache
from pathlib import Path
from time import perf_counter

from ttrv.runtime import Var

HERE = Path(__file__).resolve().parent
CHUNK = 32


class QwenPrompt:
  def __init__(self, dev, scratch, recipe, projections, kinds, eps, capacity, ranks, profiler=None):
    # Each matrix row starts on a DRAM page. Projections with multiple outputs
    # use the logical width of each output (the QKV buffer serves two layer types).
    self.graphs, self.measure = {}, {}
    labels = {}
    buffers = {v: dev.empty(CHUNK * ((v.shape[0] + 1023) // 1024) * 1024, "bf16") for v in scratch}
    packed = dev.empty(CHUNK * max(v.shape[0] for v in scratch), "bf16")
    workers = len(dev.dev.workers)

    @lru_cache(None)
    def kernel(path, **options):
      compiled = dev.kernel(HERE / path, **options)
      labels[compiled] = Path(path).stem
      return compiled

    # Projection outputs have independent page-aligned row pitches, including the padded 128-element ab row.
    head_rows = {
      "conv": {"qkv": 10240 // ranks, "output": 10240 // ranks},
      "state": {"conv": 10240 // ranks, "ab": 128, "output": 6144 // ranks},
      "gated": {"x": 6144 // ranks, "z": 6144 // ranks, "output": 6144 // ranks},
      "attention": {"q_in": 12288 // ranks, "k_in": 1024 // ranks, "v_in": 1024 // ranks, "context": 6144 // ranks},
    }
    dense_out = kernel("qwen38/gdn_out.ttrv", PACKED=0, HEADS=48 // ranks)
    dense_attention = kernel("qwen38/attention.ttrv", MAX_TOKENS=capacity, PACK_CONTEXT=0, KV_HEADS=4 // ranks)
    labels.update({original: kind for original, kind in kinds.items()})

    def capture(rows):
      tile_rows = 16 if rows <= 16 else 32
      with dev.graph() as graph:
        for original, args in recipe:
          args = {name: buffers.get(v, v) for name, v in args.items()}
          if original in projections:
            width, n, bits, group, second, third = projections[original]
            source = args.pop("x")
            kernel("prefill/pack.ttrv", K=width, WORKERS=min(width // 128, workers), TILE_ROWS=tile_rows)(
              x=source, output=packed, rows=rows
            )
            kernel(
              "nanbeige/projection.ttrv",
              K=width,
              N=n,
              BITS=bits,
              GROUP=group,
              SECOND=second,
              THIRD=third,
              WORKERS=min(n // 32, 96, workers),
              PREFILL=1,
              TILE_ROWS=tile_rows,
              SHORT_M=int(rows <= 8),
              SHARE_A=1,
            )(x=packed, rows=rows, **args)
            continue
          kind = kinds[original]
          if kind == "embed":
            dim = args["output"].shape[0] // CHUNK
            kernel("llama3/embedding.ttrv", EMBED_TILES=dim // 1024, ROW_LANES=rows)(**args)
          elif kind in head_rows:
            run = {"gated": dense_out, "attention": dense_attention}.get(kind, original)
            for row in range(rows):
              call = args.copy()
              for name, width in head_rows[kind].items():
                stride = (width + 1023) // 1024 * 1024
                call[name] = args[name].page_view(2 * row * stride, width)
              if kind != "gated":
                call["start_pos" if kind == "attention" else "pos"] = Var(f"row_{row}")
              run(**call)
          elif kind == "add" and ranks == 2:
            dim = args["x"].shape[0] // CHUNK
            for row in range(rows):
              buffers_for_row = {key: args[key].page_view(2 * row * dim, dim) for key in ("x", "other", "output")}
              original(**buffers_for_row, step=args["step"], slot=args["slot"] * rows + row)
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
    if rows not in self.graphs:
      self.graphs[rows] = self.capture(rows)

  def submit(self, start, rows, **extra):
    return self.graphs[rows](pos=start, **{f"row_{i}": start + i for i in range(rows)}, **extra)

  def run(self, length, chunk_size=CHUNK):
    if not 1 <= chunk_size <= CHUNK:
      raise ValueError("chunk size outside the allocated panel capacity")
    self.elapsed = 0.0
    self.timings = Counter()
    start = 0
    while start < length:
      rows = min(chunk_size, length - start)
      self.prepare(rows)
      start_time = perf_counter()
      # Causal attention scans the growing prefix for each query row.
      timeout = max(15, rows * (start + rows) / 1000)
      self.submit(start, rows).wait(timeout)
      self.elapsed += perf_counter() - start_time
      if rows in self.measure:
        self.timings.update(self.measure[rows]())
      start += rows
