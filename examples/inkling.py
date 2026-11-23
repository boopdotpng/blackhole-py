"""Inkling 2 Mini decode on one Blackhole card. A TTRV graph runs one greedy decode step:
embedding, 24 layers with the middle 12 run three times, final mix, LM head and argmax, in one resident table per generated token.

Per layer pass (examples/inkling/*.ttrv): block mixes (mix: page-parallel, one exchange of partial dot products per
query), cross-pass message gates (attn/k/v batched: a K-split down projection, a forget/gain projection that sums its
partials, gate, mix), one q|k|v projection, query clipping, key/value convolutions and relative logits in one launch
(prep), attention with sinks and output gates (attention), the o projection, the residual convolution (resconv),
routed MoE (router projection split over K, router, gate/up projections with the SwiGLU in their epilogue, down
projection) and its convolution. Weight matrices are the BFP8_B images of
examples/inkling/repack.py; the router and message-gate matrices are BF16. The residual stream and the block states
stay FP32.

  python examples/inkling/repack.py                      # once: ~28 GB of BFP8 images
  python examples/inkling.py --chat --prompt "Name three primary colors." --tokens 32
  python examples/inkling.py --compare /tmp/ink_ref.npz   # replay a reference.py --dump, compare logits
"""
import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "examples/inkling"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
from helpers import safe_load  # noqa: E402
from ttrv import Device, Var  # noqa: E402
from projections import bf16_bits, bf16_image, floats, upload_experts  # noqa: E402

DEFAULT = ROOT.parent / "weights/inkling-2-mini/nvfp4"
IMAGES = DEFAULT.parent / "bfp8"
IMAGES4 = DEFAULT.parent / "bfp4"   # BFP4_B experts of the NVFP4 layers (repack.py --experts-bfp4)
D, ROW = 2304, 3072
EOS = 200006
ROUTER_SPLIT = 6  # router projection: K split, each part's 128 logits a row block of one page (summed in FP32)
GATE_SPLIT = 8  # message gates: the down projection's K split; the forget/gain projection sums the partials


def read(T, name):
  """fp32 numpy array of a BF16 or F32 checkpoint tensor."""
  t = T[name]
  a = np.asarray(t.numpy())
  if t.dtype == "BF16": return floats(a.view(np.uint16))
  return a.astype(np.float32)


def rows(*vs, width=ROW):
  out = np.zeros((len(vs), width), np.float32)
  for i, v in enumerate(vs): out[i, :len(v)] = v
  return out


def stream_files(paths, chunk=64 << 20):
  """Yield (path, uint8 array of the whole file) in order. A thread reads ahead into one of two page-aligned buffers
  with large O_DIRECT reads (no page cache), so disk reads overlap the caller's copies to the card."""
  import mmap, os, queue, threading
  size = max(p.stat().st_size for p in paths)
  size += -size % mmap.PAGESIZE
  free, ready = queue.Queue(), queue.Queue()
  for _ in range(2): free.put(mmap.mmap(-1, size))

  def reader():
    try:
      for path in paths:
        buf, n = free.get(), path.stat().st_size
        view, fd = memoryview(buf), os.open(path, os.O_RDONLY | os.O_DIRECT)
        try:
          off = 0
          while off < n:
            got = os.preadv(fd, [view[off:off + chunk]], off)
            if got <= 0: raise OSError(f"{path}: short read at {off}")
            off += got
        finally:
          view.release()
          os.close(fd)
        ready.put((path, buf))
      ready.put(None)
    except BaseException as e:
      ready.put(e)

  threading.Thread(target=reader, daemon=True).start()
  while (item := ready.get()) is not None:
    if isinstance(item, BaseException): raise item
    path, buf = item
    yield path, np.frombuffer(buf, np.uint8)
    free.put(buf)


TILE_BYTES = {"bfp4_b": 576, "bfp8_b": 1088, "bf16": 2048}


