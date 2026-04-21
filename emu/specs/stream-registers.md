# Stream / NOC Overlay Registers — Blackhole Tensix Emulation

## 1. Address Space

64 streams per tile at base `0xFFB40000`, stride `0x1000` per stream, total 256 KiB.

```
STREAM_REG_ADDR(stream_id, reg_id) = 0xFFB40000 + stream_id * 0x1000 + reg_id * 4
```

## 2. CB-to-Stream Mapping (Blackhole-specific)

On Blackhole, `OPERAND_START_STREAM = 0`, so CB N maps directly to stream N (streams 0–63).

Sources:
- `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/stream_io_map.h`: `OPERAND_START_STREAM = 0`; `get_operand_stream_id(operand)` returns `OPERAND_START_STREAM + operand`.
- `tt-metal/tt_metal/hw/firmware/src/tt-1xx/trisc.cc`: `init_sync_registers()` iterates via `get_operand_stream_id(operand)`, confirming streams 0..NUM_CIRCULAR_BUFFERS-1.

Note: Wormhole used `OPERAND_START_STREAM = 8`. Blackhole reset this to 0. Do not apply a +8 offset in the emulator.

## 3. Critical Registers for CB Synchronization

Only two register indices within each stream matter for CB operation:

| Reg Index | Byte Offset | Name | Access | Purpose |
|-----------|-------------|------|--------|---------|
| 8 | `+0x020` | `STREAM_REMOTE_DEST_BUF_START_REG_INDEX` | R/W | `tiles_acked` counter |
| 10 | `+0x028` | `STREAM_REMOTE_DEST_BUF_SIZE_REG_INDEX` | R/W | `tiles_received` counter |

CB API mapping:
- `cb_push_back(cb, n)` — atomically adds n to `tiles_received` at stream cb, reg 10
- `cb_wait_front(cb, n)` — polls `tiles_received` at stream cb, reg 10 until (received - acked) >= n
- `cb_pop_front(cb, n)` — atomically adds n to `tiles_acked` at stream cb, reg 8
- `cb_reserve_back(cb, n)` — polls `tiles_acked` at stream cb, reg 8 until (acked + n - received) <= num_pages

TRISC0 zeroes both registers for all CBs during `init_sync_registers()` (triggered by `RUN_SYNC_MSG_INIT_SYNC_REGISTERS = 0x03` from BRISC). The zeroing loop steps through streams 0–63 (or however many CBs are active based on `NUM_CIRCULAR_BUFFERS`).

## 4. Sync Register (General Purpose)

| Reg Index | Byte Offset | Name | Access | Purpose |
|-----------|-------------|------|--------|---------|
| 31 | `+0x07C` | `STREAM_PHASE_AUTO_CFG_PTR_REG_INDEX` | R/W | General-purpose sync register, used by BRISC/NCRISC for kernel-to-dispatch signaling |

Used by `get_sync_register_ptr()` in firmware.

## 5. Dispatch Signaling (Stream 48)

The dispatch message address is:
```
DISPATCH_MESSAGE_ADDR = 0xFFB40000 + (48 * 0x1000) + (270 * 4) = 0xFFB70438
```

Register 270 (`STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_UPDATE_REG_INDEX`) at stream 48 is the dispatch signaling register. The `dispatch_message_offset` field in `go_msg_t` selects which stream offset from base 48 to use. Firmware computes this via `firmware_common.h:calculate_dispatch_addr()`.

For basic emulation (slow dispatch, no fast dispatch pipeline), this register only needs to be a write sink. For fast dispatch, it needs to trigger the dispatch completion protocol.

## 6. Emulator Implementation

Model the stream register space as a sparse array. Only implement:

1. **Streams 0–63, regs 8 and 10**: These are the CB tile counters. Initialize to 0. Support read and write.
2. **Stream 0, reg 31**: Sync register pointer. Simple read/write.
3. **Stream 48, reg 270**: Dispatch signaling. Write sink for slow dispatch; completion trigger for fast dispatch.

All other stream registers can return 0 on read and accept writes silently.

```python
class StreamRegisters:
    def __init__(self):
        # Only need reg 8 (tiles_acked) and reg 10 (tiles_received) per stream
        self.tiles_acked = [0] * 64     # stream N -> tiles_acked
        self.tiles_received = [0] * 64  # stream N -> tiles_received
        self.sync_reg = 0               # stream 0 reg 31
        self.dispatch_msg = 0           # stream 48 reg 270

    def read(self, stream_id, reg_id):
        if reg_id == 8 and stream_id < 64:
            return self.tiles_acked[stream_id]
        elif reg_id == 10 and stream_id < 64:
            return self.tiles_received[stream_id]
        elif stream_id == 0 and reg_id == 31:
            return self.sync_reg
        return 0

    def write(self, stream_id, reg_id, value):
        if reg_id == 8 and stream_id < 64:
            self.tiles_acked[stream_id] = value
        elif reg_id == 10 and stream_id < 64:
            self.tiles_received[stream_id] = value
        elif stream_id == 0 and reg_id == 31:
            self.sync_reg = value
        elif stream_id == 48 and reg_id == 270:
            self.dispatch_msg = value
```

## 7. init_sync_registers() Zeroing Pattern

When TRISC0 receives `RUN_SYNC_MSG_INIT_SYNC_REGISTERS` (0x03), it zeroes the CB tile counters:

```python
for cb in range(NUM_CIRCULAR_BUFFERS):  # 64 on Blackhole
    stream_regs.write(cb, 8, 0)   # tiles_acked = 0
    stream_regs.write(cb, 10, 0)  # tiles_received = 0
```

## 8. Source References

| Symbol / Function | Source File |
|-------------------|-------------|
| `OPERAND_START_STREAM`, CB-to-stream mapping | `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/stream_io_map.h` |
| `STREAM_REMOTE_DEST_BUF_START_REG_INDEX` (reg 8) | `tt-metal/tt_metal/hw/inc/tt_metal/hw/inc/blackhole/noc/stream_io_map.h` |
| `STREAM_REMOTE_DEST_BUF_SIZE_REG_INDEX` (reg 10) | `tt-metal/tt_metal/hw/inc/tt_metal/hw/inc/blackhole/noc/stream_io_map.h` |
| `STREAM_PHASE_AUTO_CFG_PTR_REG_INDEX` (reg 31) | `tt-metal/tt_metal/hw/inc/tt_metal/hw/inc/blackhole/noc/stream_io_map.h` |
| `STREAM_REMOTE_DEST_BUF_SPACE_AVAILABLE_UPDATE_REG_INDEX` (reg 270) | `tt-metal/tt_metal/hw/inc/tt_metal/hw/inc/blackhole/noc/stream_io_map.h` |
| `get_sync_register_ptr()` | `tt-metal/tt_metal/hw/firmware/src/common/firmware_common.h` |
| `calculate_dispatch_addr()` | `tt-metal/tt_metal/hw/firmware/src/common/firmware_common.h` |
| `RUN_SYNC_MSG_INIT_SYNC_REGISTERS` (0x03) | `tt-metal/tt_metal/hw/inc/tt_metal/hw/inc/dev_msgs.h` |
| `init_sync_registers()` | `tt-metal/tt_metal/hw/firmware/src/trisc.cc` |
| `cb_push_back`, `cb_wait_front`, `cb_pop_front`, `cb_reserve_back` | `tt-metal/tt_metal/hw/inc/tt_metal/hw/inc/circular_buffer_init.h` |
| `go_msg_t`, `dispatch_message_offset` | `tt-metal/tt_metal/hw/inc/tt_metal/hw/inc/dev_msgs.h` |
