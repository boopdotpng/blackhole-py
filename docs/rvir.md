# RVIR: Layer-2 RISC-V IR

`rvir.py` is the layer-2 API on top of `dsl.py`.

It is not a compiler IR in the LLVM sense. It is a structured assembler for writing
small Blackhole firmware programs in Python while preserving direct control over the
generated RISC-V.

## Goals

- Build on top of `dsl.py`, which remains the layer-1 raw encoder.
- Keep the generated code close to handwritten firmware.
- Support functions, labels, fixups, frames, and loops.
- Make MMIO-heavy firmware ergonomic with pinned base registers.
- Allow raw `dsl.py` instructions anywhere as an escape hatch.

## Non-goals

- No SSA.
- No register allocation.
- No optimization passes.
- No instruction scheduling.
- No hidden control flow.
- No auto-detection of used registers.

## Layering

1. `dsl.py`
   Raw encoders only. Given concrete register numbers and immediates, emit one
   encoded instruction word. Owns register name bindings (`zero`, `ra`, `sp`,
   `s0`, `a0`, `t0`, etc.).
2. `rvir.py`
   Structured assembler for RISC-V firmware. Imports registers from `dsl.py`.
3. `ttir.py`
   Higher-level Tensix helpers and firmware convenience routines (`wait_u8`,
   `memzero`, `copy_words`, etc.) that lower into RISC-V stores or raw TT words.

## Core model

An `rvir` program is a set of functions plus an entry symbol.

Each function contains a linear list of items:

- concrete RISC-V instructions (via `dsl.py` encoders)
- labels (assembler-time names for instruction addresses)
- fixups (unresolved branch/jump targets)

During assembly:

1. functions are laid out in declaration order (entry function first)
2. label PCs are assigned
3. fixups are resolved into branch and jump immediates
4. final instructions are encoded through `dsl.py`

## Registers

Registers live in `dsl.py`. `rvir.py` re-exports them for convenience.

```python
# from dsl.py
zero, ra, sp, gp, tp
t0, t1, t2, t3, t4, t5, t6
s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11
a0, a1, a2, a3, a4, a5, a6, a7
fp = s0
```

## Calling convention

Standard RV32 ABI-style:

- `a0-a7`: args and return values, caller-saved
- `t0-t6`: temporaries, caller-saved
- `s0-s11`: callee-saved
- `ra`: return address, saved by non-leaf functions
- `sp`: stack pointer
- `gp`: fixed global pointer

`rvir` never silently saves or restores registers.

## API shape

```python
from rvir import *
from dsl import *

fw = Program(entry="_start")


@fw.func("_start")
def _start(f):
    f.li(gp, 0xFFB007F0)
    f.li(sp, 0xFFB01FF0)
    f.call("init")
    f.call("main")
    f.halt()


@fw.func("init", save=[ra, s0, s1])
def init(f):
    f.pin(s0, MMIO.TILE)
    f.pin(s1, MMIO.NOC0)

    f.li(t1, 2)
    f.csrs(CSR.cfg0, t1)
    f.fence()

    f.sw(zero, s0, TILE.DEST_CG_CTRL - MMIO.TILE)
    f.lw(a0, s1, NOC.NODE_ID)
    f.ret()


@fw.func("main", save=[ra, s0, s1, s2])
def main(f):
    f.pin(s0, MMIO.TILE)
    f.pin(s1, MMIO.TENSIX_T0_PUSH)
    f.pin(s2, MMIO.TENSIX_SEM)

    f.raw(dsl.ADDI(int(a0), int(zero), 1))

    with f.loop("idle") as loop:
        f.fence()
        loop.continue_()


blob = fw.assemble()
```

## `Program`

Plain constructor, not a context manager.

```python
fw = Program(entry="_start")
```

- `entry`: name of the entry function (must be declared first)
- Functions are laid out in declaration order
- `fw.assemble()` resolves fixups and returns `bytes`

## `@fw.func(name, save=[...])`

Decorator that defines a function. The decorated Python function receives a
`Function` builder and is called immediately.

```python
@fw.func("init", save=[ra, s0, s1])
def init(f):
    ...
```

- `name`: function label
- `save`: list of registers to save in prologue and restore in epilogue.
  The user must explicitly list every callee-saved register they use.
  If a function does not need a frame (e.g. `_start`), omit `save`.

When `save` is provided, the decorator emits:

- **prologue**: decrement `sp`, store each register in `save` to the stack
- *(function body)*
- **epilogue**: restore each register, increment `sp`, `ret`

When `save` is omitted, no prologue/epilogue is emitted. The function body
is responsible for its own return (e.g. `f.halt()` or `f.ret()`).

## Instruction delegation

`Function` uses `__getattr__` to delegate to `dsl.py` encoders:

```python
class Function:
    def __getattr__(self, name):
        encoder = getattr(dsl, name.upper(), None)
        if encoder is None:
            raise AttributeError(f"no instruction: {name}")
        def emit(*args, **kwargs):
            self.items.append(encoder(*args, **kwargs))
        return emit
```

This means every instruction in `dsl.py` is automatically available as
`f.<lowercase>(...)` with no wrapper code. `f.sw(...)` calls `dsl.SW(...)`,
`f.fence()` calls `dsl.FENCE()`, etc.

