#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402  (does sys.path + TT_USB bootstrap on import)
from asm import KernelBase
from device import Device
from dsl import (
  a0, a1, a2, a3, a4, a5,
  s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11,
  t0, t1, t2, t3, t4, t5, t6, zero,
)
from program import DevMsgs, Dtype, Program
from ttk.addrs import Core, Dram, noc_xy, p100_dram_bank_base_coords, p100_dram_bank_endpoint_coords
from ttk.mailbox import BriscMailbox as BM
from ttk.noc import NOC, Noc
from ttk.tensix import TensixL1


RESULT_BASE = 0x150000
RESULT_WORDS = 16
RESULT_MAGIC = 0x444E4F43  # "DNOC"
STATUS_STARTED = 0x0D000001
STATUS_DONE = 0x0D00D00D
LOCAL_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
LOCAL_PAGES = 64
DEBUG_CLOCK_MHZ = 1350.0

OP_READ = 1
OP_WRITE = 2
OP_NAMES = {
  OP_READ: "read",
  OP_WRITE: "write",
}


class DramNocKernel(KernelBase, Noc):
  pass


@dataclass(frozen=True)
class CoreRun:
  core: Core
  bank: int
  start_page: int
  endpoint: int
  coord: int | None = None


@dataclass(frozen=True)
class CoreResult:
  core: Core
  words: tuple[int, ...]

  @property
  def start(self) -> int:
    return self.words[8] | (self.words[9] << 32)

  @property
  def end(self) -> int:
    return self.words[10] | (self.words[11] << 32)

  @property
  def counter_before(self) -> int:
    return self.words[12]

  @property
  def counter_after(self) -> int:
    return self.words[13]

  @property
  def sink(self) -> int:
    return self.words[14]


def result_size() -> int:
  return RESULT_WORDS * 4


def emit_header(fw: KernelBase, *, op: int, noc: int, status: int):
  fw.li(s9, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, op, noc, 0, 0, 0, 0, status,
  )):
    fw.li(t0, value)
    fw.sw(t0, s9, off * 4)
  for off in range(8, RESULT_WORDS):
    fw.sw(zero, s9, off * 4)
  return fw


def emit_counter_read(fw: KernelBase, noc: int, counter: int, out, *, addr=t3):
  fw.li(addr, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  return fw.lw(out, addr, 0)


def emit_local_seed(fw: KernelBase):
  fw.li(s8, LOCAL_PAGES)
  fw.mul(s8, s8, s2)
  fw.srli(s8, s8, 2)
  fw.li(s9, LOCAL_BASE)
  fw.li(t0, 0xA5000000)
  loop = fw._new_label("seed_local")
  done = fw._new_label("seed_local_done")
  fw.label(loop)
  fw.beq(s8, zero, done)
  fw.sw(t0, s9, 0)
  fw.addi(s9, s9, 4)
  fw.addi(t0, t0, 4)
  fw.addi(s8, s8, -1)
  fw.j(loop)
  fw.label(done)
  return fw.fence()


def emit_stateful_setup(fw: DramNocKernel, *, op: int, noc: int):
  buf = 1 if op == OP_READ else 0
  fw.noc_wait_cmd_ready(noc, buf, addr=t3, val=t4)
  if op == OP_READ:
    fw.noc_cmd_reg(noc, buf, NOC.CTRL, NOC.CMD_RD_FIELD, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, buf, NOC.RET_ADDR_MID, 0, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, buf, NOC.RET_ADDR_COORDINATE, a5, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_MID, 0, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_COORDINATE, s11, addr=t3, tmp=t4)
  else:
    fw.noc_cmd_reg(noc, buf, NOC.CTRL, NOC.CMD_WR_FIELD, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, buf, NOC.RET_ADDR_MID, 0, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, buf, NOC.RET_ADDR_COORDINATE, s11, addr=t3, tmp=t4)
  fw.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE, s2, addr=t3, tmp=t4)
  return fw.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE_1, 0, addr=t3, tmp=t4)


def emit_stateful_transfer(fw: DramNocKernel, *, op: int, noc: int):
  buf = 1 if op == OP_READ else 0
  fw.noc_wait_cmd_ready(noc, buf, addr=t3, val=t4)
  if op == OP_READ:
    fw.noc_cmd_reg(noc, buf, NOC.RET_ADDR_LO, t5, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_LO, a0, addr=t3, tmp=t4)
  else:
    fw.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_LO, t5, addr=t3, tmp=t4)
    fw.noc_cmd_reg(noc, buf, NOC.RET_ADDR_LO, a0, addr=t3, tmp=t4)
  return fw.noc_cmd_reg(noc, buf, NOC.CMD_CTRL, NOC.CTRL_SEND_REQ, addr=t3, tmp=t4)


