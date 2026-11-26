import os, random, unittest
import numpy as np
from compiler import UOp, dtypes
from device import Device
from test.test_sfpu_hw import run_sfpu_on_silicon

def expression(steps, a, b):
  values = [a, b]
  ab = lambda v: v.abs() if isinstance(v, UOp) else np.abs(v)
  for op, left, right in steps:
    x, y = values[left], values[right]
    match op:
      case 0: z = x * y + a
      case 1: z = b - x * y
      case 2: z = x * 0.5 - y
      case 3: z = ab(x)
      case 4: z = x.maximum(y) if isinstance(x, UOp) else np.maximum(x, y)
      case 5: z = (x < y).where(a, b) if isinstance(x, UOp) else np.where(x < y, a, b)
      case 6: z = x.sin() if isinstance(x, UOp) else np.sin(x)
      case 7: z = (ab(x) + 1).rsqrt() if isinstance(x, UOp) else 1 / np.sqrt(ab(x) + 1)
      case 8: z = (ab(x) + 1).log2() if isinstance(x, UOp) else np.log2(ab(x) + 1)
      case 9: z = (-ab(x)).exp2() if isinstance(x, UOp) else np.exp2(-ab(x))
      case 10: z = (ab(x) + 1).recip() if isinstance(x, UOp) else 1 / (ab(x) + 1)
      case 11: z = x * x + y
    values.append(z)
  return values[-2:]

@unittest.skip("sfpu.py pending rewrite onto the dtype-free UOp core")
class TestSfpuFuzz(unittest.TestCase):
  def test_seeded_expression_chains(self):
    dev = Device(0)
    self.addCleanup(dev.close)
    start = int(os.getenv("SFPU_FUZZ_START", "0"))
    for seed in range(start, start + int(os.getenv("SFPU_FUZZ_SEEDS", "48"))):
      rng = random.Random(seed)
      data = np.random.default_rng(seed).uniform(-1, 1, (2, 1024)).astype(np.float32)
      steps = [(rng.randrange(12), rng.randrange(i), rng.randrange(i)) for i in range(2, 9)]
      regs = rng.choice((4, 8))
      precision = rng.choice((dtypes.fp32, dtypes.bf16))
      with self.subTest(seed=seed, regs=regs, precision=precision, steps=steps):
        outs, _ = run_sfpu_on_silicon(dev, lambda a, b: expression(steps, a, b),
                                      dict(zip(("a", "b"), data)), multi_out=True, output_tiles=[1, 0],
                                      max_regs=regs, precision=precision)
        for actual, expected in zip(outs, expression(steps, *data), strict=True):
          tolerance = 5e-5 if precision is dtypes.fp32 else 8e-3
          np.testing.assert_allclose(actual, expected, rtol=tolerance, atol=tolerance)

  def test_integer_expression_chains(self):
    dev = Device(0)
    self.addCleanup(dev.close)
    for seed in range(64):
      rng = np.random.default_rng(seed)
      a, b = rng.uniform(-8, 8, (2, 1024)).astype(np.float32)
      steps = rng.integers(0, 10, size=5)
      def bits(x, y):
        for op in steps:
          match op:
            case 0: x = (x ^ y) + y
            case 1: x = x - (x & y)
            case 2: x = (~x) | y
            case 3: x = x << (y & 31)
            case 4: x = x >> (y & 31)
            case 5: x = (x >> 7) ^ (y << 11)
            case 6: x = x.minimum(y) if isinstance(x, UOp) else np.minimum(x, y)
            case 7: x = x.maximum(y) if isinstance(x, UOp) else np.maximum(x, y)
            case 8: x = -(x + y)
            case 9: x = (x < y).where(~x, y) if isinstance(x, UOp) else np.where(x < y, ~x, y)
        return x
      def halves(a, b):
        u = bits(a.bitcast(dtypes.u32), b.bitcast(dtypes.u32))
        # Read back exact halves through the FP32 packer, including NaN payloads.
        return [v.bitcast(dtypes.i32).cast(dtypes.fp32) for v in (u & 65535, u >> 16)]
      with self.subTest(seed=seed, ops=steps.tolist()):
        (lo, hi), _ = run_sfpu_on_silicon(dev, halves, {"a": a, "b": b}, multi_out=True)
        actual = lo.astype(np.uint32) | (hi.astype(np.uint32) << 16)
        np.testing.assert_array_equal(actual, bits(a.view(np.uint32), b.view(np.uint32)))
