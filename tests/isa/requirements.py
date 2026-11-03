"""Reviewed behavioral claims, kept separate from automatic opcode sightings.

Each entry describes the assertion actually present, its test selectors, and
what those assertions do not establish. Entries are partial contracts, not
instruction-level completeness declarations.
"""
REQUIREMENTS = []


def requirement(key, instructions, assertion, tests, gaps):
  REQUIREMENTS.append(dict(id=key, instructions=instructions.split(), assertion=assertion,
                           tests=tests.split(), gaps=gaps, status='partial'))


requirement('fpu.elementwise', 'ELWADD ELWSUB ELWMUL',
  'Independent numerical oracle for row/column/scalar/no broadcast; add/sub overwrite and accumulation; independent A/B/Dst placement; source and full-Dst poison guards; BF16 sources with BF16 and FP32 Dst.',
  'tests/operation_pocs/fpu/test_fpu.py::test_operation tests/operation_pocs/fpu/test_bf16.py::test_bf16_dst',
  'Only selected address/fidelity recipes and finite values. Other formats, NaN/Inf/denormals, clear_dvalid combinations, rounding and full address-modifier state transitions remain.')
requirement('fpu.matrix_pool', 'MVMUL GAPOOL GMPOOL',
  'Explicit dot-product/max host oracles, selected LoFi/HiFi2 schedules, placements and both Dst formats; checks all Dst tiles and source buffers.',
  'tests/operation_pocs/fpu/test_fpu.py::test_operation tests/operation_pocs/fpu/test_bf16.py::test_bf16_dst tests/operation_pocs/fpu/test_row_major_mapping.py::test_row_major_matrix_mapping',
  'Not complete fidelity/format coverage. Pool indices, address modifiers, valid flags, extrema and all reduction modes remain.')
requirement('fpu.moves_zero', 'MOVA2D MOVB2D MOVD2A MOVD2B ZEROACC',
  'Selected row-group copies and single-row zeroing; independent placements, FP32-to-BF16 narrowing, full-Dst/source preservation.',
  'tests/operation_pocs/fpu/test_fpu.py::test_operation tests/operation_pocs/fpu/test_bf16.py::test_bf16_dst',
  'Other move modes and ZEROACC clear-mode/zero-flag combinations remain. ZEROACC use as fixture initialization is not additional proof.')
requirement('sfpu.arithmetic', 'SFPADD SFPMUL SFPMAD SFPMOV SFPABS',
  'Finite arithmetic against FP64-derived expected values; subtraction modifier, masks, placement, destination/source aliases and repeated operations.',
  'tests/operation_pocs/sfpu_math/test_math.py::test_operations tests/operation_pocs/sfpu_math/test_math.py::test_masks_placement tests/operation_pocs/sfpu_math/test_math.py::test_aliases tests/operation_pocs/sfpu_math/test_math.py::test_repeated_short_operations',
  'Tolerance comparisons do not prove the documented partially fused bit-exact FMA model. Full sign/indirection combinations and IEEE exceptional behavior remain.')
requirement('sfpu.reciprocal_exp', 'SFPARECIP',
  'Native/refined reciprocal and exponential paths, exponent/domain boundaries and accuracy checks.',
  'tests/operation_pocs/sfpu_math/test_math.py::test_native tests/operation_pocs/sfpu_math/test_math.py::test_reciprocal_boundaries tests/operation_pocs/sfpu_math/test_math.py::test_exp_boundaries',
  'Exception-characterization output alone is not conformance. Exact documented special values, all modifiers and PRNG/config interactions remain.')
requirement('sfpu.movement_registers', 'SFPLOAD SFPSTORE SFPLOADI SFPMOV SFPCONFIG',
  'Per-lane FP32 mapping, all exposed source LRegs copied to L0-L7, self aliases, explicitly programmed configurable constants, full-Dst poison preservation.',
  'tests/operation_pocs/sfpu_movement/test_operations.py::test_load_lane_mapping tests/operation_pocs/sfpu_movement/test_operations.py::test_movement tests/operation_pocs/sfpu_movement/test_operations.py::test_registers_and_aliases',
  'Most format/address modes, backdoor loads, config-register readback, PRNG and macro-template combinations remain.')
requirement('sfpu.raw_store_edges', 'SFPLOADI SFPSTORE',
  'Raw versus ordinary store bit patterns, signed zero, subnormals, infinities and a NaN payload, with full-Dst checks.',
  'tests/operation_pocs/sfpu_movement/test_operations.py::test_immediate_and_store_bits',
  'Selected modes and values only; does not cover all integer/narrowing/partial-word formats.')
requirement('sfpu.predicated_movement', 'SFPLOAD SFPSTORE SFPLOADI SFPMOV SFPADDI SFPENCC SFPSETCC',
  'Inactive-lane preservation for load/store/add/immediate/copy; all-off, all-on, alternating and every single-lane mask; following unmasked operation verifies reset.',
  'tests/operation_pocs/sfpu_movement/test_operations.py::test_predicate tests/movement/sfpu/test_predication.py::test_sfpu_predication',
  'Not all modifier/format combinations or latent flag states are checked.')
