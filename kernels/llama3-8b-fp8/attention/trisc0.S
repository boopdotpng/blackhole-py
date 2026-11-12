# llama3 8b-fp8 decode: attention, trisc0. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (96): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5 7,6 7,7 7,8 7,9 7,10 7,11 10,2 10,3 10,4 10,5 10,6 10,7 10,8 10,9 10,10 10,11 11,2 11,3 11,4 11,5 11,6 11,7 11,8 11,9 11,10 11,11 12,2 12,3 12,4 12,5 12,6 12,7
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=attention_e2e_q_compact, 0x79c=attention_e2e_k_compact, 0x7a0=attention_e2e_v_compact, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0xe900=e2e_attention_partials, 0xe904=attention_core, 0xe908=attention_phase
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
      4: 820a8a93  addi         x21, x21, -2016  # x21 = 0xffb00820 · riscv_local_mem + 0x820
      8: 00020b37  lui          x22, 0x00020  # x22 = 0x00020000
      c: 880b0b13  addi         x22, x22, -1920  # x22 = 0x0001f880
     10: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x820 · 0xffb00820; write 0x0001f880
     14: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     18: 824a8a93  addi         x21, x21, -2012  # x21 = 0xffb00824 · riscv_local_mem + 0x824
     1c: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x824 · 0xffb00824; write 0x00000000
     20: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
     24: 82828293  addi         x5, x5, -2008  # x5 = 0xffb00828 · riscv_local_mem + 0x828
     28: 0000f337  lui          x6, 0x0000f  # x6 = 0x0000f000
     2c: 08030313  addi         x6, x6, 128  # x6 = 0x0000f080
     30: 0062a023  sw           x6, 0(x5)  # riscv_local_mem + 0x828 · 0xffb00828; write 0x0000f080
     34: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
     38: 82c28293  addi         x5, x5, -2004  # x5 = 0xffb0082c · riscv_local_mem + 0x82c
     3c: 0002a023  sw           x0, 0(x5)  # riscv_local_mem + 0x82c · 0xffb0082c; write 0x00000000
     40: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     44: 830a8a93  addi         x21, x21, -2000  # x21 = 0xffb00830 · riscv_local_mem + 0x830
     48: 00011b37  lui          x22, 0x00011  # x22 = 0x00011000
     4c: 080b0b13  addi         x22, x22, 128  # x22 = 0x00011080
     50: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x830 · 0xffb00830; write 0x00011080
     54: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     58: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
     5c: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834; write 0x00000000
     60: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     64: 838a8a93  addi         x21, x21, -1992  # x21 = 0xffb00838 · riscv_local_mem + 0x838
     68: 00015b37  lui          x22, 0x00015  # x22 = 0x00015000
     6c: 080b0b13  addi         x22, x22, 128  # x22 = 0x00015080
     70: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x838 · 0xffb00838; write 0x00015080
     74: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     78: 83ca8a93  addi         x21, x21, -1988  # x21 = 0xffb0083c · riscv_local_mem + 0x83c
     7c: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x83c · 0xffb0083c; write 0x00000000
     80: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     84: 840a8a93  addi         x21, x21, -1984  # x21 = 0xffb00840 · riscv_local_mem + 0x840
     88: 00019b37  lui          x22, 0x00019  # x22 = 0x00019000
     8c: 080b0b13  addi         x22, x22, 128  # x22 = 0x00019080
     90: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x840 · 0xffb00840; write 0x00019080
     94: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     98: 844a8a93  addi         x21, x21, -1980  # x21 = 0xffb00844 · riscv_local_mem + 0x844
     9c: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x844 · 0xffb00844; write 0x00000000
     a0: 0000f337  lui          x6, 0x0000f  # x6 = 0x0000f000
     a4: 90830313  addi         x6, x6, -1784  # x6 = 0x0000e908
     a8: 00032203  lw           x4, 0(x6)  # param attention_phase; 0x0000e908
     ac: 79000413  addi         x8, x0, 1936  # x8 = 0x00000790
     b0: 00042303  lw           x6, 0(x8)  # param kv_blocks; 0x00000790
     b4: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
     b8: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
     bc: 0063fa63  bgeu         x7, x6, 0x000000d0  # target 0x000000d0
     c0: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     c4: 08000393  addi         x7, x0, 128  # x7 = 0x00000080
     c8: 0063f463  bgeu         x7, x6, 0x000000d0  # target 0x000000d0
     cc: 00c00293  addi         x5, x0, 12  # x5 = 0x0000000c
loc_d0:
     d0: 285276e3  bgeu         x4, x5, 0x00000b5c  # target 0x00000b5c
     d4: 28d000ef  jal          x1, 0x00000b60  # target 0x00000b60; x1 = 0x000000d8
     d8: 289000ef  jal          x1, 0x00000b60  # target 0x00000b60; x1 = 0x000000dc
     dc: 285000ef  jal          x1, 0x00000b60  # target 0x00000b60; x1 = 0x000000e0
     e0: 281000ef  jal          x1, 0x00000b60  # target 0x00000b60; x1 = 0x000000e4
     e4: 79000293  addi         x5, x0, 1936  # x5 = 0x00000790
     e8: 0002a203  lw           x4, 0(x5)  # param kv_blocks; 0x00000790
     ec: 0000f3b7  lui          x7, 0x0000f  # x7 = 0x0000f000
     f0: 90838393  addi         x7, x7, -1784  # x7 = 0x0000e908
     f4: 0003a283  lw           x5, 0(x7)  # param attention_phase; 0x0000e908
     f8: 79000493  addi         x9, x0, 1936  # x9 = 0x00000790
     fc: 0004a383  lw           x7, 0(x9)  # param kv_blocks; 0x00000790
    100: 00100313  addi         x6, x0, 1  # x6 = 0x00000001
    104: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    108: 00747a63  bgeu         x8, x7, 0x0000011c  # target 0x0000011c
    10c: 00400313  addi         x6, x0, 4  # x6 = 0x00000004
    110: 08000413  addi         x8, x0, 128  # x8 = 0x00000080
    114: 00747463  bgeu         x8, x7, 0x0000011c  # target 0x0000011c
    118: 00c00313  addi         x6, x0, 12  # x6 = 0x0000000c
loc_11c:
    11c: 00620233  add          x4, x4, x6
    120: fff20213  addi         x4, x4, -1
    124: 40520233  sub          x4, x4, x5
    128: 02625233  divu         x4, x4, x6
    12c: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    130: 82c48493  addi         x9, x9, -2004  # x9 = 0xffb0082c · riscv_local_mem + 0x82c
    134: 0004a283  lw           x5, 0(x9)  # riscv_local_mem + 0x82c · 0xffb0082c
    138: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
loc_13c:
    13c: ffb484b7  lui          x9, 0xffb48  # x9 = 0xffb48000
    140: 02848493  addi         x9, x9, 40  # x9 = 0xffb48028
    144: 0004d303  lhu          x6, 0(x9)  # 0xffb48028
    148: 405303b3  sub          x7, x6, x5
    14c: 01039393  slli         x7, x7, 16
    150: 0103d393  srli         x7, x7, 16
    154: 0083f663  bgeu         x7, x8, 0x00000160  # target 0x00000160
    158: 0ff0000f  fence        0xf, 0xf
    15c: fe1ff06f  jal          x0, 0x0000013c  # target 0x0000013c
loc_160:
    160: 0ff0000f  fence        0xf, 0xf
    164: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    168: 00020313  addi         x6, x4, 0
loc_16c:
    16c: 1862f4e3  bgeu         x5, x6, 0x00000af4  # target 0x00000af4
    170: ffe803b7  lui          x7, 0xffe80  # x7 = 0xffe80000 · tensix_pc_buf + 0x0
    174: 03438393  addi         x7, x7, 52  # x7 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_178:
    178: 0003a403  lw           x8, 0(x7)  # UNPACK_CONFIG_SYNC · 0xffe80034
    17c: 0fe47413  andi         x8, x8, 254
    180: 00040663  beq          x8, x0, 0x0000018c  # target 0x0000018c
    184: 0ff0000f  fence        0xf, 0xf
    188: ff1ff06f  jal          x0, 0x00000178  # target 0x00000178
