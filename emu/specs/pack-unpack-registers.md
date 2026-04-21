# Pack/Unpack Configuration Registers

## Overview

All pack/unpack configuration lives in the **Tensix Config Register space**, a dedicated register file separate from L1 and MMIO. It is accessed via direct pointer writes during init or via Tensix instructions (WRCFG, RMWCIB, SETC16) during kernel execution.

```
TENSIX_CFG_BASE = 0xFFEF0000
```

The space supports **two config states** (double-buffered ping-pong). State 0 starts at the base; state 1 starts at `base + CFG_STATE_SIZE * 16` (offset +896 bytes, since `CFG_STATE_SIZE = 56`). All register positions are given as **ADDR32** — a 32-bit word index from the state base.

Source: `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/tensix.h`, `cfg_defines.h`

## DataFormat Enum

From `tensix_types.h:213`. Hardware encodes only the bottom 4 bits (`DATA_FORMAT_BIT_COUNT = 4`, mask `0xF`).

| Value | Name | Notes |
|------:|------|-------|
| 0 | Float32 | |
| 1 | Float16 | IEEE FP16 |
| 2 | Bfp8 | Block FP, 8-bit mantissa, format A exponent |
| 3 | Bfp4 | Block FP, 4-bit mantissa, format A exponent |
| 4 | Tf32 | TensorFloat-32 |
| 5 | Float16_b | BFloat16 |
| 6 | Bfp8_b | Block FP, 8-bit mantissa, format B exponent |
| 7 | Bfp4_b | Block FP, 4-bit mantissa, format B exponent |
| 8 | Int32 | |
| 9 | UInt16 | |
| 10 | Lf8 | FP8 E5M2 |
| 11 | Bfp2 | Block FP, 2-bit mantissa, format A exponent |
| 14 | Int8 | |
| 15 | Bfp2_b | Block FP, 2-bit mantissa, format B exponent |
| 24 | UInt32 | |
| 26 | Fp8_e4m3 | SW alias for Lf8 with `Pac_LF8_4b_exp`/`Unp_LF8_4b_exp` mode bit set |
| 30 | UInt8 | |
| 0xFF | Invalid | |

Fp8_e4m3 is encoded as Lf8 (value 10) in the 4-bit register field, with a separate mode bit to select E4M3 vs E5M2.

## 1. Packer Registers

### 1.1 Pack Config (THCON_SEC0_REG1) — ADDR32 68–71

Struct: `pack_config_t` in `tt_llk_blackhole/common/inc/cpack_common.h:27–64`. Written as 4 consecutive 32-bit words. A second packer context lives at THCON_SEC0_REG8 (ADDR32 96–99).

**Word 0 (ADDR32 68):**

| Bits | Field | Description |
|------|-------|-------------|
| [15:0] | `row_ptr_section_size` | BFP tile row pointer section size |
| [31:16] | `exp_section_size` | Exponent section size (num_faces for BFP, 0 for Lf8/Int8) |

**Word 1 (ADDR32 69):**

| Bits | Field | Description |
|------|-------|-------------|
| [31:0] | `l1_dest_addr` | L1 destination address for pack output (16-byte aligned) |

**Word 2 (ADDR32 70):**

| Bits | Field | Description |
|------|-------|-------------|
| [0] | `uncompress` | 1 = uncompressed output |
| [1] | `add_l1_dest_addr_offset` | Add dest addr offset on each tile |
| [2] | `disable_pack_zero_flag` | Disable zero flag generation (for L1 acc) |
| [7:4] | **`out_data_format`** | Output data format (4-bit DataFormat) |
| [11:8] | **`in_data_format`** | Input (source/Dest register) format (4-bit DataFormat) |
| [12] | `dis_shared_exp_assembler` | Disable shared exponent assembly for BFP |
| [13] | `auto_set_last_pacr_intf_sel` | Auto-set last packer interface select |
| [14] | `enable_out_fifo` | Enable output FIFO |
| [15] | `sub_l1_tile_header_size` | Subtract tile header size from addresses |
| [16] | `src_if_sel` | Source interface select (0=SrcA, 1=SrcB) |
| [20:17] | `pack_start_intf_pos` | Start interface position |
| [21] | `all_pack_disable_zero_compress_ovrd` | Override: disable z-compress for all packers |
| [22] | `add_tile_header_size` | Prepend 16B tile header to output |
| [23] | `pack_dis_y_pos_start_offset` | Disable Y position start offset |
| [31:24] | `l1_src_addr` | L1 source address (upper bits) |

**Word 3 (ADDR32 71):**

