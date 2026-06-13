#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
import riscv_noc_mcast_one_way_latency as mcast  # noqa: E402
import riscv_noc_hop_sweep as hop_sweep  # noqa: E402
from asm import KernelBase
from dsl import s0, s2, s3, s4, s5, s6, s7, s8, t0, t1, t3, t4, zero
from program import DevMsgs, Program, Run, UnicastWrite
from ttk.addrs import Core, noc_xy
from ttk.mailbox import BriscMailbox as BM
from ttk.noc import NOC, Noc
from ttk.tensix import TensixL1


RESULT_BASE = 0x178000
RESULT_MAGIC = 0x434D4350  # "PCMC"
STATUS_STARTED = 0x2C000001
STATUS_DONE = 0x2C00D00D

MCAST_SOURCE = (1, 2)
MCAST_RECEIVERS = (
  (2, 3), (3, 3), (4, 3),
  (2, 4), (3, 4), (4, 4),
  (2, 5), (3, 5), (4, 5),
)


class ContenderKernel(KernelBase, Noc):
  pass


@dataclass(frozen=True)
class ContenderSpec:
  name: str
  source: Core | None
  target: Core | None


CONTENDERS = {
  "none": ContenderSpec("none", None, None),
  "top_x": ContenderSpec("top_x", (2, 2), (5, 2)),
  "col2_y": ContenderSpec("col2_y", (2, 2), (2, 6)),
  "col3_y": ContenderSpec("col3_y", (3, 2), (3, 6)),
  "col4_y": ContenderSpec("col4_y", (4, 2), (4, 6)),
  "row3_x": ContenderSpec("row3_x", (1, 3), (5, 3)),
  "row4_x": ContenderSpec("row4_x", (1, 4), (5, 4)),
  "row5_x": ContenderSpec("row5_x", (1, 5), (5, 5)),
}


def parse_contenders(text: str) -> tuple[str, ...]:
  names = tuple(item.strip() for item in text.split(",") if item.strip())
  bad = [name for name in names if name not in CONTENDERS]
  if bad:
    raise argparse.ArgumentTypeError(f"unknown contender(s): {','.join(bad)}")
  return names


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


