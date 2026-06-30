#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402  (does sys.path + TT_USB bootstrap on import)
import riscv_noc_write_observe as observe
from asm import KernelBase
from device import Device
from program import DevMsgs, Program, Run, UnicastWrite
from ttk.addrs import Core, noc_xy
from ttk.noc import NOC
from ttk.tensix import TensixL1


@dataclass(frozen=True)
class Pair:
  source: Core
  target: Core


@dataclass(frozen=True)
class CoreResult:
  core: Core
  words: tuple[int, ...]

  @property
  def role(self) -> int:
    return self.words[1]

  @property
  def start(self) -> int:
    return observe.u64(self.words[8], self.words[9])

  @property
  def end(self) -> int:
    return observe.u64(self.words[10], self.words[11])

  @property
  def counter_before(self) -> int:
    return self.words[12]

  @property
  def counter_after(self) -> int:
    return self.words[13]


class AggregateProgram:
  def __init__(self, pairs: list[Pair], *, noc: int, stream_bytes: int,
               vcs: list[int | None] | None = None, posted: bool = False):
    self.pairs = list(pairs)
    self.noc = noc
    self.stream_bytes = stream_bytes
    self.posted = posted
    self.vcs = list(vcs) if vcs is not None else [None] * len(self.pairs)
    if len(self.vcs) != len(self.pairs):
      raise ValueError("vcs length must match pairs length")
    self.name = f"riscv_noc_aggregate:noc{noc}:pairs{len(pairs)}"

  def _one_core_segments(self, core: Core, kernel: KernelBase, *, dispatch_mode: int, host_assigned_id: int):
    empty = KernelBase()
    return Program(
      brisc=kernel,
      ncrisc=empty,
      trisc0=empty,
      trisc1=empty,
      trisc2=empty,
      num_cores=1,
    ).layout(core_xy=core, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id)

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    per_core_segments = {}
    target_cores = []
    for pair, vc in zip(self.pairs, self.vcs):
      write_ctrl = None if vc is None else observe.write_ctrl_for_vc(vc, posted=self.posted)
      sender = observe.build_sender(self.noc, self.stream_bytes, write_ctrl=write_ctrl, posted=self.posted)
      sender.rta(lambda _x, _y, target=pair.target: [noc_xy(*target)])
      receiver = observe.build_receiver(self.noc, self.stream_bytes)
      per_core_segments[pair.source] = self._one_core_segments(
        pair.source,
        sender,
        dispatch_mode=dispatch_mode,
        host_assigned_id=host_assigned_id,
      )
      per_core_segments[pair.target] = self._one_core_segments(
        pair.target,
        receiver,
        dispatch_mode=dispatch_mode,
        host_assigned_id=host_assigned_id,
      )
      target_cores.extend((pair.source, pair.target))

    reset_blob = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_RESET_READ_PTR_FROM_HOST)
    commands = [
      UnicastWrite(target_cores, TensixL1.GO_MSG, [reset_blob] * len(target_cores)),
      UnicastWrite(target_cores, TensixL1.GO_MSG_INDEX, [b"\0\0\0\0"] * len(target_cores)),
    ]
    for core in target_cores:
      for segment in per_core_segments[core]:
        commands.append(UnicastWrite([core], segment.addr, [segment.data]))
    commands.append(Run(target_cores))
    return commands


def rows_by_y(cores: list[Core]) -> dict[int, list[int]]:
  rows: dict[int, list[int]] = {}
  for x, y in cores:
    rows.setdefault(y, []).append(x)
  return {y: sorted(xs) for y, xs in rows.items()}


def adjacent_pairs(cores: list[Core], *, noc: int) -> list[Pair]:
  pairs = []
  for y, xs in sorted(rows_by_y(cores).items()):
    ordered = xs if noc == 0 else list(reversed(xs))
    for i in range(0, len(ordered) - 1, 2):
      pairs.append(Pair((ordered[i], y), (ordered[i + 1], y)))
  return pairs


def usable_program_cores(device: Device) -> list[Core]:
  reserved = {
    getattr(device.board_info, "dispatch_core", None),
    getattr(device.board_info, "prefetch_core", None),
  }
  return sorted(set(device.cores) - {core for core in reserved if core is not None})


def parse_counts(text: str) -> list[int]:
  counts = [int(item.strip()) for item in text.split(",") if item.strip()]
  if not counts or any(count <= 0 for count in counts):
    raise argparse.ArgumentTypeError("expected comma-separated positive pair counts")
  return counts


