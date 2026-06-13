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
import riscv_noc_mcast_vc_linked as linked  # noqa: E402
from asm import KernelBase
from device import Device
from dsl import a2, a3, s0, s1, s2, s4, s5, s6, s7, s8, s9, s10, s11, t0, t1, t2, t3, t4, t5, zero
from program import DevMsgs, Program, Run, UnicastWrite
from ttk.addrs import Core, L1_ALIGN
from ttk.mailbox import BriscMailbox as BM
from ttk.noc import NOC, Noc
from ttk.tensix import TensixL1


RESULT_BASE = 0x170000
HEADER_WORDS = 16
HEADER_SIZE = HEADER_WORDS * 4
SAMPLE_WORDS = 4
RESULT_MAGIC = 0x4D4D4354  # "TCMM"
STATUS_STARTED = 0x4D000001
STATUS_DONE = 0x4D00D00D
ROLE_SENDER = 1
ROLE_RECEIVER = 2
SRC_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
DST_BASE = SRC_BASE
SEM_BASE = RESULT_BASE - 0x2000
SLOT_STRIDE = NOC.MAX_BURST_SIZE
SENTINEL_BASE = 0xD7000001
NOC_CMD_BRCST_XY = 1 << 16
ROW_X = (1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14)


class MatmulStyleMcastKernel(KernelBase, Noc):
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
  bad_data: int


def u64(lo: int, hi: int) -> int:
  return lo | (hi << 32)


def parse_counts(text: str) -> tuple[int, ...]:
  counts = tuple(int(item.strip(), 0) for item in text.split(",") if item.strip())
  if not counts or any(count <= 0 for count in counts):
    raise argparse.ArgumentTypeError("expected comma-separated positive receiver counts")
  return counts


def row_receivers(source: Core, count: int) -> tuple[Core, ...]:
  sx, sy = source
  candidates = [(x, sy) for x in ROW_X if x != sx]
  if count > len(candidates):
    raise ValueError(f"row source {source} supports at most {len(candidates)} receivers, got {count}")
  return tuple(candidates[:count])


def result_size(iters: int) -> int:
  return HEADER_SIZE + iters * SAMPLE_WORDS * 4