| Bits | Field | Description |
|------|-------|-------------|
| [19] | `Pack_L1_Acc` | Enable L1 accumulation mode |
| [20] | `Exp_threshold_en` | Enable exponent thresholding |
| [22] | `Unp_LF8_4b_exp` | FP8 E4M3 mode for unpacker 0 (shared register) |
| [23] | `Pac_LF8_4b_exp` | FP8 E4M3 mode for packer |
| [31:24] | `Exp_threshold` | Exponent threshold value (e.g. 113 for FP32->BFP-A) |

### 1.2 Dest Read Control (PCK_DEST_RD_CTRL) — ADDR32 18

Controls how the packer reads values from the Dest accumulator register.

| Bits | Field | Description |
|------|-------|-------------|
| [0] | `Read_32b_data` | Read 32-bit from Dest (Float32/Int32/UInt32, or FP32 dest mode) |
| [1] | `Read_unsigned` | Treat data as unsigned (UInt8 output) |
| [2] | `Read_int8` | Read as 8-bit integer from Dest |
| [3] | `Round_10b_mant` | Round to 10-bit mantissa (FP32->FP16, or FP8-E4M3 output) |

### 1.3 ReLU (STACC_RELU) — ADDR32 2

Shares a register with `ALU_ACC_CTRL_Zero_Flag_*`.

| Bits | Field | Description |
|------|-------|-------------|
| [0] | `Zero_Flag_disabled_src` | Disable zero flagging for source |
| [1] | `Zero_Flag_disabled_dst` | Disable zero flagging for dest |
| [5:2] | **`ApplyRelu`** | 0=off, 1=ReLU, 2=threshold min, 3=threshold max |
| [21:6] | **`ReluThreshold`** | 16-bit threshold value in BF16 format |

### 1.4 Pack Counters (PACK_COUNTERS_SEC0) — ADDR32 28

| Bits | Field | Description |
|------|-------|-------------|
| [7:0] | `pack_per_xy_plane` | Packs per XY plane |
| [15:8] | `pack_reads_per_xy_plane` | Reads per XY plane |
| [22:16] | `pack_xys_per_tile` | XY planes per tile |
| [23] | `pack_yz_transposed` | YZ transpose flag |
| [31:24] | `auto_ctxt_inc_xys_cnt` | Auto context increment XYs count |

### 1.5 Edge Masking — ADDR32 24–27

For partial tile packing. Four edge offset registers (`PCK_EDGE_OFFSET_SEC[0:3]`), each holding a 16-bit mask in the lower half. `TILE_ROW_SET_MAPPING[0:3]` (ADDR32 20–23) map each face row (16 rows x 2 bits = 32 bits per register) to one of the 4 edge offset masks.

| Register | ADDR32 | Content |
|----------|--------|---------|
| `PCK_EDGE_OFFSET_SEC0` | 24 | mask[15:0], mode[16], tile_row_set_select_pack[25:17] |
| `PCK_EDGE_OFFSET_SEC1` | 25 | mask[15:0] |
| `PCK_EDGE_OFFSET_SEC2` | 26 | mask[15:0] |
| `PCK_EDGE_OFFSET_SEC3` | 27 | mask[15:0] |
| `TILE_ROW_SET_MAPPING0` | 20 | 16 rows x 2-bit mapping |
| `TILE_ROW_SET_MAPPING1` | 21 | 16 rows x 2-bit mapping |
| `TILE_ROW_SET_MAPPING2` | 22 | 16 rows x 2-bit mapping |
| `TILE_ROW_SET_MAPPING3` | 23 | 16 rows x 2-bit mapping |

### 1.6 Packer Address Strides — ADDR32 12–17

| Register | ADDR32 | Content |
|----------|--------|---------|
| `PCK0_ADDR_CTRL_XY_REG_0` | 12 | X-stride [15:0], Y-stride [31:16] |
| `PCK0_ADDR_CTRL_ZW_REG_0` | 13 | Z-stride [15:0], W-stride [31:16] |
| `PCK0_ADDR_CTRL_XY_REG_1` | 14 | Channel 1 X/Y strides |
| `PCK0_ADDR_CTRL_ZW_REG_1` | 15 | Channel 1 Z/W strides |
| `PCK0_ADDR_BASE_REG_0` | 16 | Base address register 0 |
| `PCK0_ADDR_BASE_REG_1` | 17 | Base address register 1 |

### 1.7 Dest Target (DEST_TARGET_REG_CFG_PACK_SEC) — ADDR32 180–183

Packer dest register offset and Z-offset for each of 4 packer sections (selects which half of Dest to read from).


