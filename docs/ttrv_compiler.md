# How the TTRV compiler should be structured

A guide for rewriting `ttrv/`. It explains what each part of a compiler is for, where the current code already has
the right shape, and what the parts and their interfaces should look like.

## 1. What a compiler is

A compiler is a pipeline. Each stage takes one representation of the program and produces a lower one, and checks
whatever can be checked at that level:

| stage | input → output | current file | status |
| --- | --- | --- | --- |
| parse | text → syntax tree (AST) | `parse.py` | fine |
| expand | AST → flat program: constants folded, macros and `repeat` inlined | `expand.py` | fine |
| layout | declarations → addresses (params, L1, CBs) | `layout.py` | fine |
| lower | each statement → instructions on *virtual* registers | `codegen.py`, `ops.py`, `noc.py`, `movement.py`, `sfpmacro.py` | the problem |
| verify | instruction list → state errors ("MOP not loaded on every path") | `state.py` | stringly |
| register allocation | virtual registers → x1..x31, spills | `regalloc.py` | fine |
| assemble | instructions → bytes, branch offsets, listing | `emit.py` | fine |
| package | images + manifest | `__init__.py` | fine |

The stages are already right. What's wrong is the **interfaces between them** and the **lowering stage's insides**:

1. The instruction list has no types: an entry is an `int` (Tensix word), an `Instruction`, a branch tuple, or `None`
   (a placeholder for a state fact), and every later stage tells them apart with `isinstance`.
2. All of lowering shares one mutable object, `g`, with ~25 attributes; other modules add attributes to it.
3. Lowering functions mix three jobs: checking operands, deciding what to emit, and emitting it.

## 2. The layers

Keep three layers, and keep the bottom two free of anything TTRV-specific. They're what a tinygrad renderer reuses.

```
isa.py   hw.py + cfg.py         encodings and hardware facts. Knows nothing about TTRV.
   \        /
    asm.py                      RV32 builder on virtual registers + device idioms (MMIO, TTSync, Tensix push).
       |                        Knows nothing about TTRV source.
lower/*.py                      TTRV operations -> asm calls, one module per hardware unit.
```

- `isa.py` already exists: `rv("addi", ...)`, `tensix("ELWMUL", ...)`, the `Stall` / `Wait` / `LReg` enums.
- `hw.py` (rewritten) has the memory map, every config field by its `cfg_defines.h` name (via the generated `cfg.py`),
  NoC registers, p150 topology, data formats, and the TTRV ABI. Rule: **no hardware number appears outside these
  files.** If lowering needs a number, it gets a name in `hw.py` first.
- `asm.py` is new (section 4).

## 3. The IR: typed items

Replace the four-kinds-of-entry list with one small class per kind. Everything downstream switches on type, and the
type says what fields exist:

```python
@dataclass(frozen=True)
class VReg:          # virtual register; regalloc maps it to x1..x31 or a spill slot
  n: int
  name: str = ""     # source variable, for the listing

@dataclass(frozen=True)
class Label:
  name: str

@dataclass
class Op:            # one RV32 instruction
  op: str            # "add", "lw", ...
  rd: VReg | None
  rs1: VReg | Reg0 | None
  rs2: VReg | Reg0 | None
  imm: int = 0

@dataclass
class Branch:  op: str; rs1: VReg; rs2: VReg; target: Label     # beq/bne/bltu/bgeu
@dataclass
class Jump:    target: Label; link: VReg | None = None          # jal
@dataclass
class Place:   label: Label                                     # where a label points
@dataclass
class Tensix:  word: int                                        # inline .ttinsn
@dataclass
class Fact:    kind: FactKind; facts: frozenset                 # for verify; emits nothing
```

Each item also carries its source location. Make facts enums or tuples, not English sentences:
`("loaded", "dot_face")` rather than `"loaded dot_face"`, `("sfpu_cycle", 3)` rather than `"SFPU cycle 3"`. A typo then
raises an error instead of silently disabling a check.

