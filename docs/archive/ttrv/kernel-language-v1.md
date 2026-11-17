> Archived design history; superseded by [the consolidated spec](../../ttrv_spec.md).

# ttrv: a kernel language for Blackhole

Status: draft 2, 2026-11-14, replacing draft 1. Nothing is implemented; `blackhole-py/ttrv/` holds
empty stubs. Once `ttrv/spec.py` (the instruction schema) exists it is normative, and the
reference parts of this document are generated from it.

## 1. Purpose

ttrv exists so that models can write Blackhole kernels and be trained with RL to write fast ones.
People read the kernels the models find, and use them to design tinygrad's lowering. Everything
below follows from that.

1. **The schedule belongs to the author.** This covers which thread does what, every
   synchronization between threads and between cores, every NoC transfer, every Tensix
   instruction, the loop structure and the fusion. The compiler never reorders, fuses, unrolls,
   hoists or otherwise changes the schedule, so a kernel that scores well is exactly the kernel
   you read. Syncs are always written out because they decide performance.
2. **Machine state belongs to the compiler.** This covers registers, config words, ADDR_MOD
   slots, MOP_CFG, replay installation, NoC command-buffer words, and CB and semaphore indices.
   The author states the mode an engine should be in. The compiler writes only what changed,
   together with the stall that write needs. Managing this by hand would dominate a model's
   output and its mistakes, and teaches nothing about schedules.
3. **Mistakes are caught before the card.** A hang costs a timeout and a card reset, and a wrong
   answer costs a reference comparison. Everything that can be checked statically is checked,
   with a diagnostic that has a stable ID. A rejected rollout never occupies a card.
4. **The compiler stays small.** It has no SSA, no optimizer, no control-flow graph and no graph
   colouring. Control flow is structured, so the one analysis (§10) is a walk over a tree. The
   target is a weekend and a bit of work (§14).

| The author writes | The compiler owns |
| --- | --- |
| Up to five instruction streams (brisc, ncrisc, trisc0-2) and the split of work between them | Five binaries, the launch table, the firmware ABI, both code slots |
| Scalar code over named registers, `loop`/`if`/`break`/`exit`, `.rep` | Physical registers, constants of any size, loop counters, branches |
| Every handoff: CB reserve/push/wait/pop, semaphores, stalls between engines, NoC waits | The polling loops, counter arithmetic and MMIO behind each one |
| Engine modes (formats, fidelity, transpose, ...), Dst placement, the Tensix instructions | Config encodings, deduplication, the stall a config change needs, ADDR_MOD slots |
| NoC transfers: channel, endpoints, when to wait | NIU command registers, command buffers, TIDs, busy and issue-safe polls, fences |
| Which sequences go in a MOP or a replay body, and when they run | Replay slot placement, MOP_CFG words, installation, skipping what is already in place |

Not in this version: inferred synchronization, automatic thread splitting, a scalar optimizer,
register spills, SFPU register allocation, subroutines, expressions over registers, macros with
parameters, indirect jumps.

The kernels in blackhole-py-old are a source of hardware facts, not a reference
implementation. Several of their habits are illegal here (§13).

## 2. Source form

A program is one file: declarations, then up to five `.kernel` sections. A role with no section
does not run, because its LAUNCH bit is clear.

One instruction goes on each line: the mnemonic, then comma-separated operands with the
destination first. Named operands (`bytes=2048`) come after positional ones. There are two
pieces of punctuation and nothing else:

| Form | Meaning |
| --- | --- |
| `; text` | Comment to end of line |
| `.word` | Anything resolved at compile time: declarations, sections, `.define`, `.if`, `.rep`. Every `.` block closes with `.end` |

There are no labels. Runtime blocks (`loop`, `if`) close with `end`, without the dot.

**Names.** Identifiers match `[A-Za-z_][A-Za-z0-9_]*`. Declarations, `.define` constants and
`.rep` variables share one namespace per program. Registers are named per kernel and may not
reuse a declared name. The reserved names are the SFPU registers `l0`-`l7`, the named SFPU
constants, and `dst`.

**Registers.** A name that is not declared is a register. It comes into existence when it is
first written. Reading a register that has not been written on every path to the read is an
error. A register that is written but never read gets a warning, which catches typos. There is
no syntax for a physical register.

**Operands.** An operand is one of:
- a register;
- a constant expression;
- a memory operand `off(reg)`;
- a constructor: `xy(x, y)`, `rect(x0, y0, x1, y1)`, `inc(...)`, `dst[expr]`.

