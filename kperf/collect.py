"""Profile ONE kernel in isolation and write a kperf bundle.

  python -m kperf.collect --model 1b --kernel o [--layer 0] [--launches 300] [--context 4096]

Runs a single Llama launch (one program with one layer's args) back to back N times, with timestamper stamps on every
RISC, observer cores sampling each core's five PCs and three Tensix thread states over the debug bus, and an observer
reading all DRAM port counters. Kernels are deterministic, so every sample folds onto one 'time since launch start'
axis. --context N runs at position N over random KV caches (as bench.py does) instead of after a short
prompt. The bundle (kperf/bundles/*.kperf, see kperf/bundle.py) is what kperf/serve.py shows.
"""
import argparse, bisect, datetime, json, sys, time
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
import fw, llama3
from llama3 import ChatTokenizer, ARGS
from ops_blackhole import BlackholeComputeQueue
from kperf.stamps import ProfiledLlama3, align, PROLOGUE
from kperf.observer import Observer, DebugObserver, dram_read_targets, clean, settled, DRAM_EPS, PC_SIGNALS, STALL_SIGNALS, PC_MASK
from kperf.symbols import Symbolizer, KINDS, IDLE, thread_state
from kperf.findings import findings
from kperf import bundle as kbundle

US = 1 / fw.AICLK_MHZ
BIN, DBIN = 0.25, 0.5  # us: lane bins, DRAM bins
THREADS = {"t0": "T0 unpack", "t1": "T1 math", "t2": "T2 pack"}
LANES = list(fw.ROLES) + list(THREADS.values())
PIN_GBS = 514.6

