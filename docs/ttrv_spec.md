# ttrv language specification

Consolidated v1 design, 2026-11-15. This is the canonical language document.
The backend emits firmware-ready RISC images. The O-projection fixture runs on p150
at both BF16 dimensions. The final section also describes design targets and open
hardware audits beyond this validated path.

[O projection with residual](examples/llama3_o.ttrv) exercises all five workers.
[Port review](ttrv_port_review.md) explains its limitations and compiler complexity.
[Pack/unpack measurements](ttrv_pack_unpack.md) and [native field encodings](ttrv_cfg.md)
are supporting references, not competing language specifications.

## 1. Model

A kernel is up to five programs, one per RISC. BRISC and NCRISC run scalar code
and NoC transfers. TRISC0 drives unpack, TRISC1 math/SFPU, and TRISC2 pack. There
is no automatic thread splitting, tiling, fusion, scheduling or spilling.

```
L1 --unpack--> SrcA / SrcB --math--> Dst --pack--> L1
    TRISC0                 TRISC1   |   TRISC2
                              SFPU (TRISC1)
```

A program has two kinds of statements:

- **Scalar code** is ordinary sequential code: typed variables, expressions,
  element loads and stores, structured control flow and calls (§5). It runs on an
  in-order RISC-V with uncached L1, so it has no timing or ordering behavior to
  hide, and the compiler chooses its instructions.
- **Device operations** are explicit statements, one per hardware action: NoC
  requests and waits, CB protocol, unpack/math/SFPU/pack instructions, stalls,
  semaphores and config. Named fields hide encodings, not device behavior.

Compute is native instruction wrappers: `math.elwmul`, `math.mvmul`, `sfp.mad`,
and so on. Algorithms are instruction sequences written by the author.

Issuing an engine instruction or NoC request does not complete it. The author
writes the stalls, waits, CB protocol, and inter-core protocol. Lowering may
allocate registers, select instruction forms, build runtime instruction words, and
emit documented issue-credit polls or hardware workarounds. It never invents a
pipeline, moves a config write, or waits for unrelated work. A source-mapped listing
shows setup, polls, fences, register assignments, temporaries, and all emitted
instructions.

## 2. Syntax

Every statement has one of three shapes:

| Shape | Form | Examples |
| --- | --- | --- |
| Declaration (file level) | `kind name[: type \| = target][, options] [{ body }]` | `grid 88`, `param x: bf16[]`, `cb w: bf16[1024], pages=4`, `sem s = math_pack, max=1`, `fn f(a) { }`, `mop m, outer=2 { }`, `shared { }` |
| Scalar statement | assignment, element store, call, or keyword | `lead = first & 31`, `y[i] = d[0]`, `for i in 0..n { }`, `fence` |
| Device operation | `[result =] space.op operands, options` | `w = cb.reserve weights, n=2`, `noc.wait t`, `tensix.stall math, srca_vld` |

Device operations follow eight rules:

1. **Always dotted.** A statement starting with a bare word is never a device
   operation. Namespaces: `noc cb tensix sem unpack pack math sfp mop replay sfpmacro`.
2. **Operand order.** The first operand is what the operation writes or acts on: a
   destination, CB, handle, semaphore, or the engine units it stalls. Sources follow.
3. **Options** come after operands as `name=value`; booleans are bare flags; sets use
   `|`. Positional operands may also be given by name; everything after a named one
   must be named. Duplicates are errors. Defaults are per operation; there is no
   global “omitted means zero” rule.
4. **Counts are `n=`** everywhere (CB pages, NoC elements, unpack/pack datums), with a
   per-operation default. **Formats** are `in=` / `out=` on `.fmt` operations and
   `fmt=` on single transfers.
5. **Values are assignments.** An operation that produces a value is written
   `x = space.op ...`; the result may be omitted unless the operation says otherwise.
6. **Positions use brackets:** `p[i]` (L1 element), `buffer[i]` (DRAM element),
   `dst[row]` and `dst[row, col]` (Dst). Ranges are `a..b`, b exclusive.
7. **Templates** (`mop`, `replay`, `sfpmacro`) are declared `kind name, options { ... }`
   with `label: instruction` lines, installed with `kind.load name`, and run with
   `kind.run name, ...`.
8. **`wait` / `reserve` block the issuing RISC** (`cb.wait`, `cb.reserve`,
   `noc.wait`, `tensix.wait`). **`stall` queues an engine dependency** and the RISC
   keeps issuing (`tensix.stall`, `sem.stall`).

Operand fields that take runtime values accept scalar expressions (§5), evaluated
before the operation issues; fields that must be constant take constant expressions.

Lexical rules: `{}` blocks; indentation is cosmetic. Statements end at a newline
or `;`, so a short block fits on one line (`repeat 8 { replay.run accumulate }`,
`sfp.add l0, l0, l1; sfp.nop`); a trailing comma continues a statement. Comments are `//` and `/* ... */`. Integer literals are
decimal, hex or binary with `_` separators. Floating literals, including `inf` /
`-inf`, occur only in float-valued operands. File-level names share one namespace;
locals cannot shadow them. Operand keywords such as `a` / `b` are contextual, not
reserved names. SFPU registers are physical and named directly (§10). Dotted names
inside expressions (`core.x`, `bf16.tile`) are read-only attributes, not operations.

## 3. Compile time

```text
const GROUPS = 8
macro accumulate(base, sum) {
    repeat row in 0..GROUPS {
        sfp.load l0, dst[base + row * 2], fmt=fp32
        sfp.add sum, sum, l0
    }
}
repeat face in 0..4 {
    accumulate!(face * 16, l7)
}
```

`const NAME = expr` declares a compile-time constant. A host `-D NAME=value`
overrides a `const` of that name; other duplicates are errors.

An `if` whose condition is constant is a **compile-time `if`**, at file level or
in a function, and works like C's `#if`: the taken branch's statements are
spliced in place of the whole `if`, and the other branches are dropped. It opens
no scope, so names assigned or declared in the taken branch are visible after it,
exactly as if the braces were not there. The untaken branches must parse (so the
braces match) but are otherwise ignored: no name resolution, type checking or
lowering. `else if` chains are resolved the same way. Whether an `if` is
compile-time is decided by its condition alone: if every name in it is a
constant, it is. There are no includes and no textual substitution.

```text
const FP8 = 0
if FP8 {
    grid 96
    type ACT = e4m3
    const SCALE = 1.0 / 448.0
} else {
    grid 88
    type ACT = bf16
}
cb x: ACT[1024], pages=2
```

**Constant kinds.** A constant is an integer, a float, or a type:

- Integer constants are exact integers (folded as mathematical integers, then
  checked against the type they are used as).
- A constant whose expression contains a float literal, a float constant, or
  `sqrt` is a float constant: `const EPS = 1e-5`,
  `const SCALE = 1.0 / sqrt(HEAD_DIM)`, `const INV_DIM = 1.0 / DIM`. Float
  constants are folded in IEEE double precision with `+ - * /`, unary `-`, and
  `sqrt(x)`; integer operands convert exactly. A float constant may appear only
  where a float literal may (float operands such as `sfp.li`, `sfp.const`,
  `sfp.addi`), where it is rounded once, to nearest even, to the operand's
  format. An operand that requires an exact value (`sfp.addi`/`sfp.muli` need a
  value exact in BF16) rejects one that does not round exactly. Floats never mix
  with integer expressions: `DIM * 0.5` is a float constant, not usable as a count.
- `type NAME = T` names a type (§4). It is usable anywhere a type is written
  (`param`, `l1`, `cb`, `fn` parameters, `fmt=`, `in=`/`out=`, `T.size`,
  `T.tile`). Types are not values and cannot appear in expressions.

`-D NAME=value` overrides an integer, float or type constant with a value of the
same kind (`-D FP8=1`, `-D EPS=1e-6`, `-D ACT=e4m3`). It applies to a constant of
that name wherever it is declared, including inside a compile-time `if` branch; if
no taken branch declares it, the override is unused (an error only if no branch
anywhere declares the name).

`macro name(args) { ... }` is file-level; `name!(args)` expands it inline at that
use. `repeat i in a..b { ... }` emits one copy per constant `i` from a to b-1, and
`repeat n { ... }` emits n copies; zero emits none. Use a macro where inlining is
wanted (Tensix templates, short hot sequences); a `fn` is a real call (§5).

