#!/usr/bin/env python3
"""Aggregate DRISC-local GDDR read bandwidth across enabled GDDR banks.

This is the multi-bank companion to microbench_drisc_gddr_dma.py.  It launches
one DRISC kernel per selected GDDR bank and uses the proven same-stream
outstanding-read pattern to copy GDDR into that DRISC's local L1 staging slots.
"""
from __future__ import annotations

import argparse
import os
import struct
import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402  (sets repo/examples paths)
from asm import KernelBase  # noqa: E402
from dsl import a2, a3, a4, a5, a6, a7, s0, s1, s2, s3, s4, t0, t1, t2, t3, t4, zero  # noqa: E402
from drisc_gddr_dma_poc import (  # noqa: E402
  DEBUG_CLOCK_MHZ, DMA_CTRL_ATTRS_BURST_255, DMA_READ_ATTR_BASE,
  RESULT_ADDR as SINGLE_RESULT_ADDR, STAGE_ADDR as DEFAULT_STAGE_ADDR,
  TX_CTRL_TRANSFER_ATTRIBUTES, TX_STREAM_STATUS, stream_reg,
)
from microbench_drisc_gddr_dma import (  # noqa: E402
  MAX_STAGE_END, emit_dma_start, emit_read_wait_n, emit_read_wall_clock,
)
from pcie import PCIDevice, TLBWindow  # noqa: E402
from ttk.drisc import (  # noqa: E402
  DRISC_FW_BASE, DRISC_L1_NOC_ALIAS, RegWindow, start_drisc, wait_drisc,
)


MAGIC = 0x41474444  # "DDGA", little-endian.
RESULT_ADDR = SINGLE_RESULT_ADDR
RESULT_WORDS = 16
START_GATE_ADDR = RESULT_ADDR + RESULT_WORDS * 4
STATUS_STARTED = 1
STATUS_DONE = 2


@dataclass(frozen=True)
class Run:
  bank: int
  endpoint: int
  core: tuple[int, int]
  code: bytes


@dataclass(frozen=True)
class Row:
  bank: int
  endpoint: int
  core: tuple[int, int]
  cycles: int
  bytes_per_cycle: float
  gbps: float
  ok: bool
  detail: str


def _u64(words: tuple[int, ...], lo_idx: int) -> int:
  return words[lo_idx] | (words[lo_idx + 1] << 32)


def _delta(start: int, end: int) -> int:
  return (end - start) & ((1 << 64) - 1)


def _gbps(byte_count: int, cycles: int) -> float:
  return (byte_count / cycles) * DEBUG_CLOCK_MHZ / 1000.0 if cycles else 0.0


def pattern_at(size: int, seed: int, offset: int) -> bytes:
  return bytes((((offset + i) * 29 + seed) ^ ((offset + i) >> 5) ^ ((offset + i) >> 11)) & 0xFF for i in range(size))


