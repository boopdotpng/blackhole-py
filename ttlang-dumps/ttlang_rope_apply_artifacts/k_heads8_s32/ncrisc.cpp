#include <cstdint>
#include "api/compile_time_args.h"
#include "api/core_local_mem.h"
#include "api/dataflow/circular_buffer.h"
#include "api/dataflow/dataflow_api.h"
#include "api/dataflow/endpoints.h"
#include "api/dataflow/noc.h"
#include "api/tensor/noc_traits.h"
#include "tools/profiler/kernel_profiler.hpp"
void kernel_main() {
  Noc noc0(0);
  int8_t v1 = 0;
  int32_t v2 = 2;
  int32_t v3 = 0;
  int32_t v4 = 2048;
  size_t v5 = 2;
  int32_t v6 = 1;
  size_t v7 = 0;
  size_t v8 = 8;
  size_t v9 = 1;
  CircularBuffer cb_ctarg_3(get_compile_time_arg_val(3));
  CircularBuffer cb_ctarg_2(get_compile_time_arg_val(2));
  CircularBuffer cb_ctarg_5(get_compile_time_arg_val(5));
  CircularBuffer cb_ctarg_4(get_compile_time_arg_val(4));
  CircularBuffer cb_ctarg_1(get_compile_time_arg_val(1));
  CircularBuffer cb_ctarg_0(get_compile_time_arg_val(0));
  for (size_t i10 = v7; i10 < v8; i10 += v9) {
    cb_ctarg_0.reserve_back(v6);
    int32_t v11 = get_common_arg_val<uint32_t>(v5);
    auto tensor_accessor_args_0 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<0, 8>(), 2>();
    TensorAccessor v12 = TensorAccessor(tensor_accessor_args_0, v11, v4);
    size_t v13 = i10 * v5;
    ptrdiff_t v14 = (ptrdiff_t) v13;
    int32_t v15 = (int32_t) v14;
    noc0.async_read(v12, CoreLocalMem<uint32_t>(cb_ctarg_0.get_write_ptr()), v12.get_aligned_page_size(), {.page_id = static_cast<uint32_t>(v15)}, {});
    noc0.async_read_barrier();
    cb_ctarg_0.push_back(v6);
    cb_ctarg_1.reserve_back(v6);
    auto tensor_accessor_args_1 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<0, 8>(), 2>();
    TensorAccessor v16 = TensorAccessor(tensor_accessor_args_1, v11, v4);
    size_t v17 = v13 + v9;
    ptrdiff_t v18 = (ptrdiff_t) v17;
    int32_t v19 = (int32_t) v18;
    noc0.async_read(v16, CoreLocalMem<uint32_t>(cb_ctarg_1.get_write_ptr()), v16.get_aligned_page_size(), {.page_id = static_cast<uint32_t>(v19)}, {});
    noc0.async_read_barrier();
    cb_ctarg_1.push_back(v6);
    cb_ctarg_2.reserve_back(v6);
    int32_t v20 = get_common_arg_val<uint32_t>(v7);
    auto tensor_accessor_args_2 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<1, 8>(), 0>();
    TensorAccessor v21 = TensorAccessor(tensor_accessor_args_2, v20, v4);
    noc0.async_read(v21, CoreLocalMem<uint32_t>(cb_ctarg_2.get_write_ptr()), v21.get_aligned_page_size(), {.page_id = static_cast<uint32_t>(v3)}, {});
    noc0.async_read_barrier();
    cb_ctarg_2.push_back(v6);
    cb_ctarg_3.reserve_back(v6);
    auto tensor_accessor_args_3 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<1, 8>(), 0>();
    TensorAccessor v22 = TensorAccessor(tensor_accessor_args_3, v20, v4);
    noc0.async_read(v22, CoreLocalMem<uint32_t>(cb_ctarg_3.get_write_ptr()), v22.get_aligned_page_size(), {.page_id = static_cast<uint32_t>(v6)}, {});
    noc0.async_read_barrier();
    cb_ctarg_3.push_back(v6);
    cb_ctarg_4.reserve_back(v6);
    int32_t v23 = get_common_arg_val<uint32_t>(v9);
    auto tensor_accessor_args_4 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<2, 8>(), 1>();
    TensorAccessor v24 = TensorAccessor(tensor_accessor_args_4, v23, v4);
    noc0.async_read(v24, CoreLocalMem<uint32_t>(cb_ctarg_4.get_write_ptr()), v24.get_aligned_page_size(), {.page_id = static_cast<uint32_t>(v3)}, {});
    noc0.async_read_barrier();
    cb_ctarg_4.push_back(v6);
    cb_ctarg_5.reserve_back(v6);
    auto tensor_accessor_args_5 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<2, 8>(), 1>();
    TensorAccessor v25 = TensorAccessor(tensor_accessor_args_5, v23, v4);
    noc0.async_read(v25, CoreLocalMem<uint32_t>(cb_ctarg_5.get_write_ptr()), v25.get_aligned_page_size(), {.page_id = static_cast<uint32_t>(v6)}, {});
    noc0.async_read_barrier();
    cb_ctarg_5.push_back(v6);
  }
  return;
}

