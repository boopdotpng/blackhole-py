"""Static census of synchronization in the exported decode kernels.

Parses kernels/<model>/<kernel>/<risc>.S listings (one instruction per line, branch targets resolved) and classifies
every instruction that waits on, or signals, another agent: Tensix STALLWAIT/SEM*, source-bank releases (SETRWC
clear_ab_vld, including inside MOP templates), RISC-side Tensix drains (PC_BUF_SYNC / MOP_SYNC), semaphore polls,
CB-counter polls/publishes, NoC polls and L1 flag spins.

Loops are found from backward branches. Each sync site is reported with its loop depth, so per-tile / per-row costs
are visible. Polling loops (a short backward branch around one load) are reported as one "spin" site, not a loop.

  python sync/census.py                 # summary table, all models
  python sync/census.py 8b-fp8 gate     # site listing for one kernel
"""
import re, sys, json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KERNELS = ROOT / "kernels"
LINE = re.compile(r"^\s+([0-9a-f]+): ([0-9a-f]{8})  (\S+)\s*(.*)$")
TARGET = re.compile(r"target 0x([0-9a-f]+)")
BRANCH = {"beq", "bne", "blt", "bge", "bltu", "bgeu", "jal"}

def parse(path):
  insns = []
  for line in path.read_text().splitlines():
    m = LINE.match(line)
    if not m: continue
    pc, word, mn, rest = int(m[1], 16), m[2], m[3], m[4]
    t = TARGET.search(rest)
    insns.append(dict(pc=pc, word=word, mn=mn, rest=rest, target=int(t[1], 16) if t else None))
  return insns

def loops(insns):
  """Backward branches -> (start, end) ranges. A spin is a loop of <= 12 insns containing a load and no Tensix op."""
  out = []
  for i in insns:
    if i["mn"] in BRANCH and i["target"] is not None and i["target"] <= i["pc"]:
      body = [x for x in insns if i["target"] <= x["pc"] <= i["pc"]]
      spin = len(body) <= 12 and any(x["mn"] in ("lw", "lhu", "lbu", "lh", "lb") for x in body) \
             and not any(x["mn"].isupper() for x in body)
      out.append(dict(start=i["target"], end=i["pc"], spin=spin, body=body))
  return out

def depth(pc, ls): return sum(1 for l in ls if not l["spin"] and l["start"] <= pc <= l["end"])

def spin_kind(body):
  text = " ".join(x["rest"] for x in body)
  if "PC_BUF" in text and "MOP" in text: return "risc:mop_sync"
  if "UNPACK_CONFIG_SYNC" in text or "0xffe80034" in text: return "risc:sem_poll(UNPACK_SYNC)"
  m = re.search(r"0xffe800([23][0-9a-f])", text)
  if m: return f"risc:sem_poll(pc_buf+0x{m[1]})"
  if "0xffb48028" in text or re.search(r"0xffb4[89a-f][0-9a-f]028", text): return "risc:cb_wait_front(received)"
  if "0xffb48020" in text or re.search(r"0xffb4[89a-f][0-9a-f]020", text): return "risc:cb_reserve_back(acked)"
  if re.search(r"0xffb4[0-9a-f]{4}", text): return "risc:cb_poll"
  if "noc" in text.lower() or "0xffb2" in text or "0xffb3" in text: return "risc:noc_poll"
  return "risc:l1_flag_spin"

