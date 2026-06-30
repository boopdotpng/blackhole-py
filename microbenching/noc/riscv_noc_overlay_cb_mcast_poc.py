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
from dsl import a2, a3, a4, a5, a6, a7, s0, s1, s2, s3, s4, s5, s6, s7, t0, t1, t2, t3, t4, t5, t6, zero  # noqa: E402
from program import DevMsgs, Program, Run, UnicastWrite  # noqa: E402
from ttk import Cb  # noqa: E402
from ttk.addrs import Core, noc_xy  # noqa: E402
from ttk.cb import CB  # noqa: E402
from ttk.mailbox import BriscMailbox as BM  # noqa: E402
from ttk.noc import NOC, Noc  # noqa: E402
from ttk.tensix import TensixL1  # noqa: E402


RESULT_BASE = 0x150000
RESULT_MAGIC = 0x43424F4D  # "MOBC"
STATUS_STARTED = 0x43000001
STATUS_SOURCE_SEEDED = 0x43000002
STATUS_SOURCE_WAIT_READY = 0x43000003
STATUS_SOURCE_MCAST = 0x43000004
STATUS_SOURCE_RELEASE = 0x43000005
STATUS_RECV_STARTED = 0x43000101
STATUS_RECV_RESERVED = 0x43000102
STATUS_RECV_SIGNALED = 0x43000103
STATUS_RECV_DONE = 0x43000104
STATUS_DONE = 0x4300D00D
STATUS_READY_TIMEOUT = 0x4300BAD1
STATUS_DONE_TIMEOUT = 0x4300BAD2
RESULT_WORDS = 32
RESULT_SIZE = RESULT_WORDS * 4
CB_INDEX = 0
CB_PAGE_BYTES = 2048
SEM_DATA_READY = 0
SEM_RECV_READY = 1


class OverlayCbMcastKernel(KernelBase, Noc, Cb):
  pass


@dataclass
class OverlayCbMcastProgram:
  source_kernel: OverlayCbMcastKernel
  receiver_kernel: OverlayCbMcastKernel
  empty: KernelBase
  source: Core
  receivers: tuple[Core, ...]
  receivers2: tuple[Core, ...]
  byte_count: int
  name: str

  def _program_for(self, brisc: KernelBase) -> Program:
    pages = self.byte_count // CB_PAGE_BYTES
    return Program(
      brisc=brisc,
      ncrisc=self.empty,
      trisc0=self.empty,
      trisc1=self.empty,
      trisc2=self.empty,
      cbs=[(CB_INDEX, CB_PAGE_BYTES, pages)],
      semaphores=2,
      num_cores=1,
    )

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    active = [self.source, *self.receivers, *self.receivers2]
    reset_blob = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_RESET_READ_PTR_FROM_HOST)
    commands = [
      UnicastWrite(active, TensixL1.GO_MSG, [reset_blob] * len(active)),
      UnicastWrite(active, TensixL1.GO_MSG_INDEX, [b"\0\0\0\0"] * len(active)),
    ]
    all_receivers = (*self.receivers, *self.receivers2)
    for core, brisc in [(self.source, self.source_kernel), *[(receiver, self.receiver_kernel) for receiver in all_receivers]]:
      segments = self._program_for(brisc).layout(
        core_xy=core,
        dispatch_mode=dispatch_mode,
        host_assigned_id=host_assigned_id,
      )
      for segment in segments:
        if dispatch_mode == DevMsgs.DISPATCH_MODE_HOST and segment.addr >= 0xFFB00000:
          continue
        commands.append(UnicastWrite([core], segment.addr, [segment.data]))
    commands.append(Run(active))
    return commands


