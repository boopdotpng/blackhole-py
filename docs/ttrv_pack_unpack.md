# unpack and pack config fields, measured

Every config field the unpackers and the packer read, measured on Blackhole (p150a, 2026-11-15), with a short name for each.
The [consolidated spec](ttrv_spec.md) has the rules and names; this file has the measurements and the reasons behind them.

decided: the names in §1 replace the spec's `base`, `offset`, `dest`. The compiler derives `exp_size` and the Dst read strides from the formats. The spec exposes plain moves as `unpack.fmt` / `unpack` and `pack.fmt` / `pack` (see §12 below for measurements). Advanced named configuration is still under audit. The short names in §1-6 are candidate API names, not a second normative grammar; native encodings remain backend reference material.

- probes, all in `blackhole-py-old/tests/probes/` (each has a Findings docstring):
  - `probe_unpack_fields.py`: unpack fields, formats, contexts (~1400 cases)
  - `probe_pack_formats.py`: every pack conversion mode, ~95 pack fields x 13 formats, per context copies
  - `probe_unpack_contexts.py`, `probe_pack_fields.py`: the earlier context / BF16 probes
- method: a known tile goes through unpack -> Src -> Dst -> pack, and every result is compared bit for bit with a host model, or with the same run without the field. a field is **dead** only if it changed nothing in every format tried
- formats used for field sweeps: unpack BF16, FP32->BF16, FP32->FP16, BFP8, BFP4, FP8, INT8. pack FP32, BF16 (both ways), BFP8/4/2, FP16, E4M3, INT32, INT8 from 32-bit Dst, and BF16, BF16->BFP8, FP16 from 16-bit Dst
- TF32 (code 4) is left out everywhere: nothing uses it
- a hang means the card needs `tt-smi --eth_train_skip -r N` (~3 s). `Device.boot()`'s soft reset does not clear a wedged Tensix

verdicts:
- **keep**: a real knob, exposed under the name given
- **fixed = X**: the compiler always writes X. writing it is an error
- **dead**: no effect anywhere. hidden, always 0, writing it is an error
- **error**: hangs the card, or is a second way to say something another field says

## 1. names

one name per job, the same on unpack and pack:

| name | unpack | pack | units |
| --- | --- | --- | --- |
| `l1` | `Base_address` (spec: `base`) | `L1_Dest_addr` (old proposal: `dest`) | byte address. compiler writes `(addr >> 4) - 1` |
| `in_fmt`, `out_fmt` | `Unpack_data_format_cntx`, `Unpack_out_data_format_cntx` | `In_data_format`, `Out_data_format` | format code |
| `uncompressed` | `Disable_zero_compress_cntx` | `Disable_zero_compress` | |
| `reg_row` | `Dest_cntx` (spec: `dest`) | `DEST_TARGET_REG_CFG_PACK_SECn_Offset` (old: `dst_row`) | rows of the register file (Src / Dst) |
| `reg_base` | `UNPn_ADDR_BASE_REG_1` | `PCK0_ADDR_BASE_REG_0` | bytes, register-file side |
| `reg_ystride`, `reg_zstride`, `reg_wstride` | `UNPn_ADDR_CTRL_*_REG_1` | `PCK0_ADDR_CTRL_*_REG_0` | bytes, register-file side |
| `e4m3` | `Unp_LF8_4b_exp` | `Pac_LF8_4b_exp` | lf8 is E4M3, not E5M2 |
| `unsigned` | `ALU_FORMAT_SPEC_REG0_SrcA/BUnsigned` | `PCK_DEST_RD_CTRL_Read_unsigned` | int8 is 0..255 |
| `fifo_end`, `fifo_size` | `Unpack_limit_address`, `Unpack_fifo_size` | REG9 `Pack_*_limit_address`, `Pack_*_fifo_size` | **bytes in the language**. hardware: unpack 16 B units, pack 32 B units |

`dest` is not used: on the packer it could mean the L1 destination or Dst. `reg_*` is always the register-file side, `l1*` always L1.

the L1-side strides have no shared name: the unpacker never reads them (dead), the packer's are `l1_*stride`.

## 2. formats

codes: 0 fp32, 1 fp16, 2 bfp8a, 3 bfp4a, 5 bf16, 6 bfp8, 7 bfp4, 8 int32, 9 int16, 10 lf8 (`e4m3` picks E4M3), 11 bfp2a, 14 int8, 15 bfp2. 4 (tf32) is out of scope. 12 and 13 are not formats = error.

### unpack: L1 -> Src / Dst

bit exact against the ISA model, on A and B:

| in_fmt | out_fmt | notes |
| --- | --- | --- |
| fp32 | bf16, fp16 | bf16: denormals flush. fp16: truncate, saturate |
| fp32, int32 | fp32, int32 with `to_dst` (A only) | raw copy to Dst |
| bf16, fp16, int16 | same | |
| lf8 | lf8 | `e4m3` per unpacker |
| int8 | int8 | `unsigned` per unpacker |
| bfp8, bfp4, bfp2 | bf16 | |
| bfp8a, bfp4a, bfp2a | fp16 | incl. BH all-ones / -0 specials. bfp4a specials depend on the throttle |

