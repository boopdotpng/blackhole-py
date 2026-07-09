module attributes {ttl.launch_grid = [1, 1], ttl.target_arch = "blackhole"} {
  func.func @compute() attributes {ttl.base_cta_index = 8 : i32, ttl.crta_indices = [], ttl.kernel_thread = #ttkernel.thread<compute>} {
    %0 = ttl.bind_cb{cb_index = 2, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %1 = ttl.bind_cb{cb_index = 3, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %2 = ttl.bind_cb{cb_index = 6, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %3 = ttl.bind_cb{cb_index = 7, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %4 = ttl.bind_cb{cb_index = 4, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %5 = ttl.bind_cb{cb_index = 5, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %6 = ttl.bind_cb{cb_index = 0, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %7 = ttl.bind_cb{cb_index = 1, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %8 = ttl.cb_wait %6 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %9 = ttl.attach_cb %8, %6 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %10 = ttl.cb_wait %7 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %11 = ttl.attach_cb %10, %7 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %12 = ttl.cb_wait %0 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %13 = ttl.attach_cb %12, %0 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %14 = ttl.cb_wait %4 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %15 = ttl.attach_cb %14, %4 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %16 = ttl.cb_reserve %2 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %17 = ttl.attach_cb %16, %2 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %18 = ttl.mul %9, %13 : tensor<1x1x!ttcore.tile<32x32, bf16>>, tensor<1x1x!ttcore.tile<32x32, bf16>> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %19 = ttl.neg %11 : tensor<1x1x!ttcore.tile<32x32, bf16>> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %20 = ttl.mul %19, %15 : tensor<1x1x!ttcore.tile<32x32, bf16>>, tensor<1x1x!ttcore.tile<32x32, bf16>> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %21 = ttl.add %18, %20 : tensor<1x1x!ttcore.tile<32x32, bf16>>, tensor<1x1x!ttcore.tile<32x32, bf16>> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    ttl.store %21, %16 : tensor<1x1x!ttcore.tile<32x32, bf16>>, tensor<1x1x!ttcore.tile<32x32, bf16>>
    ttl.cb_push %2 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    ttl.cb_pop %4 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    ttl.cb_pop %0 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    ttl.cb_pop %7 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    ttl.cb_pop %6 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %22 = ttl.cb_wait %6 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %23 = ttl.attach_cb %22, %6 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %24 = ttl.cb_wait %7 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %25 = ttl.attach_cb %24, %7 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %26 = ttl.cb_wait %1 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %27 = ttl.attach_cb %26, %1 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %28 = ttl.cb_wait %5 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %29 = ttl.attach_cb %28, %5 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %30 = ttl.cb_reserve %3 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %31 = ttl.attach_cb %30, %3 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %32 = ttl.mul %25, %27 : tensor<1x1x!ttcore.tile<32x32, bf16>>, tensor<1x1x!ttcore.tile<32x32, bf16>> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %33 = ttl.mul %23, %29 : tensor<1x1x!ttcore.tile<32x32, bf16>>, tensor<1x1x!ttcore.tile<32x32, bf16>> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %34 = ttl.add %32, %33 : tensor<1x1x!ttcore.tile<32x32, bf16>>, tensor<1x1x!ttcore.tile<32x32, bf16>> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    ttl.store %34, %30 : tensor<1x1x!ttcore.tile<32x32, bf16>>, tensor<1x1x!ttcore.tile<32x32, bf16>>
    ttl.cb_push %3 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    ttl.cb_pop %5 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    ttl.cb_pop %1 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    ttl.cb_pop %7 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    ttl.cb_pop %6 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    return
  }
  func.func @dm_read(%arg0: tensor<1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>, %arg1: tensor<1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>, %arg2: tensor<1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>) attributes {ttl.base_cta_index = 8 : i32, ttl.crta_indices = [1 : i32, 2 : i32, 0 : i32], ttl.kernel_thread = #ttkernel.thread<noc>, ttl.noc_index = 0 : i32} {
    %0 = ttl.bind_cb{cb_index = 2, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %1 = ttl.bind_cb{cb_index = 3, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %2 = ttl.bind_cb{cb_index = 4, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %3 = ttl.bind_cb{cb_index = 5, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %4 = ttl.bind_cb{cb_index = 0, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %5 = ttl.bind_cb{cb_index = 1, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %6 = ttl.cb_reserve %4 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %7 = ttl.attach_cb %6, %4 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %c0 = arith.constant 0 : index
    %c0_0 = arith.constant 0 : index
    %8 = ttl.tensor_slice %arg2[%c0, %c0_0] : tensor<1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>
    %9 = ttl.copy %8, %4 : (tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> !ttl.transfer_handle<read>
    ttl.wait %9 : !ttl.transfer_handle<read>
    ttl.cb_push %4 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %10 = ttl.cb_reserve %5 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %11 = ttl.attach_cb %10, %5 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %c0_1 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %12 = ttl.tensor_slice %arg2[%c0_1, %c1] : tensor<1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>
    %13 = ttl.copy %12, %5 : (tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> !ttl.transfer_handle<read>
    ttl.wait %13 : !ttl.transfer_handle<read>
    ttl.cb_push %5 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %14 = ttl.cb_reserve %0 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %15 = ttl.attach_cb %14, %0 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %c0_2 = arith.constant 0 : index
    %c0_3 = arith.constant 0 : index
    %16 = ttl.tensor_slice %arg0[%c0_2, %c0_3] : tensor<1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>
    %17 = ttl.copy %16, %0 : (tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> !ttl.transfer_handle<read>
    ttl.wait %17 : !ttl.transfer_handle<read>
    ttl.cb_push %0 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %18 = ttl.cb_reserve %1 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %19 = ttl.attach_cb %18, %1 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %c0_4 = arith.constant 0 : index
    %c1_5 = arith.constant 1 : index
    %20 = ttl.tensor_slice %arg0[%c0_4, %c1_5] : tensor<1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>
    %21 = ttl.copy %20, %1 : (tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> !ttl.transfer_handle<read>
    ttl.wait %21 : !ttl.transfer_handle<read>
    ttl.cb_push %1 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %22 = ttl.cb_reserve %2 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %23 = ttl.attach_cb %22, %2 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %c0_6 = arith.constant 0 : index
    %c0_7 = arith.constant 0 : index
    %24 = ttl.tensor_slice %arg1[%c0_6, %c0_7] : tensor<1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>
    %25 = ttl.copy %24, %2 : (tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> !ttl.transfer_handle<read>
    ttl.wait %25 : !ttl.transfer_handle<read>
    ttl.cb_push %2 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %26 = ttl.cb_reserve %3 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %27 = ttl.attach_cb %26, %3 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %c0_8 = arith.constant 0 : index
    %c1_9 = arith.constant 1 : index
    %28 = ttl.tensor_slice %arg1[%c0_8, %c1_9] : tensor<1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>
    %29 = ttl.copy %28, %3 : (tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> !ttl.transfer_handle<read>
    ttl.wait %29 : !ttl.transfer_handle<read>
    ttl.cb_push %3 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    return
  }
  func.func @dm_write(%arg0: tensor<1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>) attributes {ttl.base_cta_index = 8 : i32, ttl.crta_indices = [3 : i32], ttl.kernel_thread = #ttkernel.thread<noc>, ttl.noc_index = 1 : i32} {
    %0 = ttl.bind_cb{cb_index = 6, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %1 = ttl.bind_cb{cb_index = 7, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %2 = ttl.cb_wait %0 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %3 = ttl.attach_cb %2, %0 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %c0 = arith.constant 0 : index
    %c0_0 = arith.constant 0 : index
    %4 = ttl.tensor_slice %arg0[%c0, %c0_0] : tensor<1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>
    %5 = ttl.copy %0, %4 : (!ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>, tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>) -> !ttl.transfer_handle<write>
    ttl.wait %5 : !ttl.transfer_handle<write>
    ttl.cb_pop %0 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %6 = ttl.cb_wait %1 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %7 = ttl.attach_cb %6, %1 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %c0_1 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %8 = ttl.tensor_slice %arg0[%c0_1, %c1] : tensor<1x2x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>
    %9 = ttl.copy %1, %8 : (!ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>, tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 64], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>) -> !ttl.transfer_handle<write>
    ttl.wait %9 : !ttl.transfer_handle<write>
    ttl.cb_pop %1 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    return
  }
}
