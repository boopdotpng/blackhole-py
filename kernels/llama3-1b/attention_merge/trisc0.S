# llama3 1b decode: attention_merge, trisc0. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (8): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9
# params: 0x780=attention_partial_tiles, 0x784=e2e_context, 0x788=kv_blocks, 0xea40=merge_head
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
      4: 820a8a93  addi         x21, x21, -2016  # x21 = 0xffb00820 · riscv_local_mem + 0x820
      8: 0000fb37  lui          x22, 0x0000f  # x22 = 0x0000f000
      c: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x820 · 0xffb00820; write 0x0000f000
     10: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     14: 824a8a93  addi         x21, x21, -2012  # x21 = 0xffb00824 · riscv_local_mem + 0x824
     18: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x824 · 0xffb00824; write 0x00000000
     1c: 78800393  addi         x7, x0, 1928  # x7 = 0x00000788
     20: 0003a283  lw           x5, 0(x7)  # param kv_blocks; 0x00000788
     24: 00100213  addi         x4, x0, 1  # x4 = 0x00000001
     28: 00400313  addi         x6, x0, 4  # x6 = 0x00000004
     2c: 00537a63  bgeu         x6, x5, 0x00000040  # target 0x00000040
     30: 00400213  addi         x4, x0, 4  # x4 = 0x00000004
     34: 08000313  addi         x6, x0, 128  # x6 = 0x00000080
     38: 00537463  bgeu         x6, x5, 0x00000040  # target 0x00000040
     3c: 00c00213  addi         x4, x0, 12  # x4 = 0x0000000c
loc_40:
     40: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
     44: 00020313  addi         x6, x4, 0
loc_48:
     48: 0062fe63  bgeu         x5, x6, 0x00000064  # target 0x00000064
     4c: 01c000ef  jal          x1, 0x00000068  # target 0x00000068; x1 = 0x00000050
     50: 018000ef  jal          x1, 0x00000068  # target 0x00000068; x1 = 0x00000054
     54: 014000ef  jal          x1, 0x00000068  # target 0x00000068; x1 = 0x00000058
     58: 010000ef  jal          x1, 0x00000068  # target 0x00000068; x1 = 0x0000005c
     5c: 00128293  addi         x5, x5, 1
     60: fe9ff06f  jal          x0, 0x00000048  # target 0x00000048
loc_64:
     64: 2300006f  jal          x0, 0x00000294  # target 0x00000294
loc_68:
     68: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
     6c: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_70:
     70: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
     74: 0feafa93  andi         x21, x21, 254
     78: 000a8663  beq          x21, x0, 0x00000084  # target 0x00000084
     7c: 0ff0000f  fence        0xf, 0xf
     80: ff1ff06f  jal          x0, 0x00000070  # target 0x00000070
