#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as _dt
import math
import statistics
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402  (does sys.path + TT_USB bootstrap on import)
import add1

from asm import KernelBase
from device import Device
from dsl import (
  TTSETRWC,
  TTSTALLWAIT,
  a2, a3, a4, a5, a6, a7,
  s0, s1, s2, s3, s4, s5, s6,
  t0, t1, t2, t3, zero,
)
from program import Dtype, Program
from ttk.debug import DebugRange
from ttk.math import Math
from ttk.sfpu import (
  DEFAULT_TILE_WALK,
  SfpuTranscendentalOp,
  emit_constant_tile,
  emit_transcendental_tile,
)
from ttk.tensix import Tensix, TensixMMIO, TensixRegs, TensixStall, TensixWait


AICLK_MHZ = 800.0
RESULT_BASE = 0x12A000
READBACK_BASE = RESULT_BASE + 0x1000
READBACK_WORDS = 64
RISCV_DEBUG_REG_DBG_ARRAY_RD_EN = 0xFFB12060
RISCV_DEBUG_REG_DBG_ARRAY_RD_CMD = 0xFFB12064
RISCV_DEBUG_REG_DBG_ARRAY_RD_DATA = 0xFFB1206C
DBG_ARRAY_ID_DEST = 2
HEADER_WORDS = 16
RECORD_WORDS = 16
HEADER_SIZE = HEADER_WORDS * 4
RECORD_SIZE = RECORD_WORDS * 4
RESULT_MAGIC = 0x53504648  # "HFPS"
RECORD_MAGIC = 0x53504652  # "RFPS"
STATUS_STARTED = 0x5F001001
STATUS_DONE = 0x5F00D00D

MODE_ISSUE = 0
MODE_LATENCY = 1
MODE_THROUGHPUT = 2
MODE_VALIDATE = 3
MODE_NAMES = {
  MODE_ISSUE: "issue",
  MODE_LATENCY: "latency",
  MODE_THROUGHPUT: "throughput",
  MODE_VALIDATE: "validate",
}

VALIDATION_INPUTS = {
  "exp": 0.0,
  "rsqrt": 1.0,
  "recip": 2.0,
  "sigmoid": 0.0,
  "silu": 0.0,
}
VALIDATION_REFS = {
  "exp": 1.0,
  "rsqrt": 1.0,
  "recip": 0.5,
  "sigmoid": 0.5,
  "silu": 0.0,
}


@dataclass(frozen=True)
class BenchSpec:
  name: str
  op: str
  mode: int
  tiles_per_iter: int
  include_drain: bool = True
  include_readback: bool = False


OP_NAMES = tuple(op.value for op in SfpuTranscendentalOp)
SPECS_ALL = (
  BenchSpec("empty", "none", MODE_ISSUE, 0, include_drain=False),
  BenchSpec("sync_empty", "none", MODE_LATENCY, 0),
  *tuple(BenchSpec(f"{op}_issue", op, MODE_ISSUE, 1, include_drain=False) for op in OP_NAMES),
  *tuple(BenchSpec(f"{op}_latency", op, MODE_LATENCY, 1) for op in OP_NAMES),
  *tuple(BenchSpec(f"{op}_throughput", op, MODE_THROUGHPUT, 8) for op in OP_NAMES),
  *tuple(BenchSpec(f"{op}_validate", op, MODE_VALIDATE, 1, include_readback=True) for op in OP_NAMES),
)
SPECS = SPECS_ALL


@dataclass(frozen=True)
class Record:
  test_id: int
  name: str
  op: str
  mode: int
  iterations: int
  tiles_per_iter: int
  start: int
  end: int
  cycles: int
  sink: int
  readback_word0: int
  expected_bf16: int
  validation_ok: bool

  @property
  def cycles_per_iter(self) -> float:
    return self.cycles / self.iterations


class SfpuBenchKernel(KernelBase, Tensix):
  pass


def bf16_bits(value: float) -> int:
  word = struct.unpack("<I", struct.pack("<f", float(value)))[0]
  return (word >> 16) & 0xFFFF


def result_size() -> int:
  return HEADER_SIZE + len(SPECS) * RECORD_SIZE


def debug_ranges() -> tuple[DebugRange, ...]:
  return (
    DebugRange(0, "l1", RESULT_BASE, result_size(), "sfpu_microbench_results"),
    DebugRange(1, "l1", READBACK_BASE, READBACK_WORDS * 4, "sfpu_dest_readback_words"),
  )


