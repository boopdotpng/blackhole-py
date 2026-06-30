#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
import riscv_noc_aggregate as aggregate  # noqa: E402
from asm import KernelBase  # noqa: E402
from device import Device  # noqa: E402
from dsl import a2, a3, a4, a5, s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, t0, t1, t3, t4, t5, t6, zero  # noqa: E402
from program import DevMsgs, Program, Run, UnicastWrite  # noqa: E402
from ttk.addrs import Core, noc_xy  # noqa: E402
from ttk.mailbox import BriscMailbox as BM  # noqa: E402
from ttk.noc import NOC, Noc  # noqa: E402
from ttk.tensix import TensixL1  # noqa: E402


RESULT_BASE = 0x150000
RESULT_WORDS = 32
RESULT_SIZE = RESULT_WORDS * 4
RESULT_MAGIC = 0x4152504F  # "ARPO"
STATUS_STARTED = 0xA4000001
STATUS_DONE = 0xA400D00D

PACKET_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
MARKER_SRC_ADDR = PACKET_BASE + NOC.MAX_BURST_SIZE
MARKER_DST_ADDR = MARKER_SRC_ADDR
MARKER_BASE = 0xA6B00000
ARB_PRIORITY_SHIFT = 27

ROLE_SENDER = 1
ROLE_RECEIVER = 2


@dataclass(frozen=True)
class Case:
  row: int
  cut: tuple[Core, Core]
  pairs: list[aggregate.Pair]


@dataclass(frozen=True)
class Result:
  core: Core
  words: tuple[int, ...]

  @property
  def start(self) -> int:
    return self.words[8] | (self.words[9] << 32)

  @property
  def end(self) -> int:
    return self.words[10] | (self.words[11] << 32)

  @property
  def observed(self) -> int:
    return self.words[10] | (self.words[11] << 32)


class ArbPriorityKernel(KernelBase, Noc):
  def timed_write(self, *, noc: int, ctrl, src, dst_lo, dst_coord, length, ready_total=s8, ready_max=s10):
    harness.read_wall_clock(self, a4, a5)
    self.noc_wait_cmd_ready(noc, 0, addr=t3, val=t4)
    harness.read_wall_clock(self, t5, t6)
    self.sub(s11, t5, a4)
    self.add(ready_total, ready_total, s11)
    skip = self._new_label("ready_max_skip")
    self.bltu(s11, ready_max, skip)
    self.mv(ready_max, s11)
    self.label(skip)
    self.noc_cmd_reg(noc, 0, NOC.CTRL, ctrl, addr=t3, tmp=t4)
    self.noc_cmd_reg(noc, 0, NOC.TARG_ADDR_LO, src, addr=t3, tmp=t4)
    self.noc_cmd_reg(noc, 0, NOC.RET_ADDR_LO, dst_lo, addr=t3, tmp=t4)
    self.noc_cmd_reg(noc, 0, NOC.RET_ADDR_MID, 0, addr=t3, tmp=t4)
    self.noc_cmd_reg(noc, 0, NOC.RET_ADDR_COORDINATE, dst_coord, addr=t3, tmp=t4)
    self.noc_cmd_reg(noc, 0, NOC.AT_LEN_BE, length, addr=t3, tmp=t4)
    self.noc_cmd_reg(noc, 0, NOC.AT_LEN_BE_1, 0, addr=t3, tmp=t4)
    self.noc_cmd_reg(noc, 0, NOC.CMD_CTRL, NOC.CTRL_SEND_REQ, addr=t3, tmp=t4)
    return self


def parse_csv_ints(text: str) -> tuple[int, ...]:
  values = tuple(int(item.strip(), 0) for item in text.split(",") if item.strip())
  if not values:
    raise argparse.ArgumentTypeError("expected comma-separated integers")
  return values


def parse_priorities(text: str) -> tuple[int, ...]:
  values = parse_csv_ints(text)
  for value in values:
    if not 0 <= value <= 15:
      raise argparse.ArgumentTypeError("priorities must be in [0, 15]")
  return values


