**Implementation follow-up:** The attention cleanup and context partitioning are now implemented. Q/P reuse, SFPU tail masking, shared reciprocal, and exact-zero rescaling are covered by hardware tests. Exported attention now uses a fixed partial + merge sequence with up to 96 partial workers and 8 merge workers. See [kernel_core_usage.md](kernel_core_usage.md) for current counts, measurements, and validation. The audit below describes the earlier implementation.

**Yes. We should simplify attention before letting it dictate the IR.** Several awkward patterns come from our helpers, while others represent real data movement that a better kernel will still need.

I reviewed the llama3 kernel families, their export variants, standalone RMSNorm, the blocked matmul implementation, and relevant correctness/performance tests. I also inventoried the test/probe corpus; this was a source audit, not a line-by-line correctness proof of all 132 test files or a new hardware benchmark.

**Attention has the clearest avoidable work**

1. **Q is repeatedly published even though it never changes.**

   The reader reserves and pushes `query_cb` every block without writing new data. This accommodates `move_matmul`, which always pops both operands.

   Load/publish Q once, retain it, and consume only K. Our proposed per-input consumption already fixes this. [Current publication loop](/home/boop/tenstorrent/blackhole-py-old/examples/llama3/kernels.py:1002).

2. **The same probability tile is packed repeatedly.**

   For each attention block, pack writes Dst tile 0 into `probability_cb` once per feature tile. That is **two identical packs for 1B, four for 8B**, because the subsequent matmuls consume a fresh probability tile each time.

   Pack P once, reuse it across all V feature tiles, then release it. This reduces those particular pack operations by 2×/4×; it is not a prediction of overall speedup. [Probability packing](/home/boop/tenstorrent/blackhole-py-old/examples/llama3/kernels.py:1113).

3. **Tail masking takes an unnecessarily long route.**

   BRISC constructs a mask tile and a zero tile; unpack loads both; FPU adds their result to scores. We already visit scores on SFPU immediately afterward.

   I would try applying the tail predicate during that SFPU pass. That could remove both CBs and their source handoffs. Lane-to-column mapping and inactive rows need correctness tests, but this looks like ordinary predicated math—not a reason for another IR feature. [Mask construction](/home/boop/tenstorrent/blackhole-py-old/examples/llama3/kernels.py:967).

4. **Final normalization repeats reciprocal work.**

   `_softmax_normalize_program` calculates `1 / sum` for every output feature chunk, although the denominator is shared across features for a query row.

   Compute the reciprocal once and reuse it. Whether to retain it in LRegs or Dst is a scheduling choice. [Normalization helper](/home/boop/tenstorrent/blackhole-py-old/examples/llama3/kernels.py:1624).

5. **The fused kernel mixes several different jobs.**

   Gathering projection output, RoPE, cache append, attention, and output rearrangement are intertwined. Its `ready` CB is just a completion signal between NCRISC and BRISC.

   I’d give those jobs explicit internal boundaries and readiness contracts. They can remain fused in one launch; separating the source code does not require extra launches.

**What attention should look like**

At the algorithm level:

```text
prepare Q and append the new K/V
retain Q in L1
initialize running maximum, sum, and output in Dst

for each assigned cache block:
    stream K and V
    compute scores using retained Q and consumed K
    apply tail mask and update online softmax

    pack P once into L1
    return Dst ownership to math
    for each output feature:
        reuse P, consume V, accumulate into output
    release P

normalize output
pack and write output
release Q
```

That still requires the ordinary pack → L1 → unpack path to feed P into the current FPU matmul algorithm. **Removing repeated copies does not remove that handoff.** It also needs persistent Dst contents across packing—already the intended v1 contract.

There is a particularly telling helper mismatch: ordinary [`Pack._release_dst`](/home/boop/tenstorrent/blackhole-py-old/ttko/pack.py:137) invalidates Dst. Attention bypasses it and releases the semaphore directly to preserve its running state. Separating “release ownership” from “clear accumulators,” as v1 does, is the right fix.

