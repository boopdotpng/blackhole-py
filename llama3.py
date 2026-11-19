import argparse, json, mmap, struct, time
from collections import deque
from pathlib import Path
import numpy as np
import fw
from ops_blackhole import BlackholeDevice, BlackholeComputeQueue, BlackholeGraph, dram
from helpers import round_up, safe_load
from ttrv import build

ROOT = Path(__file__).resolve().parent
KERNELS, MODELS_DIR = ROOT / "kernels", ROOT / "models"
MODELS = {"1b": "Llama 3.2 1B", "8b-bf16": "Llama 3 8B BF16", "8b-fp8": "Llama 3 8B FP8"}
ARGS = 64  # one launch's argument block: 16 words
POS = ("pos", "write_token")  # integer arguments that change every run

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
  def __init__(self, model="1b", device=0, weights=None):
    self.dir = MODELS_DIR / f"llama3-{model}"
    self.m = m = json.loads((self.dir / "model.json").read_text())
    self.checkpoint = Path(weights) if weights else ROOT / m["checkpoint"]  # weights/llama3-<model> by default
    self.dev = dev = BlackholeDevice(f"BLACKHOLE:{device}")
    try:
      dev.allocator.dram_top = round_up(fw.DRAM_BANKS * m["dram_top"], 1 << 30)  # our heap goes above the model's buffers
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

  # model buffers are page-interleaved over the 8 banks at a per-bank addr
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
      elif b["kind"] == "file": sources.append((self.buffer(b), self.dir / b["src"], 0, (self.dir / b["src"]).stat().st_size))
      else: zeros.append(b)  # KV caches start zeroed
      self.weight_bytes += b["size"]
    for dst, file, offset, size in sources:  # mmap keeps safetensors offsets unaligned; only the staging slots need alignment
      with open(file, "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm, memoryview(mm) as view:
        self.dev.allocator._copyin(dst, view[offset:offset + size])
    chunk = bytes(16 << 20)
    for b in zeros:
      for off in range(0, b["size"], len(chunk)):
        self.dev.allocator._copyin(self.buffer(b) + off, memoryview(chunk)[:min(len(chunk), b["size"] - off)])

  # ---- kernels, compiled from kernels/*.ttrv against the current firmware layout
  def _install(self):
    self.prog = {}
    for name, k in self.m["kernels"].items():
      path = KERNELS / k["src"]
      self.prog[name] = build(path.read_text(), k["defines"], str(path)).install(self.dev)

  def _words(self, name, args, tokens):
    """One launch's argument words: each parameter at its slot. DRAM buffers are per-bank addresses, a list is FP32
    data (FP8 scales) uploaded here, the host buffer is the token slots, and integers in POS are bound per run."""
    words = [0] * (ARGS // 4)
    for k, d in self.prog[name].manifest["params"].items():
      v, at = args[k], d["slot"]
      if d["kind"] == "host": words[at:at + 2] = [tokens & 0xFFFFFFFF, tokens >> 32]
      elif isinstance(v, list):
        buf = self.dev.allocator.upload(struct.pack(f"<{len(v)}I", *v).ljust(64, b"\0")) & ((1 << 48) - 1)
        assert buf % (fw.DRAM_BANKS * 64) == 0
        words[at] = buf // fw.DRAM_BANKS
      elif v not in POS: words[at] = v
    return words

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
    tokens = dev.sysmem.noc_addr + self.host
    self.launches = [name for name, _ in m["launches"]]
    words = np.array([w for name, args in m["launches"] for w in self._words(name, args, tokens)], np.uint32)
    self.dyn = {v: np.array([ARGS // 4 * i + self.prog[name].manifest["params"][k]["slot"]
                             for i, (name, args) in enumerate(m["launches"]) for k, a in args.items() if a == v]) for v in POS}
    at = dev.alloc_host(words.nbytes)
    self.args_base = dev.sysmem.noc_addr + at
    np.ndarray(words.shape, np.uint32, dev.sysmem.mem, at)[:] = words
    self.words = words  # what the argument blocks hold once every queued STORE has landed
    # Start and end timestamps of a run, in pinned host memory. Two sets, used by alternate runs (graph instances 0
    # and 1), so one run can be in flight while the host reads the other.
    at = dev.alloc_host(2 * 32)
    self.ts = np.ndarray((2, 4), np.uint64, dev.sysmem.mem, at)
    q = BlackholeComputeQueue()
    patches = [(len(q._q) + 8, 32)]
    q.timestamp(dev.sysmem.noc_addr + at)
    for i, name in enumerate(self.launches): q.exec(self.prog[name], self.args_base + ARGS * i, 0)
    patches.append((len(q._q) + 8, 32))
    q.timestamp(dev.sysmem.noc_addr + at + 16)
    self.graph = BlackholeGraph(dev, q, 2, patches)
    self.pending, self.runs = deque(), 0  # (position, instance, timeline value) of queued runs not yet collected

  # ---- a request
  def _submit(self, pos, prompt_len):
    """Queue one position: STOREs for the argument words that change, then the graph."""
    new = self.words.copy()
    new[self.dyn["pos"]], new[self.dyn["write_token"]] = pos, int(pos >= prompt_len - 1)
    q = BlackholeComputeQueue()
    for pair in np.flatnonzero((new != self.words).reshape(-1, 2).any(1)):
      q.store(self.args_base + 8 * int(pair), int(new[2 * pair]) | int(new[2 * pair + 1]) << 32)
    self.words, inst = new, self.runs % 2
    value, _ = self.graph.submit(inst, before=q)
    self.pending.append((pos, inst, value))
    self.runs += 1

  def _collect(self, rows, timeout=10.0):
    """Wait for the oldest queued run and keep its timestamps (the run after next reuses them). Returns its position."""
    pos, inst, value = self.pending.popleft()
    self.dev.timeline_signal.wait(value, timeout)
    rows.append(self.ts[inst, 1::2].astype(np.int64))
    return pos

  def generate(self, ids, tokens=None):
    """Generate until EOS, the optional new-token limit, or the context limit. Returns (generated ids, stats)."""
    P = len(ids)
    assert 0 < P <= self.npos, "prompt must leave room for generation"
    assert tokens is None or tokens > 0, "tokens must be positive"
    n = self.npos if tokens is None else min(self.npos, P - 1 + tokens)
    hist = np.zeros(self.m["max_tokens"], "<u4")
    hist[:P] = ids
    self.dev.allocator._copyin(self.buffer(self.m["history"]), hist)
    gen, rows, p, done = [], [], 0, False
    # Two runs in flight: the next position's run reads its token from history on the device, so the host queues it
    # before reading the current token. After EOS the run already queued finishes and its token is dropped.
    while not done and (p < n or self.pending):
      if p < n and len(self.pending) < 2:
        self._submit(p, P)
        p += 1
        continue
      q = self._collect(rows)
      if q < P - 1: continue
      token = struct.unpack_from("<I", self.dev.sysmem.mem, self.host + 16 * (q + 1))[0]
      gen.append(token)
      done = token in self.m["eos"]
    while self.pending: self._collect(rows)
    g = np.stack(rows)[P - 1:P - 1 + len(gen)] * self.ns_per_tick / 1e3  # [start, end] us of the runs that made tokens
    stats = dict(period_us=(g[-1, 1] - g[0, 0]) / len(g), busy_us=mean((g[:, 1] - g[:, 0]).tolist()),
                 gap_us=mean((g[1:, 0] - g[:-1, 1]).tolist()) if len(g) > 1 else 0.0)
    return gen, stats

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--model", choices=MODELS, default="1b")
  ap.add_argument("--device", type=int, default=0)
  ap.add_argument("--prompt", default="Write a story about a robot learning to paint.")
  ap.add_argument("--tokens", type=int, help="maximum new tokens (default: generate until EOS or context limit)")
  ap.add_argument("--weights", help="checkpoint directory (default: weights/llama3-<model>)")
  a = ap.parse_args()
  if a.tokens is not None and a.tokens < 1: ap.error("--tokens must be positive")
  t0 = time.perf_counter()
  model = Llama3(a.model, a.device, a.weights)
  try:
    m = model.m
    tok = ChatTokenizer(model.checkpoint)
    ids = tok.chat([{"role": "user", "content": a.prompt}])
    ref = json.loads((model.dir / "reference.json").read_text())
    if ref["prompt"] == a.prompt: ids = ref["prompt_ids"]  # 1B's chat template embeds today's date
    t_start = time.perf_counter() - t0
    gen, s = model.generate(ids, a.tokens)
    row = lambda label, text: print(f"{label:<12}{text}")
    gb = model.weight_bytes / 1e9

    print(f"\n{MODELS[a.model]} on {model.dev.iface.card}, device {a.device}\n")
    row("startup", f"{t_start:.2f} s")
    row("  weights", f"{gb:.2f} GB in {model.t_weights:.2f} s ({gb / model.t_weights:.1f} GB/s)")
    row("  kernels", f"{len(m['kernels'])} kernels compiled, one launch graph built in {model.t_build:.2f} s")

    eos = next((i for i, t in enumerate(gen) if t in m["eos"]), len(gen))
    print()
    row("prompt", f"{a.prompt!r} ({len(ids)} tokens with the chat template)")
    row("output", tok.decode(gen[:eos]).strip())
    if eos < len(gen): row("", "(stopped at EOS)")
    elif len(ids) - 1 + len(gen) == model.npos: row("", "(stopped at context limit)")
    else: row("", "(stopped at token limit)")
    if ref["prompt_ids"] == ids:
      want = ref["generated_ids"]
      n = min(len(gen), len(want))
      same = next((i for i, (x, y) in enumerate(zip(gen, want)) if x != y), n)
      row("reference", f"{same}/{n} tokens match ({'OK' if same == n else 'MISMATCH'})")

    print()
    row("decode", f"{1e6 / s['period_us']:.1f} tok/s, {s['period_us'] / 1e3:.3f} ms/token (device clock)")
    row("  device", f"{s['busy_us']:.1f} us per token in the graph, {s['gap_us']:.2f} us between graphs")
  finally:
    model.close()

if __name__ == "__main__": main()
