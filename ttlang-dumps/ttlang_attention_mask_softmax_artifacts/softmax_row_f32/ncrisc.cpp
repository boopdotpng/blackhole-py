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
  size_t v2 = 1;
  int8_t v3 = 0;
  size_t v4 = 4096;
  int32_t v5 = 0;
  int32_t v6 = 4096;
  int32_t v7 = 4;
  size_t v8 = 0;
  CircularBuffer cb_ctarg_0(get_compile_time_arg_val(0));
  CircularBuffer cb_ctarg_1(get_compile_time_arg_val(1));
  size_t v9 = get_absolute_logical_y();
  cb_ctarg_0.reserve_back(v7);
  cb_ctarg_1.reserve_back(v7);
  int32_t v10 = get_common_arg_val<uint32_t>(v8);
  auto tensor_accessor_args_0 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<0, 7>(), 0>();
  TensorAccessor v11 = TensorAccessor(tensor_accessor_args_0, v10, v6);
  ptrdiff_t v12 = (ptrdiff_t) cb_ctarg_0.get_write_ptr();
  size_t v13 = (size_t) v12;
  for (size_t i14 = v8; i14 < v1; i14 += v2) {
    size_t v15 = v9 * v1;
    size_t v16 = v15 + i14;
    size_t v17 = i14 * v4;
    size_t v18 = v13 + v17;
    ptrdiff_t v19 = (ptrdiff_t) v16;
    int32_t v20 = (int32_t) v19;
    ptrdiff_t v21 = (ptrdiff_t) v18;
    int32_t v22 = (int32_t) v21;
    noc0.async_read(v11, CoreLocalMem<uint32_t>(v22), v11.get_aligned_page_size(), {.page_id = static_cast<uint32_t>(v20)}, {});
  }
  noc0.async_read_barrier();
  auto tensor_accessor_args_1 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<0, 7>(), 0>();
  TensorAccessor v23 = TensorAccessor(tensor_accessor_args_1, v10, v6);
  ptrdiff_t v24 = (ptrdiff_t) cb_ctarg_1.get_write_ptr();
  size_t v25 = (size_t) v24;
  for (size_t i26 = v8; i26 < v1; i26 += v2) {
    size_t v27 = v9 * v1;
    size_t v28 = v27 + i26;
    size_t v29 = i26 * v4;
    size_t v30 = v25 + v29;
    ptrdiff_t v31 = (ptrdiff_t) v28;
    int32_t v32 = (int32_t) v31;
    ptrdiff_t v33 = (ptrdiff_t) v30;
    int32_t v34 = (int32_t) v33;
    noc0.async_read(v23, CoreLocalMem<uint32_t>(v34), v23.get_aligned_page_size(), {.page_id = static_cast<uint32_t>(v32)}, {});
  }
  noc0.async_read_barrier();
  cb_ctarg_1.push_back(v7);
  cb_ctarg_0.push_back(v7);
  return;
}

