#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
import riscv_noc_hop_sweep as hop_sweep  # noqa: E402
import riscv_noc_mcast_one_way_latency as mcast  # noqa: E402
from asm import KernelBase
from program import DevMsgs, Program, Run, UnicastWrite
from ttk.addrs import Core
from ttk.noc import NOC
from ttk.tensix import TensixL1


@dataclass(frozen=True)
class GroupSpec:
  name: str
  source: Core
  receivers: tuple[Core, ...]


@dataclass(frozen=True)
class CaseSpec:
  name: str
  groups: tuple[GroupSpec, ...]


GROUP_A = GroupSpec(
  "a",
  (1, 2),
  (
    (2, 3), (3, 3), (4, 3),
    (2, 4), (3, 4), (4, 4),
    (2, 5), (3, 5), (4, 5),
  ),
)

GROUP_B_DISJOINT = GroupSpec(
  "b",
  (10, 2),
  (
    (11, 3), (12, 3), (13, 3),
    (11, 4), (12, 4), (13, 4),
    (11, 5), (12, 5), (13, 5),
  ),
)

GROUP_B_SHARED_COLUMNS = GroupSpec(
  "b",
  (1, 6),
  (
    (2, 7), (3, 7), (4, 7),
    (2, 8), (3, 8), (4, 8),
    (2, 9), (3, 9), (4, 9),
  ),
)

GROUP_B_ADJACENT = GroupSpec(
  "b",
  (5, 2),
  (
    (6, 3), (7, 3), (10, 3),
    (6, 4), (7, 4), (10, 4),
    (6, 5), (7, 5), (10, 5),
  ),
)

CASES = {
  "solo_a": CaseSpec("solo_a", (GROUP_A,)),
  "disjoint": CaseSpec("disjoint", (GROUP_A, GROUP_B_DISJOINT)),
  "shared_columns": CaseSpec("shared_columns", (GROUP_A, GROUP_B_SHARED_COLUMNS)),
  "adjacent": CaseSpec("adjacent", (GROUP_A, GROUP_B_ADJACENT)),
}


def parse_cases(text: str) -> tuple[str, ...]:
  names = tuple(item.strip() for item in text.split(",") if item.strip())
  bad = [name for name in names if name not in CASES]
  if bad:
    raise argparse.ArgumentTypeError(f"unknown case(s): {','.join(bad)}")
  return names


def active_cores(case: CaseSpec) -> list[Core]:
  cores: set[Core] = set()
  for group in case.groups:
    cores.add(group.source)
    cores.update(group.receivers)
  return sorted(cores)


def validate_no_overlap(case: CaseSpec) -> None:
  seen: dict[Core, str] = {}
  for group in case.groups:
    for core in (group.source, *group.receivers):
      if core in seen:
        raise ValueError(f"case {case.name}: core {core} is shared by groups {seen[core]} and {group.name}")
      seen[core] = group.name


def seed_payload(packet_bytes: int) -> bytes:
  payload = bytearray(max(packet_bytes, NOC.MAX_BURST_SIZE))
  for off in range(0, len(payload), 4):
    struct.pack_into("<I", payload, off, 0xD5000000 | off)
  return bytes(payload)


def clear_and_seed(device, case: CaseSpec, packet_bytes: int, iters: int):
  payload = seed_payload(packet_bytes)
  with harness.device_window(device, case.groups[0].source) as win:
    for core in active_cores(case):
      win.target(core)
      win.write(mcast.RESULT_BASE, b"\0" * max(mcast.result_size_sender(iters), mcast.result_size_receiver(iters)))
      win.write(mcast.SRC_BASE, payload)


class DualMcastProgram:
  def __init__(
    self,
    *,
    case: CaseSpec,
    noc: int,
    major: str,
    packet_bytes: int,
    iters: int,
    rects: dict[str, mcast.McastRect],
    start_delay: int,
    inter_delay: int,
    path_reserve: bool,
  ):
    self.case = case
    self.noc = noc
    self.major = major
    self.packet_bytes = packet_bytes
    self.iters = iters
    self.rects = rects
    self.start_delay = start_delay
    self.inter_delay = inter_delay
    self.path_reserve = path_reserve
    self.name = f"riscv_noc_dual_mcast_probe:{case.name}:noc{noc}:{major}"

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    empty = KernelBase()
    compiled_cache: dict[int, list] = {}
    per_core_segments = {}
    for group in self.case.groups:
      sender = mcast.build_sender(
        self.noc,
        self.packet_bytes,
        self.iters,
        self.start_delay,
        self.inter_delay,
        self.rects[group.name],
        self.major,
        self.path_reserve,
      )
      per_core_segments[group.source] = Program(
        brisc=sender,
        ncrisc=empty,
        trisc0=empty,
        trisc1=empty,
        trisc2=empty,
        num_cores=1,
      ).layout(
        core_xy=group.source,
        dispatch_mode=dispatch_mode,
        host_assigned_id=host_assigned_id,
        compiled_cache=compiled_cache,
      )
      receiver_kernel = mcast.build_receiver(self.noc, self.packet_bytes, self.iters)
      receiver_program = Program(
        brisc=receiver_kernel,
        ncrisc=empty,
        trisc0=empty,
        trisc1=empty,
        trisc2=empty,
        num_cores=1,
      )
      for receiver in group.receivers:
        per_core_segments[receiver] = receiver_program.layout(
          core_xy=receiver,
          dispatch_mode=dispatch_mode,
          host_assigned_id=host_assigned_id,
          compiled_cache=compiled_cache,
        )

    active = active_cores(self.case)
    reset_blob = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_RESET_READ_PTR_FROM_HOST)
    commands = [
      UnicastWrite(active, TensixL1.GO_MSG, [reset_blob] * len(active)),
      UnicastWrite(active, TensixL1.GO_MSG_INDEX, [b"\0\0\0\0"] * len(active)),
    ]
    for core in active:
      for segment in per_core_segments[core]:
        commands.append(UnicastWrite([core], segment.addr, [segment.data]))
    commands.append(Run(active))
    return commands