def parse_trids(text: str) -> tuple[int, ...]:
  values = parse_csv_ints(text)
  for value in values:
    if not 0 <= value <= NOC.MAX_TRANSACTION_ID:
      raise argparse.ArgumentTypeError(f"transaction ids must be in [0, {NOC.MAX_TRANSACTION_ID}]")
  if len(set(values)) != len(values):
    raise argparse.ArgumentTypeError("transaction ids must be unique")
  return values


def ctrl_for_priority(priority: int, *, static_vc: int | None, posted: bool) -> int:
  ctrl = NOC.CMD_CPY | NOC.CMD_WR | (priority << ARB_PRIORITY_SHIFT)
  if static_vc is not None:
    ctrl |= NOC.CMD_VC_STATIC | (static_vc << 13)
  if not posted:
    ctrl |= NOC.CMD_RESP_MARKED
  return ctrl


def emit_header(fw: ArbPriorityKernel, *, role: int, status: int, noc: int, priority: int,
                trid: int, packets: int, packet_bytes: int, static_vc: int | None, posted: bool):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, role, status, noc, priority, trid, packets, packet_bytes,
    0, 0, 0, 0, NOC.MAX_BURST_SIZE, MARKER_BASE | trid,
    0xFFFFFFFF if static_vc is None else static_vc, int(posted),
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off in range(16, RESULT_WORDS):
    fw.sw(zero, s2, off * 4)
  return fw


def emit_status(fw: ArbPriorityKernel, status: int):
  fw.li(s2, RESULT_BASE)
  fw.li(t0, status)
  fw.sw(t0, s2, 2 * 4)
  return fw


