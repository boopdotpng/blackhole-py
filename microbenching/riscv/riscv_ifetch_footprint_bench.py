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
import riscv_core_bench as core  # noqa: E402
from asm import KernelBase  # noqa: E402
from device import Device  # noqa: E402
from dsl import (  # noqa: E402
  a2, a3, a4, a5,
  s0, s1, s2, s3, s4, s5, s6, s7,
  t0, t1, t2, t3, t4, t5, t6, zero,
)
from program import Program  # noqa: E402
from ttk.debug import DebugRange  # noqa: E402


ROLE_INDEX = core.ROLE_INDEX
ROLE_NAMES = core.ROLE_NAMES
ROLE_COUNT = len(ROLE_NAMES)

RESULT_BASE = 0x130000
CTRL_BASE = RESULT_BASE + 0x8000
SCRATCH_BASE = RESULT_BASE + 0x9000
CTRL_START = CTRL_BASE
CTRL_READY = CTRL_BASE + 0x40
CTRL_DONE = CTRL_BASE + 0x80
CTRL_SIZE = 0x1000
SCRATCH_SIZE = 0x1000

HEADER_WORDS = 16
RECORD_WORDS = 16
HEADER_SIZE = HEADER_WORDS * 4
RECORD_SIZE = RECORD_WORDS * 4
RESULT_MAGIC = 0x52424649  # "RBFI"
RECORD_MAGIC = 0x52424652  # "RBFR"
STATUS_STARTED = 0x1F001001
STATUS_DONE = 0x1F00D00D

TRAFFIC_INDEX = {
  "compute": 0,
  "l1_load": 1,
  "l1_store": 2,
  "l1_mixed": 3,
}
TRAFFIC_NAMES = tuple(TRAFFIC_INDEX)


@dataclass(frozen=True)
class BenchSpec:
  name: str
  unroll: int
  traffic: str

  @property
  def instrs_per_iter(self) -> int:
    return self.unroll * 8

  @property
  def payload_bytes(self) -> int:
    return self.instrs_per_iter * 4


@dataclass(frozen=True)
class Record:
  group: str
  active_mask: int
  role: str
  test_id: int
  name: str
  iterations: int
  instrs_per_iter: int
  unroll: int
  traffic: str
  payload_bytes: int
  start: int
  end: int
  cycles: int
  sink: int


def make_specs(unrolls: list[int], traffic: list[str]) -> tuple[BenchSpec, ...]:
  specs = [BenchSpec("empty", 0, "compute")]
  for mode in traffic:
    for unroll in unrolls:
      specs.append(BenchSpec(f"{mode}_u{unroll}", unroll, mode))
  return tuple(specs)


def result_size(specs: tuple[BenchSpec, ...]) -> int:
  return HEADER_SIZE + len(specs) * ROLE_COUNT * RECORD_SIZE


