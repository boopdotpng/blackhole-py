# llama3 1b decode: down, trisc2. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x780=e2e_hidden_dense_decode_token, 0x784=e2e_l0_down, 0x788=e2e_x_a, 0x78c=e2e_x_b, 0xe980=e2e_q_compact, 0xe984=e2e_l0_down_row_start, 0xe988=dense_start, 0xe98c=e2e_l0_down_rows
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01a37  lui          x20, 0xffb01  # x20 = 0xffb01000
      4: 8c0a0a13  addi         x20, x20, -1856  # x20 = 0xffb008c0 · riscv_local_mem + 0x8c0
      8: 00017ab7  lui          x21, 0x00017  # x21 = 0x00017000
      c: 015a2023  sw           x21, 0(x20)  # riscv_local_mem + 0x8c0 · 0xffb008c0; write 0x00017000
     10: ffb01a37  lui          x20, 0xffb01  # x20 = 0xffb01000
     14: 8c4a0a13  addi         x20, x20, -1852  # x20 = 0xffb008c4 · riscv_local_mem + 0x8c4
     18: 000a2023  sw           x0, 0(x20)  # riscv_local_mem + 0x8c4 · 0xffb008c4; write 0x00000000
     1c: ffb01a37  lui          x20, 0xffb01  # x20 = 0xffb01000
     20: 8c8a0a13  addi         x20, x20, -1848  # x20 = 0xffb008c8 · riscv_local_mem + 0x8c8
     24: 0001eab7  lui          x21, 0x0001e  # x21 = 0x0001e000
     28: 015a2023  sw           x21, 0(x20)  # riscv_local_mem + 0x8c8 · 0xffb008c8; write 0x0001e000
     2c: ffb01a37  lui          x20, 0xffb01  # x20 = 0xffb01000
     30: 8cca0a13  addi         x20, x20, -1844  # x20 = 0xffb008cc · riscv_local_mem + 0x8cc
     34: 000a2023  sw           x0, 0(x20)  # riscv_local_mem + 0x8cc · 0xffb008cc; write 0x00000000
     38: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
     3c: d600011e  RMWCIB2      Mask=128, Data=0, CfgRegAddr=71  # cfg[71] (current thread StateID); THCON_SEC0_REG1_Pac_LF8_4b_exp = 0
     40: d8780006  RMWCIB3      Mask=30, Data=0, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_FORMAT_SPEC_REG2_Dstacc = 0
     44: cff0000a  RMWCIB0      Mask=252, Data=0, CfgRegAddr=2  # cfg[2] (current thread StateID); STACC_RELU_ApplyRelu = 0; STACC_RELU_ReluThreshold = 0 (masked bits only)
     48: d3fc000a  RMWCIB1      Mask=255, Data=0, CfgRegAddr=2  # cfg[2] (current thread StateID); STACC_RELU_ReluThreshold = 0 (masked bits only)
     4c: d4fc000a  RMWCIB2      Mask=63, Data=0, CfgRegAddr=2  # cfg[2] (current thread StateID); STACC_RELU_ReluThreshold = 0 (masked bits only)
     50: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
     54: 110a0a13  addi         x20, x20, 272  # x20 = 0xffef0110 · cfg[68] (bank 0) · THCON_SEC0_REG1_Row_start_section_size, THCON_SEC0_REG1_Exp_section_size
     58: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
     5c: 015a2023  sw           x21, 0(x20)  # cfg[68] (bank 0) · THCON_SEC0_REG1_Row_start_section_size, THCON_SEC0_REG1_Exp_section_size · 0xffef0110; write 0x00040000; cfg[68] (bank 0); THCON_SEC0_REG1_Row_start_section_size = 0; THCON_SEC0_REG1_Exp_section_size = 4
     60: 05100a93  addi         x21, x0, 81  # x21 = 0x00000051
     64: 015a2423  sw           x21, 8(x20)  # cfg[70] (bank 0) · THCON_SEC0_REG1_Disable_zero_compress, THCON_SEC0_REG1_Add_l1_dest_addr_offset, THCON_SEC0_REG1_Disable_pack_zero_flags, THCON_SEC0_REG1_ovrd_default_throttle_mode, THCON_SEC0_REG1_Out_data_format, THCON_SEC0_REG1_In_data_format, THCON_SEC0_REG1_Dis_shared_exp_assembler, THCON_SEC0_REG1_Auto_set_last_pacr_intf_sel, THCON_SEC0_REG1_Enable_out_fifo, THCON_SEC0_REG1_Sub_l1_tile_header_size, THCON_SEC0_REG1_Source_interface_selection, THCON_SEC0_REG1_pack_start_intf_pos, THCON_SEC0_REG1_All_pack_disable_zero_compress_ovrd, THCON_SEC0_REG1_Add_tile_header_size, THCON_SEC0_REG1_pack_dis_y_pos_start_offset, THCON_SEC0_REG1_L1_source_addr · 0xffef0118; write 0x00000051; cfg[70] (bank 0); THCON_SEC0_REG1_Disable_zero_compress = 1; THCON_SEC0_REG1_Add_l1_dest_addr_offset = 0; THCON_SEC0_REG1_Disable_pack_zero_flags = 0; THCON_SEC0_REG1_ovrd_default_throttle_mode = 0; THCON_SEC0_REG1_Out_data_format = 5; THCON_SEC0_REG1_In_data_format = 0; THCON_SEC0_REG1_Dis_shared_exp_assembler = 0; THCON_SEC0_REG1_Auto_set_last_pacr_intf_sel = 0; THCON_SEC0_REG1_Enable_out_fifo = 0; THCON_SEC0_REG1_Sub_l1_tile_header_size = 0; THCON_SEC0_REG1_Source_interface_selection = 0; THCON_SEC0_REG1_pack_start_intf_pos = 0; THCON_SEC0_REG1_All_pack_disable_zero_compress_ovrd = 0; THCON_SEC0_REG1_Add_tile_header_size = 0; THCON_SEC0_REG1_pack_dis_y_pos_start_offset = 0; THCON_SEC0_REG1_L1_source_addr = 0
     68: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
     6c: f35a2c23  sw           x21, -200(x20)  # cfg[18] (bank 0) · PCK_DEST_RD_CTRL_Read_32b_data, PCK_DEST_RD_CTRL_Read_unsigned, PCK_DEST_RD_CTRL_Read_int8, PCK_DEST_RD_CTRL_Round_10b_mant · 0xffef0048; write 0x00000001; cfg[18] (bank 0); PCK_DEST_RD_CTRL_Read_32b_data = 1; PCK_DEST_RD_CTRL_Read_unsigned = 0; PCK_DEST_RD_CTRL_Read_int8 = 0; PCK_DEST_RD_CTRL_Round_10b_mant = 0
     70: 00400ab7  lui          x21, 0x00400  # x21 = 0x00400000
     74: f35a2023  sw           x21, -224(x20)  # cfg[12] (bank 0) · PCK0_ADDR_CTRL_XY_REG_0_Xstride, PCK0_ADDR_CTRL_XY_REG_0_Ystride · 0xffef0030; write 0x00400000; cfg[12] (bank 0); PCK0_ADDR_CTRL_XY_REG_0_Xstride = 0; PCK0_ADDR_CTRL_XY_REG_0_Ystride = 64
     78: 10000ab7  lui          x21, 0x10000  # x21 = 0x10000000 · CQConfig.PCIE_MID
     7c: 400a8a93  addi         x21, x21, 1024  # x21 = 0x10000400 · arc_csm + 0x400
     80: f35a2223  sw           x21, -220(x20)  # cfg[13] (bank 0) · PCK0_ADDR_CTRL_ZW_REG_0_Zstride, PCK0_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef0034; write 0x10000400; cfg[13] (bank 0); PCK0_ADDR_CTRL_ZW_REG_0_Zstride = 1024; PCK0_ADDR_CTRL_ZW_REG_0_Wstride = 4096
     84: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
     88: f75a2023  sw           x21, -160(x20)  # cfg[28] (bank 0) · PACK_COUNTERS_SEC0_pack_per_xy_plane, PACK_COUNTERS_SEC0_pack_reads_per_xy_plane, PACK_COUNTERS_SEC0_pack_xys_per_tile, PACK_COUNTERS_SEC0_pack_yz_transposed, PACK_COUNTERS_SEC0_auto_ctxt_inc_xys_cnt · 0xffef0070; write 0x00001000; cfg[28] (bank 0); PACK_COUNTERS_SEC0_pack_per_xy_plane = 0; PACK_COUNTERS_SEC0_pack_reads_per_xy_plane = 16; PACK_COUNTERS_SEC0_pack_xys_per_tile = 0; PACK_COUNTERS_SEC0_pack_yz_transposed = 0; PACK_COUNTERS_SEC0_auto_ctxt_inc_xys_cnt = 0
     8c: 00020ab7  lui          x21, 0x00020  # x21 = 0x00020000
     90: f55a2823  sw           x21, -176(x20)  # cfg[24] (bank 0) · PCK_EDGE_OFFSET_SEC0_mask, PCK_EDGE_MODE_mode, PCK_EDGE_TILE_ROW_SET_SELECT_select · 0xffef0060; write 0x00020000; cfg[24] (bank 0); PCK_EDGE_OFFSET_SEC0_mask = 0; PCK_EDGE_MODE_mode = 0; PCK_EDGE_TILE_ROW_SET_SELECT_select = 1
     94: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
     98: f55a2a23  sw           x21, -172(x20)  # cfg[25] (bank 0) · PCK_EDGE_OFFSET_SEC1_mask · 0xffef0064; write 0x00000001; cfg[25] (bank 0); PCK_EDGE_OFFSET_SEC1_mask = 1
     9c: f40a2023  sw           x0, -192(x20)  # cfg[20] (bank 0) · TILE_ROW_SET_MAPPING_0_row_set_mapping_0, TILE_ROW_SET_MAPPING_0_row_set_mapping_1, TILE_ROW_SET_MAPPING_0_row_set_mapping_2, TILE_ROW_SET_MAPPING_0_row_set_mapping_3, TILE_ROW_SET_MAPPING_0_row_set_mapping_4, TILE_ROW_SET_MAPPING_0_row_set_mapping_5, TILE_ROW_SET_MAPPING_0_row_set_mapping_6, TILE_ROW_SET_MAPPING_0_row_set_mapping_7, TILE_ROW_SET_MAPPING_0_row_set_mapping_8, TILE_ROW_SET_MAPPING_0_row_set_mapping_9, TILE_ROW_SET_MAPPING_0_row_set_mapping_10, TILE_ROW_SET_MAPPING_0_row_set_mapping_11, TILE_ROW_SET_MAPPING_0_row_set_mapping_12, TILE_ROW_SET_MAPPING_0_row_set_mapping_13, TILE_ROW_SET_MAPPING_0_row_set_mapping_14, TILE_ROW_SET_MAPPING_0_row_set_mapping_15 · 0xffef0050; write 0x00000000; cfg[20] (bank 0); TILE_ROW_SET_MAPPING_0_row_set_mapping_0 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_1 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_2 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_3 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_4 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_5 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_6 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_7 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_8 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_9 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_10 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_11 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_12 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_13 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_14 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_15 = 0
     a0: f55a2223  sw           x21, -188(x20)  # cfg[21] (bank 0) · TILE_ROW_SET_MAPPING_1_row_set_mapping_0, TILE_ROW_SET_MAPPING_1_row_set_mapping_1, TILE_ROW_SET_MAPPING_1_row_set_mapping_2, TILE_ROW_SET_MAPPING_1_row_set_mapping_3, TILE_ROW_SET_MAPPING_1_row_set_mapping_4, TILE_ROW_SET_MAPPING_1_row_set_mapping_5, TILE_ROW_SET_MAPPING_1_row_set_mapping_6, TILE_ROW_SET_MAPPING_1_row_set_mapping_7, TILE_ROW_SET_MAPPING_1_row_set_mapping_8, TILE_ROW_SET_MAPPING_1_row_set_mapping_9, TILE_ROW_SET_MAPPING_1_row_set_mapping_10, TILE_ROW_SET_MAPPING_1_row_set_mapping_11, TILE_ROW_SET_MAPPING_1_row_set_mapping_12, TILE_ROW_SET_MAPPING_1_row_set_mapping_13, TILE_ROW_SET_MAPPING_1_row_set_mapping_14, TILE_ROW_SET_MAPPING_1_row_set_mapping_15 · 0xffef0054; write 0x00000001; cfg[21] (bank 0); TILE_ROW_SET_MAPPING_1_row_set_mapping_0 = 1; TILE_ROW_SET_MAPPING_1_row_set_mapping_1 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_2 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_3 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_4 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_5 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_6 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_7 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_8 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_9 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_10 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_11 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_12 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_13 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_14 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_15 = 0
     a4: ffe00a37  lui          x20, 0xffe00  # x20 = 0xffe00000 · TensixMMIO.REGFILE_BASE
     a8: 040a0a13  addi         x20, x20, 64  # x20 = 0xffe00040 · tensix_regfile + 0x40
     ac: 08000a93  addi         x21, x0, 128  # x21 = 0x00000080
     b0: 015a2023  sw           x21, 0(x20)  # tensix_regfile + 0x40 · 0xffe00040; write 0x00000080
     b4: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
     b8: 095a2823  sw           x21, 144(x20)  # tensix_regfile + 0xd0 · 0xffe000d0; write 0x00040000
     bc: c8940412  SETC16       setc16_reg=37, setc16_value=260  # thread_cfg[37] (current thread); ADDR_MOD_PACK_SEC0_YsrcIncr = 4; ADDR_MOD_PACK_SEC0_YsrcCR = 0; ADDR_MOD_PACK_SEC0_YsrcClear = 0; ADDR_MOD_PACK_SEC0_YdstIncr = 4; ADDR_MOD_PACK_SEC0_YdstCR = 0; ADDR_MOD_PACK_SEC0_YdstClear = 0; ADDR_MOD_PACK_SEC0_ZsrcIncr = 0; ADDR_MOD_PACK_SEC0_ZsrcClear = 0; ADDR_MOD_PACK_SEC0_ZdstIncr = 0; ADDR_MOD_PACK_SEC0_ZdstClear = 0
     c0: c898a082  SETC16       setc16_reg=38, setc16_value=10272  # thread_cfg[38] (current thread); ADDR_MOD_PACK_SEC1_YsrcIncr = 0; ADDR_MOD_PACK_SEC1_YsrcCR = 0; ADDR_MOD_PACK_SEC1_YsrcClear = 1; ADDR_MOD_PACK_SEC1_YdstIncr = 0; ADDR_MOD_PACK_SEC1_YdstCR = 0; ADDR_MOD_PACK_SEC1_YdstClear = 1; ADDR_MOD_PACK_SEC1_ZsrcIncr = 0; ADDR_MOD_PACK_SEC1_ZsrcClear = 1; ADDR_MOD_PACK_SEC1_ZdstIncr = 0; ADDR_MOD_PACK_SEC1_ZdstClear = 0
     c4: c89c4482  SETC16       setc16_reg=39, setc16_value=4384  # thread_cfg[39] (current thread); ADDR_MOD_PACK_SEC2_YsrcIncr = 0; ADDR_MOD_PACK_SEC2_YsrcCR = 0; ADDR_MOD_PACK_SEC2_YsrcClear = 1; ADDR_MOD_PACK_SEC2_YdstIncr = 4; ADDR_MOD_PACK_SEC2_YdstCR = 0; ADDR_MOD_PACK_SEC2_YdstClear = 0; ADDR_MOD_PACK_SEC2_ZsrcIncr = 1; ADDR_MOD_PACK_SEC2_ZsrcClear = 0; ADDR_MOD_PACK_SEC2_ZdstIncr = 0; ADDR_MOD_PACK_SEC2_ZdstClear = 0
     c8: 4600002d  SETADCXY     CntSetMask=4, Ch1_Y=0, Ch1_X=0, Ch0_Y=0, Ch0_X=0, BitMask=11
     cc: 5200003d  SETADCZW     CntSetMask=4, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
     d0: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
     d4: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
     d8: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
     dc: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
     e0: 01507033  and          x0, x0, x21
     e4: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
     e8: 00400a93  addi         x21, x0, 4  # x21 = 0x00000004
     ec: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000004
     f0: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000004
     f4: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
     f8: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
     fc: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x02000000; MOP template instruction · NOP
    100: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    104: 41000ab7  lui          x21, 0x41000  # x21 = 0x41000000
    108: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x41000000; MOP template instruction · PACR CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=0, AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=0
    10c: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    110: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    114: 41008ab7  lui          x21, 0x41008  # x21 = 0x41008000
    118: 001a8a93  addi         x21, x21, 1  # x21 = 0x41008001
    11c: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x41008001; MOP template instruction · PACR CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=1, AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=1
    120: 41010ab7  lui          x21, 0x41010  # x21 = 0x41010000
    124: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x41010000; MOP template instruction · PACR CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=2, AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=0
    128: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    12c: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    130: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    134: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    138: 01507033  and          x0, x0, x21
    13c: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    140: 98c28293  addi         x5, x5, -1652  # x5 = 0x0000e98c
    144: 0002a203  lw           x4, 0(x5)  # param e2e_l0_down_rows; 0x0000e98c
    148: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    14c: 00020313  addi         x6, x4, 0
