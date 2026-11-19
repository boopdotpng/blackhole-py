"""One DRAM bank's service model (k_traffic.c fixed-endpoint streams), bank 0 only: endpoints at physical
(0,11), (0,1), (0,0) = translated (17,14), (17,13), (17,12). Readers sit in row 11, so NoC0 responses run east along
row 11 (one link carries at most the bank's output, under a link's ~63 B/c): the bank is the only limit.

  init     4 cores write 8 MiB windows W0..W3 (bank-local 0x50000000 + j * 8 MiB), so every read hits written memory
  mix      llama's pattern on one core: BRISC reads (NoC0) + NCRISC non-posted writes (NoC1), same bank, writer
           throttled by an outstanding cap for different read:write ratios; also read+read and each alone
  streams  n readers on one bank: separate windows (far rows) vs interleaved in one window (near), one port vs three
  pattern  page size sweep and address stride sweep (sequential .. scattered), 4 readers; and a write size sweep
Streams advance their address every command (stride = size unless set) inside their 8 MiB window.
"""
import traffic
from traffic import sw
from routes import dram_endpoint

WIN = [0x50000000 + j * 0x800000 for j in range(4)]
EP = {11: dram_endpoint(11), 1: dram_endpoint(1), 0: dram_endpoint(0)}  # bank 0 ports by physical row
CORES = [(2, 11), (3, 11), (4, 11), (5, 11)]
CORES12 = [(x, y) for y in (11, 10) for x in (1, 2, 3, 4, 5, 6)]  # NoC0 responses: east on row 11, then down own column
MiB = 1 << 20


def fixed(ep_row=11, noc=0, write=False, tid=1):
  x, y = EP[ep_row]
  return sw(noc=noc, write=write, tid=tid) | 1 << 12 | (x | y << 6) << 16


