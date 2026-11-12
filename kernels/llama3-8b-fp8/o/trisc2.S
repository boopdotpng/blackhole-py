# llama3 8b-fp8 decode: o, trisc2. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (96): 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 14,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 14,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 14,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 14,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 14,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9 14,9 1,10 2,10 3,10 4,10 5,10 6,10 7,10 10,10 11,10 12,10 13,10 14,10 1,11 2,11 3,11 4,11 5,11 6,11 7,11 10,11 11,11 12,11 13,11 14,11
# params: 0x780=e2e_context_decode_token, 0x784=e2e_l0_q, 0x788=input_scale_0, 0x78c=input_scale_1, 0x790=output_scale_0_0, 0x794=output_scale_0_1, 0x798=e2e_x_b, 0x79c=e2e_x_a, 0xe880=e2e_q_compact, 0xe884=e2e_l0_q_row_start, 0xe888=dense_start, 0xe88c=e2e_l0_q_rows, 0xe890=dram_port
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01a37  lui          x20, 0xffb01  # x20 = 0xffb01000
      4: 8c0a0a13  addi         x20, x20, -1856  # x20 = 0xffb008c0 · riscv_local_mem + 0x8c0
      8: 00020ab7  lui          x21, 0x00020  # x21 = 0x00020000
      c: 080a8a93  addi         x21, x21, 128  # x21 = 0x00020080
     10: 015a2023  sw           x21, 0(x20)  # riscv_local_mem + 0x8c0 · 0xffb008c0; write 0x00020080
     14: ffb01a37  lui          x20, 0xffb01  # x20 = 0xffb01000
     18: 8c4a0a13  addi         x20, x20, -1852  # x20 = 0xffb008c4 · riscv_local_mem + 0x8c4
     1c: 000a2023  sw           x0, 0(x20)  # riscv_local_mem + 0x8c4 · 0xffb008c4; write 0x00000000
     20: ffb01a37  lui          x20, 0xffb01  # x20 = 0xffb01000
     24: 8c8a0a13  addi         x20, x20, -1848  # x20 = 0xffb008c8 · riscv_local_mem + 0x8c8
     28: 0001fab7  lui          x21, 0x0001f  # x21 = 0x0001f000
     2c: 080a8a93  addi         x21, x21, 128  # x21 = 0x0001f080
     30: 015a2023  sw           x21, 0(x20)  # riscv_local_mem + 0x8c8 · 0xffb008c8; write 0x0001f080
     34: ffb01a37  lui          x20, 0xffb01  # x20 = 0xffb01000
     38: 8cca0a13  addi         x20, x20, -1844  # x20 = 0xffb008cc · riscv_local_mem + 0x8cc
     3c: 000a2023  sw           x0, 0(x20)  # riscv_local_mem + 0x8cc · 0xffb008cc; write 0x00000000
     40: ffb01a37  lui          x20, 0xffb01  # x20 = 0xffb01000
     44: 8d0a0a13  addi         x20, x20, -1840  # x20 = 0xffb008d0 · riscv_local_mem + 0x8d0
     48: 00026ab7  lui          x21, 0x00026  # x21 = 0x00026000
     4c: 080a8a93  addi         x21, x21, 128  # x21 = 0x00026080
     50: 015a2023  sw           x21, 0(x20)  # riscv_local_mem + 0x8d0 · 0xffb008d0; write 0x00026080
     54: ffb01a37  lui          x20, 0xffb01  # x20 = 0xffb01000
     58: 8d4a0a13  addi         x20, x20, -1836  # x20 = 0xffb008d4 · riscv_local_mem + 0x8d4
     5c: 000a2023  sw           x0, 0(x20)  # riscv_local_mem + 0x8d4 · 0xffb008d4; write 0x00000000
     60: 00000213  addi         x4, x0, 0  # x4 = 0x00000000
     64: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
loc_68:
     68: 2a527263  bgeu         x4, x5, 0x0000030c  # target 0x0000030c
     6c: 98020026  SEMWAIT      stall_res=1, sem_sel=2, wait_sem_cond=1  # stall_res: Stall.TDMA; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_ZERO
     70: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     74: ffb01cb7  lui          x25, 0xffb01  # x25 = 0xffb01000
     78: 8c4c8c93  addi         x25, x25, -1852  # x25 = 0xffb008c4 · riscv_local_mem + 0x8c4
     7c: 000caa03  lw           x20, 0(x25)  # riscv_local_mem + 0x8c4 · 0xffb008c4
loc_80:
     80: ffb4acb7  lui          x25, 0xffb4a  # x25 = 0xffb4a000
     84: 020c8c93  addi         x25, x25, 32  # x25 = 0xffb4a020
     88: 000cda83  lhu          x21, 0(x25)  # 0xffb4a020
     8c: 415a0b33  sub          x22, x20, x21
     90: 010b1b13  slli         x22, x22, 16
     94: 010b5b13  srli         x22, x22, 16
     98: 00400b93  addi         x23, x0, 4  # x23 = 0x00000004
     9c: 416b8bb3  sub          x23, x23, x22
     a0: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
     a4: 018bf663  bgeu         x23, x24, 0x000000b0  # target 0x000000b0
     a8: 0ff0000f  fence        0xf, 0xf
     ac: fd5ff06f  jal          x0, 0x00000080  # target 0x00000080
