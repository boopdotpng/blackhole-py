#!/usr/bin/env python3
from __future__ import annotations

import random
import struct
import os

from device import CBConfig, Device, Dtype, Program

K_READER = r"""
#include <cstdint>

void kernel_main() {
  uint32_t in0_addr = get_arg_val<uint32_t>(0);
  uint32_t tile_offset = get_arg_val<uint32_t>(1);
  uint32_t n_tiles = get_arg_val<uint32_t>(2);
  constexpr uint32_t cb_in0 = tt::CBIndex::c_0;
  const uint32_t tile_size_bytes = get_tile_size(cb_in0);
  const InterleavedAddrGenFast<true> in0 = {
    .bank_base_address = in0_addr,
    .page_size = tile_size_bytes,
    .data_format = DataFormat::Float16_b,
  };
  for (uint32_t i = 0; i < n_tiles; ++i) {
    cb_reserve_back(cb_in0, 1);
    noc_async_read_tile(tile_offset + i, in0, get_write_ptr(cb_in0));
    noc_async_read_barrier();
    cb_push_back(cb_in0, 1);
  }
}
"""

K_WRITER = r"""
#include <cstdint>
#include "tools/profiler/kernel_profiler.hpp"

void kernel_main() {
  uint32_t out_addr = get_arg_val<uint32_t>(0);
  uint32_t tile_offset = get_arg_val<uint32_t>(1);
  uint32_t n_tiles = get_arg_val<uint32_t>(2);
  constexpr uint32_t cb_out0 = tt::CBIndex::c_16;
  const uint32_t tile_size_bytes = get_tile_size(cb_out0);
  const InterleavedAddrGenFast<true> out0 = {
    .bank_base_address = out_addr,
    .page_size = tile_size_bytes,
    .data_format = DataFormat::Float16_b,
  };
  for (uint32_t i = 0; i < n_tiles; ++i) {
    {
      DeviceZoneScopedN("writer_wait_front");
      cb_wait_front(cb_out0, 1);
    }
    {
      DeviceZoneScopedN("writer_dram_write");
      noc_async_write_tile(tile_offset + i, out0, get_read_ptr(cb_out0));
      noc_async_write_barrier();
    }
    cb_pop_front(cb_out0, 1);
  }
}
"""

K_COMPUTE = r"""
#include <cstdint>
#include "compute_kernel_api/common.h"
#include "compute_kernel_api/tile_move_copy.h"
#include "compute_kernel_api/eltwise_unary/eltwise_unary.h"
#include "compute_kernel_api/eltwise_unary/binop_with_scalar.h"
#include "tools/profiler/kernel_profiler.hpp"

namespace NAMESPACE {
void MAIN {
  uint32_t n_tiles = get_arg_val<uint32_t>(0);
  constexpr tt::CBIndex cb_in0 = tt::CBIndex::c_0;
  constexpr tt::CBIndex cb_out0 = tt::CBIndex::c_16;
  constexpr uint32_t dst_reg_idx = 0;
  constexpr uint32_t scalar_one = 0x3f800000;

  unary_op_init_common(cb_in0, cb_out0);
  copy_tile_init(cb_in0);
  binop_with_scalar_tile_init();
  for (uint32_t i = 0; i < n_tiles; ++i) {
    tile_regs_acquire();
    cb_wait_front(cb_in0, 1);
    DeviceZoneScopedN("sfpu_add1");
    copy_tile(cb_in0, 0, dst_reg_idx);
    cb_pop_front(cb_in0, 1);
    add_unary_tile(dst_reg_idx, scalar_one);
    tile_regs_commit();
    tile_regs_wait();
    cb_reserve_back(cb_out0, 1);
    pack_tile(dst_reg_idx, cb_out0);
    cb_push_back(cb_out0, 1);
    tile_regs_release();
  }
}
}  // namespace NAMESPACE
"""


def _bf16_from_f32(x: float) -> int:
    return struct.unpack("<I", struct.pack("<f", x))[0] >> 16


def _f32_from_bf16(x: int) -> float:
    return struct.unpack("<f", struct.pack("<I", (x & 0xFFFF) << 16))[0]


def _make_bf16_buffer(n_tiles: int, seed: int = 0) -> bytes:
  r = random.Random(seed)
  out = bytearray(n_tiles * 32 * 32 * 2)
  for i in range(n_tiles * 32 * 32):
    out[i * 2 : (i + 1) * 2] = _bf16_from_f32(r.random()).to_bytes(2, "little")
  return bytes(out)


def main():
  device = Device()
  try:
    max_cores = int(os.environ.get("CORES", "0"))
    num_cores = min(len(device.cores), max_cores) if max_cores else len(device.cores)
    n_tiles_per_core = int(os.environ.get("TILES_PER_CORE", "4"))
    n_tiles = num_cores * n_tiles_per_core
    tiles_per_core = (n_tiles + num_cores - 1) // num_cores

    src_rm = _make_bf16_buffer(n_tiles)
    tensor_shape = (n_tiles, 32, 32)
    src_buf = device.alloc_write(src_rm, dtype=Dtype.Float16_b, shape=tensor_shape, name="src")
    dst_buf = device.dram.alloc(n_tiles, dtype=Dtype.Float16_b, shape=tensor_shape, name="dst")

    def core_span(core_idx: int) -> tuple[int, int]:
      start = core_idx * tiles_per_core
      count = min(tiles_per_core, n_tiles - start)
      return start, max(count, 0)

    def reader_args(core_idx: int, core_xy: tuple[int, int], n_cores: int) -> list[int]:
      del core_xy, n_cores
      start, count = core_span(core_idx)
      return [src_buf.addr, start, count]

    def writer_args(core_idx: int, core_xy: tuple[int, int], n_cores: int) -> list[int]:
      del core_xy, n_cores
      start, count = core_span(core_idx)
      return [dst_buf.addr, start, count]

    def compute_args(core_idx: int, core_xy: tuple[int, int], n_cores: int) -> list[int]:
      del core_xy, n_cores
      _, count = core_span(core_idx)
      return [count]

    program = Program(
      cores=num_cores,
      reader_kernel=K_READER,
      compute_kernel=K_COMPUTE,
      writer_kernel=K_WRITER,
      cbs=[
        CBConfig(index=0, dtype=Dtype.Float16_b, tiles=2),
        CBConfig(index=16, dtype=Dtype.Float16_b, tiles=2),
      ],
      reader_args=reader_args,
      writer_args=writer_args,
      compute_args=compute_args,
      name="add1",
    )
    device.queue(program)
    device.run()

    out = device.dram_read(dst_buf)

    for i in range(0, len(out), 2):
      src_bf16 = int.from_bytes(src_rm[i : i + 2], "little")
      src_f32 = _f32_from_bf16(src_bf16)
      exp_bf16 = _bf16_from_f32(src_f32 + 1.0)
      got_bf16 = int.from_bytes(out[i : i + 2], "little")
      if exp_bf16 != got_bf16:
        raise SystemExit(
          f"mismatch at bf16[{i // 2}] src=0x{src_bf16:04x} exp=0x{exp_bf16:04x} got=0x{got_bf16:04x}"
        )
    print("Test Passed")
  finally:
    device.close()


if __name__ == "__main__":
    main()
