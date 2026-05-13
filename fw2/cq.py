from __future__ import annotations

from asm import Kernel


def build_prefetch() -> Kernel:
  return Kernel(kind="brisc")


def build_dispatch() -> Kernel:
  return Kernel(kind="brisc")


def build_dispatch_subordinate() -> Kernel:
  return Kernel(kind="ncrisc")
