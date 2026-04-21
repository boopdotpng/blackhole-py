# stallwait-conditions

**Source:** [`stallwait-conditions.md`](../specs/stallwait-conditions.md) · **Emulator:** `blackhole-py/extra/emu/tensix/frontend.py`

## Instruction encoding

### `SW.ENCODING.STALLWAIT`
§Instruction Encodings / STALLWAIT

> STALLWAIT: opcode=0xA2; word[23:15] = stall_res (9 bits); word[12:0] = wait_res (13 bits).

### `SW.ENCODING.SEMWAIT`
§Instruction Encodings / SEMWAIT

> SEMWAIT: opcode=0xA6; word[23:15] = stall_res (9 bits); word[9:2] = sem_sel (8 bits); word[1:0] = wait_sem_cond (2 bits).

### `SW.BLOCK.STALL_TDMA_B0`
_§stall_res — Block Mask / B0_

> B0 (STALL_TDMA=0x01): blocks Misc Unit, Mover, ThCon, Packer instructions.

### `SW.BLOCK.STALL_SYNC_B1`
_§stall_res — Block Mask / B1_

> B1 (STALL_SYNC=0x02): blocks Sync Unit instructions.

### `SW.BLOCK.STALL_MATH_B6`
_§stall_res — Block Mask / B6_

> B6 (STALL_MATH=0x40): blocks Matrix Unit (FPU) instructions.

### `SW.BLOCK.STALL_CFG_B7`
_§stall_res — Block Mask / B7_

> B7 (STALL_CFG=0x80): blocks Configuration Unit instructions.

### `SW.BLOCK.DEFAULT_STALL_MATH`
_§stall_res — Block Mask / Default_

> Default when stall_res==0: hardware treats it as 1<<6 = STALL_MATH (B6 only).

### `SW.BLOCK.NOP_NEEDS_ALL_BITS`
_§stall_res — Block Mask / Special cases_

> NOP is blocked only if ALL block bits B0–B8 are set.

### `SW.BLOCK.FRONTEND_NEVER_BLOCKED`
_§stall_res — Block Mask / Special cases_

> MOP, MOP_CFG, REPLAY, RESOURCEDECL are never blocked by the Wait Gate.

### `SW.COND.DEFAULT_0F`
_§wait_res — Condition Mask / Default when wait_res==0_

> Default when wait_res==0 in STALLWAIT: hardware uses 0x0F (C0|C1|C2|C3).

### `SW.COND.C5_SRCA_CLR`
_§wait_res / C5 SRCA_CLR_

> C5 (SRCA_CLR=0x020): keep waiting while SrcA unpack-bank AllowedClient != 'unpackers'.

### `SW.COND.C6_SRCB_CLR`
_§wait_res / C6 SRCB_CLR_

> C6 (SRCB_CLR=0x040): keep waiting while SrcB unpack-bank AllowedClient != 'unpackers'.

### `SW.COND.C7_SRCA_VLD`
_§wait_res / C7 SRCA_VLD_

> C7 (SRCA_VLD=0x080): keep waiting while SrcA FPU-bank AllowedClient != 'matrix_unit'.

### `SW.COND.C8_SRCB_VLD`
_§wait_res / C8 SRCB_VLD_

> C8 (SRCB_VLD=0x100): keep waiting while SrcB FPU-bank AllowedClient != 'matrix_unit'.

### `SW.COND.PIPELINE_OCCUPANCY_IDLE`
§Emulator Implementation Notes

> In functional (synchronous) emulation, pipeline occupancy signals (C0-C4, C9-C12) are always cleared — only bank ownership (C5-C8) matters.

### `SW.GATE.RELEASES_WHEN_CONDITION_CLEAR`
§The Wait Gate / Python pseudocode

> The Wait Gate latch is released (opcode set to None) when the condition evaluates to False (all selected conditions simultaneously cleared).

### `SW.GATE.BLOCKS_MATCHING_CATEGORY`
_§The Wait Gate / can_instruction_pass_

> While condition is active, only instructions whose block_bits & block_mask != 0 are held. Instructions in non-blocked categories pass through.

### `SW.GATE.PER_THREAD_INDEPENDENCE`
§The Wait Gate / Per-thread independence

> Each of the three Tensix threads has its own independent Wait Gate. A STALLWAIT in T0 does not affect T1 or T2.

### `SW.SEMWAIT.STALL_ON_ZERO`
_§SEMWAIT — Condition Fields / wait_sem_cond_

> STALL_ON_ZERO (C0=1): keep waiting while any selected semaphore has value == 0.

### `SW.SEMWAIT.STALL_ON_MAX`
_§SEMWAIT — Condition Fields / wait_sem_cond_

> STALL_ON_MAX (C1=1): keep waiting while any selected semaphore has value >= max.

### `SW.SEMWAIT.SEM_SEL_BITMASK`
_§SEMWAIT — sem_sel_

> sem_sel is an 8-bit bitmask; bit i selects semaphore i. Multiple bits may be set to wait on multiple semaphores simultaneously.

### `SW.SEMWAIT.MULTI_SEM_ALL_MUST_CLEAR`
_§SEMWAIT — sem_sel_

> When multiple semaphore bits are set, the SEMWAIT is released only when the condition is simultaneously cleared on ALL selected semaphores.
