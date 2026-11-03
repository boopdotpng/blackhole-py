"""E3: generalized full-chip patterns. Each case is a JSON dict:
  cores: int (default 117)       per: bytes per stream (default 2 MiB)
  slots: list of per-slot specs, slot 0 = BRISC, slot 1 = NCRISC; each spec:
     dir: read|write   noc: 0|1|'alt'   ports: table|spread|p0|p1|p2
     banks: list of bank ids (default all 8)   bytes_scale: float (default 1)
     vc: int|None (static VC; None = dynamic)  prio: int
  core_filter: 'all' | 'first' (first N in runtime order) | 'even' etc.
"""
import sys, json
from dataclasses import replace
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
import dramx
from dramx import Bench, ep, pack, ROLES
from pcie import P150_DRAM_ENDPOINTS as TABLE
from asm import Asm
from tests.movement import test_noc as n
from tests.movement.noc import InterleavedConfig, emit_interleaved_dram_to_l1, emit_l1_to_interleaved_dram


class Bench3(Bench):
  def image(self, slot, direction, noc, coords, posted, vc=1, prio=0):
    key = (slot, direction, noc, coords, posted, vc, prio)
    if key not in self._cache:
      cfg = InterleavedConfig(tuple(pack(c) for c in coords),
                              n.CB_ADDRESS + slot * self.batch * self.page, self.batch, self.page,
                              noc, command_slot=1 + slot, tid=1 + slot,
                              batch_pages=self.batch, standalone=True, posted_write=posted,
                              static_vc=vc, priority=prio)
      a = Asm(ROLES[slot])
      stamp = n.TIMING_L1_ADDRESS + slot * 16
      n._record_clock(a, stamp)
      (emit_interleaved_dram_to_l1 if direction == 'read' else emit_l1_to_interleaved_dram)(a, cfg, slot * 2, slot * 2 + 1)
      n._record_clock(a, stamp + 8)
      self._cache[key] = a.lower()
    return self._cache[key]

  def run(self, plan, runs=3, label=None):
    # patch: pass vc/prio through
    orig = self.image
    return super().run(plan, runs, label)


def coords(banks, noc, ports, k):
  r = []
  for bk in banks:
    if ports == 'table': r.append(TABLE[bk][noc])
    elif ports == 'spread': r.append(ep(bk, (k + bk) % 3))
    else: r.append(ep(bk, int(ports[1])))
  return r


def build(b, case, base):
  N = case.get('cores', 117); PER = case.get('per', 2 << 20)
  plan = {}
  k = 0
  offs = {}  # per-bank allocation cursor (bytes in each bank)
  for i, core in enumerate(b.cores[:N]):
    ss = []
    for slot, spec in enumerate(case['slots']):
      if spec is None: continue
      noc = spec['noc'] if spec['noc'] != 'alt' else (i + slot) % 2
      banks = spec.get('banks', list(range(8)))
      rot = k % len(banks)
      banks = banks[rot:] + banks[:rot]
      nbytes = int(PER * spec.get('bytes_scale', 1)) // (len(banks) * b.page) * (len(banks) * b.page)
      key = tuple(sorted(banks))
      cur = offs.get(key, 0); offs[key] = cur + nbytes // len(banks)
      # different bank sets must not overlap: give each bank-set its own window
      window = hash(key) % 4 * (64 << 20) if len(offs) > 1 or len(banks) < 8 else 0
      ss.append(dict(slot=slot, dir=spec['dir'], noc=noc, coords=coords(banks, noc, spec.get('ports', 'table'), k),
                     addr=base + window + cur, bytes=nbytes, posted=spec.get('posted', False),
                     vc=spec.get('vc', 1), prio=spec.get('prio', 0), tag=spec.get('tag', spec['dir'])))
      k += 1
    plan[core] = ss
  return plan


def main():
  dev = int(sys.argv[1]); out = sys.argv[2]; cases = json.load(open(sys.argv[3]))
  b = Bench3(dev)
  # route vc/prio into image(): wrap
  real = b.image
  rows = []
  try:
    base = b.region(256 << 20)
    for case in cases:
      pg = case.get('page', 2048)
      if pg != b.page:
        b.page = pg; b.batch = max(1, 32 * 2048 // pg); b._cache.clear(); real = b.image
      plan = build(b, case, base)
      # monkeypatch stream->image call to include vc/prio
      def img(slot, d, noc, c, posted, _p=plan):
        return real(slot, d, noc, c, posted, *img.extra.pop(0))
      img.extra = [(s['vc'], s['prio']) for ss in plan.values() for s in ss]
      b.image = img
      rows.append(b.run(plan, label=case.get('name', case)))
      b.image = real
      json.dump(rows, open(out, 'w'), indent=1)
  finally:
    b.close()


if __name__ == '__main__':
  main()
