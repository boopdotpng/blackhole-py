# xmov-and-tdma-mover

**Source:** [`xmov-and-tdma-mover.md`](../specs/xmov-and-tdma-mover.md) · **Emulator:** `blackhole-py/extra/emu/tensix/__init__.py`

## XMOV encoding

### `XMOV.ENCODING.OPCODE`
§1 XMOV Instruction (opcode 0x40) / Encoding

> XMOV opcode is 0x40.

### `XMOV.ENCODING.MOV_BLOCK_SELECTION`
_§1 XMOV Instruction / Encoding / Mov_block_selection_

> Mov_block_selection [23]: selects between two move blocks.

### `XMOV.ENCODING.LAST`
§1 XMOV Instruction / Encoding / Last

> Last [0]: flush accumulation buffers on transfer completion.

## XMOV parameter source

### `XMOV.PARAMS.FROM_CFG_SPACE`
§1 XMOV Instruction / Transfer parameters

> XMOV reads transfer parameters from Tensix Backend Config space, not from the instruction encoding:
>   src  = Config[StateID][THCON_SEC0_REG6_Source_address] << 4
>   dst  = Config[StateID][THCON_SEC0_REG6_Destination_address] << 4
>   size = (Config[StateID][THCON_SEC0_REG6_Buffer_size] & 0xFFFF) << 4
>   dir  = Config[StateID][THCON_SEC0_REG6_Transfer_direction]

## XMOV functional model (directions)

### `XMOV.FUNC.L0_TO_L1_ZERO_FILL`
_§2 Functional Model / XMOV_L0_TO_L1 (0)_

> Direction 0 (XMOV_L0_TO_L1): memset(dst, 0, count) into L1.

### `XMOV.FUNC.L1_TO_L0_MEMCPY`
_§2 Functional Model / XMOV_L1_TO_L0 (1)_

> Direction 1 (XMOV_L1_TO_L0): memcpy from L1 to CFG space or NCRISC IRAM. If dst <= 0xFFFF: dst += 0xFFEF0000 (TENSIX_CFG_BASE). If 0x40000 <= dst <= 0x4ffff: dst maps to MEM_NCRISC_IRAM_BASE + (dst-0x40000). Otherwise: writes discarded.

### `XMOV.FUNC.L0_TO_L0_ZERO_FILL_CFG`
_§2 Functional Model / XMOV_L0_TO_L0 (2)_

> Direction 2 (XMOV_L0_TO_L0): memset(dst, 0, count) into CFG space or NCRISC IRAM.

### `XMOV.FUNC.L1_TO_L1_MEMCPY`
_§2 Functional Model / XMOV_L1_TO_L1 (3)_

> Direction 3 (XMOV_L1_TO_L1): memcpy(dst, src, count) within L1.

### `XMOV.FUNC.L0_LABEL_MISNOMER`
§2 Functional Model / L0 label is a misnomer

> 'L0' in direction names does not refer to a cache level. L0-as-source = zero fill; L0-as-destination = CFG space or NCRISC IRAM.

### `XMOV.FUNC.ALIGNMENT`
§1 XMOV Instruction intro / 16-byte units

> All XMOV transfers are in aligned 16-byte units.

## STALLWAIT integration

### `XMOV.STALLWAIT.C9_CONDITION`
§1 STALLWAIT integration / C9

> STALLWAIT C9 condition (bit 0x200): keep stalling while the Mover has outstanding memory requests. After any XMOV transfer, C9 should report clear.

## TDMA-RISC register interface

### `TDMA.REG.XMOV_SRC_ADDR`
_§3 TDMA-RISC Register Map / XMOV_SRC_ADDR (0xFFB11000)_

> Write to 0xFFB11000 sets CmdParams[0] (source addr, 16B units).

### `TDMA.REG.XMOV_DST_ADDR`
_§3 TDMA-RISC Register Map / XMOV_DST_ADDR (0xFFB11004)_

