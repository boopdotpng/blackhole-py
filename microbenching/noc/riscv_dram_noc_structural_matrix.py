#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
import riscv_dram_noc_bench as dram  # noqa: E402
import riscv_noc_contention_probe as probe  # noqa: E402
from asm import KernelBase  # noqa: E402
from program import DevMsgs, Dtype, Program, Run, UnicastWrite  # noqa: E402
from ttk.addrs import Core, noc_xy, p100_dram_bank_base_coords, p100_dram_bank_endpoint_coords  # noqa: E402
from ttk.noc import NOC  # noqa: E402
from ttk.tensix import TensixL1  # noqa: E402


CASE_NAMES = (
  "same-dram-bank",
  "different-banks-same-dram-column",
  "banks-0-3",
  "banks-4-7",
  "alternating-halves",
  "same-route-links",
  "disjoint-route-links",
)


@dataclass(frozen=True)
class DramStream:
  name: str
  core: Core
  op: int
  noc: int
  bank: int
  start_page: int
  endpoint: int
  coord: int


class StructuralDramProgram:
  def __init__(
    self,
    streams: list[DramStream],
    *,
    dram_base: int,
    bank_count: int,
    packet_bytes: int,
    packet_count: int,
    stateful: bool,
    use_start_gate: bool,
  ):
    self.streams = list(streams)
    self.dram_base = dram_base
    self.bank_count = bank_count
    self.packet_bytes = packet_bytes
    self.packet_count = packet_count
    self.stateful = stateful
    self.use_start_gate = use_start_gate
    self.name = f"riscv_dram_noc_structural_matrix:streams{len(streams)}"

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    empty = KernelBase()
    per_core_segments = {}
    target_cores = [stream.core for stream in self.streams]
    if len(set(target_cores)) != len(target_cores):
      raise ValueError("DRAM structural streams require distinct active cores")
    args_by_core = {
      stream.core: [
        self.dram_base,
        self.bank_count,
        self.packet_bytes,
        self.packet_count,
        stream.bank,
        stream.start_page,
        stream.coord,
      ]
      for stream in self.streams
    }
    for stream in self.streams:
      kernel = dram.build_kernel(
        op=stream.op,
        noc=stream.noc,
        stateful=self.stateful,
        use_start_gate=self.use_start_gate,
      )
      kernel.rta(lambda x, y, args_by_core=args_by_core: args_by_core[(x, y)])
      program = Program(
        brisc=kernel,
        ncrisc=empty,
        trisc0=empty,
        trisc1=empty,
        trisc2=empty,
        num_cores=1,
      )
      per_core_segments[stream.core] = program.layout(
        core_xy=stream.core, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id,
      )

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


def _fmt_core(core: Core) -> str:
  return f"{core[0]},{core[1]}"


def parse_csv_choices(text: str, valid: set[str], what: str) -> tuple[str, ...]:
  names = tuple(item.strip() for item in text.split(",") if item.strip())
  if not names:
    raise argparse.ArgumentTypeError(f"expected comma-separated {what}")
  bad = sorted(set(names) - valid)
  if bad:
    raise argparse.ArgumentTypeError(f"unknown {what}: {', '.join(bad)}")
  return names


def parse_cases(text: str) -> tuple[str, ...]:
  return parse_csv_choices(text, set(CASE_NAMES), "cases")


def parse_op_pairs(text: str) -> tuple[tuple[int, int], ...]:
  op_map = {name: op for op, name in dram.OP_NAMES.items()}
  pairs = []
  for item in text.split(","):
    item = item.strip()
    if not item:
      continue
    left, sep, right = item.partition("/")
    if not sep or left not in op_map or right not in op_map:
      raise argparse.ArgumentTypeError("op pairs must look like read/read,write/write,read/write")
    pairs.append((op_map[left], op_map[right]))
  if not pairs:
    raise argparse.ArgumentTypeError("expected at least one op pair")
  return tuple(pairs)


def pattern_banks(case: str, bank_count: int) -> list[int]:
  available = list(range(bank_count))
  low = [bank for bank in available if bank < 4]
  high = [bank for bank in available if bank >= 4]
  if case in ("same-dram-bank", "same-route-links"):
    return [0]
  if case == "different-banks-same-dram-column":
    if len(low) < 2:
      raise ValueError("need at least two low-half DRAM banks for same-column case")
    return low
  if case == "banks-0-3":
    return low
  if case == "banks-4-7":
    if not high:
      raise ValueError("no high-half DRAM banks are available on this board")
    return high
  if case == "alternating-halves":
    out = []
    for left, right in zip(low, high):
      out.extend((left, right))
    out.extend(low[len(high):])
    out.extend(high[len(low):])
    return out
  if case == "disjoint-route-links":
    return [low[0], high[0] if high else low[-1]]
  raise ValueError(f"unknown case {case}")


