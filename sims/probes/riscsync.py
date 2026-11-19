"""RISC <-> RISC handshakes and RISC L1 access under traffic, on one tile (1,2). See RISCSYNC.md.

  python3 sims/probes/run.py --device 1 --output sims/results/<date>-riscsync-card1.jsonl riscsync

hs-<mode>-<a>-<b>: k_handshake.c ping-pong between roles a (initiator) and b. one_way = cycles per round trip / 2,
  which includes the poll loop of the waiting side (what a kernel pays).
l1lat-<kind>-<role>-<companions>: k_l1chase.c on `role` (dependent L1 load chase, or fetch-bound straight-line code)
  while companions stream L1 traffic: noc = BRISC NoC0 self-loop 8 KiB posted writes (reads and writes this L1),
  noc2 = + NCRISC on NoC1, unpack = TRISC0 unpacker 0 streaming a bf16 face (k_pack_unp.c).
"""
from statistics import median

import unpack
from tile import build

TILE = (1, 2)
L1A, L1B = 0x40000, 0x40040
def stream_reg(stream, reg): return 0xFFB40000 + stream * 0x1000 + 4 * reg
SEM = lambda i: 0xFFE80020 + 4 * i  # noqa: E731
N, SAMPLES, WARM = 64, 7, 16

CASES = []
PAIRS = [('brisc', 'ncrisc'), ('ncrisc', 'brisc'), ('brisc', 'trisc0'), ('brisc', 'trisc2'), ('ncrisc', 'trisc0'),
         ('ncrisc', 'trisc2'), ('trisc0', 'trisc1'), ('trisc1', 'trisc2'), ('trisc2', 'trisc0')]
for mode, words in (('l1', (L1A, L1B)), ('stream', (stream_reg(8 + 30, 8), stream_reg(8 + 31, 8)))):
  for a, b in PAIRS:
    CASES.append(dict(id=f'hs-{mode}-{a}-{b}', group='handshake', mode=mode, roles=[a, b], words=list(words),
                      tiles=[TILE]))
for a, b in (('trisc0', 'trisc1'), ('trisc1', 'trisc2'), ('trisc2', 'trisc0')):
  CASES.append(dict(id=f'hs-sem-{a}-{b}', group='handshake', mode='sem', roles=[a, b], words=[SEM(0), SEM(2)],
                    tiles=[TILE]))

COMPANIONS = {'none': (), 'noc': ('brisc',), 'noc2': ('brisc', 'ncrisc'), 'unpack': ('trisc0',),
              'noc+unpack': ('brisc', 'trisc0')}
for kind in ('chase', 'fetch'):
  for role in ('ncrisc', 'trisc1'):
    for comp, used in COMPANIONS.items():
      if role in used: continue
      CASES.append(dict(id=f'l1lat-{kind}-{role}-{comp}', group='l1lat', kind=kind, role=role, companions=comp,
                        tiles=[TILE], timeout=1.0))

FL_DONE, PK_FLAGS, PK_STOP = unpack.U_FLAGS + 4, 0x40200, 0x40210
RING, UNP_SRC = 0x150000, 0x168000


def _run_hs(card, case, timeout):
  a, b = case['roles']
  m = {'l1': 0, 'stream': 1, 'sem': 2}[case['mode']]
  wa, wb = case['words']
  img = {r: build('k_handshake.c', r) for r in (a, b)}
  params = {a: [m, 1, wa, wb, N, SAMPLES, WARM], b: [m, 0, wa, wb, N, SAMPLES, WARM]}
  card.run([(TILE, img, params, {L1A: bytes(0x80)})], timeout)
  w = card.log(TILE, 2 * SAMPLES, a)
  rt = [((w[2 * i + 1] - w[2 * i]) & 0xFFFFFFFF) / N for i in range(SAMPLES)]
  return dict(round_trip=rt, median=median(rt) / 2, unit='cycles one way (round trip / 2)')


def _run_l1lat(card, case, timeout):
  role, comp = case['role'], case['companions']
  mode, count = (0, 4096) if case['kind'] == 'chase' else (1, 32)
  imgs, params, stops = {}, {}, []
  l1 = {unpack.U_FLAGS: bytes(0x40), PK_FLAGS: bytes(0x100), UNP_SRC: bytes(512)}
  tag = dict(UNPACK_TAG=f'0x{unpack._hdr_tag()[:8]}')
  if 'noc' in comp:
    imgs['brisc'] = build('k_unpack_noc.c', 'brisc', **tag)
    params['brisc'] = [0, 0, 8192, 0, unpack.NOC_BUF + 0x8000, 200000, unpack.NOC_BUF, 0]
    stops = [FL_DONE]
  if comp == 'noc2':
    imgs['ncrisc'] = build('k_unpack_noc.c', 'ncrisc', **tag)
    params['ncrisc'] = [0, 1, 8192, 0, unpack.NOC_BUF + 0xC000, 200000, unpack.NOC_BUF + 0x4000, 0]
  if 'unpack' in comp:
    imgs['trisc0'], params['trisc0'] = build('k_pack_unp.c', 'trisc0'), [UNP_SRC, 1 << 24]
    stops.append(PK_STOP)
  imgs[role] = build('k_l1chase.c', role)
  params[role] = [mode, count, RING, 20000, *(stops + [0, 0])[:2]]
  card.run([(TILE, imgs, params, l1)], timeout)
  w = card.log(TILE, 12, role)
  per = [((w[2 * i + 1] - w[2 * i]) & 0xFFFFFFFF) / (count if mode == 0 else count * 1025) for i in range(6)]
  rec = dict(samples=per, median=median(per[1:]), unit='cycles per load' if mode == 0 else 'cycles per instruction')
  if 'noc' in comp: rec['noc_log'] = list(card.log(TILE, 4, 'brisc'))
  if 'unpack' in comp: rec['unpack_aux'] = list(card.aux(TILE, 3, 'trisc0'))
  return rec


def run(card, case, timeout):
  return _run_hs(card, case, timeout) if case['group'] == 'handshake' else _run_l1lat(card, case, timeout)
