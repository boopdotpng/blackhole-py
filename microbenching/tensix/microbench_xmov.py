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
  TTDMANOP, TTMOVA2D, TTMOVD2A, TTMOVD2B, TTMOVDBGA2D, TTMOVDBGB2D,
  TTRSTDMA, TTSETDMAREG, TTSHIFTDMAREG, TTSTALLWAIT, TTSETRWC, TTZEROACC,
  TTZEROSRC,
  a2, a3, a4, a5,
  s0, s1, s2, s3, s4, s5, s6, s7, s8,
  t0, t1, t2, t3, t4, t5, zero,
)
from program import Program
from ttk.debug import DebugRange
from ttk.tensix import Tensix, TensixMMIO, TensixRegs, TensixStall, TensixWait


AICLK_MHZ = 800.0
ROLE_INDEX = {"trisc0": 2, "trisc1": 3, "trisc2": 4}
ROLE_NAMES = tuple(ROLE_INDEX)

RESULT_BASE = 0x12A000
HEADER_WORDS = 16
RECORD_WORDS = 16
HEADER_SIZE = HEADER_WORDS * 4
RECORD_SIZE = RECORD_WORDS * 4
RESULT_MAGIC = 0x584D4248  # "HBMX" LE: XMOV bench header.
RECORD_MAGIC = 0x584D4252  # "RBMX" LE.
STATUS_STARTED = 0x584D0001
STATUS_DONE = 0x584DD00D

MODE_BASELINE = 0
MODE_SYNC = 1
MODE_ISSUE = 2
MODE_LATENCY = 3
MODE_THROUGHPUT = 4
MODE_READBACK = 5
MODE_NAMES = {
  MODE_BASELINE: "baseline",
  MODE_SYNC: "sync",
  MODE_ISSUE: "issue",
  MODE_LATENCY: "latency",
  MODE_THROUGHPUT: "throughput",
  MODE_READBACK: "readback",
}

WORD_REGS = (s4, s5, s6, t0, t1, t2, t3, t4)
STALLWAIT_XMOV_WORD = TTSTALLWAIT(TensixStall.SYNC, TensixWait.XMOV).raw_word()
STALLWAIT_PREP_WORD = TTSTALLWAIT(
  TensixStall.SYNC,
  TensixWait.MATH | TensixWait.SFPU | TensixWait.XMOV,
).raw_word()


def tt_raw(inst) -> int:
  return inst.raw_word() if hasattr(inst, "raw_word") else int(inst) & 0xFFFFFFFF


def _move_fields(i: int) -> dict[str, int]:
  return {
    "dest_32b_lo": 0,
    "src": i & 0x1F,
    "addr_mode": 0,
    "instr_mod": 0,
    "dst": (i * 16) & 0x7FF,
  }


def _moveb_fields(i: int) -> dict[str, int]:
  return {
    "dest_32b_lo": 0,
    "src": i & 0x1F,
    "addr_mode": 0,
    "movb2d_instr_mod": 0,
    "dst": (i * 16) & 0x7FF,
  }


def op_words(op: str, count: int) -> tuple[int, ...]:
  words = []
  for i in range(count):
    match op:
      case "ttmovd2a":
        words.append(tt_raw(TTMOVD2A(**_move_fields(i))))
      case "ttmova2d":
        words.append(tt_raw(TTMOVA2D(**_move_fields(i))))
      case "ttmovd2b":
        words.append(tt_raw(TTMOVD2B(**_move_fields(i))))
      case "ttmovdbga2d":
        words.append(tt_raw(TTMOVDBGA2D(**_move_fields(i))))
      case "ttmovdbgb2d":
        words.append(tt_raw(TTMOVDBGB2D(**_moveb_fields(i))))
      case "ttsetdmareg":
        words.append(tt_raw(TTSETDMAREG(0, i & 0x3FFF, 0, 24)))
      case "ttshiftdmareg":
        words.append(tt_raw(TTSHIFTDMAREG(1, 0, 24 + (i & 1), i & 0x3F, 24)))
      case "ttrstdma":
        words.append(tt_raw(TTRSTDMA()))
      case "ttdmanop":
        words.append(tt_raw(TTDMANOP()))
      case _:
        raise ValueError(op)
  return tuple(words)


