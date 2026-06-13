#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as _dt
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402  (does sys.path + TT_USB bootstrap on import)
from asm import KernelBase
from device import Device
from dsl import a2, a3, a4, a5, s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, t0, t1, t3, t4, t5, t6, zero
from program import DevMsgs, Program, Run, UnicastWrite
from ttk.addrs import Core, noc_xy
from ttk.mailbox import BriscMailbox as BM
from ttk.noc import NOC, Noc
from ttk.tensix import TensixL1

try:
  import noc_topology as _topology
except ImportError:
  _topology = None


RESULT_BASE = 0x150000
GATE_BASE = RESULT_BASE + 0x100
STREAM_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
HEADER_WORDS = 16
RESULT_MAGIC = 0x52544F50  # "RTOP"
STATUS_STARTED = 0x70000001
STATUS_DONE = 0x7000D00D
ROLE_SENDER = 1
ROLE_RECEIVER = 2
ROLE_CLOCK = 3

NOC_GRID_W = 20
NOC_GRID_H = 25
P100_WORKER_X = (*range(1, 8), *range(10, 15))
P100_WORKER_Y = tuple(range(2, 12))
P100_WORKER_CORES = [(x, y) for y in P100_WORKER_Y for x in P100_WORKER_X]


@dataclass(frozen=True)
class Stream:
  name: str
  source: Core
  target: Core
  noc: int


@dataclass(frozen=True)
class Scenario:
  experiment: str
  name: str
  streams: tuple[Stream, ...]
  note: str


@dataclass(frozen=True)
class CoreResult:
  core: Core
  words: tuple[int, ...]

  @property
  def role(self) -> int:
    return self.words[1]

  @property
  def status(self) -> int:
    return self.words[2]

  @property
  def start(self) -> int:
    return u64(self.words[8], self.words[9])

  @property
  def end(self) -> int:
    return u64(self.words[10], self.words[11])

  @property
  def counter_delta(self) -> int:
    return (self.words[13] - self.words[12]) & 0xFFFFFFFF

  @property
  def sentinel(self) -> int:
    return self.words[11]


@dataclass(frozen=True)
class StreamResult:
  scenario: Scenario
  stream: Stream
  sender: CoreResult
  receiver: CoreResult
  stream_bytes: int
  repeats: int
  hops_xy: int
  hops_yx: int

  @property
  def total_bytes(self) -> int:
    return self.stream_bytes * self.repeats

  @property
  def cycles(self) -> int:
    return (self.sender.end - self.sender.start) & ((1 << 64) - 1)

  @property
  def bytes_per_cycle(self) -> float:
    return self.total_bytes / self.cycles if self.cycles > 0 else 0.0


class TopologyKernel(KernelBase, Noc):
  pass


def u64(lo: int, hi: int) -> int:
  return lo | (hi << 32)


def result_size() -> int:
  return HEADER_WORDS * 4


def expected_sentinel(stream_bytes: int) -> int:
  return 0xA5000000 | ((stream_bytes - 4) % NOC.MAX_BURST_SIZE)


