"""kbench: profile ONE kernel in isolation. Runs a single Llama launch (one program, one layer's args) back to back N
times, with kprof stamps on every RISC, observer cores sampling PCs + Tensix thread stall state, and DRAM port
counters. Kernels are deterministic, so all samples fold onto one 'time since launch start' axis.

  python play/kbench.py --model 1b --kernel o [--launches 300] [--out play/kb]

Writes <out>-<model>-<kernel>.trace.json (ui.perfetto.dev): three cores (typical = all cores aggregated, slowest,
fastest), each with 5 RISC lanes + 3 Tensix thread lanes showing the dominant code region / stall state over time,
plus DRAM GB/s on the same axis. Also <...>.folded (speedscope.app) and a text report.
"""
import argparse, bisect, json, re, struct, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(ROOT), str(HERE), str(ROOT / "kview")]
import fw, llama3
from llama3 import ChatTokenizer, ARGS
from ops_blackhole import BlackholeComputeQueue
from kprof import ProfiledLlama3, align
from kprof_sample import Symbolizer, stall_frames, THREADS, SPARE, PROLOGUE
from observer import Observer, DebugObserver, dram_read_targets, bandwidth, clean, PC_SIGNALS, STALL_SIGNALS, PC_MASK

US = 1 / fw.AICLK_MHZ
BIN = 0.25  # us

def short(frames):
  """Lane label: the region (and its function), without the instruction."""
  s = " / ".join(frames[:-1]) if len(frames) > 1 else frames[0]
  s = re.sub(r"Tensix: [A-Z0-9_ …]+", "Tensix", s)
  return s[:110]

