#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("TTLANG_COMPILE_ONLY", "1")

import torch
import ttl
import ttnn


TILE = 32
HEAD_DIM = 64
HEAD_DIM_TILES = HEAD_DIM // TILE


@ttl.operation(grid=(1, 1), fp32_dest_acc_en=True)
def rope_apply_kernel(x, cos, sin, out):
    """Apply Llama first-half/second-half RoPE to a tiled (heads*S, 64) tensor."""
    x_row_tiles = x.shape[0] // TILE
    seq_tiles = cos.shape[0] // TILE

    x_lo_dfb = ttl.make_dataflow_buffer_like(x, shape=(1, 1), block_count=2)
    x_hi_dfb = ttl.make_dataflow_buffer_like(x, shape=(1, 1), block_count=2)
    cos_lo_dfb = ttl.make_dataflow_buffer_like(cos, shape=(1, 1), block_count=2)
    cos_hi_dfb = ttl.make_dataflow_buffer_like(cos, shape=(1, 1), block_count=2)
    sin_lo_dfb = ttl.make_dataflow_buffer_like(sin, shape=(1, 1), block_count=2)
    sin_hi_dfb = ttl.make_dataflow_buffer_like(sin, shape=(1, 1), block_count=2)
    out_lo_dfb = ttl.make_dataflow_buffer_like(out, shape=(1, 1), block_count=2)
    out_hi_dfb = ttl.make_dataflow_buffer_like(out, shape=(1, 1), block_count=2)

    @ttl.compute()
    def compute():
        for _ in range(x_row_tiles):
            with (
                x_lo_dfb.wait() as x_lo,
                x_hi_dfb.wait() as x_hi,
                cos_lo_dfb.wait() as cos_lo,
                cos_hi_dfb.wait() as cos_hi,
                sin_lo_dfb.wait() as sin_lo,
                sin_hi_dfb.wait() as sin_hi,
                out_lo_dfb.reserve() as out_lo,
                out_hi_dfb.reserve() as out_hi,
            ):
                out_lo.store(x_lo * cos_lo - x_hi * sin_lo)
                out_hi.store(x_hi * cos_hi + x_lo * sin_hi)

    @ttl.datamovement()
    def dm_read():
        for row_tile in range(x_row_tiles):
            seq_tile = row_tile % seq_tiles
            with x_lo_dfb.reserve() as blk:
                ttl.copy(x[row_tile, 0], blk).wait()
            with x_hi_dfb.reserve() as blk:
                ttl.copy(x[row_tile, 1], blk).wait()
            with cos_lo_dfb.reserve() as blk:
                ttl.copy(cos[seq_tile, 0], blk).wait()
            with cos_hi_dfb.reserve() as blk:
                ttl.copy(cos[seq_tile, 1], blk).wait()
            with sin_lo_dfb.reserve() as blk:
                ttl.copy(sin[seq_tile, 0], blk).wait()
            with sin_hi_dfb.reserve() as blk:
                ttl.copy(sin[seq_tile, 1], blk).wait()

    @ttl.datamovement()
    def dm_write():
        for row_tile in range(x_row_tiles):
            with out_lo_dfb.wait() as blk:
                ttl.copy(blk, out[row_tile, 0]).wait()
            with out_hi_dfb.wait() as blk:
                ttl.copy(blk, out[row_tile, 1]).wait()


def _to_dram(tensor: torch.Tensor, device):
    return ttnn.from_torch(
        tensor,
        dtype=ttnn.bfloat16,
        layout=ttnn.TILE_LAYOUT,
        device=device,
        memory_config=ttnn.DRAM_MEMORY_CONFIG,
    )


def _make_tensors(heads: int, seq_len: int, *, dtype: torch.dtype, device):
    rows = heads * seq_len
    x = torch.zeros((rows, HEAD_DIM), dtype=dtype)
    cos = torch.ones((seq_len, HEAD_DIM), dtype=dtype)
    sin = torch.zeros((seq_len, HEAD_DIM), dtype=dtype)
    out = torch.zeros((rows, HEAD_DIM), dtype=dtype)
    return tuple(_to_dram(tensor, device) for tensor in (x, cos, sin, out))


def compile_variant(name: str, heads: int, seq_len: int, dtype: torch.dtype, device) -> dict[str, object]:
    if seq_len % TILE != 0:
        raise ValueError("seq_len must be a multiple of 32 tiles for this dump harness")
    x, cos, sin, out = _make_tensors(heads, seq_len, dtype=dtype, device=device)
    rope_apply_kernel(x, cos, sin, out)
    return {
        "name": name,
        "heads": heads,
        "seq_len": seq_len,
        "head_dim": HEAD_DIM,
        "input_shape": list(x.shape),
        "table_shape": list(cos.shape),
        "output_shape": list(out.shape),
        "dtype": str(dtype).removeprefix("torch."),
        "math": {
            "rotation": "first_half_second_half",
            "low": "x[..., :32] * cos[..., :32] - x[..., 32:] * sin[..., :32]",
            "high": "x[..., 32:] * cos[..., 32:] + x[..., :32] * sin[..., 32:]",
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compile TT-Lang Llama RoPE apply dump variants.")
    parser.add_argument("--seq-len", type=int, default=32, help="S exemplar used for the dump, multiple of 32")
    parser.add_argument("--variant", choices=("q", "k", "both"), default="both")
    parser.add_argument("--manifest", default="", help="Optional path to write JSON manifest")
    parser.add_argument("--device-id", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    variants = []
    if args.variant in ("q", "both"):
        variants.append(("q_heads32", 32))
    if args.variant in ("k", "both"):
        variants.append(("k_heads8", 8))

    device = ttnn.open_device(device_id=args.device_id)
    try:
        compiled = [
            compile_variant(name, heads, args.seq_len, torch.bfloat16, device)
            for name, heads in variants
        ]
    finally:
        ttnn.close_device(device)
    manifest = {
        "kernel": "rope_apply_kernel",
        "compile_only": os.environ.get("TTLANG_COMPILE_ONLY") == "1",
        "seq_len_is_compile_time_exemplar": True,
        "variants": compiled,
    }
    text = json.dumps(manifest, indent=2, sort_keys=True)
    print(text)
    if args.manifest:
        Path(args.manifest).write_text(text + "\n")


if __name__ == "__main__":
    main()
