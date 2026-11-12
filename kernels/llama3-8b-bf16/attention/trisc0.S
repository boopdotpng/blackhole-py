# llama3 8b-bf16 decode: attention, trisc0. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (96): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5 7,6 7,7 7,8 7,9 7,10 7,11 10,2 10,3 10,4 10,5 10,6 10,7 10,8 10,9 10,10 10,11 11,2 11,3 11,4 11,5 11,6 11,7 11,8 11,9 11,10 11,11 12,2 12,3 12,4 12,5 12,6 12,7
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=attention_e2e_q_compact, 0x79c=attention_e2e_k_compact, 0x7a0=attention_e2e_v_compact, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0xe900=e2e_attention_partials, 0xe904=attention_core, 0xe908=attention_phase
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
      4: 820a8a93  addi         x21, x21, -2016  # x21 = 0xffb00820 · riscv_local_mem + 0x820
      8: 00020b37  lui          x22, 0x00020  # x22 = 0x00020000
      c: 800b0b13  addi         x22, x22, -2048  # x22 = 0x0001f800
     10: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x820 · 0xffb00820; write 0x0001f800
     14: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     18: 824a8a93  addi         x21, x21, -2012  # x21 = 0xffb00824 · riscv_local_mem + 0x824
     1c: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x824 · 0xffb00824; write 0x00000000
     20: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
     24: 82828293  addi         x5, x5, -2008  # x5 = 0xffb00828 · riscv_local_mem + 0x828
     28: 0000f337  lui          x6, 0x0000f  # x6 = 0x0000f000
     2c: 0062a023  sw           x6, 0(x5)  # riscv_local_mem + 0x828 · 0xffb00828; write 0x0000f000
     30: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
     34: 82c28293  addi         x5, x5, -2004  # x5 = 0xffb0082c · riscv_local_mem + 0x82c
     38: 0002a023  sw           x0, 0(x5)  # riscv_local_mem + 0x82c · 0xffb0082c; write 0x00000000
     3c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     40: 830a8a93  addi         x21, x21, -2000  # x21 = 0xffb00830 · riscv_local_mem + 0x830
     44: 00011b37  lui          x22, 0x00011  # x22 = 0x00011000
     48: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x830 · 0xffb00830; write 0x00011000
     4c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     50: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
     54: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834; write 0x00000000
     58: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     5c: 838a8a93  addi         x21, x21, -1992  # x21 = 0xffb00838 · riscv_local_mem + 0x838
     60: 00015b37  lui          x22, 0x00015  # x22 = 0x00015000
     64: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x838 · 0xffb00838; write 0x00015000
     68: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     6c: 83ca8a93  addi         x21, x21, -1988  # x21 = 0xffb0083c · riscv_local_mem + 0x83c
     70: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x83c · 0xffb0083c; write 0x00000000
     74: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     78: 840a8a93  addi         x21, x21, -1984  # x21 = 0xffb00840 · riscv_local_mem + 0x840
     7c: 00019b37  lui          x22, 0x00019  # x22 = 0x00019000
     80: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x840 · 0xffb00840; write 0x00019000
     84: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     88: 844a8a93  addi         x21, x21, -1980  # x21 = 0xffb00844 · riscv_local_mem + 0x844
     8c: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x844 · 0xffb00844; write 0x00000000
     90: 0000f337  lui          x6, 0x0000f  # x6 = 0x0000f000
     94: 90830313  addi         x6, x6, -1784  # x6 = 0x0000e908
     98: 00032203  lw           x4, 0(x6)  # param attention_phase; 0x0000e908
     9c: 79000413  addi         x8, x0, 1936  # x8 = 0x00000790
     a0: 00042303  lw           x6, 0(x8)  # param kv_blocks; 0x00000790
     a4: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
     a8: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
     ac: 0063fa63  bgeu         x7, x6, 0x000000c0  # target 0x000000c0
     b0: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     b4: 08000393  addi         x7, x0, 128  # x7 = 0x00000080
     b8: 0063f463  bgeu         x7, x6, 0x000000c0  # target 0x000000c0
     bc: 00c00293  addi         x5, x0, 12  # x5 = 0x0000000c
loc_c0:
     c0: 265276e3  bgeu         x4, x5, 0x00000b2c  # target 0x00000b2c
     c4: 26d000ef  jal          x1, 0x00000b30  # target 0x00000b30; x1 = 0x000000c8
     c8: 269000ef  jal          x1, 0x00000b30  # target 0x00000b30; x1 = 0x000000cc
     cc: 265000ef  jal          x1, 0x00000b30  # target 0x00000b30; x1 = 0x000000d0
     d0: 261000ef  jal          x1, 0x00000b30  # target 0x00000b30; x1 = 0x000000d4
     d4: 79000293  addi         x5, x0, 1936  # x5 = 0x00000790
     d8: 0002a203  lw           x4, 0(x5)  # param kv_blocks; 0x00000790
     dc: 0000f3b7  lui          x7, 0x0000f  # x7 = 0x0000f000
     e0: 90838393  addi         x7, x7, -1784  # x7 = 0x0000e908
     e4: 0003a283  lw           x5, 0(x7)  # param attention_phase; 0x0000e908
     e8: 79000493  addi         x9, x0, 1936  # x9 = 0x00000790
     ec: 0004a383  lw           x7, 0(x9)  # param kv_blocks; 0x00000790
     f0: 00100313  addi         x6, x0, 1  # x6 = 0x00000001
     f4: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
     f8: 00747a63  bgeu         x8, x7, 0x0000010c  # target 0x0000010c
     fc: 00400313  addi         x6, x0, 4  # x6 = 0x00000004
    100: 08000413  addi         x8, x0, 128  # x8 = 0x00000080
    104: 00747463  bgeu         x8, x7, 0x0000010c  # target 0x0000010c
    108: 00c00313  addi         x6, x0, 12  # x6 = 0x0000000c
loc_10c:
    10c: 00620233  add          x4, x4, x6
    110: fff20213  addi         x4, x4, -1
    114: 40520233  sub          x4, x4, x5
    118: 02625233  divu         x4, x4, x6
    11c: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    120: 82c48493  addi         x9, x9, -2004  # x9 = 0xffb0082c · riscv_local_mem + 0x82c
    124: 0004a283  lw           x5, 0(x9)  # riscv_local_mem + 0x82c · 0xffb0082c
    128: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
loc_12c:
    12c: ffb484b7  lui          x9, 0xffb48  # x9 = 0xffb48000
    130: 02848493  addi         x9, x9, 40  # x9 = 0xffb48028
    134: 0004d303  lhu          x6, 0(x9)  # 0xffb48028
    138: 405303b3  sub          x7, x6, x5
    13c: 01039393  slli         x7, x7, 16
    140: 0103d393  srli         x7, x7, 16
    144: 0083f663  bgeu         x7, x8, 0x00000150  # target 0x00000150
    148: 0ff0000f  fence        0xf, 0xf
    14c: fe1ff06f  jal          x0, 0x0000012c  # target 0x0000012c
loc_150:
    150: 0ff0000f  fence        0xf, 0xf
    154: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    158: 00020313  addi         x6, x4, 0
loc_15c:
    15c: 1662f6e3  bgeu         x5, x6, 0x00000ac8  # target 0x00000ac8
    160: ffe803b7  lui          x7, 0xffe80  # x7 = 0xffe80000 · tensix_pc_buf + 0x0
    164: 03438393  addi         x7, x7, 52  # x7 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_168:
    168: 0003a403  lw           x8, 0(x7)  # UNPACK_CONFIG_SYNC · 0xffe80034
    16c: 0fe47413  andi         x8, x8, 254
    170: 00040663  beq          x8, x0, 0x0000017c  # target 0x0000017c
    174: 0ff0000f  fence        0xf, 0xf
    178: ff1ff06f  jal          x0, 0x00000168  # target 0x00000168
