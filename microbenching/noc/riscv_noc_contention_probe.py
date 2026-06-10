#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402  (does sys.path + TT_USB bootstrap on import)
import riscv_noc_hop_sweep as hop_sweep
from asm import KernelBase
from device import Device
from dsl import a2, a3, a4, a5, s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, t0, t3, t4, zero
from pcie import TLBWindow
from program import DevMsgs, Program, Run, UnicastWrite
from ttk.addrs import Core, align_down, noc_xy
from ttk.mailbox import BriscMailbox as BM
from ttk.noc import NOC, Noc
from ttk.tensix import TensixL1, TensixMMIO


RESULT_BASE = 0x150000
RESULT_STRIDE = 0x100
RESULT_WORDS = 16
RESULT_SIZE = RESULT_WORDS * 4
RESULT_MAGIC = 0x524E4350  # "RNCP"
STATUS_STARTED = 0xC0000001
STATUS_DONE = 0xC000D00D

STREAM_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
READ_SINK = 0x140000
POINTER_SINK = READ_SINK + 0x4000
START_GATE_BASE = RESULT_BASE - 0x40

ROLE_WRITER = 1
ROLE_READER = 2
ROLE_POINTER = 3
ROLE_NAMES = {
  ROLE_WRITER: "write",
  ROLE_READER: "read",
  ROLE_POINTER: "pointer",
}

# DEDUPE: shares logic with noc_topology.py.
NOC_GRID_W = 25
NOC_GRID_H = 25
P100_WORKER_X = (*range(1, 8), *range(10, 15))
P100_WORKER_Y = tuple(range(2, 12))
DEFAULT_P100_CORES = [(x, y) for y in P100_WORKER_Y for x in P100_WORKER_X]


@dataclass(frozen=True)
class PathInfo:
  nodes: tuple[Core, ...]

  @property
  def hops(self) -> int:
    return max(0, len(self.nodes) - 1)

  @property
  def links(self) -> tuple[tuple[Core, Core], ...]:
    return tuple(zip(self.nodes, self.nodes[1:]))


@dataclass(frozen=True)
class ActiveStream:
  name: str
  source: Core
  target: Core
  role: int
  result_base: int
  ctrl: int | None = None


@dataclass(frozen=True)
class Result:
  core: Core
  name: str
  role: int
  status: int
  noc: int
  ctrl: int
  bytes_or_iters: int
  chunks_or_repeats: int
  start: int
  end: int
  counter_before: int
  counter_after: int
  sink: int

  @property
  def cycles(self) -> int:
    return (self.end - self.start) & ((1 << 64) - 1)

  @property
  def counter_delta(self) -> int:
    return (self.counter_after - self.counter_before) & 0xFFFFFFFF

  def bytes_per_cycle(self) -> float:
    if self.role == ROLE_POINTER or self.cycles <= 0:
      return 0.0
    return self.bytes_or_iters / self.cycles

  def cycles_per_iter(self) -> float:
    if self.role != ROLE_POINTER or self.bytes_or_iters <= 0:
      return 0.0
    return self.cycles / self.bytes_or_iters


class ProbeKernel(KernelBase, Noc):
  def noc_read_with_ctrl(self, noc: int, buf: int, src_lo, src_mid, src_coord,
                         dst, length, ctrl: int, *, ret_coord=0, a=t3, v=t4):
    self.noc_wait_cmd_ready(noc, buf, addr=a, val=v)
    self.noc_cmd_reg(noc, buf, NOC.CTRL, ctrl, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_LO, dst, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_MID, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_COORDINATE, ret_coord, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_LO, src_lo, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_MID, src_mid, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_COORDINATE, src_coord, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE, length, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE_1, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.CMD_CTRL, NOC.CTRL_SEND_REQ, addr=a, tmp=v)
    return self

  def noc_write_with_ctrl(self, noc: int, buf: int, src, dst_lo, dst_mid, dst_coord,
                          length, ctrl: int, *, a=t3, v=t4):
    self.noc_wait_cmd_ready(noc, buf, addr=a, val=v)
    self.noc_cmd_reg(noc, buf, NOC.CTRL, ctrl, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_LO, src, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_LO, dst_lo, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_MID, dst_mid, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_COORDINATE, dst_coord, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE, length, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE_1, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.CMD_CTRL, NOC.CTRL_SEND_REQ, addr=a, tmp=v)
    return self


def noc_path(src: Core, dst: Core, noc: int) -> PathInfo:
  if noc not in (0, 1):
    raise ValueError("noc must be 0 or 1")
  step = 1 if noc == 0 else -1
  x, y = src
  nodes = [(x, y)]
  while x != dst[0]:
    x = (x + step) % NOC_GRID_W
    nodes.append((x, y))
  while y != dst[1]:
    y = (y + step) % NOC_GRID_H
    nodes.append((x, y))
  return PathInfo(tuple(nodes))


def noc_hops(src: Core, dst: Core, noc: int) -> int:
  return noc_path(src, dst, noc).hops


def shared_link(a_src: Core, a_dst: Core, b_src: Core, b_dst: Core, noc: int) -> tuple[Core, Core] | None:
  b_links = set(noc_path(b_src, b_dst, noc).links)
  return next((link for link in noc_path(a_src, a_dst, noc).links if link in b_links), None)


def rows_by_y(cores: list[Core]) -> dict[int, list[int]]:
  rows: dict[int, list[int]] = {}
  for x, y in cores:
    rows.setdefault(y, []).append(x)
  return {y: sorted(xs) for y, xs in rows.items()}


