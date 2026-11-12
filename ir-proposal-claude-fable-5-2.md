# tix: one sequential program per kernel, projected onto five cores

This is a paper design. Nothing was compiled or run; I checked it by rewriting your old kernels in it. `tix` is a placeholder name.

## The idea

Your old kernels write every loop up to five times. In `projection`, the row loop appears separately on BRISC, TRISC0, TRISC1, TRISC2 and NCRISC. In `attention`, all five cores recompute `split_count` separately.

The IR removes that duplication. A kernel is one sequential program that every core in the grid runs. Each statement kind has a home RISC core. The compiler projects the program onto the five cores: each core keeps the control flow and its own statements. Data crossing between cores is always a named slot of declared storage, and all synchronization is derived from where a slot is written and last read.

The hardware's speed mechanisms are not hidden behind an optimizer. MOP is a two-level loop, replay is a recorded straight-line body, a load-macro is a fused vector chain, and address counters are the induction variables of affine views. You request each with an attribute on a loop, and the compile fails with a reason if the loop does not fit.

## The language

Line-oriented text: `[name =] op operands key=value @attr`, blocks in `{ }`. There are six concepts.

**1. Scalars.** `u32`/`i32` expressions using tinygrad's ALU op names, over `core`, `core.x`, `core.y`, launch `arg`s, loop variables and `let`s. These replace all RISC-V address math. Names are assignable, like C variables.

**2. Regions.** Declared storage with a format, a shape, an optional layout and a depth:

| Declaration     | What it is                                                                               |
| --------------- | ---------------------------------------------------------------------------------------- |
| `dram` / `host` | Launch-bound tensor, indexed logically; the compiler does page, bank and coordinate math |
| `l1`            | L1 memory; `depth 1` is resident, `depth n` is a ring                                    |
| `srca` / `srcb` | The source registers, as a depth-2 ring over their two banks                             |
| `dst`           | A partition of Dst; its format selects 16- or 32-bit mode                                |

**3. Slots and views.** Writing to a region name takes its next slot and names it: `w = copy wr <- ...`. `s = slot R` takes one to fill piecewise. Views are affine: `s[a +: n]` means n elements from a (rows for Src/Dst), `d.vec(j)` is the j-th 32-lane vector, and `r.at(x, y)` or `r.at(rect)` is the same region on other cores.

**4. Statements.** Each is one hardware action:

| Statement                                           | Moves                                          | Default core               |
| --------------------------------------------------- | ---------------------------------------------- | -------------------------- |
| `copy`                                              | DRAM, host, remote L1, multicast, atomics ↔ L1 | BRISC reads, NCRISC writes |
| `unpack`                                            | L1 → SrcA / SrcB / Dst                         | TRISC0                     |
| matrix ops (`mvmul`, `elwmul`, `mova2d`, `zero`, …) | Src → Dst, one instruction each                | TRISC1                     |
| vector ops (`load`, `store`, `mad`, `swap`, …)      | Dst ↔ lanes, one instruction each              | TRISC1                     |
| `pack`                                              | Dst → L1                                       | TRISC2                     |
| `ld` / `st` / `wait`                                | L1 words ↔ scalars                             | BRISC                      |

**5. Control.** `loop i < n`, `if`, `where` (lane predication scope) and `fn`.

**6. Attributes.**
- Placement: `@brisc`, `@ncrisc`, `@t0`, `@t1`, `@t2`.
- Mechanism: `@mop`, `@replay`, `@macro`, `@unroll`.
- Modes: `ph=`, `transpose`, `round=`, `noc=`, `vc=`, `posted`, and so on.

### Semantics

1. **Program order is the meaning.** The result equals running the text top to bottom, with each effect finished before the next statement. A numpy reference interpreter follows directly from this.
2. **Projection.** Loops and ifs are copied to every core that has statements inside them. Pure scalars are recomputed wherever they are needed. A scalar obtained by `ld` belongs to the core that loaded it; using it on another core is a compile error unless it goes through an L1 word.
3. **Handoff.** A statement reading a slot waits until every earlier write to it has completed. Taking a slot from a full ring waits until the oldest is freed, which happens at its last use. CB counters, valid bits, semaphores, STALLWAIT, NoC transaction IDs and acks all follow from this rule.
4. **Modes, not registers.** An op states the mode it runs in. The compiler writes the registers, hoists each write to the outermost point where it is invariant, and inserts the drains.
5. **Mechanism attributes are demands.** With no attribute, a loop is a RISC-V loop issuing one instruction per iteration. `@mop` demands the MOP expander, `@replay` the replay buffer, `@macro` a load-macro. Replay slots (32 per thread), address-modifier slots (8) and macro templates (4) are allocated like registers; running out is an error.
6. **Header is the manifest.** `grid`, `dram`/`host`, `arg` and per-core `let`s become your `cores`, `uploads`, `uniform` and `per_core` entries.

