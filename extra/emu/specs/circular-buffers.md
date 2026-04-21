# Circular Buffers and Tile Headers

## Overview

Circular Buffers (CBs) are the primary data-passing mechanism between RISC-V data movement cores and the Tensix compute pipeline. Each CB is a FIFO in L1 memory with hardware-tracked read/write pointers.

Blackhole supports **64 CBs** per Tensix tile (vs Wormhole's 32). Source: `circular_buffer_constants.h:33–38`.


## 1. CB Declaration (Host Side)

### API

```cpp
CBHandle CreateCircularBuffer(
    Program& program,
    const std::variant<CoreCoord, CoreRange, CoreRangeSet>& core_spec,
    const CircularBufferConfig& config);
```

Source: `tt-metalium/host_api.hpp:210`

### CircularBufferConfig

From `tt-metalium/circular_buffer_config.hpp`:

```cpp
CircularBufferConfig(
    uint32_t total_size,
    const std::map<uint8_t, tt::DataFormat>& data_format_spec);
```

The map keys are CB indices (0–63), values are `tt::DataFormat` enum values. Additional configuration:

| Method | Purpose |
|--------|---------|
| `.set_page_size(index, size)` | Set page/tile size in bytes for a CB index |
| `.set_tile_dims(index, Tile)` | Set tile geometry (face dimensions) |
| `.set_globally_allocated_address(Buffer&)` | Bind to a dynamically allocated L1 buffer |
| `.index(n)` / `.remote_index(n)` | Get a builder for CB slot n (for per-index format config) |


## 2. CB Config in L1

### Layout

The runtime CB config block written to L1 is **4 x uint32_t per CB slot** (16 bytes per slot):

| Word | Content | Description |
|------|---------|-------------|
| 0 | `cb_address` | FIFO start address in L1 (bytes) |
| 1 | `cb_size` | FIFO total size (bytes) |
| 2 | `num_pages` | Number of pages/tiles in the CB |
| 3 | `page_size` | Page/tile size (bytes) |

Source: `tt-metal/tt_metal/impl/program/dispatch.cpp:1061–1065`

**No dataformat is stored in the L1 CB config block.** The dataformat is only present in compile-time arrays baked into the kernel binary (see section 4).

Constants from `circular_buffer_constants.h`:

```
UINT32_WORDS_PER_LOCAL_CIRCULAR_BUFFER_CONFIG  = 4   (16 bytes per slot)
UINT32_WORDS_PER_REMOTE_CIRCULAR_BUFFER_CONFIG = 2
CIRCULAR_BUFFER_COMPUTE_WORD_SIZE              = 16  (16B granularity on TRISC)
CIRCULAR_BUFFER_COMPUTE_ADDR_SHIFT             = 4   (right-shift for TRISC addresses)
```

### Runtime CB Interface (firmware side)

From `circular_buffer_interface.h`:

```cpp
struct LocalCBInterface {
    uint32_t fifo_size;         // total FIFO size (in 16B units on TRISC, bytes on BRISC/NCRISC)
    uint32_t fifo_limit;        // fifo_addr + fifo_size
    uint32_t fifo_page_size;    // page size (same unit convention)
    uint32_t fifo_num_pages;    // number of pages
    uint32_t fifo_rd_ptr;       // read pointer
    uint32_t fifo_wr_ptr;       // write pointer
    union {
        uint32_t tiles_acked_received_init;
        struct {
            uint16_t tiles_acked;
            uint16_t tiles_received;
        };
    };
    uint32_t fifo_wr_tile_ptr;  // tile write pointer (packer in-order tracking)
};
```

Accessed via `get_local_cb_interface(cb_id)`. On TRISC cores, all addresses and sizes are in **16-byte units** (right-shifted by `cb_addr_shift = 4`).

The 64 CB indices are split into two halves for the `local_cb_mask` bitfield: indices 0–31 in the lower 32 bits, indices 32–63 in the upper 32 bits (Blackhole-only path in `trisc.cc:166–169`).


## 3. Tile Header

### Structure

From `tensix_types.h:110–143`:

```cpp
struct TileHeader {                       // exactly 16 bytes
    uint16_t tile_size_16B;               // tile size in units of 16 bytes
    uint16_t reserved_0_mbz : 1;
    uint16_t tile_id        : 15;         // tile sequence ID

    uint8_t  metadata_size_16B;           // exponent/metadata section size in 16B units
    uint8_t  reserved_1;
    uint16_t format;                      // [3:0] = DataFormat, bit[4] = uncompressed flag

    uint32_t zero_mask;                   // zero-compression mask
    uint32_t reserved_3;
};
static_assert(sizeof(TileHeader) == 16);
```

### Format field encoding

Bits `[3:0]` carry the same 4-bit DataFormat enum as the hardware config registers. Bit `[4]` is the uncompressed flag (0 = compressed, 1 = uncompressed). `IsCompressed()` returns `(format & 0x10) == 0`.

### Position relative to tile data

The tile header is a **16-byte prefix** at the start of each tile in L1. The union `TileHeader_u` provides `uint32_t val[4]` access.

In the packer, the header is held in GPRs `p_gpr_pack::TILE_HEADER` (GPR index 16–19, 4 consecutive registers). When `add_tile_header_size` is set in the pack config, the packer MOP writes these 4 words to L1 before the tile data.

### tt-metal does NOT use tile headers

In practice, tt-metal writes **headerless tiles**. From `cpack_common.h:540–541`:

> "Since we do not write tile headers in tt-metal, we do not need to wait for packer to finish"

The tile header fields are initialized to zero (except `tile_size`), and the `add_tile_header_size` bit is not set. Page sizes in the CB config account for data only, not headers.


## 4. How the Unpacker Knows the Datatype

The unpacker does **not** read data format from tile headers or from the L1 CB config block. The format flows through a fully compile-time path:

### Step 1: Host -> JIT build

`CircularBufferConfig(DataFormat)` feeds into `tt_hlk_desc::buf_dataformat_arr[]` via `JitBuildOptions::set_cb_dataformat_all_cores()`.

Source: `jit_build/jit_build_options.cpp:30–55`

### Step 2: JIT generates compile-time arrays

`jit_build_genfiles_descriptors()` emits `chlkc_descriptors.h` containing per-CB format and dimension constants:

```cpp
constexpr int32_t  unpack_src_format[64]     = { /* DataFormat per CB */ };
constexpr int32_t  unpack_dst_format[64]     = { /* dest register format per CB */ };
constexpr uint8_t  unpack_tile_num_faces[64]  = { /* face count per CB */ };
constexpr uint8_t  unpack_tile_face_r_dim[64] = { /* face row dim per CB */ };
// plus pack_src_format, pack_dst_format, tile dims...
```

Source: `jit_build/genfiles.cpp:161–378`

These are **compile-time constants** baked into the kernel binary.

### Step 3: Kernel init programs hardware registers

`configure_unpack_AB()` reads `unpack_src_format[operand_id]` / `unpack_dst_format[operand_id]` and writes the THCON hardware registers:

- `THCON_SEC0_REG0.in_data_format` — 4-bit input tile format
- `THCON_SEC0_REG2.out_data_format` — 4-bit output (register file) format
- `ALU_FORMAT_SPEC` fields — format for math engine

Source: `cunpack_common.h:206–385`

### Step 4: Per-tile address from CB interface

Each unpack call writes the tile's L1 address to `THCON_SEC0_REG3_Base_address` before issuing the UNPACR instruction. The tile size comes from `fifo_page_size` in the CB interface, stored in GPR `p_gpr_unpack::TILE_SIZE_A` (GPR 36) / `TILE_SIZE_B` (GPR 37):

```cpp
const uint32_t unpA_tile_size = get_local_cb_interface(unpA_operand_id).fifo_page_size;
TT_SETDMAREG(0, LOWER_HALFWORD(unpA_tile_size), 0, LO_16(p_gpr_unpack::TILE_SIZE_A));
```

Source: `llk_unpack_common_api.h:56`

### Summary: where format lives at each layer

| Layer | Format present? |
|-------|-----------------|
| L1 CB config (4 words: addr, size, num_pages, page_size) | **No** |
| `TileHeader.format[3:0]` in L1 tile data | Defined in struct, **not written** by tt-metal |
| Compile-time `unpack_src_format[cb_id]` | **Yes** — JIT-emitted from `CircularBufferConfig` |
| THCON hardware registers (tile descriptor / unpack config) | **Yes** — programmed from compile-time arrays at kernel init |
| GPR `p_gpr_unpack::TILE_SIZE_A/B` | Tile size only (from CB `fifo_page_size`), no format |


## Key Source Files

| File | Content |
|------|---------|
| `tt-metalium/circular_buffer_config.hpp` | `CircularBufferConfig` class |
| `tt-metalium/circular_buffer_constants.h` | CB count (64), word sizes, shift constants |
| `tt_metal/hw/inc/internal/circular_buffer_interface.h` | `LocalCBInterface` struct |
| `tt_metal/hw/inc/internal/circular_buffer_init.h` | CB interface init (RISC-V asm loop) |
| `tt_metal/impl/program/dispatch.cpp` | CB L1 config layout (4 words) |
| `tt_metal/hw/inc/internal/tt-1xx/blackhole/tensix_types.h` | `TileHeader` struct, `DataFormat` enum |
| `tt_metal/jit_build/genfiles.cpp` | JIT descriptor generation (`unpack_src_format[]` arrays) |
| `tt_metal/jit_build/hlk_desc.hpp` | `tt_hlk_desc` — per-CB format/dimension arrays |
| `tt_metal/hw/ckernels/blackhole/metal/llk_api/llk_unpack_common_api.h` | `llk_unpack_hw_configure` (top-level API) |
| `tt_metal/hw/inc/api/compute/cb_api.h` | CB kernel API (`cb_wait_front`, `cb_pop_front`, etc.) |
| `tt_llk_blackhole/common/inc/cunpack_common.h` | `configure_unpack_AB()`, tile descriptor/config structs |
| `tt_llk_blackhole/common/inc/cpack_common.h` | Pack config, tile header GPR init, header comment |
| `tt_llk_blackhole/common/inc/ckernel_gpr_map.h` | GPR assignments (TILE_HEADER=16, TILE_SIZE_A=36) |
