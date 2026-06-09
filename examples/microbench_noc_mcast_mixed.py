#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as _dt
import os
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
  sys.path.insert(0, str(Path(__file__).resolve().parent))

import riscv_core_bench as corebench
from asm import KernelBase
from device import Device
from dsl import a0, a1, a2, a3, a4, a5, a6, a7, s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, t0, t3, t4, t5, t6, zero
from pcie import TLBWindow
from program import DevMsgs, McastWrite, Program, Run, UnicastWrite, mcast_rects
from ttk.addrs import Core, L1_ALIGN, noc_xy
from ttk.mailbox import BriscMailbox as BM
from ttk.noc import NOC, Noc
from ttk.tensix import TensixL1


RESULT_BASE = 0x160000
STREAM_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
STREAM_SINK = STREAM_BASE + NOC.MAX_BURST_SIZE
SEM0_ADDR = TensixL1.KERNEL_CONFIG_BASE + L1_ALIGN
HEADER_WORDS = 16
RECORD_WORDS = 18
HEADER_SIZE = HEADER_WORDS * 4
RECORD_SIZE = RECORD_WORDS * 4
RESULT_MAGIC = 0x4D4E4D58  # "MNMX"
RECORD_MAGIC = 0x4D4E5258  # "MNRX"
STATUS_STARTED = 0x6D000001
STATUS_DONE = 0x6D00D00D

OP_EMPTY = 0
OP_MCAST_WRITE = 1
OP_SEM_MCAST_SET = 2
OP_ATOMIC_INC = 3
OP_READ_16K = 4
OP_WRITE_16K = 5
OP_MIXED_RWM = 6

OP_NAMES = {
  OP_EMPTY: "empty",
  OP_MCAST_WRITE: "mcast_write",
  OP_SEM_MCAST_SET: "sem_mcast_set",
  OP_ATOMIC_INC: "atomic_inc",
  OP_READ_16K: "read_16k",
  OP_WRITE_16K: "write_16k",
  OP_MIXED_RWM: "mixed_read_write_mcast",
}


@dataclass(frozen=True)
class RectSpec:
  x0: int
  y0: int
  x1: int
  y1: int
  num_dests: int


@dataclass(frozen=True)
class BenchSpec:
  name: str
  op: int
  noc: int
  byte_count: int
  rect: RectSpec
  read_noc: int = 0
  write_noc: int = 1
  mcast_noc: int = 0
  ops_per_iter: int = 1


@dataclass(frozen=True)
class BenchRecord:
  name: str
  op: int
  noc: int
  byte_count: int
  iterations: int
  num_dests: int
  cycles: int
  sink: int
  counter_delta: int
  aux0: int
  aux1: int


@dataclass(frozen=True)
class CaseRun:
  case: str
  source: Core
  peer: Core
  receivers: tuple[Core, ...]
  specs: tuple[BenchSpec, ...]
  records: list[BenchRecord]
  validation: dict[Core, tuple[int, int, int]]


class McastMixedKernel(KernelBase, Noc):
  pass


def result_size(specs: tuple[BenchSpec, ...]) -> int:
  return HEADER_SIZE + len(specs) * RECORD_SIZE


