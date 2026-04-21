# instruction-push

**Source:** [`instruction-push.md`](../specs/instruction-push.md) · **Emulator:** `blackhole-py/emu/tensix/frontend.py`

## MMIO path

### `IPUSH.MMIO.WRITE_PUSHES_WORD`
§1. MMIO Store

> A plain sw to INSTRN_BUF_BASE (0xFFE40000) pushes the 32-bit instruction word into the per-thread instruction FIFO.

### `IPUSH.MMIO.ROUTING_BRISC`
§Address Routing table

> BRISC write to 0xFFE40000 pushes to T0; 0xFFE50000 pushes to T1; 0xFFE60000 pushes to T2.

### `IPUSH.MMIO.ROUTING_TRISC`
§Address Routing table

> Each TRISC writes only to 0xFFE40000; the hardware routes the write to that TRISC's own thread (T0/T1/T2 respectively).

### `IPUSH.TTINSN.ROT_LEFT_2`
§2. .ttinsn Inline Instruction

> The 32-bit Tensix opcode is rotated left by 2 bits for encoding in the RISC-V instruction stream. The hardware rotates right by 2 to recover the original instruction word.

### `IPUSH.TTINSN.LOW_BITS_NOT_11`
§2. .ttinsn Inline Instruction

> Valid Tensix opcodes are < 0xC0000000, so the low 2 bits of the encoded word are never 0b11 (which would mark a standard 32-bit RISC-V instruction). The hardware detects this to identify .ttinsn words.

### `IPUSH.FIFO.CAPACITY_32`
§FIFO Behavior

> Capacity: 32 entries per thread.

### `IPUSH.FIFO.FULL_REJECTS_PUSH`
§FIFO Behavior

> Non-blocking until full, then the RISC-V core hardware-stalls transparently. Emulator: push() returns False when full.

### `IPUSH.FIFO.ORDERING`
§FIFO Behavior

> Instructions are consumed FIFO-ordered (first-in, first-out).

### `IPUSH.FIFO.POP_EMPTY_RETURNS_NONE`
§Emulator Implementation

> In the emulator, pop() on an empty FIFO returns None (stall signal to the MOP Expander).

### `IPUSH.BRISC.BYPASSES_MOP`
§BRISC Coprocessor Access (tensix-coprocessor-pipeline.md)

> BRISC's pushes enter after the MOP Expander, bypassing MOP expansion. BRISC cannot issue MOP instructions.