requirement('sfpu.column_exchange', 'SFPLOAD SFPSTORE SFPCONFIG',
  'Separately verifies load and store column-override bits, low address bits and all individual exchange-mask bits, with placement guards.',
  'tests/movement/sfpu/test_column_exchange.py::test_column_exchange',
  'Selected FP32 transfer mode; other formats and configuration combinations remain.')
requirement('sfpu.swap_indices', 'SFPSWAP SFPCONFIG',
  'Modes 0-9, value and paired-index results, lane min/max masks, exchange inversion, ties, signed zeros and predication.',
  'tests/movement/sfpu/test_minmax.py::test_swap_modes',
  'NaN payload ordering, all aliases, all config/modifier cross-products and documented scheduling hazards remain.')
requirement('sfpu.index_capture', 'SFPLOAD SFPCONFIG',
  'Checks captured physical Dst row/column indices at low, unaligned and high rows.',
  'tests/movement/sfpu/test_minmax.py::test_capture_dst_indices',
  'Other transfer formats, interactions with masking, and complete index configuration remain.')
requirement('sfpu.loadmacro', 'SFPLOADMACRO SFPCONFIG SFPMUL REPLAY MOP INCRWC',
  'Full-Dst scale-by-two oracle for explicit, serial/pipelined macro, explicit replay and macro replay schedules, with rotating registers.',
  'tests/compute/sfpu/test_loadmacro_pipeline.py::test_scale_pipeline',
  'One macro recipe only. Other sub-units, conversion/rounding templates, sequence slots, delays, MOP masks and replay controls remain.')
requirement('pack.formats_tails', 'PACR',
  'Runtime row counts, Dst offsets, FP32/BF16 output and exact payload/guard checks.',
  'tests/movement/packer/test_pack.py::test_pack_runtime_rows_from_dst_to_row_major_cb',
  'Other formats, compression, contexts and complete PACR modifier combinations remain.')
requirement('pack.activation', 'PACR',
  'Selected ReLU/clamp configurations checked as an independent partial pack kernel.',
  'tests/movement/packer/test_pack.py::test_packer_activation_is_a_standalone_partial_kernel',
  'All thresholds, formats, exceptional values and modifier interactions remain.')
requirement('pack.bf16_rounding', 'PACR',
  'Deterministic tie-away rounding oracle; stochastic neighbor bounds, same-seed repeatability and different-seed changes.',
  'tests/movement/packer/test_pack.py::test_deterministic_and_stochastic_bf16_format_conversion',
  'Does not prove distribution/unbiasedness or SFPU stochastic-round instruction behavior.')
requirement('pack.fp8', 'PACR',
  'E4M3 normal payloads, tail padding limits and explicit mantissa truncation oracle.',
  'tests/movement/packer/test_pack_fp8.py::test_fp8_pack_runtime_tail tests/movement/packer/test_pack_fp8.py::test_fp8_pack_truncates_mantissa tests/movement/packer/test_pack_fp8.py::test_fp8_pack_zero_and_subnormal_values',
  'Subnormal-preservation expectation is a strict expected failure, not a passing contract. Other formats and edge cases remain.')
requirement('pack.scatter', 'PACR',
  'One/four interfaces, contiguous/reverse/irregular/repeated Dst order, both Dst and output formats, exact tails and wrapping output CB.',
  'tests/movement/packer/test_scatter_formats.py::test_scatter_pack_formats_and_order tests/movement/packer/test_scatter_formats.py::test_scatter_pack_exact_tail tests/movement/packer/test_scatter_formats.py::test_scatter_pack_wrapping_cb',
  'Other context/address/format combinations, compression and stream-driven packing remain.')
requirement('pack.l1_accumulation', 'PACR',
  'Repeated writes accumulate values at reused L1 destinations for FP32/BF16 and several lengths.',
  'tests/movement/packer/test_l1_accumulation.py::test_l1_accumulation',
  'Overflow, saturation, exceptional values and other accumulation configurations remain.')
requirement('unpack.paths', 'UNPACR MOVA2D MOVB2D',
  'Direct-to-Dst and source-mediated paths, exact FP32 precision checks, BF16 source placement, full/partial runtime counts and both unpackers.',
  'tests/movement/unpacker/test_unpack.py::test_unpack_f32_row_major_to_each_dst_tile tests/movement/unpacker/test_unpack.py::test_partial_unpack_to_dst_uses_a_runtime_bounded_mop tests/movement/unpacker/test_unpack.py::test_unpack_bf16_row_major_tile_to_source_bank tests/movement/unpacker/test_unpack.py::test_parallel_unpack_places_two_row_major_tiles_in_srca_and_srcb tests/movement/unpacker/test_dst_paths.py::test_l1_to_dst_paths tests/movement/unpacker/test_dst_paths.py::test_dst_path_precision',
  'Full format/context/broadcast/transpose/tilize/cache-flush and address-counter semantics remain.')
