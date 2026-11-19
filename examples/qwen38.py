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
import ttrv  # noqa: E402
from helpers import safe_load  # noqa: E402
from ttrv.runtime import Device, Kernel, Var  # noqa: E402

KERNEL = Path(__file__).with_name("nanbeige") / "projection.ttrv"

DEFAULT = ROOT.parent / "weights/qwen3.8-27b/mixed_bfp4mlp_bfp8attn/model.safetensors"
METADATA = Path.home() / "models/qwen3.8-27b/bf16"
PREFIX = "model.language_model."


def upload_packed(dev, parts, group):
  t = parts[0]
  k = t.logical_shape[1]
  n = sum(part.logical_shape[0] for part in parts)
  bits = {"bfp4_b": 4, "bfp8_b": 8}[t.packed_format]
  tiles = [part.numpy() for part in parts]
  row_bytes = n // 32 * t.shape[-1]
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


def head_kernel(dev, linear, *, prompt=False, cache_only=False, finish=False):
  # Use the runtime's ordinary parameter binding, scratch allocator and graph dispatch
  # for a C worker image. Blackhole supports scalar FP32 arithmetic on the worker.
  names = (
    "qkv z ab conv dynamics gamma history state output" if linear else "q k v qnorm knorm rope keys values output"
  ).split()
  if linear and prompt: names.append("next_history")
  params = [f"param {name}: {'fp32' if name == 'state' else 'bf16'}[]" for name in names]
  scratch = 81920 if linear else 16384 if prompt and not cache_only else 8192
  params.append("param pos: u32")
  if prompt:
    params.append("param rows: u32")
  grid = (120 if finish else 96 if prompt else 48) if linear else (96 if prompt else 24)
  source = "\n".join([f"grid {grid}", *params, f"l1 scratch: u8[{scratch}]", "fn brisc() { }"])
  spec = ttrv.build(source)
  flags = [
    "-O2",
    "-march=rv32imf_zicsr_zba_zbb",
    f"-DSCRATCH_ADDR={spec.manifest['storage']['scratch']['address']}",
    f"-DSCRATCH_BYTES={scratch}",
    f"-DPOS_SLOT={spec.manifest['params']['pos']['slot']}",
  ]
  if prompt:
    flags.extend(["-DPROMPT=1", f"-DGRID={grid}", f"-DROWS_SLOT={spec.manifest['params']['rows']['slot']}"])
  if finish:
    flags.append("-DGDN_FINISH=1")
  if cache_only:
    flags.append("-DCACHE_ONLY=1")
  if linear:
    flags.append("-DGDN")
  directory = Path(__file__).with_name("qwen38")
  roles = {"brisc": ([directory / "head.c", "noc.c"], flags)}
  if linear and not finish:
    roles["trisc2"] = ([directory / "state.c"], [*flags, "-march=rv32imf_zve32f_zvl128b_zicsr_zba_zbb"])
  elif not linear and prompt and not cache_only:
    roles["trisc2"] = ([directory / "gqa.c"], [*flags, "-march=rv32imf_zve32f_zvl128b_zicsr_zba_zbb"])
  spec.images = fw.program(roles)
  return Kernel(dev, spec)


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
  def __init__(self, file, metadata, dev, max_tokens, profile=False):
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
    tensors = safe_load(file)
    kernels, labels = {}, {}
    projections, recipe = {}, []

    def launch(kernel, **args):
      recipe.append((kernel, args))
      kernel(**args)

    def projection(parts, dense=None, second=0, third=0):
      if dense is None:
        bits = {"bfp4_b": 4, "bfp8_b": 8}[parts[0].packed_format]
        group = 16 if bits == 4 else 8
        n, k = sum(t.logical_shape[0] for t in parts), parts[0].logical_shape[1]
        matrix = upload_packed(dev, parts, group)
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
    add = dev.kernel(vector, DIM=dim)
    swiglu = dev.kernel(vector, DIM=mlp, SWIGLU=1)
    llama = KERNEL.parent.parent / "llama3"
    embed = dev.kernel(llama / "embedding.ttrv", EMBED_TILES=dim // 1024)
    argmax = dev.kernel(llama / "argmax.ttrv", VOCAB=vocab, MAX_TOKENS=cap)
    gdn, attention = head_kernel(dev, True), head_kernel(dev, False)
    rope = cfg["rope_parameters"]
    rd = int(cfg["head_dim"] * rope["partial_rotary_factor"])
    if rd != 64:
      raise ValueError("expected 64 rotary channels")
    angle = np.arange(cap, dtype=np.float32)[:, None] * rope["rope_theta"] ** (
      -np.arange(0, rd, 2, dtype=np.float32) / rd
    )
    angles = dev.array(np.concatenate((np.cos(angle), np.sin(angle)), axis=1), "bf16")
    self.history = dev.zeros(cap, "u32")
    self.tokens = dev.zeros((cap + 1, 4), "u32", host=True)

    def buf(n):
      return dev.empty(n, "bf16")

    x, norm, tmp = (buf(dim) for _ in range(3))
    qkv, z, ab, k, v, ctx = map(buf, (12288, 6144, 128, 1024, 1024, 6144))
    gate, up, hidden = (buf(mlp) for _ in range(3))

    # Qwen RMSNorm stores a residual multiplier. Fold the unit offset during upload.
    def gamma(t):
      return dev.array(1 + floats(t), "bf16")

    emb = dev.array(tensors[PREFIX + "embed_tokens.weight"])
    pos = Var("pos")
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

          projection([lin("in_proj_qkv"), lin("in_proj_z")], second=6144)(norm, qkv, output2=z)
          # The two 48-row BF16 projections each get 16 padding rows for whole output tiles.
          abw = np.zeros((128, dim), np.uint16)
          abw[:48], abw[64:112] = lin("in_proj_a").numpy(), lin("in_proj_b").numpy()
          projection([], dense=abw)(norm, ab)
          alog, bias = (floats(tensors[layer + "linear_attn." + key]) for key in ("A_log", "dt_bias"))
          launch(
            gdn,
            qkv=qkv,
            z=z,
            ab=ab,
            conv=dev.array(lin("conv1d")),
            dynamics=dev.array(np.r_[np.exp(alog), bias], "bf16"),
            gamma=dev.array(lin("norm")),
            history=buf(48 * 9 * 128),
            state=dev.empty(48 * 128 * 128, "fp32"),
            output=ctx,
            pos=pos,
          )
          output_weight = lin("out_proj")
        elif kind == "full_attention":

          def att(name):
            return weight("self_attn." + name)

          projection([att("q_proj"), att("k_proj"), att("v_proj")], second=1024, third=1024)(
            norm, qkv, output2=k, output3=v
          )
          launch(
            attention,
            q=qkv,
            k=k,
            v=v,
            qnorm=dev.array(att("q_norm")),
            knorm=dev.array(att("k_norm")),
            rope=angles,
            keys=buf(cap * 1024),
            values=buf(cap * 1024),
            output=ctx,
            pos=pos,
          )
          output_weight = att("o_proj")
        else:
          raise ValueError(f"unknown layer type {kind}")
        projection([output_weight])(ctx, tmp)
        launch(add, x=x, other=tmp, output=x)
        launch(rms, x=x, other=gamma(weight("post_attention_layernorm")), output=norm)
        projection([weight("mlp.gate_proj"), weight("mlp.up_proj")], second=mlp)(norm, gate, output2=up)
        launch(swiglu, x=gate, other=up, output=hidden)
        projection([weight("mlp.down_proj")])(hidden, tmp)
        launch(add, x=x, other=tmp, output=x)

    from examples.qwen38_prefill import QwenPrompt

    scratch = (x, norm, tmp, qkv, z, ab, k, v, ctx, gate, up, hidden)
    kinds = {embed: "embed", rms: "rms", add: "add", swiglu: "swiglu", gdn: "gdn", attention: "attention"}
    self.prompt = None
    prompt_recipe = tuple(recipe)
    self.make_prompt = lambda: QwenPrompt(
      dev,
      scratch,
      prompt_recipe,
      projections,
      kinds,
      cfg["rms_norm_eps"],
      lambda **kw: head_kernel(dev, **kw),
      profile_graph if profile else None,
    )
    logits = buf(vocab)
    with dev.graph() as self.readout:
      rms(x=x, other=gamma(tensors[PREFIX + "norm.weight"]), output=norm)
      projection([], dense=tensors["lm_head.weight"].numpy())(norm, logits)
      argmax(logits=logits, history=self.history, tokens=self.tokens, start_pos=pos, write_token=Var("write_token"))

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
      self.measure = [profile_graph(dev, graph, labels) for graph in (self.step, self.readout)]

  def generate(self, ids, count, *, chunked=True):
    end = len(ids) + count - 1
    if not ids or count < 1 or end > self.max_tokens:
      raise ValueError("invalid prompt or generation length")
    if any(t < 0 or t >= self.vocab_size for t in ids):
      raise ValueError("token ID outside checkpoint vocabulary")
    self.history.copy_from(np.pad(np.uint32(ids), (0, self.history.shape[0] - len(ids))))
    out = self.tokens.numpy()
    prefix = len(ids) - 1 if chunked and len(ids) > 2 else 0
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


if __name__ == "__main__":
  from tokenizers import Tokenizer

  ap = argparse.ArgumentParser(description=__doc__)
  ap.add_argument("--checkpoint", type=Path, default=DEFAULT)
  ap.add_argument("--metadata", type=Path, default=METADATA, help="directory with config and tokenizer")
  ap.add_argument("--prompt", default="The capital of France is")
  ap.add_argument("--tokens", type=int, default=8)
  ap.add_argument("--serial", action="store_true", help="use single-token decode for the prompt")
  ap.add_argument("--profile", action="store_true", help="print dispatcher timings for the prefix and last decode step")
  ap.add_argument("--device", type=int, default=0)
  args = ap.parse_args()
  tok = Tokenizer.from_file(str(args.metadata / "tokenizer.json"))
  ids = tok.encode(args.prompt, add_special_tokens=False).ids
  if not ids or args.tokens < 1:
    ap.error("expected a nonempty prompt and positive token count")
  dev = Device(args.device)
  try:
    model = Qwen38(args.checkpoint, args.metadata, dev, len(ids) + args.tokens - 1, args.profile)
    generated = []
    for token in model.generate(ids, args.tokens, chunked=not args.serial):
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
  finally:
    dev.close()
