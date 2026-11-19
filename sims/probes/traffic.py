"""DRAM, host and multi-stream NoC traffic, shaped like the llama kernels (k_traffic.c, k_events.c).

Groups (case id prefix):
  dlat    one command at a time from SRC to one DRAM endpoint: read response / non-posted write ack latency vs size
  dstream one core streaming pages interleaved over the 8 banks through one port, as llama does, with at most `cap`
          requests outstanding: per-core DRAM bandwidth and how much concurrency it needs
  dload   the llama decode load: the first K of llama's 88 cores (port = index % 3) stream 2 KiB pages at once from a
          synchronized start (per-tile clock offsets from ping.offset); variants put reads on NoC1, add NCRISC writes
  cmdbuf  does a second command buffer, the other NoC, or the other RISC add issue rate or bandwidth?
  host    non-posted writes and reads to pinned host memory over PCIe (argmax's result write)
  l1      a DRAM read stream into L1 while the other RISC hammers the same L1 with loads and stores

DRAM regions: core i owns bank offsets [BASE + i * STRIDE, + STRIDE) in every bank. Each region is written before
it is read (the dinit cases run first), so no probe reads never-written GDDR.
"""
from statistics import median

from tile import build
import ping

SRC = (1, 2)
SITES = {1: 'start', 2: 'cmd_ready', 3: 'outstanding_cap', 4: 'done'}
EV_SITES = {1: 'setup_ready', 2: 'cmd_ready', 3: 'counter', 4: 'drain_ready'}
LLAMA = [(x, y) for y in range(2, 10) for x in (1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13)]  # llama's 88, port = i % 3
BASE, STRIDE = 0x40000000, 0x100000
PCIE = 1 << 24 | 24 << 6 | 19
RESP_MARKED, VC1 = 1 << 4, 1 << 7 | 1 << 13


def dram_xy(bank, port):
  ys = ((14, 13, 12), (15, 16, 17), (18, 19, 20), (21, 22, 23), (14, 13, 12), (17, 16, 15), (20, 19, 18), (23, 22, 21))
  return 17 + (bank >> 2), ys[bank][(port + bank) % 3]


def sw(noc=0, buf=0, write=False, dram=True, port=0, posted=False, tid=1):
  return noc | buf << 1 | int(write) << 3 | int(dram) << 4 | port << 5 | int(posted) << 7 | tid << 8


def region(i): return BASE + i * STRIDE


def s32(x): return (x & 0xFFFFFFFF) - (1 << 32) if x & 0x80000000 else x & 0xFFFFFFFF


def traffic(card, jobs, timeout, sync=True, log=False):
  """jobs: {tile: {role: (streams, count, cap)}}, streams = [(word, size, base)]. Starts every job at the same
  instant (in SRC's clock) when sync. Returns {(tile, role): dict(start, done[], first[], issue[])} in SRC's clock."""
  img = {r: build('k_traffic.c', r) for r in ('brisc', 'ncrisc')}
  offs = {t: ping.offset(card, t) for t in jobs} if sync else {t: 0 for t in jobs}
  t0 = card.clock(SRC) + 30_000_000 if sync else 0  # ~22 ms at 1.35 GHz: room to launch every tile
  launch = []
  for t, roles in jobs.items():
    params = {}
    for role, (streams, count, cap) in roles.items():
      words = [len(streams) | int(log) << 8, count, (int(t0 + offs[t]) | 1) & 0xFFFFFFFF if sync else 0, cap]
      for w, size, base in streams: words += [w, size, base]
      params[role] = words
    launch.append((t, {r: img[r] for r in roles}, params, None))
  card.run(launch, timeout, SITES)
  out = {}
  for t, roles in jobs.items():
    for role, (streams, count, cap) in roles.items():
      a = card.aux(t, 9, role)
      fix = lambda v: s32(v - int(offs[t]) - (t0 & 0xFFFFFFFF if sync else a[0]))  # relative to the common start
      out[t, role] = dict(start=fix(a[0]), done=[fix(a[1 + s]) for s in range(len(streams))],
                          first=[fix(a[5 + s]) for s in range(len(streams))],
                          issue=[fix(v) for v in card.log(t, len(streams) * count, role)] if log else None)
  return out