loc_18c:
    18c: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    190: d500011e  RMWCIB2      Mask=64, Data=0, CfgRegAddr=71  # cfg[71] (current thread StateID); THCON_SEC0_REG1_Unp_LF8_4b_exp = 0
    194: ffef03b7  lui          x7, 0xffef0  # x7 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    198: 10038393  addi         x7, x7, 256  # x7 = 0xffef0100 · cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor
    19c: 01500413  addi         x8, x0, 21  # x8 = 0x00000015
    1a0: 0083a023  sw           x8, 0(x7)  # cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor · 0xffef0100; write 0x00000015; cfg[64] (bank 0); THCON_SEC0_REG0_TileDescriptor = 21
    1a4: 00040437  lui          x8, 0x00040  # x8 = 0x00040000
    1a8: 00140413  addi         x8, x8, 1  # x8 = 0x00040001
    1ac: 0083a223  sw           x8, 4(x7)  # cfg[65] (bank 0) (undocumented index) · 0xffef0104; write 0x00040001; cfg[65] (bank 0) · fields not in ttsim
    1b0: 0003a423  sw           x0, 8(x7)  # cfg[66] (bank 0) (undocumented index) · 0xffef0108; write 0x00000000; cfg[66] (bank 0) · fields not in ttsim
    1b4: 0003a623  sw           x0, 12(x7)  # cfg[67] (bank 0) (undocumented index) · 0xffef010c; write 0x00000000; cfg[67] (bank 0) · fields not in ttsim
    1b8: 12500413  addi         x8, x0, 293  # x8 = 0x00000125
    1bc: 0283a023  sw           x8, 32(x7)  # cfg[72] (bank 0) · THCON_SEC0_REG2_Out_data_format, THCON_SEC0_REG2_Throttle_mode, THCON_SEC0_REG2_Context_count, THCON_SEC0_REG2_Haloize_mode, THCON_SEC0_REG2_Tileize_mode, THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC0_REG2_Unpack_If_Sel, THCON_SEC0_REG2_Upsample_rate, THCON_SEC0_REG2_Ovrd_data_format, THCON_SEC0_REG2_Upsample_and_interleave, THCON_SEC0_REG2_Shift_amount_cntx0, THCON_SEC0_REG2_Shift_amount_cntx1, THCON_SEC0_REG2_Shift_amount_cntx2, THCON_SEC0_REG2_Shift_amount_cntx3 · 0xffef0120; write 0x00000125; cfg[72] (bank 0); THCON_SEC0_REG2_Out_data_format = 5; THCON_SEC0_REG2_Throttle_mode = 2; THCON_SEC0_REG2_Context_count = 0; THCON_SEC0_REG2_Haloize_mode = 1; THCON_SEC0_REG2_Tileize_mode = 0; THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC0_REG2_Unpack_If_Sel = 0; THCON_SEC0_REG2_Upsample_rate = 0; THCON_SEC0_REG2_Ovrd_data_format = 0; THCON_SEC0_REG2_Upsample_and_interleave = 0; THCON_SEC0_REG2_Shift_amount_cntx0 = 0; THCON_SEC0_REG2_Shift_amount_cntx1 = 0; THCON_SEC0_REG2_Shift_amount_cntx2 = 0; THCON_SEC0_REG2_Shift_amount_cntx3 = 0
    1c0: 00300413  addi         x8, x0, 3  # x8 = 0x00000003
    1c4: 0283a223  sw           x8, 36(x7)  # cfg[73] (bank 0) · THCON_SEC0_REG2_Disable_zero_compress_cntx0, THCON_SEC0_REG2_Disable_zero_compress_cntx1, THCON_SEC0_REG2_Disable_zero_compress_cntx2, THCON_SEC0_REG2_Disable_zero_compress_cntx3, THCON_SEC0_REG2_Unpack_if_sel_cntx0, THCON_SEC0_REG2_Unpack_if_sel_cntx1, THCON_SEC0_REG2_Unpack_if_sel_cntx2, THCON_SEC0_REG2_Unpack_if_sel_cntx3, THCON_SEC0_REG2_Force_shared_exp, THCON_SEC0_REG2_Context_count_non_log2, THCON_SEC0_REG2_Context_count_non_log2_en, THCON_SEC0_REG2_Disable_zero_compress_cntx4, THCON_SEC0_REG2_Disable_zero_compress_cntx5, THCON_SEC0_REG2_Disable_zero_compress_cntx6, THCON_SEC0_REG2_Disable_zero_compress_cntx7, THCON_SEC0_REG2_Unpack_if_sel_cntx4, THCON_SEC0_REG2_Unpack_if_sel_cntx5, THCON_SEC0_REG2_Unpack_if_sel_cntx6, THCON_SEC0_REG2_Unpack_if_sel_cntx7, THCON_SEC0_REG2_Metadata_x_end · 0xffef0124; write 0x00000003; cfg[73] (bank 0); THCON_SEC0_REG2_Disable_zero_compress_cntx0 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx1 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx2 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx3 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx0 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx1 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx2 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx3 = 0; THCON_SEC0_REG2_Force_shared_exp = 0; THCON_SEC0_REG2_Context_count_non_log2 = 0; THCON_SEC0_REG2_Context_count_non_log2_en = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx4 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx5 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx6 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx7 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx4 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx5 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx6 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx7 = 0; THCON_SEC0_REG2_Metadata_x_end = 0
    1c8: 0203a423  sw           x0, 40(x7)  # cfg[74] (bank 0) · THCON_SEC0_REG2_Unpack_limit_address · 0xffef0128; write 0x00000000; cfg[74] (bank 0); THCON_SEC0_REG2_Unpack_limit_address = 0
    1cc: 0203a623  sw           x0, 44(x7)  # cfg[75] (bank 0) · THCON_SEC0_REG2_Unpack_fifo_size · 0xffef012c; write 0x00000000; cfg[75] (bank 0); THCON_SEC0_REG2_Unpack_fifo_size = 0
    1d0: fa03a823  sw           x0, -80(x7)  # cfg[44] (bank 0) · UNP0_ADDR_CTRL_XY_REG_0_Xstride, UNP0_ADDR_CTRL_XY_REG_0_Ystride · 0xffef00b0; write 0x00000000; cfg[44] (bank 0); UNP0_ADDR_CTRL_XY_REG_0_Xstride = 0; UNP0_ADDR_CTRL_XY_REG_0_Ystride = 0
    1d4: fa03aa23  sw           x0, -76(x7)  # cfg[45] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_0_Zstride, UNP0_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef00b4; write 0x00000000; cfg[45] (bank 0); UNP0_ADDR_CTRL_ZW_REG_0_Zstride = 0; UNP0_ADDR_CTRL_ZW_REG_0_Wstride = 0
    1d8: 00200437  lui          x8, 0x00200  # x8 = 0x00200000
    1dc: 00240413  addi         x8, x8, 2  # x8 = 0x00200002
    1e0: fe83a023  sw           x8, -32(x7)  # cfg[56] (bank 0) · UNP0_ADDR_CTRL_XY_REG_1_Xstride, UNP0_ADDR_CTRL_XY_REG_1_Ystride · 0xffef00e0; write 0x00200002; cfg[56] (bank 0); UNP0_ADDR_CTRL_XY_REG_1_Xstride = 2; UNP0_ADDR_CTRL_XY_REG_1_Ystride = 32
    1e4: 20000413  addi         x8, x0, 512  # x8 = 0x00000200
    1e8: fe83a223  sw           x8, -28(x7)  # cfg[57] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_1_Zstride, UNP0_ADDR_CTRL_ZW_REG_1_Wstride · 0xffef00e4; write 0x00000200; cfg[57] (bank 0); UNP0_ADDR_CTRL_ZW_REG_1_Zstride = 512; UNP0_ADDR_CTRL_ZW_REG_1_Wstride = 0
    1ec: fc03a023  sw           x0, -64(x7)  # cfg[48] (bank 0) · UNP0_ADDR_BASE_REG_0_Base · 0xffef00c0; write 0x00000000; cfg[48] (bank 0); UNP0_ADDR_BASE_REG_0_Base = 0
    1f0: fc03a223  sw           x0, -60(x7)  # cfg[49] (bank 0) · UNP0_ADDR_BASE_REG_1_Base · 0xffef00c4; write 0x00000000; cfg[49] (bank 0); UNP0_ADDR_BASE_REG_1_Base = 0
    1f4: 10000413  addi         x8, x0, 256  # x8 = 0x00000100
    1f8: fc83a423  sw           x8, -56(x7)  # cfg[50] (bank 0) · UNP0_FORCED_SHARED_EXP_shared_exp, UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr · 0xffef00c8; write 0x00000100; cfg[50] (bank 0); UNP0_FORCED_SHARED_EXP_shared_exp = 0; UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr = 1
    1fc: fc03aa23  sw           x0, -44(x7)  # cfg[53] (bank 0) · UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val · 0xffef00d4; write 0x00000000; cfg[53] (bank 0); UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val = 0
    200: 00400437  lui          x8, 0x00400  # x8 = 0x00400000
    204: 04040413  addi         x8, x8, 64  # x8 = 0x00400040
    208: 0483a823  sw           x8, 80(x7)  # cfg[84] (bank 0) · THCON_SEC0_REG5_Dest_cntx0_address, THCON_SEC0_REG5_Dest_cntx1_address · 0xffef0150; write 0x00400040; cfg[84] (bank 0); THCON_SEC0_REG5_Dest_cntx0_address = 64; THCON_SEC0_REG5_Dest_cntx1_address = 64
    20c: 01000437  lui          x8, 0x01000  # x8 = 0x01000000
    210: 10040413  addi         x8, x8, 256  # x8 = 0x01000100
    214: 0483ac23  sw           x8, 88(x7)  # cfg[86] (bank 0) · THCON_SEC0_REG5_Tile_x_dim_cntx0, THCON_SEC0_REG5_Tile_x_dim_cntx1 · 0xffef0158; write 0x01000100; cfg[86] (bank 0); THCON_SEC0_REG5_Tile_x_dim_cntx0 = 256; THCON_SEC0_REG5_Tile_x_dim_cntx1 = 256
    218: 0603a823  sw           x0, 112(x7)  # cfg[92] (bank 0) · THCON_SEC0_REG7_Offset_address, THCON_SEC0_REG7_Unpack_data_format_cntx0, THCON_SEC0_REG7_Unpack_out_data_format_cntx0, THCON_SEC0_REG7_Unpack_data_format_cntx4, THCON_SEC0_REG7_Unpack_out_data_format_cntx4 · 0xffef0170; write 0x00000000; cfg[92] (bank 0); THCON_SEC0_REG7_Offset_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx4 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx4 = 0
    21c: 0603aa23  sw           x0, 116(x7)  # cfg[93] (bank 0) · THCON_SEC0_REG7_Offset_cntx1_address, THCON_SEC0_REG7_Unpack_data_format_cntx1, THCON_SEC0_REG7_Unpack_out_data_format_cntx1, THCON_SEC0_REG7_Unpack_data_format_cntx5, THCON_SEC0_REG7_Unpack_out_data_format_cntx5 · 0xffef0174; write 0x00000000; cfg[93] (bank 0); THCON_SEC0_REG7_Offset_cntx1_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx5 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx5 = 0
    220: d50001de  RMWCIB2      Mask=64, Data=0, CfgRegAddr=119  # cfg[119] (current thread StateID); THCON_SEC1_REG1_Unp_LF8_4b_exp = 0
    224: ffef03b7  lui          x7, 0xffef0  # x7 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    228: 1c038393  addi         x7, x7, 448  # x7 = 0xffef01c0 · cfg[112] (bank 0) · THCON_SEC1_REG0_TileDescriptor
    22c: 01000437  lui          x8, 0x01000  # x8 = 0x01000000
    230: 01540413  addi         x8, x8, 21  # x8 = 0x01000015
    234: 0083a023  sw           x8, 0(x7)  # cfg[112] (bank 0) · THCON_SEC1_REG0_TileDescriptor · 0xffef01c0; write 0x01000015; cfg[112] (bank 0); THCON_SEC1_REG0_TileDescriptor = 16777237
    238: 00040437  lui          x8, 0x00040  # x8 = 0x00040000
    23c: 00140413  addi         x8, x8, 1  # x8 = 0x00040001
    240: 0083a223  sw           x8, 4(x7)  # cfg[113] (bank 0) (undocumented index) · 0xffef01c4; write 0x00040001; cfg[113] (bank 0) · fields not in ttsim
    244: 0003a423  sw           x0, 8(x7)  # cfg[114] (bank 0) (undocumented index) · 0xffef01c8; write 0x00000000; cfg[114] (bank 0) · fields not in ttsim
    248: 0003a623  sw           x0, 12(x7)  # cfg[115] (bank 0) (undocumented index) · 0xffef01cc; write 0x00000000; cfg[115] (bank 0) · fields not in ttsim
    24c: 02500413  addi         x8, x0, 37  # x8 = 0x00000025
    250: 0283a023  sw           x8, 32(x7)  # cfg[120] (bank 0) · THCON_SEC1_REG2_Out_data_format, THCON_SEC1_REG2_Throttle_mode, THCON_SEC1_REG2_Context_count, THCON_SEC1_REG2_Haloize_mode, THCON_SEC1_REG2_Tileize_mode, THCON_SEC1_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC1_REG2_Unpack_If_Sel, THCON_SEC1_REG2_Upsample_rate, THCON_SEC1_REG2_Ovrd_data_format, THCON_SEC1_REG2_Upsample_and_interleave, THCON_SEC1_REG2_Shift_amount_cntx0, THCON_SEC1_REG2_Shift_amount_cntx1, THCON_SEC1_REG2_Shift_amount_cntx2, THCON_SEC1_REG2_Shift_amount_cntx3 · 0xffef01e0; write 0x00000025; cfg[120] (bank 0); THCON_SEC1_REG2_Out_data_format = 5; THCON_SEC1_REG2_Throttle_mode = 2; THCON_SEC1_REG2_Context_count = 0; THCON_SEC1_REG2_Haloize_mode = 0; THCON_SEC1_REG2_Tileize_mode = 0; THCON_SEC1_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC1_REG2_Unpack_If_Sel = 0; THCON_SEC1_REG2_Upsample_rate = 0; THCON_SEC1_REG2_Ovrd_data_format = 0; THCON_SEC1_REG2_Upsample_and_interleave = 0; THCON_SEC1_REG2_Shift_amount_cntx0 = 0; THCON_SEC1_REG2_Shift_amount_cntx1 = 0; THCON_SEC1_REG2_Shift_amount_cntx2 = 0; THCON_SEC1_REG2_Shift_amount_cntx3 = 0
    254: 00300413  addi         x8, x0, 3  # x8 = 0x00000003
    258: 0283a223  sw           x8, 36(x7)  # cfg[121] (bank 0) · THCON_SEC1_REG2_Disable_zero_compress_cntx0, THCON_SEC1_REG2_Disable_zero_compress_cntx1, THCON_SEC1_REG2_Disable_zero_compress_cntx2, THCON_SEC1_REG2_Disable_zero_compress_cntx3, THCON_SEC1_REG2_Unpack_if_sel_cntx0, THCON_SEC1_REG2_Unpack_if_sel_cntx1, THCON_SEC1_REG2_Unpack_if_sel_cntx2, THCON_SEC1_REG2_Unpack_if_sel_cntx3, THCON_SEC1_REG2_Force_shared_exp, THCON_SEC1_REG2_Context_count_non_log2, THCON_SEC1_REG2_Context_count_non_log2_en, THCON_SEC1_REG2_Disable_zero_compress_cntx4, THCON_SEC1_REG2_Disable_zero_compress_cntx5, THCON_SEC1_REG2_Disable_zero_compress_cntx6, THCON_SEC1_REG2_Disable_zero_compress_cntx7, THCON_SEC1_REG2_Unpack_if_sel_cntx4, THCON_SEC1_REG2_Unpack_if_sel_cntx5, THCON_SEC1_REG2_Unpack_if_sel_cntx6, THCON_SEC1_REG2_Unpack_if_sel_cntx7, THCON_SEC1_REG2_Metadata_x_end · 0xffef01e4; write 0x00000003; cfg[121] (bank 0); THCON_SEC1_REG2_Disable_zero_compress_cntx0 = 1; THCON_SEC1_REG2_Disable_zero_compress_cntx1 = 1; THCON_SEC1_REG2_Disable_zero_compress_cntx2 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx3 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx0 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx1 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx2 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx3 = 0; THCON_SEC1_REG2_Force_shared_exp = 0; THCON_SEC1_REG2_Context_count_non_log2 = 0; THCON_SEC1_REG2_Context_count_non_log2_en = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx4 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx5 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx6 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx7 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx4 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx5 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx6 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx7 = 0; THCON_SEC1_REG2_Metadata_x_end = 0
    25c: 0203a423  sw           x0, 40(x7)  # cfg[122] (bank 0) · THCON_SEC1_REG2_Unpack_limit_address · 0xffef01e8; write 0x00000000; cfg[122] (bank 0); THCON_SEC1_REG2_Unpack_limit_address = 0
    260: 0203a623  sw           x0, 44(x7)  # cfg[123] (bank 0) · THCON_SEC1_REG2_Unpack_fifo_size · 0xffef01ec; write 0x00000000; cfg[123] (bank 0); THCON_SEC1_REG2_Unpack_fifo_size = 0
    264: ee03ac23  sw           x0, -264(x7)  # cfg[46] (bank 0) · UNP1_ADDR_CTRL_XY_REG_0_Xstride, UNP1_ADDR_CTRL_XY_REG_0_Ystride · 0xffef00b8; write 0x00000000; cfg[46] (bank 0); UNP1_ADDR_CTRL_XY_REG_0_Xstride = 0; UNP1_ADDR_CTRL_XY_REG_0_Ystride = 0
    268: ee03ae23  sw           x0, -260(x7)  # cfg[47] (bank 0) · UNP1_ADDR_CTRL_ZW_REG_0_Zstride, UNP1_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef00bc; write 0x00000000; cfg[47] (bank 0); UNP1_ADDR_CTRL_ZW_REG_0_Zstride = 0; UNP1_ADDR_CTRL_ZW_REG_0_Wstride = 0
    26c: 00200437  lui          x8, 0x00200  # x8 = 0x00200000
    270: 00240413  addi         x8, x8, 2  # x8 = 0x00200002
    274: f283a423  sw           x8, -216(x7)  # cfg[58] (bank 0) · UNP1_ADDR_CTRL_XY_REG_1_Xstride, UNP1_ADDR_CTRL_XY_REG_1_Ystride · 0xffef00e8; write 0x00200002; cfg[58] (bank 0); UNP1_ADDR_CTRL_XY_REG_1_Xstride = 2; UNP1_ADDR_CTRL_XY_REG_1_Ystride = 32
    278: 20000413  addi         x8, x0, 512  # x8 = 0x00000200
    27c: f283a623  sw           x8, -212(x7)  # cfg[59] (bank 0) · UNP1_ADDR_CTRL_ZW_REG_1_Zstride, UNP1_ADDR_CTRL_ZW_REG_1_Wstride · 0xffef00ec; write 0x00000200; cfg[59] (bank 0); UNP1_ADDR_CTRL_ZW_REG_1_Zstride = 512; UNP1_ADDR_CTRL_ZW_REG_1_Wstride = 0
    280: f203a823  sw           x0, -208(x7)  # cfg[60] (bank 0) · UNP1_ADDR_BASE_REG_0_Base · 0xffef00f0; write 0x00000000; cfg[60] (bank 0); UNP1_ADDR_BASE_REG_0_Base = 0
    284: f203aa23  sw           x0, -204(x7)  # cfg[61] (bank 0) · UNP1_ADDR_BASE_REG_1_Base · 0xffef00f4; write 0x00000000; cfg[61] (bank 0); UNP1_ADDR_BASE_REG_1_Base = 0
    288: f203ac23  sw           x0, -200(x7)  # cfg[62] (bank 0) · UNP1_FORCED_SHARED_EXP_shared_exp, UNP1_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr · 0xffef00f8; write 0x00000000; cfg[62] (bank 0); UNP1_FORCED_SHARED_EXP_shared_exp = 0; UNP1_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr = 0
    28c: f203ae23  sw           x0, -196(x7)  # cfg[63] (bank 0) · UNP1_NOP_REG_CLR_VAL_nop_reg_clr_val · 0xffef00fc; write 0x00000000; cfg[63] (bank 0); UNP1_NOP_REG_CLR_VAL_nop_reg_clr_val = 0
    290: 0403a823  sw           x0, 80(x7)  # cfg[132] (bank 0) · THCON_SEC1_REG5_Dest_cntx0_address, THCON_SEC1_REG5_Dest_cntx1_address · 0xffef0210; write 0x00000000; cfg[132] (bank 0); THCON_SEC1_REG5_Dest_cntx0_address = 0; THCON_SEC1_REG5_Dest_cntx1_address = 0
    294: 01000437  lui          x8, 0x01000  # x8 = 0x01000000
    298: 10040413  addi         x8, x8, 256  # x8 = 0x01000100
    29c: 0483ac23  sw           x8, 88(x7)  # cfg[134] (bank 0) · THCON_SEC1_REG5_Tile_x_dim_cntx0, THCON_SEC1_REG5_Tile_x_dim_cntx1 · 0xffef0218; write 0x01000100; cfg[134] (bank 0); THCON_SEC1_REG5_Tile_x_dim_cntx0 = 256; THCON_SEC1_REG5_Tile_x_dim_cntx1 = 256
    2a0: 0603a823  sw           x0, 112(x7)  # cfg[140] (bank 0) · THCON_SEC1_REG7_Offset_address, THCON_SEC1_REG7_Unpack_data_format_cntx0, THCON_SEC1_REG7_Unpack_out_data_format_cntx0, THCON_SEC1_REG7_Unpack_data_format_cntx4, THCON_SEC1_REG7_Unpack_out_data_format_cntx4 · 0xffef0230; write 0x00000000; cfg[140] (bank 0); THCON_SEC1_REG7_Offset_address = 0; THCON_SEC1_REG7_Unpack_data_format_cntx0 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx0 = 0; THCON_SEC1_REG7_Unpack_data_format_cntx4 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx4 = 0
    2a4: 0603aa23  sw           x0, 116(x7)  # cfg[141] (bank 0) · THCON_SEC1_REG7_Offset_cntx1_address, THCON_SEC1_REG7_Unpack_data_format_cntx1, THCON_SEC1_REG7_Unpack_out_data_format_cntx1, THCON_SEC1_REG7_Unpack_data_format_cntx5, THCON_SEC1_REG7_Unpack_out_data_format_cntx5 · 0xffef0234; write 0x00000000; cfg[141] (bank 0); THCON_SEC1_REG7_Offset_cntx1_address = 0; THCON_SEC1_REG7_Unpack_data_format_cntx1 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx1 = 0; THCON_SEC1_REG7_Unpack_data_format_cntx5 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx5 = 0
    2a8: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    2ac: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_2b0:
    2b0: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    2b4: 0feafa93  andi         x21, x21, 254
    2b8: 000a8663  beq          x21, x0, 0x000002c4  # target 0x000002c4
    2bc: 0ff0000f  fence        0xf, 0xf
    2c0: ff1ff06f  jal          x0, 0x000002b0  # target 0x000002b0