- same-size pairs don't convert, the bits are taken as `out_fmt` (bf16 <-> fp16 <-> int16, bfp8 / bfp8a / lf8 -> int8) = error
- most other mismatched pairs **hang** = error. the list is `KNOWN_HANG` in `probe_unpack_fields.py`
- the compiler allows only the pairs in the table

### pack: Dst -> L1

`dst32` (`Read_32b_data`) says how Dst is read. on Blackhole `in_fmt` *is* the intermediate format: `ALU_FORMAT_SPEC_REG2_Dstacc` is never read.

| dst32 | in_fmt | out_fmt | notes |
| --- | --- | --- | --- |
| 1 | fp32 | fp32, bf16, fp16, bfp8, bfp4, bfp2 | bf16: truncates, flushes fp32 denormals. fp16 keeps denormals |
| 1 | bf16 | bf16, bfp8, bfp4, bfp2 | rounds to bf16 first (half away from 0). NaN -> Inf, -0 -> +0 |
| 1 | fp16 | fp16, lf8 | `round10` = 1 required (garbage without). lf8 needs `e4m3` = 1 |
| 1 | bfp8 | bfp8, bfp4 | rounds to an 8-bit mantissa first |
| 1 | int32 | int32 | bit copy |
| 1 | int8 | int8 | Dst int32 is sign-magnitude: sign + min(\|v\|, 127). `unsigned`: min(\|v\|, 255). `descale` shifts first |
| 0 | fp16 | fp32, fp16, bf16, lf8 | exact. lf8 + `e4m3` = E4M3: truncate, saturate to 0x7e (448) |
| 0 | bf16 | fp32, bf16, bfp8, bfp4, bfp2 | |
| 0 | bfp8 | bfp8, bfp4 | |
| 0 | lf8 | lf8 | |

- `in_fmt` bfp4, bfp4a, bfp2, bfp2a **hang** in both Dst widths = error
- `out_fmt` only picks a width / block layout, the encoding comes from `in_fmt`. byte-identical outputs, for every `in_fmt`: fp32 = int32 = 12, fp16 = int16. bfpNa = bfpNb unless `in_fmt` is bfp8/bfp8a. so `out_fmt` bfp8a/4a/2a, int16 and 12/13 only ever repeat another row = error
- lf8 and int8 output starts at `l1 + exp_size * 16`: `Out_data_format & 2` reserves an exponent section these formats don't have. `exp_size` must be 0 for them (LLK does the same)
- `l1_acc` is exact (2x) only for fp32, bf16, fp16 output

## 3. unpack per context: `unpack.cfg a|b ctx=N name`

A has contexts 0-7, B has 0-1 (B on 2-7 hangs). ctx c reads copy c unless the copies column says `ctx & 3`.

| name | native | copies | what it does | verdict |
| --- | --- | --- | --- | --- |
| `l1` | `REG3_Base_address`, `REG3_Base_cntx1..3_address`, `REG4_Base_cntx4..7_address` | 8 | L1 tile address. a bfp tile starts with its exponent section | keep |
| `l1_offset` | `REG7_Offset_address`, `REG7_Offset_cntx1..3_address` | 4, ctx & 3 | added to `l1`, 16 B units | keep (spec: `offset`) |
| `in_fmt`, `out_fmt` | `REG7_Unpack_(out_)data_format_cntx0..7` | 8 | only read with `REG2_Ovrd_data_format` = 1 | keep. the compiler fixes Ovrd = 1 |
| `uncompressed` | `REG2_Disable_zero_compress_cntx0..7` | 8 | 0 on plain data **hangs** | fixed = 1 until compressed L1 data is in the language |
| `to_dst` | `REG2_Unpack_if_sel_cntx0..7` | 8, A only | unpack to Dst instead of SrcA | keep (A). error on B |
| `reg_row` | `REG5_Dest_cntx0..3_address` | 4, ctx & 3, A only | first Src / Dst row. hardware value is in datums with SrcA row 0 = 64: `reg_row = r` writes `(r + 4) * 16`. SrcA wraps mod 64 rows | keep (A). B ignores it = error |
| `x_dim` | A: `REG5_Tile_x_dim_cntx0..3`. B: descriptor `XDim` | A: 4, ctx & 3. B: 1 | datums per input row, the face-to-face stride in L1. not the count (that is `SETADCXX`) | keep. the compiler writes whichever field the unpacker reads |
| `col_shift` | `REG2_Shift_amount_cntx0..3` (`tilize` = 0) | 4, ctx & 3, A only | column c lands in c - n, columns < n dropped | keep (A). shares bits with `row_stride`: both = error |
| `fifo_end`, `fifo_size` (ctx 1) | `REG10_Unpack_limit_address`, `_fifo_size`, `_en` | ctx 1 only | same as the shared REG2 pair, only for ctx 1 and only with `_en` | keep as `ctx=1 fifo_*` (sets `_en`) |

