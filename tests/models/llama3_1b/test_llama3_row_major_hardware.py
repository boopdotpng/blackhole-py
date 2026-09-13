"""Opt-in checks: LLAMA_TEST_DEVICE=1 python3 -m unittest discover -s tests.

The CPU GEMV tolerance covers existing HiFi2 approximate products and BF16
output truncation. Both layouts also agree exactly for these fixed inputs.
"""
from dataclasses import replace
import os
import unittest

import numpy as np

from ttko.device import Device
from ttko.program import DType
from examples.llama3 import Llama3Kernels

llama3 = Llama3Kernels("1b")
decode_projection, rmsnorm = llama3.decode_projection, llama3.rmsnorm


@unittest.skipUnless('LLAMA_TEST_DEVICE' in os.environ,
                     'set LLAMA_TEST_DEVICE to select hardware')
class RawWeightHardwareTest(unittest.TestCase):
  def test_projection_and_norm(self):
    rng = np.random.default_rng(7)
    device = Device(int(os.environ['LLAMA_TEST_DEVICE']))
    try:
      device.init_device()
      cores = tuple(device.dram.cores[:117])
      for width in (2048, 8192):
        host_x = rng.normal(size=(1, width)).astype(np.float32)
        host_w = rng.normal(0, 0.02, size=(2048, width)).astype(np.float32)
        outputs = []
        for tiled in (True, False):
          suffix = f'{width}_{tiled}'
          x = device.dram.buffer(
            f'x_{suffix}', DType.BF16, (1, width), axis=0,
            global_address=True, tilized=tiled,
          )
          weight = device.dram.buffer(
            f'w_{suffix}', DType.BF16, (2048, width), axis=0,
            global_address=not tiled, cores=cores, tilized=tiled,
          )
          if not tiled: weight = replace(weight, cores=cores)
          output = device.dram.buffer(
            f'y_{suffix}', DType.BF16, (117, 18), axis=0, cores=cores,
          )
          x_bytes, weight_bytes = x.from_numpy(host_x), weight.from_numpy(host_w)
          device.write(x, x_bytes)
          device.write(weight, weight_bytes)
          device.run(decode_projection(x, weight, output), timeout=20)
          slots = output.to_numpy(device.read(output))
          actual = np.concatenate([
            row[:count] for row, count in zip(slots, weight.item_counts)
          ])
          outputs.append(actual)
          expected = weight.to_numpy(weight_bytes) @ x.to_numpy(x_bytes).ravel()
          relative_rms = np.linalg.norm(actual - expected) / np.linalg.norm(expected)
          self.assertLess(relative_rms, 0.008)
          if not tiled:
            self.assertEqual(device.read(weight), weight_bytes)
        np.testing.assert_array_equal(outputs[0], outputs[1])

      for tiled in (True, False):
        options = {'global_address': True, 'tilized': tiled}
        x = device.dram.buffer(f'nx_{tiled}', DType.BF16, (1, 2048), axis=0, **options)
        gamma = device.dram.buffer(f'ng_{tiled}', DType.BF16, (2048,), **options)
        output = device.dram.buffer(f'ny_{tiled}', DType.BF16, (1, 2048), axis=0, **options)
        if tiled:
          x_bytes = x.from_numpy(rng.normal(size=(1, 2048)))
          gamma_bytes = gamma.from_numpy(rng.uniform(0.5, 1.5, size=(2048,)))
        device.write(x, x_bytes)
        device.write(gamma, gamma_bytes)
        device.run(rmsnorm(x, gamma, output), timeout=10)
        actual = output.to_numpy(device.read(output))
        stored_x = x.to_numpy(x_bytes)
        expected = (stored_x / np.sqrt(np.mean(stored_x ** 2) + 1e-5) *
                    gamma.to_numpy(gamma_bytes))
        np.testing.assert_allclose(actual, expected, rtol=0.008, atol=0.00001)
    finally:
      device.close()
