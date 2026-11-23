"""Batched Nanbeige4.3-33B (and other Llama-architecture checkpoints with BFP-packed projections) for examples/engine.py.
One captured graph runs a decode step for every live sequence at once, one sequence per row of a 32-row activation
panel, so each weight read from DRAM serves all of them.

Per step:
  embedding     row r's token, from the step table (batch/embedding.ttrv)
  per layer     RMSNorm on panel tiles; QKV with row-major outputs; attention per (row, KV head), each row against
                its own slot's cache at its own position (batch/attention.ttrv); O, gate/up (fused SwiGLU), down on
                panel tiles, as the tiled prompt path (examples/prefill.py)
  readout       RMSNorm and the LM head for the panel; the host reads back the live rows' logits and samples

Slots are regions of the batched KV caches, each with room for `context` positions. A prompt is prefilled into its
slot through the single-sequence prompt graphs (examples/prefill.py) retargeted at the slot's cache. The host writes
each live row's (position, active, slot, token) into a pinned table before the step.

  python examples/nanbeige_batch.py --slots 8 --prompts 16 --tokens 64
"""
import argparse, sys, time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from helpers import rope
import fw
from ttrv import Device, hw
from examples.nanbeige import DEFAULT, load_checkpoint
from examples.prefill import DEFAULT_CHUNK, PromptChunks, summa_shapes
from ttrv.layout import ResidentCapacityError
from ttrv.parse import Error as TtrvError
from examples.engine import Engine, Sequence, common_prefix
from examples.kvstore import RunCopier

HERE = Path(__file__).resolve().parent
PANELS = 2  # activation panels of 32 rows: SUMMA projections work on 64-row blocks
ROWS = 32 * PANELS
PHASE = "nanbeige-prefill"
DRAM_RESERVE = 3 << 29   # activations, prompt buffers and tables allocated after the caches