loc_17c:
    17c: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    180: d500011e  RMWCIB2      Mask=64, Data=0, CfgRegAddr=71  # cfg[71] (current thread StateID); THCON_SEC0_REG1_Unp_LF8_4b_exp = 0
    184: ffef03b7  lui          x7, 0xffef0  # x7 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    188: 10038393  addi         x7, x7, 256  # x7 = 0xffef0100 · cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor
    18c: 01500413  addi         x8, x0, 21  # x8 = 0x00000015
    190: 0083a023  sw           x8, 0(x7)  # cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor · 0xffef0100; write 0x00000015; cfg[64] (bank 0); THCON_SEC0_REG0_TileDescriptor = 21
    194: 00040437  lui          x8, 0x00040  # x8 = 0x00040000
    198: 00140413  addi         x8, x8, 1  # x8 = 0x00040001
    19c: 0083a223  sw           x8, 4(x7)  # cfg[65] (bank 0) (undocumented index) · 0xffef0104; write 0x00040001; cfg[65] (bank 0) · fields not in ttsim
    1a0: 0003a423  sw           x0, 8(x7)  # cfg[66] (bank 0) (undocumented index) · 0xffef0108; write 0x00000000; cfg[66] (bank 0) · fields not in ttsim
    1a4: 0003a623  sw           x0, 12(x7)  # cfg[67] (bank 0) (undocumented index) · 0xffef010c; write 0x00000000; cfg[67] (bank 0) · fields not in ttsim
    1a8: 12500413  addi         x8, x0, 293  # x8 = 0x00000125
    1ac: 0283a023  sw           x8, 32(x7)  # cfg[72] (bank 0) · THCON_SEC0_REG2_Out_data_format, THCON_SEC0_REG2_Throttle_mode, THCON_SEC0_REG2_Context_count, THCON_SEC0_REG2_Haloize_mode, THCON_SEC0_REG2_Tileize_mode, THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC0_REG2_Unpack_If_Sel, THCON_SEC0_REG2_Upsample_rate, THCON_SEC0_REG2_Ovrd_data_format, THCON_SEC0_REG2_Upsample_and_interleave, THCON_SEC0_REG2_Shift_amount_cntx0, THCON_SEC0_REG2_Shift_amount_cntx1, THCON_SEC0_REG2_Shift_amount_cntx2, THCON_SEC0_REG2_Shift_amount_cntx3 · 0xffef0120; write 0x00000125; cfg[72] (bank 0); THCON_SEC0_REG2_Out_data_format = 5; THCON_SEC0_REG2_Throttle_mode = 2; THCON_SEC0_REG2_Context_count = 0; THCON_SEC0_REG2_Haloize_mode = 1; THCON_SEC0_REG2_Tileize_mode = 0; THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC0_REG2_Unpack_If_Sel = 0; THCON_SEC0_REG2_Upsample_rate = 0; THCON_SEC0_REG2_Ovrd_data_format = 0; THCON_SEC0_REG2_Upsample_and_interleave = 0; THCON_SEC0_REG2_Shift_amount_cntx0 = 0; THCON_SEC0_REG2_Shift_amount_cntx1 = 0; THCON_SEC0_REG2_Shift_amount_cntx2 = 0; THCON_SEC0_REG2_Shift_amount_cntx3 = 0
    1b0: 00300413  addi         x8, x0, 3  # x8 = 0x00000003
    1b4: 0283a223  sw           x8, 36(x7)  # cfg[73] (bank 0) · THCON_SEC0_REG2_Disable_zero_compress_cntx0, THCON_SEC0_REG2_Disable_zero_compress_cntx1, THCON_SEC0_REG2_Disable_zero_compress_cntx2, THCON_SEC0_REG2_Disable_zero_compress_cntx3, THCON_SEC0_REG2_Unpack_if_sel_cntx0, THCON_SEC0_REG2_Unpack_if_sel_cntx1, THCON_SEC0_REG2_Unpack_if_sel_cntx2, THCON_SEC0_REG2_Unpack_if_sel_cntx3, THCON_SEC0_REG2_Force_shared_exp, THCON_SEC0_REG2_Context_count_non_log2, THCON_SEC0_REG2_Context_count_non_log2_en, THCON_SEC0_REG2_Disable_zero_compress_cntx4, THCON_SEC0_REG2_Disable_zero_compress_cntx5, THCON_SEC0_REG2_Disable_zero_compress_cntx6, THCON_SEC0_REG2_Disable_zero_compress_cntx7, THCON_SEC0_REG2_Unpack_if_sel_cntx4, THCON_SEC0_REG2_Unpack_if_sel_cntx5, THCON_SEC0_REG2_Unpack_if_sel_cntx6, THCON_SEC0_REG2_Unpack_if_sel_cntx7, THCON_SEC0_REG2_Metadata_x_end · 0xffef0124; write 0x00000003; cfg[73] (bank 0); THCON_SEC0_REG2_Disable_zero_compress_cntx0 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx1 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx2 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx3 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx0 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx1 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx2 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx3 = 0; THCON_SEC0_REG2_Force_shared_exp = 0; THCON_SEC0_REG2_Context_count_non_log2 = 0; THCON_SEC0_REG2_Context_count_non_log2_en = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx4 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx5 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx6 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx7 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx4 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx5 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx6 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx7 = 0; THCON_SEC0_REG2_Metadata_x_end = 0
    1b8: 0203a423  sw           x0, 40(x7)  # cfg[74] (bank 0) · THCON_SEC0_REG2_Unpack_limit_address · 0xffef0128; write 0x00000000; cfg[74] (bank 0); THCON_SEC0_REG2_Unpack_limit_address = 0
    1bc: 0203a623  sw           x0, 44(x7)  # cfg[75] (bank 0) · THCON_SEC0_REG2_Unpack_fifo_size · 0xffef012c; write 0x00000000; cfg[75] (bank 0); THCON_SEC0_REG2_Unpack_fifo_size = 0
    1c0: fa03a823  sw           x0, -80(x7)  # cfg[44] (bank 0) · UNP0_ADDR_CTRL_XY_REG_0_Xstride, UNP0_ADDR_CTRL_XY_REG_0_Ystride · 0xffef00b0; write 0x00000000; cfg[44] (bank 0); UNP0_ADDR_CTRL_XY_REG_0_Xstride = 0; UNP0_ADDR_CTRL_XY_REG_0_Ystride = 0
    1c4: fa03aa23  sw           x0, -76(x7)  # cfg[45] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_0_Zstride, UNP0_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef00b4; write 0x00000000; cfg[45] (bank 0); UNP0_ADDR_CTRL_ZW_REG_0_Zstride = 0; UNP0_ADDR_CTRL_ZW_REG_0_Wstride = 0
    1c8: 00200437  lui          x8, 0x00200  # x8 = 0x00200000
    1cc: 00240413  addi         x8, x8, 2  # x8 = 0x00200002
    1d0: fe83a023  sw           x8, -32(x7)  # cfg[56] (bank 0) · UNP0_ADDR_CTRL_XY_REG_1_Xstride, UNP0_ADDR_CTRL_XY_REG_1_Ystride · 0xffef00e0; write 0x00200002; cfg[56] (bank 0); UNP0_ADDR_CTRL_XY_REG_1_Xstride = 2; UNP0_ADDR_CTRL_XY_REG_1_Ystride = 32
    1d4: 20000413  addi         x8, x0, 512  # x8 = 0x00000200
    1d8: fe83a223  sw           x8, -28(x7)  # cfg[57] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_1_Zstride, UNP0_ADDR_CTRL_ZW_REG_1_Wstride · 0xffef00e4; write 0x00000200; cfg[57] (bank 0); UNP0_ADDR_CTRL_ZW_REG_1_Zstride = 512; UNP0_ADDR_CTRL_ZW_REG_1_Wstride = 0
    1dc: fc03a023  sw           x0, -64(x7)  # cfg[48] (bank 0) · UNP0_ADDR_BASE_REG_0_Base · 0xffef00c0; write 0x00000000; cfg[48] (bank 0); UNP0_ADDR_BASE_REG_0_Base = 0
    1e0: fc03a223  sw           x0, -60(x7)  # cfg[49] (bank 0) · UNP0_ADDR_BASE_REG_1_Base · 0xffef00c4; write 0x00000000; cfg[49] (bank 0); UNP0_ADDR_BASE_REG_1_Base = 0
    1e4: 10000413  addi         x8, x0, 256  # x8 = 0x00000100
    1e8: fc83a423  sw           x8, -56(x7)  # cfg[50] (bank 0) · UNP0_FORCED_SHARED_EXP_shared_exp, UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr · 0xffef00c8; write 0x00000100; cfg[50] (bank 0); UNP0_FORCED_SHARED_EXP_shared_exp = 0; UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr = 1
    1ec: fc03aa23  sw           x0, -44(x7)  # cfg[53] (bank 0) · UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val · 0xffef00d4; write 0x00000000; cfg[53] (bank 0); UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val = 0
    1f0: 00400437  lui          x8, 0x00400  # x8 = 0x00400000
    1f4: 04040413  addi         x8, x8, 64  # x8 = 0x00400040
    1f8: 0483a823  sw           x8, 80(x7)  # cfg[84] (bank 0) · THCON_SEC0_REG5_Dest_cntx0_address, THCON_SEC0_REG5_Dest_cntx1_address · 0xffef0150; write 0x00400040; cfg[84] (bank 0); THCON_SEC0_REG5_Dest_cntx0_address = 64; THCON_SEC0_REG5_Dest_cntx1_address = 64
    1fc: 01000437  lui          x8, 0x01000  # x8 = 0x01000000
    200: 10040413  addi         x8, x8, 256  # x8 = 0x01000100
    204: 0483ac23  sw           x8, 88(x7)  # cfg[86] (bank 0) · THCON_SEC0_REG5_Tile_x_dim_cntx0, THCON_SEC0_REG5_Tile_x_dim_cntx1 · 0xffef0158; write 0x01000100; cfg[86] (bank 0); THCON_SEC0_REG5_Tile_x_dim_cntx0 = 256; THCON_SEC0_REG5_Tile_x_dim_cntx1 = 256
    208: 0603a823  sw           x0, 112(x7)  # cfg[92] (bank 0) · THCON_SEC0_REG7_Offset_address, THCON_SEC0_REG7_Unpack_data_format_cntx0, THCON_SEC0_REG7_Unpack_out_data_format_cntx0, THCON_SEC0_REG7_Unpack_data_format_cntx4, THCON_SEC0_REG7_Unpack_out_data_format_cntx4 · 0xffef0170; write 0x00000000; cfg[92] (bank 0); THCON_SEC0_REG7_Offset_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx4 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx4 = 0
    20c: 0603aa23  sw           x0, 116(x7)  # cfg[93] (bank 0) · THCON_SEC0_REG7_Offset_cntx1_address, THCON_SEC0_REG7_Unpack_data_format_cntx1, THCON_SEC0_REG7_Unpack_out_data_format_cntx1, THCON_SEC0_REG7_Unpack_data_format_cntx5, THCON_SEC0_REG7_Unpack_out_data_format_cntx5 · 0xffef0174; write 0x00000000; cfg[93] (bank 0); THCON_SEC0_REG7_Offset_cntx1_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx5 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx5 = 0
    210: d50001de  RMWCIB2      Mask=64, Data=0, CfgRegAddr=119  # cfg[119] (current thread StateID); THCON_SEC1_REG1_Unp_LF8_4b_exp = 0
    214: ffef03b7  lui          x7, 0xffef0  # x7 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    218: 1c038393  addi         x7, x7, 448  # x7 = 0xffef01c0 · cfg[112] (bank 0) · THCON_SEC1_REG0_TileDescriptor
    21c: 01000437  lui          x8, 0x01000  # x8 = 0x01000000
    220: 01540413  addi         x8, x8, 21  # x8 = 0x01000015
    224: 0083a023  sw           x8, 0(x7)  # cfg[112] (bank 0) · THCON_SEC1_REG0_TileDescriptor · 0xffef01c0; write 0x01000015; cfg[112] (bank 0); THCON_SEC1_REG0_TileDescriptor = 16777237
    228: 00040437  lui          x8, 0x00040  # x8 = 0x00040000
    22c: 00140413  addi         x8, x8, 1  # x8 = 0x00040001
    230: 0083a223  sw           x8, 4(x7)  # cfg[113] (bank 0) (undocumented index) · 0xffef01c4; write 0x00040001; cfg[113] (bank 0) · fields not in ttsim
    234: 0003a423  sw           x0, 8(x7)  # cfg[114] (bank 0) (undocumented index) · 0xffef01c8; write 0x00000000; cfg[114] (bank 0) · fields not in ttsim
    238: 0003a623  sw           x0, 12(x7)  # cfg[115] (bank 0) (undocumented index) · 0xffef01cc; write 0x00000000; cfg[115] (bank 0) · fields not in ttsim
    23c: 02500413  addi         x8, x0, 37  # x8 = 0x00000025
    240: 0283a023  sw           x8, 32(x7)  # cfg[120] (bank 0) · THCON_SEC1_REG2_Out_data_format, THCON_SEC1_REG2_Throttle_mode, THCON_SEC1_REG2_Context_count, THCON_SEC1_REG2_Haloize_mode, THCON_SEC1_REG2_Tileize_mode, THCON_SEC1_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC1_REG2_Unpack_If_Sel, THCON_SEC1_REG2_Upsample_rate, THCON_SEC1_REG2_Ovrd_data_format, THCON_SEC1_REG2_Upsample_and_interleave, THCON_SEC1_REG2_Shift_amount_cntx0, THCON_SEC1_REG2_Shift_amount_cntx1, THCON_SEC1_REG2_Shift_amount_cntx2, THCON_SEC1_REG2_Shift_amount_cntx3 · 0xffef01e0; write 0x00000025; cfg[120] (bank 0); THCON_SEC1_REG2_Out_data_format = 5; THCON_SEC1_REG2_Throttle_mode = 2; THCON_SEC1_REG2_Context_count = 0; THCON_SEC1_REG2_Haloize_mode = 0; THCON_SEC1_REG2_Tileize_mode = 0; THCON_SEC1_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC1_REG2_Unpack_If_Sel = 0; THCON_SEC1_REG2_Upsample_rate = 0; THCON_SEC1_REG2_Ovrd_data_format = 0; THCON_SEC1_REG2_Upsample_and_interleave = 0; THCON_SEC1_REG2_Shift_amount_cntx0 = 0; THCON_SEC1_REG2_Shift_amount_cntx1 = 0; THCON_SEC1_REG2_Shift_amount_cntx2 = 0; THCON_SEC1_REG2_Shift_amount_cntx3 = 0
    244: 00300413  addi         x8, x0, 3  # x8 = 0x00000003
    248: 0283a223  sw           x8, 36(x7)  # cfg[121] (bank 0) · THCON_SEC1_REG2_Disable_zero_compress_cntx0, THCON_SEC1_REG2_Disable_zero_compress_cntx1, THCON_SEC1_REG2_Disable_zero_compress_cntx2, THCON_SEC1_REG2_Disable_zero_compress_cntx3, THCON_SEC1_REG2_Unpack_if_sel_cntx0, THCON_SEC1_REG2_Unpack_if_sel_cntx1, THCON_SEC1_REG2_Unpack_if_sel_cntx2, THCON_SEC1_REG2_Unpack_if_sel_cntx3, THCON_SEC1_REG2_Force_shared_exp, THCON_SEC1_REG2_Context_count_non_log2, THCON_SEC1_REG2_Context_count_non_log2_en, THCON_SEC1_REG2_Disable_zero_compress_cntx4, THCON_SEC1_REG2_Disable_zero_compress_cntx5, THCON_SEC1_REG2_Disable_zero_compress_cntx6, THCON_SEC1_REG2_Disable_zero_compress_cntx7, THCON_SEC1_REG2_Unpack_if_sel_cntx4, THCON_SEC1_REG2_Unpack_if_sel_cntx5, THCON_SEC1_REG2_Unpack_if_sel_cntx6, THCON_SEC1_REG2_Unpack_if_sel_cntx7, THCON_SEC1_REG2_Metadata_x_end · 0xffef01e4; write 0x00000003; cfg[121] (bank 0); THCON_SEC1_REG2_Disable_zero_compress_cntx0 = 1; THCON_SEC1_REG2_Disable_zero_compress_cntx1 = 1; THCON_SEC1_REG2_Disable_zero_compress_cntx2 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx3 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx0 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx1 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx2 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx3 = 0; THCON_SEC1_REG2_Force_shared_exp = 0; THCON_SEC1_REG2_Context_count_non_log2 = 0; THCON_SEC1_REG2_Context_count_non_log2_en = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx4 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx5 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx6 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx7 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx4 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx5 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx6 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx7 = 0; THCON_SEC1_REG2_Metadata_x_end = 0
    24c: 0203a423  sw           x0, 40(x7)  # cfg[122] (bank 0) · THCON_SEC1_REG2_Unpack_limit_address · 0xffef01e8; write 0x00000000; cfg[122] (bank 0); THCON_SEC1_REG2_Unpack_limit_address = 0
    250: 0203a623  sw           x0, 44(x7)  # cfg[123] (bank 0) · THCON_SEC1_REG2_Unpack_fifo_size · 0xffef01ec; write 0x00000000; cfg[123] (bank 0); THCON_SEC1_REG2_Unpack_fifo_size = 0
    254: ee03ac23  sw           x0, -264(x7)  # cfg[46] (bank 0) · UNP1_ADDR_CTRL_XY_REG_0_Xstride, UNP1_ADDR_CTRL_XY_REG_0_Ystride · 0xffef00b8; write 0x00000000; cfg[46] (bank 0); UNP1_ADDR_CTRL_XY_REG_0_Xstride = 0; UNP1_ADDR_CTRL_XY_REG_0_Ystride = 0
    258: ee03ae23  sw           x0, -260(x7)  # cfg[47] (bank 0) · UNP1_ADDR_CTRL_ZW_REG_0_Zstride, UNP1_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef00bc; write 0x00000000; cfg[47] (bank 0); UNP1_ADDR_CTRL_ZW_REG_0_Zstride = 0; UNP1_ADDR_CTRL_ZW_REG_0_Wstride = 0
    25c: 00200437  lui          x8, 0x00200  # x8 = 0x00200000
    260: 00240413  addi         x8, x8, 2  # x8 = 0x00200002
    264: f283a423  sw           x8, -216(x7)  # cfg[58] (bank 0) · UNP1_ADDR_CTRL_XY_REG_1_Xstride, UNP1_ADDR_CTRL_XY_REG_1_Ystride · 0xffef00e8; write 0x00200002; cfg[58] (bank 0); UNP1_ADDR_CTRL_XY_REG_1_Xstride = 2; UNP1_ADDR_CTRL_XY_REG_1_Ystride = 32
    268: 20000413  addi         x8, x0, 512  # x8 = 0x00000200
    26c: f283a623  sw           x8, -212(x7)  # cfg[59] (bank 0) · UNP1_ADDR_CTRL_ZW_REG_1_Zstride, UNP1_ADDR_CTRL_ZW_REG_1_Wstride · 0xffef00ec; write 0x00000200; cfg[59] (bank 0); UNP1_ADDR_CTRL_ZW_REG_1_Zstride = 512; UNP1_ADDR_CTRL_ZW_REG_1_Wstride = 0
    270: f203a823  sw           x0, -208(x7)  # cfg[60] (bank 0) · UNP1_ADDR_BASE_REG_0_Base · 0xffef00f0; write 0x00000000; cfg[60] (bank 0); UNP1_ADDR_BASE_REG_0_Base = 0
    274: f203aa23  sw           x0, -204(x7)  # cfg[61] (bank 0) · UNP1_ADDR_BASE_REG_1_Base · 0xffef00f4; write 0x00000000; cfg[61] (bank 0); UNP1_ADDR_BASE_REG_1_Base = 0
    278: f203ac23  sw           x0, -200(x7)  # cfg[62] (bank 0) · UNP1_FORCED_SHARED_EXP_shared_exp, UNP1_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr · 0xffef00f8; write 0x00000000; cfg[62] (bank 0); UNP1_FORCED_SHARED_EXP_shared_exp = 0; UNP1_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr = 0
    27c: f203ae23  sw           x0, -196(x7)  # cfg[63] (bank 0) · UNP1_NOP_REG_CLR_VAL_nop_reg_clr_val · 0xffef00fc; write 0x00000000; cfg[63] (bank 0); UNP1_NOP_REG_CLR_VAL_nop_reg_clr_val = 0
    280: 0403a823  sw           x0, 80(x7)  # cfg[132] (bank 0) · THCON_SEC1_REG5_Dest_cntx0_address, THCON_SEC1_REG5_Dest_cntx1_address · 0xffef0210; write 0x00000000; cfg[132] (bank 0); THCON_SEC1_REG5_Dest_cntx0_address = 0; THCON_SEC1_REG5_Dest_cntx1_address = 0
    284: 01000437  lui          x8, 0x01000  # x8 = 0x01000000
    288: 10040413  addi         x8, x8, 256  # x8 = 0x01000100
    28c: 0483ac23  sw           x8, 88(x7)  # cfg[134] (bank 0) · THCON_SEC1_REG5_Tile_x_dim_cntx0, THCON_SEC1_REG5_Tile_x_dim_cntx1 · 0xffef0218; write 0x01000100; cfg[134] (bank 0); THCON_SEC1_REG5_Tile_x_dim_cntx0 = 256; THCON_SEC1_REG5_Tile_x_dim_cntx1 = 256
    290: 0603a823  sw           x0, 112(x7)  # cfg[140] (bank 0) · THCON_SEC1_REG7_Offset_address, THCON_SEC1_REG7_Unpack_data_format_cntx0, THCON_SEC1_REG7_Unpack_out_data_format_cntx0, THCON_SEC1_REG7_Unpack_data_format_cntx4, THCON_SEC1_REG7_Unpack_out_data_format_cntx4 · 0xffef0230; write 0x00000000; cfg[140] (bank 0); THCON_SEC1_REG7_Offset_address = 0; THCON_SEC1_REG7_Unpack_data_format_cntx0 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx0 = 0; THCON_SEC1_REG7_Unpack_data_format_cntx4 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx4 = 0
    294: 0603aa23  sw           x0, 116(x7)  # cfg[141] (bank 0) · THCON_SEC1_REG7_Offset_cntx1_address, THCON_SEC1_REG7_Unpack_data_format_cntx1, THCON_SEC1_REG7_Unpack_out_data_format_cntx1, THCON_SEC1_REG7_Unpack_data_format_cntx5, THCON_SEC1_REG7_Unpack_out_data_format_cntx5 · 0xffef0234; write 0x00000000; cfg[141] (bank 0); THCON_SEC1_REG7_Offset_cntx1_address = 0; THCON_SEC1_REG7_Unpack_data_format_cntx1 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx1 = 0; THCON_SEC1_REG7_Unpack_data_format_cntx5 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx5 = 0
    298: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    29c: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_2a0:
    2a0: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    2a4: 0feafa93  andi         x21, x21, 254
    2a8: 000a8663  beq          x21, x0, 0x000002b4  # target 0x000002b4
    2ac: 0ff0000f  fence        0xf, 0xf
    2b0: ff1ff06f  jal          x0, 0x000002a0  # target 0x000002a0
