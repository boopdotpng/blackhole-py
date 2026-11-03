import fcntl
from pathlib import Path

import pytest

from device import Device
from tests.harness import RawHarness


def pytest_addoption(parser):
  group = parser.getgroup("blackhole raw RISC-V")
  group.addoption(
    "--bh-hardware", action="store_true",
    help="run raw RISC-V tests on a Blackhole card",
  )
  group.addoption(
    "--bh-device", type=int, default=0,
    help="Tenstorrent device index used by --bh-hardware (default: 0)",
  )
  group.addoption(
    "--bh-core", type=int, default=0,
    help="worker-core index used by single-core raw tests (default: 0)",
  )
  group.addoption(
    "--bh-timeout", type=float, default=10.0,
    help="timeout in seconds for each raw launch/copy (default: 10)",
  )


class CardOwner:
  """Hold the card lock for the session and hand the card to one runtime.

  The session-scoped ``bh`` harness boots a raw Device lazily. A test that
  needs its own TensorDevice takes the card through ``tensor_device``; that
  closes the raw Device, and ``bh`` boots a fresh one on its next use.
  Taking the lock a second time in this process would deadlock: flock locks
  belong to each open file description, not to the process.
  """

  def __init__(self, index):
    self.index = index
    self._lock = Path(f"/tmp/blackhole-py-raw-device-{index}.lock").open("w")
    try: fcntl.flock(self._lock, fcntl.LOCK_EX)
    except BaseException: self._lock.close(); raise
    self._raw = None

  def raw(self):
    if self._raw is None:
      device = Device(self.index)
      device.boot()
      self._raw = device
    return self._raw

  def release_raw(self):
    device, self._raw = self._raw, None
    if device is not None: device.close()

  def close(self):
    try: self.release_raw()
    finally: self._lock.close()


def _require_card(request, purpose):
  if not request.config.getoption("--bh-hardware"):
    pytest.skip(f"pass --bh-hardware to run {purpose}")
  index = request.config.getoption("--bh-device")
  device_path = Path(f"/dev/tenstorrent/{index}")
  if not device_path.exists():
    pytest.skip(f"{device_path} is not present")
  return index


@pytest.fixture(scope="session")
def card(request):
  # An xdist invocation or a second shell must not reset the same card while
  # this session owns it. The lock is intentionally held until teardown.
  owner = CardOwner(_require_card(request, "Blackhole hardware tests"))
  try: yield owner
  finally: owner.close()


@pytest.fixture(scope="session")
def bh(request, card):
  _require_card(request, "raw Blackhole kernels")
  core_index = request.config.getoption("--bh-core")
  cores = card.raw().cores
  if not 0 <= core_index < len(cores):
    pytest.fail(f"--bh-core={core_index} is outside 0..{len(cores) - 1}")
  return RawHarness(
    card, timeout=request.config.getoption("--bh-timeout"),
    core_index=core_index,
  )


@pytest.fixture
def tensor_device(request, card):
  """A freshly booted TensorDevice that owns the card for one test."""
  from device import TensorDevice
  _require_card(request, "TensorDevice tests")
  card.release_raw()
  device = TensorDevice(card.index)
  try:
    device.boot()
    yield device
  finally:
    device.close()