class NanbeigeBatch:
  def __init__(self, file, dev, slots=8, context=4096, chunk=DEFAULT_CHUNK, loaded=None):
    if not 0 <= slots <= ROWS: raise ValueError(f"1 to {ROWS} slots, or 0 for as many as DRAM holds")
    self.loaded = cfg, self.eos, w, packed = loaded or load_checkpoint(file, dev)
    self.cfg = cfg
    cap = -(-context // 1024) * 1024   # whole history pages per slot
    if cap > cfg["max_position_embeddings"]: raise ValueError("context exceeds the model's")
    self.capacity = cap
    self.prefill_budget = 2 * chunk
    dim, mlp, vocab = cfg["hidden_size"], cfg["intermediate_size"], cfg["vocab_size"]
    heads, kv = cfg["num_attention_heads"], cfg["num_key_value_heads"]
    d = cfg.get("head_dim", dim // heads)
    if dim % 1024 or heads * d != dim: raise ValueError("expected hidden size = heads * head_dim, a multiple of 1024")
    workers, layers = len(dev.dev.workers), cfg["num_hidden_layers"]
    self.head_tiles = d // 32
    self.vocab = vocab
    kernels = {}
    def kernel(path, **defines):
      key = path, tuple(sorted(defines.items()))
      if key not in kernels: kernels[key] = dev.kernel(HERE / path, **defines)
      return kernels[key]
    def stride(width): return (width + 1023) // 1024 * 1024
    def matrix(width): return dev.empty(ROWS * stride(width), "bf16")

    # Per layer one K and one V buffer of `slots` regions; per slot a token history for its prompt.
    slot_elems = kv * cap * d
    per_slot = layers * 2 * 2 * slot_elems + 4 * cap
    alloc = dev.dev.allocator
    free = dev.dev.dram_banks * fw.DRAM_BANK_SIZE - alloc.top - DRAM_RESERVE
    if slots == 0: slots = min(ROWS, free // per_slot)
    if slots < 1 or slots * per_slot > free:
      raise MemoryError(f"{max(slots, 1)} slots of {cap} positions need {max(slots, 1) * per_slot / 2**30:.1f} GiB of DRAM; "
                        f"{max(free, 0) / 2**30:.1f} GiB is free after the weights. Use fewer slots or a shorter context.")
    self.dev, self.slots, self.chunk = dev, slots, chunk
    self.copier = None   # examples/kvstore.py RunCopier, made on the first save
    st = Path(file).stat()
    self.fingerprint = (f"nanbeige-batch kv-blocks v1 {Path(file).resolve()} {st.st_size} {int(st.st_mtime)} "
                        f"layers={layers} kv={kv} head_dim={d}")
    self.caches = [(dev.zeros(slots * slot_elems, "bf16"), dev.zeros(slots * slot_elems, "bf16")) for _ in range(layers)]
    self.history = dev.zeros(slots * cap, "u32")
    self.views = [[(k.page_view(2 * s * slot_elems, slot_elems), v.page_view(2 * s * slot_elems, slot_elems))
                   for k, v in self.caches] for s in range(slots)]
    self.histories = [self.history.page_view(4 * s * cap, cap) for s in range(slots)]
    self.table = dev.zeros((ROWS, 16), "u32", host=True)
    cos, sin = (dev.array(t, "bf16") for t in rope(cfg, d, cap))
    prompt_weights = {n: p for n, p in packed.items() if n != "lm_head.weight"}
    self.prompt = PromptChunks(dev, cfg, cap, w, prompt_weights, self.views[0], self.histories[0], cos, sin)
    self.prompt.phase = PHASE

    x, q, k, v, ctx = matrix(dim), matrix(heads * d), matrix(kv * d), matrix(kv * d), matrix(heads * d)
    self.vstride = vstride = stride(vocab)
    self.logits = logits = dev.empty(ROWS * vstride, "bf16")
    tiles = lambda width: dev.empty(ROWS * width, "bf16")
    xt, normt, ctxt, outt, hiddent = tiles(dim), tiles(dim), tiles(dim), tiles(dim), tiles(mlp)
    qt, kt_, vt, logitst = tiles(heads * d), tiles(kv * d), tiles(kv * d), tiles(vocab)

    def to_tiles(src, dst, width, row_stride, panels=PANELS):
      kernel("prefill/pack.ttrv", K=width, STRIDE=row_stride, BLOCK=128, PANELS=panels, TILE_ROWS=32,
             WORKERS=min(panels * width // 128, workers))(x=src, output=dst, rows=32)
    def to_rows(src, dst, width):
      block = 128 if width % 128 == 0 else 32
      kernel("prefill/unpack.ttrv", N=width, PANELS=PANELS, BLOCK=block,
             WORKERS=min(workers, PANELS * width // block))(x=src, output=dst)
    gammas = {}
    def gamma(name):  # identical rows: the norm weight as panels of tiles
      if name not in gammas:
        gammas[name] = tiles(dim)
        to_tiles(w[name], gammas[name], dim, 0)
      return gammas[name]
    def vector(op, a, b, out, width):
      kt = width // 32
      if op == 2: peers = min(16, workers // PANELS, kt); n = PANELS * peers
      else: peers, n = 1, min(workers, PANELS * kt)
      kernel("prefill/vector.ttrv", OP=op, PANELS=PANELS, KT=kt, PEERS=peers, WORKERS=n, EPS=cfg["rms_norm_eps"])(
        x=a, other=b, output=out)
    def tiled(name, src, dst, swiglu=False, **outs):  # panel tiles in and out, 64x64 output blocks (SUMMA)
      buf, k_, n, bits, group, second, third, pad = packed[name]
      epilogue = dict(SWIGLU=1) if swiglu else dict(SECOND=second, THIRD=third)
      for shape in summa_shapes(k_, n, bits, group, PANELS, swiglu, hw.L1_SIZE - dev.top):
        try:
          project = kernel("prefill/summa_projection.ttrv", K=k_, N=n, BITS=bits, GROUP=group, PAD=pad, PANELS=PANELS,
                           **epilogue, **shape)
          break
        except (ResidentCapacityError, TtrvError) as e:
          if isinstance(e, TtrvError) and e.id != "storage.overflow": raise
      else: raise ResidentCapacityError(f"no SUMMA shape fits for {name}")
      project(x=src, weights=buf, output=dst, **outs)

    embed = kernel("batch/embedding.ttrv", ROWS=ROWS, EMBED_TILES=dim // 1024)
    # Split each row's cache over as many partitions as the grid holds for all slots at once (flash decoding).
    parts = next(p for p in (8, 4, 2, 1) if slots * kv * p <= workers or p == 1)
    group_rows = min(slots, workers // (kv * parts))
    attend = kernel("batch/attention.ttrv", HEAD_TILES=d // 32, KV_HEADS=kv, GROUP=heads // kv, ROWS=group_rows,
                    PARTITIONS=parts, MAX_TOKENS=cap)
    self.copy = kernel("batch/admit.ttrv", HEAD_TILES=d // 32, KV_HEADS=kv, MAX_TOKENS=cap)
    for i in range(layers):
      for norm in ("input_layernorm", "post_attention_layernorm"): gamma(f"model.layers.{i}.{norm}.weight")
    gamma("model.norm.weight")
    dev.synchronize()

    with dev.graph() as self.step_graph:
      embed(weights=w["model.embed_tokens.weight"], output=x, table=self.table)
      to_tiles(x, xt, dim, stride(dim))
      for i, (keys, values) in enumerate(self.caches):
        layer = f"model.layers.{i}."
        vector(2, xt, gamma(layer + "input_layernorm.weight"), normt, dim)
        tiled(layer + "self_attn.q_proj.weight", normt, qt, output2=kt_, output3=vt)
        to_rows(qt, q, heads * d)
        to_rows(kt_, k, kv * d)
        to_rows(vt, v, kv * d)
        for base in range(0, slots, group_rows):
          attend(q_in=q, k_in=k, v_in=v, cos=cos, sin=sin, key_cache=keys, value_cache=values, context=ctx,
                 table=self.table, row_base=base)
        to_tiles(ctx, ctxt, heads * d, stride(heads * d))
        tiled(layer + "self_attn.o_proj.weight", ctxt, outt)
        vector(0, outt, xt, xt, dim)
        vector(2, xt, gamma(layer + "post_attention_layernorm.weight"), normt, dim)
        tiled(layer + "mlp.gate_proj.weight", normt, hiddent, swiglu=True)
        tiled(layer + "mlp.down_proj.weight", hiddent, outt)
        vector(0, outt, xt, xt, dim)
      vector(2, xt, gamma("model.norm.weight"), normt, dim)
      tiled("lm_head.weight", normt, logitst)
      to_rows(logitst, logits, vocab)

  def warm(self):
    """Capture every prompt chunk shape for every slot (a cold capture costs ~0.4 s on the first request)."""
    for slot in range(self.slots):
      for rows in (64, 320):
        self.prefill(slot, np.zeros(rows + 1, np.int64), 0, rows)
    self.dev.synchronize()

  # ---- backend interface (examples/engine.py)
  def reusable(self, slot, ids, held): return common_prefix(held, ids)

  def copy_prefix(self, src, dst, n):
    for keys, values in self.caches:
      self.copy(keys=keys, values=values, src_slot=src, dst_slot=dst, blocks=-(-n // 32))
    self.dev.synchronize()
    return True

  def _runs(self, slot, n):
    """(DRAM address, bytes) of the cache tiles holding positions 0 .. n - 1 of slot: one run per layer, K/V and KV
    head, each whole 32-position blocks of head_dim / 32 tiles."""
    kv, tiles = self.cfg["num_key_value_heads"], self.head_tiles
    per_head = self.capacity // 32 * tiles * 2048
    size = -(-n // 32) * tiles * 2048
    return [(buf.addr + slot * kv * per_head + h * per_head, size)
            for pair in self.caches for buf in pair for h in range(kv)]

  def save(self, slot, n):
    if self.copier is None: self.copier = RunCopier(self.dev)
    return self.copier.gather(self._runs(slot, n))

  def load(self, slot, data, n, m):
    if self.copier is None: self.copier = RunCopier(self.dev)
    # data holds n positions per run; take the first m of each
    stored, wanted = self._runs(slot, n)[0][1], self._runs(slot, m)[0][1]
    runs = self._runs(slot, m)
    if stored != wanted: data = np.ascontiguousarray(data.reshape(len(runs), stored)[:, :wanted]).reshape(-1)
    self.copier.scatter(runs, data)

  def prefill(self, slot, ids, start, end):
    history = np.zeros(self.capacity, np.uint32)
    history[:len(ids)] = ids
    self.histories[slot].copy_from(history)
    with self.dev.phase(PHASE):
      self.prompt.retarget(self.views[slot], self.histories[slot])
      self.prompt.run(end, self.chunk, start=start, pad_to=self.capacity)
    return end - start

  def decode(self, rows):
    table = self.table.numpy()
    table[:] = 0
    for row, (slot, pos, token) in enumerate(rows):
      table[row, :4] = pos, 1, slot, token
    self.step_graph().wait(60)
    logits = self.logits.page_view(0, len(rows) * self.vstride).numpy().reshape(len(rows), self.vstride)
    return (logits[:, :self.vocab].astype(np.uint32) << 16).view(np.float32)


def chat_prompt(text):
  return f"<|im_start|>user\n{text}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"


if __name__ == "__main__":
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument("--checkpoint", type=Path, default=DEFAULT)
  ap.add_argument("--slots", type=int, default=8)
  ap.add_argument("--context", type=int, default=4096, help="positions per slot")
  ap.add_argument("--prompts", type=int, default=16)
  ap.add_argument("--tokens", type=int, default=64)
  ap.add_argument("--temperature", type=float, default=0.0)
  ap.add_argument("--device", type=int, default=0)
  a = ap.parse_args()
  from tokenizers import Tokenizer
  tok = Tokenizer.from_file(str(a.checkpoint.parent / "tokenizer.json"))
  topics = ["a robot learning to paint", "the history of the bicycle", "why the sky is blue", "a dragon who bakes bread",
            "how compilers work", "the moon landing", "a city under the sea", "learning to play the violin"]
  prompts = [tok.encode(chat_prompt(f"Write {'a story' if i % 2 else 'a short essay'} about {topics[i % len(topics)]}. ({i})"),
                        add_special_tokens=False).ids for i in range(a.prompts)]
  dev = Device(a.device)
  try:
    t0 = time.perf_counter()
    engine = Engine(NanbeigeBatch(a.checkpoint, dev, slots=a.slots, context=a.context))
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
