#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as _dt
import os
import statistics
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
  sys.path.insert(0, str(Path(__file__).resolve().parent))

import matmul_peak as matmul

from asm import KernelBase
from device import Device
from dsl import (
  TTREPLAY, TTSEMINIT, TTSETRWC, TTSTALLWAIT, TTZEROACC, TTZEROSRC,
  a2, a3, a4, a5, a6, a7,
  s0, s1, s2, s3, s4, s5, s6, s7, s8,
  t0, t1, t2, t3, t4, t5, zero,
)
from pcie import TLBWindow
from program import Dtype, Program
from ttk.debug import DebugRange
from ttk.tensix import Cfg, Tensix, TensixMMIO, TensixRegs, TensixSem, TensixStall, TensixWait


AICLK_MHZ = 1350.0
RESULT_BASE = 0x129000
HEADER_WORDS = 16
RECORD_WORDS = 16
HEADER_SIZE = HEADER_WORDS * 4
RECORD_SIZE = RECORD_WORDS * 4
RESULT_MAGIC = 0x4D424D48  # "HMBM" LE: math backend microbench.
RECORD_MAGIC = 0x4D425243  # "CRBM" LE.
STATUS_STARTED = 0x4D0B0001
STATUS_DONE = 0x4D0BD00D

VARIANT_UNTHROTTLED = 0
VARIANT_THROTTLE0 = 1
VARIANT_NAMES = {
  VARIANT_UNTHROTTLED: "unthrottled",
  VARIANT_THROTTLE0: "throttle0",
}

MATH_PREP_WORDS = (
  TTZEROSRC(0, 0, 1, 3),
  TTZEROACC(3, 0, 0, 1, 0),
  TTSETRWC(0, 0, 0, 0, 0, 15),
)


@dataclass(frozen=True)
class BenchSpec:
  name: str
  group: str
  variant: int
  repeats: int = 1
  mops_per_iter: int = 0
  output_tiles_per_iter: int = 0
  tile_k_per_iter: int = 0
  include_drain: bool = True


SPECS = (
  BenchSpec("empty", "baseline", VARIANT_UNTHROTTLED, include_drain=False),
  BenchSpec("sync_empty", "sync", VARIANT_UNTHROTTLED),
  BenchSpec("prep_src", "prep", VARIANT_UNTHROTTLED),
  BenchSpec("math_init_unthrottled", "init", VARIANT_UNTHROTTLED, include_drain=False),
  BenchSpec("program_mop_unthrottled", "program_mop", VARIANT_UNTHROTTLED, include_drain=False),
  BenchSpec("mop_tile_unthrottled", "mop_tile", VARIANT_UNTHROTTLED, mops_per_iter=2, output_tiles_per_iter=1, tile_k_per_iter=1),
  BenchSpec("math_init_throttle0", "init", VARIANT_THROTTLE0, include_drain=False),
  BenchSpec("program_mop_throttle0", "program_mop", VARIANT_THROTTLE0, include_drain=False),
  BenchSpec("mop_tile_throttle0", "mop_tile", VARIANT_THROTTLE0, mops_per_iter=1, output_tiles_per_iter=1, tile_k_per_iter=1),
)
SPECS_ALL = SPECS
SPECS = tuple(spec for spec in SPECS_ALL if spec.group != "mop_tile")


@dataclass(frozen=True)
class Record:
  test_id: int
  name: str
  group: str
  variant: int
  iterations: int
  repeats: int
  mops_per_iter: int
  output_tiles_per_iter: int
  tile_k_per_iter: int
  start: int
  end: int
  cycles: int
  sink: int

  @property
  def cycles_per_iter(self) -> float:
    return self.cycles / self.iterations


class MathBenchKernel(KernelBase, Tensix):
  pass


def parse_core(s: str) -> tuple[int, int]:
  try:
    x, y = s.split(",", 1)
    return int(x, 0), int(y, 0)
  except ValueError as e:
    raise argparse.ArgumentTypeError("core must be X,Y") from e


def result_size() -> int:
  return HEADER_SIZE + len(SPECS) * RECORD_SIZE


def debug_ranges() -> tuple[DebugRange, ...]:
  return (
    DebugRange(0, "l1", RESULT_BASE, result_size(), "math_backend_microbench_results"),
  )


