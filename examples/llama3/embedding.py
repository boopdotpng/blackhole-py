#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os

import numpy as np

from asm import KernelBase
from dram import tilize
from dsl import a0, a1, a2, a3, a4, a5, a6, a7, s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, t0, t1, t2, t3, t4, t5, t6, zero
from device import Device
from program import Dtype, Program
from ttk import Noc
from ttk.addrs import Core, p100_dram_bank_endpoint_coords
from ttk.mailbox import BriscMailbox as BM
from ttk.noc import NOC
from ttk.tensix import TensixL1


VOCAB_SIZE = 128256
EMB_DIM = 2048
MAX_SEQ_LEN = 1024
TILE_R = 32
TILE_C = 32
BF16_BYTES = 2
TOKEN_BYTES = 4
TILE_BYTES = Dtype.Float16_b.tile_size
ROW_CHUNK_BYTES = 16 * BF16_BYTES
FACE_BYTES = 16 * 16 * BF16_BYTES
COL_TILES = EMB_DIM // TILE_C
SEQ_TILE_ROWS = MAX_SEQ_LEN // TILE_R
OUT_TILES = SEQ_TILE_ROWS * COL_TILES
TARGET_CORE: Core = (1, 2)
SCRATCH_L1 = TensixL1.DATA_BUFFER_SPACE_BASE


class Brisc(KernelBase, Noc):
  pass


def _empty_kernel() -> KernelBase:
  return KernelBase()


def _dram_tile_addr_static(fw: Brisc, bank_coords: list[int]):
  fw.mv(t0, a1)
  fw.remu(a1, t0, a2)
  fw.divu(t0, t0, a2)
  fw.slli(t0, t0, 11)
  fw.add(a0, a0, t0)
  fw.li(a2, bank_coords[0])
  for bank, coord in enumerate(bank_coords[1:], start=1):
    next_bank = fw._new_label("dram_bank")
    fw.li(t1, bank)
    fw.bne(a1, t1, next_bank)
    fw.li(a2, coord)
    fw.label(next_bank)
  return fw