## Real kernels

Library calls such as `rsqrt`, `hsum`, `matmul32` and `softmax_step` are Python DSL functions that expand to primitive ops. The IR text would contain the expansion.

**Embedding** (about 25 lines of emitter code in `kernels.py`):

```
kernel embedding
grid  1
dram  hist  u32[8192]
dram  table bf16[128256, 2048]
dram  x     bf16[2048]
arg   pos   u32
l1    ids   u32[1024]
l1    row   bf16[2048]

i   = copy ids <- hist[pos & ~1023 +: 1024]
tok = ld i[pos & 1023]
r   = copy row <- table[tok]
copy x <- r
```

**qkv: RMSNorm then one dot product per weight row** (1B shapes, Q only):

```
kernel qkv
grid  88
dram  x     bf16[2048]
dram  gamma bf16[2048]
dram  wq    bf16[2048, 2048]
dram  q     bf16[88, 1024]
let   rows = 23 + (core < 24)
let   row0 = 23*core + min(core, 24)

l1    xg   bf16[4096]
l1    xn   bf16[2048]
l1    wr   bf16[2048] depth 2            # one weight row, double buffered
l1    dot  bf16[16]   depth 2
l1    out  bf16[32, 32] faces
srca  A    bf16
srcb  B    bf16
dst   N    fp32[4096]
dst   P    fp32[1024]

g = slot xg
copy g[0 +: 2048]    <- x
copy g[2048 +: 2048] <- gamma            # both reads issue back to back; one wait at first use
n = slot N
loop t < 4 {
  a = unpack A <- g[1024*t +: 1024]
  loop h < 8 @mop { mova2d n[64*t + 8*h +: 8] <- a[8*h +: 8] }
}
ss = splat 0.0
loop j < 64 @replay {                    # sum of squares, 32 lanes at a time
  v  = load n.vec(j)
  ss = mad v, v, ss
}
k = rsqrt(hsum(ss) * (1/2048) + 1e-5)
loop j < 64 @macro {                     # x * k * gamma, fused load-multiply-store
  v = load n.vec(j)
  w = load n.vec(64 + j)
  v = mul v, k
  v = mul v, w
  store n.vec(j) <- v
}
xs = pack xn <- n[0 +: 128]

o = slot out
loop r < rows {
  w   = copy wr <- wq[row0 + r]
  p   = slot P
  acc = splat 0.0
  loop t < 2 {
    a = unpack A <- w[1024*t +: 1024]
    b = unpack B <- xs[1024*t +: 1024]
    loop f < 4 @unroll {
      zero p[16*f +: 16]
      loop ph < 2 @mop { loop h < 2 {    # two fidelity phases x two half-faces
        elwmul p[16*f + 8*h +: 8] += a[16*f + 8*h +: 8] * b[16*f + 8*h +: 8]  ph=ph
      }}
    }
    loop j < 32 @replay {
      v   = load p.vec(j)
      acc = add acc, v
    }
  }
  store p.vec(0) <- hsum(acc)
  d = pack dot <- p[0 +: 1]
  st o[0, r] <- ld d[0]   @ncrisc        # logical index; `faces` layout does the bit math
}
copy q[core] <- o
```

The second half replaces steps 3 to 7 of `_projection_program` plus `_projection_read_weights`, `_read_pages_body`, `_projection_dot_math` and `_dot_row`. The mechanism choices of the original survive as attributes: the multiply is a MOP, and the vector accumulate is a replay so the two do not fight over TRISC1's single MOP template.

**Attention, the block loop:**

```
let parts = live_partitions(nblk_all)    # written once; the old kernel computes it on all five cores
loop i < nblk {
  let blk = phase + i*parts
  k = copy kq <- kc[head, blk]           # two tiles each, one tracked batch
  v = copy vq <- vc[head, blk]
  s = slot S
  loop f < 2 {                           # scores = Q K^T
    qb = unpack B <- qh[1024*f +: 1024]
    ka = unpack A <- k[1024*f +: 1024]  transpose
    matmul32(s, qb, ka, phases=2, zero=(f == 0))
  }
  if blk == pos >> 5 { mask_tail(s, (pos & 31) + 1) }   # a `where` block against lane ids
  softmax_step(s, O, m, l, 0.125)
  pr = pack pq <- s
  loop f < 2 {                           # O += P V
    pb = unpack B <- pr
    va = unpack A <- v[1024*f +: 1024]
    matmul32(O[64*f +: 64], pb, va, phases=2)
  }
}
```

`matmul32` is this nest. The compiler derives the sixteen address-modifier steps that `Fpu.matmul` lists by hand as `(0,1,0,2,0,1,0,4,…,5)`:

