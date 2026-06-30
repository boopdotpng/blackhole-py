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
import riscv_noc_overlay_stream_poc as ovl  # noqa: E402
from asm import KernelBase  # noqa: E402
from dsl import a2, a3, a4, a5, a6, a7, s0, s1, s2, s3, s4, s5, s6, s7, t0, t1, t2, t3, t4, zero  # noqa: E402
from program import DevMsgs, Program, Run, UnicastWrite  # noqa: E402
from ttk.addrs import Core, noc_xy  # noqa: E402
from ttk.noc import NOC, Noc  # noqa: E402
from ttk.tensix import TensixL1  # noqa: E402


RESULT_BASE = 0x150000
SRC_BUF_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
DST_BUF_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
MSG_INFO_BASE = 0x130000
RESULT_WORDS = 96
RESULT_SIZE = RESULT_WORDS * 4
RESULT_MAGIC = 0x52534F42  # "RSOB"
STATUS_STARTED = 0x53000001
STATUS_READY_TIMEOUT = 0x5300BAD1
STATUS_DONE_TIMEOUT = 0x5300BAD2
STATUS_DONE = 0x5300D00D


class OverlayMcastKernel(KernelBase, Noc):
  pass


@dataclass(frozen=True)
class OverlayMcastResult:
  status: int
  noc: int
  stream_id: int
  dest_count: int
  byte_count: int
  rect: mcast.McastRect
  start: int
  end: int
  wr_ack_delta: int
  posted_delta: int
  nonposted_delta: int
  rd_resp_delta: int
  ready_remaining: int
  done_remaining: int
  wait_status: int
  debug8: int
  debug9: int
  src_first: int
  curr_phase: int
  phase_header: int
  remote_dest: int
  mcast_dest: int
  mcast_dest_num: int
  num_msgs_received: int
  msg_info_ptr: int
  msg_info_wr_ptr: int
  phase_all_msgs_pushed: int
  can_push: int
  ready_for_push: int
  remote_space0: int
  remote_space1: int
  remote_space2: int
  remote_space3: int

  @property
  def cycles(self) -> int:
    return (self.end - self.start) & ((1 << 64) - 1)

  @property
  def source_bpc(self) -> float:
    return self.byte_count / self.cycles if self.cycles else 0.0

  @property
  def delivered_bpc(self) -> float:
    return (self.byte_count * self.dest_count) / self.cycles if self.cycles else 0.0


@dataclass
class OverlayMcastProgram:
  bench: OverlayMcastKernel
  passive: KernelBase
  empty: KernelBase
  source: Core
  receivers: tuple[Core, ...]
  name: str

  def _program_for(self, brisc: KernelBase) -> Program:
    return Program(
      brisc=brisc,
      ncrisc=self.empty,
      trisc0=self.empty,
      trisc1=self.empty,
      trisc2=self.empty,
      num_cores=1,
    )

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    active = [self.source, *self.receivers]
    reset_blob = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_RESET_READ_PTR_FROM_HOST)
    commands = [
      UnicastWrite(active, TensixL1.GO_MSG, [reset_blob] * len(active)),
      UnicastWrite(active, TensixL1.GO_MSG_INDEX, [b"\0\0\0\0"] * len(active)),
    ]
    for core, brisc in [(self.source, self.bench), *[(receiver, self.passive) for receiver in self.receivers]]:
      segments = self._program_for(brisc).layout(
        core_xy=core,
        dispatch_mode=dispatch_mode,
        host_assigned_id=host_assigned_id,
      )
      for segment in segments:
        commands.append(UnicastWrite([core], segment.addr, [segment.data]))
    commands.append(Run(active))
    return commands


def emit_result_header(
  fw: KernelBase, *, status: int, noc: int, stream_id: int, dest_count: int, encoded_dest_count: int, byte_count: int,
  rect: mcast.McastRect,
):
  fw.li(s2, RESULT_BASE)
  values = (
    RESULT_MAGIC, 1, status, noc, stream_id, dest_count, byte_count, byte_count * dest_count,
    rect.x0, rect.y0, rect.x1, rect.y1, SRC_BUF_BASE, DST_BUF_BASE, MSG_INFO_BASE, 0,
    encoded_dest_count,
  )
  for off, value in enumerate(values):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off in range(len(values), RESULT_WORDS):
    fw.sw(zero, s2, off * 4)
  return fw


