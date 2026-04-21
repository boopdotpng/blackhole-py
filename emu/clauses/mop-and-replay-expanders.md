# mop-and-replay-expanders

**Source:** [`mop-and-replay-expanders.md`](../specs/mop-and-replay-expanders.md) · **Emulator:** `blackhole-py/emu/tensix/frontend.py`

## MOP: instruction encoding

### `MOP.OPCODE.MOP`
§MOP Expander / Instruction: MOP (opcode 0x01)

> MOP has opcode 0x01; bit[23] = Template; bits[22:16] = Count1; bits[15:0] = MaskLo.

### `MOP.OPCODE.MOP_CFG`
_§MOP Expander / Instruction: MOP_CFG (opcode 0x03)_

> MOP_CFG has opcode 0x03; bits[15:0] = MaskHi. Consumed by expander without emission.

### `MOP.OPCODE.PASSTHROUGH`
§MOP Expander / Functional Model

> All opcodes other than 0x01 (MOP) and 0x03 (MOP_CFG) pass through the MOP Expander unchanged.

### `MOP.MOPCFG.9_REGS`
§Configuration Registers (MopCfg)

> 9 × 32-bit write-only registers per thread at TENSIX_MOP_CFG_BASE = 0xFFB80000.

### `MOP.MOPCFG.WRITE_ONLY`
§Edge cases / MopCfg is write-only

> MopCfg reads return undefined values. Only writes are meaningful.

### `MOP.T0.ITERATION_COUNT`
§Template 0: Unpack Zero-Mask Loop

> Template 0 iterates Count1 + 1 times (Count1 from MOP instruction bits[22:16]).

### `MOP.T0.MASK_SELECTS_PATH`
§Template 0: Unpack Zero-Mask Loop

> In each iteration i, if (Mask >> i) & 1 == 0 emit InsnA0 (plus optional A1-A3, B); otherwise emit SkipA0 (plus optional SkipB).

### `MOP.T0.MASK32_FROM_CFG_AND_MOP`
_§Template 0 / MOP_CFG_

> Full 32-bit mask = (MaskHi << 16) | MaskLo from MOP_CFG and MOP instruction.

### `MOP.T0.HAS_B`
§Configuration Registers (MopCfg) / Template 0

> MopCfg[1] bit 0 = HasB. When set, InsnB (cfg[2]) / SkipB (cfg[8]) are emitted.

### `MOP.T0.HAS_A123`
§Configuration Registers (MopCfg) / Template 0

> MopCfg[1] bit 1 = HasA123. When set, InsnA1/A2/A3 (cfg[4-6]) are emitted after InsnA0.

### `MOP.T1.OUTER_INNER_LOOP`
§Template 1: Double-Nested Loop

> Template 1 implements a double-nested loop: OuterCount (cfg[0] & 127) outer iterations and InnerCount (cfg[1] & 127) inner iterations.

### `MOP.T1.START_OP_EMITTED`
§Template 1 / Functional Model

> StartOp (cfg[2]) is emitted once per outer iteration, unless it is NOP.

### `MOP.T1.END_OPS_EMITTED`
§Template 1 / Functional Model

> EndOp0 (cfg[3]) is emitted after each inner loop, unless NOP. EndOp1 (cfg[4]) is emitted after EndOp0, unless EndOp0 or EndOp1 is NOP.

### `MOP.T1.LOOP0_LAST_OVERRIDE`
§Template 1 / Functional Model

> On the last inner iteration of the last outer iteration, Loop0Last (cfg[7]) is emitted instead of LoopOp.

### `MOP.T1.LOOP1_LAST_OVERRIDE`
§Template 1 / Functional Model

> On the last inner iteration of a non-last outer iteration, Loop1Last (cfg[8]) is emitted instead of LoopOp.

### `MOP.T1.ALTERNATING_LOOP_OP`
§Edge cases / LoopOp alternation

> When LoopOp1 (cfg[6]) is non-NOP, the inner loop XOR-flips between LoopOp and LoopOp1 each iteration, and InnerCount doubles.

### `MOP.T1.HW_BUG_OUTER_COUNT`
§Edge cases / Hardware bug in Template 1

> Hardware bug (must be replicated): when OuterCount==1 AND IsNop(StartOp) AND InnerCount==0 AND NOT IsNop(EndOp0), then OuterCount += 128 (becomes 129).

### `MOP.ISNOP.ONLY_OPCODE_02`
§Edge cases / IsNop semantics

> Only opcode 0x02 (plain NOP) is recognized as NOP for MOP expansion. DMANOP (opcode 0x60) and SFPNOP (opcode 0x8F) are NOT NOP here.

### `REPLAY.OPCODE`
§Replay Expander / Instruction: REPLAY (opcode 0x04)

> REPLAY has opcode 0x04; bits[23:14] = start_idx (low 5 bits used); bits[13:4] = len (low 6 bits; 0 means 64); bit[1] = exec_while_loading; bit[0] = load_mode.

### `REPLAY.PASSTHROUGH`
§Replay Expander / Functional Model

> All instructions other than opcode 0x04 pass through the Replay Expander unchanged.

### `REPLAY.BUFFER_32_SLOTS`
§Replay Expander / Replay Buffer

> 32-slot × 32-bit circular buffer per thread. No CPU-accessible address.

### `REPLAY.RECORD.STORES_INSTRUCTIONS`
_§Replay Expander / Functional Model / load_mode=1_

> When load_mode=1, the next `len` instructions from the upstream pipeline are stored into ReplayBuffer[(start_idx + i) % 32] for i in 0..len-1.

### `REPLAY.RECORD.EXEC_WHILE_LOADING`
_§Replay Expander / Functional Model / exec_while_loading_

> When load_mode=1 and exec_while_loading=1, each recorded instruction is also emitted downstream as it is recorded.

### `REPLAY.RECORD.NO_OUTPUT_WHEN_EXEC_0`
§Replay Expander / Functional Model

> When load_mode=1 and exec_while_loading=0, recording produces no downstream output.

### `REPLAY.PLAYBACK.EMITS_FROM_BUFFER`
_§Replay Expander / Functional Model / load_mode=0_

> When load_mode=0, emits `len` instructions from ReplayBuffer[(start_idx + i) % 32] for i in 0..len-1.

### `REPLAY.PLAYBACK.WRAP_MOD32`
§Edge cases / Replay buffer wraps mod 32

> Replay buffer index wraps mod 32 during both record and playback.

### `REPLAY.COUNT_ZERO_MEANS_64`
§Edge cases / REPLAY Count=0 means 64

> A REPLAY instruction with len=0 replays exactly 64 instructions (wrapping the buffer twice).
