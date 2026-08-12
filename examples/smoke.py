import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from device import Device
from pcie import TLBWindow
from program import Kernel, Program


def marker_program(cores, marker):
  kernel = Kernel(cores)
  result = kernel.l1(4, alignment=4)
  kernel.brisc.write(result, marker)
  kernel.brisc.fence()
  return result, kernel.build()


def verify(device, result, expected, name):
  failures = []
  with TLBWindow(device.pcie.fd, device.pcie.cores[0]) as window:
    for core in device.pcie.cores:
      window.target(0, core)
      actual = int.from_bytes(window.read(result, 4), "little")
      if actual != expected[core]: failures.append((core, actual, expected[core]))
  if failures:
    detail = ", ".join(
      f"{core}={actual:#010x} expected {wanted:#010x}"
      for core, actual, wanted in failures[:8]
    )
    raise RuntimeError(f"{name}: {len(failures)} cores failed: {detail}")
  print(f"PASS: {name}")

def main():
  device = Device(0, idx=0)
  try:
    device.init_device()
    cores = tuple(device.pcie.cores)
    result, program = marker_program(cores, 0xC0DEF00D)

    with TLBWindow(device.pcie.fd, device.pcie.cores[0]) as window:
      for core in cores:
        window.target(0, core)
        window.write(result, 0)

    device.run(program, timeout=30.0)
    expected = {core: 0xC0DEF00D for core in cores}
    verify(device, result, expected, "all 117 compute cores")

    row = tuple(core for core in cores if core[1] == 5)
    _, row_program = marker_program(row, 0x11111111)
    device.run(row_program, timeout=30.0)
    expected.update({core: 0x11111111 for core in row})
    verify(device, result, expected, "row multicast across columns 8/9")

    irregular = ((1, 2), (3, 4), (10, 6), (14, 11))
    _, irregular_program = marker_program(irregular, 0x22222222)
    device.run(irregular_program, timeout=30.0)
    expected.update({core: 0x22222222 for core in irregular})
    verify(device, result, expected, "irregular and unicast targets")

    senders = tuple(core for core in cores if core[1] == 7)
    receivers = ((2, 8), (4, 9), (13, 10))
    _, sender_program = marker_program(senders, 0x33333333)
    _, receiver_program = marker_program(receivers, 0x44444444)
    mixed = Program(
      senders + receivers,
      sender_program.images | receiver_program.images,
    )
    device.run(mixed, timeout=30.0)
    expected.update({core: 0x33333333 for core in senders})
    expected.update({core: 0x44444444 for core in receivers})
    verify(device, result, expected, "different images on core groups")
  finally:
    device.close()


if __name__ == "__main__": main()
