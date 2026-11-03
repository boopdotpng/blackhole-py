"""Time the actual queued and RISC-V-looped emitters after inputs reach L1."""
import hashlib
import json
import os
from pathlib import Path
from statistics import median
import numpy as np
import pytest
from tests.compute.fpu import test_rmsnorm_hybrid as hybrid
from tests.profiler import Profiler


@pytest.mark.parametrize('n', (2048, 4096))
def test_rmsnorm_production_timing(bh, request, n):
    from examples.llama3 import Llama3Kernels
    from examples import rmsnorm_hybrid as emitter
    from program import Buffer, DType, TensorProgram
    rng = np.random.default_rng(192)
    xb = hybrid._bf16_round(rng.normal(size=n))
    gb = hybrid._bf16_round(rng.uniform(-2, 2, n))
    x, gamma = (hybrid._from_bf16(b).astype(np.float64) for b in (xb, gb))
    ref = x*gamma/np.sqrt(np.mean(x*x)+hybrid.EPS)
    allocations = [bh.dram_buffer(len(data), initial=data)
                   for data in (xb.tobytes(), gb.tobytes(), bytes(4*n))]
    buffers = tuple(Buffer(name, a.address, DType.BF16, (n,), None, (bh.core,), 1,
                    tilized=False, dram_endpoints=bh.device.pcie.dram_endpoints[:1])
                    for name, a in zip(('x','gamma','y'), allocations))
    finalize = Llama3Kernels('1b' if n == 2048 else '8b')._rms_finalize_scale()
    variants = {}
    samples = {False: [], True: []}
    for half in (False, True):
        p = TensorProgram((bh.core,), *buffers, fp32_dst=True)
        cb = p.cb(DType.BF16, depth=n//1024)
        profile = Profiler(p.trisc1)
        emitter.emit_rmsnorm(p, buffers[0], buffers[1], cb, tiles=n//1024,
                            finalize=finalize, half_sync=half, profile=profile)
        p.ncrisc.noc.write_tiles_from_cb(cb, buffers[2], tuple(range(n//1024)))
        params = tuple(np.frombuffer(p._param_table()[0], dtype='<u4').tolist())
        variants[half] = p.lower()[bh.core], params, profile
    for sample in range(52):
        outputs = {}
        for half in (False, True)[::1 if sample % 2 == 0 else -1]:
            binary, params, profile = variants[half]
            bh.launch(binary, params=params)
            raw = bh.read(allocations[2])
            outputs[half] = raw
            np.testing.assert_allclose(hybrid._from_bf16(np.frombuffer(raw[:2*n], dtype='<u2')),
                                       ref, rtol=.004, atol=1e-7)
            assert raw[2*n:] == bytes(2*n)
            if sample >= 2:
                samples[half].append(hybrid._read_intervals(bh, profile.l1_address, ('L1 to L1','compute','pack')))
        assert outputs[False] == outputs[True]
    for half in samples:
        row = dict(n=n, half_sync=half, core=list(bh.core), card=request.config.getoption('--bh-device'),
            samples=samples[half], medians={k:median(s[k] for s in samples[half]) for k in samples[half][0]},
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            emitter_source_sha256=hashlib.sha256(Path(emitter.__file__).read_bytes()).hexdigest(),
            image_sha256={k:hashlib.sha256(v).hexdigest() for k,v in variants[half][0].items()})
        print(json.dumps(row))
        if output := os.environ.get('RMS_PRODUCTION_OUTPUT'):
            with Path(output).open('a') as f: f.write(json.dumps(row)+'\n')