def emit_header(fw: KernelBase, *, role: int, status: int, noc: int, stream_bytes: int, repeats: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, role, status, noc, stream_bytes, repeats,
    NOC.MAX_BURST_SIZE, expected_sentinel(stream_bytes) if stream_bytes else 0,
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


def emit_gate_wait(fw: TopologyKernel):
  fw.li(t5, GATE_BASE)
  fw.lw(s0, t5, 0)
  fw.lw(s1, t5, 4)
  loop = fw._new_label("gate_wait")
  done = fw._new_label("gate_done")
  fw.label(loop)
  harness.read_wall_clock(fw, a2, a3)
  fw.bltu(a3, s1, loop)
  fw.bltu(s1, a3, done)
  fw.bltu(a2, s0, loop)
  fw.label(done)
  return fw


def build_sender(noc: int, stream_bytes: int, repeats: int) -> KernelBase:
  chunks = stream_bytes // NOC.MAX_BURST_SIZE
  fw = TopologyKernel()
  emit_header(fw, role=ROLE_SENDER, status=STATUS_STARTED, noc=noc, stream_bytes=stream_bytes, repeats=repeats)
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s9,))
  fw.local_noc0_coord(s5, x_addr=BM.MY_X, y_addr=BM.MY_Y)
  fw.li(s4, NOC.MAX_BURST_SIZE)
  fw.li(s8, NOC.MAX_BURST_SIZE)
  emit_counter_read(fw, noc, NOC.NIU_MST_WR_ACK_RECEIVED, s7)
  fw.mv(s6, s7)

  emit_gate_wait(fw)
  harness.read_wall_clock(fw, a2, a3)
  fw.li(t6, repeats)
  outer = fw._new_label("sender_outer")
  outer_done = fw._new_label("sender_outer_done")
  fw.label(outer)
  fw.beq(t6, zero, outer_done)
  fw.li(s2, STREAM_BASE)
  fw.li(s3, STREAM_BASE)
  fw.li(s0, chunks)
  inner = fw._new_label("sender_inner")
  inner_done = fw._new_label("sender_inner_done")
  fw.label(inner)
  fw.beq(s0, zero, inner_done)
  fw.noc_write(noc, 0, s2, s3, 0, s9, s4, posted=False, a=t3, v=t4)
  fw.addi(s6, s6, 1)
  fw.add(s2, s2, s8)
  fw.add(s3, s3, s8)
  fw.addi(s0, s0, -1)
  fw.j(inner)
  fw.label(inner_done)
  fw.addi(t6, t6, -1)
  fw.j(outer)
  fw.label(outer_done)
  fw.noc_write_barrier(noc, s6, addr=t3, val=t4)
  harness.read_wall_clock(fw, a4, a5)
  emit_counter_read(fw, noc, NOC.NIU_MST_WR_ACK_RECEIVED, s8)

  fw.li(s2, RESULT_BASE)
  for off, reg in enumerate((a2, a3, a4, a5, s7, s8), start=8):
    fw.sw(reg, s2, off * 4)
  emit_status(fw, STATUS_DONE)
  return fw.ret()


def build_receiver(noc: int, stream_bytes: int, repeats: int) -> KernelBase:
  fw = TopologyKernel()
  emit_header(fw, role=ROLE_RECEIVER, status=STATUS_STARTED, noc=noc, stream_bytes=stream_bytes, repeats=repeats)
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
  harness.read_wall_clock(fw, a2, a3)
  fw.li(s2, RESULT_BASE)
  fw.sw(a2, s2, 8 * 4)
  fw.sw(a3, s2, 9 * 4)
  fw.sw(s0, s2, 10 * 4)
  fw.sw(t1, s2, 11 * 4)
  emit_status(fw, STATUS_DONE)
  return fw.ret()


def build_clock_kernel() -> KernelBase:
  fw = TopologyKernel()
  emit_header(fw, role=ROLE_CLOCK, status=STATUS_STARTED, noc=0, stream_bytes=0, repeats=0)
  harness.read_wall_clock(fw, a2, a3)
  fw.li(s2, RESULT_BASE)
  fw.sw(a2, s2, 8 * 4)
  fw.sw(a3, s2, 9 * 4)
  emit_status(fw, STATUS_DONE)
  return fw.ret()


def _single_core_segments(core: Core, kernel: KernelBase, *, dispatch_mode: int, host_assigned_id: int):
  empty = KernelBase()
  return Program(
    brisc=kernel,
    ncrisc=empty,
    trisc0=empty,
    trisc1=empty,
    trisc2=empty,
    num_cores=1,
  ).layout(core_xy=core, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id)


class TopologyProgram:
  def __init__(self, scenario: Scenario, *, stream_bytes: int, repeats: int):
    self.scenario = scenario
    self.stream_bytes = stream_bytes
    self.repeats = repeats
    self.name = f"riscv_noc_topology_probe:{scenario.experiment}:{scenario.name}"

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    source_map = {stream.source: stream for stream in self.scenario.streams}
    target_map = {stream.target: stream for stream in self.scenario.streams}
    overlap = set(source_map) & set(target_map)
    if overlap:
      raise ValueError(f"source/target overlap is unsupported in one scenario: {sorted(overlap)}")
    if len(source_map) != len(self.scenario.streams):
      raise ValueError("duplicate stream sources are unsupported")
    if len(target_map) != len(self.scenario.streams):
      raise ValueError("duplicate stream targets are unsupported")

    target_cores = sorted(set(source_map) | set(target_map), key=lambda c: (c[1], c[0]))
    per_core_segments = {}
    for core in target_cores:
      if core in source_map:
        stream = source_map[core]
        kernel = build_sender(stream.noc, self.stream_bytes, self.repeats)
        kernel.rta(lambda _x, _y, target=stream.target: [noc_xy(*target)])
      else:
        stream = target_map[core]
        kernel = build_receiver(stream.noc, self.stream_bytes, self.repeats)
      per_core_segments[core] = _single_core_segments(
        core,
        kernel,
        dispatch_mode=dispatch_mode,
        host_assigned_id=host_assigned_id,
      )

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


