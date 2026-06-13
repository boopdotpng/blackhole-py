#!/usr/bin/env python3
from __future__ import annotations

import argparse
import statistics
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
import riscv_noc_hop_sweep as hop_sweep  # noqa: E402
from asm import KernelBase
from device import Device
from dsl import a2, a3, s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, t0, t1, t3, t4, zero
from program import DevMsgs, Program, Run, UnicastWrite
from ttk.addrs import Core, noc_xy
from ttk.blackhole_coords import (
  GRID_H, GRID_W, TensixCoordinateMap, raw_coord_for_noc, tensix_coordinate_map,
  translated_tensix_to_raw_noc0,
)
from ttk.mailbox import BriscMailbox as BM
from ttk.noc import NOC, Noc
from ttk.tensix import TensixL1


RESULT_BASE = 0x150000
HEADER_WORDS = 24
HEADER_SIZE = HEADER_WORDS * 4
SENDER_SAMPLE_WORDS = 6
RECEIVER_SAMPLE_WORDS = 2
RESULT_MAGIC = 0x444C544E  # "NTLD"
STATUS_STARTED = 0xD1000001
STATUS_DONE = 0xD100D00D
ROLE_SENDER = 1
ROLE_RECEIVER = 2

SRC_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
DST_BASE = SRC_BASE
SENTINEL_BASE = 0xA7000001
ENABLED_TENSIX_COL_TAG = 34

MODE_POSTED_WRITE = 1
MODE_NONPOSTED_WRITE = 2
MODE_READ = 3
MODE_ATOMIC_INC = 4
MODE_NAMES = {
  MODE_POSTED_WRITE: "posted_write",
  MODE_NONPOSTED_WRITE: "nonposted_write",
  MODE_READ: "read_flush",
  MODE_ATOMIC_INC: "atomic_inc",
}
WRITE_MODES = {MODE_POSTED_WRITE, MODE_NONPOSTED_WRITE}


class DependencyKernel(KernelBase, Noc):
  pass


@dataclass(frozen=True)
class Route:
  source: Core
  target: Core
  raw0_source: Core
  raw0_target: Core
  raw_source: Core
  raw_target: Core
  hops: int
  x_hops: int
  y_hops: int
  wraps: int


@dataclass(frozen=True)
class RunResult:
  noc: int
  mode: int
  source: Core
  target: Core
  route: Route
  packet_bytes: int
  iters: int
  sent_counter_delta: int
  response_counter_delta: int
  receiver_poll_iters: int
  receiver_final: int
  sender_issue: list[int]
  sender_sent: list[int]
  sender_done: list[int]
  receiver_seen: list[int]

  @property
  def done_minus_issue(self) -> list[int]:
    return [d - i for i, d in zip(self.sender_issue, self.sender_done)]

  @property
  def sent_minus_issue(self) -> list[int]:
    return [s - i for i, s in zip(self.sender_issue, self.sender_sent) if s != 0]

  @property
  def seen_minus_issue(self) -> list[int]:
    return [r - s for s, r in zip(self.sender_issue, self.receiver_seen) if r != 0]

  @property
  def seen_minus_done(self) -> list[int]:
    return [r - d for d, r in zip(self.sender_done, self.receiver_seen) if r != 0]


def u64(lo: int, hi: int) -> int:
  return lo | (hi << 32)


def parse_pair(text: str) -> tuple[Core, Core]:
  try:
    lhs, rhs = text.split(":", 1)
    return harness.parse_core(lhs), harness.parse_core(rhs)
  except Exception as exc:
    raise argparse.ArgumentTypeError("expected pair as X,Y:X,Y") from exc


def parse_sizes(text: str) -> tuple[int, ...]:
  sizes = tuple(int(item.strip(), 0) for item in text.split(",") if item.strip())
  if not sizes:
    raise argparse.ArgumentTypeError("expected comma-separated packet sizes")
  for size in sizes:
    if size < 4 or size > NOC.MAX_BURST_SIZE or size % 4:
      raise argparse.ArgumentTypeError(f"sizes must be 4-byte multiples in [4, {NOC.MAX_BURST_SIZE}]")
  return sizes


