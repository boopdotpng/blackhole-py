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
  int32_t v3 = 4096;
  int32_t v4 = 1;
  size_t v5 = 64;
  size_t v6 = 1;
  size_t v7 = 0;
  CircularBuffer cb_ctarg_9(get_compile_time_arg_val(9));
  for (size_t i8 = v7; i8 < v5; i8 += v6) {
    cb_ctarg_9.wait_front(v4);
    int32_t v9 = get_common_arg_val<uint32_t>(v7);
    auto tensor_accessor_args_0 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<3, 12>(), 0>();
    TensorAccessor v10 = TensorAccessor(tensor_accessor_args_0, v9, v3);
    ptrdiff_t v11 = (ptrdiff_t) i8;
    int32_t v12 = (int32_t) v11;
    noc1.async_write(CoreLocalMem<uint32_t>(cb_ctarg_9.get_read_ptr()), v10, v10.get_aligned_page_size(), {} , {.page_id = static_cast<uint32_t>(v12)});
    noc1.async_write_barrier();
    cb_ctarg_9.pop_front(v4);
  }
  return;
}

