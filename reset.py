#!/usr/bin/env python3
import argparse

from pcie import PCIDevice


def reset_device(index: int):
  devices = PCIDevice.list_devices()
  if index >= len(devices):
    raise RuntimeError(f"Blackhole device {index} not found (found {len(devices)})")
  bdf = devices[index].split('/')[-1]
  print(f"Resetting device {index} ({bdf}) ...")
  PCIDevice.reset_index(index)
  # Post-reset init: open device to send ARC A0 + watchdog (same as tt-kmd's init_hardware)
  with PCIDevice(index=index, use_vfio=False) as dev:
    print(f"  ARC ready, telemetry base 0x{dev.read_arc_apb32(dev.SCRATCH_RAM_12):08x}")
  print(f"Reset complete.")


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description="Standalone Blackhole reset tool")
  parser.add_argument("-r", "--reset", type=int, metavar="DEVICE", nargs="?", const=0, default=None,
                      help="reset a Blackhole device (default: device 0)")
  return parser.parse_args()


def main():
  args = parse_args()
  if args.reset is None:
    raise SystemExit("reset.py only supports reset; use -r [DEVICE]")
  reset_device(args.reset)


if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    pass
