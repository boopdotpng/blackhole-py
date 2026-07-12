# Blackhole SFPU state and API boundary

The rewrite should give the SFPU its own `ttk/sfpu.py`. `Math` and `Sfpu`
both issue on TRISC1/pipe 1, but they are different engines with different
programming models. `Tensix` owns the physical state they share.

The architectural references are the local
`../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/VectorUnit.md`,
`SFPLOAD.md`, `SFPSTORE.md`, `SFPCONFIG.md`, and `SFPLOADMACRO.md`. The model in
`../ttsim/src/tensix.cpp` is useful for executable validation, but intentionally
implements only a subset of this state.

## What the old Python kernels actually use

The old tree does not use register expressions. It names LRegs explicitly and
emits an ordered instruction sequence, either directly in a kernel or through
a helper in `../blackhole-py/ttk/sfpu.py`.

| Family | Actual use | Local source |
|---|---|---|
| Small in-place rows | Load one 4x8 Dst slice, apply an immediate operation, store it, advance the Dst RWC, and repeat through a tile. `add1` records a five-instruction row in Tensix replay. | `../blackhole-py/examples/add1.py` |
| Multi-tile pointwise arithmetic | Keep several Dst slices in L0-L7 and explicitly emit multiply/add/sign sequences. RoPE consumes four Dst tiles; SwiGLU combines gate and up tiles. | `../blackhole-py/examples/llama3/attn.py`, `swiglu.py` |
| Transcendental sequences | Build exp, reciprocal, positive rsqrt, sigmoid, and SiLU from loads, constants, field operations, MADs, and explicit scratch registers. | `../blackhole-py/ttk/sfpu.py`, used by `swiglu.py`, `softmax.py`, and `rmsnorm.py` |
| Cross-lane reductions | Use `SFPMOV`, `SFPSHFT2`, `SFPSWAP`, add, and persistent LRegs for max/sum reductions. Softmax intentionally keeps row max and reciprocal in L6/L7 across other work. | `../blackhole-py/examples/llama3/softmax.py`, `rmsnorm.py` |
| Mixed Dst views | Explicit load/store modifiers move BF16 input, FP32 accumulators, and BF16 output through the same physical Dst. Some addresses are patched from RISC-V registers at runtime. | `../blackhole-py/examples/llama3/rmsnorm.py`, `softmax.py` |
| Initialization and ordering | Initialize lane predicates and L11, configure Dst address modifiers, set/reset RWCs, and explicitly stall between FPU, SFPU, and pack phases. | `../blackhole-py/fw/brisc.py`, `../blackhole-py/ttk/math.py`, and the kernels above |

The `Sfpu` class near the top of old `ttk/sfpu.py` contains LUT and
trigonometry experiments, but no old kernel instantiates it. The used surface
is the `LReg` enum, free sequence helpers, and raw `TTSFP*` instructions. No
old Python kernel uses `SFPLOADMACRO`. That feature must be modeled eventually,
but it is not a prerequisite for a clean `add1` port.

## State taxonomy

SFPU state is not one configuration dataclass. It has four different scopes:

```text
shared, two-context main CFG
per-pipe ThreadConfig and RWCs
SFPU-persistent LaneConfig, LoadMacroConfig, constants, flags, and PRNG
runtime LRegs, pending instructions, and shared Dst contents
```

Clearing the CFG aperture does not clear `SFPCONFIG` state. In particular,
LaneConfig and LoadMacroConfig survive an ordinary CFG clear. Their software
shadows must therefore be unknown until an explicit SFPU initializer writes
them; assuming zero because `TensixState.contexts` was cleared is incorrect.

### Main CFG

There are two shared CFG contexts, selected per pipe by
`ThreadCfg.CFG_STATE_ID`. The SFPU-relevant fields are:

- CFG word 0 (`ALU_FORMAT_SPEC_REG`) contains three format override
  value/enable pairs: SrcA at bits 0:4, SrcB at bits 5:9, and Dstacc at bits
  10:14. These are five-bit fields, not byte-aligned inferred formats.
- CFG word 1 (`ALU`) contains rounding controls, unsigned flags, the inferred
  SrcA/SrcB/Dstacc format nibbles at bits 17, 21, and 25, and the FPU FP32,
  SFPU FP32, and integer-math enables at bits 29, 30, and 31.
