module attributes {ttl.compiler_allocated_dfbs = [{block_count = 2 : i32, dfb_index = 10 : i32, element_type = !ttcore.tile<32x32, f32>, num_tiles = 1 : i32}, {block_count = 2 : i32, dfb_index = 11 : i32, element_type = !ttcore.tile<32x32, f32>, num_tiles = 1 : i32}], ttl.launch_grid = [1, 1], ttl.pipe_sync_semaphore_count = 0 : i64, ttl.target_arch = "blackhole"} {
  func.func @compute() attributes {dst_full_sync_en = true, fp32_dest_acc_en = true, ttkernel.thread = #ttkernel.thread<compute>, ttl.base_cta_index = 12 : i32, ttl.crta_indices = [], ttl.enable_fpu_binary_ops = true, ttl.unpack_to_dest_fp32 = array<i32: 2, 4, 7>} {
    %0 = "emitc.constant"() <{value = 9.99999974E-6 : f32}> : () -> f32
    %1 = "emitc.constant"() <{value = 1.000000e+00 : f32}> : () -> f32
    %2 = "emitc.constant"() <{value = 1 : i32}> : () -> i32
    %3 = "emitc.constant"() <{value = 64 : index}> : () -> !emitc.size_t
    %4 = "emitc.constant"() <{value = 63 : index}> : () -> !emitc.size_t
    %5 = "emitc.constant"() <{value = 1 : index}> : () -> !emitc.size_t
    %6 = "emitc.constant"() <{value = 0 : index}> : () -> !emitc.size_t
    %7 = emitc.literal "get_compile_time_arg_val(6)" {ttkernel.cb_ctarg_idx = 6 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_6({});" args %7 : ui32
    %8 = emitc.literal "get_compile_time_arg_val(8)" {ttkernel.cb_ctarg_idx = 8 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_8({});" args %8 : ui32
    %9 = emitc.literal "get_compile_time_arg_val(9)" {ttkernel.cb_ctarg_idx = 9 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_9({});" args %9 : ui32
    %10 = emitc.literal "get_compile_time_arg_val(5)" {ttkernel.cb_ctarg_idx = 5 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_5({});" args %10 : ui32
    %11 = emitc.literal "get_compile_time_arg_val(7)" {ttkernel.cb_ctarg_idx = 7 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_7({});" args %11 : ui32
    %12 = emitc.literal "get_compile_time_arg_val(2)" {ttkernel.cb_ctarg_idx = 2 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_2({});" args %12 : ui32
    %13 = emitc.literal "get_compile_time_arg_val(1)" {ttkernel.cb_ctarg_idx = 1 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_1({});" args %13 : ui32
    %14 = emitc.literal "get_compile_time_arg_val(4)" {ttkernel.cb_ctarg_idx = 4 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_4({});" args %14 : ui32
    %15 = emitc.literal "get_compile_time_arg_val(0)" {ttkernel.cb_ctarg_idx = 0 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_0({});" args %15 : ui32
    %16 = emitc.literal "get_compile_time_arg_val(3)" {ttkernel.cb_ctarg_idx = 3 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_3({});" args %16 : ui32
    %17 = emitc.literal "get_compile_time_arg_val(10)" {ttkernel.cb_ctarg_idx = 10 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_10({});" args %17 : ui32
    %18 = emitc.literal "get_compile_time_arg_val(11)" {ttkernel.cb_ctarg_idx = 11 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_11({});" args %18 : ui32
    emitc.verbatim "cb_ctarg_2.wait_front({});" args %2 : i32
    emitc.verbatim "cb_ctarg_0.wait_front({});" args %2 : i32
    emitc.verbatim "cb_ctarg_5.reserve_back({});" args %2 : i32
    emitc.verbatim "cb_ctarg_10.reserve_back({});" args %2 : i32
    emitc.call_opaque "init_sfpu"(%15, %17)  : (ui32, ui32) -> ()
    emitc.call_opaque "tile_regs_acquire"()  : () -> ()
    emitc.call_opaque "copy_tile_init"(%15)  : (ui32) -> ()
    emitc.call_opaque "copy_tile"(%15, %6, %6)  : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "typecast_tile_init"() <{template_args = [#emitc.opaque<"static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float16_b)">, #emitc.opaque<"static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float32)">]}> : () -> ()
    emitc.call_opaque "typecast_tile"(%6) <{template_args = [#emitc.opaque<"static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float16_b)">, #emitc.opaque<"static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float32)">]}> : (!emitc.size_t) -> ()
    emitc.call_opaque "mul_binary_tile_init"()  : () -> ()
    emitc.call_opaque "mul_binary_tile"(%6, %6, %6)  : (!emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_commit"()  : () -> ()
    emitc.call_opaque "tile_regs_wait"()  : () -> ()
    emitc.call_opaque "pack_tile"(%6, %17, %6) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_release"()  : () -> ()
    emitc.verbatim "cb_ctarg_10.push_back({});" args %2 : i32
    emitc.verbatim "cb_ctarg_10.wait_front({});" args %2 : i32
    emitc.verbatim "cb_ctarg_11.reserve_back({});" args %2 : i32
    emitc.call_opaque "init_sfpu"(%18, %18)  : (ui32, ui32) -> ()
    emitc.call_opaque "tile_regs_acquire"()  : () -> ()
    emitc.call_opaque "fill_tile_init"()  : () -> ()
    emitc.call_opaque "fill_tile"(%6, %1)  : (!emitc.size_t, f32) -> ()
    emitc.call_opaque "tile_regs_commit"()  : () -> ()
    emitc.call_opaque "tile_regs_wait"()  : () -> ()
    emitc.call_opaque "pack_tile"(%6, %18, %6) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_release"()  : () -> ()
    emitc.verbatim "cb_ctarg_11.push_back({});" args %2 : i32
    emitc.verbatim "cb_ctarg_11.wait_front({});" args %2 : i32
    emitc.call_opaque "init_sfpu"(%17, %10)  : (ui32, ui32) -> ()
    emitc.call_opaque "tile_regs_acquire"()  : () -> ()
    emitc.call_opaque "reduce_init"(%17, %18, %10) <{template_args = [#emitc.opaque<"PoolType::SUM">, #emitc.opaque<"ReduceDim::REDUCE_ROW">, #emitc.opaque<"false">]}> : (ui32, ui32, ui32) -> ()
    emitc.call_opaque "reduce_tile"(%17, %18, %6, %6, %6) <{template_args = [#emitc.opaque<"PoolType::SUM">, #emitc.opaque<"ReduceDim::REDUCE_ROW">, #emitc.opaque<"false">]}> : (ui32, ui32, !emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "reduce_uninit"()  : () -> ()
    emitc.call_opaque "tile_regs_commit"()  : () -> ()
    emitc.call_opaque "tile_regs_wait"()  : () -> ()
    emitc.call_opaque "pack_tile"(%6, %10, %6) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_release"()  : () -> ()
    emitc.verbatim "cb_ctarg_11.pop_front({});" args %2 : i32
    emitc.verbatim "cb_ctarg_10.pop_front({});" args %2 : i32
    emitc.verbatim "cb_ctarg_5.push_back({});" args %2 : i32
    emitc.verbatim "cb_ctarg_0.pop_front({});" args %2 : i32
    emitc.verbatim "cb_ctarg_5.wait_front({});" args %2 : i32
    emitc.verbatim "cb_ctarg_6.reserve_back({});" args %2 : i32
    emitc.call_opaque "init_sfpu"(%10, %7)  : (ui32, ui32) -> ()
    emitc.call_opaque "tile_regs_acquire"()  : () -> ()
    emitc.call_opaque "copy_tile_init"(%10)  : (ui32) -> ()
    emitc.call_opaque "copy_tile"(%10, %6, %6)  : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_commit"()  : () -> ()
    emitc.call_opaque "tile_regs_wait"()  : () -> ()
    emitc.call_opaque "pack_tile"(%6, %7, %6) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_release"()  : () -> ()
    emitc.verbatim "cb_ctarg_6.push_back({});" args %2 : i32
    emitc.verbatim "cb_ctarg_5.pop_front({});" args %2 : i32
    emitc.for %arg0 = %6 to %4 step %5  : !emitc.size_t {
      verbatim "cb_ctarg_0.wait_front({});" args %2 : i32
      verbatim "cb_ctarg_5.reserve_back({});" args %2 : i32
      verbatim "cb_ctarg_10.reserve_back({});" args %2 : i32
      call_opaque "init_sfpu"(%15, %17)  : (ui32, ui32) -> ()
      call_opaque "tile_regs_acquire"()  : () -> ()
      call_opaque "copy_tile_init"(%15)  : (ui32) -> ()
      call_opaque "copy_tile"(%15, %6, %6)  : (ui32, !emitc.size_t, !emitc.size_t) -> ()
      call_opaque "typecast_tile_init"() <{template_args = [#emitc.opaque<"static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float16_b)">, #emitc.opaque<"static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float32)">]}> : () -> ()
      call_opaque "typecast_tile"(%6) <{template_args = [#emitc.opaque<"static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float16_b)">, #emitc.opaque<"static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float32)">]}> : (!emitc.size_t) -> ()
      call_opaque "mul_binary_tile_init"()  : () -> ()
      call_opaque "mul_binary_tile"(%6, %6, %6)  : (!emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
      call_opaque "tile_regs_commit"()  : () -> ()
      call_opaque "tile_regs_wait"()  : () -> ()
      call_opaque "pack_tile"(%6, %17, %6) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
      call_opaque "tile_regs_release"()  : () -> ()
      verbatim "cb_ctarg_10.push_back({});" args %2 : i32
      verbatim "cb_ctarg_10.wait_front({});" args %2 : i32
      verbatim "cb_ctarg_11.reserve_back({});" args %2 : i32
      call_opaque "init_sfpu"(%18, %18)  : (ui32, ui32) -> ()
      call_opaque "tile_regs_acquire"()  : () -> ()
      call_opaque "fill_tile_init"()  : () -> ()
      call_opaque "fill_tile"(%6, %1)  : (!emitc.size_t, f32) -> ()
      call_opaque "tile_regs_commit"()  : () -> ()
      call_opaque "tile_regs_wait"()  : () -> ()
      call_opaque "pack_tile"(%6, %18, %6) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
      call_opaque "tile_regs_release"()  : () -> ()
      verbatim "cb_ctarg_11.push_back({});" args %2 : i32
      verbatim "cb_ctarg_11.wait_front({});" args %2 : i32
      call_opaque "init_sfpu"(%17, %10)  : (ui32, ui32) -> ()
      call_opaque "tile_regs_acquire"()  : () -> ()
      call_opaque "reduce_init"(%17, %18, %10) <{template_args = [#emitc.opaque<"PoolType::SUM">, #emitc.opaque<"ReduceDim::REDUCE_ROW">, #emitc.opaque<"false">]}> : (ui32, ui32, ui32) -> ()
      call_opaque "reduce_tile"(%17, %18, %6, %6, %6) <{template_args = [#emitc.opaque<"PoolType::SUM">, #emitc.opaque<"ReduceDim::REDUCE_ROW">, #emitc.opaque<"false">]}> : (ui32, ui32, !emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
      call_opaque "reduce_uninit"()  : () -> ()
      call_opaque "tile_regs_commit"()  : () -> ()
      call_opaque "tile_regs_wait"()  : () -> ()
      call_opaque "pack_tile"(%6, %10, %6) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
      call_opaque "tile_regs_release"()  : () -> ()
      verbatim "cb_ctarg_11.pop_front({});" args %2 : i32
      verbatim "cb_ctarg_10.pop_front({});" args %2 : i32
      verbatim "cb_ctarg_5.push_back({});" args %2 : i32
      verbatim "cb_ctarg_0.pop_front({});" args %2 : i32
      verbatim "cb_ctarg_5.wait_front({});" args %2 : i32
      verbatim "cb_ctarg_6.wait_front({});" args %2 : i32
      verbatim "cb_ctarg_6.reserve_back({});" args %2 : i32
      call_opaque "binary_op_init_common"(%7, %10, %7)  : (ui32, ui32, ui32) -> ()
      call_opaque "tile_regs_acquire"()  : () -> ()
      call_opaque "add_tiles_init"(%7, %10)  : (ui32, ui32) -> ()
      call_opaque "add_tiles"(%7, %10, %6, %6, %6)  : (ui32, ui32, !emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
      call_opaque "tile_regs_commit"()  : () -> ()
      call_opaque "tile_regs_wait"()  : () -> ()
      call_opaque "pack_tile"(%6, %7, %6) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
      call_opaque "tile_regs_release"()  : () -> ()
      verbatim "cb_ctarg_6.push_back({});" args %2 : i32
      verbatim "cb_ctarg_6.pop_front({});" args %2 : i32
      verbatim "cb_ctarg_5.pop_front({});" args %2 : i32
    }
    emitc.verbatim "cb_ctarg_6.wait_front({});" args %2 : i32
    emitc.verbatim "cb_ctarg_7.reserve_back({});" args %2 : i32
    emitc.call_opaque "init_sfpu"(%7, %11)  : (ui32, ui32) -> ()
    emitc.call_opaque "tile_regs_acquire"()  : () -> ()
    emitc.call_opaque "unary_bcast_init"(%7, %11) <{template_args = [#emitc.opaque<"BroadcastType::COL">]}> : (ui32, ui32) -> ()
    emitc.call_opaque "unary_bcast"(%7, %6, %6) <{template_args = [#emitc.opaque<"BroadcastType::COL">]}> : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "copy_tile_init"(%12)  : (ui32) -> ()
    emitc.call_opaque "copy_tile"(%12, %6, %5)  : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "mul_binary_tile_init"()  : () -> ()
    emitc.call_opaque "mul_binary_tile"(%6, %5, %6)  : (!emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "fill_tile_init"()  : () -> ()
    emitc.call_opaque "fill_tile"(%5, %0)  : (!emitc.size_t, f32) -> ()
    emitc.call_opaque "add_binary_tile_init"()  : () -> ()
    emitc.call_opaque "add_binary_tile"(%6, %5, %6)  : (!emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_commit"()  : () -> ()
    emitc.call_opaque "tile_regs_wait"()  : () -> ()
    emitc.call_opaque "pack_tile"(%6, %11, %6) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_release"()  : () -> ()
    emitc.verbatim "cb_ctarg_7.push_back({});" args %2 : i32
    emitc.verbatim "cb_ctarg_6.pop_front({});" args %2 : i32
    emitc.verbatim "cb_ctarg_7.wait_front({});" args %2 : i32
    emitc.verbatim "cb_ctarg_8.reserve_back({});" args %2 : i32
    emitc.call_opaque "init_sfpu"(%11, %8)  : (ui32, ui32) -> ()
    emitc.call_opaque "tile_regs_acquire"()  : () -> ()
    emitc.call_opaque "copy_tile_init"(%11)  : (ui32) -> ()
    emitc.call_opaque "copy_tile"(%11, %6, %6)  : (ui32, !emitc.size_t, !emitc.size_t) -> ()
    emitc.call_opaque "rsqrt_tile_init"()  : () -> ()
    emitc.call_opaque "rsqrt_tile"(%6)  : (!emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_commit"()  : () -> ()
    emitc.call_opaque "tile_regs_wait"()  : () -> ()
    emitc.call_opaque "pack_tile"(%6, %8, %6) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
    emitc.call_opaque "tile_regs_release"()  : () -> ()
    emitc.verbatim "cb_ctarg_8.push_back({});" args %2 : i32
    emitc.verbatim "cb_ctarg_7.pop_front({});" args %2 : i32
    emitc.verbatim "cb_ctarg_8.wait_front({});" args %2 : i32
    emitc.for %arg0 = %6 to %3 step %5  : !emitc.size_t {
      verbatim "cb_ctarg_0.wait_front({});" args %2 : i32
      verbatim "cb_ctarg_1.wait_front({});" args %2 : i32
      verbatim "cb_ctarg_3.reserve_back({});" args %2 : i32
      verbatim "cb_ctarg_4.reserve_back({});" args %2 : i32
      call_opaque "init_sfpu"(%15, %16)  : (ui32, ui32) -> ()
      call_opaque "tile_regs_acquire"()  : () -> ()
      call_opaque "copy_tile_init"(%15)  : (ui32) -> ()
      call_opaque "copy_tile"(%15, %6, %6)  : (ui32, !emitc.size_t, !emitc.size_t) -> ()
      call_opaque "typecast_tile_init"() <{template_args = [#emitc.opaque<"static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float16_b)">, #emitc.opaque<"static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float32)">]}> : () -> ()
      call_opaque "typecast_tile"(%6) <{template_args = [#emitc.opaque<"static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float16_b)">, #emitc.opaque<"static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float32)">]}> : (!emitc.size_t) -> ()
      call_opaque "tile_regs_commit"()  : () -> ()
      call_opaque "tile_regs_wait"()  : () -> ()
      call_opaque "pack_tile"(%6, %16, %6) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
      call_opaque "tile_regs_release"()  : () -> ()
      call_opaque "init_sfpu"(%13, %14)  : (ui32, ui32) -> ()
      call_opaque "tile_regs_acquire"()  : () -> ()
      call_opaque "copy_tile_init"(%13)  : (ui32) -> ()
      call_opaque "copy_tile"(%13, %6, %6)  : (ui32, !emitc.size_t, !emitc.size_t) -> ()
      call_opaque "typecast_tile_init"() <{template_args = [#emitc.opaque<"static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float16_b)">, #emitc.opaque<"static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float32)">]}> : () -> ()
      call_opaque "typecast_tile"(%6) <{template_args = [#emitc.opaque<"static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float16_b)">, #emitc.opaque<"static_cast<std::underlying_type_t<DataFormat>>(DataFormat::Float32)">]}> : (!emitc.size_t) -> ()
      call_opaque "tile_regs_commit"()  : () -> ()
      call_opaque "tile_regs_wait"()  : () -> ()
      call_opaque "pack_tile"(%6, %14, %6) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
      call_opaque "tile_regs_release"()  : () -> ()
      verbatim "cb_ctarg_4.push_back({});" args %2 : i32
      verbatim "cb_ctarg_3.push_back({});" args %2 : i32
      verbatim "cb_ctarg_1.pop_front({});" args %2 : i32
      verbatim "cb_ctarg_0.pop_front({});" args %2 : i32
      verbatim "cb_ctarg_3.wait_front({});" args %2 : i32
      verbatim "cb_ctarg_4.wait_front({});" args %2 : i32
      verbatim "cb_ctarg_9.reserve_back({});" args %2 : i32
      call_opaque "binary_op_init_common"(%16, %8, %9)  : (ui32, ui32, ui32) -> ()
      call_opaque "tile_regs_acquire"()  : () -> ()
      call_opaque "copy_tile_init"(%14)  : (ui32) -> ()
      call_opaque "copy_tile"(%14, %6, %5)  : (ui32, !emitc.size_t, !emitc.size_t) -> ()
      call_opaque "mul_tiles_init"(%16, %8)  : (ui32, ui32) -> ()
      call_opaque "mul_tiles"(%16, %8, %6, %6, %6)  : (ui32, ui32, !emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
      call_opaque "mul_binary_tile_init"()  : () -> ()
      call_opaque "mul_binary_tile"(%6, %5, %6)  : (!emitc.size_t, !emitc.size_t, !emitc.size_t) -> ()
      call_opaque "tile_regs_commit"()  : () -> ()
      call_opaque "tile_regs_wait"()  : () -> ()
      call_opaque "pack_tile"(%6, %9, %6) <{template_args = [true]}> : (!emitc.size_t, ui32, !emitc.size_t) -> ()
      call_opaque "tile_regs_release"()  : () -> ()
      verbatim "cb_ctarg_9.push_back({});" args %2 : i32
      verbatim "cb_ctarg_4.pop_front({});" args %2 : i32
      verbatim "cb_ctarg_3.pop_front({});" args %2 : i32
    }
    emitc.verbatim "cb_ctarg_8.pop_front({});" args %2 : i32
    emitc.verbatim "cb_ctarg_2.pop_front({});" args %2 : i32
    return
  }
  func.func @dm_read() attributes {dst_full_sync_en = true, fp32_dest_acc_en = true, ttkernel.arg_spec = #ttkernel.arg_spec< ct_args = [<arg_type = buffer_address, operand_index = 0>, <arg_type = buffer_address, operand_index = 1>, <arg_type = buffer_address, operand_index = 2>]>, ttkernel.thread = #ttkernel.thread<noc>, ttl.base_cta_index = 12 : i32, ttl.crta_indices = [2 : i32, 1 : i32, 0 : i32], ttl.enable_fpu_binary_ops = true} {
    emitc.verbatim "Noc noc0(0);"
    %0 = "emitc.constant"() <{value = 2 : i32}> : () -> i32
    %1 = "emitc.constant"() <{value = 2048 : i32}> : () -> i32
    %2 = "emitc.constant"() <{value = 2 : index}> : () -> !emitc.size_t
    %3 = "emitc.constant"() <{value = 0 : i8}> : () -> i8
    %4 = "emitc.constant"() <{value = 0 : i32}> : () -> i32
    %5 = "emitc.constant"() <{value = 4096 : i32}> : () -> i32
    %6 = "emitc.constant"() <{value = 1 : i32}> : () -> i32
    %7 = "emitc.constant"() <{value = 64 : index}> : () -> !emitc.size_t
    %8 = "emitc.constant"() <{value = 1 : index}> : () -> !emitc.size_t
    %9 = "emitc.constant"() <{value = 0 : index}> : () -> !emitc.size_t
    %10 = emitc.literal "get_compile_time_arg_val(2)" {ttkernel.cb_ctarg_idx = 2 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_2({});" args %10 : ui32
    %11 = emitc.literal "get_compile_time_arg_val(1)" {ttkernel.cb_ctarg_idx = 1 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_1({});" args %11 : ui32
    %12 = emitc.literal "get_compile_time_arg_val(0)" {ttkernel.cb_ctarg_idx = 0 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_0({});" args %12 : ui32
    emitc.verbatim "cb_ctarg_2.reserve_back({});" args %6 : i32
    %13 = emitc.call_opaque "get_common_arg_val"(%9) <{template_args = [#emitc.opaque<"uint32_t">]}> : (!emitc.size_t) -> i32
    emitc.verbatim "auto tensor_accessor_args_0 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<2, 12>(), 0>();"
    %14 = emitc.literal "tensor_accessor_args_0" : !emitc.opaque<"TensorAccessorArgs">
    %15 = emitc.call_opaque "TensorAccessor"(%14, %13, %5)  : (!emitc.opaque<"TensorAccessorArgs">, i32, i32) -> !emitc.opaque<"TensorAccessor">
    %16 = emitc.literal "cb_ctarg_2.get_write_ptr()" : i32
    emitc.verbatim "noc0.async_read({}, CoreLocalMem<uint32_t>({}), {}.get_aligned_page_size(), {{.page_id = static_cast<uint32_t>({})}, {{});" args %15, %16, %15, %4 : !emitc.opaque<"TensorAccessor">, i32, !emitc.opaque<"TensorAccessor">, i32
    emitc.verbatim "noc0.async_read_barrier();"
    emitc.verbatim "cb_ctarg_2.push_back({});" args %6 : i32
    emitc.for %arg0 = %9 to %7 step %8  : !emitc.size_t {
      verbatim "cb_ctarg_0.reserve_back({});" args %6 : i32
      %17 = call_opaque "get_common_arg_val"(%2) <{template_args = [#emitc.opaque<"uint32_t">]}> : (!emitc.size_t) -> i32
      verbatim "auto tensor_accessor_args_1 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<0, 12>(), 2>();"
      %18 = literal "tensor_accessor_args_1" : !emitc.opaque<"TensorAccessorArgs">
      %19 = call_opaque "TensorAccessor"(%18, %17, %1)  : (!emitc.opaque<"TensorAccessorArgs">, i32, i32) -> !emitc.opaque<"TensorAccessor">
      %20 = literal "cb_ctarg_0.get_write_ptr()" : i32
      %21 = cast %arg0 : !emitc.size_t to !emitc.ptrdiff_t
      %22 = cast %21 : !emitc.ptrdiff_t to i32
      verbatim "noc0.async_read({}, CoreLocalMem<uint32_t>({}), {}.get_aligned_page_size(), {{.page_id = static_cast<uint32_t>({})}, {{});" args %19, %20, %19, %22 : !emitc.opaque<"TensorAccessor">, i32, !emitc.opaque<"TensorAccessor">, i32
      verbatim "noc0.async_read_barrier();"
      verbatim "cb_ctarg_0.push_back({});" args %6 : i32
    }
    emitc.for %arg0 = %9 to %7 step %8  : !emitc.size_t {
      verbatim "cb_ctarg_0.reserve_back({});" args %6 : i32
      %17 = call_opaque "get_common_arg_val"(%2) <{template_args = [#emitc.opaque<"uint32_t">]}> : (!emitc.size_t) -> i32
      verbatim "auto tensor_accessor_args_2 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<0, 12>(), 2>();"
      %18 = literal "tensor_accessor_args_2" : !emitc.opaque<"TensorAccessorArgs">
      %19 = call_opaque "TensorAccessor"(%18, %17, %1)  : (!emitc.opaque<"TensorAccessorArgs">, i32, i32) -> !emitc.opaque<"TensorAccessor">
      %20 = literal "cb_ctarg_0.get_write_ptr()" : i32
      %21 = cast %arg0 : !emitc.size_t to !emitc.ptrdiff_t
      %22 = cast %21 : !emitc.ptrdiff_t to i32
      verbatim "noc0.async_read({}, CoreLocalMem<uint32_t>({}), {}.get_aligned_page_size(), {{.page_id = static_cast<uint32_t>({})}, {{});" args %19, %20, %19, %22 : !emitc.opaque<"TensorAccessor">, i32, !emitc.opaque<"TensorAccessor">, i32
      verbatim "noc0.async_read_barrier();"
      verbatim "cb_ctarg_0.push_back({});" args %6 : i32
      verbatim "cb_ctarg_1.reserve_back({});" args %6 : i32
      %23 = call_opaque "get_common_arg_val"(%8) <{template_args = [#emitc.opaque<"uint32_t">]}> : (!emitc.size_t) -> i32
      verbatim "auto tensor_accessor_args_3 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<1, 12>(), 1>();"
      %24 = literal "tensor_accessor_args_3" : !emitc.opaque<"TensorAccessorArgs">
      %25 = call_opaque "TensorAccessor"(%24, %23, %1)  : (!emitc.opaque<"TensorAccessorArgs">, i32, i32) -> !emitc.opaque<"TensorAccessor">
      %26 = literal "cb_ctarg_1.get_write_ptr()" : i32
      verbatim "noc0.async_read({}, CoreLocalMem<uint32_t>({}), {}.get_aligned_page_size(), {{.page_id = static_cast<uint32_t>({})}, {{});" args %25, %26, %25, %22 : !emitc.opaque<"TensorAccessor">, i32, !emitc.opaque<"TensorAccessor">, i32
      verbatim "noc0.async_read_barrier();"
      verbatim "cb_ctarg_1.push_back({});" args %6 : i32
    }
    return
  }
  func.func @dm_write() attributes {dst_full_sync_en = true, fp32_dest_acc_en = true, ttkernel.arg_spec = #ttkernel.arg_spec< ct_args = [<arg_type = buffer_address, operand_index = 0>]>, ttkernel.thread = #ttkernel.thread<noc>, ttl.base_cta_index = 12 : i32, ttl.crta_indices = [3 : i32], ttl.enable_fpu_binary_ops = true} {
    emitc.verbatim "Noc noc1(1);"
    %0 = "emitc.constant"() <{value = 1 : i8}> : () -> i8
    %1 = "emitc.constant"() <{value = 0 : i32}> : () -> i32
    %2 = "emitc.constant"() <{value = 4096 : i32}> : () -> i32
    %3 = "emitc.constant"() <{value = 1 : i32}> : () -> i32
    %4 = "emitc.constant"() <{value = 64 : index}> : () -> !emitc.size_t
    %5 = "emitc.constant"() <{value = 1 : index}> : () -> !emitc.size_t
    %6 = "emitc.constant"() <{value = 0 : index}> : () -> !emitc.size_t
    %7 = emitc.literal "get_compile_time_arg_val(9)" {ttkernel.cb_ctarg_idx = 9 : i32} : ui32
    emitc.verbatim "CircularBuffer cb_ctarg_9({});" args %7 : ui32
    emitc.for %arg0 = %6 to %4 step %5  : !emitc.size_t {
      verbatim "cb_ctarg_9.wait_front({});" args %3 : i32
      %8 = call_opaque "get_common_arg_val"(%6) <{template_args = [#emitc.opaque<"uint32_t">]}> : (!emitc.size_t) -> i32
      verbatim "auto tensor_accessor_args_0 = TensorAccessorArgs<tensor_accessor::detail::get_tensor_accessor_args_cta_offset<3, 12>(), 0>();"
      %9 = literal "tensor_accessor_args_0" : !emitc.opaque<"TensorAccessorArgs">
      %10 = call_opaque "TensorAccessor"(%9, %8, %2)  : (!emitc.opaque<"TensorAccessorArgs">, i32, i32) -> !emitc.opaque<"TensorAccessor">
      %11 = literal "cb_ctarg_9.get_read_ptr()" : i32
      %12 = cast %arg0 : !emitc.size_t to !emitc.ptrdiff_t
      %13 = cast %12 : !emitc.ptrdiff_t to i32
      verbatim "noc1.async_write(CoreLocalMem<uint32_t>({}), {}, {}.get_aligned_page_size(), {{} , {{.page_id = static_cast<uint32_t>({})});" args %11, %10, %10, %13 : i32, !emitc.opaque<"TensorAccessor">, !emitc.opaque<"TensorAccessor">, i32
      verbatim "noc1.async_write_barrier();"
      verbatim "cb_ctarg_9.pop_front({});" args %3 : i32
    }
    return
  }
}
