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
from asm import KernelBase
from device import Device
from dsl import a2, a3, a4, a5, s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, t0, t3, t4, zero
from program import DevMsgs, Program, Run, UnicastWrite
from ttk.addrs import Core, noc_xy
from ttk.blackhole_coords import (
  GRID_H, GRID_W, TensixCoordinateMap, raw_coord_for_noc, tensix_coordinate_map,
  translated_tensix_to_raw_noc0,
)
from ttk.mailbox import BriscMailbox as BM
from ttk.noc import NOC, Noc
from ttk.tensix import TensixL1


RESULT_BASE = 0x150000
RESULT_WORDS = 16
RESULT_SIZE = RESULT_WORDS * 4
RESULT_MAGIC = 0x52504C54  # "RPLT"
STATUS_STARTED = 0x71000001
STATUS_DONE = 0x7100D00D

SRC_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
DST_BASE = SRC_BASE + NOC.MAX_BURST_SIZE
ENABLED_TENSIX_COL_TAG = 34

OP_READ = 1
OP_WRITE = 2
OP_NAMES = {
  OP_READ: "read",
  OP_WRITE: "write",
}


@dataclass(frozen=True)
class Result:
  noc: int
  op: int
  case: str
  source: Core
  target: Core
  raw0_source: Core
  raw0_target: Core
  raw_source: Core
  raw_target: Core
  hops: int
  x_hops: int
  y_hops: int
  wraps: int
  packet_bytes: int
  iters: int
  cycles: int
  counter_delta: int
  sink: int

  @property
  def cycles_per_iter(self) -> float:
    return self.cycles / self.iters if self.iters else 0.0

  @property
  def bytes_per_cycle(self) -> float:
    return self.packet_bytes / self.cycles_per_iter if self.cycles_per_iter > 0 else 0.0


class PacketLatencyKernel(KernelBase, Noc):
  pass


@dataclass(frozen=True)
class Route:
  case: str
  source: Core
  target: Core
  raw0_source: Core
  raw0_target: Core
  raw_source: Core
  raw_target: Core
  hops: int
  x_hops: int
  y_hops: int
  wraps: int


