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
  sys.path.insert(0, str(Path(__file__).resolve().parent))

import riscv_core_bench as core
import riscv_noc_hop_sweep as hops
from asm import KernelBase
from device import Device
from dsl import a2, a3, a4, a5, s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, t0, t3, t4, zero
from pcie import TLBWindow
from program import DevMsgs, Program, Run, UnicastWrite
from ttk.addrs import Core, noc_xy
from ttk.mailbox import BriscMailbox as BM
from ttk.noc import NOC, Noc
from ttk.tensix import TensixL1


RESULT_BASE = 0x150000
STREAM_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
STREAM_SINK = STREAM_BASE + NOC.MAX_BURST_SIZE
HEADER_WORDS = 16
RECORD_WORDS = 16
HEADER_SIZE = HEADER_WORDS * 4
RECORD_SIZE = RECORD_WORDS * 4
RESULT_MAGIC = 0x52534E53  # "RSNS"
RECORD_MAGIC = 0x52534E52  # "RSNR"
STATUS_STARTED = 0x51000001
STATUS_DONE = 0x5100D00D

OP_EMPTY = 0
OP_READ = 1
OP_WRITE = 2
OP_NAMES = {OP_EMPTY: "empty", OP_READ: "read_stream", OP_WRITE: "write_stream"}


@dataclass(frozen=True)
class StreamSpec:
  name: str
  noc: int
  op: int


@dataclass(frozen=True)
class StreamRecord:
  name: str
  noc: int
  op: int
  stream_bytes: int
  repeats: int
  chunks_per_repeat: int
  cycles: int
  sink: int
  counter_delta: int


@dataclass(frozen=True)
class StreamRun:
  noc: int
  source: Core
  peer: Core
  logical_distance: int
  records: list[StreamRecord]


class StreamKernel(KernelBase, Noc):
  pass


def specs_for_noc(noc: int) -> tuple[StreamSpec, ...]:
  return (
    StreamSpec("empty", noc, OP_EMPTY),
    StreamSpec(f"noc{noc}_read_stream", noc, OP_READ),
    StreamSpec(f"noc{noc}_write_stream", noc, OP_WRITE),
  )


def result_size(specs: tuple[StreamSpec, ...]) -> int:
  return HEADER_SIZE + len(specs) * RECORD_SIZE


