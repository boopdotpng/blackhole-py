#!/usr/bin/env python3
"""RISC-V MMIO contention and same-L1-word visibility probes.

This is a clone-modeling microbench: it stays on safe RISC-V/L1/MMIO paths,
uses read-only MMIO accesses, and uses only local L1 stores for the
producer/consumer handshakes.
"""

from __future__ import annotations

import argparse
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
  a0, a2, a3, a4, a5,
  s0, s1, s2, s3, s4, s5, s6, s7, s8, s9,
  t0, t1, zero,
)
from program import Program
from ttk.debug import DebugRange
from ttk.tensix import TensixMMIO


ROLE_INDEX = core.ROLE_INDEX
ROLE_NAMES = core.ROLE_NAMES
ROLE_COUNT = len(ROLE_NAMES)

RESULT_BASE = 0x136000
CTRL_BASE = RESULT_BASE + 0x5000
SCRATCH_BASE = RESULT_BASE + 0x6000

CTRL_START = CTRL_BASE
CTRL_READY = CTRL_BASE + 0x40
CTRL_DONE = CTRL_BASE + 0x80
CTRL_ACK = CTRL_BASE + 0xC0
CTRL_INIT = CTRL_BASE + 0xFC
CTRL_SIZE = 0x1000
SCRATCH_SIZE = 0x1000
VISIBILITY_WAIT_SPINS = 4096

SHARED_WORD = SCRATCH_BASE
DISTINCT_WORD_BASE = SCRATCH_BASE + 0x100

HEADER_WORDS = 16
RECORD_WORDS = 16
HEADER_SIZE = HEADER_WORDS * 4
RECORD_SIZE = RECORD_WORDS * 4
RESULT_MAGIC = 0x524D5654  # "RMVT"
RECORD_MAGIC = 0x524D5652  # "RMVR"
STATUS_STARTED = 0xC0110001
STATUS_DONE = 0xC011D00D
CTRL_INIT_VALUE = 0xC0111117


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
  Scenario("mmio_wall_lw1", "mmio", "mmio_wall_lw1", 1, description="read-only wall-clock low MMIO load"),
  Scenario("mmio_wall_hi_lw1", "mmio", "mmio_wall_hi_lw1", 1, description="read-only wall-clock high MMIO load"),
  Scenario("mmio_wall_hilo_lw2", "mmio", "mmio_wall_hilo_lw2", 2, description="read-only wall-clock high+low MMIO loads"),
  Scenario("l1_same_lw1", "producer", "l1_same_lw1", 1, description="all active roles load the same L1 word"),
  Scenario("pc_pressure_writer_readers", "producer", "pc_pressure_writer_readers", 1,
           description="BRISC stores one shared L1 word while other roles load it"),
  Scenario("pc_visibility_ack", "producer", "pc_visibility_ack", 1, 0,
           "BRISC publishes a sequence word; consumers acknowledge after observing it"),
  Scenario("pc_visibility_ack_fence", "producer", "pc_visibility_ack", 1, 1,
           "same as pc_visibility_ack, with fences in the polling/ack path"),
)