loc_2b4:
    2b4: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    2b8: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    2bc: 830a8a93  addi         x21, x21, -2000  # x21 = 0xffb00830 · riscv_local_mem + 0x830
    2c0: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x830 · 0xffb00830
    2c4: 004a5a13  srli         x20, x20, 4
    2c8: fffa0a13  addi         x20, x20, -1
    2cc: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    2d0: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    2d4: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    2d8: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    2dc: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    2e0: c8140012  SETC16       setc16_reg=5, setc16_value=4  # thread_cfg[5] (current thread); SRCA_SET_Base = 0; SRCA_SET_SetOvrdWithAddr = 1
    2e4: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    2e8: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_2ec:
    2ec: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    2f0: 0feafa93  andi         x21, x21, 254
    2f4: 000a8663  beq          x21, x0, 0x00000300  # target 0x00000300
    2f8: 0ff0000f  fence        0xf, 0xf
    2fc: ff1ff06f  jal          x0, 0x000002ec  # target 0x000002ec
loc_300:
    300: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    304: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    308: 828a8a93  addi         x21, x21, -2008  # x21 = 0xffb00828 · riscv_local_mem + 0x828
    30c: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x828 · 0xffb00828
    310: 004a5a13  srli         x20, x20, 4
    314: fffa0a13  addi         x20, x20, -1
    318: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    31c: 1f0a8a93  addi         x21, x21, 496  # x21 = 0xffef01f0 · cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address
    320: 014aa023  sw           x20, 0(x21)  # cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address · 0xffef01f0; write runtime value; cfg[124] (bank 0); THCON_SEC1_REG3_Base_address = runtime
    324: 014aa223  sw           x20, 4(x21)  # cfg[125] (bank 0) · THCON_SEC1_REG3_Base_cntx1_address · 0xffef01f4; write runtime value; cfg[125] (bank 0); THCON_SEC1_REG3_Base_cntx1_address = runtime
    328: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    32c: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    330: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    334: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    338: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    33c: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    340: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    344: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    348: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    34c: 834c0c13  addi         x24, x24, -1996  # x24 = 0xffb00834 · riscv_local_mem + 0x834
    350: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x834 · 0xffb00834
    354: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_358:
    358: ffb49c37  lui          x24, 0xffb49  # x24 = 0xffb49000
    35c: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb49028
    360: 000c5a83  lhu          x21, 0(x24)  # 0xffb49028
    364: 414a8b33  sub          x22, x21, x20
    368: 010b1b13  slli         x22, x22, 16
    36c: 010b5b13  srli         x22, x22, 16
    370: 017b7663  bgeu         x22, x23, 0x0000037c  # target 0x0000037c
    374: 0ff0000f  fence        0xf, 0xf
    378: fe1ff06f  jal          x0, 0x00000358  # target 0x00000358
loc_37c:
    37c: 0ff0000f  fence        0xf, 0xf
    380: 88100182  STALLWAIT    stall_res=8, wait_res=96  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR | Wait.SRCB_CLR
    384: 78bff001  SETADCXX     CntSetMask=1, x_end2=1023, x_start=0
    388: 793ff001  SETADCXX     CntSetMask=2, x_end2=1023, x_start=0
    38c: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    390: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    394: 0a000305  UNPACR       Unpack_block_selection=1, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    398: 08000305  UNPACR       Unpack_block_selection=0, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    39c: 8810001a  STALLWAIT    stall_res=8, wait_res=6  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0 | Wait.UNPACK1
    3a0: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    3a4: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    3a8: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    3ac: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    3b0: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    3b4: 01507033  and          x0, x0, x21
    3b8: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    3bc: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    3c0: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834
    3c4: 001a0a13  addi         x20, x20, 1
    3c8: 010a1a13  slli         x20, x20, 16
    3cc: 010a5a13  srli         x20, x20, 16
    3d0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    3d4: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    3d8: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834; write runtime value
    3dc: ffb49ab7  lui          x21, 0xffb49  # x21 = 0xffb49000
    3e0: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb49020
    3e4: 014aa023  sw           x20, 0(x21)  # 0xffb49020; write runtime value
    3e8: 0ff0000f  fence        0xf, 0xf
    3ec: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    3f0: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    3f4: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830
    3f8: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    3fc: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    400: 015a0a33  add          x20, x20, x21
    404: 00015b37  lui          x22, 0x00015  # x22 = 0x00015000
    408: 016a6663  bltu         x20, x22, 0x00000414  # target 0x00000414
    40c: 00004bb7  lui          x23, 0x00004  # x23 = 0x00004000
    410: 417a0a33  sub          x20, x20, x23
loc_414:
    414: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    418: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    41c: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830; write runtime value
    420: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    424: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_428:
    428: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    42c: 0feafa93  andi         x21, x21, 254
    430: 000a8663  beq          x21, x0, 0x0000043c  # target 0x0000043c
    434: 0ff0000f  fence        0xf, 0xf
    438: ff1ff06f  jal          x0, 0x00000428  # target 0x00000428
loc_43c:
    43c: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    440: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    444: 830a8a93  addi         x21, x21, -2000  # x21 = 0xffb00830 · riscv_local_mem + 0x830
    448: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x830 · 0xffb00830
    44c: 004a5a13  srli         x20, x20, 4
    450: fffa0a13  addi         x20, x20, -1
    454: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    458: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    45c: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    460: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    464: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    468: c8140012  SETC16       setc16_reg=5, setc16_value=4  # thread_cfg[5] (current thread); SRCA_SET_Base = 0; SRCA_SET_SetOvrdWithAddr = 1
    46c: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    470: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_474:
    474: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    478: 0feafa93  andi         x21, x21, 254
    47c: 000a8663  beq          x21, x0, 0x00000488  # target 0x00000488
    480: 0ff0000f  fence        0xf, 0xf
    484: ff1ff06f  jal          x0, 0x00000474  # target 0x00000474
loc_488:
    488: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    48c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    490: 828a8a93  addi         x21, x21, -2008  # x21 = 0xffb00828 · riscv_local_mem + 0x828
    494: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x828 · 0xffb00828
    498: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    49c: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    4a0: 015a0a33  add          x20, x20, x21
    4a4: 00011b37  lui          x22, 0x00011  # x22 = 0x00011000
    4a8: 016a6663  bltu         x20, x22, 0x000004b4  # target 0x000004b4
    4ac: 00002ab7  lui          x21, 0x00002  # x21 = 0x00002000
    4b0: 415a0a33  sub          x20, x20, x21
loc_4b4:
    4b4: 004a5a13  srli         x20, x20, 4
    4b8: fffa0a13  addi         x20, x20, -1
    4bc: ffef0bb7  lui          x23, 0xffef0  # x23 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    4c0: 1f0b8b93  addi         x23, x23, 496  # x23 = 0xffef01f0 · cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address
    4c4: 014ba023  sw           x20, 0(x23)  # cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address · 0xffef01f0; write runtime value; cfg[124] (bank 0); THCON_SEC1_REG3_Base_address = runtime
    4c8: 014ba223  sw           x20, 4(x23)  # cfg[125] (bank 0) · THCON_SEC1_REG3_Base_cntx1_address · 0xffef01f4; write runtime value; cfg[125] (bank 0); THCON_SEC1_REG3_Base_cntx1_address = runtime
    4cc: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    4d0: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    4d4: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    4d8: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    4dc: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    4e0: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    4e4: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    4e8: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    4ec: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    4f0: 834c0c13  addi         x24, x24, -1996  # x24 = 0xffb00834 · riscv_local_mem + 0x834
    4f4: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x834 · 0xffb00834
    4f8: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_4fc:
    4fc: ffb49c37  lui          x24, 0xffb49  # x24 = 0xffb49000
    500: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb49028
    504: 000c5a83  lhu          x21, 0(x24)  # 0xffb49028
    508: 414a8b33  sub          x22, x21, x20
    50c: 010b1b13  slli         x22, x22, 16
    510: 010b5b13  srli         x22, x22, 16
    514: 017b7663  bgeu         x22, x23, 0x00000520  # target 0x00000520
    518: 0ff0000f  fence        0xf, 0xf
    51c: fe1ff06f  jal          x0, 0x000004fc  # target 0x000004fc
