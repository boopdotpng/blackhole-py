# components list

list of primitive components that need to be individually validated.

scope: the local operations needed for transformer / MoE / MLA / KDA / DeltaNet inference and training, including supervised training, PPO / GRPO, sampling and AdamW. distributed collectives are out of scope.

## movement
- [x] read(base, logical_offset, dst, byte_count) — read an exact byte range from interleaved DRAM into L1
- [x] write(base, logical_offset, src, byte_count) — write an exact byte range from L1 into interleaved DRAM
- [x] send(cb, dst_cores, page_count, last_page_bytes) — unicast or multicast ready CB pages to remote cores
- [x] atomic_inc(dst_core, address, increment, return_value=False) — atomically increment a remote L1 counter, optionally returning its old value

all externally visible tensors and all L1 tensor buffers remain row-major. there are no device tilize / untilize kernels in this bring-up. unpacker / src / dst hardware layouts are internal staging details and every result is packed back to row-major L1.

### unpacker
- [x] unpack N bytes to dst at a chosen offset (including an entire tile; direct-Dst hardware granularity is one 16-element / 64-byte f32 row)
- [x] unpack tile to srcA
- [x] unpack tile to srcB
- [x] unpack 2 tiles to srcA / srcB (parallel unpacker programming; measured faster than two individual unpacks—see `tests/movement/unpacker/README.md`)

srca and srcb are one tile each, and partial fills will just fill top left to bottom right; not sure how the address counters and etc need to be set up for this.

dst is always f32 for these kernels. we need to track which region each value occupies. we fill tiles left to right and you write from top to bottom contiguously in a tile.

address counter programming is inferred from the requested region.

### packer
- [x] dst to CB (N elements at a chosen 16-element dst-row offset to any CB, including partial and full tiles; BF16 and F32 output)
- [x] packer_relu_clamp_n(N, mode, upper) — proof-of-concept for the packer's activation stage. mode = relu computes max(x, 0); mode = clamp computes clamp(x, 0, upper) with MAX_THRESHOLD_RELU. test values below zero, at zero, inside the interval, at upper and above upper; include partial outputs and a nonzero dst offset
- [x] dst to CB with deterministic and stochastic FP32-to-BF16 format-conversion rounding (seeded stochastic output is reproducible; see `tests/movement/packer/README.md` for cycle samples)

the packer clamp is only the fused output operation `clamp(x, 0, upper)`, where upper is nonnegative. arbitrary lower / upper clipping remains an SFPU compare-and-select operation.

### fpu to sfpu moves
dst into sfpu (N elements). lane masking and predicates are inferred from N. SFPLOAD
SFPLOADI (for intermediates) is also counted here

SFPU back into dst (N elements, same inferred lane predicates)

lane predicates apply to moves and compute automatically. explicit comparisons still determine which values a select chooses.

srcA to dst tile N
srcB to dst tile N

dst to srcA
dst to srcB
(all for N elements, including partial and full tiles).

movements within sfpu

moves from srcA or srcB to sfpu need to go through dst, we can just express that directly instead of having a meta-expression for that.

### sfpu move kernels

- sfpu_copy_n — copy N values between LRegs, store the result
- sfpu_constant_n — fill N values with a constant
- sfpu_rotate_n(N, shift, group_width) — rotate values within each group
- sfpu_shift_lanes_right_1_n — shift values right by one position within each eight-lane group and insert zero at the start of each group. unlike rotate, the value at the end does not wrap around. repeated shift-and-add stages form an inclusive prefix scan; carries between groups are handled explicitly by the lowering
- sfpu_transpose — transpose the values across four LRegs
- sfpu_broadcast_n — broadcast one selected value to N outputs

## compute

each bullet in a primitive section is one kernel. sizes and offsets are parameters, not different kernels. lane predicates, padding, address stepping and instruction repetition are inferred during lowering. nothing outside the requested output region should change.

numeric tensor input and output is row-major bf16, with no host or device tilization. fpu accumulation is always f32. matmul and multiply use HiFi2; LoFi is not a supported BF16 path in these tests. add / subtract do not need multiply fidelity phases. other tensor data types and fidelity choices will be added after BF16 inference bring-up.

bf16 applies to numeric values. embedding / gather / scatter IDs, sort / search / argmax / top-k indices, masks and raw RNG bits are integer metadata, not bf16 values. generate selection indices on device and verify integer outputs exactly.

N means logical elements, not hardware lanes. run the _n kernels with N = 1, 7, 8, 9, 15, 16, 17, 31, 32, 33, 127, 128, 129, 137, 1024, 2048.

ELWMUL / ELWADD / ELWSUB operate on aligned 8x16 blocks (128 elements minimum), not N individual lanes. sfpu predicates do not mask fpu instructions.