def parse_modes(text: str) -> tuple[int, ...]:
  by_name = {name: mode for mode, name in MODE_NAMES.items()}
  by_name.update({
    "posted": MODE_POSTED_WRITE,
    "nonposted": MODE_NONPOSTED_WRITE,
    "read": MODE_READ,
    "atomic": MODE_ATOMIC_INC,
    "semaphore_inc": MODE_ATOMIC_INC,
  })
  modes = []
  for item in (part.strip() for part in text.split(",") if part.strip()):
    if item not in by_name:
      raise argparse.ArgumentTypeError(f"unknown mode {item!r}; expected {','.join(by_name)}")
    modes.append(by_name[item])
  if not modes:
    raise argparse.ArgumentTypeError("expected comma-separated modes")
  return tuple(modes)


def result_size_sender(iters: int) -> int:
  return HEADER_SIZE + iters * SENDER_SAMPLE_WORDS * 4


def result_size_receiver(iters: int) -> int:
  return HEADER_SIZE + iters * RECEIVER_SAMPLE_WORDS * 4


def emit_header(fw: KernelBase, *, role: int, status: int, noc: int, mode: int, packet_bytes: int, iters: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, role, status, noc, mode, packet_bytes, iters, SRC_BASE,
    DST_BASE, SENTINEL_BASE, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  return fw


def emit_status(fw: KernelBase, status: int):
  fw.li(s2, RESULT_BASE)
  fw.li(t0, status)
  fw.sw(t0, s2, 2 * 4)
  return fw


def emit_counter_read(fw: KernelBase, noc: int, counter: int, out, *, addr=t3):
  fw.li(addr, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  return fw.lw(out, addr, 0)


def emit_wait_counter_at_least(fw: KernelBase, noc: int, counter: int, target, *, addr=t3, val=t4):
  fw.li(addr, NOC.STATUS_BASE + counter + (noc << NOC.INSTANCE_OFFSET_BIT))
  loop = fw._new_label("wait_counter")
  fw.label(loop)
  fw.lw(val, addr, 0)
  fw.bltu(val, target, loop)
  return fw


def sent_counter(mode: int) -> int | None:
  if mode == MODE_POSTED_WRITE:
    return NOC.NIU_MST_POSTED_WR_REQ_SENT
  if mode == MODE_NONPOSTED_WRITE:
    return NOC.NIU_MST_NONPOSTED_WR_REQ_SENT
  return None


def response_counter(mode: int) -> int | None:
  if mode == MODE_POSTED_WRITE:
    return None
  if mode == MODE_READ:
    return NOC.NIU_MST_RD_RESP_RECEIVED
  if mode == MODE_ATOMIC_INC:
    return NOC.NIU_MST_ATOMIC_RESP_RECEIVED
  return NOC.NIU_MST_WR_ACK_RECEIVED


def build_sender(noc: int, mode: int, packet_bytes: int, iters: int, start_delay: int) -> KernelBase:
  fw = DependencyKernel()
  emit_header(fw, role=ROLE_SENDER, status=STATUS_STARTED, noc=noc, mode=mode, packet_bytes=packet_bytes, iters=iters)
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s9,))
  fw.local_noc_coord(noc, s5, x_addr=BM.MY_X, y_addr=BM.MY_Y)
  fw.li(s2, SRC_BASE)
  fw.li(s3, DST_BASE)
  fw.li(s4, packet_bytes)
  fw.li(s11, SRC_BASE + packet_bytes - 4)
  fw.li(s10, RESULT_BASE + HEADER_SIZE)
  fw.li(s8, SENTINEL_BASE)
  scounter = sent_counter(mode)
  if scounter is None:
    fw.mv(s7, zero)
  else:
    emit_counter_read(fw, noc, scounter, s7)
  rcounter = response_counter(mode)
  if rcounter is None:
    fw.mv(s6, zero)
  else:
    emit_counter_read(fw, noc, rcounter, s6)
  fw.li(s1, RESULT_BASE)
  fw.sw(s7, s1, 10 * 4)
  fw.sw(s6, s1, 12 * 4)
  if start_delay > 0:
    fw.delay_cycles(start_delay, count=t0)

  fw.li(s0, iters)
  loop = fw._new_label("dependency_send_loop")
  done = fw._new_label("dependency_send_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  harness.read_wall_clock(fw, a2, a3)
  fw.sw(a2, s10, 0)
  fw.sw(a3, s10, 4)
  if mode in WRITE_MODES:
    fw.sw(s8, s11, 0)
    fw.fence()
    fw.noc_write(noc, 0, s2, s3, 0, s9, s4, posted=(mode == MODE_POSTED_WRITE), a=t3, v=t4)
  elif mode == MODE_READ:
    fw.noc_read(noc, 1, s2, 0, s9, s3, s4, ret_coord=s5, a=t3, v=t4)
  elif mode == MODE_ATOMIC_INC:
    fw.noc_semaphore_inc(noc, 3, s3, s9, 1, ret_coord=s5, a=t3, v=t4)
  else:
    raise ValueError(f"unknown mode {mode}")

  if scounter is None:
    fw.sw(zero, s10, 8)
    fw.sw(zero, s10, 12)
  else:
    fw.addi(s7, s7, 1)
    emit_wait_counter_at_least(fw, noc, scounter, s7, addr=t3, val=t4)
    harness.read_wall_clock(fw, a2, a3)
    fw.sw(a2, s10, 8)
    fw.sw(a3, s10, 12)

  if mode == MODE_READ:
    fw.addi(s6, s6, 1)
    fw.noc_reads_flushed(noc, s6, addr=t3, val=t4)
  elif mode == MODE_ATOMIC_INC:
    fw.addi(s6, s6, 1)
    fw.noc_wait_atomic_responses(noc, s6, addr=t3, val=t4)
  elif mode == MODE_NONPOSTED_WRITE:
    fw.addi(s6, s6, 1)
    fw.noc_write_barrier(noc, s6, addr=t3, val=t4)
  else:
    fw.fence()
  harness.read_wall_clock(fw, a2, a3)
  fw.sw(a2, s10, 16)
  fw.sw(a3, s10, 20)
  fw.addi(s10, s10, SENDER_SAMPLE_WORDS * 4)
  fw.addi(s8, s8, 1)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  if scounter is None:
    fw.mv(t1, zero)
  else:
    emit_counter_read(fw, noc, scounter, t1, addr=t3)
  if rcounter is None:
    fw.mv(t0, zero)
  else:
    emit_counter_read(fw, noc, rcounter, t0, addr=t3)
  fw.li(s2, RESULT_BASE)
  fw.sw(t1, s2, 11 * 4)
  fw.sw(t0, s2, 13 * 4)
  emit_status(fw, STATUS_DONE)
  return fw.ret()


def build_receiver(noc: int, mode: int, packet_bytes: int, iters: int) -> KernelBase:
  fw = DependencyKernel()
  emit_header(fw, role=ROLE_RECEIVER, status=STATUS_STARTED, noc=noc, mode=mode, packet_bytes=packet_bytes, iters=iters)
  fw.li(s10, RESULT_BASE + HEADER_SIZE)
  fw.mv(s8, zero)
  if mode == MODE_READ:
    fw.li(s2, RESULT_BASE)
    fw.sw(zero, s2, 10 * 4)
    fw.sw(zero, s2, 11 * 4)
    emit_status(fw, STATUS_DONE)
    return fw.ret()

  fw.li(s2, DST_BASE + packet_bytes - 4)
  fw.li(s1, SENTINEL_BASE if mode in WRITE_MODES else 1)
  fw.li(s0, iters)
  outer = fw._new_label("dependency_recv_outer")
  poll = fw._new_label("dependency_recv_poll")
  seen = fw._new_label("dependency_recv_seen")
  done = fw._new_label("dependency_recv_done")
  fw.label(outer)
  fw.beq(s0, zero, done)
  fw.label(poll)
  fw.lw(t1, s2, 0)
  fw.beq(t1, s1, seen)
  fw.addi(s8, s8, 1)
  fw.j(poll)
  fw.label(seen)
  harness.read_wall_clock(fw, a2, a3)
  fw.sw(a2, s10, 0)
  fw.sw(a3, s10, 4)
  fw.addi(s10, s10, RECEIVER_SAMPLE_WORDS * 4)
  fw.addi(s1, s1, 1)
  fw.addi(s0, s0, -1)
  fw.j(outer)
  fw.label(done)
  fw.li(s2, RESULT_BASE)
  fw.sw(s8, s2, 10 * 4)
  fw.sw(t1, s2, 11 * 4)
  emit_status(fw, STATUS_DONE)
  return fw.ret()


class DependencyProgram:
  def __init__(self, *, noc: int, mode: int, packet_bytes: int, iters: int,
               source: Core, target: Core, start_delay: int):
    self.noc = noc
    self.mode = mode
    self.packet_bytes = packet_bytes
    self.iters = iters
    self.source = source
    self.target = target
    self.start_delay = start_delay
    self.name = f"riscv_noc_dependency_latency:{MODE_NAMES[mode]}:noc{noc}:{source}->{target}"

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    empty = KernelBase()
    sender = build_sender(self.noc, self.mode, self.packet_bytes, self.iters, self.start_delay)
    sender.rta(lambda _x, _y: [noc_xy(*self.target)])
    receiver = build_receiver(self.noc, self.mode, self.packet_bytes, self.iters)
    sender_prog = Program(
      brisc=sender,
      ncrisc=empty,
      trisc0=empty,
      trisc1=empty,
      trisc2=empty,
      num_cores=1,
    ).layout(core_xy=self.source, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id)
    receiver_prog = Program(
      brisc=receiver,
      ncrisc=empty,
      trisc0=empty,
      trisc1=empty,
      trisc2=empty,
      num_cores=1,
    ).layout(core_xy=self.target, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id)
    target_cores = [self.source, self.target]
    reset_blob = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_RESET_READ_PTR_FROM_HOST)
    commands = [
      UnicastWrite(target_cores, TensixL1.GO_MSG, [reset_blob] * len(target_cores)),
      UnicastWrite(target_cores, TensixL1.GO_MSG_INDEX, [b"\0\0\0\0"] * len(target_cores)),
    ]
    for segment in sender_prog:
      commands.append(UnicastWrite([self.source], segment.addr, [segment.data]))
    for segment in receiver_prog:
      commands.append(UnicastWrite([self.target], segment.addr, [segment.data]))
    commands.append(Run(target_cores))
    return commands


