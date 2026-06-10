#!/usr/bin/env python3
from __future__ import annotations

import sys as _bs_sys
from pathlib import Path as _bs_Path
_bs_sys.path.insert(0, str(_bs_Path(__file__).resolve().parents[1]))
import _bench_path  # noqa: F401
import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
  sys.path.insert(0, str(Path(__file__).resolve().parent))

import dsl
import matmul_peak as matmul
import matmul_peak_drisc as matmul_drisc

from asm import KernelBase
from pcie import P100_TENSIX_X
from program import Program, ROLE_INDEX


Core = tuple[int, int]

AICLK_MHZ = 1350.0
RISC_CPI = 1.0
TENSIX_ISSUE_CPI = 1.25
MMIO_CPI = 2.0
DRISC_DMA_GBPS = 59.6
DRISC_GDDR_READ_GBPS = 59.4
DRISC_GDDR_WRITE_GBPS = 64.0
PEER_L1_STREAM_BPC = 64.0
DRAM_WRITE_GBPS = 245.7
NOC_MCAST_16K_BPC = 30.752
NOC_SEM_MCAST_CYCLES = 103.375
NOC_SEM_INC_ACK_CYCLES = 213.750
NOC_MIXED_RWM_16K_CYCLES = 607.625
MATH_OUTPUT_TILE_K_THROTTLE0_CYCLES = 49.0
MATH_OUTPUT_TILE_K_UNTHROTTLED_CYCLES = 54.0
MATH_MVMUL_ENCODED_SLOTS_PER_TILE_K = 16.0
MATH_MVMUL_ARCH_PRODUCTS_PER_TILE_K = 8.0
MATH_MVMUL_TILE_ISSUE_CYCLES = 19.0
MATH_MVMUL_TILE_LATENCY_CYCLES = 90.0
MATH_MVMUL_TILE_THROUGHPUT_CYCLES = 147.0
MATH_MVMUL_2X2_ISSUE_CYCLES = 32.0
MATH_MVMUL_2X2_LATENCY_CYCLES = 187.0
MATH_MVMUL_2X2_THROUGHPUT_CYCLES = 244.0
UNPACK_STEADY_ROW_CYCLES = 37.5
UNPACK_2X2_BW6_CYCLES = 487.4
UNPACK_RELOAD_2X2_CYCLES = 273.9
CB_WAIT_FRONT_READY_CYCLES = 22.0
CB_RESERVE_BACK_READY_CYCLES = 23.0
CB_PUSH_BACK_CYCLES = 31.0
CB_POP_FRONT_CYCLES = 31.5
TTSEMWAIT_READY_SYNC_CYCLES = 8.0
WORKER_STATEFUL_OUTPUT_WRITE_2K_CYCLES = 37.5
TRISC_CYCLES_PER_SUBBLOCK = 924.0
OUTPUT_TAIL_US = 60.0


@dataclass
class KernelStatic:
  text_words: int = 0
  rv_words: int = 0
  tensix_words: int = 0
  mmio_lw: int = 0
  mmio_sw: int = 0
  tensix_ops: dict[str, int] = field(default_factory=dict)

  @property
  def issue_cycles(self) -> float:
    rv = self.rv_words * RISC_CPI
    tt = self.tensix_words * TENSIX_ISSUE_CPI
    mmio = (self.mmio_lw + self.mmio_sw) * MMIO_CPI
    return rv + tt + mmio


@dataclass
class RoleEstimate:
  role: str
  static_cycles: float
  dynamic_cycles: float
  notes: list[str] = field(default_factory=list)

  @property
  def cycles(self) -> float:
    return max(self.static_cycles, self.dynamic_cycles)


@dataclass
class CoreEstimate:
  core: Core
  roles: dict[str, RoleEstimate]

  @property
  def cycles(self) -> float:
    return max((role.cycles for role in self.roles.values()), default=0.0)

  @property
  def bottleneck(self) -> str:
    if not self.roles:
      return ""
    return max(self.roles.values(), key=lambda role: role.cycles).role


