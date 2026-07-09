#include <cstdint>
#include "api/compile_time_args.h"
#include "api/compute/common.h"
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
  int32_t v1 = 1;
  size_t v2 = 0;
  CircularBuffer cb_ctarg_0(get_compile_time_arg_val(0));
  CircularBuffer cb_ctarg_2(get_compile_time_arg_val(2));
  CircularBuffer cb_ctarg_1(get_compile_time_arg_val(1));
  CircularBuffer cb_ctarg_3(get_compile_time_arg_val(3));
  cb_ctarg_0.wait_front(v1);
  cb_ctarg_2.reserve_back(v1);
  init_sfpu(get_compile_time_arg_val(0), get_compile_time_arg_val(2));
  tile_regs_acquire();
  copy_tile_init(get_compile_time_arg_val(0));
  copy_tile(get_compile_time_arg_val(0), v2, v2);
  tile_regs_commit();
  tile_regs_wait();
  pack_tile<true>(v2, get_compile_time_arg_val(2), v2);
  tile_regs_release();
  cb_ctarg_2.push_back(v1);
  cb_ctarg_0.pop_front(v1);
  cb_ctarg_1.wait_front(v1);
  cb_ctarg_3.reserve_back(v1);
  init_sfpu(get_compile_time_arg_val(1), get_compile_time_arg_val(3));
  tile_regs_acquire();
  copy_tile_init(get_compile_time_arg_val(1));
  copy_tile(get_compile_time_arg_val(1), v2, v2);
  tile_regs_commit();
  tile_regs_wait();
  pack_tile<true>(v2, get_compile_time_arg_val(3), v2);
  tile_regs_release();
  cb_ctarg_3.push_back(v1);
  cb_ctarg_1.pop_front(v1);
  return;
}

