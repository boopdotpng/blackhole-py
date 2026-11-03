"""Correctness spot-check of seg pattern (R NoC0 spread banks 0-3, W NoC1 spread banks 4-7)."""
import sys, json
sys.path.insert(0, __import__('os').path.dirname(__file__))
from exp3 import Bench3, build
from pcie import TLBWindow
from tests.movement import test_noc as n
b = Bench3(int(sys.argv[1]))
R=lambda **k: dict(dir='read',**k); W=lambda **k: dict(dir='write',**k)
case = dict(per=256 << 10, slots=[R(noc=0,ports='spread',banks=[0,1,2,3]),W(noc=1,ports='spread',banks=[4,5,6,7])])
PAT = bytes(range(256)) * 8
RP = bytes((i * 7 + 3) & 255 for i in range(2048))
try:
  base = b.region(256 << 20)
  plan = build(b, case, base)
  def span(dirn):
    out = {}
    for ss in plan.values():
      for s in ss:
        if s['dir'] == dirn:
          for x, y in s['coords']:
            bank = (x - 17) * 4 + (y - 12) // 3
            lo, hi = s['addr'], s['addr'] + s['bytes'] // len(s['coords'])
            a, z = out.get(bank, (lo, hi)); out[bank] = (min(a, lo), max(z, hi))
    return out
  ws, rs = span('write'), span('read')
  ep = lambda bank: b.d.pcie.dram_endpoints[bank][0]
  def io(bank, lo, hi, data=None):
    got = bytearray()
    with TLBWindow(b.d.pcie.fd, ep(bank)) as w:
      off = lo
      while off < hi:
        bs = off & -TLBWindow.SIZE; sz = min(hi - off, TLBWindow.SIZE - (off - bs))
        w.target(bs, ep(bank))
        if data is None: got += w.read(off - bs, sz)
        else: w.write(off - bs, data[off - lo:off - lo + sz])
        off += sz
    return bytes(got)
  for bank, (lo, hi) in ws.items(): io(bank, lo, hi, b'\xa5' * (hi - lo))
  for bank, (lo, hi) in rs.items(): io(bank, lo, hi, RP * ((hi - lo) // 2048))
  # run with real vc/prio wiring as exp3.main does
  real = b.image
  def img(slot, d, noc, c, posted):
    return real(slot, d, noc, c, posted, *img.extra.pop(0))
  img.extra = [(s['vc'], s['prio']) for ss in plan.values() for s in ss]
  b.image = img
  row = b.run(plan, runs=1, label='validate')
  for bank, (lo, hi) in ws.items():
    got = io(bank, lo, hi)
    assert got == PAT * ((hi - lo) // 2048), ('write mismatch bank', bank)
    print('bank', bank, 'write range OK', (hi - lo) >> 10, 'KiB')
  bad = 0
  with TLBWindow(b.d.pcie.fd, b.cores[0]) as w:
    for core in plan:
      w.target(0, core)
      if w.read(n.CB_ADDRESS, 32 * 2048) != RP * 32: bad += 1
  print('read staging mismatches:', bad, 'of', len(plan))
finally:
  b.close()