def choose_cores(cores: list[Core], *, case: str, total: int) -> list[Core]:
  core_set = set(cores)
  same_route = [(x, 4) for x in (1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14)]
  disjoint = [(1, 4), (13, 7), (2, 4), (12, 7), (3, 4), (11, 7), (4, 4), (10, 7)]
  preferred = disjoint if case == "disjoint-route-links" else same_route
  selected = [core for core in preferred if core in core_set]
  selected.extend(core for core in cores if core not in set(selected))
  if len(selected) < total:
    raise ValueError(f"need {total} active cores, found {len(selected)}")
  return selected[:total]


def endpoint_for(
  *,
  endpoint_mode: str,
  idx: int,
  bank: int,
  noc: int,
  preferred_coords: dict[int, list[int]],
  bank_coords: dict[int, Core],
) -> tuple[int, int]:
  preferred_endpoint = None
  if endpoint_mode == "preferred":
    base_x, base_y = bank_coords[bank]
    preferred_coord = preferred_coords[noc][bank]
    preferred_endpoint = ((preferred_coord >> 6) & 0x3F) - base_y
    if (preferred_coord & 0x3F) != base_x:
      raise ValueError(f"preferred coord bank {bank} does not match bank base coord")
  endpoint = dram.choose_endpoint(endpoint_mode=endpoint_mode, idx=idx, preferred_endpoint=preferred_endpoint)
  if endpoint_mode == "preferred":
    return endpoint, preferred_coords[noc][bank]
  x, y0 = bank_coords[bank]
  return endpoint, noc_xy(x, y0 + endpoint)


def make_streams(
  *,
  case: str,
  op_pair: tuple[int, int],
  cores: list[Core],
  bank_count: int,
  packet_count: int,
  streams_per_noc: int,
  endpoint_mode: str,
  preferred_coords: dict[int, list[int]],
  bank_coords: dict[int, Core],
) -> tuple[list[DramStream], list[DramStream]]:
  banks = pattern_banks(case, bank_count)
  selected_cores = choose_cores(cores, case=case, total=streams_per_noc * 2)
  groups = []
  stream_index = 0
  for noc, op, core_slice in (
    (0, op_pair[0], selected_cores[:streams_per_noc]),
    (1, op_pair[1], selected_cores[streams_per_noc:]),
  ):
    group = []
    for local_idx, core in enumerate(core_slice):
      bank = banks[(stream_index if case != "same-dram-bank" else 0) % len(banks)]
      endpoint, coord = endpoint_for(
        endpoint_mode=endpoint_mode,
        idx=stream_index,
        bank=bank,
        noc=noc,
        preferred_coords=preferred_coords,
        bank_coords=bank_coords,
      )
      group.append(DramStream(
        name=f"noc{noc}.{local_idx}",
        core=core,
        op=op,
        noc=noc,
        bank=bank,
        start_page=stream_index * packet_count,
        endpoint=endpoint,
        coord=coord,
      ))
      stream_index += 1
    groups.append(group)
  return groups[0], groups[1]


def clear_results_and_gate(device, cores: list[Core]):
  with harness.device_window(device, cores[0]) as win:
    for core in cores:
      win.target(core)
      win.write(dram.RESULT_BASE, b"\0" * dram.result_size())
      win.write(dram.START_GATE_BASE, b"\0" * 8)


def write_start_gate(device, cores: list[Core], threshold: int):
  blob = struct.pack("<II", threshold & 0xFFFFFFFF, (threshold >> 32) & 0xFFFFFFFF)
  with harness.device_window(device, cores[0]) as win:
    for core in cores:
      win.target(core)
      win.write(dram.START_GATE_BASE, blob)


