#!/usr/bin/env python3
"""Reproducer for Blackhole packer L1 accumulation bug with IEEE Float16.

The packer's L1 accumulation path (llk_pack_reconfig_l1_acc) is broken for
Float16 (IEEE half, A-exponent format). It produces NaN (0x7fff) when matmul
subblocks are packed to CB24 with L1 acc enabled. Float16_b (bfloat16) and
the non-L1-acc reload path are both unaffected.

tt-metal works around this by always using Float16_b as the L1 accumulation
intermediate format, even when the output tensor is Float16.

Usage:
  PYTHONPATH=. uv run examples/l1_acc_bug.py
"""
import numpy as np

from l1 import *
from program import *
from device import Device, Dtype
from dram import tilize

# Matmul geometry (matches matmul_peak layout)
#   output: 8m x 6n = 48 tiles per core
#   subblock: 8h x 1w = 8 tiles
#   K dimension: 4 tiles/block, 7 blocks total
NUM_BLOCKS = 7
NUM_CORES = 10

# ---------------------------------------------------------------------------
# Kernels
# ---------------------------------------------------------------------------

READER = """\
#include <cstdint>

void kernel_main() {
  const uint32_t num_blocks = get_arg_val<uint32_t>(0);
  const InterleavedAddrGenFast<true> a_dram = {
    .bank_base_address = get_arg_val<uint32_t>(1),
    .page_size = get_tile_size(tt::CBIndex::c_0),
    .data_format = get_dataformat(tt::CBIndex::c_0),
  };
  for (uint32_t b = 0; b < num_blocks; b++) {
    cb_reserve_back(tt::CBIndex::c_0, 32);
    uint32_t l1 = get_write_ptr(tt::CBIndex::c_0);
    for (uint32_t t = 0; t < 32; t++) {
      noc_async_read_tile(b * 32 + t, a_dram, l1);
      l1 += get_tile_size(tt::CBIndex::c_0);
    }
    noc_async_read_barrier();
    cb_push_back(tt::CBIndex::c_0, 32);
  }
}
"""

WRITER = """\
#include <cstdint>

void kernel_main() {
  const uint32_t num_blocks = get_arg_val<uint32_t>(0);
  const InterleavedAddrGenFast<true> b_dram = {
    .bank_base_address = get_arg_val<uint32_t>(1),
    .page_size = get_tile_size(tt::CBIndex::c_1),
    .data_format = get_dataformat(tt::CBIndex::c_1),
  };
  const InterleavedAddrGenFast<true> c_dram = {
    .bank_base_address = get_arg_val<uint32_t>(2),
    .page_size = get_tile_size(tt::CBIndex::c_16),
    .data_format = get_dataformat(tt::CBIndex::c_16),
  };

  // Read B tiles (reused each block)
  for (uint32_t b = 0; b < num_blocks; b++) {
    cb_reserve_back(tt::CBIndex::c_1, 24);
    uint32_t l1 = get_write_ptr(tt::CBIndex::c_1);
    for (uint32_t t = 0; t < 24; t++) {
      noc_async_read_tile(t, b_dram, l1);
      l1 += get_tile_size(tt::CBIndex::c_1);
    }
    noc_async_read_barrier();
    cb_push_back(tt::CBIndex::c_1, 24);
  }

  // Write output tiles in subblock order
  const uint32_t out_base = get_arg_val<uint32_t>(3);
  uint32_t sbh_start = out_base;
  for (uint32_t in0_sb = 0; in0_sb < 1; in0_sb++) {
    uint32_t sbw_start = sbh_start;
    for (uint32_t in1_sb = 0; in1_sb < 6; in1_sb++) {
      cb_wait_front(tt::CBIndex::c_16, 8);
      uint32_t l1_addr = get_read_ptr(tt::CBIndex::c_16);
      uint32_t row_id = sbw_start;
      for (uint32_t h = 0; h < 8; h++) {
        noc_async_write_tile(row_id, c_dram, l1_addr);
        l1_addr += get_tile_size(tt::CBIndex::c_16);
        row_id += 6;
      }
      noc_async_write_barrier();
      cb_pop_front(tt::CBIndex::c_16, 8);
      sbw_start += 1;
    }
    sbh_start += 48;
  }
}
"""

