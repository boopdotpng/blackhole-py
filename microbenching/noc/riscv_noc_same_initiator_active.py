#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
from asm import KernelBase  # noqa: E402
from device import Device  # noqa: E402
from dsl import a2, a3, a4, a5, s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, t0, t1, t3, t4, zero  # noqa: E402
from program import DevMsgs, Program, Run, UnicastWrite  # noqa: E402
from ttk.addrs import Core, noc_xy  # noqa: E402
from ttk.mailbox import BriscMailbox as BM  # noqa: E402
from ttk.noc import NOC, Noc  # noqa: E402
from ttk.tensix import TensixL1  # noqa: E402


RESULT_BASE = 0x150000
RESULT_WORDS = 24
RESULT_SIZE = RESULT_WORDS * 4
RESULT_MAGIC = 0x53494E49  # "SINI"
STATUS_STARTED = 0x51000001
STATUS_DONE = 0x5100D00D
STREAM_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
READ_SINK = STREAM_BASE + NOC.MAX_BURST_SIZE

MODE_READ = "read"
MODE_WRITE = "write"
MODE_WR_READ = "wr-read"
MODE_READ_WR = "read-wr"
MODES = (MODE_READ, MODE_WRITE, MODE_WR_READ, MODE_READ_WR)


class SameInitiatorKernel(KernelBase, Noc):
  pass


@dataclass(frozen=True)
class Result:
  noc: int
  mode: str
  source: Core
  read_target: Core
  write_target: Core
  packet_bytes: int
  iters: int
  cycles: int
  wr_delta: int
  rd_delta: int
  sink: int
  write_seen: int

  @property
  def bytes_per_cycle(self) -> float:
    streams = int(self.mode in (MODE_WRITE, MODE_WR_READ, MODE_READ_WR)) + int(self.mode in (MODE_READ, MODE_WR_READ, MODE_READ_WR))
    return streams * self.packet_bytes * self.iters / self.cycles if self.cycles > 0 else 0.0


def parse_core(text: str) -> Core:
  return harness.parse_core(text)


def parse_modes(text: str) -> tuple[str, ...]:
  modes = tuple(part.strip() for part in text.split(",") if part.strip())
  bad = sorted(set(modes) - set(MODES))
  if bad:
    raise argparse.ArgumentTypeError(f"unknown modes: {', '.join(bad)}")
  if not modes:
    raise argparse.ArgumentTypeError("expected comma-separated modes")
  return modes


