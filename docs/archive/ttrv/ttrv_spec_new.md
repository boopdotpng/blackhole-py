> Archived design history; superseded by [the consolidated spec](../../ttrv_spec.md).

# ttrv spec

## goals
1. replace ttk: write high performance blackhole kernels as readable code, with every register field and instruction argument named
2. a target models can write, compile and be trained on (RLVR)
3. familiar and simple: risc-v assembly plus a small tensix layer

## rules
- every line lowers to a short, fixed sequence of instructions. the listing shows what it became
- no optimizer, no types, no expressions over registers. performance is what you wrote
- names over numbers: every field and operand has a readable name. still one to one with the hardware
- moves, not config: unpack and pack are one line per tile, the compiler derives their config from the formats. the raw layer is still there
- one way to write each thing
- the compiler checks hard, gives clear errors, never crashes, same input = same output

measurements behind the rules are in `ttrv_pack_unpack.md`, field encodings in `ttrv_cfg.md`.

## syntax
- `{}` blocks, indentation doesn't matter, one statement per line. a line ending in `,` continues on the next
- `//` comments to end of line, `/* */` multi line
- `#define` and `#if`, same as C
- registers are named, not `x5`. a register exists once you write to it. the compiler picks the physical one. `x0` (or `zero`) is the only physical register you can name

### arguments
every instruction is `op arg, arg, name=value, ...`:
- required operands come first, by position. at most 3. like python, one can also be written by name (`sfp.mad l3, a=l0, b=l1, c=l2`), and everything after it must be named too
- everything else is optional and named. **absent = 0 / off**. the one exception: `n` on `unpack` / `pack`, absent = one tile
- a 1-bit option is a bare word: `dvalid`, not `dvalid=1`
- counters: `name+=n` moves, `name=n` sets
- flag sets: `until=unpack|math`
- each name at most once per line

long lines wrap after a `,`. reuse a set of fields with `#define`:

```
#define RESET  srca=0, srcb=0, dst=0

math.rwc     RESET
math.addrmod 3, last, RESET,
             fidelity+=1
```

## params and core
global values sent to every core, read from a fixed place in L1. usually DRAM addresses.

`param N name`: N is 0-15, one u32 at `0x780 + 4N`. `name` is a read-only register in any `fn`:
- every `fn` that uses it gets one `lw name, 0x780+4N(x0)` at its top (shown in the listing)
- writing to it is an error
- it holds a register for the whole `fn`. too many live registers = compile error, no hidden reloads

every core also knows where it is, so it can find its share of the work:
- `core.x`, `core.y`: position in the grid
- `core.id`: which slice of the work is mine. row major over the whole grid, gaps excluded

the firmware writes these at boot, along with the DRAM bank tables (DRAM coordinates in the grid and which bank each points to) that `noc.read` / `noc.write` will use.

v1 does not require per-core parameter tables. kernels can derive their work from `core.x` / `core.y` and launch parameters. the exact grid/work mapping will be settled with the runtime.

## functions
every core has 5 risc-v cpus. each runs the `fn` with its name:

| fn | job |
| --- | --- |
| `brisc` | read (dram -> l1) |
| `ncrisc` | write (l1 -> dram) |
| `trisc0` | unpack |
| `trisc1` | math |
| `trisc2` | pack |

- no args, no return value. inputs come from `param` and `core.*`
- no `fn` for a cpu = that cpu doesn't run. reaching `}` returns to firmware. the launch ends when all 5 have returned

any other `fn` is a subroutine, callable from any entry point:

```
fn tile_addr(base, p) {
    srl  row, p, 3
    sll  row, row, 11          // * 2048 (page size)
    add  addr, base, row
    ret  addr
}

param 0 out

fn brisc {
    loop i, 10 {
        a = tile_addr(out, i)
    }
}
```

