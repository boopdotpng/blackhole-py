#!/usr/bin/env python3
"""TT-Lang probes for Llama kernel-mining dumps.

Each subcommand is intentionally small and tile-shaped.  Run one probe at a
time with TTLANG_DUMP_ARTIFACTS_DIR, TTLANG_INITIAL_MLIR, and TTLANG_FINAL_MLIR
pointing at a blackhole-py/ttlang-dumps/*_artifacts directory.
"""
from __future__ import annotations

import argparse
import math

import torch
import ttnn
import ttl


TILE = 32
MLP_TILES = 4
HEAD_TILES = 2
SOFTMAX_TILES = 4
KV_HEADS = 8
ATTN_HEADS = 32
GQA_EXEC_HEADS = 8
GQA_REPEAT = ATTN_HEADS // KV_HEADS
CACHE_LEN = 8192
CACHE_LEN_TILES = CACHE_LEN // TILE
STORE_START_TILE = 7


def verify_enabled() -> bool:
    return __import__("os").environ.get("TTLANG_VERIFY", "1") != "0"


def to_device(tensor: torch.Tensor, device, dtype=None, memory_config=None):
    if dtype is None:
        dtype = ttnn.float32 if tensor.dtype == torch.float32 else ttnn.bfloat16
    if memory_config is None:
        memory_config = ttnn.DRAM_MEMORY_CONFIG
    return ttnn.from_torch(
        tensor,
        dtype=dtype,
        layout=ttnn.TILE_LAYOUT,
        device=device,
        memory_config=memory_config,
    )


def assert_pcc(name: str, result: torch.Tensor, golden: torch.Tensor, threshold: float) -> None:
    rf = result.float().flatten()
    gf = golden.float().flatten()
    pcc = torch.corrcoef(torch.stack([rf, gf]))[0, 1].item()
    max_abs = (rf - gf).abs().max().item()
    print(f"{name} PCC {pcc:.6f}")
    print(f"{name} MAX_ABS {max_abs:.6f}")
    assert pcc >= threshold, f"{name} PCC {pcc:.6f} < {threshold:.6f}"


@ttl.operation(grid=(1, 1))
def mlp_silu_mul_kernel(gate, up, out):
    gate_dfb = ttl.make_dataflow_buffer_like(gate, shape=(1, MLP_TILES), block_count=2)
    up_dfb = ttl.make_dataflow_buffer_like(up, shape=(1, MLP_TILES), block_count=2)
    out_dfb = ttl.make_dataflow_buffer_like(out, shape=(1, MLP_TILES), block_count=2)

    @ttl.compute()
    def compute():
        with gate_dfb.wait() as gate_blk, up_dfb.wait() as up_blk, out_dfb.reserve() as out_blk:
            out_blk.store(ttl.silu(gate_blk) * up_blk)

    @ttl.datamovement()
    def dm_read():
        with gate_dfb.reserve() as blk:
            ttl.copy(gate[0, 0:MLP_TILES], blk).wait()
        with up_dfb.reserve() as blk:
            ttl.copy(up[0, 0:MLP_TILES], blk).wait()

    @ttl.datamovement()
    def dm_write():
        with out_dfb.wait() as blk:
            ttl.copy(blk, out[0, 0:MLP_TILES]).wait()


