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
  size_t v1 = 4;
  int8_t v2 = 0;
  size_t v3 = 4096;
  int32_t v4 = 1;
  int32_t v5 = 0;
  int32_t v6 = 4096;
  size_t v7 = 1;
  int32_t v8 = 4;
  size_t v9 = 0;
  CircularBuffer cb_ctarg_1(get_compile_time_arg_val(1));
  CircularBuffer cb_ctarg_0(get_compile_time_arg_val(0));
  size_t v10 = get_absolute_logical_y();
  cb_ctarg_0.reserve_back(v8);
  cb_ctarg_1.reserve_back(v8);
  int32_t v11 = get_common_arg_val<uint32_t>(v7);
  auto tensor_accessor_args_0 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<0, 3>(), 1>();
  TensorAccessor v12 = TensorAccessor(tensor_accessor_args_0, v11, v6);
  ptrdiff_t v13 = (ptrdiff_t) cb_ctarg_0.get_write_ptr();
  size_t v14 = (size_t) v13;
  for (size_t i15 = v9; i15 < v1; i15 += v7) {
    size_t v16 = v10 * v1;
    size_t v17 = v16 + i15;
    size_t v18 = i15 * v3;
    size_t v19 = v14 + v18;
    ptrdiff_t v20 = (ptrdiff_t) v17;
    int32_t v21 = (int32_t) v20;
    ptrdiff_t v22 = (ptrdiff_t) v19;
    int32_t v23 = (int32_t) v22;
    noc0.async_read(v12, CoreLocalMem<uint32_t>(v23), v12.get_aligned_page_size(), {.page_id = static_cast<uint32_t>(v21)}, {});
  }
  noc0.async_read_barrier();
  int32_t v24 = get_common_arg_val<uint32_t>(v9);
  auto tensor_accessor_args_1 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<1, 3>(), 0>();
  TensorAccessor v25 = TensorAccessor(tensor_accessor_args_1, v24, v6);
  ptrdiff_t v26 = (ptrdiff_t) cb_ctarg_1.get_write_ptr();
  size_t v27 = (size_t) v26;
  for (size_t i28 = v9; i28 < v1; i28 += v7) {
    size_t v29 = v10 * v1;
    size_t v30 = v29 + i28;
    size_t v31 = i28 * v3;
    size_t v32 = v27 + v31;
    ptrdiff_t v33 = (ptrdiff_t) v30;
    int32_t v34 = (int32_t) v33;
    ptrdiff_t v35 = (ptrdiff_t) v32;
    int32_t v36 = (int32_t) v35;
    noc0.async_read(v25, CoreLocalMem<uint32_t>(v36), v25.get_aligned_page_size(), {.page_id = static_cast<uint32_t>(v34)}, {});
  }
  noc0.async_read_barrier();
  cb_ctarg_1.push_back(v8);
  cb_ctarg_0.push_back(v8);
  return;
}

