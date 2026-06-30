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
from asm import KernelBase  # noqa: E402
from device import Device  # noqa: E402
from dsl import a2, a3, a4, a5, s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, t0, t1, t3, t4, zero  # noqa: E402
from program import DevMsgs, Program, Run, UnicastWrite  # noqa: E402
from ttk.addrs import Core, noc_xy  # noqa: E402
from ttk.mailbox import BriscMailbox as BM  # noqa: E402
from ttk.noc import NOC, Noc  # noqa: E402
from ttk.tensix import TensixL1  # noqa: E402


RESULT_BASE = 0x150000
RESULT_WORDS = 24
RESULT_SIZE = RESULT_WORDS * 4
RESULT_MAGIC = 0x56534353  # "VSCS"
STATUS_STARTED = 0x56010001
STATUS_DONE = 0x5601D00D

SRC_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
DST_BASE = SRC_BASE
MARKER_SRC = SRC_BASE + NOC.MAX_BURST_SIZE
MARKER_DST = DST_BASE + NOC.MAX_BURST_SIZE
MARKER_VALUE = 0x5CA1E001

ROLE_SENDER = 1
ROLE_RECEIVER = 2
MODES = ("dynamic", "static")
ARB_PRIORITY_SHIFT = 27


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
  def cycles(self) -> int:
    return self.end - self.start

  @property
  def counter_delta(self) -> int:
    return (self.words[13] - self.words[12]) & 0xFFFFFFFF


class VcStaticKernel(KernelBase, Noc):
  def noc_write_ctrl(self, *, noc: int, ctrl, src, dst_lo, dst_coord, length, a=t3, v=t4):
    self.noc_wait_cmd_ready(noc, 0, addr=a, val=v)
    self.noc_cmd_reg(noc, 0, NOC.CTRL, ctrl, addr=a, tmp=v)
    self.noc_cmd_reg(noc, 0, NOC.TARG_ADDR_LO, src, addr=a, tmp=v)
    self.noc_cmd_reg(noc, 0, NOC.RET_ADDR_LO, dst_lo, addr=a, tmp=v)
    self.noc_cmd_reg(noc, 0, NOC.RET_ADDR_MID, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, 0, NOC.RET_ADDR_COORDINATE, dst_coord, addr=a, tmp=v)
    self.noc_cmd_reg(noc, 0, NOC.AT_LEN_BE, length, addr=a, tmp=v)
    self.noc_cmd_reg(noc, 0, NOC.AT_LEN_BE_1, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, 0, NOC.CMD_CTRL, NOC.CTRL_SEND_REQ, addr=a, tmp=v)
    return self


def parse_csv_ints(text: str) -> tuple[int, ...]:
  values = tuple(int(item.strip(), 0) for item in text.split(",") if item.strip())
  if not values or any(value <= 0 for value in values):
    raise argparse.ArgumentTypeError("expected comma-separated positive integers")
  return values


def parse_modes(text: str) -> tuple[str, ...]:
  values = tuple(item.strip() for item in text.split(",") if item.strip())
  if not values:
    raise argparse.ArgumentTypeError("expected comma-separated modes")
  bad = sorted(set(values) - set(MODES))
  if bad:
    raise argparse.ArgumentTypeError(f"unknown mode(s): {', '.join(bad)}")
  return values


def parse_vcs(text: str) -> tuple[int, ...]:
  values = tuple(int(item.strip(), 0) for item in text.split(",") if item.strip())
  if not values:
    raise argparse.ArgumentTypeError("expected comma-separated VCs")
  for value in values:
    if not 0 <= value <= 5:
      raise argparse.ArgumentTypeError("VCs must be in [0, 5]")
  return values


def parse_priorities(text: str) -> tuple[int, ...]:
  values = tuple(int(item.strip(), 0) for item in text.split(",") if item.strip())
  if not values:
    raise argparse.ArgumentTypeError("expected comma-separated priority values")
  for value in values:
    if not 0 <= value <= 15:
      raise argparse.ArgumentTypeError("priority values must be in [0, 15]")
  return values