def summarize(res, nbytes):
  start = min(r['start'] for r in res.values())
  end = max(max(r['done']) for r in res.values())
  per = sorted(max(r['done']) - min(r['first']) for r in res.values())
  return dict(cycles=end - start, bytes=nbytes, bytes_per_cycle=nbytes / (end - start), core_span_min=per[0],
              core_span_median=median(per), core_span_max=per[-1], start_skew=max(r['start'] for r in res.values()) - start)


# ---------------------------------------------------------------------------------------------------- cases
def _cases():
  # DRAM init: every LLAMA core writes its region (2 MiB, 4 KiB pages, all banks). Also the multi-core write numbers.
  yield dict(id='dinit-llama88', group='dinit', kind='init', tiles=LLAMA, timeout=2.0)
  eps = [(b, p) for b in (0, 3, 4, 7) for p in (0, 1, 2)]
  for op in ('write', 'read'):
    for size in (64, 256, 1024, 2048, 4096, 16384):
      for b, p in eps:
        for noc in (0, 1):
          yield dict(id=f'dlat-{op}-{size}-b{b}p{p}-noc{noc}', group='dlat', op=op, size=size, bank=b, port=p, noc=noc,
                     tiles=[SRC])
  for op in ('write', 'read'):
    for size in (1024, 2048, 4096, 8192):
      for cap in (1, 2, 4, 8, 16, 0):
        for noc in (0, 1):
          yield dict(id=f'dstream-{op}-{size}-cap{cap}-p0-noc{noc}', group='dstream', op=op, size=size, cap=cap, port=0,
                     noc=noc, tiles=[SRC])
    for p in (1, 2):
      for noc in (0, 1):
        yield dict(id=f'dstream-{op}-2048-cap0-p{p}-noc{noc}', group='dstream', op=op, size=2048, cap=0, port=p,
                   noc=noc, tiles=[SRC])
  for k in (1, 2, 3, 6, 12, 24, 44, 66, 88):
    for variant in ('rd-noc0', 'rd-noc1', 'rd-split', 'rd+wr', 'wr-noc1'):
      if variant != 'rd-noc0' and k not in (12, 44, 88): continue
      yield dict(id=f'dload-{variant}-k{k}', group='dload', variant=variant, k=k, size=2048, tiles=LLAMA[:k], timeout=1.0)
  yield dict(id='dload-rd-noc0-4096-k88', group='dload', variant='rd-noc0', k=88, size=4096, tiles=LLAMA, timeout=1.0)
  for op, size, b, p in (('read', 64, 0, 0), ('read', 64, 4, 0), ('read', 64, 7, 2), ('read', 2048, 0, 0), ('write', 64, 0, 0)):
    yield dict(id=f'dtrace-{op}-{size}-b{b}p{p}', group='dtrace', op=op, size=size, bank=b, port=p, tiles=[SRC])
  yield dict(id='dchain-read-2048-x4096', group='dchain', tiles=[SRC])
  # dseq: what makes a single read slow? (size, period, banks as hex nibbles, stride; 0 = same address every time)
  for size, period, banks, stride in [
      (64, 0, '0', 0), (64, 300, '0', 0), (64, 1000, '0', 0), (64, 2000, '0', 0), (64, 8000, '0', 0),
      (64, 0, '0', 64), (64, 0, '0', 2048), (64, 0, '0', 8192), (64, 0, '0', 0x8000),
      (64, 0, '40', 0), (64, 0, '76543210', 0), (64, 0, '76543210', 64),
      (128, 0, '0', 0), (256, 0, '0', 0), (512, 0, '0', 0), (1024, 0, '0', 0), (2048, 0, '0', 0), (4096, 0, '0', 0),
      (2048, 0, '76543210', 2048), (4096, 0, '76543210', 4096)]:
    yield dict(id=f'dseq-{size}-p{period}-banks{banks}-stride{stride}', group='dseq', size=size, period=period,
               banks=banks, stride=stride, tiles=[SRC])
  for name in CMDBUF:
    yield dict(id=f'cmdbuf-{name}', group='cmdbuf', name=name, tiles=[SRC, (2, 2)])
  for op in ('write', 'read'):
    for size in (16, 64, 2048, 4096):
      yield dict(id=f'host-{op}-{size}', group='host', op=op, size=size, tiles=[SRC])
  for load in ('none', 'loads', 'stores'):
    yield dict(id=f'l1-{load}', group='l1', load=load, tiles=[SRC])


