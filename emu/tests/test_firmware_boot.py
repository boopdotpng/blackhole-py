from emu.device import RUN_MSG_DONE
from emu.tests.scenarios import run_firmware_boot


def test_firmware_boot_dispatch_return_kernel():
  result = run_firmware_boot()
  assert result.boot_cycles > 0
  assert result.dispatch_cycles > 0
  assert result.tile_state
  assert all(go == RUN_MSG_DONE for _, go, _ in result.tile_state)
