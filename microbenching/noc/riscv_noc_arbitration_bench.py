#!/usr/bin/env python3
from __future__ import annotations

import argparse
import statistics
import struct
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402  (does sys.path + TT_USB bootstrap on import)
try:
  import noc_topology
except ModuleNotFoundError:
  from microbenching import noc_topology
from asm import KernelBase
from device import Device
from dsl import a2, a3, a4, a5, a6, a7, s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, t0, t3, t4, zero
from pcie import TLBWindow
from program import DevMsgs, Program, Run, UnicastWrite
from ttk.addrs import Core, align_down, noc_xy
from ttk.mailbox import BriscMailbox as BM
from ttk.noc import NOC, Noc
from ttk.tensix import TensixL1, TensixMMIO


RESULT_BASE = 0x150000
READBACK_BASE = RESULT_BASE + 0x800
START_GATE_BASE = RESULT_BASE + 0x1000
STREAM_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
DEST_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
DEST_STRIDE = 0x8000
MAX_SENDERS = 16
BASE_RECORD_WORDS = 24
VISIBILITY_BASE_WORD = BASE_RECORD_WORDS
RECORD_WORDS = VISIBILITY_BASE_WORD + 2 * MAX_SENDERS
RECORD_SIZE = RECORD_WORDS * 4
RESULT_MAGIC = 0x524E4141  # "RNAA"
STATUS_STARTED = 0xA1000001
STATUS_DONE = 0xA100D00D
P100_PROGRAM_CORES = [(x, y) for y in noc_topology.P100_WORKER_Y for x in noc_topology.P100_WORKER_X]
P100_FAST_DISPATCH_RESERVED = {(14, 2), (14, 3)}


@dataclass(frozen=True)
class SenderSpec:
  index: int
  source: Core
  target: Core
  dest_base: int
  skew_cycles: int = 0

  @property
  def stream(self) -> noc_topology.Stream:
    return (self.source, self.target)


@dataclass(frozen=True)
class SenderResult:
  core: Core
  words: tuple[int, ...]

  @property
  def sender_index(self) -> int:
    return self.words[4]

  @property
  def packet_bytes(self) -> int:
    return self.words[6]

  @property
  def packets(self) -> int:
    return self.words[7]

  @property
  def target(self) -> Core:
    return self.words[8], self.words[9]

  @property
  def dest_base(self) -> int:
    return self.words[10]

  @property
  def start(self) -> int:
    return self.words[12] | (self.words[13] << 32)

  @property
  def end(self) -> int:
    return self.words[14] | (self.words[15] << 32)

  @property
  def cycles(self) -> int:
    return (self.end - self.start) & ((1 << 64) - 1)

  @property
  def ack_delta(self) -> int:
    return (self.words[17] - self.words[16]) & 0xFFFFFFFF

  @property
  def nonposted_req_delta(self) -> int:
    return (self.words[19] - self.words[18]) & 0xFFFFFFFF

  @property
  def rd_resp_delta(self) -> int:
    return (self.words[21] - self.words[20]) & 0xFFFFFFFF

  @property
  def sentinel(self) -> int:
    return self.words[22]

  @property
  def skew_cycles(self) -> int:
    return self.words[11]

  @property
  def bytes_total(self) -> int:
    return self.packet_bytes * self.packets

  @property
  def bytes_per_cycle(self) -> float:
    return self.bytes_total / self.cycles if self.cycles > 0 else 0.0


@dataclass(frozen=True)
class TargetResult:
  core: Core
  words: tuple[int, ...]

  @property
  def missing(self) -> int:
    return self.words[11]

  @property
  def poll_iters(self) -> int:
    return self.words[16]

  @property
  def start(self) -> int:
    return self.words[12] | (self.words[13] << 32)

  @property
  def visibility_cycles(self) -> tuple[int, ...]:
    cycles = []
    for i in range(MAX_SENDERS):
      lo = self.words[VISIBILITY_BASE_WORD + 2 * i]
      hi = self.words[VISIBILITY_BASE_WORD + 2 * i + 1]
      cycles.append(lo | (hi << 32))
    return tuple(cycles)


@dataclass(frozen=True)
class ArbitrationRun:
  layout: str
  noc: int
  k: int
  packet_bytes: int
  packets: int
  target: Core
  senders: list[SenderSpec]
  results: list[SenderResult]
  target_result: TargetResult


@dataclass(frozen=True)
class LayoutSpec:
  label: str
  target: Core
  senders: list[SenderSpec]


class ArbitrationKernel(KernelBase, Noc):
  pass


def expected_sentinel(packet_bytes: int) -> int:
  return 0xA5000000 | (packet_bytes - 4)


def result_size() -> int:
  return RECORD_SIZE


