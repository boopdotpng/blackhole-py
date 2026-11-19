"""Packer timing (k_pack.c on TRISC2, k_pack_math.c on TRISC1, k_pack_noc.c on BRISC, k_pack_unp.c on TRISC0).
See PACK.md for the case groups, hypotheses and expected values.

  python3 sims/probes/run.py --device 1 --output sims/results/<date>-pack-card1.jsonl pack [-k fmt-]

Every launch fills Dst from the SFPU on TRISC1 with a pattern that is exact in every output format, configures the
packer the way the llama kernels do, and times on TRISC2 with the tile wall clock. Each case reads back the packed
bytes and compares them with a numpy reference ('verify' in the record); a mismatch is recorded, not raised, so the
timing is still kept, but such a timing must not be used.
"""
import hashlib, struct
from pathlib import Path
from statistics import median

import numpy as np

from tile import LAYOUT, build as _build

HERE = Path(__file__).resolve().parent
TILE, REMOTE = (1, 2), (2, 2)
SITES = {1: 'fill/setup', 2: 'traffic_up/ready', 3: 'unpack_up/drain', 4: 'vis_seen/go', 5: 'vis_done/resp', 6: 'sem'}

# pack.h mirrors
PK_FLAGS, PK_OUT, PK_VIS_SLOTS = 0x40200, 0x80000, 0xC0000
NEAR, FAR, PAYLOAD = 0x8C000, 0x150000, 0x100000   # NEAR: same 96 KiB range as PK_OUT (0x78000-0x8FFFF); FAR: 9 ranges away
SENT = 0xFFFFFFFF
F = dict(SETW=1, ADDR_WRCFG=2, ADDR_ADC=4, PRE=8, POST=16, CB=32, ZEROACC=64, SELFSEM=128, L1ACC=256, EDGE=512,
         RECFG=1024, PRE_TTRV=2048, SEMWAIT=4096, SEMPOLL=8192)
INLINE, MOP, TINY = 0, 1, 2

# name: (fmt id in pack.h, fill pattern, Dst 16-bit, output bytes per datum (bfp: mantissa bytes), bfp)
FORMATS = {
  'f32-f32': (0, 1, 0, 4, 0), 'f32-bf16': (1, 1, 0, 2, 0), 'bf16-bf16-d16': (2, 1, 1, 2, 0),
  'f16-e4m3': (3, 3, 0, 1, 0), 'f32-bfp8': (4, 1, 0, 1, 1), 'f32-bfp4': (5, 2, 0, 0.5, 1),
}
LLAMA_FMTS = ('f32-bf16', 'f32-f32', 'bf16-bf16-d16', 'f16-e4m3')
COUNTS, SAMPLES = (1, 2, 4, 8), 8


def build(src, role):
  h = hashlib.sha256(b''.join((HERE / f).read_bytes() for f in ('pack.h', 'probe.h'))).hexdigest()[:8]
  return _build(src, role, PKHASH=f'0x{h}')  # tile.build's cache key doesn't hash these headers


# ---------------------------------------------------------------- reference (pack.py <-> k_pack_math.c fill)

def dst_bits(pattern, t):
  """Dst tile t after the fill, as fp32 bits [64 rows, 16 columns]."""
  r, c = np.meshgrid(np.arange(64), np.arange(16), indexing='ij')
  g, lane, p = r // 4, (r % 4) * 8 + c // 2, c % 2
  e = 121 + (16 * t + g) % 11 if pattern == 3 else 64 + (16 * t + g) % 128
  term = {1: lane << 17, 2: (lane & 3) << 21, 3: lane << 20}[pattern]
  return ((p.astype(np.uint64) << 31) | (e.astype(np.uint64) << 23)) + term.astype(np.uint64)


