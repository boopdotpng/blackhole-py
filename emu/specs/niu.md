# NIU Emulator Specification (Blackhole)

## 1. Address Space Overview

Each Tensix tile has **2 NIU instances** (NoC0 and NoC1), memory-mapped into the tile's private address space:

| NIU | Base Address | Size |
|-----|-------------|------|
| NoC0 | `0xFFB20000` | `0x10000` |
| NoC1 | `0xFFB30000` | `0x10000` |

The formula firmware uses to compute a register's absolute address:

```
addr = (buf << 11) + (noc << 16) + register_offset
```

Where `register_offset` already includes the `0xFFB20000` base (the defines in `noc_parameters.h` are absolute addresses). For the emulator, offsets from the NIU base are:

| Region | Offset Range | Description |
|--------|-------------|-------------|
| **Command Buffers** | `0x0000`-`0x1FFF` | 4 buffers x 0x800 stride |
| **Misc Control** | `0x0040`-`0x0068` | CMD_CTRL, NODE_ID, ECC, CMD_BUF_AVAIL |
| **Configuration** | `0x0100`-`0x017F` | NIU_CFG_0, ROUTER_CFG, translate tables |
| **Status Counters** | `0x0200`-`0x02FF` | 128 x 4-byte counters |
| **Security Fence** | `0x0400`-`0x04A8` | Not needed for emulation |
| **Flit Counters** | `0x0500`-`0x05FF` | Not needed for emulation |

## 2. Command Buffer Registers

4 command buffers at offsets `0x000`, `0x800`, `0x1000`, `0x1800`. Each has this layout:

| Offset | Name | R/W | Description |
|--------|------|-----|-------------|
| `+0x00` | `NOC_TARG_ADDR_LO` | RW | Target address bits [31:0] |
| `+0x04` | `NOC_TARG_ADDR_MID` | RW | Target address bits [63:32] (PCIe: bit 60 set) |
| `+0x08` | `NOC_TARG_ADDR_HI` | RW | Target XY coordinate (see encoding below) |
| `+0x0C` | `NOC_RET_ADDR_LO` | RW | Return/dest address bits [31:0] |
| `+0x10` | `NOC_RET_ADDR_MID` | RW | Return/dest address bits [63:32] |
| `+0x14` | `NOC_RET_ADDR_HI` | RW | Return/dest XY coordinate |
| `+0x18` | `NOC_PACKET_TAG` | RW | `[13:10]` = transaction_id, `[9]` = header_store |
| `+0x1C` | `NOC_CTRL` | RW | Command type/flags (see bitfield below) |
| `+0x20` | `NOC_AT_LEN_BE` | RW | Transfer length in bytes (or byte-enable low word) |
| `+0x24` | `NOC_AT_LEN_BE_1` | RW | Byte-enable high word (for BE writes) |
| `+0x28` | `NOC_AT_DATA` | RW | Inline write data / atomic operand |
| `+0x2C` | `NOC_BRCST_EXCLUDE` | RW | Broadcast exclusion mask |
| `+0x30` | `NOC_L1_ACC_AT_INSTRN` | RW | L1 accumulate atomic instruction encoding |
| `+0x34` | `NOC_SEC_CTRL` | RW | Security control (ignore for emu) |
| `+0x40` | **`NOC_CMD_CTRL`** | RW | **Trigger**: write `0x1` to fire. Reads `0x0` when ready. |
| `+0x44` | `NOC_NODE_ID` | RO | Physical node XY: `{y[5:0], x[5:0]}` |
| `+0x48` | `NOC_ENDPOINT_ID` | RO | Endpoint ID |

**Registers at offsets `+0x44` and `+0x48` read the same value in all 4 command buffers** -- they are shared (the hardware aliases them).

### Conventional buffer assignments (dedicated mode, the common case)

