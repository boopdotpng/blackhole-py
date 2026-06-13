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
import riscv_noc_mcast_one_way_latency as mcast  # noqa: E402
from asm import KernelBase
from device import Device
from dsl import a2, a3, s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, t0, t1, t3, t4, zero
from program import DevMsgs, Program, Run, UnicastWrite
from ttk.addrs import Core
from ttk.noc import NOC, Noc
from ttk.tensix import TensixL1


RESULT_BASE = 0x170000
HEADER_WORDS = 16
HEADER_SIZE = HEADER_WORDS * 4
SENDER_SAMPLE_WORDS = 4
RECEIVER_SAMPLE_WORDS = 4
RESULT_MAGIC = 0x4F4D4331  # "OCM1"
STATUS_STARTED = 0x0C000001
STATUS_DONE = 0x0C00D00D

SRC_A = TensixL1.DATA_BUFFER_SPACE_BASE
DST_A = SRC_A
STREAM_STRIDE = 32 * NOC.MAX_BURST_SIZE
SRC_B = SRC_A + STREAM_STRIDE
DST_B = SRC_B
SENTINEL_A = 0xDA000001
SENTINEL_B = 0xDB000001
MASK_A = 1
MASK_B = 2
NOC_CMD_BRCST_XY = 1 << 16


class OverlapKernel(KernelBase, Noc):
  pass


@dataclass(frozen=True)
class StreamSpec:
  name: str
  source: Core
  receivers: tuple[Core, ...]
  src_base: int
  dst_base: int
  sentinel: int


STREAM_A = StreamSpec(
  "a",
  (1, 2),
  (
    (2, 3), (3, 3), (4, 3),
    (2, 4), (3, 4), (4, 4),
    (2, 5), (3, 5), (4, 5),
  ),
  SRC_A,
  DST_A,
  SENTINEL_A,
)

STREAM_B = StreamSpec(
  "b",
  (5, 2),
  (
    (3, 4), (4, 4), (5, 4),
    (3, 5), (4, 5), (5, 5),
    (3, 6), (4, 6), (5, 6),
  ),
  SRC_B,
  DST_B,
  SENTINEL_B,
)


@dataclass(frozen=True)
class ReceiverSpec:
  core: Core
  mask: int


@dataclass(frozen=True)
class SenderResult:
  stream: str
  source: Core
  issue: list[int]
  sent: list[int]
  counter_delta: int


@dataclass(frozen=True)
class ReceiverResult:
  core: Core
  mask: int
  seen_a: list[int]
  seen_b: list[int]
  poll_iters: int


def u64(lo: int, hi: int) -> int:
  return lo | (hi << 32)


def result_size_sender(iters: int) -> int:
  return HEADER_SIZE + iters * SENDER_SAMPLE_WORDS * 4


def result_size_receiver(iters: int) -> int:
  return HEADER_SIZE + iters * RECEIVER_SAMPLE_WORDS * 4


def summarize(values: list[int]) -> str:
  if not values:
    return "-"
  return (
    f"min={min(values)} avg={statistics.fmean(values):.3f} "
    f"med={statistics.median(values):.3f} max={max(values)}"
  )


