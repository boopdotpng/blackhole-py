import sys
sys.path.insert(0, __import__('os').path.dirname(__file__))
import dramx
_orig = dramx.Bench.__init__
def init(self, *a, **k):
  _orig(self, *a, **k)
  p = self.d.pcie
  n = (p.tensix_enabled & 0x3FFF).bit_count() * 10
  if n == 140:
    svc = {p.prefetch_core, p.dispatch_core, p.dram_core}
    extra = [(x, y) for x in (14, 15, 16) for y in range(2, 12) if (x, y) not in p.cores and (x, y) not in svc]
    p.cores.extend(extra)
  self.cores = self.d.cores
  print('tensix', n, 'workers', len(self.cores), file=sys.stderr)
dramx.Bench.__init__ = init
