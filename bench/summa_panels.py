"""Checks prefill/summa_projection.ttrv at many panel counts on Nanbeige's projection shapes: output against the
two-panel kernel (the batched decode path) run slice by slice, plus time per launch. Stops at the first hang.

  PYTHONPATH=. python3 bench/summa_panels.py --panels 4 8 16 20 [--layer 0] [--device 0]
"""
import argparse, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ttrv import Device, hw
from examples.nanbeige import DEFAULT, load_checkpoint
from examples.prefill import summa_shapes

ap = argparse.ArgumentParser()
ap.add_argument("--panels", type=int, nargs="+", default=[4, 8, 16, 20])
ap.add_argument("--layer", type=int, default=0)
ap.add_argument("--device", type=int, default=0)
ap.add_argument("--only", default="", help="substring of the projection names to test")
a = ap.parse_args()
KERNEL = Path("examples/prefill/summa_projection.ttrv")
dev = Device(a.device)
try:
  cfg, _, w, packed = load_checkpoint(DEFAULT, dev)
  rng = np.random.default_rng(0)
  layer = f"model.layers.{a.layer}."
  names = [layer + n for n in ("self_attn.q_proj.weight", "self_attn.o_proj.weight", "mlp.gate_proj.weight", "mlp.down_proj.weight")]
  for name in [n for n in names if a.only in n]:
    buf, k, n, bits, group, second, third, pad = packed[name]
    swiglu = "gate_proj" in name
    width = n // 2 if swiglu else n
    epi = dict(SWIGLU=1) if swiglu else dict(SECOND=0, THIRD=0)  # fused q|k|v as one output
    maxp = max(a.panels)
    x = dev.array((rng.standard_normal(maxp * 32 * k) * 0.5).astype(np.float32), "bf16")
    def kernel(p):
      for shape in summa_shapes(k, n, bits, group, p, swiglu, hw.L1_SIZE - dev.top):
        try: return dev.kernel(KERNEL, K=k, N=n, BITS=bits, GROUP=group, PAD=pad, PANELS=p, **epi, **shape), shape
        except Exception as e:
          if "overflow" not in str(e) and "exhausted" not in str(e): raise
      return None, None
    two, _ = kernel(2)
    ref = dev.empty(maxp * 32 * width, "bf16")
    for s in range(0, maxp, 2):   # reference: two panels at a time
      two(x=x.page_view(2 * s * 32 * k, 64 * k), weights=buf, output=ref.page_view(2 * s * 32 * width, 64 * width)).wait(10)
    want = ref.numpy().astype(np.uint32) << 16
    want = want.view(np.float32)
    for p in a.panels:
      kern, shape = kernel(p)
      if kern is None: print(f"{name.split('.')[-2]:10s} panels {p:2d}: no shape fits"); continue
      out = dev.zeros(maxp * 32 * width, "bf16")
      try:
        kern(x=x, weights=buf, output=out).wait(10)
        t = time.perf_counter()
        for _ in range(3): kern(x=x, weights=buf, output=out).wait(10)
        dt = (time.perf_counter() - t) / 3
      except TimeoutError:
        print(f"{name.split('.')[-2]:10s} panels {p:2d} {shape}: HANG"); raise SystemExit(1)
      got = (out.numpy().astype(np.uint32) << 16).view(np.float32)[:p * 32 * width]
      ok = np.isfinite(got).all()
      err = np.abs(got - want[:p * 32 * width]).max() / (np.abs(want[:p * 32 * width]).max() + 1e-9)
      flop = 2 * p * 32 * k * n
      print(f"{name.split('.')[-2]:10s} panels {p:2d} {shape}: {dt*1e3:6.3f} ms  {flop/dt/1e12:5.0f} TFLOP/s  "
            f"{'finite' if ok else 'NONFINITE'} rel err {err:.2e}", flush=True)
finally:
  dev.close()
