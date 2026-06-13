#!/usr/bin/env python3
"""Extract Verilator-clone guidance from RISC-V microbench markdown reports.

This is intentionally host-only. It reads checked-in markdown tables, computes
small medians/ranges, and writes a consolidated markdown report for the future
RISC-V clone model. It does not open a Device or run hardware.
"""

from __future__ import annotations

import argparse
import re
import statistics
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402  (doc_path defaults + repo path bootstrap)


DEFAULT_INPUTS = (
  harness.doc_path("riscv", "riscv-core-microbench.md"),
  harness.doc_path("riscv", "riscv-special-instr-microbench.md"),
  harness.doc_path("riscv", "riscv-memory-microbench.md"),
  harness.doc_path("riscv", "riscv-contention-microbench.md"),
  harness.doc_path("riscv", "riscv-clone-contention-trace.md"),
)
DEFAULT_REPORT = harness.doc_path("riscv", "riscv-clone-model-report.md")


@dataclass
class Record:
  source: str
  path: Path
  run: str
  group: str
  role: str
  probe: str
  suite: str
  cycles: float | None
  cyc_iter: float | None
  adj: float | None
  active_roles: int
  adj_per_iter: float | None = None


@dataclass(frozen=True)
class ParamSpec:
  name: str
  description: str
  probes: tuple[str, ...]
  note: str
  use_cyc_iter: bool = False
  active_roles: int | None = None


TIMING_PARAMS = (
  ParamSpec("rv_empty_loop_cyc_iter", "counted-loop baseline", ("empty",), "Subtract per role/group before payload modeling.", True),
  ParamSpec("rv_alu_branch_cyc_op", "base integer/control issue", (
    "nop8", "lui8", "auipc8", "addi_dep8", "xori_dep8", "ori_dep8", "andi_dep8",
    "sltiu_dep8", "slli_dep8", "srli_dep8", "srai_dep8", "add_dep8", "sub_dep8",
    "xor_dep8", "or_dep8", "and_dep8", "sll_dep8", "srl_dep8", "sra_dep8",
    "slt_dep8", "sltu_dep8", "branch_taken1", "branch_not_taken1", "jal1",
    "beq_taken1", "beq_not_taken1", "bne_taken1", "bne_not_taken1",
    "blt_taken1", "blt_not_taken1", "bge_taken1", "bge_not_taken1",
    "bltu_taken1", "bltu_not_taken1", "bgeu_taken1", "bgeu_not_taken1",
    "auipc_addi_jalr3",
  ), "Model as single-issue, no observed taken/not-taken branch penalty."),
  ParamSpec("rv_mul_dep_cyc_op", "dependent multiply", ("mul_dep4", "mulhu_dep4"), "Independent multiply remains at base issue rate."),
  ParamSpec("rv_div_rem_dep_cyc_op", "dependent divide/remainder", ("divu_dep1", "remu_dep1"), "Use as serialized integer divide latency."),
  ParamSpec("rv_fence_cyc_op", "fence", ("fence1",), "Fence is visible even without external traffic."),
  ParamSpec("rv_csr_read_cyc_op", "read-only CSR", ("csrrs_read4", "csrrc_read4"), "Applies to read-only csr probes only."),
  ParamSpec("l1_load_fixed_cyc_op", "L1 fixed-address load", ("l1_lw_fixed1", "lbu_l1_1", "lhu_l1_1", "lw_l1_1"), "Width variants line up with word load timing."),
  ParamSpec("l1_load_stream_cyc_op", "independent L1 load stream", ("l1_lw_ind4", "l1_lw_ind8"), "Use separately from dependent pointer-chase/load-use paths."),
  ParamSpec("l1_load_dep_cyc_op", "dependent L1 load/pointer chase", ("load_l1_dep1", "l1_lw_chase1"), "Primary load-use latency signal."),
  ParamSpec("l1_store_cyc_op", "L1 store", ("store_l1_4", "l1_sw_fixed1", "l1_sw_ind4", "sb_l1_1", "sh_l1_1", "sw_l1_1"), "Stores issue at the base rate in these benches."),
  ParamSpec("l1_store_load_pair_cyc_op", "L1 store then same-address load", ("l1_sw_lw_pair2",), "Reported per op; multiply by two for pair cost."),
  ParamSpec("ldm_local_cyc_op", "local RISC LDM load/store", ("ldm_lw_fixed1", "ldm_lw_ind4", "ldm_lw_chase1", "ldm_sw_fixed1"), "Treat local LDM as private one-cycle path."),
  ParamSpec("ldm_store_load_pair_cyc_op", "local LDM store then load", ("ldm_sw_lw_pair2",), "TRISC2 anomaly remains open in source docs."),
  ParamSpec("xldm_solo_read_cyc_op", "cross-RISC LDM window read", ("xldm_brisc_lw1", "xldm_ncrisc_lw1", "xldm_trisc0_lw1"), "Solo read baseline; contention model scales this separately.", active_roles=1),
  ParamSpec("mmio_read_cyc_op", "MMIO read", ("mmio_wall_lw1", "mmio_noc_status_lw1"), "Wall-clock and NoC-status reads are the available safe MMIO probes.", active_roles=1),
)