SUITES = {
  "quick": {"base", "mmio", "producer"},
  "mmio": {"base", "mmio"},
  "producer": {"base", "producer"},
  "full": {"base", "mmio", "producer"},
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
  aux0: int
  aux1: int


def result_size(scenarios: tuple[Scenario, ...]) -> int:
  return HEADER_SIZE + len(scenarios) * ROLE_COUNT * RECORD_SIZE


def debug_ranges(scenarios: tuple[Scenario, ...] = SCENARIOS) -> tuple[DebugRange, ...]:
  return (
    DebugRange(0, "l1", RESULT_BASE, result_size(scenarios), "riscv_mmio_visibility_results"),
    DebugRange(1, "l1", CTRL_BASE, CTRL_SIZE, "riscv_mmio_visibility_ctrl"),
    DebugRange(2, "l1", SCRATCH_BASE, SCRATCH_SIZE, "riscv_mmio_visibility_scratch"),
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
  aux0=s8,
  aux1=s9,
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
  for off, reg in enumerate((start_lo, start_hi, end_lo, end_hi, sink, aux0, aux1), start=7):
    fw.sw(reg, s2, off * 4)
  fw.sw(zero, s2, 14 * 4)
  fw.sw(zero, s2, 15 * 4)
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


def emit_wait_slot_reg(
  fw: KernelBase,
  addr: int,
  expected,
  *,
  spin_counter=s8,
  actual=t0,
  ptr=t1,
  use_fence: bool = False,
  max_spins: int = VISIBILITY_WAIT_SPINS,
):
  loop = fw._new_label("wait_slot_reg")
  done = fw._new_label("wait_slot_reg_done")
  fw.li(ptr, addr)
  fw.li(a0, max_spins)
  fw.label(loop)
  fw.lw(actual, ptr, 0)
  fw.beq(actual, expected, done)
  fw.addi(spin_counter, spin_counter, 1)
  fw.addi(a0, a0, -1)
  fw.beq(a0, zero, done)
  if use_fence:
    fw.fence()
  fw.j(loop)
  fw.label(done)
  if use_fence:
    fw.fence()
  return fw


def emit_setup_for_phase(fw: KernelBase, *, role_id: int, scenario: Scenario):
  role_tag = 0xE0000000 | (role_id << 24)
  fw.li(s1, role_tag | 0x1234)
  fw.li(s3, SHARED_WORD)
  fw.li(s4, DISTINCT_WORD_BASE + role_id * 0x40)
  fw.li(s5, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L)
  fw.li(s6, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_H)
  fw.li(s7, CTRL_ACK + role_id * 4)
  fw.li(s8, 0)
  fw.li(s9, 0)
  fw.sw(zero, s7, 0)
  fw.sw(zero, s3, 0)
  fw.sw(s1, s4, 0)
  fw.sw(s1, s4, 4)
  return fw


def emit_pressure_body(fw: KernelBase, role_id: int):
  if role_id == 0:
    fw.addi(s1, s1, 1)
    return fw.sw(s1, s3, 0)
  return fw.lw(s1, s3, 0)


def emit_visibility_body(fw: KernelBase, *, role_id: int, active_mask: int,
                         iterations: int, scenario: Scenario):
  use_fence = bool(scenario.param)
  fw.li(s1, 0)
  fw.li(s8, 0)
  fw.li(s9, 0)
  fw.li(s0, iterations)
  loop = fw._new_label(f"visibility_{scenario.name}")
  done = fw._new_label(f"visibility_{scenario.name}_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  fw.addi(s1, s1, 1)
  if role_id == 0:
    fw.sw(s1, s3, 0)
    if use_fence:
      fw.fence()
    for waiter_id in range(1, ROLE_COUNT):
      if active_mask & (1 << waiter_id):
        emit_wait_slot_reg(
          fw,
          CTRL_ACK + waiter_id * 4,
          s1,
          spin_counter=s8,
          use_fence=use_fence,
        )
  else:
    emit_wait_slot_reg(
      fw,
      SHARED_WORD,
      s1,
      spin_counter=s8,
      use_fence=use_fence,
    )
    fw.sw(s1, s7, 0)
    if use_fence:
      fw.fence()
  fw.addi(s9, s9, 1)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  return fw


def emit_body(fw: KernelBase, scenario: Scenario, *, role_id: int, active_mask: int,
              iterations: int):
  body = scenario.body
  if body == "empty":
    return fw
  if body == "mmio_wall_lw1":
    return fw.lw(s1, s5, 0)
  if body == "mmio_wall_hi_lw1":
    return fw.lw(s1, s6, 0)
  if body == "mmio_wall_hilo_lw2":
    fw.lw(a0, s6, 0)
    return fw.lw(s1, s5, 0)
  if body == "l1_same_lw1":
    return fw.lw(s1, s3, 0)
  if body == "pc_pressure_writer_readers":
    return emit_pressure_body(fw, role_id)
  if body == "pc_visibility_ack":
    return emit_visibility_body(
      fw,
      role_id=role_id,
      active_mask=active_mask,
      iterations=iterations,
      scenario=scenario,
    )
  raise ValueError(f"unknown MMIO/visibility body {body!r}")


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
  if scenario.body == "pc_visibility_ack":
    emit_body(fw, scenario, role_id=role_id, active_mask=active_mask, iterations=iterations)
  else:
    fw.li(s0, iterations)
    loop = fw._new_label(f"bench_{scenario.name}")
    done = fw._new_label(f"bench_{scenario.name}_done")
    fw.label(loop)
    fw.beq(s0, zero, done)
    emit_body(fw, scenario, role_id=role_id, active_mask=active_mask, iterations=iterations)
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
  emit_setup_for_phase(fw, role_id=0, scenario=scenario)
  fw.write32(CTRL_READY, phase)
  emit_wait_active_slots(fw, CTRL_READY, active_mask, phase)
  fw.write32(CTRL_START, phase)
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
    fw.write32(CTRL_INIT, CTRL_INIT_VALUE)
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
  emit_wait_word(fw, CTRL_INIT, CTRL_INIT_VALUE)
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
  program.name = f"riscv_mmio_visibility:{group_name(active_mask)}"
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
        aux0=words[12],
        aux1=words[13],
      ))
  return records


def format_table(records: list[Record]) -> str:
  by_group_role = {}
  for record in records:
    by_group_role.setdefault((record.group, record.role), {})[record.scenario] = record
  lines = [
    "| group | role | suite | scenario | cycles | cyc/iter | adj cyc/unit | sink | aux0 | aux1 |",
    "|---|---|---|---|---:|---:|---:|---:|---:|---:|",
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
          f"{cpi:.3f} | {adj_text} | 0x{record.sink:08x} | {record.aux0} | {record.aux1} |"
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
  scenarios: tuple[Scenario, ...],
  records: list[Record],
):
  bullets = [
    f"Core: logical `{target_core[0]},{target_core[1]}`",
    f"Suite: `{suite}`",
    f"Iterations per scenario: `{iterations}`",
    "Dispatch path: slow dispatch (`TT_USB=1`)",
    f"Group preset: {group_preset}",
    f"Device lifetime: {'fresh per group' if fresh_device_per_group else 'single session'}",
    "Groups: " + ", ".join(dict.fromkeys(r.group for r in records)),
  ]
  table = ["Scenarios:"]
  table.extend(f"- `{scenario.name}` ({scenario.suite}): {scenario.description or scenario.body}" for scenario in scenarios)
  table.append("")
  table.append("Debug L1 ranges:")
  table.extend(f"- `{item.name}` at `0x{item.address:x}` ({item.size} bytes)" for item in debug_ranges(scenarios))
  table.append("")
  table.append(format_table(records))
  path.parent.mkdir(parents=True, exist_ok=True)
  harness.append_report(path, "", bullets, "\n".join(table))


def parse_group(text: str) -> int:
  aliases = {
    "all": ROLE_NAMES,
    "brisc": ("brisc",),
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
  if "brisc" not in roles:
    raise argparse.ArgumentTypeError("groups must include brisc; it is the controller/producer")
  return role_mask(roles)


def default_groups() -> list[int]:
  return [
    role_mask(["brisc"]),
    role_mask(["brisc", "ncrisc"]),
    role_mask(["brisc", "trisc0"]),
    role_mask(list(ROLE_NAMES)),
  ]


def all_brisc_pair_groups() -> list[int]:
  return [role_mask(["brisc", role]) for role in ROLE_NAMES[1:]] + [role_mask(list(ROLE_NAMES))]


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


def _fake_results(active_mask: int, iterations: int, scenarios: tuple[Scenario, ...]) -> bytes:
  blob = bytearray(result_size(scenarios))
  header = [0] * HEADER_WORDS
  header[:10] = [
    RESULT_MAGIC, 1, active_mask, len(scenarios), RECORD_WORDS, STATUS_DONE,
    iterations, RESULT_BASE, CTRL_BASE, SCRATCH_BASE,
  ]
  struct.pack_into("<" + "I" * HEADER_WORDS, blob, 0, *header)
  for scenario_id, scenario in enumerate(scenarios):
    for role_id in range(ROLE_COUNT):
      if not (active_mask & (1 << role_id)):
        continue
      off = HEADER_SIZE + (scenario_id * ROLE_COUNT + role_id) * RECORD_SIZE
      start = 1000 + scenario_id * 100 + role_id * 10
      end = start + iterations * (3 + scenario_id)
      words = [
        RECORD_MAGIC,
        active_mask,
        role_id,
        scenario_id,
        iterations,
        scenario.ops_per_iter,
        scenario.param,
        start & 0xFFFFFFFF,
        start >> 32,
        end & 0xFFFFFFFF,
        end >> 32,
        0xA5000000 | (role_id << 8) | scenario_id,
        scenario_id,
        iterations if scenario.body == "pc_visibility_ack" else 0,
        0,
        0,
      ]
      struct.pack_into("<" + "I" * RECORD_WORDS, blob, off, *words)
  return bytes(blob)


def self_test() -> None:
  scenarios = select_scenarios("quick")
  groups = [role_mask(["brisc", "ncrisc"]), role_mask(list(ROLE_NAMES))]
  compiled_bytes = 0
  for active_mask in groups:
    program = build_program(active_mask, 8, scenarios)
    for kernel in program.kernel_map.values():
      for segment in kernel.compile():
        compiled_bytes += len(segment.data)
  records = parse_results(_fake_results(groups[0], 8, scenarios), group_name(groups[0]), scenarios)
  table = format_table(records)
  if "pc_visibility_ack_fence" not in table:
    raise AssertionError("formatted self-test table missed visibility scenario")
  print(f"self-test ok: compiled {compiled_bytes} bytes across {len(groups)} groups; parsed {len(records)} records")


def main() -> int:
  parser = argparse.ArgumentParser(description="RISC-V read-only MMIO contention and L1 producer/consumer visibility bench.")
  parser.add_argument("--core", type=core.parse_core, default=None, help="logical Tensix core X,Y; default: first program core")
  parser.add_argument("--suite", choices=tuple(SUITES), default="quick", help="scenario suite to run")
  parser.add_argument("--scenarios", nargs="+", default=None, help="optional scenario-name filter; empty baseline is kept automatically")
  group_selector = parser.add_mutually_exclusive_group()
  group_selector.add_argument("--groups", nargs="+", type=parse_group, default=None, help="active role groups containing brisc, e.g. all brisc+ncrisc")
  group_selector.add_argument("--all-brisc-pairs", action="store_true", help="run BRISC with each other role, then all five roles")
  parser.add_argument("--iters", type=int, default=10_000, help="iterations per timed scenario")
  parser.add_argument("--fresh-device-per-group", action="store_true", help="open and close Device() around every active-role group")
  parser.add_argument("--no-report", action="store_true", help="do not append results to the markdown report")
  parser.add_argument("--report", type=Path, default=harness.doc_path("riscv", "riscv-mmio-visibility.md"), help="markdown report path")
  parser.add_argument("--self-test", action="store_true", help="compile generated kernels and exercise parsing without opening a device")
  args = parser.parse_args()

  if args.self_test:
    self_test()
    return 0
  if args.iters <= 0:
    raise ValueError("--iters must be positive")

  scenarios = select_scenarios(args.suite, args.scenarios)
  if args.groups is not None:
    groups = list(dict.fromkeys(args.groups))
    group_preset = "custom `--groups`"
  elif args.all_brisc_pairs:
    groups = all_brisc_pair_groups()
    group_preset = "BRISC pair matrix (`--all-brisc-pairs`)"
  else:
    groups = default_groups()
    group_preset = "representative default"

  all_records: list[Record] = []
  target_core: tuple[int, int] | None = None
  fresh_device_per_group = args.fresh_device_per_group or args.all_brisc_pairs

  if fresh_device_per_group:
    for active_mask in groups:
      group_core, records = run_group(
        active_mask=active_mask,
        iterations=args.iters,
        requested_core=args.core,
        scenarios=scenarios,
      )
      if target_core is None:
        target_core = group_core
      all_records.extend(records)
  else:
    with harness.open_device() as device:
      target_core = args.core or device.cores[0]
      for active_mask in groups:
        clear_ranges(device, target_core, scenarios)
        device.run(build_program(active_mask, args.iters, scenarios))
        all_records.extend(parse_results(
          read_results(device, target_core, scenarios),
          group_name(active_mask),
          scenarios,
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
      scenarios=scenarios,
      records=all_records,
    )
    print(f"\nappended {args.report}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
