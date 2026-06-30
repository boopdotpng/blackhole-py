#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
from asm import KernelBase  # noqa: E402
from device import Device  # noqa: E402
from dsl import a2, a3, a4, a5, s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, t0, t1, t3, t4, t5, t6, zero  # noqa: E402
from program import DevMsgs, Program, Run, UnicastWrite  # noqa: E402
from ttk.addrs import Core, noc_xy  # noqa: E402
from ttk.mailbox import BriscMailbox as BM  # noqa: E402
from ttk.noc import NOC, Noc  # noqa: E402
from ttk.tensix import TensixL1  # noqa: E402


RESULT_BASE = 0x150000
STREAM_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
MARKER_VALUE = 0xC071000D
MARKER_SRC_ADDR = STREAM_BASE + NOC.MAX_BURST_SIZE
MARKER_DST_ADDR = MARKER_SRC_ADDR

RESULT_MAGIC = 0x434E5452  # "CNTR"
STATUS_STARTED = 0xC7000001
STATUS_DONE = 0xC700D00D
ROLE_SENDER = 1
ROLE_RECEIVER = 2
ROLE_SAMPLER = 3

HEADER_WORDS = 16
SNAP_COUNTER_WORDS = 20
FLIT_VCS = 16
FLIT_WORDS = FLIT_VCS * 4
SNAP_WORDS = SNAP_COUNTER_WORDS + FLIT_WORDS
SNAP_BEFORE = HEADER_WORDS
SNAP_AFTER = SNAP_BEFORE + SNAP_WORDS
RESULT_WORDS = HEADER_WORDS + 2 * SNAP_WORDS
RESULT_SIZE = RESULT_WORDS * 4

BRCST_SRC_INCLUDE = 1 << 17
ARB_PRIORITY_SHIFT = 27

SNAP_NAMES = (
  "cmd_buf_avail",
  "cmd_buf_ovfl",
  "mst_cmd_accepted",
  "mst_nonposted_wr_req_started",
  "mst_nonposted_wr_req_sent",
  "mst_nonposted_wr_data_word_sent",
  "mst_posted_wr_req_started",
  "mst_posted_wr_req_sent",
  "mst_posted_wr_data_word_sent",
  "mst_wr_ack_received",
  "mst_reqs_outstanding_id0",
  "mst_write_reqs_outgoing_id0",
  "slv_req_accepted",
  "slv_nonposted_wr_req_received",
  "slv_nonposted_wr_data_word_received",
  "slv_posted_wr_req_received",
  "slv_posted_wr_data_word_received",
  "slv_wr_ack_sent",
  "slv_rd_req_received",
)


@dataclass(frozen=True)
class Result:
  core: Core
  words: tuple[int, ...]

  @property
  def role(self) -> int:
    return self.words[1]

  @property
  def start(self) -> int:
    return self.words[8] | (self.words[9] << 32)

  @property
  def end(self) -> int:
    return self.words[10] | (self.words[11] << 32)


class CounterKernel(KernelBase, Noc):
  def noc_write_ctrl(self, *, noc: int, ctrl, src, dst_lo, dst_coord, length, a=t3, v=t4):
    self.noc_wait_cmd_ready(noc, 0, addr=a, val=v)
    self.noc_cmd_reg(noc, 0, NOC.CTRL, ctrl, addr=a, tmp=v)
    self.noc_cmd_reg(noc, 0, NOC.TARG_ADDR_LO, src, addr=a, tmp=v)
    self.noc_cmd_reg(noc, 0, NOC.TARG_ADDR_MID, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, 0, NOC.RET_ADDR_LO, dst_lo, addr=a, tmp=v)
    self.noc_cmd_reg(noc, 0, NOC.RET_ADDR_MID, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, 0, NOC.RET_ADDR_COORDINATE, dst_coord, addr=a, tmp=v)
    self.noc_cmd_reg(noc, 0, NOC.AT_LEN_BE, length, addr=a, tmp=v)
    self.noc_cmd_reg(noc, 0, NOC.AT_LEN_BE_1, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, 0, NOC.CMD_CTRL, NOC.CTRL_SEND_REQ, addr=a, tmp=v)
    return self


