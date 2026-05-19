// Corpus kernel 2/5: TTL unary transcendental/math ops.
//
// TTL coverage:
//   exp, exp2, log, sqrt, rsqrt, recip, sin, cos, tan, asin, acos, atan
//
// Note:
//   log2 is not a current TTL op in TTLElementwiseOps.def, but the Metal API
//   exposes log_with_base_tile/log_with_base_tile_init for a future mixin.

#include <cstdint>

#include "api/compute/cb_api.h"
#include "api/compute/common.h"
#include "api/compute/compute_kernel_api.h"
#include "api/compute/eltwise_unary/eltwise_unary.h"
#include "api/compute/eltwise_unary/exp.h"
#include "api/compute/eltwise_unary/recip.h"
#include "api/compute/eltwise_unary/rsqrt.h"
#include "api/compute/eltwise_unary/sqrt.h"
#include "api/compute/eltwise_unary/trigonometry.h"
#include "api/compute/pack.h"
#include "api/compute/reg_api.h"
#include "api/compute/tile_move_copy.h"

constexpr uint32_t kIn = 0;
constexpr uint32_t kOut = 16;

void kernel_main() {
  constexpr uint32_t one = 1;
  constexpr uint32_t tile = 0;

  cb_wait_front(kIn, one);
  cb_reserve_back(kOut, 12);

  init_sfpu(kIn, kOut);
  tile_regs_acquire();

  copy_tile_init(kIn);

  copy_tile(kIn, tile, 0);
  exp_tile_init();
  exp_tile(0);

  copy_tile(kIn, tile, 1);
  exp2_tile_init();
  exp2_tile(1);

  copy_tile(kIn, tile, 2);
  log_tile_init();
  log_tile(2);

  copy_tile(kIn, tile, 3);
  sqrt_tile_init();
  sqrt_tile(3);

  copy_tile(kIn, tile, 4);
  rsqrt_tile_init();
  rsqrt_tile(4);

  copy_tile(kIn, tile, 5);
  recip_tile_init();
  recip_tile(5);

  copy_tile(kIn, tile, 6);
  sin_tile_init();
  sin_tile(6);

  copy_tile(kIn, tile, 7);
  cos_tile_init();
  cos_tile(7);

  copy_tile(kIn, tile, 8);
  tan_tile_init();
  tan_tile(8);

  copy_tile(kIn, tile, 9);
  asin_tile_init();
  asin_tile(9);

  copy_tile(kIn, tile, 10);
  acos_tile_init();
  acos_tile(10);

  copy_tile(kIn, tile, 11);
  atan_tile_init();
  atan_tile(11);

  tile_regs_commit();
  tile_regs_wait();

  for (uint32_t i = 0; i < 12; ++i) {
    pack_tile<true>(i, kOut, i);
  }
  cb_push_back(kOut, 12);

  tile_regs_release();
  cb_pop_front(kIn, one);
}