def emit_header(fw: KernelBase, *, iterations: int, status: int):
  fw.li(s2, RESULT_BASE)
  values = (
    RESULT_MAGIC, len(SPECS), RECORD_WORDS, status, iterations, RESULT_BASE, result_size(), READBACK_BASE,
  )
  for off, value in enumerate(values):
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
  fw.li(s2, RESULT_BASE + HEADER_SIZE + test_id * RECORD_SIZE)
  op_index = OP_NAMES.index(spec.op) if spec.op in OP_NAMES else 0xFFFFFFFF
  expected = bf16_bits(VALIDATION_REFS[spec.op]) if spec.op in VALIDATION_REFS else 0
  const_words = (
    RECORD_MAGIC,
    test_id,
    op_index,
    spec.mode,
    iterations,
    spec.tiles_per_iter,
    1 if spec.include_drain else 0,
    1 if spec.include_readback else 0,
  )
  for off, value in enumerate(const_words):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off, reg in enumerate((start_lo, start_hi, end_lo, end_hi, sink), start=len(const_words)):
    fw.sw(reg, s2, off * 4)
  fw.li(t0, expected)
  fw.sw(t0, s2, 13 * 4)
  if spec.include_readback:
    fw.lw(t1, s6, 0)
    fw.sw(t1, s2, 14 * 4)
    fw.slli(t2, t1, 16)
    fw.srli(t2, t2, 16)
    fw.li(t3, expected)
    ok = fw._new_label("sfpu_validate_ok")
    done = fw._new_label("sfpu_validate_done")
    fw.beq(t2, t3, ok)
    fw.sw(zero, s2, 15 * 4)
    fw.j(done)
    fw.label(ok)
    fw.li(t0, 1)
    fw.sw(t0, s2, 15 * 4)
    fw.label(done)
  else:
    fw.sw(zero, s2, 14 * 4)
    fw.sw(zero, s2, 15 * 4)
  return fw


def emit_drain(fw: SfpuBenchKernel):
  fw.emit(TTSTALLWAIT(TensixStall.SYNC, TensixWait.SFPU))
  return fw.tensix_sync(1, tmp=s1)


def emit_reset_rwc(fw: SfpuBenchKernel):
  return fw.emit(TTSETRWC(0, 0, 0, 0, 0, 15))


def emit_seed_tile(fw: SfpuBenchKernel, op: str):
  emit_reset_rwc(fw)
  emit_constant_tile(fw, VALIDATION_INPUTS[op])
  return emit_drain(fw)


def emit_dest_readback(fw: SfpuBenchKernel, *, l1_addr: int = READBACK_BASE, words: int = READBACK_WORDS):
  # DEDUPE: shares logic with ttk dest-readback once a common helper lands.
  #
  # The debug path is intentionally kept outside timed rows. Blackhole exposes
  # Dest through DBG_ARRAY_RD_{EN,CMD,DATA}; MOVDBGA2D is the companion LLK uses
  # when the requested source is SrcA and must be staged into Dest first.
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_DEST_CG_CTRL, 0)
  fw.write32(RISCV_DEBUG_REG_DBG_ARRAY_RD_EN, 1)
  for idx in range(min(words, 8)):
    cmd = (DBG_ARRAY_ID_DEST << 16) | (idx << 12)
    fw.write32(RISCV_DEBUG_REG_DBG_ARRAY_RD_CMD, cmd)
    fw.delay_cycles(5)
    fw.read32(t1, RISCV_DEBUG_REG_DBG_ARRAY_RD_DATA)
    fw.write32(l1_addr + idx * 4, t1)
  fw.write32(RISCV_DEBUG_REG_DBG_ARRAY_RD_CMD, 0)
  fw.write32(RISCV_DEBUG_REG_DBG_ARRAY_RD_EN, 0)
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_DEST_CG_CTRL, 0)
  fw.li(s6, l1_addr)
  return fw


def emit_op_tiles(fw: SfpuBenchKernel, op: str, tiles: int):
  for _ in range(tiles):
    emit_reset_rwc(fw)
    emit_transcendental_tile(fw, SfpuTranscendentalOp(op), walk=DEFAULT_TILE_WALK)
  return fw


def emit_spec_body(fw: SfpuBenchKernel, spec: BenchSpec):
  if spec.name == "empty":
    return fw.li(s1, 0x5F000000)
  if spec.name == "sync_empty":
    return emit_drain(fw)
  if spec.op not in OP_NAMES:
    raise ValueError(spec.name)
  emit_seed_tile(fw, spec.op)
  emit_op_tiles(fw, spec.op, spec.tiles_per_iter)
  if spec.include_drain:
    emit_drain(fw)
  if spec.include_readback:
    emit_dest_readback(fw)
  return fw


def emit_timed_loop(fw: SfpuBenchKernel, *, test_id: int, spec: BenchSpec, iterations: int):
  harness.read_wall_clock(fw, a2, a3)
  for _ in range(iterations):
    emit_spec_body(fw, spec)
  harness.read_wall_clock(fw, a4, a5)
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


