#!/usr/bin/env python3
"""Element-wise add-1 on every tile: validates SFPU scalar broadcast path."""
import os, struct, random
import numpy as np

from device import Device, CBConfig, Dtype, Program

K_READER = r"""
#include <cstdint>
void kernel_main() {
  uint32_t addr = get_arg_val<uint32_t>(0);
  uint32_t off  = get_arg_val<uint32_t>(1);
  uint32_t n    = get_arg_val<uint32_t>(2);
  constexpr uint32_t cb = tt::CBIndex::c_0;
  const InterleavedAddrGenFast<true> s = {
    .bank_base_address = addr, .page_size = get_tile_size(cb), .data_format = DataFormat::Float16_b,
  };
  for (uint32_t i = 0; i < n; ++i) {
    cb_reserve_back(cb, 1);
    noc_async_read_tile(off + i, s, get_write_ptr(cb));
    noc_async_read_barrier();
    cb_push_back(cb, 1);
  }
}
"""

K_WRITER = r"""
#include <cstdint>
void kernel_main() {
  uint32_t addr = get_arg_val<uint32_t>(0);
  uint32_t off  = get_arg_val<uint32_t>(1);
  uint32_t n    = get_arg_val<uint32_t>(2);
  constexpr uint32_t cb = tt::CBIndex::c_16;
  const InterleavedAddrGenFast<true> s = {
    .bank_base_address = addr, .page_size = get_tile_size(cb), .data_format = DataFormat::Float16_b,
  };
  for (uint32_t i = 0; i < n; ++i) {
    cb_wait_front(cb, 1);
    noc_async_write_tile(off + i, s, get_read_ptr(cb));
    noc_async_write_barrier();
    cb_pop_front(cb, 1);
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
  uint32_t n = get_arg_val<uint32_t>(0);
  constexpr auto cb_in = tt::CBIndex::c_0;
  constexpr auto cb_out = tt::CBIndex::c_16;

  unary_op_init_common(cb_in, cb_out);
  copy_tile_init(cb_in);
  binop_with_scalar_tile_init();
  for (uint32_t i = 0; i < n; ++i) {
    tile_regs_acquire();
    cb_wait_front(cb_in, 1);
    { DeviceZoneScopedN("UNPACK");
    copy_tile(cb_in, 0, 0);
    }
    cb_pop_front(cb_in, 1);
    { DeviceZoneScopedN("SFPU_ADD");
    add_unary_tile(0, 0x3f800000);  // +1.0f
    }
    tile_regs_commit();
    tile_regs_wait();
    cb_reserve_back(cb_out, 1);
    { DeviceZoneScopedN("PACK");
    pack_tile(0, cb_out);
    }
    cb_push_back(cb_out, 1);
    tile_regs_release();
  }
}
}  // namespace NAMESPACE
"""

def _bf16(x: float) -> int: return struct.unpack("<I", struct.pack("<f", x))[0] >> 16
def _f32(x: int) -> float: return struct.unpack("<f", struct.pack("<I", (x & 0xFFFF) << 16))[0]

def main():
  device = Device()
  try:
    num_cores = len(device.cores)
    tiles_per_core = int(os.environ.get("TILES", "4"))
    n_tiles = num_cores * tiles_per_core

    rng = random.Random(42)
    src_rm = b"".join(_bf16(rng.random()).to_bytes(2, "little") for _ in range(n_tiles * 32 * 32))

    src_buf = device.alloc_write(src_rm, dtype=Dtype.Float16_b, shape=(n_tiles, 32, 32), name="src")
    dst_buf = device.dram.alloc(n_tiles, dtype=Dtype.Float16_b, shape=(n_tiles, 32, 32), name="dst")

    def reader_args(i, _xy, _n): return [src_buf.addr, i * tiles_per_core, tiles_per_core]
    def writer_args(i, _xy, _n): return [dst_buf.addr, i * tiles_per_core, tiles_per_core]
    def compute_args(i, _xy, _n): return [tiles_per_core]

    prog = Program(
      cores=num_cores, reader_kernel=K_READER, compute_kernel=K_COMPUTE, writer_kernel=K_WRITER,
      cbs=[CBConfig(index=0, dtype=Dtype.Float16_b, tiles=2), CBConfig(index=16, dtype=Dtype.Float16_b, tiles=2)],
      reader_args=reader_args, writer_args=writer_args, compute_args=compute_args, name="add1",
    )
    device.queue(prog)
    device.run()
    out = device.dram_read(dst_buf)
    for i in range(0, len(out), 2):
      got = int.from_bytes(out[i : i + 2], "little")
      exp = _bf16(_f32(int.from_bytes(src_rm[i : i + 2], "little")) + 1.0)
      if got != exp:
        raise SystemExit(f"FAIL at bf16[{i // 2}]: expected 0x{exp:04x}, got 0x{got:04x}")
    print(f"PASS  {n_tiles} tiles across {num_cores} cores")

    if device._profile_accumulated:
      device.serve_profile()

  finally:
    device.close()

if __name__ == "__main__":
  main()