@dataclass
class ProgramEstimate:
  kind: str
  cores: list[CoreEstimate]
  summary: list[str] = field(default_factory=list)

  @property
  def cycles(self) -> float:
    return max((core.cycles for core in self.cores), default=0.0)

  def print(self, *, aiclk_mhz: float = AICLK_MHZ, limit: int | None = None) -> None:
    print(f"Program timing estimate ({self.kind})")
    for line in self.summary:
      print(f"  {line}")
    print(f"  estimated wall: {self.cycles / aiclk_mhz:.1f} us")
    rows = self.cores if limit is None else self.cores[:limit]
    print("  per-core:")
    for core in rows:
      parts = " ".join(
        f"{role}={estimate.cycles / aiclk_mhz:.1f}us"
        for role, estimate in core.roles.items()
      )
      print(f"    {core.core}: wall={core.cycles / aiclk_mhz:.1f}us bottleneck={core.bottleneck} {parts}")
    if limit is not None and len(self.cores) > limit:
      print(f"    ... {len(self.cores) - limit} more cores")


@dataclass(frozen=True)
class MatmulShape:
  rows: tuple[int, ...]
  cols: tuple[int, ...]
  per_core_m: int
  per_core_n: int
  bw: int
  num_blocks: int
  in0_block_tiles: int
  in1_block_tiles: int
  out_subblock_h: int
  out_subblock_w: int
  out_subblock_tiles: int
  in0_num_subblocks: int
  in1_num_subblocks: int

  @property
  def subblocks_per_core(self) -> int:
    return self.num_blocks * self.in0_num_subblocks * self.in1_num_subblocks

  @property
  def final_output_tiles_per_core(self) -> int:
    return self.per_core_m * self.per_core_n

  @property
  def packed_tiles_per_core(self) -> int:
    return self.subblocks_per_core * self.out_subblock_tiles


def p100_fast_cores() -> list[Core]:
  cores = [(x, y) for x in P100_TENSIX_X for y in range(2, 12)]
  return [core for core in cores if core not in {(P100_TENSIX_X[-1], 2), (P100_TENSIX_X[-1], 3)}]


def _text_bytes(kernel: KernelBase) -> bytes:
  return b"".join(seg.data for seg in kernel.compile() if seg.label == "text")


def _kernel_static(kernel: KernelBase) -> KernelStatic:
  out = KernelStatic()
  text = _text_bytes(kernel)
  out.text_words = len(text) // 4
  for off in range(0, len(text), 4):
    word = int.from_bytes(text[off:off + 4], "little")
    inst = dsl.decode(word)
    name = getattr(inst, "name", "")
    if (word & 3) != 3:
      out.tensix_words += 1
      out.tensix_ops[name] = out.tensix_ops.get(name, 0) + 1
    else:
      out.rv_words += 1
      if name == "lw":
        out.mmio_lw += 1
      elif name in {"sw", "sb", "sh"}:
        out.mmio_sw += 1
  return out


def _static_role_estimates(program: Program, core: Core | None) -> dict[str, RoleEstimate]:
  selected = program.kernels_for_core(core)
  roles: dict[str, RoleEstimate] = {}
  for role in ROLE_INDEX:
    stats = _kernel_static(selected[role])
    notes = [
      f"static words={stats.text_words}",
      f"rv={stats.rv_words}",
      f"tt={stats.tensix_words}",
    ]
    interesting = {k: v for k, v in stats.tensix_ops.items() if k in {"TTMOP", "TTMVMUL", "TTPACR", "TTUNPACR", "TTSTALLWAIT"}}
    if interesting:
      notes.append("tt_ops=" + ",".join(f"{k}:{v}" for k, v in sorted(interesting.items())))
    roles[role] = RoleEstimate(role, stats.issue_cycles, 0.0, notes)
  return roles


def _role_rta(program: Program, core: Core, role: str) -> list[int]:
  kernel = program.kernels_for_core(core)[role]
  return kernel.rtas(*core) if kernel.rtas is not None else []