## 2. Unpacker Registers

### 2.1 Tile Descriptor (THCON_SEC0/1_REG0) — ADDR32 64–67 / 112–115

Struct: `unpack_tile_descriptor_t` in `tt_llk_blackhole/common/inc/cunpack_common.h:20–88`. Unpacker 0 (SrcA) at ADDR32 64–67, Unpacker 1 (SrcB) at ADDR32 112–115.

**Word 0 (ADDR32 64 / 112):**

| Bits | Field | Description |
|------|-------|-------------|
| [3:0] | **`in_data_format`** | Input tile data format (4-bit DataFormat) |
| [4] | `uncompressed` | 1 = tile is uncompressed (no zero-compress) |
| [11:8] | `blobs_per_xy_plane` | BFP metadata blobs per XY plane |
| [31:16] | `x_dim` | Tile X dimension (face_width x face_count) |

**Word 1 (ADDR32 65 / 113):**

| Bits | Field | Description |
|------|-------|-------------|
| [15:0] | `y_dim` | Tile Y dimension |
| [31:16] | `z_dim` | Z dimension (number of faces: 1, 2, or 4) |

**Word 2 (ADDR32 66 / 114):**

| Bits | Field | Description |
|------|-------|-------------|
| [15:0] | `w_dim` | W dimension |
| [31:16] | `blobs_y_start_lo` | BFP blob start Y (low 16 bits) |

**Word 3 (ADDR32 67 / 115):**

| Bits | Field | Description |
|------|-------|-------------|
| [15:0] | `blobs_y_start_hi` | BFP blob start Y (high 16 bits) |

### 2.2 Unpack Config (THCON_SEC0/1_REG2) — ADDR32 72–75 / 120–123

Struct: `unpack_config_t`.

**Word 0 (ADDR32 72 / 120):**

| Bits | Field | Description |
|------|-------|-------------|
| [3:0] | **`out_data_format`** | Output format (format in srcA/srcB register file) |
| [5:4] | `throttle_mode` | Throttle mode (default=2) |
| [7:6] | `context_count` | Number of double-buffered contexts |
| [8] | `haloize_mode` | XY transpose mode |
| [9] | `tileize_mode` | Tilize mode (row-major -> tile layout) |
| [10] | `unpack_src_reg_set_upd` | Update source register set |
| [11] | `unpack_if_sel` | Unpack interface select |
| [13:12] | `upsample_rate` | Upsampling rate |
| [15] | `upsample_and_interleave` | Upsample + interleave mode |
| [31:16] | `shift_amount` | Shift amount |

**Word 1 (ADDR32 73 / 121):**

| Bits | Field | Description |
|------|-------|-------------|
| [3:0] | `uncompress_cntx0_3` | Per-context uncompress flags (contexts 0-3) |
| [7:4] | `unpack_if_sel_cntx0_3` | Per-context interface select (0-3) |
| [8] | `force_shared_exp` | Force shared exponent mode |
| [19:16] | `uncompress_cntx4_7` | Per-context uncompress flags (contexts 4-7) |
| [23:20] | `unpack_if_sel_cntx4_7` | Per-context interface select (4-7) |

**Word 2 (ADDR32 74 / 122):**

| Bits | Field | Description |
|------|-------|-------------|
| [16:0] | `limit_addr` | L1 FIFO limit address |

**Word 3 (ADDR32 75 / 123):**

| Bits | Field | Description |
|------|-------|-------------|
| [16:0] | `fifo_size` | L1 FIFO size |

### 2.3 L1 Base Address (THCON_SEC0/1_REG3)

| Register | ADDR32 | Description |
|----------|--------|-------------|
| `THCON_SEC0_REG3_Base_address` | (REG3 base) | Unp0 tile L1 base address, context 0 |
| `THCON_SEC0_REG3_Base_cntx1_address` | (REG3 base+1) | Unp0 tile L1 base address, context 1 |
| `THCON_SEC1_REG3_Base_address` | (SEC1 equivalent) | Unp1 tile L1 base address |

Written per-tile before issuing UNPACR.

### 2.4 Per-Context Dest Address (THCON_SEC0_REG5) — ADDR32 84–87

| ADDR32 | Content |
|--------|---------|
| 84 | `Dest_cntx0_address` [15:0], `Dest_cntx1_address` [31:16] |
| 85 | `Dest_cntx2_address` [15:0], `Dest_cntx3_address` [31:16] |
| 86 | `Tile_x_dim_cntx0` [15:0], `Tile_x_dim_cntx1` [31:16] |
| 87 | `Tile_x_dim_cntx2` [15:0], `Tile_x_dim_cntx3` [31:16] |