Constant expressions use integers (decimal, `0x`, `0b`, `_` separators), `.define` names, `.rep`
variables, resource names (which stand for their L1 addresses), `sizeof(name)`, the operators
`+ - * / % << >> & | ^ ~ ! && ||`, comparisons, parentheses, and `log2`, `min`, `max`, `align`.
An expression that contains a register is an error, because runtime arithmetic is always an
instruction.

`ttrv fmt` produces one canonical form, which training data and diffs use.

## 3. Compile time

```asm
.define TILE 2048
.define ROW_BYTES EMBED_TILES * TILE        ; EMBED_TILES comes from -D

.if FP8
    sfpu.mul    l0, l6, l0                  ; undo the quantization scale
.elif HEAD_TILES == 1
    ...
.else
    .error "unsupported HEAD_TILES"
.end

.rep f, HEAD_TILES                          ; f = 0 .. HEAD_TILES-1, body copied
    dst.base    (HEAD_TILES + f) * 64
    replay      softmax_face
.end
```

- `.define NAME expr` binds an integer constant, and the host supplies others with `-D`. Using
  an undefined name is an error, not zero. Each set of `-D` values is one build.
- `.rep v, N` copies its body N times with `v` = 0 to N-1, and `.rep v, a, b` covers a to b-1.
  This is how a static Tensix field changes across copies: a Dst offset, a face index, an
  irregular row table. It replaces ttko's Python loops.
- There is no `#include` and no macro with parameters. A program is one file. Shared routines
  are built-in instructions (§9.4).
- `ttrv expand` prints the source with every compile-time construct resolved.

## 4. Control flow

| Form | Meaning | Lowering |
| --- | --- | --- |
| `loop n` ... `end` | Run the body `n` times. `n` is a register or constant, read once at entry, and 0 means no iterations | Hidden counter, a zero check unless `n` is a constant, and `bnez` back |
| `loop i, n` ... `end` | Same, with `i` = 0 to n-1. The body may read `i` but not write it | `i` and an `bltu` back |
| `loop` ... `end` | Run until a `break` or `exit` | `j` back. A loop with no `break` or `exit` inside is an error |
| `if.c a, b` ... [`else` ...] `end` | Conditional | Inverted branch over the then-part, then `j` over the else-part |
| `break[.c a, b]` | Leave the innermost loop | Branch to after its `end` |
| `exit[.c a, b]` | Leave the kernel | Branch to the kernel's end |

The conditions `.c` are `eq ne lt ltu ge geu gt gtu le leu`, which take `a` and `b` (a
register or constant), and `eqz nez ltz gez gtz lez`, which take `a` only.

Waiting on a word the author defined is a loop with a break:

```asm
loop
    lw          v, 0(flag)
    break.nez   v
end
```

Reaching the kernel's `.end`, or `exit`, returns to firmware. The lowering appends
`jalr x0, FW_x+4(x0)`. The firmware return address is below 0x800, so the `x0`-relative form
works from either slot. A branch whose target is more than ±4 KiB away is an error in this
version.

## 5. Scalar code

### 5.1 Instructions

The operations are those of RV32IM, with RV32 semantics. Signedness is in the mnemonic, and
nothing is inferred. Every form is one source line, and the compiler expands it to as many
instructions as it needs. A temporary that an expansion needs is a fresh register.

| Form | Notes |
| --- | --- |
| `add sub and or xor sll srl sra slt sltu mul mulh mulhu div divu rem remu` `rd, rs, rs\|const` | Any 32-bit constant as the last operand. The I-form when it fits, otherwise `li` then the R-form |
| `li rd, const` | Any constant or resource address |
| `mv not neg` | |
| `seq sne sgt sgtu sle sleu sge sgeu` `rd, rs, rs\|const` | The result is 0 or 1 |
| `lw lh lhu lb lbu` `rd, off(rs)` and `sw sh sb` `rs, off(rs)` | L1 only. Any constant offset |
| `mmio.lw rd, ADDR` and `mmio.sw ADDR, rs` | Register space, with a constant address |
| `csrr rd, name` and `csrw csrs csrc` `name, rs\|const` | |
| `fence` | |
| `param rd, name` | Load a launch or per-core parameter (§5.2): one `lw` |
| `la rd, name` | Address of a `.data` table (§6). This is the only place `auipc` is emitted |

