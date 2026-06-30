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
from dsl import (  # noqa: E402
  a0, a1, a2, a3, a4, a5, a6, a7,
  s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11,
  t0, t1, t2, t3, t4, t5, t6, zero,
)
from program import Program  # noqa: E402
from ttk.addrs import Core  # noqa: E402
from ttk.tensix import TensixL1  # noqa: E402


RESULT_BASE = 0x150000
STREAM_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
DEFAULT_BYTES = 1024 * 1024
DEFAULT_BLOCK_BYTES = 256
HEADER_WORDS = 16
RECORD_WORDS = 16
RESULT_MAGIC = 0x3142534C  # "LSB1"
RECORD_MAGIC = 0x5242534C  # "LSBR"
STATUS_STARTED = 0x51000001
STATUS_DONE = 0x5100D00D

MODES = ("read_discard", "read_accum", "write")
MODE_ID = {name: i for i, name in enumerate(MODES)}
READ_REGS = (t0, t1, t2, t3, t4, t5, t6, a0, a1, a6, a7, s7, s8, s9, s10, s11)


@dataclass(frozen=True)
class Record:
  mode: str
  bytes: int
  block_bytes: int
  start: int
  end: int
  cycles: int
  sink: int

  @property
  def bpc(self) -> float:
    return self.bytes / self.cycles if self.cycles > 0 else 0.0


def result_size() -> int:
  return HEADER_WORDS * 4 + len(MODES) * RECORD_WORDS * 4


def u64(lo: int, hi: int) -> int:
  return lo | (hi << 32)


