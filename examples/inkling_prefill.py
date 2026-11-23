"""Layer-major prompt execution for Inkling's recurrent layer passes and routed experts."""
from bisect import bisect_right
from copy import copy
from time import perf_counter
from pathlib import Path

from ttrv import Var
from ttrv.runtime import Buffer

CHUNK = 8


class InklingPrompt:
  def __init__(self, model):
    self.model, self.dev = model, model.dev
    self.graphs = {}
    # Record the model's actual pass order and aliases. State and weights stay shared.
    recipe = []
    prompt = copy(model)
    prompt.overlap, prompt.embedding_shard = False, 0
    def operation(name, **defines):
      def record(**args): recipe.append((name, defines, args))
      return record
    prompt.kernel = operation
    prompt.emit_step(Var("pos"))
    self.recipe = recipe
    self.starts, self.buffers = [], {}
    for source in sorted(model.activations, key=lambda b: b.addr):
      stride = (source.shape[0] + 1023) // 1024 * 1024
      self.starts.append(source.addr)
      self.buffers[source.addr] = source, stride, self.dev.zeros(CHUNK * stride, source.dtype)
    self.packed = self.dev.empty(3 * 16 * 7168, "bf16")

  def allocation(self, value):
    idx = bisect_right(self.starts, value.addr) - 1
    if idx >= 0:
      allocation = self.buffers[self.starts[idx]]
      if value.addr - allocation[0].addr < allocation[0].nbytes: return allocation

  def stride(self, value):
    allocation = self.allocation(value)
    return allocation[1] if allocation else 0

  def binding(self, value, row, whole=False):
    if isinstance(value, Var): return Var(f"p{row}")
    if not isinstance(value, Buffer): return value
    allocation = self.allocation(value)
    if allocation is None: return value
    src, stride, buf = allocation
    off = value.addr - src.addr
    item = src.nbytes // src.shape[0]
    offset = row * stride * item + off
    return buf.page_view(offset, (buf.nbytes - offset) // item if whole else value.shape)

  def capture(self, rows):
    root = Path(__file__).resolve().parent
    kernel = self.dev.kernel
    with self.dev.graph() as graph:
      for name, opts, args in self.recipe:
        if name == "embedding":
          kernel(root / "shared/embedding.ttrv", **opts, ROW_LANES=rows, STRIDE=self.model.x0.shape[0])(
            **{n: self.binding(v, 0, True) for n, v in args.items()})
          continue
        # Dense Q/K/V and O share their matrix across tokens. Routed projections use each token's own expert IDs.
        if name == "experts" and not any(opts.get(n) for n in ("SELECT", "X2", "SUMS", "SPLIT", "OUT32", "PACK_OUT")):
          k, n, group = opts["K"], opts["N"], opts["GROUP"]
          src = args["x"]
          stride = self.stride(src)
          segments = 3 if opts.get("XSEG") else 1
          kernel(root / "inkling/prompt_pack.ttrv", K=k, ROWS=rows, ROW_STRIDE=stride,
                 SEGMENTS=segments, SEG_STRIDE=opts.get("XROW", 0))(x=self.binding(src, 0, True), output=self.packed)
          second = (opts.get("SEG2", 0) - opts.get("SEG1", 0)) * 32
          third = n - opts["SEG2"] * 32 if second else 0
          outputs = {key: self.binding(v, 0, True) for key, v in args.items() if key.startswith("output")}
          kernel(root / "nanbeige/projection.ttrv", K=k, N=n, GROUP=group, BATCH=group, PAD=1, BITS=opts.get("BITS", 8),
                 WORKERS=min(n // 32, 112), PREFILL=1, TILE_ROWS=16, SHORT_M=1, INPUT_SEGMENTS=segments,
                 SECOND=second, THIRD=third, OUTPUT2_STRIDE=2048, OUTPUT3_STRIDE=2048)(x=self.packed, weights=args["weights"], rows=rows, **outputs)
          continue
        source = root / "inkling" / (name + ".ttrv")
        if name == "resconv" and rows > 1:
          call = {n: self.binding(v, 0, True) for n, v in args.items()}
          strides = {n.upper() + "_STEP": self.stride(args[n]) for n in ("y", "residual", "out") if n in args}
          kernel(source, **opts, ROWS=rows, **strides)(**call)
          kernel(root / "inkling/prompt_history.ttrv", ROWS=rows, KEEP=min(rows, 4),
                 PAGES=(opts.get("D", 2304) + 1023) // 1024, Y_STEP=strides["Y_STEP"])(
            **{n: call[n] for n in ("y", "history", "pos")})
          continue
        if name in ("mix", "gate", "router"):
          keys = {"mix": ("blocks", "cur", "queries", "out", "normed"), "gate": ("h", "m", "fa", "out"), "router": ()}
          strides = {n.upper() + "_STEP": self.stride(args[n]) for n in keys[name] if n in args}
          kernel(source, **opts, ROWS=rows, **strides)(**{n: self.binding(v, 0, True) for n, v in args.items()})
          continue
        if name == "experts" and opts.get("SELECT"):
          opts = dict(opts, STREAM_UNPACK=1, BATCH=opts["K"] // (32 if opts["SELECT"] == 1 else 256))
          opts["WORKERS"] = min(len(self.dev.dev.workers) // rows,
                                opts["N"] // (64 if opts.get("SWIGLU") else 32))
          kernel(source, **opts, ROWS=rows, X_STRIDE=self.stride(args["x"]), OUT_STRIDE=self.stride(args["output"]))(
            **{n: self.binding(v, 0, True) for n, v in args.items()})
          continue
        for r in range(rows):
          kernel(source, **opts)(**{n: self.binding(v, r) for n, v in args.items()})
    return graph

  def run(self, length):
    self.elapsed, start = 0., 0
    while start < length:
      rows = min(CHUNK, length - start)
      self.dev.activate(("inkling-prefill", rows))
      if rows not in self.graphs: self.graphs[rows] = self.capture(rows)
      graph = self.graphs[rows]
      begin = perf_counter()
      graph(**{v: start + int(v[1:]) for v in graph.graph.vars}).wait(120)
      self.elapsed += perf_counter() - begin
      start += rows