def emit_counter_read(fw: KernelBase, noc: int, counter: int, out, *, addr=t3):
  fw.li(addr, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  return fw.lw(out, addr, 0)


def emit_result_header(fw: OverlayCbMcastKernel, *, status: int, noc: int, stream_id: int, byte_count: int, dest_count: int):
  fw.li(s2, RESULT_BASE)
  values = (
    RESULT_MAGIC, status, noc, stream_id, byte_count, dest_count,
    TensixL1.DATA_BUFFER_SPACE_BASE, CB_PAGE_BYTES,
  )
  for off, value in enumerate(values):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off in range(len(values), RESULT_WORDS):
    fw.sw(zero, s2, off * 4)
  return fw


def emit_status_word(fw: OverlayCbMcastKernel, status: int, *, off: int = 1):
  fw.li(t0, status)
  return fw.write32(RESULT_BASE + off * 4, t0, tmp_addr=t1, tmp_val=t2)


def emit_wait_counter_at_least(fw: OverlayCbMcastKernel, *, noc: int, counter: int, target, timeout_iters: int, timeout_label: str):
  fw.li(t3, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  fw.li(t4, timeout_iters)
  loop = fw._new_label("wait_counter")
  done = fw._new_label("wait_counter_done")
  fw.label(loop)
  fw.lw(t5, t3, 0)
  fw.bgeu(t5, target, done)
  fw.addi(t4, t4, -1)
  fw.beq(t4, zero, timeout_label)
  fw.j(loop)
  fw.label(done)
  return fw


def emit_overlay_mcast(
  fw: OverlayCbMcastKernel, *, noc: int, stream_id: int, rect: mcast.McastRect,
  byte_count: int, path_reserve: bool, ready_timeout_iters: int, done_timeout_iters: int,
  ready_timeout_label: str, done_timeout_label: str,
):
  word_count = byte_count // ovl.MEM_WORD_WIDTH
  msg_info_word_addr = 0x130000 // ovl.MEM_WORD_WIDTH
  src_word_addr = TensixL1.DATA_BUFFER_SPACE_BASE // ovl.MEM_WORD_WIDTH
  mcast_dest = (
    (rect.x1 << ovl.STREAM_MCAST_END_X)
    | (rect.y1 << ovl.STREAM_MCAST_END_Y)
    | (1 << ovl.STREAM_MCAST_EN)
    | (1 << ovl.STREAM_MCAST_VC)
    | (0 if path_reserve else (1 << ovl.STREAM_MCAST_NO_PATH_RES))
  )
  emit_counter_read(fw, noc, NOC.NIU_MST_POSTED_WR_REQ_SENT, s6)
  fw.addi(s6, s6, (byte_count + NOC.MAX_BURST_SIZE - 1) // NOC.MAX_BURST_SIZE)

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
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_MCAST_DEST_NUM_REG_INDEX), 1)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_MCAST_DEST_REG_INDEX), mcast_dest)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_GATHER_REG_INDEX), 0)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_MSG_SRC_IN_ORDER_FWD_NUM_MSGS_REG_INDEX), 0)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_PHASE_AUTO_CFG_HEADER_REG_INDEX), 1 << ovl.CURR_PHASE_NUM_MSGS)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_REMOTE_DEST_REG_INDEX), noc_xy(rect.x0, rect.y0))
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_REMOTE_DEST_BUF_START_HI_REG_INDEX), src_word_addr >> ovl.MEM_WORD_ADDR_WIDTH)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_REMOTE_DEST_BUF_START_REG_INDEX), src_word_addr)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_REMOTE_DEST_BUF_SIZE_REG_INDEX), word_count)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_BUF_START_REG_INDEX), src_word_addr)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_BUF_SIZE_REG_INDEX), word_count)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_MSG_INFO_PTR_REG_INDEX), msg_info_word_addr)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_MSG_INFO_WR_PTR_REG_INDEX), msg_info_word_addr)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_REMOTE_DEST_TRAFFIC_REG_INDEX), 5 << ovl.UNICAST_VC_REG)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_MISC_CFG_REG_INDEX), misc_cfg)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_ONETIME_MISC_CFG_REG_INDEX), onetime_cfg)
  fw.write32(ovl.stream_reg(stream_id, ovl.STREAM_PHASE_ADVANCE_REG_INDEX), 1)
  ovl.emit_wait_src_ready(fw, stream_id=stream_id, timeout_iters=ready_timeout_iters, timeout_label=ready_timeout_label)
  fw.write32(
    ovl.stream_reg(stream_id, ovl.STREAM_DEST_PHASE_READY_UPDATE_REG_INDEX),
    (1 << ovl.PHASE_READY_MCAST) | (1 << ovl.PHASE_READY_TWO_WAY_RESP),
  )
  fw.write32(
    ovl.stream_reg(stream_id, ovl.STREAM_SOURCE_ENDPOINT_NEW_MSG_INFO_REG_INDEX),
    (src_word_addr << ovl.SOURCE_ENDPOINT_NEW_MSG_ADDR) | (word_count << ovl.SOURCE_ENDPOINT_NEW_MSG_SIZE),
  )
  ovl.emit_wait_stream_done(fw, stream_id=stream_id, timeout_iters=done_timeout_iters, timeout_label=done_timeout_label)
  emit_wait_counter_at_least(
    fw, noc=noc, counter=NOC.NIU_MST_POSTED_WR_REQ_SENT, target=s6,
    timeout_iters=done_timeout_iters, timeout_label=done_timeout_label,
  )
  return fw


