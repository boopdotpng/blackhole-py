"""kprof: per-core, per-RISC kernel timeline for blackhole-py, using the Tensix hardware debug timestamper.

Every kernel image gets a 16-byte prologue and epilogue that each store one token to RISCV_DEBUG_REG_TIMESTAMP
(0xFFB121FC). The hardware appends {token, 64-bit wall clock} as one atomic 16-byte write to a ring in L1, so all five
RISCs of a core share one stream with no locking. Cost: ~3 instructions per stamp. No kernel regeneration needed:
kernels are position-independent and their return jump is appended at install time anyway.

  python play/kprof.py --model 1b --tokens 3 [--trace out.json]

Reports, per program: dispatch -> first kernel start, start skew across cores, per-RISC busy time, the finish spread
(median core vs last core), which RISC finishes last and which cores are most often last, and the drain to the
dispatcher's done stamp. --trace writes Chrome trace events (open in ui.perfetto.dev): one process per core, one
thread per RISC.
"""
import argparse, json, struct, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import fw
import llama3
from llama3 import Llama3, ChatTokenizer

# Debug timestamper registers (tt-isa-documentation .../DebugTimestamper.md), NoC-visible on every Tensix tile
TS_CMD, TS_CNTL, TS_STATUS, TS_B0_START, TS_B0_END = 0xFFB121FC, 0xFFB12200, 0xFFB12204, 0xFFB12208, 0xFFB1220C
RING, RING_SIZE = 0x100000, 0x80000  # measured: no Llama kernel writes worker L1 above 0xC0000
START, END = 0, 1

def token(prog:int, role:int, kind:int) -> int:  # 128-bit event (low 3 bits 0); fits addi's 12-bit immediate
  t = prog << 7 | role << 4 | kind << 3
  assert 0 <= t < 2048
  return t

def stamp(tok:int) -> bytes:  # lui t0, 0xFFB12 ; addi t1, zero, tok ; sw t1, 0x1FC(t0) ; nop
  return struct.pack("<4I", 0xFFB12 << 12 | 5 << 7 | 0x37, tok << 20 | 6 << 7 | 0x13,
                     (0x1FC >> 5) << 25 | 6 << 20 | 5 << 15 | 2 << 12 | (0x1FC & 31) << 7 | 0x23, 0x13)

def wrap(image:bytes, role:str, prog:int) -> bytes:
  """Prologue stamp + kernel + epilogue stamp (+ the return jump the caller appends). Shifts the PC-relative kernel by
  16 bytes, which keeps its alignment. Clobbers t0/t1 at entry (kernels may not assume register contents) and exit."""
  r = fw.ROLES.index(role)
  return stamp(token(prog, r, START)) + image + stamp(token(prog, r, END))

