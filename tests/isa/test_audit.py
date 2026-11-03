"""Guard against false coverage credit and unsafe diagnostic instrumentation."""
import ctypes
import json

import pytest

from pcie import Sysmem, TLBWindow
from tests.isa import audit
from tests.isa.record import Recorder


def test_reviewed_claims_have_real_test_selectors():
  data = audit.build()
  assert len(data['instructions']) == 137
  assert all(row['status'] in ('partial', 'no reviewed behavioral claim') for row in data['instructions'])
  # Merely used as fixture plumbing is not automatically a reviewed contract.
  assert any(row['source_sightings'] and not row['reviewed_requirements'] for row in data['instructions'])
  assert data['dynamic_dispatch_sites'], 'dynamic opcode dispatch must remain visible as a limitation'


@pytest.mark.parametrize('phases,expected', (
  ({'call': {'outcome': 'passed'}, 'teardown': {'outcome': 'passed'}}, 'passed'),
  ({'call': {'outcome': 'passed'}, 'teardown': {'outcome': 'failed'}}, 'failed'),
  ({'setup': {'outcome': 'skipped'}}, 'skipped'),
  ({'call': {'outcome': 'skipped', 'xfail': 'documented divergence'}}, 'xfail'),
  ({'call': {'outcome': 'passed'}}, 'incomplete'),
  ({}, 'incomplete'),
))
def test_outcomes_do_not_turn_skips_or_teardown_failures_into_passes(phases, expected):
  assert audit.outcome(phases) == expected


def test_compact_evidence_preserves_failures(tmp_path):
  source, target = tmp_path / 'raw.json', tmp_path / 'compact.json'
  failure = {'call': {'outcome': 'failed', 'detail': 'wrong value'}}
  source.write_text(json.dumps({'tests': {
    'tests/test_example.py::test_value[a]': {'call': {'outcome': 'passed'}, 'teardown': {'outcome': 'passed'}},
    'tests/test_example.py::test_value[b]': failure,
    'tests/test_example.py::test_value[c]': {'setup': {'outcome': 'skipped'}},
  }}))
  audit.compact_evidence(source, target)
  data = json.loads(target.read_text())
  assert data['function_outcomes']['tests/test_example.py::test_value'] == {'passed': 1, 'failed': 1, 'skipped': 1}
  assert data['failures']['tests/test_example.py::test_value[b]'] == failure


@pytest.mark.parametrize('cls', (Sysmem, TLBWindow))
def test_native_mapping_diagnostics_guard_edges_and_closed_mapping(cls, monkeypatch):
  storage = ctypes.create_string_buffer(b'abcdefgh', 8)
  mapping = object.__new__(cls)
  mapping.addr = ctypes.addressof(storage)
  if cls is Sysmem: mapping.size = 8
  else: mapping.SIZE = 8
  recorder = object.__new__(Recorder)
  recorder.patch = monkeypatch
  recorder.wrap(cls, 'read')
  recorder.wrap(cls, 'write')
  assert mapping.read(0, 8) == b'abcdefgh'
  mapping.write(1, b'XYZ')
  assert mapping.read(0, 8) == b'aXYZefgh'
  assert mapping.read(8, 0) == b''
  for offset, length in ((-1, 1), (0, 9), (7, 2), (9, 0), (0, -1)):
    with pytest.raises(ValueError): mapping.read(offset, length)
  for offset, data in ((-1, b'x'), (0, b'x' * 9), (7, b'xy')):
    with pytest.raises(ValueError): mapping.write(offset, data)
  mapping.addr = None
  with pytest.raises(ValueError): mapping.read(0, 1)
  with pytest.raises(ValueError): mapping.write(0, b'x')
