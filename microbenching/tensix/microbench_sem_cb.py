#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as _dt
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402  (does sys.path + TT_USB bootstrap on import)
from asm import KernelBase
from device import Device
from dsl import (
  TTSEMINIT, TTSEMGET, TTSEMPOST, TTSEMWAIT,
  a2, a3, a4, a5, a6, a7,
  s0, s1, s2, s3, s4, s5, s6, s7, s8,
  t0, t1, t2, t3, t4, t5, t6, zero,
)
from program import Dtype, Program
from ttk import Cb, Noc, Tensix
from ttk.cb import CircularBuffer as CB
from ttk.debug import DebugRange
from ttk.mailbox import BriscMailbox as BM
from ttk.noc import NOC
from ttk.tensix import TensixMMIO, TensixRegs, TensixSem, TensixSemWait, TensixStall, TensixWait


Core = tuple[int, int]

RESULT_BASE = 0x130000
CONTROL_BASE = 0x134000
NOC_SEM_ADDR = 0x134100
HEADER_WORDS = 16
RECORD_WORDS = 12
HEADER_SIZE = HEADER_WORDS * 4
RECORD_SIZE = RECORD_WORDS * 4
RESULT_MAGIC = 0x53434248  # "SCBH"
RECORD_MAGIC = 0x53434252  # "SCBR"
STATUS_STARTED = 0x5C0B0001
STATUS_DONE = 0x5C0BD00D

CTRL_SEQ = CONTROL_BASE + 0x00
CTRL_KIND = CONTROL_BASE + 0x04
CTRL_DELAY = CONTROL_BASE + 0x08
CTRL_DONE = CONTROL_BASE + 0x0C

REQ_NONE = 0
REQ_CB_RECEIVED = 1
REQ_CB_ACKED = 2
REQ_NOC_SEM_SET = 3
REQ_STOP = 0xFFFF_FFFF

CB_INDEX = 0
CB_PAGES = 32768
TILE_BYTES = Dtype.Float16_b.tile_size

TTSEM = TensixSem.mask(TensixSem.MATH_PACK)
TTSEM_INIT_READY = TTSEMINIT(sem_sel=TTSEM, init_value=0, max_value=15)
TTSEM_INIT_GET = TTSEMINIT(sem_sel=TTSEM, init_value=1, max_value=15)
TTSEM_WAIT_READY = TTSEMWAIT(TensixStall.SYNC, TTSEM, TensixSemWait.STALL_ON_MAX)
TTSEM_POST = TTSEMPOST(TTSEM)
TTSEM_GET = TTSEMGET(TTSEM)


@dataclass(frozen=True)
class BenchSpec:
  name: str
  group: str
  ops_per_iter: int
  role: str
  blocking: bool = False


BRISC_SPECS = (
  BenchSpec("empty", "baseline", 0, "brisc"),
  BenchSpec("release_signal", "control", 1, "brisc"),
  BenchSpec("cb_wait_front_ready", "cb", 1, "brisc"),
  BenchSpec("cb_wait_front_block", "cb", 1, "brisc", blocking=True),
  BenchSpec("cb_reserve_back_ready", "cb", 1, "brisc"),
  BenchSpec("cb_reserve_back_block", "cb", 1, "brisc", blocking=True),
  BenchSpec("cb_push_back", "cb", 1, "brisc"),
  BenchSpec("cb_pop_front", "cb", 1, "brisc"),
  BenchSpec("noc_sem_set", "noc_sem", 1, "brisc"),
  BenchSpec("noc_sem_wait_ready", "noc_sem", 1, "brisc"),
  BenchSpec("noc_sem_wait_block", "noc_sem", 1, "brisc", blocking=True),
  BenchSpec("noc_sem_inc_wait", "noc_sem", 1, "brisc"),
)

TRISC_SPECS = (
  BenchSpec("trisc_empty", "baseline", 0, "trisc2"),
  BenchSpec("cb_push_back_tensix_received", "cb_tensix", 1, "trisc2"),
  BenchSpec("cb_pop_front_tensix_ack", "cb_tensix", 1, "trisc2"),
  BenchSpec("ttsemwait_ready_sync", "ttsem", 1, "trisc2"),
  BenchSpec("ttsempost_get_pair_sync", "ttsem", 2, "trisc2"),
  BenchSpec("ttsemget_post_pair_sync", "ttsem", 2, "trisc2"),
)