```
loop ph < 2 @mop { loop m < 2 @replay { loop n < 2 { loop kf < 2 { loop h < 2 {
  mvmul d[32*m + 16*n + 8*h +: 8] += b[32*m + 16*kf + 8*h +: 8] * a[32*kf + 16*n +: 16]  ph=ph
}}}}}
```

**Argmax, the collective tail:**

```
m = slot mine
st m[0] <- bk
st m[1] <- bi
st m[2] <- 1
copy inbox.at(0)[core] <- m              # unicast into core 0's L1
if core == 0 {
  loop c < 88 {
    wait inbox[c, 2] != 0                # explicit: the handoff rule cannot see remote writers
    ...
  }
  copy tok[wpos] <- m                    # host memory over PCIe
  copy params.at(all) <- nxt             # multicast
}
```

## Against the nine goals

| Goal                       | How                                                                              |
| -------------------------- | -------------------------------------------------------------------------------- |
| 1. No config registers     | Modes are attributes; rule 4                                                     |
| 2. No long RISC-V          | Scalars, logical tensor indices and layouts are native expressions               |
| 3. No NoC bookkeeping      | `copy` is tracked by rule 3; waits happen at first use, so batching is automatic |
| 4. Everything programmable | See below                                                                        |
| 5. One program             | Projection; loops written once                                                   |
| 6. No escape hatch         | No raw-word statement exists                                                     |
| 7. Fast by hand            | Mechanism attributes plus a Python library                                       |
| 8. tinygrad emits it       | See below                                                                        |
| 9. Few concepts            | Six; one op set, no second IR                                                    |

**Goals 4 and 6.** Completeness is a finite checklist. Your `kview/data/isa.json` has 137 encoders, and each must be either an op or derived from a named construct:

- **Ops, one to one:** matrix, vector and scalar-unit data instructions, and the atomics.
- **`unpack` / `pack` modes:** UNPACR, PACR.
- **Derived from views:** SETRWC, INCRWC and the ADC family.
- **Derived from loop attributes:** MOP, MOP_CFG, REPLAY, SFPLOADMACRO.
- **Derived from `where`:** the SFPU condition-stack instructions.
- **Derived from slots:** STALLWAIT, the semaphore instructions, CLEARDVALID.
- **Derived from modes:** WRCFG, SETC16, RMWCIB, SFPCONFIG.

The 444 fields in `tensix_regs.json` each need an owning attribute. That table is the acceptance test for the spec.

**Goal 8.** I read your local tinygrad checkout (HEAD `8dca0c66b`). A renderer there receives linearized UOps: `PARAM`, `RANGE`/`END`, `IF`, `INDEX`/`LOAD`/`STORE`, register-buffer accumulators and `SPECIAL` global ids. These map directly:

- `PARAM` becomes `dram` or `arg`.
- `SPECIAL gidx` becomes `core`, with `global_max` set to the grid.
- `RANGE` becomes `loop`.
- Register buffers become assignable names.
- Float ALU ops become vector ops; integer ALU ops become scalars.

The renderer has three forms, all in the same IR:

1. **Scalar.** Copy a window into L1, then `ld`/`st` with the RISC-V core's own float ops. It covers every kernel and is slow. The one piece of machinery is choosing the loop level for the copy, using the `vmin`/`vmax` intervals tinygrad already tracks.
2. **Lane.** When the innermost range is stride 1, emit `copy`, `unpack`, `load … store`, `pack`.
3. **Contraction.** Declare a `TensorCore` so the optimizer emits `WMMA`, and render it as the `matmul32` nest.

Whole-buffer copies never reach `render()` in this checkout; they stay with the Allocator, which maps onto your existing `OP_COPY` queue.

## Where it strains

- **The address-modifier solver.** Turning affine views into at most eight modifier slots with carry and clear is the one real analysis hidden behind "derived". When it fails under `@mop`, you restructure the loop by feel. The alternative is explicit cursors; I rejected it because tinygrad emits index expressions and stale counters are a common bug in hand kernels. This is the decision I am least sure of.
- **Derived sync is conservative.** Hand kernels place each stall knowing which engine touched which rows. The handoff rule waits on whole slots. The compiler needs a listing of everything it derived (MOP words, replay slots, modifier table, hoisted writes, waits), or "nothing hidden" is not true in practice.
- **Remote rings.** A multicast into other cores' ring slots needs credit return from N receivers. The compiler picks one protocol; the only way to choose another is `wait` and atomics by hand.
- **Vector scheduling.** Lane-register allocation has pre-coloured ops (`transp`, LUT, index capture) and only eight registers with no spill. `_rms_apply_weight_pair` interleaves two chains by hand to hide the two-cycle multiply; here you write both chains and trust the scheduler. Runtime-patched instruction words, as in `_load_scale`, become `splat <scalar>`.
- **The config long tail.** The kernels use perhaps 40 of the 444 fields. The rest are reachable only as named modes, which is close to naming registers.
- **Code size.** TRISC slots are 4 KB. `@unroll` and DSL inlining will overflow them; `fn` and per-core byte reports are required.
- **tinygrad's shape.** Its kernels are element-indexed and the device is tile-streamed. Reductions across lanes, non-unit strides and face layout all push the renderer back to the scalar form. Fusion is decided by tinygrad's scheduler: its rmsnorm is two kernels with a DRAM round trip, where yours fuses into qkv. Your archived report concluded the renderer is "almost certainly too late"; forms 2 and 3 answer that for map, reduce and matmul, but not for fused attention.
- **Not covered.** Ethernet and multi-chip, TRISC2's RISC-V vector registers, profiling timestamps inside a kernel, and L1 state persisting across launches (your manifest has `persistent`; the IR needs a matching attribute).