@ttl.operation(grid=(1, 1))
def rope_half_split_kernel(x, cos, sin, out):
    x0_dfb = ttl.make_dataflow_buffer_like(x, shape=(1, 1), block_count=2)
    x1_dfb = ttl.make_dataflow_buffer_like(x, shape=(1, 1), block_count=2)
    c0_dfb = ttl.make_dataflow_buffer_like(cos, shape=(1, 1), block_count=2)
    c1_dfb = ttl.make_dataflow_buffer_like(cos, shape=(1, 1), block_count=2)
    s0_dfb = ttl.make_dataflow_buffer_like(sin, shape=(1, 1), block_count=2)
    s1_dfb = ttl.make_dataflow_buffer_like(sin, shape=(1, 1), block_count=2)
    o0_dfb = ttl.make_dataflow_buffer_like(out, shape=(1, 1), block_count=2)
    o1_dfb = ttl.make_dataflow_buffer_like(out, shape=(1, 1), block_count=2)

    @ttl.compute()
    def compute():
        with (
            x0_dfb.wait() as x0,
            x1_dfb.wait() as x1,
            c0_dfb.wait() as c0,
            s0_dfb.wait() as s0,
            o0_dfb.reserve() as o0,
        ):
            o0.store(x0 * c0 + ttl.neg(x1) * s0)

        with (
            x0_dfb.wait() as x0,
            x1_dfb.wait() as x1,
            c1_dfb.wait() as c1,
            s1_dfb.wait() as s1,
            o1_dfb.reserve() as o1,
        ):
            o1.store(x1 * c1 + x0 * s1)

    @ttl.datamovement()
    def dm_read():
        with x0_dfb.reserve() as blk:
            ttl.copy(x[0, 0], blk).wait()
        with x1_dfb.reserve() as blk:
            ttl.copy(x[0, 1], blk).wait()
        with c0_dfb.reserve() as blk:
            ttl.copy(cos[0, 0], blk).wait()
        with c1_dfb.reserve() as blk:
            ttl.copy(cos[0, 1], blk).wait()
        with s0_dfb.reserve() as blk:
            ttl.copy(sin[0, 0], blk).wait()
        with s1_dfb.reserve() as blk:
            ttl.copy(sin[0, 1], blk).wait()

    @ttl.datamovement()
    def dm_write():
        with o0_dfb.wait() as blk:
            ttl.copy(blk, out[0, 0]).wait()
        with o1_dfb.wait() as blk:
            ttl.copy(blk, out[0, 1]).wait()


@ttl.operation(grid=(1, 1), fp32_dest_acc_en=True, dst_full_sync_en=True)
def attention_mask_scale_add_kernel(scores, mask_bias, out):
    scores_dfb = ttl.make_dataflow_buffer_like(scores, shape=(1, SOFTMAX_TILES), block_count=2)
    mask_dfb = ttl.make_dataflow_buffer_like(mask_bias, shape=(1, SOFTMAX_TILES), block_count=2)
    out_dfb = ttl.make_dataflow_buffer_like(out, shape=(1, SOFTMAX_TILES), block_count=2)

    @ttl.compute()
    def compute():
        with scores_dfb.wait() as scores_blk, mask_dfb.wait() as mask_blk, out_dfb.reserve() as out_blk:
            out_blk.store(scores_blk * 0.125 + mask_blk)

    @ttl.datamovement()
    def dm_read():
        with scores_dfb.reserve() as scores_blk, mask_dfb.reserve() as mask_blk:
            ttl.copy(scores[0, 0:SOFTMAX_TILES], scores_blk).wait()
            ttl.copy(mask_bias[0, 0:SOFTMAX_TILES], mask_blk).wait()

    @ttl.datamovement()
    def dm_write():
        with out_dfb.wait() as blk:
            ttl.copy(blk, out[0, 0:SOFTMAX_TILES]).wait()


@ttl.operation(grid=(1, 1), fp32_dest_acc_en=True, dst_full_sync_en=True)
def attention_softmax_row_kernel(scores, probs):
    scores_reduce_dfb = ttl.make_dataflow_buffer_like(scores, shape=(1, SOFTMAX_TILES), block_count=2)
    scores_sfpu_dfb = ttl.make_dataflow_buffer_like(scores, shape=(1, SOFTMAX_TILES), block_count=2)
    probs_dfb = ttl.make_dataflow_buffer_like(probs, shape=(1, SOFTMAX_TILES), block_count=2)

    @ttl.compute()
    def compute():
        with scores_reduce_dfb.wait() as reduce_blk, scores_sfpu_dfb.wait() as sfpu_blk:
            mx = ttl.math.reduce_max(reduce_blk, dims=[1])
            shifted = sfpu_blk - ttl.block.broadcast(mx, dims=[1], shape=(1, SOFTMAX_TILES))
            ex = ttl.exp(shifted)
            sm = ttl.math.reduce_sum(ex, dims=[1])
            inv_sum = ttl.recip(ttl.block.broadcast(sm, dims=[1], shape=(1, SOFTMAX_TILES)))
            with probs_dfb.reserve() as out_blk:
                out_blk.store(ttl.mul(ex, inv_sum))

    @ttl.datamovement()
    def dm_read():
        with scores_reduce_dfb.reserve() as reduce_blk, scores_sfpu_dfb.reserve() as sfpu_blk:
            ttl.copy(scores[0, 0:SOFTMAX_TILES], reduce_blk).wait()
            ttl.copy(scores[0, 0:SOFTMAX_TILES], sfpu_blk).wait()

    @ttl.datamovement()
    def dm_write():
        with probs_dfb.wait() as blk:
            ttl.copy(blk, probs[0, 0:SOFTMAX_TILES]).wait()


