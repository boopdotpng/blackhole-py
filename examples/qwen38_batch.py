"""Batched Qwen3.8-27B for examples/engine.py. One captured graph runs a decode step for every live sequence at once,
one sequence per row of two 32-row activation panels, so each weight read from DRAM serves all of them.

Per step:
  embedding       row r's token, from the step table (batch/embedding.ttrv)
  per layer       RMSNorm on panel tiles, then
    linear (48)   in_proj_qkv|z and a|b on panel tiles, unpacked to rows; the causal conv (qwen38/batch_conv.ttrv)
                  and the delta-rule recurrence (qwen38/batch_state.ttrv), each row against its own slot's conv
                  history and FP32 state; the gated RMSNorm (qwen38/gdn_out.ttrv) row by row
    full (16)     q|gate, k, v on panel tiles, unpacked to rows; q/k RMSNorm, partial RoPE, KV append and gated
                  attention per (row, KV head), each row against its own slot's cache (qwen38/batch_attention.ttrv)
                  then o_proj, gate/up (fused SwiGLU) and down on panel tiles, residual adds on tiles
  readout         RMSNorm and the LM head for the panels, in column ranges; the live rows' logits go straight to
                  pinned host memory (qwen38/unpack_host.ttrv) and the host samples

A slot owns a region of every per-layer state buffer: the GDN recurrent state (48 heads x 128 x 128 FP32, 3 MiB per
layer), the conv history ring and the full-attention KV caches (`context` positions). The host writes each live row's
(position, active, slot, token) into a pinned table before the step.

Prompts run through the single-sequence prompt graphs (examples/qwen38_prefill.py) on the single-sequence model's own
state buffers: a continued prompt first copies the slot's state in, and each prefill copies the updated state back
out to the slot (qwen38/copy.ttrv; about 150 MiB of GDN state each way). The recurrent state cannot be rewound, so a
slot's cached tokens are reusable only when they are a prefix of the new prompt.

  python examples/qwen38_batch.py --slots 8 --prompts 16 --tokens 64
"""
import argparse, sys, time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ttrv import Device, hw
from ttrv.runtime import Buffer, Var
from ttrv.layout import ResidentCapacityError
from ttrv.parse import Error as TtrvError
from examples.qwen38 import DEFAULT, METADATA, Qwen38
from examples.prefill import summa_shapes
from examples.engine import Engine, Sequence

HERE = Path(__file__).resolve().parent
PANELS = 2
ROWS = 32 * PANELS
SINGLE = "qwen-single"     # phase of the single-sequence model (prompt staging and the reference decoder)
PREFILL = "qwen-prefill"
VH, CHANNELS = 48, 10240
STATE = VH * 128 * 128     # FP32 recurrent state elements per layer and slot
RING = 4 * CHANNELS        # BF16 conv history elements per layer and slot
TABLE_L1 = 160 << 10       # worker L1 kept free for the decode graph's table and argument blocks


def dram_free(dev):
  from fw import DRAM_BANK_SIZE
  return dev.dev.dram_banks * DRAM_BANK_SIZE - dev.dev.allocator.top


def slot_bytes(cfg, cap):
  kinds = cfg["layer_types"]
  linear, full = kinds.count("linear_attention"), kinds.count("full_attention")
  return linear * (4 * STATE + 2 * RING) + full * 2 * 2 * cfg["num_key_value_heads"] * cap * cfg["head_dim"]


def host_matrix(dev, rows, cols):
  """A BF16 [rows, cols] kernel output in its own pinned host memory (the runtime's host heap is 16 MiB), and its
  numpy view."""
  pin = dev.dev.pinned(rows * cols * 2)
  buf = Buffer.__new__(Buffer)
  buf.device, buf.shape, buf.dtype, buf.host, buf.nbytes = dev, (rows * cols,), "bf16", True, rows * cols * 2
  buf.addr, buf.offset = pin.noc_addr, None
  return buf, np.ndarray((rows, cols), np.uint16, pin.mem)


