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
  size_t v1 = 14;
  size_t v2 = 512;
  size_t v3 = 1;
  int8_t v4 = 0;
  int32_t v5 = 0;
  int32_t v6 = 2048;
  size_t v7 = 0;
  int32_t v8 = 1;
  size_t v9 = 4;
  CircularBuffer cb_ctarg_0(get_compile_time_arg_val(0));
  CircularBuffer cb_ctarg_1(get_compile_time_arg_val(1));
  size_t v10 = get_absolute_logical_x();
  size_t v11 = get_absolute_logical_y();
  size_t v12 = v11 / v9;
  cb_ctarg_0.reserve_back(v8);
  int32_t v13 = get_common_arg_val<uint32_t>(v7);
  auto tensor_accessor_args_0 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<0, 4>(), 0>();
  TensorAccessor v14 = TensorAccessor(tensor_accessor_args_0, v13, v6);
  size_t v15 = v12 * v2;
  size_t v16 = v15 + v1;
  size_t v17 = v16 + v10;
  ptrdiff_t v18 = (ptrdiff_t) v17;
  int32_t v19 = (int32_t) v18;
  noc0.async_read(v14, CoreLocalMem<uint32_t>(cb_ctarg_0.get_write_ptr()), v14.get_aligned_page_size(), {.page_id = static_cast<uint32_t>(v19)}, {});
  noc0.async_read_barrier();
  cb_ctarg_0.push_back(v8);
  cb_ctarg_1.reserve_back(v8);
  int32_t v20 = get_common_arg_val<uint32_t>(v3);
  auto tensor_accessor_args_1 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<1, 4>(), 1>();
  TensorAccessor v21 = TensorAccessor(tensor_accessor_args_1, v20, v6);
  noc0.async_read(v21, CoreLocalMem<uint32_t>(cb_ctarg_1.get_write_ptr()), v21.get_aligned_page_size(), {.page_id = static_cast<uint32_t>(v19)}, {});
  noc0.async_read_barrier();
  cb_ctarg_1.push_back(v8);
  return;
}

