"""NoC event timing (k_events.c): issue cost, counter latencies (posted sent, non-posted sent, ack, read sent,
read response), and back-to-back streams. One tile, SRC; targets only receive (their RISCs are not involved).

  python3 sims/probes/run.py --device 1 --output sims/results/<date>-noc-events-card1.jsonl events
"""
from statistics import median

from tile import build

SRC = (1, 2)
SITES = {1: 'setup_ready', 2: 'cmd_ready', 3: 'counter', 4: 'drain_ready'}
COUNTER = {'ack': 1, 'rd_resp': 2, 'accepted': 4, 'rd_sent': 5, 'np_sent': 0xA, 'p_sent': 0xB}
RESP_MARKED = 1 << 4
SINGLE = [('write', True, 'p_sent'), ('write', False, 'np_sent'), ('write', False, 'ack'),
          ('read', False, 'rd_sent'), ('read', False, 'rd_resp')]
STREAM = [('write', True, 'p_sent'), ('write', False, 'ack'), ('read', False, 'rd_resp')]
TARGETS = [(2, 2), (15, 2), (1, 11), (4, 5)]
SIZES = (64, 256, 1024, 4096, 16384)
REPS, STREAM_COUNT, STREAM_RUNS, PERIOD = 32, 64, 4, 4000


def _cases():
  for op, posted, counter in SINGLE:
    for size in SIZES:
      for t in TARGETS:
        for noc in (0, 1):
          yield dict(id=f'single-{op}-{"p" if posted else "np"}-{counter}-{size}-{t[0]}_{t[1]}-noc{noc}', kind='single',
                     op=op, posted=posted, counter=counter, size=size, dst=t, noc=noc, tiles=[SRC, t])
  for op, posted, counter in STREAM:
    for size in sorted(SIZES + (16, 32, 128, 512, 2048, 8192)):
      for noc in (0, 1):
        yield dict(id=f'stream-{op}-{"p" if posted else "np"}-{counter}-{size}-noc{noc}', kind='stream',
                   op=op, posted=posted, counter=counter, size=size, dst=(2, 2), noc=noc, tiles=[SRC, (2, 2)])


CASES = list(_cases())


def _s32(x): return x - (1 << 32) if x >= 1 << 31 else x


def run(card, case, timeout):
  image = build('k_events.c')
  single = case['kind'] == 'single'
  ctrl = 0 if case['posted'] else RESP_MARKED
  count = REPS if single else STREAM_COUNT
  params = [0 if single else 1, case['noc'], 0 if case['op'] == 'write' else 1, ctrl, COUNTER[case['counter']],
            case['dst'][0] | case['dst'][1] << 6, case['size'], count, PERIOD, 0]
  if single:
    card.run([(SRC, image, params, None)], timeout, SITES)
    w = card.log(SRC, 2 * REPS)
    d = [_s32((w[2 * i + 1] - w[2 * i]) & 0xFFFFFFFF) for i in range(REPS)][2:]
    return dict(min=min(d), median=median(d), max=max(d), samples=d)
  runs = []
  for _ in range(STREAM_RUNS):
    card.run([(SRC, image, params, None)], timeout, SITES)
    w = card.log(SRC, count + 1)
    issue = [_s32((b - a) & 0xFFFFFFFF) for a, b in zip(w, w[1:count])]
    runs.append(dict(issue_median=median(issue), issue_min=min(issue), issue_max=max(issue), issue=issue,
                     total=_s32((w[count] - w[0]) & 0xFFFFFFFF)))
  tot = [r['total'] for r in runs]
  return dict(count=count, totals=tot, total_median=median(tot), bytes_per_cycle=case['size'] * count / median(tot),
              runs=runs)
