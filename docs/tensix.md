# Blackhole Tensix state and configuration

This document describes the state that the three Tensix RISC threads interact
with. It is written from the point of view of TTK: configuration should be
readable, and ownership and state transitions should be explicit before they
are lowered to raw Tensix instructions.

The primary execution-model reference is the Blackhole TTSIM model in
`../ttsim`. The old `blackhole-py/ttk` helpers are the reference for the
initialization sequences used by existing kernels.

## The short version

There are three logical Tensix instruction pipes:

```text
TRISC0 -> pipe 0 -> unpack
TRISC1 -> pipe 1 -> math/SFPU
TRISC2 -> pipe 2 -> pack
```

MOP configuration, replay buffers, instruction FIFOs, DMA/register-file state,
thread configuration, and address-counter state are per pipe.

The main Tensix CFG register space is different. It is shared by the pipes and
has two configuration contexts selected by `CFG_STATE_ID`. ALU format,
accumulator, unpack, pack, destination, and address-control registers live in
that space. TTK must distinguish between state owned by one engine/pipe and
shared configuration coordinated between engines.

## CFG register space

The Blackhole Tensix CFG aperture starts at:

```text
CFG_BASE = 0xFFEF0000
```

Registers are normally addressed as 32-bit words. For example:

```text
CFG.ALU                              = 0xFFEF0004
CFG.ALU.addr32                       = 1
CFG.THCON_SEC0_REG0_TileDescriptor   = 0xFFEF0100
CFG.THCON_SEC0_REG0_TileDescriptor.addr32 = 64
```

The byte address is used by RISC-V MMIO loads/stores. The `addr32` word index
is used by Tensix instructions such as `TTRMWCIB0..3`, `TTWRCFG`, and
`TTRDCFG`.

The CFG aperture contains configuration for the whole Tensix coprocessor:

### ALU and numeric format state

- `ALU_FORMAT_SPEC_REG`: SrcA, SrcB, destination-accumulator formats, and
  format overrides.
- `ALU_ACC_CTRL`: FP32 destination/accumulator mode, SFPU FP32 mode, integer
  math mode, and source/destination zero-flag behavior.
- Rounding and format-conversion controls.

These fields are consumed by math, SFPU, unpack, and pack paths. They are not
safe to treat as privately owned by `math.py` or `unpack.py`.

### Unpack state

- `UNP0_*` and `UNP1_*` address controls.
- Unpack base addresses and counters.
- `THCON_SEC0_*` and `THCON_SEC1_*` tile descriptors.
- Input/output format fields.
- Zero-compression and decompression controls.
- Source-register selection.
- Destination context and tile dimensions.
- Unpack FIFO and limit controls.

`THCON_SEC0` and `THCON_SEC1` describe the two unpack interfaces/contexts.
They are part of the shared CFG aperture, although normal ownership is
assigned to TRISC0.

### Pack state

- `PCK0_*` address controls and base addresses.
- `PCK_DEST_RD_CTRL`: destination read width, signedness, and conversion
  controls.
- Pack counters, face mappings, edge controls, and partial-tile controls.
- Pack format and output-interface fields, represented in THCON registers as
  well as PCK registers.

Normal ownership is assigned to TRISC2, but pack reads shared destination and
format state established by the other paths.

### Destination and architectural storage state

- Destination offset, register-window, and stack bases.
- Destination access configuration.
- Destination target selection.
- Source/destination width controls.

These fields affect both math and pack. FP32 destination mode also changes the
usable destination capacity, so it must be coordinated across both engines.

### Miscellaneous Tensix controls

- Instruction-cache invalidation.
- PRNG seed.
- ECC and scrubber controls.
- Thread end-PC and RISC controls.
- Clock-gating and related global controls.

Some of these are resident-firmware concerns rather than ordinary kernel
configuration, but they still belong to the same architectural CFG aperture.

## CFG contexts

TTSIM models two `TensixConfigState` objects:

```cpp
TensixConfigState config[2];
```

The active context is selected through the thread configuration field
`CFG_STATE_ID`. Math, unpack, and pack operations consult the selected context
for the fields relevant to their path.

This is not a per-TRISC copy of the whole CFG register file. The contexts are
shared configuration snapshots. TTK therefore needs to model:

```text
shared CFG context 0
shared CFG context 1
per-thread selected CFG_STATE_ID
```

A helper that silently writes whichever context happens to be active will be
fragile after a context switch or reload. High-level helpers should identify
the context they configure, or explicitly select it as part of the transition.

## Thread configuration

Thread configuration is separate from the main CFG aperture. It is written by
`TTSETC16` and is local to an instruction pipe. Important groups include:

- `CFG_STATE_ID`.
- SrcA/SrcB set selection.
- Destination target offset.
- Source/destination clear and valid behavior.
- Scoreboard masks.
- Fidelity phase.
- Address modifiers for SrcA, SrcB, Dst, pack, and bias.
- SFPU destination format and stack increment.

The same conceptual field name can appear in different pipes, but the state is
not one global thread-config word. TTK should keep thread configuration under
the owning engine/pipe and keep shared CFG contexts separate.

## MOP and replay state

MOP state is per pipe. TTSIM models it as:

```cpp
mop_zmask_hi16[3]
mop_cfg[3][9]
replay_buf[3][32]
replay_index[3]
replay_left[3]
replay_execute_while_loading[3]
```

The nine MOP configuration words are two loop controls followed by seven
instruction slots:

```text
[0] outer loop length
[1] inner loop length / flags
[2..8] seven Tensix instructions, executed by the MOP loop nest
```

