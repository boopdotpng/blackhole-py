# llama3 8b-bf16 decode: qkv, trisc0. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x7c0=e2e_x_a_decode_token, 0x7c4=e2e_l0_q, 0x7c8=e2e_l0_k, 0x7cc=e2e_l0_v, 0x7d0=e2e_l0_input_norm, 0x8080=e2e_q_compact, 0x8084=e2e_l0_q_row_start, 0x8088=e2e_k_compact, 0x808c=e2e_l0_k_row_start, 0x8090=e2e_v_compact, 0x8094=e2e_l0_v_row_start, 0x8098=e2e_l0_q_rows, 0x809c=e2e_l0_k_rows, 0x80a0=e2e_l0_v_rows, 0x80a4=dram_port
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama3.py installs it resident in L1 at 0x12000+ per core.

      0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
      4: 820a8a93  addi         x21, x21, -2016  # x21 = 0xffb00820 · riscv_local_mem + 0x820
      8: 00099b37  lui          x22, 0x00099  # x22 = 0x00099000
      c: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00098800
     10: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x820 · 0xffb00820; write 0x00098800
     14: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     18: 824a8a93  addi         x21, x21, -2012  # x21 = 0xffb00824 · riscv_local_mem + 0x824
     1c: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x824 · 0xffb00824; write 0x00000000
     20: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     24: 82820213  addi         x4, x4, -2008  # x4 = 0xffb00828 · riscv_local_mem + 0x828
     28: 000952b7  lui          x5, 0x00095  # x5 = 0x00095000
     2c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x828 · 0xffb00828; write 0x00095000
     30: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     34: 82c20213  addi         x4, x4, -2004  # x4 = 0xffb0082c · riscv_local_mem + 0x82c
     38: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x82c · 0xffb0082c; write 0x00000000
     3c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     40: 830a8a93  addi         x21, x21, -2000  # x21 = 0xffb00830 · riscv_local_mem + 0x830
     44: 00090b37  lui          x22, 0x00090  # x22 = 0x00090000
     48: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x830 · 0xffb00830; write 0x00090000
     4c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     50: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
     54: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834; write 0x00000000
     58: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
     5c: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_60:
     60: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
     64: 0feafa93  andi         x21, x21, 254
     68: 000a8663  beq          x21, x0, 0x00000074  # target 0x00000074
     6c: 0ff0000f  fence        0xf, 0xf
     70: ff1ff06f  jal          x0, 0x00000060  # target 0x00000060
