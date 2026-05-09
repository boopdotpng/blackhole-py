# Emulator Test Coverage Notes

This file tracks instruction and runtime coverage gaps for `blackhole-py/emu`,
with an emphasis on workloads that can be compiled without executing on a real
device.

## Current Local Coverage

`emu/tests/test_kernels.py` exercises the raw-kernel path with generated C++
kernels and emulator execution:

- Data movement through interleaved DRAM tile reads/writes.
- CB reserve/wait/push/pop paths for normal and non-default CB indices.
- Larger CB page counts and high CB indices, including `c_3 -> c_19` and
  `c_7 -> c_31` copy paths.
- BF16 and FP16 pack/unpack round trips.
- SFPU scalar add/mul variants through `add_unary_tile` and `mul_unary_tile`,
  including negative, half-scale, affine, scale+bias, and zero-add cases.
- FPU binary add/sub/mul through `add_tiles`, `sub_tiles`, and `mul_tiles`.
- Multi-tile producer/consumer flow on a single core for unary and binary
  workloads.
- Emulator-native multi-core raw `add1` smoke coverage for 1-core and 4-core
  launches.
- Matmul peak smoke coverage, including multicast/semaphore-heavy dataflow.
- Firmware boot plus dispatch return-kernel smoke coverage, including launch
  message completion state.

`test_noc_atomic_opcodes` and
`test_noc_l1_acc_atomic_instruction_selects_opcode` cover the emulator's NIU
atomic model directly, without compiling kernels or touching hardware:

- `INCR_GET`
- `INCR_GET_PTR`
- `CAS` low 16-bit
- `STORE_IND`
- `SWAP_4B`
- L1 accumulator atomic opcode selection through `NIU_L1_ACC_AT_INSTRN`

`emu/dump_raw_kernel_cases.py` writes the raw-kernel corpus to
`emu/raw_kernel_cases.json`.  The file includes C++ source for each role plus
CB address/size/page metadata, and compiling it does not execute on device.
The current corpus contains:

- SFPU scalar/affine/scale-bias unary cases.
- FPU add/sub/mul binary cases.
- BF16 and FP16 copy/pack/unpack cases.
- Multi-tile unary and binary cases for 3 and 5 tiles.
- Larger-page and non-default-CB copy cases.

## Gaps To Fill

### NOC

The direct tests cover the functional atomic cases implemented in
`emu/noc.py`, but real generated kernels should still be collected for:

- `noc_semaphore_inc`, `noc_semaphore_set`, and multicast semaphore variants.
- Atomic barrier/flush sequences around atomics, especially
  `noc_async_atomic_barrier`.
- Multicast atomics with and without source inclusion.
- Remote CB paths from `remote_circular_buffer.h`, because those stress NOC
  atomics plus CB pointer updates together.
- Inline writes on Blackhole fallback paths, where APIs may emit normal writes
  instead of hardware inline writes.

### FPU

Current raw workloads hit elementwise add/sub/mul and basic matmul smoke.
Additional generated kernels should cover:

- Accumulating matmul and L1 accumulation stores.
- Reduce ops, especially max/sum and row/column variants.
- Broadcast variants that lower to FPU or mixed FPU/SFPU sequences.
- Copy/dst multi-consumer patterns that move values between DST and CBs.
- F32 destination accumulation and full/half DST sync variants.

### SFPU

The local raw cases cover scalar add/mul variants. The emulator has SFPU support
for many less common instructions, so grab generated kernels that use:

- Unary math beyond the covered `exp`/`sqrt` path: `log`, `rsqrt`, `recip`,
  `gelu`, `silu`, `sigmoid`, `erf`/`erfc`, `i0`, clamp/relu family, softplus,
  and logsigmoid.
- Predication/control: condition set/enable, push/pop/complement condition,
  and predicated stores.
- Bit/integer operations: abs, set sign, shifts, logical and/not/xor/or,
  integer add, cast, stochastic round, exponent/mantissa extraction, set exp,
  div-by-power-of-two, and LUT/approx reciprocal instructions.
- Fused post-op chains that switch SFPU init families inside one compute body.

## What To Grab From Generated Kernels

Save generated kernel bundles in compile-only flows.  The useful inputs are the
C++ kernels and CB config, not device results:

- `test/python/simple_add.py` and `simple_add_multitile.py`: baseline DMA,
  CB sync, and FPU-vs-SFPU binary lowering.
- Fused-kernel variants, useful for SFPU init switching and fused chains.
- `test/python/test_matmul_fused_postops.py` and
  `test_matmul_fused_postop_variants.py`: gelu/relu/scale/bias/div/residual
  post-op coverage.
- `test/python/test_layernorm.py`: reduction plus reciprocal/sqrt-heavy SFPU
  sequences and compiler-allocated DFBs.
- `test/python/test_reduce.py` and `simple_reduce.py`: reduction lowering.
- `test/python/test_matmul_l1_acc.py` and `test_matmul_acc.py`: L1
  accumulation and accumulating matmul.
- `test/python/pipe/scatter.py`, `test/python/pipe/unicast.py`, and
  `test/python/pipe/test_pipe_patterns.py`: multicast/unicast pipe and remote
  synchronization coverage.
- `test/python/test_dst_multi_consumer.py`: DST lifetime and copy patterns.
- `test/python/test_bcast_ops.py`: broadcast lowering variants.

Use emitted kernel bundles or stdout kernel prints. Avoid tests whose only added
value is host/device validation unless they generate a distinct kernel sequence.

## Import Path Into blackhole-py

1. Compile selected generator tests in compile-only mode.
2. Copy or reference the generated C++ sources and manifest/CB metadata.
3. Convert each bundle into a `RawKernelCase` or a new multi-core launch case.
4. Keep direct unit tests for NIU features that generated kernels cannot
   reliably emit.
5. Add an assertion that the generated disassembly contains the target opcode
   family before using the workload as coverage.
