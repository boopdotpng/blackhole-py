# A text IR for Blackhole Tensix tiles

Status: design proposal. Grounded in `blackhole-py-old/examples/llama3/kernels.py`
(embedding, projection/qkv + RMSNorm, attention, argmax) and
`examples/matmul_peak_kernel`. Output target is what `blackhole-py` already
loads: five `.bin` images per program, plus `manifest.json`.

---

## 0. The idea in one paragraph

A kernel is **one SPMD program over a grid of tiles**, written as linear SSA text
with structured loops. **Each op's engine is determined by its opcode**: `copy`
runs on a data-movement RISC, `unpack.*` on TRISC0, `fpu.*`/`sfpu.*` on TRISC1,
and `pack` on TRISC2. Scalar code is replicated onto every core that needs it.
The compiler slices the program into five instruction streams. Every SSA value
that is defined on one engine and used on another is a **handoff edge**. The
compiler implements each edge with the right hardware protocol: CB pointers,
SrcA/SrcB valid bits, the Dst semaphore, or remote credits plus a multicast
semaphore. **Where a value lives** (an L1 pool with a depth, a Dst slot, or a
channel to other tiles) is the user's decision, and it is the main performance
lever. Configuration registers, address counters, MOP/replay, and NoC
transaction IDs are compiler state. They are derived from op attributes, never
written.

The rest of this document follows from that paragraph.

---

## 1. Why this shape (goal by goal)

**The key observation.** Read the old kernels and look at what is *not*
arithmetic. It falls into four piles:

| Pile | Examples in `kernels.py` | Goal |
|---|---|---|
| Config writes | `_configure_dst`, `_set_addr_mod`, `prepare_l1_pair_formats`, `configure_format=False`, `_rms_setup_apply_macro` (SFPCONFIG backdoor) | 1 |
| Address/setup sequences | `_read_pages_body` (bank walk + coordinate table), `_tile_offset`, `_dense_offset`, `physical_to_logical`, the argmax padding-run computation, patching `SFPLOADI` with `valid_columns` via `INSTRN_BUF_BASE` | 2 |
| Completion/handoff | `transaction()`, `_remote_pending`, `CB.reserve_back/push_back/wait_front/pop_front`, `sem_wait(MATH_PACK)`, `stall(SFPU, MATH)` | 3 |
| Per-core duplication | `load_head` and `split_count` called on 4 RISCs, `empty_exits` on all 5, `for _ in p.trisc0.range(n)` mirroring `p.trisc1.range(n)` | 5 |

All four piles are *derivable from the dataflow*. The `p.trisc0.range(rows)`
loop exists only because TRISC1 has the same loop. The `CB.wait_front` exists
only because NCRISC uses a value that TRISC2 produced. So the IR states the
dataflow once, and the compiler derives the four piles.

**Goal 1 (no config writes).** Every op carries the attributes that determine
its config: source/destination format, fidelity, transpose, broadcast, Dst
accumulate mode, and rounding. For each TRISC, the compiler runs a forward
"known config state" dataflow over the CFG. Where the required state differs
from the known state, it emits writes, and it hoists them out of loops. Mesa's
dirty-bit state tracker works the same way. The old code does this by hand with
`configure_format=False` and `prepare_matmul_formats`.

**Goal 2 (no long setup sequences).** Memory is *typed with a layout*
(DRAM-interleaved with a page size and bank set, L1 tiled with faces, or
row-major). Indexing is logical: `W.row[r].tile[k]`, `%c.elem[i]`,
`%q.tile[f].row[g]`. The compiler lowers indices to bank, NoC coordinate, page,
face, and byte offset. It turns affine loop indices into address-counter
increments.

**Goal 3 (copies are tracked).** `copy` returns a value. Using that value
means the copy is complete. The compiler assigns transaction IDs, groups
the copies in a loop iteration into one barrier, and places the barrier
immediately before the first cross-engine use of any of them.

**Goal 4 (program every part) plus goal 6 (no escape hatch).** There is a
checkable rule for completeness: **every Tensix and NoC instruction is either
an IR op or compiler-owned state.** The compiler owns these:

- config: `SETC16`, `WRCFG`, `RMWCIB*`, `SFPCONFIG`, the ADC/addr-mod setters
- address counters: `SETRWC`, `INCRWC`, `SETADC*`, `ADDRCRXY`
- sequencing: `MOP`, `REPLAY`, `SEMINIT/SEMPOST/SEMGET/SEMWAIT` *for edges*,
  `STALLWAIT`
- NIU command registers

Every other instruction maps one-to-one to an op, with attributes for its
modes. Anything the compiler infers can also be *pinned* by the user, in
the same text:

- `@dst(n)` fixes a Dst slot.
- `@brisc`/`@ncrisc` assigns a data-movement core.
- `@noc(i) @port(p)` selects a NoC and DRAM port.
- `repeat` requires a hardware loop.
- `@macro` requires an SFPU load-macro.
- Raw semaphores and `atomic` are ops, for protocols the compiler does not
  infer.

