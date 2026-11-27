import os
import unittest
import numpy as np
from compiler import Tensor, dtypes, lower_tensor, linearize_schedule
from compiler.blackhole.lower import lower_kernel


class TestReductionBlackhole(unittest.TestCase):
  @unittest.skipUnless(os.environ.get("BH_HW") == "1", "set BH_HW=1 for P150 execution")
  def test_masked_attention_softmax_on_both_cards(self):
    from device import Device
    rng = np.random.default_rng(53)
    for card in (0, 1):
      dev = Device(card)
      try:
        for dtype in (dtypes.fp32, dtypes.bf16):
          for width in (1, 2, 16, 17, 32, 83):
            values = rng.uniform(-4, -1, (1, 56, 1, width)).astype(np.float32)
            if dtype is dtypes.bf16:
              bits = values.view(np.uint32)
              values = ((bits + 0x7fff + ((bits >> 16) & 1)) & 0xffff0000).view(np.float32)
            expected = np.exp(values - values.max(-1, keepdims=True))
            expected /= expected.sum(-1, keepdims=True)
            with self.subTest(card=card, dtype=dtype, width=width):
              # Repeating the same staged program catches launch-to-launch
              # source-bank/configuration state that a single launch misses.
              for _ in range(3):
                actual = Tensor(values, dtype=dtype).softmax(-1).numpy(device=dev)
                np.testing.assert_allclose(actual, expected, atol=.002 if dtype is dtypes.bf16 else 3e-7,
                                           rtol=.03 if dtype is dtypes.bf16 else 4e-6)
      finally: dev.close()

  @unittest.skipUnless(os.environ.get("BH_HW") == "1", "set BH_HW=1 for P150 execution")
  def test_nanbeige_bf16_norm_on_both_cards(self):
    from device import Device
    from examples.nanbeige import RMSNorm
    rng = np.random.default_rng(85)
    def bf16(v):
      bits = v.view(np.uint32)
      return ((bits + 0x7fff + ((bits >> 16) & 1)) & 0xffff0000).view(np.float32)
    for index in (0, 1):
      dev = Device(index)
      try:
        for shape in ((9, 128), (1, 1, 7168)):
          a = bf16(rng.uniform(-3., 2., shape).astype(np.float32))
          weight = bf16(rng.uniform(.5, 1.5, shape[-1]).astype(np.float32))
          norm = RMSNorm(shape[-1]); norm.weight = Tensor(weight, dtype=dtypes.bf16)
          expected = bf16(bf16(a / np.sqrt((a*a).mean(-1, keepdims=True) + 1e-5)) * weight)
          with self.subTest(card=index, shape=shape):
            np.testing.assert_allclose(norm(Tensor(a, dtype=dtypes.bf16)).numpy(device=dev), expected, rtol=.008, atol=1e-5)
      finally: dev.close()

  @unittest.skipUnless(os.environ.get("BH_HW") == "1", "set BH_HW=1 for P150 execution")
  def test_staged_norm_and_softmax_on_both_cards(self):
    from device import Device
    rng = np.random.default_rng(45)
    for index in (0, 1):
      dev = Device(index)
      try:
        for shape in ((1, 32), (9, 128), (1, 1, 7168)):
          a = rng.uniform(-3., 2., shape).astype(np.float32)
          weight = rng.uniform(.5, 1.5, shape[-1]).astype(np.float32)
          x, w = Tensor(a), Tensor(weight)
          norm = x * (x.square().mean(-1, keepdim=True) + 1e-5).rsqrt() * w
          with self.subTest(card=index, shape=shape, op="rmsnorm"):
            np.testing.assert_allclose(norm.numpy(device=dev), a / np.sqrt((a*a).mean(-1, keepdims=True)+1e-5) * weight,
                                        rtol=4e-6, atol=3e-6)
          if shape[-1] < 7168:
            expected = np.exp(a - a.max(-1, keepdims=True)); expected /= expected.sum(-1, keepdims=True)
            with self.subTest(card=index, shape=shape, op="softmax"):
              np.testing.assert_allclose(x.softmax(-1).numpy(device=dev), expected, rtol=4e-6, atol=3e-7)
      finally: dev.close()

  def test_compile_row_reductions(self):
    x = Tensor.buffer("x", (9, 32), dtypes.bf16)
    for expression in (x.float().sum(-1, keepdim=True), x.float().max(-1, keepdim=True),
                       (x.float().square().mean(-1, keepdim=True) + 1e-5).rsqrt()):
      call, = linearize_schedule(lower_tensor(expression))
      self.assertEqual(lower_kernel(call.kernel, call.args).workers, 2)

  @unittest.skipUnless(os.environ.get("BH_HW") == "1", "set BH_HW=1 for P150 execution")
  def test_row_reductions_on_both_cards(self):
    from device import Device
    rng = np.random.default_rng(39)
    for index in (0, 1):
      dev = Device(index)
      try:
        for dtype, shape in ((dtypes.fp32, (9, 32)), (dtypes.bf16, (17, 128)), (dtypes.bf16, (1, 7168))):
          a = rng.uniform(-3., -0.1, shape).astype(np.float32)
          if dtype is dtypes.bf16:
            a = ((a.view(np.uint32) + 0x7fff + ((a.view(np.uint32) >> 16) & 1)) & 0xffff0000).view(np.float32)
          x = Tensor(a, dtype=dtype).float()
          cases = [(x.sum(-1, keepdim=True), a.sum(-1, keepdims=True)),
                   (x.max(-1, keepdim=True), a.max(-1, keepdims=True)),
                   ((x.square().mean(-1, keepdim=True) + 1e-5).rsqrt(), 1. / np.sqrt((a * a).mean(-1, keepdims=True) + 1e-5))]
          for expression, expected in cases:
            with self.subTest(card=index, dtype=dtype, shape=shape, op=expression.uop.op):
              actual = expression.numpy(device=dev)
              np.testing.assert_allclose(actual, expected, rtol=3e-6, atol=2e-6)
      finally: dev.close()