@dataclass(frozen=True)
class OpDef:
  name: str
  group: str
  opcode: int


OPS = (
  OpDef("ttmovd2a", "move", 0x08),
  OpDef("ttmova2d", "move", 0x12),
  OpDef("ttmovd2b", "move", 0x0A),
  OpDef("ttmovdbga2d", "debug_move", 0x09),
  OpDef("ttmovdbgb2d", "debug_move", 0x0C),
  OpDef("ttsetdmareg", "dma_reg", 0x45),
  OpDef("ttshiftdmareg", "dma_reg", 0x5C),
  OpDef("ttrstdma", "dma_reg", 0x44),
  OpDef("ttdmanop", "dma_reg", 0x60),
)


@dataclass(frozen=True)
class BenchSpec:
  name: str
  op_name: str
  group: str
  mode: int
  opcode: int
  words: tuple[int, ...] = ()
  drain_each_iter: bool = False
  needs_prep: bool = False

  @property
  def ops_per_iter(self) -> int:
    return len(self.words)


def make_specs(batch: int, include_readback: bool) -> tuple[BenchSpec, ...]:
  specs: list[BenchSpec] = [
    BenchSpec("empty", "empty", "baseline", MODE_BASELINE, 0),
    BenchSpec("sync_empty", "sync_empty", "sync", MODE_SYNC, 0, drain_each_iter=True),
  ]
  for op in OPS:
    specs.extend((
      BenchSpec(
        f"{op.name}_issue",
        op.name,
        op.group,
        MODE_ISSUE,
        op.opcode,
        op_words(op.name, batch),
        drain_each_iter=False,
        needs_prep=op.group != "dma_reg",
      ),
      BenchSpec(
        f"{op.name}_latency",
        op.name,
        op.group,
        MODE_LATENCY,
        op.opcode,
        op_words(op.name, 1),
        drain_each_iter=True,
        needs_prep=op.group != "dma_reg",
      ),
      BenchSpec(
        f"{op.name}_throughput",
        op.name,
        op.group,
        MODE_THROUGHPUT,
        op.opcode,
        op_words(op.name, batch),
        drain_each_iter=True,
        needs_prep=op.group != "dma_reg",
      ),
    ))
  if include_readback:
    specs.append(BenchSpec(
      "dest_readback_probe",
      "ttmovdbga2d",
      "readback",
      MODE_READBACK,
      0x09,
      op_words("ttmovdbga2d", 1),
      drain_each_iter=True,
      needs_prep=True,
    ))
  return tuple(specs)


SPECS = make_specs(batch=8, include_readback=True)


@dataclass(frozen=True)
class Record:
  role: str
  test_id: int
  name: str
  op_name: str
  group: str
  mode: int
  opcode: int
  iterations: int
  ops_per_iter: int
  start: int
  end: int
  cycles: int
  sink: int
  check0: int
  check1: int

  @property
  def cycles_per_iter(self) -> float:
    return self.cycles / self.iterations

  @property
  def mode_name(self) -> str:
    return MODE_NAMES[self.mode]


class XmovBenchKernel(KernelBase, Tensix):
  pass


def result_size() -> int:
  return HEADER_SIZE + len(SPECS) * RECORD_SIZE


def debug_ranges() -> tuple[DebugRange, ...]:
  return (
    DebugRange(0, "l1", RESULT_BASE, result_size(), "xmov_microbench_results"),
  )