def emit_counter_read(fw: KernelBase, noc: int, counter: int, out, *, addr=t3):
  fw.li(addr, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  return fw.lw(out, addr, 0)


def emit_header(fw: KernelBase, *, specs: tuple[StreamSpec, ...], stream_bytes: int, repeats: int, status: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, 1, len(specs), RECORD_WORDS, status, stream_bytes,
    repeats, NOC.MAX_BURST_SIZE, STREAM_BASE, STREAM_SINK,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off in range(10, HEADER_WORDS):
    fw.sw(zero, s2, off * 4)
  return fw


def emit_record(
  fw: KernelBase,
  *,
  test_id: int,
  spec: StreamSpec,
  stream_bytes: int,
  repeats: int,
  chunks_per_repeat: int,
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
    RECORD_MAGIC, test_id, spec.noc, spec.op, stream_bytes,
    repeats, chunks_per_repeat,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off, reg in enumerate((start_lo, start_hi, end_lo, end_hi, sink, counter_before, counter_after), start=7):
    fw.sw(reg, s2, off * 4)
  fw.sw(zero, s2, 14 * 4)
  fw.sw(zero, s2, 15 * 4)
  return fw


def emit_setup(fw: StreamKernel):
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s9,))
  fw.local_noc0_coord(s5, x_addr=BM.MY_X, y_addr=BM.MY_Y)
  fw.li(s1, 0x5A170C00)
  fw.li(s2, STREAM_BASE)
  fw.li(s3, STREAM_BASE)
  fw.li(s4, NOC.MAX_BURST_SIZE)
  return fw.fence()


def emit_stream_body(fw: StreamKernel, spec: StreamSpec, *, repeats: int, chunks_per_repeat: int):
  if spec.op == OP_EMPTY:
    fw.li(s0, repeats * chunks_per_repeat)
    loop = fw._new_label("empty_stream_loop")
    done = fw._new_label("empty_stream_done")
    fw.label(loop)
    fw.beq(s0, zero, done)
    fw.addi(s1, s1, 1)
    fw.addi(s0, s0, -1)
    fw.j(loop)
    fw.label(done)
    return fw

  fw.li(s0, repeats)
  fw.li(s8, NOC.MAX_BURST_SIZE)
  outer = fw._new_label(f"{spec.name}_outer")
  outer_done = fw._new_label(f"{spec.name}_outer_done")
  fw.label(outer)
  fw.beq(s0, zero, outer_done)
  fw.li(s3, STREAM_BASE)
  fw.li(s1, chunks_per_repeat)
  inner = fw._new_label(f"{spec.name}_inner")
  inner_done = fw._new_label(f"{spec.name}_inner_done")
  fw.label(inner)
  fw.beq(s1, zero, inner_done)
  if spec.op == OP_READ:
    fw.noc_read(spec.noc, 1, s3, 0, s9, STREAM_SINK, s4, ret_coord=s5, a=t3, v=t4)
  elif spec.op == OP_WRITE:
    fw.noc_write(spec.noc, 0, s2, s3, 0, s9, s4, posted=False, a=t3, v=t4)
  else:
    raise ValueError(f"unknown stream op {spec.op}")
  fw.addi(s6, s6, 1)
  fw.add(s3, s3, s8)
  fw.addi(s1, s1, -1)
  fw.j(inner)
  fw.label(inner_done)
  fw.addi(s0, s0, -1)
  fw.j(outer)
  fw.label(outer_done)
  return fw


def emit_timed_stream(
  fw: StreamKernel, *, test_id: int, spec: StreamSpec,
  stream_bytes: int, repeats: int, chunks_per_repeat: int,
):
  emit_setup(fw)
  if spec.op == OP_READ:
    emit_counter_read(fw, spec.noc, NOC.NIU_MST_RD_RESP_RECEIVED, s7)
  elif spec.op == OP_WRITE:
    emit_counter_read(fw, spec.noc, NOC.NIU_MST_WR_ACK_RECEIVED, s7)
  else:
    fw.mv(s7, zero)
  fw.mv(s6, s7)

  core.read_wall_clock(fw, a2, a3)
  emit_stream_body(fw, spec, repeats=repeats, chunks_per_repeat=chunks_per_repeat)
  if spec.op == OP_READ:
    fw.noc_reads_flushed(spec.noc, s6, addr=t3, val=t4)
  elif spec.op == OP_WRITE:
    fw.noc_write_barrier(spec.noc, s6, addr=t3, val=t4)
  core.read_wall_clock(fw, a4, a5)

  if spec.op == OP_READ:
    emit_counter_read(fw, spec.noc, NOC.NIU_MST_RD_RESP_RECEIVED, s8)
  elif spec.op == OP_WRITE:
    emit_counter_read(fw, spec.noc, NOC.NIU_MST_WR_ACK_RECEIVED, s8)
    emit_counter_read(fw, spec.noc, NOC.NIU_MST_RD_RESP_RECEIVED, t0, addr=t3)
    fw.addi(t0, t0, 1)
    fw.noc_read(spec.noc, 1, STREAM_BASE, 0, s9, STREAM_SINK, s4, ret_coord=s5, a=t3, v=t4)
    fw.noc_reads_flushed(spec.noc, t0, addr=t3, val=t4)
  else:
    fw.mv(s8, s7)
  fw.li(t0, STREAM_SINK)
  fw.lw(s1, t0, 0)
  emit_record(
    fw,
    test_id=test_id,
    spec=spec,
    stream_bytes=stream_bytes,
    repeats=repeats,
    chunks_per_repeat=chunks_per_repeat,
    start_lo=a2,
    start_hi=a3,
    end_lo=a4,
    end_hi=a5,
  )
  return fw


def build_kernel(specs: tuple[StreamSpec, ...], *, stream_bytes: int, repeats: int) -> KernelBase:
  chunks_per_repeat = stream_bytes // NOC.MAX_BURST_SIZE
  fw = StreamKernel()
  emit_header(fw, specs=specs, stream_bytes=stream_bytes, repeats=repeats, status=STATUS_STARTED)
  for test_id, spec in enumerate(specs):
    emit_timed_stream(
      fw,
      test_id=test_id,
      spec=spec,
      stream_bytes=stream_bytes,
      repeats=repeats,
      chunks_per_repeat=chunks_per_repeat,
    )
  emit_header(fw, specs=specs, stream_bytes=stream_bytes, repeats=repeats, status=STATUS_DONE)
  return fw.ret()


def build_program(specs: tuple[StreamSpec, ...], *, stream_bytes: int, repeats: int, source: Core, peer: Core) -> Program:
  empty = KernelBase()
  passive = KernelBase().ret()
  bench = build_kernel(specs, stream_bytes=stream_bytes, repeats=repeats)
  bench.rta(lambda _x, _y: [noc_xy(*peer)])
  program = Program(
    brisc=bench,
    brisc_recv=passive,
    ncrisc=empty,
    trisc0=empty,
    trisc1=empty,
    trisc2=empty,
    grid=((source[1],), (source[0], peer[0])),
  )
  program.name = f"riscv_noc_stream_sweep:noc{specs[0].noc}"
  return program


def _stream_program(brisc: KernelBase) -> Program:
  empty = KernelBase()
  return Program(
    brisc=brisc,
    ncrisc=empty,
    trisc0=empty,
    trisc1=empty,
    trisc2=empty,
    num_cores=1,
  )


class PairProgram:
  def __init__(self, specs: tuple[StreamSpec, ...], *, stream_bytes: int, repeats: int, source: Core, peer: Core):
    self.specs = specs
    self.stream_bytes = stream_bytes
    self.repeats = repeats
    self.source = source
    self.peer = peer
    self.name = f"riscv_noc_stream_pair:noc{specs[0].noc}:{source}->{peer}"

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    bench = build_kernel(self.specs, stream_bytes=self.stream_bytes, repeats=self.repeats)
    bench.rta(lambda _x, _y: [noc_xy(*self.peer)])
    source_segments = _stream_program(bench).layout(
      core_xy=self.source,
      dispatch_mode=dispatch_mode,
      host_assigned_id=host_assigned_id,
    )

    per_core_segments = {self.source: source_segments}
    target_cores = [self.source]
    if self.peer != self.source:
      passive_segments = _stream_program(KernelBase().ret()).layout(
        core_xy=self.peer,
        dispatch_mode=dispatch_mode,
        host_assigned_id=host_assigned_id,
      )
      per_core_segments[self.peer] = passive_segments
      target_cores.append(self.peer)

    reset_blob = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_RESET_READ_PTR_FROM_HOST)
    commands = [
      UnicastWrite(target_cores, TensixL1.GO_MSG, [reset_blob] * len(target_cores)),
      UnicastWrite(target_cores, TensixL1.GO_MSG_INDEX, [b"\0\0\0\0"] * len(target_cores)),
    ]
    for core in target_cores:
      for segment in per_core_segments[core]:
        commands.append(UnicastWrite([core], segment.addr, [segment.data]))
    commands.append(Run(target_cores))
    return commands