### 2.5 Per-Context Format Override (THCON_SEC0_REG7) — ADDR32 92–93

| ADDR32 | Bits | Field | Description |
|--------|------|-------|-------------|
| 92 | [15:0] | `Offset_address` | Tile offset (context 0) |
| 92 | [19:16] | `Unpack_data_format_cntx0` | Per-context input format override |
| 92 | [23:20] | `Unpack_out_data_format_cntx0` | Per-context output format override |
| 92 | [27:24] | `Unpack_data_format_cntx4` | Context 4 input format override |
| 92 | [31:28] | `Unpack_out_data_format_cntx4` | Context 4 output format override |
| 93 | [15:0] | `Offset_cntx1_address` | Tile offset (context 1) |

### 2.6 Unpacker Address Strides — ADDR32 44–50, 60–62

| Register | ADDR32 | Description |
|----------|--------|-------------|
| `UNP0_ADDR_CTRL_XY_REG_0` | 44 | Unp0 X/Y stride (channel 0) |
| `UNP0_ADDR_CTRL_ZW_REG_0` | 45 | Unp0 Z/W stride (channel 0) |
| `UNP1_ADDR_CTRL_XY_REG_0` | 46 | Unp1 X/Y stride |
| `UNP1_ADDR_CTRL_ZW_REG_0` | 47 | Unp1 Z/W stride |
| `UNP0_ADDR_BASE_REG_0` | 48 | Unp0 base address reg 0 |
| `UNP0_ADDR_BASE_REG_1` | 49 | Unp0 base address reg 1 |
| `UNP0_ADD_DEST_ADDR_CNTR` | 50 | [8]: Enable adding dest address counter |
| `UNP1_ADDR_BASE_REG_0` | 60 | Unp1 base address reg 0 |
| `UNP1_ADDR_BASE_REG_1` | 61 | Unp1 base address reg 1 |
| `UNP1_ADD_DEST_ADDR_CNTR` | 62 | Unp1 dest address counter enable |

### 2.7 Unpack Misc Config — ADDR32 41

Controls double-buffered config context switching.

| Bits | Field | Description |
|------|-------|-------------|
| [3:0] | `CfgContextOffset_0` | Offset to context 0 config block |
| [4] | `CfgContextCntReset_0` | Reset context counter 0 |
| [5] | `CfgContextCntInc_0` | Increment context counter 0 |
| [11:8] | `CfgContextOffset_1` | Offset to context 1 config block |


## 3. ALU Format / Stochastic Rounding — ADDR32 0–2

Written by the unpack thread (TRISC0) but affects all of pack/unpack/math.

**ADDR32 0 — ALU_FORMAT_SPEC override values:**

| Bits | Field | Description |
|------|-------|-------------|
| [3:0] | `SrcA_val` | SrcA format value (auto-inferred from tile) |
| [8:5] | `SrcB_val` | SrcB format value |
| [13:10] | `Dstacc_val` | Dest accumulator format value |

**ADDR32 1 — ALU_FORMAT_SPEC + ALU_ROUNDING_MODE + ALU_ACC_CTRL (packed):**

| Bits | Field | Description |
|------|-------|-------------|
| [0] | `Fpu_srnd_en` | FPU stochastic rounding enable |
| [1] | `Gasket_srnd_en` | Gasket (pre-packer) stochastic rounding |
| [2] | `Packer_srnd_en` | Packer stochastic rounding |
| [13] | `GS_LF` | Gasket LF8 mode |
| [14] | `Bfp8_HF` | BFP8 high-fidelity mode |
| [15] | `SrcAUnsigned` | SrcA is unsigned |
| [16] | `SrcBUnsigned` | SrcB is unsigned |
| [20:17] | `SrcA` | SrcA format (4 bits) |
| [24:21] | `SrcB` | SrcB format (4 bits) |
| [28:25] | `Dstacc` | Dest accumulator format (4 bits) |
| [29] | `Fp32_enabled` | FP32 dest accumulation mode |
| [30] | `SFPU_Fp32_enabled` | SFPU reads FP32 from dest |
| [31] | `INT8_math_enabled` | INT8 math mode |

**ADDR32 2 — STACC_RELU + Zero Flags:**

See section 1.3 above.


## 4. How Firmware Writes Config Registers

All mechanisms target the config space at `TENSIX_CFG_BASE`. Firmware code accesses it via `get_cfg_pointer()` which returns a `volatile uint32_t*` to the base.

