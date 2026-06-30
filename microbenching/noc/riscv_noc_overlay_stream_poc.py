#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402  (does sys.path + TT_USB bootstrap on import)
from asm import KernelBase  # noqa: E402
from dsl import a2, a3, a4, a5, a6, a7, s0, s1, s2, s3, s4, s5, s6, s7, t0, t1, t2, t3, t4, zero  # noqa: E402
from program import DevMsgs, Program, Run, UnicastWrite  # noqa: E402
from ttk.addrs import Core, noc_xy  # noqa: E402
from ttk.noc import NOC, Noc  # noqa: E402
from ttk.tensix import TensixL1  # noqa: E402


# This PoC intentionally keeps the stream-register constants local. The values
# come from tt-metal/hw/inc/internal/tt-2xx/quasar/noc/noc_overlay_parameters.h.
NOC_OVERLAY_START_ADDR = 0xFFB40000
NOC_STREAM_REG_SPACE_SIZE = 0x1000
MCAST_STREAM_ID_START = 0
MCAST_STREAM_ID_END = 3
MEM_WORD_WIDTH = 16
MEM_WORD_ADDR_WIDTH = 17

STREAM_SOURCE_ENDPOINT_NEW_MSG_INFO_REG_INDEX = 0
STREAM_NUM_MSGS_RECEIVED_INC_REG_INDEX = 1
STREAM_ONETIME_MISC_CFG_REG_INDEX = 2
STREAM_MISC_CFG_REG_INDEX = 3
STREAM_REMOTE_DEST_REG_INDEX = 7
STREAM_REMOTE_DEST_BUF_START_REG_INDEX = 8
STREAM_REMOTE_DEST_BUF_START_HI_REG_INDEX = 9
STREAM_REMOTE_DEST_BUF_SIZE_REG_INDEX = 10
STREAM_REMOTE_DEST_TRAFFIC_REG_INDEX = 16
STREAM_BUF_START_REG_INDEX = 17
STREAM_BUF_SIZE_REG_INDEX = 18
STREAM_MSG_INFO_PTR_REG_INDEX = 22
STREAM_MSG_INFO_WR_PTR_REG_INDEX = 23
STREAM_MCAST_DEST_REG_INDEX = 24
STREAM_MCAST_DEST_NUM_REG_INDEX = 25
STREAM_GATHER_REG_INDEX = 26
STREAM_MSG_SRC_IN_ORDER_FWD_NUM_MSGS_REG_INDEX = 27
STREAM_CURR_PHASE_REG_INDEX = 29
STREAM_PHASE_AUTO_CFG_HEADER_REG_INDEX = 34
STREAM_WAIT_STATUS_REG_INDEX = 257
STREAM_NUM_MSGS_RECEIVED_REG_INDEX = 259
STREAM_BUF_SPACE_AVAILABLE_REG_INDEX = 260
STREAM_PHASE_ADVANCE_REG_INDEX = 267
STREAM_DEST_PHASE_READY_UPDATE_REG_INDEX = 268
STREAM_RESET_REG_INDEX = 271
STREAM_MSG_INFO_CAN_PUSH_NEW_MSG_REG_INDEX = 275
STREAM_PHASE_ALL_MSGS_PUSHED_REG_INDEX = 277
STREAM_READY_FOR_MSG_PUSH_REG_INDEX = 278
STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_REG_INDEX = 297
STREAM_DEBUG_STATUS_REG_INDEX = 501

OUTGOING_DATA_NOC = 1
REMOTE_SRC_UPDATE_NOC = 2
SOURCE_ENDPOINT = 4
REMOTE_RECEIVER = 8
NEXT_PHASE_SRC_CHANGE = 11
NEXT_PHASE_DEST_CHANGE = 12
DEST_DATA_BUF_NO_FLOW_CTRL = 14
PHASE_AUTO_ADVANCE = 1
REG_UPDATE_VC_REG = 2
SOURCE_ENDPOINT_NEW_MSG_ADDR = 0
SOURCE_ENDPOINT_NEW_MSG_SIZE = 17
SOURCE_ENDPOINT_NEW_MSG_LAST_TILE = 31
SOURCE_ENDPOINT_NEW_MSGS_NUM = 0
SOURCE_ENDPOINT_NEW_MSGS_TOTAL_SIZE = 12
SOURCE_ENDPOINT_NEW_MSGS_LAST_TILE = 29
CURR_PHASE_NUM_MSGS = 12
UNICAST_VC_REG = 4
STREAM_MCAST_END_X = 0
STREAM_MCAST_END_Y = 6
STREAM_MCAST_EN = 12
STREAM_MCAST_LINKED = 13
STREAM_MCAST_VC = 14
STREAM_MCAST_NO_PATH_RES = 15
STREAM_MCAST_XY = 16
MSG_SRC_IN_ORDER_FWD = 16
WAIT_SW_PHASE_ADVANCE_SIGNAL = 0
PHASE_READY_DEST_NUM = 0
PHASE_READY_NUM = 6
PHASE_READY_MCAST = 26
PHASE_READY_TWO_WAY_RESP = 27