for fewer than 128 elements, or a tail, test both paths separately:
- elwmul_n / elwadd_n / elwsub_n: pad operands on device, run the fpu on a full 8x16 scratch region, copy / pack only the valid results. do not overwrite neighboring live dst values
- sfpu_mul_n / sfpu_add_n / sfpu_sub_n: run in sfpu with inferred lane predicates on the final partial footprint

use the same logical inputs for both. do not silently turn an elwmul test into an sfpu test. compare each against a reference with its numerical tolerance, not assumed bit-identical results between engines. start with explicit zero padding in L1; a short unpack by itself does not prove the unused source values are zero.

### fpu kernels

- matmul(M, N, K, accumulate=False, transpose_b=False) — A[M,K] @ B[K,N] -> dst[M,N], or A @ B.T with B[N,K]
- matmul_batched(B, M, N, K) — B independent products with different operands
- matmul_k_chunks(C) — accumulate C products A[8,16] @ B[16,16] into the same dst[8,16], keep the result in f32 until the final pack
- elwmul_n(N, accumulate=False) — A * B, optionally added to existing f32 dst
- elwadd_n(N, accumulate=False) — A + B, optionally added to existing f32 dst
- elwsub_n(N, accumulate=False) — A - B, optionally added to existing f32 dst
- elw_broadcast_row(R, C, op) — A[R,C] op B[1,C], op = add / multiply
- elw_broadcast_column(R, C, op) — A[R,C] op B[R,1], op = add / multiply
- elw_broadcast_scalar(N, op) — A[N] op scalar, op = add / multiply
- fpu_reduce_sum(R, C, axis) — BF16 sum along rows, columns or the entire input, using the matrix-unit reduction path and f32 accumulation
- fpu_reduce_max(R, C, axis) — BF16 maximum along rows, columns or the entire input, using GMPOOL where its 16x16 column reduction applies and SFPU composition for remaining stages
- fpu_reduce_argmax(R, C, axis) — value and integer index, using GMPOOL's native partial argmax only where its restricted layout is applicable and SFPU compare-exchange elsewhere

the broadcast operand is in srcB. row means repeat B[1,C] down the rows; column means repeat B[R,1] across the columns; scalar means repeat one value everywhere. this is operand selection in the fpu, not a fully expanded B tensor.

broadcast runs, each for add and multiply:
- row: A[8,16] op B[1,16], then A[32,32] op B[1,32], then A[3,5] op B[1,5]
- column: A[8,16] op B[8,1], then A[32,32] op B[32,1], then A[3,5] op B[3,1]
- scalar: 1 / 15 / 128 / 137 / 1024 elements op one value

use different values per row / column. the 32x32 cases check selection across face boundaries; the 3x5 and 137-element cases check broadcasting with padding. inputs stay compact and row-major; any staging is on device. put sentinels around the valid output to catch extra writes.

matmul runs:
- M=8, N=16, K=16 (one 8x16 output block)
- M=8, N=8, K=16, transpose_b=True (two 8x16 inputs)
- M=32, N=32, K=32 (full tile)
- M=8*B, N=16, K=16, B = 1, 2, 3, 5, 8, 9, 17 (B output blocks sharing one right operand)
- M=5, N=11, K=13 (partial rows, columns and K)
- repeat these with a nonzero initial dst and accumulate=True
- matmul_batched and matmul_k_chunks with B / C = 1, 2, 3, 5, 8, 9, 17

### dst kernels

- zero_dst_n — zero N values at a chosen dst offset, preserve everything else
- zero_src_n(bank) — zero N values in srcA / srcB, copy out both banks to check the result
- dst_roundtrip_n — unpack bf16, copy through f32 dst, pack back to bf16
- dst_offset_n(op) — copy / add / multiply N values at a nonzero dst offset, preserving neighboring values

### sfpu arithmetic kernels

bf16 data is expanded for sfpu arithmetic and packed back to bf16. integer / bit operations use internal lane values, not integer input buffers.

