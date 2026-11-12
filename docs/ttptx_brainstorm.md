# ttptx brainstorm: cbs, spaces, registers, instructions

Notes from reading `kernels/llama3-1b/qkv` (brisc line by line; ncrisc, trisc0, trisc1 by their mmio and tensix
instructions; trisc2 not read) and its old source, `_projection_program` in
`blackhole-py-old/examples/llama3/kernels.py`. Embedding and argmax were read from the old source only. Attention
and attention_merge were read from the old source only (section 9), not from the disassembly. PTX instruction names are from memory and need checking against the PTX spec.

Companion to `ttptx.md` (goals, concepts) and `ttptx_isa.md` (the actual instruction list, still empty).

## 1. the rule

The risc-v cores exist to run the coprocessor. The isa is one level above risc-v, not a respelling of it.

- An instruction either moves tiles / elements between spaces, or computes on the coprocessor, or is control
  skeleton (loops, calls, conditions).
- If a kernel is mostly scalar instructions, the isa is missing an instruction.
- Scalar risc-v work is allowed (section 5) but it is the exception and it is still typed and checked.

## 2. circular buffers / streaming

### what a cb is in the emitted code

- an l1 ring region
- two 16-bit counters in overlay stream registers: `STREAM_REG(stream, 8)` received, `STREAM_REG(stream, 10)`
  acked (e.g. `0xffb4e028` / `0xffb4e020`)
- a private pointer shadow in each risc's local memory (`0xffb00878..`)

reserve / push / wait / pop are all compare-and-bump on those counters plus a wrap check.

### what qkv uses cbs for

| cb in qkv | pattern | what it really is |
| --- | --- | --- |
| `weight_cb` (brisc -> trisc0), `scalar_cb` (trisc2 -> ncrisc) | written and consumed once per row; `weight_cb` is 2 rows deep so brisc reads ahead | fifo |
| `operands`, `normalized_cb` | written once, waited on once; normalized x is then re-read every row and never popped | latch / future |
| `compact_cbs` | ncrisc-private scratch tile | plain l1 allocation |

The other handoffs are not cbs: unpack -> math is the srcA / srcB valid handshake, math -> pack is the `MATH_PACK`
semaphore over dst. In ssa all of these are the same thing: a value defined on one risc and used on another.

### proposal

The cb is not a user-facing object. It is what a cross-risc def-use edge lowers to when the value lives in l1.

- l1 working tiles are a register class, not a state space. You declare virtual l1 tiles and the compiler
  allocates addresses (what `p.cb()` / `p.l1()` did).
- the protocol falls out of loop structure:
  - defined outside a loop, used inside: latch (wait once, never pop)
  - defined and used in the same iteration on different riscs: fifo
- depth is the only knob: how many iterations the producer may run ahead. Same meaning as
  `cp.async.wait_group N`.
- the lowering is loop distribution. The old source does it by hand: `p.brisc.range(rows)`,
  `p.trisc0.range(rows)`, `p.trisc2.range(rows)`, `p.ncrisc.range(rows)` are one loop copied per risc. The
  compiler assigns each instruction to a risc, splits the loop, and inserts ring + counters on each crossing edge.
- the primitive underneath is `mbarrier`-shaped (`mbarrier.arrive.expect_tx`,
  `cp.async.bulk ... mbarrier::complete_tx::bytes`, `mbarrier.try_wait`). Keep it as an explicit ir op so a
  hand-written kernel can use it when inference is not enough.

### catches

- control flow must be replicable: every risc gets its own copy of the loop, so conditions must be functions of
  params and induction variables. A branch on a computed value needs an explicit scalar channel to the other
  riscs.
- cross-core credits are a separate problem. In qkv everything cross-core goes through dram, so there was no
  core-to-core stream to model it on.
- cost: placement and loop distribution become the core of the compiler. Cheaper first step: explicit
  `mbarrier`-style ops and a per-instruction risc annotation, inference added later.

## 3. state spaces

Addressable. The space is part of the pointer / tensor type.