def build_bench_kernel(iterations: int) -> SfpuBenchKernel:
  fw = SfpuBenchKernel()
  fw.math = Math(fw)
  fw.data = {"dest_offset_id": 0xFFB00080}
  emit_header(fw, iterations=iterations, status=STATUS_STARTED)
  fw.zero_words(READBACK_BASE, READBACK_WORDS)
  fw.write32(fw.data["dest_offset_id"], 0)
  fw.math.init(dtype=Dtype.Float16_b, mop_cfg=add1.MATH_MOP_CFG)
  emit_drain(fw)
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
  program.name = "microbench_sfpu"
  return program


def clear_results(device: Device, core: tuple[int, int]):
  ranges = debug_ranges()
  size = max(r.address + r.size for r in ranges) - min(r.address for r in ranges)
  base = min(r.address for r in ranges)
  with harness.device_window(device, core) as win:
    win.write(base, b"\0" * size)


def read_results(device: Device, core: tuple[int, int]) -> bytes:
  result_range = debug_ranges()[0]
  with harness.device_window(device, core) as win:
    blob = win.read(result_range.address, result_range.size)
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
      op=spec.op,
      mode=words[3],
      iterations=words[4],
      tiles_per_iter=words[5],
      start=start,
      end=end,
      cycles=(end - start) & ((1 << 64) - 1),
      sink=words[12],
      expected_bf16=words[13],
      readback_word0=words[14],
      validation_ok=bool(words[15]),
    ))
  return records


def adjusted_cycles(record: Record, baseline: Record) -> float:
  return record.cycles_per_iter - baseline.cycles_per_iter


def _record_map(records: list[Record]) -> dict[str, Record]:
  return {record.name: record for record in records}


def op_metrics(records: list[Record]) -> list[dict[str, str]]:
  by_name = _record_map(records)
  empty = by_name["empty"]
  rows = []
  for op in OP_NAMES:
    issue = by_name.get(f"{op}_issue")
    latency = by_name.get(f"{op}_latency")
    throughput = by_name.get(f"{op}_throughput")
    validate = by_name.get(f"{op}_validate")
    if not issue or not latency or not throughput:
      continue
    issue_cycles = adjusted_cycles(issue, empty)
    latency_cycles = adjusted_cycles(latency, empty)
    throughput_cycles = adjusted_cycles(throughput, empty) / max(1, throughput.tiles_per_iter)
    rows.append({
      "op": op,
      "issue cyc/tile": f"{issue_cycles:.2f}",
      "latency cyc/tile": f"{latency_cycles:.2f}",
      "throughput cyc/tile": f"{throughput_cycles:.2f}",
      "throughput us/tile": f"{throughput_cycles / AICLK_MHZ:.4f}",
      "validation": (
        "pass"
        if validate and validate.validation_ok
        else ("fail" if validate else "")
      ),
    })
  return rows


def format_table(records: list[Record]) -> str:
  rows = op_metrics(records)
  headings = ("op", "issue cyc/tile", "latency cyc/tile", "throughput cyc/tile", "throughput us/tile", "validation")
  lines = [
    "| " + " | ".join(headings) + " |",
    "|---|---:|---:|---:|---:|---|",
  ]
  for row in rows:
    lines.append("| " + " | ".join(row[h] for h in headings) + " |")
  return "\n".join(lines)


def format_raw_records(records: list[Record]) -> str:
  empty = _record_map(records).get("empty")
  headings = ("test", "mode", "cycles/iter", "adj cycles", "tiles/iter", "readback", "expected", "ok")
  lines = [
    "| " + " | ".join(headings) + " |",
    "|---|---|---:|---:|---:|---:|---:|---|",
  ]
  for record in records:
    adj = adjusted_cycles(record, empty) if empty else math.nan
    lines.append(
      f"| {record.name} | {MODE_NAMES.get(record.mode, str(record.mode))} | "
      f"{record.cycles_per_iter:.2f} | {adj:.2f} | {record.tiles_per_iter} | "
      f"0x{record.readback_word0:08x} | 0x{record.expected_bf16:04x} | "
      f"{'yes' if record.validation_ok else ''} |"
    )
  return "\n".join(lines)