def emit_counter_read(fw: KernelBase, noc: int, counter: int, out, *, addr=t3):
  fw.li(addr, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  return fw.lw(out, addr, 0)


def emit_record_header(
  fw: KernelBase, *,
  status: int,
  noc: int,
  sender_index: int,
  k: int,
  packet_bytes: int,
  packets: int,
  target: Core,
  dest_base: int,
  aux_word: int = 0,
):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, 1, status, noc, sender_index, k, packet_bytes, packets,
    target[0], target[1], dest_base, aux_word,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off in range(12, RECORD_WORDS):
    fw.sw(zero, s2, off * 4)
  return fw


def emit_start_gate(fw: ArbitrationKernel):
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


def emit_start_skew(fw: ArbitrationKernel, skew_cycles: int):
  if skew_cycles <= 0:
    return fw
  wait = fw._new_label("start_skew_wait")
  done = fw._new_label("start_skew_done")
  fw.li(t0, skew_cycles & 0xFFFFFFFF)
  fw.add(t4, s10, t0)
  fw.sltu(t3, t4, s10)
  fw.mv(s10, t4)
  fw.li(t0, (skew_cycles >> 32) & 0xFFFFFFFF)
  fw.add(s11, s11, t0)
  fw.add(s11, s11, t3)
  fw.label(wait)
  harness.read_wall_clock(fw, a2, a3)
  fw.bltu(a3, s11, wait)
  fw.bne(a3, s11, done)
  fw.bltu(a2, s10, wait)
  fw.label(done)
  return fw


def build_sender(spec: SenderSpec, *, noc: int, k: int, packet_bytes: int, packets: int) -> KernelBase:
  fw = ArbitrationKernel()
  emit_record_header(
    fw,
    status=STATUS_STARTED,
    noc=noc,
    sender_index=spec.index,
    k=k,
    packet_bytes=packet_bytes,
    packets=packets,
    target=spec.target,
    dest_base=spec.dest_base,
    aux_word=spec.skew_cycles & 0xFFFFFFFF,
  )
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s9,))
  fw.local_noc_coord(noc, s5, x_addr=BM.MY_X, y_addr=BM.MY_Y)

  emit_start_gate(fw)
  emit_start_skew(fw, spec.skew_cycles)
  fw.li(s2, STREAM_BASE)
  fw.li(s3, spec.dest_base)
  fw.li(s4, packet_bytes)
  emit_counter_read(fw, noc, NOC.NIU_MST_WR_ACK_RECEIVED, s7)
  emit_counter_read(fw, noc, NOC.NIU_MST_NONPOSTED_WR_REQ_SENT, s8)
  emit_counter_read(fw, noc, NOC.NIU_MST_RD_RESP_RECEIVED, s11)
  fw.mv(s6, s7)
  harness.read_wall_clock(fw, a2, a3)

  fw.li(s0, packets)
  loop = fw._new_label("arb_write_loop")
  done = fw._new_label("arb_write_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  fw.noc_write(noc, 0, s2, s3, 0, s9, s4, posted=False, a=t3, v=t4)
  fw.addi(s6, s6, 1)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  fw.noc_write_barrier(noc, s6, addr=t3, val=t4)
  harness.read_wall_clock(fw, a4, a5)

  fw.li(s2, RESULT_BASE)
  for off, reg in enumerate((a2, a3, a4, a5, s7), start=12):
    fw.sw(reg, s2, off * 4)
  emit_counter_read(fw, noc, NOC.NIU_MST_WR_ACK_RECEIVED, t0)
  fw.sw(t0, s2, 17 * 4)
  fw.sw(s8, s2, 18 * 4)
  emit_counter_read(fw, noc, NOC.NIU_MST_NONPOSTED_WR_REQ_SENT, t0)
  fw.sw(t0, s2, 19 * 4)
  fw.sw(s11, s2, 20 * 4)
  emit_counter_read(fw, noc, NOC.NIU_MST_RD_RESP_RECEIVED, t0)
  fw.sw(t0, s2, 21 * 4)

  fw.li(s2, RESULT_BASE)
  fw.sw(zero, s2, 22 * 4)

  fw.li(t0, STATUS_DONE)
  fw.sw(t0, s2, 2 * 4)
  return fw.ret()


def build_target_receiver(*, k: int, packet_bytes: int, max_polls: int) -> KernelBase:
  if k > MAX_SENDERS:
    raise ValueError(f"receiver visibility record supports at most {MAX_SENDERS} senders")
  fw = ArbitrationKernel()
  emit_record_header(
    fw,
    status=STATUS_STARTED,
    noc=2,
    sender_index=0,
    k=k,
    packet_bytes=packet_bytes,
    packets=0,
    target=(0, 0),
    dest_base=DEST_BASE,
  )
  emit_start_gate(fw)
  fw.li(s0, max_polls)
  fw.mv(s10, zero)
  fw.mv(s7, zero)
  harness.read_wall_clock(fw, a2, a3)
  poll = fw._new_label("arb_recv_poll")
  found = [fw._new_label(f"arb_recv_found_{i}") for i in range(k)]
  done = fw._new_label("arb_recv_done")
  timeout = fw._new_label("arb_recv_timeout")
  expected = expected_sentinel(packet_bytes)
  fw.label(poll)
  fw.beq(s0, zero, timeout)
  fw.mv(s6, zero)
  for i in range(k):
    next_sender = fw._new_label(f"arb_recv_next_{i}")
    fw.li(t4, 1 << i)
    fw.and_(t3, s7, t4)
    fw.bne(t3, zero, next_sender)
    fw.li(s2, DEST_BASE + i * DEST_STRIDE + packet_bytes - 4)
    fw.lw(t0, s2, 0)
    fw.li(t3, expected)
    fw.beq(t0, t3, found[i])
    fw.addi(s6, s6, 1)
    fw.j(next_sender)
    fw.label(found[i])
    harness.read_wall_clock(fw, a6, a7, addr=t4, hi2=t3)
    fw.li(s2, RESULT_BASE)
    fw.sw(a6, s2, (VISIBILITY_BASE_WORD + 2 * i) * 4)
    fw.sw(a7, s2, (VISIBILITY_BASE_WORD + 2 * i + 1) * 4)
    fw.li(t4, 1 << i)
    fw.or_(s7, s7, t4)
    fw.label(next_sender)
  fw.beq(s6, zero, done)
  fw.addi(s10, s10, 1)
  fw.addi(s0, s0, -1)
  fw.j(poll)
  fw.label(timeout)
  fw.label(done)
  harness.read_wall_clock(fw, a4, a5)
  fw.li(s2, RESULT_BASE)
  for off, reg in enumerate((a2, a3, a4, a5), start=12):
    fw.sw(reg, s2, off * 4)
  fw.sw(s10, s2, 16 * 4)
  fw.sw(s6, s2, 11 * 4)
  fw.li(t0, STATUS_DONE)
  fw.sw(t0, s2, 2 * 4)
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


class ArbitrationProgram:
  def __init__(self, senders: list[SenderSpec], *, noc: int, packet_bytes: int, packets: int):
    self.senders = list(senders)
    self.noc = noc
    self.packet_bytes = packet_bytes
    self.packets = packets
    self.name = f"riscv_noc_arbitration:noc{noc}:k{len(senders)}:pkt{packet_bytes}"

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    per_core_segments = {}
    target_cores = []
    target = self.senders[0].target
    for spec in self.senders:
      sender = build_sender(
        spec,
        noc=self.noc,
        k=len(self.senders),
        packet_bytes=self.packet_bytes,
        packets=self.packets,
      )
      sender.rta(lambda _x, _y, target=spec.target: [noc_xy(*target)])
      per_core_segments[spec.source] = _one_core_segments(
        spec.source,
        sender,
        dispatch_mode=dispatch_mode,
        host_assigned_id=host_assigned_id,
      )
      target_cores.append(spec.source)

    per_core_segments[target] = _one_core_segments(
      target,
      build_target_receiver(k=len(self.senders), packet_bytes=self.packet_bytes, max_polls=100_000_000),
      dispatch_mode=dispatch_mode,
      host_assigned_id=host_assigned_id,
    )
    target_cores.append(target)

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


def rows_by_y(cores: list[Core]) -> dict[int, list[int]]:
  rows: dict[int, list[int]] = {}
  for x, y in cores:
    rows.setdefault(y, []).append(x)
  return {y: sorted(xs) for y, xs in rows.items()}


def choose_row(cores: list[Core], requested_row: int | None) -> tuple[int, list[int]]:
  rows = rows_by_y(cores)
  if requested_row is not None:
    xs = rows.get(requested_row)
    if xs is None or len(xs) < 9:
      raise ValueError(f"row {requested_row} needs at least 9 program cores for K=8 plus target")
    return requested_row, xs
  candidates = [(len(xs), -y, y, xs) for y, xs in rows.items()]
  _, _, y, xs = max(candidates)
  if len(xs) < 9:
    raise ValueError("arbitration bench needs a row with at least 9 program cores")
  return y, xs


def _make_senders(target: Core, sources: Sequence[Core], *, skew_step: int = 0) -> list[SenderSpec]:
  if len(sources) > MAX_SENDERS:
    raise ValueError(f"at most {MAX_SENDERS} senders are supported")
  if len(set(sources)) != len(sources):
    raise ValueError(f"duplicate sender cores in {list(sources)}")
  if target in sources:
    raise ValueError(f"target {target} cannot also be a sender")
  return [
    SenderSpec(
      index=i,
      source=source,
      target=target,
      dest_base=DEST_BASE + i * DEST_STRIDE,
      skew_cycles=i * skew_step,
    )
    for i, source in enumerate(sources)
  ]


def build_sender_set(
  cores: list[Core], *,
  noc: int,
  k: int,
  row: int | None,
  skew_step: int = 0,
  near_to_far: bool = False,
) -> tuple[Core, list[SenderSpec]]:
  y, xs = choose_row(cores, row)
  if noc == 0:
    target = (xs[-1], y)
    source_xs = xs[-1 - k:-1]
    if near_to_far:
      source_xs = list(reversed(source_xs))
  else:
    target = (xs[0], y)
    source_xs = xs[1:1 + k]
    if not near_to_far:
      source_xs = list(source_xs)
  if len(source_xs) != k:
    raise ValueError(f"row {y} does not have {k} usable sender cores for NoC{noc}")

  senders = _make_senders(target, [(x, y) for x in source_xs], skew_step=skew_step)
  final_links = {noc_topology.path_links(spec.source, spec.target, noc)[-1] for spec in senders}
  if len(final_links) != 1:
    raise RuntimeError(f"internal placement error: expected one shared final link, got {sorted(final_links)}")
  return target, senders


def _choose_middle_row(cores: list[Core], row: int | None, min_width: int) -> tuple[int, list[int]]:
  rows = rows_by_y(cores)
  if row is not None:
    xs = rows.get(row)
    if xs is None or len(xs) < min_width:
      raise ValueError(f"row {row} needs at least {min_width} program cores")
    return row, xs
  candidates = [(abs(y - 6), -len(xs), y, xs) for y, xs in rows.items() if len(xs) >= min_width]
  if not candidates:
    raise ValueError(f"no row has at least {min_width} program cores")
  _, _, y, xs = min(candidates)
  return y, xs


def _ordered_two_sided_xs(xs: Sequence[int], target_x: int, k: int) -> list[int]:
  left = sorted((x for x in xs if x < target_x), reverse=True)
  right = sorted(x for x in xs if x > target_x)
  ordered: list[int] = []
  for i in range(max(len(left), len(right))):
    if i < len(left):
      ordered.append(left[i])
    if i < len(right):
      ordered.append(right[i])
    if len(ordered) >= k:
      return ordered[:k]
  raise ValueError(f"row does not have {k} two-sided sender cores around target x={target_x}")


def build_holey_layout(cores: list[Core], *, noc: int, k: int, row: int | None) -> LayoutSpec:
  y, xs = choose_row(cores, row)
  if noc == 0:
    target = (xs[-1], y)
    source_xs = xs[:-1][-(2 * k)::2]
  else:
    target = (xs[0], y)
    source_xs = xs[1:1 + 2 * k:2]
  if len(source_xs) != k:
    raise ValueError(f"row {y} does not have {k} holey sender cores for NoC{noc}")
  return LayoutSpec("holes", target, _make_senders(target, [(x, y) for x in source_xs]))


def build_two_sided_layout(cores: list[Core], *, k: int, row: int | None) -> LayoutSpec:
  y, xs = _choose_middle_row(cores, row, min_width=k + 1)
  target_x = xs[len(xs) // 2]
  source_xs = _ordered_two_sided_xs(xs, target_x, k)
  target = (target_x, y)
  return LayoutSpec("two-sided", target, _make_senders(target, [(x, y) for x in source_xs]))


def build_two_sided_asym_layout(
  cores: list[Core], *,
  k: int,
  row: int | None,
  left_count: int,
  right_count: int,
) -> LayoutSpec:
  if left_count <= 0 or right_count <= 0:
    raise ValueError("--asym-left and --asym-right must both be positive")
  if k != left_count + right_count:
    raise ValueError(
      f"two-sided-asym needs --counts {left_count + right_count} for "
      f"{left_count} left + {right_count} right senders, got K={k}"
    )
  y, xs = _choose_middle_row(cores, row, min_width=k + 1)
  candidates = []
  for target_x in xs:
    left = sorted((x for x in xs if x < target_x), reverse=True)
    right = sorted(x for x in xs if x > target_x)
    if len(left) >= left_count and len(right) >= right_count:
      candidates.append((abs(target_x - xs[len(xs) // 2]), target_x, left, right))
  if not candidates:
    raise ValueError(
      f"no row has a target with {left_count} left and {right_count} right sender cores"
    )
  _, target_x, left, right = min(candidates)
  source_xs = left[:left_count] + right[:right_count]
  target = (target_x, y)
  return LayoutSpec(
    f"two-sided-asym-{left_count}l{right_count}r",
    target,
    _make_senders(target, [(x, y) for x in source_xs]),
  )


def _choose_interior_target(cores: list[Core], *, noc: int, row: int | None) -> Core:
  rows = rows_by_y(cores)
  if row is not None:
    y = row
    xs = rows.get(row)
    if not xs:
      raise ValueError(f"row {row} has no program cores")
  else:
    ys = sorted(rows)
    if len(ys) < 3:
      raise ValueError("multi-row layouts need at least three rows")
    y = ys[len(ys) // 2]
    xs = rows[y]
  target_x = xs[len(xs) // 2]
  if noc == 0 and y == min(rows):
    raise ValueError("NoC0 diagonal/multi-row layouts need a target below at least one sender row")
  if noc == 1 and y == max(rows):
    raise ValueError("NoC1 diagonal/multi-row layouts need a target above at least one sender row")
  return target_x, y


def build_diagonal_layout(cores: list[Core], *, noc: int, k: int, row: int | None) -> LayoutSpec:
  target = _choose_interior_target(cores, noc=noc, row=row)
  tx, ty = target
  if noc == 0:
    candidates = [core for core in cores if core[0] < tx and core[1] < ty]
  else:
    candidates = [core for core in cores if core[0] > tx and core[1] > ty]
  candidates = sorted(candidates, key=lambda c: (abs(c[0] - tx) + abs(c[1] - ty), abs(c[1] - ty), abs(c[0] - tx), c))
  if len(candidates) < k:
    raise ValueError(f"not enough diagonal sender cores for NoC{noc}: need {k}, found {len(candidates)}")
  return LayoutSpec("diagonal", target, _make_senders(target, candidates[:k]))


def _axis_predecessors(values: Sequence[int], target: int, noc: int) -> list[int]:
  if noc == 0:
    return sorted((value for value in values if value < target), reverse=True)
  return sorted(value for value in values if value > target)


def build_diagonal_xleg_layout(cores: list[Core], *, noc: int, k: int, row: int | None) -> LayoutSpec:
  target = _choose_interior_target(cores, noc=noc, row=row)
  rows = rows_by_y(cores)
  tx, ty = target
  source_y = ty - 1 if noc == 0 else ty + 1
  source_xs = _axis_predecessors(rows.get(source_y, ()), tx, noc)
  if len(source_xs) < k:
    raise ValueError(
      f"not enough same-row diagonal X-leg sender cores for NoC{noc}: need {k}, found {len(source_xs)}"
    )
  sources = [(x, source_y) for x in source_xs[:k]]
  return LayoutSpec("diagonal-xleg", target, _make_senders(target, sources))


def build_diagonal_yleg_layout(cores: list[Core], *, noc: int, k: int, row: int | None) -> LayoutSpec:
  target = _choose_interior_target(cores, noc=noc, row=row)
  rows = rows_by_y(cores)
  tx, ty = target
  target_row_xs = rows[ty]
  source_xs = _axis_predecessors(target_row_xs, tx, noc)
  if not source_xs:
    raise ValueError(f"no live predecessor X column for target {target} on NoC{noc}")
  source_x = source_xs[0]
  source_ys = _axis_predecessors(sorted(rows), ty, noc)
  sources = [(source_x, y) for y in source_ys if source_x in rows[y]]
  if len(sources) < k:
    raise ValueError(
      f"not enough diagonal Y-leg sender cores for NoC{noc}: need {k}, found {len(sources)}"
    )
  return LayoutSpec("diagonal-yleg", target, _make_senders(target, sources[:k]))


def build_multi_row_layout(cores: list[Core], *, noc: int, k: int, row: int | None) -> LayoutSpec:
  target = _choose_interior_target(cores, noc=noc, row=row)
  tx, ty = target
  if noc == 0:
    candidates = [core for core in cores if core[1] < ty]
  else:
    candidates = [core for core in cores if core[1] > ty]
  candidates = sorted(candidates, key=lambda c: (abs(c[1] - ty), abs(c[0] - tx), c))
  if len(candidates) < k:
    raise ValueError(f"not enough multi-row sender cores for NoC{noc}: need {k}, found {len(candidates)}")
  return LayoutSpec("multi-row", target, _make_senders(target, candidates[:k]))


def build_layouts(
  cores: list[Core], *,
  layouts: Sequence[str],
  noc: int,
  k: int,
  row: int | None,
  skew_step: int,
  asym_left: int,
  asym_right: int,
) -> list[LayoutSpec]:
  out: list[LayoutSpec] = []
  for layout in layouts:
    if layout == "one-sided":
      target, senders = build_sender_set(cores, noc=noc, k=k, row=row)
      out.append(LayoutSpec("one-sided", target, senders))
    elif layout == "rank-line":
      target, senders = build_sender_set(cores, noc=noc, k=k, row=row, near_to_far=True)
      out.append(LayoutSpec("rank-line", target, senders))
    elif layout == "holes":
      out.append(build_holey_layout(cores, noc=noc, k=k, row=row))
    elif layout == "two-sided":
      out.append(build_two_sided_layout(cores, k=k, row=row))
    elif layout == "two-sided-asym":
      out.append(build_two_sided_asym_layout(
        cores,
        k=k,
        row=row,
        left_count=asym_left,
        right_count=asym_right,
      ))
    elif layout == "diagonal":
      out.append(build_diagonal_layout(cores, noc=noc, k=k, row=row))
    elif layout == "diagonal-xleg":
      out.append(build_diagonal_xleg_layout(cores, noc=noc, k=k, row=row))
    elif layout == "diagonal-yleg":
      out.append(build_diagonal_yleg_layout(cores, noc=noc, k=k, row=row))
    elif layout == "multi-row":
      out.append(build_multi_row_layout(cores, noc=noc, k=k, row=row))
    elif layout == "start-skew":
      target, senders = build_sender_set(cores, noc=noc, k=k, row=row, skew_step=skew_step)
      out.append(LayoutSpec("start-skew", target, senders))
    else:
      raise ValueError(f"unknown layout {layout!r}")
  return out


def exclude_reserved_cores(cores: list[Core], reserved: set[Core]) -> list[Core]:
  return [core for core in cores if core not in reserved]


def parse_counts(text: str) -> tuple[int, ...]:
  counts = tuple(int(item.strip()) for item in text.split(",") if item.strip())
  if not counts or any(count <= 0 for count in counts):
    raise argparse.ArgumentTypeError("expected comma-separated positive K values")
  return counts


def parse_nocs(text: str) -> tuple[int, ...]:
  nocs = tuple(int(item.strip()) for item in text.split(",") if item.strip())
  if not nocs or any(noc not in (0, 1) for noc in nocs):
    raise argparse.ArgumentTypeError("expected comma-separated NoC ids from {0,1}")
  return nocs


LAYOUTS = (
  "one-sided",
  "rank-line",
  "two-sided",
  "two-sided-asym",
  "holes",
  "diagonal",
  "diagonal-xleg",
  "diagonal-yleg",
  "multi-row",
  "start-skew",
)


def parse_layouts(text: str) -> tuple[str, ...]:
  names = tuple(item.strip() for item in text.split(",") if item.strip())
  if not names:
    raise argparse.ArgumentTypeError("expected comma-separated layout names")
  expanded: list[str] = []
  for name in names:
    if name == "all":
      expanded.extend(LAYOUTS)
    elif name in LAYOUTS:
      expanded.append(name)
    else:
      raise argparse.ArgumentTypeError(f"unknown layout {name!r}; choices: {','.join(LAYOUTS)},all")
  return tuple(dict.fromkeys(expanded))


def parse_packet_sizes(text: str) -> tuple[int, ...]:
  sizes = tuple(int(item.strip()) for item in text.split(",") if item.strip())
  if not sizes or any(size <= 0 or size > NOC.MAX_BURST_SIZE or size % 4 for size in sizes):
    raise argparse.ArgumentTypeError("packet sizes must be positive 4-byte multiples no larger than 16 KiB")
  return sizes


def parse_core_list(text: str) -> tuple[Core, ...]:
  cores = tuple(harness.parse_core(item.strip()) for item in text.split(";") if item.strip())
  if not cores:
    raise argparse.ArgumentTypeError("expected semicolon-separated X,Y source cores")
  return cores


def parse_skews(text: str) -> tuple[int, ...]:
  skews = tuple(int(item.strip(), 0) for item in text.split(",") if item.strip())
  if any(skew < 0 for skew in skews):
    raise argparse.ArgumentTypeError("sender skews must be non-negative")
  return skews


def sender_signature(senders: Sequence[SenderSpec]) -> str:
  pieces = []
  for spec in senders:
    text = f"{spec.source[0]},{spec.source[1]}"
    if spec.skew_cycles:
      text += f"+{spec.skew_cycles}"
    pieces.append(f"`{text}`")
  return " ".join(pieces)


def validate_layout(
  cores: set[Core],
  layout: LayoutSpec,
  *,
  noc: int,
  require_shared_ingress: bool = True,
):
  active = [layout.target] + [spec.source for spec in layout.senders]
  missing = [core for core in active if core not in cores]
  if missing:
    raise ValueError(f"layout {layout.label} uses non-program cores: {missing}")
  targets = {spec.target for spec in layout.senders}
  if targets != {layout.target}:
    raise ValueError(f"layout {layout.label} has inconsistent sender targets: {targets}")
  if len(set(active)) != len(active):
    raise ValueError(f"layout {layout.label} repeats a source or target core: {active}")
  final_links = {noc_topology.path_links(spec.source, spec.target, noc)[-1] for spec in layout.senders}
  if require_shared_ingress and len(final_links) != 1:
    raise ValueError(
      f"layout {layout.label} does not share one final target-ingress link on NoC{noc}: {sorted(final_links)}. "
      "Pass --allow-nonshared-ingress for a deliberate debug run."
    )
  return final_links


def seed_packet(packet_bytes: int) -> bytes:
  seed = bytearray(packet_bytes)
  for off in range(0, packet_bytes, 4):
    struct.pack_into("<I", seed, off, 0xA5000000 | off)
  return bytes(seed)


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


def clear_seed_and_gate(device: Device, senders: list[SenderSpec], *, packet_bytes: int, gate_value: int):
  target = senders[0].target
  seed = seed_packet(packet_bytes)
  with harness.device_window(device, senders[0].source) as win:
    for spec in senders:
      win.target(spec.source)
      win.write(RESULT_BASE, b"\0" * result_size())
      win.write(START_GATE_BASE, struct.pack("<Q", gate_value))
      win.write(STREAM_BASE, seed)
    win.target(target)
    win.write(START_GATE_BASE, struct.pack("<Q", gate_value))
    for spec in senders:
      win.write(spec.dest_base, b"\0" * packet_bytes)


def read_sender_result(device: Device, spec: SenderSpec) -> SenderResult:
  with harness.device_window(device, spec.source) as win:
    win.target(spec.source)
    blob = win.read(RESULT_BASE, result_size())
    words = struct.unpack_from("<" + "I" * RECORD_WORDS, blob, 0)
  if words[0] != RESULT_MAGIC:
    raise RuntimeError(f"{spec.source}: bad result magic 0x{words[0]:08x}")
  if words[2] != STATUS_DONE:
    raise RuntimeError(f"{spec.source}: benchmark did not finish, status=0x{words[2]:08x}")
  return SenderResult(spec.source, words)


def read_target_result(device: Device, target: Core) -> TargetResult:
  with harness.device_window(device, target) as win:
    win.target(target)
    blob = win.read(RESULT_BASE, result_size())
    words = struct.unpack_from("<" + "I" * RECORD_WORDS, blob, 0)
  if words[0] != RESULT_MAGIC:
    raise RuntimeError(f"{target}: bad target result magic 0x{words[0]:08x}")
  if words[2] != STATUS_DONE:
    raise RuntimeError(f"{target}: target receiver did not finish, status=0x{words[2]:08x}")
  return TargetResult(target, words)


def run_once(
  device: Device,
  senders: list[SenderSpec],
  *,
  noc: int,
  packet_bytes: int,
  packets: int,
  gate_cycles: int,
) -> tuple[list[SenderResult], TargetResult]:
  now = max(read_wall_clock_host(device, spec.source) for spec in senders)
  gate_value = now + gate_cycles
  clear_seed_and_gate(device, senders, packet_bytes=packet_bytes, gate_value=gate_value)
  device.run(ArbitrationProgram(senders, noc=noc, packet_bytes=packet_bytes, packets=packets))
  return [read_sender_result(device, spec) for spec in senders], read_target_result(device, senders[0].target)


def classify_distribution(run: ArbitrationRun) -> str:
  results = run.results
  rates = [result.bytes_per_cycle for result in results]
  if len(rates) < 2:
    return "single stream"
  avg = statistics.fmean(rates)
  spread = (max(rates) - min(rates)) / avg if avg else 0.0
  if spread <= 0.10:
    return "roughly equal"
  best_index = max(range(len(results)), key=lambda i: results[i].bytes_per_cycle)
  ranked = rank_order_indices(run)
  best_rank = ranked.index(best_index)
  if best_rank == 0:
    return "near target favored"
  if best_rank == len(results) - 1:
    return "far source favored"
  return "middle source favored"


def validation_counts(run: ArbitrationRun) -> tuple[int, int]:
  bad_counters = sum(
    result.ack_delta != run.packets or result.nonposted_req_delta != run.packets
    for result in run.results
  )
  return bad_counters, run.target_result.missing


def visibility_text(run: ArbitrationRun) -> str:
  start = run.target_result.start
  parts = []
  for i, cycle in enumerate(run.target_result.visibility_cycles[:run.k]):
    if cycle == 0:
      parts.append("miss")
    else:
      parts.append(str((cycle - start) & ((1 << 64) - 1)))
  return " ".join(parts)


def aggregate_bpc(run: ArbitrationRun) -> float:
  aggregate_window = max(result.end for result in run.results) - min(result.start for result in run.results)
  aggregate_bytes = sum(result.bytes_total for result in run.results)
  return aggregate_bytes / aggregate_window if aggregate_window > 0 else 0.0


def rank_order_indices(run: ArbitrationRun) -> list[int]:
  keyed = []
  for i, spec in enumerate(run.senders):
    path = noc_topology.noc_path(spec.source, spec.target, run.noc)
    keyed.append((len(path), path, spec.source, i))
  return [i for *_prefix, i in sorted(keyed)]


def ladder_expected_rates(run: ArbitrationRun) -> list[float]:
  total = aggregate_bpc(run)
  return [total / min(rank + 2, run.k) for rank in range(run.k)]


def ladder_text(run: ArbitrationRun) -> tuple[str, str, str]:
  if run.k < 2 or run.layout not in {
    "one-sided",
    "rank-line",
    "holes",
    "diagonal-xleg",
    "diagonal-yleg",
    "multi-row",
  }:
    return "-", "-", "-"
  order = rank_order_indices(run)
  observed = [run.results[i].bytes_per_cycle for i in order]
  expected = ladder_expected_rates(run)
  rel_errors = [
    abs(obs - exp) / exp
    for obs, exp in zip(observed, expected)
    if exp > 0
  ]
  observed_text = " ".join(f"{rate:.3f}" for rate in observed)
  expected_text = " ".join(f"{rate:.3f}" for rate in expected)
  max_error = max(rel_errors) if rel_errors else 0.0
  return observed_text, expected_text, f"{max_error:.3f}"


def format_summary(runs: list[ArbitrationRun]) -> str:
  lines = [
    "| layout | noc | K | packet B | packets | target | sender order (+skew cyc) | aggregate B/cyc | aggregate req/cyc | per-stream B/cyc | near-rank B/cyc | ladder B/cyc | max ladder err | spread | interpretation | receiver visibility cycles | bad counters | target missing | target polls |",
    "|---|---:|---:|---:|---:|---|---|---:|---:|---|---|---|---:|---:|---|---|---:|---:|---:|",
  ]
  for run in runs:
    rates = [result.bytes_per_cycle for result in run.results]
    avg = statistics.fmean(rates) if rates else 0.0
    spread = (max(rates) - min(rates)) / avg if avg else 0.0
    aggregate = aggregate_bpc(run)
    aggregate_rpc = aggregate / run.packet_bytes if run.packet_bytes > 0 else 0.0
    bad_counters, bad_sentinels = validation_counts(run)
    sender_order = sender_signature(run.senders)
    rate_text = " ".join(f"{result.bytes_per_cycle:.3f}" for result in run.results)
    rank_rates, ladder_rates, ladder_err = ladder_text(run)
    lines.append(
      f"| {run.layout} | {run.noc} | {run.k} | {run.packet_bytes} | {run.packets} | `{run.target[0]},{run.target[1]}` | "
      f"{sender_order} | {aggregate:.3f} | {aggregate_rpc:.5f} | {rate_text} | "
      f"{rank_rates} | {ladder_rates} | {ladder_err} | "
      f"{spread:.3f} | {classify_distribution(run)} | "
      f"{visibility_text(run)} | "
      f"{bad_counters} | {bad_sentinels} | {run.target_result.poll_iters} |"
    )
  return "\n".join(lines)


def assert_valid_run(run: ArbitrationRun):
  bad_counters, bad_sentinels = validation_counts(run)
  if bad_counters or bad_sentinels:
    expected = expected_sentinel(run.packet_bytes)
    raise RuntimeError(
      f"invalid arbitration run noc{run.noc} K={run.k} packet={run.packet_bytes}: "
      f"bad_counters={bad_counters} target_missing={bad_sentinels} "
      f"expected_sentinel=0x{expected:08x}. "
      "Full matrix is blocked until sentinel validation is understood; pass "
      "--allow-invalid only for a deliberate debug run."
    )


def append_report(path: Path, *, gate_cycles: int, runs: list[ArbitrationRun], argv: Sequence[str]):
  harness.append_report(path, None, [
    f"Start gate lead: `{gate_cycles}` cycles",
    f"Command: `{' '.join(argv)}`",
    "Rank-priority recipe: run through `tt-device-queue` with `PYTHONPATH=.:examples python3 microbenching/noc/riscv_noc_arbitration_bench.py --layouts rank-line --counts 2,3,4,5,6,7,8,9,10,11 --packet-bytes 16384 --packets 256 --nocs 0,1`; add K=12 on devices with at least 13 live workers in one row",
    "Asymmetry recipe: `PYTHONPATH=.:examples python3 microbenching/noc/riscv_noc_arbitration_bench.py --layouts two-sided-asym --counts 4 --asym-left 3 --asym-right 1 --packet-bytes 16384 --packets 256 --nocs 0,1`",
    "Diagonal recipe: `PYTHONPATH=.:examples python3 microbenching/noc/riscv_noc_arbitration_bench.py --layouts diagonal-xleg,diagonal-yleg --counts 4 --packet-bytes 16384 --packets 256 --nocs 0,1`",
    "Traffic: BRISC nonposted peer-L1 writes, one far-end receiver tile, one destination slice per sender",
    "Placement: target-ingress layouts include one-sided row, near-to-far rank-line, two-sided row/wrap, asymmetric two-sided, holey row, diagonal, diagonal X-leg/Y-leg, multi-row, and start-skew variants",
    "Ladder columns sort senders near-to-far by modeled routed path and compare against aggregate/min(rank+2,K), which gives the farthest two senders the same tail share",
    "Receiver visibility cycles are target-side first-observed sentinel timestamps relative to the receiver's gated start",
  ], format_summary(runs))


def explicit_layout(args) -> LayoutSpec | None:
  if args.target is None and args.sources is None:
    return None
  if args.target is None or args.sources is None:
    raise ValueError("--target and --sources must be provided together")
  skews = args.sender_skews or ()
  if skews and len(skews) != len(args.sources):
    raise ValueError("--sender-skews must have one entry per --sources core")
  senders = []
  for i, source in enumerate(args.sources):
    senders.append(SenderSpec(
      index=i,
      source=source,
      target=args.target,
      dest_base=DEST_BASE + i * DEST_STRIDE,
      skew_cycles=skews[i] if skews else 0,
    ))
  return LayoutSpec("explicit", args.target, senders)


def selected_layouts(cores: list[Core], args, *, noc: int, k: int) -> list[LayoutSpec]:
  explicit = explicit_layout(args)
  if explicit is not None:
    return [explicit]
  return build_layouts(
    cores,
    layouts=args.layouts,
    noc=noc,
    k=k,
    row=args.row,
    skew_step=args.skew_step,
    asym_left=args.asym_left,
    asym_right=args.asym_right,
  )


def dry_run(args):
  runs = []
  cores = exclude_reserved_cores(P100_PROGRAM_CORES, P100_FAST_DISPATCH_RESERVED)
  core_set = set(cores)
  for noc in args.nocs:
    for k in args.counts:
      for layout in selected_layouts(cores, args, noc=noc, k=k):
        final_links = validate_layout(
          core_set,
          layout,
          noc=noc,
          require_shared_ingress=not args.allow_nonshared_ingress,
        )
        for packet_bytes in args.packet_bytes:
          program = ArbitrationProgram(layout.senders, noc=noc, packet_bytes=packet_bytes, packets=args.packets)
          program.lower(dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0)
          print(
            f"dry-run layout={layout.label} noc{noc} K={len(layout.senders)} packet={packet_bytes} "
            f"packets={args.packets} target={layout.target} senders={sender_signature(layout.senders)} "
            f"final_links={sorted(final_links)}"
          )
          runs.append((layout.label, noc, k, packet_bytes, layout.target, layout.senders))
  return runs


def main():
  parser = argparse.ArgumentParser(description="Blackhole target-ingress NoC arbitration layouts.")
  parser.add_argument("--nocs", type=parse_nocs, default=(0, 1), help="comma-separated NoC ids, default: 0,1")
  parser.add_argument("--counts", type=parse_counts, default=parse_counts("2,3,4,6,8"), help="comma-separated K values")
  parser.add_argument("--layouts", type=parse_layouts, default=parse_layouts("one-sided"), help=f"comma-separated layouts from {','.join(LAYOUTS)} or all")
  parser.add_argument("--packet-bytes", type=parse_packet_sizes, default=parse_packet_sizes("4096,16384"))
  parser.add_argument("--packets", type=int, default=256, help="NoC write packets per sender")
  parser.add_argument("--row", type=int, default=None, help="physical row to use; default: row with most program cores")
  parser.add_argument("--target", type=harness.parse_core, default=None, help="explicit target core X,Y; requires --sources")
  parser.add_argument("--sources", type=parse_core_list, default=None, help="explicit semicolon-separated sender cores X,Y;X,Y")
  parser.add_argument("--sender-skews", type=parse_skews, default=None, help="explicit per-sender start skews for --sources")
  parser.add_argument("--skew-step", type=int, default=10_000, help="cycles between senders for --layouts start-skew")
  parser.add_argument("--asym-left", type=int, default=3, help="left-side sender count for --layouts two-sided-asym")
  parser.add_argument("--asym-right", type=int, default=1, help="right-side sender count for --layouts two-sided-asym")
  parser.add_argument("--gate-cycles", type=int, default=100_000_000, help="future WALL_CLOCK start-gate lead")
  parser.add_argument("--dry-run", action="store_true", help="lower programs without opening the device")
  parser.add_argument("--allow-nonshared-ingress", action="store_true", help="allow layouts whose streams do not share one final target-ingress link")
  parser.add_argument("--allow-invalid", action="store_true", help="do not abort/report-block on bad counters or target receiver misses")
  parser.add_argument("--no-report", action="store_true", help="do not append docs/noc-arbitration.md")
  parser.add_argument("--report", type=Path, default=harness.doc_path("noc", "noc-arbitration.md"), help="markdown report path")
  args = parser.parse_args()
  if args.packets <= 0:
    raise ValueError("--packets must be positive")
  if args.gate_cycles <= 0:
    raise ValueError("--gate-cycles must be positive")
  if args.skew_step < 0:
    raise ValueError("--skew-step must be non-negative")
  if max(args.counts) > MAX_SENDERS:
    raise ValueError(f"this experiment supports K up to {MAX_SENDERS}")
  if args.sources is not None and len(args.sources) > MAX_SENDERS:
    raise ValueError(f"--sources supports at most {MAX_SENDERS} senders")
  if (args.target is None) != (args.sources is None):
    raise ValueError("--target and --sources must be provided together")
  if args.sources is not None:
    args.counts = (len(args.sources),)

  if args.dry_run:
    dry_run(args)
    return

  runs: list[ArbitrationRun] = []
  with harness.open_device() as device:
    reserved = {
      getattr(device.board_info, "dispatch_core", None),
      getattr(device.board_info, "prefetch_core", None),
    }
    core_set = set(device.cores) - {core for core in reserved if core is not None}
    usable_cores = sorted(core_set)
    for noc in args.nocs:
      for k in args.counts:
        for layout in selected_layouts(usable_cores, args, noc=noc, k=k):
          validate_layout(
            core_set,
            layout,
            noc=noc,
            require_shared_ingress=not args.allow_nonshared_ingress,
          )
          for packet_bytes in args.packet_bytes:
            results, target_result = run_once(
              device,
              layout.senders,
              noc=noc,
              packet_bytes=packet_bytes,
              packets=args.packets,
              gate_cycles=args.gate_cycles,
            )
            runs.append(ArbitrationRun(
              layout=layout.label,
              noc=noc,
              k=len(layout.senders),
              packet_bytes=packet_bytes,
              packets=args.packets,
              target=layout.target,
              senders=layout.senders,
              results=results,
              target_result=target_result,
            ))
            if not args.allow_invalid:
              try:
                assert_valid_run(runs[-1])
              except RuntimeError:
                print(format_summary(runs[-1:]))
                raise

  print(format_summary(runs))
  if not args.no_report:
    append_report(args.report, gate_cycles=args.gate_cycles, runs=runs, argv=sys.argv)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