Arguments substitute operands, variables and constant expressions, not arbitrary
statement text. Counts and compile-time conditions must be constants after binding
arguments and repeat indices. Variables declared inside an expansion are fresh per
expansion and iteration. Physical SFPU registers and device state are never renamed
or saved. No recursion, variadics, `return`, or breaks out of an expansion.
Diagnostics include definition and invocation sites. Expansion size is bounded.

## 4. Types and parameters

Data types are built-in names: float encodings `bf16 fp16 fp32 e4m3 e5m2 bfp8 bfp4`
and integers `u8 u32 i32 u64`. Engine formats (§9, §10) use the same names. A type
is an encoding and a size, not a tensor shape; nothing converts implicitly.
`type NAME = T` (§3) names one of these types, typically chosen by a compile-time
`if`.

`T[n]` is n elements of T, and plain `T` is one. Its size in bytes is n × `T.size`;
BFP has no per-element size, so `bfp8[n]` / `bfp4[n]` (n a multiple of 16) are an
exponent section of ceil16(n/16) bytes followed by n or n/2 mantissa bytes. For
arithmetic, `T.size` is bytes per element (an error for BFP) and `T.tile` is the
size of `T[1024]`: bf16 2048, fp32 4096, e4m3 1024, bfp8 1088, bfp4 576.

```text
param weights: bf16[]               // a DRAM buffer of bf16
param token: u32[], host            // a buffer in pinned host memory
param start_pos: u32 in 0..8192     // an integer value
```

Parameters are a kernel's arguments, as in a CUDA or OpenCL kernel signature: the
host supplies a value for each one at every launch, and every worker and every CPU
sees the same values. There are two kinds:

- **Buffer parameters**, `param name: T[]`: the value is the buffer's address. A
  plain buffer is in DRAM; `host` marks a device-visible host buffer (pinned
  memory, not a CPU virtual pointer). A buffer parameter is used only as a NoC
  endpoint (`name[i]`, §7), never as a scalar or a pointer. Its length is not
  part of the type; bounds are the host's binding.
- **Integer parameters**, `param name: u32 in lo..hi` or `i32`: a scalar value,
  like tinygrad's `Variable(name, lo, hi - 1)`. The range is required, its bounds
  are constant expressions, and `hi` is exclusive. The host must bind a value in
  range, and the runtime checks it when binding. The kernel reads the value as a
  read-only variable of that type, anywhere an expression may appear, including
  `shared` (§4) and loop bounds. Each read is one load from the launch's argument
  block, shown in the listing. The compiler may use the range: constant arithmetic
  over it must fit the type, and it bounds loop counts in diagnostics.

There are no float parameters. Float launch data, such as FP8 scales, lives in a
buffer like any other tensor data. Values derived from a parameter (a block count,
a mask tail) are computed by the kernel, usually in `shared`, not passed separately.

Parameters are placed in declaration order in the launch's argument block: one
word per integer parameter and per DRAM buffer, two per host buffer, 16 words in
all. The build manifest maps names to slots. The dispatcher copies the block into
every worker's L1 before the launch starts.

**Binding (runtime model).** Launches are recorded once into a graph, with their
parameters left symbolic, as tinygrad does. There is one argument set per graph.
Before each run, the host waits for the previous run to retire, writes the current
values (integer parameters such as `start_pos`, and any rebound buffer addresses)
into that set in place, and resubmits the same command buffer without waiting.
Values never change while a run is in flight: the dispatcher reads each launch's
arguments when it reaches that launch, so a mid-run write would give one run mixed
values. A prompt runs one position per run, like tinygrad's prefill. There are no
precomputed per-position argument tables.

A DRAM buffer is interleaved across banks page by page. A page is one `T.tile`
unless `page=n` declares n whole tiles (`param w: e4m3[], page=2`). Bank
mapping/rotation come from the host binding and are resolved by the NoC helper.

```text
grid 88
```

`grid N` declares how many workers the kernel runs on. It is required, and
exactly one `grid` remains at file level after compile-time `if`s are resolved
(§3), so variants choose their grid with `if`. N is an integer constant
expression and may use `const`s. The launch is always the **first N workers
in column-major order**; which physical cores those are is not the kernel's
choice. The build manifest records N.

Workers are numbered over the whole card, independently of any launch. Blackhole
has 10 worker rows (NoC y = 2..11); harvesting removes whole columns, and firmware
maps them out, so a card just has fewer columns at the end and never has holes.
The non-worker NoC columns (x = 8 and 9) are skipped:

| Name | Value |
| --- | --- |
| `grid.size` | N from `grid N`; a compile-time constant |
| `core.x` | Worker column, `x - 1 - 2 * (x >= 10)` for NoC x; runtime u32 |
| `core.y` | Worker row, `y - 2` for NoC y, 0..9; runtime u32 |
| `core.id` | Column-major index `core.x * 10 + core.y`; 0 .. grid.size-1 in a launch; runtime u32 |

Because the row count is fixed, `core.id` names the same physical core on every
Blackhole card, and the first N workers are the same cores everywhere the kernel
fits. Firmware computes all three once at boot from the `NOC_ID_LOGICAL`
register and publishes them in L1; reading one is a single load, shown in the
listing. Nothing is sent per core.

The command-queue and DMA service cores occupy the bottom of the card's last
column (worker rows 8 and 9), so they are the card's last two ids and the whole
rest of the grid is usable: N ≤ columns × 10 − 2, which is 118 on the smallest
supported card (12 columns) and 138 on 14. The runtime rejects a kernel whose N
does not fit the card; ids are never skipped. A launch is still one multicast:
the runtime covers the workers' bounding rectangle and excludes the service
cores with the NoC's multicast exclusion, a runtime detail invisible to kernels.

`first, count = split(n)` is the standard balanced work split. Worker `core.id`
owns items `[first, first + count)`, where `first = core.id * n / grid.size` and
`first + count = (core.id + 1) * n / grid.size`. Every item has exactly one owner;
counts differ by at most one; with n < grid.size some workers get zero. `n` is a
u32 expression; the intermediate products must fit u32 (constant n is checked).
It is a builtin, not a device operation. It compiles to the scalar code above,
shown in the listing. Other splits are ordinary scalar code over `core.*` and `grid.size`.

```text
shared {
    first, count = split(DIM)
    lo = first & ~31
    lead = first & 31
}
```

`shared { ... }` declares per-core values that every entry function can read, so
the five programs don't each repeat the same partitioning code. There is at most one,
at file level. It holds only assignments, each of which is evaluated the same way on
every RISC:

- right-hand sides use integer expressions over constants, integer parameters,
  `grid.size`, `core.*` and earlier shared names, plus builtin calls (`split`);
- no element access, device operations, `fn` calls, control flow or compound
  assignment.

Every RISC therefore computes identical values. Shared values use the ordinary
wrapping arithmetic of §5, and computing one that a given worker never uses (for
instance a count that wraps on a worker that exits early) is not an error. Shared names are file-level names
(§2): read-only, and locals cannot shadow them. They are visible in entry functions
only; pass them to other functions as arguments.

An entry function that reads a shared name gets that name's assignment, and those of
the shared names it depends on, copied into the start of its body in source order.
Assignments it doesn't need are omitted, and a RISC that reads none gets nothing.
Each copied name holds a register for the whole entry function, as if it were
assigned in the function's outermost block (§5). If register pressure matters, compute
the value locally where it is used instead. The listing shows the copies per RISC.

There are no per-core launch tables and no per-core images. Every worker in a
launch runs the same binary with the same parameters. Per-core values (row ranges,
DRAM ports, addresses) are formulas over `core.*` in the kernel, visible in the
source; code that must differ between cores branches on them. Irregular placement
is not expressible; placement tuned for NoC locality is a possible later addition,
not part of v1.

## 5. Scalar code

### Variables and types

A variable is created by its first assignment, `name = expr`, and lives until the
end of the enclosing block. Later assignments in scope (`=`, `+=`, `-=`, `*=`,
`&=`, `|=`, `^=`, `<<=`, `>>=`) update it. Its type is its initializer's and never
changes. A variable first assigned inside a block is not visible after it (a
compile-time `if` is not a block, §3): assign
it before the block to use it afterwards. Reading a name before it exists is an error.

