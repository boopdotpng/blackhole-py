# DRAM and PCIe Endpoint Emulator Specification (Blackhole)

DRAM and PCIe are **not separate buses**. Both are NoC endpoints — nodes on the existing NoC grid with fixed XY coordinates. The emulator accesses them via the same NIU command buffer mechanism documented in `niu.md`. This spec covers:

1. Tile data format and tilization (what gets stored)
2. DRAM bank geometry, interleaving, and address generation (how it's addressed)
3. PCIe endpoint (host memory access)

---

## 1. Tile Format and Tilization

All data flowing through DRAM is **tiled**. Understanding the tile layout is necessary to interpret DRAM contents during debugging, even though the emulator itself treats tiles as opaque byte blobs.

### 1.1 Tile Geometry

A 32×32 tile = 1024 elements, stored as 4 contiguous 16×16 **faces** in Z-order:

```
Face 0  [rows 0-15,  cols 0-15]   element offsets 0–255
Face 1  [rows 0-15,  cols 16-31]  element offsets 256–511
Face 2  [rows 16-31, cols 0-15]   element offsets 512–767
Face 3  [rows 16-31, cols 16-31]  element offsets 768–1023
```

Within each face: row-major (16 elements × 16 rows). Element index = `face_offset + (r % 16) * 16 + (c % 16)`.

The face split exists because the Tensix FPU natively computes 16×16 matrix multiplications. A 32×32 matmul decomposes into four 16×16 face operations. The unpacker reads faces into SrcA/SrcB; the packer writes faces from DEST.

Other hardware-supported tile shapes: 16×32, 32×16, 16×16 — all use 16×16 faces.

### 1.2 Data Formats and Tile Sizes

```c
enum DataFormat : uint8_t {
    Float32   = 0,   Float16   = 1,   Bfp8   = 2,   Bfp4   = 3,
    Tf32      = 4,   Float16_b = 5,   Bfp8_b = 6,   Bfp4_b = 7,
    Int32     = 8,   UInt16    = 9,   Lf8     = 10,  Bfp2   = 11,
    Int8      = 14,  Bfp2_b    = 15,  Fp8_e4m3 = 0x1A,
    UInt32    = 24,  UInt8     = 30,
    RawUInt8  = 0xF0, RawUInt16 = 0xF1, RawUInt32 = 0xF2,
};
```

`_b` suffix = "bfloat" variant (shared exponent per row). Non-`_b` = "a" format (shared exponent per face).

Tile byte sizes for the standard 32×32 (1024 elements):

| Format | Tile size (bytes) | Breakdown |
|--------|-------------------|-----------|
| Float32 / Int32 / UInt32 / RawUInt32 | 4096 | 1024 × 4 |
| Float16 / Float16_b / UInt16 / RawUInt16 | 2048 | 1024 × 2 |
| Bfp8 / Bfp8_b | 1088 | 1024 × 1 (data) + 64 (exponents) |
| Bfp4 / Bfp4_b | 576 | 512 × 1 (data) + 64 (exponents) |
| Bfp2 / Bfp2_b | 320 | 256 × 1 (data) + 64 (exponents) |
| UInt8 / Int8 / Lf8 / Fp8_e4m3 / RawUInt8 | 1024 | 1024 × 1 |

Bfp formats have a separate **exponent section** appended after the data section: 4 faces × 16 shared exponents per face = 64 bytes.

### 1.3 Tilization and Untilization

Tilization converts row-major tensor data into the face-based tile layout. Two paths exist:

**Host CPU path:** `convert_layout_row_major_to_tile()` in `tilize_utils.cpp` — pure C++ memcpy loops. Used for small tensors or when device compute is not available. Produces tiles in the face layout above and writes them to DRAM via NoC.

**Device compute path (preferred for large tensors):** A 3-kernel Tensix program (reader + compute + writer). The compute kernel calls `tilize_init()` / `tilize_block()` from `compute_kernel_api/tilize.h`. Internally, the **unpacker hardware** has a `tileize_mode` that reads row-major data from L1 and reorders it into face-based layout directly into the SrcA register file. MATH does A-to-DEST datacopy; PACK writes the tiled output to a CB. All reordering is done by the unpacker unit, not software loops.

**Untilization** is the reverse — two strategies:
- Unpacker-based: unpacker reads tiles face-by-face, outputs contiguous rows (two-pass: top faces then bottom faces)
- Pack-based (preferred): unpacker reads tiles normally; packer is configured to scatter-write DEST in row-major order

**For the emulator:** Tilization/untilization is irrelevant to the DRAM model. DRAM stores bytes. The emulator does not need to understand tile internals — it just reads and writes byte ranges. The tile format matters only for debugging (interpreting what's in DRAM) and for understanding why `MUL_WITH_TILE_SIZE` computes the addresses it does.

### 1.4 Tile Headers

The packer hardware can optionally prepend a 16-byte header (4 × uint32: tile size + 3 words of zeros) before each tile. **tt-metal disables this feature** — tiles in L1/DRAM have no prepended header in the standard flow. The emulator does not need to account for tile headers.

### 1.5 MUL_WITH_TILE_SIZE

The `InterleavedAddrGenFast` address generator uses `MUL_WITH_TILE_SIZE<tile_hw>(data_format, index)` to compute the byte offset for the `index`-th tile. This avoids a general multiply by encoding tile sizes as shift-and-add combinations:

```
Float16:  index << 11                       = index * 2048
Float32:  index << 12                       = index * 4096
Bfp8:     (index << 10) + (index << 6)      = index * 1088
Bfp4:     (index << 9) + (index << 6)       = index * 576
Bfp2:     (index << 8) + (index << 6)       = index * 320
UInt8:    index << 10                       = index * 1024
```

This is a compile-time dispatch on `data_format`. The emulator must replicate this if it interprets `InterleavedAddrGenFast` fields, or it can just store `tile_bytes` directly and multiply.

---

## 2. DRAM Banks

### 2.1 Physical Geometry (P100A — 7 Banks)

Blackhole P100A has **7 active DRAM banks** (1 of 8 physical banks harvested). Each bank is fronted by **3 DRAM tiles** — three independent NoC ingress points (ports) that all map to the same DDR controller. There is no data striping between the 3 ports; they expose identical address spaces.

`build_bank_noc_table()` in `hw.py` assigns **translated** NoC coordinates to the 7 active banks. The layout is always 4 banks on the west column (`x=17`) and 3 on the east (`x=18`), with each bank occupying a group of 3 consecutive Y coordinates (the 3 ports):

```
  West column (x=17)              East column (x=18)

  Bank 0: y = 12, 13, 14         Bank 4: y = 12, 13, 14
  Bank 1: y = 15, 16, 17         Bank 5: y = 15, 16, 17
  Bank 2: y = 18, 19, 20         Bank 6: y = 18, 19, 20
  Bank 3: y = 21, 22, 23
```

All 3 Y coordinates for a given bank alias the **same DDR controller** and the same backing memory. Firmware only uses 1 port per bank per NoC, selected by the `BANK_PORT` table:

```python
BANK_PORT = [[2,1],[0,1],[0,1],[0,1],[2,1],[2,1],[2,1],[2,1]]
# BANK_PORT[bank_id][noc] = port offset from bank's base y
```

The `dram_bank_to_noc_xy` table written to L1 contains the specific port coordinate firmware will target. For the 7-bank P100A:

| Software Bank ID | Base (x, y₀) | NOC 0 Port (y₀ + offset) | NOC 1 Port (y₀ + offset) |
|------------------|---------------|---------------------------|---------------------------|
| 0 | (17, 12) | **(17, 14)** (+2) | **(17, 13)** (+1) |
| 1 | (17, 15) | **(17, 15)** (+0) | **(17, 16)** (+1) |
| 2 | (17, 18) | **(17, 18)** (+0) | **(17, 19)** (+1) |
| 3 | (17, 21) | **(17, 21)** (+0) | **(17, 22)** (+1) |
| 4 | (18, 12) | **(18, 14)** (+2) | **(18, 13)** (+1) |
| 5 | (18, 15) | **(18, 17)** (+2) | **(18, 16)** (+1) |
| 6 | (18, 18) | **(18, 20)** (+2) | **(18, 19)** (+1) |

The packed uint16 encoding for each entry is `(y << 6) | x` (see `niu.md` §4).

### 2.2 Harvesting

The P100A has 1 of 8 physical DRAM banks disabled. The ARC telemetry tag `TAG_GDDR_ENABLED` (tag 36) provides an 8-bit mask — bit N is 0 if bank N is harvested. The specific harvested bank varies per chip.

`build_bank_noc_table()` handles this by pushing the harvested bank's "mirror" (the bank on the opposite column at the same controller position) to the last slot in its column so that software bank IDs remain 0..6 contiguously. The layout is always 4 west + 3 east.

`NUM_DRAM_BANKS = 7` → interleaving uses divide-by-7 (not a power of 2). The compile-time define `IS_NOT_POW2_NUM_DRAM_BANKS=1` selects the magic-constant code path.

### 2.3 Bank Table Initialization

Before firmware boots, the host writes a bank lookup table to L1 at `MEM_BANK_TO_NOC_SCRATCH = 0x0116B0`. The table layout (2048 bytes total):

| Offset from scratch | Size | Contents |
|---------------------|------|----------|
| `+0x000` | up to 1024 bytes | `dram_bank_to_noc_xy`: `NUM_NOCS × NUM_DRAM_BANKS` × uint16 (packed `{y[5:0], x[5:0]}`) |
| (continues) | up to 1024 bytes | `l1_bank_to_noc_xy`: `NUM_NOCS × NUM_L1_BANKS` × uint16 |
| `+0x400` | up to 1024 bytes | `bank_to_dram_offset`: `NUM_DRAM_BANKS` × uint32 (byte offset adjustment per bank, typically all zeros) |
| (continues) | up to 1024 bytes | `bank_to_l1_offset`: `NUM_L1_BANKS` × uint32 |

During `noc_bank_table_init()` (called at BRISC/NCRISC/TRISC startup), firmware copies these tables from L1 into **core-private LDM** at `0xFFB00000`. The LDM offsets vary per core (verified against Blackhole ELFs):

| Core | `dram_bank_to_noc_xy` LDM offset | `bank_to_dram_offset` LDM offset |
|------|-----------------------------------|-----------------------------------|
| BRISC | `+0x048` (0xFFB00048) | `+0x298` (0xFFB00298) |
| NCRISC | `+0x040` (0xFFB00040) | `+0x290` (0xFFB00290) |

See `ldm-layouts.md` for the full per-core LDM field maps.

The firmware reads these LDM tables at runtime to resolve DRAM NoC addresses. The emulator must populate the L1 scratch region before boot.

### 2.4 Bank Interleaving

All DRAM tensors use **interleaved storage**: pages (tiles) are distributed round-robin across the 7 active banks.

For a given page ID (tile index within a tensor):

```
bank_offset_index = page_id / 7     (which slot within that bank — the quotient)
bank_index        = page_id % 7     (which bank — the remainder)
```

Example: a tensor of 20 tiles distributes across 7 banks:

```
page_id:  0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19
bank:     0  1  2  3  4  5  6  0  1  2  3  4  5  6  0  1  2  3  4  5
slot:     0  0  0  0  0  0  0  1  1  1  1  1  1  1  2  2  2  2  2  2
```

Bank 0 holds tiles {0, 7, 14} at slots 0, 1, 2. Bank 6 holds tiles {6, 13} at slots 0, 1.

#### The magic-constant divide-by-7

7 is not a power of 2, so hardware division is needed. RISC-V has no `div` instruction in the base ISA that TT uses (and even the M extension's `div` takes 30+ cycles). Instead, firmware uses the **multiply-high** trick from Hacker's Delight (§10-9):

**Goal:** compute `floor(n / 7)` using only multiply and shift.

**Key insight:** dividing by 7 is the same as multiplying by 1/7, but we need integer arithmetic. We scale up: multiply by a large constant M ≈ 2^k / 7, then shift right by k to undo the scaling.

**Derivation:**

```
We want:  floor(n / 7) = floor(n * M / 2^(32+s))

For d = 7, s = 2:
  M = ceil(2^34 / 7)
    = ceil(17179869184 / 7)
    = ceil(2454267026.286...)
    = 2454267027
    = 0x92492493
```

**Why this works:** `M / 2^34` is slightly larger than `1/7` (by at most 1 ULP). Multiplying n by M and dividing by 2^34 gives a value in the range `[n/7, n/7 + n/2^34)`. For all 32-bit n, the error `n/2^34` is less than 1, so `floor()` always produces the exact quotient.

**In RISC-V assembly** (from `dram_bank_addr` in `ttir.py`):

```asm
    # Input: tile_idx in some register (call it a0 here)
    # Output: a5 = quotient (bank_offset_index), a4 = remainder (bank_index)

    # Step 1: Load the magic constant
    li      a5, 0x92492493          # M = ceil(2^34 / 7) = 2454267027

    # Step 2: Multiply-high — get upper 32 bits of (a0 * a5)
    mulhu   a5, a0, a5             # a5 = floor((a0 * 0x92492493) / 2^32)
                                    #     (this is the mulhu instruction: unsigned
                                    #      multiply, return high 32 bits only)

    # Step 3: Post-shift to finish the division
    srli    a5, a5, 2              # a5 = a5 >> 2 = floor(a0 / 7)
                                    #     (total shift = 32 from mulhu + 2 = 34 bits)

    # Step 4: Compute remainder via back-multiply
    #   remainder = a0 - quotient * 7
    #   but there's no "multiply by 7" — use quotient*7 = quotient*8 - quotient
    slli    a4, a5, 3              # a4 = quotient * 8  (= quotient << 3)
    sub     a4, a4, a5             # a4 = quotient * 8 - quotient = quotient * 7
    sub     a4, a0, a4             # a4 = a0 - quotient*7 = a0 % 7  (bank_index)
```

**Worked example:** tile index 13 → which bank and slot?

```
Step 1: M = 0x92492493 = 2454267027

Step 2: mulhu(13, 2454267027)
        13 × 2454267027 = 31905471351 (64-bit product)
        upper 32 bits = floor(31905471351 / 2^32) = floor(31905471351 / 4294967296)
                      = 7

Step 3: 7 >> 2 = 1
        → bank_offset_index = 1  (this is the 2nd tile assigned to its bank)

Step 4: 1 * 8 = 8, 8 - 1 = 7, 13 - 7 = 6
        → bank_index = 6

Result: tile 13 goes to bank 6, slot 1.
```

Verify: tiles assigned to bank 6 are {6, 13, 20, ...}. Tile 13 is the 2nd (index 1). Correct.

#### Full assembly: divide + table lookup + address assembly

The complete `dram_bank_addr` function from `ttir.py` — this is what the compiler emits for every DRAM access in a kernel. It computes the quotient/remainder AND looks up the bank table AND assembles the final address:

```asm
    # Input:  a0 = tile_idx (page_id)
    #         bank_offset_table_reg = pointer to bank_to_dram_offset[] in LDM
    #         bank_xy_table_reg     = pointer to dram_bank_to_noc_xy[] in LDM
    # Output: addr_lo_out = DRAM address within the bank
    #         noc_xy_out  = packed NOC coordinate for the bank
    # Clobbers: a3, a4, a5

    # --- Divide by 7: quotient in a5, remainder in a4 ---
    li      a5, 0x92492493          # magic constant M = ceil(2^34 / 7)
    mulhu   a5, a0, a5             # a5 = upper32(a0 * M)
    srli    a5, a5, 2              # a5 = page = floor(a0 / 7)

    slli    a4, a5, 3              # a4 = page * 8
    sub     a4, a4, a5             # a4 = page * 7  (= page*8 - page)
    sub     a4, a0, a4             # a4 = bank = a0 - page*7

    # --- Table lookups ---
    sh2add  a3, a4, bank_offset_table_reg   # a3 = &bank_offsets[bank]  (4 bytes/entry, Zba ext)
    slli    a5, a5, 11                       # a5 = page * 2048  (page_size_shift=11 for Float16)
    sh1add  a4, a4, bank_xy_table_reg       # a4 = &bank_xy[bank]  (2 bytes/entry, Zba ext)

    lw      addr_lo_out, 0(a3)              # addr_lo = bank_to_dram_offset[bank]  (typically 0)
    lhu     noc_xy_out, 0(a4)               # noc_xy = dram_bank_to_noc_xy[bank]   (uint16)

    add     addr_lo_out, a5, addr_lo_out    # addr_lo = page_offset + bank_offset
```

The `sh2add` and `sh1add` instructions are from the RISC-V **Zba** (address generation) extension: `sh2add rd, rs1, rs2 = rd = (rs1 << 2) + rs2` — a fused shift-add that computes array element addresses in one instruction.

The `page_size_shift` parameter (11 for Float16 = 2048 bytes, 12 for Float32 = 4096 bytes) is a compile-time constant baked into the `slli` immediate. This is the assembly-level equivalent of `MUL_WITH_TILE_SIZE`.

After this sequence, the caller adds `bank_base_address` to `addr_lo_out` and uses `noc_xy_out` for `NOC_ADDR_HI`.

**What the emulator needs:** the emulator can just use native integer division (`page_id // 7` and `page_id % 7`). The magic-constant trick is a firmware optimization that the emulator does not need to replicate. But the emulator must understand that the firmware *does* use this trick, because:
- The magic constant `0x92492493` appears as a `li` instruction early in any DRAM-accessing kernel
- The `mulhu` + `srli` + `slli` + `sub` + `sub` pattern is the signature of a bank interleaving computation
- If the emulator traces instruction execution (for debugging), recognizing this sequence helps identify what the firmware is doing

### 2.5 InterleavedAddrGenFast

This is the firmware's address generator for interleaved DRAM tensors:

```cpp
template <bool DRAM>
struct InterleavedAddrGenFast {
    uint32_t bank_base_address;   // tensor's start address within each bank
    uint32_t page_size;           // (legacy field, not used in address calc)
    DataFormat data_format;       // determines tile byte size via MUL_WITH_TILE_SIZE
};
```

**Address computation** (what `get_noc_addr(page_id)` does):

```
1. bank_offset_index = page_id / 7                              (magic-constant divide)
2. bank_index        = page_id - bank_offset_index * 7          (remainder)
3. byte_offset       = MUL_WITH_TILE_SIZE(data_format, bank_offset_index)
4. addr              = byte_offset + bank_base_address + bank_to_dram_offset[bank_index]
5. noc_xy            = dram_bank_to_noc_xy[bank_index]
6. noc_addr          = (noc_xy << 36) | addr
```

Step 3 computes how far into the bank this tile lives: if this is the `bank_offset_index`-th tile assigned to this bank, its byte offset is `bank_offset_index * tile_bytes`.

Step 4 adds the tensor's base address and any per-bank offset adjustment (typically all zeros).

Step 5 looks up the NoC coordinate for this bank from the LDM table.

Step 6 assembles the 48-bit NoC address (36-bit local address + 12-bit XY coordinate), which the NIU splits into `ADDR_LO`, `ADDR_MID`, and `ADDR_HI` as documented in `niu.md` §4.

**Worked example:** reading tile 13 from a Float16 tensor starting at DRAM address `0x40000`, using NOC 0:

```
1. bank_offset_index = 13 / 7 = 1
2. bank_index        = 13 % 7 = 6
3. byte_offset       = 1 << 11 = 2048              (Float16: MUL_WITH_TILE_SIZE shifts by 11)
4. addr              = 2048 + 0x40000 + 0 = 0x40800
5. noc_xy            = dram_bank_to_noc_xy[6]       (for NOC 0: noc_xy(18, 20) = 0x0512)
6. noc_addr          = (0x0512 << 36) | 0x40800     → ADDR_LO  = 0x00040800
                                                      ADDR_MID = 0x00000000
                                                      ADDR_HI  = 0x0512
```

The firmware then writes these values into the NIU command buffer and fires `NOC_CMD_CTRL`.

### 2.6 DRAM Read/Write via NoC

The actual DRAM access is a standard NoC transaction — the same `noc_async_write` / `noc_async_read` used for tile-to-tile L1 copies. From the `add1` kernel disassembly:

**Write path** (`noc_async_write` at `add1_ncrisc.S:5960`):
```
NOC_TARG_ADDR_LO  = local L1 source address (where the tile lives in this core's L1)
NOC_RET_ADDR_LO   = addr  (step 4 above: byte offset within bank)
NOC_RET_ADDR_HI   = noc_xy >> 4  (bank's NoC coordinate)
NOC_CTRL          = 0x2092  (WR | RESP_MARKED | VC_STATIC)
NOC_AT_LEN_BE     = tile_bytes
NOC_CMD_CTRL      = 1  (fire)
```

**Read path** (`noc_async_read`): same register setup with WR=0, TARG is the remote DRAM address, RET is the local L1 destination.

No special DRAM protocol. The NIU routes the transaction to the DRAM controller's NoC coordinate; the DRAM controller reads/writes its backing memory at the specified address.

---

## 3. PCIe Endpoint

### 3.1 Endpoint Location

The PCIe endpoint is a single NoC node at coordinate **(x=19, y=24)** (translated coordinates). Its packed encoding:

```
PCIE_NOC_XY = (24 << 6) | 19 = 0x613
```

### 3.2 PCIe Address Encoding

PCIe transactions use **bit 60** of the 64-bit NoC address as a routing flag. Since the NoC address MID register covers bits [63:32], bit 60 maps to **bit 28 of `NOC_ADDR_MID`**:

```
NOC_TARG_ADDR_LO  = host memory offset bits [31:0]
NOC_TARG_ADDR_MID = 0x10000000  (bit 28 = bit 60 of 64-bit addr = PCIe flag)
NOC_TARG_ADDR_HI  = 0x613       (PCIe endpoint coordinate)
```

From `cq_dispatch_brisc.S:5020`:
```asm
lui  a4, 0x10000          # a4 = 0x10000000 (PCIe flag in ADDR_MID)
sw   a4, 16(a3)           # NOC_RET_ADDR_MID = 0x10000000
li   a4, 1555             # a4 = 0x613 = (24<<6)|19
sw   a4, 20(a3)           # NOC_RET_ADDR_HI = PCIe endpoint coordinate
```

The prefetch core uses a compact encoding that packs both the PCIe flag and coordinate into one register, then unpacks:
```asm
# cq_prefetch_brisc.S:5800
lui  a1, 0x10006           # combine PCIe flag + coordinate
addi a1, a1, 0x130         # a1 = 0x10006130
# noc_async_read at 0x4d24 unpacks:
# TARG_ADDR_MID = a1 & 0x1000000F → 0x10000000 (PCIe bit)
# TARG_ADDR_HI  = (a1 >> 4) & 0xFFFFF → 0x00613 (PCIe coordinate)
```

### 3.3 PCIe Address Space

The lower 36 bits of the NoC address index into **host system memory** (sysmem). The prefetch core reads from a host ring buffer mapped at `0x40000100` through `0x44000100` (64 MiB PCIe BAR window), wrapping around at the end. This maps to physical host memory via the **iATU** (internal Address Translation Unit) in the PCIe controller.

The `pcie_read_ptr` variable in LDM tracks the current read position in the host ring buffer.

### 3.4 Transaction Types

- **Inbound reads** (prefetch core → host): `noc_async_read` targeting (19, 24) with bit 60 set — returns data from host memory buffer
- **Outbound writes** (dispatch core → host): `noc_async_write` targeting (19, 24) with bit 60 set — writes into host memory buffer

Both use the standard NIU command buffer flow. The only difference from a tile-to-tile transfer is the target coordinate and the bit 60 flag.

---

## 4. What the Emulator Needs

### 4.1 DRAM Controller Nodes (P100A)

Add 7 DRAM controller nodes to the NoC grid. Each bank has 3 ports (3 NoC tile coordinates) that alias the same backing buffer. Register all 21 coordinates; route any transaction targeting a bank's port to that bank's buffer:

| Bank | Port 0 (y₀) | Port 1 (y₀+1) | Port 2 (y₀+2) | Backing |
|------|-------------|----------------|----------------|---------|
| 0 | (17, 12) | (17, 13) | (17, 14) | Single buffer |
| 1 | (17, 15) | (17, 16) | (17, 17) | Single buffer |
| 2 | (17, 18) | (17, 19) | (17, 20) | Single buffer |
| 3 | (17, 21) | (17, 22) | (17, 23) | Single buffer |
| 4 | (18, 12) | (18, 13) | (18, 14) | Single buffer |
| 5 | (18, 15) | (18, 16) | (18, 17) | Single buffer |
| 6 | (18, 18) | (18, 19) | (18, 20) | Single buffer |

Firmware only targets one port per bank per NoC (selected by `BANK_PORT`), but the emulator should register all 3 ports per bank since the port selection is encoded in the bank table, not hardcoded in firmware.

**Buffer sizing:** Real hardware has 4 GiB per bank. For emulation, size to fit the workload — even 64 MiB per bank is sufficient for most kernels. The backing store is a flat `bytearray`.

### 4.2 Bank Table Population

Before firmware boots, the emulator must write the bank-to-NoC lookup tables to L1 at `MEM_BANK_TO_NOC_SCRATCH = 0x0116B0` for every tile. Use the same format as `build_bank_noc_table()`:

```python
# For each tile's L1, at offset 0x116B0:
#   dram_bank_to_noc_xy:  NUM_NOCS * NUM_DRAM_BANKS * 2 bytes (uint16 per entry)
#   l1_bank_to_noc_xy:    NUM_NOCS * NUM_L1_BANKS * 2 bytes
#   bank_to_dram_offset:  NUM_DRAM_BANKS * 4 bytes (uint32, typically all zeros)
#   bank_to_l1_offset:    NUM_L1_BANKS * 4 bytes

# Each uint16 noc_xy entry = (y << 6) | x
```

Firmware's `noc_bank_table_init()` copies these into LDM during boot. The emulator does not need to simulate this copy — if LDM is backed by the same memory or the copy is handled by the emulated firmware — but the L1 source data must be correct.

### 4.3 NIU Routing Extension

The NIU model (from `niu.md` §8) currently fires transactions between tiles. Extend the target resolution:

```python
def resolve_target(self, noc_xy, addr_mid):
    if noc_xy in self.dram_nodes:
        return self.dram_nodes[noc_xy]    # → DRAM controller backing buffer
    if noc_xy == PCIE_NOC_XY and (addr_mid & (1 << 28)):
        return self.pcie_node              # → host memory buffer
    return self.tiles[noc_xy]              # → tile L1 (existing path)
```

No changes to the NIU command flow. `NOC_CMD_CTRL` fires, NIU decodes the target coordinate, and routes to the appropriate backing store. Reads and writes execute against the target's byte buffer at the address specified in `ADDR_LO`.

### 4.4 PCIe Endpoint Node

Add 1 PCIe endpoint node at (19, 24):

```python
class PcieEndpoint:
    def __init__(self, sysmem_size=64 * 1024 * 1024):
        self.memory = bytearray(sysmem_size)  # host system memory

    def read(self, addr, length):
        offset = addr & 0xFFFFFFFFF  # lower 36 bits
        return self.memory[offset : offset + length]

    def write(self, addr, data):
        offset = addr & 0xFFFFFFFFF
        self.memory[offset : offset + len(data)] = data
```

The host side pre-fills this buffer with command data (for the prefetch core) and reads completion data (from the dispatch core).

### 4.5 What Does NOT Need a New Spec

- **No new bus or interface protocol** — both DRAM and PCIe use the existing NoC command buffer mechanism
- **No changes to the NIU command flow** — `NOC_CMD_CTRL` fires, NIU routes based on coordinate, same as tile-to-tile
- **No tile header handling** — tt-metal disables packer tile headers
- **No tilization logic in the DRAM model** — DRAM stores raw bytes; tile layout is a firmware/host concern

---

## 5. Source References

| File | Description |
|------|-------------|
| `blackhole-py/hw.py` | DRAM bank coordinates, `build_bank_noc_table()`, `PCIE_NOC_XY`, `BANK_PORT` |
| `blackhole-py/ttir.py` | RISC-V assembly for `dram_bank_addr()`, magic constant `0x92492493` |
| `tt-metal/hw/inc/internal/dataflow/dataflow_api_addrgen.h` | `InterleavedAddrGenFast`, `MUL_WITH_TILE_SIZE`, `get_bank_offset_index`, `get_bank_index` |
| `tt-metal/hw/inc/internal/mod_div_lib.h` | `fast_udiv_7()`, `udivsi3_const_divisor` |
| `tt-metal/hw/inc/internal/firmware_common.h` | `noc_bank_table_init()` |
| `tt-metal/hw/inc/internal/tt-1xx/blackhole/dev_mem_map.h` | `MEM_BANK_TO_NOC_SCRATCH`, table sizes |
| `tt-metal/api/tt-metalium/tt_backend_api_types.hpp` | `DataFormat` enum, `tile_size()` |
| `tt-metal/impl/data_format/tilize_utils.cpp` | Host-side tilization |
| `tt-metal/impl/data_format/tile.cpp` | Tile shape and size computation |
| `tt_llk_blackhole/llk_lib/llk_unpack_tilize.h` | Device-side tilize via unpacker hardware |
| `tt_llk_blackhole/llk_lib/llk_pack_untilize.h` | Device-side untilize via packer hardware |
| `tt-metal/impl/device/firmware/risc_firmware_initializer.cpp` | Host-side bank table generation |
| `tt-metal/jit_build/build_env_manager.cpp` | `NUM_DRAM_BANKS`, `PCIE_NOC_X/Y` compile defines |
