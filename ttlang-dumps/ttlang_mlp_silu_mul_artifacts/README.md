# TT-Lang Llama MLP SiLU-Mul Dump

Focused TT-Lang dump for the Llama MLP post-projection elementwise operation:

```python
hidden = gate.silu() * up
```

The workload in `mlp_silu_mul.py` compiles a 1x4 tile slice of the MLP hidden
dimension in `TTLANG_COMPILE_ONLY=1` mode using host TTNN tensors, so it does not
execute on Tenstorrent hardware.

Generated with:

```sh
cd /home/boop/tenstorrent/tt-lang
source build-gcc/env/activate
TTLANG_COMPILE_ONLY=1 \
TTLANG_INITIAL_MLIR=/home/boop/tenstorrent/blackhole-py/ttlang-dumps/ttlang_mlp_silu_mul_artifacts/initial.mlir \
TTLANG_FINAL_MLIR=/home/boop/tenstorrent/blackhole-py/ttlang-dumps/ttlang_mlp_silu_mul_artifacts/final.mlir \
TTLANG_DUMP_ARTIFACTS_DIR=/home/boop/tenstorrent/blackhole-py/ttlang-dumps/ttlang_mlp_silu_mul_artifacts \
python /home/boop/tenstorrent/blackhole-py/ttlang-dumps/ttlang_mlp_silu_mul_artifacts/mlp_silu_mul.py \
  > /home/boop/tenstorrent/blackhole-py/ttlang-dumps/ttlang_mlp_silu_mul_artifacts/compile.log 2>&1
```

Key lowering points:

- `initial.mlir` contains `ttl.silu` followed by `ttl.mul`.
- `final.mlir` and `trisc.cpp` lower the fused compute block to `silu_tile`
  followed by `mul_binary_tile`.
- `ncrisc.cpp` reads gate/up tiles and `brisc.cpp` writes hidden tiles.