def emit_normal_mcast(fw: OverlayCbMcastKernel, *, noc: int, rect: mcast.McastRect, byte_count: int):
  chunks = (byte_count + NOC.MAX_BURST_SIZE - 1) // NOC.MAX_BURST_SIZE
  fw.noc_mcast_coord(a5, rect.x0, rect.y0, rect.x1, rect.y1)
  fw.read32(s6, NOC.STATUS_BASE + NOC.NIU_MST_NONPOSTED_WR_REQ_SENT + (noc << NOC.INSTANCE_OFFSET_BIT), tmp_addr=t3)
  fw.addi(s6, s6, chunks)
  fw.li(s4, 0)
  loop = fw._new_label("normal_mcast_loop")
  done = fw._new_label("normal_mcast_done")
  fw.label(loop)
  fw.li(t0, chunks)
  fw.beq(s4, t0, done)
  fw.li(t1, NOC.MAX_BURST_SIZE)
  fw.li(t2, chunks - 1)
  not_last = fw._new_label("normal_mcast_not_last")
  size_ready = fw._new_label("normal_mcast_size_ready")
  fw.bne(s4, t2, not_last)
  fw.li(t1, byte_count - (chunks - 1) * NOC.MAX_BURST_SIZE)
  fw.j(size_ready)
  fw.label(not_last)
  fw.li(t1, NOC.MAX_BURST_SIZE)
  fw.label(size_ready)
  fw.slli(t2, s4, 14)
  fw.add(t2, s0, t2)
  fw.noc_write(noc, 0, t2, t2, 0, a5, t1, mcast=True, a=t3, v=t4)
  fw.addi(s4, s4, 1)
  fw.j(loop)
  fw.label(done)
  return fw.noc_nonposted_writes_flushed(noc, s6, addr=t3, val=t4)


def seed_payload(byte_count: int) -> bytes:
  words = byte_count // 4
  return struct.pack("<" + "I" * words, *[(0xE77A0000 + i) & 0xFFFFFFFF for i in range(words)])


