"""Two-card Llama 3.2 1B sharding plan and batch-one decode estimate.

CPU-only planning/reference math. No distributed inference launch is implied.
"""
import argparse
import json

D, F, L, V, Q, KV, HEAD = 2048, 8192, 16, 128256, 32, 8, 64


def plan(rank):
    if rank not in (0, 1):
        raise ValueError("only TP=2 is defined")
    def span(n):
        return [rank * (n // 2), (rank + 1) * (n // 2)]
    return dict(rank=rank, q_heads=span(Q), kv_heads=span(KV), mlp_features=span(F),
                vocab=span(V), q_weight_rows=span(D), kv_weight_rows=span(KV*HEAD),
                o_weight_columns=span(D), down_weight_columns=span(F),
                residual="replicated", rmsnorm="replicated",
                allreduce="FP32 SUM after O and down; add residual once after SUM")


def estimate(link_gbps=400., efficiency=0.8, latency_us=5., dram_gbs=512.,
             scalable_fraction=0.9, baseline_tps=152.3, batch=1):
    if not (link_gbps > 0 and dram_gbs > 0 and baseline_tps > 0 and
            0 < efficiency <= 1 and latency_us >= 0 and 0 <= scalable_fraction <= 1 and
            isinstance(batch, int) and batch > 0):
        raise ValueError("invalid model assumptions")
    # Q/K/V, O, gate/up/down, then tied embedding used as full vocab LM head.
    weights = 2 * (L * (D * (D + 2 * KV * HEAD) + D * D + 3 * D * F) + V * D)
    activation = batch * D * 4  # FP32 partials; each rank sends full vector to peer.
    collectives = 2 * L
    bandwidth = link_gbps * 1e9 / 8 * efficiency
    comm = collectives * (latency_us * 1e-6 + activation / bandwidth)
    # Both ranks calculate the same winner from two (FP32 score, uint32 id) candidates.
    final = latency_us * 1e-6 + 8 * batch / bandwidth
    minimum = weights / (2 * dram_gbs * 1e9) + comm + final
    measured_model = (1 / baseline_tps) * (1 - scalable_fraction / 2) + comm + final
    return dict(projection_weight_bytes=weights, weights_per_rank=weights//2,
                fp32_activation_bytes=activation, allreduces_per_step=collectives,
                sent_activation_bytes_per_rank=collectives*activation,
                communication_us=(comm+final)*1e6,
                weight_only_tp2_tps=2*dram_gbs*1e9/weights,
                ideal_weight_plus_comm_steps_per_second=1/minimum,
                baseline_scaled_steps_per_second=1/measured_model,
                assumptions=dict(link_gbps=link_gbps, payload_efficiency=efficiency,
                    effective_collective_latency_us=latency_us, dram_gbs_per_card=dram_gbs,
                    scalable_fraction=scalable_fraction, baseline_tps=baseline_tps, batch=batch),
                caveat="No ERISC, NoC, reduction, or TP performance has been measured. Batch>1 baseline scaling is illustrative only.")


def column_parallel(x, weight):
    """CPU reference: torch-style weight[out, in], split output features."""
    import numpy as np
    if weight.shape[0] % 2:
        raise ValueError("output must divide evenly")
    return [x @ w.T for w in np.split(weight, 2, axis=0)]


def row_parallel(parts, weight):
    """CPU reference: full FP32 partial exchange + sum, residual added by caller."""
    import numpy as np
    if len(parts) != 2 or weight.shape[1] % 2:
        raise ValueError("expected two even input partitions")
    partials = [x.astype(np.float32) @ w.astype(np.float32).T
                for x, w in zip(parts, np.split(weight, 2, axis=1))]
    return partials[0] + partials[1]


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--latency-us", type=float, default=5.)
    p.add_argument("--link-gbps", type=float, default=400.)
    p.add_argument("--efficiency", type=float, default=0.8)
    p.add_argument("--scalable-fraction", type=float, default=0.9)
    a = p.parse_args()
    print(json.dumps(dict(ranks=[plan(0), plan(1)], estimate=estimate(
        latency_us=a.latency_us, link_gbps=a.link_gbps, efficiency=a.efficiency,
        scalable_fraction=a.scalable_fraction)), indent=2))