loc_150:
    150: 1a62f263  bgeu         x5, x6, 0x000002f4  # target 0x000002f4
    154: 98020026  SEMWAIT      stall_res=1, sem_sel=2, wait_sem_cond=1  # stall_res: Stall.TDMA; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_ZERO
    158: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    15c: ffb01cb7  lui          x25, 0xffb01  # x25 = 0xffb01000
    160: 8c4c8c93  addi         x25, x25, -1852  # x25 = 0xffb008c4 · riscv_local_mem + 0x8c4
    164: 000caa03  lw           x20, 0(x25)  # riscv_local_mem + 0x8c4 · 0xffb008c4
loc_168:
    168: ffb49cb7  lui          x25, 0xffb49  # x25 = 0xffb49000
    16c: 020c8c93  addi         x25, x25, 32  # x25 = 0xffb49020
    170: 000cda83  lhu          x21, 0(x25)  # 0xffb49020
    174: 415a0b33  sub          x22, x20, x21
    178: 010b1b13  slli         x22, x22, 16
    17c: 010b5b13  srli         x22, x22, 16
    180: 00200b93  addi         x23, x0, 2  # x23 = 0x00000002
    184: 416b8bb3  sub          x23, x23, x22
    188: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    18c: 018bf663  bgeu         x23, x24, 0x00000198  # target 0x00000198
    190: 0ff0000f  fence        0xf, 0xf
    194: fd5ff06f  jal          x0, 0x00000168  # target 0x00000168