def build_pair_program(
  specs: tuple[StreamSpec, ...], *, stream_bytes: int, repeats: int, source: Core, peer: Core,
) -> PairProgram:
  return PairProgram(specs, stream_bytes=stream_bytes, repeats=repeats, source=source, peer=peer)


def clear_ranges(device: Device, cores: list[Core], specs: tuple[StreamSpec, ...], *, stream_bytes: int):
  seed = bytearray(NOC.MAX_BURST_SIZE)
  for off in range(0, len(seed), 4):
    struct.pack_into("<I", seed, off, 0xA5000000 | off)
  stream_seed = bytes(seed) * (stream_bytes // NOC.MAX_BURST_SIZE)
  device.dev.set_power_state(True)
  try:
    with TLBWindow(device.dev, start=cores[0]) as win:
      for target in cores:
        win.target(target)
        win.write(RESULT_BASE, b"\0" * result_size(specs))
        win.write(STREAM_BASE, stream_seed)
        win.write(STREAM_SINK, b"\0" * NOC.MAX_BURST_SIZE)
  finally:
    device.dev.set_power_state(False)


def read_results(device: Device, source: Core, specs: tuple[StreamSpec, ...]) -> bytes:
  device.dev.set_power_state(True)
  try:
    with TLBWindow(device.dev, start=source) as win:
      blob = win.read(RESULT_BASE, result_size(specs))
  finally:
    device.dev.set_power_state(False)
  if blob and all(b == 0xFF for b in blob):
    raise RuntimeError("L1 readback returned all 0xff; device is not responding cleanly")
  return blob


def parse_results(blob: bytes, specs: tuple[StreamSpec, ...]) -> list[StreamRecord]:
  header = struct.unpack_from("<" + "I" * HEADER_WORDS, blob, 0)
  if header[0] != RESULT_MAGIC:
    raise RuntimeError(f"bad result magic 0x{header[0]:08x}")
  if header[4] != STATUS_DONE:
    raise RuntimeError(f"benchmark did not finish, status=0x{header[4]:08x}")
  records = []
  for test_id, spec in enumerate(specs):
    off = HEADER_SIZE + test_id * RECORD_SIZE
    words = struct.unpack_from("<" + "I" * RECORD_WORDS, blob, off)
    if words[0] != RECORD_MAGIC:
      raise RuntimeError(f"{spec.name}: bad record magic 0x{words[0]:08x}")
    start = words[7] | (words[8] << 32)
    end = words[9] | (words[10] << 32)
    records.append(StreamRecord(
      name=spec.name,
      noc=words[2],
      op=words[3],
      stream_bytes=words[4],
      repeats=words[5],
      chunks_per_repeat=words[6],
      cycles=(end - start) & ((1 << 64) - 1),
      sink=words[11],
      counter_delta=(words[13] - words[12]) & 0xFFFFFFFF,
    ))
  return records


def adjusted(records: list[StreamRecord]) -> dict[int, tuple[float, float]]:
  empty = next(record for record in records if record.op == OP_EMPTY)
  out = {}
  for record in records:
    if record.op == OP_EMPTY:
      continue
    cycles = record.cycles - empty.cycles
    bytes_total = record.stream_bytes * record.repeats
    out[record.op] = (cycles, bytes_total / cycles if cycles > 0 else 0.0)
  return out


def format_summary(runs: list[StreamRun]) -> str:
  lines = [
    "| noc | source | peer | logical dist | bytes/op | repeats | total MiB/op | read cyc | read B/cyc | write cyc | write B/cyc | read sink | write sink |",
    "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
  ]
  for run in runs:
    by_op = {record.op: record for record in run.records}
    adj = adjusted(run.records)
    read_cycles, read_bpc = adj[OP_READ]
    write_cycles, write_bpc = adj[OP_WRITE]
    stream_bytes = by_op[OP_READ].stream_bytes
    repeats = by_op[OP_READ].repeats
    total_mib = stream_bytes * repeats / (1024 * 1024)
    lines.append(
      f"| {run.noc} | `{run.source[0]},{run.source[1]}` | `{run.peer[0]},{run.peer[1]}` | {run.logical_distance} | "
      f"{stream_bytes} | {repeats} | {total_mib:.1f} | {read_cycles:.0f} | {read_bpc:.3f} | "
      f"{write_cycles:.0f} | {write_bpc:.3f} | 0x{by_op[OP_READ].sink:08x} | 0x{by_op[OP_WRITE].sink:08x} |"
    )
  return "\n".join(lines)


def append_report(path: Path, *, mode: str, runs: list[StreamRun]):
  now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
  with path.open("a", encoding="utf-8") as f:
    f.write(f"\n## Run {now}\n\n")
    f.write(f"- Mode: `{mode}`\n")
    f.write("- Traffic: same-row peer-tile L1 unicast stream, chunked into 16 KiB NoC commands\n")
    f.write("- Timing: issue all chunks, then one read flush or write barrier; subtract empty loop\n")
    if mode == "row":
      f.write("- Direction policy: NoC0 to the right, NoC1 to the left; no DRAM writes and no multicast\n\n")
    else:
      f.write("- Target policy: all selected program cores transfer to one fixed target; no DRAM writes and no multicast\n\n")
    f.write(format_summary(runs))
    f.write("\n")


def parse_core_default(text: str) -> Core:
  return core.parse_core(text)


def all_to_one_pairs(cores: list[Core], *, target: Core, max_sources: int | None) -> list[tuple[Core, Core, int]]:
  if target not in set(cores):
    raise ValueError(f"--target-core {target[0]},{target[1]} is not a program core")
  pairs = [(source, target, abs(source[0] - target[0]) + abs(source[1] - target[1])) for source in sorted(cores, key=lambda c: (c[1], c[0]))]
  if max_sources is not None:
    pairs = pairs[:max_sources]
  return pairs


def main():
  parser = argparse.ArgumentParser(description="Sweep peer L1 NoC stream bandwidth by source/target placement.")
  parser.add_argument("--mode", choices=("row", "all-to-one"), default="row", help="row direction sweep or all sources to one target")
  parser.add_argument("--nocs", type=hops.parse_nocs, default=(0, 1), help="comma-separated NoC ids to sweep, default: 0,1")
  parser.add_argument("--row", type=int, default=None, help="logical row to sweep; default: row with most program cores")
  parser.add_argument("--core", type=core.parse_core, default=None, help="explicit source core X,Y")
  parser.add_argument("--target-core", type=parse_core_default, default=(1, 2), help="fixed target core for --mode all-to-one")
  parser.add_argument("--max-sources", type=int, default=None, help="limit source count for --mode all-to-one")
  parser.add_argument("--max-hops", type=int, default=None, help="maximum logical x distance to include")
  parser.add_argument("--bytes", type=int, default=1024 * 1024, help="bytes transferred per repeat; must be a multiple of 16 KiB")
  parser.add_argument("--repeats", type=int, default=8, help="stream repeats per timed op")
  parser.add_argument("--no-report", action="store_true", help="do not append results to docs/noc-stream-sweep.md")
  parser.add_argument("--report", type=Path, default=Path("docs/noc-stream-sweep.md"), help="markdown report path")
  args = parser.parse_args()
  if args.bytes <= 0 or args.bytes % NOC.MAX_BURST_SIZE:
    raise ValueError("--bytes must be a positive multiple of 16 KiB")
  if args.bytes > (RESULT_BASE - STREAM_BASE):
    raise ValueError(f"--bytes must fit below result range; max is {RESULT_BASE - STREAM_BASE}")
  if args.repeats <= 0:
    raise ValueError("--repeats must be positive")
  if args.max_sources is not None and args.max_sources <= 0:
    raise ValueError("--max-sources must be positive")

  os.environ.setdefault("TT_USB", "1")
  device = Device()
  runs: list[StreamRun] = []
  try:
    for noc in args.nocs:
      specs = specs_for_noc(noc)
      if args.mode == "row":
        pairs = hops.build_pairs(
          device.cores,
          noc=noc,
          row=args.row,
          source=args.core,
          max_hops=args.max_hops,
        )
      else:
        pairs = all_to_one_pairs(device.cores, target=args.target_core, max_sources=args.max_sources)
      for source, peer, logical_distance in pairs:
        clear_ranges(device, [source, peer], specs, stream_bytes=args.bytes)
        program = (
          build_program(specs, stream_bytes=args.bytes, repeats=args.repeats, source=source, peer=peer)
          if args.mode == "row"
          else build_pair_program(specs, stream_bytes=args.bytes, repeats=args.repeats, source=source, peer=peer)
        )
        device.run(program)
        records = parse_results(read_results(device, source, specs), specs)
        runs.append(StreamRun(noc=noc, source=source, peer=peer, logical_distance=logical_distance, records=records))
  finally:
    device.close()

  print(format_summary(runs))
  if not args.no_report:
    append_report(args.report, mode=args.mode, runs=runs)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
