> Archived design history; superseded by [the consolidated spec](../../ttrv_spec.md).

# ttrv spec: proposed additions

draft sections for `ttrv_spec_new.md`, written in its style so they can be merged. nothing here is implemented or measured in this form. where a lowering copies something that runs today (`fw/noc.c`, the exported kernels) it says so. **(measure)** marks a sequence that needs a probe before it is frozen.

what they cover: the grammar, the state a launch starts in, per-core values, L1, CBs, `drain`, NoC (read, write, atomic, multicast), DRAM coordinates, the math format. the last section is a worked kernel.

## grammar

```
file     = { item }
item     = param | l1 | cb | mop | replay | sfpmacro | fn
param    = "param" INT NAME [ "," "core" ]
l1       = "l1" NAME "," const { "," named }
cb       = "cb" NAME "," const "," const
fn       = "fn" NAME [ "(" [ NAME { "," NAME } ] ")" ] block
block    = "{" { stmt } "}"
stmt     = op | call | loop | if
op       = MNEMONIC [ arg { "," arg } ]
arg      = value | NAME "=" value | NAME "+=" value | NAME
call     = [ NAME { "," NAME } "=" ] NAME "(" [ value { "," value } ] ")"
loop     = "loop" [ [ NAME "," ] value ] block
if       = "if." COND value [ "," value ] block { "else" "if." COND value [ "," value ] block } [ "else" block ]
value    = NAME | const | const "(" NAME ")" | NAME "[" const "]" | NAME { "|" NAME }
const    = INT | FLOAT | NAME | const BINOP const | UNOP const | "(" const ")" | BUILTIN "(" const { "," const } ")"
```

- one statement per line. a line ending in `,` continues. `#define` / `#if` run before this grammar sees the file
- `MNEMONIC` is `[a-z0-9_.]+` from the instruction table. `NAME` is `[A-Za-z_][A-Za-z0-9_]*`
- `INT`: `123`, `0x7f`, `0b0110`, `_` allowed between digits. `FLOAT`: `1.0`, `-0.5`, `1e-3`, only where an op takes a float
- `const` is computed at compile time, 32 bits, C operators and precedence: `+ - * / % << >> & | ^ ~`. a `NAME` in it is an `l1` or `cb` name (its address). a register in it = error
- `BUILTIN`: `xy(x, y)`, `rect(x0, y0, x1, y1)` (NoC, below)
- a constant passed to a call is a `li` into the argument's register, shown in the listing

names:
- one file-level namespace: `param`, `l1`, `cb`, template and `fn` names. reusing one = error
- registers, addrmod names and noc channels belong to the `fn` they are written in. a file-level name can't be reused for one
- reserved: mnemonics, `zero`, `l0`-`l16`, `one`, `neg_one`, `dst`, `a`, `b`, `core`, the format names, the semaphore, block and condition names
- a register must be written on every path before it is read (error). written and never read = warning

## launch state

every `fn` starts from the same state. the firmware guarantees it, the compiler assumes it.

| what | at launch |
| --- | --- |
| config (both banks), thread config, addrmods | 0 |
| Dst | cleared (reads as 0) |
| SrcA / SrcB banks | all with the unpackers |
| math, unpack and pack counters | 0 |
| semaphores | value 0, max 1 |
| sfpu | all lanes enabled, flags clear. `l0`-`l7` undefined, `neg_one` = -1.0, `l12`-`l15` undefined |
| mop config, replay buffer, sfpmacros | not loaded |
| CB counters | 0 (empty) |
| noc channels | not set |
| `l1` memory | undefined, except `keep` regions |
| registers | undefined |

"using X before it is set = error" in the spec always means: on some path from here.

## per-core values

`param N name` is the same on every core and can change every launch. a value that differs per core is declared with `core`:

```
param 0 weights            // every core, sent with the launch
param 0 row_start, core    // one value per core, written once when the program is installed
param 1 rows, core
```