Methods defined explicitly on `Function` (like `li`, `pin`, `call`, `label`,
`ret`, `halt`, loops) take priority over `__getattr__`.

## Explicit `Function` methods

### `f.li(rd, imm)`

Load immediate. Handles the full 32-bit range:

- If `imm` fits in 12 bits signed: emits `ADDI(rd, zero, imm)`
- Otherwise: emits `LUI(rd, upper) + ADDI(rd, rd, lower)`

Sign-extension of the lower 12 bits must be accounted for in the upper
20 bits (add 1 to upper if bit 11 of imm is set).

### `f.pin(reg, addr)`

Shorthand for `f.li(reg, addr)`. Emits the LUI+ADDI sequence to load
a 32-bit MMIO base address into `reg`. Returns `reg`.

```python
tile = f.pin(s0, MMIO.TILE)   # tile is just s0
f.sw(zero, tile, offset)       # same as f.sw(zero, s0, offset)
```

No wrapper type. `pin()` records the register internally so that
double-pinning the same register is an error.

### `f.label(name)`

Place a label at the current position.

```python
f.label("wait_go")
f.lbu(a5, s0, GO_MSG_OFFSET)
f.li(t0, 128)
f.bne(a5, t0, "wait_go")
```

### `f.call(name)`

Emit `JAL(ra, name)` with a fixup to be resolved at assembly time.

### `f.j(name)`

Emit `JAL(zero, name)` with a fixup.

### `f.ret()`

Emit `JALR(zero, ra, 0)`.

### `f.halt()`

Emit an infinite loop: `label(".halt"); j(".halt")`.

### `f.raw(insn)`

Append a pre-encoded instruction directly.

```python
f.raw(dsl.ADDI(int(a0), int(zero), 1))
```

### Absolute address loads and stores

For loads, `rd` itself is used as scratch to hold the address:

```python
f.lw_abs(a5, 0xFFB00100)
# lowers to: LUI(a5, hi), LW(a5, a5, lo)
```

For stores, a scratch register is required because `rs2` (the value) cannot
be clobbered:

```python
f.sw_abs(a0, 0xFFB00100, scratch=t0)
# lowers to: LUI(t0, hi), SW(a0, t0, lo)
```

## Branch and jump fixups

When a branch or jump references a label name instead of a numeric offset,
`Function` records a fixup:

```python
(item_index, target_label, fixup_kind)
```

Where `fixup_kind` is one of:

- `B_TYPE` — 12-bit signed offset, encoded in B-type immediate fields
- `JAL` — 20-bit signed offset, encoded in J-type immediate fields

During `assemble()`:

1. All functions are concatenated in declaration order
2. Label PCs are computed (each instruction is 4 bytes)
3. Each fixup is resolved: `offset = target_pc - fixup_pc`
4. The instruction word is re-encoded with the resolved offset
5. Out-of-range offsets are a hard error
6. Undefined labels are a hard error

Forward references within and across functions are supported.

## Loops

Context managers for structured loops. These are the only constructs that
use `with`.

### `f.loop(name)`

Unconditional loop. Emits a top label and (at exit) an unconditional jump
back.

```python
with f.loop("idle") as loop:
    f.fence()
    loop.continue_()      # jump to top
    # or:
    loop.break_()         # jump past end
    loop.break_if_eq(rs1, rs2)
    loop.break_if_ne(rs1, rs2)
```

Lowering:

- `label("{name}")` at entry
- body
- `j("{name}")` at exit
- `label("{name}_end")` after the jump

`break_()` emits `j("{name}_end")`.
`break_if_eq(rs1, rs2)` emits `beq(rs1, rs2, "{name}_end")`.
`continue_()` emits `j("{name}")`.

### `f.for_range(reg, start, end, step=1)`

Counted loop with an explicit induction register.

```python
with f.for_range(t0, 0, 64, step=4):
    f.sw(zero, s0, t0)    # t0 is the induction variable
```

Lowering (for positive step):

```
li    reg, start
label "{name}"
body
addi  reg, reg, step
li    scratch, end         # or use blt with immediate if end fits
blt   reg, scratch, "{name}"
label "{name}_end"
```

The context manager does not yield anything. The induction variable is the
register you passed in.

A scratch register is needed for the end-of-range comparison if `end` does
not fit in a branch immediate. The API should accept an optional `scratch`
parameter, or use a convention (e.g. the register after `reg`).

## Required objects

- `Program`
- `Function`
- `Loop`

That's it. No `Frame`, no `PinnedBase`, no `Reg` wrapper, no `LabelRef`.

## Error model

Assembly fails hard with a clear message on:

- undefined label reference
- duplicate label definition
- branch offset out of 12-bit range
- JAL offset out of 20-bit range
- double-pinning a register
- `save` list contains duplicates

## Output

`fw.assemble()` returns `bytes`. This is directly compatible with writing
firmware blobs to L1 via the existing PCIe/TLB layer.

## Style rules

- Prefer explicit registers.
- Prefer explicit save lists.
- Prefer thin helpers over opaque abstractions.
- Keep raw `dsl.py` escape hatches available.
- Generate semantic labels so disassembly is readable.
