# pcbufs

**Source:** [`pcbufs.md`](../specs/pcbufs.md) · **Emulator:** `blackhole-py/extra/emu/tensix/__init__.py`

## Address map

### `PCBUF.ADDR.T0`
§Addresses

> PCBuf[0] is at 0xFFE80000 (PC_BUF_BASE), direction BRISC → TRISC0.

### `PCBUF.ADDR.T1`
§Addresses

> PCBuf[1] is at 0xFFE90000 (PC1_BUF_BASE), direction BRISC → TRISC1.

### `PCBUF.ADDR.T2`
§Addresses

> PCBuf[2] is at 0xFFEA0000 (PC2_BUF_BASE), direction BRISC → TRISC2.

### `PCBUF.ADDR.STRIDE`
§Addresses

> PCBuf stride between threads is 0x10000.

### `PCBUF.MMAP.OFFSET_00_FIFO_POP`
§Memory Map Within Each PCBuf / offset 0x00

> Offset 0x00: FIFO pop. TRISC read blocks until a value is available.

### `PCBUF.MMAP.OFFSET_04_COPROC_DONE`
§Memory Map Within Each PCBuf / offset 0x04

> Offset 0x04: CoprocessorDoneCheck. TRISC read blocks until this TRISC's coprocessor thread is idle (no in-flight instructions). Used by tensix_sync().

### `PCBUF.MMAP.OFFSET_08_MOP_DONE`
§Memory Map Within Each PCBuf / offset 0x08

> Offset 0x08: MOPExpanderDoneCheck. TRISC read blocks until the MOP expander has finished expanding. Used by mop_sync().

### `PCBUF.MMAP.OFFSET_20_SEM_WINDOW`
§Memory Map Within Each PCBuf / offsets 0x20-0x3C

> Offsets 0x20-0x3C: 8 semaphore access words (one per hardware semaphore). All three TRISCs use the same window at 0xFFE80020-0xFFE8003C.

### `PCBUF.SEM.READ_RETURNS_VALUE`
§Semaphore Window

> Reading semaphore window word i returns the current value of semaphore i.

### `PCBUF.SEM.WRITE_0_IS_POST`
§Semaphore Window

> Write to semaphore window with bit 0 == 0 performs SEMPOST (increment) on that semaphore.

### `PCBUF.SEM.WRITE_1_IS_GET`
§Semaphore Window

> Write to semaphore window with bit 0 == 1 performs SEMGET (decrement) on that semaphore.

### `PCBUF.BRISC_READ.THREE_CONDITION_BARRIER`
§BRISC Read Semantics (Sync Barrier)

> A BRISC read from PCBuf base is a three-condition hardware barrier. It blocks until ALL of: FIFO fully drained, TRISC blocking on PCBuf read, and Tensix coprocessor thread for that TRISC is idle.

### `PCBUF.EMU.READ_PCBUF_RETURNS_ZERO`
§Emulator Implementation

> In functional emulation (synchronous dispatch), read_pcbuf() resolves immediately and returns 0.

### `PCBUF.FIFO.CAPACITY_16`
§Emulator Implementation

> Each PCBuf has a 16-entry FIFO of uint32_t.