def source_kernel(
  *, noc: int, stream_id: int, rect: mcast.McastRect, rect2: mcast.McastRect | None, byte_count: int, dest_count: int,
  path_reserve: bool, ready_timeout_iters: int, done_timeout_iters: int, mode: str,
) -> OverlayCbMcastKernel:
  fw = OverlayCbMcastKernel()
  pages = byte_count // CB_PAGE_BYTES
  emit_result_header(fw, status=STATUS_STARTED, noc=noc, stream_id=stream_id, byte_count=byte_count, dest_count=dest_count)
  fw.setup_local_cbs(BM.CB_INTERFACE)
  fw.sem_addr(BM.SEM_L1_BASE, SEM_RECV_READY, out=s1)
  fw.noc_semaphore_set(s1, 0)
  fw.cb_reserve_back(BM.CB_INTERFACE, CB_INDEX, pages)
  fw.cb_write_ptr(BM.CB_INTERFACE, CB_INDEX, out=s0)

  fw.li(s2, byte_count // 4)
  fw.li(s3, 0)
  seed_loop = fw._new_label("seed_loop")
  seed_done = fw._new_label("seed_done")
  fw.label(seed_loop)
  fw.beq(s3, s2, seed_done)
  fw.li(t0, 0xE77A0000)
  fw.add(t0, t0, s3)
  fw.slli(t1, s3, 2)
  fw.add(t1, s0, t1)
  fw.sw(t0, t1, 0)
  fw.addi(s3, s3, 1)
  fw.j(seed_loop)
  fw.label(seed_done)
  fw.fence()
  emit_status_word(fw, STATUS_SOURCE_SEEDED)

  emit_status_word(fw, STATUS_SOURCE_WAIT_READY)
  fw.noc_semaphore_wait(s1, dest_count)

  emit_status_word(fw, STATUS_SOURCE_MCAST)
  ready_timeout = fw._new_label("ready_timeout")
  done_timeout = fw._new_label("done_timeout")
  finish = fw._new_label("finish")
  for send_rect in (rect, rect2):
    if send_rect is None:
      continue
    if mode == "overlay":
      emit_overlay_mcast(
        fw, noc=noc, stream_id=stream_id, rect=send_rect, byte_count=byte_count,
        path_reserve=path_reserve, ready_timeout_iters=ready_timeout_iters,
        done_timeout_iters=done_timeout_iters, ready_timeout_label=ready_timeout,
        done_timeout_label=done_timeout,
      )
    else:
      emit_normal_mcast(fw, noc=noc, rect=send_rect, byte_count=byte_count)
  emit_status_word(fw, STATUS_SOURCE_RELEASE)
  fw.sem_addr(BM.SEM_L1_BASE, SEM_DATA_READY, out=a4)
  for send_rect in (rect, rect2):
    if send_rect is None:
      continue
    fw.noc_mcast_coord(a5, send_rect.x0, send_rect.y0, send_rect.x1, send_rect.y1)
    fw.noc_semaphore_set_multicast(noc, 0, a4, a5, 1, t0, a=t1, v=t2)
  fw.cb_push_back(BM.CB_INTERFACE, CB_INDEX, pages)
  emit_status_word(fw, STATUS_DONE)
  fw.j(finish)

  fw.label(ready_timeout)
  emit_status_word(fw, STATUS_READY_TIMEOUT)
  fw.j(finish)

  fw.label(done_timeout)
  emit_status_word(fw, STATUS_DONE_TIMEOUT)

  fw.label(finish)
  fw.li(t0, RESULT_MAGIC)
  fw.write32(RESULT_BASE + (RESULT_WORDS - 1) * 4, t0, tmp_addr=t1, tmp_val=t2)
  return fw.ret()


def receiver_kernel(*, noc: int, source: Core) -> OverlayCbMcastKernel:
  fw = OverlayCbMcastKernel()
  emit_result_header(fw, status=STATUS_RECV_STARTED, noc=noc, stream_id=0, byte_count=0, dest_count=0)
  fw.setup_local_cbs(BM.CB_INTERFACE)
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s7,))
  fw.cb_reserve_back(BM.CB_INTERFACE, CB_INDEX, s7)
  emit_status_word(fw, STATUS_RECV_RESERVED)
  fw.sem_addr(BM.SEM_L1_BASE, SEM_DATA_READY, out=s1)
  fw.noc_semaphore_set(s1, 0)
  fw.sem_addr(BM.SEM_L1_BASE, SEM_RECV_READY, out=s2)
  fw.noc_coord(a5, source[0], source[1])
  fw.local_noc0_coord(a6)
  fw.noc_semaphore_inc(noc, 3, s2, a5, 1, ret_coord=a6, a=t3, v=t4)
  emit_status_word(fw, STATUS_RECV_SIGNALED)
  fw.noc_semaphore_wait(s1, 1)
  fw.cb_push_back(BM.CB_INTERFACE, CB_INDEX, s7)
  emit_status_word(fw, STATUS_RECV_DONE)
  fw.li(t0, RESULT_MAGIC)
  fw.write32(RESULT_BASE + (RESULT_WORDS - 1) * 4, t0, tmp_addr=t1, tmp_val=t2)
  return fw.ret()


def build_program(
  *, source: Core, receivers: tuple[Core, ...], receivers2: tuple[Core, ...], noc: int, stream_id: int,
  rect: mcast.McastRect, rect2: mcast.McastRect | None,
  byte_count: int, path_reserve: bool, ready_timeout_iters: int, done_timeout_iters: int, mode: str,
) -> OverlayCbMcastProgram:
  pages = byte_count // CB_PAGE_BYTES
  src = source_kernel(
    noc=noc, stream_id=stream_id, rect=rect, rect2=rect2, byte_count=byte_count,
    dest_count=len(receivers) + len(receivers2), path_reserve=path_reserve,
    ready_timeout_iters=ready_timeout_iters, done_timeout_iters=done_timeout_iters,
    mode=mode,
  )
  recv = receiver_kernel(noc=noc, source=source)
  src.rta(lambda _x, _y: [pages])
  recv.rta(lambda _x, _y: [pages])
  return OverlayCbMcastProgram(
    source_kernel=src,
    receiver_kernel=recv,
    empty=KernelBase(),
    source=source,
    receivers=receivers,
    receivers2=receivers2,
    byte_count=byte_count,
    name=f"riscv_noc_overlay_cb_mcast_poc:noc{noc}:stream{stream_id}:dests{len(receivers) + len(receivers2)}",
  )


def parse_core(text: str) -> Core:
  x, y = text.split(",", 1)
  return int(x), int(y)


def parse_core_list(text: str) -> tuple[Core, ...]:
  return tuple(parse_core(part) for part in text.split(";") if part)