Pinning is how you program every part without a lower layer.

I'd argue the CB protocol is not "hardware abstracted away." The hardware is L1
plus semaphores plus valid bits. Circular buffers are a *software convention*
on top. The IR exposes the hardware parts directly: pools (L1 regions with a
depth), Dst slots, and `sem`. It only infers the convention.

**Goal 5 (one program).** The slicing rule is mechanical: engine by opcode,
scalars replicated by backward slice, and loops/ifs replicated onto every
engine with ops inside them. It is decoupled software pipelining (see the
reading list), and the hardware is already shaped for it.

**Goal 7 (fast with little effort).** Three performance knobs are first-class
and short to write:

1. Pool depth (double buffering).
2. Dst blocking (which values stay resident).
3. Loop structure (`repeat`, `unroll`).

Everything else that made the old kernels fast moved into the compiler: bank
rotation, MOP templates, replay, TID grouping, and format hoisting. Those are
compiler passes now, not per-kernel effort.

**Goal 8 (tinygrad).** The IR is a linear SSA list with `range`/`end`, like a
linearized tinygrad UOp list. tinygrad never sees five cores, CBs, or
semaphores. It emits `copy`, `unpack`, an FPU or SFPU op, `pack`, and `copy`,
and the compiler pipelines it (§6).

**Goal 9 (few concepts).** The whole IR has six concepts: *grid/params, memory
(global, pool, chan, sem), values (scalar, L1 tile, src, dst, vec), engine ops,
structured control, and functions*. The format is plain text with one op per
line and no dialects. Transcendentals (`exp`, `rsqrt`, row reductions) are IR
`func`s written with SFPU primitives in a prelude file, not compiler built-ins.

---

## 2. The IR

### 2.1 Lexical

- One op per line. `#` starts a comment. Values are `%name`, functions are
  `@name`, and attributes are `key=value` or `@flag`.
- Blocks are closed with `end`. There are no braces.
- Literals are integers, floats, `-inf`, `+inf`, and hex.

### 2.2 Declarations (kernel header)

```
kernel NAME
grid    rects (x0,y0)-(x1,y1) ...  [as %x, %y, %i]   # core set; binds coords + linear index
dst     f32 | bf16                                  # Dst accumulate mode for the kernel
param   NAME : u32                                  # uniform launch param (rebindable)
param   NAME : u32 per-core [static]                # per-core value; static => specialize images
global  NAME : DTYPE[shape] LAYOUT                  # DRAM / host / remote buffer, launch-bound
pool    NAME : DTYPE tile x DEPTH  [layout=tiled|rowmajor]   # L1 ring on every core in the grid
chan    NAME : DTYPE tile x DEPTH  from SRCSET to DSTSET     # cross-core stream (remote pool)
sem     NAME                                        # L1 semaphore word on every core
```

`LAYOUT` is one of the following:

- `interleaved(page=N tiles, banks=…, order=tiled|rowmajor)`
- `shard(per-core)`
- `host`
- `l1(core)`

With `static`, the compiler builds one image per distinct value. This is the
old `specialize` key: projection row counts, DRAM port phase, and bank
rotation.

### 2.3 Value types

| Type | Lives in | Produced by | Notes |
|---|---|---|---|
| `u32`, `i32`, `f32` scalar | RISC GPRs | scalar ops, `param`, `ld` | replicated on demand |
| `tile<T>`, `blk<T,n>` | an L1 pool slot | `copy`, `pack`, `alloc`, `recv` | FIFO per pool, freed after last use |
| `srca<F>`, `srcb<F>` | SrcA/SrcB bank | `unpack.a/.b` | consumed by exactly one FPU op (valid bit) |
| `dst<T>` | Dst slot(s) | `unpack.dst`, `fpu.*`, `sfpu.*`, `dzero` | can be carried across loop iterations |
| `vec` | SFPU LReg (32 lanes) | `sfpu` vector ops | register-allocated; spills go to Dst |

**Ownership rule for mutable memory.** An L1 value is owned by one engine at a
time. Writes (`st`, `fill`, partial `copy`) happen on the owner. The first use
by another engine transfers ownership, and every earlier write is ordered
before it. That one rule replaces `fence()` + `push_back` in the old code.

**FIFO rule.** Within one pool, values must be first used by the consuming
engine in the order they were defined. The verifier checks this. If you need
out-of-order consumption, use two pools. A static liveness check ensures that
live slots never exceed `DEPTH`. Otherwise the kernel would deadlock, so this
is a compile error, not a hang.

### 2.4 Ops by engine

**Scalar (replicated):** `add sub mul divu remu and or xor shl shr lt ltu eq
select`, `param NAME`, `core.x core.y core.index`, `clock`.

**Data movement (BRISC/NCRISC; compiler picks, `@brisc/@ncrisc` overrides):**