loc_84:
     84: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
     88: d500011e  RMWCIB2      Mask=64, Data=0, CfgRegAddr=71  # cfg[71] (current thread StateID); THCON_SEC0_REG1_Unp_LF8_4b_exp = 0
     8c: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
     90: 100a0a13  addi         x20, x20, 256  # x20 = 0xffef0100 · cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor
     94: 01000a93  addi         x21, x0, 16  # x21 = 0x00000010
     98: 015a2023  sw           x21, 0(x20)  # cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor · 0xffef0100; write 0x00000010; cfg[64] (bank 0); THCON_SEC0_REG0_TileDescriptor = 16
     9c: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
     a0: 001a8a93  addi         x21, x21, 1  # x21 = 0x00040001
     a4: 015a2223  sw           x21, 4(x20)  # cfg[65] (bank 0) (undocumented index) · 0xffef0104; write 0x00040001; cfg[65] (bank 0) · fields not in ttsim
     a8: 000a2423  sw           x0, 8(x20)  # cfg[66] (bank 0) (undocumented index) · 0xffef0108; write 0x00000000; cfg[66] (bank 0) · fields not in ttsim
     ac: 000a2623  sw           x0, 12(x20)  # cfg[67] (bank 0) (undocumented index) · 0xffef010c; write 0x00000000; cfg[67] (bank 0) · fields not in ttsim
     b0: 02500a93  addi         x21, x0, 37  # x21 = 0x00000025
     b4: 035a2023  sw           x21, 32(x20)  # cfg[72] (bank 0) · THCON_SEC0_REG2_Out_data_format, THCON_SEC0_REG2_Throttle_mode, THCON_SEC0_REG2_Context_count, THCON_SEC0_REG2_Haloize_mode, THCON_SEC0_REG2_Tileize_mode, THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC0_REG2_Unpack_If_Sel, THCON_SEC0_REG2_Upsample_rate, THCON_SEC0_REG2_Ovrd_data_format, THCON_SEC0_REG2_Upsample_and_interleave, THCON_SEC0_REG2_Shift_amount_cntx0, THCON_SEC0_REG2_Shift_amount_cntx1, THCON_SEC0_REG2_Shift_amount_cntx2, THCON_SEC0_REG2_Shift_amount_cntx3 · 0xffef0120; write 0x00000025; cfg[72] (bank 0); THCON_SEC0_REG2_Out_data_format = 5; THCON_SEC0_REG2_Throttle_mode = 2; THCON_SEC0_REG2_Context_count = 0; THCON_SEC0_REG2_Haloize_mode = 0; THCON_SEC0_REG2_Tileize_mode = 0; THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC0_REG2_Unpack_If_Sel = 0; THCON_SEC0_REG2_Upsample_rate = 0; THCON_SEC0_REG2_Ovrd_data_format = 0; THCON_SEC0_REG2_Upsample_and_interleave = 0; THCON_SEC0_REG2_Shift_amount_cntx0 = 0; THCON_SEC0_REG2_Shift_amount_cntx1 = 0; THCON_SEC0_REG2_Shift_amount_cntx2 = 0; THCON_SEC0_REG2_Shift_amount_cntx3 = 0
     b8: 00300a93  addi         x21, x0, 3  # x21 = 0x00000003
     bc: 035a2223  sw           x21, 36(x20)  # cfg[73] (bank 0) · THCON_SEC0_REG2_Disable_zero_compress_cntx0, THCON_SEC0_REG2_Disable_zero_compress_cntx1, THCON_SEC0_REG2_Disable_zero_compress_cntx2, THCON_SEC0_REG2_Disable_zero_compress_cntx3, THCON_SEC0_REG2_Unpack_if_sel_cntx0, THCON_SEC0_REG2_Unpack_if_sel_cntx1, THCON_SEC0_REG2_Unpack_if_sel_cntx2, THCON_SEC0_REG2_Unpack_if_sel_cntx3, THCON_SEC0_REG2_Force_shared_exp, THCON_SEC0_REG2_Context_count_non_log2, THCON_SEC0_REG2_Context_count_non_log2_en, THCON_SEC0_REG2_Disable_zero_compress_cntx4, THCON_SEC0_REG2_Disable_zero_compress_cntx5, THCON_SEC0_REG2_Disable_zero_compress_cntx6, THCON_SEC0_REG2_Disable_zero_compress_cntx7, THCON_SEC0_REG2_Unpack_if_sel_cntx4, THCON_SEC0_REG2_Unpack_if_sel_cntx5, THCON_SEC0_REG2_Unpack_if_sel_cntx6, THCON_SEC0_REG2_Unpack_if_sel_cntx7, THCON_SEC0_REG2_Metadata_x_end · 0xffef0124; write 0x00000003; cfg[73] (bank 0); THCON_SEC0_REG2_Disable_zero_compress_cntx0 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx1 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx2 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx3 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx0 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx1 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx2 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx3 = 0; THCON_SEC0_REG2_Force_shared_exp = 0; THCON_SEC0_REG2_Context_count_non_log2 = 0; THCON_SEC0_REG2_Context_count_non_log2_en = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx4 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx5 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx6 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx7 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx4 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx5 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx6 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx7 = 0; THCON_SEC0_REG2_Metadata_x_end = 0
     c0: 020a2423  sw           x0, 40(x20)  # cfg[74] (bank 0) · THCON_SEC0_REG2_Unpack_limit_address · 0xffef0128; write 0x00000000; cfg[74] (bank 0); THCON_SEC0_REG2_Unpack_limit_address = 0
     c4: 020a2623  sw           x0, 44(x20)  # cfg[75] (bank 0) · THCON_SEC0_REG2_Unpack_fifo_size · 0xffef012c; write 0x00000000; cfg[75] (bank 0); THCON_SEC0_REG2_Unpack_fifo_size = 0
     c8: fa0a2823  sw           x0, -80(x20)  # cfg[44] (bank 0) · UNP0_ADDR_CTRL_XY_REG_0_Xstride, UNP0_ADDR_CTRL_XY_REG_0_Ystride · 0xffef00b0; write 0x00000000; cfg[44] (bank 0); UNP0_ADDR_CTRL_XY_REG_0_Xstride = 0; UNP0_ADDR_CTRL_XY_REG_0_Ystride = 0
     cc: fa0a2a23  sw           x0, -76(x20)  # cfg[45] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_0_Zstride, UNP0_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef00b4; write 0x00000000; cfg[45] (bank 0); UNP0_ADDR_CTRL_ZW_REG_0_Zstride = 0; UNP0_ADDR_CTRL_ZW_REG_0_Wstride = 0
     d0: 00200ab7  lui          x21, 0x00200  # x21 = 0x00200000
     d4: 002a8a93  addi         x21, x21, 2  # x21 = 0x00200002
     d8: ff5a2023  sw           x21, -32(x20)  # cfg[56] (bank 0) · UNP0_ADDR_CTRL_XY_REG_1_Xstride, UNP0_ADDR_CTRL_XY_REG_1_Ystride · 0xffef00e0; write 0x00200002; cfg[56] (bank 0); UNP0_ADDR_CTRL_XY_REG_1_Xstride = 2; UNP0_ADDR_CTRL_XY_REG_1_Ystride = 32
     dc: 20000a93  addi         x21, x0, 512  # x21 = 0x00000200
     e0: ff5a2223  sw           x21, -28(x20)  # cfg[57] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_1_Zstride, UNP0_ADDR_CTRL_ZW_REG_1_Wstride · 0xffef00e4; write 0x00000200; cfg[57] (bank 0); UNP0_ADDR_CTRL_ZW_REG_1_Zstride = 512; UNP0_ADDR_CTRL_ZW_REG_1_Wstride = 0
     e4: fc0a2023  sw           x0, -64(x20)  # cfg[48] (bank 0) · UNP0_ADDR_BASE_REG_0_Base · 0xffef00c0; write 0x00000000; cfg[48] (bank 0); UNP0_ADDR_BASE_REG_0_Base = 0
     e8: fc0a2223  sw           x0, -60(x20)  # cfg[49] (bank 0) · UNP0_ADDR_BASE_REG_1_Base · 0xffef00c4; write 0x00000000; cfg[49] (bank 0); UNP0_ADDR_BASE_REG_1_Base = 0
     ec: 10000a93  addi         x21, x0, 256  # x21 = 0x00000100
     f0: fd5a2423  sw           x21, -56(x20)  # cfg[50] (bank 0) · UNP0_FORCED_SHARED_EXP_shared_exp, UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr · 0xffef00c8; write 0x00000100; cfg[50] (bank 0); UNP0_FORCED_SHARED_EXP_shared_exp = 0; UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr = 1
     f4: fc0a2a23  sw           x0, -44(x20)  # cfg[53] (bank 0) · UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val · 0xffef00d4; write 0x00000000; cfg[53] (bank 0); UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val = 0
     f8: 00400ab7  lui          x21, 0x00400  # x21 = 0x00400000
     fc: 040a8a93  addi         x21, x21, 64  # x21 = 0x00400040
    100: 055a2823  sw           x21, 80(x20)  # cfg[84] (bank 0) · THCON_SEC0_REG5_Dest_cntx0_address, THCON_SEC0_REG5_Dest_cntx1_address · 0xffef0150; write 0x00400040; cfg[84] (bank 0); THCON_SEC0_REG5_Dest_cntx0_address = 64; THCON_SEC0_REG5_Dest_cntx1_address = 64
    104: 01000ab7  lui          x21, 0x01000  # x21 = 0x01000000
    108: 100a8a93  addi         x21, x21, 256  # x21 = 0x01000100
    10c: 055a2c23  sw           x21, 88(x20)  # cfg[86] (bank 0) · THCON_SEC0_REG5_Tile_x_dim_cntx0, THCON_SEC0_REG5_Tile_x_dim_cntx1 · 0xffef0158; write 0x01000100; cfg[86] (bank 0); THCON_SEC0_REG5_Tile_x_dim_cntx0 = 256; THCON_SEC0_REG5_Tile_x_dim_cntx1 = 256
    110: 060a2823  sw           x0, 112(x20)  # cfg[92] (bank 0) · THCON_SEC0_REG7_Offset_address, THCON_SEC0_REG7_Unpack_data_format_cntx0, THCON_SEC0_REG7_Unpack_out_data_format_cntx0, THCON_SEC0_REG7_Unpack_data_format_cntx4, THCON_SEC0_REG7_Unpack_out_data_format_cntx4 · 0xffef0170; write 0x00000000; cfg[92] (bank 0); THCON_SEC0_REG7_Offset_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx4 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx4 = 0
    114: 060a2a23  sw           x0, 116(x20)  # cfg[93] (bank 0) · THCON_SEC0_REG7_Offset_cntx1_address, THCON_SEC0_REG7_Unpack_data_format_cntx1, THCON_SEC0_REG7_Unpack_out_data_format_cntx1, THCON_SEC0_REG7_Unpack_data_format_cntx5, THCON_SEC0_REG7_Unpack_out_data_format_cntx5 · 0xffef0174; write 0x00000000; cfg[93] (bank 0); THCON_SEC0_REG7_Offset_cntx1_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx5 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx5 = 0
    118: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    11c: 820a8a93  addi         x21, x21, -2016  # x21 = 0xffb00820 · riscv_local_mem + 0x820
    120: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x820 · 0xffb00820
    124: 004a5a13  srli         x20, x20, 4
    128: fffa0a13  addi         x20, x20, -1
    12c: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    130: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    134: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    138: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    13c: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    140: c8140012  SETC16       setc16_reg=5, setc16_value=4  # thread_cfg[5] (current thread); SRCA_SET_Base = 0; SRCA_SET_SetOvrdWithAddr = 1
    144: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    148: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    14c: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    150: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    154: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    158: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    15c: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    160: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    164: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    168: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    16c: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    170: 01507033  and          x0, x0, x21
    174: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    178: 00400a93  addi         x21, x0, 4  # x21 = 0x00000004
    17c: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000004
    180: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
    184: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000001
    188: 42008ab7  lui          x21, 0x42008  # x21 = 0x42008000
    18c: 0c1a8a93  addi         x21, x21, 193  # x21 = 0x420080c1
    190: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x420080c1; MOP template instruction · UNPACR Unpack_block_selection=0, AddrMode=1, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    194: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    198: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x02000000; MOP template instruction · NOP
    19c: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    1a0: 43800ab7  lui          x21, 0x43800  # x21 = 0x43800000
    1a4: 101a8a93  addi         x21, x21, 257  # x21 = 0x43800101
    1a8: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    1ac: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    1b0: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    1b4: 43800ab7  lui          x21, 0x43800  # x21 = 0x43800000
    1b8: 101a8a93  addi         x21, x21, 257  # x21 = 0x43800101
    1bc: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    1c0: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    1c4: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    1c8: 824c0c13  addi         x24, x24, -2012  # x24 = 0xffb00824 · riscv_local_mem + 0x824
    1cc: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x824 · 0xffb00824
    1d0: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_1d4:
    1d4: ffb48c37  lui          x24, 0xffb48  # x24 = 0xffb48000
    1d8: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb48028
    1dc: 000c5a83  lhu          x21, 0(x24)  # 0xffb48028
    1e0: 414a8b33  sub          x22, x21, x20
    1e4: 010b1b13  slli         x22, x22, 16
    1e8: 010b5b13  srli         x22, x22, 16
    1ec: 017b7663  bgeu         x22, x23, 0x000001f8  # target 0x000001f8
    1f0: 0ff0000f  fence        0xf, 0xf
    1f4: fe1ff06f  jal          x0, 0x000001d4  # target 0x000001d4
