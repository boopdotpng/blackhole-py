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
  size_t v1 = 2;
  size_t v2 = 1;
  int8_t v3 = 0;
  int32_t v4 = 0;
  int32_t v5 = 2048;
  int32_t v6 = 1;
  size_t v7 = 0;
  CircularBuffer cb_ctarg_0(get_compile_time_arg_val(0));
  CircularBuffer cb_ctarg_1(get_compile_time_arg_val(1));
  size_t v8 = get_absolute_logical_x();
  size_t v9 = get_absolute_logical_y();
  cb_ctarg_0.reserve_back(v6);
  int32_t v10 = get_common_arg_val<uint32_t>(v7);
  auto tensor_accessor_args_0 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<0, 4>(), 0>();
  TensorAccessor v11 = TensorAccessor(tensor_accessor_args_0, v10, v5);
  size_t v12 = v9 * v1;
  size_t v13 = v12 + v8;
  ptrdiff_t v14 = (ptrdiff_t) v13;
  int32_t v15 = (int32_t) v14;
  noc0.async_read(v11, CoreLocalMem<uint32_t>(cb_ctarg_0.get_write_ptr()), v11.get_aligned_page_size(), {.page_id = static_cast<uint32_t>(v15)}, {});
  noc0.async_read_barrier();
  cb_ctarg_0.push_back(v6);
  cb_ctarg_1.reserve_back(v6);
  int32_t v16 = get_common_arg_val<uint32_t>(v2);
  auto tensor_accessor_args_1 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<1, 4>(), 1>();
  TensorAccessor v17 = TensorAccessor(tensor_accessor_args_1, v16, v5);
  noc0.async_read(v17, CoreLocalMem<uint32_t>(cb_ctarg_1.get_write_ptr()), v17.get_aligned_page_size(), {.page_id = static_cast<uint32_t>(v15)}, {});
  noc0.async_read_barrier();
  cb_ctarg_1.push_back(v6);
  return;
}

