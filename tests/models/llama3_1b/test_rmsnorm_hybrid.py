"""Opt-in hardware correctness for the production hybrid RMSNorm port."""
import os
import unittest
from unittest.mock import patch
import numpy as np
from ttko.device import Device
from examples import llama3_1b as llama3
from ttko.program import DType


def bf16(values):
  bits = np.asarray(values, dtype=np.float32).view(np.uint32)
  return ((bits + 0x7fff + ((bits >> 16) & 1)) >> 16).astype('<u2')


def fp32(bits):
  return (bits.astype(np.uint32) << 16).view(np.float32)


@unittest.skipUnless('LLAMA_TEST_DEVICE' in os.environ, 'set LLAMA_TEST_DEVICE')
class HybridRmsnormTest(unittest.TestCase):
  def test_precision_and_repeated_launches(self):
    device = Device(int(os.environ['LLAMA_TEST_DEVICE']))
    try:
      device.init_device()
      n = llama3.EMBED_DIM
      core = device.dram.cores[2:3]
      x, gamma, y = (device.dram.buffer(name, DType.BF16, (n,),
                      cores=core, global_address=True, tilized=False)
                     for name in ('rms_x', 'rms_gamma', 'rms_y'))
      with patch.dict(os.environ, {'LLAMA_RMSNORM': 'hybrid'}):
        kernel = llama3.rmsnorm(x, gamma, y)
      rng = np.random.default_rng(84)
      gb = bf16(rng.uniform(-2, 2, n))
      g = fp32(gb).astype(np.float64)
      device.write(gamma, gb.tobytes())
      for scale in (1., 1e-5, 1e5, 0., 1.):
        xb = bf16(rng.normal(size=n) * scale)
        a = fp32(xb).astype(np.float64)
        expected = a*g / np.sqrt(np.mean(a*a)+1e-5)
        device.write(x, xb.tobytes())
        device.run(kernel)
        actual = fp32(np.frombuffer(device.read(y), dtype='<u2'))
        np.testing.assert_allclose(actual, expected, rtol=0.004, atol=1e-7)
    finally:
      device.close()