| Buffer | Index | Used for |
|--------|-------|----------|
| WR_CMD_BUF | 0 | Large DMA writes |
| RD_CMD_BUF | 1 | All DMA reads |
| WR_REG_CMD_BUF | 2 | Small register/semaphore writes |
| AT_CMD_BUF | 3 | Atomics (incr_get, CAS, swap, accumulate) |

## 3. NOC_CTRL Bitfield

```
Bit  0: AT       (1 = atomic, 0 = copy)
Bit  1: WR       (1 = write, 0 = read)
Bit  2: WR_BE    (byte-enable write: AT_LEN_BE is a bitmask, not a length)
Bit  3: WR_INLINE (data comes from NOC_AT_DATA register, not from L1)
Bit  4: RESP_MARKED (non-posted: expect ACK; used for barrier tracking)
Bit  5: BRCST_PACKET (multicast)
Bit  6: VC_LINKED (linked VC allocation with previous transaction)
Bit  7: VC_STATIC (use static VC from bits [15:13])
Bit  8: PATH_RESERVE (reserve path for multicast)
Bit  9: MEM_RD_DROP_ACK (drop read ack -- fire-and-forget)
[12:10]: reserved
[15:13]: STATIC_VC (virtual channel number when VC_STATIC=1)
[16]: BRCST_XY (multicast direction flag)
[17]: BRCST_SRC_INCLUDE (include source in multicast)
[26:18]: reserved
[29:27]: ARB_PRIORITY
[30]: reserved
[31]: L1_ACC_AT_EN (enable L1 accumulate atomic)
```

### Transaction type decoding for the emulator

| AT | WR | WR_BE | WR_INLINE | Transaction |
|----|-----|-------|-----------|-------------|
| 0 | 0 | 0 | 0 | **Read**: copy from `TARG` to `RET` |
| 0 | 1 | 0 | 0 | **Write**: copy from `TARG` (local src) to `RET` (remote dest) |
| 0 | 1 | 1 | 0 | **Write with byte-enables**: AT_LEN_BE/BE_1 = 64-bit bitmask |
| 0 | 1 | 0 | 1 | **Inline write**: 4 bytes from NOC_AT_DATA to `TARG` addr |
| 1 | x | x | x | **Atomic**: operation encoded in NOC_L1_ACC_AT_INSTRN or NOC_AT_LEN_BE |

## 4. XY Coordinate Encoding

Coordinates are packed as 6-bit fields:

**Unicast** (in `NOC_TARG_ADDR_HI` / `NOC_RET_ADDR_HI`):
```
[5:0]  = x
[11:6] = y
```

**Multicast** (when `BRCST_PACKET=1`):
```
[5:0]   = end_x
[11:6]  = end_y
[17:12] = start_x
[23:18] = start_y
```

**64-bit address encoding** (as used by the API to build `src_noc_addr` / `dst_noc_addr`):
```
[35:0]  = local address (36-bit)
[41:36] = x
[47:42] = y
```

The API splits these: bits [31:0] go to `ADDR_LO`, bits [35:32] (plus PCIe bit 60 -> bit 28 of MID) go to `ADDR_MID`, and bits [47:36] (the XY coordinate) go to `ADDR_HI`/`ADDR_COORDINATE`.

## 5. Configuration Registers (`0x100 + index*4`)

These are the registers the emulator needs to support (firmware reads/writes them):

| Index | Name | Key bits |
|-------|------|----------|
| `0x00` | `NIU_CFG_0` | `[14]` = NOC_ID_TRANSLATE_EN, `[16]` = CMD_BUFFER_FIFO_EN |
| `0x01` | `ROUTER_CFG_0` | Router config (not needed for functional emu) |
| `0x06`-`0x0B` | `NOC_X_ID_TRANSLATE_TABLE_0..5` | X coordinate translation (6 regs, 6 entries each, 5 bits/entry) |
| `0x0C`-`0x11` | `NOC_Y_ID_TRANSLATE_TABLE_0..5` | Y coordinate translation |
| **`0x12`** | **`NOC_ID_LOGICAL`** | **Logical coordinates: `{y[5:0], x[5:0]}`** |
| `0x14` | `NOC_ID_TRANSLATE_COL_MASK` | Column mask for ID translation |
| `0x15` | `NOC_ID_TRANSLATE_ROW_MASK` | Row mask for ID translation |

