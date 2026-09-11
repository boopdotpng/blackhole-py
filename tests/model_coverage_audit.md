# Model / device coverage audit

Follow-up: matrix-pair placement has now been corrected and scattered-transfer
tests added. See [scatter_coverage.md](scatter_coverage.md) for current results.
The findings below preserve the original audit; loop lifetime changes, SFPU API
redesign, and item 6 integration work remain deferred.

Reviewed 2026-09-06 against the current working tree, including uncommitted
`ttk/model.py`, `tests/operation_pocs/`, and `examples/swiglu.py`.

The suite establishes substantial primitive coverage, but does **not** cover all
programs the current model accepts. The highest-priority omissions are allocation
constraints and composition contracts, followed by scattered unpack, additional
pack format/order combinations, and BF16 SFPU transfers. Adding more isolated
ordinary arithmetic cases would provide less value than closing those gaps.

This audit preserves 128-element allocation units: matrix A consumes an aligned
pair, FP32 Dst consumes two physical units per logical block, BF16 Dst one. GAPOOL
and GMPOOL retain full allocations despite their smaller useful output footprints.
“BF16” below means the model's `bfloat16`, not IEEE FP16, which is not exposed.

## Evidence and scope

- Fresh CPU run: `PYTHONPATH=. /home/boop/tenstorrent/.venv/bin/python -m pytest -q -p no:cacheprovider`
  produced **47 passed, 781 skipped**. Hardware cases require `--bh-hardware`.
- Existing `operation_pocs/review.md` and `operation_pocs/evidence/combined.xml`
  record a combined **622-case hardware pass**. This audit did not rerun hardware.
- Five frontend tests in `test_model.py`, plus
  `operation_pocs/sfpu_movement/test_operations.py::test_cpu_operand_validation`,
  exercise parts of the current model. Device tests construct raw assembly;
  there is no model-to-device lowering or end-to-end model execution test yet.
- Prefix loops inside a test are real coverage even though they do not create
  separate pytest node IDs. Conversely, numerical exception characterization
  is not an assertion that exception results are correct.

## Confirmed model problems

### 1. Matrix A alignment is missing from allocation and view constraints

`ttk/model.py:36` gives every source fragment alignment 1, and `allocate()` uses
that alignment. `mvmul()` and `_pool()` check sizes but not physical pair alignment.
The raw FPU emitter explicitly rejects odd A starts
(`operation_pocs/fpu/emit.py:21`); the retained hardware probes in
`compute/fpu/test_arithmetic_slots.py` demonstrate even-pair rounding for MVMUL
and GAPOOL.

CPU reproduction: keep a 128-element A fragment live, then unpack a 256-element
A fragment used by MVMUL. Allocation returns `(0,)` for the first and `(1, 2)`
for the matrix operand. That operand cannot be issued directly as one MVMUL.
Separately, `a = k.srcA.alloc(384); a.view(128, 256)` is accepted as a matrix
operand and can start at physical slot 1.

Required tests: live single block preceding a matrix pair; matrix views at
both offset parities; last legal pair `(6,7)`; overlapping views that impose
incompatible alignment requirements. Infer constraints from uses, repack, or
reject impossible cases explicitly. Merely aligning large root allocations
does not fix odd-offset matrix views.

### 2. Allocation ignores loop backedges

`ttk/model.py:262` flattens each loop body once and computes ordinary linear
intervals. An input initialized before a loop, read early in every iteration,
and unused later in the body can overlap scratch written late in that body.

CPU reproduction, with all input positions initialized:

```python
k = Kernel()
a, scratch = k.dst.alloc(), k.dst.alloc()
k.sfpu.l0.loadi(7)
for position in range(4):
    k.sfpu.l0.store(a, position=position)
k.repeat(2)
k.sfpu.l1.load(a)
k.fpu.zero(scratch)
assert k.allocate()[a] == k.allocate()[scratch]  # currently (0, 1)
```

Iteration two would read the overwritten input. Add invariant-input,
loop-carried-accumulator, scratch, post-loop-use, and multiple-loop tests.
This is a reproduced placement error, not a claimed hardware failure.

## Existing API coverage matrix

Paths below are relative to `tests/` unless otherwise stated. “Partial” refers
to the model's accepted combinations, not a failure of the existing tests.

