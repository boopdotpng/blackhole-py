import os
import unittest
import numpy as np
from compiler import Tensor, dtypes, lower_tensor, linearize_schedule
from compiler.blackhole.lower import lower_kernel


class TestTensorBlackhole(unittest.TestCase):
  @unittest.skipUnless(os.environ.get("BH_HW") == "1", "set BH_HW=1 for P150 execution")
  def test_batched_attention_matmuls_both_cards(self):
    from device import Device
    rng = np.random.default_rng(82)
    for card in (0, 1):
      dev = Device(card)
      try:
        for m, n, k in ((1, 2, 128), (1, 128, 2), (7, 19, 31), (9, 17, 33)):
          a = rng.integers(-4, 5, (2, 3, m, k)).astype(np.float32) / 8
          b = rng.integers(-4, 5, (2, 3, k, n)).astype(np.float32) / 8
          with self.subTest(card=card, shape=(m, n, k)):
            actual = Tensor(a, dtype=dtypes.bf16).matmul(Tensor(b, dtype=dtypes.bf16), dtype=dtypes.fp32).numpy(device=dev)
            np.testing.assert_array_equal(actual, a @ b)
      finally: dev.close()

  @unittest.skipUnless(os.environ.get("BH_HW") == "1", "set BH_HW=1 for P150 execution")
  def test_fused_gated_projections_both_cards(self):
    from device import Device
    rng = np.random.default_rng(392)
    a = rng.integers(-8, 9, (17, 31)).astype(np.float32) / 32
    gate, up = [rng.integers(-8, 9, (1117, 31)).astype(np.float32) / 32 for _ in range(2)]
    g, u = a @ gate.T, a @ up.T
    expected = g / (1 + np.exp(-g)) * u
    for index in (0, 1):
      dev = Device(index)
      try:
        x = Tensor(a, dtype=dtypes.bf16)
        g = x.matmul(Tensor(gate, dtype=dtypes.bf16).T, dtype=dtypes.fp32)
        u = x.matmul(Tensor(up, dtype=dtypes.bf16).T, dtype=dtypes.fp32)
        with self.subTest(card=index):
          np.testing.assert_allclose((g.silu() * u).numpy(device=dev), expected, rtol=4e-6, atol=3e-7)
      finally: dev.close()

  def test_lower_map_and_matmul(self):
    a, b = Tensor.buffer("a", (17, 35)), Tensor.buffer("b", (17, 35))
    x, w = Tensor.buffer("x", (17, 31), dtypes.bf16), Tensor.buffer("w", (1117, 31), dtypes.bf16)
    for tensor in (a.silu() * b, x @ w.T):
      call = linearize_schedule(lower_tensor(tensor))[0]
      lowered = lower_kernel(call.kernel, call.args)
      self.assertGreater(len(lowered.program.src[3].arg), 0)

  @unittest.skipUnless(os.environ.get("BH_HW") == "1", "set BH_HW=1 for P150 execution")
  def test_tensor_execution_both_cards(self):
    from device import Device
    rng = np.random.default_rng(2026)
    for index in (0, 1):
      with self.subTest(card=index):
        dev = Device(index)
        try:
          for dtype, shape in ((dtypes.fp32, (17, 35)), (dtypes.fp32, (400, 65)), (dtypes.bf16, (1, 35)),
                               (dtypes.bf16, (1, 3, 35))):
            a, b = [rng.uniform(-3., 3., shape).astype(np.float32) for _ in range(2)]
            ta, tb = Tensor(a, dtype=dtype), Tensor(b, dtype=dtype)
            if dtype is dtypes.bf16:
              a, b = [((v.view(np.uint32) + 0x7fff + ((v.view(np.uint32) >> 16) & 1)) & 0xffff0000).view(np.float32) for v in (a, b)]
            actual = (ta.silu() * tb).realize(device=dev).numpy()
            np.testing.assert_allclose(actual, a / (1 + np.exp(-a)) * b,
                                        rtol=0.008 if dtype is dtypes.bf16 else 3e-6, atol=2e-6)
          a = rng.integers(-1, 2, (17, 31)).astype(np.float32)
          w = rng.integers(-1, 2, (1117, 31)).astype(np.float32)
          actual = (Tensor(a, dtype=dtypes.bf16) @ Tensor(w, dtype=dtypes.bf16).T).realize(device=dev).numpy()
          np.testing.assert_array_equal(actual, a @ w.T)
        finally: dev.close()