loc_2c4:
    2c4: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    2c8: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    2cc: 830a8a93  addi         x21, x21, -2000  # x21 = 0xffb00830 · riscv_local_mem + 0x830
    2d0: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x830 · 0xffb00830
    2d4: 004a5a13  srli         x20, x20, 4
    2d8: fffa0a13  addi         x20, x20, -1
    2dc: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    2e0: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    2e4: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    2e8: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    2ec: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    2f0: c8140012  SETC16       setc16_reg=5, setc16_value=4  # thread_cfg[5] (current thread); SRCA_SET_Base = 0; SRCA_SET_SetOvrdWithAddr = 1
    2f4: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    2f8: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_2fc:
    2fc: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    300: 0feafa93  andi         x21, x21, 254
    304: 000a8663  beq          x21, x0, 0x00000310  # target 0x00000310
    308: 0ff0000f  fence        0xf, 0xf
    30c: ff1ff06f  jal          x0, 0x000002fc  # target 0x000002fc
loc_310:
    310: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    314: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    318: 828a8a93  addi         x21, x21, -2008  # x21 = 0xffb00828 · riscv_local_mem + 0x828
    31c: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x828 · 0xffb00828
    320: 004a5a13  srli         x20, x20, 4
    324: fffa0a13  addi         x20, x20, -1
    328: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    32c: 1f0a8a93  addi         x21, x21, 496  # x21 = 0xffef01f0 · cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address
    330: 014aa023  sw           x20, 0(x21)  # cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address · 0xffef01f0; write runtime value; cfg[124] (bank 0); THCON_SEC1_REG3_Base_address = runtime
    334: 014aa223  sw           x20, 4(x21)  # cfg[125] (bank 0) · THCON_SEC1_REG3_Base_cntx1_address · 0xffef01f4; write runtime value; cfg[125] (bank 0); THCON_SEC1_REG3_Base_cntx1_address = runtime
    338: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    33c: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    340: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    344: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    348: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    34c: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    350: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    354: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    358: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    35c: 834c0c13  addi         x24, x24, -1996  # x24 = 0xffb00834 · riscv_local_mem + 0x834
    360: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x834 · 0xffb00834
    364: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_368:
    368: ffb49c37  lui          x24, 0xffb49  # x24 = 0xffb49000
    36c: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb49028
    370: 000c5a83  lhu          x21, 0(x24)  # 0xffb49028
    374: 414a8b33  sub          x22, x21, x20
    378: 010b1b13  slli         x22, x22, 16
    37c: 010b5b13  srli         x22, x22, 16
    380: 017b7663  bgeu         x22, x23, 0x0000038c  # target 0x0000038c
    384: 0ff0000f  fence        0xf, 0xf
    388: fe1ff06f  jal          x0, 0x00000368  # target 0x00000368
loc_38c:
    38c: 0ff0000f  fence        0xf, 0xf
    390: 88100182  STALLWAIT    stall_res=8, wait_res=96  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR | Wait.SRCB_CLR
    394: 78bff001  SETADCXX     CntSetMask=1, x_end2=1023, x_start=0
    398: 793ff001  SETADCXX     CntSetMask=2, x_end2=1023, x_start=0
    39c: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    3a0: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    3a4: 0a000305  UNPACR       Unpack_block_selection=1, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    3a8: 08000305  UNPACR       Unpack_block_selection=0, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    3ac: 8810001a  STALLWAIT    stall_res=8, wait_res=6  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0 | Wait.UNPACK1
    3b0: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    3b4: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    3b8: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    3bc: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    3c0: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    3c4: 01507033  and          x0, x0, x21
    3c8: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    3cc: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    3d0: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834
    3d4: 001a0a13  addi         x20, x20, 1
    3d8: 010a1a13  slli         x20, x20, 16
    3dc: 010a5a13  srli         x20, x20, 16
    3e0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    3e4: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    3e8: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834; write runtime value
    3ec: ffb49ab7  lui          x21, 0xffb49  # x21 = 0xffb49000
    3f0: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb49020
    3f4: 014aa023  sw           x20, 0(x21)  # 0xffb49020; write runtime value
    3f8: 0ff0000f  fence        0xf, 0xf
    3fc: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    400: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    404: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830
    408: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    40c: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    410: 015a0a33  add          x20, x20, x21
    414: 00015b37  lui          x22, 0x00015  # x22 = 0x00015000
    418: 080b0b13  addi         x22, x22, 128  # x22 = 0x00015080
    41c: 016a6663  bltu         x20, x22, 0x00000428  # target 0x00000428
    420: 00004bb7  lui          x23, 0x00004  # x23 = 0x00004000
    424: 417a0a33  sub          x20, x20, x23
loc_428:
    428: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    42c: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    430: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830; write runtime value
    434: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    438: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_43c:
    43c: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    440: 0feafa93  andi         x21, x21, 254
    444: 000a8663  beq          x21, x0, 0x00000450  # target 0x00000450
    448: 0ff0000f  fence        0xf, 0xf
    44c: ff1ff06f  jal          x0, 0x0000043c  # target 0x0000043c
loc_450:
    450: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    454: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    458: 830a8a93  addi         x21, x21, -2000  # x21 = 0xffb00830 · riscv_local_mem + 0x830
    45c: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x830 · 0xffb00830
    460: 004a5a13  srli         x20, x20, 4
    464: fffa0a13  addi         x20, x20, -1
    468: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    46c: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    470: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    474: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    478: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    47c: c8140012  SETC16       setc16_reg=5, setc16_value=4  # thread_cfg[5] (current thread); SRCA_SET_Base = 0; SRCA_SET_SetOvrdWithAddr = 1
    480: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    484: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_488:
    488: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    48c: 0feafa93  andi         x21, x21, 254
    490: 000a8663  beq          x21, x0, 0x0000049c  # target 0x0000049c
    494: 0ff0000f  fence        0xf, 0xf
    498: ff1ff06f  jal          x0, 0x00000488  # target 0x00000488
loc_49c:
    49c: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    4a0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    4a4: 828a8a93  addi         x21, x21, -2008  # x21 = 0xffb00828 · riscv_local_mem + 0x828
    4a8: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x828 · 0xffb00828
    4ac: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4b0: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    4b4: 015a0a33  add          x20, x20, x21
    4b8: 00011b37  lui          x22, 0x00011  # x22 = 0x00011000
    4bc: 080b0b13  addi         x22, x22, 128  # x22 = 0x00011080
    4c0: 016a6663  bltu         x20, x22, 0x000004cc  # target 0x000004cc
    4c4: 00002ab7  lui          x21, 0x00002  # x21 = 0x00002000
    4c8: 415a0a33  sub          x20, x20, x21
loc_4cc:
    4cc: 004a5a13  srli         x20, x20, 4
    4d0: fffa0a13  addi         x20, x20, -1
    4d4: ffef0bb7  lui          x23, 0xffef0  # x23 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    4d8: 1f0b8b93  addi         x23, x23, 496  # x23 = 0xffef01f0 · cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address
    4dc: 014ba023  sw           x20, 0(x23)  # cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address · 0xffef01f0; write runtime value; cfg[124] (bank 0); THCON_SEC1_REG3_Base_address = runtime
    4e0: 014ba223  sw           x20, 4(x23)  # cfg[125] (bank 0) · THCON_SEC1_REG3_Base_cntx1_address · 0xffef01f4; write runtime value; cfg[125] (bank 0); THCON_SEC1_REG3_Base_cntx1_address = runtime
    4e4: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    4e8: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    4ec: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    4f0: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    4f4: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    4f8: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    4fc: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    500: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    504: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    508: 834c0c13  addi         x24, x24, -1996  # x24 = 0xffb00834 · riscv_local_mem + 0x834
    50c: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x834 · 0xffb00834
    510: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_514:
    514: ffb49c37  lui          x24, 0xffb49  # x24 = 0xffb49000
    518: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb49028
    51c: 000c5a83  lhu          x21, 0(x24)  # 0xffb49028
    520: 414a8b33  sub          x22, x21, x20
    524: 010b1b13  slli         x22, x22, 16
    528: 010b5b13  srli         x22, x22, 16
    52c: 017b7663  bgeu         x22, x23, 0x00000538  # target 0x00000538
    530: 0ff0000f  fence        0xf, 0xf
    534: fe1ff06f  jal          x0, 0x00000514  # target 0x00000514
