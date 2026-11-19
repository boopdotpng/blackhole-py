"""Greedy, batch-one text decode for the native tiled Qwen3.8-27B checkpoint."""

from collections import Counter
import argparse
import json
from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import fw  # noqa: E402
from helpers import safe_load  # noqa: E402
from ttrv.runtime import Device, Var  # noqa: E402

KERNEL = Path(__file__).with_name("nanbeige") / "projection.ttrv"
HEADS = Path(__file__).with_name("qwen38")  # Tensix GDN and attention kernels

DEFAULT = ROOT.parent / "weights/qwen3.8-27b/mixed_bfp4mlp_bfp8down_bfp8attn/model.safetensors"
METADATA = Path.home() / "models/qwen3.8-27b/bf16"
PREFIX = "model.language_model."


def upload_packed(dev, tiles, group, bits):
  k = tiles[0].shape[0] * 32
  n = sum(part.shape[1] * 32 for part in tiles)
  row_bytes = n // 32 * tiles[0].shape[-1]
  buf = dev.empty(k // 32 * row_bytes, f"bfp{bits}", tiles_per_page=group)
  # Keep the file's native tile bytes. Each DRAM page streams one output column over group K tiles.
  for first in range(0, k // 32, group):
    offset = buf.addr + first * row_bytes
    for matrix in tiles:
      strip = np.ascontiguousarray(matrix[first : first + group].swapaxes(0, 1))
      dev.dev.allocator._copyin(offset, strip)
      offset += strip.nbytes
  return buf


def upload_bf16(dev, matrix, group):
  n, k = matrix.shape
  buf = dev.empty(n * k, "bf16", tiles_per_page=group)
  for col in range(0, k, group * 32):
    strip = matrix[:, col : col + group * 32].reshape(n // 32, 2, 16, group, 2, 16)
    strip = strip.transpose(0, 3, 4, 1, 5, 2).copy()
    dev.dev.allocator._copyin(buf.addr + col * n * 2, strip)
  return buf


def profile_graph(dev, capture, labels):
  from ops_blackhole import BlackholeComputeQueue, BlackholeGraph

  stamps = dev.zeros((len(capture.launches), 4), "u64", host=True)
  queue = BlackholeComputeQueue()
  names = []
  for i, (kernel, _, _) in enumerate(capture.launches):
    queue.exec(kernel.program, capture.graph.base + i * fw.PARAM_SIZE, profile=stamps.addr + i * 32)
    names.append(labels[kernel])
  capture.graph.graph = BlackholeGraph(dev.dev, queue)

  def measure():
    ticks = stamps.numpy()
    totals = Counter()
    for name, cycles in zip(names, ticks[:, 3] - ticks[:, 1]):
      totals[name] += int(cycles) / (fw.AICLK_MHZ * 1000)
    return totals

  return measure


def floats(t):
  return (t.numpy().astype(np.uint32) << 16).view(np.float32)


class Qwen38:
  def __init__(self, file, metadata, dev, max_tokens, profile=False, *, rank=0, link=None):
    cfg = json.loads((metadata / "config.json").read_text())["text_config"]
    self.eos = set(np.atleast_1d(json.loads((metadata / "generation_config.json").read_text())["eos_token_id"]))
    self.vocab_size = cfg["vocab_size"]
    self.max_tokens = max_tokens
    if not 1 <= max_tokens <= cfg["max_position_embeddings"]:
      raise ValueError("invalid context length")
    sizes = (
      "hidden_size",
      "intermediate_size",
      "num_attention_heads",
      "num_key_value_heads",
      "head_dim",
      "linear_num_value_heads",
      "linear_num_key_heads",
      "linear_key_head_dim",
      "linear_value_head_dim",
      "linear_conv_kernel_dim",
    )
    if tuple(cfg[k] for k in sizes) != (5120, 17408, 24, 4, 256, 48, 16, 128, 128, 4):
      raise ValueError("expected the Qwen3.8-27B text configuration")
    cap = (max_tokens + 31) // 32 * 32
    dim, mlp, vocab = cfg["hidden_size"], cfg["intermediate_size"], cfg["vocab_size"]
    ranks = 2 if link else 1
    mlp //= ranks
    vocab //= ranks
    vh, kv = 48 // ranks, 4 // ranks
    values, channels = vh * 128, 10240 // ranks

    def shard(width):
      local = width // ranks
      return slice(rank * local, (rank + 1) * local)

    tensors = safe_load(file)
    kernels, labels = {}, {}
    projections, recipe = {}, []

    def launch(kernel, **args):
      recipe.append((kernel, args))
      kernel(**args)

    def projection(parts, dense=None, second=0, third=0, *, row_parallel=False, qkv_parts=False):
      if dense is None:
        bits = {"bfp4_b": 4, "bfp8_b": 8}[parts[0].packed_format]
        group = 16 if bits == 4 else 8
        tiles = []
        for index, part in enumerate(parts):
          tile = part.numpy()
          if row_parallel:
            tiles.append(tile[shard(tile.shape[0])])
          elif qkv_parts and index == 0:
            for block in np.split(tile, [2048 // 32, 4096 // 32], axis=1):
              tiles.append(block[:, shard(block.shape[1])])
          else:
            tiles.append(tile[:, shard(tile.shape[1])])
        n, k = sum(t.shape[1] * 32 for t in tiles), tiles[0].shape[0] * 32
        matrix = upload_packed(dev, tiles, group, bits)
      else:
        bits, group = 16, 4
        n, k = dense.shape
        matrix = upload_bf16(dev, dense, group)
      key = k, n, bits, second, third
      if key not in kernels:
        kernels[key] = dev.kernel(
          KERNEL,
          K=k,
          N=n,
          BITS=bits,
          GROUP=group,
          SECOND=second,
          THIRD=third,
          WORKERS=min(112, n // 32, len(dev.dev.workers)),
        )
      labels[kernels[key]] = f"projection {k}x{n} {bits}b"

      projections[kernels[key]] = (k, n, bits, group, second, third)

      def run(x, output, **extra):
        launch(kernels[key], x=x, weights=matrix, output=output, **extra)

      return run

    vector = KERNEL.with_name("vector.ttrv")
    rms = dev.kernel(vector, DIM=dim, RMS=1, EPS=cfg["rms_norm_eps"])
    endpoint = {"ETH_X": link.coord & 63, "ETH_Y": link.coord >> 6} if link else {}
    add = dev.kernel(vector, DIM=dim, TP=int(bool(link)), **endpoint)
    swiglu = dev.kernel(vector, DIM=mlp, SWIGLU=1)
    llama = KERNEL.parent.parent / "llama3"
    embed = dev.kernel(llama / "embedding.ttrv", EMBED_TILES=dim // 1024)
    argmax = dev.kernel(
      llama / "argmax.ttrv", VOCAB=vocab, VOCAB_BASE=rank * vocab, MAX_TOKENS=cap, LINK_PICK=int(bool(link)), **endpoint
    )
    conv = dev.kernel(HEADS / "gdn_conv.ttrv", CHANNELS=channels)
    gdn = dev.kernel(HEADS / "gdn_state.ttrv", HEADS=vh)
    gated = dev.kernel(HEADS / "gdn_out.ttrv", HEADS=vh)
    attention = dev.kernel(HEADS / "attention.ttrv", MAX_TOKENS=cap, KV_HEADS=kv)
    rope = cfg["rope_parameters"]
    rd = int(cfg["head_dim"] * rope["partial_rotary_factor"])
    if rd != 64:
      raise ValueError("expected 64 rotary channels")
    angle = np.arange(cap, dtype=np.float32)[:, None] * rope["rope_theta"] ** (
      -np.arange(0, rd, 2, dtype=np.float32) / rd
    )
    # attention.ttrv computes x cos + swapped sin over 256-wide rows; dims 64.. pass through.
    cosines, sines = np.cos(angle), np.sin(angle)
    cos = dev.array(np.concatenate((cosines, cosines, np.ones((cap, 192), np.float32)), axis=1), "bf16")
    sin = dev.array(np.concatenate((-sines, sines, np.zeros((cap, 192), np.float32)), axis=1), "bf16")
    self.history = dev.zeros(cap, "u32")
    self.tokens = dev.zeros((cap + 1, 4), "u32", host=True)

    def buf(n):
      return dev.empty(n, "bf16")

    x, norm, tmp = (buf(dim) for _ in range(3))
    qkv, z, ab, k, v, ctx = map(buf, (12288 // ranks, values, 128, kv * 256, kv * 256, values))
    convolved, heads = buf(channels), buf(values)
    gate, up, hidden = (buf(mlp) for _ in range(3))

    # Qwen RMSNorm stores a residual multiplier. Fold the unit offset during upload.
    def gamma(t):
      return dev.array(1 + floats(t), "bf16")

    emb = dev.array(tensors[PREFIX + "embed_tokens.weight"])
    pos = Var("pos")
    step = Var("step")

    def residual(slot):
      if link:
        launch(add, x=tmp, other=x, output=x, step=step, slot=slot)
      else:
        launch(add, x=x, other=tmp, output=x)

    with dev.graph() as self.step:
      launch(embed, history=self.history, weights=emb, output=x, token_pos=pos)
      for i, kind in enumerate(cfg["layer_types"]):
        layer = PREFIX + f"layers.{i}."

        def weight(name):
          return tensors[layer + name + ".weight"]

        launch(rms, x=x, other=gamma(weight("input_layernorm")), output=norm)
        if kind == "linear_attention":

          def lin(name):
            return weight("linear_attn." + name)

          projection([lin("in_proj_qkv"), lin("in_proj_z")], second=values, qkv_parts=True)(norm, qkv, output2=z)
          # Keep a and b on separate 64-row boundaries on each rank.
          abw = np.zeros((128, dim), np.uint16)
          abw[:vh], abw[64:64 + vh] = (lin(name).numpy()[shard(48)] for name in ("in_proj_a", "in_proj_b"))
          projection([], dense=abw)(norm, ab)
          alog, bias = (floats(tensors[layer + "linear_attn." + key]) for key in ("A_log", "dt_bias"))
          dynamics = dev.array(np.r_[np.exp(alog[shard(48)]), bias[shard(48)]], "bf16")
          tap_parts = np.split(floats(lin("conv1d")).reshape(10240, 4), [2048, 4096])
          taps = np.concatenate([t[shard(len(t))] for t in tap_parts]).T.copy()
          launch(conv, qkv=qkv, taps=dev.array(taps, "bf16"), history=buf(4 * channels), output=convolved, pos=pos)
          launch(
            gdn,
            conv=convolved,
            ab=ab,
            dynamics=dynamics,
            state=dev.empty(vh * 128 * 128, "fp32"),
            output=heads,
            pos=pos,
          )
          launch(gated, x=heads, z=z, gamma=dev.array(np.tile(floats(lin("norm")), 8), "bf16"), output=ctx)
          output_weight = lin("out_proj")
        elif kind == "full_attention":

          def att(name):
            return weight("self_attn." + name)

          projection([att("q_proj"), att("k_proj"), att("v_proj")], second=kv * 256, third=kv * 256)(
            norm, qkv, output2=k, output3=v
          )
          launch(
            attention,
            q_in=qkv,
            k_in=k,
            v_in=v,
            qnorm=gamma(att("q_norm")),
            knorm=gamma(att("k_norm")),
            cos=cos,
            sin=sin,
            key_cache=dev.zeros(cap * kv * 256, "bf16"),
            value_cache=dev.zeros(cap * kv * 256, "bf16"),
            context=ctx,
            start_pos=pos,
          )
          output_weight = att("o_proj")
        else:
          raise ValueError(f"unknown layer type {kind}")
        projection([output_weight], row_parallel=True)(ctx, tmp)
        residual(2 * i)
        launch(rms, x=x, other=gamma(weight("post_attention_layernorm")), output=norm)
        projection([weight("mlp.gate_proj"), weight("mlp.up_proj")], second=mlp)(norm, gate, output2=up)
        launch(swiglu, x=gate, other=up, output=hidden)
        projection([weight("mlp.down_proj")], row_parallel=True)(hidden, tmp)
        residual(2 * i + 1)

    from examples.qwen38_prefill import QwenPrompt

    scratch = (x, norm, tmp, qkv, z, ab, k, v, ctx, convolved, heads, gate, up, hidden)
    kinds = {
      embed: "embed", rms: "rms", add: "add", swiglu: "swiglu",
      conv: "conv", gdn: "state", gated: "gated", attention: "attention",
    }
    self.prompt = None
    prompt_recipe = tuple(recipe)
    self.slots = 2 * len(cfg["layer_types"])
    self.make_prompt = lambda: QwenPrompt(
      dev,
      scratch,
      prompt_recipe,
      projections,
      kinds,
      cfg["rms_norm_eps"],
      cap,
      ranks,
      profile_graph if profile else None,
    )
    logits = buf(vocab)
    with dev.graph() as self.readout:
      rms(x=x, other=gamma(tensors[PREFIX + "norm.weight"]), output=norm)
      projection([], dense=tensors["lm_head.weight"].numpy()[shard(self.vocab_size)])(norm, logits)
      exchange = {"step": step} if link else {}
      argmax(logits=logits, history=self.history, tokens=self.tokens, start_pos=pos, write_token=Var("write_token"), **exchange)

    self.measure = []
    if profile:
      labels.update(
        {
          embed: "embedding",
          rms: "RMSNorm",
          add: "residual",
          swiglu: "SwiGLU",
          argmax: "argmax",
          gdn: "GDN",
          attention: "GQA",
        }
      )
      labels.update({conv: "GDN conv", gated: "GDN gated norm"})
      self.measure = [profile_graph(dev, graph, labels) for graph in (self.step, self.readout)]

  def generate(self, ids, count):
    end = len(ids) + count - 1
    if not ids or count < 1 or end > self.max_tokens:
      raise ValueError("invalid prompt or generation length")
    if any(t < 0 or t >= self.vocab_size for t in ids):
      raise ValueError("token ID outside checkpoint vocabulary")
    self.history.copy_from(np.pad(np.uint32(ids), (0, self.history.shape[0] - len(ids))))
    out = self.tokens.numpy()
    prefix = len(ids) - 1 if len(ids) > 2 else 0
    if prefix:
      if self.prompt is None:
        self.prompt = self.make_prompt()
      self.prompt.run(prefix)
    for pos in range(prefix, end):
      self.step(pos=pos).wait(120)
      if pos >= len(ids) - 1:
        self.readout(pos=pos, write_token=int(pos + 1 < end)).wait()
        token = int(out[pos + 1, 0])
        if token in self.eos:
          break
        yield token


class Qwen38TP:
  """Two TT-link ranks with sharded attention heads and MLP, and vocabulary."""
  def __init__(self, file, metadata, devices, link, capacity, profile=False):
    self.ranks = [Qwen38(file, metadata, d, capacity, profile, rank=r, link=link) for r, d in enumerate(devices)]
    self.eos = self.ranks[0].eos
    self.tag = 1
    self.prompt = None
    self.measure = self.ranks[0].measure

  def generate(self, ids, count):
    first = self.ranks[0]
    end = len(ids) + count - 1
    if not ids or count < 1 or end > first.max_tokens or any(t < 0 or t >= first.vocab_size for t in ids):
      raise ValueError("invalid tokens or generation length")
    for rank in self.ranks:
      rank.history.copy_from(np.pad(np.uint32(ids), (0, rank.history.shape[0] - len(ids))))
    prefix = len(ids) - 1 if len(ids) > 2 else 0
    if prefix:
      from examples.qwen38_prefill import CHUNK
      for rank in self.ranks:
        if rank.prompt is None: rank.prompt = rank.make_prompt()
      self.prompt = first.prompt
      self.prompt.elapsed, self.prompt.timings = 0.0, Counter()
      for start in range(0, prefix, CHUNK):
        rows = min(CHUNK, prefix - start)
        for rank in self.ranks: rank.prompt.prepare(rows)
        begin = time.perf_counter()
        events = [rank.prompt.submit(start, rows, step=self.tag) for rank in self.ranks]
        self.tag += first.slots * rows
        for event in events: event.wait(120)
        self.prompt.elapsed += time.perf_counter() - begin
        if rows in self.prompt.measure: self.prompt.timings.update(self.prompt.measure[rows]())
    for pos in range(prefix, end):
      events = [rank.step(pos=pos, step=self.tag) for rank in self.ranks]
      self.tag += first.slots
      for event in events: event.wait(120)
      if pos < len(ids) - 1: continue
      events = [rank.readout(pos=pos, step=self.tag, write_token=int(pos + 1 < end)) for rank in self.ranks]
      self.tag += 1
      for event in events: event.wait()
      a, b = (int(rank.tokens.numpy()[pos + 1, 0]) for rank in self.ranks)
      if a != b: raise RuntimeError(f"ranks disagree at position {pos}: {a} vs {b}")
      if a in self.eos: break
      yield a


if __name__ == "__main__":
  from tokenizers import Tokenizer

  ap = argparse.ArgumentParser(description=__doc__)
  ap.add_argument("--checkpoint", type=Path, default=DEFAULT)
  ap.add_argument("--metadata", type=Path, default=METADATA, help="directory with config and tokenizer")
  ap.add_argument("--prompt", default="The capital of France is")
  ap.add_argument("--tokens", type=int, default=8)
  ap.add_argument("--profile", action="store_true", help="print dispatcher timings for the prefix and last decode step")
  ap.add_argument("--tp", type=int, choices=(1, 2), default=1, help="tensor-parallel ranks (two uses TT-link)")
  ap.add_argument("--device", type=int, default=0)
  args = ap.parse_args()
  tok = Tokenizer.from_file(str(args.metadata / "tokenizer.json"))
  ids = tok.encode(args.prompt, add_special_tokens=False).ids
  if args.tp == 2 and args.device not in (0, 1):
    ap.error("two-card TP uses device indices 0 and 1")
  if not ids or args.tokens < 1:
    ap.error("expected a nonempty prompt and positive token count")
  from contextlib import ExitStack
  with ExitStack() as stack:
    def open_device(index):
      dev = Device(index)
      stack.callback(dev.close)
      return dev
    dev = open_device(args.device)
    capacity = len(ids) + args.tokens - 1
    if args.tp == 2:
      from eth.tp import Link
      devices = [dev, open_device(1 - args.device)]
      link = Link(devices)
      stack.callback(link.close)
      model = Qwen38TP(args.checkpoint, args.metadata, devices, link, capacity, args.profile)
    else:
      model = Qwen38(args.checkpoint, args.metadata, dev, capacity, args.profile)
    generated = []
    for token in model.generate(ids, args.tokens):
      last = time.perf_counter()
      if not generated:
        start = last
      generated.append(token)
    elapsed = last - start if len(generated) > 1 else 0
    print(tok.decode(generated))
    if model.prompt is not None:
      print(
        f"{(len(ids) - 1) / model.prompt.elapsed:.1f} prompt tok/s ({len(ids) - 1} prefix tokens, device execution)",
        file=sys.stderr,
      )
    if model.prompt is not None and model.prompt.timings:
      for name, ms in model.prompt.timings.most_common():
        print(f"{ms:8.3f} ms  prefill {name}", file=sys.stderr)
    if model.measure:
      for name, ms in sum((f() for f in model.measure), Counter()).most_common():
        print(f"{ms:8.3f} ms  {name}", file=sys.stderr)
    if elapsed:
      print(f"{(len(generated) - 1) / elapsed:.2f} tok/s ({len(generated) - 1} decode steps)", file=sys.stderr)