def _matmul_shape_from_program(program: Program) -> MatmulShape | None:
  if program.grid is None:
    return None
  rows, cols = program.grid
  if not rows or not cols:
    return None
  core = (cols[0], rows[0])
  try:
    reader = _role_rta(program, core, "brisc")
    writer = _role_rta(program, core, "ncrisc")
  except Exception:
    return None
  if len(reader) < 9 or len(writer) < 29:
    return None
  per_core_m = reader[6]
  per_core_n = writer[5]
  bw = writer[6]
  num_blocks = writer[8]
  out_subblock_w = writer[24]
  out_subblock_h = writer[25]
  out_subblock_tiles = writer[26]
  in1_num_subblocks = writer[27]
  in0_num_subblocks = writer[28]
  if min(per_core_m, per_core_n, bw, num_blocks, out_subblock_tiles) <= 0:
    return None
  return MatmulShape(
    rows=tuple(rows),
    cols=tuple(cols),
    per_core_m=per_core_m,
    per_core_n=per_core_n,
    bw=bw,
    num_blocks=num_blocks,
    in0_block_tiles=reader[7],
    in1_block_tiles=writer[7],
    out_subblock_h=out_subblock_h,
    out_subblock_w=out_subblock_w,
    out_subblock_tiles=out_subblock_tiles,
    in0_num_subblocks=in0_num_subblocks,
    in1_num_subblocks=in1_num_subblocks,
  )


def _us_to_cycles(us: float, aiclk_mhz: float) -> float:
  return us * aiclk_mhz


def _gbps_us(byte_count: int, gbps: float) -> float:
  return byte_count / (gbps * 1000.0)


def _bpc_us(byte_count: int, bpc: float, aiclk_mhz: float) -> float:
  return byte_count / (bpc * aiclk_mhz)


def _estimate_matmul_program(
  program: Program,
  cores: list[Core],
  *,
  aiclk_mhz: float,
  drisc_mode: bool,
  trisc_cycles_per_subblock: float,
  output_tail_us: float,
  drisc_dma_gbps: float,
  peer_l1_stream_bpc: float,
  dram_write_gbps: float,
) -> ProgramEstimate | None:
  shape = _matmul_shape_from_program(program)
  if shape is None:
    return None

  trisc_cycles = shape.subblocks_per_core * trisc_cycles_per_subblock
  output_tail_cycles = _us_to_cycles(output_tail_us, aiclk_mhz)
  per_a_bytes = shape.in0_block_tiles * shape.num_blocks * matmul.TILE_BYTES
  per_b_bytes = shape.in1_block_tiles * shape.num_blocks * matmul.TILE_BYTES
  per_c_bytes = shape.final_output_tiles_per_core * matmul.TILE_BYTES
  if drisc_mode:
    a_feed_us = _gbps_us(per_a_bytes, drisc_dma_gbps) + _bpc_us(per_a_bytes, peer_l1_stream_bpc, aiclk_mhz)
    b_feed_us = _gbps_us(per_b_bytes, drisc_dma_gbps) + _bpc_us(per_b_bytes, peer_l1_stream_bpc, aiclk_mhz)
  else:
    a_feed_us = _gbps_us(per_a_bytes, 301.9)
    b_feed_us = _gbps_us(per_b_bytes, 245.7)
  c_write_us = _gbps_us(per_c_bytes, dram_write_gbps)
  feed_cycles = _us_to_cycles(max(a_feed_us, b_feed_us), aiclk_mhz)
  output_cycles = _us_to_cycles(c_write_us, aiclk_mhz) + output_tail_cycles

  estimates: list[CoreEstimate] = []
  first_col = shape.cols[0]
  first_row = shape.rows[0]
  for core in cores:
    roles = _static_role_estimates(program, core)
    x, y = core
    brisc_dyn = feed_cycles if x == first_col else min(feed_cycles, trisc_cycles * 0.1)
    ncrisc_input_dyn = feed_cycles if y == first_row else min(feed_cycles, trisc_cycles * 0.1)
    roles["brisc"].dynamic_cycles = brisc_dyn
    roles["brisc"].notes.append("matmul A feeder/mcast sender" if x == first_col else "matmul A receiver")
    roles["ncrisc"].dynamic_cycles = max(ncrisc_input_dyn, trisc_cycles) + output_cycles
    roles["ncrisc"].notes.append("matmul B sender + C writer" if y == first_row else "matmul B receiver + C writer")
    for role in ("trisc0", "trisc1", "trisc2"):
      roles[role].dynamic_cycles = trisc_cycles
      roles[role].notes.append(f"matmul subblocks={shape.subblocks_per_core}")
    estimates.append(CoreEstimate(core, roles))

  total_a = len(shape.rows) * per_a_bytes
  total_b = len(shape.cols) * per_b_bytes
  total_c = len(shape.rows) * len(shape.cols) * per_c_bytes
  summary = [
    f"grid={len(shape.rows)}x{len(shape.cols)} per_core={shape.per_core_m}x{shape.per_core_n} bw={shape.bw} blocks={shape.num_blocks}",
    f"subblocks/core={shape.subblocks_per_core:,} packed_tiles/core={shape.packed_tiles_per_core:,} final_tiles/core={shape.final_output_tiles_per_core:,}",
    f"partial-pack multiplier={shape.packed_tiles_per_core / shape.final_output_tiles_per_core:.1f}x",
    f"traffic A={total_a / (1 << 20):.2f}MiB B={total_b / (1 << 20):.2f}MiB C={total_c / (1 << 20):.2f}MiB",
    f"TRISC={trisc_cycles / aiclk_mhz:.1f}us output_tail={output_tail_us:.1f}us per-core-C-write-floor={c_write_us:.1f}us",
  ]
  return ProgramEstimate("matmul-drisc" if drisc_mode else "matmul", estimates, summary)