def _clean_cell(text: str) -> str:
  return text.strip().strip("`")


def _as_float(text: str | None) -> float | None:
  if text is None:
    return None
  text = _clean_cell(text)
  if not text or text in {"-", "--", "---", "—"}:
    return None
  try:
    return float(text)
  except ValueError:
    return None


def _split_row(line: str) -> list[str]:
  return [_clean_cell(cell) for cell in line.strip().strip("|").split("|")]


def _is_separator(line: str) -> bool:
  cells = _split_row(line)
  return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def parse_markdown_tables(text: str) -> list[list[dict[str, str]]]:
  lines = text.splitlines()
  tables: list[list[dict[str, str]]] = []
  i = 0
  while i + 1 < len(lines):
    if lines[i].lstrip().startswith("|") and _is_separator(lines[i + 1]):
      header = _split_row(lines[i])
      rows: list[dict[str, str]] = []
      i += 2
      while i < len(lines) and lines[i].lstrip().startswith("|"):
        cells = _split_row(lines[i])
        if len(cells) >= len(header):
          rows.append(dict(zip(header, cells)))
        i += 1
      if rows:
        tables.append(rows)
      continue
    i += 1
  return tables


def parse_runs(path: Path, *, latest_only: bool) -> list[tuple[str, list[dict[str, str]]]]:
  text = path.read_text(encoding="utf-8")
  matches = list(re.finditer(r"^## (Run .+)$", text, re.MULTILINE))
  runs: list[tuple[str, list[dict[str, str]]]] = []
  for idx, match in enumerate(matches):
    start = match.end()
    end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
    rows: list[dict[str, str]] = []
    for table in parse_markdown_tables(text[start:end]):
      if not table:
        continue
      columns = set(table[0])
      if ("test" in columns or "scenario" in columns) and ("role" in columns or "group" in columns):
        rows.extend(table)
    if rows:
      runs.append((match.group(1), rows))
  return runs[-1:] if latest_only and runs else runs


def _source_name(path: Path) -> str:
  return path.stem.replace("riscv-", "").replace("-microbench", "").replace("-", "_")


def _active_roles(group: str) -> int:
  if not group:
    return 1
  return len([part for part in re.split(r"[+,]", group) if part.strip()])


def load_records(paths: list[Path], *, latest_only: bool) -> tuple[list[Record], list[str]]:
  records: list[Record] = []
  warnings: list[str] = []
  for path in paths:
    if not path.exists():
      warnings.append(f"{path}: missing")
      continue
    runs = parse_runs(path, latest_only=latest_only)
    if not runs:
      warnings.append(f"{path.name}: no measured Run table found")
      continue
    for run, rows in runs:
      for row in rows:
        probe = row.get("test") or row.get("scenario") or ""
        role = row.get("role", "")
        if not probe or not role:
          continue
        group = row.get("group", "")
        records.append(Record(
          source=_source_name(path),
          path=path,
          run=run,
          group=group,
          role=role,
          probe=probe,
          suite=row.get("suite", ""),
          cycles=_as_float(row.get("cycles")),
          cyc_iter=_as_float(row.get("cyc/iter")),
          adj=_as_float(row.get("adj cyc/op")),
          active_roles=_active_roles(group),
        ))
  _fill_adjusted_per_iter(records)
  return records, warnings


def _fill_adjusted_per_iter(records: list[Record]) -> None:
  empty: dict[tuple[str, str, str, str], float] = {}
  for record in records:
    if record.probe == "empty" and record.cyc_iter is not None:
      empty[(record.source, record.run, record.group, record.role)] = record.cyc_iter
  for record in records:
    base = empty.get((record.source, record.run, record.group, record.role))
    if base is not None and record.cyc_iter is not None:
      record.adj_per_iter = record.cyc_iter - base