- `DEST_REGW_BASE` and `DEST_SP_BASE` participate in `SFPLOAD`/`SFPSTORE`
  addressing. They are architectural even though the current TTSIM model
  rejects nonzero use of the former and does not fully model the latter.

For load/store modifier `SRCB` (zero), the effective format is not simply a
field on `MathState`. `SFPLOAD` and `SFPSTORE` resolve it in this order:

1. SFPU FP32 enable in CFG word 1 forces FP32.
2. Otherwise, select SrcB override from word 0 or inferred SrcB from word 1.
3. A per-thread `SFPU_DEST_FMT` override, when enabled, replaces that format.
4. Resolve the result to the concrete FP32, BF16, or FP16 load/store mode.

The FPU FP32 bit at word 1 bit 29 and SFPU FP32 bit at bit 30 are normally
changed together (`0x60000000`) when selecting a 32-bit Dst phase. The FPU bit
does not choose an SFPU conversion by itself, but it changes the physical Dst
layout and must agree with SFPU and pack configuration.

Unbanked/shared controls also matter: `PRNG_SEED` seeds the 32 per-lane SFPU
PRNG states; `DEST_ACCESS_CFG` changes physical Dst access behavior; and
`CHICKEN_BITS.sfpu_scbd_disable` disables the SFPU scoreboard. These are
hardware/debug controls, not ordinary per-program arithmetic options.

CFG word 1 is shared with FPU, unpack, and pack setup. `Math` or `Sfpu` may
request a field transition, but neither may own the whole word implicitly.
All writes need a shared raw shadow and field-wise merge under the required
ordering protocol.

### Per-pipe ThreadConfig and addressing

The following state is local to an instruction pipe; SFPU normally uses pipe
1:

| State | Meaning |
|---|---|
| `CFG_STATE_ID` (thread word 0) | Selects shared CFG context 0 or 1. |
| `DEST_TARGET_REG_CFG_MATH` (word 1) | Adds a 12-bit base to every SFPU Dst address. |
| `SFPU_DEST_FMT` (word 4) | Bit 0 enables a four-bit format override held in bits 1:4. |
| `ADDR_MOD_AB[0:7]`, `ADDR_MOD_AB2[0:7]`, `ADDR_MOD_DST[0:7]`, and `ADDR_MOD_BIAS[0:7]` | Define the eight address-modifier recipes selected by load/store. They update SrcA, SrcB, Dst/current-and-carry counters, and the extra address-modifier selector; SFPU load/store do not update fidelity phase. |
| `SFPU_STACK` (word 36) | Ten-bit stack-pointer decrement used by the `INT32_ALL` Dst access mode. |

The current Dst/SrcA/SrcB RWCs and their carry values are runtime pipe state,
not configuration constants. `SETRWC`, `INCRWC`, and each SFPU load/store
address modifier mutate them. The old `add1` traversal depends on this
mutation, so a helper must make the traversal visible even if it hides the raw
instructions.

### `SFPCONFIG` state

`SFPCONFIG` writes persistent SFPU state. Its `Mod1` bits mean: bit 0 selects
the immediate value, bits 1:2 select replace/OR/AND/XOR for mutable config,
and bit 3 supplies an eight-lane mask. Without the immediate bit, values come
from L0's first eight lanes and are vertically broadcast.

| Destination | Persistent state |
|---:|---|
| 0-3 | Four arbitrary `LoadMacroConfig.InstructionTemplate` words. |
| 4-7 | Four 32-bit `LoadMacroConfig.Sequence` words. |
| 8 | Twelve-bit `LoadMacroConfig.Misc`, with replace/OR/AND/XOR support. |
| 9-10 | Non-contractual; software must not use them. |
| 11-14 | Read-mostly SFPU constants. L11 is conventionally -1.0; L12-L14 are programmable constants. Immediate mode supplies architectural defaults: `-1.0`, `1/512`, `-0.67487759`, and `-0.34484843`. |
| 15 | Eighteen-bit per-lane `LaneConfig`. |

LaneConfig contains all of the following options, even though most kernels
leave them zero:

