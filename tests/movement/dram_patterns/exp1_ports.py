"""E1: per-port and per-controller ceilings.
For each bank: 12 workers hit that single bank. Variants: one port (p0/p1/p2),
all 3 ports spread. Read / write, both RISCs (NoC0 + NoC1)."""
import sys, json
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from dramx import Bench, ep

dev = int(sys.argv[1]); banks = [int(x) for x in sys.argv[2].split(',')]
out = sys.argv[3]
b = Bench(dev)
PER = 1 << 20  # bytes per stream
NW = 12
rows = []
try:
  base = b.region(PER * NW * 2)
  for bank in banks:
    for direction in ('read', 'write'):
      for ports in ((0,), (1,), (2,), (0, 1, 2)):
        for noc_mode in ('noc0', 'noc1', 'both'):
          plan = {}
          k = 0
          for i, core in enumerate(b.cores[:NW]):
            ss = []
            slots = {'noc0': [(0, 0)], 'noc1': [(1, 1)], 'both': [(0, 0), (1, 1)]}[noc_mode]
            for slot, noc in slots:
              port = ports[k % len(ports)]
              ss.append(dict(slot=slot, dir=direction, noc=noc, coords=[ep(bank, port)],
                             addr=base + k * PER, bytes=PER))
              k += 1
            plan[core] = ss
          rows.append(b.run(plan, label=dict(bank=bank, dir=direction, ports=ports, noc=noc_mode)))
          json.dump(rows, open(out, 'w'), indent=1)
finally:
  b.close()
