#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
from asm import KernelBase
from device import Device
from dsl import a2, a3, a4, a5, s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, t0, t1, t2, t3, t4, t5, zero
from program import DevMsgs, Dtype, Program, Run, UnicastWrite
from ttk.addrs import Core, noc_xy
from ttk.mailbox import BriscMailbox as BM
from ttk.noc import NOC, Noc, NocCfg
from ttk.tensix import TensixL1


RESULT_BASE = 0x150000
RESULT_WORDS = 16
RESULT_SIZE = RESULT_WORDS * 4
RESULT_MAGIC = 0x5741524E  # "NRAW"
STATUS_STARTED = 0x72000001
STATUS_DONE = 0x7200D00D
STATUS_TIMEOUT = 0x7200EEEE

SRC_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
DST_BASE = SRC_BASE + 0x4000
PACKET_BYTES = 64
TRANSLATE_EN = 1 << 14

MODE_L1_WRITE = 1
MODE_DRAM_READ = 2
MODE_L1_ROUNDTRIP = 3
MODE_NAMES = {
  MODE_L1_WRITE: "l1-write",
  MODE_DRAM_READ: "dram-read",
  MODE_L1_ROUNDTRIP: "l1-roundtrip",
}


class RawCoordKernel(KernelBase, Noc):
  pass


@dataclass(frozen=True)
class ProbeResult:
  mode: int
  noc: int
  source: Core
  target: Core
  raw_source: Core
  raw_target: Core
  orig_cfg: int
  raw_cfg: int
  restored_cfg: int
  sink: int
  target_sink: int | None
  counter_before: int
  counter_after: int
  status: int


def mode_id(name: str) -> int:
  for mode, mode_name in MODE_NAMES.items():
    if name == mode_name:
      return mode
  raise ValueError(name)


def raw_coord_for_noc(coord: Core, noc: int) -> Core:
  if noc == 0:
    return coord
  # Raw NoC1's physical origin is the opposite corner of the 17x12 torus.
  return (16 - coord[0], 11 - coord[1])


def emit_counter_read(fw: KernelBase, noc: int, counter: int, out, *, addr=t3):
  fw.li(addr, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  return fw.lw(out, addr, 0)


def build_kernel(*, mode: int, noc: int, packet_bytes: int) -> KernelBase:
  if mode not in MODE_NAMES:
    raise ValueError(f"unknown mode {mode}")
  fw = RawCoordKernel()
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s10))
  # RTA: raw target coord, raw source coord, remote low address.

  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((RESULT_MAGIC, STATUS_STARTED, mode, noc, packet_bytes, SRC_BASE, DST_BASE, 0)):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off in range(8, RESULT_WORDS):
    fw.sw(zero, s2, off * 4)

  cfg_addr = NOC.CFG_BASE + NocCfg.NIU_CFG_0 * 4 + (noc << NOC.INSTANCE_OFFSET_BIT)
  fw.li(s3, cfg_addr)
  fw.lw(s4, s3, 0)
  fw.li(t0, ~TRANSLATE_EN & 0xFFFFFFFF)
  fw.and_(s5, s4, t0)
  fw.sw(s5, s3, 0)
  fw.fence()
  fw.lw(s6, s3, 0)

  if mode in (MODE_L1_WRITE, MODE_L1_ROUNDTRIP):
    emit_counter_read(fw, noc, NOC.NIU_MST_POSTED_WR_REQ_SENT, s7)
    fw.li(a2, SRC_BASE)
    fw.mv(a3, s10)
    fw.li(a4, packet_bytes)
    fw.noc_write(noc, 0, a2, a3, 0, s0, a4, posted=True, a=t3, v=t4)
    fw.addi(s8, s7, 1)
    fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_POSTED_WR_REQ_SENT + (noc << NOC.INSTANCE_OFFSET_BIT))
    wait_posted = fw._new_label("wait_posted")
    fw.label(wait_posted)
    fw.lw(t1, t0, 0)
    fw.bltu(t1, s8, wait_posted)
    fw.li(t2, 4096)
    delay = fw._new_label("raw_l1_delay")
    fw.label(delay)
    fw.addi(t2, t2, -1)
    fw.bne(t2, zero, delay)
    fw.mv(s9, t1)
    if mode == MODE_L1_ROUNDTRIP:
      emit_counter_read(fw, noc, NOC.NIU_MST_RD_RESP_RECEIVED, s7)
      fw.li(a2, DST_BASE)
      fw.noc_read(noc, 1, s10, 0, s0, a2, a4, ret_coord=s1, a=t3, v=t4)
      fw.addi(s8, s7, 1)
      fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED + (noc << NOC.INSTANCE_OFFSET_BIT))
      fw.li(t2, 2000000)
      wait_read = fw._new_label("wait_read")
      read_done = fw._new_label("read_done")
      read_timeout = fw._new_label("read_timeout")
      fw.label(wait_read)
      fw.lw(t1, t0, 0)
      fw.bgeu(t1, s8, read_done)
      fw.addi(t2, t2, -1)
      fw.beq(t2, zero, read_timeout)
      fw.j(wait_read)
      fw.label(read_done)
      fw.mv(s9, t1)
      fw.li(t5, DST_BASE)
      fw.lw(a5, t5, 0)
      fw.li(t2, STATUS_DONE)
      fw.j("raw_coord_restore")
      fw.label(read_timeout)
      fw.mv(s9, t1)
      fw.li(t5, DST_BASE)
      fw.lw(a5, t5, 0)
      fw.li(t2, STATUS_TIMEOUT)
    else:
      fw.li(t5, SRC_BASE)
      fw.lw(a5, t5, 0)
      fw.li(t2, STATUS_DONE)
  else:
    emit_counter_read(fw, noc, NOC.NIU_MST_RD_RESP_RECEIVED, s7)
    fw.mv(a2, s10)
    fw.li(a3, packet_bytes)
    fw.li(a4, DST_BASE)
    fw.noc_read(noc, 1, a2, 0, s0, a4, a3, ret_coord=s1, a=t3, v=t4)
    fw.addi(s8, s7, 1)
    fw.noc_reads_flushed(noc, s8, addr=t3, val=t4)
    emit_counter_read(fw, noc, NOC.NIU_MST_RD_RESP_RECEIVED, s9)
    fw.li(t5, DST_BASE)
    fw.lw(a5, t5, 0)
    fw.li(t2, STATUS_DONE)

  fw.label("raw_coord_restore")
  fw.sw(s4, s3, 0)
  fw.fence()
  fw.lw(t0, s3, 0)

  fw.li(s2, RESULT_BASE)
  for off, reg in enumerate((s4, s6, t0, a5, s7, s9, s0, s1), start=8):
    fw.sw(reg, s2, off * 4)
  fw.sw(t2, s2, 1 * 4)
  return fw.ret()


