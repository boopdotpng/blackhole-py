module attributes {ttl.launch_grid = [1, 1], ttl.target_arch = "blackhole"} {
  func.func @compute() attributes {ttl.base_cta_index = 10 : i32, ttl.crta_indices = [], ttl.kernel_thread = #ttkernel.thread<compute>} {
    %0 = ttl.bind_cb{cb_index = 6, block_count = 2} : <[1, 1], !ttcore.tile<32x32, f32>, 2>
    %1 = ttl.bind_cb{cb_index = 8, block_count = 2} : <[1, 1], !ttcore.tile<32x32, f32>, 2>
    %2 = ttl.bind_cb{cb_index = 9, block_count = 2} : <[1, 1], !ttcore.tile<32x32, f32>, 2>
    %3 = ttl.bind_cb{cb_index = 5, block_count = 2} : <[1, 1], !ttcore.tile<32x32, f32>, 2>
    %4 = ttl.bind_cb{cb_index = 7, block_count = 2} : <[1, 1], !ttcore.tile<32x32, f32>, 2>
    %5 = ttl.bind_cb{cb_index = 2, block_count = 1} : <[1, 1], !ttcore.tile<32x32, f32>, 1>
    %6 = ttl.bind_cb{cb_index = 1, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %7 = ttl.bind_cb{cb_index = 4, block_count = 2} : <[1, 1], !ttcore.tile<32x32, f32>, 2>
    %8 = ttl.bind_cb{cb_index = 0, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %9 = ttl.bind_cb{cb_index = 3, block_count = 2} : <[1, 1], !ttcore.tile<32x32, f32>, 2>
    %10 = ttl.cb_wait %5 : <[1, 1], !ttcore.tile<32x32, f32>, 1> -> tensor<1x1x!ttcore.tile<32x32, f32>>
    %11 = ttl.attach_cb %10, %5 : (tensor<1x1x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, f32>, 1>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
    %12 = ttl.cb_wait %8 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %13 = ttl.attach_cb %12, %8 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
    %14 = ttl.cb_reserve %3 : <[1, 1], !ttcore.tile<32x32, f32>, 2> -> tensor<1x1x!ttcore.tile<32x32, f32>>
    %15 = ttl.attach_cb %14, %3 : (tensor<1x1x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
    %16 = ttl.typecast %13 : (tensor<1x1x!ttcore.tile<32x32, bf16>>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
    %17 = ttl.mul %16, %16 : tensor<1x1x!ttcore.tile<32x32, f32>>, tensor<1x1x!ttcore.tile<32x32, f32>> -> tensor<1x1x!ttcore.tile<32x32, f32>>
    %18 = ttl.fill 1.000000e+00 : tensor<1x1x!ttcore.tile<32x32, f32>>
    %19 = ttl.reduce %17, %18 0 : i32 [1] : (tensor<1x1x!ttcore.tile<32x32, f32>>, tensor<1x1x!ttcore.tile<32x32, f32>>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
    ttl.store %19, %14 : tensor<1x1x!ttcore.tile<32x32, f32>>, tensor<1x1x!ttcore.tile<32x32, f32>>
    ttl.cb_push %3 : <[1, 1], !ttcore.tile<32x32, f32>, 2>
    ttl.cb_pop %8 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %20 = ttl.cb_wait %3 : <[1, 1], !ttcore.tile<32x32, f32>, 2> -> tensor<1x1x!ttcore.tile<32x32, f32>>
    %21 = ttl.attach_cb %20, %3 : (tensor<1x1x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
    %22 = ttl.cb_reserve %0 : <[1, 1], !ttcore.tile<32x32, f32>, 2> -> tensor<1x1x!ttcore.tile<32x32, f32>>
    %23 = ttl.attach_cb %22, %0 : (tensor<1x1x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
    ttl.store %21, %22 : tensor<1x1x!ttcore.tile<32x32, f32>>, tensor<1x1x!ttcore.tile<32x32, f32>>
    ttl.cb_push %0 : <[1, 1], !ttcore.tile<32x32, f32>, 2>
    ttl.cb_pop %3 : <[1, 1], !ttcore.tile<32x32, f32>, 2>
    %c0 = arith.constant 0 : index
    %c64_i64 = arith.constant 64 : i64
    %c1_i64 = arith.constant 1 : i64
    %24 = arith.subi %c64_i64, %c1_i64 : i64
    %c1 = arith.constant 1 : index
    %25 = arith.index_cast %24 : i64 to index
    scf.for %arg0 = %c0 to %25 step %c1 {
      %42 = ttl.cb_wait %8 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %43 = ttl.attach_cb %42, %8 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %44 = ttl.cb_reserve %3 : <[1, 1], !ttcore.tile<32x32, f32>, 2> -> tensor<1x1x!ttcore.tile<32x32, f32>>
      %45 = ttl.attach_cb %44, %3 : (tensor<1x1x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
      %46 = ttl.typecast %43 : (tensor<1x1x!ttcore.tile<32x32, bf16>>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
      %47 = ttl.mul %46, %46 : tensor<1x1x!ttcore.tile<32x32, f32>>, tensor<1x1x!ttcore.tile<32x32, f32>> -> tensor<1x1x!ttcore.tile<32x32, f32>>
      %48 = ttl.fill 1.000000e+00 : tensor<1x1x!ttcore.tile<32x32, f32>>
      %49 = ttl.reduce %47, %48 0 : i32 [1] : (tensor<1x1x!ttcore.tile<32x32, f32>>, tensor<1x1x!ttcore.tile<32x32, f32>>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
      ttl.store %49, %44 : tensor<1x1x!ttcore.tile<32x32, f32>>, tensor<1x1x!ttcore.tile<32x32, f32>>
      ttl.cb_push %3 : <[1, 1], !ttcore.tile<32x32, f32>, 2>
      ttl.cb_pop %8 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
      %50 = ttl.cb_wait %3 : <[1, 1], !ttcore.tile<32x32, f32>, 2> -> tensor<1x1x!ttcore.tile<32x32, f32>>
      %51 = ttl.attach_cb %50, %3 : (tensor<1x1x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
      %52 = ttl.cb_wait %0 : <[1, 1], !ttcore.tile<32x32, f32>, 2> -> tensor<1x1x!ttcore.tile<32x32, f32>>
      %53 = ttl.attach_cb %52, %0 : (tensor<1x1x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
      %54 = ttl.cb_reserve %0 : <[1, 1], !ttcore.tile<32x32, f32>, 2> -> tensor<1x1x!ttcore.tile<32x32, f32>>
      %55 = ttl.attach_cb %54, %0 : (tensor<1x1x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
      %56 = ttl.add %53, %51 : tensor<1x1x!ttcore.tile<32x32, f32>>, tensor<1x1x!ttcore.tile<32x32, f32>> -> tensor<1x1x!ttcore.tile<32x32, f32>>
      ttl.store %56, %54 : tensor<1x1x!ttcore.tile<32x32, f32>>, tensor<1x1x!ttcore.tile<32x32, f32>>
      ttl.cb_push %0 : <[1, 1], !ttcore.tile<32x32, f32>, 2>
      ttl.cb_pop %0 : <[1, 1], !ttcore.tile<32x32, f32>, 2>
      ttl.cb_pop %3 : <[1, 1], !ttcore.tile<32x32, f32>, 2>
    }
    %26 = ttl.cb_wait %0 : <[1, 1], !ttcore.tile<32x32, f32>, 2> -> tensor<1x1x!ttcore.tile<32x32, f32>>
    %27 = ttl.attach_cb %26, %0 : (tensor<1x1x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
    %28 = ttl.cb_reserve %4 : <[1, 1], !ttcore.tile<32x32, f32>, 2> -> tensor<1x1x!ttcore.tile<32x32, f32>>
    %29 = ttl.attach_cb %28, %4 : (tensor<1x1x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
    %30 = ttl.block.broadcast %27 dims = [1], shape = [1, 1] : tensor<1x1x!ttcore.tile<32x32, f32>> -> tensor<1x1x!ttcore.tile<32x32, f32>>
    %31 = ttl.mul %30, %11 : tensor<1x1x!ttcore.tile<32x32, f32>>, tensor<1x1x!ttcore.tile<32x32, f32>> -> tensor<1x1x!ttcore.tile<32x32, f32>>
    %cst = arith.constant 9.99999974E-6 : f32
    %32 = ttl.fill 9.99999974E-6 : tensor<1x1x!ttcore.tile<32x32, f32>>
    %33 = ttl.add %31, %32 : tensor<1x1x!ttcore.tile<32x32, f32>>, tensor<1x1x!ttcore.tile<32x32, f32>> -> tensor<1x1x!ttcore.tile<32x32, f32>>
    ttl.store %33, %28 : tensor<1x1x!ttcore.tile<32x32, f32>>, tensor<1x1x!ttcore.tile<32x32, f32>>
    ttl.cb_push %4 : <[1, 1], !ttcore.tile<32x32, f32>, 2>
    ttl.cb_pop %0 : <[1, 1], !ttcore.tile<32x32, f32>, 2>
    %34 = ttl.cb_wait %4 : <[1, 1], !ttcore.tile<32x32, f32>, 2> -> tensor<1x1x!ttcore.tile<32x32, f32>>
    %35 = ttl.attach_cb %34, %4 : (tensor<1x1x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
    %36 = ttl.cb_reserve %1 : <[1, 1], !ttcore.tile<32x32, f32>, 2> -> tensor<1x1x!ttcore.tile<32x32, f32>>
    %37 = ttl.attach_cb %36, %1 : (tensor<1x1x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
    %38 = ttl.rsqrt %35 : tensor<1x1x!ttcore.tile<32x32, f32>> -> tensor<1x1x!ttcore.tile<32x32, f32>>
    ttl.store %38, %36 : tensor<1x1x!ttcore.tile<32x32, f32>>, tensor<1x1x!ttcore.tile<32x32, f32>>
    ttl.cb_push %1 : <[1, 1], !ttcore.tile<32x32, f32>, 2>
    ttl.cb_pop %4 : <[1, 1], !ttcore.tile<32x32, f32>, 2>
    %39 = ttl.cb_wait %1 : <[1, 1], !ttcore.tile<32x32, f32>, 2> -> tensor<1x1x!ttcore.tile<32x32, f32>>
    %40 = ttl.attach_cb %39, %1 : (tensor<1x1x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
    %c0_0 = arith.constant 0 : index
    %c64_i64_1 = arith.constant 64 : i64
    %c1_2 = arith.constant 1 : index
    %41 = arith.index_cast %c64_i64_1 : i64 to index
    scf.for %arg0 = %c0_0 to %41 step %c1_2 {
      %42 = ttl.cb_wait %8 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %43 = ttl.attach_cb %42, %8 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %44 = ttl.cb_wait %6 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %45 = ttl.attach_cb %44, %6 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %46 = ttl.cb_reserve %9 : <[1, 1], !ttcore.tile<32x32, f32>, 2> -> tensor<1x1x!ttcore.tile<32x32, f32>>
      %47 = ttl.attach_cb %46, %9 : (tensor<1x1x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
      %48 = ttl.cb_reserve %7 : <[1, 1], !ttcore.tile<32x32, f32>, 2> -> tensor<1x1x!ttcore.tile<32x32, f32>>
      %49 = ttl.attach_cb %48, %7 : (tensor<1x1x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
      %50 = ttl.typecast %43 : (tensor<1x1x!ttcore.tile<32x32, bf16>>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
      ttl.store %50, %46 : tensor<1x1x!ttcore.tile<32x32, f32>>, tensor<1x1x!ttcore.tile<32x32, f32>>
      %51 = ttl.typecast %45 : (tensor<1x1x!ttcore.tile<32x32, bf16>>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
      ttl.store %51, %48 : tensor<1x1x!ttcore.tile<32x32, f32>>, tensor<1x1x!ttcore.tile<32x32, f32>>
      ttl.cb_push %7 : <[1, 1], !ttcore.tile<32x32, f32>, 2>
      ttl.cb_push %9 : <[1, 1], !ttcore.tile<32x32, f32>, 2>
      ttl.cb_pop %6 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
      ttl.cb_pop %8 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
      %52 = ttl.cb_wait %9 : <[1, 1], !ttcore.tile<32x32, f32>, 2> -> tensor<1x1x!ttcore.tile<32x32, f32>>
      %53 = ttl.attach_cb %52, %9 : (tensor<1x1x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
      %54 = ttl.cb_wait %7 : <[1, 1], !ttcore.tile<32x32, f32>, 2> -> tensor<1x1x!ttcore.tile<32x32, f32>>
      %55 = ttl.attach_cb %54, %7 : (tensor<1x1x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
      %56 = ttl.cb_reserve %2 : <[1, 1], !ttcore.tile<32x32, f32>, 2> -> tensor<1x1x!ttcore.tile<32x32, f32>>
      %57 = ttl.attach_cb %56, %2 : (tensor<1x1x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
      %58 = ttl.mul %53, %40 : tensor<1x1x!ttcore.tile<32x32, f32>>, tensor<1x1x!ttcore.tile<32x32, f32>> -> tensor<1x1x!ttcore.tile<32x32, f32>>
      %59 = ttl.mul %58, %55 : tensor<1x1x!ttcore.tile<32x32, f32>>, tensor<1x1x!ttcore.tile<32x32, f32>> -> tensor<1x1x!ttcore.tile<32x32, f32>>
      ttl.store %59, %56 : tensor<1x1x!ttcore.tile<32x32, f32>>, tensor<1x1x!ttcore.tile<32x32, f32>>
      ttl.cb_push %2 : <[1, 1], !ttcore.tile<32x32, f32>, 2>
      ttl.cb_pop %7 : <[1, 1], !ttcore.tile<32x32, f32>, 2>
      ttl.cb_pop %9 : <[1, 1], !ttcore.tile<32x32, f32>, 2>
    }
    ttl.cb_pop %1 : <[1, 1], !ttcore.tile<32x32, f32>, 2>
    ttl.cb_pop %5 : <[1, 1], !ttcore.tile<32x32, f32>, 1>
    return
  }
  func.func @dm_read(%arg0: tensor<1x1x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 32], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>>, %arg1: tensor<1x64x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 2048], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>, %arg2: tensor<1x64x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 2048], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>) attributes {ttl.base_cta_index = 10 : i32, ttl.crta_indices = [2 : i32, 1 : i32, 0 : i32], ttl.kernel_thread = #ttkernel.thread<noc>, ttl.noc_index = 0 : i32} {
    %0 = ttl.bind_cb{cb_index = 2, block_count = 1} : <[1, 1], !ttcore.tile<32x32, f32>, 1>
    %1 = ttl.bind_cb{cb_index = 1, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %2 = ttl.bind_cb{cb_index = 0, block_count = 2} : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    %3 = ttl.cb_reserve %0 : <[1, 1], !ttcore.tile<32x32, f32>, 1> -> tensor<1x1x!ttcore.tile<32x32, f32>>
    %4 = ttl.attach_cb %3, %0 : (tensor<1x1x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, f32>, 1>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
    %c0 = arith.constant 0 : index
    %c0_0 = arith.constant 0 : index
    %5 = ttl.tensor_slice %arg0[%c0, %c0_0] : tensor<1x1x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 32], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 32], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>>
    %6 = ttl.copy %5, %0 : (tensor<1x1x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 32], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, f32>, 1>) -> !ttl.transfer_handle<read>
    ttl.wait %6 : !ttl.transfer_handle<read>
    ttl.cb_push %0 : <[1, 1], !ttcore.tile<32x32, f32>, 1>
    %c0_1 = arith.constant 0 : index
    %c64_i64 = arith.constant 64 : i64
    %c1 = arith.constant 1 : index
    %7 = arith.index_cast %c64_i64 : i64 to index
    scf.for %arg3 = %c0_1 to %7 step %c1 {
      %9 = ttl.cb_reserve %2 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %10 = ttl.attach_cb %9, %2 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %c0_5 = arith.constant 0 : index
      %11 = ttl.tensor_slice %arg2[%c0_5, %arg3] : tensor<1x64x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 2048], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 2048], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>
      %12 = ttl.copy %11, %2 : (tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 2048], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> !ttl.transfer_handle<read>
      ttl.wait %12 : !ttl.transfer_handle<read>
      ttl.cb_push %2 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    }
    %c0_2 = arith.constant 0 : index
    %c64_i64_3 = arith.constant 64 : i64
    %c1_4 = arith.constant 1 : index
    %8 = arith.index_cast %c64_i64_3 : i64 to index
    scf.for %arg3 = %c0_2 to %8 step %c1_4 {
      %9 = ttl.cb_reserve %2 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %10 = ttl.attach_cb %9, %2 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %c0_5 = arith.constant 0 : index
      %11 = ttl.tensor_slice %arg2[%c0_5, %arg3] : tensor<1x64x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 2048], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 2048], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>
      %12 = ttl.copy %11, %2 : (tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 2048], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> !ttl.transfer_handle<read>
      ttl.wait %12 : !ttl.transfer_handle<read>
      ttl.cb_push %2 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
      %13 = ttl.cb_reserve %1 : <[1, 1], !ttcore.tile<32x32, bf16>, 2> -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %14 = ttl.attach_cb %13, %1 : (tensor<1x1x!ttcore.tile<32x32, bf16>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> tensor<1x1x!ttcore.tile<32x32, bf16>>
      %c0_6 = arith.constant 0 : index
      %15 = ttl.tensor_slice %arg1[%c0_6, %arg3] : tensor<1x64x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 2048], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 2048], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>
      %16 = ttl.copy %15, %1 : (tensor<1x1x!ttcore.tile<32x32, bf16>, #ttl.layout<shape = [32, 2048], element_type = !ttcore.tile<32x32, bf16>, buffer = l1, grid = [1, 1], memory = interleaved>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, bf16>, 2>) -> !ttl.transfer_handle<read>
      ttl.wait %16 : !ttl.transfer_handle<read>
      ttl.cb_push %1 : <[1, 1], !ttcore.tile<32x32, bf16>, 2>
    }
    return
  }
  func.func @dm_write(%arg0: tensor<1x64x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 2048], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>>) attributes {ttl.base_cta_index = 10 : i32, ttl.crta_indices = [3 : i32], ttl.kernel_thread = #ttkernel.thread<noc>, ttl.noc_index = 1 : i32} {
    %0 = ttl.bind_cb{cb_index = 9, block_count = 2} : <[1, 1], !ttcore.tile<32x32, f32>, 2>
    %c0 = arith.constant 0 : index
    %c64_i64 = arith.constant 64 : i64
    %c1 = arith.constant 1 : index
    %1 = arith.index_cast %c64_i64 : i64 to index
    scf.for %arg1 = %c0 to %1 step %c1 {
      %2 = ttl.cb_wait %0 : <[1, 1], !ttcore.tile<32x32, f32>, 2> -> tensor<1x1x!ttcore.tile<32x32, f32>>
      %3 = ttl.attach_cb %2, %0 : (tensor<1x1x!ttcore.tile<32x32, f32>>, !ttl.cb<[1, 1], !ttcore.tile<32x32, f32>, 2>) -> tensor<1x1x!ttcore.tile<32x32, f32>>
      %c0_0 = arith.constant 0 : index
      %4 = ttl.tensor_slice %arg0[%c0_0, %arg1] : tensor<1x64x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 2048], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>> -> tensor<1x1x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 2048], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>>
      %5 = ttl.copy %0, %4 : (!ttl.cb<[1, 1], !ttcore.tile<32x32, f32>, 2>, tensor<1x1x!ttcore.tile<32x32, f32>, #ttl.layout<shape = [32, 2048], element_type = !ttcore.tile<32x32, f32>, buffer = l1, grid = [1, 1], memory = interleaved>>) -> !ttl.transfer_handle<write>
      ttl.wait %5 : !ttl.transfer_handle<write>
      ttl.cb_pop %0 : <[1, 1], !ttcore.tile<32x32, f32>, 2>
    }
    return
  }
}
