import pytest

from examples.llama3 import PagedProjectionWeight
from pcie import P100_DRAM_ENDPOINTS, P100_WORKER_CORES
from program import Buffer, DType


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


def test_larger_pages_cannot_overrun_a_partial_bank_stripe():
  original = Buffer('tiny', 0x10000, DType.FP8, (1, 4096), 0,
                    P100_WORKER_CORES[:1], 8, global_address=True,
                    tilized=False, dram_endpoints=P100_DRAM_ENDPOINTS)
  with pytest.raises(ValueError): PagedProjectionWeight.from_buffer(original, 2)