def emit_counter_read(fw: KernelBase, noc: int, counter: int, out, *, addr=t3):
  fw.li(addr, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  return fw.lw(out, addr, 0)


def emit_header(fw: KernelBase, *, noc: int, mode_id: int, packet_bytes: int, iters: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, STATUS_STARTED, noc, mode_id, packet_bytes, iters, STREAM_BASE, READ_SINK,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off in range(8, RESULT_WORDS):
    fw.sw(zero, s2, off * 4)
  return fw


def build_kernel(*, noc: int, mode: str, packet_bytes: int, iters: int) -> KernelBase:
  mode_id = MODES.index(mode)
  do_read = mode in (MODE_READ, MODE_WR_READ, MODE_READ_WR)
  do_write = mode in (MODE_WRITE, MODE_WR_READ, MODE_READ_WR)
  fw = SameInitiatorKernel()
  emit_header(fw, noc=noc, mode_id=mode_id, packet_bytes=packet_bytes, iters=iters)
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s8, s9))
  fw.local_noc_coord(noc, s5, x_addr=BM.MY_X, y_addr=BM.MY_Y)
  fw.li(s2, STREAM_BASE)
  fw.li(s3, READ_SINK)
  fw.li(s4, packet_bytes)
  emit_counter_read(fw, noc, NOC.NIU_MST_WR_ACK_RECEIVED, s6)
  emit_counter_read(fw, noc, NOC.NIU_MST_RD_RESP_RECEIVED, s7)
  fw.mv(s10, s6)
  fw.mv(s11, s7)

  harness.read_wall_clock(fw, a2, a3)
  fw.li(s0, iters)
  loop = fw._new_label("same_initiator_loop")
  done = fw._new_label("same_initiator_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  if mode in (MODE_WRITE, MODE_WR_READ):
    fw.noc_write(noc, 0, s2, s2, 0, s9, s4, posted=False, a=t3, v=t4)
    fw.addi(s10, s10, 1)
  if mode in (MODE_READ, MODE_WR_READ, MODE_READ_WR):
    fw.noc_read(noc, 1, s2, 0, s8, s3, s4, ret_coord=s5, a=t3, v=t4)
    fw.addi(s11, s11, 1)
  if mode == MODE_READ_WR:
    fw.noc_write(noc, 0, s2, s2, 0, s9, s4, posted=False, a=t3, v=t4)
    fw.addi(s10, s10, 1)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  if do_write:
    fw.noc_write_barrier(noc, s10, addr=t3, val=t4)
  if do_read:
    fw.noc_reads_flushed(noc, s11, addr=t3, val=t4)
  harness.read_wall_clock(fw, a4, a5)
  emit_counter_read(fw, noc, NOC.NIU_MST_WR_ACK_RECEIVED, t0)
  emit_counter_read(fw, noc, NOC.NIU_MST_RD_RESP_RECEIVED, t1)
  fw.li(s2, READ_SINK)
  fw.lw(s1, s2, 0)

  fw.li(s2, RESULT_BASE)
  for off, reg in enumerate((a2, a3, a4, a5, s6, t0, s7, t1, s1), start=8):
    fw.sw(reg, s2, off * 4)
  fw.li(t0, STATUS_DONE)
  fw.sw(t0, s2, 1 * 4)
  return fw.ret()


class SameInitiatorProgram:
  def __init__(self, *, noc: int, mode: str, packet_bytes: int, iters: int,
               source: Core, read_target: Core, write_target: Core):
    self.noc = noc
    self.mode = mode
    self.packet_bytes = packet_bytes
    self.iters = iters
    self.source = source
    self.read_target = read_target
    self.write_target = write_target
    self.name = f"riscv_noc_same_initiator_active:noc{noc}:{mode}:{source}"

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    empty = KernelBase()
    kernel = build_kernel(noc=self.noc, mode=self.mode, packet_bytes=self.packet_bytes, iters=self.iters)
    kernel.rta(lambda _x, _y: [noc_xy(*self.read_target), noc_xy(*self.write_target)])
    source_prog = Program(
      brisc=kernel,
      ncrisc=empty,
      trisc0=empty,
      trisc1=empty,
      trisc2=empty,
      num_cores=1,
    ).layout(core_xy=self.source, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id)
    target_cores = [self.source]
    passive_segments = {}
    for core in sorted({self.read_target, self.write_target} - {self.source}):
      passive_segments[core] = Program(
        brisc=KernelBase().ret(),
        ncrisc=empty,
        trisc0=empty,
        trisc1=empty,
        trisc2=empty,
        num_cores=1,
      ).layout(core_xy=core, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id)
      target_cores.append(core)

    reset_blob = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_RESET_READ_PTR_FROM_HOST)
    commands = [
      UnicastWrite(target_cores, TensixL1.GO_MSG, [reset_blob] * len(target_cores)),
      UnicastWrite(target_cores, TensixL1.GO_MSG_INDEX, [b"\0\0\0\0"] * len(target_cores)),
    ]
    for segment in source_prog:
      commands.append(UnicastWrite([self.source], segment.addr, [segment.data]))
    for core, segments in passive_segments.items():
      for segment in segments:
        commands.append(UnicastWrite([core], segment.addr, [segment.data]))
    commands.append(Run(target_cores))
    return commands


def seed(device: Device, source: Core, read_target: Core, write_target: Core, packet_bytes: int):
  payload = bytearray(NOC.MAX_BURST_SIZE * 2)
  for off in range(0, len(payload), 4):
    struct.pack_into("<I", payload, off, 0xA5000000 | off)
  with harness.device_window(device, source) as win:
    for core in sorted({source, read_target, write_target}):
      win.target(core)
      win.write(RESULT_BASE, b"\0" * RESULT_SIZE)
      win.write(STREAM_BASE, bytes(payload[:NOC.MAX_BURST_SIZE]))
      win.write(READ_SINK, b"\0" * NOC.MAX_BURST_SIZE)
    win.target(write_target)
    win.write(STREAM_BASE, b"\0" * max(packet_bytes, 4))


def u64(lo: int, hi: int) -> int:
  return lo | (hi << 32)