def emit_header(fw: KernelBase, *, role_id: int, iterations: int, status: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, role_id, len(SPECS), RECORD_WORDS, status, iterations, RESULT_BASE, result_size(),
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  return fw


def emit_record(
  fw: KernelBase,
  *,
  role_id: int,
  test_id: int,
  iterations: int,
  spec: BenchSpec,
  start_lo,
  start_hi,
  end_lo,
  end_hi,
  sink=s1,
  check0=zero,
  check1=zero,
):
  addr = RESULT_BASE + HEADER_SIZE + test_id * RECORD_SIZE
  fw.li(s2, addr)
  const_words = (
    RECORD_MAGIC,
    role_id,
    test_id,
    spec.mode,
    spec.opcode,
    iterations,
    spec.ops_per_iter,
    1 if spec.drain_each_iter else 0,
  )
  for off, value in enumerate(const_words):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off, reg in enumerate((start_lo, start_hi, end_lo, end_hi, sink, check0, check1), start=len(const_words)):
    fw.sw(reg, s2, off * 4)
  fw.sw(zero, s2, 15 * 4)
  return fw


def emit_drain_sync(fw: KernelBase, *, stall_reg=s7, instr_reg=s3, pc_sync_reg=s8):
  fw.sw(stall_reg, instr_reg, 0)
  fw.sw(zero, pc_sync_reg, 0)
  fw.lw(s1, pc_sync_reg, 0)
  return fw.and_(zero, zero, s1)


def emit_prep_drain(fw: KernelBase, *, stall_reg=s7, instr_reg=s3, pc_sync_reg=s8):
  fw.li(stall_reg, STALLWAIT_PREP_WORD)
  emit_drain_sync(fw, stall_reg=stall_reg, instr_reg=instr_reg, pc_sync_reg=pc_sync_reg)
  fw.li(stall_reg, STALLWAIT_XMOV_WORD)
  return fw


def emit_internal_state_prep(fw: XmovBenchKernel, spec: BenchSpec):
  if not spec.needs_prep:
    return fw
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_DEST_CG_CTRL, 0)
  fw.math_direct_mova2d_init()
  fw.emit(TTZEROSRC(0, 0, 1, 3))
  fw.emit(TTZEROACC(3, 0, 0, 1, 0))
  fw.emit(TTSETRWC(0, 0, 0, 0, 0, 15))
  return emit_prep_drain(fw)


def emit_readback_probe(fw: XmovBenchKernel):
  # DEDUPE: provisional local dest-readback hook; centralize once the debug
  # readback path is validated against a known matmul Dest value.
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_DEST_CG_CTRL, 0)
  fw.read32(t4, TensixMMIO.RISCV_DEBUG_REG_DEST_CG_CTRL)
  fw.li(t5, op_words("ttmovdbga2d", 1)[0])
  fw.sw(t5, s3, 0)
  emit_drain_sync(fw)
  fw.read32(t5, TensixMMIO.RISCV_DEBUG_REG_DEST_CG_CTRL)
  return fw


