from device import Device
from pcie import TLBWindow
from program import Kernel

MARKER = 0xC0DEF00D

def main():
  device = Device(0, idx=0)
  try:
    device.init_device()
    kernel = Kernel(device.pcie.cores)
    result = kernel.l1(4, alignment=4)
    kernel.brisc.write(result, MARKER)
    kernel.brisc.fence()
    program = kernel.build()

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