def read_result(device: Device, *, source: Core, read_target: Core, write_target: Core,
                noc: int, mode: str, packet_bytes: int, iters: int) -> Result:
  with harness.device_window(device, source) as win:
    win.target(source)
    blob = win.read(RESULT_BASE, RESULT_SIZE)
    win.target(write_target)
    write_seen = struct.unpack("<I", win.read(STREAM_BASE, 4))[0]
  words = struct.unpack_from("<" + "I" * RESULT_WORDS, blob, 0)
  if words[0] != RESULT_MAGIC:
    raise RuntimeError(f"{source}: bad result magic 0x{words[0]:08x}")
  if words[1] != STATUS_DONE:
    raise RuntimeError(f"{source}: benchmark did not finish, status=0x{words[1]:08x}")
  if words[2] != noc or words[3] != MODES.index(mode) or words[4] != packet_bytes or words[5] != iters:
    raise RuntimeError(f"{source}: result header mismatch {words[:6]}")
  return Result(
    noc=noc,
    mode=mode,
    source=source,
    read_target=read_target,
    write_target=write_target,
    packet_bytes=packet_bytes,
    iters=iters,
    cycles=(u64(words[10], words[11]) - u64(words[8], words[9])) & ((1 << 64) - 1),
    wr_delta=(words[13] - words[12]) & 0xFFFFFFFF,
    rd_delta=(words[15] - words[14]) & 0xFFFFFFFF,
    sink=words[16],
    write_seen=write_seen,
  )


def format_results(results: list[Result]) -> str:
  lines = [
    "| noc | mode | source | read target | write target | bytes | iters | cycles | agg B/cyc | wr delta | rd delta | read sink | write seen |",
    "|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
  ]
  for r in results:
    lines.append(
      f"| {r.noc} | {r.mode} | `{r.source[0]},{r.source[1]}` | "
      f"`{r.read_target[0]},{r.read_target[1]}` | `{r.write_target[0]},{r.write_target[1]}` | "
      f"{r.packet_bytes} | {r.iters} | {r.cycles} | {r.bytes_per_cycle:.3f} | "
      f"{r.wr_delta} | {r.rd_delta} | 0x{r.sink:08x} | 0x{r.write_seen:08x} |"
    )
  return "\n".join(lines)


def append_report(path: Path, *, results: list[Result]):
  harness.append_report(path, "NoC same-initiator active commands", [
    "Traffic: one BRISC issues read and/or write commands on one NoC, using write slot 0 and read slot 1.",
    "The mixed modes issue both commands back-to-back inside the loop and wait for read responses/write acks only after the loop.",
    "Purpose: distinguish multiple active NoC transactions from the earlier BRISC+NCRISC same-core timeout.",
  ], format_results(results))


def main():
  parser = argparse.ArgumentParser(description="Probe same-initiator active NoC read/write commands from one BRISC.")
  parser.add_argument("--nocs", type=lambda s: tuple(int(p) for p in s.split(",") if p.strip()), default=(0, 1))
  parser.add_argument("--modes", type=parse_modes, default=parse_modes("read,write,wr-read,read-wr"))
  parser.add_argument("--source", type=parse_core, default=(1, 2))
  parser.add_argument("--read-target", type=parse_core, default=(2, 2))
  parser.add_argument("--write-target", type=parse_core, default=(1, 3))
  parser.add_argument("--bytes", type=int, default=NOC.MAX_BURST_SIZE)
  parser.add_argument("--iters", type=int, default=64)
  parser.add_argument("--no-report", action="store_true")
  parser.add_argument("--report", type=Path, default=harness.doc_path("noc", "noc-same-initiator-active.md"))
  args = parser.parse_args()
  if any(noc not in (0, 1) for noc in args.nocs):
    raise ValueError("--nocs must contain only 0 and/or 1")
  if args.bytes <= 0 or args.bytes > NOC.MAX_BURST_SIZE or args.bytes % 4:
    raise ValueError(f"--bytes must be a 4-byte multiple in [4, {NOC.MAX_BURST_SIZE}]")
  if args.iters <= 0:
    raise ValueError("--iters must be positive")

  results = []
  with harness.open_device() as device:
    available = set(device.cores)
    for core in (args.source, args.read_target, args.write_target):
      if core not in available:
        raise ValueError(f"core {core[0]},{core[1]} is not available")
    for noc in args.nocs:
      for mode in args.modes:
        seed(device, args.source, args.read_target, args.write_target, args.bytes)
        device.run(SameInitiatorProgram(
          noc=noc,
          mode=mode,
          packet_bytes=args.bytes,
          iters=args.iters,
          source=args.source,
          read_target=args.read_target,
          write_target=args.write_target,
        ))
        results.append(read_result(
          device,
          source=args.source,
          read_target=args.read_target,
          write_target=args.write_target,
          noc=noc,
          mode=mode,
          packet_bytes=args.bytes,
          iters=args.iters,
        ))

  table = format_results(results)
  print(table)
  if not args.no_report:
    append_report(args.report, results=results)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
