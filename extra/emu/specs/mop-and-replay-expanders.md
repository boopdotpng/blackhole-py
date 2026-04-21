# MOP Expander and Replay Expander

Two per-thread frontend units that expand single instructions into long sequences,
freeing the RISC-V core after a single push. The MOP Expander feeds into the Replay
Expander — a MOP expansion can emit REPLAY instructions, which are then further expanded.
The converse is not true: replayed sequences cannot contain MOP instructions.

```
RISC-V TRISC_n
    |
[Instruction FIFO, 32 slots]
    |
[MOP Expander]       1 MOP -> up to 32639 instructions
    |
[Replay Expander]    1 REPLAY -> up to 64 instructions from 32-slot buffer
    |
[Wait Gate]
    |
[Backend Units]
```

BRISC's instruction pushes enter **after** the MOP Expander, so BRISC cannot issue MOP
instructions. Only TRISC0/T1/T2 can use MOP.

---

## MOP Expander

### Instruction: MOP (opcode `0x01`)

```
[31:24] opcode    = 0x01
[23]    Template  (u1)  — 0 = Template 0 (zmask/unpack), 1 = Template 1 (double loop)
[22:16] Count1    (u7)  — Template 0: loop iterations - 1. Template 1: not used (config only)
[15:0]  MaskLo    (u16) — Template 0: low 16 bits of 32-bit zero-mask. Template 1: not used
```

```c
#define TT_OP_MOP(mop_type, loop_count, zmask_lo16_or_loop_count) \
    TT_OP(0x01, (((mop_type) << 23) + ((loop_count) << 16) + \
                  ((zmask_lo16_or_loop_count) << 0)))
```

### Instruction: MOP_CFG (opcode `0x03`)

Provides the upper 16 bits of the 32-bit zero-mask for Template 0. Must precede the
MOP instruction that uses it.

```
[31:24] opcode    = 0x03
[23:16] (reserved)
[15:0]  MaskHi    (u16) — high 16 bits of 32-bit zero-mask
```

```c
#define TT_OP_MOP_CFG(zmask_hi16) TT_OP(0x03, (((zmask_hi16) << 0)))
```

### Configuration Registers (MopCfg)

9 × 32-bit **write-only** registers per thread at `TENSIX_MOP_CFG_BASE = 0xFFB80000`.
Reading these from RISC-V is undefined behavior.

Each TRISC writes its own thread's config. BRISC cannot use MOP but can write any
thread's config registers (though there is no reason to — MOP config is only useful
if the thread can issue MOP instructions).

The registers have **dual interpretations** depending on which template the MOP
instruction selects:

| Index | Template 0 (Unpack Zmask) | Template 1 (Double Loop) |
|-------|---------------------------|--------------------------|
| `MopCfg[0]` | Not used | `OuterCount` (low 7 bits only) |
| `MopCfg[1]` | `Flags` (bit 0: `HasB`, bit 1: `HasA123`) | `InnerCount` (low 7 bits only) |
| `MopCfg[2]` | `InsnB` (only if `HasB`) | `StartOp` (skipped if NOP) |
| `MopCfg[3]` | `InsnA0` | `EndOp0` (skipped if NOP) |
| `MopCfg[4]` | `InsnA1` (only if `HasA123`) | `EndOp1` (skipped if NOP, or if `EndOp0` is NOP) |
| `MopCfg[5]` | `InsnA2` (only if `HasA123`) | `LoopOp` |
| `MopCfg[6]` | `InsnA3` (only if `HasA123`) | `LoopOp1` (alternating; skipped if NOP) |
| `MopCfg[7]` | `SkipA0` | `Loop0Last` (last inner iter of last outer iter) |
| `MopCfg[8]` | `SkipB` (only if `HasB`) | `Loop1Last` (last inner iter of non-last outer iter) |

Programming via MMIO:

```c
volatile uint32_t *mop_cfg = (volatile uint32_t *)0xFFB80000;
mop_cfg[0] = outer_count;
mop_cfg[1] = inner_count;
mop_cfg[2] = start_op;      // e.g. TT_OP_NOP
mop_cfg[3] = end_op0;       // e.g. TT_OP_SETRWC(...)
mop_cfg[4] = end_op1;       // e.g. TT_OP_NOP
mop_cfg[5] = loop_op;       // typically a REPLAY instruction word
mop_cfg[6] = loop_op1;      // TT_OP_NOP for single-instruction inner loop
mop_cfg[7] = loop0_last;    // e.g. MVMUL with CLR_A on final iteration
mop_cfg[8] = loop1_last;    // e.g. MVMUL with CLR_NONE on inner-last
```

The C++ `ckernel_template` class wraps this:

```cpp
ckernel_template tmp(outer, inner, lltt::replay_insn(16, 16));
tmp.set_end_ops(end0, end1);
tmp.set_last_outer_loop_instr(loop0_last);
tmp.set_last_inner_loop_instr(loop1_last);
tmp.program();                  // writes mop_cfg[0..8]
ckernel_template::run();        // TTI_MOP(1, 0, 0)
```

**Software must not modify MopCfg while an expansion is in progress.** Use `mop_sync()`
(blocking store to `pc_buf_base[2]`) or TTSync CSR reads to wait for completion.

### Functional Model

```python
async def MOPExpander(MopCfg):  # MopCfg is per-thread state; uint32[9] at 0xFFB80000
    MaskHi = 0                  # per-thread state, set by MOP_CFG instruction
    while True:
        Instruction = await GetNextIncomingInstruction()
        if Instruction.Opcode == 0x03:       # MOP_CFG
            MaskHi = Instruction.MaskHi
        elif Instruction.Opcode == 0x01:     # MOP
            if Instruction.Template == 0:
                async for x in ExpandTemplate0(
                    (MaskHi << 16) | Instruction.MaskLo,
                    Instruction.Count1,
                    MopCfg
                ):
                    yield x
            else:
                async for x in ExpandTemplate1(MopCfg):
                    yield x
        else:
            yield Instruction  # pass through everything else


def IsNop(Instruction):
    """Only recognizes plain NOP (opcode 0x02). NOT DMANOP (0x60) nor SFPNOP (0x8F)."""
    return (Instruction >> 24) == 0x02
```

### Template 0: Unpack Zero-Mask Loop

Used for unpack operations with column masking. Each iteration either emits the
unpack instruction(s) or the skip instruction(s), based on the corresponding mask bit.

```python
async def ExpandTemplate0(Mask, Count1, MopCfg):
    Flags  = MopCfg[1]
    InsnB  = MopCfg[2]
    InsnA0 = MopCfg[3]
    InsnA1 = MopCfg[4]
    InsnA2 = MopCfg[5]
    InsnA3 = MopCfg[6]
    SkipA0 = MopCfg[7]
    SkipB  = MopCfg[8]
    HasB    = Flags & 1
    HasA123 = Flags & 2

    for i in range(Count1 + 1):
        if (Mask & 1) == 0:
            yield InsnA0
            if HasA123:
                yield InsnA1
                yield InsnA2
                yield InsnA3
            if HasB:
                yield InsnB
        else:
            yield SkipA0
            if HasB:
                yield SkipB
        Mask >>= 1
```

Typical usage (tilize/untilize/pack):

```c
// Configure the unpack template via MopCfg registers
mop_cfg[1] = has_b | (has_halo << 1);
mop_cfg[2] = TT_OP_UNPACR(...);     // InsnB
mop_cfg[3] = TT_OP_UNPACR(...);     // InsnA0
// ...
mop_cfg[7] = TT_OP_NOP;             // SkipA0
mop_cfg[8] = TT_OP_NOP;             // SkipB

// Precede with MOP_CFG for upper mask bits, then issue MOP
TTI_MOP_CFG(zmask >> 16);
TTI_MOP(0, count - 1, zmask & 0xFFFF);
```

### Template 1: Double-Nested Loop

The common template for compute (matmul, eltwise). Implements a double-nested loop
with start/end framing instructions and last-iteration overrides.

