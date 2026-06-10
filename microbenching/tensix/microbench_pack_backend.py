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
import numpy as np

try:
  import matmul_peak as matmul
except ModuleNotFoundError:
  from examples import matmul_peak as matmul

from asm import KernelBase
from device import Device
from dsl import TTSEMINIT, TTZEROACC, a2, a3, a4, a5, s0, s1, s2, t0, t1, zero
from program import Dtype, Program
from ttk.debug import DebugRange
from ttk.tensix import TensixL1, TensixRegs, TensixSem


AICLK_MHZ = 800.0
RESULT_BASE = 0x12C000
HEADER_WORDS = 16
RECORD_WORDS = 16
HEADER_SIZE = HEADER_WORDS * 4
RECORD_SIZE = RECORD_WORDS * 4
RESULT_MAGIC = 0x50424B48  # "PBKH"
RECORD_MAGIC = 0x50424B52  # "PBKR"
STATUS_STARTED = 0x7100B001
STATUS_DONE = 0x7100D00D
OUT_SUBBLOCK_TILES = 4
MAX_SEM_TOKENS = 15
PACK_OUTPUT_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
PACK_OUTPUT_BYTES = OUT_SUBBLOCK_TILES * matmul.TILE_BYTES


@dataclass(frozen=True)
class BenchSpec:
  name: str
  out_cb: int
  l1_acc: bool | None
  cb_pages_factor: int = 2
  reconfig_each_iter: bool = True

  @property
  def mode(self) -> str:
    if self.out_cb == 0:
      return "baseline"
    acc = "unchanged" if self.l1_acc is None else ("on" if self.l1_acc else "off")
    return f"cb{self.out_cb} l1_acc={acc}"

  def cb_pages(self, iterations: int) -> int:
    if self.out_cb == 0:
      return OUT_SUBBLOCK_TILES
    return max(OUT_SUBBLOCK_TILES, OUT_SUBBLOCK_TILES * iterations * self.cb_pages_factor)


SPECS = (
  BenchSpec("empty", 0, None),
  BenchSpec("cb16_final_l1acc_off_room2x", 16, False, cb_pages_factor=2),
  BenchSpec("cb16_final_l1acc_off_room1x", 16, False, cb_pages_factor=1),
  BenchSpec("cb24_partial_l1acc_off_room2x", 24, False, cb_pages_factor=2),
  BenchSpec("cb24_partial_l1acc_on_room2x", 24, True, cb_pages_factor=2),
  BenchSpec("cb24_partial_l1acc_on_no_reconfig_room2x", 24, True, cb_pages_factor=2, reconfig_each_iter=False),
)


@dataclass(frozen=True)
class Record:
  test_id: int
  name: str
  mode: str
  iterations: int
  out_cb: int
  l1_acc: int
  cb_pages: int
  subblock_tiles: int
  reconfig_each_iter: int
  start: int
  end: int
  cycles: int
  sink: int

  @property
  def cycles_per_iter(self) -> float:
    return self.cycles / self.iterations

  @property
  def cycles_per_tile(self) -> float:
    return self.cycles_per_iter / self.subblock_tiles

  @property
  def us_per_iter(self) -> float:
    return self.cycles_per_iter / AICLK_MHZ

  @property
  def us_per_tile(self) -> float:
    return self.cycles_per_tile / AICLK_MHZ


def result_size() -> int:
  return HEADER_SIZE + RECORD_SIZE


def debug_ranges() -> tuple[DebugRange, ...]:
  return (DebugRange(0, "l1", RESULT_BASE, result_size(), "pack_backend_microbench_results"),)


