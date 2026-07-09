module attributes {ttl.launch_grid = [2, 32], ttl.pipe_sync_semaphore_count = 0 : i64} {
  func.func @compute() attributes {ttkernel.thread = #ttkernel.thread<compute>, ttl.base_cta_index = 4 : i32, ttl.crta_indices = [], ttl.enable_fpu_binary_ops = true} {
    %0 = "emitc.constant"() <{value = 1 : i32}> : () -> i32
    %1 = "emitc.constant"() <{value = 0 : index}> : () -> !emitc.size_t
    %2 = emitc.literal "get_compile_time_arg_val(0)" {ttkernel.cb_ctarg_idx = 0 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_0({});" args %2 : ui32
    %3 = emitc.literal "get_compile_time_arg_val(2)" {ttkernel.cb_ctarg_idx = 2 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_2({});" args %3 : ui32
    %4 = emitc.literal "get_compile_time_arg_val(1)" {ttkernel.cb_ctarg_idx = 1 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_1({});" args %4 : ui32
    %5 = emitc.literal "get_compile_time_arg_val(3)" {ttkernel.cb_ctarg_idx = 3 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_3({});" args %5 : ui32
    emitc.verbatim "cb_ctarg_0.wait_front({});" args %0 : i32
    emitc.verbatim "cb_ctarg_2.reserve_back({});" args %0 : i32
    emitc.call_opaque "init_sfpu"(%2, %3)  : (ui32, ui32) -> ()
    emitc.call_opaque "tile_regs_acquire"()  : () -> ()
    emitc.call_opaque "copy_tile_init"(%2)  : (ui32) -> ()
    emitc.call_opaque "copy_tile"(%2, %1, %1)  : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_commit"()  : () -> ()
    emitc.call_opaque "tile_regs_wait"()  : () -> ()
    emitc.call_opaque "pack_tile"(%1, %3, %1) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_release"()  : () -> ()
    emitc.verbatim "cb_ctarg_2.push_back({});" args %0 : i32
    emitc.verbatim "cb_ctarg_0.pop_front({});" args %0 : i32
    emitc.verbatim "cb_ctarg_1.wait_front({});" args %0 : i32
    emitc.verbatim "cb_ctarg_3.reserve_back({});" args %0 : i32
    emitc.call_opaque "init_sfpu"(%4, %5)  : (ui32, ui32) -> ()
    emitc.call_opaque "tile_regs_acquire"()  : () -> ()
    emitc.call_opaque "copy_tile_init"(%4)  : (ui32) -> ()
    emitc.call_opaque "copy_tile"(%4, %1, %1)  : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_commit"()  : () -> ()
    emitc.call_opaque "tile_regs_wait"()  : () -> ()
    emitc.call_opaque "pack_tile"(%1, %5, %1) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_release"()  : () -> ()
    emitc.verbatim "cb_ctarg_3.push_back({});" args %0 : i32
    emitc.verbatim "cb_ctarg_1.pop_front({});" args %0 : i32
    return
  }
  func.func @dm_read() attributes {ttkernel.arg_spec = #ttkernel.arg_spec< ct_args = [<arg_type = buffer_address, operand_index = 0>, <arg_type = buffer_address, operand_index = 1>]>, ttkernel.thread = #ttkernel.thread<noc>, ttl.base_cta_index = 4 : i32, ttl.crta_indices = [0 : i32, 1 : i32], ttl.enable_fpu_binary_ops = true} {
    emitc.verbatim "Noc noc0(0);"
    %0 = "emitc.constant"() <{value = 14 : index}> : () -> !emitc.size_t
    %1 = "emitc.constant"() <{value = 512 : index}> : () -> !emitc.size_t
    %2 = "emitc.constant"() <{value = 1 : index}> : () -> !emitc.size_t
    %3 = "emitc.constant"() <{value = 0 : i8}> : () -> i8
    %4 = "emitc.constant"() <{value = 0 : i32}> : () -> i32
    %5 = "emitc.constant"() <{value = 2048 : i32}> : () -> i32
    %6 = "emitc.constant"() <{value = 0 : index}> : () -> !emitc.size_t
    %7 = "emitc.constant"() <{value = 1 : i32}> : () -> i32
    %8 = "emitc.constant"() <{value = 4 : index}> : () -> !emitc.size_t
    %9 = emitc.literal "get_compile_time_arg_val(0)" {ttkernel.cb_ctarg_idx = 0 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_0({});" args %9 : ui32
    %10 = emitc.literal "get_compile_time_arg_val(1)" {ttkernel.cb_ctarg_idx = 1 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_1({});" args %10 : ui32
    %11 = "emitc.constant"() <{value = #emitc.opaque<"get_absolute_logical_x()">}> : () -> !emitc.size_t
    %12 = "emitc.constant"() <{value = #emitc.opaque<"get_absolute_logical_y()">}> : () -> !emitc.size_t
    %13 = emitc.div %12, %8 : (!emitc.size_t, !emitc.size_t) -> !emitc.size_t
    emitc.verbatim "cb_ctarg_0.reserve_back({});" args %7 : i32
    %14 = emitc.call_opaque "get_common_arg_val"(%6) <{template_args = [#emitc.opaque<"uint32_t">]}> : (!emitc.size_t) -> i32
    emitc.verbatim "auto tensor_accessor_args_0 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<0, 4>(), 0>();"
    %15 = emitc.literal "tensor_accessor_args_0" : !emitc.opaque<"TensorAccessorArgs">
    %16 = emitc.call_opaque "TensorAccessor"(%15, %14, %5)  : (!emitc.opaque<"TensorAccessorArgs">, i32, i32) -> !emitc.opaque<"TensorAccessor">
    %17 = emitc.literal "cb_ctarg_0.get_write_ptr()" : i32
    %18 = emitc.mul %13, %1 : (!emitc.size_t, !emitc.size_t) -> !emitc.size_t
    %19 = emitc.add %18, %0 : (!emitc.size_t, !emitc.size_t) -> !emitc.size_t
    %20 = emitc.add %19, %11 : (!emitc.size_t, !emitc.size_t) -> !emitc.size_t
    %21 = emitc.cast %20 : !emitc.size_t to !emitc.ptrdiff_t
    %22 = emitc.cast %21 : !emitc.ptrdiff_t to i32
    emitc.verbatim "noc0.async_read({}, CoreLocalMem<uint32_t>({}), {}.get_aligned_page_size(), {{.page_id = static_cast<uint32_t>({})}, {{});" args %16, %17, %16, %22 : !emitc.opaque<"TensorAccessor">, i32, !emitc.opaque<"TensorAccessor">, i32
    emitc.verbatim "noc0.async_read_barrier();"
    emitc.verbatim "cb_ctarg_0.push_back({});" args %7 : i32
    emitc.verbatim "cb_ctarg_1.reserve_back({});" args %7 : i32
    %23 = emitc.call_opaque "get_common_arg_val"(%2) <{template_args = [#emitc.opaque<"uint32_t">]}> : (!emitc.size_t) -> i32
    emitc.verbatim "auto tensor_accessor_args_1 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<1, 4>(), 1>();"
    %24 = emitc.literal "tensor_accessor_args_1" : !emitc.opaque<"TensorAccessorArgs">
    %25 = emitc.call_opaque "TensorAccessor"(%24, %23, %5)  : (!emitc.opaque<"TensorAccessorArgs">, i32, i32) -> !emitc.opaque<"TensorAccessor">
    %26 = emitc.literal "cb_ctarg_1.get_write_ptr()" : i32
    emitc.verbatim "noc0.async_read({}, CoreLocalMem<uint32_t>({}), {}.get_aligned_page_size(), {{.page_id = static_cast<uint32_t>({})}, {{});" args %25, %26, %25, %22 : !emitc.opaque<"TensorAccessor">, i32, !emitc.opaque<"TensorAccessor">, i32
    emitc.verbatim "noc0.async_read_barrier();"
    emitc.verbatim "cb_ctarg_1.push_back({});" args %7 : i32
    return
  }
  func.func @dm_write() attributes {ttkernel.arg_spec = #ttkernel.arg_spec< ct_args = [<arg_type = buffer_address, operand_index = 0>, <arg_type = buffer_address, operand_index = 1>]>, ttkernel.thread = #ttkernel.thread<noc>, ttl.base_cta_index = 4 : i32, ttl.crta_indices = [2 : i32, 3 : i32], ttl.enable_fpu_binary_ops = true} {
    emitc.verbatim "Noc noc1(1);"
    %0 = "emitc.constant"() <{value = 2 : index}> : () -> !emitc.size_t
    %1 = "emitc.constant"() <{value = 1 : index}> : () -> !emitc.size_t
    %2 = "emitc.constant"() <{value = 1 : i8}> : () -> i8
    %3 = "emitc.constant"() <{value = 0 : i32}> : () -> i32
    %4 = "emitc.constant"() <{value = 2048 : i32}> : () -> i32
    %5 = "emitc.constant"() <{value = 1 : i32}> : () -> i32
    %6 = "emitc.constant"() <{value = 0 : index}> : () -> !emitc.size_t
    %7 = emitc.literal "get_compile_time_arg_val(2)" {ttkernel.cb_ctarg_idx = 2 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_2({});" args %7 : ui32
    %8 = emitc.literal "get_compile_time_arg_val(3)" {ttkernel.cb_ctarg_idx = 3 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_3({});" args %8 : ui32
    %9 = "emitc.constant"() <{value = #emitc.opaque<"get_absolute_logical_x()">}> : () -> !emitc.size_t
    %10 = "emitc.constant"() <{value = #emitc.opaque<"get_absolute_logical_y()">}> : () -> !emitc.size_t
    emitc.verbatim "cb_ctarg_2.wait_front({});" args %5 : i32
    %11 = emitc.call_opaque "get_common_arg_val"(%6) <{template_args = [#emitc.opaque<"uint32_t">]}> : (!emitc.size_t) -> i32
    emitc.verbatim "auto tensor_accessor_args_0 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<2, 4>(), 0>();"
    %12 = emitc.literal "tensor_accessor_args_0" : !emitc.opaque<"TensorAccessorArgs">
    %13 = emitc.call_opaque "TensorAccessor"(%12, %11, %4)  : (!emitc.opaque<"TensorAccessorArgs">, i32, i32) -> !emitc.opaque<"TensorAccessor">
    %14 = emitc.literal "cb_ctarg_2.get_read_ptr()" : i32
    %15 = emitc.mul %10, %0 : (!emitc.size_t, !emitc.size_t) -> !emitc.size_t
    %16 = emitc.add %15, %9 : (!emitc.size_t, !emitc.size_t) -> !emitc.size_t
    %17 = emitc.cast %16 : !emitc.size_t to !emitc.ptrdiff_t
    %18 = emitc.cast %17 : !emitc.ptrdiff_t to i32
    emitc.verbatim "noc1.async_write(CoreLocalMem<uint32_t>({}), {}, {}.get_aligned_page_size(), {{} , {{.page_id = static_cast<uint32_t>({})});" args %14, %13, %13, %18 : i32, !emitc.opaque<"TensorAccessor">, !emitc.opaque<"TensorAccessor">, i32
    emitc.verbatim "noc1.async_write_barrier();"
    emitc.verbatim "cb_ctarg_2.pop_front({});" args %5 : i32
    emitc.verbatim "cb_ctarg_3.wait_front({});" args %5 : i32
    %19 = emitc.call_opaque "get_common_arg_val"(%1) <{template_args = [#emitc.opaque<"uint32_t">]}> : (!emitc.size_t) -> i32
    emitc.verbatim "auto tensor_accessor_args_1 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<3, 4>(), 1>();"
    %20 = emitc.literal "tensor_accessor_args_1" : !emitc.opaque<"TensorAccessorArgs">
    %21 = emitc.call_opaque "TensorAccessor"(%20, %19, %4)  : (!emitc.opaque<"TensorAccessorArgs">, i32, i32) -> !emitc.opaque<"TensorAccessor">
    %22 = emitc.literal "cb_ctarg_3.get_read_ptr()" : i32
    emitc.verbatim "noc1.async_write(CoreLocalMem<uint32_t>({}), {}, {}.get_aligned_page_size(), {{} , {{.page_id = static_cast<uint32_t>({})});" args %22, %21, %21, %18 : i32, !emitc.opaque<"TensorAccessor">, !emitc.opaque<"TensorAccessor">, i32
    emitc.verbatim "noc1.async_write_barrier();"
    emitc.verbatim "cb_ctarg_3.pop_front({});" args %5 : i32
    return
  }
}