def image_tiles(data, lay):
  """A page image (examples/inkling/repack.py) as its tiles [K/32, N/32, tile bytes]."""
  kt, nt, g, tb = lay["K"] // 32, lay["N"] // 32, lay["GROUP"], TILE_BYTES[lay["format"]]
  return np.asarray(data).reshape(kt // g, lay["pitch"], g, tb)[:, :nt].swapaxes(1, 2).reshape(kt, nt, tb)


def tiles_image(t, group, fmt="bfp8_b"):
  """(page image, layout) of tiles [K/32, N/32, tile bytes], as repack.image lays them out."""
  kt, nt, tb = t.shape
  pitch = nt + (nt + 1) % 2
  img = np.zeros((kt // group, pitch, group, tb), np.uint8)
  img[:, :nt] = t.reshape(kt // group, group, nt, tb).swapaxes(1, 2)
  return img.reshape(-1), {"K": kt * 32, "N": nt * 32, "GROUP": group, "pitch": pitch, "format": fmt}


class Inkling:
  def __init__(self, dev, path=DEFAULT, images=IMAGES, max_tokens=2048, bfp4=False, overlap=True):
    self.dev = dev
    # overlap: the mix that feeds q/k/v and the attention run as async launches at the end of the worker list; the
    # projection after each streams its weights into L1 meanwhile and waits on a DRAM flag for its input
    self.overlap, self.workers = overlap, len(dev.dev.workers)
    cfg = self.cfg = json.loads((path / "config.json").read_text())["text_config"]
    self.n_layers = cfg["num_hidden_layers"]
    lc = cfg["loop_config"]
    self.loop, self.passes = range(lc["core_start"], lc["core_end"]), lc["num_passes"]
    self.block = cfg["n_layers_per_attn_res_block"]
    self.sliding = [i in cfg["local_layer_ids"] for i in range(self.n_layers)]
    if not 1 <= max_tokens <= 8192:  # beyond 8192 the full layers' log-scaling tau leaves 1
      raise ValueError("max_tokens must be within 1..8192")
    self.capacity = capacity = (max_tokens + 31) // 32 * 32
    self.max_tokens = max_tokens
    self.kernels = {}
    self.H, self.KVH = cfg["num_attention_heads"], cfg["num_key_value_heads"]
    self.INTER = cfg["intermediate_size"]
    T = safe_load(path / "model-00001-of-00001.safetensors")
    W = lambda n: read(T, "model.llm." + n)  # noqa: E731
    f32 = lambda *vs: dev.array(rows(*vs))  # noqa: E731
    b16 = lambda a: dev.array(bf16_bits(np.ascontiguousarray(a, np.float32).reshape(-1)), "bf16")  # noqa: E731

    # Globals.
    self.embed = dev.array(T["model.llm.embed.weight"])
    self.embed_norm, self.final_norm = f32(W("embed_norm.weight")), f32(W("norm.weight"))
    self.output_query = f32(W("attn_res.output_query"))
    self.ones = {n: f32(*[np.ones(D)] * n) for n in (1, 3, 4)}
    q, kvq = W("middle_cycle_cross_pass_queries").reshape(-1, 2, D), W("middle_cycle_cross_pass_kv_queries").reshape(-1, 2, D)
    mq = np.concatenate([q[:, :1], kvq, q[:, 1:]], 1)  # [loop layer, (attn, k, v, mlp), D]
    self.message_queries = [f32(*mq[j]) for j in range(len(self.loop))]

    # Per-layer constants.
    self.layers = []
    for i in range(self.n_layers):
      p = f"layers.{i}."
      L = {"sliding": self.sliding[i]}
      if i > 0: L["attn_query"] = f32(*W(f"attn_res.attn_queries.{i - 1}").reshape(-1, D))
      L["mlp_query"] = f32(W(f"attn_res.mlp_queries.{i}"))
      L["mlp_norm"] = f32(W(p + "mlp_norm.weight"))
      if self.sliding[i]: L["attn_norm"] = f32(W(p + "attn_norm.weight"))
      else: L["attn_norm"] = f32(*(W(p + f"{n}_input_norm.weight") for n in "qkv"))
      lag = lambda w: np.pad(w[:, 0, ::-1].T, ((0, 0), (0, ROW - D)))  # noqa: E731  conv1d taps -> lag order
      L["attn_taps"], L["mlp_taps"] = b16(lag(W(p + "attn_sconv.weight"))), b16(lag(W(p + "mlp_sconv.weight")))
      if self.sliding[i]: kv = np.stack([W(p + f"attn.{n}_sconv.weight")[:, 0, ::-1].T for n in "kv"])
      else: kv = np.stack([W(p + f"attn.{n}_sconv.static_w") for n in "kv"])
      kvc, qc, rc = self.KVH * 128, self.H * 128, self.H * 16   # this card's channels
      L["kv_taps"] = b16(np.pad(kv, ((0, 0), (0, 0), (0, 1024 - kvc))))
      L["q_scale"] = b16(np.pad(W(p + "attn.q_l2_clip.scale").reshape(-1), (0, -qc % 1024)))
      L["r_scale"] = b16(np.pad(W(p + "attn.rel_l2_clip.scale").reshape(-1), (0, 1024 - rc)))
      P = W(p + "attn.rel_logits_proj.proj")
      tiles = np.zeros((32, 32, 32), np.float32)
      tiles[:, :16, :] = P.reshape(16, 32, 32).transpose(1, 0, 2)
      L["rel_tiles"] = b16(tiles.reshape(32, 2, 16, 2, 16).transpose(0, 1, 3, 2, 4))
      img, _ = bf16_image(W(p + "mlp.gate.weight"), group=4)
      L["router"] = dev.empty(img.size, "bf16", tiles_per_page=4).copy_from(img)
      L["router_bias"] = dev.array(np.pad(W(p + "mlp.gate.bias"), (0, 1024 - 128)).astype(np.float32))
      if i in self.loop:
        # Message gates: the attention side's three (attn, k, v) stacked into one down and one forget/gain image.
        for key, names in (("gate_akv", ("attn", "k", "v")), ("gate_mlp", ("mlp",))):
          wd = np.zeros((64 * len(names), 2 * ROW), np.float32)
          wfg = np.zeros((2 * D * len(names), 64), np.float32)
          for j, n in enumerate(names):
            down, forget, gain = (W(p + f"controllers.{n}.{m}_weight") for m in ("down", "forget", "gain"))
            wd[64 * j:64 * (j + 1), :D], wd[64 * j:64 * (j + 1), ROW:ROW + D] = down[:, :D], down[:, D:]
            wfg[2 * D * j:2 * D * j + D], wfg[2 * D * j + D:2 * D * (j + 1)] = forget, gain
          L[key] = tuple(dev.empty(im.size, "bf16", tiles_per_page=g).copy_from(im)
                         for im, g in ((bf16_image(wd)[0], 8), (bf16_image(wfg, group=2)[0], 2)))
      self.layers.append(L)

    # Weight images.
    layout = json.loads((images / "layout.json").read_text())
    t0, nbytes = time.time(), 0
    files = [images / f"layer{i:02d}.safetensors" for i in range(self.n_layers)] + [images / "head.safetensors"]
    layout4 = json.loads((IMAGES4 / "layout.json").read_text()) if bfp4 else {}
    for path, data in stream_files(files):
      tensors = safe_load(path)
      experts = data, tensors, None  # where this layer's expert images come from
      if path.stem != "head" and str(int(path.stem.removeprefix("layer"))) in layout4:
        p4 = IMAGES4 / path.name
        experts = np.fromfile(p4, np.uint8), safe_load(p4), layout4[path.stem.removeprefix("layer").lstrip("0") or "0"]
      if path.stem == "head":
        self.head = self.upload(data, tensors["lm_head"], layout["head"]["lm_head"])
      else:
        i = int(path.stem.removeprefix("layer"))
        lay, L = layout[str(i)], self.layers[i]
        L["qkv"] = self.upload_qkv([image_tiles(data[tensors[n].offset:tensors[n].offset + tensors[n].nbytes], lay[n])
                                    for n in "qkv"])
        L["o"] = self.upload(data, tensors["o"], lay["o"])
        ed, et, el = experts
        L["w13"], L["l13"] = upload_experts(dev, ed, et, el or lay, "w13")
        L["w2"], L["l2"] = upload_experts(dev, ed, et, el or lay, "w2")
      nbytes += path.stat().st_size
      dt = time.time() - t0
      print(f"\rloaded {path.name} ({nbytes / 1e9:.1f} GB in {dt:.1f}s)", end="", file=sys.stderr, flush=True)
    print(file=sys.stderr)

    # Caches: per (layer, pass) KV caches and convolution rings.
    self.caches = {}
    for i in range(self.n_layers):
      for p in range(self.passes if i in self.loop else 1):
        self.caches[i, p] = {
          "keys": dev.zeros(self.KVH * capacity * 128, "bf16"), "values": dev.zeros(self.KVH * capacity * 128, "bf16"),
          "kv_hist": dev.zeros(2 * 4 * 1024, "bf16"),
          "attn_hist": dev.zeros(4 * ROW, "bf16"), "mlp_hist": dev.zeros(4 * ROW, "bf16")}

    # Activations, shared by every layer pass (launches run in order).
    self.activations = []
    def z(n, dtype):
      buf = dev.zeros(n, dtype)
      self.activations.append(buf)
      return buf
    self.blocks = [z(4 * ROW, "fp32") for _ in range(self.passes)]  # per pass: b0, x6, x12, x18
    self.embedding_shard = dev.local(2048)
    self.x0 = z(ROW, "bf16")
    self.xs = [z(ROW, "fp32") for _ in range(2)]
    self.loop_out = [z(ROW, "fp32") for _ in range(self.passes)]
    self.res = z(ROW, "fp32")
    self.h, self.hn = z(3 * ROW, "fp32"), z(3 * ROW, "bf16")       # mixes and their rms (message gates)
    self.hx = z(3 * ROW, "bf16")                                    # q, k, v projection inputs
    self.m, self.mn = z(4 * ROW, "fp32"), z(4 * ROW, "bf16")       # messages and their rms
    self.gx, self.fa, self.g = z(GATE_SPLIT * 512, "bf16"), z(3 * 2 * D + 1024, "fp32"), z(3 * ROW, "fp32")
    self.qo, self.ko, self.vo = z(7168, "bf16"), z(2048, "bf16"), z(2048, "bf16")
    self.qp, self.rp, self.rel = z(ROW, "bf16"), z(1024, "bf16"), z(self.H * 1024, "bf16")
    self.kp, self.vp, self.ctx, self.ao = z(1024, "bf16"), z(1024, "bf16"), z(ROW, "bf16"), z(ROW, "bf16")
    self.logits_r, self.select, self.score = z(1024, "fp32"), z(16, "fp32"), z(16, "fp32")
    self.index = dev.array(np.arange(1024, dtype=np.float32))  # router.ttrv: e at element e
    self.act, self.moe_out = z(8 * 1152, "bf16"), z(ROW, "bf16")
    self.xf = dev.zeros(ROW, "bf16")
    self.logits = dev.zeros(self.head[1]["N"], "bf16")
    self.prompt = None
    self.flags, self.nflag = dev.zeros(256 * 1024, "u32"), 0  # a 4 KiB page of producer slots per async handoff
    self.ops = 1
    self.history = dev.zeros(capacity, "u32")
    self.tokens = dev.zeros((capacity + 1, 4), "u32", host=True)

    self.step_var = Var("pos"), Var("step")
    pos = self.step_var[0]
    with dev.graph() as self.decode:
      self.emit_step(pos)
      readout_start = len(self.decode.launches)
      self.emit_readout(pos, Var("write_token"))
    self._step, self._readout = self.decode.split(readout_start)

  def step(self, pos, step=None):
    """Queue one decode step. step numbers the replay (all-reduce tags, async handoff tokens): never reused."""
    if step is None: step, self.ops = self.ops, self.ops + 1
    return self._step(pos=pos, **({"step": step} if "step" in self._step.graph.vars else {}))

  def readout(self, pos, write_token, step=None):
    if step is None: step, self.ops = self.ops, self.ops + 1
    return self._readout(pos=pos, write_token=write_token, **({"step": step} if "step" in self._readout.graph.vars else {}))

  # --- building blocks
  def kernel(self, name, **defines):
    key = (name, tuple(sorted(defines.items())))
    if key not in self.kernels:
      source = ROOT / "examples/shared" if name in ("embedding", "argmax") else HERE
      self.kernels[key] = self.dev.kernel(source / f"{name}.ttrv", **defines)
    return self.kernels[key]

  def upload(self, data, t, lay):
    raw = data[t.offset:t.offset + t.nbytes]
    dtype = "bfp8" if lay["format"] == "bfp8_b" else "bf16"
    buf = self.dev.empty(raw.nbytes if dtype == "bfp8" else raw.nbytes // 2, dtype, tiles_per_page=lay["GROUP"])
    self.dev.dev.allocator.copyin(buf.addr, memoryview(np.ascontiguousarray(raw)))
    return buf, lay

  def upload_qkv(self, parts):
    """One image of the q, k and v column tiles side by side; returns (buffer, layout with the segment ends)."""
    img, lay = tiles_image(np.ascontiguousarray(np.concatenate(parts, 1)), 8)
    buf = self.dev.empty(img.nbytes, "bfp8", tiles_per_page=8)
    self.dev.dev.allocator.copyin(buf.addr, memoryview(img))
    lay["SEG1"], lay["SEG2"] = parts[0].shape[1], parts[0].shape[1] + parts[1].shape[1]
    return buf, lay

  def project(self, mat, x, out, out32=False, wait=None):
    """y = W x with a decode projection over the image layout lay. wait: (flag, slots) of an async producer of x."""
    buf, lay = mat
    nt = lay["N"] // 32
    workers = min(nt, 128)
    workers = -(-nt // -(-nt // workers))  # even columns per worker
    bits = 8 if lay["format"] == "bfp8_b" else 16
    extra = dict(WAIT=wait[1], PREFETCH=1) if wait else {}
    args = dict(flag=wait[0], token=self.step_var[1]) if wait else {}
    self.kernel("experts", K=lay["K"], N=lay["N"], BITS=bits, GROUP=lay["GROUP"], WORKERS=workers, OUT32=int(out32),
                **extra)(x=x, weights=buf, output=out, **args)

  def row(self, buf, r, n=1):
    return buf.page_view(r * ROW * (4 if buf.dtype == "fp32" else 2), n * ROW)

  def mix(self, nb, cur, queries, *, b0=0, blocks=None, nq=1, out=None, normed=None, gamma=None, dense_gamma=False,
          cur_bf16=False, cur_stride=0, gamma_stride=ROW, signal=False, embedding_shard=0):
    """signal: run async at the end of the worker list and return (flag page, producer slots) for a WAIT consumer."""
    grid = nq * (ROW // 1024)
    extra = dict(SIGNAL=1, CORE_BASE=self.workers - grid) if signal else {}
    k = self.kernel("mix", NB=nb, B0=b0, NQ=nq, DENSE=int(out is not None), NORM=int(normed is not None),
                    DENSE_GAMMA=int(dense_gamma), CUR_BF16=int(cur_bf16), EMBEDDING_SHARD=embedding_shard, CUR_STRIDE=cur_stride, GAMMA_STRIDE=gamma_stride,
                    **extra)
    args = dict(blocks=blocks if blocks is not None else self.res, cur=cur, queries=queries)
    if out is not None: args["out"] = out
    if normed is not None: args["normed"] = normed
    if gamma is not None: args["gamma"] = gamma
    if not signal: return k(**args)
    flag = self.flag()
    k(**args, flag=flag, token=self.step_var[1], _async=True)
    return flag, grid

  def flag(self):
    view = self.flags.page_view(self.nflag * 4096, 1024)
    self.nflag += 1
    return view

  def message_gates(self, i, key, h, hn, h_stride, m, mn, gamma, gamma_stride, normed, signal=False):
    """normed rows = rms(message_gate(controllers.n, h_j, m_j)) * gamma_j for the gates stacked in key (one launch
    per stage). h, hn: the mixes and their rms (row stride h_stride); m, mn: the messages and their rms."""
    down, fg = self.layers[i][key]
    ng, S = 3 if key == "gate_akv" else 1, GATE_SPLIT
    self.kernel("experts", K=2 * ROW, N=64 * ng, BITS=16, GROUP=8, X2=1, PACK_OUT=1, SPLIT=S, WORKERS=2 * ng * S,
                GROUP_NT=2, KSHIFT=2 * ROW // 32, XROW=h_stride, X2ROW=ROW)(x=hn, x2=mn, weights=down, output=self.gx)
    self.kernel("experts", K=64, N=ng * 2 * D, BITS=16, GROUP=2, SUMS=S, WORKERS=108 if ng == 3 else 72, OUT32=1,
                GROUP_NT=2 * D // 32, KSHIFT=2)(x=self.gx, weights=fg, output=self.fa)
    self.kernel("gate", NG=ng, H_STRIDE=h_stride)(h=h, m=m, fa=self.fa, out=self.g)
    return self.mix(0, self.g, self.g, nq=ng, cur_stride=ROW, normed=normed, gamma=gamma, gamma_stride=gamma_stride,
                    signal=signal)

  # --- one layer pass
  def emit_layer(self, i, p, x, out, blocks, messages, pos):
    L, c, sliding = self.layers[i], self.caches[i, p], self.sliding[i]
    nb = sum(k < i for k in range(0, self.n_layers, self.block))
    hq, hk, hv = (self.row(self.hx, j) for j in range(3))
    # Attention inputs. With overlap the last mix runs async and hands hx to the q/k/v projection through a flag.
    sig = self.overlap
    if i == 0:
      ready = self.mix(0, x, x, normed=hq, gamma=L["attn_norm"], signal=sig)
      hk = hv = hq
    elif sliding and messages is None:
      ready = self.mix(nb, x, L["attn_query"], blocks=blocks, normed=hq, gamma=L["attn_norm"], signal=sig)
      hk = hv = hq
    elif sliding:
      h, hn = self.row(self.h, 0), self.row(self.hn, 0)
      self.mix(nb, x, L["attn_query"], blocks=blocks, out=h, normed=hn, gamma=self.ones[1])
      ready = self.message_gates(i, "gate_akv", h, hn, 0, messages[0], messages[1], L["attn_norm"], 0, self.hx, signal=sig)
    elif messages is None:
      ready = self.mix(nb, x, L["attn_query"], blocks=blocks, nq=3, normed=self.hx, gamma=L["attn_norm"], signal=sig)
    else:
      self.mix(nb, x, L["attn_query"], blocks=blocks, nq=3, out=self.h, normed=self.hn, gamma=self.ones[3])
      ready = self.message_gates(i, "gate_akv", self.h, self.hn, ROW, messages[0], messages[1], L["attn_norm"], ROW,
                                 self.hx, signal=sig)
    # Attention: the q, k and v projections in one launch (separate inputs unless they share one).
    buf, lay = L["qkv"]
    nt = lay["N"] // 32
    free = self.workers - (ready[1] if ready else 0)
    workers = min(-(-nt // 2), free)   # two columns a worker streams faster than one (fewer, longer NoC streams)
    workers = -(-nt // -(-nt // workers))
    wait = dict(WAIT=ready[1], PREFETCH=1) if ready else {}
    flag = dict(flag=ready[0], token=self.step_var[1]) if ready else {}
    self.kernel("experts", K=D, N=lay["N"], GROUP=8, WORKERS=workers, SEG1=lay["SEG1"], SEG2=lay["SEG2"],
                XSEG=int(hk is not hq), XROW=ROW, **wait)(x=hq, weights=buf, output=self.qo, output2=self.ko,
                                                         output3=self.vo, **flag)
    H, KVH = self.H, self.KVH
    # q clip, k/v convolutions and relative logits in one launch (prep.ttrv: qprep, kvconv and rel side by side)
    self.kernel("prep", H=H, DYNAMIC=int(not sliding), NORM=1 / math.sqrt(5) if sliding else 1 / 3, KV=KVH,
                TAP_BASE=0)(
      proj=self.qo, q_scale=L["q_scale"], r_scale=L["r_scale"], q_out=self.qp, k_in=self.ko, v_in=self.vo,
      weights=L["kv_taps"], history=c["kv_hist"], k_out=self.kp, v_out=self.vp, proj_tiles=L["rel_tiles"], rel=self.rel,
      pos=pos)
    grid = KVH * 8
    extra = dict(SIGNAL=1, CORE_BASE=self.workers - grid) if self.overlap else {}
    args = dict(flag=self.flag(), token=self.step_var[1], _async=True) if self.overlap else {}
    self.kernel("attention", SLIDING=int(sliding), MAX_TOKENS=self.capacity, KV_HEADS=KVH, GATE_OFFSET=H * 128,
                SINK_OFFSET=2 * H * 128 + H * 16, SINK_BASE=0, **extra)(
      q_in=self.qp, proj=self.qo, k_in=self.kp, v_in=self.vp, rel=self.rel, key_cache=c["keys"],
      value_cache=c["values"], context=self.ctx, start_pos=pos, **args)
    o_wait = (args["flag"], KVH) if self.overlap else None
    first = i % self.block == 0
    self.project(L["o"], self.ctx, self.ao, wait=o_wait)
    args = dict(y=self.ao, taps=L["attn_taps"], history=c["attn_hist"], out=self.res, pos=pos)
    if not first: args["residual"] = x
    self.kernel("resconv", RESID=int(not first))(**args)
    # MLP inputs: the block mix (with x stored as a block when the layer opens one), then the message gate.
    hm = self.row(self.hx, 0)
    nb_mlp = nb + first
    if messages is None:
      self.mix(nb_mlp, self.res, L["mlp_query"], blocks=blocks, normed=hm, gamma=L["mlp_norm"])
    else:
      h, hn = self.row(self.h, 0), self.row(self.hn, 0)
      self.mix(nb_mlp, self.res, L["mlp_query"], blocks=blocks, out=h, normed=hn, gamma=self.ones[1])
      self.message_gates(i, "gate_mlp", h, hn, 0, self.row(messages[0], 3), self.row(messages[1], 3), L["mlp_norm"], 0,
                         hm)
    # Routed experts.
    # Router logits as ROUTER_SPLIT partial sums over K (rows of one page), summed by the routing kernel.
    self.kernel("experts", K=D, N=128, BITS=16, GROUP=4, WORKERS=4 * ROUTER_SPLIT, OUT32=1, SPLIT=ROUTER_SPLIT,
                SPLIT_STRIDE=128)(x=hm, weights=L["router"], output=self.logits_r)
    self.kernel("router", PARTS=ROUTER_SPLIT)(logits=self.logits_r, bias=L["router_bias"], index=self.index,
                                              select=self.select, score=self.score)
    inter = self.INTER
    bits = 4 if L["l13"]["format"] == "bfp4_b" else 8
    # gate/up projections of the routed experts with the softcapped SwiGLU and routing weights in their epilogue
    pairs = 8 * inter // 32
    self.kernel("experts", K=D, N=8 * 2 * inter, BITS=bits, GROUP=L["l13"]["GROUP"], SELECT=1, SWIGLU=1, PACK_OUT=1,
                WORKERS=pairs // -(-pairs // 96))(x=hm, weights=L["w13"], output=self.act, select=self.select,
                                                   score=self.score)
    down = self.moe_out
    self.kernel("experts", K=8 * inter, N=D, BITS=bits, GROUP=L["l2"]["GROUP"], SELECT=2, WORKERS=72)(
      x=self.act, weights=L["w2"], output=down, select=self.select)
    self.kernel("resconv", RESID=1)(y=self.moe_out, taps=L["mlp_taps"], history=c["mlp_hist"], residual=self.res,
                                    out=out, pos=pos)

  def emit_step(self, pos):
    B, xs = self.blocks, self.xs
    self.kernel("embedding", DIM=D, RESIDUAL=self.embedding_shard, MAX_TOKENS=self.capacity)(
      history=self.history, weights=self.embed, output=self.x0, token_pos=pos)
    self.mix(0, self.x0, self.ones[1], out=self.row(B[0], 0), gamma=self.embed_norm, dense_gamma=True, cur_bf16=True,
             embedding_shard=self.embedding_shard)
    x, n = self.row(B[0], 0), 0

    def run(i, p, x, blocks, messages=None, out=None):
      nonlocal n
      if out is None:
        out, n = xs[n], 1 - n
      self.emit_layer(i, p, x, out, blocks, messages, pos)
      return out

    for i in range(self.loop.start):
      x = run(i, 0, x, B[0], out=self.row(B[0], 1) if i == self.loop.start - 1 else None)
    self.kernel("copy", N=2 * ROW)(src=B[0], dst=B[1], dst2=B[2])
    for p in range(self.passes):
      x = self.row(B[0], 1)
      if p:  # messages: the previous pass's block after the loop's first layer, and its loop output
        prev_block, prev_out = self.row(B[p - 1], 2), self.loop_out[p - 1]
      for j, i in enumerate(self.loop):
        messages = None
        if p:
          self.mix(1, prev_out, self.message_queries[j], b0=2, blocks=B[p - 1], nq=4, out=self.m, normed=self.mn,
                   gamma=self.ones[4])
          messages = (self.m, self.mn)
        last = p == self.passes - 1
        out = None
        if i == 2 * self.block - 1: out = self.row(B[p], 2)           # x12
        if i == self.loop.stop - 1: out = self.row(B[p], 3) if last else self.loop_out[p]
        x = run(i, p, x, B[p], messages, out)
    for i in range(self.loop.stop, self.n_layers):
      x = run(i, 0, x, B[-1])
    self.final_x = x

  def emit_readout(self, pos, write_token):
    self.mix(4, self.final_x, self.output_query, blocks=self.blocks[-1], normed=self.xf, gamma=self.final_norm)
    self.project(self.head, self.xf, self.logits)
    self.kernel("argmax", VOCAB=self.cfg["unpadded_vocab_size"], MAX_TOKENS=self.capacity)(
      logits=self.logits, history=self.history, tokens=self.tokens, start_pos=pos, write_token=write_token)

  def set_history(self, ids):
    self.history.copy_from(np.pad(np.uint32(ids), (0, self.capacity - len(ids))))

  def logits_numpy(self):
    """The last readout's softcapped logits (unpadded vocabulary)."""
    z = floats(self.logits.numpy())[:self.cfg["unpadded_vocab_size"]]
    cap = self.cfg["final_logit_softcapping"]
    return np.tanh(z / cap) * cap

  def generate(self, ids, tokens):
    end = len(ids) + tokens - 1
    if not ids or tokens < 1 or end > self.max_tokens:
      raise ValueError("expected a nonempty prompt and a generation length within the allocated context")
    self.history.copy_from(np.pad(np.uint32(ids), (0, self.capacity - len(ids))))
    out = self.tokens.numpy()
    prefix = len(ids) - 1
    if prefix:
      from examples.inkling_prefill import InklingPrompt
      with self.dev.phase("inkling-prefill"):
        if self.prompt is None: self.prompt = InklingPrompt(self)
        self.prompt.run(prefix)
    for pos in range(prefix, end):
      values = dict(pos=pos, write_token=int(pos + 1 < end))
      if "step" in self.decode.graph.vars:
        values["step"], self.ops = self.ops, self.ops + 1
      self.decode(**values).wait(timeout=60)
      token = int(out[pos + 1, 0])
      yield token
      if token == EOS: return


def chat(path, prompt):
  sys.path.insert(0, str(HERE))
  from reference import chat as render
  return render(path, prompt)


if __name__ == "__main__":
  from tokenizers import Tokenizer
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument("--device", type=int, default=0)
  ap.add_argument("--bfp4", action="store_true", help="BFP4_B experts in the NVFP4 layers (repack.py --experts-bfp4)")
  ap.add_argument("--prompt", default="The capital of France is")
  ap.add_argument("--chat", action="store_true", help="wrap the prompt in the chat template (thinking effort 0)")
  ap.add_argument("--tokens", type=int, default=16)
  ap.add_argument("--max-tokens", type=int, default=2048, help="allocated context")
  ap.add_argument("--compare", type=Path, help="reference .npz from reference.py --dump: replay its tokens, compare logits")
  a = ap.parse_args()
  tok = Tokenizer.from_file(str(DEFAULT / "tokenizer.json"))
  dev = Device(a.device)
  try:
    t0 = time.time()
    model = Inkling(dev, max_tokens=a.max_tokens, bfp4=a.bfp4)
    print(f"ready in {time.time() - t0:.1f}s", file=sys.stderr)
    if a.compare:
      ref = np.load(a.compare)
      seq = [int(t) for t in list(ref["prompt"]) + list(ref["generated"])]
      model.set_history(seq)
      for pos, want in enumerate(ref["logits"]):
        model.step(pos=pos)
        model.readout(pos=pos, write_token=0).wait(timeout=60)
        got = model.logits_numpy()
        pw, pg = (np.exp(z - z.max()) / np.exp(z - z.max()).sum() for z in (want, got))
        kl = float((pw * (np.log(pw + 1e-30) - np.log(pg + 1e-30))).sum())
        print(f"pos {pos}: top-1 ref {want.argmax()} device {got.argmax()} {'ok' if want.argmax() == got.argmax() else 'DIFF'}"
              f"  KL {kl:.4f}  max |dlogit| {np.abs(got - want).max():.3f}")
    else:
      ids = tok.encode(chat(DEFAULT, a.prompt) if a.chat else a.prompt, add_special_tokens=False).ids
      generated, stamps = [], []
      for token in model.generate(ids, a.tokens):
        stamps.append(time.perf_counter())
        generated.append(token)
        print(tok.decode([token], skip_special_tokens=False), end="", flush=True)
      print()
      if model.prompt is not None and model.prompt.elapsed:
        print(f"{(len(ids)-1) / model.prompt.elapsed:.2f} prompt tok/s ({len(ids)-1} prefix tokens, worker replay)", file=sys.stderr)
      if len(stamps) > 1:
        rate = (len(stamps) - 1) / (stamps[-1] - stamps[0])
        print(f"{len(ids)} prompt tokens, {len(generated)} generated; decode {rate:.2f} tok/s", file=sys.stderr)
  finally: dev.close()
