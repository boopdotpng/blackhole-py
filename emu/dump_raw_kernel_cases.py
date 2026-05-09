"""Dump emulator raw-kernel corpus sources and CB config.

This intentionally compiles kernels but does not create a hardware Device or
execute anything on a card.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from emu.kernel_runner import export_raw_kernel_cases
from emu.tests.test_kernels import (
  build_cases,
  build_multi_tile_cases,
  build_unary_copy_case,
)


def _cases():
  cases = [case.raw_kernel() for case in build_cases()]
  for num_tiles in (3, 5):
    cases.extend(case.raw_kernel() for case in build_multi_tile_cases(num_tiles))
  for cb_pages in (4, 8):
    cases.append(build_unary_copy_case(
      f"unary_copy_cb_pages_{cb_pages}",
      num_tiles=5,
      cb_pages=cb_pages,
    ).raw_kernel())
  for cb0, cb_out in ((3, 19), (7, 31)):
    cases.append(build_unary_copy_case(
      f"unary_copy_cb{cb0}_to_cb{cb_out}",
      num_tiles=5,
      cb0=cb0,
      cb_out=cb_out,
    ).raw_kernel())
  return cases


def main() -> int:
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "--output",
    type=Path,
    default=Path("emu/raw_kernel_cases.json"),
    help="JSON file to write",
  )
  args = parser.parse_args()

  path = export_raw_kernel_cases(_cases(), args.output)
  print(path)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
