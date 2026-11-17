"""kprof sampling: where every RISC of every core spends its time, as a flame graph.

Runs decode with kprof's stamped kernels (exact per-RISC spans) while spare 'observer' cores sample, over the NoC,
every program core's five RISC PCs and its three Tensix threads' stall bits (debug bus), plus all DRAM port counters.
Each PC sample is attributed to the program whose span contains it and symbolized with kview: loops are named by
what they poll. Outputs:

  <out>.folded       collapsed stacks, open at https://www.speedscope.app (drag the file in)
  <out>.trace.json   Perfetto/chrome://tracing: per-RISC spans, launch windows, DRAM GB/s counter
  stdout             per program: where each RISC's time goes, and what each Tensix thread is stalled on

  python play/kprof_sample.py --model 1b --tokens 8 --out play/prof_1b
"""
import argparse, bisect, json, re, sys
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(ROOT), str(HERE), str(ROOT / "kview")]
import fw, llama3
from llama3 import ChatTokenizer
import decode as kview
from kprof import ProfiledLlama3, align
from observer import (Observer, DebugObserver, dram_read_targets, bandwidth, clean, PC_SIGNALS, STALL_SIGNALS, PC_MASK)

STALL_NAMES = [(0x2000000, "math"), (0x40000, "sfpu"), (0xC000000, "unpack"), (0x10000000, "pack"), (0x1000000, "tdma"),
               (0x100000, "sync (STALLWAIT/SEM)"), (0x80000, "cfg"), (0x200000, "thcon"), (0x800000, "move")]
THREADS = {"t0": "T0 unpack thread", "t1": "T1 math thread", "t2": "T2 pack thread"}
SPARE = [(15, y) for y in range(2, 12)] + [(16, y) for y in range(2, 10)]
PROLOGUE = 16  # kprof's stamp in front of every image

class Symbolizer:
  """pc offset in one kernel image -> (region, instruction) frames, via kview's annotated disassembly."""
  def __init__(self, kdir, manifest):
    self.kdir, self.m = kdir, manifest

  @lru_cache(maxsize=None)
  def image(self, program, role, variant):
    rel = self.m["programs"][program]["files"][role][variant]
    ctx = kview.Context(role, self.m, program, kview.ABI)
    d = kview.disassemble((self.kdir / rel).read_bytes(), ctx)
    rows = {r["pc"]: r for r in d["rows"]}
    # loops = backward branches; innermost loop containing pc names the region
    loops = sorted(((r["target"], r["pc"]) for r in d["rows"] if isinstance(r.get("target"), int) and r["target"] <= r["pc"]
                    and not r.get("call")), key=lambda l: l[1] - l[0])
    funcs = {f["pc"]: f for f in d["funcs"]}
    return rows, loops, funcs

  @staticmethod
  def _text(row):
    if row is None: return "?"
    ann = next((a for a in row.get("ann", ()) if a[0] in ("load", "store", "gist")), None)
    s = f"{row.get('op', '?')}"
    if ann: s += f" {'<-' if ann[0] == 'load' else '->' if ann[0] == 'store' else ''} {ann[1]}"
    return re.sub(r"[;\n]", ",", s)[:90]

  def frames(self, program, role, variant, off):
    rows, loops, funcs = self.image(program, role, variant)
    pc = off & ~3
    row = rows.get(pc)
    loop = next(((a, b) for a, b in loops if a <= pc <= b), None)
    fn = row.get("fn") if row else None
    out = []
    if fn not in (None, 0) and fn in funcs: out.append(re.sub(r"[;\n]", ",", f"{funcs[fn]['name']} {funcs[fn]['title']}"[:80]))
    if loop:
      a, b = loop
      body = [rows[p] for p in range(a, b + 4, 4) if p in rows]
      polls = [x for x in body if any(n[0] == "load" for n in x.get("ann", ()))]
      if b - a <= 40 and polls: out.append(f"wait loop @{a:#x}: {self._text(polls[0])}")
      else: out.append(f"loop @{a:#x}-{b:#x} ({(b - a) // 4 + 1} instrs)")
    else: out.append("straight-line code")
    out.append(f"{pc:#06x} {self._text(row)}")
    return out