- `u32` is the integer type by default; `i32` holds signed values. A literal takes
  the type of the other operand (u32 on its own) and must fit it. Mixing u32 and i32
  in one operation is an error; `i32(e)` / `u32(e)` reinterpret the bits.
- A pointer refers to elements of one type, written `T*` in function parameters. L1
  and CB names are constant pointers of their declared element type, and
  `cb.reserve` / `cb.wait` return page pointers. `p + n` / `p - n` move by n
  elements and `p[i]` is element i. There is no other pointer arithmetic, no pointer
  difference or comparison, and no pointer into DRAM (parameters are NoC endpoints).
  `u32(p)` is the byte address.
- Float elements (`bf16`, `fp32`, ...) can be loaded, stored, held in a variable and
  passed to float operands such as `sfp.li`, but not used in arithmetic or
  comparisons; the RISCs have no float unit. BFP elements cannot be indexed.

### Expressions

Operators, highest precedence first, as in C: unary `- ~ !`; `* / %`; `+ -`;
`<< >>`; `< <= > >=`; `== !=`; `&`; `^`; `|`; `&&`; `||`. Parentheses group.
`&&` / `||` short-circuit. Comparisons and `!` produce u32 0 or 1; conditions treat
nonzero as true.

Arithmetic wraps modulo 2^32, as RV32IM does. Signedness comes from the operand
type: `/ % >> < <= > >=` are signed for i32 and unsigned for u32; the other
operators give the same bits either way. Shift counts use their low five bits, and
division by zero gives the RV32M result. `mulh(a, b)` is the high word of the 64-bit
product. Constant subexpressions are folded with mathematical integers and must fit
their type; no silent truncation.

### Element access

`p[i]` in an expression loads element i; `p[i] = e` stores it. Each access is
exactly one load or store of the element's width, in program order: the compiler
never caches, merges, reorders or removes L1 accesses. Ordering against engines and
the NoC is the author's job (CB protocol, `tensix.wait`, `noc.wait`). `fence` orders this
RISC's earlier memory accesses before its later ones. Element access reaches L1
only; MMIO goes through named operations. Known out-of-bounds constant indices into
declared storage are errors.

### Control flow

| Form | Meaning |
| --- | --- |
| `if c { ... } else if c { ... } else { ... }` | Conditional |
| `while c { ... }` | Test before each iteration |
| `for i in a..b { ... }` | i from a to b-1; a and b sampled once; empty if a ≥ b (u32); i is read-only |
| `loop n { ... }` | n times, sampled once; zero skips |
| `loop { ... }` | Until `break` or `return`; an exit must occur syntactically |
| `break` / `continue` | Innermost loop |
| `return [values]` | All returning paths agree in count |

There are no labels or gotos. Merely having an exit in an infinite loop does not
prove termination. An `if` on a constant condition is resolved at compile time (§3).

### Functions

Entry functions are `fn brisc() { ... }`, `ncrisc`, and `trisc0` through `trisc2`.
An absent entry does not run. Entry functions have no arguments or results;
reaching `}` returns to firmware. Other functions take scalar arguments and return
zero or more results:

```text
fn tile_span(first: u32, count: u32) {
    lo = first & ~31
    return lo, first + count - lo
}
lo, n = tile_span(first, count)
```

Parameters are u32 unless annotated, as in `fn f(p: bf16*, n: i32)`. A call is a
statement of its own (`f(x)`, `y = f(x)`, `a, b = f(x)`), never part of a larger
expression. Builtin functions (`split`, §4) follow the same call rules, and their
names are reserved. The call graph is acyclic. A function is a real call with one copy of
its code per RISC that uses it; use a macro to inline. Calls do not reset or restore
device state, and engine restrictions apply through calls.

### Registers

There is no stack, no spilling and no RISC-V calling convention: `ra`, `sp`, `gp`
and `tp` are ordinary registers here. A kernel owns x1–x31; firmware reloads its own
`sp`/`gp` when the kernel returns.

Some registers are base registers. Each RISC has a fixed table of hot MMIO blocks
in `hw.py` (for example RISC-local memory, the RISC's NoC registers, Tensix config):
the entry prologue loads each base once (two instructions), and the compiler never
allocates those registers. A load or store whose constant address lies within
−2048..+2047 bytes of a base is one instruction, `offset(base)`; any other constant
address costs one `lui` first, with the low 12 bits in the access's offset. Whether an access is one instruction
follows from its address alone. The rest of x1–x31 hold variables:

- A variable holds its register from its first assignment to the end of its block;
  expression temporaries are released at the end of their statement. Lifetimes are
  lexical, so there is no liveness analysis.
- Functions are compiled after all their callers. A callee's registers (parameters,
  locals, temporaries, and the register it returns through) are chosen from those
  free at every one of its call sites, so a call saves nothing. A call moves the
  arguments into the callee's parameter registers, jumps with `jal` through the
  callee's return register, and copies the results out.
- Exhaustion is a compile error naming the statement or call site and the variables
  holding registers there. Narrow a scope or split an expression.

The listing shows the base registers, each variable's register and every temporary.

## 6. L1 and CBs

```text
l1 x: bf16[2048]                      // 2048 bf16 values in L1
l1 scratch: u8[4096], align=128
l1 arrived: u32[4], keep
cb weights: bf16[1024], pages=8       // ring of 8 pages, each 1024 bf16 values
cb tokens: u32[16], pages=2           // two pages of 16 u32 values
```

`l1 name: T[n]` reserves L1 storage for the elements. `cb name: T[n], pages=p`
declares a CB whose pages each hold `T[n]`. Counts are constant expressions.

L1 and CB names are constant pointers shared by the five RISCs. Storage is placed
deterministically in declaration order within the runtime-provided arena, aligned
to 64 bytes by default (`align=` can increase it). Code, runtime reservations and
persistent bindings are excluded from this arena; CB state is not in L1 at all. Report the full map;
overlap, invalid alignment and overflow are errors. No implicit scratch reuse.

Scratch contents are undefined on entry. `keep` storage is zeroed at installation,
retained across launches and excluded from other programs' scratch placement. The
runtime binds its stable address; the program rearms it with explicit synchronization.

CB capacity (`pages=`) is a power of two, at most 32768 pages, subject to L1
capacity. Page size is a positive multiple of four bytes; it need not be a power of
two. Up to 32 CBs. Each has one producing RISC and one consuming RISC, including
accesses through functions. Exactly one end of each kind must exist.

| Operation | Meaning |
| --- | --- |
| `p = cb.reserve q, n=1` | Poll until n pages are free; p points to the first. Does not advance a counter |
| `cb.push q, n=1` | Publish n pages; advance the producer counter |
| `p = cb.wait q, n=1` | Poll until n pages are available and retain them; p points to the oldest |
| `cb.pop q, n=1` | Release n pages; advance the consumer counter |
| `c = cb.read q, pushed\|popped` | Counter value, for author-written nonblocking protocols |

`n` is a constant or expression in 1..capacity.
Counters are modulo 65536; occupancy is `(pushed-popped) & 65535` and must remain
in 0..capacity. A page pointer is base + `(counter & (capacity-1))` × page size.

CB state lives outside L1, as in the existing kernels:

- The shared counters are overlay stream registers: CB i uses stream 8 + i, whose
  registers 8 and 10 hold `pushed` and `popped`, 16 bits each. The producer writes
  `pushed` and reads `popped`; the consumer does the reverse. Firmware zeroes them
  before every launch.
- Each end keeps a cursor in its RISC's private RAM (`0xFFB00000`): the current page
  pointer and its own counter, 8 bytes per CB end. The pointer advances by page size
  and wraps at the ring's end, so there is no multiply; it equals the formula above.
  The prologue initializes each cursor the RISC uses. Placement is deterministic and
  shown in the listing, below firmware's stack and data.

Reserve/wait do not accumulate
reservations: the author must not publish more than was reserved or release more
than was retained. Reserving or waiting again without moving the counter returns
the same page.

CBs carry data; don't use one as a bare flag. Signal between TRISCs with a
semaphore (§8).

A multi-page span is contiguous only before the ring boundary. Fixed-size groups
that divide capacity and always advance by that group size do not straddle it.
Otherwise split at the boundary or reserve/wait page by page.