def read_wall_clock(fw: KernelBase, lo, hi, *, addr=a7, hi2=a6):
  retry = fw._new_label("wall_clock_retry")
  fw.li(addr, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_H)
  fw.label(retry)
  fw.lw(hi, addr, 0)
  fw.lw(lo, addr, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L - TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_H)
  fw.lw(hi2, addr, 0)
  fw.bne(hi, hi2, retry)
  return fw


def emit_header(fw: KernelBase, *, iterations: int, status: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, len(SPECS), RECORD_WORDS, status, iterations, RESULT_BASE, result_size(), 1,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
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
  sink=s1,
):
  addr = RESULT_BASE + HEADER_SIZE + test_id * RECORD_SIZE
  fw.li(s2, addr)
  const_words = (
    RECORD_MAGIC,
    test_id,
    spec.variant,
    iterations,
    spec.repeats,
    spec.mops_per_iter,
    spec.output_tiles_per_iter,
    spec.tile_k_per_iter,
  )
  for off, value in enumerate(const_words):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off, reg in enumerate((start_lo, start_hi, end_lo, end_hi, sink), start=len(const_words)):
    fw.sw(reg, s2, off * 4)
  fw.li(t0, 1 if spec.include_drain else 0)
  fw.sw(t0, s2, 13 * 4)
  fw.sw(zero, s2, 14 * 4)
  fw.sw(zero, s2, 15 * 4)
  return fw


def emit_drain(fw: MathBenchKernel):
  fw.emit(TTSTALLWAIT(TensixStall.SYNC, TensixWait.MATH | TensixWait.SFPU))
  return fw.tensix_sync(1, tmp=s1)


def replay_load(variant: int):
  return (
    matmul.MATMUL_MATH_REPLAY_LOAD_THROTTLE0
    if variant == VARIANT_THROTTLE0
    else matmul.MATMUL_MATH_REPLAY_LOAD
  )


def mop_cfg(variant: int):
  return (
    matmul.MATMUL_MATH_MOP_CFG_THROTTLE0
    if variant == VARIANT_THROTTLE0
    else matmul.MATMUL_MATH_MOP_CFG
  )


def emit_program_mop(fw: MathBenchKernel, variant: int):
  matmul.matmul_math_addrmod_init(fw)
  load = replay_load(variant)
  fw.emit(TTREPLAY(16, len(load), 0, 1))
  for word in load:
    fw.emit(word)
  fw.write_mop_cfg(mop_cfg(variant), 1)
  return fw.emit(TTSETRWC(0, 0, 0, 0, 0, 15))


def emit_math_init(fw: MathBenchKernel, variant: int):
  fw.math._local_state(fw, Dtype.Float16_b)
  emit_program_mop(fw, variant)
  fw.tensix_sync(1)
  fw.wait_mmio_low_byte_zero(TensixRegs.pc_buf_sem(TensixSem.MATH_PACK))
  fw.emit(TTSEMINIT(sem_sel=TensixSem.mask(TensixSem.MATH_PACK), init_value=0, max_value=2))
  emit_program_mop(fw, variant)
  fw.push_tensix_word(TensixRegs.INSTRN_BUF_BASE, matmul.TTSETC16(matmul.ThreadCfg.DEST_TARGET_REG_CFG_MATH_Offset, 0).raw_word())
  fw.push_tensix_word(TensixRegs.INSTRN_BUF_BASE, matmul.TTRMWCIB0(Mask=0x08, Data=0x08, CfgRegAddr=Cfg.DEST_ACCESS_CFG.addr32).raw_word())
  fw.emit(TTSTALLWAIT(TensixStall.CFG, TensixWait.MATH))
  return fw


def emit_prep_src(fw: MathBenchKernel):
  for word in MATH_PREP_WORDS:
    fw.emit(word)
  return emit_drain(fw)


def emit_one_output_tile(fw: MathBenchKernel, variant: int, tile_index: int = 0):
  matmul.emit_math_dst_base_addr(fw, t3)
  if tile_index:
    fw.addi(t3, t3, tile_index * 64)
  fw.write32(TensixRegs.INSTRN_BUF_BASE, t3)
  if variant == VARIANT_THROTTLE0:
    fw.emit(matmul.TTMOP(1, 0, 0))
  else:
    fw.emit(matmul.TTMOP(1, 0, 0))
    fw.emit(matmul.TTMOP(1, 0, 0))
    fw.emit(TTSETRWC(1, 0, 0, 0, 0, 15))
  return fw


