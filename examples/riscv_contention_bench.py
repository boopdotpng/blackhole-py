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

import riscv_core_bench as core
from asm import KernelBase
from device import Device
from dsl import (
  a0, a1, a2, a3, a4, a5,
  s0, s1, s2, s3, s4, s5, s6, s7, s8, s9,
  t0, t1, t2, t4, t5, t6, zero,
)
from pcie import TLBWindow
from program import Program
from ttk.debug import DebugRange
from ttk.noc import NOC
from ttk.tensix import TensixMMIO


ROLE_INDEX = core.ROLE_INDEX
ROLE_NAMES = core.ROLE_NAMES
ROLE_COUNT = len(ROLE_NAMES)

RESULT_BASE = 0x128000
CTRL_BASE = RESULT_BASE + 0x4000
SCRATCH_BASE = RESULT_BASE + 0x5000
LOCAL_LDM_BASE = 0xFFB00080
BRISC_LDM_WINDOW = 0xFFB14080
NCRISC_LDM_WINDOW = 0xFFB16080
TRISC0_LDM_WINDOW = 0xFFB18080
TRISC1_LDM_WINDOW = 0xFFB1A080
TRISC2_LDM_WINDOW = 0xFFB1C080

CTRL_START = CTRL_BASE
CTRL_READY = CTRL_BASE + 0x40
CTRL_DONE = CTRL_BASE + 0x80
CTRL_SIZE = 0x1000
SCRATCH_SIZE = 0x1000


HEADER_WORDS = 16
RECORD_WORDS = 12
HEADER_SIZE = HEADER_WORDS * 4
RECORD_SIZE = RECORD_WORDS * 4
RESULT_MAGIC = 0x5242434E  # "RBCN"
RECORD_MAGIC = 0x52424352  # "RBCR"
STATUS_STARTED = 0xC0010001
STATUS_DONE = 0xC001D00D


@dataclass(frozen=True)
class BenchSpec:
  name: str
  ops_per_iter: int
  kind: str


SPECS = (
  BenchSpec("empty", 0, "empty"),
  BenchSpec("mmio_wall_lw1", 1, "mmio_wall_lw1"),
  BenchSpec("mmio_noc_status_lw1", 1, "mmio_noc_status_lw1"),
  BenchSpec("l1_same_lw1", 1, "l1_same_lw1"),
  BenchSpec("l1_dist_lw1", 1, "l1_dist_lw1"),
  BenchSpec("l1_same_sw1", 1, "l1_same_sw1"),
  BenchSpec("l1_dist_sw1", 1, "l1_dist_sw1"),
  BenchSpec("l1_same_rmw2", 2, "l1_same_rmw2"),
  BenchSpec("ldm_self_lw1", 1, "ldm_self_lw1"),
  BenchSpec("ldm_self_sw1", 1, "ldm_self_sw1"),
  BenchSpec("xldm_brisc_lw1", 1, "xldm_brisc_lw1"),
  BenchSpec("xldm_ncrisc_lw1", 1, "xldm_ncrisc_lw1"),
  BenchSpec("xldm_trisc0_lw1", 1, "xldm_trisc0_lw1"),
  BenchSpec("xldm_trisc1_lw1", 1, "xldm_trisc1_lw1"),
  BenchSpec("xldm_trisc2_lw1", 1, "xldm_trisc2_lw1"),
  # All roles read the NEXT role's window in round-robin order.
  # brisc→ncrisc, ncrisc→trisc0, trisc0→trisc1, trisc1→trisc2, trisc2→brisc.
  BenchSpec("xldm_roundrobin_lw1", 1, "xldm_roundrobin_lw1"),
  # Owner role writes its own LDM while the other active roles read its window.
  # Measures write-side contention vs the read-only xldm_*_lw1 baselines.
  BenchSpec("xldm_contested_brisc_lw1", 1, "xldm_contested_brisc_lw1"),
  BenchSpec("xldm_contested_ncrisc_lw1", 1, "xldm_contested_ncrisc_lw1"),
  BenchSpec("xldm_contested_trisc0_lw1", 1, "xldm_contested_trisc0_lw1"),
  BenchSpec("xldm_contested_trisc1_lw1", 1, "xldm_contested_trisc1_lw1"),
  BenchSpec("xldm_contested_trisc2_lw1", 1, "xldm_contested_trisc2_lw1"),
  # 2-hop dependent load through BRISC's cross-LDM window.
  # LDM[16] is pre-seeded with 16; second load hits the same word (self-referential ptr).
  BenchSpec("xldm_ptr_chase_lw2", 2, "xldm_ptr_chase_lw2"),
)


