# ttptx isa

The instruction list. Goals and concepts are in `ttptx.md`; the reasoning behind the shape of things is in
`ttptx_brainstorm.md`. Where those two disagree with this file, this file wins.

Each instruction is a thin layer over one Blackhole instruction (or a short fixed sequence). The layer takes away
three things and nothing else:

- **configuration**: formats, address modifiers, `ThreadConfig`, unpacker / packer descriptors, MOP config words,
  `LoadMacroConfig`. You never write a config register; the assembler derives the config each instruction needs
  and writes only the parts that changed (state trackers in `ttptx.md`).
- **raw addresses and counters**: you name a register (a dst tile, an l1 tile, srcA) and a row; the assembler turns
  that into `DstRow` + `RWC` + `DEST_TARGET_REG_CFG_MATH_Offset`, L1 base addresses, and so on.
- **synchronisation between the five riscs**: semaphores, `STALLWAIT`, cb counters, dvalid handshakes, noc
  acks. It is all inferred from which register each instruction reads and writes.

It never hides work. A 32x32 tile multiply that takes 32 `MVMUL`s is written as 32 `mma`s, or as one `mma.tile`,
which is listed as a pseudo-instruction that expands to exactly those 32.

Status: draft. Items marked **verify** are hardware behaviour I have not confirmed on Blackhole.

---

## 1. reading this document

```
op.mod1.mod2   dst, src0, src1   {counter increments}
```

- operand class decides the unit. `add.f32 %v0, %v1, %v2` is an SFPU add (lregs), `add %d0[0], %a[0], %b[0]`
  is an FPU add (dst / srcA / srcB), `add.u32 %r0, %r1, %r2` is a risc-v add. The tables are grouped by unit.
- **lowers to** names the hardware instruction(s), so you can read cost off the page.
- **unit / risc**: which risc ends up issuing it. You never write this; it is listed so you know where the cost
  lands. `brisc` = noc reads, `ncrisc` = noc writes, `t0` = unpack thread, `t1` = math thread (FPU + SFPU),
  `t2` = pack thread. Scalar ops are replicated onto whichever riscs need their result.
- `imm` is an assembler constant expression. `%r` is a scalar register, `%v` an SFPU register, `%d` a dst tile,
  `%t` an l1 tile register, `%a` / `%b` srcA / srcB.

---

## 2. program structure

### 2.1 directives

| directive | what it does | notes |
| --- | --- | --- |
| `.version 0` | isa version | first line |
| `.target blackhole` | target | `.target blackhole.p150a` pins the core grid (140 cores) |
| `.include "file"` | textual include | for shared `.func`s, e.g. `ttptx/std.ttptx` |
| `.define NAME expr` | assembler constant | integer or float. Usable anywhere an `imm` is, including register counts (`%x<TILES>`) and loop bounds |
| `.dst .b32` / `.dst .b16` | how the kernel views dst | `.b32`: 8 tiles of fp32 / int32. `.b16`: 16 tiles of bf16 / fp16 / int8. One view per kernel (tracker 1). Mixing views per tile is an open question (section 13) |
| `.visible .entry name (params) .cores N` | kernel entry point | `.cores N`, `.cores (x0,y0)-(x1,y1)`, or `.cores list(...)`. The assembler emits the manifest entry |
| `.func (rets) name (args) { }` | function | called with `call`. Args and returns are typed registers of any class. Calls are closed-world: the assembler clones a function per distinct incoming state (ttptx.md, "how tracking works") |
| `.param .dram name` | uniform launch arg: an interleaved dram buffer | addressed as `[name + byte_offset]`. Bank interleave and page size come from the buffer's runtime metadata, never from your code |
| `.param .u32 name` | uniform scalar launch arg | read with `ld.param.u32` or used directly as an operand |
| `.param::core .u32 name` | per-core scalar arg | value differs per core. Lands in the per-core table (`0xe8c0..`) |
| `.const .b8 name[N] = {...}` | read-only data in the kernel image | |
| `.l1 .b8 name[N]` (`.align A`) | raw addressable l1 on this core | for scalar data you ld/st by byte offset, scratch and flags. Tiles you compute on should be `.tile` registers (2.2) instead |
| `.reg <class> %name` / `%name<N>` | declare virtual registers | `%x<4>` declares `%x0..%x3`, also indexable as `%x[i]`. Classes are in 2.2 |
| `.replay`, `.mop`, `.sfpmacro` | define a template | section 10 |

### 2.2 register classes

| class | physical | count | notes |
| --- | --- | --- | --- |
| `.u32` `.s32` `.b32` | risc-v x-regs | virtual | scalar. 32-bit only: there is no `.u64` and no `.f32` scalar (the riscs have no fpu) |
| `.pred` | risc-v x-reg holding 0 / 1 | virtual | scalar predicate, for `@%p` and `if` |
| `.tile.<fmt>` (`.depth N`) | l1, allocator-managed | l1 size | one tile: 1024 datums in storage format `<fmt>`. The compiler infers from def/use whether it is a fifo or a latch and inserts the cb on every cross-risc edge (brainstorm section 2). `.depth N`: how many iterations the producer may run ahead (default 2 in a loop, 1 outside) |
| `.dst` | `Dst` | 8 (`.b32`) / 16 (`.b16`) | one tile = 64 dst rows of 16 datums (4 faces of 16 rows) |
| `%a`, `%b` | `SrcA`, `SrcB` | 1 each (fixed names) | 64 rows x 16 of 19-bit. Double-banked in hardware; the bank flip is part of `unpack` / `release` |
| `.v` | `LReg[0..7]` | 8, minus pinned | SFPU vector: 32 lanes of 32 bits. Type comes from the instruction suffix (`.f32` `.s32` `.u32` `.sm32`) |
| `.vconst` | `LReg[11..14]` | 4 | per-row constants (8 values broadcast to 4 rows). Written only by `mov.vconst` |
| `%vzero` `%vone` `%vlane` `%v8373` | `LReg[9]` `LReg[10]` `LReg[15]` `LReg[8]` | fixed | read-only: 0, 1.0, `2*lane`, 0.8373 |
| `%vm` | `LReg[16]` | fixed | written only by ops inside an `.sfpmacro`, read only by a macro's store |
| `.sreg` | none | | read-only scalars: `%core.x` `%core.y` `%core.idx` `%ncores` |

