#define REDUCE_OP PoolType::SUM
#define REDUCE_DIM ReduceDim::REDUCE_COL
#include <cstdint>
#include "api/compile_time_args.h"
#include "api/compute/bcast.h"
#include "api/compute/common.h"
#include "api/compute/eltwise_binary_sfpu.h"
#include "api/compute/eltwise_unary/eltwise_unary.h"
#include "api/compute/eltwise_unary/exp.h"
#include "api/compute/eltwise_unary/fill.h"
#include "api/compute/eltwise_unary/recip.h"
#include "api/compute/pack.h"
#include "api/compute/reduce.h"
#include "api/compute/reg_api.h"
#include "api/compute/tile_move_copy.h"
#include "api/dataflow/circular_buffer.h"
#include "tools/profiler/kernel_profiler.hpp"
inline uint32_t float_to_bits(const float f) { uint32_t r; __builtin_memcpy(&r, &f, sizeof(r)); return r; }
#ifndef INFINITY
#define INFINITY __builtin_inff()
#endif
void kernel_main() {
  float v1 = 1.000000000e+00f;
  size_t v2 = 7;
  size_t v3 = 6;
  size_t v4 = 5;
  size_t v5 = 3;
  size_t v6 = 2;
  int32_t v7 = 1;
  int32_t v8 = 4;
  size_t v9 = 4;
  size_t v10 = 1;
  size_t v11 = 0;
  CircularBuffer cb_ctarg_2(get_compile_time_arg_val(2));
  CircularBuffer cb_ctarg_0(get_compile_time_arg_val(0));
  CircularBuffer cb_ctarg_1(get_compile_time_arg_val(1));
  CircularBuffer cb_ctarg_3(get_compile_time_arg_val(3));
  CircularBuffer cb_ctarg_4(get_compile_time_arg_val(4));
  CircularBuffer cb_ctarg_6(get_compile_time_arg_val(6));
  CircularBuffer cb_ctarg_5(get_compile_time_arg_val(5));
  cb_ctarg_0.wait_front(v8);
  cb_ctarg_1.wait_front(v8);
  cb_ctarg_3.reserve_back(v7);
  init_sfpu(get_compile_time_arg_val(3), get_compile_time_arg_val(3));
  tile_regs_acquire();
  fill_tile_init();
  fill_tile(v11, v1);
  tile_regs_commit();
  tile_regs_wait();
  pack_tile<true>(v11, get_compile_time_arg_val(3), v11);
  tile_regs_release();
  cb_ctarg_3.push_back(v7);
  cb_ctarg_3.wait_front(v7);
  cb_ctarg_4.reserve_back(v7);
  init_sfpu(get_compile_time_arg_val(0), get_compile_time_arg_val(4));
  tile_regs_acquire();
  reduce_init<PoolType::MAX, ReduceDim::REDUCE_ROW, false>(get_compile_time_arg_val(0), get_compile_time_arg_val(3), get_compile_time_arg_val(4));
  for (size_t i12 = v11; i12 < v9; i12 += v10) {
    reduce_tile<PoolType::MAX, ReduceDim::REDUCE_ROW, false>(get_compile_time_arg_val(0), get_compile_time_arg_val(3), i12, v11, v11);
  }
  reduce_uninit();
  tile_regs_commit();
  tile_regs_wait();
  pack_tile<true>(v11, get_compile_time_arg_val(4), v11);
  tile_regs_release();
  cb_ctarg_3.pop_front(v7);
  cb_ctarg_4.push_back(v7);
  cb_ctarg_4.wait_front(v7);
  cb_ctarg_6.reserve_back(v8);
  init_sfpu(get_compile_time_arg_val(4), get_compile_time_arg_val(6));
  tile_regs_acquire();
  unary_bcast_init<BroadcastType::COL>(get_compile_time_arg_val(4), get_compile_time_arg_val(6));
  unary_bcast<BroadcastType::COL>(get_compile_time_arg_val(4), v11, v11);
  unary_bcast<BroadcastType::COL>(get_compile_time_arg_val(4), v11, v6);
  unary_bcast<BroadcastType::COL>(get_compile_time_arg_val(4), v11, v9);
  unary_bcast<BroadcastType::COL>(get_compile_time_arg_val(4), v11, v3);
  copy_tile_init(get_compile_time_arg_val(1));
  copy_tile(get_compile_time_arg_val(1), v11, v10);
  copy_tile(get_compile_time_arg_val(1), v10, v5);
  copy_tile(get_compile_time_arg_val(1), v6, v4);
  copy_tile(get_compile_time_arg_val(1), v5, v2);
  sub_binary_tile_init();
  sub_binary_tile(v10, v11, v11);
  sub_binary_tile(v5, v6, v6);
  sub_binary_tile(v4, v9, v9);
  sub_binary_tile(v2, v3, v3);
  exp_tile_init();
  exp_tile(v11);
  exp_tile(v6);
  exp_tile(v9);
  exp_tile(v3);
  tile_regs_commit();
  tile_regs_wait();
  pack_tile<true>(v11, get_compile_time_arg_val(6), v11);
  pack_tile<true>(v6, get_compile_time_arg_val(6), v10);
  pack_tile<true>(v9, get_compile_time_arg_val(6), v6);
  pack_tile<true>(v3, get_compile_time_arg_val(6), v5);
  tile_regs_release();
  cb_ctarg_6.push_back(v8);
  cb_ctarg_6.wait_front(v8);
  cb_ctarg_3.reserve_back(v7);
  init_sfpu(get_compile_time_arg_val(3), get_compile_time_arg_val(3));
  tile_regs_acquire();
  fill_tile_init();
  fill_tile(v11, v1);
  tile_regs_commit();
  tile_regs_wait();
  pack_tile<true>(v11, get_compile_time_arg_val(3), v11);
  tile_regs_release();
  cb_ctarg_3.push_back(v7);
  cb_ctarg_3.wait_front(v7);
  cb_ctarg_5.reserve_back(v7);
  init_sfpu(get_compile_time_arg_val(6), get_compile_time_arg_val(5));
  tile_regs_acquire();
  reduce_init<PoolType::SUM, ReduceDim::REDUCE_ROW, false>(get_compile_time_arg_val(6), get_compile_time_arg_val(3), get_compile_time_arg_val(5));
  for (size_t i13 = v11; i13 < v9; i13 += v10) {
    reduce_tile<PoolType::SUM, ReduceDim::REDUCE_ROW, false>(get_compile_time_arg_val(6), get_compile_time_arg_val(3), i13, v11, v11);
  }
  reduce_uninit();
  tile_regs_commit();
  tile_regs_wait();
  pack_tile<true>(v11, get_compile_time_arg_val(5), v11);
  tile_regs_release();
  cb_ctarg_3.pop_front(v7);
  cb_ctarg_6.pop_front(v8);
  cb_ctarg_5.push_back(v7);
  cb_ctarg_5.wait_front(v7);
  cb_ctarg_2.reserve_back(v8);
  init_sfpu(get_compile_time_arg_val(4), get_compile_time_arg_val(2));
  tile_regs_acquire();
  unary_bcast_init<BroadcastType::COL>(get_compile_time_arg_val(4), get_compile_time_arg_val(2));
  unary_bcast<BroadcastType::COL>(get_compile_time_arg_val(4), v11, v11);
  unary_bcast<BroadcastType::COL>(get_compile_time_arg_val(4), v11, v6);
  unary_bcast<BroadcastType::COL>(get_compile_time_arg_val(4), v11, v9);
  unary_bcast<BroadcastType::COL>(get_compile_time_arg_val(4), v11, v3);
  copy_tile_init(get_compile_time_arg_val(1));
  copy_tile(get_compile_time_arg_val(1), v11, v10);
  copy_tile(get_compile_time_arg_val(1), v10, v5);
  copy_tile(get_compile_time_arg_val(1), v6, v4);
  copy_tile(get_compile_time_arg_val(1), v5, v2);
  sub_binary_tile_init();
  sub_binary_tile(v10, v11, v11);
  sub_binary_tile(v5, v6, v6);
  sub_binary_tile(v4, v9, v9);
  sub_binary_tile(v2, v3, v3);
  unary_bcast_init<BroadcastType::COL>(get_compile_time_arg_val(5), get_compile_time_arg_val(2));
  unary_bcast<BroadcastType::COL>(get_compile_time_arg_val(5), v11, v10);
  unary_bcast<BroadcastType::COL>(get_compile_time_arg_val(5), v11, v5);
  unary_bcast<BroadcastType::COL>(get_compile_time_arg_val(5), v11, v4);
  unary_bcast<BroadcastType::COL>(get_compile_time_arg_val(5), v11, v2);
  exp_tile_init();
  exp_tile(v11);
  exp_tile(v6);
  exp_tile(v9);
  exp_tile(v3);
  recip_tile_init();
  recip_tile(v10);
  recip_tile(v5);
  recip_tile(v4);
  recip_tile(v2);
  mul_binary_tile_init();
  mul_binary_tile(v11, v10, v11);
  mul_binary_tile(v6, v5, v6);
  mul_binary_tile(v9, v4, v9);
  mul_binary_tile(v3, v2, v3);
  tile_regs_commit();
  tile_regs_wait();
  pack_tile<true>(v11, get_compile_time_arg_val(2), v11);
  pack_tile<true>(v6, get_compile_time_arg_val(2), v10);
  pack_tile<true>(v9, get_compile_time_arg_val(2), v6);
  pack_tile<true>(v3, get_compile_time_arg_val(2), v5);
  tile_regs_release();
  cb_ctarg_5.pop_front(v7);
  cb_ctarg_4.pop_front(v7);
  cb_ctarg_2.push_back(v8);
  cb_ctarg_1.pop_front(v8);
  cb_ctarg_0.pop_front(v8);
  return;
}

