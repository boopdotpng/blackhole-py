from __future__ import annotations
from asm import Firmware
from dsl import *

def build(trisc_id: int) -> Firmware:
  if trisc_id not in (0, 1, 2):
    raise ValueError(f"unknown TRISC id {trisc_id!r}")
  return Firmware(f"trisc{trisc_id}")

def build_trisc0() -> Firmware:
  f = Firmware()
  pass

def build_trisc1() -> Firmware:
  pass

def build_trisc2() -> Firmware:
  pass
