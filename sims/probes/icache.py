"""Instruction-cache cost (k_icache.c), port of the old test_icache.py: a straight-line body of N instructions in a
counted loop, timed at 4, 8 and 16 passes; steady cost per pass from the slopes, cold first pass from the intercept.
Per role and body kind: addi on all five RISCs, SFPNOP (.ttinsn) on trisc1, TTNOP (.ttinsn) on trisc0.

  python3 sims/probes/run.py --device 1 --output sims/results/<date>-icache-card1.jsonl icache

Prefetch is the firmware's (reset_tensix writes 0x11F after every launch, as the old run re-applied by hand); the
value in effect is recorded per case (not readable on NCRISC). 'expect' holds the 2026-11-18 results per card.
"""
import json
from pathlib import Path
from statistics import median
from struct import unpack

from tile import LAYOUT, build

TILE = (1, 2)
RESULTS = Path(__file__).resolve().parents[1] / 'results'
PASSES = (4, 8, 16)
SIZES = (32, 64, 96, 120, 128, 160, 256, 480, 512, 1024)
KINDS = {'addi': 0, 'sfpnop': 1, 'ttnop': 2}
ROLES = [(r, 'addi') for r in ('brisc', 'ncrisc', 'trisc0', 'trisc1', 'trisc2')] + [('trisc1', 'sfpnop'), ('trisc0', 'ttnop')]
LAUNCHES = 6  # per point; the first is discarded


def _expect():
  out = {}
  for card in (0, 1):
    p = RESULTS / f'2026-11-18-icache-card{card}.jsonl'
    for r in (json.loads(line) for line in (p.read_text().splitlines() if p.exists() else ()) if line.strip()):
      out.setdefault((r['role'], r['kind'], r['n']), {})[f'card{card}'] = dict(
        steady_per_pass=r['steady_per_pass'], steady_per_insn=r['steady_per_insn'], first_pass=r['first_pass'],
        cold_extra=r['cold_extra'], medians=[pt['median'] for pt in r['points']])
  return out


EXPECT = _expect()
CASES = [dict(id=f'icache-{role}-{kind}-n{n}', role=role, kind=kind, n=n, expect=EXPECT.get((role, kind, n)),
              tiles=[TILE]) for role, kind in ROLES for n in SIZES]


def image(role, kind, n):
  extra = dict(NO_TENSIX_CFG=1) if role == 'ncrisc' else {}
  return build('k_icache.c', role, KIND=KINDS[kind], N=n, **extra)


def run(card, case, timeout):
  role, kind, n = case['role'], case['kind'], case['n']
  img, pts = image(role, kind, n), []
  for passes in PASSES:
    s = []
    for _ in range(LAUNCHES):
      card.run([(TILE, {role: img}, {role: [passes]}, None)], timeout)
      t0, t1 = unpack('<2I', card.iface.read(TILE, LAYOUT[role]['log'] + 0xFC0, 8))  # PROF0/PROF1 (sfpu.h)
      s.append((t1 - t0) & 0xFFFFFFFF)
    pts.append(dict(passes=passes, median=median(s[1:]), raw=s[1:]))
  steady = [(b['median'] - a['median']) / (b['passes'] - a['passes']) for a, b in zip(pts, pts[1:])]
  first = pts[0]['median'] - steady[0] * (pts[0]['passes'] - 1)
  a = card.aux(TILE, 5, role)
  cfg = dict(cfg0=hex(a[0]), prefetch=None if role == 'ncrisc' else hex(a[2]))
  want = (case.get('expect') or {}).get(f'card{card.index}')
  match = None if want is None else all(abs(x - y) <= max(2.0, 0.015 * y) for x, y in
                                         zip([p['median'] for p in pts], want['medians']))
  return dict(steady_per_pass=steady, steady_per_insn=steady[-1] / (n + 2), first_pass=first,
              cold_extra=first - steady[-1], points=pts, cfg=cfg, match=match)
