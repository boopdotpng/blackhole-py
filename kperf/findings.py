"""Rules that turn a kperf bundle into sentences. Each finding: kind, title, detail, and est_us (time it plausibly costs
per launch; None when it is a diagnosis rather than a cost)."""
from collections import Counter
import numpy as np
from kperf.bundle import lane_kinds

def _share(bundle, lane):
  """lane -> Counter(kind -> samples) over all cores and bins."""
  return Counter(lane_kinds(bundle, lane))

def findings(b):
  out = []
  med = b["launch"]["median"]
  tot = np.array(b["dram"]["total"]); banks = np.array(b["dram"]["banks"]); db = b["dram_bin_us"]
  n = min(len(tot), int(med / db))
  if n >= 8:
    steady = float(np.median(tot[n // 4: 3 * n // 4]))
    lost = float(np.clip(steady - tot[:n], 0, None).sum() * db / max(steady, 1))
    dip = int(np.argmin(tot[: max(2, n // 4)]))  # bin 0 can hold the previous launch's in-flight tail
    up = next((i for i in range(dip, n) if tot[i] >= 0.9 * steady), n) * db
    down = next((i for i in range(n - 1, -1, -1) if tot[i] >= 0.9 * steady), 0) * db
    out.append(dict(kind="dram", est_us=round(lost, 2),
      title=f"DRAM runs below its steady {steady:.0f} GB/s for {lost:.1f} µs of a {med:.1f} µs launch",
      detail=f"Reaches 90% of steady bandwidth {up:.1f} µs after launch start and falls below it at {down:.1f} µs. "
             f"Steady state is {steady / b['pin_gbs']:.0%} of the {b['pin_gbs']} GB/s pin rate."))
    q = banks[: max(2, n // 4)].mean(0)
    hot = [i for i in range(8) if q[i] > 2 * np.median(q) and q[i] > 30]
    if hot:
      rest = np.mean([q[i] for i in range(8) if i not in hot])
      out.append(dict(kind="dram", est_us=None,
        title=f"Hot spot: bank{'s' if len(hot) > 1 else ''} {', '.join(map(str, hot))} saturated in the first quarter of the launch",
        detail=f"Bank{'s' if len(hot) > 1 else ''} {', '.join(map(str, hot))} average {np.mean(q[hot]):.0f} GB/s while the other "
               f"banks average {rest:.0f} GB/s. Every core is probably reading the same small buffer (activation, residual, "
               f"gamma) at once; replicating it across banks or multicasting it would spread the load."))
  if n >= 8 and "ports" in b["dram"]:
    P = np.array(b["dram"]["ports"])[:n]; meta = b["dram"]["port_meta"]
    per = P.mean(0)                                   # GB/s per (port, NoC) counter, over the launch
    tile = {}
    for j, mm in enumerate(meta): tile[(mm["bank"], mm["port"])] = tile.get((mm["bank"], mm["port"]), 0) + per[j]
    used = [k for k, v in tile.items() if v > 1.0]
    noc = [sum(per[j] for j, mm in enumerate(meta) if mm["noc"] == q) for q in (0, 1)]
    shares = sorted(((v / max(sum(tile[(bk, p)] for p in range(3)), 1e-9), bk, p) for (bk, p), v in tile.items()), reverse=True)
    top = max(tile.values())
    out.append(dict(kind="dram", est_us=None,
      title=f"{len(used)} of 24 DRAM ports carry traffic; NoC0 {noc[0] / max(sum(noc), 1e-9):.0%}, NoC1 {noc[1] / max(sum(noc), 1e-9):.0%}",
      detail="Per bank, share of reads by port (0/1/2): " + "; ".join(
        f"bank {bk} " + "/".join(f"{tile[(bk, p)] / max(sum(tile[(bk, q)] for q in range(3)), 1e-9):.0%}" for p in range(3)) for bk in range(8)) +
        f". Busiest single port averages {top:.0f} GB/s (a controller's pin rate is 64.3)."))
  cs = b["core_stats"]
  if cs:
    fin = {k: v["finish"] for k, v in cs.items()}
    slow, fast = max(fin, key=fin.get), min(fin, key=fin.get)
    xs = sorted({int(k.split(",")[0]) for k in fin}); mx = xs[len(xs) // 2]
    left = np.mean([v for k, v in fin.items() if int(k.split(",")[0]) < mx])
    right = np.mean([v for k, v in fin.items() if int(k.split(",")[0]) >= mx])
    spread = fin[slow] - fin[fast]
    if spread > 0.05 * med:
      out.append(dict(kind="balance", est_us=round(fin[slow] - float(np.mean(list(fin.values()))), 2),
        title=f"Cores finish {spread:.1f} µs apart (fastest {fast}, slowest {slow})",
        detail=f"Mean core finishes at {np.mean(list(fin.values())):.1f} µs, the slowest at {fin[slow]:.1f} µs. "
               f"Columns x<{mx} average {left:.1f} µs, x≥{mx} average {right:.1f} µs" +
               (" — a left/right split, e.g. different NoC routes or DRAM ports per half." if abs(left - right) > 0.1 * med else ".")))
    last = Counter()
    for v in cs.values(): last[max(v["roles"], key=lambda r: v["roles"][r][1])] += 1
    role, cnt = last.most_common(1)[0]
    gaps = [v["roles"][role][1] - max(e for r, (s, e) in v["roles"].items() if r != role) for v in cs.values() if len(v["roles"]) > 1]
    if gaps and cnt > 0.6 * len(cs):
      out.append(dict(kind="tail", est_us=round(float(np.median(gaps)), 2),
        title=f"{role.upper()} finishes last on {cnt / len(cs):.0%} of cores, {np.median(gaps):.1f} µs after the other RISCs",
        detail=f"Whatever {role.upper()} does after the others are done (epilogue, output writes) is on the critical path."))
    out.append(dict(kind="tail", est_us=round(med - fin[slow], 2),
      title=f"{med - fin[slow]:.1f} µs from the slowest core's last RISC to the dispatcher's done",
      detail="Done-count atomics, dispatch bookkeeping and the next GO; per-launch fixed cost outside the kernels."))
  names = b["kinds"]
  for lane, rule in (("brisc", 1), ("trisc0", 2), ("T1 math", 7), ("T0 unpack", None)):
    s = _share(b, lane); total = sum(s.values())
    if not total: continue
    if rule is not None and s[rule] / total > 0.4:
      what = {1: "waiting for DRAM/NoC reads — the reader is bandwidth- or latency-bound",
              2: "waiting for its input CB — it is starved by the RISC that fills it",
              7: "stalled on math issue — the FPU is starved of SrcA/SrcB (unpack/feeder bound)"}[rule]
      out.append(dict(kind="pipeline", est_us=None, title=f"{lane} spends {s[rule] / total:.0%} of its time {what.split(' — ')[0]}",
                      detail=what.split(" — ")[1] if " — " in what else what))
    if lane == "T0 unpack":
      busy = (s[5] + s[6] + s[7]) / total
      if busy < 0.3:
        out.append(dict(kind="pipeline", est_us=None, title=f"Unpacker hardware is busy only {busy:.0%} of the time",
          detail="The T0 thread mostly has nothing queued: the TRISC0 RISC-side loop (CB polling, address setup), not the "
                 "unpack engine, sets the pace."))
  return out