- sfpu_add_n — a + b
- sfpu_sub_n — a - b
- sfpu_mul_n — a * b
- sfpu_mad_n — a * b + c
- sfpu_add_scalar_n — a + constant
- sfpu_mul_scalar_n — a * constant
- sfpu_neg_n — -a
- sfpu_abs_n — native floating-point absolute value with SFPABS
- sfpu_minmax_n — use SFPSWAP to produce both the lane-wise minimum and maximum simultaneously
- sfpu_compare_n(compare) — produce one boolean / integer mask per element; compare = eq / ne / lt / le / gt / ge
- sfpu_select_n — select either of two values from a boolean / integer mask; arbitrary clipping uses compare + select
- sfpu_integer_n(op) — signed and unsigned 32-bit integer add / subtract
- sfpu_mul23_n(part) — unsigned 23-bit by 23-bit multiply using SFPMUL24; part = low / high selects which 23 bits of the product are returned. this is not a general 32-bit integer multiply
- sfpu_integer_compare_n(compare) — signed and unsigned eq / ne / lt / le / gt / ge
- sfpu_bitwise_n(op) — and / or / xor / not
- sfpu_bitshift_n(direction, bits) — shift the bits within each value, not the lanes
- sfpu_exponent_n — extract each value's exponent
- sfpu_mantissa_n — extract each value's mantissa
- sfpu_set_exponent_n — replace each value's exponent
- sfpu_set_mantissa_n — replace each value's mantissa
- sfpu_set_sign_n — replace / flip each value's sign
- sfpu_scale_pow2_n — add a constant to each floating-point exponent with SFPDIVP2, implementing multiplication by an integer power of two in one instruction
- sfpu_cast_n(conversion, rounding) — convert between internal f32 / bf16-representable values and 32-bit integer lane values; include halfway, overflow, underflow and saturating integer-conversion cases

full 32-bit integer multiplication is not an SFPU primitive. use scalar RISC-V multiplication, a future T2 RVV path, or a multi-part software sequence when it is actually required.

### sfpu reduction kernels

- sfpu_butterfly_n(N, distance, group_width) — one rotate-and-add step, distances 1 / 2 / 4

### sfpu selection kernels

- sfpu_compare_exchange_n — compare N pairs of values with SFPSWAP, keeping each original integer index attached when values swap. larger value first; equal values use the smaller original index first

SFPSWAP and the native compare instructions use the device's total ordering for floating-point bit patterns. explicitly test positive / negative zero, infinities and NaNs instead of assuming host IEEE min / max behavior.

### sfpu lookup-table kernel

- sfpu_lut_n(table_format, retain_sign) — evaluate the native SFPLUT / SFPLUTFP32 piecewise-linear function. for the current BF16 bring-up, test packed 8-bit coefficients, FP32 three-entry tables and sign-retaining mode

the LUT is a small programmable piecewise-linear evaluator, not a memory lookup table. it selects coefficients from three or six magnitude ranges and computes `a * abs(x) + b` in one SFPU instruction, optionally restoring the input sign. range reduction plus this kernel provides a fast approximation path for activations and unusual scalar functions without adding one primitive per function.

### sfpu special-function kernels

- sfpu_reciprocal_n — 1/x; use the one-cycle SFPARECIP estimate and Newton refinement for the requested BF16 accuracy
- sfpu_rsqrt_n — 1/sqrt(x); construct a bit-level initial estimate with integer shift / subtract operations and refine it with MADs
- sfpu_exp2_n — 2^x; split x into integer and fractional parts with cast / rounding, approximate the fractional part with MAD or LUT, and construct the power-of-two part with exponent operations
- sfpu_log2_n — log2(x); extract the exponent, normalize the mantissa, approximate the normalized mantissa with MAD or LUT, then add the exponent

these are software SFPU kernels rather than single native transcendental instructions. natural exponential lowers to `exp2(x * log2(e))`, and natural logarithm lowers to `log2(x) * ln(2)`. division uses multiply by reciprocal and square root uses multiply by reciprocal-square-root, with explicit zero, negative, infinity and NaN tests.

### random kernels

- hardware_rng_bits_n(N, seed) — expose the per-lane SFPU hardware PRNG. identical seeds reproduce exactly. use this fast path only where its weak statistical quality is acceptable, and test its actual sequence separately from distribution-level tests
- threefry_rng_bits_n(N, seed, counter) — counter-based random integer bits using repeated add, xor and rotate rounds. identical seed / counter pairs reproduce exactly and disjoint counter ranges do not overlap

Threefry treats the seed as a key and each logical element number as a counter, then mixes them with a fixed sequence of modular 32-bit additions, xor operations and rotations. it therefore does not require general SFPU integer multiplication and lets any element's random bits be regenerated independently without maintaining mutable PRNG state.

### sfpu issue / throughput kernel

- sfpu_loadmacro_n — configure SFPLOADMACRO and prove a fused load + arithmetic + round / move + store schedule, compare against the same unfused SFPU sequence and record cycles for both. include dependency delays, an inactive final-lane predicate and repeated invocations after configuration

SFPLOADMACRO is a scheduling primitive rather than a new mathematical operation. an ordinary SFPU instruction can feed only one subunit per cycle; a configured load macro can load dst and schedule work on the simple, MAD, round and store subunits concurrently. lowerings may use it after correctness is established to avoid leaving most of the SFPU pipeline idle.

## random config writes and risc-v
