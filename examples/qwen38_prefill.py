"""Batched prompt projections with per-layer Qwen recurrent and KV state shared with decode."""

from collections import Counter
from functools import lru_cache
from pathlib import Path
from time import perf_counter

HERE = Path(__file__).resolve().parent
CHUNK = 32


class QwenPrompt:
  def __init__(self, dev, scratch, recipe, projections, kinds, eps, head_kernel, profiler=None):
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

    gdn = head_kernel(linear=True, prompt=True)
    finish = head_kernel(linear=True, prompt=True, finish=True)
    cache = head_kernel(linear=False, prompt=True, cache_only=True)
    attention = head_kernel(linear=False, prompt=True)

    labels.update({gdn: "GDN", finish: "GDN output", cache: "KV append", attention: "GQA"})

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
          elif kind in ("gdn", "attention"):
            if kind == "attention":
              cache(**args, rows=rows)
            if kind == "gdn":
              # Both half-heads read the old history. Publish the new history after their graph barrier.
              gdn(**args, rows=rows, next_history=packed)
              finish(**args, rows=rows, next_history=packed)
            else:
              attention(**args, rows=rows)
          else:
            dim = args["x"].shape[0] // CHUNK
            lanes = min(rows, workers // (dim // 1024))
            for first in range(0, rows, lanes):
              size = min(rows - first, lanes)
              batch = {
                name: v if kind == "rms" and name == "other" else v.page_view(2 * first * dim, size * dim)
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

  def run(self, length, chunk_size=CHUNK):
    if not 1 <= chunk_size <= CHUNK:
      raise ValueError("chunk size outside the allocated panel capacity")
    self.elapsed = 0.0
    self.timings = Counter()
    start = 0
    while start < length:
      rows = min(chunk_size, length - start)
      if rows not in self.graphs:
        self.graphs[rows] = self.capture(rows)
      start_time = perf_counter()
      # Causal attention scans the growing prefix for each query row.
      timeout = max(15, rows * (start + rows) / 1000)
      self.graphs[rows](pos=start).wait(timeout)
      self.elapsed += perf_counter() - start_time
      if rows in self.measure:
        self.timings.update(self.measure[rows]())
      start += rows
