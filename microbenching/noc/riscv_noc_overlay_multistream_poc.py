#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
import riscv_noc_overlay_stream_poc as ovl  # noqa: E402
from asm import KernelBase  # noqa: E402
from dsl import a2, a3, a4, a5, a6, a7, s0, s1, s2, s3, s4, s5, s6, s7, t0, t1, t2, t3, t4, t5, t6, zero  # noqa: E402
from program import DevMsgs, Program, Run, UnicastWrite  # noqa: E402
from ttk.addrs import Core, noc_xy  # noqa: E402
from ttk.noc import NOC, Noc  # noqa: E402
from ttk.tensix import TensixL1  # noqa: E402


RESULT_BASE = 0x150000
SRC_BUF_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
DST_BUF_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
MSG_INFO_BASE = 0x130000
RESULT_WORDS = 64
RESULT_SIZE = RESULT_WORDS * 4
RESULT_MAGIC = 0x52534F4D  # "RSOM"
STATUS_STARTED = 0x52000001
STATUS_READY_TIMEOUT = 0x5200BAD1
STATUS_DONE_TIMEOUT = 0x5200BAD2
STATUS_DONE = 0x5200D00D


class MultiOverlayKernel(KernelBase, Noc):
  pass


@dataclass(frozen=True)
class MultiResult:
  status: int
  noc: int
  start_stream: int
  stream_count: int
  byte_count: int
  start: int
  end: int
  wr_ack_delta: int
  posted_delta: int
  nonposted_delta: int
  rd_resp_delta: int
  ready_remaining: int
  done_remaining: int
  wait_status_xor: int
  debug8_xor: int
  debug9_xor: int
  src_first_xor: int

  @property
  def cycles(self) -> int:
    return (self.end - self.start) & ((1 << 64) - 1)

  @property
  def total_bytes(self) -> int:
    return self.byte_count * self.stream_count

  @property
  def bpc(self) -> float:
    return self.total_bytes / self.cycles if self.cycles else 0.0


@dataclass
class MultiOverlayProgram:
  bench: MultiOverlayKernel
  passive: KernelBase
  empty: KernelBase
  source: Core
  peers: list[Core]
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
    target_cores = [self.source] + self.peers
    reset_blob = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_RESET_READ_PTR_FROM_HOST)
    commands = [
      UnicastWrite(target_cores, TensixL1.GO_MSG, [reset_blob] * len(target_cores)),
      UnicastWrite(target_cores, TensixL1.GO_MSG_INDEX, [b"\0\0\0\0"] * len(target_cores)),
    ]
    for core, brisc in [(self.source, self.bench), *[(peer, self.passive) for peer in self.peers]]:
      segments = self._program_for(brisc).layout(
        core_xy=core,
        dispatch_mode=dispatch_mode,
        host_assigned_id=host_assigned_id,
      )
      for segment in segments:
        commands.append(UnicastWrite([core], segment.addr, [segment.data]))
    commands.append(Run(target_cores))
    return commands


def emit_result_header(
  fw: KernelBase, *, status: int, noc: int, start_stream: int, stream_count: int, byte_count: int,
):
  fw.li(s2, RESULT_BASE)
  values = (
    RESULT_MAGIC, 1, status, noc, start_stream, stream_count, byte_count,
    byte_count * stream_count, SRC_BUF_BASE, DST_BUF_BASE, MSG_INFO_BASE,
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


def emit_program_one_stream(
  fw: MultiOverlayKernel, *, noc: int, stream_id: int, peer_coord: int,
  src_addr: int, dst_addr: int, msg_info_addr: int, byte_count: int, vc: int,
):
  word_count = byte_count // ovl.MEM_WORD_WIDTH
  src_word_addr = src_addr // ovl.MEM_WORD_WIDTH
  dst_word_addr = dst_addr // ovl.MEM_WORD_WIDTH
  msg_info_word_addr = msg_info_addr // ovl.MEM_WORD_WIDTH
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
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_PHASE_AUTO_CFG_HEADER_REG_INDEX), 1 << ovl.CURR_PHASE_NUM_MSGS)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_REMOTE_DEST_REG_INDEX), peer_coord & 0xFFF)
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


