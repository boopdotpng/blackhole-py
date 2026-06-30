#!/usr/bin/env python3
from __future__ import annotations

import argparse
import statistics
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402  (does sys.path + TT_USB bootstrap on import)
try:
  import noc_topology
except ModuleNotFoundError:
  from microbenching.noc import noc_topology
from asm import KernelBase
from device import Device
from dsl import a2, a3, a4, a5, s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, t0, t1, t3, t4, zero
from pcie import TLBWindow
from program import DevMsgs, Program, Run, UnicastWrite
from ttk.addrs import Core, align_down, noc_xy
from ttk.mailbox import BriscMailbox as BM
from ttk.noc import NOC, Noc
from ttk.tensix import TensixL1, TensixMMIO


RESULT_BASE = 0x150000
START_GATE_BASE = 0x148000
COUNTER_BASE = 0x148100
MIXED_WRITE_BASE = 0x148400
STREAM_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
MIXED_WRITE_STRIDE = 16
MIXED_WRITE_BYTES = 16
RECORD_WORDS = 32
RECORD_SIZE = RECORD_WORDS * 4
RESULT_MAGIC = 0x524E4154  # "RNAT"
STATUS_STARTED = 0xA7000001
STATUS_DONE = 0xA700D00D
ROLE_SENDER = 1
ROLE_TARGET = 2
OP_ATOMIC = 1
OP_SEM = 2
OP_MIXED = 3
OP_SEM_NORET = 4
ISSUE_PIPELINED = 1
ISSUE_BLOCKING = 2
P100_PROGRAM_CORES = [(x, y) for y in noc_topology.P100_WORKER_Y for x in noc_topology.P100_WORKER_X]
P100_FAST_DISPATCH_RESERVED = {(14, 2), (14, 3)}


@dataclass(frozen=True)
class SenderSpec:
  index: int
  source: Core
  targets: tuple[Core, ...]

  @property
  def first_target(self) -> Core:
    return self.targets[0]


@dataclass(frozen=True)
class TargetSpec:
  core: Core
  expected_value: int
  write_senders: tuple[int, ...]


@dataclass(frozen=True)
class CasePlan:
  name: str
  pattern: str
  op: int
  issue_mode: int
  noc: int
  count: int
  senders: tuple[SenderSpec, ...]
  targets: tuple[TargetSpec, ...]


@dataclass(frozen=True)
class CoreResult:
  core: Core
  words: tuple[int, ...]

  @property
  def role(self) -> int:
    return self.words[1]

  @property
  def sender_index(self) -> int:
    return self.words[4]

  @property
  def start(self) -> int:
    return self.words[13] | (self.words[14] << 32)

  @property
  def end(self) -> int:
    return self.words[15] | (self.words[16] << 32)

  @property
  def cycles(self) -> int:
    return (self.end - self.start) & ((1 << 64) - 1)

  @property
  def atomic_delta(self) -> int:
    return (self.words[18] - self.words[17]) & 0xFFFFFFFF

  @property
  def write_ack_delta(self) -> int:
    return (self.words[20] - self.words[19]) & 0xFFFFFFFF

  @property
  def observed_value(self) -> int:
    return self.words[21]

  @property
  def value_observed(self) -> int:
    return self.words[22] | (self.words[23] << 32)

  @property
  def writes_observed(self) -> int:
    return self.words[24] | (self.words[25] << 32)

  @property
  def poll_iters(self) -> int:
    return self.words[26]

  @property
  def missing_writes(self) -> int:
    return self.words[27]

  @property
  def issue_mode(self) -> int:
    return self.words[28]

  @property
  def issue_end(self) -> int:
    return self.words[30] | (self.words[31] << 32)

  @property
  def issue_cycles(self) -> int:
    return (self.issue_end - self.start) & ((1 << 64) - 1)


@dataclass(frozen=True)
class BenchRun:
  plan: CasePlan
  sender_results: tuple[CoreResult, ...]
  target_results: tuple[CoreResult, ...]


class AtomicKernel(KernelBase, Noc):
  pass


def op_name(op: int) -> str:
  return {OP_ATOMIC: "atomic", OP_SEM: "sem", OP_MIXED: "mixed", OP_SEM_NORET: "sem-noret"}[op]


def issue_mode_name(issue_mode: int) -> str:
  return {ISSUE_PIPELINED: "pipelined", ISSUE_BLOCKING: "blocking"}[issue_mode]


def op_has_source_response(op: int) -> bool:
  return op != OP_SEM_NORET


def mixed_sentinel(sender_index: int) -> int:
  return 0xA77C0000 | (sender_index & 0xFFFF)


def result_size() -> int:
  return RECORD_SIZE


def u64(lo: int, hi: int) -> int:
  return lo | (hi << 32)


