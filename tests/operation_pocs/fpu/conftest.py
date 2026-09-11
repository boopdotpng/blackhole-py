"""Retain the software and physical execution context with queued measurements."""
import hashlib
import json
from pathlib import Path

import pytest


@pytest.fixture(scope='session', autouse=True)
def fpu_context(bh, request):
    root = Path(__file__).resolve().parents[3]
    paths = [root / name for name in ('fw/llama3-manifest.json', 'fw/build.py', 'fw/consts.py', 'device.py', 'cq.py')]
    paths += sorted(Path(__file__).parent.glob('*.py'))
    print('FPU_CONTEXT ' + json.dumps(dict(
        device=request.config.getoption('--bh-device'), core_index=bh.core_index,
        core=list(bh.core), timeout=bh.timeout,
        firmware='vendored llama3 cce3e77f3a245dadfaa4a29ae3a0dda499b53708',
        sha256={str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
    ), sort_keys=True))