@ttl.operation(grid=(1, 1))
def qk_score_tile_kernel(q, k, scale, scores):
    q_dfb = ttl.make_dataflow_buffer_like(q, shape=(1, HEAD_TILES), block_count=2)
    k_dfb = ttl.make_dataflow_buffer_like(k, shape=(1, HEAD_TILES), block_count=2)
    scale_dfb = ttl.make_dataflow_buffer_like(scale, shape=(1, 1), block_count=1)
    scores_dfb = ttl.make_dataflow_buffer_like(scores, shape=(1, 1), block_count=2)

    @ttl.compute()
    def compute():
        with q_dfb.wait() as q_blk, k_dfb.wait() as k_blk, scale_dfb.wait() as sc:
            dot = ttl.math.reduce_sum(q_blk * k_blk, dims=[1])
            with scores_dfb.reserve() as out_blk:
                out_blk.store(dot * sc)

    @ttl.datamovement()
    def dm_read():
        with q_dfb.reserve() as blk:
            ttl.copy(q[0, 0:HEAD_TILES], blk).wait()
        with k_dfb.reserve() as blk:
            ttl.copy(k[0, 0:HEAD_TILES], blk).wait()
        with scale_dfb.reserve() as blk:
            ttl.copy(scale[0, 0], blk).wait()

    @ttl.datamovement()
    def dm_write():
        with scores_dfb.wait() as blk:
            ttl.copy(blk, scores[0, 0]).wait()


@ttl.operation(grid=(1, 1))
def causal_mask_tile_kernel(scores, masked):
    scores_dfb = ttl.make_dataflow_buffer_like(scores, shape=(1, 1), block_count=2)
    masked_dfb = ttl.make_dataflow_buffer_like(masked, shape=(1, 1), block_count=2)

    @ttl.compute()
    def compute():
        pass

    @ttl.datamovement()
    def dm_read():
        with scores_dfb.reserve() as blk:
            ttl.copy(scores[0, 0], blk).wait()

    @ttl.datamovement()
    def dm_write():
        with scores_dfb.wait() as src:
            with masked_dfb.reserve() as dst:
                for row in range(TILE):
                    for col in range(TILE):
                        val = ttl.raw_element_read(src, row, col)
                        if col > row:
                            val = float("-inf")
                        ttl.raw_element_write(dst, row, col, val)
                ttl.copy(dst, masked[0, 0]).wait()


@ttl.operation(grid=(HEAD_TILES, KV_HEADS), memory_space="DRAM")
def kv_cache_store_static_kernel(k_in, v_in, k_cache, v_cache):
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


@ttl.operation(grid=(HEAD_TILES, GQA_EXEC_HEADS), memory_space="DRAM")
def gqa_repeat_static_kernel(k_cache, v_cache, k_repeated, v_repeated):
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
            ttl.copy(k_cache[kv_head, STORE_START_TILE, dim_tile], k_blk).wait()
        with v_dfb.reserve() as v_blk:
            ttl.copy(v_cache[kv_head, STORE_START_TILE, dim_tile], v_blk).wait()

    @ttl.datamovement()
    def dm_write():
        dim_tile, query_head = ttl.node(dims=2)
        with k_repeat_dfb.wait() as k_blk:
            ttl.copy(k_blk, k_repeated[query_head, 0, dim_tile]).wait()
        with v_repeat_dfb.wait() as v_blk:
            ttl.copy(v_blk, v_repeated[query_head, 0, dim_tile]).wait()