> Write to 0xFFB11004 sets CmdParams[1] (dest addr, 16B units).

### `TDMA.REG.XMOV_SIZE`
_§3 TDMA-RISC Register Map / XMOV_SIZE (0xFFB11008)_

> Write to 0xFFB11008 sets CmdParams[2] (transfer size, 16B units).

### `TDMA.REG.XMOV_DIRECTION`
_§3 TDMA-RISC Register Map / XMOV_DIRECTION (0xFFB1100C)_

> Write to 0xFFB1100C sets CmdParams[3] (xmov_direction_t).

### `TDMA.REG.COMMAND_ADDR_TRIGGER`
_§3 TDMA-RISC Register Map / COMMAND_ADDR (0xFFB11010)_

> Write to 0xFFB11010 enqueues a command. Opcode 0x40 with mover_number encoded in bits [15:8] triggers the Mover transfer using the staged CmdParams[].

### `TDMA.REG.STATUS_IDLE`
§3 TDMA-RISC Register Map / STATUS (0xFFB11014)

> STATUS register at 0xFFB11014. Bit 3 (0x08) = FIFO_EMPTY (queue drained). Emulator implementation note: always return 0x08 to unblock polling firmware.

### `TDMA.REG.L1_BASE_ADDR`
_§3 TDMA-RISC Register Map / XMOV_L1_BASE_ADDR (0xFFB1102C)_

> Write to 0xFFB1102C sets MovCmdBase[CurrentThread] (16B units). Used as base address for compact commands.

## Compact command encoding

### `TDMA.COMPACT.ENCODING`
§3 Command processor / Compact command (bit 31 = 1)

> Compact command (bit [31]=1): bits [7:0]=0x40, [15:8]=src_offset, [23:16]=dst_addr, [29:24]=xfer_size (16B units, max 63), [30]=xfer_dir (0=L1→CFG, 1=L1→L1). Source address = MovCmdBase[CurrentThread] + src_offset.

### `TDMA.COMPACT.SRC_OFFSET_RESOLUTION`
_§3 Command processor / Compact command / src_offset_

> Compact command source address = MovCmdBase[CurrentThread] + src_offset (both in 16B units).

## Hardware bug

### `TDMA.BUG.PARAMETER_CREDITS`
§3 Command processor / Known hardware bug

> When ParameterCredits==0, COMMAND_ADDR write should stall but does not. Software inserts NOP command 0x80000089 after parameterized commands to avoid data corruption.

### `TDMA.API.NON_COMPACT_SEQUENCE`
§4 Firmware API / Non-compact path

> Non-compact sequence: write SRC_ADDR, DST_ADDR, SIZE, DIRECTION, then write CMD_TDMA_XMOV | (mover_number << 8) to COMMAND_ADDR.

### `TDMA.API.WAIT_DONE_POLLING`
_§4 Firmware API / wait_tdma_movers_done_

> wait_tdma_movers_done(mask): poll STATUS until (status & (mask | 0x08)) == 0x08 (Mover idle and FIFO empty).

## Packer metadata sideband

### `TDMA.PACKED_SIZE.FIFO_TILE_SIZE`
_§5 Packer Metadata Registers / FIFO_PACKED_TILE_SIZE_

> 0xFFB11030 (FIFO_PACKED_TILE_SIZE for packer 0): read returns the byte size of the most recently packed tile sitting at the head of the FIFO.

### `TDMA.PACKED_SIZE.FIFO_ZERO_MASK`
_§5 Packer Metadata Registers / FIFO_PACKED_TILE_ZEROMASK_

> 0xFFB11034 (FIFO_PACKED_TILE_ZEROMASK for packer 0): read pops the FIFO and returns the zero-compression mask for the popped tile.

### `TDMA.PACKED_SIZE.PACKER_STRIDE`
§5 Packer Metadata Registers / packer N stride

> Packers 0-3 have metadata registers at stride 0x100 from the TDMA base: packer N at 0xFFB11000 + N*0x100 + offset.