| ours | ptx analog | notes |
| --- | --- | --- |
| `.dram` | `.global` | bank interleave hidden behind a tensor declaration, like a tma tensor map. the bank -> noc coordinate table is a compiler-emitted `.const` (today embedded three times in qkv brisc) |
| `.l1::core` | `.shared::cta` | only for persistent or explicitly addressed l1 |
| `.l1::grid` | `.shared::cluster` + `mapa` | `mapa` turns a local reference plus a core into a remote one |
| `.param` / `.param::core` | `.param` | uniform args at `0x780`, per-core table at `0xe8c0`; the manifest already splits `uniform` and `per_core` |
| `.const` | `.const` | pc-relative in the image |
| `.local` | `.local` | per-risc local memory. compiler use (shadows, spills) |
| `.host` | none | argmax posts the token over pcie |

Addressing is by subscript on a declared tensor, in the tensor's own units (row, tile, page, element):
`[wq: row0 + r]` is row `row0 + r` of `wq`. The compiler owns the interleave math. Precedent:
`cp.async.bulk.tensor` takes a tensor map and coordinates, not an address.

## 4. register spaces

Not addressable. The class decides which risc runs the op.

| class | physical | notes |
| --- | --- | --- |
| `.idx` | x-regs on any risc | index values, see below |
| `.x32` | x-regs on one risc | general scalar, section 5 |
| `.l1.tile.<fmt>` | l1, allocator-managed | new. this is where cbs come from |
| `.src` | srcA, srcB | one physical register each, live ranges may never overlap |
| `.tile.b16` / `.tile.b32` | dst | qkv uses 64-row offsets (0 / 64 / 128 / 192) in fp32 mode, consistent with 16 x b16 or 8 x b32 |
| `.lreg.f32` / `.lreg.s32` | lregs | 32 lanes. spills to dst rows, so one allocator with dst |
| `.pred` | sfpu condition-code stack | depth checked |
| `.sreg` | none | read-only `%core.x`, `%core.y`, `%core.idx`, `%ncores`, like `%tid` / `%ctaid` |

Difference from ptx: ptx registers belong to one thread. Here the class picks the processor, and src / dst / lreg
values come out of a queued pipeline, so each has an availability point the way a `cp.async` destination does.

### index values

- come from: a param, a loop induction variable, an `.sreg`, an affine combination of those, or a load from a
  tensor
- go to: a subscript, a trip count, a loop / `if` condition, or a store into a tensor
- are replicated: an index used on several riscs is recomputed on each, no channel needed

Embedding is the data-dependent case. The old source does `srli` / `andi` / `slli` / `add` on brisc; here:

```
ld.idx    %tok, [history: pos]        // token id read from dram
cp.async  %x,   [emb: %tok]           // row selected by data
```

## 5. risc-v scalar work

Open question: how much real work does the risc-v do beyond driving the coprocessor in a loop? Needs a read of
every kernel. Inventory so far:

| kernel | risc-v work that is not coprocessor control | could be an instruction? |
| --- | --- | --- |
| qkv / lm | ncrisc copies one value from the scalar tile into slot `r` of the compact tile | `mov.elem %compact[r], %d0[0]` |
| o / down | ncrisc gathers this core's residual features into compact layout | `gather %res_c, %res[start : start + n]` |
| gate, o, down | scatter of compact rows into the dense output (`_scatter_dense`) | scatter, not yet read in detail |
| all | zeroing an l1 tile | `zero` |
| embedding | token id -> row address | `ld.idx` + subscript |
| argmax | sfpu keeps 32 candidates per core; brisc picks the best of 32; core 0 picks the global winner, writes host memory and token history, multicasts next-token params | `hmax` with index on the sfpu, or one `argmax.tile` instruction; the multicast of runtime params is unexamined |
| attention | rope gather across per-core shards with a sign flip, cos / sin row select and replicate, query re-layout, causal mask build, k / v cache row append, dense context scatter. see section 9 | mostly tensor declarations plus `gather` / `relayout` / `fill`; no `.x32` needed so far |

Everything found so far is element-granularity data movement or a small reduction, not arithmetic. That argues for
a few move / gather / scatter / reduce instructions. But the list is incomplete, and each added instruction makes
the isa bigger.

### fallback: a scalar register space

If the inventory keeps growing, give risc-v a real register class (`.x32`) with the ordinary ptx scalar set
(`add sub mul and or shl shr setp selp`), interleaved with everything else. This still reads fine as long as most
kernels barely use it. Rules that keep the goals intact:

- no raw addresses. `.x32` values load from and store to typed spaces through subscripts, never through an
  integer cast to a pointer. That keeps mmio, config registers and noc registers unreachable (goals 1 to 3) and
  keeps the state trackers sound.
- `.idx` is the restricted subset of `.x32`: affine and replicable. An `.x32` value that is not replicable lives
  on one risc; using it on another is a channel crossing like any other value.
- placement: the compiler puts scalar ops on the risc that already owns their inputs or outputs. An optional pin
  (`.on ncrisc`) for when it matters.
- it is isa, not an escape hatch: the assembler, disassembler and reference interpreter all understand it, so
  goal 6 (never go below this layer) still holds.

Suggested order: start with `.idx` plus the move / gather / scatter instructions, add `.x32` when a kernel needs
it, and treat each `.x32` use as a hint that an instruction may be missing.

## 6. instructions

### take from ptx

- control: `bra`, `call`, `ret`, `@p` guards, loops with trip counts
- `cp.async` with commit / wait groups for noc reads. brisc already does both forms: a throttle on outstanding
  reads `< 129` and a full barrier on `== 0`
- `mbarrier.*` for the counter pair
- `atom.add` / `atom.cas` / `atom.exch` on `.l1::grid`. noc atomics are integer only as far as i know, so this
  covers credits and semaphores, not float tree reductions. verify
- `.rn` / `.rz`-style modifiers for pack rounding and fidelity
- `fma`, `mul`, `add`, `min`, `max`, `abs`, `neg` on lregs
- `mapa` for remote l1
- the scalar set, only if `.x32` exists

### invent

- `ld.tile.<fmt>` / `st.tile.<fmt>`: unpack and pack
- fpu ops on src / dst: `elwmul`, `elwadd`, `mvmul`, `mov` between A / B / dst, `zero`, with `.acc` and `.pN`
- `ld.rows` / `st.rows`: between a dst tile and lregs
- `map.rows %d, fn`: run an sfpu function over every row group of a tile. lowers to replay / mop (trisc1 records
  four such bodies in replay slots 0 to 18)
- `hsum`, `hmax`: lane reductions. `hsum` today is a `SFPSHFT2` / `SFPADD` / `SFPTRANSP` chain
- macro instructions the compiler expands, e.g. `rsqrt` (trisc1 does newton steps from `0x5f1110a0`)
- `mov.elem`, `gather`, `scatter`: element-granularity movement in l1
- `ld.idx` / `st.idx`: index values to and from tensors
- `.departed` / `.landed` waits on noc writes

## 7. qkv sketch

```
.reg .l1.tile.bf16 %ops[4]            // x, gamma: written once
.reg .l1.tile.bf16 %xn[2]             // normalized x: written once, read every row
.reg .l1.tile.bf16 %w[2]  .depth 2    // one weight row per iteration
.reg .l1.tile.bf16 %compact           // this core's outputs, one element per row

.visible .entry qkv (.param .dram x, .param .dram gamma, .param .dram wq, .param .dram q_out,
                     .param::core .idx row0, .param::core .idx rows) .cores 88
{
  cp.async       %ops[0], [x: 0], 2
  cp.async       %ops[2], [gamma: 0], 2
  ...rmsnorm: ld.tile -> dst, map.rows, st.tile.bf16 %xn...
  zero           %compact

  loop r, rows:
    cp.async       %w, [wq: row0 + r]          // brisc runs ahead by .depth
    loop t, 2:
      ld.tile.bf16   %srcA, %w[t]              // trisc0
      ld.tile.bf16   %srcB, %xn[t]             // latch: no pop
      elwmul.p2      %d0, %srcA, %srcB         // trisc1
      map.rows       %d0, dot_acc              // %acc += row group
    hsum           %s, %acc
    st.rows        %d0, %s
    mov.elem       %compact[r], %d0[0]         // trisc2 pack + ncrisc copy today

  cp.async       [q_out: %core.idx], %compact  // ncrisc, noc1
}
```

Nothing names a risc, a stream id, a pointer or a counter.

## 8. additions for ttptx.md from the disassembly

- config writes need a drain too, not only read-backs. trisc0 polls `UNPACK_CONFIG_SYNC` before its mmio config
  stores. emitting config as in-stream instructions (`SETC16`, `RMWCIB`, `WRCFG`) wherever possible makes ordering
  free.