| Model surface | Existing evidence | Missing or unresolved |
|---|---|---|
| `Bank.alloc`, fragment `view`, `allocate` | `test_model.py`: reuse, view lifetime, capacity failure, invalid view | Matrix alignment; loop lifetimes; mixed BF16/FP32 live allocations; nested/nonzero views; exact capacity and fragmentation cases |
| `L1.alloc`, buffer `view` | Frontend tail/offset assertions | L1 placement/capacity; overlapping views and cross-engine dependencies; actual nonzero-offset device transfers |
| `read_from`, `write_to` | `operation_pocs/runtime/test_runtime.py`: both directions/NoCs, offsets, 128/256 elements; older NoC/CB pipelines | Arbitrary short views and exact external tails; model loop stride semantics; model-driven pipeline |
| `elwadd`, `elwsub`, `elwmul` | FPU PoCs: all four broadcast modes, independent placement, FP32/BF16 Dst, add/sub overwrite and accumulation | Model multi-block shared-B and per-block-B expansion; output larger than inputs; mixed operation/configuration sequences; general precision policy |
| `mvmul` | FPU PoCs: all aligned A starts, LoFi/HiFi2, independent B/Dst, both Dst formats; arithmetic-slot and reduction compositions | Model's special A1024/B1024/D1024 full-tile branch; general multi-pair expansion; root/view alignment |
| `gapool`, `gmpool` | FPU PoCs and arithmetic-slot tests: footprints, preservation, accumulation; sum/mean compositions | Multi-pair shared/per-pair B contracts; non-unit GMPOOL scaling (tests use B=1); explicit GAPOOL fidelity policy |
| `zero` | FPU PoCs verify one owned block and guard all other Dst | Multi-block/view zero; interleaving with live SFPU and alternate Dst formats |
| `move` | All four source/Dst directions, first/last placement, both Dst formats; narrowing tests; older full-bank readback | General multi-block/views; Dst-to-source followed by real FPU consumption and subsequent unpack/bank reuse |
| `load`, `store` | SFPU movement: independently tagged lanes, four positions, placement extremes, register sources, masked preservation | BF16 Dst addressing/conversion; explicit multi-block/view transfer lowering; unrelated live-register preservation across special-register store |
| `loadi`, `copy` | Bit-pattern immediates, all exposed source registers copied to all writable registers, aliases, masks | Bitwise versus numerical API contract; configured L11–L14 state; arbitrary arithmetic using high/read-only source registers |
| `add/sub/mul/mad/neg/abs` | SFPU math: FP32, four positions, masks, aliases, repeated dependent chains | Every writable destination/register placement; preserving all unrelated LRegs; BF16 load/compute/store; cancellation/overflow/underflow contracts |
| `exp`, `reciprocal` | Native/refined recipes, bounded input grids, masks, reciprocal exponent/mantissa boundaries | Scratch allocation/preservation; chained special functions; numerical contract in model; exceptional values asserted rather than only logged |
| `predicate` | Every single lane plus structured masks, replacement from all-off, reset, masked load/store/immediate/copy/add | Preservation of live scratch candidates; tracked predicate dependencies across other recipes; data-dependent comparisons/nesting absent from API |
| `unpack.to` | Exact N=1..128 at low/high A/B slots; full aligned A256; both input formats; source-preserving FP32 Dst insertion | Scattered sequence with one publication; short A256 tails; multi-block tails; nonzero fill; BF16 Dst; clobber-aware scheduling |
| `pack.to` | Exact prefixes from FP32 Dst to BF16/F32; BF16 Dst observation in FPU tests; optimized scatter | Scatter from BF16 Dst, scatter to FP32, arbitrary order/count, CB-ring composition, exact scatter tail and nonzero page-view offset |
| `repeat`, `once` | SwiGLU record/allocate and explicit tail; raw device loops throughout suite | Model semantics through actual execution, loop allocation, full-page-plus-tail pipeline and address advancement |

## Transfer requirements: what the tests do and do not establish

### Unpack

`operation_pocs/transport/test_source.py` sweeps all N=1..128 for SrcA/SrcB
slots 0 and 7, in BF16 and FP32 input formats. Every unused element in the owned
slot is zero-filled; neighboring source slots, the other source bank, and Dst
are checked. The A256 cases test only N=256, at A starts 0 and 6.

The exact-N implementation stages bytes into L1 scratch and unpacks the padded
allocation. It does not establish a fast direct arbitrary-N hardware unpack:
the source read is exact, but UNPACR reads the padded scratch allocation.
Existing measurements include this substantial scalar staging cost.

I found no regression issuing several `unpack_source(..., publish=False)` calls
into different slots followed by one final publication and FPU consumption.
The helper exposes this option, but the tests call its default `publish=True`.
Arithmetic scatter tests initialize whole A/B banks outside timing; they prove
scattered arithmetic addressing, not scattered unpack throughput.

