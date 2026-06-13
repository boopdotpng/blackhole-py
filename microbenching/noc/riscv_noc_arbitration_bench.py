#!/usr/bin/env python3
from __future__ import annotations

import argparse
import statistics
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402  (does sys.path + TT_USB bootstrap on import)
try:
  import noc_topology
except ModuleNotFoundError:
  from microbenching import noc_topology
from asm import KernelBase
from device import Device
from dsl import a2, a3, a4, a5, s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, t0, t3, t4, zero
from pcie import TLBWindow
from program import DevMsgs, Program, Run, UnicastWrite
from ttk.addrs import Core, align_down, noc_xy
from ttk.mailbox import BriscMailbox as BM
from ttk.noc import NOC, Noc
from ttk.tensix import TensixL1, TensixMMIO


RESULT_BASE = 0x150000
READBACK_BASE = RESULT_BASE + 0x800
START_GATE_BASE = RESULT_BASE + 0x1000
STREAM_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
DEST_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
DEST_STRIDE = 0x8000
RECORD_WORDS = 24
RECORD_SIZE = RECORD_WORDS * 4
RESULT_MAGIC = 0x524E4141  # "RNAA"
STATUS_STARTED = 0xA1000001
STATUS_DONE = 0xA100D00D
P100_PROGRAM_CORES = [(x, y) for y in noc_topology.P100_WORKER_Y for x in noc_topology.P100_WORKER_X]
P100_FAST_DISPATCH_RESERVED = {(14, 2), (14, 3)}


@dataclass(frozen=True)
class SenderSpec:
  index: int
  source: Core
  target: Core
  dest_base: int

  @property
  def stream(self) -> noc_topology.Stream:
    return (self.source, self.target)


@dataclass(frozen=True)
class SenderResult:
  core: Core
  words: tuple[int, ...]

  @property
  def sender_index(self) -> int:
    return self.words[4]

  @property
  def packet_bytes(self) -> int:
    return self.words[6]

  @property
  def packets(self) -> int:
    return self.words[7]

  @property
  def target(self) -> Core:
    return self.words[8], self.words[9]

  @property
  def dest_base(self) -> int:
    return self.words[10]

  @property
  def start(self) -> int:
    return self.words[12] | (self.words[13] << 32)

  @property
  def end(self) -> int:
    return self.words[14] | (self.words[15] << 32)

  @property
  def cycles(self) -> int:
    return (self.end - self.start) & ((1 << 64) - 1)

  @property
  def ack_delta(self) -> int:
    return (self.words[17] - self.words[16]) & 0xFFFFFFFF

  @property
  def nonposted_req_delta(self) -> int:
    return (self.words[19] - self.words[18]) & 0xFFFFFFFF

  @property
  def rd_resp_delta(self) -> int:
    return (self.words[21] - self.words[20]) & 0xFFFFFFFF

  @property
  def sentinel(self) -> int:
    return self.words[22]

  @property
  def bytes_total(self) -> int:
    return self.packet_bytes * self.packets

  @property
  def bytes_per_cycle(self) -> float:
    return self.bytes_total / self.cycles if self.cycles > 0 else 0.0


@dataclass(frozen=True)
class TargetResult:
  core: Core
  words: tuple[int, ...]

  @property
  def missing(self) -> int:
    return self.words[11]

  @property
  def poll_iters(self) -> int:
    return self.words[16]


@dataclass(frozen=True)
class ArbitrationRun:
  noc: int
  k: int
  packet_bytes: int
  packets: int
  target: Core
  senders: list[SenderSpec]
  results: list[SenderResult]
  target_result: TargetResult


class ArbitrationKernel(KernelBase, Noc):
  pass


def expected_sentinel(packet_bytes: int) -> int:
  return 0xA5000000 | (packet_bytes - 4)


def result_size() -> int:
  return RECORD_SIZE


