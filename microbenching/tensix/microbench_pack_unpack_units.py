#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as _dt
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402  (does sys.path + TT_USB bootstrap on import)

import microbench_pack_backend as pack_backend  # noqa: E402
import microbench_unpack_backend as unpack_backend  # noqa: E402


Core = tuple[int, int]


@dataclass(frozen=True)
class UnitRecord:
  unit: str
  test: str
  mode: str
  iterations: int
  cycles: int
  cycles_per_iter: float
  cycles_per_tile: float | None
  note: str


UNPACK_NOTES = {
  "empty": "loop/readback baseline",
  "pc_unpack_sync_poll": "poll PC_UNPACK_SYNC until ready",
  "pc_unpack_sync_write": "clear PC_UNPACK_SYNC",
  "cfg_context_flip_setc16": "toggle unpack cfg context via setc16",
  "stallwait_unpack_trisc_cfg": "TTSTALLWAIT on UNPACK/TRISC_CFG",
  "matmul_unpack_row": "one matmul-style TRISC0 row: cfg base writes, TTUNPACR, TTMOP, TTSEMGET, cfg flip",
  "reload_recfg_2x2": "reload-unpack proxy with MOP reconfig and restore",
}

PACK_NOTES = {
  "empty": "loop/readback baseline",
  "cb16_final_l1acc_off_room2x": "pack 2x2 final tiles to cb16, L1 accumulate off",
  "cb16_final_l1acc_off_room1x": "same cb16 final pack with minimal CB room",
  "cb24_partial_l1acc_off_room2x": "pack partial tiles to cb24, L1 accumulate off",
  "cb24_partial_l1acc_on_room2x": "pack partial tiles to cb24, L1 accumulate on",
  "cb24_partial_l1acc_on_no_reconfig_room2x": "same cb24 partial pack with format/L1-acc config hoisted out of loop",
}


def _split_names(value: str | None) -> list[str] | None:
  if not value:
    return None
  names = [item.strip() for item in value.split(",") if item.strip()]
  return names or None


def _unpack_specs(args) -> tuple[unpack_backend.BenchSpec, ...]:
  bws = tuple(args.unpack_bw)
  specs = unpack_backend.build_specs(bws, include_reload=not args.no_reload)
  return unpack_backend.filter_specs(specs, args.unpack_only)


def _pack_specs(args) -> list[pack_backend.BenchSpec]:
  selected = list(pack_backend.SPECS)
  names = _split_names(args.pack_only)
  if names is None:
    names = ["empty"]
  by_name = {spec.name: spec for spec in pack_backend.SPECS}
  missing = [name for name in names if name not in by_name]
  if missing:
    raise ValueError("unknown pack spec(s): " + ", ".join(missing))
  selected = [by_name[name] for name in names]
  if "empty" not in names:
    selected.insert(0, by_name["empty"])
  return selected


def list_experiments(args) -> None:
  if args.unit in ("both", "unpack"):
    print("unpack:")
    for spec in _unpack_specs(args):
      note = UNPACK_NOTES.get(spec.name, "matmul-style unpack subblock")
      print(f"  {spec.name:32s} group={spec.group:8s} tiles/iter={spec.unpack_tiles_per_iter:<3d} {note}")
    if args.unit == "both":
      print()
  if args.unit in ("both", "pack"):
    print("pack:")
    for spec in _pack_specs(args):
      print(f"  {spec.name:32s} mode={spec.mode:28s} tiles/iter={pack_backend.OUT_SUBBLOCK_TILES:<3d} {PACK_NOTES.get(spec.name, '')}")


def run_unpack(device, core: Core, args) -> list[UnitRecord]:
  specs = _unpack_specs(args)
  unpack_backend.clear_results(device, core, specs)
  device.run(unpack_backend.build_program(
    specs,
    args.unpack_iters,
    clear_valid=args.clear_valid,
    trisc1_clear=not args.no_trisc1_clear,
  ))
  records = unpack_backend.parse_results(unpack_backend.read_results(device, core, specs), specs)
  out: list[UnitRecord] = []
  empty = records[0].cycles_per_iter if records else 0.0
  for record in records:
    adjusted = record.cycles_per_iter - empty
    tile_cycles = adjusted / record.unpack_tiles_per_iter if record.unpack_tiles_per_iter else None
    out.append(UnitRecord(
      unit="unpack",
      test=record.name,
      mode=record.group,
      iterations=record.iterations,
      cycles=record.cycles,
      cycles_per_iter=adjusted,
      cycles_per_tile=tile_cycles,
      note=UNPACK_NOTES.get(record.name, f"bw={record.bw}, rows={record.rows_per_iter}"),
    ))
  return out


