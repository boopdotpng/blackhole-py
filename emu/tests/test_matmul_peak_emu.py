from emu.tests.scenarios import run_matmul_peak_grid


def test_matmul_peak_emu_default_grid_smoke():
  assert run_matmul_peak_grid() == 0
