import numpy as np
import pytest

from examples.llama3 import PagedProjectionWeight
from pcie import P100_DRAM_ENDPOINTS, P100_WORKER_CORES
from program import Buffer, DType
from tests.fp8 import decode, encode
from tools.llama_fp8 import quantize_rows


def test_row_quantization_matches_independent_e4m3_reference():
  levels = np.array([decode(code) for code in range(8, 127)], dtype=np.float32)
  midpoints = (levels[:-1] + levels[1:]) / 2
  values = np.concatenate((levels, midpoints, -levels, -midpoints, [0., 448.]))
  rows = np.stack((values, values / 16, values * 2))
  codes, scales = quantize_rows(rows)
  expected = np.frombuffer(encode(values), dtype=np.uint8)
  np.testing.assert_array_equal(codes, np.broadcast_to(expected, codes.shape))
  np.testing.assert_array_equal(scales, [1., 1/16, 2.])


def test_zero_rows_and_nonfinite_weights():
  codes, scales = quantize_rows(np.zeros((2, 16)))
  assert not codes.any()
  np.testing.assert_array_equal(scales, [1., 1.])
  with pytest.raises(ValueError): quantize_rows([[np.nan]])
  with pytest.raises(ValueError): quantize_rows([[np.inf]])


@pytest.mark.parametrize('width,page_tiles', [(4096, 1), (4096, 2), (4096, 4), (14336, 2)])
def test_paged_projection_storage_preserves_rows_and_bytes(width, page_tiles):
  original = Buffer('weight', 0x10000, DType.FP8, (128, width), 0,
                    P100_WORKER_CORES[:96], 8, global_address=True,
                    tilized=False, dram_endpoints=P100_DRAM_ENDPOINTS)
  paged = PagedProjectionWeight.from_buffer(original, page_tiles)
  assert paged.size == original.size
  assert paged.item_counts == original.item_counts
  assert paged.item_starts == original.item_starts
  assert paged.tiles_per_item == original.tiles_per_item
  # Every row's page mapping reconstructs its exact checkpoint byte range.
  seen = set()
  for row in range(128):
    for page in range(width // paged.tile_size):
      logical = row * width // paged.tile_size + page
      bank, offset = logical % 8, logical // 8 * paged.tile_size
      assert (bank, offset) not in seen
      seen.add((bank, offset))
  assert len(seen) * paged.tile_size == paged.size


def test_paged_projection_rejects_partial_rows():
  original = Buffer('weight', 0x10000, DType.FP8, (128, 14336), 0,
                    P100_WORKER_CORES[:96], 8, global_address=True,
                    tilized=False, dram_endpoints=P100_DRAM_ENDPOINTS)
  with pytest.raises(ValueError): PagedProjectionWeight.from_buffer(original, 4)


def test_subnormal_boundary_rounds_before_flush():
  values = np.array([[0., 1/512, 7/512, 15/1024, 1/64, 448.]], dtype=np.float32)
  codes, scales = quantize_rows(values)
  np.testing.assert_array_equal(codes, [[0, 0, 0, 8, 8, 126]])
  np.testing.assert_array_equal(scales, [1.])


def test_tiny_finite_rows_do_not_divide_by_zero():
  codes, scales = quantize_rows([[np.nextafter(np.float32(0), np.float32(1))]])
  assert np.isfinite(scales).all() and (scales > 0).all()
  assert not codes.any()


def test_larger_pages_cannot_overrun_a_partial_bank_stripe():
  original = Buffer('tiny', 0x10000, DType.FP8, (1, 4096), 0,
                    P100_WORKER_CORES[:1], 8, global_address=True,
                    tilized=False, dram_endpoints=P100_DRAM_ENDPOINTS)
  with pytest.raises(ValueError): PagedProjectionWeight.from_buffer(original, 2)