- first win for the state tracker: trisc0 writes the same ~20 unpack config words and the full 9-word mop template
  twice, identically.
- each tracked state needs one owning risc, otherwise the tracker itself needs cross-risc sync.
- goal 4 ("program every part of the device") should say what it covers: every coprocessor and noc capability, plus
  scalar work through typed spaces. not arbitrary code on the five riscs.

## 9. attention

> **superseded.** The "what changes in the isa" list and the sketch below overcorrected: they design
> abstractions (tensor declarations, `gather`, `scatter`, `relayout`, `fill`) around a kernel nobody should
> write. Revised position:
> - an instruction may hide bookkeeping (config, noc transaction mechanics, cb counters, address counters, bank
>   interleave). it may not hide work.
> - no tensor declarations. ptx has none: it has byte-array variables in state spaces, pointers and integer
>   arithmetic. index math is written out in `.x32` scalar ops, so a bad layout shows up as a page of scalar code.
> - `gather` / `scatter` / `relayout` / `fill` / `mov.elem` are loops of `ld` / `st`. not instructions.
> - `hsum` / `hmax` / `rsqrt` are functions written in the isa, not instructions.
> - still stands from the list: dst allocated in row ranges and loop-carried (4), ordering without data and the
>   cross-core barrier (6).
> - the "what the risc-v does there" table is still accurate as a description of the old kernel.

Read from `_attention_program`, `_attention_rope`, `_rope_gather_group`, `_append_cache_rows` and
`attention_merge` in the old source. Not checked against the disassembly.

### what the risc-v does there

| risc-v work | why it exists | isa answer |
| --- | --- | --- |
| brisc gathers a head's 64 features out of several projection cores' compact shards (`_compact_locate` uses `divu`, then a min-of-three run-length loop, then `lhu` / `sh` per value) | qkv writes ragged per-core shards (46 or 47 rows each), attention wants head-major rows | sharded tensor declaration + `gather` by logical range |
| the same loop writes `rotate_half(x)` with the sign bit xor-ed on risc-v | rope operand built by hand | do it on the sfpu: row-pair swap + negate. half a head is 2 dst rows. verify the swap is expressible |
| cos / sin: read the table tile, copy one row, replicate it to each group | per-position row select | subscript `[cos: pos]` + a broadcast modifier on the multiply |
| ncrisc re-lays the rotated q from head-major into one matmul tile per feature tile (face-aware copies) | two tile layouts for the same data | `relayout` between declared layouts |
| brisc builds the causal mask: -inf words for columns >= `valid_columns` on 4 rows | scalar loop writing fp32 into l1 | `fill` on a rectangular region, or a 32-entry mask table indexed by `valid_columns` |
| ncrisc appends one k and one v row into a cache tile in dram (`pos >> 5`, `pos & 15`, face offsets) | cache tile = 32 tokens x 32 features, a token is one row | multi-dim tensor, subscript `[kcache: head, pos]`, compiler splits into the two 16-value face writes |
| ncrisc scatters the output heads into the dense context in 16-value runs | same | subscript by logical range on the dense tensor |
| `head = core >> 2`, `phase = core & 3`, `count = (blocks + 3 - phase) >> 2`, last-block ownership | split attention: 4 cores per kv head take every 4th block | per-core constant expressions + strided loop |

None of it is arithmetic on data. It is all layout conversion and index math, and nearly all of the index math is
there because of layout choices (compact shards, tilized faces, the cache tile shape).

### what changes in the isa

1. **tensor declarations become the centre, not a footnote.** A tensor needs dims, units, a tile layout
   (row-major or tilized faces), and optionally sharding (per-core shards with ragged counts). Subscripts go down
   to row / element granularity and take ranges. The compiler splits a logical range into contiguous runs. This
   one feature absorbs the rope gather, the cache append, the context scatter and the cos / sin select.
2. **layout conversion is an explicit instruction** (`gather`, `scatter`, `relayout`). The index math is hidden
   but the cost is not: these lower to risc-v copy loops or many small noc transactions, and the user should see
   that they wrote one.
3. **index expressions.** Any constant expression over `%core.idx` (div, mod, shifts) is legal and is folded per
   core by the assembler into the per-core table. Loops take a start and a stride. Runtime div / mod happens only
   inside multi-dim subscripts. With that, attention needs no `.x32`.