def ctrl_word(*, vc: int, priority: int, posted: bool) -> int:
  ctrl = NOC.CMD_CPY | NOC.CMD_WR | NOC.CMD_VC_STATIC | (vc << 13) | (priority << ARB_PRIORITY_SHIFT)
  if not posted:
    ctrl |= NOC.CMD_RESP_MARKED
  return ctrl


def emit_header(fw: CounterKernel, *, role: int, noc: int, vc: int, priority: int,
                packets: int, packet_bytes: int, samples: int, posted: bool):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, role, STATUS_STARTED, noc, vc, priority, packets, packet_bytes,
    0, 0, 0, 0, samples, int(posted), 0, 0,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off in range(HEADER_WORDS, RESULT_WORDS):
    fw.sw(zero, s2, off * 4)
  return fw


def emit_status(fw: CounterKernel, status: int):
  fw.li(s2, RESULT_BASE)
  fw.li(t0, status)
  fw.sw(t0, s2, 2 * 4)
  return fw


def emit_reset_debug_counters(fw: CounterKernel, noc: int):
  value = (1 << NOC.ROUTER_OUTGOING_FLIT_COUNTER_BIT) | (1 << NOC.CMD_BUFFER_FIFO_OVFL_CLEAR_BIT)
  return fw.write32(NOC.CFG_DEBUG_COUNTER_RESET + (noc << NOC.INSTANCE_OFFSET_BIT), value, tmp_addr=t3, tmp_val=t4)


def emit_reg_read(fw: CounterKernel, addr: int, out, *, noc: int, tmp=t3):
  fw.li(tmp, addr + (noc << NOC.INSTANCE_OFFSET_BIT))
  return fw.lw(out, tmp, 0)


def emit_status_read(fw: CounterKernel, offset: int, out, *, noc: int, tmp=t3):
  fw.li(tmp, NOC.STATUS_BASE + offset + (noc << NOC.INSTANCE_OFFSET_BIT))
  return fw.lw(out, tmp, 0)


def emit_snapshot(fw: CounterKernel, *, noc: int, out_word: int):
  fw.li(s2, RESULT_BASE + out_word * 4)
  for off, addr in enumerate((
    NOC.CMD_BUF_AVAIL,
    NOC.CMD_BUF_OVFL,
  )):
    emit_reg_read(fw, addr, t0, noc=noc, tmp=t3)
    fw.sw(t0, s2, off * 4)
  status_offsets = (
    NOC.NIU_MST_CMD_ACCEPTED,
    NOC.NIU_MST_NONPOSTED_WR_REQ_STARTED,
    NOC.NIU_MST_NONPOSTED_WR_REQ_SENT,
    NOC.NIU_MST_NONPOSTED_WR_DATA_WORD_SENT,
    NOC.NIU_MST_POSTED_WR_REQ_STARTED,
    NOC.NIU_MST_POSTED_WR_REQ_SENT,
    NOC.NIU_MST_POSTED_WR_DATA_WORD_SENT,
    NOC.NIU_MST_WR_ACK_RECEIVED,
    NOC.niu_mst_reqs_outstanding_id(0),
    NOC.niu_mst_write_reqs_outgoing_id(0),
    NOC.NIU_SLV_REQ_ACCEPTED,
    NOC.NIU_SLV_NONPOSTED_WR_REQ_RECEIVED,
    NOC.NIU_SLV_NONPOSTED_WR_DATA_WORD_RECEIVED,
    NOC.NIU_SLV_POSTED_WR_REQ_RECEIVED,
    NOC.NIU_SLV_POSTED_WR_DATA_WORD_RECEIVED,
    NOC.NIU_SLV_WR_ACK_SENT,
    NOC.NIU_SLV_RD_REQ_RECEIVED,
  )
  for i, offset in enumerate(status_offsets, start=2):
    emit_status_read(fw, offset, t0, noc=noc, tmp=t3)
    fw.sw(t0, s2, i * 4)
  word = SNAP_COUNTER_WORDS
  for vc in range(FLIT_VCS):
    for addr in (
      NOC.port1_flit_counter_lower(vc),
      NOC.port1_flit_counter_upper(vc),
      NOC.port2_flit_counter_lower(vc),
      NOC.port2_flit_counter_upper(vc),
    ):
      emit_reg_read(fw, addr, t0, noc=noc, tmp=t3)
      fw.sw(t0, s2, word * 4)
      word += 1
  return fw


