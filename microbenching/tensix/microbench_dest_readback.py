#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402  (does sys.path + TT_USB bootstrap on import)
import numpy as np

import matmul_peak as matmul

from asm import KernelBase
from device import Device
from dram import tilize
from dsl import TTSEMWAIT, a2, a3, a4, a5, s2, t0, t1, t2, zero
from program import Dtype, Program
from ttk.debug import DebugRange
from ttk.tensix import TensixDebugArray, TensixSem, TensixSemWait


AICLK_MHZ = 800.0
RESULT_BASE = 0x12D000
READBACK_BASE = 0x12D400
RESULT_MAGIC = 0x44524248  # "HBRD"
RECORD_MAGIC = 0x44524252  # "RBRD"
STATUS_STARTED = 0xD57B0001
STATUS_DONE = 0xD57BD00D
HEADER_WORDS = 16
RECORD_WORDS = 16
HEADER_SIZE = HEADER_WORDS * 4
RECORD_SIZE = RECORD_WORDS * 4
OUT_TILES = 4
READBACK_TILES = 1
ROWS_PER_TILE = 64
READBACK_BYTES = READBACK_TILES * ROWS_PER_TILE * TensixDebugArray.ROW_BYTES


@dataclass(frozen=True)
class TimingRecord:
  readback: bool
  start: int
  end: int
  cycles: int

  @property
  def us(self) -> float:
    return self.cycles / AICLK_MHZ


def tiny_plan(core: tuple[int, int]) -> matmul.MatmulPlan:
  return matmul.MatmulPlan(
    rows=(core[1],), cols=(core[0],), mt=2, kt=1, nt=2,
    per_core_m=2, per_core_n=2, in0_block_w=1, num_blocks=1,
    out_subblock_h=2, out_subblock_w=2,
    in0_num_subblocks=1, in1_num_subblocks=1,
    in0_block_num_tiles=2, in0_subblock_num_tiles=2,
    in1_block_num_tiles=2, in1_per_core_w=2,
    out_subblock_num_tiles=OUT_TILES,
    out_block_num_tiles=OUT_TILES,
    cb0_pages=2, cb1_pages=2, cb16_pages=OUT_TILES, cb24_pages=OUT_TILES,
    logical_mt=2, logical_nt=2,
  )


def result_size() -> int:
  return HEADER_SIZE + RECORD_SIZE


def debug_ranges() -> tuple[DebugRange, ...]:
  return (
    DebugRange(0, "l1", RESULT_BASE, result_size(), "dest_readback_result"),
    DebugRange(1, "l1", READBACK_BASE, READBACK_BYTES, "dest_readback_rows"),
  )


def emit_header(fw: KernelBase, *, status: int, readback: bool):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, 1, int(readback), status, READBACK_BASE, READBACK_BYTES, result_size(), 0,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  return fw


def emit_record(fw: KernelBase, *, readback: bool, start_lo, start_hi, end_lo, end_hi):
  fw.li(s2, RESULT_BASE + HEADER_SIZE)
  for off, value in enumerate((RECORD_MAGIC, int(readback), READBACK_TILES, ROWS_PER_TILE)):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off, reg in enumerate((start_lo, start_hi, end_lo, end_hi), start=4):
    fw.sw(reg, s2, off * 4)
  for off in range(8, RECORD_WORDS):
    fw.sw(zero, s2, off * 4)
  return fw


def emit_readback(fw: matmul.MatmulTrisc):
  for tile in range(READBACK_TILES):
    for row in range(ROWS_PER_TILE):
      dest_row = tile * ROWS_PER_TILE + row
      l1_addr = READBACK_BASE + dest_row * TensixDebugArray.ROW_BYTES
      fw.dest_row_to_l1(l1_addr, dest_row, thread_id=1)
  return fw


def trisc1_with_optional_readback(plan: matmul.MatmulPlan, *, do_readback: bool) -> matmul.MatmulTrisc:
  fw = matmul.MatmulTrisc(1)
  fw.prologue()
  emit_header(fw, status=STATUS_STARTED, readback=do_readback)
  matmul.matmul_math_init(fw, plan)
  fw.init_barrier()

  fw.emit(TTSEMWAIT(
    matmul.STALL_MATH_PACK_ROOM,
    TensixSem.mask(TensixSem.MATH_PACK),
    TensixSemWait.STALL_ON_MAX,
  ))
  harness.read_wall_clock(fw, a2, a3)
  matmul.emit_math_subblock_body(fw, plan, 0, 0)
  fw.emit(matmul.TTSTALLWAIT(matmul.TensixStall.SYNC, matmul.TensixWait.MATH | matmul.TensixWait.SFPU))
  fw.tensix_sync(1, tmp=t1)
  if do_readback:
    emit_readback(fw)
  harness.read_wall_clock(fw, a4, a5)
  emit_record(fw, readback=do_readback, start_lo=a2, start_hi=a3, end_lo=a4, end_hi=a5)
  matmul.emit_math_subblock_commit(fw)
  emit_header(fw, status=STATUS_DONE, readback=do_readback)
  return fw.ret_kernel()


