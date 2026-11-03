"""End-to-end hybrid RMSNorm with semaphore-owned scratch buffers."""
import hashlib
import json
import os
from pathlib import Path
from statistics import median
import numpy as np
import pytest
from tests.compute.fpu import test_rmsnorm_hybrid as hybrid


@pytest.mark.parametrize('n', (1024, 2048, 3072, 4096))
@pytest.mark.parametrize('macro', (False, True))
def test_rmsnorm_half_pipeline(bh, request, n, macro):
    options = {'queued': {}, 'queued_upper': {'scratch_tile': 7},
               'lower_products': {'scratch_tile': 7, 'product_first_tile': 0},
               'half_lower_products': {'schedule': 'half2', 'scratch_tile': 7,
                   'scratch_tiles': (7,), 'product_first_tile': 0},
               'half_alternate': {'schedule': 'half2', 'scratch_tiles': (0, 7)},
               'upper_single': {'schedule': 'half2', 'scratch_tiles': (7,)},
               'upper_double': {'schedule': 'half2', 'scratch_tiles': (6, 7)}}
    variants = {name: hybrid._images(n, square_macro=macro, prefetch=True, **kw)
                for name, kw in options.items()}
    times = {name: [] for name in variants}
    rng = np.random.default_rng(84)
    inputs = {'normal': rng.normal(size=n), 'arange': np.arange(n), 'zero': np.zeros(n),
              'small': rng.normal(size=n)*1e-8, 'large': rng.normal(size=n)*1e8,
              'outlier': rng.normal(size=n)}
    for tile in range(n//1024):
        inputs['normal'][tile*1024:(tile+1)*1024] *= 2**tile
        inputs['outlier'][tile*1024] = (tile+1)*100
    gb = hybrid._bf16_round(rng.uniform(-2, 2, n))
    gamma = hybrid._from_bf16(gb).astype(np.float64)
    for kind, values in inputs.items():
        xb = hybrid._bf16_round(values)
        x = hybrid._from_bf16(xb).astype(np.float64)
        ref = x*gamma/np.sqrt(np.mean(x*x)+hybrid.EPS)
        for sample in range(32 if kind == 'normal' else 1):
            outputs = {}
            for name in tuple(variants)[::1 if sample % 2 == 0 else -1]:
                images, profile = variants[name]
                bh.launch(images, l1={hybrid.INPUT: xb.tobytes(), hybrid.GAMMA: gb.tobytes(),
                    hybrid.OUTPUT: b'\xa5'*(2*n+64), hybrid.SCALE: b'\xa5'*128,
                    hybrid.SPLIT_SYNC: bytes(32)})
                output = bh.read_l1(bh.core, hybrid.OUTPUT, 2*n)
                outputs[name] = output
                y = hybrid._from_bf16(np.frombuffer(output, dtype='<u2'))
                np.testing.assert_allclose(y, ref, rtol=.004, atol=1e-7, err_msg=str((n, macro, name, kind)))
                assert bh.read_l1(bh.core, hybrid.OUTPUT+2*n, 64) == b'\xa5'*64
                assert bh.read_l1(bh.core, hybrid.SCALE, 128) == b'\xa5'*128
                if kind == 'normal' and sample >= 2:
                    times[name].append(hybrid._read_intervals(bh, profile.l1_address, ('L1 to L1', 'compute', 'pack')))
            assert all(o == outputs['queued'] for o in outputs.values()), (n, macro, kind)
    for name, samples in times.items():
        row = dict(n=n, macro=macro, schedule=name, options=options[name], core=list(bh.core),
            card=request.config.getoption('--bh-device'), samples=samples,
            medians={k:median(s[k] for s in samples) for k in samples[0]},
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            kernel_source_sha256=hashlib.sha256(Path(hybrid.__file__).read_bytes()).hexdigest(),
            image_sha256={k:hashlib.sha256(v).hexdigest() for k,v in variants[name][0].items()})
        print(json.dumps(row))
        if output := os.environ.get('RMS_HALF_OUTPUT'):
            with Path(output).open('a') as f: f.write(json.dumps(row)+'\n')


@pytest.mark.parametrize('n, calls', ((2048, 2), (4096, 2)))
def test_half_pipeline_production_sequence(bh, n, calls):
    """Compare the real emitters, including repeated calls and CB/DRAM transport."""
    from examples.llama3 import Llama3Kernels
    from examples.rmsnorm_hybrid import emit_rmsnorm
    from program import Buffer, DType, TensorProgram
    rng = np.random.default_rng(191)
    xb = hybrid._bf16_round(rng.normal(size=n))
    gb = hybrid._bf16_round(rng.uniform(-2, 2, n))
    x = hybrid._from_bf16(xb).astype(np.float64)
    gamma = hybrid._from_bf16(gb).astype(np.float64)
    ref = x*gamma/np.sqrt(np.mean(x*x)+hybrid.EPS)
    allocations = [bh.dram_buffer(len(data), initial=data)
                   for data in (xb.tobytes(), gb.tobytes(), bytes(4*n), bytes(4*n))]
    buffers = tuple(Buffer(name, allocation.address, DType.BF16, (n,), None,
                    (bh.core,), 1, tilized=False, dram_endpoints=bh.device.pcie.dram_endpoints[:1])
                    for name, allocation in zip(('x', 'gamma', 'y0', 'y1'), allocations))
    finalize = Llama3Kernels('1b' if n == 2048 else '8b')._rms_finalize_scale()
    outputs = {}
    for half_sync in (False, True):
        p = TensorProgram((bh.core,), *buffers, fp32_dst=True)
        for index in range(calls):
            cb = p.cb(DType.BF16, depth=n//1024)
            emit_rmsnorm(p, buffers[0], buffers[1], cb, tiles=n//1024,
                         finalize=finalize, half_sync=half_sync)
            p.ncrisc.noc.write_tiles_from_cb(cb, buffers[index+2], tuple(range(n//1024)))
        params = tuple(np.frombuffer(p._param_table()[0], dtype='<u4').tolist())
        binary = p.lower()[bh.core]
        from firmware.consts import TensixL1
        assert all(len(v) <= TensixL1.WORKER_TEXT_SIZE[k] for k, v in binary.items())
        print('PRODUCTION_SEQUENCE', n, half_sync, {k:len(v) for k,v in binary.items()})
        for _ in range(3):
            bh.launch(binary, params=params)
            for index in range(calls):
                raw = bh.read(allocations[index+2])
                y = hybrid._from_bf16(np.frombuffer(raw[:2*n], dtype='<u2'))
                np.testing.assert_allclose(y, ref, rtol=.004, atol=1e-7)
                assert raw[2*n:] == bytes(2*n)
                outputs[half_sync, index] = raw
    assert all(raw == outputs[False, 0] for raw in outputs.values())