def emit_counter_read(fw: KernelBase, noc: int, counter: int, out, *, addr=t3):
  fw.li(addr, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  return fw.lw(out, addr, 0)


def emit_header(fw: KernelBase, *, noc: int, op: int, packet_bytes: int, iters: int, status: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, status, noc, op, packet_bytes, iters, SRC_BASE, DST_BASE,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off in range(8, RESULT_WORDS):
    fw.sw(zero, s2, off * 4)
  return fw


def build_kernel(*, noc: int, op: int, packet_bytes: int, iters: int) -> KernelBase:
  if op not in OP_NAMES:
    raise ValueError(f"unknown op {op}")
  fw = PacketLatencyKernel()
  emit_header(fw, noc=noc, op=op, packet_bytes=packet_bytes, iters=iters, status=STATUS_STARTED)
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s9,))
  fw.local_noc_coord(noc, s5, x_addr=BM.MY_X, y_addr=BM.MY_Y)
  fw.li(s2, SRC_BASE)
  fw.li(s3, DST_BASE)
  fw.li(s4, packet_bytes)
  if op == OP_WRITE:
    fw.noc_cmd_reg(noc, 0, NOC.TARG_ADDR_COORDINATE, s5, addr=t3, tmp=t4)
  counter = NOC.NIU_MST_RD_RESP_RECEIVED if op == OP_READ else NOC.NIU_MST_WR_ACK_RECEIVED
  emit_counter_read(fw, noc, counter, s7)
  fw.mv(s6, s7)

  harness.read_wall_clock(fw, a2, a3)
  fw.li(s0, iters)
  loop = fw._new_label("packet_latency_loop")
  done = fw._new_label("packet_latency_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  if op == OP_READ:
    fw.noc_read(noc, 1, s2, 0, s9, s3, s4, ret_coord=s5, a=t3, v=t4)
    fw.addi(s6, s6, 1)
    fw.noc_reads_flushed(noc, s6, addr=t3, val=t4)
  else:
    fw.noc_write(noc, 0, s2, s3, 0, s9, s4, posted=False, a=t3, v=t4)
    fw.addi(s6, s6, 1)
    fw.noc_write_barrier(noc, s6, addr=t3, val=t4)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  harness.read_wall_clock(fw, a4, a5)
  emit_counter_read(fw, noc, counter, s8)

  if op == OP_WRITE:
    emit_counter_read(fw, noc, NOC.NIU_MST_RD_RESP_RECEIVED, t0, addr=t3)
    fw.addi(t0, t0, 1)
    fw.noc_read(noc, 1, s3, 0, s9, s3, s4, ret_coord=s5, a=t3, v=t4)
    fw.noc_reads_flushed(noc, t0, addr=t3, val=t4)
  fw.lw(s1, s3, 0)

  fw.li(s2, RESULT_BASE)
  for off, reg in enumerate((a2, a3, a4, a5, s7, s8, s1), start=8):
    fw.sw(reg, s2, off * 4)
  fw.li(t0, STATUS_DONE)
  fw.sw(t0, s2, 1 * 4)
  return fw.ret()


class PairProgram:
  def __init__(self, *, noc: int, op: int, packet_bytes: int, iters: int, source: Core, target: Core):
    self.noc = noc
    self.op = op
    self.packet_bytes = packet_bytes
    self.iters = iters
    self.source = source
    self.target = target
    self.name = f"riscv_noc_packet_latency:{OP_NAMES[op]}:noc{noc}:{source}->{target}"

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    empty = KernelBase()
    bench = build_kernel(noc=self.noc, op=self.op, packet_bytes=self.packet_bytes, iters=self.iters)
    bench.rta(lambda _x, _y: [noc_xy(*self.target)])
    sender = Program(
      brisc=bench,
      ncrisc=empty,
      trisc0=empty,
      trisc1=empty,
      trisc2=empty,
      num_cores=1,
    ).layout(core_xy=self.source, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id)
    receiver = Program(
      brisc=KernelBase().ret(),
      ncrisc=empty,
      trisc0=empty,
      trisc1=empty,
      trisc2=empty,
      num_cores=1,
    ).layout(core_xy=self.target, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id)
    target_cores = [self.source, self.target]
    reset_blob = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_RESET_READ_PTR_FROM_HOST)
    commands = [
      UnicastWrite(target_cores, TensixL1.GO_MSG, [reset_blob] * len(target_cores)),
      UnicastWrite(target_cores, TensixL1.GO_MSG_INDEX, [b"\0\0\0\0"] * len(target_cores)),
    ]
    for segment in sender:
      commands.append(UnicastWrite([self.source], segment.addr, [segment.data]))
    if self.target != self.source:
      for segment in receiver:
        commands.append(UnicastWrite([self.target], segment.addr, [segment.data]))
    commands.append(Run(target_cores))
    return commands


def build_program(*, noc: int, op: int, packet_bytes: int, iters: int, source: Core, target: Core) -> PairProgram:
  return PairProgram(noc=noc, op=op, packet_bytes=packet_bytes, iters=iters, source=source, target=target)


def parse_sizes(text: str) -> tuple[int, ...]:
  sizes = tuple(int(item.strip(), 0) for item in text.split(",") if item.strip())
  if not sizes:
    raise argparse.ArgumentTypeError("expected comma-separated packet sizes")
  for size in sizes:
    if size <= 0 or size > NOC.MAX_BURST_SIZE or size % 4:
      raise argparse.ArgumentTypeError(f"sizes must be 4-byte multiples in [4, {NOC.MAX_BURST_SIZE}]")
  return sizes


def parse_ops(text: str) -> tuple[int, ...]:
  by_name = {name: op for op, name in OP_NAMES.items()}
  ops = tuple(by_name[item.strip()] for item in text.split(",") if item.strip())
  if not ops:
    raise argparse.ArgumentTypeError("expected comma-separated ops from read,write")
  return ops


def parse_pair(text: str) -> tuple[Core, Core]:
  try:
    lhs, rhs = text.split(":", 1)
    return harness.parse_core(lhs), harness.parse_core(rhs)
  except Exception as exc:
    raise argparse.ArgumentTypeError("expected pair as X,Y:X,Y") from exc


def compact_worker_map(cores: list[Core]) -> tuple[dict[Core, Core], dict[Core, Core]]:
  xs = sorted({x for x, _ in cores})
  ys = sorted({y for _, y in cores})
  compact_to_physical = {
    (cx, cy): (x, y)
    for cx, x in enumerate(xs)
    for cy, y in enumerate(ys)
    if (x, y) in set(cores)
  }
  physical_to_compact = {physical: compact for compact, physical in compact_to_physical.items()}
  return compact_to_physical, physical_to_compact