loc_74:
     74: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
     78: d500011e  RMWCIB2      Mask=64, Data=0, CfgRegAddr=71  # cfg[71] (current thread StateID); THCON_SEC0_REG1_Unp_LF8_4b_exp = 0
     7c: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
     80: 100a0a13  addi         x20, x20, 256  # x20 = 0xffef0100 · cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor
     84: 01500a93  addi         x21, x0, 21  # x21 = 0x00000015
     88: 015a2023  sw           x21, 0(x20)  # cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor · 0xffef0100; write 0x00000015; cfg[64] (bank 0); THCON_SEC0_REG0_TileDescriptor = 21
     8c: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
     90: 001a8a93  addi         x21, x21, 1  # x21 = 0x00040001
     94: 015a2223  sw           x21, 4(x20)  # cfg[65] (bank 0) (undocumented index) · 0xffef0104; write 0x00040001; cfg[65] (bank 0) · fields not in ttsim
     98: 000a2423  sw           x0, 8(x20)  # cfg[66] (bank 0) (undocumented index) · 0xffef0108; write 0x00000000; cfg[66] (bank 0) · fields not in ttsim
     9c: 000a2623  sw           x0, 12(x20)  # cfg[67] (bank 0) (undocumented index) · 0xffef010c; write 0x00000000; cfg[67] (bank 0) · fields not in ttsim
     a0: 02500a93  addi         x21, x0, 37  # x21 = 0x00000025
     a4: 035a2023  sw           x21, 32(x20)  # cfg[72] (bank 0) · THCON_SEC0_REG2_Out_data_format, THCON_SEC0_REG2_Throttle_mode, THCON_SEC0_REG2_Context_count, THCON_SEC0_REG2_Haloize_mode, THCON_SEC0_REG2_Tileize_mode, THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC0_REG2_Unpack_If_Sel, THCON_SEC0_REG2_Upsample_rate, THCON_SEC0_REG2_Ovrd_data_format, THCON_SEC0_REG2_Upsample_and_interleave, THCON_SEC0_REG2_Shift_amount_cntx0, THCON_SEC0_REG2_Shift_amount_cntx1, THCON_SEC0_REG2_Shift_amount_cntx2, THCON_SEC0_REG2_Shift_amount_cntx3 · 0xffef0120; write 0x00000025; cfg[72] (bank 0); THCON_SEC0_REG2_Out_data_format = 5; THCON_SEC0_REG2_Throttle_mode = 2; THCON_SEC0_REG2_Context_count = 0; THCON_SEC0_REG2_Haloize_mode = 0; THCON_SEC0_REG2_Tileize_mode = 0; THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC0_REG2_Unpack_If_Sel = 0; THCON_SEC0_REG2_Upsample_rate = 0; THCON_SEC0_REG2_Ovrd_data_format = 0; THCON_SEC0_REG2_Upsample_and_interleave = 0; THCON_SEC0_REG2_Shift_amount_cntx0 = 0; THCON_SEC0_REG2_Shift_amount_cntx1 = 0; THCON_SEC0_REG2_Shift_amount_cntx2 = 0; THCON_SEC0_REG2_Shift_amount_cntx3 = 0
     a8: 00300a93  addi         x21, x0, 3  # x21 = 0x00000003
     ac: 035a2223  sw           x21, 36(x20)  # cfg[73] (bank 0) · THCON_SEC0_REG2_Disable_zero_compress_cntx0, THCON_SEC0_REG2_Disable_zero_compress_cntx1, THCON_SEC0_REG2_Disable_zero_compress_cntx2, THCON_SEC0_REG2_Disable_zero_compress_cntx3, THCON_SEC0_REG2_Unpack_if_sel_cntx0, THCON_SEC0_REG2_Unpack_if_sel_cntx1, THCON_SEC0_REG2_Unpack_if_sel_cntx2, THCON_SEC0_REG2_Unpack_if_sel_cntx3, THCON_SEC0_REG2_Force_shared_exp, THCON_SEC0_REG2_Context_count_non_log2, THCON_SEC0_REG2_Context_count_non_log2_en, THCON_SEC0_REG2_Disable_zero_compress_cntx4, THCON_SEC0_REG2_Disable_zero_compress_cntx5, THCON_SEC0_REG2_Disable_zero_compress_cntx6, THCON_SEC0_REG2_Disable_zero_compress_cntx7, THCON_SEC0_REG2_Unpack_if_sel_cntx4, THCON_SEC0_REG2_Unpack_if_sel_cntx5, THCON_SEC0_REG2_Unpack_if_sel_cntx6, THCON_SEC0_REG2_Unpack_if_sel_cntx7, THCON_SEC0_REG2_Metadata_x_end · 0xffef0124; write 0x00000003; cfg[73] (bank 0); THCON_SEC0_REG2_Disable_zero_compress_cntx0 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx1 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx2 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx3 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx0 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx1 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx2 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx3 = 0; THCON_SEC0_REG2_Force_shared_exp = 0; THCON_SEC0_REG2_Context_count_non_log2 = 0; THCON_SEC0_REG2_Context_count_non_log2_en = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx4 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx5 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx6 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx7 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx4 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx5 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx6 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx7 = 0; THCON_SEC0_REG2_Metadata_x_end = 0
     b0: 020a2423  sw           x0, 40(x20)  # cfg[74] (bank 0) · THCON_SEC0_REG2_Unpack_limit_address · 0xffef0128; write 0x00000000; cfg[74] (bank 0); THCON_SEC0_REG2_Unpack_limit_address = 0
     b4: 020a2623  sw           x0, 44(x20)  # cfg[75] (bank 0) · THCON_SEC0_REG2_Unpack_fifo_size · 0xffef012c; write 0x00000000; cfg[75] (bank 0); THCON_SEC0_REG2_Unpack_fifo_size = 0
     b8: fa0a2823  sw           x0, -80(x20)  # cfg[44] (bank 0) · UNP0_ADDR_CTRL_XY_REG_0_Xstride, UNP0_ADDR_CTRL_XY_REG_0_Ystride · 0xffef00b0; write 0x00000000; cfg[44] (bank 0); UNP0_ADDR_CTRL_XY_REG_0_Xstride = 0; UNP0_ADDR_CTRL_XY_REG_0_Ystride = 0
     bc: fa0a2a23  sw           x0, -76(x20)  # cfg[45] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_0_Zstride, UNP0_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef00b4; write 0x00000000; cfg[45] (bank 0); UNP0_ADDR_CTRL_ZW_REG_0_Zstride = 0; UNP0_ADDR_CTRL_ZW_REG_0_Wstride = 0
     c0: 00200ab7  lui          x21, 0x00200  # x21 = 0x00200000
     c4: 002a8a93  addi         x21, x21, 2  # x21 = 0x00200002
     c8: ff5a2023  sw           x21, -32(x20)  # cfg[56] (bank 0) · UNP0_ADDR_CTRL_XY_REG_1_Xstride, UNP0_ADDR_CTRL_XY_REG_1_Ystride · 0xffef00e0; write 0x00200002; cfg[56] (bank 0); UNP0_ADDR_CTRL_XY_REG_1_Xstride = 2; UNP0_ADDR_CTRL_XY_REG_1_Ystride = 32
     cc: 20000a93  addi         x21, x0, 512  # x21 = 0x00000200
     d0: ff5a2223  sw           x21, -28(x20)  # cfg[57] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_1_Zstride, UNP0_ADDR_CTRL_ZW_REG_1_Wstride · 0xffef00e4; write 0x00000200; cfg[57] (bank 0); UNP0_ADDR_CTRL_ZW_REG_1_Zstride = 512; UNP0_ADDR_CTRL_ZW_REG_1_Wstride = 0
     d4: fc0a2023  sw           x0, -64(x20)  # cfg[48] (bank 0) · UNP0_ADDR_BASE_REG_0_Base · 0xffef00c0; write 0x00000000; cfg[48] (bank 0); UNP0_ADDR_BASE_REG_0_Base = 0
     d8: fc0a2223  sw           x0, -60(x20)  # cfg[49] (bank 0) · UNP0_ADDR_BASE_REG_1_Base · 0xffef00c4; write 0x00000000; cfg[49] (bank 0); UNP0_ADDR_BASE_REG_1_Base = 0
     dc: 10000a93  addi         x21, x0, 256  # x21 = 0x00000100
     e0: fd5a2423  sw           x21, -56(x20)  # cfg[50] (bank 0) · UNP0_FORCED_SHARED_EXP_shared_exp, UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr · 0xffef00c8; write 0x00000100; cfg[50] (bank 0); UNP0_FORCED_SHARED_EXP_shared_exp = 0; UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr = 1
     e4: fc0a2a23  sw           x0, -44(x20)  # cfg[53] (bank 0) · UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val · 0xffef00d4; write 0x00000000; cfg[53] (bank 0); UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val = 0
     e8: 00400ab7  lui          x21, 0x00400  # x21 = 0x00400000
     ec: 040a8a93  addi         x21, x21, 64  # x21 = 0x00400040
     f0: 055a2823  sw           x21, 80(x20)  # cfg[84] (bank 0) · THCON_SEC0_REG5_Dest_cntx0_address, THCON_SEC0_REG5_Dest_cntx1_address · 0xffef0150; write 0x00400040; cfg[84] (bank 0); THCON_SEC0_REG5_Dest_cntx0_address = 64; THCON_SEC0_REG5_Dest_cntx1_address = 64
     f4: 01000ab7  lui          x21, 0x01000  # x21 = 0x01000000
     f8: 100a8a93  addi         x21, x21, 256  # x21 = 0x01000100
     fc: 055a2c23  sw           x21, 88(x20)  # cfg[86] (bank 0) · THCON_SEC0_REG5_Tile_x_dim_cntx0, THCON_SEC0_REG5_Tile_x_dim_cntx1 · 0xffef0158; write 0x01000100; cfg[86] (bank 0); THCON_SEC0_REG5_Tile_x_dim_cntx0 = 256; THCON_SEC0_REG5_Tile_x_dim_cntx1 = 256
    100: 060a2823  sw           x0, 112(x20)  # cfg[92] (bank 0) · THCON_SEC0_REG7_Offset_address, THCON_SEC0_REG7_Unpack_data_format_cntx0, THCON_SEC0_REG7_Unpack_out_data_format_cntx0, THCON_SEC0_REG7_Unpack_data_format_cntx4, THCON_SEC0_REG7_Unpack_out_data_format_cntx4 · 0xffef0170; write 0x00000000; cfg[92] (bank 0); THCON_SEC0_REG7_Offset_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx4 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx4 = 0
    104: 060a2a23  sw           x0, 116(x20)  # cfg[93] (bank 0) · THCON_SEC0_REG7_Offset_cntx1_address, THCON_SEC0_REG7_Unpack_data_format_cntx1, THCON_SEC0_REG7_Unpack_out_data_format_cntx1, THCON_SEC0_REG7_Unpack_data_format_cntx5, THCON_SEC0_REG7_Unpack_out_data_format_cntx5 · 0xffef0174; write 0x00000000; cfg[93] (bank 0); THCON_SEC0_REG7_Offset_cntx1_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx5 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx5 = 0
    108: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    10c: 820a8a93  addi         x21, x21, -2016  # x21 = 0xffb00820 · riscv_local_mem + 0x820
    110: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x820 · 0xffb00820
    114: 004a5a13  srli         x20, x20, 4
    118: fffa0a13  addi         x20, x20, -1
    11c: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    120: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    124: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    128: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    12c: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    130: c8140012  SETC16       setc16_reg=5, setc16_value=4  # thread_cfg[5] (current thread); SRCA_SET_Base = 0; SRCA_SET_SetOvrdWithAddr = 1
    134: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    138: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    13c: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    140: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    144: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    148: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    14c: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    150: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    154: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    158: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    15c: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    160: 01507033  and          x0, x0, x21
    164: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    168: 00400a93  addi         x21, x0, 4  # x21 = 0x00000004
    16c: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000004
    170: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
    174: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000001
    178: 42008ab7  lui          x21, 0x42008  # x21 = 0x42008000
    17c: 0c1a8a93  addi         x21, x21, 193  # x21 = 0x420080c1
    180: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x420080c1; MOP template instruction · UNPACR Unpack_block_selection=0, AddrMode=1, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    184: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    188: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x02000000; MOP template instruction · NOP 
    18c: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP 
    190: 43800ab7  lui          x21, 0x43800  # x21 = 0x43800000
    194: 101a8a93  addi         x21, x21, 257  # x21 = 0x43800101
    198: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    19c: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    1a0: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP 
    1a4: 43800ab7  lui          x21, 0x43800  # x21 = 0x43800000
    1a8: 101a8a93  addi         x21, x21, 257  # x21 = 0x43800101
    1ac: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    1b0: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    1b4: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    1b8: 824c0c13  addi         x24, x24, -2012  # x24 = 0xffb00824 · riscv_local_mem + 0x824
    1bc: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x824 · 0xffb00824
    1c0: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_1c4:
    1c4: ffb4ec37  lui          x24, 0xffb4e  # x24 = 0xffb4e000
    1c8: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb4e028
    1cc: 000c5a83  lhu          x21, 0(x24)  # 0xffb4e028
    1d0: 414a8b33  sub          x22, x21, x20
    1d4: 010b1b13  slli         x22, x22, 16
    1d8: 010b5b13  srli         x22, x22, 16
    1dc: 017b7663  bgeu         x22, x23, 0x000001e8  # target 0x000001e8
    1e0: 0ff0000f  fence        0xf, 0xf
    1e4: fe1ff06f  jal          x0, 0x000001c4  # target 0x000001c4