Push/pop use release ordering; successful reserve/wait use acquire ordering.
The operation emits the necessary scalar fences, but **no engine/NoC completion
wait**. Wait for incoming NoC reads or packing before push; finish unpack/outgoing
reads of storage before pop. Repeated reads, in-place patches and remote-filled
pages are legal. Multi-reader lifetimes remain author-written counters/protocols.

`wait` consumes nothing, so resident data (reused weights, norm scales, a shared
input vector) is a CB that's published once and read any number of times:

```text
cb gamma: bf16[1024], pages=1
// producer, once:   g = cb.reserve gamma; noc.read g, ..., wait; cb.push gamma
// consumer, once:   g = cb.wait gamma
// then any number of unpack.move / g[i] reads; cb.pop gamma when finished, or never
```

A page retained at exit needs no pop, because launch state resets CBs. This is the
way to publish one-time data. Don't publish plain `l1` storage as a side effect
of some other CB's push.

## 7. NoC

BRISC issues every request on NoC0 and NCRISC on NoC1; the TRISCs issue none.
There is no NoC selection in source. Requests are `noc.read`, `noc.write`,
`noc.inc` and `noc.mcast`, destination first. Writes are acknowledged unless
marked `posted`; increments are acknowledged; multicast is posted.

```text
t = noc.read w, matrix[row * DIM], n=DIM
noc.wait t
```

A request returns a handle naming its transaction ID; `noc.wait` takes handles.
The `wait` flag waits for the request's full completion right after issuing it,
like a following `noc.wait` on its handle, and then no handle is needed:
`noc.read w, matrix[row * DIM], n=DIM, wait`.
Each request statement gets its own transaction ID at compile time, so a statement
in a loop reuses its ID and a wait covers every request it has issued. `tid=h` puts
a request under an existing handle of the same kind instead. Handles are compile-time
names, not values: they hold no register, cannot be stored or computed with, and
follow variable scoping. A request's handle may be omitted only if it uses `tid=`
or `wait`.
Transaction IDs are 16 per NoC minus firmware reservations; running out is a
compile error. Merge requests with `tid=` to save IDs.

The compiler gives each RISC one command buffer per request kind it uses and writes
that buffer's fixed fields once at the start of the entry function; the listing
shows these stores. Each request polls its kind's issue credits and command-buffer
busy state, writes operands, fences, triggers, then fences. It does not drain
earlier requests or wait for remote completion. Reads/atomics use
outstanding-response flow control, writes use outgoing counters, and acknowledged
writes also account for responses. Lift the current per-kind recipes, including
packet-count/counter-wrap limits, rather than a universal “in-flight” counter.

### Endpoints and transfers

| Endpoint | Meaning |
| --- | --- |
| `buffer[i]` | Element i of a buffer parameter (DRAM: its pages concatenated) |
| `remote(x, y, p)` | L1 pointer p in another worker |
| `rect(x0, y0, x1, y1, p)` | L1 pointer p in every worker of a rectangle (multicast only) |

The local side of a transfer is an L1 pointer expression. `n=` counts elements of
that pointer's type; when the other side is a typed DRAM buffer, the element sizes
must match (a `u8` pointer counts bytes). Endpoint components may be constants or
scalar expressions. DRAM lookup, bank rotation, and coordinate encoding are inside
the helper. `port=` optionally selects a DRAM port, 0..2, as a constant or scalar expression;
default is the binding's preferred port. Remote L1 and host operands have no DRAM port option.

```text
a = noc.read  w, matrix[row * DIM], n=DIM              // one weight row
b = noc.read  r, residual[lo], n=first + count - lo
c = noc.write output[first], s + lead, n=count
d = noc.write result[0], token, n=4, posted           // into a host buffer
e = noc.write remote(x, y, inbox), message, n=4
f = noc.inc   remote(x, y, arrived), by=1, ret=old
g = noc.mcast rect(x0, y0, x1, y1, x), x, n=DIM        // to x on every target
```

A DRAM transfer may cross pages: the helper issues one request per page touched,
in address order, under the same handle, as a loop shown in the listing, and
`noc.wait` covers them all. Each request is at most one page; the transfer has no
other length limit. That is the only splitting a transfer does, plus whatever the
audited partial-write rule requires (§12, item 4); that rule lives in the helper,
not in kernels. A remote or host transfer is one request of 1..16384 bytes. No
implicit gather, bounce buffer, or unicast fallback.

Alignment constraints are transfer-specific. DRAM reads require matching
source/destination offsets modulo 64: the L1 address ≡ the element's byte offset in
the buffer (mod 64). Every piece preserves that because every `T.tile` is a
multiple of 64 bytes. Known violations are errors; dynamic ones are caller
preconditions. Finalize the partial-write constraints from existing helper tests
rather than applying a blanket 16-byte-source rule to every write.

`noc.inc` adds a u32 modulo 2^32, `by=1` by default. `ret=` is a 16-byte-aligned
response slot of at least 16 bytes, given on the request. Wait before
reading/reusing it; simultaneous requests need distinct slots. The supported
increment operand range must match the selected native recipe, with no truncation.

### Completion

`noc.wait h1, h2, ...` covers all preceding requests under each handle, not just
the last one:

| Kind | Completion guarantee |
| --- | --- |
| Read | Destination L1 bytes are available |
| Acknowledged write | Destination acknowledged the write |
| Increment | Atomic response is available in `ret` |
| Posted write / multicast | Local source bytes are no longer in use; no arrival guarantee |

`noc.wait h, sent` waits only for source release on write/multicast.
Before exit, acknowledged operations must reach full completion; posted operations
must reach sent. No implicit end-of-scope wait. A wait checks command acceptance
before its counters and establishes the required local memory ordering.

`s = noc.status h, outstanding|outgoing` exposes a handle's counters for
hand-written pumps. The compiler reports physical assignments. Counter polling, CB progression,
and remote notifications remain visible source code.

Rectangle bounds are inclusive and use worker coordinates (`core.x`, `core.y`, §4); the helper
encodes coordinates and corner order for the issuing RISC's NoC. `include_sender` defaults off. Target
membership must be valid; do not silently include nonparticipants in a bounding
rectangle. Readiness, consumption credits and generation reuse are manual.
A multicast send wait followed by an unrelated flag write does not prove arrival.
The ordered multicast notification recipe is still an explicit audit item below.

For remote publication via unicast: write payload acknowledged, wait, increment
the receiver's counter, wait for the atomic. The receiver polls with the necessary
fence before consuming payload. Persistent counters must be rearmed before the next
generation can publish. Host completion means device-visible write completion;
host mapping/coherency and notification policy are runtime obligations.

## 8. Engine synchronization and configuration

`tensix.stall units, conditions` enqueues an engine dependency: the named units
hold until the conditions are met, and the RISC keeps issuing. Units: `tdma sync
pack unpack xmov thcon math cfg sfpu`, or `thread`. Conditions: `thcon unpack0
unpack1 pack0 math srca_clr srcb_clr srca_vld srcb_vld xmov trisc_cfg sfpu cfgexu`.
`src*_vld` waits for a consumable bank; `src*_clr` waits for a writable bank. Busy
conditions wait for completion.

`tensix.wait` stops the calling TRISC until its preceding Tensix work completes. Use
the existing thread-sync MMIO recipe; do not treat an engine-local stall as a RISC
barrier. Firmware does this once at entry-function return, never at a function
return. Early CB publication still requires its own explicit `tensix.wait`.

Eight hardware semaphores use names `fpu_sfpu math_pack unpack_to_dest
unpack_operand_sync pack_done unpack_sync unpack_math_done math_done`.

```text
sem dst_full = math_pack, max=1     // math -> pack: one Dst result in flight
```

`sem name = hw, max=n` is a file-level alias that names a semaphore by its role.
`max=` records the maximum the program relies on (default 1, the launch value).
If it is not 1, a `sem.init` with that max must run before the semaphore is used;
the checker rejects programs where it can't see one. Each hardware semaphore has at
most one alias. Operations accept the alias or the hardware name.

