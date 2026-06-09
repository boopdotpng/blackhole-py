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

from asm import KernelBase
from device import Device
from dsl import (
  a0, a1, a2, a3, a4, a5, a6, a7,
  s0, s1, s2, s3, s4, s5, s6, s7,
  t0, t1, t2, t3, t4, t5, t6, zero,
)
from pcie import TLBWindow
from program import Program
from ttk.debug import DebugRange
from ttk.tensix import TensixMMIO


ROLE_INDEX = {"brisc": 0, "ncrisc": 1, "trisc0": 2, "trisc1": 3, "trisc2": 4}
ROLE_NAMES = tuple(ROLE_INDEX)

RESULT_BASE = 0x120000
SCRATCH_BASE = RESULT_BASE + 0x4000
HEADER_WORDS = 16
RECORD_WORDS = 12
HEADER_SIZE = HEADER_WORDS * 4
RECORD_SIZE = RECORD_WORDS * 4
RESULT_MAGIC = 0x52424348  # "RBCH"
RECORD_MAGIC = 0x52424352  # "RBCR"
STATUS_STARTED = 0xBEEFB001
STATUS_DONE = 0xBEEFBEEF


@dataclass(frozen=True)
class BenchSpec:
  name: str
  ops_per_iter: int
  kind: str


SPECS = (
  BenchSpec("empty", 0, "empty"),
  BenchSpec("nop8", 8, "nop8"),
  BenchSpec("lui8", 8, "lui8"),
  BenchSpec("auipc8", 8, "auipc8"),
  BenchSpec("addi_dep8", 8, "addi_dep8"),
  BenchSpec("xori_dep8", 8, "xori_dep8"),
  BenchSpec("ori_dep8", 8, "ori_dep8"),
  BenchSpec("andi_dep8", 8, "andi_dep8"),
  BenchSpec("sltiu_dep8", 8, "sltiu_dep8"),
  BenchSpec("slli_dep8", 8, "slli_dep8"),
  BenchSpec("srli_dep8", 8, "srli_dep8"),
  BenchSpec("srai_dep8", 8, "srai_dep8"),
  BenchSpec("ctz_dep4", 4, "ctz_dep4"),
  BenchSpec("sext_b_dep8", 8, "sext_b_dep8"),
  BenchSpec("sext_h_dep8", 8, "sext_h_dep8"),
  BenchSpec("zext_h_dep8", 8, "zext_h_dep8"),
  BenchSpec("add_dep8", 8, "add_dep8"),
  BenchSpec("sub_dep8", 8, "sub_dep8"),
  BenchSpec("addi_ind8", 8, "addi_ind8"),
  BenchSpec("xor_dep8", 8, "xor_dep8"),
  BenchSpec("or_dep8", 8, "or_dep8"),
  BenchSpec("and_dep8", 8, "and_dep8"),
  BenchSpec("sll_dep8", 8, "sll_dep8"),
  BenchSpec("srl_dep8", 8, "srl_dep8"),
  BenchSpec("sra_dep8", 8, "sra_dep8"),
  BenchSpec("slt_dep8", 8, "slt_dep8"),
  BenchSpec("sltu_dep8", 8, "sltu_dep8"),
  BenchSpec("sh1add_dep8", 8, "sh1add_dep8"),
  BenchSpec("sh2add_dep8", 8, "sh2add_dep8"),
  BenchSpec("sh3add_dep8", 8, "sh3add_dep8"),
  BenchSpec("min_dep8", 8, "min_dep8"),
  BenchSpec("minu_dep8", 8, "minu_dep8"),
  BenchSpec("maxu_dep8", 8, "maxu_dep8"),
  BenchSpec("add_ind8", 8, "add_ind8"),
  BenchSpec("xor_ind8", 8, "xor_ind8"),
  BenchSpec("mul_dep4", 4, "mul_dep4"),
  BenchSpec("mulhu_dep4", 4, "mulhu_dep4"),
  BenchSpec("mul_ind4", 4, "mul_ind4"),
  BenchSpec("divu_dep1", 1, "divu_dep1"),
  BenchSpec("remu_dep1", 1, "remu_dep1"),
  BenchSpec("branch_taken1", 1, "branch_taken1"),
  BenchSpec("branch_not_taken1", 1, "branch_not_taken1"),
  BenchSpec("jal1", 1, "jal1"),
  BenchSpec("fence1", 1, "fence1"),
  BenchSpec("load_l1_dep1", 1, "load_l1_dep1"),
  BenchSpec("store_l1_4", 4, "store_l1_4"),
)