def _copy_32b(fw: Brisc, *, src_lo=t3, src_coord=t4, dst_lo=t5, dst_coord=a7, src_stage=t2, dst_stage=t6):
  fw.read32(a4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
  fw.addi(a4, a4, 1)
  fw.li(a1, ROW_CHUNK_BYTES)
  fw.noc_read(0, 1, src_lo, 0, src_coord, src_stage, a1, ret_coord=a5, a=t0, v=t1)
  fw.noc_reads_flushed(0, a4, addr=t0, val=t1)

  for off in range(0, ROW_CHUNK_BYTES, 4):
    fw.lw(a0, src_stage, off)
    fw.sw(a0, dst_stage, off)

  fw.read32(a4, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED)
  fw.addi(a4, a4, 1)
  fw.li(a1, ROW_CHUNK_BYTES)
  fw.noc_write(0, 0, dst_stage, dst_lo, 0, dst_coord, a1, a=t0, v=t1)
  return fw.noc_write_barrier(0, a4, addr=t0, val=t1)


def _row_offset_from_32(fw: Brisc, row_reg, out_reg):
  fw.andi(t1, row_reg, 31)
  fw.andi(t0, t1, 15)
  fw.slli(out_reg, t0, 5)
  top_half_done = fw._new_label("row_top_half_done")
  fw.li(t0, 16)
  fw.bltu(t1, t0, top_half_done)
  fw.addi(out_reg, out_reg, 2 * FACE_BYTES)
  fw.label(top_half_done)
  return fw


def _read_token_id(fw: Brisc, token_bank_coords: list[int]):
  # token byte offset = row * sizeof(uint32), with the padded token buffer
  # stored as raw bytes in 2 KiB DRAM pages.
  fw.slli(t6, s7, 2)
  fw.srli(a1, t6, 11)
  fw.li(t2, TILE_BYTES - 1)
  fw.and_(t2, t6, t2)
  fw.mv(a0, s1)
  fw.mv(a2, s6)
  _dram_tile_addr_static(fw, token_bank_coords)
  fw.add(t3, a0, t2)
  fw.mv(t4, a2)
  fw.li(t2, SCRATCH_L1)
  fw.add(t2, t2, t6)

  fw.read32(a4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
  fw.addi(a4, a4, 1)
  fw.li(a1, TOKEN_BYTES)
  fw.noc_read(0, 1, t3, 0, t4, t2, a1, ret_coord=a5, a=t0, v=t1)
  fw.noc_reads_flushed(0, a4, addr=t0, val=t1)
  return fw.lw(s8, t2, 0)


def embedding_gather_brisc(bank_coords: list[int]) -> Brisc:
  """Gather a padded token-id buffer into a padded tiled activation tensor.

  RTA:
    s0: source embedding DRAM base
    s1: source token-id DRAM base, raw uint32 ids padded to 1024 entries
    s2: destination activation DRAM base
    s3: first output col tile for this core
    s4: number of col tiles for this core
    s5: logical sequence length, <= 1024
    s6: DRAM bank count
    s11: reserved

  Source layout is tilized `(vocab, 2048)`. Llama 3.2 1B has vocab and hidden
  dims divisible by 32, so there is no model-dimension padding here.

  Destination layout is tiled `(1024, 2048)`. Only rows `< seq_len` are written;
  padded rows are left as-is, normally zeroed by the caller.
  """
  fw = Brisc()
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s2, s3, s4, s5, s6, s11))

  fw.local_noc0_coord(a5)
  fw.li(s7, 0)
  row_loop = fw._new_label("embedding_row")
  row_done = fw._new_label("embedding_done")
  fw.label(row_loop)
  fw.bgeu(s7, s5, row_done)

  _read_token_id(fw, bank_coords)
  fw.srli(s9, s8, 5)      # source tile row = token // 32
  _row_offset_from_32(fw, s8, s10)
  _row_offset_from_32(fw, s7, a3)

  fw.li(a6, 0)
  col_loop = fw._new_label("embedding_col")
  col_done = fw._new_label("embedding_col_done")
  fw.label(col_loop)
  fw.bgeu(a6, s4, col_done)
  fw.add(t6, s3, a6)      # col tile

  # Source tile id = (token // 32) * 64 + col_tile.
  fw.slli(t2, s8, 6)
  fw.slli(t2, s9, 6)
  fw.add(t2, t2, t6)
  fw.mv(a0, s0)
  fw.mv(a1, t2)
  fw.mv(a2, s6)
  _dram_tile_addr_static(fw, bank_coords)
  fw.add(t3, a0, s9)      # source chunk 0 address
  fw.add(t3, a0, s10)     # source chunk 0 address
  fw.mv(t4, a2)           # source DRAM NOC coord

  # Destination tile id = (sequence row // 32) * 64 + col_tile.
  fw.srli(t2, s7, 5)
  fw.slli(t2, t2, 6)
  fw.add(t2, t2, t6)
  fw.mv(a0, s1)
  fw.mv(a0, s2)
  fw.mv(a1, t6)
  fw.mv(a1, t2)
  fw.mv(a2, s6)
  _dram_tile_addr_static(fw, bank_coords)
  fw.mv(t5, a0)           # destination chunk 0 address
  fw.add(t5, t5, a3)      # destination chunk 0 address
  fw.mv(a7, a2)           # destination DRAM NOC coord

  fw.li(t2, SCRATCH_L1)
  fw.add(t2, t2, s10)
  fw.li(t6, SCRATCH_L1)
  fw.add(t6, t6, a3)
  _copy_32b(fw)
  fw.addi(t3, t3, FACE_BYTES)
  fw.addi(t5, t5, FACE_BYTES)
  fw.addi(t2, t2, FACE_BYTES)
  fw.addi(t6, t6, FACE_BYTES)
  _copy_32b(fw)

  fw.addi(a6, a6, 1)
  fw.j(col_loop)
  fw.label(col_done)

  fw.addi(s7, s7, 1)
  fw.j(row_loop)
  fw.label(row_done)
  return fw.ret()


