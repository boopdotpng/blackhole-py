#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
  sys.path.insert(0, str(Path(__file__).resolve().parent))

import riscv_core_bench as corebench
import riscv_noc_aggregate as agg
import riscv_noc_write_observe as observe
from asm import KernelBase
from device import Device
from dsl import a0, a1, a2, a3, a4, a5, s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, t0, t1, t3, t4, zero
from pcie import TLBWindow
from program import DevMsgs, Program, Run, UnicastWrite
from ttk.addrs import Core, noc_xy
from ttk.mailbox import BriscMailbox as BM
from ttk.noc import NOC, Noc
from ttk.tensix import TensixL1


RESULT_BASE = observe.RESULT_BASE
STREAM0_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
HEADER_WORDS = 16
RESULT_MAGIC = 0x5244414E  # "RDAN"
STATUS_STARTED = 0xDA000001
STATUS_DONE = 0xDA00D00D


class DualKernel(KernelBase, Noc):
  pass


def stream1_base(stream_bytes: int) -> int:
  return STREAM0_BASE + stream_bytes


def expected_sentinel(stream_bytes: int) -> int:
  return 0xA5000000 | ((stream_bytes - 4) % NOC.MAX_BURST_SIZE)


def result_size() -> int:
  return HEADER_WORDS * 4


