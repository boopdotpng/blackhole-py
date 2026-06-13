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
from dsl import a2, a3, s0, s1, s2, s4, s5, s6, s7, s8, s9, s10, s11, t0, t1, t3, t4, zero
from program import DevMsgs, Program, Run, UnicastWrite
from ttk.addrs import Core, noc_xy
from ttk.blackhole_coords import (
  GRID_H,
  GRID_W,
  TensixCoordinateMap,
  raw_coord_for_noc,
  tensix_coordinate_map,
  translated_tensix_to_raw_noc0,
)
from ttk.mailbox import BriscMailbox as BM
from ttk.noc import NOC, Noc
from ttk.tensix import TensixL1


RESULT_BASE = 0x170000
HEADER_WORDS = 16
HEADER_SIZE = HEADER_WORDS * 4
SENDER_SAMPLE_WORDS = 4
RECEIVER_SAMPLE_WORDS = 2
RESULT_MAGIC = 0x3143534D  # "MSC1"
STATUS_STARTED = 0x1C000001
STATUS_DONE = 0x1C00D00D
ROLE_SENDER = 1
ROLE_RECEIVER = 2

SRC_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
DST_BASE = SRC_BASE
SENTINEL_BASE = 0xB6000001
ENABLED_TENSIX_COL_TAG = 34

NOC_CMD_BRCST_XY = 1 << 16


class McastOneWayKernel(KernelBase, Noc):
  pass


@dataclass(frozen=True)
class ReceiverRoute:
  receiver: Core
  raw_source: Core
  raw_receiver: Core
  hops: int
  x_hops: int
  y_hops: int
  wraps: int


@dataclass(frozen=True)
class McastRect:
  x0: int
  y0: int
  x1: int
  y1: int


@dataclass(frozen=True)
class RunResult:
  noc: int
  case: str
  major: str
  source: Core
  rect: McastRect
  packet_bytes: int
  iters: int
  route: ReceiverRoute
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


def parse_core_list(text: str) -> tuple[Core, ...]:
  try:
    return tuple(harness.parse_core(item.strip()) for item in text.split(";") if item.strip())
  except Exception as exc:
    raise argparse.ArgumentTypeError("expected semicolon-separated cores as X,Y;X,Y") from exc


def parse_sizes(text: str) -> tuple[int, ...]:
  sizes = tuple(int(item.strip(), 0) for item in text.split(",") if item.strip())
  if not sizes:
    raise argparse.ArgumentTypeError("expected comma-separated packet sizes")
  for size in sizes:
    if size < 4 or size > NOC.MAX_BURST_SIZE or size % 4:
      raise argparse.ArgumentTypeError(f"sizes must be 4-byte multiples in [4, {NOC.MAX_BURST_SIZE}]")
  return sizes


def parse_cases(text: str) -> tuple[str, ...]:
  cases = tuple(item.strip() for item in text.split(",") if item.strip())
  bad = [case for case in cases if case not in {"row", "column", "rect"}]
  if bad:
    raise argparse.ArgumentTypeError(f"unknown case(s): {','.join(bad)}")
  return cases


def parse_majors(text: str) -> tuple[str, ...]:
  majors = tuple(item.strip().lower() for item in text.split(",") if item.strip())
  bad = [major for major in majors if major not in {"x", "y"}]
  if bad:
    raise argparse.ArgumentTypeError(f"unknown major axis: {','.join(bad)}")
  return majors


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


def emit_mcast_write(fw: McastOneWayKernel, noc: int, src, dst_lo, dst_coord, length, *,
                     major: str, path_reserve: bool, a=t3, v=t4):
  ctrl = (
    NOC.CMD_CPY | NOC.CMD_WR | NOC.CMD_RESP_MARKED | NOC.CMD_VC_STATIC |
    NOC.CMD_STATIC_VC_5 | NOC.CMD_BRCST_PACKET
  )
  if path_reserve:
    ctrl |= NOC.CMD_PATH_RESERVE
  if major == "y":
    ctrl |= NOC_CMD_BRCST_XY
  fw.noc_wait_cmd_ready(noc, 0, addr=a, val=v)
  fw.noc_cmd_reg(noc, 0, NOC.CTRL, ctrl, addr=a, tmp=v)
  fw.noc_cmd_reg(noc, 0, NOC.TARG_ADDR_LO, src, addr=a, tmp=v)
  fw.noc_cmd_reg(noc, 0, NOC.RET_ADDR_LO, dst_lo, addr=a, tmp=v)
  fw.noc_cmd_reg(noc, 0, NOC.RET_ADDR_MID, 0, addr=a, tmp=v)
  fw.noc_cmd_reg(noc, 0, NOC.RET_ADDR_COORDINATE, dst_coord, addr=a, tmp=v)
  fw.noc_cmd_reg(noc, 0, NOC.AT_LEN_BE, length, addr=a, tmp=v)
  fw.noc_cmd_reg(noc, 0, NOC.AT_LEN_BE_1, 0, addr=a, tmp=v)
  fw.noc_cmd_reg(noc, 0, NOC.CMD_CTRL, NOC.CTRL_SEND_REQ, addr=a, tmp=v)
  return fw