SRC_READY_WAIT_ALL_DESTS = 4

RESULT_BASE = 0x150000
SRC_BUF_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
DST_BUF_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
MSG_INFO_BASE = 0x130000
RESULT_WORDS = 32
RESULT_SIZE = RESULT_WORDS * 4
RESULT_MAGIC = 0x52534F53  # "RSOS"
STATUS_STARTED = 0x51000001
STATUS_READY_TIMEOUT = 0x5100BAD1
STATUS_DONE_TIMEOUT = 0x5100BAD2
STATUS_DONE = 0x5100D00D


class OverlayKernel(KernelBase, Noc):
  pass


@dataclass(frozen=True)
class OverlayResult:
  status: int
  noc: int
  stream_id: int
  peer_coord: int
  byte_count: int
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
  buf_space: int
  remote_space: int
  can_push: int
  ready_for_push: int
  src_first: int

  @property
  def cycles(self) -> int:
    return (self.end - self.start) & ((1 << 64) - 1)

  @property
  def bpc(self) -> float:
    return self.byte_count / self.cycles if self.cycles else 0.0


def stream_reg(stream_id: int, reg_id: int) -> int:
  return NOC_OVERLAY_START_ADDR + stream_id * NOC_STREAM_REG_SPACE_SIZE + reg_id * 4


def noc_addr_hi(coord: int) -> int:
  return coord & 0xFFF


def emit_status(fw: KernelBase, status: int):
  fw.li(s2, RESULT_BASE)
  fw.li(t0, status)
  fw.sw(t0, s2, 2 * 4)
  return fw