def append_report(path: Path, *, core: tuple[int, int], iterations: int, command: str, records: list[Record]):
  now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
  with path.open("a", encoding="utf-8") as f:
    f.write(f"\n## Run {now}\n\n")
    f.write(f"- Command: `{command}`\n")
    f.write(f"- Core: logical `{core[0]},{core[1]}`\n")
    f.write(f"- Iterations per timed row: `{iterations}`\n")
    f.write("- Dispatch path: slow dispatch (`TT_USB=1`), one active TRISC1 role\n")
    f.write("- Methodology: issue, completion latency, and steady-state throughput rows per op\n")
    f.write("- Completion: `TTSTALLWAIT(SYNC, SFPU)` plus `PC_BUF_SYNC`\n")
    f.write("- Validation: local Dest debug readback using `TTMOVDBGA2D` and `DEST_CG_CTRL`\n\n")
    f.write(format_table(records))
    f.write("\n\nRaw records:\n\n")
    f.write(format_raw_records(records))
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
  records = run_active_specs(device, core, iterations, (empty,))
  for spec in selected_specs:
    if spec.name == "empty":
      continue
    active_iters = iterations
    if spec.mode in {MODE_LATENCY, MODE_VALIDATE}:
      active_iters = 1
    row_records = run_active_specs(device, core, active_iters, (empty, spec))
    records.append(next(record for record in row_records if record.name == spec.name))
  return records


def command_line(args) -> str:
  parts = ["PYTHONPATH=.", "TT_USB=1", sys.executable, "microbenching/microbench_sfpu.py", "--iters", str(args.iters)]
  if args.core is not None:
    parts += ["--core", f"{args.core[0]},{args.core[1]}"]
  if args.ops:
    parts += ["--ops", ",".join(args.ops)]
  if args.tests:
    parts += ["--tests", ",".join(args.tests)]
  if args.no_report:
    parts += ["--no-report"]
  return " ".join(parts)


def selected_specs(args) -> tuple[BenchSpec, ...]:
  specs = SPECS_ALL
  if args.ops:
    wanted_ops = set(args.ops)
    specs = tuple(spec for spec in specs if spec.op == "none" or spec.op in wanted_ops)
  if args.tests:
    wanted = set(args.tests)
    unknown = wanted - {spec.name for spec in SPECS_ALL}
    if unknown:
      raise ValueError(f"unknown --tests entries: {', '.join(sorted(unknown))}")
    specs = tuple(spec for spec in SPECS_ALL if spec.name in wanted)
  return specs


def main() -> None:
  parser = argparse.ArgumentParser(description="Microbenchmark Blackhole TRISC1 SFPU transcendental tile ops.")
  parser.add_argument("--core", type=harness.parse_core, default=None, help="logical Tensix core X,Y; default: first program core")
  parser.add_argument("--iters", type=int, default=4, help="iterations for issue/throughput rows")
  parser.add_argument("--ops", type=lambda s: tuple(x for x in s.split(",") if x), default=None, help="comma-separated ops: exp,rsqrt,recip,sigmoid,silu")
  parser.add_argument("--tests", type=lambda s: tuple(x for x in s.split(",") if x), default=None, help="comma-separated test names for smoke/bisect runs")
  parser.add_argument("--build-only", action="store_true", help="build Program/assembly and exit without opening the device")
  parser.add_argument("--no-report", action="store_true", help="do not append docs/sfpu-microbench.md")
  parser.add_argument("--report", type=Path, default=Path("microbenching/docs/sfpu-microbench.md"), help="markdown report path")
  args = parser.parse_args()
  if args.iters <= 0:
    raise ValueError("--iters must be positive")
  if args.ops:
    unknown = set(args.ops) - set(OP_NAMES)
    if unknown:
      raise ValueError(f"unknown --ops entries: {', '.join(sorted(unknown))}")

  global SPECS
  SPECS = selected_specs(args)
  if "empty" not in {spec.name for spec in SPECS}:
    SPECS = (next(spec for spec in SPECS_ALL if spec.name == "empty"), *SPECS)

  if args.build_only:
    old_specs = SPECS
    try:
      rows = [next(spec for spec in SPECS_ALL if spec.name == "empty")]
      rows.extend(spec for spec in SPECS if spec.name != "empty")
      max_size = 0
      for spec in rows:
        active = (rows[0],) if spec.name == "empty" else (rows[0], spec)
        globals()["SPECS"] = active
        prog = build_program(1 if spec.mode in {MODE_LATENCY, MODE_VALIDATE} else args.iters)
        size = sum(len(seg.data) for seg in prog.trisc1.compile())
        max_size = max(max_size, size)
      print(f"build ok: {len(rows)} isolated launches max_trisc1_bytes={max_size}")
    finally:
      SPECS = old_specs
    return

  with harness.open_device() as device:
    core = args.core or device.cores[0]
    records = run_isolated(device, core, args.iters, SPECS)

  print(format_table(records))
  print("\nRaw records:")
  print(format_raw_records(records))
  throughputs = []
  for row in op_metrics(records):
    try:
      throughputs.append(float(row["throughput cyc/tile"]))
    except ValueError:
      pass
  if throughputs:
    print(f"\nthroughput mean={statistics.mean(throughputs):.2f} cycles/tile across reported ops")
  if not args.no_report:
    append_report(args.report, core=core, iterations=args.iters, command=command_line(args), records=records)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