**Critical for emulation**: `NOC_ID_LOGICAL` (at absolute address `NIU_base + 0x148`) is what firmware reads during `noc_init()` to discover "who am I." The ARC firmware pre-programs this before tensix cores boot. Your emulator must pre-populate this for each tile.

## 6. Status Counters (`0x200 + index*4`)

These are hardware-maintained monotonically increasing counters. Firmware polls them for barriers ("have all my writes been acked?"). The emulator must **increment them when transactions complete**.

Key counters firmware actually reads:

| Index | Name | When to increment |
|-------|------|-------------------|
| `0x0` | `NIU_MST_ATOMIC_RESP_RECEIVED` | After atomic completes |
| `0x1` | `NIU_MST_WR_ACK_RECEIVED` | After non-posted write ACK received |
| `0x2` | `NIU_MST_RD_RESP_RECEIVED` | After read response received |
| `0x4` | `NIU_MST_CMD_ACCEPTED` | After any command accepted (optional) |
| `0x5` | `NIU_MST_RD_REQ_SENT` | After read request sent |
| `0xA` | `NIU_MST_NONPOSTED_WR_REQ_SENT` | After non-posted write sent |
| `0xB` | `NIU_MST_POSTED_WR_REQ_SENT` | After posted write sent |
| `0x10+id` | `NIU_MST_REQS_OUTSTANDING_ID(id)` | Outstanding count per transaction_id |

**Barrier pattern** (this is what firmware spins on):
```c
// Read barrier: spin until RD_RESP_RECEIVED == local counter
while (NOC_STATUS_READ_REG(noc, NIU_MST_RD_RESP_RECEIVED) != noc_reads_num_issued[noc]);

// Write barrier: spin until WR_ACK_RECEIVED == local counter
while (NOC_STATUS_READ_REG(noc, NIU_MST_WR_ACK_RECEIVED) != noc_nonposted_writes_acked[noc]);
```

For a synchronous emulator: increment counters immediately when `NOC_CMD_CTRL` fires. This makes all barriers resolve on the next load.

## 7. Misc Control Registers (at NIU base)

| Offset | Name | Notes |
|--------|------|-------|
| `0x50` | `NUM_MEM_PARITY_ERR` | Always 0 in emu |
| `0x54` | `NUM_HEADER_1B_ERR` | Always 0 |
| `0x58` | `NUM_HEADER_2B_ERR` | Always 0 |
| `0x5C` | `ECC_CTRL` | Ignore |
| `0x60` | `NOC_CLEAR_OUTSTANDING_REQ_CNT` | Write to clear outstanding request counts by ID mask |
| `0x64` | `CMD_BUF_AVAIL` | `[4:0]`=buf0 slots, `[12:8]`=buf1, `[20:16]`=buf2, `[28:24]`=buf3. Return all-available. |
| `0x68` | `CMD_BUF_OVFL` | Overflow flag, always 0 in emu |

## 8. Transaction Execution (on CMD_CTRL write)

When firmware writes `0x1` to `NOC_CMD_CTRL` at offset `+0x40` of a command buffer:

```python
def fire_cmd(self, buf_idx):
    regs = self.cmd_bufs[buf_idx]
    ctrl = regs[0x1C]  # NOC_CTRL

    is_atomic = ctrl & 1
    is_write  = (ctrl >> 1) & 1
    is_wr_be  = (ctrl >> 2) & 1
    is_inline = (ctrl >> 3) & 1
    is_resp_marked = (ctrl >> 4) & 1  # non-posted
    is_mcast  = (ctrl >> 5) & 1

    targ_lo  = regs[0x00]
    targ_mid = regs[0x04]
    targ_xy  = regs[0x08]
    ret_lo   = regs[0x0C]
    ret_mid  = regs[0x10]
    ret_xy   = regs[0x14]
    length   = regs[0x20]

    if is_atomic:
        # Atomic operation on target, return result to ret addr
        execute_atomic(...)
        self.inc_counter(NIU_MST_ATOMIC_RESP_RECEIVED)
    elif is_write:
        if is_inline:
            # Write NOC_AT_DATA (4 bytes) to targ address
            execute_inline_write(...)
        else:
            # DMA from local TARG addr to remote RET addr
            execute_dma_write(...)
        if is_resp_marked:
            self.inc_counter(NIU_MST_WR_ACK_RECEIVED)
            self.inc_counter(NIU_MST_NONPOSTED_WR_REQ_SENT)
        else:
            self.inc_counter(NIU_MST_POSTED_WR_REQ_SENT)
    else:
        # Read: DMA from remote TARG addr to local RET addr
        execute_dma_read(...)
        self.inc_counter(NIU_MST_RD_RESP_RECEIVED)
```

## 9. Firmware Boot Sequence (what the emulator must handle)

The BRISC firmware `noc_init()` does this for each NoC:

1. **Read `NOC_CFG(NOC_ID_LOGICAL)`** (offset `0x148` from NIU base) to get `my_x`, `my_y`
2. **Pre-program command buffers** with local coordinates:
   - WR_CMD_BUF (0): set `TARG_ADDR_MID=0`, `TARG_ADDR_COORDINATE=my_xy` (local source for writes)
   - WR_REG_CMD_BUF (2): same as above
   - AT_CMD_BUF (3): set `RET_ADDR_LO`, `RET_ADDR_MID=0`, `RET_ADDR_COORDINATE=my_xy` (atomic return addr)
   - RD_CMD_BUF (1): set `NOC_CTRL` to read command flags, `RET_ADDR_MID=0`, `RET_ADDR_COORDINATE=my_xy`
3. **Read status counters** (`noc_local_state_init`): read `RD_RESP_RECEIVED`, `NONPOSTED_WR_REQ_SENT`, `WR_ACK_RECEIVED`, `ATOMIC_RESP_RECEIVED`, `POSTED_WR_REQ_SENT` and store in L1 variables

This means your emulator **must pre-populate** before firmware starts:
- `NOC_CFG(NOC_ID_LOGICAL)` = `(y << 6) | x` for the tile's logical coordinates
- `NOC_NODE_ID` (offset `0x44`) = `(y << 6) | x` for the tile's physical coordinates
- All status counters = `0`

## 10. Disassembly Verification

From the real `add1` kernel disassembly, here's `noc_async_write` (NCRISC, using NoC0, cmd_buf 0):

```asm
; a4 = 0xFFB20000 (NoC0 base, cmd buf 0)
; Wait for CMD_CTRL ready
.L4:
    lw   a5, 64(a4)     ; read NOC_CMD_CTRL (+0x40)
    bnez a5, .L4         ; spin until 0

    ; Write NOC_CTRL = 0x2092 (CPY|WR|RESP_MARKED|VC_STATIC|STATIC_VC(1))
    li   a5, 0x2092
    sw   a5, 28(a4)      ; +0x1C = NOC_CTRL

    ; Write source address
    sw   a0, 0(a4)       ; +0x00 = NOC_TARG_ADDR_LO  (local L1 source)

    ; Write dest address
    sw   a1, 12(a4)      ; +0x0C = NOC_RET_ADDR_LO
    sw   zero, 16(a4)    ; +0x10 = NOC_RET_ADDR_MID = 0

    ; Write dest coordinate (pre-shifted)
    srli a2, a2, 4
    sw   a2, 20(a4)      ; +0x14 = NOC_RET_ADDR_COORDINATE

    ; Write length
    li   a5, 0x800       ; 2048 bytes
    sw   a5, 32(a4)      ; +0x20 = NOC_AT_LEN_BE

    ; FIRE
    li   a5, 1
    sw   a5, 64(a4)      ; +0x40 = NOC_CMD_CTRL = 1
```