# The only difference between these two compute kernels is how L1 accumulation
# is managed. With L1 acc, intermediate results stay in CB24 across blocks and
# the packer accumulates into them. Without L1 acc, each block reloads from
# CB24 into DST explicitly.

COMPUTE_L1_ACC = """\
#include <cstdint>
#define PACKER_L1_ACC 1
#include "compute_kernel_api/common.h"
#include "compute_kernel_api/matmul.h"
#include "compute_kernel_api/tile_move_copy.h"

namespace NAMESPACE {
void MAIN {
  const uint32_t num_blocks = get_arg_val<uint32_t>(0);

  mm_block_init(tt::CBIndex::c_0, tt::CBIndex::c_1, tt::CBIndex::c_16,
    0, 1, 8, 4);

  bool enable_reload = false;
  uint32_t out_num_tiles_to_wait = 8;

  for (uint32_t block = 0; block < num_blocks; block++) {
    const bool last_out = (block == (num_blocks - 1));

    cb_wait_front(tt::CBIndex::c_0, 32);
    cb_wait_front(tt::CBIndex::c_1, 24);

    int in0_index_subblock_offset = 0;
    for (uint32_t in0_sb = 0; in0_sb < 1; in0_sb++) {
      int in1_index_subblock_offset = 0;
      for (uint32_t in1_sb = 0; in1_sb < 6; in1_sb++) {
        tile_regs_acquire();
        if (enable_reload) {
          copy_tile_to_dst_init_short(tt::CBIndex::c_24);
          cb_wait_front(tt::CBIndex::c_24, 8);
          #pragma GCC unroll 0
          for (uint32_t i = 0; i < 8; i++) { copy_tile(tt::CBIndex::c_24, i, i); }
          cb_pop_front(tt::CBIndex::c_24, 8);
          mm_block_init_short(tt::CBIndex::c_0, tt::CBIndex::c_1, 0, 1, 8, 4);
        }

        #pragma GCC unroll 0
        for (uint32_t inner = 0; inner < 4; inner++) {
          matmul_block(tt::CBIndex::c_0, tt::CBIndex::c_1,
            in0_index_subblock_offset + inner,
            in1_index_subblock_offset + inner * 6,
            0, 0, 1, 8, 4);
        }

        tile_regs_commit();

        if (last_out) {
          cb_reserve_back(tt::CBIndex::c_16, 8);
          tile_regs_wait();
          PACK((llk_pack_reconfig_l1_acc(0)));
          #pragma GCC unroll 0
          for (uint32_t i = 0; i < 8; i++) { pack_tile(i, tt::CBIndex::c_16); }
          tile_regs_release();
          cb_push_back(tt::CBIndex::c_16, 8);
        } else {
          if (block == 0) {
            cb_reserve_back(tt::CBIndex::c_16, out_num_tiles_to_wait);
            out_num_tiles_to_wait += 8;
          }
          cb_reserve_back(tt::CBIndex::c_24, 8);
          tile_regs_wait();
          if (block == 0) { PACK((llk_pack_reconfig_l1_acc(0))); }
          else if (block == 1) { PACK((llk_pack_reconfig_l1_acc(1))); }
          #pragma GCC unroll 0
          for (uint32_t i = 0; i < 8; i++) { pack_tile(i, tt::CBIndex::c_24); }
          tile_regs_release();
          cb_push_back(tt::CBIndex::c_24, 8);
        }
        in1_index_subblock_offset += 1;
      }
      in0_index_subblock_offset += 32;
    }

    if (num_blocks > 2 && block < num_blocks - 2) {
      cb_wait_front(tt::CBIndex::c_24, 48);
      cb_pop_front(tt::CBIndex::c_24, 48);
    }
    if (num_blocks >= 2 && block == num_blocks - 2) enable_reload = true;

    cb_pop_front(tt::CBIndex::c_0, 32);
    cb_pop_front(tt::CBIndex::c_1, 24);
  }
}
}  // namespace NAMESPACE
"""