loc_198:
    198: 0ff0000f  fence        0xf, 0xf
    19c: ffb01bb7  lui          x23, 0xffb01  # x23 = 0xffb01000
    1a0: 8c0b8b93  addi         x23, x23, -1856  # x23 = 0xffb008c0 · riscv_local_mem + 0x8c0
    1a4: 000baa03  lw           x20, 0(x23)  # riscv_local_mem + 0x8c0 · 0xffb008c0
    1a8: 004a5a13  srli         x20, x20, 4
    1ac: fffa0a13  addi         x20, x20, -1
    1b0: 508c0bb7  lui          x23, 0x508c0  # x23 = 0x508c0000
    1b4: 01fbebb3  or           x23, x23, x31  # x23 = 0x508c0000
    1b8: ffe40c37  lui          x24, 0xffe40  # x24 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    1bc: 017c2023  sw           x23, 0(x24)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write 0x508c0000; MMIO instruction · SETADC CntSetMask=4, ChannelIndex=0, DimensionIndex=3, Value=0
    1c0: 008a1c13  slli         x24, x20, 8
    1c4: 01000cb7  lui          x25, 0x01000  # x25 = 0x01000000
    1c8: f00c8c93  addi         x25, x25, -256  # x25 = 0x00ffff00
    1cc: 019c7c33  and          x24, x24, x25
    1d0: 45000d37  lui          x26, 0x45000  # x26 = 0x45000000
    1d4: 018d0d13  addi         x26, x26, 24  # x26 = 0x45000018
    1d8: 01ac6c33  or           x24, x24, x26
    1dc: ffe40db7  lui          x27, 0xffe40  # x27 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    1e0: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    1e4: 010a5a93  srli         x21, x20, 16
    1e8: 00008b37  lui          x22, 0x00008  # x22 = 0x00008000
    1ec: 015b6b33  or           x22, x22, x21
    1f0: 008b1c13  slli         x24, x22, 8
    1f4: 01000cb7  lui          x25, 0x01000  # x25 = 0x01000000
    1f8: f00c8c93  addi         x25, x25, -256  # x25 = 0x00ffff00
    1fc: 019c7c33  and          x24, x24, x25
    200: 45000d37  lui          x26, 0x45000  # x26 = 0x45000000
    204: 019d0d13  addi         x26, x26, 25  # x26 = 0x45000019
    208: 01ac6c33  or           x24, x24, x26
    20c: ffe40db7  lui          x27, 0xffe40  # x27 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    210: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    214: 89000026  STALLWAIT    stall_res=128, wait_res=9  # stall_res: Stall.CFG; wait_res: Wait.THCON | Wait.PACK0
    218: c0300116  WRCFG        GprAddress=12, wr128b=0, CfgReg=69  # cfg[69] (current thread StateID); THCON_SEC0_REG1_L1_Dest_addr = runtime
    21c: 008a9c13  slli         x24, x21, 8
    220: 01000cb7  lui          x25, 0x01000  # x25 = 0x01000000
    224: f00c8c93  addi         x25, x25, -256  # x25 = 0x00ffff00
    228: 019c7c33  and          x24, x24, x25
    22c: 45000d37  lui          x26, 0x45000  # x26 = 0x45000000
    230: 019d0d13  addi         x26, x26, 25  # x26 = 0x45000019
    234: 01ac6c33  or           x24, x24, x26
    238: ffe40db7  lui          x27, 0xffe40  # x27 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    23c: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    240: 80000001  DMANOP
    244: 7a00f001  SETADCXX     CntSetMask=4, x_end2=15, x_start=0
    248: 52000015  SETADCZW     CntSetMask=4, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=5
    24c: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    250: 2d0a0a13  addi         x20, x20, 720  # x20 = 0xffef02d0 · cfg[180] (bank 0) · DEST_TARGET_REG_CFG_PACK_SEC0_Offset, DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset
    254: 00000a93  addi         x21, x0, 0  # x21 = 0x00000000
    258: 015a2023  sw           x21, 0(x20)  # cfg[180] (bank 0) · DEST_TARGET_REG_CFG_PACK_SEC0_Offset, DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset · 0xffef02d0; write 0x00000000; cfg[180] (bank 0); DEST_TARGET_REG_CFG_PACK_SEC0_Offset = 0; DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset = 0
    25c: 89000022  STALLWAIT    stall_res=128, wait_res=8  # stall_res: Stall.CFG; wait_res: Wait.PACK0
    260: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    264: 88040022  STALLWAIT    stall_res=2, wait_res=8  # stall_res: Stall.SYNC; wait_res: Wait.PACK0
    268: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    26c: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    270: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    274: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    278: 01507033  and          x0, x0, x21
    27c: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    280: 8c0c0c13  addi         x24, x24, -1856  # x24 = 0xffb008c0 · riscv_local_mem + 0x8c0
    284: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x8c0 · 0xffb008c0
    288: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    28c: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    290: 015a0a33  add          x20, x20, x21
    294: 00018b37  lui          x22, 0x00018  # x22 = 0x00018000
    298: 016a6663  bltu         x20, x22, 0x000002a4  # target 0x000002a4
    29c: 00001bb7  lui          x23, 0x00001  # x23 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2a0: 417a0a33  sub          x20, x20, x23
