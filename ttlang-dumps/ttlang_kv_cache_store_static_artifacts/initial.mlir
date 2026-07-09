module attributes {ttl.launch_grid = [2, 8], ttl.target_arch = "blackhole"} {
  func.func @compute() attributes {ttl.base_cta_index = 4 : i32, ttl.crta_indices = [], ttl.kernel_thread = #ttkernel.thread<compute>} {
    %0 = ttl.bind_cb{cb_index = 0, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %1 = ttl.bind_cb{cb_index = 2, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %2 = ttl.bind_cb{cb_index = 1, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %3 = ttl.bind_cb{cb_index = 3, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %4 = ttl.cb_wait %0 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %5 = ttl.attach_cb %4, %0 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %6 = ttl.cb_reserve %1 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %7 = ttl.attach_cb %6, %1 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    ttl.store %5, %6 : tensor<1x1x!ttcore.tile<32x32, bf16>>, tensor<1x1x!ttcore.tile<32x32, bf16>>
    ttl.cb_push %1 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    ttl.cb_pop %0 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %8 = ttl.cb_wait %2 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %9 = ttl.attach_cb %8, %2 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %10 = ttl.cb_reserve %3 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %11 = ttl.attach_cb %10, %3 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    ttl.store %9, %10 : tensor<1x1x!ttcore.tile<32x32, bf16>>, tensor<1x1x!ttcore.tile<32x32, bf16>>
    ttl.cb_push %3 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    ttl.cb_pop %2 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    return
  }
  func.func @dm_read(%arg0: tensor<8x1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [8, 32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [8, 2], memory = interleaved>>, %arg1: tensor<8x1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [8, 32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [8, 2], memory = interleaved>>) attributes {ttl.base_cta_index = 4 : i32, ttl.crta_indices = [0 : i32, 1 : i32], ttl.kernel_thread = #ttkernel.thread<noc>, ttl.noc_index = 0 : i32} {
    %0 = ttl.bind_cb{cb_index = 0, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %1 = ttl.bind_cb{cb_index = 1, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %c2_i64 = arith.constant 2 : i64
    %2 = ttl.core_x : index
    %3 = ttl.core_y : index
    %4 = ttl.cb_reserve %0 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %5 = ttl.attach_cb %4, %0 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %c0 = arith.constant 0 : index
    %6 = ttl.tensor_slice %arg0[%3, %c0, %2] : tensor<8x1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [8, 32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [8, 2], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [8, 32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [8, 2], memory = interleaved>>
    %7 = ttl.copy %6, %0 : (tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [8, 32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [8, 2], memory = interleaved>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> !ttl.transfer_handle<read>
    ttl.wait %7 : !ttl.transfer_handle<read>
    ttl.cb_push %0 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %8 = ttl.cb_reserve %1 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %9 = ttl.attach_cb %8, %1 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %c0_0 = arith.constant 0 : index
    %10 = ttl.tensor_slice %arg1[%3, %c0_0, %2] : tensor<8x1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [8, 32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [8, 2], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [8, 32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [8, 2], memory = interleaved>>
    %11 = ttl.copy %10, %1 : (tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [8, 32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [8, 2], memory = interleaved>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> !ttl.transfer_handle<read>
    ttl.wait %11 : !ttl.transfer_handle<read>
    ttl.cb_push %1 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    return
  }
  func.func @dm_write(%arg0: tensor<8x256x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [8, 8192, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [8, 2], memory = interleaved>>, %arg1: tensor<8x256x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [8, 8192, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [8, 2], memory = interleaved>>) attributes {ttl.base_cta_index = 4 : i32, ttl.crta_indices = [2 : i32, 3 : i32], ttl.kernel_thread = #ttkernel.thread<noc>, ttl.noc_index = 1 : i32} {
    %0 = ttl.bind_cb{cb_index = 2, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %1 = ttl.bind_cb{cb_index = 3, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %c2_i64 = arith.constant 2 : i64
    %2 = ttl.core_x : index
    %3 = ttl.core_y : index
    %4 = ttl.cb_wait %0 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %5 = ttl.attach_cb %4, %0 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %c7_i64 = arith.constant 7 : i64
    %6 = arith.index_cast %c7_i64 : i64 to index
    %7 = ttl.tensor_slice %arg0[%3, %6, %2] : tensor<8x256x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [8, 8192, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [8, 2], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [8, 8192, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [8, 2], memory = interleaved>>
    %8 = ttl.copy %0, %7 : (!ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>, tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [8, 8192, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [8, 2], memory = interleaved>>) -> !ttl.transfer_handle<write>
    ttl.wait %8 : !ttl.transfer_handle<write>
    ttl.cb_pop %0 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %9 = ttl.cb_wait %1 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %10 = ttl.attach_cb %9, %1 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %c7_i64_0 = arith.constant 7 : i64
    %11 = arith.index_cast %c7_i64_0 : i64 to index
    %12 = ttl.tensor_slice %arg1[%3, %11, %2] : tensor<8x256x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [8, 8192, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [8, 2], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [8, 8192, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [8, 2], memory = interleaved>>
    %13 = ttl.copy %1, %12 : (!ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>, tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [8, 8192, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [8, 2], memory = interleaved>>) -> !ttl.transfer_handle<write>
    ttl.wait %13 : !ttl.transfer_handle<write>
    ttl.cb_pop %1 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    return
  }
}