And from `noc_async_read` (BRISC, using NoC1, cmd_buf 1):

```asm
; a4 = 0xFFB31000 (NoC1 base + buf1*0x800 = 0xFFB30000 + 0x800)
; Wait for CMD_CTRL ready
.L7:
    lw   a5, -1984(a4)   ; 0xFFB31000 + (-1984) = 0xFFB30840 = NOC_CMD_CTRL of buf 1
    bnez a5, .L7

    ; Write dest coordinate (local return)
    sw   a2, -2036(a4)   ; 0xFFB30814 = NOC_RET_ADDR_HI of buf 1

    ; Write source address
    sw   a0, -2048(a4)   ; 0xFFB30800 = NOC_TARG_ADDR_LO of buf 1
    sw   zero, -2044(a4) ; 0xFFB30804 = NOC_TARG_ADDR_MID of buf 1 = 0

    ; Write source coordinate
    sw   a1, -2040(a4)   ; 0xFFB30808 = NOC_TARG_ADDR_HI of buf 1

    ; Write length
    li   a2, 0x800
    sw   a2, -2016(a4)   ; 0xFFB30820 = NOC_AT_LEN_BE of buf 1

    ; FIRE
    li   a2, 1
    sw   a2, -1984(a4)   ; 0xFFB30840 = NOC_CMD_CTRL of buf 1
```

## 11. Overlay / Stream Path

The stream/overlay engine lives at a separate base:

- `NOC_OVERLAY_START_ADDR = 0xFFB40000`
- 64 streams, each with `0x1000` bytes of register space
- `STREAM_REG_ADDR(stream_id, reg_id) = 0xFFB40000 + stream_id*0x1000 + reg_id*4`

The stream engine can issue NoC transactions on behalf of firmware (used for data movement pipelines). This is a separate subsystem from the raw NIU command path. For the matmul_peak and add1 kernels, the **raw NIU path above is what's used** -- the stream/overlay path is for pipelined data movement (not needed for basic emulation of compute kernels).

## 12. CMD_BUFFER_FIFO_EN (NIU_CFG_0 bit 16)

When bit 16 of `NIU_CFG_0` is set, the 4 command buffers operate as a FIFO rather than independently addressable slots. Commands are written to buffer 0's registers and the hardware auto-advances. **Not used in add1 or matmul_peak kernels.** Can be stubbed as a no-op for initial emulation.

## 13. Atomic Operations

When `NOC_CMD_AT` (bit 0 of NOC_CTRL) is set, the transaction is an atomic. The operation type is encoded in `NOC_AT_LEN_BE` (bits [15:12]) or `NOC_L1_ACC_AT_INSTRN` (when `L1_ACC_AT_EN` is set):

| Code | Name | Description |
|------|------|-------------|
| `0x0` | `NOP` | No operation |
| `0x1` | `INCR_GET` | Increment target, return old value |
| `0x2` | `INCR_GET_PTR` | Increment-get with pointer wrap |
| `0x3` | `SWAP` | Swap target with NOC_AT_DATA |
| `0x4` | `CAS` | Compare-and-swap |
| `0x5` | `GET_TILE_MAP` | Tile map lookup |
| `0x6` | `STORE_IND` | Indirect store |
| `0x7` | `SWAP_4B` | 4-byte swap |
| `0x9` | `ACC` | Accumulate (FP32/FP16/INT32/INT8) |

The atomic instruction field in `NOC_AT_LEN_BE`:
```
[1:0]  = IND_32 (index)
[5:2]  = WRAP (wrap count)
[9:6]  = (reserved / INCR)
[11:10] = IND_32_SRC (source index)
[15:12] = INS (instruction opcode from table above)
```