def emit_counter_read(fw: KernelBase, noc: int, counter: int, out, *, addr=t3):
  fw.li(addr, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  return fw.lw(out, addr, 0)


def emit_header(fw: KernelBase, *, noc: int, stream_id: int, peer_coord: int, byte_count: int, status: int):
  fw.li(s2, RESULT_BASE)
  values = (
    RESULT_MAGIC, 1, status, noc, stream_id, peer_coord, byte_count, byte_count // MEM_WORD_WIDTH,
    SRC_BUF_BASE, DST_BUF_BASE, MSG_INFO_BASE,
  )
  for off, value in enumerate(values):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off in range(len(values), RESULT_WORDS):
    fw.sw(zero, s2, off * 4)
  return fw


def emit_snapshot_tail(fw: OverlayKernel, *, noc: int, stream_id: int):
  emit_counter_read(fw, noc, NOC.NIU_MST_WR_ACK_RECEIVED, a6)
  emit_counter_read(fw, noc, NOC.NIU_MST_POSTED_WR_REQ_SENT, a7)
  emit_counter_read(fw, noc, NOC.NIU_MST_NONPOSTED_WR_REQ_SENT, s3)
  emit_counter_read(fw, noc, NOC.NIU_MST_RD_RESP_RECEIVED, s4)

  fw.read32(s5, stream_reg(stream_id, STREAM_WAIT_STATUS_REG_INDEX), tmp_addr=t3)
  fw.read32(s6, stream_reg(stream_id, STREAM_DEBUG_STATUS_REG_INDEX + 8), tmp_addr=t3)
  fw.read32(s7, stream_reg(stream_id, STREAM_DEBUG_STATUS_REG_INDEX + 9), tmp_addr=t3)
  fw.read32(t0, stream_reg(stream_id, STREAM_BUF_SPACE_AVAILABLE_REG_INDEX), tmp_addr=t3)
  fw.read32(t1, stream_reg(stream_id, STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_REG_INDEX), tmp_addr=t3)
  fw.read32(t2, stream_reg(stream_id, STREAM_MSG_INFO_CAN_PUSH_NEW_MSG_REG_INDEX), tmp_addr=t3)
  fw.read32(t3, stream_reg(stream_id, STREAM_READY_FOR_MSG_PUSH_REG_INDEX), tmp_addr=t4)
  fw.read32(t4, SRC_BUF_BASE)

  fw.li(s2, RESULT_BASE)
  for off, reg in (
    (14, a6), (15, a7), (16, s3), (17, s4),
    (20, s0), (21, s1), (22, s5), (23, s6), (24, s7),
    (25, t0), (26, t1), (27, t2), (28, t3), (29, t4),
  ):
    fw.sw(reg, s2, off * 4)
  fw.li(t0, RESULT_MAGIC)
  fw.sw(t0, s2, 31 * 4)
  return fw


def emit_wait_src_ready(fw: OverlayKernel, *, stream_id: int, timeout_iters: int, timeout_label: str):
  fw.li(s0, timeout_iters)
  loop = fw._new_label("overlay_src_ready")
  done = fw._new_label("overlay_src_ready_done")
  fw.label(loop)
  fw.read32(t0, stream_reg(stream_id, STREAM_DEBUG_STATUS_REG_INDEX + 8), tmp_addr=t3)
  fw.srli(t0, t0, 4)
  fw.andi(t0, t0, 0x7)
  fw.li(t1, SRC_READY_WAIT_ALL_DESTS)
  fw.beq(t0, t1, done)
  fw.addi(s0, s0, -1)
  fw.bne(s0, zero, loop)
  fw.j(timeout_label)
  fw.label(done)
  return fw


def emit_wait_stream_done(fw: OverlayKernel, *, stream_id: int, timeout_iters: int, timeout_label: str):
  fw.li(s1, timeout_iters)
  loop = fw._new_label("overlay_stream_done")
  done = fw._new_label("overlay_stream_done_ok")
  next_try = fw._new_label("overlay_stream_done_next")
  fw.label(loop)
  fw.read32(t0, stream_reg(stream_id, STREAM_WAIT_STATUS_REG_INDEX), tmp_addr=t3)
  fw.andi(t0, t0, 1 << WAIT_SW_PHASE_ADVANCE_SIGNAL)
  fw.beq(t0, zero, next_try)
  fw.read32(t1, stream_reg(stream_id, STREAM_DEBUG_STATUS_REG_INDEX + 9), tmp_addr=t3)
  fw.srli(t1, t1, MEM_WORD_ADDR_WIDTH)
  fw.beq(t1, zero, done)
  fw.label(next_try)
  fw.addi(s1, s1, -1)
  fw.bne(s1, zero, loop)
  fw.j(timeout_label)
  fw.label(done)
  return fw


def emit_overlay_write(
  fw: OverlayKernel, *, noc: int, stream_id: int, peer_coord: int, byte_count: int, vc: int,
  ready_timeout_iters: int, done_timeout_iters: int,
):
  word_count = byte_count // MEM_WORD_WIDTH
  src_word_addr = SRC_BUF_BASE // MEM_WORD_WIDTH
  dst_word_addr = DST_BUF_BASE // MEM_WORD_WIDTH
  msg_info_word_addr = MSG_INFO_BASE // MEM_WORD_WIDTH
  misc_cfg = (
    (noc << OUTGOING_DATA_NOC)
    | ((1 - noc) << REMOTE_SRC_UPDATE_NOC)
    | (1 << SOURCE_ENDPOINT)
    | (1 << REMOTE_RECEIVER)
    | (1 << NEXT_PHASE_SRC_CHANGE)
    | (1 << NEXT_PHASE_DEST_CHANGE)
    | (1 << DEST_DATA_BUF_NO_FLOW_CTRL)
  )
  onetime_cfg = (1 << PHASE_AUTO_ADVANCE) | (3 << REG_UPDATE_VC_REG)

  ready_timeout = fw._new_label("overlay_ready_timeout")
  done_timeout = fw._new_label("overlay_done_timeout")
  finish = fw._new_label("overlay_finish")

  emit_header(fw, noc=noc, stream_id=stream_id, peer_coord=peer_coord, byte_count=byte_count, status=STATUS_STARTED)

  # Reset then program the one-shot source endpoint + remote receiver stream.
  fw.write32(stream_reg(stream_id, STREAM_RESET_REG_INDEX), 1)
  fw.write32(stream_reg(stream_id, STREAM_PHASE_AUTO_CFG_HEADER_REG_INDEX), 1 << CURR_PHASE_NUM_MSGS)
  fw.write32(stream_reg(stream_id, STREAM_REMOTE_DEST_REG_INDEX), noc_addr_hi(peer_coord))
  fw.write32(stream_reg(stream_id, STREAM_REMOTE_DEST_BUF_START_HI_REG_INDEX), dst_word_addr >> MEM_WORD_ADDR_WIDTH)
  fw.write32(stream_reg(stream_id, STREAM_REMOTE_DEST_BUF_START_REG_INDEX), dst_word_addr)
  fw.write32(stream_reg(stream_id, STREAM_REMOTE_DEST_BUF_SIZE_REG_INDEX), word_count)
  fw.write32(stream_reg(stream_id, STREAM_BUF_START_REG_INDEX), src_word_addr)
  fw.write32(stream_reg(stream_id, STREAM_BUF_SIZE_REG_INDEX), word_count)
  fw.write32(stream_reg(stream_id, STREAM_MSG_INFO_PTR_REG_INDEX), msg_info_word_addr)
  fw.write32(stream_reg(stream_id, STREAM_MSG_INFO_WR_PTR_REG_INDEX), msg_info_word_addr)
  fw.write32(stream_reg(stream_id, STREAM_REMOTE_DEST_TRAFFIC_REG_INDEX), vc << UNICAST_VC_REG)
  fw.write32(stream_reg(stream_id, STREAM_MISC_CFG_REG_INDEX), misc_cfg)
  fw.write32(stream_reg(stream_id, STREAM_ONETIME_MISC_CFG_REG_INDEX), onetime_cfg)
  fw.write32(stream_reg(stream_id, STREAM_PHASE_ADVANCE_REG_INDEX), 1)

  emit_wait_src_ready(fw, stream_id=stream_id, timeout_iters=ready_timeout_iters, timeout_label=ready_timeout)

  emit_counter_read(fw, noc, NOC.NIU_MST_WR_ACK_RECEIVED, a6)
  emit_counter_read(fw, noc, NOC.NIU_MST_POSTED_WR_REQ_SENT, a7)
  emit_counter_read(fw, noc, NOC.NIU_MST_NONPOSTED_WR_REQ_SENT, s3)
  emit_counter_read(fw, noc, NOC.NIU_MST_RD_RESP_RECEIVED, s4)
  fw.li(s2, RESULT_BASE)
  for off, reg in ((10, a6), (11, a7), (12, s3), (13, s4)):
    fw.sw(reg, s2, off * 4)

  harness.read_wall_clock(fw, a2, a3)
  fw.write32(stream_reg(stream_id, STREAM_DEST_PHASE_READY_UPDATE_REG_INDEX), 1 << PHASE_READY_TWO_WAY_RESP)
  fw.write32(
    stream_reg(stream_id, STREAM_SOURCE_ENDPOINT_NEW_MSG_INFO_REG_INDEX),
    (src_word_addr << SOURCE_ENDPOINT_NEW_MSG_ADDR) | (word_count << SOURCE_ENDPOINT_NEW_MSG_SIZE),
  )
  emit_wait_stream_done(fw, stream_id=stream_id, timeout_iters=done_timeout_iters, timeout_label=done_timeout)
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
  fw.li(s2, RESULT_BASE)
  for off, reg in ((6, a2), (7, a3), (8, a4), (9, a5)):
    fw.sw(reg, s2, off * 4)
  emit_snapshot_tail(fw, noc=noc, stream_id=stream_id)
  return fw.ret()


@dataclass
class OverlayPairProgram:
  bench: OverlayKernel
  passive: KernelBase
  empty: KernelBase
  source: Core
  peer: Core
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
    source_segments = self._program_for(self.bench).layout(
      core_xy=self.source,
      dispatch_mode=dispatch_mode,
      host_assigned_id=host_assigned_id,
    )
    peer_segments = self._program_for(self.passive).layout(
      core_xy=self.peer,
      dispatch_mode=dispatch_mode,
      host_assigned_id=host_assigned_id,
    )

    target_cores = [self.source, self.peer]
    reset_blob = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_RESET_READ_PTR_FROM_HOST)
    commands = [
      UnicastWrite(target_cores, TensixL1.GO_MSG, [reset_blob] * len(target_cores)),
      UnicastWrite(target_cores, TensixL1.GO_MSG_INDEX, [b"\0\0\0\0"] * len(target_cores)),
    ]
    for core, segments in ((self.source, source_segments), (self.peer, peer_segments)):
      for segment in segments:
        commands.append(UnicastWrite([core], segment.addr, [segment.data]))
    commands.append(Run(target_cores))
    return commands