Storage formats (`<fmt>`) for `.tile`, plus the size of one tile in l1:

| fmt | bytes / tile | unpacks to | notes |
| --- | ---: | --- | --- |
| `fp32` | 4096 | tf32 in src (mantissa truncated), fp32 in dst | |
| `bf16` | 2048 | bf16 | |
| `fp16` | 2048 | fp16 | |
| `fp8` | 1024 | fp16 (e5m2, lossless) | what the 8B fp8 kernels call e4m3 needs checking against this, **verify** |
| `bfp8` `bfp4` `bfp2` | 1088 / 576 / 320 | bf16 (lossless) | shared exponent per 16 datums. Sizes assume 64 exponent bytes / tile |
| `int8` `int32` | 1024 / 4096 | int "8" / int "32" (sign-magnitude) | |
| `u16` `u32` `u8` | 2048 / 4096 / 1024 | opaque bits | token ids, indices |

A `.tile` holds 1024 datums. Whether they form a 32x32 tilized tile or 1024 consecutive elements of a vector is a
property of the data, not of the register. Elementwise code does not care; `mma` does.

### 2.3 dst tile layout and addressing

A dst tile is 64 rows of 16 datums. In a 32x32 tilized tile, face `f` (0 top-left, 1 top-right, 2 bottom-left,
3 bottom-right) is rows `16f .. 16f+15`.

| operand | means | used by |
| --- | --- | --- |
| `%d0[r]` | row `r` (0..63) of tile `%d0` | FPU, pack |
| `%d0.v[i]` | SFPU vector `i` (0..31) of tile `%d0`: rows `4*(i>>1) .. +3`, columns `(i&1), (i&1)+2, .., (i&1)+14`. Lane `l` is row `+ l/8`, column `(i&1) + 2*(l%8)` | SFPU `ld` / `st` / `vmacro` |
| `%dx[%r]` | tile chosen at runtime from a register array | anywhere a tile goes; lowers to a runtime-built `SETC16` word (the risc writes the instruction word), about 3 risc-v instructions |
| `%d0.v[%r]` | runtime vector index | same mechanism. Inside a loop that only steps `%r` by 1, the assembler uses an `RWC` increment instead (free) |
| `%a[r]`, `%b[r]` | row `r` (0..63) of srcA / srcB | FPU |

Every FPU / SFPU address is `imm + counter` (section 10.1). Counters are zero unless you change them, so outside
templates `%d0[8]` simply means row 8.

---

## 3. scalar (risc-v)

Integer only, 32-bit. Same shape as ptx. Census (`ttptx/census.md`): llama3 uses `add sub and or xor sll srl mul
divu` and compare/branch. Everything else in rv32 (csr, `amo*` on local memory, `fence`, `lui` / `auipc`) is
either compiler-only or covered by an instruction below.

| instruction | what it does | operands / notes |
| --- | --- | --- |
| `mov.b32 %r, a` | copy / load immediate | `a` is a reg, imm, `.param`, `.sreg`, or `.l1` / `.const` symbol address. Imm loads become `lui` + `addi` as needed |
| `add` `sub` `.u32/.s32` | `d = a ± b` | `b` may be an imm |
| `mul.lo.u32` | low 32 bits of `a*b` | rv `mul` |
| `mul.hi.u32` / `.s32` | high 32 bits | rv `mulhu` / `mulh` |
| `mad.lo.u32 d, a, b, c` | `d = a*b + c` | two instructions |
| `div` `rem` `.u32/.s32` | division | rv `divu/div/remu/rem`. Slow (multi-cycle). Division by an imm power of two becomes a shift |
| `and` `or` `xor` `not` `.b32` | bitwise | |
| `shl.b32` `shr.u32` `shr.s32` | shifts | by reg or imm |
| `min` `max` `.u32/.s32` | | Zbb `min/max` if present, else compare + branch, **verify** |
| `neg.s32` `abs.s32` | | |
| `setp.<cmp>.<type> %p, a, b` | `%p = a cmp b` | cmp: `eq ne lt le gt ge`; type `.u32` / `.s32` |
| `selp.b32 d, a, b, %p` | `d = %p ? a : b` | |
| `ld.<space>.<t> %r, [addr]` | scalar load | space: `.l1` (a `.l1` symbol or a `.tile` register as base), `.param`, `.const`, `.local`. t: `.u8 .s8 .u16 .s16 .u32`. Loading from a `.tile` waits for that tile to be produced (inferred) |
| `st.<space>.<t> [addr], %r` | scalar store | `.l1` / `.local` / `.tile`. A store into a `.tile` makes this risc a producer of it |

Address syntax: `[base + %r + imm]`, byte offsets. `base` is a symbol, a `.tile` register, or a `.param .dram`
(dram only via `cp.async`, not `ld`).

---

## 4. control flow

Structured only, no `bra`. Every risc gets its own copy of every loop and `if`, and loop distribution needs the
structure. A condition must be computable on every risc that has work inside it: a function of params,
induction variables, `.sreg`, or a scalar the compiler can send across (that costs a channel, see
brainstorm section 2, "catches").

| instruction | what it does | notes |
| --- | --- | --- |
| `loop %i = a, b[, s] { }` | `for (i = a; i < b; i += s)` | a / b / s: reg or imm. `.unroll N` after the header unrolls by N |
| `if %p { } else { }` | scalar conditional | `@!%p` style negation via `if !%p` |
| `@%p op ...` | guard a single scalar or noc instruction | not allowed on coprocessor instructions: use `if`. SFPU per-lane conditions are `vif` (section 8.7) |
| `call (rets), fn, (args)` | call a `.func` | lowers to `jal` per risc that has work in `fn` |
| `ret` | return | |
| `exit` | end of kernel on this core | all outstanding noc writes are waited for (`.landed`) first |

