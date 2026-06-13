#!/usr/bin/env python3
"""RISC-V local/cross-LDM interconnect microbenchmarks.

This isolates the LDM fabric shapes needed by a future Verilator clone:
local LDM baseline, cross-LDM fan-in/fan-out, owner-writer plus remote-readers,
dependent pointer chase, and role-pair/all-five arbitration groups.
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
  s0, s1, s2, s3, s4, s6, s7, s8, s9,
  t0, t1, t2, t4, t5, t6, zero,
)
from program import Program
from ttk.debug import DebugRange


ROLE_INDEX = core.ROLE_INDEX
ROLE_NAMES = core.ROLE_NAMES
ROLE_COUNT = len(ROLE_NAMES)

RESULT_BASE = 0x134000
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
CTRL_INIT = CTRL_BASE + 0xC0
CTRL_SIZE = 0x1000
SCRATCH_SIZE = 0x1000

HEADER_WORDS = 16
RECORD_WORDS = 14
HEADER_SIZE = HEADER_WORDS * 4
RECORD_SIZE = RECORD_WORDS * 4
RESULT_MAGIC = 0x524C444D  # "RLDM"
RECORD_MAGIC = 0x524C4452  # "RLDR"
STATUS_STARTED = 0x1D000001
STATUS_DONE = 0x1D00D00D
CTRL_INIT_VALUE = 0x1D001117


@dataclass(frozen=True)
class Scenario:
  name: str
  body: str
  description: str


SCENARIOS: tuple[Scenario, ...] = (
  Scenario("empty", "empty", "loop overhead baseline"),
  Scenario("ldm_self_lw1", "ldm_self_lw1", "each active role loads its own local LDM"),
  Scenario("ldm_self_sw1", "ldm_self_sw1", "each active role stores its own local LDM"),
  Scenario("ldm_self_rmw2", "ldm_self_rmw2", "each active role load+stores its own local LDM"),
  Scenario("ldm_self_ptr_chase_lw1", "ldm_self_ptr_chase_lw1", "dependent load through own local LDM pointer"),
  Scenario("xldm_fanin_owner_lw1", "xldm_fanin_owner_lw1", "non-owner roles read the first active role's LDM window"),
  Scenario("xldm_roundrobin_lw1", "xldm_roundrobin_lw1", "each active role reads the next active role's LDM window"),
  Scenario("xldm_fanout_reader_lwN", "xldm_fanout_reader_lwN", "first active role reads every other active LDM window"),
  Scenario("xldm_all_to_all_lwN", "xldm_all_to_all_lwN", "each active role reads every other active LDM window"),
  Scenario("xldm_owner_write_readers_lw1", "xldm_owner_write_readers_lw1", "owner writes local LDM while remote roles read it"),
  Scenario("xldm_ptr_chase_owner_lw2", "xldm_ptr_chase_owner_lw2", "non-owner roles issue two dependent loads through owner's LDM window"),
)


@dataclass(frozen=True)
class Record:
  group: str
  active_mask: int
  role: str
  scenario_id: int
  scenario: str
  iterations: int
  ops_per_iter: int
  owner_role: str
  start: int
  end: int
  cycles: int
  sink: int


def result_size(scenarios: tuple[Scenario, ...] = SCENARIOS) -> int:
  return HEADER_SIZE + len(scenarios) * ROLE_COUNT * RECORD_SIZE


def debug_ranges(scenarios: tuple[Scenario, ...] = SCENARIOS) -> tuple[DebugRange, ...]:
  return (
    DebugRange(0, "l1", RESULT_BASE, result_size(scenarios), "riscv_ldm_interconnect_results"),
    DebugRange(1, "l1", CTRL_BASE, CTRL_SIZE, "riscv_ldm_interconnect_ctrl"),
    DebugRange(2, "l1", SCRATCH_BASE, SCRATCH_SIZE, "riscv_ldm_interconnect_scratch"),
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


def owner_role_id(active_mask: int) -> int:
  for role_id in range(ROLE_COUNT):
    if active_mask & (1 << role_id):
      return role_id
  raise ValueError("active_mask must contain at least one role")


def next_active_role_id(active_mask: int, role_id: int) -> int:
  active = [idx for idx in range(ROLE_COUNT) if active_mask & (1 << idx)]
  if len(active) < 2:
    return role_id
  return active[(active.index(role_id) + 1) % len(active)]


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
    role_mask(["ncrisc", "trisc1"]),
    role_mask(list(ROLE_NAMES)),
  ]


def select_scenarios(names: list[str] | None) -> tuple[Scenario, ...]:
  if names is None:
    return SCENARIOS
  wanted = set(names)
  known = {scenario.name for scenario in SCENARIOS}
  unknown = sorted(wanted - known)
  if unknown:
    raise ValueError(f"unknown scenario(s): {', '.join(unknown)}")
  selected = tuple(s for s in SCENARIOS if s.name == "empty" or s.name in wanted)
  if len(selected) == 1:
    raise ValueError("--scenarios selected no non-empty scenarios")
  return selected


def role_ops_per_iter(scenario: Scenario, *, active_mask: int, role_id: int) -> int:
  owner = owner_role_id(active_mask)
  active_count = len(mask_roles(active_mask))
  if scenario.body == "empty":
    return 0
  if scenario.body in {"ldm_self_lw1", "ldm_self_sw1", "ldm_self_ptr_chase_lw1"}:
    return 1
  if scenario.body == "ldm_self_rmw2":
    return 2
  if scenario.body == "xldm_fanin_owner_lw1":
    return 0 if role_id == owner else 1
  if scenario.body == "xldm_roundrobin_lw1":
    return 0 if active_count < 2 else 1
  if scenario.body == "xldm_fanout_reader_lwN":
    return active_count - 1 if role_id == owner else 0
  if scenario.body == "xldm_all_to_all_lwN":
    return active_count - 1
  if scenario.body == "xldm_owner_write_readers_lw1":
    return 1
  if scenario.body == "xldm_ptr_chase_owner_lw2":
    return 0 if role_id == owner else 2
  raise ValueError(f"unknown scenario body {scenario.body!r}")


def emit_header(
  fw: KernelBase,
  *,
  active_mask: int,
  iterations: int,
  scenario_count: int,
  status: int,
):
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
  owner = owner_role_id(active_mask)
  ops_per_iter = role_ops_per_iter(scenario, active_mask=active_mask, role_id=role_id)
  fw.li(s2, record_addr(scenario_id, role_id))
  for off, value in enumerate((
    RECORD_MAGIC,
    active_mask,
    role_id,
    scenario_id,
    iterations,
    ops_per_iter,
    owner,
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


def window_reg(role_id: int):
  return (s7, t4, t5, t6, s9)[role_id]


def emit_load_window(fw: KernelBase, role_id: int, *, dst=s1, off: int = 0):
  return fw.lw(dst, window_reg(role_id), off)


def emit_setup_for_phase(fw: KernelBase, *, role_id: int):
  role_tag = 0x1D000000 | (role_id << 24)
  fw.li(s1, role_tag | 0x1234)
  fw.li(s3, SCRATCH_BASE)
  fw.li(s4, role_tag | 0x5678)
  fw.sw(s1, s3, role_id * 4)

  fw.li(s6, LOCAL_LDM_BASE)
  fw.sw(s6, s6, 0)       # self pointer chase returns to LDM[0].
  fw.sw(s1, s6, 4)
  fw.li(t2, 0x10)
  fw.sw(t2, s6, 0x10)    # cross pointer chase: LDM[16] contains offset 16.

  fw.li(s7, BRISC_LDM_WINDOW)
  fw.li(t4, NCRISC_LDM_WINDOW)
  fw.li(t5, TRISC0_LDM_WINDOW)
  fw.li(t6, TRISC1_LDM_WINDOW)
  fw.li(s9, TRISC2_LDM_WINDOW)
  return fw


def emit_body(fw: KernelBase, scenario: Scenario, *, role_id: int, active_mask: int):
  owner = owner_role_id(active_mask)
  if scenario.body == "empty":
    return fw
  if scenario.body == "ldm_self_lw1":
    return fw.lw(s1, s6, 4)
  if scenario.body == "ldm_self_sw1":
    return fw.sw(s1, s6, 4)
  if scenario.body == "ldm_self_rmw2":
    fw.lw(a0, s6, 4)
    return fw.sw(a0, s6, 4)
  if scenario.body == "ldm_self_ptr_chase_lw1":
    return fw.lw(s6, s6, 0)
  if scenario.body == "xldm_fanin_owner_lw1":
    return fw if role_id == owner else emit_load_window(fw, owner)
  if scenario.body == "xldm_roundrobin_lw1":
    peer = next_active_role_id(active_mask, role_id)
    return fw if peer == role_id else emit_load_window(fw, peer)
  if scenario.body == "xldm_fanout_reader_lwN":
    if role_id != owner:
      return fw
    for peer in range(ROLE_COUNT):
      if peer != role_id and active_mask & (1 << peer):
        emit_load_window(fw, peer)
    return fw
  if scenario.body == "xldm_all_to_all_lwN":
    for peer in range(ROLE_COUNT):
      if peer != role_id and active_mask & (1 << peer):
        emit_load_window(fw, peer)
    return fw
  if scenario.body == "xldm_owner_write_readers_lw1":
    return fw.sw(s1, s6, 4) if role_id == owner else emit_load_window(fw, owner)
  if scenario.body == "xldm_ptr_chase_owner_lw2":
    if role_id == owner:
      return fw
    emit_load_window(fw, owner, dst=t2, off=0x10)
    fw.add(t2, window_reg(owner), t2)
    return fw.lw(s1, t2, 0)
  raise ValueError(f"unknown LDM interconnect body {scenario.body!r}")


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
  emit_body(fw, scenario, role_id=role_id, active_mask=active_mask)
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
  emit_setup_for_phase(fw, role_id=role_id)
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
    emit_setup_for_phase(fw, role_id=0)
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
  program.name = f"riscv_ldm_interconnect:{group_name(active_mask)}"
  return program


def read_results(device: Device, target_core: tuple[int, int], scenarios: tuple[Scenario, ...]) -> bytes:
  result_range = debug_ranges(scenarios)[0]
  with harness.device_window(device, target_core) as win:
    blob = win.read(result_range.address, result_range.size)
  if blob and all(b == 0xFF for b in blob):
    raise RuntimeError(harness.ALL_FF_ERROR)
  return blob


def clear_ranges(device: Device, target_core: tuple[int, int], scenarios: tuple[Scenario, ...]):
  harness.clear_window(device, target_core, ((item.address, item.size) for item in debug_ranges(scenarios)))


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
        scenario_id=words[3],
        scenario=scenario.name,
        iterations=words[4],
        ops_per_iter=words[5],
        owner_role=ROLE_NAMES[words[6]],
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
    "| group | owner | role | scenario | ops/iter | cycles | cyc/iter | adj cyc/op | sink |",
    "|---|---|---|---|---:|---:|---:|---:|---:|",
  ]
  for group in dict.fromkeys(r.group for r in records):
    for role in ROLE_NAMES:
      role_records = by_group_role.get((group, role))
      if not role_records:
        continue
      empty = role_records["empty"]
      empty_cpi = empty.cycles / empty.iterations
      for record in role_records.values():
        cpi = record.cycles / record.iterations
        if record.ops_per_iter:
          adj = (record.cycles - empty_cpi * record.iterations) / (record.iterations * record.ops_per_iter)
          adj_text = f"{adj:.3f}"
        else:
          adj_text = ""
        lines.append(
          f"| {group} | {record.owner_role} | {role} | {record.scenario} | {record.ops_per_iter} | "
          f"{record.cycles} | {cpi:.3f} | {adj_text} | 0x{record.sink:08x} |"
        )
  return "\n".join(lines)


def append_report(
  path: Path,
  *,
  target_core: tuple[int, int],
  iterations: int,
  group_preset: str,
  fresh_device_per_group: bool,
  scenarios: tuple[Scenario, ...],
  records: list[Record],
):
  bullets = [
    f"Core: logical `{target_core[0]},{target_core[1]}`",
    f"Iterations per scenario: `{iterations}`",
    "Dispatch path: slow dispatch (`TT_USB=1`)",
    f"Group preset: {group_preset}",
    f"Device lifetime: {'fresh per group' if fresh_device_per_group else 'single session'}",
    "Groups: " + ", ".join(dict.fromkeys(r.group for r in records)),
  ]
  ranges = "\n".join(f"- `{item.name}` at `0x{item.address:x}` ({item.size} bytes)" for item in debug_ranges(scenarios))
  scenario_lines = "\n".join(f"- `{scenario.name}`: {scenario.description}" for scenario in scenarios)
  table = f"Scenarios:\n{scenario_lines}\n\nDebug L1 ranges:\n{ranges}\n\n{format_table(records)}"
  path.parent.mkdir(parents=True, exist_ok=True)
  harness.append_report(path, "LDM interconnect", bullets, table)


def synthetic_result_blob(active_mask: int, iterations: int, scenarios: tuple[Scenario, ...]) -> bytes:
  blob = bytearray(result_size(scenarios))
  header = [
    RESULT_MAGIC, 1, active_mask, len(scenarios), RECORD_WORDS, STATUS_DONE,
    iterations, RESULT_BASE, CTRL_BASE, SCRATCH_BASE,
  ] + [0] * (HEADER_WORDS - 10)
  struct.pack_into("<" + "I" * HEADER_WORDS, blob, 0, *header)
  owner = owner_role_id(active_mask)
  for scenario_id, scenario in enumerate(scenarios):
    for role_id in range(ROLE_COUNT):
      if not (active_mask & (1 << role_id)):
        continue
      ops = role_ops_per_iter(scenario, active_mask=active_mask, role_id=role_id)
      start = 1000 + scenario_id * 100 + role_id
      cycles = iterations * (3 + ops)
      end = start + cycles
      words = [
        RECORD_MAGIC,
        active_mask,
        role_id,
        scenario_id,
        iterations,
        ops,
        owner,
        start & 0xFFFFFFFF,
        start >> 32,
        end & 0xFFFFFFFF,
        end >> 32,
        0x5A000000 | (role_id << 8) | scenario_id,
        0,
        0,
      ]
      off = HEADER_SIZE + (scenario_id * ROLE_COUNT + role_id) * RECORD_SIZE
      struct.pack_into("<" + "I" * RECORD_WORDS, blob, off, *words)
  return bytes(blob)


def build_only(groups: list[int], iterations: int, scenarios: tuple[Scenario, ...]):
  for active_mask in groups:
    program = build_program(active_mask, iterations, scenarios)
    for role, kernel in program.kernel_map.items():
      for segment in kernel.compile():
        if len(segment.data) % 4:
          raise RuntimeError(f"{group_name(active_mask)}/{role}/{segment.label}: unaligned segment")
    program.layout(core_xy=(0, 0))


def self_test() -> None:
  scenarios = select_scenarios(["ldm_self_lw1", "xldm_fanin_owner_lw1", "xldm_all_to_all_lwN"])
  groups = [role_mask(["brisc", "ncrisc"]), role_mask(list(ROLE_NAMES))]
  build_only(groups, 8, scenarios)
  for active_mask in groups:
    records = parse_results(synthetic_result_blob(active_mask, 8, scenarios), group_name(active_mask), scenarios)
    expected = len(mask_roles(active_mask)) * len(scenarios)
    if len(records) != expected:
      raise RuntimeError(f"self-test record count mismatch {len(records)} != {expected}")
    table = format_table(records)
    if "xldm_all_to_all_lwN" not in table or group_name(active_mask) not in table:
      raise RuntimeError("self-test formatted table is missing expected content")


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
  parser = argparse.ArgumentParser(description="Microbenchmark local/cross-LDM interconnect arbitration across Tensix RISC-V roles.")
  parser.add_argument("--core", type=core.parse_core, default=None, help="logical Tensix core X,Y; default: first program core")
  parser.add_argument("--scenarios", nargs="+", default=None, help="optional scenario-name filter; empty baseline is kept automatically")
  group_selector = parser.add_mutually_exclusive_group()
  group_selector.add_argument("--groups", nargs="+", type=parse_group, default=None, help="active role groups, e.g. all brisc+ncrisc trisc0")
  group_selector.add_argument("--all-pairs", action="store_true", help="run solos, all C(5,2) pairs, and all five roles")
  parser.add_argument("--iters", type=int, default=10_000, help="iterations per timed scenario")
  parser.add_argument("--fresh-device-per-group", action="store_true", help="open and close Device() around every active-role group")
  parser.add_argument("--build-only", action="store_true", help="compile/layout selected programs without opening the device")
  parser.add_argument("--self-test", action="store_true", help="run host-only compile and parser self-tests")
  parser.add_argument("--no-report", action="store_true", help="do not append results to the markdown report")
  parser.add_argument("--report", type=Path, default=harness.doc_path("riscv", "riscv-ldm-interconnect.md"), help="markdown report path")
  args = parser.parse_args()
  if args.iters <= 0:
    raise ValueError("--iters must be positive")

  scenarios = select_scenarios(args.scenarios)
  if args.groups is not None:
    groups = list(dict.fromkeys(args.groups))
    group_preset = "custom `--groups`"
  elif args.all_pairs:
    groups = all_pair_groups()
    group_preset = "full pair matrix (`--all-pairs`)"
  else:
    groups = default_groups()
    group_preset = "representative default"

  if args.self_test:
    self_test()
    print("self-test passed")
    return 0
  if args.build_only:
    build_only(groups, args.iters, scenarios)
    print(f"build-only passed for {len(groups)} group(s), {len(scenarios)} scenario(s)")
    return 0

  all_records: list[Record] = []
  target_core: tuple[int, int] | None = None
  fresh_device_per_group = args.fresh_device_per_group or args.all_pairs

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
      group_preset=group_preset,
      fresh_device_per_group=fresh_device_per_group,
      scenarios=scenarios,
      records=all_records,
    )
    print(f"\nappended {args.report}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
