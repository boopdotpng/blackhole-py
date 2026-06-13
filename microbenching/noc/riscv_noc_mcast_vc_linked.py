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
from ttk.mailbox import BriscMailbox as BM
from ttk.noc import NOC, Noc
from ttk.tensix import TensixL1


RESULT_BASE = 0x170000
HEADER_WORDS = 16
HEADER_SIZE = HEADER_WORDS * 4
SENDER_SAMPLE_WORDS = 4
RECEIVER_SAMPLE_WORDS = 2
RESULT_MAGIC = 0x4C434D31  # "LCM1"
STATUS_STARTED = 0x2C000001
STATUS_DONE = 0x2C00D00D
ROLE_SENDER = 1
ROLE_RECEIVER = 2

SRC_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
DST_BASE = SRC_BASE
SLOT_STRIDE = NOC.MAX_BURST_SIZE
SENTINEL_BASE = 0xC7000001
NOC_CMD_BRCST_XY = 1 << 16


class LinkedMcastKernel(KernelBase, Noc):
  pass


@dataclass(frozen=True)
class SenderResult:
  issue: list[int]
  sent: list[int]
  counter_delta: int


@dataclass(frozen=True)
class ReceiverResult:
  core: Core
  seen: list[int]
  poll_iters: int


def u64(lo: int, hi: int) -> int:
  return lo | (hi << 32)


def parse_depths(text: str) -> tuple[int, ...]:
  depths = tuple(int(item.strip(), 0) for item in text.split(",") if item.strip())
  if not depths:
    raise argparse.ArgumentTypeError("expected comma-separated linked depths")
  for depth in depths:
    if depth < 1 or depth > 64:
      raise argparse.ArgumentTypeError("depths must be in [1, 64]")
  return depths


def parse_core_list(text: str) -> tuple[Core, ...]:
  try:
    return tuple(harness.parse_core(item.strip()) for item in text.split(";") if item.strip())
  except Exception as exc:
    raise argparse.ArgumentTypeError("expected semicolon-separated cores as X,Y;X,Y") from exc


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