The language has no `lui`, `auipc`, `jal`, `jalr`, branches or physical registers. The listing
shows what the source became.

### 5.2 Parameters

```asm
.param weights,   dram, page=2048, banks=8      ; launch word: base address | first bank
.param out,       dram, per_core, page=2048     ; per-core table word: this core's shard
.param token_pos                                ; u32 launch word
.param row_start, per_core                      ; u32 per-core table word
```

| Kind | Where it lives | Set by the host | Read with |
| --- | --- | --- | --- |
| launch (default) | One of 16 words at `L1_PARAM_BASE` (0x780), in declaration order | With every launch | `param` |
| `per_core` | One of 16 words in this program's per-core table above `DATA_BASE` | Once, at install | `param` |
| `dram` | A word holding the base address and first bank, in either place | Either | `dram.*` by name. `param` gives the raw word |

More than 16 parameters of either kind is an error. Parameters do not change during a launch.

On the host, parameters are keyword arguments, packed by name from the manifest:

```python
prg = ttrv.build("kernels/qkv.ttrv", EMBED_TILES=4, FP8=0, l1=(lo, hi), table=k)
dev.install(prg, cores, row_start=[...], out=[...])     # one value per core
q.exec(prg, weights=w, token_pos=5)                     # launch words by name
```

A missing or unknown name raises before anything is sent. For launch graphs (a model forward
pass is 83 to 163 launches per token), `prg.args(**fixed)` returns the packed block and
`prg.offset("token_pos")` gives the word to patch.

## 6. Declarations and memory

Declarations sit at file level and are visible to every kernel. The five kernels are compiled
together, so shared names, CB ends, semaphores and NoC resources are checked as a set.

```asm
.l1      ids,     bytes=4096, align=64        ; same address on every core
.persist merges,  bytes=16, zero              ; survives launches, zeroed at install
.cb      row,     tile=2048, depth=EMBED_TILES
.sem     ready,   max=1, init=0
.noc     wrd,     read, noc=0, bytes=2048     ; §8
.data    rects                                ; constant words that travel with the code
    .word   0x00041081, 0x000820C3
.end
```

- **Placement.** The host passes the L1 window the program may use (`l1=(lo, hi)`) and the
  address of each `.persist` region. Programs that are resident together share L1, and only the
  host's graph planner sees all of them. Inside the window, the compiler places `.l1` and CB
  storage itself, or at `addr=` if one is given. Every placement goes into the manifest.
- **Ordering.** `.l1` and `.persist` memory may be written by other threads and by the NoC, so
  the compiler never caches or reorders accesses to it.
- **`.data`.** Data tables are placed after the code of the kernels that use them, and
  addressed PC-relatively. The DRAM bank-coordinate tables behind `dram.coord` are generated
  this way.