def choose_row(cores: list[Core], row: int | None) -> tuple[int, list[int]]:
  rows = rows_by_y(cores)
  if row is not None:
    xs = rows.get(row)
    if xs is None or len(xs) < 2:
      raise ValueError(f"row {row} does not have at least two program cores")
    return row, xs
  candidates = [(len(xs), -y, y, xs) for y, xs in rows.items() if len(xs) >= 2]
  if not candidates:
    raise ValueError("need a row with at least two program cores")
  _, _, y, xs = max(candidates)
  return y, xs


def static_vc_ctrl(role: int, vc: int | None) -> int | None:
  if vc is None:
    return None
  if not 0 <= vc <= 7:
    raise ValueError("static VC must be in [0, 7]")
  vc_bits = NOC.CMD_VC_STATIC | (vc << 13)
  if role == ROLE_READER or role == ROLE_POINTER:
    return NOC.CMD_CPY | NOC.CMD_RESP_MARKED | vc_bits
  if role == ROLE_WRITER:
    return NOC.CMD_CPY | NOC.CMD_WR | NOC.CMD_RESP_MARKED | vc_bits
  raise ValueError(f"unknown role {role}")


def emit_result(fw: ProbeKernel, *, result_base: int, role: int, status: int, noc: int,
                ctrl: int, bytes_or_iters: int, chunks_or_repeats: int,
                start_lo=zero, start_hi=zero, end_lo=zero, end_hi=zero,
                before=zero, after=zero, sink=zero):
  fw.li(s2, result_base)
  const = (
    RESULT_MAGIC, role, status, noc, ctrl & 0xFFFFFFFF,
    bytes_or_iters, chunks_or_repeats,
  )
  for off, value in enumerate(const):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off, reg in enumerate((start_lo, start_hi, end_lo, end_hi, before, after, sink), start=7):
    fw.sw(reg, s2, off * 4)
  fw.sw(zero, s2, 14 * 4)
  fw.sw(zero, s2, 15 * 4)
  return fw


def emit_counter_read(fw: ProbeKernel, noc: int, counter: int, out, *, addr=t3):
  fw.li(addr, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  return fw.lw(out, addr, 0)


def emit_wait_gate(fw: ProbeKernel):
  fw.li(s2, START_GATE_BASE)
  fw.lw(s3, s2, 0)
  fw.lw(s4, s2, 4)
  fw.or_(t0, s3, s4)
  no_gate = fw._new_label("start_gate_none")
  wait = fw._new_label("start_gate_wait")
  done = fw._new_label("start_gate_done")
  fw.beq(t0, zero, no_gate)
  fw.label(wait)
  harness.read_wall_clock(fw, a2, a3)
  fw.bltu(a3, s4, wait)
  fw.bltu(s4, a3, done)
  fw.bltu(a2, s3, wait)
  fw.j(done)
  fw.label(no_gate)
  fw.label(done)
  return fw


def emit_stream_loop(fw: ProbeKernel, *, noc: int, role: int, stream_bytes: int,
                     repeats: int, ctrl: int | None):
  chunks = stream_bytes // NOC.MAX_BURST_SIZE
  fw.li(s4, NOC.MAX_BURST_SIZE)
  fw.li(s8, NOC.MAX_BURST_SIZE)
  fw.li(s0, repeats)
  outer = fw._new_label("stream_outer")
  outer_done = fw._new_label("stream_outer_done")
  fw.label(outer)
  fw.beq(s0, zero, outer_done)
  fw.li(s1, chunks)
  if role == ROLE_WRITER:
    fw.li(s2, STREAM_BASE)
    fw.li(s3, STREAM_BASE)
  elif role == ROLE_READER:
    fw.li(s2, READ_SINK)
    fw.li(s3, STREAM_BASE)
  else:
    raise ValueError("stream loop only supports read/write")
  inner = fw._new_label("stream_inner")
  inner_done = fw._new_label("stream_inner_done")
  fw.label(inner)
  fw.beq(s1, zero, inner_done)
  if role == ROLE_WRITER:
    if ctrl is None:
      fw.noc_write(noc, 0, s2, s3, 0, s9, s4, posted=False, a=t3, v=t4)
    else:
      fw.noc_write_with_ctrl(noc, 0, s2, s3, 0, s9, s4, ctrl, a=t3, v=t4)
    fw.add(s2, s2, s8)
  else:
    if ctrl is None:
      fw.noc_read(noc, 1, s3, 0, s9, s2, s4, ret_coord=s5, a=t3, v=t4)
    else:
      fw.noc_read_with_ctrl(noc, 1, s3, 0, s9, s2, s4, ctrl, ret_coord=s5, a=t3, v=t4)
  fw.addi(s6, s6, 1)
  fw.add(s3, s3, s8)
  fw.addi(s1, s1, -1)
  fw.j(inner)
  fw.label(inner_done)
  fw.addi(s0, s0, -1)
  fw.j(outer)
  fw.label(outer_done)
  return fw


def build_stream_kernel(*, noc: int, role: int, stream_bytes: int, repeats: int,
                        result_base: int, ctrl: int | None = None) -> ProbeKernel:
  chunks = stream_bytes // NOC.MAX_BURST_SIZE
  ctrl_word = ctrl if ctrl is not None else (NOC.CMD_RD_FIELD if role == ROLE_READER else NOC.CMD_WR_FIELD)
  fw = ProbeKernel()
  emit_result(
    fw, result_base=result_base, role=role, status=STATUS_STARTED, noc=noc,
    ctrl=ctrl_word, bytes_or_iters=stream_bytes * repeats,
    chunks_or_repeats=chunks * repeats,
  )
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s9,))
  fw.local_noc0_coord(s5, x_addr=BM.MY_X, y_addr=BM.MY_Y)
  if role == ROLE_READER:
    emit_counter_read(fw, noc, NOC.NIU_MST_RD_RESP_RECEIVED, s7)
  elif role == ROLE_WRITER:
    emit_counter_read(fw, noc, NOC.NIU_MST_WR_ACK_RECEIVED, s7)
  else:
    raise ValueError(f"bad stream role {role}")
  fw.mv(s6, s7)
  emit_wait_gate(fw)
  harness.read_wall_clock(fw, a2, a3)
  emit_stream_loop(fw, noc=noc, role=role, stream_bytes=stream_bytes, repeats=repeats, ctrl=ctrl)
  if role == ROLE_READER:
    fw.noc_reads_flushed(noc, s6, addr=t3, val=t4)
  else:
    fw.noc_write_barrier(noc, s6, addr=t3, val=t4)
  harness.read_wall_clock(fw, a4, a5)
  if role == ROLE_READER:
    emit_counter_read(fw, noc, NOC.NIU_MST_RD_RESP_RECEIVED, s8)
    fw.li(s2, READ_SINK)
    fw.lw(s1, s2, 0)
  else:
    emit_counter_read(fw, noc, NOC.NIU_MST_WR_ACK_RECEIVED, s8)
    emit_counter_read(fw, noc, NOC.NIU_MST_RD_RESP_RECEIVED, t0, addr=t3)
    fw.addi(t0, t0, 1)
    fw.li(s2, STREAM_BASE)
    fw.li(s4, 4)
    if ctrl is None:
      fw.noc_read(noc, 1, s2, 0, s9, READ_SINK, s4, ret_coord=s5, a=t3, v=t4)
    else:
      rd_ctrl = static_vc_ctrl(ROLE_READER, (ctrl >> 13) & 0x7)
      fw.noc_read_with_ctrl(noc, 1, s2, 0, s9, READ_SINK, s4, rd_ctrl, ret_coord=s5, a=t3, v=t4)
    fw.noc_reads_flushed(noc, t0, addr=t3, val=t4)
    fw.li(s2, READ_SINK)
    fw.lw(s1, s2, 0)
  emit_result(
    fw, result_base=result_base, role=role, status=STATUS_DONE, noc=noc,
    ctrl=ctrl_word, bytes_or_iters=stream_bytes * repeats,
    chunks_or_repeats=chunks * repeats, start_lo=a2, start_hi=a3,
    end_lo=a4, end_hi=a5, before=s7, after=s8, sink=s1,
  )
  return fw.ret()