| Operation | Meaning |
| --- | --- |
| `sem.init sems, max=1, value=0` | Initialize selected counters; max/value 0..15 |
| `sem.inc sems` / `sem.dec sems` | Queued SEMPOST/SEMGET |
| `sem.inc sems, risc` / `sem.dec sems, risc` | Immediate RISC-side update |
| `sem.stall units, sems, nonzero\|notmax` | Hold the units until the counters are >0 / <max; the RISC keeps issuing |
| `v = sem.read sem` | Scalar counter read |

Updates at full/empty respectively are invalid. Queued updates do not themselves
complete math or packing: order them with `tensix.stall sync, ...`. Compiler-reserved
unpack credits cannot be used by the application. Their initialization is part of
the unpack recipe, not the application's default max-one semaphore state.

`.fmt` / `.cfg` execute where written, always emitting writes. A write changes only
the fields it names, so the compiler does not track config values.

Config has one copy per Tensix core and is shared by its three TRISCs, and one word
can hold several engines' fields: word 1 holds unpack's SrcA/SrcB formats (bits
17–24) next to math's Dstacc and FP32 bits (25–30), sharing byte 3. Every Config
field write is masked: one `RMWCIB` per byte touched, changing only that field's
bits. The configuration unit runs one such instruction per cycle across all threads,
so concurrent masked writes from different TRISCs, even to the same byte in the same
cycle, are serialized and never lost (measured:
`blackhole-py-old/tests/probes/probe_cfg_shared_word.py`, word 1, about 600k writes
per thread, none lost; unmasked writers lost thousands). This holds only while:

- no thread writes a shared word whole. `WRCFG` and RISC stores to Config are used
  only for words one RISC owns entirely, such as runtime addresses (the unpack base
  address is a TRISC0 store to its own words);
- every thread uses config bank 0. `CFG_STATE_ID` is never written;
- fields lie in words 0–255, `RMWCIB`'s range. Every field the language uses does
  (the highest is word 222).

Each field, identified by address space, word and bits, has one writing RISC; two
is an error. The same index in Config and ThreadConfig names different registers.
ThreadConfig is per thread and written 16 bits at a time by `SETC16`; an operation
that writes a ThreadConfig word supplies every field in it. The one word holding
fields an operation does not otherwise set is `UNPACK_MISC_CFG`; its unpack context
offsets are program constants (§9).

Masked writes settle whether a value survives, not when an engine sees it. Ordering
a change against the engines that read the field, such as switching Dst from fp32 to
bf16 while pack runs, is the author's protocol: quiesce with `tensix.stall` /
`tensix.wait` and signal with semaphores or CBs. The compiler neither infers nor
checks it.

## 9. Unpack and pack

Formats: `bf16 fp16 fp32 e4m3 e5m2 bfp8 bfp4`, the built-in types of §4 (the
integer types are not unpack/pack formats in v1). Format names select hardware encodings,
datum strides and exponent storage. L1 tile layout and partial-tile shape must be
specified by the move/descriptor; byte storage alone does not imply a layout.

| Operation | Options / meaning |
| --- | --- |
| `unpack.fmt a\|b, in=T` | `a`, `b` or both (`a\|b`); `out=bf16\|fp16` for fp32 input, `transpose` for A only, `shared_exp=` for BFP without exponent storage |
| `unpack.move a\|b, p` | From L1 pointer p; `n=1024` datums, `dvalid` off by default, `ctx=0` |
| `unpack.dvalid a\|b` | Publish a Src bank without moving data |
| `pack.fmt in=T, out=T` | Set pack conversion; input interpretation includes documented prerounding |
| `pack.move p, dst[row]` | To L1 pointer p from Dst row (64 per tile); `n=1024` datums; enqueue packing, do not release/clear Dst |
| `pack.gather p, dst[row, col]` | `n=1` datums from one Dst column, rows `row`, `row+step`, ...; `step=1`, `acc` off |

The unpack pointer is 16-byte aligned. Non-BFP n is 1..1024; BFP n is 128, 256, 512 or
1024, with one UNPACR per face and dvalid only on the final face. BFP address begins
at the exponent section. A Src bank holds up to a tile; A/B each have two banks.
Math waits for valid banks and releases them explicitly. For face-at-a-time code,
`n=256, dvalid` publishes each face separately; the next face starts at Src row zero.

SrcA and SrcB banks are independent (measured,
`blackhole-py-old/tests/probes/probe_srcb_release.py`): an unpack to A neither
publishes nor overwrites a B bank, and `math.mova2d` does not wait for B. A copy
to Dst is therefore `unpack.move a, ..., dvalid` on the unpack side and
`math.mova2d` followed by `math.rwc release=a` on the math side; nothing is
published to or released from B. **Release only banks that were published.**
Releasing B when math holds no valid B bank does not wait and does not fail: it
moves math's B bank pointer one bank out of step with the unpacker, and the error
persists into later kernels (an odd number of such releases leaves it, an even
number cancels it). Every `release=` must match a `dvalid` publication on the same
path; the checker rejects a `release=b` with no B publication it can see.

The helper must acquire the selected base context before writing it and return
credit only when safe. A global “at most two outstanding” count is not sufficient
for repeated use of the same context. The exact context-update recipe still needs
confirmation. Shape changes emit their required counter setup; the listing shows it.

The unpack context offsets (`CfgContextOffset` for A and B) are fixed for the whole
program at their launch value 0; no v1 operation changes them. They share
ThreadConfig word `UNPACK_MISC_CFG` with the context-counter reset bits, and
`SETC16` cannot mask, so the reset recipe (`SETC16` offsets | reset bit,
`UNPACR_NOP` delay, `SETC16` offsets) writes those constants. An operation that
changes offsets must keep them one value per program, so that every write of this
word can use them without tracking.

Pack n is a multiple of 64 up to 1024; BFP uses the same restricted counts as unpack.
The Dst row is a multiple of 64 (a tile start) for `pack.move`. Output formats currently designed:
`bf16 fp32 e4m3 bfp8 bfp4`. Input `fp32 bf16 fp16 bfp8` is format-pair dependent;
BFP input selectors `bfp4`/`bfp2` are rejected. For BFP output, input `fp32` means no
prerounding, `bf16` seven bits, `bfp8` six bits; these are hardware conversion modes,
not a declaration that all three use the same Dst storage width.

Plain pack emits inline PACRs, resetting its counters at the end. The hardware regression checks BF16/FP32 and constant-one BFP8, BFP4 and E4M3 outputs. The block-format checks use 128 and 1024 datums.

`pack.gather` packs individual datums: one single-datum PACR per row, all one tile,
written to consecutive elements starting at p. `row` is a logical Dst row across
tiles (64 per tile), `col` 0..15; both may be runtime expressions. n is 1..64, and
`row + (n-1)*step` must stay in Dst. `n=1` is a single value.

- The packer writes whole 16-byte blocks, so p need not be aligned: the helper
  splits it into its 16-byte block and the slot within it (at runtime if p is
  runtime). The block's slots before p are written as zeros (ZeroWrite), and the
  rest of the final block is zero-filled.
- Footprint: from the start of p's block to the end of the final block, plus up to
  16 more bytes when the tile's input ends 16 bytes into a 32-byte unit (PACR tail
  completion). The compiler reports this range; L1 in it is overwritten.
- `acc` sets Pack_L1_Acc: L1 += packed. All the zeros then add nothing, so only
  elements p .. p+n-1 change, and they become old + datum. Preconditions: the
  target slots hold +0 beforehand, written and visible before the pack; neighbours
  in the footprint are +0 or normal numbers (−0, NaN and denormal neighbours are
  unverified under +0).
- Measured pairs only, from 32-bit Dst (`math.fmt dst=fp32`): `pack.fmt` in/out
  `fp32`/`fp32`, `fp32`/`bf16`, `bf16`/`bf16`. Other pairs, 16-bit Dst and widening conversions
  (which zero-fill further) are rejected until probed.

Scalar masks, transpose-B, tilize, strides, packer zero fill and other advanced modes
remain named native config/instruction work pending the pack/unpack audit.
No compiler-generated numerical conversion or layout conversion is implicit.

## 10. Math and SFPU

Native instructions have named operands and enum values; integer modifier codes
and complete instruction words are backend details. Fields accepting runtime values
build words explicitly. Each `math.*` / `sfp.*` statement below emits exactly the
native instruction(s) its row names. Nothing is inserted between statements: no
NOPs, stalls or reordering (§10, Scheduling).

