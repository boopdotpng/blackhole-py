"""Smoke coverage for scratch emulator entrypoints."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def run_script(script: str, extra_env: dict[str, str] | None = None):
  env = os.environ.copy()
  if extra_env:
    env.update(extra_env)

  result = subprocess.run(
    [sys.executable, str(ROOT / script)],
    cwd=ROOT,
    env=env,
    text=True,
    capture_output=True,
    timeout=120,
    check=False,
  )

  assert result.returncode == 0, (
    f"{script} exited with {result.returncode}\n"
    f"stdout:\n{result.stdout}\n"
    f"stderr:\n{result.stderr}"
  )
  return result


@pytest.mark.parametrize("cores", [1, 4], ids=lambda cores: f"cores_{cores}")
def test_add1_emu_smoke(cores: int):
  result = run_script("add1_emu.py", {"CORES": str(cores)})
  assert "blackhole-py add1 raw-kernel emulation: pass" in result.stdout
  assert f"cores   : {cores} tensix cores" in result.stdout


def test_matmul_peak_emu_default_grid_smoke():
  result = run_script("matmul_peak_emu.py")
  assert "matmul_peak raw-kernel emulation: pass" in result.stdout
  assert "grid: 1x7 cores" in result.stdout
