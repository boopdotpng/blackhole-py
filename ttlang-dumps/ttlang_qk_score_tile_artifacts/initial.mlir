module attributes {ttl.launch_grid = [1, 1], ttl.target_arch = "blackhole"} {
  func.func @compute() attributes {ttl.base_cta_index = 4 : i32, ttl.crta_indices = [], ttl.kernel_thread = #ttkernel.thread<compute>} {
    %0 = ttl.bind_cb{cb_index = 1, block_count = 2} : <[1, 2], !ttcore.tile<32x32, bf16>, 2>
    %1 = ttl.bind_cb{cb_index = 0, block_count = 2} : <[1, 2], !ttcore.tile<32x32, bf16>, 2>
    %2 = ttl.bind_cb{cb_index = 2, block_count = 1} : <[1, 1], !ttcore.tile<32x32, bf16>, 1>
    %3 = ttl.bind_cb{cb_index = 3, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %4 = ttl.cb_wait %1 : <[1, 2], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x2x!ttcore.tile<32x32, bf16>>
    %5 = ttl.attach_cb %4, %1 : (tensor<1x2x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 2], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x2x!ttcore.tile<32x32, bf16>>
    %6 = ttl.cb_wait %0 : <[1, 2], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x2x!ttcore.tile<32x32, bf16>>
    %7 = ttl.attach_cb %6, %0 : (tensor<1x2x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 2], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x2x!ttcore.tile<32x32, bf16>>
    %8 = ttl.cb_wait %2 : <[1, 1], !ttcore.tile<32x32, bf16>, 1> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %9 = ttl.attach_cb %8, %2 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 1>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %10 = ttl.mul %5, %7 : tensor<1x2x!ttcore.tile<32x32, bf16>>, tensor<1x2x!ttcore.tile<32x32, bf16>> -> tensor<1x2x!ttcore.tile<32x32, bf16>>
    %11 = ttl.fill 1.000000e+00 : tensor<1x1x!ttcore.tile<32x32, bf16>>
    %12 = ttl.reduce %10, %11 0 : i32 [1] : (tensor<1x2x!ttcore.tile<32x32, bf16>>, tensor<1x1x!ttcore.tile<32x32, bf16>>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %13 = ttl.cb_reserve %3 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %14 = ttl.attach_cb %13, %3 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %15 = ttl.mul %12, %9 : tensor<1x1x!ttcore.tile<32x32, bf16>>, tensor<1x1x!ttcore.tile<32x32, bf16>> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    ttl.store %15, %13 : tensor<1x1x!ttcore.tile<32x32, bf16>>, tensor<1x1x!ttcore.tile<32x32, bf16>>
    ttl.cb_push %3 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    ttl.cb_pop %2 : <[1, 1], !ttcore.tile<32x32, bf16>, 1>
    ttl.cb_pop %0 : <[1, 2], !ttcore.tile<32x32, bf16>, 2>
    ttl.cb_pop %1 : <[1, 2], !ttcore.tile<32x32, bf16>, 2>
    return
  }
  func.func @dm_read(%arg0: tensor<1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>, %arg1: tensor<1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>, %arg2: tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 32], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>) attributes {ttl.base_cta_index = 4 : i32, ttl.crta_indices = [1 : i32, 0 : i32, 2 : i32], ttl.kernel_thread = #ttkernel.thread<noc>, ttl.noc_index = 0 : i32} {
    %0 = ttl.bind_cb{cb_index = 1, block_count = 2} : <[1, 2], !ttcore.tile<32x32, bf16>, 2>
    %1 = ttl.bind_cb{cb_index = 0, block_count = 2} : <[1, 2], !ttcore.tile<32x32, bf16>, 2>
    %2 = ttl.bind_cb{cb_index = 2, block_count = 1} : <[1, 1], !ttcore.tile<32x32, bf16>, 1>
    %3 = ttl.cb_reserve %1 : <[1, 2], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x2x!ttcore.tile<32x32, bf16>>
    %4 = ttl.attach_cb %3, %1 : (tensor<1x2x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 2], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x2x!ttcore.tile<32x32, bf16>>
    %c0 = arith.constant 0 : index
    %c0_0 = arith.constant 0 : index
    %5 = ttl.tensor_slice %arg1[%c0, %c0_0] : tensor<1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>
    %6 = ttl.copy %5, %1 : (tensor<1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>, !ttl.cb<[1, 2], !ttcore.tile<32x32, bf16>, 2>) -> !ttl.transfer_handle<read>
    ttl.wait %6 : !ttl.transfer_handle<read>
    ttl.cb_push %1 : <[1, 2], !ttcore.tile<32x32, bf16>, 2>
    %7 = ttl.cb_reserve %0 : <[1, 2], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x2x!ttcore.tile<32x32, bf16>>
    %8 = ttl.attach_cb %7, %0 : (tensor<1x2x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 2], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x2x!ttcore.tile<32x32, bf16>>
    %c0_1 = arith.constant 0 : index
    %c0_2 = arith.constant 0 : index
    %9 = ttl.tensor_slice %arg0[%c0_1, %c0_2] : tensor<1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>
    %10 = ttl.copy %9, %0 : (tensor<1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>, !ttl.cb<[1, 2], !ttcore.tile<32x32, bf16>, 2>) -> !ttl.transfer_handle<read>
    ttl.wait %10 : !ttl.transfer_handle<read>
    ttl.cb_push %0 : <[1, 2], !ttcore.tile<32x32, bf16>, 2>
    %11 = ttl.cb_reserve %2 : <[1, 1], !ttcore.tile<32x32, bf16>, 1> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %12 = ttl.attach_cb %11, %2 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 1>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %c0_3 = arith.constant 0 : index
    %c0_4 = arith.constant 0 : index
    %13 = ttl.tensor_slice %arg2[%c0_3, %c0_4] : tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 32], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 32], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>
    %14 = ttl.copy %13, %2 : (tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 32], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 1>) -> !ttl.transfer_handle<read>
    ttl.wait %14 : !ttl.transfer_handle<read>
    ttl.cb_push %2 : <[1, 1], !ttcore.tile<32x32, bf16>, 1>
    return
  }
  func.func @dm_write(%arg0: tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 32], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>) attributes {ttl.base_cta_index = 4 : i32, ttl.crta_indices = [3 : i32], ttl.kernel_thread = #ttkernel.thread<noc>, ttl.noc_index = 1 : i32} {
    %0 = ttl.bind_cb{cb_index = 3, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %1 = ttl.cb_wait %0 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %2 = ttl.attach_cb %1, %0 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %c0 = arith.constant 0 : index
    %c0_0 = arith.constant 0 : index
    %3 = ttl.tensor_slice %arg0[%c0, %c0_0] : tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 32], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 32], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>
    %4 = ttl.copy %0, %3 : (!ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>, tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 32], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>) -> !ttl.transfer_handle<write>
    ttl.wait %4 : !ttl.transfer_handle<write>
    ttl.cb_pop %0 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    return
  }
}