def emit_status(fw: KernelBase, status: int):
  fw.li(s2, RESULT_BASE)
  fw.li(t0, status)
  return fw.sw(t0, s2, 2 * 4)


def emit_counter_read(fw: KernelBase, noc: int, counter: int, out, *, addr=t3):
  fw.li(addr, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  return fw.lw(out, addr, 0)


def mcast_dest_value(rect: mcast.McastRect, *, major: str, path_reserve: bool, vc: int, linked: bool) -> int:
  value = (
    (rect.x1 << ovl.STREAM_MCAST_END_X)
    | (rect.y1 << ovl.STREAM_MCAST_END_Y)
    | (1 << ovl.STREAM_MCAST_EN)
  )
  if linked:
    value |= 1 << ovl.STREAM_MCAST_LINKED
  if vc == 5:
    value |= 1 << ovl.STREAM_MCAST_VC
  if not path_reserve:
    value |= 1 << ovl.STREAM_MCAST_NO_PATH_RES
  if major == "y":
    value |= 1 << ovl.STREAM_MCAST_XY
  return value


def emit_program_mcast_stream(
  fw: OverlayMcastKernel, *, noc: int, stream_id: int, rect: mcast.McastRect, encoded_dest_count: int,
  byte_count: int, major: str, path_reserve: bool, vc: int, linked: bool, in_order_fwd: bool,
):
  word_count = byte_count // ovl.MEM_WORD_WIDTH
  src_word_addr = SRC_BUF_BASE // ovl.MEM_WORD_WIDTH
  dst_word_addr = DST_BUF_BASE // ovl.MEM_WORD_WIDTH
  msg_info_word_addr = MSG_INFO_BASE // ovl.MEM_WORD_WIDTH
  misc_cfg = (
    (noc << ovl.OUTGOING_DATA_NOC)
    | ((1 - noc) << ovl.REMOTE_SRC_UPDATE_NOC)
    | (1 << ovl.SOURCE_ENDPOINT)
    | (1 << ovl.REMOTE_RECEIVER)
    | (1 << ovl.NEXT_PHASE_SRC_CHANGE)
    | (1 << ovl.NEXT_PHASE_DEST_CHANGE)
    | (1 << ovl.DEST_DATA_BUF_NO_FLOW_CTRL)
  )
  onetime_cfg = (1 << ovl.PHASE_AUTO_ADVANCE) | (3 << ovl.REG_UPDATE_VC_REG)

  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_RESET_REG_INDEX), 1)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_MCAST_DEST_NUM_REG_INDEX), encoded_dest_count)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_MCAST_DEST_REG_INDEX), mcast_dest_value(
    rect, major=major, path_reserve=path_reserve, vc=vc, linked=linked,
  ))
  if in_order_fwd:
    fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_GATHER_REG_INDEX), 1 << ovl.MSG_SRC_IN_ORDER_FWD)
    fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_MSG_SRC_IN_ORDER_FWD_NUM_MSGS_REG_INDEX), 1)
  else:
    fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_GATHER_REG_INDEX), 0)
    fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_MSG_SRC_IN_ORDER_FWD_NUM_MSGS_REG_INDEX), 0)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_PHASE_AUTO_CFG_HEADER_REG_INDEX), 1 << ovl.CURR_PHASE_NUM_MSGS)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_REMOTE_DEST_REG_INDEX), noc_xy(rect.x0, rect.y0))
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_REMOTE_DEST_BUF_START_HI_REG_INDEX), dst_word_addr >> ovl.MEM_WORD_ADDR_WIDTH)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_REMOTE_DEST_BUF_START_REG_INDEX), dst_word_addr)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_REMOTE_DEST_BUF_SIZE_REG_INDEX), word_count)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_BUF_START_REG_INDEX), src_word_addr)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_BUF_SIZE_REG_INDEX), word_count)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_MSG_INFO_PTR_REG_INDEX), msg_info_word_addr)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_MSG_INFO_WR_PTR_REG_INDEX), msg_info_word_addr)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_REMOTE_DEST_TRAFFIC_REG_INDEX), vc << ovl.UNICAST_VC_REG)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_MISC_CFG_REG_INDEX), misc_cfg)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_ONETIME_MISC_CFG_REG_INDEX), onetime_cfg)
  return fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_PHASE_ADVANCE_REG_INDEX), 1)