loc_b0:
     b0: 0ff0000f  fence        0xf, 0xf
     b4: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
     b8: d602011e  RMWCIB2      Mask=128, Data=128, CfgRegAddr=71  # cfg[71] (current thread StateID); THCON_SEC0_REG1_Pac_LF8_4b_exp = 1
     bc: d8780806  RMWCIB3      Mask=30, Data=2, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_FORMAT_SPEC_REG2_Dstacc = 1
     c0: cff0000a  RMWCIB0      Mask=252, Data=0, CfgRegAddr=2  # cfg[2] (current thread StateID); STACC_RELU_ApplyRelu = 0; STACC_RELU_ReluThreshold = 0 (masked bits only)
     c4: d3fc000a  RMWCIB1      Mask=255, Data=0, CfgRegAddr=2  # cfg[2] (current thread StateID); STACC_RELU_ReluThreshold = 0 (masked bits only)
     c8: d4fc000a  RMWCIB2      Mask=63, Data=0, CfgRegAddr=2  # cfg[2] (current thread StateID); STACC_RELU_ReluThreshold = 0 (masked bits only)
     cc: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
     d0: 110a0a13  addi         x20, x20, 272  # x20 = 0xffef0110 · cfg[68] (bank 0) · THCON_SEC0_REG1_Row_start_section_size, THCON_SEC0_REG1_Exp_section_size
     d4: 000a2023  sw           x0, 0(x20)  # cfg[68] (bank 0) · THCON_SEC0_REG1_Row_start_section_size, THCON_SEC0_REG1_Exp_section_size · 0xffef0110; write 0x00000000; cfg[68] (bank 0); THCON_SEC0_REG1_Row_start_section_size = 0; THCON_SEC0_REG1_Exp_section_size = 0
     d8: 1a100a93  addi         x21, x0, 417  # x21 = 0x000001a1
     dc: 015a2423  sw           x21, 8(x20)  # cfg[70] (bank 0) · THCON_SEC0_REG1_Disable_zero_compress, THCON_SEC0_REG1_Add_l1_dest_addr_offset, THCON_SEC0_REG1_Disable_pack_zero_flags, THCON_SEC0_REG1_ovrd_default_throttle_mode, THCON_SEC0_REG1_Out_data_format, THCON_SEC0_REG1_In_data_format, THCON_SEC0_REG1_Dis_shared_exp_assembler, THCON_SEC0_REG1_Auto_set_last_pacr_intf_sel, THCON_SEC0_REG1_Enable_out_fifo, THCON_SEC0_REG1_Sub_l1_tile_header_size, THCON_SEC0_REG1_Source_interface_selection, THCON_SEC0_REG1_pack_start_intf_pos, THCON_SEC0_REG1_All_pack_disable_zero_compress_ovrd, THCON_SEC0_REG1_Add_tile_header_size, THCON_SEC0_REG1_pack_dis_y_pos_start_offset, THCON_SEC0_REG1_L1_source_addr · 0xffef0118; write 0x000001a1; cfg[70] (bank 0); THCON_SEC0_REG1_Disable_zero_compress = 1; THCON_SEC0_REG1_Add_l1_dest_addr_offset = 0; THCON_SEC0_REG1_Disable_pack_zero_flags = 0; THCON_SEC0_REG1_ovrd_default_throttle_mode = 0; THCON_SEC0_REG1_Out_data_format = 10; THCON_SEC0_REG1_In_data_format = 1; THCON_SEC0_REG1_Dis_shared_exp_assembler = 0; THCON_SEC0_REG1_Auto_set_last_pacr_intf_sel = 0; THCON_SEC0_REG1_Enable_out_fifo = 0; THCON_SEC0_REG1_Sub_l1_tile_header_size = 0; THCON_SEC0_REG1_Source_interface_selection = 0; THCON_SEC0_REG1_pack_start_intf_pos = 0; THCON_SEC0_REG1_All_pack_disable_zero_compress_ovrd = 0; THCON_SEC0_REG1_Add_tile_header_size = 0; THCON_SEC0_REG1_pack_dis_y_pos_start_offset = 0; THCON_SEC0_REG1_L1_source_addr = 0
     e0: 00900a93  addi         x21, x0, 9  # x21 = 0x00000009
     e4: f35a2c23  sw           x21, -200(x20)  # cfg[18] (bank 0) · PCK_DEST_RD_CTRL_Read_32b_data, PCK_DEST_RD_CTRL_Read_unsigned, PCK_DEST_RD_CTRL_Read_int8, PCK_DEST_RD_CTRL_Round_10b_mant · 0xffef0048; write 0x00000009; cfg[18] (bank 0); PCK_DEST_RD_CTRL_Read_32b_data = 1; PCK_DEST_RD_CTRL_Read_unsigned = 0; PCK_DEST_RD_CTRL_Read_int8 = 0; PCK_DEST_RD_CTRL_Round_10b_mant = 1
     e8: 00200ab7  lui          x21, 0x00200  # x21 = 0x00200000
     ec: f35a2023  sw           x21, -224(x20)  # cfg[12] (bank 0) · PCK0_ADDR_CTRL_XY_REG_0_Xstride, PCK0_ADDR_CTRL_XY_REG_0_Ystride · 0xffef0030; write 0x00200000; cfg[12] (bank 0); PCK0_ADDR_CTRL_XY_REG_0_Xstride = 0; PCK0_ADDR_CTRL_XY_REG_0_Ystride = 32
     f0: 08000ab7  lui          x21, 0x08000  # x21 = 0x08000000
     f4: 200a8a93  addi         x21, x21, 512  # x21 = 0x08000200
     f8: f35a2223  sw           x21, -220(x20)  # cfg[13] (bank 0) · PCK0_ADDR_CTRL_ZW_REG_0_Zstride, PCK0_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef0034; write 0x08000200; cfg[13] (bank 0); PCK0_ADDR_CTRL_ZW_REG_0_Zstride = 512; PCK0_ADDR_CTRL_ZW_REG_0_Wstride = 2048
     fc: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    100: f75a2023  sw           x21, -160(x20)  # cfg[28] (bank 0) · PACK_COUNTERS_SEC0_pack_per_xy_plane, PACK_COUNTERS_SEC0_pack_reads_per_xy_plane, PACK_COUNTERS_SEC0_pack_xys_per_tile, PACK_COUNTERS_SEC0_pack_yz_transposed, PACK_COUNTERS_SEC0_auto_ctxt_inc_xys_cnt · 0xffef0070; write 0x00001000; cfg[28] (bank 0); PACK_COUNTERS_SEC0_pack_per_xy_plane = 0; PACK_COUNTERS_SEC0_pack_reads_per_xy_plane = 16; PACK_COUNTERS_SEC0_pack_xys_per_tile = 0; PACK_COUNTERS_SEC0_pack_yz_transposed = 0; PACK_COUNTERS_SEC0_auto_ctxt_inc_xys_cnt = 0
    104: 00010ab7  lui          x21, 0x00010  # x21 = 0x00010000
    108: fffa8a93  addi         x21, x21, -1  # x21 = 0x0000ffff
    10c: f55a2823  sw           x21, -176(x20)  # cfg[24] (bank 0) · PCK_EDGE_OFFSET_SEC0_mask, PCK_EDGE_MODE_mode, PCK_EDGE_TILE_ROW_SET_SELECT_select · 0xffef0060; write 0x0000ffff; cfg[24] (bank 0); PCK_EDGE_OFFSET_SEC0_mask = 65535; PCK_EDGE_MODE_mode = 0; PCK_EDGE_TILE_ROW_SET_SELECT_select = 0
    110: f40a2a23  sw           x0, -172(x20)  # cfg[25] (bank 0) · PCK_EDGE_OFFSET_SEC1_mask · 0xffef0064; write 0x00000000; cfg[25] (bank 0); PCK_EDGE_OFFSET_SEC1_mask = 0
    114: f40a2023  sw           x0, -192(x20)  # cfg[20] (bank 0) · TILE_ROW_SET_MAPPING_0_row_set_mapping_0, TILE_ROW_SET_MAPPING_0_row_set_mapping_1, TILE_ROW_SET_MAPPING_0_row_set_mapping_2, TILE_ROW_SET_MAPPING_0_row_set_mapping_3, TILE_ROW_SET_MAPPING_0_row_set_mapping_4, TILE_ROW_SET_MAPPING_0_row_set_mapping_5, TILE_ROW_SET_MAPPING_0_row_set_mapping_6, TILE_ROW_SET_MAPPING_0_row_set_mapping_7, TILE_ROW_SET_MAPPING_0_row_set_mapping_8, TILE_ROW_SET_MAPPING_0_row_set_mapping_9, TILE_ROW_SET_MAPPING_0_row_set_mapping_10, TILE_ROW_SET_MAPPING_0_row_set_mapping_11, TILE_ROW_SET_MAPPING_0_row_set_mapping_12, TILE_ROW_SET_MAPPING_0_row_set_mapping_13, TILE_ROW_SET_MAPPING_0_row_set_mapping_14, TILE_ROW_SET_MAPPING_0_row_set_mapping_15 · 0xffef0050; write 0x00000000; cfg[20] (bank 0); TILE_ROW_SET_MAPPING_0_row_set_mapping_0 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_1 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_2 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_3 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_4 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_5 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_6 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_7 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_8 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_9 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_10 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_11 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_12 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_13 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_14 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_15 = 0
    118: f40a2223  sw           x0, -188(x20)  # cfg[21] (bank 0) · TILE_ROW_SET_MAPPING_1_row_set_mapping_0, TILE_ROW_SET_MAPPING_1_row_set_mapping_1, TILE_ROW_SET_MAPPING_1_row_set_mapping_2, TILE_ROW_SET_MAPPING_1_row_set_mapping_3, TILE_ROW_SET_MAPPING_1_row_set_mapping_4, TILE_ROW_SET_MAPPING_1_row_set_mapping_5, TILE_ROW_SET_MAPPING_1_row_set_mapping_6, TILE_ROW_SET_MAPPING_1_row_set_mapping_7, TILE_ROW_SET_MAPPING_1_row_set_mapping_8, TILE_ROW_SET_MAPPING_1_row_set_mapping_9, TILE_ROW_SET_MAPPING_1_row_set_mapping_10, TILE_ROW_SET_MAPPING_1_row_set_mapping_11, TILE_ROW_SET_MAPPING_1_row_set_mapping_12, TILE_ROW_SET_MAPPING_1_row_set_mapping_13, TILE_ROW_SET_MAPPING_1_row_set_mapping_14, TILE_ROW_SET_MAPPING_1_row_set_mapping_15 · 0xffef0054; write 0x00000000; cfg[21] (bank 0); TILE_ROW_SET_MAPPING_1_row_set_mapping_0 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_1 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_2 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_3 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_4 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_5 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_6 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_7 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_8 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_9 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_10 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_11 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_12 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_13 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_14 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_15 = 0
    11c: ffe00a37  lui          x20, 0xffe00  # x20 = 0xffe00000 · TensixMMIO.REGFILE_BASE
    120: 040a0a13  addi         x20, x20, 64  # x20 = 0xffe00040 · tensix_regfile + 0x40
    124: 04000a93  addi         x21, x0, 64  # x21 = 0x00000040
    128: 015a2023  sw           x21, 0(x20)  # tensix_regfile + 0x40 · 0xffe00040; write 0x00000040
    12c: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
    130: 095a2823  sw           x21, 144(x20)  # tensix_regfile + 0xd0 · 0xffe000d0; write 0x00040000
    134: c8940412  SETC16       setc16_reg=37, setc16_value=260  # thread_cfg[37] (current thread); ADDR_MOD_PACK_SEC0_YsrcIncr = 4; ADDR_MOD_PACK_SEC0_YsrcCR = 0; ADDR_MOD_PACK_SEC0_YsrcClear = 0; ADDR_MOD_PACK_SEC0_YdstIncr = 4; ADDR_MOD_PACK_SEC0_YdstCR = 0; ADDR_MOD_PACK_SEC0_YdstClear = 0; ADDR_MOD_PACK_SEC0_ZsrcIncr = 0; ADDR_MOD_PACK_SEC0_ZsrcClear = 0; ADDR_MOD_PACK_SEC0_ZdstIncr = 0; ADDR_MOD_PACK_SEC0_ZdstClear = 0
    138: c898a082  SETC16       setc16_reg=38, setc16_value=10272  # thread_cfg[38] (current thread); ADDR_MOD_PACK_SEC1_YsrcIncr = 0; ADDR_MOD_PACK_SEC1_YsrcCR = 0; ADDR_MOD_PACK_SEC1_YsrcClear = 1; ADDR_MOD_PACK_SEC1_YdstIncr = 0; ADDR_MOD_PACK_SEC1_YdstCR = 0; ADDR_MOD_PACK_SEC1_YdstClear = 1; ADDR_MOD_PACK_SEC1_ZsrcIncr = 0; ADDR_MOD_PACK_SEC1_ZsrcClear = 1; ADDR_MOD_PACK_SEC1_ZdstIncr = 0; ADDR_MOD_PACK_SEC1_ZdstClear = 0
    13c: c89c4482  SETC16       setc16_reg=39, setc16_value=4384  # thread_cfg[39] (current thread); ADDR_MOD_PACK_SEC2_YsrcIncr = 0; ADDR_MOD_PACK_SEC2_YsrcCR = 0; ADDR_MOD_PACK_SEC2_YsrcClear = 1; ADDR_MOD_PACK_SEC2_YdstIncr = 4; ADDR_MOD_PACK_SEC2_YdstCR = 0; ADDR_MOD_PACK_SEC2_YdstClear = 0; ADDR_MOD_PACK_SEC2_ZsrcIncr = 1; ADDR_MOD_PACK_SEC2_ZsrcClear = 0; ADDR_MOD_PACK_SEC2_ZdstIncr = 0; ADDR_MOD_PACK_SEC2_ZdstClear = 0
    140: 4600002d  SETADCXY     CntSetMask=4, Ch1_Y=0, Ch1_X=0, Ch0_Y=0, Ch0_X=0, BitMask=11
    144: 5200003d  SETADCZW     CntSetMask=4, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    148: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    14c: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    150: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    154: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    158: 01507033  and          x0, x0, x21
    15c: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    160: 00400a93  addi         x21, x0, 4  # x21 = 0x00000004
    164: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000004
    168: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000004
    16c: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    170: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
    174: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x02000000; MOP template instruction · NOP
    178: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    17c: 41000ab7  lui          x21, 0x41000  # x21 = 0x41000000
    180: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x41000000; MOP template instruction · PACR CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=0, AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=0
    184: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    188: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    18c: 41008ab7  lui          x21, 0x41008  # x21 = 0x41008000
    190: 001a8a93  addi         x21, x21, 1  # x21 = 0x41008001
    194: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x41008001; MOP template instruction · PACR CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=1, AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=1
    198: 41010ab7  lui          x21, 0x41010  # x21 = 0x41010000
    19c: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x41010000; MOP template instruction · PACR CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=2, AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=0
    1a0: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    1a4: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    1a8: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    1ac: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    1b0: 01507033  and          x0, x0, x21
    1b4: ffb01bb7  lui          x23, 0xffb01  # x23 = 0xffb01000
    1b8: 8c0b8b93  addi         x23, x23, -1856  # x23 = 0xffb008c0 · riscv_local_mem + 0x8c0
    1bc: 000baa03  lw           x20, 0(x23)  # riscv_local_mem + 0x8c0 · 0xffb008c0
    1c0: 004a5a13  srli         x20, x20, 4
    1c4: fffa0a13  addi         x20, x20, -1
    1c8: 508c0bb7  lui          x23, 0x508c0  # x23 = 0x508c0000
    1cc: 01fbebb3  or           x23, x23, x31  # x23 = 0x508c0000
    1d0: ffe40c37  lui          x24, 0xffe40  # x24 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    1d4: 017c2023  sw           x23, 0(x24)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write 0x508c0000; MMIO instruction · SETADC CntSetMask=4, ChannelIndex=0, DimensionIndex=3, Value=0
    1d8: 008a1c13  slli         x24, x20, 8
    1dc: 01000cb7  lui          x25, 0x01000  # x25 = 0x01000000
    1e0: f00c8c93  addi         x25, x25, -256  # x25 = 0x00ffff00
    1e4: 019c7c33  and          x24, x24, x25
    1e8: 45000d37  lui          x26, 0x45000  # x26 = 0x45000000
    1ec: 018d0d13  addi         x26, x26, 24  # x26 = 0x45000018
    1f0: 01ac6c33  or           x24, x24, x26
    1f4: ffe40db7  lui          x27, 0xffe40  # x27 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    1f8: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    1fc: 010a5a93  srli         x21, x20, 16
    200: 00008b37  lui          x22, 0x00008  # x22 = 0x00008000
    204: 015b6b33  or           x22, x22, x21
    208: 008b1c13  slli         x24, x22, 8
    20c: 01000cb7  lui          x25, 0x01000  # x25 = 0x01000000
    210: f00c8c93  addi         x25, x25, -256  # x25 = 0x00ffff00
    214: 019c7c33  and          x24, x24, x25
    218: 45000d37  lui          x26, 0x45000  # x26 = 0x45000000
    21c: 019d0d13  addi         x26, x26, 25  # x26 = 0x45000019
    220: 01ac6c33  or           x24, x24, x26
    224: ffe40db7  lui          x27, 0xffe40  # x27 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    228: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    22c: 89000026  STALLWAIT    stall_res=128, wait_res=9  # stall_res: Stall.CFG; wait_res: Wait.THCON | Wait.PACK0
    230: c0300116  WRCFG        GprAddress=12, wr128b=0, CfgReg=69  # cfg[69] (current thread StateID); THCON_SEC0_REG1_L1_Dest_addr = runtime
    234: 008a9c13  slli         x24, x21, 8
    238: 01000cb7  lui          x25, 0x01000  # x25 = 0x01000000
    23c: f00c8c93  addi         x25, x25, -256  # x25 = 0x00ffff00
    240: 019c7c33  and          x24, x24, x25
    244: 45000d37  lui          x26, 0x45000  # x26 = 0x45000000
    248: 019d0d13  addi         x26, x26, 25  # x26 = 0x45000019
    24c: 01ac6c33  or           x24, x24, x26
    250: ffe40db7  lui          x27, 0xffe40  # x27 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    254: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    258: 80000001  DMANOP
    25c: 7a00f001  SETADCXX     CntSetMask=4, x_end2=15, x_start=0
    260: 52000015  SETADCZW     CntSetMask=4, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=5
    264: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    268: 2d0a0a13  addi         x20, x20, 720  # x20 = 0xffef02d0 · cfg[180] (bank 0) · DEST_TARGET_REG_CFG_PACK_SEC0_Offset, DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset
    26c: 00000a93  addi         x21, x0, 0  # x21 = 0x00000000
    270: 015a2023  sw           x21, 0(x20)  # cfg[180] (bank 0) · DEST_TARGET_REG_CFG_PACK_SEC0_Offset, DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset · 0xffef02d0; write 0x00000000; cfg[180] (bank 0); DEST_TARGET_REG_CFG_PACK_SEC0_Offset = 0; DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset = 0
    274: 89000022  STALLWAIT    stall_res=128, wait_res=8  # stall_res: Stall.CFG; wait_res: Wait.PACK0
    278: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    27c: 88040022  STALLWAIT    stall_res=2, wait_res=8  # stall_res: Stall.SYNC; wait_res: Wait.PACK0
    280: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    284: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    288: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    28c: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    290: 01507033  and          x0, x0, x21
    294: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    298: 8c0c0c13  addi         x24, x24, -1856  # x24 = 0xffb008c0 · riscv_local_mem + 0x8c0
    29c: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x8c0 · 0xffb008c0
    2a0: 40000a93  addi         x21, x0, 1024  # x21 = 0x00000400
    2a4: 015a0a33  add          x20, x20, x21
    2a8: 00021b37  lui          x22, 0x00021  # x22 = 0x00021000
    2ac: 080b0b13  addi         x22, x22, 128  # x22 = 0x00021080
    2b0: 016a6663  bltu         x20, x22, 0x000002bc  # target 0x000002bc
    2b4: 00001bb7  lui          x23, 0x00001  # x23 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2b8: 417a0a33  sub          x20, x20, x23
