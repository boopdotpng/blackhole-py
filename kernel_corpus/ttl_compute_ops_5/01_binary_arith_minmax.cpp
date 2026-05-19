// Corpus kernel 1/5: TTL binary elementwise ops.
//
// TTL coverage:
//   add, sub, mul, div, max, min
//
// Mixin shape:
//   CB wait/reserve/push/pop, tile_regs acquire/commit/wait/release,
//   copy_tile, add/sub/mul/div_binary_tile, binary_max/min_tile, pack_tile.

#include <cstdint>

#include "api/compute/cb_api.h"
#include "api/compute/common.h"
#include "api/compute/compute_kernel_api.h"
#include "api/compute/eltwise_binary_sfpu.h"
#include "api/compute/binary_max_min.h"
#include "api/compute/eltwise_unary/eltwise_unary.h"
#include "api/compute/pack.h"
#include "api/compute/reg_api.h"
#include "api/compute/tile_move_copy.h"

constexpr uint32_t kIn0 = 0;
constexpr uint32_t kIn1 = 1;
constexpr uint32_t kOut = 16;

void kernel_main() {
  constexpr uint32_t one = 1;
  constexpr uint32_t tile = 0;

  cb_wait_front(kIn0, one);
  cb_wait_front(kIn1, one);
  cb_reserve_back(kOut, 6);

  init_sfpu(kIn0, kOut);
  tile_regs_acquire();

  copy_tile_init(kIn0);
  copy_tile(kIn0, tile, 0);
  copy_tile_init(kIn1);
  copy_tile(kIn1, tile, 1);

  add_binary_tile_init();
  add_binary_tile(0, 1, 2);

  sub_binary_tile_init();
  sub_binary_tile(0, 1, 3);

  mul_binary_tile_init();
  mul_binary_tile(0, 1, 4);

  div_binary_tile_init();
  div_binary_tile(0, 1, 5);

  binary_max_tile_init();
  binary_max_tile(0, 1, 6);

  binary_min_tile_init();
  binary_min_tile(0, 1, 7);

  tile_regs_commit();
  tile_regs_wait();

  pack_tile<true>(2, kOut, 0);
  pack_tile<true>(3, kOut, 1);
  pack_tile<true>(4, kOut, 2);
  pack_tile<true>(5, kOut, 3);
  pack_tile<true>(6, kOut, 4);
  pack_tile<true>(7, kOut, 5);

  cb_push_back(kOut, 6);

  tile_regs_release();
  cb_pop_front(kIn0, one);
  cb_pop_front(kIn1, one);
}