def emit_counter_read(fw: KernelBase, noc: int, counter: int, out, *, addr=t3):
  fw.li(addr, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  return fw.lw(out, addr, 0)


def emit_record_header(
  fw: KernelBase, *,
  role: int,
  noc: int,
  sender_index: int,
  count: int,
  target_count: int,
  iters: int,
  op: int,
  source: Core,
  first_target: Core,
):
  fw.li(s2, RESULT_BASE)
  values = (
    RESULT_MAGIC, role, STATUS_STARTED, noc, sender_index, count, target_count, iters,
    op, source[0], source[1], first_target[0], first_target[1],
  )
  for off, value in enumerate(values):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off in range(len(values), RECORD_WORDS):
    fw.sw(zero, s2, off * 4)
  return fw


def emit_status_done(fw: KernelBase):
  fw.li(s2, RESULT_BASE)
  fw.li(t0, STATUS_DONE)
  fw.sw(t0, s2, 2 * 4)
  return fw


def emit_start_gate(fw: AtomicKernel):
  wait = fw._new_label("start_gate_wait")
  done = fw._new_label("start_gate_done")
  fw.li(s2, START_GATE_BASE)
  fw.lw(s10, s2, 0)
  fw.lw(s11, s2, 4)
  fw.label(wait)
  harness.read_wall_clock(fw, a2, a3)
  fw.bltu(a3, s11, wait)
  fw.bne(a3, s11, done)
  fw.bltu(a2, s10, wait)
  fw.label(done)
  return fw


def build_sender(spec: SenderSpec, *, noc: int, count: int, op: int, issue_mode: int, iters: int) -> KernelBase:
  fw = AtomicKernel()
  emit_record_header(
    fw,
    role=ROLE_SENDER,
    noc=noc,
    sender_index=spec.index,
    count=count,
    target_count=len(spec.targets),
    iters=iters,
    op=op,
    source=spec.source,
    first_target=spec.first_target,
  )
  fw.local_noc_coord(noc, s5, x_addr=BM.MY_X, y_addr=BM.MY_Y)
  emit_start_gate(fw)

  emit_counter_read(fw, noc, NOC.NIU_MST_ATOMIC_RESP_RECEIVED, s7)
  emit_counter_read(fw, noc, NOC.NIU_MST_WR_ACK_RECEIVED, s8)
  fw.mv(s6, s7)
  if op_has_source_response(op):
    fw.li(t0, iters * len(spec.targets))
    fw.add(s6, s6, t0)
  fw.mv(s11, s8)
  if op == OP_MIXED:
    fw.li(t0, iters * len(spec.targets))
    fw.add(s11, s11, t0)
  fw.mv(s1, s7)
  fw.mv(s10, s8)

  harness.read_wall_clock(fw, a2, a3)
  fw.li(s0, iters)
  loop = fw._new_label("atomic_sender_loop")
  done = fw._new_label("atomic_sender_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  for target in spec.targets:
    fw.li(s3, COUNTER_BASE)
    fw.li(s9, noc_xy(*target))
    if op == OP_SEM:
      fw.noc_semaphore_inc(noc, 3, s3, s9, 1, ret_coord=s5, a=t3, v=t4)
    elif op == OP_SEM_NORET:
      fw.noc_semaphore_inc(noc, 3, s3, s9, 1, ret_coord=0, a=t3, v=t4)
    else:
      fw.noc_atomic_inc(noc, 3, s3, s9, 1, ret_coord=s5, a=t3, v=t4)
    if issue_mode == ISSUE_BLOCKING and op_has_source_response(op):
      fw.addi(s1, s1, 1)
      fw.noc_wait_atomic_responses(noc, s1, addr=t3, val=t4)
    if op == OP_MIXED:
      fw.li(s2, STREAM_BASE)
      fw.li(s3, MIXED_WRITE_BASE + spec.index * MIXED_WRITE_STRIDE)
      fw.li(s4, MIXED_WRITE_BYTES)
      fw.noc_write(noc, 0, s2, s3, 0, s9, s4, posted=False, a=t3, v=t4)
      if issue_mode == ISSUE_BLOCKING:
        fw.addi(s10, s10, 1)
        fw.noc_write_barrier(noc, s10, addr=t3, val=t4)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  harness.read_wall_clock(fw, s0, s1)

  if issue_mode == ISSUE_PIPELINED and op_has_source_response(op):
    fw.noc_wait_atomic_responses(noc, s6, addr=t3, val=t4)
  if issue_mode == ISSUE_PIPELINED and op == OP_MIXED:
    fw.noc_write_barrier(noc, s11, addr=t3, val=t4)
  harness.read_wall_clock(fw, a4, a5)
  fw.li(s2, RESULT_BASE)
  for off, reg in enumerate((a2, a3, a4, a5, s7), start=13):
    fw.sw(reg, s2, off * 4)
  emit_counter_read(fw, noc, NOC.NIU_MST_ATOMIC_RESP_RECEIVED, t0)
  fw.sw(t0, s2, 18 * 4)
  fw.sw(s8, s2, 19 * 4)
  emit_counter_read(fw, noc, NOC.NIU_MST_WR_ACK_RECEIVED, t0)
  fw.sw(t0, s2, 20 * 4)
  fw.li(t0, issue_mode)
  fw.sw(t0, s2, 28 * 4)
  fw.li(t0, mixed_sentinel(spec.index))
  fw.sw(t0, s2, 29 * 4)
  fw.sw(s0, s2, 30 * 4)
  fw.sw(s1, s2, 31 * 4)
  emit_status_done(fw)
  return fw.ret()


def build_target_receiver(spec: TargetSpec, *, noc: int, count: int, op: int, iters: int, max_polls: int) -> KernelBase:
  fw = AtomicKernel()
  emit_record_header(
    fw,
    role=ROLE_TARGET,
    noc=noc,
    sender_index=0xFFFFFFFF,
    count=count,
    target_count=1,
    iters=iters,
    op=op,
    source=spec.core,
    first_target=spec.core,
  )
  emit_start_gate(fw)
  harness.read_wall_clock(fw, a2, a3)

  fw.li(s0, max_polls)
  fw.li(s1, spec.expected_value)
  fw.li(s2, COUNTER_BASE)
  fw.mv(s10, zero)
  value_poll = fw._new_label("target_value_poll")
  value_done = fw._new_label("target_value_done")
  value_retry = fw._new_label("target_value_retry")
  fw.label(value_poll)
  fw.beq(s0, zero, value_done)
  fw.lw(t1, s2, 0)
  fw.bltu(t1, s1, value_retry)
  fw.j(value_done)
  fw.label(value_retry)
  fw.addi(s10, s10, 1)
  fw.addi(s0, s0, -1)
  fw.j(value_poll)
  fw.label(value_done)
  harness.read_wall_clock(fw, a4, a5)
  fw.li(s2, RESULT_BASE)
  fw.sw(t1, s2, 21 * 4)
  fw.sw(a4, s2, 22 * 4)
  fw.sw(a5, s2, 23 * 4)

  if spec.write_senders:
    fw.li(s0, max_polls)
    fw.mv(s6, zero)
    write_poll = fw._new_label("target_write_poll")
    write_done = fw._new_label("target_write_done")
    write_timeout = fw._new_label("target_write_timeout")
    found_labels = [fw._new_label(f"target_write_found_{idx}") for idx, _ in enumerate(spec.write_senders)]
    fw.label(write_poll)
    fw.beq(s0, zero, write_timeout)
    fw.mv(s6, zero)
    for i, sender_index in enumerate(spec.write_senders):
      fw.li(s2, MIXED_WRITE_BASE + sender_index * MIXED_WRITE_STRIDE)
      fw.lw(t1, s2, 0)
      fw.li(t0, mixed_sentinel(sender_index))
      fw.beq(t1, t0, found_labels[i])
      fw.addi(s6, s6, 1)
      fw.label(found_labels[i])
    fw.beq(s6, zero, write_done)
    fw.addi(s10, s10, 1)
    fw.addi(s0, s0, -1)
    fw.j(write_poll)
    fw.label(write_timeout)
    fw.label(write_done)
    harness.read_wall_clock(fw, a4, a5)
  else:
    fw.mv(s6, zero)

  fw.li(s2, RESULT_BASE)
  fw.sw(a2, s2, 13 * 4)
  fw.sw(a3, s2, 14 * 4)
  fw.sw(a4, s2, 15 * 4)
  fw.sw(a5, s2, 16 * 4)
  fw.sw(a4, s2, 24 * 4)
  fw.sw(a5, s2, 25 * 4)
  fw.sw(s10, s2, 26 * 4)
  fw.sw(s6, s2, 27 * 4)
  emit_status_done(fw)
  return fw.ret()


def _one_core_segments(core: Core, kernel: KernelBase, *, dispatch_mode: int, host_assigned_id: int):
  empty = KernelBase()
  return Program(
    brisc=kernel,
    ncrisc=empty,
    trisc0=empty,
    trisc1=empty,
    trisc2=empty,
    num_cores=1,
  ).layout(core_xy=core, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id)


class AtomicProgram:
  def __init__(self, plan: CasePlan, *, iters: int, max_polls: int):
    self.plan = plan
    self.iters = iters
    self.max_polls = max_polls
    self.name = f"riscv_noc_atomic_visibility:noc{plan.noc}:{plan.name}:k{plan.count}"

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    per_core_segments = {}
    active_cores = []
    for spec in self.plan.senders:
      kernel = build_sender(
        spec,
        noc=self.plan.noc,
        count=self.plan.count,
        op=self.plan.op,
        issue_mode=self.plan.issue_mode,
        iters=self.iters,
      )
      per_core_segments[spec.source] = _one_core_segments(
        spec.source,
        kernel,
        dispatch_mode=dispatch_mode,
        host_assigned_id=host_assigned_id,
      )
      active_cores.append(spec.source)
    for spec in self.plan.targets:
      kernel = build_target_receiver(
        spec,
        noc=self.plan.noc,
        count=self.plan.count,
        op=self.plan.op,
        iters=self.iters,
        max_polls=self.max_polls,
      )
      per_core_segments[spec.core] = _one_core_segments(
        spec.core,
        kernel,
        dispatch_mode=dispatch_mode,
        host_assigned_id=host_assigned_id,
      )
      active_cores.append(spec.core)

    reset_blob = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_RESET_READ_PTR_FROM_HOST)
    commands = [
      UnicastWrite(active_cores, TensixL1.GO_MSG, [reset_blob] * len(active_cores)),
      UnicastWrite(active_cores, TensixL1.GO_MSG_INDEX, [b"\0\0\0\0"] * len(active_cores)),
    ]
    for core in active_cores:
      for segment in per_core_segments[core]:
        commands.append(UnicastWrite([core], segment.addr, [segment.data]))
    commands.append(Run(active_cores))
    return commands


def rows_by_y(cores: list[Core]) -> dict[int, list[int]]:
  rows: dict[int, list[int]] = {}
  for x, y in cores:
    rows.setdefault(y, []).append(x)
  return {y: sorted(xs) for y, xs in rows.items()}


def cols_by_x(cores: list[Core]) -> dict[int, list[int]]:
  cols: dict[int, list[int]] = {}
  for x, y in cores:
    cols.setdefault(x, []).append(y)
  return {x: sorted(ys) for x, ys in cols.items()}


def choose_row(cores: list[Core], row: int | None, needed: int) -> tuple[int, list[int]]:
  rows = rows_by_y(cores)
  if row is not None:
    xs = rows.get(row)
    if xs is None or len(xs) < needed:
      raise ValueError(f"row {row} needs at least {needed} usable cores")
    return row, xs
  candidates = [(len(xs), -y, y, xs) for y, xs in rows.items()]
  _, _, y, xs = max(candidates)
  if len(xs) < needed:
    raise ValueError(f"need a row with at least {needed} usable cores")
  return y, xs


def choose_col(cores: list[Core], col: int | None, needed: int) -> tuple[int, list[int]]:
  cols = cols_by_x(cores)
  if col is not None:
    ys = cols.get(col)
    if ys is None or len(ys) < needed:
      raise ValueError(f"column {col} needs at least {needed} usable cores")
    return col, ys
  candidates = [(len(ys), -x, x, ys) for x, ys in cols.items()]
  _, _, x, ys = max(candidates)
  if len(ys) < needed:
    raise ValueError(f"need a column with at least {needed} usable cores")
  return x, ys


def choose_diag(cores: list[Core], needed: int, noc: int) -> list[Core]:
  xs = sorted({x for x, _ in cores})
  ys = sorted({y for _, y in cores})
  if len(xs) < needed or len(ys) < needed:
    raise ValueError(f"need at least {needed} rows and columns for diagonal placement")
  if noc == 0:
    coords = tuple(zip(xs[-needed:], ys[-needed:]))
  else:
    coords = tuple(zip(xs[:needed], ys[:needed]))
  missing = [core for core in coords if core not in set(cores)]
  if missing:
    raise ValueError(f"diagonal placement hit unavailable cores: {missing}")
  return list(coords)


def _target_specs(senders: tuple[SenderSpec, ...], *, iters: int, mixed: bool) -> tuple[TargetSpec, ...]:
  incoming: dict[Core, list[int]] = {}
  for sender in senders:
    for target in sender.targets:
      incoming.setdefault(target, []).append(sender.index)
  return tuple(
    TargetSpec(
      core=target,
      expected_value=iters * len(sender_indices),
      write_senders=tuple(sender_indices if mixed else ()),
    )
    for target, sender_indices in sorted(incoming.items())
  )


def build_same_target(
  cores: list[Core], *,
  noc: int,
  count: int,
  pattern: str,
  op: int,
  issue_mode: int,
  row: int | None,
  col: int | None,
  iters: int,
) -> CasePlan:
  needed = count + 1
  if pattern == "row":
    y, xs = choose_row(cores, row, needed)
    if noc == 0:
      target = (xs[-1], y)
      sources = [(x, y) for x in xs[-1 - count:-1]]
    else:
      target = (xs[0], y)
      sources = [(x, y) for x in xs[1:1 + count]]
  elif pattern == "col":
    x, ys = choose_col(cores, col, needed)
    if noc == 0:
      target = (x, ys[-1])
      sources = [(x, y) for y in ys[-1 - count:-1]]
    else:
      target = (x, ys[0])
      sources = [(x, y) for y in ys[1:1 + count]]
  elif pattern == "diag":
    coords = choose_diag(cores, needed, noc)
    if noc == 0:
      target = coords[-1]
      sources = coords[:-1]
    else:
      target = coords[0]
      sources = coords[1:]
  else:
    raise ValueError(pattern)
  senders = tuple(SenderSpec(i, source, (target,)) for i, source in enumerate(sources))
  mode_suffix = "" if issue_mode == ISSUE_PIPELINED else "-blocking"
  return CasePlan(
    f"same-{pattern}-{op_name(op)}{mode_suffix}",
    f"same-{pattern}",
    op,
    issue_mode,
    noc,
    count,
    senders,
    _target_specs(senders, iters=iters, mixed=op == OP_MIXED),
  )


def build_separate_targets(cores: list[Core], *, noc: int, count: int, pattern: str, op: int, issue_mode: int, row: int | None, col: int | None, iters: int) -> CasePlan:
  needed = count * 2
  if pattern == "row":
    y, xs = choose_row(cores, row, needed)
    if noc == 0:
      sources = [(x, y) for x in xs[:count]]
      targets = [(x, y) for x in xs[count:count * 2]]
    else:
      targets = [(x, y) for x in xs[:count]]
      sources = [(x, y) for x in xs[count:count * 2]]
  elif pattern == "col":
    x, ys = choose_col(cores, col, needed)
    if noc == 0:
      sources = [(x, y) for y in ys[:count]]
      targets = [(x, y) for y in ys[count:count * 2]]
    else:
      targets = [(x, y) for y in ys[:count]]
      sources = [(x, y) for y in ys[count:count * 2]]
  elif pattern == "diag":
    coords = choose_diag(cores, needed, noc)
    if noc == 0:
      sources = coords[:count]
      targets = coords[count:count * 2]
    else:
      targets = coords[:count]
      sources = coords[count:count * 2]
  else:
    raise ValueError(pattern)
  senders = tuple(SenderSpec(i, source, (target,)) for i, (source, target) in enumerate(zip(sources, targets)))
  mode_suffix = "" if issue_mode == ISSUE_PIPELINED else "-blocking"
  return CasePlan(
    f"separate-{pattern}-{op_name(op)}{mode_suffix}",
    f"separate-{pattern}",
    op,
    issue_mode,
    noc,
    count,
    senders,
    _target_specs(senders, iters=iters, mixed=op == OP_MIXED),
  )


def build_one_to_many(cores: list[Core], *, noc: int, count: int, pattern: str, op: int, issue_mode: int, row: int | None, col: int | None, iters: int) -> CasePlan:
  needed = count + 1
  if pattern == "row":
    y, xs = choose_row(cores, row, needed)
    if noc == 0:
      source = (xs[0], y)
      targets = tuple((x, y) for x in xs[1:1 + count])
    else:
      source = (xs[-1], y)
      targets = tuple((x, y) for x in reversed(xs[-1 - count:-1]))
  elif pattern == "col":
    x, ys = choose_col(cores, col, needed)
    if noc == 0:
      source = (x, ys[0])
      targets = tuple((x, y) for y in ys[1:1 + count])
    else:
      source = (x, ys[-1])
      targets = tuple((x, y) for y in reversed(ys[-1 - count:-1]))
  elif pattern == "diag":
    coords = choose_diag(cores, needed, noc)
    if noc == 0:
      source = coords[0]
      targets = tuple(coords[1:])
    else:
      source = coords[-1]
      targets = tuple(reversed(coords[:-1]))
  else:
    raise ValueError(pattern)
  senders = (SenderSpec(0, source, targets),)
  mode_suffix = "" if issue_mode == ISSUE_PIPELINED else "-blocking"
  return CasePlan(
    f"one-many-{pattern}-{op_name(op)}{mode_suffix}",
    f"one-many-{pattern}",
    op,
    issue_mode,
    noc,
    count,
    senders,
    _target_specs(senders, iters=iters, mixed=op == OP_MIXED),
  )


def build_hop_sweep(
  cores: list[Core], *,
  noc: int,
  count: int,
  pattern: str,
  op: int,
  issue_mode: int,
  row: int | None,
  col: int | None,
  iters: int,
) -> tuple[CasePlan, ...]:
  plans: list[CasePlan] = []
  if pattern == "row":
    y, xs = choose_row(cores, row, count + 1)
    if noc == 0:
      source = (xs[0], y)
      targets = [(x, y) for x in xs[1:1 + count]]
    else:
      source = (xs[-1], y)
      targets = [(x, y) for x in reversed(xs[-1 - count:-1])]
  elif pattern == "col":
    x, ys = choose_col(cores, col, count + 1)
    if noc == 0:
      source = (x, ys[0])
      targets = [(x, y) for y in ys[1:1 + count]]
    else:
      source = (x, ys[-1])
      targets = [(x, y) for y in reversed(ys[-1 - count:-1])]
  else:
    raise ValueError(f"hop sweep supports row/col, got {pattern}")
  for target in targets:
    hop = noc_topology.noc_hops(source, target, noc)
    senders = (SenderSpec(0, source, (target,)),)
    plans.append(CasePlan(
      f"hop-{pattern}-h{hop}-{op_name(op)}-{issue_mode_name(issue_mode)}",
      f"hop-{pattern}",
      op,
      issue_mode,
      noc,
      1,
      senders,
      _target_specs(senders, iters=iters, mixed=False),
    ))
  return tuple(plans)


def parse_counts(text: str) -> tuple[int, ...]:
  counts = tuple(int(item.strip()) for item in text.split(",") if item.strip())
  if not counts or any(count <= 0 for count in counts):
    raise argparse.ArgumentTypeError("expected comma-separated positive counts")
  return counts


def parse_nocs(text: str) -> tuple[int, ...]:
  nocs = tuple(int(item.strip()) for item in text.split(",") if item.strip())
  if not nocs or any(noc not in (0, 1) for noc in nocs):
    raise argparse.ArgumentTypeError("expected comma-separated NoC ids from {0,1}")
  return nocs


def parse_cases(text: str) -> tuple[str, ...]:
  cases = tuple(item.strip() for item in text.split(",") if item.strip())
  if not cases:
    raise argparse.ArgumentTypeError("expected comma-separated case names")
  return cases


REPRESENTATIVE_CASES = (
  "same-row-atomic",
  "same-row-sem",
  "same-col-atomic",
  "same-diag-atomic",
  "separate-row-atomic",
  "one-many-row-atomic",
  "mixed-row",
)
CALIBRATION_CASES = (
  "hop-row-atomic-blocking",
  "hop-col-atomic-blocking",
  "same-row-atomic",
  "same-row-sem",
  "same-row-sem-noret",
)
FULL_CASES = (
  "same-row-atomic",
  "same-col-atomic",
  "same-diag-atomic",
  "same-row-sem",
  "same-col-sem",
  "same-diag-sem",
  "same-row-sem-noret",
  "separate-row-atomic",
  "separate-col-atomic",
  "separate-diag-atomic",
  "one-many-row-atomic",
  "one-many-col-atomic",
  "one-many-diag-atomic",
  "mixed-row",
  "mixed-col",
  "mixed-diag",
)


def expand_case_name(name: str) -> tuple[str, str, int, int]:
  issue_mode = ISSUE_PIPELINED
  base = name
  if name.endswith("-blocking"):
    issue_mode = ISSUE_BLOCKING
    base = name.removesuffix("-blocking")
  elif name.endswith("-pipelined"):
    issue_mode = ISSUE_PIPELINED
    base = name.removesuffix("-pipelined")
  if base.startswith("hop-"):
    _, pattern, op_text = base.split("-", 2)
    op = OP_SEM_NORET if op_text == "sem-noret" else (OP_SEM if op_text == "sem" else OP_ATOMIC)
    return "hop", pattern, op, issue_mode
  if base.startswith("same-"):
    _, pattern, op_text = base.split("-", 2)
    op = OP_SEM_NORET if op_text == "sem-noret" else (OP_SEM if op_text == "sem" else OP_ATOMIC)
    return "same", pattern, op, issue_mode
  if base.startswith("separate-"):
    _, pattern, _op_text = base.split("-", 2)
    return "separate", pattern, OP_ATOMIC, issue_mode
  if base.startswith("one-many-"):
    _, _, pattern, _op_text = base.split("-", 3)
    return "one-many", pattern, OP_ATOMIC, issue_mode
  if base.startswith("mixed-"):
    _, pattern = base.split("-", 1)
    return "same", pattern, OP_MIXED, issue_mode
  raise argparse.ArgumentTypeError(f"unknown case {name!r}")


def build_plans(name: str, cores: list[Core], *, noc: int, count: int, row: int | None, col: int | None, iters: int) -> tuple[CasePlan, ...]:
  kind, pattern, op, issue_mode = expand_case_name(name)
  if kind == "hop":
    return build_hop_sweep(
      cores,
      noc=noc,
      count=count,
      pattern=pattern,
      op=op,
      issue_mode=issue_mode,
      row=row,
      col=col,
      iters=iters,
    )
  if kind == "same":
    return (build_same_target(cores, noc=noc, count=count, pattern=pattern, op=op, issue_mode=issue_mode, row=row, col=col, iters=iters),)
  if kind == "separate":
    return (build_separate_targets(cores, noc=noc, count=count, pattern=pattern, op=op, issue_mode=issue_mode, row=row, col=col, iters=iters),)
  if kind == "one-many":
    return (build_one_to_many(cores, noc=noc, count=count, pattern=pattern, op=op, issue_mode=issue_mode, row=row, col=col, iters=iters),)
  raise ValueError(kind)


def seed_payload(sender_index: int) -> bytes:
  payload = bytearray(MIXED_WRITE_BYTES)
  for off in range(0, len(payload), 4):
    struct.pack_into("<I", payload, off, mixed_sentinel(sender_index))
  return bytes(payload)


def read_wall_clock_host(device: Device, core: Core) -> int:
  base, off_h = align_down(TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_H, TLBWindow.SIZE_2M)
  off_l = TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L - base
  with harness.device_window(device, core, addr=base) as win:
    while True:
      hi0 = struct.unpack("<I", win.read(off_h, 4))[0]
      lo = struct.unpack("<I", win.read(off_l, 4))[0]
      hi1 = struct.unpack("<I", win.read(off_h, 4))[0]
      if hi0 == hi1:
        return lo | (hi0 << 32)


def clear_seed_and_gate(device: Device, plan: CasePlan, *, gate_value: int):
  cores = {spec.source for spec in plan.senders} | {spec.core for spec in plan.targets}
  with harness.device_window(device, next(iter(cores))) as win:
    for core in sorted(cores):
      win.target(core)
      win.write(RESULT_BASE, b"\0" * result_size())
      win.write(START_GATE_BASE, struct.pack("<Q", gate_value))
    for spec in plan.senders:
      win.target(spec.source)
      win.write(STREAM_BASE, seed_payload(spec.index))
    for spec in plan.targets:
      win.target(spec.core)
      win.write(COUNTER_BASE, b"\0\0\0\0")
      if spec.write_senders:
        last_slot = max(spec.write_senders) * MIXED_WRITE_STRIDE + MIXED_WRITE_BYTES
        win.write(MIXED_WRITE_BASE, b"\0" * last_slot)


def read_result(device: Device, core: Core) -> CoreResult:
  with harness.device_window(device, core) as win:
    win.target(core)
    blob = win.read(RESULT_BASE, result_size())
    words = struct.unpack_from("<" + "I" * RECORD_WORDS, blob, 0)
  if words[0] != RESULT_MAGIC:
    raise RuntimeError(f"{core}: bad result magic 0x{words[0]:08x}")
  if words[2] != STATUS_DONE:
    raise RuntimeError(f"{core}: benchmark did not finish, status=0x{words[2]:08x}")
  return CoreResult(core, words)


def run_once(device: Device, plan: CasePlan, *, iters: int, gate_cycles: int, max_polls: int) -> BenchRun:
  active = [spec.source for spec in plan.senders] + [spec.core for spec in plan.targets]
  now = max(read_wall_clock_host(device, core) for core in active)
  gate_value = now + gate_cycles
  clear_seed_and_gate(device, plan, gate_value=gate_value)
  device.run(AtomicProgram(plan, iters=iters, max_polls=max_polls))
  sender_results = tuple(read_result(device, spec.source) for spec in plan.senders)
  target_results = tuple(read_result(device, spec.core) for spec in plan.targets)
  return BenchRun(plan, sender_results, target_results)


def validate_run(run: BenchRun, *, iters: int):
  plan = run.plan
  expected_sender = {
    spec.source: (iters * len(spec.targets)) if op_has_source_response(plan.op) else 0
    for spec in plan.senders
  }
  bad_atomic = [
    (result.core, result.atomic_delta, expected_sender[result.core])
    for result in run.sender_results
    if result.atomic_delta != expected_sender[result.core]
  ]
  expected_writes = expected_sender if plan.op == OP_MIXED else {spec.source: 0 for spec in plan.senders}
  bad_writes = [
    (result.core, result.write_ack_delta, expected_writes[result.core])
    for result in run.sender_results
    if result.write_ack_delta != expected_writes[result.core]
  ]
  expected_targets = {spec.core: spec.expected_value for spec in plan.targets}
  bad_targets = [
    (result.core, result.observed_value, expected_targets[result.core], result.missing_writes)
    for result in run.target_results
    if result.observed_value != expected_targets[result.core] or result.missing_writes
  ]
  if bad_atomic or bad_writes or bad_targets:
    raise RuntimeError(
      f"invalid {plan.name} noc{plan.noc}: "
      f"bad_atomic={bad_atomic} bad_writes={bad_writes} bad_targets={bad_targets}"
    )


def plan_hops(plan: CasePlan) -> str:
  hops = []
  for sender in plan.senders:
    for target in sender.targets:
      hops.append(noc_topology.noc_hops(sender.source, target, plan.noc))
  if not hops:
    return "0"
  if len(set(hops)) == 1:
    return str(hops[0])
  return f"{min(hops)}..{max(hops)}"


def format_core_list(cores: tuple[Core, ...] | list[Core]) -> str:
  return " ".join(f"`{x},{y}`" for x, y in cores)


def format_summary(runs: list[BenchRun], *, iters: int) -> str:
  lines = [
    "| case | mode | noc | K | op | initiators | targets | hops | atomic ops | issue cyc | issue op/cyc | sender cyc | sender op/cyc | target observed cyc | observed op/cyc | observed-minus-sender cyc | sender spreads | bad | target polls |",
    "|---|---|---:|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
  ]
  for run in runs:
    plan = run.plan
    start = min(result.start for result in run.sender_results)
    issue_end = max(result.issue_end for result in run.sender_results)
    sender_end = max(result.end for result in run.sender_results)
    observed_end = max(result.writes_observed if plan.op == OP_MIXED else result.value_observed for result in run.target_results)
    issue_cycles = issue_end - start
    sender_cycles = sender_end - start
    observed_cycles = observed_end - start
    ops = sum(iters * len(spec.targets) for spec in plan.senders)
    rates = [iters * len(spec.targets) / result.cycles if result.cycles > 0 else 0.0 for spec, result in zip(plan.senders, run.sender_results)]
    spread = (max(rates) - min(rates)) / statistics.fmean(rates) if len(rates) > 1 and statistics.fmean(rates) else 0.0
    bad = 0
    for result, spec in zip(run.sender_results, plan.senders):
      expected_atomic = (iters * len(spec.targets)) if op_has_source_response(plan.op) else 0
      bad += int(result.atomic_delta != expected_atomic)
      bad += int(result.write_ack_delta != ((iters * len(spec.targets)) if plan.op == OP_MIXED else 0))
    target_expected = {spec.core: spec.expected_value for spec in plan.targets}
    bad += sum(result.observed_value != target_expected[result.core] or result.missing_writes for result in run.target_results)
    lines.append(
      f"| {plan.name} | {issue_mode_name(plan.issue_mode)} | {plan.noc} | {plan.count} | {op_name(plan.op)} | "
      f"{format_core_list([spec.source for spec in plan.senders])} | "
      f"{format_core_list([spec.core for spec in plan.targets])} | {plan_hops(plan)} | {ops} | "
      f"{issue_cycles} | {ops / issue_cycles if issue_cycles > 0 else 0.0:.5f} | "
      f"{sender_cycles} | {ops / sender_cycles if sender_cycles > 0 else 0.0:.5f} | "
      f"{observed_cycles} | {ops / observed_cycles if observed_cycles > 0 else 0.0:.5f} | "
      f"{observed_end - sender_end} | {spread:.3f} | {bad} | "
      f"{max(result.poll_iters for result in run.target_results)} |"
    )
  return "\n".join(lines)


def append_report(path: Path, *, gate_cycles: int, iters: int, runs: list[BenchRun], suite: str):
  target_cycles = []
  for run in runs:
    same_target = run.plan.pattern.startswith("same-") and run.plan.op in (OP_ATOMIC, OP_SEM)
    if same_target:
      start = min(result.start for result in run.sender_results)
      observed = max(result.value_observed for result in run.target_results)
      ops = sum(iters * len(spec.targets) for spec in run.plan.senders)
      if observed > start and ops:
        target_cycles.append((observed - start) / ops)
  target_note = "n/a"
  if target_cycles:
    target_note = f"{statistics.fmean(target_cycles):.1f} cycles/op observed-window mean across same-target rows"
  harness.append_report(path, None, [
    f"Suite: `{suite}`",
    f"Iterations per sender-target edge: `{iters}`",
    f"Start gate lead: `{gate_cycles}` cycles",
    "Traffic: BRISC NoC atomic/semaphore increments, optional nonposted unicast writes to the same target L1",
    "Completion columns compare sender atomic-response/write-ack completion with target BRISC polling of the final L1 value",
    f"Scheduler calibration hint: `{target_note}`; use same-target atomic rows to refine `atomic_target_cycles` only after subtracting hop/response overhead",
  ], format_summary(runs, iters=iters))


def selected_cases(args) -> tuple[str, ...]:
  if args.cases:
    return args.cases
  if args.suite == "calibration":
    return CALIBRATION_CASES
  if args.suite == "full":
    return FULL_CASES
  return REPRESENTATIVE_CASES


def dry_run(args):
  cores = sorted(set(P100_PROGRAM_CORES) - P100_FAST_DISPATCH_RESERVED)
  for noc in args.nocs:
    for count in args.counts:
      for case_name in selected_cases(args):
        for plan in build_plans(case_name, cores, noc=noc, count=count, row=args.row, col=args.col, iters=args.iters):
          AtomicProgram(plan, iters=args.iters, max_polls=args.max_polls).lower(
            dispatch_mode=DevMsgs.DISPATCH_MODE_HOST,
            host_assigned_id=0,
          )
          print(
            f"dry-run {plan.name} noc{noc} K={count} op={op_name(plan.op)} mode={issue_mode_name(plan.issue_mode)} "
            f"senders={[spec.source for spec in plan.senders]} targets={[spec.core for spec in plan.targets]} "
            f"hops={plan_hops(plan)}"
          )


def main():
  parser = argparse.ArgumentParser(description="Blackhole NoC atomic/semaphore arbitration and target-visibility microbench.")
  parser.add_argument("--nocs", type=parse_nocs, default=(0, 1), help="comma-separated NoC ids, default: 0,1")
  parser.add_argument("--counts", type=parse_counts, default=parse_counts("2,4"), help="comma-separated initiator/target fanout counts")
  parser.add_argument("--suite", choices=("representative", "full", "calibration"), default="representative")
  parser.add_argument("--cases", type=parse_cases, default=None, help="override suite with comma-separated case names")
  parser.add_argument("--iters", type=int, default=128, help="atomic increments per sender-target edge")
  parser.add_argument("--row", type=int, default=None, help="physical row override for row cases")
  parser.add_argument("--col", type=int, default=None, help="physical column override for column cases")
  parser.add_argument("--gate-cycles", type=int, default=100_000_000, help="future WALL_CLOCK start-gate lead")
  parser.add_argument("--max-polls", type=int, default=100_000_000)
  parser.add_argument("--dry-run", action="store_true", help="lower programs and validate placement without opening the device")
  parser.add_argument("--allow-invalid", action="store_true", help="print/report rows even if counters or target observations fail")
  parser.add_argument("--no-report", action="store_true", help="do not append docs/noc-atomic-visibility.md")
  parser.add_argument("--report", type=Path, default=harness.doc_path("noc", "noc-atomic-visibility.md"), help="markdown report path")
  args = parser.parse_args()

  if args.iters <= 0:
    raise ValueError("--iters must be positive")
  if args.gate_cycles <= 0:
    raise ValueError("--gate-cycles must be positive")
  if args.max_polls <= 0:
    raise ValueError("--max-polls must be positive")
  if max(args.counts) > 8:
    raise ValueError("this bench supports fanout/count up to 8")

  if args.dry_run:
    dry_run(args)
    return

  runs: list[BenchRun] = []
  with harness.open_device() as device:
    reserved = {
      getattr(device.board_info, "dispatch_core", None),
      getattr(device.board_info, "prefetch_core", None),
    }
    core_set = set(device.cores) - {core for core in reserved if core is not None}
    usable_cores = sorted(core_set)
    for noc in args.nocs:
      for count in args.counts:
        for case_name in selected_cases(args):
          for plan in build_plans(case_name, usable_cores, noc=noc, count=count, row=args.row, col=args.col, iters=args.iters):
            needed_cores = {spec.source for spec in plan.senders} | {spec.core for spec in plan.targets}
            if not needed_cores <= core_set:
              raise ValueError(f"{plan.name} selected unavailable cores: {sorted(needed_cores - core_set)}")
            run = run_once(device, plan, iters=args.iters, gate_cycles=args.gate_cycles, max_polls=args.max_polls)
            runs.append(run)
            if not args.allow_invalid:
              try:
                validate_run(run, iters=args.iters)
              except RuntimeError:
                print(format_summary(runs[-1:], iters=args.iters))
                raise

  print(format_summary(runs, iters=args.iters))
  if not args.no_report:
    append_report(args.report, gate_cycles=args.gate_cycles, iters=args.iters, runs=runs, suite=args.suite)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