- call: `name(p, p2)`, `r = name(...)`, `r, r2 = name(...)`. `f(...)` is only for your own `fn`s
- `ret a` / `ret a, b`. every `ret` in a function returns the same count. falling off `}` = returns nothing
- a `param` or `core.*` name can't be reused as an argument or local
- lowers to `jal` / `jalr`. no recursion, no function pointers: the call graph is static, so the compiler assigns registers across calls (no calling convention) and return addresses live in fixed places (no stack)
- each cpu has its own code slot: a function called from 2 cpus is compiled into both
- tensix instructions only exist on the triscs. calling a function that uses them from `brisc` / `ncrisc` = error

## control flow
| form | does | lowers to |
| --- | --- | --- |
| `loop n {}` | n times. register or constant, 0 = none | hidden counter + `bnez` |
| `loop i, n {}` | same, `i` = 0 .. n-1, read only | `i` + `bltu` |
| `loop {}` | until `break` or `ret` (one is required) | `j` back |
| `if.c a, b {} else if.c a, b {} else {}` | conditional, any number of `else if` | inverted branch per case + `j` to the end |
| `break[.c a, b]` | leave the innermost loop | branch past its `}` |
| `ret[.c a, b] [values]` | return to caller (entry point: to firmware) | `jalr`, with `.c` an inverted branch over it |

conditions `.c`: with `a, b`: `eq ne lt ltu ge geu gt gtu le leu`. with `a` only: `eqz nez ltz gez gtz lez`.

no labels, no raw branches. waiting on a flag:

```
loop {
    lw         v, 0(flag)
    break.nez  v
}
```

## risc-v
rv32im on named registers.

| group | instructions |
| --- | --- |
| alu | `add sub and or xor sll srl sra slt sltu` |
| multiply / divide | `mul mulh mulhsu mulhu div divu rem remu` |
| load / store | `lw lh lhu lb lbu rd, off(rs)`, `sw sh sb rs, off(rs)` |
| other | `fence` |
| pseudo | `li mv not neg seqz snez` |

- the last operand can be a register or any 32-bit constant: the compiler picks the i-form when it fits, else `li` + r-form. no `addi`, `andi`, ... to learn. same for `off`
- left out: branches and jumps (use `loop` `if` `break` `ret` and calls), `lui auipc` (`li`), `ecall ebreak` (no os), csr instructions (firmware only), `nop`

## tensix
each core has one tensix engine. the triscs push instructions into it:

```
L1 --unpack--> SrcA / SrcB --math--> Dst --pack--> L1
   (trisc0)                (trisc1)  |   (trisc2)
                               sfpu on Dst (trisc1)
```

every tensix instruction starts with its engine (`unpack`, `math`, `sfp`, `pack`), which decides the trisc. wrong `fn` = error. all operands constant = one word in the code stream. a register operand = the compiler builds the word at runtime (a few visible risc-v instructions).

### formats
`bf16 fp16 fp32 e4m3 e5m2 bfp8 bfp4`. the name picks everything the hardware derives from it: the Src format, the lf8 E4M3 bit, the datum size behind the strides, the bfp exponent section size.

### unpack (trisc0)
moves up to one tile (1024 datums) from L1 into SrcA (`a`) or SrcB (`b`). set the format once, then one line per move:

```
unpack.fmt a, bf16
unpack.fmt b, bfp8
loop i, n {
    unpack a, tile_a, dvalid
    unpack b, tile_b, dvalid
}
```

