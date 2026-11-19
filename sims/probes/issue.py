"""Command issue cost and command-buffer occupancy (k_issue.c), single tile SRC.

Varies: fences around the send, whether the per-page address registers are rewritten, polling for ready right after
the send (the llama exports' pattern, which also logs how long the buffer stays busy), and 1/2/4 command buffers on
one NoC (do several buffers raise the command rate, or do they share one queue?).
Ops: posted 64 B write to tile (2,2), and 2 KiB non-posted write / read / 64 B read against DRAM (port 0).
"""
from statistics import median

from tile import build

SRC = (1, 2)
SITES = {1: 'cmd_ready', 2: 'done'}
OPS = {'posted64-tile': (0, 64, False), 'npwrite2k-dram': (1, 2048, False), 'read2k-dram': (2, 2048, True),
       'read64-dram': (2, 64, True), 'posted2k-tile': (0, 2048, False)}
T = 2 | 2 << 6
COUNT = 256


def _cases():
  for op in OPS:
    for fences in ('both', 'none'):
      for regs in (0, 1):
        for poll in (0, 1):
          for nbuf in (1, 2, 4):
            if nbuf > 1 and poll: continue
            yield dict(id=f'issue-{op}-fence_{fences}-regs{regs}-poll{poll}-buf{nbuf}', op=op, fences=fences, regs=regs,
                       poll=poll, nbuf=nbuf, tiles=[SRC])


CASES = list(_cases())


def run(card, case, timeout):
  op, size, read = OPS[case['op']]
  dram = case['op'].endswith('dram')
  flags = (3 if case['fences'] == 'both' else 0) | 4 * case['poll'] | 8 * case['regs']
  params = [flags, COUNT, size, T, int(dram), op, case['nbuf'], 0]
  card.run([(SRC, build('k_issue.c'), params, None)], timeout, SITES)
  a = card.aux(SRC, 3)
  s32 = lambda x: (x & 0xFFFFFFFF) - (1 << 32) if x & 0x80000000 else x & 0xFFFFFFFF
  interval = s32(a[1] - a[0]) / (COUNT - 1)
  total = s32(a[2] - a[0])
  rec = dict(issue_interval=round(interval, 2), total=total, bytes_per_cycle=COUNT * size / total)
  if case['poll']:
    busy = card.log(SRC, COUNT)[8:]
    rec.update(busy_median=median(busy), busy_min=min(busy), busy_max=max(busy))
  return rec