| Bits | Option |
|---:|---|
| 0 | Treat the largest FP16A encoding as infinity. |
| 1 | Disable the instruction-template backdoor for writes with VD >= 12. |
| 2 | Enable destination-index tracking for argmin/argmax. Due to erratum TEN-2932, most instructions must not write L4-L7 while it is set. |
| 3 | Capture the default Dst index into the paired index LReg. |
| 4 / 5 | Block SFPU writes to Dst / reads from Dst. |
| 6 / 7 | Force exchanged Dst columns for reads / writes. |
| 8 | Invert `SFPSWAP` comparison direction. |
| 9:10 | Block selected Dst movement columns. |
| 11 | Reserved. |
| 12:15 | Four-row predication mask. |
| 16:17 | Reserved. |

Changing `DISABLE_BACKDOOR_LOAD` requires an immediately following `SFPNOP`
when the next instruction's interpretation could differ.

### LoadMacro state

`SFPLOADMACRO` performs a Dst load and can schedule one future instruction on
each of the simple, MAD, round, and store sub-units. Its persistent state is
per lane:

- Four arbitrary instruction templates.
- Four 32-bit sequences, one per macro. Each sequence has one byte per
  sub-unit. A byte selects none/NOP/store/template 0-3, a delay from 0-7,
  optional temporary L16, and which source operand is replaced by the loaded
  VD.
- A 12-bit misc word: four-bit store modifier, four per-macro bits selecting
  the load modifier for store, and four per-sub-unit bits selecting whether
  delay counts elapsed instructions or elapsed cycles.

The pending per-sub-unit scheduled instructions and their delays are runtime
state too. A scheduled instruction wins over a normal instruction issued to
the same sub-unit in the same cycle. L16 exists only for LoadMacro-scheduled
compute/store. This feature needs a dedicated typed description; it should
never be represented as four unexplained integers in a kernel.

Current TTSIM coverage is narrower than the architecture. In
`../ttsim/src/tensix.cpp`, `SFPCONFIG` accepts only Mod1 0/1, LaneConfig only
accepts bits `0x104`, immediate defaults are only modeled for L11, and
`SFPLOADMACRO` is explicitly unsupported. `../ttsim/src/sim.h` nevertheless
shows the separate LRegs, lane config, macro templates/sequences/misc, PRNG,
condition flags/stack, and RWC state that TTK must keep distinct. Simulator
limitations should be recorded as validation gaps, not used to shrink the API
model.

### Other runtime state

- L0-L7 are the eight ordinary writable 32x32-bit vectors. L8 is the read-only
  0.8373 constant, L9 is zero, L10 is 1.0, L11-L14 are `SFPCONFIG` constants,
  L15 contains `lane * 2`, and macro-only L16 is described above.
- Lane flags, whether flags gate execution, and the per-lane condition stack
  are mutated by compare, `SFPENCC`, push/pop, and complement instructions.
- Each lane has PRNG state used by stochastic operations.
- Shared Dst contents/valid bits, the selected 16/32-bit view, and outstanding
  FPU/SFPU hazards are runtime state.
- Tensix instruction replay and MOP RAM are per-pipe execution mechanisms, not
  SFPU registers. `add1` may ask `Tensix` to replay an SFPU program, but `Sfpu`
  should describe that program.

## Findings and current model coverage

The audit found and corrected two bad `Math` register images from the initial
rewrite. Formats had been packed into CFG word 0 as byte fields, and FP32 mode
had been written as `0x60` in CFG word 2. Word 0 actually contains five-bit
override value/enable pairs; the FP32 enables are word 1 bits 29:30.

The corrected lowering also does not full-write the three inferred format
nibbles from Math. On Blackhole, SrcA and SrcB are inferred from unpack state,
pack owns the Dstacc nibble, and Math owns only the paired FP32 bits and the
integer-math bit. These shared fields are updated with in-pipe masked RMWs so
independently compiled TRISCs cannot clobber one another.

