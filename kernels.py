# Kernel sources for tilize/untilize data transfer programs.
# Each function returns a complete C++ source string with all defines baked in.

_A = '#define A(n) get_arg_val<uint32_t>(n)\n'

def _sysmem_defs(pcie_base: int, tile_row_bytes: int, tile_cols: int, row_bytes: int) -> str:
  return (
    f"#define PCIE_BASE 0x{pcie_base:x}ULL\n"
    f"#define TILE_ROW_BYTES {tile_row_bytes}\n"
    f"#define TILE_COLS {tile_cols}\n"
    f"#define ROW_BYTES {row_bytes}\n"
  )

def _dram_defs(dram_addr: int) -> str:
  return f"#define DRAM_ADDR {dram_addr}\n"

def tilize_reader(pcie_base: int, tile_row_bytes: int, tile_cols: int, row_bytes: int) -> str:
  return _sysmem_defs(pcie_base, tile_row_bytes, tile_cols, row_bytes) + _A + """\
#include <cstdint>

void kernel_main() {
  const uint32_t start = A(0), count = A(1);
  const uint32_t ps = get_tile_size(tt::CBIndex::c_0);
  uint32_t t = 0;
  // batch pairs: issue reads for 2 tiles with one barrier instead of two
  for (; t + 1 < count; t += 2) {
    uint32_t id0 = start + t, id1 = start + t + 1;
    uint32_t pr0 = (id0 / TILE_COLS) * 32, cb0 = (id0 % TILE_COLS) * TILE_ROW_BYTES;
    uint32_t pr1 = (id1 / TILE_COLS) * 32, cb1 = (id1 % TILE_COLS) * TILE_ROW_BYTES;
    cb_reserve_back(tt::CBIndex::c_0, 2);
    uint32_t l1_0 = get_write_ptr(tt::CBIndex::c_0);
    uint32_t l1_1 = l1_0 + ps;
    for (uint32_t r = 0; r < 32; ++r) {
      noc_async_read(PCIE_BASE + (uint64_t)(pr0 + r) * ROW_BYTES + cb0, l1_0 + r * TILE_ROW_BYTES, TILE_ROW_BYTES);
      noc_async_read(PCIE_BASE + (uint64_t)(pr1 + r) * ROW_BYTES + cb1, l1_1 + r * TILE_ROW_BYTES, TILE_ROW_BYTES);
    }
    noc_async_read_barrier();
    cb_push_back(tt::CBIndex::c_0, 2);
  }
  if (t < count) {
    uint32_t id = start + t;
    uint32_t pixel_row = (id / TILE_COLS) * 32;
    uint32_t pixel_col_bytes = (id % TILE_COLS) * TILE_ROW_BYTES;
    cb_reserve_back(tt::CBIndex::c_0, 1);
    uint32_t l1 = get_write_ptr(tt::CBIndex::c_0);
    for (uint32_t r = 0; r < 32; ++r) {
      noc_async_read(PCIE_BASE + (uint64_t)(pixel_row + r) * ROW_BYTES + pixel_col_bytes, l1, TILE_ROW_BYTES);
      l1 += TILE_ROW_BYTES;
    }
    noc_async_read_barrier();
    cb_push_back(tt::CBIndex::c_0, 1);
  }
}
"""

TILIZE_COMPUTE = """\
#include <cstdint>
#include "compute_kernel_api/tilize.h"

namespace NAMESPACE {
void MAIN {
  const uint32_t num_tiles = get_arg_val<uint32_t>(0);
  compute_kernel_hw_startup(tt::CBIndex::c_0, tt::CBIndex::c_16);
  tilize_init(tt::CBIndex::c_0, 1, tt::CBIndex::c_16);
  for (uint32_t t = 0; t < num_tiles; ++t) {
    cb_wait_front(tt::CBIndex::c_0, 1);
    cb_reserve_back(tt::CBIndex::c_16, 1);
    tilize_block(tt::CBIndex::c_0, 1, tt::CBIndex::c_16);
    cb_push_back(tt::CBIndex::c_16, 1);
    cb_pop_front(tt::CBIndex::c_0, 1);
  }
}
}  // namespace NAMESPACE
"""

def tilize_writer(dram_addr: int) -> str:
  return _dram_defs(dram_addr) + _A + """\
#include <cstdint>

void kernel_main() {
  const uint32_t start = A(0), count = A(1);
  const uint32_t ps = get_tile_size(tt::CBIndex::c_16);
  const InterleavedAddrGenFast<true> dram = {
    .bank_base_address = DRAM_ADDR, .page_size = ps,
    .data_format = get_dataformat(tt::CBIndex::c_16),
  };
  uint32_t t = 0;
  for (; t + 1 < count; t += 2) {
    cb_wait_front(tt::CBIndex::c_16, 2);
    uint32_t base = get_read_ptr(tt::CBIndex::c_16);
    noc_async_write_tile(start + t, dram, base);
    noc_async_write_tile(start + t + 1, dram, base + ps);
    noc_async_write_barrier();
    cb_pop_front(tt::CBIndex::c_16, 2);
  }
  if (t < count) {
    cb_wait_front(tt::CBIndex::c_16, 1);
    noc_async_write_tile(start + t, dram, get_read_ptr(tt::CBIndex::c_16));
    noc_async_write_barrier();
    cb_pop_front(tt::CBIndex::c_16, 1);
  }
}
"""