def emit_counter_read(fw: ArbPriorityKernel, noc: int, counter: int, out, *, addr=t3):
  fw.li(addr, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  return fw.lw(out, addr, 0)


def emit_wait_trid_zero(fw: ArbPriorityKernel, noc: int, trid: int, *, addr=t3, val=t4):
  fw.li(addr, NOC.STATUS_BASE + NOC.niu_mst_reqs_outstanding_id(trid) + (noc << NOC.INSTANCE_OFFSET_BIT))
  loop = fw._new_label("trid_zero")
  fw.label(loop)
  fw.lw(val, addr, 0)
  fw.bne(val, zero, loop)
  return fw.fence()


def emit_read_trid(fw: ArbPriorityKernel, noc: int, trid: int, out, *, addr=t3):
  fw.li(addr, NOC.STATUS_BASE + NOC.niu_mst_reqs_outstanding_id(trid) + (noc << NOC.INSTANCE_OFFSET_BIT))
  return fw.lw(out, addr, 0)


def build_sender(*, noc: int, priority: int, trid: int, packets: int, packet_bytes: int,
                 static_vc: int | None, posted: bool) -> KernelBase:
  fw = ArbPriorityKernel()
  ctrl = ctrl_for_priority(priority, static_vc=static_vc, posted=posted)
  counter = NOC.NIU_MST_POSTED_WR_REQ_SENT if posted else NOC.NIU_MST_WR_ACK_RECEIVED
  emit_header(
    fw, role=ROLE_SENDER, status=STATUS_STARTED, noc=noc, priority=priority,
    trid=trid, packets=packets, packet_bytes=packet_bytes, static_vc=static_vc, posted=posted,
  )
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s9,))
  fw.reset_noc_trid_barrier_counter(noc, 1 << trid, addr=t3, val=t4)
  fw.noc_set_transaction_id(noc, 0, trid, addr=t3, val=t4)
  fw.li(s1, ctrl)
  fw.li(s2, PACKET_BASE)
  fw.li(s3, PACKET_BASE)
  fw.li(s4, packet_bytes)
  fw.mv(s8, zero)
  fw.mv(s10, zero)
  emit_counter_read(fw, noc, counter, s7)

  harness.read_wall_clock(fw, a2, a3)
  fw.li(s0, packets)
  loop = fw._new_label("arb_packet_loop")
  done = fw._new_label("arb_packet_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  fw.timed_write(noc=noc, ctrl=s1, src=s2, dst_lo=s3, dst_coord=s9, length=s4)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  fw.li(s2, MARKER_SRC_ADDR)
  fw.li(s3, MARKER_DST_ADDR)
  fw.li(s4, 4)
  fw.timed_write(noc=noc, ctrl=s1, src=s2, dst_lo=s3, dst_coord=s9, length=s4)
  if posted:
    fw.noc_wait_cmd_ready(noc, 0, addr=t3, val=t4).fence()
  else:
    emit_wait_trid_zero(fw, noc, trid, addr=t3, val=t4)
  harness.read_wall_clock(fw, a4, a5)
  emit_counter_read(fw, noc, counter, t0)
  emit_read_trid(fw, noc, trid, t1, addr=t3)

  fw.li(s2, RESULT_BASE)
  for off, reg in enumerate((a2, a3, a4, a5, s7, t0, s8, zero, s10, t1), start=8):
    fw.sw(reg, s2, off * 4)
  emit_status(fw, STATUS_DONE)
  return fw.ret()


def build_receiver(*, noc: int, priority: int, trid: int, packets: int,
                   packet_bytes: int, static_vc: int | None, posted: bool) -> KernelBase:
  fw = ArbPriorityKernel()
  marker = MARKER_BASE | trid
  emit_header(
    fw, role=ROLE_RECEIVER, status=STATUS_STARTED, noc=noc, priority=priority,
    trid=trid, packets=packets, packet_bytes=packet_bytes, static_vc=static_vc, posted=posted,
  )
  fw.li(s0, marker)
  fw.li(s1, MARKER_DST_ADDR)
  fw.mv(s8, zero)
  poll = fw._new_label("arb_marker_poll")
  done = fw._new_label("arb_marker_seen")
  fw.label(poll)
  fw.lw(t0, s1, 0)
  fw.beq(t0, s0, done)
  fw.addi(s8, s8, 1)
  fw.j(poll)
  fw.label(done)
  harness.read_wall_clock(fw, a2, a3)
  fw.li(s2, RESULT_BASE)
  fw.sw(a2, s2, 10 * 4)
  fw.sw(a3, s2, 11 * 4)
  fw.sw(s8, s2, 16 * 4)
  fw.sw(t0, s2, 17 * 4)
  emit_status(fw, STATUS_DONE)
  return fw.ret()


class ArbPriorityProgram:
  def __init__(self, *, pairs: list[aggregate.Pair], noc: int, priorities: tuple[int, ...],
               trids: tuple[int, ...], packets: int, packet_bytes: int,
               static_vc: int | None, posted: bool):
    if len(pairs) != len(priorities) or len(pairs) != len(trids):
      raise ValueError("pairs, priorities, and trids must have the same length")
    self.pairs = list(pairs)
    self.noc = noc
    self.priorities = tuple(priorities)
    self.trids = tuple(trids)
    self.packets = packets
    self.packet_bytes = packet_bytes
    self.static_vc = static_vc
    self.posted = posted
    self.name = f"riscv_noc_arb_priority_order:noc{noc}:streams{len(pairs)}"

  def _layout(self, core: Core, kernel: KernelBase, *, dispatch_mode: int, host_assigned_id: int):
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
    segments = {}
    active = []
    for pair, priority, trid in zip(self.pairs, self.priorities, self.trids):
      sender = build_sender(
        noc=self.noc, priority=priority, trid=trid, packets=self.packets,
        packet_bytes=self.packet_bytes, static_vc=self.static_vc, posted=self.posted,
      )
      sender.rta(lambda _x, _y, target=pair.target: [noc_xy(*target)])
      receiver = build_receiver(
        noc=self.noc, priority=priority, trid=trid, packets=self.packets,
        packet_bytes=self.packet_bytes, static_vc=self.static_vc, posted=self.posted,
      )
      segments[pair.source] = self._layout(
        pair.source, sender, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id,
      )
      segments[pair.target] = self._layout(
        pair.target, receiver, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id,
      )
      active.extend((pair.source, pair.target))
    reset_blob = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_RESET_READ_PTR_FROM_HOST)
    commands = [
      UnicastWrite(active, TensixL1.GO_MSG, [reset_blob] * len(active)),
      UnicastWrite(active, TensixL1.GO_MSG_INDEX, [b"\0\0\0\0"] * len(active)),
    ]
    for core in active:
      for segment in segments[core]:
        commands.append(UnicastWrite([core], segment.addr, [segment.data]))
    commands.append(Run(active))
    return commands