def encode(fmt, bits, nibble_hi_first=False):
  """Packed bytes of Dst rows `bits` [rows, 16] in format `fmt` (exact for the fill patterns)."""
  bits = bits.astype(np.uint64)
  s, e = bits >> 31, (bits >> 23) & 0xFF
  if fmt in ('f32-f32',): return bits.astype('<u4').tobytes()
  if fmt in ('f32-bf16', 'bf16-bf16-d16'): return (bits >> 16).astype('<u2').tobytes()
  if fmt == 'f16-e4m3': return (s << 7 | (e - 120) << 3 | (bits >> 20) & 7).astype(np.uint8).tobytes()
  rows = bits.shape[0]
  exps = np.zeros(16 * max(1, rows // 16), np.uint8)
  exps[:rows] = e.max(axis=1)
  if fmt == 'f32-bfp8': mant = (s << 7 | 64 | (bits >> 17) & 31).astype(np.uint8).ravel()
  else:
    nib = (s << 3 | 4 | (bits >> 21) & 3).astype(np.uint8).ravel()
    lo, hi = (nib[1::2], nib[0::2]) if nibble_hi_first else (nib[0::2], nib[1::2])
    mant = (lo | hi << 4).astype(np.uint8)
  return exps.tobytes() + mant.tobytes()


def unit_bytes(fmt, rows):
  _, _, _, size, bfp = FORMATS[fmt]
  return (16 * max(1, rows // 16) if bfp else 0) + int(rows * 16 * size)


def bf16_rne(x):
  b = np.asarray(x, np.float32).view(np.uint32).astype(np.uint64)
  return ((b + 0x7FFF + ((b >> 16) & 1)) >> 16).astype(np.uint16)


def expected(case):
  """[(address, bytes or list of alternatives)] the run must leave in L1, or None when the case can't be checked."""
  fmt, rows, fl, body = case['fmt'], case['rows'], case['flags'], case['body']
  pattern = FORMATS[fmt][1]
  if fl & (F['ZEROACC'] | F['EDGE']) or case['mode'] == 3: return None
  tile = lambda u: dst_bits(pattern, u % case['dstt'] if fl & F['SETW'] else 0)
  if body == TINY:
    x, n = case['tinyx'] + 1, [c for c in case['counts'] if c][-1]
    row = dst_bits(pattern, 0)[0:1, :x]
    reps = n if case['k'] else 1
    return [(PK_OUT, encode(fmt, np.tile(row, (1, reps))))]
  if fl & F['L1ACC']:
    k = SAMPLES * sum(case['counts'])
    v = tile(0)[:rows]
    if fmt == 'f32-f32': return [(PK_OUT, (v.astype(np.uint32).view(np.float32).astype(np.float64) * k).astype('<f4').tobytes())]
    acc = np.zeros(v.shape, np.uint16)
    vf = (v >> 16).astype(np.uint32) << 16
    for _ in range(k):
      acc = bf16_rne((acc.astype(np.uint32) << 16).view(np.float32) + vf.astype(np.uint32).view(np.float32))
    return [(PK_OUT, acc.astype('<u2').tobytes())]
  outs = lambda u: ([encode(fmt, tile(u)[:rows]), encode(fmt, tile(u)[:rows], True)] if fmt == 'f32-bfp4'
                    else encode(fmt, tile(u)[:rows]))
  if case['mode'] in (1, 2): return [(PK_OUT, outs(0))]
  if fl & (F['ADDR_WRCFG'] | F['ADDR_ADC']):
    return [(PK_OUT + u * case['stride'], outs(u)) for u in range(max(case['counts']))]
  return [(PK_OUT, outs(case['counts'][-1] - 1))]


def check(card, case):
  exp = expected(case)
  if exp is None: return dict(verify='skip')
  bad, notes = 0, []
  for addr, want in exp:
    alts = want if isinstance(want, list) else [want]
    got = card.iface.read(TILE, addr, len(alts[0]))
    hit = [i for i, w in enumerate(alts) if got == w]
    if not hit:
      bad += 1
      w = alts[0]
      first = next(i for i in range(len(w)) if got[i] != w[i])
      notes.append(dict(addr=addr, first_bad_byte=first, mismatched=sum(a != b for a, b in zip(got, w)),
                        got=got[first:first + 16].hex(), want=w[first:first + 16].hex()))
    elif len(alts) > 1: notes.append(dict(addr=addr, variant=hit[0]))
  end = exp[-1][0] + len(exp[-1][1][0] if isinstance(exp[-1][1], list) else exp[-1][1])
  guard = card.iface.read(TILE, end, 32)
  return dict(verify='ok' if not bad else 'FAIL', verify_notes=notes[:4], guard_after=guard.hex())


# ---------------------------------------------------------------- cases

def C(id, group, fmt='f32-bf16', body=MOP, rows=64, k=4, flags=0, counts=COUNTS, dstt=1, mode=0, n=0, vis=0,
      semmax=1, tinyx=0, companions=(), hmode=0, delay=0, timeout=None):
  stride = (unit_bytes(fmt, rows) + 63) // 64 * 64
  d = dict(id=id, group=group, fmt=fmt, body=body, rows=rows, k=k, flags=flags, counts=tuple(counts), dstt=dstt,
           mode=mode, n=n, vis=vis, semmax=semmax, tinyx=tinyx, stride=stride, companions=tuple(companions),
           hmode=hmode, delay=delay, tiles=[TILE] + ([REMOTE] if any(c.startswith('remote') for c in companions) else []))
  if timeout: d['timeout'] = timeout
  return d


ADV = F['SETW'] | F['ADDR_ADC']
LLAMA_PRE = F['SETW'] | F['ADDR_WRCFG'] | F['PRE']
LLAMA_TILE = LLAMA_PRE | F['POST'] | F['CB'] | F['ZEROACC'] | F['SELFSEM']
OVERHEAD = {  # name: (body, flags): the per-tile instruction sets the kernels emit, built up one piece at a time
  'bare-mop': (MOP, 0), 'bare-inline': (INLINE, 0), 'setw': (MOP, F['SETW']),
  'addr-wrcfg': (MOP, F['SETW'] | F['ADDR_WRCFG']), 'addr-adc': (MOP, ADV), 'llama-pre': (MOP, LLAMA_PRE),
  'llama-post': (MOP, LLAMA_PRE | F['POST']), 'llama-cb': (MOP, LLAMA_PRE | F['POST'] | F['CB']),
  'llama-tile': (MOP, LLAMA_TILE), 'llama-tile-nozero': (MOP, LLAMA_TILE & ~F['ZEROACC']),
  'ttrv-move': (INLINE, F['SETW'] | F['ADDR_WRCFG'] | F['PRE_TTRV']),
  'ttrv-move-post': (INLINE, F['SETW'] | F['ADDR_WRCFG'] | F['PRE_TTRV'] | F['POST']),
  'recfg-tile': (MOP, F['RECFG'] | LLAMA_PRE | F['POST']), 'edge-llama': (MOP, F['EDGE']),
}
CONTEND = {  # name: companion jobs running while TRISC2 packs
  'none': (), 'selfwr-near': ('selfwr-near',), 'selfwr-far': ('selfwr-far',), 'selfrd-near': ('selfrd-near',),
  'selfrd-far': ('selfrd-far',), 'remotewr-near': ('remotewr-near',), 'remotewr-far': ('remotewr-far',),
  'unpack-near': ('unpack-near',), 'unpack-far': ('unpack-far',), 'unpack+selfwr-near': ('unpack-near', 'selfwr-near'),
}


def _cases():
  # fmt: every in-scope (in, out) pair, a whole tile, llama's MOP and ttrv's inline PACRs, back to back
  for fmt in FORMATS:
    for body, bn in ((MOP, 'mop'), (INLINE, 'inline')):
      yield C(f'fmt-{fmt}-{bn}', 'fmt', fmt, body, dstt=2, flags=F['SETW'])
    yield C(f'fmt-{fmt}-mop-adv', 'fmt', fmt, MOP, dstt=4, flags=ADV)
  # shape: rows per unit x rows per PACR (ReadIntfSel 1, 3, 15 / 0)
  for fmt in LLAMA_FMTS + ('f32-bfp8', 'f32-bfp4'):
    for rows in (4, 16, 64):
      if FORMATS[fmt][4] and rows < 16: continue
      for k in (1, 2, 4):
        yield C(f'shape-{fmt}-r{rows}-k{k}', 'shape', fmt, INLINE, rows, k, counts=(1, 2, 4, 8) if rows > 4 else (2, 4, 8, 16))
  # tiny: per-PACR admission with almost no data
  for fmt in ('f32-bf16', 'f32-f32', 'bf16-bf16-d16'):
    for x in (0, 15):
      for last in (0, 1):
        yield C(f'tiny-{fmt}-x{x + 1}-{"lastonce" if last else "lasteach"}', 'tiny', fmt, TINY, 1, last,
                counts=(8, 16, 32, 64), tinyx=x)
  # l1acc: L1 += packed, overwrite timing for comparison is fmt-*
  for fmt in ('f32-f32', 'f32-bf16'):
    for body, bn in ((MOP, 'mop'), (INLINE, 'inline')):
      yield C(f'l1acc-{fmt}-{bn}', 'l1acc', fmt, body, flags=F['L1ACC'])
    yield C(f'l1acc-{fmt}-mop-selfwr-near', 'l1acc', fmt, MOP, flags=F['L1ACC'], companions=('selfwr-near',))
  # overhead: per-tile config writes / ADC resets / drains as the kernels emit them
  for fmt in ('f32-bf16', 'f16-e4m3', 'f32-f32'):
    for name, (body, fl) in OVERHEAD.items():
      if fmt != 'f32-bf16' and name in ('edge-llama', 'setw', 'bare-inline'): continue
      yield C(f'overhead-{fmt}-{name}', 'overhead', fmt, body, flags=fl, dstt=2)
  # visibility: last PACR issue -> data readable by this RISC / by an outgoing NoC read
  for fmt in ('f32-bf16', 'f32-f32', 'f16-e4m3'):
    for rows in (64, 4) if fmt == 'f32-bf16' else (64,):
      body = MOP if rows == 64 else INLINE
      yield C(f'vis-{fmt}-r{rows}-poll', 'vis', fmt, body, rows, mode=1, vis=0)
      yield C(f'vis-{fmt}-r{rows}-drainfirst', 'vis', fmt, body, rows, mode=1, vis=1)
      yield C(f'vis-{fmt}-r{rows}-noc', 'vis', fmt, body, rows, mode=1, vis=2)
  # handoff: math SEMPOST -> pack done (latency), and the steady pipeline rate
  for wait, fl in (('semwait', F['SEMWAIT']), ('sempoll', F['SEMPOLL'])):
    yield C(f'handoff-lat-{wait}', 'handoff', 'f32-bf16', MOP, flags=fl | F['POST'], mode=2, n=16, hmode=1, delay=3000)
  yield C('handoff-lat-selfsem', 'handoff', 'f32-bf16', MOP, flags=F['SELFSEM'] | F['POST'], mode=2, n=16)
  pipe = LLAMA_PRE | F['POST'] | F['CB'] | F['ZEROACC'] | F['SEMWAIT']
  for semmax in (1, 2):
    for d in (0, 100, 200, 400, 800, 1600):
      yield C(f'handoff-pipe-max{semmax}-d{d}', 'handoff', 'f32-bf16', MOP, flags=pipe, dstt=2, mode=3, n=32,
              hmode=2, delay=d, semmax=semmax)
    yield C(f'handoff-pipe-max{semmax}-d200-poll', 'handoff', 'f32-bf16', MOP, flags=pipe & ~F['SEMWAIT'] | F['SEMPOLL'],
            dstt=2, mode=3, n=32, hmode=2, delay=200, semmax=semmax)
  # contention: back-to-back tiles to advancing addresses while something else uses L1
  # (unpack companions last: the unpacker stream is the riskiest configuration here, see PACK.md)
  for unpack in (False, True):
    for fmt in ('f32-bf16', 'f32-f32'):
      for name, comp in CONTEND.items():
        if ('unpack' in name) != unpack: continue
        if fmt == 'f32-f32' and name not in ('none', 'selfwr-near', 'remotewr-near', 'unpack-near'): continue
        yield C(f'contend-{fmt}-{name}', 'contend', fmt, MOP, flags=ADV, dstt=4, companions=comp)
      if not unpack:
        yield C(f'contend-{fmt}-llama-tile-selfwr-near', 'contend', fmt, MOP, flags=LLAMA_TILE & ~F['ZEROACC'],
                dstt=2, companions=('selfwr-near',))


CASES = list(_cases())
assert len({c['id'] for c in CASES}) == len(CASES)


# ---------------------------------------------------------------- run

def _s32(x): return (x & 0xFFFFFFFF) - (1 << 32) if x & 0x80000000 else x & 0xFFFFFFFF


def _traffic(name, remote=False):
  op = 1 if 'rd' in name else 0
  addr = NEAR if name.endswith('near') else FAR
  target = TILE[0] | TILE[1] << 6 if remote else 0xFFFFFFFF
  return [0, 0, op, target, PAYLOAD, addr, 4096, 1 << 16, 2_000_000 if remote else 0]


def run(card, case, timeout):
  fmt = case['fmt']
  fid, pattern, d16, _, _ = FORMATS[fmt]
  counts = case['counts']
  waitup = 0
  images = {'trisc1': build('k_pack_math.c', 'trisc1'), 'trisc2': build('k_pack.c', 'trisc2')}
  params = {'trisc1': [pattern, d16, max(case['dstt'], 1), case['hmode'], case['n'], case['delay'], case['semmax']]}
  l1 = {PK_FLAGS: bytes(0x100)}
  span = case['stride'] * (max(counts) if case['flags'] & (F['ADDR_WRCFG'] | F['ADDR_ADC']) else 1) + 256
  l1[PK_OUT] = bytes(span) if case['flags'] & F['L1ACC'] else b'\xa5' * span
  jobs = []
  for comp in case['companions']:
    if comp.startswith('self'):
      images['brisc'], params['brisc'] = build('k_pack_noc.c', 'brisc'), _traffic(comp)
      waitup |= 1
    elif comp.startswith('remote'):
      jobs.append((REMOTE, {'brisc': build('k_pack_noc.c', 'brisc')}, {'brisc': _traffic(comp, True)}, {PK_FLAGS: bytes(0x100)}))
    elif comp.startswith('unpack'):
      src = NEAR if comp.endswith('near') else FAR
      images['trisc0'], params['trisc0'] = build('k_pack_unp.c', 'trisc0'), [src, 1 << 20]
      l1[src] = bytes(512)
      waitup |= 2
  vis_stride = unit_bytes(fmt, case['rows'])
  if case['mode'] == 1 and case['vis'] & 2:
    images['brisc'] = build('k_pack_noc.c', 'brisc')
    params['brisc'] = [1, 0, 0, 0xFFFFFFFF, 0, 0, 0, 0, 0, SAMPLES, 64, PK_OUT + vis_stride - 16]
  params['trisc2'] = [fid, case['body'], case['rows'], case['k'], case['flags'],
                      sum(c << 8 * i for i, c in enumerate(counts)), SAMPLES, case['dstt'], PK_OUT,
                      vis_stride if case['mode'] == 1 else case['stride'], case['mode'], case['n'], case['vis'],
                      case['semmax'], waitup, case['tinyx']]
  jobs.append((TILE, images, params, l1))
  card.run(jobs, timeout, SITES)

  res = lambda role: LAYOUT[role]['res']
  n2 = card.iface.read32(TILE, res('trisc2') + 8)
  log = card.log(TILE, n2, 'trisc2')
  aux2 = card.aux(TILE, 4, 'trisc2')
  rec = dict(check(card, case), t2_start=aux2[0], t2_end=aux2[1])
  for role in ('brisc', 'trisc0'):
    if role in images:
      a = card.aux(TILE, 3, role)
      rec[f'{role}_aux'] = a
      rec[f'{role}_covers'] = bool(a[0] and _s32(aux2[0] - a[0]) >= 0 and _s32(a[1] - aux2[1]) >= 0)
  if case['hmode']: rec['math_late'] = card.aux(TILE, 2, 'trisc1')[1]

  if case['mode'] == 0:
    per = {}
    i = 0
    for s in range(SAMPLES):
      for c in counts:
        if not c: continue
        per.setdefault(c, []).append((log[i], log[i + 1]))
        i += 2
    med_t = {c: median(t for _, t in v[1:]) for c, v in per.items()}
    med_i = {c: median(t for t, _ in v[1:]) for c, v in per.items()}
    cs = sorted(med_t)
    slope = (med_t[cs[-1]] - med_t[cs[0]]) / (cs[-1] - cs[0])
    rec.update(samples={str(c): v for c, v in per.items()}, median_total={str(c): m for c, m in med_t.items()},
               median_issue={str(c): m for c, m in med_i.items()}, median=slope, per_unit=slope,
               per_unit_issue=(med_i[cs[-1]] - med_i[cs[0]]) / (cs[-1] - cs[0]),
               steps=[(med_t[b] - med_t[a]) / (b - a) for a, b in zip(cs, cs[1:])],
               fixed=med_t[cs[0]] - slope * cs[0])
  elif case['mode'] == 1:
    s = [log[4 * i:4 * i + 4] for i in range(SAMPLES)]
    issue = [_s32(b - a) for a, b, _, _ in s]
    idle = [_s32(c - a) for a, _, c, _ in s]
    seen = [_s32(d - a) for a, _, _, d in s]
    rec.update(raw=s, issue=issue, idle=idle, seen=seen, median=median(seen[1:]), median_idle=median(idle[1:]))
    if case['vis'] & 2:
      nb = card.iface.read32(TILE, res('brisc') + 8)
      bl = card.log(TILE, nb, 'brisc')
      noc = []
      for i in range(SAMPLES):
        fires, vals = bl[128 * i:128 * i + 64], bl[128 * i + 64:128 * i + 128]
        new = [j for j, v in enumerate(vals) if v != SENT]
        if new and all(vals[j] != SENT for j in range(new[0], 64)):
          j = new[0]
          noc.append(dict(first_new_fire=_s32(fires[j] - s[i][0]), last_old_fire=_s32(fires[j - 1] - s[i][0]) if j else None))
        else: noc.append(dict(first_new_fire=None, new=new[:8]))
      rec['noc'] = noc
      ok = [x['first_new_fire'] for x in noc[1:] if x['first_new_fire'] is not None]
      rec['median_noc_first_new'] = median(ok) if ok else None
  else:
    t = list(log)
    if case['hmode'] == 1:
      posts = card.log(TILE, case['n'], 'trisc1')
      lat = [_s32(b - a) for a, b in zip(posts, t)]
      rec.update(posts=list(posts), done=t, latency=lat, median=median(lat[2:]))
    else:
      d = [_s32(b - a) for a, b in zip(t, t[1:])]
      rec.update(done=t, period=d, median=median(d[4:]))
      if case['hmode'] == 2: rec['posts'] = list(card.log(TILE, case['n'], 'trisc1'))
  return rec


def selftest():
  """Encodings in pack.h against ttrv.isa, and reference sanity (python3 sims/probes/pack.py; no hardware)."""
  import subprocess, sys, tempfile
  sys.path.insert(0, str(HERE.parents[1]))
  from ttrv.isa import tensix as T
  want = {
    'TT_PACR(1, 0, 1)': T('PACR', AddrMode=1, Last=1), 'TT_PACR(3, 3, 0)': T('PACR', AddrMode=3, ReadIntfSel=3),
    'TT_SETADC(4, 1, 3, 5)': T('SETADC', CntSetMask=4, ChannelIndex=1, DimensionIndex=3, Value=5),
    'TT_SETADCXX(4, 15, 0)': T('SETADCXX', CntSetMask=4, x_end2=15),
    'TT_SETADCXY(4, 0, 0, 0, 0, 0xB)': T('SETADCXY', CntSetMask=4, BitMask=11),
    'TT_SETADCZW(4, 0, 0, 0, 0, 5)': T('SETADCZW', CntSetMask=4, BitMask=5),
    'TT_STALLWAIT(0x80, 9)': T('STALLWAIT', stall_res=128, wait_res=9),
    'TT_SEMWAIT(1, 2, 1)': T('SEMWAIT', stall_res=1, sem_sel=2, wait_sem_cond=1),
    'TT_SEMPOST(2)': T('SEMPOST', sem_sel=2), 'TT_SEMGET(2)': T('SEMGET', sem_sel=2),
    'TT_SEMINIT(2, 0, 2)': T('SEMINIT', max_value=2, sem_sel=2),
    'TT_ZEROACC(3, 1, 0, 1, 0)': T('ZEROACC', clear_mode=3, use_32_bit_mode=1, addr_mode=1),
    'TT_WRCFG(12, 0, 69)': T('WRCFG', GprAddress=12, CfgReg=69), 'TT_MOP(1, 0, 0)': T('MOP', mop_type=1),
    'TT_SETDMAREG16(25, 0x8001)': T('SETDMAREG', Payload_SigSelSize=2, Payload_SigSel=1, RegIndex16b=25),
    'TT_SFPLOADI(0, 0, 0xBF80)': T('SFPLOADI', imm16=0xBF80),
    'TT_SFPSTORE(0, 3, 0, 66)': T('SFPSTORE', instr_mod0=3, dest_reg_addr=66),
    'TT_SFPSHFT(-9, 0, 1, 1)': T('SFPSHFT', imm12_math=0xFF7, lreg_dest=1, instr_mod1=1),
    'TT_SFPSHFT(16, 15, 1, 5)': T('SFPSHFT', imm12_math=16, lreg_c=15, lreg_dest=1, instr_mod1=5),
    'TT_SFPIADD(0, 1, 0, 4)': T('SFPIADD', lreg_c=1, instr_mod1=4),
    'TT_UNPACR(0, 0, 1, 0, 1)': T('UNPACR', OvrdThreadId=1, Last=1),
    'TT_SFPNOP': T('SFPNOP'), 'TT_NOP': T('NOP'), 'TT_DMANOP': T('DMANOP'),
    'TT_RMWCIB(2, 0x80, 0, 71)': T('RMWCIB2', Mask=0x80, CfgRegAddr=71),
    'TT_REPLAY(0, 16, 0, 1)': T('REPLAY', len=16, load_mode=1),
  }
  macros = [l for l in (HERE / 'pack.h').read_text().splitlines()]
  src = ['typedef unsigned int u32;', '#include <stdio.h>']
  keep, cont = [], False
  for l in macros:  # just the TT_ encoding macros, without the RISC-V parts of probe.h
    if l.startswith('#define TT_') or cont: keep.append(l); cont = l.endswith('\\')
  src += keep + ['int main(void) {'] + [f'  printf("%u\\n", (u32)({e}));' for e in want] + ['  return 0;', '}']
  with tempfile.TemporaryDirectory() as d:
    c, exe = Path(d) / 't.c', Path(d) / 't'
    c.write_text('\n'.join(src))
    subprocess.run(['cc', '-o', str(exe), str(c)], check=True)
    got = [int(x) for x in subprocess.run([str(exe)], capture_output=True, text=True, check=True).stdout.split()]
  bad = 0
  for (e, w), g in zip(want.items(), got):
    if g != w: bad += 1; print(f'MISMATCH {e}: {g:#010x} != ttrv {w:#010x}')
  print(f'{len(want) - bad}/{len(want)} encodings match ttrv.isa')
  for fmt, (_, pat, *_rest) in FORMATS.items():
    b = dst_bits(pat, 3)
    out = encode(fmt, b)
    assert len(out) == unit_bytes(fmt, 64), fmt
    assert SENT.to_bytes(4, 'little') not in [out[i:i + 4] for i in range(0, len(out), 4)], fmt
  print(f'{len(CASES)} cases:', {g: sum(c["group"] == g for c in CASES) for g in dict.fromkeys(c["group"] for c in CASES)})
  return bad


if __name__ == '__main__':
  raise SystemExit(selftest())
