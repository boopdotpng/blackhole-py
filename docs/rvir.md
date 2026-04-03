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

## Layering

1. `dsl.py`
   Raw encoders only. Given concrete register numbers and immediates, emit one
   encoded instruction word.
2. `rvir.py`
   Structured assembler for RISC-V firmware.
3. `ttir.py`
   Higher-level Tensix helpers that lower into RISC-V stores or raw TT words.

## Core model

An `rvir` program is a set of functions plus an entry symbol.

Each function contains a linear list of items:

- concrete RISC-V instructions
- labels
- unresolved control-flow fixups
- assembler-time helpers that lower into the above

During assembly/lowering:

1. helpers are expanded into concrete items
2. label PCs are assigned
3. fixups are resolved into branch and jump immediates
4. final instructions are encoded through `dsl.py`

## Registers

`rvir.py` owns ABI register names and register-role conventions.

Example register names:

```python
zero, ra, sp, gp, tp
t0, t1, t2, t3, t4, t5, t6
s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11
a0, a1, a2, a3, a4, a5, a6, a7
fp = s0
```

Layer 1 only needs register numbers. Layer 2 adds names and policy.

## Calling convention

`rvir` uses a normal RV32 ABI-style convention.

- `a0-a7`: args and return values, caller-saved
- `t0-t6`: temporaries, caller-saved
- `s0-s11`: callee-saved
- `ra`: return address, saved by non-leaf functions that need it
- `sp`: stack pointer
- `gp`: fixed global pointer

`rvir` should not silently save `a*` or `t*` registers.

## Frames

Frames are explicit.

```python
Frame(save=[ra, s0, s1], local_size=32)
```

This means:

- allocate `local_size` bytes on the stack
- save the listed registers in the prologue
- restore them in the epilogue

If a function does not need a frame, it should be able to omit one.

## Pinned base registers

Firmware uses the same MMIO bases repeatedly. `rvir` should make this explicit.

```python
tile = f.pin(s0, MMIO.TILE)
noc0 = f.pin(s1, MMIO.NOC0)
t0q = f.pin(s2, MMIO.TENSIX_T0_PUSH)
```

Pinned bases are long-lived base registers used for repeated offset-based accesses.

This is preferred for fixed MMIO regions such as:

- tile debug/control registers
- NOC0/NOC1 register blocks
- Tensix instruction push ports
- Tensix semaphore windows

Pinned bases are not `.bss` globals. They are immediate constants loaded into a
register once and then reused.

## Labels and fixups

Labels are assembler-time names for instruction addresses.

The machine never jumps to a label directly. It jumps to a PC address encoded in a
branch or jump immediate.

`rvir` must support:

- function labels
- block labels
- internal loop labels
- user-defined semantic labels

Example:

```python
f.label("wait_go")
f.lbu_abs(a5, L1.GO_MSG)
f.li(t0, 128)
f.bne(a5, t0, "wait_go")
```

The `bne` cannot be fully encoded until label layout is known. `rvir` records a fixup,
then resolves it during lowering.

For the current firmware size, direct `jal` and branch fixups are enough. If a target is
out of range, assembly should fail with a clear error.

## Raw instruction escape hatch

`rvir` must allow raw `dsl.py` instructions anywhere.

```python
f.raw(dsl.ADDI(int(a0), int(zero), 1))
```

This keeps layer 2 honest and prevents it from becoming a closed abstraction.

## Program shape

The expected program shape is:

1. `_start`
2. initialization helpers
3. `main`
4. small helper functions

`_start` is a small bootstrap that typically:

- initializes `gp`
- initializes `sp`
- performs any required CSR setup
- calls `main`
- halts or spins forever

## Final product API

This is the intended shape of the final user-facing DSL.

