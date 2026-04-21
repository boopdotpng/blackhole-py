# XMOV Instruction and TDMA Mover

The Mover is a hardware DMA block inside every Tensix tile that performs bulk data transfers between L1, the Tensix Backend Configuration register space, and NCRISC Instruction RAM. All transfers are in aligned 16-byte units.

Two interfaces access the same Mover hardware:
- **XMOV** — a Tensix coprocessor instruction issued through the thread pipeline
- **TDMA-RISC** — memory-mapped registers at `0xFFB11000`, used by RISC-V cores directly


## 1. XMOV Instruction (opcode 0x40)

Executes on the **Mover** backend unit. The thread issuing XMOV is automatically stalled until the Mover can start, then the instruction completes in one cycle and the transfer proceeds in the background.

### Encoding

```
[31:24] = 0x40  (opcode)
[23]    = Mov_block_selection  (1 bit — selects between two move blocks)
[22:1]  = (reserved)
[0]     = Last                 (1 bit — flush accumulation buffers on completion)
```

```c
#define TT_OP_XMOV(Mov_block_selection, Last) \
    TT_OP(0x40, (((Mov_block_selection) << 23) + ((Last) << 0)))
```

### Transfer parameters

XMOV reads its parameters from the Tensix Backend Configuration space, not from the instruction encoding:

```c
uint1_t StateID = ThreadConfig[CurrentThread].CFG_STATE_ID_StateID;

uint32_t src  = Config[StateID][THCON_SEC0_REG6_Source_address_ADDR32] << 4;       // byte addr
uint32_t dst  = Config[StateID][THCON_SEC0_REG6_Destination_address_ADDR32] << 4;  // byte addr
uint32_t size = (Config[StateID][THCON_SEC0_REG6_Buffer_size_ADDR32] & 0xFFFF) << 4;  // bytes
uint32_t dir  = Config[StateID][THCON_SEC0_REG6_Transfer_direction_ADDR32];
```

All address and size fields are stored in 16-byte units in config; multiply by 16 for byte addresses.

### STALLWAIT integration

| Block mask | Bits | Effect |
|---|---|---|
| `STALL_TDMA` (B0) | `0x01` | Blocks XMOV (and ThCon, Packer, etc.) |
| `STALL_XMOV` (B4) | `0x10` | Blocks XMOV specifically |

| Wait condition | Bit | Meaning |
|---|---|---|
| C9 (`XMOV`) | `0x200` | Keep waiting while the Mover has any outstanding memory requests |


## 2. Functional Model

```c
enum xmov_direction_t {
    XMOV_L0_TO_L1 = 0,   // memset(0) → L1
    XMOV_L1_TO_L0 = 1,   // memcpy L1 → CFG space or NCRISC IRAM
    XMOV_L0_TO_L0 = 2,   // memset(0) → CFG space or NCRISC IRAM
    XMOV_L1_TO_L1 = 3,   // memcpy L1 → L1
};

void Mover(uint32_t dst, uint32_t src, uint32_t count, xmov_direction_t mode) {
    // Resolve destination address for non-L1 modes
    if (mode == XMOV_L1_TO_L0 || mode == XMOV_L0_TO_L0) {
        if (dst <= 0xFFFF)
            dst += 0xFFEF0000;            // TENSIX_CFG_BASE
        else if (0x40000 <= dst && dst <= 0x4ffff) {
            if ((dst & 0xffff) + count > 0x10000) UndefinedBehaviour();
            dst = (dst - 0x40000) + MEM_NCRISC_IRAM_BASE;
        }
        else
            return;  // writes discarded (unmapped)
    }

    // Execute transfer
    if (mode == XMOV_L1_TO_L1 || mode == XMOV_L1_TO_L0) {
        memcpy(dst, src, count);   // copy from L1
    } else {
        memset(dst, 0, count);     // zero-fill ("L0" = zero source)
    }
}
```

The "L0" label is a hardware misnomer — it does not refer to a cache level. Modes with "L0" as source produce zero-fills; modes with "L0" as destination target the configuration register space or NCRISC IRAM.

| Direction | Operation | Source | Destination |
|---|---|---|---|
| `XMOV_L0_TO_L1` (0) | `memset(0)` | (zeros) | L1 |
| `XMOV_L1_TO_L0` (1) | `memcpy` | L1 | CFG space or NCRISC IRAM |
| `XMOV_L0_TO_L0` (2) | `memset(0)` | (zeros) | CFG space or NCRISC IRAM |
| `XMOV_L1_TO_L1` (3) | `memcpy` | L1 | L1 |


## 3. TDMA-RISC Register Map (`0xFFB11000`)

### Mover command registers

