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
import riscv_noc_mcast_one_way_latency as mcast  # noqa: E402
from asm import KernelBase
from device import Device
from dsl import a2, a3, s0, s1, s2, s4, s5, s8, s9, t0, t1, t3, t4, zero
from program import DevMsgs, Program, Run, UnicastWrite
from ttk.addrs import Core
from ttk.mailbox import BriscMailbox as BM
from ttk.noc import NOC, Noc
from ttk.tensix import TensixL1


RESULT_BASE = 0x170000
HEADER_WORDS = 16
HEADER_SIZE = HEADER_WORDS * 4
RESULT_MAGIC = 0x5357434D  # "MCWS"
STATUS_STARTED = 0x5C000001
STATUS_DONE = 0x5C00D00D
ROLE_SENDER = 1
ROLE_RECEIVER = 2
SRC_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
DST_BASE = SRC_BASE
SENTINEL = 0xE7000001
NOC_CMD_BRCST_XY = 1 << 16


class RectSweepKernel(KernelBase, Noc):
  pass


@dataclass(frozen=True)
class Case:
  logical_rect: mcast.McastRect
  physical_rect: mcast.McastRect
  encoded_rect: mcast.McastRect
  receivers: tuple[Core, ...]


def parse_range(text: str) -> tuple[int, int]:
  parts = [int(part.strip(), 0) for part in text.split(":", 1)]
  if len(parts) != 2 or parts[0] > parts[1]:
    raise argparse.ArgumentTypeError("expected START:END inclusive range")
  return parts[0], parts[1]


