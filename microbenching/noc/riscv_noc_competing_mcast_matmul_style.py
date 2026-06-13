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
from dsl import a2, a3, s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, t0, t1, t2, t3, t4, zero
from program import DevMsgs, Program, Run, UnicastWrite
from ttk.addrs import Core, L1_ALIGN
from ttk.mailbox import BriscMailbox as BM
from ttk.noc import NOC, Noc
from ttk.tensix import TensixL1


RESULT_BASE = 0x170000
HEADER_WORDS = 16
HEADER_SIZE = HEADER_WORDS * 4
SAMPLE_WORDS = 4
RESULT_MAGIC = 0x434D4354  # "TCMC"
STATUS_STARTED = 0xC0010001
STATUS_DONE = 0xC001D00D
ROLE_SENDER = 1
ROLE_RECEIVER = 2
SRC_A = TensixL1.DATA_BUFFER_SPACE_BASE
DST_A = SRC_A
SRC_B = 0x90000
DST_B = SRC_B
SEM_A = RESULT_BASE - 0x10000
SEM_B = RESULT_BASE - 0x8000
SLOT_STRIDE = NOC.MAX_BURST_SIZE
SENTINEL_A = 0xDA000001
SENTINEL_B = 0xDB000001
MASK_A = 1
MASK_B = 2
NOC_CMD_BRCST_XY = 1 << 16


class CompetingMcastKernel(KernelBase, Noc):
  pass


@dataclass(frozen=True)
class StreamSpec:
  name: str
  source: Core
  receivers: tuple[Core, ...]
  src_base: int
  dst_base: int
  sem_base: int
  sentinel: int
  mask: int


@dataclass(frozen=True)
class CaseSpec:
  name: str
  a: StreamSpec
  b: StreamSpec


@dataclass(frozen=True)
class SenderResult:
  stream: str
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
  bad_data: int


def stream_a(receivers: tuple[Core, ...] = ((2, 3), (3, 3), (4, 3), (5, 3),
                                           (2, 4), (3, 4), (4, 4), (5, 4),
                                           (2, 5), (3, 5), (4, 5), (5, 5),
                                           (2, 6), (3, 6), (4, 6), (5, 6))) -> StreamSpec:
  return StreamSpec("a", (1, 2), receivers, SRC_A, DST_A, SEM_A, SENTINEL_A, MASK_A)


def stream_b(receivers: tuple[Core, ...]) -> StreamSpec:
  return StreamSpec("b", (10, 2), receivers, SRC_B, DST_B, SEM_B, SENTINEL_B, MASK_B)


CASES = {
  "disjoint": CaseSpec(
    "disjoint",
    stream_a(),
    stream_b(((11, 3), (12, 3), (13, 3), (14, 3),
              (11, 4), (12, 4), (13, 4), (14, 4),
              (11, 5), (12, 5), (13, 5), (14, 5),
              (11, 6), (12, 6), (13, 6), (14, 6))),
  ),
  "adjacent": CaseSpec(
    "adjacent",
    stream_a(),
    stream_b(((6, 3), (7, 3), (10, 3), (11, 3),
              (6, 4), (7, 4), (10, 4), (11, 4),
              (6, 5), (7, 5), (10, 5), (11, 5),
              (6, 6), (7, 6), (10, 6), (11, 6))),
  ),
  "overlap": CaseSpec(
    "overlap",
    stream_a(),
    stream_b(((4, 5), (5, 5), (6, 5), (7, 5),
              (4, 6), (5, 6), (6, 6), (7, 6),
              (4, 7), (5, 7), (6, 7), (7, 7),
              (4, 8), (5, 8), (6, 8), (7, 8))),
  ),
  "nested": CaseSpec(
    "nested",
    stream_a(),
    stream_b(((3, 4), (4, 4),
              (3, 5), (4, 5))),
  ),
  "same_rect": CaseSpec(
    "same_rect",
    stream_a(),
    stream_b(stream_a().receivers),
  ),
}


def u64(lo: int, hi: int) -> int:
  return lo | (hi << 32)


def parse_cases(text: str) -> tuple[str, ...]:
  out = tuple(item.strip() for item in text.split(",") if item.strip())
  bad = [name for name in out if name not in CASES]
  if bad:
    raise argparse.ArgumentTypeError(f"unknown case(s): {','.join(bad)}")
  return out


def parse_ints(text: str) -> tuple[int, ...]:
  out = tuple(int(item.strip(), 0) for item in text.split(",") if item.strip())
  if not out or any(item <= 0 for item in out):
    raise argparse.ArgumentTypeError("expected comma-separated positive integers")
  return out