IND_REGS = (t0, t1, t2, t3, t4, t5, t6, a0)


def result_size() -> int:
  return HEADER_SIZE + len(SPECS) * RECORD_SIZE


def debug_ranges() -> tuple[DebugRange, ...]:
  return (
    DebugRange(0, "l1", RESULT_BASE, result_size(), "riscv_core_bench_results"),
    DebugRange(1, "l1", SCRATCH_BASE, 64, "riscv_core_bench_scratch"),
  )


@dataclass(frozen=True)
class Record:
  role: str
  test_id: int
  name: str
  iterations: int
  ops_per_iter: int
  start: int
  end: int
  cycles: int
  sink: int


def parse_core(s: str) -> tuple[int, int]:
  try:
    x, y = s.split(",", 1)
    return int(x, 0), int(y, 0)
  except ValueError as e:
    raise argparse.ArgumentTypeError("core must be X,Y") from e


def read_wall_clock(fw: KernelBase, lo, hi, *, addr=a7, hi2=a6):
  retry = fw._new_label("wall_clock_retry")
  fw.li(addr, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_H)
  fw.label(retry)
  fw.lw(hi, addr, 0)
  fw.lw(lo, addr, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L - TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_H)
  fw.lw(hi2, addr, 0)
  fw.bne(hi, hi2, retry)
  return fw


def emit_header(fw: KernelBase, *, role_id: int, iterations: int, status: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, role_id, len(SPECS), RECORD_WORDS, status, iterations, RESULT_BASE, SCRATCH_BASE,
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
):
  addr = RESULT_BASE + HEADER_SIZE + test_id * RECORD_SIZE
  fw.li(s2, addr)
  const_words = (
    RECORD_MAGIC,
    role_id,
    test_id,
    iterations,
    spec.ops_per_iter,
  )
  for off, value in enumerate(const_words):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off, reg in enumerate((start_lo, start_hi, end_lo, end_hi, sink), start=len(const_words)):
    fw.sw(reg, s2, off * 4)
  fw.sw(zero, s2, 10 * 4)
  fw.sw(zero, s2, 11 * 4)
  return fw


