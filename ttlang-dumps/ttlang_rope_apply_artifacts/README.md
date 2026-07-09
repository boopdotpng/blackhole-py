# TT-Lang RoPE Apply Artifacts

This directory contains TT-Lang-generated dump artifacts for applying Llama
RoPE to Q and K tiles.

Shape assumptions:

- `B = 1`
- `head_dim = 64`, represented as two 32-column tiles
- Q exemplar: `n_heads = 32`, `S = 32`, input/output shape `(1024, 64)`
- K exemplar: `n_kv_heads = 8`, `S = 32`, input/output shape `(256, 64)`
- RoPE tables are not expanded per head: `cos` and `sin` have shape `(S, 64)`
  and are addressed as `row_tile % seq_tiles`.

Math:

```text
x1 = x[..., :32]
x2 = x[..., 32:]
out[..., :32] = x1 * cos[..., :32] - x2 * sin[..., :32]
out[..., 32:] = x2 * cos[..., 32:] + x1 * sin[..., 32:]
```

Files:

- `rope_apply_ttlang.py`: reusable TT-Lang source/capture harness.
- `q_heads32_s32/`: Q compile-only capture.
- `k_heads8_s32/`: K compile-only capture.

Each variant directory contains:

- `initial.mlir`
- `final.mlir`
- `trisc.cpp`
- `ncrisc.cpp`
- `brisc.cpp`
- `manifest.json`
- `compile.log`

The captures were generated with `TTLANG_COMPILE_ONLY=1` through
`tt-device-queue`, using `/home/boop/tenstorrent/tt-lang/build-gcc/env/activate`.
They compile and JIT-register the kernels but do not execute the RoPE kernel.