def emit_counter_read(fw: KernelBase, noc: int, counter: int, out, *, addr=t3):
  fw.li(addr, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  return fw.lw(out, addr, 0)


def emit_header(fw: KernelBase, *, specs: tuple[BenchSpec, ...], iterations: int, status: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, 1, len(specs), RECORD_WORDS, status, iterations,
    RESULT_BASE, STREAM_BASE, STREAM_SINK, NOC.MAX_BURST_SIZE, SEM0_ADDR,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off in range(11, HEADER_WORDS):
    fw.sw(zero, s2, off * 4)
  return fw


def emit_record(
  fw: KernelBase,
  *,
  test_id: int,
  spec: BenchSpec,
  iterations: int,
  start_lo,
  start_hi,
  end_lo,
  end_hi,
):
  fw.li(s2, RESULT_BASE + HEADER_SIZE + test_id * RECORD_SIZE)
  for off, value in enumerate((
    RECORD_MAGIC,
    test_id,
    spec.op,
    spec.noc,
    spec.byte_count,
    iterations,
    spec.rect.num_dests,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off, reg in enumerate((start_lo, start_hi, end_lo, end_hi, s1, s7, s8, s10, s11), start=7):
    fw.sw(reg, s2, off * 4)
  fw.sw(zero, s2, 16 * 4)
  fw.sw(zero, s2, 17 * 4)
  return fw


def emit_setup(fw: McastMixedKernel):
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s9,))
  fw.local_noc0_coord(s5, x_addr=BM.MY_X, y_addr=BM.MY_Y)
  fw.li(s1, 0x5A170C00)
  fw.li(s2, STREAM_BASE)
  fw.li(s3, STREAM_SINK)
  return fw.fence()


def emit_prepare_counters(fw: McastMixedKernel, spec: BenchSpec):
  fw.mv(s10, zero)
  fw.mv(s11, zero)
  if spec.op == OP_EMPTY:
    fw.mv(s7, zero)
    fw.mv(s8, zero)
    fw.mv(s6, zero)
  elif spec.op == OP_MCAST_WRITE or spec.op == OP_SEM_MCAST_SET:
    emit_counter_read(fw, spec.noc, NOC.NIU_MST_NONPOSTED_WR_REQ_SENT, s7)
    fw.mv(s6, s7)
  elif spec.op == OP_ATOMIC_INC:
    emit_counter_read(fw, spec.noc, NOC.NIU_MST_ATOMIC_RESP_RECEIVED, s7)
    fw.mv(s6, s7)
  elif spec.op == OP_READ_16K:
    emit_counter_read(fw, spec.noc, NOC.NIU_MST_RD_RESP_RECEIVED, s7)
    fw.mv(s6, s7)
  elif spec.op == OP_WRITE_16K:
    emit_counter_read(fw, spec.noc, NOC.NIU_MST_WR_ACK_RECEIVED, s7)
    fw.mv(s6, s7)
  elif spec.op == OP_MIXED_RWM:
    emit_counter_read(fw, spec.read_noc, NOC.NIU_MST_RD_RESP_RECEIVED, s10)
    emit_counter_read(fw, spec.write_noc, NOC.NIU_MST_WR_ACK_RECEIVED, s11)
    emit_counter_read(fw, spec.mcast_noc, NOC.NIU_MST_NONPOSTED_WR_REQ_SENT, s7)
    fw.mv(s6, s7)
    fw.mv(t5, s10)
    fw.mv(t6, s11)
  else:
    raise ValueError(f"unknown op {spec.op}")
  return fw


def emit_mcast_write_once(fw: McastMixedKernel, noc: int):
  fw.noc_write(noc, 0, s2, s2, 0, a0, s4, mcast=True, mcast_linked=False, a=t3, v=t4)
  fw.addi(s6, s6, 1)
  return fw.noc_nonposted_writes_flushed(noc, s6, addr=t3, val=t4)


def emit_sem_mcast_once(fw: McastMixedKernel, noc: int):
  fw.noc_semaphore_set_multicast(noc, 0, a1, a0, 1, 1, a=t3, v=t4)
  fw.addi(s6, s6, 1)
  return fw.noc_nonposted_writes_flushed(noc, s6, addr=t3, val=t4)


def emit_atomic_inc_once(fw: McastMixedKernel, noc: int):
  fw.noc_semaphore_inc(noc, 3, a1, s9, 1, ret_coord=s5, a=t3, v=t4)
  fw.addi(s6, s6, 1)
  return fw.noc_wait_atomic_responses(noc, s6, addr=t3, val=t4)


def emit_read_once(fw: McastMixedKernel, noc: int):
  fw.noc_read(noc, 1, s2, 0, s9, s3, s4, ret_coord=s5, a=t3, v=t4)
  fw.addi(s6, s6, 1)
  return fw.noc_reads_flushed(noc, s6, addr=t3, val=t4)


def emit_write_once(fw: McastMixedKernel, noc: int):
  fw.noc_write(noc, 0, s2, s2, 0, s9, s4, posted=False, a=t3, v=t4)
  fw.addi(s6, s6, 1)
  return fw.noc_write_barrier(noc, s6, addr=t3, val=t4)


def emit_mixed_once(fw: McastMixedKernel, spec: BenchSpec):
  fw.noc_read(spec.read_noc, 1, s2, 0, s9, s3, s4, ret_coord=s5, a=t3, v=t4)
  fw.addi(t5, t5, 1)
  fw.noc_write(spec.write_noc, 0, s2, s2, 0, s9, s4, posted=False, a=t3, v=t4)
  fw.addi(t6, t6, 1)
  fw.noc_write(spec.mcast_noc, 0, s2, s2, 0, a0, s4, mcast=True, mcast_linked=False, a=t3, v=t4)
  fw.addi(s6, s6, 1)
  fw.noc_reads_flushed(spec.read_noc, t5, addr=t3, val=t4)
  fw.noc_write_barrier(spec.write_noc, t6, addr=t3, val=t4)
  return fw.noc_nonposted_writes_flushed(spec.mcast_noc, s6, addr=t3, val=t4)


def emit_loop_body(fw: McastMixedKernel, spec: BenchSpec):
  if spec.op == OP_EMPTY:
    fw.addi(s1, s1, 1)
  elif spec.op == OP_MCAST_WRITE:
    emit_mcast_write_once(fw, spec.noc)
  elif spec.op == OP_SEM_MCAST_SET:
    emit_sem_mcast_once(fw, spec.noc)
  elif spec.op == OP_ATOMIC_INC:
    emit_atomic_inc_once(fw, spec.noc)
  elif spec.op == OP_READ_16K:
    emit_read_once(fw, spec.noc)
  elif spec.op == OP_WRITE_16K:
    emit_write_once(fw, spec.noc)
  elif spec.op == OP_MIXED_RWM:
    emit_mixed_once(fw, spec)
  else:
    raise ValueError(f"unknown op {spec.op}")
  return fw


def emit_finish_counters(fw: McastMixedKernel, spec: BenchSpec):
  if spec.op == OP_EMPTY:
    fw.mv(s8, s7)
  elif spec.op in (OP_MCAST_WRITE, OP_SEM_MCAST_SET):
    emit_counter_read(fw, spec.noc, NOC.NIU_MST_NONPOSTED_WR_REQ_SENT, s8)
  elif spec.op == OP_ATOMIC_INC:
    emit_counter_read(fw, spec.noc, NOC.NIU_MST_ATOMIC_RESP_RECEIVED, s8)
  elif spec.op == OP_READ_16K:
    emit_counter_read(fw, spec.noc, NOC.NIU_MST_RD_RESP_RECEIVED, s8)
  elif spec.op == OP_WRITE_16K:
    emit_counter_read(fw, spec.noc, NOC.NIU_MST_WR_ACK_RECEIVED, s8)
    emit_counter_read(fw, spec.noc, NOC.NIU_MST_RD_RESP_RECEIVED, t0, addr=t3)
    fw.addi(t0, t0, 1)
    fw.noc_read(spec.noc, 1, s2, 0, s9, s3, s4, ret_coord=s5, a=t3, v=t4)
    fw.noc_reads_flushed(spec.noc, t0, addr=t3, val=t4)
  elif spec.op == OP_MIXED_RWM:
    emit_counter_read(fw, spec.read_noc, NOC.NIU_MST_RD_RESP_RECEIVED, a6)
    fw.sub(s10, a6, s10)
    emit_counter_read(fw, spec.write_noc, NOC.NIU_MST_WR_ACK_RECEIVED, a6)
    fw.sub(s11, a6, s11)
    emit_counter_read(fw, spec.mcast_noc, NOC.NIU_MST_NONPOSTED_WR_REQ_SENT, s8)
  return fw


def emit_timed_spec(fw: McastMixedKernel, *, test_id: int, spec: BenchSpec, iterations: int):
  emit_setup(fw)
  fw.li(s4, spec.byte_count)
  if spec.rect.num_dests:
    fw.noc_mcast_coord(a0, spec.rect.x0, spec.rect.y0, spec.rect.x1, spec.rect.y1)
  else:
    fw.mv(a0, zero)
  fw.sem_addr(BM.SEM_L1_BASE, 0, out=a1)
  emit_prepare_counters(fw, spec)

  corebench.read_wall_clock(fw, a2, a3)
  fw.li(s0, iterations)
  loop = fw._new_label(f"bench_{test_id}_loop")
  done = fw._new_label(f"bench_{test_id}_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  emit_loop_body(fw, spec)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  corebench.read_wall_clock(fw, a4, a5)

  emit_finish_counters(fw, spec)
  fw.lw(s1, s3, 0)
  emit_record(
    fw,
    test_id=test_id,
    spec=spec,
    iterations=iterations,
    start_lo=a2,
    start_hi=a3,
    end_lo=a4,
    end_hi=a5,
  )
  return fw


def build_kernel(specs: tuple[BenchSpec, ...], *, iterations: int) -> KernelBase:
  fw = McastMixedKernel()
  emit_header(fw, specs=specs, iterations=iterations, status=STATUS_STARTED)
  for test_id, spec in enumerate(specs):
    emit_timed_spec(fw, test_id=test_id, spec=spec, iterations=iterations)
  emit_header(fw, specs=specs, iterations=iterations, status=STATUS_DONE)
  return fw.ret()


def _single_core_program(kernel: KernelBase, *, semaphores: int) -> Program:
  empty = KernelBase()
  return Program(
    brisc=kernel,
    ncrisc=empty,
    trisc0=empty,
    trisc1=empty,
    trisc2=empty,
    semaphores=semaphores,
    num_cores=1,
  )


class SelectedCoreProgram:
  def __init__(
    self,
    *,
    source: Core,
    active_cores: list[Core],
    sender: KernelBase,
    receiver: KernelBase,
    semaphores: int,
    name: str,
  ):
    self.source = source
    self.active_cores = list(active_cores)
    self.sender = sender
    self.receiver = receiver
    self.semaphores = semaphores
    self.name = name

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    per_core_segments = {}
    compiled_cache: dict[int, list] = {}
    for core in self.active_cores:
      kernel = self.sender if core == self.source else self.receiver
      per_core_segments[core] = _single_core_program(kernel, semaphores=self.semaphores).layout(
        core_xy=core,
        dispatch_mode=dispatch_mode,
        host_assigned_id=host_assigned_id,
        compiled_cache=compiled_cache,
      )

    reset_blob = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_RESET_READ_PTR_FROM_HOST)
    commands = [
      McastWrite(mcast_rects(self.active_cores), TensixL1.GO_MSG, reset_blob),
      McastWrite(mcast_rects(self.active_cores), TensixL1.GO_MSG_INDEX, b"\0\0\0\0"),
    ]
    for core in self.active_cores:
      for segment in per_core_segments[core]:
        commands.append(UnicastWrite([core], segment.addr, [segment.data]))
    commands.append(Run(self.active_cores))
    return commands


def make_specs(rect: RectSpec, *, include_mixed: bool) -> tuple[BenchSpec, ...]:
  specs = [
    BenchSpec("empty", OP_EMPTY, 0, 0, rect, ops_per_iter=0),
    BenchSpec("mcast_write_noc0_16k", OP_MCAST_WRITE, 0, NOC.MAX_BURST_SIZE, rect),
    BenchSpec("mcast_write_noc1_16k", OP_MCAST_WRITE, 1, NOC.MAX_BURST_SIZE, rect),
    BenchSpec("sem_mcast_set_noc0", OP_SEM_MCAST_SET, 0, L1_ALIGN, rect),
    BenchSpec("sem_mcast_set_noc1", OP_SEM_MCAST_SET, 1, L1_ALIGN, rect),
    BenchSpec("atomic_inc_noc0", OP_ATOMIC_INC, 0, 4, rect),
    BenchSpec("atomic_inc_noc1", OP_ATOMIC_INC, 1, 4, rect),
    BenchSpec("read_peer_noc0_16k", OP_READ_16K, 0, NOC.MAX_BURST_SIZE, rect),
    BenchSpec("write_peer_noc1_16k", OP_WRITE_16K, 1, NOC.MAX_BURST_SIZE, rect),
  ]
  if include_mixed:
    specs.extend((
      BenchSpec(
        "mixed_read0_write1_mcast0_16k",
        OP_MIXED_RWM,
        0,
        NOC.MAX_BURST_SIZE,
        rect,
        read_noc=0,
        write_noc=1,
        mcast_noc=0,
        ops_per_iter=3,
      ),
      BenchSpec(
        "mixed_read1_write0_mcast1_16k",
        OP_MIXED_RWM,
        1,
        NOC.MAX_BURST_SIZE,
        rect,
        read_noc=1,
        write_noc=0,
        mcast_noc=1,
        ops_per_iter=3,
      ),
    ))
  return tuple(specs)


def parse_cases(text: str) -> tuple[str, ...]:
  cases = tuple(item.strip() for item in text.split(",") if item.strip())
  bad = [case for case in cases if case not in {"row", "column"}]
  if bad:
    raise argparse.ArgumentTypeError(f"unknown case(s): {','.join(bad)}")
  if not cases:
    raise argparse.ArgumentTypeError("expected at least one case")
  return cases


def select_row_case(cores: list[Core], dests: int) -> tuple[Core, tuple[Core, ...]]:
  rows: dict[int, list[int]] = {}
  for x, y in cores:
    rows.setdefault(y, []).append(x)
  for y, xs in sorted(rows.items()):
    xs = sorted(xs)
    if len(xs) >= dests + 1:
      return (xs[0], y), tuple((x, y) for x in xs[1:1 + dests])
  raise ValueError(f"no row has {dests + 1} program cores")


def select_column_case(cores: list[Core], dests: int) -> tuple[Core, tuple[Core, ...]]:
  cols: dict[int, list[int]] = {}
  for x, y in cores:
    cols.setdefault(x, []).append(y)
  for x, ys in sorted(cols.items()):
    ys = sorted(ys)
    if len(ys) >= dests + 1:
      return (x, ys[0]), tuple((x, y) for y in ys[1:1 + dests])
  raise ValueError(f"no column has {dests + 1} program cores")


def rect_for(case: str, source: Core, receivers: tuple[Core, ...]) -> RectSpec:
  if not receivers:
    return RectSpec(0, 0, 0, 0, 0)
  if case == "row":
    xs = [core[0] for core in receivers]
    y = source[1]
    return RectSpec(min(xs), y, max(xs), y, len(receivers))
  ys = [core[1] for core in receivers]
  x = source[0]
  return RectSpec(x, max(ys), x, min(ys), len(receivers))


def seed_payload(stream_bytes: int) -> bytes:
  seed = bytearray(NOC.MAX_BURST_SIZE)
  for off in range(0, len(seed), 4):
    struct.pack_into("<I", seed, off, 0xA5000000 | off)
  return bytes(seed) * (stream_bytes // NOC.MAX_BURST_SIZE)


def clear_and_seed(device: Device, cores: list[Core], specs: tuple[BenchSpec, ...], *, stream_bytes: int):
  payload = seed_payload(stream_bytes)
  device.dev.set_power_state(True)
  try:
    with TLBWindow(device.dev, start=cores[0]) as win:
      for core in cores:
        win.target(core)
        win.write(RESULT_BASE, b"\0" * result_size(specs))
        win.write(STREAM_BASE, payload if core == cores[0] else b"\0" * stream_bytes)
        win.write(STREAM_SINK, b"\0" * NOC.MAX_BURST_SIZE)
  finally:
    device.dev.set_power_state(False)


def read_result_blob(device: Device, source: Core, specs: tuple[BenchSpec, ...]) -> bytes:
  device.dev.set_power_state(True)
  try:
    with TLBWindow(device.dev, start=source) as win:
      blob = win.read(RESULT_BASE, result_size(specs))
  finally:
    device.dev.set_power_state(False)
  if blob and all(b == 0xFF for b in blob):
    raise RuntimeError("L1 readback returned all 0xff; device is not responding cleanly")
  return blob


def read_validation(device: Device, cores: list[Core], *, stream_bytes: int) -> dict[Core, tuple[int, int, int]]:
  out: dict[Core, tuple[int, int, int]] = {}
  device.dev.set_power_state(True)
  try:
    with TLBWindow(device.dev, start=cores[0]) as win:
      for core in cores:
        win.target(core)
        first = struct.unpack("<I", win.read(STREAM_BASE, 4))[0]
        last = struct.unpack("<I", win.read(STREAM_BASE + stream_bytes - 4, 4))[0]
        sem0 = struct.unpack("<I", win.read(SEM0_ADDR, 4))[0]
        out[core] = (first, last, sem0)
  finally:
    device.dev.set_power_state(False)
  return out


def parse_results(blob: bytes, specs: tuple[BenchSpec, ...]) -> list[BenchRecord]:
  header = struct.unpack_from("<" + "I" * HEADER_WORDS, blob, 0)
  if header[0] != RESULT_MAGIC:
    raise RuntimeError(f"bad result magic 0x{header[0]:08x}")
  if header[4] != STATUS_DONE:
    raise RuntimeError(f"benchmark did not finish, status=0x{header[4]:08x}")
  if header[2] != len(specs) or header[3] != RECORD_WORDS:
    raise RuntimeError(f"unexpected result layout: specs={header[2]} record_words={header[3]}")
  records = []
  for test_id, spec in enumerate(specs):
    off = HEADER_SIZE + test_id * RECORD_SIZE
    words = struct.unpack_from("<" + "I" * RECORD_WORDS, blob, off)
    if words[0] != RECORD_MAGIC:
      raise RuntimeError(f"{spec.name}: bad record magic 0x{words[0]:08x}")
    start = words[7] | (words[8] << 32)
    end = words[9] | (words[10] << 32)
    records.append(BenchRecord(
      name=spec.name,
      op=words[2],
      noc=words[3],
      byte_count=words[4],
      iterations=words[5],
      num_dests=words[6],
      cycles=(end - start) & ((1 << 64) - 1),
      sink=words[11],
      counter_delta=(words[13] - words[12]) & 0xFFFFFFFF,
      aux0=words[14],
      aux1=words[15],
    ))
  return records


def adjusted(records: list[BenchRecord]) -> dict[str, float]:
  empty = next(record for record in records if record.op == OP_EMPTY)
  empty_cpi = empty.cycles / empty.iterations
  out = {}
  for record in records:
    if record.op == OP_EMPTY:
      continue
    cycles = record.cycles - empty_cpi * record.iterations
    out[record.name] = cycles / record.iterations
  return out


def format_records(run: CaseRun) -> str:
  empty = next(record for record in run.records if record.op == OP_EMPTY)
  empty_cpi = empty.cycles / empty.iterations
  lines = [
    "| case | test | noc | op | bytes | dests | cycles | adj cyc/op | source B/cyc | counter delta | aux0 | aux1 | sink |",
    "|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
  ]
  for record in run.records:
    if record.op == OP_EMPTY:
      adj = 0.0
      bpc = 0.0
    else:
      adj = (record.cycles - empty_cpi * record.iterations) / record.iterations
      bpc = record.byte_count / adj if adj > 0 and record.byte_count else 0.0
    noc = "" if record.op == OP_EMPTY else str(record.noc)
    lines.append(
      f"| {run.case} | {record.name} | {noc} | {OP_NAMES.get(record.op, str(record.op))} | "
      f"{record.byte_count} | {record.num_dests} | {record.cycles} | {adj:.3f} | {bpc:.3f} | "
      f"{record.counter_delta} | {record.aux0} | {record.aux1} | 0x{record.sink:08x} |"
    )
  return "\n".join(lines)


def format_validation(run: CaseRun) -> str:
  lines = [
    "| case | core | first word | last word | sem0 |",
    "|---|---|---:|---:|---:|",
  ]
  for core, (first, last, sem0) in run.validation.items():
    lines.append(f"| {run.case} | `{core[0]},{core[1]}` | 0x{first:08x} | 0x{last:08x} | {sem0} |")
  return "\n".join(lines)


def proposed_constants(runs: list[CaseRun]) -> str:
  def best_bpc(names: tuple[str, ...]) -> float:
    vals = []
    for run in runs:
      adj = adjusted(run.records)
      for name in names:
        record = next((r for r in run.records if r.name == name), None)
        if record is None:
          continue
        cyc = adj[name]
        if cyc > 0 and record.byte_count:
          vals.append(record.byte_count / cyc)
    return min(vals) if vals else 0.0

  def mean_cyc(names: tuple[str, ...]) -> float:
    vals = []
    for run in runs:
      adj = adjusted(run.records)
      vals.extend(adj[name] for name in names if name in adj)
    return sum(vals) / len(vals) if vals else 0.0

  mcast_bpc = best_bpc(("mcast_write_noc0_16k", "mcast_write_noc1_16k"))
  sem_mcast_cycles = mean_cyc(("sem_mcast_set_noc0", "sem_mcast_set_noc1"))
  atomic_cycles = mean_cyc(("atomic_inc_noc0", "atomic_inc_noc1"))
  mixed_cycles = mean_cyc(("mixed_read0_write1_mcast0_16k", "mixed_read1_write0_mcast1_16k"))
  lines = [
    "| constant | proposed value | note |",
    "|---|---:|---|",
    f"| `NOC_MCAST_16K_BPC` | {mcast_bpc:.3f} | min observed source-bytes/cycle for safe unlinked row/column multicast |",
    f"| `NOC_SEM_MCAST_CYCLES` | {sem_mcast_cycles:.3f} | mean BRISC issue + nonposted flush for `noc_semaphore_set_multicast` |",
    f"| `NOC_SEM_INC_ACK_CYCLES` | {atomic_cycles:.3f} | mean `noc_semaphore_inc` plus atomic response wait |",
  ]
  if mixed_cycles:
    lines.append(f"| `NOC_MIXED_RWM_16K_CYCLES` | {mixed_cycles:.3f} | mean read+write+mcast safe-loop bundle, one 16KiB packet each |")
  return "\n".join(lines)


def append_report(path: Path, *, argv: list[str], iterations: int, runs: list[CaseRun]):
  now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
  with path.open("a", encoding="utf-8") as f:
    f.write(f"\n## Run {now}\n\n")
    f.write("Command:\n\n")
    f.write("```sh\n")
    f.write(" ".join(argv) + "\n")
    f.write("```\n\n")
    f.write(f"- Iterations per timed loop: `{iterations}`\n")
    f.write("- Dispatch path: slow dispatch (`TT_USB=1`); hardware run timeout set by `BLACKHOLE_RUN_TIMEOUT_S`.\n")
    f.write("- Multicast policy: unlinked multicast writes only, with a nonposted-write-sent flush before the next multicast reservation.\n")
    f.write("- Mixed policy: issue one read, one write, and one multicast, then drain all three before the next iteration.\n\n")
    for run in runs:
      f.write(f"### Case `{run.case}`\n\n")
      f.write(f"- Source: `{run.source[0]},{run.source[1]}`\n")
      f.write(f"- Atomic peer: `{run.peer[0]},{run.peer[1]}`\n")
      f.write("- Receivers: " + ", ".join(f"`{x},{y}`" for x, y in run.receivers) + "\n\n")
      f.write(format_records(run))
      f.write("\n\nValidation readback:\n\n")
      f.write(format_validation(run))
      f.write("\n\n")
    f.write("### Proposed Constants\n\n")
    f.write(proposed_constants(runs))
    f.write("\n")


def run_case(device: Device, case: str, *, dests: int, iterations: int, include_mixed: bool) -> CaseRun:
  if case == "row":
    source, receivers = select_row_case(device.cores, dests)
  else:
    source, receivers = select_column_case(device.cores, dests)
  peer = receivers[0]
  rect = rect_for(case, source, receivers)
  specs = make_specs(rect, include_mixed=include_mixed)
  active_cores = [source, *receivers]
  sender = build_kernel(specs, iterations=iterations)
  sender.rta(lambda _x, _y, peer=peer: [noc_xy(*peer)])
  receiver = KernelBase().ret()
  receiver.rta(lambda _x, _y: [0])
  clear_and_seed(device, active_cores, specs, stream_bytes=NOC.MAX_BURST_SIZE)
  program = SelectedCoreProgram(
    source=source,
    active_cores=active_cores,
    sender=sender,
    receiver=receiver,
    semaphores=4,
    name=f"microbench_noc_mcast_mixed:{case}:dests{dests}",
  )
  device.run(program)
  records = parse_results(read_result_blob(device, source, specs), specs)
  validation = read_validation(device, active_cores, stream_bytes=NOC.MAX_BURST_SIZE)
  return CaseRun(case, source, peer, receivers, specs, records, validation)


def main():
  parser = argparse.ArgumentParser(description="Conservative Blackhole NoC multicast, semaphore, atomic, and mixed-traffic microbench.")
  parser.add_argument("--cases", type=parse_cases, default=("row", "column"), help="comma-separated cases: row,column")
  parser.add_argument("--dests", type=int, default=3, help="receivers in each multicast rectangle")
  parser.add_argument("--iters", type=int, default=4, help="iterations per timed loop; keep small for multicast safety")
  parser.add_argument("--skip-mixed", action="store_true", help="skip mixed read+write+mcast tests")
  parser.add_argument("--no-report", action="store_true", help="do not append docs/noc-mcast-mixed-microbench.md")
  parser.add_argument("--report", type=Path, default=Path("docs/noc-mcast-mixed-microbench.md"))
  args = parser.parse_args()
  if args.dests <= 0:
    raise ValueError("--dests must be positive")
  if args.iters <= 0:
    raise ValueError("--iters must be positive")

  os.environ.setdefault("TT_USB", "1")
  os.environ.setdefault("BLACKHOLE_RUN_TIMEOUT_S", "5.0")
  device = Device()
  runs: list[CaseRun] = []
  try:
    for case in args.cases:
      runs.append(run_case(device, case, dests=args.dests, iterations=args.iters, include_mixed=not args.skip_mixed))
  finally:
    device.close()

  for run in runs:
    print(f"\n## {run.case}")
    print(format_records(run))
    print("\nvalidation:")
    print(format_validation(run))
  print("\n## Proposed constants")
  print(proposed_constants(runs))
  if not args.no_report:
    append_report(args.report, argv=sys.argv, iterations=args.iters, runs=runs)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