```python
from rvir import *
from ttir import *
from bhdefs import *

fw = Program(entry="_start", base=L1.BRISC_FIRMWARE_BASE)


@fw.func("_start")
def _start(f):
    f.set_gp(0xFFB007F0)
    f.set_sp(0xFFB01FF0)
    f.call("init")
    f.call("main")
    f.halt()


@fw.func("init", frame=Frame(save=[ra, s0, s1], local_size=0))
def init(f):
    tile = f.pin(s0, MMIO.TILE)
    noc0 = f.pin(s1, MMIO.NOC0)

    f.li(t1, 2)
    f.csrs(CSR.cfg0, t1)
    f.li(t1, 1)
    f.slli(t1, t1, 18)
    f.fence()
    f.csrs(CSR.cfg0, t1)
    f.li(t1, 2)
    f.csrc(CSR.cfg0, t1)
    f.fence()
    f.fence()

    f.sw(zero, tile, TILE.DEST_CG_CTRL - MMIO.TILE)
    f.lw(a0, noc0, NOC.NODE_ID)
    f.ret()


@fw.func("main", frame=Frame(save=[ra, s0, s1, s2], local_size=0))
def main(f):
    tile = f.pin(s0, MMIO.TILE)
    t0q = f.pin(s1, MMIO.TENSIX_T0_PUSH)
    sem = f.pin(s2, MMIO.TENSIX_SEM)

    f.wait_u8(L1.GO_MSG, 128)

    f.raw(dsl.ADDI(int(a0), int(zero), 1))

    tt.push_t0(f, TT_NOP(), base=t0q)

    with f.loop("idle") as loop:
        f.fence()
        loop.continue_()


blob = fw.assemble()
elf = fw.to_elf()
```

## Required layer-2 objects

At minimum, `rvir.py` should define:

- `Program`
- `Function`
- `Frame`
- `Reg`
- `PinnedBase`
- `LabelRef`
- `Fixup`

## Required `Function` methods

### Structural

- `label(name)`
- `raw(insn)`
- `call(name)`
- `ret()`
- `halt()`

### Register and frame helpers

- `pin(reg, addr)`
- `set_gp(value)`
- `set_sp(value)`

### Pseudo-ops

- `li(rd, imm)`
- `mv(rd, rs)`
- `nop()`

### Integer and memory ops

- `add`, `addi`, `sub`
- `and_`, `andi`, `or_`, `ori`, `xor`, `xori`
- `sll`, `slli`, `srli`, `srai`
- `lw`, `sw`, `lbu`, `sb`, `lhu`, `sh`
- `lw_abs`, `sw_abs`, `lbu_abs`, `sb_abs`

### Control flow

- `beq`, `bne`, `blt`, `bge`, `bltu`, `bgeu`
- `j(name)`
- `jal(name)` or `call(name)`
- `jalr(rd, rs, imm=0)`

### CSR and misc

- `csrs(csr, rs)`
- `csrc(csr, rs)`
- `fence()`

### Common firmware helpers

- `wait_u8(addr, value)`
- `memzero(base, size)`
- `copy_words(dst, src, nwords)`

## Loop abstractions

`rvir` should include thin loop helpers. These are assembler conveniences, not a high-level
language runtime.

### 1. Raw label loop

Always supported.

```python
f.label("poll")
f.lbu_abs(a5, L1.GO_MSG)
f.li(t0, 128)
f.bne(a5, t0, "poll")
```

### 2. `loop()`

Lowest-level structured loop helper.

```python
with f.loop("idle") as loop:
    f.fence()
    loop.continue_()
```

Expected lowering:

- a top label
- the loop body
- an unconditional jump back to the top label

The loop object should support:

- `continue_()`
- `break_()`
- `break_if_eq(rs1, rs2)`
- `break_if_ne(rs1, rs2)`

### 3. `while_*()`

Best for polling loops.

```python
with f.while_ne(a5, 128, load=lambda: f.lbu_abs(a5, L1.GO_MSG), scratch=t0):
    f.fence()
```

This should lower to:

- loop label
- execute `load`
- compare
- branch to exit if condition fails
- body
- jump back

Specialized convenience helpers like `wait_u8()` may exist on top of this.

### 4. `for_range()`

Best for counted loops and table walks.

```python
with f.for_range(t0, 0, 64, step=4) as i:
    f.sw(zero, s0, i)
```

Semantics:

- initialize induction register to `start`
- loop while `i < end` for positive steps
- execute body
- increment by `step`
- jump back

The induction register should be explicit. The loop helper should not allocate hidden
registers unless the API asks for a scratch register.

## Range assumptions

Current firmware is small enough that plain branch and `jal` fixups are sufficient.

- branches: range check at assembly time
- `jal`: range check at assembly time

Out-of-range relaxation is not required for the initial implementation.

## Style rules for `rvir`

- Prefer explicit registers.
- Prefer explicit frame declarations.
- Prefer thin helpers over opaque abstractions.
- Keep raw `dsl.py` escape hatches available.
- Generate semantic labels when possible so disassembly is readable.

## Summary

`rvir` is a structured assembler for small Blackhole firmware, not a full compiler.

It should make this easy:

- writing functions
- managing frames
- using pinned MMIO bases
- expressing loops and polling patterns
- resolving labels and fixups
- dropping to raw `dsl.py` when needed

while keeping the emitted code obviously RISC-V-shaped.