def emit_header(fw: KernelBase, *, role: int, status: int, noc: int, packet_bytes: int, iters: int, aux: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, role, status, noc, packet_bytes, iters, SRC_A, SRC_B,
    DST_A, DST_B, SENTINEL_A, SENTINEL_B, aux, 0, 0, 0,
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


def emit_mcast_write(fw: OverlapKernel, noc: int, src: int, dst: int, dst_coord, length, *,
                     major: str, linked: bool, path_reserve: bool, a=t3, v=t4):
  ctrl = (
    NOC.CMD_CPY | NOC.CMD_WR | NOC.CMD_RESP_MARKED | NOC.CMD_VC_STATIC |
    NOC.CMD_STATIC_VC_5 | NOC.CMD_BRCST_PACKET
  )
  if linked:
    ctrl |= NOC.CMD_VC_LINKED
  if path_reserve:
    ctrl |= NOC.CMD_PATH_RESERVE
  if major == "y":
    ctrl |= NOC_CMD_BRCST_XY
  fw.noc_wait_cmd_ready(noc, 0, addr=a, val=v)
  fw.noc_cmd_reg(noc, 0, NOC.CTRL, ctrl, addr=a, tmp=v)
  fw.noc_cmd_reg(noc, 0, NOC.TARG_ADDR_LO, src, addr=a, tmp=v)
  fw.noc_cmd_reg(noc, 0, NOC.RET_ADDR_LO, dst, addr=a, tmp=v)
  fw.noc_cmd_reg(noc, 0, NOC.RET_ADDR_MID, 0, addr=a, tmp=v)
  fw.noc_cmd_reg(noc, 0, NOC.RET_ADDR_COORDINATE, dst_coord, addr=a, tmp=v)
  fw.noc_cmd_reg(noc, 0, NOC.AT_LEN_BE, length, addr=a, tmp=v)
  fw.noc_cmd_reg(noc, 0, NOC.AT_LEN_BE_1, 0, addr=a, tmp=v)
  fw.noc_cmd_reg(noc, 0, NOC.CMD_CTRL, NOC.CTRL_SEND_REQ, addr=a, tmp=v)
  return fw


def build_sender(stream: StreamSpec, *, noc: int, major: str, rect: mcast.McastRect, packet_bytes: int,
                 iters: int, depth: int, start_delay: int, inter_delay: int, path_reserve: bool) -> KernelBase:
  fw = OverlapKernel()
  emit_header(fw, role=1, status=STATUS_STARTED, noc=noc, packet_bytes=packet_bytes, iters=iters, aux=ord(stream.name))
  fw.local_noc_coord(noc, s5, x_addr=mcast.BM.MY_X, y_addr=mcast.BM.MY_Y)
  fw.noc_cmd_reg(noc, 0, NOC.TARG_ADDR_COORDINATE, s5, addr=t3, tmp=t4)
  fw.noc_mcast_coord(s9, rect.x0, rect.y0, rect.x1, rect.y1)
  fw.li(s4, packet_bytes)
  fw.li(s10, RESULT_BASE + HEADER_SIZE)
  fw.li(s8, stream.sentinel)
  emit_counter_read(fw, noc, NOC.NIU_MST_NONPOSTED_WR_REQ_SENT, s7)
  fw.mv(s6, s7)
  if start_delay:
    fw.delay_cycles(start_delay, count=t0)

  fw.li(s0, iters)
  loop = fw._new_label("overlap_send_loop")
  body = fw._new_label("overlap_send_body")
  done = fw._new_label("overlap_send_done")
  fw.label(loop)
  fw.bne(s0, zero, body)
  fw.j(done)
  fw.label(body)
  for slot in range(depth):
    fw.li(s11, stream.src_base + slot * NOC.MAX_BURST_SIZE + packet_bytes - 4)
    fw.sw(s8, s11, 0)
  fw.fence()
  harness.read_wall_clock(fw, a2, a3)
  fw.sw(a2, s10, 0)
  fw.sw(a3, s10, 4)
  for slot in range(depth):
    emit_mcast_write(
      fw, noc,
      stream.src_base + slot * NOC.MAX_BURST_SIZE,
      stream.dst_base + slot * NOC.MAX_BURST_SIZE,
      s9, s4,
      major=major,
      linked=(slot + 1) < depth,
      path_reserve=path_reserve and slot == 0,
      a=t3,
      v=t4,
    )
  fw.addi(s6, s6, depth)
  emit_wait_counter_at_least(fw, noc, NOC.NIU_MST_NONPOSTED_WR_REQ_SENT, s6, addr=t3, val=t4)
  harness.read_wall_clock(fw, a2, a3)
  fw.sw(a2, s10, 8)
  fw.sw(a3, s10, 12)
  if inter_delay:
    fw.delay_cycles(inter_delay, count=t0)
  fw.addi(s10, s10, SENDER_SAMPLE_WORDS * 4)
  fw.addi(s8, s8, 1)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  emit_counter_read(fw, noc, NOC.NIU_MST_NONPOSTED_WR_REQ_SENT, t1)
  fw.li(s2, RESULT_BASE)
  fw.sw(s7, s2, 13 * 4)
  fw.sw(t1, s2, 14 * 4)
  emit_status(fw, STATUS_DONE)
  return fw.ret()


def build_receiver(mask: int, *, noc: int, packet_bytes: int, iters: int, depth: int, allow_lap: bool) -> KernelBase:
  fw = OverlapKernel()
  emit_header(fw, role=2, status=STATUS_STARTED, noc=noc, packet_bytes=packet_bytes, iters=iters, aux=mask)
  fw.li(s1, SENTINEL_A)
  fw.li(s2, DST_A + (depth - 1) * NOC.MAX_BURST_SIZE + packet_bytes - 4)
  fw.li(s3, SENTINEL_B)
  fw.li(s4, DST_B + (depth - 1) * NOC.MAX_BURST_SIZE + packet_bytes - 4)
  fw.li(s10, RESULT_BASE + HEADER_SIZE)
  fw.mv(s8, zero)
  fw.li(s0, iters)
  outer = fw._new_label("overlap_recv_outer")
  done = fw._new_label("overlap_recv_done")
  fw.label(outer)
  fw.beq(s0, zero, done)

  if mask == MASK_A:
    poll_a = fw._new_label("overlap_poll_a")
    fw.label(poll_a)
    fw.lw(t1, s2, 0)
    if allow_lap:
      fw.bgeu(t1, s1, "overlap_seen_a")
    else:
      fw.beq(t1, s1, "overlap_seen_a")
    fw.addi(s8, s8, 1)
    fw.j(poll_a)
    fw.label("overlap_seen_a")
    harness.read_wall_clock(fw, a2, a3)
    fw.sw(a2, s10, 0)
    fw.sw(a3, s10, 4)
    fw.sw(zero, s10, 8)
    fw.sw(zero, s10, 12)
  elif mask == MASK_B:
    poll_b = fw._new_label("overlap_poll_b")
    fw.label(poll_b)
    fw.lw(t1, s4, 0)
    if allow_lap:
      fw.bgeu(t1, s3, "overlap_seen_b")
    else:
      fw.beq(t1, s3, "overlap_seen_b")
    fw.addi(s8, s8, 1)
    fw.j(poll_b)
    fw.label("overlap_seen_b")
    fw.sw(zero, s10, 0)
    fw.sw(zero, s10, 4)
    harness.read_wall_clock(fw, a2, a3)
    fw.sw(a2, s10, 8)
    fw.sw(a3, s10, 12)
  elif mask == (MASK_A | MASK_B):
    fw.mv(s5, zero)
    fw.mv(s6, zero)
    poll = fw._new_label("overlap_poll_ab")
    check_b = fw._new_label("overlap_check_b")
    maybe_done = fw._new_label("overlap_maybe_done")
    fw.label(poll)
    fw.bne(s5, zero, check_b)
    fw.lw(t1, s2, 0)
    if allow_lap:
      fw.bltu(t1, s1, check_b)
    else:
      fw.bne(t1, s1, check_b)
    harness.read_wall_clock(fw, a2, a3)
    fw.sw(a2, s10, 0)
    fw.sw(a3, s10, 4)
    fw.li(s5, 1)
    fw.label(check_b)
    fw.bne(s6, zero, maybe_done)
    fw.lw(t1, s4, 0)
    if allow_lap:
      fw.bltu(t1, s3, maybe_done)
    else:
      fw.bne(t1, s3, maybe_done)
    harness.read_wall_clock(fw, a2, a3)
    fw.sw(a2, s10, 8)
    fw.sw(a3, s10, 12)
    fw.li(s6, 1)
    fw.label(maybe_done)
    fw.and_(t1, s5, s6)
    fw.bne(t1, zero, "overlap_seen_both")
    fw.addi(s8, s8, 1)
    fw.j(poll)
    fw.label("overlap_seen_both")
  else:
    raise ValueError(f"bad receiver mask {mask}")

  fw.addi(s10, s10, RECEIVER_SAMPLE_WORDS * 4)
  fw.addi(s1, s1, 1)
  fw.addi(s3, s3, 1)
  fw.addi(s0, s0, -1)
  fw.j(outer)
  fw.label(done)
  fw.li(s2, RESULT_BASE)
  fw.sw(s8, s2, 13 * 4)
  emit_status(fw, STATUS_DONE)
  return fw.ret()


class OverlapMcastProgram:
  def __init__(self, *, noc: int, major: str, packet_bytes: int, iters: int, depth: int,
               rects: dict[str, mcast.McastRect],
               start_delay: int, inter_delay: int, path_reserve: bool, allow_lap: bool):
    self.noc = noc
    self.major = major
    self.packet_bytes = packet_bytes
    self.iters = iters
    self.depth = depth
    self.rects = rects
    self.start_delay = start_delay
    self.inter_delay = inter_delay
    self.path_reserve = path_reserve
    self.allow_lap = allow_lap
    self.name = f"riscv_noc_overlap_mcast_probe:noc{noc}:{major}"

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    empty = KernelBase()
    compiled_cache: dict[int, list] = {}
    per_core_segments = {}
    for stream in (STREAM_A, STREAM_B):
      sender = build_sender(
        stream,
        noc=self.noc,
        major=self.major,
        rect=self.rects[stream.name],
        packet_bytes=self.packet_bytes,
        iters=self.iters,
        depth=self.depth,
        start_delay=self.start_delay,
        inter_delay=self.inter_delay,
        path_reserve=self.path_reserve,
      )
      per_core_segments[stream.source] = Program(
        brisc=sender, ncrisc=empty, trisc0=empty, trisc1=empty, trisc2=empty, num_cores=1,
      ).layout(core_xy=stream.source, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id, compiled_cache=compiled_cache)

    for spec in receiver_specs():
      receiver = build_receiver(
        spec.mask, noc=self.noc, packet_bytes=self.packet_bytes,
        iters=self.iters, depth=self.depth, allow_lap=self.allow_lap,
      )
      per_core_segments[spec.core] = Program(
        brisc=receiver, ncrisc=empty, trisc0=empty, trisc1=empty, trisc2=empty, num_cores=1,
      ).layout(core_xy=spec.core, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id, compiled_cache=compiled_cache)

    active = sorted(per_core_segments)
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


def receiver_specs() -> tuple[ReceiverSpec, ...]:
  a = set(STREAM_A.receivers)
  b = set(STREAM_B.receivers)
  specs = []
  for core in sorted(a | b):
    mask = (MASK_A if core in a else 0) | (MASK_B if core in b else 0)
    specs.append(ReceiverSpec(core, mask))
  return tuple(specs)


def active_cores() -> list[Core]:
  return sorted({STREAM_A.source, STREAM_B.source, *(spec.core for spec in receiver_specs())})


def seed_payload(packet_bytes: int, depth: int, tag: int) -> bytes:
  payload = bytearray(depth * NOC.MAX_BURST_SIZE)
  for slot in range(depth):
    base = slot * NOC.MAX_BURST_SIZE
    for off in range(0, packet_bytes, 4):
      struct.pack_into("<I", payload, base + off, tag | (slot << 16) | off)
  return bytes(payload)


def clear_and_seed(device: Device, packet_bytes: int, depth: int, iters: int):
  payload_a = seed_payload(packet_bytes, depth, 0xD0A00000)
  payload_b = seed_payload(packet_bytes, depth, 0xD0B00000)
  with harness.device_window(device, STREAM_A.source) as win:
    for core in active_cores():
      win.target(core)
      win.write(RESULT_BASE, b"\0" * max(result_size_sender(iters), result_size_receiver(iters)))
      win.write(SRC_A, payload_a)
      win.write(SRC_B, payload_b)


def read_words(device: Device, core: Core, size: int) -> tuple[int, ...]:
  with harness.device_window(device, core) as win:
    blob = win.read(RESULT_BASE, size)
  return struct.unpack_from("<" + "I" * (size // 4), blob, 0)


def parse_sender(device: Device, stream: StreamSpec, iters: int) -> SenderResult:
  words = read_words(device, stream.source, result_size_sender(iters))
  if words[0] != RESULT_MAGIC or words[1] != 1 or words[2] != STATUS_DONE:
    raise RuntimeError(f"sender {stream.name}@{stream.source} bad status magic=0x{words[0]:08x} role={words[1]} status=0x{words[2]:08x}")
  issue = []
  sent = []
  for i in range(iters):
    base = HEADER_WORDS + i * SENDER_SAMPLE_WORDS
    issue.append(u64(words[base], words[base + 1]))
    sent.append(u64(words[base + 2], words[base + 3]))
  return SenderResult(stream.name, stream.source, issue, sent, (words[14] - words[13]) & 0xFFFFFFFF)


def parse_receiver(device: Device, spec: ReceiverSpec, iters: int) -> ReceiverResult:
  words = read_words(device, spec.core, result_size_receiver(iters))
  if words[0] != RESULT_MAGIC or words[1] != 2 or words[2] != STATUS_DONE:
    raise RuntimeError(f"receiver {spec.core} bad status magic=0x{words[0]:08x} role={words[1]} status=0x{words[2]:08x}")
  seen_a = []
  seen_b = []
  for i in range(iters):
    base = HEADER_WORDS + i * RECEIVER_SAMPLE_WORDS
    seen_a.append(u64(words[base], words[base + 1]))
    seen_b.append(u64(words[base + 2], words[base + 3]))
  return ReceiverResult(spec.core, spec.mask, seen_a, seen_b, words[13])


def format_results(*, noc: int, major: str, packet_bytes: int, iters: int, depth: int,
                   senders: dict[str, SenderResult], receivers: list[ReceiverResult]) -> str:
  lines = [
    "| stream | noc | major | depth | receiver | mask | bytes | iters | seen-issue cyc | seen-sent cyc | recv polls |",
    "|---|---:|---|---:|---|---:|---:|---:|---|---|---:|",
  ]
  for r in receivers:
    if r.mask & MASK_A:
      s = senders["a"]
      lines.append(
        f"| a | {noc} | {major} | {depth} | `{r.core[0]},{r.core[1]}` | {r.mask} | {packet_bytes} | {iters} | "
        f"{summarize([seen - issue for seen, issue in zip(r.seen_a, s.issue)])} | "
        f"{summarize([seen - sent for seen, sent in zip(r.seen_a, s.sent)])} | {r.poll_iters} |"
      )
    if r.mask & MASK_B:
      s = senders["b"]
      lines.append(
        f"| b | {noc} | {major} | {depth} | `{r.core[0]},{r.core[1]}` | {r.mask} | {packet_bytes} | {iters} | "
        f"{summarize([seen - issue for seen, issue in zip(r.seen_b, s.issue)])} | "
        f"{summarize([seen - sent for seen, sent in zip(r.seen_b, s.sent)])} | {r.poll_iters} |"
      )
  lines.append("\n| sender | source | sent reqs |")
  lines.append("|---|---|---:|")
  for s in senders.values():
    lines.append(f"| {s.stream} | `{s.source[0]},{s.source[1]}` | {s.counter_delta} |")
  return "\n".join(lines)


def main() -> None:
  parser = argparse.ArgumentParser(description="Run two overlapping multicast rectangles with separate destination addresses.")
  parser.add_argument("--nocs", type=hop_sweep.parse_nocs, default=(0,))
  parser.add_argument("--majors", type=mcast.parse_majors, default=("x",))
  parser.add_argument("--sizes", type=mcast.parse_sizes, default=mcast.parse_sizes("16384"))
  parser.add_argument("--iters", type=int, default=8)
  parser.add_argument("--depth", type=int, default=1, help="number of multicast requests per VC_LINKED transaction")
  parser.add_argument("--start-delay", type=int, default=4096)
  parser.add_argument("--inter-delay", type=int, default=2048)
  parser.add_argument("--path-reserve", action="store_true")
  parser.add_argument(
    "--allow-lap", action="store_true",
    help="stress mode: let receivers treat a later sentinel as progress if senders lap them",
  )
  args = parser.parse_args()
  if args.iters <= 0:
    raise ValueError("--iters must be positive")
  if args.depth <= 0:
    raise ValueError("--depth must be positive")
  if SRC_B + args.depth * NOC.MAX_BURST_SIZE > RESULT_BASE:
    raise ValueError(f"--depth {args.depth} exceeds scratch space before RESULT_BASE")

  outputs = []
  with harness.open_device() as device:
    missing = sorted(set(active_cores()) - set(device.cores))
    if missing:
      raise ValueError(f"unavailable cores: {missing}")
    cmap = mcast.read_tensix_coordinate_map(device)
    for noc in args.nocs:
      rects = {
        stream.name: mcast.logical_rect_for_physical_span(stream.receivers, noc=noc, cmap=cmap)
        for stream in (STREAM_A, STREAM_B)
      }
      for major in args.majors:
        for packet_bytes in args.sizes:
          clear_and_seed(device, packet_bytes, args.depth, args.iters)
          device.run(OverlapMcastProgram(
            noc=noc,
            major=major,
            packet_bytes=packet_bytes,
            iters=args.iters,
            depth=args.depth,
            rects=rects,
            start_delay=args.start_delay,
            inter_delay=args.inter_delay,
            path_reserve=args.path_reserve,
            allow_lap=args.allow_lap,
          ))
          senders = {
            "a": parse_sender(device, STREAM_A, args.iters),
            "b": parse_sender(device, STREAM_B, args.iters),
          }
          receivers = [parse_receiver(device, spec, args.iters) for spec in receiver_specs()]
          outputs.append(format_results(
            noc=noc,
            major=major,
            packet_bytes=packet_bytes,
            iters=args.iters,
            depth=args.depth,
            senders=senders,
            receivers=receivers,
          ))
  print("\n\n".join(outputs))


if __name__ == "__main__":
  main()