---

## 5. noc (data movement between cores and dram)

Reads are issued by brisc and writes by ncrisc. The compiler places them there, coalesces adjacent pages, and
tracks every transaction. Each transfer has one completion point for reads (the data is in l1, which the compiler
waits for before the first use) and two for writes (departed: the source can be reused; landed: the data is
visible at the destination).

| instruction | what it does | operands / notes |
| --- | --- | --- |
| `cp.async %t, [src + off]` | copy one tile into l1 tile register `%t` | src: `.param .dram` or a remote l1 ref. Size = tile size of `%t`'s format. The consumer of `%t` waits for it to land |
| `cp.async %t, [src + off], n` | copy `n` bytes | partial tile (an embedding row, a compact vector). `n` reg or imm; 16-byte aligned at both ends (noc rule) |
| `cp.async [dst + off], %t[, n]` | write a tile / `n` bytes from l1 to dram or remote l1 | completes "departed" before `%t` is overwritten (inferred) |
| `cp.async.mcast [%t @ rect], %t` | write one tile to the same register on every core in `rect` | `rect` = `(x0,y0)-(x1,y1)`. The destination cores must run this kernel, so `%t` sits at the same l1 address on every one of them. Each receiver's cb credit is handled by the compiler (receiver counts landed tiles) |
| `cp.async.wait.landed` / `.departed` | wait for all outstanding writes from this core | needed only when ordering goes through memory rather than a register: e.g. append to the kv cache in dram, then read it back. Register-carried dependencies never need it |
| `cp.l1 %t1, %t0[, n]` | l1 to l1 copy on this core | lowers to `XMOV` (async, 16-byte units). Census: unused today. Candidate for the compact scatter / gather loops on ncrisc |

Remote references: `[%t @ core(x, y)]` (another core's copy of tile register `%t`) and `[sym @ core(x, y)]` (an
`.l1` symbol on another core). This is ptx's `mapa`. `x, y` may be registers.

### 5.1 atomics and cross-core sync

| instruction | what it does | operands / notes |
| --- | --- | --- |
| `atom.<op>.u32 %old, [ref], v` | remote l1 atomic, returns the old value | op: `add xor or and min max minu maxu`. noc "Zaamo" request. `%old` lands in this core's l1; reading it waits (inferred) |
| `atom.cas.u32 %old, [ref], cmp, v` | compare and swap | noc atomic CAS |
| `atom.exch.u32 %old, [ref], v` | swap | |
| `atom.inc.u32 %old, [ref], v, wrap` | increment with wrap | noc atomic increment |
| `red.add.<t> [ref], v` | fire-and-forget parallel add on 16 bytes | `<t>`: `f32` (4 lanes), `bf16` / `fp16` (8 lanes), `u32` (wrap), `u8.sat`. `v` is 4 bytes broadcast across the 16. **Floats work**: this is the tree-reduction primitive `ttptx.md` asked about. denormals flush to zero |
| `wait.<cmp>.u32 [sym], v` | spin until an l1 word on this core satisfies `cmp v` | for flags and counters set by other cores' atomics. Lowers to a load-and-branch loop on whichever risc needs it |
| `bar.grid name, count` | all `count` cores reach this point | pseudo: `atom.add` to a counter on core 0, `wait.ge`, then a multicast release. Listed so kernels don't each reinvent it |

---

## 6. unpack (l1 tile to srcA / srcB / dst) — thread t0

Unpacker 0 writes srcA or dst, unpacker 1 writes srcB. The input format is `%t`'s format; the output format
follows from it (2.2 table) unless you override it with `.as`. Tracker 6 records which format sits in each of
srcA and srcB.

| instruction | what it does | operands / notes |
| --- | --- | --- |
| `unpack %a, %t` | whole tile into srcA, then hand srcA to the FPU | `UNPACR` x4 faces (via the unpack MOP the assembler builds), then set dvalid. The FPU waits on srcA valid (inferred) |
| `unpack %b, %t` | whole tile into srcB | unpacker 1 |
| `unpack %d0, %t` | whole tile straight into dst | unpacker 0 to dst. The assembler inserts the `UNPACR`-to-srcA workaround for the `WroteDst` hardware bug (SrcASrcB.md) before srcA is next handed to the FPU |
| `.t` | transpose the 32x32 tile (x/y swap) | srcA only (hardware). For a transposed srcB use `transpose %b` (FPU) |
| `.as.<fmt>` | override the output format | e.g. `unpack.as.tf32 %a, %t` for fp32 input |
| `.rows n` | unpack only the first `n` rows (of 16 datums) | partial tiles, vectors shorter than 1024 |
| `.keep` | don't hand the bank over yet | follow with more `unpack.face` or with `give` |
| `unpack.face %a[r], %t[f] {in+=1, out+=16}` | one 16x16 face from face `f` of `%t` into rows `r..r+15` | the template-level form. `in` / `out` are the unpacker ADC channels 0 / 1 (`Y`/`Z` increments in the `UNPACR` instruction bits). **verify** which increments are legal per channel |
| `give %a` / `give %b` | hand the bank to the FPU without unpacking | `UNPACR_NOP` (set-dvalid). Sequenced with unpacks |
| `unpack.zero %a` / `%b` (`.half`) | zero the unpacker-side bank, sequenced with unpacks | `UNPACR_NOP` (zerosrc). On BH can also give srcA in the same instruction (avoids the `WroteDst` bug) |

Census: every unpack in the shipped kernels goes through a MOP (137 `UNPACR` inside templates, 12 in the stream).
That is why the whole-tile form exists.

---

## 7. FPU (matrix unit) — thread t1

Hardware granularity is an 8x16 block (`mma`, elementwise) or one / four / eight rows (moves). Alignment: row
operands must be multiples of 8 for 8-row ops, 4 for 4-row ops.

