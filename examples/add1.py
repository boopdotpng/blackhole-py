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
    copy_tile(cb_in, 0, 0);
    cb_pop_front(cb_in, 1);
    add_unary_tile(0, 0x3f800000);  // +1.0f
    tile_regs_commit();
    tile_regs_wait();
    cb_reserve_back(cb_out, 1);
    pack_tile(0, cb_out);
    cb_push_back(cb_out, 1);
    tile_regs_release();
  }
}
}  // namespace NAMESPACE
"""

def _bf16(x: float) -> int: return struct.unpack("<I", struct.pack("<f", x))[0] >> 16
def _f32(x: int) -> float: return struct.unpack("<f", struct.pack("<I", (x & 0xFFFF) << 16))[0]
def _bf16_rtne(x: float) -> int:
  bits = struct.unpack("<I", struct.pack("<f", x))[0]
  low = bits & 0xFFFF
  hi = bits >> 16
  if low > 0x8000 or (low == 0x8000 and (hi & 1)):
    hi += 1
  return hi & 0xFFFF

def _format_bf16_words(data: bytes, count: int = 16) -> str:
  return " ".join(
    f"{int.from_bytes(data[i : i + 2], 'little'):04x}"
    for i in range(0, min(len(data), count * 2), 2)
  )

def _seed_src_tensor(num_tiles: int, pattern: str) -> bytes:
  if pattern == "ordered":
    return b"".join(
      _bf16(float(i)).to_bytes(2, "little")
      for i in range(num_tiles * 32 * 32)
    )
  rng = random.Random(42)
  return b"".join(
    _bf16(rng.random()).to_bytes(2, "little")
    for _ in range(num_tiles * 32 * 32)
  )

def _expected_add1(src: bytes, *, rtne: bool) -> bytes:
  conv = _bf16_rtne if rtne else _bf16
  out = bytearray(len(src))
  for i in range(0, len(src), 2):
    x = int.from_bytes(src[i : i + 2], "little")
    y = conv(_f32(x) + 1.0)
    out[i : i + 2] = y.to_bytes(2, "little")
  return bytes(out)

def _first_mismatch(got: bytes, exp: bytes) -> int | None:
  return next((i for i, (g, e) in enumerate(zip(got, exp)) if g != e), None)

def main():
  device = Device()
  try:
    num_cores = len(device.cores)
    tiles_per_core = int(os.environ.get("TILES", "4"))
    input_pattern = os.environ.get("INPUT_PATTERN", "ordered")
    print_n = int(os.environ.get("PRINT_N", "16"))
    n_tiles = num_cores * tiles_per_core

    src_rm = _seed_src_tensor(n_tiles, input_pattern)

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
    trunc = _expected_add1(src_rm, rtne=False)
    rtne = _expected_add1(src_rm, rtne=True)
    trunc_mismatch = _first_mismatch(out, trunc)
    rtne_mismatch = _first_mismatch(out, rtne)

    print(f"add1 input pattern: {input_pattern}")
    print(f"output first {print_n}: {_format_bf16_words(out, print_n)}")
    print(f"trunc  first {print_n}: {_format_bf16_words(trunc, print_n)}")
    print(f"rtne   first {print_n}: {_format_bf16_words(rtne, print_n)}")
    if trunc_mismatch is None:
      print(f"PASS trunc  {n_tiles} tiles across {num_cores} cores")
    else:
      print(
        f"trunc mismatch byte={trunc_mismatch} "
        f"got={out[trunc_mismatch:trunc_mismatch + 32].hex()} "
        f"exp={trunc[trunc_mismatch:trunc_mismatch + 32].hex()}"
      )
    if rtne_mismatch is None:
      print(f"PASS rtne   {n_tiles} tiles across {num_cores} cores")
    else:
      print(
        f"rtne mismatch byte={rtne_mismatch} "
        f"got={out[rtne_mismatch:rtne_mismatch + 32].hex()} "
        f"exp={rtne[rtne_mismatch:rtne_mismatch + 32].hex()}"
      )

  finally:
    device.close()

if __name__ == "__main__":
  main()