def emit_body(fw: KernelBase, kind: str):
  if kind == "empty":
    return fw
  if kind == "nop8":
    for _ in range(8):
      fw.nop()
    return fw
  if kind == "lui8":
    for reg in IND_REGS:
      fw.lui(reg, 0x12345000)
    return fw
  if kind == "auipc8":
    for reg in IND_REGS:
      fw.auipc(reg, 0)
    return fw
  if kind == "addi_dep8":
    for _ in range(8):
      fw.addi(s1, s1, 1)
    return fw
  if kind == "xori_dep8":
    for _ in range(8):
      fw.xori(s1, s1, 0x5A5)
    return fw
  if kind == "ori_dep8":
    for _ in range(8):
      fw.ori(s1, s1, 0x123)
    return fw
  if kind == "andi_dep8":
    for _ in range(8):
      fw.andi(s1, s1, 0x7FF)
    return fw
  if kind == "sltiu_dep8":
    for _ in range(8):
      fw.sltiu(s1, s1, 0x400)
    return fw
  if kind == "slli_dep8":
    for _ in range(8):
      fw.slli(s1, s1, 1)
    return fw
  if kind == "srli_dep8":
    for _ in range(8):
      fw.srli(s1, s1, 1)
    return fw
  if kind == "srai_dep8":
    for _ in range(8):
      fw.srai(s1, s1, 1)
    return fw
  if kind == "ctz_dep4":
    for _ in range(4):
      fw.ctz(s1, s1)
    return fw
  if kind == "sext_b_dep8":
    for _ in range(8):
      fw.sext_b(s1, s1)
    return fw
  if kind == "sext_h_dep8":
    for _ in range(8):
      fw.sext_h(s1, s1)
    return fw
  if kind == "zext_h_dep8":
    for _ in range(8):
      fw.zext_h(s1, s1)
    return fw
  if kind == "add_dep8":
    for _ in range(8):
      fw.add(s1, s1, s4)
    return fw
  if kind == "sub_dep8":
    for _ in range(8):
      fw.sub(s1, s1, s4)
    return fw
  if kind == "addi_ind8":
    for reg in IND_REGS:
      fw.addi(reg, reg, 1)
    return fw
  if kind == "xor_dep8":
    for _ in range(8):
      fw.xor(s1, s1, s4)
    return fw
  if kind == "or_dep8":
    for _ in range(8):
      fw.or_(s1, s1, s4)
    return fw
  if kind == "and_dep8":
    for _ in range(8):
      fw.and_(s1, s1, s4)
    return fw
  if kind == "sll_dep8":
    for _ in range(8):
      fw.sll(s1, s1, s4)
    return fw
  if kind == "srl_dep8":
    for _ in range(8):
      fw.srl(s1, s1, s4)
    return fw
  if kind == "sra_dep8":
    for _ in range(8):
      fw.sra(s1, s1, s4)
    return fw
  if kind == "slt_dep8":
    for _ in range(8):
      fw.slt(s1, s1, s4)
    return fw
  if kind == "sltu_dep8":
    for _ in range(8):
      fw.sltu(s1, s1, s4)
    return fw
  if kind == "sh1add_dep8":
    for _ in range(8):
      fw.sh1add(s1, s1, s4)
    return fw
  if kind == "sh2add_dep8":
    for _ in range(8):
      fw.sh2add(s1, s1, s4)
    return fw
  if kind == "sh3add_dep8":
    for _ in range(8):
      fw.sh3add(s1, s1, s4)
    return fw
  if kind == "min_dep8":
    for _ in range(8):
      fw.min(s1, s1, s4)
    return fw
  if kind == "minu_dep8":
    for _ in range(8):
      fw.minu(s1, s1, s4)
    return fw
  if kind == "maxu_dep8":
    for _ in range(8):
      fw.maxu(s1, s1, s4)
    return fw
  if kind == "add_ind8":
    for reg in IND_REGS:
      fw.add(reg, reg, s4)
    return fw
  if kind == "xor_ind8":
    for reg in IND_REGS:
      fw.xor(reg, reg, s4)
    return fw
  if kind == "mul_dep4":
    for _ in range(4):
      fw.mul(s1, s1, s4)
    return fw
  if kind == "mulhu_dep4":
    for _ in range(4):
      fw.mulhu(s1, s1, s4)
    return fw
  if kind == "mul_ind4":
    for reg in IND_REGS[:4]:
      fw.mul(reg, reg, s4)
    return fw
  if kind == "divu_dep1":
    fw.divu(s1, s1, s4)
    return fw
  if kind == "remu_dep1":
    fw.remu(s1, s1, s4)
    return fw
  if kind == "branch_taken1":
    taken = fw._new_label("branch_taken")
    fw.beq(s1, s1, taken)
    fw.label(taken)
    return fw
  if kind == "branch_not_taken1":
    not_taken = fw._new_label("branch_not_taken")
    fw.bne(s1, s1, not_taken)
    fw.label(not_taken)
    return fw
  if kind == "jal1":
    target = fw._new_label("jal_target")
    fw.j(target)
    fw.label(target)
    return fw
  if kind == "fence1":
    fw.fence()
    return fw
  if kind == "load_l1_dep1":
    fw.lw(s3, s3, 0)
    return fw
  if kind == "store_l1_4":
    for off in range(0, 16, 4):
      fw.sw(s1, s3, off)
    return fw
  raise ValueError(f"unknown benchmark body {kind!r}")