def emit_header(fw: KernelBase, *, role: int, status: int, stream_bytes: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, role, status, stream_bytes, NOC.MAX_BURST_SIZE,
    STREAM0_BASE, stream1_base(stream_bytes), expected_sentinel(stream_bytes),
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off in range(8, HEADER_WORDS):
    fw.sw(zero, s2, off * 4)
  return fw


def emit_status(fw: KernelBase, status: int):
  fw.li(s2, RESULT_BASE)
  fw.li(t0, status)
  return fw.sw(t0, s2, 2 * 4)


def emit_counter_read(fw: KernelBase, noc: int, counter: int, out, *, addr=t3):
  fw.li(addr, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  return fw.lw(out, addr, 0)


def build_sender(stream_bytes: int) -> KernelBase:
  chunks = stream_bytes // NOC.MAX_BURST_SIZE
  fw = DualKernel()
  emit_header(fw, role=observe.ROLE_SENDER, status=STATUS_STARTED, stream_bytes=stream_bytes)
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s9,))
  fw.li(s4, NOC.MAX_BURST_SIZE)
  fw.li(s5, NOC.MAX_BURST_SIZE)
  emit_counter_read(fw, 0, NOC.NIU_MST_WR_ACK_RECEIVED, s6)
  emit_counter_read(fw, 1, NOC.NIU_MST_WR_ACK_RECEIVED, s7)

  corebench.read_wall_clock(fw, a2, a3)
  fw.li(s0, chunks)
  fw.li(s2, STREAM0_BASE)
  fw.li(s3, STREAM0_BASE)
  fw.li(a0, stream1_base(stream_bytes))
  fw.li(a1, stream1_base(stream_bytes))
  loop = fw._new_label("dual_send_loop")
  done = fw._new_label("dual_send_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  fw.noc_write(0, 0, s2, s3, 0, s9, s4, posted=False, a=t3, v=t4)
  fw.addi(s6, s6, 1)
  fw.noc_write(1, 0, a0, a1, 0, s9, s4, posted=False, a=t3, v=t4)
  fw.addi(s7, s7, 1)
  fw.add(s2, s2, s5)
  fw.add(s3, s3, s5)
  fw.add(a0, a0, s5)
  fw.add(a1, a1, s5)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  fw.noc_write_barrier(0, s6, addr=t3, val=t4)
  fw.noc_write_barrier(1, s7, addr=t3, val=t4)
  corebench.read_wall_clock(fw, a4, a5)
  emit_counter_read(fw, 0, NOC.NIU_MST_WR_ACK_RECEIVED, s8)
  emit_counter_read(fw, 1, NOC.NIU_MST_WR_ACK_RECEIVED, s9)

  fw.li(s2, RESULT_BASE)
  for off, reg in enumerate((a2, a3, a4, a5, s6, s8, s7, s9), start=8):
    fw.sw(reg, s2, off * 4)
  emit_status(fw, STATUS_DONE)
  return fw.ret()


def build_receiver(stream_bytes: int) -> KernelBase:
  fw = DualKernel()
  emit_header(fw, role=observe.ROLE_RECEIVER, status=STATUS_STARTED, stream_bytes=stream_bytes)
  fw.li(s1, expected_sentinel(stream_bytes))
  fw.li(s2, STREAM0_BASE + stream_bytes - 4)
  fw.li(s3, stream1_base(stream_bytes) + stream_bytes - 4)
  fw.mv(s0, zero)
  loop = fw._new_label("dual_recv_poll")
  done = fw._new_label("dual_recv_done")
  fw.label(loop)
  fw.lw(t0, s2, 0)
  fw.lw(t1, s3, 0)
  fw.bne(t0, s1, loop)
  fw.bne(t1, s1, loop)
  fw.label(done)
  corebench.read_wall_clock(fw, a2, a3)
  fw.li(s2, RESULT_BASE)
  fw.sw(a2, s2, 8 * 4)
  fw.sw(a3, s2, 9 * 4)
  fw.sw(s0, s2, 10 * 4)
  fw.sw(t0, s2, 11 * 4)
  fw.sw(t1, s2, 12 * 4)
  emit_status(fw, STATUS_DONE)
  return fw.ret()


class DualAggregateProgram:
  def __init__(self, pairs: list[agg.Pair], *, stream_bytes: int):
    self.pairs = list(pairs)
    self.stream_bytes = stream_bytes
    self.name = f"riscv_noc_dual_aggregate:pairs{len(pairs)}"

  def _segments(self, core: Core, kernel: KernelBase, *, dispatch_mode: int, host_assigned_id: int):
    empty = KernelBase()
    return Program(
      brisc=kernel,
      ncrisc=empty,
      trisc0=empty,
      trisc1=empty,
      trisc2=empty,
      num_cores=1,
    ).layout(core_xy=core, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id)

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    per_core_segments = {}
    target_cores = []
    for pair in self.pairs:
      sender = build_sender(self.stream_bytes)
      sender.rta(lambda _x, _y, target=pair.target: [noc_xy(*target)])
      per_core_segments[pair.source] = self._segments(pair.source, sender, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id)
      per_core_segments[pair.target] = self._segments(pair.target, build_receiver(self.stream_bytes), dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id)
      target_cores.extend((pair.source, pair.target))

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


def clear_and_seed(device: Device, pairs: list[agg.Pair], stream_bytes: int):
  seed = bytearray(NOC.MAX_BURST_SIZE)
  for off in range(0, len(seed), 4):
    struct.pack_into("<I", seed, off, 0xA5000000 | off)
  stream_seed = bytes(seed) * (stream_bytes // NOC.MAX_BURST_SIZE)
  zeroes = b"\0" * (2 * stream_bytes)
  device.dev.set_power_state(True)
  try:
    with TLBWindow(device.dev, start=pairs[0].source) as win:
      for pair in pairs:
        win.target(pair.source)
        win.write(RESULT_BASE, b"\0" * result_size())
        win.write(STREAM0_BASE, stream_seed + stream_seed)
        win.target(pair.target)
        win.write(RESULT_BASE, b"\0" * result_size())
        win.write(STREAM0_BASE, zeroes)
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


def summarize(stream_bytes: int, pairs: list[agg.Pair], senders: list[tuple[int, ...]], receivers: list[tuple[int, ...]]) -> str:
  starts = [observe.u64(words[8], words[9]) for words in senders]
  acks = [observe.u64(words[10], words[11]) for words in senders]
  observed = [observe.u64(words[8], words[9]) for words in receivers]
  total_bytes = len(pairs) * stream_bytes * 2
  sender_window = max(acks) - min(starts)
  receiver_window = max(observed) - min(starts)
  bad_sentinel = sum(words[11] != expected_sentinel(stream_bytes) or words[12] != expected_sentinel(stream_bytes) for words in receivers)
  bad_ack = sum(words[13] != words[12] or words[15] != words[14] for words in senders)
  return (
    f"| dual | {len(pairs)} | {total_bytes / (1024 * 1024):.1f} | "
    f"{sender_window} | {total_bytes / sender_window:.3f} | "
    f"{receiver_window} | {total_bytes / receiver_window:.3f} | {bad_ack} | {bad_sentinel} |"
  )


def main():
  parser = argparse.ArgumentParser(description="Run simultaneous dual-NoC peer L1 write streams.")
  parser.add_argument("--bytes-per-noc", type=int, default=512 * 1024, help="payload bytes per sender per NoC; multiple of 16 KiB")
  parser.add_argument("--counts", type=agg.parse_counts, default=agg.parse_counts("1,2,4,8,16,32,60"))
  parser.add_argument("--no-report", action="store_true")
  parser.add_argument("--report", type=Path, default=Path("docs/noc-dual-aggregate.md"))
  args = parser.parse_args()
  if args.bytes_per_noc <= 0 or args.bytes_per_noc % NOC.MAX_BURST_SIZE:
    raise ValueError("--bytes-per-noc must be a positive multiple of 16 KiB")
  if 2 * args.bytes_per_noc > RESULT_BASE - STREAM0_BASE:
    raise ValueError(f"two streams must fit below result range; max per NoC is {(RESULT_BASE - STREAM0_BASE) // 2}")

  os.environ.setdefault("TT_USB", "1")
  device = Device()
  lines = [
    "| noc | pairs | total MiB | sender window cyc | sender agg B/cyc | receiver window cyc | receiver agg B/cyc | bad ack rows | bad sentinel rows |",
    "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
  ]
  try:
    all_pairs = agg.adjacent_pairs(device.cores, noc=0)
    for count in args.counts:
      if count > len(all_pairs):
        raise ValueError(f"requested {count} pairs but only {len(all_pairs)} available")
      pairs = all_pairs[:count]
      clear_and_seed(device, pairs, args.bytes_per_noc)
      device.run(DualAggregateProgram(pairs, stream_bytes=args.bytes_per_noc))
      senders = [read_result(device, pair.source) for pair in pairs]
      receivers = [read_result(device, pair.target) for pair in pairs]
      lines.append(summarize(args.bytes_per_noc, pairs, senders, receivers))
  finally:
    device.close()

  table = "\n".join(lines)
  print(table)
  if not args.no_report:
    with args.report.open("a", encoding="utf-8") as f:
      f.write("\n## Run\n\n")
      f.write(f"- Bytes per sender per NoC: `{args.bytes_per_noc}`\n")
      f.write("- Pairing: disjoint adjacent same-row sender/receiver pairs\n\n")
      f.write(table)
      f.write("\n")
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