def choose_case(cores: list[Core], *, noc: int, row: int | None, count: int) -> Case:
  candidates = []
  for y, xs in aggregate.rows_by_y(cores).items():
    if row is not None and y != row:
      continue
    ordered = xs if noc == 0 else list(reversed(xs))
    for split in range(1, len(ordered)):
      upstream = ordered[:split]
      downstream = ordered[split:]
      if len(upstream) < count or len(downstream) < count:
        continue
      sources = upstream[-count:]
      targets = downstream[:count]
      distances = [abs(dst - src) for src, dst in zip(sources, targets)]
      spread = max(distances) - min(distances)
      cut = ((ordered[split - 1], y), (ordered[split], y))
      candidates.append((spread, max(distances), y, split, upstream, downstream, cut))
  if not candidates:
    raise ValueError(f"could not find {count} streams sharing one directed row cut")
  _spread, _max_distance, y, _split, upstream, downstream, cut = min(candidates)
  sources = upstream[-count:]
  targets = downstream[:count]
  return Case(
    row=y,
    cut=cut,
    pairs=[aggregate.Pair((src, y), (dst, y)) for src, dst in zip(sources, targets)],
  )


def seed(device: Device, pairs: list[aggregate.Pair], *, trids: tuple[int, ...]):
  packet = bytearray(NOC.MAX_BURST_SIZE + 0x80)
  for off in range(0, NOC.MAX_BURST_SIZE, 4):
    struct.pack_into("<I", packet, off, 0xA5000000 | off)
  with harness.device_window(device, pairs[0].source) as win:
    for pair, trid in zip(pairs, trids):
      struct.pack_into("<I", packet, MARKER_SRC_ADDR - PACKET_BASE, MARKER_BASE | trid)
      win.target(pair.source)
      win.write(RESULT_BASE, b"\0" * RESULT_SIZE)
      win.write(PACKET_BASE, bytes(packet))
      win.target(pair.target)
      win.write(RESULT_BASE, b"\0" * RESULT_SIZE)
      win.write(PACKET_BASE, b"\0" * len(packet))


def read_result(device: Device, core: Core, role: int) -> Result:
  blob = harness.read_window(device, core, RESULT_BASE, RESULT_SIZE)
  words = struct.unpack_from("<" + "I" * RESULT_WORDS, blob)
  if words[0] != RESULT_MAGIC or words[1] != role:
    raise RuntimeError(f"{core}: bad result magic=0x{words[0]:08x} role={words[1]}")
  if words[2] != STATUS_DONE:
    raise RuntimeError(f"{core}: status 0x{words[2]:08x}")
  return Result(core, words)


def format_order(label: str, rows: list[tuple[int, int, int]]) -> str:
  ordered = sorted(rows, key=lambda item: item[2])
  return " ".join(f"{label}{i}:p{priority}:d{delta}" for i, priority, delta in ordered)


