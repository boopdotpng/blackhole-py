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
  size_t v1 = 4;
  size_t v2 = 1;
  int8_t v3 = 1;
  size_t v4 = 2048;
  int32_t v5 = 0;
  int32_t v6 = 2048;
  int32_t v7 = 4;
  size_t v8 = 0;
  CircularBuffer cb_ctarg_2(get_compile_time_arg_val(2));
  cb_ctarg_2.wait_front(v7);
  int32_t v9 = get_common_arg_val<uint32_t>(v8);
  auto tensor_accessor_args_0 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<2, 3>(), 0>();
  TensorAccessor v10 = TensorAccessor(tensor_accessor_args_0, v9, v6);
  ptrdiff_t v11 = (ptrdiff_t) cb_ctarg_2.get_read_ptr();
  size_t v12 = (size_t) v11;
  for (size_t i13 = v8; i13 < v1; i13 += v2) {
    size_t v14 = i13 * v4;
    size_t v15 = v12 + v14;
    ptrdiff_t v16 = (ptrdiff_t) i13;
    int32_t v17 = (int32_t) v16;
    ptrdiff_t v18 = (ptrdiff_t) v15;
    int32_t v19 = (int32_t) v18;
    noc1.async_write(CoreLocalMem<uint32_t>(v19), v10, v10.get_aligned_page_size(), {} , {.page_id = static_cast<uint32_t>(v17)});
  }
  noc1.async_write_barrier();
  cb_ctarg_2.pop_front(v7);
  return;
}