```
%v = copy SRC -> POOL            # DRAM/remote/host -> new L1 value
copy DST <- %v | SRC             # L1 value -> DRAM/remote/host/param slot
copy mcast(RECT).POOL <- %v      # raw multicast (sync is yours, via sem)
%v = alloc POOL [fill=X]
%x = ld %v.elem[i]   /  st %v.elem[i], %x    # layout-aware element access
fill %v.elem[a:b], X
send CHAN <- %v | SRC            # chan producer (credits + mcast inferred)
%v = recv CHAN                   # chan consumer
atomic.add CORE.sem, n  /  sem.wait SEM >= n  /  sem.set SEM, n
```

`SRC`/`DST` are logical views: `W.row[r].tiles[0:K]`, `q.flat[a:a+32]`,
`kcache.tile[h, b, f]`, `core(x,y).POOL`, `host[addr]`, and
`launch(KERNEL).param[NAME]`.

**Unpack (TRISC0):**

```
%a = unpack.a %t  [as=FMT] [transpose] [bcast=row|col|scalar] [rows=a:b] [tilize]
%b = unpack.b %t  ...
%d = unpack.dst %t ...           # straight to Dst (UNPACR to dest)
```

**FPU (TRISC1):**

```
%d = fpu.matmul %a, %b [acc=%d0] [fidelity=n]
%d = fpu.add|sub|mul %a, %b [acc=%d0] [fidelity=n]
%d = fpu.copy %a | %b           # MOVA2D / MOVB2D
%d = fpu.reduce.max|sum %a [axis=row|col|all]   # GMPOOL / GAPOOL
%d = fpu.transpose %b
%a = fpu.to_a %d   / %b = fpu.to_b %d          # MOVD2A / MOVD2B, Dst reuse
%d = dzero
```

**SFPU (TRISC1).** There are two forms. The *map* forms iterate over whole
tiles, and the compiler handles faces, rows, and replay. The *vector* forms are
single instructions.

```
%o = sfpu.map (%d0, %d1, ...) [rows=a:b] [@macro]  |x0, x1, ...|     # elementwise, writes tile 0
       ... vector ops ...
       yield %y
     end
%v.. = sfpu.fold (%d0, ...) init(%acc..) [index] [rows=a:b] |x.., acc..|   # reduce slices into vecs
       ...
       yield %acc'..
     end
%v = vload %d.slice[s]  / vstore %d.slice[s], %v
%v = vconst X | vparam %scalar          # scalar -> all lanes (compiler picks LOADI/patch/Dst)
mad mul add iadd and or xor not shl shr abs
exexp exman setexp setman setsgn lz
cast round [stoch] swap(max/min) recip.approx lut
lanes.rot %v, n     lanes.transpose4 %v0..%v3     lane.row  lane.col  lane.index
where %cond ... [else ...] end           # lane-predicate stack (SETCC/PUSHC/POPC)
```

**Pack (TRISC2):**

```
%t = pack %d -> POOL  [as=FMT] [untilize] [relu] [rows=a:b] [accumulate=%t0]   # L1 accumulate
```

### 2.5 Control and functions

```
range %i = A, B [step S] [carry %a = %a0, ...]   ...  next %a', ...  end [-> %af, ...]
repeat ...            # same as range, but must lower to MOP/replay/HW loop, else compile error
unroll ...            # expand at compile time
if %c ... [else ...] end
func @name(args) -> (results) ... ret ... end     # SFPU/scalar helpers; called via replay or jal
```

Two small concessions to pure SSA keep kernels readable. First, an op written
with `acc=` and no result name accumulates in place, and the accumulator's name
then denotes the new contents. Second, inside `where`, rebinding a name is a
predicated write to the active lanes. A pass converts both to plain SSA before
anything else runs.

`carry` holds loop-carried SSA values: Dst accumulators, SFPU vectors, and
scalars. A carried `dst` stays resident in Dst for the whole loop. That is how
attention keeps O, m, and l across KV blocks.

### 2.6 What the compiler does, in order

No dialect stack is involved. These are passes over one data structure.

1. **Parse and verify.** Types, the FIFO rule, pool depth versus liveness, and
   the ownership rule.
2. **Specialize.** Produce one program per distinct static per-core key.
3. **Slice.** Assign each op its engine. For each engine, keep its ops plus the
   backward slice of scalars and the control flow they need.
4. **Edges.** Classify each cross-engine use and insert the protocol:

   | Edge | Protocol |
   |---|---|
   | dm → unpack | CB push and wait |
   | unpack → fpu | valid bit (implicit) |
   | fpu → sfpu | `STALLWAIT SFPU, MATH` |
   | math → pack | Dst semaphore; flip halves if no Dst value is live across the pack |
   | pack → dm | CB |
   | dm → dm on another core | `chan` credits plus a semaphore |
   | scalar computed on engine X and used on Y | L1 mailbox |

5. **Resources.** Allocate Dst slots, LRegs, replay slots (FPU and SFPU share
   the 32-entry RAM), TIDs per data-movement core, the NoC/port policy, and the
   L1 layout.
6. **Config state.** Run the dataflow pass from §1, per TRISC. Shared
   registers get a cross-thread handshake.