class QwenBatch:
  def __init__(self, dev, slots=8, context=4096, checkpoint=DEFAULT, metadata=METADATA, model=None):
    if not 0 <= slots <= ROWS: raise ValueError(f"1 to {ROWS} slots, or 0 for as many as DRAM holds")
    if model is None:
      with dev.phase(SINGLE): model = Qwen38(checkpoint, metadata, dev, context)
    self.model = m = model
    cfg, cap = m.cfg, m.capacity
    self.cfg, self.capacity, self.eos, self.vocab = cfg, cap, m.eos, cfg["vocab_size"]
    self.prefill_budget = 128
    reserve = 1 << 30      # batched activations, logits and tiles, with headroom
    free = dram_free(dev)
    fit = max(0, (free - reserve) // slot_bytes(cfg, cap))
    if slots == 0: slots = min(ROWS, fit)
    self.dev, self.slots = dev, slots
    need = slots * slot_bytes(cfg, cap)
    if slots < 1 or need + reserve > free:
      raise MemoryError(f"{slots} slots of {cap} positions need {need / 2**30:.1f} GiB of DRAM; {free / 2**30:.1f} GiB "
                        f"is free after the weights, enough for {fit} slots at this context (each slot holds "
                        f"{slot_bytes(cfg, cap) / 2**20:.0f} MiB of recurrent state and KV cache)")
    dim, mlp, vocab = cfg["hidden_size"], cfg["intermediate_size"], cfg["vocab_size"]
    kv, heads = cfg["num_key_value_heads"], cfg["num_attention_heads"]
    workers = len(dev.dev.workers)
    kernels = {}
    def kernel(path, **defines):
      key = path, tuple(sorted(defines.items()))
      if key not in kernels: kernels[key] = dev.kernel(HERE / path, **defines)
      return kernels[key]
    def stride(width): return (width + 1023) // 1024 * 1024
    def matrix(width): return dev.empty(ROWS * stride(width), "bf16")
    tiles = lambda width: dev.empty(ROWS * width, "bf16")

    # ---- the single model's recipe, one entry list per layer
    layers, current, adds = [], [], 0
    for launch in m.recipe[1:]:
      current.append(launch)
      adds += m.kinds.get(launch[0]) == "add"
      if adds == 2: layers.append(current); current, adds = [], 0
    assert not current and len(layers) == cfg["num_hidden_layers"]
    def projections(layer): return [(m.projections[k], a["weights"]) for k, a in layer if k in m.projections]
    def of(layer, kind): return [a for k, a in layer if m.kinds.get(k) == kind]

    # ---- per-slot state
    self.table = dev.zeros((ROWS, 16), "u32", host=True)
    table = dev.zeros(ROWS * 16, "u32")   # its copy in DRAM, for the kernels whose many workers read it
    self.states, self.rings, self.caches = [], [], []   # (single, batched) pairs
    for layer in layers:
      if of(layer, "state"):
        single = of(layer, "state")[0]["state"]
        self.states.append((single, dev.empty(slots * STATE, "fp32")))
        self.rings.append((of(layer, "conv")[0]["history"], dev.zeros(slots * RING, "bf16")))
      else:
        a = of(layer, "attention")[0]
        for name in ("key_cache", "value_cache"):
          self.caches.append((a[name], dev.zeros(slots * a[name].shape[0], "bf16")))
    self.cache_elems = self.caches[0][0].shape[0]      # one slot: KV_HEADS heads of cap / 32 blocks of 8 tiles

    # ---- activations
    x, qkv, z, ab, conv, mixed, ctx = (matrix(w) for w in (dim, CHANNELS, VH * 128, 128, CHANNELS, VH * 128, VH * 128))
    q, k, v = matrix(heads * 512), matrix(kv * 256), matrix(kv * 256)
    self.vstride = stride(vocab)
    logits, self.logits = host_matrix(dev, ROWS, self.vstride)
    self.wide_logits = np.empty((ROWS, vocab), np.uint32)
    xt, normt, outt, ctxt, hiddent = tiles(dim), tiles(dim), tiles(dim), tiles(VH * 128), tiles(mlp)
    wide = [tiles(w) for w in (heads * 512, VH * 128, kv * 256)]   # projection outputs before unpacking

    def to_tiles(src, dst, width, row_stride):
      kernel("prefill/pack.ttrv", K=width, STRIDE=row_stride, BLOCK=128, PANELS=PANELS, TILE_ROWS=32,
             WORKERS=min(PANELS * width // 128, workers))(x=src, output=dst, rows=32)
    def to_rows(src, dst, width):
      block = 128 if width % 128 == 0 else 32
      kernel("prefill/unpack.ttrv", N=width, PANELS=PANELS, BLOCK=block,
             WORKERS=min(workers, PANELS * width // block))(x=src, output=dst)
    gammas = {}
    def gamma(buf):  # identical rows: the norm multiplier as panels of tiles
      if id(buf) not in gammas:
        gammas[id(buf)] = tiles(dim)
        to_tiles(buf, gammas[id(buf)], dim, 0)
      return gammas[id(buf)]
    def vector(op, a, b, out, width):
      kt = width // 32
      if op == 2: peers = min(16, workers // PANELS, kt); n = PANELS * peers
      else: peers, n = 1, min(workers, PANELS * kt)
      kernel("prefill/vector.ttrv", OP=op, PANELS=PANELS, KT=kt, PEERS=peers, WORKERS=n, EPS=cfg["rms_norm_eps"])(
        x=a, other=b, output=out)
    def summa(k_, n, bits, group, swiglu=False, second=0, third=0, **extra):
      epilogue = dict(SWIGLU=1) if swiglu else dict(SECOND=second, THIRD=third)
      # Leave room for the step graph's table: about 1000 launches over 64 layers.
      for shape in summa_shapes(k_, n, bits, group, PANELS, swiglu, hw.L1_SIZE - dev.top - TABLE_L1):
        try:
          return kernel("prefill/summa_projection.ttrv", K=k_, N=n, BITS=bits, GROUP=group, PAD=0, PANELS=PANELS,
                        **epilogue, **shape, **extra)
        except (ResidentCapacityError, TtrvError) as e:
          if isinstance(e, TtrvError) and e.id != "storage.overflow": raise
      return None
    def tiled(spec, weights, src, outputs, swiglu=False):  # panel tiles in and out (SUMMA)
      k_, n, bits, group, second, third = spec
      project = summa(k_, n, bits, group, swiglu, second, third)
      if project is None: raise ResidentCapacityError(f"no SUMMA shape fits for {k_}x{n}")
      project(x=src, weights=weights, **dict(zip(("output", "output2", "output3"), outputs)))
    def head_rows(spec, weights, src, dst):
      # The LM head's weight buffers do not fit L1 in one launch: column ranges of whole 1024-column pages, each
      # reading its pages of the full matrix (NT_PITCH) and unpacked into its columns of the logits rows.
      k_, n, bits, group, _, _ = spec
      for parts in range(1, 65):
        width = -(-n // parts // 1024) * 1024
        if summa(k_, width, bits, group, NT_PITCH=n // 32) is not None: break
      page = group * {4: 576, 8: 1088, 16: 2048}[bits]
      for col in range(0, n, width):
        size = min(width, n - col)
        part = tiles(size) if size != width or col == 0 else part
        summa(k_, size, bits, group, NT_PITCH=n // 32)(
          x=src, weights=weights.page_view(col // 32 * page, weights.shape[0] - col * k_), output=part)
        block = 128 if size % 128 == 0 else 32
        kernel("qwen38/unpack_host.ttrv", N=size, STRIDE=self.vstride, PANELS=PANELS, BLOCK=block,
               WORKERS=min(workers, PANELS * size // block))(x=part, output=dst, col=col, rows=Var("rows"))

    embed = kernel("batch/embedding.ttrv", ROWS=ROWS, EMBED_TILES=dim // 1024)
    lanes = workers // (CHANNELS // 1024)
    conv_kernel = kernel("qwen38/batch_conv.ttrv", ROWS=slots, LANES=min(lanes, slots))
    state_kernel = kernel("qwen38/batch_state.ttrv", ROWS=slots, WORKERS=min(128, workers))
    out_lanes = min(slots, workers // 6)
    # Split each row's cache over as many partitions as the grid holds for all slots at once.
    parts = next(p for p in (8, 4, 2, 1) if slots * 2 * kv * p <= workers or p == 1)
    group_rows = min(slots, workers // (2 * kv * parts))
    attend = kernel("qwen38/batch_attention.ttrv", MAX_TOKENS=cap, KV_HEADS=kv, ROWS=group_rows, PARTITIONS=parts)
    for layer in layers:
      for a in of(layer, "rms"): gamma(a["other"])
    gamma(m.final_norm)
    dev.synchronize()

    with dev.graph() as self.step_graph:
      kernel("qwen38/stage_table.ttrv", ROWS=ROWS)(table=self.table, output=table)
      embed(weights=m.embedding, output=x, table=self.table)
      to_tiles(x, xt, dim, stride(dim))
      state_layer = attention_layer = 0
      for layer in layers:
        (norm_in, norm_post), proj = of(layer, "rms"), projections(layer)
        vector(2, xt, gamma(norm_in["other"]), normt, dim)
        if of(layer, "state"):
          (qkvz, wq), (abspec, wab) = proj[:2]
          tiled(qkvz, wq, normt, wide[:2])
          to_rows(wide[0], qkv, CHANNELS)
          to_rows(wide[1], z, VH * 128)
          tiled(abspec, wab, normt, [wide[2]])
          to_rows(wide[2], ab, 128)
          c, s, g = of(layer, "conv")[0], of(layer, "state")[0], of(layer, "gated")[0]
          conv_kernel(qkv=qkv, taps=c["taps"], history=self.rings[state_layer][1], output=conv, table=table)
          state_kernel(conv=conv, ab=ab, dynamics=s["dynamics"], state=self.states[state_layer][1], output=mixed,
                       table=table)
          for first in range(0, slots, out_lanes):
            size = min(out_lanes, slots - first)
            view = lambda t: t.page_view(2 * first * VH * 128, size * VH * 128)
            kernel("qwen38/gdn_out.ttrv", PACKED=0, ROWS=size)(x=view(mixed), z=view(z), gamma=g["gamma"],
                                                                 output=view(ctx))
          state_layer += 1
        else:
          spec, wq = proj[0]
          tiled(spec, wq, normt, [wide[0], wide[2], wide[1]])   # q|gate, k, v
          to_rows(wide[0], q, heads * 512)
          to_rows(wide[2], k, kv * 256)
          to_rows(wide[1], v, kv * 256)
          a = of(layer, "attention")[0]
          keys, values = self.caches[2 * attention_layer][1], self.caches[2 * attention_layer + 1][1]
          for base in range(0, slots, group_rows):
            attend(q_in=q, k_in=k, v_in=v, qnorm=a["qnorm"], knorm=a["knorm"], cos=a["cos"], sin=a["sin"],
                   key_cache=keys, value_cache=values, context=ctx, table=table, row_base=base)
          attention_layer += 1
        to_tiles(ctx, ctxt, VH * 128, VH * 128)
        (ospec, wo), (upspec, wup), (downspec, wdown) = proj[-3:]
        tiled(ospec, wo, ctxt, [outt])
        vector(0, outt, xt, xt, dim)
        vector(2, xt, gamma(norm_post["other"]), normt, dim)
        tiled(upspec, wup, normt, [hiddent], swiglu=True)
        tiled(downspec, wdown, hiddent, [outt])
        vector(0, outt, xt, xt, dim)
      vector(2, xt, gamma(m.final_norm), normt, dim)
      head, head_args = m.lm_head
      head_rows(m.projections[head], head_args["weights"], normt, logits)

    print(f"decode phase L1: resident top {dev.top:#x}, scratch base {dev.scratch_base:#x}", file=sys.stderr)
    # ---- state moves between the single model's buffers and the slots (qwen38/copy.ttrv)
    copy_b = kernel("qwen38/copy.ttrv", T="bf16", CHUNK=8192, WORKERS=min(128, workers))
    copy_f = kernel("qwen38/copy.ttrv", T="fp32", CHUNK=4096, WORKERS=min(128, workers))
    def mover(src, dst):  # src, dst: 0 for the single model's buffers, 1 for the slots
      with dev.graph() as graph:
        for pair in self.states:
          copy_f(src=pair[src], dst=pair[dst], src_at=Var("s_from"), dst_at=Var("s_to"), runs=1, stride=0, count=STATE)
        for pair in self.rings:
          copy_b(src=pair[src], dst=pair[dst], src_at=Var("r_from"), dst_at=Var("r_to"), runs=1, stride=0, count=RING)
        for pair in self.caches:
          copy_b(src=pair[src], dst=pair[dst], src_at=Var("kv_from"), dst_at=Var("kv_to"), runs=kv,
                 stride=self.cache_elems // kv, count=Var("kv_count"))
      return graph
    self.movers = {(src, dst): mover(src, dst) for src, dst in ((0, 1), (1, 0), (1, 1))}

  def move(self, src, dst, src_slot, dst_slot, first, end):
    """Copy recurrent state and conv history, and KV cache blocks covering positions first .. end - 1."""
    b0, b1 = first // 32, -(-end // 32)
    at = lambda slot, side, size: slot * size if side else 0
    block = 8 * 1024
    self.movers[src, dst](s_from=at(src_slot, src, STATE), s_to=at(dst_slot, dst, STATE),
                          r_from=at(src_slot, src, RING), r_to=at(dst_slot, dst, RING),
                          kv_from=at(src_slot, src, self.cache_elems) + b0 * block,
                          kv_to=at(dst_slot, dst, self.cache_elems) + b0 * block, kv_count=(b1 - b0) * block).wait(60)

  # ---- backend interface (examples/engine.py)
  def reusable(self, slot, ids, held):
    """The recurrent state holds exactly the held tokens: all of them if they start the prompt, else none."""
    n = len(held)
    return n if n <= len(ids) and np.array_equal(np.asarray(ids[:n]), held) else 0

  def copy_prefix(self, src, dst, n):
    self.move(1, 1, src, dst, 0, n)
    return True

  def prefill(self, slot, ids, start, end):
    m = self.model
    if start: self.move(1, 0, slot, 0, 0, start)
    history = np.zeros(m.history.shape[0], np.uint32)
    history[:len(ids)] = ids
    m.history.copy_from(history)
    with self.dev.phase(PREFILL):
      if m.prompt is None: m.prompt = m.make_prompt()
      m.prompt.run(end, serial_step=m.step, start=start)
    self.move(0, 1, 0, slot, start, end)
    return end - start

  def decode(self, rows):
    table = self.table.numpy()
    table[:] = 0
    for row, (slot, pos, token) in enumerate(rows):
      table[row, :4] = pos, 1, slot, token
    self.step_graph(rows=len(rows)).wait(60)
    out = self.wide_logits[:len(rows)]
    np.left_shift(self.logits[:len(rows), :self.vocab], 16, out=out, dtype=np.uint32)
    return out.view(np.float32)


def chat_prompt(text):
  return f"<|im_start|>user\n{text}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"


if __name__ == "__main__":
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument("--checkpoint", type=Path, default=DEFAULT)
  ap.add_argument("--metadata", type=Path, default=METADATA)
  ap.add_argument("--slots", type=int, default=8)
  ap.add_argument("--context", type=int, default=4096, help="positions per slot")
  ap.add_argument("--prompts", type=int, default=16)
  ap.add_argument("--tokens", type=int, default=64)
  ap.add_argument("--temperature", type=float, default=0.0)
  ap.add_argument("--device", type=int, default=0)
  a = ap.parse_args()
  from tokenizers import Tokenizer
  tok = Tokenizer.from_file(str(a.metadata / "tokenizer.json"))
  topics = ["a robot learning to paint", "the history of the bicycle", "why the sky is blue", "a dragon who bakes bread",
            "how compilers work", "the moon landing", "a city under the sea", "learning to play the violin"]
  prompts = [tok.encode(chat_prompt(f"Write {'a story' if i % 2 else 'a short essay'} about {topics[i % len(topics)]}. ({i})"),
                        add_special_tokens=False).ids for i in range(a.prompts)]
  dev = Device(a.device)
  try:
    t0 = time.perf_counter()
    engine = Engine(QwenBatch(dev, slots=a.slots, context=a.context, checkpoint=a.checkpoint, metadata=a.metadata))
    print(f"loaded in {time.perf_counter() - t0:.1f}s", file=sys.stderr)
    seqs = [Sequence(p, a.tokens, temperature=a.temperature, seed=i) for i, p in enumerate(prompts)]
    start = time.perf_counter()
    engine.run(seqs)
    elapsed = time.perf_counter() - start
    total = sum(len(s.out) for s in seqs)
    for i, s in enumerate(seqs[:3]): print(f"--- {i}: {tok.decode(s.out)!r}")
    print(f"{len(seqs)} sequences on {a.slots} slots: {total} tokens in {elapsed:.2f}s, {engine.steps} steps, "
          f"{total / elapsed:.1f} tok/s overall, {dict(engine.stats)}", file=sys.stderr)
  finally:
    dev.close()
