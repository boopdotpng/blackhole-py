import argparse, collections, json, struct, time
from pathlib import Path
import numpy as np
import fw
from cq import ComputeQueue, HWQueue, dram, rects
from device import Device
from helpers import round_up, safe_load

ROOT = Path(__file__).resolve().parent
KERNELS = ROOT / "kernels"
MODELS = {"1b": "Llama 3.2 1B", "8b-bf16": "Llama 3 8B BF16", "8b-fp8": "Llama 3 8B FP8"}
ARGS = 64  # up to 16 dynamic words per launch

def mean(xs): return sum(xs) / len(xs) if xs else float("nan")

class ChatTokenizer:
  """The checkpoint's tokenizer.json and chat template, read with tokenizers and jinja2 rather than transformers,
  whose import and AutoTokenizer load cost ~1.8 s of startup. Same ids and text as transformers for this model."""
  def __init__(self, path):
    import datetime, tokenizers
    from jinja2.sandbox import ImmutableSandboxedEnvironment
    path = Path(path)
    cfg = json.loads((path / "tokenizer_config.json").read_text())
    self.tok = tokenizers.Tokenizer.from_file(str(path / "tokenizer.json"))
    self.tok.no_padding(); self.tok.no_truncation()  # 8B FP8's tokenizer.json pads to 512; transformers ignores that
    special = {k: v if isinstance(v, str) else v["content"] for k, v in cfg.items() if k.endswith("_token") and isinstance(v, (str, dict))}
    jinja = path / "chat_template.jinja"
    env = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True, extensions=["jinja2.ext.loopcontrols"])
    def raise_exception(msg): raise ValueError(msg)
    env.globals.update(raise_exception=raise_exception, strftime_now=lambda fmt: datetime.datetime.now().strftime(fmt))
    self.template = env.from_string(jinja.read_text() if jinja.exists() else cfg["chat_template"])
    self.special, self.cleanup = special, cfg.get("clean_up_tokenization_spaces", False)

  def chat(self, messages) -> list[int]:
    text = self.template.render(messages=messages, add_generation_prompt=True, **self.special)
    return self.tok.encode(text, add_special_tokens=False).ids

  def decode(self, ids) -> str:
    text = self.tok.decode(list(ids), skip_special_tokens=False)
    if self.cleanup:  # what transformers' clean_up_tokenization does
      for a, b in ((" .", "."), (" ?", "?"), (" !", "!"), (" ,", ","), (" ' ", "'"), (" n't", "n't"), (" 'm", "'m"),
                   (" 's", "'s"), (" 've", "'ve"), (" 're", "'re")): text = text.replace(a, b)
    return text

