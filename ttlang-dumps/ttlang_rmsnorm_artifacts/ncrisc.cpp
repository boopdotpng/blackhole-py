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
  int32_t v1 = 2;
  int32_t v2 = 2048;
  size_t v3 = 2;
  int8_t v4 = 0;
  int32_t v5 = 0;
  int32_t v6 = 4096;
  int32_t v7 = 1;
  size_t v8 = 64;
  size_t v9 = 1;
  size_t v10 = 0;
  CircularBuffer cb_ctarg_2(get_compile_time_arg_val(2));
  CircularBuffer cb_ctarg_1(get_compile_time_arg_val(1));
  CircularBuffer cb_ctarg_0(get_compile_time_arg_val(0));
  cb_ctarg_2.reserve_back(v7);
  int32_t v11 = get_common_arg_val<uint32_t>(v10);
  auto tensor_accessor_args_0 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<2, 12>(), 0>();
  TensorAccessor v12 = TensorAccessor(tensor_accessor_args_0, v11, v6);
  noc0.async_read(v12, CoreLocalMem<uint32_t>(cb_ctarg_2.get_write_ptr()), v12.get_aligned_page_size(), {.page_id = static_cast<uint32_t>(v5)}, {});
  noc0.async_read_barrier();
  cb_ctarg_2.push_back(v7);
  for (size_t i13 = v10; i13 < v8; i13 += v9) {
    cb_ctarg_0.reserve_back(v7);
    int32_t v14 = get_common_arg_val<uint32_t>(v3);
    auto tensor_accessor_args_1 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<0, 12>(), 2>();
    TensorAccessor v15 = TensorAccessor(tensor_accessor_args_1, v14, v2);
    ptrdiff_t v16 = (ptrdiff_t) i13;
    int32_t v17 = (int32_t) v16;
    noc0.async_read(v15, CoreLocalMem<uint32_t>(cb_ctarg_0.get_write_ptr()), v15.get_aligned_page_size(), {.page_id = static_cast<uint32_t>(v17)}, {});
    noc0.async_read_barrier();
    cb_ctarg_0.push_back(v7);
  }
  for (size_t i18 = v10; i18 < v8; i18 += v9) {
    cb_ctarg_0.reserve_back(v7);
    int32_t v19 = get_common_arg_val<uint32_t>(v3);
    auto tensor_accessor_args_2 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<0, 12>(), 2>();
    TensorAccessor v20 = TensorAccessor(tensor_accessor_args_2, v19, v2);
    ptrdiff_t v21 = (ptrdiff_t) i18;
    int32_t v22 = (int32_t) v21;
    noc0.async_read(v20, CoreLocalMem<uint32_t>(cb_ctarg_0.get_write_ptr()), v20.get_aligned_page_size(), {.page_id = static_cast<uint32_t>(v22)}, {});
    noc0.async_read_barrier();
    cb_ctarg_0.push_back(v7);
    cb_ctarg_1.reserve_back(v7);
    int32_t v23 = get_common_arg_val<uint32_t>(v9);
    auto tensor_accessor_args_3 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<1, 12>(), 1>();
    TensorAccessor v24 = TensorAccessor(tensor_accessor_args_3, v23, v2);
    noc0.async_read(v24, CoreLocalMem<uint32_t>(cb_ctarg_1.get_write_ptr()), v24.get_aligned_page_size(), {.page_id = static_cast<uint32_t>(v22)}, {});
    noc0.async_read_barrier();
    cb_ctarg_1.push_back(v7);
  }
  return;
}

