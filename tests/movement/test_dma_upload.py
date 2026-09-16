"""Host DMA scatter: page layout, staging tails, and cross-engine ordering."""
import random

import pytest

from cq import Dma, DramCopy
from firmware.consts import DRAM_UPLOAD_BATCH_SIZE


@pytest.mark.parametrize('banks', (1, 3, 7, 8))
@pytest.mark.parametrize('page', (64, 192, 1024, 2048, 16384))
def test_upload_block_tails(bh, banks, page):
  device = bh.device
  if banks > len(device.pcie.dram_endpoints):
    pytest.skip('bank count is not available on this board')
  limit = DRAM_UPLOAD_BATCH_SIZE // page
  rng = random.Random(page + banks)
  # One engine, transition to both engines, buffer reuse, and partial stripes.
  for count in (1, banks + 1, limit - 1, limit, limit + 1, 2 * limit + 1, 4 * limit + 17):
    size = count * page - 13  # Also exercise the host API's final-page padding.
    buffer = device.alloc_interleaved_dram(size, page_size=page, banks=banks)
    data = rng.randbytes(size)
    device.write_dram(buffer, data)
    assert device.read_dram(buffer) == data, (banks, page, count)


@pytest.mark.parametrize('page,banks', ((1024, 7), (2048, 8)))
def test_queued_upload_download_overwrite(bh, page, banks):
  device = bh.device
  if banks > len(device.pcie.dram_endpoints):
    pytest.skip('bank count is not available on this board')
  size = (2 * (DRAM_UPLOAD_BATCH_SIZE // page) + 13) * page
  buffer = device.alloc_interleaved_dram(size, page_size=page, banks=banks)
  rng = random.Random(page)
  a, b = rng.randbytes(size), rng.randbytes(size)
  host = device.pcie.sysmem.noc_addr + device.cq.dram
  device.pcie.sysmem.write(device.cq.dram, a + b + bytes(2 * size))
  def copy(offset, direction):
    return DramCopy(buffer.address, host + offset, page, buffer.page_count, banks, direction)
  # No intervening signals: changing from block ownership to bank ownership
  # must not let either engine overwrite bytes the other still needs.
  device.cq.submit((copy(0, 0), copy(2 * size, 1), copy(size, 0), copy(3 * size, 1)))
  assert device.pcie.sysmem.read(device.cq.dram + 2 * size, size) == a
  assert device.pcie.sysmem.read(device.cq.dram + 3 * size, size) == b


def test_tagged_dma_uses_upload_scatter(bh):
  device = bh.device
  banks = len(device.pcie.dram_endpoints)
  size = (2 * (DRAM_UPLOAD_BATCH_SIZE // 2048) + 13) * 2048
  device._dram.alloc(0, 2048)
  buffer = device.alloc_interleaved_dram(size)
  address = (1 << 63) | (buffer.address * banks)
  host = device.pcie.sysmem.noc_addr + device.cq.dram
  data = random.Random(42).randbytes(size)
  device.pcie.sysmem.write(device.cq.dram, data + bytes(size))
  device.cq.submit((Dma(address, host, size), Dma(host + size, address, size)))
  assert device.pcie.sysmem.read(device.cq.dram + size, size) == data
