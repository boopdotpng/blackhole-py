"""Validate split GQA, tail masking, and stable merge against NumPy."""
import fcntl
from pathlib import Path

import numpy as np
import pytest

from examples.llama3 import Llama3Kernels
from pcie import P100_WORKER_CORES
from program import DType
from device import TensorDevice


@pytest.fixture
def llama_device(request):
  if not request.config.getoption('--bh-hardware'):
    pytest.skip('pass --bh-hardware to run Llama attention')
  index = request.config.getoption('--bh-device')
  if not Path(f'/dev/tenstorrent/{index}').exists():
    pytest.skip('device is absent')
  with open(f'/tmp/blackhole-py-raw-device-{index}.lock', 'w') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    device = TensorDevice(index)
    try:
      device.boot()
      yield device
    finally:
      device.close()


def bf16(values):
  values = np.asarray(values, dtype=np.float32)
  return (values.view(np.uint32) & np.uint32(0xffff0000)).view(np.float32)


@pytest.mark.parametrize('length', [1, 31, 32, 33, 129, 512, 1025, 4096])
def test_split_gqa_against_numpy(llama_device, length):
  device = llama_device
  kernels = Llama3Kernels('8b', 'fp8')
  rng = np.random.default_rng(17)
  q = bf16(rng.normal(size=(32, 128)))
  k = bf16(rng.normal(size=(8, length, 128)))
  v = bf16(rng.normal(size=(8, length, 128)))
  # Large masked values expose reading beyond the final sequence position.
  blocks = (length + 31) // 32
  cache_shape = (8, 256, 4, 32, 32)
  caches = []
  for name, values in (('keys', k), ('values', v)):
    cache = device.dram.buffer(name, DType.BF16, kernels.KV_CACHE_STORAGE_SHAPE,
                               axis=0, global_address=True)
    packed = np.zeros(cache_shape, dtype=np.float32)
    live = np.full((8, blocks * 32, 128), 20., dtype=np.float32)
    live[:, :length] = values
    packed[:, :blocks] = live.reshape(8, blocks, 32, 4, 32).transpose(0, 1, 3, 2, 4)
    device.write(cache, cache.from_numpy(packed.reshape(cache.shape)))
    caches.append(cache)
  query = device.dram.buffer('queries', DType.BF16, (32, 1024), axis=0, global_address=True)
  values = np.zeros(query.shape, dtype=np.float32)
  values[:, :128] = q
  device.write(query, query.from_numpy(values))
  output = device.dram.buffer('context', DType.BF16, (1, 4096), axis=0, global_address=True, tilized=False)
  partials = device.dram.buffer('partials', DType.F32, (32, 6, 1024), axis=0, cores=P100_WORKER_CORES[:32])
  split = kernels.gqa_attention_fused(query, *caches, output, partial_output=partials)
  merge = kernels.gqa_attention_merge(partials, output)
  single = kernels.gqa_attention_fused(query, *caches, output)
  params = {'kv_blocks': blocks, 'valid_columns': (length - 1) % 32 + 1}
  device.run()
  device.cache_kernels((single, split, merge))
  results = []
  for program, do_merge in ((single, False), (split, True)):
    device.queue(program, params=params)
    if do_merge: device.queue(merge)
    trace = device.capture_trace(tuple(params))
    trace.replay(params)
    results.append(output.to_numpy(device.read(output)).reshape(32, 128))
  expected = []
  for head in range(32):
    scores = k[head // 4] @ q[head] / np.sqrt(128)
    probabilities = np.exp(scores - scores.max())
    expected.append(probabilities @ v[head // 4] / probabilities.sum())
  expected = np.asarray(expected)
  for label, actual in zip(('single', 'split'), results):
    assert np.isfinite(actual).all()
    pcc = np.corrcoef(actual.ravel(), expected.ravel())[0, 1]
    relative_rms = np.linalg.norm(actual - expected) / np.linalg.norm(expected)
    print(f'{length=} {label}: PCC={pcc:.7f} relative_RMS={relative_rms:.7f}')
    # The unsplit implementation accumulates all 128 blocks at 4K; its
    # existing low-precision online update is less accurate there. Require
    # the new split path to meet the same bound at every tested length.
    if label == 'split' or length <= 1025:
      assert pcc > .999, (label, pcc)
      assert relative_rms < .03, (label, relative_rms)
  if length >= 1024:
    assert np.linalg.norm(results[1] - expected) < np.linalg.norm(results[0] - expected)