def build_kernel(*, op: int, noc: int, stateful: bool) -> KernelBase:
  if op not in OP_NAMES:
    raise ValueError(f"unknown op {op}")
  counter = NOC.NIU_MST_RD_RESP_RECEIVED if op == OP_READ else NOC.NIU_MST_WR_ACK_RECEIVED
  fw = DramNocKernel()
  emit_header(fw, op=op, noc=noc, status=STATUS_STARTED)
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s2, s3, s4, s5, s11))
  # RTA: dram_base, bank_count, page_size, page_count, bank_id, start_page, endpoint_coord.
  if op == OP_WRITE:
    emit_local_seed(fw)
  fw.local_noc0_coord(a5, x_addr=BM.MY_X, y_addr=BM.MY_Y)
  emit_counter_read(fw, noc, counter, s7)
  fw.mv(s6, s7)
  if stateful:
    emit_stateful_setup(fw, op=op, noc=noc)

  harness.read_wall_clock(fw, a2, a3)
  fw.li(s9, RESULT_BASE)
  fw.sw(a2, s9, 8 * 4)
  fw.sw(a3, s9, 9 * 4)
  fw.mv(s8, zero)
  loop = fw._new_label("dram_noc_loop")
  done = fw._new_label("dram_noc_done")
  fw.label(loop)
  fw.beq(s8, s3, done)

  fw.add(a1, s5, s8)
  # Explicit endpoint mode: address stays within the selected DRAM bank and
  # coord is the selected routable DRAM endpoint coordinate.
  fw.mul(t0, a1, s2)
  fw.mv(a0, s0)
  fw.add(a0, a0, t0)
  fw.mv(a2, s11)

  fw.andi(t5, s8, LOCAL_PAGES - 1)
  fw.mul(t5, t5, s2)
  fw.li(t6, LOCAL_BASE)
  fw.add(t5, t5, t6)
  if stateful:
    emit_stateful_transfer(fw, op=op, noc=noc)
  elif op == OP_READ:
    fw.noc_read(noc, 1, a0, 0, a2, t5, s2, ret_coord=a5, a=t3, v=t4)
  else:
    fw.noc_write(noc, 0, t5, a0, 0, a2, s2, posted=False, a=t3, v=t4)
  fw.addi(s6, s6, 1)
  fw.addi(s8, s8, 1)
  fw.j(loop)

  fw.label(done)
  if op == OP_READ:
    fw.noc_reads_flushed(noc, s6, addr=t3, val=t4)
  else:
    fw.noc_write_barrier(noc, s6, addr=t3, val=t4)
  harness.read_wall_clock(fw, a4, a5)
  emit_counter_read(fw, noc, counter, s11)
  fw.li(t0, LOCAL_BASE)
  fw.lw(s10, t0, 0)

  fw.li(s9, RESULT_BASE)
  for off, reg in enumerate((a4, a5, s7, s11, s10), start=10):
    fw.sw(reg, s9, off * 4)
  fw.li(t0, STATUS_DONE)
  fw.sw(t0, s9, 7 * 4)
  return fw.ret()


def build_program(
  core_runs: list[CoreRun], *, op: int, noc: int, dram_base: int, bank_count: int,
  packet_bytes: int, packet_count: int, stateful: bool,
) -> Program:
  empty = KernelBase()
  args_by_core = {
    run.core: [
      dram_base, bank_count, packet_bytes, packet_count,
      run.bank, run.start_page, run.coord or 0,
    ]
    for run in core_runs
  }
  kernel = build_kernel(op=op, noc=noc, stateful=stateful)
  kernel.rta(lambda x, y: args_by_core[(x, y)])
  program = Program(
    brisc=kernel,
    ncrisc=empty,
    trisc0=empty,
    trisc1=empty,
    trisc2=empty,
    num_cores=len(core_runs),
  )
  post_mode = "stateful" if stateful else "standard"
  program.name = f"riscv_dram_noc_bench:{OP_NAMES[op]}:noc{noc}:{post_mode}:cores{len(core_runs)}"
  return program


def parse_counts(text: str) -> list[int]:
  counts = [int(item.strip()) for item in text.split(",") if item.strip()]
  if not counts or any(count <= 0 for count in counts):
    raise argparse.ArgumentTypeError("expected comma-separated positive core counts")
  return counts


