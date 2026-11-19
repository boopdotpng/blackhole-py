import argparse, json, mmap, struct, time
from collections import deque
from pathlib import Path
import numpy as np
import fw
from ops_blackhole import BlackholeDevice, BlackholeComputeQueue, BlackholeGraph, blackhole_build_program, dram
from helpers import round_up, safe_load

ROOT = Path(__file__).resolve().parent
KERNELS = ROOT / "kernels"
MODELS = {"1b": "Llama 3.2 1B", "8b-bf16": "Llama 3 8B BF16", "8b-fp8": "Llama 3 8B FP8"}
ARGS = 64  # one launch's argument block: 16 words

def mean(xs): return sum(xs) / len(xs) if xs else float("nan")

class ChatTokenizer:
  """The checkpoint's tokenizer.json as a tiktoken BPE (cached in ~/.cache/blackhole-py) and Llama 3's chat format."""
  def __init__(self, path):
    import datetime, hashlib, pickle, tiktoken
    path, raw = Path(path), (Path(path) / "tokenizer.json").read_bytes()
    if (cache := fw.CACHE / f"tokenizer-{hashlib.sha256(raw).hexdigest()[:24]}.pkl").exists(): pat, ranks, special = pickle.loads(cache.read_bytes())
    else:
      tok = json.loads(raw)
      bs = [*range(33, 127), *range(161, 173), *range(174, 256)]  # GPT-2's byte-level BPE writes bytes as these characters
      byte = {chr(b): b for b in bs} | {chr(256 + i): b for i, b in enumerate(b for b in range(256) if b not in bs)}
      ranks = {bytes(byte[c] for c in k): v for k, v in tok["model"]["vocab"].items()}
      special = {t["content"]: t["id"] for t in tok["added_tokens"]}
      pat = tok["pre_tokenizer"]["pretokenizers"][0]["pattern"]["Regex"]
      cache.parent.mkdir(parents=True, exist_ok=True)
      cache.write_bytes(pickle.dumps((pat, ranks, special)))
    self.enc = tiktoken.Encoding("llama3", pat_str=pat, mergeable_ranks=ranks, special_tokens=special)
    cfg = json.loads((path / "tokenizer_config.json").read_text())
    template = (path / "chat_template.jinja").read_text() if (path / "chat_template.jinja").exists() else cfg["chat_template"]
    # Llama 3.1+ templates open with a system header carrying today's date
    self.system = f"Cutting Knowledge Date: December 2023\nToday Date: {datetime.date.today():%d %b %Y}\n\n" if "Today Date" in template else None
    self.cleanup = cfg.get("clean_up_tokenization_spaces", False)

  def chat(self, messages) -> list[int]:
    msgs = ([{"role": "system", "content": self.system}] if self.system is not None else []) + list(messages)
    text = "<|begin_of_text|>" + "".join(f"<|start_header_id|>{m['role']}<|end_header_id|>\n\n"
      + (m["content"] if m["role"] == "system" else m["content"].strip()) + "<|eot_id|>" for m in msgs)
    return self.enc.encode(text + "<|start_header_id|>assistant<|end_header_id|>\n\n", allowed_special="all")

  def decode(self, ids) -> str:
    text = self.enc.decode(list(ids))
    if self.cleanup:  # what transformers' clean_up_tokenization does
      for a, b in ((" .", "."), (" ?", "?"), (" !", "!"), (" ,", ","), (" ' ", "'"), (" n't", "n't"), (" 'm", "'m"),
                   (" 's", "'s"), (" 've", "'ve"), (" 're", "'re")): text = text.replace(a, b)
    return text