loc_520:
    520: 0ff0000f  fence        0xf, 0xf
    524: 88100182  STALLWAIT    stall_res=8, wait_res=96  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR | Wait.SRCB_CLR
    528: 78bff001  SETADCXX     CntSetMask=1, x_end2=1023, x_start=0
    52c: 793ff001  SETADCXX     CntSetMask=2, x_end2=1023, x_start=0
    530: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    534: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    538: 0a000305  UNPACR       Unpack_block_selection=1, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    53c: 08000305  UNPACR       Unpack_block_selection=0, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    540: 8810001a  STALLWAIT    stall_res=8, wait_res=6  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0 | Wait.UNPACK1
    544: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    548: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    54c: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    550: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    554: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    558: 01507033  and          x0, x0, x21
    55c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    560: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    564: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834
    568: 001a0a13  addi         x20, x20, 1
    56c: 010a1a13  slli         x20, x20, 16
    570: 010a5a13  srli         x20, x20, 16
    574: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    578: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    57c: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834; write runtime value
    580: ffb49ab7  lui          x21, 0xffb49  # x21 = 0xffb49000
    584: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb49020
    588: 014aa023  sw           x20, 0(x21)  # 0xffb49020; write runtime value
    58c: 0ff0000f  fence        0xf, 0xf
    590: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    594: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    598: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830
    59c: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5a0: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    5a4: 015a0a33  add          x20, x20, x21
    5a8: 00015b37  lui          x22, 0x00015  # x22 = 0x00015000
    5ac: 016a6663  bltu         x20, x22, 0x000005b8  # target 0x000005b8
    5b0: 00004bb7  lui          x23, 0x00004  # x23 = 0x00004000
    5b4: 417a0a33  sub          x20, x20, x23
loc_5b8:
    5b8: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    5bc: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    5c0: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830; write runtime value
    5c4: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    5c8: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_5cc:
    5cc: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    5d0: 0feafa93  andi         x21, x21, 254
    5d4: 000a8663  beq          x21, x0, 0x000005e0  # target 0x000005e0
    5d8: 0ff0000f  fence        0xf, 0xf
    5dc: ff1ff06f  jal          x0, 0x000005cc  # target 0x000005cc
loc_5e0:
    5e0: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    5e4: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    5e8: 830a8a93  addi         x21, x21, -2000  # x21 = 0xffb00830 · riscv_local_mem + 0x830
    5ec: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x830 · 0xffb00830
    5f0: 004a5a13  srli         x20, x20, 4
    5f4: fffa0a13  addi         x20, x20, -1
    5f8: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    5fc: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    600: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    604: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    608: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    60c: c8140012  SETC16       setc16_reg=5, setc16_value=4  # thread_cfg[5] (current thread); SRCA_SET_Base = 0; SRCA_SET_SetOvrdWithAddr = 1
    610: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    614: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_618:
    618: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    61c: 0feafa93  andi         x21, x21, 254
    620: 000a8663  beq          x21, x0, 0x0000062c  # target 0x0000062c
    624: 0ff0000f  fence        0xf, 0xf
    628: ff1ff06f  jal          x0, 0x00000618  # target 0x00000618
loc_62c:
    62c: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    630: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    634: 828a8a93  addi         x21, x21, -2008  # x21 = 0xffb00828 · riscv_local_mem + 0x828
    638: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x828 · 0xffb00828
    63c: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    640: 015a0a33  add          x20, x20, x21
    644: 00011b37  lui          x22, 0x00011  # x22 = 0x00011000
    648: 016a6663  bltu         x20, x22, 0x00000654  # target 0x00000654
    64c: 00002ab7  lui          x21, 0x00002  # x21 = 0x00002000
    650: 415a0a33  sub          x20, x20, x21
loc_654:
    654: 004a5a13  srli         x20, x20, 4
    658: fffa0a13  addi         x20, x20, -1
    65c: ffef0bb7  lui          x23, 0xffef0  # x23 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    660: 1f0b8b93  addi         x23, x23, 496  # x23 = 0xffef01f0 · cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address
    664: 014ba023  sw           x20, 0(x23)  # cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address · 0xffef01f0; write runtime value; cfg[124] (bank 0); THCON_SEC1_REG3_Base_address = runtime
    668: 014ba223  sw           x20, 4(x23)  # cfg[125] (bank 0) · THCON_SEC1_REG3_Base_cntx1_address · 0xffef01f4; write runtime value; cfg[125] (bank 0); THCON_SEC1_REG3_Base_cntx1_address = runtime
    66c: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    670: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    674: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    678: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    67c: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    680: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    684: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    688: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    68c: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    690: 834c0c13  addi         x24, x24, -1996  # x24 = 0xffb00834 · riscv_local_mem + 0x834
    694: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x834 · 0xffb00834
    698: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_69c:
    69c: ffb49c37  lui          x24, 0xffb49  # x24 = 0xffb49000
    6a0: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb49028
    6a4: 000c5a83  lhu          x21, 0(x24)  # 0xffb49028
    6a8: 414a8b33  sub          x22, x21, x20
    6ac: 010b1b13  slli         x22, x22, 16
    6b0: 010b5b13  srli         x22, x22, 16
    6b4: 017b7663  bgeu         x22, x23, 0x000006c0  # target 0x000006c0
    6b8: 0ff0000f  fence        0xf, 0xf
    6bc: fe1ff06f  jal          x0, 0x0000069c  # target 0x0000069c
loc_6c0:
    6c0: 0ff0000f  fence        0xf, 0xf
    6c4: 88100182  STALLWAIT    stall_res=8, wait_res=96  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR | Wait.SRCB_CLR
    6c8: 78bff001  SETADCXX     CntSetMask=1, x_end2=1023, x_start=0
    6cc: 793ff001  SETADCXX     CntSetMask=2, x_end2=1023, x_start=0
    6d0: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    6d4: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    6d8: 0a000305  UNPACR       Unpack_block_selection=1, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    6dc: 08000305  UNPACR       Unpack_block_selection=0, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    6e0: 8810001a  STALLWAIT    stall_res=8, wait_res=6  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0 | Wait.UNPACK1
    6e4: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    6e8: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    6ec: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    6f0: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    6f4: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    6f8: 01507033  and          x0, x0, x21
    6fc: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    700: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    704: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834
    708: 001a0a13  addi         x20, x20, 1
    70c: 010a1a13  slli         x20, x20, 16
    710: 010a5a13  srli         x20, x20, 16
    714: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    718: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    71c: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834; write runtime value
    720: ffb49ab7  lui          x21, 0xffb49  # x21 = 0xffb49000
    724: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb49020
    728: 014aa023  sw           x20, 0(x21)  # 0xffb49020; write runtime value
    72c: 0ff0000f  fence        0xf, 0xf
    730: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    734: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    738: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830
    73c: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    740: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    744: 015a0a33  add          x20, x20, x21
    748: 00015b37  lui          x22, 0x00015  # x22 = 0x00015000
    74c: 016a6663  bltu         x20, x22, 0x00000758  # target 0x00000758
    750: 00004bb7  lui          x23, 0x00004  # x23 = 0x00004000
    754: 417a0a33  sub          x20, x20, x23
loc_758:
    758: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    75c: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    760: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830; write runtime value
    764: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    768: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_76c:
    76c: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    770: 0feafa93  andi         x21, x21, 254
    774: 000a8663  beq          x21, x0, 0x00000780  # target 0x00000780
    778: 0ff0000f  fence        0xf, 0xf
    77c: ff1ff06f  jal          x0, 0x0000076c  # target 0x0000076c
loc_780:
    780: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    784: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    788: 830a8a93  addi         x21, x21, -2000  # x21 = 0xffb00830 · riscv_local_mem + 0x830
    78c: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x830 · 0xffb00830
    790: 004a5a13  srli         x20, x20, 4
    794: fffa0a13  addi         x20, x20, -1
    798: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    79c: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    7a0: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    7a4: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    7a8: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    7ac: c8140012  SETC16       setc16_reg=5, setc16_value=4  # thread_cfg[5] (current thread); SRCA_SET_Base = 0; SRCA_SET_SetOvrdWithAddr = 1
    7b0: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    7b4: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_7b8:
    7b8: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    7bc: 0feafa93  andi         x21, x21, 254
    7c0: 000a8663  beq          x21, x0, 0x000007cc  # target 0x000007cc
    7c4: 0ff0000f  fence        0xf, 0xf
    7c8: ff1ff06f  jal          x0, 0x000007b8  # target 0x000007b8
loc_7cc:
    7cc: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    7d0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    7d4: 828a8a93  addi         x21, x21, -2008  # x21 = 0xffb00828 · riscv_local_mem + 0x828
    7d8: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x828 · 0xffb00828
    7dc: 00002ab7  lui          x21, 0x00002  # x21 = 0x00002000
    7e0: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00001800
    7e4: 015a0a33  add          x20, x20, x21
    7e8: 00011b37  lui          x22, 0x00011  # x22 = 0x00011000
    7ec: 016a6663  bltu         x20, x22, 0x000007f8  # target 0x000007f8
    7f0: 00002ab7  lui          x21, 0x00002  # x21 = 0x00002000
    7f4: 415a0a33  sub          x20, x20, x21
loc_7f8:
    7f8: 004a5a13  srli         x20, x20, 4
    7fc: fffa0a13  addi         x20, x20, -1
    800: ffef0bb7  lui          x23, 0xffef0  # x23 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    804: 1f0b8b93  addi         x23, x23, 496  # x23 = 0xffef01f0 · cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address
    808: 014ba023  sw           x20, 0(x23)  # cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address · 0xffef01f0; write runtime value; cfg[124] (bank 0); THCON_SEC1_REG3_Base_address = runtime
    80c: 014ba223  sw           x20, 4(x23)  # cfg[125] (bank 0) · THCON_SEC1_REG3_Base_cntx1_address · 0xffef01f4; write runtime value; cfg[125] (bank 0); THCON_SEC1_REG3_Base_cntx1_address = runtime
    810: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    814: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    818: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    81c: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    820: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    824: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    828: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    82c: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    830: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    834: 834c0c13  addi         x24, x24, -1996  # x24 = 0xffb00834 · riscv_local_mem + 0x834
    838: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x834 · 0xffb00834
    83c: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_840:
    840: ffb49c37  lui          x24, 0xffb49  # x24 = 0xffb49000
    844: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb49028
    848: 000c5a83  lhu          x21, 0(x24)  # 0xffb49028
    84c: 414a8b33  sub          x22, x21, x20
    850: 010b1b13  slli         x22, x22, 16
    854: 010b5b13  srli         x22, x22, 16
    858: 017b7663  bgeu         x22, x23, 0x00000864  # target 0x00000864
    85c: 0ff0000f  fence        0xf, 0xf
    860: fe1ff06f  jal          x0, 0x00000840  # target 0x00000840
loc_864:
    864: 0ff0000f  fence        0xf, 0xf
    868: 88100182  STALLWAIT    stall_res=8, wait_res=96  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR | Wait.SRCB_CLR
    86c: 78bff001  SETADCXX     CntSetMask=1, x_end2=1023, x_start=0
    870: 793ff001  SETADCXX     CntSetMask=2, x_end2=1023, x_start=0
    874: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    878: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    87c: 0a000305  UNPACR       Unpack_block_selection=1, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    880: 08000305  UNPACR       Unpack_block_selection=0, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    884: 8810001a  STALLWAIT    stall_res=8, wait_res=6  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0 | Wait.UNPACK1
    888: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    88c: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    890: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    894: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    898: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    89c: 01507033  and          x0, x0, x21
    8a0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    8a4: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    8a8: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834
    8ac: 001a0a13  addi         x20, x20, 1
    8b0: 010a1a13  slli         x20, x20, 16
    8b4: 010a5a13  srli         x20, x20, 16
    8b8: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    8bc: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    8c0: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834; write runtime value
    8c4: ffb49ab7  lui          x21, 0xffb49  # x21 = 0xffb49000
    8c8: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb49020
    8cc: 014aa023  sw           x20, 0(x21)  # 0xffb49020; write runtime value
    8d0: 0ff0000f  fence        0xf, 0xf
    8d4: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    8d8: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    8dc: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830
    8e0: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    8e4: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    8e8: 015a0a33  add          x20, x20, x21
    8ec: 00015b37  lui          x22, 0x00015  # x22 = 0x00015000
    8f0: 016a6663  bltu         x20, x22, 0x000008fc  # target 0x000008fc
    8f4: 00004bb7  lui          x23, 0x00004  # x23 = 0x00004000
    8f8: 417a0a33  sub          x20, x20, x23
