module attributes {ttl.launch_grid = [1, 1], ttl.pipe_sync_semaphore_count = 0 : i64, ttl.target_arch = "blackhole"} {
  func.func @compute() attributes {fp32_dest_acc_en = true, ttkernel.thread = #ttkernel.thread<compute>, ttl.base_cta_index = 8 : i32, ttl.crta_indices = [], ttl.enable_fpu_binary_ops = true} {
    %0 = "emitc.constant"() <{value = 1 : i32}> : () -> i32
    %1 = "emitc.constant"() <{value = 1 : index}> : () -> !emitc.size_t
    %2 = "emitc.constant"() <{value = 0 : index}> : () -> !emitc.size_t
    %3 = "emitc.constant"() <{value = 32 : index}> : () -> !emitc.size_t
    %4 = emitc.literal "get_compile_time_arg_val(3)" {ttkernel.cb_ctarg_idx = 3 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_3({});" args %4 : ui32
    %5 = emitc.literal "get_compile_time_arg_val(2)" {ttkernel.cb_ctarg_idx = 2 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_2({});" args %5 : ui32
    %6 = emitc.literal "get_compile_time_arg_val(7)" {ttkernel.cb_ctarg_idx = 7 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_7({});" args %6 : ui32
    %7 = emitc.literal "get_compile_time_arg_val(6)" {ttkernel.cb_ctarg_idx = 6 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_6({});" args %7 : ui32
    %8 = emitc.literal "get_compile_time_arg_val(5)" {ttkernel.cb_ctarg_idx = 5 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_5({});" args %8 : ui32
    %9 = emitc.literal "get_compile_time_arg_val(4)" {ttkernel.cb_ctarg_idx = 4 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_4({});" args %9 : ui32
    %10 = emitc.literal "get_compile_time_arg_val(1)" {ttkernel.cb_ctarg_idx = 1 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_1({});" args %10 : ui32
    %11 = emitc.literal "get_compile_time_arg_val(0)" {ttkernel.cb_ctarg_idx = 0 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_0({});" args %11 : ui32
    emitc.for %arg0 = %2 to %3 step %1  : !emitc.size_t {
      verbatim "cb_ctarg_0.wait_front({});" args %0 : i32
      verbatim "cb_ctarg_1.wait_front({});" args %0 : i32
      verbatim "cb_ctarg_2.wait_front({});" args %0 : i32
      verbatim "cb_ctarg_3.wait_front({});" args %0 : i32
      verbatim "cb_ctarg_4.wait_front({});" args %0 : i32
      verbatim "cb_ctarg_5.wait_front({});" args %0 : i32
      verbatim "cb_ctarg_6.reserve_back({});" args %0 : i32
      verbatim "cb_ctarg_7.reserve_back({});" args %0 : i32
      call_opaque "binary_op_init_common"(%11, %5, %7)  : (ui32, ui32, ui32) -> ()
      call_opaque "tile_regs_acquire"()  : () -> ()
      call_opaque "mul_tiles_init"(%11, %5)  : (ui32, ui32) -> ()
      call_opaque "mul_tiles"(%11, %5, %2, %2, %2)  : (ui32, ui32, !emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
      call_opaque "mul_tiles_init"(%10, %9)  : (ui32, ui32) -> ()
      call_opaque "mul_tiles"(%10, %9, %2, %2, %1)  : (ui32, ui32, !emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
      call_opaque "sub_binary_tile_init"()  : () -> ()
      call_opaque "sub_binary_tile"(%2, %1, %2)  : (!emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
      call_opaque "tile_regs_commit"()  : () -> ()
      call_opaque "tile_regs_wait"()  : () -> ()
      call_opaque "pack_tile"(%2, %7, %2) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
      call_opaque "tile_regs_release"()  : () -> ()
      call_opaque "binary_op_init_common"(%10, %4, %6)  : (ui32, ui32, ui32) -> ()
      call_opaque "tile_regs_acquire"()  : () -> ()
      call_opaque "mul_tiles_init"(%10, %4)  : (ui32, ui32) -> ()
      call_opaque "mul_tiles"(%10, %4, %2, %2, %2)  : (ui32, ui32, !emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
      call_opaque "mul_tiles_init"(%11, %8)  : (ui32, ui32) -> ()
      call_opaque "mul_tiles"(%11, %8, %2, %2, %1)  : (ui32, ui32, !emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
      call_opaque "add_binary_tile_init"()  : () -> ()
      call_opaque "add_binary_tile"(%2, %1, %2)  : (!emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
      call_opaque "tile_regs_commit"()  : () -> ()
      call_opaque "tile_regs_wait"()  : () -> ()
      call_opaque "pack_tile"(%2, %6, %2) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
      call_opaque "tile_regs_release"()  : () -> ()
      verbatim "cb_ctarg_7.push_back({});" args %0 : i32
      verbatim "cb_ctarg_6.push_back({});" args %0 : i32
      verbatim "cb_ctarg_5.pop_front({});" args %0 : i32
      verbatim "cb_ctarg_4.pop_front({});" args %0 : i32
      verbatim "cb_ctarg_3.pop_front({});" args %0 : i32
      verbatim "cb_ctarg_2.pop_front({});" args %0 : i32
      verbatim "cb_ctarg_1.pop_front({});" args %0 : i32
      verbatim "cb_ctarg_0.pop_front({});" args %0 : i32
    }
    return
  }
  func.func @dm_read() attributes {fp32_dest_acc_en = true, ttkernel.arg_spec = #ttkernel.arg_spec< ct_args = [<arg_type = buffer_address, operand_index = 0>, <arg_type = buffer_address, operand_index = 1>, <arg_type = buffer_address, operand_index = 2>]>, ttkernel.thread = #ttkernel.thread<noc>, ttl.base_cta_index = 8 : i32, ttl.crta_indices = [1 : i32, 2 : i32, 0 : i32], ttl.enable_fpu_binary_ops = true} {
    emitc.verbatim "Noc noc0(0);"
    %0 = "emitc.constant"() <{value = 0 : i8}> : () -> i8
    %1 = "emitc.constant"() <{value = 2 : i32}> : () -> i32
    %2 = "emitc.constant"() <{value = 0 : i32}> : () -> i32
    %3 = "emitc.constant"() <{value = 2048 : i32}> : () -> i32
    %4 = "emitc.constant"() <{value = 2 : index}> : () -> !emitc.size_t
    %5 = "emitc.constant"() <{value = 1 : i32}> : () -> i32
    %6 = "emitc.constant"() <{value = 0 : index}> : () -> !emitc.size_t
    %7 = "emitc.constant"() <{value = 32 : index}> : () -> !emitc.size_t
    %8 = "emitc.constant"() <{value = 1 : index}> : () -> !emitc.size_t
    %9 = emitc.literal "get_compile_time_arg_val(3)" {ttkernel.cb_ctarg_idx = 3 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_3({});" args %9 : ui32
    %10 = emitc.literal "get_compile_time_arg_val(2)" {ttkernel.cb_ctarg_idx = 2 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_2({});" args %10 : ui32
    %11 = emitc.literal "get_compile_time_arg_val(5)" {ttkernel.cb_ctarg_idx = 5 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_5({});" args %11 : ui32
    %12 = emitc.literal "get_compile_time_arg_val(4)" {ttkernel.cb_ctarg_idx = 4 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_4({});" args %12 : ui32
    %13 = emitc.literal "get_compile_time_arg_val(1)" {ttkernel.cb_ctarg_idx = 1 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_1({});" args %13 : ui32
    %14 = emitc.literal "get_compile_time_arg_val(0)" {ttkernel.cb_ctarg_idx = 0 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_0({});" args %14 : ui32
    emitc.for %arg0 = %6 to %7 step %8  : !emitc.size_t {
      verbatim "cb_ctarg_0.reserve_back({});" args %5 : i32
      %15 = call_opaque "get_common_arg_val"(%4) <{template_args = [#emitc.opaque<"uint32_t">]}> : (!emitc.size_t) -> i32
      verbatim "auto tensor_accessor_args_0 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<0, 8>(), 2>();"
      %16 = literal "tensor_accessor_args_0" : !emitc.opaque<"TensorAccessorArgs">
      %17 = call_opaque "TensorAccessor"(%16, %15, %3)  : (!emitc.opaque<"TensorAccessorArgs">, i32, i32) -> !emitc.opaque<"TensorAccessor">
      %18 = literal "cb_ctarg_0.get_write_ptr()" : i32
      %19 = mul %arg0, %4 : (!emitc.size_t, !emitc.size_t) -> !emitc.size_t
      %20 = cast %19 : !emitc.size_t to !emitc.ptrdiff_t
      %21 = cast %20 : !emitc.ptrdiff_t to i32
      verbatim "noc0.async_read({}, CoreLocalMem<uint32_t>({}), {}.get_aligned_page_size(), {{.page_id = static_cast<uint32_t>({})}, {{});" args %17, %18, %17, %21 : !emitc.opaque<"TensorAccessor">, i32, !emitc.opaque<"TensorAccessor">, i32
      verbatim "noc0.async_read_barrier();"
      verbatim "cb_ctarg_0.push_back({});" args %5 : i32
      verbatim "cb_ctarg_1.reserve_back({});" args %5 : i32
      verbatim "auto tensor_accessor_args_1 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<0, 8>(), 2>();"
      %22 = literal "tensor_accessor_args_1" : !emitc.opaque<"TensorAccessorArgs">
      %23 = call_opaque "TensorAccessor"(%22, %15, %3)  : (!emitc.opaque<"TensorAccessorArgs">, i32, i32) -> !emitc.opaque<"TensorAccessor">
      %24 = literal "cb_ctarg_1.get_write_ptr()" : i32
      %25 = add %19, %8 : (!emitc.size_t, !emitc.size_t) -> !emitc.size_t
      %26 = cast %25 : !emitc.size_t to !emitc.ptrdiff_t
      %27 = cast %26 : !emitc.ptrdiff_t to i32
      verbatim "noc0.async_read({}, CoreLocalMem<uint32_t>({}), {}.get_aligned_page_size(), {{.page_id = static_cast<uint32_t>({})}, {{});" args %23, %24, %23, %27 : !emitc.opaque<"TensorAccessor">, i32, !emitc.opaque<"TensorAccessor">, i32
      verbatim "noc0.async_read_barrier();"
      verbatim "cb_ctarg_1.push_back({});" args %5 : i32
      verbatim "cb_ctarg_2.reserve_back({});" args %5 : i32
      %28 = call_opaque "get_common_arg_val"(%6) <{template_args = [#emitc.opaque<"uint32_t">]}> : (!emitc.size_t) -> i32
      verbatim "auto tensor_accessor_args_2 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<1, 8>(), 0>();"
      %29 = literal "tensor_accessor_args_2" : !emitc.opaque<"TensorAccessorArgs">
      %30 = call_opaque "TensorAccessor"(%29, %28, %3)  : (!emitc.opaque<"TensorAccessorArgs">, i32, i32) -> !emitc.opaque<"TensorAccessor">
      %31 = literal "cb_ctarg_2.get_write_ptr()" : i32
      verbatim "noc0.async_read({}, CoreLocalMem<uint32_t>({}), {}.get_aligned_page_size(), {{.page_id = static_cast<uint32_t>({})}, {{});" args %30, %31, %30, %2 : !emitc.opaque<"TensorAccessor">, i32, !emitc.opaque<"TensorAccessor">, i32
      verbatim "noc0.async_read_barrier();"
      verbatim "cb_ctarg_2.push_back({});" args %5 : i32
      verbatim "cb_ctarg_3.reserve_back({});" args %5 : i32
      verbatim "auto tensor_accessor_args_3 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<1, 8>(), 0>();"
      %32 = literal "tensor_accessor_args_3" : !emitc.opaque<"TensorAccessorArgs">
      %33 = call_opaque "TensorAccessor"(%32, %28, %3)  : (!emitc.opaque<"TensorAccessorArgs">, i32, i32) -> !emitc.opaque<"TensorAccessor">
      %34 = literal "cb_ctarg_3.get_write_ptr()" : i32
      verbatim "noc0.async_read({}, CoreLocalMem<uint32_t>({}), {}.get_aligned_page_size(), {{.page_id = static_cast<uint32_t>({})}, {{});" args %33, %34, %33, %5 : !emitc.opaque<"TensorAccessor">, i32, !emitc.opaque<"TensorAccessor">, i32
      verbatim "noc0.async_read_barrier();"
      verbatim "cb_ctarg_3.push_back({});" args %5 : i32
      verbatim "cb_ctarg_4.reserve_back({});" args %5 : i32
      %35 = call_opaque "get_common_arg_val"(%8) <{template_args = [#emitc.opaque<"uint32_t">]}> : (!emitc.size_t) -> i32
      verbatim "auto tensor_accessor_args_4 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<2, 8>(), 1>();"
      %36 = literal "tensor_accessor_args_4" : !emitc.opaque<"TensorAccessorArgs">
      %37 = call_opaque "TensorAccessor"(%36, %35, %3)  : (!emitc.opaque<"TensorAccessorArgs">, i32, i32) -> !emitc.opaque<"TensorAccessor">
      %38 = literal "cb_ctarg_4.get_write_ptr()" : i32
      verbatim "noc0.async_read({}, CoreLocalMem<uint32_t>({}), {}.get_aligned_page_size(), {{.page_id = static_cast<uint32_t>({})}, {{});" args %37, %38, %37, %2 : !emitc.opaque<"TensorAccessor">, i32, !emitc.opaque<"TensorAccessor">, i32
      verbatim "noc0.async_read_barrier();"
      verbatim "cb_ctarg_4.push_back({});" args %5 : i32
      verbatim "cb_ctarg_5.reserve_back({});" args %5 : i32
      verbatim "auto tensor_accessor_args_5 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<2, 8>(), 1>();"
      %39 = literal "tensor_accessor_args_5" : !emitc.opaque<"TensorAccessorArgs">
      %40 = call_opaque "TensorAccessor"(%39, %35, %3)  : (!emitc.opaque<"TensorAccessorArgs">, i32, i32) -> !emitc.opaque<"TensorAccessor">
      %41 = literal "cb_ctarg_5.get_write_ptr()" : i32
      verbatim "noc0.async_read({}, CoreLocalMem<uint32_t>({}), {}.get_aligned_page_size(), {{.page_id = static_cast<uint32_t>({})}, {{});" args %40, %41, %40, %5 : !emitc.opaque<"TensorAccessor">, i32, !emitc.opaque<"TensorAccessor">, i32
      verbatim "noc0.async_read_barrier();"
      verbatim "cb_ctarg_5.push_back({});" args %5 : i32
    }
    return
  }
  func.func @dm_write() attributes {fp32_dest_acc_en = true, ttkernel.arg_spec = #ttkernel.arg_spec< ct_args = [<arg_type = buffer_address, operand_index = 0>]>, ttkernel.thread = #ttkernel.thread<noc>, ttl.base_cta_index = 8 : i32, ttl.crta_indices = [3 : i32], ttl.enable_fpu_binary_ops = true} {
    emitc.verbatim "Noc noc1(1);"
    %0 = "emitc.constant"() <{value = 2 : index}> : () -> !emitc.size_t
    %1 = "emitc.constant"() <{value = 1 : i8}> : () -> i8
    %2 = "emitc.constant"() <{value = 0 : i32}> : () -> i32
    %3 = "emitc.constant"() <{value = 2048 : i32}> : () -> i32
    %4 = "emitc.constant"() <{value = 1 : i32}> : () -> i32
    %5 = "emitc.constant"() <{value = 1 : index}> : () -> !emitc.size_t
    %6 = "emitc.constant"() <{value = 0 : index}> : () -> !emitc.size_t
    %7 = "emitc.constant"() <{value = 32 : index}> : () -> !emitc.size_t
    %8 = emitc.literal "get_compile_time_arg_val(7)" {ttkernel.cb_ctarg_idx = 7 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_7({});" args %8 : ui32
    %9 = emitc.literal "get_compile_time_arg_val(6)" {ttkernel.cb_ctarg_idx = 6 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_6({});" args %9 : ui32
    emitc.for %arg0 = %6 to %7 step %5  : !emitc.size_t {
      verbatim "cb_ctarg_6.wait_front({});" args %4 : i32
      %10 = call_opaque "get_common_arg_val"(%6) <{template_args = [#emitc.opaque<"uint32_t">]}> : (!emitc.size_t) -> i32
      verbatim "auto tensor_accessor_args_0 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<3, 8>(), 0>();"
      %11 = literal "tensor_accessor_args_0" : !emitc.opaque<"TensorAccessorArgs">
      %12 = call_opaque "TensorAccessor"(%11, %10, %3)  : (!emitc.opaque<"TensorAccessorArgs">, i32, i32) -> !emitc.opaque<"TensorAccessor">
      %13 = literal "cb_ctarg_6.get_read_ptr()" : i32
      %14 = mul %arg0, %0 : (!emitc.size_t, !emitc.size_t) -> !emitc.size_t
      %15 = cast %14 : !emitc.size_t to !emitc.ptrdiff_t
      %16 = cast %15 : !emitc.ptrdiff_t to i32
      verbatim "noc1.async_write(CoreLocalMem<uint32_t>({}), {}, {}.get_aligned_page_size(), {{} , {{.page_id = static_cast<uint32_t>({})});" args %13, %12, %12, %16 : i32, !emitc.opaque<"TensorAccessor">, !emitc.opaque<"TensorAccessor">, i32
      verbatim "noc1.async_write_barrier();"
      verbatim "cb_ctarg_6.pop_front({});" args %4 : i32
      verbatim "cb_ctarg_7.wait_front({});" args %4 : i32
      verbatim "auto tensor_accessor_args_1 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<3, 8>(), 0>();"
      %17 = literal "tensor_accessor_args_1" : !emitc.opaque<"TensorAccessorArgs">
      %18 = call_opaque "TensorAccessor"(%17, %10, %3)  : (!emitc.opaque<"TensorAccessorArgs">, i32, i32) -> !emitc.opaque<"TensorAccessor">
      %19 = literal "cb_ctarg_7.get_read_ptr()" : i32
      %20 = add %14, %5 : (!emitc.size_t, !emitc.size_t) -> !emitc.size_t
      %21 = cast %20 : !emitc.size_t to !emitc.ptrdiff_t
      %22 = cast %21 : !emitc.ptrdiff_t to i32
      verbatim "noc1.async_write(CoreLocalMem<uint32_t>({}), {}, {}.get_aligned_page_size(), {{} , {{.page_id = static_cast<uint32_t>({})});" args %19, %18, %18, %22 : i32, !emitc.opaque<"TensorAccessor">, !emitc.opaque<"TensorAccessor">, i32
      verbatim "noc1.async_write_barrier();"
      verbatim "cb_ctarg_7.pop_front({});" args %4 : i32
    }
    return
  }
}
