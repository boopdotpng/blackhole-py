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
  Noc noc1(1);
  size_t v1 = 2;
  int8_t v2 = 1;
  int32_t v3 = 0;
  int32_t v4 = 2048;
  int32_t v5 = 1;
  size_t v6 = 1;
  size_t v7 = 0;
  size_t v8 = 32;
  CircularBuffer cb_ctarg_7(get_compile_time_arg_val(7));
  CircularBuffer cb_ctarg_6(get_compile_time_arg_val(6));
  for (size_t i9 = v7; i9 < v8; i9 += v6) {
    cb_ctarg_6.wait_front(v5);
    int32_t v10 = get_common_arg_val<uint32_t>(v7);
    auto tensor_accessor_args_0 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<3, 8>(), 0>();
    TensorAccessor v11 = TensorAccessor(tensor_accessor_args_0, v10, v4);
    size_t v12 = i9 * v1;
    ptrdiff_t v13 = (ptrdiff_t) v12;
    int32_t v14 = (int32_t) v13;
    noc1.async_write(CoreLocalMem<uint32_t>(cb_ctarg_6.get_read_ptr()), v11, v11.get_aligned_page_size(), {} , {.page_id = static_cast<uint32_t>(v14)});
    noc1.async_write_barrier();
    cb_ctarg_6.pop_front(v5);
    cb_ctarg_7.wait_front(v5);
    auto tensor_accessor_args_1 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<3, 8>(), 0>();
    TensorAccessor v15 = TensorAccessor(tensor_accessor_args_1, v10, v4);
    size_t v16 = v12 + v6;
    ptrdiff_t v17 = (ptrdiff_t) v16;
    int32_t v18 = (int32_t) v17;
    noc1.async_write(CoreLocalMem<uint32_t>(cb_ctarg_7.get_read_ptr()), v15, v15.get_aligned_page_size(), {} , {.page_id = static_cast<uint32_t>(v18)});
    noc1.async_write_barrier();
    cb_ctarg_7.pop_front(v5);
  }
  return;
}