loc_8fc:
    8fc: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    900: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    904: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830; write runtime value
    908: ffe803b7  lui          x7, 0xffe80  # x7 = 0xffe80000 · tensix_pc_buf + 0x0
    90c: 03438393  addi         x7, x7, 52  # x7 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_910:
    910: 0003a403  lw           x8, 0(x7)  # UNPACK_CONFIG_SYNC · 0xffe80034
    914: 0fe47413  andi         x8, x8, 254
    918: 00040663  beq          x8, x0, 0x00000924  # target 0x00000924
    91c: 0ff0000f  fence        0xf, 0xf
    920: ff1ff06f  jal          x0, 0x00000910  # target 0x00000910
loc_924:
    924: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    928: d500011e  RMWCIB2      Mask=64, Data=0, CfgRegAddr=71  # cfg[71] (current thread StateID); THCON_SEC0_REG1_Unp_LF8_4b_exp = 0
    92c: ffef03b7  lui          x7, 0xffef0  # x7 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    930: 10038393  addi         x7, x7, 256  # x7 = 0xffef0100 · cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor
    934: 01500413  addi         x8, x0, 21  # x8 = 0x00000015
    938: 0083a023  sw           x8, 0(x7)  # cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor · 0xffef0100; write 0x00000015; cfg[64] (bank 0); THCON_SEC0_REG0_TileDescriptor = 21
    93c: 00040437  lui          x8, 0x00040  # x8 = 0x00040000
    940: 00140413  addi         x8, x8, 1  # x8 = 0x00040001
    944: 0083a223  sw           x8, 4(x7)  # cfg[65] (bank 0) (undocumented index) · 0xffef0104; write 0x00040001; cfg[65] (bank 0) · fields not in ttsim
    948: 0003a423  sw           x0, 8(x7)  # cfg[66] (bank 0) (undocumented index) · 0xffef0108; write 0x00000000; cfg[66] (bank 0) · fields not in ttsim
    94c: 0003a623  sw           x0, 12(x7)  # cfg[67] (bank 0) (undocumented index) · 0xffef010c; write 0x00000000; cfg[67] (bank 0) · fields not in ttsim
    950: 02500413  addi         x8, x0, 37  # x8 = 0x00000025
    954: 0283a023  sw           x8, 32(x7)  # cfg[72] (bank 0) · THCON_SEC0_REG2_Out_data_format, THCON_SEC0_REG2_Throttle_mode, THCON_SEC0_REG2_Context_count, THCON_SEC0_REG2_Haloize_mode, THCON_SEC0_REG2_Tileize_mode, THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC0_REG2_Unpack_If_Sel, THCON_SEC0_REG2_Upsample_rate, THCON_SEC0_REG2_Ovrd_data_format, THCON_SEC0_REG2_Upsample_and_interleave, THCON_SEC0_REG2_Shift_amount_cntx0, THCON_SEC0_REG2_Shift_amount_cntx1, THCON_SEC0_REG2_Shift_amount_cntx2, THCON_SEC0_REG2_Shift_amount_cntx3 · 0xffef0120; write 0x00000025; cfg[72] (bank 0); THCON_SEC0_REG2_Out_data_format = 5; THCON_SEC0_REG2_Throttle_mode = 2; THCON_SEC0_REG2_Context_count = 0; THCON_SEC0_REG2_Haloize_mode = 0; THCON_SEC0_REG2_Tileize_mode = 0; THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC0_REG2_Unpack_If_Sel = 0; THCON_SEC0_REG2_Upsample_rate = 0; THCON_SEC0_REG2_Ovrd_data_format = 0; THCON_SEC0_REG2_Upsample_and_interleave = 0; THCON_SEC0_REG2_Shift_amount_cntx0 = 0; THCON_SEC0_REG2_Shift_amount_cntx1 = 0; THCON_SEC0_REG2_Shift_amount_cntx2 = 0; THCON_SEC0_REG2_Shift_amount_cntx3 = 0
    958: 00300413  addi         x8, x0, 3  # x8 = 0x00000003
    95c: 0283a223  sw           x8, 36(x7)  # cfg[73] (bank 0) · THCON_SEC0_REG2_Disable_zero_compress_cntx0, THCON_SEC0_REG2_Disable_zero_compress_cntx1, THCON_SEC0_REG2_Disable_zero_compress_cntx2, THCON_SEC0_REG2_Disable_zero_compress_cntx3, THCON_SEC0_REG2_Unpack_if_sel_cntx0, THCON_SEC0_REG2_Unpack_if_sel_cntx1, THCON_SEC0_REG2_Unpack_if_sel_cntx2, THCON_SEC0_REG2_Unpack_if_sel_cntx3, THCON_SEC0_REG2_Force_shared_exp, THCON_SEC0_REG2_Context_count_non_log2, THCON_SEC0_REG2_Context_count_non_log2_en, THCON_SEC0_REG2_Disable_zero_compress_cntx4, THCON_SEC0_REG2_Disable_zero_compress_cntx5, THCON_SEC0_REG2_Disable_zero_compress_cntx6, THCON_SEC0_REG2_Disable_zero_compress_cntx7, THCON_SEC0_REG2_Unpack_if_sel_cntx4, THCON_SEC0_REG2_Unpack_if_sel_cntx5, THCON_SEC0_REG2_Unpack_if_sel_cntx6, THCON_SEC0_REG2_Unpack_if_sel_cntx7, THCON_SEC0_REG2_Metadata_x_end · 0xffef0124; write 0x00000003; cfg[73] (bank 0); THCON_SEC0_REG2_Disable_zero_compress_cntx0 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx1 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx2 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx3 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx0 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx1 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx2 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx3 = 0; THCON_SEC0_REG2_Force_shared_exp = 0; THCON_SEC0_REG2_Context_count_non_log2 = 0; THCON_SEC0_REG2_Context_count_non_log2_en = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx4 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx5 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx6 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx7 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx4 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx5 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx6 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx7 = 0; THCON_SEC0_REG2_Metadata_x_end = 0
    960: 0203a423  sw           x0, 40(x7)  # cfg[74] (bank 0) · THCON_SEC0_REG2_Unpack_limit_address · 0xffef0128; write 0x00000000; cfg[74] (bank 0); THCON_SEC0_REG2_Unpack_limit_address = 0
    964: 0203a623  sw           x0, 44(x7)  # cfg[75] (bank 0) · THCON_SEC0_REG2_Unpack_fifo_size · 0xffef012c; write 0x00000000; cfg[75] (bank 0); THCON_SEC0_REG2_Unpack_fifo_size = 0
    968: fa03a823  sw           x0, -80(x7)  # cfg[44] (bank 0) · UNP0_ADDR_CTRL_XY_REG_0_Xstride, UNP0_ADDR_CTRL_XY_REG_0_Ystride · 0xffef00b0; write 0x00000000; cfg[44] (bank 0); UNP0_ADDR_CTRL_XY_REG_0_Xstride = 0; UNP0_ADDR_CTRL_XY_REG_0_Ystride = 0
    96c: fa03aa23  sw           x0, -76(x7)  # cfg[45] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_0_Zstride, UNP0_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef00b4; write 0x00000000; cfg[45] (bank 0); UNP0_ADDR_CTRL_ZW_REG_0_Zstride = 0; UNP0_ADDR_CTRL_ZW_REG_0_Wstride = 0
    970: 00200437  lui          x8, 0x00200  # x8 = 0x00200000
    974: 00240413  addi         x8, x8, 2  # x8 = 0x00200002
    978: fe83a023  sw           x8, -32(x7)  # cfg[56] (bank 0) · UNP0_ADDR_CTRL_XY_REG_1_Xstride, UNP0_ADDR_CTRL_XY_REG_1_Ystride · 0xffef00e0; write 0x00200002; cfg[56] (bank 0); UNP0_ADDR_CTRL_XY_REG_1_Xstride = 2; UNP0_ADDR_CTRL_XY_REG_1_Ystride = 32
    97c: 20000413  addi         x8, x0, 512  # x8 = 0x00000200
    980: fe83a223  sw           x8, -28(x7)  # cfg[57] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_1_Zstride, UNP0_ADDR_CTRL_ZW_REG_1_Wstride · 0xffef00e4; write 0x00000200; cfg[57] (bank 0); UNP0_ADDR_CTRL_ZW_REG_1_Zstride = 512; UNP0_ADDR_CTRL_ZW_REG_1_Wstride = 0
    984: fc03a023  sw           x0, -64(x7)  # cfg[48] (bank 0) · UNP0_ADDR_BASE_REG_0_Base · 0xffef00c0; write 0x00000000; cfg[48] (bank 0); UNP0_ADDR_BASE_REG_0_Base = 0
    988: fc03a223  sw           x0, -60(x7)  # cfg[49] (bank 0) · UNP0_ADDR_BASE_REG_1_Base · 0xffef00c4; write 0x00000000; cfg[49] (bank 0); UNP0_ADDR_BASE_REG_1_Base = 0
    98c: 10000413  addi         x8, x0, 256  # x8 = 0x00000100
    990: fc83a423  sw           x8, -56(x7)  # cfg[50] (bank 0) · UNP0_FORCED_SHARED_EXP_shared_exp, UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr · 0xffef00c8; write 0x00000100; cfg[50] (bank 0); UNP0_FORCED_SHARED_EXP_shared_exp = 0; UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr = 1
    994: fc03aa23  sw           x0, -44(x7)  # cfg[53] (bank 0) · UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val · 0xffef00d4; write 0x00000000; cfg[53] (bank 0); UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val = 0
    998: 00400437  lui          x8, 0x00400  # x8 = 0x00400000
    99c: 04040413  addi         x8, x8, 64  # x8 = 0x00400040
    9a0: 0483a823  sw           x8, 80(x7)  # cfg[84] (bank 0) · THCON_SEC0_REG5_Dest_cntx0_address, THCON_SEC0_REG5_Dest_cntx1_address · 0xffef0150; write 0x00400040; cfg[84] (bank 0); THCON_SEC0_REG5_Dest_cntx0_address = 64; THCON_SEC0_REG5_Dest_cntx1_address = 64
    9a4: 01000437  lui          x8, 0x01000  # x8 = 0x01000000
    9a8: 10040413  addi         x8, x8, 256  # x8 = 0x01000100
    9ac: 0483ac23  sw           x8, 88(x7)  # cfg[86] (bank 0) · THCON_SEC0_REG5_Tile_x_dim_cntx0, THCON_SEC0_REG5_Tile_x_dim_cntx1 · 0xffef0158; write 0x01000100; cfg[86] (bank 0); THCON_SEC0_REG5_Tile_x_dim_cntx0 = 256; THCON_SEC0_REG5_Tile_x_dim_cntx1 = 256
    9b0: 0603a823  sw           x0, 112(x7)  # cfg[92] (bank 0) · THCON_SEC0_REG7_Offset_address, THCON_SEC0_REG7_Unpack_data_format_cntx0, THCON_SEC0_REG7_Unpack_out_data_format_cntx0, THCON_SEC0_REG7_Unpack_data_format_cntx4, THCON_SEC0_REG7_Unpack_out_data_format_cntx4 · 0xffef0170; write 0x00000000; cfg[92] (bank 0); THCON_SEC0_REG7_Offset_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx4 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx4 = 0
    9b4: 0603aa23  sw           x0, 116(x7)  # cfg[93] (bank 0) · THCON_SEC0_REG7_Offset_cntx1_address, THCON_SEC0_REG7_Unpack_data_format_cntx1, THCON_SEC0_REG7_Unpack_out_data_format_cntx1, THCON_SEC0_REG7_Unpack_data_format_cntx5, THCON_SEC0_REG7_Unpack_out_data_format_cntx5 · 0xffef0174; write 0x00000000; cfg[93] (bank 0); THCON_SEC0_REG7_Offset_cntx1_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx5 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx5 = 0
    9b8: d50001de  RMWCIB2      Mask=64, Data=0, CfgRegAddr=119  # cfg[119] (current thread StateID); THCON_SEC1_REG1_Unp_LF8_4b_exp = 0
    9bc: ffef03b7  lui          x7, 0xffef0  # x7 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    9c0: 1c038393  addi         x7, x7, 448  # x7 = 0xffef01c0 · cfg[112] (bank 0) · THCON_SEC1_REG0_TileDescriptor
    9c4: 01000437  lui          x8, 0x01000  # x8 = 0x01000000
    9c8: 01540413  addi         x8, x8, 21  # x8 = 0x01000015
    9cc: 0083a023  sw           x8, 0(x7)  # cfg[112] (bank 0) · THCON_SEC1_REG0_TileDescriptor · 0xffef01c0; write 0x01000015; cfg[112] (bank 0); THCON_SEC1_REG0_TileDescriptor = 16777237
    9d0: 00040437  lui          x8, 0x00040  # x8 = 0x00040000
    9d4: 00140413  addi         x8, x8, 1  # x8 = 0x00040001
    9d8: 0083a223  sw           x8, 4(x7)  # cfg[113] (bank 0) (undocumented index) · 0xffef01c4; write 0x00040001; cfg[113] (bank 0) · fields not in ttsim
    9dc: 0003a423  sw           x0, 8(x7)  # cfg[114] (bank 0) (undocumented index) · 0xffef01c8; write 0x00000000; cfg[114] (bank 0) · fields not in ttsim
    9e0: 0003a623  sw           x0, 12(x7)  # cfg[115] (bank 0) (undocumented index) · 0xffef01cc; write 0x00000000; cfg[115] (bank 0) · fields not in ttsim
    9e4: 02500413  addi         x8, x0, 37  # x8 = 0x00000025
    9e8: 0283a023  sw           x8, 32(x7)  # cfg[120] (bank 0) · THCON_SEC1_REG2_Out_data_format, THCON_SEC1_REG2_Throttle_mode, THCON_SEC1_REG2_Context_count, THCON_SEC1_REG2_Haloize_mode, THCON_SEC1_REG2_Tileize_mode, THCON_SEC1_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC1_REG2_Unpack_If_Sel, THCON_SEC1_REG2_Upsample_rate, THCON_SEC1_REG2_Ovrd_data_format, THCON_SEC1_REG2_Upsample_and_interleave, THCON_SEC1_REG2_Shift_amount_cntx0, THCON_SEC1_REG2_Shift_amount_cntx1, THCON_SEC1_REG2_Shift_amount_cntx2, THCON_SEC1_REG2_Shift_amount_cntx3 · 0xffef01e0; write 0x00000025; cfg[120] (bank 0); THCON_SEC1_REG2_Out_data_format = 5; THCON_SEC1_REG2_Throttle_mode = 2; THCON_SEC1_REG2_Context_count = 0; THCON_SEC1_REG2_Haloize_mode = 0; THCON_SEC1_REG2_Tileize_mode = 0; THCON_SEC1_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC1_REG2_Unpack_If_Sel = 0; THCON_SEC1_REG2_Upsample_rate = 0; THCON_SEC1_REG2_Ovrd_data_format = 0; THCON_SEC1_REG2_Upsample_and_interleave = 0; THCON_SEC1_REG2_Shift_amount_cntx0 = 0; THCON_SEC1_REG2_Shift_amount_cntx1 = 0; THCON_SEC1_REG2_Shift_amount_cntx2 = 0; THCON_SEC1_REG2_Shift_amount_cntx3 = 0
    9ec: 00300413  addi         x8, x0, 3  # x8 = 0x00000003
    9f0: 0283a223  sw           x8, 36(x7)  # cfg[121] (bank 0) · THCON_SEC1_REG2_Disable_zero_compress_cntx0, THCON_SEC1_REG2_Disable_zero_compress_cntx1, THCON_SEC1_REG2_Disable_zero_compress_cntx2, THCON_SEC1_REG2_Disable_zero_compress_cntx3, THCON_SEC1_REG2_Unpack_if_sel_cntx0, THCON_SEC1_REG2_Unpack_if_sel_cntx1, THCON_SEC1_REG2_Unpack_if_sel_cntx2, THCON_SEC1_REG2_Unpack_if_sel_cntx3, THCON_SEC1_REG2_Force_shared_exp, THCON_SEC1_REG2_Context_count_non_log2, THCON_SEC1_REG2_Context_count_non_log2_en, THCON_SEC1_REG2_Disable_zero_compress_cntx4, THCON_SEC1_REG2_Disable_zero_compress_cntx5, THCON_SEC1_REG2_Disable_zero_compress_cntx6, THCON_SEC1_REG2_Disable_zero_compress_cntx7, THCON_SEC1_REG2_Unpack_if_sel_cntx4, THCON_SEC1_REG2_Unpack_if_sel_cntx5, THCON_SEC1_REG2_Unpack_if_sel_cntx6, THCON_SEC1_REG2_Unpack_if_sel_cntx7, THCON_SEC1_REG2_Metadata_x_end · 0xffef01e4; write 0x00000003; cfg[121] (bank 0); THCON_SEC1_REG2_Disable_zero_compress_cntx0 = 1; THCON_SEC1_REG2_Disable_zero_compress_cntx1 = 1; THCON_SEC1_REG2_Disable_zero_compress_cntx2 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx3 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx0 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx1 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx2 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx3 = 0; THCON_SEC1_REG2_Force_shared_exp = 0; THCON_SEC1_REG2_Context_count_non_log2 = 0; THCON_SEC1_REG2_Context_count_non_log2_en = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx4 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx5 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx6 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx7 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx4 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx5 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx6 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx7 = 0; THCON_SEC1_REG2_Metadata_x_end = 0
    9f4: 0203a423  sw           x0, 40(x7)  # cfg[122] (bank 0) · THCON_SEC1_REG2_Unpack_limit_address · 0xffef01e8; write 0x00000000; cfg[122] (bank 0); THCON_SEC1_REG2_Unpack_limit_address = 0
    9f8: 0203a623  sw           x0, 44(x7)  # cfg[123] (bank 0) · THCON_SEC1_REG2_Unpack_fifo_size · 0xffef01ec; write 0x00000000; cfg[123] (bank 0); THCON_SEC1_REG2_Unpack_fifo_size = 0
    9fc: ee03ac23  sw           x0, -264(x7)  # cfg[46] (bank 0) · UNP1_ADDR_CTRL_XY_REG_0_Xstride, UNP1_ADDR_CTRL_XY_REG_0_Ystride · 0xffef00b8; write 0x00000000; cfg[46] (bank 0); UNP1_ADDR_CTRL_XY_REG_0_Xstride = 0; UNP1_ADDR_CTRL_XY_REG_0_Ystride = 0
    a00: ee03ae23  sw           x0, -260(x7)  # cfg[47] (bank 0) · UNP1_ADDR_CTRL_ZW_REG_0_Zstride, UNP1_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef00bc; write 0x00000000; cfg[47] (bank 0); UNP1_ADDR_CTRL_ZW_REG_0_Zstride = 0; UNP1_ADDR_CTRL_ZW_REG_0_Wstride = 0
    a04: 00200437  lui          x8, 0x00200  # x8 = 0x00200000
    a08: 00240413  addi         x8, x8, 2  # x8 = 0x00200002
    a0c: f283a423  sw           x8, -216(x7)  # cfg[58] (bank 0) · UNP1_ADDR_CTRL_XY_REG_1_Xstride, UNP1_ADDR_CTRL_XY_REG_1_Ystride · 0xffef00e8; write 0x00200002; cfg[58] (bank 0); UNP1_ADDR_CTRL_XY_REG_1_Xstride = 2; UNP1_ADDR_CTRL_XY_REG_1_Ystride = 32
    a10: 20000413  addi         x8, x0, 512  # x8 = 0x00000200
    a14: f283a623  sw           x8, -212(x7)  # cfg[59] (bank 0) · UNP1_ADDR_CTRL_ZW_REG_1_Zstride, UNP1_ADDR_CTRL_ZW_REG_1_Wstride · 0xffef00ec; write 0x00000200; cfg[59] (bank 0); UNP1_ADDR_CTRL_ZW_REG_1_Zstride = 512; UNP1_ADDR_CTRL_ZW_REG_1_Wstride = 0
    a18: f203a823  sw           x0, -208(x7)  # cfg[60] (bank 0) · UNP1_ADDR_BASE_REG_0_Base · 0xffef00f0; write 0x00000000; cfg[60] (bank 0); UNP1_ADDR_BASE_REG_0_Base = 0
    a1c: f203aa23  sw           x0, -204(x7)  # cfg[61] (bank 0) · UNP1_ADDR_BASE_REG_1_Base · 0xffef00f4; write 0x00000000; cfg[61] (bank 0); UNP1_ADDR_BASE_REG_1_Base = 0
    a20: f203ac23  sw           x0, -200(x7)  # cfg[62] (bank 0) · UNP1_FORCED_SHARED_EXP_shared_exp, UNP1_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr · 0xffef00f8; write 0x00000000; cfg[62] (bank 0); UNP1_FORCED_SHARED_EXP_shared_exp = 0; UNP1_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr = 0
    a24: f203ae23  sw           x0, -196(x7)  # cfg[63] (bank 0) · UNP1_NOP_REG_CLR_VAL_nop_reg_clr_val · 0xffef00fc; write 0x00000000; cfg[63] (bank 0); UNP1_NOP_REG_CLR_VAL_nop_reg_clr_val = 0
    a28: 0403a823  sw           x0, 80(x7)  # cfg[132] (bank 0) · THCON_SEC1_REG5_Dest_cntx0_address, THCON_SEC1_REG5_Dest_cntx1_address · 0xffef0210; write 0x00000000; cfg[132] (bank 0); THCON_SEC1_REG5_Dest_cntx0_address = 0; THCON_SEC1_REG5_Dest_cntx1_address = 0
    a2c: 01000437  lui          x8, 0x01000  # x8 = 0x01000000
    a30: 10040413  addi         x8, x8, 256  # x8 = 0x01000100
    a34: 0483ac23  sw           x8, 88(x7)  # cfg[134] (bank 0) · THCON_SEC1_REG5_Tile_x_dim_cntx0, THCON_SEC1_REG5_Tile_x_dim_cntx1 · 0xffef0218; write 0x01000100; cfg[134] (bank 0); THCON_SEC1_REG5_Tile_x_dim_cntx0 = 256; THCON_SEC1_REG5_Tile_x_dim_cntx1 = 256
    a38: 0603a823  sw           x0, 112(x7)  # cfg[140] (bank 0) · THCON_SEC1_REG7_Offset_address, THCON_SEC1_REG7_Unpack_data_format_cntx0, THCON_SEC1_REG7_Unpack_out_data_format_cntx0, THCON_SEC1_REG7_Unpack_data_format_cntx4, THCON_SEC1_REG7_Unpack_out_data_format_cntx4 · 0xffef0230; write 0x00000000; cfg[140] (bank 0); THCON_SEC1_REG7_Offset_address = 0; THCON_SEC1_REG7_Unpack_data_format_cntx0 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx0 = 0; THCON_SEC1_REG7_Unpack_data_format_cntx4 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx4 = 0
    a3c: 0603aa23  sw           x0, 116(x7)  # cfg[141] (bank 0) · THCON_SEC1_REG7_Offset_cntx1_address, THCON_SEC1_REG7_Unpack_data_format_cntx1, THCON_SEC1_REG7_Unpack_out_data_format_cntx1, THCON_SEC1_REG7_Unpack_data_format_cntx5, THCON_SEC1_REG7_Unpack_out_data_format_cntx5 · 0xffef0234; write 0x00000000; cfg[141] (bank 0); THCON_SEC1_REG7_Offset_cntx1_address = 0; THCON_SEC1_REG7_Unpack_data_format_cntx1 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx1 = 0; THCON_SEC1_REG7_Unpack_data_format_cntx5 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx5 = 0
    a40: 324000ef  jal          x1, 0x00000d64  # target 0x00000d64; x1 = 0x00000a44
    a44: 320000ef  jal          x1, 0x00000d64  # target 0x00000d64; x1 = 0x00000a48
    a48: 31c000ef  jal          x1, 0x00000d64  # target 0x00000d64; x1 = 0x00000a4c
    a4c: 318000ef  jal          x1, 0x00000d64  # target 0x00000d64; x1 = 0x00000a50
    a50: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    a54: 84440413  addi         x8, x8, -1980  # x8 = 0xffb00844 · riscv_local_mem + 0x844
    a58: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x844 · 0xffb00844
    a5c: 00138393  addi         x7, x7, 1
    a60: 01039393  slli         x7, x7, 16
    a64: 0103d393  srli         x7, x7, 16
    a68: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    a6c: 84440413  addi         x8, x8, -1980  # x8 = 0xffb00844 · riscv_local_mem + 0x844
    a70: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x844 · 0xffb00844; write runtime value
    a74: ffb4b437  lui          x8, 0xffb4b  # x8 = 0xffb4b000
    a78: 02040413  addi         x8, x8, 32  # x8 = 0xffb4b020
    a7c: 00742023  sw           x7, 0(x8)  # 0xffb4b020; write runtime value
    a80: 0ff0000f  fence        0xf, 0xf
    a84: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    a88: 84058593  addi         x11, x11, -1984  # x11 = 0xffb00840 · riscv_local_mem + 0x840
    a8c: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x840 · 0xffb00840
    a90: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    a94: 80040413  addi         x8, x8, -2048  # x8 = 0x00000800
    a98: 008383b3  add          x7, x7, x8
    a9c: 0001a4b7  lui          x9, 0x0001a  # x9 = 0x0001a000
    aa0: 80048493  addi         x9, x9, -2048  # x9 = 0x00019800
    aa4: 0093e863  bltu         x7, x9, 0x00000ab4  # target 0x00000ab4
    aa8: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    aac: 80050513  addi         x10, x10, -2048  # x10 = 0x00000800
    ab0: 40a383b3  sub          x7, x7, x10