def ctrl_for_mode(*, mode: str, vc: int, priority: int, posted: bool) -> int:
  ctrl = NOC.CMD_CPY | NOC.CMD_WR | (vc << 13) | (priority << ARB_PRIORITY_SHIFT)
  if mode == "static":
    ctrl |= NOC.CMD_VC_STATIC
  if not posted:
    ctrl |= NOC.CMD_RESP_MARKED
  return ctrl


def emit_header(fw: VcStaticKernel, *, role: int, status: int, noc: int, vc: int,
                priority: int, packets: int, packet_bytes: int, mode: str, posted: bool):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, role, status, noc, vc, packets, packet_bytes, int(posted),
    SRC_BASE, DST_BASE, MARKER_DST, MARKER_VALUE, 1 if mode == "static" else 0,
    priority,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off in range(14, RESULT_WORDS):
    fw.sw(zero, s2, off * 4)
  return fw


def emit_status(fw: VcStaticKernel, status: int):
  fw.li(s2, RESULT_BASE)
  fw.li(t0, status)
  fw.sw(t0, s2, 2 * 4)
  return fw


def emit_counter_read(fw: VcStaticKernel, noc: int, counter: int, out, *, addr=t3):
  fw.li(addr, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  return fw.lw(out, addr, 0)


def build_sender(*, noc: int, vc: int, priority: int, packets: int, packet_bytes: int,
                 mode: str, posted: bool) -> KernelBase:
  ctrl = ctrl_for_mode(mode=mode, vc=vc, priority=priority, posted=posted)
  counter = NOC.NIU_MST_POSTED_WR_REQ_SENT if posted else NOC.NIU_MST_WR_ACK_RECEIVED
  fw = VcStaticKernel()
  emit_header(fw, role=ROLE_SENDER, status=STATUS_STARTED, noc=noc, vc=vc,
              priority=priority, packets=packets, packet_bytes=packet_bytes,
              mode=mode, posted=posted)
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s9,))
  fw.li(s1, ctrl)
  fw.li(s2, SRC_BASE)
  fw.li(s3, DST_BASE)
  fw.li(s4, packet_bytes)
  emit_counter_read(fw, noc, counter, s7)
  fw.mv(s6, s7)

  harness.read_wall_clock(fw, a2, a3)
  fw.li(s0, packets)
  loop = fw._new_label("vc_static_loop")
  done = fw._new_label("vc_static_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  fw.noc_write_ctrl(noc=noc, ctrl=s1, src=s2, dst_lo=s3, dst_coord=s9, length=s4)
  fw.addi(s6, s6, 1)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  fw.li(s2, MARKER_SRC)
  fw.li(s3, MARKER_DST)
  fw.li(s4, 4)
  fw.noc_write_ctrl(noc=noc, ctrl=s1, src=s2, dst_lo=s3, dst_coord=s9, length=s4)
  fw.addi(s6, s6, 1)

  if posted:
    fw.noc_wait_cmd_ready(noc, 0, addr=t3, val=t4).fence()
  else:
    fw.noc_write_barrier(noc, s6, addr=t3, val=t4)
  harness.read_wall_clock(fw, a4, a5)
  emit_counter_read(fw, noc, counter, s8)

  fw.li(s2, RESULT_BASE)
  for off, reg in enumerate((a2, a3, a4, a5, s7, s8), start=8):
    fw.sw(reg, s2, off * 4)
  emit_status(fw, STATUS_DONE)
  return fw.ret()


def build_receiver(*, noc: int, vc: int, priority: int, packets: int, packet_bytes: int,
                   mode: str, posted: bool) -> KernelBase:
  fw = VcStaticKernel()
  emit_header(fw, role=ROLE_RECEIVER, status=STATUS_STARTED, noc=noc, vc=vc,
              priority=priority, packets=packets, packet_bytes=packet_bytes,
              mode=mode, posted=posted)
  fw.li(s0, MARKER_VALUE)
  fw.li(s1, MARKER_DST)
  fw.mv(s8, zero)
  poll = fw._new_label("vc_static_poll")
  done = fw._new_label("vc_static_seen")
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
  emit_status(fw, STATUS_DONE)
  return fw.ret()


class VcStaticProgram:
  def __init__(self, *, noc: int, vc: int, packets: int, packet_bytes: int,
               source: Core, target: Core, mode: str, priority: int, posted: bool):
    self.noc = noc
    self.vc = vc
    self.packets = packets
    self.packet_bytes = packet_bytes
    self.source = source
    self.target = target
    self.mode = mode
    self.priority = priority
    self.posted = posted
    self.name = (
      f"riscv_noc_vc_static_speed:{mode}:{'posted' if posted else 'nonposted'}:"
      f"noc{noc}:vc{vc}:pri{priority}"
    )

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    empty = KernelBase()
    sender_fw = build_sender(
      noc=self.noc, vc=self.vc, packets=self.packets, packet_bytes=self.packet_bytes,
      mode=self.mode, priority=self.priority, posted=self.posted,
    )
    sender_fw.rta(lambda _x, _y: [noc_xy(*self.target)])
    receiver_fw = build_receiver(
      noc=self.noc, vc=self.vc, packets=self.packets, packet_bytes=self.packet_bytes,
      mode=self.mode, priority=self.priority, posted=self.posted,
    )
    compiled_cache: dict[int, list] = {}
    sender = Program(
      brisc=sender_fw, ncrisc=empty, trisc0=empty, trisc1=empty, trisc2=empty, num_cores=1,
    ).layout(core_xy=self.source, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id, compiled_cache=compiled_cache)
    receiver = Program(
      brisc=receiver_fw, ncrisc=empty, trisc0=empty, trisc1=empty, trisc2=empty, num_cores=1,
    ).layout(core_xy=self.target, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id, compiled_cache=compiled_cache)
    active = [self.source, self.target]
    reset_blob = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_RESET_READ_PTR_FROM_HOST)
    commands = [
      UnicastWrite(active, TensixL1.GO_MSG, [reset_blob] * len(active)),
      UnicastWrite(active, TensixL1.GO_MSG_INDEX, [b"\0\0\0\0"] * len(active)),
    ]
    for segment in sender:
      commands.append(UnicastWrite([self.source], segment.addr, [segment.data]))
    if self.target != self.source:
      for segment in receiver:
        commands.append(UnicastWrite([self.target], segment.addr, [segment.data]))
    commands.append(Run(active))
    return commands