def active_cores(case: CaseSpec) -> list[Core]:
  return sorted({case.a.source, case.b.source, *case.a.receivers, *case.b.receivers})


def receiver_mask(case: CaseSpec, core: Core) -> int:
  mask = 0
  if core in case.a.receivers:
    mask |= MASK_A
  if core in case.b.receivers:
    mask |= MASK_B
  return mask


def result_size(iters: int) -> int:
  return HEADER_SIZE + iters * SAMPLE_WORDS * 4


def summarize(values: list[int]) -> str:
  if not values:
    return "-"
  return f"min={min(values)} avg={statistics.fmean(values):.1f} med={statistics.median(values):.1f} max={max(values)}"


def emit_header(fw: KernelBase, *, role: int, noc: int, stream_mask: int, packet_bytes: int, iters: int, chunks: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, role, STATUS_STARTED, noc, stream_mask, packet_bytes, iters, chunks,
    SRC_A, SRC_B, SEM_A, SEM_B, 0, 0, 0, 0,
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


def emit_mcast_write(fw: CompetingMcastKernel, noc: int, src: int, dst: int, dst_coord, length,
                     *, major: str, path_reserve: bool, a=t3, v=t4):
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


def build_sender(*, stream: StreamSpec, noc: int, major: str, rect: mcast.McastRect,
                 packet_bytes: int, iters: int, chunks: int, path_reserve: bool, start_delay: int) -> KernelBase:
  fw = CompetingMcastKernel()
  emit_header(fw, role=ROLE_SENDER, noc=noc, stream_mask=stream.mask, packet_bytes=packet_bytes, iters=iters, chunks=chunks)
  fw.local_noc_coord(noc, s5, x_addr=BM.MY_X, y_addr=BM.MY_Y)
  fw.noc_cmd_reg(noc, 0, NOC.TARG_ADDR_COORDINATE, s5, addr=t3, tmp=t4)
  fw.noc_mcast_coord(s9, rect.x0, rect.y0, rect.x1, rect.y1)
  fw.li(s4, packet_bytes)
  fw.li(s10, RESULT_BASE + HEADER_SIZE)
  fw.li(s8, stream.sentinel)
  fw.li(s1, stream.sem_base)
  emit_counter_read(fw, noc, NOC.NIU_MST_NONPOSTED_WR_REQ_SENT, s7)
  fw.mv(s6, s7)
  if start_delay > 0:
    fw.delay_cycles(start_delay, count=t0)
  fw.li(s0, iters)
  loop = fw._new_label("comp_mcast_loop")
  done = fw._new_label("comp_mcast_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  for chunk in range(chunks):
    fw.li(s11, stream.src_base + chunk * SLOT_STRIDE + packet_bytes - 4)
    fw.sw(s8, s11, 0)
  fw.fence()
  harness.read_wall_clock(fw, a2, a3)
  fw.sw(a2, s10, 0)
  fw.sw(a3, s10, 4)
  for chunk in range(chunks):
    emit_mcast_write(
      fw, noc, stream.src_base + chunk * SLOT_STRIDE, stream.dst_base + chunk * SLOT_STRIDE,
      s9, s4, major=major, path_reserve=path_reserve, a=t3, v=t4,
    )
  fw.addi(s6, s6, chunks)
  fw.noc_nonposted_writes_flushed(noc, s6, addr=t3, val=t4)
  fw.li(t0, L1_ALIGN)
  fw.sw(s8, s1, 0)
  emit_mcast_write(fw, noc, s1, s1, s9, t0, major=major, path_reserve=path_reserve, a=t3, v=t4)
  fw.addi(s6, s6, 1)
  fw.noc_nonposted_writes_flushed(noc, s6, addr=t3, val=t4)
  harness.read_wall_clock(fw, a2, a3)
  fw.sw(a2, s10, 8)
  fw.sw(a3, s10, 12)
  fw.addi(s10, s10, SAMPLE_WORDS * 4)
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


def build_receiver(*, mask: int, noc: int, packet_bytes: int, iters: int, chunks: int) -> KernelBase:
  fw = CompetingMcastKernel()
  emit_header(fw, role=ROLE_RECEIVER, noc=noc, stream_mask=mask, packet_bytes=packet_bytes, iters=iters, chunks=chunks)
  fw.li(s1, SENTINEL_A)
  fw.li(s2, SEM_A)
  fw.li(s3, SENTINEL_B)
  fw.li(s4, SEM_B)
  fw.li(s10, RESULT_BASE + HEADER_SIZE)
  fw.mv(s8, zero)
  fw.mv(s7, zero)
  fw.li(s0, iters)
  outer = fw._new_label("comp_recv_outer")
  done = fw._new_label("comp_recv_done")
  fw.label(outer)
  fw.beq(s0, zero, done)

  if mask == MASK_A:
    poll_a = fw._new_label("comp_poll_a")
    seen_a = fw._new_label("comp_seen_a")
    good_a = fw._new_label("comp_good_a")
    fw.label(poll_a)
    fw.lw(t1, s2, 0)
    fw.beq(t1, s1, seen_a)
    fw.addi(s8, s8, 1)
    fw.j(poll_a)
    fw.label(seen_a)
    harness.read_wall_clock(fw, a2, a3)
    fw.sw(a2, s10, 0)
    fw.sw(a3, s10, 4)
    fw.sw(zero, s10, 8)
    fw.sw(zero, s10, 12)
    fw.li(t2, DST_A + (chunks - 1) * SLOT_STRIDE + packet_bytes - 4)
    fw.lw(t1, t2, 0)
    fw.bgeu(t1, s1, good_a)
    fw.addi(s7, s7, 1)
    fw.label(good_a)
  elif mask == MASK_B:
    poll_b = fw._new_label("comp_poll_b")
    seen_b = fw._new_label("comp_seen_b")
    good_b = fw._new_label("comp_good_b")
    fw.label(poll_b)
    fw.lw(t1, s4, 0)
    fw.beq(t1, s3, seen_b)
    fw.addi(s8, s8, 1)
    fw.j(poll_b)
    fw.label(seen_b)
    fw.sw(zero, s10, 0)
    fw.sw(zero, s10, 4)
    harness.read_wall_clock(fw, a2, a3)
    fw.sw(a2, s10, 8)
    fw.sw(a3, s10, 12)
    fw.li(t2, DST_B + (chunks - 1) * SLOT_STRIDE + packet_bytes - 4)
    fw.lw(t1, t2, 0)
    fw.bgeu(t1, s3, good_b)
    fw.addi(s7, s7, 1)
    fw.label(good_b)
  elif mask == (MASK_A | MASK_B):
    fw.mv(s5, zero)
    fw.mv(s6, zero)
    poll = fw._new_label("comp_poll_ab")
    check_b = fw._new_label("comp_check_b")
    maybe_done = fw._new_label("comp_maybe_done")
    seen_both = fw._new_label("comp_seen_both")
    good_a = fw._new_label("comp_good_ab_a")
    good_b = fw._new_label("comp_good_ab_b")
    fw.label(poll)
    fw.bne(s5, zero, check_b)
    fw.lw(t1, s2, 0)
    fw.bne(t1, s1, check_b)
    harness.read_wall_clock(fw, a2, a3)
    fw.sw(a2, s10, 0)
    fw.sw(a3, s10, 4)
    fw.li(s5, 1)
    fw.li(t2, DST_A + (chunks - 1) * SLOT_STRIDE + packet_bytes - 4)
    fw.lw(t1, t2, 0)
    fw.bgeu(t1, s1, good_a)
    fw.addi(s7, s7, 1)
    fw.label(good_a)
    fw.label(check_b)
    fw.bne(s6, zero, maybe_done)
    fw.lw(t1, s4, 0)
    fw.bne(t1, s3, maybe_done)
    harness.read_wall_clock(fw, a2, a3)
    fw.sw(a2, s10, 8)
    fw.sw(a3, s10, 12)
    fw.li(s6, 1)
    fw.li(t2, DST_B + (chunks - 1) * SLOT_STRIDE + packet_bytes - 4)
    fw.lw(t1, t2, 0)
    fw.bgeu(t1, s3, good_b)
    fw.addi(s7, s7, 1)
    fw.label(good_b)
    fw.label(maybe_done)
    fw.and_(t1, s5, s6)
    fw.bne(t1, zero, seen_both)
    fw.addi(s8, s8, 1)
    fw.j(poll)
    fw.label(seen_both)
  else:
    raise ValueError(f"bad receiver mask {mask}")

  fw.addi(s10, s10, SAMPLE_WORDS * 4)
  fw.addi(s2, s2, L1_ALIGN)
  fw.addi(s4, s4, L1_ALIGN)
  fw.addi(s1, s1, 1)
  fw.addi(s3, s3, 1)
  fw.addi(s0, s0, -1)
  fw.j(outer)
  fw.label(done)
  fw.li(s2, RESULT_BASE)
  fw.sw(s8, s2, 12 * 4)
  fw.sw(s7, s2, 13 * 4)
  emit_status(fw, STATUS_DONE)
  return fw.ret()


class CompetingMcastProgram:
  def __init__(self, *, case: CaseSpec, noc: int, major: str, rects: dict[str, mcast.McastRect],
               packet_bytes: int, iters: int, chunks: int, path_reserve: int, start_gap: int):
    self.case = case
    self.noc = noc
    self.major = major
    self.rects = rects
    self.packet_bytes = packet_bytes
    self.iters = iters
    self.chunks = chunks
    self.path_reserve_a = bool(path_reserve & MASK_A)
    self.path_reserve_b = bool(path_reserve & MASK_B)
    self.start_gap = start_gap
    self.name = f"riscv_noc_competing_mcast:{case.name}:noc{noc}:{major}:pr{path_reserve}"

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    empty = KernelBase()
    compiled_cache: dict[int, list] = {}
    per_core_segments = {}
    owned_kernels = [empty]
    for stream, delay in ((self.case.a, 0), (self.case.b, self.start_gap)):
      stream_path_reserve = self.path_reserve_a if stream.name == "a" else self.path_reserve_b
      sender = build_sender(
        stream=stream, noc=self.noc, major=self.major, rect=self.rects[stream.name],
        packet_bytes=self.packet_bytes, iters=self.iters, chunks=self.chunks,
        path_reserve=stream_path_reserve, start_delay=delay,
      )
      owned_kernels.append(sender)
      per_core_segments[stream.source] = Program(
        brisc=sender, ncrisc=empty, trisc0=empty, trisc1=empty, trisc2=empty, num_cores=1,
      ).layout(core_xy=stream.source, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id, compiled_cache=compiled_cache)

    for receiver in sorted({*self.case.a.receivers, *self.case.b.receivers}):
      receiver_fw = build_receiver(
        mask=receiver_mask(self.case, receiver), noc=self.noc,
        packet_bytes=self.packet_bytes, iters=self.iters, chunks=self.chunks,
      )
      owned_kernels.append(receiver_fw)
      per_core_segments[receiver] = Program(
        brisc=receiver_fw, ncrisc=empty, trisc0=empty, trisc1=empty, trisc2=empty, num_cores=1,
      ).layout(core_xy=receiver, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id, compiled_cache=compiled_cache)

    active = active_cores(self.case)
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


def seed_payload(packet_bytes: int, chunks: int, tag: int) -> bytes:
  payload = bytearray(chunks * SLOT_STRIDE)
  for chunk in range(chunks):
    base = chunk * SLOT_STRIDE
    for off in range(0, packet_bytes, 4):
      struct.pack_into("<I", payload, base + off, tag | (chunk << 16) | off)
  return bytes(payload)


def clear_and_seed(device: Device, case: CaseSpec, packet_bytes: int, chunks: int, iters: int):
  payload_a = seed_payload(packet_bytes, chunks, 0xD0A00000)
  payload_b = seed_payload(packet_bytes, chunks, 0xD0B00000)
  zero_payload = b"\0" * (chunks * SLOT_STRIDE)
  with harness.device_window(device, case.a.source) as win:
    for core in active_cores(case):
      win.target(core)
      win.write(RESULT_BASE, b"\0" * result_size(iters))
      win.write(SEM_A, b"\0" * (iters * L1_ALIGN))
      win.write(SEM_B, b"\0" * (iters * L1_ALIGN))
      win.write(SRC_A, payload_a if core == case.a.source else zero_payload)
      win.write(SRC_B, payload_b if core == case.b.source else zero_payload)


def read_words(device: Device, core: Core, iters: int) -> tuple[int, ...]:
  with harness.device_window(device, core) as win:
    blob = win.read(RESULT_BASE, result_size(iters))
  return struct.unpack_from("<" + "I" * (len(blob) // 4), blob, 0)


def parse_sender(device: Device, stream: StreamSpec, iters: int) -> SenderResult:
  words = read_words(device, stream.source, iters)
  if words[0] != RESULT_MAGIC or words[1] != ROLE_SENDER or words[2] != STATUS_DONE:
    raise RuntimeError(f"sender {stream.name}@{stream.source} bad status magic=0x{words[0]:08x} role={words[1]} status=0x{words[2]:08x}")
  issue = []
  sent = []
  for i in range(iters):
    base = HEADER_WORDS + i * SAMPLE_WORDS
    issue.append(u64(words[base], words[base + 1]))
    sent.append(u64(words[base + 2], words[base + 3]))
  return SenderResult(stream.name, issue, sent, (words[13] - words[12]) & 0xFFFFFFFF)


def parse_receiver(device: Device, case: CaseSpec, receiver: Core, iters: int) -> ReceiverResult:
  words = read_words(device, receiver, iters)
  if words[0] != RESULT_MAGIC or words[1] != ROLE_RECEIVER or words[2] != STATUS_DONE:
    raise RuntimeError(f"receiver {receiver} bad status magic=0x{words[0]:08x} role={words[1]} status=0x{words[2]:08x}")
  seen_a = []
  seen_b = []
  for i in range(iters):
    base = HEADER_WORDS + i * SAMPLE_WORDS
    seen_a.append(u64(words[base], words[base + 1]))
    seen_b.append(u64(words[base + 2], words[base + 3]))
  return ReceiverResult(receiver, receiver_mask(case, receiver), seen_a, seen_b, words[12], words[13])


def stream_receiver_results(stream: StreamSpec, receivers: list[ReceiverResult]) -> list[ReceiverResult]:
  return [receiver for receiver in receivers if receiver.mask & stream.mask]


def format_stream_row(*, case: str, repeat: int, noc: int, major: str, path_reserve: str, stream: StreamSpec,
                      rect: mcast.McastRect, packet_bytes: int, iters: int, chunks: int,
                      sender: SenderResult, receivers: list[ReceiverResult]) -> str:
  participating = stream_receiver_results(stream, receivers)
  seen_lists = [r.seen_a if stream.mask == MASK_A else r.seen_b for r in participating]
  last_seen = [seen[-1] for seen in seen_lists]
  source_bytes = iters * chunks * packet_bytes
  delivered_bytes = source_bytes * len(participating)
  source_window = max(sender.sent) - min(sender.issue)
  receiver_window = max(last_seen) - min(sender.issue) if last_seen else 0
  source_bpc = source_bytes / source_window if source_window > 0 else 0.0
  delivered_bpc = delivered_bytes / receiver_window if receiver_window > 0 else 0.0
  total_reqs = iters * (chunks + 1)
  bad_counter = int(sender.counter_delta != total_reqs)
  bad_data = sum(r.bad_data for r in participating)
  max_polls = max((r.poll_iters for r in participating), default=0)
  lags = [seen - issue for seen_list in seen_lists for seen, issue in zip(seen_list, sender.issue)]
  return (
    f"| {case} | {repeat} | {noc} | {major} | {path_reserve} | {stream.name} | "
    f"`{rect.x0},{rect.y0}->{rect.x1},{rect.y1}` | {len(participating)} | "
    f"{packet_bytes} | {iters} | {chunks} | {source_bpc:.3f} | {delivered_bpc:.3f} | "
    f"{summarize(lags)} | {bad_counter} | {bad_data} | {max_polls} |"
  )


def format_aggregate_row(*, case: str, repeat: int, noc: int, major: str, path_reserve: str,
                         packet_bytes: int, iters: int, chunks: int,
                         senders: dict[str, SenderResult], receivers: list[ReceiverResult]) -> str:
  first_issue = min(min(sender.issue) for sender in senders.values())
  last_seen = []
  delivered_bytes = 0
  for stream_name, stream_mask in (("a", MASK_A), ("b", MASK_B)):
    for receiver in receivers:
      if receiver.mask & stream_mask:
        seen = receiver.seen_a if stream_name == "a" else receiver.seen_b
        last_seen.append(seen[-1])
        delivered_bytes += iters * chunks * packet_bytes
  window = max(last_seen) - first_issue if last_seen else 0
  delivered_bpc = delivered_bytes / window if window > 0 else 0.0
  return f"| {case} | {repeat} | {noc} | {major} | {path_reserve} | all | - | - | {packet_bytes} | {iters} | {chunks} | - | {delivered_bpc:.3f} | - | - | - | - |"


def main() -> None:
  parser = argparse.ArgumentParser(description="Matmul-style competing multicast rectangle benchmark.")
  parser.add_argument("--cases", type=parse_cases, default=parse_cases("disjoint,adjacent,overlap,nested"))
  parser.add_argument("--nocs", type=hop_sweep.parse_nocs, default=(0, 1))
  parser.add_argument("--majors", type=mcast.parse_majors, default=("x", "y"))
  parser.add_argument("--sizes", type=mcast.parse_sizes, default=mcast.parse_sizes("16384"))
  parser.add_argument("--iters", type=int, default=64)
  parser.add_argument("--repeats", type=int, default=1, help="repeat each case in the same Device() instance")
  parser.add_argument("--chunks", type=parse_ints, default=parse_ints("1,4"))
  parser.add_argument("--start-gap", type=int, default=0, help="delay stream B by this many cycles")
  parser.add_argument(
    "--path-reserve-mode",
    choices=("both", "a", "b", "none"),
    default=None,
    help="select which stream uses CMD_PATH_RESERVE; overrides --no-path-reserve",
  )
  parser.add_argument("--no-path-reserve", action="store_true")
  args = parser.parse_args()
  if args.iters <= 0:
    raise ValueError("--iters must be positive")
  if args.repeats <= 0:
    raise ValueError("--repeats must be positive")
  if SEM_B + args.iters * L1_ALIGN > RESULT_BASE:
    raise ValueError(f"--iters {args.iters} needs too many semaphore slots before RESULT_BASE")
  if args.path_reserve_mode is None:
    path_reserve_mask = MASK_A | MASK_B if not args.no_path_reserve else 0
  else:
    path_reserve_mask = {
      "both": MASK_A | MASK_B,
      "a": MASK_A,
      "b": MASK_B,
      "none": 0,
    }[args.path_reserve_mode]
  path_reserve_label = {
    MASK_A | MASK_B: "both",
    MASK_A: "a",
    MASK_B: "b",
    0: "none",
  }[path_reserve_mask]
  lines = [
    "| case | repeat | noc | major | path reserve | stream | rect | dests | packet B | iters | chunks | source payload B/cyc | delivered payload B/cyc | seen-issue cyc | bad counter | stale data | max polls |",
    "|---|---:|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|",
  ]
  with harness.open_device() as device:
    core_set = set(device.cores)
    cmap = mcast.read_tensix_coordinate_map(device)
    for case_name in args.cases:
      case = CASES[case_name]
      missing = sorted(set(active_cores(case)) - core_set)
      if missing:
        raise ValueError(f"case {case.name}: unavailable cores {missing}")
      for noc in args.nocs:
        rects = {
          case.a.name: mcast.logical_rect_for_physical_span(case.a.receivers, noc=noc, cmap=cmap),
          case.b.name: mcast.logical_rect_for_physical_span(case.b.receivers, noc=noc, cmap=cmap),
        }
        for major in args.majors:
          for packet_bytes in args.sizes:
            for chunks in args.chunks:
              if SRC_B + chunks * SLOT_STRIDE > SEM_A:
                raise ValueError(f"chunks {chunks} exceeds scratch space before SEM_A")
              for repeat in range(args.repeats):
                clear_and_seed(device, case, packet_bytes, chunks, args.iters)
                try:
                  device.run(CompetingMcastProgram(
                    case=case, noc=noc, major=major, rects=rects,
                    packet_bytes=packet_bytes, iters=args.iters, chunks=chunks,
                    path_reserve=path_reserve_mask, start_gap=args.start_gap,
                  ))
                except TimeoutError as exc:
                  if len(lines) > 2:
                    print("\n".join(lines), flush=True)
                  raise TimeoutError(
                    f"repeat {repeat}: case={case.name} noc={noc} major={major} "
                    f"path_reserve={path_reserve_label} packet_bytes={packet_bytes} chunks={chunks}: {exc}"
                  ) from exc
                senders = {
                  "a": parse_sender(device, case.a, args.iters),
                  "b": parse_sender(device, case.b, args.iters),
                }
                receiver_results = [
                  parse_receiver(device, case, receiver, args.iters)
                  for receiver in sorted({*case.a.receivers, *case.b.receivers})
                ]
                lines.append(format_aggregate_row(
                  case=case.name, repeat=repeat, noc=noc, major=major, path_reserve=path_reserve_label,
                  packet_bytes=packet_bytes, iters=args.iters, chunks=chunks,
                  senders=senders, receivers=receiver_results,
                ))
                for stream in (case.a, case.b):
                  lines.append(format_stream_row(
                    case=case.name, repeat=repeat, noc=noc, major=major, path_reserve=path_reserve_label,
                    stream=stream, rect=rects[stream.name], packet_bytes=packet_bytes,
                    iters=args.iters, chunks=chunks, sender=senders[stream.name],
                    receivers=receiver_results,
                  ))
  print("\n".join(lines))


if __name__ == "__main__":
  main()