def emit_header(fw: KernelBase, *, test_id: int, iterations: int, cb_pages: int, status: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, 1, test_id, len(SPECS), status, iterations, cb_pages, result_size(),
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
  cb_pages: int,
  start_lo,
  start_hi,
  end_lo,
  end_hi,
  sink=s1,
):
  fw.li(s2, RESULT_BASE + HEADER_SIZE)
  for off, value in enumerate((
    RECORD_MAGIC,
    test_id,
    iterations,
    spec.out_cb,
    -1 if spec.l1_acc is None else int(spec.l1_acc),
    cb_pages,
    OUT_SUBBLOCK_TILES,
    int(spec.reconfig_each_iter),
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off, reg in enumerate((start_lo, start_hi, end_lo, end_hi, sink), start=8):
    fw.sw(reg, s2, off * 4)
  fw.sw(zero, s2, 13 * 4)
  fw.sw(zero, s2, 14 * 4)
  fw.sw(zero, s2, 15 * 4)
  return fw


def tiny_pack_plan(cb16_pages: int, cb24_pages: int) -> matmul.MatmulPlan:
  return matmul.MatmulPlan(
    rows=(2,), cols=(1,), mt=2, kt=1, nt=2,
    per_core_m=2, per_core_n=2, in0_block_w=1, num_blocks=1,
    out_subblock_h=2, out_subblock_w=2,
    in0_num_subblocks=1, in1_num_subblocks=1,
    in0_block_num_tiles=2, in0_subblock_num_tiles=2,
    in1_block_num_tiles=2, in1_per_core_w=2,
    out_subblock_num_tiles=OUT_SUBBLOCK_TILES,
    out_block_num_tiles=OUT_SUBBLOCK_TILES,
    cb0_pages=2, cb1_pages=2, cb16_pages=cb16_pages, cb24_pages=cb24_pages,
  )


def emit_seed_dest_valid(fw: matmul.MatmulTrisc):
  zeroacc = TTZEROACC(2, 0, 0, 1).raw_word()
  fw.emit(TTZEROACC(2, 0, 0, 1))
  fw.push_tensix(zeroacc + 1)
  return fw.tensix_sync(2, tmp=t1)


def emit_pack_once(fw: matmul.MatmulTrisc, spec: BenchSpec, plan: matmul.MatmulPlan):
  if spec.reconfig_each_iter and spec.l1_acc is not None:
    matmul.emit_pack_reconfig_l1_acc(fw, spec.l1_acc)
  return matmul.emit_pack_tile_to_cb(fw, plan, spec.out_cb)


def emit_timed_loop(fw: matmul.MatmulTrisc, *, test_id: int, iterations: int, spec: BenchSpec, plan: matmul.MatmulPlan):
  fw.li(s1, 0x50420000 | test_id)
  harness.read_wall_clock(fw, a2, a3)
  fw.li(s0, iterations)
  loop = fw._new_label(f"pack_bench_{spec.name}")
  done = fw._new_label(f"pack_bench_{spec.name}_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  if spec.out_cb:
    emit_pack_once(fw, spec, plan)
  else:
    fw.addi(s1, s1, 1)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  harness.read_wall_clock(fw, a4, a5)
  if spec.out_cb:
    fw.tensix_sync(2, tmp=t1)
  return emit_record(
    fw,
    test_id=test_id,
    spec=spec,
    iterations=iterations,
    cb_pages=spec.cb_pages(iterations),
    start_lo=a2,
    start_hi=a3,
    end_lo=a4,
    end_hi=a5,
  )


def build_kernel(spec: BenchSpec, test_id: int, iterations: int, plan: matmul.MatmulPlan) -> KernelBase:
  if iterations > MAX_SEM_TOKENS:
    raise ValueError(f"--iters must be <= {MAX_SEM_TOKENS}; pack_tile consumes one MATH_PACK token per iteration")

  fw = matmul.MatmulTrisc(2)
  emit_header(fw, test_id=test_id, iterations=iterations, cb_pages=spec.cb_pages(iterations), status=STATUS_STARTED)
  if spec.out_cb:
    matmul.matmul_math_init(fw, plan)
    fw.pack.init(dtype=Dtype.Float16_b, out_cb=16, mop_cfg=matmul.MATMUL_PACK_MOP_CFG)
    fw.emit(TTSEMINIT(
      sem_sel=TensixSem.mask(TensixSem.MATH_PACK),
      init_value=MAX_SEM_TOKENS,
      max_value=MAX_SEM_TOKENS,
    ))
    if spec.l1_acc is not None and not spec.reconfig_each_iter:
      matmul.emit_pack_reconfig_l1_acc(fw, spec.l1_acc)
    emit_seed_dest_valid(fw)
  emit_timed_loop(fw, test_id=test_id, iterations=iterations, spec=spec, plan=plan)
  emit_header(fw, test_id=test_id, iterations=iterations, cb_pages=spec.cb_pages(iterations), status=STATUS_DONE)
  return fw.ret()


def build_program(spec: BenchSpec, test_id: int, iterations: int) -> Program:
  cb_pages = spec.cb_pages(iterations)
  plan = tiny_pack_plan(cb16_pages=cb_pages, cb24_pages=cb_pages)
  empty = KernelBase().ret()
  trisc2 = build_kernel(spec, test_id, iterations, plan)
  trisc2.rta(lambda _x, _y: [])
  program = Program(
    brisc=empty, ncrisc=empty, trisc0=empty, trisc1=empty, trisc2=trisc2,
    cbs=[
      (16, matmul.TILE_BYTES, cb_pages),
      (24, matmul.TILE_BYTES, cb_pages),
    ],
    semaphores=matmul.NUM_SEMAPHORES,
    num_cores=1,
  )
  program.name = f"pack_backend_microbench:{spec.name}"
  return program


def clear_results(device: Device, core: tuple[int, int]):
  result_range = debug_ranges()[0]
  with harness.device_window(device, core) as win:
    win.write(result_range.address, b"\0" * result_range.size)
    win.write(PACK_OUTPUT_BASE, b"\xA5" * PACK_OUTPUT_BYTES)


def read_results(device: Device, core: tuple[int, int]) -> bytes:
  result_range = debug_ranges()[0]
  with harness.device_window(device, core) as win:
    blob = win.read(result_range.address, result_range.size)
  if blob and all(b == 0xFF for b in blob):
    raise RuntimeError("L1 readback returned all 0xff; device is not responding cleanly and likely needs a host reboot")
  return blob


def read_pack_output(device: Device, core: tuple[int, int]) -> bytes:
  with harness.device_window(device, core) as win:
    blob = win.read(PACK_OUTPUT_BASE, PACK_OUTPUT_BYTES)
  if blob and all(b == 0xFF for b in blob):
    raise RuntimeError("pack L1 output readback returned all 0xff; device is not responding cleanly")
  return blob


def validate_pack_output(blob: bytes, spec: BenchSpec) -> str:
  if not spec.out_cb:
    return "skipped"
  if blob == b"\xA5" * len(blob):
    raise AssertionError(f"{spec.name}: pack output still contains the pre-run sentinel")
  values = matmul.from_bf16_device_bytes(blob, (OUT_SUBBLOCK_TILES * 32, 32))
  if not np.all(np.isfinite(values)):
    bad = int(values.size - np.count_nonzero(np.isfinite(values)))
    raise AssertionError(f"{spec.name}: pack output contains {bad} non-finite values")
  max_abs = float(np.max(np.abs(values)))
  if max_abs != 0.0:
    raise AssertionError(f"{spec.name}: expected zero-packed output from seeded ZEROACC, max_abs={max_abs}")
  return "finite zero"


def parse_result(blob: bytes, spec: BenchSpec, test_id: int) -> Record:
  header = struct.unpack_from("<" + "I" * HEADER_WORDS, blob, 0)
  if header[0] != RESULT_MAGIC:
    raise RuntimeError(f"{spec.name}: bad result magic 0x{header[0]:08x}")
  if header[4] != STATUS_DONE:
    raise RuntimeError(f"{spec.name}: benchmark did not finish, status=0x{header[4]:08x}")
  words = struct.unpack_from("<" + "I" * RECORD_WORDS, blob, HEADER_SIZE)
  if words[0] != RECORD_MAGIC:
    raise RuntimeError(f"{spec.name}: bad record magic 0x{words[0]:08x}")
  start = words[8] | (words[9] << 32)
  end = words[10] | (words[11] << 32)
  l1_acc = words[4] if words[4] != 0xFFFFFFFF else -1
  return Record(
    test_id=words[1],
    name=spec.name,
    mode=spec.mode,
    iterations=words[2],
    out_cb=words[3],
    l1_acc=l1_acc,
    cb_pages=words[5],
    subblock_tiles=words[6],
    reconfig_each_iter=words[7],
    start=start,
    end=end,
    cycles=(end - start) & ((1 << 64) - 1),
    sink=words[12],
  )


def adjusted_records(records: list[Record]) -> list[tuple[Record, float, float, float, float]]:
  empty = next((r for r in records if r.name == "empty"), None)
  empty_cpi = empty.cycles_per_iter if empty is not None else 0.0
  out = []
  for record in records:
    adj_subblock = max(0.0, record.cycles_per_iter - empty_cpi)
    adj_tile = adj_subblock / record.subblock_tiles
    out.append((record, adj_subblock, adj_tile, adj_subblock / AICLK_MHZ, adj_tile / AICLK_MHZ))
  return out


def format_table(records: list[Record]) -> str:
  lines = [
    "| test | mode | iters | cb pages | cycles | cyc/subblock adj | cyc/tile adj | us/subblock | us/tile | sink |",
    "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
  ]
  for r, adj_sb, adj_tile, us_sb, us_tile in adjusted_records(records):
    lines.append(
      f"| {r.name} | {r.mode} | {r.iterations} | {r.cb_pages} | {r.cycles} | "
      f"{adj_sb:.1f} | {adj_tile:.1f} | {us_sb:.3f} | {us_tile:.3f} | 0x{r.sink:08x} |"
    )
  return "\n".join(lines)


def append_report(path: Path, *, core: tuple[int, int], iterations: int, command: str, records: list[Record]):
  now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
  with path.open("a", encoding="utf-8") as f:
    f.write(f"\n## Run {now}\n\n")
    f.write(f"- Command: `{command}`\n")
    f.write(f"- Core: logical `{core[0]},{core[1]}`\n")
    f.write(f"- Iterations per pack row: `{iterations}`\n")
    f.write("- Dispatch path: slow dispatch (`TT_USB=1`), one active TRISC2 role per launch\n")
    f.write("- Pack body: `matmul_peak.emit_pack_tile_to_cb`, 2x2 output subblock, BF16 tiles\n")
    f.write("- Baseline subtraction: adjusted rows subtract the `empty` loop cycles per iteration\n\n")
    f.write("Debug L1 ranges:\n")
    for item in debug_ranges():
      f.write(f"- `{item.name}` at `0x{item.address:x}` ({item.size} bytes)\n")
    f.write("\n")
    f.write(format_table(records))
    f.write("\n")


def main() -> None:
  parser = argparse.ArgumentParser(description="Microbenchmark Blackhole TRISC2 pack backend costs.")
  parser.add_argument("--core", type=harness.parse_core, default=None, help="logical Tensix core X,Y; default: first program core")
  parser.add_argument("--iters", type=int, default=8, help=f"iterations per timed loop, max {MAX_SEM_TOKENS}")
  parser.add_argument("--only", nargs="+", default=None, help="optional subset of spec names")
  parser.add_argument("--allow-standalone-pack", action="store_true", help="run experimental standalone pack rows; these may time out without a live math producer")
  parser.add_argument("--validate", action="store_true", help="validate standalone pack L1 output is finite and matches seeded ZEROACC zeros")
  parser.add_argument("--no-report", action="store_true", help="do not append results to docs/pack-backend-microbench.md")
  parser.add_argument("--report", type=Path, default=Path("docs/pack-backend-microbench.md"), help="markdown report path")
  args = parser.parse_args()
  if not (0 < args.iters <= MAX_SEM_TOKENS):
    raise ValueError(f"--iters must be in 1..{MAX_SEM_TOKENS}")

  selected = list(SPECS)
  if args.only:
    by_name = {spec.name: spec for spec in SPECS}
    missing = [name for name in args.only if name not in by_name]
    if missing:
      raise ValueError("unknown spec(s): " + ", ".join(missing))
    selected = [by_name[name] for name in args.only]
    if "empty" not in args.only:
      selected.insert(0, by_name["empty"])
  elif not args.allow_standalone_pack:
    selected = [SPECS[0]]
  if not args.allow_standalone_pack:
    blocked = [spec.name for spec in selected if spec.out_cb]
    if blocked:
      raise SystemExit(
        "standalone pack rows are experimental and currently may time out; "
        "rerun with --allow-standalone-pack to opt in: " + ", ".join(blocked)
      )

  records: list[Record] = []
  with harness.open_device() as device:
    core = args.core or device.cores[0]
    for test_id, spec in enumerate(selected):
      clear_results(device, core)
      device.run(build_program(spec, test_id, args.iters))
      records.append(parse_result(read_results(device, core), spec, test_id))
      if args.validate:
        verdict = validate_pack_output(read_pack_output(device, core), spec)
        if spec.out_cb:
          print(f"{spec.name}: validation {verdict}")

  print(format_table(records))
  if not args.no_report:
    command = " ".join(sys.argv)
    append_report(args.report, core=core, iterations=args.iters, command=command, records=records)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