def route_for_pair(source: Core, target: Core, *, noc: int, cmap: TensixCoordinateMap, case: str) -> Route:
  raw0_source = translated_tensix_to_raw_noc0(source, cmap)
  raw0_target = translated_tensix_to_raw_noc0(target, cmap)
  raw_source = raw_coord_for_noc(raw0_source, noc)
  raw_target = raw_coord_for_noc(raw0_target, noc)
  x_hops = (raw_target[0] - raw_source[0]) % GRID_W
  y_hops = (raw_target[1] - raw_source[1]) % GRID_H
  wraps = int(raw_target[0] < raw_source[0] and x_hops != 0) + int(raw_target[1] < raw_source[1] and y_hops != 0)
  return Route(
    case=case,
    source=source,
    target=target,
    raw0_source=raw0_source,
    raw0_target=raw0_target,
    raw_source=raw_source,
    raw_target=raw_target,
    hops=x_hops + y_hops,
    x_hops=x_hops,
    y_hops=y_hops,
    wraps=wraps,
  )


def read_tensix_coordinate_map(device: Device) -> TensixCoordinateMap:
  layout = device.dev.telemetry_layout()
  enabled = device.dev.telemetry_tag(layout, ENABLED_TENSIX_COL_TAG)
  if enabled is None:
    raise RuntimeError("ENABLED_TENSIX_COL telemetry is unavailable")
  return tensix_coordinate_map(enabled)


def select_source(cores: list[Core], requested: Core | None, row: int | None) -> Core:
  core_set = set(cores)
  if requested is not None:
    if requested not in core_set:
      raise ValueError(f"--core {requested[0]},{requested[1]} is not a program core")
    return requested
  rows: dict[int, list[int]] = {}
  for x, y in cores:
    if row is None or y == row:
      rows.setdefault(y, []).append(x)
  candidates = [(len(xs), -y, y, sorted(xs)) for y, xs in rows.items()]
  if not candidates:
    raise ValueError(f"no program cores found on row {row}")
  _, _, y, xs = max(candidates)
  return (xs[0], y)


def default_routes(cores: list[Core], *, noc: int, cmap: TensixCoordinateMap, row: int | None,
                   source: Core | None, max_hops: int | None) -> list[Route]:
  src = select_source(cores, source, row)
  candidates = [
    route_for_pair(src, dst, noc=noc, cmap=cmap, case="candidate")
    for dst in cores
    if dst != src
  ]
  if max_hops is not None:
    candidates = [route for route in candidates if route.hops <= max_hops]
  if not candidates:
    raise ValueError(f"NoC{noc} sweep from {src} has no candidate targets")

  same_row = [route for route in candidates if route.target[1] == src[1]]
  same_col = [route for route in candidates if route.target[0] == src[0]]
  two_d = [route for route in candidates if route.target[0] != src[0] and route.target[1] != src[1]]

  picks: list[Route] = []
  for name, group, chooser in (
    ("x-near", same_row, min),
    ("x-far", same_row, max),
    ("y-near", same_col, min),
    ("y-far", same_col, max),
    ("2d-far", two_d, max),
  ):
    if not group:
      continue
    chosen = chooser(group, key=lambda route: (route.hops, route.x_hops, route.y_hops, route.target))
    picks.append(route_for_pair(src, chosen.target, noc=noc, cmap=cmap, case=name))

  seen: set[tuple[Core, Core, str]] = set()
  unique: list[Route] = []
  for route in picks:
    key = (route.source, route.target, route.case)
    if key not in seen:
      seen.add(key)
      unique.append(route)
  return unique


def routes_from_args(args, cores: list[Core], noc: int, cmap: TensixCoordinateMap) -> list[Route]:
  if args.compact_pair is not None:
    compact_to_physical, _ = compact_worker_map(cores)
    src_c, dst_c = args.compact_pair
    if src_c not in compact_to_physical or dst_c not in compact_to_physical:
      raise ValueError(f"compact pair {src_c}->{dst_c} does not map to available worker cores")
    return [route_for_pair(compact_to_physical[src_c], compact_to_physical[dst_c], noc=noc, cmap=cmap, case="compact-pair")]

  if args.pair is not None:
    src, dst = args.pair
    if src not in set(cores) or dst not in set(cores):
      raise ValueError(f"translated pair {src}->{dst} must use available worker cores")
    return [route_for_pair(src, dst, noc=noc, cmap=cmap, case="pair")]

  return default_routes(cores, noc=noc, cmap=cmap, row=args.row, source=args.core, max_hops=args.max_hops)