def emit_header(fw: KernelBase, *, role: int, noc: int, packet_bytes: int, iters: int, chunks: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, role, STATUS_STARTED, noc, packet_bytes, iters, chunks,
    SRC_BASE, DST_BASE, SEM_BASE, SENTINEL_BASE, 0, 0, 0, 0, 0,
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


def emit_mcast_write(fw: MatmulStyleMcastKernel, noc: int, src: int, dst: int, dst_coord, length,
                     *, major: str, path_reserve: bool = True, a=t3, v=t4):
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
  fw.noc_cmd_reg(noc, 0, NOC.RET_ADDR_LO, dst, addr=a, tmp=v)
  fw.noc_cmd_reg(noc, 0, NOC.RET_ADDR_MID, 0, addr=a, tmp=v)
  fw.noc_cmd_reg(noc, 0, NOC.RET_ADDR_COORDINATE, dst_coord, addr=a, tmp=v)
  fw.noc_cmd_reg(noc, 0, NOC.AT_LEN_BE, length, addr=a, tmp=v)
  fw.noc_cmd_reg(noc, 0, NOC.AT_LEN_BE_1, 0, addr=a, tmp=v)
  fw.noc_cmd_reg(noc, 0, NOC.CMD_CTRL, NOC.CTRL_SEND_REQ, addr=a, tmp=v)
  return fw


def build_sender(*, noc: int, major: str, rect: mcast.McastRect, packet_bytes: int,
                 iters: int, chunks: int, include_sem: bool, path_reserve: bool) -> KernelBase:
  fw = MatmulStyleMcastKernel()
  emit_header(fw, role=ROLE_SENDER, noc=noc, packet_bytes=packet_bytes, iters=iters, chunks=chunks)
  fw.local_noc_coord(noc, s5, x_addr=BM.MY_X, y_addr=BM.MY_Y)
  fw.noc_cmd_reg(noc, 0, NOC.TARG_ADDR_COORDINATE, s5, addr=t3, tmp=t4)
  fw.noc_mcast_coord(s9, rect.x0, rect.y0, rect.x1, rect.y1)
  fw.li(s4, packet_bytes)
  fw.li(s10, RESULT_BASE + HEADER_SIZE)
  fw.li(s8, SENTINEL_BASE)
  fw.li(s1, SEM_BASE)
  emit_counter_read(fw, noc, NOC.NIU_MST_NONPOSTED_WR_REQ_SENT, s7)
  fw.mv(s6, s7)
  fw.li(s0, iters)
  loop = fw._new_label("mm_mcast_loop")
  done = fw._new_label("mm_mcast_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  for chunk in range(chunks):
    fw.li(s11, SRC_BASE + chunk * SLOT_STRIDE + packet_bytes - 4)
    fw.sw(s8, s11, 0)
  fw.fence()
  harness.read_wall_clock(fw, a2, a3)
  fw.sw(a2, s10, 0)
  fw.sw(a3, s10, 4)
  for chunk in range(chunks):
    emit_mcast_write(
      fw, noc, SRC_BASE + chunk * SLOT_STRIDE, DST_BASE + chunk * SLOT_STRIDE,
      s9, s4, major=major, path_reserve=path_reserve, a=t3, v=t4,
    )
  fw.addi(s6, s6, chunks)
  fw.noc_nonposted_writes_flushed(noc, s6, addr=t3, val=t4)
  if include_sem:
    fw.li(t0, L1_ALIGN)
    fw.sw(s8, s1, 0)
    emit_mcast_write(fw, noc, s1, s1, s9, t0, major=major, path_reserve=path_reserve, a=t3, v=t4)
    fw.addi(s6, s6, 1)
    fw.noc_nonposted_writes_flushed(noc, s6, addr=t3, val=t4)
  harness.read_wall_clock(fw, a2, a3)
  fw.sw(a2, s10, 8)
  fw.sw(a3, s10, 12)
  fw.addi(s10, s10, SAMPLE_WORDS * 4)
  if include_sem:
    fw.addi(s1, s1, L1_ALIGN)
  fw.addi(s8, s8, 1)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  emit_counter_read(fw, noc, NOC.NIU_MST_NONPOSTED_WR_REQ_SENT, t1)
  fw.li(s2, RESULT_BASE)
  fw.sw(s7, s2, 12 * 4)
  fw.sw(t1, s2, 13 * 4)
  emit_status(fw, STATUS_DONE)
  return fw.ret()


def build_receiver(*, noc: int, packet_bytes: int, iters: int, chunks: int, include_sem: bool) -> KernelBase:
  fw = MatmulStyleMcastKernel()
  emit_header(fw, role=ROLE_RECEIVER, noc=noc, packet_bytes=packet_bytes, iters=iters, chunks=chunks)
  fw.li(s1, SENTINEL_BASE)
  fw.li(s2, SEM_BASE if include_sem else DST_BASE + (chunks - 1) * SLOT_STRIDE + packet_bytes - 4)
  fw.li(s10, RESULT_BASE + HEADER_SIZE)
  fw.mv(s8, zero)
  fw.mv(s7, zero)
  fw.li(s0, iters)
  outer = fw._new_label("mm_recv_outer")
  poll = fw._new_label("mm_recv_poll")
  seen = fw._new_label("mm_recv_seen")
  good = fw._new_label("mm_recv_good")
  done = fw._new_label("mm_recv_done")
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
  fw.li(t2, DST_BASE + (chunks - 1) * SLOT_STRIDE + packet_bytes - 4)
  fw.lw(t1, t2, 0)
  fw.beq(t1, s1, good)
  fw.addi(s7, s7, 1)
  fw.label(good)
  fw.sw(t1, s10, 8)
  fw.addi(s10, s10, SAMPLE_WORDS * 4)
  if include_sem:
    fw.addi(s2, s2, L1_ALIGN)
  fw.addi(s1, s1, 1)
  fw.addi(s0, s0, -1)
  fw.j(outer)
  fw.label(done)
  fw.li(s2, RESULT_BASE)
  fw.sw(s8, s2, 12 * 4)
  fw.sw(s7, s2, 13 * 4)
  emit_status(fw, STATUS_DONE)
  return fw.ret()


class MatmulStyleMcastProgram:
  def __init__(self, *, noc: int, major: str, source: Core, receivers: tuple[Core, ...],
               rect: mcast.McastRect, packet_bytes: int, iters: int, chunks: int,
               include_sem: bool, path_reserve: bool):
    self.noc = noc
    self.major = major
    self.source = source
    self.receivers = receivers
    self.rect = rect
    self.packet_bytes = packet_bytes
    self.iters = iters
    self.chunks = chunks
    self.include_sem = include_sem
    self.path_reserve = path_reserve
    self.name = f"riscv_noc_mcast_matmul_style:noc{noc}:{major}:c{chunks}"

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    empty = KernelBase()
    compiled_cache: dict[int, list] = {}
    per_core_segments = {}
    sender = build_sender(
      noc=self.noc, major=self.major, rect=self.rect, packet_bytes=self.packet_bytes,
      iters=self.iters, chunks=self.chunks, include_sem=self.include_sem,
      path_reserve=self.path_reserve,
    )
    per_core_segments[self.source] = Program(
      brisc=sender, ncrisc=empty, trisc0=empty, trisc1=empty, trisc2=empty, num_cores=1,
    ).layout(core_xy=self.source, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id, compiled_cache=compiled_cache)
    for receiver in self.receivers:
      receiver_fw = build_receiver(
        noc=self.noc, packet_bytes=self.packet_bytes, iters=self.iters,
        chunks=self.chunks, include_sem=self.include_sem,
      )
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


def seed_payload(packet_bytes: int, chunks: int) -> bytes:
  payload = bytearray(chunks * SLOT_STRIDE)
  for chunk in range(chunks):
    base = chunk * SLOT_STRIDE
    for off in range(0, packet_bytes, 4):
      struct.pack_into("<I", payload, base + off, 0xD5000000 | (chunk << 16) | off)
  return bytes(payload)


def clear_and_seed(device: Device, source: Core, receivers: tuple[Core, ...], packet_bytes: int, chunks: int, iters: int):
  payload = seed_payload(packet_bytes, chunks)
  active = sorted({source, *receivers})
  with harness.device_window(device, source) as win:
    for core in active:
      win.target(core)
      win.write(RESULT_BASE, b"\0" * result_size(iters))
      win.write(SEM_BASE, b"\0" * (iters * L1_ALIGN))
      win.write(SRC_BASE, payload if core == source else b"\0" * len(payload))


def read_words(device: Device, core: Core, iters: int) -> tuple[int, ...]:
  with harness.device_window(device, core) as win:
    blob = win.read(RESULT_BASE, result_size(iters))
  return struct.unpack_from("<" + "I" * (len(blob) // 4), blob, 0)


def parse_sender(device: Device, source: Core, iters: int) -> SenderResult:
  words = read_words(device, source, iters)
  if words[0] != RESULT_MAGIC or words[1] != ROLE_SENDER or words[2] != STATUS_DONE:
    raise RuntimeError(f"sender {source} bad status magic=0x{words[0]:08x} role={words[1]} status=0x{words[2]:08x}")
  issue = []
  sent = []
  for i in range(iters):
    base = HEADER_WORDS + i * SAMPLE_WORDS
    issue.append(u64(words[base], words[base + 1]))
    sent.append(u64(words[base + 2], words[base + 3]))
  return SenderResult(issue, sent, (words[13] - words[12]) & 0xFFFFFFFF)


def parse_receiver(device: Device, receiver: Core, iters: int) -> ReceiverResult:
  words = read_words(device, receiver, iters)
  if words[0] != RESULT_MAGIC or words[1] != ROLE_RECEIVER or words[2] != STATUS_DONE:
    raise RuntimeError(f"receiver {receiver} bad status magic=0x{words[0]:08x} role={words[1]} status=0x{words[2]:08x}")
  seen = []
  for i in range(iters):
    base = HEADER_WORDS + i * SAMPLE_WORDS
    seen.append(u64(words[base], words[base + 1]))
  return ReceiverResult(receiver, seen, words[12], words[13])


def format_row(*, noc: int, major: str, receivers: tuple[Core, ...], rect: mcast.McastRect,
               packet_bytes: int, iters: int, chunks: int, include_sem: bool, path_reserve: bool,
               sender: SenderResult, receiver_results: list[ReceiverResult]) -> str:
  payload_reqs = iters * chunks
  total_reqs = payload_reqs + (iters if include_sem else 0)
  source_bytes = payload_reqs * packet_bytes
  delivered_bytes = source_bytes * len(receivers)
  source_window = max(sender.sent) - min(sender.issue)
  receiver_last = [r.seen[-1] for r in receiver_results]
  receiver_window = max(receiver_last) - min(sender.issue)
  source_bpc = source_bytes / source_window if source_window > 0 else 0.0
  delivered_bpc = delivered_bytes / receiver_window if receiver_window > 0 else 0.0
  req_cyc = total_reqs / source_window if source_window > 0 else 0.0
  first_seen = [r.seen[0] for r in receiver_results]
  avg_first = statistics.fmean([seen - sender.issue[0] for seen in first_seen])
  avg_last = statistics.fmean([seen - sender.issue[0] for seen in receiver_last])
  bad_counter = int(sender.counter_delta != total_reqs)
  bad_data = sum(r.bad_data for r in receiver_results)
  max_polls = max((r.poll_iters for r in receiver_results), default=0)
  return (
    f"| {noc} | {major} | {int(path_reserve)} | {int(include_sem)} | {len(receivers)} | "
    f"`{rect.x0},{rect.y0}->{rect.x1},{rect.y1}` | {packet_bytes} | {iters} | {chunks} | "
    f"{source_bpc:.3f} | {delivered_bpc:.3f} | {req_cyc:.5f} | "
    f"{avg_first:.1f} | {avg_last:.1f} | {bad_counter} | {bad_data} | {max_polls} |"
  )


def main() -> None:
  parser = argparse.ArgumentParser(description="Matmul-style unlinked mcast payload + semaphore benchmark.")
  parser.add_argument("--nocs", type=hop_sweep.parse_nocs, default=(0, 1))
  parser.add_argument("--majors", type=mcast.parse_majors, default=("x", "y"))
  parser.add_argument("--source", type=harness.parse_core, default=(1, 4))
  parser.add_argument("--counts", type=parse_counts, default=parse_counts("1,2,4,8,11"))
  parser.add_argument("--sizes", type=mcast.parse_sizes, default=mcast.parse_sizes("16384"))
  parser.add_argument("--iters", type=int, default=128)
  parser.add_argument("--chunks", type=linked.parse_depths, default=linked.parse_depths("1,4,8"))
  parser.add_argument("--no-sem", action="store_true", help="skip the matmul completion semaphore")
  parser.add_argument("--no-path-reserve", action="store_true", help="clear CMD_PATH_RESERVE on payload and semaphore mcasts")
  args = parser.parse_args()
  if args.iters <= 0:
    raise ValueError("--iters must be positive")
  if SEM_BASE + args.iters * L1_ALIGN > RESULT_BASE:
    raise ValueError(f"--iters {args.iters} needs too many semaphore slots before RESULT_BASE")
  include_sem = not args.no_sem
  path_reserve = not args.no_path_reserve
  lines = [
    "| noc | major | path reserve | sem | dests | rect | packet B | iters | chunks | source payload B/cyc | delivered payload B/cyc | total req/cyc | avg first done cyc | avg last done cyc | bad counter | bad data | max recv polls |",
    "|---:|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
  ]
  with harness.open_device() as device:
    core_set = set(device.cores)
    if args.source not in core_set:
      raise ValueError(f"source {args.source} is not a program core")
    cmap = mcast.read_tensix_coordinate_map(device)
    for count in args.counts:
      receivers = row_receivers(args.source, count)
      missing = sorted(set(receivers) - core_set)
      if missing:
        raise ValueError(f"unavailable receivers for count {count}: {missing}")
      for noc in args.nocs:
        rect = mcast.logical_rect_for_physical_span(receivers, noc=noc, cmap=cmap)
        for major in args.majors:
          for packet_bytes in args.sizes:
            for chunks in args.chunks:
              if SRC_BASE + chunks * SLOT_STRIDE > SEM_BASE:
                raise ValueError(f"chunks {chunks} exceeds scratch space before SEM_BASE")
              clear_and_seed(device, args.source, receivers, packet_bytes, chunks, args.iters)
              device.run(MatmulStyleMcastProgram(
                noc=noc, major=major, source=args.source, receivers=receivers,
                rect=rect, packet_bytes=packet_bytes, iters=args.iters,
                chunks=chunks, include_sem=include_sem, path_reserve=path_reserve,
              ))
              sender = parse_sender(device, args.source, args.iters)
              receiver_results = [parse_receiver(device, receiver, args.iters) for receiver in receivers]
              lines.append(format_row(
                noc=noc, major=major, receivers=receivers, rect=rect,
                packet_bytes=packet_bytes, iters=args.iters, chunks=chunks,
                include_sem=include_sem, path_reserve=path_reserve,
                sender=sender, receiver_results=receiver_results,
              ))
  print("\n".join(lines))


if __name__ == "__main__":
  main()
