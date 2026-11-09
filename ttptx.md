# bhir: a PTX-style IR for Blackhole kernels (minimal spec, draft 0)

One text module describes one program: the five instruction streams of a
Tensix core (BRISC, NCRISC, TRISC0/1/2) and the grid of cores that runs them.
The author writes RISC-V scalar code on virtual registers, Tensix instructions
by mnemonic, and bulk data movement between memory spaces. The compiler owns
encoding, register allocation, branch relaxation, per-core specialization, and
the sync rules in §10 that have exactly one correct form. Everything else
(engine choice, fidelity, tiling, buffer depth, Dst layout, MOP shape) is in
the source.

Names follow PTX where the meaning matches (`.entry`, `.shared`, `.param`,
`cp.async.bulk`, `commit_group`, `call`), Tensix mnemonics where they don't.

---

## 1. Module

```
.version 1.0                         // always
.target tt_30                        // grayskull / wormhole / blackhole generation; encodings differ
.grid   88                           // cores requested; the loader picks them, throws if the card has fewer

// declarations: visible to every entry
.param  .buffer W, X, OUT            // u32 DRAM addresses in the launch table
.param  .u32    token_pos
.spec   .u32    ROWS                 // per-core compile-time constant
.define IN      2                    // compile-time integer expression
.const  .b8     ones[128] = { 0x80, 0x3f, ... }   // uploaded once into L1
.shared .b8     token[IN * 2048]     // L1 arena, 16-byte aligned by default
.shared .align 16 .u32 sem[8]        // NoC atomics and inline writes need 16-byte alignment
.local  .u32    cursor               // this RISC's local RAM (0xFFB00xxx)
.cb     weight  .bf16 depth=2*IN     // circular buffer in L1
.cb     a_rows  page=P depth=2*M*BW  // page size in bytes for row-major landing buffers
.cb     partial .f32 depth=T alias=out   // same L1 as `out`: in-place accumulation (CB24/CB16)
.dst    .f32                         // Dst mode for the whole module
.dst    P   tiles=0      depth=1     // named Dst regions (optional, §10)
.dst    O   tiles=1..IN  resident

.mop    dot_mul    { ... }           // §8
.replay dot_acc    { ... }

.entry brisc  { ... }                // one per RISC; omitted roles return
.entry ncrisc { ... }
.entry trisc0 { ... }
.entry trisc1 { ... }
.entry trisc2 { ... }
.func  tile_offset (%i) -> (%r) { ... }
```

- Comments are `//`. One instruction per line, `;` optional.
- Destination operand first, PTX order.
- A module is compiled once per distinct `.spec` tuple. The host supplies the
  core list and one tuple per core; the loader launches the variant set. This
  replaces `ttko.shard.specialize`.
- Because every core runs the same module, every `.shared`, `.cb`, `.const`
  symbol has the same L1 address on every core. Remote operands (§6) rely on this.

### 1.1 Topology

`.grid N` asks for `N` worker cores. The loader chooses which physical cores
(harvesting, the dispatch cores, the DRAM-side split) and assigns each a
`%core_index` in `0..N-1`; the text never names a physical core except in
`on (x,y)` clauses, which should be rare. `.grid N spread` asks for cores spread
across the chip (what `runtime._allocate` does with `linspace`); `.grid N
rows=R cols=C` asks for a rectangle with logical `%ri`/`%ci` (`GridProgram`).
DRAM bank count, DRAM endpoints, and core count are runtime facts hidden from
the text; a module that needs more cores than the card has fails at load.

Core identity is available two ways, and the author picks per use:

- `.spec` values (`%core_index`, `%ri`, `%ci` as `.spec`): the compiler builds
  one variant per distinct value. Right when the code differs a lot per core
  (llama attention heads).