class ClockProgram:
  def __init__(self, cores: list[Core]):
    self.cores = list(cores)
    self.name = "riscv_noc_topology_probe:clock"

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    target_cores = sorted(set(self.cores), key=lambda c: (c[1], c[0]))
    kernel = build_clock_kernel()
    per_core_segments = {
      core: _single_core_segments(core, kernel, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id)
      for core in target_cores
    }
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


if _topology is not None and hasattr(_topology, "shared_links"):
  noc_path = _topology.noc_path
  noc_hops = _topology.noc_hops
  shared_links = _topology.shared_links
else:
  # DEDUPE: shares logic with noc_topology.py
  def _axis_nodes(start: int, stop: int, *, size: int, step: int) -> list[int]:
    values = [start]
    cur = start
    while cur != stop:
      cur = (cur + step) % size
      values.append(cur)
    return values

  def noc_path(src_xy: Core, dst_xy: Core, noc: int, *, dimension_order: str = "xy", torus: bool = True) -> list[Core]:
    if noc not in (0, 1):
      raise ValueError("noc must be 0 or 1")
    if dimension_order not in ("xy", "yx"):
      raise ValueError("dimension_order must be 'xy' or 'yx'")
    if not torus:
      raise NotImplementedError("non-torus path modeling is intentionally reported by failed/worse probes")

    step = 1 if noc == 0 else -1
    x0, y0 = src_xy
    x1, y1 = dst_xy
    path = [src_xy]
    for axis in dimension_order:
      x, y = path[-1]
      if axis == "x":
        for x_next in _axis_nodes(x, x1, size=NOC_GRID_W, step=step)[1:]:
          path.append((x_next, y))
      else:
        for y_next in _axis_nodes(y, y1, size=NOC_GRID_H, step=step)[1:]:
          path.append((x, y_next))
    return path

  def noc_hops(src_xy: Core, dst_xy: Core, noc: int, *, dimension_order: str = "xy", torus: bool = True) -> int:
    return len(noc_path(src_xy, dst_xy, noc, dimension_order=dimension_order, torus=torus)) - 1

  def _links(path: list[Core]) -> set[tuple[Core, Core]]:
    return set(zip(path, path[1:]))

  def shared_links(a: tuple[Core, Core, int], b: tuple[Core, Core, int], *, dimension_order: str = "xy") -> set[tuple[Core, Core]]:
    return _links(noc_path(a[0], a[1], a[2], dimension_order=dimension_order)) & _links(noc_path(b[0], b[1], b[2], dimension_order=dimension_order))


def parse_core(text: str) -> Core:
  return harness.parse_core(text)


def parse_experiments(text: str) -> tuple[str, ...]:
  items = tuple(item.strip().upper() for item in text.split(",") if item.strip())
  if not items:
    raise argparse.ArgumentTypeError("expected C, D, or C,D")
  bad = [item for item in items if item not in ("C", "D")]
  if bad:
    raise argparse.ArgumentTypeError(f"unknown experiment(s): {', '.join(bad)}")
  return items


def parse_start_time(words: tuple[int, ...]) -> int:
  if words[0] != RESULT_MAGIC or words[1] != ROLE_CLOCK or words[2] != STATUS_DONE:
    raise RuntimeError(f"bad clock result header: {words[:4]}")
  return u64(words[8], words[9])


def validate_stream_bytes(stream_bytes: int):
  if stream_bytes <= 0 or stream_bytes % NOC.MAX_BURST_SIZE:
    raise ValueError("--bytes must be a positive multiple of 16 KiB")
  if stream_bytes > RESULT_BASE - STREAM_BASE:
    raise ValueError(f"--bytes must fit below result range; max is {RESULT_BASE - STREAM_BASE}")


