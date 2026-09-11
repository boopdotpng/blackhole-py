I used `[?]` where the handwriting, glare, or eraser made a word uncertain.

## tinygrad porting path — layers / tinygrad abstractions

### PCIe / raw transport — `support/tt/pcie.py`

* ioctls

  * set power state
  * pin pages / free (`lgbSysmem`?)
  * alloc / config / free TLBs
* use tiny mmap and ioctls from AMD
* ✓ easy

### Device init / boot — not sure, maybe ↑

Through `ttlib` [?]:

* harvesting / card info

  * DRAM bank + core count
* boot core FW
* boot CQ kernels (`M4,2`, `M4,3`, `M4,4`?)

  * PCIe / DIS / DRAM
* init sysmem
* ↓ simple

### HCQ / HCQ2 implementation

`HCQ2 in progress`

* copy tinygrad copy / wait / signal queue

  * must check in RISC-V
* write CQ FW in uops? See AMD PM4
* repurpose global / locals for core count

  * `(Ops.Special?)` — Program
* see tiny meeting 7/27: tensor programs?

---

## Allocator — `device.py` subclass

Main issue: minimum compute unit and tilization → padding

* FPU `elwmul` + `mvmul` rely on tilized tensors

  * `(8×16 · 16×16 → 16×16) mvmul`
* unpack + pack with row-major tensors

  * possible
  * ~20% more cycles, 1.5× slowdown

Solution: TPU-like problem — should hide from tinygrad

* weights tilized on copy-in, un-tilized on copy-out
* device activations are always tilized
* need to store tilized true / false somewhere

  * no tinygrad primitive
* read TensorFlow / IEEE / MLIR + XLA/HLO
* tensors need padding to 32×32 on the last two axes

  * so that tilizing is valid
  * may be reducible
* tiny inserts mask / where; inefficient

### Allocator, continued

Needs to store — not in tiny at present:

* lowest tensor size per compute op
* padded versus real dimensions
* tilized?
* base address

  * later `Ops.INDEX` stuff
* pass into HCQ / lower-write op
* optional interleaving

  * probably not necessary

Lowering assumes:

* these layouts and padding are hidden from tinygrad
* see PM shrink / pad / contiguous hack

  * not nice!

---

## `isa/tensix.py`, like x86 lowering / representation pieces

* RV32 ops

  * base RV32IM + multiply + immediate
  * no `ecall` / break
  * limited CSRs, two codes hardcoded
* no group ops like x86
* no register diff + complicated lowering
* pattern redesign
* SFPU

  * registers modeled as `L0–L7` RV registers
  * 128-byte
  * `[r8–r15?]` read-only / constants
* tinygrad handles spill

  * destination or L1 internal `(B)`
* PatternMatchers here:

  * `UPat → Ops.INS`
  * post-regalloc instruction-selection matcher → extra matcher
  * and some other ops
  * → `TensixRenderer (ISARenderer)`
* lowering to RV bytes happens here

  * needs modification to support five kernels
  * graph must lower all at once, then split
  * data analysis on dependencies across kernels / syncs / semaphores
* need PM to do register / NOP / dependency tracing for SFPU

  * configure spill
* fixup modification versus x86

  * long jumps
  * also no function calls

---

## Special lowering path: `tt-rewrite-to-sink`

* tiny renderer gets unrecoverable ops for TT; move higher
* hook pre-`rangeify`

  * reduce axis, etc. is visible
* own a new chain of PatternMatchers from there
* add to tiny core, not modify
* this partially unlowered form goes into our renderer

Questions / research tasks:

* find a good boundary; keep most tiny PMs
* adopt Metal maximum 32 inputs + outputs PM
* new kernel-fusion boundary

  * study current tinygrad
  * many `callify`s? → program boundary
* tensor core `[PAOTO?]`

  * reuse AMD dimensions
  * `8×16 · 16×16 → 16×16`
  * min dimensions / accumulator [?]

---

# Codegen — new TT kernel and dependency graph

## QKV-fused flash attention

### Outside the loop

* `QLo, QHi = [1/2?] tile(query-[1/2?])`
* zero-mask tile
* `O0 = dst(0)`
* `O1 = dst(1)`
* `M = dst(-inf)`
* `L = dst(0)`

For block `0 .. Kv-blocks - 1`

---

## Phase 1 — scores

Key cache:

* `2b`, `2b+1`
* BRISC NoC 0 read
* key CB
* two-CB depth

Flow:

```text
KLo + QLo0
      │
    MVMUL ──ACC──→ MVMUL
                    │
KHi + QHi0          │
                    │  unpack + FPU
                    │
              S = Q·Kᵀ + dst0
```

Then:

* zero / mask
* if `B = N - 1`
* `FWADD`
* accumulator
* unpack / FPU

---

## Phase 2 — online softmax

Inputs:

* `M`
* `L`
* `O0`
* `O1`

Operation:

```text
online softmax
scale · max · exp · sum
```

Outputs:

* `M′ → dst 3`
* `L′ → dst 4`
* SFPU
* `O0 · α → dst 1`
* `O1 · α → dst 0`

Below block: `P + O′s + O` [?]

---

## Phase 3

* spill `dst0 → L1`
* `P0` read twice
* pack → L1 → unpack

Value cache:

* `2b`, `2b+1`
* BRISC NoC 0
* value CB, depth 2

Flow:

```text
VLo → MVMUL ACC → O0 / dst1
VHi → MVMUL ACC → O1 / dst2
```

* unpack + FPU
* carry to next block

After loop:

* `O0`, `O1`, `L`
* normalize:

  * `O × (1/L)`
  * SFPU
* store `(try-CB L2?)`
* Pack
* scatter-write

  * interconnect + DRAM
* NCRISC NoC 1

---

# Explicit sync / wait points

* NoC read and write verification
* CB reserve, pop, push, and page/tile counters
* unpack / pack done (`TTSEM`)
* `srcA` / `srcB` clear / valid
* destination valid / ready
* SFPU register-load cycle dependency
* unpack-to-destination requires stalls
* eight `[HSEM?]` semaphores

  * research needed
* destination ownership switching

  * math or pack
* add more

### New TT kernel

* `(tinygrad codegen)`