loc_2bc:
    2bc: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    2c0: 8c0c0c13  addi         x24, x24, -1856  # x24 = 0xffb008c0 · riscv_local_mem + 0x8c0
    2c4: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x8c0 · 0xffb008c0; write runtime value
    2c8: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    2cc: 8c4a8a93  addi         x21, x21, -1852  # x21 = 0xffb008c4 · riscv_local_mem + 0x8c4
    2d0: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x8c4 · 0xffb008c4
    2d4: 001a0a13  addi         x20, x20, 1
    2d8: 010a1a13  slli         x20, x20, 16
    2dc: 010a5a13  srli         x20, x20, 16
    2e0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    2e4: 8c4a8a93  addi         x21, x21, -1852  # x21 = 0xffb008c4 · riscv_local_mem + 0x8c4
    2e8: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x8c4 · 0xffb008c4; write runtime value
    2ec: ffb4aab7  lui          x21, 0xffb4a  # x21 = 0xffb4a000
    2f0: 028a8a93  addi         x21, x21, 40  # x21 = 0xffb4a028
    2f4: 014aa023  sw           x20, 0(x21)  # 0xffb4a028; write runtime value
    2f8: 0ff0000f  fence        0xf, 0xf
    2fc: 40710000  ZEROACC      clear_mode=3, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=0
    300: 94000022  SEMGET       sem_sel=2  # sem_sel: Sem.MATH_PACK
    304: 00120213  addi         x4, x4, 1
    308: d61ff06f  jal          x0, 0x00000068  # target 0x00000068