def classify(i):
  """Non-spin sync sites. Returns a list of kinds (MOP-config stores may carry a template op)."""
  mn, rest = i["mn"], i["rest"]
  kinds = []
  if mn == "STALLWAIT":
    m = re.search(r"stall_res: ([^;]+); wait_res: ([^#]+?)(?:$|  #|;)", rest)
    kinds.append(f"tt:STALLWAIT[{m[1].replace('Stall.', '').replace(' ', '')}<-{m[2].replace('Wait.', '').replace(' ', '').strip()}]" if m else "tt:STALLWAIT")
  elif mn in ("SEMWAIT", "SEMPOST", "SEMGET", "SEMINIT"):
    m = re.search(r"sem_sel: Sem\.(\w+)", rest)
    kinds.append(f"tt:{mn}[{m[1] if m else '?'}]")
  elif mn == "SETRWC" and re.search(r"clear_ab_vld=[123]", rest):
    kinds.append("tt:SETRWC.clear_ab_vld")
  elif mn in ("SETDVALID", "CLEARDVALID", "ATGETM", "ATRELM", "STREAMWAIT"):
    kinds.append(f"tt:{mn}")
  elif mn == "ZEROACC":
    kinds.append("tt:ZEROACC")
  elif mn in ("ELWMUL", "ELWADD", "ELWSUB", "MVMUL", "MOVA2D", "MOVB2D", "GMPOOL", "GAPOOL") and re.search(r"clear_dvalid=[123]", rest):
    kinds.append("tt:FPU.clear_dvalid")
  if "MOP template instruction" in rest:
    t = rest.split("MOP template instruction · ", 1)[1]
    if re.search(r"SETRWC clear_ab_vld=[123]", t): kinds.append("tpl:SETRWC.clear_ab_vld")
    if re.search(r"^(ELWMUL|ELWADD|ELWSUB|MVMUL|MOVA2D)\b.*clear_dvalid=[123]", t): kinds.append("tpl:FPU.clear_dvalid")
    if t.startswith("UNPACR") and re.search(r"SetDatValid=1|set_dat_valid=1|Set_DVALID=1|SetDvalid=1", t, re.I): kinds.append("tpl:UNPACR.set_dvalid")
  if mn == "sw" and "PC_BUF_SYNC" in rest: kinds.append("risc:tensix_drain(PC_BUF_SYNC)")
  if mn == "sw" and "PC_BUF_MOP_SYNC" in rest: kinds.append("risc:mop_drain(PC_BUF_MOP_SYNC)")
  if mn == "sw" and ("UNPACK_CONFIG_SYNC" in rest or "0xffe80034" in rest): kinds.append("risc:sem_post(UNPACK_SYNC)")
  if mn in ("sw", "sh") and re.search(r"0xffb4[89a-f][0-9a-f]0(20|28)", rest): kinds.append("risc:cb_publish")
  if mn == "fence": kinds.append("risc:fence")
  return kinds

def census(path):
  insns = parse(path)
  ls = loops(insns)
  spins = [l for l in ls if l["spin"]]
  in_spin = {x["pc"] for l in spins for x in l["body"]}
  sites = []
  for i in insns:
    for k in classify(i):
      if k == "risc:fence" and i["pc"] in in_spin: continue  # part of a spin
      sites.append((i["pc"], depth(i["pc"], ls), k))
  for l in spins: sites.append((l["start"], depth(l["start"], ls), spin_kind(l["body"])))
  return sorted(sites), len(insns), max((depth(i["pc"], ls) for i in insns), default=0)

def models(): return sorted(p.name.removeprefix("llama3-") for p in KERNELS.glob("llama3-*"))

def summary(model):
  rows = []
  for kdir in sorted((KERNELS / f"llama3-{model}").iterdir()):
    if not kdir.is_dir(): continue
    for s in sorted(kdir.glob("*.S")):
      sites, n, _ = census(s)
      c = Counter(k for _, _, k in sites)
      tt = sum(v for k, v in c.items() if k.startswith(("tt:", "tpl:")))
      risc = sum(v for k, v in c.items() if k.startswith("risc:"))
      rows.append((kdir.name, s.stem, n, tt, risc, c))
  return rows

def main():
  if len(sys.argv) >= 3:
    model, kernel = sys.argv[1], sys.argv[2]
    for s in sorted((KERNELS / f"llama3-{model}" / kernel).glob("*.S")):
      sites, n, d = census(s)
      print(f"\n== {kernel}/{s.name}: {n} insns, max loop depth {d}")
      for pc, dep, k in sites: print(f"  {pc:5x}  {'  ' * dep}d{dep} {k}")
    return
  out = {}
  for model in (sys.argv[1:] or models()):
    rows = summary(model)
    out[model] = [dict(kernel=k, risc=r, insns=n, tensix_sync=tt, risc_sync=rs, kinds=dict(c)) for k, r, n, tt, rs, c in rows]
    print(f"\n### llama3-{model}\n")
    print(f"{'kernel':<16}{'risc':<10}{'insns':>6}{'tensix':>8}{'risc':>6}  top kinds")
    tot = Counter()
    for k, r, n, tt, rs, c in rows:
      tot.update(c)
      top = ", ".join(f"{x.split(':', 1)[1]}×{v}" for x, v in c.most_common(4))
      print(f"{k:<16}{r:<10}{n:>6}{tt:>8}{rs:>6}  {top}")
    print("\nall kernels, by kind:")
    for x, v in sorted(tot.items(), key=lambda kv: -kv[1]): print(f"  {v:5d}  {x}")
  (Path(__file__).parent / "census.json").write_text(json.dumps(out, indent=1))

if __name__ == "__main__": main()