def emit_timed_loop(fw: XmovBenchKernel, *, role_id: int, test_id: int, iterations: int, spec: BenchSpec):
  fw.li(s1, 0x584D0000 | test_id)
  fw.li(s3, TensixRegs.INSTRN_BUF_BASE)
  fw.li(s8, TensixRegs.PC_BUF_SYNC)
  fw.li(s7, STALLWAIT_XMOV_WORD)
  emit_internal_state_prep(fw, spec)

  unique_words = tuple(dict.fromkeys(spec.words))
  if len(unique_words) > len(WORD_REGS):
    raise ValueError(f"{spec.name}: too many distinct Tensix words")
  word_to_reg = {}
  for word, reg in zip(unique_words, WORD_REGS):
    fw.li(reg, word)
    word_to_reg[word] = reg

  harness.read_wall_clock(fw, a2, a3)
  fw.li(s0, iterations)
  loop = fw._new_label(f"bench_{spec.name}")
  done = fw._new_label(f"bench_{spec.name}_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  if spec.mode == MODE_READBACK:
    emit_readback_probe(fw)
  else:
    for word in spec.words:
      fw.sw(word_to_reg[word], s3, 0)
  if spec.mode != MODE_READBACK and spec.drain_each_iter:
    emit_drain_sync(fw)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  harness.read_wall_clock(fw, a4, a5)
  if spec.words and not spec.drain_each_iter:
    emit_drain_sync(fw)
  if spec.mode == MODE_READBACK:
    emit_record(
      fw,
      role_id=role_id,
      test_id=test_id,
      iterations=iterations,
      spec=spec,
      start_lo=a2,
      start_hi=a3,
      end_lo=a4,
      end_hi=a5,
      check0=t4,
      check1=t5,
    )
  else:
    emit_record(
      fw,
      role_id=role_id,
      test_id=test_id,
      iterations=iterations,
      spec=spec,
      start_lo=a2,
      start_hi=a3,
      end_lo=a4,
      end_hi=a5,
    )
  return fw


def build_bench_kernel(role: str, iterations: int) -> XmovBenchKernel:
  role_id = ROLE_INDEX[role]
  fw = XmovBenchKernel()
  emit_header(fw, role_id=role_id, iterations=iterations, status=STATUS_STARTED)
  for test_id, spec in enumerate(SPECS):
    emit_timed_loop(fw, role_id=role_id, test_id=test_id, iterations=iterations, spec=spec)
  emit_header(fw, role_id=role_id, iterations=iterations, status=STATUS_DONE)
  return fw.ret()


def build_program(role: str, iterations: int) -> Program:
  empty = KernelBase()
  kernels = {"brisc": empty, "ncrisc": empty, "trisc0": empty, "trisc1": empty, "trisc2": empty}
  kernels[role] = build_bench_kernel(role, iterations)
  program = Program(**kernels, num_cores=1)
  program.name = f"microbench_xmov:{role}"
  return program


def clear_results(device: Device, core: tuple[int, int]):
  result_range = debug_ranges()[0]
  with harness.device_window(device, core) as win:
    win.write(result_range.address, b"\0" * result_range.size)


def read_results(device: Device, core: tuple[int, int]) -> bytes:
  result_range = debug_ranges()[0]
  with harness.device_window(device, core) as win:
    blob = win.read(result_range.address, result_range.size)
  if blob and all(b == 0xFF for b in blob):
    raise RuntimeError("L1 readback returned all 0xff; device likely needs reset/reboot")
  return blob


def parse_results(blob: bytes, role: str) -> list[Record]:
  header = struct.unpack_from("<" + "I" * HEADER_WORDS, blob, 0)
  if header[0] != RESULT_MAGIC:
    raise RuntimeError(f"{role}: bad result magic 0x{header[0]:08x}")
  if header[4] != STATUS_DONE:
    raise RuntimeError(f"{role}: benchmark did not finish, status=0x{header[4]:08x}")
  records = []
  for test_id, spec in enumerate(SPECS):
    off = HEADER_SIZE + test_id * RECORD_SIZE
    words = struct.unpack_from("<" + "I" * RECORD_WORDS, blob, off)
    if words[0] != RECORD_MAGIC:
      raise RuntimeError(f"{role}/{spec.name}: bad record magic 0x{words[0]:08x}")
    start = words[8] | (words[9] << 32)
    end = words[10] | (words[11] << 32)
    cycles = (end - start) & ((1 << 64) - 1)
    records.append(Record(
      role=role,
      test_id=words[2],
      name=spec.name,
      op_name=spec.op_name,
      group=spec.group,
      mode=words[3],
      opcode=words[4],
      iterations=words[5],
      ops_per_iter=words[6],
      start=start,
      end=end,
      cycles=cycles,
      sink=words[12],
      check0=words[13],
      check1=words[14],
    ))
  return records


def _record_map(records: list[Record]) -> dict[str, Record]:
  return {record.name: record for record in records}


def format_table(records: list[Record]) -> str:
  by_name = _record_map(records)
  empty = by_name.get("empty")
  sync_empty = by_name.get("sync_empty")
  empty_cpi = empty.cycles_per_iter if empty is not None else 0.0
  sync_adj = (sync_empty.cycles_per_iter - empty_cpi) if sync_empty is not None else 0.0
  headings = (
    "role", "test", "op", "mode", "ops/iter", "cycles/iter",
    "adj cycles", "cycles/op", "engine cycles/op", "us/op", "check",
  )
  lines = [
    "| " + " | ".join(headings) + " |",
    "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
  ]
  for record in records:
    cpi = record.cycles_per_iter
    adj = cpi - empty_cpi
    cycles_per_op = ""
    engine_cycles_per_op = ""
    us_per_op = ""
    if record.ops_per_iter:
      cycles = adj / record.ops_per_iter
      cycles_per_op = f"{cycles:.3f}"
      us_per_op = f"{cycles / AICLK_MHZ:.5f}"
      if record.mode == MODE_THROUGHPUT:
        engine_cycles_per_op = f"{(adj - sync_adj) / record.ops_per_iter:.3f}"
      elif record.mode == MODE_LATENCY:
        engine_cycles_per_op = f"{adj - sync_adj:.3f}"
    check = ""
    if record.mode == MODE_READBACK:
      check = f"0x{record.check0:08x}->0x{record.check1:08x}"
    lines.append(
      f"| {record.role} | {record.name} | {record.op_name} | {record.mode_name} | "
      f"{record.ops_per_iter} | {cpi:.3f} | {adj:.3f} | {cycles_per_op} | "
      f"{engine_cycles_per_op} | {us_per_op} | {check} |"
    )
  return "\n".join(lines)


def summary_rows(records: list[Record]) -> str:
  by_op: dict[str, dict[int, Record]] = {}
  by_name = _record_map(records)
  empty = by_name.get("empty")
  sync_empty = by_name.get("sync_empty")
  if empty is None or sync_empty is None:
    return ""
  empty_cpi = empty.cycles_per_iter
  sync_adj = sync_empty.cycles_per_iter - empty_cpi
  for r in records:
    if r.op_name in {"empty", "sync_empty"}:
      continue
    by_op.setdefault(r.op_name, {})[r.mode] = r
  lines = [
    "| op | issue cyc/op | latency cyc | steady cyc/op | steady engine cyc/op |",
    "|---|---:|---:|---:|---:|",
  ]
  for op in [op.name for op in OPS]:
    modes = by_op.get(op, {})
    issue = modes.get(MODE_ISSUE)
    latency = modes.get(MODE_LATENCY)
    throughput = modes.get(MODE_THROUGHPUT)
    def per_op(r: Record | None) -> str:
      if r is None or not r.ops_per_iter:
        return ""
      return f"{(r.cycles_per_iter - empty_cpi) / r.ops_per_iter:.3f}"
    lat = ""
    if latency is not None:
      lat = f"{latency.cycles_per_iter - empty_cpi:.3f}"
    steady_engine = ""
    if throughput is not None and throughput.ops_per_iter:
      steady_engine = f"{(throughput.cycles_per_iter - empty_cpi - sync_adj) / throughput.ops_per_iter:.3f}"
    lines.append(f"| `{op}` | {per_op(issue)} | {lat} | {per_op(throughput)} | {steady_engine} |")
  return "\n".join(lines)


def append_report(path: Path, *, role: str, core: tuple[int, int], iterations: int, batch: int, command: str, records: list[Record]):
  now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
  with path.open("a", encoding="utf-8") as f:
    f.write(f"\n## Run {now}\n\n")
    f.write(f"- Command: `{command}`\n")
    f.write(f"- Core: logical `{core[0]},{core[1]}`\n")
    f.write(f"- Active role: `{role}`\n")
    f.write(f"- Iterations per row: `{iterations}`\n")
    f.write(f"- Batch size for issue/throughput rows: `{batch}` ops\n")
    f.write("- Dispatch path: slow dispatch (`TT_USB=1`), one active TRISC role per launch\n")
    f.write("- Timed issue path: raw `sw word, 0(INSTRN_BUF_BASE)` pushes\n")
    f.write("- Completion edge: raw `TTSTALLWAIT(SYNC, XMOV)` followed by `PC_BUF_SYNC` write/read\n\n")
    f.write(summary_rows(records))
    f.write("\n\n")
    f.write(format_table(records))
    f.write("\n")


def run_active_specs(device: Device, role: str, core: tuple[int, int], iterations: int, active_specs: tuple[BenchSpec, ...]) -> list[Record]:
  global SPECS
  old_specs = SPECS
  try:
    SPECS = active_specs
    print(f"running {role}:{','.join(spec.name for spec in active_specs)} iters={iterations}", flush=True)
    clear_results(device, core)
    device.run(build_program(role, iterations))
    return parse_results(read_results(device, core), role)
  finally:
    SPECS = old_specs


def run_isolated(device: Device, role: str, core: tuple[int, int], iterations: int, selected_specs: tuple[BenchSpec, ...]) -> list[Record]:
  empty = next(spec for spec in SPECS if spec.name == "empty")
  records: list[Record] = []
  records.extend(run_active_specs(device, role, core, iterations, (empty,)))
  for spec in selected_specs:
    if spec.name == "empty":
      continue
    row_records = run_active_specs(device, role, core, iterations, (empty, spec))
    records.append(next(record for record in row_records if record.name == spec.name))
  return records


def command_line(args) -> str:
  parts = ["PYTHONPATH=.", "TT_USB=1", sys.executable, "microbenching/microbench_xmov.py"]
  parts += ["--role", args.role, "--iters", str(args.iters), "--batch", str(args.batch)]
  if args.core is not None:
    parts += ["--core", f"{args.core[0]},{args.core[1]}"]
  if args.tests:
    parts += ["--tests", ",".join(args.tests)]
  if args.no_readback_probe:
    parts += ["--no-readback-probe"]
  if args.no_report:
    parts += ["--no-report"]
  return " ".join(parts)


def main() -> None:
  parser = argparse.ArgumentParser(description="Microbenchmark Blackhole Tensix XMOV/TDMA internal mover ops.")
  parser.add_argument("--core", type=harness.parse_core, default=None, help="logical Tensix core X,Y; default: first program core")
  parser.add_argument("--role", choices=ROLE_NAMES, default="trisc1", help="TRISC role that issues the XMOV/TDMA instructions")
  parser.add_argument("--iters", type=int, default=8, help="iterations per timed row; keep small for isolated mover state")
  parser.add_argument("--batch", type=int, default=8, help="ops per issue/throughput row; max 8 distinct words")
  parser.add_argument("--tests", type=lambda s: tuple(x for x in s.split(",") if x), default=None, help="comma-separated test names for smoke/bisect runs")
  parser.add_argument("--no-readback-probe", action="store_true", help="omit the provisional DEST_CG_CTRL/TTMOVDBGA2D probe row")
  parser.add_argument("--no-report", action="store_true", help="do not append microbenching/docs/xmov-microbench.md")
  parser.add_argument("--report", type=Path, default=Path("microbenching/docs/xmov-microbench.md"), help="markdown report path")
  args = parser.parse_args()
  if args.iters <= 0:
    raise ValueError("--iters must be positive")
  if not 1 <= args.batch <= len(WORD_REGS):
    raise ValueError(f"--batch must be in [1, {len(WORD_REGS)}]")

  global SPECS
  SPECS = make_specs(args.batch, include_readback=not args.no_readback_probe)
  if args.tests:
    wanted = set(args.tests)
    unknown = wanted - {spec.name for spec in SPECS}
    if unknown:
      raise ValueError(f"unknown --tests entries: {', '.join(sorted(unknown))}")
    SPECS = tuple(spec for spec in SPECS if spec.name in wanted)
    if "empty" not in {spec.name for spec in SPECS}:
      SPECS = (next(spec for spec in make_specs(args.batch, include_readback=not args.no_readback_probe) if spec.name == "empty"), *SPECS)

  with harness.open_device() as device:
    core = args.core or device.cores[0]
    records = run_isolated(device, args.role, core, args.iters, SPECS)

  print(summary_rows(records))
  print()
  print(format_table(records))
  if not args.no_report:
    append_report(args.report, role=args.role, core=core, iterations=args.iters, batch=args.batch, command=command_line(args), records=records)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