| Address | Name | On Write | On Read |
|---|---|---|---|
| `0xFFB11000` | `XMOV_SRC_ADDR` | Set `CmdParams[0]` (source addr, 16B units) | 0 |
| `0xFFB11004` | `XMOV_DST_ADDR` | Set `CmdParams[1]` (dest addr, 16B units) | 0 |
| `0xFFB11008` | `XMOV_SIZE` | Set `CmdParams[2]` (transfer size, 16B units) | 0 |
| `0xFFB1100C` | `XMOV_DIRECTION` | Set `CmdParams[3]` (`xmov_direction_t`) | 0 |
| `0xFFB11010` | `COMMAND_ADDR` | Enqueue command (see below) | 0 |
| `0xFFB11014` | `STATUS` | No effect | Status bits (see below) |
| `0xFFB1102C` | `XMOV_L1_BASE_ADDR` | Set `MovCmdBase[CurrentThread]` (16B units) | Current thread's base |

### STATUS register bits (`0xFFB11014`)

```
Bit  0: mover_busy           (0x01 — Mover 0 is executing)
Bit  1: reserved
Bit  2: command_queue_full   (0x04 — FIFO has no free slots)
Bit  3: command_queue_empty  (0x08 — FIFO is drained)
Bit  4: parameter_queue_full (0x10 — ParameterCredits == 0)
[15:8]: remaining_capacity   (command queue slots free; max = 4)
Bit 16: packer_reg_write_fifo_full
Bit 17: unpacker_reg_write_fifo_full
```

### Command processor

The TDMA-RISC has a 4-entry command queue. Write to `COMMAND_ADDR` (`0xFFB11010`) to enqueue a command.

**Non-compact command** (bit 31 = 0): Uses the four `CmdParams[]` registers written before the command.

```c
// Write parameters first
*(volatile uint32_t*)0xFFB11000 = src_addr_16B;
*(volatile uint32_t*)0xFFB11004 = dst_addr_16B;
*(volatile uint32_t*)0xFFB11008 = size_16B;
*(volatile uint32_t*)0xFFB1100C = direction;
// Then enqueue
*(volatile uint32_t*)0xFFB11010 = 0x40 | (mover_number << 8);  // CMD_TDMA_XMOV
```

**Compact command** (bit 31 = 1): All parameters encoded in the 32-bit write:

```
Bits [7:0]   = 0x40  (mover opcode)
Bits [15:8]  = src_offset  (added to MovCmdBase[CurrentThread])
Bits [23:16] = dst_addr    (16B-aligned destination)
Bits [29:24] = xfer_size   (in 16B units, max 63)
Bit  [30]    = xfer_dir    (0 = L1→CFG, 1 = L1→L1)
Bit  [31]    = 1           (compact flag)
```

**Known hardware bug:** When ParameterCredits == 0, `COMMAND_ADDR` write should stall but does not. Software inserts a NOP command (`0x80000089`) after parameterized commands to avoid this.

| Command opcode | Name | Function |
|---|---|---|
| `0x40` | Mover | Start mover transfer |
| `0x46` | Mover wait/flush | Wait for mover idle |
| `0x66` | L1 write | Direct 32/64-bit write to L1 |
| `0x89` | NOP | Pipeline bubble (for ParameterCredits bug) |


## 4. Firmware API

### Non-compact path (full parameterized transfer)

```c
void tdma_xmov(uint mover_number, uint src_addr, uint dst_addr,
               uint size, xmov_direction_t direction) {
    memory_write(RISCV_TDMA_REG_XMOV_SRC_ADDR, src_addr);     // 16B units
    memory_write(RISCV_TDMA_REG_XMOV_DST_ADDR, dst_addr);     // 16B units
    memory_write(RISCV_TDMA_REG_XMOV_SIZE, size);              // 16B units
    memory_write(RISCV_TDMA_REG_XMOV_DIRECTION, (uint)direction);
    memory_write(RISCV_TDMA_REG_COMMAND_ADDR, CMD_TDMA_XMOV | (mover_number << 8));
}

void wait_tdma_movers_done(uint mover_busy_mask) {
    volatile uint s;
    s = memory_read(RISCV_TDMA_REG_STATUS);  // dummy read to flush pipe
    do {
        s = memory_read(RISCV_TDMA_REG_STATUS);
    } while ((s & (mover_busy_mask | 0x08)) != 0x08);  // wait until idle + queue empty
}
```

### Compact path (fast tile descriptor programming)

```c
// Set L1 base once per kernel
xmov_set_base(l1_base_addr_16B);  // writes to XMOV_L1_BASE_ADDR

// Issue compact L1→CFG move (single MMIO write)
xmov_cfg_program(l1_offset_16B, cfg_reg_addr32, xfer_size_16B);

// Issue non-compact L1→L1 move
xmov_l1_to_l1_non_compact(src_16B, dst_16B, size_16B);

// Poll for idle
xmov_wait_till_idle();  // polls STATUS & 0x01
```


