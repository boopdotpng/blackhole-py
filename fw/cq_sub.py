from __future__ import annotations

from asm import Kernel


def build() -> Kernel:
  return Kernel(kind="ncrisc")