def seed(device: Device, source: Core, target: Core):
  payload = bytearray(NOC.MAX_BURST_SIZE)
  for off in range(0, len(payload), 4):
    struct.pack_into("<I", payload, off, 0xA5000000 | off)
  with harness.device_window(device, source) as win:
    for core in (source, target):
      win.target(core)
      win.write(RESULT_BASE, b"\0" * RESULT_SIZE)
      win.write(SRC_BASE, payload)
      win.write(DST_BASE, b"\0" * NOC.MAX_BURST_SIZE)


def read_result(
  device: Device,
  source: Core,
  *,
  noc: int,
  op: int,
  target: Core,
  route: Route,
  packet_bytes: int,
) -> Result:
  with harness.device_window(device, source) as win:
    blob = win.read(RESULT_BASE, RESULT_SIZE)
  words = struct.unpack_from("<" + "I" * RESULT_WORDS, blob, 0)
  if words[0] != RESULT_MAGIC:
    raise RuntimeError(f"{source}: bad result magic 0x{words[0]:08x}")
  if words[1] != STATUS_DONE:
    raise RuntimeError(f"{source}: benchmark did not finish, status=0x{words[1]:08x}")
  if words[2] != noc or words[3] != op or words[4] != packet_bytes:
    raise RuntimeError(f"{source}: result header mismatch {words[:5]}")
  start = words[8] | (words[9] << 32)
  end = words[10] | (words[11] << 32)
  before, after = words[12], words[13]
  return Result(
    noc=noc,
    op=op,
    case=route.case,
    source=source,
    target=target,
    raw0_source=route.raw0_source,
    raw0_target=route.raw0_target,
    raw_source=route.raw_source,
    raw_target=route.raw_target,
    hops=route.hops,
    x_hops=route.x_hops,
    y_hops=route.y_hops,
    wraps=route.wraps,
    packet_bytes=packet_bytes,
    iters=words[5],
    cycles=(end - start) & ((1 << 64) - 1),
    counter_delta=(after - before) & 0xFFFFFFFF,
    sink=words[14],
  )


def fit_line(points: list[tuple[float, float]]) -> tuple[float, float]:
  n = len(points)
  if n < 2:
    return 0.0, points[0][1] if points else 0.0
  sx = sum(x for x, _ in points)
  sy = sum(y for _, y in points)
  sxx = sum(x * x for x, _ in points)
  sxy = sum(x * y for x, y in points)
  denom = n * sxx - sx * sx
  if denom == 0:
    return 0.0, sy / n
  slope = (n * sxy - sx * sy) / denom
  intercept = (sy - slope * sx) / n
  return slope, intercept


def format_results(results: list[Result]) -> str:
  lines = [
    "| case | noc | op | translated src | translated dst | raw noc0 route | raw noc route | hops | x | y | wraps | bytes | iters | cyc/iter | B/cyc | counter | sink |",
    "|---|---:|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
  ]
  for r in results:
    lines.append(
      f"| {r.case} | {r.noc} | {OP_NAMES[r.op]} | `{r.source[0]},{r.source[1]}` | `{r.target[0]},{r.target[1]}` | "
      f"`{r.raw0_source[0]},{r.raw0_source[1]}->{r.raw0_target[0]},{r.raw0_target[1]}` | "
      f"`{r.raw_source[0]},{r.raw_source[1]}->{r.raw_target[0]},{r.raw_target[1]}` | "
      f"{r.hops} | {r.x_hops} | {r.y_hops} | {r.wraps} | {r.packet_bytes} | {r.iters} | {r.cycles_per_iter:.3f} | "
      f"{r.bytes_per_cycle:.3f} | {r.counter_delta} | 0x{r.sink:08x} |"
    )
  lines.append("")
  lines.append("| noc | op | bytes | slope cyc/hop | intercept cyc |")
  lines.append("|---:|---|---:|---:|---:|")
  grouped: dict[tuple[int, int, int], list[tuple[float, float]]] = {}
  for r in results:
    grouped.setdefault((r.noc, r.op, r.packet_bytes), []).append((r.hops, r.cycles_per_iter))
  for (noc, op, packet_bytes), points in sorted(grouped.items()):
    slope, intercept = fit_line(points)
    lines.append(f"| {noc} | {OP_NAMES[op]} | {packet_bytes} | {slope:.3f} | {intercept:.3f} |")
  return "\n".join(lines)