loc_1e8:
    1e8: 0ff0000f  fence        0xf, 0xf
    1ec: 88100082  STALLWAIT    stall_res=8, wait_res=32  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR
    1f0: 788ff001  SETADCXX     CntSetMask=1, x_end2=255, x_start=0
    1f4: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    1f8: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    1fc: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    200: 8810000a  STALLWAIT    stall_res=8, wait_res=2  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0
    204: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    208: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    20c: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    210: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    214: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    218: 01507033  and          x0, x0, x21
    21c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    220: 824a8a93  addi         x21, x21, -2012  # x21 = 0xffb00824 · riscv_local_mem + 0x824
    224: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x824 · 0xffb00824
    228: 001a0a13  addi         x20, x20, 1
    22c: 010a1a13  slli         x20, x20, 16
    230: 010a5a13  srli         x20, x20, 16
    234: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    238: 824a8a93  addi         x21, x21, -2012  # x21 = 0xffb00824 · riscv_local_mem + 0x824
    23c: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x824 · 0xffb00824; write runtime value
    240: ffb4eab7  lui          x21, 0xffb4e  # x21 = 0xffb4e000
    244: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb4e020
    248: 014aa023  sw           x20, 0(x21)  # 0xffb4e020; write runtime value
    24c: 0ff0000f  fence        0xf, 0xf
    250: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    254: 820c0c13  addi         x24, x24, -2016  # x24 = 0xffb00820 · riscv_local_mem + 0x820
    258: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x820 · 0xffb00820
    25c: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    260: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    264: 015a0a33  add          x20, x20, x21
    268: 0009db37  lui          x22, 0x0009d  # x22 = 0x0009d000
    26c: 800b0b13  addi         x22, x22, -2048  # x22 = 0x0009c800
    270: 016a6663  bltu         x20, x22, 0x0000027c  # target 0x0000027c
    274: 00004bb7  lui          x23, 0x00004  # x23 = 0x00004000
    278: 417a0a33  sub          x20, x20, x23
loc_27c:
    27c: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    280: 820c0c13  addi         x24, x24, -2016  # x24 = 0xffb00820 · riscv_local_mem + 0x820
    284: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x820 · 0xffb00820; write runtime value
    288: 00000213  addi         x4, x0, 0  # x4 = 0x00000000
    28c: 00700293  addi         x5, x0, 7  # x5 = 0x00000007
loc_290:
    290: 1a527663  bgeu         x4, x5, 0x0000043c  # target 0x0000043c
    294: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    298: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_29c:
    29c: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    2a0: 0feafa93  andi         x21, x21, 254
    2a4: 000a8663  beq          x21, x0, 0x000002b0  # target 0x000002b0
    2a8: 0ff0000f  fence        0xf, 0xf
    2ac: ff1ff06f  jal          x0, 0x0000029c  # target 0x0000029c
loc_2b0:
    2b0: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    2b4: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    2b8: 820a8a93  addi         x21, x21, -2016  # x21 = 0xffb00820 · riscv_local_mem + 0x820
    2bc: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x820 · 0xffb00820
    2c0: 004a5a13  srli         x20, x20, 4
    2c4: fffa0a13  addi         x20, x20, -1
    2c8: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    2cc: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    2d0: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    2d4: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    2d8: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    2dc: c8140012  SETC16       setc16_reg=5, setc16_value=4  # thread_cfg[5] (current thread); SRCA_SET_Base = 0; SRCA_SET_SetOvrdWithAddr = 1
    2e0: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    2e4: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    2e8: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    2ec: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    2f0: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    2f4: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    2f8: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    2fc: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    300: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    304: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    308: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    30c: 01507033  and          x0, x0, x21
    310: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    314: 00400a93  addi         x21, x0, 4  # x21 = 0x00000004
    318: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000004
    31c: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
    320: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000001
    324: 42008ab7  lui          x21, 0x42008  # x21 = 0x42008000
    328: 0c1a8a93  addi         x21, x21, 193  # x21 = 0x420080c1
    32c: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x420080c1; MOP template instruction · UNPACR Unpack_block_selection=0, AddrMode=1, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    330: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    334: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x02000000; MOP template instruction · NOP 
    338: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP 
    33c: 43800ab7  lui          x21, 0x43800  # x21 = 0x43800000
    340: 101a8a93  addi         x21, x21, 257  # x21 = 0x43800101
    344: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    348: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    34c: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP 
    350: 43800ab7  lui          x21, 0x43800  # x21 = 0x43800000
    354: 101a8a93  addi         x21, x21, 257  # x21 = 0x43800101
    358: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    35c: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    360: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    364: 824c0c13  addi         x24, x24, -2012  # x24 = 0xffb00824 · riscv_local_mem + 0x824
    368: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x824 · 0xffb00824
    36c: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_370:
    370: ffb4ec37  lui          x24, 0xffb4e  # x24 = 0xffb4e000
    374: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb4e028
    378: 000c5a83  lhu          x21, 0(x24)  # 0xffb4e028
    37c: 414a8b33  sub          x22, x21, x20
    380: 010b1b13  slli         x22, x22, 16
    384: 010b5b13  srli         x22, x22, 16
    388: 017b7663  bgeu         x22, x23, 0x00000394  # target 0x00000394
    38c: 0ff0000f  fence        0xf, 0xf
    390: fe1ff06f  jal          x0, 0x00000370  # target 0x00000370
