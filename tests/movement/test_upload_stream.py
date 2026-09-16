"""Pinned upload-slot lifetime, chunk boundaries, and ordered tensor uploads."""
import random

import pytest

from ttko import DType
from ttko.device import Device
from ttko.program import Dram


@pytest.fixture
def upload_device(bh):
  # Borrow the session's booted transport, so raw and tensor-runtime tests
  # share one device owner and cannot reset or deadlock each other's fixture.
  device = Device.__new__(Device)
  device.__dict__.update(bh.device.__dict__)
  device.dram = Dram(len(device.pcie.dram_endpoints), device.pcie.cores,
                     device.pcie.dram_endpoints)
  device.dram.allocator = device._dram
  device.program_queue, device.read_queue = [], []
  device._staging_next, device._upload_stream = 0, None
  device._cached_static = {}
  return device


@pytest.mark.parametrize('dtype', (DType.FP8, DType.BF16))
def test_upload_slot_reuse_and_tails(upload_device, dtype):
  d = upload_device
  buffers, payloads = [], []
  for i, pages in enumerate((1, 11, 97, 3, 65)):
    buffer = d.dram.buffer(f'upload_{i}', dtype, (pages * 1024,), None,
                           global_address=True, tilized=False)
    buffers.append(buffer)
    payloads.append(random.Random(i).randbytes(buffer.size))
  with d.upload_stream(slot_bytes=32 << 10) as stream:
    for buffer, data in zip(buffers, payloads):
      stream.write(buffer, data)
    # Overwriting a previously uploaded tensor must preserve queue order.
    stream.write(buffers[0], payloads[0][::-1])
    payloads[0] = payloads[0][::-1]
    with pytest.raises(RuntimeError, match='upload stream'):
      d.read(buffers[0])
    with pytest.raises(RuntimeError, match='upload stream'):
      d.run()
    with pytest.raises(RuntimeError, match='flush queued'):
      with d.upload_stream(): pass
  for buffer, data in zip(buffers, payloads):
    assert d.read(buffer) == data


def test_upload_context_drains_on_exception(upload_device):
  d = upload_device
  buffer = d.dram.buffer('exception', DType.BF16, (64 * 1024,), None,
                         global_address=True, tilized=False)
  data = random.Random(42).randbytes(buffer.size)
  with pytest.raises(ValueError, match='caller failed'):
    with d.upload_stream(slot_bytes=32 << 10) as stream:
      stream.write(buffer, data)
      raise ValueError('caller failed')
  assert d.read(buffer) == data
  with pytest.raises(RuntimeError, match='not active'):
    stream.write(buffer, data)


def test_upload_rejects_queued_staging(upload_device):
  d = upload_device
  buffer = d.dram.buffer('queued', DType.BF16, (1024,), None,
                         global_address=True, tilized=False)
  d.write(buffer, bytes(buffer.size))
  with pytest.raises(RuntimeError, match='flush queued'):
    with d.upload_stream(): pass
  d.run()
  with d.upload_stream(slot_bytes=64) as stream:
    with pytest.raises(ValueError, match='bank stripe'):
      stream.write(buffer, bytes(buffer.size))


@pytest.mark.parametrize('dtype,encoded', ((DType.FP8, 'F8_E4M3'), (DType.BF16, 'BF16')))
def test_direct_checkpoint_upload(upload_device, tmp_path, dtype, encoded):
  import json
  import struct
  from st import Safetensor

  d = upload_device
  # Seven banks force chunk sizes to round down to a whole bank stripe.
  dram = Dram(7, d.pcie.cores, d.pcie.dram_endpoints[:7])
  dram.allocator = d._dram
  buffer = dram.buffer('direct', dtype, (97 * 1024,), None,
                       global_address=True, tilized=False)
  data = random.Random(97).randbytes(buffer.size)
  header = json.dumps({'weight': {'dtype': encoded, 'shape': list(buffer.shape),
                                  'data_offsets': [0, len(data)]}}).encode()
  shard = tmp_path / 'part.safetensors'
  shard.write_bytes(struct.pack('<Q', len(header)) + header + data)
  (tmp_path / 'model.safetensors.index.json').write_text(json.dumps({
    'weight_map': {'weight': shard.name},
  }))
  reader = Safetensor(tmp_path)
  buffer.check_safetensor(reader.info('weight'))
  # Host loading must preserve every byte, including FP8 subnormals.
  assert buffer.from_safetensor('weight', reader) == data
  with d.upload_stream(slot_bytes=32 << 10) as stream:
    stream.write_from(buffer, lambda target, offset: reader.readinto('weight', target, offset))
  # Read through the raw API because this tensor uses a seven-bank prefix.
  from device import InterleavedDramBuffer
  raw = InterleavedDramBuffer(buffer.addr, buffer.size, buffer.size,
                              buffer.tile_size, buffer.physical_tiles, 7)
  from device import Device as RawDevice
  assert RawDevice.read_dram(d, raw) == data
  guard = bytearray(b'\xa5' * 32)
  reader.readinto('weight', memoryview(guard)[8:24], 13)
  assert guard == b'\xa5' * 8 + data[13:29] + b'\xa5' * 8
  with pytest.raises(ValueError, match='read exceeds'):
    reader.readinto('weight', guard, len(data) - 1)
  with shard.open('r+b') as file:
    file.truncate(shard.stat().st_size - 1)
  with pytest.raises(ValueError, match='ended while reading'):
    reader.readinto('weight', bytearray(1), len(data) - 1)
