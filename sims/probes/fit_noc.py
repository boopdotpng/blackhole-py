"""Score NoC parameter variants (ttrv.cycle_noc.P) on recorded stream probes: fit_noc.py JSON CAPTURE..."""
import sys, gzip, json
from statistics import median
from multiprocessing import Pool
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[2]))
import ttrv.cycle_noc as N
from ttrv import build
from ttrv.cycles import estimate

def run(job):
  params, src, bindings, meas = job
  N.P.update(params)
  rep = estimate(build(src), bindings=bindings, sample_iterations=None)
  out = []
  for t in rep['tiles']:
    m = meas[f"{t['x']},{t['y']}"]
    out.append(100 * (t['cores']['brisc']['cycles'] / m - 1))
  return out

if __name__ == '__main__':
  params = json.loads(sys.argv[1])
  jobs, names = [], []
  for f in sys.argv[2:]:
    for r in map(json.loads, gzip.open(f)):
      src = r.get('source')
      if not src: continue
      meas = {f"{c['x']},{c['y']}": c['measured'] for c in r['cores']}
      jobs.append((params, src, {'w': r['w']}, meas)); names.append(r['name'])
  with Pool(min(10, len(jobs))) as p:
    res = p.map(run, jobs)
  allerr = []
  for n, e in zip(names, res):
    a = sorted(abs(x) for x in e); allerr += a
    print(f"{n:12s} within3 {sum(x<=3 for x in a):3d}/{len(a)}  med|e| {a[len(a)//2]:5.2f}  signed med {median(e):+6.2f}  worst {a[-1]:5.1f}")
  allerr.sort(); print('TOTAL', sum(x<=3 for x in allerr), '/', len(allerr), 'med', round(allerr[len(allerr)//2],2))