def run_stream_group(
  device,
  streams: list[DramStream],
  *,
  dram_base: int,
  bank_count: int,
  packet_bytes: int,
  packet_count: int,
  stateful: bool,
  dry_run: bool,
  gate_delay_cycles: int,
) -> list[dram.CoreResult]:
  cores = [stream.core for stream in streams]
  if not dry_run:
    clear_results_and_gate(device, cores)
  program = StructuralDramProgram(
    streams,
    dram_base=dram_base,
    bank_count=bank_count,
    packet_bytes=packet_bytes,
    packet_count=packet_count,
    stateful=stateful,
    use_start_gate=gate_delay_cycles > 0,
  )
  if dry_run:
    program.lower(cores)
    return []
  if gate_delay_cycles > 0:
    threshold = probe.read_host_wall_clock(device, cores[0]) + gate_delay_cycles
    write_start_gate(device, cores, threshold)
  device.run(program)
  return [dram.read_result(device, stream.core) for stream in streams]


def group_bpc(results: list[dram.CoreResult], *, packet_bytes: int, packet_count: int) -> tuple[int, float]:
  window = max(result.end for result in results) - min(result.start for result in results)
  total_bytes = len(results) * packet_bytes * packet_count
  return window, total_bytes / window if window > 0 else 0.0


def bad_counters(results: list[dram.CoreResult], packet_count: int) -> int:
  return sum(((result.counter_after - result.counter_before) & 0xFFFFFFFF) != packet_count for result in results)


def stream_summary(streams: list[DramStream]) -> str:
  return ", ".join(
    f"NoC{stream.noc}/{dram.OP_NAMES[stream.op]} `{_fmt_core(stream.core)}`->b{stream.bank}.e{stream.endpoint}"
    for stream in streams
  )


