"""Smoke coverage for raw-kernel emulator scenarios."""

from __future__ import annotations

import pytest

from emu.tests.scenarios import run_add1


@pytest.mark.parametrize("cores", [1, 4], ids=lambda cores: f"cores_{cores}")
def test_add1_emu_smoke(cores: int):
  result = run_add1(cores=cores)
  assert result.output == result.expected
  assert result.steps > 0