def validate_payloads(device, receivers: tuple[Core, ...], byte_count: int) -> tuple[int, list[tuple[Core, bool, int, int]]]:
  expected = seed_payload(byte_count)
  bad = 0
  rows = []
  for receiver in receivers:
    got = harness.read_window(device, receiver, TensixL1.DATA_BUFFER_SPACE_BASE, byte_count)
    ok = got == expected
    bad += 0 if ok else 1
    first = struct.unpack_from("<I", got, 0)[0] if byte_count >= 4 else 0
    last = struct.unpack_from("<I", got, byte_count - 4)[0] if byte_count >= 4 else 0
    rows.append((receiver, ok, first, last))
  return bad, rows


def read_status_words(device, cores: tuple[Core, ...] | list[Core]) -> list[tuple[Core, int, int]]:
  out = []
  for core in cores:
    try:
      blob = harness.read_window(device, core, RESULT_BASE, RESULT_SIZE)
      words = struct.unpack("<" + "I" * RESULT_WORDS, blob)
      out.append((core, words[0], words[1]))
    except Exception:
      out.append((core, 0, 0))
  return out


def main() -> None:
  parser = argparse.ArgumentParser(description="CB-backed Blackhole NoC overlay mcast handoff PoC.")
  parser.add_argument("--source", type=parse_core, default=(1, 2))
  parser.add_argument("--receivers", type=parse_core_list, required=True)
  parser.add_argument("--receivers2", type=parse_core_list, default=())
  parser.add_argument("--noc", type=int, choices=(0, 1), default=0)
  parser.add_argument("--stream", type=int, default=0)
  parser.add_argument("--bytes", type=int, default=196608)
  parser.add_argument("--mode", choices=("overlay", "normal"), default="overlay")
  parser.add_argument("--no-path-reserve", action="store_true")
  parser.add_argument("--ready-timeout-iters", type=int, default=1_000_000)
  parser.add_argument("--done-timeout-iters", type=int, default=10_000_000)
  args = parser.parse_args()

  if args.bytes <= 0 or args.bytes % CB_PAGE_BYTES:
    raise ValueError(f"--bytes must be a positive multiple of {CB_PAGE_BYTES}")
  if args.bytes // ovl.MEM_WORD_WIDTH >= (1 << 14):
    raise ValueError("--bytes exceeds SOURCE_ENDPOINT_NEW_MSG_SIZE field")
  if args.stream not in range(4):
    raise ValueError("--stream must be in [0, 3] for mcast-capable streams")

  with harness.open_device() as device:
    live = set(device.cores)
    missing = [core for core in (args.source, *args.receivers, *args.receivers2) if core not in live]
    if missing:
      raise ValueError(f"cores are not live program cores: {missing}")
    cmap = mcast.read_tensix_coordinate_map(device)
    rect = mcast.logical_rect_for_physical_span(args.receivers, noc=args.noc, cmap=cmap)
    rect2 = mcast.logical_rect_for_physical_span(args.receivers2, noc=args.noc, cmap=cmap) if args.receivers2 else None
    program = build_program(
      source=args.source,
      receivers=args.receivers,
      receivers2=args.receivers2,
      noc=args.noc,
      stream_id=args.stream,
      rect=rect,
      rect2=rect2,
      byte_count=args.bytes,
      path_reserve=not args.no_path_reserve,
      ready_timeout_iters=args.ready_timeout_iters,
      done_timeout_iters=args.done_timeout_iters,
      mode=args.mode,
    )
    try:
      device.run(program)
    except Exception:
      print("| core | magic | status |")
      print("|---|---:|---:|")
      for core, magic, status in read_status_words(device, [args.source, *args.receivers, *args.receivers2]):
        print(f"| `{core[0]},{core[1]}` | 0x{magic:08x} | 0x{status:08x} |")
      raise
    bad, rows = validate_payloads(device, (*args.receivers, *args.receivers2), args.bytes)

  print("| source | noc | stream | rect | dests | bytes | bad payloads |")
  print("|---|---:|---:|---|---:|---:|---:|")
  rect_label = f"{rect.x0},{rect.y0}->{rect.x1},{rect.y1}"
  if rect2 is not None:
    rect_label += f"; {rect2.x0},{rect2.y0}->{rect2.x1},{rect2.y1}"
  print(f"| `{args.source[0]},{args.source[1]}` | {args.noc} | {args.stream} | `{rect_label}` | {len(args.receivers) + len(args.receivers2)} | {args.bytes} | {bad} |")
  print("\n| receiver | payload ok | first | last |")
  print("|---|---|---:|---:|")
  for receiver, ok, first, last in rows:
    print(f"| `{receiver[0]},{receiver[1]}` | {ok} | 0x{first:08x} | 0x{last:08x} |")
  if bad:
    raise SystemExit(1)


if __name__ == "__main__":
  main()