def build_pointer_kernel(*, noc: int, iters: int, result_base: int,
                         ctrl: int | None = None) -> ProbeKernel:
  ctrl_word = ctrl if ctrl is not None else NOC.CMD_RD_FIELD
  fw = ProbeKernel()
  emit_result(
    fw, result_base=result_base, role=ROLE_POINTER, status=STATUS_STARTED, noc=noc,
    ctrl=ctrl_word, bytes_or_iters=iters, chunks_or_repeats=1,
  )
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s9,))
  fw.local_noc0_coord(s5, x_addr=BM.MY_X, y_addr=BM.MY_Y)
  fw.li(s2, STREAM_BASE)
  fw.li(s3, POINTER_SINK)
  fw.li(s4, 4)
  emit_counter_read(fw, noc, NOC.NIU_MST_RD_RESP_RECEIVED, s7)
  fw.mv(s6, s7)
  emit_wait_gate(fw)
  harness.read_wall_clock(fw, a2, a3)
  fw.li(s0, iters)
  loop = fw._new_label("pointer_chase")
  done = fw._new_label("pointer_chase_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  if ctrl is None:
    fw.noc_read(noc, 1, s2, 0, s9, s3, s4, ret_coord=s5, a=t3, v=t4)
  else:
    fw.noc_read_with_ctrl(noc, 1, s2, 0, s9, s3, s4, ctrl, ret_coord=s5, a=t3, v=t4)
  fw.addi(s6, s6, 1)
  fw.noc_reads_flushed(noc, s6, addr=t3, val=t4)
  fw.lw(s2, s3, 0)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  harness.read_wall_clock(fw, a4, a5)
  emit_counter_read(fw, noc, NOC.NIU_MST_RD_RESP_RECEIVED, s8)
  fw.mv(s1, s2)
  emit_result(
    fw, result_base=result_base, role=ROLE_POINTER, status=STATUS_DONE, noc=noc,
    ctrl=ctrl_word, bytes_or_iters=iters, chunks_or_repeats=1,
    start_lo=a2, start_hi=a3, end_lo=a4, end_hi=a5,
    before=s7, after=s8, sink=s1,
  )
  return fw.ret()


def one_core_program(brisc: KernelBase, *, ncrisc: KernelBase | None = None) -> Program:
  empty = KernelBase()
  return Program(
    brisc=brisc,
    ncrisc=ncrisc or empty,
    trisc0=empty,
    trisc1=empty,
    trisc2=empty,
    num_cores=1,
  )


class MultiCoreProgram:
  def __init__(self, streams: list[ActiveStream], *, noc: int, stream_bytes: int, repeats: int):
    self.streams = list(streams)
    self.noc = noc
    self.stream_bytes = stream_bytes
    self.repeats = repeats
    self.name = f"riscv_noc_contention_probe:noc{noc}:streams{len(streams)}"

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    per_core_segments = {}
    target_cores: list[Core] = []
    active_by_core = {stream.source: stream for stream in self.streams}
    passive = sorted({stream.target for stream in self.streams} - set(active_by_core))
    for stream in self.streams:
      kernel = build_stream_kernel(
        noc=self.noc, role=stream.role, stream_bytes=self.stream_bytes,
        repeats=self.repeats, result_base=stream.result_base, ctrl=stream.ctrl,
      )
      kernel.rta(lambda _x, _y, target=stream.target: [noc_xy(*target)])
      per_core_segments[stream.source] = one_core_program(kernel).layout(
        core_xy=stream.source, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id,
      )
      target_cores.append(stream.source)
    for core in passive:
      per_core_segments[core] = one_core_program(KernelBase().ret()).layout(
        core_xy=core, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id,
      )
      target_cores.append(core)

    reset_blob = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_RESET_READ_PTR_FROM_HOST)
    commands = [
      UnicastWrite(target_cores, TensixL1.GO_MSG, [reset_blob] * len(target_cores)),
      UnicastWrite(target_cores, TensixL1.GO_MSG_INDEX, [b"\0\0\0\0"] * len(target_cores)),
    ]
    for core in target_cores:
      for segment in per_core_segments[core]:
        commands.append(UnicastWrite([core], segment.addr, [segment.data]))
    commands.append(Run(target_cores))
    return commands


