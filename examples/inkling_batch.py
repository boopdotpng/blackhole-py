"""Batched Inkling 2 Mini for examples/engine.py: one captured graph runs a decode step for every live sequence at once,
one sequence per row, and prompts prefill in chunks of consecutive positions through the same machinery.

The graphs replay Inkling's decode recipe (examples/inkling.py, recorded as InklingPrompt does) over rows instead of
one token. Every row's (position, active, slot, token) lives in a pinned host step table; nothing per row is a kernel
argument, so one graph serves any mix of slots and positions:
  rows of one launch  block mixes, message gates, router (the decode kernels' ROWS modes, in row groups that fit the
                      grid), table-driven embedding, convolutions and attention (inkling/batch_*.ttrv)
  shared weights      q/k/v, o, the message gates' projections, the router projection and the LM head run on 32-row
                      activation panels (inkling/batch_pack.ttrv, inkling/batch_projection.ttrv), one weight read for
                      every row
  routed experts      each row its own eight experts (experts.ttrv ROWS mode)
Per-slot state stays in DRAM: per (layer, pass) KV caches (sliding layers keep a ring of window + chunk positions),
and the q/k/v, attention-residual and MoE-residual convolution histories. A decode step appends each row's state
directly (one row per slot); a prompt chunk's rows see each other's convolution inputs inside the launch and its
last rows are committed to the rings afterwards (inkling/batch_commit.ttrv). Prompt state needs no reset: positions
below a row's never reach past position 0, and every read is masked to the slot's own positions.

  python examples/inkling_batch.py --slots 8 --prompts 16 --tokens 64
"""
import argparse, json, sys, time
from bisect import bisect_right
from collections import Counter
from copy import copy
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import fw
from ttrv import Device, Var
from ttrv.runtime import Buffer
from examples.inkling import DEFAULT, Inkling, read, D, ROW, EOS
from examples.engine import Engine, Sequence

PANEL = 32
DECODE, PROMPT = "inkling-batch", "inkling-batch-prompt"


def stride(n): return (n + 1023) // 1024 * 1024