def estimate_program(
  program: Program,
  cores: list[Core] | None = None,
  *,
  aiclk_mhz: float = AICLK_MHZ,
  trisc_cycles_per_subblock: float = TRISC_CYCLES_PER_SUBBLOCK,
  output_tail_us: float = OUTPUT_TAIL_US,
  drisc_dma_gbps: float = DRISC_DMA_GBPS,
  peer_l1_stream_bpc: float = PEER_L1_STREAM_BPC,
  dram_write_gbps: float = DRAM_WRITE_GBPS,
) -> ProgramEstimate:
  if cores is None:
    cores = program.grid_cores() if program.grid is not None else p100_fast_cores()
  name = getattr(program, "name", "")
  drisc_mode = "drisc" in name
  if "matmul" in name or _matmul_shape_from_program(program) is not None:
    matmul_estimate = _estimate_matmul_program(
      program,
      cores,
      aiclk_mhz=aiclk_mhz,
      drisc_mode=drisc_mode,
      trisc_cycles_per_subblock=trisc_cycles_per_subblock,
      output_tail_us=output_tail_us,
      drisc_dma_gbps=drisc_dma_gbps,
      peer_l1_stream_bpc=peer_l1_stream_bpc,
      dram_write_gbps=dram_write_gbps,
    )
    if matmul_estimate is not None:
      return matmul_estimate

  estimates = [
    CoreEstimate(core, _static_role_estimates(program, core if program.grid is not None else None))
    for core in cores
  ]
  return ProgramEstimate("generic-static", estimates, ["dynamic loops not recognized; showing static issue lower bounds"])


def _build_demo_program(args) -> Program:
  cores = p100_fast_cores()
  if args.example == "matmul-drisc":
    plan = matmul_drisc.plan_matmul_drisc(args.M, args.K, args.N, cores, 20)
    program = matmul_drisc.build_program_drisc(plan, 0, 7)
    program.name = f"matmul_drisc_M{args.M}_N{args.N}_K{args.K}"
    return program
  plan = matmul.plan_matmul(args.M, args.K, args.N, cores)
  program = matmul.build_program(plan, 0, 0, 0, 7)
  program.name = f"matmul_M{args.M}_N{args.N}_K{args.K}"
  return program


def main() -> None:
  parser = argparse.ArgumentParser(description="Estimate Program timing from static structure and calibrated microbench constants.")
  parser.add_argument("--example", choices=("matmul", "matmul-drisc"), default="matmul-drisc")
  parser.add_argument("M", type=int, nargs="?", default=5000)
  parser.add_argument("N", type=int, nargs="?", default=5000)
  parser.add_argument("K", type=int, nargs="?", default=5000)
  parser.add_argument("--limit-cores", type=int, default=12)
  parser.add_argument("--aiclk-mhz", type=float, default=AICLK_MHZ)
  parser.add_argument("--trisc-cycles-per-subblock", type=float, default=TRISC_CYCLES_PER_SUBBLOCK)
  parser.add_argument("--output-tail-us", type=float, default=OUTPUT_TAIL_US)
  args = parser.parse_args()
  program = _build_demo_program(args)
  estimate = estimate_program(
    program,
    aiclk_mhz=args.aiclk_mhz,
    trisc_cycles_per_subblock=args.trisc_cycles_per_subblock,
    output_tail_us=args.output_tail_us,
  )
  estimate.print(aiclk_mhz=args.aiclk_mhz, limit=args.limit_cores)


if __name__ == "__main__":
  main()
