# TT-Lang GQA Repeat Probe

This directory captures a compile-only TT-Lang data-movement probe for reading
packed K/V cache heads and materializing the Llama GQA repeat pattern:

- Query heads: 32.
- KV heads: 8.
- Repeat factor: 4.
- Mapping: `kv_head = query_head // 4`.
- Cache tensors: `(8, 8192, 64)` bf16.
- Repeated output tensors: `(32, 32, 64)` bf16 for one token tile.
- Grid: `(head_dim_tiles=2, query_heads=32)`.

The probe uses static `READ_START_TILE = 7`, for the same reason as the KV-cache
store probe: TT-Lang tensor subscripts can use constants and core-derived
expressions, but this frontend does not expose a plain runtime scalar argument
for dynamic cache position. Attention readers should ultimately avoid
materializing `k_repeated`/`v_repeated` and instead apply this `query_head // 4`
mapping inside the score/value readers.

The probe uses the TT-Lang interop-required three-thread shape: `dm_read`,
pass-through `compute`, and `dm_write`. The compute kernel only forwards the tile
through a DFB so the reader/writer data-movement kernels expose the GQA addressing.

No hardware execution was run. This compile-only path generated MLIR and kernel
C++ only; no matching ELF disassembly was produced for this probe.

Compile command used:

```sh
cd /home/boop/tenstorrent/tt-lang
source build-gcc/env/activate
TTLANG_COMPILE_ONLY=1 \
TTLANG_DUMP_ARTIFACTS_DIR=/home/boop/tenstorrent/blackhole-py/ttlang-dumps/ttlang_gqa_repeat_artifacts \
TTLANG_INITIAL_MLIR=/home/boop/tenstorrent/blackhole-py/ttlang-dumps/ttlang_gqa_repeat_artifacts/initial.mlir \
TTLANG_FINAL_MLIR=/home/boop/tenstorrent/blackhole-py/ttlang-dumps/ttlang_gqa_repeat_artifacts/final.mlir \
python /home/boop/tenstorrent/blackhole-py/ttlang-dumps/ttlang_gqa_repeat_artifacts/gqa_repeat_static.py
```