def emit_header(fw: KernelBase, *, role: int, noc: int, aux: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, role, STATUS_STARTED, noc, SRC_BASE, DST_BASE, SENTINEL, aux,
    0, 0, 0, 0, 0, 0, 0, 0,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  return fw


def emit_status(fw: KernelBase, status: int):
  fw.li(s2, RESULT_BASE)
  fw.li(t0, status)
  fw.sw(t0, s2, 2 * 4)
  return fw


def emit_mcast_write(fw: RectSweepKernel, noc: int, src, dst_lo, dst_coord, length, *,
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


def build_sender(*, noc: int, major: str, rect: mcast.McastRect, packet_bytes: int, path_reserve: bool) -> KernelBase:
  fw = RectSweepKernel()
  emit_header(fw, role=ROLE_SENDER, noc=noc, aux=0)
  fw.local_noc_coord(noc, s5, x_addr=BM.MY_X, y_addr=BM.MY_Y)
  fw.noc_cmd_reg(noc, 0, NOC.TARG_ADDR_COORDINATE, s5, addr=t3, tmp=t4)
  fw.noc_mcast_coord(s9, rect.x0, rect.y0, rect.x1, rect.y1)
  fw.li(s1, SENTINEL)
  fw.li(s2, SRC_BASE + packet_bytes - 4)
  fw.sw(s1, s2, 0)
  fw.fence()
  fw.li(s4, packet_bytes)
  emit_mcast_write(fw, noc, SRC_BASE, DST_BASE, s9, s4, major=major, path_reserve=path_reserve, a=t3, v=t4)
  emit_status(fw, STATUS_DONE)
  return fw.ret()


def build_receiver(*, noc: int, packet_bytes: int, max_polls: int) -> KernelBase:
  fw = RectSweepKernel()
  emit_header(fw, role=ROLE_RECEIVER, noc=noc, aux=max_polls)
  fw.li(s1, SENTINEL)
  fw.li(s2, DST_BASE + packet_bytes - 4)
  fw.li(s0, max_polls)
  fw.mv(s8, zero)
  poll = fw._new_label("rect_poll")
  missed = fw._new_label("rect_missed")
  done = fw._new_label("rect_done")
  fw.label(poll)
  fw.beq(s0, zero, missed)
  fw.lw(t1, s2, 0)
  fw.beq(t1, s1, done)
  fw.addi(s8, s8, 1)
  fw.addi(s0, s0, -1)
  fw.j(poll)
  fw.label(missed)
  fw.li(s8, 0xFFFFFFFF)
  fw.label(done)
  harness.read_wall_clock(fw, a2, a3)
  fw.li(s2, RESULT_BASE)
  fw.sw(s8, s2, HEADER_SIZE)
  fw.sw(a2, s2, HEADER_SIZE + 4)
  fw.sw(a3, s2, HEADER_SIZE + 8)
  emit_status(fw, STATUS_DONE)
  return fw.ret()


class RectSweepProgram:
  def __init__(self, *, noc: int, major: str, source: Core, receivers: tuple[Core, ...],
               physical_rect: mcast.McastRect, packet_bytes: int, max_polls: int, path_reserve: bool):
    self.noc = noc
    self.major = major
    self.source = source
    self.receivers = receivers
    self.physical_rect = physical_rect
    self.packet_bytes = packet_bytes
    self.max_polls = max_polls
    self.path_reserve = path_reserve
    self.name = f"riscv_noc_mcast_rect_sweep:noc{noc}:{major}"

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    empty = KernelBase()
    compiled_cache: dict[int, list] = {}
    per_core_segments = {}
    sender = build_sender(
      noc=self.noc, major=self.major, rect=self.physical_rect,
      packet_bytes=self.packet_bytes, path_reserve=self.path_reserve,
    )
    per_core_segments[self.source] = Program(
      brisc=sender, ncrisc=empty, trisc0=empty, trisc1=empty, trisc2=empty, num_cores=1,
    ).layout(core_xy=self.source, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id, compiled_cache=compiled_cache)
    for receiver in self.receivers:
      receiver_fw = build_receiver(noc=self.noc, packet_bytes=self.packet_bytes, max_polls=self.max_polls)
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


def make_case(x0: int, y0: int, width: int, height: int, *, noc: int, cmap, coord_mode: str) -> Case:
  receivers = tuple(
    (x, y)
    for y in range(y0, y0 + height)
    for x in range(x0, x0 + width)
  )
  logical = mcast.rect_for(receivers)
  physical = mcast.physical_rect_for_noc(receivers, noc=noc, cmap=cmap)
  if coord_mode == "logical":
    encoded = logical
  elif coord_mode == "logical-physical-order":
    encoded = mcast.logical_rect_for_physical_span(receivers, noc=noc, cmap=cmap)
  else:
    encoded = physical
  return Case(logical, physical, encoded, receivers)


def seed_and_clear(device: Device, source: Core, receivers: tuple[Core, ...], packet_bytes: int):
  payload = bytearray(packet_bytes)
  for off in range(0, packet_bytes, 4):
    struct.pack_into("<I", payload, off, 0xE7000000 | off)
  with harness.device_window(device, source) as win:
    for core in sorted({source, *receivers}):
      win.target(core)
      win.write(RESULT_BASE, b"\0" * (HEADER_SIZE + 16))
      if core == source:
        win.write(SRC_BASE, payload)
      else:
        win.write(DST_BASE, b"\0" * packet_bytes)


def read_receiver(device: Device, receiver: Core) -> int:
  with harness.device_window(device, receiver) as win:
    blob = win.read(RESULT_BASE, HEADER_SIZE + 16)
  words = struct.unpack_from("<" + "I" * ((HEADER_SIZE + 16) // 4), blob, 0)
  if words[0] != RESULT_MAGIC or words[1] != ROLE_RECEIVER or words[2] != STATUS_DONE:
    return 0xFFFFFFFE
  return words[HEADER_WORDS]


def main() -> None:
  parser = argparse.ArgumentParser(description="Bounded NoC multicast rectangle sweep.")
  parser.add_argument("--nocs", type=hop_sweep.parse_nocs, default=(1,))
  parser.add_argument("--majors", type=mcast.parse_majors, default=("x", "y"))
  parser.add_argument("--source", type=harness.parse_core, default=(1, 2))
  parser.add_argument("--x0", type=parse_range, default=parse_range("1:6"))
  parser.add_argument("--y0", type=parse_range, default=parse_range("2:7"))
  parser.add_argument("--width", type=int, default=3)
  parser.add_argument("--height", type=int, default=3)
  parser.add_argument("--sizes", type=mcast.parse_sizes, default=mcast.parse_sizes("16384"))
  parser.add_argument("--max-polls", type=int, default=2_000_000)
  parser.add_argument("--path-reserve", action="store_true")
  parser.add_argument(
    "--coord-mode",
    choices=("logical", "logical-physical-order", "physical"),
    default="physical",
    help="coordinate rectangle written into RET_ADDR_COORDINATE",
  )
  args = parser.parse_args()

  lines = [
    "| noc | major | reserve | coord mode | source | logical rect | physical rect | encoded rect | bytes | seen/total | misses |",
    "|---:|---|---:|---|---|---|---|---|---:|---:|---|",
  ]
  with harness.open_device() as device:
    core_set = set(device.cores)
    cmap = mcast.read_tensix_coordinate_map(device)
    if args.source not in core_set:
      raise ValueError(f"source {args.source} is not a program core")
    for noc in args.nocs:
      for major in args.majors:
        for packet_bytes in args.sizes:
          for y0 in range(args.y0[0], args.y0[1] + 1):
            for x0 in range(args.x0[0], args.x0[1] + 1):
              try:
                case = make_case(x0, y0, args.width, args.height, noc=noc, cmap=cmap, coord_mode=args.coord_mode)
              except ValueError:
                continue
              if any(receiver not in core_set for receiver in case.receivers):
                continue
              seed_and_clear(device, args.source, case.receivers, packet_bytes)
              device.run(RectSweepProgram(
                noc=noc,
                major=major,
                source=args.source,
                receivers=case.receivers,
                physical_rect=case.encoded_rect,
                packet_bytes=packet_bytes,
                max_polls=args.max_polls,
                path_reserve=args.path_reserve,
              ))
              polls = {receiver: read_receiver(device, receiver) for receiver in case.receivers}
              misses = [receiver for receiver, value in polls.items() if value in (0xFFFFFFFF, 0xFFFFFFFE)]
              lines.append(
                f"| {noc} | {major} | {int(args.path_reserve)} | {args.coord_mode} | `{args.source[0]},{args.source[1]}` | "
                f"`{case.logical_rect.x0},{case.logical_rect.y0}->{case.logical_rect.x1},{case.logical_rect.y1}` | "
                f"`{case.physical_rect.x0},{case.physical_rect.y0}->{case.physical_rect.x1},{case.physical_rect.y1}` | "
                f"`{case.encoded_rect.x0},{case.encoded_rect.y0}->{case.encoded_rect.x1},{case.encoded_rect.y1}` | "
                f"{packet_bytes} | {len(case.receivers) - len(misses)}/{len(case.receivers)} | "
                f"{' '.join(f'`{x},{y}`' for x, y in misses) if misses else '-'} |"
              )
  print("\n".join(lines))


if __name__ == "__main__":
  main()