def profile(model_key, kernel, layer, launches, device, context=0):
  model = ProfiledLlama3(model_key, device)
  try:
    m, dev = model.m, model.dev
    names = [n for n, _ in m["launches"]]
    k = [i for i, n in enumerate(names) if n == kernel][layer]
    cores = sorted({tuple(c["core"]) for c in m["programs"][kernel]["per_core"]})
    if context:  # random KV caches (timing does not depend on the values) and decode from position `context`
      caches = [b for b in m["uploads"] if b["kind"] == "zeros"]
      rand = (np.random.default_rng(0).standard_normal(max(b["size"] for b in caches) // 2, np.float32).view(np.uint32) >> 16).astype(np.uint16)
      for b in caches: dev.allocator._copyin(model.buffer(b), rand[:b["size"] // 2])
      ids = np.random.default_rng(0).integers(0, 128000, context + 1).tolist()
      model.generate(ids, 2, start=context)
    else:
      ids = ChatTokenizer(model.checkpoint).chat([{"role": "user", "content": "Write a story about a robot learning to paint."}])
      model.generate(ids, 2)  # activations, KV cache and the args of position len(ids)-1 are now in place
    args = model.args_base + (len(ids) - 1) * model.args_stride + ARGS * k
    stamps = dev.allocator._alloc(32 * launches)
    # observers: any worker outside this kernel's multicast bounding box
    x0, x1 = min(c[0] for c in cores), max(c[0] for c in cores)
    y0, y1 = min(c[1] for c in cores), max(c[1] for c in cores)
    spare = [c for c in dev.workers if not (x0 <= c[0] <= x1 and y0 <= c[1] <= y1)]
    dram_core, dbg_cores = spare[0], spare[1:]
    per = -(-len(cores) // len(dbg_cores))
    assert per <= 32, "not enough observer cores"
    groups = [cores[i:i + per] for i in range(0, len(cores), per)]
    model.arm()
    dram = Observer(dev, dram_core, dram_read_targets(), int(1 * fw.AICLK_MHZ))
    obs = [DebugObserver(dev, c, g, {**PC_SIGNALS, **STALL_SIGNALS}) for c, g in zip(dbg_cores, groups)]
    for o in [dram, *obs]: o.start()
    q = BlackholeComputeQueue()
    for i in range(launches): q.exec(model.prog[kernel], args, stamps + 32 * i)
    q.signal(dev.timeline_signal, dev.next_timeline()).submit(dev)
    dev.synchronize(60.0)
    samples = [(o.targets, *o.stop()) for o in obs]
    dram_raw = dram.stop_windows()
    events, lost, dups = model.collect(cores)
    raw = bytearray(32 * launches); dev.allocator._copyout(raw, stamps)
    win = np.frombuffer(bytes(raw), "<u8").reshape(-1, 4)[:, [1, 3]].astype(np.int64)
    spans, problems = align(model, events, [kernel] * launches)
    meta = dict(workers=[list(c) for c in dev.workers], observers=[list(c) for c in [dram_core, *dbg_cores[:len(groups)]]],
                cq=list(dev.cq_core), dma=list(dev.dma_core), card=dev.iface.card)
    meta["position"] = len(ids) - 1
    return m, cores, win, spans, problems, lost, dups, samples, dram_raw, meta
  finally:
    model.close()

def build(model_key, kernel, layer, m, cores, win, spans, problems, lost, dups, samples, dram, meta):
  N = len(win)
  dur = (win[:, 1] - win[:, 0]) * US
  starts = win[:, 0]
  sym = Symbolizer(ROOT / "kernels" / f"llama3-{model_key}", m)
  variant = {(tuple(c["core"]), r): v for c in m["programs"][kernel]["per_core"] for r, v in zip(m["roles"], c["variants"]) if v >= 0}

  # spans per core
  per_ck = defaultdict(list)
  for (i, c, r), (s, e) in spans.items(): per_ck[(c, r)].append((s, e, i))
  for v in per_ck.values(): v.sort()
  core_stats = {}
  for c in cores:
    roles, fin = {}, []
    for r in fw.ROLES:
      sp = per_ck.get((c, r))
      if not sp: continue
      rs = [(s - starts[i]) * US for s, _, i in sp]; re_ = [(e - starts[i]) * US for _, e, i in sp]
      roles[r] = [round(float(np.median(rs)), 3), round(float(np.median(re_)), 3)]
    if roles:
      core_stats[f"{c[0]},{c[1]}"] = dict(start=min(v[0] for v in roles.values()), finish=max(v[1] for v in roles.values()), roles=roles)

  # fold samples
  labels, label_id = [], {}
  def lab(lane, text, kind, file=None, pc=None):
    key = (lane, text)
    if key not in label_id:
      label_id[key] = len(labels)
      labels.append(dict(lane=lane, text=text, kind=kind, file=file, pc=pc, insns=Counter()))
    return label_id[key]
  bins = defaultdict(lambda: defaultdict(lambda: defaultdict(Counter)))  # core -> lane -> bin -> Counter(label)
  def where(c, r, t):
    sp = per_ck.get((c, r), [])
    j = bisect.bisect_right(sp, (t, 1 << 62)) - 1
    return sp[j] if j >= 0 and sp[j][0] <= t <= sp[j][1] else None
  n_samples, periods, pc_launches = 0, [], set()
  for targets, ts, vals in samples:
    nsw = len(ts["brisc"])
    if nsw > 1: periods.append(float(np.diff(ts["brisc"]).mean() * US))
    for kk in range(nsw):
      for j, c in enumerate(targets):
        ck = f"{c[0]},{c[1]}"
        for r in fw.ROLES:
          t = int(ts[r][kk]); hit = where(c, r, t)
          if hit is None: continue
          b = int((t - starts[hit[2]]) * US / BIN)
          pc = int(vals[r][kk, j]) & PC_MASK
          base = fw.CODE[r]
          off = pc - base if base <= pc < base + fw.CODE_SIZE[r] else pc - base - fw.SLOT_STRIDE
          off -= PROLOGUE
          if 0 <= off < fw.CODE_SIZE[r]:
            v = variant[(c, r)]
            text, kind, start, insn = sym.region(kernel, r, v, off)
            li = lab(r, text, kind, sym.file(kernel, r, v), start)
            labels[li]["insns"][insn] += 1
          else:
            li = lab(r, "firmware / launch stamp", IDLE)
          bins[ck][r][b][li] += 1
          n_samples += 1; pc_launches.add(hit[2])
        for th, lane in THREADS.items():
          role = "trisc" + th[1]
          t = int(ts[th][kk]); hit = where(c, role, t)
          if hit is None: continue
          b = int((t - starts[hit[2]]) * US / BIN)
          text, kind = thread_state(int(vals[th][kk, j]))
          bins[ck][lane][b][lab(lane, text, kind)] += 1

  # DRAM: per bank, per bin since launch start
  t_dram, v_dram, slow_reads = settled(*dram)
  v_dram, misreads = clean(v_dram)
  bank_of = np.array([(e[0] - 17) * 4 + (e[1] - 12) // 3 for e in DRAM_EPS] * 2)
  # Each pair of consecutive records gives every counter's mean rate over that window (~3 us, longer where congested
  # reads were dropped). A bin's value is the time-weighted mean of the windows overlapping it, folded per launch.
  dv = np.diff(v_dram, axis=0) % (1 << 32)
  nb = int(np.ceil(np.median(dur) * 1.15 / DBIN))
  pacc, wsum, cnt, dram_launches = np.zeros((nb, len(bank_of))), np.zeros(nb), np.zeros(nb, np.int64), set()
  nxt = np.append(starts[1:], np.iinfo(np.int64).max)
  for row, a, z in zip(dv, t_dram[:-1], t_dram[1:]):
    if z <= a: continue
    gbs = row * 64 / ((z - a) * US * 1e3)  # GB/s per counter
    i = max(bisect.bisect_right(starts, a) - 1, 0)
    while i < len(starts) and starts[i] < z:  # the window's piece inside each launch it overlaps
      lo, hi = (max(a, starts[i]) - starts[i]) * US, (min(z, nxt[i]) - starts[i]) * US
      for b in range(int(lo / DBIN), min(int(np.ceil(hi / DBIN)), nb)):
        w = min(hi, (b + 1) * DBIN) - max(lo, b * DBIN)
        if w > 0: pacc[b] += w * gbs; wsum[b] += w; cnt[b] += 1; dram_launches.add(i)
      i += 1
  ports = pacc / np.maximum(wsum, 1e-12)[:, None]
  banks = ports @ (bank_of[:, None] == np.arange(8)).astype(float)
  # physical tile of each counter (tt-metal blackhole_140_arch.yaml dram: bank b = column 0 or 9, rows DRAM_ROWS[b % 4])
  DRAM_ROWS = [[0, 1, 11], [2, 10, 3], [9, 4, 8], [5, 7, 6]]
  port_meta = [dict(noc=n, bank=int(bank_of[j]), port=(e[1] - 12) % 3,
                    tile=[0 if bank_of[j] < 4 else 9, DRAM_ROWS[bank_of[j] % 4][(e[1] - 12) % 3]], noc_coord=list(e))
               for j, (n, e) in enumerate([(n, e) for n in (0, 1) for e in DRAM_EPS])]
  bundle = dict(
    version=1, created=datetime.datetime.now().isoformat(timespec="seconds"),
    model=model_key, model_name=llama3.MODELS[model_key], kernel=kernel, layer=layer, position=meta["position"], launches=N, card=meta["card"],
    bin_us=BIN, dram_bin_us=DBIN, aiclk_mhz=fw.AICLK_MHZ, pin_gbs=PIN_GBS,
    grid=meta, cores=[list(c) for c in cores],
    launch=dict(median=float(np.median(dur)), p10=float(np.percentile(dur, 10)), p90=float(np.percentile(dur, 90)),
                all=[round(float(x), 3) for x in dur]),
    core_stats=core_stats, kinds=KINDS, lanes=LANES,
    labels=[dict(l, insns=l["insns"].most_common(6)) for l in labels],
    dram=dict(banks=[[round(float(x), 2) for x in row] for row in banks], samples=[int(x) for x in cnt],
              total=[round(float(x), 2) for x in banks.sum(1)],
              ports=[[round(float(x), 2) for x in row] for row in ports], port_meta=port_meta),
    quality=dict(samples=n_samples, sweep_us=float(np.mean(periods)) if periods else None, observers=len(samples),
                 alignment_problems=dict(problems), ring_overflow=[list(c) for c in lost], duplicate_stamps=dups,
                 dram_misreads=int(misreads), dram_slow_reads=slow_reads,
                 pc_launches=len(pc_launches), dram_launches=len(dram_launches)),  # launches the observer logs reached
  )
  bundle["streams"], bundle["arrays"] = kbundle.columns({(ck, lane): lb for ck, lanes in bins.items() for lane, lb in lanes.items()})
  bundle["findings"] = findings(bundle)
  return bundle

def main():
  ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
  ap.add_argument("--model", default="1b", choices=list(llama3.MODELS))
  ap.add_argument("--kernel", default="o")
  ap.add_argument("--layer", type=int, default=0)
  ap.add_argument("--launches", type=int, default=300)
  ap.add_argument("--device", type=int, default=0)
  ap.add_argument("--context", type=int, default=0, help="profile at this KV position over random caches (default: short prompt)")
  ap.add_argument("--name", help="bundle name (default <model>-<kernel>-L<layer>-<time>)")
  a = ap.parse_args()
  t = time.time()
  raw = profile(a.model, a.kernel, a.layer, a.launches, a.device, a.context)
  b = build(a.model, a.kernel, a.layer, *raw)
  name = a.name or f"{a.model}-{a.kernel}-L{a.layer}{f'-ctx{a.context}' if a.context else ''}-{datetime.datetime.now():%Y%m%d-%H%M%S}"
  path = HERE / "bundles" / f"{name}.kperf"
  kbundle.write(path, b)
  print(f"{b['model_name']} / {a.kernel}: median launch {b['launch']['median']:.2f} us over {b['launches']} launches, "
        f"{b['quality']['samples']} samples; {time.time() - t:.0f} s")
  for f in b["findings"]: print(f"  [{f['kind']}] {f['title']}")
  print(f"wrote {path} ({path.stat().st_size / 1e6:.1f} MB)")

if __name__ == "__main__": main()
