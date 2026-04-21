# Dest, SrcA, and SrcB Register Files

The Tensix coprocessor has three named register files that hold tile data during
computation: **Dest** (also called "accumulator" or "Dst"), **SrcA**, and **SrcB**.
Each is physically separate storage with its own addressing and ownership rules.

---

## 1. Dest Register File

### 1.1 Physical Storage

Dest is a flat array of 16-bit cells:

```c
uint16_t DstBits[1024][16];
bool     DstRowValid[1024];
```

- **1024 rows**, each **16 columns** wide.
- Each cell is **16 bits** of raw storage.
- Each row has one associated **valid bit** (`DstRowValid`).
- Total storage: `1024 × 16 × 2 bytes = 32 KiB`.

### 1.2 Two Views: Dst16b and Dst32b

The same storage is exposed under two named views depending on the active
data format:

| View | Shape | Element width | Row index range |
|------|-------|--------------|-----------------|
| `Dst16b` | 1024 rows × 16 cols | 16-bit | 0–1023 |
| `Dst32b` | 512 rows × 16 cols | 32-bit | 0–511 |

Both views alias the same `DstBits[1024][16]` array. `Dst32b[Row][Col]` is
defined as:

```c
uint32_t read  = (DstBits[Adj32(Row)][Col] << 16) | DstBits[Adj32(Row) + 8][Col];
// write stores the high 16b at Adj32(Row) and the low 16b at Adj32(Row)+8
```

`Dst16b[Row][Col]` is normally sugar for `DstBits[Adj16(Row)][Col]`.

**`Adj16` and `Adj32` functions** (from `Dst.md`):

```c
uint10_t Adj16(uint10_t r) {
  if (Config.DEST_ACCESS_CFG_remap_addrs) {
    r = (r & 0x3c7) ^ ((r & 0x030) >> 1) ^ ((r & 0x008) << 2);
  }
  return r;
}

uint10_t Adj32(uint10_t r) {
  r = Adj16(r);
  if (Config.DEST_ACCESS_CFG_swizzle_32b) {
    r = (r & 0x3f3) ^ ((r & 0x018) >> 1) ^ ((r & 0x004) << 1);
  }
  return ((r & 0x1f8) << 1) | (r & 0x207);
}
```

Both `remap_addrs` and `swizzle_32b` also affect how packers address Dest.

### 1.3 Data Types

`Dst16b` elements hold one of:

| Type | Width | Notes |
|------|-------|-------|
| BF16 | 16-bit | Sign(1) + Man(7) + Exp(8); bit order in storage is Sign,Man(7b),Exp(8b) |
| FP16 | 16-bit | Sign(1) + Exp(5) + Man(10); bit order in storage is Sign,Man(10b),Exp(5b) |
| Integer "8" | 16-bit | Overlaid on FP16; Sign(1) + Mag(10b), raw exponent field held as 16 (or 0 when zero) |
| Integer "16" | 16-bit | Opaque 16 bits; no computation instructions use this type |

`Dst32b` elements hold one of:

| Type | Width | Notes |
|------|-------|-------|
| FP32 | 32-bit | Sign(1) + Exp(8) + Man(23); stored as Sign,Man(7b),Exp(8b),Man(3b low),Zeros(13b) |
| Integer "32" | 32-bit | Sign/magnitude: 1 sign bit + 31 magnitude bits |

The coprocessor does not fully conform to IEEE 754 for floating-point types.

**Active mode selection:** `Config.ALU_ACC_CTRL_Fp32_enabled` or
`Config.ALU_ACC_CTRL_INT8_math_enabled` selects Dst32b; otherwise Dst16b is
active. Most instructions (`MVMUL`, `ZEROACC`, `MOVD2A`, etc.) read this flag
to decide which view to use.

### 1.4 Tile and Face Decomposition

LLK software decomposes Dest into tiles and faces for addressing:

| Constant | Value | Source |
|----------|-------|--------|
| `FACE_HEIGHT` | 16 rows | `ckernel_defs.h` |
| `FACE_WIDTH` | 16 columns | `ckernel_defs.h` |
| `TILE_HEIGHT` | 32 rows | `ckernel_defs.h` |
| `TILE_WIDTH` | 32 columns | `ckernel_defs.h` |
| `DEST_REGISTER_FULL_SIZE` | 1024 rows (Dst16b) | `tensix_types.h`: `64 * DEST_FACE_HEIGHT` |
| `DEST_REGISTER_HALF_SIZE` | 512 rows (Dst16b) | `tensix_types.h`: `DEST_REGISTER_FULL_SIZE / 2` |
| `BIT32_DEST_REGISTER_HALF_SIZE` | 256 rows (Dst32b) | `tensix_types.h`: `DEST_REGISTER_HALF_SIZE / 2` |
| `DEST_NUM_TILES_FP16` | 16 tiles (32×32) | `ckernel_defs.h` |
| `MATH_HALF_DEST_SIZE` | 32 faces (of 16×16) | `ckernel_structs.h` |

A 32×32 tile occupies **64 Dst16b rows** (4 faces × 16 rows/face). A 32×16
tile occupies 32 rows. A 16×16 tile occupies 16 rows.