def emit_subblock_body(fw: MathBenchKernel, variant: int):
  matmul.emit_math_dst_base_addr(fw, t3)
  for tile_index in range(4):
    fw.mv(t1, t3)
    if tile_index:
      fw.addi(t1, t1, tile_index * 64)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, t1)
    if variant == VARIANT_THROTTLE0:
      fw.emit(matmul.TTMOP(1, 0, 0))
    else:
      fw.emit(matmul.TTMOP(1, 0, 0))
      fw.emit(matmul.TTMOP(1, 0, 0))
      fw.emit(TTSETRWC(1, 0, 0, 0, 0, 15))
    if tile_index % 2 == 1:
      fw.emit(TTSETRWC(2, 0, 0, 0, 0, 15))
  return fw


def emit_spec_body(fw: MathBenchKernel, spec: BenchSpec):
  if spec.name == "empty":
    return fw.li(s1, 0x4D0B0000)
  if spec.name == "sync_empty":
    return emit_drain(fw)
  if spec.name == "prep_src":
    return emit_prep_src(fw)
  if spec.group == "init":
    return emit_math_init(fw, spec.variant)
  if spec.group == "program_mop":
    return emit_program_mop(fw, spec.variant)
  if spec.group == "mop_tile":
    emit_prep_src(fw)
    emit_one_output_tile(fw, spec.variant)
    return emit_drain(fw)
  if spec.group == "subblock":
    for _ in range(spec.repeats):
      for tile_index in range(4):
        emit_prep_src(fw)
        emit_one_output_tile(fw, spec.variant, tile_index)
        emit_drain(fw)
    return fw
  raise ValueError(spec.name)


