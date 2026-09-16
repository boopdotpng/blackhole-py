"""Completion-checked write-only contention probe, including all 117 workers."""
import json
from statistics import median
from unittest.mock import patch

import pytest

from tests.movement import test_noc as noc


@pytest.mark.parametrize('count', (16, 117))
@pytest.mark.parametrize('page_bytes', (2048, 16384))
@pytest.mark.parametrize('routing', ('baseline', 'preferred'))
def test_output_writers(bh, count, page_bytes, routing):
  device = bh.device
  if count > len(device.cores):
    pytest.skip('not enough workers')
  cores = device.cores[:count]
  banks = len(device.pcie.dram_endpoints)
  # Whole bank rounds make each worker shard occupy a disjoint address range.
  byte_count = banks * page_bytes * 16
  depth, batch = 16, 8
  result = device.alloc_interleaved_dram(count * byte_count, page_size=page_bytes)
  device.write_dram(result, b'\xa5' * result.size)
  page = bytes((i*131 + i//251 + 7) & 255 for i in range(page_bytes))
  images = []
  with patch.object(noc, 'SCALING_PAGE_BYTES', page_bytes):
    for network in range(2):
      coordinates = tuple(pair[network if routing == 'preferred' else 0][0] |
                          pair[network if routing == 'preferred' else 0][1] << 6
                          for pair in device.pcie.dram_endpoints)
      images.append(noc._one_way_images(coordinates, depth, batch, read=False, noc=network))
  mapped = {core: images[(i % 2) ^ 1] for i, core in enumerate(cores)}
  params = {core: (0, byte_count, result.address + i*byte_count//banks)
            for i, core in enumerate(cores)}
  rates = []
  for iteration in range(4):
    bh.launch_many_mapped(mapped, params=params, l1={noc.CB_ADDRESS: page*depth})
    timings = [noc._CoreTiming.read(bh, core) for core in cores]
    cycles = max(t.ncrisc_end for t in timings) - min(t.ncrisc_start for t in timings)
    if iteration:
      rates.append(count*byte_count*noc.CLOCK_GHZ/cycles)
  assert device.read_dram(result) == page * (count*byte_count//page_bytes)
  print(json.dumps(dict(cores=count, page_bytes=page_bytes, routing=routing,
                       gb_s=rates, median_gb_s=median(rates))))
