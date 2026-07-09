#!/usr/bin/env python3
"""Compile-only TT-Lang probe for Llama KV-cache store data movement.

This models the Llama 3.2 1B cache layout from kernel_list.md:

  K/V input slice:  (8 kv heads, 32 tokens, 64 head-dim)
  K/V cache:        (8 kv heads, 8192 tokens, 64 head-dim)

The store position is intentionally static (`STORE_START_TILE`) because this
TT-Lang frontend has tensor arguments but no ordinary runtime scalar argument for
`start_pos`. The README in this directory records that limitation.
"""

import os

os.environ["TTLANG_COMPILE_ONLY"] = "1"

import torch
import ttnn
import ttl


TILE = 32
KV_HEADS = 8
HEAD_DIM = 64
HEAD_DIM_TILES = HEAD_DIM // TILE
CACHE_LEN = 8192
STORE_START_TILE = 7


@ttl.operation(grid=(HEAD_DIM_TILES, KV_HEADS), memory_space="DRAM")
def kv_cache_store_static(k_in, v_in, k_cache, v_cache):
    k_dfb = ttl.make_dataflow_buffer_like(k_in, shape=(1, 1), block_count=2)
    v_dfb = ttl.make_dataflow_buffer_like(v_in, shape=(1, 1), block_count=2)
    k_store_dfb = ttl.make_dataflow_buffer_like(k_in, shape=(1, 1), block_count=2)
    v_store_dfb = ttl.make_dataflow_buffer_like(v_in, shape=(1, 1), block_count=2)

    @ttl.compute()
    def compute():
        with k_dfb.wait() as k_in_blk:
            with k_store_dfb.reserve() as k_out_blk:
                k_out_blk.store(k_in_blk)
        with v_dfb.wait() as v_in_blk:
            with v_store_dfb.reserve() as v_out_blk:
                v_out_blk.store(v_in_blk)

    @ttl.datamovement()
    def dm_read():
        dim_tile, kv_head = ttl.node(dims=2)
        with k_dfb.reserve() as k_blk:
            ttl.copy(k_in[kv_head, 0, dim_tile], k_blk).wait()
        with v_dfb.reserve() as v_blk:
            ttl.copy(v_in[kv_head, 0, dim_tile], v_blk).wait()

    @ttl.datamovement()
    def dm_write():
        dim_tile, kv_head = ttl.node(dims=2)
        with k_store_dfb.wait() as k_blk:
            ttl.copy(k_blk, k_cache[kv_head, STORE_START_TILE, dim_tile]).wait()
        with v_store_dfb.wait() as v_blk:
            ttl.copy(v_blk, v_cache[kv_head, STORE_START_TILE, dim_tile]).wait()


def main():
    def tt_tensor(shape):
        return ttnn.from_torch(
            torch.zeros(shape, dtype=torch.bfloat16),
            dtype=ttnn.bfloat16,
            layout=ttnn.TILE_LAYOUT,
        )

    k_in = tt_tensor((KV_HEADS, TILE, HEAD_DIM))
    v_in = tt_tensor((KV_HEADS, TILE, HEAD_DIM))
    k_cache = tt_tensor((KV_HEADS, CACHE_LEN, HEAD_DIM))
    v_cache = tt_tensor((KV_HEADS, CACHE_LEN, HEAD_DIM))
    kv_cache_store_static(k_in, v_in, k_cache, v_cache)


if __name__ == "__main__":
    main()