loc_538:
    538: 0ff0000f  fence        0xf, 0xf
    53c: 88100182  STALLWAIT    stall_res=8, wait_res=96  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR | Wait.SRCB_CLR
    540: 78bff001  SETADCXX     CntSetMask=1, x_end2=1023, x_start=0
    544: 793ff001  SETADCXX     CntSetMask=2, x_end2=1023, x_start=0
    548: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    54c: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    550: 0a000305  UNPACR       Unpack_block_selection=1, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    554: 08000305  UNPACR       Unpack_block_selection=0, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    558: 8810001a  STALLWAIT    stall_res=8, wait_res=6  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0 | Wait.UNPACK1
    55c: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    560: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    564: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    568: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    56c: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    570: 01507033  and          x0, x0, x21
    574: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    578: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    57c: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834
    580: 001a0a13  addi         x20, x20, 1
    584: 010a1a13  slli         x20, x20, 16
    588: 010a5a13  srli         x20, x20, 16
    58c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    590: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    594: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834; write runtime value
    598: ffb49ab7  lui          x21, 0xffb49  # x21 = 0xffb49000
    59c: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb49020
    5a0: 014aa023  sw           x20, 0(x21)  # 0xffb49020; write runtime value
    5a4: 0ff0000f  fence        0xf, 0xf
    5a8: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    5ac: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    5b0: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830
    5b4: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5b8: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    5bc: 015a0a33  add          x20, x20, x21
    5c0: 00015b37  lui          x22, 0x00015  # x22 = 0x00015000
    5c4: 080b0b13  addi         x22, x22, 128  # x22 = 0x00015080
    5c8: 016a6663  bltu         x20, x22, 0x000005d4  # target 0x000005d4
    5cc: 00004bb7  lui          x23, 0x00004  # x23 = 0x00004000
    5d0: 417a0a33  sub          x20, x20, x23
loc_5d4:
    5d4: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    5d8: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    5dc: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830; write runtime value
    5e0: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    5e4: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_5e8:
    5e8: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    5ec: 0feafa93  andi         x21, x21, 254
    5f0: 000a8663  beq          x21, x0, 0x000005fc  # target 0x000005fc
    5f4: 0ff0000f  fence        0xf, 0xf
    5f8: ff1ff06f  jal          x0, 0x000005e8  # target 0x000005e8
loc_5fc:
    5fc: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    600: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    604: 830a8a93  addi         x21, x21, -2000  # x21 = 0xffb00830 · riscv_local_mem + 0x830
    608: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x830 · 0xffb00830
    60c: 004a5a13  srli         x20, x20, 4
    610: fffa0a13  addi         x20, x20, -1
    614: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    618: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    61c: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    620: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    624: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    628: c8140012  SETC16       setc16_reg=5, setc16_value=4  # thread_cfg[5] (current thread); SRCA_SET_Base = 0; SRCA_SET_SetOvrdWithAddr = 1
    62c: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    630: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_634:
    634: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    638: 0feafa93  andi         x21, x21, 254
    63c: 000a8663  beq          x21, x0, 0x00000648  # target 0x00000648
    640: 0ff0000f  fence        0xf, 0xf
    644: ff1ff06f  jal          x0, 0x00000634  # target 0x00000634
loc_648:
    648: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    64c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    650: 828a8a93  addi         x21, x21, -2008  # x21 = 0xffb00828 · riscv_local_mem + 0x828
    654: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x828 · 0xffb00828
    658: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    65c: 015a0a33  add          x20, x20, x21
    660: 00011b37  lui          x22, 0x00011  # x22 = 0x00011000
    664: 080b0b13  addi         x22, x22, 128  # x22 = 0x00011080
    668: 016a6663  bltu         x20, x22, 0x00000674  # target 0x00000674
    66c: 00002ab7  lui          x21, 0x00002  # x21 = 0x00002000
    670: 415a0a33  sub          x20, x20, x21
loc_674:
    674: 004a5a13  srli         x20, x20, 4
    678: fffa0a13  addi         x20, x20, -1
    67c: ffef0bb7  lui          x23, 0xffef0  # x23 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    680: 1f0b8b93  addi         x23, x23, 496  # x23 = 0xffef01f0 · cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address
    684: 014ba023  sw           x20, 0(x23)  # cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address · 0xffef01f0; write runtime value; cfg[124] (bank 0); THCON_SEC1_REG3_Base_address = runtime
    688: 014ba223  sw           x20, 4(x23)  # cfg[125] (bank 0) · THCON_SEC1_REG3_Base_cntx1_address · 0xffef01f4; write runtime value; cfg[125] (bank 0); THCON_SEC1_REG3_Base_cntx1_address = runtime
    68c: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    690: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    694: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    698: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    69c: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    6a0: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    6a4: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    6a8: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    6ac: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    6b0: 834c0c13  addi         x24, x24, -1996  # x24 = 0xffb00834 · riscv_local_mem + 0x834
    6b4: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x834 · 0xffb00834
    6b8: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_6bc:
    6bc: ffb49c37  lui          x24, 0xffb49  # x24 = 0xffb49000
    6c0: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb49028
    6c4: 000c5a83  lhu          x21, 0(x24)  # 0xffb49028
    6c8: 414a8b33  sub          x22, x21, x20
    6cc: 010b1b13  slli         x22, x22, 16
    6d0: 010b5b13  srli         x22, x22, 16
    6d4: 017b7663  bgeu         x22, x23, 0x000006e0  # target 0x000006e0
    6d8: 0ff0000f  fence        0xf, 0xf
    6dc: fe1ff06f  jal          x0, 0x000006bc  # target 0x000006bc
loc_6e0:
    6e0: 0ff0000f  fence        0xf, 0xf
    6e4: 88100182  STALLWAIT    stall_res=8, wait_res=96  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR | Wait.SRCB_CLR
    6e8: 78bff001  SETADCXX     CntSetMask=1, x_end2=1023, x_start=0
    6ec: 793ff001  SETADCXX     CntSetMask=2, x_end2=1023, x_start=0
    6f0: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    6f4: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    6f8: 0a000305  UNPACR       Unpack_block_selection=1, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    6fc: 08000305  UNPACR       Unpack_block_selection=0, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    700: 8810001a  STALLWAIT    stall_res=8, wait_res=6  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0 | Wait.UNPACK1
    704: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    708: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    70c: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    710: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    714: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    718: 01507033  and          x0, x0, x21
    71c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    720: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    724: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834
    728: 001a0a13  addi         x20, x20, 1
    72c: 010a1a13  slli         x20, x20, 16
    730: 010a5a13  srli         x20, x20, 16
    734: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    738: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    73c: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834; write runtime value
    740: ffb49ab7  lui          x21, 0xffb49  # x21 = 0xffb49000
    744: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb49020
    748: 014aa023  sw           x20, 0(x21)  # 0xffb49020; write runtime value
    74c: 0ff0000f  fence        0xf, 0xf
    750: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    754: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    758: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830
    75c: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    760: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    764: 015a0a33  add          x20, x20, x21
    768: 00015b37  lui          x22, 0x00015  # x22 = 0x00015000
    76c: 080b0b13  addi         x22, x22, 128  # x22 = 0x00015080
    770: 016a6663  bltu         x20, x22, 0x0000077c  # target 0x0000077c
    774: 00004bb7  lui          x23, 0x00004  # x23 = 0x00004000
    778: 417a0a33  sub          x20, x20, x23
loc_77c:
    77c: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    780: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    784: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830; write runtime value
    788: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    78c: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_790:
    790: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    794: 0feafa93  andi         x21, x21, 254
    798: 000a8663  beq          x21, x0, 0x000007a4  # target 0x000007a4
    79c: 0ff0000f  fence        0xf, 0xf
    7a0: ff1ff06f  jal          x0, 0x00000790  # target 0x00000790
loc_7a4:
    7a4: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    7a8: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    7ac: 830a8a93  addi         x21, x21, -2000  # x21 = 0xffb00830 · riscv_local_mem + 0x830
    7b0: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x830 · 0xffb00830
    7b4: 004a5a13  srli         x20, x20, 4
    7b8: fffa0a13  addi         x20, x20, -1
    7bc: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    7c0: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    7c4: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    7c8: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    7cc: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    7d0: c8140012  SETC16       setc16_reg=5, setc16_value=4  # thread_cfg[5] (current thread); SRCA_SET_Base = 0; SRCA_SET_SetOvrdWithAddr = 1
    7d4: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    7d8: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_7dc:
    7dc: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    7e0: 0feafa93  andi         x21, x21, 254
    7e4: 000a8663  beq          x21, x0, 0x000007f0  # target 0x000007f0
    7e8: 0ff0000f  fence        0xf, 0xf
    7ec: ff1ff06f  jal          x0, 0x000007dc  # target 0x000007dc
loc_7f0:
    7f0: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    7f4: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    7f8: 828a8a93  addi         x21, x21, -2008  # x21 = 0xffb00828 · riscv_local_mem + 0x828
    7fc: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x828 · 0xffb00828
    800: 00002ab7  lui          x21, 0x00002  # x21 = 0x00002000
    804: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00001800
    808: 015a0a33  add          x20, x20, x21
    80c: 00011b37  lui          x22, 0x00011  # x22 = 0x00011000
    810: 080b0b13  addi         x22, x22, 128  # x22 = 0x00011080
    814: 016a6663  bltu         x20, x22, 0x00000820  # target 0x00000820
    818: 00002ab7  lui          x21, 0x00002  # x21 = 0x00002000
    81c: 415a0a33  sub          x20, x20, x21
loc_820:
    820: 004a5a13  srli         x20, x20, 4
    824: fffa0a13  addi         x20, x20, -1
    828: ffef0bb7  lui          x23, 0xffef0  # x23 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    82c: 1f0b8b93  addi         x23, x23, 496  # x23 = 0xffef01f0 · cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address
    830: 014ba023  sw           x20, 0(x23)  # cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address · 0xffef01f0; write runtime value; cfg[124] (bank 0); THCON_SEC1_REG3_Base_address = runtime
    834: 014ba223  sw           x20, 4(x23)  # cfg[125] (bank 0) · THCON_SEC1_REG3_Base_cntx1_address · 0xffef01f4; write runtime value; cfg[125] (bank 0); THCON_SEC1_REG3_Base_cntx1_address = runtime
    838: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    83c: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    840: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    844: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    848: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    84c: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    850: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    854: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    858: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    85c: 834c0c13  addi         x24, x24, -1996  # x24 = 0xffb00834 · riscv_local_mem + 0x834
    860: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x834 · 0xffb00834
    864: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_868:
    868: ffb49c37  lui          x24, 0xffb49  # x24 = 0xffb49000
    86c: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb49028
    870: 000c5a83  lhu          x21, 0(x24)  # 0xffb49028
    874: 414a8b33  sub          x22, x21, x20
    878: 010b1b13  slli         x22, x22, 16
    87c: 010b5b13  srli         x22, x22, 16
    880: 017b7663  bgeu         x22, x23, 0x0000088c  # target 0x0000088c
    884: 0ff0000f  fence        0xf, 0xf
    888: fe1ff06f  jal          x0, 0x00000868  # target 0x00000868
loc_88c:
    88c: 0ff0000f  fence        0xf, 0xf
    890: 88100182  STALLWAIT    stall_res=8, wait_res=96  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR | Wait.SRCB_CLR
    894: 78bff001  SETADCXX     CntSetMask=1, x_end2=1023, x_start=0
    898: 793ff001  SETADCXX     CntSetMask=2, x_end2=1023, x_start=0
    89c: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    8a0: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    8a4: 0a000305  UNPACR       Unpack_block_selection=1, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    8a8: 08000305  UNPACR       Unpack_block_selection=0, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    8ac: 8810001a  STALLWAIT    stall_res=8, wait_res=6  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0 | Wait.UNPACK1
    8b0: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    8b4: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    8b8: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    8bc: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    8c0: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    8c4: 01507033  and          x0, x0, x21
    8c8: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    8cc: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    8d0: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834
    8d4: 001a0a13  addi         x20, x20, 1
    8d8: 010a1a13  slli         x20, x20, 16
    8dc: 010a5a13  srli         x20, x20, 16
    8e0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    8e4: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    8e8: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834; write runtime value
    8ec: ffb49ab7  lui          x21, 0xffb49  # x21 = 0xffb49000
    8f0: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb49020
    8f4: 014aa023  sw           x20, 0(x21)  # 0xffb49020; write runtime value
    8f8: 0ff0000f  fence        0xf, 0xf
    8fc: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    900: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    904: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830
    908: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    90c: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    910: 015a0a33  add          x20, x20, x21
    914: 00015b37  lui          x22, 0x00015  # x22 = 0x00015000
    918: 080b0b13  addi         x22, x22, 128  # x22 = 0x00015080
    91c: 016a6663  bltu         x20, x22, 0x00000928  # target 0x00000928
    920: 00004bb7  lui          x23, 0x00004  # x23 = 0x00004000
    924: 417a0a33  sub          x20, x20, x23