def debug_ranges(specs: tuple[BenchSpec, ...]) -> tuple[DebugRange, ...]:
  return (
    DebugRange(0, "l1", RESULT_BASE, result_size(specs), "riscv_ifetch_footprint_results"),
    DebugRange(1, "l1", CTRL_BASE, CTRL_SIZE, "riscv_ifetch_footprint_ctrl"),
    DebugRange(2, "l1", SCRATCH_BASE, SCRATCH_SIZE, "riscv_ifetch_footprint_scratch"),
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


def default_groups() -> list[int]:
  return [role_mask(["brisc"]), role_mask(["brisc", "ncrisc"]), role_mask(list(ROLE_NAMES))]


def emit_header(fw: KernelBase, *, active_mask: int, iterations: int, specs: tuple[BenchSpec, ...], status: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, 1, active_mask, len(specs), RECORD_WORDS, status, iterations,
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
    spec.instrs_per_iter,
    spec.unroll,
    TRAFFIC_INDEX[spec.traffic],
    spec.payload_bytes,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off, reg in enumerate((start_lo, start_hi, end_lo, end_hi, sink), start=9):
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


def emit_setup_for_phase(fw: KernelBase, *, role_id: int):
  tag = 0x1F000000 | (role_id << 24)
  fw.li(s1, tag | 0x1234)
  fw.li(s3, SCRATCH_BASE + role_id * 0x100)
  fw.li(s4, 3)
  fw.li(s5, 5)
  fw.li(s6, 7)
  fw.li(s7, 11)
  for off in range(0, 128, 4):
    fw.sw(s1, s3, off)
  return fw


def emit_payload_block(fw: KernelBase, traffic: str):
  if traffic == "compute":
    fw.addi(s1, s1, 1)
    fw.xori(s4, s4, 0x55)
    fw.add(s5, s5, s1)
    fw.sub(s6, s6, s4)
    fw.slli(t0, s5, 1)
    fw.srli(t1, s6, 1)
    fw.xor(t2, t0, t1)
    return fw.add(s1, s1, t2)
  if traffic == "l1_load":
    for reg, off in ((t0, 0), (t1, 4), (t2, 8), (t3, 12)):
      fw.lw(reg, s3, off)
    fw.add(s1, s1, t0)
    fw.xor(s4, s4, t1)
    fw.add(s5, s5, t2)
    return fw.xor(s6, s6, t3)
  if traffic == "l1_store":
    fw.sw(s1, s3, 0)
    fw.addi(s1, s1, 1)
    fw.sw(s4, s3, 4)
    fw.addi(s4, s4, 1)
    fw.sw(s5, s3, 8)
    fw.addi(s5, s5, 1)
    fw.sw(s6, s3, 12)
    return fw.addi(s6, s6, 1)
  if traffic == "l1_mixed":
    fw.lw(t0, s3, 0)
    fw.add(s1, s1, t0)
    fw.sw(s1, s3, 16)
    fw.lw(t1, s3, 4)
    fw.xor(s4, s4, t1)
    fw.sw(s4, s3, 20)
    fw.add(s5, s5, s4)
    return fw.xor(s6, s6, s5)
  raise ValueError(f"unknown traffic mode {traffic!r}")


def emit_payload(fw: KernelBase, spec: BenchSpec):
  if spec.unroll == 0:
    return fw
  for _ in range(spec.unroll):
    emit_payload_block(fw, spec.traffic)
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
  loop = fw._new_label(f"bench_{spec.name}")
  body = fw._new_label(f"bench_{spec.name}_body")
  done = fw._new_label(f"bench_{spec.name}_done")
  fw.label(loop)
  fw.bne(s0, zero, body)
  fw.j(done)
  fw.label(body)
  emit_payload(fw, spec)
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
  emit_timed_payload(fw, role_id=role_id, active_mask=active_mask, test_id=test_id, iterations=iterations, spec=spec)
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
    emit_timed_payload(fw, role_id=0, active_mask=active_mask, test_id=test_id, iterations=iterations, spec=spec)
    fw.write32(CTRL_DONE, phase)
  emit_wait_active_slots(fw, CTRL_DONE, active_mask, phase)
  return fw


def build_role_kernel(role: str, active_mask: int, iterations: int, specs: tuple[BenchSpec, ...]) -> KernelBase:
  role_id = ROLE_INDEX[role]
  fw = KernelBase()
  if role == "brisc":
    fw.zero_word_range(CTRL_BASE, CTRL_BASE + CTRL_SIZE)
    emit_header(fw, active_mask=active_mask, iterations=iterations, specs=specs, status=STATUS_STARTED)
    for test_id, spec in enumerate(specs):
      emit_controller_phase(fw, active_mask=active_mask, test_id=test_id, iterations=iterations, spec=spec)
    emit_header(fw, active_mask=active_mask, iterations=iterations, specs=specs, status=STATUS_DONE)
    return fw.ret()
  if not (active_mask & (1 << role_id)):
    return fw.ret()
  for test_id, spec in enumerate(specs):
    emit_worker_phase(fw, role_id=role_id, active_mask=active_mask, test_id=test_id, iterations=iterations, spec=spec)
  return fw.ret()


def build_program(active_mask: int, iterations: int, specs: tuple[BenchSpec, ...]) -> Program:
  kernels = {role: build_role_kernel(role, active_mask, iterations, specs) for role in ROLE_NAMES}
  program = Program(**kernels, num_cores=1)
  program.name = f"riscv_ifetch_footprint:{group_name(active_mask)}"
  return program


def read_results(device: Device, target_core: tuple[int, int], specs: tuple[BenchSpec, ...]) -> bytes:
  result_range = debug_ranges(specs)[0]
  return harness.read_window(device, target_core, result_range.address, result_range.size)


def clear_ranges(device: Device, target_core: tuple[int, int], specs: tuple[BenchSpec, ...]):
  harness.clear_window(device, target_core, [(item.address, item.size) for item in debug_ranges(specs)])


def parse_results(blob: bytes, group: str, specs: tuple[BenchSpec, ...]) -> list[Record]:
  header = struct.unpack_from("<" + "I" * HEADER_WORDS, blob, 0)
  if header[0] != RESULT_MAGIC:
    raise RuntimeError(f"{group}: bad result magic 0x{header[0]:08x}")
  if header[5] != STATUS_DONE:
    raise RuntimeError(f"{group}: benchmark did not finish, status=0x{header[5]:08x}")
  active_mask = header[2]
  records = []
  for test_id, spec in enumerate(specs):
    for role_id, role in enumerate(ROLE_NAMES):
      if not (active_mask & (1 << role_id)):
        continue
      off = HEADER_SIZE + (test_id * ROLE_COUNT + role_id) * RECORD_SIZE
      words = struct.unpack_from("<" + "I" * RECORD_WORDS, blob, off)
      if words[0] != RECORD_MAGIC:
        raise RuntimeError(f"{group}/{role}/{spec.name}: bad record magic 0x{words[0]:08x}")
      start = words[9] | (words[10] << 32)
      end = words[11] | (words[12] << 32)
      traffic_id = words[7]
      traffic = next((name for name, idx in TRAFFIC_INDEX.items() if idx == traffic_id), f"unknown:{traffic_id}")
      records.append(Record(
        group=group,
        active_mask=active_mask,
        role=role,
        test_id=words[3],
        name=spec.name,
        iterations=words[4],
        instrs_per_iter=words[5],
        unroll=words[6],
        traffic=traffic,
        payload_bytes=words[8],
        start=start,
        end=end,
        cycles=(end - start) & ((1 << 64) - 1),
        sink=words[13],
      ))
  return records


def format_table(records: list[Record]) -> str:
  by_group_role = {}
  for record in records:
    by_group_role.setdefault((record.group, record.role), {})[record.name] = record
  spec_order = list(dict.fromkeys(record.name for record in records))
  lines = [
    "| group | role | test | traffic | payload bytes | cycles | cyc/iter | adj cyc/inst | sink |",
    "|---|---|---:|---|---:|---:|---:|---:|---:|",
  ]
  for group in dict.fromkeys(r.group for r in records):
    for role in ROLE_NAMES:
      role_records = by_group_role.get((group, role))
      if not role_records:
        continue
      empty = role_records["empty"]
      empty_cpi = empty.cycles / empty.iterations
      for name in spec_order:
        if name not in role_records:
          continue
        r = role_records[name]
        cpi = r.cycles / r.iterations
        if r.instrs_per_iter:
          baseline = empty_cpi * r.iterations
          adj = (r.cycles - baseline) / (r.iterations * r.instrs_per_iter)
          adj_text = f"{adj:.3f}"
        else:
          adj_text = ""
        lines.append(
          f"| {group} | {role} | {r.name} | {r.traffic} | {r.payload_bytes} | {r.cycles} | {cpi:.3f} | {adj_text} | 0x{r.sink:08x} |"
        )
  return "\n".join(lines)


def append_report(
  path: Path,
  *,
  target_core: tuple[int, int],
  iterations: int,
  groups: list[int],
  specs: tuple[BenchSpec, ...],
  records: list[Record],
):
  now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
  with path.open("a", encoding="utf-8") as f:
    f.write(f"\n## Run {now}\n\n")
    f.write(f"- Core: logical `{target_core[0]},{target_core[1]}`\n")
    f.write(f"- Iterations per test: `{iterations}`\n")
    f.write("- Dispatch path: slow dispatch (`TT_USB=1`)\n")
    f.write("- Groups: " + ", ".join(group_name(g) for g in groups) + "\n")
    f.write("- Traffic modes: " + ", ".join(dict.fromkeys(s.traffic for s in specs if s.unroll)) + "\n")
    f.write("- Unrolls: " + ", ".join(str(s.unroll) for s in specs if s.unroll and s.traffic == specs[1].traffic) + "\n\n")
    f.write("Debug L1 ranges:\n")
    for item in debug_ranges(specs):
      f.write(f"- `{item.name}` at `0x{item.address:x}` ({item.size} bytes)\n")
    f.write("\n")
    f.write(format_table(records))
    f.write("\n")


def parse_group(text: str) -> int:
  aliases = {"all": ROLE_NAMES}
  roles = list(aliases[text]) if text in aliases else text.replace(",", "+").split("+")
  roles = [role.strip() for role in roles if role.strip()]
  if not roles:
    raise argparse.ArgumentTypeError("group must contain at least one role")
  unknown = [role for role in roles if role not in ROLE_INDEX]
  if unknown:
    raise argparse.ArgumentTypeError(f"unknown role(s): {', '.join(unknown)}")
  return role_mask(roles)


def parse_csv_ints(text: str) -> list[int]:
  values = [int(part, 0) for part in text.replace(",", " ").split()]
  if not values or any(v <= 0 for v in values):
    raise argparse.ArgumentTypeError("expected positive integer unroll(s)")
  return values


def compile_summary(groups: list[int], iterations: int, specs: tuple[BenchSpec, ...]) -> str:
  lines = [
    "| group | layout bytes | text segments | max role text bytes |",
    "|---|---:|---:|---:|",
  ]
  for active_mask in groups:
    program = build_program(active_mask, iterations, specs)
    layout = program.layout(core_xy=(0, 0))
    text_segments = [seg for seg in layout if "." in seg.label and seg.label.endswith(".text")]
    max_role_text = max((len(seg.data) for seg in text_segments), default=0)
    layout_bytes = sum(len(seg.data) for seg in layout)
    lines.append(f"| {group_name(active_mask)} | {layout_bytes} | {len(text_segments)} | {max_role_text} |")
  return "\n".join(lines)


def self_test(specs: tuple[BenchSpec, ...], groups: list[int], iterations: int):
  summary = compile_summary(groups, iterations, specs)
  active_mask = groups[0]
  blob = bytearray(result_size(specs))
  struct.pack_into("<" + "I" * HEADER_WORDS, blob, 0, RESULT_MAGIC, 1, active_mask, len(specs), RECORD_WORDS, STATUS_DONE, iterations, RESULT_BASE, CTRL_BASE, SCRATCH_BASE, 0, 0, 0, 0, 0, 0)
  for test_id, spec in enumerate(specs):
    for role_id in range(ROLE_COUNT):
      if not (active_mask & (1 << role_id)):
        continue
      off = HEADER_SIZE + (test_id * ROLE_COUNT + role_id) * RECORD_SIZE
      start = 1000 + test_id * 100
      end = start + iterations * (3 + spec.instrs_per_iter)
      words = (
        RECORD_MAGIC, active_mask, role_id, test_id, iterations, spec.instrs_per_iter,
        spec.unroll, TRAFFIC_INDEX[spec.traffic], spec.payload_bytes,
        start & 0xFFFFFFFF, start >> 32, end & 0xFFFFFFFF, end >> 32,
        0x12340000 | test_id, 0, 0,
      )
      struct.pack_into("<" + "I" * RECORD_WORDS, blob, off, *words)
  records = parse_results(bytes(blob), group_name(active_mask), specs)
  expected = len(specs) * len(mask_roles(active_mask))
  if len(records) != expected:
    raise AssertionError(f"expected {expected} records, got {len(records)}")
  print(summary)
  print(f"\nself-test ok: compiled {len(groups)} group(s), parsed {len(records)} synthetic record(s)")


def run_group(
  *,
  active_mask: int,
  iterations: int,
  specs: tuple[BenchSpec, ...],
  requested_core: tuple[int, int] | None,
) -> tuple[tuple[int, int], list[Record]]:
  with harness.open_device() as device:
    target_core = requested_core or device.cores[0]
    clear_ranges(device, target_core, specs)
    device.run(build_program(active_mask, iterations, specs))
    return target_core, parse_results(read_results(device, target_core, specs), group_name(active_mask), specs)


def main():
  parser = argparse.ArgumentParser(description="Microbenchmark RISC-V I-fetch/code-footprint pressure with optional local L1 data traffic.")
  parser.add_argument("--core", type=core.parse_core, default=None, help="logical Tensix core X,Y; default: first program core")
  parser.add_argument("--groups", nargs="+", type=parse_group, default=None, help="active role groups, e.g. all brisc+ncrisc")
  parser.add_argument("--unrolls", type=parse_csv_ints, default=parse_csv_ints("1,4,16,64"), help="comma/space list of generated payload unroll counts")
  parser.add_argument("--traffic", nargs="+", choices=TRAFFIC_NAMES, default=["compute", "l1_load", "l1_store", "l1_mixed"], help="payload traffic modes")
  parser.add_argument("--iters", type=int, default=5_000, help="iterations per timed loop")
  parser.add_argument("--build-only", action="store_true", help="compile/layout selected Programs without opening the device")
  parser.add_argument("--self-test", action="store_true", help="run host-only compile and parser checks without opening the device")
  parser.add_argument("--no-report", action="store_true", help="do not append results to docs/riscv/riscv-ifetch-footprint.md")
  parser.add_argument("--report", type=Path, default=harness.doc_path("riscv", "riscv-ifetch-footprint.md"), help="markdown report path")
  args = parser.parse_args()
  if args.iters <= 0:
    raise ValueError("--iters must be positive")

  specs = make_specs(args.unrolls, args.traffic)
  groups = list(dict.fromkeys(args.groups if args.groups is not None else default_groups()))

  if args.self_test:
    self_test(specs, groups, args.iters)
    return
  if args.build_only:
    print(compile_summary(groups, args.iters, specs))
    return

  all_records: list[Record] = []
  target_core: tuple[int, int] | None = None
  for active_mask in groups:
    group_core, records = run_group(
      active_mask=active_mask,
      iterations=args.iters,
      specs=specs,
      requested_core=args.core,
    )
    if target_core is None:
      target_core = group_core
    all_records.extend(records)

  print(format_table(all_records))
  if not args.no_report:
    assert target_core is not None
    append_report(args.report, target_core=target_core, iterations=args.iters, groups=groups, specs=specs, records=all_records)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
