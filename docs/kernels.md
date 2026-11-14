# Llama kernels: core usage, attention scaling, and remaining work

Counts come from the exported manifests. A core here means one Tensix worker,
not each of its five RISC-V instruction streams. Launches reuse workers
sequentially; assigned core counts are not arithmetic-utilization measurements.

| Exported program | 1B BF16 | 8B BF16 | 8B FP8 | Work |
|---|---:|---:|---:|---|
| `embedding` | 1 | 1 | 1 | Gather one token's embedding |
| `qkv` | 88 | 88 | 96 | Replicated RMSNorm; rows of dense Q/K/V vectors |
| `attention` | 64 | 64 | 64 | Up to 64 active context partitions, fused RoPE/cache append and merge |
| `o` | 88 | 88 | 96 | Output projection and residual |
| `gate` | 88 | 88 | 96 | RMSNorm, gate/up projections, SwiGLU |
| `down` | 88 | 88 | 96 | Down projection and residual |
| `lm` | 88 | 88 | 96 | RMSNorm and vocabulary-row shards |
| `argmax` | 88 | 88 | 96 | Local scans, then one participating core reduces candidates |

RMSNorm, SwiGLU, residual additions, RoPE, and cache append are fused work,
not additional launches. RMSNorm is replicated on projection workers rather
than distributed as a cross-core reduction. Embedding, LM, and argmax run
once per token; the other five launches run per layer. There are 83 launches
per token for 1B and 163 for 8B.

The exporter's placement pool contains 118 workers: a 12-by-10 grid minus
its two service cores. It targets the smallest supported layout rather than
using every physical worker on a larger card. Projection placement also
requires a multicast rectangle. Standalone RMSNorm/matmul/probe programs
outside this decode graph have caller-selected shapes and core counts.

## Attention implementation

Each worker handles all four queries that share a KV head and a disjoint,
interleaved subset of that head's 32-token cache blocks. One launch does
everything; there is no separate merge program.

1. **Gather.** qkv writes dense row-major `q`, `k`, `v` vectors. BRISC builds
   the four RoPE operand rows (x, swapped halves, cos, sin) with about 23 NoC
   reads in one transaction: a KV head's four query heads are contiguous, and
   `rotate_half`'s sign lives in the sin table (first half negated). No scalar
   copy loops.
2. **Stream.** BRISC starts reading cache blocks as soon as the gather is
   issued; it no longer waits for RoPE or the cache append. Each tile's reads
   rotate over all three NoC 0 ports of its DRAM bank: one port per bank
   capped the stream near 330 GB/s, three reach the DRAM peak (~500 GB/s
   between 4K and 8K).
3. **Current token.** Only the partition that owns the current block appends
   the new K/V row to DRAM (others used to write identical bytes). That block
   is read like any other and the rotated K/V rows are patched into it in L1,
   so nothing reads its own append back from DRAM.
4. **Merge.** Every live partition NoC-writes its FP32 (O, m, l) state into its
   slot of the head's first worker's L1 (a 48-tile, 192 KiB CB on 8B), then
   bumps that worker's counter with a non-posted atomic increment. The merger
   waits for the count, re-arms it, and runs the stable merge (rescale to the
   common maximum, combine, normalize once) on the states in place.

The merge counter is a persistent L1 word below the kernel data region, listed
under `persistent` in the manifest and zeroed at install. It cannot be cleared
per launch: dispatch does not order unicast writes before GO, so a late clear
erased early increments and hung the merger. A posted atomic increment also
hung intermittently; the non-posted form (response to a scratch word) does not.

The same binaries and core lists run at every position. A device-side policy
picks how many of the 8 partitions per KV head are active:

| Context length | Partitions per KV head | Active workers |
|---|---:|---:|
| 1–128 | 1 | 8 |
| 129–2560 | 4 | 32 |
| 2561–8192 | 8 | 64 |