loc_2a4:
    2a4: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    2a8: 8c0c0c13  addi         x24, x24, -1856  # x24 = 0xffb008c0 · riscv_local_mem + 0x8c0
    2ac: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x8c0 · 0xffb008c0; write runtime value
    2b0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    2b4: 8c4a8a93  addi         x21, x21, -1852  # x21 = 0xffb008c4 · riscv_local_mem + 0x8c4
    2b8: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x8c4 · 0xffb008c4
    2bc: 001a0a13  addi         x20, x20, 1
    2c0: 010a1a13  slli         x20, x20, 16
    2c4: 010a5a13  srli         x20, x20, 16
    2c8: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    2cc: 8c4a8a93  addi         x21, x21, -1852  # x21 = 0xffb008c4 · riscv_local_mem + 0x8c4
    2d0: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x8c4 · 0xffb008c4; write runtime value
    2d4: ffb49ab7  lui          x21, 0xffb49  # x21 = 0xffb49000
    2d8: 028a8a93  addi         x21, x21, 40  # x21 = 0xffb49028
    2dc: 014aa023  sw           x20, 0(x21)  # 0xffb49028; write runtime value
    2e0: 0ff0000f  fence        0xf, 0xf
    2e4: 40710000  ZEROACC      clear_mode=3, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=0
    2e8: 94000022  SEMGET       sem_sel=2  # sem_sel: Sem.MATH_PACK
    2ec: 00128293  addi         x5, x5, 1
    2f0: e61ff06f  jal          x0, 0x00000150  # target 0x00000150
