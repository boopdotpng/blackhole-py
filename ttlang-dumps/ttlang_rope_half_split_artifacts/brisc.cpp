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
  int8_t v1 = 1;
  int32_t v2 = 0;
  int32_t v3 = 2048;
  int32_t v4 = 1;
  size_t v5 = 0;
  CircularBuffer cb_ctarg_6(get_compile_time_arg_val(6));
  CircularBuffer cb_ctarg_7(get_compile_time_arg_val(7));
  cb_ctarg_6.wait_front(v4);
  int32_t v6 = get_common_arg_val<uint32_t>(v5);
  auto tensor_accessor_args_0 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<3, 8>(), 0>();
  TensorAccessor v7 = TensorAccessor(tensor_accessor_args_0, v6, v3);
  noc1.async_write(CoreLocalMem<uint32_t>(cb_ctarg_6.get_read_ptr()), v7, v7.get_aligned_page_size(), {} , {.page_id = static_cast<uint32_t>(v2)});
  noc1.async_write_barrier();
  cb_ctarg_6.pop_front(v4);
  cb_ctarg_7.wait_front(v4);
  auto tensor_accessor_args_1 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<3, 8>(), 0>();
  TensorAccessor v8 = TensorAccessor(tensor_accessor_args_1, v6, v3);
  noc1.async_write(CoreLocalMem<uint32_t>(cb_ctarg_7.get_read_ptr()), v8, v8.get_aligned_page_size(), {} , {.page_id = static_cast<uint32_t>(v4)});
  noc1.async_write_barrier();
  cb_ctarg_7.pop_front(v4);
  return;
}