def build_program(
  *, noc: int, stream_id: int, source: Core, peer: Core, byte_count: int, vc: int,
  ready_timeout_iters: int, done_timeout_iters: int,
) -> OverlayPairProgram:
  if source == peer:
    raise ValueError("source and peer must be distinct cores")
  passive = KernelBase().ret()
  empty = KernelBase()
  bench = OverlayKernel()
  emit_overlay_write(
    bench,
    noc=noc,
    stream_id=stream_id,
    peer_coord=noc_xy(*peer),
    byte_count=byte_count,
    vc=vc,
    ready_timeout_iters=ready_timeout_iters,
    done_timeout_iters=done_timeout_iters,
  )
  return OverlayPairProgram(
    bench=bench,
    passive=passive,
    empty=empty,
    source=source,
    peer=peer,
    name=f"riscv_noc_overlay_stream_poc:noc{noc}:stream{stream_id}:{source}->{peer}",
  )


def seed_payload(byte_count: int) -> bytes:
  out = bytearray(byte_count)
  for off in range(0, byte_count, 4):
    struct.pack_into("<I", out, off, 0xD00D0000 | ((off // 4) & 0xFFFF))
  return bytes(out)


def clear_and_seed(device, *, source: Core, peer: Core, byte_count: int):
  payload = seed_payload(byte_count)
  with harness.device_window(device, source) as win:
    win.write(RESULT_BASE, b"\0" * RESULT_SIZE)
    win.write(SRC_BUF_BASE, payload)
    win.write(MSG_INFO_BASE, b"\0" * 256)
  with harness.device_window(device, peer) as win:
    win.write(DST_BUF_BASE, b"\0" * byte_count)


def read_result(device, source: Core, byte_count: int) -> OverlayResult:
  blob = harness.read_window(device, source, RESULT_BASE, RESULT_SIZE)
  words = struct.unpack("<" + "I" * RESULT_WORDS, blob)
  if words[0] != RESULT_MAGIC or words[31] != RESULT_MAGIC:
    raise RuntimeError(f"bad result magic head=0x{words[0]:08x} tail=0x{words[31]:08x}")
  start = words[6] | (words[7] << 32)
  end = words[8] | (words[9] << 32)
  return OverlayResult(
    status=words[2],
    noc=words[3],
    stream_id=words[4],
    peer_coord=words[5],
    byte_count=byte_count,
    start=start,
    end=end,
    wr_ack_delta=(words[14] - words[10]) & 0xFFFFFFFF,
    posted_delta=(words[15] - words[11]) & 0xFFFFFFFF,
    nonposted_delta=(words[16] - words[12]) & 0xFFFFFFFF,
    rd_resp_delta=(words[17] - words[13]) & 0xFFFFFFFF,
    ready_remaining=words[20],
    done_remaining=words[21],
    wait_status=words[22],
    debug8=words[23],
    debug9=words[24],
    buf_space=words[25],
    remote_space=words[26],
    can_push=words[27],
    ready_for_push=words[28],
    src_first=words[29],
  )


def parse_result(device, source: Core, byte_count: int) -> OverlayResult:
  return read_result(device, source, byte_count)


def verify_payload(device, peer: Core, byte_count: int) -> tuple[bool, int, int]:
  got = harness.read_window(device, peer, DST_BUF_BASE, byte_count)
  expected = seed_payload(byte_count)
  first_bad = -1
  for i, (a, b) in enumerate(zip(got, expected, strict=True)):
    if a != b:
      first_bad = i
      break
  first = struct.unpack_from("<I", got, 0)[0] if byte_count >= 4 else 0
  last = struct.unpack_from("<I", got, byte_count - 4)[0] if byte_count >= 4 else 0
  return first_bad < 0, first, last


def format_summary(result: OverlayResult, *, source: Core, peer: Core, ok: bool, first: int, last: int) -> str:
  status_name = {
    STATUS_STARTED: "started",
    STATUS_READY_TIMEOUT: "ready-timeout",
    STATUS_DONE_TIMEOUT: "done-timeout",
    STATUS_DONE: "done",
  }.get(result.status, f"0x{result.status:08x}")
  lines = [
    "| source | peer | noc | stream | status | bytes | cycles | B/cyc | payload ok | first | last | wr ack d | posted d | nonposted d | rd resp d | wait | debug8 | debug9 | buf space | remote space | can push | ready push |",
    "|---|---|---:|---:|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    (
      f"| `{source[0]},{source[1]}` | `{peer[0]},{peer[1]}` | {result.noc} | {result.stream_id} | {status_name} | "
      f"{result.byte_count} | {result.cycles} | {result.bpc:.3f} | {ok} | 0x{first:08x} | 0x{last:08x} | "
      f"{result.wr_ack_delta} | {result.posted_delta} | {result.nonposted_delta} | {result.rd_resp_delta} | "
      f"0x{result.wait_status:08x} | 0x{result.debug8:08x} | 0x{result.debug9:08x} | "
      f"{result.buf_space} | {result.remote_space} | {result.can_push} | {result.ready_for_push} |"
    ),
  ]
  return "\n".join(lines)


def append_report(path: Path, *, source: Core, peer: Core, result: OverlayResult, ok: bool, first: int, last: int):
  harness.append_report(path, None, [
    "Scope: one-shot Blackhole NoC overlay source endpoint to remote L1 destination buffer",
    "Programming sequence mirrors tt-metal `tt-2xx/quasar/stream_interface.h::stream_dram_write`.",
    "Timing starts immediately before `STREAM_SOURCE_ENDPOINT_NEW_MSG_INFO` and ends after stream phase completion.",
  ], format_summary(result, source=source, peer=peer, ok=ok, first=first, last=last))


def main():
  parser = argparse.ArgumentParser(description="PoC Blackhole NoC overlay stream write from one Tensix L1 to another.")
  parser.add_argument("--source", type=harness.parse_core, default=(1, 2), help="source core X,Y")
  parser.add_argument("--peer", type=harness.parse_core, default=(2, 2), help="destination core X,Y")
  parser.add_argument("--noc", type=int, choices=(0, 1), default=0)
  parser.add_argument("--stream", type=int, default=8, help="overlay stream id to program, default: 8")
  parser.add_argument("--bytes", type=int, default=16 * 1024, help="payload bytes, multiple of 16; max 262128")
  parser.add_argument("--vc", type=int, default=1, help="unicast VC register value")
  parser.add_argument("--ready-timeout-iters", type=int, default=1_000_000)
  parser.add_argument("--done-timeout-iters", type=int, default=10_000_000)
  parser.add_argument("--no-report", action="store_true")
  parser.add_argument("--report", type=Path, default=harness.doc_path("noc", "noc-overlay-stream-poc.md"))
  args = parser.parse_args()

  if args.source == args.peer:
    raise ValueError("--source and --peer must be distinct")
  if not 0 <= args.stream < 64:
    raise ValueError("--stream must be in [0, 63]")
  if args.bytes <= 0 or args.bytes % MEM_WORD_WIDTH:
    raise ValueError("--bytes must be a positive multiple of 16")
  if args.bytes // MEM_WORD_WIDTH >= (1 << 14):
    raise ValueError("--bytes exceeds SOURCE_ENDPOINT_NEW_MSG_SIZE field")
  if args.bytes > RESULT_BASE - SRC_BUF_BASE:
    raise ValueError(f"--bytes overlaps result area; max is {RESULT_BASE - SRC_BUF_BASE}")
  if not 0 <= args.vc <= 5:
    raise ValueError("--vc should be in [0, 5]")

  with harness.open_device() as device:
    clear_and_seed(device, source=args.source, peer=args.peer, byte_count=args.bytes)
    program = build_program(
      noc=args.noc,
      stream_id=args.stream,
      source=args.source,
      peer=args.peer,
      byte_count=args.bytes,
      vc=args.vc,
      ready_timeout_iters=args.ready_timeout_iters,
      done_timeout_iters=args.done_timeout_iters,
    )
    device.run(program)
    result = parse_result(device, args.source, args.bytes)
    ok, first, last = verify_payload(device, args.peer, args.bytes)

  print(format_summary(result, source=args.source, peer=args.peer, ok=ok, first=first, last=last))
  if not args.no_report:
    append_report(args.report, source=args.source, peer=args.peer, result=result, ok=ok, first=first, last=last)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