def emit_timed_loop(fw: MathBenchKernel, *, test_id: int, spec: BenchSpec, iterations: int):
  read_wall_clock(fw, a2, a3)
  fw.li(s0, iterations)
  loop = fw._new_label(f"bench_{spec.name}")
  done = fw._new_label(f"bench_{spec.name}_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  emit_spec_body(fw, spec)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  read_wall_clock(fw, a4, a5)
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


def build_bench_kernel(iterations: int) -> MathBenchKernel:
  fw = MathBenchKernel()
  fw.math = matmul.MatmulTrisc(1).math
  fw.data = matmul.MatmulTrisc(1).data
  fw.data["dest_offset_id"] = 0xFFB00080
  emit_header(fw, iterations=iterations, status=STATUS_STARTED)
  fw.write32(fw.data["dest_offset_id"], 0)
  for test_id, spec in enumerate(SPECS):
    emit_timed_loop(fw, test_id=test_id, spec=spec, iterations=iterations)
  emit_header(fw, iterations=iterations, status=STATUS_DONE)
  return fw.ret()


def build_program(iterations: int) -> Program:
  empty = KernelBase()
  program = Program(
    brisc=empty,
    ncrisc=empty,
    trisc0=empty,
    trisc1=build_bench_kernel(iterations),
    trisc2=empty,
    num_cores=1,
  )
  program.name = "microbench_math_backend"
  return program


def clear_results(device: Device, core: tuple[int, int]):
  result_range = debug_ranges()[0]
  device.dev.set_power_state(True)
  try:
    with TLBWindow(device.dev, start=core) as win:
      win.write(result_range.address, b"\0" * result_range.size)
  finally:
    device.dev.set_power_state(False)


def read_results(device: Device, core: tuple[int, int]) -> bytes:
  result_range = debug_ranges()[0]
  device.dev.set_power_state(True)
  try:
    with TLBWindow(device.dev, start=core) as win:
      blob = win.read(result_range.address, result_range.size)
  finally:
    device.dev.set_power_state(False)
  if blob and all(b == 0xFF for b in blob):
    raise RuntimeError("L1 readback returned all 0xff; device likely needs reset/reboot")
  return blob


def parse_results(blob: bytes) -> list[Record]:
  header = struct.unpack_from("<" + "I" * HEADER_WORDS, blob, 0)
  if header[0] != RESULT_MAGIC:
    raise RuntimeError(f"bad result magic 0x{header[0]:08x}")
  if header[3] != STATUS_DONE:
    raise RuntimeError(f"benchmark did not finish, status=0x{header[3]:08x}")
  records = []
  for test_id, spec in enumerate(SPECS):
    off = HEADER_SIZE + test_id * RECORD_SIZE
    words = struct.unpack_from("<" + "I" * RECORD_WORDS, blob, off)
    if words[0] != RECORD_MAGIC:
      raise RuntimeError(f"{spec.name}: bad record magic 0x{words[0]:08x}")
    start = words[8] | (words[9] << 32)
    end = words[10] | (words[11] << 32)
    records.append(Record(
      test_id=words[1],
      name=spec.name,
      group=spec.group,
      variant=words[2],
      iterations=words[3],
      repeats=words[4],
      mops_per_iter=words[5],
      output_tiles_per_iter=words[6],
      tile_k_per_iter=words[7],
      start=start,
      end=end,
      cycles=(end - start) & ((1 << 64) - 1),
      sink=words[12],
    ))
  return records


def _record_map(records: list[Record]) -> dict[str, Record]:
  return {record.name: record for record in records}


def adjusted_cycles(record: Record, baseline: Record) -> float:
  return record.cycles_per_iter - baseline.cycles_per_iter


def metric_rows(records: list[Record]) -> list[dict[str, str]]:
  by_name = _record_map(records)
  empty = by_name["empty"]
  rows = []
  for record in records:
    adj = adjusted_cycles(record, empty)
    us = adj / AICLK_MHZ
    row = {
      "test": record.name,
      "variant": VARIANT_NAMES.get(record.variant, str(record.variant)),
      "group": record.group,
      "cycles/iter": f"{record.cycles_per_iter:.2f}",
      "adj cycles": f"{adj:.2f}",
      "adj us": f"{us:.4f}",
      "cycles/MOP": "",
      "cycles/tile-K": "",
      "cycles/subblock": "",
    }
    if record.mops_per_iter:
      row["cycles/MOP"] = f"{adj / record.mops_per_iter:.2f}"
    if record.tile_k_per_iter:
      row["cycles/tile-K"] = f"{adj / record.tile_k_per_iter:.2f}"
    if record.group == "subblock":
      row["cycles/subblock"] = f"{adj / record.repeats:.2f}"
    rows.append(row)
  return rows


def proposed_constants(records: list[Record]) -> dict[str, float]:
  by_name = _record_map(records)
  empty = by_name["empty"]
  constants = {}
  for name in ("subblock_unthrottled", "subblock_throttle0", "mop_tile_unthrottled", "mop_tile_throttle0"):
    if name not in by_name:
      continue
    record = by_name[name]
    adj = adjusted_cycles(record, empty)
    if record.group == "subblock":
      constants[f"{name}_cycles_per_subblock"] = adj / record.repeats
    if record.group == "mop_tile":
      constants[f"{name}_cycles_per_output_tile_k"] = adj / max(1, record.tile_k_per_iter)
  if "mop_tile_unthrottled_cycles_per_output_tile_k" in constants:
    constants["program_timing_model_TRISC_CYCLES_PER_SUBBLOCK"] = 4.0 * constants["mop_tile_unthrottled_cycles_per_output_tile_k"]
  elif "subblock_unthrottled_cycles_per_subblock" in constants:
    constants["program_timing_model_TRISC_CYCLES_PER_SUBBLOCK"] = constants["subblock_unthrottled_cycles_per_subblock"]
  return constants


def format_table(records: list[Record]) -> str:
  rows = metric_rows(records)
  headings = ("test", "variant", "group", "cycles/iter", "adj cycles", "adj us", "cycles/MOP", "cycles/tile-K", "cycles/subblock")
  lines = [
    "| " + " | ".join(headings) + " |",
    "|---|---|---|---:|---:|---:|---:|---:|---:|",
  ]
  for row in rows:
    lines.append("| " + " | ".join(row[h] for h in headings) + " |")
  return "\n".join(lines)


def format_constants(records: list[Record]) -> str:
  constants = proposed_constants(records)
  lines = [
    "| constant | cycles | us @ 1.35 GHz |",
    "|---|---:|---:|",
  ]
  for name, value in constants.items():
    lines.append(f"| `{name}` | {value:.2f} | {value / AICLK_MHZ:.4f} |")
  return "\n".join(lines)


def append_report(path: Path, *, core: tuple[int, int], iterations: int, command: str, records: list[Record]):
  now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
  with path.open("a", encoding="utf-8") as f:
    f.write(f"\n## Run {now}\n\n")
    f.write(f"- Command: `{command}`\n")
    f.write(f"- Core: logical `{core[0]},{core[1]}`\n")
    f.write(f"- Iterations per test: `{iterations}`\n")
    f.write("- Dispatch path: slow dispatch (`TT_USB=1`), one active TRISC1 role\n")
    f.write("- Drain marker: `PC_BUF_SYNC` plus `TTSTALLWAIT(SYNC, MATH|SFPU)` for math rows\n")
    f.write("- Math sequence: `examples/matmul_peak.py` matmul MOP cfg/replay payloads\n\n")
    f.write(format_table(records))
    f.write("\n\nProposed constants:\n\n")
    f.write(format_constants(records))
    f.write("\n")


def run_active_specs(device: Device, core: tuple[int, int], iterations: int, active_specs: tuple[BenchSpec, ...]) -> list[Record]:
  global SPECS
  old_specs = SPECS
  try:
    SPECS = active_specs
    print(f"running {','.join(spec.name for spec in active_specs)} iters={iterations}", flush=True)
    clear_results(device, core)
    device.run(build_program(iterations))
    return parse_results(read_results(device, core))
  finally:
    SPECS = old_specs


def run_isolated(device: Device, core: tuple[int, int], iterations: int, selected_specs: tuple[BenchSpec, ...]) -> list[Record]:
  empty = next(spec for spec in SPECS_ALL if spec.name == "empty")
  records: list[Record] = []
  if any(spec.name == "empty" for spec in selected_specs):
    records.extend(run_active_specs(device, core, iterations, (empty,)))
  else:
    records.extend(run_active_specs(device, core, iterations, (empty,)))
  for spec in selected_specs:
    if spec.name == "empty":
      continue
    active_iterations = iterations if spec.group in {"sync", "prep"} else 1
    active = (empty, spec)
    row_records = run_active_specs(device, core, active_iterations, active)
    records.append(next(record for record in row_records if record.name == spec.name))
  return records


def command_line(args) -> str:
  parts = ["PYTHONPATH=.", "TT_USB=1", sys.executable, "examples/microbench_math_backend.py", "--iters", str(args.iters)]
  if args.core is not None:
    parts += ["--core", f"{args.core[0]},{args.core[1]}"]
  if args.tests:
    parts += ["--tests", ",".join(args.tests)]
  if args.no_report:
    parts += ["--no-report"]
  return " ".join(parts)


def main() -> None:
  parser = argparse.ArgumentParser(description="Microbenchmark Blackhole TRISC1 math backend matmul MOP/replay costs.")
  parser.add_argument("--core", type=parse_core, default=None, help="logical Tensix core X,Y; default: first program core")
  parser.add_argument("--iters", type=int, default=100, help="iterations per timed loop")
  parser.add_argument("--tests", type=lambda s: tuple(x for x in s.split(",") if x), default=None, help="comma-separated test names for smoke/bisect runs")
  parser.add_argument("--no-report", action="store_true", help="do not append docs/math-backend-microbench.md")
  parser.add_argument("--report", type=Path, default=Path("docs/math-backend-microbench.md"), help="markdown report path")
  args = parser.parse_args()
  if args.iters <= 0:
    raise ValueError("--iters must be positive")
  global SPECS
  if args.tests:
    wanted = set(args.tests)
    unknown = wanted - {spec.name for spec in SPECS_ALL}
    if unknown:
      raise ValueError(f"unknown --tests entries: {', '.join(sorted(unknown))}")
    SPECS = tuple(spec for spec in SPECS_ALL if spec.name in wanted)
    if "empty" not in {spec.name for spec in SPECS}:
      SPECS = (next(spec for spec in SPECS_ALL if spec.name == "empty"), *SPECS)

  os.environ.setdefault("TT_USB", "1")
  device = Device()
  try:
    core = args.core or device.cores[0]
    records = run_isolated(device, core, args.iters, SPECS)
  finally:
    device.close()

  print(format_table(records))
  print("\nProposed constants:")
  print(format_constants(records))
  subblocks = [
    proposed_constants(records)[key]
    for key in proposed_constants(records)
    if key.endswith("_cycles_per_subblock")
  ]
  if subblocks:
    print(f"\nsubblock mean={statistics.mean(subblocks):.2f} cycles across variants")
  if not args.no_report:
    append_report(args.report, core=core, iterations=args.iters, command=command_line(args), records=records)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