### Math (FPU)

| Operation | Native | Meaning / defaults |
| --- | --- | --- |
| `math.fmt dst=fp32\|bf16, sfp=fp32\|bf16` | `RMWCIB`, `SETC16` | Dst storage and default SFPU transfer format; sfp defaults to the Dst format |
| `math.cfg dst_offset=rows` | `SETC16` | Add logical row offset to math and SFPU Dst addressing |
| `math.elwmul [dst[row]]`, `math.elwadd`, `math.elwsub` | `ELWMUL` / `ELWADD` / `ELWSUB` | Optional destination, default `dst[0]`; `addr=hold`, `release=none`, `accumulate` off, `broadcast=none\|column\|row\|scalar` |
| `math.mvmul [dst[row]]` | `MVMUL` | `Dst[row..row+8] += SrcB[8 rows] @ SrcA[16×16]`; `addr=hold`, `release=none` |
| `math.mova2d [dst[row]], src=r` | `MOVA2D` | Copy SrcA rows to Dst; `rows=8` (default) or `1`; `src=0`, `addr=hold` |
| `math.zero face=i, fmt=fp32\|bf16` | `ZEROACC` | Face invalidation for accumulation identity, not physical zero fill |

ZEROACC marks rows invalid; SFPU loads need actual valid data. Its named lowering
must preserve the working face-clear recipe until the encoder/manual discrepancy
is resolved. Do not change that encoding by guessing from raw argument names. A
whole-tile clear is `repeat f in 0..4 { math.zero face=f, ... }`.

`math.mova2d` with `rows=8` moves an aligned 8-row block (`dst` row and SrcA row
are rounded down to multiples of 8); `rows=1` moves one row. On Blackhole an odd
address-modifier slot turns the one-row form into an undocumented four-row move, so
`rows=1` with an odd `addr` slot is an error. With `math.fmt dst=fp32` the move
writes 32-bit Dst datums, but SrcA holds at most TF32: FP32 data that reaches Dst
through SrcA keeps 10 mantissa bits (open item, §12).

#### Matrix products

`math.mvmul` computes `Dst += SrcB @ SrcA` on one 8×16 block of the left operand
and one 16×16 face of the right: the **left** operand of a product is unpacked to
**SrcB** (`unpack.move b`), the **right** operand to **SrcA** (`unpack.move a`).
Blackhole aligns the SrcA row counter to 16 (one face); SrcB and Dst step by 8.
A 32×32 tile product per fidelity phase is 16 instructions: for each of the four
output faces, two K faces × two 8-row halves. The counter order that visits them
is author-written with `math.addrmod` (reference recipe:
`blackhole-py-old/ttko/fpu.py`, `matmul`). Each instruction consumes at most 5
mantissa bits of SrcA and 7 of SrcB; further fidelity phases (fidelity counter
0..3, advanced by an addrmod) add precision. The number of phases is the author's
precision choice. `math.zero` beforehand gives `=` instead of `+=`.

`unpack.fmt a, transpose` transposes **within** each 16×16 face and leaves the
faces in place. A whole-tile transposed right operand, as in `Q @ Kᵀ`, also needs
the off-diagonal faces (1 and 2) exchanged, which the author does by stepping the
SrcA counter by 32 instead of 16 between K faces (and by 16 instead of 32 between
output columns). Acceptance test: an asymmetric 32×32 input, where a swapped
operand or a missing face exchange changes the result.

### SFPU registers

L0–L7 are physical working registers. Named constants: `zero` (L9), `one` (L10),
`neg_one` (L11), `const_0_8373` (L8). L12–L14 are programmable via `sfp.const`.
`lane_x2` (L15) is the read-only lane sequence 0,2,...,62, not a fourth programmable
constant. L16 is available only within SFPMACRO. These names are SFPU operands
only; scalar code has no register names.

```text
alias m = l0
alias scale = l12
```

`alias name = reg` names a physical SFPU register for the rest of the enclosing
block (a function, macro or `{}`); it is a statement, not a declaration. It renames
only: nothing is allocated, saved or checked, and two aliases may name one
register. An alias follows variable scoping (§5) and shares the local namespace.

### SFPU lanes and Dst

The SFPU has 32 lanes. A Dst address `a` (the instruction's row, plus
`math.cfg dst_offset`, plus the Dst counter, plus the SFPU base) selects an aligned
group of four Dst rows, `a & ~3`, and a column parity, bit 1 of `a`; bit 0 is
ignored. Lane `l` reads or writes

```text
Dst row    = (a & ~3) + l / 8
Dst column = 2 * (l % 8) + ((a >> 1) & 1)
```

so one `sfp.load` covers 4 rows × 8 columns, the even or the odd columns of a
16-wide Dst row. A 32×32 tile occupies 64 Dst rows as four 16×16 faces in order
(top-left, top-right, bottom-left, bottom-right). With `t = a % 64`, `F = t / 16`:

```text
tile row    = (F / 2) * 16 + (t % 16 & ~3) + l / 8
tile column = (F % 2) * 16 + 2 * (l % 8) + ((a >> 1) & 1)
```

A full tile is 32 addresses: 4 faces × 4 row groups × 2 parities, i.e.
`a = 16*F + 4*g + 2*p`. `dst.tile` (64) and `dst.face` (16) are read-only
constants for writing these addresses. `lane_x2 & 15` is `2 * (l % 8)`; adding the
parity and `16 * (F % 2)` gives each lane's tile column. Lane `l` is in SFPU row
`l / 8` (an eight-lane group): `sfp.shft2 rotate`, `sfp.transp` and the reduction
butterflies work on these groups.

### SFPU instructions

Operands: `rd` is written, `a b c` are read. Registers are any of L0–L15 when read
and L0–L7 when written, unless the row says otherwise. Where the native instruction
reads its destination, the row writes `rd` in that source position and the
compiler checks that the same register is given there. Integer instructions work
on two's-complement 32-bit lanes; float instructions on FP32. Every instruction
writes only enabled lanes (§10, Predication) unless the row says otherwise.