loc_2f4:
    2f4: 98020026  SEMWAIT      stall_res=1, sem_sel=2, wait_sem_cond=1  # stall_res: Stall.TDMA; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_ZERO
    2f8: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    2fc: ffb01cb7  lui          x25, 0xffb01  # x25 = 0xffb01000
    300: 8ccc8c93  addi         x25, x25, -1844  # x25 = 0xffb008cc · riscv_local_mem + 0x8cc
    304: 000caa03  lw           x20, 0(x25)  # riscv_local_mem + 0x8cc · 0xffb008cc
loc_308:
    308: ffb4ccb7  lui          x25, 0xffb4c  # x25 = 0xffb4c000
    30c: 020c8c93  addi         x25, x25, 32  # x25 = 0xffb4c020
    310: 000cda83  lhu          x21, 0(x25)  # 0xffb4c020
    314: 415a0b33  sub          x22, x20, x21
    318: 010b1b13  slli         x22, x22, 16
    31c: 010b5b13  srli         x22, x22, 16
    320: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
    324: 416b8bb3  sub          x23, x23, x22
    328: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    32c: 018bf663  bgeu         x23, x24, 0x00000338  # target 0x00000338
    330: 0ff0000f  fence        0xf, 0xf
    334: fd5ff06f  jal          x0, 0x00000308  # target 0x00000308
