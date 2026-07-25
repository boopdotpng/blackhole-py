# Llama 3.2 1B end-to-end decode profile

Measured July 25, 2026 on p100a, batch 1, using:

```sh
PYTHONPATH=. python3 examples/llama3.py \
  --prompt "The capital of France is" --steps 8 --profile
```

Correctness output: `The capital of France is Paris.`

## Generated-token timing

| interval | average |
|---|---:|
| full `decode()` call, including token readback | 9246.21 us |
| host replay wall | 9244.14 us |
| CQ doorbell to final completion | 9226.17 us |
| host time outside the device interval | 20.04 us |
| runtime-state encode + trace patch | 8.50 us |
| CQ event patch + slot check + doorbell | 4.65 us |
| completion descriptor tail | 1.80 us |
| live 4-byte token readback | 1.11 us |
| text streaming, outside `decode()` | 19.68 us/token |

The completion timestamp is per launch, so the final kernel's 37.51 us
timestamp is **not** the full-token device time. Doorbell-to-final-completion
is the useful whole-trace boundary. At 9226.17 us versus 9246.21 us, host work
inside `decode()` is about 0.20% of latency.

Throughput was 108.15 tok/s. The older launch report's conclusion still holds:
steady-state decode is dominated by device weight streaming, not by the host
loop.

## Fused QKV projection

Q, K, and V retain their original per-core compact layouts. Each fused core
computes its own three shards, using one token fetch and one launch. The only
compile-time variants are `(18,5,5)`, `(18,4,4)`, and `(17,4,4)` rows.

An isolated random-BF16 hardware check compares every output byte, including
compact padding:

```text
Q: PASS
K: PASS
V: PASS
separate Q + K + V kernels: 60.06 us
fused QKV kernel: 43.14 us
```

The full trace drops from 260 to 228 launches. Against the preceding
non-fused run, its device/CQ interval fell from 9504.33 us to about 9226 us,
saving about 278 us/token and raising throughput from 105.03 to 108.15 tok/s.

## Startup and DRAM upload

| stage | wall time |
|---|---:|
| complete runtime startup | 4998.18 ms |
| device initialization | 406.85 ms |
| safetensor/rope preparation | 633.96 ms |
| host tilize + pinned-memory staging | 2917.80 ms |
| CQ/device DRAM upload | 165.45 ms |
| resident program build/cache | 769.18 ms |

The embedding and LM head are tied in the model, so the runtime now allocates
and uploads the 128256x2048 BF16 tensor once. The LM projection uses a
118-core row-sharded view of that same global DRAM allocation. This removes
0.489 GiB of duplicate allocation, tilization, staging, and upload.

The upload now transfers 2.599 GiB at 15.71 GiB/s. The transfer itself is only
3.3% of startup; host layout conversion and staging remain the bottleneck.

The new complete-axis-0 tilization path writes directly into final sharded
tile storage. Against the immediately preceding correct run, it reduced host
tile/staging from 6414.54 ms to 3526.89 ms and startup from 8507.88 ms to
5594.49 ms. It was checked byte-for-byte against the generic tilizer across
sharded/unsharded and tilized/row-major cases before hardware validation.

Trace completion now busy-polls the pinned completion word, while long upload
waits retain their sleep. This removes scheduler wake-up latency from the
token loop without burning a CPU during model upload.

## Optimizations deliberately not retained

- Skipping the 256 MiB KV-cache zero upload passed on a warm card but produced
  incorrect tokens after a device reset. Cache initialization remains.
- A first gate+up projection fusion improved latency slightly but changed
  generated output. It was reverted. Fusion needs kernel-level numerical
  validation in `ttsim` before hardware revalidation.
- Device-autonomous runtime-state replay was not retained. The existing
  device multicast is posted, so a reliable handoff needs an explicit remote
  completion protocol before the host trace patch can be removed safely.

## Next work

For steady-state tok/s, follow the existing decode report: rewrite GEMV to
amortize scalar reduction/packing across output rows, then parallelize
attention for long contexts. Prompt ingestion still runs the complete decode
trace once per prompt token. Any prefill work belongs in the separate prefill
implementation; `llama3.py` is intentionally decode-only.

For startup, the next meaningful step is device-side tilization or a persistent
pre-tilized weight cache. Optimizing the 165 ms DRAM transfer alone cannot
materially reduce the current 5.0 s startup.
