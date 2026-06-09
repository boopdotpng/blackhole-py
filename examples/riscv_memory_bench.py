#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import riscv_core_bench as core
from dsl import (
  a2, a3, a4, a5,
  s0, s1, s3, s4, s5, s6, s7,
  t0, t1, t2, t3, t4, t5, t6, zero,
)


LOCAL_LDM_BASE = 0xFFB00080
BRISC_LDM_WINDOW = 0xFFB14080
NCRISC_LDM_WINDOW = 0xFFB16080
TRISC0_LDM_WINDOW = 0xFFB18080


MEMORY_SPECS = (
  core.BenchSpec("empty", 0, "empty"),
  core.BenchSpec("l1_lw_fixed1", 1, "l1_lw_fixed1"),
  core.BenchSpec("l1_lw_ind4", 4, "l1_lw_ind4"),
  core.BenchSpec("l1_lw_ind8", 8, "l1_lw_ind8"),
  core.BenchSpec("l1_lw_chase1", 1, "l1_lw_chase1"),
  core.BenchSpec("l1_load_use0_2", 2, "l1_load_use0_2"),
  core.BenchSpec("l1_load_use1_3", 3, "l1_load_use1_3"),
  core.BenchSpec("l1_load_use2_4", 4, "l1_load_use2_4"),
  core.BenchSpec("l1_load_use4_6", 6, "l1_load_use4_6"),
  core.BenchSpec("l1_sw_fixed1", 1, "l1_sw_fixed1"),
  core.BenchSpec("l1_sw_ind4", 4, "l1_sw_ind4"),
  core.BenchSpec("l1_sw_lw_pair2", 2, "l1_sw_lw_pair2"),
  core.BenchSpec("ldm_lw_fixed1", 1, "ldm_lw_fixed1"),
  core.BenchSpec("ldm_lw_ind4", 4, "ldm_lw_ind4"),
  core.BenchSpec("ldm_lw_chase1", 1, "ldm_lw_chase1"),
  core.BenchSpec("ldm_sw_fixed1", 1, "ldm_sw_fixed1"),
  core.BenchSpec("ldm_sw_lw_pair2", 2, "ldm_sw_lw_pair2"),
  core.BenchSpec("xldm_brisc_lw1", 1, "xldm_brisc_lw1"),
  core.BenchSpec("xldm_ncrisc_lw1", 1, "xldm_ncrisc_lw1"),
  core.BenchSpec("xldm_trisc0_lw1", 1, "xldm_trisc0_lw1"),
)


def emit_body(fw, kind: str):
  if kind == "empty":
    return fw
  if kind == "l1_lw_fixed1":
    return fw.lw(s1, s3, 0)
  if kind == "l1_lw_ind4":
    fw.lw(t0, s3, 0)
    fw.lw(t1, s3, 4)
    fw.lw(t2, s3, 8)
    return fw.lw(t3, s3, 12)
  if kind == "l1_lw_ind8":
    for reg, off in ((t0, 0), (t1, 4), (t2, 8), (t3, 12), (t4, 16), (t5, 20), (t6, 24), (s5, 28)):
      fw.lw(reg, s3, off)
    return fw
  if kind == "l1_lw_chase1":
    return fw.lw(s3, s3, 0)
  if kind == "l1_load_use0_2":
    fw.lw(s5, s3, 0)
    return fw.add(s1, s1, s5)
  if kind == "l1_load_use1_3":
    fw.lw(s5, s3, 0)
    fw.addi(t0, t0, 1)
    return fw.add(s1, s1, s5)
  if kind == "l1_load_use2_4":
    fw.lw(s5, s3, 0)
    fw.addi(t0, t0, 1)
    fw.addi(t1, t1, 1)
    return fw.add(s1, s1, s5)
  if kind == "l1_load_use4_6":
    fw.lw(s5, s3, 0)
    for reg in (t0, t1, t2, t3):
      fw.addi(reg, reg, 1)
    return fw.add(s1, s1, s5)
  if kind == "l1_sw_fixed1":
    return fw.sw(s1, s3, 4)
  if kind == "l1_sw_ind4":
    for off in (0, 4, 8, 12):
      fw.sw(s1, s3, off)
    return fw
  if kind == "l1_sw_lw_pair2":
    fw.sw(s1, s3, 4)
    return fw.lw(s5, s3, 4)
  if kind == "ldm_lw_fixed1":
    return fw.lw(s1, s6, 0)
  if kind == "ldm_lw_ind4":
    fw.lw(t0, s6, 0)
    fw.lw(t1, s6, 4)
    fw.lw(t2, s6, 8)
    return fw.lw(t3, s6, 12)
  if kind == "ldm_lw_chase1":
    return fw.lw(s6, s6, 0)
  if kind == "ldm_sw_fixed1":
    return fw.sw(s1, s6, 4)
  if kind == "ldm_sw_lw_pair2":
    fw.sw(s1, s6, 4)
    return fw.lw(s5, s6, 4)
  if kind == "xldm_brisc_lw1":
    return fw.lw(s1, s7, 0)
  if kind == "xldm_ncrisc_lw1":
    return fw.lw(s1, t4, 0)
  if kind == "xldm_trisc0_lw1":
    return fw.lw(s1, t5, 0)
  raise ValueError(f"unknown memory benchmark body {kind!r}")


def emit_timed_loop(fw, *, role_id: int, test_id: int, iterations: int, spec: core.BenchSpec):
  fw.li(s1, 0x12345679)
  fw.li(s4, 3)
  fw.li(s3, core.SCRATCH_BASE)
  fw.sw(s3, s3, 0)
  fw.sw(s1, s3, 4)
  fw.sw(s4, s3, 8)
  fw.sw(zero, s3, 12)
  for off in range(16, 64, 4):
    fw.sw(s1, s3, off)

  fw.li(s6, LOCAL_LDM_BASE)
  fw.sw(s6, s6, 0)
  fw.sw(s1, s6, 4)
  fw.sw(s4, s6, 8)
  fw.sw(zero, s6, 12)

  fw.li(s7, BRISC_LDM_WINDOW)
  fw.li(t4, NCRISC_LDM_WINDOW)
  fw.li(t5, TRISC0_LDM_WINDOW)

  core.read_wall_clock(fw, a2, a3)
  fw.li(s0, iterations)
  loop = fw._new_label(f"bench_{spec.kind}")
  done = fw._new_label(f"bench_{spec.kind}_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  emit_body(fw, spec.kind)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  core.read_wall_clock(fw, a4, a5)
  core.emit_record(
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


def install_suite():
  core.SPECS = MEMORY_SPECS
  core.emit_body = emit_body
  core.emit_timed_loop = emit_timed_loop


def main():
  install_suite()
  parser = argparse.ArgumentParser(description="Microbenchmark Blackhole Tensix RISC-V memory access.")
  parser.add_argument("--core", type=core.parse_core, default=None, help="logical Tensix core X,Y; default: first program core")
  parser.add_argument("--roles", nargs="+", choices=core.ROLE_NAMES, default=list(core.ROLE_NAMES), help="roles to benchmark")
  parser.add_argument("--iters", type=int, default=10_000, help="iterations per timed loop")
  parser.add_argument("--no-report", action="store_true", help="do not append results to docs/riscv-memory-microbench.md")
  parser.add_argument("--report", type=Path, default=Path("docs/riscv-memory-microbench.md"), help="markdown report path")
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
