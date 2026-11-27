import json
import os
from pathlib import Path
import tempfile
import unittest
import numpy as np
from compiler import Tensor, dtypes, safe_load


def checkpoint(path, bits, k_tiles=2, n_tiles=3):
  rng = np.random.default_rng(bits)
  magnitude = rng.integers(0, 8, (k_tiles, n_tiles, 2, 2, 16, 16), dtype=np.uint8)
  negative = rng.integers(0, 2, magnitude.shape, dtype=np.uint8)
  negative[magnitude == 0] = 0
  signed = np.empty(magnitude.shape, np.float32)
  np.multiply(negative, -2, dtype=np.float32, out=signed)
  signed += 1
  np.multiply(magnitude, signed, out=signed)
  weight = signed.transpose(1, 3, 5, 0, 2, 4).reshape(n_tiles * 32, k_tiles * 32)
  encoded = np.empty_like(magnitude)
  np.left_shift(negative, bits - 1, out=encoded)
  np.bitwise_or(magnitude, encoded, out=encoded)
  code = encoded.reshape(k_tiles, n_tiles, 1024)
  # Exponent makes each decoded magnitude an integer, for exact GEMM checks.
  exponent = np.full((k_tiles, n_tiles, 64), 127 + bits - 2, np.uint8)
  if bits == 4: code = code[..., ::2] | (code[..., 1::2] << 4)
  raw = np.concatenate((exponent, code), axis=-1)
  header = {"__metadata__": {"blackhole.layout": "kn_tiles_32x32_v1", "blackhole.formats": json.dumps({"weight": f"bfp{bits}_b"})},
            "weight": {"dtype": "U8", "shape": list(raw.shape), "data_offsets": [0, raw.nbytes]}}
  encoded = json.dumps(header).encode()
  path.write_bytes(len(encoded).to_bytes(8, "little") + encoded + raw.tobytes())
  return weight


class TestPackedCheckpoint(unittest.TestCase):
  def test_host_face_conversion_preserves_large_packed_values(self):
    from device import FaceBuffer
    from compiler.tensor import _BUFFER_SOURCE
    class HostDMA:
      def __init__(self): self.dma = self
      def alloc_dram(self, size): self.data = bytearray(size); return 0
      def synchronize(self): pass
      def copyin(self, offset, data):
        raw = memoryview(data).cast("B")
        self.data[offset:offset + len(raw)] = raw
      def copyout(self, data, offset):
        raw = memoryview(data).cast("B")
        raw[:] = self.data[offset:offset + len(raw)]
    with tempfile.TemporaryDirectory() as directory:
      for bits in (4, 8):
        path = Path(directory) / f"bfp{bits}.safetensors"
        expected = checkpoint(path, bits, k_tiles=64)
        tensor = safe_load(path)["weight"]
        source = _BUFFER_SOURCE[tensor.uop]
        buffer = FaceBuffer(HostDMA(), tensor.shape, tensor.dtype, rows=16)
        buffer.copy_from_packed_kn(source.path, source.offset, source.shape)
        np.testing.assert_array_equal(buffer.numpy(), expected)

  def test_packed_logical_shapes_and_dtypes(self):
    with tempfile.TemporaryDirectory() as directory:
      for bits, dtype in ((4, dtypes.bfp4), (8, dtypes.bfp8)):
        path = Path(directory) / f"bfp{bits}.safetensors"
        checkpoint(path, bits)
        tensor = safe_load(path)["weight"]
        self.assertEqual(tensor.shape, (96, 64))
        self.assertIs(tensor.dtype, dtype)

  @unittest.skipUnless(os.environ.get("BH_HW") == "1", "set BH_HW=1 for P150 execution")
  def test_packed_checkpoint_matmuls_both_cards(self):
    from device import Device
    with tempfile.TemporaryDirectory() as directory:
      for index in (0, 1):
        dev = Device(index)
        try:
          for bits in (4, 8):
            with self.subTest(card=index, bits=bits):
              path = Path(directory) / f"bfp{bits}.safetensors"
              weight = checkpoint(path, bits)
              w = safe_load(path)["weight"]
              a = np.random.default_rng(42).integers(-1, 2, (9, 64)).astype(np.float32)
              out = Tensor(a, dtype=dtypes.bf16).matmul(w.T, dtype=dtypes.fp32).numpy(device=dev)
              np.testing.assert_array_equal(out, a @ weight.T)
        finally: dev.close()
