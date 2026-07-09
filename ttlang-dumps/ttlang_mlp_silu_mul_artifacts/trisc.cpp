#include <cstdint>
#include "api/compile_time_args.h"
#include "api/compute/common.h"
#include "api/compute/compute_kernel_api.h"
#include "api/compute/eltwise_binary_sfpu.h"
#include "api/compute/eltwise_unary/eltwise_unary.h"
#include "api/compute/pack.h"
#include "api/compute/reg_api.h"
#include "api/compute/tile_move_copy.h"
#include "api/dataflow/circular_buffer.h"
#include "tools/profiler/kernel_profiler.hpp"
inline uint32_t float_to_bits(const float f) { uint32_t r; __builtin_memcpy(&r, &f, sizeof(r)); return r; }
#ifndef INFINITY
#define INFINITY __builtin_inff()
#endif
void kernel_main() {
  size_t v1 = 7;
  size_t v2 = 6;
  size_t v3 = 5;
  size_t v4 = 4;
  size_t v5 = 3;
  size_t v6 = 2;
  int32_t v7 = 4;
  size_t v8 = 1;
  size_t v9 = 0;
  CircularBuffer cb_ctarg_0(get_compile_time_arg_val(0));
  CircularBuffer cb_ctarg_2(get_compile_time_arg_val(2));
  CircularBuffer cb_ctarg_1(get_compile_time_arg_val(1));
  cb_ctarg_0.wait_front(v7);
  cb_ctarg_1.wait_front(v7);
  cb_ctarg_2.reserve_back(v7);
  init_sfpu(get_compile_time_arg_val(0), get_compile_time_arg_val(2));
  tile_regs_acquire();
  copy_tile_init(get_compile_time_arg_val(0));
  copy_tile(get_compile_time_arg_val(0), v9, v9);
  copy_tile(get_compile_time_arg_val(0), v8, v6);
  copy_tile(get_compile_time_arg_val(0), v6, v4);
  copy_tile(get_compile_time_arg_val(0), v5, v2);
  copy_tile_init(get_compile_time_arg_val(1));
  copy_tile(get_compile_time_arg_val(1), v9, v8);
  copy_tile(get_compile_time_arg_val(1), v8, v5);
  copy_tile(get_compile_time_arg_val(1), v6, v3);
  copy_tile(get_compile_time_arg_val(1), v5, v1);
  silu_tile_init();
  silu_tile(v9);
  silu_tile(v6);
  silu_tile(v4);
  silu_tile(v2);
  mul_binary_tile_init();
  mul_binary_tile(v9, v8, v9);
  mul_binary_tile(v6, v5, v6);
  mul_binary_tile(v4, v3, v4);
  mul_binary_tile(v2, v1, v2);
  tile_regs_commit();
  tile_regs_wait();
  pack_tile<true>(v9, get_compile_time_arg_val(2), v9);
  pack_tile<true>(v6, get_compile_time_arg_val(2), v8);
  pack_tile<true>(v4, get_compile_time_arg_val(2), v6);
  pack_tile<true>(v2, get_compile_time_arg_val(2), v5);
  tile_regs_release();
  cb_ctarg_2.push_back(v7);
  cb_ctarg_1.pop_front(v7);
  cb_ctarg_0.pop_front(v7);
  return;
}

