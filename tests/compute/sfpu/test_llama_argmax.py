"""Exercise the actual Llama argmax, publication, history and resident replay."""
import fcntl
from pathlib import Path

import numpy as np
import pytest

from device import TensorDevice
from examples.llama3 import Llama3Kernels
from firmware.consts import TensixL1
from pcie import TLBWindow
from program import DType


@pytest.fixture
def llama_device(request):
    if not request.config.getoption('--bh-hardware'):
        pytest.skip('pass --bh-hardware to run Llama argmax')
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


@pytest.mark.parametrize('model,dtype', [('1b', 'bf16'), ('8b', 'bf16'), ('8b', 'fp8')])
@pytest.mark.parametrize('core_count', [80, 88, 96, 104, 112, 117])
def test_llama_argmax(llama_device, model, dtype, core_count):
    d = llama_device
    k = Llama3Kernels(model, dtype, projection_cores=core_count)
    cores = tuple(d.cores[i] for i in np.linspace(0, len(d.cores) - 1, core_count, dtype=int))
    counts = k._token_counts(k.VOCAB_SIZE, core_count)
    logits = d.dram.buffer('logits', DType.BF16, (core_count, max(counts)), axis=0, cores=cores)
    history = d.dram.buffer('history', DType.U32, (2048,), axis=None,
                            cores=cores, global_address=True, tilized=False)
    program = k.decode_argmax(logits, history, d.cq.noc + d.cq.live)
    d.cache_kernels([program])
    d.queue(program, report=False)
    trace = d.capture_trace(('write_pos', 'write_token'))
    for case in ('random', 'negative_ties', 'positive_ties', 'last', 'zeros',
                 'infinities', 'all_negative_infinity', 'subnormals'):
        values = np.random.default_rng(61).normal(size=k.VOCAB_SIZE).astype('<f4')
        if case.endswith('ties'):
            values[:] = -9
            values[[17, 64, counts[0] + 3, k.VOCAB_SIZE - 1]] = -1 if case == 'negative_ties' else 7
        elif case == 'last':
            values[:] = -9
            values[-1] = -1
        elif case == 'zeros':
            values[:] = -0.
            values[[17, 64]] = 0.
        elif case == 'infinities':
            values[:] = -np.inf
            values[-1] = np.inf
        elif case == 'all_negative_infinity':
            values[:] = -np.inf
        elif case == 'subnormals':
            values[:] = np.float32(-2**-130)
            values[-1] = np.float32(2**-130)
        words = (values.view('<u4') >> 16).astype('<u2')
        keys = np.where(words >> 15, (~words) & 65535, words ^ 0x8000)
        expected = int(keys.argmax())
        # Poison unused shard slots. Buffer's additional tile padding is zero.
        data = np.full(logits.shape, 0x7f80, dtype='<u2')
        start = 0
        for row, count in zip(data, counts):
            row[:count] = words[start:start + count]
            start += count
        d.write(logits, data.tobytes())
        sentinel = np.full(history.shape, 0xdeadbeef, dtype='<u4')
        d.write(history, sentinel.tobytes())
        d.run()
        for position, append in ((17, True), (1023, False), (1024, True)):
            trace.replay({'write_pos': position, 'write_token': int(append)})
            actual = int.from_bytes(d.pcie.sysmem.read(d.cq.live + position * 16, 4), 'little')
            assert actual == expected, (case, actual, expected)
            if append: sentinel[position] = expected
            actual_history = np.frombuffer(d.read(history), dtype='<u4')
            bad = np.flatnonzero(actual_history != sentinel)
            assert not len(bad), (case, position, bad.tolist(), actual_history[bad].tolist(), sentinel[bad].tolist())
            # The winner also advances device-side replay state on every core.
            for core in (cores[0], cores[-1]):
                with TLBWindow(d.pcie.fd, core) as window:
                    address = TensixL1.RUNTIME_PARAM_BASE
                    window.target(address & -TLBWindow.SIZE)
                    state = np.frombuffer(window.read(address % TLBWindow.SIZE, 24), dtype='<u4')
                assert tuple(state) == (position, position + 1, 1, position,
                                        position // 32 + 1, position % 32 + 1)