def emit_wait_all_ready(
  fw: MultiOverlayKernel, *, start_stream: int, stream_count: int, timeout_iters: int, timeout_label: str,
):
  fw.li(s0, timeout_iters)
  loop = fw._new_label("overlay_all_ready")
  done = fw._new_label("overlay_all_ready_done")
  next_try = fw._new_label("overlay_all_ready_next")
  fw.label(loop)
  for i in range(stream_count):
    stream_id = start_stream + i
    fw.read32(t0, ovl.stream_reg(stream_id, ovl.STREAM_DEBUG_STATUS_REG_INDEX + 8), tmp_addr=t3)
    fw.srli(t0, t0, 4)
    fw.andi(t0, t0, 0x7)
    fw.li(t1, ovl.SRC_READY_WAIT_ALL_DESTS)
    fw.bne(t0, t1, next_try)
  fw.j(done)
  fw.label(next_try)
  fw.addi(s0, s0, -1)
  fw.bne(s0, zero, loop)
  fw.j(timeout_label)
  fw.label(done)
  return fw


def emit_wait_all_done(
  fw: MultiOverlayKernel, *, start_stream: int, stream_count: int, timeout_iters: int, timeout_label: str,
):
  fw.li(s1, timeout_iters)
  loop = fw._new_label("overlay_all_done")
  done = fw._new_label("overlay_all_done_ok")
  next_try = fw._new_label("overlay_all_done_next")
  fw.label(loop)
  for i in range(stream_count):
    stream_id = start_stream + i
    fw.read32(t0, ovl.stream_reg(stream_id, ovl.STREAM_WAIT_STATUS_REG_INDEX), tmp_addr=t3)
    fw.andi(t0, t0, 1 << ovl.WAIT_SW_PHASE_ADVANCE_SIGNAL)
    fw.beq(t0, zero, next_try)
    fw.read32(t1, ovl.stream_reg(stream_id, ovl.STREAM_DEBUG_STATUS_REG_INDEX + 9), tmp_addr=t3)
    fw.srli(t1, t1, ovl.MEM_WORD_ADDR_WIDTH)
    fw.bne(t1, zero, next_try)
  fw.j(done)
  fw.label(next_try)
  fw.addi(s1, s1, -1)
  fw.bne(s1, zero, loop)
  fw.j(timeout_label)
  fw.label(done)
  return fw


def emit_debug_xors(fw: MultiOverlayKernel, *, start_stream: int, stream_count: int):
  fw.mv(s2, zero)
  fw.mv(s3, zero)
  fw.mv(s4, zero)
  fw.mv(s5, zero)
  for i in range(stream_count):
    stream_id = start_stream + i
    fw.read32(t0, ovl.stream_reg(stream_id, ovl.STREAM_WAIT_STATUS_REG_INDEX), tmp_addr=t3)
    fw.xor(s2, s2, t0)
    fw.read32(t0, ovl.stream_reg(stream_id, ovl.STREAM_DEBUG_STATUS_REG_INDEX + 8), tmp_addr=t3)
    fw.xor(s3, s3, t0)
    fw.read32(t0, ovl.stream_reg(stream_id, ovl.STREAM_DEBUG_STATUS_REG_INDEX + 9), tmp_addr=t3)
    fw.xor(s4, s4, t0)
    fw.read32(t0, SRC_BUF_BASE + i * 0x20000, tmp_addr=t3)
    fw.xor(s5, s5, t0)
  fw.li(t0, RESULT_BASE)
  for off, reg in ((24, s2), (25, s3), (26, s4), (27, s5)):
    fw.sw(reg, t0, off * 4)
  return fw