loc_394:
    394: 0ff0000f  fence        0xf, 0xf
    398: 88100082  STALLWAIT    stall_res=8, wait_res=32  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR
    39c: 788ff001  SETADCXX     CntSetMask=1, x_end2=255, x_start=0
    3a0: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    3a4: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    3a8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    3ac: 8810000a  STALLWAIT    stall_res=8, wait_res=2  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0
    3b0: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    3b4: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    3b8: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    3bc: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    3c0: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    3c4: 01507033  and          x0, x0, x21
    3c8: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    3cc: 824a8a93  addi         x21, x21, -2012  # x21 = 0xffb00824 · riscv_local_mem + 0x824
    3d0: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x824 · 0xffb00824
    3d4: 001a0a13  addi         x20, x20, 1
    3d8: 010a1a13  slli         x20, x20, 16
    3dc: 010a5a13  srli         x20, x20, 16
    3e0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    3e4: 824a8a93  addi         x21, x21, -2012  # x21 = 0xffb00824 · riscv_local_mem + 0x824
    3e8: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x824 · 0xffb00824; write runtime value
    3ec: ffb4eab7  lui          x21, 0xffb4e  # x21 = 0xffb4e000
    3f0: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb4e020
    3f4: 014aa023  sw           x20, 0(x21)  # 0xffb4e020; write runtime value
    3f8: 0ff0000f  fence        0xf, 0xf
    3fc: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    400: 820c0c13  addi         x24, x24, -2016  # x24 = 0xffb00820 · riscv_local_mem + 0x820
    404: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x820 · 0xffb00820
    408: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    40c: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    410: 015a0a33  add          x20, x20, x21
    414: 0009db37  lui          x22, 0x0009d  # x22 = 0x0009d000
    418: 800b0b13  addi         x22, x22, -2048  # x22 = 0x0009c800
    41c: 016a6663  bltu         x20, x22, 0x00000428  # target 0x00000428
    420: 00004bb7  lui          x23, 0x00004  # x23 = 0x00004000
    424: 417a0a33  sub          x20, x20, x23
loc_428:
    428: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    42c: 820c0c13  addi         x24, x24, -2016  # x24 = 0xffb00820 · riscv_local_mem + 0x820
    430: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x820 · 0xffb00820; write runtime value
    434: 00120213  addi         x4, x4, 1
    438: e59ff06f  jal          x0, 0x00000290  # target 0x00000290
loc_43c:
    43c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    440: 82c40413  addi         x8, x8, -2004  # x8 = 0xffb0082c · riscv_local_mem + 0x82c
    444: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x82c · 0xffb0082c
    448: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
loc_44c:
    44c: ffb4a437  lui          x8, 0xffb4a  # x8 = 0xffb4a000
    450: 02840413  addi         x8, x8, 40  # x8 = 0xffb4a028
    454: 00045283  lhu          x5, 0(x8)  # 0xffb4a028
    458: 40428333  sub          x6, x5, x4
    45c: 01031313  slli         x6, x6, 16
    460: 01035313  srli         x6, x6, 16
    464: 00737663  bgeu         x6, x7, 0x00000470  # target 0x00000470
    468: 0ff0000f  fence        0xf, 0xf
    46c: fe1ff06f  jal          x0, 0x0000044c  # target 0x0000044c
loc_470:
    470: 0ff0000f  fence        0xf, 0xf
    474: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
    478: 03420213  addi         x4, x4, 52  # x4 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_47c:
    47c: 00022283  lw           x5, 0(x4)  # UNPACK_CONFIG_SYNC · 0xffe80034
    480: 0fe2f293  andi         x5, x5, 254
    484: 00028663  beq          x5, x0, 0x00000490  # target 0x00000490
    488: 0ff0000f  fence        0xf, 0xf
    48c: ff1ff06f  jal          x0, 0x0000047c  # target 0x0000047c