4. **dst is allocated in row ranges, not whole tiles, and is loop-carried.** O, m, l and alpha live in dst across
   all blocks (phi nodes at the loop head for dst-class values). Only 4 rows are live (`GQA_ROW_CHUNKS`), and
   `attention_merge` parks alpha and beta in unused rows of the max tile. `map.rows` and the reductions take a row
   range, and `hsum` / `hmax` need an axis (per row, 4 rows at once).
5. **dst -> src feedback.** Probabilities go dst -> pack -> l1 -> unpack -> srcA for P @ V. Write `mov %srcA, %d`
   and let the compiler pick pack + unpack or a direct move. An iteration visits trisc0 and trisc1 twice; loop
   distribution still works, but there is no read-ahead across that edge.
6. **ordering without data.** brisc must not read a cache block before ncrisc's append has landed (the `ready`
   cb). That is a memory dependency through dram, so tensors need memory-ssa style versions and the compiler
   inserts a token channel. Across cores the old kernel dodges this: workers sharing a kv head all write identical
   cache bytes and each waits on its own acks. The real fix is a cross-core barrier, the first actual use for
   `mbarrier` / `atom` on `.l1::grid`.
7. **`fill`** replaces `zero` and covers the mask.

### what attention confirms

- the latch / fifo split: the old kernel re-publishes the resident query every block
  (`reserve_back` + `push_back` with no write) because its cbs are fifo-only. A latch needs no hack.
- replay slots are a shared compiler resource: fpu matmul takes 16..31 and the sfpu gets the rest.
- replicable control flow is enough: the last-block branch is induction variable vs param on trisc0 and trisc1.

### sketch

```
.tensor .dram .bf16 q      [q_dim]                        .shard core      // qkv's compact output
.tensor .dram .bf16 kcache [kv_heads][max_tokens][head_dim] .tile [32][32]
.tensor .dram .bf16 cos    [max_tokens][head_dim]
.tensor .dram .bf16 ctx    [q_dim]
.const::core .idx head  = %core.idx / SPLIT
.const::core .idx phase = %core.idx % SPLIT

  // a. rope + cache append
  gather       %x,  [q: head*G*HD : +G*HD]           // brisc, runs across shards
  gather       %xk, [k: head*HD : +HD]
  gather       %v,  [v: head*HD : +HD]
  cp.async     %cs, [cos: pos]
  cp.async     %sn, [sin: pos]
  ...ld.tile into dst; map.rows rope (x*cos + neg(swap_halves(x))*sin, cos / sin broadcast); st.tile %rot...
  cp.async     [kcache: head, pos], %rot[k rows]  .landed
  cp.async     [vcache: head, pos], %v            .landed
  relayout     %qm, %rot[q rows]                     // head-major -> one tile per feature tile

  // b. blocks
  fill         %O, 0.0
  fill         %m, -inf
  fill         %l, 0.0
  loop b, phase, kv_blocks, SPLIT:
    cp.async     %K, [kcache: head, b*32 : +32]      // ordered after the append above
    cp.async     %V, [vcache: head, b*32 : +32]
    loop f, head_tiles:
      ld.tile.bf16   %srcA, %qm[f]
      ld.tile.bf16.t %srcB, %K[f]
      mvmul.p2.acc   %s, %srcA, %srcB
    if b == last:
      add          %s, %s, %mask
    call         softmax_update, %s, %m, %l, %O      // sfpu, 4 live rows
    mov          %srcA, %s
    loop f, head_tiles:
      ld.tile.bf16   %srcB, %V[f]
      mvmul.p2.acc   %O[f], %srcA, %srcB

  // c. normalize and scatter
  map.rows     %O, div_by_l
  scatter      [ctx: head*G*HD : +G*HD], %O
```

### does attention pass

Yes, with the seven changes above, and without a scalar register space. The risk moved: the hard part is no
longer the instruction set, it is the compiler's `gather` / `scatter` / `relayout` lowering, which has to
generate the run-splitting loops the old kernel wrote by hand.

A cheaper route worth weighing: much of this layout work is self-inflicted. If qkv wrote head-major output
directly (o / down already scatter dense), the rope gather disappears and `gather` only has to handle regular
layouts.
