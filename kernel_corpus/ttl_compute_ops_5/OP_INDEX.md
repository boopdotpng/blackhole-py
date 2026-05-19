# TTL Op To Compute API Index

This is the porting-oriented map for the five corpus kernels.

## Common Skeleton

Every compute kernel needs some subset of:

| Role | API calls |
| --- | --- |
| Input CB lifecycle | `cb_wait_front`, `cb_pop_front` |
| Output CB lifecycle | `cb_reserve_back`, `cb_push_back` |
| DST register lifecycle | `tile_regs_acquire`, `tile_regs_commit`, `tile_regs_wait`, `tile_regs_release` |
| CB to DST | `copy_tile_init`, `copy_tile` |
| DST to CB | `pack_tile` |
| SFPU setup | `init_sfpu` |

## TTL Elementwise Ops

| TTL op | Compute API calls |
| --- | --- |
| `add` | `add_binary_tile_init`, `add_binary_tile` |
| `sub` | `sub_binary_tile_init`, `sub_binary_tile` |
| `mul` | `mul_binary_tile_init`, `mul_binary_tile` |
| `div` | `div_binary_tile_init`, `div_binary_tile` |
| `max` | `binary_max_tile_init`, `binary_max_tile` |
| `min` | `binary_min_tile_init`, `binary_min_tile` |
| `exp` | `exp_tile_init`, `exp_tile` |
| `exp2` | `exp2_tile_init`, `exp2_tile` |
| `log` | `log_tile_init`, `log_tile` |
| `sqrt` | `sqrt_tile_init`, `sqrt_tile` |
| `rsqrt` | `rsqrt_tile_init`, `rsqrt_tile` |
| `tanh` | `tanh_tile_init`, `tanh_tile` |
| `abs` | `abs_tile_init`, `abs_tile` |
| `neg` | `negative_tile_init`, `negative_tile` |
| `relu` | `relu_tile_init`, `relu_tile` |
| `sigmoid` | `sigmoid_tile_init`, `sigmoid_tile` |
| `floor` | `rounding_op_tile_init`, `floor_tile` |
| `recip` | `recip_tile_init`, `recip_tile` |
| `sin` | `sin_tile_init`, `sin_tile` |
| `cos` | `cos_tile_init`, `cos_tile` |
| `tan` | `tan_tile_init`, `tan_tile` |
| `asin` | `asin_tile_init`, `asin_tile` |
| `acos` | `acos_tile_init`, `acos_tile` |
| `atan` | `atan_tile_init`, `atan_tile` |
| `ceil` | `rounding_op_tile_init`, `ceil_tile` |
| `sign` | `sign_tile_init`, `sign_tile` |
| `gelu` | `gelu_tile_init`, `gelu_tile` |
| `silu` | `silu_tile_init`, `silu_tile` |
| `hardsigmoid` | `hardsigmoid_tile_init`, `hardsigmoid_tile` |
| `expm1` | `expm1_tile_init`, `expm1_tile` |
| `square` | `square_tile_init`, `square_tile` |
| `softsign` | `softsign_tile_init`, `softsign_tile` |
| `signbit` | `signbit_tile_init`, `signbit_tile` |
| `frac` | `rounding_op_tile_init`, `frac_tile` |
| `trunc` | `rounding_op_tile_init`, `trunc_tile` |

## TTL Structural / Higher-Level Ops

| TTL op | Compute API calls |
| --- | --- |
| `broadcast(..., dims=[0])` | `unary_bcast_init<BroadcastType::ROW>`, `unary_bcast<BroadcastType::ROW>` |
| `broadcast(..., dims=[1])` | `unary_bcast_init<BroadcastType::COL>`, `unary_bcast<BroadcastType::COL>` |
| `broadcast(..., dims=[0, 1])` | `unary_bcast_init<BroadcastType::SCALAR>`, `unary_bcast<BroadcastType::SCALAR>` |
| `reduce_sum(..., dims=[0])` | `reduce_init<PoolType::SUM, ReduceDim::REDUCE_ROW>`, `reduce_tile<PoolType::SUM, ReduceDim::REDUCE_ROW>`, `reduce_uninit` |
| `reduce_sum(..., dims=[1])` | `reduce_init<PoolType::SUM, ReduceDim::REDUCE_COL>`, `reduce_tile<PoolType::SUM, ReduceDim::REDUCE_COL>`, `reduce_uninit` |
| `reduce_sum(..., dims=[0, 1])` | `reduce_init<PoolType::SUM, ReduceDim::REDUCE_SCALAR>`, `reduce_tile<PoolType::SUM, ReduceDim::REDUCE_SCALAR>`, `reduce_uninit` |
| `reduce_max(..., dims=[0])` | `reduce_init<PoolType::MAX, ReduceDim::REDUCE_ROW>`, `reduce_tile<PoolType::MAX, ReduceDim::REDUCE_ROW>`, `reduce_uninit` |
| `reduce_max(..., dims=[1])` | `reduce_init<PoolType::MAX, ReduceDim::REDUCE_COL>`, `reduce_tile<PoolType::MAX, ReduceDim::REDUCE_COL>`, `reduce_uninit` |
| `reduce_max(..., dims=[0, 1])` | `reduce_init<PoolType::MAX, ReduceDim::REDUCE_SCALAR>`, `reduce_tile<PoolType::MAX, ReduceDim::REDUCE_SCALAR>`, `reduce_uninit` |
| `transpose` | `transpose_wh_init`, `transpose_wh_tile` |
| `fill` | `fill_tile_init`, `fill_tile` or `fill_tile_bitcast` |
| `typecast` | `typecast_tile_init<IN_DTYPE, OUT_DTYPE>`, `typecast_tile<IN_DTYPE, OUT_DTYPE>` |
| `matmul` | `mm_init`, `matmul_tiles`; for blocks, later add `mm_block_init`, `matmul_block` |
| accumulated `store` / `+=` | `pack_reconfig_l1_acc`, `pack_tile` |

## Not Currently TTL Elementwise, But Useful Soon

These are not in the current `TTLElementwiseOps.def` surface, but are close to tinygrad-style needs and have local API support:

| Desired op | Likely API calls |
| --- | --- |
| `pow` | `power_binary_tile_init`, `power_binary_tile`, or unary `power_tile_init`, `power_tile` |
| `log2` | `log_with_base_tile_init`, `log_with_base_tile` |
| `where` | `where_tile_init`, `where_tile` from `eltwise_unary/where.h` |
| comparisons | `binary_comp` APIs or unary comparison APIs in `eltwise_unary/comp.h` |
