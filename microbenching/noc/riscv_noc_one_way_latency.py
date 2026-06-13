#!/usr/bin/env python3
from __future__ import annotations

import argparse
import statistics
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
import riscv_noc_hop_sweep as hop_sweep  # noqa: E402
from asm import KernelBase
from device import Device
from dsl import a2, a3, s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, t0, t1, t3, t4, zero
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
HEADER_WORDS = 16
HEADER_SIZE = HEADER_WORDS * 4
SENDER_SAMPLE_WORDS = 4
RECEIVER_SAMPLE_WORDS = 2
RESULT_MAGIC = 0x314F574E  # "NWO1"
STATUS_STARTED = 0x1A000001
STATUS_DONE = 0x1A00D00D
ROLE_SENDER = 1
ROLE_RECEIVER = 2

SRC_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
DST_BASE = SRC_BASE
SENTINEL_BASE = 0xA6000001
ENABLED_TENSIX_COL_TAG = 34


class OneWayKernel(KernelBase, Noc):
  pass


@dataclass(frozen=True)
class Route:
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


@dataclass(frozen=True)
class RunResult:
  noc: int
  source: Core
  target: Core
  route: Route
  packet_bytes: int
  iters: int
  sender_counter_delta: int
  receiver_poll_iters: int
  sender_issue: list[int]
  sender_sent: list[int]
  receiver_seen: list[int]

  @property
  def seen_minus_issue(self) -> list[int]:
    return [r - s for s, r in zip(self.sender_issue, self.receiver_seen)]

  @property
  def seen_minus_sent(self) -> list[int]:
    return [r - s for s, r in zip(self.sender_sent, self.receiver_seen)]


def u64(lo: int, hi: int) -> int:
  return lo | (hi << 32)


def parse_pair(text: str) -> tuple[Core, Core]:
  try:
    lhs, rhs = text.split(":", 1)
    return harness.parse_core(lhs), harness.parse_core(rhs)
  except Exception as exc:
    raise argparse.ArgumentTypeError("expected pair as X,Y:X,Y") from exc


def parse_sizes(text: str) -> tuple[int, ...]:
  sizes = tuple(int(item.strip(), 0) for item in text.split(",") if item.strip())
  if not sizes:
    raise argparse.ArgumentTypeError("expected comma-separated packet sizes")
  for size in sizes:
    if size < 4 or size > NOC.MAX_BURST_SIZE or size % 4:
      raise argparse.ArgumentTypeError(f"sizes must be 4-byte multiples in [4, {NOC.MAX_BURST_SIZE}]")
  return sizes


def result_size_sender(iters: int) -> int:
  return HEADER_SIZE + iters * SENDER_SAMPLE_WORDS * 4


def result_size_receiver(iters: int) -> int:
  return HEADER_SIZE + iters * RECEIVER_SAMPLE_WORDS * 4


