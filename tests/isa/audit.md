# Tensix behavioral coverage audit

66 / 137 instructions have a reviewed **partial** behavioral claim.
This is not a percentage of ISA functionality. No instruction is declared exhaustively covered.
A test passing supports only its stated assertion and exercised parameters.

Source sightings include fixture setup and helper code. They are navigation aids, not coverage.
Dynamic dispatch sites are retained separately in audit.json, so static absence is not proof of absence.

## Instruction map

| Instruction | Reviewed behavioral requirements | Source sightings |
|---|---|---|
| ADDDMAREG | [isa.scalar](#isascalar) | none found |
| ADDRCRXY | **gap: no reviewed claim** | none found |
| ADDRCRZW | **gap: no reviewed claim** | none found |
| APOOL3S1 | **gap: no reviewed claim** | none found |
| APOOL3S2 | **gap: no reviewed claim** | none found |
| ATCAS | **gap: no reviewed claim** | none found |
| ATGETM | [sync.mutex_exclusion](#syncmutex_exclusion) | [tests/isa/test_sync.py:92](../isa/test_sync.py#L92), [tests/isa/test_sync.py:93](../isa/test_sync.py#L93) |
| ATINCGET | **gap: no reviewed claim** | none found |
| ATINCGETPTR | **gap: no reviewed claim** | none found |
| ATRELM | [sync.mutex_exclusion](#syncmutex_exclusion) | [tests/isa/test_sync.py:99](../isa/test_sync.py#L99) |
| ATSWAP | **gap: no reviewed claim** | none found |
| BITWOPDMAREG | [isa.scalar](#isascalar) | none found |
| CFGSHIFTMASK | **gap: no reviewed claim** | none found |
| CLEARDVALID | [sync.source_flags](#syncsource_flags) | [tests/movement/packer/test_scatter_formats.py:67](../movement/packer/test_scatter_formats.py#L67), [tests/operation_pocs/runtime/ops.py:154](../operation_pocs/runtime/ops.py#L154) |
| CLREXPHIST | **gap: no reviewed claim** | none found |
| CMPDMAREG | [isa.scalar](#isascalar) | none found |
| CONV3S1 | **gap: no reviewed claim** | none found |
| CONV3S2 | **gap: no reviewed claim** | none found |
| DMANOP | **gap: no reviewed claim** | [tests/movement/unpacker/unpack.py:594](../movement/unpacker/unpack.py#L594), [tests/timing/test_instruction_timing.py:91](../timing/test_instruction_timing.py#L91) |
| DOTPV | **gap: no reviewed claim** | none found |
| ELWADD | [fpu.elementwise](#fpuelementwise) | [tests/compute/fpu/test_elwmul_slots.py:107](../compute/fpu/test_elwmul_slots.py#L107) |
| ELWMUL | [fpu.elementwise](#fpuelementwise) | [tests/compute/fpu/test_dst_bandwidth.py:163](../compute/fpu/test_dst_bandwidth.py#L163), [tests/compute/fpu/test_elwmul_slots.py:106](../compute/fpu/test_elwmul_slots.py#L106), [tests/compute/fpu/test_rmsnorm_blog.py:73](../compute/fpu/test_rmsnorm_blog.py#L73) |
| ELWSUB | [fpu.elementwise](#fpuelementwise) | none found |
| FLUSHDMA | **gap: no reviewed claim** | none found |
| GAPOOL | [fpu.matrix_pool](#fpumatrix_pool) | [tests/compute/fpu/test_elwmul_slots.py:109](../compute/fpu/test_elwmul_slots.py#L109), [tests/compute/fpu/test_mean.py:110](../compute/fpu/test_mean.py#L110), [tests/compute/fpu/test_rmsnorm_reduce.py:318](../compute/fpu/test_rmsnorm_reduce.py#L318) |
| GATESRCRST | **gap: no reviewed claim** | [tests/compute/fpu/test_rmsnorm_reduce.py:310](../compute/fpu/test_rmsnorm_reduce.py#L310), [tests/compute/fpu/test_rmsnorm_reduce.py:360](../compute/fpu/test_rmsnorm_reduce.py#L360), [tests/compute/fpu/test_sum_finish.py:50](../compute/fpu/test_sum_finish.py#L50) |
| GMPOOL | [fpu.matrix_pool](#fpumatrix_pool) | [tests/compute/fpu/test_elwmul_slots.py:110](../compute/fpu/test_elwmul_slots.py#L110), [tests/operation_pocs/fpu/emit.py:40](../operation_pocs/fpu/emit.py#L40) |
| INCADCXY | **gap: no reviewed claim** | none found |
| INCADCZW | **gap: no reviewed claim** | none found |
| INCRWC | [sfpu.loadmacro](#sfpuloadmacro) | [tests/compute/fpu/test_elwmul_slots.py:102](../compute/fpu/test_elwmul_slots.py#L102), [tests/compute/fpu/test_elwmul_slots.py:104](../compute/fpu/test_elwmul_slots.py#L104), [tests/compute/fpu/test_rmsnorm_llama3.py:92](../compute/fpu/test_rmsnorm_llama3.py#L92) |
| LOADIND | **gap: no reviewed claim** | none found |
| LOADREG | **gap: no reviewed claim** | none found |
| MFCONV3S1 | **gap: no reviewed claim** | none found |
| MOP | [sfpu.loadmacro](#sfpuloadmacro) | [tests/movement/unpacker/unpack.py:166](../movement/unpacker/unpack.py#L166) |
| MOP_CFG | **gap: no reviewed claim** | none found |
| MOVA2D | [fpu.moves_zero](#fpumoves_zero), [unpack.paths](#unpackpaths) | [tests/compute/fpu/test_dst_bandwidth.py:58](../compute/fpu/test_dst_bandwidth.py#L58), [tests/compute/fpu/test_dst_bandwidth.py:73](../compute/fpu/test_dst_bandwidth.py#L73), [tests/compute/fpu/test_dst_bandwidth.py:147](../compute/fpu/test_dst_bandwidth.py#L147) |
| MOVB2A | **gap: no reviewed claim** | [tests/compute/fpu/test_sum_finish.py:55](../compute/fpu/test_sum_finish.py#L55) |
| MOVB2D | [fpu.moves_zero](#fpumoves_zero), [unpack.paths](#unpackpaths) | [tests/compute/fpu/test_rmsnorm_blog.py:79](../compute/fpu/test_rmsnorm_blog.py#L79), [tests/compute/fpu/test_rmsnorm_llama3.py:214](../compute/fpu/test_rmsnorm_llama3.py#L214), [tests/compute/fpu/test_rmsnorm_reduce.py:371](../compute/fpu/test_rmsnorm_reduce.py#L371) |
| MOVD2A | [fpu.moves_zero](#fpumoves_zero) | [tests/compute/fpu/test_rmsnorm_reduce.py:305](../compute/fpu/test_rmsnorm_reduce.py#L305), [tests/compute/fpu/test_rmsnorm_reduce.py:358](../compute/fpu/test_rmsnorm_reduce.py#L358), [tests/operation_pocs/fpu/emit.py:51](../operation_pocs/fpu/emit.py#L51) |
| MOVD2B | [fpu.moves_zero](#fpumoves_zero) | [tests/compute/fpu/test_rmsnorm_reduce.py:172](../compute/fpu/test_rmsnorm_reduce.py#L172), [tests/compute/fpu/test_rmsnorm_reduce.py:359](../compute/fpu/test_rmsnorm_reduce.py#L359), [tests/compute/fpu/test_sum_finish.py:49](../compute/fpu/test_sum_finish.py#L49) |
| MOVDBGA2D | **gap: no reviewed claim** | none found |
| MOVDBGB2D | **gap: no reviewed claim** | none found |
| MPOOL3S1 | **gap: no reviewed claim** | none found |
| MPOOL3S2 | **gap: no reviewed claim** | none found |
| MULDMAREG | [isa.scalar](#isascalar) | none found |
| MVMUL | [fpu.matrix_pool](#fpumatrix_pool) | [tests/compute/fpu/bench_matmul_compute_only.py:51](../compute/fpu/bench_matmul_compute_only.py#L51), [tests/compute/fpu/test_elwmul_slots.py:108](../compute/fpu/test_elwmul_slots.py#L108), [tests/compute/fpu/test_mean.py:110](../compute/fpu/test_mean.py#L110) |
| NOP | **gap: no reviewed claim** | [tests/movement/unpacker/unpack.py:148](../movement/unpacker/unpack.py#L148), [tests/movement/unpacker/unpack.py:149](../movement/unpacker/unpack.py#L149), [tests/movement/unpacker/unpack.py:150](../movement/unpacker/unpack.py#L150) |
| PACR | [pack.formats_tails](#packformats_tails), [pack.activation](#packactivation), [pack.bf16_rounding](#packbf16_rounding), [pack.fp8](#packfp8), [pack.scatter](#packscatter), [pack.l1_accumulation](#packl1_accumulation), [transport.prefixes](#transportprefixes) | [tests/movement/packer/pack.py:18](../movement/packer/pack.py#L18), [tests/movement/packer/test_scatter.py:57](../movement/packer/test_scatter.py#L57), [tests/movement/packer/test_scatter.py:58](../movement/packer/test_scatter.py#L58) |
| PACR_SETREG | **gap: no reviewed claim** | none found |
| RAREB | **gap: no reviewed claim** | none found |
| RDCFG | **gap: no reviewed claim** | none found |
| REG2FLOP | **gap: no reviewed claim** | none found |
| REPLAY | [sfpu.loadmacro](#sfpuloadmacro) | [tests/compute/fpu/bench_matmul_compute_only.py:57](../compute/fpu/bench_matmul_compute_only.py#L57), [tests/compute/fpu/test_dst_bandwidth.py:30](../compute/fpu/test_dst_bandwidth.py#L30), [tests/compute/fpu/test_elwmul_slots.py:117](../compute/fpu/test_elwmul_slots.py#L117) |
| RESOURCEDECL | **gap: no reviewed claim** | none found |
| RMWCIB0 | **gap: no reviewed claim** | [tests/movement/unpacker/unpack.py:421](../movement/unpacker/unpack.py#L421) |
| RMWCIB1 | **gap: no reviewed claim** | [tests/movement/unpacker/unpack.py:421](../movement/unpacker/unpack.py#L421) |
| RMWCIB2 | **gap: no reviewed claim** | [tests/movement/unpacker/unpack.py:421](../movement/unpacker/unpack.py#L421) |
| RMWCIB3 | **gap: no reviewed claim** | [tests/movement/unpacker/unpack.py:421](../movement/unpacker/unpack.py#L421) |
| RSTDMA | **gap: no reviewed claim** | none found |
| SEMGET | [sync.semaphores](#syncsemaphores), [sync.all_masks_saturation](#syncall_masks_saturation) | [tests/isa/test_sync.py:25](../isa/test_sync.py#L25), [tests/movement/unpacker/unpack.py:125](../movement/unpacker/unpack.py#L125), [tests/operation_pocs/runtime/ops.py:126](../operation_pocs/runtime/ops.py#L126) |
| SEMINIT | [sync.semaphores](#syncsemaphores), [sync.all_masks_saturation](#syncall_masks_saturation), [sync.combined_wait_conditions](#synccombined_wait_conditions) | [tests/compute/sfpu/test_q6.py:271](../compute/sfpu/test_q6.py#L271), [tests/isa/test_sync.py:22](../isa/test_sync.py#L22), [tests/isa/test_sync.py:23](../isa/test_sync.py#L23) |
| SEMPOST | [sync.semaphores](#syncsemaphores), [sync.all_masks_saturation](#syncall_masks_saturation) | [tests/isa/test_sync.py:24](../isa/test_sync.py#L24), [tests/isa/test_sync.py:56](../isa/test_sync.py#L56), [tests/movement/unpacker/unpack.py:129](../movement/unpacker/unpack.py#L129) |
| SEMWAIT | [sync.semaphores](#syncsemaphores), [sync.combined_wait_conditions](#synccombined_wait_conditions) | [tests/isa/test_sync.py:55](../isa/test_sync.py#L55), [tests/movement/unpacker/unpack.py:121](../movement/unpacker/unpack.py#L121), [tests/operation_pocs/runtime/ops.py:129](../operation_pocs/runtime/ops.py#L129) |
| SETADC | **gap: no reviewed claim** | [tests/movement/packer/pack.py:62](../movement/packer/pack.py#L62), [tests/movement/packer/pack.py:63](../movement/packer/pack.py#L63), [tests/movement/packer/pack.py:64](../movement/packer/pack.py#L64) |
| SETADCXX | **gap: no reviewed claim** | [tests/compute/fpu/bench_matmul_compute_only.py:38](../compute/fpu/bench_matmul_compute_only.py#L38), [tests/compute/fpu/bench_matmul_compute_only.py:81](../compute/fpu/bench_matmul_compute_only.py#L81), [tests/compute/fpu/test_dst_bandwidth.py:38](../compute/fpu/test_dst_bandwidth.py#L38) |
| SETADCXY | **gap: no reviewed claim** | [tests/movement/packer/test_scatter_formats.py:128](../movement/packer/test_scatter_formats.py#L128), [tests/movement/unpacker/test_unpack_row_major.py:48](../movement/unpacker/test_unpack_row_major.py#L48), [tests/movement/unpacker/unpack.py:568](../movement/unpacker/unpack.py#L568) |
| SETADCZW | **gap: no reviewed claim** | [tests/compute/fpu/test_mean.py:75](../compute/fpu/test_mean.py#L75), [tests/compute/fpu/test_mean.py:80](../compute/fpu/test_mean.py#L80), [tests/compute/fpu/test_rmsnorm_llama3.py:127](../compute/fpu/test_rmsnorm_llama3.py#L127) |
| SETASHRMH | **gap: no reviewed claim** | none found |
| SETASHRMH0 | **gap: no reviewed claim** | none found |
| SETASHRMH1 | **gap: no reviewed claim** | none found |
| SETASHRMV | **gap: no reviewed claim** | none found |
| SETC16 | **gap: no reviewed claim** | [tests/movement/unpacker/unpack.py:233](../movement/unpacker/unpack.py#L233), [tests/movement/unpacker/unpack.py:283](../movement/unpacker/unpack.py#L283), [tests/movement/unpacker/unpack.py:285](../movement/unpacker/unpack.py#L285) |
| SETDMAREG | **gap: no reviewed claim** | [tests/isa/test_scalar.py:26](../isa/test_scalar.py#L26), [tests/movement/unpacker/unpack.py:514](../movement/unpacker/unpack.py#L514) |
| SETDVALID | **gap: no reviewed claim** | none found |
| SETIBRWC | **gap: no reviewed claim** | none found |
| SETPKEDGOF | **gap: no reviewed claim** | none found |
| SETRWC | **gap: no reviewed claim** | [tests/compute/fpu/bench_matmul_compute_only.py:48](../compute/fpu/bench_matmul_compute_only.py#L48), [tests/compute/fpu/bench_matmul_compute_only.py:73](../compute/fpu/bench_matmul_compute_only.py#L73), [tests/compute/fpu/test_dst_bandwidth.py:53](../compute/fpu/test_dst_bandwidth.py#L53) |
| SFPABS | [sfpu.arithmetic](#sfpuarithmetic), [isa.sfpu_bits](#isasfpu_bits) | [tests/operation_pocs/sfpu_math/emit.py:40](../operation_pocs/sfpu_math/emit.py#L40) |
| SFPADD | [sfpu.arithmetic](#sfpuarithmetic) | [tests/compute/fpu/test_mean.py:37](../compute/fpu/test_mean.py#L37), [tests/compute/fpu/test_rmsnorm_hybrid.py:189](../compute/fpu/test_rmsnorm_hybrid.py#L189), [tests/compute/fpu/test_rmsnorm_llama3.py:42](../compute/fpu/test_rmsnorm_llama3.py#L42) |
| SFPADDI | [sfpu.predicated_movement](#sfpupredicated_movement) | [tests/movement/sfpu/test_predication.py:41](../movement/sfpu/test_predication.py#L41), [tests/movement/sfpu/test_predication.py:50](../movement/sfpu/test_predication.py#L50), [tests/operation_pocs/sfpu_movement/test_operations.py:156](../operation_pocs/sfpu_movement/test_operations.py#L156) |
| SFPAND | [isa.sfpu_bits](#isasfpu_bits) | [tests/compute/sfpu/test_q6.py:155](../compute/sfpu/test_q6.py#L155), [tests/compute/sfpu/test_q6.py:158](../compute/sfpu/test_q6.py#L158), [tests/isa/test_sfpu_bits.py:173](../isa/test_sfpu_bits.py#L173) |
| SFPARECIP | [sfpu.reciprocal_exp](#sfpureciprocal_exp) | [tests/operation_pocs/sfpu_math/emit.py:47](../operation_pocs/sfpu_math/emit.py#L47), [tests/operation_pocs/sfpu_math/emit.py:50](../operation_pocs/sfpu_math/emit.py#L50), [tests/operation_pocs/sfpu_math/emit.py:57](../operation_pocs/sfpu_math/emit.py#L57) |
| SFPCAST | [sfpu.cast_rounding](#sfpucast_rounding), [isa.sfpu_bits](#isasfpu_bits) | [tests/compute/sfpu/test_q6.py:89](../compute/sfpu/test_q6.py#L89), [tests/compute/sfpu/test_q6.py:140](../compute/sfpu/test_q6.py#L140), [tests/compute/sfpu/test_q6.py:160](../compute/sfpu/test_q6.py#L160) |
| SFPCOMPC | [isa.predicate_stack](#isapredicate_stack) | none found |
| SFPCONFIG | [sfpu.movement_registers](#sfpumovement_registers), [sfpu.column_exchange](#sfpucolumn_exchange), [sfpu.swap_indices](#sfpuswap_indices), [sfpu.index_capture](#sfpuindex_capture), [sfpu.loadmacro](#sfpuloadmacro) | [tests/compute/fpu/test_dst_bandwidth.py:61](../compute/fpu/test_dst_bandwidth.py#L61), [tests/compute/fpu/test_dst_bandwidth.py:150](../compute/fpu/test_dst_bandwidth.py#L150), [tests/compute/fpu/test_rmsnorm_blog.py:48](../compute/fpu/test_rmsnorm_blog.py#L48) |
| SFPDIVP2 | [isa.sfpu_bits](#isasfpu_bits) | none found |
| SFPENCC | [sfpu.predicated_movement](#sfpupredicated_movement), [isa.predicate_stack](#isapredicate_stack) | [tests/compute/fpu/test_dst_bandwidth.py:60](../compute/fpu/test_dst_bandwidth.py#L60), [tests/compute/fpu/test_dst_bandwidth.py:149](../compute/fpu/test_dst_bandwidth.py#L149), [tests/compute/fpu/test_mean.py:107](../compute/fpu/test_mean.py#L107) |
| SFPEXEXP | [isa.sfpu_bits](#isasfpu_bits) | none found |
| SFPEXMAN | [isa.sfpu_bits](#isasfpu_bits) | none found |
| SFPGT | [isa.sfpu_bits](#isasfpu_bits), [isa.predicate_stack](#isapredicate_stack) | none found |
| SFPIADD | [isa.sfpu_bits](#isasfpu_bits) | [tests/compute/fpu/test_rmsnorm_llama3.py:73](../compute/fpu/test_rmsnorm_llama3.py#L73), [tests/compute/fpu/test_rmsnorm_reduce.py:86](../compute/fpu/test_rmsnorm_reduce.py#L86), [tests/isa/test_sfpu_bits.py:160](../isa/test_sfpu_bits.py#L160) |
| SFPLE | [isa.sfpu_bits](#isasfpu_bits), [isa.predicate_stack](#isapredicate_stack) | none found |
| SFPLOAD | [sfpu.movement_registers](#sfpumovement_registers), [sfpu.predicated_movement](#sfpupredicated_movement), [sfpu.column_exchange](#sfpucolumn_exchange), [sfpu.index_capture](#sfpuindex_capture) | [tests/compute/fpu/test_dst_bandwidth.py:68](../compute/fpu/test_dst_bandwidth.py#L68), [tests/compute/fpu/test_dst_bandwidth.py:164](../compute/fpu/test_dst_bandwidth.py#L164), [tests/compute/fpu/test_mean.py:134](../compute/fpu/test_mean.py#L134) |
| SFPLOADI | [sfpu.movement_registers](#sfpumovement_registers), [sfpu.raw_store_edges](#sfpuraw_store_edges), [sfpu.predicated_movement](#sfpupredicated_movement), [isa.sfpu_bits](#isasfpu_bits) | [tests/compute/fpu/test_rmsnorm_blog.py:58](../compute/fpu/test_rmsnorm_blog.py#L58), [tests/compute/fpu/test_rmsnorm_hybrid.py:51](../compute/fpu/test_rmsnorm_hybrid.py#L51), [tests/compute/fpu/test_rmsnorm_hybrid.py:52](../compute/fpu/test_rmsnorm_hybrid.py#L52) |
| SFPLOADMACRO | [sfpu.loadmacro](#sfpuloadmacro) | [tests/compute/fpu/test_rmsnorm_hybrid.py:173](../compute/fpu/test_rmsnorm_hybrid.py#L173), [tests/compute/fpu/test_rmsnorm_hybrid.py:202](../compute/fpu/test_rmsnorm_hybrid.py#L202), [tests/compute/fpu/test_rmsnorm_llama3.py:232](../compute/fpu/test_rmsnorm_llama3.py#L232) |
| SFPLUT | **gap: no reviewed claim** | none found |
| SFPLUTFP32 | **gap: no reviewed claim** | none found |
| SFPLZ | [isa.sfpu_bits](#isasfpu_bits) | none found |
| SFPMAD | [sfpu.arithmetic](#sfpuarithmetic) | [tests/compute/fpu/test_dst_bandwidth.py:166](../compute/fpu/test_dst_bandwidth.py#L166), [tests/compute/fpu/test_rmsnorm_blog.py:36](../compute/fpu/test_rmsnorm_blog.py#L36), [tests/compute/fpu/test_rmsnorm_hybrid.py:109](../compute/fpu/test_rmsnorm_hybrid.py#L109) |
| SFPMOV | [sfpu.arithmetic](#sfpuarithmetic), [sfpu.movement_registers](#sfpumovement_registers), [sfpu.predicated_movement](#sfpupredicated_movement), [isa.sfpu_bits](#isasfpu_bits) | [tests/compute/fpu/test_mean.py:44](../compute/fpu/test_mean.py#L44), [tests/compute/fpu/test_mean.py:51](../compute/fpu/test_mean.py#L51), [tests/compute/fpu/test_rmsnorm_hybrid.py:194](../compute/fpu/test_rmsnorm_hybrid.py#L194) |
| SFPMUL | [sfpu.arithmetic](#sfpuarithmetic), [sfpu.loadmacro](#sfpuloadmacro) | [tests/compute/fpu/test_rmsnorm_hybrid.py:50](../compute/fpu/test_rmsnorm_hybrid.py#L50), [tests/compute/fpu/test_rmsnorm_llama3.py:47](../compute/fpu/test_rmsnorm_llama3.py#L47), [tests/compute/fpu/test_rmsnorm_llama3.py:65](../compute/fpu/test_rmsnorm_llama3.py#L65) |
| SFPMUL24 | [isa.sfpu_bits](#isasfpu_bits) | [tests/isa/test_sfpu_bits.py:163](../isa/test_sfpu_bits.py#L163), [tests/timing/test_instruction_timing.py:83](../timing/test_instruction_timing.py#L83) |
| SFPMULI | **gap: no reviewed claim** | [tests/compute/fpu/test_mean.py:141](../compute/fpu/test_mean.py#L141), [tests/compute/fpu/test_rmsnorm_reduce.py:87](../compute/fpu/test_rmsnorm_reduce.py#L87), [tests/compute/fpu/test_rmsnorm_reduce.py:295](../compute/fpu/test_rmsnorm_reduce.py#L295) |
| SFPNOP | **gap: no reviewed claim** | [tests/compute/fpu/test_rmsnorm_blog.py:49](../compute/fpu/test_rmsnorm_blog.py#L49), [tests/compute/fpu/test_rmsnorm_blog.py:85](../compute/fpu/test_rmsnorm_blog.py#L85), [tests/compute/fpu/test_rmsnorm_hybrid.py:92](../compute/fpu/test_rmsnorm_hybrid.py#L92) |
| SFPNOT | [isa.sfpu_bits](#isasfpu_bits) | none found |
| SFPOR | [isa.sfpu_bits](#isasfpu_bits) | [tests/compute/sfpu/test_q6.py:126](../compute/sfpu/test_q6.py#L126), [tests/compute/sfpu/test_q6.py:159](../compute/sfpu/test_q6.py#L159), [tests/isa/test_sfpu_bits.py:174](../isa/test_sfpu_bits.py#L174) |
| SFPPOPC | [isa.predicate_stack](#isapredicate_stack) | [tests/isa/test_predicate_stack.py:114](../isa/test_predicate_stack.py#L114), [tests/isa/test_predicate_stack.py:116](../isa/test_predicate_stack.py#L116) |
| SFPPUSHC | [isa.predicate_stack](#isapredicate_stack) | [tests/isa/test_predicate_stack.py:98](../isa/test_predicate_stack.py#L98) |
| SFPSETCC | [sfpu.predicated_movement](#sfpupredicated_movement), [isa.sfpu_bits](#isasfpu_bits) | [tests/operation_pocs/sfpu_math/test_math.py:53](../operation_pocs/sfpu_math/test_math.py#L53), [tests/operation_pocs/sfpu_movement/emitters.py:81](../operation_pocs/sfpu_movement/emitters.py#L81), [tests/operation_pocs/transport/dst.py:46](../operation_pocs/transport/dst.py#L46) |
| SFPSETEXP | [isa.sfpu_bits](#isasfpu_bits) | none found |
| SFPSETMAN | [isa.sfpu_bits](#isasfpu_bits) | none found |
| SFPSETSGN | [isa.sfpu_bits](#isasfpu_bits) | none found |
| SFPSHFT | [isa.sfpu_bits](#isasfpu_bits) | [tests/compute/fpu/test_rmsnorm_llama3.py:70](../compute/fpu/test_rmsnorm_llama3.py#L70), [tests/compute/fpu/test_rmsnorm_reduce.py:83](../compute/fpu/test_rmsnorm_reduce.py#L83), [tests/compute/sfpu/test_q6.py:125](../compute/sfpu/test_q6.py#L125) |
| SFPSHFT2 | **gap: no reviewed claim** | [tests/compute/fpu/test_mean.py:46](../compute/fpu/test_mean.py#L46), [tests/compute/fpu/test_rmsnorm_llama3.py:56](../compute/fpu/test_rmsnorm_llama3.py#L56), [tests/timing/test_instruction_timing.py:87](../timing/test_instruction_timing.py#L87) |
| SFPSTOCHRND | **gap: no reviewed claim** | none found |
| SFPSTORE | [sfpu.movement_registers](#sfpumovement_registers), [sfpu.raw_store_edges](#sfpuraw_store_edges), [sfpu.predicated_movement](#sfpupredicated_movement), [sfpu.column_exchange](#sfpucolumn_exchange) | [tests/compute/fpu/test_dst_bandwidth.py:70](../compute/fpu/test_dst_bandwidth.py#L70), [tests/compute/fpu/test_dst_bandwidth.py:90](../compute/fpu/test_dst_bandwidth.py#L90), [tests/compute/fpu/test_dst_bandwidth.py:91](../compute/fpu/test_dst_bandwidth.py#L91) |
| SFPSWAP | [sfpu.swap_indices](#sfpuswap_indices) | [tests/movement/sfpu/test_minmax.py:45](../movement/sfpu/test_minmax.py#L45), [tests/timing/test_instruction_timing.py:86](../timing/test_instruction_timing.py#L86) |
| SFPTRANSP | **gap: no reviewed claim** | [tests/compute/fpu/test_mean.py:52](../compute/fpu/test_mean.py#L52), [tests/compute/fpu/test_rmsnorm_llama3.py:61](../compute/fpu/test_rmsnorm_llama3.py#L61), [tests/timing/test_instruction_timing.py:85](../timing/test_instruction_timing.py#L85) |
| SFPXOR | [isa.sfpu_bits](#isasfpu_bits) | [tests/compute/sfpu/test_q6.py:139](../compute/sfpu/test_q6.py#L139) |
| SHIFTDMAREG | [isa.scalar](#isascalar) | none found |
| SHIFTXA | **gap: no reviewed claim** | none found |
| SHIFTXB | **gap: no reviewed claim** | none found |
| STALLWAIT | [sync.source_flags](#syncsource_flags) | [tests/compute/fpu/test_mean.py:81](../compute/fpu/test_mean.py#L81), [tests/movement/unpacker/test_dst_paths.py:37](../movement/unpacker/test_dst_paths.py#L37), [tests/movement/unpacker/unpack.py:117](../movement/unpacker/unpack.py#L117) |
| STOREIND | **gap: no reviewed claim** | none found |
| STOREREG | **gap: no reviewed claim** | none found |
| STREAMWAIT | **gap: no reviewed claim** | none found |
| STREAMWRCFG | **gap: no reviewed claim** | none found |
| SUBDMAREG | [isa.scalar](#isascalar) | none found |
| TBUFCMD | **gap: no reviewed claim** | none found |
| TRNSPSRCA | **gap: no reviewed claim** | none found |
| TRNSPSRCB | **gap: no reviewed claim** | [tests/compute/fpu/test_sum_finish.py:52](../compute/fpu/test_sum_finish.py#L52) |
| UNPACR | [unpack.paths](#unpackpaths), [unpack.fp8](#unpackfp8), [transport.prefixes](#transportprefixes), [transport.scatter](#transportscatter) | [tests/movement/unpacker/test_unpack_row_major.py:53](../movement/unpacker/test_unpack_row_major.py#L53), [tests/movement/unpacker/unpack.py:179](../movement/unpacker/unpack.py#L179), [tests/operation_pocs/transport/ops.py:92](../operation_pocs/transport/ops.py#L92) |
| UNPACR_NOP | [sync.source_flags](#syncsource_flags) | [tests/compute/fpu/test_rmsnorm_reduce.py:150](../compute/fpu/test_rmsnorm_reduce.py#L150), [tests/movement/unpacker/unpack.py:186](../movement/unpacker/unpack.py#L186), [tests/operation_pocs/runtime/ops.py:151](../operation_pocs/runtime/ops.py#L151) |
| WRCFG | **gap: no reviewed claim** | [tests/movement/unpacker/unpack.py:592](../movement/unpacker/unpack.py#L592) |
| XMOV | **gap: no reviewed claim** | none found |
| ZEROACC | [fpu.moves_zero](#fpumoves_zero) | [tests/compute/fpu/bench_matmul_compute_only.py:49](../compute/fpu/bench_matmul_compute_only.py#L49), [tests/compute/fpu/test_dst_bandwidth.py:54](../compute/fpu/test_dst_bandwidth.py#L54), [tests/compute/fpu/test_dst_bandwidth.py:142](../compute/fpu/test_dst_bandwidth.py#L142) |
| ZEROSRC | **gap: no reviewed claim** | [tests/compute/fpu/test_rmsnorm_reduce.py:171](../compute/fpu/test_rmsnorm_reduce.py#L171), [tests/movement/unpacker/unpack.py:618](../movement/unpacker/unpack.py#L618) |

## Reviewed requirements

### fpu.elementwise

Instructions: ELWADD, ELWSUB, ELWMUL.

**Checked:** Independent numerical oracle for row/column/scalar/no broadcast; add/sub overwrite and accumulation; independent A/B/Dst placement; source and full-Dst poison guards; BF16 sources with BF16 and FP32 Dst.

**Remaining:** Only selected address/fidelity recipes and finite values. Other formats, NaN/Inf/denormals, clear_dvalid combinations, rounding and full address-modifier state transitions remain.

**Recorded outcomes:** {'passed': 224}.

- [test_operation](../operation_pocs/fpu/test_fpu.py#L64) — `tests/operation_pocs/fpu/test_fpu.py`
- [test_bf16_dst](../operation_pocs/fpu/test_bf16.py#L17) — `tests/operation_pocs/fpu/test_bf16.py`

### fpu.matrix_pool

Instructions: MVMUL, GAPOOL, GMPOOL.

**Checked:** Explicit dot-product/max host oracles, selected LoFi/HiFi2 schedules, placements and both Dst formats; checks all Dst tiles and source buffers.

**Remaining:** Not complete fidelity/format coverage. Pool indices, address modifiers, valid flags, extrema and all reduction modes remain.

**Recorded outcomes:** {'passed': 248}.

- [test_operation](../operation_pocs/fpu/test_fpu.py#L64) — `tests/operation_pocs/fpu/test_fpu.py`
- [test_bf16_dst](../operation_pocs/fpu/test_bf16.py#L17) — `tests/operation_pocs/fpu/test_bf16.py`
- [test_row_major_matrix_mapping](../operation_pocs/fpu/test_row_major_mapping.py#L22) — `tests/operation_pocs/fpu/test_row_major_mapping.py`

### fpu.moves_zero

Instructions: MOVA2D, MOVB2D, MOVD2A, MOVD2B, ZEROACC.

**Checked:** Selected row-group copies and single-row zeroing; independent placements, FP32-to-BF16 narrowing, full-Dst/source preservation.

**Remaining:** Other move modes and ZEROACC clear-mode/zero-flag combinations remain. ZEROACC use as fixture initialization is not additional proof.

**Recorded outcomes:** {'passed': 224}.

- [test_operation](../operation_pocs/fpu/test_fpu.py#L64) — `tests/operation_pocs/fpu/test_fpu.py`
- [test_bf16_dst](../operation_pocs/fpu/test_bf16.py#L17) — `tests/operation_pocs/fpu/test_bf16.py`

### sfpu.arithmetic

Instructions: SFPADD, SFPMUL, SFPMAD, SFPMOV, SFPABS.

**Checked:** Finite arithmetic against FP64-derived expected values; subtraction modifier, masks, placement, destination/source aliases and repeated operations.

**Remaining:** Tolerance comparisons do not prove the documented partially fused bit-exact FMA model. Full sign/indirection combinations and IEEE exceptional behavior remain.

**Recorded outcomes:** {'passed': 47}.

- [test_operations](../operation_pocs/sfpu_math/test_math.py#L128) — `tests/operation_pocs/sfpu_math/test_math.py`
- [test_masks_placement](../operation_pocs/sfpu_math/test_math.py#L133) — `tests/operation_pocs/sfpu_math/test_math.py`
- [test_aliases](../operation_pocs/sfpu_math/test_math.py#L143) — `tests/operation_pocs/sfpu_math/test_math.py`
- [test_repeated_short_operations](../operation_pocs/sfpu_math/test_math.py#L151) — `tests/operation_pocs/sfpu_math/test_math.py`

### sfpu.reciprocal_exp

Instructions: SFPARECIP.

**Checked:** Native/refined reciprocal and exponential paths, exponent/domain boundaries and accuracy checks.

**Remaining:** Exception-characterization output alone is not conformance. Exact documented special values, all modifiers and PRNG/config interactions remain.

**Recorded outcomes:** {'passed': 22}.

- [test_native](../operation_pocs/sfpu_math/test_math.py#L147) — `tests/operation_pocs/sfpu_math/test_math.py`
- [test_reciprocal_boundaries](../operation_pocs/sfpu_math/test_math.py#L157) — `tests/operation_pocs/sfpu_math/test_math.py`
- [test_exp_boundaries](../operation_pocs/sfpu_math/test_math.py#L165) — `tests/operation_pocs/sfpu_math/test_math.py`

### sfpu.movement_registers

Instructions: SFPLOAD, SFPSTORE, SFPLOADI, SFPMOV, SFPCONFIG.

**Checked:** Per-lane FP32 mapping, all exposed source LRegs copied to L0-L7, self aliases, explicitly programmed configurable constants, full-Dst poison preservation.

**Remaining:** Most format/address modes, backdoor loads, config-register readback, PRNG and macro-template combinations remain.

**Recorded outcomes:** {'passed': 33}.

- [test_load_lane_mapping](../operation_pocs/sfpu_movement/test_operations.py#L90) — `tests/operation_pocs/sfpu_movement/test_operations.py`
- [test_movement](../operation_pocs/sfpu_movement/test_operations.py#L115) — `tests/operation_pocs/sfpu_movement/test_operations.py`
- [test_registers_and_aliases](../operation_pocs/sfpu_movement/test_operations.py#L191) — `tests/operation_pocs/sfpu_movement/test_operations.py`

### sfpu.raw_store_edges

Instructions: SFPLOADI, SFPSTORE.

**Checked:** Raw versus ordinary store bit patterns, signed zero, subnormals, infinities and a NaN payload, with full-Dst checks.

**Remaining:** Selected modes and values only; does not cover all integer/narrowing/partial-word formats.

**Recorded outcomes:** {'passed': 24}.

- [test_immediate_and_store_bits](../operation_pocs/sfpu_movement/test_operations.py#L231) — `tests/operation_pocs/sfpu_movement/test_operations.py`

### sfpu.predicated_movement

Instructions: SFPLOAD, SFPSTORE, SFPLOADI, SFPMOV, SFPADDI, SFPENCC, SFPSETCC.

**Checked:** Inactive-lane preservation for load/store/add/immediate/copy; all-off, all-on, alternating and every single-lane mask; following unmasked operation verifies reset.

**Remaining:** Not all modifier/format combinations or latent flag states are checked.

**Recorded outcomes:** {'passed': 186}.

- [test_predicate](../operation_pocs/sfpu_movement/test_operations.py#L148) — `tests/operation_pocs/sfpu_movement/test_operations.py`
- [test_sfpu_predication](../movement/sfpu/test_predication.py#L18) — `tests/movement/sfpu/test_predication.py`

### sfpu.column_exchange

Instructions: SFPLOAD, SFPSTORE, SFPCONFIG.

**Checked:** Separately verifies load and store column-override bits, low address bits and all individual exchange-mask bits, with placement guards.

**Remaining:** Selected FP32 transfer mode; other formats and configuration combinations remain.

**Recorded outcomes:** {'passed': 96}.

- [test_column_exchange](../movement/sfpu/test_column_exchange.py#L31) — `tests/movement/sfpu/test_column_exchange.py`

### sfpu.swap_indices

Instructions: SFPSWAP, SFPCONFIG.

**Checked:** Modes 0-9, value and paired-index results, lane min/max masks, exchange inversion, ties, signed zeros and predication.

**Remaining:** NaN payload ordering, all aliases, all config/modifier cross-products and documented scheduling hazards remain.

**Recorded outcomes:** {'passed': 30}.

- [test_swap_modes](../movement/sfpu/test_minmax.py#L29) — `tests/movement/sfpu/test_minmax.py`

### sfpu.index_capture

Instructions: SFPLOAD, SFPCONFIG.

**Checked:** Checks captured physical Dst row/column indices at low, unaligned and high rows.

**Remaining:** Other transfer formats, interactions with masking, and complete index configuration remain.

**Recorded outcomes:** {'passed': 5}.

- [test_capture_dst_indices](../movement/sfpu/test_minmax.py#L71) — `tests/movement/sfpu/test_minmax.py`

### sfpu.loadmacro

Instructions: SFPLOADMACRO, SFPCONFIG, SFPMUL, REPLAY, MOP, INCRWC.

**Checked:** Full-Dst scale-by-two oracle for explicit, serial/pipelined macro, explicit replay and macro replay schedules, with rotating registers.

**Remaining:** One macro recipe only. Other sub-units, conversion/rounding templates, sequence slots, delays, MOP masks and replay controls remain.

**Recorded outcomes:** {'passed': 5}.

- [test_scale_pipeline](../compute/sfpu/test_loadmacro_pipeline.py#L10) — `tests/compute/sfpu/test_loadmacro_pipeline.py`

### pack.formats_tails

Instructions: PACR.

**Checked:** Runtime row counts, Dst offsets, FP32/BF16 output and exact payload/guard checks.

**Remaining:** Other formats, compression, contexts and complete PACR modifier combinations remain.

**Recorded outcomes:** {'passed': 12}.

- [test_pack_runtime_rows_from_dst_to_row_major_cb](../movement/packer/test_pack.py#L87) — `tests/movement/packer/test_pack.py`

### pack.activation

Instructions: PACR.

**Checked:** Selected ReLU/clamp configurations checked as an independent partial pack kernel.

**Remaining:** All thresholds, formats, exceptional values and modifier interactions remain.

**Recorded outcomes:** {'passed': 4}.

- [test_packer_activation_is_a_standalone_partial_kernel](../movement/packer/test_pack.py#L130) — `tests/movement/packer/test_pack.py`

### pack.bf16_rounding

Instructions: PACR.

**Checked:** Deterministic tie-away rounding oracle; stochastic neighbor bounds, same-seed repeatability and different-seed changes.

**Remaining:** Does not prove distribution/unbiasedness or SFPU stochastic-round instruction behavior.

**Recorded outcomes:** {'passed': 1}.

- [test_deterministic_and_stochastic_bf16_format_conversion](../movement/packer/test_pack.py#L209) — `tests/movement/packer/test_pack.py`

### pack.fp8

Instructions: PACR.

**Checked:** E4M3 normal payloads, tail padding limits and explicit mantissa truncation oracle.

**Remaining:** Subnormal-preservation expectation is a strict expected failure, not a passing contract. Other formats and edge cases remain.

**Recorded outcomes:** {'passed': 19, 'xfail': 1}.

- [test_fp8_pack_runtime_tail](../movement/packer/test_pack_fp8.py#L10) — `tests/movement/packer/test_pack_fp8.py`
- [test_fp8_pack_truncates_mantissa](../movement/packer/test_pack_fp8.py#L34) — `tests/movement/packer/test_pack_fp8.py`
- [test_fp8_pack_zero_and_subnormal_values](../movement/packer/test_pack_fp8.py#L25) — `tests/movement/packer/test_pack_fp8.py`

### pack.scatter

Instructions: PACR.

**Checked:** One/four interfaces, contiguous/reverse/irregular/repeated Dst order, both Dst and output formats, exact tails and wrapping output CB.

**Remaining:** Other context/address/format combinations, compression and stream-driven packing remain.

**Recorded outcomes:** {'passed': 60}.

- [test_scatter_pack_formats_and_order](../movement/packer/test_scatter_formats.py#L166) — `tests/movement/packer/test_scatter_formats.py`
- [test_scatter_pack_exact_tail](../movement/packer/test_scatter_formats.py#L177) — `tests/movement/packer/test_scatter_formats.py`
- [test_scatter_pack_wrapping_cb](../movement/packer/test_scatter_formats.py#L259) — `tests/movement/packer/test_scatter_formats.py`

### pack.l1_accumulation

Instructions: PACR.

**Checked:** Repeated writes accumulate values at reused L1 destinations for FP32/BF16 and several lengths.

**Remaining:** Overflow, saturation, exceptional values and other accumulation configurations remain.

**Recorded outcomes:** {'passed': 12}.

- [test_l1_accumulation](../movement/packer/test_l1_accumulation.py#L52) — `tests/movement/packer/test_l1_accumulation.py`

### unpack.paths

Instructions: UNPACR, MOVA2D, MOVB2D.

**Checked:** Direct-to-Dst and source-mediated paths, exact FP32 precision checks, BF16 source placement, full/partial runtime counts and both unpackers.

**Remaining:** Full format/context/broadcast/transpose/tilize/cache-flush and address-counter semantics remain.

**Recorded outcomes:** {'passed': 25}.

- [test_unpack_f32_row_major_to_each_dst_tile](../movement/unpacker/test_unpack.py#L67) — `tests/movement/unpacker/test_unpack.py`
- [test_partial_unpack_to_dst_uses_a_runtime_bounded_mop](../movement/unpacker/test_unpack.py#L87) — `tests/movement/unpacker/test_unpack.py`
- [test_unpack_bf16_row_major_tile_to_source_bank](../movement/unpacker/test_unpack.py#L109) — `tests/movement/unpacker/test_unpack.py`
- [test_parallel_unpack_places_two_row_major_tiles_in_srca_and_srcb](../movement/unpacker/test_unpack.py#L138) — `tests/movement/unpacker/test_unpack.py`
- [test_l1_to_dst_paths](../movement/unpacker/test_dst_paths.py#L93) — `tests/movement/unpacker/test_dst_paths.py`
- [test_dst_path_precision](../movement/unpacker/test_dst_paths.py#L107) — `tests/movement/unpacker/test_dst_paths.py`

### unpack.fp8

Instructions: UNPACR.

**Checked:** E4M3 source-bank payloads, parallel banks and conversion paths, including explicit subnormal cleanup comparison.

**Remaining:** Expected failures and normal-only input selections must remain visible. No claim for all FP8 encodings.

**Recorded outcomes:** {'passed': 11, 'xfail': 4}.

- [test_fp8_source_bank](../movement/unpacker/test_unpack_fp8.py#L17) — `tests/movement/unpacker/test_unpack_fp8.py`
- [test_fp8_parallel_source_banks](../movement/unpacker/test_unpack_fp8.py#L33) — `tests/movement/unpacker/test_unpack_fp8.py`
- [test_fp8_host_subnormal_cleanup_is_redundant](../movement/unpacker/test_unpack_fp8.py#L51) — `tests/movement/unpacker/test_unpack_fp8.py`

### transport.prefixes

Instructions: UNPACR, PACR.

**Checked:** Independent payload and poison guards for every configured runtime prefix; checks unowned source/Dst preservation.

**Remaining:** TRANSPORT_LENGTHS can restrict the sweep; evidence must record the environment. Narrow format/recipe scope, not general modifiers.

**Recorded outcomes:** {'passed': 32}.

- [test_pack_all_prefixes](../operation_pocs/transport/test_transport.py#L62) — `tests/operation_pocs/transport/test_transport.py`
- [test_source_prefixes](../operation_pocs/transport/test_source.py#L89) — `tests/operation_pocs/transport/test_source.py`
- [test_dst_prefixes](../operation_pocs/transport/test_dst.py#L71) — `tests/operation_pocs/transport/test_dst.py`
- [test_signed_and_rounding_edges](../operation_pocs/transport/test_edges.py#L18) — `tests/operation_pocs/transport/test_edges.py`

### transport.scatter

Instructions: UNPACR.

**Checked:** Scattered source allocations and matrix pairs, native and staged paths, scattered Dst output with independent layout oracle.

**Remaining:** Selected address recipes do not prove complete address-counter/context semantics.

**Recorded outcomes:** {'passed': 56}.

- [test_scattered_source_unpack](../operation_pocs/transport/test_scatter_unpack.py#L68) — `tests/operation_pocs/transport/test_scatter_unpack.py`
- [test_scattered_matrix_pairs](../operation_pocs/transport/test_scatter_unpack.py#L74) — `tests/operation_pocs/transport/test_scatter_unpack.py`
- [test_native_scattered_source_unpack](../operation_pocs/transport/test_scatter_unpack.py#L81) — `tests/operation_pocs/transport/test_scatter_unpack.py`
- [test_native_scattered_matrix_pairs](../operation_pocs/transport/test_scatter_unpack.py#L87) — `tests/operation_pocs/transport/test_scatter_unpack.py`
- [test_scattered_dst_unpack](../operation_pocs/transport/test_scatter_unpack.py#L99) — `tests/operation_pocs/transport/test_scatter_unpack.py`

### sync.semaphores

Instructions: SEMINIT, SEMPOST, SEMGET, SEMWAIT.

**Checked:** Selected semaphore counts, untouched sentinel semaphore, ready/space conditions and a delayed peer proof that waits really block.

**Remaining:** All masks, saturation boundaries, maxima and resource-mask combinations need additional tests.

**Recorded outcomes:** {'passed': 18}.

- [test_semaphore_primitive](../operation_pocs/runtime/test_runtime.py#L121) — `tests/operation_pocs/runtime/test_runtime.py`
- [test_semaphore_blocking](../operation_pocs/runtime/test_runtime.py#L184) — `tests/operation_pocs/runtime/test_runtime.py`

### sync.source_flags

Instructions: UNPACR_NOP, CLEARDVALID, STALLWAIT.

**Checked:** Repeated source publish/wait/release cycles preserve payload; delayed peer checks wait-valid blocking for A and B.

**Remaining:** Not all source-bank selectors, clear modes or STALLWAIT resource masks. Completion alone does not prove every flag transition.

**Recorded outcomes:** {'passed': 10}.

- [test_source_flags](../operation_pocs/runtime/test_runtime.py#L217) — `tests/operation_pocs/runtime/test_runtime.py`
- [test_source_flag_blocking](../operation_pocs/runtime/test_runtime.py#L257) — `tests/operation_pocs/runtime/test_runtime.py`

### sync.all_masks_saturation

Instructions: SEMINIT, SEMPOST, SEMGET.

**Checked:** Walking-bit and multi-bit masks on TRISC1 plus an all-mask case on TRISC0/TRISC2 (trimmed 2026-10-07 from all 256 masks × 3 threads, which the recorded run covered); empty-mask no-op, unselected semaphore preservation, zero/fifteen saturation and increment past configured Max.

**Remaining:** Boundary Value/Max pairs are selected, not exhaustive. Concurrent updates and all Max values remain.

**Recorded outcomes:** {'passed': 2304}.

- [test_semaphore_masks_saturation](../isa/test_sync.py#L17) — `tests/isa/test_sync.py`

### sync.combined_wait_conditions

Instructions: SEMWAIT, SEMINIT.

**Checked:** Condition masks 1/2/3, both endpoints for combined condition, several multi-semaphore masks and all directed thread-cycle pairs. Partial peer release must not unblock before the last selected semaphore becomes ready.

**Remaining:** Only the Sync block bit is used. Other resource block masks, wait replacement and zero BlockMask remain.

**Recorded outcomes:** {'passed': 72}.

- [test_semaphore_wait_all_conditions](../isa/test_sync.py#L48) — `tests/isa/test_sync.py`

### sync.mutex_exclusion

Instructions: ATGETM, ATRELM.

**Checked:** All four valid Blackhole mutex indices; two/three contending threads increment shared memory under the mutex with an exact final-count oracle; same-owner reacquisition must allow one release.

**Remaining:** Round-robin fairness and release by a non-owner remain. Invalid mutex indices intentionally hang and are not executed.

**Recorded outcomes:** {'passed': 32}.

- [test_mutex_exclusion](../isa/test_sync.py#L84) — `tests/isa/test_sync.py`

### sfpu.cast_rounding

Instructions: SFPCAST.

**Checked:** Integer-to-FP32 nearest-even rounding at representability boundaries and ties, both signs including negative zero; stochastic results must be adjacent representable neighbors. Checks aliases, masks and raw 32-bit results.

**Remaining:** Stochastic probability distribution, exact PRNG sequence and reduced PRNG precision are not proved by neighbor bounds.

**Recorded outcomes:** {'passed': 24}.

- [test_cast_integer_to_float](../isa/test_sfpu_cast.py#L35) — `tests/isa/test_sfpu_cast.py`

### isa.scalar

Instructions: ADDDMAREG, BITWOPDMAREG, CMPDMAREG, MULDMAREG, SHIFTDMAREG, SUBDMAREG.

**Checked:** Register/immediate scalar arithmetic, all documented ALU selectors, aliases, GPR bank boundaries, all three threads, intermediate results and final 64-GPR contents.

**Remaining:** Exhaustive operand combinations, concurrent threads and scheduling hazards remain.

**Recorded outcomes:** {'passed': 594}.

- [test_scalar_gpr](../isa/test_scalar.py#L44) — `tests/isa/test_scalar.py`

### isa.sfpu_bits

Instructions: SFPABS, SFPAND, SFPCAST, SFPDIVP2, SFPEXEXP, SFPEXMAN, SFPGT, SFPIADD, SFPLE, SFPLOADI, SFPLZ, SFPMOV, SFPMUL24, SFPNOT, SFPOR, SFPSETCC, SFPSETEXP, SFPSETMAN, SFPSETSGN, SFPSHFT, SFPXOR.

**Checked:** Selected mode/immediate cross-products with integer/FP bit edges, aliases, all/none/half masks and observed flags.

**Remaining:** Lane-varying indirect indices, full register/configuration space, cast rounding and interactions remain.

**Recorded outcomes:** {'passed': 1122}.

- [test_sfpu_bits](../isa/test_sfpu_bits.py#L130) — `tests/isa/test_sfpu_bits.py`

### isa.predicate_stack

Instructions: SFPCOMPC, SFPENCC, SFPGT, SFPLE, SFPPOPC, SFPPUSHC.

**Checked:** All push/pop/comparison-stack modifiers and truth tables over selected depths including eight; observed masks and complement, deeper-stack preservation.

**Remaining:** Latent flags while predication is disabled are not fully observed; nonuniform lane stacks and backdoor configuration remain.

**Recorded outcomes:** {'passed': 5424}.

- [test_predicate_stack](../isa/test_predicate_stack.py#L76) — `tests/isa/test_predicate_stack.py`

## Runs

- Device 0, core 0, complete=True, exit=0: {'passed': 33725, 'xfail': 5}; changed sources: [].
