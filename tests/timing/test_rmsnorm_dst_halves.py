"""Reproduce the Dst-half effect in the original hybrid RMSNorm kernel.

Only scratch placement changes within each schedule. Prefetch and load macros
are disabled equally across schedules to isolate the FPU/SFPU comparison.
"""
import hashlib
import json
import os
from pathlib import Path
from statistics import median

import numpy as np
import pytest
from tests.compute.fpu import test_rmsnorm_hybrid as hybrid


@pytest.mark.parametrize('n', (1024, 2048))
def test_rmsnorm_dst_halves(bh, request, n):
    variants = {(schedule, tile): hybrid._images(n, schedule=schedule, scratch_tile=tile,
                square_macro=False, prefetch=False)
                for schedule in ('queued', 'interleaved', 'split0', 'split2') for tile in (0, 7)}
    samples = {key: [] for key in variants}
    rng = np.random.default_rng(42)
    gamma_bits = hybrid._bf16_round(rng.uniform(-1.5, 1.5, n))
    gamma = hybrid._from_bf16(gamma_bits).astype(np.float64)
    inputs = {'normal': rng.normal(size=n), 'arange': np.arange(n), 'zero': np.zeros(n),
              'outlier': np.concatenate(([100.], rng.normal(size=n-1)))}
    for kind, values in inputs.items():
        bits = hybrid._bf16_round(values)
        x = hybrid._from_bf16(bits).astype(np.float64)
        expected = x * gamma / np.sqrt(np.mean(x*x) + hybrid.EPS)
        for sample in range(16 if kind == 'normal' else 1):
            outputs = {}
            for key in tuple(variants)[::1 if sample % 2 == 0 else -1]:
                images, profile = variants[key]
                bh.launch(images, l1={hybrid.INPUT: bits.tobytes(), hybrid.GAMMA: gamma_bits.tobytes(),
                          hybrid.OUTPUT: b'\xa5'*(2*n+64), hybrid.SCALE: b'\xa5'*128,
                          hybrid.SPLIT_SYNC: bytes(32)})
                output = bh.read_l1(bh.core, hybrid.OUTPUT, 2*n)
                outputs[key] = output
                actual = hybrid._from_bf16(np.frombuffer(output, dtype='<u2'))
                np.testing.assert_allclose(actual, expected, rtol=0.004, atol=1e-7, err_msg=str((kind, key)))
                assert bh.read_l1(bh.core, hybrid.OUTPUT+2*n, 64) == b'\xa5'*64
                assert bh.read_l1(bh.core, hybrid.SCALE, 128) == b'\xa5'*128
                if kind == 'normal' and sample:
                    samples[key].append(hybrid._read_intervals(bh, profile.l1_address, ('L1 to L1', 'compute', 'pack')))
            for schedule in ('queued', 'interleaved', 'split0', 'split2'):
                assert outputs[schedule, 0] == outputs[schedule, 7], (kind, schedule, 'placement changed bits')
    for (schedule, tile), times in samples.items():
        images, _ = variants[schedule, tile]
        row = dict(n=n, schedule=schedule, scratch_tile=tile, product_tiles=list(range(1, n//1024+1)),
                   card=request.config.getoption('--bh-device'), core=list(bh.core), core_index=bh.core_index,
                   samples=times, medians={label: median(t[label] for t in times) for label in times[0]},
                   validation='normal/arange/zero/outlier; float64 reference; same-schedule placements bitwise equal; output guards',
                   source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   kernel_source_sha256=hashlib.sha256(Path(hybrid.__file__).read_bytes()).hexdigest(),
                   image_sha256={role: hashlib.sha256(image).hexdigest() for role,image in images.items()})
        print('RMSNORM_DST_HALVES ' + json.dumps(row, sort_keys=True))
        if output := os.environ.get('RMSNORM_HALVES_OUTPUT'):
            with Path(output).open('a') as f: f.write(json.dumps(row, sort_keys=True)+'\n')