loc_928:
    928: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    92c: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    930: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830; write runtime value
    934: ffe803b7  lui          x7, 0xffe80  # x7 = 0xffe80000 · tensix_pc_buf + 0x0
    938: 03438393  addi         x7, x7, 52  # x7 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_93c:
    93c: 0003a403  lw           x8, 0(x7)  # UNPACK_CONFIG_SYNC · 0xffe80034
    940: 0fe47413  andi         x8, x8, 254
    944: 00040663  beq          x8, x0, 0x00000950  # target 0x00000950
    948: 0ff0000f  fence        0xf, 0xf
    94c: ff1ff06f  jal          x0, 0x0000093c  # target 0x0000093c
loc_950:
    950: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    954: d500011e  RMWCIB2      Mask=64, Data=0, CfgRegAddr=71  # cfg[71] (current thread StateID); THCON_SEC0_REG1_Unp_LF8_4b_exp = 0
    958: ffef03b7  lui          x7, 0xffef0  # x7 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    95c: 10038393  addi         x7, x7, 256  # x7 = 0xffef0100 · cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor
    960: 01500413  addi         x8, x0, 21  # x8 = 0x00000015
    964: 0083a023  sw           x8, 0(x7)  # cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor · 0xffef0100; write 0x00000015; cfg[64] (bank 0); THCON_SEC0_REG0_TileDescriptor = 21
    968: 00040437  lui          x8, 0x00040  # x8 = 0x00040000
    96c: 00140413  addi         x8, x8, 1  # x8 = 0x00040001
    970: 0083a223  sw           x8, 4(x7)  # cfg[65] (bank 0) (undocumented index) · 0xffef0104; write 0x00040001; cfg[65] (bank 0) · fields not in ttsim
    974: 0003a423  sw           x0, 8(x7)  # cfg[66] (bank 0) (undocumented index) · 0xffef0108; write 0x00000000; cfg[66] (bank 0) · fields not in ttsim
    978: 0003a623  sw           x0, 12(x7)  # cfg[67] (bank 0) (undocumented index) · 0xffef010c; write 0x00000000; cfg[67] (bank 0) · fields not in ttsim
    97c: 02500413  addi         x8, x0, 37  # x8 = 0x00000025
    980: 0283a023  sw           x8, 32(x7)  # cfg[72] (bank 0) · THCON_SEC0_REG2_Out_data_format, THCON_SEC0_REG2_Throttle_mode, THCON_SEC0_REG2_Context_count, THCON_SEC0_REG2_Haloize_mode, THCON_SEC0_REG2_Tileize_mode, THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC0_REG2_Unpack_If_Sel, THCON_SEC0_REG2_Upsample_rate, THCON_SEC0_REG2_Ovrd_data_format, THCON_SEC0_REG2_Upsample_and_interleave, THCON_SEC0_REG2_Shift_amount_cntx0, THCON_SEC0_REG2_Shift_amount_cntx1, THCON_SEC0_REG2_Shift_amount_cntx2, THCON_SEC0_REG2_Shift_amount_cntx3 · 0xffef0120; write 0x00000025; cfg[72] (bank 0); THCON_SEC0_REG2_Out_data_format = 5; THCON_SEC0_REG2_Throttle_mode = 2; THCON_SEC0_REG2_Context_count = 0; THCON_SEC0_REG2_Haloize_mode = 0; THCON_SEC0_REG2_Tileize_mode = 0; THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC0_REG2_Unpack_If_Sel = 0; THCON_SEC0_REG2_Upsample_rate = 0; THCON_SEC0_REG2_Ovrd_data_format = 0; THCON_SEC0_REG2_Upsample_and_interleave = 0; THCON_SEC0_REG2_Shift_amount_cntx0 = 0; THCON_SEC0_REG2_Shift_amount_cntx1 = 0; THCON_SEC0_REG2_Shift_amount_cntx2 = 0; THCON_SEC0_REG2_Shift_amount_cntx3 = 0
    984: 00300413  addi         x8, x0, 3  # x8 = 0x00000003
    988: 0283a223  sw           x8, 36(x7)  # cfg[73] (bank 0) · THCON_SEC0_REG2_Disable_zero_compress_cntx0, THCON_SEC0_REG2_Disable_zero_compress_cntx1, THCON_SEC0_REG2_Disable_zero_compress_cntx2, THCON_SEC0_REG2_Disable_zero_compress_cntx3, THCON_SEC0_REG2_Unpack_if_sel_cntx0, THCON_SEC0_REG2_Unpack_if_sel_cntx1, THCON_SEC0_REG2_Unpack_if_sel_cntx2, THCON_SEC0_REG2_Unpack_if_sel_cntx3, THCON_SEC0_REG2_Force_shared_exp, THCON_SEC0_REG2_Context_count_non_log2, THCON_SEC0_REG2_Context_count_non_log2_en, THCON_SEC0_REG2_Disable_zero_compress_cntx4, THCON_SEC0_REG2_Disable_zero_compress_cntx5, THCON_SEC0_REG2_Disable_zero_compress_cntx6, THCON_SEC0_REG2_Disable_zero_compress_cntx7, THCON_SEC0_REG2_Unpack_if_sel_cntx4, THCON_SEC0_REG2_Unpack_if_sel_cntx5, THCON_SEC0_REG2_Unpack_if_sel_cntx6, THCON_SEC0_REG2_Unpack_if_sel_cntx7, THCON_SEC0_REG2_Metadata_x_end · 0xffef0124; write 0x00000003; cfg[73] (bank 0); THCON_SEC0_REG2_Disable_zero_compress_cntx0 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx1 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx2 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx3 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx0 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx1 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx2 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx3 = 0; THCON_SEC0_REG2_Force_shared_exp = 0; THCON_SEC0_REG2_Context_count_non_log2 = 0; THCON_SEC0_REG2_Context_count_non_log2_en = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx4 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx5 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx6 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx7 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx4 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx5 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx6 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx7 = 0; THCON_SEC0_REG2_Metadata_x_end = 0
    98c: 0203a423  sw           x0, 40(x7)  # cfg[74] (bank 0) · THCON_SEC0_REG2_Unpack_limit_address · 0xffef0128; write 0x00000000; cfg[74] (bank 0); THCON_SEC0_REG2_Unpack_limit_address = 0
    990: 0203a623  sw           x0, 44(x7)  # cfg[75] (bank 0) · THCON_SEC0_REG2_Unpack_fifo_size · 0xffef012c; write 0x00000000; cfg[75] (bank 0); THCON_SEC0_REG2_Unpack_fifo_size = 0
    994: fa03a823  sw           x0, -80(x7)  # cfg[44] (bank 0) · UNP0_ADDR_CTRL_XY_REG_0_Xstride, UNP0_ADDR_CTRL_XY_REG_0_Ystride · 0xffef00b0; write 0x00000000; cfg[44] (bank 0); UNP0_ADDR_CTRL_XY_REG_0_Xstride = 0; UNP0_ADDR_CTRL_XY_REG_0_Ystride = 0
    998: fa03aa23  sw           x0, -76(x7)  # cfg[45] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_0_Zstride, UNP0_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef00b4; write 0x00000000; cfg[45] (bank 0); UNP0_ADDR_CTRL_ZW_REG_0_Zstride = 0; UNP0_ADDR_CTRL_ZW_REG_0_Wstride = 0
    99c: 00200437  lui          x8, 0x00200  # x8 = 0x00200000
    9a0: 00240413  addi         x8, x8, 2  # x8 = 0x00200002
    9a4: fe83a023  sw           x8, -32(x7)  # cfg[56] (bank 0) · UNP0_ADDR_CTRL_XY_REG_1_Xstride, UNP0_ADDR_CTRL_XY_REG_1_Ystride · 0xffef00e0; write 0x00200002; cfg[56] (bank 0); UNP0_ADDR_CTRL_XY_REG_1_Xstride = 2; UNP0_ADDR_CTRL_XY_REG_1_Ystride = 32
    9a8: 20000413  addi         x8, x0, 512  # x8 = 0x00000200
    9ac: fe83a223  sw           x8, -28(x7)  # cfg[57] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_1_Zstride, UNP0_ADDR_CTRL_ZW_REG_1_Wstride · 0xffef00e4; write 0x00000200; cfg[57] (bank 0); UNP0_ADDR_CTRL_ZW_REG_1_Zstride = 512; UNP0_ADDR_CTRL_ZW_REG_1_Wstride = 0
    9b0: fc03a023  sw           x0, -64(x7)  # cfg[48] (bank 0) · UNP0_ADDR_BASE_REG_0_Base · 0xffef00c0; write 0x00000000; cfg[48] (bank 0); UNP0_ADDR_BASE_REG_0_Base = 0
    9b4: fc03a223  sw           x0, -60(x7)  # cfg[49] (bank 0) · UNP0_ADDR_BASE_REG_1_Base · 0xffef00c4; write 0x00000000; cfg[49] (bank 0); UNP0_ADDR_BASE_REG_1_Base = 0
    9b8: 10000413  addi         x8, x0, 256  # x8 = 0x00000100
    9bc: fc83a423  sw           x8, -56(x7)  # cfg[50] (bank 0) · UNP0_FORCED_SHARED_EXP_shared_exp, UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr · 0xffef00c8; write 0x00000100; cfg[50] (bank 0); UNP0_FORCED_SHARED_EXP_shared_exp = 0; UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr = 1
    9c0: fc03aa23  sw           x0, -44(x7)  # cfg[53] (bank 0) · UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val · 0xffef00d4; write 0x00000000; cfg[53] (bank 0); UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val = 0
    9c4: 00400437  lui          x8, 0x00400  # x8 = 0x00400000
    9c8: 04040413  addi         x8, x8, 64  # x8 = 0x00400040
    9cc: 0483a823  sw           x8, 80(x7)  # cfg[84] (bank 0) · THCON_SEC0_REG5_Dest_cntx0_address, THCON_SEC0_REG5_Dest_cntx1_address · 0xffef0150; write 0x00400040; cfg[84] (bank 0); THCON_SEC0_REG5_Dest_cntx0_address = 64; THCON_SEC0_REG5_Dest_cntx1_address = 64
    9d0: 01000437  lui          x8, 0x01000  # x8 = 0x01000000
    9d4: 10040413  addi         x8, x8, 256  # x8 = 0x01000100
    9d8: 0483ac23  sw           x8, 88(x7)  # cfg[86] (bank 0) · THCON_SEC0_REG5_Tile_x_dim_cntx0, THCON_SEC0_REG5_Tile_x_dim_cntx1 · 0xffef0158; write 0x01000100; cfg[86] (bank 0); THCON_SEC0_REG5_Tile_x_dim_cntx0 = 256; THCON_SEC0_REG5_Tile_x_dim_cntx1 = 256
    9dc: 0603a823  sw           x0, 112(x7)  # cfg[92] (bank 0) · THCON_SEC0_REG7_Offset_address, THCON_SEC0_REG7_Unpack_data_format_cntx0, THCON_SEC0_REG7_Unpack_out_data_format_cntx0, THCON_SEC0_REG7_Unpack_data_format_cntx4, THCON_SEC0_REG7_Unpack_out_data_format_cntx4 · 0xffef0170; write 0x00000000; cfg[92] (bank 0); THCON_SEC0_REG7_Offset_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx4 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx4 = 0
    9e0: 0603aa23  sw           x0, 116(x7)  # cfg[93] (bank 0) · THCON_SEC0_REG7_Offset_cntx1_address, THCON_SEC0_REG7_Unpack_data_format_cntx1, THCON_SEC0_REG7_Unpack_out_data_format_cntx1, THCON_SEC0_REG7_Unpack_data_format_cntx5, THCON_SEC0_REG7_Unpack_out_data_format_cntx5 · 0xffef0174; write 0x00000000; cfg[93] (bank 0); THCON_SEC0_REG7_Offset_cntx1_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx5 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx5 = 0
    9e4: d50001de  RMWCIB2      Mask=64, Data=0, CfgRegAddr=119  # cfg[119] (current thread StateID); THCON_SEC1_REG1_Unp_LF8_4b_exp = 0
    9e8: ffef03b7  lui          x7, 0xffef0  # x7 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    9ec: 1c038393  addi         x7, x7, 448  # x7 = 0xffef01c0 · cfg[112] (bank 0) · THCON_SEC1_REG0_TileDescriptor
    9f0: 01000437  lui          x8, 0x01000  # x8 = 0x01000000
    9f4: 01540413  addi         x8, x8, 21  # x8 = 0x01000015
    9f8: 0083a023  sw           x8, 0(x7)  # cfg[112] (bank 0) · THCON_SEC1_REG0_TileDescriptor · 0xffef01c0; write 0x01000015; cfg[112] (bank 0); THCON_SEC1_REG0_TileDescriptor = 16777237
    9fc: 00040437  lui          x8, 0x00040  # x8 = 0x00040000
    a00: 00140413  addi         x8, x8, 1  # x8 = 0x00040001
    a04: 0083a223  sw           x8, 4(x7)  # cfg[113] (bank 0) (undocumented index) · 0xffef01c4; write 0x00040001; cfg[113] (bank 0) · fields not in ttsim
    a08: 0003a423  sw           x0, 8(x7)  # cfg[114] (bank 0) (undocumented index) · 0xffef01c8; write 0x00000000; cfg[114] (bank 0) · fields not in ttsim
    a0c: 0003a623  sw           x0, 12(x7)  # cfg[115] (bank 0) (undocumented index) · 0xffef01cc; write 0x00000000; cfg[115] (bank 0) · fields not in ttsim
    a10: 02500413  addi         x8, x0, 37  # x8 = 0x00000025
    a14: 0283a023  sw           x8, 32(x7)  # cfg[120] (bank 0) · THCON_SEC1_REG2_Out_data_format, THCON_SEC1_REG2_Throttle_mode, THCON_SEC1_REG2_Context_count, THCON_SEC1_REG2_Haloize_mode, THCON_SEC1_REG2_Tileize_mode, THCON_SEC1_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC1_REG2_Unpack_If_Sel, THCON_SEC1_REG2_Upsample_rate, THCON_SEC1_REG2_Ovrd_data_format, THCON_SEC1_REG2_Upsample_and_interleave, THCON_SEC1_REG2_Shift_amount_cntx0, THCON_SEC1_REG2_Shift_amount_cntx1, THCON_SEC1_REG2_Shift_amount_cntx2, THCON_SEC1_REG2_Shift_amount_cntx3 · 0xffef01e0; write 0x00000025; cfg[120] (bank 0); THCON_SEC1_REG2_Out_data_format = 5; THCON_SEC1_REG2_Throttle_mode = 2; THCON_SEC1_REG2_Context_count = 0; THCON_SEC1_REG2_Haloize_mode = 0; THCON_SEC1_REG2_Tileize_mode = 0; THCON_SEC1_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC1_REG2_Unpack_If_Sel = 0; THCON_SEC1_REG2_Upsample_rate = 0; THCON_SEC1_REG2_Ovrd_data_format = 0; THCON_SEC1_REG2_Upsample_and_interleave = 0; THCON_SEC1_REG2_Shift_amount_cntx0 = 0; THCON_SEC1_REG2_Shift_amount_cntx1 = 0; THCON_SEC1_REG2_Shift_amount_cntx2 = 0; THCON_SEC1_REG2_Shift_amount_cntx3 = 0
    a18: 00300413  addi         x8, x0, 3  # x8 = 0x00000003
    a1c: 0283a223  sw           x8, 36(x7)  # cfg[121] (bank 0) · THCON_SEC1_REG2_Disable_zero_compress_cntx0, THCON_SEC1_REG2_Disable_zero_compress_cntx1, THCON_SEC1_REG2_Disable_zero_compress_cntx2, THCON_SEC1_REG2_Disable_zero_compress_cntx3, THCON_SEC1_REG2_Unpack_if_sel_cntx0, THCON_SEC1_REG2_Unpack_if_sel_cntx1, THCON_SEC1_REG2_Unpack_if_sel_cntx2, THCON_SEC1_REG2_Unpack_if_sel_cntx3, THCON_SEC1_REG2_Force_shared_exp, THCON_SEC1_REG2_Context_count_non_log2, THCON_SEC1_REG2_Context_count_non_log2_en, THCON_SEC1_REG2_Disable_zero_compress_cntx4, THCON_SEC1_REG2_Disable_zero_compress_cntx5, THCON_SEC1_REG2_Disable_zero_compress_cntx6, THCON_SEC1_REG2_Disable_zero_compress_cntx7, THCON_SEC1_REG2_Unpack_if_sel_cntx4, THCON_SEC1_REG2_Unpack_if_sel_cntx5, THCON_SEC1_REG2_Unpack_if_sel_cntx6, THCON_SEC1_REG2_Unpack_if_sel_cntx7, THCON_SEC1_REG2_Metadata_x_end · 0xffef01e4; write 0x00000003; cfg[121] (bank 0); THCON_SEC1_REG2_Disable_zero_compress_cntx0 = 1; THCON_SEC1_REG2_Disable_zero_compress_cntx1 = 1; THCON_SEC1_REG2_Disable_zero_compress_cntx2 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx3 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx0 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx1 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx2 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx3 = 0; THCON_SEC1_REG2_Force_shared_exp = 0; THCON_SEC1_REG2_Context_count_non_log2 = 0; THCON_SEC1_REG2_Context_count_non_log2_en = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx4 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx5 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx6 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx7 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx4 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx5 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx6 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx7 = 0; THCON_SEC1_REG2_Metadata_x_end = 0
    a20: 0203a423  sw           x0, 40(x7)  # cfg[122] (bank 0) · THCON_SEC1_REG2_Unpack_limit_address · 0xffef01e8; write 0x00000000; cfg[122] (bank 0); THCON_SEC1_REG2_Unpack_limit_address = 0
    a24: 0203a623  sw           x0, 44(x7)  # cfg[123] (bank 0) · THCON_SEC1_REG2_Unpack_fifo_size · 0xffef01ec; write 0x00000000; cfg[123] (bank 0); THCON_SEC1_REG2_Unpack_fifo_size = 0
    a28: ee03ac23  sw           x0, -264(x7)  # cfg[46] (bank 0) · UNP1_ADDR_CTRL_XY_REG_0_Xstride, UNP1_ADDR_CTRL_XY_REG_0_Ystride · 0xffef00b8; write 0x00000000; cfg[46] (bank 0); UNP1_ADDR_CTRL_XY_REG_0_Xstride = 0; UNP1_ADDR_CTRL_XY_REG_0_Ystride = 0
    a2c: ee03ae23  sw           x0, -260(x7)  # cfg[47] (bank 0) · UNP1_ADDR_CTRL_ZW_REG_0_Zstride, UNP1_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef00bc; write 0x00000000; cfg[47] (bank 0); UNP1_ADDR_CTRL_ZW_REG_0_Zstride = 0; UNP1_ADDR_CTRL_ZW_REG_0_Wstride = 0
    a30: 00200437  lui          x8, 0x00200  # x8 = 0x00200000
    a34: 00240413  addi         x8, x8, 2  # x8 = 0x00200002
    a38: f283a423  sw           x8, -216(x7)  # cfg[58] (bank 0) · UNP1_ADDR_CTRL_XY_REG_1_Xstride, UNP1_ADDR_CTRL_XY_REG_1_Ystride · 0xffef00e8; write 0x00200002; cfg[58] (bank 0); UNP1_ADDR_CTRL_XY_REG_1_Xstride = 2; UNP1_ADDR_CTRL_XY_REG_1_Ystride = 32
    a3c: 20000413  addi         x8, x0, 512  # x8 = 0x00000200
    a40: f283a623  sw           x8, -212(x7)  # cfg[59] (bank 0) · UNP1_ADDR_CTRL_ZW_REG_1_Zstride, UNP1_ADDR_CTRL_ZW_REG_1_Wstride · 0xffef00ec; write 0x00000200; cfg[59] (bank 0); UNP1_ADDR_CTRL_ZW_REG_1_Zstride = 512; UNP1_ADDR_CTRL_ZW_REG_1_Wstride = 0
    a44: f203a823  sw           x0, -208(x7)  # cfg[60] (bank 0) · UNP1_ADDR_BASE_REG_0_Base · 0xffef00f0; write 0x00000000; cfg[60] (bank 0); UNP1_ADDR_BASE_REG_0_Base = 0
    a48: f203aa23  sw           x0, -204(x7)  # cfg[61] (bank 0) · UNP1_ADDR_BASE_REG_1_Base · 0xffef00f4; write 0x00000000; cfg[61] (bank 0); UNP1_ADDR_BASE_REG_1_Base = 0
    a4c: f203ac23  sw           x0, -200(x7)  # cfg[62] (bank 0) · UNP1_FORCED_SHARED_EXP_shared_exp, UNP1_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr · 0xffef00f8; write 0x00000000; cfg[62] (bank 0); UNP1_FORCED_SHARED_EXP_shared_exp = 0; UNP1_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr = 0
    a50: f203ae23  sw           x0, -196(x7)  # cfg[63] (bank 0) · UNP1_NOP_REG_CLR_VAL_nop_reg_clr_val · 0xffef00fc; write 0x00000000; cfg[63] (bank 0); UNP1_NOP_REG_CLR_VAL_nop_reg_clr_val = 0
    a54: 0403a823  sw           x0, 80(x7)  # cfg[132] (bank 0) · THCON_SEC1_REG5_Dest_cntx0_address, THCON_SEC1_REG5_Dest_cntx1_address · 0xffef0210; write 0x00000000; cfg[132] (bank 0); THCON_SEC1_REG5_Dest_cntx0_address = 0; THCON_SEC1_REG5_Dest_cntx1_address = 0
    a58: 01000437  lui          x8, 0x01000  # x8 = 0x01000000
    a5c: 10040413  addi         x8, x8, 256  # x8 = 0x01000100
    a60: 0483ac23  sw           x8, 88(x7)  # cfg[134] (bank 0) · THCON_SEC1_REG5_Tile_x_dim_cntx0, THCON_SEC1_REG5_Tile_x_dim_cntx1 · 0xffef0218; write 0x01000100; cfg[134] (bank 0); THCON_SEC1_REG5_Tile_x_dim_cntx0 = 256; THCON_SEC1_REG5_Tile_x_dim_cntx1 = 256
    a64: 0603a823  sw           x0, 112(x7)  # cfg[140] (bank 0) · THCON_SEC1_REG7_Offset_address, THCON_SEC1_REG7_Unpack_data_format_cntx0, THCON_SEC1_REG7_Unpack_out_data_format_cntx0, THCON_SEC1_REG7_Unpack_data_format_cntx4, THCON_SEC1_REG7_Unpack_out_data_format_cntx4 · 0xffef0230; write 0x00000000; cfg[140] (bank 0); THCON_SEC1_REG7_Offset_address = 0; THCON_SEC1_REG7_Unpack_data_format_cntx0 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx0 = 0; THCON_SEC1_REG7_Unpack_data_format_cntx4 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx4 = 0
    a68: 0603aa23  sw           x0, 116(x7)  # cfg[141] (bank 0) · THCON_SEC1_REG7_Offset_cntx1_address, THCON_SEC1_REG7_Unpack_data_format_cntx1, THCON_SEC1_REG7_Unpack_out_data_format_cntx1, THCON_SEC1_REG7_Unpack_data_format_cntx5, THCON_SEC1_REG7_Unpack_out_data_format_cntx5 · 0xffef0234; write 0x00000000; cfg[141] (bank 0); THCON_SEC1_REG7_Offset_cntx1_address = 0; THCON_SEC1_REG7_Unpack_data_format_cntx1 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx1 = 0; THCON_SEC1_REG7_Unpack_data_format_cntx5 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx5 = 0
    a6c: 328000ef  jal          x1, 0x00000d94  # target 0x00000d94; x1 = 0x00000a70
    a70: 324000ef  jal          x1, 0x00000d94  # target 0x00000d94; x1 = 0x00000a74
    a74: 320000ef  jal          x1, 0x00000d94  # target 0x00000d94; x1 = 0x00000a78
    a78: 31c000ef  jal          x1, 0x00000d94  # target 0x00000d94; x1 = 0x00000a7c
    a7c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    a80: 84440413  addi         x8, x8, -1980  # x8 = 0xffb00844 · riscv_local_mem + 0x844
    a84: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x844 · 0xffb00844
    a88: 00138393  addi         x7, x7, 1
    a8c: 01039393  slli         x7, x7, 16
    a90: 0103d393  srli         x7, x7, 16
    a94: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    a98: 84440413  addi         x8, x8, -1980  # x8 = 0xffb00844 · riscv_local_mem + 0x844
    a9c: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x844 · 0xffb00844; write runtime value
    aa0: ffb4b437  lui          x8, 0xffb4b  # x8 = 0xffb4b000
    aa4: 02040413  addi         x8, x8, 32  # x8 = 0xffb4b020
    aa8: 00742023  sw           x7, 0(x8)  # 0xffb4b020; write runtime value
    aac: 0ff0000f  fence        0xf, 0xf
    ab0: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    ab4: 84058593  addi         x11, x11, -1984  # x11 = 0xffb00840 · riscv_local_mem + 0x840
    ab8: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x840 · 0xffb00840
    abc: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    ac0: 80040413  addi         x8, x8, -2048  # x8 = 0x00000800
    ac4: 008383b3  add          x7, x7, x8
    ac8: 0001a4b7  lui          x9, 0x0001a  # x9 = 0x0001a000
    acc: 88048493  addi         x9, x9, -1920  # x9 = 0x00019880
    ad0: 0093e863  bltu         x7, x9, 0x00000ae0  # target 0x00000ae0
    ad4: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    ad8: 80050513  addi         x10, x10, -2048  # x10 = 0x00000800
    adc: 40a383b3  sub          x7, x7, x10