def build_contender(noc: int, packets: int, start_delay: int) -> KernelBase:
  fw = ContenderKernel()
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((RESULT_MAGIC, STATUS_STARTED, noc, packets, 0, 0, 0, 0)):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s8,))
  fw.local_noc_coord(noc, s5, x_addr=BM.MY_X, y_addr=BM.MY_Y)
  fw.noc_cmd_reg(noc, 0, NOC.TARG_ADDR_COORDINATE, s5, addr=t3, tmp=t4)
  fw.li(s2, TensixL1.DATA_BUFFER_SPACE_BASE)
  fw.li(s3, TensixL1.DATA_BUFFER_SPACE_BASE)
  fw.li(s4, NOC.MAX_BURST_SIZE)
  emit_counter_read(fw, noc, NOC.NIU_MST_POSTED_WR_REQ_SENT, s7)
  fw.mv(s6, s7)
  if start_delay > 0:
    fw.delay_cycles(start_delay, count=t0)

  fw.li(s0, packets)
  loop = fw._new_label("contender_loop")
  done = fw._new_label("contender_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  fw.noc_write(noc, 0, s2, s3, 0, s8, s4, posted=True, a=t3, v=t4)
  fw.addi(s6, s6, 1)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  emit_wait_counter_at_least(fw, noc, NOC.NIU_MST_POSTED_WR_REQ_SENT, s6, addr=t3, val=t4)
  emit_counter_read(fw, noc, NOC.NIU_MST_POSTED_WR_REQ_SENT, t1)
  fw.li(s2, RESULT_BASE)
  fw.li(t0, STATUS_DONE)
  fw.sw(t0, s2, 1 * 4)
  fw.sw(s7, s2, 4 * 4)
  fw.sw(t1, s2, 5 * 4)
  return fw.ret()


class McastContentionProgram:
  def __init__(
    self,
    *,
    noc: int,
    major: str,
    packet_bytes: int,
    iters: int,
    contender: ContenderSpec,
    contender_packets: int,
    rect: mcast.McastRect,
    start_delay: int,
    inter_delay: int,
  ):
    self.noc = noc
    self.major = major
    self.packet_bytes = packet_bytes
    self.iters = iters
    self.contender = contender
    self.contender_packets = contender_packets
    self.start_delay = start_delay
    self.inter_delay = inter_delay
    self.rect = rect
    self.name = f"riscv_noc_mcast_contention_probe:{contender.name}:noc{noc}:{major}"

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    empty = KernelBase()
    sender = mcast.build_sender(
      self.noc,
      self.packet_bytes,
      self.iters,
      self.start_delay,
      self.inter_delay,
      self.rect,
      self.major,
      False,
    )
    receiver = mcast.build_receiver(self.noc, self.packet_bytes, self.iters)
    compiled_cache: dict[int, list] = {}
    per_core_segments = {
      MCAST_SOURCE: Program(brisc=sender, ncrisc=empty, trisc0=empty, trisc1=empty, trisc2=empty, num_cores=1).layout(
        core_xy=MCAST_SOURCE,
        dispatch_mode=dispatch_mode,
        host_assigned_id=host_assigned_id,
        compiled_cache=compiled_cache,
      )
    }
    recv_program = Program(brisc=receiver, ncrisc=empty, trisc0=empty, trisc1=empty, trisc2=empty, num_cores=1)
    for core in MCAST_RECEIVERS:
      per_core_segments[core] = recv_program.layout(
        core_xy=core,
        dispatch_mode=dispatch_mode,
        host_assigned_id=host_assigned_id,
        compiled_cache=compiled_cache,
      )
    if self.contender.source is not None and self.contender.target is not None:
      contender = build_contender(self.noc, self.contender_packets, self.start_delay)
      contender.rta(lambda _x, _y, target=self.contender.target: [noc_xy(*target)])
      per_core_segments[self.contender.source] = Program(
        brisc=contender,
        ncrisc=empty,
        trisc0=empty,
        trisc1=empty,
        trisc2=empty,
        num_cores=1,
      ).layout(
        core_xy=self.contender.source,
        dispatch_mode=dispatch_mode,
        host_assigned_id=host_assigned_id,
        compiled_cache=compiled_cache,
      )
      per_core_segments.setdefault(
        self.contender.target,
        Program(brisc=empty, ncrisc=empty, trisc0=empty, trisc1=empty, trisc2=empty, num_cores=1).layout(
          core_xy=self.contender.target,
          dispatch_mode=dispatch_mode,
          host_assigned_id=host_assigned_id,
          compiled_cache=compiled_cache,
        ),
      )

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


def seed_payload(packet_bytes: int) -> bytes:
  payload = bytearray(max(packet_bytes, NOC.MAX_BURST_SIZE))
  for off in range(0, len(payload), 4):
    struct.pack_into("<I", payload, off, 0xC5000000 | off)
  return bytes(payload)


def clear_and_seed(device, source: Core, receivers: tuple[Core, ...], contender: ContenderSpec,
                   packet_bytes: int, iters: int):
  payload = seed_payload(packet_bytes)
  active = {source, *receivers}
  if contender.source is not None and contender.target is not None:
    active.add(contender.source)
    active.add(contender.target)
  with harness.device_window(device, source) as win:
    for core in sorted(active):
      win.target(core)
      win.write(mcast.RESULT_BASE, b"\0" * max(mcast.result_size_sender(iters), mcast.result_size_receiver(iters)))
      win.write(RESULT_BASE, b"\0" * 64)
      win.write(TensixL1.DATA_BUFFER_SPACE_BASE, payload)


def contender_delta(device, contender: ContenderSpec) -> int:
  if contender.source is None:
    return 0
  with harness.device_window(device, contender.source) as win:
    blob = win.read(RESULT_BASE, 64)
  words = struct.unpack_from("<" + "I" * 16, blob, 0)
  if words[0] != RESULT_MAGIC or words[1] != STATUS_DONE:
    raise RuntimeError(f"contender {contender.name} did not finish: magic=0x{words[0]:08x} status=0x{words[1]:08x}")
  return (words[5] - words[4]) & 0xFFFFFFFF


def main() -> None:
  parser = argparse.ArgumentParser(description="Infer multicast tree links by adding targeted unicast contention.")
  parser.add_argument("--nocs", type=hop_sweep.parse_nocs, default=(0,))
  parser.add_argument("--majors", type=mcast.parse_majors, default=("x", "y"))
  parser.add_argument("--contenders", type=parse_contenders, default=("none", "top_x", "col2_y", "col3_y", "col4_y", "row3_x", "row4_x", "row5_x"))
  parser.add_argument("--sizes", type=mcast.parse_sizes, default=mcast.parse_sizes("64"))
  parser.add_argument("--iters", type=int, default=16)
  parser.add_argument("--contender-packets", type=int, default=128)
  parser.add_argument("--start-delay", type=int, default=4096)
  parser.add_argument("--inter-delay", type=int, default=2048)
  args = parser.parse_args()
  if args.iters <= 0:
    raise ValueError("--iters must be positive")
  if args.contender_packets <= 0:
    raise ValueError("--contender-packets must be positive")

  all_results: list[mcast.RunResult] = []
  contender_counts: dict[tuple[str, int, str, int], int] = {}
  with harness.open_device() as device:
    core_set = set(device.cores)
    required = {MCAST_SOURCE, *MCAST_RECEIVERS}
    for name in args.contenders:
      spec = CONTENDERS[name]
      if spec.source is not None:
        required.add(spec.source)
        required.add(spec.target)
    missing = sorted(required - core_set)
    if missing:
      raise ValueError(f"required cores are unavailable: {missing}")
    cmap = mcast.read_tensix_coordinate_map(device)
    for noc in args.nocs:
      routes = {receiver: mcast.receiver_route(MCAST_SOURCE, receiver, noc=noc, cmap=cmap) for receiver in MCAST_RECEIVERS}
      rect = mcast.logical_rect_for_physical_span(MCAST_RECEIVERS, noc=noc, cmap=cmap)
      for major in args.majors:
        for contender_name in args.contenders:
          contender = CONTENDERS[contender_name]
          for packet_bytes in args.sizes:
            clear_and_seed(device, MCAST_SOURCE, MCAST_RECEIVERS, contender, packet_bytes, args.iters)
            device.run(McastContentionProgram(
              noc=noc,
              major=major,
              packet_bytes=packet_bytes,
              iters=args.iters,
              contender=contender,
              contender_packets=args.contender_packets,
              rect=rect,
              start_delay=args.start_delay,
              inter_delay=args.inter_delay,
            ))
            all_results.extend(mcast.parse_results(
              device,
              noc=noc,
              case=contender_name,
              major=major,
              source=MCAST_SOURCE,
              receivers=MCAST_RECEIVERS,
              rect=rect,
              routes=routes,
              packet_bytes=packet_bytes,
              iters=args.iters,
            ))
            contender_counts[(contender_name, noc, major, packet_bytes)] = contender_delta(device, contender)

  print(mcast.format_results(all_results))
  print("\n| contender | noc | major | bytes | posted writes sent |")
  print("|---|---:|---|---:|---:|")
  for key, count in contender_counts.items():
    contender_name, noc, major, packet_bytes = key
    print(f"| {contender_name} | {noc} | {major} | {packet_bytes} | {count} |")


if __name__ == "__main__":
  main()