def build_kernel(
  *, noc: int, stream_id: int, rect: mcast.McastRect, dest_count: int, byte_count: int,
  major: str, path_reserve: bool, vc: int, linked: bool, in_order_fwd: bool, dest_count_override: int | None,
  enqueue: str, last_tile: bool, phase_ready_num: int, phase_ready_dest_num: int,
  ready_timeout_iters: int, done_timeout_iters: int, repeats: int,
) -> OverlayMcastKernel:
  fw = OverlayMcastKernel()
  # The NoC mcast rectangle controls packet fanout. For this source-endpoint
  # overlay path, STREAM_MCAST_DEST_NUM appears to count the single tracked
  # overlay mcast destination slot; setting it to the receiver count wedges
  # the stream phase for rectangles wider than two cores.
  encoded_dest_count = 1 if dest_count_override is None else dest_count_override
  emit_result_header(
    fw, status=STATUS_STARTED, noc=noc, stream_id=stream_id, dest_count=dest_count,
    encoded_dest_count=encoded_dest_count, byte_count=byte_count, rect=rect,
  )
  ready_timeout = fw._new_label("overlay_mcast_ready_timeout")
  done_timeout = fw._new_label("overlay_mcast_done_timeout")
  finish = fw._new_label("overlay_mcast_finish")

  emit_counter_read(fw, noc, NOC.NIU_MST_WR_ACK_RECEIVED, a6)
  emit_counter_read(fw, noc, NOC.NIU_MST_POSTED_WR_REQ_SENT, a7)
  emit_counter_read(fw, noc, NOC.NIU_MST_NONPOSTED_WR_REQ_SENT, s6)
  emit_counter_read(fw, noc, NOC.NIU_MST_RD_RESP_RECEIVED, s7)
  fw.li(t0, RESULT_BASE)
  for off, reg in ((20, a6), (21, a7), (22, s6), (23, s7)):
    fw.sw(reg, t0, off * 4)

  harness.read_wall_clock(fw, a2, a3)

  def emit_one_transfer():
    emit_program_mcast_stream(
      fw,
      noc=noc,
      stream_id=stream_id,
      rect=rect,
      encoded_dest_count=encoded_dest_count,
      byte_count=byte_count,
      major=major,
      path_reserve=path_reserve,
      vc=vc,
      linked=linked,
      in_order_fwd=in_order_fwd,
    )

    ovl.emit_wait_src_ready(fw, stream_id=stream_id, timeout_iters=ready_timeout_iters, timeout_label=ready_timeout)

    fw.write32(
      ovl.stream_reg(stream_id, ovl.STREAM_DEST_PHASE_READY_UPDATE_REG_INDEX),
      (phase_ready_dest_num << ovl.PHASE_READY_DEST_NUM)
      | (phase_ready_num << ovl.PHASE_READY_NUM)
      | (1 << ovl.PHASE_READY_MCAST)
      | (1 << ovl.PHASE_READY_TWO_WAY_RESP),
    )
    src_word_addr = SRC_BUF_BASE // ovl.MEM_WORD_WIDTH
    word_count = byte_count // ovl.MEM_WORD_WIDTH
    if enqueue == "direct":
      value = (
        (src_word_addr << ovl.SOURCE_ENDPOINT_NEW_MSG_ADDR)
        | (word_count << ovl.SOURCE_ENDPOINT_NEW_MSG_SIZE)
      )
      if last_tile:
        value |= 1 << ovl.SOURCE_ENDPOINT_NEW_MSG_LAST_TILE
      fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_SOURCE_ENDPOINT_NEW_MSG_INFO_REG_INDEX), value)
    else:
      value = (
        (1 << ovl.SOURCE_ENDPOINT_NEW_MSGS_NUM)
        | (word_count << ovl.SOURCE_ENDPOINT_NEW_MSGS_TOTAL_SIZE)
      )
      if last_tile:
        value |= 1 << ovl.SOURCE_ENDPOINT_NEW_MSGS_LAST_TILE
      fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_NUM_MSGS_RECEIVED_INC_REG_INDEX), value)
    ovl.emit_wait_stream_done(fw, stream_id=stream_id, timeout_iters=done_timeout_iters, timeout_label=done_timeout)

  for _repeat in range(repeats):
    emit_one_transfer()
  harness.read_wall_clock(fw, a4, a5)
  emit_status(fw, STATUS_DONE)
  fw.j(finish)

  fw.label(ready_timeout)
  harness.read_wall_clock(fw, a2, a3)
  fw.mv(a4, a2)
  fw.mv(a5, a3)
  emit_status(fw, STATUS_READY_TIMEOUT)
  fw.j(finish)

  fw.label(done_timeout)
  harness.read_wall_clock(fw, a4, a5)
  emit_status(fw, STATUS_DONE_TIMEOUT)

  fw.label(finish)
  fw.li(t0, RESULT_BASE)
  for off, reg in ((16, a2), (17, a3), (18, a4), (19, a5), (28, s0), (29, s1)):
    fw.sw(reg, t0, off * 4)
  emit_counter_read(fw, noc, NOC.NIU_MST_WR_ACK_RECEIVED, a6)
  emit_counter_read(fw, noc, NOC.NIU_MST_POSTED_WR_REQ_SENT, a7)
  emit_counter_read(fw, noc, NOC.NIU_MST_NONPOSTED_WR_REQ_SENT, s6)
  emit_counter_read(fw, noc, NOC.NIU_MST_RD_RESP_RECEIVED, s7)
  fw.read32(s2, ovl.stream_reg(stream_id, ovl.STREAM_WAIT_STATUS_REG_INDEX), tmp_addr=t3)
  fw.read32(s3, ovl.stream_reg(stream_id, ovl.STREAM_DEBUG_STATUS_REG_INDEX + 8), tmp_addr=t3)
  fw.read32(s4, ovl.stream_reg(stream_id, ovl.STREAM_DEBUG_STATUS_REG_INDEX + 9), tmp_addr=t3)
  fw.read32(s5, SRC_BUF_BASE, tmp_addr=t3)
  fw.li(t0, RESULT_BASE)
  for off, reg in (
    (24, a6), (25, a7), (26, s6), (27, s7),
    (32, s2), (33, s3), (34, s4), (35, s5),
  ):
    fw.sw(reg, t0, off * 4)
  for off, reg_id in (
    (36, ovl.STREAM_CURR_PHASE_REG_INDEX),
    (37, ovl.STREAM_PHASE_AUTO_CFG_HEADER_REG_INDEX),
    (38, ovl.STREAM_REMOTE_DEST_REG_INDEX),
    (39, ovl.STREAM_MCAST_DEST_REG_INDEX),
    (40, ovl.STREAM_MCAST_DEST_NUM_REG_INDEX),
    (41, ovl.STREAM_NUM_MSGS_RECEIVED_REG_INDEX),
    (42, ovl.STREAM_MSG_INFO_PTR_REG_INDEX),
    (43, ovl.STREAM_MSG_INFO_WR_PTR_REG_INDEX),
    (44, ovl.STREAM_PHASE_ALL_MSGS_PUSHED_REG_INDEX),
    (45, ovl.STREAM_MSG_INFO_CAN_PUSH_NEW_MSG_REG_INDEX),
    (46, ovl.STREAM_READY_FOR_MSG_PUSH_REG_INDEX),
    (47, ovl.STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_REG_INDEX),
    (48, ovl.STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_REG_INDEX + 1),
    (49, ovl.STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_REG_INDEX + 2),
    (50, ovl.STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_REG_INDEX + 3),
  ):
    fw.read32(t1, ovl.stream_reg(stream_id, reg_id), tmp_addr=t3)
    fw.li(t0, RESULT_BASE)
    fw.sw(t1, t0, off * 4)
  fw.li(t1, RESULT_MAGIC)
  fw.sw(t1, t0, (RESULT_WORDS - 1) * 4)
  return fw.ret()