`write_mop_cfg` for TRISC0 must not be modeled as overwriting TRISC1 or
TRISC2's template.

MOP configuration persists. A `TTMOP` uses the current configuration; it does
not consume it. Reconfiguration is needed only when the template or loop
configuration changes.

Replay state also persists per pipe:

- `TTREPLAY(load_mode=1)` loads entries into that pipe's replay buffer.
- `TTREPLAY(load_mode=0)` executes entries already loaded there.
- `TTMOP_CFG` changes the high part of that pipe's MOP z-mask.

TTK exposes this as engine-local state:

```python
unpack = Unpack(k)
unpack.mop.configure(MopCfg.unpack_ab())
unpack.mop.load_replay(words, start=0)
unpack.mop.run()

math = Math(k)
math.configure_mop(my_math_program)
math.mop.run()

pack = Pack(k)
pack.mop.configure(MopCfg.pack_tile())
pack.mop.run()
```

The replay buffer is separate from the MOP: it is a 32-word per-pipe RAM.
`load_replay()` writes raw Tensix instructions into a window of that RAM;
`execute_replay(start, length)` issues a `TTREPLAY` that executes the window.
A MOP slot can issue that same replay operation, which is how matmul loads
several repeated operand instructions without putting them directly in the
seven MOP slots. Replay state is persistent and is not a semantic Dst or CB
state.

The public API should not require users to write MOP aperture addresses or
manually construct `TTMOP_CFG` words.

## Other per-pipe state

TTSIM also keeps the following state per instruction pipe:

- Instruction FIFO and read/write pointers.
- Replay buffer and replay loading cursor.
- DMA/register-file words.
- Address counters for unpack0, unpack1, and pack.
- Thread state, including RWC values, bias, and fidelity phase.
- Active instruction-pipe state.

This is why a single global MOP or thread-state object in TTK would be too
coarse.

## Shared execution state

The following resources are physically shared or cross-engine and need raw
hardware/shadow coordination:

- The two CFG contexts.
- Shared SrcA, SrcB, and Dst storage.
- Tensix semaphores and semaphore maxima.
- Synchronization resources such as Tensix and MOP sync points.
- Global controls such as PRNG/ECC state when they are part of the program
  initialization contract.

The physical Dst storage does not have one authoritative semantic format. One
operation may write Dst using FP32 accumulation semantics while a later pack
operation intentionally reads the same storage as BF16. Format, width,
conversion, destination offsets, and interpretation therefore belong to the
engine and phase that performs the operation. TTK may keep a raw shadow of the
underlying hardware words for diffing, but it must not expose one global
`DstState` that declares what Dst "is".

Likewise, shared ALU/accumulator registers are hardware state, not a semantic
promise that applies forever. An engine may reconfigure them before its phase;
the engine's own state records what its next operation expects.

## Proposed TTK ownership model

```text
TensixState
├── contexts[2]
│   └── shared CFG register shadows
├── shared
│   ├── raw CFG-context/register shadows
│   ├── physical SrcA/SrcB/Dst storage ownership
│   ├── semaphores
│   └── synchronization state
└── pipes[3]
    ├── unpack pipe 0
    │   ├── thread cfg
    │   ├── address counters
    │   ├── MOP/replay
    │   └── instruction state
    ├── math pipe 1
    │   ├── thread cfg
    │   ├── address counters
    │   ├── MOP/replay
    │   └── instruction state
    └── pack pipe 2
        ├── thread cfg
        ├── address counters
        ├── MOP/replay
        └── instruction state
```

The engine modules remain separated:

- `ttk/unpack.py` owns unpack-specific transitions.
- `ttk/math.py` owns FPU/math-specific transitions.
- `ttk/sfpu.py` owns SFPU-specific state and imperative vector programs.
- `ttk/pack.py` owns pack-specific transitions.
- `ttk/tensix.py` owns shared state, per-pipe plumbing, and raw lowering used
  by both `Math` and `Sfpu`.

If an operation changes a physically shared register, the engine calls a
named engine-local operation, for example:

```python
math.configure_accumulator(FP32)
pack.configure_read_format(BF16)
```

rather than treating one semantic Dst format as globally authoritative.

## Human-readable configuration API

Normal code should describe intent:

```python
unpack = Unpack(k)
unpack.configure_input(
    format=BF16,
    tile_bytes=2048,
    zero_compression=False,
)
math = Math(k)
math.configure_operands(
    src_a=BF16,
    src_b=BF16,
    destination=BF16,
)
pack = Pack(k)
pack.configure_output(
    source=BF16,
    destination=BF16,
    out_cb=16,
)
```

These calls should lower internally to the required CFG writes, thread
configuration writes, MOP writes, and synchronization. A raw line such as:

```python
TTRMWCIB0(Mask=0x10, Data=0x10, CfgRegAddr=...)
```

should be reserved for the implementation of a named operation such as
`unpack.enable_zero_compression()` and should not appear in normal kernels.

## Configuration linearity

Configuration calls are compile-time lowering operations. They should be
emitted in a linear sequence before runtime tile-processing loops, or as
explicit linear transitions between phases:

```text
configure input
run input phase
switch to intermediate format
run reload phase
restore input format
continue
```

The old code contains runtime branches and loops for work scheduling and tile
processing, but its configuration choices are Python-side specialization or
ordered transitions. We should preserve that property in the rewrite.

If a future API attempts to configure an engine inside a device-runtime branch,
TTK should reject it unless both paths produce the same resulting state. This
keeps the state shadow exact instead of introducing an unknown state merely to
support an avoidable control-flow pattern.