loc_490:
    490: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    494: d500011e  RMWCIB2      Mask=64, Data=0, CfgRegAddr=71  # cfg[71] (current thread StateID); THCON_SEC0_REG1_Unp_LF8_4b_exp = 0
    498: ffef0237  lui          x4, 0xffef0  # x4 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    49c: 10020213  addi         x4, x4, 256  # x4 = 0xffef0100 · cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor
    4a0: 01500293  addi         x5, x0, 21  # x5 = 0x00000015
    4a4: 00522023  sw           x5, 0(x4)  # cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor · 0xffef0100; write 0x00000015; cfg[64] (bank 0); THCON_SEC0_REG0_TileDescriptor = 21
    4a8: 000402b7  lui          x5, 0x00040  # x5 = 0x00040000
    4ac: 00128293  addi         x5, x5, 1  # x5 = 0x00040001
    4b0: 00522223  sw           x5, 4(x4)  # cfg[65] (bank 0) (undocumented index) · 0xffef0104; write 0x00040001; cfg[65] (bank 0) · fields not in ttsim
    4b4: 00022423  sw           x0, 8(x4)  # cfg[66] (bank 0) (undocumented index) · 0xffef0108; write 0x00000000; cfg[66] (bank 0) · fields not in ttsim
    4b8: 00022623  sw           x0, 12(x4)  # cfg[67] (bank 0) (undocumented index) · 0xffef010c; write 0x00000000; cfg[67] (bank 0) · fields not in ttsim
    4bc: 02500293  addi         x5, x0, 37  # x5 = 0x00000025
    4c0: 02522023  sw           x5, 32(x4)  # cfg[72] (bank 0) · THCON_SEC0_REG2_Out_data_format, THCON_SEC0_REG2_Throttle_mode, THCON_SEC0_REG2_Context_count, THCON_SEC0_REG2_Haloize_mode, THCON_SEC0_REG2_Tileize_mode, THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC0_REG2_Unpack_If_Sel, THCON_SEC0_REG2_Upsample_rate, THCON_SEC0_REG2_Ovrd_data_format, THCON_SEC0_REG2_Upsample_and_interleave, THCON_SEC0_REG2_Shift_amount_cntx0, THCON_SEC0_REG2_Shift_amount_cntx1, THCON_SEC0_REG2_Shift_amount_cntx2, THCON_SEC0_REG2_Shift_amount_cntx3 · 0xffef0120; write 0x00000025; cfg[72] (bank 0); THCON_SEC0_REG2_Out_data_format = 5; THCON_SEC0_REG2_Throttle_mode = 2; THCON_SEC0_REG2_Context_count = 0; THCON_SEC0_REG2_Haloize_mode = 0; THCON_SEC0_REG2_Tileize_mode = 0; THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC0_REG2_Unpack_If_Sel = 0; THCON_SEC0_REG2_Upsample_rate = 0; THCON_SEC0_REG2_Ovrd_data_format = 0; THCON_SEC0_REG2_Upsample_and_interleave = 0; THCON_SEC0_REG2_Shift_amount_cntx0 = 0; THCON_SEC0_REG2_Shift_amount_cntx1 = 0; THCON_SEC0_REG2_Shift_amount_cntx2 = 0; THCON_SEC0_REG2_Shift_amount_cntx3 = 0
    4c4: 00300293  addi         x5, x0, 3  # x5 = 0x00000003
    4c8: 02522223  sw           x5, 36(x4)  # cfg[73] (bank 0) · THCON_SEC0_REG2_Disable_zero_compress_cntx0, THCON_SEC0_REG2_Disable_zero_compress_cntx1, THCON_SEC0_REG2_Disable_zero_compress_cntx2, THCON_SEC0_REG2_Disable_zero_compress_cntx3, THCON_SEC0_REG2_Unpack_if_sel_cntx0, THCON_SEC0_REG2_Unpack_if_sel_cntx1, THCON_SEC0_REG2_Unpack_if_sel_cntx2, THCON_SEC0_REG2_Unpack_if_sel_cntx3, THCON_SEC0_REG2_Force_shared_exp, THCON_SEC0_REG2_Context_count_non_log2, THCON_SEC0_REG2_Context_count_non_log2_en, THCON_SEC0_REG2_Disable_zero_compress_cntx4, THCON_SEC0_REG2_Disable_zero_compress_cntx5, THCON_SEC0_REG2_Disable_zero_compress_cntx6, THCON_SEC0_REG2_Disable_zero_compress_cntx7, THCON_SEC0_REG2_Unpack_if_sel_cntx4, THCON_SEC0_REG2_Unpack_if_sel_cntx5, THCON_SEC0_REG2_Unpack_if_sel_cntx6, THCON_SEC0_REG2_Unpack_if_sel_cntx7, THCON_SEC0_REG2_Metadata_x_end · 0xffef0124; write 0x00000003; cfg[73] (bank 0); THCON_SEC0_REG2_Disable_zero_compress_cntx0 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx1 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx2 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx3 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx0 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx1 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx2 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx3 = 0; THCON_SEC0_REG2_Force_shared_exp = 0; THCON_SEC0_REG2_Context_count_non_log2 = 0; THCON_SEC0_REG2_Context_count_non_log2_en = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx4 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx5 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx6 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx7 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx4 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx5 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx6 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx7 = 0; THCON_SEC0_REG2_Metadata_x_end = 0
    4cc: 02022423  sw           x0, 40(x4)  # cfg[74] (bank 0) · THCON_SEC0_REG2_Unpack_limit_address · 0xffef0128; write 0x00000000; cfg[74] (bank 0); THCON_SEC0_REG2_Unpack_limit_address = 0
    4d0: 02022623  sw           x0, 44(x4)  # cfg[75] (bank 0) · THCON_SEC0_REG2_Unpack_fifo_size · 0xffef012c; write 0x00000000; cfg[75] (bank 0); THCON_SEC0_REG2_Unpack_fifo_size = 0
    4d4: fa022823  sw           x0, -80(x4)  # cfg[44] (bank 0) · UNP0_ADDR_CTRL_XY_REG_0_Xstride, UNP0_ADDR_CTRL_XY_REG_0_Ystride · 0xffef00b0; write 0x00000000; cfg[44] (bank 0); UNP0_ADDR_CTRL_XY_REG_0_Xstride = 0; UNP0_ADDR_CTRL_XY_REG_0_Ystride = 0
    4d8: fa022a23  sw           x0, -76(x4)  # cfg[45] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_0_Zstride, UNP0_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef00b4; write 0x00000000; cfg[45] (bank 0); UNP0_ADDR_CTRL_ZW_REG_0_Zstride = 0; UNP0_ADDR_CTRL_ZW_REG_0_Wstride = 0
    4dc: 002002b7  lui          x5, 0x00200  # x5 = 0x00200000
    4e0: 00228293  addi         x5, x5, 2  # x5 = 0x00200002
    4e4: fe522023  sw           x5, -32(x4)  # cfg[56] (bank 0) · UNP0_ADDR_CTRL_XY_REG_1_Xstride, UNP0_ADDR_CTRL_XY_REG_1_Ystride · 0xffef00e0; write 0x00200002; cfg[56] (bank 0); UNP0_ADDR_CTRL_XY_REG_1_Xstride = 2; UNP0_ADDR_CTRL_XY_REG_1_Ystride = 32
    4e8: 20000293  addi         x5, x0, 512  # x5 = 0x00000200
    4ec: fe522223  sw           x5, -28(x4)  # cfg[57] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_1_Zstride, UNP0_ADDR_CTRL_ZW_REG_1_Wstride · 0xffef00e4; write 0x00000200; cfg[57] (bank 0); UNP0_ADDR_CTRL_ZW_REG_1_Zstride = 512; UNP0_ADDR_CTRL_ZW_REG_1_Wstride = 0
    4f0: fc022023  sw           x0, -64(x4)  # cfg[48] (bank 0) · UNP0_ADDR_BASE_REG_0_Base · 0xffef00c0; write 0x00000000; cfg[48] (bank 0); UNP0_ADDR_BASE_REG_0_Base = 0
    4f4: fc022223  sw           x0, -60(x4)  # cfg[49] (bank 0) · UNP0_ADDR_BASE_REG_1_Base · 0xffef00c4; write 0x00000000; cfg[49] (bank 0); UNP0_ADDR_BASE_REG_1_Base = 0
    4f8: 10000293  addi         x5, x0, 256  # x5 = 0x00000100
    4fc: fc522423  sw           x5, -56(x4)  # cfg[50] (bank 0) · UNP0_FORCED_SHARED_EXP_shared_exp, UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr · 0xffef00c8; write 0x00000100; cfg[50] (bank 0); UNP0_FORCED_SHARED_EXP_shared_exp = 0; UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr = 1
    500: fc022a23  sw           x0, -44(x4)  # cfg[53] (bank 0) · UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val · 0xffef00d4; write 0x00000000; cfg[53] (bank 0); UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val = 0
    504: 004002b7  lui          x5, 0x00400  # x5 = 0x00400000
    508: 04028293  addi         x5, x5, 64  # x5 = 0x00400040
    50c: 04522823  sw           x5, 80(x4)  # cfg[84] (bank 0) · THCON_SEC0_REG5_Dest_cntx0_address, THCON_SEC0_REG5_Dest_cntx1_address · 0xffef0150; write 0x00400040; cfg[84] (bank 0); THCON_SEC0_REG5_Dest_cntx0_address = 64; THCON_SEC0_REG5_Dest_cntx1_address = 64
    510: 010002b7  lui          x5, 0x01000  # x5 = 0x01000000
    514: 10028293  addi         x5, x5, 256  # x5 = 0x01000100
    518: 04522c23  sw           x5, 88(x4)  # cfg[86] (bank 0) · THCON_SEC0_REG5_Tile_x_dim_cntx0, THCON_SEC0_REG5_Tile_x_dim_cntx1 · 0xffef0158; write 0x01000100; cfg[86] (bank 0); THCON_SEC0_REG5_Tile_x_dim_cntx0 = 256; THCON_SEC0_REG5_Tile_x_dim_cntx1 = 256
    51c: 06022823  sw           x0, 112(x4)  # cfg[92] (bank 0) · THCON_SEC0_REG7_Offset_address, THCON_SEC0_REG7_Unpack_data_format_cntx0, THCON_SEC0_REG7_Unpack_out_data_format_cntx0, THCON_SEC0_REG7_Unpack_data_format_cntx4, THCON_SEC0_REG7_Unpack_out_data_format_cntx4 · 0xffef0170; write 0x00000000; cfg[92] (bank 0); THCON_SEC0_REG7_Offset_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx4 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx4 = 0
    520: 06022a23  sw           x0, 116(x4)  # cfg[93] (bank 0) · THCON_SEC0_REG7_Offset_cntx1_address, THCON_SEC0_REG7_Unpack_data_format_cntx1, THCON_SEC0_REG7_Unpack_out_data_format_cntx1, THCON_SEC0_REG7_Unpack_data_format_cntx5, THCON_SEC0_REG7_Unpack_out_data_format_cntx5 · 0xffef0174; write 0x00000000; cfg[93] (bank 0); THCON_SEC0_REG7_Offset_cntx1_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx5 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx5 = 0
    524: d50001de  RMWCIB2      Mask=64, Data=0, CfgRegAddr=119  # cfg[119] (current thread StateID); THCON_SEC1_REG1_Unp_LF8_4b_exp = 0
    528: ffef0237  lui          x4, 0xffef0  # x4 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    52c: 1c020213  addi         x4, x4, 448  # x4 = 0xffef01c0 · cfg[112] (bank 0) · THCON_SEC1_REG0_TileDescriptor
    530: 010002b7  lui          x5, 0x01000  # x5 = 0x01000000
    534: 01528293  addi         x5, x5, 21  # x5 = 0x01000015
    538: 00522023  sw           x5, 0(x4)  # cfg[112] (bank 0) · THCON_SEC1_REG0_TileDescriptor · 0xffef01c0; write 0x01000015; cfg[112] (bank 0); THCON_SEC1_REG0_TileDescriptor = 16777237
    53c: 000402b7  lui          x5, 0x00040  # x5 = 0x00040000
    540: 00128293  addi         x5, x5, 1  # x5 = 0x00040001
    544: 00522223  sw           x5, 4(x4)  # cfg[113] (bank 0) (undocumented index) · 0xffef01c4; write 0x00040001; cfg[113] (bank 0) · fields not in ttsim
    548: 00022423  sw           x0, 8(x4)  # cfg[114] (bank 0) (undocumented index) · 0xffef01c8; write 0x00000000; cfg[114] (bank 0) · fields not in ttsim
    54c: 00022623  sw           x0, 12(x4)  # cfg[115] (bank 0) (undocumented index) · 0xffef01cc; write 0x00000000; cfg[115] (bank 0) · fields not in ttsim
    550: 02500293  addi         x5, x0, 37  # x5 = 0x00000025
    554: 02522023  sw           x5, 32(x4)  # cfg[120] (bank 0) · THCON_SEC1_REG2_Out_data_format, THCON_SEC1_REG2_Throttle_mode, THCON_SEC1_REG2_Context_count, THCON_SEC1_REG2_Haloize_mode, THCON_SEC1_REG2_Tileize_mode, THCON_SEC1_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC1_REG2_Unpack_If_Sel, THCON_SEC1_REG2_Upsample_rate, THCON_SEC1_REG2_Ovrd_data_format, THCON_SEC1_REG2_Upsample_and_interleave, THCON_SEC1_REG2_Shift_amount_cntx0, THCON_SEC1_REG2_Shift_amount_cntx1, THCON_SEC1_REG2_Shift_amount_cntx2, THCON_SEC1_REG2_Shift_amount_cntx3 · 0xffef01e0; write 0x00000025; cfg[120] (bank 0); THCON_SEC1_REG2_Out_data_format = 5; THCON_SEC1_REG2_Throttle_mode = 2; THCON_SEC1_REG2_Context_count = 0; THCON_SEC1_REG2_Haloize_mode = 0; THCON_SEC1_REG2_Tileize_mode = 0; THCON_SEC1_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC1_REG2_Unpack_If_Sel = 0; THCON_SEC1_REG2_Upsample_rate = 0; THCON_SEC1_REG2_Ovrd_data_format = 0; THCON_SEC1_REG2_Upsample_and_interleave = 0; THCON_SEC1_REG2_Shift_amount_cntx0 = 0; THCON_SEC1_REG2_Shift_amount_cntx1 = 0; THCON_SEC1_REG2_Shift_amount_cntx2 = 0; THCON_SEC1_REG2_Shift_amount_cntx3 = 0
    558: 00300293  addi         x5, x0, 3  # x5 = 0x00000003
    55c: 02522223  sw           x5, 36(x4)  # cfg[121] (bank 0) · THCON_SEC1_REG2_Disable_zero_compress_cntx0, THCON_SEC1_REG2_Disable_zero_compress_cntx1, THCON_SEC1_REG2_Disable_zero_compress_cntx2, THCON_SEC1_REG2_Disable_zero_compress_cntx3, THCON_SEC1_REG2_Unpack_if_sel_cntx0, THCON_SEC1_REG2_Unpack_if_sel_cntx1, THCON_SEC1_REG2_Unpack_if_sel_cntx2, THCON_SEC1_REG2_Unpack_if_sel_cntx3, THCON_SEC1_REG2_Force_shared_exp, THCON_SEC1_REG2_Context_count_non_log2, THCON_SEC1_REG2_Context_count_non_log2_en, THCON_SEC1_REG2_Disable_zero_compress_cntx4, THCON_SEC1_REG2_Disable_zero_compress_cntx5, THCON_SEC1_REG2_Disable_zero_compress_cntx6, THCON_SEC1_REG2_Disable_zero_compress_cntx7, THCON_SEC1_REG2_Unpack_if_sel_cntx4, THCON_SEC1_REG2_Unpack_if_sel_cntx5, THCON_SEC1_REG2_Unpack_if_sel_cntx6, THCON_SEC1_REG2_Unpack_if_sel_cntx7, THCON_SEC1_REG2_Metadata_x_end · 0xffef01e4; write 0x00000003; cfg[121] (bank 0); THCON_SEC1_REG2_Disable_zero_compress_cntx0 = 1; THCON_SEC1_REG2_Disable_zero_compress_cntx1 = 1; THCON_SEC1_REG2_Disable_zero_compress_cntx2 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx3 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx0 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx1 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx2 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx3 = 0; THCON_SEC1_REG2_Force_shared_exp = 0; THCON_SEC1_REG2_Context_count_non_log2 = 0; THCON_SEC1_REG2_Context_count_non_log2_en = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx4 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx5 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx6 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx7 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx4 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx5 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx6 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx7 = 0; THCON_SEC1_REG2_Metadata_x_end = 0
    560: 02022423  sw           x0, 40(x4)  # cfg[122] (bank 0) · THCON_SEC1_REG2_Unpack_limit_address · 0xffef01e8; write 0x00000000; cfg[122] (bank 0); THCON_SEC1_REG2_Unpack_limit_address = 0
    564: 02022623  sw           x0, 44(x4)  # cfg[123] (bank 0) · THCON_SEC1_REG2_Unpack_fifo_size · 0xffef01ec; write 0x00000000; cfg[123] (bank 0); THCON_SEC1_REG2_Unpack_fifo_size = 0
    568: ee022c23  sw           x0, -264(x4)  # cfg[46] (bank 0) · UNP1_ADDR_CTRL_XY_REG_0_Xstride, UNP1_ADDR_CTRL_XY_REG_0_Ystride · 0xffef00b8; write 0x00000000; cfg[46] (bank 0); UNP1_ADDR_CTRL_XY_REG_0_Xstride = 0; UNP1_ADDR_CTRL_XY_REG_0_Ystride = 0
    56c: ee022e23  sw           x0, -260(x4)  # cfg[47] (bank 0) · UNP1_ADDR_CTRL_ZW_REG_0_Zstride, UNP1_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef00bc; write 0x00000000; cfg[47] (bank 0); UNP1_ADDR_CTRL_ZW_REG_0_Zstride = 0; UNP1_ADDR_CTRL_ZW_REG_0_Wstride = 0
    570: 002002b7  lui          x5, 0x00200  # x5 = 0x00200000
    574: 00228293  addi         x5, x5, 2  # x5 = 0x00200002
    578: f2522423  sw           x5, -216(x4)  # cfg[58] (bank 0) · UNP1_ADDR_CTRL_XY_REG_1_Xstride, UNP1_ADDR_CTRL_XY_REG_1_Ystride · 0xffef00e8; write 0x00200002; cfg[58] (bank 0); UNP1_ADDR_CTRL_XY_REG_1_Xstride = 2; UNP1_ADDR_CTRL_XY_REG_1_Ystride = 32
    57c: 20000293  addi         x5, x0, 512  # x5 = 0x00000200
    580: f2522623  sw           x5, -212(x4)  # cfg[59] (bank 0) · UNP1_ADDR_CTRL_ZW_REG_1_Zstride, UNP1_ADDR_CTRL_ZW_REG_1_Wstride · 0xffef00ec; write 0x00000200; cfg[59] (bank 0); UNP1_ADDR_CTRL_ZW_REG_1_Zstride = 512; UNP1_ADDR_CTRL_ZW_REG_1_Wstride = 0
    584: f2022823  sw           x0, -208(x4)  # cfg[60] (bank 0) · UNP1_ADDR_BASE_REG_0_Base · 0xffef00f0; write 0x00000000; cfg[60] (bank 0); UNP1_ADDR_BASE_REG_0_Base = 0
    588: f2022a23  sw           x0, -204(x4)  # cfg[61] (bank 0) · UNP1_ADDR_BASE_REG_1_Base · 0xffef00f4; write 0x00000000; cfg[61] (bank 0); UNP1_ADDR_BASE_REG_1_Base = 0
    58c: f2022c23  sw           x0, -200(x4)  # cfg[62] (bank 0) · UNP1_FORCED_SHARED_EXP_shared_exp, UNP1_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr · 0xffef00f8; write 0x00000000; cfg[62] (bank 0); UNP1_FORCED_SHARED_EXP_shared_exp = 0; UNP1_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr = 0
    590: f2022e23  sw           x0, -196(x4)  # cfg[63] (bank 0) · UNP1_NOP_REG_CLR_VAL_nop_reg_clr_val · 0xffef00fc; write 0x00000000; cfg[63] (bank 0); UNP1_NOP_REG_CLR_VAL_nop_reg_clr_val = 0
    594: 04022823  sw           x0, 80(x4)  # cfg[132] (bank 0) · THCON_SEC1_REG5_Dest_cntx0_address, THCON_SEC1_REG5_Dest_cntx1_address · 0xffef0210; write 0x00000000; cfg[132] (bank 0); THCON_SEC1_REG5_Dest_cntx0_address = 0; THCON_SEC1_REG5_Dest_cntx1_address = 0
    598: 010002b7  lui          x5, 0x01000  # x5 = 0x01000000
    59c: 10028293  addi         x5, x5, 256  # x5 = 0x01000100
    5a0: 04522c23  sw           x5, 88(x4)  # cfg[134] (bank 0) · THCON_SEC1_REG5_Tile_x_dim_cntx0, THCON_SEC1_REG5_Tile_x_dim_cntx1 · 0xffef0218; write 0x01000100; cfg[134] (bank 0); THCON_SEC1_REG5_Tile_x_dim_cntx0 = 256; THCON_SEC1_REG5_Tile_x_dim_cntx1 = 256
    5a4: 06022823  sw           x0, 112(x4)  # cfg[140] (bank 0) · THCON_SEC1_REG7_Offset_address, THCON_SEC1_REG7_Unpack_data_format_cntx0, THCON_SEC1_REG7_Unpack_out_data_format_cntx0, THCON_SEC1_REG7_Unpack_data_format_cntx4, THCON_SEC1_REG7_Unpack_out_data_format_cntx4 · 0xffef0230; write 0x00000000; cfg[140] (bank 0); THCON_SEC1_REG7_Offset_address = 0; THCON_SEC1_REG7_Unpack_data_format_cntx0 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx0 = 0; THCON_SEC1_REG7_Unpack_data_format_cntx4 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx4 = 0
    5a8: 06022a23  sw           x0, 116(x4)  # cfg[141] (bank 0) · THCON_SEC1_REG7_Offset_cntx1_address, THCON_SEC1_REG7_Unpack_data_format_cntx1, THCON_SEC1_REG7_Unpack_out_data_format_cntx1, THCON_SEC1_REG7_Unpack_data_format_cntx5, THCON_SEC1_REG7_Unpack_out_data_format_cntx5 · 0xffef0234; write 0x00000000; cfg[141] (bank 0); THCON_SEC1_REG7_Offset_cntx1_address = 0; THCON_SEC1_REG7_Unpack_data_format_cntx1 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx1 = 0; THCON_SEC1_REG7_Unpack_data_format_cntx5 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx5 = 0
    5ac: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
    5b0: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    5b4: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    5b8: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    5bc: 00507033  and          x0, x0, x5
    5c0: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
    5c4: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
    5c8: 00522023  sw           x5, 0(x4)  # MOP_CFG · 0xffb80000; write 0x00000004
    5cc: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
    5d0: 00522223  sw           x5, 4(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000001
    5d4: 420082b7  lui          x5, 0x42008  # x5 = 0x42008000
    5d8: 0c128293  addi         x5, x5, 193  # x5 = 0x420080c1
    5dc: 00522423  sw           x5, 8(x4)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x420080c1; MOP template instruction · UNPACR Unpack_block_selection=0, AddrMode=1, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    5e0: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    5e4: 00522623  sw           x5, 12(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x02000000; MOP template instruction · NOP 
    5e8: 00522823  sw           x5, 16(x4)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP 
    5ec: 428082b7  lui          x5, 0x42808  # x5 = 0x42808000
    5f0: 0c128293  addi         x5, x5, 193  # x5 = 0x428080c1
    5f4: 00522a23  sw           x5, 20(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x428080c1; MOP template instruction · UNPACR Unpack_block_selection=1, AddrMode=1, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    5f8: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    5fc: 00522c23  sw           x5, 24(x4)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP 
    600: 428082b7  lui          x5, 0x42808  # x5 = 0x42808000
    604: 0c128293  addi         x5, x5, 193  # x5 = 0x428080c1
    608: 00522e23  sw           x5, 28(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x428080c1; MOP template instruction · UNPACR Unpack_block_selection=1, AddrMode=1, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    60c: 02522023  sw           x5, 32(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x428080c1; MOP template instruction · UNPACR Unpack_block_selection=1, AddrMode=1, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    610: 788ff001  SETADCXX     CntSetMask=1, x_end2=255, x_start=0
    614: 790ff001  SETADCXX     CntSetMask=2, x_end2=255, x_start=0
    618: 000082b7  lui          x5, 0x00008  # x5 = 0x00008000
    61c: 09828293  addi         x5, x5, 152  # x5 = 0x00008098
    620: 0002a203  lw           x4, 0(x5)  # param e2e_l0_q_rows; 0x00008098
    624: 00008337  lui          x6, 0x00008  # x6 = 0x00008000
    628: 09c30313  addi         x6, x6, 156  # x6 = 0x0000809c
    62c: 00032283  lw           x5, 0(x6)  # param e2e_l0_k_rows; 0x0000809c
    630: 00520233  add          x4, x4, x5
    634: 00008337  lui          x6, 0x00008  # x6 = 0x00008000
    638: 0a030313  addi         x6, x6, 160  # x6 = 0x000080a0
    63c: 00032283  lw           x5, 0(x6)  # param e2e_l0_v_rows; 0x000080a0
    640: 00520233  add          x4, x4, x5
    644: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    648: 00020313  addi         x6, x4, 0
loc_64c:
    64c: 1a62f263  bgeu         x5, x6, 0x000007f0  # target 0x000007f0
    650: 000953b7  lui          x7, 0x00095  # x7 = 0x00095000
    654: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    658: 80040413  addi         x8, x8, -2048  # x8 = 0x00000800
    65c: 00000493  addi         x9, x0, 0  # x9 = 0x00000000
    660: 00400513  addi         x10, x0, 4  # x10 = 0x00000004
loc_664:
    664: 18a4f263  bgeu         x9, x10, 0x000007e8  # target 0x000007e8
    668: 00038f93  addi         x31, x7, 0
    66c: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    670: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_674:
    674: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    678: 0feafa93  andi         x21, x21, 254
    67c: 000a8663  beq          x21, x0, 0x00000688  # target 0x00000688
    680: 0ff0000f  fence        0xf, 0xf
    684: ff1ff06f  jal          x0, 0x00000674  # target 0x00000674
loc_688:
    688: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    68c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    690: 830a8a93  addi         x21, x21, -2000  # x21 = 0xffb00830 · riscv_local_mem + 0x830
    694: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x830 · 0xffb00830
    698: 004a5a13  srli         x20, x20, 4
    69c: fffa0a13  addi         x20, x20, -1
    6a0: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    6a4: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    6a8: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    6ac: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    6b0: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    6b4: c8140012  SETC16       setc16_reg=5, setc16_value=4  # thread_cfg[5] (current thread); SRCA_SET_Base = 0; SRCA_SET_SetOvrdWithAddr = 1
    6b8: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    6bc: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_6c0:
    6c0: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    6c4: 0feafa93  andi         x21, x21, 254
    6c8: 000a8663  beq          x21, x0, 0x000006d4  # target 0x000006d4
    6cc: 0ff0000f  fence        0xf, 0xf
    6d0: ff1ff06f  jal          x0, 0x000006c0  # target 0x000006c0
loc_6d4:
    6d4: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    6d8: 004fda13  srli         x20, x31, 4
    6dc: fffa0a13  addi         x20, x20, -1
    6e0: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    6e4: 1f0a8a93  addi         x21, x21, 496  # x21 = 0xffef01f0 · cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address
    6e8: 014aa023  sw           x20, 0(x21)  # cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address · 0xffef01f0; write runtime value; cfg[124] (bank 0); THCON_SEC1_REG3_Base_address = runtime
    6ec: 014aa223  sw           x20, 4(x21)  # cfg[125] (bank 0) · THCON_SEC1_REG3_Base_cntx1_address · 0xffef01f4; write runtime value; cfg[125] (bank 0); THCON_SEC1_REG3_Base_cntx1_address = runtime
    6f0: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    6f4: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    6f8: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    6fc: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    700: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    704: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    708: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    70c: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    710: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    714: 834c0c13  addi         x24, x24, -1996  # x24 = 0xffb00834 · riscv_local_mem + 0x834
    718: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x834 · 0xffb00834
    71c: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_720:
    720: ffb48c37  lui          x24, 0xffb48  # x24 = 0xffb48000
    724: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb48028
    728: 000c5a83  lhu          x21, 0(x24)  # 0xffb48028
    72c: 414a8b33  sub          x22, x21, x20
    730: 010b1b13  slli         x22, x22, 16
    734: 010b5b13  srli         x22, x22, 16
    738: 017b7663  bgeu         x22, x23, 0x00000744  # target 0x00000744
    73c: 0ff0000f  fence        0xf, 0xf
    740: fe1ff06f  jal          x0, 0x00000720  # target 0x00000720
loc_744:
    744: 0ff0000f  fence        0xf, 0xf
    748: 88100182  STALLWAIT    stall_res=8, wait_res=96  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR | Wait.SRCB_CLR
    74c: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    750: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    754: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    758: 8810001a  STALLWAIT    stall_res=8, wait_res=6  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0 | Wait.UNPACK1
    75c: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    760: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    764: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    768: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    76c: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    770: 01507033  and          x0, x0, x21
    774: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    778: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    77c: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834
    780: 001a0a13  addi         x20, x20, 1
    784: 010a1a13  slli         x20, x20, 16
    788: 010a5a13  srli         x20, x20, 16
    78c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    790: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    794: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834; write runtime value
    798: ffb48ab7  lui          x21, 0xffb48  # x21 = 0xffb48000
    79c: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb48020
    7a0: 014aa023  sw           x20, 0(x21)  # 0xffb48020; write runtime value
    7a4: 0ff0000f  fence        0xf, 0xf
    7a8: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    7ac: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    7b0: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830
    7b4: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    7b8: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    7bc: 015a0a33  add          x20, x20, x21
    7c0: 00094b37  lui          x22, 0x00094  # x22 = 0x00094000
    7c4: 016a6663  bltu         x20, x22, 0x000007d0  # target 0x000007d0
    7c8: 00004bb7  lui          x23, 0x00004  # x23 = 0x00004000
    7cc: 417a0a33  sub          x20, x20, x23
loc_7d0:
    7d0: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    7d4: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    7d8: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830; write runtime value
    7dc: 008383b3  add          x7, x7, x8
    7e0: 00148493  addi         x9, x9, 1
    7e4: e81ff06f  jal          x0, 0x00000664  # target 0x00000664
loc_7e8:
    7e8: 00128293  addi         x5, x5, 1
    7ec: e61ff06f  jal          x0, 0x0000064c  # target 0x0000064c
    7f0:           j FW_TRISC0+4   # return to firmware, linked at install