loc_ae0:
    ae0: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    ae4: 84058593  addi         x11, x11, -1984  # x11 = 0xffb00840 · riscv_local_mem + 0x840
    ae8: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x840 · 0xffb00840; write runtime value
    aec: 00128293  addi         x5, x5, 1
    af0: e7cff06f  jal          x0, 0x0000016c  # target 0x0000016c
loc_af4:
    af4: ffb01337  lui          x6, 0xffb01  # x6 = 0xffb01000
    af8: 82c30313  addi         x6, x6, -2004  # x6 = 0xffb0082c · riscv_local_mem + 0x82c
    afc: 00032283  lw           x5, 0(x6)  # riscv_local_mem + 0x82c · 0xffb0082c
    b00: 00428293  addi         x5, x5, 4
    b04: 01029293  slli         x5, x5, 16
    b08: 0102d293  srli         x5, x5, 16
    b0c: ffb01337  lui          x6, 0xffb01  # x6 = 0xffb01000
    b10: 82c30313  addi         x6, x6, -2004  # x6 = 0xffb0082c · riscv_local_mem + 0x82c
    b14: 00532023  sw           x5, 0(x6)  # riscv_local_mem + 0x82c · 0xffb0082c; write runtime value
    b18: ffb48337  lui          x6, 0xffb48  # x6 = 0xffb48000
    b1c: 02030313  addi         x6, x6, 32  # x6 = 0xffb48020
    b20: 00532023  sw           x5, 0(x6)  # 0xffb48020; write runtime value
    b24: 0ff0000f  fence        0xf, 0xf
    b28: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    b2c: 82848493  addi         x9, x9, -2008  # x9 = 0xffb00828 · riscv_local_mem + 0x828
    b30: 0004a283  lw           x5, 0(x9)  # riscv_local_mem + 0x828 · 0xffb00828
    b34: 00002337  lui          x6, 0x00002  # x6 = 0x00002000
    b38: 006282b3  add          x5, x5, x6
    b3c: 000113b7  lui          x7, 0x00011  # x7 = 0x00011000
    b40: 08038393  addi         x7, x7, 128  # x7 = 0x00011080
    b44: 0072e663  bltu         x5, x7, 0x00000b50  # target 0x00000b50
    b48: 00002437  lui          x8, 0x00002  # x8 = 0x00002000
    b4c: 408282b3  sub          x5, x5, x8