## 4. unpack per unpacker: `unpack.cfg a|b name`

| name | native | what it does | formats | verdict |
| --- | --- | --- | --- | --- |
| `e4m3` | A: `THCON_SEC0_REG1_Unp_LF8_4b_exp` (word 71 bit 22). B: `THCON_SEC1_REG1_Unp_LF8_4b_exp` (word 119 bit 22) | lf8 is E4M3. **lives in pack words** (pack ctx 0 and ctx 2), the compiler merges it with pack writes | lf8 | keep |
| `unsigned` | A: `ALU_FORMAT_SPEC_REG0_SrcAUnsigned`. B: `SrcBUnsigned` (math word 1) | int8 is 0..255 | int8 | keep |
| `transpose` | `REG2_Haloize_mode` | transposes each 16x16 face. B ignores it | all | keep (A). error on B |
| `tilize`, `row_stride` | `REG2_Tileize_mode`, `REG2_Shift_amount_cntx0..2` | reads 32-datum rows, `row_stride` bytes apart (multiple of 16, < 64 KiB). works on A and B (ttsim: B unsupported, wrong) | 16/32-bit measured | keep |
| `upsample` | `REG2_Upsample_rate` | 1: a zero after each datum, 2: three zeros | all | keep 0-2. 3 overflows the face = error |
| `upsample_skip` | `REG2_Upsample_and_interleave` | skip instead of writing zeros (not told apart yet) | | keep, unmeasured |
| `shared_exp` | `REG2_Force_shared_exp` + `UNPn_FORCED_SHARED_EXP_shared_exp` | bfp data with no exponent section, every block uses this exponent. also int8 read as bfp8 | bfp*, int8 | keep as one field, absent = off |
| `y_dim`, `z_dim`, `w_dim` | descriptor `YDim`, `ZDim`, `WDim` | `y_dim` multiplies the face stride. `z_dim` 0 = 1. `w_dim` only matters with W stepping (and sizes bfp exponent sections per the ISA) | all | keep |
| `fifo_end`, `fifo_size` | `REG2_Unpack_limit_address`, `REG2_Unpack_fifo_size` | L1 ring: a 16 B word past `fifo_end` moves back by `fifo_size`. `fifo_end` is the last word *inside*. 16 B units. measured on ctx 0-1 (ctx 1 uses REG10 instead when its `_en` is set) | all | keep, bytes in the language |
| `reg_base` | `UNPn_ADDR_BASE_REG_1_Base` | added to the output address, bytes of `out_fmt` | all | keep, or fixed = 0 (`reg_row` covers it on A) |
| `reg_ystride`, `reg_zstride`, `reg_wstride` | `UNPn_ADDR_CTRL_XY/ZW_REG_1_*` | output address step per ADC ch1 Y/Z/W, bytes of `out_fmt` | all | keep |
| `clear_fmt` | `REG2_Out_data_format` | not read by unpacks when Ovrd = 1. it is the format of `UNPACR_NOP` clear-to-one / clear-to-value | NOP clears | keep, or the compiler mirrors ctx 0's `out_fmt` |
| `nop_value` | `UNPn_NOP_REG_CLR_VAL` | `UNPACR_NOP` ClearValue = 3 writes its low 16 bits. dead for unpacks | NOP clears | keep |
| `count` | `REG2_Context_count`, `_non_log2`, `_non_log2_en` | context counter wrap | | as in the spec (`unpack.ctx count=`) |

fixed by the compiler (writing them is an error):

