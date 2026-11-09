import argparse, collections, json, struct, time
from pathlib import Path
import numpy as np
import fw
from cq import ComputeQueue, HWQueue, dram, rects
from device import Device
from helpers import round_up, safe_load

KDIR = Path(__file__).resolve().parent / "kernels" / "llama1b"
ARGS = 64  # up to 16 dynamic words per launch

def mean(xs): return sum(xs) / len(xs) if xs else float("nan")

class Llama1B:
  def __init__(self, device=0, weights=None, *, profile=False):
    self.profile = profile
    self.m = m = json.loads((KDIR / "manifest.json").read_text())
    self.launches = m["launches"]
    self.dev = dev = Device(device)
    try:
      dev.dram_top = round_up(fw.DRAM_BANKS * m["dram_top"], 1 << 30)  # our heap goes above the old layout
      t = time.perf_counter()
      self._upload_weights(weights or m["checkpoint"])
      self.t_weights = time.perf_counter() - t
      t = time.perf_counter()
      self._install()
      self._build()
      self.t_build = time.perf_counter() - t
      self.ns_per_tick = self._calibrate()
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
    tensors = safe_load(path if path.is_file() else path / "model.safetensors")
    sources, zeros, self.weight_bytes = [], [], 0
    for b in self.m["uploads"]:
      if b["kind"] == "tensor":
        t = tensors[b["src"]]
        assert t.nbytes <= b["size"], (b["name"], t.nbytes, b["size"])
        sources.append((self.buffer(b), t.path, t.offset, t.nbytes))
      elif b["kind"] == "file": sources.append((self.buffer(b), KDIR / b["src"], 0, (KDIR / b["src"]).stat().st_size))
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
      files = {role: [(KDIR / f).read_bytes() for f in fs] for role, fs in p['files'].items()}
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

  def _calibrate(self) -> float:
    """Device wall clock ticks -> ns, against the host clock."""
    dev, sig = self.dev, 250
    def stamp(n):
      HWQueue().timestamp(dev.signal(sig)).signal(dev.signal(sig), n).submit(dev.compute)
      return dev.wait(sig, n), time.perf_counter_ns()
    (d0, h0), _ = stamp(1), time.sleep(0.2)
    d1, h1 = stamp(2)
    return (h1 - h0) / (d1 - d0)

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

  def generate(self, ids, steps):
    """Decode the prompt and steps more positions in one go. Returns (generated ids, stats)."""
    P, n = len(ids), len(ids) - 1 + steps
    ops0 = self._ring_ops()
    assert steps > 0 and 0 < P and n <= self.npos, "steps must be positive and prompt + steps must fit the context"
    hist = np.zeros(self.m["max_tokens"], "<u4")
    hist[:P] = ids
    self.dev.copyin(self.buffer(self.m["history"]), hist)
    self.dev.sysmem.mem[self.host:self.host + 16 * (n + 1)] = bytes(16 * (n + 1))
    t = time.perf_counter_ns()
    self._upload_args(n, P)
    t_args = time.perf_counter_ns() - t
    submit, wall = self._run(self.graph_base, self.graph_size, self.graph_stride, n)
    request_ops = {q: c - ops0[q] for q, c in self._ring_ops().items()}  # timestamp readback below not included
    ts = self._timestamps(self.ts_base, n)
    gen = [struct.unpack_from("<I", self.dev.sysmem.mem, self.host + 16 * (p + 1))[0] for p in range(P - 1, n)]
    tick = self.ns_per_tick
    g = ts[P - 1:]  # the positions that generate a token
    stats = dict(ops=request_ops, positions=n, steps=steps, args_upload_us=t_args / 1e3, submit_us=submit / 1e3, wall_us=wall / 1e3,
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
  ap.add_argument("--device", type=int, default=0)
  ap.add_argument("--prompt", default="Write a story about a robot learning to paint.")
  ap.add_argument("--steps", type=int, default=64)
  ap.add_argument("--weights", help="checkpoint directory (default: the one the kernels were exported with)")
  ap.add_argument("--profile", action="store_true", help="record per-launch timestamps and report kernel/dispatch timings")
  a = ap.parse_args()
  if a.steps < 1: ap.error("--steps must be positive")
  from transformers import AutoTokenizer
  t0 = time.perf_counter()
  model = Llama1B(a.device, a.weights, profile=a.profile)
  try:
    m = model.m
    tok = AutoTokenizer.from_pretrained(a.weights or m["checkpoint"], local_files_only=True)
    ids = tok.apply_chat_template([{"role": "user", "content": a.prompt}], add_generation_prompt=True)
    if not isinstance(ids, list): ids = ids["input_ids"]
    t_start = time.perf_counter() - t0
    gen, s = model.generate(ids, a.steps)
    if a.profile: per_exec, noop_token = model.dispatch_baseline()
    row = lambda label, text: print(f"{label:<12}{text}")
    gb = model.weight_bytes / 1e9

    print(f"\nLlama 3.2 1B on {model.dev.pci_dev.card}, device {a.device}\n")
    row("startup", f"{t_start:.2f} s")
    row("  weights", f"{gb:.2f} GB in {model.t_weights:.2f} s ({gb / model.t_weights:.1f} GB/s)")
    row("  kernels", f"{len(m['programs'])} programs, {model.code_slot_bytes / 1024:.1f} KB of double-buffered code slots per core, "
                     f"{model.npos} position graphs built in {model.t_build:.2f} s")

    eos = next((i for i, t in enumerate(gen) if t in m["eos"]), len(gen))
    print()
    row("prompt", f"{a.prompt!r} ({len(ids)} tokens with the chat template)")
    row("output", tok.decode(gen[:eos]).strip())
    if eos < len(gen): row("", f"(EOS after {eos} tokens; the device kept going, timing covers all {len(gen)})")
    ref = json.loads((KDIR / "reference.json").read_text()) if (KDIR / "reference.json").exists() else None
    if ref and ref["prompt_ids"] == ids:
      want = ref["generated_ids"]
      n = min(len(gen), len(want))
      same = next((i for i, (x, y) in enumerate(zip(gen, want)) if x != y), n)
      row("reference", f"{same}/{n} tokens match blackhole-py ({'OK' if same == n else 'MISMATCH'}; "
                       f"it runs {1e6 / ref['mean_wall_us']:.1f} tok/s)")

    print()
    row("decode", f"{1e6 / s['period_us']:.1f} tok/s, {s['period_us'] / 1e3:.3f} ms/token "
                  f"({s['steps']} tokens, device clock, {model.nts} timestamps per token)")
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
    ks, steps = s["kernels"], s["steps"]
    tot = sum(v.sum() for v in ks.values()) / steps
    print(f"\n{'kernel':<12}{'launches':>9}{'us/launch':>11}{'min':>9}{'max':>9}{'us/token':>11}{'share':>8}")
    for name, v in sorted(ks.items(), key=lambda kv: -kv[1].sum()):
      per_tok = v.sum() / steps
      print(f"{name:<12}{len(v) // steps:>9}{v.mean():>11.1f}{v.min():>9.1f}{v.max():>9.1f}{per_tok:>11.1f}{per_tok / tot:>8.1%}")
    print(f"{'total':<12}{sum(len(v) for v in ks.values()) // steps:>9}{'':>29}{tot:>11.1f}")
    print(f"{'dispatch':<12}{len(model.launches):>9}{per_exec:>11.1f}{'':>18}{noop_token:>11.1f}{noop_token / tot:>8.1%}"
          f"   no-op kernels: already inside each row above")
  finally:
    model.close()

if __name__ == "__main__": main()
