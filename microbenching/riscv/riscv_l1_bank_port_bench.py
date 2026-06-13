#!/usr/bin/env python3
"""Focused RISC-V L1 bank/port contention sweep.

This is a narrow Verilator-clone calibration wrapper around
`riscv_clone_trace.py`. It keeps the launch/barrier/result-record machinery in
one place, but selects only L1 shared-memory scenarios: same-address pressure
and role-distinct stride pressure for loads, stores, and read-modify-write
pairs.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
import riscv_clone_trace as trace  # noqa: E402


DEFAULT_STRIDES = (0, 4, 16, 64, 256, 2048)
DEFAULT_OPS = ("lw", "sw", "rmw")
OP_BODY = {
  "lw": ("l1_lw_stride", 1, "load"),
  "sw": ("l1_sw_stride", 1, "store"),
  "rmw": ("l1_rmw_stride", 2, "read+write pair"),
}


def scenario_name(op: str, stride: int) -> str:
  mode = "same" if stride == 0 else f"stride{stride}"
  return f"l1_{op}_{mode}"


def make_scenarios(strides: tuple[int, ...], ops: tuple[str, ...]) -> tuple[trace.Scenario, ...]:
  scenarios = [
    trace.Scenario("empty", "base", "empty", 0, description="loop overhead baseline"),
  ]
  for op in ops:
    body, ops_per_iter, unit = OP_BODY[op]
    for stride in strides:
      if stride < 0 or stride % 4:
        raise ValueError("L1 strides must be non-negative word-aligned byte counts")
      mode = "all active roles hit the same word" if stride == 0 else f"role_id * {stride} byte address spacing"
      scenarios.append(trace.Scenario(
        scenario_name(op, stride),
        "l1-bank-port",
        body,
        ops_per_iter,
        stride,
        f"L1 {unit}; {mode}",
      ))
  return tuple(scenarios)


def parse_stride_list(text: str) -> tuple[int, ...]:
  values = tuple(int(part, 0) for part in text.replace(",", " ").split())
  if not values:
    raise argparse.ArgumentTypeError("stride list must not be empty")
  bad = [value for value in values if value < 0 or value % 4]
  if bad:
    raise argparse.ArgumentTypeError(f"strides must be non-negative and word-aligned: {bad}")
  return tuple(dict.fromkeys(values))


def compile_self_test(scenarios: tuple[trace.Scenario, ...], groups: list[int], iterations: int) -> str:
  lines = [
    "| group | enabled roles | text bytes | layout segments |",
    "|---|---:|---:|---:|",
  ]
  for active_mask in groups:
    program = trace.build_program(active_mask, iterations, scenarios)
    text_bytes = 0
    for kernel in program.kernel_map.values():
      for segment in kernel.compile():
        if segment.label == "text":
          text_bytes += len(segment.data)
    layout = program.layout(core_xy=(0, 0))
    enabled_roles = len(trace.mask_roles(active_mask))
    lines.append(
      f"| {trace.group_name(active_mask)} | {enabled_roles} | {text_bytes} | {len(layout)} |"
    )
  return "\n".join(lines)


def selected_groups(args) -> tuple[list[int], str]:
  if args.groups is not None:
    return list(dict.fromkeys(args.groups)), "custom `--groups`"
  if args.all_pairs:
    return trace.all_pair_groups(), "full pair matrix (`--all-pairs`)"
  return trace.default_groups(), "representative default"


def main() -> int:
  parser = argparse.ArgumentParser(description="Sweep RISC-V L1 same-address and stride/bank contention.")
  parser.add_argument("--core", type=trace.core.parse_core, default=None, help="logical Tensix core X,Y; default: first program core")
  parser.add_argument("--iters", type=int, default=10_000, help="iterations per timed scenario")
  parser.add_argument("--strides", type=parse_stride_list, default=DEFAULT_STRIDES, help="byte strides, comma or space separated")
  parser.add_argument("--ops", nargs="+", choices=tuple(OP_BODY), default=list(DEFAULT_OPS), help="operation families to include")
  group_selector = parser.add_mutually_exclusive_group()
  group_selector.add_argument("--groups", nargs="+", type=trace.parse_group, default=None, help="active role groups, e.g. all brisc+ncrisc trisc0")
  group_selector.add_argument("--all-pairs", action="store_true", help="run solos, all C(5,2) pairs, and all five roles")
  parser.add_argument("--fresh-device-per-group", action="store_true", help="open and close Device() around every active-role group")
  parser.add_argument("--dry-run", action="store_true", help="print selected scenarios/groups and compile kernels without opening Device()")
  parser.add_argument("--self-test", action="store_true", help="host-only compile/layout check; alias for --dry-run with concise output")
  parser.add_argument("--no-report", action="store_true", help="do not append results to the markdown report")
  parser.add_argument("--report", type=Path, default=harness.doc_path("riscv", "riscv-l1-bank-port-microbench.md"), help="markdown report path")
  args = parser.parse_args()

  if args.iters <= 0:
    raise ValueError("--iters must be positive")

  strides = args.strides if isinstance(args.strides, tuple) else tuple(args.strides)
  scenarios = make_scenarios(strides, tuple(dict.fromkeys(args.ops)))
  groups, group_preset = selected_groups(args)

  if args.dry_run or args.self_test:
    print(f"scenarios: {', '.join(s.name for s in scenarios)}")
    print(f"groups: {', '.join(trace.group_name(group) for group in groups)}")
    print()
    print(compile_self_test(scenarios, groups, args.iters))
    return 0

  all_records: list[trace.Record] = []
  target_core: tuple[int, int] | None = None
  fresh_device_per_group = args.fresh_device_per_group or args.all_pairs

  if fresh_device_per_group:
    for active_mask in groups:
      group_core, records = trace.run_group(
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
        trace.clear_ranges(device, target_core, scenarios)
        device.run(trace.build_program(active_mask, args.iters, scenarios))
        all_records.extend(trace.parse_results(
          trace.read_results(device, target_core, scenarios),
          trace.group_name(active_mask),
          scenarios,
        ))

  if target_core is None:
    raise RuntimeError("no groups selected")

  print(trace.format_table(all_records))
  if not args.no_report:
    trace.append_report(
      args.report,
      target_core=target_core,
      iterations=args.iters,
      suite="l1-bank-port",
      group_preset=group_preset,
      fresh_device_per_group=fresh_device_per_group,
      scenarios=scenarios,
      records=all_records,
    )
    print(f"\nappended {args.report}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