def _median(vals: list[float]) -> float | None:
  vals = [v for v in vals if v is not None]
  return statistics.median(vals) if vals else None


def _fmt(v: float | None) -> str:
  if v is None:
    return "MISSING"
  if abs(v - round(v)) < 0.0005:
    return f"{v:.1f}"
  return f"{v:.3f}"


def _range(vals: list[float]) -> str:
  if not vals:
    return "MISSING"
  lo = min(vals)
  hi = max(vals)
  if abs(lo - hi) < 0.0005:
    return _fmt(statistics.median(vals))
  return f"{_fmt(statistics.median(vals))} ({_fmt(lo)}..{_fmt(hi)})"


def _source_summary(records: list[Record]) -> str:
  by_source: dict[tuple[str, str], list[Record]] = {}
  for record in records:
    by_source.setdefault((record.source, record.run), []).append(record)
  lines = [
    "| Source | Run | Rows | Non-empty probes |",
    "|---|---|---:|---:|",
  ]
  for (source, run), rows in sorted(by_source.items()):
    probes = {row.probe for row in rows if row.probe != "empty"}
    lines.append(f"| `{source}` | {run} | {len(rows)} | {len(probes)} |")
  return "\n".join(lines)


def _timing_table(records: list[Record]) -> str:
  lines = [
    "| Clone parameter | What it models | Recommended value | Evidence probes | Notes |",
    "|---|---|---:|---|---|",
  ]
  for spec in TIMING_PARAMS:
    vals: list[float] = []
    probes_seen: list[str] = []
    for record in records:
      if record.probe not in spec.probes:
        continue
      if spec.active_roles is not None and record.active_roles != spec.active_roles:
        continue
      value = record.cyc_iter if spec.use_cyc_iter else record.adj
      if value is None:
        continue
      vals.append(value)
      if record.probe not in probes_seen:
        probes_seen.append(record.probe)
    evidence = ", ".join(f"`{probe}`" for probe in probes_seen[:6])
    if len(probes_seen) > 6:
      evidence += f", +{len(probes_seen) - 6} more"
    lines.append(
      f"| `{spec.name}` | {spec.description} | {_range(vals)} cycles | "
      f"{evidence or 'MISSING'} | {spec.note} |"
    )
  return "\n".join(lines)


def _contention_values(records: list[Record], probes: set[str], *, exclude: tuple[str, ...] = ()) -> dict[int, list[float]]:
  out: dict[int, list[float]] = {}
  for record in records:
    if not record.group or record.adj is None:
      continue
    if probes and record.probe not in probes:
      continue
    if any(part in record.probe for part in exclude):
      continue
    out.setdefault(record.active_roles, []).append(record.adj)
  return out


def _probe_prefix_values(records: list[Record], prefix: str, *, exclude: tuple[str, ...] = ()) -> dict[int, list[float]]:
  out: dict[int, list[float]] = {}
  for record in records:
    if not record.group or record.adj is None or not record.probe.startswith(prefix):
      continue
    if any(part in record.probe for part in exclude):
      continue
    out.setdefault(record.active_roles, []).append(record.adj)
  return out


def _contention_table(records: list[Record]) -> str:
  patterns = [
    ("MMIO read", _contention_values(records, {"mmio_wall_lw1", "mmio_noc_status_lw1"}), "Fixed-latency MMIO read port; small five-way wall-clock penalty."),
    ("L1 same-address load", _contention_values(records, {"l1_same_lw1", "l1_lw_stride0"}), "Near-flat; add slight same-word serialization only under all-role pressure."),
    ("L1 distinct-address load", _contention_values(records, {"l1_dist_lw1", "l1_lw_stride64", "l1_lw_stride2048"}), "Near-flat for measured groups."),
    ("L1 store", _contention_values(records, {"l1_same_sw1", "l1_dist_sw1", "l1_sw_stride0", "l1_sw_stride64", "l1_sw_stride2048"}), "Stores issue at base rate in measured safe probes."),
    ("L1 read-modify-write", _contention_values(records, {"l1_same_rmw2", "l1_rmw_stride0", "l1_rmw_stride64"}), "Shared L1 RMW path serializes with active roles."),
    ("Local LDM", _contention_values(records, {"ldm_self_lw1", "ldm_self_sw1"}), "Private path; no measured role-count scaling."),
    ("Cross-LDM read", _probe_prefix_values(records, "xldm_", exclude=("contested", "ptr_chase")), "Model as a shared cross-LDM fabric, not per-target ports."),
    ("Cross-LDM contested readers", _probe_prefix_values(records, "xldm_contested_", exclude=()), "Owner write path appears separate from reader path."),
  ]
  lines = [
    "| Pattern | 1 role | 2 roles | 5 roles | Recommendation |",
    "|---|---:|---:|---:|---|",
  ]
  for name, by_count, recommendation in patterns:
    lines.append(
      f"| {name} | {_range(by_count.get(1, []))} | {_range(by_count.get(2, []))} | "
      f"{_range(by_count.get(5, []))} | {recommendation} |"
    )
  return "\n".join(lines)


