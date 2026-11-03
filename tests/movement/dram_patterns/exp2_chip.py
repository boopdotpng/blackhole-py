"""E2: full-chip patterns. 117 workers x (BRISC, NCRISC) streams.
noc policy:
  alt        : baseline -- core i%2 picks which slot uses noc0 (same as repo bench)
  r0w1       : reads on NoC0, writes on NoC1 (theory: avoids DRAM-column Y legs)
  r1w0       : anti (reads NoC1, writes NoC0)
port policy:
  table      : repo table (bank's fixed port per noc)
  spread     : stream k uses port (k + bank) % 3 for each bank -> all 24 ports used
  p0/p1/p2   : one fixed port index for all
direction: read / write / mixed (slot0 read, slot1 write; for 'alt' slot0 noc alternates)
"""
import sys, json, itertools
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from dramx import Bench, ep
from pcie import P150_DRAM_ENDPOINTS as TABLE

dev = int(sys.argv[1]); out = sys.argv[2]
cases = json.loads(sys.argv[3])  # list of [dir, nocpol, portpol, posted]
NCORE = int(sys.argv[4]) if len(sys.argv) > 4 else 117
PER = int(sys.argv[5]) if len(sys.argv) > 5 else 2 << 20
b = Bench(dev)
rows = []


def coords(bank_list, noc, portpol, k):
  r = []
  for bk in bank_list:
    if portpol == 'table':
      r.append(TABLE[bk][noc])
    elif portpol == 'spread':
      r.append(ep(bk, (k + bk) % 3))
    else:
      r.append(ep(bk, int(portpol[1])))
  return r


try:
  base = b.region(PER * NCORE * 2 // 8 + (1 << 20))
  for direction, nocpol, portpol, posted in cases:
    plan = {}
    k = 0
    for i, core in enumerate(b.cores[:NCORE]):
      ss = []
      for slot in (0, 1):
        d = direction if direction != 'mixed' else ('read' if slot == 0 else 'write')
        if nocpol == 'alt':
          noc = (i + slot) % 2
        elif nocpol == 'r0w1':
          noc = 0 if d == 'read' else 1
        elif nocpol == 'r1w0':
          noc = 1 if d == 'read' else 0
        elif nocpol == 'slot':
          noc = slot
        rot = k % 8
        banks = list(range(8))[rot:] + list(range(8))[:rot]
        ss.append(dict(slot=slot, dir=d, noc=noc, coords=coords(banks, noc, portpol, k),
                       addr=base + k * PER // 8, bytes=PER, posted=posted, tag=f'{d}'))
        k += 1
      plan[core] = ss
    rows.append(b.run(plan, label=dict(dir=direction, noc=nocpol, ports=portpol, posted=posted, cores=NCORE)))
    json.dump(rows, open(out, 'w'), indent=1)
finally:
  b.close()