Add A/B slot sequences such as `(7,0,5,2)`, independently selected A and B,
changing lengths per segment, and both bank reuse and delayed math consumers.
For matrix A retain aligned pairs, e.g. `(6,7)` then `(0,1)`. Compare against
consecutive destinations with staging/setup/drain boundaries held identical.
Keep unrelated source slots, Dst, and live SFPU registers poisoned and checked.

`Unpack.to(..., fill=value)` accepts arbitrary fill; proofs implement zero only.
Test 1, a negative finite value, and an explicitly chosen max-reduction neutral
value/policy. Test N=129,255 into A256 and N=129,257,1023 into larger fragments,
including an entirely padded remaining block.

### Pack

The existing scatter test is `movement/packer/test_scatter.py`. It packs four
logical 128-element blocks from FP32 Dst to BF16 output, with slot sequences
`(0,s,2s,3s)` for s=1,2,4,8,16,21. It compares drained/queued counter updates,
fixed output addresses, and four read interfaces. This is meaningful existing
evidence for low overhead when switching nonconsecutive Dst sources.

Missing dimensions: BF16 Dst (one physical allocation unit); FP32 output;
irregular/reversed orders such as `(63,0,17,4)`; more than four segments;
the BF16 allocation edge 127; and an exact partial final segment.
The current fixed output address is L1 scratch subsequently copied to DRAM,
not a wrapping producer/consumer CB integrated with math.

The model can express scatter by packing different fragments/views into
different views of one Buffer. It has no explicit gathered-fragment operation,
and one fragment is allocated contiguously. Test that a lowering can combine
these model operations into one output stream without premature page publication
or excessive per-segment setup. A gather API is optional, not required for
expressibility.

## Composition gaps that primitive passes cannot resolve

### Hidden LReg, predicate, engine and configuration effects

The current IR does not describe the resources required by several raw recipes:

| Recipe | Actual effects in current PoC |
|---|---|
| Refined exp/reciprocal (`sfpu_math/emit.py`) | Writable temporary LRegs; math tests operate on L0 and provide scratch L3–L6 |
| Arbitrary fixed predicate (`sfpu_movement/emitters.py`) | Clobbers L6/L7 by default; resets previous condition state before rebuilding it |
| Store from L12–L15 | Copies through writable scratch, default L5 |
| Source-preserving exact Dst unpack (`transport/dst.py`) | Executes on TRISC1; clobbers L0/L7, predicate, math counters, FP32 configuration |
| FPU recipes | Change address/fidelity modifiers, Replay and MOP configuration |

But `model.py` exposes all L0–L7 to the author; special functions only record
their destination, predicate records no register effects, and unpack is always
recorded as TRISC0. Reusing these recipes unchanged cannot support arbitrary
compositions. The alternate direct-Dst unpack path also has a documented SrcA
clobber; the exact insertion PoC was written specifically to preserve sources.

Choose a contract before lowering: reserve scratch explicitly, allocate/spill
temporaries with liveness, save/restore affected state, or reject excess pressure.
Add live sentinels in every non-output LReg across exp, reciprocal, predicate,
special-register store, and Dst unpack. Include special functions targeting L3–L7,
masked operations followed by all-lane stores, FPU→SFPU→FPU, and pack→Dst reuse.

The model permits BF16 and FP32 Dst to coexist. Existing FPU fixtures switch
formats globally between test modes, while SFPU helpers assume FP32 addressing.
Require an explicit mixed-format preservation/addressing proof or constrain
mixed-format programs until a valid schedule is established.

### Full programs, tails and backpressure

`examples/swiglu.py` is recording-only. Its sequence is an excellent first
integration target: input→unpack→move→exp→add→reciprocal→multiply→pack→output.
Test sizes 1,37,127,128,129,1023,1024,1025,4096+37, distinct inputs per page,
nonzero offsets and neighboring external-output sentinels.

Runtime `Transfer` currently rejects sizes not divisible by 128 and requires
32-byte-aligned offsets/strides. Therefore local exact-prefix tests do not prove
the model's arbitrary external tails. Also, the example uses `stride` to advance
between loop pages; the raw adapter's stride advances between 128-element blocks
inside one transfer. These need an explicit translation and separate tests.

Use small CB depths with wraparound and delayed producers/consumers to exercise
ownership. Existing CB/NoC and semaphore tests are useful evidence, but no test
joins the model's complete five-engine pipeline. Blocking source-free remains
an explicitly documented unresolved PoC gap; uncontended cycles and delayed
source-valid tests do not close it.

### Numerical semantics

Basic FPU coverage deliberately uses controlled inputs to distinguish addressing
from fidelity loss. BF16 Dst tests use exact integer controls and one operation;
they do not prove repeated rounding behavior. HiFi2 input families constrain B's
mantissa. Add general signed BF16 mantissas, cancellation, repeated BF16
accumulation, and a documented expected-precision oracle.

