#!/usr/bin/env python3
"""RISC-V clone trace probes for shared-resource/contention modeling.

This complements the older core/memory/contention benches with Verilator-facing
scenarios: L1 stride/bank pressure, role-specific victim/aggressor mixes,
same-address producer/consumer pressure, and instruction-footprint pressure.
It intentionally stays inside RISC-V/L1/LDM/MMIO paths and does not touch the
known quarantined Tensix readback/mover paths.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
import riscv_core_bench as core  # noqa: E402
from asm import KernelBase
from device import Device
from dsl import (
  a0, a1, a2, a3, a4, a5,
  s0, s1, s2, s3, s4, s5, s6, s7, s8, s9,
  t0, t1, t2, t4, t5, t6, zero,
)
from program import Program
from ttk.debug import DebugRange
from ttk.noc import NOC
from ttk.tensix import TensixMMIO


ROLE_INDEX = core.ROLE_INDEX
ROLE_NAMES = core.ROLE_NAMES
ROLE_COUNT = len(ROLE_NAMES)

RESULT_BASE = 0x130000
CTRL_BASE = RESULT_BASE + 0x5000
SCRATCH_BASE = RESULT_BASE + 0x6000
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
SCRATCH_SIZE = 0x2000

HEADER_WORDS = 16
RECORD_WORDS = 14
HEADER_SIZE = HEADER_WORDS * 4
RECORD_SIZE = RECORD_WORDS * 4
RESULT_MAGIC = 0x52435654  # "RCVT"
RECORD_MAGIC = 0x52435652  # "RCVR"
STATUS_STARTED = 0xC10A0001
STATUS_DONE = 0xC10AD00D


@dataclass(frozen=True)
class Scenario:
  name: str
  suite: str
  body: str
  ops_per_iter: int
  param: int = 0
  description: str = ""


SCENARIOS: tuple[Scenario, ...] = (
  Scenario("empty", "base", "empty", 0, description="loop overhead baseline"),
  Scenario("l1_lw_stride0", "l1", "l1_lw_stride", 1, 0, "all roles load same L1 word"),
  Scenario("l1_lw_stride4", "l1", "l1_lw_stride", 1, 4, "roles load adjacent words"),
  Scenario("l1_lw_stride64", "l1", "l1_lw_stride", 1, 64, "roles load 64B-spaced words"),
  Scenario("l1_lw_stride128", "l1", "l1_lw_stride", 1, 128, "roles load 128B-spaced words"),
  Scenario("l1_lw_stride256", "l1", "l1_lw_stride", 1, 256, "roles load 256B-spaced words"),
  Scenario("l1_lw_stride2048", "l1", "l1_lw_stride", 1, 2048, "roles load 2KiB-spaced words"),
  Scenario("l1_sw_stride0", "l1", "l1_sw_stride", 1, 0, "all roles store same L1 word"),
  Scenario("l1_sw_stride64", "l1", "l1_sw_stride", 1, 64, "roles store 64B-spaced words"),
  Scenario("l1_sw_stride2048", "l1", "l1_sw_stride", 1, 2048, "roles store 2KiB-spaced words"),
  Scenario("l1_rmw_stride0", "l1", "l1_rmw_stride", 2, 0, "all roles load+store same L1 word"),
  Scenario("l1_rmw_stride64", "l1", "l1_rmw_stride", 2, 64, "roles load+store 64B-spaced words"),
  Scenario("same_word_writer_readers", "producer", "same_word_writer_readers", 1, 0,
           "BRISC stores a shared word while other roles load it"),
  Scenario("victim_l1_dep_vs_l1_load", "mixed", "victim_l1_dep_vs_l1_load", 1, 0,
           "BRISC dependent L1-load victim; other roles independent L1 loads"),
  Scenario("victim_l1_dep_vs_l1_store", "mixed", "victim_l1_dep_vs_l1_store", 1, 0,
           "BRISC dependent L1-load victim; other roles L1 stores"),
  Scenario("victim_l1_dep_vs_mmio_wall", "mixed", "victim_l1_dep_vs_mmio_wall", 1, 0,
           "BRISC dependent L1-load victim; other roles wall-clock MMIO loads"),
  Scenario("victim_l1_dep_vs_xldm_brisc", "mixed", "victim_l1_dep_vs_xldm_brisc", 1, 0,
           "BRISC dependent L1-load victim; other roles read BRISC cross-LDM window"),
  Scenario("ifetch_addi8", "ifetch", "ifetch_addi", 8, 8, "small unrolled integer body"),
  Scenario("ifetch_addi64", "ifetch", "ifetch_addi", 64, 64, "medium unrolled integer body"),
  Scenario("ifetch_addi256", "ifetch", "ifetch_addi", 256, 256, "large safe unrolled integer body"),
  Scenario("ifetch_victim256_vs_l1_load", "ifetch", "ifetch_victim_vs_l1_load", 1, 0,
           "BRISC runs 256-addi footprint; other roles do L1 loads"),
)

SUITES = {
  "quick": {"base", "l1", "mixed"},
  "full": {"base", "l1", "producer", "mixed", "ifetch"},
  "l1": {"base", "l1"},
  "producer": {"base", "producer"},
  "mixed": {"base", "mixed"},
  "ifetch": {"base", "ifetch"},
}


@dataclass(frozen=True)
class Record:
  group: str
  active_mask: int
  role: str
  scenario: str
  suite: str
  iterations: int
  ops_per_iter: int
  param: int
  start: int
  end: int
  cycles: int
  sink: int


def result_size(scenarios: tuple[Scenario, ...]) -> int:
  return HEADER_SIZE + len(scenarios) * ROLE_COUNT * RECORD_SIZE


def debug_ranges(scenarios: tuple[Scenario, ...] = SCENARIOS) -> tuple[DebugRange, ...]:
  return (
    DebugRange(0, "l1", RESULT_BASE, result_size(scenarios), "riscv_clone_trace_results"),
    DebugRange(1, "l1", CTRL_BASE, CTRL_SIZE, "riscv_clone_trace_ctrl"),
    DebugRange(2, "l1", SCRATCH_BASE, SCRATCH_SIZE, "riscv_clone_trace_scratch"),
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


def emit_header(fw: KernelBase, *, active_mask: int, iterations: int,
                scenario_count: int, status: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, 1, active_mask, scenario_count, RECORD_WORDS, status,
    iterations, RESULT_BASE, CTRL_BASE, SCRATCH_BASE,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off in range(10, HEADER_WORDS):
    fw.sw(zero, s2, off * 4)
  return fw


def record_addr(scenario_id: int, role_id: int) -> int:
  slot = scenario_id * ROLE_COUNT + role_id
  return RESULT_BASE + HEADER_SIZE + slot * RECORD_SIZE


def emit_record(
  fw: KernelBase,
  *,
  role_id: int,
  active_mask: int,
  scenario_id: int,
  iterations: int,
  scenario: Scenario,
  start_lo,
  start_hi,
  end_lo,
  end_hi,
  sink=s1,
):
  fw.li(s2, record_addr(scenario_id, role_id))
  for off, value in enumerate((
    RECORD_MAGIC,
    active_mask,
    role_id,
    scenario_id,
    iterations,
    scenario.ops_per_iter,
    scenario.param,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off, reg in enumerate((start_lo, start_hi, end_lo, end_hi, sink), start=7):
    fw.sw(reg, s2, off * 4)
  fw.sw(zero, s2, 12 * 4)
  fw.sw(zero, s2, 13 * 4)
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


def emit_setup_for_phase(fw: KernelBase, *, role_id: int, scenario: Scenario):
  role_tag = 0xD0000000 | (role_id << 24)
  stride_addr = SCRATCH_BASE + 0x400 + role_id * scenario.param
  distinct_addr = SCRATCH_BASE + 0x100 + role_id * 0x40

  fw.li(s1, role_tag | 0x1234)
  fw.li(s3, SCRATCH_BASE)
  fw.li(s2, distinct_addr)
  fw.li(s4, stride_addr)
  fw.li(s5, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L)
  fw.li(s8, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
  fw.li(s6, LOCAL_LDM_BASE)
  fw.li(s7, BRISC_LDM_WINDOW)
  fw.li(t4, NCRISC_LDM_WINDOW)
  fw.li(t5, TRISC0_LDM_WINDOW)
  fw.li(t6, TRISC1_LDM_WINDOW)
  fw.li(s9, TRISC2_LDM_WINDOW)

  for off in range(0, 0x80, 4):
    fw.sw(s1, s3, off)
  for off in range(0, 0x20, 4):
    fw.sw(s1, s2, off)
    fw.sw(s1, s4, off)
    fw.sw(s1, s6, off)
  fw.sw(s3, s3, 0)  # dependent L1 pointer-chase target points to itself.
  fw.sw(s1, s3, 4)
  return fw


def emit_ifetch_addi(fw: KernelBase, count: int):
  for _ in range(count):
    fw.addi(s1, s1, 1)
  return fw


def emit_body(fw: KernelBase, scenario: Scenario, role_id: int):
  body = scenario.body
  if body == "empty":
    return fw
  if body == "l1_lw_stride":
    return fw.lw(s1, s4, 0)
  if body == "l1_sw_stride":
    return fw.sw(s1, s4, 4)
  if body == "l1_rmw_stride":
    fw.lw(a0, s4, 8)
    return fw.sw(a0, s4, 8)
  if body == "same_word_writer_readers":
    return fw.sw(s1, s3, 4) if role_id == 0 else fw.lw(s1, s3, 4)
  if body == "victim_l1_dep_vs_l1_load":
    return fw.lw(s3, s3, 0) if role_id == 0 else fw.lw(s1, s4, 0)
  if body == "victim_l1_dep_vs_l1_store":
    return fw.lw(s3, s3, 0) if role_id == 0 else fw.sw(s1, s4, 4)
  if body == "victim_l1_dep_vs_mmio_wall":
    return fw.lw(s3, s3, 0) if role_id == 0 else fw.lw(s1, s5, 0)
  if body == "victim_l1_dep_vs_xldm_brisc":
    return fw.lw(s3, s3, 0) if role_id == 0 else fw.lw(s1, s7, 0)
  if body == "ifetch_addi":
    return emit_ifetch_addi(fw, scenario.param)
  if body == "ifetch_victim_vs_l1_load":
    return emit_ifetch_addi(fw, 256) if role_id == 0 else fw.lw(s1, s4, 0)
  raise ValueError(f"unknown clone-trace body {body!r}")


def emit_timed_payload(
  fw: KernelBase,
  *,
  role_id: int,
  active_mask: int,
  scenario_id: int,
  iterations: int,
  scenario: Scenario,
):
  core.read_wall_clock(fw, a2, a3)
  fw.li(s0, iterations)
  loop = fw._new_label(f"bench_{scenario.name}")
  done = fw._new_label(f"bench_{scenario.name}_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  emit_body(fw, scenario, role_id)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  core.read_wall_clock(fw, a4, a5)
  emit_record(
    fw,
    role_id=role_id,
    active_mask=active_mask,
    scenario_id=scenario_id,
    iterations=iterations,
    scenario=scenario,
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
  scenario_id: int,
  iterations: int,
  scenario: Scenario,
):
  phase = scenario_id + 1
  emit_setup_for_phase(fw, role_id=role_id, scenario=scenario)
  fw.write32(CTRL_READY + role_id * 4, phase)
  emit_wait_word(fw, CTRL_START, phase)
  emit_timed_payload(
    fw,
    role_id=role_id,
    active_mask=active_mask,
    scenario_id=scenario_id,
    iterations=iterations,
    scenario=scenario,
  )
  fw.write32(CTRL_DONE + role_id * 4, phase)
  return fw


def emit_controller_phase(
  fw: KernelBase,
  *,
  active_mask: int,
  scenario_id: int,
  iterations: int,
  scenario: Scenario,
):
  phase = scenario_id + 1
  brisc_active = bool(active_mask & 1)
  if brisc_active:
    emit_setup_for_phase(fw, role_id=0, scenario=scenario)
    fw.write32(CTRL_READY, phase)
  emit_wait_active_slots(fw, CTRL_READY, active_mask, phase)
  fw.write32(CTRL_START, phase)
  if brisc_active:
    emit_timed_payload(
      fw,
      role_id=0,
      active_mask=active_mask,
      scenario_id=scenario_id,
      iterations=iterations,
      scenario=scenario,
    )
    fw.write32(CTRL_DONE, phase)
  emit_wait_active_slots(fw, CTRL_DONE, active_mask, phase)
  return fw


def build_role_kernel(
  role: str,
  active_mask: int,
  iterations: int,
  scenarios: tuple[Scenario, ...],
) -> KernelBase:
  role_id = ROLE_INDEX[role]
  fw = KernelBase()
  if role == "brisc":
    fw.zero_word_range(CTRL_BASE, CTRL_BASE + CTRL_SIZE)
    emit_header(
      fw,
      active_mask=active_mask,
      iterations=iterations,
      scenario_count=len(scenarios),
      status=STATUS_STARTED,
    )
    for scenario_id, scenario in enumerate(scenarios):
      emit_controller_phase(
        fw,
        active_mask=active_mask,
        scenario_id=scenario_id,
        iterations=iterations,
        scenario=scenario,
      )
    emit_header(
      fw,
      active_mask=active_mask,
      iterations=iterations,
      scenario_count=len(scenarios),
      status=STATUS_DONE,
    )
    return fw.ret()
  if not (active_mask & (1 << role_id)):
    return fw.ret()
  for scenario_id, scenario in enumerate(scenarios):
    emit_worker_phase(
      fw,
      role_id=role_id,
      active_mask=active_mask,
      scenario_id=scenario_id,
      iterations=iterations,
      scenario=scenario,
    )
  return fw.ret()


def build_program(active_mask: int, iterations: int, scenarios: tuple[Scenario, ...]) -> Program:
  kernels = {
    role: build_role_kernel(role, active_mask, iterations, scenarios)
    for role in ROLE_NAMES
  }
  program = Program(**kernels, num_cores=1)
  program.name = f"riscv_clone_trace:{group_name(active_mask)}"
  return program


def read_results(device: Device, target_core: tuple[int, int], scenarios: tuple[Scenario, ...]) -> bytes:
  result_range = debug_ranges(scenarios)[0]
  with harness.device_window(device, target_core) as win:
    blob = win.read(result_range.address, result_range.size)
  if blob and all(b == 0xFF for b in blob):
    raise RuntimeError(harness.ALL_FF_ERROR)
  return blob


def clear_ranges(device: Device, target_core: tuple[int, int], scenarios: tuple[Scenario, ...]):
  with harness.device_window(device, target_core) as win:
    for item in debug_ranges(scenarios):
      win.write(item.address, b"\0" * item.size)


def parse_results(blob: bytes, group: str, scenarios: tuple[Scenario, ...]) -> list[Record]:
  header = struct.unpack_from("<" + "I" * HEADER_WORDS, blob, 0)
  if header[0] != RESULT_MAGIC:
    raise RuntimeError(f"{group}: bad result magic 0x{header[0]:08x}")
  if header[5] != STATUS_DONE:
    raise RuntimeError(f"{group}: benchmark did not finish, status=0x{header[5]:08x}")
  active_mask = header[2]
  scenario_count = header[3]
  if scenario_count != len(scenarios):
    raise RuntimeError(f"{group}: scenario count mismatch {scenario_count} != {len(scenarios)}")
  records = []
  for scenario_id, scenario in enumerate(scenarios):
    for role_id, role in enumerate(ROLE_NAMES):
      if not (active_mask & (1 << role_id)):
        continue
      off = HEADER_SIZE + (scenario_id * ROLE_COUNT + role_id) * RECORD_SIZE
      words = struct.unpack_from("<" + "I" * RECORD_WORDS, blob, off)
      if words[0] != RECORD_MAGIC:
        raise RuntimeError(f"{group}/{role}/{scenario.name}: bad record magic 0x{words[0]:08x}")
      start = words[7] | (words[8] << 32)
      end = words[9] | (words[10] << 32)
      records.append(Record(
        group=group,
        active_mask=active_mask,
        role=role,
        scenario=scenario.name,
        suite=scenario.suite,
        iterations=words[4],
        ops_per_iter=words[5],
        param=words[6],
        start=start,
        end=end,
        cycles=(end - start) & ((1 << 64) - 1),
        sink=words[11],
      ))
  return records


def format_table(records: list[Record]) -> str:
  by_group_role = {}
  for record in records:
    by_group_role.setdefault((record.group, record.role), {})[record.scenario] = record
  lines = [
    "| group | role | suite | scenario | cycles | cyc/iter | adj cyc/op | sink |",
    "|---|---|---|---|---:|---:|---:|---:|",
  ]
  for group in dict.fromkeys(r.group for r in records):
    for role in ROLE_NAMES:
      role_records = by_group_role.get((group, role))
      if not role_records:
        continue
      empty = role_records["empty"]
      empty_cpi = empty.cycles / empty.iterations
      for scenario, record in role_records.items():
        cpi = record.cycles / record.iterations
        if record.ops_per_iter:
          adj = (record.cycles - empty_cpi * record.iterations) / (record.iterations * record.ops_per_iter)
          adj_text = f"{adj:.3f}"
        else:
          adj_text = ""
        lines.append(
          f"| {group} | {role} | {record.suite} | {scenario} | {record.cycles} | "
          f"{cpi:.3f} | {adj_text} | 0x{record.sink:08x} |"
        )
  return "\n".join(lines)


def append_report(
  path: Path,
  *,
  target_core: tuple[int, int],
  iterations: int,
  suite: str,
  group_preset: str,
  fresh_device_per_group: bool,
  chunk_scenarios: bool,
  scenarios: tuple[Scenario, ...],
  records: list[Record],
):
  now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
  path.parent.mkdir(parents=True, exist_ok=True)
  with path.open("a", encoding="utf-8") as f:
    f.write(f"\n## Run {now}\n\n")
    f.write(f"- Core: logical `{target_core[0]},{target_core[1]}`\n")
    f.write(f"- Suite: `{suite}`\n")
    f.write(f"- Iterations per scenario: `{iterations}`\n")
    f.write("- Dispatch path: slow dispatch (`TT_USB=1`)\n")
    f.write(f"- Group preset: {group_preset}\n")
    f.write(f"- Device lifetime: {'fresh per group' if fresh_device_per_group else 'single session'}\n")
    f.write(f"- Scenario execution: {'one non-empty scenario per launch' if chunk_scenarios else 'all selected scenarios in one launch'}\n")
    f.write("- Groups: " + ", ".join(dict.fromkeys(r.group for r in records)) + "\n\n")
    f.write("Scenarios:\n")
    for scenario in scenarios:
      f.write(f"- `{scenario.name}` ({scenario.suite}): {scenario.description or scenario.body}\n")
    f.write("\nDebug L1 ranges:\n")
    for item in debug_ranges(scenarios):
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
  singles = [role_mask([role]) for role in ROLE_NAMES]
  pairs = [
    role_mask([r1, r2])
    for i, r1 in enumerate(ROLE_NAMES)
    for r2 in ROLE_NAMES[i + 1:]
  ]
  return singles + pairs + [role_mask(list(ROLE_NAMES))]


def default_groups() -> list[int]:
  return [
    role_mask(["brisc"]),
    role_mask(["ncrisc"]),
    role_mask(["trisc0"]),
    role_mask(["brisc", "ncrisc"]),
    role_mask(["brisc", "trisc0"]),
    role_mask(list(ROLE_NAMES)),
  ]


def select_scenarios(suite: str, names: list[str] | None = None) -> tuple[Scenario, ...]:
  wanted = SUITES[suite]
  selected = tuple(scenario for scenario in SCENARIOS if scenario.suite in wanted)
  if names is None:
    return selected
  wanted_names = set(names)
  unknown = sorted(wanted_names - {scenario.name for scenario in SCENARIOS})
  if unknown:
    raise ValueError(f"unknown scenario(s): {', '.join(unknown)}")
  selected = tuple(scenario for scenario in selected if scenario.name == "empty" or scenario.name in wanted_names)
  if len(selected) == 1:
    raise ValueError("--scenarios selected no non-empty scenarios for this --suite")
  return selected


def scenario_chunks(scenarios: tuple[Scenario, ...], *, chunk_scenarios: bool) -> list[tuple[Scenario, ...]]:
  if not chunk_scenarios:
    return [scenarios]
  empty = next((scenario for scenario in scenarios if scenario.name == "empty"), None)
  if empty is None:
    raise ValueError("chunked scenario execution requires the empty baseline")
  chunks = []
  for scenario in scenarios:
    if scenario.name == "empty":
      continue
    chunks.append((empty, scenario))
  return chunks or [(empty,)]


def run_group(
  *,
  active_mask: int,
  iterations: int,
  requested_core: tuple[int, int] | None,
  scenarios: tuple[Scenario, ...],
) -> tuple[tuple[int, int], list[Record]]:
  with harness.open_device() as device:
    target_core = requested_core or device.cores[0]
    clear_ranges(device, target_core, scenarios)
    device.run(build_program(active_mask, iterations, scenarios))
    return target_core, parse_results(read_results(device, target_core, scenarios), group_name(active_mask), scenarios)


def main() -> int:
  parser = argparse.ArgumentParser(description="RISC-V shared-resource trace bench for Verilator clone modeling.")
  parser.add_argument("--core", type=core.parse_core, default=None, help="logical Tensix core X,Y; default: first program core")
  parser.add_argument("--suite", choices=tuple(SUITES), default="quick", help="scenario suite to run")
  parser.add_argument("--scenarios", nargs="+", default=None, help="optional scenario-name filter; empty baseline is kept automatically")
  group_selector = parser.add_mutually_exclusive_group()
  group_selector.add_argument("--groups", nargs="+", type=parse_group, default=None, help="active role groups, e.g. all brisc+ncrisc trisc0")
  group_selector.add_argument("--all-pairs", action="store_true", help="run solos, all C(5,2) pairs, and all five roles")
  parser.add_argument("--iters", type=int, default=10_000, help="iterations per timed scenario")
  parser.add_argument("--fresh-device-per-group", action="store_true", help="open and close Device() around every active-role group")
  parser.add_argument("--chunk-scenarios", action="store_true", help="run one non-empty scenario per launch and merge the table; default for mixed/full suites")
  parser.add_argument("--no-report", action="store_true", help="do not append results to the markdown report")
  parser.add_argument("--report", type=Path, default=harness.doc_path("riscv", "riscv-clone-contention-trace.md"), help="markdown report path")
  args = parser.parse_args()
  if args.iters <= 0:
    raise ValueError("--iters must be positive")

  scenarios = select_scenarios(args.suite, args.scenarios)
  if args.groups is not None:
    groups = list(dict.fromkeys(args.groups))
    group_preset = "custom `--groups`"
  elif args.all_pairs:
    groups = all_pair_groups()
    group_preset = "full pair matrix (`--all-pairs`)"
  else:
    groups = default_groups()
    group_preset = "representative default"

  all_records: list[Record] = []
  target_core: tuple[int, int] | None = None
  fresh_device_per_group = args.fresh_device_per_group or args.all_pairs
  chunk_scenarios = args.chunk_scenarios or args.suite in {"mixed", "full"}
  chunks = scenario_chunks(scenarios, chunk_scenarios=chunk_scenarios)

  if fresh_device_per_group:
    for active_mask in groups:
      for chunk in chunks:
        group_core, records = run_group(
          active_mask=active_mask,
          iterations=args.iters,
          requested_core=args.core,
          scenarios=chunk,
        )
        if target_core is None:
          target_core = group_core
        all_records.extend(records)
  else:
    with harness.open_device() as device:
      target_core = args.core or device.cores[0]
      for active_mask in groups:
        for chunk in chunks:
          clear_ranges(device, target_core, chunk)
          device.run(build_program(active_mask, args.iters, chunk))
          all_records.extend(parse_results(
            read_results(device, target_core, chunk),
            group_name(active_mask),
            chunk,
          ))

  if target_core is None:
    raise RuntimeError("no groups selected")

  print(format_table(all_records))
  if not args.no_report:
    append_report(
      args.report,
      target_core=target_core,
      iterations=args.iters,
      suite=args.suite,
      group_preset=group_preset,
      fresh_device_per_group=fresh_device_per_group,
      chunk_scenarios=chunk_scenarios,
      scenarios=scenarios,
      records=all_records,
    )
    print(f"\nappended {args.report}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