loc_338:
    338: 0ff0000f  fence        0xf, 0xf
    33c: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    340: d600011e  RMWCIB2      Mask=128, Data=0, CfgRegAddr=71  # cfg[71] (current thread StateID); THCON_SEC0_REG1_Pac_LF8_4b_exp = 0
    344: d8782806  RMWCIB3      Mask=30, Data=10, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_FORMAT_SPEC_REG2_Dstacc = 5
    348: cff0000a  RMWCIB0      Mask=252, Data=0, CfgRegAddr=2  # cfg[2] (current thread StateID); STACC_RELU_ApplyRelu = 0; STACC_RELU_ReluThreshold = 0 (masked bits only)
    34c: d3fc000a  RMWCIB1      Mask=255, Data=0, CfgRegAddr=2  # cfg[2] (current thread StateID); STACC_RELU_ReluThreshold = 0 (masked bits only)
    350: d4fc000a  RMWCIB2      Mask=63, Data=0, CfgRegAddr=2  # cfg[2] (current thread StateID); STACC_RELU_ReluThreshold = 0 (masked bits only)
    354: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    358: 110a0a13  addi         x20, x20, 272  # x20 = 0xffef0110 · cfg[68] (bank 0) · THCON_SEC0_REG1_Row_start_section_size, THCON_SEC0_REG1_Exp_section_size
    35c: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
    360: 015a2023  sw           x21, 0(x20)  # cfg[68] (bank 0) · THCON_SEC0_REG1_Row_start_section_size, THCON_SEC0_REG1_Exp_section_size · 0xffef0110; write 0x00040000; cfg[68] (bank 0); THCON_SEC0_REG1_Row_start_section_size = 0; THCON_SEC0_REG1_Exp_section_size = 4
    364: 55100a93  addi         x21, x0, 1361  # x21 = 0x00000551
    368: 015a2423  sw           x21, 8(x20)  # cfg[70] (bank 0) · THCON_SEC0_REG1_Disable_zero_compress, THCON_SEC0_REG1_Add_l1_dest_addr_offset, THCON_SEC0_REG1_Disable_pack_zero_flags, THCON_SEC0_REG1_ovrd_default_throttle_mode, THCON_SEC0_REG1_Out_data_format, THCON_SEC0_REG1_In_data_format, THCON_SEC0_REG1_Dis_shared_exp_assembler, THCON_SEC0_REG1_Auto_set_last_pacr_intf_sel, THCON_SEC0_REG1_Enable_out_fifo, THCON_SEC0_REG1_Sub_l1_tile_header_size, THCON_SEC0_REG1_Source_interface_selection, THCON_SEC0_REG1_pack_start_intf_pos, THCON_SEC0_REG1_All_pack_disable_zero_compress_ovrd, THCON_SEC0_REG1_Add_tile_header_size, THCON_SEC0_REG1_pack_dis_y_pos_start_offset, THCON_SEC0_REG1_L1_source_addr · 0xffef0118; write 0x00000551; cfg[70] (bank 0); THCON_SEC0_REG1_Disable_zero_compress = 1; THCON_SEC0_REG1_Add_l1_dest_addr_offset = 0; THCON_SEC0_REG1_Disable_pack_zero_flags = 0; THCON_SEC0_REG1_ovrd_default_throttle_mode = 0; THCON_SEC0_REG1_Out_data_format = 5; THCON_SEC0_REG1_In_data_format = 5; THCON_SEC0_REG1_Dis_shared_exp_assembler = 0; THCON_SEC0_REG1_Auto_set_last_pacr_intf_sel = 0; THCON_SEC0_REG1_Enable_out_fifo = 0; THCON_SEC0_REG1_Sub_l1_tile_header_size = 0; THCON_SEC0_REG1_Source_interface_selection = 0; THCON_SEC0_REG1_pack_start_intf_pos = 0; THCON_SEC0_REG1_All_pack_disable_zero_compress_ovrd = 0; THCON_SEC0_REG1_Add_tile_header_size = 0; THCON_SEC0_REG1_pack_dis_y_pos_start_offset = 0; THCON_SEC0_REG1_L1_source_addr = 0
    36c: f20a2c23  sw           x0, -200(x20)  # cfg[18] (bank 0) · PCK_DEST_RD_CTRL_Read_32b_data, PCK_DEST_RD_CTRL_Read_unsigned, PCK_DEST_RD_CTRL_Read_int8, PCK_DEST_RD_CTRL_Round_10b_mant · 0xffef0048; write 0x00000000; cfg[18] (bank 0); PCK_DEST_RD_CTRL_Read_32b_data = 0; PCK_DEST_RD_CTRL_Read_unsigned = 0; PCK_DEST_RD_CTRL_Read_int8 = 0; PCK_DEST_RD_CTRL_Round_10b_mant = 0
    370: 00200ab7  lui          x21, 0x00200  # x21 = 0x00200000
    374: f35a2023  sw           x21, -224(x20)  # cfg[12] (bank 0) · PCK0_ADDR_CTRL_XY_REG_0_Xstride, PCK0_ADDR_CTRL_XY_REG_0_Ystride · 0xffef0030; write 0x00200000; cfg[12] (bank 0); PCK0_ADDR_CTRL_XY_REG_0_Xstride = 0; PCK0_ADDR_CTRL_XY_REG_0_Ystride = 32
    378: 08000ab7  lui          x21, 0x08000  # x21 = 0x08000000
    37c: 200a8a93  addi         x21, x21, 512  # x21 = 0x08000200
    380: f35a2223  sw           x21, -220(x20)  # cfg[13] (bank 0) · PCK0_ADDR_CTRL_ZW_REG_0_Zstride, PCK0_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef0034; write 0x08000200; cfg[13] (bank 0); PCK0_ADDR_CTRL_ZW_REG_0_Zstride = 512; PCK0_ADDR_CTRL_ZW_REG_0_Wstride = 2048
    384: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    388: f75a2023  sw           x21, -160(x20)  # cfg[28] (bank 0) · PACK_COUNTERS_SEC0_pack_per_xy_plane, PACK_COUNTERS_SEC0_pack_reads_per_xy_plane, PACK_COUNTERS_SEC0_pack_xys_per_tile, PACK_COUNTERS_SEC0_pack_yz_transposed, PACK_COUNTERS_SEC0_auto_ctxt_inc_xys_cnt · 0xffef0070; write 0x00001000; cfg[28] (bank 0); PACK_COUNTERS_SEC0_pack_per_xy_plane = 0; PACK_COUNTERS_SEC0_pack_reads_per_xy_plane = 16; PACK_COUNTERS_SEC0_pack_xys_per_tile = 0; PACK_COUNTERS_SEC0_pack_yz_transposed = 0; PACK_COUNTERS_SEC0_auto_ctxt_inc_xys_cnt = 0
    38c: 00010ab7  lui          x21, 0x00010  # x21 = 0x00010000
    390: fffa8a93  addi         x21, x21, -1  # x21 = 0x0000ffff
    394: f55a2823  sw           x21, -176(x20)  # cfg[24] (bank 0) · PCK_EDGE_OFFSET_SEC0_mask, PCK_EDGE_MODE_mode, PCK_EDGE_TILE_ROW_SET_SELECT_select · 0xffef0060; write 0x0000ffff; cfg[24] (bank 0); PCK_EDGE_OFFSET_SEC0_mask = 65535; PCK_EDGE_MODE_mode = 0; PCK_EDGE_TILE_ROW_SET_SELECT_select = 0
    398: f40a2a23  sw           x0, -172(x20)  # cfg[25] (bank 0) · PCK_EDGE_OFFSET_SEC1_mask · 0xffef0064; write 0x00000000; cfg[25] (bank 0); PCK_EDGE_OFFSET_SEC1_mask = 0
    39c: f40a2023  sw           x0, -192(x20)  # cfg[20] (bank 0) · TILE_ROW_SET_MAPPING_0_row_set_mapping_0, TILE_ROW_SET_MAPPING_0_row_set_mapping_1, TILE_ROW_SET_MAPPING_0_row_set_mapping_2, TILE_ROW_SET_MAPPING_0_row_set_mapping_3, TILE_ROW_SET_MAPPING_0_row_set_mapping_4, TILE_ROW_SET_MAPPING_0_row_set_mapping_5, TILE_ROW_SET_MAPPING_0_row_set_mapping_6, TILE_ROW_SET_MAPPING_0_row_set_mapping_7, TILE_ROW_SET_MAPPING_0_row_set_mapping_8, TILE_ROW_SET_MAPPING_0_row_set_mapping_9, TILE_ROW_SET_MAPPING_0_row_set_mapping_10, TILE_ROW_SET_MAPPING_0_row_set_mapping_11, TILE_ROW_SET_MAPPING_0_row_set_mapping_12, TILE_ROW_SET_MAPPING_0_row_set_mapping_13, TILE_ROW_SET_MAPPING_0_row_set_mapping_14, TILE_ROW_SET_MAPPING_0_row_set_mapping_15 · 0xffef0050; write 0x00000000; cfg[20] (bank 0); TILE_ROW_SET_MAPPING_0_row_set_mapping_0 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_1 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_2 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_3 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_4 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_5 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_6 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_7 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_8 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_9 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_10 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_11 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_12 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_13 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_14 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_15 = 0
    3a0: f40a2223  sw           x0, -188(x20)  # cfg[21] (bank 0) · TILE_ROW_SET_MAPPING_1_row_set_mapping_0, TILE_ROW_SET_MAPPING_1_row_set_mapping_1, TILE_ROW_SET_MAPPING_1_row_set_mapping_2, TILE_ROW_SET_MAPPING_1_row_set_mapping_3, TILE_ROW_SET_MAPPING_1_row_set_mapping_4, TILE_ROW_SET_MAPPING_1_row_set_mapping_5, TILE_ROW_SET_MAPPING_1_row_set_mapping_6, TILE_ROW_SET_MAPPING_1_row_set_mapping_7, TILE_ROW_SET_MAPPING_1_row_set_mapping_8, TILE_ROW_SET_MAPPING_1_row_set_mapping_9, TILE_ROW_SET_MAPPING_1_row_set_mapping_10, TILE_ROW_SET_MAPPING_1_row_set_mapping_11, TILE_ROW_SET_MAPPING_1_row_set_mapping_12, TILE_ROW_SET_MAPPING_1_row_set_mapping_13, TILE_ROW_SET_MAPPING_1_row_set_mapping_14, TILE_ROW_SET_MAPPING_1_row_set_mapping_15 · 0xffef0054; write 0x00000000; cfg[21] (bank 0); TILE_ROW_SET_MAPPING_1_row_set_mapping_0 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_1 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_2 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_3 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_4 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_5 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_6 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_7 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_8 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_9 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_10 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_11 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_12 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_13 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_14 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_15 = 0
    3a4: ffe00a37  lui          x20, 0xffe00  # x20 = 0xffe00000 · TensixMMIO.REGFILE_BASE
    3a8: 040a0a13  addi         x20, x20, 64  # x20 = 0xffe00040 · tensix_regfile + 0x40
    3ac: 08000a93  addi         x21, x0, 128  # x21 = 0x00000080
    3b0: 015a2023  sw           x21, 0(x20)  # tensix_regfile + 0x40 · 0xffe00040; write 0x00000080
    3b4: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
    3b8: 095a2823  sw           x21, 144(x20)  # tensix_regfile + 0xd0 · 0xffe000d0; write 0x00040000
    3bc: c8940412  SETC16       setc16_reg=37, setc16_value=260  # thread_cfg[37] (current thread); ADDR_MOD_PACK_SEC0_YsrcIncr = 4; ADDR_MOD_PACK_SEC0_YsrcCR = 0; ADDR_MOD_PACK_SEC0_YsrcClear = 0; ADDR_MOD_PACK_SEC0_YdstIncr = 4; ADDR_MOD_PACK_SEC0_YdstCR = 0; ADDR_MOD_PACK_SEC0_YdstClear = 0; ADDR_MOD_PACK_SEC0_ZsrcIncr = 0; ADDR_MOD_PACK_SEC0_ZsrcClear = 0; ADDR_MOD_PACK_SEC0_ZdstIncr = 0; ADDR_MOD_PACK_SEC0_ZdstClear = 0
    3c0: c898a082  SETC16       setc16_reg=38, setc16_value=10272  # thread_cfg[38] (current thread); ADDR_MOD_PACK_SEC1_YsrcIncr = 0; ADDR_MOD_PACK_SEC1_YsrcCR = 0; ADDR_MOD_PACK_SEC1_YsrcClear = 1; ADDR_MOD_PACK_SEC1_YdstIncr = 0; ADDR_MOD_PACK_SEC1_YdstCR = 0; ADDR_MOD_PACK_SEC1_YdstClear = 1; ADDR_MOD_PACK_SEC1_ZsrcIncr = 0; ADDR_MOD_PACK_SEC1_ZsrcClear = 1; ADDR_MOD_PACK_SEC1_ZdstIncr = 0; ADDR_MOD_PACK_SEC1_ZdstClear = 0
    3c4: c89c4482  SETC16       setc16_reg=39, setc16_value=4384  # thread_cfg[39] (current thread); ADDR_MOD_PACK_SEC2_YsrcIncr = 0; ADDR_MOD_PACK_SEC2_YsrcCR = 0; ADDR_MOD_PACK_SEC2_YsrcClear = 1; ADDR_MOD_PACK_SEC2_YdstIncr = 4; ADDR_MOD_PACK_SEC2_YdstCR = 0; ADDR_MOD_PACK_SEC2_YdstClear = 0; ADDR_MOD_PACK_SEC2_ZsrcIncr = 1; ADDR_MOD_PACK_SEC2_ZsrcClear = 0; ADDR_MOD_PACK_SEC2_ZdstIncr = 0; ADDR_MOD_PACK_SEC2_ZdstClear = 0
    3c8: 4600002d  SETADCXY     CntSetMask=4, Ch1_Y=0, Ch1_X=0, Ch0_Y=0, Ch0_X=0, BitMask=11
    3cc: 5200003d  SETADCZW     CntSetMask=4, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    3d0: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    3d4: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    3d8: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    3dc: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    3e0: 01507033  and          x0, x0, x21
    3e4: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    3e8: 00400a93  addi         x21, x0, 4  # x21 = 0x00000004
    3ec: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000004
    3f0: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000004
    3f4: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    3f8: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
    3fc: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x02000000; MOP template instruction · NOP
    400: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    404: 41000ab7  lui          x21, 0x41000  # x21 = 0x41000000
    408: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x41000000; MOP template instruction · PACR CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=0, AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=0
    40c: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    410: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    414: 41008ab7  lui          x21, 0x41008  # x21 = 0x41008000
    418: 001a8a93  addi         x21, x21, 1  # x21 = 0x41008001
    41c: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x41008001; MOP template instruction · PACR CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=1, AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=1
    420: 41010ab7  lui          x21, 0x41010  # x21 = 0x41010000
    424: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x41010000; MOP template instruction · PACR CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=2, AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=0
    428: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    42c: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    430: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    434: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    438: 01507033  and          x0, x0, x21
    43c: ffb01bb7  lui          x23, 0xffb01  # x23 = 0xffb01000
    440: 8c8b8b93  addi         x23, x23, -1848  # x23 = 0xffb008c8 · riscv_local_mem + 0x8c8
    444: 000baa03  lw           x20, 0(x23)  # riscv_local_mem + 0x8c8 · 0xffb008c8
    448: 004a5a13  srli         x20, x20, 4
    44c: fffa0a13  addi         x20, x20, -1
    450: 508c0bb7  lui          x23, 0x508c0  # x23 = 0x508c0000
    454: 01fbebb3  or           x23, x23, x31  # x23 = 0x508c0000
    458: ffe40c37  lui          x24, 0xffe40  # x24 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    45c: 017c2023  sw           x23, 0(x24)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write 0x508c0000; MMIO instruction · SETADC CntSetMask=4, ChannelIndex=0, DimensionIndex=3, Value=0
    460: 008a1c13  slli         x24, x20, 8
    464: 01000cb7  lui          x25, 0x01000  # x25 = 0x01000000
    468: f00c8c93  addi         x25, x25, -256  # x25 = 0x00ffff00
    46c: 019c7c33  and          x24, x24, x25
    470: 45000d37  lui          x26, 0x45000  # x26 = 0x45000000
    474: 018d0d13  addi         x26, x26, 24  # x26 = 0x45000018
    478: 01ac6c33  or           x24, x24, x26
    47c: ffe40db7  lui          x27, 0xffe40  # x27 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    480: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    484: 010a5a93  srli         x21, x20, 16
    488: 00008b37  lui          x22, 0x00008  # x22 = 0x00008000
    48c: 015b6b33  or           x22, x22, x21
    490: 008b1c13  slli         x24, x22, 8
    494: 01000cb7  lui          x25, 0x01000  # x25 = 0x01000000
    498: f00c8c93  addi         x25, x25, -256  # x25 = 0x00ffff00
    49c: 019c7c33  and          x24, x24, x25
    4a0: 45000d37  lui          x26, 0x45000  # x26 = 0x45000000
    4a4: 019d0d13  addi         x26, x26, 25  # x26 = 0x45000019
    4a8: 01ac6c33  or           x24, x24, x26
    4ac: ffe40db7  lui          x27, 0xffe40  # x27 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    4b0: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    4b4: 89000026  STALLWAIT    stall_res=128, wait_res=9  # stall_res: Stall.CFG; wait_res: Wait.THCON | Wait.PACK0
    4b8: c0300116  WRCFG        GprAddress=12, wr128b=0, CfgReg=69  # cfg[69] (current thread StateID); THCON_SEC0_REG1_L1_Dest_addr = runtime
    4bc: 008a9c13  slli         x24, x21, 8
    4c0: 01000cb7  lui          x25, 0x01000  # x25 = 0x01000000
    4c4: f00c8c93  addi         x25, x25, -256  # x25 = 0x00ffff00
    4c8: 019c7c33  and          x24, x24, x25
    4cc: 45000d37  lui          x26, 0x45000  # x26 = 0x45000000
    4d0: 019d0d13  addi         x26, x26, 25  # x26 = 0x45000019
    4d4: 01ac6c33  or           x24, x24, x26
    4d8: ffe40db7  lui          x27, 0xffe40  # x27 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    4dc: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    4e0: 80000001  DMANOP
    4e4: 7a00f001  SETADCXX     CntSetMask=4, x_end2=15, x_start=0
    4e8: 52000015  SETADCZW     CntSetMask=4, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=5
    4ec: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    4f0: 2d0a0a13  addi         x20, x20, 720  # x20 = 0xffef02d0 · cfg[180] (bank 0) · DEST_TARGET_REG_CFG_PACK_SEC0_Offset, DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset
    4f4: 00000a93  addi         x21, x0, 0  # x21 = 0x00000000
    4f8: 015a2023  sw           x21, 0(x20)  # cfg[180] (bank 0) · DEST_TARGET_REG_CFG_PACK_SEC0_Offset, DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset · 0xffef02d0; write 0x00000000; cfg[180] (bank 0); DEST_TARGET_REG_CFG_PACK_SEC0_Offset = 0; DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset = 0
    4fc: 89000022  STALLWAIT    stall_res=128, wait_res=8  # stall_res: Stall.CFG; wait_res: Wait.PACK0
    500: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    504: 88040022  STALLWAIT    stall_res=2, wait_res=8  # stall_res: Stall.SYNC; wait_res: Wait.PACK0
    508: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    50c: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    510: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    514: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    518: 01507033  and          x0, x0, x21
    51c: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    520: 8c8c0c13  addi         x24, x24, -1848  # x24 = 0xffb008c8 · riscv_local_mem + 0x8c8
    524: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x8c8 · 0xffb008c8
    528: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    52c: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    530: 015a0a33  add          x20, x20, x21
    534: 0001fb37  lui          x22, 0x0001f  # x22 = 0x0001f000
    538: 800b0b13  addi         x22, x22, -2048  # x22 = 0x0001e800
    53c: 016a6863  bltu         x20, x22, 0x0000054c  # target 0x0000054c
    540: 00001bb7  lui          x23, 0x00001  # x23 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    544: 800b8b93  addi         x23, x23, -2048  # x23 = 0x00000800
    548: 417a0a33  sub          x20, x20, x23