class InklingBatch:
  def __init__(self, dev, slots=8, context=2048, chunk=32, bfp4=True, model=None, profile=False, grouped=True):
    if not 1 <= slots <= 2 * PANEL: raise ValueError(f"1 to {2 * PANEL} slots")
    if chunk % PANEL or chunk < PANEL: raise ValueError(f"chunk: a multiple of {PANEL} positions")
    self.dev, self.slots, self.chunk = dev, slots, chunk
    self.workers = len(dev.dev.workers)
    if model is None:
      with dev.phase("inkling-single"): model = Inkling(dev, max_tokens=64, bfp4=bfp4)
    self.model = m = model
    cfg = m.cfg
    self.capacity = cap = -(-context // 32) * 32
    if cap > 8192: raise ValueError("context exceeds 8192 positions (the full layers' log-scaling)")
    self.vocab, self.eos, self.prefill_budget = cfg["unpadded_vocab_size"], {EOS}, chunk
    self.softcap = cfg["final_logit_softcapping"]
    self.rows = -(-max(slots, chunk) // PANEL) * PANEL  # rows of the activation buffers
    self.profile, self.grouped = profile, grouped
    self.buckets = [b for b in (4, 8, 16, 32) if b < slots] + [slots]

    # The decode recipe, as InklingPrompt records it.
    recipe = []
    rec = copy(m)
    rec.overlap, rec.embedding_shard = False, 0
    rec.kernel = lambda name, **defines: (lambda **args: recipe.append((name, defines, args)))
    rec.emit_step(Var("pos"))
    self.step_ops = len(recipe)
    rec.emit_readout(Var("pos"), Var("write_token"))
    self.recipe = recipe

    # Per-slot state: check it fits before allocating.
    H, KVH = m.H, m.KVH
    self.window = cfg["sliding_window_size"]
    self.ring = (self.window + chunk) // 32 + 2        # sliding ring blocks: the window plus a chunk appended ahead
    blocks = {key: min(self.ring, cap // 32) if m.sliding[key[0]] else cap // 32 for key in m.caches}
    per_slot = sum(2 * KVH * b * 4 * 2048 for b in blocks.values()) + len(m.caches) * 2 * (2 * 4 * 1024 + 2 * 4 * ROW)
    alloc = dev.dev.allocator
    free = dev.dev.dram_banks * fw.DRAM_BANK_SIZE - alloc.top
    scratch = 256 << 20
    if slots * per_slot + scratch > free:
      raise MemoryError(f"{slots} slots x {cap} positions need {slots * per_slot / 2**30:.2f} GiB of DRAM state, "
                        f"{free / 2**30:.2f} GiB is free after the weights (use --bfp4, fewer slots or less context)")
    self.state, self.cache_of = {}, {}
    for key, c in m.caches.items():
      b = blocks[key]
      slot_elems = KVH * b * 4 * 1024
      self.state[key] = dict(
        keys=dev.zeros(slots * slot_elems, "bf16"), values=dev.zeros(slots * slot_elems, "bf16"), blocks=b,
        kv_hist=dev.zeros(slots * 2 * 4 * 1024, "bf16"),
        attn_hist=dev.zeros(slots * 4 * ROW, "bf16"), mlp_hist=dev.zeros(slots * 4 * ROW, "bf16"))
      for kind in ("keys", "values", "kv_hist", "attn_hist", "mlp_hist"): self.cache_of[c[kind].addr] = key, kind

    # Batched activations: every recorded activation gets `rows` rows of its pitch.
    R = self.rows
    self.starts, self.buffers = [], {}
    for src in sorted(m.activations + [m.xf], key=lambda b: b.addr):
      pitch = stride(src.shape[0])
      self.starts.append(src.addr)
      self.buffers[src.addr] = src, pitch, dev.zeros(R * pitch, src.dtype)
    self.tiles = dev.zeros(R * 3 * 2 * D, "bf16")                       # projection input panels
    self.gx = [dev.zeros(R * 1024, "bf16") for _ in range(3)]            # message gate down projections, per gate
    self.fa = dev.zeros(3 * R * 5120, "fp32")                            # their forget/gain projections, per gate
    self.vstride = stride(m.head[1]["N"])
    self.logits = dev.zeros(R * self.vstride, "bf16")
    self.pinned = dev.dev.pinned(R * self.vstride * 2)                  # host side: DMA without staging
    self.host_logits = np.ndarray((R, self.vstride), np.uint16, self.pinned.mem)
    self.host_table = dev.zeros((R, 16), "u32", host=True)
    self.table = dev.zeros((R, 16), "u32")                               # staged by the embedding launch
    # Grouped experts: the plan, each group's gathered activations, its SwiGLU tiles and its rows' down projections.
    self.gmax = -(-min(8 * R, 128 + -(-8 * R // 32)) // 16) * 16
    inter = m.INTER
    self.plan = dev.zeros(16 + 2 * self.gmax + 32 * self.gmax + 8 * R, "u32")
    self.xt = dev.zeros(self.gmax * D * 32, "bf16")
    self.ht = dev.zeros(self.gmax * inter * 32, "bf16")
    self.y = dev.zeros(self.gmax * 32 * ROW, "bf16")

    # The message gates' down projections per gate, without the padding between the h and m halves.
    from helpers import safe_load
    from projections import bf16_image  # examples/inkling, on the path through examples.inkling
    T = safe_load(DEFAULT / "model-00001-of-00001.safetensors")
    self.downs = {}
    for i in m.loop:
      for key, names in (("gate_akv", ("attn", "k", "v")), ("gate_mlp", ("mlp",))):
        imgs = [bf16_image(read(T, f"model.llm.layers.{i}.controllers.{n}.down_weight"), group=8)[0] for n in names]
        self.downs[m.layers[i][key][0].addr] = [dev.empty(im.size, "bf16", tiles_per_page=8).copy_from(im)
                                                for im in imgs]
    self.graphs, self.kernels, self.labels = {}, {}, {}

  # ---- activation mapping
  def allocation(self, v):
    i = bisect_right(self.starts, v.addr) - 1
    if i >= 0:
      a = self.buffers[self.starts[i]]
      if v.addr - a[0].addr < a[0].nbytes: return a

  def pitch(self, v):
    a = self.allocation(v) if isinstance(v, Buffer) else None
    return a[1] if a else 0

  def at(self, v, row=0, offset=0):
    """The batched buffer for recorded value v from row `row` on (plus `offset` elements); state and constants as is."""
    if not isinstance(v, Buffer): return v
    a = self.allocation(v)
    if a is None: return v
    src, pitch, buf = a
    item = src.nbytes // src.shape[0]
    off = row * pitch * item + v.addr - src.addr + offset * item
    return buf.page_view(off, (buf.nbytes - off) // item)

  def kernel(self, path, **defines):
    key = self.dev.phase_name, path, tuple(sorted(defines.items()))
    if key not in self.kernels:
      self.kernels[key] = self.dev.kernel(HERE / path, **defines)
      tags = "".join(f" {k}={defines[k]}" for k in ("K", "N", "SELECT", "SEGMENTS", "INPUT_SEGMENTS", "NQ") if k in defines)
      self.labels[self.kernels[key]] = Path(path).stem + tags
    return self.kernels[key]

  def groups(self, rows, per_row):
    g = max(1, self.workers // per_row)
    return [(a, min(g, rows - a)) for a in range(0, rows, g)]

  # ---- batched building blocks
  def pack(self, x, k, tiles, tile0, rows, face=1, step=None):
    """Rows of k values of x (face-packed or dense) into panel tiles tile0 .. of `tiles` tiles per panel."""
    kt, panels = k // 32, -(-rows // PANEL)
    # fill the grid; face-packed reads start on 64-byte boundaries (an even tile), like their L1 staging
    sub = next(s for s in (1, 2, 4) if s >= 1 + face and (s == 4 or panels * -(-kt // s) <= self.workers))
    units = panels * -(-kt // sub)
    self.kernel("inkling/batch_pack.ttrv", K=k, ROWS=rows, SRC_STEP=step or self.pitch(x), FACE=face, TILE0=tile0,
                PANEL_TILES=tiles, SUB=sub, WORKERS=min(units, self.workers))(x=self.at(x), output=self.tiles)

  def project(self, rows, k, n, bits, group, weights, outputs, segments=1, second=0, third=0, out32=0):
    """outputs: name -> (row 0 view, row pitch). Panels go in launches of up to 10 (a column group of the grid
    multicasts each weight block to its panels), each launch reading the weights once."""
    kt, nt = k // 32, n // 32
    batch = 16 if kt % 16 == 0 and group <= 16 else group
    share = int(segments * k * PANEL % 8192 == 0)
    extra = {}
    pitches = [outputs[key][1] for key in ("output", "output2", "output3") if key in outputs]
    extra["OUTPUT_STRIDE"] = pitches[0]
    if second: extra["OUTPUT2_STRIDE"] = pitches[1]
    if third: extra["OUTPUT3_STRIDE"] = pitches[2]
    left, p0, item = -(-rows // PANEL), 0, 4 if out32 else 2
    while left:
      panels = next(p for p in (10, 5, 2, 1) if p <= left)
      workers = min(nt, 112 // panels) * panels
      x = self.tiles.page_view(p0 * segments * kt * 2048, panels * segments * kt * 1024)
      outs = {key: v.page_view(p0 * PANEL * pitch * item, (v.nbytes // item) - p0 * PANEL * pitch)
              for key, (v, pitch) in outputs.items()}
      self.kernel("inkling/batch_projection.ttrv", K=k, N=n, BITS=bits, GROUP=group, BATCH=batch, PAD=1,
                  WORKERS=workers, PREFILL=1, TILE_ROWS=PANEL, SHORT_M=0, SHARE_A=share, PANELS=panels,
                  INPUT_SEGMENTS=segments, SECOND=second, THIRD=third, OUT32=out32, **extra)(
        x=x, weights=weights, rows=PANEL, **outs)
      left, p0 = left - panels, p0 + panels

  # ---- one recorded launch over `rows` rows
  def emit(self, name, opts, args, rows, prompt):
    W, table = self.workers, self.table
    if name == "embedding":
      self.kernel("inkling/batch_embedding.ttrv", ROWS=rows, WORKERS=min(rows, W), D=D, STRIDE=self.pitch(args["output"]))(
        weights=args["weights"], output=self.at(args["output"]), host_table=self.host_table, table=table)
    elif name == "mix":
      keys = ("blocks", "cur", "queries", "out", "normed")
      steps = {n.upper() + "_STEP": self.pitch(args[n]) for n in keys if n in args}
      lanes = min(rows, W // (opts.get("NQ", 1) * 3))
      self.kernel("inkling/batch_mix.ttrv", **opts, ROWS=rows, LANES=lanes, **steps)(**{k: self.at(v) for k, v in args.items()})
    elif name == "gate":
      steps = {n.upper() + "_STEP": self.pitch(args[n]) for n in ("h", "m", "out")}
      call = {k: self.at(v) for k, v in args.items()}
      call["fa"] = self.fa
      self.kernel("inkling/batch_gate.ttrv", **opts, ROWS=rows, LANES=min(rows, W // (opts["NG"] * 3)), **steps,
                  FA_STEP=5120, FA_G=self.rows * 5120)(**call)
    elif name == "router":
      self.kernel("inkling/batch_router.ttrv", **dict(opts, PARTS=1), ROWS=rows, WORKERS=min(rows, W))(
        **{k: self.at(v) for k, v in args.items()})
    elif name == "copy":
      src = args["src"]
      self.kernel("inkling/batch_copy.ttrv", ROWS=rows, N=opts["N"], STEP=self.pitch(src),
                  WORKERS=min(W, rows * opts["N"] // 1024))(src=self.at(src), dst=self.at(args["dst"]),
                                                             dst2=self.at(args["dst2"]))
    elif name == "prep": self.prep(opts, args, rows, prompt)
    elif name == "attention": self.attention(opts, args, rows)
    elif name == "resconv":
      key, kind = self.cache_of[args["history"].addr]
      y = args["y"]
      steps = dict(Y_STEP=self.pitch(y), OUT_STEP=self.pitch(args["out"]))
      if "residual" in args: steps["RESIDUAL_STEP"] = self.pitch(args["residual"])
      call = {k: self.at(v) for k, v in args.items() if k != "pos"}
      call["history"], call["table"] = self.state[key][kind], table
      self.kernel("inkling/batch_resconv.ttrv", **opts, ROWS=rows, WORKERS=min(W, rows * 3), DIRECT=int(not prompt),
                  PROMPT=int(prompt), HIST_SLOT=4 * ROW, **steps)(**call)
      if prompt:
        self.kernel("inkling/batch_commit.ttrv", PAGES=3, SRC_STEP=self.pitch(y), HIST_SLOT=4 * ROW, RING=ROW)(
          src=self.at(y), history=self.state[key][kind], table=table)
    elif name == "experts": self.experts(opts, args, rows)
    elif name == "argmax": pass
    else: raise NotImplementedError(name)

  def prep(self, opts, args, rows, prompt):
    key, _ = self.cache_of[args["history"].addr]
    lanes = min(rows, self.workers // (3 + 2 + 4))
    steps = dict(PROJ_STEP=self.pitch(args["proj"]), Q_STEP=self.pitch(args["q_out"]), KV_STEP=self.pitch(args["k_in"]),
                 KVO_STEP=self.pitch(args["k_out"]), REL_STEP=self.pitch(args["rel"]))
    call = {k: self.at(v) for k, v in args.items() if k != "pos"}
    call["history"], call["table"] = self.state[key]["kv_hist"], self.table
    self.kernel("inkling/batch_prep.ttrv", **opts, RW=4, ROWS=rows, LANES=lanes, DIRECT=int(not prompt),
                PROMPT=int(prompt), HIST_SLOT=2 * 4 * 1024, **steps)(**call)
    if prompt:
      self.kernel("inkling/batch_commit.ttrv", SOURCES=2, PAGES=1, SRC_STEP=self.pitch(args["k_in"]), HIST_SLOT=8192,
                  RING=1024, SECOND=4096)(src=call["k_in"], src2=call["v_in"], history=call["history"], table=self.table)

  def attention(self, opts, args, rows):
    key, _ = self.cache_of[args["key_cache"].addr]
    st = self.state[key]
    kvh = opts["KV_HEADS"]
    self.kernel("inkling/batch_append.ttrv", ROWS=rows, WORKERS=min(self.workers, rows * kvh), KV_HEADS=kvh,
                BLOCKS=st["blocks"], KV_STEP=self.pitch(args["k_in"]))(
      k_in=self.at(args["k_in"]), v_in=self.at(args["v_in"]), key_cache=st["keys"], value_cache=st["values"],
      table=self.table)
    parts = 1
    defines = {k: v for k, v in opts.items() if k not in ("MAX_TOKENS",)}
    steps = dict(Q_STEP=self.pitch(args["q_in"]), PROJ_STEP=self.pitch(args["proj"]), REL_STEP=self.pitch(args["rel"]),
                 CTX_STEP=self.pitch(args["context"]))
    call = dict(q_in=self.at(args["q_in"]), proj=self.at(args["proj"]), rel=self.at(args["rel"]),
                key_cache=st["keys"], value_cache=st["values"], context=self.at(args["context"]), table=self.table)
    self.kernel("inkling/batch_attention.ttrv", **defines, MAX_TOKENS=self.capacity, BLOCKS=st["blocks"], ROWS=rows,
                WORKERS=min(self.workers, rows * kvh), PARTITIONS=parts, **steps)(**call)

  def experts(self, opts, args, rows):
    m = self.model
    x = args["x"]
    if opts.get("SELECT") and self.grouped: return self.moe(opts, args, rows)
    if opts.get("SELECT"):  # routed experts, each row its own (experts.ttrv ROWS mode)
      opts = dict(opts, STREAM_UNPACK=1, BATCH=opts["K"] // (32 if opts["SELECT"] == 1 else 256))
      per = max(1, self.workers // rows)
      for a, n in self.groups(rows, per):
        opts["WORKERS"] = min(per, opts["N"] // (64 if opts.get("SWIGLU") else 32))
        self.kernel("inkling/experts.ttrv", **opts, ROWS=n, X_STRIDE=self.pitch(x),
                    OUT_STRIDE=self.pitch(args["output"]))(**{k: self.at(v, a) for k, v in args.items()})
      return
    if opts.get("X2"):  # message gate down projections: per gate, [rms(h_g), rms(m_g)] (K = 2 D) -> 64
      ng = opts["N"] // 64
      for g, w in enumerate(self.downs[args["weights"].addr]):
        self.pack(self.at(x, 0, g * opts["XROW"]), D, 2 * D // 32, 0, rows, step=self.pitch(x))
        self.pack(self.at(args["x2"], 0, g * opts["X2ROW"]), D, 2 * D // 32, D // 32, rows, step=self.pitch(args["x2"]))
        self.project(rows, 2 * D, 64, 16, 8, w, dict(output=(self.gx[g], 1024)))
      return
    if opts.get("SUMS"):  # their forget/gain projections, one input segment per gate, FP32 out
      ng = opts["N"] // (2 * D)
      for g in range(ng): self.pack(self.gx[g], 64, 2 * ng, 2 * g, rows, face=0, step=1024)
      second = 2 * D if ng == 3 else 0
      outs = {"output": (self.fa.page_view(0, self.rows * 5120), 5120)}
      if ng == 3:
        outs["output2"] = (self.fa.page_view(4 * self.rows * 5120, self.rows * 5120), 5120)
        outs["output3"] = (self.fa.page_view(8 * self.rows * 5120, self.rows * 5120), 5120)
      self.project(rows, 64, opts["N"], 16, 2, args["weights"], outs, segments=ng, second=second, third=second, out32=1)
      return
    if opts.get("SPLIT"):  # router logits, FP32
      self.pack(x, opts["K"], opts["K"] // 32, 0, rows)
      out = args["output"]
      self.project(rows, opts["K"], opts["N"], 16, opts["GROUP"], args["weights"], dict(output=(self.at(out), self.pitch(out))),
                   out32=1)
      return
    # dense: q/k/v (input segments), o, LM head
    k, n = opts["K"], opts["N"]
    segs = 3 if opts.get("XSEG") else 1
    for s in range(segs):
      self.pack(self.at(x, 0, s * opts.get("XROW", 0)), k, segs * k // 32, s * k // 32, rows, step=self.pitch(x))
    second = third = 0
    if opts.get("SEG1"):
      second, third = (opts["SEG2"] - opts["SEG1"]) * 32, n - opts["SEG2"] * 32
    outs = {key: (self.at(v), self.pitch(v)) for key, v in args.items() if key.startswith("output")}
    if args["output"] is m.logits: outs["output"] = self.logits, self.vstride
    self.project(rows, k, n, opts.get("BITS", 8), opts["GROUP"], args["weights"], outs, segments=segs, second=second,
                 third=third)

  def moe(self, opts, args, rows):
    """Routed experts grouped by expert over the step's rows (inkling/moe_*.ttrv): one weight read per used expert."""
    W, gm = self.workers, self.gmax
    k, bits, group = opts["K"], opts.get("BITS", 8), opts["GROUP"]
    common = dict(G_MAX=gm, WORKERS=W)
    if opts["SELECT"] == 1:
      self.score = self.at(args["score"])
      self.kernel("inkling/moe_plan.ttrv", ROWS=rows, G_MAX=gm)(select=self.at(args["select"]), table=self.table,
                                                                plan=self.plan)
      self.kernel("inkling/moe_pack.ttrv", K=k, SRC_STEP=self.pitch(args["x"]), **common)(
        x=self.at(args["x"]), plan=self.plan, output=self.xt)
      n = opts["N"] // 8
      self.kernel("inkling/moe_matmul.ttrv", SWIGLU=1, K=k, N=n, BITS=bits, GROUP=group, BATCH=24 if (k // 32) % 24 == 0 else group,
                  **common)(x=self.xt, weights=args["weights"], plan=self.plan, output=self.ht)
    else:
      inter = k // 8
      self.kernel("inkling/moe_matmul.ttrv", SWIGLU=0, K=inter, N=D, BITS=bits, GROUP=group,
                  BATCH=12 if (inter // 32) % 12 == 0 else group, YS=ROW, **common)(
        x=self.ht, weights=args["weights"], plan=self.plan, output=self.y)
      out = args["output"]
      self.kernel("inkling/moe_combine.ttrv", ROWS=rows, YS=ROW, OUT_STEP=self.pitch(out), G_MAX=gm,
                  WORKERS=min(W, rows * 3))(y=self.y, plan=self.plan, score=self.score, out=self.at(out))

  # ---- graphs
  def graph(self, prompt, live=0):
    """The prompt chunk graph, or the decode graph of the smallest row bucket holding `live` rows (each in its own
    worker L1 phase: a decode step runs the rows its bucket holds, live or not)."""
    rows = self.chunk if prompt else next(b for b in self.buckets if b >= live)
    phase = PROMPT if prompt else f"{DECODE}-{rows}"
    self.dev.activate(phase)
    if phase not in self.graphs:
      ops = self.recipe[:self.step_ops] if prompt else self.recipe
      with self.dev.graph() as g:
        for name, opts, args in ops: self.emit(name, opts, args, rows, prompt)
      timing = g.graph.enable_timing() if self.profile else None
      self.graphs[phase] = g, timing
    return self.graphs[phase]

  def profile_last(self, phase):
    g, timing = self.graphs[phase if phase in self.graphs else f"{DECODE}-{self.buckets[-1]}"]
    totals = Counter()
    for launch, ms in zip(g.launches, timing()): totals[self.labels.get(launch[0], "?")] += ms
    return totals

  # ---- backend interface (examples/engine.py)
  def reusable(self, slot, ids, held):
    n = len(held)
    return n if n <= len(ids) and np.array_equal(np.asarray(ids[:n]), np.asarray(held)) else 0

  def prefill(self, slot, ids, start, end):
    n = min(self.chunk, end - start)
    g, _ = self.graph(True)
    t = self.host_table.numpy()
    t[:] = 0
    for r in range(n): t[r, :4] = start + r, 1, slot, ids[start + r]
    t[0, 4] = n
    g().wait(120)
    return n

  def decode(self, rows):
    g, _ = self.graph(False, len(rows))
    t = self.host_table.numpy()
    t[:] = 0
    for r, (slot, pos, token) in enumerate(rows): t[r, :4] = pos, 1, slot, token
    g().wait(60)
    raw = self.host_logits[:len(rows)]
    self.dev.dev.allocator.copyout(raw.reshape(-1), self.logits.addr)
    raw = raw[:, :self.vocab]
    z = np.empty(raw.shape, np.uint32)
    np.left_shift(raw, 16, out=z, dtype=np.uint32)
    z = z.view(np.float32)
    z *= np.float32(1 / self.softcap)
    np.tanh(z, out=z)
    z *= np.float32(self.softcap)
    return z


def chat_prompt(text):
  from examples.inkling import chat
  return chat(DEFAULT, text)


if __name__ == "__main__":
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument("--slots", type=int, default=8)
  ap.add_argument("--context", type=int, default=2048, help="positions per slot")
  ap.add_argument("--chunk", type=int, default=32, help="prompt positions per prefill launch")
  ap.add_argument("--bfp8", action="store_true", help="BFP8 experts in every layer (less room for slots)")
  ap.add_argument("--prompts", type=int, default=16)
  ap.add_argument("--tokens", type=int, default=64)
  ap.add_argument("--temperature", type=float, default=0.0)
  ap.add_argument("--device", type=int, default=0)
  a = ap.parse_args()
  from tokenizers import Tokenizer
  tok = Tokenizer.from_file(str(DEFAULT / "tokenizer.json"))
  topics = ["a robot learning to paint", "the history of the bicycle", "why the sky is blue", "a dragon who bakes bread",
            "how compilers work", "the moon landing", "a city under the sea", "learning to play the violin"]
  prompts = [tok.encode(chat_prompt(f"Write {'a story' if i % 2 else 'a short essay'} about {topics[i % len(topics)]}. ({i})"),
                        add_special_tokens=False).ids for i in range(a.prompts)]
  dev = Device(a.device)
  try:
    t0 = time.perf_counter()
    engine = Engine(InklingBatch(dev, slots=a.slots, context=a.context, chunk=a.chunk, bfp4=not a.bfp8))
    print(f"loaded in {time.perf_counter() - t0:.1f}s", file=sys.stderr)
    seqs = [Sequence(p, a.tokens, temperature=a.temperature, seed=i) for i, p in enumerate(prompts)]
    start = time.perf_counter()
    engine.run(seqs)
    elapsed = time.perf_counter() - start
    total = sum(len(s.out) for s in seqs)
    for i, s in enumerate(seqs[:3]): print(f"--- {i}: {tok.decode(s.out)!r}")
    print(f"{len(seqs)} sequences on {a.slots} slots: {total} tokens in {elapsed:.2f}s, {engine.steps} steps, "
          f"{total / elapsed:.1f} tok/s overall, {dict(engine.stats)}, {dict(engine.times)}", file=sys.stderr)
  finally:
    dev.close()