## 4. Emitting RISC-V: an assembler-builder

Today lowering emits through `g.rv(op, rd, a, b, imm)`, `g.calc`, `g.imm` and `g.mem`, with positional register
arguments whose meaning changes per instruction (a store's `rd` is 0 and its value goes in `b`), and with polling
loops written out by hand about six times. A builder fixes this. It has one method per instruction, each returning a
fresh virtual register, plus named idioms:

```python
class Asm:
  def __init__(self, role): ...

  # values: every call returns a new VReg (never reused), so lowering never thinks about register lifetimes
  def li(self, n: int) -> VReg
  def add(self, a, b) -> VReg            # also sub, and_, or_, xor, sll, srl, sra, mul, divu, remu, sltu, slt
  def addi(self, a, imm: int) -> VReg    # also andi, ori, xori, slli, srli, srai, sltiu
  def zext16(self, a) -> VReg

  # memory: absolute addresses (MMIO, L1 globals) resolve through the base registers in one place
  def load(self, addr: int | tuple[VReg, int], width=4) -> VReg
  def store(self, addr: int | tuple[VReg, int], value: VReg | int, width=4)
  def fence(self)

  # control flow
  def label(self, name="") -> Label
  def place(self, label: Label)
  def branch(self, cond: str, a, b, target: Label)    # "eq" "ne" "ltu" "geu"
  def jump(self, target: Label)

  # idioms (each written once, documented once)
  def spin_while(self, addr: int, cond="ne", value=0)     # poll an MMIO register
  def ttsync(self, check: int)                            # ManualTTSync: sw, lw, consume
  def tensix(self, word: int)                             # push a constant Tensix instruction inline
  def tensix_runtime(self, word: int, field: str, value: VReg)  # constant word | runtime field, via INSTRN_BUF
  def rmw(self, *writes: Set)                             # Config fields: RMWCIB per byte touched
  def setc16(self, *writes: Set)                          # one whole ThreadConfig word
```

Compare the CB wait loop today with the builder:

```python
# today (ops.py)
loop = object()
g.mark(loop)
other = g.mem("lhu", popped if producer else pushed)
occ = g.calc("sub", own, other) if producer else g.calc("sub", other, own)
occ = g.zext16(occ)
free = g.calc("sub", g.li(cap), occ) if producer else occ
g.branch("bltu", free, n, loop)

# with Asm
retry = a.label("cb_wait")
a.place(retry)
other = a.load(hw.cb_popped(cb) if producer else hw.cb_pushed(cb), width=2)
occupied = a.zext16(a.sub(own, other) if producer else a.sub(other, own))
free = a.sub(a.li(capacity), occupied) if producer else occupied
a.branch("ltu", free, n, retry)
```

The builder is also where generated-code quality lives: hoisting constants out of loops, bottom-tested loops (one
branch per iteration instead of two), and dropping the `jal` to the very next instruction after an `if` with no `else`.

## 5. No strings for hardware names

Hardware names are Python objects, never strings built at compile time:

- **Fields** are module attributes of the generated `cfg.py`: `cfg.ALU_FORMAT_SPEC_REG2_Dstacc` is a
  `Field(space, word, shift, width, name)`. Calling it with a value makes a checked write, `Set(field, value)`:
  `rmw(g, cfg.ALU_FORMAT_SPEC_REG2_Dstacc(f), cfg.ALU_ACC_CTRL_Fp32_enabled(f == FP32))`. A misspelled field is an
  `AttributeError` (and an editor error) instead of a `KeyError` halfway through a compile.
- **Families** that differ only by a number are grouped in `hw.py` as typed views built once at import:
  `hw.UNPACKER[i].out_data_format`, `hw.UNPACKER[i].base_address[ctx]`, `hw.ADDR_MOD[slot].incr[counter]`,
  `hw.PACK_ADDR_MOD[slot].ydst_incr`. `hw.py` is the only place a name is assembled from parts, and a wrong one fails
  when the module loads.
- **Writes are explicit calls**, not attribute assignment. `unpacker.out_data_format = fmt` emitting an instruction
  would hide an ordered side effect inside what reads like a plain assignment. If you later want "assignments" that
  emit, make the emission point explicit: a shadow copy of the config state that records writes and emits the
  minimal RMWCIB/SETC16 set on `flush()` (skipping writes of values already known to be there). That shadow state is
  also exactly what the verifier needs, replacing facts like `"pack output bf16"`.

The same rule applies elsewhere: Tensix instructions through the `isa.SFPMAD(...)` functions that already exist rather than
`g.tt("SFPMAD", ...)`, RISC-V through `Asm` methods rather than `g.rv("addi", ...)`, operand signatures from Python
function signatures (section 6) rather than `bind(s, "rd a b")`, and types and facts as small classes or tuples.

## 6. Lowering: one module per hardware unit, operations declared once

Replace `g` and `f(g, s)` with small objects that each own their state:

```
lower/
  program.py    per-RISC driver: walks statements, owns the Asm, the scope (env), loops, calls/returns
  scalar.py     expressions and statements: arithmetic, comparisons, loads/stores of L1, if/for/while
  cb.py         cb.reserve/push/wait/pop/read          state: which RISC owns each end
  noc.py        noc.read/write/inc/mcast/wait/status   state: transaction IDs in use
  unpack.py     unpack.*                               state: unpack credit in use
  math.py       math.*                                 state: addrmod slot names
  sfpu.py       sfp.*, sfpmacro.*                      state: predicate depth, index mode, macros, SFPU schedule
  pack.py       pack.*
  templates.py  mop.*, replay.*                        state: replay buffer allocation, what is loaded
  sync.py       tensix.wait/stall, sem.*
```

Declare each operation once, as an ordinary Python function, and let a decorator read its signature with
`inspect.signature`: positional parameters are the TTRV operands, keyword-only parameters the options, and each
annotation says how to convert and check the operand. Checking happens before the body runs, and the body receives
plain Python values:

```python
class Sfpu(Unit):
  namespace = "sfp"

  @op(roles=TRISC1)
  def mad(self, rd: Dest, a: LReg, b: LReg, c: LReg, *, neg_ab: Flag = False, neg_c: Flag = False):
    self.asm.tensix(isa.SFPMAD(a, b, c, rd, neg_ab | neg_c << 1))

class Noc(Unit):
  namespace = "noc"

  @op(roles=DATA_MOVEMENT)
  def read(self, dst: Pointer, src: Endpoint, *, n: Scalar, tid: Handle | None = None,
           port: Annotated[int, Range(0, 3)] | Scalar | None = None, wait: Flag = False) -> Handle: ...
```

The operation's name, operand order, defaults and types live in one place, and the error message for a bad operand
comes from the annotation.

That replaces the four separate signature dictionaries (`sfp` signatures, `sfpmacro` signatures, the
`movement` opts dict, inline `bind()` strings), gives every operation the same error messages, and lets a test check
the spec against the implementation.

Internal types become small classes instead of strings: `Pointer(elem="bf16")` rather than `"bf16*"`,
`Handle(kind="read", tid=4)` rather than `"tid:read:4"`.

## 7. How to do the rewrite safely

Keep the old compiler as the reference until the new one matches it:

1. A golden test builds every example in every model variant (1B, 8B, 8B FP8: 21 builds) and hashes the images,
   listings and manifests. One was used for the hw.py change; it isn't in the repo yet.
2. Rewrite one layer at a time, each step byte-identical: typed IR items, then `Asm` with the existing lowering
   calling it, then one `lower/` module at a time.
3. Only after the structure is done, make the generated-code improvements (section 4), each as its own change,
   measured in cycles.
