#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import riscv_core_bench as core
from dsl import s1, s3, s4, s5, zero


SPECIAL_SPECS = (
  core.BenchSpec("empty", 0, "empty"),
  core.BenchSpec("lbu_l1_1", 1, "lbu_l1_1"),
  core.BenchSpec("lhu_l1_1", 1, "lhu_l1_1"),
  core.BenchSpec("lw_l1_1", 1, "lw_l1_1"),
  core.BenchSpec("sb_l1_1", 1, "sb_l1_1"),
  core.BenchSpec("sh_l1_1", 1, "sh_l1_1"),
  core.BenchSpec("sw_l1_1", 1, "sw_l1_1"),
  core.BenchSpec("beq_taken1", 1, "beq_taken1"),
  core.BenchSpec("beq_not_taken1", 1, "beq_not_taken1"),
  core.BenchSpec("bne_taken1", 1, "bne_taken1"),
  core.BenchSpec("bne_not_taken1", 1, "bne_not_taken1"),
  core.BenchSpec("blt_taken1", 1, "blt_taken1"),
  core.BenchSpec("blt_not_taken1", 1, "blt_not_taken1"),
  core.BenchSpec("bge_taken1", 1, "bge_taken1"),
  core.BenchSpec("bge_not_taken1", 1, "bge_not_taken1"),
  core.BenchSpec("bltu_taken1", 1, "bltu_taken1"),
  core.BenchSpec("bltu_not_taken1", 1, "bltu_not_taken1"),
  core.BenchSpec("bgeu_taken1", 1, "bgeu_taken1"),
  core.BenchSpec("bgeu_not_taken1", 1, "bgeu_not_taken1"),
  core.BenchSpec("auipc_addi_jalr3", 3, "auipc_addi_jalr3"),
  core.BenchSpec("csrrs_read4", 4, "csrrs_read4"),
  core.BenchSpec("csrrc_read4", 4, "csrrc_read4"),
)


def _branch(fw, op: str, taken: bool):
  target = fw._new_label(f"{op}_{'taken' if taken else 'not_taken'}")
  if op == "beq":
    fw.beq(s1, s1 if taken else s4, target)
  elif op == "bne":
    fw.bne(s1, s4 if taken else s1, target)
  elif op == "blt":
    fw.blt(s4 if taken else s5, s5 if taken else s4, target)
  elif op == "bge":
    fw.bge(s5 if taken else s4, s4 if taken else s5, target)
  elif op == "bltu":
    fw.bltu(s4 if taken else s5, s5 if taken else s4, target)
  elif op == "bgeu":
    fw.bgeu(s5 if taken else s4, s4 if taken else s5, target)
  else:
    raise ValueError(op)
  fw.label(target)
  return fw


def emit_body(fw, kind: str):
  if kind == "empty":
    return fw
  if kind == "lbu_l1_1":
    return fw.lbu(s1, s3, 0)
  if kind == "lhu_l1_1":
    return fw.lhu(s1, s3, 0)
  if kind == "lw_l1_1":
    return fw.lw(s1, s3, 0)
  if kind == "sb_l1_1":
    return fw.sb(s1, s3, 0)
  if kind == "sh_l1_1":
    return fw.sh(s1, s3, 0)
  if kind == "sw_l1_1":
    return fw.sw(s1, s3, 0)
  if kind.endswith("_taken1"):
    return _branch(fw, kind.split("_", 1)[0], True)
  if kind.endswith("_not_taken1"):
    return _branch(fw, kind.split("_", 1)[0], False)
  if kind == "auipc_addi_jalr3":
    fw.auipc(s5, 0)
    fw.addi(s5, s5, 12)
    return fw.jalr(zero, s5, 0)
  if kind == "csrrs_read4":
    for _ in range(4):
      fw.csrrs(s1, zero, 0x7C0)
    return fw
  if kind == "csrrc_read4":
    for _ in range(4):
      fw.csrrc(s1, zero, 0x7C0)
    return fw
  raise ValueError(f"unknown special benchmark body {kind!r}")


def install_suite():
  core.SPECS = SPECIAL_SPECS
  core.emit_body = emit_body


def main():
  install_suite()
  parser = argparse.ArgumentParser(description="Microbenchmark special Blackhole Tensix RISC-V instructions.")
  parser.add_argument("--core", type=core.parse_core, default=None, help="logical Tensix core X,Y; default: first program core")
  parser.add_argument("--roles", nargs="+", choices=core.ROLE_NAMES, default=list(core.ROLE_NAMES), help="roles to benchmark")
  parser.add_argument("--iters", type=int, default=10_000, help="iterations per timed loop")
  parser.add_argument("--no-report", action="store_true", help="do not append results to docs/riscv-special-instr-microbench.md")
  parser.add_argument("--report", type=Path, default=Path("docs/riscv-special-instr-microbench.md"), help="markdown report path")
  args = parser.parse_args()
  if args.iters <= 0:
    raise ValueError("--iters must be positive")

  os.environ.setdefault("TT_USB", "1")
  device = core.Device()
  all_records: list[core.Record] = []
  try:
    target_core = args.core or device.cores[0]
    for role in args.roles:
      core.clear_results(device, target_core)
      device.run(core.build_program(role, args.iters))
      all_records.extend(core.parse_results(core.read_results(device, target_core), role))
  finally:
    device.close()

  print(core.format_table(all_records))
  if not args.no_report:
    core.append_report(args.report, core=target_core, iterations=args.iters, records=all_records)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