7. **Address generation.** Turn affine indices into addr-mods and counters.
   Turn uniform engine loops into MOP templates, and `sfpu.map` bodies into
   replay or load-macro. For example, `fidelity=2` becomes the MOP outer loop.
8. **Emit.** RISC-V for the five cores, Tensix instruction words, and the
   manifest. The manifest records params, uniform/static values, and images per
   core set.

The compiler also writes a **report**: config writes per loop body, Dst
residency, replay use, the steady-state issue count per tile for each engine,
and the predicted bottleneck engine. That report serves goal 7 better than any
syntax choice.

---

## 3. Real kernels in the IR

The listings are abridged where noted, but none of them hides a call into
Python.

### 3.1 Embedding (`kernels.py:74`)

The old kernel is about 45 lines across BRISC/NCRISC, with hand-written shifts
to find the token's page and offset.

```
kernel embedding
grid    rects (1,2)-(1,2)
param   token_pos : u32
global  ids   : u32[8192]            interleaved(page=1024 elems)
global  emb   : bf16[128256, 2048]   interleaved(page=1 tile, order=tiled)
global  out   : bf16[1, 2048]        interleaved(page=1 tile, order=tiled)
pool    row   : bf16 tile x 2

%pos = param token_pos
%tok = ld ids.elem[%pos]                 # DRAM scalar: page read + offset, inferred
range %t = 0, 2
  %r = copy emb.row[%tok].tile[%t] -> row
  copy out.tile[%t] <- %r                # dm -> dm edge: BRISC reads, NCRISC writes
end
```

A `ld` on a `global` is a NoC read of one page into scratch L1, followed by a
load. The old code wrote that out as `srli/andi/read_tile/slli/add/read`.

### 3.2 Projection: qkv with fused RMSNorm (`kernels.py:178`, BF16 path)

The old code is about 300 lines of Python generating five streams by hand. The
IR below shows q only; k and v are the same three lines with different
names.

```
kernel qkv
grid    proj_cores as %x, %y, %i
dst     f32
param   rows   : u32 per-core static          # 46 | 47 -> two images
param   row0   : u32 per-core
param   phase  : u32 per-core static          # DRAM port rotation, %i % 3
global  x      : bf16[1, 2048]  interleaved(order=tiled)
global  gamma  : bf16[1, 2048]  interleaved(order=tiled)
global  Wq     : bf16[2048, 2048] interleaved(page=1 tile, banks=8, order=rowmajor-tiles)
global  q_out  : bf16 tile[cores] shard(per-core)
pool    inp    : bf16 tile x 4                # x tiles then gamma tiles
pool    xn     : bf16 tile x 2
pool    wp     : bf16 tile x 4                # 2 rows of K=2 tiles in flight
pool    sc     : bf16 tile x 2
pool    cmp    : bf16 tile x 1

# --- RMSNorm (once per launch)
%xg  = copy x.tiles[0:2] ++ gamma.tiles[0:2] -> inp          # one completion group
%d   = unpack.dst %xg                                         # blk of 4 Dst tiles
%sq  = sfpu.fold (%d.tile[0:2]) init(%a = vconst 0) |x, a|
         %a2 = mad %x, %x, %a
         yield %a2
       end
%ss  = call @lanes_sum(%sq)                                   # prelude: SHFT2 butterfly + TRANSP
%ms  = mad %ss, vconst 0.00048828125, vconst 1e-5             # mean + eps
%r   = call @rsqrt(%ms)
%dn  = sfpu.map (%d.tile[0:2], %d.tile[2:4]) @macro |x, g|    # load-macro: x*r on load, *g
         %y = mul %x, %r
         %z = mul %y, %g
         yield %z
       end
%xnv = pack %dn -> xn

# --- one dot product per owned row
%c = alloc cmp fill=0
range %r = 0, param rows
  %w = copy Wq.row[param row0 + %r].tiles[0:2] -> wp  @noc(0) @port(param phase)
  range %k = 0, 2 carry %acc = vconst 0
    %wa = unpack.a %w.tile[%k]
    %xb = unpack.b %xnv.tile[%k]
    %p  = fpu.mul %wa, %xb fidelity=2
    %acc2 = sfpu.fold (%p) init(%acc) |x, a|
              %s = add %x, %a
              yield %s
            end
  next %acc2 end -> %accf
  %sum = call @lanes_sum(%accf)
  %ds  = dzero
  vstore %ds.slice[0], %sum
  %t   = pack %ds -> sc
  %v   = ld %t.elem[0]                       # scalar on NCRISC (pack -> dm edge)
  st %c.elem[%r], %v                         # layout-aware: face/row offset inferred
end
copy q_out.tile[%i] <- %c                    # 'write NoC = 1 - read NoC' is policy
```

What disappeared:

- `_read_pages_body` and its coordinate table. `interleaved(banks=8)` plus a
  static `row0 % 8` gives the compiler the bank walk.
- `_set_addr_mod` ×4 and the `LoopTemplate`. `fpu.mul fidelity=2` inside a
  `range` over a uniform pair is the MOP.