def build_program(
  *, source: Core, receivers: tuple[Core, ...], noc: int, stream_id: int, rect: mcast.McastRect,
  byte_count: int, major: str, path_reserve: bool, vc: int, linked: bool, in_order_fwd: bool,
  dest_count_override: int | None, enqueue: str, last_tile: bool, phase_ready_num: int, phase_ready_dest_num: int,
  ready_timeout_iters: int, done_timeout_iters: int, repeats: int,
) -> OverlayMcastProgram:
  bench = build_kernel(
    noc=noc,
    stream_id=stream_id,
    rect=rect,
    dest_count=len(receivers),
    byte_count=byte_count,
    major=major,
    path_reserve=path_reserve,
    vc=vc,
    linked=linked,
    in_order_fwd=in_order_fwd,
    dest_count_override=dest_count_override,
    enqueue=enqueue,
    last_tile=last_tile,
    phase_ready_num=phase_ready_num,
    phase_ready_dest_num=phase_ready_dest_num,
    ready_timeout_iters=ready_timeout_iters,
    done_timeout_iters=done_timeout_iters,
    repeats=repeats,
  )
  return OverlayMcastProgram(
    bench=bench,
    passive=KernelBase().ret(),
    empty=KernelBase(),
    source=source,
    receivers=receivers,
    name=f"riscv_noc_overlay_mcast_poc:noc{noc}:stream{stream_id}:dests{len(receivers)}",
  )