def format_coordinate_map(cmap: TensixCoordinateMap) -> str:
  live = ", ".join(f"{tx}->{cmap.translated_to_raw_x[tx]}" for tx in cmap.translated_live_x)
  hidden = ", ".join(f"{tx}->{raw}" for tx, raw in sorted(cmap.translated_harvested_to_raw_x.items()))
  lines = [
    f"ENABLED_TENSIX_COL: `0x{cmap.enabled_tensix_col:08x}`",
    f"Live raw Tensix columns: `{list(cmap.live_raw_x)}`",
    f"Harvested raw Tensix columns: `{list(cmap.harvested_raw_x)}`",
    f"Translated live x -> raw NoC0 x: `{live}`",
  ]
  if hidden:
    lines.append(f"Translated hidden x -> harvested raw NoC0 x: `{hidden}`")
  return "\n".join(lines)


def append_report(path: Path, *, args, cmap: TensixCoordinateMap, results: list[Result]):
  harness.append_report(path, "NoC packet latency", [
    f"NoCs: `{','.join(str(noc) for noc in args.nocs)}`",
    f"Ops: `{','.join(OP_NAMES[op] for op in args.ops)}`",
    f"Sizes: `{','.join(str(size) for size in args.sizes)}` bytes",
    f"Iters: `{args.iters}`",
    "Traffic: one source issues one blocking packet per iteration and waits for read response or write ack each iteration.",
    "Purpose: small-packet read/write intercept, hop slope, and one-way unicast latency calibration.",
    format_coordinate_map(cmap),
  ], format_results(results))


def main() -> None:
  parser = argparse.ArgumentParser(description="Harvest-aware safe L1 unicast NoC packet latency/hop sweep.")
  parser.add_argument("--nocs", type=hop_sweep.parse_nocs, default=(0, 1))
  parser.add_argument("--ops", type=parse_ops, default=parse_ops("read,write"))
  parser.add_argument("--sizes", type=parse_sizes, default=parse_sizes("4,16,64,256,4096,16384"))
  parser.add_argument("--row", type=int, default=None, help="translated worker row for automatic source selection")
  parser.add_argument("--core", type=harness.parse_core, default=None, help="translated source worker X,Y")
  parser.add_argument("--pair", type=parse_pair, default=None, help="explicit translated worker pair X,Y:X,Y")
  parser.add_argument("--compact-pair", type=parse_pair, default=None, help="compact worker pair X,Y:X,Y, mapped through available translated workers")
  parser.add_argument("--max-hops", type=int, default=None, help="maximum raw selected-NoC hops for automatic cases")
  parser.add_argument("--iters", type=int, default=128)
  parser.add_argument("--no-report", action="store_true", help="do not append docs/noc-packet-latency.md")
  parser.add_argument("--report", type=Path, default=harness.doc_path("noc", "noc-packet-latency.md"))
  args = parser.parse_args()
  if args.iters <= 0:
    raise ValueError("--iters must be positive")
  if args.max_hops is not None and args.max_hops <= 0:
    raise ValueError("--max-hops must be positive")
  if args.pair is not None and args.compact_pair is not None:
    raise ValueError("--pair and --compact-pair are mutually exclusive")

  results: list[Result] = []
  with harness.open_device() as device:
    cmap = read_tensix_coordinate_map(device)
    for noc in args.nocs:
      for route in routes_from_args(args, device.cores, noc, cmap):
        for op in args.ops:
          for packet_bytes in args.sizes:
            seed(device, route.source, route.target)
            device.run(build_program(
              noc=noc,
              op=op,
              packet_bytes=packet_bytes,
              iters=args.iters,
              source=route.source,
              target=route.target,
            ))
            results.append(read_result(
              device,
              route.source,
              noc=noc,
              op=op,
              target=route.target,
              route=route,
              packet_bytes=packet_bytes,
            ))

  print(format_coordinate_map(cmap))
  print()
  table = format_results(results)
  print(table)
  if not args.no_report:
    append_report(args.report, args=args, cmap=cmap, results=results)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