- The `TTREPLAY` loop and the `SETRWC` pairs. `sfpu.fold` over a Dst tile is
  the replay body.
- `sem_wait(MATH_PACK)` / `_move_acquired` / `_release_dst`, all inferred.
- The `trisc0.range(sum(rows))` mirror loop, from slicing.
- `_tile_offset` in `st %c.elem[%r]`.

What stays explicit is the performance shape:

- `wp` depth 4 means two rows in flight.
- The read NoC and port are set per core.
- `@macro` requires the load-macro.

### 3.3 Attention, unsplit decode path (`kernels.py:898`)

In this listing, `HT` is head tiles (4) and `G` is group size (4 query rows).
The online softmax uses prelude functions so the shape stays visible. §3.5
shows one of those functions written out.

```
kernel attention
grid    first 8 workers as %x, %y, %i
dst     f32
param   kv_blocks  : u32
param   valid_cols : u32
global  q      : bf16[1, 4096]                interleaved(order=tiled)
global  kc     : bf16 tile[8, 256, HT]        interleaved
global  vc     : bf16 tile[8, 256, HT]        interleaved
global  ctx    : bf16[1, 4096]                interleaved(order=tiled)
pool    qp : bf16 tile x HT
pool    kp : bf16 tile x 2*HT
pool    vp : bf16 tile x 2*HT
pool    pp : bf16 tile x 1
pool    op : bf16 tile x HT

%h  = core.index
%q  = alloc qp fill=0
unroll %g = 0, G
  unroll %f = 0, HT
    copy %q.tile[%f].row[%g] <- q.flat[(%h*G + %g)*128 + %f*32 : +32]   # 2 face-row writes
  end
end
%nb = param kv_blocks
range %b = 0, %nb carry %o = dzero x HT, %m = dconst -inf, %l = dconst 0
  %k = copy kc.tile[%h, %b, 0:HT] -> kp               # unsplit: core h owns KV head h
  %v = copy vc.tile[%h, %b, 0:HT] -> vp
  range %f = 0, HT carry %s = dzero
    %s2 = fpu.matmul (unpack.a %q.tile[%f]), (unpack.b %k.tile[%f] transpose), acc=%s fidelity=2
  next %s2 end -> %sc
  %lim = select (eq %b, sub %nb, 1), param valid_cols, 32   # mask only the last block
  %sm = sfpu.map (%sc) rows=0:G |x|                        # tail mask, no instruction patching
          where ge lane.col, vparam %lim
            %x = vconst -inf                               # predicated rebind
          end
          yield %x
        end
  %pr, %m2, %l2, %al = call @online_softmax(%sm, %m, %l, scale=0.0883883)  # rows 0:G
  %o2 = sfpu.map (%o, %al) rows=0:G |o, a| %y = mul %o, %a  yield %y end
  %p  = pack %pr -> pp                                   # Dst value %o2 stays live: no half flip
  unroll %f = 0, HT
    fpu.matmul (unpack.a %p), (unpack.b %v.tile[%f]), acc=%o2.tile[%f] fidelity=2   # in place
  end
next %o2, %m2, %l2 end -> %of, %mf, %lf
%on = sfpu.map (%of, %lf) rows=0:G |o, l| %y = mul %o, (call @recip(%l)) yield %y end
%ot = pack %on -> op
unroll %g = 0, G
  unroll %f = 0, HT
    copy ctx.flat[(%h*G + %g)*128 + %f*32 : +32] <- %ot.tile[%f].row[%g]
  end
end
```

The split-KV variant adds `param phase per-core` and `if ge %phase, %live`
around the body. The compiler replicates that one predicate onto all five
cores, which is exactly the old `empty_exits`, without five hand copies.

### 3.4 Argmax (`kernels.py:1855`)

```
kernel argmax
grid    first N workers as %x, %y, %i
param   start : u32 per-core
param   count : u32 per-core
global  logits  : bf16 tile[N, T] shard(per-core)
global  history : u32[8192] interleaved
global  out     : u32[1] host
pool    lg   : bf16 tile x T
pool    cand : f32 tile x 1
pool    part : u32 tile x 1 @core(0,0)        # gather target
sem     arrived

%L = copy logits.tile[%i, 0:T] -> lg
%d = unpack.dst %L
%bv, %bi = sfpu.fold (%d) index init(%v = vconst -inf, %j = vconst 0) |x, idx, v, j|
             where and (lt %idx, vparam param count), (gt %x, %v)   # padding never wins
               %v = %x
               %j = %idx                    # logical index: physical_to_logical is gone
             end
             yield %v, %j
           end
%cd = dzero x 2
vstore %cd.slice[0], %bv
vstore %cd.slice[64], %bi
%c = pack %cd -> cand
range %n = 0, 32 carry %best = 0, %id = 0x7fffffff     # 32 candidates, scalar loop on dm
  ... ld %c.elem[%n], ld %c.elem[64+%n], compare ...
next ... end -> %bk, %bid
copy core(0,0).part.elem[2*%i : +2] <- (%bk, add param start, %bid)
atomic.add core(0,0).arrived, 1
if eq %i, 0
  sem.wait arrived >= N
  ... scalar reduce over part ...
  copy out <- %tok
  copy history.elem[param write_pos] <- %tok
  copy mcast(all).launch(embedding).param[token_pos] <- %pos1   # autonomous replay
end
```