class Llama3:
  def __init__(self, model="1b", device=0, weights=None, *, profile=False, ttrv=False):
    self.profile, self.kdir = profile, KERNELS / f"llama3-{model}"
    self.m = m = json.loads((self.kdir / "manifest.json").read_text())
    self.checkpoint = Path(weights) if weights else ROOT / m["checkpoint"]  # weights/llama3-<model> by default
    self.launches = list(m["launches"])
    self.ttrv = ttrv
    self.dev = dev = BlackholeDevice(f"BLACKHOLE:{device}")
    try:
      dev.allocator.dram_top = round_up(fw.DRAM_BANKS * m["dram_top"], 1 << 30)  # our heap goes above the old layout
      t = time.perf_counter()
      self._upload_weights(self.checkpoint)
      self.t_weights = time.perf_counter() - t
      t = time.perf_counter()
      self._install()
      self._build()
      self.t_build = time.perf_counter() - t
      self.ns_per_tick = 1e3 / fw.AICLK_MHZ  # device timestamps count AICLK cycles
    except BaseException:
      dev.close()
      raise

  def close(self): self.dev.close()

  # manifest buffers are page-interleaved over the 8 banks at a per-bank addr
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
    for dst, file, offset, size in sources:  # mmap keeps safetensors offsets unaligned; only the staging slots need alignment
      with open(file, "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm, memoryview(mm) as view:
        self.dev.allocator._copyin(dst, view[offset:offset + size])
    # KV caches start zeroed. Written from the host like the weights, so startup runs no device kernel whose image
    # would be tied to one firmware L1 layout.
    chunk = bytes(16 << 20)
    for b in zeros:
      for off in range(0, b["size"], len(chunk)):
        self.dev.allocator._copyin(self.buffer(b) + off, memoryview(chunk)[:min(len(chunk), b["size"] - off)])

  # ---- fixed execution slots, immutable descriptors and per-core parameter tables
  def _install(self):
    m, dev = self.m, self.dev
    self.prog = {}
    if self.ttrv:  # compiled here against the current fw layout; the exported binaries' layout does not matter
      self._install_ttrv()
      return
    assert m['static_base'] == fw.DATA_BASE and m['l1_param_base'] == fw.L1_PARAM_BASE, "kernels exported for another L1 layout"
    tables_end = max(m['static_base'] + 0x40 * (p['k'] + 1) for p in m['programs'].values())
    for name, p in m['programs'].items():
      assert not p["pre"], "export kernels with resident state instead of per-launch L1 writes"
      files = {role: [(self.kdir / f).read_bytes() for f in fs] for role, fs in p['files'].items()}
      images = {}
      for c in p['per_core']:
        core = tuple(c['core'])
        if c['params']:
          dev.iface.write(core, m['static_base'] + 0x40 * p['k'], struct.pack(f"<{len(c['params'])}I", *c['params']))
        images[core] = {}
        for role, v in zip(m['roles'], c['variants']):
          if v < 0: continue
          img = files[role][v]
          images[core][role] = img + fw.ret(role)  # PC-relative code: runs from either slot
      args_size = round_up(4 * len(p['uniform']), 16)
      self.prog[name] = blackhole_build_program(dev, images, args_size)
    for state in m.get('persistent', ()):
      assert tables_end <= state['addr'] and state['addr'] + state['size'] <= m['l1_data_base'], state
      dev.iface.write(tuple(state['core']), state['addr'], bytes(state['size']))

  def _install_ttrv(self):
    from ttrv import build
    m = self.m
    embed = m["buffers"]["e2e_x_a"]["size"] // 2048
    hidden = m["buffers"]["e2e_hidden_dense"]["size"] // 2048
    fp8 = int(m["model"] == "8b-fp8")
    projection = dict(EMBED_TILES=embed, FP8=fp8)
    variants = dict(embedding=dict(EMBED_TILES=embed, MAX_TOKENS=m["max_tokens"]),
                    attention=dict(HEAD_TILES=embed, MAX_TOKENS=m["max_tokens"]),
                    qkv=projection, gate=dict(projection, MLP_TILES=hidden), o=projection,
                    down=dict(projection, INPUT_TILES=hidden), lm=projection,
                    argmax=dict(FP8=fp8, MAX_TOKENS=m["max_tokens"]))
    for name in m["programs"]:
      path = ROOT / "docs" / "examples" / f"llama3_{'o' if name == 'down' else name}.ttrv"
      self.prog[name] = build(path.read_text(), variants[name], str(path)).install(self.dev)

    logits = m["buffers"]["e2e_logits"]["addr"]
    def arguments(name, w):
      # The exported graph stores stripe-aligned bank addresses and encodes
      # FP8 scales as pairs of SFPLOADI instructions (low and high halfwords).
      if name == "embedding": return w
      if name == "attention": return [*w[6:11], w[1], w[2], w[3], w[11]]
      if name == "lm": return [w[0], w[2], w[1], logits]
      if name == "argmax": return [logits, w[0], "argmax_host_address", "host_hi", "start_pos", "write_token"]
      scale = []
      if fp8:
        names = m["programs"][name]["uniform"]
        encoded = [v for k,v in zip(names, w) if k.startswith(("input_scale_", "output_scale_"))]
        bits = [(hi & 65535) << 16 | (lo & 65535) for lo, hi in zip(encoded[::2], encoded[1::2])]
        buf = self.dev.allocator.upload(struct.pack(f"<{len(bits)}I", *bits).ljust(64, b"\0"))
        scale = [(buf & ((1 << 48) - 1)) // fw.DRAM_BANKS]
      if name == "qkv": return [w[0], w[-1], w[1], w[3], w[5], *scale, w[2], w[4], w[6]]
      if name == "gate": return [w[0], w[-1], w[-2], w[1], w[2], *scale]
      return [w[0], w[1], w[-2], w[-1], *scale]
    self.launches = [(name, arguments(name, words)) for name, words in self.launches]

  # ---- arguments and graph, built once
  # One argument block per launch, in pinned host memory, which the dispatcher copies to the workers as it reaches
  # each EXEC. Buffer addresses never change and are written once here. The host never writes the blocks again:
  # each run queues STOREs of the 8-byte argument words whose integers changed (the position and values derived
  # from it) ahead of its CALL, as cuStreamWriteValue64 before cudaGraphLaunch. They land in queue order, so the host
  # queues the next run without waiting for the previous one.
  def _build(self):
    m, dev = self.m, self.dev
    self.npos = m["max_tokens"] - 1
    self.host = dev.alloc_host(16 * m["max_tokens"])  # argmax posts token pos + 1 to slot pos + 1
    noc = dev.sysmem.noc_addr + self.host
    assert noc >> 32 == 0x10000000, "argmax's PCIe mid address is compiled in"
    fixed = dict(argmax_host_address=noc & 0xFFFFFFFF, host_hi=noc >> 32)
    words, dyn = np.zeros(len(self.launches) * ARGS // 4, np.uint32), {}
    for i, (_, ws) in enumerate(self.launches):
      assert len(ws) * 4 <= ARGS
      for j, w in enumerate(ws):
        if isinstance(w, str) and w not in fixed: dyn.setdefault(w, []).append(ARGS // 4 * i + j)
        else: words[ARGS // 4 * i + j] = fixed[w] if isinstance(w, str) else w
    at = dev.alloc_host(words.nbytes)
    self.args_base = dev.sysmem.noc_addr + at
    np.ndarray(words.shape, np.uint32, dev.sysmem.mem, at)[:] = words
    self.words = words  # what the argument blocks hold once every queued STORE has landed
    self.dyn = {name: np.array(cols) for name, cols in dyn.items()}
    # one run: boundary timestamps and optional paired timestamps fused into EXEC, also in pinned host memory. Two
    # sets, used by alternate runs (graph instances 0 and 1), so one run can be in flight while the host reads the other.
    self.nts = 2 * len(self.launches) + 2 if self.profile else 2
    at = dev.alloc_host(2 * 16 * self.nts)
    self.ts_base = dev.sysmem.noc_addr + at
    self.ts = np.ndarray((2, 2 * self.nts), np.uint64, dev.sysmem.mem, at)
    self.graph = self._graph(self.prog, self.ts_base)
    self.pending, self.runs = deque(), 0  # (position, instance, timeline value) of queued runs not yet collected

  def _graph(self, programs, ts_base):
    q, patches, step = BlackholeComputeQueue(), [], 16 * self.nts
    patches.append((len(q._q) + 8, step))
    q.timestamp(ts_base)
    for i, (name, _) in enumerate(self.launches):
      if self.profile: patches.append((len(q._q) + 24, step))
      q.exec(programs[name], self.args_base + ARGS * i, ts_base + 16 * (1 + 2 * i) if self.profile else 0)
    patches.append((len(q._q) + 8, step))
    q.timestamp(ts_base + 16 * (self.nts - 1))
    return BlackholeGraph(self.dev, q, 2, patches)

  # ---- a request
  def _submit(self, pos, prompt_len):
    """Queue one position: STOREs for the argument words that change, then the graph. Returns (STORE ns, submit ns)."""
    t = time.perf_counter_ns()
    kvb = self.m["kv_block"]
    val = dict(token_pos=pos, write_pos=pos + 1, write_token=int(pos >= prompt_len - 1), start_pos=pos,
               kv_blocks=pos // kvb + 1, valid_columns=pos % kvb + 1)
    new = self.words.copy()
    for name, cols in self.dyn.items(): new[cols] = val[name]
    q = BlackholeComputeQueue()
    for pair in np.flatnonzero((new != self.words).reshape(-1, 2).any(1)):
      q.store(self.args_base + 8 * int(pair), int(new[2 * pair]) | int(new[2 * pair + 1]) << 32)
    self.words, inst = new, self.runs % 2
    stores = time.perf_counter_ns() - t
    value, submit = self.graph.submit(inst, before=q)
    self.pending.append((pos, inst, value))
    self.runs += 1
    return stores, submit

  def _collect(self, rows, timeout=10.0):
    """Wait for the oldest queued run and keep its timestamps (the run after next reuses them). Returns its position."""
    pos, inst, value = self.pending.popleft()
    self.dev.timeline_signal.wait(value, timeout)
    rows.append(self.ts[inst, 1:2 * self.nts:2].astype(np.int64))
    return pos

  def _drain(self, timeout=10.0):
    while self.pending: self.dev.timeline_signal.wait(self.pending.popleft()[2], timeout)

  def generate(self, ids, tokens=None, *, start=0, on_token=None):
    """Generate until EOS, the optional new-token limit, or the context limit. Returns (generated ids, stats).
    Positions before start reuse the KV cache of the previous request, which must have consumed the same ids there.
    on_token(id) is called as each token arrives."""
    P = len(ids)
    assert 0 < P <= self.npos, "prompt must leave room for generation"
    assert 0 <= start < P, "start must index a prompt token"
    assert tokens is None or tokens > 0, "tokens must be positive"
    n = self.npos if tokens is None else min(self.npos, P - 1 + tokens)
    hist = np.zeros(self.m["max_tokens"], "<u4")
    hist[:P] = ids
    self.dev.allocator._copyin(self.buffer(self.m["history"]), hist)
    gen, submit, bind, rows = [], 0, 0, []
    t = time.perf_counter_ns()
    p, done = start, False
    # Two runs in flight: the next position's run reads its token from history on the device, so the host queues it
    # before reading the current token. After EOS the run already queued finishes and its token is dropped.
    while not done and (p < n or self.pending):
      if p < n and len(self.pending) < 2:
        bd, sub = self._submit(p, P)
        bind, submit, p = bind + bd, submit + sub, p + 1
        continue
      q = self._collect(rows)
      if q < P - 1: continue
      token = struct.unpack_from("<I", self.dev.sysmem.mem, self.host + 16 * (q + 1))[0]
      gen.append(token)
      if on_token: on_token(token)
      done = token in self.m["eos"]
    wall, n = time.perf_counter_ns() - t, P - 1 + len(gen)
    self._drain()
    ts = np.stack(rows)  # one row of timestamps per position run by this request, in order
    tick = self.ns_per_tick
    g = ts[P - 1 - start:]  # the positions that generate a token
    stats = dict(positions=n - start, tokens=len(gen), bind_us=bind / 1e3, submit_us=submit / 1e3, wall_us=wall / 1e3,
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
    self._drain()
    if not hasattr(self, "_noop_graph"):
      noop = {name: blackhole_build_program(self.dev, {tuple(c['core']): {} for c in p['per_core']}, self.prog[name].args_size)
              for name, p in self.m['programs'].items()}
      self._noop_graph = self._graph(noop, self.ts_base)
    per = []
    for _ in range(reps):
      self._noop_graph()
      t = self.ts[0, 1:2 * self.nts:2].astype(np.int64)  # instance 0
      per.append((t[-1] - t[0]) * self.ns_per_tick / 1e3)
    return mean(per) / len(self.launches), mean(per)

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--model", choices=MODELS, default="1b", help="model for --prompt (--chat picks one in the page)")
  ap.add_argument("--device", type=int, default=0)
  ap.add_argument("--prompt", default="Write a story about a robot learning to paint.")
  ap.add_argument("--tokens", type=int, help="maximum new tokens (default: generate until EOS or context limit)")
  ap.add_argument("--weights", help="checkpoint directory (default: the one the kernels were exported with)")
  ap.add_argument("--ttrv", action="store_true", help="compile every decode kernel from TTRV source")
  ap.add_argument("--profile", action="store_true", help="record per-launch timestamps and report kernel/dispatch timings")
  ap.add_argument("--chat", action="store_true", help="serve the web chat (chat/) instead of running --prompt")
  ap.add_argument("--host", default="0.0.0.0", help="--chat: address to listen on")
  ap.add_argument("--port", type=int, default=8000, help="--chat: port to listen on")
  a = ap.parse_args()
  if a.tokens is not None and a.tokens < 1: ap.error("--tokens must be positive")
  if a.chat:
    import chat.server
    def load(key):  # the page picks the model; --weights replaces the checkpoint of --model only
      model = Llama3(key, a.device, a.weights if key == a.model else None, profile=a.profile, ttrv=a.ttrv)
      try: tok = ChatTokenizer(model.checkpoint)
      except BaseException:
        model.close()
        raise
      generate = lambda ids, start, on_token: model.generate(ids, a.tokens, start=start, on_token=on_token)[0]
      return tok, generate, model.npos, model.m["eos"], model.close
    return chat.server.serve(MODELS, load, a.host, a.port)
  t0 = time.perf_counter()
  model = Llama3(a.model, a.device, a.weights, profile=a.profile, ttrv=a.ttrv)
  try:
    m = model.m
    tok = ChatTokenizer(model.checkpoint)
    ids = tok.chat([{"role": "user", "content": a.prompt}])
    ref = json.loads((model.kdir / "reference.json").read_text()) if (model.kdir / "reference.json").exists() else None
    if ref and ref["prompt"] == a.prompt: ids = ref["prompt_ids"]  # 1B's chat template embeds today's date
    t_start = time.perf_counter() - t0
    gen, s = model.generate(ids, a.tokens)
    if a.profile: per_exec, noop_token = model.dispatch_baseline()
    row = lambda label, text: print(f"{label:<12}{text}")
    gb = model.weight_bytes / 1e9

    print(f"\n{MODELS[a.model]} on {model.dev.iface.card}, device {a.device}\n")
    row("startup", f"{t_start:.2f} s")
    row("  weights", f"{gb:.2f} GB in {model.t_weights:.2f} s ({gb / model.t_weights:.1f} GB/s)")
    row("  kernels", f"{len(m['programs'])} programs, one launch graph built in {model.t_build:.2f} s")

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
                  f"(submit {s['submit_us'] / s['positions']:.1f} us/position, binding args {s['bind_us'] / s['positions']:.1f} us/position)")

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