Fidelity: one hardware instruction does one fidelity phase (A: implicit bit + 4 mantissa bits, B: implicit bit +
6 mantissa bits per phase). `.pN` on an FPU instruction outside a template means "do phases 0..N-1": the
assembler emits N copies with the phase counter stepped. Inside a template you get exactly one phase, the
counter's, and step it yourself with `{f+=1}`. The default and the minimum come from the formats in src
(tracker 6), from SrcASrcB.md:

| src format | minimum (`.lossy` to go below) | full precision |
| --- | --- | --- |
| fp8, bfp4, bfp2 | 1 | 1 |
| bfp8 | 1 | 2 |
| bf16 | 2 | 4 |
| tf32, fp16 | 4 | not possible in srcA |

Release: an op with `.ra` / `.rb` / `.rab` gives srcA / srcB / both back to the unpacker after it executes
(`FlipSrcA/B` bits). Outside templates the assembler puts the release on the last reader. Inside templates you
write it.

| instruction | what it does | operands / notes |
| --- | --- | --- |
| `mma %d[r], %b[rb], %a[ra]` | `D[8x16] += B[8x16] @ A[16x16]` | `MVMUL`. bf16/tf32 x bf16/tf32 into fp32/bf16; fp16 into fp32/fp16; int8 into int32. A's lsb mantissa is ignored. Undefined dst rows read as zero, so `zero` + `mma` = assign |
| `mma.bcast %d[r], %b[rb], %a[ra]` | B row broadcast | odd hardware semantics: only rows `r`, `r+4` or `r+6` of the result are meaningful (MVMUL.md). Use for 1-row x tile (decode matvec) |
| `mma.m4 %d[r], %b[rb], %a[ra]` | `D[4x16] += B[4x16] @ A[16x16]` | `GAPOOL`. Half the throughput of `mma` |
| `fma %d[r], %a[r], %b[r]` | `D[8x16] += A ⊙ B` | `ELWMUL`. Always accumulates (hardware); `zero` first for assign. Fidelity applies |
| `add %d[r], %a[r], %b[r]` | `D = A + B` | `ELWADD`. `.acc` for `D += A + B` (twice the throughput, MatrixUnit.md) |
| `sub %d[r], %a[r], %b[r]` | `D = A - B` | `ELWSUB`. `.acc` as above. Census: unused |
| `.bcast.row k` / `.bcast.col` / `.bcast.scalar` | broadcast on B for `fma` / `add` / `sub` | row `k` of B to all 8 rows / column 0 to all columns / both |
| `max.col %d[r], %a[ra]` | `D[r] = max(D[r], colmax(A[ra..ra+15]))` | `GMPOOL`. `r` must be 4-aligned; the other 3 rows of that 4-row block get zero. `.init` = no max with old D (zero D first). Census: unused. Candidate for row max in softmax (on a transposed tile) and argmax's value pass |
| `mov.r8 %d[r], %a[ra]` / `.r1` | srcA rows to dst | `MOVA2D`. bf16/tf32 to fp32 conversion when dst is `.b32`. 4-cycle latency |
| `mov.r4 %d[r], %b[rb]` / `.r1` / `.bcast8` | srcB rows to dst | `MOVB2D`; `.bcast8` broadcasts one B row to 8 dst rows; `.bcast.col` also available |
| `mov.r4 %a[ra], %d[r]` / `.r1` | dst rows to srcA | `MOVD2A`. fp32 to tf32/bf16. Census: unused. **Candidate**: attention's P goes dst → pack → l1 → unpack → srcA today; this skips l1 |
| `mov.r4 %b[rb], %d[r]` / `.r1` | dst rows to srcB | `MOVD2B`. Census: unused |
| `mov.r4 %a[ra], %b[rb]` / `.r1` | srcB rows to srcA | `MOVB2A` |
| `transpose %b` | transpose the 16x16 block in srcB rows 16..31 | `TRNSPSRCB`. Only that block (hardware) |
| `rot.lane %b[r]` / `shl.lane %b[r]` | rotate / shift one srcB row left by one lane | `SHIFTXB`. Half rate |
| `zero %d` / `%d[r].rows n` | mark rows undefined (they read as 0 for the FPU and packer) | `ZEROACC`; n ∈ {1, 16, 256, 512, 1024}-row granules in `Dst16b` rows. **Does not** give the SFPU zeros: `ld` of an undefined row is undefined behaviour. Use `fill` for that |
| `zero %a` / `%b` / `%ab` (`.half`) | set src bank to 0 | `ZEROSRC` |
| `fill.neginf %a` | set srcA bank to -inf | `ZEROSRC` mode. For `max.col` init |
| `release %a` / `%b` / `%ab` | give banks back to the unpackers without computing | `SETRWC` with clear-dvalid bits |

### 7.1 tile-level pseudo-instructions

Each expands to a straight-line sequence of the instructions above and is listed with its exact length. They are
the "naive" layer: write these first, swap in a template (section 10) when the issue rate matters.

| pseudo | expands to | count (per phase) |
| --- | --- | --- |
| `mma.tile.pN %d, %b, %a` | 32x32 `+= B @ A`: 4 output faces x 2 k-faces x 2 eight-row halves | 16 `mma` per phase |
| `mma.tile.t.pN %d, %b, %a` | same with A read transposed by face order (for `K^T` when K was unpacked plainly) | 16 |
| `mma.vec.pN %d, %b, %a` | 1x32 row of B times 32x32 A (decode matvec) using `mma.bcast` | 4 per phase |
| `fma.tile.pN` / `add.tile` / `sub.tile %d, %a, %b` | whole tile elementwise | 8 per phase |
| `mov.tile %d, %a` / `%d, %b` / `%a, %d` | whole tile move | 8 / 16 / 16 |
| `max.col.tile %d, %a` | column max of each 16-row half | 4 `max.col` |

---

## 8. SFPU (vector unit) — thread t1

