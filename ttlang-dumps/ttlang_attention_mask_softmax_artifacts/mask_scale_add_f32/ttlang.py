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
SCALE = 0.125


def _tensor(tile_shape: tuple[int, int]):
    rows, cols = tile_shape
    return _Tensor((rows * TILE, cols * TILE), dtype=torch.float32)


@ttl.operation(
    grid=(1, HEADS * S_TILES),
    fp32_dest_acc_en=True,
    dst_full_sync_en=True,
)
def attention_mask_scale_add(scores, mask_bias, out):
    scores_dfb = ttl.make_dataflow_buffer_like(scores, shape=(1, T_TILES), block_count=2)
    mask_dfb = ttl.make_dataflow_buffer_like(mask_bias, shape=(1, T_TILES), block_count=2)
    out_dfb = ttl.make_dataflow_buffer_like(out, shape=(1, T_TILES), block_count=2)

    @ttl.compute()
    def compute():
        with scores_dfb.wait() as scores_blk, mask_dfb.wait() as mask_blk, out_dfb.reserve() as out_blk:
            out_blk.store(scores_blk * SCALE + mask_blk)

    @ttl.datamovement()
    def dm_read():
        _, row = ttl.node(dims=2)
        with scores_dfb.reserve() as scores_blk, mask_dfb.reserve() as mask_blk:
            ttl.copy(scores[row, 0:T_TILES], scores_blk).wait()
            ttl.copy(mask_bias[row, 0:T_TILES], mask_blk).wait()

    @ttl.datamovement()
    def dm_write():
        _, row = ttl.node(dims=2)
        with out_dfb.wait() as out_blk:
            ttl.copy(out_blk, out[row, 0:T_TILES]).wait()


def main() -> int:
    scores = _tensor((HEADS * S_TILES, T_TILES))
    mask_bias = _tensor((HEADS * S_TILES, T_TILES))
    out = _tensor((HEADS * S_TILES, T_TILES))
    attention_mask_scale_add(scores, mask_bias, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
