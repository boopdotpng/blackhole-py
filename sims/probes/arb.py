"""How a contested link is shared (k_traffic.c posted tile-to-tile writes: the data rides on the request, so each source's
rate is its share). Every case runs twice: the second run sizes each flow from the first run's rates so all flows end
together, and the rates are concurrent shares, not averages over different durations.

  chainN    N sources in row 5, each joining at a different router, all sharing the last link before (5,5) on NoC0
            (or before (3,5) on NoC1, mirrored). Per-flow fair: 1/N each. Round-robin per router input port: the
            source joining last gets 1/2, the one before 1/4, ...
  merge3    three flows into the south link out of (6,5) on NoC0: one turning from x to y, one straight through in y,
            one injected locally at (6,5)
  packet    a 16 KiB-packet flow against a 4 KiB-packet flow on one link (per-packet arbitration -> 4:1, per-flit -> 1:1)
  demand    one low-demand source (512 B packets, issue-limited ~7 B/c) plus three saturating sources (chain4 layout)
"""
from statistics import median

import ping
from tile import build
from traffic import sw, s32, SITES

LINK = 63.0


def flows_chain(n, noc):
  if noc == 0:
    src = [(x, 5) for x in (1, 2, 3, 4)][-n:]
    dst = [(5, 5), (6, 5), (7, 5), (10, 5)][:n]
  else:
    src = [(x, 5) for x in (7, 6, 5, 4)][-n:]
    dst = [(3, 5), (2, 5), (1, 5), (16, 5)][:n]
  return [(s, d, 8192) for s, d in zip(src, dst)]


CASE_FLOWS = {
  'chain2-noc0': (0, flows_chain(2, 0)), 'chain3-noc0': (0, flows_chain(3, 0)), 'chain4-noc0': (0, flows_chain(4, 0)),
  'chain4-noc1': (1, flows_chain(4, 1)),
  'merge3-noc0': (0, [((4, 5), (6, 8), 8192), ((6, 3), (6, 9), 8192), ((6, 5), (6, 7), 8192)]),
  'packet-16k-vs-4k-noc0': (0, [((3, 5), (5, 5), 16384), ((4, 5), (6, 5), 4096)]),
  'demand-noc0': (0, [((1, 5), (5, 5), 512)] + flows_chain(3, 0)),
}

CASES = [dict(id=f'arb-{name}', name=name, tiles=sorted({t for s, d, _ in fl for t in (s, d)}))
         for name, (noc, fl) in CASE_FLOWS.items()]


PERIOD, RECORDS = 500, 3800


def _run(card, noc, flows, timeout):
  """Each source streams ~4 MiB; its NCRISC samples its own NIU's posted-data-sent counter every PERIOD cycles.
  Rates are measured over the window where every flow is running (middle of the overlap)."""
  img = {'brisc': build('k_traffic.c', 'brisc'), 'ncrisc': build('k_observe.c', 'ncrisc')}
  offs = {s: ping.offset(card, s) for s, _, _ in flows}
  t0 = card.clock((1, 2)) + 30_000_000
  jobs, info = [], []
  for s, d, size in flows:
    count = (4 << 20) // size
    start = (int(t0 + offs[s]) | 1) & 0xFFFFFFFF
    w = [1, count, start, 0, sw(noc=noc, dram=False, write=True, posted=True), size, d[0] | d[1] << 6]
    counter = 0xFFB20000 + noc * 0x10000 + 0x200 + 4 * 0x9  # NIU_MST_POSTED_WR_DATA_WORD_SENT
    jobs.append((s, img, {'brisc': w, 'ncrisc': [counter, RECORDS, 40_000_000, PERIOD, (start - 2000) & 0xFFFFFFFF]}, None))
    info.append((s, d, size, count))
  card.run(jobs, timeout, SITES)
  series = []
  for s, d, size, count in info:
    n = card.aux(s, 1, 'ncrisc')[0]
    w = card.log(s, 2 * n, 'ncrisc')
    t = [s32(w[2 * i] - int(offs[s]) - t0) for i in range(n)]
    v = [(w[2 * i + 1] - w[1]) & 0xFFFFFFFF for i in range(n)]
    moving = [i for i in range(1, n) if v[i] != v[i - 1]]
    if not moving: raise RuntimeError(f'{s}: counter never moved')
    series.append(dict(src=s, dst=d, size=size, t=t, v=v, bytes_per_unit=size * count / v[-1],
                       start=t[moving[0] - 1], end=t[moving[-1]]))
  lo, hi = max(x['start'] for x in series), min(x['end'] for x in series)
  lo, hi = lo + (hi - lo) // 4, hi - (hi - lo) // 4
  out = []
  for x in series:
    i = next(i for i, tt in enumerate(x['t']) if tt >= lo)
    j = max(i + 1, max(k for k, tt in enumerate(x['t']) if tt <= hi))
    rate = (x['v'][j] - x['v'][i]) * x['bytes_per_unit'] / (x['t'][j] - x['t'][i])
    out.append(dict(src=list(x['src']), dst=list(x['dst']), size=x['size'], rate=round(rate, 2), share=round(rate / LINK, 3),
                    active=[x['start'], x['end']]))
  return out, hi - lo


def run(card, case, timeout):
  noc, flows = CASE_FLOWS[case['name']]
  r, window = _run(card, noc, flows, timeout)
  return dict(flows=r, total=round(sum(f['rate'] for f in r), 1), window_cycles=window)
