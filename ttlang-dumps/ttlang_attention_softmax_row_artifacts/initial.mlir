module attributes {ttl.launch_grid = [1, 1], ttl.target_arch = "blackhole"} {
  func.func @compute() attributes {ttl.base_cta_index = 3 : i32, ttl.crta_indices = [], ttl.kernel_thread = #ttkernel.thread<compute>} {
    %0 = ttl.bind_cb{cb_index = 2, block_count = 2} : <[1, 4], !ttcore.tile<32x32, f32>, 2>
    %1 = ttl.bind_cb{cb_index = 0, block_count = 2} : <[1, 4], !ttcore.tile<32x32, f32>, 2>
    %2 = ttl.bind_cb{cb_index = 1, block_count = 2} : <[1, 4], !ttcore.tile<32x32, f32>, 2>
    %3 = ttl.cb_wait %1 : <[1, 4], !ttcore.tile<32x32, f32>, 2> -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %4 = ttl.attach_cb %3, %1 : (tensor<1x4x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 4], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %5 = ttl.cb_wait %2 : <[1, 4], !ttcore.tile<32x32, f32>, 2> -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %6 = ttl.attach_cb %5, %2 : (tensor<1x4x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 4], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %7 = ttl.fill 1.000000e+00 : tensor<1x1x!ttcore.tile<32x32, f32>>
    %8 = ttl.reduce %4, %7 1 : i32 [1] : (tensor<1x4x!ttcore.tile<32x32, f32>>, tensor<1x1x!ttcore.tile<32x32, f32>>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
    %c1_i64 = arith.constant 1 : i64
    %c4_i64 = arith.constant 4 : i64
    %9 = ttl.block.broadcast %8 dims = [1], shape = [1, 4] : tensor<1x1x!ttcore.tile<32x32, f32>> -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %10 = ttl.sub %6, %9 : tensor<1x4x!ttcore.tile<32x32, f32>>, tensor<1x4x!ttcore.tile<32x32, f32>> -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %11 = ttl.exp %10 : tensor<1x4x!ttcore.tile<32x32, f32>> -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %12 = ttl.fill 1.000000e+00 : tensor<1x1x!ttcore.tile<32x32, f32>>
    %13 = ttl.reduce %11, %12 0 : i32 [1] : (tensor<1x4x!ttcore.tile<32x32, f32>>, tensor<1x1x!ttcore.tile<32x32, f32>>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
    %c1_i64_0 = arith.constant 1 : i64
    %c4_i64_1 = arith.constant 4 : i64
    %14 = ttl.block.broadcast %13 dims = [1], shape = [1, 4] : tensor<1x1x!ttcore.tile<32x32, f32>> -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %15 = ttl.recip %14 : tensor<1x4x!ttcore.tile<32x32, f32>> -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %16 = ttl.cb_reserve %0 : <[1, 4], !ttcore.tile<32x32, f32>, 2> -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %17 = ttl.attach_cb %16, %0 : (tensor<1x4x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 4], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %18 = ttl.mul %11, %15 : tensor<1x4x!ttcore.tile<32x32, f32>>, tensor<1x4x!ttcore.tile<32x32, f32>> -> tensor<1x4x!ttcore.tile<32x32, f32>>
    ttl.store %18, %16 : tensor<1x4x!ttcore.tile<32x32, f32>>, tensor<1x4x!ttcore.tile<32x32, f32>>
    ttl.cb_push %0 : <[1, 4], !ttcore.tile<32x32, f32>, 2>
    ttl.cb_pop %2 : <[1, 4], !ttcore.tile<32x32, f32>, 2>
    ttl.cb_pop %1 : <[1, 4], !ttcore.tile<32x32, f32>, 2>
    return
  }
  func.func @dm_read(%arg0: tensor<1x4x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 128], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>>) attributes {ttl.base_cta_index = 3 : i32, ttl.crta_indices = [0 : i32], ttl.kernel_thread = #ttkernel.thread<noc>, ttl.noc_index = 0 : i32} {
    %0 = ttl.bind_cb{cb_index = 0, block_count = 2} : <[1, 4], !ttcore.tile<32x32, f32>, 2>
    %1 = ttl.bind_cb{cb_index = 1, block_count = 2} : <[1, 4], !ttcore.tile<32x32, f32>, 2>
    %2 = ttl.cb_reserve %0 : <[1, 4], !ttcore.tile<32x32, f32>, 2> -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %3 = ttl.attach_cb %2, %0 : (tensor<1x4x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 4], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %4 = ttl.cb_reserve %1 : <[1, 4], !ttcore.tile<32x32, f32>, 2> -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %5 = ttl.attach_cb %4, %1 : (tensor<1x4x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 4], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x4x!ttcore.tile<32x32, f32>>
    %c0 = arith.constant 0 : index
    %c0_0 = arith.constant 0 : index
    %6 = ttl.tensor_slice %arg0[%c0, %c0_0] : tensor<1x4x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 128], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x4x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 128], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>>
    %7 = ttl.copy %6, %0 : (tensor<1x4x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 128], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>>, !ttl.cb<[1, 4], !ttcore.tile<32x32, f32>, 2>) -> !ttl.transfer_handle<read>
    ttl.wait %7 : !ttl.transfer_handle<read>
    %c0_1 = arith.constant 0 : index
    %c0_2 = arith.constant 0 : index
    %8 = ttl.tensor_slice %arg0[%c0_1, %c0_2] : tensor<1x4x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 128], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x4x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 128], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>>
    %9 = ttl.copy %8, %1 : (tensor<1x4x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 128], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>>, !ttl.cb<[1, 4], !ttcore.tile<32x32, f32>, 2>) -> !ttl.transfer_handle<read>
    ttl.wait %9 : !ttl.transfer_handle<read>
    ttl.cb_push %1 : <[1, 4], !ttcore.tile<32x32, f32>, 2>
    ttl.cb_push %0 : <[1, 4], !ttcore.tile<32x32, f32>, 2>
    return
  }
  func.func @dm_write(%arg0: tensor<1x4x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 128], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>>) attributes {ttl.base_cta_index = 3 : i32, ttl.crta_indices = [1 : i32], ttl.kernel_thread = #ttkernel.thread<noc>, ttl.noc_index = 1 : i32} {
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