def emit_wait_trid_zero(fw: CounterKernel, noc: int, trid: int = 0):
  fw.li(t3, NOC.STATUS_BASE + NOC.niu_mst_reqs_outstanding_id(trid) + (noc << NOC.INSTANCE_OFFSET_BIT))
  loop = fw._new_label("trid_zero")
  fw.label(loop)
  fw.lw(t4, t3, 0)
  fw.bne(t4, zero, loop)
  return fw.fence()


def emit_monitor_sample(fw: CounterKernel, *, noc: int, selected_vc: int):
  emit_reg_read(fw, NOC.CMD_BUF_AVAIL, t0, noc=noc, tmp=t3)
  skip_min = fw._new_label("cmd_avail_min_skip")
  fw.bgeu(t0, s10, skip_min)
  fw.mv(s10, t0)
  fw.label(skip_min)
  emit_status_read(fw, NOC.niu_mst_reqs_outstanding_id(0), t0, noc=noc, tmp=t3)
  skip_out = fw._new_label("outstanding_max_skip")
  fw.bltu(t0, s11, skip_out)
  fw.mv(s11, t0)
  fw.label(skip_out)
  emit_reg_read(fw, NOC.port1_flit_counter_lower(selected_vc), t0, noc=noc, tmp=t3)
  emit_reg_read(fw, NOC.port2_flit_counter_lower(selected_vc), t0, noc=noc, tmp=t3)
  return fw


def emit_warmup(fw: CounterKernel, cycles: int):
  if cycles <= 0:
    return fw
  fw.li(s0, cycles)
  loop = fw._new_label("warmup")
  fw.label(loop)
  fw.addi(s0, s0, -1)
  fw.bne(s0, zero, loop)
  return fw


