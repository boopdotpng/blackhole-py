#include <cstdint>
#include "api/compile_time_args.h"
#include "api/compute/common.h"
#include "api/compute/eltwise_binary.h"
#include "api/compute/eltwise_binary_sfpu.h"
#include "api/compute/pack.h"
#include "api/compute/reg_api.h"
#include "api/dataflow/circular_buffer.h"
#include "tools/profiler/kernel_profiler.hpp"
inline uint32_t float_to_bits(const float f) { uint32_t r; __builtin_memcpy(&r, &f, sizeof(r)); return r; }
#ifndef INFINITY
#define INFINITY __builtin_inff()
#endif
void kernel_main() {
  int32_t v1 = 1;
  size_t v2 = 1;
  size_t v3 = 0;
  size_t v4 = 8;
  CircularBuffer cb_ctarg_3(get_compile_time_arg_val(3));
  CircularBuffer cb_ctarg_2(get_compile_time_arg_val(2));
  CircularBuffer cb_ctarg_7(get_compile_time_arg_val(7));
  CircularBuffer cb_ctarg_6(get_compile_time_arg_val(6));
  CircularBuffer cb_ctarg_5(get_compile_time_arg_val(5));
  CircularBuffer cb_ctarg_4(get_compile_time_arg_val(4));
  CircularBuffer cb_ctarg_1(get_compile_time_arg_val(1));
  CircularBuffer cb_ctarg_0(get_compile_time_arg_val(0));
  for (size_t i5 = v3; i5 < v4; i5 += v2) {
    cb_ctarg_0.wait_front(v1);
    cb_ctarg_1.wait_front(v1);
    cb_ctarg_2.wait_front(v1);
    cb_ctarg_3.wait_front(v1);
    cb_ctarg_4.wait_front(v1);
    cb_ctarg_5.wait_front(v1);
    cb_ctarg_6.reserve_back(v1);
    cb_ctarg_7.reserve_back(v1);
    binary_op_init_common(get_compile_time_arg_val(0), get_compile_time_arg_val(2), get_compile_time_arg_val(6));
    tile_regs_acquire();
    mul_tiles_init(get_compile_time_arg_val(0), get_compile_time_arg_val(2));
    mul_tiles(get_compile_time_arg_val(0), get_compile_time_arg_val(2), v3, v3, v3);
    mul_tiles_init(get_compile_time_arg_val(1), get_compile_time_arg_val(4));
    mul_tiles(get_compile_time_arg_val(1), get_compile_time_arg_val(4), v3, v3, v2);
    sub_binary_tile_init();
    sub_binary_tile(v3, v2, v3);
    tile_regs_commit();
    tile_regs_wait();
    pack_tile<true>(v3, get_compile_time_arg_val(6), v3);
    tile_regs_release();
    binary_op_init_common(get_compile_time_arg_val(1), get_compile_time_arg_val(3), get_compile_time_arg_val(7));
    tile_regs_acquire();
    mul_tiles_init(get_compile_time_arg_val(1), get_compile_time_arg_val(3));
    mul_tiles(get_compile_time_arg_val(1), get_compile_time_arg_val(3), v3, v3, v3);
    mul_tiles_init(get_compile_time_arg_val(0), get_compile_time_arg_val(5));
    mul_tiles(get_compile_time_arg_val(0), get_compile_time_arg_val(5), v3, v3, v2);
    add_binary_tile_init();
    add_binary_tile(v3, v2, v3);
    tile_regs_commit();
    tile_regs_wait();
    pack_tile<true>(v3, get_compile_time_arg_val(7), v3);
    tile_regs_release();
    cb_ctarg_7.push_back(v1);
    cb_ctarg_6.push_back(v1);
    cb_ctarg_5.pop_front(v1);
    cb_ctarg_4.pop_front(v1);
    cb_ctarg_3.pop_front(v1);
    cb_ctarg_2.pop_front(v1);
    cb_ctarg_1.pop_front(v1);
    cb_ctarg_0.pop_front(v1);
  }
  return;
}