def build_program(
  embed_addr: int,
  token_addr: int,
  dst_addr: int,
  num_banks: int,
  *,
  seq_len: int,
  cores: list[Core] | None = None,
  bank_coords_noc0: list[int] | None = None,
) -> Program:
  if cores is None:
    cores = [TARGET_CORE]
  if bank_coords_noc0 is None:
    bank_coords_noc0 = p100_dram_bank_endpoint_coords(None, 0)[:num_banks]
  if not 0 <= seq_len <= MAX_SEQ_LEN:
    raise ValueError(f"seq_len must be in [0, {MAX_SEQ_LEN}]")

  core_index = {core: i for i, core in enumerate(cores)}

  def tile_range(core: Core) -> tuple[int, int]:
    idx = core_index[core]
    start = (COL_TILES * idx) // len(cores)
    end = (COL_TILES * (idx + 1)) // len(cores)
    return start, end - start

  brisc_fw = embedding_gather_brisc(bank_coords_noc0)
  brisc_fw.rta(lambda x, y: [
    embed_addr, token_addr, dst_addr,
    tile_range((x, y))[0], tile_range((x, y))[1],
    seq_len, num_banks, 0,
  ])

  prog = Program(
    brisc=brisc_fw,
    ncrisc=_empty_kernel(),
    trisc0=_empty_kernel(),
    trisc1=_empty_kernel(),
    trisc2=_empty_kernel(),
    core_order=tuple(cores),
  )
  prog.name = "llama_embedding_gather"
  return prog


def row_chunk_offsets(row: int) -> tuple[int, int]:
  in_face_row = row & 15
  row_half = row >> 4
  base = row_half * 2 * FACE_BYTES + in_face_row * ROW_CHUNK_BYTES
  return base, base + FACE_BYTES


def reference_gather_tiled(table_tilized: bytes, token_id: int, *, emb_dim: int = EMB_DIM) -> bytes:
  if emb_dim % TILE_C:
    raise ValueError("emb_dim must be a multiple of 32")
  col_tiles = emb_dim // TILE_C
  src_row_tile = token_id // TILE_R
  src_row = token_id % TILE_R
  src_off0, src_off1 = row_chunk_offsets(src_row)
  dst_off0, dst_off1 = row_chunk_offsets(0)

  out = bytearray(col_tiles * TILE_BYTES)
  for col_tile in range(col_tiles):
    src_tile = src_row_tile * col_tiles + col_tile
    src_base = src_tile * TILE_BYTES
    dst_base = col_tile * TILE_BYTES
    out[dst_base + dst_off0 : dst_base + dst_off0 + ROW_CHUNK_BYTES] = (
      table_tilized[src_base + src_off0 : src_base + src_off0 + ROW_CHUNK_BYTES]
    )
    out[dst_base + dst_off1 : dst_base + dst_off1 + ROW_CHUNK_BYTES] = (
      table_tilized[src_base + src_off1 : src_base + src_off1 + ROW_CHUNK_BYTES]
    )
  return bytes(out)


def reference_gather_sequence_tiled(table_tilized: bytes, tokens: np.ndarray, seq_len: int, *, emb_dim: int = EMB_DIM) -> bytes:
  if emb_dim % TILE_C:
    raise ValueError("emb_dim must be a multiple of 32")
  if len(tokens) != MAX_SEQ_LEN:
    raise ValueError(f"tokens must be padded to {MAX_SEQ_LEN}")
  col_tiles = emb_dim // TILE_C
  out = bytearray(OUT_TILES * TILE_BYTES)
  for row in range(seq_len):
    token_id = int(tokens[row])
    src_row_tile = token_id // TILE_R
    src_row = token_id % TILE_R
    dst_row_tile = row // TILE_R
    dst_row = row % TILE_R
    src_off0, src_off1 = row_chunk_offsets(src_row)
    dst_off0, dst_off1 = row_chunk_offsets(dst_row)
    for col_tile in range(col_tiles):
      src_tile = src_row_tile * col_tiles + col_tile
      dst_tile = dst_row_tile * col_tiles + col_tile
      src_base = src_tile * TILE_BYTES
      dst_base = dst_tile * TILE_BYTES
      out[dst_base + dst_off0 : dst_base + dst_off0 + ROW_CHUNK_BYTES] = (
        table_tilized[src_base + src_off0 : src_base + src_off0 + ROW_CHUNK_BYTES]
      )
      out[dst_base + dst_off1 : dst_base + dst_off1 + ROW_CHUNK_BYTES] = (
        table_tilized[src_base + src_off1 : src_base + src_off1 + ROW_CHUNK_BYTES]
      )
  return bytes(out)