def build_sender(noc: int, packet_bytes: int, iters: int, start_delay: int, inter_delay: int,
                 rect: McastRect, major: str, path_reserve: bool) -> KernelBase:
  fw = McastOneWayKernel()
  emit_header(fw, role=ROLE_SENDER, status=STATUS_STARTED, noc=noc, packet_bytes=packet_bytes, iters=iters)
  fw.local_noc_coord(noc, s5, x_addr=BM.MY_X, y_addr=BM.MY_Y)
  fw.noc_cmd_reg(noc, 0, NOC.TARG_ADDR_COORDINATE, s5, addr=t3, tmp=t4)
  fw.noc_mcast_coord(s9, rect.x0, rect.y0, rect.x1, rect.y1)
  fw.li(s2, SRC_BASE)
  fw.li(s4, packet_bytes)
  fw.li(s11, SRC_BASE + packet_bytes - 4)
  fw.li(s10, RESULT_BASE + HEADER_SIZE)
  fw.li(s8, SENTINEL_BASE)
  emit_counter_read(fw, noc, NOC.NIU_MST_NONPOSTED_WR_REQ_SENT, s7)
  fw.mv(s6, s7)
  if start_delay > 0:
    fw.delay_cycles(start_delay, count=t0)

  fw.li(s0, iters)
  loop = fw._new_label("mcast_send_loop")
  done = fw._new_label("mcast_send_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  fw.sw(s8, s11, 0)
  fw.fence()
  emit_mcast_write(fw, noc, s2, s2, s9, s4, major=major, path_reserve=path_reserve, a=t3, v=t4)
  harness.read_wall_clock(fw, a2, a3)
  fw.sw(a2, s10, 0)
  fw.sw(a3, s10, 4)
  fw.addi(s6, s6, 1)
  emit_wait_counter_at_least(fw, noc, NOC.NIU_MST_NONPOSTED_WR_REQ_SENT, s6, addr=t3, val=t4)
  harness.read_wall_clock(fw, a2, a3)
  fw.sw(a2, s10, 8)
  fw.sw(a3, s10, 12)
  if inter_delay > 0:
    fw.delay_cycles(inter_delay, count=t0)
  fw.addi(s10, s10, SENDER_SAMPLE_WORDS * 4)
  fw.addi(s8, s8, 1)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  emit_counter_read(fw, noc, NOC.NIU_MST_NONPOSTED_WR_REQ_SENT, t1)
  fw.li(s2, RESULT_BASE)
  fw.sw(s7, s2, 10 * 4)
  fw.sw(t1, s2, 11 * 4)
  emit_status(fw, STATUS_DONE)
  return fw.ret()


def build_receiver(noc: int, packet_bytes: int, iters: int) -> KernelBase:
  fw = McastOneWayKernel()
  emit_header(fw, role=ROLE_RECEIVER, status=STATUS_STARTED, noc=noc, packet_bytes=packet_bytes, iters=iters)
  fw.li(s1, SENTINEL_BASE)
  fw.li(s2, DST_BASE + packet_bytes - 4)
  fw.li(s10, RESULT_BASE + HEADER_SIZE)
  fw.mv(s8, zero)
  fw.li(s0, iters)
  outer = fw._new_label("mcast_recv_outer")
  poll = fw._new_label("mcast_recv_poll")
  seen = fw._new_label("mcast_recv_seen")
  done = fw._new_label("mcast_recv_done")
  fw.label(outer)
  fw.beq(s0, zero, done)
  fw.label(poll)
  fw.lw(t1, s2, 0)
  fw.beq(t1, s1, seen)
  fw.addi(s8, s8, 1)
  fw.j(poll)
  fw.label(seen)
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


class McastOneWayProgram:
  def __init__(self, *, noc: int, packet_bytes: int, iters: int, source: Core,
               receivers: tuple[Core, ...], rect: McastRect, major: str,
               path_reserve: bool, start_delay: int, inter_delay: int):
    self.noc = noc
    self.packet_bytes = packet_bytes
    self.iters = iters
    self.source = source
    self.receivers = receivers
    self.rect = rect
    self.major = major
    self.path_reserve = path_reserve
    self.start_delay = start_delay
    self.inter_delay = inter_delay
    self.name = f"riscv_noc_mcast_one_way_latency:noc{noc}:{source}:dests{len(receivers)}"

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    empty = KernelBase()
    sender = build_sender(
      self.noc, self.packet_bytes, self.iters, self.start_delay, self.inter_delay,
      self.rect, self.major, self.path_reserve,
    )
    receiver = build_receiver(self.noc, self.packet_bytes, self.iters)
    compiled_cache: dict[int, list] = {}
    sender_prog = Program(
      brisc=sender,
      ncrisc=empty,
      trisc0=empty,
      trisc1=empty,
      trisc2=empty,
      num_cores=1,
    ).layout(core_xy=self.source, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id, compiled_cache=compiled_cache)
    receiver_prog = Program(
      brisc=receiver,
      ncrisc=empty,
      trisc0=empty,
      trisc1=empty,
      trisc2=empty,
      num_cores=1,
    )
    per_receiver = {
      core: receiver_prog.layout(
        core_xy=core,
        dispatch_mode=dispatch_mode,
        host_assigned_id=host_assigned_id,
        compiled_cache=compiled_cache,
      )
      for core in self.receivers
    }
    active = [self.source, *self.receivers]
    reset_blob = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_RESET_READ_PTR_FROM_HOST)
    commands = [
      UnicastWrite(active, TensixL1.GO_MSG, [reset_blob] * len(active)),
      UnicastWrite(active, TensixL1.GO_MSG_INDEX, [b"\0\0\0\0"] * len(active)),
    ]
    for segment in sender_prog:
      commands.append(UnicastWrite([self.source], segment.addr, [segment.data]))
    for core, segments in per_receiver.items():
      for segment in segments:
        commands.append(UnicastWrite([core], segment.addr, [segment.data]))
    commands.append(Run(active))
    return commands