loc_ab4:
    ab4: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    ab8: 84058593  addi         x11, x11, -1984  # x11 = 0xffb00840 · riscv_local_mem + 0x840
    abc: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x840 · 0xffb00840; write runtime value
    ac0: 00128293  addi         x5, x5, 1
    ac4: e98ff06f  jal          x0, 0x0000015c  # target 0x0000015c
loc_ac8:
    ac8: ffb01337  lui          x6, 0xffb01  # x6 = 0xffb01000
    acc: 82c30313  addi         x6, x6, -2004  # x6 = 0xffb0082c · riscv_local_mem + 0x82c
    ad0: 00032283  lw           x5, 0(x6)  # riscv_local_mem + 0x82c · 0xffb0082c
    ad4: 00428293  addi         x5, x5, 4
    ad8: 01029293  slli         x5, x5, 16
    adc: 0102d293  srli         x5, x5, 16
    ae0: ffb01337  lui          x6, 0xffb01  # x6 = 0xffb01000
    ae4: 82c30313  addi         x6, x6, -2004  # x6 = 0xffb0082c · riscv_local_mem + 0x82c
    ae8: 00532023  sw           x5, 0(x6)  # riscv_local_mem + 0x82c · 0xffb0082c; write runtime value
    aec: ffb48337  lui          x6, 0xffb48  # x6 = 0xffb48000
    af0: 02030313  addi         x6, x6, 32  # x6 = 0xffb48020
    af4: 00532023  sw           x5, 0(x6)  # 0xffb48020; write runtime value
    af8: 0ff0000f  fence        0xf, 0xf
    afc: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    b00: 82848493  addi         x9, x9, -2008  # x9 = 0xffb00828 · riscv_local_mem + 0x828
    b04: 0004a283  lw           x5, 0(x9)  # riscv_local_mem + 0x828 · 0xffb00828
    b08: 00002337  lui          x6, 0x00002  # x6 = 0x00002000
    b0c: 006282b3  add          x5, x5, x6
    b10: 000113b7  lui          x7, 0x00011  # x7 = 0x00011000
    b14: 0072e663  bltu         x5, x7, 0x00000b20  # target 0x00000b20
    b18: 00002437  lui          x8, 0x00002  # x8 = 0x00002000
    b1c: 408282b3  sub          x5, x5, x8
