"""Retain the software and physical execution context with queued measurements."""
import hashlib
import json
from pathlib import Path

import pytest
from fw.build import source_files


@pytest.fixture(scope='session', autouse=True)
def fpu_context(bh, request):
    root = Path(__file__).resolve().parents[3]
    paths = [*source_files(), root / 'device.py', root / 'cq.py']
    paths += sorted(Path(__file__).parent.glob('*.py'))
    print('FPU_CONTEXT ' + json.dumps(dict(
        device=request.config.getoption('--bh-device'), core_index=bh.core_index,
        core=list(bh.core), timeout=bh.timeout,
        firmware='C firmware BHCQ0002',
        sha256={str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
    ), sort_keys=True))
