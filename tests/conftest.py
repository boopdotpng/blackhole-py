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


@pytest.fixture(scope="session")
def bh(request):
  if not request.config.getoption("--bh-hardware"):
    pytest.skip("pass --bh-hardware to run raw Blackhole kernels")
  index = request.config.getoption("--bh-device")
  device_path = Path(f"/dev/tenstorrent/{index}")
  if not device_path.exists():
    pytest.skip(f"{device_path} is not present")

  # An xdist invocation or a second shell must not reset the same card while
  # this session owns it.  The lock is intentionally held until teardown.
  lock_path = Path(f"/tmp/blackhole-py-raw-device-{index}.lock")
  with lock_path.open("w") as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    device = Device(index)
    try:
      device.boot()
      core_index = request.config.getoption("--bh-core")
      if not 0 <= core_index < len(device.cores):
        pytest.fail(
          f"--bh-core={core_index} is outside 0..{len(device.cores) - 1}",
        )
      yield RawHarness(
        device, timeout=request.config.getoption("--bh-timeout"),
        core_index=core_index,
      )
    finally:
      device.close()
