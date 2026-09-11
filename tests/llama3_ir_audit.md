# Llama 3 IR expressibility audit

Snapshot: 2026-09-10. This is an audit of the current implementation, not a replacement specification. No inference kernels or lowering were changed.

**Conclusion: the IR does not yet express the complete Llama kernel set.** It expresses the core RMSNorm arithmetic and basic streaming/retention. Several missing operations and contracts are observable before lowering. Successful tracing is not a correctness or performance proof.

## Scope and method

Read the kernel builders and relevant helpers in:

- `blackhole-py/examples/llama3.py`: the ten existing Program-building families.
- `blackhole-py-llama3-8b/examples/llama3.py`: the corresponding ten families, including fused projection epilogues, fused RoPE/cache/attention, and autonomous argmax publication.
- `blackhole-py-llama3-8b/examples/llama3_prefill.py`: both new builders, plus their reuse of decode programs.
- `blackhole-py-llama3-8b/examples/llama3_row_major.py`: K0 and its copy/square/xgamma/GAPOOL alternatives.
- Supporting SFPU, FPU, NoC, and unpack recipes in the 8B worktree.

An AST inventory checked the direct Program builders in all four files. CPU-only probes exercised selected representation boundaries. No hardware was accessed. Speculative, FP8/TP2, other worktrees, historical validation snapshots, and future tiled-GEMM prefill are outside this audit. The existing prefill is chunked repeated GEMV with retained weights, not a full tiled prefill implementation.

The detailed references below use the 8B file unless otherwise stated. Path prefix: `/home/boop/tenstorrent/blackhole-py-llama3-8b/`.

## Complete kernel-family inventory

| Family and source | What is expressible | Missing for the existing kernel |
|---|---|---|
| `decode_embedding`, `examples/llama3.py:1992` | Parameter-based address arithmetic, resident reads and writes | Actual token is `token_history[token_pos]`, a device memory value. L1 indexing still returns a byte view, not a typed scalar. Replacing it with a host parameter changes autonomous execution. |
| `rmsnorm`, `:2032` | SFPU square/MAD reduction, lane sum, rsqrt, gamma application, full-block transfers | Mathematical rewrite is available. Existing unpack mapping, BF16 rounding contract and LOADMACRO schedule are not established by tracing. No cycle/bitwise equivalence claim. |
| Fused K0, `examples/llama3_row_major.py:464` | Runtime-token version is the existing IR sketch; raw residual can have two L1 readers | Device-read token missing. SFPU versus GAPOOL alternative, source/Dst movement, scaler broadcast and precision must be specified. Readiness fan-out is described by uses but not yet lowered. Optional timing is instrumentation, not math. |
| `decode_projection`/`decode_qkv_projection` and `_decode_fused_projections`, builder `:458` | Streaming weights, retained activation, elementwise FPU multiply, SSA dot reduction | Existing projection uses ELWMUL + SFPU reduction, not necessarily MVMUL. Scalar-result packing, local scalar assembly, zeroing, and output/internal CB production are missing. Fused norm/residual/SwiGLU variants inherit these gaps. |
| `decode_projection_residual`, builder `:829` | Residual add itself | Reassembles compact BF16 slots with local loads/stores/copies, then packs/scatters. Current L1 API cannot perform that reassembly. |
| `decode_swiglu`, `:984` | Arithmetic expression through current `swiglu` composition | Current exp/reciprocal recipes differ from decode; numerical domain and precision need matching. Existing output CB flow is not represented. A resident-L1 rewrite can represent the local mathematical flow, not establish the same schedule. |
| `decode_compact_to_dense`, builder `:1107` | Fixed byte-range NoC writes and compile-time layout arithmetic | Local scalar copy/gather/zero operations missing. Compact physical layout must stay explicit. |
| `decode_rope`, builder `:1223` | FP32 multiply/MAD after operands are assembled | Split-half rearrangement/sign manipulation, table-row extraction and local copies missing. Exact kernel uses BF16 Dst with SFPU FP32 loads and explicit `round_bf16`; current SFPU rejects BF16 Dst. FP32-Dst rewrite is possible but changes resource requirements and still needs rounding semantics. |
| `kv_cache_write`, `:1467`; fused `_append_cache_rows`, `:1396` | Fixed-size 32-byte writes at runtime addresses can be expressed using arithmetic (`//`, `%`, `*`, `+`) and fixed L1 slices | Plain append needs no fundamentally new arithmetic primitive. Requires a defined buffer bank/layout binding and acknowledged write semantics. Fused producer paths inherit local assembly gaps. |
| GQA attention, builder `:1803`, helper `:1580`, fused prep `:1687` | Persistent Dst allocations, runtime block loop, explicit SFPU positions, subgroup sum ladder | SFPU max, correct exp sentinel behavior, runtime tail conditions, internal pack-to-unpack stream, explicit conversion, matmul transpose/mapping contract, local rearrangement, and cache-write/read ordering. Cannot currently express the full program. |
| `decode_argmax`, `:656` | SSA can express a reduction once scalar operations exist | Typed local reads/writes, bitwise key construction, comparisons/select/branches, remote L1 partials/readiness, PCIe output and runtime-parameter publication absent. No equivalent one-launch distributed program in current IR. |
| Prefill grouped projections, `examples/llama3_prefill.py:82` | Retain one streamed weight item across token iterations; release after all uses. This traces today. | Runtime-offset fixed-width L1 windows, internally produced retained normalized inputs, scalar output assembly and the projection contracts above. Unrolling the small fixed token count can avoid some dynamic windows, at a code-size cost. |
| Prefill SwiGLU/scatter, `:169` | Elementwise arithmetic with stated domain limits | Local scatter, output producer stream, numerical and conversion contracts. Attention/O/down/embedding/LM/argmax are reused decode programs, not additional new prefill kernels. |

