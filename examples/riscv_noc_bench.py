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

import riscv_core_bench as core
from asm import KernelBase
from device import Device
from dsl import (
  a2, a3, a4, a5,
  s0, s1, s2, s3, s4, s5, s6, s7, s8, s9,
  t0, t3, t4, zero,
)
from pcie import TLBWindow
from program import Program
from ttk.addrs import Core, noc_xy
from ttk.debug import DebugRange
from ttk.mailbox import BriscMailbox as BM
from ttk.noc import NOC, Noc


RESULT_BASE = 0x130000
SCRATCH_BASE = RESULT_BASE + 0x4000
HEADER_WORDS = 16
RECORD_WORDS = 16
HEADER_SIZE = HEADER_WORDS * 4
RECORD_SIZE = RECORD_WORDS * 4
RESULT_MAGIC = 0x52424E43  # "RBNC"
RECORD_MAGIC = 0x52424352  # "RBCR"
STATUS_STARTED = 0x0C000001
STATUS_DONE = 0x0C00D00D
SCRATCH_SIZE = 0x2000

OP_EMPTY = 0
OP_READ_CMD = 1
OP_READ_FLUSH = 2
OP_WRITE_CMD = 3
OP_WRITE_BARRIER = 4

OP_NAMES = {
  OP_EMPTY: "empty",
  OP_READ_CMD: "read_cmd",
  OP_READ_FLUSH: "read_flush",
  OP_WRITE_CMD: "write_cmd",
  OP_WRITE_BARRIER: "write_barrier",
}


@dataclass(frozen=True)
class BenchSpec:
  name: str
  noc: int
  op: int
  byte_count: int
  ops_per_iter: int = 1
  target: str = "local"


def _append_l1_specs(specs: list[BenchSpec], *, target: str, prefix: str):
  sizes = (4, 16, 64, 256, 512, 1024)
  for noc in (0, 1):
    specs.extend((
      BenchSpec(f"{prefix}_noc{noc}_read_4_cmd", noc, OP_READ_CMD, 4, target=target),
      BenchSpec(f"{prefix}_noc{noc}_read_4_flush", noc, OP_READ_FLUSH, 4, target=target),
      BenchSpec(f"{prefix}_noc{noc}_write_4_cmd", noc, OP_WRITE_CMD, 4, target=target),
      BenchSpec(f"{prefix}_noc{noc}_write_4_barrier", noc, OP_WRITE_BARRIER, 4, target=target),
    ))
    for size in sizes[1:]:
      specs.append(BenchSpec(f"{prefix}_noc{noc}_read_{size}_flush", noc, OP_READ_FLUSH, size, target=target))
    for size in sizes[1:]:
      specs.append(BenchSpec(f"{prefix}_noc{noc}_write_{size}_barrier", noc, OP_WRITE_BARRIER, size, target=target))


def make_specs(target: str) -> tuple[BenchSpec, ...]:
  specs: list[BenchSpec] = [BenchSpec("empty", 0, OP_EMPTY, 0, 0)]
  if target in ("local", "both"):
    _append_l1_specs(specs, target="local", prefix="local")
  if target in ("peer", "both"):
    _append_l1_specs(specs, target="peer", prefix="peer")
  return tuple(specs)


SPECS = make_specs("local")


@dataclass(frozen=True)
class Record:
  test_id: int
  name: str
  noc: int
  op: int
  byte_count: int
  iterations: int
  ops_per_iter: int
  start: int
  end: int
  cycles: int
  sink: int
  counter_before: int
  counter_after: int


class NocBenchKernel(KernelBase, Noc):
  pass


def result_size() -> int:
  return HEADER_SIZE + len(SPECS) * RECORD_SIZE


def result_size_for(specs: tuple[BenchSpec, ...]) -> int:
  return HEADER_SIZE + len(specs) * RECORD_SIZE


