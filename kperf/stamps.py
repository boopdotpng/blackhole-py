"""Per-RISC kernel spans from the Tensix hardware debug timestamper.

Every kernel image gets a 16-byte prologue and epilogue that each store one token to RISCV_DEBUG_REG_TIMESTAMP
(0xFFB121FC). The hardware appends {token, 64-bit wall clock} as one atomic 16-byte write to a ring in L1, so all five
RISCs of a core share one stream without locking. Kernels are position-independent and get their return jump appended
at install anyway, so no regeneration is needed.

Measured: one store is sometimes recorded 2-4 times, 2 cycles apart (store replay around kernel entry/exit), so
collect() drops repeats of the same token within 64 cycles.
"""
import struct, sys
from collections import Counter
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
import fw
from llama3 import Llama3

TS_CMD, TS_CNTL, TS_STATUS, TS_B0_START, TS_B0_END = 0xFFB121FC, 0xFFB12200, 0xFFB12204, 0xFFB12208, 0xFFB1220C
RING, RING_SIZE = 0x100000, 0x80000  # measured: no Llama kernel writes worker L1 above 0xC0000
PROLOGUE = 16

def token(prog:int, role:int, end:bool) -> int:  # 128-bit event (low 3 bits 0); fits addi's 12-bit immediate
  t = prog << 7 | role << 4 | int(end) << 3
  assert 0 <= t < 2048
  return t

def stamp(tok:int) -> bytes:  # lui t0, 0xFFB12 ; addi t1, zero, tok ; sw t1, 0x1FC(t0) ; nop
  return struct.pack("<4I", 0xFFB12 << 12 | 5 << 7 | 0x37, tok << 20 | 6 << 7 | 0x13,
                     (0x1FC >> 5) << 25 | 6 << 20 | 5 << 15 | 2 << 12 | (0x1FC & 31) << 7 | 0x23, 0x13)

def wrap(image:bytes, role:str, prog:int) -> bytes:
  r = fw.ROLES.index(role)
  return stamp(token(prog, r, False)) + image + stamp(token(prog, r, True))

class ProfiledLlama3(Llama3):
  """Llama3 whose installed kernel images carry timestamper stamps."""
  def _install(self):
    self.prog_ids = {n: i for i, n in enumerate(self.m["programs"])}
    orig_read = Path.read_bytes
    def read_bytes(p):  # _install reads kernels/<model>/<program>/<role>[.vN].bin
      data = orig_read(p)
      role = p.name.split(".")[0]
      if p.suffix == ".bin" and p.parent.parent == self.kdir and p.parent.name in self.prog_ids and role in fw.ROLES:
        data = wrap(data, role, self.prog_ids[p.parent.name])
        assert len(data) + 4 <= fw.CODE_SIZE[role], (p, len(data))
      return data
    Path.read_bytes = read_bytes
    try: super()._install()
    finally: Path.read_bytes = orig_read
    self.runs = {n: {(tuple(c["core"]), role) for c in p["per_core"] for role, v in zip(self.m["roles"], c["variants"]) if v >= 0}
                 for n, p in self.m["programs"].items()}

  def arm(self):
    io = self.dev.iface
    for c in self.dev.workers:
      io.write32(c, TS_CNTL, 1 << 31 | 1); io.write32(c, TS_CNTL, 1)  # pulse reset_streams; buffer 0 valid
      io.write32(c, TS_STATUS, 0x33)                                   # clear full/overflow, position 0
      io.write32(c, TS_B0_START, RING // 16); io.write32(c, TS_B0_END, (RING + RING_SIZE) // 16 - 1)

  def collect(self, cores=None):
    """-> ({core: [(token, t)]}, cores whose ring overflowed, duplicates dropped)"""
    io, events, lost, dups = self.dev.iface, {}, [], 0
    for c in cores or self.dev.workers:
      st = io.read32(c, TS_STATUS)
      if st & 0x11: lost.append(c)
      pos = st >> 14
      raw = np.frombuffer(io.read(c, RING, pos * 16), "<u4").reshape(-1, 4) if pos else np.zeros((0, 4), "<u4")
      evs, last = [], {}
      for h, lo, hi, _ in raw:
        h, t = int(h), int(lo) | int(hi) << 32
        if h in last and t - last[h] < 64: dups += 1; continue
        last[h] = t; evs.append((h, t))
      events[c] = evs
    return events, lost, dups

def align(model, events, seq):
  """seq: program name of each launch, in order. -> ({(launch, core, role): (start, end)}, problems).
  The k-th start of program P by (core, role) is the k-th launch of P that (core, role) takes part in."""
  names = {i: n for n, i in model.prog_ids.items()}
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
      for i, s, e in zip(mine, starts, ends):
        if s[1] != seq[i] or e[1] != seq[i]: problems["program order mismatch"] += 1; continue
        out[(i, core, role)] = (s[0], e[0])
  return out, problems