class RawCoordProgram:
  def __init__(self, *, mode: int, noc: int, source: Core, raw_source: Core, raw_target: Core,
               remote_lo: int = SRC_BASE):
    self.mode = mode
    self.noc = noc
    self.source = source
    self.raw_source = raw_source
    self.raw_target = raw_target
    self.remote_lo = remote_lo
    self.name = f"riscv_noc_raw_coords_probe:{MODE_NAMES[mode]}:noc{noc}:{source}->{raw_target}"

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    empty = KernelBase()
    bench = build_kernel(mode=self.mode, noc=self.noc, packet_bytes=PACKET_BYTES)
    bench.rta(lambda _x, _y: [noc_xy(*self.raw_target), noc_xy(*self.raw_source), self.remote_lo])
    sender = Program(
      brisc=bench,
      ncrisc=empty,
      trisc0=empty,
      trisc1=empty,
      trisc2=empty,
      num_cores=1,
    ).layout(core_xy=self.source, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id)
    reset_blob = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_RESET_READ_PTR_FROM_HOST)
    commands = [
      UnicastWrite([self.source], TensixL1.GO_MSG, [reset_blob]),
      UnicastWrite([self.source], TensixL1.GO_MSG_INDEX, [b"\0\0\0\0"]),
    ]
    for segment in sender:
      commands.append(UnicastWrite([self.source], segment.addr, [segment.data]))
    commands.append(Run([self.source]))
    return commands


def seed_l1(device: Device, source: Core, target: Core | None):
  payload = bytearray(PACKET_BYTES)
  for off in range(0, PACKET_BYTES, 4):
    struct.pack_into("<I", payload, off, 0xA5000000 | off)
  with harness.device_window(device, source) as win:
    for core in (source, *( [target] if target is not None else [] )):
      win.target(core)
      win.write(RESULT_BASE, b"\0" * RESULT_SIZE)
      win.write(SRC_BASE, payload)
      win.write(DST_BASE, b"\0" * PACKET_BYTES)


def seed_dram(device: Device, bank: int) -> tuple[int, Core]:
  buf = device.dram.alloc(1, Dtype.Float16_b, name="raw_coord_probe")
  payload = bytearray(Dtype.Float16_b.tile_size)
  for off in range(0, len(payload), 4):
    struct.pack_into("<I", payload, off, 0xD5000000 | off)
  device.dram.write(buf, payload)
  _, x, y = device.dram.bank_tiles[bank]
  return buf.addr, (x, y)


