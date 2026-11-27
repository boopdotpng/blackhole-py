import os
import unittest
import numpy as np
from compiler import Tensor, dtypes


@unittest.skipUnless(os.environ.get("BH_HW") == "1", "set BH_HW=1 for P150 execution")
class TestMapBlackhole(unittest.TestCase):
  def test_runtime_position_reuses_native_code_on_both_cards(self):
    from compiler import Variable, function
    from compiler.blackhole.lower import _lower_kernel
    from device import Device
    for card in (0, 1):
      dev = Device(card)
      try:
        expected = np.zeros((1, 8, 16), np.float32)
        cache = Tensor(expected)
        position = Variable("position", 0, 7)
        @function(allow_implicit=True)
        def update(value, pos):
          write = cache[:, pos:pos + 1, :].uop.store(value.uop)
          return Tensor.from_uop(cache.uop.after(write))
        misses = None
        for pos in (1, 4, 7, 0):
          values = np.full((1, 1, 16), pos + 1, np.float32)
          expected[:, pos:pos + 1] = values
          with self.subTest(card=card, position=pos):
            np.testing.assert_array_equal(update(Tensor(values), position.bind(pos)).numpy(device=dev), expected)
            current = _lower_kernel.cache_info().misses
            if misses is not None: self.assertEqual(current, misses)
            misses = current
      finally: dev.close()

  def test_partial_cache_writes_on_both_cards(self):
    from device import Device
    for card in (0, 1):
      dev = Device(card)
      try:
        for dtype in (dtypes.fp32, dtypes.bf16):
          expected = np.full((2, 1, 8, 32, 128), -3, np.float32)
          cache = Tensor(expected, dtype=dtype)
          value = np.arange(1024, dtype=np.float32).reshape(1, 8, 1, 128) % 31
          for which, position in ((0, 0), (1, 3), (0, 17)):
            write = cache[which, :, :, position:position+1, :].uop.store(Tensor(value, dtype=dtype).uop)
            result = Tensor.from_uop(cache.uop.after(write))
            expected[which, :, :, position:position+1, :] = value
            with self.subTest(card=card, dtype=dtype, position=position):
              np.testing.assert_array_equal(result.numpy(device=dev), expected)
          expected = np.arange(51, dtype=np.float32).reshape(3, 17)
          target = Tensor(expected, dtype=dtype)
          write = target[:, 3:8].uop.store(Tensor(np.full((3, 5), 7, np.float32), dtype=dtype).uop)
          expected[:, 3:8] = 7
          with self.subTest(card=card, dtype=dtype, operation="unaligned write"):
            np.testing.assert_array_equal(Tensor.from_uop(target.uop.after(write)).numpy(device=dev), expected)
      finally: dev.close()

  def test_full_width_integer_conversion_and_argmax(self):
    from device import Device
    values = np.array([-2147483520., -166912.75, -32768.5, -1.99999988, -.99999994, 0.,
                       .99999994, 1.99999988, 32768.5, 55637., 166912.75, 2147483520.], np.float32)
    for card in (0, 1):
      dev = Device(card)
      try:
        with self.subTest(card=card, operation="fp32 to i32"):
          np.testing.assert_array_equal(Tensor(values).cast(dtypes.i32).numpy(device=dev), values.astype(np.int32))
        for size, dtype in ((128, dtypes.fp32), (128, dtypes.bf16), (166912, dtypes.bf16)):
          logits = np.full(size, -3, np.float32)
          logits[size // 3] = logits[-2] = -.5
          with self.subTest(card=card, size=size, operation="argmax"):
            actual = Tensor(logits, dtype=dtype).argmax().numpy(device=dev)
            self.assertEqual(actual.shape, ())
            self.assertEqual(actual.item(), size // 3)
      finally: dev.close()

  def test_views_and_indices_on_both_cards(self):
    from device import Device
    for card in (0, 1):
      dev = Device(card)
      try:
        for dtype in (dtypes.fp32, dtypes.bf16):
          a = np.arange(51, dtype=np.float32).reshape(3, 17) / 8
          x = Tensor(a, dtype=dtype)
          cases = [("transpose", x.T, a.T), ("slice", x[:, 2:15], a[:, 2:15]),
                   ("reshape", x.reshape(1, 51), a.reshape(1, 51)),
                   ("broadcast", x + Tensor(np.arange(17, dtype=np.float32), dtype=dtype), a + np.arange(17))]
          for name, expression, expected in cases:
            with self.subTest(card=card, dtype=dtype, operation=name):
              np.testing.assert_array_equal(expression.numpy(device=dev), expected)
        with self.subTest(card=card, operation="indices"):
          np.testing.assert_array_equal(Tensor.arange(137).numpy(device=dev), np.arange(137))
          np.testing.assert_allclose((Tensor.arange(137).float() / 100).sin().numpy(device=dev),
                                     np.sin(np.arange(137, dtype=np.float32) / 100), rtol=2e-6, atol=2e-6)
      finally: dev.close()

  def test_embedding_gather_on_both_cards(self):
    from device import Device
    from examples.nanbeige import Embedding
    values = np.arange(31 * 17, dtype=np.float32).reshape(31, 17) / 8
    indices = np.array([[29, 1, 17], [0, -1, 31]], dtype=np.int32)
    expected = values[indices.clip(0, 30)]
    expected[(indices < 0) | (indices >= 31)] = 0
    for card in (0, 1):
      dev = Device(card)
      try:
        embedding = Embedding(31, 17)
        embedding.weight = Tensor(values)
        with self.subTest(card=card):
          np.testing.assert_array_equal(embedding(Tensor(indices)).numpy(device=dev), expected)
      finally: dev.close()

  def test_nanbeige_rope_on_both_cards(self):
    from device import Device
    from examples.nanbeige import apply_rope, rope_theta
    def bf16(v):
      bits = v.view(np.uint32)
      return ((bits + 0x7fff + ((bits >> 16) & 1)) & 0xffff0000).view(np.float32)
    a = bf16(np.random.default_rng(385).uniform(-1, 1, (1, 56, 1, 128)).astype(np.float32))
    rotated = np.concatenate((-a[..., 64:], a[..., :64]), axis=-1)
    for card in (0, 1):
      dev = Device(card)
      try:
        for position in (0, 3, 411):
          angle = position / (rope_theta ** (np.arange(0, 128, 2, dtype=np.float32) / 128))
          angle = np.tile(angle, 2)
          expected = bf16(a * bf16(np.cos(angle)) + rotated * bf16(np.sin(angle)))
          with self.subTest(card=card, position=position):
            actual = apply_rope(Tensor(a, dtype=dtypes.bf16), position).numpy(device=dev)
            np.testing.assert_allclose(actual, expected, atol=.012, rtol=.015)
      finally: dev.close()
