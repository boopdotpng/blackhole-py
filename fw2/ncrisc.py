from __future__ import annotations

from asm import Firmware


def build() -> Firmware:
  return Firmware("ncrisc")