def host_check(seq_len: int, rows: int) -> None:
  rows = ((rows + TILE_R - 1) // TILE_R) * TILE_R
  if not 0 <= seq_len <= MAX_SEQ_LEN:
    raise ValueError(f"seq_len must be in [0, {MAX_SEQ_LEN}]")
  table = make_host_table(rows)
  tokens = make_tokens(seq_len, rows)
  gathered = reference_gather_sequence_tiled(tilize(table.tobytes(), BF16_BYTES, table.shape), tokens, seq_len)
  check_gathered_sequence(gathered, table, tokens, seq_len)


def make_host_table(rows: int) -> np.ndarray:
  return np.arange(rows * EMB_DIM, dtype=np.uint16).reshape(rows, EMB_DIM)


def make_tokens(seq_len: int, rows: int) -> np.ndarray:
  tokens = np.zeros(MAX_SEQ_LEN, dtype=np.uint32)
  seed = [0, 1, 15, 16, 17, 31, 32, 33, 63, 64, 127, 128]
  for i in range(seq_len):
    tokens[i] = seed[i] % rows if i < len(seed) else (i * 37 + 17) % rows
  return tokens


def check_gathered_row(gathered: bytes, expected: np.ndarray) -> None:
  got = np.empty(EMB_DIM, dtype=np.uint16)
  for col_tile in range(COL_TILES):
    dst_base = col_tile * TILE_BYTES
    dst_off0, dst_off1 = row_chunk_offsets(0)
    got[col_tile * TILE_C : col_tile * TILE_C + 16] = np.frombuffer(
      gathered[dst_base + dst_off0 : dst_base + dst_off0 + ROW_CHUNK_BYTES],
      dtype=np.uint16,
    )
    got[col_tile * TILE_C + 16 : col_tile * TILE_C + TILE_C] = np.frombuffer(
      gathered[dst_base + dst_off1 : dst_base + dst_off1 + ROW_CHUNK_BYTES],
      dtype=np.uint16,
    )

  if not np.array_equal(got, expected):
    mismatch = int(np.flatnonzero(got != expected)[0])
    raise AssertionError(
      f"gathered row mismatch at col {mismatch}: got=0x{int(got[mismatch]):04x} "
      f"expected=0x{int(expected[mismatch]):04x}"
    )


def check_gathered_sequence(gathered: bytes, table: np.ndarray, tokens: np.ndarray, seq_len: int) -> None:
  for row in range(seq_len):
    dst_row_tile = row // TILE_R
    dst_row = row % TILE_R
    dst_off0, dst_off1 = row_chunk_offsets(dst_row)
    got = np.empty(EMB_DIM, dtype=np.uint16)
    for col_tile in range(COL_TILES):
      dst_tile = dst_row_tile * COL_TILES + col_tile
      dst_base = dst_tile * TILE_BYTES
      got[col_tile * TILE_C : col_tile * TILE_C + 16] = np.frombuffer(
        gathered[dst_base + dst_off0 : dst_base + dst_off0 + ROW_CHUNK_BYTES],
        dtype=np.uint16,
      )
      got[col_tile * TILE_C + 16 : col_tile * TILE_C + TILE_C] = np.frombuffer(
        gathered[dst_base + dst_off1 : dst_base + dst_off1 + ROW_CHUNK_BYTES],
        dtype=np.uint16,
      )
    expected = table[int(tokens[row])]
    if not np.array_equal(got, expected):
      mismatch = int(np.flatnonzero(got != expected)[0])
      raise AssertionError(
        f"sequence gather mismatch at row {row}, col {mismatch}: "
        f"token={int(tokens[row])} got=0x{int(got[mismatch]):04x} "
        f"expected=0x{int(expected[mismatch]):04x}"
      )

  pad_start = (seq_len + TILE_R - 1) // TILE_R * TILE_R
  if seq_len < MAX_SEQ_LEN and any(gathered[pad_start * EMB_DIM * BF16_BYTES:]):
    raise AssertionError("padded output rows are not zero")


def run_device_check(seq_len: int, rows: int, cores: list[Core] | None, core_count: int | None) -> None:
  rows = ((rows + TILE_R - 1) // TILE_R) * TILE_R
  if not 0 <= seq_len <= MAX_SEQ_LEN:
    raise ValueError(f"seq_len must be in [0, {MAX_SEQ_LEN}]")
  table = make_host_table(rows)
  tokens = make_tokens(seq_len, rows)
  src_tiled = tilize(table.tobytes(), BF16_BYTES, table.shape)
  expected = reference_gather_sequence_tiled(src_tiled, tokens, seq_len)

  device = Device()
  try:
    if cores is not None:
      run_cores = cores
    elif core_count is not None:
      run_cores = device.cores[:core_count]
    else:
      run_cores = [TARGET_CORE]
    num_banks = len(device.dram.bank_tiles)
    src_buf = device.dram.alloc(len(src_tiled) // TILE_BYTES, Dtype.Float16_b, name="embed")
    token_buf = device.dram.alloc((MAX_SEQ_LEN * TOKEN_BYTES) // TILE_BYTES, Dtype.Float16_b, name="tokens")
    dst_buf = device.dram.alloc(OUT_TILES, Dtype.Float16_b, name="activation")
    device.dram_write(src_buf, src_tiled)
    device.dram_write(token_buf, tokens.tobytes())
    device.dram_write(dst_buf, bytes(dst_buf.size))

    prog = build_program(
      src_buf.addr,
      token_buf.addr,
      dst_buf.addr,
      num_banks,
      seq_len=seq_len,
      cores=run_cores,
      bank_coords_noc0=p100_dram_bank_endpoint_coords(device.board_info.harvested_dram_bank, 0)[:num_banks],
    )
    timings = device.run(prog)
    got = device.dram_read(dst_buf)
    if got != expected:
      mismatch = next(i for i, (g, e) in enumerate(zip(got, expected)) if g != e)
      raise AssertionError(f"device tiled output mismatch at byte {mismatch}: got=0x{got[mismatch]:02x} expected=0x{expected[mismatch]:02x}")
    check_gathered_sequence(got, table, tokens, seq_len)
    for timing in timings:
      name = f"{timing['name']}: " if timing["name"] else ""
      print(f"  {name}{timing['us']:,.1f} us")
  finally:
    device.close()


def parse_core(value: str) -> Core:
  try:
    x, y = value.split(",", 1)
    return int(x, 0), int(y, 0)
  except ValueError as e:
    raise argparse.ArgumentTypeError("core must be X,Y") from e


def main() -> None:
  parser = argparse.ArgumentParser(description="Llama embedding gather kernel.")
  parser.add_argument("--seq-len", type=int, default=17)
  parser.add_argument("--table-rows", type=int, default=1024)
  parser.add_argument("--embed-addr", type=lambda x: int(x, 0), default=0x40)
  parser.add_argument("--token-addr", type=lambda x: int(x, 0), default=0x100000)
  parser.add_argument("--dst-addr", type=lambda x: int(x, 0), default=0x200000)
  parser.add_argument("--num-banks", type=int, default=8)
  parser.add_argument("--core", type=parse_core, action="append", dest="cores")
  parser.add_argument("--core-count", type=int, default=None)
  parser.add_argument("--run", action="store_true", help="run the kernel through Device")
  parser.add_argument("--hardware", action="store_true", help="allow --run without EMU=1")
  args = parser.parse_args()

  host_check(args.seq_len, args.table_rows)
  if args.run:
    if os.environ.get("EMU") != "1" and not args.hardware:
      raise RuntimeError("--run without EMU=1 needs --hardware")
    run_device_check(args.seq_len, args.table_rows, args.cores, args.core_count)
    print("device-check: ok")

  prog = build_program(
    args.embed_addr,
    args.token_addr,
    args.dst_addr,
    args.num_banks,
    seq_len=args.seq_len,
    cores=args.cores or [TARGET_CORE],
  )
  segments = prog.layout(core_xy=(args.cores or [TARGET_CORE])[0])
  text_bytes = sum(len(seg.data) for seg in segments if ".text" in seg.label or seg.label.endswith("text"))
  print(f"compiled {prog.name}: {len(segments)} segments, {text_bytes} text bytes")
  print("host-check: ok")


if __name__ == "__main__":
  main()