def emit_header(fw: KernelBase, *, role: int, status: int, noc: int, packet_bytes: int, iters: int, depth: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, role, status, noc, packet_bytes, iters, depth, SRC_BASE,
    DST_BASE, SLOT_STRIDE, SENTINEL_BASE, 0, 0, 0, 0, 0,
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


def emit_mcast_write(fw: LinkedMcastKernel, noc: int, src: int, dst: int, dst_coord, length,
                     *, major: str, linked: bool, path_reserve: bool, a=t3, v=t4):
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


def build_sender(*, noc: int, major: str, rect: mcast.McastRect, packet_bytes: int, iters: int, depth: int,
                 receivers: tuple[Core, ...], path_reserve: bool, start_delay: int, inter_delay: int) -> KernelBase:
  fw = LinkedMcastKernel()
  emit_header(fw, role=ROLE_SENDER, status=STATUS_STARTED, noc=noc, packet_bytes=packet_bytes, iters=iters, depth=depth)
  fw.local_noc_coord(noc, s5, x_addr=BM.MY_X, y_addr=BM.MY_Y)
  fw.noc_cmd_reg(noc, 0, NOC.TARG_ADDR_COORDINATE, s5, addr=t3, tmp=t4)
  fw.noc_mcast_coord(s9, rect.x0, rect.y0, rect.x1, rect.y1)
  fw.li(s4, packet_bytes)
  fw.li(s10, RESULT_BASE + HEADER_SIZE)
  fw.li(s8, SENTINEL_BASE)
  emit_counter_read(fw, noc, NOC.NIU_MST_NONPOSTED_WR_REQ_SENT, s7)
  fw.mv(s6, s7)
  if start_delay:
    fw.delay_cycles(start_delay, count=t0)

  fw.li(s0, iters)
  loop = fw._new_label("linked_send_loop")
  body = fw._new_label("linked_send_body")
  done = fw._new_label("linked_send_done")
  fw.label(loop)
  fw.bne(s0, zero, body)
  fw.j(done)
  fw.label(body)
  for slot in range(depth):
    fw.li(s11, SRC_BASE + slot * SLOT_STRIDE + packet_bytes - 4)
    fw.sw(s8, s11, 0)
  fw.fence()
  harness.read_wall_clock(fw, a2, a3)
  fw.sw(a2, s10, 0)
  fw.sw(a3, s10, 4)
  for slot in range(depth):
    emit_mcast_write(
      fw, noc, SRC_BASE + slot * SLOT_STRIDE, DST_BASE + slot * SLOT_STRIDE, s9, s4,
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


def build_receiver(*, noc: int, packet_bytes: int, iters: int, depth: int) -> KernelBase:
  fw = LinkedMcastKernel()
  emit_header(fw, role=ROLE_RECEIVER, status=STATUS_STARTED, noc=noc, packet_bytes=packet_bytes, iters=iters, depth=depth)
  fw.li(s1, SENTINEL_BASE)
  fw.li(s2, DST_BASE + (depth - 1) * SLOT_STRIDE + packet_bytes - 4)
  fw.li(s10, RESULT_BASE + HEADER_SIZE)
  fw.mv(s8, zero)
  fw.li(s0, iters)
  outer = fw._new_label("linked_recv_outer")
  done = fw._new_label("linked_recv_done")
  poll = fw._new_label("linked_recv_poll")
  fw.label(outer)
  fw.beq(s0, zero, done)
  fw.label(poll)
  fw.lw(t1, s2, 0)
  fw.beq(t1, s1, "linked_seen")
  fw.addi(s8, s8, 1)
  fw.j(poll)
  fw.label("linked_seen")
  harness.read_wall_clock(fw, a2, a3)
  fw.sw(a2, s10, 0)
  fw.sw(a3, s10, 4)
  fw.addi(s10, s10, RECEIVER_SAMPLE_WORDS * 4)
  fw.addi(s1, s1, 1)
  fw.addi(s0, s0, -1)
  fw.j(outer)
  fw.label(done)
  fw.li(s2, RESULT_BASE)
  fw.sw(s8, s2, 13 * 4)
  emit_status(fw, STATUS_DONE)
  return fw.ret()


class LinkedMcastProgram:
  def __init__(self, *, noc: int, major: str, packet_bytes: int, iters: int, depth: int,
               source: Core, receivers: tuple[Core, ...], rect: mcast.McastRect, path_reserve: bool,
               start_delay: int, inter_delay: int):
    self.noc = noc
    self.major = major
    self.packet_bytes = packet_bytes
    self.iters = iters
    self.depth = depth
    self.source = source
    self.receivers = receivers
    self.rect = rect
    self.path_reserve = path_reserve
    self.start_delay = start_delay
    self.inter_delay = inter_delay
    self.name = f"riscv_noc_mcast_vc_linked:noc{noc}:{major}:d{depth}"

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    empty = KernelBase()
    compiled_cache: dict[int, list] = {}
    per_core_segments = {}
    sender = build_sender(
      noc=self.noc,
      major=self.major,
      rect=self.rect,
      packet_bytes=self.packet_bytes,
      iters=self.iters,
      depth=self.depth,
      receivers=self.receivers,
      path_reserve=self.path_reserve,
      start_delay=self.start_delay,
      inter_delay=self.inter_delay,
    )
    per_core_segments[self.source] = Program(
      brisc=sender, ncrisc=empty, trisc0=empty, trisc1=empty, trisc2=empty, num_cores=1,
    ).layout(core_xy=self.source, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id, compiled_cache=compiled_cache)

    for receiver in self.receivers:
      receiver_fw = build_receiver(noc=self.noc, packet_bytes=self.packet_bytes, iters=self.iters, depth=self.depth)
      per_core_segments[receiver] = Program(
        brisc=receiver_fw, ncrisc=empty, trisc0=empty, trisc1=empty, trisc2=empty, num_cores=1,
      ).layout(core_xy=receiver, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id, compiled_cache=compiled_cache)

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


def seed_payload(packet_bytes: int, depth: int) -> bytes:
  payload = bytearray(depth * SLOT_STRIDE)
  for slot in range(depth):
    base = slot * SLOT_STRIDE
    for off in range(0, packet_bytes, 4):
      struct.pack_into("<I", payload, base + off, 0xCC000000 | (slot << 16) | off)
  return bytes(payload)


def clear_and_seed(device: Device, source: Core, receivers: tuple[Core, ...], packet_bytes: int, depth: int, iters: int):
  payload = seed_payload(packet_bytes, depth)
  active = sorted({source, *receivers})
  result_size = max(result_size_sender(iters), result_size_receiver(iters))
  with harness.device_window(device, source) as win:
    for core in active:
      win.target(core)
      win.write(RESULT_BASE, b"\0" * result_size)
      win.write(SRC_BASE, payload)


def read_words(device: Device, core: Core, size: int) -> tuple[int, ...]:
  with harness.device_window(device, core) as win:
    blob = win.read(RESULT_BASE, size)
  return struct.unpack_from("<" + "I" * (size // 4), blob, 0)


def parse_sender(device: Device, source: Core, iters: int) -> SenderResult:
  words = read_words(device, source, result_size_sender(iters))
  if words[0] != RESULT_MAGIC or words[1] != ROLE_SENDER or words[2] != STATUS_DONE:
    raise RuntimeError(f"sender {source} bad status magic=0x{words[0]:08x} role={words[1]} status=0x{words[2]:08x}")
  issue = []
  sent = []
  for i in range(iters):
    base = HEADER_WORDS + i * SENDER_SAMPLE_WORDS
    issue.append(u64(words[base], words[base + 1]))
    sent.append(u64(words[base + 2], words[base + 3]))
  return SenderResult(issue, sent, (words[14] - words[13]) & 0xFFFFFFFF)


def parse_receiver(device: Device, receiver: Core, iters: int) -> ReceiverResult:
  words = read_words(device, receiver, result_size_receiver(iters))
  if words[0] != RESULT_MAGIC or words[1] != ROLE_RECEIVER or words[2] != STATUS_DONE:
    raise RuntimeError(f"receiver {receiver} bad status magic=0x{words[0]:08x} role={words[1]} status=0x{words[2]:08x}")
  seen = []
  for i in range(iters):
    base = HEADER_WORDS + i * RECEIVER_SAMPLE_WORDS
    seen.append(u64(words[base], words[base + 1]))
  return ReceiverResult(receiver, seen, words[13])


def format_result(*, noc: int, major: str, source: Core, receivers: tuple[Core, ...],
                  packet_bytes: int, iters: int, depth: int, path_reserve: bool,
                  rect: mcast.McastRect, sender: SenderResult,
                  receiver_results: list[ReceiverResult]) -> str:
  lines = [
    "| noc | major | reserve | depth | source | receiver | rect | bytes | iters | seen-issue cyc | seen-sent cyc | sent reqs | recv polls |",
    "|---:|---|---:|---:|---|---|---|---:|---:|---|---|---:|---:|",
  ]
  for r in receiver_results:
    lines.append(
      f"| {noc} | {major} | {int(path_reserve)} | {depth} | `{source[0]},{source[1]}` | "
      f"`{r.core[0]},{r.core[1]}` | `{rect.x0},{rect.y0}->{rect.x1},{rect.y1}` | "
      f"{packet_bytes} | {iters} | "
      f"{summarize([seen - issue for seen, issue in zip(r.seen, sender.issue)])} | "
      f"{summarize([seen - sent for seen, sent in zip(r.seen, sender.sent)])} | "
      f"{sender.counter_delta} | {r.poll_iters} |"
    )
  return "\n".join(lines)


def default_receivers() -> tuple[Core, ...]:
  return (
    (2, 3), (3, 3), (4, 3),
    (2, 4), (3, 4), (4, 4),
    (2, 5), (3, 5), (4, 5),
  )


def main() -> None:
  parser = argparse.ArgumentParser(description="Legal VC_LINKED multicast transaction benchmark.")
  parser.add_argument("--nocs", type=hop_sweep.parse_nocs, default=(0,))
  parser.add_argument("--majors", type=mcast.parse_majors, default=("x",))
  parser.add_argument("--source", type=harness.parse_core, default=(1, 2))
  parser.add_argument("--receivers", type=parse_core_list, default=default_receivers(), help="semicolon-separated X,Y;X,Y list")
  parser.add_argument("--sizes", type=mcast.parse_sizes, default=mcast.parse_sizes("64,1024,16384"))
  parser.add_argument("--iters", type=int, default=16)
  parser.add_argument("--depths", type=parse_depths, default=parse_depths("1,2,4,8"))
  parser.add_argument("--no-path-reserve", action="store_true")
  parser.add_argument("--start-delay", type=int, default=4096)
  parser.add_argument("--inter-delay", type=int, default=4096)
  args = parser.parse_args()
  if args.iters <= 0:
    raise ValueError("--iters must be positive")

  outputs = []
  path_reserve = not args.no_path_reserve
  with harness.open_device() as device:
    active = {args.source, *args.receivers}
    missing = sorted(active - set(device.cores))
    if missing:
      raise ValueError(f"unavailable cores: {missing}")
    cmap = mcast.read_tensix_coordinate_map(device)
    for noc in args.nocs:
      rect = mcast.logical_rect_for_physical_span(args.receivers, noc=noc, cmap=cmap)
      for major in args.majors:
        for packet_bytes in args.sizes:
          for depth in args.depths:
            if SRC_BASE + depth * SLOT_STRIDE > RESULT_BASE:
              raise ValueError(f"depth {depth} exceeds scratch space before RESULT_BASE")
            clear_and_seed(device, args.source, args.receivers, packet_bytes, depth, args.iters)
            device.run(LinkedMcastProgram(
              noc=noc,
              major=major,
              packet_bytes=packet_bytes,
              iters=args.iters,
              depth=depth,
              source=args.source,
              receivers=args.receivers,
              rect=rect,
              path_reserve=path_reserve,
              start_delay=args.start_delay,
              inter_delay=args.inter_delay,
            ))
            sender = parse_sender(device, args.source, args.iters)
            receiver_results = [parse_receiver(device, receiver, args.iters) for receiver in args.receivers]
            outputs.append(format_result(
              noc=noc,
              major=major,
              source=args.source,
              receivers=args.receivers,
              packet_bytes=packet_bytes,
              iters=args.iters,
              depth=depth,
              path_reserve=path_reserve,
              rect=rect,
              sender=sender,
              receiver_results=receiver_results,
            ))
  print("\n\n".join(outputs))


if __name__ == "__main__":
  main()
