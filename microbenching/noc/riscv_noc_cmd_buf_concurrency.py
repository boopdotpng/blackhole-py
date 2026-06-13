#!/usr/bin/env python3
from __future__ import annotations

import argparse
import itertools
import math
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
from asm import KernelBase  # noqa: E402
from device import Device  # noqa: E402
from dsl import a2, a3, a4, a5, s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, t0, t1, t3, t4, zero  # noqa: E402
from pcie import TLBWindow  # noqa: E402
from program import DevMsgs, Program, Run, UnicastWrite  # noqa: E402
from ttk.addrs import Core, align_down, noc_xy  # noqa: E402
from ttk.mailbox import BriscMailbox as BM  # noqa: E402
from ttk.noc import NOC, Noc  # noqa: E402
from ttk.tensix import TensixL1, TensixMMIO  # noqa: E402


RESULT_BASE = 0x150000
RESULT_STRIDE = 0x100
RESULT_WORDS = 24
RESULT_SIZE = RESULT_WORDS * 4
RESULT_MAGIC = 0x43424343  # "CBCC"
STATUS_STARTED = 0xCB000001
STATUS_DONE = 0xCB00D00D
STATUS_TIMEOUT_READY = 0xCB00E001
STATUS_TIMEOUT_FLUSH = 0xCB00E002

STREAM_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
READ_SINK_BASE = STREAM_BASE + NOC.MAX_BURST_SIZE
START_GATE_BASE = RESULT_BASE - 0x40

ROLE_BRISC = 0
ROLE_NCRISC = 1
ROLE_NAMES = {ROLE_BRISC: "brisc", ROLE_NCRISC: "ncrisc"}

OP_WRITE = "write"
OP_READ = "read"
OP_ATOMIC = "atomic"
OP_INLINE = "inline"
OPS = (OP_WRITE, OP_READ, OP_ATOMIC, OP_INLINE)
OP_IDS = {name: i for i, name in enumerate(OPS)}
OP_NAMES = {i: name for name, i in OP_IDS.items()}
OP_COUNTER = {
  OP_WRITE: NOC.NIU_MST_WR_ACK_RECEIVED,
  OP_READ: NOC.NIU_MST_RD_RESP_RECEIVED,
  OP_ATOMIC: NOC.NIU_MST_ATOMIC_RESP_RECEIVED,
  OP_INLINE: NOC.NIU_MST_WR_ACK_RECEIVED,
}
DEFAULT_SLOT = {
  OP_WRITE: 0,
  OP_READ: 1,
  OP_INLINE: 2,
  OP_ATOMIC: 3,
}

PAIR_NAMES = ("write+read", "write+atomic", "write+inline")
SLOT_MODES = ("diff", "same")
NOC_MODES = ("same0", "same1", "diff01", "diff10")

P100_WORKER_X = (*range(1, 8), *range(10, 15))
P100_WORKER_Y = tuple(range(2, 12))
P100_FAST_DISPATCH_RESERVED = {(14, 2), (14, 3)}


class CmdBufKernel(KernelBase, Noc):
  pass


@dataclass(frozen=True)
class Case:
  pair: str
  noc_mode: str
  slot_mode: str
  source: Core
  brisc_target: Core
  ncrisc_target: Core
  brisc_op: str
  ncrisc_op: str
  brisc_noc: int
  ncrisc_noc: int
  brisc_slot: int
  ncrisc_slot: int

  @property
  def label(self) -> str:
    return f"{self.pair}:{self.noc_mode}:{self.slot_mode}"


@dataclass(frozen=True)
class Result:
  role: int
  op: str
  noc: int
  slot: int
  status: int
  source: Core
  target: Core
  iters: int
  bytes_per_iter: int
  cycles: int
  counter_delta: int
  sink: int

  @property
  def ok(self) -> bool:
    return self.status == STATUS_DONE

  @property
  def rate(self) -> float:
    if self.cycles <= 0:
      return 0.0
    if self.op in (OP_WRITE, OP_READ):
      return self.iters * self.bytes_per_iter / self.cycles
    return self.cycles / self.iters if self.iters > 0 else 0.0