| Operation | Native | Meaning |
| --- | --- | --- |
| `sfp.load rd, dst[a]` | `SFPLOAD` | `fmt=` `fp32 bf16 fp16 i32` overrides the configured transfer format; `addr=hold` |
| `sfp.store dst[a], a` | `SFPSTORE` | Same `fmt`/`addr` rules. Marks all four rows of the group defined, even lanes it does not write |
| `sfp.li rd, value` | `SFPLOADI` ×1–2 | Below |
| `sfp.mov rd, a` | `SFPMOV` | `neg` flips the sign bit; `all` writes every lane regardless of predication |
| `sfp.mad rd, a, b, c` | `SFPMAD` | `rd = ±(a·b) ± c`; `neg_ab`, `neg_c` |
| `sfp.mul rd, a, b` | `SFPMUL` | `rd = ±(a·b) + 0` (−0 becomes +0); `neg` |
| `sfp.add rd, a, b` / `sfp.sub rd, a, b` | `SFPADD` | `rd = 1·a ± b` |
| `sfp.addi rd, rd, k` | `SFPADDI` | `rd = k + rd`; k a float constant exact in BF16; `neg` negates rd first |
| `sfp.muli rd, rd, k` | `SFPMULI` | `rd = rd·k + 0`; k exact in BF16; `neg` |
| `sfp.recip rd, a` | `SFPARECIP` | Approximate `1/a` (refine with `sfp.mad`) |
| `sfp.aexp rd, a` | `SFPARECIP` | Approximate `e^a` |
| `sfp.rnd rd, a, to=bf16\|fp16` | `SFPSTOCHRND` | Round the FP32 mantissa to 7 / 10 bits, result stays FP32; `mode=nearest` (default) `\|zero\|stoch`; zero/denormal → 0, Inf/NaN → ±Inf |
| `sfp.cast rd, a` | `SFPCAST` | Sign-magnitude integer → FP32, round to nearest even; `stoch` |
| `sfp.abs rd, a, int\|float` | `SFPABS` | Two's-complement or FP32 absolute value |
| `sfp.iadd rd, a, rd` / `sfp.iadd rd, a, k` | `SFPIADD` | `rd = a + rd` / `rd = a + k`, k in −2048..2047. Never changes lane flags |
| `sfp.isub rd, a, rd` | `SFPIADD` | `rd = a − rd`. Never changes lane flags |
| `sfp.shl rd, a, n` / `sfp.shr` / `sfp.sar` | `SFPSHFT` | Shift by constant n in 0..31: left, logical right, arithmetic right |
| `sfp.shift rd, rd, a` | `SFPSHFT` | Shift rd by a's signed lane value: left if ≥ 0, logical right by −a otherwise; `arith` for arithmetic right |
| `sfp.and rd, a, b` / `sfp.or rd, a, b` | `SFPAND` / `SFPOR` | Bitwise |
| `sfp.xor rd, rd, a` / `sfp.not rd, a` | `SFPXOR` / `SFPNOT` | Bitwise |
| `sfp.exexp rd, a` | `SFPEXEXP` | Exponent field as an integer, minus 127; `raw` for 0..255 |
| `sfp.exman rd, a` | `SFPEXMAN` | Mantissa in bits 0–22, hidden bit 23 set; `hidden=0` clears it |
| `sfp.setexp rd, a, e` | `SFPSETEXP` | Sign and mantissa of a, exponent e: a constant 0..255, or `rd` with `from=int` (low 8 bits, default) or `from=fp32` (rd's exponent field) |
| `sfp.setsgn rd, a, s` | `SFPSETSGN` | Exponent and mantissa of a, sign s: constant 0/1, or `rd` (its bit 31) |
| `sfp.minmax lo, hi` | `SFPSWAP` | `lo = min`, `hi = max` in FP32 / sign-magnitude total order; equal values may be exchanged. `hi` may be a constant register (L8–L15), which is read but not written: `sfp.minmax x, one` clamps x to ≤ 1. Both in L0–L3 under `sfp.index` |
| `sfp.swap x, y` | `SFPSWAP` | Exchange x and y |
| `sfp.shft2 rd, a, rotate` | `SFPSHFT2` | Rotate right by one lane within each eight-lane group |
| `sfp.transp` | `SFPTRANSP` | Transpose the 4×4 lane groups of L0–L3 and of L4–L7 |
| `sfp.const rd, value` | `SFPLOADI` ×2, `SFPCONFIG` | Program L12–L14 (via L0, which it overwrites) |
| `sfp.nop` | `SFPNOP` | One idle SFPU cycle |

Comparisons and compare-against-zero are not separate operations; they exist only
as `sfp.if` conditions, so lane flags change only where the source shows a
predicate.

```text
sfp.li l0, 1.0
sfp.li l4, -inf
sfp.li l2, valid_columns, fmt=i32
sfp.li l6, scale, fmt=fp32
```

`sfp.li` accepts a complete constant or a scalar expression, hiding SFPLOADI's
halfword encoding. Default fmt is fp32; integer formats are i32/u32. Constant
numeric values are encoded at compile time; a runtime fp32 operand already holds
float bits, with no integer-to-float conversion. Both halves obey current lane
predication; inactive lanes retain their old values. The operation does not change
predicate state. Unsupported forms/ranges are errors, not truncation.

### Predication

```text
sfp.if col >= tail {
    sfp.store dst[a], neg_inf_reg, fmt=fp32
}
sfp.if delta == 0 { sfp.mov value, one } else { sfp.mov value, value }
```

`sfp.if cond { ... } [else { ... }]` runs its body with only the lanes where `cond`
holds enabled; `else` runs with the remaining previously enabled lanes; `else if`
nests. Conditions:

| Condition | Native | Meaning |
| --- | --- | --- |
| `a < 0`, `a >= 0`, `a == 0`, `a != 0` | `SFPSETCC` | Tests a's 32 bits as a two's-complement integer: sign bit, all-zero. For FP32, −0 is `< 0` and not `== 0` |
| `a > b`, `a <= b`, `a < b`, `a >= b` | `SFPGT` / `SFPLE` | FP32 total order (−NaN < −Inf < … < −0 < +0 < … < +NaN), which is also sign-magnitude integer order. Agrees with two's-complement order only when both are ≥ 0 |

The operand the native compare reads through its destination field (the left
operand of `>` and `<=`, the right operand of `<` and `>=`) must be L0–L11: with
L12–L14 there the instruction is a backdoor template write, not a compare.

An outermost `sfp.if` lowers to `SFPENCC` (enable predication, all flags set), the
compare, the body, `SFPCOMPC` and the else body, then `SFPENCC` (disable, all flags
set). A nested `sfp.if` lowers to `SFPPUSHC`, the compare, the body, `SFPCOMPC`
and the else body, `SFPPOPC`. A compare updates only enabled lanes, so nested
conditions narrow the outer ones. At most eight `sfp.if` are nested inside an
outermost one (the flag stack holds eight). The listing shows every instruction.

Every SFPU instruction writes only enabled lanes, except `sfp.mov all`. The body
may contain SFPU operations, `repeat`, macro uses and nested `sfp.if`. It may not
contain `sfp.cfg`, `sfp.index`, `sfp.const` (SFPCONFIG uses lane flags differently),
non-SFPU device operations, or a `break`, `continue` or `return` that leaves it.
Predication is SFPU-local state that a function call does not change; an `sfp.if`
may contain a call only if the callee's body obeys the same rules.

`sfp.store` under predication still marks all four rows of its group defined
(table above): store to rows that hold valid data, or write them first.

Acceptance test: the attention tail. For every valid-column count 1..32, masked
columns become `-inf`, live columns keep their exact bits, and an instruction after
the `sfp.if` reaches every lane.

### Lane configuration and index capture

`sfp.cfg` writes named fields of the per-lane SFPU configuration (`LaneConfig`):

| Field | Meaning |
| --- | --- |
| `load_odd` / `store_odd` | `sfp.load` / `sfp.store` always use odd columns |
| `block_load` / `block_store` | `sfp.load` does not write LRegs / `sfp.store` does not write Dst |
| `invert_minmax` | `sfp.minmax` computes `lo = max`, `hi = min` |
| `fp16_inf` | FP16 loads interpret the max exponent as infinity |
| `row_mask=m` | Disable SFPU row `r` (lanes 8r..8r+7) where bit r of m (0..15) is set |

Booleans are `name` / `name=0`; as with `.cfg` (§8), a write changes only the
fields it names: one `SFPCONFIG` AND clearing them, then one OR setting them,
omitting either when it would do nothing. The launch value of every field is 0.
`sfp.cfg` may not appear inside `sfp.if`.

```text
sfp.index capture {
    repeat ... { sfp.load l1, dst[a], fmt=fp32; ...; sfp.minmax l1, l0 }
}
```

`sfp.index paired|capture { ... }` enables index mode for its body (an `SFPCONFIG`
OR at entry, AND at exit; the index bits are not `sfp.cfg` fields). Each value
register L0–L3 has an index register L4–L7 (`l0`↔`l4`, …):

- `paired`: `sfp.minmax lo, hi` with both operands in L0–L3 moves the paired index
  registers with the values, so each index follows its value.
- `capture`: additionally, `sfp.load` into L0–L3 writes the physical Dst index of
  each lane's datum, `row * 16 + column` (absolute Dst row and column, §10 lanes),
  into the paired register. Which logical element that is depends on the tensor
  layout, and converting it is the kernel's job.

Inside the body, only `sfp.load`, `sfp.li`, `sfp.minmax`, `sfp.swap` and
`sfp.transp` may write L4–L7 (hardware restriction TEN-2932); `sfp.minmax` and
`sfp.swap` operands must be in L0–L3. `sfp.index` cannot nest, may not appear
inside `sfp.if`, and its body follows the `sfp.if` body rules otherwise.

Acceptance test: argmax with equal winning BF16 keys placed in different lanes,
faces, tiles and workers; the lowest logical token ID must win.

### Scheduling

The compiler inserts no `sfp.nop` and no stall. Blackhole stalls automatically
after `SFPMAD`-family results (mad, mul, add, addi, muli), `SFPSWAP` and the
rotating `SFPSHFT2` modes, except in the cases the ISA lists as undetected:
an `SFPMAD` result read by `sfp.iadd`/`sfp.isub`/`sfp.shift`/`sfp.shl`-family,
`sfp.setexp`/`sfp.setsgn` (reading rd), `sfp.and`/`sfp.or`, `sfp.recip`, the
compare of `sfp.minmax`, `sfp.shft2`, or `SFPCONFIG` reading L0 (`sfp.const`,
`sfp.cfg`); and nothing is automatic inside `sfpmacro`. In those cases the author
writes `sfp.nop`. Existing kernels' NOPs are kept until a hazard probe shows they
are unneeded. A later checker may reject missing ones; it will not insert them.

### Counters and address modifiers

`math.rwc` controls `srca`, `srcb`, `dst`, `fidelity`, `sp`. Src rows are 0..63;
Dst/sp fields are 0..1023 subject to storage/footprint bounds; fidelity is 0..3.
Each position counter has a carriage-return copy `cr`:

| Form | Effect |
| --- | --- |
| `c+=n` | Advance current value, retain cr |
| `c=n` | Set current and cr |
| `c=cr+n` | Set current and cr to old cr+n |
| `dst=c+n` | Set current and cr to old current+n |

`math.addrmod name, slot=1..7, ...` writes the slot at its source location and names
it. Use `addr=name` or `addr=slot` on the consuming instruction. Omitted counters mean +=0.

Slot 0 is reserved as `hold`: it changes no counter. Its launch value is all-zero
(§12) and `math.addrmod` cannot write it, so it needs no setup and emits nothing.
Every instruction with an address-modifier field (math instructions, `sfp.load`,
`sfp.store`, `sfpmacro.run`, and the same instructions inside templates) uses
`hold` when `addr=` is omitted. Slot 0 is also even, so it is valid for
`math.mova2d rows=1`.
Addrmods accept src increments 0..63, dst 0..1023, fidelity 0..3; absolute assignments
are =0 only. CR forms are allowed; current-to-CR is Dst-only. SFPU never updates fidelity.
Template addrmod names resolve at load in the using function; ambiguous bindings error.

`math.rwc` with only += uses INCRWC (increments 0..15); assignment forms use SETRWC.
Mixing both classes is an error. Fidelity permits =0. `math.rwc reset` is
`srca=0, srcb=0, dst=0, fidelity=0`, and options can follow it
(`math.rwc reset, release=a|b`). `release=a|b` releases Src
banks. The compiler does not move math counters on the author's behalf.

## 11. Hardware templates

These differ from source macros: they occupy hardware resources and must be loaded.
Definitions are file-level; operands must be constant after source-macro expansion.
Run before load on any path is an error. Replacing a template requires its previous
use to be finished; loads implement their documented resource-safety waits.

| Definition / install / run | Contract |
| --- | --- |
| `replay name { ... }`, `replay.load name`, `replay.run name` | Record/replay a constant instruction body; per-TRISC buffer, at most 32 words |
| `mop name, outer=, inner= { ... }`, `mop.load name`, `mop.run name` | Per-TRISC MOP state; load waits for prior MOP, then writes config |
| `sfpmacro name, slot=0..3 { ... }`, `sfpmacro.load name`, `sfpmacro.run name, reg, dst[row]` (`addr=`, default `hold`) | Configure delayed SFPU operations |

Bodies are one `label: instruction` per line (replay bodies are plain instructions).

Replay placement is deterministic; total resident bodies must fit. Installing one
must not silently overwrite another live body. A MOP can invoke replay; a replay
cannot invoke MOP. Expanded instructions must fit the engine and native template
slots: an operation that lowers to several words cannot occupy one MOP slot.

Loop MOP: header options `outer=` (1..1023) and `inner=` (0..1023); labels `start`,
required `loop0`, optional `loop1`, `last_inner`, `last`, `end0`, `end1`. `start`
runs per outer pass; inner zero requires it. `loop1` alternates with `loop0` for 2n
steps. `last_inner` replaces the last inner step of nonfinal passes (default: the
loop instruction at that step); `last` replaces the final pass's last step
(default: `last_inner`). End slots run after each outer pass. Unspecified slots
contain plain skipped NOPs.

Mask MOP: `mop name, mask { ... }` with labels `a`, `b`, `skip_a`, `skip_b`. `a`
contains one or four instructions; optional b follows. Mask-bit 1 selects
skip_a/skip_b instead. Run with `mop.run name, n=1..128, mask=value`; n and mask may
be runtime expressions. The mask is 32 bits; steps beyond 31 read zero. Required
MOP_CFG updates are shown in the listing. Loop-MOP counts are fixed at installation.

In SFPMACRO bodies `x` is a contextual operand keyword for the loaded register, like
`a`/`b` elsewhere (§2); it does not clash with a file-level `x`.

SFPMACRO labels are the units `simple mad round store`, one line per unit, with `delay=0..7`
(cycles after load, plus one) or `after=n` (subsequent SFPU instructions). Timing
mode is shared per unit. Enough SFPU instructions must follow an `after` schedule
on every path. Destination is loaded register `x` or L16; x occurs exactly once as
VB or VC input. Store uses the loaded row, optionally L16, with a shared store format.
At most four distinct non-store instructions occupy shared instruction slots.
The implementation must check cross-macro/unit collisions and clobbers, not just
individual macro bodies. Loads involving round/store clobber L0 and emit SFPNOP.
Register group L0–L3 requires even effective load address, L4–L7 odd; addrmod applies
to the load only. Detailed timing/encoding limits remain in the hardware reference.

## 12. Launch state, diagnostics and remaining audits

Before any entry runs, runtime establishes zero config/thread-config/counters,
empty CBs, Src banks owned by unpack, semaphores value 0/max 1 except reserved
helper credits, all SFPU lanes enabled, predicates reset, the flag stack empty and every
`sfp.cfg` / `sfp.index` field 0. Dst is invalidated
for accumulation, not initialized for arbitrary SFPU loads. SFPU working registers
and scratch are undefined; programmable constants/templates are not loaded. `keep`
regions retain their contents. Firmware initializes named fixed SFPU constants.
These are runtime obligations; ordinary function calls do none of this.

Reject invalid operands, engine misuse, use before initialization, impossible
resource allocation, known layout/alignment violations and unsupported hazardous
modes. Check template installation and semaphore initialization through branches,
loop fixed points, calls and expanded templates; config values are not tracked (§8).
Give stable diagnostic IDs and bounded compile time. Do not claim to prove arbitrary
runtime bounds or distributed liveness. Debug runs and correctness tests cover these.

The consolidated design intentionally leaves these audits open:

1. SFPU hazards: probe the undetected-stall cases of §10 Scheduling and the
   existing kernels' NOPs. Hardware-probe each §10 instruction row, `sfp.if` and
   `sfp.index` against its acceptance test.
2. Pack/unpack advanced named fields, base-context reuse and BFP exponent variation;
   `pack.gather` with fp16 output, 16-bit Dst, and −0/NaN/denormal neighbours under
   `acc`; a packer zero-fill (`ZeroWrite`, whole rows) for preparing `acc` targets.
3. ZEROACC's encoder/manual discrepancy and exact format-dependent Dst address
   interpretation.
4. Multicast payload/notification ordering and partial NoC-write alignment rules,
   including whether DRAM writes must split at 16-element boundaries as the
   existing scatter does. The KV-cache append (32-byte rows into tiled cache pages)
   and the attention context write depend on it.
5. The endpoint ABI, resource reservations, code-slot limits and numerical/performance
   validation of actual compiled Llama3 ports.
6. FP32 data into Dst. Unpack offers FP32 only as `out=bf16|fp16`, and SrcA holds
   at most TF32, so the attention merge's FP32 (O, m, l) states lose mantissa bits
   on the way into Dst. Decide between an unpack-to-Dst path and accepting TF32.
7. Decided: parameters are host-bound per graph run (§4), so the old argmax's
   device-side publication of next-token parameters is dropped. Its per-launch
   zeroing of partial slots becomes `keep` slots with generation counters. Audit
   remaining: the cost of one host round trip per token versus the old autonomous
   replay.
8. `sfpmacro` coverage of the RMSNorm apply macro, which installs an `SFPMUL`
   template through the backdoor `CONFIG0` write.

No raw instruction-word construction is required in accepted application source.
Backend encoding tools remain available for probes. An unreviewed hardware field
is not made supported merely by accepting its integer bit pattern.
