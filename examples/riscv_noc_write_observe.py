#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import struct
import sys
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
  sys.path.insert(0, str(Path(__file__).resolve().parent))

import riscv_core_bench as corebench
from asm import KernelBase
from device import Device
from dsl import a2, a3, a4, a5, s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, t0, t1, t3, t4, zero
from pcie import TLBWindow
from program import Program
from ttk.addrs import Core, noc_xy
from ttk.mailbox import BriscMailbox as BM
from ttk.noc import NOC, Noc
from ttk.tensix import TensixL1


RESULT_BASE = 0x150000
STREAM_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
HEADER_WORDS = 16
ROLE_SENDER = 1
ROLE_RECEIVER = 2
RESULT_MAGIC = 0x524F4257  # "ROBW"
STATUS_STARTED = 0x0B000001
STATUS_DONE = 0x0B00D00D


class ObserveKernel(KernelBase, Noc):
  pass


def result_size() -> int:
  return HEADER_WORDS * 4


def expected_sentinel(stream_bytes: int) -> int:
  return 0xA5000000 | ((stream_bytes - 4) % NOC.MAX_BURST_SIZE)


def emit_header(fw: KernelBase, *, role: int, status: int, noc: int, stream_bytes: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, role, status, noc, stream_bytes, NOC.MAX_BURST_SIZE,
    STREAM_BASE, expected_sentinel(stream_bytes),
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off in range(8, HEADER_WORDS):
    fw.sw(zero, s2, off * 4)
  return fw


def emit_status(fw: KernelBase, status: int):
  fw.li(s2, RESULT_BASE)
  fw.li(t0, status)
  fw.sw(t0, s2, 2 * 4)
  return fw


def emit_counter_read(fw: KernelBase, noc: int, counter: int, out, *, addr=t3):
  fw.li(addr, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  return fw.lw(out, addr, 0)


def build_sender(noc: int, stream_bytes: int) -> KernelBase:
  chunks = stream_bytes // NOC.MAX_BURST_SIZE
  fw = ObserveKernel()
  emit_header(fw, role=ROLE_SENDER, status=STATUS_STARTED, noc=noc, stream_bytes=stream_bytes)
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s9,))
  fw.local_noc0_coord(s5, x_addr=BM.MY_X, y_addr=BM.MY_Y)
  fw.li(s2, STREAM_BASE)
  fw.li(s3, STREAM_BASE)
  fw.li(s4, NOC.MAX_BURST_SIZE)
  fw.li(s8, NOC.MAX_BURST_SIZE)
  emit_counter_read(fw, noc, NOC.NIU_MST_WR_ACK_RECEIVED, s7)
  fw.mv(s6, s7)

  corebench.read_wall_clock(fw, a2, a3)
  fw.li(s0, chunks)
  loop = fw._new_label("sender_write_loop")
  done = fw._new_label("sender_write_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  fw.noc_write(noc, 0, s2, s3, 0, s9, s4, posted=False, a=t3, v=t4)
  fw.addi(s6, s6, 1)
  fw.add(s2, s2, s8)
  fw.add(s3, s3, s8)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  fw.noc_write_barrier(noc, s6, addr=t3, val=t4)
  corebench.read_wall_clock(fw, a4, a5)
  emit_counter_read(fw, noc, NOC.NIU_MST_WR_ACK_RECEIVED, s8)

  fw.li(s2, RESULT_BASE)
  for off, reg in enumerate((a2, a3, a4, a5, s7, s8), start=8):
    fw.sw(reg, s2, off * 4)
  emit_status(fw, STATUS_DONE)
  return fw.ret()


def build_receiver(noc: int, stream_bytes: int) -> KernelBase:
  fw = ObserveKernel()
  emit_header(fw, role=ROLE_RECEIVER, status=STATUS_STARTED, noc=noc, stream_bytes=stream_bytes)
  fw.li(s1, expected_sentinel(stream_bytes))
  fw.li(s2, STREAM_BASE + stream_bytes - 4)
  fw.mv(s0, zero)
  loop = fw._new_label("receiver_poll")
  done = fw._new_label("receiver_done")
  fw.label(loop)
  fw.lw(t1, s2, 0)
  fw.beq(t1, s1, done)
  fw.addi(s0, s0, 1)
  fw.j(loop)
  fw.label(done)
  corebench.read_wall_clock(fw, a2, a3)
  fw.li(s2, RESULT_BASE)
  fw.sw(a2, s2, 8 * 4)
  fw.sw(a3, s2, 9 * 4)
  fw.sw(s0, s2, 10 * 4)
  fw.sw(t1, s2, 11 * 4)
  emit_status(fw, STATUS_DONE)
  return fw.ret()


def build_program(noc: int, stream_bytes: int, source: Core, target: Core) -> Program:
  if source[1] != target[1] or source[0] >= target[0]:
    raise ValueError("initial observed-completion probe needs same-row source left of target")
  empty = KernelBase()
  sender = build_sender(noc, stream_bytes)
  sender.rta(lambda _x, _y: [noc_xy(*target)])
  program = Program(
    brisc=sender,
    brisc_recv=build_receiver(noc, stream_bytes),
    ncrisc=empty,
    trisc0=empty,
    trisc1=empty,
    trisc2=empty,
    grid=((source[1],), (source[0], target[0])),
  )
  program.name = f"riscv_noc_write_observe:noc{noc}"
  return program


def clear_and_seed(device: Device, source: Core, target: Core, stream_bytes: int):
  seed = bytearray(NOC.MAX_BURST_SIZE)
  for off in range(0, len(seed), 4):
    struct.pack_into("<I", seed, off, 0xA5000000 | off)
  stream_seed = bytes(seed) * (stream_bytes // NOC.MAX_BURST_SIZE)
  device.dev.set_power_state(True)
  try:
    with TLBWindow(device.dev, start=source) as win:
      win.target(source)
      win.write(RESULT_BASE, b"\0" * result_size())
      win.write(STREAM_BASE, stream_seed)
      win.target(target)
      win.write(RESULT_BASE, b"\0" * result_size())
      win.write(STREAM_BASE, b"\0" * stream_bytes)
  finally:
    device.dev.set_power_state(False)


def read_result(device: Device, core: Core) -> tuple[int, ...]:
  device.dev.set_power_state(True)
  try:
    with TLBWindow(device.dev, start=core) as win:
      blob = win.read(RESULT_BASE, result_size())
  finally:
    device.dev.set_power_state(False)
  words = struct.unpack_from("<" + "I" * HEADER_WORDS, blob, 0)
  if words[0] != RESULT_MAGIC:
    raise RuntimeError(f"{core}: bad result magic 0x{words[0]:08x}")
  if words[2] != STATUS_DONE:
    raise RuntimeError(f"{core}: benchmark did not finish, status=0x{words[2]:08x}")
  return words


def u64(lo: int, hi: int) -> int:
  return lo | (hi << 32)


def main():
  parser = argparse.ArgumentParser(description="Compare source NoC write ack time with receiver-observed sentinel time.")
  parser.add_argument("--noc", type=int, choices=(0, 1), default=0)
  parser.add_argument("--source", type=corebench.parse_core, default=(1, 2))
  parser.add_argument("--target", type=corebench.parse_core, default=(2, 2))
  parser.add_argument("--bytes", type=int, default=1024 * 1024, help="payload bytes; multiple of 16 KiB")
  args = parser.parse_args()
  if args.bytes <= 0 or args.bytes % NOC.MAX_BURST_SIZE:
    raise ValueError("--bytes must be a positive multiple of 16 KiB")
  if args.bytes > RESULT_BASE - STREAM_BASE:
    raise ValueError(f"--bytes must fit below result range; max is {RESULT_BASE - STREAM_BASE}")

  os.environ.setdefault("TT_USB", "1")
  device = Device()
  try:
    if args.source not in set(device.cores) or args.target not in set(device.cores):
      raise ValueError("source and target must be program cores")
    clear_and_seed(device, args.source, args.target, args.bytes)
    device.run(build_program(args.noc, args.bytes, args.source, args.target))
    sender = read_result(device, args.source)
    receiver = read_result(device, args.target)
  finally:
    device.close()

  start = u64(sender[8], sender[9])
  ack = u64(sender[10], sender[11])
  observed = u64(receiver[8], receiver[9])
  counter_delta = (sender[13] - sender[12]) & 0xFFFFFFFF
  print(f"source: `{args.source[0]},{args.source[1]}` target: `{args.target[0]},{args.target[1]}` noc{args.noc}")
  print(f"bytes: {args.bytes} chunks: {args.bytes // NOC.MAX_BURST_SIZE}")
  print(f"sender start: {start}")
  print(f"sender write ack/barrier: {ack} delta_from_start={ack - start}")
  print(f"receiver observed sentinel: {observed} delta_from_start={observed - start}")
  print(f"observed_minus_ack: {observed - ack}")
  print(f"write ack counter delta: {counter_delta}")
  print(f"receiver poll iterations: {receiver[10]}")
  print(f"receiver sentinel: 0x{receiver[11]:08x}")


if __name__ == "__main__":
  main()