def w1(size, stride=0):
  assert size < 1 << 16 and stride % 256 == 0
  return size | (stride // 256) << 16


def _cases():
  yield dict(id='init-4x8MiB', group='init', tiles=CORES, timeout=2.0)
  for size in (8192, 2048):
    for name in ('read', 'write', 'read+read', 'read+write-cap0', 'read+write-cap4', 'read+write-cap2', 'read+write-cap1'):
      if size == 2048 and name in ('read+read', 'read+write-cap4', 'read+write-cap2'): continue
      yield dict(id=f'mix-{name}-{size}', group='mix', name=name, size=size, tiles=CORES[:1])
  for n in (1, 2, 3, 4):
    yield dict(id=f'streams-far-n{n}', group='streams', n=n, near=False, ports=1, tiles=CORES[:n])
  for n in (2, 4):
    yield dict(id=f'streams-near-n{n}', group='streams', n=n, near=True, ports=1, tiles=CORES[:n])
  yield dict(id='streams-far-n3-3ports', group='streams', n=3, near=False, ports=3, tiles=CORES[:3])
  for size in (256, 512, 1024, 2048, 4096, 8192, 16384):
    yield dict(id=f'pattern-read-size{size}', group='pattern', write=False, size=size, stride=0, tiles=CORES)
  for stride in (4096, 8192, 16384, 65536, 0x51000):
    yield dict(id=f'pattern-read-2048-stride{stride:#x}', group='pattern', write=False, size=2048, stride=stride, tiles=CORES)
  for size in (256, 512, 1024, 2048):
    yield dict(id=f'small-read-size{size}-x12', group='small', size=size, tiles=CORES12)
    yield dict(id=f'small-read-size{size}-x12-staggered', group='small', size=size, stagger=True, tiles=CORES12)
  for size in (256, 1024, 2048, 8192):
    yield dict(id=f'pattern-write-size{size}', group='pattern', write=True, size=size, stride=0, tiles=CORES)


# phase: one core per bank, one read at a time; which reads hit refresh, in a common (offset-corrected) time base
PHASE_CORES = [(2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (10, 9), (11, 10)]


def _cases_more():
  for rep in (1, 2):
    yield dict(id=f'phase-8banks-run{rep}', group='phase', tiles=PHASE_CORES, timeout=1.0)
  for k in range(8, 22):
    yield dict(id=f'align-256-offset2^{k}', group='align', k=k, tiles=CORES12)
  yield dict(id='align-256-staggered', group='align', k=None, tiles=CORES12)


CASES = list(_cases()) + list(_cases_more())


def _rates(res, jobs):
  out = {}
  for (t, role), r in res.items():
    streams, count, _ = jobs[t][role]
    size = streams[0][1] & 0xFFFF
    out[f'{t[0]},{t[1]}:{role}'] = dict(rate=size * count / (r['done'][0] - r['first'][0]),
                                        first=r['first'][0], done=r['done'][0])
  return out


def run(card, case, timeout):
  g = case['group']
  if g == 'init':
    jobs = {c: {'brisc': ([(fixed(write=True), w1(8192), WIN[j])], MiB * 8 // 8192, 0)} for j, c in enumerate(CORES)}
    r = _rates(traffic.traffic(card, jobs, timeout), jobs)
    return dict(per_core=r, total=sum(v['rate'] for v in r.values()))

  if g == 'mix':
    size, name, c = case['size'], case['name'], CORES[0]
    count = 4 * MiB // size
    rd = ([(fixed(), w1(size), WIN[0])], count, 0)
    if name == 'read': jobs = {c: {'brisc': rd}}
    elif name == 'write': jobs = {c: {'ncrisc': ([(fixed(noc=1, write=True, tid=2), w1(size), WIN[1])], count, 0)}}
    elif name == 'read+read':
      jobs = {c: {'brisc': rd, 'ncrisc': ([(fixed(noc=1, tid=2), w1(size), WIN[1])], count, 0)}}
    else:
      cap = int(name.split('cap')[1])
      jobs = {c: {'brisc': rd, 'ncrisc': ([(fixed(noc=1, write=True, tid=2), w1(size), WIN[1])], count, cap)}}
    r = _rates(traffic.traffic(card, jobs, timeout), jobs)
    if len(r) == 2:  # second pass: size the NCRISC stream so both finish together, so both rates are concurrent
      ra, rb = r[f'{c[0]},{c[1]}:brisc']['rate'], r[f'{c[0]},{c[1]}:ncrisc']['rate']
      streams, _, cap = jobs[c]['ncrisc']
      jobs[c]['ncrisc'] = (streams, max(8, min(4 * count, round(count * rb / ra))), cap)
      r = _rates(traffic.traffic(card, jobs, timeout), jobs)
    ends = [v['done'] for v in r.values()]
    return dict(per_stream=r, total=sum(v['rate'] for v in r.values()), end_mismatch=max(ends) - min(ends))

  if g == 'streams':
    n, size = case['n'], 8192
    count = 2 * MiB // size
    jobs = {}
    for j, c in enumerate(CORES[:n]):
      port = (11, 1, 0)[j % 3] if case['ports'] == 3 else 11
      if case['near']: base, stride = WIN[0] + j * size, n * size
      else: base, stride = WIN[j], 0
      jobs[c] = {'brisc': ([(fixed(port), w1(size, stride), base)], count, 0)}
    r = _rates(traffic.traffic(card, jobs, timeout), jobs)
    return dict(per_core=r, total=sum(v['rate'] for v in r.values()),
                bank_rate=n * count * size / (max(v['done'] for v in r.values()) - min(v['first'] for v in r.values())))

  if g == 'pattern':
    size, write = case['size'], case['write']
    count = min(2048, 2 * MiB // size)
    role, noc, tid = ('ncrisc', 1, 2) if write else ('brisc', 0, 1)
    jobs = {c: {role: ([(fixed(noc=noc, write=write, tid=tid), w1(size, case['stride']), WIN[j])], count, 0)}
            for j, c in enumerate(CORES)}
    r = _rates(traffic.traffic(card, jobs, timeout), jobs)
    return dict(per_core=r, bank_rate=4 * count * size / (max(v['done'] for v in r.values()) - min(v['first'] for v in r.values())))
  if g == 'small':  # enough readers that the bank, not the issue loops, limits small requests
    size, count = case['size'], 256
    stag = 0x3100 if case.get('stagger') else 0  # odd multiple of 256: start addresses no longer share low address bits
    jobs = {c: {'brisc': ([(fixed(), w1(size), WIN[j % 4] + (j // 4) * 0x200000 + j * stag)], count, 0)}
            for j, c in enumerate(CORES12)}
    r = _rates(traffic.traffic(card, jobs, timeout), jobs)
    span = max(v['done'] for v in r.values()) - min(v['first'] for v in r.values())
    return dict(per_core=r, bank_rate=12 * count * size / span, requests_per_kcycle=1000 * 12 * count / span)
  if g == 'phase':
    from statistics import median
    import ping
    from tile import build
    from traffic import region, s32, EV_SITES
    n, img = 1500, build('k_dseq.c')
    offs = {c: ping.offset(card, c) for c in PHASE_CORES}
    jobs = [(c, img, [n, 64, 0, 1, b, 0, region(0) + 0x20000, 0], None) for b, c in enumerate(PHASE_CORES)]
    card.run(jobs, timeout, EV_SITES)
    out = {}
    for b, c in enumerate(PHASE_CORES):
      w = card.log(c, 2 * n)
      fire, lat = w[0::2], w[1::2]
      base = median(lat)
      out[b] = [s32(fire[i] - int(offs[c])) for i in range(n) if lat[i] - base >= 30]  # SRC-clock fire times of slow reads
    return dict(slow_fire=out, offsets={str(c): offs[c] for c in PHASE_CORES})

  if g == 'align':
    size, count = 256, 256
    off = (1 << case['k']) if case['k'] is not None else 0x3100
    jobs = {c: {'brisc': ([(fixed(), w1(size), WIN[0] + j * off)], count, 0)} for j, c in enumerate(CORES12)}
    r = _rates(traffic.traffic(card, jobs, timeout), jobs)
    span = max(v['done'] for v in r.values()) - min(v['first'] for v in r.values())
    return dict(cycles_per_request=span / (12 * count), bank_rate=12 * count * size / span)
  raise ValueError(g)