Execution pattern:
```
for outer in 0..OuterCount:
    emit StartOp               (skipped if NOP)
    for inner in 0..InnerCount:
        emit LoopOp            (alternating LoopOp/LoopOp1 if both non-NOP)
        last inner, last outer: emit Loop0Last instead
        last inner, not last outer: emit Loop1Last instead
    emit EndOp0                (skipped if NOP)
    emit EndOp1                (skipped if NOP, or if EndOp0 is NOP)
```

```python
async def ExpandTemplate1(MopCfg):
    OuterCount = MopCfg[0] & 127
    InnerCount = MopCfg[1] & 127
    StartOp    = MopCfg[2]
    EndOp0     = MopCfg[3]
    EndOp1     = MopCfg[4]
    LoopOp     = MopCfg[5]
    LoopOp1    = MopCfg[6]
    Loop0Last  = MopCfg[7]
    Loop1Last  = MopCfg[8]

    # If LoopOp1 is non-NOP, inner loop alternates between LoopOp and LoopOp1
    # by XOR-flipping, and InnerCount doubles.
    if IsNop(LoopOp1):
        LoopOpFlip = 0
    else:
        LoopOpFlip = LoopOp ^ LoopOp1
        InnerCount *= 2

    # Hardware bug: must be replicated exactly
    if OuterCount == 1 and IsNop(StartOp) and InnerCount == 0 and not IsNop(EndOp0):
        OuterCount += 128

    for j in range(OuterCount):
        if not IsNop(StartOp):
            yield StartOp
        for i in range(InnerCount):
            if i != InnerCount - 1:
                yield LoopOp
            elif j != OuterCount - 1:
                yield Loop1Last      # last inner, but not last outer
            else:
                yield Loop0Last      # last inner of last outer
            LoopOp ^= LoopOpFlip     # alternate between LoopOp and LoopOp1
        if not IsNop(EndOp0):
            yield EndOp0
            if not IsNop(EndOp1):
                yield EndOp1
```

### MOP Performance

| State | Ingestion | Emission |
|-------|-----------|----------|
| Pass-through (non-MOP/MOP_CFG) | 1/cycle | 1/cycle |
| During MOP expansion | 0 (blocked) | 1/cycle |
| Transition after expansion ends | **1-cycle penalty** — neither ingests nor emits |

The 1-cycle transition penalty after expansion is why the expanded sequence should
include at least one REPLAY instruction that expands to ≥2 instructions — this fills
the gap so the backend sees uninterrupted 1-instruction/cycle throughput.

---

## Replay Expander

### Instruction: REPLAY (opcode `0x04`)

```
[31:24] opcode              = 0x04
[23:14] start_idx   (u10, but only low 5 bits used — wraps mod 32)
[13:4]  len         (u10, but only low 6 bits used — 0 means 64)
[1]     exec_while_loading  (u1) — execute instructions as they're recorded (only when load_mode=1)
[0]     load_mode           (u1) — 1 = record, 0 = playback
```

```c
#define TT_OP_REPLAY(start_idx, len, execute_while_loading, load_mode) \
    TT_OP(0x04, (((start_idx) << 14) + ((len) << 4) + \
                  ((execute_while_loading) << 1) + ((load_mode) << 0)))
```

### Replay Buffer

32-slot × 32-bit circular buffer per thread. **No memory-mapped address** — the buffer
has no CPU-accessible address. It is accessed exclusively through the REPLAY instruction.

Software convention partitions the buffer (not enforced by hardware):

| Slots | Reserved for |
|-------|-------------|
| 0–15 | SFPU instructions |
| 16–31 | FPU/matmul instructions |

### Functional Model

