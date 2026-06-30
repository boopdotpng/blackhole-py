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
RESULT_WORDS = 24
RESULT_SIZE = RESULT_WORDS * 4
RESULT_MAGIC = 0x56504350  # "VPCP"
STATUS_STARTED = 0x56000001
STATUS_DONE = 0x5600D00D

PACKET_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
MARKER_ADDR = PACKET_BASE + NOC.MAX_BURST_SIZE
MARKER_SRC_ADDR = MARKER_ADDR + 0x40
MARKER_VALUE = 0xC001CAFE
NOC_CMD_BRCST_XY = 1 << 16

ROLE_SENDER = 1
ROLE_RECEIVER = 2
MODES = ("unicast-posted", "unicast-nonposted", "mcast-posted", "mcast-nonposted")


@dataclass(frozen=True)
class PressureCase:
  row: int
  cut: tuple[Core, Core] | None
  pairs: list[aggregate.Pair]
  mcast_rects: list[tuple[Core, Core]]


@dataclass(frozen=True)
class Result:
  core: Core
  words: tuple[int, ...]

  @property
  def status(self) -> int:
    return self.words[2]

  @property
  def start(self) -> int:
    return self.words[8] | (self.words[9] << 32)

  @property
  def end(self) -> int:
    return self.words[10] | (self.words[11] << 32)

  @property
  def ready_total(self) -> int:
    return self.words[12] | (self.words[13] << 32)

  @property
  def ready_max(self) -> int:
    return self.words[14]


class PressureKernel(KernelBase, Noc):
  def timed_write(self, *, noc: int, ctrl, src, dst_lo, dst_coord, length,
                  ready_total=s8, ready_max=s10):
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
  if not values or any(value <= 0 for value in values):
    raise argparse.ArgumentTypeError("expected comma-separated positive integers")
  return values


def parse_vcs(text: str) -> tuple[int, ...]:
  values = tuple(int(item.strip(), 0) for item in text.split(",") if item.strip())
  if not values:
    raise argparse.ArgumentTypeError("expected comma-separated VCs")
  for value in values:
    if not 0 <= value <= 5:
      raise argparse.ArgumentTypeError("VCs must be in [0, 5]")
  return values


def parse_modes(text: str) -> tuple[str, ...]:
  values = tuple(item.strip() for item in text.split(",") if item.strip())
  if not values:
    raise argparse.ArgumentTypeError("expected comma-separated modes")
  bad = sorted(set(values) - set(MODES))
  if bad:
    raise argparse.ArgumentTypeError(f"unknown mode(s): {', '.join(bad)}")
  return values


