# pack-unpack-registers

**Source:** [`pack-unpack-registers.md`](../specs/pack-unpack-registers.md) · **Emulator:** `blackhole-py/extra/emu/tensix/`

## DataFormat enum

### `PUKREG.FMT.FLOAT32`
§DataFormat Enum / 0

> DataFormat 0 = Float32 (IEEE FP32).

### `PUKREG.FMT.FLOAT16`
§DataFormat Enum / 1

> DataFormat 1 = Float16 (IEEE FP16).

### `PUKREG.FMT.BFP8`
§DataFormat Enum / 2

> DataFormat 2 = Bfp8 (block FP, 8-bit mantissa, format A exponent).

### `PUKREG.FMT.TF32`
§DataFormat Enum / 4

> DataFormat 4 = Tf32 (TensorFloat-32).

### `PUKREG.FMT.FLOAT16B`
§DataFormat Enum / 5

> DataFormat 5 = Float16_b (BFloat16).

### `PUKREG.FMT.INT32`
§DataFormat Enum / 8

> DataFormat 8 = Int32 (sign-magnitude 32-bit).

### `PUKREG.FMT.INT8`
§DataFormat Enum / 14

> DataFormat 14 = Int8 (sign-magnitude 8-bit).

### `PUKREG.FMT.LF8_DUAL_MODE`
§DataFormat Enum / 10

> DataFormat 10 = Lf8: encodes two FP8 formats depending on the Pac_LF8_4b_exp / Unp_LF8_4b_exp mode bit. 0=E5M2, 1=E4M3.

## Pack config

### `PUKREG.PACK_CFG.OUT_DATA_FORMAT`
§1.1 Pack Config / Word 2 bits[7:4]

> out_data_format [bits 7:4 of ADDR32 70 word 2]: 4-bit DataFormat for L1 output.

### `PUKREG.PACK_CFG.IN_DATA_FORMAT`
§1.1 Pack Config / Word 2 bits[11:8]

> in_data_format [bits 11:8 of ADDR32 70 word 2]: 4-bit DataFormat for Dest register input.

### `PUKREG.PACK_CFG.L1_DEST_ADDR`
§1.1 Pack Config / Word 1

> l1_dest_addr [ADDR32 69]: L1 destination address for pack output (must be 16-byte aligned).

### `PUKREG.PACK_CFG.LF8_4B_EXP`
§1.1 Pack Config / Word 3 bit[23]

> Pac_LF8_4b_exp [bit 23 of ADDR32 71 word 3]: selects E4M3 (1) vs E5M2 (0) FP8 mode for packer.

### `PUKREG.PACK_CFG.PACK_L1_ACC`
§1.1 Pack Config / Word 3 bit[19]

> Pack_L1_Acc [bit 19 of ADDR32 71]: enable L1 accumulation mode for packer.

## Dest read control

### `PUKREG.DEST_RD.READ_32B`
_§1.2 Dest Read Control / Read_32b_data_

> Read_32b_data=1: packer reads 32-bit values from Dest (FP32/INT32 mode).

### `PUKREG.DEST_RD.READ_UNSIGNED`
_§1.2 Dest Read Control / Read_unsigned_

> Read_unsigned=1: treat Dest data as unsigned (for UInt8 output).

## Config space

### `PUKREG.CFG.BASE_ADDRESS`
_§Overview / TENSIX_CFG_BASE_

> Tensix config register space base address: 0xFFEF0000.

### `PUKREG.CFG.DOUBLE_BUFFERED`
§Overview / two config states

> Config space supports two states (double-buffered): state 0 at base, state 1 at base + CFG_STATE_SIZE*16.