def read_tensix_coordinate_map(device: Device) -> TensixCoordinateMap:
  layout = device.dev.telemetry_layout()
  enabled = device.dev.telemetry_tag(layout, ENABLED_TENSIX_COL_TAG)
  if enabled is None:
    raise RuntimeError("ENABLED_TENSIX_COL telemetry is unavailable")
  return tensix_coordinate_map(enabled)


def receiver_route(source: Core, receiver: Core, *, noc: int, cmap: TensixCoordinateMap) -> ReceiverRoute:
  raw0_source = translated_tensix_to_raw_noc0(source, cmap)
  raw0_receiver = translated_tensix_to_raw_noc0(receiver, cmap)
  raw_source = raw_coord_for_noc(raw0_source, noc)
  raw_receiver = raw_coord_for_noc(raw0_receiver, noc)
  x_hops = (raw_receiver[0] - raw_source[0]) % GRID_W
  y_hops = (raw_receiver[1] - raw_source[1]) % GRID_H
  wraps = int(raw_receiver[0] < raw_source[0] and x_hops != 0) + int(raw_receiver[1] < raw_source[1] and y_hops != 0)
  return ReceiverRoute(receiver, raw_source, raw_receiver, x_hops + y_hops, x_hops, y_hops, wraps)


def default_case(case: str) -> tuple[Core, tuple[Core, ...]]:
  if case == "row":
    return (1, 2), ((2, 2), (5, 2), (14, 2))
  if case == "column":
    return (1, 2), ((1, 3), (1, 7), (1, 11))
  return (1, 2), ((2, 3), (14, 3), (2, 11), (14, 11))


def rect_for(receivers: tuple[Core, ...]) -> McastRect:
  xs = [x for x, _y in receivers]
  ys = [y for _x, y in receivers]
  return McastRect(min(xs), min(ys), max(xs), max(ys))