loc_b50:
    b50: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    b54: 82848493  addi         x9, x9, -2008  # x9 = 0xffb00828 · riscv_local_mem + 0x828
    b58: 0054a023  sw           x5, 0(x9)  # riscv_local_mem + 0x828 · 0xffb00828; write runtime value
loc_b5c:
    b5c: 4000006f  jal          x0, 0x00000f5c  # target 0x00000f5c
loc_b60:
    b60: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    b64: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_b68:
    b68: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    b6c: 0feafa93  andi         x21, x21, 254
    b70: 000a8663  beq          x21, x0, 0x00000b7c  # target 0x00000b7c
    b74: 0ff0000f  fence        0xf, 0xf
    b78: ff1ff06f  jal          x0, 0x00000b68  # target 0x00000b68
loc_b7c:
    b7c: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    b80: d500011e  RMWCIB2      Mask=64, Data=0, CfgRegAddr=71  # cfg[71] (current thread StateID); THCON_SEC0_REG1_Unp_LF8_4b_exp = 0
    b84: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    b88: 100a0a13  addi         x20, x20, 256  # x20 = 0xffef0100 · cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor
    b8c: 01500a93  addi         x21, x0, 21  # x21 = 0x00000015
    b90: 015a2023  sw           x21, 0(x20)  # cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor · 0xffef0100; write 0x00000015; cfg[64] (bank 0); THCON_SEC0_REG0_TileDescriptor = 21
    b94: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
    b98: 001a8a93  addi         x21, x21, 1  # x21 = 0x00040001
    b9c: 015a2223  sw           x21, 4(x20)  # cfg[65] (bank 0) (undocumented index) · 0xffef0104; write 0x00040001; cfg[65] (bank 0) · fields not in ttsim
    ba0: 000a2423  sw           x0, 8(x20)  # cfg[66] (bank 0) (undocumented index) · 0xffef0108; write 0x00000000; cfg[66] (bank 0) · fields not in ttsim
    ba4: 000a2623  sw           x0, 12(x20)  # cfg[67] (bank 0) (undocumented index) · 0xffef010c; write 0x00000000; cfg[67] (bank 0) · fields not in ttsim
    ba8: 02500a93  addi         x21, x0, 37  # x21 = 0x00000025
    bac: 035a2023  sw           x21, 32(x20)  # cfg[72] (bank 0) · THCON_SEC0_REG2_Out_data_format, THCON_SEC0_REG2_Throttle_mode, THCON_SEC0_REG2_Context_count, THCON_SEC0_REG2_Haloize_mode, THCON_SEC0_REG2_Tileize_mode, THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC0_REG2_Unpack_If_Sel, THCON_SEC0_REG2_Upsample_rate, THCON_SEC0_REG2_Ovrd_data_format, THCON_SEC0_REG2_Upsample_and_interleave, THCON_SEC0_REG2_Shift_amount_cntx0, THCON_SEC0_REG2_Shift_amount_cntx1, THCON_SEC0_REG2_Shift_amount_cntx2, THCON_SEC0_REG2_Shift_amount_cntx3 · 0xffef0120; write 0x00000025; cfg[72] (bank 0); THCON_SEC0_REG2_Out_data_format = 5; THCON_SEC0_REG2_Throttle_mode = 2; THCON_SEC0_REG2_Context_count = 0; THCON_SEC0_REG2_Haloize_mode = 0; THCON_SEC0_REG2_Tileize_mode = 0; THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC0_REG2_Unpack_If_Sel = 0; THCON_SEC0_REG2_Upsample_rate = 0; THCON_SEC0_REG2_Ovrd_data_format = 0; THCON_SEC0_REG2_Upsample_and_interleave = 0; THCON_SEC0_REG2_Shift_amount_cntx0 = 0; THCON_SEC0_REG2_Shift_amount_cntx1 = 0; THCON_SEC0_REG2_Shift_amount_cntx2 = 0; THCON_SEC0_REG2_Shift_amount_cntx3 = 0
    bb0: 00300a93  addi         x21, x0, 3  # x21 = 0x00000003
    bb4: 035a2223  sw           x21, 36(x20)  # cfg[73] (bank 0) · THCON_SEC0_REG2_Disable_zero_compress_cntx0, THCON_SEC0_REG2_Disable_zero_compress_cntx1, THCON_SEC0_REG2_Disable_zero_compress_cntx2, THCON_SEC0_REG2_Disable_zero_compress_cntx3, THCON_SEC0_REG2_Unpack_if_sel_cntx0, THCON_SEC0_REG2_Unpack_if_sel_cntx1, THCON_SEC0_REG2_Unpack_if_sel_cntx2, THCON_SEC0_REG2_Unpack_if_sel_cntx3, THCON_SEC0_REG2_Force_shared_exp, THCON_SEC0_REG2_Context_count_non_log2, THCON_SEC0_REG2_Context_count_non_log2_en, THCON_SEC0_REG2_Disable_zero_compress_cntx4, THCON_SEC0_REG2_Disable_zero_compress_cntx5, THCON_SEC0_REG2_Disable_zero_compress_cntx6, THCON_SEC0_REG2_Disable_zero_compress_cntx7, THCON_SEC0_REG2_Unpack_if_sel_cntx4, THCON_SEC0_REG2_Unpack_if_sel_cntx5, THCON_SEC0_REG2_Unpack_if_sel_cntx6, THCON_SEC0_REG2_Unpack_if_sel_cntx7, THCON_SEC0_REG2_Metadata_x_end · 0xffef0124; write 0x00000003; cfg[73] (bank 0); THCON_SEC0_REG2_Disable_zero_compress_cntx0 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx1 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx2 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx3 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx0 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx1 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx2 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx3 = 0; THCON_SEC0_REG2_Force_shared_exp = 0; THCON_SEC0_REG2_Context_count_non_log2 = 0; THCON_SEC0_REG2_Context_count_non_log2_en = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx4 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx5 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx6 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx7 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx4 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx5 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx6 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx7 = 0; THCON_SEC0_REG2_Metadata_x_end = 0
    bb8: 020a2423  sw           x0, 40(x20)  # cfg[74] (bank 0) · THCON_SEC0_REG2_Unpack_limit_address · 0xffef0128; write 0x00000000; cfg[74] (bank 0); THCON_SEC0_REG2_Unpack_limit_address = 0
    bbc: 020a2623  sw           x0, 44(x20)  # cfg[75] (bank 0) · THCON_SEC0_REG2_Unpack_fifo_size · 0xffef012c; write 0x00000000; cfg[75] (bank 0); THCON_SEC0_REG2_Unpack_fifo_size = 0
    bc0: fa0a2823  sw           x0, -80(x20)  # cfg[44] (bank 0) · UNP0_ADDR_CTRL_XY_REG_0_Xstride, UNP0_ADDR_CTRL_XY_REG_0_Ystride · 0xffef00b0; write 0x00000000; cfg[44] (bank 0); UNP0_ADDR_CTRL_XY_REG_0_Xstride = 0; UNP0_ADDR_CTRL_XY_REG_0_Ystride = 0
    bc4: fa0a2a23  sw           x0, -76(x20)  # cfg[45] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_0_Zstride, UNP0_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef00b4; write 0x00000000; cfg[45] (bank 0); UNP0_ADDR_CTRL_ZW_REG_0_Zstride = 0; UNP0_ADDR_CTRL_ZW_REG_0_Wstride = 0
    bc8: 00200ab7  lui          x21, 0x00200  # x21 = 0x00200000
    bcc: 002a8a93  addi         x21, x21, 2  # x21 = 0x00200002
    bd0: ff5a2023  sw           x21, -32(x20)  # cfg[56] (bank 0) · UNP0_ADDR_CTRL_XY_REG_1_Xstride, UNP0_ADDR_CTRL_XY_REG_1_Ystride · 0xffef00e0; write 0x00200002; cfg[56] (bank 0); UNP0_ADDR_CTRL_XY_REG_1_Xstride = 2; UNP0_ADDR_CTRL_XY_REG_1_Ystride = 32
    bd4: 20000a93  addi         x21, x0, 512  # x21 = 0x00000200
    bd8: ff5a2223  sw           x21, -28(x20)  # cfg[57] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_1_Zstride, UNP0_ADDR_CTRL_ZW_REG_1_Wstride · 0xffef00e4; write 0x00000200; cfg[57] (bank 0); UNP0_ADDR_CTRL_ZW_REG_1_Zstride = 512; UNP0_ADDR_CTRL_ZW_REG_1_Wstride = 0
    bdc: fc0a2023  sw           x0, -64(x20)  # cfg[48] (bank 0) · UNP0_ADDR_BASE_REG_0_Base · 0xffef00c0; write 0x00000000; cfg[48] (bank 0); UNP0_ADDR_BASE_REG_0_Base = 0
    be0: fc0a2223  sw           x0, -60(x20)  # cfg[49] (bank 0) · UNP0_ADDR_BASE_REG_1_Base · 0xffef00c4; write 0x00000000; cfg[49] (bank 0); UNP0_ADDR_BASE_REG_1_Base = 0
    be4: 10000a93  addi         x21, x0, 256  # x21 = 0x00000100
    be8: fd5a2423  sw           x21, -56(x20)  # cfg[50] (bank 0) · UNP0_FORCED_SHARED_EXP_shared_exp, UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr · 0xffef00c8; write 0x00000100; cfg[50] (bank 0); UNP0_FORCED_SHARED_EXP_shared_exp = 0; UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr = 1
    bec: fc0a2a23  sw           x0, -44(x20)  # cfg[53] (bank 0) · UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val · 0xffef00d4; write 0x00000000; cfg[53] (bank 0); UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val = 0
    bf0: 00400ab7  lui          x21, 0x00400  # x21 = 0x00400000
    bf4: 040a8a93  addi         x21, x21, 64  # x21 = 0x00400040
    bf8: 055a2823  sw           x21, 80(x20)  # cfg[84] (bank 0) · THCON_SEC0_REG5_Dest_cntx0_address, THCON_SEC0_REG5_Dest_cntx1_address · 0xffef0150; write 0x00400040; cfg[84] (bank 0); THCON_SEC0_REG5_Dest_cntx0_address = 64; THCON_SEC0_REG5_Dest_cntx1_address = 64
    bfc: 01000ab7  lui          x21, 0x01000  # x21 = 0x01000000
    c00: 100a8a93  addi         x21, x21, 256  # x21 = 0x01000100
    c04: 055a2c23  sw           x21, 88(x20)  # cfg[86] (bank 0) · THCON_SEC0_REG5_Tile_x_dim_cntx0, THCON_SEC0_REG5_Tile_x_dim_cntx1 · 0xffef0158; write 0x01000100; cfg[86] (bank 0); THCON_SEC0_REG5_Tile_x_dim_cntx0 = 256; THCON_SEC0_REG5_Tile_x_dim_cntx1 = 256
    c08: 060a2823  sw           x0, 112(x20)  # cfg[92] (bank 0) · THCON_SEC0_REG7_Offset_address, THCON_SEC0_REG7_Unpack_data_format_cntx0, THCON_SEC0_REG7_Unpack_out_data_format_cntx0, THCON_SEC0_REG7_Unpack_data_format_cntx4, THCON_SEC0_REG7_Unpack_out_data_format_cntx4 · 0xffef0170; write 0x00000000; cfg[92] (bank 0); THCON_SEC0_REG7_Offset_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx4 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx4 = 0
    c0c: 060a2a23  sw           x0, 116(x20)  # cfg[93] (bank 0) · THCON_SEC0_REG7_Offset_cntx1_address, THCON_SEC0_REG7_Unpack_data_format_cntx1, THCON_SEC0_REG7_Unpack_out_data_format_cntx1, THCON_SEC0_REG7_Unpack_data_format_cntx5, THCON_SEC0_REG7_Unpack_out_data_format_cntx5 · 0xffef0174; write 0x00000000; cfg[93] (bank 0); THCON_SEC0_REG7_Offset_cntx1_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx5 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx5 = 0
    c10: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    c14: 820a8a93  addi         x21, x21, -2016  # x21 = 0xffb00820 · riscv_local_mem + 0x820
    c18: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x820 · 0xffb00820
    c1c: 004a5a13  srli         x20, x20, 4
    c20: fffa0a13  addi         x20, x20, -1
    c24: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    c28: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    c2c: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    c30: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    c34: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    c38: c8140012  SETC16       setc16_reg=5, setc16_value=4  # thread_cfg[5] (current thread); SRCA_SET_Base = 0; SRCA_SET_SetOvrdWithAddr = 1
    c3c: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    c40: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    c44: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    c48: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    c4c: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    c50: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    c54: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    c58: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    c5c: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    c60: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    c64: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    c68: 01507033  and          x0, x0, x21
    c6c: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    c70: 00400a93  addi         x21, x0, 4  # x21 = 0x00000004
    c74: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000004
    c78: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
    c7c: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000001
    c80: 42008ab7  lui          x21, 0x42008  # x21 = 0x42008000
    c84: 0c1a8a93  addi         x21, x21, 193  # x21 = 0x420080c1
    c88: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x420080c1; MOP template instruction · UNPACR Unpack_block_selection=0, AddrMode=1, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    c8c: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    c90: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x02000000; MOP template instruction · NOP
    c94: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    c98: 43800ab7  lui          x21, 0x43800  # x21 = 0x43800000
    c9c: 101a8a93  addi         x21, x21, 257  # x21 = 0x43800101
    ca0: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    ca4: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    ca8: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    cac: 43800ab7  lui          x21, 0x43800  # x21 = 0x43800000
    cb0: 101a8a93  addi         x21, x21, 257  # x21 = 0x43800101
    cb4: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    cb8: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    cbc: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    cc0: 824c0c13  addi         x24, x24, -2012  # x24 = 0xffb00824 · riscv_local_mem + 0x824
    cc4: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x824 · 0xffb00824
    cc8: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_ccc:
    ccc: ffb4dc37  lui          x24, 0xffb4d  # x24 = 0xffb4d000
    cd0: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb4d028
    cd4: 000c5a83  lhu          x21, 0(x24)  # 0xffb4d028
    cd8: 414a8b33  sub          x22, x21, x20
    cdc: 010b1b13  slli         x22, x22, 16
    ce0: 010b5b13  srli         x22, x22, 16
    ce4: 017b7663  bgeu         x22, x23, 0x00000cf0  # target 0x00000cf0
    ce8: 0ff0000f  fence        0xf, 0xf
    cec: fe1ff06f  jal          x0, 0x00000ccc  # target 0x00000ccc