### 4.1 Direct Pointer Write (initialization)

```cpp
volatile uint32_t *cfg = get_cfg_pointer();
cfg[THCON_SEC0_REG0_TileDescriptor_ADDR32 + 0] = tile_descriptor.val[0];
cfg[THCON_SEC0_REG0_TileDescriptor_ADDR32 + 1] = tile_descriptor.val[1];
// ...
```

Used during `configure_unpack_AB()` and `configure_pack()` at kernel init.

### 4.2 WRCFG (write 32-bit or 128-bit from GPR to config)

Opcode `0xB0`. Format: `GprAddress[7:0] | wr128b[15] | CfgReg[14:0]`.

```cpp
TTI_STALLWAIT(p_stall::STALL_CFG, p_stall::THCON);
TTI_WRCFG(p_gpr_pack::TMP0, p_cfg::WRCFG_32b, STACC_RELU_ApplyRelu_ADDR32);
TTI_NOP; TTI_NOP;  // 2 NOPs required after WRCFG
```

### 4.3 RMWCIB0/1/2/3 (read-modify-write individual bytes)

Opcodes `0xB3–0xB6` for bytes 0–3. Used for sub-word bitfield modifications without disturbing surrounding bits.

```cpp
// cfg_reg_rmw_tensix<ADDR32, SHAMT, MASK>(val) decomposes to:
TT_RMWCIB0(mask_b0, data_b0, CfgAddr32);
TT_RMWCIB1(mask_b1, data_b1, CfgAddr32);
TT_RMWCIB2(mask_b2, data_b2, CfgAddr32);
TT_RMWCIB3(mask_b3, data_b3, CfgAddr32);
```

### 4.4 SETC16 (16-bit write to config register)

Opcode `0xB2`.

```cpp
TTI_SETC16(UNPACK_MISC_CFG_CfgContextOffset_0_ADDR32, 0x0101);
```

### 4.5 Sequencing: STALLWAIT

All config writes affecting packer/unpacker hardware must be preceded by a STALLWAIT to avoid races:

```cpp
TTI_STALLWAIT(p_stall::STALL_CFG, p_stall::THCON);   // before THCON (pack/unpack) config
TTI_STALLWAIT(p_stall::STALL_CFG, p_stall::PACK);     // before ReLU, edge mask config
TTI_STALLWAIT(p_stall::STALL_CFG, p_stall::UNPACK0);  // before unpack reconfig
```


## 5. Blackhole-Specific Notes

From `cpack_common.h:51–61`:

- **Word 3 of pack config** (ADDR32 71) was restructured vs Wormhole: `Pack_L1_Acc`, `Exp_threshold_en`, `Unp_LF8_4b_exp`, `Pac_LF8_4b_exp`, and `Exp_threshold` moved here to avoid a race condition between unpack and pack threads sharing these fields.
- Only **1 packer** is active in the Blackhole LLK (`NUM_PACKERS = 1`), compared to up to 4 in hardware.
- Packer `x_start/x_end` must be within 1 row (0 to `FACE_C_DIM-1 = 15`). Set via `TTI_SETADCXX(p_setadc::PAC, FACE_C_DIM-1, 0x0)`.
- FP8 E4M3 support uses `Unp_LF8_4b_exp` / `Pac_LF8_4b_exp` bits at ADDR32 71.


## Key Source Files

| File | Content |
|------|---------|
| `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/cfg_defines.h` | Master register map — all ADDR32/SHAMT/MASK definitions |
| `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/tensix.h` | Address map (TENSIX_CFG_BASE, TDMA, debug) |
| `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/tensix_types.h` | DataFormat enum, ReLU modes, stochastic rounding enum |
| `tt_llk_blackhole/common/inc/cpack_common.h` | `pack_config_t`, ReLU config, dest_rd_ctrl, configure_pack |
| `tt_llk_blackhole/common/inc/cunpack_common.h` | `unpack_tile_descriptor_t`, `unpack_config_t`, `configure_unpack_AB` |
| `tt_llk_blackhole/common/inc/ckernel.h` | `cfg_reg_rmw_tensix`, `cfg_write`, `get_cfg_pointer` |
| `tt_llk_blackhole/common/inc/ckernel_ops.h` | WRCFG, RMWCIB0-3, SETC16 instruction encoding macros |
| `tt_llk_blackhole/llk_lib/llk_pack_common.h` | High-level pack LLK (ReLU, L1 acc, edge masks) |
| `tt_llk_blackhole/llk_lib/llk_unpack_common.h` | High-level unpack LLK (stochastic rounding, reconfig) |