In FP32 (Dst32b) mode, a 32×32 tile still uses the same 64 `DstBits` rows,
but only 32 `Dst32b` row-index slots are consumed (because each 32-bit row
uses two adjacent 16-bit rows via `Adj32`). The effective tile capacity is
halved: instead of 16 tiles, only **8 tiles** fit in Dest, and each half holds
4 tiles instead of 8.

### 1.5 Half-Dest Double-Buffering

Dest is logically split into two halves:

| Half | Dst16b rows | Dst32b rows | LLK constant |
|------|------------|-------------|--------------|
| Low half | 0–511 | 0–255 | offset 0 (`dest_offset_id == 0`) |
| High half | 512–1023 | 256–511 | offset `DEST_REGISTER_HALF_SIZE` = 512 (`dest_offset_id == 1`) |

The **MATH_PACK semaphore** (index 1) coordinates ownership of these halves
between the math thread (T1) and the pack thread (T2). The protocol:

```
Initialization (SyncHalf mode):
  SEMINIT(max=2, val=0, sem=MATH_PACK)
  dest_offset_id = 0

Math thread (T1) before each tile:
  SEMWAIT on MATH_PACK != Max (i.e. room to write)
  → writes math results into current half (dest_offset_id)
  → SEMPOST(MATH_PACK)    [set_math_semaphores()]
  → dest_section_flip():  update_dest_offset_id(), flip DEST_TARGET_REG_CFG_MATH_Offset

Pack thread (T2) before each tile:
  SEMWAIT on MATH_PACK != 0 (i.e. data to pack)
  → PACR reads the half that math just finished
  → ZEROACC(CLR_HALF, dest_offset_id) to mark that half as invalid
  → SEMGET(MATH_PACK)     [_llk_packer_set_math_semaphore_()]
  → flip_packer_dest_offset_id(), select_packer_dest_registers()
```

The semaphore's `Max` value is 2 in `SyncHalf` mode and 1 in `SyncFull` mode
(where math and pack share the entire Dest sequentially). With `Max=2`, the
semaphore can range 0–2, allowing one half to be in math's hands and the other
in pack's hands simultaneously.

The global variable `dest_offset_id` (0 or 1) tracks which half is currently
being written by math. `get_dest_buffer_base()` returns
`dest_offset_id ? DEST_REGISTER_HALF_SIZE : 0`. Both the math thread and the
pack thread maintain their own pointer using the same variable, flipped in
lockstep via the semaphore.

### 1.6 ZEROACC: Marking Rows Invalid

`ZEROACC` does not write zeroes into `DstBits`. It clears `DstRowValid` bits.
Subsequent reads of an invalid row behave as:

- **Packers**: read zero from invalid rows.
- **Matrix Unit (FPU)**: read the identity element (0 for `MVMUL`/`ELWADD`;
  −∞ for `GMPOOL`/`MPOOL3S*`), then mark the row valid after writing.
- **Vector Unit (SFPU)**: `UndefinedBehavior` if reading an invalid row.
- **Unpackers**: `UndefinedBehavior` if writing to only some columns of an
  invalid row.

**ZEROACC field encoding** (from `dsl.py` and `ZEROACC.md`):

```
bits[23:19] = clear_mode    (5 bits)
bits[18]    = use_32_bit_mode
bits[17]    = clear_zero_flags
bits[16:14] = addr_mode     (3 bits, AddrMod)
bits[13:0]  = where         (14 bits, Imm10 + extras)
```

**`clear_mode` values** (from LLK `ckernel_defs.h`):

| `clear_mode` | Constant | Behavior |
|-------------|----------|----------|
| 0 | `ClearRow` / `ZEROACC_MODE_ONE_ROW` | Clear one row at `Imm10 + DEST_TARGET_REG_CFG_MATH_Offset + RWC.Dst + DEST_REGW_BASE`. Applies address remapping when Dst32b mode is active. Advances AddrMod. |
| 1 | `Clear16Rows` / `ZEROACC_MODE_16_ROWS` | Clear 16 contiguous rows within a tile-aligned block. `Imm10` selects the block. In Dst16b mode: block = `Imm10 * 16` (requires `Imm10 < 64`). In Dst32b (`use_32_bit_mode=1`): block = `Imm10 * 32` with 16 rows scattered (requires `Imm10 < 32`). Advances AddrMod. Out-of-range `Imm10` is a NOP on current silicon. |
| 2 | `ClearHalf` / `ZEROACC_MODE_HALF_OF_DST` | Clear rows 0–511 (`where & 1 == 0`) or rows 512–1023 (`where & 1 == 1`). No AddrMod. |
| 3 | `ClearFull` / `ZEROACC_MODE_ALL_OF_DST` | Clear all 1024 rows. No AddrMod. |

**`use_32_bit_mode`** (`use_32_bit_mode=1`): selects the Dst32b scatter
pattern for `ZEROACC_MODE_16_ROWS`. For `ZEROACC_MODE_ONE_ROW`, equivalent
behavior is controlled by `ALU_ACC_CTRL_Fp32_enabled` or
`ALU_ACC_CTRL_INT8_math_enabled` in the backend config.

