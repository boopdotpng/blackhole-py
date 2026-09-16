"""Queued runtime metadata, emitted after the selected hardware fixture boots."""
import hashlib
import json
from pathlib import Path

import pytest
from firmware import source_files


@pytest.fixture(scope='session', autouse=True)
def runtime_context(bh, request):
  root = Path(__file__).resolve().parents[3]
  print('RUNTIME_CONTEXT ' + json.dumps({
    'card': request.config.getoption('--bh-device'),
    'core_index': bh.core_index, 'core': bh.core,
    'worker_count': len(bh.device.cores),
    'dram_endpoints': bh.device.pcie.dram_endpoints,
    'firmware_source_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files()},
    'runtime_sha256': hashlib.sha256((root / 'device.py').read_bytes()).hexdigest(),
    'ops_sha256': hashlib.sha256((Path(__file__).parent / 'ops.py').read_bytes()).hexdigest(),
  }, sort_keys=True))
