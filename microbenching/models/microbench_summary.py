#!/usr/bin/env python3
"""Parse blackhole-py benchmark markdown tables and print per-test summaries.

Extracts all 'Run ...' sections from common RISC bench docs and computes
min/median/max adj-cyc/op across roles (or role+group for contention).

Usage:
    PYTHONPATH=. python3 microbenching/microbench_summary.py
    PYTHONPATH=. python3 microbenching/microbench_summary.py --latest
    PYTHONPATH=. python3 microbenching/microbench_summary.py --outliers
    PYTHONPATH=. python3 microbenching/microbench_summary.py --files microbenching/docs/riscv-core-microbench.md
"""

import sys as _bs_sys
from pathlib import Path as _bs_Path
_bs_sys.path.insert(0, str(_bs_Path(__file__).resolve().parents[1]))
import _bench_path  # noqa: F401
import argparse
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

DOCS = Path(__file__).parent / "docs"

DEFAULT_FILES = [
    DOCS / "riscv-core-microbench.md",
    DOCS / "riscv-memory-microbench.md",
    DOCS / "riscv-special-instr-microbench.md",
    DOCS / "riscv-contention-microbench.md",
]


def _maybe_float(s):
    s = s.strip()
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _parse_table(block):
    """Return list-of-dicts from the first markdown table found in block."""
    lines = [l for l in block.splitlines() if l.strip().startswith("|")]
    if len(lines) < 2:
        return []
    header = [c.strip() for c in lines[0].strip("|").split("|")]
    rows = []
    for line in lines[2:]:  # skip separator
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= len(header):
            rows.append(dict(zip(header, cells)))
    return rows


def parse_runs(path):
    """Return [(run_label, rows), ...] for every 'Run ...' section in path."""
    text = Path(path).read_text()
    runs = []
    for m in re.finditer(r"^## (Run .+)$", text, re.MULTILINE):
        start = m.end()
        nxt = re.search(r"^## ", text[start:], re.MULTILINE)
        block = text[start: start + nxt.start()] if nxt else text[start:]
        rows = _parse_table(block)
        if rows:
            runs.append((m.group(1).strip(), rows))
    return runs


def summarise(rows):
    """
    Aggregate adj-cyc/op values by (group, test) across roles.
    Contention tables have a 'group' column; others do not.
    Returns list of dicts with keys: group, test, n, min, median, max, outlier.
    """
    is_contention = "group" in rows[0]
    buckets = defaultdict(list)
    for row in rows:
        test = row.get("test", "").strip()
        if test == "empty":
            continue
        val = _maybe_float(row.get("adj cyc/op"))
        if val is None:
            continue
        grp = row.get("group", "").strip() if is_contention else ""
        buckets[(grp, test)].append(val)

    out = []
    for (grp, test), vals in buckets.items():
        lo, hi = min(vals), max(vals)
        med = statistics.median(vals)
        spread = (hi - lo) / med if med > 0 else 0.0
        out.append(dict(group=grp, test=test, n=len(vals),
                        min=lo, median=med, max=hi, outlier=spread > 0.05))
    return out


def _f(v):
    return f"{v:7.3f}"


def print_summary(entries, show_group):
    if not entries:
        print("  (no data)")
        return
    if show_group:
        hdr = f"  {'group':<48} {'test':<30} {'n':>3} {'min':>8} {'median':>8} {'max':>8}  flag"
        print(hdr)
        print("  " + "-" * (len(hdr) - 2))
        for e in entries:
            flag = "  *" if e["outlier"] else ""
            print(f"  {e['group']:<48} {e['test']:<30} {e['n']:>3}"
                  f" {_f(e['min'])} {_f(e['median'])} {_f(e['max'])}{flag}")
    else:
        hdr = f"  {'test':<35} {'n':>3} {'min':>8} {'median':>8} {'max':>8}  flag"
        print(hdr)
        print("  " + "-" * (len(hdr) - 2))
        for e in entries:
            flag = "  *" if e["outlier"] else ""
            print(f"  {e['test']:<35} {e['n']:>3}"
                  f" {_f(e['min'])} {_f(e['median'])} {_f(e['max'])}{flag}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--files", nargs="+", type=Path, default=DEFAULT_FILES,
                    metavar="FILE", help="Bench doc files to parse (default: all four)")
    ap.add_argument("--latest", action="store_true",
                    help="Only process the most recent run section per file")
    ap.add_argument("--outliers", action="store_true",
                    help="Print only rows where cross-role spread exceeds 5%%")
    args = ap.parse_args()

    found_any = False
    for path in args.files:
        path = Path(path)
        if not path.exists():
            print(f"[skip] {path}: not found", file=sys.stderr)
            continue
        runs = parse_runs(path)
        if not runs:
            print(f"[skip] {path.name}: no 'Run ...' sections found", file=sys.stderr)
            continue
        if args.latest:
            runs = [runs[-1]]
        found_any = True
        for run_label, rows in runs:
            entries = summarise(rows)
            if args.outliers:
                entries = [e for e in entries if e["outlier"]]
            is_contention = "group" in rows[0]
            print(f"\n{'='*70}")
            print(f"  {path.name}  |  {run_label}")
            print(f"  {len(rows)} rows, {len(entries)} non-empty tests summarised")
            print_summary(entries, show_group=is_contention)

    if not found_any:
        print("No benchmark docs found. Run from blackhole-py root "
              "or pass --files explicitly.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