def read_tensix_coordinate_map(device: Device) -> TensixCoordinateMap:
  layout = device.dev.telemetry_layout()
  enabled = device.dev.telemetry_tag(layout, ENABLED_TENSIX_COL_TAG)
  if enabled is None:
    raise RuntimeError("ENABLED_TENSIX_COL telemetry is unavailable")
  return tensix_coordinate_map(enabled)


def route_for_pair(source: Core, target: Core, *, noc: int, cmap: TensixCoordinateMap) -> Route:
  raw0_source = translated_tensix_to_raw_noc0(source, cmap)
  raw0_target = translated_tensix_to_raw_noc0(target, cmap)
  raw_source = raw_coord_for_noc(raw0_source, noc)
  raw_target = raw_coord_for_noc(raw0_target, noc)
  x_hops = (raw_target[0] - raw_source[0]) % GRID_W
  y_hops = (raw_target[1] - raw_source[1]) % GRID_H
  wraps = int(raw_target[0] < raw_source[0] and x_hops != 0) + int(raw_target[1] < raw_source[1] and y_hops != 0)
  return Route(
    source=source,
    target=target,
    raw0_source=raw0_source,
    raw0_target=raw0_target,
    raw_source=raw_source,
    raw_target=raw_target,
    hops=x_hops + y_hops,
    x_hops=x_hops,
    y_hops=y_hops,
    wraps=wraps,
  )