32 lanes of 32 bits. One instruction per cycle unless you use `.sfpmacro` (10.4). Type suffix: `.f32` (default for
float ops), `.s32` (two's complement), `.u32`, `.sm32` (sign-magnitude, the format of `int32` in dst).

Latency: most ops take 1 cycle, `add` / `mul` / `fma` take 2. Outside templates the assembler inserts `vnop` where a
result is read too early. Inside templates you do it yourself and the assembler checks.

### 8.1 load / store (dst ↔ lreg)

| instruction | what it does | operands / notes |
| --- | --- | --- |
| `ld.<fmt> %v, %d.v[i]` | load one vector (4 rows x 8 cols) from dst | `SFPLOAD`. fmt: `f32` (from `.b32` fp32), `bf16`, `fp16` (to fp32), `sm32` (int32 kept sign-mag), `s32` (int32, converted to two's complement), `int8`, `u16`, `lo16`/`hi16` (merge into half of `%v`). Reading an undefined (`zero`ed) row is undefined |
| `ld.idx.<fmt> %v, %vi, %d.v[i]` | load and capture each lane's dst (row, col) into `%vi` | `SFPLOAD` with `ENABLE_DEST_INDEX` lane config. `%v` is pinned to L0..3 and `%vi` to the matching L4..7. For argmax |
| `st.<fmt> %d.v[i], %v` | store one vector | `SFPSTORE`. fmt as for `ld`, plus rounding `.rn` (bf16) |
| `fill.<fmt> %d, imm` | write `imm` to every vector of a tile | 32 `st` of a constant. Use instead of `zero` when the SFPU will read |

### 8.2 float arithmetic

| instruction | what it does | operands / notes |
| --- | --- | --- |
| `add.f32 %d, %a, %b` | `a + b` | `SFPADD`. If `%b` is an imm and `%d == %a`, becomes `SFPADDI` (bf16 imm) |
| `sub.f32 %d, %a, %b` | `a - b` | `SFPMAD` with negate-C (Blackhole mod1), **verify** encoding |
| `mul.f32 %d, %a, %b` | `a * b` | `SFPMUL`. Imm form with `%d == %a` becomes `SFPMULI` |
| `fma.f32 %d, %a, %b, %c` | `a*b + c` | `SFPMAD`. Partially fused, one rounding, denormal results flush to +0. `.neg.a` / `.neg.c` negate operands |
| `neg.f32` `abs.f32` | | `SFPMOV` (negate mode), `SFPABS` |
| `copysign.f32 %d, %a, %s` | magnitude of a, sign of s | `SFPSETSGN` |
| `minmax.f32 %lo, %hi` | in place: `lo = min, hi = max` | `SFPSWAP` (min/max mode). Also `.sm32` |
| `min.f32` / `max.f32 %d, %a, %b` | pseudo | `mov` + `minmax`, keeps the side you asked for |
| `rcp.approx.f32 %d, %a` | `≈ 1/a` | `SFPARECIP` (Blackhole). Refine with Newton steps for full precision |
| `exp.approx.f32 %d, %a` | `≈ e^a` | `SFPARECIP` exp mode (Blackhole). Range-reduce first (see the old `_softmax_exp_program`) |
| `lut.f32 %d, %x, %c0, %c1, %c2` | piecewise-linear: pick one of three `(slope, offset)` pairs by `abs(x)` | `SFPLUT` / `SFPLUTFP32`. The assembler pins `%x` to L3 and `%c0..2` to L0..2 (and L4..6 for the fp32 form) for the duration. Census: unused |
| `ldexp.f32 %d, %a, imm` | `a * 2^imm` | `SFPDIVP2` (exponent add); NaN / inf pass through |
| `exp.get.f32 %d, %a` (`.unbiased`) | exponent field as an integer | `SFPEXEXP` |
| `man.get.f32 %d, %a` | mantissa with the implicit bit | `SFPEXMAN` |
| `exp.set.f32 %d, %a, e` | replace exponent (`e` reg or imm) | `SFPSETEXP` |
| `man.set.f32 %d, %a, m` | replace mantissa | `SFPSETMAN` |

### 8.3 integer and bit ops

| instruction | what it does | operands / notes |
| --- | --- | --- |
| `add.s32` / `sub.s32 %d, %a, %b` | two's complement | `SFPIADD`; `%b` may be an 11-bit imm |
| `abs.s32` | | `SFPABS` (int mode) |
| `mul24.lo` / `.hi.u32` | 23-bit x 23-bit product, low / high 23 bits | `SFPMUL24` (Blackhole) |
| `and` `or` `xor` `not` `.b32` | bitwise | `SFPAND` / `SFPOR` / `SFPXOR` / `SFPNOT` (two-operand in hardware: the assembler adds a `mov` when `%d` is neither source) |
| `shl.b32` / `shr.u32 %d, %a, n` | logical shift by imm or by a vector | `SFPSHFT`. There is no arithmetic right shift (hardware); `shr.s32` is a 3-instruction pseudo |
| `clz.b32 %d, %a` | count leading zeros | `SFPLZ` |

### 8.4 conversion

| instruction | what it does | notes |
| --- | --- | --- |
| `cvt.f32.sm32 %d, %a` | sign-magnitude int to float | `SFPCAST` |
| `cvt.s32.sm32` / `cvt.sm32.s32` | between integer encodings | `SFPCAST` (Blackhole int-int) |
| `cvt.rn.bf16.f32` / `cvt.rs.bf16.f32` | round to bf16 (result in the high 16 bits) | `SFPSTOCHRND`; `.rs` = stochastic |
| `cvt.rn.tf32.f32` | round to tf32 | `SFPSTOCHRND` |
| `cvt.sat.u8.f32` / `.u16` / `.s8` / `.s16` | float to small int, saturating | `SFPSTOCHRND` float-int modes (sign-magnitude results for the signed forms) |
| `cvt.shr.sat.u8.s32 %d, %a, n` | `min(round(a >> n), 255)` | `SFPSTOCHRND` int-int. Quantisation |

### 8.5 moves and constants

| instruction | what it does | notes |
| --- | --- | --- |
| `mov %d, %a` | copy | `SFPMOV` |
| `mov.f32 %v, imm` / `mov.u32 %v, imm` | load a constant into every lane | `SFPLOADI`: one instruction if the imm fits bf16 / fp16 / 16-bit, else two (high + low halves) |
| `mov.b32 %v, %r` | broadcast a scalar register (e.g. a `.param` scale) to every lane | the risc builds two `SFPLOADI` words from `%r` at runtime and pushes them (how the old fp8 scales arrive) |
| `mov.vconst %k, %v` | set per-row constant register from lanes 0..7 of `%v` | `SFPCONFIG`. The assembler adds the `vnop` that must follow |
| `swap %a, %b` | exchange | `SFPSWAP` swap mode |
| `rand.u32 %d` | per-lane prng | `SFPMOV` prng mode |
| `vnop [n]` | `n` SFPU no-ops | `SFPNOP`. Needed by hand only inside templates and after the last `vmacro` |

### 8.6 cross-lane

Lanes form a 4 x 8 grid (4 dst rows x 8 columns), section 2.3.

| instruction | what it does | notes |
| --- | --- | --- |
| `rot.lane %d, %a[, n]` | rotate each 8-lane row right by `n` (default 1) | `SFPSHFT2` rotate mode, once per step: `n` steps cost `2n` cycles. `hsum` is built from this |
| `shr.lane %d, %a` | shift each 8-lane row right by one, zero fill | `SFPSHFT2` |
| `transp4 %v0, %v1, %v2, %v3` | treat the 4 registers as a 16x8 grid, transpose 4x4 within each column | `SFPTRANSP`. Pins the four to L0..3 (or L4..7). Turns "4 row sums" into "each register has one row's sum" |
| `shift4 %v0, %v1, %v2, %v3` | `v0 = v1, v1 = v2, v2 = v3, v3 = 0` | `SFPSHFT2` register-shift mode. Pins L0..3 |

### 8.7 per-lane conditions

The SFPU has no branches; it has a lane-enable stack of depth 8. ttptx exposes it as structured blocks. Inside a
`vif` every vector op is lane-masked; FPU, scalar and noc ops are not allowed inside one.

| instruction | what it does | notes |
| --- | --- | --- |
| `vif.<cmp>.<t> %a, %b \| imm { } velse { }` | run the block on lanes where `a cmp b` | cmp `lt ge eq ne` vs 0 → `SFPSETCC`; `gt le` reg-vs-reg → `SFPGT` / `SFPLE` (Blackhole); other forms subtract into a temp first. Lowers to `SFPPUSHC` / `SFPSETCC` / `SFPCOMPC` / `SFPPOPC`. Nesting = AND. Depth ≤ 8 is checked |
| `vif.nonzero` / `vif.zero %a` | | `SFPLZ` flag mode |
| `set.<cmp>.<t> %m, %a, %b` | lane mask: all-ones where true, 0 elsewhere | `SFPGT` / `SFPLE` write-to-VD mode. Branch-free select: `and` / `or` with the mask |

Library functions are written in ttptx, not added as instructions (brainstorm section 9): `hsum`, `hmax`
(+ index), `rsqrt`, `exp`, `silu`, `recip`. See `ttptx/rmsnorm.ttptx` for `hsum` and `rsqrt`.

---

## 9. pack (dst to l1 tile) — thread t2

The output format is `%t`'s format. The packer rounds fp32 dst to it (rounding mode is a modifier).

| instruction | what it does | operands / notes |
| --- | --- | --- |
| `pack %t, %d` | whole tile from dst into l1 | `PACR` x4 packers. The packer waits for math to finish with `%d` and math waits for the pack before it reuses `%d` (inferred; today's `MATH_PACK` semaphore) |
| `.relu` (`.relu.max v` / `.relu.min v`) | zero negatives, optionally clamp / zero small values | packer ReLU |
| `.acc` | `l1 += value` instead of `=` | packer l1 accumulation. Cross-core reductions into one tile |
| `.rn` / `.rz` | round to nearest even / truncate on narrowing | default `.rn`. Old rmsnorm comment: truncating fp32 dst to bf16 "nearly doubles error". **verify** which packer stage does the rounding |
| `.rows n` | pack only the first `n` dst rows | e.g. one row per projection output (the compact layouts) |
| `.mask.cols n` (`.neginf`) | write 0 / -inf past column `n` | packer edge masking. Today's causal mask is built on brisc with scalar stores |
| `pack.face %t[f], %d[r] {in+=16, out+=1}` | one face, template form | `in` = packer ADC channel 0 (dst side), `out` = channel 1 (l1 side). The 2-bit `AddrMode` gives at most 4 increment sets for the pack thread. **verify** |
| `pack.flush` | flush packer output buffers | `PACR` flush form |

---

## 10. templates: counters, replay, MOP, SFPU macros

Opt-in. Every loop also works written naively: the assembler emits it straight-line. Templates exist because
one risc can't push one coprocessor instruction per cycle, and because the SFPU only reaches more than one op per
cycle through `SFPLOADMACRO`. A compiler that finds these patterns automatically is future work.

Templates hold coprocessor instructions only (sections 6 to 9), all for one thread: unpack (t0), math (t1, FPU and
SFPU together) or pack (t2). The assembler rejects a template that mixes threads, and derives and sets the config
a template needs (formats, addr-mod table, MOP config, macro config) before it runs, the same as for any other
instruction.

### 10.1 counters (RWC / ADC)

Every FPU, SFPU-load/store, unpack and pack address is `imm + counter`. Counters per thread:

| counter | for | width |
| --- | --- | --- |
| `a`, `b` | srcA / srcB row | 6 bits, plus carry register |
| `d` | dst row | 10 bits, plus carry register |
| `f` | fidelity phase | 2 bits |
| `in`, `out` | unpacker / packer ADC channels | per unpacker / packer |

Any counter-using instruction can end with an increment block applied after it executes:

| syntax | meaning (hardware field) |
| --- | --- |
| `x+=n` | `x += n` |
| `x=0` | clear `x` and its carry register |
| `x^+=n` | carry jump: `cr += n; x = cr` (`*CR`) |
| `x+=n^` | advance and save: `x += n; cr = x` (`DestCToCR`, dst only) |
| `f+=1`, `f=0` | fidelity phase |

`{a+=16, b^+=8, d+=8, f+=1}` is one entry of the address-modifier table. The math thread has **8 entries**, shared
by the FPU and the SFPU `ld` / `st` / `vmacro`. The pack thread has 4. The assembler allocates entries across the
whole kernel and errors when it runs out, printing which instructions hold which entry.

| instruction | what it does | notes |
| --- | --- | --- |
| `ctr.set {a=0, d=16, ...}` | set counters | `SETRWC` (also takes `.ra` / `.rb`); `SETADC*` for `in` / `out` |
| `ctr.inc {a+=4, ...}` | add to counters | `INCRWC` / `INCADC*` |

Rule outside templates: counters are 0. After any template runs, the assembler resets the counters it changed,
unless it can prove they ended at 0. Census: 661 `SETRWC` + 122 `INCRWC` in the shipped kernels.

### 10.2 replay

```
.replay name [(.dst %t)] {
    <1..32 instructions>
}
replay name [, %dN]
```

| rule | |
| --- | --- |
| capacity | 32 slots per thread, shared by every replay that is loaded at the same time. The assembler allocates slots and reloads a replay when slots get reused (reloading costs one push per instruction) |
| body | coprocessor instructions of one thread. No `replay`, no `mop` inside |
| `.dst %t` | the body is tile-relative. `replay name, %d3` runs it on tile 3 (sets the dst base offset first). Without a param, operands name concrete tiles |
| lowers to | `REPLAY` load (once, or when evicted) and one `REPLAY` per invocation |

Census: 540 `REPLAY`s, mostly SFPU bodies (`SFPLOAD` / `SFPMAD` / `INCRWC`) and the 16-`MVMUL` matmul body.

### 10.3 mop

Two shapes, matching the two hardware templates.

**loop template** (template 1):

```
.mop name loop(outer = O, inner = I) [(.dst %t)] {
    start:      <instr>          // once per outer iteration, before the inner loop
    body:       <instr>          // inner loop body
    body.alt:   <instr>          // optional: inner loop alternates body / body.alt (runs 2*I times)
    inner_last: <instr>          // last inner iteration of every outer iteration except the final one
    final:      <instr>          // last inner iteration of the final outer iteration
    end:        <instr>[; <instr>]  // once per outer iteration, after the inner loop (at most 2)
}
mop name [, %dN]
```

**mask template** (template 0):

```
.mop name mask {
    a:      <i0>[; <i1>; <i2>; <i3>]   // run when the mask bit is 0
    b:      <instr>                    // optional, after a
    skip_a: <instr>                    // run instead of a when the mask bit is 1
    skip_b: <instr>                    // optional, instead of b
}
mop name, count, mask          // count iterations (1..), mask bit i decides iteration i (32-bit)
```

| rule | |
| --- | --- |
| slots | each slot is one instruction or `replay <name>`. That is how a template runs more than one instruction per step. Empty slots are `NOP` (`start` / `end` are then skipped) |
| defaults | `inner_last` and `final` default to `body` |
| counts | `O`, `I`: 1..1023 (Blackhole), imm or scalar reg. A reg count costs a config write before the run |
| hardware bugs | the assembler rejects the empty-start / zero-inner shapes that MOPExpander.md marks as buggy |
| one config | each thread has one MOP config, so running a different `.mop` costs up to 9 config words (tracker 5 skips unchanged words) |
| performance | a `mop` followed by a non-`mop` costs one idle cycle unless one slot expands through a `replay` of length ≥ 2 (MOPExpander.md) |
| lowers to | `MOP` (and `MOP_CFG` for mask bits 16..31) |

Census: 563 `MOP`s. Template contents: `PACR`, `UNPACR`, `UNPACR_NOP`, `REPLAY`, `SETRWC`, `MOVA2D`, `ELWMUL`,
`ELWADD`.

### 10.4 sfpmacro

`SFPLOADMACRO` does an `ld` and schedules up to four more SFPU ops on the other sub-units (simple, mad, round,
store). It is the only way the SFPU runs more than one op per cycle.

```
.sfpmacro name {
    @<delay> <instr>      // at most one per sub-unit; %x = this invocation's load target
    ...
}
vmacro.<fmt> name, %v, %d.v[i]   // ld.<fmt> %v, %d.v[i]; then schedule the body with %x = %v
```

| rule | |
| --- | --- |
| `%x` | the register this invocation loaded into (any of L0..7; the hardware picks L0..3 vs L4..7 from a spare address bit). One macro can serve several targets: rotate targets across invocations so a load doesn't overwrite a value a scheduled op still needs |
| destination | every scheduled op writes `%x` or `%vm` (hardware overrides the destination) |
| sources | the loaded value goes in the op's B or C position (hardware). Other operands are ordinary `.v` registers, pinned while the macro is live. `%x` in the A position is fixed in the template, so it is allowed only if every invocation uses the same target (checked) |
| scope | defined at kernel or function scope, after the registers they name |
| sub-units | simple: `abs and cast compc divp2 exp.get man.get add.s32 clz mov not or set* shl shr swap transp xor`... (SFPLOADMACRO.md table); mad: `add mul fma lut addi muli`; round: `cvt.*` (stochrnd), `rot.lane`/`shift`; store: `st` |
| store | `@n st` writes `%x` (or `%vm`) back to the vector that was loaded, in the load's format unless given (`st.f32`) |
| `@n` | delay 0..7 cycles. `@n.i` counts SFPU instructions issued instead of cycles (needed when the op consumes something a *later* instruction produces) |
| capacity | at most 4 macros live, and at most 4 distinct non-store ops across all live macros (`InstructionTemplate[4]`) |
| hazards | after an FPU write to the dst rows a `vmacro` reads, 3 unrelated instructions or a stall (inserted outside templates). After the last `vmacro`, enough `vnop` for every scheduled op to drain (inserted outside templates) |
| lowers to | `SFPCONFIG` writes for template / sequence / misc (+ `SFPNOP`) once, then one `SFPLOADMACRO` per invocation |

Census: only 18 `SFPLOADMACRO`, all in rmsnorm (gate / lm / qkv). The projection dot-product inner loop is
`SFPLOAD; SFPMAD; INCRWC` = 3 instructions per vector; as a macro it is 1 (section 12).

---

## 11. what is deliberately left out

| hardware | why | covered by |
| --- | --- | --- |
| `SETC16` `WRCFG` `RMWCIB` `RDCFG` `CFGSHIFTMASK`, cfg mmio | config | the assembler (trackers). Census: ~1600 config instructions + ~2560 cfg stores. Biggest win of the isa |
| `STALLWAIT` `SEMWAIT` `SEMINIT` `SEMPOST` `SEMGET` `STREAMWAIT` `ATGETM` `ATRELM` | sync | inferred. Census: 1052 `STALLWAIT` + 372 sem ops |
| `SETADC*` `INCADC*` `ADDRCRXY/ZW` `SETDVALID` `CLEARDVALID` | counters / handshakes | `ctr.*`, `give`, `release` |
| `MOP` `MOP_CFG` `REPLAY` `SFPLOADMACRO` `SFPCONFIG` `SFPENCC` `SFPPUSHC` `SFPPOPC` `SFPCOMPC` `SFPSETCC` | raw template / predication plumbing | `.mop`, `.replay`, `.sfpmacro`, `mov.vconst`, `vif` |
| `DOTPV` | identical to `MVMUL`, docs say prefer `MVMUL` | `mma` |
| `SHIFTXA` | hardware bug, unsupported | |
| `MOVDBGA2D`, `CLREXPHIST`, `GATESRCRST`, legacy conv/pool opcodes | debug or no-ops | |
| tensix GPR family (`SETDMAREG` `ADDDMAREG` ... `LOADIND` `STOREIND` `LOADREG` `STOREREG`) | a second scalar unit; the riscs already do scalar work | `.u32` ops. Revisit if a kernel ever needs scalar math in the coprocessor's queue order |
| `ATCAS` `ATSWAP` `ATINCGET(PTR)` | tensix-side local l1 atomics | `atom.*` covers remote and local |
| `STREAMWRCFG`, overlay streams | cb plumbing | inferred cbs |
| rv32: csr, local `amo*`, `fence`, `lui` / `auipc`, `jal` / `jalr` as such | compiler-owned or spelled differently | `mov`, `call`, control flow |

---

## 12. performance notes from the census

From `ttptx/census.md`, static counts over the three shipped llama3 builds (not dynamic counts):

1. **Config and sync are most of the coprocessor stream.** `SETC16` (1125), `STALLWAIT` (1052), `SFPNOP` (1026),
   `RMWCIB*` (605), plus 2559 risc-v stores to cfg and 1390 to `MopCfg`. Compute instructions (`MVMUL`, `ELWMUL`,
   `SFPMAD` ...) are a small minority. Trackers 2 to 5 target exactly this.
2. **Projections compute dot products with `ELWMUL` + SFPU reduction, not `MVMUL`.** Only attention uses
   `MVMUL`. For a 1-row activation, `mma.bcast` does 256 useful MACs per instruction against `ELWMUL`'s 128, and
   needs no SFPU lane sum per row. Decode is dram-bound (78–89% in README), so this matters only if trisc1 is on
   the critical path. Measure first.
3. **The dot-product SFPU loop is not macro'd.** `SFPLOAD; SFPMAD; INCRWC` per vector (63 `INCRWC` recorded in
   replays). The two-chain `fma` macros from `ttptx/rmsnorm.ttptx`
   (`rmsnorm_fast`, with `%vone` in place of the second `%x`) do it in 1 instruction per vector.
4. **Unused instructions with obvious uses**: `MOVD2A` (P to srcA in attention without an l1 round trip),
   `GMPOOL` (column max), packer `.mask.cols` (causal mask), `XMOV` (`cp.l1` for compact scatter), `red.add.f32`
   (cross-core reductions without a dram hop), `SFPLUT` (cheap activations).
5. **Scalar work is address math.** `addi` / `lui` / `sw` dominate risc-v; `mul` appears 111 times and `divu` 24
   (all in attention's shard lookup). There is no float scalar code at all.

---

## 13. open questions

1. **dst view per tile.** `.dst` is per kernel here. Is there a kernel that needs b32 accumulators next to b16
   tiles? (The hardware allows it "with great care", Dst.md.)
2. **unpack / pack counters.** `unpack.face` / `pack.face` increment syntax is a guess at the ADC model. It needs
   checking against the MOPs the old `ttko/unpack.py` / `pack.py` build before it is final.
3. **tilize on unpack.** Old projections assert weights and activations share an element order and never
   tilize. Do we need `unpack.tilize` at all, or is every tensor stored in the order it is consumed?
4. **sub / negate encodings** for `SFPMAD` on Blackhole, and packer rounding stages: listed, not confirmed.
5. **`.tile` larger than one tile.** Embedding and compact vectors are "N bytes"; currently written as arrays of
   tiles plus a byte count on `cp.async`. A `.buf.<fmt> [n]` class may read better.
6. **template + inference.** The compiler infers sync between riscs from register use. Inside a template the
   registers are template parameters, so inference sees one use per `mop` call, not one per instruction. That
   matches hardware (a MOP is atomic from the risc's view) but means a template must not wait on another thread
   mid-body. The assembler should reject it.
