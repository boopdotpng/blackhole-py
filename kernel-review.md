# Layer 1 and TTRV kernel review

**Keep UOps for the values. Exit the graph when binding resources.** This follows [direction.md](direction.md). A product, lane predicate or remote tile is a useful thing to share across consumers. Two releases on a semaphore, two advances of a Dst cursor and two repetitions of a replay body each have observable order. Represent those in the per-RISC instruction streams. The current rewrite has the graph, a functional evaluator and an executable SFPU compiler. Its silicon test supplies unpack, pack, loop control and synchronization by hand. A general kernel-to-five-images compiler is still missing.

The inventory covers the local blackhole-py working tree, including its untracked sources. Its 65 example TTRV files comprise 56 with RISC entry points and nine shared include files. By directory, there are 31 Inkling, 12 Qwen, seven common, five shared, five prefill, three batch and two Nanbeige files. The older Python compiler supplies the hash-consed UOp and pattern machinery. The TTRV compiler separately implements argument binding, layout, code generation and role ownership. The handwritten host graph tests also exercise persistent L1 and disjoint worker sets across launches. [Older graph core](../blackhole-py/compiler/uop.py) · [TTRV compiler](../blackhole-py/ttrv/__init__.py) · [Resident graph test](../blackhole-py/test/test_table.py)

## Which kernels fit?

| Kernel family and references | Layer 1 today | Smallest useful change |
|---|---|---|
| Whole-page copy, embedding, admission, stage tables, cache append and host output | Fixed full tiles, scalar indices, gates and host buffers fit. The last chunk of batch admission has a runtime length. Row/panel conversion has independent pitches and sub-tile destinations. NoC size currently lives in a static argument and the evaluator reads whole tiles even for byte counts. | Put dynamic extent and source/destination offsets on value edges with explicit units. Use a view for strided data and a worker-qualified L1 address for peer publication. Lower eligible contiguous runs to one transfer. [Admission](../blackhole-py/examples/batch/admit.ttrv) · [Host unpack](../blackhole-py/examples/qwen38/unpack_host.ttrv) |
| RoPE, SwiGLU, convolution, residual and GDN point math | The inner arithmetic, explicit BF16 rounding, multiple inputs and reused values fit. Some kernels load a per-slot runtime scalar into an SFPU register. The SFPU emitter accepts Dst inputs and literal constants, and lacks a runtime scalar broadcast path. | Lower a loop-invariant scalar operand to a programmed register per update. Bind paired faces or tiles explicitly. Use MULACC where a kernel specifies which product rounds first. [RoPE](../blackhole-py/examples/shared/prompt_rope.ttrv) · [Weighted SwiGLU](../blackhole-py/examples/inkling/swiglu.ttrv) · [GDN convolution](../blackhole-py/examples/qwen38/gdn_conv.ttrv) |
| RMSNorm, gates, routers, argmax | Logical row sum/max and row argmax exist and evaluate on CPU. The emitter cannot compile them. Physical eight-lane row reduction, reduction across an entire footprint and reduction across a logical 32-column row are three different schedules. Global argmax carries a value and its original index over many tiles and workers. | Specify axes/layout, reduction identity, tie order and index origin. Lower row reductions to face loads, rotates, adds/max and broadcast. Lower stable indexed reductions to a value/index pair with one comparator. Use index capture when its physical index can be converted to the logical index. [Lane reduction](../blackhole-py/examples/common/reduce_lanes.ttrv) · [Top-k router](../blackhole-py/examples/inkling/router.ttrv) · [Argmax](../blackhole-py/examples/shared/argmax.ttrv) |
| Decode and prompt attention, recurrent GDN state, gated chunk updates | Tile contraction, exp, masks and individual sums fit. Online softmax carries multiple mutually dependent values across iterations. Row offsets span even/odd columns and both faces. Scalar mutable slots can model sequential updates, but lose the simultaneous old-state reads and the intended register lifetime unless ordered explicitly. | Add a loop with explicit carried values and yielded replacements. Bind a tuple of live Dst tiles or resident LRegs across the loop. Recognize the max/rescale/sum update and fold broadcast into its consumers. [Shared attention primitives](../blackhole-py/examples/common/attention.ttrv) · [GDN chunk](../blackhole-py/examples/qwen38/gdn_chunk.ttrv) |
| Decode projection, expert matmul, prefill and SUMMA | MVMUL, fidelity, transpose-on-unpack, L1 accumulation, multicast and reduction can describe the tile mathematics. Host tests evaluate a multicast matmul. There is no generated panel schedule, source-bank ownership, rotating sender credit or multi-slot completion protocol. | Derive row/column multicast from index invariance, bind panel lifetimes and lower affine face accesses to ADDR_MOD, replay and MOP. Scope waits to the publishing transfer. The SUMMA inner replay already fills all 32 words. [SUMMA](../blackhole-py/examples/prefill/summa_projection.ttrv) · [Decode projection](../blackhole-py/examples/nanbeige/projection.ttrv) |
| MoE plan, routing, packing, cache/history publication | Bounded scalar RANGE/IF/load/store covers much of the arithmetic. The planner uses data-dependent counts and break. Publications use remote atomic increment and completion waits. The grid model lacks arbitrary worker subsets across persistent launches. | Rewrite a bounded break loop as a counted range when its bound is known, e.g. ceil(count/32) for expert groups. Model general remote publication with release/acquire effects and an explicit peer address. Lower the counter/flag implementation from that contract. [MoE plan](../blackhole-py/examples/inkling/moe_plan.ttrv) · [History commit](../blackhole-py/examples/inkling/prompt_history.ttrv) |

