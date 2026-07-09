module attributes {ttl.launch_grid = [1, 1], ttl.pipe_sync_semaphore_count = 0 : i64, ttl.target_arch = "blackhole"} {
  func.func @compute() attributes {ttkernel.thread = #ttkernel.thread<compute>, ttl.base_cta_index = 3 : i32, ttl.crta_indices = [], ttl.enable_fpu_binary_ops = true} {
    %0 = "emitc.constant"() <{value = 7 : index}> : () -> !emitc.size_t
    %1 = "emitc.constant"() <{value = 6 : index}> : () -> !emitc.size_t
    %2 = "emitc.constant"() <{value = 5 : index}> : () -> !emitc.size_t
    %3 = "emitc.constant"() <{value = 4 : index}> : () -> !emitc.size_t
    %4 = "emitc.constant"() <{value = 3 : index}> : () -> !emitc.size_t
    %5 = "emitc.constant"() <{value = 2 : index}> : () -> !emitc.size_t
    %6 = "emitc.constant"() <{value = 4 : i32}> : () -> i32
    %7 = "emitc.constant"() <{value = 1 : index}> : () -> !emitc.size_t
    %8 = "emitc.constant"() <{value = 0 : index}> : () -> !emitc.size_t
    %9 = emitc.literal "get_compile_time_arg_val(0)" {ttkernel.cb_ctarg_idx = 0 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_0({});" args %9 : ui32
    %10 = emitc.literal "get_compile_time_arg_val(2)" {ttkernel.cb_ctarg_idx = 2 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_2({});" args %10 : ui32
    %11 = emitc.literal "get_compile_time_arg_val(1)" {ttkernel.cb_ctarg_idx = 1 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_1({});" args %11 : ui32
    emitc.verbatim "cb_ctarg_0.wait_front({});" args %6 : i32
    emitc.verbatim "cb_ctarg_1.wait_front({});" args %6 : i32
    emitc.verbatim "cb_ctarg_2.reserve_back({});" args %6 : i32
    emitc.call_opaque "init_sfpu"(%9, %10)  : (ui32, ui32) -> ()
    emitc.call_opaque "tile_regs_acquire"()  : () -> ()
    emitc.call_opaque "copy_tile_init"(%9)  : (ui32) -> ()
    emitc.call_opaque "copy_tile"(%9, %8, %8)  : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "copy_tile"(%9, %7, %5)  : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "copy_tile"(%9, %5, %3)  : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "copy_tile"(%9, %4, %1)  : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "copy_tile_init"(%11)  : (ui32) -> ()
    emitc.call_opaque "copy_tile"(%11, %8, %7)  : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "copy_tile"(%11, %7, %4)  : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "copy_tile"(%11, %5, %2)  : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "copy_tile"(%11, %4, %0)  : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "silu_tile_init"()  : () -> ()
    emitc.call_opaque "silu_tile"(%8)  : (!emitc.size_t) -> ()
    emitc.call_opaque "silu_tile"(%5)  : (!emitc.size_t) -> ()
    emitc.call_opaque "silu_tile"(%3)  : (!emitc.size_t) -> ()
    emitc.call_opaque "silu_tile"(%1)  : (!emitc.size_t) -> ()
    emitc.call_opaque "mul_binary_tile_init"()  : () -> ()
    emitc.call_opaque "mul_binary_tile"(%8, %7, %8)  : (!emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "mul_binary_tile"(%5, %4, %5)  : (!emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "mul_binary_tile"(%3, %2, %3)  : (!emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "mul_binary_tile"(%1, %0, %1)  : (!emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_commit"()  : () -> ()
    emitc.call_opaque "tile_regs_wait"()  : () -> ()
    emitc.call_opaque "pack_tile"(%8, %10, %8) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "pack_tile"(%5, %10, %7) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "pack_tile"(%3, %10, %5) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "pack_tile"(%1, %10, %4) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_release"()  : () -> ()
    emitc.verbatim "cb_ctarg_2.push_back({});" args %6 : i32
    emitc.verbatim "cb_ctarg_1.pop_front({});" args %6 : i32
    emitc.verbatim "cb_ctarg_0.pop_front({});" args %6 : i32
    return
  }
  func.func @dm_read() attributes {ttkernel.arg_spec = #ttkernel.arg_spec< ct_args = [<arg_type = buffer_address, operand_index = 0>, <arg_type = buffer_address, operand_index = 1>]>, ttkernel.thread = #ttkernel.thread<noc>, ttl.base_cta_index = 3 : i32, ttl.crta_indices = [0 : i32, 1 : i32], ttl.enable_fpu_binary_ops = true} {
    emitc.verbatim "Noc noc0(0);"
    %0 = "emitc.constant"() <{value = 1 : i32}> : () -> i32
    %1 = "emitc.constant"() <{value = 4 : index}> : () -> !emitc.size_t
    %2 = "emitc.constant"() <{value = 1 : index}> : () -> !emitc.size_t
    %3 = "emitc.constant"() <{value = 0 : i8}> : () -> i8
    %4 = "emitc.constant"() <{value = 2048 : index}> : () -> !emitc.size_t
    %5 = "emitc.constant"() <{value = 0 : i32}> : () -> i32
    %6 = "emitc.constant"() <{value = 2048 : i32}> : () -> i32
    %7 = "emitc.constant"() <{value = 4 : i32}> : () -> i32
    %8 = "emitc.constant"() <{value = 0 : index}> : () -> !emitc.size_t
    %9 = emitc.literal "get_compile_time_arg_val(0)" {ttkernel.cb_ctarg_idx = 0 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_0({});" args %9 : ui32
    %10 = emitc.literal "get_compile_time_arg_val(1)" {ttkernel.cb_ctarg_idx = 1 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_1({});" args %10 : ui32
    emitc.verbatim "cb_ctarg_0.reserve_back({});" args %7 : i32
    %11 = emitc.call_opaque "get_common_arg_val"(%8) <{template_args = [#emitc.opaque<"uint32_t">]}> : (!emitc.size_t) -> i32
    emitc.verbatim "auto tensor_accessor_args_0 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<0, 3>(), 0>();"
    %12 = emitc.literal "tensor_accessor_args_0" : !emitc.opaque<"TensorAccessorArgs">
    %13 = emitc.call_opaque "TensorAccessor"(%12, %11, %6)  : (!emitc.opaque<"TensorAccessorArgs">, i32, i32) -> !emitc.opaque<"TensorAccessor">
    %14 = emitc.literal "cb_ctarg_0.get_write_ptr()" : i32
    %15 = emitc.cast %14 : i32 to !emitc.ptrdiff_t
    %16 = emitc.cast %15 : !emitc.ptrdiff_t to !emitc.size_t
    emitc.for %arg0 = %8 to %1 step %2  : !emitc.size_t {
      %23 = mul %arg0, %4 : (!emitc.size_t, !emitc.size_t) -> !emitc.size_t
      %24 = add %16, %23 : (!emitc.size_t, !emitc.size_t) -> !emitc.size_t
      %25 = cast %arg0 : !emitc.size_t to !emitc.ptrdiff_t
      %26 = cast %25 : !emitc.ptrdiff_t to i32
      %27 = cast %24 : !emitc.size_t to !emitc.ptrdiff_t
      %28 = cast %27 : !emitc.ptrdiff_t to i32
      verbatim "noc0.async_read({}, CoreLocalMem<uint32_t>({}), {}.get_aligned_page_size(), {{.page_id = static_cast<uint32_t>({})}, {{});" args %13, %28, %13, %26 : !emitc.opaque<"TensorAccessor">, i32, !emitc.opaque<"TensorAccessor">, i32
    }
    emitc.verbatim "noc0.async_read_barrier();"
    emitc.verbatim "cb_ctarg_0.push_back({});" args %7 : i32
    emitc.verbatim "cb_ctarg_1.reserve_back({});" args %7 : i32
    %17 = emitc.call_opaque "get_common_arg_val"(%2) <{template_args = [#emitc.opaque<"uint32_t">]}> : (!emitc.size_t) -> i32
    emitc.verbatim "auto tensor_accessor_args_1 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<1, 3>(), 1>();"
    %18 = emitc.literal "tensor_accessor_args_1" : !emitc.opaque<"TensorAccessorArgs">
    %19 = emitc.call_opaque "TensorAccessor"(%18, %17, %6)  : (!emitc.opaque<"TensorAccessorArgs">, i32, i32) -> !emitc.opaque<"TensorAccessor">
    %20 = emitc.literal "cb_ctarg_1.get_write_ptr()" : i32
    %21 = emitc.cast %20 : i32 to !emitc.ptrdiff_t
    %22 = emitc.cast %21 : !emitc.ptrdiff_t to !emitc.size_t
    emitc.for %arg0 = %8 to %1 step %2  : !emitc.size_t {
      %23 = mul %arg0, %4 : (!emitc.size_t, !emitc.size_t) -> !emitc.size_t
      %24 = add %22, %23 : (!emitc.size_t, !emitc.size_t) -> !emitc.size_t
      %25 = cast %arg0 : !emitc.size_t to !emitc.ptrdiff_t
      %26 = cast %25 : !emitc.ptrdiff_t to i32
      %27 = cast %24 : !emitc.size_t to !emitc.ptrdiff_t
      %28 = cast %27 : !emitc.ptrdiff_t to i32
      verbatim "noc0.async_read({}, CoreLocalMem<uint32_t>({}), {}.get_aligned_page_size(), {{.page_id = static_cast<uint32_t>({})}, {{});" args %19, %28, %19, %26 : !emitc.opaque<"TensorAccessor">, i32, !emitc.opaque<"TensorAccessor">, i32
    }
    emitc.verbatim "noc0.async_read_barrier();"
    emitc.verbatim "cb_ctarg_1.push_back({});" args %7 : i32
    return
  }
  func.func @dm_write() attributes {ttkernel.arg_spec = #ttkernel.arg_spec< ct_args = [<arg_type = buffer_address, operand_index = 0>]>, ttkernel.thread = #ttkernel.thread<noc>, ttl.base_cta_index = 3 : i32, ttl.crta_indices = [2 : i32], ttl.enable_fpu_binary_ops = true} {
    emitc.verbatim "Noc noc1(1);"
    %0 = "emitc.constant"() <{value = 4 : index}> : () -> !emitc.size_t
    %1 = "emitc.constant"() <{value = 1 : index}> : () -> !emitc.size_t
    %2 = "emitc.constant"() <{value = 1 : i8}> : () -> i8
    %3 = "emitc.constant"() <{value = 2048 : index}> : () -> !emitc.size_t
    %4 = "emitc.constant"() <{value = 0 : i32}> : () -> i32
    %5 = "emitc.constant"() <{value = 2048 : i32}> : () -> i32
    %6 = "emitc.constant"() <{value = 4 : i32}> : () -> i32
    %7 = "emitc.constant"() <{value = 0 : index}> : () -> !emitc.size_t
    %8 = emitc.literal "get_compile_time_arg_val(2)" {ttkernel.cb_ctarg_idx = 2 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_2({});" args %8 : ui32
    emitc.verbatim "cb_ctarg_2.wait_front({});" args %6 : i32
    %9 = emitc.call_opaque "get_common_arg_val"(%7) <{template_args = [#emitc.opaque<"uint32_t">]}> : (!emitc.size_t) -> i32
    emitc.verbatim "auto tensor_accessor_args_0 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<2, 3>(), 0>();"
    %10 = emitc.literal "tensor_accessor_args_0" : !emitc.opaque<"TensorAccessorArgs">
    %11 = emitc.call_opaque "TensorAccessor"(%10, %9, %5)  : (!emitc.opaque<"TensorAccessorArgs">, i32, i32) -> !emitc.opaque<"TensorAccessor">
    %12 = emitc.literal "cb_ctarg_2.get_read_ptr()" : i32
    %13 = emitc.cast %12 : i32 to !emitc.ptrdiff_t
    %14 = emitc.cast %13 : !emitc.ptrdiff_t to !emitc.size_t
    emitc.for %arg0 = %7 to %0 step %1  : !emitc.size_t {
      %15 = mul %arg0, %3 : (!emitc.size_t, !emitc.size_t) -> !emitc.size_t
      %16 = add %14, %15 : (!emitc.size_t, !emitc.size_t) -> !emitc.size_t
      %17 = cast %arg0 : !emitc.size_t to !emitc.ptrdiff_t
      %18 = cast %17 : !emitc.ptrdiff_t to i32
      %19 = cast %16 : !emitc.size_t to !emitc.ptrdiff_t
      %20 = cast %19 : !emitc.ptrdiff_t to i32
      verbatim "noc1.async_write(CoreLocalMem<uint32_t>({}), {}, {}.get_aligned_page_size(), {{} , {{.page_id = static_cast<uint32_t>({})});" args %20, %11, %11, %18 : i32, !emitc.opaque<"TensorAccessor">, !emitc.opaque<"TensorAccessor">, i32
    }
    emitc.verbatim "noc1.async_write_barrier();"
    emitc.verbatim "cb_ctarg_2.pop_front({});" args %6 : i32
    return
  }
}