def build_program(
  plan: matmul.MatmulPlan,
  a_addr: int,
  b_addr: int,
  c_addr: int,
  num_banks: int,
  *,
  do_readback: bool,
) -> Program:
  brisc_sender = matmul.matmul_reader_sender(plan)
  brisc_recv = matmul.matmul_reader_recv()
  ncrisc_sender = matmul.matmul_writer_sender(plan)
  ncrisc_recv = matmul.matmul_writer_recv(plan)
  trisc0 = matmul.matmul_trisc0(plan)
  trisc1 = trisc1_with_optional_readback(plan, do_readback=do_readback)
  trisc2 = matmul.matmul_trisc2(plan)

  brisc_sender.rta(lambda x, y: matmul.reader_args(plan, a_addr, (x, y), num_banks))
  brisc_recv.rta(lambda x, y: matmul.reader_args(plan, a_addr, (x, y), num_banks))
  ncrisc_sender.rta(lambda x, y: matmul.writer_args(plan, b_addr, c_addr, (x, y), num_banks))
  ncrisc_recv.rta(lambda x, y: matmul.writer_args(plan, b_addr, c_addr, (x, y), num_banks))

  prog = Program(
    brisc=brisc_sender,
    brisc_recv=brisc_recv,
    ncrisc=ncrisc_sender,
    ncrisc_recv=ncrisc_recv,
    trisc0=trisc0,
    trisc1=trisc1,
    trisc2=trisc2,
    cbs=[
      (0, matmul.TILE_BYTES, plan.cb0_pages),
      (1, matmul.TILE_BYTES, plan.cb1_pages),
      (16, matmul.TILE_BYTES, plan.cb16_pages),
      (24, matmul.TILE_BYTES, plan.cb24_pages),
    ],
    semaphores=matmul.NUM_SEMAPHORES,
    grid=(plan.rows, plan.cols),
  )
  prog.name = f"microbench_dest_readback:{'on' if do_readback else 'off'}"
  return prog


def clear_l1(device: Device, core: tuple[int, int]):
  with harness.device_window(device, core) as win:
    for item in debug_ranges():
      win.write(item.address, b"\0" * item.size)


def read_l1(device: Device, core: tuple[int, int], item: DebugRange) -> bytes:
  with harness.device_window(device, core) as win:
    blob = win.read(item.address, item.size)
  if blob and all(b == 0xFF for b in blob):
    raise RuntimeError("L1 readback returned all 0xff; device likely needs reset/reboot")
  return blob


def parse_timing(blob: bytes) -> TimingRecord:
  header = struct.unpack_from("<" + "I" * HEADER_WORDS, blob, 0)
  if header[0] != RESULT_MAGIC:
    raise RuntimeError(f"bad result magic 0x{header[0]:08x}")
  if header[3] != STATUS_DONE:
    raise RuntimeError(f"benchmark did not finish, status=0x{header[3]:08x}")
  words = struct.unpack_from("<" + "I" * RECORD_WORDS, blob, HEADER_SIZE)
  if words[0] != RECORD_MAGIC:
    raise RuntimeError(f"bad record magic 0x{words[0]:08x}")
  start = words[4] | (words[5] << 32)
  end = words[6] | (words[7] << 32)
  return TimingRecord(readback=bool(words[1]), start=start, end=end, cycles=(end - start) & ((1 << 64) - 1))