def clear_and_seed(device: Device, pairs: list[Pair], stream_bytes: int):
  seed = bytearray(NOC.MAX_BURST_SIZE)
  for off in range(0, len(seed), 4):
    struct.pack_into("<I", seed, off, 0xA5000000 | off)
  stream_seed = bytes(seed) * (stream_bytes // NOC.MAX_BURST_SIZE)
  with harness.device_window(device, pairs[0].source) as win:
    for pair in pairs:
      win.target(pair.source)
      win.write(observe.RESULT_BASE, b"\0" * observe.result_size())
      win.write(observe.STREAM_BASE, stream_seed)
      win.target(pair.target)
      win.write(observe.RESULT_BASE, b"\0" * observe.result_size())
      win.write(observe.STREAM_BASE, b"\0" * stream_bytes)


def read_core_result(device: Device, core: Core) -> CoreResult:
  return CoreResult(core, observe.read_result(device, core))


def run_once(device: Device, pairs: list[Pair], *, noc: int, stream_bytes: int,
             vcs: list[int | None] | None = None,
             posted: bool = False) -> tuple[list[CoreResult], list[CoreResult]]:
  clear_and_seed(device, pairs, stream_bytes)
  device.run(AggregateProgram(pairs, noc=noc, stream_bytes=stream_bytes, vcs=vcs, posted=posted))
  senders = [read_core_result(device, pair.source) for pair in pairs]
  receivers = [read_core_result(device, pair.target) for pair in pairs]
  return senders, receivers


def summarize(noc: int, stream_bytes: int, pairs: list[Pair], senders: list[CoreResult], receivers: list[CoreResult]) -> str:
  starts = [result.start for result in senders]
  acks = [result.end for result in senders]
  observed = [result.start for result in receivers]
  total_bytes = len(pairs) * stream_bytes
  sender_window = max(acks) - min(starts)
  observed_window = max(observed) - min(starts)
  sender_bpc = total_bytes / sender_window if sender_window > 0 else 0.0
  observed_bpc = total_bytes / observed_window if observed_window > 0 else 0.0
  bad_sentinels = sum(result.words[11] != observe.expected_sentinel(stream_bytes) for result in receivers)
  bad_acks = sum(((result.counter_after - result.counter_before) & 0xFFFFFFFF) != stream_bytes // NOC.MAX_BURST_SIZE for result in senders)
  return (
    f"| {noc} | {len(pairs)} | {total_bytes / (1024 * 1024):.1f} | "
    f"{sender_window} | {sender_bpc:.3f} | {observed_window} | {observed_bpc:.3f} | "
    f"{bad_acks} | {bad_sentinels} |"
  )


def main():
  parser = argparse.ArgumentParser(description="Run multiple simultaneous peer L1 NoC write streams.")
  parser.add_argument("--noc", type=int, choices=(0, 1), default=0)
  parser.add_argument("--bytes", type=int, default=1024 * 1024, help="payload bytes per sender; multiple of 16 KiB")
  parser.add_argument("--counts", type=parse_counts, default=parse_counts("1,2,4,8,16,32,60"), help="comma-separated pair counts")
  parser.add_argument("--no-report", action="store_true", help="do not append docs/noc-aggregate.md")
  parser.add_argument("--report", type=Path, default=harness.doc_path("noc", "noc-aggregate.md"), help="markdown report path")
  args = parser.parse_args()
  if args.bytes <= 0 or args.bytes % NOC.MAX_BURST_SIZE:
    raise ValueError("--bytes must be a positive multiple of 16 KiB")
  if args.bytes > observe.RESULT_BASE - observe.STREAM_BASE:
    raise ValueError(f"--bytes must fit below result range; max is {observe.RESULT_BASE - observe.STREAM_BASE}")

  lines = [
    "| noc | pairs | total MiB | sender window cyc | sender agg B/cyc | receiver window cyc | receiver agg B/cyc | bad ack rows | bad sentinel rows |",
    "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
  ]
  with harness.open_device() as device:
    all_pairs = adjacent_pairs(usable_program_cores(device), noc=args.noc)
    if not all_pairs:
      raise ValueError("no adjacent same-row pairs available")
    for count in args.counts:
      if count > len(all_pairs):
        raise ValueError(f"requested {count} pairs but only {len(all_pairs)} disjoint adjacent pairs are available")
      pairs = all_pairs[:count]
      senders, receivers = run_once(device, pairs, noc=args.noc, stream_bytes=args.bytes)
      lines.append(summarize(args.noc, args.bytes, pairs, senders, receivers))

  table = "\n".join(lines)
  print(table)
  if not args.no_report:
    with args.report.open("a", encoding="utf-8") as f:
      f.write("\n## Run\n\n")
      f.write(f"- NoC: `{args.noc}`\n")
      f.write(f"- Bytes per sender: `{args.bytes}`\n")
      f.write("- Pairing: disjoint adjacent same-row sender/receiver pairs\n\n")
      f.write(table)
      f.write("\n")
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