The cross-core gather stays explicit (raw `copy` + `sem`) because it is a
protocol, not a stream. The compiler still tracks the NoC completion. You only
write the "receiver may read" semaphore, which is program logic.

### 3.5 Prelude example: `@lanes_sum`

The cross-lane reduction is IR, not a built-in:

```
func @lanes_sum(%v: vec) -> vec        # sums each 8-lane row, then the 4 rows; result broadcast
  unroll %r in (4, 2, 1)
    %t = lanes.rot %v, %r
    %v = add %v, %t
  end
  %a, %b, %c, %d = lanes.transpose4 %v, %v, %v, %v
  %s = add (add %a, %b), (add %c, %d)
  ret %s
end
```

That is 10 lines, replacing 16 hand-written words with explicit `SFPNOP`
spacing. The compiler inserts the NOPs by scheduling around latencies.

### 3.6 Multicast matmul (`matmul_peak_kernel`, sketch)

```
grid    rects (0,0)-(C-1,R-1) as %x, %y
chan    ar : bf16 tile x 2*W  from (0,%y) to (*,%y)      # A panels along each row
chan    bc : bf16 tile x 2*W  from (%x,0) to (%x,*)      # B panels down each column
range %kb = 0, KB carry %acc = dzero x (SH*SW) ...
  if eq %x, 0   send ar <- A.tiles[rowblock(%y), %kb*W : +W]   end
  if eq %y, 0   send bc <- B.tiles[%kb*W : +W, colblock(%x)]   end
  %a = recv ar
  %b = recv bc
  ... unroll subblocks: fpu.matmul (unpack.a %a.tile[..]), (unpack.b %b.tile[..]), acc=...
next ... end
... pack accumulate=%partial (packer L1 acc) for K-spill, untilize to row-major, copy out
```

`if eq %x, 0` depends only on a core coordinate, so the compiler specializes it
statically. That produces the four sender/receiver roles from
`boop-docs/matmul/scheduling.md` without four kernels.

---

## 4. Where it strains

Ordered roughly by risk.

1. **SFPU lane geometry.** A `vload` slice maps lanes to (row, col) in an
   interleaved way. The old code says "lane columns are `(2*lane % 16)` +
   face/parity". `sfpu.map` hides this for elementwise work. Row reductions,
   masks, and argmax indices still depend on it. Exposing `lane.row`,
   `lane.col`, and `lane.index` as compiler-computed intrinsics helps, but
   anyone who writes `lanes.rot` still has to know the geometry. Expect the
   prelude to carry most of that knowledge.
2. **Load-macro and SFPU scheduling.** Automatic load-macro use plus latency
   scheduling is the one place where the compiler must beat hand schedules and
   probably won't at first. `@macro` (restricted body: one load, at most one
   op per sub-unit, one store) maps 1:1 to the hardware template, so humans
   keep control. Its body shape is a hardware constraint showing through.
3. **Replay/MOP as a shared resource.** The FPU and SFPU share the replay RAM
   (the old attention kernel reserves 16..31 by hand). If automatic allocation
   fails, performance falls off a cliff without a visible cause. The mitigation
   is that `repeat` turns that failure into an error, plus the report.
4. **Config shared across TRISCs.** Some config is read by more than one
   thread, such as formats seen by both unpack and math. Format changes inside
   a pipelined loop (FP8 weights plus BF16 activations, or the FP8 quantize
   prologue) need a cross-thread handshake. Inference is correct but can be
   slow, and the report must show it.
5. **FIFO and lifetime inference.** Pool sharing is legal only when
   consumption order matches production order. Retained values (Q across all
   KV blocks) work, but they occupy depth. Users will hit "pool too shallow
   for this liveness" errors and need to understand slots. That is a
   reasonable cost, but it is a concept.
6. **Data-dependent control across engines.** Replication works for anything
   computed from params, coordinates, or loop indices. A branch that depends
   on a computed value (from L1 or Dst) forces a mailbox forward to the other
   engines, which adds latency nobody wrote. The compiler should warn on it.
7. **Code size.** TRISC instruction memory is small. The old code outlines
   aggressively (`k.outline`, `k.subroutine`). The compiler must dedupe
   identical sliced regions into subroutines. Explicit `func` is the manual
   fallback.
8. **NoC hazards that are global properties.** "Never mix split-NoC and
   rotated-port policies inside one program; it hung both p150a cards"
   (`_projection_route`) is a whole-program invariant. The compiler must
   enforce a per-kernel NoC policy. It is not visible in any single op.
9. **Cross-launch state.** Argmax writes the next embedding's params and
   multicasts runtime state for autonomous replay. `launch(K).param[...]` makes
   the manifest part of the IR's namespace, so the IR and the runtime are now
   coupled.