def main():
  parser = argparse.ArgumentParser(description="Priority arbitration order probe for same-direction unicast NoC streams.")
  parser.add_argument("--noc", type=int, choices=(0, 1), default=0)
  parser.add_argument("--row", type=int, default=None)
  parser.add_argument("--count", type=int, default=4)
  parser.add_argument("--priorities", type=parse_priorities, default=parse_priorities("0,1,8,15"))
  parser.add_argument("--trids", type=parse_trids, default=parse_trids("0,1,2,3"))
  parser.add_argument("--packets", type=int, default=16)
  parser.add_argument("--bytes", type=int, default=NOC.MAX_BURST_SIZE)
  parser.add_argument("--static-vc", type=int, default=None, help="pin all streams to this static VC; omit for dynamic VC allocation")
  parser.add_argument("--posted", action="store_true")
  parser.add_argument("--no-report", action="store_true")
  parser.add_argument("--report", type=Path, default=harness.doc_path("noc", "noc-vc-command-flags.md"))
  args = parser.parse_args()
  if args.count <= 0:
    raise ValueError("--count must be positive")
  if len(args.priorities) != args.count:
    raise ValueError("--priorities length must match --count")
  if len(args.trids) != args.count:
    raise ValueError("--trids length must match --count")
  if args.packets <= 0:
    raise ValueError("--packets must be positive")
  if args.bytes <= 0 or args.bytes > NOC.MAX_BURST_SIZE or args.bytes % 4:
    raise ValueError(f"--bytes must be a 4-byte multiple in [4, {NOC.MAX_BURST_SIZE}]")
  if args.static_vc is not None and not 0 <= args.static_vc <= 5:
    raise ValueError("--static-vc must be in [0, 5]")

  lines = [
    "| stream | priority | trid | source | target | sender done delta | receiver seen delta | sender B/cyc | ready avg | ready max | ack delta | trid outstanding | polls | marker |",
    "|---:|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
  ]
  with harness.open_device() as device:
    case = choose_case(aggregate.usable_program_cores(device), noc=args.noc, row=args.row, count=args.count)
    for pair in case.pairs:
      if pair.source not in set(device.cores) or pair.target not in set(device.cores):
        raise ValueError("selected source/target must be usable program cores")
    seed(device, case.pairs, trids=args.trids)
    device.run(ArbPriorityProgram(
      pairs=case.pairs, noc=args.noc, priorities=args.priorities, trids=args.trids,
      packets=args.packets, packet_bytes=args.bytes, static_vc=args.static_vc, posted=args.posted,
    ))
    senders = [read_result(device, pair.source, ROLE_SENDER) for pair in case.pairs]
    receivers = [read_result(device, pair.target, ROLE_RECEIVER) for pair in case.pairs]

  start0 = min(sender.start for sender in senders)
  total_bytes = args.bytes * args.packets
  sender_order = []
  receiver_order = []
  for i, (pair, priority, trid, sender, receiver) in enumerate(
      zip(case.pairs, args.priorities, args.trids, senders, receivers)):
    sender_delta = sender.end - start0
    receiver_delta = receiver.observed - start0
    sender_order.append((i, priority, sender_delta))
    receiver_order.append((i, priority, receiver_delta))
    sender_cycles = sender.end - sender.start
    sender_bpc = total_bytes / sender_cycles if sender_cycles > 0 else 0.0
    ack_delta = (sender.words[13] - sender.words[12]) & 0xFFFFFFFF
    ready_total = sender.words[14] | (sender.words[15] << 32)
    commands = args.packets + 1
    lines.append(
      f"| {i} | {priority} | {trid} | `{pair.source[0]},{pair.source[1]}` | `{pair.target[0]},{pair.target[1]}` | "
      f"{sender_delta} | {receiver_delta} | {sender_bpc:.3f} | {ready_total / commands:.2f} | "
      f"{sender.words[16]} | {ack_delta} | {sender.words[17]} | {receiver.words[16]} | 0x{receiver.words[17]:08x} |"
    )
  summary = [
    f"NoC: `{args.noc}`; cut: `{case.cut[0][0]},{case.cut[0][1]}->{case.cut[1][0]},{case.cut[1][1]}`",
    f"Dynamic VC: `{args.static_vc is None}`; static VC: `{args.static_vc}`; posted: `{args.posted}`",
    f"Packets/stream: `{args.packets}`; bytes/packet: `{args.bytes}`; priorities: `{','.join(str(p) for p in args.priorities)}`",
    f"Sender order: `{format_order('s', sender_order)}`",
    f"Receiver order: `{format_order('s', receiver_order)}`",
  ]
  table = "\n".join(lines)
  print("\n".join(f"- {item}" for item in summary))
  print()
  print(table)
  if not args.no_report:
    harness.append_report(args.report, "NoC arbitration priority order", summary, table)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