def emit_header(fw: KernelBase, *, role: int, status: int, noc: int, packet_bytes: int, iters: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, role, status, noc, packet_bytes, iters, SRC_BASE, DST_BASE,
    SENTINEL_BASE, NOC.MAX_BURST_SIZE, 0, 0, 0, 0, 0, 0,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  return fw


def emit_status(fw: KernelBase, status: int):
  fw.li(s2, RESULT_BASE)
  fw.li(t0, status)
  fw.sw(t0, s2, 2 * 4)
  return fw


def emit_counter_read(fw: KernelBase, noc: int, counter: int, out, *, addr=t3):
  fw.li(addr, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  return fw.lw(out, addr, 0)


def emit_wait_counter_at_least(fw: KernelBase, noc: int, counter: int, target, *, addr=t3, val=t4):
  fw.li(addr, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  loop = fw._new_label("wait_counter")
  fw.label(loop)
  fw.lw(val, addr, 0)
  fw.bltu(val, target, loop)
  return fw


def build_sender(noc: int, packet_bytes: int, iters: int, start_delay: int) -> KernelBase:
  fw = OneWayKernel()
  emit_header(fw, role=ROLE_SENDER, status=STATUS_STARTED, noc=noc, packet_bytes=packet_bytes, iters=iters)
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s9,))
  fw.local_noc_coord(noc, s5, x_addr=BM.MY_X, y_addr=BM.MY_Y)
  fw.noc_cmd_reg(noc, 0, NOC.TARG_ADDR_COORDINATE, s5, addr=t3, tmp=t4)
  fw.li(s2, SRC_BASE)
  fw.li(s3, DST_BASE)
  fw.li(s4, packet_bytes)
  fw.li(s11, SRC_BASE + packet_bytes - 4)
  fw.li(s10, RESULT_BASE + HEADER_SIZE)
  fw.li(s8, SENTINEL_BASE)
  emit_counter_read(fw, noc, NOC.NIU_MST_POSTED_WR_REQ_SENT, s7)
  fw.mv(s6, s7)
  if start_delay > 0:
    fw.delay_cycles(start_delay, count=t0)

  fw.li(s0, iters)
  loop = fw._new_label("oneway_send_loop")
  done = fw._new_label("oneway_send_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  fw.sw(s8, s11, 0)
  fw.fence()
  fw.noc_write(noc, 0, s2, s3, 0, s9, s4, posted=True, a=t3, v=t4)
  harness.read_wall_clock(fw, a2, a3)
  fw.sw(a2, s10, 0)
  fw.sw(a3, s10, 4)
  fw.addi(s6, s6, 1)
  emit_wait_counter_at_least(fw, noc, NOC.NIU_MST_POSTED_WR_REQ_SENT, s6, addr=t3, val=t4)
  harness.read_wall_clock(fw, a2, a3)
  fw.sw(a2, s10, 8)
  fw.sw(a3, s10, 12)
  fw.addi(s10, s10, SENDER_SAMPLE_WORDS * 4)
  fw.addi(s8, s8, 1)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  emit_counter_read(fw, noc, NOC.NIU_MST_POSTED_WR_REQ_SENT, t1)
  fw.li(s2, RESULT_BASE)
  fw.sw(s7, s2, 10 * 4)
  fw.sw(t1, s2, 11 * 4)
  emit_status(fw, STATUS_DONE)
  return fw.ret()


def build_receiver(noc: int, packet_bytes: int, iters: int) -> KernelBase:
  fw = OneWayKernel()
  emit_header(fw, role=ROLE_RECEIVER, status=STATUS_STARTED, noc=noc, packet_bytes=packet_bytes, iters=iters)
  fw.li(s1, SENTINEL_BASE)
  fw.li(s2, DST_BASE + packet_bytes - 4)
  fw.li(s10, RESULT_BASE + HEADER_SIZE)
  fw.mv(s8, zero)
  fw.li(s0, iters)
  outer = fw._new_label("oneway_recv_outer")
  poll = fw._new_label("oneway_recv_poll")
  done = fw._new_label("oneway_recv_done")
  fw.label(outer)
  fw.beq(s0, zero, done)
  fw.label(poll)
  fw.lw(t1, s2, 0)
  fw.beq(t1, s1, "oneway_recv_seen")
  fw.addi(s8, s8, 1)
  fw.j(poll)
  fw.label("oneway_recv_seen")
  harness.read_wall_clock(fw, a2, a3)
  fw.sw(a2, s10, 0)
  fw.sw(a3, s10, 4)
  fw.addi(s10, s10, RECEIVER_SAMPLE_WORDS * 4)
  fw.addi(s1, s1, 1)
  fw.addi(s0, s0, -1)
  fw.j(outer)
  fw.label(done)
  fw.li(s2, RESULT_BASE)
  fw.sw(s8, s2, 10 * 4)
  fw.sw(t1, s2, 11 * 4)
  emit_status(fw, STATUS_DONE)
  return fw.ret()


class OneWayProgram:
  def __init__(self, *, noc: int, packet_bytes: int, iters: int, source: Core, target: Core, start_delay: int):
    self.noc = noc
    self.packet_bytes = packet_bytes
    self.iters = iters
    self.source = source
    self.target = target
    self.start_delay = start_delay
    self.name = f"riscv_noc_one_way_latency:noc{noc}:{source}->{target}"

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    empty = KernelBase()
    sender = build_sender(self.noc, self.packet_bytes, self.iters, self.start_delay)
    sender.rta(lambda _x, _y: [noc_xy(*self.target)])
    receiver = build_receiver(self.noc, self.packet_bytes, self.iters)
    sender_prog = Program(
      brisc=sender,
      ncrisc=empty,
      trisc0=empty,
      trisc1=empty,
      trisc2=empty,
      num_cores=1,
    ).layout(core_xy=self.source, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id)
    receiver_prog = Program(
      brisc=receiver,
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
    for segment in sender_prog:
      commands.append(UnicastWrite([self.source], segment.addr, [segment.data]))
    for segment in receiver_prog:
      commands.append(UnicastWrite([self.target], segment.addr, [segment.data]))
    commands.append(Run(target_cores))
    return commands


def read_tensix_coordinate_map(device: Device) -> TensixCoordinateMap:
  layout = device.dev.telemetry_layout()
  enabled = device.dev.telemetry_tag(layout, ENABLED_TENSIX_COL_TAG)
  if enabled is None:
    raise RuntimeError("ENABLED_TENSIX_COL telemetry is unavailable")
  return tensix_coordinate_map(enabled)


def route_for_pair(source: Core, target: Core, *, noc: int, cmap: TensixCoordinateMap) -> Route:
  raw0_source = translated_tensix_to_raw_noc0(source, cmap)
  raw0_target = translated_tensix_to_raw_noc0(target, cmap)
  raw_source = raw_coord_for_noc(raw0_source, noc)
  raw_target = raw_coord_for_noc(raw0_target, noc)
  x_hops = (raw_target[0] - raw_source[0]) % GRID_W
  y_hops = (raw_target[1] - raw_source[1]) % GRID_H
  wraps = int(raw_target[0] < raw_source[0] and x_hops != 0) + int(raw_target[1] < raw_source[1] and y_hops != 0)
  return Route(
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


def clear_and_seed(device: Device, source: Core, target: Core, packet_bytes: int, iters: int):
  payload = bytearray(packet_bytes)
  for off in range(0, packet_bytes, 4):
    struct.pack_into("<I", payload, off, 0xA5000000 | off)
  with harness.device_window(device, source) as win:
    win.target(source)
    win.write(RESULT_BASE, b"\0" * result_size_sender(iters))
    win.write(SRC_BASE, payload)
    win.target(target)
    win.write(RESULT_BASE, b"\0" * result_size_receiver(iters))
    win.write(DST_BASE, b"\0" * packet_bytes)


def read_words(device: Device, core: Core, size: int) -> tuple[int, ...]:
  with harness.device_window(device, core) as win:
    blob = win.read(RESULT_BASE, size)
  if blob and all(b == 0xFF for b in blob):
    raise RuntimeError(f"{core}: L1 readback returned all 0xff")
  return struct.unpack_from("<" + "I" * (size // 4), blob, 0)


def parse_run_result(device: Device, *, noc: int, source: Core, target: Core, route: Route,
                     packet_bytes: int, iters: int) -> RunResult:
  sender = read_words(device, source, result_size_sender(iters))
  receiver = read_words(device, target, result_size_receiver(iters))
  for core, words, role in ((source, sender, ROLE_SENDER), (target, receiver, ROLE_RECEIVER)):
    if words[0] != RESULT_MAGIC:
      raise RuntimeError(f"{core}: bad result magic 0x{words[0]:08x}")
    if words[1] != role:
      raise RuntimeError(f"{core}: bad role {words[1]}")
    if words[2] != STATUS_DONE:
      raise RuntimeError(f"{core}: benchmark did not finish, status=0x{words[2]:08x}")
  sender_issue = []
  sender_sent = []
  receiver_seen = []
  for i in range(iters):
    base = HEADER_WORDS + i * SENDER_SAMPLE_WORDS
    sender_issue.append(u64(sender[base], sender[base + 1]))
    sender_sent.append(u64(sender[base + 2], sender[base + 3]))
    rbase = HEADER_WORDS + i * RECEIVER_SAMPLE_WORDS
    receiver_seen.append(u64(receiver[rbase], receiver[rbase + 1]))
  return RunResult(
    noc=noc,
    source=source,
    target=target,
    route=route,
    packet_bytes=packet_bytes,
    iters=iters,
    sender_counter_delta=(sender[11] - sender[10]) & 0xFFFFFFFF,
    receiver_poll_iters=receiver[10],
    sender_issue=sender_issue,
    sender_sent=sender_sent,
    receiver_seen=receiver_seen,
  )


def summarize_values(values: list[int]) -> str:
  return (
    f"min={min(values)} avg={statistics.fmean(values):.3f} "
    f"med={statistics.median(values):.3f} max={max(values)}"
  )


def format_results(results: list[RunResult]) -> str:
  lines = [
    "| noc | source | target | raw noc route | hops | x | y | wraps | bytes | iters | seen-issue cyc | seen-sent cyc | posted reqs | recv polls |",
    "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---|---|---:|---:|",
  ]
  for r in results:
    route = r.route
    lines.append(
      f"| {r.noc} | `{r.source[0]},{r.source[1]}` | `{r.target[0]},{r.target[1]}` | "
      f"`{route.raw_source[0]},{route.raw_source[1]}->{route.raw_target[0]},{route.raw_target[1]}` | "
      f"{route.hops} | {route.x_hops} | {route.y_hops} | {route.wraps} | "
      f"{r.packet_bytes} | {r.iters} | {summarize_values(r.seen_minus_issue)} | "
      f"{summarize_values(r.seen_minus_sent)} | {r.sender_counter_delta} | {r.receiver_poll_iters} |"
    )
  return "\n".join(lines)


def default_pairs(cores: list[Core]) -> list[tuple[Core, Core]]:
  return [((1, 2), (2, 2)), ((1, 2), (14, 2)), ((1, 2), (1, 3)), ((1, 2), (1, 11)), ((1, 2), (14, 11))]


def main() -> None:
  parser = argparse.ArgumentParser(description="One-way posted L1-to-L1 NoC latency observed by receiver polling.")
  parser.add_argument("--nocs", type=hop_sweep.parse_nocs, default=(0, 1))
  parser.add_argument("--pair", type=parse_pair, default=None, help="translated worker pair X,Y:X,Y")
  parser.add_argument("--sizes", type=parse_sizes, default=parse_sizes("64,1024,16384"))
  parser.add_argument("--iters", type=int, default=64)
  parser.add_argument("--start-delay", type=int, default=4096, help="sender delay before first packet so receiver is polling")
  args = parser.parse_args()
  if args.iters <= 0:
    raise ValueError("--iters must be positive")
  if args.start_delay < 0:
    raise ValueError("--start-delay must be non-negative")

  results: list[RunResult] = []
  with harness.open_device() as device:
    core_set = set(device.cores)
    cmap = read_tensix_coordinate_map(device)
    pairs = [args.pair] if args.pair is not None else default_pairs(device.cores)
    for source, target in pairs:
      if source not in core_set or target not in core_set:
        raise ValueError(f"pair {source}->{target} must use program cores")
      for noc in args.nocs:
        route = route_for_pair(source, target, noc=noc, cmap=cmap)
        for packet_bytes in args.sizes:
          clear_and_seed(device, source, target, packet_bytes, args.iters)
          device.run(OneWayProgram(
            noc=noc,
            packet_bytes=packet_bytes,
            iters=args.iters,
            source=source,
            target=target,
            start_delay=args.start_delay,
          ))
          results.append(parse_run_result(
            device,
            noc=noc,
            source=source,
            target=target,
            route=route,
            packet_bytes=packet_bytes,
            iters=args.iters,
          ))

  print(format_results(results))


if __name__ == "__main__":
  main()