loc_b20:
    b20: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    b24: 82848493  addi         x9, x9, -2008  # x9 = 0xffb00828 · riscv_local_mem + 0x828
    b28: 0054a023  sw           x5, 0(x9)  # riscv_local_mem + 0x828 · 0xffb00828; write runtime value
loc_b2c:
    b2c: 3fc0006f  jal          x0, 0x00000f28  # target 0x00000f28
loc_b30:
    b30: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    b34: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_b38:
    b38: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    b3c: 0feafa93  andi         x21, x21, 254
    b40: 000a8663  beq          x21, x0, 0x00000b4c  # target 0x00000b4c
    b44: 0ff0000f  fence        0xf, 0xf
    b48: ff1ff06f  jal          x0, 0x00000b38  # target 0x00000b38
loc_b4c:
    b4c: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    b50: d500011e  RMWCIB2      Mask=64, Data=0, CfgRegAddr=71  # cfg[71] (current thread StateID); THCON_SEC0_REG1_Unp_LF8_4b_exp = 0
    b54: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    b58: 100a0a13  addi         x20, x20, 256  # x20 = 0xffef0100 · cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor
    b5c: 01500a93  addi         x21, x0, 21  # x21 = 0x00000015
    b60: 015a2023  sw           x21, 0(x20)  # cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor · 0xffef0100; write 0x00000015; cfg[64] (bank 0); THCON_SEC0_REG0_TileDescriptor = 21
    b64: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
    b68: 001a8a93  addi         x21, x21, 1  # x21 = 0x00040001
    b6c: 015a2223  sw           x21, 4(x20)  # cfg[65] (bank 0) (undocumented index) · 0xffef0104; write 0x00040001; cfg[65] (bank 0) · fields not in ttsim
    b70: 000a2423  sw           x0, 8(x20)  # cfg[66] (bank 0) (undocumented index) · 0xffef0108; write 0x00000000; cfg[66] (bank 0) · fields not in ttsim
    b74: 000a2623  sw           x0, 12(x20)  # cfg[67] (bank 0) (undocumented index) · 0xffef010c; write 0x00000000; cfg[67] (bank 0) · fields not in ttsim
    b78: 02500a93  addi         x21, x0, 37  # x21 = 0x00000025
    b7c: 035a2023  sw           x21, 32(x20)  # cfg[72] (bank 0) · THCON_SEC0_REG2_Out_data_format, THCON_SEC0_REG2_Throttle_mode, THCON_SEC0_REG2_Context_count, THCON_SEC0_REG2_Haloize_mode, THCON_SEC0_REG2_Tileize_mode, THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC0_REG2_Unpack_If_Sel, THCON_SEC0_REG2_Upsample_rate, THCON_SEC0_REG2_Ovrd_data_format, THCON_SEC0_REG2_Upsample_and_interleave, THCON_SEC0_REG2_Shift_amount_cntx0, THCON_SEC0_REG2_Shift_amount_cntx1, THCON_SEC0_REG2_Shift_amount_cntx2, THCON_SEC0_REG2_Shift_amount_cntx3 · 0xffef0120; write 0x00000025; cfg[72] (bank 0); THCON_SEC0_REG2_Out_data_format = 5; THCON_SEC0_REG2_Throttle_mode = 2; THCON_SEC0_REG2_Context_count = 0; THCON_SEC0_REG2_Haloize_mode = 0; THCON_SEC0_REG2_Tileize_mode = 0; THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC0_REG2_Unpack_If_Sel = 0; THCON_SEC0_REG2_Upsample_rate = 0; THCON_SEC0_REG2_Ovrd_data_format = 0; THCON_SEC0_REG2_Upsample_and_interleave = 0; THCON_SEC0_REG2_Shift_amount_cntx0 = 0; THCON_SEC0_REG2_Shift_amount_cntx1 = 0; THCON_SEC0_REG2_Shift_amount_cntx2 = 0; THCON_SEC0_REG2_Shift_amount_cntx3 = 0
    b80: 00300a93  addi         x21, x0, 3  # x21 = 0x00000003
    b84: 035a2223  sw           x21, 36(x20)  # cfg[73] (bank 0) · THCON_SEC0_REG2_Disable_zero_compress_cntx0, THCON_SEC0_REG2_Disable_zero_compress_cntx1, THCON_SEC0_REG2_Disable_zero_compress_cntx2, THCON_SEC0_REG2_Disable_zero_compress_cntx3, THCON_SEC0_REG2_Unpack_if_sel_cntx0, THCON_SEC0_REG2_Unpack_if_sel_cntx1, THCON_SEC0_REG2_Unpack_if_sel_cntx2, THCON_SEC0_REG2_Unpack_if_sel_cntx3, THCON_SEC0_REG2_Force_shared_exp, THCON_SEC0_REG2_Context_count_non_log2, THCON_SEC0_REG2_Context_count_non_log2_en, THCON_SEC0_REG2_Disable_zero_compress_cntx4, THCON_SEC0_REG2_Disable_zero_compress_cntx5, THCON_SEC0_REG2_Disable_zero_compress_cntx6, THCON_SEC0_REG2_Disable_zero_compress_cntx7, THCON_SEC0_REG2_Unpack_if_sel_cntx4, THCON_SEC0_REG2_Unpack_if_sel_cntx5, THCON_SEC0_REG2_Unpack_if_sel_cntx6, THCON_SEC0_REG2_Unpack_if_sel_cntx7, THCON_SEC0_REG2_Metadata_x_end · 0xffef0124; write 0x00000003; cfg[73] (bank 0); THCON_SEC0_REG2_Disable_zero_compress_cntx0 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx1 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx2 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx3 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx0 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx1 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx2 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx3 = 0; THCON_SEC0_REG2_Force_shared_exp = 0; THCON_SEC0_REG2_Context_count_non_log2 = 0; THCON_SEC0_REG2_Context_count_non_log2_en = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx4 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx5 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx6 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx7 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx4 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx5 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx6 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx7 = 0; THCON_SEC0_REG2_Metadata_x_end = 0
    b88: 020a2423  sw           x0, 40(x20)  # cfg[74] (bank 0) · THCON_SEC0_REG2_Unpack_limit_address · 0xffef0128; write 0x00000000; cfg[74] (bank 0); THCON_SEC0_REG2_Unpack_limit_address = 0
    b8c: 020a2623  sw           x0, 44(x20)  # cfg[75] (bank 0) · THCON_SEC0_REG2_Unpack_fifo_size · 0xffef012c; write 0x00000000; cfg[75] (bank 0); THCON_SEC0_REG2_Unpack_fifo_size = 0
    b90: fa0a2823  sw           x0, -80(x20)  # cfg[44] (bank 0) · UNP0_ADDR_CTRL_XY_REG_0_Xstride, UNP0_ADDR_CTRL_XY_REG_0_Ystride · 0xffef00b0; write 0x00000000; cfg[44] (bank 0); UNP0_ADDR_CTRL_XY_REG_0_Xstride = 0; UNP0_ADDR_CTRL_XY_REG_0_Ystride = 0
    b94: fa0a2a23  sw           x0, -76(x20)  # cfg[45] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_0_Zstride, UNP0_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef00b4; write 0x00000000; cfg[45] (bank 0); UNP0_ADDR_CTRL_ZW_REG_0_Zstride = 0; UNP0_ADDR_CTRL_ZW_REG_0_Wstride = 0
    b98: 00200ab7  lui          x21, 0x00200  # x21 = 0x00200000
    b9c: 002a8a93  addi         x21, x21, 2  # x21 = 0x00200002
    ba0: ff5a2023  sw           x21, -32(x20)  # cfg[56] (bank 0) · UNP0_ADDR_CTRL_XY_REG_1_Xstride, UNP0_ADDR_CTRL_XY_REG_1_Ystride · 0xffef00e0; write 0x00200002; cfg[56] (bank 0); UNP0_ADDR_CTRL_XY_REG_1_Xstride = 2; UNP0_ADDR_CTRL_XY_REG_1_Ystride = 32
    ba4: 20000a93  addi         x21, x0, 512  # x21 = 0x00000200
    ba8: ff5a2223  sw           x21, -28(x20)  # cfg[57] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_1_Zstride, UNP0_ADDR_CTRL_ZW_REG_1_Wstride · 0xffef00e4; write 0x00000200; cfg[57] (bank 0); UNP0_ADDR_CTRL_ZW_REG_1_Zstride = 512; UNP0_ADDR_CTRL_ZW_REG_1_Wstride = 0
    bac: fc0a2023  sw           x0, -64(x20)  # cfg[48] (bank 0) · UNP0_ADDR_BASE_REG_0_Base · 0xffef00c0; write 0x00000000; cfg[48] (bank 0); UNP0_ADDR_BASE_REG_0_Base = 0
    bb0: fc0a2223  sw           x0, -60(x20)  # cfg[49] (bank 0) · UNP0_ADDR_BASE_REG_1_Base · 0xffef00c4; write 0x00000000; cfg[49] (bank 0); UNP0_ADDR_BASE_REG_1_Base = 0
    bb4: 10000a93  addi         x21, x0, 256  # x21 = 0x00000100
    bb8: fd5a2423  sw           x21, -56(x20)  # cfg[50] (bank 0) · UNP0_FORCED_SHARED_EXP_shared_exp, UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr · 0xffef00c8; write 0x00000100; cfg[50] (bank 0); UNP0_FORCED_SHARED_EXP_shared_exp = 0; UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr = 1
    bbc: fc0a2a23  sw           x0, -44(x20)  # cfg[53] (bank 0) · UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val · 0xffef00d4; write 0x00000000; cfg[53] (bank 0); UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val = 0
    bc0: 00400ab7  lui          x21, 0x00400  # x21 = 0x00400000
    bc4: 040a8a93  addi         x21, x21, 64  # x21 = 0x00400040
    bc8: 055a2823  sw           x21, 80(x20)  # cfg[84] (bank 0) · THCON_SEC0_REG5_Dest_cntx0_address, THCON_SEC0_REG5_Dest_cntx1_address · 0xffef0150; write 0x00400040; cfg[84] (bank 0); THCON_SEC0_REG5_Dest_cntx0_address = 64; THCON_SEC0_REG5_Dest_cntx1_address = 64
    bcc: 01000ab7  lui          x21, 0x01000  # x21 = 0x01000000
    bd0: 100a8a93  addi         x21, x21, 256  # x21 = 0x01000100
    bd4: 055a2c23  sw           x21, 88(x20)  # cfg[86] (bank 0) · THCON_SEC0_REG5_Tile_x_dim_cntx0, THCON_SEC0_REG5_Tile_x_dim_cntx1 · 0xffef0158; write 0x01000100; cfg[86] (bank 0); THCON_SEC0_REG5_Tile_x_dim_cntx0 = 256; THCON_SEC0_REG5_Tile_x_dim_cntx1 = 256
    bd8: 060a2823  sw           x0, 112(x20)  # cfg[92] (bank 0) · THCON_SEC0_REG7_Offset_address, THCON_SEC0_REG7_Unpack_data_format_cntx0, THCON_SEC0_REG7_Unpack_out_data_format_cntx0, THCON_SEC0_REG7_Unpack_data_format_cntx4, THCON_SEC0_REG7_Unpack_out_data_format_cntx4 · 0xffef0170; write 0x00000000; cfg[92] (bank 0); THCON_SEC0_REG7_Offset_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx4 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx4 = 0
    bdc: 060a2a23  sw           x0, 116(x20)  # cfg[93] (bank 0) · THCON_SEC0_REG7_Offset_cntx1_address, THCON_SEC0_REG7_Unpack_data_format_cntx1, THCON_SEC0_REG7_Unpack_out_data_format_cntx1, THCON_SEC0_REG7_Unpack_data_format_cntx5, THCON_SEC0_REG7_Unpack_out_data_format_cntx5 · 0xffef0174; write 0x00000000; cfg[93] (bank 0); THCON_SEC0_REG7_Offset_cntx1_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx5 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx5 = 0
    be0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    be4: 820a8a93  addi         x21, x21, -2016  # x21 = 0xffb00820 · riscv_local_mem + 0x820
    be8: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x820 · 0xffb00820
    bec: 004a5a13  srli         x20, x20, 4
    bf0: fffa0a13  addi         x20, x20, -1
    bf4: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    bf8: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    bfc: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    c00: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    c04: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    c08: c8140012  SETC16       setc16_reg=5, setc16_value=4  # thread_cfg[5] (current thread); SRCA_SET_Base = 0; SRCA_SET_SetOvrdWithAddr = 1
    c0c: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    c10: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    c14: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    c18: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    c1c: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    c20: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    c24: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    c28: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    c2c: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    c30: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    c34: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    c38: 01507033  and          x0, x0, x21
    c3c: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    c40: 00400a93  addi         x21, x0, 4  # x21 = 0x00000004
    c44: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000004
    c48: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
    c4c: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000001
    c50: 42008ab7  lui          x21, 0x42008  # x21 = 0x42008000
    c54: 0c1a8a93  addi         x21, x21, 193  # x21 = 0x420080c1
    c58: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x420080c1; MOP template instruction · UNPACR Unpack_block_selection=0, AddrMode=1, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    c5c: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    c60: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x02000000; MOP template instruction · NOP
    c64: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    c68: 43800ab7  lui          x21, 0x43800  # x21 = 0x43800000
    c6c: 101a8a93  addi         x21, x21, 257  # x21 = 0x43800101
    c70: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    c74: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    c78: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    c7c: 43800ab7  lui          x21, 0x43800  # x21 = 0x43800000
    c80: 101a8a93  addi         x21, x21, 257  # x21 = 0x43800101
    c84: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    c88: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    c8c: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    c90: 824c0c13  addi         x24, x24, -2012  # x24 = 0xffb00824 · riscv_local_mem + 0x824
    c94: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x824 · 0xffb00824
    c98: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_c9c:
    c9c: ffb4dc37  lui          x24, 0xffb4d  # x24 = 0xffb4d000
    ca0: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb4d028
    ca4: 000c5a83  lhu          x21, 0(x24)  # 0xffb4d028
    ca8: 414a8b33  sub          x22, x21, x20
    cac: 010b1b13  slli         x22, x22, 16
    cb0: 010b5b13  srli         x22, x22, 16
    cb4: 017b7663  bgeu         x22, x23, 0x00000cc0  # target 0x00000cc0
    cb8: 0ff0000f  fence        0xf, 0xf
    cbc: fe1ff06f  jal          x0, 0x00000c9c  # target 0x00000c9c
