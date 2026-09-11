"""Checkpoint bytes stay unchanged through allocation and host staging."""
from dataclasses import replace
from math import prod
from types import SimpleNamespace
import unittest
import os
from unittest.mock import patch

from ttko.device import Device

from examples.llama3_8b import Llama3Decode, _dense_byte_offset
from pcie import P150_DRAM_ENDPOINTS, P100_WORKER_CORES
from ttko.program import Dram
from ttko import DType


class RowMajorWeightsTest(unittest.TestCase):
  def setUp(self):
    self.dram = Dram(8, P100_WORKER_CORES, P150_DRAM_ENDPOINTS)

  def test_global_row_shards_do_not_change_checkpoint_bytes(self):
    storage = self.dram.buffer(
      'weights', DType.BF16, (119, 2048), axis=0,
      global_address=True, tilized=False,
    )
    weight = replace(storage, cores=P100_WORKER_CORES)
    data = bytes(range(256)) * (119 * 2048 * 2 // 256)
    self.assertEqual(weight.size, len(data))
    self.assertEqual(weight.addr, storage.addr)
    self.assertEqual(sum(weight.item_counts), 119)
    self.assertIs(weight.pad_data(data), data)
    self.assertIs(weight.unpad_data(data), data)
    with self.assertRaises(ValueError):
      weight.pad_data(data[:-2])

  def test_all_model_weights_and_dense_projection_inputs_are_raw(self):
    runtime = Llama3Decode.__new__(Llama3Decode)
    runtime.device = SimpleNamespace(dram=self.dram)
    runtime._allocate()
    weights = [runtime.embedding_weight, runtime.lm_weight, runtime.final_norm]
    weights += [w for layer in runtime.layers for w in layer['weights'].values()]
    for weight in weights:
      with self.subTest(weight=weight.name):
        self.assertFalse(weight.tilized)
        self.assertTrue(weight.global_address)
        self.assertEqual(weight.size, prod(weight.shape) * weight.dtype.itemsize)
    if hasattr(runtime, "lm_storage"):
      self.assertNotEqual(runtime.embedding_weight.addr, runtime.lm_weight.addr)
    else:
      self.assertEqual(runtime.embedding_weight.addr, runtime.lm_weight.addr)
    for vector in (runtime.x_a, runtime.x_b, runtime.normalized,
                   runtime.context, runtime.hidden_dense):
      self.assertFalse(vector.tilized)
      for index in (0, 15, 16, 31, 32, 511, 512, 1023):
        self.assertEqual(_dense_byte_offset(vector, index), index * vector.dtype.itemsize)


  def test_weight_write_never_enters_numpy_layout_code(self):
    storage = self.dram.buffer(
      "raw", DType.BF16, (119, 2048), axis=0,
      global_address=True, tilized=False,
    )
    weight = replace(storage, cores=P100_WORKER_CORES)
    data = bytes(range(256)) * (weight.size // 256)
    device = Device.__new__(Device)
    writes = []
    device._write_physical = lambda buffer, payload: writes.append((buffer, payload))
    with patch("ttko.program.np.frombuffer", side_effect=AssertionError("host layout conversion")):
      device.write(weight, data)
    self.assertEqual(len(writes), 1)
    self.assertIs(writes[0][1], data)


  def test_model_staging_bypasses_layout_conversion(self):
    storage = self.dram.buffer("weight", DType.BF16, (2048,),
                               global_address=True, tilized=False)
    data = bytes(range(256)) * (storage.size // 256)
    writes = []
    runtime = Llama3Decode.__new__(Llama3Decode)
    runtime.device = SimpleNamespace(
      _write_physical=lambda buffer, payload: writes.append((buffer, payload)),
    )
    runtime.profile = {"weight_stage_s": 0.0, "dram_upload_bytes": 0}
    with patch("ttko.program.np.frombuffer", side_effect=AssertionError("host layout conversion")):
      runtime._stage_upload(storage, data)
    self.assertIs(writes[0][1], data)
    self.assertEqual(runtime.profile["dram_upload_bytes"], len(data))
    with self.assertRaises(ValueError):
      runtime._stage_upload(replace(storage, tilized=True), data)
    with self.assertRaises(ValueError):
      runtime._stage_upload(storage, data[:-2])

  def test_kernel0_weights_are_raw(self):
    from examples.diagnostics.llama3_8b.llama3_row_major import allocate_kernel0_buffers
    buffers = allocate_kernel0_buffers(self.dram)
    self.assertFalse(buffers.embedding_weight.tilized)
    self.assertFalse(buffers.gamma.tilized)


  @unittest.skipUnless("LLAMA_TEST_DEVICE" in os.environ, "set LLAMA_TEST_DEVICE to select hardware")
  def test_raw_weight_device_readback(self):
    device = Device(int(os.environ["LLAMA_TEST_DEVICE"]))
    try:
      device.init_device()
      formats = (DType.BF16, DType.F32, DType.U32)
      if hasattr(DType, "FP8"): formats += (DType.FP8,)
      for dtype in formats:
        storage = device.dram.buffer("raw_" + dtype.name, dtype, (119, 2048),
                                     axis=0, global_address=True, tilized=False)
        weight = replace(storage, cores=device.dram.cores[:117])
        data = bytes(range(256)) * (weight.size // 256)
        device.write(weight, data)
        device.run()
        self.assertEqual(device.read(weight), data)
    finally:
      device.close()


if __name__ == '__main__':
  unittest.main()