Raw REPLAY/MOP words can encode a chosen inner sequence. They carry no description of lane permutation, implicit register clobbers, destination strides or NoC visibility. They cannot establish functional equivalence of an entire kernel. Keep the raw escape hatch for schedules with declared inputs, outputs and clobbers.

## Operations and missing rewrites

- Keep RANGE, effects, residency, layout-sensitive reductions, casts, bitcasts and fidelity-bearing contractions distinct. The seven areas in the design are categories. Compressing the enum to seven tags would put the same distinctions into unchecked arguments.
- Once tuple reductions exist, make ARGMAX a builder for stable max-by-value/min-by-index. Once reductions have explicit axes and broadcast semantics, REDUCE_ROW can become a builder too. GATHER and ALLGATHER could share one collective operation with explicit recipients, but only after their root/visibility semantics have separate tests. Move REPLAY and MOP into schedule annotations when the binder can consume them. These changes can shrink the public op set without hiding missing behavior behind a generic hardware call.
- Keep convenience functions for SiLU, sigmoid, GELU and tanh. They already build ordinary expressions. Log2 now uses the ordinary integer-to-FP cast, which emits both required hardware conversions. Legacy primitive names still lower for existing callers. A one-input TRANSP failed to load its source and silently read unrelated registers. It now fails at compile time. Put the four-register permutation inside the reduction backend or give it four explicit inputs and an output selector.
- Keep reciprocal square root as an accuracy choice. The old reciprocal-of-sqrt matcher ran after the child had decomposed. Moving it ahead of decomposition changes zero handling. Use rsqrt explicitly on positive finite RMS inputs. An automatic fusion needs a proven input-domain and rounding contract.
- Hoist runtime broadcasts. Match reduction-of-square to an accumulator kept in an LReg across footprints. Today the elementwise fragment needs an accumulator tile load and output store each iteration. The handwritten square loop only loads x and updates the resident accumulator with MAD. [Square replay](../blackhole-py/examples/common/square.ttrv)
- Schedule independent loads into MAD latency slots, interleave even/odd footprints, and select SFPLOADMACRO only after identifying register lifetimes and address increments. The hazard model already understands macro subunits. The compiler does not synthesize the load macros, replay or MOP. [RMS scale macro](../blackhole-py/examples/common/vector_math.ttrv)
- Make the semantics of integer MUL/DIV/MOD explicit before adding selectors. MUL24 needs a range proof or expansion for full-width multiplication. RV32 scalar arithmetic and SFPU tile arithmetic need different lowering. Also specify out-of-range casts, FP comparisons on signed zero and NaN, and contraction policy. SFPGT has a total ordering of float bit patterns. [Blackhole comparison semantics](../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPGT.md)

## Code review findings