loc_30c:
    30c: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    310: d600011e  RMWCIB2      Mask=128, Data=0, CfgRegAddr=71  # cfg[71] (current thread StateID); THCON_SEC0_REG1_Pac_LF8_4b_exp = 0
    314: d8780006  RMWCIB3      Mask=30, Data=0, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_FORMAT_SPEC_REG2_Dstacc = 0
    318: cff0000a  RMWCIB0      Mask=252, Data=0, CfgRegAddr=2  # cfg[2] (current thread StateID); STACC_RELU_ApplyRelu = 0; STACC_RELU_ReluThreshold = 0 (masked bits only)
    31c: d3fc000a  RMWCIB1      Mask=255, Data=0, CfgRegAddr=2  # cfg[2] (current thread StateID); STACC_RELU_ReluThreshold = 0 (masked bits only)
    320: d4fc000a  RMWCIB2      Mask=63, Data=0, CfgRegAddr=2  # cfg[2] (current thread StateID); STACC_RELU_ReluThreshold = 0 (masked bits only)
    324: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    328: 110a0a13  addi         x20, x20, 272  # x20 = 0xffef0110 · cfg[68] (bank 0) · THCON_SEC0_REG1_Row_start_section_size, THCON_SEC0_REG1_Exp_section_size
    32c: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
    330: 015a2023  sw           x21, 0(x20)  # cfg[68] (bank 0) · THCON_SEC0_REG1_Row_start_section_size, THCON_SEC0_REG1_Exp_section_size · 0xffef0110; write 0x00040000; cfg[68] (bank 0); THCON_SEC0_REG1_Row_start_section_size = 0; THCON_SEC0_REG1_Exp_section_size = 4
    334: 05100a93  addi         x21, x0, 81  # x21 = 0x00000051
    338: 015a2423  sw           x21, 8(x20)  # cfg[70] (bank 0) · THCON_SEC0_REG1_Disable_zero_compress, THCON_SEC0_REG1_Add_l1_dest_addr_offset, THCON_SEC0_REG1_Disable_pack_zero_flags, THCON_SEC0_REG1_ovrd_default_throttle_mode, THCON_SEC0_REG1_Out_data_format, THCON_SEC0_REG1_In_data_format, THCON_SEC0_REG1_Dis_shared_exp_assembler, THCON_SEC0_REG1_Auto_set_last_pacr_intf_sel, THCON_SEC0_REG1_Enable_out_fifo, THCON_SEC0_REG1_Sub_l1_tile_header_size, THCON_SEC0_REG1_Source_interface_selection, THCON_SEC0_REG1_pack_start_intf_pos, THCON_SEC0_REG1_All_pack_disable_zero_compress_ovrd, THCON_SEC0_REG1_Add_tile_header_size, THCON_SEC0_REG1_pack_dis_y_pos_start_offset, THCON_SEC0_REG1_L1_source_addr · 0xffef0118; write 0x00000051; cfg[70] (bank 0); THCON_SEC0_REG1_Disable_zero_compress = 1; THCON_SEC0_REG1_Add_l1_dest_addr_offset = 0; THCON_SEC0_REG1_Disable_pack_zero_flags = 0; THCON_SEC0_REG1_ovrd_default_throttle_mode = 0; THCON_SEC0_REG1_Out_data_format = 5; THCON_SEC0_REG1_In_data_format = 0; THCON_SEC0_REG1_Dis_shared_exp_assembler = 0; THCON_SEC0_REG1_Auto_set_last_pacr_intf_sel = 0; THCON_SEC0_REG1_Enable_out_fifo = 0; THCON_SEC0_REG1_Sub_l1_tile_header_size = 0; THCON_SEC0_REG1_Source_interface_selection = 0; THCON_SEC0_REG1_pack_start_intf_pos = 0; THCON_SEC0_REG1_All_pack_disable_zero_compress_ovrd = 0; THCON_SEC0_REG1_Add_tile_header_size = 0; THCON_SEC0_REG1_pack_dis_y_pos_start_offset = 0; THCON_SEC0_REG1_L1_source_addr = 0
    33c: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
    340: f35a2c23  sw           x21, -200(x20)  # cfg[18] (bank 0) · PCK_DEST_RD_CTRL_Read_32b_data, PCK_DEST_RD_CTRL_Read_unsigned, PCK_DEST_RD_CTRL_Read_int8, PCK_DEST_RD_CTRL_Round_10b_mant · 0xffef0048; write 0x00000001; cfg[18] (bank 0); PCK_DEST_RD_CTRL_Read_32b_data = 1; PCK_DEST_RD_CTRL_Read_unsigned = 0; PCK_DEST_RD_CTRL_Read_int8 = 0; PCK_DEST_RD_CTRL_Round_10b_mant = 0
    344: 00400ab7  lui          x21, 0x00400  # x21 = 0x00400000
    348: f35a2023  sw           x21, -224(x20)  # cfg[12] (bank 0) · PCK0_ADDR_CTRL_XY_REG_0_Xstride, PCK0_ADDR_CTRL_XY_REG_0_Ystride · 0xffef0030; write 0x00400000; cfg[12] (bank 0); PCK0_ADDR_CTRL_XY_REG_0_Xstride = 0; PCK0_ADDR_CTRL_XY_REG_0_Ystride = 64
    34c: 10000ab7  lui          x21, 0x10000  # x21 = 0x10000000 · CQConfig.PCIE_MID
    350: 400a8a93  addi         x21, x21, 1024  # x21 = 0x10000400 · arc_csm + 0x400
    354: f35a2223  sw           x21, -220(x20)  # cfg[13] (bank 0) · PCK0_ADDR_CTRL_ZW_REG_0_Zstride, PCK0_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef0034; write 0x10000400; cfg[13] (bank 0); PCK0_ADDR_CTRL_ZW_REG_0_Zstride = 1024; PCK0_ADDR_CTRL_ZW_REG_0_Wstride = 4096
    358: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    35c: f75a2023  sw           x21, -160(x20)  # cfg[28] (bank 0) · PACK_COUNTERS_SEC0_pack_per_xy_plane, PACK_COUNTERS_SEC0_pack_reads_per_xy_plane, PACK_COUNTERS_SEC0_pack_xys_per_tile, PACK_COUNTERS_SEC0_pack_yz_transposed, PACK_COUNTERS_SEC0_auto_ctxt_inc_xys_cnt · 0xffef0070; write 0x00001000; cfg[28] (bank 0); PACK_COUNTERS_SEC0_pack_per_xy_plane = 0; PACK_COUNTERS_SEC0_pack_reads_per_xy_plane = 16; PACK_COUNTERS_SEC0_pack_xys_per_tile = 0; PACK_COUNTERS_SEC0_pack_yz_transposed = 0; PACK_COUNTERS_SEC0_auto_ctxt_inc_xys_cnt = 0
    360: 00020ab7  lui          x21, 0x00020  # x21 = 0x00020000
    364: f55a2823  sw           x21, -176(x20)  # cfg[24] (bank 0) · PCK_EDGE_OFFSET_SEC0_mask, PCK_EDGE_MODE_mode, PCK_EDGE_TILE_ROW_SET_SELECT_select · 0xffef0060; write 0x00020000; cfg[24] (bank 0); PCK_EDGE_OFFSET_SEC0_mask = 0; PCK_EDGE_MODE_mode = 0; PCK_EDGE_TILE_ROW_SET_SELECT_select = 1
    368: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
    36c: f55a2a23  sw           x21, -172(x20)  # cfg[25] (bank 0) · PCK_EDGE_OFFSET_SEC1_mask · 0xffef0064; write 0x00000001; cfg[25] (bank 0); PCK_EDGE_OFFSET_SEC1_mask = 1
    370: f40a2023  sw           x0, -192(x20)  # cfg[20] (bank 0) · TILE_ROW_SET_MAPPING_0_row_set_mapping_0, TILE_ROW_SET_MAPPING_0_row_set_mapping_1, TILE_ROW_SET_MAPPING_0_row_set_mapping_2, TILE_ROW_SET_MAPPING_0_row_set_mapping_3, TILE_ROW_SET_MAPPING_0_row_set_mapping_4, TILE_ROW_SET_MAPPING_0_row_set_mapping_5, TILE_ROW_SET_MAPPING_0_row_set_mapping_6, TILE_ROW_SET_MAPPING_0_row_set_mapping_7, TILE_ROW_SET_MAPPING_0_row_set_mapping_8, TILE_ROW_SET_MAPPING_0_row_set_mapping_9, TILE_ROW_SET_MAPPING_0_row_set_mapping_10, TILE_ROW_SET_MAPPING_0_row_set_mapping_11, TILE_ROW_SET_MAPPING_0_row_set_mapping_12, TILE_ROW_SET_MAPPING_0_row_set_mapping_13, TILE_ROW_SET_MAPPING_0_row_set_mapping_14, TILE_ROW_SET_MAPPING_0_row_set_mapping_15 · 0xffef0050; write 0x00000000; cfg[20] (bank 0); TILE_ROW_SET_MAPPING_0_row_set_mapping_0 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_1 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_2 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_3 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_4 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_5 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_6 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_7 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_8 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_9 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_10 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_11 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_12 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_13 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_14 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_15 = 0
    374: f55a2223  sw           x21, -188(x20)  # cfg[21] (bank 0) · TILE_ROW_SET_MAPPING_1_row_set_mapping_0, TILE_ROW_SET_MAPPING_1_row_set_mapping_1, TILE_ROW_SET_MAPPING_1_row_set_mapping_2, TILE_ROW_SET_MAPPING_1_row_set_mapping_3, TILE_ROW_SET_MAPPING_1_row_set_mapping_4, TILE_ROW_SET_MAPPING_1_row_set_mapping_5, TILE_ROW_SET_MAPPING_1_row_set_mapping_6, TILE_ROW_SET_MAPPING_1_row_set_mapping_7, TILE_ROW_SET_MAPPING_1_row_set_mapping_8, TILE_ROW_SET_MAPPING_1_row_set_mapping_9, TILE_ROW_SET_MAPPING_1_row_set_mapping_10, TILE_ROW_SET_MAPPING_1_row_set_mapping_11, TILE_ROW_SET_MAPPING_1_row_set_mapping_12, TILE_ROW_SET_MAPPING_1_row_set_mapping_13, TILE_ROW_SET_MAPPING_1_row_set_mapping_14, TILE_ROW_SET_MAPPING_1_row_set_mapping_15 · 0xffef0054; write 0x00000001; cfg[21] (bank 0); TILE_ROW_SET_MAPPING_1_row_set_mapping_0 = 1; TILE_ROW_SET_MAPPING_1_row_set_mapping_1 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_2 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_3 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_4 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_5 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_6 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_7 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_8 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_9 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_10 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_11 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_12 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_13 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_14 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_15 = 0
    378: ffe00a37  lui          x20, 0xffe00  # x20 = 0xffe00000 · TensixMMIO.REGFILE_BASE
    37c: 040a0a13  addi         x20, x20, 64  # x20 = 0xffe00040 · tensix_regfile + 0x40
    380: 08000a93  addi         x21, x0, 128  # x21 = 0x00000080
    384: 015a2023  sw           x21, 0(x20)  # tensix_regfile + 0x40 · 0xffe00040; write 0x00000080
    388: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
    38c: 095a2823  sw           x21, 144(x20)  # tensix_regfile + 0xd0 · 0xffe000d0; write 0x00040000
    390: c8940412  SETC16       setc16_reg=37, setc16_value=260  # thread_cfg[37] (current thread); ADDR_MOD_PACK_SEC0_YsrcIncr = 4; ADDR_MOD_PACK_SEC0_YsrcCR = 0; ADDR_MOD_PACK_SEC0_YsrcClear = 0; ADDR_MOD_PACK_SEC0_YdstIncr = 4; ADDR_MOD_PACK_SEC0_YdstCR = 0; ADDR_MOD_PACK_SEC0_YdstClear = 0; ADDR_MOD_PACK_SEC0_ZsrcIncr = 0; ADDR_MOD_PACK_SEC0_ZsrcClear = 0; ADDR_MOD_PACK_SEC0_ZdstIncr = 0; ADDR_MOD_PACK_SEC0_ZdstClear = 0
    394: c898a082  SETC16       setc16_reg=38, setc16_value=10272  # thread_cfg[38] (current thread); ADDR_MOD_PACK_SEC1_YsrcIncr = 0; ADDR_MOD_PACK_SEC1_YsrcCR = 0; ADDR_MOD_PACK_SEC1_YsrcClear = 1; ADDR_MOD_PACK_SEC1_YdstIncr = 0; ADDR_MOD_PACK_SEC1_YdstCR = 0; ADDR_MOD_PACK_SEC1_YdstClear = 1; ADDR_MOD_PACK_SEC1_ZsrcIncr = 0; ADDR_MOD_PACK_SEC1_ZsrcClear = 1; ADDR_MOD_PACK_SEC1_ZdstIncr = 0; ADDR_MOD_PACK_SEC1_ZdstClear = 0
    398: c89c4482  SETC16       setc16_reg=39, setc16_value=4384  # thread_cfg[39] (current thread); ADDR_MOD_PACK_SEC2_YsrcIncr = 0; ADDR_MOD_PACK_SEC2_YsrcCR = 0; ADDR_MOD_PACK_SEC2_YsrcClear = 1; ADDR_MOD_PACK_SEC2_YdstIncr = 4; ADDR_MOD_PACK_SEC2_YdstCR = 0; ADDR_MOD_PACK_SEC2_YdstClear = 0; ADDR_MOD_PACK_SEC2_ZsrcIncr = 1; ADDR_MOD_PACK_SEC2_ZsrcClear = 0; ADDR_MOD_PACK_SEC2_ZdstIncr = 0; ADDR_MOD_PACK_SEC2_ZdstClear = 0
    39c: 4600002d  SETADCXY     CntSetMask=4, Ch1_Y=0, Ch1_X=0, Ch0_Y=0, Ch0_X=0, BitMask=11
    3a0: 5200003d  SETADCZW     CntSetMask=4, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    3a4: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    3a8: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    3ac: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    3b0: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    3b4: 01507033  and          x0, x0, x21
    3b8: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    3bc: 00400a93  addi         x21, x0, 4  # x21 = 0x00000004
    3c0: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000004
    3c4: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000004
    3c8: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    3cc: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
    3d0: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x02000000; MOP template instruction · NOP
    3d4: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    3d8: 41000ab7  lui          x21, 0x41000  # x21 = 0x41000000
    3dc: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x41000000; MOP template instruction · PACR CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=0, AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=0
    3e0: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    3e4: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    3e8: 41008ab7  lui          x21, 0x41008  # x21 = 0x41008000
    3ec: 001a8a93  addi         x21, x21, 1  # x21 = 0x41008001
    3f0: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x41008001; MOP template instruction · PACR CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=1, AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=1
    3f4: 41010ab7  lui          x21, 0x41010  # x21 = 0x41010000
    3f8: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x41010000; MOP template instruction · PACR CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=2, AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=0
    3fc: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    400: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    404: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    408: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    40c: 01507033  and          x0, x0, x21
    410: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    414: 88c28293  addi         x5, x5, -1908  # x5 = 0x0000e88c
    418: 0002a203  lw           x4, 0(x5)  # param e2e_l0_q_rows; 0x0000e88c
    41c: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    420: 00020313  addi         x6, x4, 0
