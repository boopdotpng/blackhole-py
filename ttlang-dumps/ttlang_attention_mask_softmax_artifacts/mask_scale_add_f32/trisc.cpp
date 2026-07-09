#include <cstdint>
#include "api/compile_time_args.h"
#include "api/compute/common.h"
#include "api/compute/eltwise_binary_sfpu.h"
#include "api/compute/eltwise_unary/binop_with_scalar.h"
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
  int32_t v1 = 1040187392;
  size_t v2 = 7;
  size_t v3 = 6;
  size_t v4 = 5;
  size_t v5 = 4;
  size_t v6 = 3;
  size_t v7 = 2;
  int32_t v8 = 4;
  size_t v9 = 1;
  size_t v10 = 0;
  CircularBuffer cb_ctarg_1(get_compile_time_arg_val(1));
  CircularBuffer cb_ctarg_2(get_compile_time_arg_val(2));
  CircularBuffer cb_ctarg_0(get_compile_time_arg_val(0));
  cb_ctarg_0.wait_front(v8);
  cb_ctarg_1.wait_front(v8);
  cb_ctarg_2.reserve_back(v8);
  init_sfpu(get_compile_time_arg_val(0), get_compile_time_arg_val(2));
  tile_regs_acquire();
  copy_tile_init(get_compile_time_arg_val(0));
  copy_tile(get_compile_time_arg_val(0), v10, v10);
  copy_tile(get_compile_time_arg_val(0), v9, v7);
  copy_tile(get_compile_time_arg_val(0), v7, v5);
  copy_tile(get_compile_time_arg_val(0), v6, v3);
  copy_tile_init(get_compile_time_arg_val(1));
  copy_tile(get_compile_time_arg_val(1), v10, v9);
  copy_tile(get_compile_time_arg_val(1), v9, v6);
  copy_tile(get_compile_time_arg_val(1), v7, v4);
  copy_tile(get_compile_time_arg_val(1), v6, v2);
  binop_with_scalar_tile_init();
  { volatile int32_t __s = v1; mul_unary_tile(v10, __s); }
  binop_with_scalar_tile_init();
  { volatile int32_t __s = v1; mul_unary_tile(v7, __s); }
  binop_with_scalar_tile_init();
  { volatile int32_t __s = v1; mul_unary_tile(v5, __s); }
  binop_with_scalar_tile_init();
  { volatile int32_t __s = v1; mul_unary_tile(v3, __s); }
  add_binary_tile_init();
  add_binary_tile(v10, v9, v10);
  add_binary_tile(v7, v6, v7);
  add_binary_tile(v5, v4, v5);
  add_binary_tile(v3, v2, v3);
  tile_regs_commit();
  tile_regs_wait();
  pack_tile<true>(v10, get_compile_time_arg_val(2), v10);
  pack_tile<true>(v7, get_compile_time_arg_val(2), v9);
  pack_tile<true>(v5, get_compile_time_arg_val(2), v7);
  pack_tile<true>(v3, get_compile_time_arg_val(2), v6);
  tile_regs_release();
  cb_ctarg_2.push_back(v8);
  cb_ctarg_1.pop_front(v8);
  cb_ctarg_0.pop_front(v8);
  return;
}