def _role_spread_gaps(records: list[Record]) -> list[str]:
  buckets: dict[tuple[str, str, str], list[float]] = {}
  for record in records:
    if record.adj is None or record.probe == "empty":
      continue
    key = (record.source, record.group, record.probe)
    buckets.setdefault(key, []).append(record.adj)
  gaps: list[str] = []
  for (source, group, probe), vals in sorted(buckets.items()):
    if len(vals) < 2:
      continue
    med = statistics.median(vals)
    if med <= 0:
      continue
    spread = (max(vals) - min(vals)) / med
    if spread > 0.05:
      where = f"{source}/{group or 'solo'}"
      gaps.append(f"- `{where}` `{probe}` role spread {_fmt(min(vals))}..{_fmt(max(vals))} cycles/op; repeat before hard-coding priority.")
  return gaps[:8]


def _open_gaps(records: list[Record], warnings: list[str]) -> str:
  lines: list[str] = []
  clone_rows = [r for r in records if r.source == "clone_contention_trace"]
  if not clone_rows:
    lines.append("- Clone trace doc has no measured Run table yet; stride, mixed victim/aggressor, producer, and ifetch recommendations are pending.")
  if not any(r.probe.startswith("ifetch_") for r in records):
    lines.append("- IRAM/ifetch behavior is still indirect or unmeasured in the checked-in tables.")
  contention_groups = {r.group for r in records if r.source == "contention" and r.group}
  if contention_groups and len(contention_groups) < 16:
    lines.append(f"- Contention matrix is representative, not exhaustive: {len(contention_groups)} groups present vs 16 all-pairs groups.")
  lines.append("- Launch/dispatch overhead is outside these RISC-V in-kernel tables and still needs a separate model input.")
  lines.append("- Remote LDM stores should stay excluded from safe benches; model them only after a simulator or protected scratch protocol exists.")
  for warning in warnings:
    lines.append(f"- Input warning: {warning}.")
  lines.extend(_role_spread_gaps(records))
  return "\n".join(dict.fromkeys(lines))


def _rtl_interfaces() -> str:
  rows = [
    ("`rv_issue_if`", "`role`, decoded op class, dependency tag", "`done`, `latency_cycles`", "Uses integer timing table; one op/cycle base issue."),
    ("`l1_data_if`", "`role`, `addr`, `size`, `is_store`, `rmw`", "`ready`, `rdata`", "Owns fixed-load, stream-load, store, and same-address/RMW contention knobs."),
    ("`ldm_local_if`", "`role`, `addr`, `size`, `is_store`", "`ready`, `rdata`", "Private one-cycle local LDM path."),
    ("`xldm_fabric_if`", "`src_role`, `dst_role`, `addr`, `size`, `is_store`", "`ready`, `rdata`", "Shared read fabric with role-count contention; remote stores disabled by default."),
    ("`mmio_if`", "`role`, `addr`, `size`, `is_store`", "`ready`, `rdata`", "Fixed MMIO read latency plus optional all-role contention bump."),
    ("`wall_clock_if`", "`role`", "`wall_clock[63:0]`", "Monotonic timestamp source used by benches and firmware."),
    ("`clone_trace_cfg_if`", "`suite`, `group_mask`, `iters`, `scenario_id`", "`result_valid`, counters", "Optional verification hook matching the safe clone-trace scenarios."),
  ]
  lines = [
    "| Interface | Request fields | Response fields | Clone-model use |",
    "|---|---|---|---|",
  ]
  lines.extend(f"| {name} | {req} | {resp} | {use} |" for name, req, resp, use in rows)
  return "\n".join(lines)