## 5. Packer Metadata Registers

The TDMA register block also hosts packer/unpacker metadata sideband registers. These are unrelated to XMOV transfers but share the `0xFFB11xxx` address space:

| Address | Name | Read | Write |
|---|---|---|---|
| `0xFFB11018` | `PACKED_SIZE` | Last packer 0 tile size | No effect |
| `0xFFB1101C` | `ACC_PACKED_SIZE` / `INITIAL_PACK_ACC` | Accumulated size | Reset accumulator |
| `0xFFB11030` | `FIFO_PACKED_TILE_SIZE(0)` | Peek packer 0 FIFO tile size | No effect |
| `0xFFB11034` | `FIFO_PACKED_TILE_ZEROMASK(0)` | Pop + return zero mask | Pop FIFO |
| `0xFFB11038` | `FIFO_PACKED_TILE_STATUS` | FIFO empty/full flags | SetPackRegAddr |

Packers 0–3 have registers at stride `0x100` (packer N at `0xFFB11000 + N*0x100 + offset`). These report how many bytes the packer wrote per tile and the zero-mask for compression. Firmware reads them after packing to update output buffer pointers.


## 6. Performance

| Mode | Ideal throughput | With L1 port contention |
|---|---|---|
| `XMOV_L1_TO_L1` / `XMOV_L1_TO_L0` (memcpy) | 93.1 bits/cycle (8 reads + 8 writes per 11 cycles) | ~32 bits/cycle |
| `XMOV_L0_TO_L1` (L1 zero-fill) | 128 bits/cycle (1 write/cycle) | ~42.7 bits/cycle |
| `XMOV_L0_TO_L0` (CFG/IRAM zero-fill) | 128 bits/cycle | 128 bits/cycle (no L1 contention) |

The Mover shares L1 access ports with unpackers, packers, ThCon, and the NoC, so contention is the common case during compute kernels.


## 7. Emulator Implementation Notes

1. **XMOV instruction**: When the emulator encounters opcode `0x40`, read the transfer parameters from `Config[StateID][THCON_SEC0_REG6_*]`, execute the `Mover()` function model synchronously, and mark the Mover as busy for pipeline tracking.

2. **TDMA-RISC registers**: Implement the `CmdParams[]` staging registers and `COMMAND_ADDR` trigger. On `COMMAND_ADDR` write with opcode `0x40`, execute the transfer synchronously. Return `0x08` (FIFO_EMPTY) from `STATUS` reads to unblock any `wait_tdma_movers_done()` polling.

3. **Compact commands**: Decode the packed fields from the 32-bit `COMMAND_ADDR` write and resolve the source address as `MovCmdBase[CurrentThread] + src_offset`.

4. **STALLWAIT C9**: After any Mover transfer, the C9 condition should report clear (Mover not busy) since transfers complete synchronously.

5. **Packer metadata registers**: Implement `FIFO_PACKED_TILE_SIZE` and `FIFO_PACKED_TILE_ZEROMASK` for pack kernels. The packer functional model populates these as tiles are packed; firmware reads them to learn the compressed tile size.

6. **Firmware init**: BRISC writes `0x3F` to `RISCV_TDMA_REG_CLK_GATE_EN` (`0xFFB11024`) during `device_setup()`. The emulator can treat this as a no-op.


## 8. Source References

| File | Content |
|---|---|
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/XMOV.md` | XMOV instruction spec (applies to Blackhole) |
| `tt-isa-documentation/WormholeB0/TensixTile/Mover.md` | Mover functional model, performance, direction enum |
| `tt-isa-documentation/WormholeB0/TensixTile/TDMA-RISC.md` | Full register map, command processor, compact encoding |
| `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/tensix.h` | `RISCV_TDMA_REG_*` defines, STATUS flag masks |
| `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/tensix_types.h` | `xmov_direction_t` enum, `tdma_mover_id_t` |
| `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/cfg_defines.h` | `THCON_SEC0_REG6_*` config register addresses |
| `tt-metal/tt_metal/hw/firmware/src/tt-1xx/tdma_xmov.c` | `tdma_xmov()`, `wait_tdma_movers_done()` |
| `tt-llk/tt_llk_blackhole/common/inc/ckernel_xmov.h` | Compact/non-compact XMOV helpers |
| `tt-llk/tt_llk_blackhole/common/inc/ckernel_ops.h` | `TT_OP_XMOV` / `TTI_XMOV` macros |
| `tt-llk/tt_llk_blackhole/instructions/assembly.yaml` | XMOV opcode 0x40 field layout |