def emit_header(fw: KernelBase, *, stream_bytes: int, block_bytes: int, status: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, len(MODES), RECORD_WORDS, status,
    stream_bytes, STREAM_BASE, RESULT_BASE, TensixL1.SIZE,
    block_bytes, 0, 0, 0, 0, 0, 0, 0,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  return fw


def emit_record(fw: KernelBase, *, mode: str, stream_bytes: int, block_bytes: int,
                start_lo, start_hi, end_lo, end_hi, sink):
  record_base = RESULT_BASE + HEADER_WORDS * 4 + MODE_ID[mode] * RECORD_WORDS * 4
  fw.li(s2, record_base)
  for off, value in enumerate((
    RECORD_MAGIC, MODE_ID[mode], stream_bytes, block_bytes,
    STREAM_BASE, 0, 0, 0,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off, reg in enumerate((start_lo, start_hi, end_lo, end_hi, sink), start=8):
    fw.sw(reg, s2, off * 4)
  fw.sw(zero, s2, 13 * 4)
  fw.sw(zero, s2, 14 * 4)
  fw.sw(zero, s2, 15 * 4)
  return fw


def emit_loop_prologue(fw: KernelBase, *, stream_bytes: int, block_bytes: int):
  fw.li(s3, STREAM_BASE)
  fw.li(s4, STREAM_BASE + stream_bytes)
  fw.li(s5, block_bytes)
  fw.fence()
  harness.read_wall_clock(fw, a2, a3)
  return fw


def emit_loop_epilogue(fw: KernelBase, *, mode: str, stream_bytes: int, block_bytes: int, sink=s6):
  fw.fence()
  harness.read_wall_clock(fw, a4, a5)
  return emit_record(
    fw, mode=mode, stream_bytes=stream_bytes, block_bytes=block_bytes,
    start_lo=a2, start_hi=a3, end_lo=a4, end_hi=a5, sink=sink,
  )


def emit_read_discard(fw: KernelBase, *, stream_bytes: int, block_bytes: int):
  emit_loop_prologue(fw, stream_bytes=stream_bytes, block_bytes=block_bytes)
  loop = fw._new_label("read_discard_loop")
  done = fw._new_label("read_discard_done")
  fw.label(loop)
  fw.beq(s3, s4, done)
  for base in range(0, block_bytes, 64):
    for i, reg in enumerate(READ_REGS):
      fw.lw(reg, s3, base + i * 4)
    fw.mv(s6, READ_REGS[-1])
  fw.add(s3, s3, s5)
  fw.j(loop)
  fw.label(done)
  return emit_loop_epilogue(fw, mode="read_discard", stream_bytes=stream_bytes, block_bytes=block_bytes)


def emit_read_accum(fw: KernelBase, *, stream_bytes: int, block_bytes: int):
  fw.mv(s6, zero)
  emit_loop_prologue(fw, stream_bytes=stream_bytes, block_bytes=block_bytes)
  loop = fw._new_label("read_accum_loop")
  done = fw._new_label("read_accum_done")
  fw.label(loop)
  fw.beq(s3, s4, done)
  for base in range(0, block_bytes, 64):
    for i, reg in enumerate(READ_REGS):
      fw.lw(reg, s3, base + i * 4)
    for reg in READ_REGS:
      fw.add(s6, s6, reg)
  fw.add(s3, s3, s5)
  fw.j(loop)
  fw.label(done)
  return emit_loop_epilogue(fw, mode="read_accum", stream_bytes=stream_bytes, block_bytes=block_bytes)


def emit_write(fw: KernelBase, *, stream_bytes: int, block_bytes: int):
  fw.li(s1, 0xA5A50001)
  emit_loop_prologue(fw, stream_bytes=stream_bytes, block_bytes=block_bytes)
  loop = fw._new_label("write_loop")
  done = fw._new_label("write_done")
  fw.label(loop)
  fw.beq(s3, s4, done)
  for off in range(0, block_bytes, 4):
    fw.sw(s1, s3, off)
  fw.addi(s1, s1, 1)
  fw.add(s3, s3, s5)
  fw.j(loop)
  fw.label(done)
  return emit_loop_epilogue(fw, mode="write", stream_bytes=stream_bytes, block_bytes=block_bytes, sink=s1)


def build_kernel(stream_bytes: int, block_bytes: int) -> KernelBase:
  fw = KernelBase()
  emit_header(fw, stream_bytes=stream_bytes, block_bytes=block_bytes, status=STATUS_STARTED)
  emit_read_discard(fw, stream_bytes=stream_bytes, block_bytes=block_bytes)
  emit_read_accum(fw, stream_bytes=stream_bytes, block_bytes=block_bytes)
  emit_write(fw, stream_bytes=stream_bytes, block_bytes=block_bytes)
  emit_header(fw, stream_bytes=stream_bytes, block_bytes=block_bytes, status=STATUS_DONE)
  return fw.ret()


def build_program(stream_bytes: int, block_bytes: int, core: Core) -> Program:
  empty = KernelBase()
  program = Program(
    brisc=build_kernel(stream_bytes, block_bytes),
    ncrisc=empty,
    trisc0=empty,
    trisc1=empty,
    trisc2=empty,
    grid=((core[1],), (core[0],)),
  )
  program.name = f"riscv_l1_stream_bandwidth:{stream_bytes}"
  return program


def seed(device: Device, core: Core, stream_bytes: int, block_bytes: int):
  seed_block = bytearray(block_bytes)
  for off in range(0, block_bytes, 4):
    struct.pack_into("<I", seed_block, off, 0x51000000 | off)
  payload = bytes(seed_block) * (stream_bytes // block_bytes)
  with harness.device_window(device, core) as win:
    win.write(RESULT_BASE, b"\0" * result_size())
    win.write(STREAM_BASE, payload)


def read_records(device: Device, core: Core) -> list[Record]:
  blob = harness.read_window(device, core, RESULT_BASE, result_size())
  words = struct.unpack_from("<" + "I" * (len(blob) // 4), blob)
  if words[0] != RESULT_MAGIC:
    raise RuntimeError(f"{core}: bad result magic 0x{words[0]:08x}")
  if words[3] != STATUS_DONE:
    raise RuntimeError(f"{core}: benchmark did not finish, status=0x{words[3]:08x}")
  records = []
  base = HEADER_WORDS
  for mode in MODES:
    off = base + MODE_ID[mode] * RECORD_WORDS
    rec = words[off:off + RECORD_WORDS]
    if rec[0] != RECORD_MAGIC:
      raise RuntimeError(f"{mode}: bad record magic 0x{rec[0]:08x}")
    records.append(Record(
      mode=mode,
      bytes=rec[2],
      block_bytes=rec[3],
      start=u64(rec[8], rec[9]),
      end=u64(rec[10], rec[11]),
      cycles=(u64(rec[10], rec[11]) - u64(rec[8], rec[9])) & ((1 << 64) - 1),
      sink=rec[12],
    ))
  return records


def format_table(core: Core, records: list[Record]) -> str:
  lines = [
    "| core | mode | bytes | block B | cycles | B/cyc | sink |",
    "|---|---|---:|---:|---:|---:|---:|",
  ]
  for record in records:
    lines.append(
      f"| `{core[0]},{core[1]}` | {record.mode} | {record.bytes} | {record.block_bytes} | "
      f"{record.cycles} | {record.bpc:.3f} | 0x{record.sink:08x} |"
    )
  return "\n".join(lines)


def main() -> None:
  parser = argparse.ArgumentParser(description="Measure sustained BRISC local L1 read/write sweep bandwidth.")
  parser.add_argument("--core", type=harness.parse_core, default=None, help="logical Tensix core X,Y; default: first program core")
  parser.add_argument("--bytes", type=int, default=DEFAULT_BYTES, help="working-set bytes; multiple of block size")
  parser.add_argument("--block-bytes", type=int, default=DEFAULT_BLOCK_BYTES, help="loop unroll size; multiple of 64 B, max 1024 B")
  parser.add_argument("--no-report", action="store_true")
  parser.add_argument("--report", type=Path, default=harness.doc_path("riscv", "riscv-l1-stream-bandwidth.md"))
  args = parser.parse_args()

  if args.block_bytes <= 0 or args.block_bytes % 64:
    raise ValueError("--block-bytes must be a positive multiple of 64")
  if args.block_bytes > 1024:
    raise ValueError("--block-bytes must be <= 1024 so generated loop branches stay in range")
  if args.bytes <= 0 or args.bytes % args.block_bytes:
    raise ValueError("--bytes must be a positive multiple of --block-bytes")
  if STREAM_BASE + args.bytes > RESULT_BASE:
    raise ValueError(f"--bytes overlaps result area; max is {RESULT_BASE - STREAM_BASE}")

  with harness.open_device() as device:
    core = args.core or device.cores[0]
    if core not in set(device.cores):
      raise ValueError(f"core {core[0]},{core[1]} is not a program core")
    seed(device, core, args.bytes, args.block_bytes)
    device.run(build_program(args.bytes, args.block_bytes, core))
    records = read_records(device, core)

  table = format_table(core, records)
  print(table)
  if not args.no_report:
    harness.append_report(args.report, "RISC-V local L1 stream bandwidth", [
      f"Core: `{core[0]},{core[1]}`",
      f"Bytes: `{args.bytes}`",
      f"Block bytes: `{args.block_bytes}`",
      "Traffic: BRISC local L1 loads/stores only; no NoC traffic in timed loops",
    ], table)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