def seed_payload(byte_count: int) -> bytes:
  out = bytearray(byte_count)
  for off in range(0, byte_count, 4):
    struct.pack_into("<I", out, off, 0xE77A0000 | ((off // 4) & 0xFFFF))
  return bytes(out)


def clear_and_seed(device, *, source: Core, receivers: tuple[Core, ...], byte_count: int):
  payload = seed_payload(byte_count)
  with harness.device_window(device, source) as win:
    win.write(RESULT_BASE, b"\0" * RESULT_SIZE)
    win.write(SRC_BUF_BASE, payload)
    win.write(MSG_INFO_BASE, b"\0" * 256)
  for receiver in receivers:
    with harness.device_window(device, receiver) as win:
      win.write(DST_BUF_BASE, b"\0" * byte_count)


def verify_payloads(device, receivers: tuple[Core, ...], byte_count: int) -> tuple[int, list[tuple[Core, bool, int, int]]]:
  expected = seed_payload(byte_count)
  bad = 0
  rows = []
  for receiver in receivers:
    got = harness.read_window(device, receiver, DST_BUF_BASE, byte_count)
    ok = got == expected
    bad += 0 if ok else 1
    first = struct.unpack_from("<I", got, 0)[0] if byte_count >= 4 else 0
    last = struct.unpack_from("<I", got, byte_count - 4)[0] if byte_count >= 4 else 0
    rows.append((receiver, ok, first, last))
  return bad, rows


def parse_result(device, source: Core) -> OverlayMcastResult:
  blob = harness.read_window(device, source, RESULT_BASE, RESULT_SIZE)
  words = struct.unpack("<" + "I" * RESULT_WORDS, blob)
  if words[0] != RESULT_MAGIC or words[RESULT_WORDS - 1] != RESULT_MAGIC:
    raise RuntimeError(f"bad result magic head=0x{words[0]:08x} tail=0x{words[RESULT_WORDS - 1]:08x}")
  start = words[16] | (words[17] << 32)
  end = words[18] | (words[19] << 32)
  return OverlayMcastResult(
    status=words[2],
    noc=words[3],
    stream_id=words[4],
    dest_count=words[5],
    byte_count=words[6],
    rect=mcast.McastRect(words[8], words[9], words[10], words[11]),
    start=start,
    end=end,
    wr_ack_delta=(words[24] - words[20]) & 0xFFFFFFFF,
    posted_delta=(words[25] - words[21]) & 0xFFFFFFFF,
    nonposted_delta=(words[26] - words[22]) & 0xFFFFFFFF,
    rd_resp_delta=(words[27] - words[23]) & 0xFFFFFFFF,
    ready_remaining=words[28],
    done_remaining=words[29],
    wait_status=words[32],
    debug8=words[33],
    debug9=words[34],
    src_first=words[35],
    curr_phase=words[36],
    phase_header=words[37],
    remote_dest=words[38],
    mcast_dest=words[39],
    mcast_dest_num=words[40],
    num_msgs_received=words[41],
    msg_info_ptr=words[42],
    msg_info_wr_ptr=words[43],
    phase_all_msgs_pushed=words[44],
    can_push=words[45],
    ready_for_push=words[46],
    remote_space0=words[47],
    remote_space1=words[48],
    remote_space2=words[49],
    remote_space3=words[50],
  )


def format_summary(result: OverlayMcastResult, *, source: Core, receivers: tuple[Core, ...], payload_bad: int, payload_rows):
  status_name = {
    STATUS_STARTED: "started",
    STATUS_READY_TIMEOUT: "ready-timeout",
    STATUS_DONE_TIMEOUT: "done-timeout",
    STATUS_DONE: "done",
  }.get(result.status, f"0x{result.status:08x}")
  rect = result.rect
  lines = [
    "| source | noc | stream | rect | dests | status | bytes | cycles | src B/cyc | delivered B/cyc | bad payloads | wr ack d | posted d | nonposted d | rd resp d | wait | debug8 | debug9 |",
    "|---|---:|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    (
      f"| `{source[0]},{source[1]}` | {result.noc} | {result.stream_id} | "
      f"`{rect.x0},{rect.y0}->{rect.x1},{rect.y1}` | {result.dest_count} | {status_name} | "
      f"{result.byte_count} | {result.cycles} | {result.source_bpc:.3f} | {result.delivered_bpc:.3f} | "
      f"{payload_bad} | {result.wr_ack_delta} | {result.posted_delta} | {result.nonposted_delta} | "
      f"{result.rd_resp_delta} | 0x{result.wait_status:08x} | 0x{result.debug8:08x} | 0x{result.debug9:08x} |"
    ),
    "",
    "| receiver | payload ok | first | last |",
    "|---|---|---:|---:|",
  ]
  for receiver, ok, first, last in payload_rows:
    lines.append(f"| `{receiver[0]},{receiver[1]}` | {ok} | 0x{first:08x} | 0x{last:08x} |")
  lines.extend([
    "",
    "| curr phase | phase header | remote dest | mcast dest | mcast num | msgs recv | msg ptr | msg wr | all pushed | can push | ready push | remote space 0 | remote space 1 | remote space 2 | remote space 3 |",
    "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    (
      f"| 0x{result.curr_phase:08x} | 0x{result.phase_header:08x} | 0x{result.remote_dest:08x} | "
      f"0x{result.mcast_dest:08x} | {result.mcast_dest_num} | {result.num_msgs_received} | "
      f"0x{result.msg_info_ptr:08x} | 0x{result.msg_info_wr_ptr:08x} | {result.phase_all_msgs_pushed} | "
      f"{result.can_push} | {result.ready_for_push} | 0x{result.remote_space0:08x} | "
      f"0x{result.remote_space1:08x} | 0x{result.remote_space2:08x} | 0x{result.remote_space3:08x} |"
    ),
  ])
  return "\n".join(lines)


def append_report(path: Path, *, result: OverlayMcastResult, source: Core, receivers: tuple[Core, ...], payload_bad: int, payload_rows):
  harness.append_report(path, None, [
    "Scope: arm one Blackhole NoC overlay source-endpoint stream as a multicast write.",
    "The stream reads one source L1 buffer and writes the same payload into a receiver rectangle.",
    "Blackhole stream-overlay multicast requires one of the multicast-capable streams 0..3.",
    "`STREAM_MCAST_DEST_NUM` is programmed to 1 for this PoC; the NoC mcast rectangle controls the actual fanout.",
    "tt-metal exposes the register map, but its `stream_dram_write` helper clears mcast state and uses the overlay as unicast.",
    "Timing starts before `STREAM_SOURCE_ENDPOINT_NEW_MSG_INFO` and ends after the stream phase completes.",
  ], format_summary(result, source=source, receivers=receivers, payload_bad=payload_bad, payload_rows=payload_rows))


def parse_core_list(text: str) -> tuple[Core, ...]:
  return tuple(harness.parse_core(item.strip()) for item in text.split(";") if item.strip())


def default_receivers(device, source: Core, count: int) -> tuple[Core, ...]:
  sx, sy = source
  same_row = [core for core in sorted(device.cores) if core[1] == sy and core != source]
  right = [core for core in same_row if core[0] > sx]
  left = [core for core in same_row if core[0] < sx]
  receivers = right + left
  if len(receivers) < count:
    raise ValueError(f"need {count} receivers on row y={sy}; only found {len(receivers)}")
  return tuple(receivers[:count])


def main():
  parser = argparse.ArgumentParser(description="Blackhole NoC overlay stream multicast PoC.")
  parser.add_argument("--source", type=harness.parse_core, default=(1, 2))
  parser.add_argument("--receivers", type=parse_core_list, default=None, help="semicolon-separated X,Y receiver list")
  parser.add_argument("--count", type=int, default=2, help="default receiver count from the source row")
  parser.add_argument("--noc", type=int, choices=(0, 1), default=0)
  # tt-metal's Blackhole overlay register map marks only streams 0..3 as
  # multicast-capable. Non-mcast-capable streams can accept the mcast registers
  # but behave like a unicast to the rectangle start, which is a very plausible
  # trap when experimenting.
  parser.add_argument(
    "--stream", type=int, default=ovl.MCAST_STREAM_ID_START,
    help="overlay stream id to program; Blackhole stream-overlay multicast is only supported on streams 0..3",
  )
  parser.add_argument("--bytes", type=int, default=16 * 1024)
  parser.add_argument("--repeats", type=int, default=1, help="repeat the stream programming/enqueue/wait sequence in one kernel")
  parser.add_argument("--major", choices=("x", "y"), default="x")
  parser.add_argument("--no-path-reserve", action="store_true")
  parser.add_argument("--linked", action="store_true")
  parser.add_argument("--no-in-order-fwd", action="store_true")
  parser.add_argument(
    "--dest-count-override", type=int, default=None,
    help="diagnostic override for STREAM_MCAST_DEST_NUM; default 1 tracks one overlay mcast destination slot",
  )
  parser.add_argument("--enqueue", choices=("direct", "inc"), default="direct")
  parser.add_argument("--last-tile", action="store_true")
  parser.add_argument("--phase-ready-num", type=int, default=0)
  parser.add_argument("--phase-ready-dest-num", type=int, default=0)
  parser.add_argument("--vc", type=int, choices=(4, 5), default=5, help="mcast VC selector; overlay supports VC4 or VC5 here")
  parser.add_argument("--ready-timeout-iters", type=int, default=1_000_000)
  parser.add_argument("--done-timeout-iters", type=int, default=10_000_000)
  parser.add_argument("--no-report", action="store_true")
  parser.add_argument("--report", type=Path, default=harness.doc_path("noc", "noc-overlay-mcast-poc.md"))
  args = parser.parse_args()

  if args.bytes <= 0 or args.bytes % ovl.MEM_WORD_WIDTH:
    raise ValueError("--bytes must be a positive multiple of 16")
  if args.bytes // ovl.MEM_WORD_WIDTH >= (1 << 14):
    raise ValueError("--bytes exceeds SOURCE_ENDPOINT_NEW_MSG_SIZE field")
  if args.count <= 0:
    raise ValueError("--count must be positive")
  if args.repeats <= 0:
    raise ValueError("--repeats must be positive")
  if not ovl.MCAST_STREAM_ID_START <= args.stream <= ovl.MCAST_STREAM_ID_END:
    raise ValueError("--stream must be in [0, 3] for Blackhole stream-overlay multicast")
  if not 0 <= args.phase_ready_dest_num < 64:
    raise ValueError("--phase-ready-dest-num must be in [0, 63]")
  if not 0 <= args.phase_ready_num < (1 << 20):
    raise ValueError("--phase-ready-num must fit in 20 bits")

  with harness.open_device() as device:
    receivers = args.receivers if args.receivers is not None else default_receivers(device, args.source, args.count)
    if args.source in receivers:
      raise ValueError("--receivers must not include --source")
    live = set(device.cores)
    missing = [core for core in (args.source, *receivers) if core not in live]
    if missing:
      raise ValueError(f"cores are not live program cores: {missing}")
    rect = mcast.logical_rect_for_physical_span(receivers, noc=args.noc, cmap=mcast.read_tensix_coordinate_map(device))
    clear_and_seed(device, source=args.source, receivers=receivers, byte_count=args.bytes)
    program = build_program(
      source=args.source,
      receivers=receivers,
      noc=args.noc,
      stream_id=args.stream,
      rect=rect,
      byte_count=args.bytes,
      major=args.major,
      path_reserve=not args.no_path_reserve,
      vc=args.vc,
      linked=args.linked,
      in_order_fwd=not args.no_in_order_fwd,
      dest_count_override=args.dest_count_override,
      enqueue=args.enqueue,
      last_tile=args.last_tile,
      phase_ready_num=args.phase_ready_num,
      phase_ready_dest_num=args.phase_ready_dest_num,
      ready_timeout_iters=args.ready_timeout_iters,
      done_timeout_iters=args.done_timeout_iters,
      repeats=args.repeats,
    )
    device.run(program)
    result = parse_result(device, args.source)
    payload_bad, payload_rows = verify_payloads(device, receivers, args.bytes)

  print(format_summary(result, source=args.source, receivers=receivers, payload_bad=payload_bad, payload_rows=payload_rows))
  if not args.no_report:
    append_report(args.report, result=result, source=args.source, receivers=receivers, payload_bad=payload_bad, payload_rows=payload_rows)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
