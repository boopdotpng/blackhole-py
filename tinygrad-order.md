Your model is mostly right: use PMs to make the DAG TT-shaped before linearization. The current renderer is only non-ISA because it was deliberately added as a diagnostic placeholder.

## Why it is not an `ISARenderer` yet

`TensixRenderer` currently only implements:

```python
render(linear_uops) -> diagnostic text
compiler.compile(text) -> empty TTPR
```

Meanwhile, `renderer/isa/tensix.py` already contains:

- RV32 and Tensix opcode enums;
- RV32 GPR definitions;
- SFPU LReg definitions;
- instruction encoders.

What is missing is the actual ISA pipeline connecting generic UOps to those encoders.

## Full ISA renderer split

```text
rewrite_to_sink
  │ graph-level architecture and resource transformations
  ↓
extra_matcher
  │ final semantic legalization during generic lowering
  ↓
pre_isel_matcher
  │ graph rewrite immediately before instruction selection
  ↓
isel_matcher
  │ generic UOps → Ops.INS with virtual registers
  ↓
linearize
  ↓
pre_regalloc_matcher
  │ line transformations that must happen before allocation
  ↓
generic register allocation
  ↓
post_regalloc_matcher
  │ loops, fixed-register copies, hazards, latency NOPs
  ↓
render/asm
  │ encoding, branch fixups, TTPR packaging
```

### `rewrite_to_sink`

This is where TT should eventually handle:

- splitting dense accesses into pages;
- CB allocation;
- SrcA/SrcB/Dst ownership;
- stream assignment;
- synchronization;
- SFPU vectorization;
- FPU block recognition.

It runs while we still have a DAG.

### `pre_isel_matcher`

Small architecture legalization immediately before selection:

- normalize immediates;
- prepare parameter registers;
- turn TT pseudo-operations into forms accepted by instruction selection;
- expose fixed hardware operands.

It should not perform whole-kernel scheduling.

### `isel_matcher`

Maps individual operations to instructions:

```text
ADD int32    → RV32Ops.ADD
LOAD int32   → RV32Ops.LW
SFPU add     → TensixOps.SFPADD
MVMUL        → TensixOps.MVMUL
STALLWAIT    → TensixOps.STALLWAIT
```

This is also where virtual registers are assigned:

```python
ctx.vreg(WGPR)
ctx.vreg(LREG)
```

The result is still a DAG, now made mostly of `Ops.INS`.

### `pre_regalloc_matcher`

Likely small for TT initially:

- fixed-register constraints;
- rematerialization if required;
- resource clobber annotations;
- possibly no rules initially.

### `post_regalloc_matcher`

Handles things that depend on physical register assignment or final ordering:

- `RANGE`/`END` into RV32 labels, increments and branches;
- copies when operands were not coalesced;
- SFPU producer/consumer latency NOPs;
- fixed-register setup;
- branch expansion/fixups where appropriate.

## Yes, rewrite before linearization

For a generic elementwise loop:

```text
RANGE i
  LOAD A[i]
  LOAD B[i]
  ADD
  STORE C[i]
END
```

TT graph rewriting should eventually produce something closer to:

```text
RANGE page
  NOC_READ A → CB0
  NOC_READ B → CB1
  WAIT/PUSH
  UNPACK CB0/CB1 → Dst
  SFPLOAD Dst → virtual LReg A
  SFPLOAD Dst → virtual LReg B
  SFPADD A, B → virtual LReg C
  SFPSTORE C → Dst
  PACK Dst → CB31
  NOC_WRITE CB31 → C
END
```

Instruction selection then turns each of these into concrete `Ops.INS`, and the linearizer only decides the order allowed by dependencies.

Trying to construct this after receiving the linear list would be much harder.

## Which hardware resources should use generic regalloc?

A hybrid model is appropriate.