loc_424:
    424: 1a62f463  bgeu         x5, x6, 0x000005cc  # target 0x000005cc
    428: 98020026  SEMWAIT      stall_res=1, sem_sel=2, wait_sem_cond=1  # stall_res: Stall.TDMA; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_ZERO
    42c: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    430: ffb01cb7  lui          x25, 0xffb01  # x25 = 0xffb01000
    434: 8ccc8c93  addi         x25, x25, -1844  # x25 = 0xffb008cc · riscv_local_mem + 0x8cc
    438: 000caa03  lw           x20, 0(x25)  # riscv_local_mem + 0x8cc · 0xffb008cc
loc_43c:
    43c: ffb49cb7  lui          x25, 0xffb49  # x25 = 0xffb49000
    440: 020c8c93  addi         x25, x25, 32  # x25 = 0xffb49020
    444: 000cda83  lhu          x21, 0(x25)  # 0xffb49020
    448: 415a0b33  sub          x22, x20, x21
    44c: 010b1b13  slli         x22, x22, 16
    450: 010b5b13  srli         x22, x22, 16
    454: 00200b93  addi         x23, x0, 2  # x23 = 0x00000002
    458: 416b8bb3  sub          x23, x23, x22
    45c: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    460: 018bf663  bgeu         x23, x24, 0x0000046c  # target 0x0000046c
    464: 0ff0000f  fence        0xf, 0xf
    468: fd5ff06f  jal          x0, 0x0000043c  # target 0x0000043c