For `L1_ACC_AT_INSTRN` (when `L1_ACC_AT_EN=1`):
```
[2:0]  = ACC_FORMAT (0=FP32, 1=FP16_A, 2=FP16_B, 3=INT32, 4=INT32_COMPL, 5=INT32_UNS, 6=INT8)
[3]    = ACC_SAT_DIS (disable saturation)
[15:12] = INS (must be 0x9 for ACC)
```

## 14. Multicast Delivery Model

When `NOC_CMD_BRCST_PACKET` (bit 5 of `NOC_CTRL`) is set, the transaction is delivered to a rectangle of tiles rather than a single target.

### Coordinate encoding (in `NOC_RET_ADDR_HI` for DMA writes, `NOC_TARG_ADDR_HI` for inline writes)

```
[5:0]   = EndX      (6 bits)
[11:6]  = EndY      (6 bits)
[17:12] = StartX    (6 bits)
[23:18] = StartY    (6 bits)
```

The 64-bit multicast address is constructed by the firmware API:

```c
#define NOC_MULTICAST_ADDR(x_start, y_start, x_end, y_end, addr)  \
    ((uint64_t)(x_start) << 48) | ((uint64_t)(y_start) << 54) |   \
    ((uint64_t)(x_end) << 36) | ((uint64_t)(y_end) << 42) |       \
    ((uint64_t)(addr))
```

This splits across the three address registers: bits [31:0] to `ADDR_LO`, bits [35:32] to `ADDR_MID`, and the XY fields to `ADDR_HI`.

### Delivery algorithm

The hardware delivers to all tiles whose coordinates lie within the rectangle:

```python
def multicast_targets(start_x, start_y, end_x, end_y, src_x, src_y, src_include):
    """Return set of (x, y) coordinates that receive the multicast."""
    targets = set()
    for y in range(start_y, end_y + 1):
        for x in range(start_x, end_x + 1):
            if not src_include and x == src_x and y == src_y:
                continue  # skip sender unless BRCST_SRC_INCLUDE is set
            targets.add((x, y))
    return targets
```

The rectangle is always `{(x,y) | StartX <= x <= EndX AND StartY <= y <= EndY}`. Only tiles that have been registered in the NOC routing table actually receive data (unregistered grid positions are ignored).

### `NOC_CMD_BRCST_XY` (bit 16) — routing axis, not delivery set

This bit controls which axis the multicast packet traverses first through the routers:
- `BRCST_XY=0`: X is the major axis (traverse columns first, then branch along rows)
- `BRCST_XY=1`: Y is the major axis (traverse rows first, then branch along columns)

This affects only routing topology and congestion behavior — **it does not change which tiles receive the write**. The emulator should ignore this bit entirely.

### `NOC_CMD_BRCST_SRC_INCLUDE` (bit 17) — source tile inclusion

Controls whether the sending tile receives its own multicast:
- `BRCST_SRC_INCLUDE=0` (default): if the sender's `(x, y)` falls inside the rectangle, it is excluded from receiving
- `BRCST_SRC_INCLUDE=1`: the sender also receives the write (loopback)

The firmware API exposes two variants for each multicast operation:
- `noc_async_write_multicast(...)` — excludes self (default)
- `noc_async_write_multicast_loopback_src(...)` — includes self

### `NOC_BRCST_EXCLUDE` (register offset `+0x2C`) — non-rectangular exclusion

When bit 22 is set in this register, a single row or column can be carved out of the rectangle:

```
Bits [7:0]   = start_x of excluded region
Bits [13:8]  = start_y of excluded region
Bit  [20]    = exclude direction X
Bit  [21]    = exclude direction Y
Bit  [22]    = exclude enabled
```

Used by `noc_multicast_copy_exclude()` for non-rectangular broadcast patterns. Standard firmware APIs (including `noc_semaphore_set_multicast`) always write `0x0` to this register (no exclusion). The emulator can leave this unimplemented for basic kernel emulation.