def seed(device: Device, source: Core, target: Core, packet_bytes: int):
  payload = bytearray(NOC.MAX_BURST_SIZE + 0x100)
  for off in range(0, NOC.MAX_BURST_SIZE, 4):
    struct.pack_into("<I", payload, off, 0xA5000000 | off)
  struct.pack_into("<I", payload, MARKER_SRC - SRC_BASE, MARKER_VALUE)
  with harness.device_window(device, source) as win:
    win.target(source)
    win.write(RESULT_BASE, b"\0" * RESULT_SIZE)
    win.write(SRC_BASE, bytes(payload))
    win.target(target)
    win.write(RESULT_BASE, b"\0" * RESULT_SIZE)
    win.write(DST_BASE, b"\0" * len(payload))


def read_result(device: Device, core: Core, *, role: int) -> Result:
  blob = harness.read_window(device, core, RESULT_BASE, RESULT_SIZE)
  words = struct.unpack_from("<" + "I" * RESULT_WORDS, blob)
  if words[0] != RESULT_MAGIC or words[1] != role:
    raise RuntimeError(f"{core}: bad result magic=0x{words[0]:08x} role={words[1]}")
  if words[2] != STATUS_DONE:
    raise RuntimeError(f"{core}: status 0x{words[2]:08x}")
  return Result(core, words)


def summarize(values: list[float]) -> str:
  if not values:
    return "-"
  return f"{statistics.fmean(values):.3f} (min {min(values):.3f}, max {max(values):.3f})"