def clear_and_seed(device: Device, source: Core, target: Core, mode: int, packet_bytes: int, iters: int):
  payload = bytearray(packet_bytes)
  for off in range(0, packet_bytes, 4):
    struct.pack_into("<I", payload, off, 0xA5000000 | off)
  with harness.device_window(device, source) as win:
    win.target(source)
    win.write(RESULT_BASE, b"\0" * result_size_sender(iters))
    win.write(SRC_BASE, payload)
    win.write(DST_BASE, b"\0" * packet_bytes)
    win.target(target)
    win.write(RESULT_BASE, b"\0" * result_size_receiver(iters))
    win.write(SRC_BASE, payload)
    win.write(DST_BASE, b"\0" * packet_bytes)
  if mode == MODE_ATOMIC_INC:
    with harness.device_window(device, target) as win:
      win.write(DST_BASE + packet_bytes - 4, b"\0\0\0\0")


def read_words(device: Device, core: Core, size: int) -> tuple[int, ...]:
  with harness.device_window(device, core) as win:
    blob = win.read(RESULT_BASE, size)
  if blob and all(b == 0xFF for b in blob):
    raise RuntimeError(f"{core}: L1 readback returned all 0xff")
  return struct.unpack_from("<" + "I" * (size // 4), blob, 0)


def parse_run_result(device: Device, *, noc: int, mode: int, source: Core, target: Core,
                     route: Route, packet_bytes: int, iters: int) -> RunResult:
  sender = read_words(device, source, result_size_sender(iters))
  receiver = read_words(device, target, result_size_receiver(iters))
  for core, words, role in ((source, sender, ROLE_SENDER), (target, receiver, ROLE_RECEIVER)):
    if words[0] != RESULT_MAGIC:
      raise RuntimeError(f"{core}: bad result magic 0x{words[0]:08x}")
    if words[1] != role:
      raise RuntimeError(f"{core}: bad role {words[1]}")
    if words[2] != STATUS_DONE:
      raise RuntimeError(f"{core}: benchmark did not finish, status=0x{words[2]:08x}")
    if words[3] != noc or words[4] != mode or words[5] != packet_bytes or words[6] != iters:
      raise RuntimeError(f"{core}: result header mismatch {words[:7]}")
  sender_issue = []
  sender_sent = []
  sender_done = []
  receiver_seen = []
  for i in range(iters):
    base = HEADER_WORDS + i * SENDER_SAMPLE_WORDS
    sender_issue.append(u64(sender[base], sender[base + 1]))
    sender_sent.append(u64(sender[base + 2], sender[base + 3]))
    sender_done.append(u64(sender[base + 4], sender[base + 5]))
    rbase = HEADER_WORDS + i * RECEIVER_SAMPLE_WORDS
    receiver_seen.append(u64(receiver[rbase], receiver[rbase + 1]))
  return RunResult(
    noc=noc,
    mode=mode,
    source=source,
    target=target,
    route=route,
    packet_bytes=packet_bytes,
    iters=iters,
    sent_counter_delta=(sender[11] - sender[10]) & 0xFFFFFFFF,
    response_counter_delta=(sender[13] - sender[12]) & 0xFFFFFFFF,
    receiver_poll_iters=receiver[10],
    receiver_final=receiver[11],
    sender_issue=sender_issue,
    sender_sent=sender_sent,
    sender_done=sender_done,
    receiver_seen=receiver_seen,
  )


def summarize_values(values: list[int]) -> str:
  if not values:
    return "n/a"
  return (
    f"min={min(values)} avg={statistics.fmean(values):.3f} "
    f"med={statistics.median(values):.3f} max={max(values)}"
  )


def format_results(results: list[RunResult]) -> str:
  lines = [
    "| mode | noc | source | target | raw noc route | hops | bytes | iters | sent-issue cyc | done-issue cyc | seen-issue cyc | seen-done cyc | sent ctr | resp ctr | recv polls | recv final |",
    "|---|---:|---|---|---|---:|---:|---:|---|---|---|---|---:|---:|---:|---:|",
  ]
  for r in results:
    route = r.route
    lines.append(
      f"| {MODE_NAMES[r.mode]} | {r.noc} | `{r.source[0]},{r.source[1]}` | `{r.target[0]},{r.target[1]}` | "
      f"`{route.raw_source[0]},{route.raw_source[1]}->{route.raw_target[0]},{route.raw_target[1]}` | "
      f"{route.hops} | {r.packet_bytes} | {r.iters} | {summarize_values(r.sent_minus_issue)} | "
      f"{summarize_values(r.done_minus_issue)} | {summarize_values(r.seen_minus_issue)} | "
      f"{summarize_values(r.seen_minus_done)} | {r.sent_counter_delta} | {r.response_counter_delta} | "
      f"{r.receiver_poll_iters} | 0x{r.receiver_final:08x} |"
    )
  return "\n".join(lines)


def format_coordinate_map(cmap: TensixCoordinateMap) -> str:
  live = ", ".join(f"{tx}->{cmap.translated_to_raw_x[tx]}" for tx in cmap.translated_live_x)
  hidden = ", ".join(f"{tx}->{raw}" for tx, raw in sorted(cmap.translated_harvested_to_raw_x.items()))
  lines = [
    f"ENABLED_TENSIX_COL: `0x{cmap.enabled_tensix_col:08x}`",
    f"Live raw Tensix columns: `{list(cmap.live_raw_x)}`",
    f"Harvested raw Tensix columns: `{list(cmap.harvested_raw_x)}`",
    f"Translated live x -> raw NoC0 x: `{live}`",
  ]
  if hidden:
    lines.append(f"Translated hidden x -> harvested raw NoC0 x: `{hidden}`")
  return "\n".join(lines)


def default_pairs() -> list[tuple[Core, Core]]:
  return [((1, 2), (2, 2)), ((1, 2), (14, 2)), ((1, 2), (1, 3)), ((1, 2), (1, 11)), ((1, 2), (14, 11))]


def packet_sizes_for_mode(mode: int, sizes: tuple[int, ...]) -> tuple[int, ...]:
  return (4,) if mode == MODE_ATOMIC_INC else sizes


def append_report(path: Path, *, args, cmap: TensixCoordinateMap, results: list[RunResult]):
  harness.append_report(path, "NoC dependency latency", [
    f"NoCs: `{','.join(str(noc) for noc in args.nocs)}`",
    f"Modes: `{','.join(MODE_NAMES[mode] for mode in args.modes)}`",
    f"Sizes: `{','.join(str(size) for size in args.sizes)}` bytes; atomic_inc is fixed 4-byte request/response",
    f"Iters: `{args.iters}`",
    f"Pairs: `{';'.join(f'{a[0]},{a[1]}:{b[0]},{b[1]}' for a, b in ([args.pair] if args.pair else default_pairs()))}`",
    "Traffic: one source issues one dependency-forming transaction per iteration while the target polls for receiver-visible modes.",
    "Read rows report sender-side response flush only; NoC slave read service has no receiver-side counter in this harness.",
    "Full matrix command: `python3 microbenching/noc/riscv_noc_dependency_latency.py --nocs 0,1 --modes posted_write,nonposted_write,read_flush,atomic_inc --sizes 4,16,64,256,4096,16384 --iters 16`",
    format_coordinate_map(cmap),
  ], format_results(results))


def validate_args(args):
  if args.iters <= 0:
    raise ValueError("--iters must be positive")
  if args.start_delay < 0:
    raise ValueError("--start-delay must be non-negative")
  if MODE_ATOMIC_INC in args.modes and args.iters > 31:
    raise ValueError("--iters must be <=31 when atomic_inc is selected because the semaphore increment wraps at 31")
  for source, target in ([args.pair] if args.pair else default_pairs()):
    if source == target:
      raise ValueError("source and target must be distinct cores")


def main() -> None:
  parser = argparse.ArgumentParser(description="Blackhole NoC dependency latency decomposition with sender and receiver timestamps.")
  parser.add_argument("--nocs", type=hop_sweep.parse_nocs, default=(0, 1))
  parser.add_argument("--modes", type=parse_modes, default=parse_modes("posted_write,nonposted_write,read_flush,atomic_inc"))
  parser.add_argument("--pair", type=parse_pair, default=None, help="translated worker pair X,Y:X,Y")
  parser.add_argument("--sizes", type=parse_sizes, default=parse_sizes("4,16,64,256,4096,16384"))
  parser.add_argument("--iters", type=int, default=16)
  parser.add_argument("--start-delay", type=int, default=4096, help="sender delay before first packet so receiver is polling")
  parser.add_argument("--dry-run", action="store_true", help="print selected matrix without opening the device")
  parser.add_argument("--no-report", action="store_true", help="do not append docs/noc/noc-dependency-latency.md")
  parser.add_argument("--report", type=Path, default=harness.doc_path("noc", "noc-dependency-latency.md"))
  args = parser.parse_args()
  validate_args(args)

  pairs = [args.pair] if args.pair is not None else default_pairs()
  if args.dry_run:
    for source, target in pairs:
      for noc in args.nocs:
        for mode in args.modes:
          print(
            f"dry-run pair={source[0]},{source[1]}:{target[0]},{target[1]} noc={noc} "
            f"mode={MODE_NAMES[mode]} sizes={','.join(str(size) for size in packet_sizes_for_mode(mode, args.sizes))}"
          )
    return

  results: list[RunResult] = []
  with harness.open_device() as device:
    core_set = set(device.cores)
    cmap = read_tensix_coordinate_map(device)
    for source, target in pairs:
      if source not in core_set or target not in core_set:
        raise ValueError(f"pair {source}->{target} must use program cores")
      for noc in args.nocs:
        route = route_for_pair(source, target, noc=noc, cmap=cmap)
        for mode in args.modes:
          for packet_bytes in packet_sizes_for_mode(mode, args.sizes):
            clear_and_seed(device, source, target, mode, packet_bytes, args.iters)
            device.run(DependencyProgram(
              noc=noc,
              mode=mode,
              packet_bytes=packet_bytes,
              iters=args.iters,
              source=source,
              target=target,
              start_delay=args.start_delay,
            ))
            results.append(parse_run_result(
              device,
              noc=noc,
              mode=mode,
              source=source,
              target=target,
              route=route,
              packet_bytes=packet_bytes,
              iters=args.iters,
            ))

  print(format_coordinate_map(cmap))
  print()
  table = format_results(results)
  print(table)
  if not args.no_report:
    append_report(args.report, args=args, cmap=cmap, results=results)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