def choose_endpoint(*, endpoint_mode: str, idx: int, preferred_endpoint: int | None) -> int:
  if endpoint_mode == "preferred":
    if preferred_endpoint is None:
      raise ValueError("preferred endpoint was not supplied")
    return preferred_endpoint
  if endpoint_mode == "split3":
    return idx % Dram.TILES_PER_BANK
  return int(endpoint_mode)


def assign_core_runs(
  cores: list[Core], *, count: int, bank_count: int, mode: str, bank: int, packet_count: int,
  endpoint_mode: str, preferred_coords: list[int], bank_coords: dict[int, Core],
) -> list[CoreRun]:
  selected = cores[:count]
  runs = []
  for idx, core in enumerate(selected):
    if mode == "single-bank":
      run_bank = bank
      start_page = idx * packet_count
    else:
      run_bank = idx % bank_count
      start_page = (idx // bank_count) * packet_count
    preferred_endpoint = None
    if endpoint_mode == "preferred":
      base_x, base_y = bank_coords[run_bank]
      preferred_coord = preferred_coords[run_bank]
      preferred_endpoint = ((preferred_coord >> 6) & 0x3F) - base_y
      if (preferred_coord & 0x3F) != base_x:
        raise ValueError(f"preferred coord bank {run_bank} does not match bank base coord")
    endpoint = choose_endpoint(endpoint_mode=endpoint_mode, idx=idx, preferred_endpoint=preferred_endpoint)
    if endpoint_mode == "preferred":
      coord = preferred_coords[run_bank]
    else:
      x, y0 = bank_coords[run_bank]
      coord = noc_xy(x, y0 + endpoint)
    runs.append(CoreRun(core=core, bank=run_bank, start_page=start_page, endpoint=endpoint, coord=coord))
  return runs


def clear_results(device: Device, cores: list[Core]):
  with harness.device_window(device, cores[0]) as win:
    for core in cores:
      win.target(core)
      win.write(RESULT_BASE, b"\0" * result_size())


def read_result(device: Device, core: Core) -> CoreResult:
  with harness.device_window(device, core) as win:
    blob = win.read(RESULT_BASE, result_size())
  if blob and all(b == 0xFF for b in blob):
    raise RuntimeError(f"{core}: L1 readback returned all 0xff")
  words = struct.unpack_from("<" + "I" * RESULT_WORDS, blob, 0)
  if words[0] != RESULT_MAGIC:
    raise RuntimeError(f"{core}: bad result magic 0x{words[0]:08x}")
  if words[7] != STATUS_DONE:
    raise RuntimeError(f"{core}: benchmark did not finish, status=0x{words[7]:08x}")
  return CoreResult(core=core, words=words)


def summarize(
  *, op: int, noc: int, mode: str, endpoint_mode: str, count: int, packet_bytes: int, packet_count: int,
  stateful: bool, results: list[CoreResult],
) -> str:
  total_bytes = count * packet_count * packet_bytes
  window = max(result.end for result in results) - min(result.start for result in results)
  bpc = total_bytes / window if window > 0 else 0.0
  gbps = bpc * DEBUG_CLOCK_MHZ / 1000.0
  bad = sum(((result.counter_after - result.counter_before) & 0xFFFFFFFF) != packet_count for result in results)
  post_mode = "stateful" if stateful else "standard"
  return (
    f"| {OP_NAMES[op]} | {noc} | {mode} | {endpoint_mode} | {post_mode} | {count} | {total_bytes / (1024 * 1024):.1f} | "
    f"{window} | {bpc:.3f} | {gbps:.1f} | {bad} |"
  )


def append_report(
  path: Path, *, bytes_per_core: int, packet_bytes: int, bank_count: int, endpoint_mode: str,
  stateful: bool, lines: list[str],
):
  harness.append_report(path, None, [
    f"Bytes per core: `{bytes_per_core}`",
    f"Packet size: `{packet_bytes}` bytes",
    f"DRAM banks/controllers used by allocator: `{bank_count}`",
    f"Endpoint mode: `{endpoint_mode}`",
    f"Posting mode: `{'stateful' if stateful else 'standard'}`",
    "Timing: device-side wall clock around NoC tile reads/writes and completion flush/barrier",
  ], "\n".join(lines))


def main():
  parser = argparse.ArgumentParser(description="Benchmark device-side DRAM<->L1 NoC transfers.")
  parser.add_argument("--ops", default="read,write", help="comma-separated ops: read,write")
  parser.add_argument("--nocs", default="0,1", help="comma-separated NoC ids")
  parser.add_argument("--mode", choices=("spread", "single-bank"), default="spread")
  parser.add_argument("--bank", type=int, default=0, help="bank id for --mode single-bank")
  parser.add_argument(
    "--endpoint",
    choices=("preferred", "0", "1", "2", "split3"),
    default="preferred",
    help="DRAM endpoint mode: preferred bank table, explicit endpoint 0/1/2, or stripe endpoints across workers",
  )
  parser.add_argument("--bytes-per-core", type=int, default=1024 * 1024)
  parser.add_argument(
    "--packet-bytes",
    type=int,
    default=Dtype.Float16_b.tile_size,
    help="bytes per NoC DRAM command; must be 2 KiB..16 KiB and divide --bytes-per-core",
  )
  parser.add_argument("--counts", type=parse_counts, default=parse_counts("1,7,14,28,56,118"))
  parser.add_argument(
    "--stateful",
    action="store_true",
    help="preprogram fixed NoC command fields once, like TT-Metal one-packet stateful APIs",
  )
  parser.add_argument("--no-report", action="store_true")
  parser.add_argument("--report", type=Path, default=harness.doc_path("noc", "dram-noc-bench.md"))
  args = parser.parse_args()

  op_map = {name: op for op, name in OP_NAMES.items()}
  ops = tuple(op_map[item.strip()] for item in args.ops.split(",") if item.strip())
  nocs = tuple(int(item.strip()) for item in args.nocs.split(",") if item.strip())
  if not ops:
    raise ValueError("--ops selected no operations")
  if any(noc not in (0, 1) for noc in nocs):
    raise ValueError("--nocs must contain only 0 and/or 1")
  if args.packet_bytes <= 0 or args.packet_bytes > NOC.MAX_BURST_SIZE:
    raise ValueError(f"--packet-bytes must be in [1, {NOC.MAX_BURST_SIZE}]")
  if args.packet_bytes % Dtype.Float16_b.tile_size:
    raise ValueError(f"--packet-bytes must be a multiple of {Dtype.Float16_b.tile_size}")
  if args.bytes_per_core <= 0 or args.bytes_per_core % args.packet_bytes:
    raise ValueError("--bytes-per-core must be a positive multiple of --packet-bytes")
  packet_count = args.bytes_per_core // args.packet_bytes

  os.environ.pop("TT_USB", None)
  lines = [
    "| op | noc | mode | endpoint | posting | cores | total MiB | window cyc | agg B/cyc | agg GB/s | bad counter rows |",
    "|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|",
  ]
  with harness.open_device() as device:
    bank_count = len(device.dram.bank_tiles)
    bank_coords = p100_dram_bank_base_coords(device.board_info.harvested_dram_bank)
    if args.bank < 0 or args.bank >= bank_count:
      raise ValueError(f"--bank must be in [0, {bank_count - 1}]")
    max_count = len(device.cores)
    if any(count > max_count for count in args.counts):
      raise ValueError(f"requested core count above available program cores ({max_count})")

    max_pages_per_bank = (max(args.counts) * args.bytes_per_core + Dtype.Float16_b.tile_size - 1) // Dtype.Float16_b.tile_size
    # Logical tile ids are bank + page * bank_count, so this allocation covers
    # the largest single-bank case with plenty of room for spread mode too.
    buf = device.dram.alloc(bank_count * max_pages_per_bank, Dtype.Float16_b, name="dram_noc_bench")
    for op in ops:
      for noc in nocs:
        preferred_coords = p100_dram_bank_endpoint_coords(device.board_info.harvested_dram_bank, noc)
        for count in args.counts:
          core_runs = assign_core_runs(
            device.cores,
            count=count,
            bank_count=bank_count,
            mode=args.mode,
            bank=args.bank,
            packet_count=packet_count,
            endpoint_mode=args.endpoint,
            preferred_coords=preferred_coords,
            bank_coords=bank_coords,
          )
          clear_results(device, [run.core for run in core_runs])
          device.run(build_program(
            core_runs,
            op=op,
            noc=noc,
            dram_base=buf.addr,
            bank_count=bank_count,
            packet_bytes=args.packet_bytes,
            packet_count=packet_count,
            stateful=args.stateful,
          ))
          results = [read_result(device, run.core) for run in core_runs]
          lines.append(summarize(
            op=op,
            noc=noc,
            mode=args.mode,
            endpoint_mode=args.endpoint,
            count=count,
            packet_bytes=args.packet_bytes,
            packet_count=packet_count,
            stateful=args.stateful,
            results=results,
          ))

  table = "\n".join(lines)
  print(table)
  if not args.no_report:
    append_report(
      args.report,
      bytes_per_core=args.bytes_per_core,
      packet_bytes=args.packet_bytes,
      bank_count=bank_count,
      endpoint_mode=args.endpoint,
      stateful=args.stateful,
      lines=lines,
    )
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
