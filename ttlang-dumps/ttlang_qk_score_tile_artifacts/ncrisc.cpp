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
  int8_t v2 = 0;
  size_t v3 = 2048;
  int32_t v4 = 1;
  int32_t v5 = 0;
  int32_t v6 = 2048;
  size_t v7 = 1;
  int32_t v8 = 2;
  size_t v9 = 0;
  CircularBuffer cb_ctarg_1(get_compile_time_arg_val(1));
  CircularBuffer cb_ctarg_0(get_compile_time_arg_val(0));
  CircularBuffer cb_ctarg_2(get_compile_time_arg_val(2));
  cb_ctarg_0.reserve_back(v8);
  int32_t v10 = get_common_arg_val<uint32_t>(v7);
  auto tensor_accessor_args_0 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<0, 7>(), 1>();
  TensorAccessor v11 = TensorAccessor(tensor_accessor_args_0, v10, v6);
  ptrdiff_t v12 = (ptrdiff_t) cb_ctarg_0.get_write_ptr();
  size_t v13 = (size_t) v12;
  for (size_t i14 = v9; i14 < v1; i14 += v7) {
    size_t v15 = i14 * v3;
    size_t v16 = v13 + v15;
    ptrdiff_t v17 = (ptrdiff_t) i14;
    int32_t v18 = (int32_t) v17;
    ptrdiff_t v19 = (ptrdiff_t) v16;
    int32_t v20 = (int32_t) v19;
    noc0.async_read(v11, CoreLocalMem<uint32_t>(v20), v11.get_aligned_page_size(), {.page_id = static_cast<uint32_t>(v18)}, {});
  }
  noc0.async_read_barrier();
  cb_ctarg_0.push_back(v8);
  cb_ctarg_1.reserve_back(v8);
  int32_t v21 = get_common_arg_val<uint32_t>(v9);
  auto tensor_accessor_args_1 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<1, 7>(), 0>();
  TensorAccessor v22 = TensorAccessor(tensor_accessor_args_1, v21, v6);
  ptrdiff_t v23 = (ptrdiff_t) cb_ctarg_1.get_write_ptr();
  size_t v24 = (size_t) v23;
  for (size_t i25 = v9; i25 < v1; i25 += v7) {
    size_t v26 = i25 * v3;
    size_t v27 = v24 + v26;
    ptrdiff_t v28 = (ptrdiff_t) i25;
    int32_t v29 = (int32_t) v28;
    ptrdiff_t v30 = (ptrdiff_t) v27;
    int32_t v31 = (int32_t) v30;
    noc0.async_read(v22, CoreLocalMem<uint32_t>(v31), v22.get_aligned_page_size(), {.page_id = static_cast<uint32_t>(v29)}, {});
  }
  noc0.async_read_barrier();
  cb_ctarg_1.push_back(v8);
  cb_ctarg_2.reserve_back(v4);
  int32_t v32 = get_common_arg_val<uint32_t>(v1);
  auto tensor_accessor_args_2 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<2, 7>(), 2>();
  TensorAccessor v33 = TensorAccessor(tensor_accessor_args_2, v32, v6);
  noc0.async_read(v33, CoreLocalMem<uint32_t>(cb_ctarg_2.get_write_ptr()), v33.get_aligned_page_size(), {.page_id = static_cast<uint32_t>(v5)}, {});
  noc0.async_read_barrier();
  cb_ctarg_2.push_back(v4);
  return;
}