class ProfiledLlama3(Llama3):
  """Llama3 whose installed kernel images are wrapped with timestamper stamps."""
  def _install(self):
    self.prog_ids = {n: i for i, n in enumerate(self.m["programs"])}
    # _install reads kernels/<model>/<program>/<role>[.vN].bin; wrap each image as it is read.
    orig_read = Path.read_bytes
    def read_bytes(p):
      data = orig_read(p)
      role = p.name.split(".")[0]
      if p.suffix == ".bin" and p.parent.parent == self.kdir and p.parent.name in self.prog_ids and role in fw.ROLES:
        data = wrap(data, role, self.prog_ids[p.parent.name])
        assert len(data) + 4 <= fw.CODE_SIZE[role], (p, len(data))
      return data
    Path.read_bytes = read_bytes
    try: super()._install()
    finally: Path.read_bytes = orig_read
    # Which (core, role) runs each program: needed to align each core's event stream with the launch sequence.
    self.runs = {n: {(tuple(c["core"]), role) for c in p["per_core"] for role, v in zip(self.m["roles"], c["variants"]) if v >= 0}
                 for n, p in self.m["programs"].items()}

  # ---- rings
  def arm(self):
    io = self.dev.iface
    for c in self.dev.workers:
      io.write32(c, TS_CNTL, 1 << 31 | 1); io.write32(c, TS_CNTL, 1)  # pulse reset_streams; buffer 0 valid, 1 off
      io.write32(c, TS_STATUS, 0x33)                                   # clear full/overflow sticky bits, position 0
      io.write32(c, TS_B0_START, RING // 16); io.write32(c, TS_B0_END, (RING + RING_SIZE) // 16 - 1)

  def collect(self):
    io, events, lost = self.dev.iface, {}, []
    for c in self.dev.workers:
      st = io.read32(c, TS_STATUS)
      if st & 0x11: lost.append(c)
      pos = st >> 14
      raw = np.frombuffer(io.read(c, RING, pos * 16), "<u4").reshape(-1, 4) if pos else np.zeros((0, 4), "<u4")
      evs, last, dups = [], {}, 0
      for h, lo, hi, _ in raw:
        h, t = int(h), int(lo) | int(hi) << 32
        # Measured: one sw to TS_CMD is sometimes recorded 2-4 times, 2 cycles apart (store replay around launch
        # entry/exit). A given (program, role, start|end) happens once per launch, so drop near-identical repeats.
        if h in last and t - last[h] < 64: dups += 1; continue
        last[h] = t
        evs.append((h, t))
      events[c] = evs
      self.duplicates = getattr(self, "duplicates", 0) + dups
    return events, lost

def align(model, events, positions):
  """-> {(launch index, core, role): (t_start, t_end)}. Launch index runs over positions x model.launches.
  The k-th start of program P by (core, role) is the k-th launch of P in the sequence that (core, role) takes part in."""
  names = {i: n for n, i in model.prog_ids.items()}
  seq = [name for _ in range(positions) for name, _ in model.launches]
  out, problems = {}, Counter()
  for core, evs in events.items():
    for r, role in enumerate(fw.ROLES):
      mine = [i for i, n in enumerate(seq) if (core, role) in model.runs[n]]
      starts = [(t, names[h >> 7]) for h, t in evs if (h >> 4 & 7) == r and not (h >> 3 & 1)]
      ends = [(t, names[h >> 7]) for h, t in evs if (h >> 4 & 7) == r and (h >> 3 & 1)]
      if not mine and not starts: continue
      if len(starts) != len(mine) or len(ends) != len(mine):
        problems[f"{role}: {len(starts)} starts / {len(ends)} ends, expected {len(mine)}"] += 1
        continue
      for i, (s, e) in zip(mine, zip(starts, ends)):
        if s[1] != seq[i] or e[1] != seq[i]: problems["program order mismatch"] += 1; continue
        out[(i, core, role)] = (s[0], e[0])
  return out, seq, problems

def report(model, spans, seq, disp, positions):
  """disp: (positions, 2*launches+2) dispatcher timestamps from --profile (EXEC start/end pairs)."""
  us = 1 / fw.AICLK_MHZ
  by_launch = defaultdict(dict)
  for (i, core, role), (s, e) in spans.items(): by_launch[i][(core, role)] = (s, e)
  rows = defaultdict(lambda: defaultdict(list))
  last_core, last_role = defaultdict(Counter), defaultdict(Counter)
  L = len(model.launches)
  for i, d in by_launch.items():
    name, pos, k = seq[i], i // L, i % L
    w0, w1 = int(disp[pos, 1 + 2 * k]), int(disp[pos, 2 + 2 * k])  # dispatcher: before fetch/GO, after all done
    starts = [s for s, _ in d.values()]
    core_end = defaultdict(int)
    for (core, role), (s, e) in d.items(): core_end[core] = max(core_end[core], e)
    ends = sorted(core_end.values())
    t0, tl = min(starts), ends[-1]
    (lc, lr), _ = max(d.items(), key=lambda kv: kv[1][1])
    last_core[name][lc] += 1; last_role[name][lr] += 1
    r = rows[name]
    r["window"].append((w1 - w0) * us)
    r["dispatch->first start"].append((t0 - w0) * us)
    bs = [s for (c, ro), (s, _) in d.items() if ro == "brisc"]
    r["brisc start skew"].append((max(bs) - min(bs)) * us if bs else float("nan"))
    r["first start->median core end"].append((ends[len(ends) // 2] - t0) * us)
    r["median->last core end (tail)"].append((tl - ends[len(ends) // 2]) * us)
    r["last end->dispatcher done"].append((w1 - tl) * us)
    for role in fw.ROLES:
      ds = [(e - s) * us for (c, ro), (s, e) in d.items() if ro == role]
      if ds: r[f"{role} busy (max core)"].append(max(ds))
  print(f"\n{'program':<10}{'n':>4}  " + "  ".join(f"{h:>12}" for h in ("window", "disp->start", "skew", "->median end", "tail", "drain")) + "   last RISC (share)   most-often-last cores")
  for name in dict.fromkeys(seq):
    if name not in rows: continue
    r, n = rows[name], len(rows[name]["window"])
    cols = [np.median(r[k]) for k in ("window", "dispatch->first start", "brisc start skew", "first start->median core end",
                                      "median->last core end (tail)", "last end->dispatcher done")]
    lr = ", ".join(f"{k} {v / n:.0%}" for k, v in last_role[name].most_common(2))
    lc = " ".join(f"{c[0]},{c[1]}:{v}" for c, v in last_core[name].most_common(3))
    print(f"{name:<10}{n:>4}  " + "  ".join(f"{x:10.2f}us" for x in cols) + f"   {lr:<20} {lc}")
  print("\nper-RISC busy time on the slowest core (median over launches, us):")
  print(f"{'program':<10}" + "".join(f"{r:>9}" for r in fw.ROLES))
  for name in dict.fromkeys(seq):
    if name in rows: print(f"{name:<10}" + "".join(f"{np.median(rows[name][f'{r} busy (max core)']) if rows[name][f'{r} busy (max core)'] else float('nan'):9.2f}" for r in fw.ROLES))
  return rows

def chrome_trace(spans, seq, path, origin):
  ev = []
  for (i, core, role), (s, e) in spans.items():
    ev.append(dict(name=seq[i], ph="X", ts=(s - origin) / fw.AICLK_MHZ, dur=(e - s) / fw.AICLK_MHZ,
                   pid=f"core {core[0]},{core[1]}", tid=role, args=dict(launch=i)))
  Path(path).write_text(json.dumps(dict(traceEvents=ev, displayTimeUnit="ns")))
  print(f"wrote {len(ev)} spans to {path} (open in ui.perfetto.dev)")

def main():
  ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
  ap.add_argument("--model", default="1b", choices=list(llama3.MODELS))
  ap.add_argument("--device", type=int, default=0)
  ap.add_argument("--tokens", type=int, default=3, help="decode positions to record (ring holds ~4 tokens on 1B/8B)")
  ap.add_argument("--trace", help="write a Chrome/Perfetto trace JSON here")
  ap.add_argument("--json", help="write raw spans here")
  a = ap.parse_args()
  model = ProfiledLlama3(a.model, a.device, profile=True)
  try:
    ids = ChatTokenizer(model.checkpoint).chat([{"role": "user", "content": "Write a story about a robot learning to paint."}])
    gen, _ = model.generate(ids, a.tokens + 1)  # warm up, and fill the KV cache for the recorded positions
    model.arm()
    gen2, s = model.generate(ids, a.tokens, start=len(ids) - 1)
    assert gen2 == gen[:a.tokens], "profiled run generated different tokens"
    events, lost = model.collect()
    print(f"dropped {model.duplicates} duplicated stamps (hardware store replay)")
    if lost: print(f"WARNING: timestamp ring full/overflow on {len(lost)} cores: {lost[:5]}")
    n = a.tokens  # positions run: len(ids)-1 .. len(ids)-2+tokens
    spans, seq, problems = align(model, events, n)
    if problems: print("alignment problems:", dict(problems))
    disp = model._timestamps(model.ts_base, len(ids) - 1 + n)[len(ids) - 1:]
    print(f"{MODEL_NAME(a.model)}: {len(spans)} RISC spans over {n} positions, {sum(map(len, events.values()))} events; "
          f"decode {s['period_us'] / 1e3:.3f} ms/token while profiling")
    report(model, spans, seq, disp, n)
    if a.trace: chrome_trace(spans, seq, a.trace, int(disp[0, 0]))
    if a.json: Path(a.json).write_text(json.dumps([[i, list(c), r, s_, e_] for (i, c, r), (s_, e_) in spans.items()]))
  finally:
    model.close()

def MODEL_NAME(k): return llama3.MODELS[k]

if __name__ == "__main__": main()