## Missing pieces, ordered by impact

### 1. Local memory operations are still missing

We removed `noc.read_scalar` in favor of runtime parameters, but that only handles launch-supplied integers. It does not handle the actual token history read, packed projection scalars, rearranged RoPE operands, or argmax candidates.

`noc.read(...)[0]` is currently a one-byte `View`; multiplying it raises TypeError. The previously discussed typed indexing was never implemented. Add typed scalar access and local copy/fill operations without exposing RISC-V registers. Keep byte ranges distinct from typed indexing.

A second gap: `data[runtime_offset:runtime_offset + fixed_size]` is rejected because slice bounds must be Python integers. Indexing with a GPR yields only a one-byte view. A named fixed-width byte window with a symbolic offset would preserve register/offset semantics and support the prefill input addressing pattern.

### 2. Internally produced streams and readiness edges

`cb.read` only declares DRAM-fed storage. Existing pipelines include:

- PACK -> UNPACK: attention probabilities consumed by PV.
- PACK -> resident L1 -> UNPACK: normalized inputs reused throughout projection.
- PACK -> NCRISC local scalar assembly -> UNPACK: fused gate/up and residual epilogues.
- NCRISC -> BRISC readiness: fused RoPE/cache preparation before attention cache reads.

Attention explicitly packs the same P tile four times while preserving Dst tiles 1..7 (`:1954`). This does not require freeing/reallocating persistent state. An internal producer/consumer item abstraction and explicit storage effects can retain the single sequential-program model; a separate scheduler API is unnecessary.

Using ordinary L1 pack/unpack can express some mathematical dependencies, but does not yet describe a bounded concurrent output pipeline. Likewise a `noc.write` has a DRAM write effect, but `cb.next` reads a StreamRange whose relationship to that write is not yet an alias/order contract. Prior cache writes must complete before subsequent reads, even across generated threads.

### 3. Comparisons, selection and runtime conditions

`VReg < VReg` is unsupported, and `sfpu.predicate` accepts only a host integer mask. Attention conditionally applies the tail mask on the last KV block and builds it from `valid_columns`. Argmax compares values and retains indices with defined tie order.

Needed: typed comparisons/select and structured runtime conditions, plus a way to construct data-dependent SFPU lane masks. A sum across all 32 lanes is also different from attention's four independent eight-lane row reductions. The existing shft2/add primitives can express the subgroup sum; max is absent.

### 4. Numerical fidelity is a real gap

Current `exp` is the PoC's degree-8 polynomial with repeated squaring, intended for a bounded finite domain. Decode's SFPU exp uses a different range/exponent construction (`ttk/sfpu.py:390`). Decode reciprocal also uses a different correction sequence (`:458`). Availability of similarly named helpers does not prove numerical equivalence.

A CPU evaluation of the current emitted exp arithmetic gives **exp(-inf) = +inf**. Attention needs **exp(-inf) = 0** for masked scores and the initially negative-infinite running maximum. This is outside the helper's documented domain, but inside the kernel's real domain: it blocks reusing that helper unchanged.