def emit_timed_loop(fw: KernelBase, *, role_id: int, test_id: int, iterations: int, spec: BenchSpec):
  fw.li(s1, 0x12345679)
  fw.li(s4, 3)
  fw.li(s3, SCRATCH_BASE)
  fw.sw(s3, s3, 0)
  fw.sw(s1, s3, 4)
  fw.sw(s4, s3, 8)
  fw.sw(zero, s3, 12)
  for i, reg in enumerate(IND_REGS, start=1):
    fw.li(reg, 0x1000 + i)

  read_wall_clock(fw, a2, a3)
  fw.li(s0, iterations)
  loop = fw._new_label(f"bench_{spec.kind}")
  done = fw._new_label(f"bench_{spec.kind}_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  emit_body(fw, spec.kind)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  read_wall_clock(fw, a4, a5)
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


def build_bench_kernel(role: str, iterations: int) -> KernelBase:
  role_id = ROLE_INDEX[role]
  fw = KernelBase()
  emit_header(fw, role_id=role_id, iterations=iterations, status=STATUS_STARTED)
  for test_id, spec in enumerate(SPECS):
    emit_timed_loop(fw, role_id=role_id, test_id=test_id, iterations=iterations, spec=spec)
  emit_header(fw, role_id=role_id, iterations=iterations, status=STATUS_DONE)
  return fw.ret()


def build_program(role: str, iterations: int) -> Program:
  empty = KernelBase()
  kernels = {name: empty for name in ROLE_NAMES}
  kernels[role] = build_bench_kernel(role, iterations)
  program = Program(**kernels, num_cores=1)
  program.name = f"riscv_core_bench:{role}"
  return program


def read_results(device: Device, core: tuple[int, int]) -> bytes:
  result_range = debug_ranges()[0]
  device.dev.set_power_state(True)
  try:
    with TLBWindow(device.dev, start=core) as win:
      blob = win.read(result_range.address, result_range.size)
  finally:
    device.dev.set_power_state(False)
  if blob and all(b == 0xFF for b in blob):
    raise RuntimeError("L1 readback returned all 0xff; device is not responding cleanly and likely needs a host reboot")
  return blob


def clear_results(device: Device, core: tuple[int, int]):
  result_range, scratch_range = debug_ranges()
  device.dev.set_power_state(True)
  try:
    with TLBWindow(device.dev, start=core) as win:
      win.write(result_range.address, b"\0" * result_range.size)
      win.write(scratch_range.address, b"\0" * scratch_range.size)
  finally:
    device.dev.set_power_state(False)


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
    start = words[5] | (words[6] << 32)
    end = words[7] | (words[8] << 32)
    cycles = (end - start) & ((1 << 64) - 1)
    records.append(Record(
      role=role,
      test_id=words[2],
      name=spec.name,
      iterations=words[3],
      ops_per_iter=words[4],
      start=start,
      end=end,
      cycles=cycles,
      sink=words[9],
    ))
  return records


def format_table(records: list[Record]) -> str:
  by_role = {}
  for record in records:
    by_role.setdefault(record.role, {})[record.name] = record
  lines = [
    "| role | test | cycles | cyc/iter | adj cyc/op | sink |",
    "|---|---:|---:|---:|---:|---:|",
  ]
  for role in ROLE_NAMES:
    role_records = by_role.get(role)
    if not role_records:
      continue
    empty = role_records["empty"].cycles
    empty_iters = role_records["empty"].iterations
    empty_cpi = empty / empty_iters
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
        f"| {role} | {r.name} | {r.cycles} | {cpi:.3f} | {adj_text} | 0x{r.sink:08x} |"
      )
  return "\n".join(lines)


def append_report(path: Path, *, core: tuple[int, int], iterations: int, records: list[Record]):
  table = format_table(records)
  now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
  with path.open("a", encoding="utf-8") as f:
    f.write(f"\n## Run {now}\n\n")
    f.write(f"- Core: logical `{core[0]},{core[1]}`\n")
    f.write(f"- Iterations per test: `{iterations}`\n")
    f.write("- Dispatch path: slow dispatch (`TT_USB=1`), one active role per launch\n\n")
    f.write("Debug L1 ranges:\n")
    for item in debug_ranges():
      f.write(f"- `{item.name}` at `0x{item.address:x}` ({item.size} bytes)\n")
    f.write("\n")
    f.write(table)
    f.write("\n")


def main():
  parser = argparse.ArgumentParser(description="Microbenchmark Blackhole Tensix RISC-V core execution.")
  parser.add_argument("--core", type=parse_core, default=None, help="logical Tensix core X,Y; default: first program core")
  parser.add_argument("--roles", nargs="+", choices=ROLE_NAMES, default=list(ROLE_NAMES), help="roles to benchmark")
  parser.add_argument("--iters", type=int, default=10_000, help="iterations per timed loop")
  parser.add_argument("--no-report", action="store_true", help="do not append results to docs/riscv-core-microbench.md")
  parser.add_argument("--report", type=Path, default=Path("docs/riscv-core-microbench.md"), help="markdown report path")
  args = parser.parse_args()
  if args.iters <= 0:
    raise ValueError("--iters must be positive")

  os.environ.setdefault("TT_USB", "1")
  device = Device()
  all_records: list[Record] = []
  try:
    core = args.core or device.cores[0]
    for role in args.roles:
      clear_results(device, core)
      device.run(build_program(role, args.iters))
      all_records.extend(parse_results(read_results(device, core), role))
  finally:
    device.close()

  print(format_table(all_records))
  if not args.no_report:
    append_report(args.report, core=core, iterations=args.iters, records=all_records)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