def format_with_group(results: list[tuple[str, mcast.RunResult]]) -> str:
  lines = [
    "| case | group | noc | major | source | receiver | rect | raw route | hops | bytes | iters | seen-issue cyc | seen-sent cyc | sent reqs | recv polls |",
    "|---|---|---:|---|---|---|---|---|---:|---:|---:|---|---|---:|---:|",
  ]
  for group_name, result in results:
    route = result.route
    lines.append(
      f"| {result.case} | {group_name} | {result.noc} | {result.major} | "
      f"`{result.source[0]},{result.source[1]}` | `{route.receiver[0]},{route.receiver[1]}` | "
      f"`{result.rect.x0},{result.rect.y0}->{result.rect.x1},{result.rect.y1}` | "
      f"`{route.raw_source[0]},{route.raw_source[1]}->{route.raw_receiver[0]},{route.raw_receiver[1]}` | "
      f"{route.hops} | {result.packet_bytes} | {result.iters} | "
      f"{mcast.summarize(result.seen_minus_issue)} | {mcast.summarize(result.seen_minus_sent)} | "
      f"{result.sender_counter_delta} | {result.receiver_poll_iters} |"
    )
  return "\n".join(lines)


def main() -> None:
  parser = argparse.ArgumentParser(description="Run one or two simultaneous NoC multicast rectangles.")
  parser.add_argument("--cases", type=parse_cases, default=("solo_a", "disjoint", "shared_columns"))
  parser.add_argument("--nocs", type=hop_sweep.parse_nocs, default=(0,))
  parser.add_argument("--majors", type=mcast.parse_majors, default=("x",))
  parser.add_argument("--sizes", type=mcast.parse_sizes, default=mcast.parse_sizes("16384"))
  parser.add_argument("--iters", type=int, default=8)
  parser.add_argument("--start-delay", type=int, default=4096)
  parser.add_argument("--inter-delay", type=int, default=2048)
  parser.add_argument("--path-reserve", action="store_true")
  args = parser.parse_args()
  if args.iters <= 0:
    raise ValueError("--iters must be positive")

  all_results: list[tuple[str, mcast.RunResult]] = []
  with harness.open_device() as device:
    core_set = set(device.cores)
    cmap = mcast.read_tensix_coordinate_map(device)
    for case_name in args.cases:
      case = CASES[case_name]
      validate_no_overlap(case)
      missing = sorted(set(active_cores(case)) - core_set)
      if missing:
        raise ValueError(f"case {case.name}: unavailable cores {missing}")
      for noc in args.nocs:
        rects = {
          group.name: mcast.logical_rect_for_physical_span(group.receivers, noc=noc, cmap=cmap)
          for group in case.groups
        }
        for major in args.majors:
          for packet_bytes in args.sizes:
            clear_and_seed(device, case, packet_bytes, args.iters)
            device.run(DualMcastProgram(
              case=case,
              noc=noc,
              major=major,
              packet_bytes=packet_bytes,
              iters=args.iters,
              rects=rects,
              start_delay=args.start_delay,
              inter_delay=args.inter_delay,
              path_reserve=args.path_reserve,
            ))
            for group in case.groups:
              routes = {
                receiver: mcast.receiver_route(group.source, receiver, noc=noc, cmap=cmap)
                for receiver in group.receivers
              }
              parsed = mcast.parse_results(
                device,
                noc=noc,
                case=case.name,
                major=major,
                source=group.source,
                receivers=group.receivers,
                rect=rects[group.name],
                routes=routes,
                packet_bytes=packet_bytes,
                iters=args.iters,
              )
              all_results.extend((group.name, result) for result in parsed)

  print(format_with_group(all_results))


if __name__ == "__main__":
  main()
