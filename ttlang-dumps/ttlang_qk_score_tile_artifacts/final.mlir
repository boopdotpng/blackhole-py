module attributes {ttl.compiler_allocated_dfbs = [{block_count = 2 : i32, dfb_index = 4 : i32, element_type = !ttcore.tile<32x32, bf16>, num_tiles = 2 : i32}, {block_count = 2 : i32, dfb_index = 5 : i32, element_type = !ttcore.tile<32x32, bf16>, num_tiles = 1 : i32}, {block_count = 2 : i32, dfb_index = 6 : i32, element_type = !ttcore.tile<32x32, bf16>, num_tiles = 1 : i32}], ttl.launch_grid = [1, 1], ttl.pipe_sync_semaphore_count = 0 : i64, ttl.target_arch = "blackhole"} {
  func.func @compute() attributes {ttkernel.thread = #ttkernel.thread<compute>, ttl.base_cta_index = 7 : i32, ttl.crta_indices = [], ttl.enable_fpu_binary_ops = true} {
    %0 = "emitc.constant"() <{value = 1.000000e+00 : f32}> : () -> f32
    %1 = "emitc.constant"() <{value = 1 : i32}> : () -> i32
    %2 = "emitc.constant"() <{value = 2 : i32}> : () -> i32
    %3 = "emitc.constant"() <{value = 2 : index}> : () -> !emitc.size_t
    %4 = "emitc.constant"() <{value = 1 : index}> : () -> !emitc.size_t
    %5 = "emitc.constant"() <{value = 0 : index}> : () -> !emitc.size_t
    %6 = emitc.literal "get_compile_time_arg_val(1)" {ttkernel.cb_ctarg_idx = 1 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_1({});" args %6 : ui32
    %7 = emitc.literal "get_compile_time_arg_val(0)" {ttkernel.cb_ctarg_idx = 0 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_0({});" args %7 : ui32
    %8 = emitc.literal "get_compile_time_arg_val(2)" {ttkernel.cb_ctarg_idx = 2 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_2({});" args %8 : ui32
    %9 = emitc.literal "get_compile_time_arg_val(3)" {ttkernel.cb_ctarg_idx = 3 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_3({});" args %9 : ui32
    %10 = emitc.literal "get_compile_time_arg_val(4)" {ttkernel.cb_ctarg_idx = 4 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_4({});" args %10 : ui32
    %11 = emitc.literal "get_compile_time_arg_val(5)" {ttkernel.cb_ctarg_idx = 5 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_5({});" args %11 : ui32
    %12 = emitc.literal "get_compile_time_arg_val(6)" {ttkernel.cb_ctarg_idx = 6 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_6({});" args %12 : ui32
    emitc.verbatim "cb_ctarg_0.wait_front({});" args %2 : i32
    emitc.verbatim "cb_ctarg_1.wait_front({});" args %2 : i32
    emitc.verbatim "cb_ctarg_2.wait_front({});" args %1 : i32
    emitc.verbatim "cb_ctarg_4.reserve_back({});" args %2 : i32
    emitc.call_opaque "binary_op_init_common"(%7, %6, %10)  : (ui32, ui32, ui32) -> ()
    emitc.call_opaque "tile_regs_acquire"()  : () -> ()
    emitc.call_opaque "mul_tiles_init"(%7, %6)  : (ui32, ui32) -> ()
    emitc.call_opaque "mul_tiles"(%7, %6, %5, %5, %5)  : (ui32, ui32, !emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "mul_tiles"(%7, %6, %4, %4, %4)  : (ui32, ui32, !emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_commit"()  : () -> ()
    emitc.call_opaque "tile_regs_wait"()  : () -> ()
    emitc.call_opaque "pack_tile_block"(%5, %10, %3)  : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_release"()  : () -> ()
    emitc.verbatim "cb_ctarg_4.push_back({});" args %2 : i32
    emitc.verbatim "cb_ctarg_4.wait_front({});" args %2 : i32
    emitc.verbatim "cb_ctarg_5.reserve_back({});" args %1 : i32
    emitc.call_opaque "init_sfpu"(%11, %11)  : (ui32, ui32) -> ()
    emitc.call_opaque "tile_regs_acquire"()  : () -> ()
    emitc.call_opaque "fill_tile_init"()  : () -> ()
    emitc.call_opaque "fill_tile"(%5, %0)  : (!emitc.size_t, f32) -> ()
    emitc.call_opaque "tile_regs_commit"()  : () -> ()
    emitc.call_opaque "tile_regs_wait"()  : () -> ()
    emitc.call_opaque "pack_tile"(%5, %11, %5) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_release"()  : () -> ()
    emitc.verbatim "cb_ctarg_5.push_back({});" args %1 : i32
    emitc.verbatim "cb_ctarg_5.wait_front({});" args %1 : i32
    emitc.verbatim "cb_ctarg_6.reserve_back({});" args %1 : i32
    emitc.call_opaque "init_sfpu"(%10, %12)  : (ui32, ui32) -> ()
    emitc.call_opaque "tile_regs_acquire"()  : () -> ()
    emitc.call_opaque "reduce_init"(%10, %11, %12) <{template_args = [#emitc.opaque<"PoolType::SUM">, #emitc.opaque<"ReduceDim::REDUCE_ROW">, #emitc.opaque<"false">]}> : (ui32, ui32, ui32) -> ()
    emitc.for %arg0 = %5 to %3 step %4  : !emitc.size_t {
      call_opaque "reduce_tile"(%10, %11, %arg0, %5, %5) <{template_args = [#emitc.opaque<"PoolType::SUM">, #emitc.opaque<"ReduceDim::REDUCE_ROW">, #emitc.opaque<"false">]}> : (ui32, ui32, !emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
    }
    emitc.call_opaque "reduce_uninit"()  : () -> ()
    emitc.call_opaque "tile_regs_commit"()  : () -> ()
    emitc.call_opaque "tile_regs_wait"()  : () -> ()
    emitc.call_opaque "pack_tile"(%5, %12, %5) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_release"()  : () -> ()
    emitc.verbatim "cb_ctarg_5.pop_front({});" args %1 : i32
    emitc.verbatim "cb_ctarg_4.pop_front({});" args %2 : i32
    emitc.verbatim "cb_ctarg_6.push_back({});" args %1 : i32
    emitc.verbatim "cb_ctarg_6.wait_front({});" args %1 : i32
    emitc.verbatim "cb_ctarg_3.reserve_back({});" args %1 : i32
    emitc.call_opaque "binary_op_init_common"(%12, %8, %9)  : (ui32, ui32, ui32) -> ()
    emitc.call_opaque "tile_regs_acquire"()  : () -> ()
    emitc.call_opaque "mul_tiles_init"(%12, %8)  : (ui32, ui32) -> ()
    emitc.call_opaque "mul_tiles"(%12, %8, %5, %5, %5)  : (ui32, ui32, !emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_commit"()  : () -> ()
    emitc.call_opaque "tile_regs_wait"()  : () -> ()
    emitc.call_opaque "pack_tile"(%5, %9, %5) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_release"()  : () -> ()
    emitc.verbatim "cb_ctarg_6.pop_front({});" args %1 : i32
    emitc.verbatim "cb_ctarg_3.push_back({});" args %1 : i32
    emitc.verbatim "cb_ctarg_2.pop_front({});" args %1 : i32
    emitc.verbatim "cb_ctarg_1.pop_front({});" args %2 : i32
    emitc.verbatim "cb_ctarg_0.pop_front({});" args %2 : i32
    return
  }
  func.func @dm_read() attributes {ttkernel.arg_spec = #ttkernel.arg_spec< ct_args = [<arg_type = buffer_address, operand_index = 0>, <arg_type = buffer_address, operand_index = 1>, <arg_type = buffer_address, operand_index = 2>]>, ttkernel.thread = #ttkernel.thread<noc>, ttl.base_cta_index = 7 : i32, ttl.crta_indices = [1 : i32, 0 : i32, 2 : i32], ttl.enable_fpu_binary_ops = true} {
    emitc.verbatim "Noc noc0(0);"
    %0 = "emitc.constant"() <{value = 2 : index}> : () -> !emitc.size_t
    %1 = "emitc.constant"() <{value = 0 : i8}> : () -> i8
    %2 = "emitc.constant"() <{value = 2048 : index}> : () -> !emitc.size_t
    %3 = "emitc.constant"() <{value = 1 : i32}> : () -> i32
    %4 = "emitc.constant"() <{value = 0 : i32}> : () -> i32
    %5 = "emitc.constant"() <{value = 2048 : i32}> : () -> i32
    %6 = "emitc.constant"() <{value = 1 : index}> : () -> !emitc.size_t
    %7 = "emitc.constant"() <{value = 2 : i32}> : () -> i32
    %8 = "emitc.constant"() <{value = 0 : index}> : () -> !emitc.size_t
    %9 = emitc.literal "get_compile_time_arg_val(1)" {ttkernel.cb_ctarg_idx = 1 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_1({});" args %9 : ui32
    %10 = emitc.literal "get_compile_time_arg_val(0)" {ttkernel.cb_ctarg_idx = 0 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_0({});" args %10 : ui32
    %11 = emitc.literal "get_compile_time_arg_val(2)" {ttkernel.cb_ctarg_idx = 2 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_2({});" args %11 : ui32
    emitc.verbatim "cb_ctarg_0.reserve_back({});" args %7 : i32
    %12 = emitc.call_opaque "get_common_arg_val"(%6) <{template_args = [#emitc.opaque<"uint32_t">]}> : (!emitc.size_t) -> i32
    emitc.verbatim "auto tensor_accessor_args_0 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<0, 7>(), 1>();"
    %13 = emitc.literal "tensor_accessor_args_0" : !emitc.opaque<"TensorAccessorArgs">
    %14 = emitc.call_opaque "TensorAccessor"(%13, %12, %5)  : (!emitc.opaque<"TensorAccessorArgs">, i32, i32) -> !emitc.opaque<"TensorAccessor">
    %15 = emitc.literal "cb_ctarg_0.get_write_ptr()" : i32
    %16 = emitc.cast %15 : i32 to !emitc.ptrdiff_t
    %17 = emitc.cast %16 : !emitc.ptrdiff_t to !emitc.size_t
    emitc.for %arg0 = %8 to %0 step %6  : !emitc.size_t {
      %28 = mul %arg0, %2 : (!emitc.size_t, !emitc.size_t) -> !emitc.size_t
      %29 = add %17, %28 : (!emitc.size_t, !emitc.size_t) -> !emitc.size_t
      %30 = cast %arg0 : !emitc.size_t to !emitc.ptrdiff_t
      %31 = cast %30 : !emitc.ptrdiff_t to i32
      %32 = cast %29 : !emitc.size_t to !emitc.ptrdiff_t
      %33 = cast %32 : !emitc.ptrdiff_t to i32
      verbatim "noc0.async_read({}, CoreLocalMem<uint32_t>({}), {}.get_aligned_page_size(), {{.page_id = static_cast<uint32_t>({})}, {{});" args %14, %33, %14, %31 : !emitc.opaque<"TensorAccessor">, i32, !emitc.opaque<"TensorAccessor">, i32
    }
    emitc.verbatim "noc0.async_read_barrier();"
    emitc.verbatim "cb_ctarg_0.push_back({});" args %7 : i32
    emitc.verbatim "cb_ctarg_1.reserve_back({});" args %7 : i32
    %18 = emitc.call_opaque "get_common_arg_val"(%8) <{template_args = [#emitc.opaque<"uint32_t">]}> : (!emitc.size_t) -> i32
    emitc.verbatim "auto tensor_accessor_args_1 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<1, 7>(), 0>();"
    %19 = emitc.literal "tensor_accessor_args_1" : !emitc.opaque<"TensorAccessorArgs">
    %20 = emitc.call_opaque "TensorAccessor"(%19, %18, %5)  : (!emitc.opaque<"TensorAccessorArgs">, i32, i32) -> !emitc.opaque<"TensorAccessor">
    %21 = emitc.literal "cb_ctarg_1.get_write_ptr()" : i32
    %22 = emitc.cast %21 : i32 to !emitc.ptrdiff_t
    %23 = emitc.cast %22 : !emitc.ptrdiff_t to !emitc.size_t
    emitc.for %arg0 = %8 to %0 step %6  : !emitc.size_t {
      %28 = mul %arg0, %2 : (!emitc.size_t, !emitc.size_t) -> !emitc.size_t
      %29 = add %23, %28 : (!emitc.size_t, !emitc.size_t) -> !emitc.size_t
      %30 = cast %arg0 : !emitc.size_t to !emitc.ptrdiff_t
      %31 = cast %30 : !emitc.ptrdiff_t to i32
      %32 = cast %29 : !emitc.size_t to !emitc.ptrdiff_t
      %33 = cast %32 : !emitc.ptrdiff_t to i32
      verbatim "noc0.async_read({}, CoreLocalMem<uint32_t>({}), {}.get_aligned_page_size(), {{.page_id = static_cast<uint32_t>({})}, {{});" args %20, %33, %20, %31 : !emitc.opaque<"TensorAccessor">, i32, !emitc.opaque<"TensorAccessor">, i32
    }
    emitc.verbatim "noc0.async_read_barrier();"
    emitc.verbatim "cb_ctarg_1.push_back({});" args %7 : i32
    emitc.verbatim "cb_ctarg_2.reserve_back({});" args %3 : i32
    %24 = emitc.call_opaque "get_common_arg_val"(%0) <{template_args = [#emitc.opaque<"uint32_t">]}> : (!emitc.size_t) -> i32
    emitc.verbatim "auto tensor_accessor_args_2 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<2, 7>(), 2>();"
    %25 = emitc.literal "tensor_accessor_args_2" : !emitc.opaque<"TensorAccessorArgs">
    %26 = emitc.call_opaque "TensorAccessor"(%25, %24, %5)  : (!emitc.opaque<"TensorAccessorArgs">, i32, i32) -> !emitc.opaque<"TensorAccessor">
    %27 = emitc.literal "cb_ctarg_2.get_write_ptr()" : i32
    emitc.verbatim "noc0.async_read({}, CoreLocalMem<uint32_t>({}), {}.get_aligned_page_size(), {{.page_id = static_cast<uint32_t>({})}, {{});" args %26, %27, %26, %4 : !emitc.opaque<"TensorAccessor">, i32, !emitc.opaque<"TensorAccessor">, i32
    emitc.verbatim "noc0.async_read_barrier();"
    emitc.verbatim "cb_ctarg_2.push_back({});" args %3 : i32
    return
  }
  func.func @dm_write() attributes {ttkernel.arg_spec = #ttkernel.arg_spec< ct_args = [<arg_type = buffer_address, operand_index = 0>]>, ttkernel.thread = #ttkernel.thread<noc>, ttl.base_cta_index = 7 : i32, ttl.crta_indices = [3 : i32], ttl.enable_fpu_binary_ops = true} {
    emitc.verbatim "Noc noc1(1);"
    %0 = "emitc.constant"() <{value = 1 : i8}> : () -> i8
    %1 = "emitc.constant"() <{value = 0 : i32}> : () -> i32
    %2 = "emitc.constant"() <{value = 2048 : i32}> : () -> i32
    %3 = "emitc.constant"() <{value = 1 : i32}> : () -> i32
    %4 = "emitc.constant"() <{value = 0 : index}> : () -> !emitc.size_t
    %5 = emitc.literal "get_compile_time_arg_val(3)" {ttkernel.cb_ctarg_idx = 3 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_3({});" args %5 : ui32
    emitc.verbatim "cb_ctarg_3.wait_front({});" args %3 : i32
    %6 = emitc.call_opaque "get_common_arg_val"(%4) <{template_args = [#emitc.opaque<"uint32_t">]}> : (!emitc.size_t) -> i32
    emitc.verbatim "auto tensor_accessor_args_0 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<3, 7>(), 0>();"
    %7 = emitc.literal "tensor_accessor_args_0" : !emitc.opaque<"TensorAccessorArgs">
    %8 = emitc.call_opaque "TensorAccessor"(%7, %6, %2)  : (!emitc.opaque<"TensorAccessorArgs">, i32, i32) -> !emitc.opaque<"TensorAccessor">
    %9 = emitc.literal "cb_ctarg_3.get_read_ptr()" : i32
    emitc.verbatim "noc1.async_write(CoreLocalMem<uint32_t>({}), {}, {}.get_aligned_page_size(), {{} , {{.page_id = static_cast<uint32_t>({})});" args %9, %8, %8, %1 : i32, !emitc.opaque<"TensorAccessor">, !emitc.opaque<"TensorAccessor">, i32
    emitc.verbatim "noc1.async_write_barrier();"
    emitc.verbatim "cb_ctarg_3.pop_front({});" args %3 : i32
    return
  }
}