loc_46c:
    46c: 0ff0000f  fence        0xf, 0xf
    470: ffb01bb7  lui          x23, 0xffb01  # x23 = 0xffb01000
    474: 8c8b8b93  addi         x23, x23, -1848  # x23 = 0xffb008c8 · riscv_local_mem + 0x8c8
    478: 000baa03  lw           x20, 0(x23)  # riscv_local_mem + 0x8c8 · 0xffb008c8
    47c: 004a5a13  srli         x20, x20, 4
    480: fffa0a13  addi         x20, x20, -1
    484: 508c0bb7  lui          x23, 0x508c0  # x23 = 0x508c0000
    488: 01fbebb3  or           x23, x23, x31  # x23 = 0x508c0000
    48c: ffe40c37  lui          x24, 0xffe40  # x24 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    490: 017c2023  sw           x23, 0(x24)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write 0x508c0000; MMIO instruction · SETADC CntSetMask=4, ChannelIndex=0, DimensionIndex=3, Value=0
    494: 008a1c13  slli         x24, x20, 8
    498: 01000cb7  lui          x25, 0x01000  # x25 = 0x01000000
    49c: f00c8c93  addi         x25, x25, -256  # x25 = 0x00ffff00
    4a0: 019c7c33  and          x24, x24, x25
    4a4: 45000d37  lui          x26, 0x45000  # x26 = 0x45000000
    4a8: 018d0d13  addi         x26, x26, 24  # x26 = 0x45000018
    4ac: 01ac6c33  or           x24, x24, x26
    4b0: ffe40db7  lui          x27, 0xffe40  # x27 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    4b4: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    4b8: 010a5a93  srli         x21, x20, 16
    4bc: 00008b37  lui          x22, 0x00008  # x22 = 0x00008000
    4c0: 015b6b33  or           x22, x22, x21
    4c4: 008b1c13  slli         x24, x22, 8
    4c8: 01000cb7  lui          x25, 0x01000  # x25 = 0x01000000
    4cc: f00c8c93  addi         x25, x25, -256  # x25 = 0x00ffff00
    4d0: 019c7c33  and          x24, x24, x25
    4d4: 45000d37  lui          x26, 0x45000  # x26 = 0x45000000
    4d8: 019d0d13  addi         x26, x26, 25  # x26 = 0x45000019
    4dc: 01ac6c33  or           x24, x24, x26
    4e0: ffe40db7  lui          x27, 0xffe40  # x27 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    4e4: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    4e8: 89000026  STALLWAIT    stall_res=128, wait_res=9  # stall_res: Stall.CFG; wait_res: Wait.THCON | Wait.PACK0
    4ec: c0300116  WRCFG        GprAddress=12, wr128b=0, CfgReg=69  # cfg[69] (current thread StateID); THCON_SEC0_REG1_L1_Dest_addr = runtime
    4f0: 008a9c13  slli         x24, x21, 8
    4f4: 01000cb7  lui          x25, 0x01000  # x25 = 0x01000000
    4f8: f00c8c93  addi         x25, x25, -256  # x25 = 0x00ffff00
    4fc: 019c7c33  and          x24, x24, x25
    500: 45000d37  lui          x26, 0x45000  # x26 = 0x45000000
    504: 019d0d13  addi         x26, x26, 25  # x26 = 0x45000019
    508: 01ac6c33  or           x24, x24, x26
    50c: ffe40db7  lui          x27, 0xffe40  # x27 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    510: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    514: 80000001  DMANOP
    518: 7a00f001  SETADCXX     CntSetMask=4, x_end2=15, x_start=0
    51c: 52000015  SETADCZW     CntSetMask=4, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=5
    520: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    524: 2d0a0a13  addi         x20, x20, 720  # x20 = 0xffef02d0 · cfg[180] (bank 0) · DEST_TARGET_REG_CFG_PACK_SEC0_Offset, DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset
    528: 00000a93  addi         x21, x0, 0  # x21 = 0x00000000
    52c: 015a2023  sw           x21, 0(x20)  # cfg[180] (bank 0) · DEST_TARGET_REG_CFG_PACK_SEC0_Offset, DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset · 0xffef02d0; write 0x00000000; cfg[180] (bank 0); DEST_TARGET_REG_CFG_PACK_SEC0_Offset = 0; DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset = 0
    530: 89000022  STALLWAIT    stall_res=128, wait_res=8  # stall_res: Stall.CFG; wait_res: Wait.PACK0
    534: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    538: 88040022  STALLWAIT    stall_res=2, wait_res=8  # stall_res: Stall.SYNC; wait_res: Wait.PACK0
    53c: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    540: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    544: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    548: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    54c: 01507033  and          x0, x0, x21
    550: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    554: 8c8c0c13  addi         x24, x24, -1848  # x24 = 0xffb008c8 · riscv_local_mem + 0x8c8
    558: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x8c8 · 0xffb008c8
    55c: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    560: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    564: 015a0a33  add          x20, x20, x21
    568: 00020b37  lui          x22, 0x00020  # x22 = 0x00020000
    56c: 080b0b13  addi         x22, x22, 128  # x22 = 0x00020080
    570: 016a6663  bltu         x20, x22, 0x0000057c  # target 0x0000057c
    574: 00001bb7  lui          x23, 0x00001  # x23 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    578: 417a0a33  sub          x20, x20, x23
loc_57c:
    57c: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    580: 8c8c0c13  addi         x24, x24, -1848  # x24 = 0xffb008c8 · riscv_local_mem + 0x8c8
    584: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x8c8 · 0xffb008c8; write runtime value
    588: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    58c: 8cca8a93  addi         x21, x21, -1844  # x21 = 0xffb008cc · riscv_local_mem + 0x8cc
    590: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x8cc · 0xffb008cc
    594: 001a0a13  addi         x20, x20, 1
    598: 010a1a13  slli         x20, x20, 16
    59c: 010a5a13  srli         x20, x20, 16
    5a0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    5a4: 8cca8a93  addi         x21, x21, -1844  # x21 = 0xffb008cc · riscv_local_mem + 0x8cc
    5a8: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x8cc · 0xffb008cc; write runtime value
    5ac: ffb49ab7  lui          x21, 0xffb49  # x21 = 0xffb49000
    5b0: 028a8a93  addi         x21, x21, 40  # x21 = 0xffb49028
    5b4: 014aa023  sw           x20, 0(x21)  # 0xffb49028; write runtime value
    5b8: 0ff0000f  fence        0xf, 0xf
    5bc: 40710000  ZEROACC      clear_mode=3, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=0
    5c0: 94000022  SEMGET       sem_sel=2  # sem_sel: Sem.MATH_PACK
    5c4: 00128293  addi         x5, x5, 1
    5c8: e5dff06f  jal          x0, 0x00000424  # target 0x00000424
loc_5cc:
    5cc: 98020026  SEMWAIT      stall_res=1, sem_sel=2, wait_sem_cond=1  # stall_res: Stall.TDMA; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_ZERO
    5d0: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    5d4: ffb01cb7  lui          x25, 0xffb01  # x25 = 0xffb01000
    5d8: 8d4c8c93  addi         x25, x25, -1836  # x25 = 0xffb008d4 · riscv_local_mem + 0x8d4
    5dc: 000caa03  lw           x20, 0(x25)  # riscv_local_mem + 0x8d4 · 0xffb008d4
loc_5e0:
    5e0: ffb4ecb7  lui          x25, 0xffb4e  # x25 = 0xffb4e000
    5e4: 020c8c93  addi         x25, x25, 32  # x25 = 0xffb4e020
    5e8: 000cda83  lhu          x21, 0(x25)  # 0xffb4e020
    5ec: 415a0b33  sub          x22, x20, x21
    5f0: 010b1b13  slli         x22, x22, 16
    5f4: 010b5b13  srli         x22, x22, 16
    5f8: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
    5fc: 416b8bb3  sub          x23, x23, x22
    600: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    604: 018bf663  bgeu         x23, x24, 0x00000610  # target 0x00000610
    608: 0ff0000f  fence        0xf, 0xf
    60c: fd5ff06f  jal          x0, 0x000005e0  # target 0x000005e0