def scenario_cores(scenario: Scenario) -> list[Core]:
  return sorted({core for stream in scenario.streams for core in (stream.source, stream.target)}, key=lambda c: (c[1], c[0]))


def default_c_scenarios(cores: list[Core]) -> list[Scenario]:
  core_set = set(cores)
  for y in P100_WORKER_Y:
    needed = {(14, y), (1, y), (7, y)}
    if needed <= core_set:
      return [
        Scenario(
          "C",
          "noc0_wrap_high_to_low",
          (Stream("wrap_wrong_direction", (14, y), (1, y), 0),),
          "NoC0 high-x to low-x; a fast result means the ascending ring wraps.",
        ),
        Scenario(
          "C",
          "noc0_forward_same_hops",
          (Stream("forward_reference", (7, y), (14, y), 0),),
          "Same-row NoC0 forward reference with the same modeled 7-hop distance.",
        ),
        Scenario(
          "C",
          "noc1_high_to_low",
          (Stream("noc1_directional_reference", (14, y), (1, y), 1),),
          "NoC1 direction-compatible high-x to low-x endpoint reference.",
        ),
      ]
  raise ValueError("default Experiment C placement needs cores (1,y), (7,y), and (14,y)")


def default_d_scenarios(cores: list[Core], *, noc: int) -> list[Scenario]:
  needed = {(1, 2), (4, 5), (2, 2), (5, 2), (1, 3), (1, 6)}
  if not needed <= set(cores):
    raise ValueError("default Experiment D placement needs cores (1,2), (4,5), (2,2), (5,2), (1,3), and (1,6)")
  victim = Stream("diagonal_victim", (1, 2), (4, 5), noc)
  x_cross = Stream("x_leg_cross", (2, 2), (5, 2), noc)
  y_cross = Stream("y_leg_cross", (1, 3), (1, 6), noc)
  return [
    Scenario(
      "D",
      "diagonal_baseline",
      (victim,),
      "Diagonal victim alone.",
    ),
    Scenario(
      "D",
      "cross_source_row_x_leg",
      (victim, x_cross),
      "Crossing stream on the source-row X leg; slowdown points to X-then-Y routing.",
    ),
    Scenario(
      "D",
      "cross_source_col_y_leg",
      (victim, y_cross),
      "Crossing stream on the source-column Y leg; slowdown points to Y-then-X routing.",
    ),
  ]


def build_scenarios(args, cores: list[Core]) -> list[Scenario]:
  scenarios: list[Scenario] = []
  if "C" in args.experiments:
    scenarios.extend(default_c_scenarios(cores))
  if "D" in args.experiments:
    scenarios.extend(default_d_scenarios(cores, noc=args.d_noc))
  return scenarios