Each extra partition adds a state the merger combines serially. Measured on a
p150a, 4 partitions win below about 2.5K tokens (8B) to 3.5K (1B), and a
capacity of 8 beat 12 at every length (8B, 8K: 99 vs 107 us). The capacity is
`attention_partitions` in the old runtime and `--attention-partitions` in the
exporter (0 selects the unsplit baseline; 4/8/12 select capacities). With the
same policy, the kernels reproduce the previous implementation's outputs bit for
bit; changing the policy changes the summation order of long prefills.

Fused attention exceeds 4 KiB on TRISC0/1, so `fw/abi.h` gives each TRISC a
6 KiB slot; `DATA_BASE` moved from 0xE840 to 0x11840.

## Measurements and validation

Per-layer attention time on device (us, `--profile`), before and after this
change; "before" includes the separate merge launch:

| Context | 1B before | 1B after | 8B BF16 before | 8B BF16 after |
|---:|---:|---:|---:|---:|
| 16 | 32.2 | 11.2 | 47.9 | 16.0 |
| 512 | 43.2 | 24.0 | 63.8 | 30.5 |
| 2048 | 56.1 | 36.4 | 84.8 | 49.3 |
| 4096 | 80.0 | 50.9 | 122.1 | 67.2 |
| 8000 | 97.5 | 61.8 | 167.6 | 99.0 |

qkv costs 0.7 us (1B) to 2.2 us (8B) more for its dense outputs. Where the rest
goes, from in-kernel timestamps and ablations on the old kernel (8B, 16 tokens,
~39 us): about 25 us was BRISC gathering heads from per-core compact shards
with scalar copies, 4 us NCRISC re-tiling Q, 2 us the append acknowledgement
before the first read, 8.5 us the merge launch. At 8K the cache stream was
DRAM-port bound; deeper read pipelining (whole loop in one transaction) and
contiguous 8 KiB reads did not help.

What still costs: the merger combines states one at a time (about 1 us each on
8B), and with 4 partitions each worker's QK/softmax/PV pipeline (about 2 us
per block on 8B) rather than DRAM sets the time.

Hardware validation: 84 cases pass, comparing unsplit, 32-, 64-, and 96-worker
variants against NumPy and checking identical repeated replay; the fused cases
also check that exactly one partition's append reaches both caches. All three
models' 64-token references match, and 24-token generations after real
2K/3K/5K/6K-token prompts match the previous kernels.

Reproduce from `blackhole-py-old`:

```sh
../.venv/bin/python -m pytest tests/compute/fpu/test_llama_attention.py --bh-hardware --bh-device 0 -q
../.venv/bin/python tools/bench_llama_attention.py --device 0 --lengths 32 512 4096 8192 33 --json /tmp/attention.json
../.venv/bin/python tools/rewrite_export/export_llama3.py --model all --rewrite ../blackhole-py
```

Export complete model artifact sets together: parameter tables, the merge
counter and data addresses move with the programs, and the firmware slot sizes
in `fw/abi.h` must match the exporter's.

## Other kernels

Projection counts are unchanged. `config.py` records earlier measurements
where 104 and 117 workers were slower, citing bandwidth saturation and repeated
activation reads. Argmax already scans one shard per projection worker;
embedding moves just one small vector. Neither is an obvious candidate for
more workers without evidence from profiling.

Sources: `kernels/llama3-{1b,8b-bf16,8b-fp8}/manifest.json`, and
`../blackhole-py-old/examples/llama3/{config,runtime,kernels}.py` plus
`../blackhole-py-old/tools/rewrite_export/export_llama3.py`.

## Completed attention cleanup

The earlier kernel audit identified repeated work that the implementation above now removes:

- Publish Q once and retain it across cache blocks, instead of republishing it to accommodate an operand-consuming matmul helper.
- Pack each probability tile once and retain it across V feature tiles. The old path packed identical data twice for 1B and four times for 8B.
- Mask invalid score columns during the SFPU pass, removing the BRISC mask/zero tiles and their unpack/FPU handoffs.
- Compute the normalization reciprocal once per query row and reuse it across output features.
- Use partial attention plus merge for long contexts, with exact-zero rescaling and the validation described above.