def build_kernel(
  *, noc: int, start_stream: int, peers: list[Core], byte_count: int, vc: int,
  ready_timeout_iters: int, done_timeout_iters: int,
) -> MultiOverlayKernel:
  stream_count = len(peers)
  fw = MultiOverlayKernel()
  emit_result_header(
    fw, status=STATUS_STARTED, noc=noc, start_stream=start_stream,
    stream_count=stream_count, byte_count=byte_count,
  )
  ready_timeout = fw._new_label("overlay_ready_timeout")
  done_timeout = fw._new_label("overlay_done_timeout")
  finish = fw._new_label("overlay_finish")
  for i, peer in enumerate(peers):
    emit_program_one_stream(
      fw,
      noc=noc,
      stream_id=start_stream + i,
      peer_coord=noc_xy(*peer),
      src_addr=SRC_BUF_BASE + i * 0x20000,
      dst_addr=DST_BUF_BASE,
      msg_info_addr=MSG_INFO_BASE + i * 0x100,
      byte_count=byte_count,
      vc=vc,
    )

  emit_wait_all_ready(
    fw, start_stream=start_stream, stream_count=stream_count,
    timeout_iters=ready_timeout_iters, timeout_label=ready_timeout,
  )

  emit_counter_read(fw, noc, NOC.NIU_MST_WR_ACK_RECEIVED, a6)
  emit_counter_read(fw, noc, NOC.NIU_MST_POSTED_WR_REQ_SENT, a7)
  emit_counter_read(fw, noc, NOC.NIU_MST_NONPOSTED_WR_REQ_SENT, s6)
  emit_counter_read(fw, noc, NOC.NIU_MST_RD_RESP_RECEIVED, s7)
  fw.li(t0, RESULT_BASE)
  for off, reg in ((12, a6), (13, a7), (14, s6), (15, s7)):
    fw.sw(reg, t0, off * 4)

  harness.read_wall_clock(fw, a2, a3)
  for i in range(stream_count):
    stream_id = start_stream + i
    src_word_addr = (SRC_BUF_BASE + i * 0x20000) // ovl.MEM_WORD_WIDTH
    word_count = byte_count // ovl.MEM_WORD_WIDTH
    fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_DEST_PHASE_READY_UPDATE_REG_INDEX), 1 << ovl.PHASE_READY_TWO_WAY_RESP)
    fw.write32(
      ovl.stream_reg(stream_id, ovl.STREAM_SOURCE_ENDPOINT_NEW_MSG_INFO_REG_INDEX),
      (src_word_addr << ovl.SOURCE_ENDPOINT_NEW_MSG_ADDR) | (word_count << ovl.SOURCE_ENDPOINT_NEW_MSG_SIZE),
    )
  emit_wait_all_done(
    fw, start_stream=start_stream, stream_count=stream_count,
    timeout_iters=done_timeout_iters, timeout_label=done_timeout,
  )
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
  for off, reg in ((8, a2), (9, a3), (10, a4), (11, a5), (20, s0), (21, s1)):
    fw.sw(reg, t0, off * 4)
  emit_counter_read(fw, noc, NOC.NIU_MST_WR_ACK_RECEIVED, a6)
  emit_counter_read(fw, noc, NOC.NIU_MST_POSTED_WR_REQ_SENT, a7)
  emit_counter_read(fw, noc, NOC.NIU_MST_NONPOSTED_WR_REQ_SENT, s6)
  emit_counter_read(fw, noc, NOC.NIU_MST_RD_RESP_RECEIVED, s7)
  fw.li(t0, RESULT_BASE)
  for off, reg in ((16, a6), (17, a7), (18, s6), (19, s7)):
    fw.sw(reg, t0, off * 4)
  emit_debug_xors(fw, start_stream=start_stream, stream_count=stream_count)
  fw.li(t1, RESULT_MAGIC)
  fw.sw(t1, t0, 63 * 4)
  return fw.ret()


def build_program(
  *, source: Core, peers: list[Core], noc: int, start_stream: int, byte_count: int, vc: int,
  ready_timeout_iters: int, done_timeout_iters: int,
) -> MultiOverlayProgram:
  bench = build_kernel(
    noc=noc,
    start_stream=start_stream,
    peers=peers,
    byte_count=byte_count,
    vc=vc,
    ready_timeout_iters=ready_timeout_iters,
    done_timeout_iters=done_timeout_iters,
  )
  return MultiOverlayProgram(
    bench=bench,
    passive=KernelBase().ret(),
    empty=KernelBase(),
    source=source,
    peers=peers,
    name=f"riscv_noc_overlay_multistream_poc:noc{noc}:streams{start_stream}+{len(peers)}",
  )