def parse_csv(choices: tuple[str, ...]):
  def parse(text: str) -> tuple[str, ...]:
    values = tuple(part.strip() for part in text.split(",") if part.strip())
    if not values:
      raise argparse.ArgumentTypeError("expected comma-separated values")
    bad = sorted(set(values) - set(choices))
    if bad:
      raise argparse.ArgumentTypeError(f"unknown values: {', '.join(bad)}")
    return values
  return parse


def emit_counter_read(fw: CmdBufKernel, noc: int, counter: int, out, *, addr=t3):
  fw.li(addr, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  return fw.lw(out, addr, 0)


def emit_result_header(fw: CmdBufKernel, *, role: int, op: str, noc: int, slot: int,
                       iters: int, bytes_per_iter: int, status: int):
  base = RESULT_BASE + role * RESULT_STRIDE
  fw.li(s2, base)
  for off, value in enumerate((
    RESULT_MAGIC, role, OP_IDS[op], noc, slot, iters, bytes_per_iter, status,
    STREAM_BASE, READ_SINK_BASE + role * 0x1000,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off in range(10, RESULT_WORDS):
    fw.sw(zero, s2, off * 4)
  return fw


def emit_finish(fw: CmdBufKernel, *, role: int, status, start_lo=a2, start_hi=a3,
                end_lo=a4, end_hi=a5, before=s7, after=s8, sink=s1):
  base = RESULT_BASE + role * RESULT_STRIDE
  fw.li(s2, base)
  for off, reg in enumerate((start_lo, start_hi, end_lo, end_hi, before, after, sink), start=10):
    fw.sw(reg, s2, off * 4)
  fw.sw(status, s2, 7 * 4)
  return fw.ret()


def emit_wait_gate(fw: CmdBufKernel):
  fw.li(s2, START_GATE_BASE)
  fw.lw(s3, s2, 0)
  fw.lw(s4, s2, 4)
  fw.or_(t0, s3, s4)
  no_gate = fw._new_label("cmd_gate_none")
  wait = fw._new_label("cmd_gate_wait")
  done = fw._new_label("cmd_gate_done")
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


def emit_wait_cmd_ready(fw: CmdBufKernel, *, noc: int, slot: int, budget: int, fail_label: str):
  fw.li(t3, NOC.CMD_CTRL + (slot << NOC.CMD_BUF_OFFSET_BIT) + (noc << NOC.INSTANCE_OFFSET_BIT))
  fw.li(t1, budget)
  loop = fw._new_label("cmd_ready")
  ready = fw._new_label("cmd_ready_done")
  fw.label(loop)
  fw.lw(t4, t3, 0)
  fw.beq(t4, zero, ready)
  fw.addi(t1, t1, -1)
  fw.bne(t1, zero, loop)
  fw.j(fail_label)
  fw.label(ready)
  return fw


def emit_wait_counter(fw: CmdBufKernel, *, noc: int, counter: int, budget: int, fail_label: str):
  fw.li(t3, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  fw.li(t1, budget)
  loop = fw._new_label("cmd_flush")
  done = fw._new_label("cmd_flush_done")
  fw.label(loop)
  fw.lw(t4, t3, 0)
  fw.bgeu(t4, s6, done)
  fw.addi(t1, t1, -1)
  fw.bne(t1, zero, loop)
  fw.j(fail_label)
  fw.label(done)
  return fw.fence()


def emit_issue_op(fw: CmdBufKernel, *, op: str, noc: int, slot: int, fail_label: str,
                  ready_budget: int, value_seed: int):
  emit_wait_cmd_ready(fw, noc=noc, slot=slot, budget=ready_budget, fail_label=fail_label)
  if op == OP_WRITE:
    fw.noc_cmd_reg(noc, slot, NOC.CTRL, NOC.CMD_WR_FIELD, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.TARG_ADDR_LO, s2, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.RET_ADDR_LO, s2, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.RET_ADDR_MID, 0, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.RET_ADDR_COORDINATE, s9, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.AT_LEN_BE, s4, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.AT_LEN_BE_1, 0, addr=t3, tmp=t4)
  elif op == OP_READ:
    fw.noc_cmd_reg(noc, slot, NOC.CTRL, NOC.CMD_RD_FIELD, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.RET_ADDR_LO, s3, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.RET_ADDR_MID, 0, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.RET_ADDR_COORDINATE, s5, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.TARG_ADDR_LO, s2, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.TARG_ADDR_MID, 0, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.TARG_ADDR_COORDINATE, s9, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.AT_LEN_BE, s4, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.AT_LEN_BE_1, 0, addr=t3, tmp=t4)
  elif op == OP_ATOMIC:
    fw.noc_cmd_reg(noc, slot, NOC.RET_ADDR_LO, s3, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.RET_ADDR_MID, 0, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.RET_ADDR_COORDINATE, s5, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.TARG_ADDR_LO, s2, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.TARG_ADDR_MID, 0, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.TARG_ADDR_COORDINATE, s9, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.CTRL, NOC.CMD_AT_INC_FIELD, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.AT_LEN_BE, NOC.AT_INCR_GET, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.AT_LEN_BE_1, 0, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.AT_DATA, 1, addr=t3, tmp=t4)
  elif op == OP_INLINE:
    fw.li(t0, 0x1A110000 | value_seed)
    fw.noc_cmd_reg(noc, slot, NOC.AT_DATA, t0, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.CTRL, NOC.CMD_INLINE_FIELD, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.TARG_ADDR_LO, s2, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.TARG_ADDR_MID, 0, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.TARG_ADDR_COORDINATE, s9, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.AT_LEN_BE, 0xF, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, slot, NOC.AT_LEN_BE_1, 0, addr=t3, tmp=t4)
  else:
    raise ValueError(f"unknown op {op}")
  fw.noc_cmd_reg(noc, slot, NOC.CMD_CTRL, NOC.CTRL_SEND_REQ, addr=t3, tmp=t4)
  fw.addi(s6, s6, 1)
  return fw


def build_role_kernel(*, role: int, op: str, noc: int, slot: int, iters: int,
                      bytes_per_iter: int, ready_timeout: int, flush_timeout: int) -> KernelBase:
  fail_ready = f"cmd_fail_ready_{role}"
  fail_flush = f"cmd_fail_flush_{role}"
  fw = CmdBufKernel()
  emit_result_header(
    fw, role=role, op=op, noc=noc, slot=slot, iters=iters,
    bytes_per_iter=bytes_per_iter, status=STATUS_STARTED,
  )
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s9,))
  fw.local_noc_coord(noc, s5, x_addr=BM.MY_X, y_addr=BM.MY_Y)
  fw.li(s2, STREAM_BASE + role * 0x4000)
  fw.li(s3, READ_SINK_BASE + role * 0x1000)
  fw.li(s4, bytes_per_iter)
  emit_counter_read(fw, noc, OP_COUNTER[op], s7)
  fw.mv(s6, s7)
  emit_wait_gate(fw)
  harness.read_wall_clock(fw, a2, a3)
  fw.li(s0, iters)
  loop = fw._new_label("cmd_loop")
  done = fw._new_label("cmd_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  emit_issue_op(
    fw, op=op, noc=noc, slot=slot, fail_label=fail_ready,
    ready_budget=ready_timeout, value_seed=role,
  )
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  emit_wait_counter(
    fw, noc=noc, counter=OP_COUNTER[op], budget=flush_timeout,
    fail_label=fail_flush,
  )
  harness.read_wall_clock(fw, a4, a5)
  emit_counter_read(fw, noc, OP_COUNTER[op], s8)
  if op == OP_READ:
    fw.li(s2, READ_SINK_BASE + role * 0x1000)
    fw.lw(s1, s2, 0)
  else:
    fw.mv(s1, zero)
  fw.li(s11, STATUS_DONE)
  emit_finish(fw, role=role, status=s11)

  fw.label(fail_ready)
  harness.read_wall_clock(fw, a4, a5)
  emit_counter_read(fw, noc, OP_COUNTER[op], s8)
  fw.mv(s1, zero)
  fw.li(s11, STATUS_TIMEOUT_READY)
  emit_finish(fw, role=role, status=s11)

  fw.label(fail_flush)
  harness.read_wall_clock(fw, a4, a5)
  emit_counter_read(fw, noc, OP_COUNTER[op], s8)
  fw.mv(s1, zero)
  fw.li(s11, STATUS_TIMEOUT_FLUSH)
  emit_finish(fw, role=role, status=s11)
  return fw


class CmdBufProgram:
  def __init__(self, case: Case, *, iters: int, bytes_per_iter: int,
               ready_timeout: int, flush_timeout: int):
    self.case = case
    self.iters = iters
    self.bytes_per_iter = bytes_per_iter
    self.ready_timeout = ready_timeout
    self.flush_timeout = flush_timeout
    self.name = f"riscv_noc_cmd_buf_concurrency:{case.label}"

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    empty = KernelBase()
    brisc = build_role_kernel(
      role=ROLE_BRISC, op=self.case.brisc_op, noc=self.case.brisc_noc,
      slot=self.case.brisc_slot, iters=self.iters, bytes_per_iter=self.bytes_per_iter,
      ready_timeout=self.ready_timeout, flush_timeout=self.flush_timeout,
    )
    ncrisc = build_role_kernel(
      role=ROLE_NCRISC, op=self.case.ncrisc_op, noc=self.case.ncrisc_noc,
      slot=self.case.ncrisc_slot, iters=self.iters, bytes_per_iter=self.bytes_per_iter,
      ready_timeout=self.ready_timeout, flush_timeout=self.flush_timeout,
    )
    brisc.rta(lambda _x, _y: [noc_xy(*self.case.brisc_target)])
    ncrisc.rta(lambda _x, _y: [noc_xy(*self.case.ncrisc_target)])
    source_segments = Program(
      brisc=brisc,
      ncrisc=ncrisc,
      trisc0=empty,
      trisc1=empty,
      trisc2=empty,
      num_cores=1,
    ).layout(core_xy=self.case.source, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id)
    target_cores = [self.case.source]
    per_core_segments = {self.case.source: source_segments}
    for target in sorted({self.case.brisc_target, self.case.ncrisc_target} - {self.case.source}):
      per_core_segments[target] = Program(
        brisc=KernelBase().ret(),
        ncrisc=empty,
        trisc0=empty,
        trisc1=empty,
        trisc2=empty,
        num_cores=1,
      ).layout(core_xy=target, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id)
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


def choose_placement(cores: list[Core], row: int | None) -> tuple[Core, Core, Core]:
  rows = rows_by_y(cores)
  if row is not None:
    xs = rows.get(row)
    if xs is None or len(xs) < 3:
      raise ValueError(f"row {row} needs at least three program cores")
    y = row
  else:
    candidates = [(len(xs), -y, y, xs) for y, xs in rows.items() if len(xs) >= 3]
    if not candidates:
      raise ValueError("need a row with at least three program cores")
    _, _, y, xs = max(candidates)
  source = (xs[len(xs) // 2], y)
  return source, (xs[-1], y), (xs[0], y)


def usable_cores(device: Device | None) -> list[Core]:
  if device is None:
    return [(x, y) for y in P100_WORKER_Y for x in P100_WORKER_X if (x, y) not in P100_FAST_DISPATCH_RESERVED]
  reserved = {
    getattr(device.board_info, "dispatch_core", None),
    getattr(device.board_info, "prefetch_core", None),
  }
  return sorted(set(device.cores) - {core for core in reserved if core is not None})


def nocs_for_mode(mode: str) -> tuple[int, int]:
  return {
    "same0": (0, 0),
    "same1": (1, 1),
    "diff01": (0, 1),
    "diff10": (1, 0),
  }[mode]


def ops_for_pair(pair: str) -> tuple[str, str]:
  lhs, rhs = pair.split("+", 1)
  if lhs != OP_WRITE or rhs not in (OP_READ, OP_ATOMIC, OP_INLINE):
    raise ValueError(f"unsupported pair {pair}")
  return lhs, rhs


def slots_for_ops(brisc_op: str, ncrisc_op: str, slot_mode: str) -> tuple[int, int]:
  if slot_mode == "diff":
    return DEFAULT_SLOT[brisc_op], DEFAULT_SLOT[ncrisc_op]
  if slot_mode == "same":
    return 0, 0
  raise ValueError(f"unknown slot mode {slot_mode}")


def build_cases(*, source: Core, brisc_target: Core, ncrisc_target: Core,
                pairs: tuple[str, ...], noc_modes: tuple[str, ...],
                slot_modes: tuple[str, ...]) -> list[Case]:
  cases = []
  for pair, noc_mode, slot_mode in itertools.product(pairs, noc_modes, slot_modes):
    brisc_op, ncrisc_op = ops_for_pair(pair)
    brisc_noc, ncrisc_noc = nocs_for_mode(noc_mode)
    brisc_slot, ncrisc_slot = slots_for_ops(brisc_op, ncrisc_op, slot_mode)
    cases.append(Case(
      pair=pair,
      noc_mode=noc_mode,
      slot_mode=slot_mode,
      source=source,
      brisc_target=brisc_target,
      ncrisc_target=ncrisc_target,
      brisc_op=brisc_op,
      ncrisc_op=ncrisc_op,
      brisc_noc=brisc_noc,
      ncrisc_noc=ncrisc_noc,
      brisc_slot=brisc_slot,
      ncrisc_slot=ncrisc_slot,
    ))
  return cases


def seed_payload(bytes_per_iter: int) -> bytes:
  payload = bytearray(max(NOC.MAX_BURST_SIZE, bytes_per_iter))
  for off in range(0, len(payload), 4):
    struct.pack_into("<I", payload, off, 0xA5000000 | off)
  return bytes(payload)


def clear_and_seed(device: Device, case: Case, *, bytes_per_iter: int, gate_value: int):
  payload = seed_payload(bytes_per_iter)
  gate_blob = struct.pack("<Q", gate_value)
  with harness.device_window(device, case.source) as win:
    for core in sorted({case.source, case.brisc_target, case.ncrisc_target}):
      win.target(core)
      win.write(RESULT_BASE, b"\0" * (RESULT_STRIDE * 3))
      win.write(START_GATE_BASE, gate_blob)
      win.write(STREAM_BASE, payload)
      win.write(STREAM_BASE + 0x4000, payload)
      win.write(READ_SINK_BASE, b"\0" * 0x3000)
    for target in (case.brisc_target, case.ncrisc_target):
      win.target(target)
      win.write(STREAM_BASE, payload)
      win.write(STREAM_BASE + 0x4000, payload)


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


def parse_result(blob: bytes, *, role: int, source: Core, target: Core) -> Result:
  words = struct.unpack_from("<" + "I" * RESULT_WORDS, blob, 0)
  if words[0] != RESULT_MAGIC:
    raise RuntimeError(f"{ROLE_NAMES[role]} bad result magic 0x{words[0]:08x}")
  result_role = words[1]
  if result_role != role:
    raise RuntimeError(f"{ROLE_NAMES[role]} result role mismatch {result_role}")
  return Result(
    role=role,
    op=OP_NAMES[words[2]],
    noc=words[3],
    slot=words[4],
    status=words[7],
    source=source,
    target=target,
    iters=words[5],
    bytes_per_iter=words[6],
    cycles=((words[12] | (words[13] << 32)) - (words[10] | (words[11] << 32))) & ((1 << 64) - 1),
    counter_delta=(words[15] - words[14]) & 0xFFFFFFFF,
    sink=words[16],
  )


def read_results(device: Device, case: Case) -> tuple[Result, Result]:
  with harness.device_window(device, case.source) as win:
    win.target(case.source)
    brisc_blob = win.read(RESULT_BASE + ROLE_BRISC * RESULT_STRIDE, RESULT_SIZE)
    ncrisc_blob = win.read(RESULT_BASE + ROLE_NCRISC * RESULT_STRIDE, RESULT_SIZE)
  return (
    parse_result(brisc_blob, role=ROLE_BRISC, source=case.source, target=case.brisc_target),
    parse_result(ncrisc_blob, role=ROLE_NCRISC, source=case.source, target=case.ncrisc_target),
  )


def run_case(device: Device, case: Case, *, iters: int, bytes_per_iter: int,
             ready_timeout: int, flush_timeout: int, gate_delay_cycles: int) -> tuple[Result, Result]:
  gate = 0 if gate_delay_cycles == 0 else read_host_wall_clock(device, case.source) + gate_delay_cycles
  clear_and_seed(device, case, bytes_per_iter=bytes_per_iter, gate_value=gate)
  device.run(CmdBufProgram(
    case,
    iters=iters,
    bytes_per_iter=bytes_per_iter,
    ready_timeout=ready_timeout,
    flush_timeout=flush_timeout,
  ))
  return read_results(device, case)


def status_text(status: int) -> str:
  return {
    STATUS_DONE: "pass",
    STATUS_STARTED: "started",
    STATUS_TIMEOUT_READY: "timeout-ready",
    STATUS_TIMEOUT_FLUSH: "timeout-flush",
  }.get(status, f"0x{status:08x}")


def result_cell(result: Result | None) -> str:
  if result is None:
    return "dry-run"
  suffix = "B/cyc" if result.op in (OP_WRITE, OP_READ) else "cyc/op"
  value = result.rate
  if math.isinf(value):
    return "inf"
  return f"{status_text(result.status)} {value:.3f} {suffix} ctr={result.counter_delta}"


def format_table(rows: list[tuple[Case, Result | None, Result | None]]) -> str:
  lines = [
    "| pair | nocs | slots | source | brisc target | ncrisc target | BRISC result | NCRISC result | verdict |",
    "|---|---|---|---|---|---|---|---|---|",
  ]
  for case, brisc, ncrisc in rows:
    if brisc is None or ncrisc is None:
      verdict = "planned"
    elif brisc.ok and ncrisc.ok:
      verdict = "pass"
    else:
      verdict = "timeout/error"
    lines.append(
      f"| {case.pair} | `{case.brisc_noc}/{case.ncrisc_noc}` | "
      f"`{case.brisc_slot}/{case.ncrisc_slot}` ({case.slot_mode}) | "
      f"`{case.source[0]},{case.source[1]}` | "
      f"`{case.brisc_target[0]},{case.brisc_target[1]}` | "
      f"`{case.ncrisc_target[0]},{case.ncrisc_target[1]}` | "
      f"{result_cell(brisc)} | {result_cell(ncrisc)} | {verdict} |"
    )
  return "\n".join(lines)


def append_report(path: Path, *, args, rows: list[tuple[Case, Result | None, Result | None]]):
  metadata = [
    f"Command-buffer matrix: pairs `{','.join(args.pairs)}`, NoC modes `{','.join(args.noc_modes)}`, slot modes `{','.join(args.slot_modes)}`",
    f"Iters: `{args.iters}`, bytes per copy command: `{args.bytes}`, command-ready timeout loops: `{args.ready_timeout}`, response timeout loops: `{args.flush_timeout}`",
    "Traffic uses one BRISC and one NCRISC on the same Tensix core, with disjoint remote L1 targets by default.",
    "Rates are bytes/cycle for read/write copies and cycles/op for atomic/inline operations.",
    "Same-slot rows are intentionally opt-in because both RISCs program the same NIU command buffer concurrently.",
  ]
  harness.append_report(path, "NoC command-buffer concurrency truth table", metadata, format_table(rows))


def main():
  parser = argparse.ArgumentParser(description="Safe BRISC+NCRISC NoC command-buffer ownership/concurrency probe.")
  parser.add_argument("--dry-run", action="store_true", help="compile/lower planned cases without opening hardware")
  parser.add_argument("--pairs", type=parse_csv(PAIR_NAMES), default=("write+read",),
                      help="comma list: write+read,write+atomic,write+inline")
  parser.add_argument("--noc-modes", type=parse_csv(NOC_MODES), default=("same0", "diff01"),
                      help="comma list: same0,same1,diff01,diff10; values are BRISC/NCRISC NoC assignment")
  parser.add_argument("--slot-modes", type=parse_csv(SLOT_MODES), default=("diff",),
                      help="comma list: diff,same; same is opt-in risky ownership coverage")
  parser.add_argument("--include-same-slot", action="store_true",
                      help="allow --slot-modes same; otherwise same-slot cases are rejected")
  parser.add_argument("--row", type=int, default=None)
  parser.add_argument("--source", type=harness.parse_core, default=None)
  parser.add_argument("--brisc-target", type=harness.parse_core, default=None)
  parser.add_argument("--ncrisc-target", type=harness.parse_core, default=None)
  parser.add_argument("--bytes", type=int, default=4096, help="copy size for read/write commands")
  parser.add_argument("--iters", type=int, default=8)
  parser.add_argument("--ready-timeout", type=int, default=1_000_000,
                      help="RISC loop iterations while waiting for CMD_CTRL to clear")
  parser.add_argument("--flush-timeout", type=int, default=10_000_000,
                      help="RISC loop iterations while waiting for response counters")
  parser.add_argument("--gate-delay-cycles", type=int, default=20_000_000)
  parser.add_argument("--no-report", action="store_true")
  parser.add_argument("--report", type=Path, default=harness.doc_path("noc", "noc-cmd-buffer-concurrency.md"))
  args = parser.parse_args()

  if args.bytes <= 0 or args.bytes > NOC.MAX_BURST_SIZE or args.bytes % 4:
    raise ValueError(f"--bytes must be a 4-byte multiple in [4, {NOC.MAX_BURST_SIZE}]")
  if args.iters <= 0:
    raise ValueError("--iters must be positive")
  if args.ready_timeout <= 0 or args.flush_timeout <= 0:
    raise ValueError("--ready-timeout and --flush-timeout must be positive")
  if args.gate_delay_cycles < 0:
    raise ValueError("--gate-delay-cycles must be non-negative")
  if "same" in args.slot_modes and not args.include_same_slot:
    raise ValueError("same-slot cases are opt-in; pass --include-same-slot to run them")

  device = None if args.dry_run else Device()
  try:
    cores = usable_cores(device)
    source, brisc_target, ncrisc_target = choose_placement(cores, args.row)
    source = args.source or source
    brisc_target = args.brisc_target or brisc_target
    ncrisc_target = args.ncrisc_target or ncrisc_target
    required = {source, brisc_target, ncrisc_target}
    missing = sorted(required - set(cores))
    if missing:
      raise ValueError(f"selected unavailable cores: {missing}")
    if len(required) != 3:
      raise ValueError("source, --brisc-target, and --ncrisc-target must be three distinct cores")

    cases = build_cases(
      source=source,
      brisc_target=brisc_target,
      ncrisc_target=ncrisc_target,
      pairs=args.pairs,
      noc_modes=args.noc_modes,
      slot_modes=args.slot_modes,
    )
    rows: list[tuple[Case, Result | None, Result | None]] = []
    if args.dry_run:
      for case in cases:
        CmdBufProgram(
          case,
          iters=args.iters,
          bytes_per_iter=args.bytes,
          ready_timeout=args.ready_timeout,
          flush_timeout=args.flush_timeout,
        ).lower([source, brisc_target, ncrisc_target])
        rows.append((case, None, None))
    else:
      assert device is not None
      for case in cases:
        rows.append((case, *run_case(
          device,
          case,
          iters=args.iters,
          bytes_per_iter=args.bytes,
          ready_timeout=args.ready_timeout,
          flush_timeout=args.flush_timeout,
          gate_delay_cycles=args.gate_delay_cycles,
        )))
  finally:
    if device is not None:
      device.close()

  table = format_table(rows)
  print(table)
  if not args.no_report and not args.dry_run:
    append_report(args.report, args=args, rows=rows)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