loc_1f8:
    1f8: 0ff0000f  fence        0xf, 0xf
    1fc: 88100082  STALLWAIT    stall_res=8, wait_res=32  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR
    200: 788ff001  SETADCXX     CntSetMask=1, x_end2=255, x_start=0
    204: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    208: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    20c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    210: 8810000a  STALLWAIT    stall_res=8, wait_res=2  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0
    214: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    218: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    21c: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    220: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    224: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    228: 01507033  and          x0, x0, x21
    22c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    230: 824a8a93  addi         x21, x21, -2012  # x21 = 0xffb00824 · riscv_local_mem + 0x824
    234: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x824 · 0xffb00824
    238: 001a0a13  addi         x20, x20, 1
    23c: 010a1a13  slli         x20, x20, 16
    240: 010a5a13  srli         x20, x20, 16
    244: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    248: 824a8a93  addi         x21, x21, -2012  # x21 = 0xffb00824 · riscv_local_mem + 0x824
    24c: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x824 · 0xffb00824; write runtime value
    250: ffb48ab7  lui          x21, 0xffb48  # x21 = 0xffb48000
    254: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb48020
    258: 014aa023  sw           x20, 0(x21)  # 0xffb48020; write runtime value
    25c: 0ff0000f  fence        0xf, 0xf
    260: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    264: 820c0c13  addi         x24, x24, -2016  # x24 = 0xffb00820 · riscv_local_mem + 0x820
    268: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x820 · 0xffb00820
    26c: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    270: 015a0a33  add          x20, x20, x21
    274: 00017b37  lui          x22, 0x00017  # x22 = 0x00017000
    278: 016a6663  bltu         x20, x22, 0x00000284  # target 0x00000284
    27c: 00008bb7  lui          x23, 0x00008  # x23 = 0x00008000
    280: 417a0a33  sub          x20, x20, x23
loc_284:
    284: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    288: 820c0c13  addi         x24, x24, -2016  # x24 = 0xffb00820 · riscv_local_mem + 0x820
    28c: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x820 · 0xffb00820; write runtime value
    290: 00008067  jalr         x0, 0(x1)
    294:           j FW_TRISC0+4   # return to firmware, linked at install
