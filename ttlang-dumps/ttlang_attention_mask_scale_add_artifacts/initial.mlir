module attributes {ttl.launch_grid = [1, 1], ttl.target_arch = "blackhole"} {
  func.func @compute() attributes {ttl.base_cta_index = 3 : i32, ttl.crta_indices = [], ttl.kernel_thread = #ttkernel.thread<compute>} {
    %0 = ttl.bind_cb{cb_index = 1, block_count = 2} : <[1, 4], !ttcore.tile<32x32, f32>, 2>
    %1 = ttl.bind_cb{cb_index = 2, block_count = 2} : <[1, 4], !ttcore.tile<32x32, f32>, 2>
    %2 = ttl.bind_cb{cb_index = 0, block_count = 2} : <[1, 4], !ttcore.tile<32x32, f32>, 2>
    %3 = ttl.cb_wait %2 : <[1, 4], !ttcore.tile<32x32, f32>, 2> -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %4 = ttl.attach_cb %3, %2 : (tensor<1x4x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 4], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %5 = ttl.cb_wait %0 : <[1, 4], !ttcore.tile<32x32, f32>, 2> -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %6 = ttl.attach_cb %5, %0 : (tensor<1x4x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 4], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %7 = ttl.cb_reserve %1 : <[1, 4], !ttcore.tile<32x32, f32>, 2> -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %8 = ttl.attach_cb %7, %1 : (tensor<1x4x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 4], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %9 = ttl.mul_unary_const %4, 1.250000e-01 : tensor<1x4x!ttcore.tile<32x32, f32>> -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %10 = ttl.add %9, %6 : tensor<1x4x!ttcore.tile<32x32, f32>>, tensor<1x4x!ttcore.tile<32x32, f32>> -> tensor<1x4x!ttcore.tile<32x32, f32>>
    ttl.store %10, %7 : tensor<1x4x!ttcore.tile<32x32, f32>>, tensor<1x4x!ttcore.tile<32x32, f32>>
    ttl.cb_push %1 : <[1, 4], !ttcore.tile<32x32, f32>, 2>
    ttl.cb_pop %0 : <[1, 4], !ttcore.tile<32x32, f32>, 2>
    ttl.cb_pop %2 : <[1, 4], !ttcore.tile<32x32, f32>, 2>
    return
  }
  func.func @dm_read(%arg0: tensor<1x4x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 128], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>>, %arg1: tensor<1x4x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 128], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>>) attributes {ttl.base_cta_index = 3 : i32, ttl.crta_indices = [1 : i32, 0 : i32], ttl.kernel_thread = #ttkernel.thread<noc>, ttl.noc_index = 0 : i32} {
    %0 = ttl.bind_cb{cb_index = 1, block_count = 2} : <[1, 4], !ttcore.tile<32x32, f32>, 2>
    %1 = ttl.bind_cb{cb_index = 0, block_count = 2} : <[1, 4], !ttcore.tile<32x32, f32>, 2>
    %2 = ttl.cb_reserve %1 : <[1, 4], !ttcore.tile<32x32, f32>, 2> -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %3 = ttl.attach_cb %2, %1 : (tensor<1x4x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 4], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %4 = ttl.cb_reserve %0 : <[1, 4], !ttcore.tile<32x32, f32>, 2> -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %5 = ttl.attach_cb %4, %0 : (tensor<1x4x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 4], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %c0 = arith.constant 0 : index
    %c0_0 = arith.constant 0 : index
    %6 = ttl.tensor_slice %arg1[%c0, %c0_0] : tensor<1x4x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 128], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x4x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 128], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>>
    %7 = ttl.copy %6, %1 : (tensor<1x4x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 128], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>>, !ttl.cb<[1, 4], !ttcore.tile<32x32, f32>, 2>) -> !ttl.transfer_handle<read>
    ttl.wait %7 : !ttl.transfer_handle<read>
    %c0_1 = arith.constant 0 : index
    %c0_2 = arith.constant 0 : index
    %8 = ttl.tensor_slice %arg0[%c0_1, %c0_2] : tensor<1x4x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 128], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x4x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 128], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>>
    %9 = ttl.copy %8, %0 : (tensor<1x4x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 128], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>>, !ttl.cb<[1, 4], !ttcore.tile<32x32, f32>, 2>) -> !ttl.transfer_handle<read>
    ttl.wait %9 : !ttl.transfer_handle<read>
    ttl.cb_push %0 : <[1, 4], !ttcore.tile<32x32, f32>, 2>
    ttl.cb_push %1 : <[1, 4], !ttcore.tile<32x32, f32>, 2>
    return
  }
  func.func @dm_write(%arg0: tensor<1x4x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 128], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>>) attributes {ttl.base_cta_index = 3 : i32, ttl.crta_indices = [2 : i32], ttl.kernel_thread = #ttkernel.thread<noc>, ttl.noc_index = 1 : i32} {
    %0 = ttl.bind_cb{cb_index = 2, block_count = 2} : <[1, 4], !ttcore.tile<32x32, f32>, 2>
    %1 = ttl.cb_wait %0 : <[1, 4], !ttcore.tile<32x32, f32>, 2> -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %2 = ttl.attach_cb %1, %0 : (tensor<1x4x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 4], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %c0 = arith.constant 0 : index
    %c0_0 = arith.constant 0 : index
    %3 = ttl.tensor_slice %arg0[%c0, %c0_0] : tensor<1x4x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 128], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x4x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 128], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>>
    %4 = ttl.copy %0, %3 : (!ttl.cb<[1, 4], !ttcore.tile<32x32, f32>, 2>, tensor<1x4x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 128], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>>) -> !ttl.transfer_handle<write>
    ttl.wait %4 : !ttl.transfer_handle<write>
    ttl.cb_pop %0 : <[1, 4], !ttcore.tile<32x32, f32>, 2>
    return
  }
}