def debug_ranges(specs: tuple[BenchSpec, ...] = SPECS) -> tuple[DebugRange, ...]:
  return (
    DebugRange(0, "l1", RESULT_BASE, result_size_for(specs), "riscv_noc_bench_results"),
    DebugRange(1, "l1", SCRATCH_BASE, SCRATCH_SIZE, "riscv_noc_bench_scratch"),
  )


def emit_header(fw: KernelBase, *, iterations: int, specs: tuple[BenchSpec, ...], status: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, 2, len(specs), RECORD_WORDS, status, iterations,
    RESULT_BASE, SCRATCH_BASE, SCRATCH_SIZE,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off in range(9, HEADER_WORDS):
    fw.sw(zero, s2, off * 4)
  return fw


def emit_record(
  fw: KernelBase,
  *,
  test_id: int,
  iterations: int,
  spec: BenchSpec,
  start_lo,
  start_hi,
  end_lo,
  end_hi,
  sink=s1,
  counter_before=s7,
  counter_after=s8,
):
  fw.li(s2, RESULT_BASE + HEADER_SIZE + test_id * RECORD_SIZE)
  for off, value in enumerate((
    RECORD_MAGIC,
    test_id,
    spec.noc,
    spec.op,
    spec.byte_count,
    iterations,
    spec.ops_per_iter,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off, reg in enumerate((start_lo, start_hi, end_lo, end_hi, sink, counter_before, counter_after), start=7):
    fw.sw(reg, s2, off * 4)
  fw.sw(zero, s2, 14 * 4)
  fw.sw(zero, s2, 15 * 4)
  return fw


def emit_counter_read(fw: KernelBase, noc: int, counter: int, out, *, addr=t3):
  fw.li(addr, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  return fw.lw(out, addr, 0)


def emit_setup(fw: NocBenchKernel):
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s9,))
  fw.li(s1, 0x5A170C00)
  fw.li(s2, SCRATCH_BASE)
  fw.li(s3, SCRATCH_BASE + 0x800)
  for off in range(0, 1024, 4):
    fw.li(t0, 0xA5000000 | off)
    fw.sw(t0, s2, off)
    fw.sw(zero, s3, off)
  fw.local_noc0_coord(s5, x_addr=BM.MY_X, y_addr=BM.MY_Y)
  return fw.fence()


def emit_noc_op(fw: NocBenchKernel, spec: BenchSpec):
  target_coord = s9 if spec.target == "peer" else s5
  if spec.op == OP_EMPTY:
    fw.addi(s1, s1, 1)
    return fw
  if spec.op in (OP_READ_CMD, OP_READ_FLUSH):
    fw.noc_read(spec.noc, 1, s2, 0, target_coord, s3, s4, ret_coord=s5, a=t3, v=t4)
    fw.addi(s6, s6, 1)
    if spec.op == OP_READ_FLUSH:
      fw.noc_reads_flushed(spec.noc, s6, addr=t3, val=t4)
    return fw
  if spec.op in (OP_WRITE_CMD, OP_WRITE_BARRIER):
    fw.noc_write(spec.noc, 0, s2, s3, 0, target_coord, s4, posted=False, a=t3, v=t4)
    fw.addi(s6, s6, 1)
    if spec.op == OP_WRITE_BARRIER:
      fw.noc_write_barrier(spec.noc, s6, addr=t3, val=t4)
    return fw
  raise ValueError(f"unknown NoC op {spec.op}")


def emit_cleanup(fw: NocBenchKernel, spec: BenchSpec):
  if spec.op in (OP_READ_CMD, OP_READ_FLUSH):
    fw.noc_reads_flushed(spec.noc, s6, addr=t3, val=t4)
    emit_counter_read(fw, spec.noc, NOC.NIU_MST_RD_RESP_RECEIVED, s8)
    return fw
  if spec.op in (OP_WRITE_CMD, OP_WRITE_BARRIER):
    fw.noc_write_barrier(spec.noc, s6, addr=t3, val=t4)
    emit_counter_read(fw, spec.noc, NOC.NIU_MST_WR_ACK_RECEIVED, s8)
    if spec.target == "peer":
      emit_counter_read(fw, spec.noc, NOC.NIU_MST_RD_RESP_RECEIVED, t0, addr=t3)
      fw.addi(t0, t0, 1)
      fw.noc_read(spec.noc, 1, s3, 0, s9, s3, s4, ret_coord=s5, a=t3, v=t4)
      fw.noc_reads_flushed(spec.noc, t0, addr=t3, val=t4)
    return fw
  fw.mv(s8, s7)
  return fw


def emit_timed_loop(fw: NocBenchKernel, *, test_id: int, iterations: int, spec: BenchSpec):
  emit_setup(fw)
  fw.li(s4, spec.byte_count)
  if spec.op in (OP_READ_CMD, OP_READ_FLUSH):
    emit_counter_read(fw, spec.noc, NOC.NIU_MST_RD_RESP_RECEIVED, s7)
  elif spec.op in (OP_WRITE_CMD, OP_WRITE_BARRIER):
    emit_counter_read(fw, spec.noc, NOC.NIU_MST_WR_ACK_RECEIVED, s7)
  else:
    fw.mv(s7, zero)
  fw.mv(s6, s7)

  core.read_wall_clock(fw, a2, a3)
  fw.li(s0, iterations)
  loop = fw._new_label(f"bench_{spec.name}")
  done = fw._new_label(f"bench_{spec.name}_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  emit_noc_op(fw, spec)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  core.read_wall_clock(fw, a4, a5)

  emit_cleanup(fw, spec)
  fw.lw(s1, s3, 0)
  emit_record(
    fw,
    test_id=test_id,
    iterations=iterations,
    spec=spec,
    start_lo=a2,
    start_hi=a3,
    end_lo=a4,
    end_hi=a5,
  )
  return fw


def build_bench_kernel(iterations: int, specs: tuple[BenchSpec, ...]) -> KernelBase:
  fw = NocBenchKernel()
  emit_header(fw, iterations=iterations, specs=specs, status=STATUS_STARTED)
  for test_id, spec in enumerate(specs):
    emit_timed_loop(fw, test_id=test_id, iterations=iterations, spec=spec)
  emit_header(fw, iterations=iterations, specs=specs, status=STATUS_DONE)
  return fw.ret()


def _return_kernel() -> KernelBase:
  return KernelBase().ret()


def build_program(iterations: int, specs: tuple[BenchSpec, ...], *, source_core: Core, peer_core: Core | None) -> Program:
  empty = KernelBase()
  bench = build_bench_kernel(iterations, specs)
  bench.rta(lambda _x, _y: [noc_xy(*(peer_core or source_core))])
  if peer_core is None:
    program = Program(
      brisc=bench,
      ncrisc=empty,
      trisc0=empty,
      trisc1=empty,
      trisc2=empty,
      num_cores=1,
    )
  else:
    brisc_recv = _return_kernel()
    program = Program(
      brisc=bench,
      brisc_recv=brisc_recv,
      ncrisc=empty,
      trisc0=empty,
      trisc1=empty,
      trisc2=empty,
      grid=((source_core[1],), (source_core[0], peer_core[0])),
    )
  program.name = "riscv_noc_bench:brisc"
  return program


def select_source_and_peer(cores: list[Core], *, source: Core | None, peer: Core | None, needs_peer: bool) -> tuple[Core, Core | None]:
  if not cores:
    raise RuntimeError("device reported no program cores")
  core_set = set(cores)
  if source is not None and source not in core_set:
    raise ValueError(f"--core {source[0]},{source[1]} is not a program core")
  if peer is not None and peer not in core_set:
    raise ValueError(f"--peer-core {peer[0]},{peer[1]} is not a program core")

  if not needs_peer:
    return source or cores[0], None

  if source is not None and peer is not None:
    if source[1] != peer[1]:
      raise ValueError("peer mode currently needs --core and --peer-core on the same logical row")
    if source == peer:
      raise ValueError("--peer-core must differ from --core")
    return source, peer

  if source is not None:
    row_peers = sorted(c for c in cores if c[1] == source[1] and c != source)
    if not row_peers:
      raise ValueError(f"no same-row peer found for source core {source}")
    return source, peer or row_peers[0]

  rows: dict[int, list[int]] = {}
  for x, y in cores:
    rows.setdefault(y, []).append(x)
  for y, xs in sorted(rows.items()):
    xs = sorted(xs)
    if len(xs) >= 2:
      return (xs[0], y), (xs[1], y)
  raise ValueError("peer mode needs at least two program cores on the same logical row")


def read_results(device: Device, source_core: Core, specs: tuple[BenchSpec, ...]) -> bytes:
  result_range = debug_ranges(specs)[0]
  device.dev.set_power_state(True)
  try:
    with TLBWindow(device.dev, start=source_core) as win:
      blob = win.read(result_range.address, result_range.size)
  finally:
    device.dev.set_power_state(False)
  if blob and all(b == 0xFF for b in blob):
    raise RuntimeError("L1 readback returned all 0xff; device is not responding cleanly and likely needs a host reboot")
  return blob


def clear_ranges(device: Device, cores: list[Core], specs: tuple[BenchSpec, ...]):
  seed = bytearray(1024)
  for off in range(0, len(seed), 4):
    struct.pack_into("<I", seed, off, 0xA5000000 | off)
  device.dev.set_power_state(True)
  try:
    with TLBWindow(device.dev, start=cores[0]) as win:
      for target_core in cores:
        win.target(target_core)
        for item in debug_ranges(specs):
          win.write(item.address, b"\0" * item.size)
        win.write(SCRATCH_BASE, seed)
  finally:
    device.dev.set_power_state(False)


def parse_results(blob: bytes, specs: tuple[BenchSpec, ...]) -> list[Record]:
  header = struct.unpack_from("<" + "I" * HEADER_WORDS, blob, 0)
  if header[0] != RESULT_MAGIC:
    raise RuntimeError(f"bad result magic 0x{header[0]:08x}")
  if header[4] != STATUS_DONE:
    raise RuntimeError(f"benchmark did not finish, status=0x{header[4]:08x}")
  if header[2] != len(specs) or header[3] != RECORD_WORDS:
    raise RuntimeError(f"unexpected result layout: specs={header[2]} record_words={header[3]}")

  records = []
  for test_id, spec in enumerate(specs):
    off = HEADER_SIZE + test_id * RECORD_SIZE
    words = struct.unpack_from("<" + "I" * RECORD_WORDS, blob, off)
    if words[0] != RECORD_MAGIC:
      raise RuntimeError(f"{spec.name}: bad record magic 0x{words[0]:08x}")
    start = words[7] | (words[8] << 32)
    end = words[9] | (words[10] << 32)
    records.append(Record(
      test_id=words[1],
      name=spec.name,
      noc=words[2],
      op=words[3],
      byte_count=words[4],
      iterations=words[5],
      ops_per_iter=words[6],
      start=start,
      end=end,
      cycles=(end - start) & ((1 << 64) - 1),
      sink=words[11],
      counter_before=words[12],
      counter_after=words[13],
    ))
  return records


def format_table(records: list[Record], specs: tuple[BenchSpec, ...]) -> str:
  by_name = {record.name: record for record in records}
  empty = by_name["empty"]
  empty_cpi = empty.cycles / empty.iterations
  lines = [
    "| test | noc | op | bytes | cycles | cyc/iter | adj cyc/op | bytes/cyc | counter delta | sink |",
    "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|",
  ]
  for spec in specs:
    r = by_name[spec.name]
    cpi = r.cycles / r.iterations
    if r.ops_per_iter:
      baseline = empty_cpi * r.iterations
      adj = (r.cycles - baseline) / (r.iterations * r.ops_per_iter)
      adj_text = f"{adj:.3f}"
      bpc = r.byte_count / adj if adj > 0 else 0.0
      bpc_text = f"{bpc:.3f}" if r.byte_count else ""
    else:
      adj_text = ""
      bpc_text = ""
    counter_delta = (r.counter_after - r.counter_before) & 0xFFFFFFFF
    noc_text = "" if r.op == OP_EMPTY else str(r.noc)
    lines.append(
      f"| {r.name} | {noc_text} | {OP_NAMES.get(r.op, str(r.op))} | {r.byte_count} | "
      f"{r.cycles} | {cpi:.3f} | {adj_text} | {bpc_text} | {counter_delta} | 0x{r.sink:08x} |"
    )
  return "\n".join(lines)


def append_report(
  path: Path, *, source_core: Core, peer_core: Core | None, target: str,
  iterations: int, specs: tuple[BenchSpec, ...], records: list[Record],
):
  now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
  with path.open("a", encoding="utf-8") as f:
    f.write(f"\n## Run {now}\n\n")
    f.write(f"- Source core: logical `{source_core[0]},{source_core[1]}`\n")
    if peer_core is not None:
      f.write(f"- Peer core: logical `{peer_core[0]},{peer_core[1]}`\n")
    f.write(f"- Target mode: `{target}`\n")
    f.write(f"- Iterations per test: `{iterations}`\n")
    f.write("- Dispatch path: slow dispatch (`TT_USB=1`), BRISC only\n")
    f.write("- Traffic: local L1 and/or peer-tile L1 unicast; no DRAM writes and no multicast\n\n")
    f.write("Debug L1 ranges:\n")
    for item in debug_ranges(specs):
      f.write(f"- `{item.name}` at `0x{item.address:x}` ({item.size} bytes)\n")
    f.write("\n")
    f.write(format_table(records, specs))
    f.write("\n")


def main():
  parser = argparse.ArgumentParser(description="Microbenchmark BRISC-driven local and peer L1 NoC command, flush, and barrier costs.")
  parser.add_argument("--core", type=core.parse_core, default=None, help="logical source Tensix core X,Y; default: first suitable program core")
  parser.add_argument("--peer-core", type=core.parse_core, default=None, help="logical peer Tensix core X,Y for peer/both target modes")
  parser.add_argument("--target", choices=("local", "peer", "both"), default="local", help="NoC L1 target set to benchmark")
  parser.add_argument("--iters", type=int, default=1000, help="iterations per timed loop")
  parser.add_argument("--no-report", action="store_true", help="do not append results to docs/noc-microbench.md")
  parser.add_argument("--report", type=Path, default=Path("docs/noc-microbench.md"), help="markdown report path")
  args = parser.parse_args()
  if args.iters <= 0:
    raise ValueError("--iters must be positive")

  os.environ.setdefault("TT_USB", "1")
  specs = make_specs(args.target)
  device = Device()
  try:
    source_core, peer_core = select_source_and_peer(
      device.cores,
      source=args.core,
      peer=args.peer_core,
      needs_peer=args.target in ("peer", "both"),
    )
    clear_cores = [source_core] + ([peer_core] if peer_core is not None else [])
    clear_ranges(device, clear_cores, specs)
    device.run(build_program(args.iters, specs, source_core=source_core, peer_core=peer_core))
    records = parse_results(read_results(device, source_core, specs), specs)
  finally:
    device.close()

  print(format_table(records, specs))
  if not args.no_report:
    append_report(
      args.report,
      source_core=source_core,
      peer_core=peer_core,
      target=args.target,
      iterations=args.iters,
      specs=specs,
      records=records,
    )
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