def main():
  parser = argparse.ArgumentParser(description="Simultaneous NoC0+NoC1 DRAM structural bank-set matrix.")
  parser.add_argument("--cases", type=parse_cases, default=parse_cases(",".join(CASE_NAMES)))
  parser.add_argument("--op-pairs", type=parse_op_pairs, default=parse_op_pairs("read/read,write/write,read/write"))
  parser.add_argument("--streams-per-noc", type=int, default=2)
  parser.add_argument("--bytes-per-stream", type=int, default=512 * 1024)
  parser.add_argument("--packet-bytes", type=int, default=Dtype.Float16_b.tile_size)
  parser.add_argument(
    "--endpoint",
    choices=("preferred", "0", "1", "2", "split3"),
    default="preferred",
    help="DRAM endpoint mode: preferred bank table, explicit endpoint 0/1/2, or split3",
  )
  parser.add_argument("--stateful", action="store_true")
  parser.add_argument("--gate-delay-cycles", type=int, default=200_000_000)
  parser.add_argument("--dry-run", action="store_true")
  parser.add_argument("--no-report", action="store_true")
  parser.add_argument("--report", type=Path, default=harness.doc_path("noc", "dram-noc-structural-matrix.md"))
  args = parser.parse_args()

  if args.streams_per_noc <= 0:
    raise ValueError("--streams-per-noc must be positive")
  if args.packet_bytes <= 0 or args.packet_bytes > NOC.MAX_BURST_SIZE:
    raise ValueError(f"--packet-bytes must be in [1, {NOC.MAX_BURST_SIZE}]")
  if args.packet_bytes % Dtype.Float16_b.tile_size:
    raise ValueError(f"--packet-bytes must be a multiple of {Dtype.Float16_b.tile_size}")
  if args.bytes_per_stream <= 0 or args.bytes_per_stream % args.packet_bytes:
    raise ValueError("--bytes-per-stream must be a positive multiple of --packet-bytes")
  if args.gate_delay_cycles < 0:
    raise ValueError("--gate-delay-cycles must be non-negative")
  packet_count = args.bytes_per_stream // args.packet_bytes

  rows = [
    "| case | op pair | NoC0 streams | NoC1 streams | NoC0 alone B/cyc | NoC1 alone B/cyc | mixed NoC0 B/cyc | mixed NoC1 B/cyc | mixed aggregate B/cyc | bad counters |",
    "|---|---|---|---|---:|---:|---:|---:|---:|---:|",
  ]
  device_cm = _null_device() if args.dry_run else harness.open_device()
  with device_cm as device:
    if args.dry_run:
      bank_count = 7
      bank_coords = p100_dram_bank_base_coords(7)
      preferred_coords = {noc: p100_dram_bank_endpoint_coords(7, noc) for noc in (0, 1)}
      cores = probe.usable_cores(None)
      dram_base = 0x10000000
    else:
      bank_count = len(device.dram.bank_tiles)
      bank_coords = p100_dram_bank_base_coords(device.board_info.harvested_dram_bank)
      preferred_coords = {
        noc: p100_dram_bank_endpoint_coords(device.board_info.harvested_dram_bank, noc)
        for noc in (0, 1)
      }
      cores = probe.usable_cores(device)
      max_streams = args.streams_per_noc * 2
      max_pages = max_streams * packet_count
      buf = device.dram.alloc(bank_count * max_pages, Dtype.Float16_b, name="dram_noc_structural_matrix")
      dram_base = buf.addr

    for case in args.cases:
      for op_pair in args.op_pairs:
        group0, group1 = make_streams(
          case=case,
          op_pair=op_pair,
          cores=cores,
          bank_count=bank_count,
          packet_count=packet_count,
          streams_per_noc=args.streams_per_noc,
          endpoint_mode=args.endpoint,
          preferred_coords=preferred_coords,
          bank_coords=bank_coords,
        )
        alone0 = run_stream_group(
          device, group0, dram_base=dram_base, bank_count=bank_count,
          packet_bytes=args.packet_bytes, packet_count=packet_count,
          stateful=args.stateful, dry_run=args.dry_run,
          gate_delay_cycles=args.gate_delay_cycles,
        )
        alone1 = run_stream_group(
          device, group1, dram_base=dram_base, bank_count=bank_count,
          packet_bytes=args.packet_bytes, packet_count=packet_count,
          stateful=args.stateful, dry_run=args.dry_run,
          gate_delay_cycles=args.gate_delay_cycles,
        )
        mixed = run_stream_group(
          device, group0 + group1, dram_base=dram_base, bank_count=bank_count,
          packet_bytes=args.packet_bytes, packet_count=packet_count,
          stateful=args.stateful, dry_run=args.dry_run,
          gate_delay_cycles=args.gate_delay_cycles,
        )
        if args.dry_run:
          alone0_bpc = alone1_bpc = mixed0_bpc = mixed1_bpc = mixed_agg = "dry-run"
          bad = ""
        else:
          _, alone0_v = group_bpc(alone0, packet_bytes=args.packet_bytes, packet_count=packet_count)
          _, alone1_v = group_bpc(alone1, packet_bytes=args.packet_bytes, packet_count=packet_count)
          _, mixed0_v = group_bpc(mixed[:len(group0)], packet_bytes=args.packet_bytes, packet_count=packet_count)
          _, mixed1_v = group_bpc(mixed[len(group0):], packet_bytes=args.packet_bytes, packet_count=packet_count)
          mixed_window = max(result.end for result in mixed) - min(result.start for result in mixed)
          mixed_agg_v = (len(mixed) * args.packet_bytes * packet_count) / mixed_window if mixed_window > 0 else 0.0
          alone0_bpc = f"{alone0_v:.3f}"
          alone1_bpc = f"{alone1_v:.3f}"
          mixed0_bpc = f"{mixed0_v:.3f}"
          mixed1_bpc = f"{mixed1_v:.3f}"
          mixed_agg = f"{mixed_agg_v:.3f}"
          bad = str(bad_counters(mixed, packet_count))
        rows.append(
          f"| {case} | {dram.OP_NAMES[op_pair[0]]}/{dram.OP_NAMES[op_pair[1]]} | "
          f"{stream_summary(group0)} | {stream_summary(group1)} | "
          f"{alone0_bpc} | {alone1_bpc} | {mixed0_bpc} | {mixed1_bpc} | {mixed_agg} | {bad} |"
        )

  table = "\n".join(rows)
  print(table)
  if not args.no_report and not args.dry_run:
    harness.append_report(args.report, "DRAM structural matrix", [
      f"Streams per NoC: `{args.streams_per_noc}`",
      f"Bytes per stream: `{args.bytes_per_stream}`",
      f"Packet size: `{args.packet_bytes}` bytes",
      f"Endpoint mode: `{args.endpoint}`",
      f"Posting mode: `{'stateful' if args.stateful else 'standard'}`",
      f"Start gate lead: `{args.gate_delay_cycles}` cycles",
      "Traffic: NoC0 group alone, NoC1 group alone, then both groups simultaneously",
      "Read/write pairs use disjoint DRAM page ranges within the selected bank pattern.",
    ], table)
    print(f"\nappended {args.report}")


class _null_device:
  def __enter__(self):
    return None

  def __exit__(self, exc_type, exc, tb):
    return False


if __name__ == "__main__":
  main()