loc_54c:
    54c: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    550: 8c8c0c13  addi         x24, x24, -1848  # x24 = 0xffb008c8 · riscv_local_mem + 0x8c8
    554: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x8c8 · 0xffb008c8; write runtime value
    558: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    55c: 8cca8a93  addi         x21, x21, -1844  # x21 = 0xffb008cc · riscv_local_mem + 0x8cc
    560: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x8cc · 0xffb008cc
    564: 001a0a13  addi         x20, x20, 1
    568: 010a1a13  slli         x20, x20, 16
    56c: 010a5a13  srli         x20, x20, 16
    570: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    574: 8cca8a93  addi         x21, x21, -1844  # x21 = 0xffb008cc · riscv_local_mem + 0x8cc
    578: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x8cc · 0xffb008cc; write runtime value
    57c: ffb4cab7  lui          x21, 0xffb4c  # x21 = 0xffb4c000
    580: 028a8a93  addi         x21, x21, 40  # x21 = 0xffb4c028
    584: 014aa023  sw           x20, 0(x21)  # 0xffb4c028; write runtime value
    588: 0ff0000f  fence        0xf, 0xf
    58c: 40610000  ZEROACC      clear_mode=3, use_32_bit_mode=0, clear_zero_flags=0, addr_mode=1, where=0
    590: 94000022  SEMGET       sem_sel=2  # sem_sel: Sem.MATH_PACK
    594:           j FW_TRISC2+4   # return to firmware, linked at install
