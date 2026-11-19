"""Two-tile timing (k_ping.c): clock offsets between tiles, one-way inline-write latency, atomic round trip and
semaphore visibility (what attention's cross-core sync costs).

clock: inline writes A->B on NoC0 and B->A on NoC1. Both paths have the same hop counts (NoC1 is NoC0 mirrored), so
  offset(B - A) = (d_ab - d_ba) / 2 and one-way = (d_ab + d_ba) / 2, with d = t_seen(receiver clock) - t_fire(sender).
atomic: non-posted atomic increment, sender polls ATOMIC_RESP (round trip); receiver logs when the word changes,
  corrected by the clock offset (one-way visibility). Posted atomics: visibility only.
"""
from statistics import median

from tile import build

A = (1, 2)
PEERS = [(2, 2), (4, 5), (1, 11), (13, 9), (7, 6)]
SITES = {1: 'cmd_ready', 2: 'flag', 3: 'atomic_resp'}
OPS = {'inline': 0, 'atomic_posted': 1, 'atomic_np': 2}
COUNT, PERIOD = 32, 3000
FLAG = 0x40000


def coord(t): return t[0] | t[1] << 6


def one_way(card, src, dst, noc, op, timeout):
  img = build('k_ping.c')
  card.run([(dst, img, [1, 0, 0, COUNT], {FLAG: bytes(8)}),
            (src, img, [0, noc, coord(dst), COUNT, PERIOD, OPS[op], 0], {FLAG: bytes(8)})], timeout, SITES)
  s, r = card.log(src, 2 * COUNT), card.log(dst, 2 * COUNT)
  fire, resp = s[0::2], s[1::2]
  value, seen = r[0::2], r[1::2]
  if op == 'inline' and list(value) != list(fire): raise RuntimeError('receiver saw values the sender did not send')
  s32 = lambda x: (x & 0xFFFFFFFF) - (1 << 32) if x & 0x80000000 else x & 0xFFFFFFFF
  d = [s32(b - a) for a, b in zip(fire, seen)][2:]
  rt = [s32(b - a) for a, b in zip(fire, resp)][2:] if op == 'atomic_np' else None
  return d, rt


def _cases():
  for p in PEERS:
    yield dict(id=f'clock-{p[0]}_{p[1]}', kind='clock', peer=p, tiles=[A, p])
  for op in ('atomic_np', 'atomic_posted'):
    for p in PEERS[:3]:
      for noc in (0, 1):
        yield dict(id=f'{op}-{p[0]}_{p[1]}-noc{noc}', kind='atomic', op=op, peer=p, noc=noc, tiles=[A, p])


CASES = list(_cases()) + [dict(id='clockmap', kind='clockmap', tiles=[A])]
OFFSETS = {}  # peer -> clock(peer) - clock(A), from the clock cases (rerun them first in a new session)


def offset(card, t, timeout=0.25):
  """clock(t) - clock(A), measured once per session (cached on the card)."""
  cache = card.__dict__.setdefault('clock_offsets', {A: 0.0})
  if t not in cache:
    d_ab, _ = one_way(card, A, t, 0, 'inline', timeout)
    d_ba, _ = one_way(card, t, A, 1, 'inline', timeout)
    cache[t] = (median(d_ab) - median(d_ba)) / 2
  return cache[t]


def run(card, case, timeout):
  if case['kind'] == 'clockmap':
    offs = {f'{t[0]},{t[1]}': offset(card, t, timeout) for t in sorted(card.workers)}
    return dict(offsets=offs, distinct=sorted(set(offs.values())))
  p = case['peer']
  if case['kind'] == 'clock':
    d_ab, _ = one_way(card, A, p, 0, 'inline', timeout)
    d_ba, _ = one_way(card, p, A, 1, 'inline', timeout)
    ab, ba = median(d_ab), median(d_ba)
    OFFSETS[p] = (ab - ba) / 2
    return dict(d_ab=ab, d_ba=ba, offset=(ab - ba) / 2, one_way=(ab + ba) / 2,
                spread_ab=max(d_ab) - min(d_ab), spread_ba=max(d_ba) - min(d_ba), samples_ab=d_ab, samples_ba=d_ba)
  if p not in OFFSETS: run(card, dict(case, kind='clock'), timeout)
  d, rt = one_way(card, A, p, case['noc'], case['op'], timeout)
  off = OFFSETS[p]
  vis = [x - off for x in d]
  rec = dict(offset=off, visible_median=median(vis), visible_min=min(vis), visible_max=max(vis), visible=vis)
  if rt: rec.update(rtt_median=median(rt), rtt_min=min(rt), rtt_max=max(rt), rtt=rt)
  return rec
