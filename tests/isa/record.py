"""Opt-in pytest evidence and native-memory diagnostics.

Use -p tests.isa.record --isa-record=/tmp/run.json [--isa-memory-checks].
A separate .current.json file survives a native crash and records its test ID.
The final JSON records phase outcomes, xfails/skips, and source fingerprints.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time

import pytest


def source_hashes(root):
  return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
          for directory in ('tests', 'ttko', 'firmware')
          for p in sorted((root / directory).rglob('*.py'))} | {
            str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.glob('*.py'))} | {
            str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((root / 'firmware').rglob('*'))
            if p.is_file() and p.suffix in ('.c', '.h', '.S', '.ld')} | {
            'tests/isa/inventory.json': hashlib.sha256((root / 'tests/isa/inventory.json').read_bytes()).hexdigest()}


def pytest_addoption(parser):
  group = parser.getgroup('ISA evidence')
  group.addoption('--isa-record', help='write per-test outcomes and source fingerprints to JSON')
  group.addoption('--isa-memory-checks', action='store_true', help='check host mapping bounds before ctypes reads/writes')


def pytest_configure(config):
  path = config.getoption('--isa-record')
  if path:
    config.pluginmanager.register(Recorder(config, Path(path)), 'isa-evidence-recorder')


class Recorder:
  def __init__(self, config, path):
    self.config, self.path = config, path
    self.patch = pytest.MonkeyPatch()
    self.data = {'started_unix': time.time(), 'pid': os.getpid(), 'python': sys.version,
                 'platform': platform.platform(), 'argv': sys.argv,
                 'hardware': config.getoption('--bh-hardware'),
                 'device': config.getoption('--bh-device'), 'core': config.getoption('--bh-core'),
                 'environment': {name: os.environ.get(name) for name in
                   ('PYTHONMALLOC', 'PYTHONDEVMODE', 'TRANSPORT_LENGTHS', 'BLACKHOLE_DEBUG')},
                 'memory_checks': config.getoption('--isa-memory-checks'),
                 'capture': config.getoption('capture'),
                 'source_sha256': source_hashes(Path(__file__).resolve().parents[2]),
                 'tests': {}, 'complete': False}
    self.path.parent.mkdir(parents=True, exist_ok=True)
    self.save()
    if config.getoption('--isa-memory-checks'):
      from pcie import Sysmem, TLBWindow
      for cls in (Sysmem, TLBWindow):
        for name in ('read', 'write'):
          self.wrap(cls, name)

  def wrap(self, cls, method):
    original = getattr(cls, method)

    def checked(obj, offset, *args, **kwargs):
      size = obj.size if hasattr(obj, 'size') else obj.SIZE
      if method == 'read':
        length = args[0] if args else kwargs.get('size', kwargs.get('bytes', 4))
      else:
        value = args[0] if args else kwargs.get('data', kwargs.get('value'))
        length = (args[1] if len(args) > 1 else kwargs.get('bytes', 4)) if isinstance(value, int) else len(value)
      if obj.addr is None or offset < 0 or length < 0 or offset + length > size:
        raise ValueError(f'{cls.__name__}.{method}: offset={offset} length={length} mapping={size} addr={obj.addr}')
      return original(obj, offset, *args, **kwargs)
    self.patch.setattr(cls, method, checked)

  def save(self):
    temporary = self.path.with_suffix('.tmp')
    temporary.write_text(json.dumps(self.data, indent=2) + '\n')
    temporary.replace(self.path)

  def pytest_runtest_logstart(self, nodeid, location):
    current = {'pid': os.getpid(), 'nodeid': nodeid, 'started_unix': time.time()}
    self.path.with_suffix('.current.json').write_text(json.dumps(current) + '\n')

  def pytest_runtest_logreport(self, report):
    record = self.data['tests'].setdefault(report.nodeid, {})
    record[report.when] = {'outcome': report.outcome, 'duration': report.duration}
    if hasattr(report, 'wasxfail'): record[report.when]['xfail'] = str(report.wasxfail)
    if report.failed or report.skipped:
      record[report.when]['detail'] = str(report.longrepr)[-12000:]
    if report.failed: self.save()

  def pytest_sessionfinish(self, session, exitstatus):
    self.data.update(finished_unix=time.time(), exitstatus=int(exitstatus), complete=True)
    self.save()
    self.patch.undo()