The model records output as read by add/sub/mul/matrix/pool operations, suggesting
accumulation; raw add/sub tests support both accumulate and overwrite, but the
model has no selection parameter. Define that contract, the full-tile MVMUL
layout/expansion, GAPOOL fidelity, and pool inactive-row behavior explicitly.
Already-tested pool footprints should remain regression requirements, not trigger
smaller allocations.

Exp and reciprocal have useful bounded-domain proofs, but no model-level
accuracy/domain policy. Exception tests only log results and check guards.
MAD's repeated test allows one ULP per call on a noncancelling chain; that is not
general IEEE FMA equivalence. Add assertions for chosen exception semantics and
heterogeneous chains, especially SwiGLU with large positive/negative inputs.

## Useful operations absent from the model

These are API opportunities, not requirements to expose every device opcode.

| Priority | Addition | Why / existing evidence |
|---|---|---|
| First | Bit shifts, AND/OR/XOR, integer add, raw bit immediates, conversion versus reinterpretation | Q6 tests already compose these instructions; no corresponding register API. Needed for quantization/index/mask work. |
| First | Lane rotate, zero-fill lane shift, register transpose | Mean tests already use SFPSHFT2 mode 3 and SFPTRANSP. Add isolated lane-tag and masked/alias tests; scalar sums can hide permutations. |
| First | Register comparisons and select, optional scoped predicates | Current predicate only accepts a static host mask. Needed for data-dependent selection, clamps, stable special functions and masked reductions. |
| Next | Min/max and indexed min/max | SFPSWAP supports these; no instruction use under tests found. Useful for max reductions, softmax and argmax. Define tie/NaN/signed-zero/index behavior. |
| Next | rsqrt; optionally sqrt/log | RMSNorm needs rsqrt; choose numerical contract and approximation/refinement before exposing it. |
| Next | Explicit pack rounding and activation options | Existing tests prove deterministic/stochastic BF16 conversion and packer ReLU/clamp, but Pack.to exposes none of them. |
| Optional | TF32 source representation and additional fidelity modes | Mean tests already use TF32; current source model is BF16-only and Fidelity exposes LoFi/HiFi2. Keep conversion/error visible to authors. |
| Optional | Piecewise-linear SFPU LUT | Potential activation acceleration; not needed to complete the existing API. Requires fixed-register/scratch and numerical tests. |

Distinguish per-lane bit shifts from lane movement. Blackhole's basic lane rotate
is within each group of eight lanes, not a flat rotate across all 32. The official
[SFPSHFT2 specification](https://github.com/tenstorrent/tt-isa-documentation/blob/main/BlackholeA0/TensixTile/TensixCoprocessor/SFPSHFT2.md)
documents that distinction and multi-register modes.

The official [SFPSWAP specification](https://github.com/tenstorrent/tt-isa-documentation/blob/main/BlackholeA0/TensixTile/TensixCoprocessor/SFPSWAP.md)
describes min/max and associated index swapping, including nontrivial tie behavior.
The [SFPLUTFP32 specification](https://github.com/tenstorrent/tt-isa-documentation/blob/main/BlackholeA0/TensixTile/TensixCoprocessor/SFPLUTFP32.md)
documents piecewise-linear modes and a destination-selection bug in the FP16
three-entry mode. Prefer proving a selected useful mode over blanket exposure.

After primitive additions, prioritize these compositions: sum/max across all
four SFPU positions with tail masks; stable softmax; RMSNorm; argmax with indices;
SwiGLU; Q6 decode feeding FPU consumption. Sum/mean and Q6 already have raw
composition coverage, so extend those rather than treating them as absent.

## Suggested implementation order

1. Add regression tests for the two reproduced allocator problems and correct
   allocation/view constraints and loop lifetimes.
2. Define numerical, layout, scratch/clobber and mixed-format contracts; exercise
   live LRegs/predicates and BF16 SFPU transfers.
3. Add scattered-unpack publication/reuse tests and the missing scatter-pack
   dtype/order/tail/CB cases, retaining fixed 128-element allocation units.
4. Prove multi-block/shared-B/full-tile FPU expansion and external exact tails.
5. Execute the model's complete SwiGLU pipeline, then compare bounded generated
   valid model programs against an independent reference. Generate resource
   pressure, views, aliases, loop boundaries and operation transitions, not only
   Cartesian products of isolated opcodes. Check untouched resources as well as
   output; use contract-specific numerical tolerances.
6. Add shifts/rotates/transpose and compare/select first; follow with workload-
   driven reductions, rsqrt, argmax and optional pack/LUT optimizations.

No production code or executable tests were changed by this audit.