def main():
  parser = argparse.ArgumentParser(description="Compare dynamic vs CMD_VC_STATIC NoC write speed.")
  parser.add_argument("--nocs", type=hop_sweep.parse_nocs, default=(0,))
  parser.add_argument("--source", type=harness.parse_core, default=(1, 2))
  parser.add_argument("--target", type=harness.parse_core, default=(2, 2))
  parser.add_argument("--modes", type=parse_modes, default=MODES)
  parser.add_argument("--vcs", type=parse_vcs, default=(1,))
  parser.add_argument("--priorities", type=parse_priorities, default=(0,))
  parser.add_argument("--sizes", type=mcast.parse_sizes, default=mcast.parse_sizes("64,1024,16384"))
  parser.add_argument("--packets", type=parse_csv_ints, default=(16, 128, 1024))
  parser.add_argument("--posted", action="store_true")
  parser.add_argument("--repeat", type=int, default=1)
  parser.add_argument("--no-report", action="store_true")
  parser.add_argument("--report", type=Path, default=harness.doc_path("noc", "noc-vc-command-flags.md"))
  args = parser.parse_args()
  if args.repeat <= 0:
    raise ValueError("--repeat must be positive")

  rows = [
    "| mode | posted | noc | vc | priority | source | target | bytes | packets | sender B/cyc | receiver B/cyc | sender cyc | receiver cyc | counter delta | receiver polls |",
    "|---|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---|---|---|---:|",
  ]
  with harness.open_device() as device:
    if args.source == args.target:
      raise ValueError("source and target must be different cores")
    if args.source not in set(device.cores) or args.target not in set(device.cores):
      raise ValueError("source and target must be usable program cores")
    for noc in args.nocs:
      for mode in args.modes:
        for vc in args.vcs:
          for priority in args.priorities:
            for packet_bytes in args.sizes:
              for packets in args.packets:
                sender_bpc = []
                receiver_bpc = []
                sender_cycles = []
                receiver_cycles = []
                counter_deltas = []
                receiver_polls = []
                total_bytes = packet_bytes * packets
                for _ in range(args.repeat):
                  seed(device, args.source, args.target, packet_bytes)
                  device.run(VcStaticProgram(
                    noc=noc, vc=vc, packets=packets, packet_bytes=packet_bytes,
                    source=args.source, target=args.target, mode=mode,
                    priority=priority, posted=args.posted,
                  ))
                  sender = read_result(device, args.source, role=ROLE_SENDER)
                  receiver = read_result(device, args.target, role=ROLE_RECEIVER)
                  receiver_cycles_i = receiver.end - sender.start
                  sender_cycles.append(sender.cycles)
                  receiver_cycles.append(receiver_cycles_i)
                  counter_deltas.append(sender.counter_delta)
                  receiver_polls.append(receiver.words[12])
                  if sender.cycles > 0:
                    sender_bpc.append(total_bytes / sender.cycles)
                  if receiver_cycles_i > 0:
                    receiver_bpc.append(total_bytes / receiver_cycles_i)
                rows.append(
                  f"| {mode} | {int(args.posted)} | {noc} | {vc} | {priority} | `{args.source[0]},{args.source[1]}` | "
                  f"`{args.target[0]},{args.target[1]}` | {packet_bytes} | {packets} | "
                  f"{summarize(sender_bpc)} | {summarize(receiver_bpc)} | "
                  f"{summarize([float(v) for v in sender_cycles])} | {summarize([float(v) for v in receiver_cycles])} | "
                  f"{summarize([float(v) for v in counter_deltas])} | {max(receiver_polls)} |"
                )

  table = "\n".join(rows)
  print(table)
  if not args.no_report:
    harness.append_report(args.report, "NoC VC static speed", [
      f"Command: `microbenching/noc/riscv_noc_vc_static_speed.py --nocs {','.join(str(n) for n in args.nocs)} --modes {','.join(args.modes)} --vcs {','.join(str(v) for v in args.vcs)} --priorities {','.join(str(p) for p in args.priorities)} --sizes {','.join(str(s) for s in args.sizes)} --packets {','.join(str(p) for p in args.packets)} --repeat {args.repeat}{' --posted' if args.posted else ''}`",
      "`dynamic` clears `CMD_VC_STATIC`; `static` sets `CMD_VC_STATIC | NOC_CMD_STATIC_VC(vc)`.",
      "`priority` is encoded as `priority << 27`; tt-metal documents `0` as round-robin/no priority.",
      "The measured payload excludes the final 4-byte marker used to stop the receiver.",
    ], table)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
