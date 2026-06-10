"""Shared host-side plumbing for the microbenching device benches.

Importing this module does the sys.path bootstrap that every bench used to
open-code (the 7-line shim + `if __package__ in (None, ""):` guard) by running
the `_bench_path` setup, and sets the slow-dispatch default `TT_USB=1`. After
`import harness`, the repo root, `examples/`, the microbenching root, and every
category subdir are on `sys.path`.

It also collects the helpers ~26 benches copy-paste verbatim:

  - parse_core(s)                      argparse type for "X,Y" logical cores
  - read_wall_clock(fw, lo, hi)        emit the WALL_CLOCK_{H,L} read into a kernel
  - open_device()                      context manager: Device() + close()
  - device_window(device, core)        context manager: power on + TLBWindow + power off
  - read_window / clear_window / seed_window  L1 helpers with the all-0xff guard
  - append_report(path, title, ...)    the datetime + `## Run` markdown template

Per-bench result-record codecs are intentionally left in their own modules.
"""
from __future__ import annotations

import contextlib
import datetime as _dt
import os
import sys
from pathlib import Path as _Path

# --- bootstrap: path setup + slow-dispatch default -------------------------
# Insert the microbenching root so `_bench_path` (and this module) resolve, then
# run `_bench_path`, which adds the repo root, examples/, and the category dirs.
sys.path.insert(0, str(_Path(__file__).resolve().parent))
import _bench_path  # noqa: E402,F401

os.environ.setdefault("TT_USB", "1")

from asm import KernelBase  # noqa: E402
from device import Device  # noqa: E402
from dsl import a6, a7  # noqa: E402
from pcie import TLBWindow  # noqa: E402
from ttk.tensix import TensixMMIO  # noqa: E402

Core = tuple[int, int]

ALL_FF_ERROR = "L1 readback returned all 0xff; device is not responding cleanly and likely needs a host reboot"


def parse_core(s: str) -> Core:
  import argparse

  try:
    x, y = s.split(",", 1)
    return int(x, 0), int(y, 0)
  except ValueError as e:
    raise argparse.ArgumentTypeError("core must be X,Y") from e


def read_wall_clock(fw: KernelBase, lo, hi, *, addr=a7, hi2=a6):
  retry = fw._new_label("wall_clock_retry")
  fw.li(addr, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_H)
  fw.label(retry)
  fw.lw(hi, addr, 0)
  fw.lw(lo, addr, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L - TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_H)
  fw.lw(hi2, addr, 0)
  fw.bne(hi, hi2, retry)
  return fw


@contextlib.contextmanager
def open_device():
  """Open a Device and guarantee close() on exit."""
  device = Device()
  try:
    yield device
  finally:
    device.close()


@contextlib.contextmanager
def device_window(device: Device, core: Core, **window_kwargs):
  """Power the device on, open a TLBWindow at `core`, power off on exit.

  Replaces the hand-rolled set_power_state(True)/try/finally/set_power_state(False)
  blocks. Extra keyword args (e.g. addr=...) are forwarded to TLBWindow.
  """
  device.dev.set_power_state(True)
  try:
    with TLBWindow(device.dev, start=core, **window_kwargs) as win:
      yield win
  finally:
    device.dev.set_power_state(False)


def _check_not_all_ff(blob: bytes, error: str | None):
  if blob and all(b == 0xFF for b in blob):
    raise RuntimeError(error or ALL_FF_ERROR)


def read_window(device: Device, core: Core, address: int, size: int, *, error: str | None = None) -> bytes:
  """Read `size` bytes at `address` from `core`'s L1, with the all-0xff guard baked in."""
  with device_window(device, core) as win:
    blob = win.read(address, size)
  _check_not_all_ff(blob, error)
  return blob


def clear_window(device: Device, core: Core, ranges):
  """Zero each (address, size) range in `core`'s L1."""
  with device_window(device, core) as win:
    for address, size in ranges:
      win.write(address, b"\0" * size)


def seed_window(device: Device, core: Core, writes):
  """Write each (address, bytes) pair into `core`'s L1."""
  with device_window(device, core) as win:
    for address, payload in writes:
      win.write(address, payload)


def append_report(path, title, bullets, table=None):
  """Append the standard `## Run <timestamp>` block.

  `bullets` is an iterable of already-formatted bullet bodies (no leading "- ").
  `table` is an optional pre-rendered markdown table string.
  `title`, when given, is appended after the timestamp on the heading line.
  """
  path = _Path(path)
  now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
  heading = f"## Run {now}" + (f" {title}" if title else "")
  with path.open("a", encoding="utf-8") as f:
    f.write(f"\n{heading}\n\n")
    for bullet in bullets:
      f.write(f"- {bullet}\n")
    if table is not None:
      f.write("\n")
      f.write(table)
      f.write("\n")
