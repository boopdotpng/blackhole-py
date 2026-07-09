module attributes {ttl.compiler_allocated_dfbs = [{block_count = 2 : i32, dfb_index = 3 : i32, element_type = !ttcore.tile<32x32, f32>, num_tiles = 1 : i32}, {block_count = 2 : i32, dfb_index = 4 : i32, element_type = !ttcore.tile<32x32, f32>, num_tiles = 1 : i32}, {block_count = 2 : i32, dfb_index = 5 : i32, element_type = !ttcore.tile<32x32, f32>, num_tiles = 1 : i32}, {block_count = 2 : i32, dfb_index = 6 : i32, element_type = !ttcore.tile<32x32, f32>, num_tiles = 4 : i32}], ttl.launch_grid = [1, 1], ttl.pipe_sync_semaphore_count = 0 : i64, ttl.target_arch = "blackhole"} {
  func.func @compute() attributes {dst_full_sync_en = true, fp32_dest_acc_en = true, ttkernel.thread = #ttkernel.thread<compute>, ttl.base_cta_index = 7 : i32, ttl.crta_indices = [], ttl.enable_fpu_binary_ops = true, ttl.unpack_to_dest_fp32 = array<i32: 1>} {
    %0 = "emitc.constant"() <{value = 1.000000e+00 : f32}> : () -> f32
    %1 = "emitc.constant"() <{value = 7 : index}> : () -> !emitc.size_t
    %2 = "emitc.constant"() <{value = 6 : index}> : () -> !emitc.size_t
    %3 = "emitc.constant"() <{value = 5 : index}> : () -> !emitc.size_t
    %4 = "emitc.constant"() <{value = 3 : index}> : () -> !emitc.size_t
    %5 = "emitc.constant"() <{value = 2 : index}> : () -> !emitc.size_t
    %6 = "emitc.constant"() <{value = 1 : i32}> : () -> i32
    %7 = "emitc.constant"() <{value = 4 : i32}> : () -> i32
    %8 = "emitc.constant"() <{value = 4 : index}> : () -> !emitc.size_t
    %9 = "emitc.constant"() <{value = 1 : index}> : () -> !emitc.size_t
    %10 = "emitc.constant"() <{value = 0 : index}> : () -> !emitc.size_t
    %11 = emitc.literal "get_compile_time_arg_val(2)" {ttkernel.cb_ctarg_idx = 2 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_2({});" args %11 : ui32
    %12 = emitc.literal "get_compile_time_arg_val(0)" {ttkernel.cb_ctarg_idx = 0 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_0({});" args %12 : ui32
    %13 = emitc.literal "get_compile_time_arg_val(1)" {ttkernel.cb_ctarg_idx = 1 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_1({});" args %13 : ui32
    %14 = emitc.literal "get_compile_time_arg_val(3)" {ttkernel.cb_ctarg_idx = 3 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_3({});" args %14 : ui32
    %15 = emitc.literal "get_compile_time_arg_val(4)" {ttkernel.cb_ctarg_idx = 4 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_4({});" args %15 : ui32
    %16 = emitc.literal "get_compile_time_arg_val(6)" {ttkernel.cb_ctarg_idx = 6 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_6({});" args %16 : ui32
    %17 = emitc.literal "get_compile_time_arg_val(5)" {ttkernel.cb_ctarg_idx = 5 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_5({});" args %17 : ui32
    emitc.verbatim "cb_ctarg_0.wait_front({});" args %7 : i32
    emitc.verbatim "cb_ctarg_1.wait_front({});" args %7 : i32
    emitc.verbatim "cb_ctarg_3.reserve_back({});" args %6 : i32
    emitc.call_opaque "init_sfpu"(%14, %14)  : (ui32, ui32) -> ()
    emitc.call_opaque "tile_regs_acquire"()  : () -> ()
    emitc.call_opaque "fill_tile_init"()  : () -> ()
    emitc.call_opaque "fill_tile"(%10, %0)  : (!emitc.size_t, f32) -> ()
    emitc.call_opaque "tile_regs_commit"()  : () -> ()
    emitc.call_opaque "tile_regs_wait"()  : () -> ()
    emitc.call_opaque "pack_tile"(%10, %14, %10) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_release"()  : () -> ()
    emitc.verbatim "cb_ctarg_3.push_back({});" args %6 : i32
    emitc.verbatim "cb_ctarg_3.wait_front({});" args %6 : i32
    emitc.verbatim "cb_ctarg_4.reserve_back({});" args %6 : i32
    emitc.call_opaque "init_sfpu"(%12, %15)  : (ui32, ui32) -> ()
    emitc.call_opaque "tile_regs_acquire"()  : () -> ()
    emitc.call_opaque "reduce_init"(%12, %14, %15) <{template_args = [#emitc.opaque<"PoolType::MAX">, #emitc.opaque<"ReduceDim::REDUCE_ROW">, #emitc.opaque<"false">]}> : (ui32, ui32, ui32) -> ()
    emitc.for %arg0 = %10 to %8 step %9  : !emitc.size_t {
      call_opaque "reduce_tile"(%12, %14, %arg0, %10, %10) <{template_args = [#emitc.opaque<"PoolType::MAX">, #emitc.opaque<"ReduceDim::REDUCE_ROW">, #emitc.opaque<"false">]}> : (ui32, ui32, !emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
    }
    emitc.call_opaque "reduce_uninit"()  : () -> ()
    emitc.call_opaque "tile_regs_commit"()  : () -> ()
    emitc.call_opaque "tile_regs_wait"()  : () -> ()
    emitc.call_opaque "pack_tile"(%10, %15, %10) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_release"()  : () -> ()
    emitc.verbatim "cb_ctarg_3.pop_front({});" args %6 : i32
    emitc.verbatim "cb_ctarg_4.push_back({});" args %6 : i32
    emitc.verbatim "cb_ctarg_4.wait_front({});" args %6 : i32
    emitc.verbatim "cb_ctarg_6.reserve_back({});" args %7 : i32
    emitc.call_opaque "init_sfpu"(%15, %16)  : (ui32, ui32) -> ()
    emitc.call_opaque "tile_regs_acquire"()  : () -> ()
    emitc.call_opaque "unary_bcast_init"(%15, %16) <{template_args = [#emitc.opaque<"BroadcastType::COL">]}> : (ui32, ui32) -> ()
    emitc.call_opaque "unary_bcast"(%15, %10, %10) <{template_args = [#emitc.opaque<"BroadcastType::COL">]}> : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "unary_bcast"(%15, %10, %5) <{template_args = [#emitc.opaque<"BroadcastType::COL">]}> : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "unary_bcast"(%15, %10, %8) <{template_args = [#emitc.opaque<"BroadcastType::COL">]}> : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "unary_bcast"(%15, %10, %2) <{template_args = [#emitc.opaque<"BroadcastType::COL">]}> : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "copy_tile_init"(%13)  : (ui32) -> ()
    emitc.call_opaque "copy_tile"(%13, %10, %9)  : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "copy_tile"(%13, %9, %4)  : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "copy_tile"(%13, %5, %3)  : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "copy_tile"(%13, %4, %1)  : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "sub_binary_tile_init"()  : () -> ()
    emitc.call_opaque "sub_binary_tile"(%9, %10, %10)  : (!emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "sub_binary_tile"(%4, %5, %5)  : (!emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "sub_binary_tile"(%3, %8, %8)  : (!emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "sub_binary_tile"(%1, %2, %2)  : (!emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "exp_tile_init"()  : () -> ()
    emitc.call_opaque "exp_tile"(%10)  : (!emitc.size_t) -> ()
    emitc.call_opaque "exp_tile"(%5)  : (!emitc.size_t) -> ()
    emitc.call_opaque "exp_tile"(%8)  : (!emitc.size_t) -> ()
    emitc.call_opaque "exp_tile"(%2)  : (!emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_commit"()  : () -> ()
    emitc.call_opaque "tile_regs_wait"()  : () -> ()
    emitc.call_opaque "pack_tile"(%10, %16, %10) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "pack_tile"(%5, %16, %9) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "pack_tile"(%8, %16, %5) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "pack_tile"(%2, %16, %4) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_release"()  : () -> ()
    emitc.verbatim "cb_ctarg_6.push_back({});" args %7 : i32
    emitc.verbatim "cb_ctarg_6.wait_front({});" args %7 : i32
    emitc.verbatim "cb_ctarg_3.reserve_back({});" args %6 : i32
    emitc.call_opaque "init_sfpu"(%14, %14)  : (ui32, ui32) -> ()
    emitc.call_opaque "tile_regs_acquire"()  : () -> ()
    emitc.call_opaque "fill_tile_init"()  : () -> ()
    emitc.call_opaque "fill_tile"(%10, %0)  : (!emitc.size_t, f32) -> ()
    emitc.call_opaque "tile_regs_commit"()  : () -> ()
    emitc.call_opaque "tile_regs_wait"()  : () -> ()
    emitc.call_opaque "pack_tile"(%10, %14, %10) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_release"()  : () -> ()
    emitc.verbatim "cb_ctarg_3.push_back({});" args %6 : i32
    emitc.verbatim "cb_ctarg_3.wait_front({});" args %6 : i32
    emitc.verbatim "cb_ctarg_5.reserve_back({});" args %6 : i32
    emitc.call_opaque "init_sfpu"(%16, %17)  : (ui32, ui32) -> ()
    emitc.call_opaque "tile_regs_acquire"()  : () -> ()
    emitc.call_opaque "reduce_init"(%16, %14, %17) <{template_args = [#emitc.opaque<"PoolType::SUM">, #emitc.opaque<"ReduceDim::REDUCE_ROW">, #emitc.opaque<"false">]}> : (ui32, ui32, ui32) -> ()
    emitc.for %arg0 = %10 to %8 step %9  : !emitc.size_t {
      call_opaque "reduce_tile"(%16, %14, %arg0, %10, %10) <{template_args = [#emitc.opaque<"PoolType::SUM">, #emitc.opaque<"ReduceDim::REDUCE_ROW">, #emitc.opaque<"false">]}> : (ui32, ui32, !emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
    }
    emitc.call_opaque "reduce_uninit"()  : () -> ()
    emitc.call_opaque "tile_regs_commit"()  : () -> ()
    emitc.call_opaque "tile_regs_wait"()  : () -> ()
    emitc.call_opaque "pack_tile"(%10, %17, %10) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_release"()  : () -> ()
    emitc.verbatim "cb_ctarg_3.pop_front({});" args %6 : i32
    emitc.verbatim "cb_ctarg_6.pop_front({});" args %7 : i32
    emitc.verbatim "cb_ctarg_5.push_back({});" args %6 : i32
    emitc.verbatim "cb_ctarg_5.wait_front({});" args %6 : i32
    emitc.verbatim "cb_ctarg_2.reserve_back({});" args %7 : i32
    emitc.call_opaque "init_sfpu"(%15, %11)  : (ui32, ui32) -> ()
    emitc.call_opaque "tile_regs_acquire"()  : () -> ()
    emitc.call_opaque "unary_bcast_init"(%15, %11) <{template_args = [#emitc.opaque<"BroadcastType::COL">]}> : (ui32, ui32) -> ()
    emitc.call_opaque "unary_bcast"(%15, %10, %10) <{template_args = [#emitc.opaque<"BroadcastType::COL">]}> : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "unary_bcast"(%15, %10, %5) <{template_args = [#emitc.opaque<"BroadcastType::COL">]}> : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "unary_bcast"(%15, %10, %8) <{template_args = [#emitc.opaque<"BroadcastType::COL">]}> : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "unary_bcast"(%15, %10, %2) <{template_args = [#emitc.opaque<"BroadcastType::COL">]}> : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "copy_tile_init"(%13)  : (ui32) -> ()
    emitc.call_opaque "copy_tile"(%13, %10, %9)  : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "copy_tile"(%13, %9, %4)  : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "copy_tile"(%13, %5, %3)  : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "copy_tile"(%13, %4, %1)  : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "sub_binary_tile_init"()  : () -> ()
    emitc.call_opaque "sub_binary_tile"(%9, %10, %10)  : (!emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "sub_binary_tile"(%4, %5, %5)  : (!emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "sub_binary_tile"(%3, %8, %8)  : (!emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "sub_binary_tile"(%1, %2, %2)  : (!emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "unary_bcast_init"(%17, %11) <{template_args = [#emitc.opaque<"BroadcastType::COL">]}> : (ui32, ui32) -> ()
    emitc.call_opaque "unary_bcast"(%17, %10, %9) <{template_args = [#emitc.opaque<"BroadcastType::COL">]}> : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "unary_bcast"(%17, %10, %4) <{template_args = [#emitc.opaque<"BroadcastType::COL">]}> : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "unary_bcast"(%17, %10, %3) <{template_args = [#emitc.opaque<"BroadcastType::COL">]}> : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "unary_bcast"(%17, %10, %1) <{template_args = [#emitc.opaque<"BroadcastType::COL">]}> : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "exp_tile_init"()  : () -> ()
    emitc.call_opaque "exp_tile"(%10)  : (!emitc.size_t) -> ()
    emitc.call_opaque "exp_tile"(%5)  : (!emitc.size_t) -> ()
    emitc.call_opaque "exp_tile"(%8)  : (!emitc.size_t) -> ()
    emitc.call_opaque "exp_tile"(%2)  : (!emitc.size_t) -> ()
    emitc.call_opaque "recip_tile_init"()  : () -> ()
    emitc.call_opaque "recip_tile"(%9)  : (!emitc.size_t) -> ()
    emitc.call_opaque "recip_tile"(%4)  : (!emitc.size_t) -> ()
    emitc.call_opaque "recip_tile"(%3)  : (!emitc.size_t) -> ()
    emitc.call_opaque "recip_tile"(%1)  : (!emitc.size_t) -> ()
    emitc.call_opaque "mul_binary_tile_init"()  : () -> ()
    emitc.call_opaque "mul_binary_tile"(%10, %9, %10)  : (!emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "mul_binary_tile"(%5, %4, %5)  : (!emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "mul_binary_tile"(%8, %3, %8)  : (!emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "mul_binary_tile"(%2, %1, %2)  : (!emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_commit"()  : () -> ()
    emitc.call_opaque "tile_regs_wait"()  : () -> ()
    emitc.call_opaque "pack_tile"(%10, %11, %10) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "pack_tile"(%5, %11, %9) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "pack_tile"(%8, %11, %5) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "pack_tile"(%2, %11, %4) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_release"()  : () -> ()
    emitc.verbatim "cb_ctarg_5.pop_front({});" args %6 : i32
    emitc.verbatim "cb_ctarg_4.pop_front({});" args %6 : i32
    emitc.verbatim "cb_ctarg_2.push_back({});" args %7 : i32
    emitc.verbatim "cb_ctarg_1.pop_front({});" args %7 : i32
    emitc.verbatim "cb_ctarg_0.pop_front({});" args %7 : i32
    return
  }
  func.func @dm_read() attributes {dst_full_sync_en = true, fp32_dest_acc_en = true, ttkernel.arg_spec = #ttkernel.arg_spec< ct_args = [<arg_type = buffer_address, operand_index = 0>]>, ttkernel.thread = #ttkernel.thread<noc>, ttl.base_cta_index = 7 : i32, ttl.crta_indices = [0 : i32], ttl.enable_fpu_binary_ops = true} {
    emitc.verbatim "Noc noc0(0);"
    %0 = "emitc.constant"() <{value = 4 : index}> : () -> !emitc.size_t
    %1 = "emitc.constant"() <{value = 1 : index}> : () -> !emitc.size_t
    %2 = "emitc.constant"() <{value = 0 : i8}> : () -> i8
    %3 = "emitc.constant"() <{value = 4096 : index}> : () -> !emitc.size_t
    %4 = "emitc.constant"() <{value = 0 : i32}> : () -> i32
    %5 = "emitc.constant"() <{value = 4096 : i32}> : () -> i32
    %6 = "emitc.constant"() <{value = 4 : i32}> : () -> i32
    %7 = "emitc.constant"() <{value = 0 : index}> : () -> !emitc.size_t
    %8 = emitc.literal "get_compile_time_arg_val(0)" {ttkernel.cb_ctarg_idx = 0 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_0({});" args %8 : ui32
    %9 = emitc.literal "get_compile_time_arg_val(1)" {ttkernel.cb_ctarg_idx = 1 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_1({});" args %9 : ui32
    emitc.verbatim "cb_ctarg_0.reserve_back({});" args %6 : i32
    emitc.verbatim "cb_ctarg_1.reserve_back({});" args %6 : i32
    %10 = emitc.call_opaque "get_common_arg_val"(%7) <{template_args = [#emitc.opaque<"uint32_t">]}> : (!emitc.size_t) -> i32
    emitc.verbatim "auto tensor_accessor_args_0 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<0, 7>(), 0>();"
    %11 = emitc.literal "tensor_accessor_args_0" : !emitc.opaque<"TensorAccessorArgs">
    %12 = emitc.call_opaque "TensorAccessor"(%11, %10, %5)  : (!emitc.opaque<"TensorAccessorArgs">, i32, i32) -> !emitc.opaque<"TensorAccessor">
    %13 = emitc.literal "cb_ctarg_0.get_write_ptr()" : i32
    %14 = emitc.cast %13 : i32 to !emitc.ptrdiff_t
    %15 = emitc.cast %14 : !emitc.ptrdiff_t to !emitc.size_t
    emitc.for %arg0 = %7 to %0 step %1  : !emitc.size_t {
      %21 = mul %arg0, %3 : (!emitc.size_t, !emitc.size_t) -> !emitc.size_t
      %22 = add %15, %21 : (!emitc.size_t, !emitc.size_t) -> !emitc.size_t
      %23 = cast %arg0 : !emitc.size_t to !emitc.ptrdiff_t
      %24 = cast %23 : !emitc.ptrdiff_t to i32
      %25 = cast %22 : !emitc.size_t to !emitc.ptrdiff_t
      %26 = cast %25 : !emitc.ptrdiff_t to i32
      verbatim "noc0.async_read({}, CoreLocalMem<uint32_t>({}), {}.get_aligned_page_size(), {{.page_id = static_cast<uint32_t>({})}, {{});" args %12, %26, %12, %24 : !emitc.opaque<"TensorAccessor">, i32, !emitc.opaque<"TensorAccessor">, i32
    }
    emitc.verbatim "noc0.async_read_barrier();"
    emitc.verbatim "auto tensor_accessor_args_1 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<0, 7>(), 0>();"
    %16 = emitc.literal "tensor_accessor_args_1" : !emitc.opaque<"TensorAccessorArgs">
    %17 = emitc.call_opaque "TensorAccessor"(%16, %10, %5)  : (!emitc.opaque<"TensorAccessorArgs">, i32, i32) -> !emitc.opaque<"TensorAccessor">
    %18 = emitc.literal "cb_ctarg_1.get_write_ptr()" : i32
    %19 = emitc.cast %18 : i32 to !emitc.ptrdiff_t
    %20 = emitc.cast %19 : !emitc.ptrdiff_t to !emitc.size_t
    emitc.for %arg0 = %7 to %0 step %1  : !emitc.size_t {
      %21 = mul %arg0, %3 : (!emitc.size_t, !emitc.size_t) -> !emitc.size_t
      %22 = add %20, %21 : (!emitc.size_t, !emitc.size_t) -> !emitc.size_t
      %23 = cast %arg0 : !emitc.size_t to !emitc.ptrdiff_t
      %24 = cast %23 : !emitc.ptrdiff_t to i32
      %25 = cast %22 : !emitc.size_t to !emitc.ptrdiff_t
      %26 = cast %25 : !emitc.ptrdiff_t to i32
      verbatim "noc0.async_read({}, CoreLocalMem<uint32_t>({}), {}.get_aligned_page_size(), {{.page_id = static_cast<uint32_t>({})}, {{});" args %17, %26, %17, %24 : !emitc.opaque<"TensorAccessor">, i32, !emitc.opaque<"TensorAccessor">, i32
    }
    emitc.verbatim "noc0.async_read_barrier();"
    emitc.verbatim "cb_ctarg_1.push_back({});" args %6 : i32
    emitc.verbatim "cb_ctarg_0.push_back({});" args %6 : i32
    return
  }
  func.func @dm_write() attributes {dst_full_sync_en = true, fp32_dest_acc_en = true, ttkernel.arg_spec = #ttkernel.arg_spec< ct_args = [<arg_type = buffer_address, operand_index = 0>]>, ttkernel.thread = #ttkernel.thread<noc>, ttl.base_cta_index = 7 : i32, ttl.crta_indices = [1 : i32], ttl.enable_fpu_binary_ops = true} {
    emitc.verbatim "Noc noc1(1);"
    %0 = "emitc.constant"() <{value = 4 : index}> : () -> !emitc.size_t
    %1 = "emitc.constant"() <{value = 1 : index}> : () -> !emitc.size_t
    %2 = "emitc.constant"() <{value = 1 : i8}> : () -> i8
    %3 = "emitc.constant"() <{value = 4096 : index}> : () -> !emitc.size_t
    %4 = "emitc.constant"() <{value = 0 : i32}> : () -> i32
    %5 = "emitc.constant"() <{value = 4096 : i32}> : () -> i32
    %6 = "emitc.constant"() <{value = 4 : i32}> : () -> i32
    %7 = "emitc.constant"() <{value = 0 : index}> : () -> !emitc.size_t
    %8 = emitc.literal "get_compile_time_arg_val(2)" {ttkernel.cb_ctarg_idx = 2 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_2({});" args %8 : ui32
    emitc.verbatim "cb_ctarg_2.wait_front({});" args %6 : i32
    %9 = emitc.call_opaque "get_common_arg_val"(%7) <{template_args = [#emitc.opaque<"uint32_t">]}> : (!emitc.size_t) -> i32
    emitc.verbatim "auto tensor_accessor_args_0 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<1, 7>(), 0>();"
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