def build_sender(*, noc: int, vc: int, priority: int, packets: int,
                 packet_bytes: int, posted: bool, warmup: int) -> KernelBase:
  fw = CounterKernel()
  ctrl = ctrl_word(vc=vc, priority=priority, posted=posted)
  emit_header(fw, role=ROLE_SENDER, noc=noc, vc=vc, priority=priority,
              packets=packets, packet_bytes=packet_bytes, samples=packets, posted=posted)
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s9,))
  emit_reset_debug_counters(fw, noc)
  fw.reset_noc_trid_barrier_counter(noc, 1, addr=t3, val=t4)
  fw.noc_set_transaction_id(noc, 0, 0, addr=t3, val=t4)
  emit_snapshot(fw, noc=noc, out_word=SNAP_BEFORE)
  fw.li(s10, 0xFFFFFFFF)
  fw.mv(s11, zero)
  emit_warmup(fw, warmup)
  harness.read_wall_clock(fw, a2, a3)
  fw.li(s0, packets)
  fw.li(s1, ctrl)
  fw.li(s2, STREAM_BASE)
  fw.li(s3, STREAM_BASE)
  fw.li(s4, packet_bytes)
  loop = fw._new_label("counter_sender_loop")
  done = fw._new_label("counter_sender_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  fw.noc_write_ctrl(noc=noc, ctrl=s1, src=s2, dst_lo=s3, dst_coord=s9, length=s4)
  emit_monitor_sample(fw, noc=noc, selected_vc=vc)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  fw.li(s2, MARKER_SRC_ADDR)
  fw.li(s3, MARKER_DST_ADDR)
  fw.li(s4, 4)
  fw.noc_write_ctrl(noc=noc, ctrl=s1, src=s2, dst_lo=s3, dst_coord=s9, length=s4)
  if posted:
    fw.noc_wait_cmd_ready(noc, 0, addr=t3, val=t4).fence()
  else:
    emit_wait_trid_zero(fw, noc, 0)
  harness.read_wall_clock(fw, a4, a5)
  emit_snapshot(fw, noc=noc, out_word=SNAP_AFTER)
  fw.li(s2, RESULT_BASE)
  for off, reg in enumerate((a2, a3, a4, a5), start=8):
    fw.sw(reg, s2, off * 4)
  fw.sw(s10, s2, 14 * 4)
  fw.sw(s11, s2, 15 * 4)
  emit_status(fw, STATUS_DONE)
  return fw.ret()


def build_receiver(*, noc: int, vc: int, priority: int, packets: int,
                   packet_bytes: int, posted: bool) -> KernelBase:
  fw = CounterKernel()
  emit_header(fw, role=ROLE_RECEIVER, noc=noc, vc=vc, priority=priority,
              packets=packets, packet_bytes=packet_bytes, samples=0, posted=posted)
  emit_reset_debug_counters(fw, noc)
  emit_snapshot(fw, noc=noc, out_word=SNAP_BEFORE)
  harness.read_wall_clock(fw, a2, a3)
  fw.li(s0, MARKER_VALUE)
  fw.li(s1, MARKER_DST_ADDR)
  fw.mv(s8, zero)
  poll = fw._new_label("counter_receiver_poll")
  done = fw._new_label("counter_receiver_done")
  fw.label(poll)
  fw.lw(t0, s1, 0)
  fw.beq(t0, s0, done)
  fw.addi(s8, s8, 1)
  fw.j(poll)
  fw.label(done)
  harness.read_wall_clock(fw, a4, a5)
  emit_snapshot(fw, noc=noc, out_word=SNAP_AFTER)
  fw.li(s2, RESULT_BASE)
  for off, reg in enumerate((a2, a3, a4, a5), start=8):
    fw.sw(reg, s2, off * 4)
  fw.sw(s8, s2, 12 * 4)
  fw.sw(t0, s2, 13 * 4)
  emit_status(fw, STATUS_DONE)
  return fw.ret()


def build_sampler(*, noc: int, vc: int, priority: int, packets: int,
                  packet_bytes: int, samples: int, posted: bool, warmup: int) -> KernelBase:
  fw = CounterKernel()
  emit_header(fw, role=ROLE_SAMPLER, noc=noc, vc=vc, priority=priority,
              packets=packets, packet_bytes=packet_bytes, samples=samples, posted=posted)
  emit_reset_debug_counters(fw, noc)
  emit_snapshot(fw, noc=noc, out_word=SNAP_BEFORE)
  emit_warmup(fw, max(0, warmup // 2))
  harness.read_wall_clock(fw, a2, a3)
  fw.li(s10, 0xFFFFFFFF)
  fw.mv(s11, zero)
  fw.li(s0, samples)
  loop = fw._new_label("counter_sampler_loop")
  done = fw._new_label("counter_sampler_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  emit_monitor_sample(fw, noc=noc, selected_vc=vc)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  harness.read_wall_clock(fw, a4, a5)
  emit_snapshot(fw, noc=noc, out_word=SNAP_AFTER)
  fw.li(s2, RESULT_BASE)
  for off, reg in enumerate((a2, a3, a4, a5), start=8):
    fw.sw(reg, s2, off * 4)
  fw.sw(s10, s2, 14 * 4)
  fw.sw(s11, s2, 15 * 4)
  emit_status(fw, STATUS_DONE)
  return fw.ret()


class CounterProbeProgram:
  def __init__(self, *, source: Core, target: Core, samplers: list[Core],
               noc: int, vc: int, priority: int, packets: int,
               packet_bytes: int, samples: int, posted: bool, warmup: int):
    self.source = source
    self.target = target
    self.samplers = list(samplers)
    self.noc = noc
    self.vc = vc
    self.priority = priority
    self.packets = packets
    self.packet_bytes = packet_bytes
    self.samples = samples
    self.posted = posted
    self.warmup = warmup
    self.name = f"riscv_noc_counter_probe:noc{noc}:vc{vc}"

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
    segments = {}
    sender = build_sender(
      noc=self.noc, vc=self.vc, priority=self.priority, packets=self.packets,
      packet_bytes=self.packet_bytes, posted=self.posted, warmup=self.warmup,
    )
    sender.rta(lambda _x, _y: [noc_xy(*self.target)])
    segments[self.source] = self._layout(self.source, sender, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id)
    receiver = build_receiver(
      noc=self.noc, vc=self.vc, priority=self.priority, packets=self.packets,
      packet_bytes=self.packet_bytes, posted=self.posted,
    )
    segments[self.target] = self._layout(self.target, receiver, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id)
    for core in self.samplers:
      kernel = build_sampler(
        noc=self.noc, vc=self.vc, priority=self.priority, packets=self.packets,
        packet_bytes=self.packet_bytes, samples=self.samples, posted=self.posted, warmup=self.warmup,
      )
      segments[core] = self._layout(core, kernel, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id)
    active = [self.source, self.target] + self.samplers
    reset_blob = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_RESET_READ_PTR_FROM_HOST)
    commands = [
      UnicastWrite(active, TensixL1.GO_MSG, [reset_blob] * len(active)),
      UnicastWrite(active, TensixL1.GO_MSG_INDEX, [b"\0\0\0\0"] * len(active)),
    ]
    for core in active:
      for segment in segments[core]:
        commands.append(UnicastWrite([core], segment.addr, [segment.data]))
    commands.append(Run(active))
    return commands


def path_cores(source: Core, target: Core) -> list[Core]:
  if source[1] != target[1]:
    raise ValueError("counter probe currently expects a same-row route")
  step = 1 if target[0] > source[0] else -1
  return [(x, source[1]) for x in range(source[0], target[0] + step, step)]


def seed(device: Device, *, source: Core, target: Core, active: list[Core]):
  payload = bytearray(NOC.MAX_BURST_SIZE + 0x100)
  for off in range(0, NOC.MAX_BURST_SIZE, 4):
    struct.pack_into("<I", payload, off, 0xA5000000 | off)
  struct.pack_into("<I", payload, MARKER_SRC_ADDR - STREAM_BASE, MARKER_VALUE)
  with harness.device_window(device, source) as win:
    for core in active:
      win.target(core)
      win.write(RESULT_BASE, b"\0" * RESULT_SIZE)
    win.target(source)
    win.write(STREAM_BASE, bytes(payload))
    win.target(target)
    win.write(STREAM_BASE, b"\0" * len(payload))


def read_result(device: Device, core: Core) -> Result:
  blob = harness.read_window(device, core, RESULT_BASE, RESULT_SIZE)
  words = struct.unpack_from("<" + "I" * RESULT_WORDS, blob)
  if words[0] != RESULT_MAGIC:
    raise RuntimeError(f"{core}: bad counter result magic 0x{words[0]:08x}")
  if words[2] != STATUS_DONE:
    raise RuntimeError(f"{core}: counter probe status 0x{words[2]:08x}")
  return Result(core, words)


def snap(words: tuple[int, ...], base: int) -> dict[str, int]:
  out = {name: words[base + i] for i, name in enumerate(SNAP_NAMES)}
  flit_base = base + SNAP_COUNTER_WORDS
  for vc in range(FLIT_VCS):
    off = flit_base + vc * 4
    out[f"vc{vc}_p1"] = words[off] | (words[off + 1] << 32)
    out[f"vc{vc}_p2"] = words[off + 2] | (words[off + 3] << 32)
  return out


def delta(result: Result) -> dict[str, int]:
  before = snap(result.words, SNAP_BEFORE)
  after = snap(result.words, SNAP_AFTER)
  return {name: (after[name] - before[name]) & 0xFFFFFFFFFFFFFFFF for name in before}


def format_core(core: Core) -> str:
  return f"{core[0]},{core[1]}"


def flit_summary(d: dict[str, int]) -> str:
  parts = []
  for vc in range(FLIT_VCS):
    p1 = d[f"vc{vc}_p1"]
    p2 = d[f"vc{vc}_p2"]
    if p1 or p2:
      parts.append(f"vc{vc}:p1={p1}:p2={p2}")
  return " ".join(parts) or "-"


def main():
  parser = argparse.ArgumentParser(description="Snapshot Blackhole NoC NIU and router counters around a unicast transfer.")
  parser.add_argument("--noc", type=int, choices=(0, 1), default=0)
  parser.add_argument("--source", type=harness.parse_core, default=(1, 4))
  parser.add_argument("--target", type=harness.parse_core, default=(14, 4))
  parser.add_argument("--vc", type=int, default=1)
  parser.add_argument("--priority", type=int, default=0)
  parser.add_argument("--packets", type=int, default=512)
  parser.add_argument("--bytes", type=int, default=NOC.MAX_BURST_SIZE)
  parser.add_argument("--samples", type=int, default=4096)
  parser.add_argument("--warmup", type=int, default=20000)
  parser.add_argument("--posted", action="store_true")
  parser.add_argument("--no-report", action="store_true")
  parser.add_argument("--report", type=Path, default=harness.doc_path("noc", "noc-counter-probe.md"))
  args = parser.parse_args()
  if not 0 <= args.vc < FLIT_VCS:
    raise ValueError(f"--vc must be in [0, {FLIT_VCS - 1}]")
  if not 0 <= args.priority <= 15:
    raise ValueError("--priority must be in [0, 15]")
  if args.packets <= 0:
    raise ValueError("--packets must be positive")
  if args.bytes <= 0 or args.bytes > NOC.MAX_BURST_SIZE or args.bytes % 4:
    raise ValueError(f"--bytes must be a 4-byte multiple in [4, {NOC.MAX_BURST_SIZE}]")
  if args.samples <= 0:
    raise ValueError("--samples must be positive")

  with harness.open_device() as device:
    usable = set(device.cores)
    route = path_cores(args.source, args.target)
    missing = [core for core in route if core not in usable]
    if args.source not in usable or args.target not in usable or missing:
      raise ValueError(f"source/target/route must be usable program cores; missing route cores: {missing}")
    samplers = [core for core in route if core not in (args.source, args.target)]
    active = [args.source, args.target] + samplers
    seed(device, source=args.source, target=args.target, active=active)
    device.run(CounterProbeProgram(
      source=args.source, target=args.target, samplers=samplers, noc=args.noc,
      vc=args.vc, priority=args.priority, packets=args.packets,
      packet_bytes=args.bytes, samples=args.samples, posted=args.posted,
      warmup=args.warmup,
    ))
    results = [read_result(device, core) for core in active]

  rows = [
    "| core | role | window cyc | cmd accepted | np wr req sent | np data sent | p wr req sent | p data sent | ack recv | slv req accepted | slv np wr recv | slv np data recv | slv p wr recv | slv p data recv | slv ack sent | out max | cmd avail min | selected vc p1 | selected vc p2 | nonzero flit counters | cmd ovfl |",
    "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
  ]
  role_names = {ROLE_SENDER: "sender", ROLE_RECEIVER: "receiver", ROLE_SAMPLER: "sampler"}
  for result in results:
    d = delta(result)
    rows.append(
      f"| `{format_core(result.core)}` | {role_names.get(result.role, result.role)} | {result.end - result.start} | "
      f"{d['mst_cmd_accepted']} | {d['mst_nonposted_wr_req_sent']} | {d['mst_nonposted_wr_data_word_sent']} | "
      f"{d['mst_posted_wr_req_sent']} | {d['mst_posted_wr_data_word_sent']} | {d['mst_wr_ack_received']} | "
      f"{d['slv_req_accepted']} | {d['slv_nonposted_wr_req_received']} | {d['slv_nonposted_wr_data_word_received']} | "
      f"{d['slv_posted_wr_req_received']} | {d['slv_posted_wr_data_word_received']} | {d['slv_wr_ack_sent']} | "
      f"{result.words[15]} | 0x{result.words[14]:08x} | {d[f'vc{args.vc}_p1']} | {d[f'vc{args.vc}_p2']} | "
      f"`{flit_summary(d)}` | {d['cmd_buf_ovfl']} |"
    )
  summary = [
    f"NoC: `{args.noc}`; source: `{format_core(args.source)}`; target: `{format_core(args.target)}`; route: `{' '.join(format_core(c) for c in route)}`",
    f"Static VC: `{args.vc}`; priority: `{args.priority}`; posted: `{args.posted}`",
    f"Packets: `{args.packets}`; bytes/packet: `{args.bytes}`; sampler iterations: `{args.samples}`",
    "Each row is a RISC-side before/after delta from that core's local NoC/NIU registers. `vc p1/p2 flits` are router flit counter deltas for the selected VC only.",
  ]
  table = "\n".join(rows)
  print("\n".join(f"- {item}" for item in summary))
  print()
  print(table)
  if not args.no_report:
    harness.append_report(args.report, "NoC counter probe", summary, table)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