loc_cf0:
    cf0: 0ff0000f  fence        0xf, 0xf
    cf4: 88100082  STALLWAIT    stall_res=8, wait_res=32  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR
    cf8: 788ff001  SETADCXX     CntSetMask=1, x_end2=255, x_start=0
    cfc: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    d00: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    d04: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    d08: 8810000a  STALLWAIT    stall_res=8, wait_res=2  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0
    d0c: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    d10: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    d14: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    d18: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    d1c: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    d20: 01507033  and          x0, x0, x21
    d24: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    d28: 824a8a93  addi         x21, x21, -2012  # x21 = 0xffb00824 · riscv_local_mem + 0x824
    d2c: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x824 · 0xffb00824
    d30: 001a0a13  addi         x20, x20, 1
    d34: 010a1a13  slli         x20, x20, 16
    d38: 010a5a13  srli         x20, x20, 16
    d3c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    d40: 824a8a93  addi         x21, x21, -2012  # x21 = 0xffb00824 · riscv_local_mem + 0x824
    d44: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x824 · 0xffb00824; write runtime value
    d48: ffb4dab7  lui          x21, 0xffb4d  # x21 = 0xffb4d000
    d4c: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb4d020
    d50: 014aa023  sw           x20, 0(x21)  # 0xffb4d020; write runtime value
    d54: 0ff0000f  fence        0xf, 0xf
    d58: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    d5c: 820c0c13  addi         x24, x24, -2016  # x24 = 0xffb00820 · riscv_local_mem + 0x820
    d60: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x820 · 0xffb00820
    d64: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    d68: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    d6c: 015a0a33  add          x20, x20, x21
    d70: 00022b37  lui          x22, 0x00022  # x22 = 0x00022000
    d74: 880b0b13  addi         x22, x22, -1920  # x22 = 0x00021880
    d78: 016a6663  bltu         x20, x22, 0x00000d84  # target 0x00000d84
    d7c: 00002bb7  lui          x23, 0x00002  # x23 = 0x00002000
    d80: 417a0a33  sub          x20, x20, x23
loc_d84:
    d84: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    d88: 820c0c13  addi         x24, x24, -2016  # x24 = 0xffb00820 · riscv_local_mem + 0x820
    d8c: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x820 · 0xffb00820; write runtime value
    d90: 00008067  jalr         x0, 0(x1)
loc_d94:
    d94: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    d98: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_d9c:
    d9c: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    da0: 0feafa93  andi         x21, x21, 254
    da4: 000a8663  beq          x21, x0, 0x00000db0  # target 0x00000db0
    da8: 0ff0000f  fence        0xf, 0xf
    dac: ff1ff06f  jal          x0, 0x00000d9c  # target 0x00000d9c
loc_db0:
    db0: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    db4: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    db8: 838a8a93  addi         x21, x21, -1992  # x21 = 0xffb00838 · riscv_local_mem + 0x838
    dbc: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x838 · 0xffb00838
    dc0: 004a5a13  srli         x20, x20, 4
    dc4: fffa0a13  addi         x20, x20, -1
    dc8: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    dcc: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    dd0: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    dd4: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    dd8: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    ddc: c8140012  SETC16       setc16_reg=5, setc16_value=4  # thread_cfg[5] (current thread); SRCA_SET_Base = 0; SRCA_SET_SetOvrdWithAddr = 1
    de0: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    de4: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_de8:
    de8: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    dec: 0feafa93  andi         x21, x21, 254
    df0: 000a8663  beq          x21, x0, 0x00000dfc  # target 0x00000dfc
    df4: 0ff0000f  fence        0xf, 0xf
    df8: ff1ff06f  jal          x0, 0x00000de8  # target 0x00000de8
loc_dfc:
    dfc: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    e00: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    e04: 840a8a93  addi         x21, x21, -1984  # x21 = 0xffb00840 · riscv_local_mem + 0x840
    e08: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x840 · 0xffb00840
    e0c: 004a5a13  srli         x20, x20, 4
    e10: fffa0a13  addi         x20, x20, -1
    e14: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    e18: 1f0a8a93  addi         x21, x21, 496  # x21 = 0xffef01f0 · cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address
    e1c: 014aa023  sw           x20, 0(x21)  # cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address · 0xffef01f0; write runtime value; cfg[124] (bank 0); THCON_SEC1_REG3_Base_address = runtime
    e20: 014aa223  sw           x20, 4(x21)  # cfg[125] (bank 0) · THCON_SEC1_REG3_Base_cntx1_address · 0xffef01f4; write runtime value; cfg[125] (bank 0); THCON_SEC1_REG3_Base_cntx1_address = runtime
    e24: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    e28: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    e2c: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    e30: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    e34: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    e38: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    e3c: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    e40: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    e44: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    e48: 844c0c13  addi         x24, x24, -1980  # x24 = 0xffb00844 · riscv_local_mem + 0x844
    e4c: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x844 · 0xffb00844
    e50: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_e54:
    e54: ffb4bc37  lui          x24, 0xffb4b  # x24 = 0xffb4b000
    e58: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb4b028
    e5c: 000c5a83  lhu          x21, 0(x24)  # 0xffb4b028
    e60: 414a8b33  sub          x22, x21, x20
    e64: 010b1b13  slli         x22, x22, 16
    e68: 010b5b13  srli         x22, x22, 16
    e6c: 017b7663  bgeu         x22, x23, 0x00000e78  # target 0x00000e78
    e70: 0ff0000f  fence        0xf, 0xf
    e74: fe1ff06f  jal          x0, 0x00000e54  # target 0x00000e54
loc_e78:
    e78: 0ff0000f  fence        0xf, 0xf
    e7c: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    e80: 83cc0c13  addi         x24, x24, -1988  # x24 = 0xffb0083c · riscv_local_mem + 0x83c
    e84: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x83c · 0xffb0083c
    e88: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_e8c:
    e8c: ffb4ac37  lui          x24, 0xffb4a  # x24 = 0xffb4a000
    e90: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb4a028
    e94: 000c5a83  lhu          x21, 0(x24)  # 0xffb4a028
    e98: 414a8b33  sub          x22, x21, x20
    e9c: 010b1b13  slli         x22, x22, 16
    ea0: 010b5b13  srli         x22, x22, 16
    ea4: 017b7663  bgeu         x22, x23, 0x00000eb0  # target 0x00000eb0
    ea8: 0ff0000f  fence        0xf, 0xf
    eac: fe1ff06f  jal          x0, 0x00000e8c  # target 0x00000e8c
loc_eb0:
    eb0: 0ff0000f  fence        0xf, 0xf
    eb4: 88100182  STALLWAIT    stall_res=8, wait_res=96  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR | Wait.SRCB_CLR
    eb8: 78bff001  SETADCXX     CntSetMask=1, x_end2=1023, x_start=0
    ebc: 793ff001  SETADCXX     CntSetMask=2, x_end2=1023, x_start=0
    ec0: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    ec4: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    ec8: 0a000305  UNPACR       Unpack_block_selection=1, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    ecc: 08000305  UNPACR       Unpack_block_selection=0, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    ed0: 8810001a  STALLWAIT    stall_res=8, wait_res=6  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0 | Wait.UNPACK1
    ed4: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    ed8: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    edc: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    ee0: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    ee4: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    ee8: 01507033  and          x0, x0, x21
    eec: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    ef0: 83ca8a93  addi         x21, x21, -1988  # x21 = 0xffb0083c · riscv_local_mem + 0x83c
    ef4: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x83c · 0xffb0083c
    ef8: 001a0a13  addi         x20, x20, 1
    efc: 010a1a13  slli         x20, x20, 16
    f00: 010a5a13  srli         x20, x20, 16
    f04: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    f08: 83ca8a93  addi         x21, x21, -1988  # x21 = 0xffb0083c · riscv_local_mem + 0x83c
    f0c: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x83c · 0xffb0083c; write runtime value
    f10: ffb4aab7  lui          x21, 0xffb4a  # x21 = 0xffb4a000
    f14: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb4a020
    f18: 014aa023  sw           x20, 0(x21)  # 0xffb4a020; write runtime value
    f1c: 0ff0000f  fence        0xf, 0xf
    f20: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    f24: 838c0c13  addi         x24, x24, -1992  # x24 = 0xffb00838 · riscv_local_mem + 0x838
    f28: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x838 · 0xffb00838
    f2c: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    f30: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    f34: 015a0a33  add          x20, x20, x21
    f38: 00019b37  lui          x22, 0x00019  # x22 = 0x00019000
    f3c: 080b0b13  addi         x22, x22, 128  # x22 = 0x00019080
    f40: 016a6663  bltu         x20, x22, 0x00000f4c  # target 0x00000f4c
    f44: 00004bb7  lui          x23, 0x00004  # x23 = 0x00004000
    f48: 417a0a33  sub          x20, x20, x23
loc_f4c:
    f4c: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    f50: 838c0c13  addi         x24, x24, -1992  # x24 = 0xffb00838 · riscv_local_mem + 0x838
    f54: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x838 · 0xffb00838; write runtime value
    f58: 00008067  jalr         x0, 0(x1)
    f5c:           j FW_TRISC0+4   # return to firmware, linked at install