### Multicast is write-only

Multicast applies only to write and atomic transactions. Read requests must always be unicast (`BRCST_PACKET=0`).

### Counter accounting for multicast

For non-posted multicast writes (`RESP_MARKED=1`):
- `NIU_MST_NONPOSTED_WR_REQ_SENT` increments by 1 (one command issued)
- `NIU_MST_WR_ACK_RECEIVED` increments by 1 per destination tile that ACKs

The firmware pre-charges its local LDM counter: `noc_nonposted_writes_acked[noc] += num_dests`. The synchronous emulator should increment `WR_ACK_RECEIVED` by the number of actual targets delivered to when `fire_cmd()` runs, so that barrier polling resolves immediately.

### Emulator `fire_cmd()` multicast path

```python
def fire_cmd(self, buf_idx):
    regs = self.cmd_bufs[buf_idx]
    ctrl = regs[0x1C]
    is_mcast = (ctrl >> 5) & 1
    mcast_src_include = (ctrl >> 17) & 1

    if is_mcast and is_write:
        sx, sy, ex, ey = self._mcast_rect(ret_xy)
        targets_hit = 0
        for y in range(sy, ey + 1):
            for x in range(sx, ex + 1):
                if not mcast_src_include and x == self.x and y == self.y:
                    continue
                if (x, y) in self.fabric:
                    self.fabric[(x, y)].write(dst_addr, data)
                    targets_hit += 1
        if is_resp_marked:
            self.inc_counter(NIU_MST_WR_ACK_RECEIVED, targets_hit)
            self.inc_counter(NIU_MST_NONPOSTED_WR_REQ_SENT)
    # ... (existing unicast path unchanged)
```

### Firmware API summary

| Function | Src included? | Notes |
|---|---|---|
| `noc_async_write_multicast(src, dst_mcast, size, num_dests, linked, noc)` | No | Standard multicast DMA |
| `noc_async_write_multicast_loopback_src(...)` | Yes | `num_dests` includes self |
| `noc_semaphore_set_multicast(src, dst_mcast, num_dests, linked, noc)` | No | 4-byte non-posted write |
| `noc_semaphore_set_multicast_loopback_src(...)` | Yes | 4-byte with loopback |
| `noc_semaphore_inc_multicast(addr, incr, num_dests, noc)` | No | Atomic increment multicast |
| `get_noc_multicast_addr(x_start, y_start, x_end, y_end, addr, noc)` | — | Constructs the 64-bit multicast address |


## 15. Source Files Reference

| Purpose | File |
|---------|------|
| Primary BH register defines | `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/noc/noc_parameters.h` |
| NoC nonblocking API (C++) | `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/noc_nonblocking_api.h` |
| Overlay/stream params | `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/noc/noc_overlay_parameters.h` |
| Firmware C noc_transfer | `tt-metal/tt_metal/hw/firmware/src/tt-1xx/blackhole/noc.c` |
| Firmware multicast helpers | `tt-metal/tt_metal/hw/inc/api/dataflow/dataflow_api.h` |
| Multicast addr construction | `tt-metal/tt_metal/hw/inc/internal/dataflow/dataflow_api_addrgen.h` |
| NOC architecture overview | `tt-isa-documentation/BlackholeA0/NoC/README.md` |
| NOC register field spec | `tt-isa-documentation/BlackholeA0/NoC/MemoryMap.md` |
| NOC routing paths | `tt-isa-documentation/BlackholeA0/NoC/RoutingPaths.md` |
| NIU register Python map | `tt-exalens/ttexalens/hardware/blackhole/niu_registers.py` |
| ARC firmware coordinate map | `tt-zephyr-platforms/lib/tenstorrent/bh_arc/noc.c` |
| ARC NIU init/config | `tt-zephyr-platforms/lib/tenstorrent/bh_arc/noc_init.c` |
| Existing emulator NIU model | `blackhole-py/emu/noc.py` |