def physical_rect_for_noc(receivers: tuple[Core, ...], *, noc: int, cmap: TensixCoordinateMap) -> McastRect:
  raw = [
    raw_coord_for_noc(translated_tensix_to_raw_noc0(receiver, cmap), noc)
    for receiver in receivers
  ]
  xs = [x for x, _y in raw]
  ys = [y for _x, y in raw]
  return McastRect(min(xs), min(ys), max(xs), max(ys))


def logical_rect_for_physical_span(receivers: tuple[Core, ...], *, noc: int, cmap: TensixCoordinateMap) -> McastRect:
  physical = physical_rect_for_noc(receivers, noc=noc, cmap=cmap)

  def raw_x_to_logical(raw_x: int) -> int:
    raw0_x = raw_x if noc == 0 else GRID_W - 1 - raw_x
    if raw0_x not in cmap.raw_to_translated_x:
      raise ValueError(f"raw NoC0 x {raw0_x} is not a live translated Tensix column")
    return cmap.raw_to_translated_x[raw0_x]

  def raw_y_to_logical(raw_y: int) -> int:
    return raw_y if noc == 0 else GRID_H - 1 - raw_y

  return McastRect(
    raw_x_to_logical(physical.x0),
    raw_y_to_logical(physical.y0),
    raw_x_to_logical(physical.x1),
    raw_y_to_logical(physical.y1),
  )


def clear_and_seed(device: Device, source: Core, receivers: tuple[Core, ...], packet_bytes: int, iters: int):
  payload = bytearray(packet_bytes)
  for off in range(0, packet_bytes, 4):
    struct.pack_into("<I", payload, off, 0xB5000000 | off)
  with harness.device_window(device, source) as win:
    win.target(source)
    win.write(RESULT_BASE, b"\0" * result_size_sender(iters))
    win.write(SRC_BASE, payload)
    for receiver in receivers:
      win.target(receiver)
      win.write(RESULT_BASE, b"\0" * result_size_receiver(iters))
      win.write(DST_BASE, b"\0" * packet_bytes)


