"""PC -> code region, named with kview's annotated disassembly, and classified into a few phase kinds."""
import re, sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "kview"):
  if str(p) not in sys.path: sys.path.insert(0, str(p))
import decode as kview

# Phase kinds: index = categorical palette slot (fixed order, see static/style.css). IDLE is neutral, not a slot.
KINDS = ["compute / issue loop", "wait: DRAM / NoC", "wait: CB (other RISC)", "wait: sync / semaphore", "setup code",
         "Tensix: busy, not stalled", "Tensix: stalled (other)", "Tensix: stalled on math"]
IDLE = len(KINDS)  # firmware, between launches, nothing busy
STALL_BITS = [(0x2000000, "math"), (0x40000, "sfpu"), (0xC000000, "unpack"), (0x10000000, "pack"), (0x1000000, "tdma"),
              (0x100000, "sync"), (0x80000, "cfg"), (0x200000, "thcon"), (0x800000, "move")]
BUSY_BITS = [(0x30, "unpacker"), (0x40, "packer"), (0xF80, "tdma"), (0x8, "thcon"), (0x4, "mover")]

def thread_state(word:int):
  """Tensix frontend debug word of one thread -> (label, kind)."""
  stalled = [n for b, n in STALL_BITS if word & b]
  if stalled: return "stalled on " + "+".join(stalled), 7 if stalled == ["math"] else 6
  busy = [n for b, n in BUSY_BITS if word & b]
  return ("busy: " + "+".join(busy), 5) if busy else ("idle", IDLE)

def _clean(s): return re.sub(r"[;\n]", ",", s)

class Symbolizer:
  def __init__(self, kdir, manifest):
    self.kdir, self.m = Path(kdir), manifest

  def file(self, program, role, variant): return Path(self.m["programs"][program]["files"][role][variant]).stem

  @lru_cache(maxsize=None)
  def image(self, program, role, variant):
    rel = self.m["programs"][program]["files"][role][variant]
    d = kview.disassemble((self.kdir / rel).read_bytes(), kview.Context(role, self.m, program, kview.ABI))
    rows = {r["pc"]: r for r in d["rows"]}
    loops = sorted(((r["target"], r["pc"]) for r in d["rows"] if isinstance(r.get("target"), int) and r["target"] <= r["pc"]
                    and not r.get("call")), key=lambda l: l[1] - l[0])
    return rows, loops, {f["pc"]: f for f in d["funcs"]}

  @staticmethod
  def _insn(row):
    if row is None: return "?"
    ann = next((a for a in row.get("ann", ()) if a[0] in ("load", "store", "gist")), None)
    return _clean(f"{row.get('op', '?')}" + (f" {'<-' if ann[0] == 'load' else '->' if ann[0] == 'store' else ''} {ann[1]}" if ann else ""))[:90]

  @lru_cache(maxsize=None)
  def region(self, program, role, variant, off):
    """-> (label, kind, region start pc, instruction text)"""
    rows, loops, funcs = self.image(program, role, variant)
    pc = off & ~3
    row = rows.get(pc)
    fn = row.get("fn") if row else None
    fname = _clean(f"{funcs[fn]['name']} {funcs[fn]['title']}")[:70] if fn not in (None, 0) and fn in funcs else ""
    loop = next(((a, b) for a, b in loops if a <= pc <= b), None)
    if loop:
      a, b = loop
      polls = [rows[p] for p in range(a, b + 4, 4) if p in rows and any(n[0] == "load" for n in rows[p].get("ann", ()))]
      if b - a <= 40 and polls:
        what = self._insn(polls[0])
        label = f"wait @{a:#x}: {what}"
        text = f"{fname} {what}".lower()
        kind = 1 if ("noc" in text or "tid" in text or "niu" in text) else 2 if "cb" in text else 3
      else:
        label, kind = f"loop @{a:#x}-{b:#x} ({(b - a) // 4 + 1} instrs)", 0
        if "wait until noc" in fname.lower(): kind = 1
      start = a
    else:
      label, kind, start = "straight-line code", 4, pc
    if fname: label = f"{fname} / {label}"
    return label[:140], kind, start, f"{pc:#06x} {self._insn(row)}"
