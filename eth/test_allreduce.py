# Two-card all-reduce: correctness against numpy, bit-identical outputs on both cards, and time per all-reduce.
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
from tp import Link, allreduce_kernel
from ttrv import Device, Var

DIM, N, REPLAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 4096, 8, 50
def bf16(x):
  u = x.astype(np.float32).view(np.uint32).astype(np.uint64)
  return ((u + 0x7FFF + (u >> 16 & 1)) >> 16).astype(np.uint16)
def f32(b): return (b.astype(np.uint32) << 16).view(np.float32)

rng = np.random.default_rng(0)
parts = [[bf16(rng.standard_normal(DIM)) for _ in range(N)] for _ in range(2)]
res = [bf16(rng.standard_normal(DIM)) for _ in range(N)]
want = [bf16((f32(parts[0][i]) + f32(parts[1][i])) + f32(res[i])) for i in range(N)]

devs = [Device(0), Device(1)]
link = Link(devs)
graphs, outs = [], []
step = Var("step")
for r, d in enumerate(devs):
  k = allreduce_kernel(d, link, dim=DIM, rank=r, nslot=N)
  P = [d.empty(DIM, "bf16").copy_from(parts[r][i]) for i in range(N)]
  R = [d.empty(DIM, "bf16").copy_from(res[i]) for i in range(N)]
  O = [d.zeros(DIM, "bf16") for _ in range(N)]
  with d.graph() as g:
    for i in range(N): k(partial=P[i], residual=R[i], output=O[i], step=step, slot=i)
  graphs.append(g); outs.append(O)

ev = [g(step=1) for g in graphs]
for e in ev: e.wait(5)
ok = all(np.array_equal(outs[r][i].numpy(), want[i]) for r in range(2) for i in range(N))
print("replay 1:", "match" if ok else "MISMATCH", link.status(0), link.status(1))
if not ok:
  for r in range(2):
    got = outs[r][0].numpy(); bad = np.nonzero(got != want[0])[0]
    print(f"card {r}: {len(bad)} bad, first {bad[:8]} got {got[bad[:4]]} want {want[0][bad[:4]]}")
  sys.exit(1)

t = time.perf_counter()
for s in range(2, REPLAYS + 2):
  ev = [g(step=s) for g in graphs]
for e in ev: e.wait(10)
dt = time.perf_counter() - t
ok = all(np.array_equal(outs[r][i].numpy(), want[i]) for r in range(2) for i in range(N))
print(f"{REPLAYS} replays x {N} all-reduces of {DIM}: {dt / REPLAYS / N * 1e6:.1f} us each, {'match' if ok else 'MISMATCH'}")
print(link.status(0), link.status(1))
link.close()
