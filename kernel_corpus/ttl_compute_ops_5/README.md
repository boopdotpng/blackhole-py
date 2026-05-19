# TTL Compute Ops Corpus

This folder is a five-kernel C++ corpus for expanding the `blackhole-py` mixin layer. The kernels are intentionally grouped by lowering style rather than by one-op-per-file, because the compute path is mostly a small set of repeated patterns:

- CB lifecycle: `cb_wait_front`, `cb_reserve_back`, `cb_push_back`, `cb_pop_front`
- DST lifecycle: `tile_regs_acquire`, `tile_regs_commit`, `tile_regs_wait`, `tile_regs_release`
- Tile movement: `copy_tile_init`, `copy_tile`, `pack_tile`
- SFPU unary ops: `*_tile_init`, `*_tile`
- SFPU/FPU binary ops: `*_binary_tile_init`, `*_binary_tile`, `binary_max/min_tile`
- Structural ops: `unary_bcast`, `transpose_wh_tile`, `fill_tile`, `typecast_tile`
- Higher-level math: `reduce_init/reduce_tile/reduce_uninit`, `mm_init/matmul_tiles`, `pack_reconfig_l1_acc`

## Files

1. `01_binary_arith_minmax.cpp`
   - Covers `add`, `sub`, `mul`, `div`, `max`, `min`.
   - Writes six result tiles to output CB 16.

2. `02_unary_math_trig.cpp`
   - Covers `exp`, `exp2`, `log`, `sqrt`, `rsqrt`, `recip`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan`.
   - Writes twelve result tiles to output CB 16.

3. `03_activations_rounding_misc.cpp`
   - Covers `tanh`, `abs`, `neg`, `relu`, `sigmoid`, `floor`, `ceil`, `sign`, `gelu`, `silu`, `hardsigmoid`, `expm1`, `square`, `softsign`, `signbit`, `frac`, `trunc`.
   - Writes seventeen result tiles to output CB 16; `trunc` is split into a second DST acquisition so the example avoids using DST index 16.

4. `04_structural_fill_cast_bcast_transpose.cpp`
   - Covers `broadcast`, `transpose`, `fill`, `typecast`.
   - Writes six result tiles to output CB 16.

5. `05_reduce_matmul_accumulate.cpp`
   - Covers `reduce_sum`, `reduce_max`, `matmul`, and the L1 accumulation packer path used by accumulated stores.
   - Writes sum/max/matmul tiles to output CB 16 and an accumulated tile to CB 24.

## Porting Targets

For `blackhole-py/ttk/mixins`, this corpus suggests these next mixin families:

- `ComputeCbMixin`: wait/reserve/push/pop for compute CBs.
- `DstRegsMixin`: acquire/commit/wait/release.
- `TileMoveMixin`: copy tile to DST and pack DST to CB.
- `SfpuUnaryMixin`: all `*_tile_init` and `*_tile` unary functions.
- `SfpuBinaryMixin`: add/sub/mul/div/max/min binary tile functions.
- `StructuralTileMixin`: broadcast, transpose, fill, typecast.
- `ReduceMixin`: reduce init/tile/uninit for sum/max row/col/scalar.
- `MatmulMixin`: `mm_init`, `matmul_tiles`, later `mm_block_init` and `matmul_block`.
- `L1AccumMixin`: `pack_reconfig_l1_acc` and safe accumulation guard patterns.

These kernels are a source/API corpus, not a checked-in TT program. Some calls are directly observed in tt-lang emitted C++ (`cb_*`, `tile_regs_*`, `copy_tile`, `exp_tile`, `sqrt_tile`, `add_binary_tile`, `pack_tile`); the remaining calls come from the local Metal compute API headers under `blackhole-py-old/tt-metal-deps/include/tt_metal/include/compute_kernel_api`.