| native | value | why |
| --- | --- | --- |
| `REG2_Ovrd_data_format` | 1 | makes the per-context formats real. descriptor `InDataFormat` is then dead |
| `REG2_Throttle_mode`, `THCON_SEC0_REG1_ovrd_default_throttle_mode` (word 70 bit 3, **one bit for both unpackers, in pack ctx 0's word**) | ovrd = 0 | hardware picks (x8 for 8-bit, else x4), exact in all 12 formats. with ovrd = 1, x8 **hangs** FP32->16-bit, bfp4, bfp4a and drops half the rows of 16-bit inputs. pack writes to word 70 must keep bit 3 = 0 |
| `UNP0_ADD_DEST_ADDR_CNTR` | 1 | makes `reg_row` and the ch1 strides add up (LLK value). B's copy is dead |
| `SRCA_SET_SetOvrdWithAddr` (thread) | 1 for Src, 0 around `to_dst` | the compiler emits it: a `to_dst` context implies 0 |
| `SRCA_SET_Base`, `SRCB_SET_Base`, `REG2_Unpack_Src_Reg_Set_Upd` | 0 | only move SrcRow when the above is 0 |
| descriptor `NoBFPExpSection` (bit 5) | 0 | `shared_exp` covers bfp without exponents |
| descriptor `DigestSize` | 0 | skips `DigestSize * 16` bytes: a second way to say the address |

dead (no effect on A or B in any format):
- `UNPn_ADDR_CTRL_XY/ZW_REG_0_*` (the L1-side strides) and `UNPn_ADDR_BASE_REG_0`: the input address comes only from the descriptor dims and the ADCs
- `reg_xstride` (`UNPn_ADDR_CTRL_XY_REG_1_Xstride`)
- REG6 (the mover's `Source/Destination_address`, `Buffer_size`, `Transfer_direction`, `Metadata_misc`)
- REG10 `Unpacker_Reg_Wr_Addr`, `Packer_Reg_Wr_Addr`. REG11 `Metadata_*`. REG2 `Metadata_x_end`
- `UNP0_BLOBS_Y_START_*`, descriptor `BlobsYStart`, `BlobsPerXYPlane` (only `UNPACR RowSearch`, not in the language)
- `THCON_SEC0/1_REG8_unpack_tile_offset` (named for the unpacker, sits in pack REG8, read by neither)
- descriptor reserved bits, `IsUncompressed`, A's descriptor `XDim`, global `REG2_Unpack_If_Sel` (all overridden in multi-context mode, the only mode the language emits)
- `UNPACK_SCBD_BANK_MASK_32b_Enable` (thread word 10)

## 5. pack per context: `pack.cfg ctx=N name` (N = 0-3)

ctx c reads copy c (`THCON_SEC0_REG1`, `SEC0_REG8`, `SEC1_REG1`, `SEC1_REG8`, and `_SEC0..3` / `PACK_SEC0..3` fields) unless the copies column says otherwise.

| name | native (ctx 0 copy) | copies | what it does | formats | verdict |
| --- | --- | --- | --- | --- | --- |
| `l1` | `THCON_SEC0_REG1_L1_Dest_addr` | 4 | output byte address | all | keep |
| `in_fmt`, `out_fmt` | `In_data_format`, `Out_data_format` | 4 | see §2 | all | keep |
| `uncompressed` | `Disable_zero_compress` | 4 | 0 = zero-compressed output | all | keep, default 1 |
| `exp_size` | `Exp_section_size` | 4 | exponent section, 16 B units. moves the data of every `out_fmt & 2` format | bfp*, lf8, int8 | **derived by the compiler**, writing it is an error: bfp = faces per tile (from the pack shape), lf8 / int8 / others = 0 |
| `skip_exps` | `Dis_shared_exp_assembler` | 4 | the bfp exponent section is not written. mantissas stay where they were | bfp* | keep, default 0 |
| `rsi_size` | `Row_start_section_size` | 4 | row-start index section, 16 B units. only read with `uncompressed` = 0 | compressed | keep |
| `reg_row` | `DEST_TARGET_REG_CFG_PACK_SEC0_Offset` | 4 | first Dst row read (0x10 = one face). also moves the edge-mask start row | all | keep |
| `l1_acc` | `Pack_L1_Acc` | 4 | L1 += packed value | fp32, bf16, fp16 exact | keep. bfp*, lf8 = error. int32, int8: L1 changes but not by integer addition (unverified) |
| `keep_mask` | `Downsample_mask` | 4 | 16-bit mask over datums, repeating. bit 1 = keep, kept datums are compacted | all | keep, 0 = off |
| `exp_min` | `Exp_threshold` + `Exp_threshold_en` | 4 | datums with exponent below it become 0 | float only (int unaffected) | keep as one field, 0 = off |
| `e4m3` | `Pac_LF8_4b_exp` | **2**: ctx 0/1 read `SEC0_REG1`, ctx 2/3 read `SEC1_REG1` | lf8 is E4M3 | lf8 | keep. one field for the pair, like unpack's ctx & 3 fields: `ctx=0 e4m3` and `ctx=1 e4m3` write the same bit, the listing shows it. error if the write changes the value for the other context of the pair while its `out_fmt` is lf8 |
| `edge_row0` | `pack_start_intf_pos` | **2 bits per context in 2 copies**: bits 1:0 = ctx 0 (SEC0_REG1) / ctx 2 (SEC1_REG1), bits 3:2 = ctx 1 (SEC0_REG1) / ctx 3 (SEC1_REG1) | edge-mask start row | edge masks | keep. each context has its own 2 bits, the pair just shares a word: the compiler tracks both halves and always writes the full field |
| `edge_no_reg_row` | `pack_dis_y_pos_start_offset` (REG1 bit 23, REG8 bit 18) | 4 | `reg_row` no longer moves the edge-mask start row | edge masks | keep |
| `edge_rowset` | `PCK_EDGE_TILE_ROW_SET_SELECT_select` bits 2c+1:2c | 4 (in one shared word) | which row-set table (0-3) | edge masks | keep |
| `fifo_end`, `fifo_size` | REG9 `Pack_0_2_*` (SEC0: ctx 0, SEC1: ctx 2), `Pack_1_3_*` (SEC0: ctx 1, SEC1: ctx 3) | 4 | L1 ring, 32 B units | all | keep, bytes in the language |
| `from_l1`, `src_hi` | `Source_interface_selection`, `L1_source_addr` | 4 | read L1 at `src_hi << 18 + reg_base` instead of Dst | all | keep (rare) |
| `plane_rows`, `tile_planes` | `PACK_COUNTERS_SEC0_pack_per_xy_plane`, `pack_xys_per_tile` | 4 | both nonzero: the packer ends the tile by itself every rows x planes Dst rows | all | keep |
| `edge_rows` | `pack_reads_per_xy_plane` | 4 | edge-mask row wrap (ISA) | edge masks | keep, default 1 (no effect without masks) |
| — | `auto_ctxt_inc_xys_cnt` | 4 | nonzero: the PACR context counter stops stepping | | error if nonzero |
| — | `Sub_l1_tile_header_size` | 4 | output at `L1_Dest_addr * 16` instead of `+ 16` | | error: one way to say the address |
| — | `Downsample_rate` | 4 | no effect with a nonzero mask. mask 0 + rate != 0 writes nothing | | error |
| — | `Enable_out_fifo` | 4 | no visible output change, but **hangs** (fp16+round10 -> lf8 in ctx 0, bf16 in ctx 3) | | error |

dead (no effect in any format, 1-3 tiles): `Add_tile_header_size`, `Add_l1_dest_addr_offset` (adds a software-set TDMA register, not used), `Disable_pack_zero_flags`, `Auto_set_last_pacr_intf_sel`, `All_pack_disable_zero_compress_ovrd`, `pack_yz_transposed`, `PACK_CONCAT_MASK_SEC0..3`, `DEST_TARGET_REG_CFG_PACK_SECn_ZOffset`.

not pack fields although they sit in pack words: `ovrd_default_throttle_mode` (word 70 bit 3) and `Unp_LF8_4b_exp` (words 71/119 bit 22) belong to the unpackers (§4), and `unpack_tile_offset` (REG8) is dead.

## 6. pack shared: `pack.cfg name`

| name | native | what it does | formats | verdict |
| --- | --- | --- | --- | --- |
| `dst32` | `PCK_DEST_RD_CTRL_Read_32b_data` | Dst is read as 32-bit words | all | keep |
| `round10` | `Round_10b_mant` | round to a 10-bit mantissa first | in fp16 | 1 for `dst32` + in fp16, else 0. it also changes bf16 output, and breaks the 16-bit fp16 Dst path (output was mostly zeros) |
| `trunc` | `Read_int8` | 32 -> 16-bit narrowing truncates instead of rounding. also used on the int8 path | bf16, fp16, int8 | keep |
| `unsigned` | `Read_unsigned` | int8 output 0..255 | int8 | keep |
| `reg_base` | `PCK0_ADDR_BASE_REG_0_Base` | Dst read offset in bytes (0x100 = datum 64 with 4 B datums) | all | keep (ttsim: "not instantiated", wrong) |
| `reg_ystride`, `reg_zstride`, `reg_wstride` | `PCK0_ADDR_CTRL_XY/ZW_REG_0_*` | Dst read strides in bytes. with x = datum size of `in_fmt` (4/2/1): y = 16x, z = 256x, w = 1024x | all | **derived by the compiler** from `in_fmt`, writing them is an error. `reg_xstride`: dead |
| `l1_base` | `PCK0_ADDR_BASE_REG_1_Base` | added to every context's `l1`, in bytes | all | keep or fixed = 0 (ttsim: "must be 0", wrong) |
| `l1_ystride`, `l1_zstride`, `l1_wstride` | `PCK0_ADDR_CTRL_*_REG_1_*` | L1 write strides. in a plain tile pack only `l1_ystride` changed anything, and only bfp | | default 0. `l1_xstride`: dead |
| `relu`, `relu_thr` | `STACC_RELU_ApplyRelu` (bits 1:0), `ReluThreshold` | 1: negatives -> 0. 2: x <= thr -> 0. 3: clamp at thr and negatives -> 0. every format incl. int | all | keep. ApplyRelu bits 3:2: dead |
| `srnd` | `ALU_ROUNDING_MODE_Packer_srnd_en` | stochastic rounding of bfp mantissas | bfp* | keep |
| `srnd16` | `ALU_ROUNDING_MODE_Gasket_srnd_en` | stochastic rounding of the 32 -> 16-bit step (in bf16, or fp16 + `round10`) | bf16, fp16, lf8 | keep |
| `descale`, `descale_by_face`, `descale0..15` | `INT_DESCALE_Enable`, `_Mode`, `INT_DESCALE_VALUES_SEC0..15` | shift int32 before the int8 conversion | in int8, `dst32` | keep |
| `edge_mask0..3` | `PCK_EDGE_OFFSET_SEC0..3_mask` | 1 bit per Dst column: 1 = keep | all | keep |
| `edge_neginf` | `PCK_EDGE_MODE_mode` | masked datums become -inf (0xff800000, 0xff80) instead of 0 | all | keep |
| `edge_rowmap0..3` | `TILE_ROW_SET_MAPPING_0..3` | per face row: which edge mask (0-3) | all | keep. all 4 work (ttsim models 2) |
| `edge_by_face`, `edge_facemap0..3`, `edge_facesel` | `PCK_EDGE_TILE_FACE_SET_SELECT_enable`, `TILE_FACE_SET_MAPPING_0..3`, `_select` | per face: which row-set table, instead of `edge_rowset` | all | keep. `_1` measured working (ttsim: `_1..3` not instantiated, wrong) |
| `slow_drain` | `PACK_GLOBAL_CFG_CTL_pack_disable_fast_tile_end_drain` | no visible effect. LLK sets it with `l1_acc` | | keep, default 0 |
| — | `ALU_FORMAT_SPEC_REG_Dstacc_override` + `Dstacc_val` | replaces `in_fmt` for every context | all | error: a second way to say `in_fmt` |

no effect on the packer (math fields, or dead): `ALU_FORMAT_SPEC_REG2_Dstacc`, `SrcA/SrcB_override`, `ALU_ACC_CTRL_Fp32_enabled`, `SFPU_Fp32_enabled`, `INT8_math_enabled`, `Zero_Flag_disabled_src/dst`, `Fpu_srnd_en`, `ALU_ROUNDING_MODE_Padding`, `GS_LF`, `Bfp8_HF`.

## 7. fields read by the other engine

the `pack.cfg` / `unpack.cfg` prefix must follow who reads the field, not where `ttrv_cfg.md` puts it:

| field | `ttrv_cfg.md` group | read by |
| --- | --- | --- |
| `THCON_SEC0_REG1_Unp_LF8_4b_exp`, `THCON_SEC1_REG1_Unp_LF8_4b_exp` | pack | unpacker A, unpacker B |
| `THCON_SEC0_REG1_ovrd_default_throttle_mode` | pack | both unpackers |
| `ALU_FORMAT_SPEC_REG0_SrcAUnsigned`, `SrcBUnsigned` | math | unpacker A, unpacker B |
| `STACC_RELU_*`, `ALU_ROUNDING_MODE_Packer_srnd_en`, `Gasket_srnd_en`, `INT_DESCALE_*`, `Dstacc_override` | math | packer |
| `THCON_SEC0/1_REG8_unpack_tile_offset` | pack | nobody (dead) |

when one 32-bit word holds fields of both engines (words 70, 71, 119), the compiler has to merge them: a `pack.cfg` write must not clear the unpacker's bit, and the other way round.

## 8. what hangs

all need `tt-smi --eth_train_skip -r N`:
- unpack B on context 2-7
- unpack `uncompressed` = 0 on plain data
- unpack throttle x8 (with the override) on FP32 -> 16-bit, bfp4, bfp4a
- unpack mismatched format pairs (`KNOWN_HANG`)
- pack `in_fmt` bfp4, bfp4a, bfp2, bfp2a
- pack `Enable_out_fifo`

## 9. corrections to other sources

- `ttrv_cfg.md`: `Dest_cntx`, `Tile_x_dim_cntx`, `Offset_cntx` and `Shift_amount_cntx` are shared by ctx and ctx + 4 (ctx & 3). `Unp_LF8_4b_exp`, `ovrd_default_throttle_mode` and `SrcA/BUnsigned` belong to unpack. ReLU, srnd, descale and `Dstacc_override` belong to pack
- ttsim: wrong on BH for `PCK0_ADDR_BASE_REG_0/1`, `TILE_FACE_SET_MAPPING_1..3` and unpack B tileize (all work). It also doesn't model pack ctx 1-3, row sets 2-3, or the pack fifo
- LLK: writes `Throttle_mode` = 2, which does nothing because every LLK pack write clears the override bit in word 70. LLK also writes `ALU_FORMAT_SPEC_REG2_Dstacc`, which the BH packer doesn't read
- the unpack and pack FIFO units differ (16 B vs 32 B). The language takes bytes for both

## 10. not measured yet

- unpack:
  - `to_dst` with 16-bit Dst
  - `upsample_skip` vs `upsample`
  - compressed input
  - 8-bit tileize row width
  - bfp2 with `NoBFPExpSection`
  - REG10 fifo on ctx 2-7
  - `w_dim` with W stepping
  - `clear_fmt` as the format math sees after a NOP SetDvalid
  - `SetOvrdWithAddr` = 0 row mechanics
- pack:
  - `l1_acc` for int32 / int8
  - int16 output from 16-bit Dst
  - bfp*a output values (the sizes are right)
  - compressed output contents (`rsi_size` is per context, values not decoded)
  - `edge_rows`, `edge_facesel` per context
  - `Auto_set_last_pacr_intf_sel` with partial `ReadIntfSel` patterns
- both:
  - `CFG_STATE_ID` = 1 (the second config bank)
  - the math-thread fields `DISABLE_IMPLIED_*`, `CLR_DVALID_*`

## 11. moved from the spec

findings that used to sit in `ttrv_spec_new.md`. the spec keeps the rule, this keeps the reason.

### unpack contexts
- probe: `blackhole-py-old/tests/probes/probe_unpack_contexts.py` (p150a)
- A: contexts 0-7. B: 0-1. B on 2-7 hangs the card until `tt-smi -r`. B's registers for 2-7 exist and hold values, but B never reads them
- the context read is `(CfgContextOffset + (AutoIncContextID ? counter : CfgContextId)) mod 8`. the offset is 4 bits but wraps mod 8. the counter steps on every UNPACR with AutoIncContextID and does not include the offset, so `count=4 offset=4` cycles 4, 5, 6, 7
- `count` lowers to `Context_count_non_log2_en = 1`, `_non_log2 = count - 1`: wraps after exactly `count`, `Context_count` is ignored while `_en` = 1
- counter reset bug: a lone `SETC16` reset with no unpacker instruction within a few cycles is silently lost (stalls, 8 NOPs and disabling clock gating don't help). lowering: `SETC16 reset=1`, `UNPACR_NOP` mode 2, `SETC16 reset=0`, nothing in between. mode 1 would clear a Src bank
- `SETC16 CfgContextCntInc` does nothing. use `AutoIncContextID` (`ctxa.next`)
- the spec forms emit every unpack in multi-context mode (`OvrdThreadId` = 1)

### counters
- `ADDR_MOD_BIAS` only picks slots 4-7 on wormhole, nothing on blackhole: fixed 0. `ADDR_MOD_AB2` not measured, not written
- `sp` (sfpu stack pointer rwc) is blackhole only, int32-all mode
- unpack L1-side strides are dead: the L1 address comes from the ADCs and the tile dims

### mop
- after a mop, the next non-mop instruction costs 1 idle cycle. a `replay` of 2+ instructions inside the mop hides it
- `inner 0` without `start` triggers hardware bugs, so the spec rejects it

### sfpmacro
- the macro register's high bit comes from the low bit of the full Dst address, so `dst` and the math Dst offset must be even
- an fpu write to Dst and an `sfpmacro.run` reading the same rows need 3 unrelated tensix instructions between them
- across macros, or against your own sfpu instructions, a scheduled instruction on the same sub-unit and cycle wins and yours is dropped silently

### how llama3-1b `qkv` uses the counters (ttk era, before `unpack` / `pack` moves)
- unpack: once per tile `x_start=0, x_end=255` and z/w = 0, then a mop whose loop is `unpack ctxa0, l1_z+=1`: each unpack moves one face, the counter steps to the next
- math: addrmod `step` (`srca+=8, dst+=8`), a mop of `math.mova2d addr=step`, `math.rwc srca=0, srcb=0, dst=0` around it, `math.rwc release=a|b` as the mop's `end`. the Dst tile comes from the math Dst offset
- sfpu: a replay of `sfp.load` ... `math.rwc dst+=2`
- pack: addrmods `row` / `tile` / `face`, `pack.adc` zeros per tile, a mop of packs with `addr=row`, the last ones `addr=tile` / `addr=face`

### not measured yet (spec features)
the second config state (`CFG_STATE_ID`), per-context `in_fmt` / `out_fmt`, `to_dst` and `reg_row` per context, other `UNPACR_NOP` forms (clear, overlay)

## 12. plain tile moves: `unpack` / `pack`

the design behind the spec's `unpack.fmt` / `unpack` / `pack.fmt` / `pack`. probes: `tests/probes/test_bfp_blocks.py`, `test_lowbit_weight_formats.py`, `probe_unpack_fields.py`.

### dvalid
SrcA and SrcB each have 2 banks. the unpacker fills one, sets dvalid (the bank now belongs to math) and moves to the other. math stalls on `SRCA_VLD` / `SRCB_VLD`, computes, clears dvalid (bank back to the unpacker). if math holds both banks, the next unpacker write waits. set by the `UNPACR` `SetDatValid` bit, or by `UNPACR_NOP` `Set_Dvalid` without unpacking (LLK: to satisfy math's SrcB check when an op only needs SrcA)

### bfp
- one `UNPACR` reads only one face of bfp. asking for 512 or 1024 values completes but delivers the first 256. `x_end` = 1023 with bfp input hung card 0 once. so a bfp tile takes up to 4 `UNPACR`s that step a counter, unlike every other format
- mantissas sit after the exponents: an L1 block is `[ceil16(n/16) exponent bytes][mantissas]`. the unpacker finds the mantissas from the descriptor dims, so for bfp the block size must be known: `x_dim = min(n, 256)`, `z_dim = n / 256`
- mantissa reads must start on a 16-byte word. other starts corrupt fixed 8-value chunks
- Src format code = input code (bfp8 -> bfp8). the values land in Src as bf16
- forced shared exponent (`shared_exp`): bfp data with no exponent section, exact. int8 read as bfp8 with a forced exponent is exact too
- pack `Exp_section_size` = number of faces, in 16 B units. blocks of 1, 2 or 4 faces, or half a face, can go at any 16 B aligned address
- pack rounding depends on the packer's input format: bfp8 (tt-metal's default) pre-rounds to 6 bits, bf16 to 7 bits half-away, fp32 doesn't pre-round. the shared exponent is the group max, rounded half-away to 7 bits. bfp4 truncates to 3 bits. -0 packs as +0
- a packer input format of bfp4 or bfp2 hangs
- bfp4 at the default x4 rate: a run that starts partway into a group of 256 must end inside it (ISA model, confirmed below). keep bfp at whole faces (or the first half of a face) per `UNPACR`
- 4 bfp faces into one Src bank with one `dvalid`: bit exact (`test_bfp_bank_and_groups.py`). 4 x `UNPACR` with `x_end` = 255, `AddrMode` = 0x11 (ch0 Z += 1: next L1 face, ch1 Z += 1: next 16 Src rows), `SetDatValid` only on the last. bfp8 and bfp4 use the same 4 instructions
- Src `Zstride` counts in the Src format's datum size. with bfp8 / bfp4 as the Src format (1 byte) a face is 256 apart, not bf16's 512. wrong stride = faces 2 and 3 overwrite faces 0 and 1. the compiler derives it from the format
- bfp4 group crossing (`test_bfp_bank_and_groups.py`): at the default rate, a run that crosses a 256-datum group and stops partway through a 16-byte word gets wrong exponents **and breaks later unpacks until a card reset**. whole-face unpacks never hit it

### fixed by the compiler for `unpack`
`Ovrd_data_format` = 1, uncompressed = 1, throttle auto, `ADD_DEST_ADDR_CNTR` = 1, `SetOvrdWithAddr` = 1, multi-context mode, `reg_row` = 0, Src strides from the format, descriptor dims from `n` (x = min(n, 256), z = n / 256)

### base address
the `unpack` base write is a RISC-side post on `UNPACK_SYNC`, paired with the Tensix `SEMGET` after the `UNPACR` (LLK's context acquire / release, at most 2 in flight). unpaired = hang on the third

### one datum (p150a, `blackhole-py-old/tests/probes/probe_pack_one.py`)
32-bit Dst, `fp32>fp32`, `fp32>bf16`, `bf16>bf16`, `ReadIntfSel` 0b0001, no hangs:
- `SETADCXX(4, c, c)` packs exactly datum (row, c) for any row / column tried, at the block start, then zeros to the end of the 16-byte block
- n one-datum `PACR`s with `Last` only on the final one pack back to back: a Dst column gathered into consecutive L1 slots
- tail: 16 B past the block, or 32 B when the tile's input ends 16 B into a 32-byte unit (4 fp32 / 8 bf16 datums), as `PACR.md` says
- `PCK0_ADDR_BASE_REG_1` of 2 / 4 / 8 bytes is ignored; only multiples of 16 move the output
- a `ZeroWrite` `PACR` of k zeros then the datum puts it at slot k (k = 1, 3, 7) and zeroes the rest of the block
- the same with `Pack_L1_Acc`: only slot k changes, bit exact; every neighbour (normal floats) unchanged, including in the 32 B tail case. the slot must hold 0 first
- not tested: −0, NaN or denormal neighbours under `Pack_L1_Acc`, fp16 output, 16-bit Dst

### cycles (p150a)
- inline Tensix words issue at 4 per RISC cycle when the code is warm, and the TRISC can be 32+ words ahead before it stalls. issuing never holds the TRISC up, only explicit waits do
- bf16 unpack pair: 17 cycles / tile (one `UNPACR` each = face mop). fp8: 16 (one `UNPACR` each) vs 20 (face mop)
- pack 1024: bf16 18 cycles, fp32 35. mop = replay = 16 inline `PACR`s
- re-arming the pack per tile costs +14 cycles (mop, hand written) to +41 (ttk)
- llama3's current per-tile unpack loop: 92-95 cycles, from the config poll, commit and drain, not the issue
- so plain moves don't need a mop: the issue is at most 4 `UNPACR`s or 16 `PACR`s
- pack: 15 x (`reg_y+=4, l1_y+=4`), the last with `Last` + reset, no face structure. measured for bf16 / fp32 output, bfp output still to confirm