def final_pages(pages: int, depth: int) -> list[int]:
  return [
    slot + ((pages - 1 - slot) // depth) * depth
    for slot in range(min(depth, pages))
  ]


def enabled_banks(dev: PCIDevice) -> list[int]:
  info = dev.board_info(fast_dispatch=True)
  return sorted({bank for bank, _x, _y in info.dram_tiles})


def select_dram_core(dev: PCIDevice, bank: int, endpoint: int) -> tuple[int, int]:
  info = dev.board_info(fast_dispatch=True)
  tiles = [(x, y) for b, x, y in info.dram_tiles if b == bank]
  if not tiles:
    raise ValueError(f"bank {bank} is not enabled")
  if endpoint < 0 or endpoint >= len(tiles):
    raise ValueError(f"endpoint must be in [0, {len(tiles) - 1}] for bank {bank}")
  return tiles[endpoint]


def read_wall(dev: PCIDevice, core: tuple[int, int]) -> int:
  regs = RegWindow(dev, core)
  try:
    addr = 0xFFB121F8
    while True:
      hi = regs.read32(addr)
      lo = regs.read32(0xFFB121F0)
      hi2 = regs.read32(addr)
      if hi == hi2:
        return lo | (hi << 32)
  finally:
    regs.close()


def emit_header(fw: KernelBase, *, bank: int, endpoint: int, page_size: int, pages: int, depth: int):
  values = (
    MAGIC,
    bank,
    endpoint,
    page_size,
    pages,
    0,
    STATUS_STARTED,
    depth,
  )
  for idx, value in enumerate(values):
    fw.write32(RESULT_ADDR + idx * 4, value, tmp_addr=t0, tmp_val=t1)
  for idx in range(len(values), RESULT_WORDS):
    fw.write32(RESULT_ADDR + idx * 4, 0, tmp_addr=t0, tmp_val=t1)
  return fw


def emit_wait_gate(fw: KernelBase):
  armed = fw._new_label("gate_armed")
  wait = fw._new_label("gate_wait")
  done = fw._new_label("gate_done")
  fw.li(t0, START_GATE_ADDR)
  fw.label(armed)
  fw.lw(t1, t0, 0)
  fw.lw(t2, t0, 4)
  fw.or_(t3, t1, t2)
  fw.beq(t3, zero, armed)
  fw.label(wait)
  emit_read_wall_clock(fw, a2, a3, addr=t4, hi2=t3)
  fw.bltu(a3, t2, wait)
  fw.bltu(t2, a3, done)
  fw.bltu(a2, t1, wait)
  fw.j(done)
  fw.label(done)
  return fw


def build_kernel(
  *, bank: int, endpoint: int, gddr_addr: int, page_size: int, pages: int,
  stage_addr: int, depth: int, stream: int,
) -> bytes:
  if page_size <= 0 or page_size % 16:
    raise ValueError("page size must be a positive multiple of 16")
  if pages <= 0:
    raise ValueError("pages must be positive")
  if depth < 2 or depth > 255 or depth & (depth - 1):
    raise ValueError("depth must be a power of two in [2, 255]")
  if stream not in (0, 1):
    raise ValueError("stream must be 0 or 1")
  if stage_addr < DRISC_FW_BASE + 0x1000:
    raise ValueError("stage address is too close to DRISC code")
  if stage_addr + depth * page_size > MAX_STAGE_END:
    raise ValueError(f"{depth} stage slots do not fit before result area 0x{MAX_STAGE_END:x}")

  gddr_hi = (gddr_addr >> 32) & 0xFFFFFFFF
  fw = KernelBase(base_addr=DRISC_FW_BASE)
  emit_header(fw, bank=bank, endpoint=endpoint, page_size=page_size, pages=pages, depth=depth)
  fw.write32(TX_CTRL_TRANSFER_ATTRIBUTES, DMA_CTRL_ATTRS_BURST_255, tmp_addr=t0, tmp_val=t1)
  emit_wait_gate(fw)

  emit_read_wall_clock(fw, a2, a3, addr=t4, hi2=t3)
  fw.write32(RESULT_ADDR + 8 * 4, a2, tmp_addr=t0, tmp_val=t1)
  fw.write32(RESULT_ADDR + 9 * 4, a3, tmp_addr=t0, tmp_val=t1)

  fw.li(s0, 0)  # pages issued
  fw.li(s1, pages)
  fw.li(s2, gddr_addr & 0xFFFFFFFF)
  fw.li(s3, depth - 1)
  loop = fw._new_label("pipe_loop")
  done = fw._new_label("pipe_done")
  fw.label(loop)
  fw.bgeu(s0, s1, done)
  emit_read_wait_n(fw, stream=stream, max_outstanding=depth - 1)
  fw.and_(s4, s0, s3)
  fw.li(t1, page_size)
  fw.mul(s4, s4, t1)
  fw.li(t1, stage_addr)
  fw.add(s4, s4, t1)
  emit_dma_start(
    fw, direction=1, stream=stream, gddr_lo=s2, gddr_hi=gddr_hi,
    l1_addr=s4, page_size=page_size, read_attr_base=DMA_READ_ATTR_BASE,
    write_attr_base=0,
  )
  fw.li(t1, page_size)
  fw.add(s2, s2, t1)
  fw.addi(s0, s0, 1)
  fw.j(loop)
  fw.label(done)

  emit_read_wall_clock(fw, a4, a5, addr=t4, hi2=t3)
  fw.write32(RESULT_ADDR + 10 * 4, a4, tmp_addr=t0, tmp_val=t1)
  fw.write32(RESULT_ADDR + 11 * 4, a5, tmp_addr=t0, tmp_val=t1)
  emit_read_wait_n(fw, stream=stream, max_outstanding=0)
  emit_read_wall_clock(fw, a6, a7, addr=t4, hi2=t3)
  fw.write32(RESULT_ADDR + 12 * 4, a6, tmp_addr=t0, tmp_val=t1)
  fw.write32(RESULT_ADDR + 13 * 4, a7, tmp_addr=t0, tmp_val=t1)
  fw.read32(t1, stream_reg(stream, TX_STREAM_STATUS), tmp_addr=t0)
  fw.write32(RESULT_ADDR + 14 * 4, t1, tmp_addr=t0, tmp_val=t2)
  fw.write32(RESULT_ADDR + 15 * 4, depth, tmp_addr=t0, tmp_val=t1)
  fw.write32(RESULT_ADDR + 6 * 4, STATUS_DONE, tmp_addr=t0, tmp_val=t1)
  spin = fw._new_label("done_spin")
  fw.label(spin)
  fw.j(spin)
  return fw.compile()[0].data


def parse_banks(text: str, available: list[int]) -> list[int]:
  if text == "all":
    return available
  banks = [int(item.strip(), 0) for item in text.split(",") if item.strip()]
  if not banks:
    raise argparse.ArgumentTypeError("bank list must not be empty")
  missing = sorted(set(banks) - set(available))
  if missing:
    raise argparse.ArgumentTypeError(f"bank(s) not enabled: {missing}; available={available}")
  return banks


def seed_and_clear_gate(
  dev: PCIDevice, run: Run, *, gddr_addr: int, page_size: int, pages: int,
  stage_addr: int, depth: int,
):
  with TLBWindow(dev, start=run.core, addr=0, size=TLBWindow.SIZE_4G, wc=True) as gddr:
    for page in final_pages(pages, depth):
      off = page * page_size
      gddr.write(gddr_addr + off, pattern_at(page_size, 0x31 + run.bank, off))
  with TLBWindow(dev, start=run.core, addr=DRISC_L1_NOC_ALIAS) as l1:
    l1.write(stage_addr, b"\0" * (depth * page_size))
    l1.write(START_GATE_ADDR, b"\0" * 8)


def arm_gate(dev: PCIDevice, run: Run, *, delay_cycles: int):
  gate = read_wall(dev, run.core) + delay_cycles
  with TLBWindow(dev, start=run.core, addr=DRISC_L1_NOC_ALIAS) as l1:
    l1.write(START_GATE_ADDR, struct.pack("<Q", gate))


def verify_run(
  dev: PCIDevice, run: Run, *, page_size: int, pages: int, stage_addr: int, depth: int,
) -> tuple[bool, str]:
  with TLBWindow(dev, start=run.core, addr=DRISC_L1_NOC_ALIAS) as l1:
    for slot, final_page in enumerate(final_pages(pages, depth)):
      expected = pattern_at(page_size, 0x31 + run.bank, final_page * page_size)
      got = l1.read(stage_addr + slot * page_size, page_size)
      mismatch = next((idx for idx, (a, b) in enumerate(zip(got, expected)) if a != b), -1)
      if mismatch != -1:
        return False, f"slot={slot} final_page={final_page} mismatch={mismatch}"
  return True, f"checked_slots={min(depth, pages)}"


def format_rows(rows: list[Row], *, aggregate_cycles: int, aggregate_gbps: float, target_gbps: float) -> str:
  lines = [
    "| bank | endpoint | core | cycles | B/cyc | GB/s | ok | detail |",
    "|---:|---:|---|---:|---:|---:|---|---|",
  ]
  for row in rows:
    lines.append(
      f"| {row.bank} | {row.endpoint} | `{row.core[0]},{row.core[1]}` | {row.cycles} | "
      f"{row.bytes_per_cycle:.3f} | {row.gbps:.1f} | {row.ok} | {row.detail} |"
    )
  lines.append("")
  lines.append(
    f"Aggregate max-duration window: {aggregate_cycles} cycles; aggregate: {aggregate_gbps:.1f} GB/s; "
    f"per-channel target sum: {target_gbps:.1f} GB/s; saturation: {100.0 * aggregate_gbps / target_gbps:.1f}%"
  )
  return "\n".join(lines)


def main() -> None:
  parser = argparse.ArgumentParser(description="Aggregate DRISC GDDR DMA read bandwidth across GDDR banks.")
  parser.add_argument("--banks", default="all", help="comma list of enabled banks, or all")
  parser.add_argument("--endpoint", type=int, default=0)
  parser.add_argument("--gddr-addr", type=lambda s: int(s, 0), default=0x100000)
  parser.add_argument("--stage-addr", type=lambda s: int(s, 0), default=DEFAULT_STAGE_ADDR)
  parser.add_argument("--page-size", type=int, default=16 * 1024)
  parser.add_argument("--pages", type=int, default=64)
  parser.add_argument("--pipe-depth", type=int, default=4)
  parser.add_argument("--stream", type=int, default=0)
  parser.add_argument("--gate-delay-ms", type=float, default=200.0)
  parser.add_argument("--timeout", type=float, default=10.0)
  parser.add_argument("--dry-run", action="store_true")
  parser.add_argument("--no-report", action="store_true")
  parser.add_argument("--report", type=Path, default=harness.doc_path("tensix", "drisc-gddr-dma-aggregate.md"))
  args = parser.parse_args()

  os.environ.pop("TT_USB", None)
  dev = PCIDevice(use_vfio=True)
  try:
    available = enabled_banks(dev)
    banks = parse_banks(args.banks, available)
    runs = [
      Run(
        bank=bank,
        endpoint=args.endpoint,
        core=select_dram_core(dev, bank, args.endpoint),
        code=build_kernel(
          bank=bank, endpoint=args.endpoint, gddr_addr=args.gddr_addr,
          page_size=args.page_size, pages=args.pages, stage_addr=args.stage_addr,
          depth=args.pipe_depth, stream=args.stream,
        ),
      )
      for bank in banks
    ]
    if args.dry_run:
      for run in runs:
        print(f"dry-run bank={run.bank} endpoint={run.endpoint} core={run.core} code_B={len(run.code)}")
      print(f"dry-run passed: banks={len(runs)} total_code_B={sum(len(run.code) for run in runs)}")
      return

    dev.set_power_state(True)
    try:
      for run in runs:
        seed_and_clear_gate(
          dev, run, gddr_addr=args.gddr_addr, page_size=args.page_size, pages=args.pages,
          stage_addr=args.stage_addr, depth=args.pipe_depth,
        )
      for run in runs:
        start_drisc(run.core, run.code, dev, result_addr=RESULT_ADDR, result_words=RESULT_WORDS)
      delay_cycles = int(DEBUG_CLOCK_MHZ * 1000.0 * args.gate_delay_ms)
      for run in runs:
        arm_gate(dev, run, delay_cycles=delay_cycles)
      words_by_bank = {
        run.bank: wait_drisc(
          run.core, dev, args.timeout, magic=MAGIC, result_addr=RESULT_ADDR,
          result_words=RESULT_WORDS, label=f"DRISC aggregate bank {run.bank}",
        )
        for run in runs
      }
      verify = {
        run.bank: verify_run(
          dev, run, page_size=args.page_size, pages=args.pages,
          stage_addr=args.stage_addr, depth=args.pipe_depth,
        )
        for run in runs
      }
    finally:
      dev.set_power_state(False)
  finally:
    dev.close()

  total_bytes = args.page_size * args.pages
  rows = []
  cycles_all = []
  for run in runs:
    words = words_by_bank[run.bank]
    start = _u64(words, 8)
    end = _u64(words, 12)
    cycles = _delta(start, end)
    cycles_all.append(cycles)
    ok, detail = verify[run.bank]
    rows.append(Row(
      bank=run.bank,
      endpoint=run.endpoint,
      core=run.core,
      cycles=cycles,
      bytes_per_cycle=total_bytes / cycles if cycles else 0.0,
      gbps=_gbps(total_bytes, cycles),
      ok=ok and words[6] == STATUS_DONE,
      detail=f"status=0x{words[14]:08x} {detail}",
    ))

  aggregate_cycles = max(cycles_all)
  aggregate_gbps = _gbps(total_bytes * len(runs), aggregate_cycles)
  target_gbps = 64.0 * len(runs)
  table = format_rows(rows, aggregate_cycles=aggregate_cycles, aggregate_gbps=aggregate_gbps, target_gbps=target_gbps)
  print(table)
  if not args.no_report:
    args.report.parent.mkdir(parents=True, exist_ok=True)
    harness.append_report(args.report, "DRISC GDDR DMA Aggregate", [
      f"Command: `{' '.join(sys.argv)}`",
      "Scope: one DRISC per selected GDDR bank; same-stream pipelined GDDR reads into DRISC-local L1",
      f"Banks: {','.join(str(run.bank) for run in runs)}; endpoint: {args.endpoint}",
      f"Page size: {args.page_size}; pages per bank: {args.pages}; pipe depth: {args.pipe_depth}",
      f"Clock assumption: {DEBUG_CLOCK_MHZ:.1f} MHz",
    ], table=table)
    print(f"appended {args.report}")
  if not all(row.ok for row in rows):
    raise SystemExit(1)


if __name__ == "__main__":
  main()
