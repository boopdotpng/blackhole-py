#!/usr/bin/env python3
"""Compile-only TT-Lang probe for GQA K/V head repeat data movement.

Each core handles one `(query_head, head_dim_tile)` pair and maps the query head
to the source KV head with `query_head // 4`, matching the Llama 3.2 1B
32-query-head / 8-KV-head GQA repeat rule.
"""

import os

os.environ["TTLANG_COMPILE_ONLY"] = "1"

import torch
import ttnn
import ttl


TILE = 32
ATTN_HEADS = 32
KV_HEADS = 8
GQA_REPEAT = ATTN_HEADS // KV_HEADS
HEAD_DIM = 64
HEAD_DIM_TILES = HEAD_DIM // TILE
CACHE_LEN = 8192
READ_START_TILE = 7


@ttl.operation(grid=(HEAD_DIM_TILES, ATTN_HEADS), memory_space="DRAM")
def gqa_repeat_static(k_cache, v_cache, k_repeated, v_repeated):
    k_dfb = ttl.make_dataflow_buffer_like(k_cache, shape=(1, 1), block_count=2)
    v_dfb = ttl.make_dataflow_buffer_like(v_cache, shape=(1, 1), block_count=2)
    k_repeat_dfb = ttl.make_dataflow_buffer_like(k_repeated, shape=(1, 1), block_count=2)
    v_repeat_dfb = ttl.make_dataflow_buffer_like(v_repeated, shape=(1, 1), block_count=2)

    @ttl.compute()
    def compute():
        with k_dfb.wait() as k_in_blk:
            with k_repeat_dfb.reserve() as k_out_blk:
                k_out_blk.store(k_in_blk)
        with v_dfb.wait() as v_in_blk:
            with v_repeat_dfb.reserve() as v_out_blk:
                v_out_blk.store(v_in_blk)

    @ttl.datamovement()
    def dm_read():
        dim_tile, query_head = ttl.node(dims=2)
        kv_head = query_head // GQA_REPEAT
        with k_dfb.reserve() as k_blk:
            ttl.copy(k_cache[kv_head, READ_START_TILE, dim_tile], k_blk).wait()
        with v_dfb.reserve() as v_blk:
            ttl.copy(v_cache[kv_head, READ_START_TILE, dim_tile], v_blk).wait()

    @ttl.datamovement()
    def dm_write():
        dim_tile, query_head = ttl.node(dims=2)
        with k_repeat_dfb.wait() as k_blk:
            ttl.copy(k_blk, k_repeated[query_head, 0, dim_tile]).wait()
        with v_repeat_dfb.wait() as v_blk:
            ttl.copy(v_blk, v_repeated[query_head, 0, dim_tile]).wait()


def main():
    def tt_tensor(shape):
        return ttnn.from_torch(
            torch.zeros(shape, dtype=torch.bfloat16),
            dtype=ttnn.bfloat16,
            layout=ttnn.TILE_LAYOUT,
        )

    k_cache = tt_tensor((KV_HEADS, CACHE_LEN, HEAD_DIM))
    v_cache = tt_tensor((KV_HEADS, CACHE_LEN, HEAD_DIM))
    k_repeated = tt_tensor((ATTN_HEADS, TILE, HEAD_DIM))
    v_repeated = tt_tensor((ATTN_HEADS, TILE, HEAD_DIM))
    gqa_repeat_static(k_cache, v_cache, k_repeated, v_repeated)


if __name__ == "__main__":
    main()