10. **Out of scope today.** Ethernet/ERISC, PCIe/host dispatch, and the
    command queue. "Every part of the device" needs either a second engine
    family (an ERISC slice of the same IR) or an explicit statement that this
    IR is Tensix-only.
11. **tinygrad mismatch.** tinygrad's idea of a "vector" is not a 32×32
    faced tile, and its loads are synchronous pointer loads. The renderer has
    to tile to 32×32 and pad partial tiles (`pack rows=`, masked copies).
    Fast tinygrad output also needs a Blackhole `TensorCore` entry and opts
    that pick pool depth and Dst blocking. Correct-but-slow output comes
    cheap; fast output does not.

---

## 5. Small decisions I made and why

- **Explicit `unpack` rather than an FPU op taking L1 tiles.** It costs tinygrad
  one extra line, and it keeps transpose, broadcast, format, and tilize on the
  op that actually performs them.
- **No `exp` in the IR.** tinygrad already decomposes transcendentals
  (`tinygrad/codegen/decomp/transcendental.py`) for backends without them.
  Humans get a prelude of IR `func`s. Either way the compiler stays small, and
  the math stays visible and editable.
- **SSA with `carry` instead of mutable registers.** Liveness of Dst and L1
  falls out of SSA directly. Liveness *is* the sync protocol here.
- **Data-movement core assignment is inferred, not declared.** BRISC and NCRISC
  are interchangeable for most work. The default is reads on one and writes
  on the other (matching `write_noc = 1 - read_noc`), with `@brisc`/`@ncrisc`
  to override.

---

## 6. tinygrad emission sketch

The renderer is a table in the style of `tinygrad/renderer/cstyle.py`:

| UOp | IR |
|---|---|
| `DEFINE_GLOBAL` | `global` decl, layout from the buffer |
| `SPECIAL` (global idx) | `core.index` / `grid as %x,%y` |
| `RANGE` / `END` | `range` / `end` |
| `LOAD` of a 32×32 global tile | `copy -> pool` then `unpack.dst` (or `.a/.b` when feeding WMMA) |
| ALU ops on tile-vectors | body of one `sfpu.map` (consecutive elementwise UOps fuse into one map) |
| `WMMA` | `fpu.matmul` with `acc=` |
| `DEFINE_REG` + reduce | `carry` of a `dst` (FPU) or a `vec` via `sfpu.fold` |
| `STORE` to global | `pack -> pool` then `copy` |
| index ALU on ints | scalar ops |

Pool depths default to 2, which gives double buffering for free. tinygrad's
search can tune depth and Dst blocking later, the same way it tunes upcast and
local today.

---

## 7. Reading list

**Decoupled access/execute and one-program-to-many-cores (goal 5)**

- **J. E. Smith, "Decoupled Access/Execute Computer Architectures" (ISCA 1982).**
  BRISC/TRISC0/TRISC1/TRISC2 is a DAE machine. This paper defines the
  vocabulary and the deadlock and queue-depth issues your pools inherit.
- **Ottoni et al., "Decoupled Software Pipelining" (MICRO 2005).** The
  algorithm for slicing one loop into a pipeline of threads joined by
  queues. It is literally your §2.6 step 3–4.
- **Moreau et al., "VTA: An Open Hardware-Software Stack for Deep Learning"
  (IEEE Micro 2019).** Load/compute/store modules joined by dependency-token
  queues, driven by one instruction stream. This is the closest published
  analogue to unpack/math/pack with semaphores.
- **Chen et al., "Tawa: Automatic Warp Specialization for Modern GPUs with
  Asynchronous References" (2025).** A compiler that turns a single-program
  Triton kernel into producer/consumer warp roles with inferred barriers. This
  is goal 5 on Hopper.
- **Yadav et al., "Cypress: Task-Based Tensor Computations on Modern GPUs"
  (PLDI 2025).** A sequential task program compiled to warp-specialized code
  with inferred data movement. Read it for how they keep the user's mental
  model sequential.

**Streams and FIFOs between engines (goal 3 and the pool/chan design)**

- **AMD MLIR-AIE / IRON "ObjectFifo".** A depth-annotated FIFO object that
  hides locks and DMA between AI Engine tiles, both local and remote. It is
  the nearest prior art to `pool` + `chan`. It also shows what goes wrong
  when FIFO lifetimes are too implicit.
- **Huawei Ascend C programming guide (`TQue`, `EnQue`/`DeQue`, CopyIn/Compute/CopyOut).**
  The same CB protocol, exposed to users. A useful contrast: they make the
  user write the queue ops, and you infer them.
- **Cerebras SDK / CSL docs (DSDs, colors, tasks).** Data Structure
  Descriptors are declarative, auto-incrementing address generators fed to
  vector ops. That is the right mental model for exposing Blackhole address
  counters as indices instead of registers.
- **StreamIt (Thies et al., CC 2002).** Static-rate streams and how
  compile-time knowledge of rates lets you size buffers and prove deadlock
  freedom. That matters for your "pool too shallow" check.