def emit_header(fw: PressureKernel, *, role: int, status: int, noc: int, vc: int, packets: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, role, status, noc, vc, packets, NOC.MAX_BURST_SIZE, MARKER_VALUE,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off in range(8, RESULT_WORDS):
    fw.sw(zero, s2, off * 4)
  return fw


def ctrl_for_mode(*, vc: int, mode: str, path_reserve: bool) -> int:
  ctrl = NOC.CMD_CPY | NOC.CMD_WR | NOC.CMD_VC_STATIC | (vc << 13)
  if "nonposted" in mode:
    ctrl |= NOC.CMD_RESP_MARKED
  if mode.startswith("mcast"):
    ctrl |= NOC.CMD_BRCST_PACKET
    if path_reserve:
      ctrl |= NOC.CMD_PATH_RESERVE
  return ctrl


def completion_counter_for_mode(mode: str) -> int:
  if mode == "unicast-nonposted":
    return NOC.NIU_MST_WR_ACK_RECEIVED
  if mode == "mcast-nonposted":
    return NOC.NIU_MST_NONPOSTED_WR_REQ_SENT
  return NOC.NIU_MST_WR_ACK_RECEIVED


def build_sender(*, noc: int, vc: int, packets: int, mode: str, target: Core,
                 mcast_rect: tuple[Core, Core], path_reserve: bool) -> PressureKernel:
  fw = PressureKernel()
  ctrl = ctrl_for_mode(vc=vc, mode=mode, path_reserve=path_reserve)
  emit_header(fw, role=ROLE_SENDER, status=STATUS_STARTED, noc=noc, vc=vc, packets=packets)
  if mode.startswith("mcast"):
    start, end = mcast_rect
    fw.noc_mcast_coord(s9, start[0], start[1], end[0], end[1])
  else:
    fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s9,))
  fw.li(s0, packets)
  fw.li(s1, ctrl)
  fw.li(s2, PACKET_BASE)
  fw.li(s3, PACKET_BASE)
  fw.li(s4, NOC.MAX_BURST_SIZE)
  fw.li(s5, MARKER_SRC_ADDR)
  fw.li(s6, MARKER_ADDR)
  fw.mv(s8, zero)
  fw.mv(s10, zero)
  completion_counter = completion_counter_for_mode(mode)
  fw.li(t3, NOC.STATUS_BASE + completion_counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  fw.lw(s7, t3, 0)

  harness.read_wall_clock(fw, a2, a3)
  loop = fw._new_label("packet_loop")
  done = fw._new_label("packet_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  fw.timed_write(noc=noc, ctrl=s1, src=s2, dst_lo=s3, dst_coord=s9, length=s4)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  fw.li(t0, 4)
  fw.timed_write(noc=noc, ctrl=s1, src=s5, dst_lo=s6, dst_coord=s9, length=t0)
  if "nonposted" in mode:
    fw.mv(s6, s7)
    fw.li(t0, packets + 1)
    fw.add(s6, s6, t0)
    fw.li(t3, NOC.STATUS_BASE + completion_counter + (noc << NOC.INSTANCE_OFFSET_BIT))
    wait_done = fw._new_label("completion_done")
    wait_loop = fw._new_label("completion_loop")
    fw.label(wait_loop)
    fw.lw(t4, t3, 0)
    fw.bgeu(t4, s6, wait_done)
    fw.j(wait_loop)
    fw.label(wait_done).fence()
  else:
    fw.noc_wait_cmd_ready(noc, 0, addr=t3, val=t4).fence()
  harness.read_wall_clock(fw, a4, a5)
  fw.li(t3, NOC.STATUS_BASE + completion_counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  fw.lw(t4, t3, 0)

  fw.li(s2, RESULT_BASE)
  for off, reg in enumerate((a2, a3, a4, a5, s8, zero, s10, s7, t4), start=8):
    fw.sw(reg, s2, off * 4)
  fw.li(t0, STATUS_DONE)
  fw.sw(t0, s2, 2 * 4)
  return fw.ret()


def build_receiver(*, noc: int, vc: int, packets: int) -> PressureKernel:
  fw = PressureKernel()
  emit_header(fw, role=ROLE_RECEIVER, status=STATUS_STARTED, noc=noc, vc=vc, packets=packets)
  fw.li(s0, MARKER_VALUE)
  fw.li(s1, MARKER_ADDR)
  fw.mv(s8, zero)
  poll = fw._new_label("marker_poll")
  done = fw._new_label("marker_seen")
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
  fw.sw(s8, s2, 12 * 4)
  fw.sw(t0, s2, 13 * 4)
  fw.li(t1, STATUS_DONE)
  fw.sw(t1, s2, 2 * 4)
  return fw.ret()


class PressureProgram:
  def __init__(self, *, pairs: list[aggregate.Pair], mcast_rects: list[tuple[Core, Core]],
               noc: int, vc: int, packets: int, mode: str, path_reserve: bool):
    self.pairs = list(pairs)
    self.mcast_rects = list(mcast_rects)
    if len(self.mcast_rects) != len(self.pairs):
      raise ValueError("mcast_rects length must match pairs length")
    self.noc = noc
    self.vc = vc
    self.packets = packets
    self.mode = mode
    self.path_reserve = path_reserve
    self.name = f"riscv_noc_vc_pressure_loop:{mode}:noc{noc}:vc{vc}:pairs{len(pairs)}:n{packets}"

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
    target_cores = []
    segments = {}
    for pair, rect in zip(self.pairs, self.mcast_rects):
      sender = build_sender(
        noc=self.noc, vc=self.vc, packets=self.packets, mode=self.mode,
        target=pair.target, mcast_rect=rect, path_reserve=self.path_reserve,
      )
      sender.rta(lambda _x, _y, target=pair.target: [noc_xy(*target)])
      receiver = build_receiver(noc=self.noc, vc=self.vc, packets=self.packets)
      segments[pair.source] = self._layout(
        pair.source, sender, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id,
      )
      segments[pair.target] = self._layout(
        pair.target, receiver, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id,
      )
      target_cores.extend((pair.source, pair.target))
    reset_blob = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_RESET_READ_PTR_FROM_HOST)
    commands = [
      UnicastWrite(target_cores, TensixL1.GO_MSG, [reset_blob] * len(target_cores)),
      UnicastWrite(target_cores, TensixL1.GO_MSG_INDEX, [b"\0\0\0\0"] * len(target_cores)),
    ]
    for core in target_cores:
      for segment in segments[core]:
        commands.append(UnicastWrite([core], segment.addr, [segment.data]))
    commands.append(Run(target_cores))
    return commands


def choose_pair(cores: list[Core], *, noc: int, row: int | None) -> tuple[Core, Core]:
  rows = aggregate.rows_by_y(cores)
  if row is None:
    row = max(((len(xs), -y, y) for y, xs in rows.items()), default=(0, 0, -1))[2]
  xs = rows.get(row)
  if not xs or len(xs) < 2:
    raise ValueError(f"row {row} does not have at least two usable cores")
  if noc == 0:
    return (xs[len(xs) // 2], row), (xs[-1], row)
  return (xs[len(xs) // 2], row), (xs[0], row)


def choose_pressure_case(cores: list[Core], *, noc: int, row: int | None, count: int,
                         source: Core | None, target: Core | None,
                         mcast_fanout: int) -> PressureCase:
  if source is not None or target is not None:
    if source is None or target is None:
      raise ValueError("--source and --target must be provided together")
    if count != 1:
      raise ValueError("--source/--target only support --count 1")
    return PressureCase(row=source[1], cut=None, pairs=[aggregate.Pair(source, target)], mcast_rects=[(target, target)])

  if count == 1:
    source, target = choose_pair(cores, noc=noc, row=row)
    return PressureCase(row=source[1], cut=None, pairs=[aggregate.Pair(source, target)], mcast_rects=[(target, target)])

  rows = aggregate.rows_by_y(cores)
  candidates = []
  for y, xs in rows.items():
    if row is not None and y != row:
      continue
    ordered = xs if noc == 0 else list(reversed(xs))
    for split in range(1, len(ordered)):
      upstream = ordered[:split]
      downstream = ordered[split:]
      if len(upstream) < count or len(downstream) < count * mcast_fanout:
        continue
      cut = ((ordered[split - 1], y), (ordered[split], y))
      candidates.append((y, split, upstream, downstream, cut))
  if not candidates:
    raise ValueError(f"could not find {count} disjoint streams sharing one directed row cut")
  y, _split, upstream, downstream, cut = min(candidates, key=lambda item: (item[0], item[1]))
  sources = upstream[-count:]
  pairs = []
  rects = []
  for i, src in enumerate(sources):
    rect_xs = downstream[i * mcast_fanout:(i + 1) * mcast_fanout]
    monitor = rect_xs[0]
    pairs.append(aggregate.Pair((src, y), (monitor, y)))
    rects.append(((rect_xs[0], y), (rect_xs[-1], y)))
  return PressureCase(row=y, cut=cut, pairs=pairs, mcast_rects=rects)


def rect_cores(rect: tuple[Core, Core]) -> list[Core]:
  (x0, y0), (x1, y1) = rect
  if y0 != y1:
    raise ValueError("pressure-loop mcast rectangles are row-only for now")
  lo, hi = sorted((x0, x1))
  return [(x, y0) for x in range(lo, hi + 1)]


def seed(device: Device, case: PressureCase):
  packet = bytearray(NOC.MAX_BURST_SIZE)
  for off in range(0, len(packet), 4):
    struct.pack_into("<I", packet, off, 0xA5000000 | off)
  with harness.device_window(device, case.pairs[0].source) as win:
    for pair, rect in zip(case.pairs, case.mcast_rects):
      win.target(pair.source)
      win.write(RESULT_BASE, b"\0" * RESULT_SIZE)
      win.write(PACKET_BASE, bytes(packet))
      win.write(MARKER_SRC_ADDR, struct.pack("<I", MARKER_VALUE))
      for receiver in rect_cores(rect):
        win.target(receiver)
        win.write(RESULT_BASE, b"\0" * RESULT_SIZE)
        win.write(PACKET_BASE, b"\0" * (NOC.MAX_BURST_SIZE + 0x80))


def read_result(device: Device, core: Core) -> Result:
  blob = harness.read_window(device, core, RESULT_BASE, RESULT_SIZE)
  words = struct.unpack_from("<" + "I" * RESULT_WORDS, blob)
  if words[0] != RESULT_MAGIC:
    raise RuntimeError(f"{core}: bad magic 0x{words[0]:08x}")
  if words[2] != STATUS_DONE:
    raise RuntimeError(f"{core}: status 0x{words[2]:08x}")
  return Result(core, words)


def main():
  parser = argparse.ArgumentParser(description="Issue many posted NoC packets on one static VC using a reused source packet.")
  parser.add_argument("--noc", type=int, choices=(0, 1), default=0)
  parser.add_argument("--row", type=int, default=None)
  parser.add_argument("--source", type=harness.parse_core, default=None)
  parser.add_argument("--target", type=harness.parse_core, default=None)
  parser.add_argument("--count", type=int, default=1, help="number of disjoint same-cut streams")
  parser.add_argument("--mcast-fanout", type=int, default=1, help="receivers per row multicast rectangle")
  parser.add_argument("--no-path-reserve", action="store_true", help="clear CMD_PATH_RESERVE for multicast modes")
  parser.add_argument("--vcs", type=parse_vcs, default=(1,))
  parser.add_argument("--modes", type=parse_modes, default=("unicast-posted",))
  parser.add_argument("--packets", type=parse_csv_ints, default=(100, 1000, 10000))
  parser.add_argument("--no-report", action="store_true")
  parser.add_argument("--report", type=Path, default=harness.doc_path("noc", "noc-vc-pressure-loop.md"))
  args = parser.parse_args()
  if args.count <= 0:
    raise ValueError("--count must be positive")
  if args.mcast_fanout <= 0:
    raise ValueError("--mcast-fanout must be positive")

  lines = [
    "| mode | noc | vc | streams | packets/stream | pairs | cut | total MiB | sender window cyc | sender agg B/cyc | receiver window cyc | receiver agg B/cyc | per-stream min B/cyc | per-stream max B/cyc | ready avg cyc | ready max cyc | completion delta | receiver polls max |",
    "|---|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
  ]
  with harness.open_device() as device:
    case = choose_pressure_case(
      aggregate.usable_program_cores(device), noc=args.noc, row=args.row, count=args.count,
      source=args.source, target=args.target, mcast_fanout=args.mcast_fanout,
    )
    for pair in case.pairs:
      if pair.source not in set(device.cores) or pair.target not in set(device.cores):
        raise ValueError("source and target must be usable program cores")
    for packets in args.packets:
      for mode in args.modes:
       for vc in args.vcs:
        seed(device, case)
        device.run(PressureProgram(
          pairs=case.pairs, mcast_rects=case.mcast_rects,
          noc=args.noc, vc=vc, packets=packets, mode=mode,
          path_reserve=not args.no_path_reserve,
        ))
        senders = [read_result(device, pair.source) for pair in case.pairs]
        receivers = [read_result(device, pair.target) for pair in case.pairs]
        total_bytes = len(case.pairs) * packets * NOC.MAX_BURST_SIZE
        start = min(sender.start for sender in senders)
        sender_cycles = max(sender.end for sender in senders) - start
        receiver_cycles = max(receiver.end for receiver in receivers) - start
        commands = packets + 1
        ack_delta = sum((sender.words[16] - sender.words[15]) & 0xFFFFFFFF for sender in senders)
        per_stream = [
          packets * NOC.MAX_BURST_SIZE / (sender.end - sender.start)
          for sender in senders
          if sender.end > sender.start
        ]
        ready_total = sum(sender.ready_total for sender in senders)
        ready_max = max(sender.ready_max for sender in senders)
        pairs_text = " ".join(f"{pair.source[0]},{pair.source[1]}->{pair.target[0]},{pair.target[1]}" for pair in case.pairs)
        cut_text = "-" if case.cut is None else f"{case.cut[0][0]},{case.cut[0][1]}->{case.cut[1][0]},{case.cut[1][1]}"
        rects_text = " ".join(
          f"{rect[0][0]},{rect[0][1]}..{rect[1][0]},{rect[1][1]}" for rect in case.mcast_rects
        )
        lines.append(
          f"| {mode} | {args.noc} | {vc} | {len(case.pairs)} | {packets} | `{pairs_text}; mrects {rects_text}` | `{cut_text}` | "
          f"{total_bytes / (1024 * 1024):.2f} | {sender_cycles} | {total_bytes / sender_cycles:.3f} | "
          f"{receiver_cycles} | {total_bytes / receiver_cycles:.3f} | "
          f"{min(per_stream):.3f} | {max(per_stream):.3f} | {ready_total / (len(case.pairs) * commands):.2f} | "
          f"{ready_max} | {ack_delta} | {max(receiver.words[12] for receiver in receivers)} |"
        )

  table = "\n".join(lines)
  print(table)
  if not args.no_report:
    harness.append_report(args.report, "NoC VC posted pressure loop", [
      f"NoC: `{args.noc}`",
      f"VCs: `{','.join(str(v) for v in args.vcs)}`",
      f"Modes: `{','.join(args.modes)}`",
      f"Packets: `{','.join(str(p) for p in args.packets)}`",
      f"Streams: `{len(case.pairs)}`",
      f"Mcast fanout: `{args.mcast_fanout}`",
      f"Mcast path reserve: `{not args.no_path_reserve}`",
      "Traffic: posted 16 KiB writes from one source buffer, then a same-VC 4B final marker",
    ], table)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
