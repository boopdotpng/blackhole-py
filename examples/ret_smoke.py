#!/usr/bin/env python3
from __future__ import annotations

import os

os.environ.setdefault("TT_USB", "1")

from asm import Kernel
from device import Device
from program import Program

def ret_kernel() -> Kernel:
  return Kernel().ret()

def main():
  device = Device()
  try:
    trisc0, trisc1, trisc2 = (ret_kernel(), ret_kernel(), ret_kernel())
    prog = Program(
      num_cores=len(device.cores),
      brisc=Kernel(),
      ncrisc=Kernel(),
      trisc0=trisc0,
      trisc1=trisc1,
      trisc2=trisc2,
    )
    prog.name = "ret_smoke"
    device.run(prog)
    print(f"PASS ret_smoke: launched ret kernels on {len(device.cores)} core(s)")
  finally:
    device.close()

if __name__ == "__main__":
  main()