class SameCoreReadWriteProgram:
  def __init__(self, *, source: Core, target: Core, noc: int, stream_bytes: int,
               repeats: int, read_ctrl: int | None, write_ctrl: int | None):
    self.source = source
    self.target = target
    self.noc = noc
    self.stream_bytes = stream_bytes
    self.repeats = repeats
    self.read_ctrl = read_ctrl
    self.write_ctrl = write_ctrl
    self.name = f"riscv_noc_contention_probe:e:noc{noc}:{source}->{target}"

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    writer = build_stream_kernel(
      noc=self.noc, role=ROLE_WRITER, stream_bytes=self.stream_bytes,
      repeats=self.repeats, result_base=RESULT_BASE, ctrl=self.write_ctrl,
    )
    reader = build_stream_kernel(
      noc=self.noc, role=ROLE_READER, stream_bytes=self.stream_bytes,
      repeats=self.repeats, result_base=RESULT_BASE + RESULT_STRIDE, ctrl=self.read_ctrl,
    )
    writer.rta(lambda _x, _y: [noc_xy(*self.target)])
    reader.rta(lambda _x, _y: [noc_xy(*self.target)])
    source_segments = one_core_program(writer, ncrisc=reader).layout(
      core_xy=self.source, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id,
    )
    target_cores = [self.source]
    per_core_segments = {self.source: source_segments}
    if self.target != self.source:
      per_core_segments[self.target] = one_core_program(KernelBase().ret()).layout(
        core_xy=self.target, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id,
      )
      target_cores.append(self.target)
    reset_blob = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_RESET_READ_PTR_FROM_HOST)
    commands = [
      UnicastWrite(target_cores, TensixL1.GO_MSG, [reset_blob] * len(target_cores)),
      UnicastWrite(target_cores, TensixL1.GO_MSG_INDEX, [b"\0\0\0\0"] * len(target_cores)),
    ]
    for core in target_cores:
      for segment in per_core_segments[core]:
        commands.append(UnicastWrite([core], segment.addr, [segment.data]))
    commands.append(Run(target_cores))
    return commands


class PointerProgram:
  def __init__(self, *, source: Core, target: Core, noc: int, iters: int, ctrl: int | None):
    self.source = source
    self.target = target
    self.noc = noc
    self.iters = iters
    self.ctrl = ctrl
    self.name = f"riscv_noc_contention_probe:hop:noc{noc}:{source}->{target}"

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    kernel = build_pointer_kernel(noc=self.noc, iters=self.iters, result_base=RESULT_BASE, ctrl=self.ctrl)
    kernel.rta(lambda _x, _y: [noc_xy(*self.target)])
    per_core_segments = {
      self.source: one_core_program(kernel).layout(
        core_xy=self.source, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id,
      )
    }
    target_cores = [self.source]
    if self.target != self.source:
      per_core_segments[self.target] = one_core_program(KernelBase().ret()).layout(
        core_xy=self.target, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id,
      )
      target_cores.append(self.target)
    reset_blob = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_RESET_READ_PTR_FROM_HOST)
    commands = [
      UnicastWrite(target_cores, TensixL1.GO_MSG, [reset_blob] * len(target_cores)),
      UnicastWrite(target_cores, TensixL1.GO_MSG_INDEX, [b"\0\0\0\0"] * len(target_cores)),
    ]
    for core in target_cores:
      for segment in per_core_segments[core]:
        commands.append(UnicastWrite([core], segment.addr, [segment.data]))
    commands.append(Run(target_cores))
    return commands