COMPUTE_RELOAD = """\
#include <cstdint>
#include "compute_kernel_api/common.h"
#include "compute_kernel_api/matmul.h"
#include "compute_kernel_api/tile_move_copy.h"

namespace NAMESPACE {
void MAIN {
  const uint32_t num_blocks = get_arg_val<uint32_t>(0);

  mm_block_init(tt::CBIndex::c_0, tt::CBIndex::c_1, tt::CBIndex::c_16,
    0, 1, 8, 4);

  bool enable_reload = false;
  uint32_t out_num_tiles_to_wait = 8;

  for (uint32_t block = 0; block < num_blocks; block++) {
    const bool last_out = (block == (num_blocks - 1));

    cb_wait_front(tt::CBIndex::c_0, 32);
    cb_wait_front(tt::CBIndex::c_1, 24);

    int in0_index_subblock_offset = 0;
    for (uint32_t in0_sb = 0; in0_sb < 1; in0_sb++) {
      int in1_index_subblock_offset = 0;
      for (uint32_t in1_sb = 0; in1_sb < 6; in1_sb++) {
        tile_regs_acquire();
        if (enable_reload) {
          copy_tile_to_dst_init_short(tt::CBIndex::c_24);
          cb_wait_front(tt::CBIndex::c_24, 8);
          #pragma GCC unroll 0
          for (uint32_t i = 0; i < 8; i++) { copy_tile(tt::CBIndex::c_24, i, i); }
          cb_pop_front(tt::CBIndex::c_24, 8);
          mm_block_init_short(tt::CBIndex::c_0, tt::CBIndex::c_1, 0, 1, 8, 4);
        }

        #pragma GCC unroll 0
        for (uint32_t inner = 0; inner < 4; inner++) {
          matmul_block(tt::CBIndex::c_0, tt::CBIndex::c_1,
            in0_index_subblock_offset + inner,
            in1_index_subblock_offset + inner * 6,
            0, 0, 1, 8, 4);
        }

        tile_regs_commit();

        if (last_out) {
          cb_reserve_back(tt::CBIndex::c_16, 8);
          tile_regs_wait();
          PACK((llk_pack_reconfig_l1_acc(0)));
          #pragma GCC unroll 0
          for (uint32_t i = 0; i < 8; i++) { pack_tile(i, tt::CBIndex::c_16); }
          tile_regs_release();
          cb_push_back(tt::CBIndex::c_16, 8);
        } else {
          if (block == 0) {
            cb_reserve_back(tt::CBIndex::c_16, out_num_tiles_to_wait);
            out_num_tiles_to_wait += 8;
          }
          cb_reserve_back(tt::CBIndex::c_24, 8);
          tile_regs_wait();
          PACK((llk_pack_reconfig_l1_acc(0)));
          #pragma GCC unroll 0
          for (uint32_t i = 0; i < 8; i++) { pack_tile(i, tt::CBIndex::c_24); }
          tile_regs_release();
          cb_push_back(tt::CBIndex::c_24, 8);
        }
        in1_index_subblock_offset += 1;
      }
      in0_index_subblock_offset += 32;
    }

    if (block == 0) enable_reload = true;

    cb_pop_front(tt::CBIndex::c_0, 32);
    cb_pop_front(tt::CBIndex::c_1, 24);
  }
}
}  // namespace NAMESPACE
"""

# ---------------------------------------------------------------------------
# Host
# ---------------------------------------------------------------------------

def to_tile_bytes(arr: np.ndarray, dtype: Dtype) -> bytes:
  tile = arr.astype(np.float16).flatten()
  if dtype == Dtype.Float16:
    return tile.tobytes()
  u32 = tile.astype(np.float32).view(np.uint32)
  return (u32 >> 16).astype(np.uint16).tobytes()

def from_raw(data: bytes, dtype: Dtype) -> np.ndarray:
  if dtype == Dtype.Float16:
    return np.frombuffer(data, dtype=np.float16).astype(np.float32)
  u16 = np.frombuffer(data, dtype=np.uint16)
  return (u16.astype(np.uint32) << 16).view(np.float32).flatten()

