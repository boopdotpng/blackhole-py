#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
from asm import KernelBase
from device import Device
from dsl import s2, s4, s5, s6, s7, s8, s9, t0, t3, t4
from program import DevMsgs, Program, Run, UnicastWrite
from ttk.addrs import Core
from ttk.blackhole_coords import raw_coord_for_noc, tensix_coordinate_map, translated_tensix_to_raw_noc0
from ttk.mailbox import BriscMailbox as BM
from ttk.noc import NOC, Noc
from ttk.tensix import TensixL1


RESULT_BASE = 0x170000
RESULT_MAGIC = 0x5845434D  # "MCEX"
STATUS_STARTED = 0x1C000001
STATUS_DONE = 0x1C00D00D
SCRATCH_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
WORD_SIZE = 4
ENABLED_TENSIX_COL_TAG = 34


@dataclass(frozen=True)
class McastRect:
  x0: int
  y0: int
  x1: int
  y1: int

  @property
  def cores(self) -> tuple[Core, ...]:
    return tuple((x, y) for x in range(self.x0, self.x1 + 1) for y in range(self.y0, self.y1 + 1))

  @property
  def size(self) -> int:
    return (self.x1 - self.x0 + 1) * (self.y1 - self.y0 + 1)


@dataclass(frozen=True)
class ProbeCase:
  name: str
  exclude: int


@dataclass(frozen=True)
class ProbeResult:
  case: ProbeCase
  hits: tuple[Core, ...]
  misses: tuple[Core, ...]


class McastExcludeKernel(KernelBase, Noc):
  pass


class McastExcludeProgram:
  def __init__(self, *, noc: int, source: Core, rect: McastRect, major: str,
               marker: int, exclude: int, settle_cycles: int):
    self.noc = noc
    self.source = source
    self.rect = rect
    self.major = major
    self.marker = marker
    self.exclude = exclude
    self.settle_cycles = settle_cycles
    self.name = f"riscv_noc_mcast_exclude_probe:noc{noc}:{source}:0x{exclude:x}"

  def lower(self, cores: list[Core] | None = None, *,
            dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    empty = KernelBase()
    sender = build_sender(
      noc=self.noc,
      rect=self.rect,
      major=self.major,
      marker=self.marker,
      exclude=self.exclude,
      settle_cycles=self.settle_cycles,
    )
    segments = Program(
      brisc=sender,
      ncrisc=empty,
      trisc0=empty,
      trisc1=empty,
      trisc2=empty,
      num_cores=1,
    ).layout(core_xy=self.source, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id, compiled_cache={})
    reset_blob = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_RESET_READ_PTR_FROM_HOST)
    commands = [
      UnicastWrite([self.source], TensixL1.GO_MSG, [reset_blob]),
      UnicastWrite([self.source], TensixL1.GO_MSG_INDEX, [b"\0\0\0\0"]),
    ]
    for segment in segments:
      commands.append(UnicastWrite([self.source], segment.addr, [segment.data]))
    commands.append(Run([self.source]))
    return commands


def parse_rect(text: str) -> McastRect:
  try:
    lo, hi = text.split(":", 1)
    x0, y0 = (int(part, 0) for part in lo.split(",", 1))
    x1, y1 = (int(part, 0) for part in hi.split(",", 1))
  except ValueError as exc:
    raise argparse.ArgumentTypeError("rect must be X0,Y0:X1,Y1") from exc
  if x1 < x0 or y1 < y0:
    raise argparse.ArgumentTypeError("rect end must be >= rect start")
  return McastRect(x0, y0, x1, y1)


def parse_core_list(text: str) -> tuple[Core, ...]:
  try:
    return tuple(harness.parse_core(item.strip()) for item in text.split(";") if item.strip())
  except Exception as exc:
    raise argparse.ArgumentTypeError("expected semicolon-separated cores as X,Y;X,Y") from exc


def parse_excludes(text: str) -> tuple[int, ...]:
  try:
    values = tuple(int(item.strip(), 0) for item in text.split(",") if item.strip())
  except ValueError as exc:
    raise argparse.ArgumentTypeError("expected comma-separated integer exclude values") from exc
  if not values:
    raise argparse.ArgumentTypeError("expected at least one exclude value")
  return values