- `ld.grid %r, ri|ci|index`: a runtime load from the rank table the loader
  writes to L1. One image for the whole grid; role chosen by branch. Right for
  resident kernels launched many times (matmul_peak's sender/receiver split).

Derived sync must be correct on every runtime path, so a runtime role branch
costs nothing in the text but may cost conservative sync; `.spec` costs images.

### 1.2 Launch

A launch is a list of `(module, variant/spec values, core set, params)` tuples
run under one GO. One module may appear several times with different `.define`
or `.spec` values on disjoint core sets (matmul_peak's two row-band regions
with different plans). The loader writes the rank table, the topology tables
(§6.2), the param tables, and `.const` data, then releases all cores together.
There is no author-written prologue handshake (`release_triscs`); entries
start when the loader says so.

---

## 2. State spaces

| Space | Lives in | Declared by | Accessed by | PTX analog |
|---|---|---|---|---|
| `.global` | DRAM, host memory, other cores' L1 | `.param .buffer` | `cp.async.bulk` only (no scalar `ld.global`) | `.global` + `cp.async.bulk` |
| `.shared` | this core's L1 (`DATA_BUFFER_SPACE`) | `.shared`, `.cb`, `.const` | RISC `ld/st`, NoC, unpack, pack | `.shared` |
| `.shared::cluster` | another core's L1 | same symbols, `on (x,y)` | NoC only | distributed shared memory |
| `.local` | per-RISC local RAM | `.local` | RISC `ld/st` on that RISC only | `.local` |
| `.param` | launch param table (`PARAM_BASE`, 24 slots) | `.param` | `ld.param` | `.param` |
| `.const` | L1, written once at program load | `.const` | like `.shared`, read-only | `.const` |
| `.cb` | L1 ring + hardware counters at `CB_SYNC_*` + local state | `.cb` | `cb.*` | none (closest: `cp.async` groups + mbarrier) |
| `.dst` | Dst register file, 16-bit (16 tiles) or 32-bit (8 tiles) mode | `.dst` | FPU writes, SFPU ld/st, pack reads, unpack-to-dst | wgmma accumulator fragments |
| srca / srcb | FPU source banks, 2 hardware banks each | implicit | unpack writes, FPU reads | `ldmatrix` fragments |
| lregs | SFPU `l0..l7` + constants | implicit | SFPU ops | vector registers |
| cfg / thread-cfg | Tensix config (`0xFFEF0000`, SETC16 space) | implicit | `cfg.*`, `setc16` | none |

Tile dtypes: `.bf16 .f16 .f32 .fp8 .u32` (`ttko.DType`). Scalar types: `.u32 .s32 .b32`.
A tile is 1024 elements, four 16x16 faces, unless a tiny-tile mode is given.

---

## 3. Compile time

```
.spec   .u32 ROWS                    // per-core; compiler builds one variant per value
.define EMBED_TILES 2                // integer constexpr
.define SCALE  f32bits(1.0 / sqrt(64))   // float literals allowed inside builtins
.if FP8  ...  .else ... .endif        // folds on .define / .spec
.for t in 0..IN { ... }               // textual unroll, body may use t in immediates
```

Builtins: `f32bits(x)`, `bf16bits(x)`, `lo16(x)`, `hi16(x)`, `tile_off(i)`
(logical BF16 element → face-tiled byte offset), `dst_row(tile)` (`tile*64`),
`log2(n)`, `sizeof(dtype)`.

Loops are ordinarily real loops (§4 branches). `.for` exists only because a
replay or MOP body is recorded once and must be constant, and for tiny bodies
whose varying operand is a Tensix immediate that no hardware counter can step
(§5.2). The compiler never unrolls on its own.

---

## 4. Scalar code (RISC-V RV32IM)

Registers: `%r0, %r1, ...` virtual (allocated by liveness, no spills unless
`.func` convention requires them), `x0..x31` / ABI names physical and reserved
from allocation for that entry. `x0`, `ra`, `sp`, `gp` are never allocated.

| IR | Lowers to |
|---|---|
| `add sub mul divu remu sltu min and or xor sll srl sra` | same |
| `add %r, %r, imm` etc. | `addi` if it fits, else `li`+`add` |
| `li %r, imm32` | `addi` or `lui`+`addi` |
| `mv`, `nop` | `addi` |
| `ld.shared.{u32,u16,u8} %r, [sym + off]`, `ld.local`, `st.*` | `lw/lhu/lbu/sw/sh/sb` with the symbol's address materialized once per live range |
| `ld.param.u32 %r, NAME` | `lw` from `PARAM_BASE + slot*4` |
| `ld.spec %r, NAME` | `li` of the variant's constant |
| `beq bne blt bge bltu bgeu %a, %b, label` | branch, relaxed to inverse-branch + `jal` when out of range |
| `j label` | `jal x0` |
| `call fn, (%args) -> (%rets)`, `ret` | §9 |
| `fence` | `fence` |
| `mov.u32 %r, %core_x` / `%core_y` / `%core_index` | `.spec` values the loader fills |
| `ld.grid %r, ri \| ci \| index` | `lw` from the loader's rank table (runtime identity, §1.1) |
| `mov.u32 %r, %clock_lo` / `%clock_hi` | `lw` from `RISCV_DEBUG_REG_WALL_CLOCK_*` (PTX `%clock`) |
| `csrr %r, imm` | `csrrs rd, x0, csr` |

No `jalr` to a register, no stack frames unless a `.noinline` function needs one.

---

## 5. Tensix instructions

### 5.1 Form

```
mvmul   addr_mode=2, dst=64            // named fields, names from ttko/isa.py
setrwc  0, 0, 0, 0, 0, 15              // positional, isa.py order
sfpload l0, FP32, 7, 0                 // enum names allowed for enum-typed fields
.tt     0x37c00003                     // raw unrotated word
```

Issue path is per role and hidden: inline (rotated by two) on TRISC0/1/2,
`sw` to `INSTRN_BUF` on BRISC, rejected on NCRISC.

### 5.2 Register operands in Tensix fields

A Tensix word has no register operands. A field may still be a `%r`:

```
setadc  4, 0, 3, %tile                 // runtime Dst tile for the packer
```

The compiler lowers it by building the word in a GPR and pushing through
`INSTRN_BUF` (`li`, `or`, `sw`; what `Pack._destination` and `_load_scale`
do today). Not allowed inside `.mop` or `.replay` bodies. When the varying
field is an address counter, prefer the hardware increment instead
(`incrwc`, `setrwc`, `incadc*`, address modifiers): one word, one issue.

### 5.3 Address modifiers

```
addrmod 2, srca_clear, srcb_clear, dest_carry, fidelity_inc=1
addrmod 0, srca=8, srcb=8, dest=8
```
Lowers to the three `setc16` writes of `Fpu._set_addr_mod`.

---

## 6. Bulk data movement (NoC)

The NoC moves blocks between L1 and DRAM, host, or another core's L1. There is
no scalar `ld.global`. A global operand is always a **view of a `.param
.buffer`**; the text never contains a DRAM address, bank, NoC coordinate, NIU
index, or port.

```
cp.async.bulk.shared.global   [weight.wr + 2048], W.tile(%t)              // one tile of W -> L1
cp.async.bulk.shared.global   [token], X.tiles(0, IN)                     // IN consecutive tiles
cp.async.bulk.shared.global   [cos_l1], COS.row(%pos)                     // one row of a row-major buffer
cp.async.bulk.global.shared   OUT.tile(0), [compact]                      // L1 -> DRAM, non-posted
cp.async.bulk.global.shared.posted OUT.row(%pos).cols(%c, 16), [kv_row]   // 16 elements, posted
cp.async.bulk.cluster.shared  [partials + %i*16 on (0)], [local], 12      // L1 -> core 0's L1
cp.async.bulk.cluster.shared.multicast [rt on all], [rt], 24              // to every core of the launch
cp.async.inline.cluster       [flag on (0)], %value                       // 4-byte inline write
cp.async.bulk.host            HOST_OUT + %pos*16, [local], 16             // PCIe write
atom.cluster.inc.u32          [sem on (0)], 1                             // NoC atomic increment
cp.async.commit_group  %g                                                 // all copies since last commit -> %g
cp.async.wait_group    %g                                                 // source drained and responses received
cp.async.wait_source   %g                                                 // local read side only (write issued)
```

Views: `B.tile(i)`, `B.tiles(i, n)`, `B.row(r)`, `B.row(r).cols(c, n)`,
`B.rows(r, n).cols(c, w)` (a 2D box), `B.bytes(off, n)`; indices are constants
or `%r`. Byte counts come from the view. The L1 side is `[sym + off]`, `[%r]`,
or a strided landing `[%r : rows=32, pitch=P]` for 2D boxes (PTX
`cp.async.bulk.tensor` with a tensor map; matmul_peak's `input_row_pitch`
with its bank-spreading gap is a landing pitch, not kernel logic). Remote
cores are named by `%core_index`, `(x,y)`, a topology group (§6.2), or `all`.

- `%g` is a transaction group (PTX `cp.async` groups). The compiler maps
  groups to NoC transaction IDs 1..15 and inserts the issue-safe polls and
  command-buffer waits. Fields of the command buffer that do not change
  between consecutive copies are not rewritten (matmul_peak's stateful
  output writer is this, done by hand).
- `cp.async.*` is legal only in `brisc` and `ncrisc` entries.

### 6.1 Layout and routing are hidden (basic version)

Each `.param .buffer` is bound at launch to a **layout descriptor**, today's
`program.Buffer`: base address, dtype, shape, tiled or row-major element
order, bank count and DRAM endpoints, page size (`page_tiles`), global versus
per-core sharding. The compiler expands every view into the bank/page/offset
arithmetic and the endpoint coordinate (what `NoC._dram_tile` and
`_projection_read_weights` compute by hand). Kernels say *which* tiles, never
*where* they are.

Each entry is also bound to a **route**: which NIU (0 or 1), which DRAM port
per bank, and whether consecutive copies rotate ports. Today this is
`_projection_route`, `rotate_ports`, `noc_split_x`, and the per-core bank
rotation key. In this draft the route is a host-side object attached to the
launch, not text; its default is BRISC on NoC 0 and NCRISC on NoC 1 with
fixed ports. Later drafts may let the compiler choose routes, pre-assign
reader and writer roles per core, and fuse copies that the layout proves
contiguous within one bank. None of that changes the kernel text.

### 6.2 Topology groups

Multicast and collective targets are named by relation to this core, never by
coordinates:

```
cp.async.bulk.cluster.shared.multicast [a_rows.wr on row_peers], [a_rows.wr], BYTES   // every other core in my grid row
atom.cluster.inc.u32  [sem + 21*16 on row_leader], 1                                 // the ci == 0 core of my row
cp.async.bulk.cluster.shared.multicast [gate on wave(%w)], [gate], 16                // a loader-defined core set
```

Groups: `row_peers`, `col_peers`, `row_leader`, `col_leader`, `all`,
`rect(x0,y0,x1,y1)`, and `set(NAME)` for sets the launch defines (writer
waves). The loader resolves a group to one or more NoC rectangles, splitting
around harvested columns and the dispatch columns that multicast cannot cross
(matmul_peak's west/east rectangles in `args.py`), and writes the result to
a topology table in L1 that the lowered code reads. Receiver counts for
credit protocols come from the same table: `ld.topo %r, count(row_peers)`.

---

## 7. Circular buffers

```
.cb weight .bf16 depth=16            // index, L1 range, local state assigned by the compiler
cb.reserve  weight, 2                // producer: wait for 2 free tiles
cb.push     weight, 2                // producer: publish 2 tiles
cb.wait     weight, 1                // consumer: wait for 1 tile
cb.pop      weight, 1                // consumer: release
cb.ptr.wr   %r, weight               // current write pointer (L1 address)
cb.ptr.rd   %r, weight
cb.pop.tensix weight, 1              // publish the ack through the Tensix thread (after PACR)
```

Rules the compiler checks: each CB has exactly one producer role and one
consumer role; counts balance inside statically bounded loops; `cb.push` on
a TRISC2 producer is preceded by `stallwait pack0` + `sync` (the packer-drain rule).

---

## 8. Engines on the TRISCs

These are the Tensix mnemonics of §5 plus a few macros whose only job is to
hide addresses. Nothing here chooses an engine or a schedule for you.

```
// TRISC0
unpack.mode  0, in=.bf16, out=.bf16, target=srca, xdim=256, tilize=0, transpose=0   // ~20 cfg words (Unpack._write_mode)
unpack.base  0, %l1_addr                                 // THCON base registers from a runtime address
unpack.commit                                            // read-back + UNPACK_CONFIG_SYNC
unpacr ...                                               // the instruction itself, or a MOP that issues it

// TRISC1
setc16   DEST_TARGET_REG_CFG_MATH_Offset, dst_row(3)
mvmul / elwmul / elwadd / gapool / gmpool / mova2d / movd2b / zeroacc / setrwc / incrwc ...
sfpload l0, FP32, 7, 0  ;  sfpmad l0, ONE, l7, l7  ;  sfpstore ...
sfp.loadf  l7, 1e-5                                     // two SFPLOADI words
sfp.config.const CONFIG0, 1.4427                        // SFPCONFIG programmable constant
%v0, %v1 ...                                            // virtual lregs, allocated over l0..l7

// TRISC2
pack.mode   out=scalar_cb, fp32_dst=1, scalar=0          // Pack._configure
pack.dest   %tile, out=scalar_cb                         // Pack._destination (SETDMAREG/WRCFG path)
pacr ...
```

SFPU lregs may be virtual (`%v`) or physical (`l0..l7`); `ZERO ONE NEG_ONE
CONFIG0..2 LANE_X2` are the fixed names. The compiler inserts `sfpnop` for the
two-cycle result latency and after `sfpswap`; it does not reorder. A `%v`
used inside a `.replay` body is allocated before the body is recorded.

---

## 9. Functions

```
.func tile_offset (%i) -> (%r) { ... ret }
.func .noinline scatter_dense (%first, %count) { ... }   // large helper, real call
call tile_offset, (%idx) -> (%off)
```

- Default is inline (PTX semantics). `.noinline` emits a real call:
  `jal ra, fn` / `jalr x0, ra, 0`. The compiler never outlines on its own.
- Convention: arguments and results in virtual registers; `a0..a7`/`t*`
  caller-saved, `s0..s11` callee-saved; spills go to this RISC's `.local`
  slice and are reported.
- A non-inlined call invalidates the caller's MOP/SETC16 knowledge (§11) unless
  the callee has no Tensix effects.
- Functions are role-agnostic text; a function that contains Tensix words or
  `cp.async` can only be called from a role that may issue them.

---

## 10. Synchronization

Every edge where data crosses a space in §2 needs a sync. Edges with one
protocol are derived; the rest are authored. An explicit sync on an edge
suppresses derivation for that edge.

### 10.1 Explicit instructions

```
stallwait  math, srca_vld|srcb_vld        // TTSTALLWAIT; names from ttko.sync.Stall / Wait
semwait    MATH_PACK, on_max,  sync|math|sfpu
sempost    MATH_PACK
semget     MATH_PACK
seminit    MATH_PACK, max=1, init=0
sync                                       // PC_BUF_SYNC round trip
mop.sync                                   // PC_BUF_MOP_SYNC round trip
cfg.sync                                   // UNPACK_CONFIG_SYNC idle poll
wait.shared.{eq,ne,ge} [sym], %value       // spin on an L1 word (cross-core flags)
bar.core   trisc, %phase                   // same-core barrier across the three TRISCs (or `all` five RISCs):
                                           // engine drain + sync + phase word in L1 (prepare.barrier)
```

Any sync-bearing instruction takes `.async` to suppress derivation on its
edge: `cfg.st.async`, `unpack.base.async`, `setc16.async`. matmul_peak
double-buffers the unpacker's config contexts (`THCON_*_cntx1`,
`UNPACK_MISC_CFG_CfgContext` 0/257, `cfg.sync` only when the context is
busy) precisely to avoid the drain the compiler would insert; the author
owns that edge and says so.

### 10.2 Derived (compiler-inserted)

| Edge | Rule |
|---|---|
| `cp.async` → L1 read, or L1 reuse | `wait_group` on the owning group before the first read / overwrite |
| producer `cb.push` ↔ consumer `cb.wait` | nothing extra; the CB protocol is the sync |
| TRISC2 `pacr` → `cb.push` | `stallwait pack0` + `sync` before the RISC store |
| unpack → FPU through srca/srcb | hardware dvalid; the last FPU reader of a Src occupancy carries `clear_dvalid`; unary SrcA path releases both banks |
| FPU write Dst → SFPU read, and reverse (same TRISC) | `stallwait sfpu, math` / `stallwait math, sfpu` |
| SFPU result latency | `sfpnop` insertion (§8) |
| RISC `cfg.st`/`setc16` → engine use | `stallwait cfg, <engine>` drain; `unpack.commit` read-back |
| `.mop` / `.replay` reconfiguration | `mop.sync` before MOP_CFG writes; `sync` after replay load |

### 10.3 Authored (declare, or write by hand)

| Edge | Why |
|---|---|
| Dst between math and pack | four protocols in llama alone: full handoff, retained tiles with partial pack, FPU/SFPU shared tile with live lregs, unpack-to-dst. Declare `.dst` regions with `depth=` and the compiler emits one `MATH_PACK`-style semaphore per region (8 semaphores, SEMPOST max 15: running out is an error). Or write `semwait/sempost` yourself. |
| Cross-core flags | data write must be non-posted before the flag write; use `wait.shared` on the reader |
| Anything through `.tt` raw words | declare reads/writes with `.effects` or accept no derivation |

---

## 11. MOP and replay

```
.mop dot_mul {
  outer 2 ; inner 2
  loop       elwmul 0, 0, 0, 0, 0
  last       elwmul 3, 0, 0, 3, 0           // LoopTemplate slot names
  outer_last elwmul 0, 0, 0, 2, 0
}
.mop reduce .mask { a0 unpacr_nop ... ; a1 unpacr 0 ; b unpacr 1 ; skip_a0 nop }   // MaskTemplate
.replay dot_acc { sfpload l0, FP32, 7, 0 ; sfpmad l0, ONE, l7, l7 ; incrwc 0, 2, 0, 0 }

mop.cfg  dot_mul            // write the MOP_CFG words that differ from the last known state
mop.run  dot_mul            // TTMOP (type 1), or mop.run reduce, count=4, mask=0 for mask templates
replay   dot_acc            // TTREPLAY start,len
```

- Replay slots (32 per TRISC) are allocated per module; TRISC1 shares them
  between FPU and SFPU uses. `.replay ... slot=16` pins.
- Bodies are constant: no `%r`, no `%v` that isn't already allocated.
- MOP_CFG and SETC16 elision is a dataflow pass over the control-flow graph
  (not reset at every label as `Asm.mop_words` is today). Labels, calls, and
  `.tt` words are the only things that make the state unknown.

---

## 12. Config

```
cfg.st   THCON_SEC0_REG3_Base_address, %r      // sw to 0xFFEF0000 + index*4; names from ttko.registers.Cfg
cfg.st   UNPACK0_TILE_DESCRIPTOR, 0x15
cfg.rmw  ALU.byte3, mask=0x20, 0x20            // RMWCIB0..3
setc16   ADDR_MOD_AB_SEC2_Src, 8               // thread-cfg, immediate only
gpr.st   PACK_DEST_OFFSET_LO, 0                // Tensix GPR file (0xFFE00000)
```

---

## 13. What the compiler does and does not do

Does: encode; allocate `%r`, `%v`, transaction groups, replay slots, CB
indices, L1/local addresses; relax branches; specialize per `.spec`; expand
buffer views through the layout descriptor and route (§6.1); insert the §10.2
syncs; elide redundant MOP/SETC16 writes; insert `sfpnop`; merge copies the
layout proves contiguous within one bank and share one wait per group; inline
functions.

Does not: choose engines, fidelity, Dst layout, buffer depth, or MOP shape;
unroll; reorder instructions; move work between RISCs; invent Dst handoffs.

---

## 14. Example: `o` projection (y = W @ x, one row at a time)

```
.version 1.0
.target tt_30
.grid   88 spread
.param  .buffer W, X, OUT
.param  .u32    row_start
.spec   .u32    ROWS
.define IN 2
.cb     weight  .bf16 depth=2*IN
.cb     scalar  .bf16 depth=2
.shared .b8     token[IN*2048]
.dst    .f32
.mop    dot_mul { outer 2 ; inner 2 ; loop elwmul 0,0,0,0,0 ; last elwmul 3,0,0,3,0 ; outer_last elwmul 0,0,0,2,0 }
.replay dot_acc { sfpload l0, FP32, 7, 0 ; sfpmad l0, ONE, l7, l7 ; incrwc 0, 2, 0, 0 }

.entry brisc {
  cp.async.bulk.shared.global [token], X.tiles(0, IN)
  cp.async.commit_group %g0
  cp.async.wait_group   %g0
  ld.param.u32 %row0, row_start
  li %i, 0
loop:
  bgeu %i, ROWS, done
  add  %src, %row0, %i
  mul  %first, %src, IN
  cb.reserve weight, IN
  cb.ptr.wr %wr, weight
  cp.async.bulk.shared.global [%wr], W.tiles(%first, IN)   // layout + route expand this
  cp.async.commit_group %g1
  cp.async.wait_group   %g1
  cb.push weight, IN
  add %i, %i, 1
  j loop
done:
}

.entry trisc0 {
  unpack.mode 0, in=.bf16, out=.bf16, target=srca, xdim=256
  unpack.mode 1, in=.bf16, out=.bf16, target=srcb, xdim=256
  mop.cfg pair
  li %i, 0
loop:
  bgeu %i, ROWS, done
  .for t in 0..IN {
    cb.wait weight, 1
    cb.ptr.rd %rd, weight
    unpack.base 0, %rd
    unpack.base 1, token + t*2048
    unpack.commit
    stallwait unpack, srca_clr|srcb_clr
    setadcxx 1, 255, 0 ; setadcxx 2, 255, 0 ; setadczw 3, 0,0,0,0, 15
    mop.run pair
    cb.pop weight, 1
  }
  add %i, %i, 1
  j loop
done:
}

.entry trisc1 {
  addrmod 0, srca=8, srcb=8, dest=8
  addrmod 2, srca_clear, srcb_clear, dest_carry, fidelity_inc=1
  addrmod 3, srca_clear, srcb_clear, dest=8, dest_carry_to_carry, fidelity_clear
  mop.cfg dot_mul
  li %i, 0
loop:
  bgeu %i, ROWS, done
  semwait MATH_PACK, on_max, sync|math|sfpu          // authored Dst handoff
  sfp.loadf l7, 0.0
  .for t in 0..IN {
    .for f in 0..4 { zeroacc 1, 1, 0, 1, f }
    setrwc 0,0,0,0,0,15
    stallwait math, srca_vld|srcb_vld
    mop.run dot_mul ; mop.run dot_mul ; mop.run dot_mul ; mop.run dot_mul
    .for f in 0..4 {                                  // SFPU: l7 += Dst[0], 8 rows per face
      replay dot_acc ; replay dot_acc ; replay dot_acc ; replay dot_acc
      replay dot_acc ; replay dot_acc ; replay dot_acc ; replay dot_acc
      setrwc 0, 4, 8, 0, 0, 4 ; setrwc 0, 4, 8, 0, 0, 4
    }
    setrwc 0, 0, 0, 0, 0, 4
  }
  call lane_sum, (l7) -> (l0)                         // std-lib: butterfly + transpose
  sfpstore l0, FP32, 7, 0
  sempost MATH_PACK
  add %i, %i, 1
  j loop
done:
}

.entry trisc2 {
  pack.mode out=scalar, fp32_dst=1, scalar=1
  li %i, 0
loop:
  bgeu %i, ROWS, done
  semwait MATH_PACK, on_zero, tdma
  cb.reserve scalar, 1
  pack.dest 0, out=scalar
  setadcxx 4, 15, 0 ; setadczw 4, 0,0,0,0, 5
  mop.run pack
  cb.push scalar, 1                                   // compiler adds stallwait pack0 + sync
  zeroacc 3, 1, 0, 1, 0
  semget MATH_PACK
  add %i, %i, 1
  j loop
done:
}

.entry ncrisc {
  li %i, 0
loop:
  bgeu %i, ROWS, done
  cb.wait scalar, 1
  cb.ptr.rd %rd, scalar
  ld.shared.u16 %val, [%rd]
  call tile_offset, (%i) -> (%off)
  st.shared.u16 [compact + %off], %val
  cb.pop scalar, 1
  add %i, %i, 1
  j loop
done:
  cp.async.bulk.global.shared OUT.tile(0), [compact]
  cp.async.commit_group %g ; cp.async.wait_group %g
}
```

The inserted syncs in this example are the `wait_group`s the author wrote
anyway, the packer drain before `cb.push`, `stallwait sfpu, math` between the
last `mop.run dot_mul` and the first `replay dot_acc`, and `sfpnop`s inside the
SFPU sequences. The Dst handoff is authored with `semwait`/`sempost`.

---

## 15. Stress test: matmul_peak in one module

`examples/matmul_peak_kernel` is the most complex kernel in the repo: one
resident image on a core rectangle, role by grid rank, A rows multicast along
rows by BRISC on NoC 0, B columns multicast down columns by NCRISC on NoC 1,
credit semaphores through NoC atomics, in-place FP32 L1 accumulation across
K blocks, double-buffered Dst and double-buffered unpack config contexts,
runtime MOP counts for edge tiles with `jal`-called fringe subroutines, a
tilize phase with a three-TRISC barrier, an untilizing epilogue with its own
semaphores and Dst remap, writer waves gated by a coordinator, optional N
passes with manual register spills, two row-band regions launched together.
Every piece maps; the right column says what the spec needed.

| matmul_peak | bhir | Added for it |
|---|---|---|
| one image, `GRID_RANK_BASE` branch for sender/receiver | `ld.grid %r, ci` + branch, or `.spec` variants | §1.1 runtime identity |
| two regions with different plans under one GO | launch list of (module, defines, cores, params) | §1.2 |
| `emit_args`: per-core scratch tables from rank + topology | scalar code at entry start, duplicated per RISC | none |
| CB interface tables written in every prologue | generated from `.cb` | none |
| CB24 aliases CB16, CB17 aliases CB16 | `.cb ... alias=` | §2 |
| row-major A/B landing with `input_row_pitch`, odd-width header | 2D view + `[dst : rows, pitch]` landing | §6 |
| 8-bank unrolled fast reader, `DRAM_BANK_TO_NOC_XY` table | layout descriptor expansion | §6.1 (already) |
| west/east multicast rectangles around the dispatch column | `on row_peers`, loader splits | §6.2 |
| receiver credit: `atom inc` on sender's `sem[21]`, sender waits `== count` | `atom.cluster.inc [sem on row_leader]`, `wait.shared.eq`, `ld.topo count(row_peers)` | §6.2 |
| `noc_semaphore_set_multicast` valid flag | `cp.async.bulk.cluster.shared.multicast [sem on row_peers], [sem], 16` | none |
| writer waves: DONE counter + GATE multicast | `atom.cluster.inc`, `wait.shared.ge`, `on set(wave)` | §6.2 |
| output NoC chosen at runtime by column parity | route object, 2 variants or runtime table | §6.1 |
| stateful NoC command buffer reuse | compiler keeps unchanged command fields | §6 |
| `SEMINIT MATH_PACK max=2`, `dest_offset_id` flip, runtime `SETC16 DEST offset`, `ZEROACC` with parity bit | authored Dst protocol; `%r` in Tensix fields | §5.2, §10.3 |
| `SETDMAREG`/`WRCFG` pack destination from a register | `pack.dest %r` or raw `gpr.st` + `wrcfg` | §8, §12 |
| unpack config context ping-pong, `PC_UNPACK_SYNC` poll | `cfg.st.async`, `setc16.async`, `cfg.sync` | §10 `.async` |
| `RDCFG`/`ADDDMAREG`/`WRCFG` inside a replay to auto-advance unpack base | raw Tensix in `.replay` | none |
| `TTMOP(1, 0, k<<10 \| n)` runtime counts, `TTMOP(0, n, 0xFF)` | raw `mop` word; `.mop` only for the template | none |
| `edge_<m>_<n>_<k>` subroutines via `jal ra` | `.func .noinline` on trisc1 | §9 (already) |
| `prepare.barrier` across TRISC0/1/2 | `bar.core trisc, %phase` | §10 |
| tilize: Dst remap `DEST_ACCESS_CFG`, swizzle, remapped pack | `cfg.st` by name; needs the full register name table | §12 (names) |
| epilogue `EPILOGUE_SEM` / `PACK_IDLE_SEM` | explicit `semwait`/`sempost` | none |
| `emit_overlap_output` saving S0..S11,GP to L1 around a nested writer | `.func .noinline` with callee-saved spills | §9 (already) |
| profile stamps from the wall clock, CSR fusion check | `%clock_lo/hi`, `csrr` | §4 |
| `PROFILE_LEVEL`, `ENABLE_BREADCRUMBS`, `FP8` variants | `.define` + `.if` | §3 (already) |
| `release_triscs`, `init_barrier`, `wait8` on start bytes | loader releases all RISCs; not in text | §1.2 |

Two conclusions. First, the explicit tier needs no new *instructions* for
matmul_peak; what it needed were declarations (alias, 2D landing, topology
groups, runtime identity) and one escape (`.async`). Second, the kernel is
built on the hidden objects: of its roughly 2800 lines, the DRAM bank
arithmetic, rectangle computation, CB table setup, and NoC command-buffer
plumbing that disappear into layout, route, topology, and `.cb` are the
largest single share.

---

## Appendix: ttko → bhir

| ttko | bhir |
|---|---|
| `Asm.reg()` / `VReg` | `%r` |
| `Asm.li / mv / read / write` | `li / mv / ld.* / st.*` |
| `Asm.loop(Cond)`, `range`, `break_` | labels + branches |
| `Asm.label(local=True)` | plain label (elision is CFG-based) |
| `Program(cores, *params)` | `.param`, `.spec`, host core list |
| `Const(name, tuple)` | `.spec` (compile-time) or `.param` (runtime) |
| `p.cb(dtype, depth)` | `.cb` |
| `p.l1(size)` / `p.l1_constant(bytes)` | `.shared` / `.const` |
| `Asm.local.alloc` | `.local` |
| `Dst(fp32)` | `.dst .f32` |
| `CB.reserve_back / push_back / wait_front / pop_front / get_*_ptr` | `cb.reserve / push / wait / pop / ptr.*` |
| `NoC.transaction()` + `read/write/multicast_write/inline_write/atomic_inc` | `cp.async.bulk.*`, `cp.async.inline`, `atom.cluster.inc`, `commit_group / wait_group` |
| `NoC._dram_tile`, `_projection_read_weights` bank rotation, `PagedProjectionWeight` | buffer views (`B.tile(i)`, `B.row(r)`) + layout descriptor; not in the text |
| `_projection_route`, `rotate_ports`, `noc_split_x`, `noc_at(index, port)` | route object bound at launch; not in the text |
| `TT.TTxxx(fields)` | `xxx fields` |
| `push_tensix(reg)` | a `%r` in a Tensix field |
| `Mop.configure(LoopTemplate)` / `MaskTemplate` / `run` | `.mop { }`, `mop.cfg`, `mop.run` |
| `Replay`, `ReplayBuffer.allocate`, `Mop.load` | `.replay { }`, `replay` |
| `stall / sem_wait / sem_post / sem_get / sync / mop_sync` | `stallwait / semwait / sempost / semget / sync / mop.sync` |
| `Fpu._set_addr_mod` | `addrmod` |
| `Fpu._configure_dst` | `setc16 DEST_TARGET_REG_CFG_MATH_Offset` + `cfg.rmw ALU.byte3` |
| `Unpack._write_mode / _write_base / _commit_config` | `unpack.mode / unpack.base / unpack.commit` |
| `Pack._configure / _destination` | `pack.mode / pack.dest` |
| `SfpuProgramBuilder.vec()` | `%v` |
| `_sfpu_float_words` | `sfp.loadf` |
| `sfpu.exp / reciprocal / rsqrt`, `_round_fp8_program`, lane reductions | std-lib `.func`s written in bhir |
| `specialize(build, cores, keys)` | one module, `.spec`, variant set |
| `Fpu.matmul / binary / copy_a_tiles`, `Unpack.move_*`, `Pack.move*` | not primitives: std-lib `.func`s composed from the above |