def run_mlp_silu_mul(device) -> None:
    torch.manual_seed(1)
    gate_t = torch.randn(TILE, MLP_TILES * TILE, dtype=torch.bfloat16)
    up_t = torch.randn(TILE, MLP_TILES * TILE, dtype=torch.bfloat16)
    out_t = torch.zeros_like(gate_t)
    gate = to_device(gate_t, device)
    up = to_device(up_t, device)
    out = to_device(out_t, device)
    mlp_silu_mul_kernel(gate, up, out)
    if not verify_enabled():
        print("mlp_silu_mul launched; readback verification skipped")
        return
    result = ttnn.to_torch(out)
    golden = torch.nn.functional.silu(gate_t.float()) * up_t.float()
    assert_pcc("mlp_silu_mul", result, golden, 0.998)


def run_rope_half_split(device) -> None:
    torch.manual_seed(2)
    x_t = torch.randn(TILE, HEAD_TILES * TILE, dtype=torch.bfloat16)
    angle = torch.linspace(0.0, math.pi, HEAD_TILES * TILE).reshape(1, -1).repeat(TILE, 1)
    cos_t = torch.cos(angle).to(torch.bfloat16)
    sin_t = torch.sin(angle).to(torch.bfloat16)
    out_t = torch.zeros_like(x_t)
    x = to_device(x_t, device)
    cos = to_device(cos_t, device)
    sin = to_device(sin_t, device)
    out = to_device(out_t, device)
    rope_half_split_kernel(x, cos, sin, out)
    if not verify_enabled():
        print("rope_half_split launched; readback verification skipped")
        return
    result = ttnn.to_torch(out)
    x0 = x_t[:, :TILE].float()
    x1 = x_t[:, TILE:].float()
    golden = torch.cat(
        [
            x0 * cos_t[:, :TILE].float() - x1 * sin_t[:, :TILE].float(),
            x1 * cos_t[:, TILE:].float() + x0 * sin_t[:, TILE:].float(),
        ],
        dim=1,
    )
    assert_pcc("rope_half_split", result, golden, 0.995)


def run_attention_softmax_row(device) -> None:
    torch.manual_seed(3)
    scores_t = torch.randn(TILE, SOFTMAX_TILES * TILE, dtype=torch.float32)
    probs_t = torch.zeros(TILE, SOFTMAX_TILES * TILE, dtype=torch.float32)
    scores = to_device(scores_t, device, dtype=ttnn.float32)
    probs = to_device(probs_t, device, dtype=ttnn.float32)
    attention_softmax_row_kernel(scores, probs)
    if not verify_enabled():
        print("attention_softmax_row launched; readback verification skipped")
        return
    result = ttnn.to_torch(probs)
    golden = torch.softmax(scores_t, dim=1)
    assert_pcc("attention_softmax_row", result, golden, 0.99)


def run_attention_mask_scale_add(device) -> None:
    torch.manual_seed(6)
    scores_t = torch.randn(TILE, SOFTMAX_TILES * TILE, dtype=torch.float32)
    mask_t = torch.zeros(TILE, SOFTMAX_TILES * TILE, dtype=torch.float32)
    mask_t[:, TILE * 2 :] = -1.0e9
    out_t = torch.zeros_like(scores_t)
    scores = to_device(scores_t, device, dtype=ttnn.float32)
    mask = to_device(mask_t, device, dtype=ttnn.float32)
    out = to_device(out_t, device, dtype=ttnn.float32)
    attention_mask_scale_add_kernel(scores, mask, out)
    if not verify_enabled():
        print("attention_mask_scale_add launched; readback verification skipped")
        return
    result = ttnn.to_torch(out)
    golden = scores_t * 0.125 + mask_t
    assert_pcc("attention_mask_scale_add", result, golden, 0.999)