def emit_counter_read(fw: KernelBase, noc: int, counter: int, out, *, addr=t3):
  fw.li(addr, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  return fw.lw(out, addr, 0)


def emit_record_header(
  fw: KernelBase, *,
  status: int,
  noc: int,
  sender_index: int,
  k: int,
  packet_bytes: int,
  packets: int,
  target: Core,
  dest_base: int,
):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, 1, status, noc, sender_index, k, packet_bytes, packets,
    target[0], target[1], dest_base, 0,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off in range(12, RECORD_WORDS):
    fw.sw(zero, s2, off * 4)
  return fw


def emit_start_gate(fw: ArbitrationKernel):
  wait = fw._new_label("start_gate_wait")
  done = fw._new_label("start_gate_done")
  fw.li(s2, START_GATE_BASE)
  fw.lw(s10, s2, 0)
  fw.lw(s11, s2, 4)
  fw.label(wait)
  harness.read_wall_clock(fw, a2, a3)
  fw.bltu(a3, s11, wait)
  fw.bne(a3, s11, done)
  fw.bltu(a2, s10, wait)
  fw.label(done)
  return fw


def build_sender(spec: SenderSpec, *, noc: int, k: int, packet_bytes: int, packets: int) -> KernelBase:
  fw = ArbitrationKernel()
  emit_record_header(
    fw,
    status=STATUS_STARTED,
    noc=noc,
    sender_index=spec.index,
    k=k,
    packet_bytes=packet_bytes,
    packets=packets,
    target=spec.target,
    dest_base=spec.dest_base,
  )
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s9,))
  fw.local_noc_coord(noc, s5, x_addr=BM.MY_X, y_addr=BM.MY_Y)

  emit_start_gate(fw)
  fw.li(s2, STREAM_BASE)
  fw.li(s3, spec.dest_base)
  fw.li(s4, packet_bytes)
  emit_counter_read(fw, noc, NOC.NIU_MST_WR_ACK_RECEIVED, s7)
  emit_counter_read(fw, noc, NOC.NIU_MST_NONPOSTED_WR_REQ_SENT, s8)
  emit_counter_read(fw, noc, NOC.NIU_MST_RD_RESP_RECEIVED, s11)
  fw.mv(s6, s7)
  harness.read_wall_clock(fw, a2, a3)

  fw.li(s0, packets)
  loop = fw._new_label("arb_write_loop")
  done = fw._new_label("arb_write_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  fw.noc_write(noc, 0, s2, s3, 0, s9, s4, posted=False, a=t3, v=t4)
  fw.addi(s6, s6, 1)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  fw.noc_write_barrier(noc, s6, addr=t3, val=t4)
  harness.read_wall_clock(fw, a4, a5)

  fw.li(s2, RESULT_BASE)
  for off, reg in enumerate((a2, a3, a4, a5, s7), start=12):
    fw.sw(reg, s2, off * 4)
  emit_counter_read(fw, noc, NOC.NIU_MST_WR_ACK_RECEIVED, t0)
  fw.sw(t0, s2, 17 * 4)
  fw.sw(s8, s2, 18 * 4)
  emit_counter_read(fw, noc, NOC.NIU_MST_NONPOSTED_WR_REQ_SENT, t0)
  fw.sw(t0, s2, 19 * 4)
  fw.sw(s11, s2, 20 * 4)
  emit_counter_read(fw, noc, NOC.NIU_MST_RD_RESP_RECEIVED, t0)
  fw.sw(t0, s2, 21 * 4)

  fw.li(s2, RESULT_BASE)
  fw.sw(zero, s2, 22 * 4)

  fw.li(t0, STATUS_DONE)
  fw.sw(t0, s2, 2 * 4)
  return fw.ret()


def build_target_receiver(*, k: int, packet_bytes: int, max_polls: int) -> KernelBase:
  fw = ArbitrationKernel()
  emit_record_header(
    fw,
    status=STATUS_STARTED,
    noc=2,
    sender_index=0,
    k=k,
    packet_bytes=packet_bytes,
    packets=0,
    target=(0, 0),
    dest_base=DEST_BASE,
  )
  emit_start_gate(fw)
  fw.li(s0, max_polls)
  fw.mv(s10, zero)
  harness.read_wall_clock(fw, a2, a3)
  poll = fw._new_label("arb_recv_poll")
  found = [fw._new_label(f"arb_recv_found_{i}") for i in range(k)]
  done = fw._new_label("arb_recv_done")
  timeout = fw._new_label("arb_recv_timeout")
  expected = expected_sentinel(packet_bytes)
  fw.label(poll)
  fw.beq(s0, zero, timeout)
  fw.mv(s6, zero)
  for i in range(k):
    fw.li(s2, DEST_BASE + i * DEST_STRIDE + packet_bytes - 4)
    fw.lw(t0, s2, 0)
    fw.li(t4, expected)
    fw.beq(t0, t4, found[i])
    fw.addi(s6, s6, 1)
    fw.label(found[i])
  fw.beq(s6, zero, done)
  fw.addi(s10, s10, 1)
  fw.addi(s0, s0, -1)
  fw.j(poll)
  fw.label(timeout)
  fw.label(done)
  harness.read_wall_clock(fw, a4, a5)
  fw.li(s2, RESULT_BASE)
  for off, reg in enumerate((a2, a3, a4, a5), start=12):
    fw.sw(reg, s2, off * 4)
  fw.sw(s10, s2, 16 * 4)
  fw.sw(s6, s2, 11 * 4)
  fw.li(t0, STATUS_DONE)
  fw.sw(t0, s2, 2 * 4)
  return fw.ret()


def _one_core_segments(core: Core, kernel: KernelBase, *, dispatch_mode: int, host_assigned_id: int):
  empty = KernelBase()
  return Program(
    brisc=kernel,
    ncrisc=empty,
    trisc0=empty,
    trisc1=empty,
    trisc2=empty,
    num_cores=1,
  ).layout(core_xy=core, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id)


class ArbitrationProgram:
  def __init__(self, senders: list[SenderSpec], *, noc: int, packet_bytes: int, packets: int):
    self.senders = list(senders)
    self.noc = noc
    self.packet_bytes = packet_bytes
    self.packets = packets
    self.name = f"riscv_noc_arbitration:noc{noc}:k{len(senders)}:pkt{packet_bytes}"

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    per_core_segments = {}
    target_cores = []
    target = self.senders[0].target
    for spec in self.senders:
      sender = build_sender(
        spec,
        noc=self.noc,
        k=len(self.senders),
        packet_bytes=self.packet_bytes,
        packets=self.packets,
      )
      sender.rta(lambda _x, _y, target=spec.target: [noc_xy(*target)])
      per_core_segments[spec.source] = _one_core_segments(
        spec.source,
        sender,
        dispatch_mode=dispatch_mode,
        host_assigned_id=host_assigned_id,
      )
      target_cores.append(spec.source)

    per_core_segments[target] = _one_core_segments(
      target,
      build_target_receiver(k=len(self.senders), packet_bytes=self.packet_bytes, max_polls=100_000_000),
      dispatch_mode=dispatch_mode,
      host_assigned_id=host_assigned_id,
    )
    target_cores.append(target)

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


def rows_by_y(cores: list[Core]) -> dict[int, list[int]]:
  rows: dict[int, list[int]] = {}
  for x, y in cores:
    rows.setdefault(y, []).append(x)
  return {y: sorted(xs) for y, xs in rows.items()}


def choose_row(cores: list[Core], requested_row: int | None) -> tuple[int, list[int]]:
  rows = rows_by_y(cores)
  if requested_row is not None:
    xs = rows.get(requested_row)
    if xs is None or len(xs) < 9:
      raise ValueError(f"row {requested_row} needs at least 9 program cores for K=8 plus target")
    return requested_row, xs
  candidates = [(len(xs), -y, y, xs) for y, xs in rows.items()]
  _, _, y, xs = max(candidates)
  if len(xs) < 9:
    raise ValueError("arbitration bench needs a row with at least 9 program cores")
  return y, xs


def build_sender_set(cores: list[Core], *, noc: int, k: int, row: int | None) -> tuple[Core, list[SenderSpec]]:
  y, xs = choose_row(cores, row)
  if noc == 0:
    target = (xs[-1], y)
    source_xs = xs[-1 - k:-1]
  else:
    target = (xs[0], y)
    source_xs = xs[1:1 + k]
  if len(source_xs) != k:
    raise ValueError(f"row {y} does not have {k} usable sender cores for NoC{noc}")

  senders = [
    SenderSpec(index=i, source=(x, y), target=target, dest_base=DEST_BASE + i * DEST_STRIDE)
    for i, x in enumerate(source_xs)
  ]
  final_links = {noc_topology.path_links(spec.source, spec.target, noc)[-1] for spec in senders}
  if len(final_links) != 1:
    raise RuntimeError(f"internal placement error: expected one shared final link, got {sorted(final_links)}")
  return target, senders


def exclude_reserved_cores(cores: list[Core], reserved: set[Core]) -> list[Core]:
  return [core for core in cores if core not in reserved]


def parse_counts(text: str) -> tuple[int, ...]:
  counts = tuple(int(item.strip()) for item in text.split(",") if item.strip())
  if not counts or any(count <= 0 for count in counts):
    raise argparse.ArgumentTypeError("expected comma-separated positive K values")
  return counts


def parse_nocs(text: str) -> tuple[int, ...]:
  nocs = tuple(int(item.strip()) for item in text.split(",") if item.strip())
  if not nocs or any(noc not in (0, 1) for noc in nocs):
    raise argparse.ArgumentTypeError("expected comma-separated NoC ids from {0,1}")
  return nocs


def parse_packet_sizes(text: str) -> tuple[int, ...]:
  sizes = tuple(int(item.strip()) for item in text.split(",") if item.strip())
  if not sizes or any(size <= 0 or size > NOC.MAX_BURST_SIZE or size % 4 for size in sizes):
    raise argparse.ArgumentTypeError("packet sizes must be positive 4-byte multiples no larger than 16 KiB")
  return sizes


def seed_packet(packet_bytes: int) -> bytes:
  seed = bytearray(packet_bytes)
  for off in range(0, packet_bytes, 4):
    struct.pack_into("<I", seed, off, 0xA5000000 | off)
  return bytes(seed)


def read_wall_clock_host(device: Device, core: Core) -> int:
  base, off_h = align_down(TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_H, TLBWindow.SIZE_2M)
  off_l = TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L - base
  with harness.device_window(device, core, addr=base) as win:
    while True:
      hi0 = struct.unpack("<I", win.read(off_h, 4))[0]
      lo = struct.unpack("<I", win.read(off_l, 4))[0]
      hi1 = struct.unpack("<I", win.read(off_h, 4))[0]
      if hi0 == hi1:
        return lo | (hi0 << 32)


def clear_seed_and_gate(device: Device, senders: list[SenderSpec], *, packet_bytes: int, gate_value: int):
  target = senders[0].target
  seed = seed_packet(packet_bytes)
  with harness.device_window(device, senders[0].source) as win:
    for spec in senders:
      win.target(spec.source)
      win.write(RESULT_BASE, b"\0" * result_size())
      win.write(START_GATE_BASE, struct.pack("<Q", gate_value))
      win.write(STREAM_BASE, seed)
    win.target(target)
    win.write(START_GATE_BASE, struct.pack("<Q", gate_value))
    for spec in senders:
      win.write(spec.dest_base, b"\0" * packet_bytes)


def read_sender_result(device: Device, spec: SenderSpec) -> SenderResult:
  with harness.device_window(device, spec.source) as win:
    win.target(spec.source)
    blob = win.read(RESULT_BASE, result_size())
    words = struct.unpack_from("<" + "I" * RECORD_WORDS, blob, 0)
  if words[0] != RESULT_MAGIC:
    raise RuntimeError(f"{spec.source}: bad result magic 0x{words[0]:08x}")
  if words[2] != STATUS_DONE:
    raise RuntimeError(f"{spec.source}: benchmark did not finish, status=0x{words[2]:08x}")
  return SenderResult(spec.source, words)


def read_target_result(device: Device, target: Core) -> TargetResult:
  with harness.device_window(device, target) as win:
    win.target(target)
    blob = win.read(RESULT_BASE, result_size())
    words = struct.unpack_from("<" + "I" * RECORD_WORDS, blob, 0)
  if words[0] != RESULT_MAGIC:
    raise RuntimeError(f"{target}: bad target result magic 0x{words[0]:08x}")
  if words[2] != STATUS_DONE:
    raise RuntimeError(f"{target}: target receiver did not finish, status=0x{words[2]:08x}")
  return TargetResult(target, words)


def run_once(
  device: Device,
  senders: list[SenderSpec],
  *,
  noc: int,
  packet_bytes: int,
  packets: int,
  gate_cycles: int,
) -> tuple[list[SenderResult], TargetResult]:
  now = max(read_wall_clock_host(device, spec.source) for spec in senders)
  gate_value = now + gate_cycles
  clear_seed_and_gate(device, senders, packet_bytes=packet_bytes, gate_value=gate_value)
  device.run(ArbitrationProgram(senders, noc=noc, packet_bytes=packet_bytes, packets=packets))
  return [read_sender_result(device, spec) for spec in senders], read_target_result(device, senders[0].target)


def classify_distribution(results: list[SenderResult]) -> str:
  rates = [result.bytes_per_cycle for result in results]
  if len(rates) < 2:
    return "single stream"
  avg = statistics.fmean(rates)
  spread = (max(rates) - min(rates)) / avg if avg else 0.0
  if spread <= 0.10:
    return "roughly equal"
  best = max(results, key=lambda result: result.bytes_per_cycle)
  if best.sender_index == len(results) - 1:
    return "near target favored"
  if best.sender_index == 0:
    return "far source favored"
  return "middle source favored"


def validation_counts(run: ArbitrationRun) -> tuple[int, int]:
  bad_counters = sum(
    result.ack_delta != run.packets or result.nonposted_req_delta != run.packets
    for result in run.results
  )
  return bad_counters, run.target_result.missing


def format_summary(runs: list[ArbitrationRun]) -> str:
  lines = [
    "| noc | K | packet B | packets | target | sender order | aggregate B/cyc | aggregate req/cyc | per-stream B/cyc | spread | interpretation | bad counters | target missing | target polls |",
    "|---:|---:|---:|---:|---|---|---:|---:|---|---:|---|---:|---:|---:|",
  ]
  for run in runs:
    rates = [result.bytes_per_cycle for result in run.results]
    avg = statistics.fmean(rates) if rates else 0.0
    spread = (max(rates) - min(rates)) / avg if avg else 0.0
    aggregate_window = max(result.end for result in run.results) - min(result.start for result in run.results)
    aggregate_bytes = sum(result.bytes_total for result in run.results)
    aggregate_bpc = aggregate_bytes / aggregate_window if aggregate_window > 0 else 0.0
    aggregate_rpc = aggregate_bpc / run.packet_bytes if run.packet_bytes > 0 else 0.0
    bad_counters, bad_sentinels = validation_counts(run)
    sender_order = " ".join(f"`{spec.source[0]},{spec.source[1]}`" for spec in run.senders)
    rate_text = " ".join(f"{result.bytes_per_cycle:.3f}" for result in run.results)
    lines.append(
      f"| {run.noc} | {run.k} | {run.packet_bytes} | {run.packets} | `{run.target[0]},{run.target[1]}` | "
      f"{sender_order} | {aggregate_bpc:.3f} | {aggregate_rpc:.5f} | {rate_text} | "
      f"{spread:.3f} | {classify_distribution(run.results)} | "
      f"{bad_counters} | {bad_sentinels} | {run.target_result.poll_iters} |"
    )
  return "\n".join(lines)


def assert_valid_run(run: ArbitrationRun):
  bad_counters, bad_sentinels = validation_counts(run)
  if bad_counters or bad_sentinels:
    expected = expected_sentinel(run.packet_bytes)
    raise RuntimeError(
      f"invalid arbitration run noc{run.noc} K={run.k} packet={run.packet_bytes}: "
      f"bad_counters={bad_counters} target_missing={bad_sentinels} "
      f"expected_sentinel=0x{expected:08x}. "
      "Full matrix is blocked until sentinel validation is understood; pass "
      "--allow-invalid only for a deliberate debug run."
    )


def append_report(path: Path, *, gate_cycles: int, runs: list[ArbitrationRun]):
  harness.append_report(path, None, [
    f"Start gate lead: `{gate_cycles}` cycles",
    "Traffic: BRISC nonposted peer-L1 writes, one far-end receiver tile, one destination slice per sender",
    "Placement: one row; NoC0 sends right into the row's right edge, NoC1 sends left into the row's left edge",
    "Sender order: farthest from target to nearest target; favored nearest implies through-traffic priority, favored farthest implies injection priority",
  ], format_summary(runs))


def dry_run(args):
  runs = []
  cores = exclude_reserved_cores(P100_PROGRAM_CORES, P100_FAST_DISPATCH_RESERVED)
  for noc in args.nocs:
    for k in args.counts:
      target, senders = build_sender_set(cores, noc=noc, k=k, row=args.row)
      for packet_bytes in args.packet_bytes:
        program = ArbitrationProgram(senders, noc=noc, packet_bytes=packet_bytes, packets=args.packets)
        program.lower(dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0)
        print(
          f"dry-run noc{noc} K={k} packet={packet_bytes} packets={args.packets} "
          f"target={target} shared_final={noc_topology.path_links(senders[0].source, target, noc)[-1]}"
        )
        runs.append((noc, k, packet_bytes, target, senders))
  return runs


def main():
  parser = argparse.ArgumentParser(description="Experiment A: NoC fair-share / injection arbitration.")
  parser.add_argument("--nocs", type=parse_nocs, default=(0, 1), help="comma-separated NoC ids, default: 0,1")
  parser.add_argument("--counts", type=parse_counts, default=parse_counts("2,3,4,6,8"), help="comma-separated K values")
  parser.add_argument("--packet-bytes", type=parse_packet_sizes, default=parse_packet_sizes("4096,16384"))
  parser.add_argument("--packets", type=int, default=256, help="NoC write packets per sender")
  parser.add_argument("--row", type=int, default=None, help="physical row to use; default: row with most program cores")
  parser.add_argument("--gate-cycles", type=int, default=100_000_000, help="future WALL_CLOCK start-gate lead")
  parser.add_argument("--dry-run", action="store_true", help="lower programs without opening the device")
  parser.add_argument("--allow-invalid", action="store_true", help="do not abort/report-block on bad counters or target receiver misses")
  parser.add_argument("--no-report", action="store_true", help="do not append docs/noc-arbitration.md")
  parser.add_argument("--report", type=Path, default=harness.doc_path("noc", "noc-arbitration.md"), help="markdown report path")
  args = parser.parse_args()
  if args.packets <= 0:
    raise ValueError("--packets must be positive")
  if args.gate_cycles <= 0:
    raise ValueError("--gate-cycles must be positive")
  if max(args.counts) > 8:
    raise ValueError("this initial experiment supports K up to 8")

  if args.dry_run:
    dry_run(args)
    return

  runs: list[ArbitrationRun] = []
  with harness.open_device() as device:
    reserved = {
      getattr(device.board_info, "dispatch_core", None),
      getattr(device.board_info, "prefetch_core", None),
    }
    core_set = set(device.cores) - {core for core in reserved if core is not None}
    usable_cores = sorted(core_set)
    for noc in args.nocs:
      for k in args.counts:
        target, senders = build_sender_set(usable_cores, noc=noc, k=k, row=args.row)
        if target not in core_set or any(spec.source not in core_set for spec in senders):
          raise ValueError("selected sender/target is not a program core")
        for packet_bytes in args.packet_bytes:
          results, target_result = run_once(
            device,
            senders,
            noc=noc,
            packet_bytes=packet_bytes,
            packets=args.packets,
            gate_cycles=args.gate_cycles,
          )
          runs.append(ArbitrationRun(
            noc=noc,
            k=k,
            packet_bytes=packet_bytes,
            packets=args.packets,
            target=target,
            senders=senders,
            results=results,
            target_result=target_result,
          ))
          if not args.allow_invalid:
            try:
              assert_valid_run(runs[-1])
            except RuntimeError:
              print(format_summary(runs[-1:]))
              raise

  print(format_summary(runs))
  if not args.no_report:
    append_report(args.report, gate_cycles=args.gate_cycles, runs=runs)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
