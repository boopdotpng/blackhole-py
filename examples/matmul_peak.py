#!/usr/bin/env python3
import os, sys, time
from dataclasses import dataclass
import numpy as np

from l1 import *
from program import *
from device import Device
from dram import DramBuffer

IO_MODE = "f16" if os.environ.get("F16") == "1" else "bf16"
# Blackhole does not have a real f32 matmul path. F32_ACC only enables the
# internal DEST-accum variant for this benchmark while IO stays f16/bf16.
F32_ACC = os.environ.get("F32_ACC") == "1"
IO_DTYPE = Dtype.Float16 if IO_MODE == "f16" else Dtype.Float16_b
_MATH_FIDELITY_MAP = {"lofi": MathFidelity.LoFi, "hifi2": MathFidelity.HiFi2}
MATH_FIDELITY_NAME = os.environ.get("MATH_FIDELITY", "hifi2").lower()
MATH_FIDELITY = _MATH_FIDELITY_MAP.get(MATH_FIDELITY_NAME)
if MATH_FIDELITY is None:
  raise SystemExit(f"Invalid MATH_FIDELITY={MATH_FIDELITY_NAME!r}. Expected: {', '.join(_MATH_FIDELITY_MAP)}")

NUM_ITERS = int(os.environ.get("NUM_ITERS", "3"))
INPUT_PATTERN = os.environ.get("INPUT_PATTERN", "random").lower()
VALIDATE_SAMPLES = max(1, int(os.environ.get("VALIDATE_SAMPLES", "64")))
VALIDATE_SEED = int(os.environ.get("VALIDATE_SEED", "0"))

# --- matmul planner ---

L1_DATA_BYTES = TensixL1.SIZE - TensixL1.DATA_BUFFER_SPACE_BASE
NUM_SEMS = 4