**There’s also an attention validation gap to fix before optimizing**

The export script explicitly **disables split attention**, using the unsplit path at every position. Meanwhile, the attention test deliberately exempts unsplit attention at 4096 tokens from its usual accuracy thresholds, citing accumulated numerical error.

That doesn’t establish that exported inference is broken. It does mean our current tests don’t give the exported long-context path the same accuracy guarantee. I’d address that before declaring the replacement successful. [Export configuration](/home/boop/tenstorrent/blackhole-py-old/tools/rewrite_export/export_llama3.py:59), [accuracy assertions](/home/boop/tenstorrent/blackhole-py-old/tests/compute/fpu/test_llama_attention.py:73).

**The other kernel families**

| Family | Assessment | What I would change |
|---|---|---|
| **Embedding** | Straightforward indexed read followed by write. | Keep. It establishes scalar indexing and reader-to-writer handoff requirements. |
| **QKV / gate-up / O / down / LM** | Sensible basic structure: retain X, stream weight rows, reduce each dot product. | Clean up output assembly and ownership; don’t replace the algorithm merely because its code is verbose. |
| **Fused RMSNorm** | Understandable baseline, but stores X and gamma together in Dst and uses all-SFPU math. | Compare with the existing hybrid implementation before choosing the canonical kernel. Arithmetic order and rounding must remain explicit. |
| **SwiGLU / residual epilogues** | Ordinary compute with considerable layout-conversion plumbing. | Simplify compact/dense layout boundaries. Keep byte addressing and explicit conversion. |
| **Attention merge** | Reasonable streaming reduction of four partial states. | Keep the algorithm; express its repeated operations and persistent state more clearly. |
| **Argmax** | More complexity is justified than its appearance suggests. | Preserve tie-breaking, padding, ordered keys, and mailbox ordering. Keep runtime publication separate from the numerical reduction. |
| **Blocked matmul** | Complex for substantive reasons: multicast, operand reuse, partial accumulation, layout conversion, overlapping transfers. | Use a simpler matmul as the first compiler target; retain this as an advanced scheduling benchmark. |
| **Q6, reduction experiments, ISA/movement probes** | Experiments and hardware evidence, not canonical application kernels. | Preserve their checks without making every experimental schedule a v1 requirement. |

Two broader observations:

- **Projection output movement deserves a separate cleanup.** Each dot result is packed into a tile-sized CB slot, read by NCRISC, and placed into a compact buffer; dense output then requires another rearrangement. The packer uses scalar mode, so this is not necessarily a full tile of payload per scalar. Still, it is substantial bookkeeping. A measured experiment with grouped results or direct placement would be worthwhile. [Output assembly](/home/boop/tenstorrent/blackhole-py-old/examples/llama3/kernels.py:299).

- **Some matmul complexity really cannot be wished away.** Its prepared operand buffers are read both by local compute and by multicast. Storage must remain alive until both finish. The implementation tracks local consumption and transmission separately. Retained SPSC CBs alone don’t express that concurrent lifetime. We can defer it in v1, but should not call it a bad kernel pattern. [Multicast sender](/home/boop/tenstorrent/blackhole-py-old/examples/matmul_peak_kernel/kernel.py:1103).

**What this means for v1**

I would keep the current core: byte buffers, retained/consumed CB blocks, explicit copies, source-bank handoffs, persistent Dst, and explicit math.

I would avoid adding features specifically to reproduce repeated Q publication, duplicated P packing, dummy mask/zero queues, or instruction-word patching in the Python helpers.

My suggested next step is **a cleaned-up attention implementation in the existing Python backend**, preserving its numerical choices initially. Validate fused RoPE/cache append, tail blocks, repeated launches, and short/long contexts; then measure it. Alongside streaming copy, projection, and RMSNorm, that gives us a much better set of kernels to design the compiler around.

No kernels or spec were changed during this audit.
