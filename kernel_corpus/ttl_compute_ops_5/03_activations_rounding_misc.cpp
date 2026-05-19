// Corpus kernel 3/5: TTL activations, rounding, and simple unary ops.
//
// TTL coverage:
//   tanh, abs, neg, relu, sigmoid, floor, ceil, sign, gelu, silu,
//   hardsigmoid, expm1, square, softsign, signbit, frac, trunc

#include <cstdint>

#include "api/compute/cb_api.h"
#include "api/compute/common.h"
#include "api/compute/compute_kernel_api.h"
#include "api/compute/eltwise_unary/activations.h"
#include "api/compute/eltwise_unary/eltwise_unary.h"
#include "api/compute/eltwise_unary/gelu.h"
#include "api/compute/eltwise_unary/negative.h"
#include "api/compute/eltwise_unary/relu.h"
#include "api/compute/eltwise_unary/rounding.h"
#include "api/compute/pack.h"
#include "api/compute/reg_api.h"
#include "api/compute/tile_move_copy.h"

constexpr uint32_t kIn = 0;
constexpr uint32_t kOut = 16;

void kernel_main() {
  constexpr uint32_t one = 1;
  constexpr uint32_t tile = 0;

  cb_wait_front(kIn, one);
  cb_reserve_back(kOut, 17);

  init_sfpu(kIn, kOut);
  tile_regs_acquire();
  copy_tile_init(kIn);

  copy_tile(kIn, tile, 0);
  tanh_tile_init();
  tanh_tile(0);

  copy_tile(kIn, tile, 1);
  abs_tile_init();
  abs_tile(1);

  copy_tile(kIn, tile, 2);
  negative_tile_init();
  negative_tile(2);

  copy_tile(kIn, tile, 3);
  relu_tile_init();
  relu_tile(3);

  copy_tile(kIn, tile, 4);
  sigmoid_tile_init();
  sigmoid_tile(4);

  copy_tile(kIn, tile, 5);
  rounding_op_tile_init();
  floor_tile(5);

  copy_tile(kIn, tile, 6);
  rounding_op_tile_init();
  ceil_tile(6);

  copy_tile(kIn, tile, 7);
  sign_tile_init();
  sign_tile(7);

  copy_tile(kIn, tile, 8);
  gelu_tile_init();
  gelu_tile(8);

  copy_tile(kIn, tile, 9);
  silu_tile_init();
  silu_tile(9);

  copy_tile(kIn, tile, 10);
  hardsigmoid_tile_init();
  hardsigmoid_tile(10);

  copy_tile(kIn, tile, 11);
  expm1_tile_init();
  expm1_tile(11);

  copy_tile(kIn, tile, 12);
  square_tile_init();
  square_tile(12);

  copy_tile(kIn, tile, 13);
  softsign_tile_init();
  softsign_tile(13);

  copy_tile(kIn, tile, 14);
  signbit_tile_init();
  signbit_tile(14);

  copy_tile(kIn, tile, 15);
  rounding_op_tile_init();
  frac_tile(15);

  tile_regs_commit();
  tile_regs_wait();

  for (uint32_t i = 0; i < 16; ++i) {
    pack_tile<true>(i, kOut, i);
  }
  tile_regs_release();

  tile_regs_acquire();
  copy_tile_init(kIn);
  copy_tile(kIn, tile, 0);
  rounding_op_tile_init();
  trunc_tile(0);
  tile_regs_commit();
  tile_regs_wait();
  pack_tile<true>(0, kOut, 16);
  tile_regs_release();

  cb_push_back(kOut, 17);
  cb_pop_front(kIn, one);
}