def seed_blob(stream_bytes: int) -> bytes:
  seed = bytearray(NOC.MAX_BURST_SIZE)
  for off in range(0, len(seed), 4):
    struct.pack_into("<I", seed, off, 0xA5000000 | off)
  return bytes(seed) * (stream_bytes // NOC.MAX_BURST_SIZE)


def pointer_blob(chain_len: int) -> bytes:
  chain_len = max(1, chain_len)
  blob = bytearray(chain_len * 4)
  for i in range(chain_len):
    nxt = STREAM_BASE + ((i + 1) % chain_len) * 4
    struct.pack_into("<I", blob, i * 4, nxt)
  return bytes(blob)


def clear_cores(device: Device, cores: list[Core], *, stream_bytes: int,
                source_cores: set[Core], target_cores: set[Core],
                pointer_targets: dict[Core, int] | None = None):
  payload = seed_blob(stream_bytes)
  pointer_targets = pointer_targets or {}
  with harness.device_window(device, cores[0]) as win:
    for core in sorted(set(cores)):
      win.target(core)
      win.write(RESULT_BASE - RESULT_STRIDE, b"\0" * (RESULT_STRIDE * 4))
      win.write(START_GATE_BASE, b"\0" * 8)
      if core in source_cores:
        win.write(STREAM_BASE, payload)
      if core in target_cores:
        win.write(STREAM_BASE, payload)
      if core in pointer_targets:
        win.write(STREAM_BASE, pointer_blob(pointer_targets[core]))


def read_host_wall_clock(device: Device, core: Core) -> int:
  mmio_base, _ = align_down(TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_H, TLBWindow.SIZE_2M)
  h_off = TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_H - mmio_base
  l_off = TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L - mmio_base
  with harness.device_window(device, core, addr=mmio_base) as win:
    win.target(core, addr=mmio_base)
    while True:
      hi0 = struct.unpack("<I", win.read(h_off, 4))[0]
      lo = struct.unpack("<I", win.read(l_off, 4))[0]
      hi1 = struct.unpack("<I", win.read(h_off, 4))[0]
      if hi0 == hi1:
        return lo | (hi0 << 32)


def write_start_gate(device: Device, cores: list[Core], threshold: int):
  blob = struct.pack("<II", threshold & 0xFFFFFFFF, (threshold >> 32) & 0xFFFFFFFF)
  with harness.device_window(device, cores[0]) as win:
    for core in sorted(set(cores)):
      win.target(core)
      win.write(START_GATE_BASE, blob)


def parse_result(blob: bytes, *, core: Core, name: str) -> Result:
  words = struct.unpack_from("<" + "I" * RESULT_WORDS, blob, 0)
  if words[0] != RESULT_MAGIC:
    raise RuntimeError(f"{name}@{core}: bad result magic 0x{words[0]:08x}")
  if words[2] != STATUS_DONE:
    raise RuntimeError(f"{name}@{core}: benchmark did not finish, status=0x{words[2]:08x}")
  return Result(
    core=core, name=name, role=words[1], status=words[2], noc=words[3], ctrl=words[4],
    bytes_or_iters=words[5], chunks_or_repeats=words[6],
    start=words[7] | (words[8] << 32), end=words[9] | (words[10] << 32),
    counter_before=words[11], counter_after=words[12], sink=words[13],
  )


def read_result(device: Device, core: Core, *, result_base: int, name: str) -> Result:
  with harness.device_window(device, core) as win:
    win.target(core)
    blob = win.read(result_base, RESULT_SIZE)
  return parse_result(blob, core=core, name=name)


def maybe_run(device: Device | None, program, target_cores: list[Core], *, dry_run: bool, gate_delay_cycles: int):
  if dry_run:
    program.lower(target_cores)
    return
  assert device is not None
  if gate_delay_cycles > 0:
    threshold = read_host_wall_clock(device, target_cores[0]) + gate_delay_cycles
    write_start_gate(device, target_cores, threshold)
  device.run(program)


def validate_bytes(stream_bytes: int):
  if stream_bytes <= 0 or stream_bytes % NOC.MAX_BURST_SIZE:
    raise ValueError("--bytes must be a positive multiple of 16 KiB")
  if stream_bytes > START_GATE_BASE - STREAM_BASE:
    raise ValueError(f"--bytes must fit below result area; max is {START_GATE_BASE - STREAM_BASE}")


def run_stream_set(device: Device | None, streams: list[ActiveStream], *, noc: int,
                   stream_bytes: int, repeats: int, dry_run: bool,
                   gate_delay_cycles: int) -> list[Result]:
  all_cores = sorted({s.source for s in streams} | {s.target for s in streams})
  if device is not None and not dry_run:
    clear_cores(
      device, all_cores, stream_bytes=stream_bytes,
      source_cores={s.source for s in streams if s.role == ROLE_WRITER},
      target_cores={s.target for s in streams},
    )
  program = MultiCoreProgram(streams, noc=noc, stream_bytes=stream_bytes, repeats=repeats)
  maybe_run(device, program, all_cores, dry_run=dry_run, gate_delay_cycles=gate_delay_cycles)
  if dry_run:
    return []
  assert device is not None
  return [
    read_result(device, stream.source, result_base=stream.result_base, name=stream.name)
    for stream in streams
  ]


def b_pairs(cores: list[Core], *, noc: int, row: int | None) -> tuple[Core, Core, list[Core]]:
  y, xs = choose_row(cores, row)
  victim_src = (xs[0], y) if noc == 0 else (xs[-1], y)
  victim_dst = (xs[-1], y) if noc == 0 else (xs[0], y)
  path_nodes = set(noc_path(victim_src, victim_dst, noc).nodes)
  injections = [
    (x, y) for x in (xs[1:-1] if noc == 0 else list(reversed(xs[1:-1])))
    if (x, y) in path_nodes
  ]
  if not injections:
    raise ValueError("victim path has no intermediate worker cores to inject from")
  return victim_src, victim_dst, injections


def command_b(args):
  validate_bytes(args.bytes)
  device = None if args.dry_run else Device()
  cores = DEFAULT_P100_CORES if args.dry_run else device.cores
  rows: list[tuple[str, Result | None, Result | None, Core | None, int | None]] = []
  try:
    victim_src, victim_dst, injections = b_pairs(cores, noc=args.noc, row=args.row)
    baseline_stream = ActiveStream("victim", victim_src, victim_dst, ROLE_WRITER, RESULT_BASE)
    baseline = run_stream_set(
      device, [baseline_stream], noc=args.noc, stream_bytes=args.bytes,
      repeats=args.repeats, dry_run=args.dry_run, gate_delay_cycles=args.gate_delay_cycles,
    )
    rows.append(("baseline", baseline[0] if baseline else None, None, None, None))
    for idx, inj in enumerate(injections):
      streams = [
        ActiveStream("victim", victim_src, victim_dst, ROLE_WRITER, RESULT_BASE),
        ActiveStream("injector", inj, victim_dst, ROLE_WRITER, RESULT_BASE, None),
      ]
      # Put per-source results at the same address; they live in different L1s.
      results = run_stream_set(
        device, streams, noc=args.noc, stream_bytes=args.bytes,
        repeats=args.repeats, dry_run=args.dry_run, gate_delay_cycles=args.gate_delay_cycles,
      )
      rows.append((f"inject@{inj[0]},{inj[1]}", results[0] if results else None, results[1] if results else None, inj, idx + 1))
  finally:
    if device is not None:
      device.close()
  print(format_b(args.noc, victim_src, victim_dst, rows, dry=args.dry_run))
  if not args.no_report and not args.dry_run:
    append_report(args.report, "B", format_b(args.noc, victim_src, victim_dst, rows, dry=False))


def format_b(noc: int, victim_src: Core, victim_dst: Core,
             rows: list[tuple[str, Result | None, Result | None, Core | None, int | None]], *, dry: bool) -> str:
  lines = [
    f"NoC{noc} victim `{victim_src[0]},{victim_src[1]}` -> `{victim_dst[0]},{victim_dst[1]}` "
    f"(true hops {noc_hops(victim_src, victim_dst, noc)})",
    "",
    "| case | injection | path index | victim B/cyc | injector B/cyc | victim counter | injector counter |",
    "|---|---|---:|---:|---:|---:|---:|",
  ]
  for label, victim, injector, inj_core, path_idx in rows:
    inj = "" if inj_core is None else f"`{inj_core[0]},{inj_core[1]}`"
    if dry:
      lines.append(f"| {label} | {inj} | {path_idx or 0} | dry-run | dry-run |  |  |")
    else:
      assert victim is not None
      inj_bpc = "" if injector is None else f"{injector.bytes_per_cycle():.3f}"
      inj_ctr = "" if injector is None else str(injector.counter_delta)
      lines.append(
        f"| {label} | {inj} | {path_idx or 0} | {victim.bytes_per_cycle():.3f} | "
        f"{inj_bpc} | {victim.counter_delta} | {inj_ctr} |"
      )
  return "\n".join(lines)


def choose_same_row_pair(cores: list[Core], *, noc: int, row: int | None) -> tuple[Core, Core]:
  y, xs = choose_row(cores, row)
  return ((xs[0], y), (xs[-1], y)) if noc == 0 else ((xs[-1], y), (xs[0], y))


def command_e(args):
  validate_bytes(args.bytes)
  device = None if args.dry_run else Device()
  cores = DEFAULT_P100_CORES if args.dry_run else device.cores
  rows = []
  try:
    source, target = choose_same_row_pair(cores, noc=args.noc, row=args.row)
    vc_pairs = [(args.read_vc, args.write_vc)]
    if args.vc_sweep:
      vc_pairs = [(None, None), (1, 1), (1, 5), (5, 1), (5, 5)]
    for read_vc, write_vc in vc_pairs:
      read_ctrl = static_vc_ctrl(ROLE_READER, read_vc)
      write_ctrl = static_vc_ctrl(ROLE_WRITER, write_vc)
      read_stream = ActiveStream("read_alone", source, target, ROLE_READER, RESULT_BASE, read_ctrl)
      if device is not None and not args.dry_run:
        clear_cores(device, [source, target], stream_bytes=args.bytes, source_cores=set(), target_cores={target})
      read_prog = MultiCoreProgram([read_stream], noc=args.noc, stream_bytes=args.bytes, repeats=args.repeats)
      maybe_run(device, read_prog, [source, target], dry_run=args.dry_run, gate_delay_cycles=args.gate_delay_cycles)
      read_alone = None if args.dry_run else read_result(device, source, result_base=RESULT_BASE, name="read_alone")

      if device is not None and not args.dry_run:
        clear_cores(device, [source, target], stream_bytes=args.bytes, source_cores={source}, target_cores={target})
      rw_prog = SameCoreReadWriteProgram(
        source=source, target=target, noc=args.noc, stream_bytes=args.bytes,
        repeats=args.repeats, read_ctrl=read_ctrl, write_ctrl=write_ctrl,
      )
      maybe_run(device, rw_prog, [source, target], dry_run=args.dry_run, gate_delay_cycles=args.gate_delay_cycles)
      read_with = None if args.dry_run else read_result(device, source, result_base=RESULT_BASE + RESULT_STRIDE, name="read_with_write")
      write_res = None if args.dry_run else read_result(device, source, result_base=RESULT_BASE, name="write_saturator")
      rows.append((read_vc, write_vc, read_alone, read_with, write_res))
  finally:
    if device is not None:
      device.close()
  table = format_e(args.noc, source, target, rows, dry=args.dry_run)
  print(table)
  if not args.no_report and not args.dry_run:
    append_report(args.report, "E", table)


def format_e(noc: int, source: Core, target: Core, rows, *, dry: bool) -> str:
  lines = [
    f"NoC{noc} same-core read/write `{source[0]},{source[1]}` -> `{target[0]},{target[1]}` "
    f"(true hops {noc_hops(source, target, noc)})",
    "",
    "| read VC | write VC | read-alone B/cyc | read+write B/cyc | read slowdown | write B/cyc | read ctr | write ctr |",
    "|---:|---:|---:|---:|---:|---:|---:|---:|",
  ]
  for read_vc, write_vc, read_alone, read_with, write_res in rows:
    rv = "default" if read_vc is None else str(read_vc)
    wv = "default" if write_vc is None else str(write_vc)
    if dry:
      lines.append(f"| {rv} | {wv} | dry-run | dry-run |  | dry-run |  |  |")
      continue
    ra = read_alone.bytes_per_cycle()
    rw = read_with.bytes_per_cycle()
    slowdown = ra / rw if rw > 0 else math.inf
    lines.append(
      f"| {rv} | {wv} | {ra:.3f} | {rw:.3f} | {slowdown:.3f}x | "
      f"{write_res.bytes_per_cycle():.3f} | {read_with.counter_delta} | {write_res.counter_delta} |"
    )
  return "\n".join(lines)


def bisection_pairs(cores: list[Core], *, max_pairs: int | None) -> list[tuple[Core, Core]]:
  pairs = []
  rows = rows_by_y(cores)
  for y, xs in sorted(rows.items()):
    left = [x for x in xs if x <= 7]
    right = [x for x in xs if x >= 10]
    for lx, rx in zip(reversed(left), right):
      pairs.append(((lx, y), (rx, y)))
  if max_pairs is not None:
    pairs = pairs[:max_pairs]
  if not pairs:
    raise ValueError("no left-half to right-half pairs found")
  return pairs


def command_f(args):
  validate_bytes(args.bytes)
  device = None if args.dry_run else Device()
  cores = DEFAULT_P100_CORES if args.dry_run else device.cores
  try:
    pairs = bisection_pairs(cores, max_pairs=args.max_pairs)
    single_stream = [ActiveStream("single", pairs[0][0], pairs[0][1], ROLE_WRITER, RESULT_BASE)]
    single = run_stream_set(
      device, single_stream, noc=args.noc, stream_bytes=args.bytes,
      repeats=args.repeats, dry_run=args.dry_run, gate_delay_cycles=args.gate_delay_cycles,
    )
    streams = [
      ActiveStream(f"p{i}", src, dst, ROLE_WRITER, RESULT_BASE)
      for i, (src, dst) in enumerate(pairs)
    ]
    aggregate = run_stream_set(
      device, streams, noc=args.noc, stream_bytes=args.bytes,
      repeats=args.repeats, dry_run=args.dry_run, gate_delay_cycles=args.gate_delay_cycles,
    )
  finally:
    if device is not None:
      device.close()
  table = format_f(args.noc, pairs, single[0] if single else None, aggregate, args.dry_run)
  print(table)
  if not args.no_report and not args.dry_run:
    append_report(args.report, "F", table)


def format_f(noc: int, pairs: list[tuple[Core, Core]], single: Result | None,
             aggregate: list[Result], dry: bool) -> str:
  if dry:
    agg = "dry-run"
    single_bpc = "dry-run"
    ratio = ""
  else:
    window = max(r.end for r in aggregate) - min(r.start for r in aggregate)
    total_bytes = sum(r.bytes_or_iters for r in aggregate)
    agg_bpc = total_bytes / window if window > 0 else 0.0
    sbpc = single.bytes_per_cycle()
    agg = f"{agg_bpc:.3f}"
    single_bpc = f"{sbpc:.3f}"
    ratio = f"{agg_bpc / sbpc:.3f}" if sbpc > 0 else "inf"
  lines = [
    f"NoC{noc} left-half -> right-half bisection, {len(pairs)} pairs",
    "",
    "| pairs | single-link B/cyc | aggregate cross-section B/cyc | aggregate / single-link | bad counters |",
    "|---:|---:|---:|---:|---:|",
  ]
  bad = "" if dry else str(sum(r.counter_delta != r.chunks_or_repeats for r in aggregate))
  lines.append(f"| {len(pairs)} | {single_bpc} | {agg} | {ratio} | {bad} |")
  return "\n".join(lines)


def hop_pairs(cores: list[Core], *, noc: int, row: int | None, source: Core | None, max_hops: int | None):
  return hop_sweep.build_pairs(cores, noc=noc, row=row, source=source, max_hops=max_hops)


def fit_line(points: list[tuple[float, float]]) -> tuple[float, float]:
  n = len(points)
  if n < 2:
    return 0.0, points[0][1] if points else 0.0
  sx = sum(x for x, _ in points)
  sy = sum(y for _, y in points)
  sxx = sum(x * x for x, _ in points)
  sxy = sum(x * y for x, y in points)
  denom = n * sxx - sx * sx
  if denom == 0:
    return 0.0, sy / n
  slope = (n * sxy - sx * sy) / denom
  intercept = (sy - slope * sx) / n
  return slope, intercept


def command_hop(args):
  if args.iters <= 0:
    raise ValueError("--iters must be positive")
  device = None if args.dry_run else Device()
  cores = DEFAULT_P100_CORES if args.dry_run else device.cores
  rows = []
  try:
    for noc in args.nocs:
      for source, target, _logical in hop_pairs(
        cores, noc=noc, row=args.row, source=args.core, max_hops=args.max_hops,
      ):
        true_hops = noc_hops(source, target, noc)
        if device is not None and not args.dry_run:
          clear_cores(
            device, [source, target], stream_bytes=NOC.MAX_BURST_SIZE,
            source_cores=set(), target_cores={target},
            pointer_targets={target: min(args.iters, args.chain_len)},
          )
        program = PointerProgram(
          source=source, target=target, noc=noc, iters=args.iters,
          ctrl=static_vc_ctrl(ROLE_POINTER, args.read_vc),
        )
        maybe_run(device, program, [source, target], dry_run=args.dry_run, gate_delay_cycles=args.gate_delay_cycles)
        result = None if args.dry_run else read_result(device, source, result_base=RESULT_BASE, name="pointer")
        rows.append((noc, source, target, true_hops, result))
  finally:
    if device is not None:
      device.close()
  table = format_hop(rows, dry=args.dry_run)
  print(table)
  if not args.no_report and not args.dry_run:
    append_report(args.report, "hop", table)


def format_hop(rows, *, dry: bool) -> str:
  lines = [
    "| noc | source | target | true hops | cyc/iter | counter delta | sink |",
    "|---:|---|---|---:|---:|---:|---:|",
  ]
  fit_points: dict[int, list[tuple[float, float]]] = {}
  for noc, source, target, hops, result in rows:
    if dry:
      lines.append(f"| {noc} | `{source[0]},{source[1]}` | `{target[0]},{target[1]}` | {hops} | dry-run |  |  |")
      continue
    cpi = result.cycles_per_iter()
    fit_points.setdefault(noc, []).append((hops, cpi))
    lines.append(
      f"| {noc} | `{source[0]},{source[1]}` | `{target[0]},{target[1]}` | {hops} | "
      f"{cpi:.3f} | {result.counter_delta} | 0x{result.sink:08x} |"
    )
  if not dry:
    lines.append("")
    lines.append("| noc | slope cyc/hop | intercept cyc |")
    lines.append("|---:|---:|---:|")
    for noc, points in sorted(fit_points.items()):
      slope, intercept = fit_line(points)
      lines.append(f"| {noc} | {slope:.3f} | {intercept:.3f} |")
  return "\n".join(lines)


def append_report(path: Path, experiment: str, table: str):
  harness.append_report(path, None, [
    f"Experiment: `{experiment}`",
    "Traffic: peer L1 unicast only, 16 KiB command trains except the dependent 4-byte hop chase",
    "Timing: per-active-core `WALL_CLOCK`; optional absolute start gate in L1",
    "Topology labels: host-side X-then-Y torus model with physical worker coordinates",
  ], table)


def add_common(p):
  p.add_argument("--dry-run", action="store_true", help="build programs and print planned rows without opening hardware")
  p.add_argument("--no-report", action="store_true", help="do not append microbenching/docs/noc-contention.md")
  p.add_argument("--report", type=Path, default=Path("microbenching/docs/noc-contention.md"))
  p.add_argument("--gate-delay-cycles", type=int, default=200_000_000,
                 help="future WALL_CLOCK start gate; set 0 to disable")


def main():
  parser = argparse.ArgumentParser(description="Blackhole NoC contention, VC, bisection, and per-hop probes.")
  sub = parser.add_subparsers(dest="mode", required=True)

  pb = sub.add_parser("b", aliases=["B", "victim"], help="Experiment B: crossing-traffic victim")
  add_common(pb)
  pb.add_argument("--noc", type=int, choices=(0, 1), default=0)
  pb.add_argument("--row", type=int, default=None)
  pb.add_argument("--bytes", type=int, default=256 * 1024, help="bytes per stream repeat; multiple of 16 KiB")
  pb.add_argument("--repeats", type=int, default=2)
  pb.set_defaults(func=command_b)

  pe = sub.add_parser("e", aliases=["E", "vc"], help="Experiment E: read/write virtual-channel isolation")
  add_common(pe)
  pe.add_argument("--noc", type=int, choices=(0, 1), default=0)
  pe.add_argument("--row", type=int, default=None)
  pe.add_argument("--bytes", type=int, default=256 * 1024, help="bytes per stream repeat; multiple of 16 KiB")
  pe.add_argument("--repeats", type=int, default=2)
  pe.add_argument("--read-vc", type=int, default=None, help="force read CMD static VC")
  pe.add_argument("--write-vc", type=int, default=None, help="force write CMD static VC")
  pe.add_argument("--vc-sweep", action="store_true", help="run default plus VC 1/5 combinations")
  pe.set_defaults(func=command_e)

  pf = sub.add_parser("f", aliases=["F", "bisection"], help="Experiment F: vertical bisection bandwidth")
  add_common(pf)
  pf.add_argument("--noc", type=int, choices=(0, 1), default=0)
  pf.add_argument("--bytes", type=int, default=256 * 1024, help="bytes per sender repeat; multiple of 16 KiB")
  pf.add_argument("--repeats", type=int, default=2)
  pf.add_argument("--max-pairs", type=int, default=None)
  pf.set_defaults(func=command_f)

  ph = sub.add_parser("hop", aliases=["latency"], help="Aux: dependent per-hop pointer-chase")
  add_common(ph)
  ph.add_argument("--nocs", type=hop_sweep.parse_nocs, default=(0, 1))
  ph.add_argument("--row", type=int, default=None)
  ph.add_argument("--core", type=harness.parse_core, default=None)
  ph.add_argument("--max-hops", type=int, default=None)
  ph.add_argument("--iters", type=int, default=64)
  ph.add_argument("--chain-len", type=int, default=256)
  ph.add_argument("--read-vc", type=int, default=None, help="force read CMD static VC")
  ph.set_defaults(func=command_hop)

  args = parser.parse_args()
  if getattr(args, "repeats", 1) <= 0:
    raise ValueError("--repeats must be positive")
  if args.gate_delay_cycles < 0:
    raise ValueError("--gate-delay-cycles must be non-negative")
  args.func(args)


if __name__ == "__main__":
  main()