- **NVIDIA CUTLASS pipelines / `mbarrier` + TMA docs.** A producer/consumer
  async-copy pipeline at the asynchronous NoC-copy level. Their
  `PipelineState` is the hand-written thing you want the compiler to derive.

**Hardware loops, address counters, replay (goal 7)**

- **Zaruba et al., "Snitch" (IEEE TC 2020); Schuiki et al., "Stream Semantic
  Registers" (IEEE TC 2021); the FREP extension.** Hardware loops, a sequencer
  that replays instructions, and affine address streamers on a tiny RISC-V.
  These are almost the same primitives as MOP, replay, and ADCs, and the
  papers cover how a compiler targets them.
- **B. R. Rau, "Iterative Modulo Scheduling" (MICRO 1994).** What the SFPU
  scheduler (latency-aware NOP removal, load-macro overlap) really is.
- **Exo: Ikarashi et al., "Exocompilation for Productive Programming of
  Hardware Accelerators" (PLDI 2022).** The best treatment of
  *configuration state as a first-class compiler concern* for accelerators.
  Read the config-state and hardware-library sections for goal 1.

**Tile-level kernel languages (goal 7 ergonomics)**

- **Triton (Tillet et al., MAPL 2019) and its TTGIR layouts.** Block-level SSA
  with the compiler owning layouts and pipelining, and the canonical "humans
  write tiles, compiler writes threads" design.
- **TileLang (2025) and ThunderKittens (Spector et al., 2024).** Two opposite
  bets on how much to expose. TK's small set of tile primitives is close to
  your goal 9. TileLang shows explicit pipelining annotations
  (`T.Pipelined(num_stages=)`), which correspond to your pool depth.
- **Pallas / Mosaic (JAX docs, "Pallas TPU" pipelining).** TPU is another DAE
  machine with a vector unit and DMA. `BlockSpec` + `emit_pipeline` is a
  clean way to state the copy-in/compute/copy-out shape.
- **Graphene (Hagedorn et al., ASPLOS 2023) and CuTe layouts (CUTLASS 3 docs).**
  Layout algebra for mapping logical indices to swizzled physical ones. This
  is how to specify the face layout and the SFPU lane map *once*, as data.
- **Halide (Ragan-Kelley et al., PLDI 2013).** Algorithm/schedule separation.
  Useful mostly as the road you are *not* taking for kernels. Read it to
  decide which knobs belong as attributes.

**Small IRs and backend contracts (goals 8, 9)**

- **PTX ISA manual.** The proven model for "a virtual ISA is the contract
  between many producers and one backend". It has virtual registers, the
  backend allocates and schedules, and completeness is relative to the
  hardware. Copy its discipline about what the backend may assume.
- **QBE IL (c9x.me/compile).** A tiny, readable SSA text format with
  one op per line, a good syntax reference for keeping the text format small.
- **tinygrad `renderer/cstyle.py`, `renderer/ptx.py`, `renderer/tc.py`,
  `uop/spec.py`, `codegen/decomp/transcendental.py`** (local, in `tinygrad/`).
  These show exactly how much machinery a renderer gets to have. `tc.py` is
  where a 32×32 Blackhole "tensor core" would plug in.
- **luminal** (local, `luminal/`). A deliberately tiny primitive op set for ML
  compilation. Read it for the "how few ops" argument.

**Tenstorrent-specific**

- **`tt-isa-documentation/BlackholeA0`** (local). Use it for the
  instruction-classification table in §1 (op versus compiler state) and for
  errata the compiler must encode: SFPMAD auto-stall, SFPSTOCHRND bias,
  `NOC_CMD_L1_ACC_AT_EN`.
- **`tt-llk`** (local). Every `_init`/`reconfig` function is a config-state
  transition your pass must reproduce. Mine it for the state model and for MOP
  templates per op.
- **`tt-lang` spec, `docs/sphinx/specs/TTLangSpecification.md`** (local). This
  is the closest existing design: dataflow buffers and `Pipe`/`PipeNet`. It
  still splits kernels into `@ttl.compute` and `@ttl.datamovement`
  functions, which is the exact thing your goal 5 removes. Its functionality
  matrix shows where they got stuck.
- **`tt-mlir` TTKernel / D2M docs** (local, `tt-mlir/docs/src`). How
  Tenstorrent lowers to per-RISC kernels through dialects. Read it to see
  which of their passes you need (CB inference, Dst allocation) and which you
  don't (goal 9).
- **Peter Cawley (corsix), "Tenstorrent Wormhole" blog series.** First-principles
  reverse engineering of Tensix: MOP, replay, address counters, and the NoC.
  It is the best prose explanation of why the hardware is shaped this way.
- **`boop-docs/kernel-dev/known-issues.md`, `boop-docs/matmul/scheduling.md`**
  (yours). Known-issues is the list of invariants the compiler must own. The
  four-roles table is the test of your static-specialization rule.
- **Mesa Gallium state tracker / "dirty bits" pattern.** The dataflow pass for
  goal 1 is a driver state tracker turned into a compile-time pass.