- both kinds: N is 0-15, both are read-only registers with one `lw` at the top of each `fn` that uses them
- the two kinds are numbered separately: 16 of each
- built in, same rules: `core.x`, `core.y` (grid position), `core.rank` (index of this core in the launch's core list, 0-based), `core.count` (cores in the launch)
- `core.id` (row major over the whole grid) is dropped: launches run on 1, 64, 88 or 96 cores, so the grid index is not the work index. `core.rank` is

## L1

every core has 1.5 MB of L1, shared by its five cpus. it is plain memory: `lw` / `sw` from any cpu, the unpacker reads it, the packer writes it, NoC transfers read and write it.

```
l1 ids,   4096
l1 merge, 16, keep
```

`l1 name, bytes`: a block of L1 at the same address on every core.
- `name` is a constant (the address). use it anywhere a constant goes: `li p, ids`, `lw v, ids+8(zero)`, `noc.read rd, ids, a, c`
- placed in file order, each block aligned to 64 B (`align=` for more). 64 is what a DRAM read needs (see noc). the listing prints the map
- nothing is zeroed at launch, and blocks are reused by the next launch of any program
- `keep`: the block survives between launches, no other program gets its address, and it is zeroed when the program is installed. for counters and mailboxes that another core writes
- past the end of L1 = error

`lw` / `sw` with a constant address must land inside a declared block or a `cb` (error otherwise). there is no way to write an MMIO address: everything outside L1 has an instruction.

## CBs

a CB hands pages of L1 from one cpu to another. it is a block of L1 plus two counters that all five cpus can read: pages `pushed` and pages `popped`. nothing else: no hidden pointers.

```
cb row, 2048, 4            // page bytes, pages. also declares the 8192 B block `row`
```

- pages is a power of 2 (error otherwise). up to 32 CBs
- exactly one `fn` writes (`reserve`, `wptr`, `push`) and one reads (`wait`, `rptr`, `pop`). a second of either = error. a CB with one end and not the other = error

| op | end | does | lowers to |
| --- | --- | --- | --- |
| `cb.reserve cb, n` | writer | wait until n pages are free | loop: 2 `lhu`, `sub`, `and`, `bltu` |
| `cb.wptr rd, cb` | writer | address of the next page to write | `lhu` pushed, `and`, `sll`, `add` |
| `cb.push cb, n` | writer | n more pages are readable | `lhu` pushed, `add`, `sw` |
| `cb.wait cb, n` | reader | wait until n pages are readable | loop: 2 `lhu`, `sub`, `and`, `bltu` |
| `cb.rptr rd, cb` | reader | address of the oldest page | `lhu` popped, `and`, `sll`, `add` |
| `cb.pop cb, n` | reader | n pages are free again | `lhu` popped, `add`, `sw` |

- `n` is a constant or a register, 1 to pages
- a group of n pages is contiguous only if n divides pages and you always move n at a time. otherwise step with `cb.wptr` / `cb.rptr` per page
- the counters are 16 bits and wrap. the ops handle it
- `push` and `pop` only move a counter. who filled the pages is not checked, so all of these are fine:
  - reading a page many times before one `pop` (a retained operand)
  - patching a page in place before `push`
  - `push` for pages another core wrote over the NoC
  - a 1-page CB with no data as a signal between two cpus
- the hazards are the other way round:
  - `push` does not wait for anything. after `noc.read` into the pages: `noc.wait` first. after `pack` into the pages: `drain` first
  - `pop` does not wait either. the unpacker reads L1 when the `UNPACR` runs, not when the trisc issues it: `drain` before `pop`, or pop one iteration late

```
fn trisc0 {
    unpack.fmt a, bf16
    loop rows {
        cb.wait  w, 4
        cb.rptr  p, w
        loop 4 {
            unpack  a, p, dvalid
            add     p, p, 2048
        }
        drain
        cb.pop   w, 4
    }
}
```

**(measure)** `push` / `pop` issued from the tensix stream (ordered after the `PACR` / `UNPACR`, no `drain`), the same way `sem.inc` has a tensix form and a `risc` form.

## drain

`drain`: the trisc waits until every tensix instruction it has issued is done. triscs only. lowers to a `sw` + `lw` on this trisc's sync word and one instruction that uses the result (3 words).

needed whenever risc-v code depends on tensix work having finished: `cb.push` after `pack`, `cb.pop` after `unpack`, reading a packed result with `lw`. it is the only instruction that waits for tensix work from the risc-v side, so it is the first thing to look for in a slow loop: today's kernels poll, commit and drain once per tile, 92-95 cycles against 17 for the unpacks themselves.

every trisc also drains once after `}`. that one is the firmware's.

## noc

every core has two NoC interfaces, `noc=0` and `noc=1`. each has 4 command buffers. a transfer is: load a command buffer, trigger it, and later wait for it. `brisc` and `ncrisc` only.

like unpack and pack: set the shape once, then one line per transfer.

```
fn brisc {
    noc.fmt  rd, read, noc=0, n=2048
    loop i, 8 {
        dram.xy   c, i
        noc.read  rd, buf, addr, c
        add       buf, buf, 2048
    }
    noc.wait rd                       // all 8 have arrived
}
```

a **channel** (`rd`) is one command buffer with its fixed words loaded. it exists from its `noc.fmt` on. the compiler picks the buffer and the transaction id, the listing shows both. more than 4 channels on one interface across `brisc` + `ncrisc` = error.

### noc.fmt

`noc.fmt ch, kind, noc=, ...`: writes the words of the command buffer that don't change per transfer.

| kind | moves | named |
| --- | --- | --- |
| `read` | remote -> my L1 | `n=` |
| `write` | my L1 -> remote | `n=`, `posted` |
| `mcast` | my L1 -> the same address on every core in a rectangle | `n=` |
| `inc` | adds to a u32 in a remote L1, atomically | `ret=` |

- `noc`: 0 or 1, or a register (one image for cores that use different interfaces)
- `n`: bytes per transfer, 1 to 16384. absent = every transfer gives its own `n=`
- `write` waits for an acknowledgement unless `posted`. `posted` writes can't be waited for arrival, only for leaving (see `noc.wait`)
- `mcast` is always posted
- `inc` is always acknowledged (a posted one hung the card intermittently). `ret=` is an `l1` block of 16 B where the old value lands
- lowers to: 1 `lw` (my coordinate) and 8-9 `sw`. a channel holds one register (its command buffer address) for the rest of the `fn`
- a channel can be set again with another `noc.fmt`. a transfer on a channel that is not set on some path = error

### transfers

| op | positional | named | does |
| --- | --- | --- | --- |
| `noc.read` | ch, l1, addr, xy | `n=` | `n` bytes from `addr` at `xy` into `l1` |
| `noc.write` | ch, addr, xy, l1 | `n=` | `n` bytes from `l1` to `addr` at `xy` |
| `noc.mcast` | ch, addr, rect, l1 | `n=` | `n` bytes from `l1` to `addr` on every core in `rect` |
| `noc.inc` | ch, addr, xy | `by=` | `*addr += by` at `xy`. absent `by` = 1 |

- the destination comes first, like `lw` and `unpack`
- `l1`, `addr`: byte addresses, register or constant. `addr` is 32 bits
- `xy`: a NoC coordinate, register or constant. `xy(x, y)` builds a constant, `dram.xy` loads a DRAM bank's, a `param` can hold one
- `rect`: `rect(x0, y0, x1, y1)`, corners included. the compiler orders the corners for the interface. columns with no tensix cores are skipped by the hardware
- every transfer lowers to the same sequence:
  1. flow control: `lw` this channel's in-flight count, loop while it is 129 or more (the counter is 8 bits)
  2. `lw` the command buffer's busy word, loop while it is set
  3. `sw` the 3 words that change (+1 with `n=`)
  4. `fence`, `sw` trigger, `fence`
- a transfer returns as soon as it is triggered. many can be in flight on one channel
- nothing orders two transfers against each other, on the same channel or not. if B needs A to have landed: `noc.wait` in between

### noc.wait

`noc.wait ch`: wait until every transfer triggered on `ch` is finished. lowers to polling loops on the channel's counters.

| kind | finished = |
| --- | --- |
| `read` | the data is in my L1 |
| `write` | the destination has acknowledged |
| `write` with `posted`, `mcast` | the data has left my L1 (the source can be reused). says nothing about arrival |
| `inc` | the old value is in `ret` |

- on every path to the end of an entry `fn`, each channel must have a `noc.wait` after its last transfer (error). the firmware does not wait for the NoC
- data the host or the next launch reads must be written acknowledged

### rules

- a DRAM read needs `addr % 64 == l1 % 64`, or it silently corrupts. checked when both are constants. `l1` blocks are 64 B aligned for this
- a write's source must be 16 B aligned
- one transfer is at most 16384 B. more = a loop

### DRAM

DRAM is 8 banks, each behind its own NoC endpoints. `dram.xy rd, bank` loads the coordinate of bank 0-7: `sll`, `lhu` from a table the firmware keeps in L1. `port=` (0-2, constant or register) picks one of the bank's three endpoints, absent = 0. spreading a stream over all three is worth about 50% on long reads.

a DRAM `param` is a plain byte address. a tensor is interleaved over the banks by page, and the arithmetic is yours:

```
fn page_addr(base, p) {            // page p of a tensor with 2048 B pages
    and  bank, p, 7
    srl  row, p, 3
    sll  row, row, 11
    add  addr, base, row
    ret  addr, bank
}
```

### between cores

there is no cross-core primitive. it is a `keep` block, `noc.inc` and a loop:

```
param 0 merger, core                         // xy of the core that merges
l1 arrived, 16, keep
l1 old,     16

fn ncrisc {                                  // every worker
    noc.fmt  bump, inc, noc=1, ret=old
    noc.inc  bump, arrived, merger
    noc.wait bump
}

fn brisc {                                   // the merger
    loop {
        lw         v, arrived(zero)
        break.geu  v, core.count
    }
    sw  zero, arrived(zero)                  // re-arm for the next launch
}
```

a `keep` word can't be cleared at launch: the launch does not order writes against the start signal. clear it after use.

## math format

unpack and pack have `.fmt`. math needs one, or Dst width is only reachable through raw config:

`math.fmt dst, sfp=`: how math writes Dst (`fp32` or `bf16`) and what `sfp.load` / `sfp.store` assume when they give no `fmt=`. lowers to one config write. `pack.fmt`'s `in` must agree with it (error across `fn`s when both are constant).

`math.zero`: clear Dst so that an accumulating instruction starts from 0. named: `rows=` (16, 64 or `all`), at the `dst` counter. one `ZEROACC`. never implied by `pack` or anything else.

## worked example: embedding

not compiled. one token's row: read the id, read the row from DRAM, write it back out.

```
#define TILE   2048
#define TILES  4                         // tiles per row

param 0 history                          // dram, 4096 B pages of token ids
param 1 table                            // dram, TILE pages, TILES per token
param 2 out                              // dram, TILE pages
param 3 pos                              // token index

l1 ids, 4096
cb row, TILE, TILES                      // brisc -> ncrisc

fn page_addr(base, p, shift) {
    and  bank, p, 7
    srl  r, p, 3
    sll  r, r, shift
    add  addr, base, r
    ret  addr, bank
}

fn brisc {
    noc.fmt   idrd, read, noc=0, n=4096
    noc.fmt   rd,   read, noc=0, n=TILE

    srl       p, pos, 10                 // 1024 ids per page
    a, bank = page_addr(history, p, 12)
    dram.xy   c, bank
    noc.read  idrd, ids, a, c
    noc.wait  idrd

    and       i, pos, 1023
    sll       i, i, 2
    lw        tok, ids(i)
    mul       p, tok, TILES

    a, bank = page_addr(table, p, 11)
    cb.reserve row, TILES
    cb.wptr   w, row
    loop TILES {
        dram.xy   c, bank
        noc.read  rd, w, a, c
        add       w, w, TILE
        add       bank, bank, 1
        if.eq bank, 8 {                  // next row of every bank
            li   bank, 0
            add  a, a, TILE
        }
    }
    noc.wait  rd
    cb.push   row, TILES
}

fn ncrisc {
    noc.fmt   wr, write, noc=1, n=TILE
    a, bank = page_addr(out, 0, 11)
    cb.wait   row, TILES
    cb.rptr   r, row
    loop TILES {
        dram.xy    c, bank
        noc.write  wr, a, c, r
        add        r, r, TILE
        add        bank, bank, 1
        if.eq bank, 8 {
            li   bank, 0
            add  a, a, TILE
        }
    }
    noc.wait  wr
    cb.pop    row, TILES
}
```

what you can read off it: 4 transfers in flight per direction, two waits per cpu, no per-tile barrier. today's image for this kernel does a full wait before and after every tile, writes all 12 command words per transfer, and keeps the bank coordinates in the image (389 words on 8B).
