"""Hardware projection equivalence for prefill and decode."""
from dataclasses import replace
import os
import unittest

import numpy as np
from ttko.device import Device
from ttko.program import DType
from examples.llama3 import Llama3Kernels, SequenceBuffer

d = Llama3Kernels("8b")
prefill_projection, prefill_projections = d.prefill_projection, d.prefill_projections


def buffers(device, count, rows=176):
  cores = device.dram.cores[:88]
  x = device.dram.buffer('test_x', DType.BF16, (1, 4096), axis=0,
                         global_address=True, tilized=False)
  storage = device.dram.buffer('test_weight', DType.BF16, (rows, 4096), axis=0,
                               global_address=True, tilized=False)
  weight = replace(storage, name='test_weight_shards', cores=cores)
  out = device.dram.buffer('test_out', DType.BF16, (88, weight.items_per_core), axis=0, cores=cores)
  return SequenceBuffer(device, x, count), storage, weight, SequenceBuffer(device, out, count)


class PrefillTest(unittest.TestCase):


  @unittest.skipUnless('LLAMA_PREFILL_DEVICE' in os.environ, 'set LLAMA_PREFILL_DEVICE to run on hardware')
  def test_projection_matches_decode(self):
    device = Device(int(os.environ['LLAMA_PREFILL_DEVICE']))
    try:
      device.init_device()
      x, storage, weight, out = buffers(device, 8)
      rng = np.random.default_rng(17)
      activations = rng.normal(0, .1, (8, 4096)).astype(np.float32)
      weights = rng.normal(0, .1, weight.shape).astype(np.float32)
      device.write(storage, storage.from_numpy(weights))
      for i in range(8): device.write(x.view(i), x.prototype.from_numpy(activations[i]))
      device.run(timeout=30)
      for count in (1, 3, 4, 8):
        device.run(prefill_projection(x, weight, out, count), timeout=30)
        actual = [device.read(out.view(i)) for i in range(count)]
        for i in range(count):
          device.run(d.decode_projection(x.view(i), weight, out.view(i)), timeout=30)
          self.assertEqual(actual[i], device.read(out.view(i)))
      gamma = device.dram.buffer('test_gamma', DType.BF16, (4096,),
                                 global_address=True, tilized=False)
      device.write(gamma, gamma.from_numpy(rng.uniform(.5, 1.5, 4096)))
      device.run(timeout=30)
      projections = [(weight, out)]
      for index in (1, 2):
        # Distinct names/bindings exercise the grouped parameter table; weight
        # storage can be shared because all three projections are read-only.
        target = SequenceBuffer(device, replace(out.prototype, name=f'test_out_{index}'), 8)
        projections.append((replace(weight, name=f'test_weight_{index}'), target))
      for count in (1, 3, 4, 8):
        device.run(prefill_projections(x, projections, count, gamma), timeout=30)
        actual = [[device.read(target.view(i)) for _, target in projections] for i in range(count)]
        for i in range(count):
          for w, target in projections:
            device.run(d._decode_fused_projections(x.view(i),
              ((w, target.view(i)),), norm_weight=gamma), timeout=30)
          self.assertEqual(actual[i], [device.read(target.view(i)) for _, target in projections])
    finally:
      device.close()


if __name__ == '__main__': unittest.main()