def read_counter(fw: KernelBase, noc: int, counter: int, out, *, addr=t3):
  fw.li(addr, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  return fw.lw(out, addr, 0)


def wait_counter_at_least(fw: KernelBase, noc: int, counter: int, target, *, addr=t3, val=t4):
  fw.li(addr, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  loop = fw._new_label("wait_counter")
  fw.label(loop)
  fw.lw(val, addr, 0)
  fw.bltu(val, target, loop)
  return fw


def build_sender(*, noc: int, rect: McastRect, major: str, marker: int,
                 exclude: int, settle_cycles: int) -> KernelBase:
  fw = McastExcludeKernel()
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((RESULT_MAGIC, STATUS_STARTED, noc, marker, exclude, rect.x0, rect.y0, rect.x1, rect.y1)):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)

  fw.local_noc_coord(noc, s5, x_addr=BM.MY_X, y_addr=BM.MY_Y)
  fw.noc_cmd_reg(noc, 0, NOC.TARG_ADDR_COORDINATE, s5, addr=t3, tmp=t4)
  fw.noc_mcast_coord(s9, rect.x0, rect.y0, rect.x1, rect.y1)
  fw.li(s2, SCRATCH_BASE)
  fw.li(s4, WORD_SIZE)
  fw.li(s8, marker)
  fw.sw(s8, s2, 0)
  fw.fence()

  read_counter(fw, noc, NOC.NIU_MST_NONPOSTED_WR_REQ_SENT, s7, addr=t3)
  fw.addi(s7, s7, 1)
  fw.noc_write(
    noc, 0, s2, s2, 0, s9, s4,
    mcast=True,
    mcast_linked=False,
    mcast_exclude=exclude,
    mcast_path_reserve=True,
    mcast_y=(major == "y"),
    a=t3,
    v=t4,
  )
  wait_counter_at_least(fw, noc, NOC.NIU_MST_NONPOSTED_WR_REQ_SENT, s7, addr=t3, val=t4)
  if settle_cycles > 0:
    fw.delay_cycles(settle_cycles, count=s6)

  fw.li(s2, RESULT_BASE)
  fw.li(t0, STATUS_DONE)
  fw.sw(t0, s2, 1 * 4)
  return fw.ret()


def default_cases(anchor: Core, include_baseline: bool) -> tuple[ProbeCase, ...]:
  cases = []
  if include_baseline:
    cases.append(ProbeCase("none", 0))
  ax, ay = anchor
  for dx in (0, 1):
    for dy in (0, 1):
      cases.append(ProbeCase(f"dx{dx}_dy{dy}", NOC.mcast_exclude_quad(ax, ay, dir_x=dx, dir_y=dy)))
  return tuple(cases)


def raw_anchor_for(device: Device, logical_anchor: Core, noc: int) -> Core:
  layout = device.dev.telemetry_layout()
  enabled = device.dev.telemetry_tag(layout, ENABLED_TENSIX_COL_TAG)
  if enabled is None:
    raise RuntimeError("ENABLED_TENSIX_COL telemetry is unavailable")
  cmap = tensix_coordinate_map(enabled)
  return raw_coord_for_noc(translated_tensix_to_raw_noc0(logical_anchor, cmap), noc)


def clear_targets(device: Device, rect: McastRect, source: Core):
  with harness.device_window(device, source) as win:
    for core in rect.cores:
      win.target(core)
      win.write(SCRATCH_BASE, b"\0" * WORD_SIZE)
    win.target(source)
    win.write(RESULT_BASE, b"\0" * 64)


def run_case(device: Device, *, case: ProbeCase, noc: int, source: Core,
             rect: McastRect, major: str, marker: int, settle_cycles: int) -> ProbeResult:
  clear_targets(device, rect, source)
  device.run(McastExcludeProgram(
    noc=noc,
    source=source,
    rect=rect,
    major=major,
    marker=marker,
    exclude=case.exclude,
    settle_cycles=settle_cycles,
  ))
  hits: list[Core] = []
  misses: list[Core] = []
  marker_blob = struct.pack("<I", marker & 0xFFFFFFFF)
  with harness.device_window(device, source) as win:
    for core in rect.cores:
      win.target(core)
      blob = win.read(SCRATCH_BASE, WORD_SIZE)
      if blob == marker_blob:
        hits.append(core)
      else:
        misses.append(core)
  return ProbeResult(case=case, hits=tuple(hits), misses=tuple(misses))


def fmt_cores(cores: tuple[Core, ...]) -> str:
  if not cores:
    return "-"
  return " ".join(f"{x},{y}" for x, y in cores)


def format_results(results: list[ProbeResult], expected_excluded: tuple[Core, ...]) -> str:
  expected = tuple(sorted(expected_excluded))
  lines = [
    "| case | exclude | hits | misses | missed cores | expected? |",
    "|---|---:|---:|---:|---|---|",
  ]
  for result in results:
    misses = tuple(sorted(result.misses))
    ok = "yes" if misses == expected else "no"
    lines.append(
      f"| {result.case.name} | `0x{result.case.exclude:06x}` | {len(result.hits)} | "
      f"{len(result.misses)} | `{fmt_cores(misses)}` | {ok} |"
    )
  return "\n".join(lines)


def main() -> None:
  parser = argparse.ArgumentParser(description="Probe Blackhole NoC multicast exclude encoding.")
  parser.add_argument("--noc", type=int, choices=(0, 1), default=0)
  parser.add_argument("--major", choices=("x", "y"), default="x")
  parser.add_argument("--source", type=harness.parse_core, default=(1, 2))
  parser.add_argument("--rect", type=parse_rect, default=parse_rect("10,2:14,11"))
  parser.add_argument("--anchor", type=harness.parse_core, default=(14, 3))
  parser.add_argument("--raw-anchor", action="store_true", help="interpret --anchor as raw NoC coordinates")
  parser.add_argument("--expected-excluded", type=parse_core_list, default=parse_core_list("14,2;14,3"))
  parser.add_argument("--exclude", type=parse_excludes, default=None, help="comma-separated raw BRCST_EXCLUDE values")
  parser.add_argument("--skip-baseline", action="store_true")
  parser.add_argument("--marker", type=lambda s: int(s, 0), default=0x4D434558)
  parser.add_argument("--settle-cycles", type=int, default=4096)
  args = parser.parse_args()
  if args.settle_cycles < 0:
    raise ValueError("--settle-cycles must be non-negative")

  with harness.open_device() as device:
    missing = [core for core in (args.source, *args.rect.cores) if core not in set(device.cores)]
    if missing:
      raise RuntimeError(f"device does not expose required logical cores: {fmt_cores(tuple(missing))}")
    exclude_anchor = args.anchor if args.raw_anchor else raw_anchor_for(device, args.anchor, args.noc)
    if args.exclude is None:
      cases = default_cases(exclude_anchor, include_baseline=not args.skip_baseline)
    else:
      cases = tuple(ProbeCase(f"raw{i}", value) for i, value in enumerate(args.exclude))
    results = [
      run_case(
        device,
        case=case,
        noc=args.noc,
        source=args.source,
        rect=args.rect,
        major=args.major,
        marker=(args.marker + i) & 0xFFFFFFFF,
        settle_cycles=args.settle_cycles,
      )
      for i, case in enumerate(cases)
    ]

  print("mcast_exclude_probe")
  print(f"  source: {args.source[0]},{args.source[1]}")
  print(f"  rect: {args.rect.x0},{args.rect.y0}->{args.rect.x1},{args.rect.y1} ({args.rect.size} cores)")
  print(f"  anchor: {args.anchor[0]},{args.anchor[1]} {'raw' if args.raw_anchor else 'logical'}")
  print(f"  exclude anchor: {exclude_anchor[0]},{exclude_anchor[1]} raw noc{args.noc}")
  print(f"  expected excluded: {fmt_cores(tuple(sorted(args.expected_excluded)))}")
  print(format_results(results, tuple(args.expected_excluded)))


if __name__ == "__main__":
  main()