BUSY_NAMES = [(0x30, "unpacker"), (0x40, "packer"), (0xF80, "tdma"), (0x8, "thcon"), (0x4, "mover")]

def stall_frames(word):
  names = [n for bit, n in STALL_NAMES if word & bit]
  if names: return ["stalled: " + "+".join(names)]
  busy = [n for bit, n in BUSY_NAMES if word & bit]
  return ["not stalled, busy: " + "+".join(busy)] if busy else ["not stalled, nothing busy"]

def main():
  ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
  ap.add_argument("--model", default="1b", choices=list(llama3.MODELS))
  ap.add_argument("--device", type=int, default=0)
  ap.add_argument("--tokens", type=int, default=6)
  ap.add_argument("--out", default=str(HERE / "prof"))
  a = ap.parse_args()
  model = ProfiledLlama3(a.model, a.device, profile=True)
  try:
    m = model.m
    used = sorted({tuple(c["core"]) for p in m["programs"].values() for c in p["per_core"]})
    spare = [c for c in SPARE if c not in used and c not in (model.dev.cq_core, model.dev.dma_core)]
    dram_core, dbg_cores = spare[0], spare[1:]
    per = -(-len(used) // len(dbg_cores))
    assert per <= 32, "not enough observer cores"
    groups = [used[i:i + per] for i in range(0, len(used), per)]
    signals = {**PC_SIGNALS, **STALL_SIGNALS}
    ids = ChatTokenizer(model.checkpoint).chat([{"role": "user", "content": "Write a story about a robot learning to paint."}])
    gen, _ = model.generate(ids, a.tokens + 1)
    model.arm()
    dram = Observer(model.dev, dram_core, dram_read_targets(), 2 * fw.AICLK_MHZ)
    obs = [DebugObserver(model.dev, c, g, signals) for c, g in zip(dbg_cores, groups)]
    for o in [dram, *obs]: o.start()
    gen2, stats = model.generate(ids, a.tokens, start=len(ids) - 1)
    samples = [o.stop() for o in obs]
    t_dram, v_dram = dram.stop()
    assert gen2 == gen[:a.tokens], "profiled run generated different tokens"
    events, lost = model.collect()
    if lost: print(f"WARNING: timestamp ring overflow on {len(lost)} cores")
    spans, seq, problems = align(model, events, a.tokens)
    if problems: print("alignment problems:", dict(problems))
    disp = model._timestamps(model.ts_base, len(ids) - 1 + a.tokens)[len(ids) - 1:]
  finally:
    model.close()

  # ---- attribute samples
  per_key = defaultdict(list)  # (core, role) -> sorted [(start, end, program, launch)]
  for (i, core, role), (s, e) in spans.items(): per_key[(core, role)].append((s, e, seq[i], i))
  for v in per_key.values(): v.sort()
  variant = {(name, tuple(c["core"]), role): v for name, p in m["programs"].items() for c in p["per_core"]
             for role, v in zip(m["roles"], c["variants"]) if v >= 0}
  sym = Symbolizer(ROOT / "kernels" / f"llama3-{a.model}", m)
  folded, per_prog, stall = Counter(), defaultdict(Counter), defaultdict(Counter)
  n_samples, period = 0, []
  g0, g1 = int(disp[0, 0]), int(disp[-1, -1])
  for (t, vals), o in zip(samples, obs):
    n_sw = len(t["brisc"])
    if n_sw > 1: period.append(np.diff(t["brisc"]).mean() / fw.AICLK_MHZ)
    for k in range(n_sw):
      if not g0 <= t["brisc"][k] <= g1: continue
      for j, core in enumerate(o.targets):
        for role in fw.ROLES:
          tk = int(t[role][k])
          pc = int(vals[role][k, j]) & PC_MASK
          sp = per_key.get((core, role), [])
          idx = bisect.bisect_right(sp, (tk, 1 << 62)) - 1
          inside = idx >= 0 and sp[idx][0] <= tk <= sp[idx][1]
          base, size = fw.CODE[role], fw.CODE_SIZE[role]
          slot_off = pc - base if base <= pc < base + size else pc - base - fw.SLOT_STRIDE if base + fw.SLOT_STRIDE <= pc < base + fw.SLOT_STRIDE + size else None
          if inside and slot_off is not None and slot_off >= PROLOGUE:
            prog = sp[idx][2]
            fr = sym.frames(prog, role, variant[(prog, core, role)], slot_off - PROLOGUE)
            stack = [prog, role, *fr]
          elif inside:
            prog = sp[idx][2]; stack = [prog, role, "firmware/stamp (outside kernel body)"]
          else:
            prog = None; stack = ["(no kernel running)", role]
          folded[";".join(stack)] += 1
          if prog: per_prog[(prog, role)][" > ".join(stack[2:4])] += 1
          n_samples += 1
        for th, name in THREADS.items():
          w = int(vals[th][k, j])
          # thread belongs to the program running on its TRISC
          role = {"t0": "trisc0", "t1": "trisc1", "t2": "trisc2"}[th]
          sp, tk = per_key.get((core, role), []), int(t[th][k])
          idx = bisect.bisect_right(sp, (tk, 1 << 62)) - 1
          if idx >= 0 and sp[idx][0] <= tk <= sp[idx][1]:
            prog = sp[idx][2]
            folded[";".join([prog, name, *stall_frames(w)])] += 1
            stall[(prog, name)][stall_frames(w)[0]] += 1

  out = Path(a.out)
  out.with_suffix(".folded").write_text("".join(f"{k} {v}\n" for k, v in sorted(folded.items())))
  print(f"{n_samples} RISC samples from {len(obs)} observers, sweep period {np.mean(period):.1f} us; "
        f"decode {stats['period_us'] / 1e3:.3f} ms/token while profiling")

  # ---- report
  names = list(dict.fromkeys(seq))
  for prog in names:
    tot = {r: sum(per_prog[(prog, r)].values()) for r in fw.ROLES}
    if not any(tot.values()): continue
    print(f"\n=== {prog}")
    for r in fw.ROLES:
      if not tot[r]: continue
      top = per_prog[(prog, r)].most_common(4)
      print(f"  {r:7} " + " | ".join(f"{c / tot[r]:4.0%} {k[:70]}" for k, c in top))
    for th in THREADS.values():
      c = stall[(prog, th)]
      if c: print(f"  {th:17} " + ", ".join(f"{k} {v / sum(c.values()):.0%}" for k, v in c.most_common(4)))

  # ---- trace: spans + launch windows + DRAM bandwidth
  origin, us = int(disp[0, 0]), 1 / fw.AICLK_MHZ
  ev = [dict(name=seq[i], ph="X", ts=(s - origin) * us, dur=(e - s) * us, pid=f"core {c[0]},{c[1]}", tid=r)
        for (i, c, r), (s, e) in spans.items()]
  L = len(llama3_launches := [n for n, _ in m["launches"]])
  for pos in range(disp.shape[0]):
    for k, name in enumerate(llama3_launches):
      w0, w1 = int(disp[pos, 1 + 2 * k]), int(disp[pos, 2 + 2 * k])
      ev.append(dict(name=name, ph="X", ts=(w0 - origin) * us, dur=(w1 - w0) * us, pid="dispatcher", tid="launches"))
  v_dram, _ = clean(v_dram)
  tm, bw = bandwidth(t_dram, v_dram)
  ev += [dict(name="DRAM read GB/s", ph="C", ts=(int(x) - origin) * us, pid="DRAM", args={"GB/s": round(float(b), 1)})
         for x, b in zip(tm, bw) if g0 <= x <= g1]
  out.with_suffix(".trace.json").write_text(json.dumps(dict(traceEvents=ev, displayTimeUnit="ns")))
  print(f"\nwrote {out.with_suffix('.folded')} (speedscope.app) and {out.with_suffix('.trace.json')} (ui.perfetto.dev)")

if __name__ == "__main__": main()