def run(a):
  model = ProfiledLlama3(a.model, a.device, profile=False)
  try:
    m, dev = model.m, model.dev
    names = [n for n, _ in m["launches"]]
    k = [i for i, n in enumerate(names) if n == a.kernel][a.layer]  # launch index within one position
    cores = sorted({tuple(c["core"]) for c in m["programs"][a.kernel]["per_core"]})
    ids = ChatTokenizer(model.checkpoint).chat([{"role": "user", "content": "Write a story about a robot learning to paint."}])
    model.generate(ids, 2)  # activations, KV cache and per-position args for position len(ids)-1 are now in place
    pos = len(ids) - 1
    args = model.args_base + pos * model.args_stride + ARGS * k
    stamps = dev.allocator._alloc(32 * a.launches)
    # observers: spread the kernel's cores over the spare tiles
    spare = [c for c in SPARE if c not in {tuple(c2["core"]) for p in m["programs"].values() for c2 in p["per_core"]}
             and c not in (dev.cq_core, dev.dma_core)]
    dram_core, dbg_cores = spare[0], spare[1:]
    per = -(-len(cores) // len(dbg_cores))
    groups = [cores[i:i + per] for i in range(0, len(cores), per)]
    model.arm()
    dram = Observer(dev, dram_core, dram_read_targets(), int(1 * fw.AICLK_MHZ))
    obs = [DebugObserver(dev, c, g, {**PC_SIGNALS, **STALL_SIGNALS}) for c, g in zip(dbg_cores, groups)]
    for o in [dram, *obs]: o.start()
    q = BlackholeComputeQueue()
    for i in range(a.launches): q.exec(model.prog[a.kernel], args, stamps + 32 * i)
    q.signal(dev.timeline_signal, dev.next_timeline()).submit(dev)
    dev.synchronize(60.0)
    samples = [o.stop() for o in obs]
    t_dram, v_dram = dram.stop()
    events, lost = model.collect()
    raw = bytearray(32 * a.launches); dev.allocator._copyout(raw, stamps)
    win = np.frombuffer(bytes(raw), "<u8").reshape(-1, 4)[:, [1, 3]].astype(np.int64)  # dispatcher: EXEC start, all done
    # align: every launch is the same program
    model.launches = [(a.kernel, None)]
    spans, seq, problems = align(model, events, a.launches)
    return m, cores, win, spans, problems, lost, samples, obs, (t_dram, v_dram)
  finally:
    model.close()

def main():
  ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
  ap.add_argument("--model", default="1b", choices=list(llama3.MODELS))
  ap.add_argument("--kernel", default="o")
  ap.add_argument("--layer", type=int, default=0, help="which occurrence of the kernel in a position (its args)")
  ap.add_argument("--launches", type=int, default=300)
  ap.add_argument("--device", type=int, default=0)
  ap.add_argument("--out", default=str(HERE / "kb"))
  a = ap.parse_args()
  m, cores, win, spans, problems, lost, samples, obs, (t_dram, v_dram) = run(a)
  if problems: print("alignment problems:", dict(problems))
  if lost: print(f"WARNING: timestamp ring overflow on {len(lost)} cores")
  N = len(win)
  dur = (win[:, 1] - win[:, 0]) * US
  print(f"{llama3.MODELS[a.model]} / {a.kernel} (layer {a.layer}), {len(cores)} cores, {N} back-to-back launches")
  print(f"launch window (dispatcher EXEC start -> all cores done): median {np.median(dur):.2f} us, "
        f"p10 {np.percentile(dur, 10):.2f}, p90 {np.percentile(dur, 90):.2f}")

  # per launch: core start/end relative to the launch's EXEC start
  core_end = defaultdict(list); core_start = defaultdict(list); role_dur = defaultdict(list)
  by_launch = defaultdict(dict)
  for (i, c, r), (s, e) in spans.items():
    by_launch[i][(c, r)] = (s, e)
  for i, d in by_launch.items():
    w0 = win[i, 0]
    ends = defaultdict(int)
    for (c, r), (s, e) in d.items():
      ends[c] = max(ends[c], e); role_dur[r].append((e - s) * US)
      if r == "brisc": core_start[c].append((s - w0) * US)
    for c, e in ends.items(): core_end[c].append((e - w0) * US)
  fin = {c: float(np.median(v)) for c, v in core_end.items()}
  order = sorted(fin, key=fin.get)
  slow, fast = order[-1], order[0]
  med_core = order[len(order) // 2]
  print(f"core finish (median over launches, us after EXEC start): fastest {fast} {fin[fast]:.2f}, median {fin[med_core]:.2f}, "
        f"slowest {slow} {fin[slow]:.2f}; start skew {np.median([max(v) - min(v) for v in zip(*core_start.values())]) if core_start else 0:.2f} us")
  xs = sorted({c[0] for c in fin}); ys = sorted({c[1] for c in fin}); lo = fin[fast]
  print("finish time minus fastest core (us):\n     " + "".join(f"{x:>5}" for x in xs))
  for y in ys: print(f"y={y:<3}" + "".join(f"{fin[(x, y)] - lo:5.1f}" if (x, y) in fin else "    ." for x in xs))

  # ---- fold samples onto time-since-launch-start
  sym = Symbolizer(ROOT / "kernels" / f"llama3-{a.model}", m)
  variant = {(tuple(c["core"]), r): v for c in m["programs"][a.kernel]["per_core"] for r, v in zip(m["roles"], c["variants"]) if v >= 0}
  starts = win[:, 0]
  lanes = {"typical": defaultdict(lambda: defaultdict(Counter)), "slowest": defaultdict(lambda: defaultdict(Counter)),
           "fastest": defaultdict(lambda: defaultdict(Counter))}
  folded, totals = Counter(), defaultdict(Counter)
  spans_ck = defaultdict(list)
  for (i, c, r), (s, e) in spans.items(): spans_ck[(c, r)].append((s, e, i))
  for v in spans_ck.values(): v.sort()
  def where(c, r, t):
    sp = spans_ck.get((c, r), [])
    j = bisect.bisect_right(sp, (t, 1 << 62)) - 1
    return sp[j] if j >= 0 and sp[j][0] <= t <= sp[j][1] else None
  for (ts, vals), o in zip(samples, obs):
    for kk in range(len(ts["brisc"])):
      for j, c in enumerate(o.targets):
        which = ["typical"] + (["slowest"] if c == slow else []) + (["fastest"] if c == fast else [])
        for r in fw.ROLES:
          t = int(ts[r][kk]); hit = where(c, r, t)
          if hit is None: continue
          tau = (t - starts[hit[2]]) * US
          pc = int(vals[r][kk, j]) & PC_MASK
          base = fw.CODE[r]; off = pc - base if base <= pc < base + fw.CODE_SIZE[r] else pc - base - fw.SLOT_STRIDE
          fr = sym.frames(a.kernel, r, variant[(c, r)], off - PROLOGUE) if 0 <= off - PROLOGUE < fw.CODE_SIZE[r] else ["firmware / stamp"]
          for w in which: lanes[w][r][int(tau / BIN)][short(fr)] += 1
          folded[";".join([a.kernel, r, *fr])] += 1
          totals[r][short(fr)] += 1
        for th, tname in THREADS.items():
          role = "trisc" + th[1]
          t = int(ts[th][kk]); hit = where(c, role, t)
          if hit is None: continue
          tau = (t - starts[hit[2]]) * US
          lab = stall_frames(int(vals[th][kk, j]))[0]
          for w in which: lanes[w][tname][int(tau / BIN)][lab] += 1
          folded[";".join([a.kernel, tname, lab])] += 1
          totals[tname][lab] += 1

  print("\nwhere the time goes (all cores, all launches):")
  for lane, cnt in totals.items():
    tot = sum(cnt.values())
    print(f"  {lane:17} " + " | ".join(f"{v / tot:4.0%} {k[:60]}" for k, v in cnt.most_common(3)))

  # ---- DRAM bandwidth folded onto the same axis
  v_dram, _ = clean(v_dram)
  tm, bw = bandwidth(t_dram, v_dram)
  bins = defaultdict(list)
  for x, b in zip(tm, bw):
    i = bisect.bisect_right(starts, x) - 1
    if i >= 0 and x <= win[i, 1]: bins[int((x - starts[i]) * US / 0.5)].append(b)
  # per DRAM bank (3 ports x 2 NoCs each), in the first 25% of the launch vs the middle
  from observer import DRAM_EPS
  bank_of = [(e[0] - 17) * 4 + (e[1] - 12) // 3 for e in DRAM_EPS] * 2
  dv = np.diff(v_dram, axis=0) % (1 << 32); dt = np.diff(t_dram) * US * 1e-6
  phase = {"first 25%": (0.0, 0.25), "middle 50%": (0.25, 0.75), "last 25%": (0.75, 1.0)}
  acc = {k: np.zeros(8) for k in phase}; tim = {k: 0.0 for k in phase}
  md = float(np.median(dur))
  for row, x, d in zip(dv, tm, dt):
    i = bisect.bisect_right(starts, x) - 1
    if i < 0 or x > win[i, 1]: continue
    f = (x - starts[i]) * US / md
    for kname, (lo_, hi_) in phase.items():
      if lo_ <= f < hi_:
        for j, b in enumerate(bank_of): acc[kname][b] += row[j] * 64
        tim[kname] += d
  print("\nDRAM read GB/s per bank (controller), by phase of the launch:")
  print("  " + " " * 12 + "".join(f"{b:>7}" for b in range(8)) + "    total")
  for kname in phase:
    g = acc[kname] / max(tim[kname], 1e-12) / 1e9
    print(f"  {kname:<12}" + "".join(f"{x:7.0f}" for x in g) + f"  {g.sum():7.0f}")
  print("\nDRAM read GB/s vs time since launch start (0.5 us bins, mean over launches):")
  dmax = max(bins) if bins else 0
  print("  " + " ".join(f"{np.mean(bins[i]):.0f}" if i in bins else "." for i in range(dmax + 1)))

  # ---- trace
  ev, pid = [], 0
  def meta(p, name, sort): ev.extend([dict(name="process_name", ph="M", pid=p, args=dict(name=name)),
                                      dict(name="process_sort_index", ph="M", pid=p, args=dict(sort_index=sort))])
  lane_order = list(fw.ROLES) + list(THREADS.values())
  for idx, (key, title) in enumerate((("typical", f"A. typical core (all {len(cores)} cores folded)"),
                                      ("slowest", f"B. slowest core {slow[0]},{slow[1]} (done at {fin[slow]:.1f} us)"),
                                      ("fastest", f"C. fastest core {fast[0]},{fast[1]} (done at {fin[fast]:.1f} us)"))):
    pid += 1; meta(pid, title, idx)
    for tid, lane in enumerate(lane_order):
      ev.append(dict(name="thread_name", ph="M", pid=pid, tid=tid, args=dict(name=lane)))
      ev.append(dict(name="thread_sort_index", ph="M", pid=pid, tid=tid, args=dict(sort_index=tid)))
      b = lanes[key].get(lane, {})
      if not b: continue
      cur, t0, share = None, 0, []
      for i in range(max(b) + 2):
        c = b.get(i)
        lab = c.most_common(1)[0][0] if c and sum(c.values()) >= (3 if key == "typical" else 1) else None
        if lab != cur:
          if cur: ev.append(dict(name=cur, ph="X", pid=pid, tid=tid, ts=t0 * BIN, dur=(i - t0) * BIN))
          cur, t0 = lab, i
  pid += 1; meta(pid, "D. DRAM read bandwidth (all ports)", 3)
  for i in range(dmax + 1):
    if i in bins: ev.append(dict(name="DRAM GB/s", ph="C", pid=pid, ts=i * 0.5, args={"GB/s": round(float(np.mean(bins[i])), 1)}))
  pid += 1; meta(pid, "E. launch window (dispatcher)", 4)
  ev.append(dict(name=f"{a.kernel}: median launch", ph="X", pid=pid, tid=0, ts=0, dur=float(np.median(dur))))
  out = Path(f"{a.out}-{a.model}-{a.kernel}")
  out.with_suffix(".trace.json").write_text(json.dumps(dict(traceEvents=ev, displayTimeUnit="ns")))
  out.with_suffix(".folded").write_text("".join(f"{k} {v}\n" for k, v in sorted(folded.items())))
  print(f"\nwrote {out.with_suffix('.trace.json')} ({len(ev)} events; ui.perfetto.dev) and {out.with_suffix('.folded')} (speedscope.app)")

if __name__ == "__main__": main()