| State group | Modeled now | Deliberate gap |
|---|---|---|
| Shared main CFG | Both raw contexts, named format/base/PRNG/access registers, Math FP32/int8 updates, and pack Dstacc updates. | No high-level word-0 override resolver, Dst register/stack-base API, PRNG reseed API, or debug scoreboard toggle. |
| Per-pipe ThreadConfig | Named `SFPU_DEST_FMT`, all AB/AB2/Dst/Bias address-modifier sections, Dst target, and SFPU stack. Add1 initializes its format override and sections 6/7 explicitly. | No generic typed address-modifier recipe or `INT32_ALL` stack lifecycle yet. |
| Persistent `SFPCONFIG` | Uniform typed `LaneConfig`, with an unknown-after-reset shadow that prevents accidental elision. | Programmable constants, per-lane/masked writes, bitwise update modes, and LoadMacro configuration/scheduling are deferred until a kernel uses them. |
| Runtime program state | Checked L0-L7 allocation/initialization, architectural constants, typed Dst refs and all load/store modifiers, conservative dependencies, replay allocation, and add1 tile traversal. | Predication/condition stack, shuffles/reductions, persistent cross-program LRegs, most arithmetic opcodes, PRNG use, and LoadMacro temporary L16 remain to be added with the kernels that need them. |

Thus all SFPU configuration families are identified, and the add1-relevant
subset is modeled and hardware-validated. The table is intentionally explicit
about the options that are named but do not yet have a safe high-level API.

## Ownership

| Object | Owns |
|---|---|
| `Tensix` / `TensixState` | The two raw main-CFG context shadows; per-pipe ThreadConfig, RWCs, MOP/replay, and instruction ordering; shared Dst and semaphore coordination; masked field updates and unknown-until-initialized state. |
| `Math` | FPU operand/fidelity/accumulation intent and math MOP programs. It may request a coordinated Dst-width transition, but does not own SFPU LRegs, LaneConfig, or SFPU programs. |
| `Sfpu` | LReg allocation and clobbers, uniform LaneConfig, imperative vector sequences, tile traversal, ordering, and replay installation. |

TRISC1 is normally the sole issuing role for FPU and SFPU instructions. That
role-level rule does not make shared CFG word 1 or physical Dst private to a
`Math` Python object.

## Staged API

Start with an imperative API whose order is the program:

```python
sfpu.initialize(lane_config=LaneConfig())
sfpu.addrmod(7, dst_incr=0)
sfpu.set_rwc(dst=0)
sfpu.load(L0, Dst(0), format=SfpuFormat.SRCB, addrmod=7)
sfpu.addi(L0, 1.0)
sfpu.nop()
sfpu.store(Dst(0), L0, format=SfpuFormat.SRCB, addrmod=7)
sfpu.incr_rwc(dst=2)
```

The exact spelling can change, but raw `TTSFP*`, magic load/store modifiers,
and packed config words should not appear in `examples/add1.py`.

Build the surface in this order:

1. Named LRegs/constants, typed Dst addresses and load/store formats, exact
   LaneConfig initialization, RWC/address-modifier helpers, and one method per
   ordinary SFPU instruction needed by `add1`.
2. An `SfpuProgram`/sequence builder with declared inputs, outputs, scratch
   LRegs, persistent LRegs, config preconditions, and hazards. A tile iterator
   can inline or use Tensix replay, but face/slice traversal and RWC effects
   must remain inspectable.
3. Trusted algorithm helpers (`exp`, reciprocal, rsqrt, SiLU, lane reduction)
   implemented from those imperative primitives. Port only helpers exercised
   by a kernel and validate their instruction stream and numeric behavior.
4. Typed LoadMacro templates/sequences after ordinary programs work and a
   validation strategy exists beyond current TTSIM coverage.
5. Optionally add expression syntax over the same program builder.

Operator expressions are deliberately deferred. SFPU operations are
destructive and modifier-dependent; only eight ordinary writable vectors are
available; old kernels rely on explicit clobber sets and values surviving in
L6/L7; condition masks and stacks are side effects; shuffles change lanes;
load/store changes RWCs; and NOPs, FPU-to-SFPU hazards, replay, and LoadMacro
scheduling constrain legal order. An expression tree can easily duplicate,
reorder, or hide those effects before the allocator and scheduler are proven.
Lightweight register objects are still useful as checked architectural names,
but should not imply host-value semantics yet.

For `add1`, stages 1 and the small replay/tile helper from stage 2 are enough.
That gives the rewrite a short kernel without committing the entire SFPU API to
an unvalidated expression model.