@dataclass(frozen=True)
class Record:
  group: str
  active_mask: int
  role: str
  test_id: int
  name: str
  iterations: int
  ops_per_iter: int
  start: int
  end: int
  cycles: int
  sink: int


def result_size() -> int:
  return HEADER_SIZE + len(SPECS) * ROLE_COUNT * RECORD_SIZE


def debug_ranges() -> tuple[DebugRange, ...]:
  return (
    DebugRange(0, "l1", RESULT_BASE, result_size(), "riscv_contention_results"),
    DebugRange(1, "l1", CTRL_BASE, CTRL_SIZE, "riscv_contention_ctrl"),
    DebugRange(2, "l1", SCRATCH_BASE, SCRATCH_SIZE, "riscv_contention_scratch"),
  )


def role_mask(roles: list[str]) -> int:
  mask = 0
  for role in roles:
    mask |= 1 << ROLE_INDEX[role]
  return mask


def mask_roles(mask: int) -> list[str]:
  return [role for role in ROLE_NAMES if mask & (1 << ROLE_INDEX[role])]


def group_name(mask: int) -> str:
  return "+".join(mask_roles(mask))


def emit_header(fw: KernelBase, *, active_mask: int, iterations: int, status: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, 1, active_mask, len(SPECS), RECORD_WORDS, status, iterations,
    RESULT_BASE, CTRL_BASE, SCRATCH_BASE,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off in range(10, HEADER_WORDS):
    fw.sw(zero, s2, off * 4)
  return fw


def record_addr(role_id: int, test_id: int) -> int:
  slot = test_id * ROLE_COUNT + role_id
  return RESULT_BASE + HEADER_SIZE + slot * RECORD_SIZE


def emit_record(
  fw: KernelBase,
  *,
  role_id: int,
  active_mask: int,
  test_id: int,
  iterations: int,
  spec: BenchSpec,
  start_lo,
  start_hi,
  end_lo,
  end_hi,
  sink=s1,
):
  fw.li(s2, record_addr(role_id, test_id))
  for off, value in enumerate((
    RECORD_MAGIC,
    active_mask,
    role_id,
    test_id,
    iterations,
    spec.ops_per_iter,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off, reg in enumerate((start_lo, start_hi, end_lo, end_hi, sink), start=6):
    fw.sw(reg, s2, off * 4)
  fw.sw(zero, s2, 11 * 4)
  return fw


def emit_wait_word(fw: KernelBase, addr: int, value: int, *, actual=t0, expected=t1):
  fw.li(expected, value)
  loop = fw._new_label("wait_word")
  done = fw._new_label("wait_word_done")
  fw.label(loop)
  fw.read32(actual, addr)
  fw.beq(actual, expected, done)
  fw.fence()
  fw.j(loop)
  fw.label(done)
  return fw.fence()


def emit_wait_active_slots(fw: KernelBase, base: int, active_mask: int, phase: int):
  for role_id in range(ROLE_COUNT):
    if active_mask & (1 << role_id):
      emit_wait_word(fw, base + role_id * 4, phase)
  return fw


def emit_body(fw: KernelBase, kind: str, role_id: int = -1):
  if kind == "empty":
    return fw
  if kind == "mmio_wall_lw1":
    return fw.lw(s1, s5, 0)
  if kind == "mmio_noc_status_lw1":
    return fw.lw(s1, s8, 0)
  if kind == "l1_same_lw1":
    return fw.lw(s1, s3, 0)
  if kind == "l1_dist_lw1":
    return fw.lw(s1, s2, 0)
  if kind == "l1_same_sw1":
    return fw.sw(s1, s3, 4)
  if kind == "l1_dist_sw1":
    return fw.sw(s1, s2, 4)
  if kind == "l1_same_rmw2":
    fw.lw(a0, s3, 8)
    return fw.sw(a0, s3, 8)
  if kind == "ldm_self_lw1":
    return fw.lw(s1, s6, 0)
  if kind == "ldm_self_sw1":
    return fw.sw(s1, s6, 4)
  if kind == "xldm_brisc_lw1":
    return fw.lw(s1, s7, 0)
  if kind == "xldm_ncrisc_lw1":
    return fw.lw(s1, t4, 0)
  if kind == "xldm_trisc0_lw1":
    return fw.lw(s1, t5, 0)
  if kind == "xldm_trisc1_lw1":
    return fw.lw(s1, t6, 0)
  if kind == "xldm_trisc2_lw1":
    return fw.lw(s1, s9, 0)
  # Round-robin: each role reads the next role's window.
  # brisc(0)→ncrisc(t4), ncrisc(1)→trisc0(t5), trisc0(2)→trisc1(t6),
  # trisc1(3)→trisc2(s9), trisc2(4)→brisc(s7).
  if kind == "xldm_roundrobin_lw1":
    rr_regs = (t4, t5, t6, s9, s7)
    return fw.lw(s1, rr_regs[role_id], 0)
  # Contested: owner writes own LDM; other active roles read owner's window.
  # Compares write-side cost vs read-only xldm_*_lw1 baselines under contention.
  if kind == "xldm_contested_brisc_lw1":
    return fw.sw(s1, s6, 4) if role_id == 0 else fw.lw(s1, s7, 0)
  if kind == "xldm_contested_ncrisc_lw1":
    return fw.sw(s1, s6, 4) if role_id == 1 else fw.lw(s1, t4, 0)
  if kind == "xldm_contested_trisc0_lw1":
    return fw.sw(s1, s6, 4) if role_id == 2 else fw.lw(s1, t5, 0)
  if kind == "xldm_contested_trisc1_lw1":
    return fw.sw(s1, s6, 4) if role_id == 3 else fw.lw(s1, t6, 0)
  if kind == "xldm_contested_trisc2_lw1":
    return fw.sw(s1, s6, 4) if role_id == 4 else fw.lw(s1, s9, 0)
  # 2-hop dependent load through BRISC's cross-LDM window.
  # emit_setup_for_phase seeds LDM[16]=16 so the second load hits the same word.
  if kind == "xldm_ptr_chase_lw2":
    fw.lw(t2, s7, 0x10)      # t2 = BRISC_LDM[16] = 16
    fw.add(t2, s7, t2)       # t2 = BRISC_window_base + 16
    return fw.lw(s1, t2, 0)  # s1 = BRISC_LDM[16] again (data-dependent 2nd load)
  raise ValueError(f"unknown contention benchmark body {kind!r}")


def emit_setup_for_phase(fw: KernelBase, *, role_id: int):
  role_tag = 0xC0000000 | (role_id << 24)
  fw.li(s1, role_tag | 0x1234)
  fw.li(s3, SCRATCH_BASE)
  fw.li(s2, SCRATCH_BASE + 0x100 + role_id * 0x40)
  fw.sw(s1, s3, 0)
  fw.sw(s1, s3, 4)
  fw.sw(s1, s3, 8)
  fw.sw(s1, s2, 0)
  fw.sw(s1, s2, 4)
  fw.li(s5, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L)
  fw.li(s8, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
  fw.li(s6, LOCAL_LDM_BASE)
  fw.sw(s1, s6, 0)
  fw.sw(s1, s6, 4)
  fw.li(t2, 0x10)
  fw.sw(t2, s6, 0x10)  # seed for xldm_ptr_chase_lw2: LDM[16]=16 (self-referential ptr)
  fw.li(s7, BRISC_LDM_WINDOW)
  fw.li(t4, NCRISC_LDM_WINDOW)
  fw.li(t5, TRISC0_LDM_WINDOW)
  fw.li(t6, TRISC1_LDM_WINDOW)
  fw.li(s9, TRISC2_LDM_WINDOW)
  return fw


def emit_timed_payload(
  fw: KernelBase,
  *,
  role_id: int,
  active_mask: int,
  test_id: int,
  iterations: int,
  spec: BenchSpec,
):
  core.read_wall_clock(fw, a2, a3)
  fw.li(s0, iterations)
  loop = fw._new_label(f"bench_{spec.kind}")
  done = fw._new_label(f"bench_{spec.kind}_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  emit_body(fw, spec.kind, role_id)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  core.read_wall_clock(fw, a4, a5)
  emit_record(
    fw,
    role_id=role_id,
    active_mask=active_mask,
    test_id=test_id,
    iterations=iterations,
    spec=spec,
    start_lo=a2,
    start_hi=a3,
    end_lo=a4,
    end_hi=a5,
  )
  return fw


def emit_worker_phase(
  fw: KernelBase,
  *,
  role_id: int,
  active_mask: int,
  test_id: int,
  iterations: int,
  spec: BenchSpec,
):
  phase = test_id + 1
  emit_setup_for_phase(fw, role_id=role_id)
  fw.write32(CTRL_READY + role_id * 4, phase)
  emit_wait_word(fw, CTRL_START, phase)
  emit_timed_payload(
    fw,
    role_id=role_id,
    active_mask=active_mask,
    test_id=test_id,
    iterations=iterations,
    spec=spec,
  )
  fw.write32(CTRL_DONE + role_id * 4, phase)
  return fw


def emit_controller_phase(
  fw: KernelBase,
  *,
  active_mask: int,
  test_id: int,
  iterations: int,
  spec: BenchSpec,
):
  phase = test_id + 1
  brisc_active = bool(active_mask & 1)
  if brisc_active:
    emit_setup_for_phase(fw, role_id=0)
    fw.write32(CTRL_READY, phase)
  emit_wait_active_slots(fw, CTRL_READY, active_mask, phase)
  fw.write32(CTRL_START, phase)
  if brisc_active:
    emit_timed_payload(
      fw,
      role_id=0,
      active_mask=active_mask,
      test_id=test_id,
      iterations=iterations,
      spec=spec,
    )
    fw.write32(CTRL_DONE, phase)
  emit_wait_active_slots(fw, CTRL_DONE, active_mask, phase)
  return fw


def build_role_kernel(role: str, active_mask: int, iterations: int) -> KernelBase:
  role_id = ROLE_INDEX[role]
  fw = KernelBase()
  if role == "brisc":
    fw.zero_word_range(CTRL_BASE, CTRL_BASE + CTRL_SIZE)
    emit_header(fw, active_mask=active_mask, iterations=iterations, status=STATUS_STARTED)
    for test_id, spec in enumerate(SPECS):
      emit_controller_phase(
        fw,
        active_mask=active_mask,
        test_id=test_id,
        iterations=iterations,
        spec=spec,
      )
    emit_header(fw, active_mask=active_mask, iterations=iterations, status=STATUS_DONE)
    return fw.ret()
  if not (active_mask & (1 << role_id)):
    return fw.ret()
  for test_id, spec in enumerate(SPECS):
    emit_worker_phase(
      fw,
      role_id=role_id,
      active_mask=active_mask,
      test_id=test_id,
      iterations=iterations,
      spec=spec,
    )
  return fw.ret()


def build_program(active_mask: int, iterations: int) -> Program:
  kernels = {
    role: build_role_kernel(role, active_mask, iterations)
    for role in ROLE_NAMES
  }
  program = Program(**kernels, num_cores=1)
  program.name = f"riscv_contention_bench:{group_name(active_mask)}"
  return program


def read_results(device: Device, target_core: tuple[int, int]) -> bytes:
  result_range = debug_ranges()[0]
  device.dev.set_power_state(True)
  try:
    with TLBWindow(device.dev, start=target_core) as win:
      blob = win.read(result_range.address, result_range.size)
  finally:
    device.dev.set_power_state(False)
  if blob and all(b == 0xFF for b in blob):
    raise RuntimeError("L1 readback returned all 0xff; device is not responding cleanly and likely needs a host reboot")
  return blob


def clear_ranges(device: Device, target_core: tuple[int, int]):
  device.dev.set_power_state(True)
  try:
    with TLBWindow(device.dev, start=target_core) as win:
      for item in debug_ranges():
        win.write(item.address, b"\0" * item.size)
  finally:
    device.dev.set_power_state(False)


def parse_results(blob: bytes, group: str) -> list[Record]:
  header = struct.unpack_from("<" + "I" * HEADER_WORDS, blob, 0)
  if header[0] != RESULT_MAGIC:
    raise RuntimeError(f"{group}: bad result magic 0x{header[0]:08x}")
  if header[5] != STATUS_DONE:
    raise RuntimeError(f"{group}: benchmark did not finish, status=0x{header[5]:08x}")
  active_mask = header[2]
  records = []
  for test_id, spec in enumerate(SPECS):
    for role_id, role in enumerate(ROLE_NAMES):
      if not (active_mask & (1 << role_id)):
        continue
      off = HEADER_SIZE + (test_id * ROLE_COUNT + role_id) * RECORD_SIZE
      words = struct.unpack_from("<" + "I" * RECORD_WORDS, blob, off)
      if words[0] != RECORD_MAGIC:
        raise RuntimeError(f"{group}/{role}/{spec.name}: bad record magic 0x{words[0]:08x}")
      start = words[6] | (words[7] << 32)
      end = words[8] | (words[9] << 32)
      records.append(Record(
        group=group,
        active_mask=active_mask,
        role=role,
        test_id=words[3],
        name=spec.name,
        iterations=words[4],
        ops_per_iter=words[5],
        start=start,
        end=end,
        cycles=(end - start) & ((1 << 64) - 1),
        sink=words[10],
      ))
  return records


def format_table(records: list[Record]) -> str:
  by_group_role = {}
  for record in records:
    by_group_role.setdefault((record.group, record.role), {})[record.name] = record
  lines = [
    "| group | role | test | cycles | cyc/iter | adj cyc/op | sink |",
    "|---|---|---:|---:|---:|---:|---:|",
  ]
  for group in dict.fromkeys(r.group for r in records):
    for role in ROLE_NAMES:
      role_records = by_group_role.get((group, role))
      if not role_records:
        continue
      empty = role_records["empty"]
      empty_cpi = empty.cycles / empty.iterations
      for spec in SPECS:
        r = role_records[spec.name]
        cpi = r.cycles / r.iterations
        if r.ops_per_iter:
          baseline = empty_cpi * r.iterations
          adj = (r.cycles - baseline) / (r.iterations * r.ops_per_iter)
          adj_text = f"{adj:.3f}"
        else:
          adj_text = ""
        lines.append(
          f"| {group} | {role} | {r.name} | {r.cycles} | {cpi:.3f} | {adj_text} | 0x{r.sink:08x} |"
        )
  return "\n".join(lines)


def append_report(
  path: Path,
  *,
  target_core: tuple[int, int],
  iterations: int,
  group_preset: str,
  fresh_device_per_group: bool,
  records: list[Record],
):
  now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
  with path.open("a", encoding="utf-8") as f:
    f.write(f"\n## Run {now}\n\n")
    f.write(f"- Core: logical `{target_core[0]},{target_core[1]}`\n")
    f.write(f"- Iterations per test: `{iterations}`\n")
    f.write("- Dispatch path: slow dispatch (`TT_USB=1`)\n")
    f.write(f"- Group preset: {group_preset}\n")
    f.write(f"- Device lifetime: {'fresh per group' if fresh_device_per_group else 'single session'}\n")
    f.write("- Groups: " + ", ".join(dict.fromkeys(r.group for r in records)) + "\n\n")
    f.write("Debug L1 ranges:\n")
    for item in debug_ranges():
      f.write(f"- `{item.name}` at `0x{item.address:x}` ({item.size} bytes)\n")
    f.write("\n")
    f.write(format_table(records))
    f.write("\n")


def parse_group(text: str) -> int:
  aliases = {
    "all": ROLE_NAMES,
    "none": [],
  }
  if text in aliases:
    roles = list(aliases[text])
  else:
    roles = text.split("+") if "+" in text else text.split(",")
  roles = [role.strip() for role in roles if role.strip()]
  if not roles:
    raise argparse.ArgumentTypeError("group must contain at least one role")
  unknown = [role for role in roles if role not in ROLE_INDEX]
  if unknown:
    raise argparse.ArgumentTypeError(f"unknown role(s): {', '.join(unknown)}")
  return role_mask(roles)


def all_pair_groups() -> list[int]:
  singles = [role_mask([r]) for r in ROLE_NAMES]
  # Full role-pair matrix: all C(5,2)=10 two-role combinations.
  pairs = [
    role_mask([r1, r2])
    for i, r1 in enumerate(ROLE_NAMES)
    for r2 in ROLE_NAMES[i + 1:]
  ]
  all_five = role_mask(list(ROLE_NAMES))
  return singles + pairs + [all_five]


def default_groups() -> list[int]:
  singles = [role_mask([r]) for r in ROLE_NAMES]
  representative_pairs = [
    role_mask(["brisc", "ncrisc"]),
    role_mask(["brisc", "trisc0"]),
  ]
  all_five = role_mask(list(ROLE_NAMES))
  return singles + representative_pairs + [all_five]


def run_group(
  *,
  active_mask: int,
  iterations: int,
  requested_core: tuple[int, int] | None,
) -> tuple[tuple[int, int], list[Record]]:
  device = Device()
  try:
    target_core = requested_core or device.cores[0]
    clear_ranges(device, target_core)
    device.run(build_program(active_mask, iterations))
    group = group_name(active_mask)
    return target_core, parse_results(read_results(device, target_core), group)
  finally:
    device.close()


def main():
  parser = argparse.ArgumentParser(description="Microbenchmark simultaneous Blackhole Tensix RISC-V contention.")
  parser.add_argument("--core", type=core.parse_core, default=None, help="logical Tensix core X,Y; default: first program core")
  group_selector = parser.add_mutually_exclusive_group()
  group_selector.add_argument("--groups", nargs="+", type=parse_group, default=None, help="active role groups, e.g. all brisc+ncrisc trisc0")
  group_selector.add_argument("--all-pairs", action="store_true", help="run the full 16-group matrix: solos, all C(5,2) pairs, and all five roles")
  parser.add_argument("--iters", type=int, default=10_000, help="iterations per timed loop")
  parser.add_argument("--fresh-device-per-group", action="store_true", help="open and close Device() around every group to avoid stale launch state in long sweeps")
  parser.add_argument("--no-report", action="store_true", help="do not append results to docs/riscv-contention-microbench.md")
  parser.add_argument("--report", type=Path, default=Path("docs/riscv-contention-microbench.md"), help="markdown report path")
  args = parser.parse_args()
  if args.iters <= 0:
    raise ValueError("--iters must be positive")

  if args.groups is not None:
    groups = list(dict.fromkeys(args.groups))
    group_preset = "custom `--groups`"
  elif args.all_pairs:
    groups = all_pair_groups()
    group_preset = "full pair matrix (`--all-pairs`)"
  else:
    groups = default_groups()
    group_preset = "representative default"

  os.environ.setdefault("TT_USB", "1")
  all_records: list[Record] = []
  target_core: tuple[int, int] | None = None
  fresh_device_per_group = args.fresh_device_per_group or (args.all_pairs and args.groups is None)

  if fresh_device_per_group:
    for active_mask in groups:
      group_core, records = run_group(
        active_mask=active_mask,
        iterations=args.iters,
        requested_core=args.core,
      )
      if target_core is None:
        target_core = group_core
      all_records.extend(records)
  else:
    device = Device()
    try:
      target_core = args.core or device.cores[0]
      for active_mask in groups:
        clear_ranges(device, target_core)
        device.run(build_program(active_mask, args.iters))
        group = group_name(active_mask)
        all_records.extend(parse_results(read_results(device, target_core), group))
    finally:
      device.close()

  if target_core is None:
    raise RuntimeError("no groups selected")

  print(format_table(all_records))
  if not args.no_report:
    append_report(
      args.report,
      target_core=target_core,
      iterations=args.iters,
      group_preset=group_preset,
      fresh_device_per_group=fresh_device_per_group,
      records=all_records,
    )
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
