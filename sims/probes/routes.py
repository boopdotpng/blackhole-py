"""Does the NoC route the way the link-load model says, and is the NoC1 DRAM read collapse really link contention?

route  Two tile-to-tile read flows (reader R_i reads 8 KiB pages from source S_i's L1, uncapped, synchronized start).
       Each pair is chosen so the hypotheses disagree on whether the two response paths (S -> R, which carry the data)
       share a directed link: NoC0 x-first vs y-first, NoC1 y-first ("mirror of NoC0") vs x-first. Sharing a
       ~61 B/c link should give ~30 B/c per flow; no sharing ~60.
dcol   8 cores, one per row 2..9 and each in its own column, each streaming 8 KiB reads from ONE DRAM endpoint in the
       x = 0 DRAM column (physical): either the endpoint in the core's own row (no vertical segment in the DRAM
       column on NoC1) or the one 4 rows below (NoC1 responses climb 4 rows inside the column, overlapping 4 deep;
       NoC0 responses run along the endpoint's row, then down the core's own column, so they don't overlap).
       If the column funnel is the cause: same-row fast on both NoCs, offset slow on NoC1 only.
"""
import itertools, random
from statistics import median

import traffic
from traffic import sw, region

X, Y = 17, 12
SOC = [[0, 1, 11], [2, 10, 3], [9, 4, 8], [5, 7, 6]]  # physical y of DRAM (bank % 4, port k): tt-umd blackhole soc desc
WORKERS = [(x, y) for x in (1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14, 15, 16) for y in range(2, 12)]


def _walk(a, b, order, dx, dy):
  (x, y), out = a, []
  for axis in order:
    while (x, y)[axis] != b[axis]:
      if axis == 0: out.append(((x, y), 'x', dx)); x = (x + dx) % X
      else: out.append(((x, y), 'y', dy)); y = (y + dy) % Y
  return set(out)


MODELS = {  # response path S -> R under each hypothesis (directed links as (from-node, axis, direction))
  'noc0_xfirst': lambda a, b: _walk(a, b, (0, 1), 1, 1),
  'noc0_yfirst': lambda a, b: _walk(a, b, (1, 0), 1, 1),
  'noc1_yfirst': lambda a, b: _walk(a, b, (1, 0), -1, -1),
  'noc1_xfirst': lambda a, b: _walk(a, b, (0, 1), -1, -1),
}


def dram_endpoint(phys_y, column=0):
  """Translated coordinate of the DRAM endpoint at physical (0 or 9, phys_y)."""
  for b4, ks in enumerate(SOC):
    if phys_y in ks: return (17 + column, 12 + 3 * b4 + ks.index(phys_y))
  raise ValueError(phys_y)


def _route_pairs():
  rng, out = random.Random(7), []
  wanted = {(0, 'noc0_xfirst', 'noc0_yfirst', True): 3, (0, 'noc0_xfirst', 'noc0_yfirst', False): 3,
            (1, 'noc1_yfirst', 'noc1_xfirst', True): 3, (1, 'noc1_yfirst', 'noc1_xfirst', False): 3}
  while any(wanted.values()):
    t = rng.sample(WORKERS, 4)
    s1, r1, s2, r2 = t
    for (noc, h, alt, share), n in wanted.items():
      if not n: continue
      a = bool(MODELS[h](s1, r1) & MODELS[h](s2, r2))
      b = bool(MODELS[alt](s1, r1) & MODELS[alt](s2, r2))
      if a == share and b != share:
        out.append(dict(noc=noc, flows=[(s1, r1), (s2, r2)], predict={h: a, alt: b}))
        wanted[noc, h, alt, share] -= 1
        break
  return out


DCOL = [(x, y) for x, y in zip((1, 2, 3, 4, 5, 6, 7, 10), range(2, 10))]


def _cases():
  for i, p in enumerate(_route_pairs()):
    yield dict(id=f'route-noc{p["noc"]}-{i}', group='route', **p, tiles=[t for f in p['flows'] for t in f])
  for noc in (0, 1):
    yield dict(id=f'dcol-solo-noc{noc}', group='dcol', noc=noc, offset=0, cores=DCOL[:1], tiles=DCOL[:1])
    for off in (0, 4):
      yield dict(id=f'dcol-off{off}-noc{noc}', group='dcol', noc=noc, offset=off, cores=DCOL, tiles=DCOL)


# dcol2: (core, physical DRAM endpoint) lists, all endpoints in the x = 0 column, one bank per core unless noted.
DCOL2 = {
  'samerow-4banks': [((2, 11), (0, 11)), ((3, 10), (0, 10)), ((4, 9), (0, 9)), ((5, 7), (0, 7))],
  'row2-4banks':    [((2, 2), (0, 11)), ((3, 2), (0, 10)), ((4, 2), (0, 9)), ((5, 2), (0, 7))],
  'samebank-2ports': [((2, 11), (0, 11)), ((3, 2), (0, 1))],  # bank 0 via two of its ports
  'diffbank-2':      [((2, 11), (0, 11)), ((3, 10), (0, 10))],
}


def _cases2():
  for name in DCOL2:
    for noc in (0, 1):
      cores = [c for c, _ in DCOL2[name]]
      yield dict(id=f'dcol2-{name}-noc{noc}', group='dcol2', name=name, noc=noc, tiles=cores)


CASES = list(_cases()) + list(_cases2())


def _bw(res, size, count):
  return {f'{t[0]},{t[1]}': size * count / (r['done'][0] - r['first'][0]) for (t, _), r in res.items()}


def run(card, case, timeout):
  size, count = 8192, 128
  if case['group'] == 'route':
    jobs = {tuple(r): {'brisc': ([(sw(noc=case['noc'], dram=False), size, s[0] | s[1] << 6)], count, 0)}
            for s, r in case['flows']}
    bw = _bw(traffic.traffic(card, jobs, timeout), size, count)
    links = {h: sorted(map(str, MODELS[h](*map(tuple, case['flows'][0])) & MODELS[h](*map(tuple, case['flows'][1]))))
             for h in case['predict']}
    return dict(bw=bw, min_bw=min(bw.values()), shared_links=links)
  if case['group'] == 'dcol2':
    pairs = DCOL2[case['name']]
  else:
    pairs = [(c, (0, (c[1] + case['offset']) % Y)) for c in case['cores']]
  jobs, paths = {}, {}
  for i, (c, ep_phys) in enumerate(pairs):
    ep = dram_endpoint(ep_phys[1])
    w = sw(noc=case['noc']) | 1 << 12 | (ep[0] | ep[1] << 6) << 16
    jobs[c] = {'brisc': ([(w, size, region(i))], count, 0)}
    paths[c] = MODELS['noc0_xfirst' if case['noc'] == 0 else 'noc1_yfirst'](ep_phys, c)
  from collections import Counter
  load = Counter(l for p in paths.values() for l in p)
  bw = _bw(traffic.traffic(card, jobs, timeout), size, count)
  return dict(bw=bw, total=sum(bw.values()), median_bw=median(bw.values()), predicted_max_link_flows=max(load.values()),
              endpoints=[list(e) for _, e in pairs])