## Reading list

Citations are from memory and not link-checked.

**One program, many endpoints**
- Montesi, *Introduction to Choreographies* (2023). Endpoint projection is the per-core split here; "knowledge of choice" is the cross-core scalar rule.
- Shen, Kashiwa, Kuper, "HasChor" (ICFP 2023). A choreography library in a few hundred lines; a model for the Python DSL.
- Kahn, "The semantics of a simple language for parallel programming" (1974). Why derived synchronization cannot change results.
- Lee and Messerschmitt, "Synchronous Data Flow" (1987). Static rates give buffer bounds; this is the theory behind checking ring depths.

**Tiled machines**
- Gordon et al., "A Stream Compiler for Communication-Exposed Architectures" (ASPLOS 2002). StreamIt onto MIT Raw; the closest prior art to one program on a tile grid.
- Lee et al., "Space-Time Scheduling of Instruction-Level Parallelism on a Raw Machine" (ASPLOS 1998). What happens when the compiler owns placement and routing.
- Cerebras SDK, CSL documentation. The opposite choice: per-tile tasks and hand-routed fabric colours.
- occam 2 reference manual. `PAR`, `SEQ` and channels for transputers; small and complete.

**Accelerators with configuration state and loop engines**
- Ikarashi et al., "Exocompilation for Productive Programming of Hardware Accelerators" (PLDI 2022). Models configuration registers as first-class state and schedules as checked rewrites; the nearest thing to goals 1 and 7.
- Moreau et al., "VTA: An Open Hardware-Software Stack for Deep Learning" (2018). Its GEMM instruction is a two-level loop over a micro-op buffer with affine index factors, which is MOP plus address modifiers under another name.
- Koeplinger et al., "Spatial" (PLDI 2018). Explicit DRAM, SRAM, FIFO and register memories with transfers between them as statements.
- Ragan-Kelley et al., "Halide" (PLDI 2013). The algorithm/schedule split; here the schedule is inline and must hold.
- Tillet, Kung, Cox, "Triton" (2019). A tile-level IR between a tensor framework and a device.

**Tracking, ownership, predication**
- Bauer et al., "Legion" (SC 2012). State what a task touches; the runtime derives ordering and copies.
- Fatahalian et al., "Sequoia: Programming the Memory Hierarchy" (SC 2006). Memory levels and the copies between them as the program's structure.
- Nigam et al., "Predictable Accelerator Design with Time-Sensitive Affine Types" (Dahlia, PLDI 2020). Hardware resource conflicts as type errors, like the slot and replay budgets.
- Pharr and Mark, "ispc" (2012). SPMD with a mask stack; the precedent for `where` and for one program on all cores.

**Address counters**
- Liao et al., "Storage Assignment to Decrease Code Size" (PLDI 1995). Offset assignment for DSP auto-increment addressing; the literature for the modifier solver.

**Small text IRs**
- QBE IL reference. A complete IR specified in one page.
- Haas et al., "Bringing the Web up to Speed with WebAssembly" (PLDI 2017). Structured control and one-pass validation; a model for the verifier.
- Nigam et al., "A Compiler Infrastructure for Accelerator Generators" (Calyx, ASPLOS 2021). A small text IR mixing structure and control.

**Local**
- `tinygrad/renderer/llvmir.py` (310 lines) and `ptx.py` (232). Size and shape targets for the renderer.
- `tt-isa-documentation`: `MOPExpander.md`, `REPLAY.md`, `RWCs.md`, `SFPLOADMACRO.md`. Their functional models are the exact templates the loop attributes must match.
- `tt-llk` matmul and SFPU kernels. A corpus of hand-written modifier tables and MOP templates to test the solver against.
- `tt-lang`. I did not open it this session; as far as I know it is Tenstorrent's Python kernel DSL lowered through MLIR, so it is the direct contrast case for goal 9.