def read_words(device: Device, core: Core, size: int) -> tuple[int, ...]:
  with harness.device_window(device, core) as win:
    blob = win.read(RESULT_BASE, size)
  if blob and all(b == 0xFF for b in blob):
    raise RuntimeError(f"{core}: L1 readback returned all 0xff")
  return struct.unpack_from("<" + "I" * (size // 4), blob, 0)


def parse_results(device: Device, *, noc: int, case: str, major: str, source: Core,
                  receivers: tuple[Core, ...], rect: McastRect, routes: dict[Core, ReceiverRoute],
                  packet_bytes: int, iters: int) -> list[RunResult]:
  sender = read_words(device, source, result_size_sender(iters))
  if sender[0] != RESULT_MAGIC or sender[1] != ROLE_SENDER or sender[2] != STATUS_DONE:
    raise RuntimeError(f"{source}: bad sender status magic=0x{sender[0]:08x} role={sender[1]} status=0x{sender[2]:08x}")
  sender_issue = []
  sender_sent = []
  for i in range(iters):
    base = HEADER_WORDS + i * SENDER_SAMPLE_WORDS
    sender_issue.append(u64(sender[base], sender[base + 1]))
    sender_sent.append(u64(sender[base + 2], sender[base + 3]))

  out = []
  for receiver in receivers:
    words = read_words(device, receiver, result_size_receiver(iters))
    if words[0] != RESULT_MAGIC or words[1] != ROLE_RECEIVER or words[2] != STATUS_DONE:
      raise RuntimeError(f"{receiver}: bad receiver status magic=0x{words[0]:08x} role={words[1]} status=0x{words[2]:08x}")
    receiver_seen = []
    for i in range(iters):
      base = HEADER_WORDS + i * RECEIVER_SAMPLE_WORDS
      receiver_seen.append(u64(words[base], words[base + 1]))
    out.append(RunResult(
      noc=noc,
      case=case,
      major=major,
      source=source,
      rect=rect,
      packet_bytes=packet_bytes,
      iters=iters,
      route=routes[receiver],
      sender_counter_delta=(sender[11] - sender[10]) & 0xFFFFFFFF,
      receiver_poll_iters=words[10],
      sender_issue=sender_issue,
      sender_sent=sender_sent,
      receiver_seen=receiver_seen,
    ))
  return out


def summarize(values: list[int]) -> str:
  return (
    f"min={min(values)} avg={statistics.fmean(values):.3f} "
    f"med={statistics.median(values):.3f} max={max(values)}"
  )


def format_results(results: list[RunResult]) -> str:
  lines = [
    "| case | noc | major | source | receiver | rect | raw route | hops | x | y | wraps | bytes | iters | seen-issue cyc | seen-sent cyc | sent reqs | recv polls |",
    "|---|---:|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|---:|---:|",
  ]
  for r in results:
    route = r.route
    lines.append(
      f"| {r.case} | {r.noc} | {r.major} | `{r.source[0]},{r.source[1]}` | "
      f"`{route.receiver[0]},{route.receiver[1]}` | `{r.rect.x0},{r.rect.y0}->{r.rect.x1},{r.rect.y1}` | "
      f"`{route.raw_source[0]},{route.raw_source[1]}->{route.raw_receiver[0]},{route.raw_receiver[1]}` | "
      f"{route.hops} | {route.x_hops} | {route.y_hops} | {route.wraps} | "
      f"{r.packet_bytes} | {r.iters} | {summarize(r.seen_minus_issue)} | "
      f"{summarize(r.seen_minus_sent)} | {r.sender_counter_delta} | {r.receiver_poll_iters} |"
    )
  return "\n".join(lines)


def main() -> None:
  parser = argparse.ArgumentParser(description="One-way NoC multicast latency observed by receiver polling.")
  parser.add_argument("--nocs", type=hop_sweep.parse_nocs, default=(0, 1))
  parser.add_argument("--cases", type=parse_cases, default=("row", "column", "rect"))
  parser.add_argument("--source", type=harness.parse_core, default=None)
  parser.add_argument("--receivers", type=parse_core_list, default=None, help="semicolon-separated X,Y;X,Y list")
  parser.add_argument("--sizes", type=parse_sizes, default=parse_sizes("64,1024,16384"))
  parser.add_argument("--iters", type=int, default=32)
  parser.add_argument("--majors", type=parse_majors, default=("x", "y"), help="x,y or one major axis")
  parser.add_argument("--no-path-reserve", action="store_true", help="clear NOC_CMD_PATH_RESERVE; unsafe under some traffic patterns")
  parser.add_argument("--start-delay", type=int, default=4096)
  parser.add_argument("--inter-delay", type=int, default=2048)
  args = parser.parse_args()
  if args.iters <= 0:
    raise ValueError("--iters must be positive")
  if args.start_delay < 0:
    raise ValueError("--start-delay must be non-negative")
  if args.inter_delay < 0:
    raise ValueError("--inter-delay must be non-negative")

  results: list[RunResult] = []
  with harness.open_device() as device:
    core_set = set(device.cores)
    cmap = read_tensix_coordinate_map(device)
    cases = args.cases
    if args.source is not None or args.receivers is not None:
      if len(cases) != 1:
        raise ValueError("explicit --source/--receivers requires exactly one --cases entry")
      if args.source is None or args.receivers is None:
        raise ValueError("--source and --receivers must be provided together")
      case_specs = [(cases[0], args.source, args.receivers)]
    else:
      case_specs = [(case, *default_case(case)) for case in cases]

    for case, source, receivers in case_specs:
      if source not in core_set:
        raise ValueError(f"source {source} is not a program core")
      for receiver in receivers:
        if receiver not in core_set:
          raise ValueError(f"receiver {receiver} is not a program core")
      for noc in args.nocs:
        rect = logical_rect_for_physical_span(receivers, noc=noc, cmap=cmap)
        routes = {receiver: receiver_route(source, receiver, noc=noc, cmap=cmap) for receiver in receivers}
        for major in args.majors:
          for packet_bytes in args.sizes:
            clear_and_seed(device, source, receivers, packet_bytes, args.iters)
            device.run(McastOneWayProgram(
              noc=noc,
              packet_bytes=packet_bytes,
              iters=args.iters,
              source=source,
              receivers=receivers,
              rect=rect,
              major=major,
              path_reserve=not args.no_path_reserve,
              start_delay=args.start_delay,
              inter_delay=args.inter_delay,
            ))
            results.extend(parse_results(
              device,
              noc=noc,
              case=case,
              major=major,
              source=source,
              receivers=receivers,
              rect=rect,
              routes=routes,
              packet_bytes=packet_bytes,
              iters=args.iters,
            ))

  print(format_results(results))


if __name__ == "__main__":
  main()
