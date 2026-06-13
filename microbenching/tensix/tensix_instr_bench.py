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
  TTNOP, TTSEMINIT, TTSTALLWAIT,
  a2, a3, a4, a5, a6, a7,
  s0, s1, s2, s3, s4, s5, s6, s7, s8,
  t0, t1, t2, t3, t4, t5, zero,
)
from program import Program
from ttk.debug import DebugRange
from ttk.tensix import TensixMMIO, TensixRegs, TensixSem


ROLE_INDEX = {"trisc0": 2, "trisc1": 3, "trisc2": 4}
ROLE_NAMES = tuple(ROLE_INDEX)

RESULT_BASE = 0x128000
HEADER_WORDS = 16
RECORD_WORDS = 12
HEADER_SIZE = HEADER_WORDS * 4
RECORD_SIZE = RECORD_WORDS * 4
RESULT_MAGIC = 0x54494248  # "TIBH"
RECORD_MAGIC = 0x54494252  # "TIBR"
STATUS_STARTED = 0x7100B001
STATUS_DONE = 0x7100D00D

WORD_REGS = (s4, s5, s6, s7, t2, t3, t4, t5)


def tt_raw(inst) -> int:
  return inst.raw_word() if hasattr(inst, "raw_word") else int(inst) & 0xFFFFFFFF


TTNOP_WORD = tt_raw(TTNOP())
TTSTALLWAIT_NONE_WORD = tt_raw(TTSTALLWAIT(0, 0))
TTSEMINIT_MATH_PACK_WORD = tt_raw(
  TTSEMINIT(sem_sel=TensixSem.mask(TensixSem.MATH_PACK), init_value=0, max_value=1)
)


@dataclass(frozen=True)
class BenchSpec:
  name: str
  group: str
  words: tuple[int, ...]
  drain_each_iter: bool = False

  @property
  def ops_per_iter(self) -> int:
    return len(self.words)

  @property
  def mode(self) -> str:
    if self.name == "empty":
      return "baseline"
    if self.name == "sync_empty":
      return "sync-only"
    return "issue+sync" if self.drain_each_iter else "issue"


SPECS = (
  BenchSpec("empty", "empty", ()),
  BenchSpec("sync_empty", "sync_empty", (), drain_each_iter=True),
  BenchSpec("ttnop_issue8", "ttnop", (TTNOP_WORD,) * 8),
  BenchSpec("ttnop_sync8", "ttnop", (TTNOP_WORD,) * 8, drain_each_iter=True),
  BenchSpec("stallwait_none_issue8", "stallwait_none", (TTSTALLWAIT_NONE_WORD,) * 8),
  BenchSpec("stallwait_none_sync8", "stallwait_none", (TTSTALLWAIT_NONE_WORD,) * 8, drain_each_iter=True),
  BenchSpec("seminit_issue4", "seminit", (TTSEMINIT_MATH_PACK_WORD,) * 4),
  BenchSpec("seminit_sync4", "seminit", (TTSEMINIT_MATH_PACK_WORD,) * 4, drain_each_iter=True),
  BenchSpec(
    "seminit_stallwait_issue4",
    "seminit_stallwait",
    (TTSEMINIT_MATH_PACK_WORD, TTSTALLWAIT_NONE_WORD) * 2,
  ),
  BenchSpec(
    "seminit_stallwait_sync4",
    "seminit_stallwait",
    (TTSEMINIT_MATH_PACK_WORD, TTSTALLWAIT_NONE_WORD) * 2,
    drain_each_iter=True,
  ),
)


@dataclass(frozen=True)
class Record:
  role: str
  test_id: int
  name: str
  group: str
  mode: str
  iterations: int
  ops_per_iter: int
  start: int
  end: int
  cycles: int
  sink: int


def result_size() -> int:
  return HEADER_SIZE + len(SPECS) * RECORD_SIZE


