# Llama decode core usage and attention scaling

Counts come from the exported manifests. A core here means one Tensix worker,
not each of its five RISC-V instruction streams. Launches reuse workers
sequentially; assigned core counts are not arithmetic-utilization measurements.

| Exported program | 1B BF16 | 8B BF16 | 8B FP8 | Work |
|---|---:|---:|---:|---|
| `embedding` | 1 | 1 | 1 | Gather one token's embedding |
| `qkv` | 88 | 88 | 96 | Replicated RMSNorm; shards of Q/K/V output rows |
| `attention` | 96 | 96 | 96 | Up to 96 active context partitions, with fused RoPE/cache append |
| `attention_merge` | 8 | 8 | 8 | One merger per KV head |
| `o` | 88 | 88 | 96 | Output projection and residual |
| `gate` | 88 | 88 | 96 | RMSNorm, gate/up projections, SwiGLU |
| `down` | 88 | 88 | 96 | Down projection and residual |
| `lm` | 88 | 88 | 96 | RMSNorm and vocabulary-row shards |
| `argmax` | 88 | 88 | 96 | Local scans, then one participating core reduces candidates |

RMSNorm, SwiGLU, residual additions, RoPE, and cache append are fused work,
not additional launches. RMSNorm is replicated on projection workers rather
than distributed as a cross-core reduction. Embedding, LM, and argmax run
once per token; the other six launches run per layer. There are 99 launches
per token for 1B and 195 for 8B.

The exporter's placement pool contains 118 workers: a 12-by-10 grid minus
its two service cores. It targets the smallest supported layout rather than
using every physical worker on a larger card. Projection placement also
requires a multicast rectangle. Standalone RMSNorm/matmul/probe programs
outside this decode graph have caller-selected shapes and core counts.

## Attention implementation

Previously, unsplit attention used 16 workers for 1B and 32 for 8B. Each
worker scanned a KV head's entire history for two queries (1B) or one (8B),
reading the same KV head twice or four times across workers.

The new kernel groups all four queries that share a KV head on each worker,
and distributes cache blocks across that head's context partitions. Cache
streaming collectively reads each KV head once. Preparation still repeats
Q gathering and RoPE on active partitions; each worker waits for its own
acknowledged current-token cache writes before streaming.

The exported graph always launches **partial attention, then merge**. The
same binaries and same core lists run at every position. A small device-side
work-assignment policy selects how many of the 12 partitions per KV head
are active:

| Context length | Partitions per KV head | Active partial workers | Subsequent merge workers |
|---|---:|---:|---:|
| 1–128 | 1 | 8 | 8 |
| 129–4096 | 4 | 32 | 8 |
| 4097–8192 | 12 | 96 | 8 |

All five RISCs return early on inactive partitions. Active phase `s` visits
blocks `s, s + active_partitions, ...`; tail masking follows the partition
that owns the final block. The merge reads only active states, so stale or
empty states cannot contaminate the result. Each state contains FP32 weighted
output, maximum, and denominator. Merge rescales states to their common
maximum, combines them, and normalizes once; it does not average independently
normalized outputs.

The thresholds reflect the measured tradeoff: four partitions were competitive
at 4K and faster at 512/1024, whereas twelve were fastest at 8K. There is no
host-side kernel or graph switch. The default capacity is configurable as
`attention_partitions` in the old runtime and `--attention-partitions` in the
exporter (0 selects the unsplit baseline; 4/8/12 select capacities).

The retained Q block is waited on once before its loop; subsequent unpack
moves omit redundant Q waits. P remains retained across V feature tiles.
Merge computes each row's reciprocal once and retains exact `exp(0) = 1`
for rescaling. The binaries fit the existing instruction slots; export now
checks image size including the runtime return instruction.

## Measurements and validation

Final hardware validation: **84 cases passed**, each comparing unsplit,
32-, 64-, and 96-worker variants against NumPy and checking identical repeated
replay. Cases cover both model shapes, random and unchanged maxima, poisoned
tails, partition-count boundaries, and eight fused RoPE/cache-append cases
whose current cache rows are poisoned before each variant. The maximum tested
length is 8192. All three models' short 64-token generations match their stored
references exactly.

End-to-end device-clock throughput, 64 generated tokens (earlier unsplit run
versus the scaled implementation):

| Model | Short, before | Short, after | 4K, before | 4K, after |
|---|---:|---:|---:|---:|
| 1B BF16 | 162.9 | 159.3 | 120.3 | 142.5 |
| 8B BF16 | 30.5 | 30.0 | 24.7 | 28.0 |
| 8B FP8 | 52.0 | 50.5 | 37.4 (only 5 tokens) | 45.2 |

Units: tokens/second. The 4K run starts with 4096 prompt tokens; most of its
64 decode steps therefore use the long-context partition count. Short-context
throughput loses roughly 2–3% to the extra launch/merge. The earlier and scaled
FP8 prompt benchmarks both experienced intermittent device/runtime timeouts;
the final scaled FP8 run completed on retry. The five-token baseline is not
a comparable fixed-length measurement. The timeout cause remains unresolved;
no unrelated runtime or reset fix is included in this change.

The isolated pre-RoPE benchmark includes partial + merge and host replay
latency. The final 1B build measured 163 → 77 microseconds at exactly 4K and
298 → 104 microseconds at 8K. Before the final redundant-Q-wait removal, 8B
measured 281 → 112 microseconds at 4K and 514 → 165 microseconds at 8K. These
are kernel-path timings, not total decode speedups. A later benchmark attempt
failed during 8B's initial upload, before attention ran.

Reproduce from `blackhole-py-old`:

```sh
../.venv/bin/python -m pytest tests/compute/fpu/test_llama_attention.py --bh-hardware --bh-device 0 -q
../.venv/bin/python tools/bench_llama_attention.py --device 0 --lengths 32 512 4096 8192 33 --json /tmp/attention.json
../.venv/bin/python tools/rewrite_export/export_llama3.py --model all --attention-partitions 12 --rewrite ../blackhole-py
```

Export complete model artifact sets together: the extra merge program changes
parameter-table and data addresses, so replacing only attention binaries would
leave inconsistent layouts. Runtime code and firmware need no changes.

## Other kernels

Projection counts are unchanged. `config.py` records earlier measurements
where 104 and 117 workers were slower, citing bandwidth saturation and repeated
activation reads. Argmax already scans one shard per projection worker;
embedding moves just one small vector. Neither is an obvious candidate for
more workers without evidence from profiling.

Sources: `kernels/llama3-{1b,8b-bf16,8b-fp8}/manifest.json`, and
`../blackhole-py-old/examples/llama3/{config,runtime,kernels}.py` plus
`../blackhole-py-old/tools/rewrite_export/export_llama3.py`.