- **Initialized L1** (the scaler and -1 tiles in today's kernels) is `.persist name, init=file`,
  written at install.

## 7. Synchronization

Every synchronization is an instruction. Each lowers to a fixed sequence and does nothing else.

```asm
cb.reserve  row, N        ; producer: poll tiles-acked until N slots are free
cb.wptr     p, row        ; producer: current write address
cb.push     row, N        ; producer: advance, publish tiles-received (RISC store)
cb.push     row, N, after=pack   ; publish from the Tensix stream once the packer has finished
cb.wait     row, N        ; consumer: poll tiles-received until N tiles are present
cb.rptr     p, row        ; consumer: current read address
cb.pop      row, N        ; consumer: advance, publish tiles-acked

sem.post    s             ; SEMPOST
sem.get     s             ; SEMGET
sem.wait    s, nonzero|notmax [, blocks=math|sfpu|pack|unpack|...]
stall       blocks=..., until=...     ; STALLWAIT with named flags
tensix.drain              ; this RISC waits until its thread's Tensix instructions have completed
dst.clear   ...           ; ZEROACC: clears per-row zero flags, which reads as zero. It is never implied
```

- **CBs.** Each CB has one producer RISC and one consumer RISC. The compiler finds them from
  use and rejects a second of either. `N` is a constant. Firmware zeroes the tile-sync counters
  at every launch, and the kernel prologue resets each end's private pointer and count. Both are
  kept in registers. A plain `cb.push` does not wait for NoC reads or the packer, so
  `after=pack` exists for tiles the packer is still writing.
- **Semaphores.** The compiler picks indices. A `.sem` with `max=1, init=0` placed on index 0, 1,
  2 or 7 needs no setup, because firmware initializes those. Any other `.sem` gets a SEMINIT in
  the launch table (§12). The only usable mutexes are 0, 2, 3 and 4.
- **Static checks.** A semaphore that is waited on but never posted is an error, and so is a CB
  with a producer and no consumer.

## 8. NoC

### 8.1 Channels

Each core has two NIUs. Each NIU has four command buffers and 16 transaction IDs, and each TID
has two counters, `requests_outstanding` and `writes_outgoing`. A channel is declared once. It
fixes the NIU, the request kind, the options, and any operand that never changes. The compiler
gives it a command buffer and a TID, writes its static words once, and on each request writes
only the words that vary.

```asm
.noc wrd,   read,    noc=0, bytes=2048        ; fixed length stays loaded
.noc ids,   read,    noc=0                    ; length given per request
.noc store, write,   noc=1                    ; acknowledged write (default)
.noc cast,  mcast,   noc=0, bytes=2048        ; posted multicast
.noc bump,  inc,     noc=0                    ; atomic increment, always acknowledged
.noc poke,  write32, noc=0, posted            ; inline 32-bit write
```

```asm
noc.read    wrd,   dst_l1, src_addr, src_coord [, bytes=N|reg]
noc.write   store, dst_addr, dst_coord, src_l1 [, bytes=...]
noc.mcast   cast,  dst_addr, rect(x0,y0,x1,y1)|reg, src_l1
noc.write32 poke,  dst_addr, dst_coord, value
noc.inc     bump,  dst_addr, dst_coord, value [, ret=slot]   ; ret: old value lands in an .l1 slot
```

Any operand may instead be fixed in the declaration (`src.coord=xy(1,2)`, `bytes=`). Coordinate
arithmetic is done with `noc.xy c, x, y` and `noc.rect r, start, end`. Static rectangles are
validated: start before end, and the excluded columns 8 and 9. The compiler swaps start and end
by NoC index, and the local coordinate is never an operand.

One request lowers to the following steps:
1. Issue-safe poll on the counter that applies to the kind: reads check outstanding, writes and
   multicast check outgoing, acknowledged writes check both, and posted inline writes check
   nothing. The counter must be below 129. A single command that splits into 128 packets or
   more drains it first.
2. Poll the command buffer's trigger until it reads 0.
3. Store the operands that vary.
4. `fence`, store 1 to the trigger, `fence`. Without the second fence, the next busy poll can
   pass the trigger store.

### 8.2 Waits

| Instruction | Lowers to | Meaning |
| --- | --- | --- |
| `noc.wait ch, sent` | Trigger idle, then `writes_outgoing[tid] == 0` | Every write has left local L1, so the source may be reused. It says nothing about arrival |
| `noc.wait ch, resp` | Trigger idle, then `requests_outstanding[tid] == 0` | Every request expecting a response has one. For acknowledged writes this implies `sent` |

`sent` is legal on write and mcast channels. `resp` is legal on read, acknowledged write,
acknowledged write32 and inc channels. Anything else is an error. Waits are the only ordering:
a flag write is not ordered after an earlier payload write unless the author waits in between,
and the language has no ordering by virtual channel.

### 8.3 Resources and checks

- **TIDs.** One per channel, from 1-15 per NIU. TID 1 on NIU 1 is reserved for the firmware's
  done notification. `tid=name` makes channels share a TID, so one wait covers them all.
- **Command buffers.** Four per NIU. Channels of one kernel may share a buffer, and the compiler
  reloads static words when the owner changes (tracked state, §10). Channels of different
  kernels never share one.
- **Launch boundary.** On every path to a kernel's end, each channel must have been waited since
  its last request: `resp` if it has responses, otherwise `sent`. Firmware does not drain the
  NoC before reporting done, so data that the host or the next launch reads must be written with
  an acknowledged write and waited with `resp`.
- **DRAM reads into L1** are corrupted silently unless `src % 64 == dst % 64`. This is checked
  when both addresses are constant, and otherwise it is the author's obligation.
- Multicast is posted only in this version.

### 8.4 DRAM addressing

```asm
dram.locate addr, bank, weights, page        ; first-bank rotation, bank = page mod banks,
                                             ; addr = base + (page / banks) * page_size
dram.coord  coord, weights, bank [, port=K|reg]
```

A streaming loop calls `dram.locate` once, then steps `bank` and `addr` itself, calling
`dram.coord` for each request. To address a byte inside a page, add the offset to `addr`.

## 9. Tensix

### 9.1 Modes

A mode instruction states the full mode of one engine. Fields it does not name take their
documented defaults. Later instructions on that engine use that mode.

```asm
unpack.mode a, from=bf16, to=fp32 [, transpose] [, x_dim=...]
math.mode   dst=fp32, fidelity=...
pack.mode   to=bf16, via=fp32 [, scalar]     ; via: the intermediate format the packer rounds through
sfpu.mode   fp32
sfpu.const  c0, 1.0                          ; programmable constant
dst.base    64 | reg                         ; Dst row base for this thread
unpack.base a, reg                           ; where the next unpack reads
pack.dest   reg
```

Writing modes never costs the author anything to think about. The compiler handles them as
follows:

- **Prologue modes are free.** Mode instructions at the top of a kernel, before any other
  instruction, go into the launch table, which firmware applies before any RISC starts (§12).
  All five kernels' prologues merge into one table. If two prologues give the same field
  different values, that is an error.
- **Later changes are deduplicated.** Every other mode instruction emits only the fields whose
  value differs from the state the compiler has tracked (§10). A changed field costs one stall
  on the engines that read it, followed by the write. A field that did not change costs
  nothing. The listing shows every emitted and every skipped write.
- **Ownership is decided by use.** A field read by engine instructions of only one thread
  belongs to that thread, and only that thread may change it after the prologue. A field read
  from several threads is shared and may only be set in a prologue. Changing a shared field
  mid-kernel is an error in this version. This replaces ttko's practice of several threads
  writing the same config word.
- **A mode must be set before use.** An engine instruction reached on some path before its mode
  is set is an error.
- **Runtime values are always written.** A runtime operand (`dst.base reg`) is written every
  time and makes the field unknown afterwards.
- **Stalls.** The stall a config write needs is part of the write. Every other stall between
  engines is the author's `stall`.
- **Format combinations that hang the card** are errors, from a table in the schema. Examples
  are FP8 input with BF16 output data format, and an X end of 1023 with BFP input.

### 9.2 Instructions

Readable mnemonics over the native instructions, one to one:

```asm
fpu.elwmul  inc(a=8, b=8, d=8)
fpu.elwmul  clr(a, b), carry(d), fid+1
fpu.mvmul   inc(b=8, d=8)
unpack      a [, to=dst] ...
pack        ...
setrwc      a=0, b=0, d=0
incrwc      d=40                  ; split into steps of at most 15 by the compiler
sfpu.load   l0, dst[0], format=fp32
sfpu.mad    l7, l0, one, l7
sfpu.store  dst[0], l0, format=fp32
sfpu.loadi  l1, 1.0 | 0x3f800000 | reg
```

- **Address progressions.** Address progression is written inline (`inc`, `clr`, `carry`,
  `fid`). The compiler gives each distinct progression in a kernel an ADDR_MOD slot, and sets
  them with SETC16 once at kernel start. Running out of slots is an error that lists the
  progressions. The unpacker and packer address counters (SETADC*) are written the same way
  once the schema inventories them.
- **SFPU registers.** They are physical: `l0`-`l7` plus the named constants. Firmware loads -1.0
  into `l11` at every launch (as `neg_one`). Predication is the native instructions.
- **SFPU NOPs.** The assembler inserts the one NOP measured to be required, after the SWAP and
  SHFT2 lane modes. Dependent MAD/MUL/ADD chains are interlocked and need no NOP.
- **Numerics.** There is no reassociation, no contraction and no change to rounding. Numerical
  order is source order.

### 9.3 Static and runtime operands

A Tensix instruction whose operands are all constant is one word inline in the TRISC stream. A
register operand makes the compiler build the word at run time and push it, which costs a few
RISC-V instructions. The schema says which operands allow this. Runtime operands are not
allowed inside `.replay` or `.mop` bodies.

### 9.4 Built-in routines

```asm
sfpu.exp        l0, l0, tmp=(l1, l2, l3)
sfpu.recip      l0, l0, tmp=(l1, l2)
sfpu.rsqrt      l0, l0, tmp=(l1, l2, l3)
sfpu.round_bf16 l0, l0
```

Each routine expands in place to a fixed, versioned sequence. Its temporaries are operands,
because SFPU registers are physical. `.version 1` freezes the sequences, so a compiler upgrade
cannot change a model's numerics. Because they expand in place, routines also work inside
replay bodies.

### 9.5 `.replay` and `.mop`

```asm
.replay accumulate                    ; up to 32 instructions across all live replays
    sfpu.load   l0, dst[0], format=fp32
    sfpu.mad    l7, l0, one, l7
    incrwc      d=2
.end

.mop dot_face, loop
    outer       PHASES
    inner       2
    loop        fpu.elwmul inc(a=8, b=8, d=8)
    last_inner  fpu.elwmul clr(a, b), carry(d), fid+1
    last        fpu.elwmul clr(a, b), inc(d=8), fid=0
.end

    replay      accumulate
    mop         dot_face [, outer=reg|N, inner=reg|N]       ; counts may be overridden per issue
    mop         unpack_row, count=N, zmask=0x0000FFFF
```

- **Slots.** A `loop` template has `outer`, `inner`, and the slots `start`, `loop`, `loop1`,
  `last_inner`, `last`, `end0` and `end1`. A `mask` template has `a0`-`a3`, `b`, `skip_a0` and
  `skip_b`. A slot holds one Tensix instruction or `replay name`.
- **Diagnostics.** A non-NOP `loop1` doubles the inner count, and `end1` runs only when `end0`
  is set. Both get a diagnostic.
- **Issuing.** `replay name` and `mop name` mean "install it if it is not already in place,
  then issue it". Replays are recorded at kernel start. A replay issued from a math MOP is
  placed in slots 16 and up. More than 32 live replay slots in one kernel is an error.
- **Hardware limits** are errors: counts above 127, and the template-1 case where the outer
  count gains 128.
- **Bodies.** A body contains Tensix instructions only. Scalar instructions, control flow and
  mode instructions are not allowed in it.
- **Deferred.** SFPU load-macros (`.sfpmacro`) are deferred. Their fields are inventoried in
  `rmsnorm_hybrid.py` and the loadmacro tests in blackhole-py-old.

## 10. State tracking

This is the compiler's one analysis. It runs per kernel, after `.rep` expansion, over the tree
of `loop`/`if` blocks.

| Cells | Entry state at launch |
| --- | --- |
| Each 32-bit config word of bank 0, as (value, known-bit mask) | Known: firmware zeroes config, then applies the launch table |
| ThreadConfig words, including `CFG_STATE_ID` and the ADDR_MOD slots | Unknown |
| The nine MOP_CFG words | Unknown |
| The contents of each replay slot | Unknown |
| The static words loaded in each NoC command buffer | Unknown |
| SFPU programmable constants | Known after the launch table. `l11` is -1 |

- **Walking the tree.** Straight-line code updates the cells in order. An `if` joins its two
  branches: a bit stays known only if it is known and equal on both. A `loop` joins the state
  at entry with the state at the end of its body and at each `break`, then walks the body again
  until nothing changes. Cells only lose information, so this takes two or three passes.
- **Emitting writes.** A mode instruction emits only the bits it changes. Config words are
  written in the Tensix stream: RMWCIB for each changed byte (atomic, and it leaves other
  threads' bits alone), SETC16 for ThreadConfig. RISC stores to config are never used for
  tracked state, because they are not ordered against in-flight engine work. MOP_CFG is written
  by RISC store after a MOP sync.
- **Unknown cells.** A runtime-valued write leaves its cell unknown afterwards, and so does a raw
  `tt.*` instruction according to its schema effects.
- **`--no-elide`.** This flag turns off all skipping. Every kernel must produce identical
  outputs both ways, which is tested.

The algorithm is a few hundred lines. The real work is the schema data: which bits each mode
field occupies, which engine instructions read which fields, and which stall each change needs.
Inventory only the fields the kernels being ported need, and add each one together with a
hardware test.

## 11. Compiler

```text
preprocess (.define, .if, .rep) -> parse against the schema -> resolve declarations
  -> per kernel: state tracking and lowering of built-ins (§10)
  -> linear-scan register allocation -> encode -> launch table
  -> static checks -> five binaries, listing, manifest
```

- **Registers.** Linear scan over the instruction order. A register that is live into a loop
  stays live until the loop's end. When the registers run out, compilation fails and the
  diagnostic names the live registers. There are no spills. Each MMIO region the kernel uses
  (config, NIU 0/1, tile sync, instruction buffer, MOP_CFG) gets a fixed base register, loaded
  at kernel start. That is a convention, not an analysis.
- **Raw escape hatch.** `tt.<isa name> field=value, ...` emits one raw Tensix instruction. The
  schema states its state effects. RL builds may disable it.
- **Static checks**, all run before any device time:
  - undefined registers;
  - loops that cannot exit;
  - role capability (`noc.*` on a TRISC, Tensix on NCRISC);
  - one producer and one consumer per CB;
  - semaphores waited but never posted, and illegal mutexes;
  - NoC obligations at kernel end, and NoC alignment;
  - modes unset at use, shared fields changed mid-kernel, and format combinations that hang;
  - MOP limits;
  - slot overflow: ADDR_MOD, replay, TIDs, command buffers, parameters;
  - register pressure, branch range, and code size (8 KiB BRISC and NCRISC, 6 KiB per TRISC).
- **Diagnostics** have stable IDs, `file:line:col`, and a JSON form, so they can serve as
  shaped reward.
- **Outputs.**
  - One position-independent `.bin` per role.
  - A listing: address, word, the machine instruction with physical registers, source line,
    and emitted and skipped state writes. The listing is output only.
  - `manifest.json`: parameter slots, per-core table layout, L1 placements, CB and semaphore
    indices, channel assignments, the launch table, sizes, and the versions of compiler, schema
    and language.
- **`--trace`.** Before each blocking instruction, the kernel stores that instruction's line id
  to a per-role L1 word, so a hang reports five line numbers. It is off by default because it
  changes timing.
- **Robustness.** The compiler is Python, and a pure function: source and `-D` values in;
  bytes, manifest and diagnostics out. Input size and loop-fixpoint passes are capped, and every
  internal failure becomes a diagnostic. Model-written input must never crash or hang it.

## 12. Runtime contract

From `fw/abi.h`:
- Launch parameters are 16 words at `L1_PARAM_BASE` (0x780).
- There are two execution slots `SLOT_STRIDE` apart, chosen by the GO word.
- `LAUNCH` is a role bitmask per slot.
- Kernel data lives from `DATA_BASE` up.
- The code slots are 8, 8, 6, 6 and 6 KiB.

Code and embedded data are PC-relative, and tests cover both slots.

**Entry state.** At every launch, before releasing the other RISCs, BRISC firmware:
- zeroes config banks 0 and 1 and the globals (except icache invalidate and the PRNG seed);
- runs ZEROACC and resets SFPU condition codes;
- sets `l0` and `l11` to -1.0;
- runs SEMINIT on semaphores 0, 1, 2 and 7 (max 1, value 0);
- zeroes the CB counters.

It does not reset ThreadConfig, MOP_CFG, replay slots, LRegs other than `l0` and `l11`, or any
NoC state.

**Launch table** (a firmware change). The compiler appends a table to the BRISC image, and
`LAUNCH + 4` holds its offset and entry count. Each entry is either a config write (address,
value) or a Tensix instruction word to push: SFPU constant setup, or SEMINIT for semaphores
outside {0, 1, 2, 7}. Firmware applies it after `reset_tensix` and before releasing the other
RISCs. A program with no BRISC kernel still has a BRISC image, which returns immediately.

**Persistent words** are zeroed or initialized at install and never at launch. Placement and
launch graphs stay in host Python and bind parameters by name. Building kernels must not import
blackhole-py-old.

## 13. Porting from blackhole-py-old

These ttko habits are illegal or unnecessary here. Kernels are rewritten, not transliterated:

- several threads writing the same config word, and SFPU state configured on one thread but
  used on another (use prologue modes);
- config writes inside replay bodies (the matmul GPR address trick is deferred);
- implicit Dst clears, implicit stalls and implicit drains around every NoC request;
- posted writes by default (here writes are acknowledged by default);
- unrolling in Python (use `.rep`);
- automatic outlining into subroutines;
- SEMGET on semaphore 5, which is never initialized.

These hardware facts carry over and are already reflected above:
- NoC fences, and the per-kind issue-safe counters;
- the DRAM alignment rule;
- the firmware entry state;
- the usable mutexes;
- the SFPU NOP rule;
- the MOP limits.

A port is judged by the outputs in `reference.json` and by `bench.py`, not by matching today's
bytes.

## 14. Order of work

1. **Encoder** (day 1). RV32IM and Tensix encoders from the ISA tables, a disassembler, and the
   listing. Inline TRISC Tensix words are rotated left by 2; words pushed over MMIO and MOP_CFG
   words are not. Test: `encode(decode(bin)) == bin` over the shipped `.bin` files, after
   stripping the appended return.
2. **Language core** (day 1). Parser, `.define`/`.if`/`.rep`, `loop`/`if`/`break`/`exit`,
   linear scan, `param`, `.l1`, `.data`. Test on the card: tiny kernels that store and loop.
3. **Data movement** (day 2). `.cb`, `.sem`, channels, waits and `dram.*`. Port `zero` and
   `embedding`, check them against reference outputs, and compare words and time per request.
4. **Tensix** (day 3, "the bit"). Modes, state tracking, the launch table and its firmware
   change, ADDR_MOD assignment, `.replay` and `.mop`. Port `qkv` and check that `--no-elide`
   agrees.
5. **The rest of Llama.** Attention (persistent counter, `noc.inc ret=`), argmax, then building
   all three models from `.ttrv` and deleting the prebuilt trees.

Gates at every step: all three models match `reference.json`, `bench.py` is no slower, elided
and `--no-elide` builds agree, and the word count per kernel is tracked. Mnemonics and operand
order are frozen after step 4, before any training corpus is generated.

## 15. Open decisions

- **Mid-kernel changes to shared fields** (for example ALU formats between phases of one fused
  kernel). This draft forbids them. The alternative is an explicit handoff instruction.
- **Per-core image variants.** `down` uses NoC 0 on half the chip and NoC 1 on the other half.
  Options are a runtime `noc=` from a per-core parameter, or one build per variant mapped onto a
  single launch.
- **Subroutines**, for code size. Under state tracking, a call would make every cell it touches
  unknown.
- **`.sfpmacro`, tilize/untilize, CBs between cores, and the matmul_peak tricks** (Tensix GPRs,
  config contexts, a 48 KiB code arena).
- **The firmware's done notification** is a posted atomic. Old tests report that posted atomics
  can hang under memory-port contention. Verify, or make it acknowledged.
- **SFPU store after MUL or CAST.** Whether it needs a NOP is untested.
- **Whether RL builds allow `tt.*`.**

## 16. Example: embedding

This example is illustrative and has not been compiled.

```asm
.version 1
.program embedding

.define TILE  2048
.define BANKS 8

.param  token_ids, dram, page=4096, banks=BANKS
.param  table,     dram, page=TILE, banks=BANKS
.param  out,       dram, page=TILE, banks=BANKS
.param  token_pos
.l1     ids,   bytes=4096, align=64
.cb     row,   tile=TILE, depth=EMBED_TILES
.noc    idrd,  read,  noc=0, bytes=4096
.noc    rowrd, read,  noc=0, bytes=TILE
.noc    wr,    write, noc=1, bytes=TILE

.kernel brisc
    param       pos, token_pos
    srl         page, pos, 10               ; 1024 token ids per page
    and         idx, pos, 1023
    dram.locate a, bank, token_ids, page
    dram.coord  c, token_ids, bank
    li          buf, ids
    noc.read    idrd, buf, a, c
    noc.wait    idrd, resp
    sll         idx, idx, 2
    add         idx, idx, buf
    lw          tok, 0(idx)
    mul         page, tok, EMBED_TILES
    cb.reserve  row, EMBED_TILES
    cb.wptr     p, row
    dram.locate a, bank, table, page
    loop        EMBED_TILES
        dram.coord  c, table, bank
        noc.read    rowrd, p, a, c
        add         p, p, TILE
        add         bank, bank, 1
        if.eq       bank, BANKS                 ; wrapped: next row of every bank
            li      bank, 0
            add     a, a, TILE
        end
    end
    noc.wait    rowrd, resp
    cb.push     row, EMBED_TILES
.end

.kernel ncrisc
    cb.wait     row, EMBED_TILES
    cb.rptr     p, row
    dram.locate a, bank, out, 0
    loop        EMBED_TILES
        dram.coord  c, out, bank
        noc.write   wr, a, c, p
        add         p, p, TILE
        add         bank, bank, 1
        if.eq       bank, BANKS
            li      bank, 0
            add     a, a, TILE
        end
    end
    noc.wait    wr, resp                    ; acknowledged writes: resp implies sent
    cb.pop      row, EMBED_TILES
.end
```

Today's BRISC image for this kernel is 389 words (8B) and 273 words (1B).