def render_report(records: list[Record], warnings: list[str], *, inputs: list[Path], latest_only: bool) -> str:
  def display(path: Path) -> str:
    try:
      return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
      return str(path)

  return "\n".join((
    "# RISC-V Clone Model Extract",
    "",
    "This report is generated by `microbenching/riscv/riscv_clone_model_extract.py` from checked-in RISC-V markdown Run tables. It is host-only and does not run hardware.",
    "",
    "## Inputs",
    "",
    "\n".join(f"- `{display(path)}`" for path in inputs),
    "",
    f"Run selection: {'latest Run section per file' if latest_only else 'all Run sections per file'}.",
    "",
    "## Source Runs",
    "",
    _source_summary(records) if records else "No measured rows loaded.",
    "",
    "## Timing Parameters",
    "",
    _timing_table(records),
    "",
    "## Contention Model",
    "",
    _contention_table(records),
    "",
    "## Suggested RTL Interfaces",
    "",
    _rtl_interfaces(),
    "",
    "## Open Gaps",
    "",
    _open_gaps(records, warnings),
    "",
    "## Safe Commands",
    "",
    "```sh",
    "python3 -m py_compile microbenching/riscv/riscv_clone_model_extract.py",
    "python3 microbenching/riscv/riscv_clone_model_extract.py --self-test",
    "python3 microbenching/riscv/riscv_clone_model_extract.py --no-report",
    "python3 microbenching/riscv/riscv_clone_model_extract.py --report microbenching/docs/riscv/riscv-clone-model-report.md",
    "```",
    "",
    "Do not use `tt-device-queue` for this extractor; it is an offline markdown parser.",
    "",
  ))


def self_test() -> None:
  sample_core = """# Core

## Run old

| role | test | cycles | cyc/iter | adj cyc/op | sink |
|---|---:|---:|---:|---:|---:|
| brisc | empty | 30 | 3.000 |  | 0x0 |
| brisc | addi_dep8 | 110 | 11.000 | 1.000 | 0x0 |

## Run new

| role | test | cycles | cyc/iter | adj cyc/op | sink |
|---|---:|---:|---:|---:|---:|
| brisc | empty | 30 | 3.000 |  | 0x0 |
| brisc | addi_dep8 | 110 | 11.000 | 1.000 | 0x0 |
| ncrisc | empty | 30 | 3.000 |  | 0x0 |
| ncrisc | addi_dep8 | 110 | 11.000 | 1.000 | 0x0 |
"""
  sample_contention = """# Contention

## Run sample

| group | role | test | cycles | cyc/iter | adj cyc/op | sink |
|---|---|---:|---:|---:|---:|---:|
| brisc | brisc | empty | 30 | 3.000 |  | 0x0 |
| brisc | brisc | xldm_brisc_lw1 | 55 | 5.500 | 2.500 | 0x0 |
| brisc+ncrisc | brisc | empty | 30 | 3.000 |  | 0x0 |
| brisc+ncrisc | brisc | xldm_brisc_lw1 | 80 | 8.000 | 5.000 | 0x0 |
"""
  with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    core = root / "riscv-core-microbench.md"
    contention = root / "riscv-contention-microbench.md"
    core.write_text(sample_core, encoding="utf-8")
    contention.write_text(sample_contention, encoding="utf-8")
    records, warnings = load_records([core, contention], latest_only=True)
    assert not warnings
    assert len(records) == 8, len(records)
    assert {r.run for r in records if r.source == "core"} == {"Run new"}
    report = render_report(records, [], inputs=[core, contention], latest_only=True)
    assert "`rv_alu_branch_cyc_op`" in report
    assert "Cross-LDM read" in report
    assert "Suggested RTL Interfaces" in report
  print("self-test passed")


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--files", nargs="+", type=Path, default=list(DEFAULT_INPUTS), help="markdown report files to parse")
  parser.add_argument("--all-runs", action="store_true", help="parse every Run section instead of only the latest per file")
  parser.add_argument("--report", type=Path, default=DEFAULT_REPORT, help="markdown report output path")
  parser.add_argument("--no-report", action="store_true", help="print only; do not write the report file")
  parser.add_argument("--self-test", action="store_true", help="run host-only parser/report self-test")
  args = parser.parse_args()

  if args.self_test:
    self_test()
    return 0

  inputs = [Path(path) for path in args.files]
  records, warnings = load_records(inputs, latest_only=not args.all_runs)
  report = render_report(records, warnings, inputs=inputs, latest_only=not args.all_runs)
  print(report, end="")
  if not args.no_report:
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report, encoding="utf-8")
    print(f"wrote {args.report}", file=sys.stderr)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