def untilize_reader(dram_addr: int) -> str:
  return _dram_defs(dram_addr) + _A + """\
#include <cstdint>

void kernel_main() {
  const uint32_t start = A(0), count = A(1);
  const uint32_t ps = get_tile_size(tt::CBIndex::c_0);
  const InterleavedAddrGenFast<true> dram = {
    .bank_base_address = DRAM_ADDR, .page_size = ps,
    .data_format = get_dataformat(tt::CBIndex::c_0),
  };
  uint32_t t = 0;
  for (; t + 1 < count; t += 2) {
    cb_reserve_back(tt::CBIndex::c_0, 2);
    uint32_t base = get_write_ptr(tt::CBIndex::c_0);
    noc_async_read_tile(start + t, dram, base);
    noc_async_read_tile(start + t + 1, dram, base + ps);
    noc_async_read_barrier();
    cb_push_back(tt::CBIndex::c_0, 2);
  }
  if (t < count) {
    cb_reserve_back(tt::CBIndex::c_0, 1);
    noc_async_read_tile(start + t, dram, get_write_ptr(tt::CBIndex::c_0));
    noc_async_read_barrier();
    cb_push_back(tt::CBIndex::c_0, 1);
  }
}
"""

UNTILIZE_COMPUTE = """\
#include <cstdint>
#include "compute_kernel_api/pack_untilize.h"

namespace NAMESPACE {
void MAIN {
  const uint32_t num_tiles = get_arg_val<uint32_t>(0);
  compute_kernel_hw_startup(tt::CBIndex::c_0, tt::CBIndex::c_16);
  pack_untilize_init<1, 1>(tt::CBIndex::c_0, tt::CBIndex::c_16);
  for (uint32_t t = 0; t < num_tiles; ++t) {
    cb_wait_front(tt::CBIndex::c_0, 1);
    cb_reserve_back(tt::CBIndex::c_16, 1);
    pack_untilize_block<1, 1>(tt::CBIndex::c_0, 1, tt::CBIndex::c_16, 0);
    cb_push_back(tt::CBIndex::c_16, 1);
    cb_pop_front(tt::CBIndex::c_0, 1);
  }
  pack_untilize_uninit(tt::CBIndex::c_16);
}
}  // namespace NAMESPACE
"""

def untilize_writer(pcie_base: int, tile_row_bytes: int, tile_cols: int, row_bytes: int) -> str:
  return _sysmem_defs(pcie_base, tile_row_bytes, tile_cols, row_bytes) + _A + """\
#include <cstdint>

void kernel_main() {
  const uint32_t start = A(0), count = A(1);
  const uint32_t ps = get_tile_size(tt::CBIndex::c_16);
  uint32_t t = 0;
  for (; t + 1 < count; t += 2) {
    uint32_t id0 = start + t, id1 = start + t + 1;
    uint32_t pr0 = (id0 / TILE_COLS) * 32, cb0 = (id0 % TILE_COLS) * TILE_ROW_BYTES;
    uint32_t pr1 = (id1 / TILE_COLS) * 32, cb1 = (id1 % TILE_COLS) * TILE_ROW_BYTES;
    cb_wait_front(tt::CBIndex::c_16, 2);
    uint32_t l1_0 = get_read_ptr(tt::CBIndex::c_16);
    uint32_t l1_1 = l1_0 + ps;
    for (uint32_t r = 0; r < 32; ++r) {
      noc_async_write(l1_0 + r * TILE_ROW_BYTES, PCIE_BASE + (uint64_t)(pr0 + r) * ROW_BYTES + cb0, TILE_ROW_BYTES);
      noc_async_write(l1_1 + r * TILE_ROW_BYTES, PCIE_BASE + (uint64_t)(pr1 + r) * ROW_BYTES + cb1, TILE_ROW_BYTES);
    }
    noc_async_write_barrier();
    cb_pop_front(tt::CBIndex::c_16, 2);
  }
  if (t < count) {
    uint32_t id = start + t;
    uint32_t pixel_row = (id / TILE_COLS) * 32;
    uint32_t pixel_col_bytes = (id % TILE_COLS) * TILE_ROW_BYTES;
    cb_wait_front(tt::CBIndex::c_16, 1);
    uint32_t l1 = get_read_ptr(tt::CBIndex::c_16);
    for (uint32_t r = 0; r < 32; ++r) {
      noc_async_write(l1, PCIE_BASE + (uint64_t)(pixel_row + r) * ROW_BYTES + pixel_col_bytes, TILE_ROW_BYTES);
      l1 += TILE_ROW_BYTES;
    }
    noc_async_write_barrier();
    cb_pop_front(tt::CBIndex::c_16, 1);
  }
}
"""