def readback_candidates(blob: bytes) -> tuple[bytes, bytes]:
  words = struct.unpack("<" + "I" * (len(blob) // 4), blob)
  little = b"".join(word.to_bytes(4, "little") for word in words)
  big = b"".join(word.to_bytes(4, "big") for word in words)
  return little, big


def validate_readback(readback: bytes, c_raw: bytes, shape: tuple[int, int]) -> tuple[str, int]:
  expected_tiled = tilize(c_raw, Dtype.Float16_b.bpe, shape)
  expected_tiled = expected_tiled[:len(readback)]
  best_name = "little"
  best = readback_candidates(readback)[0]
  best_mismatches = sum(a != b for a, b in zip(best, expected_tiled))
  for name, candidate in zip(("little", "big"), readback_candidates(readback)):
    mismatches = sum(a != b for a, b in zip(candidate, expected_tiled))
    if mismatches < best_mismatches:
      best_name, best, best_mismatches = name, candidate, mismatches
  if best_mismatches:
    raise AssertionError(f"dest readback did not match packed output ({best_mismatches} byte mismatches, best={best_name})")
  got = matmul.from_bf16_device_bytes(c_raw, shape)
  if not np.all(np.isfinite(got)):
    raise AssertionError("dest readback validation output contains non-finite values")
  return best_name, best_mismatches


def make_case() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
  m, k, n = 64, 32, 64
  a_ref, b_ref = matmul.make_inputs(m, k, n)
  a_padded = np.zeros((m, k), dtype=np.float32)
  b_padded = np.zeros((k, n), dtype=np.float32)
  a_padded[:m, :k] = a_ref
  b_padded[:k, :n] = b_ref
  return a_ref, b_ref, a_padded, b_padded


def validate_matmul_output(c_raw: bytes):
  a_ref, b_ref, _, _ = make_case()
  return matmul.validate(a_ref, b_ref, c_raw, 64, 64, 64, 64)


def run_once(
  device: Device,
  core: tuple[int, int],
  *,
  do_readback: bool,
  validate_output: bool = True,
) -> tuple[TimingRecord, bytes, bytes]:
  plan = tiny_plan(core)
  a_ref, b_ref, a_padded, b_padded = make_case()
  a_buf = device.alloc_write(matmul.to_bf16_device_bytes(a_padded), dtype=Dtype.Float16_b, shape=a_padded.shape, name="A_readback")
  b_buf = device.alloc_write(matmul.to_bf16_device_bytes(b_padded), dtype=Dtype.Float16_b, shape=b_padded.shape, name="B_readback")
  c_buf = device.dram.alloc(OUT_TILES, dtype=Dtype.Float16_b, shape=(64, 64), name="C_readback")

  clear_l1(device, core)
  prog = build_program(plan, a_buf.addr, b_buf.addr, c_buf.addr, len(device.dram.bank_tiles), do_readback=do_readback)
  device.run(prog)
  timing = parse_timing(read_l1(device, core, debug_ranges()[0]))
  readback = read_l1(device, core, debug_ranges()[1]) if do_readback else b""
  c_raw = device.dram_read(c_buf)
  if validate_output:
    matmul.validate(a_ref, b_ref, c_raw, 64, 64, 64, 64)
  return timing, readback, c_raw


def build_only(core: tuple[int, int]):
  plan = tiny_plan(core)
  for do_readback in (False, True):
    prog = build_program(plan, 0, 0, 0, 1, do_readback=do_readback)
    segments = prog.layout(core_xy=core)
    total = sum(len(seg.data) for seg in segments)
    print(f"build-only readback={do_readback}: {len(segments)} segments, {total} bytes")


def main() -> None:
  parser = argparse.ArgumentParser(description="Validate Blackhole Tensix Dest debug-array readback against a tiny matmul.")
  parser.add_argument("--core", type=harness.parse_core, default=(1, 2), help="logical Tensix core X,Y")
  parser.add_argument("--build-only", action="store_true", help="only build Program/assembly; do not open the device")
  args = parser.parse_args()

  if args.build_only:
    build_only(args.core)
    return

  with harness.open_device() as device:
    core = args.core or device.cores[0]
    no_rb, _, c_ref = run_once(device, core, do_readback=False)
    with_rb, readback, c_after_readback = run_once(device, core, do_readback=True, validate_output=False)

  byte_order, _ = validate_readback(readback, c_ref, (64, 64))
  try:
    validate_matmul_output(c_after_readback)
    pack_after_readback = "passed"
  except AssertionError as exc:
    pack_after_readback = f"failed: {exc}"
  perturb = with_rb.cycles - no_rb.cycles
  print("| row | cycles | us |")
  print("|---|---:|---:|")
  print(f"| math no readback | {no_rb.cycles} | {no_rb.us:.3f} |")
  print(f"| math plus readback | {with_rb.cycles} | {with_rb.us:.3f} |")
  print(f"\nreadback matched packed matmul output using {byte_order}-endian debug words")
  print(f"pack output after readback validation: {pack_after_readback}")
  print(f"readback perturbation: {perturb} cycles ({perturb / AICLK_MHZ:.3f} us)")


if __name__ == "__main__":
  main()