loc_cc0:
    cc0: 0ff0000f  fence        0xf, 0xf
    cc4: 88100082  STALLWAIT    stall_res=8, wait_res=32  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR
    cc8: 788ff001  SETADCXX     CntSetMask=1, x_end2=255, x_start=0
    ccc: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    cd0: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    cd4: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    cd8: 8810000a  STALLWAIT    stall_res=8, wait_res=2  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0
    cdc: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    ce0: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    ce4: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    ce8: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    cec: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    cf0: 01507033  and          x0, x0, x21
    cf4: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    cf8: 824a8a93  addi         x21, x21, -2012  # x21 = 0xffb00824 · riscv_local_mem + 0x824
    cfc: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x824 · 0xffb00824
    d00: 001a0a13  addi         x20, x20, 1
    d04: 010a1a13  slli         x20, x20, 16
    d08: 010a5a13  srli         x20, x20, 16
    d0c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    d10: 824a8a93  addi         x21, x21, -2012  # x21 = 0xffb00824 · riscv_local_mem + 0x824
    d14: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x824 · 0xffb00824; write runtime value
    d18: ffb4dab7  lui          x21, 0xffb4d  # x21 = 0xffb4d000
    d1c: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb4d020
    d20: 014aa023  sw           x20, 0(x21)  # 0xffb4d020; write runtime value
    d24: 0ff0000f  fence        0xf, 0xf
    d28: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    d2c: 820c0c13  addi         x24, x24, -2016  # x24 = 0xffb00820 · riscv_local_mem + 0x820
    d30: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x820 · 0xffb00820
    d34: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    d38: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    d3c: 015a0a33  add          x20, x20, x21
    d40: 00022b37  lui          x22, 0x00022  # x22 = 0x00022000
    d44: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00021800
    d48: 016a6663  bltu         x20, x22, 0x00000d54  # target 0x00000d54
    d4c: 00002bb7  lui          x23, 0x00002  # x23 = 0x00002000
    d50: 417a0a33  sub          x20, x20, x23
loc_d54:
    d54: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    d58: 820c0c13  addi         x24, x24, -2016  # x24 = 0xffb00820 · riscv_local_mem + 0x820
    d5c: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x820 · 0xffb00820; write runtime value
    d60: 00008067  jalr         x0, 0(x1)
loc_d64:
    d64: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    d68: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_d6c:
    d6c: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    d70: 0feafa93  andi         x21, x21, 254
    d74: 000a8663  beq          x21, x0, 0x00000d80  # target 0x00000d80
    d78: 0ff0000f  fence        0xf, 0xf
    d7c: ff1ff06f  jal          x0, 0x00000d6c  # target 0x00000d6c
loc_d80:
    d80: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    d84: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    d88: 838a8a93  addi         x21, x21, -1992  # x21 = 0xffb00838 · riscv_local_mem + 0x838
    d8c: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x838 · 0xffb00838
    d90: 004a5a13  srli         x20, x20, 4
    d94: fffa0a13  addi         x20, x20, -1
    d98: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    d9c: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    da0: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    da4: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    da8: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    dac: c8140012  SETC16       setc16_reg=5, setc16_value=4  # thread_cfg[5] (current thread); SRCA_SET_Base = 0; SRCA_SET_SetOvrdWithAddr = 1
    db0: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    db4: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_db8:
    db8: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    dbc: 0feafa93  andi         x21, x21, 254
    dc0: 000a8663  beq          x21, x0, 0x00000dcc  # target 0x00000dcc
    dc4: 0ff0000f  fence        0xf, 0xf
    dc8: ff1ff06f  jal          x0, 0x00000db8  # target 0x00000db8
loc_dcc:
    dcc: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    dd0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    dd4: 840a8a93  addi         x21, x21, -1984  # x21 = 0xffb00840 · riscv_local_mem + 0x840
    dd8: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x840 · 0xffb00840
    ddc: 004a5a13  srli         x20, x20, 4
    de0: fffa0a13  addi         x20, x20, -1
    de4: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    de8: 1f0a8a93  addi         x21, x21, 496  # x21 = 0xffef01f0 · cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address
    dec: 014aa023  sw           x20, 0(x21)  # cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address · 0xffef01f0; write runtime value; cfg[124] (bank 0); THCON_SEC1_REG3_Base_address = runtime
    df0: 014aa223  sw           x20, 4(x21)  # cfg[125] (bank 0) · THCON_SEC1_REG3_Base_cntx1_address · 0xffef01f4; write runtime value; cfg[125] (bank 0); THCON_SEC1_REG3_Base_cntx1_address = runtime
    df4: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    df8: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    dfc: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    e00: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    e04: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    e08: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    e0c: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    e10: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    e14: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    e18: 844c0c13  addi         x24, x24, -1980  # x24 = 0xffb00844 · riscv_local_mem + 0x844
    e1c: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x844 · 0xffb00844
    e20: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_e24:
    e24: ffb4bc37  lui          x24, 0xffb4b  # x24 = 0xffb4b000
    e28: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb4b028
    e2c: 000c5a83  lhu          x21, 0(x24)  # 0xffb4b028
    e30: 414a8b33  sub          x22, x21, x20
    e34: 010b1b13  slli         x22, x22, 16
    e38: 010b5b13  srli         x22, x22, 16
    e3c: 017b7663  bgeu         x22, x23, 0x00000e48  # target 0x00000e48
    e40: 0ff0000f  fence        0xf, 0xf
    e44: fe1ff06f  jal          x0, 0x00000e24  # target 0x00000e24
loc_e48:
    e48: 0ff0000f  fence        0xf, 0xf
    e4c: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    e50: 83cc0c13  addi         x24, x24, -1988  # x24 = 0xffb0083c · riscv_local_mem + 0x83c
    e54: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x83c · 0xffb0083c
    e58: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_e5c:
    e5c: ffb4ac37  lui          x24, 0xffb4a  # x24 = 0xffb4a000
    e60: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb4a028
    e64: 000c5a83  lhu          x21, 0(x24)  # 0xffb4a028
    e68: 414a8b33  sub          x22, x21, x20
    e6c: 010b1b13  slli         x22, x22, 16
    e70: 010b5b13  srli         x22, x22, 16
    e74: 017b7663  bgeu         x22, x23, 0x00000e80  # target 0x00000e80
    e78: 0ff0000f  fence        0xf, 0xf
    e7c: fe1ff06f  jal          x0, 0x00000e5c  # target 0x00000e5c
loc_e80:
    e80: 0ff0000f  fence        0xf, 0xf
    e84: 88100182  STALLWAIT    stall_res=8, wait_res=96  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR | Wait.SRCB_CLR
    e88: 78bff001  SETADCXX     CntSetMask=1, x_end2=1023, x_start=0
    e8c: 793ff001  SETADCXX     CntSetMask=2, x_end2=1023, x_start=0
    e90: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    e94: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    e98: 0a000305  UNPACR       Unpack_block_selection=1, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    e9c: 08000305  UNPACR       Unpack_block_selection=0, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    ea0: 8810001a  STALLWAIT    stall_res=8, wait_res=6  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0 | Wait.UNPACK1
    ea4: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    ea8: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    eac: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    eb0: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    eb4: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    eb8: 01507033  and          x0, x0, x21
    ebc: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    ec0: 83ca8a93  addi         x21, x21, -1988  # x21 = 0xffb0083c · riscv_local_mem + 0x83c
    ec4: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x83c · 0xffb0083c
    ec8: 001a0a13  addi         x20, x20, 1
    ecc: 010a1a13  slli         x20, x20, 16
    ed0: 010a5a13  srli         x20, x20, 16
    ed4: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    ed8: 83ca8a93  addi         x21, x21, -1988  # x21 = 0xffb0083c · riscv_local_mem + 0x83c
    edc: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x83c · 0xffb0083c; write runtime value
    ee0: ffb4aab7  lui          x21, 0xffb4a  # x21 = 0xffb4a000
    ee4: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb4a020
    ee8: 014aa023  sw           x20, 0(x21)  # 0xffb4a020; write runtime value
    eec: 0ff0000f  fence        0xf, 0xf
    ef0: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    ef4: 838c0c13  addi         x24, x24, -1992  # x24 = 0xffb00838 · riscv_local_mem + 0x838
    ef8: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x838 · 0xffb00838
    efc: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    f00: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    f04: 015a0a33  add          x20, x20, x21
    f08: 00019b37  lui          x22, 0x00019  # x22 = 0x00019000
    f0c: 016a6663  bltu         x20, x22, 0x00000f18  # target 0x00000f18
    f10: 00004bb7  lui          x23, 0x00004  # x23 = 0x00004000
    f14: 417a0a33  sub          x20, x20, x23
loc_f18:
    f18: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    f1c: 838c0c13  addi         x24, x24, -1992  # x24 = 0xffb00838 · riscv_local_mem + 0x838
    f20: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x838 · 0xffb00838; write runtime value
    f24: 00008067  jalr         x0, 0(x1)
    f28:           j FW_TRISC0+4   # return to firmware, linked at install
