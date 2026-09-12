"""Checkpoint bytes stay unchanged through allocation and host staging."""
from dataclasses import replace
import unittest
import os

from ttko.device import Device

from ttko import DType


class RowMajorWeightsTest(unittest.TestCase):
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