**Typical packer sequence (SyncHalf)**:

```c
// In pack thread, after reading a half:
TT_ZEROACC(p_zeroacc::CLR_HALF, is_fp32_dest_acc_en, 0, ADDR_MOD_1, dest_offset_id % 2);
// dest_offset_id==0 → clears low half (rows 0–511)
// dest_offset_id==1 → clears high half (rows 512–1023)
```

**Typical init sequence (SyncFull)**:

```c
TTI_ZEROACC(p_zeroacc::CLR_ALL, 0, 0, ADDR_MOD_1, 0);
```

### 1.7 RISCV Debug Window at 0xFFBD8000

RISCV T0, T1, and T2 can read and write Dest directly via a memory-mapped
window:

```
Base address: 0xFFBD8000
Size:         32 KiB  (= DEST_REGISTER_FULL_SIZE_BYTES = 1024 × 16 × 2 bytes)
```

The window always spans the entire 1024-row, 16-column Dest array regardless
of whether Dst16b or Dst32b mode is active. Access format is controlled by
per-thread config `RISC_DEST_ACCESS_CTRL_SEC[CurrentThread].{no_swizzle, unsigned_int, fmt}`:

| `fmt` | RISCV view | Access width |
|------:|-----------|-------------|
| 0 | `float Dst32b[512][16]` or `uint32_t Dst32b[512][16]` | 32-bit `lw`/`sw` |
| 1 | `int32_t Dst32b[512][16]` (two's complement ↔ sign-magnitude conversion) | 32-bit |
| 2 | `__fp16 Dst16b[1024][16]` | 16-bit `lh`/`sh` |
| 3 | `__bf16 Dst16b[1024][16]` | 16-bit |
| 4 | `int16_t` or `uint16_t Dst16b[1024][16]` | 16-bit |
| 5 | `int8_t` or `uint8_t Dst16b[1024][16]` | 8-bit `lb`/`sb` |

Bit-layout conversions (swizzling) are applied on access unless `no_swizzle`
is set. For example, FP32 bits are stored in Dest with a non-standard layout
(`Sign,Man(7b),Exp(8b),Man(3b low),Zeros(13b)`) and the `no_swizzle=0` path
re-orders them to standard IEEE754 on each load/store.

RISCV T0 and T1 access one element at a time with the appropriate-width
instruction. RISCV T2 can access multiple elements per instruction, aligned to
the total transfer size.

Address calculation (for T0/T1): `element_index = (Addr - 0xFFBD8000) / element_bytes`.

```c
// FP32 mode (fmt=0): Addr = 0xFFBD8000 + (row * 16 + col) * 4
// BF16 mode (fmt=3): Addr = 0xFFBD8000 + (row * 16 + col) * 2
```

**Debug usage example** (from `dprint_tensix.h`):

```c
// Read a FP32 row from Dest (ARCH_BLACKHOLE path):
const uint32_t* addr = reinterpret_cast<const uint32_t*>(0xFFBD8000);
for (int i = 0; i < 16; ++i) {
    rd_data[i] = addr[i + (row << 4)];  // row * 16 + column
}
```

**Note on debug window size**: the window is always 32 KiB regardless of
active data format, because the underlying `DstBits[1024][16]` is 32 KiB of
16-bit storage. FP32 mode (`fmt=0,1`) exposes only rows 0–511 of Dst32b
(512 × 16 × 4 bytes = 32 KiB), which maps to the same physical storage.

### 1.8 Instruction Scheduling Hazard

After any instruction that writes to Dest, the written 8×16-row-aligned block
cannot be read for the next **4 cycles**. The hardware stalls the thread
automatically if a Matrix Unit or PACR instruction tries to read it. To avoid
stalls when accumulating (e.g., looping `MVMUL`), software should cycle over at
least **5 distinct 8-row blocks** of Dest between consecutive writes to the same
block.

---

## 2. SrcA Register File

### 2.1 Physical Storage

```c
enum class SrcClient { MatrixUnit, Unpackers };

struct {
  SrcClient AllowedClient;   // initially Unpackers
  uint19_t  Rows[64][16];
} SrcA[2];
```

- **2 banks**, each with **64 rows** × **16 columns** of **19-bit** data.
- Total storage per bank: `64 × 16 × 19 bits ≈ 2.4 KiB` (stored in 3-byte cells).
- Total SrcA: `2 × 2.4 KiB ≈ 4.8 KiB`.

The 19-bit element width accommodates TF32 (19 bits: 1 sign + 10 mantissa + 8
exponent), the widest data type in SrcA.

### 2.2 Data Types

| Type | Storage width | Notes |
|------|--------------|-------|
| TF32 | 19 bits | Sign(1) + Man(10) + Exp(8); stored as Sign,Man(10b),Exp(8b) |
| BF16 | 19 bits | Overlaid on TF32 with low 3 mantissa bits = 0; stored as Sign,Man(10b),Exp(8b) |
| FP16 | 19 bits | Stored as Sign,Man(10b),Zero(3b),Exp(5b) |
| Integer "8" | 19 bits | Overlaid on FP16; Sign(1) + Mag(10b), fixed exponent field |
| Integer "16" | 19 bits | Opaque 16-bit transfer; no computation instructions |

The BF16/TF32 and FP16/Int8 internal representations differ between Src and Dst.
Shuffle functions handle the conversion:

```c
uint19_t ShuffleBF16(uint16_t x) {  // Dst BF16 → Src BF16
  return ((x & 0xFF00) << 3) | (x & 0xFF);
}
uint19_t ShuffleFP16(uint16_t x) {  // Dst FP16 → Src FP16
  return ((x & 0xFFE0) << 3) | (x & 0x1F);
}
uint19_t ShuffleTF32(uint19_t x) {  // Dst TF32 → Src TF32
  uint19_t SignHiMan = x & 0x3fc000;
  uint19_t Exp       = x & 0x0007f8;
  uint19_t LoMan     = x & 0x000007;
  return SignHiMan | (LoMan << 8) | (Exp >> 3);
}
```

### 2.3 Bank Tracking State

Four bank indices are maintained:

```c
uint1_t MatrixUnit::SrcABank = 0;     // which bank FPU is reading from
uint1_t Unpackers[0]::SrcBank = 0;   // which bank unpacker 0 is writing to
```

Additionally, each unpacker tracks a per-thread row cursor:

```c
uint6_t Unpackers[0]::SrcRow[3];  // indexed by Tensix thread
```

### 2.4 Double-Buffering Protocol (Bank Flipping)

The two SrcA banks allow the unpacker to load the next tile while the Matrix
Unit consumes the current tile. Ownership is mediated by `AllowedClient`:

**Giving a bank to the Matrix Unit (SETDVALID / UNPACR_NOP):**

```c
// SETDVALID with FlipSrcA=1 (or UNPACR_NOP 0x7 for WhichUnpacker=0):
SrcA[Unpackers[0].SrcBank].AllowedClient = SrcClient::MatrixUnit;
Unpackers[0].SrcBank ^= 1;
Unpackers[0].SrcRow[CurrentThread] = ThreadConfig[CurrentThread].SRCA_SET_Base << 4;
```

**Giving a bank back to Unpackers (CLEARDVALID):**

```c
// CLEARDVALID with FlipSrcA=1:
SrcA[MatrixUnit.SrcABank].AllowedClient = SrcClient::Unpackers;
if (!KeepReadingSameSrc) MatrixUnit.SrcABank ^= 1;
```

**Flipping during MVMUL (FlipSrcA bit):**

```c
// At end of MVMUL with FlipSrcA=1:
if (!ThreadConfig[CurrentThread].CLR_DVALID_SrcA_Disable) {
    SrcA[MatrixUnit.SrcABank].AllowedClient = SrcClient::Unpackers;
}
MatrixUnit.SrcABank ^= 1;
```

**STALLWAIT conditions** for SrcA bank synchronization:

| Condition | Meaning |
|-----------|---------|
| C5 | `SrcA[Unpackers[0].SrcBank].AllowedClient != SrcClient::Unpackers` — unpack side is not ready |
| C7 | `SrcA[MatrixUnit.SrcABank].AllowedClient != SrcClient::MatrixUnit` — math side is not ready |
| `SRCA_VLD` (0x80) | Used as a STALLWAIT mask for waiting for SrcA to be given to the Matrix Unit |

LLK calls: `wait_bank_valid<SrcA>()` issues `TTI_STALLWAIT(p_stall::STALL_MATH, p_stall::SRCA_VLD)`.

**SETRWC** with `CLR_A` also gives the current SrcA bank back to Unpackers
and flips MatrixUnit.SrcABank.

### 2.5 How UNPACR Fills SrcA

Unpacker 0 fills SrcA. Key fields from `UNPACR_Regular.md`:

- `WhichUnpacker = 0` → targets SrcA (or Dest if configured).
- The unpacker writes to `SrcA[Unpackers[0].SrcBank]` starting at
  `Unpackers[0].SrcRow[CurrentThread]`.
- Row filling is **sequential** from the initial row, advancing by 1 per datum
  until the configured `YDim` rows are written.
- XDim controls the column count per row (normally 16).
- In MultiContextMode, `XDim` can vary by context.
- **X/Y transposition** is available when writing to SrcA (not available for
  SrcB or Dest): if enabled, the unpacker writes columns as rows, producing a
  transposed result in SrcA.

After the UNPACR operation completes, `UNPACR_NOP` with opcode 0x7 is used to
hand the filled bank to the Matrix Unit and flip the unpacker to the other bank.

### 2.6 How MVMUL/ELWADD Read from SrcA

`MVMUL` reads a **16-row × 16-column block** from SrcA:

```c
uint6_t SrcARow = RWCs[CurrentThread].SrcA & 0x38;  // aligned to 8
// reads SrcA[MatrixUnit.SrcABank][SrcARow + 0..15][0..15]
```

The SrcA operand to `MVMUL` is always exactly 16 rows × 16 columns (a 16×16
matrix). The SrcB operand is 8 rows × 16 columns (aligned to 8). The result
is an 8×16 matrix added into Dest.

`ELWADD` and other element-wise operations also read from
`SrcA[MatrixUnit.SrcABank]` using `RWCs[CurrentThread].SrcA` as the row
index, operating on up to 16 rows.

---

## 3. SrcB Register File

### 3.1 Physical Storage

```c
struct {
  SrcClient AllowedClient;   // initially Unpackers
  uint19_t  Rows[64][16];
} SrcB[2];
```

Identical layout to SrcA: **2 banks** × **64 rows** × **16 columns** × **19 bits**.

SrcA and SrcB are physically the same size and the same element width. The
distinction is which unpacker writes them (unpacker 0 → SrcA, unpacker 1 →
SrcB) and that certain operations treat them asymmetrically (SrcA is the
right-hand matrix in `MVMUL`; SrcB is the left-hand matrix).

### 3.2 Data Types

Identical to SrcA: TF32, BF16, FP16, Integer "8", Integer "16" — all stored
in 19-bit cells with the same bit layouts.

### 3.3 Bank Tracking State

```c
uint1_t MatrixUnit::SrcBBank = 0;     // which bank FPU is reading from
uint1_t Unpackers[1]::SrcBank = 0;   // which bank unpacker 1 is writing to
uint6_t Unpackers[1]::SrcRow[3];     // per-thread row cursor
```

### 3.4 Double-Buffering Protocol

Identical to SrcA, but using `Unpackers[1]` and `MatrixUnit.SrcBBank`:

```c
// SETDVALID with FlipSrcB=1 (or UNPACR_NOP 0x7 for WhichUnpacker=1):
SrcB[Unpackers[1].SrcBank].AllowedClient = SrcClient::MatrixUnit;
Unpackers[1].SrcBank ^= 1;
Unpackers[1].SrcRow[CurrentThread] = ThreadConfig[CurrentThread].SRCB_SET_Base << 4;
```

```c
// CLEARDVALID with FlipSrcB=1:
SrcB[MatrixUnit.SrcBBank].AllowedClient = SrcClient::Unpackers;
if (!KeepReadingSameSrc) MatrixUnit.SrcBBank ^= 1;
```

**STALLWAIT conditions** for SrcB:

| Condition | Meaning |
|-----------|---------|
| C6 | `SrcB[Unpackers[1].SrcBank].AllowedClient != SrcClient::Unpackers` |
| C8 | `SrcB[MatrixUnit.SrcBBank].AllowedClient != SrcClient::MatrixUnit` |
| `SRCB_VLD` (0x100) | Used as STALLWAIT mask for waiting for SrcB to be given to the Matrix Unit |

LLK constant `SRCB_ROW16_OFFSET = 0x10` (16 rows) is a frequently used SrcB
row offset for separating two 16×16 faces within the same bank.

### 3.5 How UNPACR Fills SrcB

Unpacker 1 fills SrcB. Behavior is symmetric to SrcA / Unpacker 0, except:

- **No X/Y transposition** available for SrcB (only SrcA supports this).
- SrcB unpacker (`WhichUnpacker = 1`) does **not** support MultiContextMode
  with `WhichContext >= 2` (UndefinedBehavior if attempted).
- Row filling is sequential from `Unpackers[1].SrcRow[CurrentThread]`.

### 3.6 TRNSPSRCB: Transpose Rows 16–31 In Place

`TRNSPSRCB` transposes the 16×16 matrix stored in SrcB rows 16–31 of the
current Matrix Unit bank:

```c
// Waits for SrcB[MatrixUnit.SrcBBank].AllowedClient == MatrixUnit:
uint6_t RowBase = 16;
for (unsigned i = 0; i < 16; ++i) {
  for (unsigned j = 0; j < i; ++j) {
    uint19_t ij = SrcB[MatrixUnit.SrcBBank][RowBase + i][j];
    uint19_t ji = SrcB[MatrixUnit.SrcBBank][RowBase + j][i];
    SrcB[MatrixUnit.SrcBBank][RowBase + i][j] = ji;
    SrcB[MatrixUnit.SrcBBank][RowBase + j][i] = ij;
  }
}
```

**What changes**: only rows 16–31 of the active SrcB bank are affected.
Rows 0–15 are untouched. The operation swaps elements `[i][j]` and `[j][i]`
for all `j < i`, producing a standard matrix transpose of the 16×16 block in
place. Rows 0–15 are typically used to hold the SrcB matrix for the current
`MVMUL`, while rows 16–31 hold a pre-transposed version for the next phase.

`TRNSPSRCB` waits at the Wait Gate until `SrcB[MatrixUnit.SrcBBank].AllowedClient == MatrixUnit`.

### 3.7 SrcA vs SrcB Differences

| Property | SrcA | SrcB |
|----------|------|------|
| Unpacker | Unpacker 0 | Unpacker 1 |
| X/Y transpose during unpack | Yes | No |
| Role in MVMUL | Right-hand matrix (16×16) | Left-hand matrix (8×16 or 1×16 broadcast) |
| TRNSPSRCB | Not applicable | Rows 16–31 transposable |
| MultiContextMode context limit | 8 contexts (context 0–7) | 2 contexts (0 and 1 only) |
| Row cursor SETBASE config | `SRCA_SET_Base` | `SRCB_SET_Base` |

---

## 4. Data Movement Instructions: MOVD2A, MOVD2B, MOVA2D, MOVB2D, MOVB2A

These Matrix Unit (FPU) instructions move data between the three register files
without involving L1 memory.

### 4.1 MOVD2A — Dest → SrcA

Copies 1 or 4 aligned rows from Dest into the active SrcA bank.

```c
TT_MOVD2A(/* bool */ UseDst32bLo,
          /* u6  */ SrcRow,      // destination row in SrcA
          /* u2  */ AddrMod,
         (/* bool */ Move4Rows) << 1,
          /* u10 */ DstRow)      // source row in Dest
```

- `Move4Rows=0`: copies 1 row; `Move4Rows=1`: copies 4 rows (DstRow aligned
  to 4, SrcRow aligned to 4).
- SrcRow range: `SrcRow + RWCs[CurrentThread].SrcA`, masked to 6 bits.
- DstRow range: `DstRow + DEST_TARGET_REG_CFG_MATH_Offset + RWCs[CurrentThread].Dst + DEST_REGW_BASE_Base`.
- Writes to `SrcA[MatrixUnit.SrcABank]`.
- **Does not automatically wait** for `SrcA[MatrixUnit.SrcABank].AllowedClient == MatrixUnit`.
  Use `STALLWAIT(B6, C7)` before `MOVD2A` if needed.
- After `MOVD2A`, the next cycle only accepts `MOVD2A` or `MOVB2A` from the
  Matrix Unit; other instructions are automatically stalled for 1 cycle.
- Data format conversion: applies `ShuffleBF16`, `ShuffleFP16`, or
  `ShuffleTF32` based on `ALU_FORMAT_SPEC_REG0_SrcA` and Fp32 mode.

### 4.2 MOVD2B — Dest → SrcB

Copies 1 or 4 aligned rows from Dest into the active SrcB bank.

```c
TT_MOVD2B(/* bool */ UseDst32bLo,
          /* u6  */ SrcRow,      // destination row in SrcB
          /* u2  */ AddrMod,
         (/* bool */ Move4Rows) << 1,
          /* u10 */ DstRow)
```

- Identical structure to `MOVD2A` but targets `SrcB[MatrixUnit.SrcBBank]`.
- **Does not automatically wait** for SrcB bank validity. Use
  `STALLWAIT(B6, C8)`.
- After `MOVD2B`, the next **3 cycles** only accept another `MOVD2B`.
- Note: `MOVD2B` uses `ALU_FORMAT_SPEC_REG0_SrcA` (not SrcB) to determine
  the conversion style — this is not a documentation error, it is hardware
  behavior.

### 4.3 MOVA2D — SrcA → Dest

Copies 1 or 8 aligned rows from the active SrcA bank into Dest.

```c
TT_MOVA2D(/* bool */ UseDst32bLo,
          /* u6  */ SrcRow,
          /* u2  */ AddrMod,
         (/* bool */ Move8Rows) << 1,
          /* u10 */ DstRow)
```

- `Move8Rows=1`: copies 8 rows (SrcRow aligned to 8, DstRow aligned to 8).
- **Waits** at Wait Gate for `SrcA[MatrixUnit.SrcABank].AllowedClient == MatrixUnit`.
- After `MOVA2D`, software should avoid reading the written Dest region for 3
  cycles (hardware partially enforces this by stalling on follow-up
  `MOVD2A`, `MOVD2B`, `ELWMUL`, `MVMUL`, etc.).
- Data format: reverse of `MOVD2A`; removes low mantissa (BF16/TF32) or high
  exponent bits (FP16) to produce Dest's 16-bit format.

### 4.4 MOVB2D — SrcB → Dest

Copies 1, 4, or 8 rows from the active SrcB bank into Dest, with optional
column-0 broadcast or row broadcast.

```c
TT_MOVB2D(/* bool */ UseDst32bLo,
          /* u6  */ SrcRow,
          /* u2  */ AddrMod,
        ((/* bool */ Move4Rows)        << 2) +
        ((/* bool */ Broadcast1RowTo8) << 1) +
          /* bool */ BroadcastCol0,
          /* u10 */ DstRow)
```

- `Broadcast1RowTo8=1`: one SrcB row is replicated into 8 consecutive Dest
  rows (DstRow aligned to 8).
- `BroadcastCol0=1`: column 0 of each SrcB row is replicated across all 16
  columns of the corresponding Dest row.
- **Waits** at Wait Gate for `SrcB[MatrixUnit.SrcBBank].AllowedClient == MatrixUnit`.
- After `MOVB2D`, avoid reading the written Dest region for 3 cycles.
- Data format: same `ALU_FORMAT_SPEC_REG0_SrcA`-driven conversion as `MOVD2B`.

### 4.5 MOVB2A — SrcB → SrcA

Copies 1 or 4 aligned rows from the active SrcB bank into the active SrcA
bank.

```c
TT_MOVB2A(/* u6 */ SrcARow,
          /* u2 */ AddrMod,
         (/* bool */ Move4Rows) << 1,
          /* u6 */ SrcBRow)
```

- **Waits** at Wait Gate for `SrcB[MatrixUnit.SrcBBank].AllowedClient == MatrixUnit`.
- **Does not automatically wait** for SrcA bank validity.
- After `MOVB2A`, the next cycle only accepts `MOVD2A` or `MOVB2A`.

---

## 5. Ownership Model Across Threads

The three Tensix threads have dedicated roles:

| Thread | RISC-V core | Primary role | Register files owned |
|--------|-------------|-------------|---------------------|
| T0 | TRISC0 | Unpack | Writes SrcA (via Unpacker 0), writes SrcB (via Unpacker 1) |
| T1 | TRISC1 | Math | Reads SrcA, reads SrcB, writes Dest |
| T2 | TRISC2 | Pack | Reads Dest |

### 5.1 SrcA/SrcB Ownership Flow

```
T0 thread:
  UNPACR (WhichUnpacker=0) → writes SrcA[Unpackers[0].SrcBank]
  UNPACR_NOP (0x7, WhichUnpacker=0) → flips SrcA bank to MatrixUnit ownership
  (Similarly for SrcB using WhichUnpacker=1)

T1 thread:
  STALLWAIT(STALL_MATH, SRCA_VLD) → wait until SrcA is owned by MatrixUnit
  STALLWAIT(STALL_MATH, SRCB_VLD) → wait until SrcB is owned by MatrixUnit
  MVMUL / ELWADD / etc. → consume SrcA and SrcB, write Dest
  MVMUL with FlipSrcA/FlipSrcB → return consumed bank to Unpackers, flip to other bank
```

### 5.2 Dest Ownership Flow (MATH_PACK Semaphore)

Dest ownership between T1 (math) and T2 (pack) is coordinated by the
**MATH_PACK** semaphore (index 1). The semaphore acts as a **token counter**:
one token = one half-Dest's worth of math results ready to be packed.

```
SyncHalf initialization:
  SEMINIT(max=2, val=0, sem=MATH_PACK)
  dest_offset_id = 0

T1 (math) per tile:
  SEMWAIT(MATH_PACK, STALL_ON_MAX)   ← block if both halves are full
  ... compute into current half (dest_offset_id) ...
  SEMPOST(MATH_PACK)                 ← signal: one half ready to pack
  update_dest_offset_id()            ← flip dest_offset_id (0→1 or 1→0)
  SETC16(DEST_TARGET_REG_CFG_MATH_Offset, new_base)  ← point to new half

T2 (pack) per tile:
  SEMWAIT(MATH_PACK, STALL_ON_ZERO)  ← block if no half is ready
  PACR ...                            ← read and pack a half
  ZEROACC(CLR_HALF, dest_offset_id)  ← invalidate rows in packed half
  SEMGET(MATH_PACK)                   ← release token; signal math can write here again
  flip_packer_dest_offset_id()       ← advance to the other half
```

In **SyncFull** mode, `SEMINIT(max=1, val=0)` is used and the full Dest is
treated as a single unit. Math waits for the semaphore to be 0 (not at max),
packs the whole Dest, then SEMGET releases it.

### 5.3 Other Relevant Semaphores

**UNPACK_OPERAND_SYNC** (index 3): coordinates between T0 (unpack) and T1
(math) on operand tile lifecycle. T1 calls `SEMGET(UNPACK_OPERAND_SYNC)` after
consuming a tile's SrcA/SrcB banks (via `_llk_math_release_tile_()`), which
releases the operand slot for T0 to refill.

**UNPACK_TO_DEST** (index 2): used when Unpacker 0 writes directly to Dest
(bypassing SrcA) for certain operations. T0 posts to this semaphore when the
unpack-to-dest write completes; T1 waits on it before reading from Dest.

**MATH_DONE** (index 7): used when unpacking directly to Dest; signals T1 to
proceed with SFPU computation.

Full semaphore table (from `ckernel_structs.h`):

| Index | Name | Direction |
|------:|------|-----------|
| 0 | `FPU_SFPU` | FPU ↔ SFPU sync |
| 1 | `MATH_PACK` | T1 math → T2 pack; Dest ownership |
| 2 | `UNPACK_TO_DEST` | T0 unpack → T1 math; unpack-to-dest completion |
| 3 | `UNPACK_OPERAND_SYNC` | T0 unpack ↔ T1 math; operand get/release |
| 4 | `PACK_DONE` | T2 pack iteration start/end; perf events |
| 5 | `UNPACK_SYNC` | TRISC ↔ unpack; HW kernel sync |
| 6 | `UNPACK_MATH_DONE` | Unpack or math iteration done; perf events |
| 7 | `MATH_DONE` | T1 math done; used with unpack-to-dest |

---

## 6. Emulator Implementation Notes

### Dest

Model `DstBits[1024][16]` as a flat `u16` array and `DstRowValid[1024]` as a
`bool` array. Track `dest_offset_id` (0 or 1) as a per-tile-state variable
shared between the math and pack thread contexts.

ZEROACC clears `DstRowValid` bits (not `DstBits`). Packers read zeros from
invalid rows. Matrix Unit reads identity elements from invalid rows and then
marks them valid.

The debug window at `0xFFBD8000` is a 32 KiB view directly into `DstBits`,
with optional bit-layout swizzling on load/store controlled by per-thread
`RISC_DEST_ACCESS_CTRL_SEC.fmt` and `.no_swizzle`.

### SrcA / SrcB

Model each as two banks of `u32` (or packed u19 for exact fidelity) arrays
`[64][16]`. Track four `AllowedClient` bits (2 for SrcA, 2 for SrcB) and
four bank index bits (MatrixUnit.SrcABank, MatrixUnit.SrcBBank,
Unpackers[0].SrcBank, Unpackers[1].SrcBank).

For bank-ownership checks: `STALLWAIT` conditions C5–C8 map directly to the
four `AllowedClient` states. Instructions that `wait at Wait Gate` (MOVA2D,
MOVB2D, MOVB2A, MVMUL, etc.) spin until the relevant bank is owned by
MatrixUnit.

ZEROSRC (`TT_ZEROSRC` opcode 0x11) zeros one or both SrcA/SrcB banks by
writing the `zero_val` pattern (typically 0) to all cells in the specified
bank. `src_mask` bits: bit 0 = SrcA, bit 1 = SrcB.

TRNSPSRCB operates on `SrcB[MatrixUnit.SrcBBank].Rows[16..31]` in place.

---

## Source References

| File | Purpose |
|------|---------|
| `tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/Dst.md` | Authoritative Dest spec: storage, types, bit layouts, Adj16/Adj32, RISCV debug window |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/SrcASrcB.md` | Authoritative SrcA/SrcB spec (Wormhole; Blackhole is identical for these register files) |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/ZEROACC.md` | ZEROACC functional model and mode constants |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/MOVD2A.md` | MOVD2A functional model and shuffle functions |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/MOVD2B.md` | MOVD2B functional model |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/MOVA2D.md` | MOVA2D functional model |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/MOVB2D.md` | MOVB2D functional model including broadcast modes |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/MOVB2A.md` | MOVB2A functional model |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/MVMUL.md` | MVMUL including FlipSrcA/FlipSrcB bank-flip behavior |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/SETDVALID.md` | SETDVALID: give SrcA/SrcB to Matrix Unit |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/CLEARDVALID.md` | CLEARDVALID: give SrcA/SrcB to Unpackers |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/TRNSPSRCB.md` | TRNSPSRCB: SrcB rows 16–31 transpose |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/UNPACR_NOP_SETDVALID.md` | UNPACR_NOP SETDVALID variant |
| `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/Unpackers/README.md` | Unpacker pipeline overview |
| `tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/STALLWAIT.md` | STALLWAIT condition codes C5–C8 for SrcA/SrcB ownership |
| `tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/BackendConfiguration.md` | Config register space; RISC_DEST_ACCESS_CTRL_SEC |
| `tt-llk/tt_llk_blackhole/common/inc/ckernel_structs.h` | Semaphore index constants; MATH_HALF_DEST_SIZE |
| `tt-llk/tt_llk_blackhole/common/inc/ckernel_defs.h` | FACE_HEIGHT/WIDTH, TILE_HEIGHT/WIDTH, DEST_NUM_TILES_FP16 |
| `tt-llk/tt_llk_blackhole/common/inc/cmath_common.h` | wait_math_semaphores, set_math_semaphores, dest_section_flip |
| `tt-llk/tt_llk_blackhole/common/inc/cpack_common.h` | flip_packer_dest_offset_id, select_packer_dest_registers |
| `tt-llk/tt_llk_blackhole/common/inc/ckernel_instr_params.h` | SRCA_VLD, SRCB_VLD, SRCB_ROW16_OFFSET constants |
| `tt-llk/tt_llk_blackhole/llk_lib/llk_math_common.h` | _llk_math_pack_sync_init_, _llk_math_dest_section_done_ |
| `tt-llk/tt_llk_blackhole/llk_lib/llk_pack_common.h` | _llk_packer_wait_for_math_done_, _llk_pack_dest_section_done_ |
| `tt-llk/tt_llk_blackhole/llk_lib/llk_defs.h` | DstSync enum (SyncHalf, SyncFull) |
| `blackhole-py/tt-metal-deps/include/.../tensix_types.h` | DEST_REGISTER_FULL_SIZE, DEST_REGISTER_HALF_SIZE, DEST_FACE_WIDTH/HEIGHT |
| `blackhole-py/dsl.py` | ZEROACC, MOVD2A, MOVD2B, MOVB2D, CLEARDVALID, ZEROSRC field encodings |
| `tt-metal/tt_metal/hw/inc/api/debug/dprint_tensix.h` | Debug window usage at 0xFFBD8000 |