`round_bf16` (`ttk/sfpu.py:217`) is missing. Pack has no rounding-mode contract. RoPE uses explicit BF16 rounding before storage. Add the proven recipes/conversions and their semantic tests; do not silently substitute a pack/unpack round trip and assume the same result or cost.

### 5. FPU shape, ordering, accumulation and movement contracts

The low-level MVMUL primitive exists and the aligned A pair is checked. That alone is not a specified tile matmul. The existing matmul expands face products, K accumulation, transpose-sensitive operand traversal and fidelity phases (`ttk/fpu.py:246`). `unpack` currently offers no transpose/mapping selection. The mapping of A/B physical slots to products and Dst write footprints needs a precise contract or an explicit helper expansion.

More seriously, `fpu.op(..., accumulate=False)` currently advertises no destination read for all operations. The existing raw FPU recipe rejects non-accumulating modes for operations other than add/sub; overwrite matmul is implemented by zeroing before accumulating. Decide whether overwrite is a pseudo-op that includes initialization or expose zero/init explicitly. Otherwise SSA effects can be wrong despite successful tracing.

Source-to-Dst copies, zeroing, broadcast/scaler paths and format conversions need descriptions. Some can be composed through existing primitives, but their configuration, full write footprint and precision cannot be left implicit in arbitrary modifier dictionaries.

### 6. Distributed argmax and launch binding

Argmax is already cross-core, including in the current blackhole-py copy. It writes partials to reducer L1 and polls readiness. The 8B variant additionally publishes next-token runtime data to workers by multicast, and writes host output via PCIe. `MemorySpace` only contains DRAM; these endpoints are not representable.

A two-launch DRAM reduction is a possible redesign, not a faithful translation of the existing one-launch kernel. Host/result publication and autonomous runtime updates can belong to the launch/runtime layer, but remote reduction cannot simply be classified as register allocation or hidden synchronization.

Buffer core/shard/bank metadata and per-core parameter binding also need a host-side contract. They need not become tensor operations in the per-core IR. Current parameters can carry specialized starts/heads once launch binding exists, but that binding does not yet exist.

## What should stay lowering work

Physical register allocation, fixed-register copies, hazard insertion, RWC encoding for the existing affine indices, and thread projection remain lowering tasks. Replay/MOP/LOADMACRO selection affects preserving the optimized schedule; absent those mechanisms we cannot claim performance parity. A callback body already unrolls fixed offsets cleanly, so the inspected attention Dst accesses do not justify arbitrary computed Dst indices: its physical offsets are constants plus block positions.

Runtime loop bounds work. `cb.read(count=...)` currently only accepts a positive Python integer. Declaring a maximum-capacity source and consuming a runtime prefix may be sufficient under acquisition-driven production; define whether count is a bound or exact consumption before adding another stream API. This is a contract question, not evidence that all dynamic attention loops are impossible.

## CPU probe results

Probes were run with the workspace Python, without importing device runtimes:

| Probe | Result |
|---|---|
| Existing RMSNorm sketch with runtime token parameter | Traces: 83 instructions |
| Retain a weight item across four token iterations | Traces |
| Load a token via L1 indexing, then multiply it | TypeError: View has no multiplication |
| Fixed-width L1 slice at runtime offset | ValueError: invalid view bounds |
| Runtime scalar comparison | TypeError: `<` unsupported |
| SFPU max / BF16 round / internal CB allocation | Missing public methods |
| SFPU load from BF16 Dst | Explicitly rejected |
| Runtime CB source count | Explicitly rejected |
| Current exp arithmetic at negative infinity | Positive infinity; attention requires zero |

Probe script: `/tmp/llama3_ir_probes.py`. These are focused reproductions, not full-kernel numerical tests. Existing model tests are separate.

## Recommended next implementation slice

1. Typed L1 scalar access/copy/fill and symbolic fixed-width windows.
2. Internal CB production and storage/readiness effects, demonstrated by a projection scalar-output path and attention P -> PV.
3. SFPU max/compare/select, runtime conditions, proven exp/reciprocal and BF16 rounding.
4. Define FPU overwrite/accumulation and matmul mapping/transpose contracts.
5. Choose the distributed argmax/runtime boundary explicitly.

Then translate one complete retained-weight prefill projection and one complete GQA block, including all movement. Until those trace and their numerical references pass, the entire kernel set cannot be signed off as expressible.