1. **Fixed silent wrong results.** Distinct requested outputs could alias one Dst tile. A repeated source in a parallel swap could be reloaded from the overwritten old tile. Explicit output positions are now reserved first, invalid assignments fail, and copy cycles hold an old value in a register. A four-way cycle runs on silicon with two writable registers. Input expressions already resident in Dst are opaque during lowering, so FMA fusion cannot reach into a previous stage.
2. **Fixed numeric ordering and selection.** Signed-magnitude CAST mapped INT_MIN to negative zero and unsigned comparisons used signed ordering. Ordered integer keys now cover i32/u32, and min/max lower through compare/select. The host lane-ID oracle previously identified columns as lanes. Its full 32×32 logical layout now agrees with silicon.
3. **Fixed precision-sensitive selection.** Fourteen of the initial 2,048 mixed-precision graph seeds failed against NumPy. The failures were all in BF16 approximation mode with conditionals. Small errors before a comparison can change its selected value by more than one unit. FP32 transcendental inputs to explicit FP32 comparisons now use the FP32 decomposition, including shared uses. Explicit BF16 casts still request rounding. The same seeds passed after the fix.
4. **Reduced lowering overhead.** Whole-DAG allocation now runs before prefix search, and the compiler uses the selected allocation directly. Trial lowering uses actual tile addresses. Signed 12-bit add/sub immediates skip programmable constant setup, including an immediate on the left of an add.
5. **Remaining evaluator risk.** Gather and allgather both stack all peers for every worker, ignoring gather's root and count. Rectangular multicast does not model receiver exclusion. Barrier staging recognizes top-level barriers. The evaluator cannot validate credit ordering or deadlocks. Test redistribution and publication with a role-level simulator or generated multi-core silicon kernels before relying on these operations.
6. **Remaining format risk.** The verifier checks the destination space of engine operations, but the SFPU API does not validate every operand dtype and width against instruction support. For example the cast emitter selects the signed conversion path for unsigned-to-float input. The fuzzer exercises FP32 inputs with FP32/BF16 approximation modes. Packed BFP8/E4M3, 64-bit scalar glue and cross-role synchronization need their own oracles.

## Device results and costs

The extended suite passed all 41 tests with 2,048 floating-point graph seeds and 64 additional integer seeds. No tested kernel hit the device completion timeout. Run the campaign from the rewrite root with `SFPU_FUZZ_SEEDS=2048 ../.venv/bin/python -m unittest discover -s test`.

The silicon oracle executes emitted words on worker 0 and reads back 1,024 values per output. The generated DAGs use shared subexpressions, two output roots, swapped Dst slots, four/eight registers and twelve arithmetic, comparison and transcendental forms. Failure output includes seed, graph, precision and register budget. A separate 64-seed integer campaign checks all 32 result bits for shifts, boolean operations, wrapping arithmetic, min/max and selection. The existing five-second completion timeout also detects kernels that fail to signal completion. Replay one case with the following command from the rewrite root.

```sh
SFPU_FUZZ_START=252 SFPU_FUZZ_SEEDS=1 ../.venv/bin/python -m unittest test.test_sfpu_fuzz_hw
```

The following are **emitted body words and modeled steady-state SFPU issue cycles per 32-lane footprint**. All rows use one compiler pass. Prologue, unpack/pack, RV32 loop control and NoC time are excluded.

| Fragment | Body words | Modeled cycles |
|---|---:|---:|
| Prompt RoPE with explicit MAD and BF16 round | 8 | 9 |
| Handwritten RoPE body in original instruction order | 8 | 10 |
| SiLU(gate) × up, FP32 | 41 | 55 |
| SiLU(gate) × up, BF16 approximation | 26 | 33 |
| Positive rsqrt, FP32 | 14 | 21 |
| Positive rsqrt, BF16 approximation | 10 | 14 |

RoPE matched the expected BF16 bits on silicon. Both bodies use four loads, multiply, MAD, round and store. The compiler issues independent loads between the multiply and MAD. On the card, the same 32-footprint loop took **646 wall-clock ticks per tile** for compiled inline issue, **639** for compiled replay, **678** for handwritten inline issue and **671** for handwritten replay. Each value was the median of 50 interleaved launches after one warmup per case. TRISC1 sampled WALL_CLOCK_L between drains around the loop, excluding replay setup, unpack and pack. All four variants matched the reference bits on every launch. These measurements cover the RoPE tile loop. Full prompt-kernel throughput also depends on input movement and worker overlap. SiLU is a candidate for direct porting. The handwritten prefill version saves an intermediate to Dst between two sweeps, whereas the eight-register rewrite fits in one sweep. [Handwritten SwiGLU](../blackhole-py/examples/prefill/summa_projection.ttrv)

### Remaining numerical boundaries measured on silicon

| FP32 expression | Silicon | NumPy reference |
|---|---:|---:|
| rsqrt(0) | 3.5788857e19 | +∞ |
| recip(sqrt(0)) | +∞ | +∞ |
| log2(0) | −127 | −∞ |
| log2(+∞) | 128 | +∞ |
| exp2(127.5) | 1.7014118e38 | 2.4061597e38 |
| exp2(128) | 1.7014118e38 | +∞ |
| sin(1e6) | −0.35182244 | −0.3499935 |
| sin(1e8) | −0.5332931 | 0.931639 |

The exp2 decomposition clamps above 127 and flushes below −126. The sin reducer loses accuracy at large arguments. The rsqrt seed assumes positive finite input, as does the handwritten normalization macro. A generic math contract would need special-value selection, a separate upper-exponent path and a large-angle reducer. Range-proven activation and normalization paths can retain the cheaper sequences.