def debug_ranges() -> tuple[DebugRange, ...]:
  return (
    DebugRange(0, "l1", RESULT_BASE, result_size(), "tensix_instr_bench_results"),
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
  fw.li(t0, 1 if spec.drain_each_iter else 0)
  fw.sw(t0, s2, 10 * 4)
  fw.sw(zero, s2, 11 * 4)
  return fw


def emit_drain_sync(fw: KernelBase):
  fw.sw(zero, s8, 0)
  fw.lw(s1, s8, 0)
  return fw.and_(zero, zero, s1)


def emit_timed_loop(fw: KernelBase, *, role_id: int, test_id: int, iterations: int, spec: BenchSpec):
  fw.li(s1, 0x71000000 | test_id)
  fw.li(s3, TensixRegs.INSTRN_BUF_BASE)
  fw.li(s8, TensixRegs.PC_BUF_SYNC)
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
  for word in spec.words:
    fw.sw(word_to_reg[word], s3, 0)
  if spec.drain_each_iter:
    emit_drain_sync(fw)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  harness.read_wall_clock(fw, a4, a5)
  if spec.words and not spec.drain_each_iter:
    emit_drain_sync(fw)
  elif not spec.words and spec.name == "empty":
    fw.li(s1, 0x71000000 | test_id)
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
  kernels = {"brisc": empty, "ncrisc": empty, "trisc0": empty, "trisc1": empty, "trisc2": empty}
  kernels[role] = build_bench_kernel(role, iterations)
  program = Program(**kernels, num_cores=1)
  program.name = f"tensix_instr_bench:{role}"
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
    raise RuntimeError("L1 readback returned all 0xff; device is not responding cleanly and likely needs a host reboot")
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
    start = words[5] | (words[6] << 32)
    end = words[7] | (words[8] << 32)
    cycles = (end - start) & ((1 << 64) - 1)
    records.append(Record(
      role=role,
      test_id=words[2],
      name=spec.name,
      group=spec.group,
      mode=spec.mode,
      iterations=words[3],
      ops_per_iter=words[4],
      start=start,
      end=end,
      cycles=cycles,
      sink=words[9],
    ))
  return records


def _by_role(records: list[Record]) -> dict[str, dict[str, Record]]:
  by_role = {}
  for record in records:
    by_role.setdefault(record.role, {})[record.name] = record
  return by_role


def _sync_extra_per_push(role_records: dict[str, Record], record: Record) -> str:
  if not record.name.endswith("_sync8") and not record.name.endswith("_sync4"):
    return ""
  empty = role_records["empty"]
  sync_empty = role_records["sync_empty"]
  issue_name = record.name.replace("_sync", "_issue")
  issue = role_records.get(issue_name)
  if issue is None or record.ops_per_iter == 0:
    return ""
  fixed_sync = (sync_empty.cycles / sync_empty.iterations) - (empty.cycles / empty.iterations)
  extra = (
    (record.cycles / record.iterations)
    - (issue.cycles / issue.iterations)
    - fixed_sync
  ) / record.ops_per_iter
  return f"{extra:.3f}"


def format_table(records: list[Record]) -> str:
  by_role = _by_role(records)
  lines = [
    "| role | test | mode | pushes/iter | cycles | cyc/iter | adj cyc/push | sync extra/push | sink |",
    "|---|---|---|---:|---:|---:|---:|---:|---:|",
  ]
  for role in ROLE_NAMES:
    role_records = by_role.get(role)
    if not role_records:
      continue
    empty = role_records["empty"]
    empty_cpi = empty.cycles / empty.iterations
    for spec in SPECS:
      r = role_records[spec.name]
      cpi = r.cycles / r.iterations
      if r.ops_per_iter:
        adj = (cpi - empty_cpi) / r.ops_per_iter
        adj_text = f"{adj:.3f}"
      else:
        adj_text = ""
      extra_text = _sync_extra_per_push(role_records, r)
      lines.append(
        f"| {role} | {r.name} | {r.mode} | {r.ops_per_iter} | {r.cycles} | "
        f"{cpi:.3f} | {adj_text} | {extra_text} | 0x{r.sink:08x} |"
      )
  return "\n".join(lines)


def append_report(path: Path, *, core: tuple[int, int], iterations: int, records: list[Record]):
  table = format_table(records)
  now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
  with path.open("a", encoding="utf-8") as f:
    f.write(f"\n## Run {now}\n\n")
    f.write(f"- Core: logical `{core[0]},{core[1]}`\n")
    f.write(f"- Iterations per test: `{iterations}`\n")
    f.write("- Dispatch path: slow dispatch (`TT_USB=1`), one active TRISC role per launch\n")
    f.write("- Timed issue path: preloaded `sw raw_word, 0(INSTRN_BUF_BASE)` stores\n")
    f.write("- Drain marker: `PC_BUF_SYNC` write/read after each timed sequence for `*_sync*` rows\n\n")
    f.write("Debug L1 ranges:\n")
    for item in debug_ranges():
      f.write(f"- `{item.name}` at `0x{item.address:x}` ({item.size} bytes)\n")
    f.write("\n")
    f.write(table)
    f.write("\n")


def main():
  parser = argparse.ArgumentParser(description="Microbenchmark TRISC pushes into the Tensix instruction buffer.")
  parser.add_argument("--core", type=harness.parse_core, default=None, help="logical Tensix core X,Y; default: first program core")
  parser.add_argument("--roles", nargs="+", choices=ROLE_NAMES, default=["trisc1"], help="TRISC roles to benchmark")
  parser.add_argument("--iters", type=int, default=10_000, help="iterations per timed loop")
  parser.add_argument("--no-report", action="store_true", help="do not append results to docs/tensix-instr-microbench.md")
  parser.add_argument("--report", type=Path, default=harness.doc_path("tensix", "tensix-instr-microbench.md"), help="markdown report path")
  args = parser.parse_args()
  if args.iters <= 0:
    raise ValueError("--iters must be positive")

  all_records: list[Record] = []
  with harness.open_device() as device:
    core = args.core or device.cores[0]
    for role in args.roles:
      clear_results(device, core)
      device.run(build_program(role, args.iters))
      all_records.extend(parse_results(read_results(device, core), role))

  print(format_table(all_records))
  if not args.no_report:
    append_report(args.report, core=core, iterations=args.iters, records=all_records)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