def seed_blob(stream_bytes: int) -> bytes:
  seed = bytearray(NOC.MAX_BURST_SIZE)
  for off in range(0, len(seed), 4):
    struct.pack_into("<I", seed, off, 0xA5000000 | off)
  return bytes(seed) * (stream_bytes // NOC.MAX_BURST_SIZE)


def clear_and_seed(device: Device, scenario: Scenario, *, stream_bytes: int, gate_time: int):
  payload = seed_blob(stream_bytes)
  threshold = struct.pack("<II", gate_time & 0xFFFFFFFF, (gate_time >> 32) & 0xFFFFFFFF)
  with harness.device_window(device, scenario_cores(scenario)[0]) as win:
    for stream in scenario.streams:
      win.target(stream.source)
      win.write(RESULT_BASE, b"\0" * result_size())
      win.write(GATE_BASE, threshold)
      win.write(STREAM_BASE, payload)
      win.target(stream.target)
      win.write(RESULT_BASE, b"\0" * result_size())
      win.write(STREAM_BASE, b"\0" * stream_bytes)


def read_result(device: Device, core: Core) -> CoreResult:
  with harness.device_window(device, core) as win:
    blob = win.read(RESULT_BASE, result_size())
  if blob and all(b == 0xFF for b in blob):
    raise RuntimeError(f"{core}: L1 readback returned all 0xff")
  words = struct.unpack_from("<" + "I" * HEADER_WORDS, blob, 0)
  if words[0] != RESULT_MAGIC:
    raise RuntimeError(f"{core}: bad result magic 0x{words[0]:08x}")
  if words[2] != STATUS_DONE:
    raise RuntimeError(f"{core}: benchmark did not finish, status=0x{words[2]:08x}")
  return CoreResult(core, words)


def read_clock_result(device: Device, core: Core) -> int:
  return parse_start_time(read_result(device, core).words)


def sample_gate_time(device: Device, cores: list[Core], gate_cycles: int) -> int:
  with harness.device_window(device, cores[0]) as win:
    for core in cores:
      win.target(core)
      win.write(RESULT_BASE, b"\0" * result_size())
  device.run(ClockProgram(cores))
  now = max(read_clock_result(device, core) for core in cores)
  return now + gate_cycles


def run_scenario(device: Device, scenario: Scenario, *, stream_bytes: int, repeats: int, gate_cycles: int) -> list[StreamResult]:
  cores = scenario_cores(scenario)
  gate_time = sample_gate_time(device, cores, gate_cycles) if gate_cycles > 0 else 0
  clear_and_seed(device, scenario, stream_bytes=stream_bytes, gate_time=gate_time)
  device.run(TopologyProgram(scenario, stream_bytes=stream_bytes, repeats=repeats))
  out = []
  for stream in scenario.streams:
    sender = read_result(device, stream.source)
    receiver = read_result(device, stream.target)
    out.append(StreamResult(
      scenario=scenario,
      stream=stream,
      sender=sender,
      receiver=receiver,
      stream_bytes=stream_bytes,
      repeats=repeats,
      hops_xy=noc_hops(stream.source, stream.target, stream.noc, dimension_order="xy"),
      hops_yx=noc_hops(stream.source, stream.target, stream.noc, dimension_order="yx"),
    ))
  return out


def dry_run(scenarios: list[Scenario], *, stream_bytes: int, repeats: int) -> str:
  lines = ["dry-run program lowering:"]
  for scenario in scenarios:
    commands = TopologyProgram(scenario, stream_bytes=stream_bytes, repeats=repeats).lower(scenario_cores(scenario))
    lines.append(f"- {scenario.experiment}/{scenario.name}: {len(scenario.streams)} stream(s), {len(commands)} IR commands")
  return "\n".join(lines)


def result_table(results: list[StreamResult]) -> str:
  lines = [
    "| exp | scenario | stream | noc | source | target | hops xy/yx | total KiB | cycles | B/cyc | ack chunks | recv sentinel |",
    "|---|---|---|---:|---|---|---:|---:|---:|---:|---:|---:|",
  ]
  for result in results:
    lines.append(
      f"| {result.scenario.experiment} | {result.scenario.name} | {result.stream.name} | {result.stream.noc} | "
      f"`{result.stream.source[0]},{result.stream.source[1]}` | `{result.stream.target[0]},{result.stream.target[1]}` | "
      f"{result.hops_xy}/{result.hops_yx} | {result.total_bytes / 1024:.1f} | {result.cycles} | "
      f"{result.bytes_per_cycle:.3f} | {result.sender.counter_delta} | 0x{result.receiver.sentinel:08x} |"
    )
  return "\n".join(lines)


def interpret(results: list[StreamResult]) -> list[str]:
  lines = []
  by_scenario = {result.scenario.name: result for result in results if result.stream.name == "diagonal_victim"}
  wrap = next((r for r in results if r.scenario.name == "noc0_wrap_high_to_low"), None)
  forward = next((r for r in results if r.scenario.name == "noc0_forward_same_hops"), None)
  noc1 = next((r for r in results if r.scenario.name == "noc1_high_to_low"), None)
  if wrap and forward:
    ratio = wrap.bytes_per_cycle / forward.bytes_per_cycle if forward.bytes_per_cycle else 0.0
    lines.append(f"- Experiment C: NoC0 wrap/reference bandwidth ratio is `{ratio:.3f}`.")
    if ratio >= 0.75:
      lines.append("- Experiment C interpretation: high-x to low-x behaves like the short forward path, consistent with a real wrap link.")
    elif noc1 and noc1.bytes_per_cycle > wrap.bytes_per_cycle * 1.5:
      lines.append("- Experiment C interpretation: NoC1 is much healthier than the NoC0 backward probe, consistent with mesh-like directionality.")
    else:
      lines.append("- Experiment C interpretation: inconclusive; rerun with larger byte counts or inspect for hangs/timeouts.")

  base = by_scenario.get("diagonal_baseline")
  x_case = by_scenario.get("cross_source_row_x_leg")
  y_case = by_scenario.get("cross_source_col_y_leg")
  if base and x_case and y_case:
    x_ratio = x_case.bytes_per_cycle / base.bytes_per_cycle if base.bytes_per_cycle else 0.0
    y_ratio = y_case.bytes_per_cycle / base.bytes_per_cycle if base.bytes_per_cycle else 0.0
    lines.append(f"- Experiment D: victim bandwidth ratios vs baseline are X-leg `{x_ratio:.3f}`, Y-leg `{y_ratio:.3f}`.")
    if x_ratio < y_ratio * 0.85:
      lines.append("- Experiment D interpretation: source-row X crossing interferes more, consistent with X-then-Y routing.")
    elif y_ratio < x_ratio * 0.85:
      lines.append("- Experiment D interpretation: source-column Y crossing interferes more, consistent with Y-then-X routing.")
    else:
      lines.append("- Experiment D interpretation: inconclusive; crossing streams did not separate strongly.")
  return lines


def append_report(path: Path, *, args, scenarios: list[Scenario], results: list[StreamResult]):
  now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
  with path.open("a", encoding="utf-8") as f:
    f.write(f"\n## Run {now}\n\n")
    f.write(f"- Experiments: `{','.join(args.experiments)}`\n")
    f.write(f"- Bytes per repeat: `{args.bytes}`\n")
    f.write(f"- Repeats: `{args.repeats}`\n")
    f.write(f"- Gate cycles: `{args.gate_cycles}`\n")
    f.write("- Traffic: BRISC nonposted L1-to-L1 unicast writes, 16 KiB chunks, sender wall-clock plus NIU write-ack counters\n")
    f.write("- Path labels: local model assumes NoC0 ascending/right/down, NoC1 descending/left/up, 20x25 torus, and reports `xy/yx` hop counts\n\n")
    for scenario in scenarios:
      f.write(f"- `{scenario.experiment}/{scenario.name}`: {scenario.note}\n")
    f.write("\n")
    f.write(result_table(results))
    f.write("\n\n")
    for line in interpret(results):
      f.write(line)
      f.write("\n")


def main():
  parser = argparse.ArgumentParser(description="Probe Blackhole NoC torus wrapping and routing dimension order.")
  parser.add_argument("--experiments", type=parse_experiments, default=("C", "D"), help="comma-separated subset: C,D")
  parser.add_argument("--d-noc", type=int, choices=(0, 1), default=0, help="NoC instance for Experiment D")
  parser.add_argument("--bytes", type=int, default=256 * 1024, help="bytes per stream repeat; multiple of 16 KiB")
  parser.add_argument("--repeats", type=int, default=4, help="stream repeats per scenario")
  parser.add_argument("--gate-cycles", type=int, default=200_000_000, help="future wall-clock offset for sender start gate; 0 disables")
  parser.add_argument("--dry-run", action="store_true", help="build/lower programs without opening hardware")
  parser.add_argument("--no-report", action="store_true", help="do not append microbenching/docs/noc-topology.md")
  parser.add_argument("--report", type=Path, default=harness.doc_path("noc", "noc-topology.md"), help="markdown report path")
  args = parser.parse_args()
  validate_stream_bytes(args.bytes)
  if args.repeats <= 0:
    raise ValueError("--repeats must be positive")
  if args.gate_cycles < 0:
    raise ValueError("--gate-cycles must be nonnegative")

  if args.dry_run:
    scenarios = build_scenarios(args, P100_WORKER_CORES)
    print(dry_run(scenarios, stream_bytes=args.bytes, repeats=args.repeats))
    return

  results: list[StreamResult] = []
  with harness.open_device() as device:
    scenarios = build_scenarios(args, device.cores)
    for scenario in scenarios:
      results.extend(run_scenario(
        device,
        scenario,
        stream_bytes=args.bytes,
        repeats=args.repeats,
        gate_cycles=args.gate_cycles,
      ))

  print(result_table(results))
  for line in interpret(results):
    print(line)
  if not args.no_report:
    append_report(args.report, args=args, scenarios=scenarios, results=results)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
