from tests.models.topology import P150_WORKER_CORES
"""CPU lowering/layout checks and opt-in hardware projection equivalence."""
from dataclasses import replace
import os
from types import SimpleNamespace
import unittest

import numpy as np
from ttko.device import Device
from examples import llama3_8b as d
from examples.llama3_prefill import SequenceBuffer, prefill_projection, prefill_projections
from fw.consts import TensixL1
from pcie import P100_DRAM_ENDPOINTS, P100_WORKER_CORES, P150_DRAM_ENDPOINTS
from ttko.program import Dram, DType


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
  def test_layout_and_lowering(self):
    for endpoints, cores in ((P100_DRAM_ENDPOINTS, P100_WORKER_CORES),
                             (P150_DRAM_ENDPOINTS, P150_WORKER_CORES)):
      device = SimpleNamespace(dram=Dram(len(endpoints), cores, endpoints))
      x, storage, weight, out = buffers(device, 8, rows=d.MLP_DIM)
      for sequence in (x, out):
        self.assertEqual(sequence.stride % len(endpoints), 0)
        for i in range(8):
          view = sequence.view(i)
          self.assertEqual(view.addr, sequence.storage.addr + i * sequence.stride // len(endpoints) * 2048)
          self.assertLessEqual(view.addr + (view.physical_tiles + len(endpoints)-1)//len(endpoints)*2048,
                               sequence.storage.addr + sequence.storage.size//len(endpoints))
      for count in (1, 3, 4, 8):
        with self.subTest(banks=len(endpoints), count=count):
          program = prefill_projection(x, weight, out, count)
          # Includes text partition, parameter table and L1 allocation checks.
          self.assertTrue(program.static_commands())
          self.assertLessEqual(program._l1.next, TensixL1.DATA_BUFFER_SPACE_END)
          program._param_table()
      gamma = device.dram.buffer('scale', DType.BF16, (4096,), global_address=True, tilized=False)
      group = tuple((replace(weight, name=f'group_w_{i}'),
                     SequenceBuffer(device, replace(out.prototype, name=f'group_o_{i}'), 8))
                    for i in range(3))
      for count in (1, 4, 8):
        program = prefill_projections(x, group, count, gamma)
        self.assertTrue(program.static_commands())
        self.assertLessEqual(program._l1.next, TensixL1.DATA_BUFFER_SPACE_END)
        self.assertEqual(len(program.params), 12)
      for count in (0, 9, 1.5):
        with self.assertRaises(ValueError): prefill_projection(x, weight, out, count)

  def test_load_tokens_rejects_invalid_input_before_device_access(self):
    runtime = d.Llama3Decode.__new__(d.Llama3Decode)
    for tokens in ([], [-1], [d.VOCAB_SIZE], [2**32], [1.5], [[1]], [True],
                   [1] * d.ROPE_CACHE_TOKENS):
      with self.subTest(tokens=str(tokens)[:40]), self.assertRaises(ValueError):
        runtime.load_tokens(tokens)

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