# cmdbuf experiments: {role: [streams]} on SRC. 'T' = tile (2,2) L1 target, else DRAM via port 0. All count 64, no cap.
# Reads only touch regions dinit wrote (region(0), region(1)); writes go to region(0) + 0x80000, never read.
T = 2 | 2 << 6
CMDBUF = {
  'posted64-1buf':  {'brisc': [(sw(dram=False, write=True, posted=True), 64, T)]},
  'posted64-2buf':  {'brisc': [(sw(buf=b, dram=False, write=True, posted=True, tid=1 + b), 64, T) for b in range(2)]},
  'posted64-4buf':  {'brisc': [(sw(buf=b, dram=False, write=True, posted=True, tid=1 + b), 64, T) for b in range(4)]},
  'posted64-2noc':  {'brisc': [(sw(noc=n, dram=False, write=True, posted=True, tid=1 + n), 64, T) for n in range(2)]},
  'posted16k-1buf': {'brisc': [(sw(dram=False, write=True, posted=True), 16384, T)]},
  'posted16k-2buf': {'brisc': [(sw(buf=b, dram=False, write=True, posted=True, tid=1 + b), 16384, T) for b in range(2)]},
  'posted16k-2noc': {'brisc': [(sw(noc=n, dram=False, write=True, posted=True, tid=1 + n), 16384, T) for n in range(2)]},
  'read2k-1buf':    {'brisc': [(sw(), 2048, region(0))]},
  'read2k-2buf':    {'brisc': [(sw(buf=b, tid=1 + b), 2048, region(b)) for b in range(2)]},
  'read2k-2noc':    {'brisc': [(sw(noc=n, tid=1 + n), 2048, region(n)) for n in range(2)]},
  'read2k-2risc':   {'brisc': [(sw(), 2048, region(0))], 'ncrisc': [(sw(noc=1, tid=2), 2048, region(1))]},
  'npwrite2k-1buf': {'brisc': [(sw(write=True), 2048, region(0))]},
  'npwrite2k-2buf': {'brisc': [(sw(buf=b, write=True, tid=1 + b), 2048, region(0) + b * 0x80000) for b in range(2)]},
  'rd0+wr1-1risc':  {'brisc': [(sw(), 2048, region(0)), (sw(noc=1, write=True, tid=2), 2048, region(0) + 0x80000)]},
  'rd0+wr1-2risc':  {'brisc': [(sw(), 2048, region(0))], 'ncrisc': [(sw(noc=1, write=True, tid=2), 2048, region(0) + 0x80000)]},
}

CASES = list(_cases())