def run_pack(device, core: Core, args) -> list[UnitRecord]:
  records = []
  for test_id, spec in enumerate(_pack_specs(args)):
    pack_backend.clear_results(device, core)
    device.run(pack_backend.build_program(spec, test_id, args.pack_iters))
    record = pack_backend.parse_result(pack_backend.read_results(device, core), spec, test_id)
    if args.validate_pack:
      pack_backend.validate_pack_output(pack_backend.read_pack_output(device, core), spec)
    records.append(record)

  empty = next((r.cycles_per_iter for r in records if r.name == "empty"), 0.0)
  out: list[UnitRecord] = []
  for record in records:
    adjusted = record.cycles_per_iter - empty
    out.append(UnitRecord(
      unit="pack",
      test=record.name,
      mode=record.mode,
      iterations=record.iterations,
      cycles=record.cycles,
      cycles_per_iter=adjusted,
      cycles_per_tile=adjusted / record.subblock_tiles if record.subblock_tiles else None,
      note=PACK_NOTES.get(record.name, ""),
    ))
  return out


def format_table(records: list[UnitRecord]) -> str:
  lines = [
    "| unit | test | mode | iters | cycles | adj cyc/iter | adj cyc/tile | note |",
    "|---|---|---|---:|---:|---:|---:|---|",
  ]
  for record in records:
    cyc_tile = "" if record.cycles_per_tile is None else f"{record.cycles_per_tile:.2f}"
    lines.append(
      f"| {record.unit} | {record.test} | {record.mode} | {record.iterations} | "
      f"{record.cycles} | {record.cycles_per_iter:.2f} | {cyc_tile} | {record.note} |"
    )
  return "\n".join(lines)


def write_report(path: Path, *, argv: list[str], core: Core, records: list[UnitRecord], args) -> None:
  now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
  path.parent.mkdir(parents=True, exist_ok=True)
  with path.open("a", encoding="utf-8") as f:
    f.write(f"\n## Run {now}\n\n")
    f.write("```bash\n")
    f.write("PYTHONDONTWRITEBYTECODE=1 " + " ".join(argv) + "\n")
    f.write("```\n\n")
    f.write(f"- Core: logical `{core[0]},{core[1]}`\n")
    f.write(f"- Unpack iterations: `{args.unpack_iters}`\n")
    f.write(f"- Pack iterations: `{args.pack_iters}`\n")
    f.write(f"- Unpack companion TRISC1 clear-valid loop: `{'off' if args.no_trisc1_clear else 'on'}`\n")
    f.write(f"- Pack output validation: `{'on' if args.validate_pack else 'off'}`\n\n")
    f.write(format_table(records))
    f.write("\n")


def make_argparser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
    description="Combined Blackhole pack/unpack unit microbenchmark front door.",
  )
  parser.add_argument("--unit", choices=("both", "unpack", "pack"), default="both")
  parser.add_argument("--core", type=harness.parse_core, default=None, help="logical Tensix core X,Y; default: first program core")
  parser.add_argument("--list", action="store_true", help="list the experiments without touching the device")
  parser.add_argument("--no-report", action="store_true", help="do not append docs/tensix/pack-unpack-units.md")
  parser.add_argument("--report", type=Path, default=harness.doc_path("tensix", "pack-unpack-units.md"))

  parser.add_argument("--unpack-iters", type=int, default=5)
  parser.add_argument("--unpack-bw", type=int, nargs="+", default=list(unpack_backend.DEFAULT_BWS))
  parser.add_argument("--unpack-only", default="empty", help="comma-separated unpack tests; empty baseline is always added")
  parser.add_argument("--no-reload", action="store_true")
  parser.add_argument("--clear-valid", action="store_true")
  parser.add_argument("--no-trisc1-clear", action="store_true")

  parser.add_argument("--pack-iters", type=int, default=8, help=f"pack iterations, max {pack_backend.MAX_SEM_TOKENS}")
  parser.add_argument("--pack-only", default=None, help="comma-separated pack tests; empty baseline is always added")
  parser.add_argument("--pack-empty-only", action="store_true", help="deprecated: pack baseline is the default; use --pack-only to name real pack rows")
  parser.add_argument("--validate-pack", action="store_true", help="read back standalone pack output and check finite zeros")
  return parser


def main() -> None:
  args = make_argparser().parse_args()
  if args.unpack_iters <= 0:
    raise ValueError("--unpack-iters must be positive")
  if not (0 < args.pack_iters <= pack_backend.MAX_SEM_TOKENS):
    raise ValueError(f"--pack-iters must be in 1..{pack_backend.MAX_SEM_TOKENS}")
  if any(bw <= 0 for bw in args.unpack_bw):
    raise ValueError("--unpack-bw values must be positive")

  if args.list:
    list_experiments(args)
    return

  records: list[UnitRecord] = []
  with harness.open_device() as device:
    core = args.core or device.cores[0]
    if args.unit in ("both", "unpack"):
      records.extend(run_unpack(device, core, args))
    if args.unit in ("both", "pack"):
      records.extend(run_pack(device, core, args))

  print(format_table(records))
  if not args.no_report:
    write_report(args.report, argv=sys.argv, core=core, records=records, args=args)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
