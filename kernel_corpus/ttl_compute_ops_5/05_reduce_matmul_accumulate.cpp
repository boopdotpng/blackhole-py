// Corpus kernel 5/5: TTL reductions and matmul.
//
// TTL coverage:
//   reduce_sum, reduce_max, matmul, store(accumulate=True style)
//
// Notes:
//   TTL reduce requires a scaler CB. Use a tile filled with 1.0 for sum/max.
//   The L1 accumulation packer path shown here is the compute-side hook behind
//   block += rhs / store(accumulate=True)-style lowering.

#include <cstdint>

#include "api/compute/cb_api.h"
#include "api/compute/common.h"
#include "api/compute/compute_kernel_api.h"
#include "api/compute/eltwise_unary/eltwise_unary.h"
#include "api/compute/matmul.h"
#include "api/compute/pack.h"
#include "api/compute/reduce.h"
#include "api/compute/reg_api.h"
#include "api/compute/tile_move_copy.h"

constexpr uint32_t kA = 0;
constexpr uint32_t kB = 1;
constexpr uint32_t kScaler = 2;
constexpr uint32_t kOut = 16;
constexpr uint32_t kAccumOut = 24;

void kernel_main() {
  constexpr uint32_t one = 1;
  constexpr uint32_t tile = 0;

  cb_wait_front(kA, one);
  cb_wait_front(kB, one);
  cb_wait_front(kScaler, one);
  cb_reserve_back(kOut, 3);
  cb_reserve_back(kAccumOut, one);

  tile_regs_acquire();

  reduce_init<PoolType::SUM, ReduceDim::REDUCE_ROW>(kA, kScaler, kOut);
  reduce_tile<PoolType::SUM, ReduceDim::REDUCE_ROW>(kA, kScaler, tile, tile, 0);
  reduce_uninit();

  reduce_init<PoolType::MAX, ReduceDim::REDUCE_COL>(kA, kScaler, kOut);
  reduce_tile<PoolType::MAX, ReduceDim::REDUCE_COL>(kA, kScaler, tile, tile, 1);
  reduce_uninit();

  mm_init(kA, kB, kOut);
  matmul_tiles(kA, kB, tile, tile, 2);

  // Accumulation-shaped store: pack once as overwrite, then reconfigure the
  // packer to add subsequent packs into the existing L1 tile.
  copy_tile_init(kA);
  copy_tile(kA, tile, 3);

  tile_regs_commit();
  tile_regs_wait();

  pack_tile<true>(0, kOut, 0);
  pack_tile<true>(1, kOut, 1);
  pack_tile<true>(2, kOut, 2);

  pack_reconfig_l1_acc(0);
  pack_tile<true>(3, kAccumOut, tile);
  pack_reconfig_l1_acc(1);
  pack_tile<true>(2, kAccumOut, tile);
  pack_reconfig_l1_acc(0);

  cb_push_back(kOut, 3);
  cb_push_back(kAccumOut, one);

  tile_regs_release();
  cb_pop_front(kA, one);
  cb_pop_front(kB, one);
  cb_pop_front(kScaler, one);
}