# ---------------------------------------------------------------------------------------------------- run
def run(card, case, timeout):
  g = case['group']
  if g == 'dinit':
    jobs = {t: {'ncrisc': ([(sw(noc=1, write=True, port=i % 3), 4096, region(i))], 512, 128)} for i, t in enumerate(LLAMA)}
    res = traffic(card, jobs, timeout)
    return summarize(res, 88 * 512 * 4096)

  if g == 'dlat':
    x, y = dram_xy(case['bank'], case['port'])
    write = case['op'] == 'write'
    ctrl = VC1 | RESP_MARKED if write else VC1
    params = [0, case['noc'], 0 if write else 1, ctrl, 1 if write else 2, x | y << 6, case['size'], 32, 4000, 0,
              region(0) + 0x10000, 0]
    img = build('k_events.c')
    card.run([(SRC, img, params, None)], timeout, EV_SITES)
    w = card.log(SRC, 64)
    d = [s32(w[2 * i + 1] - w[2 * i]) for i in range(32)][2:]
    return dict(min=min(d), median=median(d), max=max(d), samples=d, endpoint=[x, y])

  if g == 'dtrace':  # back-to-back single commands, every one logged: where do slow ones fall in time?
    x, y = dram_xy(case['bank'], case['port'])
    write, n = case['op'] == 'write', 3800
    params = [0, 0, 0 if write else 1, VC1 | (RESP_MARKED if write else 0), 1 if write else 2, x | y << 6, case['size'],
              n, 0, 0, region(0) + 0x20000, 0]
    card.run([(SRC, build('k_events.c'), params, None)], timeout, EV_SITES)
    w = card.log(SRC, 2 * n)
    t0 = w[0]
    return dict(fire=[s32(w[2 * i] - t0) for i in range(n)], lat=[s32(w[2 * i + 1] - w[2 * i]) for i in range(n)])

  if g == 'dseq':
    n, banks = 1500, case['banks']
    params = [n, case['size'], case['period'], len(banks), int(banks[::-1], 16),
              0, region(0) + 0x20000, case['stride']]
    card.run([(SRC, build('k_dseq.c'), params, None)], timeout, EV_SITES)
    w = card.log(SRC, 2 * n)
    lat = list(w[1::2])
    base = median(lat)
    slow = [i for i, x in enumerate(lat) if x - base >= 30]
    gaps = [b - a for a, b in zip(slow, slow[1:])]
    return dict(median=base, slow_frac=len(slow) / n, slow_every=median(gaps) if gaps else None,
                slow_extra=sorted({lat[i] - base for i in slow})[:8], lat=lat)

  if g == 'dchain':  # BRISC streams uncapped reads; NCRISC logs every change of BRISC's NoC0 read-response counter
    count, max_rec = 4096, 3800
    img = {'brisc': build('k_traffic.c', 'brisc'), 'ncrisc': build('k_observe.c', 'ncrisc')}
    params = {'brisc': [1, count, 0, 0, sw(), 2048, region(0)], 'ncrisc': [0xFFB20000 + 0x200 + 4 * 2, max_rec, 2_000_000]}
    card.run([(SRC, img, params, None)], timeout, SITES)
    n = card.aux(SRC, 1, 'ncrisc')[0]
    w = card.log(SRC, 2 * n, 'ncrisc')
    t0, v0 = w[0], w[1]
    return dict(t=[s32(w[2 * i] - t0) for i in range(n)], resp=[(w[2 * i + 1] - v0) & 0xFFFFFFFF for i in range(n)])

  if g == 'dstream':
    write = case['op'] == 'write'
    count = 256
    jobs = {SRC: {'brisc': ([(sw(noc=case['noc'], write=write, port=case['port']), case['size'], region(0))], count, case['cap'])}}
    res = traffic(card, jobs, timeout, sync=False, log=True)[SRC, 'brisc']
    total = res['done'][0] - res['first'][0]
    iss = [b - a for a, b in zip(res['issue'], res['issue'][1:])]
    return dict(cycles=total, bytes_per_cycle=count * case['size'] / total, issue_median=median(iss), issue_max=max(iss))

  if g == 'dload':
    k, size, v = case['k'], case['size'], case['variant']
    count = (1 << 20) // size  # 1 MiB per core
    jobs = {}
    for i, t in enumerate(LLAMA[:k]):
      noc = 1 if v == 'rd-noc1' or (v == 'rd-split' and i % 2) else 0
      roles = {}
      if v != 'wr-noc1': roles['brisc'] = ([(sw(noc=noc, port=i % 3), size, region(i))], count, 0)
      if v in ('rd+wr', 'wr-noc1'):
        roles['ncrisc'] = ([(sw(noc=1, write=True, port=i % 3, tid=2), size, region(i) + 0x80000)], count // (1 if v == 'wr-noc1' else 8), 0)
      jobs[t] = roles
    res = traffic(card, jobs, timeout)
    nbytes = sum(c * s for roles in jobs.values() for streams, c, _ in roles.values() for _, s, _ in streams)
    out = summarize(res, nbytes)
    reads = {key: r for key, r in res.items() if key[1] == 'brisc'}
    if reads and v == 'rd+wr':
      rb = sum(c * s for roles in jobs.values() for role, (streams, c, _) in roles.items() if role == 'brisc' for _, s, _ in streams)
      out['read_bytes_per_cycle'] = rb / (max(max(r['done']) for r in reads.values()) - min(r['start'] for r in reads.values()))
    out['per_core_cycles'] = {f'{t[0]},{t[1]}:{role}': max(r['done']) - min(r['first']) for (t, role), r in res.items()}
    return out

  if g == 'cmdbuf':
    roles = {role: (streams, 64, 0) for role, streams in CMDBUF[case['name']].items()}
    res = traffic(card, {SRC: roles}, timeout, sync=False, log=True)
    out = {}
    for (t, role), r in res.items():
      n = len(roles[role][0])
      for s in range(n):
        iss = r['issue'][s::n]
        gaps = [b - a for a, b in zip(iss, iss[1:])]
        size = roles[role][0][s][1]
        out[f'{role}.s{s}'] = dict(span=r['done'][s] - r['first'][s], issue_median=median(gaps), issue_max=max(gaps),
                                   bytes_per_cycle=64 * size / (r['done'][s] - r['first'][s]), issue_first=gaps[:12])
    allb = sum(64 * s for streams, _, _ in roles.values() for _, s, _ in streams)
    span = max(max(r['done']) for r in res.values()) - min(min(r['first']) for r in res.values())
    out['total'] = dict(span=span, bytes_per_cycle=allb / span)
    return out

  if g == 'host':
    mem = card.__dict__.get('sysmem')
    if mem is None:
      from system import Sysmem
      mem = card.sysmem = Sysmem(card.iface.fd, 1 << 16)
      card.__dict__.setdefault('cleanup', []).append(mem.close)
    write = case['op'] == 'write'
    lo, mid = mem.noc_addr & 0xFFFFFFFF, mem.noc_addr >> 32
    params = [0, 0, 0 if write else 1, VC1 | (RESP_MARKED if write else 0), 1 if write else 2, PCIE, case['size'], 32,
              8000, 0, lo, mid]
    card.run([(SRC, build('k_events.c'), params, None)], timeout, EV_SITES)
    w = card.log(SRC, 64)
    d = [s32(w[2 * i + 1] - w[2 * i]) for i in range(32)][2:]
    return dict(min=min(d), median=median(d), max=max(d), samples=d)

  if g == 'l1':
    count = 64
    img = {'brisc': build('k_traffic.c', 'brisc')}
    params = {'brisc': [1, count, 0, 0, sw(), 4096, region(0)]}
    if case['load'] != 'none':
      img['ncrisc'] = build('k_l1load.c', 'ncrisc')
      params['ncrisc'] = [1 if case['load'] == 'stores' else 0, 1 << 20]
    card.run([(SRC, img, params, None)], timeout, SITES)
    a = card.aux(SRC, 9)
    span = s32(a[1] - a[5])
    out = dict(read_cycles=span, read_bytes_per_cycle=count * 4096 / span)
    if 'ncrisc' in img:
      b = card.aux(SRC, 4, 'ncrisc')
      out.update(l1_ops=b[0], l1_cycles=s32(b[1] - b[2]))
    return out
  raise ValueError(g)