loc_610:
    610: 0ff0000f  fence        0xf, 0xf
    614: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    618: d600011e  RMWCIB2      Mask=128, Data=0, CfgRegAddr=71  # cfg[71] (current thread StateID); THCON_SEC0_REG1_Pac_LF8_4b_exp = 0
    61c: d8782806  RMWCIB3      Mask=30, Data=10, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_FORMAT_SPEC_REG2_Dstacc = 5
    620: cff0000a  RMWCIB0      Mask=252, Data=0, CfgRegAddr=2  # cfg[2] (current thread StateID); STACC_RELU_ApplyRelu = 0; STACC_RELU_ReluThreshold = 0 (masked bits only)
    624: d3fc000a  RMWCIB1      Mask=255, Data=0, CfgRegAddr=2  # cfg[2] (current thread StateID); STACC_RELU_ReluThreshold = 0 (masked bits only)
    628: d4fc000a  RMWCIB2      Mask=63, Data=0, CfgRegAddr=2  # cfg[2] (current thread StateID); STACC_RELU_ReluThreshold = 0 (masked bits only)
    62c: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    630: 110a0a13  addi         x20, x20, 272  # x20 = 0xffef0110 · cfg[68] (bank 0) · THCON_SEC0_REG1_Row_start_section_size, THCON_SEC0_REG1_Exp_section_size
    634: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
    638: 015a2023  sw           x21, 0(x20)  # cfg[68] (bank 0) · THCON_SEC0_REG1_Row_start_section_size, THCON_SEC0_REG1_Exp_section_size · 0xffef0110; write 0x00040000; cfg[68] (bank 0); THCON_SEC0_REG1_Row_start_section_size = 0; THCON_SEC0_REG1_Exp_section_size = 4
    63c: 55100a93  addi         x21, x0, 1361  # x21 = 0x00000551
    640: 015a2423  sw           x21, 8(x20)  # cfg[70] (bank 0) · THCON_SEC0_REG1_Disable_zero_compress, THCON_SEC0_REG1_Add_l1_dest_addr_offset, THCON_SEC0_REG1_Disable_pack_zero_flags, THCON_SEC0_REG1_ovrd_default_throttle_mode, THCON_SEC0_REG1_Out_data_format, THCON_SEC0_REG1_In_data_format, THCON_SEC0_REG1_Dis_shared_exp_assembler, THCON_SEC0_REG1_Auto_set_last_pacr_intf_sel, THCON_SEC0_REG1_Enable_out_fifo, THCON_SEC0_REG1_Sub_l1_tile_header_size, THCON_SEC0_REG1_Source_interface_selection, THCON_SEC0_REG1_pack_start_intf_pos, THCON_SEC0_REG1_All_pack_disable_zero_compress_ovrd, THCON_SEC0_REG1_Add_tile_header_size, THCON_SEC0_REG1_pack_dis_y_pos_start_offset, THCON_SEC0_REG1_L1_source_addr · 0xffef0118; write 0x00000551; cfg[70] (bank 0); THCON_SEC0_REG1_Disable_zero_compress = 1; THCON_SEC0_REG1_Add_l1_dest_addr_offset = 0; THCON_SEC0_REG1_Disable_pack_zero_flags = 0; THCON_SEC0_REG1_ovrd_default_throttle_mode = 0; THCON_SEC0_REG1_Out_data_format = 5; THCON_SEC0_REG1_In_data_format = 5; THCON_SEC0_REG1_Dis_shared_exp_assembler = 0; THCON_SEC0_REG1_Auto_set_last_pacr_intf_sel = 0; THCON_SEC0_REG1_Enable_out_fifo = 0; THCON_SEC0_REG1_Sub_l1_tile_header_size = 0; THCON_SEC0_REG1_Source_interface_selection = 0; THCON_SEC0_REG1_pack_start_intf_pos = 0; THCON_SEC0_REG1_All_pack_disable_zero_compress_ovrd = 0; THCON_SEC0_REG1_Add_tile_header_size = 0; THCON_SEC0_REG1_pack_dis_y_pos_start_offset = 0; THCON_SEC0_REG1_L1_source_addr = 0
    644: f20a2c23  sw           x0, -200(x20)  # cfg[18] (bank 0) · PCK_DEST_RD_CTRL_Read_32b_data, PCK_DEST_RD_CTRL_Read_unsigned, PCK_DEST_RD_CTRL_Read_int8, PCK_DEST_RD_CTRL_Round_10b_mant · 0xffef0048; write 0x00000000; cfg[18] (bank 0); PCK_DEST_RD_CTRL_Read_32b_data = 0; PCK_DEST_RD_CTRL_Read_unsigned = 0; PCK_DEST_RD_CTRL_Read_int8 = 0; PCK_DEST_RD_CTRL_Round_10b_mant = 0
    648: 00200ab7  lui          x21, 0x00200  # x21 = 0x00200000
    64c: f35a2023  sw           x21, -224(x20)  # cfg[12] (bank 0) · PCK0_ADDR_CTRL_XY_REG_0_Xstride, PCK0_ADDR_CTRL_XY_REG_0_Ystride · 0xffef0030; write 0x00200000; cfg[12] (bank 0); PCK0_ADDR_CTRL_XY_REG_0_Xstride = 0; PCK0_ADDR_CTRL_XY_REG_0_Ystride = 32
    650: 08000ab7  lui          x21, 0x08000  # x21 = 0x08000000
    654: 200a8a93  addi         x21, x21, 512  # x21 = 0x08000200
    658: f35a2223  sw           x21, -220(x20)  # cfg[13] (bank 0) · PCK0_ADDR_CTRL_ZW_REG_0_Zstride, PCK0_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef0034; write 0x08000200; cfg[13] (bank 0); PCK0_ADDR_CTRL_ZW_REG_0_Zstride = 512; PCK0_ADDR_CTRL_ZW_REG_0_Wstride = 2048
    65c: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    660: f75a2023  sw           x21, -160(x20)  # cfg[28] (bank 0) · PACK_COUNTERS_SEC0_pack_per_xy_plane, PACK_COUNTERS_SEC0_pack_reads_per_xy_plane, PACK_COUNTERS_SEC0_pack_xys_per_tile, PACK_COUNTERS_SEC0_pack_yz_transposed, PACK_COUNTERS_SEC0_auto_ctxt_inc_xys_cnt · 0xffef0070; write 0x00001000; cfg[28] (bank 0); PACK_COUNTERS_SEC0_pack_per_xy_plane = 0; PACK_COUNTERS_SEC0_pack_reads_per_xy_plane = 16; PACK_COUNTERS_SEC0_pack_xys_per_tile = 0; PACK_COUNTERS_SEC0_pack_yz_transposed = 0; PACK_COUNTERS_SEC0_auto_ctxt_inc_xys_cnt = 0
    664: 00010ab7  lui          x21, 0x00010  # x21 = 0x00010000
    668: fffa8a93  addi         x21, x21, -1  # x21 = 0x0000ffff
    66c: f55a2823  sw           x21, -176(x20)  # cfg[24] (bank 0) · PCK_EDGE_OFFSET_SEC0_mask, PCK_EDGE_MODE_mode, PCK_EDGE_TILE_ROW_SET_SELECT_select · 0xffef0060; write 0x0000ffff; cfg[24] (bank 0); PCK_EDGE_OFFSET_SEC0_mask = 65535; PCK_EDGE_MODE_mode = 0; PCK_EDGE_TILE_ROW_SET_SELECT_select = 0
    670: f40a2a23  sw           x0, -172(x20)  # cfg[25] (bank 0) · PCK_EDGE_OFFSET_SEC1_mask · 0xffef0064; write 0x00000000; cfg[25] (bank 0); PCK_EDGE_OFFSET_SEC1_mask = 0
    674: f40a2023  sw           x0, -192(x20)  # cfg[20] (bank 0) · TILE_ROW_SET_MAPPING_0_row_set_mapping_0, TILE_ROW_SET_MAPPING_0_row_set_mapping_1, TILE_ROW_SET_MAPPING_0_row_set_mapping_2, TILE_ROW_SET_MAPPING_0_row_set_mapping_3, TILE_ROW_SET_MAPPING_0_row_set_mapping_4, TILE_ROW_SET_MAPPING_0_row_set_mapping_5, TILE_ROW_SET_MAPPING_0_row_set_mapping_6, TILE_ROW_SET_MAPPING_0_row_set_mapping_7, TILE_ROW_SET_MAPPING_0_row_set_mapping_8, TILE_ROW_SET_MAPPING_0_row_set_mapping_9, TILE_ROW_SET_MAPPING_0_row_set_mapping_10, TILE_ROW_SET_MAPPING_0_row_set_mapping_11, TILE_ROW_SET_MAPPING_0_row_set_mapping_12, TILE_ROW_SET_MAPPING_0_row_set_mapping_13, TILE_ROW_SET_MAPPING_0_row_set_mapping_14, TILE_ROW_SET_MAPPING_0_row_set_mapping_15 · 0xffef0050; write 0x00000000; cfg[20] (bank 0); TILE_ROW_SET_MAPPING_0_row_set_mapping_0 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_1 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_2 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_3 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_4 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_5 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_6 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_7 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_8 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_9 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_10 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_11 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_12 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_13 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_14 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_15 = 0
    678: f40a2223  sw           x0, -188(x20)  # cfg[21] (bank 0) · TILE_ROW_SET_MAPPING_1_row_set_mapping_0, TILE_ROW_SET_MAPPING_1_row_set_mapping_1, TILE_ROW_SET_MAPPING_1_row_set_mapping_2, TILE_ROW_SET_MAPPING_1_row_set_mapping_3, TILE_ROW_SET_MAPPING_1_row_set_mapping_4, TILE_ROW_SET_MAPPING_1_row_set_mapping_5, TILE_ROW_SET_MAPPING_1_row_set_mapping_6, TILE_ROW_SET_MAPPING_1_row_set_mapping_7, TILE_ROW_SET_MAPPING_1_row_set_mapping_8, TILE_ROW_SET_MAPPING_1_row_set_mapping_9, TILE_ROW_SET_MAPPING_1_row_set_mapping_10, TILE_ROW_SET_MAPPING_1_row_set_mapping_11, TILE_ROW_SET_MAPPING_1_row_set_mapping_12, TILE_ROW_SET_MAPPING_1_row_set_mapping_13, TILE_ROW_SET_MAPPING_1_row_set_mapping_14, TILE_ROW_SET_MAPPING_1_row_set_mapping_15 · 0xffef0054; write 0x00000000; cfg[21] (bank 0); TILE_ROW_SET_MAPPING_1_row_set_mapping_0 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_1 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_2 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_3 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_4 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_5 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_6 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_7 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_8 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_9 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_10 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_11 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_12 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_13 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_14 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_15 = 0
    67c: ffe00a37  lui          x20, 0xffe00  # x20 = 0xffe00000 · TensixMMIO.REGFILE_BASE
    680: 040a0a13  addi         x20, x20, 64  # x20 = 0xffe00040 · tensix_regfile + 0x40
    684: 08000a93  addi         x21, x0, 128  # x21 = 0x00000080
    688: 015a2023  sw           x21, 0(x20)  # tensix_regfile + 0x40 · 0xffe00040; write 0x00000080
    68c: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
    690: 095a2823  sw           x21, 144(x20)  # tensix_regfile + 0xd0 · 0xffe000d0; write 0x00040000
    694: c8940412  SETC16       setc16_reg=37, setc16_value=260  # thread_cfg[37] (current thread); ADDR_MOD_PACK_SEC0_YsrcIncr = 4; ADDR_MOD_PACK_SEC0_YsrcCR = 0; ADDR_MOD_PACK_SEC0_YsrcClear = 0; ADDR_MOD_PACK_SEC0_YdstIncr = 4; ADDR_MOD_PACK_SEC0_YdstCR = 0; ADDR_MOD_PACK_SEC0_YdstClear = 0; ADDR_MOD_PACK_SEC0_ZsrcIncr = 0; ADDR_MOD_PACK_SEC0_ZsrcClear = 0; ADDR_MOD_PACK_SEC0_ZdstIncr = 0; ADDR_MOD_PACK_SEC0_ZdstClear = 0
    698: c898a082  SETC16       setc16_reg=38, setc16_value=10272  # thread_cfg[38] (current thread); ADDR_MOD_PACK_SEC1_YsrcIncr = 0; ADDR_MOD_PACK_SEC1_YsrcCR = 0; ADDR_MOD_PACK_SEC1_YsrcClear = 1; ADDR_MOD_PACK_SEC1_YdstIncr = 0; ADDR_MOD_PACK_SEC1_YdstCR = 0; ADDR_MOD_PACK_SEC1_YdstClear = 1; ADDR_MOD_PACK_SEC1_ZsrcIncr = 0; ADDR_MOD_PACK_SEC1_ZsrcClear = 1; ADDR_MOD_PACK_SEC1_ZdstIncr = 0; ADDR_MOD_PACK_SEC1_ZdstClear = 0
    69c: c89c4482  SETC16       setc16_reg=39, setc16_value=4384  # thread_cfg[39] (current thread); ADDR_MOD_PACK_SEC2_YsrcIncr = 0; ADDR_MOD_PACK_SEC2_YsrcCR = 0; ADDR_MOD_PACK_SEC2_YsrcClear = 1; ADDR_MOD_PACK_SEC2_YdstIncr = 4; ADDR_MOD_PACK_SEC2_YdstCR = 0; ADDR_MOD_PACK_SEC2_YdstClear = 0; ADDR_MOD_PACK_SEC2_ZsrcIncr = 1; ADDR_MOD_PACK_SEC2_ZsrcClear = 0; ADDR_MOD_PACK_SEC2_ZdstIncr = 0; ADDR_MOD_PACK_SEC2_ZdstClear = 0
    6a0: 4600002d  SETADCXY     CntSetMask=4, Ch1_Y=0, Ch1_X=0, Ch0_Y=0, Ch0_X=0, BitMask=11
    6a4: 5200003d  SETADCZW     CntSetMask=4, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    6a8: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    6ac: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    6b0: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    6b4: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    6b8: 01507033  and          x0, x0, x21
    6bc: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    6c0: 00400a93  addi         x21, x0, 4  # x21 = 0x00000004
    6c4: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000004
    6c8: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000004
    6cc: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    6d0: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
    6d4: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x02000000; MOP template instruction · NOP
    6d8: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    6dc: 41000ab7  lui          x21, 0x41000  # x21 = 0x41000000
    6e0: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x41000000; MOP template instruction · PACR CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=0, AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=0
    6e4: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    6e8: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    6ec: 41008ab7  lui          x21, 0x41008  # x21 = 0x41008000
    6f0: 001a8a93  addi         x21, x21, 1  # x21 = 0x41008001
    6f4: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x41008001; MOP template instruction · PACR CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=1, AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=1
    6f8: 41010ab7  lui          x21, 0x41010  # x21 = 0x41010000
    6fc: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x41010000; MOP template instruction · PACR CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=2, AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=0
    700: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    704: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    708: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    70c: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    710: 01507033  and          x0, x0, x21
    714: ffb01bb7  lui          x23, 0xffb01  # x23 = 0xffb01000
    718: 8d0b8b93  addi         x23, x23, -1840  # x23 = 0xffb008d0 · riscv_local_mem + 0x8d0
    71c: 000baa03  lw           x20, 0(x23)  # riscv_local_mem + 0x8d0 · 0xffb008d0
    720: 004a5a13  srli         x20, x20, 4
    724: fffa0a13  addi         x20, x20, -1
    728: 508c0bb7  lui          x23, 0x508c0  # x23 = 0x508c0000
    72c: 01fbebb3  or           x23, x23, x31  # x23 = 0x508c0000
    730: ffe40c37  lui          x24, 0xffe40  # x24 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    734: 017c2023  sw           x23, 0(x24)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write 0x508c0000; MMIO instruction · SETADC CntSetMask=4, ChannelIndex=0, DimensionIndex=3, Value=0
    738: 008a1c13  slli         x24, x20, 8
    73c: 01000cb7  lui          x25, 0x01000  # x25 = 0x01000000
    740: f00c8c93  addi         x25, x25, -256  # x25 = 0x00ffff00
    744: 019c7c33  and          x24, x24, x25
    748: 45000d37  lui          x26, 0x45000  # x26 = 0x45000000
    74c: 018d0d13  addi         x26, x26, 24  # x26 = 0x45000018
    750: 01ac6c33  or           x24, x24, x26
    754: ffe40db7  lui          x27, 0xffe40  # x27 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    758: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    75c: 010a5a93  srli         x21, x20, 16
    760: 00008b37  lui          x22, 0x00008  # x22 = 0x00008000
    764: 015b6b33  or           x22, x22, x21
    768: 008b1c13  slli         x24, x22, 8
    76c: 01000cb7  lui          x25, 0x01000  # x25 = 0x01000000
    770: f00c8c93  addi         x25, x25, -256  # x25 = 0x00ffff00
    774: 019c7c33  and          x24, x24, x25
    778: 45000d37  lui          x26, 0x45000  # x26 = 0x45000000
    77c: 019d0d13  addi         x26, x26, 25  # x26 = 0x45000019
    780: 01ac6c33  or           x24, x24, x26
    784: ffe40db7  lui          x27, 0xffe40  # x27 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    788: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    78c: 89000026  STALLWAIT    stall_res=128, wait_res=9  # stall_res: Stall.CFG; wait_res: Wait.THCON | Wait.PACK0
    790: c0300116  WRCFG        GprAddress=12, wr128b=0, CfgReg=69  # cfg[69] (current thread StateID); THCON_SEC0_REG1_L1_Dest_addr = runtime
    794: 008a9c13  slli         x24, x21, 8
    798: 01000cb7  lui          x25, 0x01000  # x25 = 0x01000000
    79c: f00c8c93  addi         x25, x25, -256  # x25 = 0x00ffff00
    7a0: 019c7c33  and          x24, x24, x25
    7a4: 45000d37  lui          x26, 0x45000  # x26 = 0x45000000
    7a8: 019d0d13  addi         x26, x26, 25  # x26 = 0x45000019
    7ac: 01ac6c33  or           x24, x24, x26
    7b0: ffe40db7  lui          x27, 0xffe40  # x27 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    7b4: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    7b8: 80000001  DMANOP
    7bc: 7a00f001  SETADCXX     CntSetMask=4, x_end2=15, x_start=0
    7c0: 52000015  SETADCZW     CntSetMask=4, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=5
    7c4: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    7c8: 2d0a0a13  addi         x20, x20, 720  # x20 = 0xffef02d0 · cfg[180] (bank 0) · DEST_TARGET_REG_CFG_PACK_SEC0_Offset, DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset
    7cc: 00000a93  addi         x21, x0, 0  # x21 = 0x00000000
    7d0: 015a2023  sw           x21, 0(x20)  # cfg[180] (bank 0) · DEST_TARGET_REG_CFG_PACK_SEC0_Offset, DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset · 0xffef02d0; write 0x00000000; cfg[180] (bank 0); DEST_TARGET_REG_CFG_PACK_SEC0_Offset = 0; DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset = 0
    7d4: 89000022  STALLWAIT    stall_res=128, wait_res=8  # stall_res: Stall.CFG; wait_res: Wait.PACK0
    7d8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    7dc: 88040022  STALLWAIT    stall_res=2, wait_res=8  # stall_res: Stall.SYNC; wait_res: Wait.PACK0
    7e0: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    7e4: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    7e8: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    7ec: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    7f0: 01507033  and          x0, x0, x21
    7f4: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    7f8: 8d0c0c13  addi         x24, x24, -1840  # x24 = 0xffb008d0 · riscv_local_mem + 0x8d0
    7fc: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x8d0 · 0xffb008d0
    800: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    804: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    808: 015a0a33  add          x20, x20, x21
    80c: 00027b37  lui          x22, 0x00027  # x22 = 0x00027000
    810: 880b0b13  addi         x22, x22, -1920  # x22 = 0x00026880
    814: 016a6863  bltu         x20, x22, 0x00000824  # target 0x00000824
    818: 00001bb7  lui          x23, 0x00001  # x23 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    81c: 800b8b93  addi         x23, x23, -2048  # x23 = 0x00000800
    820: 417a0a33  sub          x20, x20, x23