def _divisors(n):
  divs = []
  for i in range(1, int(n**0.5) + 1):
    if n % i == 0:
      divs.append(i)
      if i != n // i:
        divs.append(n // i)
  return sorted(divs)

def _ceil32(x):
  return (x + 31) & ~31

@dataclass(frozen=True)
class MatmulPlan:
  rows: tuple[int, ...]
  cols: tuple[int, ...]
  mt: int; kt: int; nt: int
  per_core_m: int; per_core_n: int
  in0_block_w: int
  out_subblock_h: int; out_subblock_w: int; out_subblock_num_tiles: int
  num_blocks: int
  in0_num_subblocks: int; in1_num_subblocks: int
  in0_block_num_tiles: int; in0_subblock_num_tiles: int
  in1_block_num_tiles: int; in1_per_core_w: int
  out_block_num_tiles: int
  cb0_pages: int; cb1_pages: int; cb16_pages: int; cb24_pages: int

  @property
  def num_rows(self) -> int: return len(self.rows)
  @property
  def num_cols(self) -> int: return len(self.cols)
  @property
  def active_core_count(self) -> int: return self.num_rows * self.num_cols

  def grid(self) -> list[list[Core]]:
    return [[(x, y) for x in self.cols] for y in self.rows]
  def active_cores(self) -> list[Core]:
    return [c for row in self.grid() for c in row]

def plan_matmul(M: int, K: int, N: int, cores: list[Core], io_dtype: Dtype = Dtype.Float16_b, f32_acc: bool = False) -> MatmulPlan:
  mt_base, kt, nt_base = _ceil32(M) // 32, _ceil32(K) // 32, max(1, _ceil32(N) // 32)
  tile_bytes = io_dtype.tile_size
  cb24_tile_bytes = Dtype.Float32.tile_size if f32_acc else tile_bytes

  ordered = sorted(set(cores), key=lambda xy: (xy[0], xy[1]))
  if not ordered: raise SystemExit("No cores")
  core_set = frozenset(ordered)
  xs = tuple(sorted({x for x, _ in ordered}))
  ys = tuple(sorted({y for _, y in ordered}))

  def fits_l1(pcm, pcn, bw):
    cb0 = 2 * pcm * bw * tile_bytes
    cb1 = 2 * pcn * bw * tile_bytes
    cb_out = max(pcm * pcn * tile_bytes, pcm * pcn * cb24_tile_bytes)
    return cb0 + cb1 + cb_out <= L1_DATA_BYTES

  max_bw_cap = (1 << 30) if f32_acc else None
  kt_divs = _divisors(kt)
  best, best_score = None, None

  for y_start in range(len(ys)):
    for y_stop in range(y_start + 1, len(ys) + 1):
      rows = ys[y_start:y_stop]
      valid_cols = [x for x in xs if all((x, y) in core_set for y in rows)]
      if not valid_cols: continue
      for nc in range(1, len(valid_cols) + 1):
        cols = tuple(valid_cols[:nc])
        nr = len(rows)
        if nr * nc > len(cores): continue
        pcm = (mt_base + nr - 1) // nr
        pcn = (nt_base + nc - 1) // nc
        mt, nt = nr * pcm, nc * pcn
        out_tiles = pcm * pcn
        bw_cap = max_bw_cap or (32 if out_tiles <= 16 else 64)
        for sbh in range(1, 9):
          for sbw in range(1, 9):
            if sbh * sbw > 8 or pcm % sbh != 0 or pcn % sbw != 0: continue
            for bw in kt_divs:
              if bw > bw_cap or not fits_l1(pcm, pcn, bw): continue
              bias = min(out_tiles, 16)
              score = (nr * nc * bw * bias * bias, -(mt * nt), nr * nc * bw, sbh * sbw, nr * nc)
              if best_score is None or score > best_score:
                best = (rows, cols, mt, nt, pcm, pcn, bw, sbh, sbw)
                best_score = score

  if best is None:
    raise SystemExit(f"No valid matmul plan for Mt={mt_base} Kt={kt} Nt={nt_base}")
  rows, cols, mt, nt, pcm, pcn, bw, sbh, sbw = best
  return MatmulPlan(
    rows=rows, cols=cols, mt=mt, kt=kt, nt=nt, per_core_m=pcm, per_core_n=pcn,
    in0_block_w=bw, out_subblock_h=sbh, out_subblock_w=sbw, out_subblock_num_tiles=sbh * sbw,
    num_blocks=kt // bw, in0_num_subblocks=pcm // sbh, in1_num_subblocks=pcn // sbw,
    in0_block_num_tiles=pcm * bw, in0_subblock_num_tiles=sbh * bw,
    in1_block_num_tiles=pcn * bw, in1_per_core_w=pcn, out_block_num_tiles=pcm * pcn,
    cb0_pages=2 * pcm * bw, cb1_pages=2 * pcn * bw, cb16_pages=pcm * pcn, cb24_pages=pcm * pcn,
  )

# --- kernel templates ---

_OUTPUT_WRITE_LOOP = """\
  uint32_t sbh_start = out_start;
  for (uint32_t sbh = 0; sbh < out_num_sb_h; sbh++) {{
  uint32_t sbw_start = sbh_start;
  for (uint32_t sbw = 0; sbw < out_num_sb_w; sbw++) {{
    cb_wait_front(cb_out, out_sb_tiles);
    uint32_t l1_addr = get_read_ptr(cb_out);
    uint32_t row_start = sbw_start;
    for (uint32_t h = 0; h < out_sb_h; h++) {{
    uint32_t tile_id = row_start;
    for (uint32_t w = 0; w < out_sb_w; w++) {{
      noc_async_write_tile(tile_id, out_gen, l1_addr);
      l1_addr += tile_bytes;
      tile_id += out_stride_w;
    }}
    row_start += out_stride_h;
    }}
    noc_async_write_barrier();
    cb_pop_front(cb_out, out_sb_tiles);
    sbw_start += out_next_sb_w;
  }}
  sbh_start += out_next_sb_h;
  }}"""

def _mcast_rect_args(x_list, y):
  return (min(x_list), y, max(x_list), y, len(x_list)) if x_list else (0, 0, 0, 0, 0)

def _reader_sender_src(data_format):
  return f"""\
#include <cstdint>
#define A(n) get_arg_val<uint32_t>(n)
#define SEM(n) reinterpret_cast<volatile tt_l1_ptr uint32_t*>(get_semaphore(A(n)))

void kernel_main() {{
  const uint32_t tile_bytes = get_tile_size(tt::CBIndex::c_0);
  const uint32_t block_w = A(5), block_h = A(6), block_tiles = A(7), nblocks = A(8);
  const uint32_t w_nd = A(13), e_nd = A(18);
  volatile tt_l1_ptr uint32_t* sender_sem = SEM(21);
  volatile tt_l1_ptr uint32_t* recv_sem = SEM(22);
  *recv_sem = VALID;
  const InterleavedAddrGenFast<true> in0_gen = {{
  .bank_base_address = A(0), .page_size = tile_bytes, .data_format = DataFormat::{data_format},
  }};
  uint32_t cur_block = A(1);
  for (uint32_t block = 0; block < nblocks; block++) {{
  cb_reserve_back(tt::CBIndex::c_0, block_tiles);
  uint32_t l1_addr = get_write_ptr(tt::CBIndex::c_0);
  uint32_t start_addr = l1_addr;
  uint32_t row = cur_block;
  uint32_t block_bytes = 0;
  for (uint32_t h = 0; h < block_h; h++) {{
    uint32_t tile_id = row;
    for (uint32_t w = 0; w < block_w; w++) {{
    noc_async_read_tile(tile_id, in0_gen, l1_addr);
    l1_addr += tile_bytes;
    tile_id += A(2);
    block_bytes += tile_bytes;
    }}
    row += A(3);
  }}
  cur_block += A(4);
  noc_async_read_barrier();
  noc_semaphore_wait(sender_sem, w_nd + e_nd);
  noc_semaphore_set(sender_sem, 0);
  if (w_nd > 0) {{
    uint64_t wa = get_noc_multicast_addr(A(9), A(10), A(11), A(12), start_addr);
    noc_async_write_multicast(start_addr, wa, block_bytes, w_nd);
    noc_async_writes_flushed();
    noc_semaphore_set_multicast(get_semaphore(A(22)), get_noc_multicast_addr(A(9), A(10), A(11), A(12), get_semaphore(A(22))), w_nd);
  }}
  if (e_nd > 0) {{
    uint64_t ea = get_noc_multicast_addr(A(14), A(15), A(16), A(17), start_addr);
    noc_async_write_multicast(start_addr, ea, block_bytes, e_nd);
    noc_async_writes_flushed();
    noc_semaphore_set_multicast(get_semaphore(A(22)), get_noc_multicast_addr(A(14), A(15), A(16), A(17), get_semaphore(A(22))), e_nd);
  }}
  cb_push_back(tt::CBIndex::c_0, block_tiles);
  }}
}}"""

_READER_RECV_SRC = """\
#include <cstdint>
#define A(n) get_arg_val<uint32_t>(n)
#define SEM(n) reinterpret_cast<volatile tt_l1_ptr uint32_t*>(get_semaphore(A(n)))

void kernel_main() {
  const uint32_t block_tiles = A(7), nblocks = A(8);
  volatile tt_l1_ptr uint32_t* recv_sem = SEM(22);
  for (uint32_t block = 0; block < nblocks; block++) {
  cb_reserve_back(tt::CBIndex::c_0, block_tiles);
  noc_semaphore_set(recv_sem, INVALID);
  noc_semaphore_inc(get_noc_addr(A(19), A(20), get_semaphore(A(21))), 1);
  noc_semaphore_wait(recv_sem, VALID);
  cb_push_back(tt::CBIndex::c_0, block_tiles);
  }
}"""

def _writer_sender_src(data_format):
  return f"""\
#include <cstdint>
#define A(n) get_arg_val<uint32_t>(n)
#define SEM(n) reinterpret_cast<volatile tt_l1_ptr uint32_t*>(get_semaphore(A(n)))

void kernel_main() {{
  constexpr uint32_t cb_out = tt::CBIndex::c_16;
  const uint32_t tile_bytes = get_tile_size(tt::CBIndex::c_1);
  const uint32_t block_w = A(5), block_h = A(6), block_tiles = A(7), nblocks = A(8), i1_nd = A(13);
  const uint32_t out_start = A(19), out_stride_w = A(20), out_stride_h = A(21);
  const uint32_t out_next_sb_w = A(22), out_next_sb_h = A(23);
  const uint32_t out_sb_w = A(24), out_sb_h = A(25), out_sb_tiles = A(26);
  const uint32_t out_num_sb_w = A(27), out_num_sb_h = A(28);
  volatile tt_l1_ptr uint32_t* sender_sem = SEM(16);
  volatile tt_l1_ptr uint32_t* recv_sem = SEM(17);
  *recv_sem = VALID;
  const InterleavedAddrGenFast<true> in1_gen = {{
  .bank_base_address = A(0), .page_size = tile_bytes, .data_format = DataFormat::{data_format},
  }};
  const InterleavedAddrGenFast<true> out_gen = {{
  .bank_base_address = A(18), .page_size = tile_bytes, .data_format = DataFormat::{data_format},
  }};
  uint32_t cur_block = A(1);
  for (uint32_t block = 0; block < nblocks; block++) {{
  cb_reserve_back(tt::CBIndex::c_1, block_tiles);
  uint32_t l1_addr = get_write_ptr(tt::CBIndex::c_1);
  uint32_t start_addr = l1_addr;
  uint32_t row = cur_block;
  uint32_t block_bytes = 0;
  for (uint32_t h = 0; h < block_h; h++) {{
    uint32_t tile_id = row;
    for (uint32_t w = 0; w < block_w; w++) {{
    noc_async_read_tile(tile_id, in1_gen, l1_addr);
    l1_addr += tile_bytes;
    tile_id += A(2);
    block_bytes += tile_bytes;
    }}
    row += A(3);
  }}
  cur_block += A(4);
  noc_async_read_barrier();
  noc_semaphore_wait(sender_sem, i1_nd);
  noc_semaphore_set(sender_sem, 0);
  if (i1_nd > 0) {{
    uint64_t ma = get_noc_multicast_addr(A(9), A(10), A(11), A(12), start_addr);
    noc_async_write_multicast(start_addr, ma, block_bytes, i1_nd);
    noc_async_writes_flushed();
    noc_semaphore_set_multicast(get_semaphore(A(17)), get_noc_multicast_addr(A(9), A(10), A(11), A(12), get_semaphore(A(17))), i1_nd);
  }}
  cb_push_back(tt::CBIndex::c_1, block_tiles);
  }}
{_OUTPUT_WRITE_LOOP}
}}"""

def _writer_recv_src(data_format):
  return f"""\
#include <cstdint>
#define A(n) get_arg_val<uint32_t>(n)
#define SEM(n) reinterpret_cast<volatile tt_l1_ptr uint32_t*>(get_semaphore(A(n)))

void kernel_main() {{
  constexpr uint32_t cb_out = tt::CBIndex::c_16;
  const uint32_t tile_bytes = get_tile_size(tt::CBIndex::c_1);
  const uint32_t block_tiles = A(7), nblocks = A(8);
  const uint32_t out_start = A(19), out_stride_w = A(20), out_stride_h = A(21);
  const uint32_t out_next_sb_w = A(22), out_next_sb_h = A(23);
  const uint32_t out_sb_w = A(24), out_sb_h = A(25), out_sb_tiles = A(26);
  const uint32_t out_num_sb_w = A(27), out_num_sb_h = A(28);
  const InterleavedAddrGenFast<true> out_gen = {{
  .bank_base_address = A(18), .page_size = tile_bytes, .data_format = DataFormat::{data_format},
  }};
  volatile tt_l1_ptr uint32_t* recv_sem = SEM(17);
  for (uint32_t block = 0; block < nblocks; block++) {{
  cb_reserve_back(tt::CBIndex::c_1, block_tiles);
  noc_semaphore_set(recv_sem, INVALID);
  noc_semaphore_inc(get_noc_addr(A(14), A(15), get_semaphore(A(16))), 1);
  noc_semaphore_wait(recv_sem, VALID);
  cb_push_back(tt::CBIndex::c_1, block_tiles);
  }}
{_OUTPUT_WRITE_LOOP}
}}"""

def _compute_src(plan: MatmulPlan, f32_acc: bool):
  if f32_acc:
    mode_defines = "#define FP32_DEST_ACC_EN 1\n"
    pack_include = '#include "compute_kernel_api/pack.h"\n'
    reload_init = "copy_tile_to_dst_init_short_with_dt(tt::CBIndex::c_1, tt::CBIndex::c_24);"
    mm_short = """mm_block_init_short_with_dt(
      tt::CBIndex::c_0, tt::CBIndex::c_1, tt::CBIndex::c_24,
      transpose, out_subblock_w, out_subblock_h, in0_block_w);"""
    pack16_reconfig = "PACK((pack_reconfig_data_format(tt::CBIndex::c_16)));"
    pack24_reconfig = "PACK((pack_reconfig_data_format(tt::CBIndex::c_24)));"
  else:
    mode_defines = ""
    pack_include = ""
    reload_init = "copy_tile_to_dst_init_short(tt::CBIndex::c_24);"
    mm_short = """mm_block_init_short(
      tt::CBIndex::c_0, tt::CBIndex::c_1,
      transpose, out_subblock_w, out_subblock_h, in0_block_w);"""
    pack16_reconfig = ""
    pack24_reconfig = ""
  return f"""\
#include <cstdint>
{mode_defines}#define PACKER_L1_ACC 1
#include "compute_kernel_api/matmul.h"
{pack_include}#include "compute_kernel_api/tile_move_copy.h"

namespace NAMESPACE {{
void MAIN {{
  constexpr uint32_t in0_block_w = {plan.in0_block_w};
  constexpr uint32_t in0_num_subblocks = {plan.in0_num_subblocks};
  constexpr uint32_t in0_block_num_tiles = {plan.in0_block_num_tiles};
  constexpr uint32_t in0_subblock_num_tiles = {plan.in0_subblock_num_tiles};
  constexpr uint32_t in1_num_subblocks = {plan.in1_num_subblocks};
  constexpr uint32_t in1_block_num_tiles = {plan.in1_block_num_tiles};
  constexpr uint32_t in1_per_core_w = {plan.in1_per_core_w};
  constexpr uint32_t num_blocks = {plan.num_blocks};
  constexpr uint32_t out_subblock_h = {plan.out_subblock_h};
  constexpr uint32_t out_subblock_w = {plan.out_subblock_w};
  constexpr uint32_t out_subblock_num_tiles = {plan.out_subblock_num_tiles};
  constexpr uint32_t out_block_num_tiles = {plan.out_block_num_tiles};
  constexpr uint32_t transpose = 0;
  mm_block_init(tt::CBIndex::c_0, tt::CBIndex::c_1, tt::CBIndex::c_16,
  transpose, out_subblock_w, out_subblock_h, in0_block_w);
  bool enable_reload = false;
  uint32_t out_num_tiles_to_wait = out_subblock_num_tiles;
  for (uint32_t block = 0; block < num_blocks; block++) {{
  const bool last_out = (block == (num_blocks - 1));
  cb_wait_front(tt::CBIndex::c_0, in0_block_num_tiles);
  cb_wait_front(tt::CBIndex::c_1, in1_block_num_tiles);
  int in0_index_subblock_offset = 0;
  for (uint32_t in0_sb = 0; in0_sb < in0_num_subblocks; in0_sb++) {{
    int in1_index_subblock_offset = 0;
    for (uint32_t in1_sb = 0; in1_sb < in1_num_subblocks; in1_sb++) {{
    tile_regs_acquire();
    if (enable_reload) {{
      {reload_init}
      cb_wait_front(tt::CBIndex::c_24, out_subblock_num_tiles);
      #pragma GCC unroll 0
      for (uint32_t i = 0; i < out_subblock_num_tiles; i++) {{ copy_tile(tt::CBIndex::c_24, i, i); }}
      cb_pop_front(tt::CBIndex::c_24, out_subblock_num_tiles);
      {mm_short}
    }}
    #pragma GCC unroll 0
    for (uint32_t inner = 0; inner < in0_block_w; inner++) {{
      const uint32_t in0_tile_index = (uint32_t)(in0_index_subblock_offset + (int)inner);
      const uint32_t in1_tile_index = (uint32_t)(in1_index_subblock_offset + (int)(inner * in1_per_core_w));
      matmul_block(tt::CBIndex::c_0, tt::CBIndex::c_1,
      in0_tile_index, in1_tile_index, 0, transpose, out_subblock_w, out_subblock_h, in0_block_w);
    }}
    tile_regs_commit();
    if (last_out) {{
      cb_reserve_back(tt::CBIndex::c_16, out_subblock_num_tiles);
      tile_regs_wait();
      {pack16_reconfig}
      PACK((llk_pack_reconfig_l1_acc(0)));
      #pragma GCC unroll 0
      for (uint32_t i = 0; i < out_subblock_num_tiles; i++) {{ pack_tile(i, tt::CBIndex::c_16); }}
      tile_regs_release();
      cb_push_back(tt::CBIndex::c_16, out_subblock_num_tiles);
    }} else {{
      if (block == 0) {{
      cb_reserve_back(tt::CBIndex::c_16, out_num_tiles_to_wait);
      out_num_tiles_to_wait += out_subblock_num_tiles;
      }}
      cb_reserve_back(tt::CBIndex::c_24, out_subblock_num_tiles);
      tile_regs_wait();
      if (block == 0) {{ {pack24_reconfig} PACK((llk_pack_reconfig_l1_acc(0))); }}
      else if (block == 1) {{ PACK((llk_pack_reconfig_l1_acc(1))); }}
      #pragma GCC unroll 0
      for (uint32_t i = 0; i < out_subblock_num_tiles; i++) {{ pack_tile(i, tt::CBIndex::c_24); }}
      tile_regs_release();
      cb_push_back(tt::CBIndex::c_24, out_subblock_num_tiles);
    }}
    in1_index_subblock_offset += out_subblock_w;
    }}
    in0_index_subblock_offset += in0_subblock_num_tiles;
  }}
  if (num_blocks > 2 && block < num_blocks - 2) {{
    cb_wait_front(tt::CBIndex::c_24, out_block_num_tiles);
    cb_pop_front(tt::CBIndex::c_24, out_block_num_tiles);
  }}
  if (num_blocks >= 2 && block == num_blocks - 2) enable_reload = true;
  cb_pop_front(tt::CBIndex::c_0, in0_block_num_tiles);
  cb_pop_front(tt::CBIndex::c_1, in1_block_num_tiles);
  }}
}}
}} // namespace NAMESPACE"""

# --- build matmul program ---

def build_matmul_program(
  plan: MatmulPlan, a: DramBuffer, b: DramBuffer, c: DramBuffer,
  io_dtype: Dtype = Dtype.Float16_b, math_fidelity: MathFidelity = MathFidelity.HiFi2, f32_acc: bool = False,
) -> Program:
  df = io_dtype.name
  cb24_dtype = Dtype.Float32 if f32_acc else io_dtype
  M, K, N = plan.mt * 32, plan.kt * 32, plan.nt * 32

  grid = plan.grid()
  rows, cols = plan.rows, plan.cols
  core_to_rc = {grid[r][c]: (r, c) for r in range(len(rows)) for c in range(len(cols))}
  west_cols = [x for x in cols if x < 8]
  east_cols = [x for x in cols if x >= 10]

  def reader_args(core_idx, core_xy, num_cores):
    ri, _ = core_to_rc[core_xy]
    w_rect = _mcast_rect_args([c for c in west_cols if c != cols[0]], core_xy[1])
    e_rect = _mcast_rect_args(list(east_cols), core_xy[1])
    sender_xy = grid[ri][0]
    return [
      a.addr, ri * plan.per_core_m * plan.kt, 1, plan.kt, plan.in0_block_w,
      plan.in0_block_w, plan.per_core_m, plan.in0_block_num_tiles, plan.num_blocks,
      *w_rect, *e_rect, sender_xy[0], sender_xy[1], 0, 1,
    ]

  def writer_args(core_idx, core_xy, num_cores):
    ri, ci = core_to_rc[core_xy]
    recv_ys = rows[1:]
    mcast = (core_xy[0], max(recv_ys), core_xy[0], min(recv_ys), len(recv_ys)) if recv_ys else (0, 0, 0, 0, 0)
    sender_xy = grid[0][ci]
    out_start = ri * plan.per_core_m * plan.nt + ci * plan.per_core_n
    return [
      b.addr, ci * plan.per_core_n, 1, plan.nt, plan.in0_block_w * plan.nt,
      plan.per_core_n, plan.in0_block_w, plan.in1_block_num_tiles, plan.num_blocks,
      *mcast, sender_xy[0], sender_xy[1], 2, 3,
      c.addr, out_start, 1, plan.nt, plan.out_subblock_w, plan.out_subblock_h * plan.nt,
      plan.out_subblock_w, plan.out_subblock_h, plan.out_subblock_num_tiles,
      plan.in1_num_subblocks, plan.in0_num_subblocks,
    ]

  return Program(
    cores="all",
    reader_kernel=_reader_sender_src(df),
    writer_kernel=_writer_sender_src(df),
    compute_kernel=_compute_src(plan, f32_acc),
    reader_recv_kernel=_READER_RECV_SRC,
    writer_recv_kernel=_writer_recv_src(df),
    grid=(rows, cols),
    name=f"matmul_{M}x{K}x{N}",
    cbs=[
      (0, io_dtype.tile_size, plan.cb0_pages),
      (1, io_dtype.tile_size, plan.cb1_pages),
      (16, io_dtype.tile_size, plan.cb16_pages),
      (24, cb24_dtype.tile_size, plan.cb24_pages),
    ],
    reader_args=reader_args,
    writer_args=writer_args,
    math_fidelity=math_fidelity,
    dst_accum_mode=f32_acc,
    dst_full_sync=f32_acc,
    semaphores=NUM_SEMS,
  )

# --- benchmark harness ---

def _host_input_dtype():
  return np.float16 if IO_MODE == "f16" else np.float32

def _to_device_bytes(x: np.ndarray) -> bytes:
  if IO_MODE == "f16":
    return np.ascontiguousarray(x, dtype=np.float16).tobytes()
  u32 = np.ascontiguousarray(x, dtype=np.float32).view(np.uint32)
  return (u32 >> 16).astype(np.uint16).tobytes()

def _from_device_bytes(data: bytes, shape: tuple[int, ...]) -> np.ndarray:
  if IO_MODE == "f16":
    return np.frombuffer(data, dtype=np.float16).astype(np.float32).reshape(shape)
  u16 = np.frombuffer(data, dtype=np.uint16)
  return (u16.astype(np.uint32) << 16).view(np.float32).reshape(shape)

def _sample_coords(M: int, N: int) -> tuple[np.ndarray, np.ndarray]:
  total = M * N
  target = min(total, VALIDATE_SAMPLES)
  fixed = [0, N - 1, (M // 2) * N + (N // 2), (M - 1) * N, total - 1]
  chosen, seen = [], set()
  for idx in fixed:
    if 0 <= idx < total and idx not in seen:
      chosen.append(idx)
      seen.add(idx)
      if len(chosen) == target:
        break
  if len(chosen) < target:
    rng = np.random.default_rng(VALIDATE_SEED)
    while len(chosen) < target:
      idx = int(rng.integers(total))
      if idx not in seen:
        chosen.append(idx)
        seen.add(idx)
  flat = np.asarray(chosen, dtype=np.int64)
  return flat // N, flat % N


def _validate(a, b, c_bytes, M, N, Mp, Np):
  c_full = _from_device_bytes(c_bytes, (Mp, Np))
  c_got = c_full[:M, :N]
  got_flat = c_got.reshape(-1)
  if not np.all(np.isfinite(got_flat)):
    bad = int(got_flat.size - np.count_nonzero(np.isfinite(got_flat)))
    raise SystemExit(f"Validation failed: {bad} non-finite values")

  sample_rows, sample_cols = _sample_coords(M, N)
  row_ids, row_inv = np.unique(sample_rows, return_inverse=True)
  col_ids, col_inv = np.unique(sample_cols, return_inverse=True)
  ref_block = a[row_ids] @ b[:, col_ids]
  ref_flat = ref_block[row_inv, col_inv].astype(np.float32, copy=False).reshape(-1)
  got_flat = c_got[sample_rows, sample_cols].astype(np.float32, copy=False).reshape(-1)

  rel_l2 = float(np.linalg.norm(got_flat - ref_flat) / (np.linalg.norm(ref_flat) + 1e-12))
  max_abs = float(np.max(np.abs(got_flat - ref_flat)))
  ref_std = float(np.std(ref_flat))
  if ref_std < 1e-12:
    pcc = 1.0 if max_abs < 1e-6 else 0.0
  else:
    pcc = float(np.corrcoef(ref_flat, got_flat)[0, 1])
  print(f"Validation ({got_flat.size} samples): PCC={pcc:.6f}, rel_l2={rel_l2:.6f}, max_abs={max_abs:.6f}")
  if pcc < 0.995 or rel_l2 > 0.08:
    raise SystemExit(f"Validation failed: PCC={pcc:.6f}, rel_l2={rel_l2:.6f}")


def _make_inputs(M: int, K: int, N: int) -> tuple[np.ndarray, np.ndarray]:
  host_dtype = _host_input_dtype()
  if INPUT_PATTERN == "random":
    rng_a, rng_b = np.random.default_rng(42), np.random.default_rng(123)
    a_src = rng_a.uniform(-0.5, 0.5, size=(M, K)).astype(host_dtype)
    b_src = rng_b.uniform(-0.5, 0.5, size=(K, N)).astype(host_dtype)
    return a_src, b_src
  if INPUT_PATTERN in ("selector", "selector_int"):
    a_src = np.zeros((M, K), dtype=host_dtype)
    a_src[np.arange(M), np.arange(M) % K] = host_dtype(1.0)
    k_ids = np.arange(K, dtype=np.float32).reshape(K, 1)
    n_ids = np.arange(N, dtype=np.float32).reshape(1, N)
    b_src = (k_ids * 256.0 + n_ids).astype(host_dtype)
    return a_src, b_src
  if INPUT_PATTERN in ("selector_decimal", "selector_float"):
    a_src = np.zeros((M, K), dtype=host_dtype)
    a_src[np.arange(M), np.arange(M) % K] = host_dtype(1.0)
    k_ids = np.arange(K, dtype=np.float32).reshape(K, 1)
    n_ids = np.arange(N, dtype=np.float32).reshape(1, N)
    b_src = (k_ids + n_ids / 1024.0).astype(host_dtype)
    return a_src, b_src
  if INPUT_PATTERN == "ones":
    return np.ones((M, K), dtype=host_dtype), np.ones((K, N), dtype=host_dtype)
  if INPUT_PATTERN == "ramp":
    a_src = np.broadcast_to(np.arange(1, K + 1, dtype=host_dtype), (M, K)).copy()
    b_src = np.broadcast_to(np.arange(1, K + 1, dtype=host_dtype).reshape(K, 1), (K, N)).copy()
    return a_src, b_src
  raise SystemExit(
    f"Invalid INPUT_PATTERN={INPUT_PATTERN!r}. "
    "Expected: random, selector_int, selector_decimal, ones, ramp")

def main():
  if len(sys.argv) == 4:
    M, K, N = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
  elif len(sys.argv) == 1:
    M, K, N = 5120, 4096, 5632
  else:
    raise SystemExit("Usage: matmul_peak.py [M K N]")

  device = Device()
  try:
    max_cores = int(os.environ.get("MAX_CORES", "0")) or len(device.cores)
    plan = plan_matmul(M, K, N, device.cores[:max_cores], io_dtype=IO_DTYPE, f32_acc=F32_ACC)
    Mp, Kp, Np = plan.mt * 32, plan.kt * 32, plan.nt * 32
    padded = (M != Mp or K != Kp or N != Np)

    print(
      f"Matmul Peak: C[{M},{N}] = A[{M},{K}] @ B[{K},{N}] "
      f"({IO_MODE} io, {'fp32' if F32_ACC else 'mixed'} accum, {MATH_FIDELITY.name})"
    )
    if padded: print(f"  padded: A[{Mp},{Kp}] @ B[{Kp},{Np}] -> C[{Mp},{Np}]")
    print(f"  Mt={plan.mt} Kt={plan.kt} Nt={plan.nt} grid={plan.num_rows}x{plan.num_cols}")
    print(f"  per_core_M={plan.per_core_m} per_core_N={plan.per_core_n} "
          f"in0_block_w={plan.in0_block_w} num_blocks={plan.num_blocks}")
    print(f"  subblock: {plan.out_subblock_h}h x {plan.out_subblock_w}w = {plan.out_subblock_num_tiles} tiles")
    print(f"  cores: {plan.active_core_count} ({len(device.cores)} available)")
    print(f"  input pattern: {INPUT_PATTERN}")
    print(f"  validation: {VALIDATE_SAMPLES} sampled outputs (seed={VALIDATE_SEED})")

    a_src, b_src = _make_inputs(M, K, N)

    if padded:
      a_padded = np.zeros((Mp, Kp), dtype=_host_input_dtype()); a_padded[:M, :K] = a_src
      b_padded = np.zeros((Kp, Np), dtype=_host_input_dtype()); b_padded[:K, :N] = b_src
      a_bytes, b_bytes = _to_device_bytes(a_padded), _to_device_bytes(b_padded)
    else:
      a_bytes, b_bytes = _to_device_bytes(a_src), _to_device_bytes(b_src)

    a_ref = _from_device_bytes(_to_device_bytes(a_src), (M, K))
    b_ref = _from_device_bytes(_to_device_bytes(b_src), (K, N))

    a_buf = device.alloc_write(a_bytes, dtype=IO_DTYPE, shape=(Mp, Kp), name="A")
    b_buf = device.alloc_write(b_bytes, dtype=IO_DTYPE, shape=(Kp, Np), name="B")
    c_buf = device.dram.alloc(plan.mt * plan.nt, dtype=IO_DTYPE, name="C", shape=(Mp, Np))

    prog = build_matmul_program(plan, a_buf, b_buf, c_buf, io_dtype=IO_DTYPE, math_fidelity=MATH_FIDELITY, f32_acc=F32_ACC)

    for _ in range(NUM_ITERS):
      device.queue(prog)

    c_raw = device.dram_read(c_buf)
    _validate(a_ref, b_ref, c_raw, M, N, Mp, Np)

  finally:
    device.close()

if __name__ == "__main__":
  main()