```python
async def ReplayExpander():
    ReplayBuffer = [0] * 32  # per-thread state; no CPU address
    while True:
        Instruction = await GetNextIncomingInstruction()
        if Instruction.Opcode != 0x04:       # not REPLAY
            yield Instruction                # pass through
        elif Instruction.Load:               # record mode
            Index = Instruction.Index
            Exec = Instruction.Exec
            for i in range(Instruction.Count or 64):  # 0 means 64
                Instruction = await GetNextIncomingInstruction()
                ReplayBuffer[(Index + i) % 32] = Instruction
                if Exec:
                    yield Instruction         # execute while recording
        else:                                # playback mode
            Index = Instruction.Index
            for i in range(Instruction.Count or 64):
                yield ReplayBuffer[(Index + i) % 32]
```

### C++ API

```cpp
// sfpi/include/lltt.h
namespace lltt {
    // Record next `length` instructions into replay buffer starting at `start`
    template<ExecBool E = NoExec>
    inline void record(unsigned start, unsigned length) {
        __builtin_rvtt_ttreplay(start, length, bool(E), true);
    }

    // Replay `length` instructions from buffer starting at `start`
    inline void replay(unsigned start, unsigned length) {
        __builtin_rvtt_ttreplay(start, length, false, false);
    }

    // Returns a raw REPLAY instruction word for embedding in MopCfg LoopOp
    constexpr uint32_t replay_insn(unsigned start, unsigned length) {
        return (0x04 << 24) | (start << 14) | (length << 4);
    }
}
```

Blackhole convenience wrapper (disables instruction gathering during recording):

```cpp
// ckernel.h
template <ExecBool Exec = NoExec, typename Callable, typename... Args>
inline void load_replay_buf(uint32_t start, uint32_t len, Callable &&f, Args &&...args) {
    disable_gathering();          // CSR 0x7C0 bit 18 — prevents instruction fusion
    lltt::record<Exec>(start, len);
    f(std::forward<Args>(args)...);  // lambda body emits instructions into buffer
    enable_gathering();
}
```

### Replay Performance

| Mode | Ingestion | Emission |
|------|-----------|----------|
| Pass-through (non-REPLAY) | 1/cycle | 1/cycle |
| Playback (`Load=0`) | 0 (stalls incoming) | 1/cycle from buffer |
| Record+Execute (`Load=1, Exec=1`) | 1/cycle | 1/cycle |
| Record only (`Load=1, Exec=0`) | 1/cycle | 0 |

**No transition penalties** when switching between modes.

During playback, incoming instructions accumulate in the upstream FIFO/MOP expander
(up to 32 slots). The replay expander does not consume from the incoming stream until
playback completes.

---

## MOP + Replay Composition

The typical high-throughput pattern: MOP emits REPLAY instructions as its loop body,
which the Replay Expander then further expands. This gives two levels of expansion
from a single RISC-V instruction.

### Example: Matmul

```cpp
// Step 1: Record 16 MVMUL instructions into replay buffer slots 16..31
load_replay_buf<ExecBool::Exec>(16, 16, [&]{
    TTI_MVMUL(CLR_NONE, 0, ADDR_MOD_0, 0);   // slot 16
    TTI_MVMUL(CLR_NONE, 0, ADDR_MOD_1, 0);   // slot 17
    // ... 14 more MVMULs with varying addr modes
});

// Step 2: Program MOP Template 1 with LoopOp = REPLAY(16, 16)
ckernel_template tmp(1, fidelity_phases,
    lltt::replay_insn(16, 16));               // LoopOp
tmp.set_last_outer_loop_instr(
    TT_OP_MVMUL(CLR_A, 0, ADDR_MOD_3, 0));   // Loop0Last: clear accum
tmp.program();

// Step 3: Per tile — one instruction, RISC-V is free
ckernel_template::run();   // TTI_MOP(1, 0, 0)
```

Expansion chain:
```
MOP(1, 0, 0)                                        [1 RISC-V instruction]
  -> MOP Expander emits REPLAY(16, 16) x fidelity    [fidelity REPLAY words]
    -> Replay Expander emits 16 MVMULs x fidelity    [16*fidelity backend ops]
```

### Example: SFPU tile-wide add