def seed_payload(byte_count: int, index: int) -> bytes:
  out = bytearray(byte_count)
  tag = (0xD10D0000 | ((index & 0xFF) << 8)) & 0xFFFFFFFF
  for off in range(0, byte_count, 4):
    struct.pack_into("<I", out, off, tag | ((off // 4) & 0xFF))
  return bytes(out)


def clear_and_seed(device, *, source: Core, peers: list[Core], byte_count: int):
  with harness.device_window(device, source) as win:
    win.write(RESULT_BASE, b"\0" * RESULT_SIZE)
    for i in range(len(peers)):
      win.write(SRC_BUF_BASE + i * 0x20000, seed_payload(byte_count, i))
      win.write(MSG_INFO_BASE + i * 0x100, b"\0" * 256)
  for peer in peers:
    with harness.device_window(device, peer) as win:
      win.write(DST_BUF_BASE, b"\0" * byte_count)


def verify_payloads(device, peers: list[Core], byte_count: int) -> tuple[int, list[tuple[Core, bool, int, int]]]:
  bad = 0
  rows = []
  for i, peer in enumerate(peers):
    got = harness.read_window(device, peer, DST_BUF_BASE, byte_count)
    expected = seed_payload(byte_count, i)
    ok = got == expected
    bad += 0 if ok else 1
    first = struct.unpack_from("<I", got, 0)[0] if byte_count >= 4 else 0
    last = struct.unpack_from("<I", got, byte_count - 4)[0] if byte_count >= 4 else 0
    rows.append((peer, ok, first, last))
  return bad, rows


def parse_result(device, source: Core) -> MultiResult:
  blob = harness.read_window(device, source, RESULT_BASE, RESULT_SIZE)
  words = struct.unpack("<" + "I" * RESULT_WORDS, blob)
  if words[0] != RESULT_MAGIC or words[63] != RESULT_MAGIC:
    raise RuntimeError(f"bad result magic head=0x{words[0]:08x} tail=0x{words[63]:08x}")
  start = words[8] | (words[9] << 32)
  end = words[10] | (words[11] << 32)
  return MultiResult(
    status=words[2],
    noc=words[3],
    start_stream=words[4],
    stream_count=words[5],
    byte_count=words[6],
    start=start,
    end=end,
    wr_ack_delta=(words[16] - words[12]) & 0xFFFFFFFF,
    posted_delta=(words[17] - words[13]) & 0xFFFFFFFF,
    nonposted_delta=(words[18] - words[14]) & 0xFFFFFFFF,
    rd_resp_delta=(words[19] - words[15]) & 0xFFFFFFFF,
    ready_remaining=words[20],
    done_remaining=words[21],
    wait_status_xor=words[24],
    debug8_xor=words[25],
    debug9_xor=words[26],
    src_first_xor=words[27],
  )


def format_summary(result: MultiResult, *, source: Core, payload_bad: int, payload_rows):
  status_name = {
    STATUS_STARTED: "started",
    STATUS_READY_TIMEOUT: "ready-timeout",
    STATUS_DONE_TIMEOUT: "done-timeout",
    STATUS_DONE: "done",
  }.get(result.status, f"0x{result.status:08x}")
  lines = [
    "| source | noc | streams | status | bytes/stream | total bytes | cycles | B/cyc | bad payloads | wr ack d | posted d | nonposted d | rd resp d | wait xor | debug8 xor | debug9 xor |",
    "|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    (
      f"| `{source[0]},{source[1]}` | {result.noc} | {result.stream_count} | {status_name} | "
      f"{result.byte_count} | {result.total_bytes} | {result.cycles} | {result.bpc:.3f} | {payload_bad} | "
      f"{result.wr_ack_delta} | {result.posted_delta} | {result.nonposted_delta} | {result.rd_resp_delta} | "
      f"0x{result.wait_status_xor:08x} | 0x{result.debug8_xor:08x} | 0x{result.debug9_xor:08x} |"
    ),
    "",
    "| peer | payload ok | first | last |",
    "|---|---|---:|---:|",
  ]
  for peer, ok, first, last in payload_rows:
    lines.append(f"| `{peer[0]},{peer[1]}` | {ok} | 0x{first:08x} | 0x{last:08x} |")
  return "\n".join(lines)


def append_report(path: Path, *, result: MultiResult, source: Core, payload_bad: int, payload_rows):
  harness.append_report(path, None, [
    "Scope: arm multiple Blackhole NoC overlay source-endpoint streams on one source core.",
    "Each stream writes a distinct source L1 buffer to one peer L1 destination buffer.",
    "Timing starts before the first `STREAM_SOURCE_ENDPOINT_NEW_MSG_INFO` and ends after all stream phases complete.",
  ], format_summary(result, source=source, payload_bad=payload_bad, payload_rows=payload_rows))


def parse_core_list(values: list[str]) -> list[Core]:
  return [harness.parse_core(value) for value in values]


def default_peers(device, source: Core, count: int) -> list[Core]:
  sx, sy = source
  same_row = [core for core in sorted(device.cores) if core[1] == sy and core != source]
  right = [core for core in same_row if core[0] > sx]
  left = [core for core in same_row if core[0] < sx]
  peers = right + left
  if len(peers) < count:
    raise ValueError(f"need {count} peers on row y={sy}; only found {len(peers)}")
  return peers[:count]


def main():
  parser = argparse.ArgumentParser(description="Arm multiple Blackhole NoC overlay streams from one source core.")
  parser.add_argument("--source", type=harness.parse_core, default=(1, 2))
  parser.add_argument("--peers", nargs="*", default=None, help="destination cores as X,Y values; overrides --count")
  parser.add_argument("--count", type=int, default=2, help="default peer count from source row")
  parser.add_argument("--noc", type=int, choices=(0, 1), default=0)
  parser.add_argument("--start-stream", type=int, default=8)
  parser.add_argument("--bytes", type=int, default=16 * 1024)
  parser.add_argument("--vc", type=int, default=1)
  parser.add_argument("--ready-timeout-iters", type=int, default=1_000_000)
  parser.add_argument("--done-timeout-iters", type=int, default=10_000_000)
  parser.add_argument("--no-report", action="store_true")
  parser.add_argument("--report", type=Path, default=harness.doc_path("noc", "noc-overlay-multistream-poc.md"))
  args = parser.parse_args()

  if args.bytes <= 0 or args.bytes % ovl.MEM_WORD_WIDTH:
    raise ValueError("--bytes must be a positive multiple of 16")
  if args.bytes // ovl.MEM_WORD_WIDTH >= (1 << 14):
    raise ValueError("--bytes exceeds SOURCE_ENDPOINT_NEW_MSG_SIZE field")
  if args.count <= 0:
    raise ValueError("--count must be positive")
  if not 0 <= args.start_stream < 64:
    raise ValueError("--start-stream must be in [0, 63]")
  if not 0 <= args.vc <= 5:
    raise ValueError("--vc should be in [0, 5]")

  with harness.open_device() as device:
    peers = parse_core_list(args.peers) if args.peers else default_peers(device, args.source, args.count)
    if args.source in peers:
      raise ValueError("--peers must not include --source")
    if args.start_stream + len(peers) > 64:
      raise ValueError("stream range exceeds 64 overlay streams")
    if args.bytes > 0x20000:
      raise ValueError("--bytes must be <= 128 KiB with current source stride")
    live = set(device.cores)
    missing = [core for core in [args.source] + peers if core not in live]
    if missing:
      raise ValueError(f"cores are not live program cores: {missing}")
    if SRC_BUF_BASE + len(peers) * 0x20000 > RESULT_BASE:
      raise ValueError("source buffers overlap result area")
    clear_and_seed(device, source=args.source, peers=peers, byte_count=args.bytes)
    program = build_program(
      source=args.source,
      peers=peers,
      noc=args.noc,
      start_stream=args.start_stream,
      byte_count=args.bytes,
      vc=args.vc,
      ready_timeout_iters=args.ready_timeout_iters,
      done_timeout_iters=args.done_timeout_iters,
    )
    device.run(program)
    result = parse_result(device, args.source)
    payload_bad, payload_rows = verify_payloads(device, peers, args.bytes)

  print(format_summary(result, source=args.source, payload_bad=payload_bad, payload_rows=payload_rows))
  if not args.no_report:
    append_report(args.report, result=result, source=args.source, payload_bad=payload_bad, payload_rows=payload_rows)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
