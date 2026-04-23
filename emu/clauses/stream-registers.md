# stream-registers

**Source:** [`stream-registers.md`](../specs/stream-registers.md)

## Address space

### `STREG.ADDR.BASE`
§1 Address Space

> 64 streams per tile at base 0xFFB40000, stride 0x1000 per stream, total 256 KiB.

### `STREG.ADDR.FORMULA`
_§1 Address Space / STREAM_REG_ADDR_

> STREAM_REG_ADDR(stream_id, reg_id) = 0xFFB40000 + stream_id*0x1000 + reg_id*4.

### `STREG.CB.TILES_ACKED_REG`
§3 Critical Registers / reg 8

> Reg 8 (+0x020) within each stream is tiles_acked (cb_pop_front target).

### `STREG.CB.TILES_RECEIVED_REG`
§3 Critical Registers / reg 10

> Reg 10 (+0x028) within each stream is tiles_received (cb_push_back target).

### `STREG.CB.WRITE_VISIBLE`
§6 Emulator Implementation

> Write to tiles_received/tiles_acked on a tile's stream regs is visible to all cores on that tile.

### `STREG.CB.ISOLATION_FROM_L1`
§6 Emulator Implementation

> Stream registers are a separate Memory from L1; a write to a stream-reg address must not modify L1.

### `STREG.CB.REMOTE_ATOMIC`
§3 CB Synchronization / remote atomic

> A remote NOC atomic increment targeting a tile's tiles_received address lands in that tile's StreamRegisters, not its L1. The tile_bus Router dispatches based on address range.

### `STREG.SYNC.STREAM0_REG31`
§4 Sync Register

> Stream 0, reg 31 (+0x07C) is a general-purpose sync register pointer (BRISC/NCRISC).

### `STREG.DISPATCH.ADDR`
§5 Dispatch Signaling

> DISPATCH_MESSAGE_ADDR = 0xFFB40000 + 48*0x1000 + 270*4 = 0xFFB70438.

### `STREG.DISPATCH.STREAM_ID`
§5 Dispatch Signaling / stream 48

> Dispatch signaling uses stream 48, reg 270.

### `STREG.IMPL.SPARSE`
§6 Emulator Implementation

> Stream register space is modeled as a sparse array; unwritten addresses read 0.
