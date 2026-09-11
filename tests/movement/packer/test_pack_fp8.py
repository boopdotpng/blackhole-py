"""FP32 Dst to compact E4M3 L1, including runtime row tails."""
import pytest
from tests import fp8
from tests.movement.unpacker.unpack import FP8_E4M3, F32_TILE_BYTES
from tests.movement.packer.test_pack import _images, INPUT, OUTPUT


@pytest.mark.parametrize('tile', (0, 3, 7))
@pytest.mark.parametrize('count,offset', ((1, 0), (15, 16), (16, 32), (17, 48), (137, 64), (1024, 0)))
def test_fp8_pack_runtime_tail(bh, tile, count, offset):
  payload = fp8.normal_tile(13)
  images, profile = _images(tile, count, offset, output_format=FP8_E4M3)
  bh.launch(images, params=(F32_TILE_BYTES, count),
            l1={INPUT: fp8.as_f32(payload), OUTPUT: b'\xa5' * 1152}, profiler=profile)
  actual = bh.read_l1(bh.core, OUTPUT, 1152)
  assert actual[:count] == payload[offset:offset + count]
  # PACR can zero-pad its last physical output word, but cannot touch the guard.
  padding = actual[count:].find(b'\xa5')
  assert 0 <= padding <= 64
  assert actual[count:count + padding] == bytes(padding)
  assert actual[count + padding:] == b'\xa5' * (1152 - count - padding)


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="Blackhole E4M3 pack flushes subnormals instead of preserving E4M3FN encodings")
def test_fp8_pack_zero_and_subnormal_values(bh):
  payload = bytes(range(16)) + bytes(range(128, 144))
  source = fp8.as_f32(payload) + bytes(F32_TILE_BYTES - len(payload) * 4)
  images, profile = _images(0, len(payload), output_format=FP8_E4M3)
  bh.launch(images, params=(F32_TILE_BYTES, len(payload)),
            l1={INPUT: source, OUTPUT: b'\xa5' * 128}, profiler=profile)
  assert bh.read_l1(bh.core, OUTPUT, len(payload)) == payload


def test_fp8_pack_truncates_mantissa(bh):
  from struct import pack
  values = (1.01, 1.06, 1.07, 1.12, 1.13, 1.18, 1.19, 1.24)
  values += tuple(-v for v in values)
  source = pack('<16f', *values) + bytes(F32_TILE_BYTES - 64)
  images, profile = _images(0, 16, output_format=FP8_E4M3)
  bh.launch(images, params=(F32_TILE_BYTES, 16),
            l1={INPUT: source, OUTPUT: b'\xa5' * 128}, profiler=profile)
  # The late E4M3 conversion truncates; host nearest-even encoding is different.
  assert bh.read_l1(bh.core, OUTPUT, 16) == bytes((0x38,) * 4 + (0x39,) * 4 + (0xB8,) * 4 + (0xB9,) * 4)