```cpp
// Record 4 SFPU instructions into slots 0..3
lltt::record(0, 4);
TTI_SFPLOAD(LREG0, 0, ADDR_MOD_7, 0);
TTI_SFPADD(LREG0, LCONST_0, LREG0, LREG0, 0);
TTI_SFPSTORE(LREG0, 0, ADDR_MOD_7, 0);
TTI_INCRWC(0, 2, 0, 0);

// Program MOP: 32 inner iterations, body = REPLAY(0, 4)
ckernel_template tmp(1, 32, lltt::replay_insn(0, 4));
tmp.program();
ckernel_template::run();
// -> 32 x (SFPLOAD + SFPADD + SFPSTORE + INCRWC) = 128 backend instructions
```

### Example: Replay without MOP

For shorter sequences, replay can be used standalone without MOP:

```c
// Record 5 SFPU instructions, executing them as they're recorded
TTI_REPLAY(0, 5, 1, 1);     // record+execute, slots 0..4
TTI_SFPLOAD(...);            // slot 0
TTI_SFPADD(...);             // slot 1
TTI_SFPNOP;                  // slot 2
TTI_SFPSTORE(...);           // slot 3
TTI_INCRWC(...);             // slot 4

// Replay 6 more times
TTI_REPLAY(0, 5, 0, 0);     // playback
TTI_REPLAY(0, 5, 0, 0);
TTI_REPLAY(0, 5, 0, 0);
TTI_REPLAY(0, 5, 0, 0);
TTI_REPLAY(0, 5, 0, 0);
TTI_REPLAY(0, 5, 0, 0);
```

---

## Emulator Implementation

### State per thread

```python
class MOPExpander:
    def __init__(self):
        self.mop_cfg = [0] * 9    # write-only from RISC-V at 0xFFB80000
        self.mask_hi = 0          # set by MOP_CFG instruction (opcode 0x03)
        self.busy = False         # for qstatus CSR bit 1

class ReplayExpander:
    def __init__(self):
        self.buffer = [0] * 32    # not memory-mapped; no CPU address
        self.busy = False         # for qstatus CSR bit 0

class TensixThread:
    def __init__(self, thread_id):
        self.input_fifo = deque(maxlen=32)
        self.mop = MOPExpander()
        self.replay = ReplayExpander()
```

### MMIO intercepts

| Address | Width | Access | Meaning |
|---------|-------|--------|---------|
| `0xFFB80000 + i*4` (i=0..8) | 32-bit | Write-only | `MopCfg[i]` for the calling TRISC's thread |

Writes from TRISC0 go to T0's MopCfg, TRISC1 to T1's, TRISC2 to T2's. The address
is the same (`0xFFB80000`) for all three — hardware routes by source core.

### CSR `0xBC0` (tensix_queue_status)

Read-only CSR accessible from any TRISC. Reports busy state of frontend and backend
units for the reading thread.

```python
def read_qstatus(thread):
    status = 0
    status |= (thread.replay.busy << 0)    # bit 0: replay expander busy (this thread)
    status |= (thread.mop.busy << 1)       # bit 1: MOP expander busy (this thread)
    # bits 2-12: thcon, xmov, unpack, pack, cfg, sync, tdma, sfpu, fpu, sfpucc
    status |= (any_thread_replay_busy << 13)  # bit 13: any thread's replay busy
    status |= (any_thread_mop_busy << 14)     # bit 14: any thread's MOP busy
    return status
```

### Edge cases that must be replicated

1. **Hardware bug in Template 1**: When `OuterCount==1 && IsNop(StartOp) && InnerCount==0 && !IsNop(EndOp0)`, then `OuterCount += 128`. This is in the ISA spec and real kernels may depend on it.

2. **LoopOp alternation**: When `LoopOp1` is non-NOP, the inner loop XOR-flips between `LoopOp` and `LoopOp1` each iteration, and `InnerCount` doubles. The last-iteration override (Loop0Last/Loop1Last) replaces whichever instruction would have been emitted.

3. **IsNop semantics**: Only opcode `0x02` (plain NOP) is recognized as NOP. `DMANOP` (opcode `0x60`) and `SFPNOP` (opcode `0x8F`) are **not** NOP for this purpose. If `StartOp` is set to `DMANOP`, it will be emitted — it won't be skipped.

