#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import types
from enum import Enum

os.environ.setdefault("TTLANG_COMPILE_ONLY", "1")

import torch

try:
    import ttnn as _ttnn
except ImportError:
    _ttnn = types.ModuleType("ttnn")
    sys.modules.setdefault("ttnn", _ttnn)


class DataType(Enum):
    BFLOAT16 = 0
    FLOAT32 = 1
    INT32 = 2
    UINT32 = 7
    UINT16 = 6
    UINT8 = 5
    BFLOAT8_B = 3
    BFLOAT4_B = 4


class _MemoryConfig:
    buffer_type = "L1"
    memory_layout = "INTERLEAVED"


class _Device:
    arch = "BLACKHOLE"


class _Tensor:
    layout = "TILE_LAYOUT"

    def __init__(self, shape: tuple[int, int], dtype=torch.float32):
        self.shape = shape
        self.dtype = dtype

    def memory_config(self):
        return _MemoryConfig()

    def device(self):
        return _Device()


_ttnn.Tensor = _Tensor
if not hasattr(_ttnn, "DataType"):
    _ttnn.DataType = DataType
if not hasattr(_ttnn, "bfloat16"):
    _ttnn.bfloat16 = DataType.BFLOAT16
if not hasattr(_ttnn, "float32"):
    _ttnn.float32 = DataType.FLOAT32
if not hasattr(_ttnn, "TILE_LAYOUT"):
    _ttnn.TILE_LAYOUT = "TILE_LAYOUT"

import ttl


TILE = 32
HEADS = 32
S_TILES = 1
T_TILES = 4


def _tensor(tile_shape: tuple[int, int]):
    rows, cols = tile_shape
    return _Tensor((rows * TILE, cols * TILE), dtype=torch.float32)


@ttl.operation(
    grid=(1, HEADS * S_TILES),
    fp32_dest_acc_en=True,
    dst_full_sync_en=True,
)
def attention_softmax_row(scores, probs):
    scores_reduce_dfb = ttl.make_dataflow_buffer_like(scores, shape=(1, T_TILES), block_count=2)
    scores_sfpu_dfb = ttl.make_dataflow_buffer_like(scores, shape=(1, T_TILES), block_count=2)
    probs_dfb = ttl.make_dataflow_buffer_like(probs, shape=(1, T_TILES), block_count=2)

    @ttl.compute()
    def compute():
        with scores_reduce_dfb.wait() as scores_reduce_blk, scores_sfpu_dfb.wait() as scores_sfpu_blk, probs_dfb.reserve() as probs_blk:
            row_max = ttl.math.reduce_max(scores_reduce_blk, dims=[1])
            shifted = scores_sfpu_blk - ttl.block.broadcast(row_max, dims=[1], shape=(1, T_TILES))
            exp_scores = ttl.math.exp(shifted)
            row_sum = ttl.math.reduce_sum(exp_scores, dims=[1])
            inv_sum = ttl.math.recip(ttl.block.broadcast(row_sum, dims=[1], shape=(1, T_TILES)))
            probs_blk.store(exp_scores * inv_sum)

    @ttl.datamovement()
    def dm_read():
        _, row = ttl.node(dims=2)
        with scores_reduce_dfb.reserve() as scores_reduce_blk, scores_sfpu_dfb.reserve() as scores_sfpu_blk:
            ttl.copy(scores[row, 0:T_TILES], scores_reduce_blk).wait()
            ttl.copy(scores[row, 0:T_TILES], scores_sfpu_blk).wait()

    @ttl.datamovement()
    def dm_write():
        _, row = ttl.node(dims=2)
        with probs_dfb.wait() as probs_blk:
            ttl.copy(probs_blk, probs[row, 0:T_TILES]).wait()


def main() -> int:
    scores = _tensor((HEADS * S_TILES, T_TILES))
    probs = _tensor((HEADS * S_TILES, T_TILES))
    attention_softmax_row(scores, probs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
