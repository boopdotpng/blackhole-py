# circular-buffers

**Source:** [`circular-buffers.md`](../specs/circular-buffers.md) · **Emulator:** `blackhole-py/emu/device.py`

## CB count

### `CB.COUNT.64`
§Overview / Blackhole 64 CBs

> Blackhole supports 64 CBs per Tensix tile.

### `CB.CONFIG.WORDS_PER_SLOT`
§2 CB Config in L1 / Layout

> CB L1 config block is 4 uint32 per slot (16 bytes): addr, size, num_pages, page_size.

### `CB.CONFIG.BASE_ADDR`
§2 CB Config in L1 / Layout

> CB config block starts at KERNEL_CONFIG_BASE in L1.

### `CB.CONFIG.WORD0_ADDR`
§2 CB Config in L1 / word 0

> Word 0 of each 16-byte CB slot is cb_address (FIFO start address in L1).

### `CB.CONFIG.WORD1_SIZE`
§2 CB Config in L1 / word 1

> Word 1 is cb_size = num_pages * page_size (total FIFO size in bytes).

### `CB.CONFIG.WORD2_NUM_PAGES`
§2 CB Config in L1 / word 2

> Word 2 is num_pages.

### `CB.CONFIG.WORD3_PAGE_SIZE`
§2 CB Config in L1 / word 3

> Word 3 is page_size (tile size in bytes).

### `CB.CONFIG.NO_DATAFORMAT`
§2 CB Config in L1 / No dataformat

> No dataformat is stored in the L1 CB config block.

### `CB.ALLOC.SEQUENTIAL`
§2 CB Config in L1 / Allocation

> CB data buffers are allocated sequentially from DATA_BUFFER_SPACE_BASE.

### `CB.ALLOC.OVERFLOW_RAISES`
§2 CB Config in L1 / Overflow

> Configuring a CB that would overflow L1 raises ValueError.

### `CB.ALLOC.INDEX_RANGE`
§Overview / CB indices

> CB index must be in range 0..63; out-of-range raises ValueError.

### `CB.ALLOC.ALL_TILES`
§2 CB Config in L1 / all tiles

> configure_cbs writes identical config to every tile's L1.

### `CB.STREAM.CB_N_IS_STREAM_N`
_§stream-registers.md §2 / OPERAND_START_STREAM=0_

> On Blackhole, CB N maps directly to stream N (OPERAND_START_STREAM=0).

### `CB.STREAM.TILES_RECEIVED_ADDR`
§stream-registers.md §3 / reg 10

> tiles_received for CB n is at STREAM_BASE + n*STREAM_STRIDE + STREAM_TILES_RECEIVED (reg 10, +0x028).

### `CB.STREAM.TILES_ACKED_ADDR`
§stream-registers.md §3 / reg 8

> tiles_acked for CB n is at STREAM_BASE + n*STREAM_STRIDE + STREAM_TILES_ACKED (reg 8, +0x020).

### `CB.TILE_HDR.NOT_USED`
§3 Tile Header / tt-metal does NOT use tile headers

> tt-metal writes headerless tiles; add_tile_header_size is not set.