4. **REPLAY Count=0 means 64**: Not 0, not 32 — exactly 64 instructions, wrapping through the buffer twice.

5. **Replay buffer wraps mod 32**: `ReplayBuffer[(Index + i) % 32]`.

6. **MopCfg is write-only**: Reads return undefined values. Only writes are meaningful.

7. **MopCfg is sampled during expansion**: The ISA docs note the hardware "mostly samples values as required during the expansion process." Software must not change MopCfg while a MOP is expanding. The emulator should snapshot at expansion start (matching the functional model) or implement live-sampling with a warning.

8. **mop_sync**: A blocking store to `pc_buf_base[2]` (`PC_BUF_BASE + 8`). The store does not complete until the MOP expansion finishes. The emulator must stall the RISC-V core on this write until the MOP expander is idle.

### What can be skipped for functional (non-cycle-accurate) emulation

- **Instruction gathering** (CSR `0x7C0` bit 18): Only affects cycle-level timing of `.ttinsn` fusion, not functional correctness.
- **FIFO backpressure**: If not cycle-accurate, expand MOP and REPLAY synchronously without modeling FIFO occupancy.
- **1-cycle MOP transition penalty**: Cycle-level detail only.
- **RESOURCEDECL** (opcode `0x05`): Resource usage hints for hardware scheduling. Has no effect on instruction semantics.

---

## Assembly Encoding

The `.ttinsn` mechanism rotates the 32-bit Tensix word left by 2 bits for encoding in
the RISC-V instruction stream. The emulator reverses this:

```python
tensix_word = ((encoded >> 2) | (encoded << 30)) & 0xFFFFFFFF
```

Assembly mnemonics (from disassembly):

```asm
ttmop      1,0,0          # MOP Template 1, Count1=0, MaskLo=0
ttmop_cfg  0xABCD         # MOP_CFG with MaskHi=0xABCD
ttreplay   0,5,1,1        # REPLAY: start=0, len=5, exec=1, load=1
ttreplay   16,16,0,1      # REPLAY: record 16 insns at slots 16..31
ttreplay   0,5,0,0        # REPLAY: playback 5 insns from slot 0
```

Binary encoding examples:

| Hex (after `.ttinsn` rotate) | Tensix word | Meaning |
|-----|-------------|---------|
| `0x06000000` | `MOP(1,0,0)` | Template 1 double-loop |
| `0x10100404` | `REPLAY(16,16,0,1)` | Record 16 slots starting at 16 |
| `0x1000014C` | `REPLAY(0,5,1,1)` | Record+execute 5 slots at 0 |
| `0x10000140` | `REPLAY(0,5,0,0)` | Playback 5 slots from 0 |

---

## Source References

- MOP Expander spec: `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/MOPExpander.md`
- MOP instruction: `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/MOP.md`
- MOP_CFG instruction: `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/MOP_CFG.md`
- REPLAY instruction: `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/REPLAY.md`
- Instruction encoding macros: `tt-llk/tt_llk_blackhole/common/inc/ckernel_ops.h`
- ckernel_template class: `tt-llk/tt_llk_blackhole/common/inc/ckernel_template.h`
- lltt C++ API: `sfpi/include/lltt.h`
- MopCfg base address: `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/tensix.h` (`TENSIX_MOP_CFG_BASE = 0xFFB80000`)
- Assembly YAML (instruction fields): `tt-llk/tt_llk_blackhole/instructions/assembly.yaml` (MOP at line 3339, REPLAY at line 3388)
- Queue status CSR: `tt-llk/tt_llk_blackhole/common/inc/ckernel.h` (`qstatus_u` union)
- Matmul MOP+replay usage: `tt-llk/tt_llk_blackhole/llk_lib/llk_math_matmul.h`
- SFPU replay patterns: `tt-llk/tt_llk_blackhole/common/inc/sfpu/ckernel_sfpu_welfords.h`
- Developer guide: `boop-docs/kernel-dev/replay-buffer-and-mop-for-sfpu.md`