def run_qk_score_tile(device) -> None:
    torch.manual_seed(4)
    q_t = torch.randn(TILE, HEAD_TILES * TILE, dtype=torch.bfloat16)
    k_t = torch.randn(TILE, HEAD_TILES * TILE, dtype=torch.bfloat16)
    scale_t = torch.full((TILE, TILE), 0.125, dtype=torch.bfloat16)
    scores_t = torch.zeros(TILE, TILE, dtype=torch.bfloat16)
    q = to_device(q_t, device)
    k = to_device(k_t, device)
    scale = to_device(scale_t, device)
    scores = to_device(scores_t, device)
    qk_score_tile_kernel(q, k, scale, scores)
    if not verify_enabled():
        print("qk_score_tile launched; readback verification skipped")
        return
    result = ttnn.to_torch(scores)
    golden = (q_t.float() * k_t.float()).reshape(TILE, HEAD_TILES, TILE).sum(dim=1) * 0.125
    assert_pcc("qk_score_tile", result, golden, 0.99)


def run_causal_mask_tile(device) -> None:
    torch.manual_seed(5)
    scores_t = torch.randn(TILE, TILE, dtype=torch.float32)
    masked_t = torch.zeros_like(scores_t)
    scores = to_device(scores_t, device, dtype=ttnn.float32)
    masked = to_device(masked_t, device, dtype=ttnn.float32)
    causal_mask_tile_kernel(scores, masked)
    if not verify_enabled():
        print("causal_mask_tile launched; readback verification skipped")
        return
    result = ttnn.to_torch(masked)
    golden = scores_t.masked_fill(torch.triu(torch.ones(TILE, TILE, dtype=torch.bool), diagonal=1), float("-inf"))
    finite = torch.isfinite(golden)
    max_abs = (result[finite] - golden[finite]).abs().max().item()
    invalid_ok = torch.isneginf(result[~finite]).all().item()
    print(f"causal_mask_tile MAX_ABS {max_abs:.6f}")
    print(f"causal_mask_tile INVALID_NEG_INF {invalid_ok}")
    assert max_abs == 0.0
    assert invalid_ok


def run_kv_cache_store_static(device) -> None:
    k_in_t = torch.zeros(KV_HEADS, TILE, HEAD_TILES * TILE, dtype=torch.bfloat16)
    v_in_t = torch.zeros_like(k_in_t)
    k_cache_t = torch.zeros(KV_HEADS, CACHE_LEN, HEAD_TILES * TILE, dtype=torch.bfloat16)
    v_cache_t = torch.zeros_like(k_cache_t)
    k_in = to_device(k_in_t, device)
    v_in = to_device(v_in_t, device)
    k_cache = to_device(k_cache_t, device)
    v_cache = to_device(v_cache_t, device)
    kv_cache_store_static_kernel(k_in, v_in, k_cache, v_cache)
    print("kv_cache_store_static launched; readback verification skipped")


def run_gqa_repeat_static(device) -> None:
    k_cache_t = torch.zeros(KV_HEADS, CACHE_LEN, HEAD_TILES * TILE, dtype=torch.bfloat16)
    v_cache_t = torch.zeros_like(k_cache_t)
    k_rep_t = torch.zeros(ATTN_HEADS, TILE, HEAD_TILES * TILE, dtype=torch.bfloat16)
    v_rep_t = torch.zeros_like(k_rep_t)
    k_cache = to_device(k_cache_t, device)
    v_cache = to_device(v_cache_t, device)
    k_rep = to_device(k_rep_t, device)
    v_rep = to_device(v_rep_t, device)
    gqa_repeat_static_kernel(k_cache, v_cache, k_rep, v_rep)
    print("gqa_repeat_static launched; readback verification skipped")


PROBES = {
    "attention-mask-scale-add": run_attention_mask_scale_add,
    "gqa-repeat-static": run_gqa_repeat_static,
    "kv-cache-store-static": run_kv_cache_store_static,
    "mlp-silu-mul": run_mlp_silu_mul,
    "rope-half-split": run_rope_half_split,
    "attention-softmax-row": run_attention_softmax_row,
    "qk-score-tile": run_qk_score_tile,
    "causal-mask-tile": run_causal_mask_tile,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("probe", choices=sorted(PROBES))
    args = parser.parse_args()

    device = ttnn.open_device(device_id=0)
    try:
        PROBES[args.probe](device)
    finally:
        ttnn.close_device(device)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