def read_result(device: Device, source: Core, target: Core | None, *, mode: int, noc: int,
                raw_source: Core, raw_target: Core) -> ProbeResult:
  with harness.device_window(device, source) as win:
    blob = win.read(RESULT_BASE, RESULT_SIZE)
  words = struct.unpack_from("<" + "I" * RESULT_WORDS, blob, 0)
  if words[0] != RESULT_MAGIC:
    raise RuntimeError(f"{source}: bad magic 0x{words[0]:08x}")
  if words[1] not in (STATUS_DONE, STATUS_TIMEOUT):
    raise RuntimeError(f"{source}: did not finish, status=0x{words[1]:08x}")
  target_sink = None
  if target is not None:
    with harness.device_window(device, target) as win:
      target_sink = struct.unpack("<I", win.read(DST_BASE, 4))[0]
  return ProbeResult(
    mode=mode,
    noc=noc,
    source=source,
    target=target or raw_target,
    raw_source=raw_source,
    raw_target=raw_target,
    orig_cfg=words[8],
    raw_cfg=words[9],
    restored_cfg=words[10],
    sink=words[11],
    counter_before=words[12],
    counter_after=words[13],
    target_sink=target_sink,
    status=words[1],
  )


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description="Disable NIU coordinate translation and probe raw physical NoC coords.")
  parser.add_argument("--mode", default=MODE_NAMES[MODE_L1_WRITE], choices=tuple(MODE_NAMES.values()))
  parser.add_argument("--noc", type=int, default=0, choices=(0, 1))
  parser.add_argument("--source", type=harness.parse_core, default=(1, 2))
  parser.add_argument("--target", type=harness.parse_core, default=(2, 2), help="worker target for l1-write")
  parser.add_argument("--raw-source", type=harness.parse_core, default=None)
  parser.add_argument("--raw-target", type=harness.parse_core, default=None)
  parser.add_argument("--bank", type=int, default=0, help="DRAM bank for dram-read")
  return parser.parse_args()


def main() -> None:
  args = parse_args()
  mode = mode_id(args.mode)
  with harness.open_device() as device:
    if args.source not in set(device.board_info.worker_cores):
      raise ValueError(f"--source {args.source} is not a worker core")
    raw_source = args.raw_source or raw_coord_for_noc(args.source, args.noc)
    host_target = None
    if mode in (MODE_L1_WRITE, MODE_L1_ROUNDTRIP):
      if args.raw_target is None and args.target not in set(device.board_info.worker_cores):
        raise ValueError(f"--target {args.target} is not a worker core")
      host_target = None if args.raw_target is not None else args.target
      raw_target = args.raw_target or raw_coord_for_noc(args.target, args.noc)
      seed_l1(device, args.source, host_target)
    else:
      if args.bank < 0 or args.bank >= len(device.dram.bank_tiles):
        raise ValueError(f"--bank must be in [0, {len(device.dram.bank_tiles) - 1}]")
      dram_addr, dram_coord = seed_dram(device, args.bank)
      raw_target = args.raw_target or raw_coord_for_noc(dram_coord, args.noc)
      with harness.device_window(device, args.source) as win:
        win.target(args.source)
        win.write(RESULT_BASE, b"\0" * RESULT_SIZE)
        win.write(DST_BASE, b"\0" * PACKET_BYTES)
      device.run(RawCoordProgram(
        mode=mode,
        noc=args.noc,
        source=args.source,
        raw_source=raw_source,
        raw_target=raw_target,
        remote_lo=dram_addr,
      ))
      result = read_result(device, args.source, None, mode=mode, noc=args.noc,
                           raw_source=raw_source, raw_target=raw_target)
      print_result(result)
      return

    device.run(RawCoordProgram(
      mode=mode,
      noc=args.noc,
      source=args.source,
      raw_source=raw_source,
      raw_target=raw_target,
      remote_lo=DST_BASE,
    ))
    result = read_result(device, args.source, host_target, mode=mode, noc=args.noc,
                         raw_source=raw_source, raw_target=raw_target)
    print_result(result)


def print_result(r: ProbeResult) -> None:
  print(f"mode={MODE_NAMES[r.mode]} noc={r.noc}")
  print(f"source translated={r.source} raw={r.raw_source}")
  print(f"target translated/host={r.target} raw={r.raw_target}")
  print(f"NIU_CFG_0 original=0x{r.orig_cfg:08x} raw-mode=0x{r.raw_cfg:08x} restored=0x{r.restored_cfg:08x}")
  print(f"translate bits original={(r.orig_cfg >> 14) & 1} raw-mode={(r.raw_cfg >> 14) & 1} restored={(r.restored_cfg >> 14) & 1}")
  print(f"status=0x{r.status:08x}")
  print(f"source_sink=0x{r.sink:08x}")
  if r.target_sink is not None:
    print(f"target_sink=0x{r.target_sink:08x}")
  print(f"counter_before={r.counter_before} counter_after={r.counter_after}")
  if r.status == STATUS_TIMEOUT:
    print("TIMEOUT raw-coordinate probe")
    return
  expected = 0xA5000000 if r.mode in (MODE_L1_WRITE, MODE_L1_ROUNDTRIP) else 0xD5000000
  got = r.target_sink if r.target_sink is not None else r.sink
  if got != expected:
    raise AssertionError(f"expected sink 0x{expected:08x}, got 0x{got:08x}")
  if ((r.raw_cfg >> 14) & 1) != 0 or ((r.restored_cfg >> 14) & 1) != ((r.orig_cfg >> 14) & 1):
    raise AssertionError("translation bit did not clear and restore as expected")
  print("PASS raw-coordinate probe")


if __name__ == "__main__":
  main()