| Resource | Generic register allocation? | Reason |
|---|---|---|
| RV32 GPRs | Yes | Ordinary scalar registers |
| SFPU L0–L7 | Yes | Real interchangeable value registers |
| L1 | No | Memory allocator/addressing concern |
| Circular buffers | No | Stateful producer/consumer queues |
| SrcA/SrcB | No | Pipeline banks with validity and ownership |
| Dst rows | Probably no | Indexed matrix/SFPU resource with pack ownership |
| Semaphores | No | Finite synchronization resources |

SrcA, SrcB and Dst are not normal registers. They have state transitions such as:

```text
unpack owns SrcA/SrcB
→ valid
→ math consumes
→ clear
```

Generic register allocation does not model that.

SFPU LRegs are much closer to normal registers:

```text
virtual 32-lane value
  → choose L0...L7
  → spill if register pressure exceeds 8
```

## The float4 approach

Using generic `float4` memory coalescing is not enough.

`supports_float4` currently groups adjacent scalar memory operations into vectors of:

```text
float2 / float4
```

An SFPU LReg contains:

```text
32 lanes × 32 bits = 128 bytes
```

Eight independent float4 values do not naturally become one LReg because generic regalloc does not perform subregister/lane packing.

The better representation is:

```python
dtypes.float.vec(32)
```

mapped to:

```python
Register("l0", ..., size=128)
```

Then one vector ADD can become one `SFPADD`.

However, generic lowering currently scalarizes elementwise vectors before memory coalescing. We will need a TT vectorization rewrite that groups a dense loop into 32-lane operations. The float4 flag does not provide that.

## Can generic regalloc handle 128-byte LRegs?

Mostly, yes. The existing register abstraction already permits:

```python
LREG = Register(..., size=128)
```

and constraints can select only L0–L7.

But the generic spill code contains x86 assumptions. In particular, spill-slot sizing special-cases 16-byte XMM registers and otherwise relies on the UOp dtype size. We would need to generalize it to respect `Register.size`.

More importantly, an SFPU LReg cannot necessarily spill directly to arbitrary L1:

```text
LReg → SFPSTORE → Dst
Dst → pack/unpack if moving through L1
```

The practical first spill path is likely:

```text
LReg → reserved Dst spill rows
reserved Dst rows → LReg
```

That requires Dst allocation from TT codegen. It is not a normal stack-pointer spill.

Therefore:

- use generic allocation for L0–L7;
- initially reject LReg spills;
- keep first kernels under eight simultaneously live LRegs;
- later let TT codegen reserve Dst spill slots and teach `spill()`/`fill()` to use them.

## What we need to write next

Convert `TensixRenderer` to `ISARenderer` with a deliberately small contract:

1. **RV32 instruction selection**
   - constants, parameters;
   - integer arithmetic;
   - indexes/address calculations;
   - branches and loops;
   - L1 loads/stores.

2. **Regalloc methods**
   - `stack_pointer()`;
   - `copy()`;
   - GPR `spill()` and `fill()`;
   - reject LReg spilling initially.

3. **Control-flow lowering**
   - `RANGE` and `END`;
   - labels and RV32 branches;
   - branch displacement fixups.

4. **Encoding**
   - use existing `encodings`;
   - byte-compare against bootstrap `support/tt/asm.py`;
   - package the generated role image into TTPR.

5. **One SFPU register class**
   - `float32x32 → LREG`;
   - `SFPLOAD`, `SFPADD`, `SFPMUL`, `SFPSTORE`;
   - post-regalloc latency NOP insertion.

For the first step, generate only one stream and keep the other four as return-only images. That avoids solving five-stream register allocation immediately.

## Recommended boundary

```text
Generic tinygrad:
  fusion
  ranges
  symbolic/index simplification
  scalar semantic operations

TT codegen:
  group 32 iterations
  L1/CB staging
  Src/Dst allocation
  stream and synchronization graph

Generic ISARenderer machinery:
  RV32 and LReg virtual registers
  instruction selection
  linearization
  per-stream register allocation
  encoding
```

So the answer is hybrid: use tinygrad’s generic regalloc for true registers, but keep L1, CBs, SrcA/SrcB, Dst and stream scheduling as TT codegen properties. That is much more practical than pretending every Tensix resource is a 128-byte register.