def run_matmul(device, compute_kernel, io_dtype, label):
  num_cores = min(len(device.cores), NUM_CORES)
  out_tiles_per_core = 48
  out_tiles = num_cores * out_tiles_per_core
  num_a_tiles = 8 * 4 * NUM_BLOCKS   # PCM * BW * NUM_BLOCKS
  num_b_tiles = 6 * 4                 # PCN * BW

  rng = np.random.default_rng(42)
  a_data = rng.uniform(-0.5, 0.5, size=(num_a_tiles, 32, 32)).astype(np.float16)
  b_data = rng.uniform(-0.5, 0.5, size=(num_b_tiles, 32, 32)).astype(np.float16)

  a_bytes = b"".join(tilize(to_tile_bytes(a_data[t], io_dtype), io_dtype.bpe, (32, 32))
                      for t in range(num_a_tiles))
  b_bytes = b"".join(tilize(to_tile_bytes(b_data[t], io_dtype), io_dtype.bpe, (32, 32))
                      for t in range(num_b_tiles))

  a_buf = device.dram.alloc(num_a_tiles, io_dtype, name=f"A_{label}")
  b_buf = device.dram.alloc(num_b_tiles, io_dtype, name=f"B_{label}")
  c_buf = device.dram.alloc(out_tiles, io_dtype, name=f"C_{label}")
  device.dram.write(a_buf, a_bytes)
  device.dram.write(b_buf, b_bytes)

  prog = Program(
    cores=num_cores,
    reader_kernel=READER,
    compute_kernel=compute_kernel,
    writer_kernel=WRITER,
    cbs=[
      (0, io_dtype.tile_size, 2 * 8 * 4),
      (1, io_dtype.tile_size, 2 * 6 * 4),
      (16, io_dtype.tile_size, out_tiles_per_core),
      (24, io_dtype.tile_size, out_tiles_per_core),
    ],
    reader_args=[NUM_BLOCKS, a_buf.addr],
    writer_args=lambda ci, xy, n: [NUM_BLOCKS, b_buf.addr, c_buf.addr,
                                    ci * out_tiles_per_core],
    compute_args=[NUM_BLOCKS],
    name=label,
  )

  device.queue(prog)
  device.run()

  result = device.dram.read(c_buf)
  values = from_raw(result, io_dtype)
  nan_count = int((~np.isfinite(values)).sum())

  if nan_count > 0:
    raw = np.frombuffer(result, dtype=np.uint16)
    positions = np.where(~np.isfinite(values))[0]
    print(f"  {label}: *** {nan_count} NaN values out of {len(values)} ***")
    for pos in positions[:5]:
      tile = pos // 1024
      elem = pos % 1024
      face_r, face_c = (elem // 256) // 2, (elem // 256) % 2
      row, col = (elem % 256) // 16, (elem % 256) % 16
      print(f"    tile {tile}  face=({face_r},{face_c})  pos=({row},{col})  raw=0x{raw[pos]:04x}")
    if nan_count > 5:
      print(f"    ... and {nan_count - 5} more")
  else:
    print(f"  {label}: clean ({len(values)} elements, no NaN)")

def main():
  device = Device()
  try:
    print(f"Packer L1 accumulation Float16 bug reproducer")
    print(f"  {min(len(device.cores), NUM_CORES)} cores, {NUM_BLOCKS} K-blocks, "
          f"matmul 8m x 6n (subblock 8h x 1w, in0_block_w=4)\n")

    run_matmul(device, COMPUTE_L1_ACC,  Dtype.Float16,   "Float16  + L1 acc")
    run_matmul(device, COMPUTE_L1_ACC,  Dtype.Float16_b, "Float16_b + L1 acc")
    run_matmul(device, COMPUTE_RELOAD,  Dtype.Float16,   "Float16  + reload")

    print()
    print("Float16 + L1 acc triggers the bug. The other two are controls.")

  finally:
    device.close()

if __name__ == "__main__":
  main()