The old audit's warning about an unsplit-only exporter and relaxed 4K checks describes the previous implementation;
it is superseded by the exported partitioned path and 84-case validation above. The long-prefill ring timeout was
caused by submitting one CALL per token with a fixed 10-second ring wait, although retiring 1024 8B BF16 tokens
takes about 34 seconds. Prefill now submits one ranged CALL over the existing DRAM graphs, followed by a completion
signal; graph timeouts also propagate to ring submission. On card 1, a real 4097-token prefill plus 64 decode tokens
completed in 138.75 seconds. Reproduce with `python bench.py --device 1 --prefill 4097 8b-bf16`;
`python test_graph.py --device 1` checks range, stride, chunk boundaries, and address rollover. Decode remains
host-driven one token at a time, including its EOS check. The earlier 150-token signal timeout was not reproduced
after a clean reset, so its cause remains unconfirmed.

Attention still needs the pack → L1 → unpack handoff to feed probabilities into FPU matmul, and Dst contents must
survive that handoff. The old `Pack._release_dst` helper invalidates Dst, while attention releases the semaphore
directly to preserve its state. The assembler should distinguish releasing ownership from clearing accumulators.

Separating Q gathering, RoPE, cache append, attention, and output rearrangement into clearer internal stages is
still useful. They can remain fused in one launch; clearer source boundaries do not require extra dispatches.

## Kernel review and remaining work

| Family | Assessment | What I would change |
|---|---|---|
| **Embedding** | Straightforward indexed read followed by write. | Keep. It establishes scalar indexing and reader-to-writer handoff requirements. |
| **QKV / gate-up / O / down / LM** | Sensible basic structure: retain X, stream weight rows, reduce each dot product. | Clean up output assembly and ownership; don’t replace the algorithm merely because its code is verbose. |
| **Fused RMSNorm** | Understandable baseline, but stores X and gamma together in Dst and uses all-SFPU math. | Compare with the existing hybrid implementation before choosing the canonical kernel. Arithmetic order and rounding must remain explicit. |
| **SwiGLU / residual epilogues** | Ordinary compute with considerable layout-conversion plumbing. | Simplify compact/dense layout boundaries. Keep byte addressing and explicit conversion. |
| **Attention merge** | Serial reduction of the live partition states on each head's first worker, in L1. | Merge in a tree or merge several states per SFPU pass; it is the main cost of more partitions. |
| **Argmax** | More complexity is justified than its appearance suggests. | Preserve tie-breaking, padding, ordered keys, and mailbox ordering. Keep runtime publication separate from the numerical reduction. |
| **Blocked matmul** | Complex for substantive reasons: multicast, operand reuse, partial accumulation, layout conversion, overlapping transfers. | Use a simpler matmul as the first compiler target; retain this as an advanced scheduling benchmark. |
| **Q6, reduction experiments, ISA/movement probes** | Experiments and hardware evidence, not canonical application kernels. | Preserve their checks without making every experimental schedule a v1 requirement. |

Two broader observations:

- **Projection output movement deserves a separate cleanup.** Each dot result is packed into a tile-sized CB slot, read by NCRISC, and placed into a compact buffer; dense output then requires another rearrangement. The packer uses scalar mode, so this is not necessarily a full tile of payload per scalar. Still, it is substantial bookkeeping. A measured experiment with grouped results or direct placement would be worthwhile. [Output assembly](/home/boop/tenstorrent/blackhole-py-old/examples/llama3/kernels.py:299).

- **Some matmul complexity really cannot be wished away.** Its prepared operand buffers are read both by local compute and by multicast. Storage must remain alive until both finish. The implementation tracks local consumption and transmission separately. Retained SPSC CBs alone don’t express that concurrent lifetime. We can defer it in v1, but should not call it a bad kernel pattern. [Multicast sender](/home/boop/tenstorrent/blackhole-py-old/examples/matmul_peak_kernel/kernel.py:1103).

## Implications for the assembler

I would keep the current core: byte buffers, retained/consumed CB blocks, explicit copies, source-bank handoffs, persistent Dst, and explicit math.

I would avoid adding features specifically to reproduce repeated Q publication, duplicated P packing, dummy mask/zero queues, or instruction-word patching in the Python helpers.