SPECS = BRISC_SPECS + TRISC_SPECS
SPEC_BY_NAME = {spec.name: spec for spec in SPECS}


@dataclass(frozen=True)
class Record:
  role: str
  test_id: int
  name: str
  group: str
  iterations: int
  ops_per_iter: int
  start: int
  end: int
  cycles: int
  sink: int
  blocking: bool

  @property
  def cycles_per_iter(self) -> float:
    return self.cycles / self.iterations


class BenchKernel(KernelBase, Cb, Noc, Tensix):
  pass


def tt_raw(inst) -> int:
  return inst.raw_word() if hasattr(inst, "raw_word") else int(inst) & 0xFFFFFFFF


def result_size() -> int:
  return HEADER_SIZE + len(SPECS) * RECORD_SIZE


def debug_ranges() -> tuple[DebugRange, ...]:
  return (
    DebugRange(0, "l1", RESULT_BASE, result_size(), "sem_cb_microbench_results"),
    DebugRange(1, "l1", CONTROL_BASE, 0x200, "sem_cb_microbench_control"),
  )


def emit_header(fw: KernelBase, *, iterations: int, status: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, len(SPECS), RECORD_WORDS, status, iterations, RESULT_BASE, result_size(), 0,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  return fw


def emit_record(fw: KernelBase, *, spec: BenchSpec, test_id: int, iterations: int, start_lo, start_hi, end_lo, end_hi, sink=s1):
  addr = RESULT_BASE + HEADER_SIZE + test_id * RECORD_SIZE
  role_id = 0 if spec.role == "brisc" else 4
  fw.li(s2, addr)
  for off, value in enumerate((
    RECORD_MAGIC, role_id, test_id, iterations, spec.ops_per_iter,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off, reg in enumerate((start_lo, start_hi, end_lo, end_hi, sink), start=5):
    fw.sw(reg, s2, off * 4)
  fw.li(t0, 1 if spec.blocking else 0)
  fw.sw(t0, s2, 10 * 4)
  fw.sw(zero, s2, 11 * 4)
  return fw


def emit_clear_results(fw: KernelBase):
  emit_header(fw, iterations=0, status=STATUS_STARTED)
  fw.li(t0, RESULT_BASE + HEADER_SIZE)
  fw.li(t1, len(SPECS) * RECORD_WORDS)
  clear = fw._new_label("clear_records")
  done = fw._new_label("clear_records_done")
  fw.label(clear)
  fw.beq(t1, zero, done)
  fw.sw(zero, t0, 0)
  fw.addi(t0, t0, 4)
  fw.addi(t1, t1, -1)
  fw.j(clear)
  fw.label(done)
  return fw


def emit_reset_cb(fw: BenchKernel, *, interface_base: int, cb_index: int, received: int = 0, acked: int = 0):
  iface = t6
  fw.cb_iface(interface_base, cb_index, out=iface)
  fw.lw(t0, iface, 0)
  fw.sw(t0, iface, 16)
  fw.sw(t0, iface, 20)
  fw.li(t0, ((received & 0xFFFF) << 16) | (acked & 0xFFFF))
  fw.sw(t0, iface, 24)
  fw.write32(CB.SYNC_TILES_RECEIVED_BASE + cb_index * CB.SYNC_STRIDE, received)
  fw.write32(CB.SYNC_TILES_ACKED_BASE + cb_index * CB.SYNC_STRIDE, acked)
  return fw.fence()


def emit_request_release(fw: BenchKernel, *, kind: int, delay: int, seq_reg=s8):
  fw.addi(seq_reg, seq_reg, 1)
  fw.write32(CTRL_DELAY, delay, tmp_addr=t0, tmp_val=t1)
  fw.write32(CTRL_KIND, kind, tmp_addr=t0, tmp_val=t1)
  fw.write32(CTRL_SEQ, seq_reg, tmp_addr=t0, tmp_val=t1)
  return fw.fence()


def emit_wait_release_done(fw: BenchKernel, *, seq_reg=s8):
  loop = fw._new_label("wait_release_done")
  done = fw._new_label("wait_release_done_done")
  fw.label(loop)
  fw.read32(t0, CTRL_DONE, tmp_addr=t1)
  fw.beq(t0, seq_reg, done)
  fw.fence()
  fw.j(loop)
  fw.label(done)
  return fw.fence()


def emit_empty_body(fw: BenchKernel):
  return fw.addi(s1, s1, 1)


def emit_release_signal_body(fw: BenchKernel, *, delay: int):
  emit_request_release(fw, kind=REQ_CB_RECEIVED, delay=delay)
  return emit_wait_release_done(fw)


def emit_brisc_body(fw: BenchKernel, spec: BenchSpec, *, iterations: int, delay: int):
  if spec.name == "empty":
    return emit_empty_body(fw)
  if spec.name == "release_signal":
    return emit_release_signal_body(fw, delay=delay)
  if spec.name == "cb_wait_front_ready":
    return fw.cb_wait_front(BM.CB_INTERFACE, CB_INDEX)
  if spec.name == "cb_wait_front_block":
    emit_reset_cb(fw, interface_base=BM.CB_INTERFACE, cb_index=CB_INDEX, received=0, acked=0)
    emit_request_release(fw, kind=REQ_CB_RECEIVED, delay=delay)
    fw.cb_wait_front(BM.CB_INTERFACE, CB_INDEX)
    return emit_wait_release_done(fw)
  if spec.name == "cb_reserve_back_ready":
    return fw.cb_reserve_back(BM.CB_INTERFACE, CB_INDEX)
  if spec.name == "cb_reserve_back_block":
    emit_reset_cb(fw, interface_base=BM.CB_INTERFACE, cb_index=CB_INDEX, received=CB_PAGES, acked=0)
    emit_request_release(fw, kind=REQ_CB_ACKED, delay=delay)
    fw.cb_reserve_back(BM.CB_INTERFACE, CB_INDEX)
    return emit_wait_release_done(fw)
  if spec.name == "cb_push_back":
    return fw.cb_push_back(BM.CB_INTERFACE, CB_INDEX)
  if spec.name == "cb_pop_front":
    return fw.cb_pop_front(BM.CB_INTERFACE, CB_INDEX)
  if spec.name == "noc_sem_set":
    fw.li(s4, NOC_SEM_ADDR)
    return fw.noc_semaphore_set(s4, 1)
  if spec.name == "noc_sem_wait_ready":
    fw.li(s4, NOC_SEM_ADDR)
    return fw.noc_semaphore_wait(s4, 1)
  if spec.name == "noc_sem_wait_block":
    fw.write32(NOC_SEM_ADDR, 0)
    emit_request_release(fw, kind=REQ_NOC_SEM_SET, delay=delay)
    fw.li(s4, NOC_SEM_ADDR)
    fw.noc_semaphore_wait(s4, 1)
    return emit_wait_release_done(fw)
  if spec.name == "noc_sem_inc_wait":
    fw.li(s4, NOC_SEM_ADDR)
    fw.local_noc0_coord(a5)
    fw.read32(s5, NOC.STATUS_BASE + NOC.NIU_MST_ATOMIC_RESP_RECEIVED, tmp_addr=t0)
    fw.addi(s5, s5, 1)
    fw.noc_semaphore_inc(0, 3, s4, a5, 1, ret_coord=a5, a=t0, v=t1)
    fw.noc_wait_atomic_responses(0, s5, addr=t0, val=t1)
    return fw
  raise ValueError(spec.name)


def emit_timed_brisc(fw: BenchKernel, *, spec: BenchSpec, test_id: int, iterations: int, delay: int):
  fw.li(s1, 0x5C0B0000 | test_id)
  if spec.name == "cb_wait_front_ready":
    emit_reset_cb(fw, interface_base=BM.CB_INTERFACE, cb_index=CB_INDEX, received=1, acked=0)
  elif spec.name == "cb_reserve_back_ready":
    emit_reset_cb(fw, interface_base=BM.CB_INTERFACE, cb_index=CB_INDEX, received=0, acked=0)
  elif spec.name in {"cb_push_back", "cb_pop_front"}:
    emit_reset_cb(fw, interface_base=BM.CB_INTERFACE, cb_index=CB_INDEX, received=iterations + 4, acked=0)
  elif spec.name == "noc_sem_wait_ready":
    fw.write32(NOC_SEM_ADDR, 1)
  harness.read_wall_clock(fw, a2, a3)
  fw.li(s0, iterations)
  loop = fw._new_label(f"bench_{spec.name}")
  done = fw._new_label(f"bench_{spec.name}_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  emit_brisc_body(fw, spec, iterations=iterations, delay=delay)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  harness.read_wall_clock(fw, a4, a5)
  emit_record(fw, spec=spec, test_id=test_id, iterations=iterations, start_lo=a2, start_hi=a3, end_lo=a4, end_hi=a5)
  return fw


def emit_tensix_sync(fw: BenchKernel):
  fw.write32(TensixRegs.PC_BUF_SYNC, 0, tmp_addr=t0, tmp_val=t1)
  fw.read32(s1, TensixRegs.PC_BUF_SYNC, tmp_addr=t0)
  return fw.and_(zero, zero, s1)


def emit_trisc_body(fw: BenchKernel, spec: BenchSpec, *, iterations: int):
  if spec.name == "trisc_empty":
    return fw.addi(s1, s1, 1)
  if spec.name == "cb_push_back_tensix_received":
    return fw.cb_push_back(fw.data["cb_interface"], CB_INDEX, tensix_received=True)
  if spec.name == "cb_pop_front_tensix_ack":
    return fw.cb_pop_front(fw.data["cb_interface"], CB_INDEX, tensix_ack=True)
  if spec.name == "ttsemwait_ready_sync":
    fw.emit(TTSEM_WAIT_READY)
    return emit_tensix_sync(fw)
  if spec.name == "ttsempost_get_pair_sync":
    fw.emit(TTSEM_POST)
    fw.emit(TTSEM_GET)
    return emit_tensix_sync(fw)
  if spec.name == "ttsemget_post_pair_sync":
    fw.emit(TTSEM_GET)
    fw.emit(TTSEM_POST)
    return emit_tensix_sync(fw)
  raise ValueError(spec.name)


def emit_timed_trisc(fw: BenchKernel, *, spec: BenchSpec, test_id: int, iterations: int):
  fw.li(s1, 0x5C0B0000 | test_id)
  if spec.name == "cb_push_back_tensix_received":
    emit_reset_cb(fw, interface_base=fw.data["cb_interface"], cb_index=CB_INDEX, received=iterations + 4, acked=0)
  elif spec.name == "cb_pop_front_tensix_ack":
    emit_reset_cb(fw, interface_base=fw.data["cb_interface"], cb_index=CB_INDEX, received=iterations + 4, acked=0)
  if spec.group == "ttsem":
    fw.emit(TTSEM_INIT_READY if spec.name == "ttsemwait_ready_sync" else TTSEM_INIT_GET)
    emit_tensix_sync(fw)
  harness.read_wall_clock(fw, a2, a3)
  fw.li(s0, iterations)
  loop = fw._new_label(f"bench_{spec.name}")
  done = fw._new_label(f"bench_{spec.name}_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  emit_trisc_body(fw, spec, iterations=iterations)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  harness.read_wall_clock(fw, a4, a5)
  emit_record(fw, spec=spec, test_id=test_id, iterations=iterations, start_lo=a2, start_hi=a3, end_lo=a4, end_hi=a5)
  return fw


def build_brisc(iterations: int, delay: int, *, skip_noc: bool) -> BenchKernel:
  fw = BenchKernel()
  emit_header(fw, iterations=iterations, status=STATUS_STARTED)
  fw.write32(CTRL_SEQ, 0)
  fw.write32(CTRL_KIND, REQ_NONE)
  fw.write32(CTRL_DELAY, delay)
  fw.write32(CTRL_DONE, 0)
  fw.li(s8, 0)
  for test_id, spec in enumerate(SPECS):
    if spec.role != "brisc":
      continue
    if skip_noc and spec.group == "noc_sem":
      continue
    emit_timed_brisc(fw, spec=spec, test_id=test_id, iterations=iterations, delay=delay)
  fw.write32(CTRL_KIND, REQ_STOP)
  fw.addi(s8, s8, 1)
  fw.write32(CTRL_SEQ, s8)
  emit_wait_release_done(fw)
  emit_header(fw, iterations=iterations, status=STATUS_DONE)
  return fw.ret()


def build_ncrisc_releaser() -> BenchKernel:
  fw = BenchKernel()
  fw.li(s7, 0)
  poll = fw._new_label("release_poll")
  stop = fw._new_label("release_stop")
  do_delay = fw._new_label("release_delay")
  delay_done = fw._new_label("release_delay_done")
  after = fw._new_label("release_after")
  cb_recv = fw._new_label("release_cb_received")
  cb_ack = fw._new_label("release_cb_acked")
  sem_set = fw._new_label("release_sem_set")
  fw.label(poll)
  fw.read32(s0, CTRL_SEQ, tmp_addr=t0)
  fw.beq(s0, s7, poll)
  fw.mv(s7, s0)
  fw.read32(s1, CTRL_KIND, tmp_addr=t0)
  fw.li(t1, REQ_STOP)
  fw.beq(s1, t1, stop)
  fw.read32(s2, CTRL_DELAY, tmp_addr=t0)
  fw.label(do_delay)
  fw.beq(s2, zero, delay_done)
  fw.addi(s2, s2, -1)
  fw.j(do_delay)
  fw.label(delay_done)
  fw.li(t1, REQ_CB_RECEIVED)
  fw.beq(s1, t1, cb_recv)
  fw.li(t1, REQ_CB_ACKED)
  fw.beq(s1, t1, cb_ack)
  fw.li(t1, REQ_NOC_SEM_SET)
  fw.beq(s1, t1, sem_set)
  fw.j(after)
  fw.label(cb_recv)
  fw.write32(CB.SYNC_TILES_RECEIVED_BASE + CB_INDEX * CB.SYNC_STRIDE, 1, tmp_addr=t0, tmp_val=t1)
  fw.j(after)
  fw.label(cb_ack)
  fw.write32(CB.SYNC_TILES_ACKED_BASE + CB_INDEX * CB.SYNC_STRIDE, 1, tmp_addr=t0, tmp_val=t1)
  fw.j(after)
  fw.label(sem_set)
  fw.write32(NOC_SEM_ADDR, 1, tmp_addr=t0, tmp_val=t1)
  fw.label(after)
  fw.write32(CTRL_DONE, s7, tmp_addr=t0, tmp_val=t1)
  fw.j(poll)
  fw.label(stop)
  fw.write32(CTRL_DONE, s7, tmp_addr=t0, tmp_val=t1)
  return fw.ret()


def build_trisc(iterations: int) -> BenchKernel:
  fw = BenchKernel()
  fw.data = {"cb_interface": 0xFFB00020}
  for test_id, spec in enumerate(SPECS):
    if spec.role == "trisc2":
      emit_timed_trisc(fw, spec=spec, test_id=test_id, iterations=iterations)
  return fw.ret()


def build_program(iterations: int, delay: int, *, skip_noc: bool) -> Program:
  empty = KernelBase()
  program = Program(
    brisc=build_brisc(iterations, delay, skip_noc=skip_noc),
    ncrisc=build_ncrisc_releaser(),
    trisc0=empty,
    trisc1=empty,
    trisc2=build_trisc(iterations),
    cbs=[(CB_INDEX, TILE_BYTES, CB_PAGES)],
    semaphores=4,
    num_cores=1,
  )
  program.name = "microbench_sem_cb"
  return program


def clear_results(device: Device, core: Core):
  with harness.device_window(device, core) as win:
    for item in debug_ranges():
      win.write(item.address, b"\0" * item.size)


def read_results(device: Device, core: Core) -> bytes:
  with harness.device_window(device, core) as win:
    blob = win.read(RESULT_BASE, result_size())
  if blob and all(b == 0xFF for b in blob):
    raise RuntimeError("L1 readback returned all 0xff; device is not responding cleanly")
  return blob


def parse_results(blob: bytes) -> list[Record]:
  header = struct.unpack_from("<" + "I" * HEADER_WORDS, blob, 0)
  if header[0] != RESULT_MAGIC:
    raise RuntimeError(f"bad result magic 0x{header[0]:08x}")
  records: list[Record] = []
  for test_id, spec in enumerate(SPECS):
    off = HEADER_SIZE + test_id * RECORD_SIZE
    words = struct.unpack_from("<" + "I" * RECORD_WORDS, blob, off)
    if words[0] == 0:
      continue
    if words[0] != RECORD_MAGIC:
      raise RuntimeError(f"{spec.name}: bad record magic 0x{words[0]:08x}")
    start = words[5] | (words[6] << 32)
    end = words[7] | (words[8] << 32)
    role = "brisc" if words[1] == 0 else "trisc2"
    records.append(Record(
      role=role,
      test_id=words[2],
      name=spec.name,
      group=spec.group,
      iterations=words[3],
      ops_per_iter=words[4],
      start=start,
      end=end,
      cycles=(end - start) & ((1 << 64) - 1),
      sink=words[9],
      blocking=bool(words[10]),
    ))
  return records


def _empty_for(records: list[Record], role: str) -> Record | None:
  name = "empty" if role == "brisc" else "trisc_empty"
  return next((r for r in records if r.name == name), None)


def format_table(records: list[Record]) -> str:
  lines = [
    "| role | test | group | mode | ops/iter | cycles | cyc/iter | adj cyc/op | sink |",
    "|---|---|---|---|---:|---:|---:|---:|---:|",
  ]
  for r in records:
    empty = _empty_for(records, r.role)
    adj = ""
    if empty is not None and r.ops_per_iter:
      adj = f"{((r.cycles_per_iter - empty.cycles_per_iter) / r.ops_per_iter):.3f}"
    mode = "blocking" if r.blocking else "ready"
    if r.group in {"baseline", "control"}:
      mode = r.group
    lines.append(
      f"| {r.role} | {r.name} | {r.group} | {mode} | {r.ops_per_iter} | {r.cycles} | "
      f"{r.cycles_per_iter:.3f} | {adj} | 0x{r.sink:08x} |"
    )
  return "\n".join(lines)


def proposed_constants(records: list[Record]) -> list[tuple[str, float, str]]:
  by_name = {r.name: r for r in records}

  def adj(name: str, empty_name: str) -> float | None:
    r = by_name.get(name)
    e = by_name.get(empty_name)
    if r is None or e is None or r.ops_per_iter == 0:
      return None
    return (r.cycles_per_iter - e.cycles_per_iter) / r.ops_per_iter

  candidates = (
    ("CB_WAIT_FRONT_READY_CYCLES", adj("cb_wait_front_ready", "empty"), "BRISC ready helper"),
    ("CB_RESERVE_BACK_READY_CYCLES", adj("cb_reserve_back_ready", "empty"), "BRISC ready helper"),
    ("CB_PUSH_BACK_CYCLES", adj("cb_push_back", "empty"), "BRISC helper"),
    ("CB_POP_FRONT_CYCLES", adj("cb_pop_front", "empty"), "BRISC helper"),
    ("NOC_SEM_SET_CYCLES", adj("noc_sem_set", "empty"), "local RISC helper"),
    ("NOC_SEM_WAIT_READY_CYCLES", adj("noc_sem_wait_ready", "empty"), "local RISC helper"),
    ("NOC_SEM_INC_WAIT_CYCLES", adj("noc_sem_inc_wait", "empty"), "local NOC atomic inc plus response wait"),
    ("CB_PUSH_BACK_TENSIX_RECEIVED_CYCLES", adj("cb_push_back_tensix_received", "trisc_empty"), "TRISC helper including Tensix received path"),
    ("CB_POP_FRONT_TENSIX_ACK_CYCLES", adj("cb_pop_front_tensix_ack", "trisc_empty"), "TRISC helper including Tensix ack path"),
    ("TTSEMWAIT_READY_SYNC_CYCLES", adj("ttsemwait_ready_sync", "trisc_empty"), "TTSEMWAIT plus per-iter PC_BUF_SYNC"),
  )
  out = [(name, value, note) for name, value, note in candidates if value is not None]
  pair = adj("ttsempost_get_pair_sync", "trisc_empty")
  if pair is not None:
    out.append(("TTSEMPOST_OR_GET_SYNC_PAIR_HALF_CYCLES", pair / 2.0, "half of TTSEMPOST+TTSEMGET pair with per-iter sync"))
  return out


def format_constants(records: list[Record]) -> str:
  rows = proposed_constants(records)
  if not rows:
    return "_No constants: benchmark did not produce matching rows._"
  lines = ["| constant | cycles | basis |", "|---|---:|---|"]
  for name, value, note in rows:
    lines.append(f"| `{name}` | {value:.1f} | {note} |")
  return "\n".join(lines)


def append_report(path: Path, *, command: str, core: Core, iterations: int, delay: int, records: list[Record], skip_noc: bool):
  now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
  with path.open("a", encoding="utf-8") as f:
    f.write(f"\n## Run {now}\n\n")
    f.write("Command:\n\n")
    f.write(f"```sh\n{command}\n```\n\n")
    f.write(f"- Core: logical `{core[0]},{core[1]}`\n")
    f.write(f"- Iterations per test: `{iterations}`\n")
    f.write(f"- Light contention release delay loop: `{delay}` NCRISC decrement iterations\n")
    f.write(f"- NOC semaphore rows skipped: `{skip_noc}`\n")
    f.write("- Dispatch path: slow dispatch (`TT_USB=1`), one worker core\n\n")
    f.write("Debug L1 ranges:\n")
    for item in debug_ranges():
      f.write(f"- `{item.name}` at `0x{item.address:x}` ({item.size} bytes)\n")
    f.write("\n")
    f.write(format_table(records))
    f.write("\n\nProposed constants for `examples/program_timing_model.py`:\n\n")
    f.write(format_constants(records))
    f.write("\n")


def shell_command(args: argparse.Namespace) -> str:
  parts = [
    "PYTHONPATH=.",
    "TT_USB=1",
    sys.executable,
    "microbenching/tensix/microbench_sem_cb.py",
    "--iters", str(args.iters),
    "--release-delay", str(args.release_delay),
  ]
  if args.core is not None:
    parts += ["--core", f"{args.core[0]},{args.core[1]}"]
  if args.skip_noc:
    parts.append("--skip-noc")
  if args.no_report:
    parts.append("--no-report")
  if args.report != harness.doc_path("tensix", "sem-cb-microbench.md"):
    parts += ["--report", str(args.report)]
  return " ".join(parts)


def main():
  parser = argparse.ArgumentParser(description="Focused Blackhole semaphore and circular-buffer control microbench.")
  parser.add_argument("--core", type=harness.parse_core, default=None, help="logical Tensix core X,Y; default: first program core")
  parser.add_argument("--iters", type=int, default=1000, help="iterations per timed loop")
  parser.add_argument("--release-delay", type=int, default=64, help="NCRISC delay-loop iterations before releasing blocking rows")
  parser.add_argument("--skip-noc", action="store_true", help="skip RISC NOC semaphore rows")
  parser.add_argument("--no-report", action="store_true", help="do not append markdown report")
  parser.add_argument("--report", type=Path, default=harness.doc_path("tensix", "sem-cb-microbench.md"), help="markdown report path")
  args = parser.parse_args()
  if args.iters <= 0:
    raise ValueError("--iters must be positive")
  if args.release_delay < 0:
    raise ValueError("--release-delay must be non-negative")

  with harness.open_device() as device:
    core = args.core or device.cores[0]
    clear_results(device, core)
    device.run(build_program(args.iters, args.release_delay, skip_noc=args.skip_noc))
    records = parse_results(read_results(device, core))

  print(format_table(records))
  print("\nProposed constants:")
  print(format_constants(records))
  if not args.no_report:
    append_report(
      args.report,
      command=shell_command(args),
      core=core,
      iterations=args.iters,
      delay=args.release_delay,
      records=records,
      skip_noc=args.skip_noc,
    )
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