class Llama3:
  def __init__(self, model="1b", device=0, weights=None, *, profile=False):
    self.profile, self.kdir = profile, KERNELS / f"llama3-{model}"
    self.m = m = json.loads((self.kdir / "manifest.json").read_text())
    self.checkpoint = Path(weights) if weights else ROOT / m["checkpoint"]  # weights/llama3-<model> by default
    self.launches = m["launches"]
    self.dev = dev = Device(device)
    try:
      dev.dram_top = round_up(fw.DRAM_BANKS * m["dram_top"], 1 << 30)  # our heap goes above the old layout
      t = time.perf_counter()
      self._upload_weights(self.checkpoint)
      self.t_weights = time.perf_counter() - t
      t = time.perf_counter()
      self._install()
      self._build()
      self.t_build = time.perf_counter() - t
      self.ns_per_tick = 1e3 / fw.AICLK_MHZ  # device timestamps count AICLK cycles
      self.startup_ops = self._ring_ops()
    except BaseException:
      dev.close()
      raise

  def close(self): self.dev.close()

  # ---- DRAM: blackhole-py's buffers are page-interleaved over the 8 banks at a page-aligned per-bank addr, which is
  # this runtime's dram(8 * addr, page): the DMA engine does the interleaving.
  def buffer(self, b) -> int: return dram(fw.DRAM_BANKS * b["addr"], b["tile"])

  def _upload_weights(self, checkpoint):
    path = Path(checkpoint)
    if path.is_dir(): path = next(f for f in (path / "model.safetensors.index.json", path / "model.safetensors") if f.exists())
    tensors = safe_load(path)
    sources, zeros, self.weight_bytes = [], [], 0
    for b in self.m["uploads"]:
      if b["kind"] == "tensor":
        t = tensors[b["src"]]
        assert t.nbytes <= b["size"], (b["name"], t.nbytes, b["size"])
        sources.append((self.buffer(b), t.path, t.offset, t.nbytes))
      elif b["kind"] == "file": sources.append((self.buffer(b), self.kdir / b["src"], 0, (self.kdir / b["src"]).stat().st_size))
      else: zeros.append(b)  # KV caches start zeroed
      self.weight_bytes += b["size"]
    self.dev.load(sources)
    for b in zeros: self.dev.zero(self.buffer(b), b["size"])

  # ---- fixed execution slots, immutable descriptors and per-core parameter tables
  def _install(self):
    m, dev = self.m, self.dev
    self.prog, self.noop = {}, {}
    tables_end = max(m['static_base'] + 0x40 * (p['k'] + 1) for p in m['programs'].values())
    for name, p in m['programs'].items():
      files = {role: [(self.kdir / f).read_bytes() for f in fs] for role, fs in p['files'].items()}
      images = {}
      for c in p['per_core']:
        core = tuple(c['core'])
        if c['params']:
          dev.pci_dev.write(core, m['static_base'] + 0x40 * p['k'], struct.pack(f"<{len(c['params'])}I", *c['params']))
        images[core] = {}
        for role, v in zip(m['roles'], c['variants']):
          if v < 0: continue
          img = files[role][v]
          images[core][role] = img + fw.ret(role)  # PC-relative code: runs from either slot
      args_size = round_up(4 * len(p['uniform']), 16)
      self.prog[name] = dev.bind(images, args_size)
      self.noop[name] = dev.bind({c: {} for c in images}, args_size)
    for state in m.get('persistent', ()):
      assert tables_end <= state['addr'] and state['addr'] + state['size'] <= 0x9000, state
      dev.pci_dev.write(tuple(state['core']), state['addr'], bytes(state['size']))
    self.code_slot_bytes = 2 * sum(fw.CODE_SIZE.values())  # double buffered

  # ---- per-position args and graphs
  def _build(self):
    m, dev = self.m, self.dev
    self.npos = m["max_tokens"] - 1
    self.host = dev.alloc(16 * m["max_tokens"])  # argmax posts token pos + 1 to slot pos + 1
    noc = dev.sysmem.noc_addr + self.host
    assert noc >> 32 == 0x10000000, "argmax's PCIe mid address is compiled in"
    self.host_lo = noc & 0xFFFFFFFF
    # args template for one position; dyn = (word offset, name) of the per-position words
    tpl, self.dyn = bytearray(), []
    for i, (name, words) in enumerate(self.launches):
      p = m["programs"][name]
      assert len(words) * 4 <= ARGS
      tpl += bytes(ARGS)
      for j, w in enumerate(words):
        at = ARGS * i + 4 * j
        if isinstance(w, str): self.dyn.append((at // 4, w))
        else: struct.pack_into("<I", tpl, at, w)
    self.args_tpl = np.frombuffer(bytes(tpl), np.uint32)
    self.args_stride = len(tpl)
    self.args_base = dram(dev.alloc_dram(self.npos * self.args_stride), fw.DRAM_PAGE_MAX)
    # one position: boundary timestamps and optional paired timestamps fused into EXEC
    self.nts = 2 * len(self.launches) + 2 if self.profile else 2
    self.ts_stride = round_up(16 * self.nts, 64)
    self.ts_base = dram(dev.alloc_dram(self.npos * self.ts_stride), fw.DRAM_PAGE_MAX)
    self.graph_base, self.graph_size, self.graph_stride = self._graphs(self.prog, self.ts_base, self.npos, stores=True)

  def _graphs(self, prog, ts_base, npos, stores):
    """Upload npos graphs, graph p using position p's args and timestamp slots. Returns (base, size, stride)."""
    m, q = self.m, ComputeQueue()
    stamp = lambda j: q.timestamp(ts_base + 16 * j)
    stamp(0)
    for i, (name, words) in enumerate(self.launches):
      p = m["programs"][name]
      for w in p["pre"] if stores else ():  # the CQ has no bulk L1 write
        data = bytes.fromhex(w["data"])
        for o in range(0, len(data), 8): q.signal(fw.noc(w["core"]) << 32 | w["addr"] + o, int.from_bytes(data[o:o + 8], "little"))
      q.exec(prog[name], self.args_base + ARGS * i, ts_base + 16 * (1 + 2 * i) if self.profile else 0)
    stamp(self.nts - 1)
    tpl = np.frombuffer(bytes(q.blob), np.uint64).reshape(-1, 4)
    op = tpl[:, 0] & np.uint64(0xFFFFFFFF)
    if stores: self.graph_ops = collections.Counter(fw.Op(int(o)).name for o in op)
    rows = np.tile(tpl, (npos, 1, 1))
    pos = np.arange(npos, dtype=np.uint64)[:, None]
    rows[:, op == fw.Op.EXEC, 2] += pos * np.uint64(self.args_stride)       # b = this position's args
    rows[:, op == fw.Op.TIMESTAMP, 1] += pos * np.uint64(self.ts_stride)    # a = this position's timestamp slots
    if self.profile: rows[:, op == fw.Op.EXEC, 3] += pos * np.uint64(self.ts_stride)
    size, stride = len(q.blob), round_up(len(q.blob), 64)                   # CALL fetches need 64-byte alignment
    g = np.zeros((npos, stride), np.uint8)
    g[:, :size] = rows.reshape(npos, -1).view(np.uint8)
    base = dram(self.dev.alloc_dram(npos * stride), fw.DRAM_PAGE_MAX)
    self.dev.copyin(base, g)
    return base, size, stride

  # ---- a request
  def _upload_args(self, n, prompt_len):
    pos = np.arange(n, dtype=np.uint32)
    kvb = self.m["kv_block"]
    val = dict(token_pos=pos, write_pos=pos + 1, write_token=(pos >= prompt_len - 1).astype(np.uint32), start_pos=pos,
               kv_blocks=pos // kvb + 1, valid_columns=pos % kvb + 1, argmax_host_address=np.full(n, self.host_lo, np.uint32))
    a = np.tile(self.args_tpl, (n, 1))
    for col, name in self.dyn: a[:, col] = val[name]
    self.dev.copyin(self.args_base, a.view(np.uint8))

  def _run(self, base, size, stride, n):
    """Push n position graphs back to back and wait once; returns (host submit ns, wall ns)."""
    dev, ring = self.dev, self.dev.compute
    self.done = getattr(self, "done", 0)
    t0, submit = time.perf_counter_ns(), 0
    for p in range(n):
      s = time.perf_counter_ns()
      ring.call(base + p * stride, size)
      if p == n - 1:
        self.done += 1
        HWQueue().signal(dev.signal(252), self.done).submit(ring)
      submit += time.perf_counter_ns() - s
    dev.wait(252, self.done, timeout=60.0)
    return submit, time.perf_counter_ns() - t0

  def _timestamps(self, base, n):
    raw = bytearray(n * self.ts_stride)
    self.dev.copyout(raw, base)
    return np.frombuffer(bytes(raw), np.uint64).reshape(n, -1)[:, 1:2 * self.nts:2].astype(np.int64)

  def _ring_ops(self): return {"compute": self.dev.compute.ops.copy(), "copy": self.dev.copy.ops.copy()}

  def generate(self, ids, tokens=None, *, start=0, on_token=None):
    """Generate until EOS, the optional new-token limit, or the context limit. Returns (generated ids, stats).
    Positions before start reuse the KV cache of the previous request, which must have consumed the same ids there.
    on_token(id) is called as each token arrives."""
    P = len(ids)
    assert 0 < P <= self.npos, "prompt must leave room for generation"
    assert 0 <= start < P, "start must index a prompt token"
    assert tokens is None or tokens > 0, "tokens must be positive"
    n = self.npos if tokens is None else min(self.npos, P - 1 + tokens)
    ops0 = self._ring_ops()
    hist = np.zeros(self.m["max_tokens"], "<u4")
    hist[:P] = ids
    self.dev.copyin(self.buffer(self.m["history"]), hist)
    self.dev.sysmem.mem[self.host:self.host + 16 * (n + 1)] = bytes(16 * (n + 1))
    t = time.perf_counter_ns()
    self._upload_args(n, P)
    t_args = time.perf_counter_ns() - t
    gen, submit = [], 0
    t = time.perf_counter_ns()
    for p in range(P - 1, n):
      # Batch the uncached prompt; thereafter wait for each token before submitting the next position.
      first = start if p == P - 1 else p
      elapsed, _ = self._run(self.graph_base + first * self.graph_stride, self.graph_size, self.graph_stride, p + 1 - first)
      submit += elapsed
      token = struct.unpack_from("<I", self.dev.sysmem.mem, self.host + 16 * (p + 1))[0]
      gen.append(token)
      if on_token: on_token(token)
      if token in self.m["eos"]: break
    wall, n = time.perf_counter_ns() - t, P - 1 + len(gen)
    request_ops = {q: c - ops0[q] for q, c in self._ring_ops().items()}  # timestamp readback below not included
    ts = self._timestamps(self.ts_base, n)[start:]  # the positions run by this request
    tick = self.ns_per_tick
    g = ts[P - 1 - start:]  # the positions that generate a token
    stats = dict(ops=request_ops, positions=n - start, tokens=len(gen), args_upload_us=t_args / 1e3, submit_us=submit / 1e3, wall_us=wall / 1e3,
                 period_us=(g[-1, -1] - g[0, 0]) * tick / 1e3 / len(g),            # start of first to end of last
                 busy_us=mean((g[:, -1] - g[:, 0]).tolist()) * tick / 1e3,         # inside one position's graph
                 gap_us=mean((g[1:, 0] - g[:-1, -1]).tolist()) * tick / 1e3 if len(g) > 1 else 0.0,
                 device_us=(ts[-1, -1] - ts[0, 0]) * tick / 1e3)  # every position, prompt included
    stats["kernels"] = {}
    if self.profile:
      d = (g[:, 2:-1:2] - g[:, 1:-1:2]) * tick / 1e3  # paired EXEC timestamps, excluding prior dependencies
      stats["kernels"] = {name: d[:, [i for i, (nm, _) in enumerate(self.launches) if nm == name]].ravel()
                          for name in dict.fromkeys(nm for nm, _ in self.launches)}
    return gen, stats

  def dispatch_baseline(self, reps=20):
    """us per EXEC for the same launch list with no-op kernels (no STOREs): the cost of dispatch alone."""
    self._upload_args(1, 1)
    if not hasattr(self, "_noop_graph"):
      ts = dram(self.dev.alloc_dram(self.ts_stride), fw.DRAM_PAGE_MAX)
      self._noop_graph = (*self._graphs(self.noop, ts, 1, stores=False), ts)
    base, size, stride, ts = self._noop_graph
    per = []
    for _ in range(reps):
      self._run(base, size, stride, 1)
      t = self._timestamps(ts, 1)[0]
      per.append((t[-1] - t[0]) * self.ns_per_tick / 1e3)
    return mean(per) / len(self.launches), mean(per)

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--model", choices=MODELS, default="1b")
  ap.add_argument("--device", type=int, default=0)
  ap.add_argument("--prompt", default="Write a story about a robot learning to paint.")
  ap.add_argument("--tokens", type=int, help="maximum new tokens (default: generate until EOS or context limit)")
  ap.add_argument("--weights", help="checkpoint directory (default: the one the kernels were exported with)")
  ap.add_argument("--profile", action="store_true", help="record per-launch timestamps and report kernel/dispatch timings")
  ap.add_argument("--chat", action="store_true", help="serve the web chat (chat/) instead of running --prompt")
  ap.add_argument("--host", default="0.0.0.0", help="--chat: address to listen on")
  ap.add_argument("--port", type=int, default=8000, help="--chat: port to listen on")
  a = ap.parse_args()
  if a.tokens is not None and a.tokens < 1: ap.error("--tokens must be positive")
  t0 = time.perf_counter()
  model = Llama3(a.model, a.device, a.weights, profile=a.profile)
  try:
    m = model.m
    tok = ChatTokenizer(model.checkpoint)
    if a.chat:
      import chat.server
      generate = lambda ids, start, on_token: model.generate(ids, a.tokens, start=start, on_token=on_token)[0]
      return chat.server.serve(MODELS[a.model], tok, generate, model.npos, m["eos"], a.host, a.port)
    ids = tok.chat([{"role": "user", "content": a.prompt}])
    ref = json.loads((model.kdir / "reference.json").read_text()) if (model.kdir / "reference.json").exists() else None
    if ref and ref["prompt"] == a.prompt: ids = ref["prompt_ids"]  # 1B's chat template embeds today's date
    t_start = time.perf_counter() - t0
    gen, s = model.generate(ids, a.tokens)
    if a.profile: per_exec, noop_token = model.dispatch_baseline()
    row = lambda label, text: print(f"{label:<12}{text}")
    gb = model.weight_bytes / 1e9

    print(f"\n{MODELS[a.model]} on {model.dev.pci_dev.card}, device {a.device}\n")
    row("startup", f"{t_start:.2f} s")
    row("  weights", f"{gb:.2f} GB in {model.t_weights:.2f} s ({gb / model.t_weights:.1f} GB/s)")
    row("  kernels", f"{len(m['programs'])} programs, {model.code_slot_bytes / 1024:.1f} KB of double-buffered code slots per core, "
                     f"{model.npos} position graphs built in {model.t_build:.2f} s")

    eos = next((i for i, t in enumerate(gen) if t in m["eos"]), len(gen))
    print()
    row("prompt", f"{a.prompt!r} ({len(ids)} tokens with the chat template)")
    row("output", tok.decode(gen[:eos]).strip())
    if eos < len(gen): row("", "(stopped at EOS; timing includes the EOS token)")
    elif s["positions"] == model.npos: row("", "(stopped at context limit)")
    else: row("", "(stopped at token limit)")
    if ref and ref["prompt_ids"] == ids:
      want = ref["generated_ids"]
      n = min(len(gen), len(want))
      same = next((i for i, (x, y) in enumerate(zip(gen, want)) if x != y), n)
      row("reference", f"{same}/{n} tokens match blackhole-py ({'OK' if same == n else 'MISMATCH'}; "
                       f"it runs {1e6 / ref['mean_wall_us']:.1f} tok/s)")

    print()
    row("decode", f"{1e6 / s['period_us']:.1f} tok/s, {s['period_us'] / 1e3:.3f} ms/token "
                  f"({s['tokens']} tokens, device clock, {model.nts} timestamps per token)")
    row("  device", f"{s['busy_us']:.1f} us per token in the graph, {s['gap_us']:.2f} us between graphs")
    row("  host", f"{(s['wall_us'] - s['device_us']) / s['positions']:.1f} us per position on top of the device "
                  f"(submit {s['submit_us'] / s['positions']:.1f} us/position, args upload {s['args_upload_us']:.0f} us once)")

    fmt = lambda c: ", ".join(f"{k} {v}" for k, v in c.most_common()) + f"  ({sum(c.values())})" if c else "-"
    print(f"\n{'commands':<16}{'startup':<36}per request ({s['positions']} positions)")
    for q in ("compute", "copy"):
      print(f"{q + ' ring':<16}{fmt(model.startup_ops[q]):<36}{fmt(s['ops'][q])}")
    print(f"{'graph (DRAM)':<16}{'':<36}{fmt(model.graph_ops)} per position, run by the CQ from DRAM")

    if not a.profile:
      print("\nUse --profile for per-kernel and dispatch timings.")
      return
    ks, tokens = s["kernels"], s["tokens"]
    tot = sum(v.sum() for v in ks.values()) / tokens
    print(f"\n{'kernel':<12}{'launches':>9}{'us/launch':>11}{'min':>9}{'max':>9}{'us/token':>11}{'share':>8}")
    for name, v in sorted(ks.items(), key=lambda kv: -kv[1].sum()):
      per_tok = v.sum() / tokens
      print(f"{name:<12}{len(v) // tokens:>9}{v.mean():>11.1f}{v.min():>9.1f}{v.max():>9.1f}{per_tok:>11.1f}{per_tok / tot:>8.1%}")
    print(f"{'total':<12}{sum(len(v) for v in ks.values()) // tokens:>9}{'':>29}{tot:>11.1f}")
    print(f"{'dispatch':<12}{len(model.launches):>9}{per_exec:>11.1f}{'':>18}{noop_token:>11.1f}{noop_token / tot:>8.1%}"
          f"   no-op kernels: already inside each row above")
  finally:
    model.close()

if __name__ == "__main__": main()
