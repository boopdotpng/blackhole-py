import os

from device import Device
from pcie import TLBWindow
from program import Program


MARKER = 0xC0DEF00D


def main():
  device_index = int(os.environ.get("TT_VISIBLE_DEVICES", "0").split(",")[0])
  device = Device(device_index)
  try:
    device.init_device()
    program = Program(device.pcie.cores)
    result = program.l1(4, alignment=4)
    program.brisc.write(result, MARKER)
    program.brisc.fence()

    with TLBWindow(device.pcie.fd, device.pcie.cores[0]) as window:
      for core in device.pcie.cores:
        window.target(0, core)
        window.write(result, 0)

    device.run(program, timeout=30.0)

    failures = []
    with TLBWindow(device.pcie.fd, device.pcie.cores[0]) as window:
      for core in device.pcie.cores:
        window.target(0, core)
        actual = int.from_bytes(window.read(result, 4), "little")
        if actual != MARKER: failures.append((core, actual))
    if failures:
      detail = ", ".join(
        f"{core}={actual:#010x}" for core, actual in failures[:8]
      )
      raise RuntimeError(
        f"{len(failures)}/{len(device.pcie.cores)} cores failed: {detail}"
      )
    print(
      f"PASS: {len(device.pcie.cores)} cores wrote {MARKER:#010x} "
      f"to L1 {result:#x}"
    )
  finally:
    device.close()


if __name__ == "__main__": main()