requirement('unpack.fp8', 'UNPACR',
  'E4M3 source-bank payloads, parallel banks and conversion paths, including explicit subnormal cleanup comparison.',
  'tests/movement/unpacker/test_unpack_fp8.py::test_fp8_source_bank tests/movement/unpacker/test_unpack_fp8.py::test_fp8_parallel_source_banks tests/movement/unpacker/test_unpack_fp8.py::test_fp8_host_subnormal_cleanup_is_redundant',
  'Expected failures and normal-only input selections must remain visible. No claim for all FP8 encodings.')
requirement('transport.prefixes', 'UNPACR PACR',
  'Independent payload and poison guards for every configured runtime prefix; checks unowned source/Dst preservation.',
  'tests/operation_pocs/transport/test_transport.py::test_pack_all_prefixes tests/operation_pocs/transport/test_source.py::test_source_prefixes tests/operation_pocs/transport/test_dst.py::test_dst_prefixes tests/operation_pocs/transport/test_edges.py::test_signed_and_rounding_edges',
  'TRANSPORT_LENGTHS can restrict the sweep; evidence must record the environment. Narrow format/recipe scope, not general modifiers.')
requirement('transport.scatter', 'UNPACR',
  'Scattered source allocations and matrix pairs, native and staged paths, scattered Dst output with independent layout oracle.',
  'tests/operation_pocs/transport/test_scatter_unpack.py::test_scattered_source_unpack tests/operation_pocs/transport/test_scatter_unpack.py::test_scattered_matrix_pairs tests/operation_pocs/transport/test_scatter_unpack.py::test_native_scattered_source_unpack tests/operation_pocs/transport/test_scatter_unpack.py::test_native_scattered_matrix_pairs tests/operation_pocs/transport/test_scatter_unpack.py::test_scattered_dst_unpack',
  'Selected address recipes do not prove complete address-counter/context semantics.')
requirement('sync.semaphores', 'SEMINIT SEMPOST SEMGET SEMWAIT',
  'Selected semaphore counts, untouched sentinel semaphore, ready/space conditions and a delayed peer proof that waits really block.',
  'tests/operation_pocs/runtime/test_runtime.py::test_semaphore_primitive tests/operation_pocs/runtime/test_runtime.py::test_semaphore_blocking',
  'All masks, saturation boundaries, maxima and resource-mask combinations need additional tests.')
requirement('sync.source_flags', 'UNPACR_NOP CLEARDVALID STALLWAIT',
  'Repeated source publish/wait/release cycles preserve payload; delayed peer checks wait-valid blocking for A and B.',
  'tests/operation_pocs/runtime/test_runtime.py::test_source_flags tests/operation_pocs/runtime/test_runtime.py::test_source_flag_blocking',
  'Not all source-bank selectors, clear modes or STALLWAIT resource masks. Completion alone does not prove every flag transition.')
requirement('sync.all_masks_saturation', 'SEMINIT SEMPOST SEMGET',
  'All 256 semaphore masks on all three issuing threads; empty-mask no-op, unselected semaphore preservation, zero/fifteen saturation and increment past configured Max.',
  'tests/isa/test_sync.py::test_semaphore_masks_saturation',
  'Boundary Value/Max pairs are selected, not exhaustive. Concurrent updates and all Max values remain.')
requirement('sync.combined_wait_conditions', 'SEMWAIT SEMINIT',
  'Condition masks 1/2/3, both endpoints for combined condition, several multi-semaphore masks and all directed thread-cycle pairs. Partial peer release must not unblock before the last selected semaphore becomes ready.',
  'tests/isa/test_sync.py::test_semaphore_wait_all_conditions',
  'Only the Sync block bit is used. Other resource block masks, wait replacement and zero BlockMask remain.')
requirement('sync.mutex_exclusion', 'ATGETM ATRELM',
  'All four valid Blackhole mutex indices; two/three contending threads increment shared memory under the mutex with an exact final-count oracle; same-owner reacquisition must allow one release.',
  'tests/isa/test_sync.py::test_mutex_exclusion',
  'Round-robin fairness and release by a non-owner remain. Invalid mutex indices intentionally hang and are not executed.')
requirement('sfpu.cast_rounding', 'SFPCAST',
  'Integer-to-FP32 nearest-even rounding at representability boundaries and ties, both signs including negative zero; stochastic results must be adjacent representable neighbors. Checks aliases, masks and raw 32-bit results.',
  'tests/isa/test_sfpu_cast.py::test_cast_integer_to_float',
  'Stochastic probability distribution, exact PRNG sequence and reduced PRNG precision are not proved by neighbor bounds.')