loc_824:
    824: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    828: 8d0c0c13  addi         x24, x24, -1840  # x24 = 0xffb008d0 · riscv_local_mem + 0x8d0
    82c: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x8d0 · 0xffb008d0; write runtime value
    830: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    834: 8d4a8a93  addi         x21, x21, -1836  # x21 = 0xffb008d4 · riscv_local_mem + 0x8d4
    838: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x8d4 · 0xffb008d4
    83c: 001a0a13  addi         x20, x20, 1
    840: 010a1a13  slli         x20, x20, 16
    844: 010a5a13  srli         x20, x20, 16
    848: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    84c: 8d4a8a93  addi         x21, x21, -1836  # x21 = 0xffb008d4 · riscv_local_mem + 0x8d4
    850: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x8d4 · 0xffb008d4; write runtime value
    854: ffb4eab7  lui          x21, 0xffb4e  # x21 = 0xffb4e000
    858: 028a8a93  addi         x21, x21, 40  # x21 = 0xffb4e028
    85c: 014aa023  sw           x20, 0(x21)  # 0xffb4e028; write runtime value
    860: 0ff0000f  fence        0xf, 0xf
    864: 40610000  ZEROACC      clear_mode=3, use_32_bit_mode=0, clear_zero_flags=0, addr_mode=1, where=0
    868: 94000022  SEMGET       sem_sel=2  # sem_sel: Sem.MATH_PACK
    86c:           j FW_TRISC2+4   # return to firmware, linked at install
