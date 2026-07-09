#define REDUCE_OP PoolType::SUM
#define REDUCE_DIM ReduceDim::REDUCE_COL
#include <cstdint>
#include "api/compile_time_args.h"
#include "api/compute/bcast.h"
#include "api/compute/common.h"
#include "api/compute/eltwise_binary.h"
#include "api/compute/eltwise_binary_sfpu.h"
#include "api/compute/eltwise_unary/eltwise_unary.h"
#include "api/compute/eltwise_unary/fill.h"
#include "api/compute/eltwise_unary/rsqrt.h"
#include "api/compute/eltwise_unary/typecast.h"
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
  float v1 = 9.999999740e-06f;
  float v2 = 1.000000000e+00f;
  int32_t v3 = 1;
  size_t v4 = 64;
  size_t v5 = 63;
  size_t v6 = 1;
  size_t v7 = 0;
  CircularBuffer cb_ctarg_6(get_compile_time_arg_val(6));
  CircularBuffer cb_ctarg_8(get_compile_time_arg_val(8));
  CircularBuffer cb_ctarg_9(get_compile_time_arg_val(9));
  CircularBuffer cb_ctarg_5(get_compile_time_arg_val(5));
  CircularBuffer cb_ctarg_7(get_compile_time_arg_val(7));
  CircularBuffer cb_ctarg_2(get_compile_time_arg_val(2));
  CircularBuffer cb_ctarg_1(get_compile_time_arg_val(1));
  CircularBuffer cb_ctarg_4(get_compile_time_arg_val(4));
  CircularBuffer cb_ctarg_0(get_compile_time_arg_val(0));
  CircularBuffer cb_ctarg_3(get_compile_time_arg_val(3));
  CircularBuffer cb_ctarg_10(get_compile_time_arg_val(10));
  CircularBuffer cb_ctarg_11(get_compile_time_arg_val(11));
  cb_ctarg_2.wait_front(v3);
  cb_ctarg_0.wait_front(v3);
  cb_ctarg_5.reserve_back(v3);
  cb_ctarg_10.reserve_back(v3);
  init_sfpu(get_compile_time_arg_val(0), get_compile_time_arg_val(10));
  tile_regs_acquire();
  copy_tile_init(get_compile_time_arg_val(0));
  copy_tile(get_compile_time_arg_val(0), v7, v7);
  typecast_tile_init<static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float16_b), static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float32)>();
  typecast_tile<static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float16_b), static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float32)>(v7);
  mul_binary_tile_init();
  mul_binary_tile(v7, v7, v7);
  tile_regs_commit();
  tile_regs_wait();
  pack_tile<true>(v7, get_compile_time_arg_val(10), v7);
  tile_regs_release();
  cb_ctarg_10.push_back(v3);
  cb_ctarg_10.wait_front(v3);
  cb_ctarg_11.reserve_back(v3);
  init_sfpu(get_compile_time_arg_val(11), get_compile_time_arg_val(11));
  tile_regs_acquire();
  fill_tile_init();
  fill_tile(v7, v2);
  tile_regs_commit();
  tile_regs_wait();
  pack_tile<true>(v7, get_compile_time_arg_val(11), v7);
  tile_regs_release();
  cb_ctarg_11.push_back(v3);
  cb_ctarg_11.wait_front(v3);
  init_sfpu(get_compile_time_arg_val(10), get_compile_time_arg_val(5));
  tile_regs_acquire();
  reduce_init<PoolType::SUM, ReduceDim::REDUCE_ROW, false>(get_compile_time_arg_val(10), get_compile_time_arg_val(11), get_compile_time_arg_val(5));
  reduce_tile<PoolType::SUM, ReduceDim::REDUCE_ROW, false>(get_compile_time_arg_val(10), get_compile_time_arg_val(11), v7, v7, v7);
  reduce_uninit();
  tile_regs_commit();
  tile_regs_wait();
  pack_tile<true>(v7, get_compile_time_arg_val(5), v7);
  tile_regs_release();
  cb_ctarg_11.pop_front(v3);
  cb_ctarg_10.pop_front(v3);
  cb_ctarg_5.push_back(v3);
  cb_ctarg_0.pop_front(v3);
  cb_ctarg_5.wait_front(v3);
  cb_ctarg_6.reserve_back(v3);
  init_sfpu(get_compile_time_arg_val(5), get_compile_time_arg_val(6));
  tile_regs_acquire();
  copy_tile_init(get_compile_time_arg_val(5));
  copy_tile(get_compile_time_arg_val(5), v7, v7);
  tile_regs_commit();
  tile_regs_wait();
  pack_tile<true>(v7, get_compile_time_arg_val(6), v7);
  tile_regs_release();
  cb_ctarg_6.push_back(v3);
  cb_ctarg_5.pop_front(v3);
  for (size_t i8 = v7; i8 < v5; i8 += v6) {
    cb_ctarg_0.wait_front(v3);
    cb_ctarg_5.reserve_back(v3);
    cb_ctarg_10.reserve_back(v3);
    init_sfpu(get_compile_time_arg_val(0), get_compile_time_arg_val(10));
    tile_regs_acquire();
    copy_tile_init(get_compile_time_arg_val(0));
    copy_tile(get_compile_time_arg_val(0), v7, v7);
    typecast_tile_init<static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float16_b), static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float32)>();
    typecast_tile<static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float16_b), static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float32)>(v7);
    mul_binary_tile_init();
    mul_binary_tile(v7, v7, v7);
    tile_regs_commit();
    tile_regs_wait();
    pack_tile<true>(v7, get_compile_time_arg_val(10), v7);
    tile_regs_release();
    cb_ctarg_10.push_back(v3);
    cb_ctarg_10.wait_front(v3);
    cb_ctarg_11.reserve_back(v3);
    init_sfpu(get_compile_time_arg_val(11), get_compile_time_arg_val(11));
    tile_regs_acquire();
    fill_tile_init();
    fill_tile(v7, v2);
    tile_regs_commit();
    tile_regs_wait();
    pack_tile<true>(v7, get_compile_time_arg_val(11), v7);
    tile_regs_release();
    cb_ctarg_11.push_back(v3);
    cb_ctarg_11.wait_front(v3);
    init_sfpu(get_compile_time_arg_val(10), get_compile_time_arg_val(5));
    tile_regs_acquire();
    reduce_init<PoolType::SUM, ReduceDim::REDUCE_ROW, false>(get_compile_time_arg_val(10), get_compile_time_arg_val(11), get_compile_time_arg_val(5));
    reduce_tile<PoolType::SUM, ReduceDim::REDUCE_ROW, false>(get_compile_time_arg_val(10), get_compile_time_arg_val(11), v7, v7, v7);
    reduce_uninit();
    tile_regs_commit();
    tile_regs_wait();
    pack_tile<true>(v7, get_compile_time_arg_val(5), v7);
    tile_regs_release();
    cb_ctarg_11.pop_front(v3);
    cb_ctarg_10.pop_front(v3);
    cb_ctarg_5.push_back(v3);
    cb_ctarg_0.pop_front(v3);
    cb_ctarg_5.wait_front(v3);
    cb_ctarg_6.wait_front(v3);
    cb_ctarg_6.reserve_back(v3);
    binary_op_init_common(get_compile_time_arg_val(6), get_compile_time_arg_val(5), get_compile_time_arg_val(6));
    tile_regs_acquire();
    add_tiles_init(get_compile_time_arg_val(6), get_compile_time_arg_val(5));
    add_tiles(get_compile_time_arg_val(6), get_compile_time_arg_val(5), v7, v7, v7);
    tile_regs_commit();
    tile_regs_wait();
    pack_tile<true>(v7, get_compile_time_arg_val(6), v7);
    tile_regs_release();
    cb_ctarg_6.push_back(v3);
    cb_ctarg_6.pop_front(v3);
    cb_ctarg_5.pop_front(v3);
  }
  cb_ctarg_6.wait_front(v3);
  cb_ctarg_7.reserve_back(v3);
  init_sfpu(get_compile_time_arg_val(6), get_compile_time_arg_val(7));
  tile_regs_acquire();
  unary_bcast_init<BroadcastType::COL>(get_compile_time_arg_val(6), get_compile_time_arg_val(7));
  unary_bcast<BroadcastType::COL>(get_compile_time_arg_val(6), v7, v7);
  copy_tile_init(get_compile_time_arg_val(2));
  copy_tile(get_compile_time_arg_val(2), v7, v6);
  mul_binary_tile_init();
  mul_binary_tile(v7, v6, v7);
  fill_tile_init();
  fill_tile(v6, v1);
  add_binary_tile_init();
  add_binary_tile(v7, v6, v7);
  tile_regs_commit();
  tile_regs_wait();
  pack_tile<true>(v7, get_compile_time_arg_val(7), v7);
  tile_regs_release();
  cb_ctarg_7.push_back(v3);
  cb_ctarg_6.pop_front(v3);
  cb_ctarg_7.wait_front(v3);
  cb_ctarg_8.reserve_back(v3);
  init_sfpu(get_compile_time_arg_val(7), get_compile_time_arg_val(8));
  tile_regs_acquire();
  copy_tile_init(get_compile_time_arg_val(7));
  copy_tile(get_compile_time_arg_val(7), v7, v7);
  rsqrt_tile_init();
  rsqrt_tile(v7);
  tile_regs_commit();
  tile_regs_wait();
  pack_tile<true>(v7, get_compile_time_arg_val(8), v7);
  tile_regs_release();
  cb_ctarg_8.push_back(v3);
  cb_ctarg_7.pop_front(v3);
  cb_ctarg_8.wait_front(v3);
  for (size_t i9 = v7; i9 < v4; i9 += v6) {
    cb_ctarg_0.wait_front(v3);
    cb_ctarg_1.wait_front(v3);
    cb_ctarg_3.reserve_back(v3);
    cb_ctarg_4.reserve_back(v3);
    init_sfpu(get_compile_time_arg_val(0), get_compile_time_arg_val(3));
    tile_regs_acquire();
    copy_tile_init(get_compile_time_arg_val(0));
    copy_tile(get_compile_time_arg_val(0), v7, v7);
    typecast_tile_init<static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float16_b), static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float32)>();
    typecast_tile<static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float16_b), static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float32)>(v7);
    tile_regs_commit();
    tile_regs_wait();
    pack_tile<true>(v7, get_compile_time_arg_val(3), v7);
    tile_regs_release();
    init_sfpu(get_compile_time_arg_val(1), get_compile_time_arg_val(4));
    tile_regs_acquire();
    copy_tile_init(get_compile_time_arg_val(1));
    copy_tile(get_compile_time_arg_val(1), v7, v7);
    typecast_tile_init<static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float16_b), static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float32)>();
    typecast_tile<static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float16_b), static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float32)>(v7);
    tile_regs_commit();
    tile_regs_wait();
    pack_tile<true>(v7, get_compile_time_arg_val(4), v7);
    tile_regs_release();
    cb_ctarg_4.push_back(v3);
    cb_ctarg_3.push_back(v3);
    cb_ctarg_1.pop_front(v3);
    cb_ctarg_0.pop_front(v3);
    cb_ctarg_3.wait_front(v3);
    cb_ctarg_4.wait_front(v3);
    cb_ctarg_9.reserve_back(v3);
    binary_op_init_common(get_compile_time_arg_val(3), get_compile_time_arg_val(8), get_compile_time_arg_val(9));
    tile_regs_acquire();
    copy_tile_init(get_compile_time_arg_val(4));
    copy_tile(get_compile_time_arg_val(4), v7, v6);
    mul_tiles_init(get_compile_time_arg_val(3), get_compile_time_arg_val(8));
    mul_tiles(get_compile_time_arg_val(3), get_compile_time_arg_val(8), v7, v7, v7);
    mul_binary_tile_init();
    mul_binary_tile(v7, v6, v7);
    tile_regs_commit();
    tile_regs_wait();
    pack_tile<true>(v7, get_compile_time_arg_val(9), v7);
    tile_regs_release();
    cb_ctarg_9.push_back(v3);
    cb_ctarg_4.pop_front(v3);
    cb_ctarg_3.pop_front(v3);
  }
  cb_ctarg_8.pop_front(v3);
  cb_ctarg_2.pop_front(v3);
  return;
}

