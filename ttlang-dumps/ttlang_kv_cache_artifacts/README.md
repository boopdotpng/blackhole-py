# TT-Lang KV Cache Store Probe

This directory captures a compile-only TT-Lang data-movement probe for storing
one packed K/V tile slice into Llama's per-layer cache layout:

- `k_in`, `v_in`: `(8, 32, 64)` bf16, interpreted as one token tile for 8 KV heads.
- `k_cache`, `v_cache`: `(8, 8192, 64)` bf16.
- Grid: `(head_dim_tiles=2, kv_heads=8)`.

`kv_cache_store_static.py` uses a static `STORE_START_TILE = 7`. TT-Lang tensor
subscripts can use constants and core-derived expressions, but this frontend does
not expose an ordinary runtime scalar kernel argument for `start_pos`. A fully
dynamic store slice such as `cache[kv_head, start_pos_tile, dim_tile]` is
therefore not expressed cleanly here. The generated MLIR/C++ is still useful for
the packed cache addressing and NOC read/write pattern.

The probe uses the TT-Lang interop-required three-thread shape: `dm_read`,
pass-through `compute`, and `dm_write`. The compute kernel only forwards the tile
through a DFB so the writer can produce the cache-store C++.

No hardware execution was run. This compile-only path generated MLIR and kernel
C++ only; no matching ELF disassembly was produced for this probe.

Compile command used:

```sh
cd /home/boop/tenstorrent/tt-lang
source build-gcc/env/activate
TTLANG_COMPILE_ONLY=1 \
TTLANG_DUMP_ARTIFACTS_DIR=/home/boop/tenstorrent/blackhole-py/ttlang-dumps/ttlang_kv_cache_artifacts \
TTLANG_INITIAL_MLIR=/home/boop/tenstorrent/blackhole-py/ttlang-dumps/ttlang_kv_cache_artifacts/initial.mlir \
TTLANG_FINAL_MLIR=/home/boop/tenstorrent/blackhole-py/ttlang-dumps/ttlang_kv_cache_artifacts/final.mlir \
python /home/boop/tenstorrent/blackhole-py/ttlang-dumps/ttlang_kv_cache_artifacts/kv_cache_store_static.py
```
