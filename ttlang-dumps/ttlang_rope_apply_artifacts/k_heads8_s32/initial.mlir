module attributes {ttl.launch_grid = [1, 1], ttl.target_arch = "blackhole"} {
  func.func @compute() attributes {ttl.base_cta_index = 8 : i32, ttl.crta_indices = [], ttl.kernel_thread = #ttkernel.thread<compute>} {
    %0 = ttl.bind_cb{cb_index = 3, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %1 = ttl.bind_cb{cb_index = 2, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %2 = ttl.bind_cb{cb_index = 7, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %3 = ttl.bind_cb{cb_index = 6, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %4 = ttl.bind_cb{cb_index = 5, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %5 = ttl.bind_cb{cb_index = 4, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %6 = ttl.bind_cb{cb_index = 1, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %7 = ttl.bind_cb{cb_index = 0, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %c8 = arith.constant 8 : index
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    scf.for %arg0 = %c0 to %c8 step %c1 {
      %8 = ttl.cb_wait %7 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %9 = ttl.attach_cb %8, %7 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %10 = ttl.cb_wait %6 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %11 = ttl.attach_cb %10, %6 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %12 = ttl.cb_wait %1 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %13 = ttl.attach_cb %12, %1 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %14 = ttl.cb_wait %0 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %15 = ttl.attach_cb %14, %0 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %16 = ttl.cb_wait %5 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %17 = ttl.attach_cb %16, %5 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %18 = ttl.cb_wait %4 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %19 = ttl.attach_cb %18, %4 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %20 = ttl.cb_reserve %3 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %21 = ttl.attach_cb %20, %3 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %22 = ttl.cb_reserve %2 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %23 = ttl.attach_cb %22, %2 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %24 = ttl.mul %9, %13 : tensor<1x1x!ttcore.tile<32x32, bf16>>, tensor<1x1x!ttcore.tile<32x32, bf16>> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %25 = ttl.mul %11, %17 : tensor<1x1x!ttcore.tile<32x32, bf16>>, tensor<1x1x!ttcore.tile<32x32, bf16>> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %26 = ttl.sub %24, %25 : tensor<1x1x!ttcore.tile<32x32, bf16>>, tensor<1x1x!ttcore.tile<32x32, bf16>> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      ttl.store %26, %20 : tensor<1x1x!ttcore.tile<32x32, bf16>>, tensor<1x1x!ttcore.tile<32x32, bf16>>
      %27 = ttl.mul %11, %15 : tensor<1x1x!ttcore.tile<32x32, bf16>>, tensor<1x1x!ttcore.tile<32x32, bf16>> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %28 = ttl.mul %9, %19 : tensor<1x1x!ttcore.tile<32x32, bf16>>, tensor<1x1x!ttcore.tile<32x32, bf16>> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %29 = ttl.add %27, %28 : tensor<1x1x!ttcore.tile<32x32, bf16>>, tensor<1x1x!ttcore.tile<32x32, bf16>> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      ttl.store %29, %22 : tensor<1x1x!ttcore.tile<32x32, bf16>>, tensor<1x1x!ttcore.tile<32x32, bf16>>
      ttl.cb_push %2 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
      ttl.cb_push %3 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
      ttl.cb_pop %4 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
      ttl.cb_pop %5 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
      ttl.cb_pop %0 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
      ttl.cb_pop %1 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
      ttl.cb_pop %6 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
      ttl.cb_pop %7 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    }
    return
  }
  func.func @dm_read(%arg0: tensor<1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>, %arg1: tensor<1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>, %arg2: tensor<8x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [256, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>) attributes {ttl.base_cta_index = 8 : i32, ttl.crta_indices = [1 : i32, 2 : i32, 0 : i32], ttl.kernel_thread = #ttkernel.thread<noc>, ttl.noc_index = 0 : i32} {
    %0 = ttl.bind_cb{cb_index = 3, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %1 = ttl.bind_cb{cb_index = 2, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %c1 = arith.constant 1 : index
    %2 = ttl.bind_cb{cb_index = 5, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %3 = ttl.bind_cb{cb_index = 4, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %4 = ttl.bind_cb{cb_index = 1, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %5 = ttl.bind_cb{cb_index = 0, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %c8 = arith.constant 8 : index
    %c0 = arith.constant 0 : index
    %c1_0 = arith.constant 1 : index
    scf.for %arg3 = %c0 to %c8 step %c1_0 {
      %6 = arith.remsi %arg3, %c1 : index
      %7 = ttl.cb_reserve %5 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %8 = ttl.attach_cb %7, %5 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %c0_1 = arith.constant 0 : index
      %9 = ttl.tensor_slice %arg2[%arg3, %c0_1] : tensor<8x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [256, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [256, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>
      %10 = ttl.copy %9, %5 : (tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [256, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> !ttl.transfer_handle<read>
      ttl.wait %10 : !ttl.transfer_handle<read>
      ttl.cb_push %5 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
      %11 = ttl.cb_reserve %4 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %12 = ttl.attach_cb %11, %4 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %c1_2 = arith.constant 1 : index
      %13 = ttl.tensor_slice %arg2[%arg3, %c1_2] : tensor<8x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [256, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [256, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>
      %14 = ttl.copy %13, %4 : (tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [256, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> !ttl.transfer_handle<read>
      ttl.wait %14 : !ttl.transfer_handle<read>
      ttl.cb_push %4 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
      %15 = ttl.cb_reserve %1 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %16 = ttl.attach_cb %15, %1 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %c0_3 = arith.constant 0 : index
      %17 = ttl.tensor_slice %arg0[%6, %c0_3] : tensor<1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>
      %18 = ttl.copy %17, %1 : (tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> !ttl.transfer_handle<read>
      ttl.wait %18 : !ttl.transfer_handle<read>
      ttl.cb_push %1 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
      %19 = ttl.cb_reserve %0 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %20 = ttl.attach_cb %19, %0 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %c1_4 = arith.constant 1 : index
      %21 = ttl.tensor_slice %arg0[%6, %c1_4] : tensor<1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>
      %22 = ttl.copy %21, %0 : (tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> !ttl.transfer_handle<read>
      ttl.wait %22 : !ttl.transfer_handle<read>
      ttl.cb_push %0 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
      %23 = ttl.cb_reserve %3 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %24 = ttl.attach_cb %23, %3 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %c0_5 = arith.constant 0 : index
      %25 = ttl.tensor_slice %arg1[%6, %c0_5] : tensor<1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>
      %26 = ttl.copy %25, %3 : (tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> !ttl.transfer_handle<read>
      ttl.wait %26 : !ttl.transfer_handle<read>
      ttl.cb_push %3 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
      %27 = ttl.cb_reserve %2 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %28 = ttl.attach_cb %27, %2 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %c1_6 = arith.constant 1 : index
      %29 = ttl.tensor_slice %arg1[%6, %c1_6] : tensor<1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>
      %30 = ttl.copy %29, %2 : (tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> !ttl.transfer_handle<read>
      ttl.wait %30 : !ttl.transfer_handle<read>
      ttl.cb_push %2 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    }
    return
  }
  func.func @dm_write(%arg0: tensor<8x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [256, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>) attributes {ttl.base_cta_index = 8 : i32, ttl.crta_indices = [3 : i32], ttl.kernel_thread = #ttkernel.thread<noc>, ttl.noc_index = 1 : i32} {
    %0 = ttl.bind_cb{cb_index = 7, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %1 = ttl.bind_cb{cb_index = 6, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %c8 = arith.constant 8 : index
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    scf.for %arg1 = %c0 to %c8 step %c1 {
      %2 = ttl.cb_wait %1 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %3 = ttl.attach_cb %2, %1 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %c0_0 = arith.constant 0 : index
      %4 = ttl.tensor_slice %arg0[%arg1, %c0_0] : tensor<8x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [256, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [256, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>
      %5 = ttl.copy %1, %4 : (!ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>, tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [256, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>) -> !ttl.transfer_handle<write>
      ttl.wait %5 : !ttl.transfer_handle<write>
      ttl.cb_pop %1 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
      %6 = ttl.cb_wait %0 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %7 = ttl.attach_cb %6, %0 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %c1_1 = arith.constant 1 : index
      %8 = ttl.tensor_slice %arg0[%arg1, %c1_1] : tensor<8x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [256, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [256, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>
      %9 = ttl.copy %0, %8 : (!ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>, tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [256, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>) -> !ttl.transfer_handle<write>
      ttl.wait %9 : !ttl.transfer_handle<write>
      ttl.cb_pop %0 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    }
    return
  }
}
