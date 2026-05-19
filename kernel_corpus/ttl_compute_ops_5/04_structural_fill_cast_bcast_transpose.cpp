// Corpus kernel 4/5: TTL structural/block ops.
//
// TTL coverage:
//   broadcast, transpose, fill, typecast
//
// Notes:
//   TTL's Python broadcast op lowers to a unary bcast variant for row/col/scalar.
//   TTL typecast currently supports floating output formats; this example shows
//   bf16->fp32 as the shape of the low-level call.

#include <cstdint>

#include "api/compute/bcast.h"
#include "api/compute/cb_api.h"
#include "api/compute/common.h"
#include "api/compute/compute_kernel_api.h"
#include "api/compute/eltwise_unary/eltwise_unary.h"
#include "api/compute/eltwise_unary/fill.h"
#include "api/compute/eltwise_unary/typecast.h"
#include "api/compute/pack.h"
#include "api/compute/reg_api.h"
#include "api/compute/tile_move_copy.h"
#include "api/compute/transpose_wh.h"

constexpr uint32_t kIn = 0;
constexpr uint32_t kOut = 16;

void kernel_main() {
  constexpr uint32_t one = 1;
  constexpr uint32_t tile = 0;

  cb_wait_front(kIn, one);
  cb_reserve_back(kOut, 6);

  tile_regs_acquire();

  unary_bcast_init<BroadcastType::ROW>(kIn, kOut);
  unary_bcast<BroadcastType::ROW>(kIn, tile, 0);

  unary_bcast_init<BroadcastType::COL>(kIn, kOut);
  unary_bcast<BroadcastType::COL>(kIn, tile, 1);

  unary_bcast_init<BroadcastType::SCALAR>(kIn, kOut);
  unary_bcast<BroadcastType::SCALAR>(kIn, tile, 2);

  transpose_wh_init(kIn, kOut);
  transpose_wh_tile(kIn, tile, 3);

  init_sfpu(kIn, kOut);
  fill_tile_init();
  fill_tile(4, 1.0f);

  copy_tile_init(kIn);
  copy_tile(kIn, tile, 5);
  typecast_tile_init<static_cast<uint32_t>(DataFormat::Float16_b),
                     static_cast<uint32_t>(DataFormat::Float32)>();
  typecast_tile<static_cast<uint32_t>(DataFormat::Float16_b),
                static_cast<uint32_t>(DataFormat::Float32)>(5);

  tile_regs_commit();
  tile_regs_wait();

  pack_tile<true>(0, kOut, 0);
  pack_tile<true>(1, kOut, 1);
  pack_tile<true>(2, kOut, 2);
  pack_tile<true>(3, kOut, 3);
  pack_tile<true>(4, kOut, 4);
  pack_tile<true>(5, kOut, 5);

  cb_push_back(kOut, 6);

  tile_regs_release();
  cb_pop_front(kIn, one);
}