| op | positional | named | lowers to |
| --- | --- | --- | --- |
| `unpack.fmt` | `a` / `b`, format | `out=` (fp32 input only: `bf16`, `fp16`), `transpose` (a), `shared_exp=` (bfp with no exponent section in L1) | config writes |
| `unpack` | `a` / `b`, l1 | `n=`, `dvalid`, `ctx=` (0-1) | base write + `UNPACR` (bfp: one per face) |
| `unpack.dvalid` | `a` / `b` | | `UNPACR_NOP` `Set_Dvalid`: hand a bank to math without unpacking (an op that only needs SrcA still has to satisfy math's SrcB check) |

- `l1`: byte address, 16 B aligned. bfp: the start of the exponent section
- `n`: datums, absent = 1024. not bfp: up to 1024, one `UNPACR`. bfp: 128, 256, 512 or 1024, one `UNPACR` per face with `l1_z+=1, reg_z+=1`, every face into the same bank, `dvalid` on the last. bfp8 and bfp4 are the same sequence. a different `n` than last time also emits `SETADCXX` (bfp: and a `SETADCZW` reset), the listing shows it
- `dvalid`: hand the filled Src bank (one tile) to math. SrcA and SrcB each have 2 banks: the unpacker fills one while math works on the other. math waits for a valid bank (`stallwait`, `until=srca_vld|srcb_vld`) and gives it back (`math.rwc release=a|b`). if math holds both, the next unpack waits. no semaphores
- `ctx`: which of the two base-address copies to write. the write is a `sem.inc unpack_sync, risc`; the compiler pairs it with a `sem.dec unpack_sync` after the `UNPACR`, so at most 2 are in flight
- everything else is fixed or derived by the compiler (format override, uncompressed, throttle, strides from the format, descriptor dims from `n`), see `ttrv_pack_unpack.md` §12

### pack (trisc2)
moves up to one tile from Dst to L1:

```
pack.fmt fp32, bf16
pack out_tile, dst=2
```

| op | positional | named | lowers to |
| --- | --- | --- | --- |
| `pack.fmt` | in, out | | config writes |
| `pack` | l1 | `n=`, `dst=` | address write + n/64 `PACR`s |

- in = how Dst is read: `fp32` (32-bit Dst), `bf16`, `fp16`, and `bfp8` for bfp output. for bfp output it is also the rounding: `fp32` none, `bf16` 7 bits, `bfp8` 6 bits (tt-metal's default). `bfp4` / `bfp2` = error
- out: `bf16 fp32 e4m3 bfp8 bfp4`
- `n`: multiple of 64, absent = 1024. bfp: 128, 256, 512 or 1024, at any 16 B aligned `l1`
- `dst`: Dst tile to read (tile i starts at row 64·i), absent = 0
- the `PACR`s are inline: n/64 - 1 with `reg_y+=4, l1_y+=4`, the last with `Last` and a reset. inline is as fast as a mop or replay
- derived by the compiler: exponent section size, Dst read strides, `round10` (`fp32 -> e4m3` goes through fp16), the pack addrmods, `Last`

### math and sfpu (trisc1)
native instructions, lowercased, one to one. registers and Dst rows positional, modifiers named:

```
math.elwmul  addr=step
sfp.load     l0, dst[0]
sfp.add      l2, l0, l1             // SFPADD VA=one, VB=l0, VC=l1, VD=l2
sfp.mad      l3, l0, l1, l2         // l3 = l0 * l1 + l2
sfp.store    dst[0], l3
```

the layer fills fixed operands: native `SFPADD` is `VD = VA * VB + VC`, so `sfp.add` sets `VA` to `one`.

| op | positional | named | lowers to |
| --- | --- | --- | --- |
| `math.addrmod` | slot (0-7), name | counters | `SETC16 ADDR_MOD_AB/_DST/_BIAS`, at the top of the `fn` |
| `math.rwc` | | counters, `release=a\|b` | `SETRWC` / `INCRWC` |
| `math.cfg` | | fields | config writes |

sfpu registers are physical: `l0` - `l7` (fixed groups `l0-l3` / `l4-l7` matter for `sfp.transp`, `sfp.shft2` and `sfpmacro`). constants: `one` (`l10`), `neg_one` (`l11`), `l12` - `l15` set with `sfp.const`. read only: `l8` (0.8373), `l9` (0). `l16`: only inside a `sfpmacro`.

### loading sfpu values

hide `SFPLOADI`'s immediate encoding, like the scalar layer hides `addi` and `lui`. the author gives a complete value, never half-immediates or an encoded instruction word. the compiler selects the load sequence; the listing shows its cost.

proposed spelling:

```
sfp.li l0, 1.0                  // fp32 literal
sfp.li l4, -inf                 // fp32 literal
sfp.li l2, valid_columns, fmt=i32
sfp.li l6, scale, fmt=fp32      // scalar register containing fp32 bits
```

- constant values and scalar-register values are supported. `fmt` defaults to `fp32`; `i32` / `u32` request integer values
- an fp32 literal is encoded at compile time. a scalar register with `fmt=fp32` already contains the fp32 bit representation: this loads it, without integer-to-float conversion
- integer literals and registers use the selected integer interpretation; unsupported values/formats are errors, never silently truncated
- a runtime load constructs the necessary instruction fields internally. callers and the host pass values, not `SFPLOADI` words (FP8 scales and attention tail counts need this)
- this changes the destination value, not the active lanes or predicate state. exact predication behavior, instruction forms and legal destinations belong in the SFPU audit

### sfpu lanes and masks (to audit)

provide a named helper for setting which lanes are active and their mask. audit lane configuration, lane-derived values, condition-code enable/set/push/pop, and index capture/swap mode against the current kernels. document the mask's bit-to-lane mapping, its interaction with predicates, state lifetime and required stalls. no numeric `SFPCONFIG` mode words in ordinary source.

the helper's signature and lowering are not frozen yet. it must distinguish persistent lane configuration from temporary predicate masking; restoring predicates must not silently reset index mode. attention masking and argmax index tracking are the acceptance examples.

### raw
anything the layer above doesn't cover, one word each, with native names:
- `unpack.tt`, `math.tt`, `pack.tt` + native instruction + native fields: `pack.tt PACR, AddrMode=1, Last`
- `unpack.cfg`, `math.cfg`, `pack.cfg` with native field names from `ttrv_cfg.md`: `pack.cfg THCON_SEC0_REG1_Exp_threshold=5`

this is how you build your own mop or replay of unpacks and packs. the compiler checks field widths and tracks the words; keeping them consistent with `.fmt` is yours.

### sync
`stallwait block, until`: block `block` until every condition in `until` is clear.
- block: `tdma sync pack unpack xmov thcon math cfg sfpu`, or `thread`
- until: `thcon unpack0 unpack1 pack0 math srca_clr srcb_clr srca_vld srcb_vld xmov trisc_cfg sfpu cfgexu`

```
stallwait cfg, unpack0|math
```

### semaphores
8 counters (value and max, 0-15) shared by the triscs. a launch starts with all at value 0, max 1. operands are flag sets: `fpu_sfpu math_pack unpack_to_dest unpack_operand_sync pack_done unpack_sync unpack_math_done math_done` (0-7, tt-llk's names).

| op | positional | named | lowers to |
| --- | --- | --- | --- |
| `sem.init` | sems, max | `value=` | `SEMINIT` |
| `sem.inc` | sems | `risc` | `SEMPOST`. `risc`: `sw` to the sem's mmio word |
| `sem.dec` | sems | `risc` | `SEMGET`. `risc`: `sw` to the sem's mmio word |
| `sem.wait` | block, sems | `nonzero`, `notmax` | `SEMWAIT`: block `block` until every sem is > 0 / < max |
| `sem.read` | rd, sem | | `lw` + `and` from the sem's mmio word |

```
sem.wait   tdma|sync, math_pack, nonzero
pack       out_tile
stallwait  sync, pack0
sem.dec    math_pack
```

- triscs only
- tensix `sem.*` act when they reach the sync unit, not when earlier work is done: `stallwait sync, ...` first. `risc` acts immediately
- `sem.inc` at max, `sem.dec` at 0: undefined. `value` > max = error

## config
`.fmt` and `.cfg` lines write config words:
- each 32-bit word a line touches is written once, whole. the other fields in it keep the value the compiler tracks. paths that disagree at a merge = error, write the field again after the merge
- words holding fields of both pack and unpack (70, 71, 119) are merged
- thread config fields lower to `SETC16`
- always emitted. a write that changes nothing is a warning. the stall a config write needs is yours (`stallwait`)

`math.cfg` short names:

| field | does |
| --- | --- |
| `dst_offset` | added to every math Dst row (usually `64 * tile`) |

## counters
math and the sfpu read and write at counters (rwc), not addresses. each thread has its own. the compiler never moves one by itself, it tracks known values only to check. (unpack and pack counters are driven by `unpack` / `pack`, or raw.)

- `srca`, `srcb`: row in SrcA / SrcB (0-63)
- `dst`: row in Dst (0-1023), plus `dst_offset`
- `fidelity`: multiply pass (0-3)
- `sp`: `sfp.load` / `sfp.store` stack pointer

every counter `c` has a saved copy, its carriage return `cr` (where the current run started):

| form | does |
| --- | --- |
| `c+=n` | `c` moves, `cr` stays |
| `c=n` | both = n. in an addrmod only `c=0` |
| `c=cr+n` | both = old `cr` + n. n = 0: back to the start of the run |
| `c=c+n` | both = old `c` + n. `dst` only |

### math.addrmod
numbered slots, applied after the instruction that names them with `addr=`:

```
math.addrmod 0, step, srca+=8, srcb+=8, dst+=8
math.addrmod 3, last, srca=0, srcb=0, dst=cr+0, fidelity+=1
```

| field | forms | n |
| --- | --- | --- |
| `srca`, `srcb` | `+=`, `=cr+`, `=0` | 0-63 |
| `dst` | `+=`, `=cr+`, `=c+`, `=0` | 0-1023 |
| `fidelity` | `+=`, `=0` | 0-3 |

a field not written = `+=0`. `sfp.*` use the same slots but never touch `fidelity`.

### math.rwc
one line = one instruction: only `+=` is `INCRWC` (n 0-15), anything else `SETRWC`. both kinds in one line = error. `fidelity` only `=0`, `sp` 0-1023, `release=a|b` gives the Src banks back to the unpackers.

```
math.rwc srca=0, srcb=0, dst=0, fidelity=0
math.rwc dst+=2
math.rwc release=a|b
```

## templates: mop, replay, sfpmacro
defined at file level, never in a `fn`. global: any trisc whose engine matches the contents can load them.

| | where | does |
| --- | --- | --- |
| `mop` | trisc | one instruction expands into a loop of tensix instructions |
| `replay` | trisc | replays up to 32 recorded instructions |
| `sfpmacro` | sfpu | one load also schedules up to 4 sfpu instructions, one per sub-unit, on later cycles |

```
mop dot {
    outer       4
    inner       2
    loop        math.elwmul addr=step
    last_inner  math.elwmul addr=last
}

replay acc {
    sfp.load  l0, dst[0]
    sfp.mad   l7, l0, one, l7
}

fn trisc1 {
    mop.load     dot          // waits for the running mop, then 9 stores
    replay.load  acc
    loop n {
        mop     dot
        replay  acc
    }
}
```

- loading is explicit (`mop.load`, `replay.load`, `sfpmacro.load`) so you see the cost and hoist it. running one that might not be loaded on some path = error
- contents are normal instructions, all operands constant (a register = error)
- each trisc has its own mop config and replay buffer

### mop
each line is a slot. a slot not written holds `NOP`, and only a plain `NOP` is skipped.

loop form:

| line | runs |
| --- | --- |
| `outer n` | n passes, 1-1023 |
| `inner n` | n steps per pass, 0-1023. `inner 0` needs `start` |
| `start` | at the start of every pass |
| `loop` | every step. required |
| `loop1` | if written, steps alternate `loop`, `loop1`, and there are 2n |
| `last_inner` | the last step of every pass but the final one. default: what the loop runs there |
| `last` | the last step of the final pass. default: `last_inner` |
| `end` | after the steps of every pass. up to 2 lines, in order |

mask form, a per-step choice between two sequences:

```
mop faces mask {
    a       math.elwmul addr=step
    skip_a  math.rwc dst+=8            // skipped step: only move the counter
}

mop faces, count=4, mask=0b0110         // steps 1 and 2 are skipped
```

| line | runs |
| --- | --- |
| `a` | step with its mask bit 0. 1 or 4 lines |
| `b` | after the `a` lines, if written |
| `skip_a` | step with its mask bit 1 |
| `skip_b` | after `skip_a`, if `b` is written |

- `count` 1-128, `mask` 32 bits (step i reads bit i, past 32 reads 0). constants or registers. the high mask bits go out as a `MOP_CFG` before the `MOP` when needed, the listing shows it
- a loop mop's counts are part of the template. a runtime count needs the mask form or another `mop.load`
- a mop can contain `replay name`. a replay can't contain `mop`

### sfpmacro
numbered 0-3. each line: sub-unit, timing, instruction. `x` is the register the macro loads into:

```
sfpmacro 0 scale {
    mad    delay=0  sfp.mul x, l12, x
    store  delay=2
}

replay row {
    sfp.macro scale, l1, dst[0]        // load l1 from dst[0], the mul and store follow
    sfp.macro scale, l3, dst[2]
}
```

- sub-units `simple mad round store`, at most one line each. which instruction fits which sub-unit: `SFPLOADMACRO.md`
- `delay=n` (0-7): n + 1 cycles after the `sfp.macro`. `after=n`: counts sfpu instructions issued instead (for inputs from later instructions). per sub-unit, all macros use the same kind. after an `after=`, n more sfpu instructions (`sfp.nop` is fine) must follow the last `sfp.macro` on every path
- the destination is `x` or `l16`. `x` is exactly one source, in `VB` or `VC` (`sfp.mul x, x, l12` = error)
- `store` stores `x` (`store delay=n l16`: `l16`) to the row it was loaded from. `fmt=` on the store line, all macros share one store format
- checked inside one macro: `simple` and `round` on the same cycle need exactly one writing `l16`. a `mad` result read on the next cycle is stale. `sfp.swap` on `simple` idles `mad` that cycle and `simple`, `round` the next
- the 4 instruction slots are shared by all macros, assigned in order of first appearance. more than 4 distinct = error. `store` takes none
- `sfpmacro.load` writes slots, sequence and shared bits (`SFPCONFIG`) plus one `sfp.nop`. a macro with `round` or `store` overwrites `l0`, the listing shows it
- run: `sfp.macro name, xreg, dst[n], fmt=, addr=`. `xreg` is `l0-l3` with even n, `l4-l7` with odd n. `addr=` applies on the load only

## checks
the compiler tracks config, counters, loaded templates and sfpu modes along every path, only to check. the output is always exactly what you wrote.
- error: running a template that isn't loaded, using an engine before its config is set, format pairs that hang the card, any case marked error above
- warning: a config write that changes nothing, a tensix `sem.inc` / `sem.dec` not behind a `stallwait` / `sem.wait` blocking `sync`

## not designed yet
- noc transfers (`noc.read`, `noc.write`), CBs, sync with brisc / ncrisc and between cores (L1 semaphores over noc atomics)
- NoC writes to host memory: a named host endpoint with the full device-visible host address, not a truncated u32 or a user-encoded PCIe coordinate. use the ordinary write/wait protocol; the helper encodes the endpoint's high address/routing fields. acknowledgement/completion semantics must be documented for argmax output. DRAM lookup remains inside the NoC helpers; remote L1 uses ordinary NoC writes/atomics
- compile-time macros: define `macro name(args) { ... }`, expand with `name!(args)`. ordinary `name(args)` remains a function call. `repeat i, N { ... }` repeats at compile time; expansion rules in `ttrv_v1_followup.md`
- SFPU value loads and lane/mask helpers above: finish signatures and audit the lowering
- the signature table for the remaining math / sfp instructions, short names for math config
- unpack / pack beyond plain tiles: dims and strides, tilize, transpose of b, upsample, fifo, unpack to Dst, edge masks, relu, `l1_acc`, compression, srnd, descale. raw until designed
- open: the fastest safe way to change `l1` per tile (the two base copies vs ordered in-stream writes). pack with bfp output under the uniform addrmods is unconfirmed
