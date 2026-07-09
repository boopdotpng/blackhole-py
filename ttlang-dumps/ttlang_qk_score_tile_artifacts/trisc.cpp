#define REDUCE_OP PoolType::SUM
#define REDUCE_DIM ReduceDim::REDUCE_COL
#include <cstdint>
#include "api/compile_time_args.h"
#include "api/compute/common.h"
#include "api/compute/eltwise_binary.h"
#include "api/compute/eltwise_unary/eltwise_unary.h"
#include "api/compute/eltwise_unary/fill.h"
#include "api/compute/pack.h"
#include "api/compute/reduce.h"
#include "api/compute/reg_api.h"
#include "api/dataflow/circular_buffer.h"
#include "tools/profiler/kernel_profiler.hpp"
inline uint32_t float_to_bits(const float f) { uint32_t r; __builtin_memcpy(&r, &f, sizeof(r)); return r; }
#ifndef INFINITY
#define INFINITY __builtin_inff()
#endif
void kernel_main() {
  float v1 = 1.000000000e+00f;
  int32_t v2 = 1;
  int32_t v3 = 2;
  size_t v4 = 2;
  size_t v5 = 1;
  size_t v6 = 0;
  CircularBuffer cb_ctarg_1(get_compile_time_arg_val(1));
  CircularBuffer cb_ctarg_0(get_compile_time_arg_val(0));
  CircularBuffer cb_ctarg_2(get_compile_time_arg_val(2));
  CircularBuffer cb_ctarg_3(get_compile_time_arg_val(3));
  CircularBuffer cb_ctarg_4(get_compile_time_arg_val(4));
  CircularBuffer cb_ctarg_5(get_compile_time_arg_val(5));
  CircularBuffer cb_ctarg_6(get_compile_time_arg_val(6));
  cb_ctarg_0.wait_front(v3);
  cb_ctarg_1.wait_front(v3);
  cb_ctarg_2.wait_front(v2);
  cb_ctarg_4.reserve_back(v3);
  binary_op_init_common(get_compile_time_arg_val(0), get_compile_time_arg_val(1), get_compile_time_arg_val(4));
  tile_regs_acquire();
  mul_tiles_init(get_compile_time_arg_val(0), get_compile_time_arg_val(1));
  mul_tiles(get_compile_time_arg_val(0), get_compile_time_arg_val(1), v6, v6, v6);
  mul_tiles(get_compile_time_arg_val(0), get_compile_time_arg_val(1), v5, v5, v5);
  tile_regs_commit();
  tile_regs_wait();
  pack_tile_block(v6, get_compile_time_arg_val(4), v4);
  tile_regs_release();
  cb_ctarg_4.push_back(v3);
  cb_ctarg_4.wait_front(v3);
  cb_ctarg_5.reserve_back(v2);
  init_sfpu(get_compile_time_arg_val(5), get_compile_time_arg_val(5));
  tile_regs_acquire();
  fill_tile_init();
  fill_tile(v6, v1);
  tile_regs_commit();
  tile_regs_wait();
  pack_tile<true>(v6, get_compile_time_arg_val(5), v6);
  tile_regs_release();
  cb_ctarg_5.push_back(v2);
  cb_ctarg_5.wait_front(v2);
  cb_ctarg_6.reserve_back(v2);
  init_sfpu(get_compile_time_arg_val(4), get_compile_time_arg_val(6));
  tile_regs_acquire();
  reduce_init<PoolType::SUM, ReduceDim::REDUCE_ROW, false>(get_compile_time_arg_val(4), get_compile_time_arg_val(5), get_compile_time_arg_val(6));
  for (size_t i7 = v6; i7 < v4; i7 += v5) {
    reduce_tile<PoolType::SUM, ReduceDim::REDUCE_ROW, false>(get_compile_time_arg_val(4), get_compile_time_arg_val(5), i7, v6, v6);
  }
  reduce_uninit();
  tile_regs_commit();
  tile_regs_wait();
  pack_tile<true>(v6, get_compile_time_arg_val(6), v6);
  tile_regs_release();
  cb_ctarg_5.pop_front(v2);
  cb_ctarg_4.pop_front(v3);
  cb_ctarg_6.push_back(v2);
  cb_ctarg_6.wait_front(v2);
  cb_ctarg_3.reserve_back(v2);
  binary_op_init_common(get_compile_time_arg_val(6), get_compile_time_arg_val(2), get_compile_time_arg_val(3));
  tile_regs_acquire();
  mul_tiles_init(get_compile_time_arg_val(6), get_compile_time_arg_val(2));
  mul_tiles(get_compile_time_arg_val(6), get_compile_time_arg_val(2), v6, v6, v6);
  tile_regs_commit();
  tile_regs_wait();
  pack_tile<true>(v6, get_compile_time_arg_val(3), v6);
  tile_regs_release();
  cb_ctarg_6.pop_front(v2);
  cb_ctarg_3.push_back(v2);
  cb_ctarg_2.pop_front(v2);
  cb_ctarg_1.pop_front(v3);
  cb_ctarg_0.pop_front(v3);
  return;
}

