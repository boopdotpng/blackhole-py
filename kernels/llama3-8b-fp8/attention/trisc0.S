# llama3 8b-fp8 decode: attention, trisc0. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (32): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3
# params: 0x7c0=e2e_q_heads, 0x7c4=e2e_l0_key_cache, 0x7c8=e2e_l0_value_cache, 0x7cc=e2e_context, 0x7d0=kv_blocks, 0x7d4=valid_columns, 0x7d8=attention_e2e_q_compact, 0x7dc=attention_e2e_k_compact, 0x7e0=attention_e2e_v_compact, 0x7e4=e2e_rope_cos, 0x7e8=e2e_rope_sin, 0x7ec=start_pos, 0x80c0=attention_core
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama3.py installs it resident in L1 at 0x12000+ per core.

      0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
      4: 820a8a93  addi         x21, x21, -2016  # x21 = 0xffb00820 · riscv_local_mem + 0x820
      8: 000a0b37  lui          x22, 0x000a0  # x22 = 0x000a0000
      c: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x820 · 0xffb00820; write 0x000a0000
     10: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     14: 824a8a93  addi         x21, x21, -2012  # x21 = 0xffb00824 · riscv_local_mem + 0x824
     18: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x824 · 0xffb00824; write 0x00000000
     1c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     20: 828a8a93  addi         x21, x21, -2008  # x21 = 0xffb00828 · riscv_local_mem + 0x828
     24: 00092b37  lui          x22, 0x00092  # x22 = 0x00092000
     28: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x828 · 0xffb00828; write 0x00092000
     2c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     30: 82ca8a93  addi         x21, x21, -2004  # x21 = 0xffb0082c · riscv_local_mem + 0x82c
     34: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x82c · 0xffb0082c; write 0x00000000
     38: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     3c: 830a8a93  addi         x21, x21, -2000  # x21 = 0xffb00830 · riscv_local_mem + 0x830
     40: 00090b37  lui          x22, 0x00090  # x22 = 0x00090000
     44: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x830 · 0xffb00830; write 0x00090000
     48: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     4c: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
     50: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834; write 0x00000000
     54: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     58: 838a8a93  addi         x21, x21, -1992  # x21 = 0xffb00838 · riscv_local_mem + 0x838
     5c: 0009db37  lui          x22, 0x0009d  # x22 = 0x0009d000
     60: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x838 · 0xffb00838; write 0x0009d000
     64: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     68: 83ca8a93  addi         x21, x21, -1988  # x21 = 0xffb0083c · riscv_local_mem + 0x83c
     6c: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x83c · 0xffb0083c; write 0x00000000
     70: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     74: 840a8a93  addi         x21, x21, -1984  # x21 = 0xffb00840 · riscv_local_mem + 0x840
     78: 0009cb37  lui          x22, 0x0009c  # x22 = 0x0009c000
     7c: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x840 · 0xffb00840; write 0x0009c000
     80: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     84: 844a8a93  addi         x21, x21, -1980  # x21 = 0xffb00844 · riscv_local_mem + 0x844
     88: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x844 · 0xffb00844; write 0x00000000
     8c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     90: 848a8a93  addi         x21, x21, -1976  # x21 = 0xffb00848 · riscv_local_mem + 0x848
     94: 00096b37  lui          x22, 0x00096  # x22 = 0x00096000
     98: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x848 · 0xffb00848; write 0x00096000
     9c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     a0: 84ca8a93  addi         x21, x21, -1972  # x21 = 0xffb0084c · riscv_local_mem + 0x84c
     a4: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x84c · 0xffb0084c; write 0x00000000
     a8: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     ac: 850a8a93  addi         x21, x21, -1968  # x21 = 0xffb00850 · riscv_local_mem + 0x850
     b0: 0009ab37  lui          x22, 0x0009a  # x22 = 0x0009a000
     b4: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x850 · 0xffb00850; write 0x0009a000
     b8: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     bc: 854a8a93  addi         x21, x21, -1964  # x21 = 0xffb00854 · riscv_local_mem + 0x854
     c0: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x854 · 0xffb00854; write 0x00000000
     c4: 660000ef  jal          x1, 0x00000724  # target 0x00000724; x1 = 0x000000c8
     c8: 65c000ef  jal          x1, 0x00000724  # target 0x00000724; x1 = 0x000000cc
     cc: 658000ef  jal          x1, 0x00000724  # target 0x00000724; x1 = 0x000000d0
     d0: 654000ef  jal          x1, 0x00000724  # target 0x00000724; x1 = 0x000000d4
     d4: 7d000313  addi         x6, x0, 2000  # x6 = 0x000007d0
     d8: 00032203  lw           x4, 0(x6)  # param kv_blocks; 0x000007d0
     dc: fff20293  addi         x5, x4, -1
     e0: 00000313  addi         x6, x0, 0  # x6 = 0x00000000
     e4: 00020393  addi         x7, x4, 0
loc_e8:
     e8: 62737c63  bgeu         x6, x7, 0x00000720  # target 0x00000720
     ec: ffe80437  lui          x8, 0xffe80  # x8 = 0xffe80000 · tensix_pc_buf + 0x0
     f0: 03440413  addi         x8, x8, 52  # x8 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_f4:
     f4: 00042483  lw           x9, 0(x8)  # UNPACK_CONFIG_SYNC · 0xffe80034
     f8: 0fe4f493  andi         x9, x9, 254
     fc: 00048663  beq          x9, x0, 0x00000108  # target 0x00000108
    100: 0ff0000f  fence        0xf, 0xf
    104: ff1ff06f  jal          x0, 0x000000f4  # target 0x000000f4
loc_108:
    108: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    10c: d500011e  RMWCIB2      Mask=64, Data=0, CfgRegAddr=71  # cfg[71] (current thread StateID); THCON_SEC0_REG1_Unp_LF8_4b_exp = 0
    110: ffef0437  lui          x8, 0xffef0  # x8 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    114: 10040413  addi         x8, x8, 256  # x8 = 0xffef0100 · cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor
    118: 01500493  addi         x9, x0, 21  # x9 = 0x00000015
    11c: 00942023  sw           x9, 0(x8)  # cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor · 0xffef0100; write 0x00000015; cfg[64] (bank 0); THCON_SEC0_REG0_TileDescriptor = 21
    120: 000404b7  lui          x9, 0x00040  # x9 = 0x00040000
    124: 00148493  addi         x9, x9, 1  # x9 = 0x00040001
    128: 00942223  sw           x9, 4(x8)  # cfg[65] (bank 0) (undocumented index) · 0xffef0104; write 0x00040001; cfg[65] (bank 0) · fields not in ttsim
    12c: 00042423  sw           x0, 8(x8)  # cfg[66] (bank 0) (undocumented index) · 0xffef0108; write 0x00000000; cfg[66] (bank 0) · fields not in ttsim
    130: 00042623  sw           x0, 12(x8)  # cfg[67] (bank 0) (undocumented index) · 0xffef010c; write 0x00000000; cfg[67] (bank 0) · fields not in ttsim
    134: 12500493  addi         x9, x0, 293  # x9 = 0x00000125
    138: 02942023  sw           x9, 32(x8)  # cfg[72] (bank 0) · THCON_SEC0_REG2_Out_data_format, THCON_SEC0_REG2_Throttle_mode, THCON_SEC0_REG2_Context_count, THCON_SEC0_REG2_Haloize_mode, THCON_SEC0_REG2_Tileize_mode, THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC0_REG2_Unpack_If_Sel, THCON_SEC0_REG2_Upsample_rate, THCON_SEC0_REG2_Ovrd_data_format, THCON_SEC0_REG2_Upsample_and_interleave, THCON_SEC0_REG2_Shift_amount_cntx0, THCON_SEC0_REG2_Shift_amount_cntx1, THCON_SEC0_REG2_Shift_amount_cntx2, THCON_SEC0_REG2_Shift_amount_cntx3 · 0xffef0120; write 0x00000125; cfg[72] (bank 0); THCON_SEC0_REG2_Out_data_format = 5; THCON_SEC0_REG2_Throttle_mode = 2; THCON_SEC0_REG2_Context_count = 0; THCON_SEC0_REG2_Haloize_mode = 1; THCON_SEC0_REG2_Tileize_mode = 0; THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC0_REG2_Unpack_If_Sel = 0; THCON_SEC0_REG2_Upsample_rate = 0; THCON_SEC0_REG2_Ovrd_data_format = 0; THCON_SEC0_REG2_Upsample_and_interleave = 0; THCON_SEC0_REG2_Shift_amount_cntx0 = 0; THCON_SEC0_REG2_Shift_amount_cntx1 = 0; THCON_SEC0_REG2_Shift_amount_cntx2 = 0; THCON_SEC0_REG2_Shift_amount_cntx3 = 0
    13c: 00300493  addi         x9, x0, 3  # x9 = 0x00000003
    140: 02942223  sw           x9, 36(x8)  # cfg[73] (bank 0) · THCON_SEC0_REG2_Disable_zero_compress_cntx0, THCON_SEC0_REG2_Disable_zero_compress_cntx1, THCON_SEC0_REG2_Disable_zero_compress_cntx2, THCON_SEC0_REG2_Disable_zero_compress_cntx3, THCON_SEC0_REG2_Unpack_if_sel_cntx0, THCON_SEC0_REG2_Unpack_if_sel_cntx1, THCON_SEC0_REG2_Unpack_if_sel_cntx2, THCON_SEC0_REG2_Unpack_if_sel_cntx3, THCON_SEC0_REG2_Force_shared_exp, THCON_SEC0_REG2_Context_count_non_log2, THCON_SEC0_REG2_Context_count_non_log2_en, THCON_SEC0_REG2_Disable_zero_compress_cntx4, THCON_SEC0_REG2_Disable_zero_compress_cntx5, THCON_SEC0_REG2_Disable_zero_compress_cntx6, THCON_SEC0_REG2_Disable_zero_compress_cntx7, THCON_SEC0_REG2_Unpack_if_sel_cntx4, THCON_SEC0_REG2_Unpack_if_sel_cntx5, THCON_SEC0_REG2_Unpack_if_sel_cntx6, THCON_SEC0_REG2_Unpack_if_sel_cntx7, THCON_SEC0_REG2_Metadata_x_end · 0xffef0124; write 0x00000003; cfg[73] (bank 0); THCON_SEC0_REG2_Disable_zero_compress_cntx0 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx1 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx2 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx3 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx0 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx1 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx2 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx3 = 0; THCON_SEC0_REG2_Force_shared_exp = 0; THCON_SEC0_REG2_Context_count_non_log2 = 0; THCON_SEC0_REG2_Context_count_non_log2_en = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx4 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx5 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx6 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx7 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx4 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx5 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx6 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx7 = 0; THCON_SEC0_REG2_Metadata_x_end = 0
    144: 02042423  sw           x0, 40(x8)  # cfg[74] (bank 0) · THCON_SEC0_REG2_Unpack_limit_address · 0xffef0128; write 0x00000000; cfg[74] (bank 0); THCON_SEC0_REG2_Unpack_limit_address = 0
    148: 02042623  sw           x0, 44(x8)  # cfg[75] (bank 0) · THCON_SEC0_REG2_Unpack_fifo_size · 0xffef012c; write 0x00000000; cfg[75] (bank 0); THCON_SEC0_REG2_Unpack_fifo_size = 0
    14c: fa042823  sw           x0, -80(x8)  # cfg[44] (bank 0) · UNP0_ADDR_CTRL_XY_REG_0_Xstride, UNP0_ADDR_CTRL_XY_REG_0_Ystride · 0xffef00b0; write 0x00000000; cfg[44] (bank 0); UNP0_ADDR_CTRL_XY_REG_0_Xstride = 0; UNP0_ADDR_CTRL_XY_REG_0_Ystride = 0
    150: fa042a23  sw           x0, -76(x8)  # cfg[45] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_0_Zstride, UNP0_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef00b4; write 0x00000000; cfg[45] (bank 0); UNP0_ADDR_CTRL_ZW_REG_0_Zstride = 0; UNP0_ADDR_CTRL_ZW_REG_0_Wstride = 0
    154: 002004b7  lui          x9, 0x00200  # x9 = 0x00200000
    158: 00248493  addi         x9, x9, 2  # x9 = 0x00200002
    15c: fe942023  sw           x9, -32(x8)  # cfg[56] (bank 0) · UNP0_ADDR_CTRL_XY_REG_1_Xstride, UNP0_ADDR_CTRL_XY_REG_1_Ystride · 0xffef00e0; write 0x00200002; cfg[56] (bank 0); UNP0_ADDR_CTRL_XY_REG_1_Xstride = 2; UNP0_ADDR_CTRL_XY_REG_1_Ystride = 32
    160: 20000493  addi         x9, x0, 512  # x9 = 0x00000200
    164: fe942223  sw           x9, -28(x8)  # cfg[57] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_1_Zstride, UNP0_ADDR_CTRL_ZW_REG_1_Wstride · 0xffef00e4; write 0x00000200; cfg[57] (bank 0); UNP0_ADDR_CTRL_ZW_REG_1_Zstride = 512; UNP0_ADDR_CTRL_ZW_REG_1_Wstride = 0
    168: fc042023  sw           x0, -64(x8)  # cfg[48] (bank 0) · UNP0_ADDR_BASE_REG_0_Base · 0xffef00c0; write 0x00000000; cfg[48] (bank 0); UNP0_ADDR_BASE_REG_0_Base = 0
    16c: fc042223  sw           x0, -60(x8)  # cfg[49] (bank 0) · UNP0_ADDR_BASE_REG_1_Base · 0xffef00c4; write 0x00000000; cfg[49] (bank 0); UNP0_ADDR_BASE_REG_1_Base = 0
    170: 10000493  addi         x9, x0, 256  # x9 = 0x00000100
    174: fc942423  sw           x9, -56(x8)  # cfg[50] (bank 0) · UNP0_FORCED_SHARED_EXP_shared_exp, UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr · 0xffef00c8; write 0x00000100; cfg[50] (bank 0); UNP0_FORCED_SHARED_EXP_shared_exp = 0; UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr = 1
    178: fc042a23  sw           x0, -44(x8)  # cfg[53] (bank 0) · UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val · 0xffef00d4; write 0x00000000; cfg[53] (bank 0); UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val = 0
    17c: 004004b7  lui          x9, 0x00400  # x9 = 0x00400000
    180: 04048493  addi         x9, x9, 64  # x9 = 0x00400040
    184: 04942823  sw           x9, 80(x8)  # cfg[84] (bank 0) · THCON_SEC0_REG5_Dest_cntx0_address, THCON_SEC0_REG5_Dest_cntx1_address · 0xffef0150; write 0x00400040; cfg[84] (bank 0); THCON_SEC0_REG5_Dest_cntx0_address = 64; THCON_SEC0_REG5_Dest_cntx1_address = 64
    188: 010004b7  lui          x9, 0x01000  # x9 = 0x01000000
    18c: 10048493  addi         x9, x9, 256  # x9 = 0x01000100
    190: 04942c23  sw           x9, 88(x8)  # cfg[86] (bank 0) · THCON_SEC0_REG5_Tile_x_dim_cntx0, THCON_SEC0_REG5_Tile_x_dim_cntx1 · 0xffef0158; write 0x01000100; cfg[86] (bank 0); THCON_SEC0_REG5_Tile_x_dim_cntx0 = 256; THCON_SEC0_REG5_Tile_x_dim_cntx1 = 256
    194: 06042823  sw           x0, 112(x8)  # cfg[92] (bank 0) · THCON_SEC0_REG7_Offset_address, THCON_SEC0_REG7_Unpack_data_format_cntx0, THCON_SEC0_REG7_Unpack_out_data_format_cntx0, THCON_SEC0_REG7_Unpack_data_format_cntx4, THCON_SEC0_REG7_Unpack_out_data_format_cntx4 · 0xffef0170; write 0x00000000; cfg[92] (bank 0); THCON_SEC0_REG7_Offset_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx4 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx4 = 0
    198: 06042a23  sw           x0, 116(x8)  # cfg[93] (bank 0) · THCON_SEC0_REG7_Offset_cntx1_address, THCON_SEC0_REG7_Unpack_data_format_cntx1, THCON_SEC0_REG7_Unpack_out_data_format_cntx1, THCON_SEC0_REG7_Unpack_data_format_cntx5, THCON_SEC0_REG7_Unpack_out_data_format_cntx5 · 0xffef0174; write 0x00000000; cfg[93] (bank 0); THCON_SEC0_REG7_Offset_cntx1_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx5 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx5 = 0
    19c: d50001de  RMWCIB2      Mask=64, Data=0, CfgRegAddr=119  # cfg[119] (current thread StateID); THCON_SEC1_REG1_Unp_LF8_4b_exp = 0
    1a0: ffef0437  lui          x8, 0xffef0  # x8 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    1a4: 1c040413  addi         x8, x8, 448  # x8 = 0xffef01c0 · cfg[112] (bank 0) · THCON_SEC1_REG0_TileDescriptor
    1a8: 010004b7  lui          x9, 0x01000  # x9 = 0x01000000
    1ac: 01548493  addi         x9, x9, 21  # x9 = 0x01000015
    1b0: 00942023  sw           x9, 0(x8)  # cfg[112] (bank 0) · THCON_SEC1_REG0_TileDescriptor · 0xffef01c0; write 0x01000015; cfg[112] (bank 0); THCON_SEC1_REG0_TileDescriptor = 16777237
    1b4: 000404b7  lui          x9, 0x00040  # x9 = 0x00040000
    1b8: 00148493  addi         x9, x9, 1  # x9 = 0x00040001
    1bc: 00942223  sw           x9, 4(x8)  # cfg[113] (bank 0) (undocumented index) · 0xffef01c4; write 0x00040001; cfg[113] (bank 0) · fields not in ttsim
    1c0: 00042423  sw           x0, 8(x8)  # cfg[114] (bank 0) (undocumented index) · 0xffef01c8; write 0x00000000; cfg[114] (bank 0) · fields not in ttsim
    1c4: 00042623  sw           x0, 12(x8)  # cfg[115] (bank 0) (undocumented index) · 0xffef01cc; write 0x00000000; cfg[115] (bank 0) · fields not in ttsim
    1c8: 02500493  addi         x9, x0, 37  # x9 = 0x00000025
    1cc: 02942023  sw           x9, 32(x8)  # cfg[120] (bank 0) · THCON_SEC1_REG2_Out_data_format, THCON_SEC1_REG2_Throttle_mode, THCON_SEC1_REG2_Context_count, THCON_SEC1_REG2_Haloize_mode, THCON_SEC1_REG2_Tileize_mode, THCON_SEC1_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC1_REG2_Unpack_If_Sel, THCON_SEC1_REG2_Upsample_rate, THCON_SEC1_REG2_Ovrd_data_format, THCON_SEC1_REG2_Upsample_and_interleave, THCON_SEC1_REG2_Shift_amount_cntx0, THCON_SEC1_REG2_Shift_amount_cntx1, THCON_SEC1_REG2_Shift_amount_cntx2, THCON_SEC1_REG2_Shift_amount_cntx3 · 0xffef01e0; write 0x00000025; cfg[120] (bank 0); THCON_SEC1_REG2_Out_data_format = 5; THCON_SEC1_REG2_Throttle_mode = 2; THCON_SEC1_REG2_Context_count = 0; THCON_SEC1_REG2_Haloize_mode = 0; THCON_SEC1_REG2_Tileize_mode = 0; THCON_SEC1_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC1_REG2_Unpack_If_Sel = 0; THCON_SEC1_REG2_Upsample_rate = 0; THCON_SEC1_REG2_Ovrd_data_format = 0; THCON_SEC1_REG2_Upsample_and_interleave = 0; THCON_SEC1_REG2_Shift_amount_cntx0 = 0; THCON_SEC1_REG2_Shift_amount_cntx1 = 0; THCON_SEC1_REG2_Shift_amount_cntx2 = 0; THCON_SEC1_REG2_Shift_amount_cntx3 = 0
    1d0: 00300493  addi         x9, x0, 3  # x9 = 0x00000003
    1d4: 02942223  sw           x9, 36(x8)  # cfg[121] (bank 0) · THCON_SEC1_REG2_Disable_zero_compress_cntx0, THCON_SEC1_REG2_Disable_zero_compress_cntx1, THCON_SEC1_REG2_Disable_zero_compress_cntx2, THCON_SEC1_REG2_Disable_zero_compress_cntx3, THCON_SEC1_REG2_Unpack_if_sel_cntx0, THCON_SEC1_REG2_Unpack_if_sel_cntx1, THCON_SEC1_REG2_Unpack_if_sel_cntx2, THCON_SEC1_REG2_Unpack_if_sel_cntx3, THCON_SEC1_REG2_Force_shared_exp, THCON_SEC1_REG2_Context_count_non_log2, THCON_SEC1_REG2_Context_count_non_log2_en, THCON_SEC1_REG2_Disable_zero_compress_cntx4, THCON_SEC1_REG2_Disable_zero_compress_cntx5, THCON_SEC1_REG2_Disable_zero_compress_cntx6, THCON_SEC1_REG2_Disable_zero_compress_cntx7, THCON_SEC1_REG2_Unpack_if_sel_cntx4, THCON_SEC1_REG2_Unpack_if_sel_cntx5, THCON_SEC1_REG2_Unpack_if_sel_cntx6, THCON_SEC1_REG2_Unpack_if_sel_cntx7, THCON_SEC1_REG2_Metadata_x_end · 0xffef01e4; write 0x00000003; cfg[121] (bank 0); THCON_SEC1_REG2_Disable_zero_compress_cntx0 = 1; THCON_SEC1_REG2_Disable_zero_compress_cntx1 = 1; THCON_SEC1_REG2_Disable_zero_compress_cntx2 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx3 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx0 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx1 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx2 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx3 = 0; THCON_SEC1_REG2_Force_shared_exp = 0; THCON_SEC1_REG2_Context_count_non_log2 = 0; THCON_SEC1_REG2_Context_count_non_log2_en = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx4 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx5 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx6 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx7 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx4 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx5 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx6 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx7 = 0; THCON_SEC1_REG2_Metadata_x_end = 0
    1d8: 02042423  sw           x0, 40(x8)  # cfg[122] (bank 0) · THCON_SEC1_REG2_Unpack_limit_address · 0xffef01e8; write 0x00000000; cfg[122] (bank 0); THCON_SEC1_REG2_Unpack_limit_address = 0
    1dc: 02042623  sw           x0, 44(x8)  # cfg[123] (bank 0) · THCON_SEC1_REG2_Unpack_fifo_size · 0xffef01ec; write 0x00000000; cfg[123] (bank 0); THCON_SEC1_REG2_Unpack_fifo_size = 0
    1e0: ee042c23  sw           x0, -264(x8)  # cfg[46] (bank 0) · UNP1_ADDR_CTRL_XY_REG_0_Xstride, UNP1_ADDR_CTRL_XY_REG_0_Ystride · 0xffef00b8; write 0x00000000; cfg[46] (bank 0); UNP1_ADDR_CTRL_XY_REG_0_Xstride = 0; UNP1_ADDR_CTRL_XY_REG_0_Ystride = 0
    1e4: ee042e23  sw           x0, -260(x8)  # cfg[47] (bank 0) · UNP1_ADDR_CTRL_ZW_REG_0_Zstride, UNP1_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef00bc; write 0x00000000; cfg[47] (bank 0); UNP1_ADDR_CTRL_ZW_REG_0_Zstride = 0; UNP1_ADDR_CTRL_ZW_REG_0_Wstride = 0
    1e8: 002004b7  lui          x9, 0x00200  # x9 = 0x00200000
    1ec: 00248493  addi         x9, x9, 2  # x9 = 0x00200002
    1f0: f2942423  sw           x9, -216(x8)  # cfg[58] (bank 0) · UNP1_ADDR_CTRL_XY_REG_1_Xstride, UNP1_ADDR_CTRL_XY_REG_1_Ystride · 0xffef00e8; write 0x00200002; cfg[58] (bank 0); UNP1_ADDR_CTRL_XY_REG_1_Xstride = 2; UNP1_ADDR_CTRL_XY_REG_1_Ystride = 32
    1f4: 20000493  addi         x9, x0, 512  # x9 = 0x00000200
    1f8: f2942623  sw           x9, -212(x8)  # cfg[59] (bank 0) · UNP1_ADDR_CTRL_ZW_REG_1_Zstride, UNP1_ADDR_CTRL_ZW_REG_1_Wstride · 0xffef00ec; write 0x00000200; cfg[59] (bank 0); UNP1_ADDR_CTRL_ZW_REG_1_Zstride = 512; UNP1_ADDR_CTRL_ZW_REG_1_Wstride = 0
    1fc: f2042823  sw           x0, -208(x8)  # cfg[60] (bank 0) · UNP1_ADDR_BASE_REG_0_Base · 0xffef00f0; write 0x00000000; cfg[60] (bank 0); UNP1_ADDR_BASE_REG_0_Base = 0
    200: f2042a23  sw           x0, -204(x8)  # cfg[61] (bank 0) · UNP1_ADDR_BASE_REG_1_Base · 0xffef00f4; write 0x00000000; cfg[61] (bank 0); UNP1_ADDR_BASE_REG_1_Base = 0
    204: f2042c23  sw           x0, -200(x8)  # cfg[62] (bank 0) · UNP1_FORCED_SHARED_EXP_shared_exp, UNP1_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr · 0xffef00f8; write 0x00000000; cfg[62] (bank 0); UNP1_FORCED_SHARED_EXP_shared_exp = 0; UNP1_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr = 0
    208: f2042e23  sw           x0, -196(x8)  # cfg[63] (bank 0) · UNP1_NOP_REG_CLR_VAL_nop_reg_clr_val · 0xffef00fc; write 0x00000000; cfg[63] (bank 0); UNP1_NOP_REG_CLR_VAL_nop_reg_clr_val = 0
    20c: 04042823  sw           x0, 80(x8)  # cfg[132] (bank 0) · THCON_SEC1_REG5_Dest_cntx0_address, THCON_SEC1_REG5_Dest_cntx1_address · 0xffef0210; write 0x00000000; cfg[132] (bank 0); THCON_SEC1_REG5_Dest_cntx0_address = 0; THCON_SEC1_REG5_Dest_cntx1_address = 0
    210: 010004b7  lui          x9, 0x01000  # x9 = 0x01000000
    214: 10048493  addi         x9, x9, 256  # x9 = 0x01000100
    218: 04942c23  sw           x9, 88(x8)  # cfg[134] (bank 0) · THCON_SEC1_REG5_Tile_x_dim_cntx0, THCON_SEC1_REG5_Tile_x_dim_cntx1 · 0xffef0218; write 0x01000100; cfg[134] (bank 0); THCON_SEC1_REG5_Tile_x_dim_cntx0 = 256; THCON_SEC1_REG5_Tile_x_dim_cntx1 = 256
    21c: 06042823  sw           x0, 112(x8)  # cfg[140] (bank 0) · THCON_SEC1_REG7_Offset_address, THCON_SEC1_REG7_Unpack_data_format_cntx0, THCON_SEC1_REG7_Unpack_out_data_format_cntx0, THCON_SEC1_REG7_Unpack_data_format_cntx4, THCON_SEC1_REG7_Unpack_out_data_format_cntx4 · 0xffef0230; write 0x00000000; cfg[140] (bank 0); THCON_SEC1_REG7_Offset_address = 0; THCON_SEC1_REG7_Unpack_data_format_cntx0 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx0 = 0; THCON_SEC1_REG7_Unpack_data_format_cntx4 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx4 = 0
    220: 06042a23  sw           x0, 116(x8)  # cfg[141] (bank 0) · THCON_SEC1_REG7_Offset_cntx1_address, THCON_SEC1_REG7_Unpack_data_format_cntx1, THCON_SEC1_REG7_Unpack_out_data_format_cntx1, THCON_SEC1_REG7_Unpack_data_format_cntx5, THCON_SEC1_REG7_Unpack_out_data_format_cntx5 · 0xffef0234; write 0x00000000; cfg[141] (bank 0); THCON_SEC1_REG7_Offset_cntx1_address = 0; THCON_SEC1_REG7_Unpack_data_format_cntx1 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx1 = 0; THCON_SEC1_REG7_Unpack_data_format_cntx5 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx5 = 0
    224: 730000ef  jal          x1, 0x00000954  # target 0x00000954; x1 = 0x00000228
    228: 72c000ef  jal          x1, 0x00000954  # target 0x00000954; x1 = 0x0000022c
    22c: 728000ef  jal          x1, 0x00000954  # target 0x00000954; x1 = 0x00000230
    230: 724000ef  jal          x1, 0x00000954  # target 0x00000954; x1 = 0x00000234
    234: 38531e63  bne          x6, x5, 0x000005d0  # target 0x000005d0
    238: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    23c: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_240:
    240: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    244: 0feafa93  andi         x21, x21, 254
    248: 000a8663  beq          x21, x0, 0x00000254  # target 0x00000254
    24c: 0ff0000f  fence        0xf, 0xf
    250: ff1ff06f  jal          x0, 0x00000240  # target 0x00000240
loc_254:
    254: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    258: d500011e  RMWCIB2      Mask=64, Data=0, CfgRegAddr=71  # cfg[71] (current thread StateID); THCON_SEC0_REG1_Unp_LF8_4b_exp = 0
    25c: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    260: 100a0a13  addi         x20, x20, 256  # x20 = 0xffef0100 · cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor
    264: 01000a93  addi         x21, x0, 16  # x21 = 0x00000010
    268: 015a2023  sw           x21, 0(x20)  # cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor · 0xffef0100; write 0x00000010; cfg[64] (bank 0); THCON_SEC0_REG0_TileDescriptor = 16
    26c: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
    270: 001a8a93  addi         x21, x21, 1  # x21 = 0x00040001
    274: 015a2223  sw           x21, 4(x20)  # cfg[65] (bank 0) (undocumented index) · 0xffef0104; write 0x00040001; cfg[65] (bank 0) · fields not in ttsim
    278: 000a2423  sw           x0, 8(x20)  # cfg[66] (bank 0) (undocumented index) · 0xffef0108; write 0x00000000; cfg[66] (bank 0) · fields not in ttsim
    27c: 000a2623  sw           x0, 12(x20)  # cfg[67] (bank 0) (undocumented index) · 0xffef010c; write 0x00000000; cfg[67] (bank 0) · fields not in ttsim
    280: 02500a93  addi         x21, x0, 37  # x21 = 0x00000025
    284: 035a2023  sw           x21, 32(x20)  # cfg[72] (bank 0) · THCON_SEC0_REG2_Out_data_format, THCON_SEC0_REG2_Throttle_mode, THCON_SEC0_REG2_Context_count, THCON_SEC0_REG2_Haloize_mode, THCON_SEC0_REG2_Tileize_mode, THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC0_REG2_Unpack_If_Sel, THCON_SEC0_REG2_Upsample_rate, THCON_SEC0_REG2_Ovrd_data_format, THCON_SEC0_REG2_Upsample_and_interleave, THCON_SEC0_REG2_Shift_amount_cntx0, THCON_SEC0_REG2_Shift_amount_cntx1, THCON_SEC0_REG2_Shift_amount_cntx2, THCON_SEC0_REG2_Shift_amount_cntx3 · 0xffef0120; write 0x00000025; cfg[72] (bank 0); THCON_SEC0_REG2_Out_data_format = 5; THCON_SEC0_REG2_Throttle_mode = 2; THCON_SEC0_REG2_Context_count = 0; THCON_SEC0_REG2_Haloize_mode = 0; THCON_SEC0_REG2_Tileize_mode = 0; THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC0_REG2_Unpack_If_Sel = 0; THCON_SEC0_REG2_Upsample_rate = 0; THCON_SEC0_REG2_Ovrd_data_format = 0; THCON_SEC0_REG2_Upsample_and_interleave = 0; THCON_SEC0_REG2_Shift_amount_cntx0 = 0; THCON_SEC0_REG2_Shift_amount_cntx1 = 0; THCON_SEC0_REG2_Shift_amount_cntx2 = 0; THCON_SEC0_REG2_Shift_amount_cntx3 = 0
    288: 00300a93  addi         x21, x0, 3  # x21 = 0x00000003
    28c: 035a2223  sw           x21, 36(x20)  # cfg[73] (bank 0) · THCON_SEC0_REG2_Disable_zero_compress_cntx0, THCON_SEC0_REG2_Disable_zero_compress_cntx1, THCON_SEC0_REG2_Disable_zero_compress_cntx2, THCON_SEC0_REG2_Disable_zero_compress_cntx3, THCON_SEC0_REG2_Unpack_if_sel_cntx0, THCON_SEC0_REG2_Unpack_if_sel_cntx1, THCON_SEC0_REG2_Unpack_if_sel_cntx2, THCON_SEC0_REG2_Unpack_if_sel_cntx3, THCON_SEC0_REG2_Force_shared_exp, THCON_SEC0_REG2_Context_count_non_log2, THCON_SEC0_REG2_Context_count_non_log2_en, THCON_SEC0_REG2_Disable_zero_compress_cntx4, THCON_SEC0_REG2_Disable_zero_compress_cntx5, THCON_SEC0_REG2_Disable_zero_compress_cntx6, THCON_SEC0_REG2_Disable_zero_compress_cntx7, THCON_SEC0_REG2_Unpack_if_sel_cntx4, THCON_SEC0_REG2_Unpack_if_sel_cntx5, THCON_SEC0_REG2_Unpack_if_sel_cntx6, THCON_SEC0_REG2_Unpack_if_sel_cntx7, THCON_SEC0_REG2_Metadata_x_end · 0xffef0124; write 0x00000003; cfg[73] (bank 0); THCON_SEC0_REG2_Disable_zero_compress_cntx0 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx1 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx2 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx3 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx0 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx1 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx2 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx3 = 0; THCON_SEC0_REG2_Force_shared_exp = 0; THCON_SEC0_REG2_Context_count_non_log2 = 0; THCON_SEC0_REG2_Context_count_non_log2_en = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx4 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx5 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx6 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx7 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx4 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx5 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx6 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx7 = 0; THCON_SEC0_REG2_Metadata_x_end = 0
    290: 020a2423  sw           x0, 40(x20)  # cfg[74] (bank 0) · THCON_SEC0_REG2_Unpack_limit_address · 0xffef0128; write 0x00000000; cfg[74] (bank 0); THCON_SEC0_REG2_Unpack_limit_address = 0
    294: 020a2623  sw           x0, 44(x20)  # cfg[75] (bank 0) · THCON_SEC0_REG2_Unpack_fifo_size · 0xffef012c; write 0x00000000; cfg[75] (bank 0); THCON_SEC0_REG2_Unpack_fifo_size = 0
    298: fa0a2823  sw           x0, -80(x20)  # cfg[44] (bank 0) · UNP0_ADDR_CTRL_XY_REG_0_Xstride, UNP0_ADDR_CTRL_XY_REG_0_Ystride · 0xffef00b0; write 0x00000000; cfg[44] (bank 0); UNP0_ADDR_CTRL_XY_REG_0_Xstride = 0; UNP0_ADDR_CTRL_XY_REG_0_Ystride = 0
    29c: fa0a2a23  sw           x0, -76(x20)  # cfg[45] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_0_Zstride, UNP0_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef00b4; write 0x00000000; cfg[45] (bank 0); UNP0_ADDR_CTRL_ZW_REG_0_Zstride = 0; UNP0_ADDR_CTRL_ZW_REG_0_Wstride = 0
    2a0: 00200ab7  lui          x21, 0x00200  # x21 = 0x00200000
    2a4: 002a8a93  addi         x21, x21, 2  # x21 = 0x00200002
    2a8: ff5a2023  sw           x21, -32(x20)  # cfg[56] (bank 0) · UNP0_ADDR_CTRL_XY_REG_1_Xstride, UNP0_ADDR_CTRL_XY_REG_1_Ystride · 0xffef00e0; write 0x00200002; cfg[56] (bank 0); UNP0_ADDR_CTRL_XY_REG_1_Xstride = 2; UNP0_ADDR_CTRL_XY_REG_1_Ystride = 32
    2ac: 20000a93  addi         x21, x0, 512  # x21 = 0x00000200
    2b0: ff5a2223  sw           x21, -28(x20)  # cfg[57] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_1_Zstride, UNP0_ADDR_CTRL_ZW_REG_1_Wstride · 0xffef00e4; write 0x00000200; cfg[57] (bank 0); UNP0_ADDR_CTRL_ZW_REG_1_Zstride = 512; UNP0_ADDR_CTRL_ZW_REG_1_Wstride = 0
    2b4: fc0a2023  sw           x0, -64(x20)  # cfg[48] (bank 0) · UNP0_ADDR_BASE_REG_0_Base · 0xffef00c0; write 0x00000000; cfg[48] (bank 0); UNP0_ADDR_BASE_REG_0_Base = 0
    2b8: fc0a2223  sw           x0, -60(x20)  # cfg[49] (bank 0) · UNP0_ADDR_BASE_REG_1_Base · 0xffef00c4; write 0x00000000; cfg[49] (bank 0); UNP0_ADDR_BASE_REG_1_Base = 0
    2bc: 10000a93  addi         x21, x0, 256  # x21 = 0x00000100
    2c0: fd5a2423  sw           x21, -56(x20)  # cfg[50] (bank 0) · UNP0_FORCED_SHARED_EXP_shared_exp, UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr · 0xffef00c8; write 0x00000100; cfg[50] (bank 0); UNP0_FORCED_SHARED_EXP_shared_exp = 0; UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr = 1
    2c4: fc0a2a23  sw           x0, -44(x20)  # cfg[53] (bank 0) · UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val · 0xffef00d4; write 0x00000000; cfg[53] (bank 0); UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val = 0
    2c8: 00400ab7  lui          x21, 0x00400  # x21 = 0x00400000
    2cc: 040a8a93  addi         x21, x21, 64  # x21 = 0x00400040
    2d0: 055a2823  sw           x21, 80(x20)  # cfg[84] (bank 0) · THCON_SEC0_REG5_Dest_cntx0_address, THCON_SEC0_REG5_Dest_cntx1_address · 0xffef0150; write 0x00400040; cfg[84] (bank 0); THCON_SEC0_REG5_Dest_cntx0_address = 64; THCON_SEC0_REG5_Dest_cntx1_address = 64
    2d4: 01000ab7  lui          x21, 0x01000  # x21 = 0x01000000
    2d8: 100a8a93  addi         x21, x21, 256  # x21 = 0x01000100
    2dc: 055a2c23  sw           x21, 88(x20)  # cfg[86] (bank 0) · THCON_SEC0_REG5_Tile_x_dim_cntx0, THCON_SEC0_REG5_Tile_x_dim_cntx1 · 0xffef0158; write 0x01000100; cfg[86] (bank 0); THCON_SEC0_REG5_Tile_x_dim_cntx0 = 256; THCON_SEC0_REG5_Tile_x_dim_cntx1 = 256
    2e0: 060a2823  sw           x0, 112(x20)  # cfg[92] (bank 0) · THCON_SEC0_REG7_Offset_address, THCON_SEC0_REG7_Unpack_data_format_cntx0, THCON_SEC0_REG7_Unpack_out_data_format_cntx0, THCON_SEC0_REG7_Unpack_data_format_cntx4, THCON_SEC0_REG7_Unpack_out_data_format_cntx4 · 0xffef0170; write 0x00000000; cfg[92] (bank 0); THCON_SEC0_REG7_Offset_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx4 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx4 = 0
    2e4: 060a2a23  sw           x0, 116(x20)  # cfg[93] (bank 0) · THCON_SEC0_REG7_Offset_cntx1_address, THCON_SEC0_REG7_Unpack_data_format_cntx1, THCON_SEC0_REG7_Unpack_out_data_format_cntx1, THCON_SEC0_REG7_Unpack_data_format_cntx5, THCON_SEC0_REG7_Unpack_out_data_format_cntx5 · 0xffef0174; write 0x00000000; cfg[93] (bank 0); THCON_SEC0_REG7_Offset_cntx1_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx5 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx5 = 0
    2e8: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    2ec: 838a8a93  addi         x21, x21, -1992  # x21 = 0xffb00838 · riscv_local_mem + 0x838
    2f0: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x838 · 0xffb00838
    2f4: 004a5a13  srli         x20, x20, 4
    2f8: fffa0a13  addi         x20, x20, -1
    2fc: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    300: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    304: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    308: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    30c: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    310: c8140012  SETC16       setc16_reg=5, setc16_value=4  # thread_cfg[5] (current thread); SRCA_SET_Base = 0; SRCA_SET_SetOvrdWithAddr = 1
    314: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    318: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_31c:
    31c: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    320: 0feafa93  andi         x21, x21, 254
    324: 000a8663  beq          x21, x0, 0x00000330  # target 0x00000330
    328: 0ff0000f  fence        0xf, 0xf
    32c: ff1ff06f  jal          x0, 0x0000031c  # target 0x0000031c
loc_330:
    330: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    334: d50001de  RMWCIB2      Mask=64, Data=0, CfgRegAddr=119  # cfg[119] (current thread StateID); THCON_SEC1_REG1_Unp_LF8_4b_exp = 0
    338: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    33c: 1c0a0a13  addi         x20, x20, 448  # x20 = 0xffef01c0 · cfg[112] (bank 0) · THCON_SEC1_REG0_TileDescriptor
    340: 01000ab7  lui          x21, 0x01000  # x21 = 0x01000000
    344: 010a8a93  addi         x21, x21, 16  # x21 = 0x01000010
    348: 015a2023  sw           x21, 0(x20)  # cfg[112] (bank 0) · THCON_SEC1_REG0_TileDescriptor · 0xffef01c0; write 0x01000010; cfg[112] (bank 0); THCON_SEC1_REG0_TileDescriptor = 16777232
    34c: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
    350: 001a8a93  addi         x21, x21, 1  # x21 = 0x00040001
    354: 015a2223  sw           x21, 4(x20)  # cfg[113] (bank 0) (undocumented index) · 0xffef01c4; write 0x00040001; cfg[113] (bank 0) · fields not in ttsim
    358: 000a2423  sw           x0, 8(x20)  # cfg[114] (bank 0) (undocumented index) · 0xffef01c8; write 0x00000000; cfg[114] (bank 0) · fields not in ttsim
    35c: 000a2623  sw           x0, 12(x20)  # cfg[115] (bank 0) (undocumented index) · 0xffef01cc; write 0x00000000; cfg[115] (bank 0) · fields not in ttsim
    360: 02500a93  addi         x21, x0, 37  # x21 = 0x00000025
    364: 035a2023  sw           x21, 32(x20)  # cfg[120] (bank 0) · THCON_SEC1_REG2_Out_data_format, THCON_SEC1_REG2_Throttle_mode, THCON_SEC1_REG2_Context_count, THCON_SEC1_REG2_Haloize_mode, THCON_SEC1_REG2_Tileize_mode, THCON_SEC1_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC1_REG2_Unpack_If_Sel, THCON_SEC1_REG2_Upsample_rate, THCON_SEC1_REG2_Ovrd_data_format, THCON_SEC1_REG2_Upsample_and_interleave, THCON_SEC1_REG2_Shift_amount_cntx0, THCON_SEC1_REG2_Shift_amount_cntx1, THCON_SEC1_REG2_Shift_amount_cntx2, THCON_SEC1_REG2_Shift_amount_cntx3 · 0xffef01e0; write 0x00000025; cfg[120] (bank 0); THCON_SEC1_REG2_Out_data_format = 5; THCON_SEC1_REG2_Throttle_mode = 2; THCON_SEC1_REG2_Context_count = 0; THCON_SEC1_REG2_Haloize_mode = 0; THCON_SEC1_REG2_Tileize_mode = 0; THCON_SEC1_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC1_REG2_Unpack_If_Sel = 0; THCON_SEC1_REG2_Upsample_rate = 0; THCON_SEC1_REG2_Ovrd_data_format = 0; THCON_SEC1_REG2_Upsample_and_interleave = 0; THCON_SEC1_REG2_Shift_amount_cntx0 = 0; THCON_SEC1_REG2_Shift_amount_cntx1 = 0; THCON_SEC1_REG2_Shift_amount_cntx2 = 0; THCON_SEC1_REG2_Shift_amount_cntx3 = 0
    368: 00300a93  addi         x21, x0, 3  # x21 = 0x00000003
    36c: 035a2223  sw           x21, 36(x20)  # cfg[121] (bank 0) · THCON_SEC1_REG2_Disable_zero_compress_cntx0, THCON_SEC1_REG2_Disable_zero_compress_cntx1, THCON_SEC1_REG2_Disable_zero_compress_cntx2, THCON_SEC1_REG2_Disable_zero_compress_cntx3, THCON_SEC1_REG2_Unpack_if_sel_cntx0, THCON_SEC1_REG2_Unpack_if_sel_cntx1, THCON_SEC1_REG2_Unpack_if_sel_cntx2, THCON_SEC1_REG2_Unpack_if_sel_cntx3, THCON_SEC1_REG2_Force_shared_exp, THCON_SEC1_REG2_Context_count_non_log2, THCON_SEC1_REG2_Context_count_non_log2_en, THCON_SEC1_REG2_Disable_zero_compress_cntx4, THCON_SEC1_REG2_Disable_zero_compress_cntx5, THCON_SEC1_REG2_Disable_zero_compress_cntx6, THCON_SEC1_REG2_Disable_zero_compress_cntx7, THCON_SEC1_REG2_Unpack_if_sel_cntx4, THCON_SEC1_REG2_Unpack_if_sel_cntx5, THCON_SEC1_REG2_Unpack_if_sel_cntx6, THCON_SEC1_REG2_Unpack_if_sel_cntx7, THCON_SEC1_REG2_Metadata_x_end · 0xffef01e4; write 0x00000003; cfg[121] (bank 0); THCON_SEC1_REG2_Disable_zero_compress_cntx0 = 1; THCON_SEC1_REG2_Disable_zero_compress_cntx1 = 1; THCON_SEC1_REG2_Disable_zero_compress_cntx2 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx3 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx0 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx1 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx2 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx3 = 0; THCON_SEC1_REG2_Force_shared_exp = 0; THCON_SEC1_REG2_Context_count_non_log2 = 0; THCON_SEC1_REG2_Context_count_non_log2_en = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx4 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx5 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx6 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx7 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx4 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx5 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx6 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx7 = 0; THCON_SEC1_REG2_Metadata_x_end = 0
    370: 020a2423  sw           x0, 40(x20)  # cfg[122] (bank 0) · THCON_SEC1_REG2_Unpack_limit_address · 0xffef01e8; write 0x00000000; cfg[122] (bank 0); THCON_SEC1_REG2_Unpack_limit_address = 0
    374: 020a2623  sw           x0, 44(x20)  # cfg[123] (bank 0) · THCON_SEC1_REG2_Unpack_fifo_size · 0xffef01ec; write 0x00000000; cfg[123] (bank 0); THCON_SEC1_REG2_Unpack_fifo_size = 0
    378: ee0a2c23  sw           x0, -264(x20)  # cfg[46] (bank 0) · UNP1_ADDR_CTRL_XY_REG_0_Xstride, UNP1_ADDR_CTRL_XY_REG_0_Ystride · 0xffef00b8; write 0x00000000; cfg[46] (bank 0); UNP1_ADDR_CTRL_XY_REG_0_Xstride = 0; UNP1_ADDR_CTRL_XY_REG_0_Ystride = 0
    37c: ee0a2e23  sw           x0, -260(x20)  # cfg[47] (bank 0) · UNP1_ADDR_CTRL_ZW_REG_0_Zstride, UNP1_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef00bc; write 0x00000000; cfg[47] (bank 0); UNP1_ADDR_CTRL_ZW_REG_0_Zstride = 0; UNP1_ADDR_CTRL_ZW_REG_0_Wstride = 0
    380: 00200ab7  lui          x21, 0x00200  # x21 = 0x00200000
    384: 002a8a93  addi         x21, x21, 2  # x21 = 0x00200002
    388: f35a2423  sw           x21, -216(x20)  # cfg[58] (bank 0) · UNP1_ADDR_CTRL_XY_REG_1_Xstride, UNP1_ADDR_CTRL_XY_REG_1_Ystride · 0xffef00e8; write 0x00200002; cfg[58] (bank 0); UNP1_ADDR_CTRL_XY_REG_1_Xstride = 2; UNP1_ADDR_CTRL_XY_REG_1_Ystride = 32
    38c: 20000a93  addi         x21, x0, 512  # x21 = 0x00000200
    390: f35a2623  sw           x21, -212(x20)  # cfg[59] (bank 0) · UNP1_ADDR_CTRL_ZW_REG_1_Zstride, UNP1_ADDR_CTRL_ZW_REG_1_Wstride · 0xffef00ec; write 0x00000200; cfg[59] (bank 0); UNP1_ADDR_CTRL_ZW_REG_1_Zstride = 512; UNP1_ADDR_CTRL_ZW_REG_1_Wstride = 0
    394: f20a2823  sw           x0, -208(x20)  # cfg[60] (bank 0) · UNP1_ADDR_BASE_REG_0_Base · 0xffef00f0; write 0x00000000; cfg[60] (bank 0); UNP1_ADDR_BASE_REG_0_Base = 0
    398: f20a2a23  sw           x0, -204(x20)  # cfg[61] (bank 0) · UNP1_ADDR_BASE_REG_1_Base · 0xffef00f4; write 0x00000000; cfg[61] (bank 0); UNP1_ADDR_BASE_REG_1_Base = 0
    39c: f20a2c23  sw           x0, -200(x20)  # cfg[62] (bank 0) · UNP1_FORCED_SHARED_EXP_shared_exp, UNP1_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr · 0xffef00f8; write 0x00000000; cfg[62] (bank 0); UNP1_FORCED_SHARED_EXP_shared_exp = 0; UNP1_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr = 0
    3a0: f20a2e23  sw           x0, -196(x20)  # cfg[63] (bank 0) · UNP1_NOP_REG_CLR_VAL_nop_reg_clr_val · 0xffef00fc; write 0x00000000; cfg[63] (bank 0); UNP1_NOP_REG_CLR_VAL_nop_reg_clr_val = 0
    3a4: 040a2823  sw           x0, 80(x20)  # cfg[132] (bank 0) · THCON_SEC1_REG5_Dest_cntx0_address, THCON_SEC1_REG5_Dest_cntx1_address · 0xffef0210; write 0x00000000; cfg[132] (bank 0); THCON_SEC1_REG5_Dest_cntx0_address = 0; THCON_SEC1_REG5_Dest_cntx1_address = 0
    3a8: 01000ab7  lui          x21, 0x01000  # x21 = 0x01000000
    3ac: 100a8a93  addi         x21, x21, 256  # x21 = 0x01000100
    3b0: 055a2c23  sw           x21, 88(x20)  # cfg[134] (bank 0) · THCON_SEC1_REG5_Tile_x_dim_cntx0, THCON_SEC1_REG5_Tile_x_dim_cntx1 · 0xffef0218; write 0x01000100; cfg[134] (bank 0); THCON_SEC1_REG5_Tile_x_dim_cntx0 = 256; THCON_SEC1_REG5_Tile_x_dim_cntx1 = 256
    3b4: 060a2823  sw           x0, 112(x20)  # cfg[140] (bank 0) · THCON_SEC1_REG7_Offset_address, THCON_SEC1_REG7_Unpack_data_format_cntx0, THCON_SEC1_REG7_Unpack_out_data_format_cntx0, THCON_SEC1_REG7_Unpack_data_format_cntx4, THCON_SEC1_REG7_Unpack_out_data_format_cntx4 · 0xffef0230; write 0x00000000; cfg[140] (bank 0); THCON_SEC1_REG7_Offset_address = 0; THCON_SEC1_REG7_Unpack_data_format_cntx0 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx0 = 0; THCON_SEC1_REG7_Unpack_data_format_cntx4 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx4 = 0
    3b8: 060a2a23  sw           x0, 116(x20)  # cfg[141] (bank 0) · THCON_SEC1_REG7_Offset_cntx1_address, THCON_SEC1_REG7_Unpack_data_format_cntx1, THCON_SEC1_REG7_Unpack_out_data_format_cntx1, THCON_SEC1_REG7_Unpack_data_format_cntx5, THCON_SEC1_REG7_Unpack_out_data_format_cntx5 · 0xffef0234; write 0x00000000; cfg[141] (bank 0); THCON_SEC1_REG7_Offset_cntx1_address = 0; THCON_SEC1_REG7_Unpack_data_format_cntx1 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx1 = 0; THCON_SEC1_REG7_Unpack_data_format_cntx5 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx5 = 0
    3bc: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    3c0: 840a8a93  addi         x21, x21, -1984  # x21 = 0xffb00840 · riscv_local_mem + 0x840
    3c4: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x840 · 0xffb00840
    3c8: 004a5a13  srli         x20, x20, 4
    3cc: fffa0a13  addi         x20, x20, -1
    3d0: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    3d4: 1f0a8a93  addi         x21, x21, 496  # x21 = 0xffef01f0 · cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address
    3d8: 014aa023  sw           x20, 0(x21)  # cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address · 0xffef01f0; write runtime value; cfg[124] (bank 0); THCON_SEC1_REG3_Base_address = runtime
    3dc: 014aa223  sw           x20, 4(x21)  # cfg[125] (bank 0) · THCON_SEC1_REG3_Base_cntx1_address · 0xffef01f4; write runtime value; cfg[125] (bank 0); THCON_SEC1_REG3_Base_cntx1_address = runtime
    3e0: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    3e4: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    3e8: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    3ec: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    3f0: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    3f4: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    3f8: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    3fc: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    400: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    404: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    408: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    40c: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    410: 01507033  and          x0, x0, x21
    414: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    418: 00400a93  addi         x21, x0, 4  # x21 = 0x00000004
    41c: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000004
    420: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
    424: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000001
    428: 42008ab7  lui          x21, 0x42008  # x21 = 0x42008000
    42c: 0c1a8a93  addi         x21, x21, 193  # x21 = 0x420080c1
    430: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x420080c1; MOP template instruction · UNPACR Unpack_block_selection=0, AddrMode=1, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    434: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    438: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x02000000; MOP template instruction · NOP 
    43c: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP 
    440: 42808ab7  lui          x21, 0x42808  # x21 = 0x42808000
    444: 0c1a8a93  addi         x21, x21, 193  # x21 = 0x428080c1
    448: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x428080c1; MOP template instruction · UNPACR Unpack_block_selection=1, AddrMode=1, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    44c: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    450: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP 
    454: 42808ab7  lui          x21, 0x42808  # x21 = 0x42808000
    458: 0c1a8a93  addi         x21, x21, 193  # x21 = 0x428080c1
    45c: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x428080c1; MOP template instruction · UNPACR Unpack_block_selection=1, AddrMode=1, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    460: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x428080c1; MOP template instruction · UNPACR Unpack_block_selection=1, AddrMode=1, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    464: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    468: 83cc0c13  addi         x24, x24, -1988  # x24 = 0xffb0083c · riscv_local_mem + 0x83c
    46c: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x83c · 0xffb0083c
    470: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_474:
    474: ffb4dc37  lui          x24, 0xffb4d  # x24 = 0xffb4d000
    478: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb4d028
    47c: 000c5a83  lhu          x21, 0(x24)  # 0xffb4d028
    480: 414a8b33  sub          x22, x21, x20
    484: 010b1b13  slli         x22, x22, 16
    488: 010b5b13  srli         x22, x22, 16
    48c: 017b7663  bgeu         x22, x23, 0x00000498  # target 0x00000498
    490: 0ff0000f  fence        0xf, 0xf
    494: fe1ff06f  jal          x0, 0x00000474  # target 0x00000474
loc_498:
    498: 0ff0000f  fence        0xf, 0xf
    49c: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    4a0: 844c0c13  addi         x24, x24, -1980  # x24 = 0xffb00844 · riscv_local_mem + 0x844
    4a4: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x844 · 0xffb00844
    4a8: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_4ac:
    4ac: ffb4cc37  lui          x24, 0xffb4c  # x24 = 0xffb4c000
    4b0: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb4c028
    4b4: 000c5a83  lhu          x21, 0(x24)  # 0xffb4c028
    4b8: 414a8b33  sub          x22, x21, x20
    4bc: 010b1b13  slli         x22, x22, 16
    4c0: 010b5b13  srli         x22, x22, 16
    4c4: 017b7663  bgeu         x22, x23, 0x000004d0  # target 0x000004d0
    4c8: 0ff0000f  fence        0xf, 0xf
    4cc: fe1ff06f  jal          x0, 0x000004ac  # target 0x000004ac
loc_4d0:
    4d0: 0ff0000f  fence        0xf, 0xf
    4d4: 88100182  STALLWAIT    stall_res=8, wait_res=96  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR | Wait.SRCB_CLR
    4d8: 788ff001  SETADCXX     CntSetMask=1, x_end2=255, x_start=0
    4dc: 790ff001  SETADCXX     CntSetMask=2, x_end2=255, x_start=0
    4e0: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    4e4: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    4e8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    4ec: 8810001a  STALLWAIT    stall_res=8, wait_res=6  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0 | Wait.UNPACK1
    4f0: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    4f4: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    4f8: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    4fc: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    500: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    504: 01507033  and          x0, x0, x21
    508: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    50c: 83ca8a93  addi         x21, x21, -1988  # x21 = 0xffb0083c · riscv_local_mem + 0x83c
    510: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x83c · 0xffb0083c
    514: 001a0a13  addi         x20, x20, 1
    518: 010a1a13  slli         x20, x20, 16
    51c: 010a5a13  srli         x20, x20, 16
    520: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    524: 83ca8a93  addi         x21, x21, -1988  # x21 = 0xffb0083c · riscv_local_mem + 0x83c
    528: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x83c · 0xffb0083c; write runtime value
    52c: ffb4dab7  lui          x21, 0xffb4d  # x21 = 0xffb4d000
    530: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb4d020
    534: 014aa023  sw           x20, 0(x21)  # 0xffb4d020; write runtime value
    538: 0ff0000f  fence        0xf, 0xf
    53c: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    540: 838c0c13  addi         x24, x24, -1992  # x24 = 0xffb00838 · riscv_local_mem + 0x838
    544: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x838 · 0xffb00838
    548: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    54c: 015a0a33  add          x20, x20, x21
    550: 0009eb37  lui          x22, 0x0009e  # x22 = 0x0009e000
    554: 016a6663  bltu         x20, x22, 0x00000560  # target 0x00000560
    558: 00001bb7  lui          x23, 0x00001  # x23 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    55c: 417a0a33  sub          x20, x20, x23
loc_560:
    560: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    564: 838c0c13  addi         x24, x24, -1992  # x24 = 0xffb00838 · riscv_local_mem + 0x838
    568: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x838 · 0xffb00838; write runtime value
    56c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    570: 844a8a93  addi         x21, x21, -1980  # x21 = 0xffb00844 · riscv_local_mem + 0x844
    574: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x844 · 0xffb00844
    578: 001a0a13  addi         x20, x20, 1
    57c: 010a1a13  slli         x20, x20, 16
    580: 010a5a13  srli         x20, x20, 16
    584: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    588: 844a8a93  addi         x21, x21, -1980  # x21 = 0xffb00844 · riscv_local_mem + 0x844
    58c: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x844 · 0xffb00844; write runtime value
    590: ffb4cab7  lui          x21, 0xffb4c  # x21 = 0xffb4c000
    594: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb4c020
    598: 014aa023  sw           x20, 0(x21)  # 0xffb4c020; write runtime value
    59c: 0ff0000f  fence        0xf, 0xf
    5a0: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    5a4: 840c0c13  addi         x24, x24, -1984  # x24 = 0xffb00840 · riscv_local_mem + 0x840
    5a8: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x840 · 0xffb00840
    5ac: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5b0: 015a0a33  add          x20, x20, x21
    5b4: 0009db37  lui          x22, 0x0009d  # x22 = 0x0009d000
    5b8: 016a6663  bltu         x20, x22, 0x000005c4  # target 0x000005c4
    5bc: 00001bb7  lui          x23, 0x00001  # x23 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5c0: 417a0a33  sub          x20, x20, x23
loc_5c4:
    5c4: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    5c8: 840c0c13  addi         x24, x24, -1984  # x24 = 0xffb00840 · riscv_local_mem + 0x840
    5cc: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x840 · 0xffb00840; write runtime value
loc_5d0:
    5d0: ffe80437  lui          x8, 0xffe80  # x8 = 0xffe80000 · tensix_pc_buf + 0x0
    5d4: 03440413  addi         x8, x8, 52  # x8 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_5d8:
    5d8: 00042483  lw           x9, 0(x8)  # UNPACK_CONFIG_SYNC · 0xffe80034
    5dc: 0fe4f493  andi         x9, x9, 254
    5e0: 00048663  beq          x9, x0, 0x000005ec  # target 0x000005ec
    5e4: 0ff0000f  fence        0xf, 0xf
    5e8: ff1ff06f  jal          x0, 0x000005d8  # target 0x000005d8
loc_5ec:
    5ec: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    5f0: d500011e  RMWCIB2      Mask=64, Data=0, CfgRegAddr=71  # cfg[71] (current thread StateID); THCON_SEC0_REG1_Unp_LF8_4b_exp = 0
    5f4: ffef0437  lui          x8, 0xffef0  # x8 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    5f8: 10040413  addi         x8, x8, 256  # x8 = 0xffef0100 · cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor
    5fc: 01500493  addi         x9, x0, 21  # x9 = 0x00000015
    600: 00942023  sw           x9, 0(x8)  # cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor · 0xffef0100; write 0x00000015; cfg[64] (bank 0); THCON_SEC0_REG0_TileDescriptor = 21
    604: 000404b7  lui          x9, 0x00040  # x9 = 0x00040000
    608: 00148493  addi         x9, x9, 1  # x9 = 0x00040001
    60c: 00942223  sw           x9, 4(x8)  # cfg[65] (bank 0) (undocumented index) · 0xffef0104; write 0x00040001; cfg[65] (bank 0) · fields not in ttsim
    610: 00042423  sw           x0, 8(x8)  # cfg[66] (bank 0) (undocumented index) · 0xffef0108; write 0x00000000; cfg[66] (bank 0) · fields not in ttsim
    614: 00042623  sw           x0, 12(x8)  # cfg[67] (bank 0) (undocumented index) · 0xffef010c; write 0x00000000; cfg[67] (bank 0) · fields not in ttsim
    618: 02500493  addi         x9, x0, 37  # x9 = 0x00000025
    61c: 02942023  sw           x9, 32(x8)  # cfg[72] (bank 0) · THCON_SEC0_REG2_Out_data_format, THCON_SEC0_REG2_Throttle_mode, THCON_SEC0_REG2_Context_count, THCON_SEC0_REG2_Haloize_mode, THCON_SEC0_REG2_Tileize_mode, THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC0_REG2_Unpack_If_Sel, THCON_SEC0_REG2_Upsample_rate, THCON_SEC0_REG2_Ovrd_data_format, THCON_SEC0_REG2_Upsample_and_interleave, THCON_SEC0_REG2_Shift_amount_cntx0, THCON_SEC0_REG2_Shift_amount_cntx1, THCON_SEC0_REG2_Shift_amount_cntx2, THCON_SEC0_REG2_Shift_amount_cntx3 · 0xffef0120; write 0x00000025; cfg[72] (bank 0); THCON_SEC0_REG2_Out_data_format = 5; THCON_SEC0_REG2_Throttle_mode = 2; THCON_SEC0_REG2_Context_count = 0; THCON_SEC0_REG2_Haloize_mode = 0; THCON_SEC0_REG2_Tileize_mode = 0; THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC0_REG2_Unpack_If_Sel = 0; THCON_SEC0_REG2_Upsample_rate = 0; THCON_SEC0_REG2_Ovrd_data_format = 0; THCON_SEC0_REG2_Upsample_and_interleave = 0; THCON_SEC0_REG2_Shift_amount_cntx0 = 0; THCON_SEC0_REG2_Shift_amount_cntx1 = 0; THCON_SEC0_REG2_Shift_amount_cntx2 = 0; THCON_SEC0_REG2_Shift_amount_cntx3 = 0
    620: 00300493  addi         x9, x0, 3  # x9 = 0x00000003
    624: 02942223  sw           x9, 36(x8)  # cfg[73] (bank 0) · THCON_SEC0_REG2_Disable_zero_compress_cntx0, THCON_SEC0_REG2_Disable_zero_compress_cntx1, THCON_SEC0_REG2_Disable_zero_compress_cntx2, THCON_SEC0_REG2_Disable_zero_compress_cntx3, THCON_SEC0_REG2_Unpack_if_sel_cntx0, THCON_SEC0_REG2_Unpack_if_sel_cntx1, THCON_SEC0_REG2_Unpack_if_sel_cntx2, THCON_SEC0_REG2_Unpack_if_sel_cntx3, THCON_SEC0_REG2_Force_shared_exp, THCON_SEC0_REG2_Context_count_non_log2, THCON_SEC0_REG2_Context_count_non_log2_en, THCON_SEC0_REG2_Disable_zero_compress_cntx4, THCON_SEC0_REG2_Disable_zero_compress_cntx5, THCON_SEC0_REG2_Disable_zero_compress_cntx6, THCON_SEC0_REG2_Disable_zero_compress_cntx7, THCON_SEC0_REG2_Unpack_if_sel_cntx4, THCON_SEC0_REG2_Unpack_if_sel_cntx5, THCON_SEC0_REG2_Unpack_if_sel_cntx6, THCON_SEC0_REG2_Unpack_if_sel_cntx7, THCON_SEC0_REG2_Metadata_x_end · 0xffef0124; write 0x00000003; cfg[73] (bank 0); THCON_SEC0_REG2_Disable_zero_compress_cntx0 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx1 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx2 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx3 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx0 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx1 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx2 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx3 = 0; THCON_SEC0_REG2_Force_shared_exp = 0; THCON_SEC0_REG2_Context_count_non_log2 = 0; THCON_SEC0_REG2_Context_count_non_log2_en = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx4 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx5 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx6 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx7 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx4 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx5 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx6 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx7 = 0; THCON_SEC0_REG2_Metadata_x_end = 0
    628: 02042423  sw           x0, 40(x8)  # cfg[74] (bank 0) · THCON_SEC0_REG2_Unpack_limit_address · 0xffef0128; write 0x00000000; cfg[74] (bank 0); THCON_SEC0_REG2_Unpack_limit_address = 0
    62c: 02042623  sw           x0, 44(x8)  # cfg[75] (bank 0) · THCON_SEC0_REG2_Unpack_fifo_size · 0xffef012c; write 0x00000000; cfg[75] (bank 0); THCON_SEC0_REG2_Unpack_fifo_size = 0
    630: fa042823  sw           x0, -80(x8)  # cfg[44] (bank 0) · UNP0_ADDR_CTRL_XY_REG_0_Xstride, UNP0_ADDR_CTRL_XY_REG_0_Ystride · 0xffef00b0; write 0x00000000; cfg[44] (bank 0); UNP0_ADDR_CTRL_XY_REG_0_Xstride = 0; UNP0_ADDR_CTRL_XY_REG_0_Ystride = 0
    634: fa042a23  sw           x0, -76(x8)  # cfg[45] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_0_Zstride, UNP0_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef00b4; write 0x00000000; cfg[45] (bank 0); UNP0_ADDR_CTRL_ZW_REG_0_Zstride = 0; UNP0_ADDR_CTRL_ZW_REG_0_Wstride = 0
    638: 002004b7  lui          x9, 0x00200  # x9 = 0x00200000
    63c: 00248493  addi         x9, x9, 2  # x9 = 0x00200002
    640: fe942023  sw           x9, -32(x8)  # cfg[56] (bank 0) · UNP0_ADDR_CTRL_XY_REG_1_Xstride, UNP0_ADDR_CTRL_XY_REG_1_Ystride · 0xffef00e0; write 0x00200002; cfg[56] (bank 0); UNP0_ADDR_CTRL_XY_REG_1_Xstride = 2; UNP0_ADDR_CTRL_XY_REG_1_Ystride = 32
    644: 20000493  addi         x9, x0, 512  # x9 = 0x00000200
    648: fe942223  sw           x9, -28(x8)  # cfg[57] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_1_Zstride, UNP0_ADDR_CTRL_ZW_REG_1_Wstride · 0xffef00e4; write 0x00000200; cfg[57] (bank 0); UNP0_ADDR_CTRL_ZW_REG_1_Zstride = 512; UNP0_ADDR_CTRL_ZW_REG_1_Wstride = 0
    64c: fc042023  sw           x0, -64(x8)  # cfg[48] (bank 0) · UNP0_ADDR_BASE_REG_0_Base · 0xffef00c0; write 0x00000000; cfg[48] (bank 0); UNP0_ADDR_BASE_REG_0_Base = 0
    650: fc042223  sw           x0, -60(x8)  # cfg[49] (bank 0) · UNP0_ADDR_BASE_REG_1_Base · 0xffef00c4; write 0x00000000; cfg[49] (bank 0); UNP0_ADDR_BASE_REG_1_Base = 0
    654: 10000493  addi         x9, x0, 256  # x9 = 0x00000100
    658: fc942423  sw           x9, -56(x8)  # cfg[50] (bank 0) · UNP0_FORCED_SHARED_EXP_shared_exp, UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr · 0xffef00c8; write 0x00000100; cfg[50] (bank 0); UNP0_FORCED_SHARED_EXP_shared_exp = 0; UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr = 1
    65c: fc042a23  sw           x0, -44(x8)  # cfg[53] (bank 0) · UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val · 0xffef00d4; write 0x00000000; cfg[53] (bank 0); UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val = 0
    660: 004004b7  lui          x9, 0x00400  # x9 = 0x00400000
    664: 04048493  addi         x9, x9, 64  # x9 = 0x00400040
    668: 04942823  sw           x9, 80(x8)  # cfg[84] (bank 0) · THCON_SEC0_REG5_Dest_cntx0_address, THCON_SEC0_REG5_Dest_cntx1_address · 0xffef0150; write 0x00400040; cfg[84] (bank 0); THCON_SEC0_REG5_Dest_cntx0_address = 64; THCON_SEC0_REG5_Dest_cntx1_address = 64
    66c: 010004b7  lui          x9, 0x01000  # x9 = 0x01000000
    670: 10048493  addi         x9, x9, 256  # x9 = 0x01000100
    674: 04942c23  sw           x9, 88(x8)  # cfg[86] (bank 0) · THCON_SEC0_REG5_Tile_x_dim_cntx0, THCON_SEC0_REG5_Tile_x_dim_cntx1 · 0xffef0158; write 0x01000100; cfg[86] (bank 0); THCON_SEC0_REG5_Tile_x_dim_cntx0 = 256; THCON_SEC0_REG5_Tile_x_dim_cntx1 = 256
    678: 06042823  sw           x0, 112(x8)  # cfg[92] (bank 0) · THCON_SEC0_REG7_Offset_address, THCON_SEC0_REG7_Unpack_data_format_cntx0, THCON_SEC0_REG7_Unpack_out_data_format_cntx0, THCON_SEC0_REG7_Unpack_data_format_cntx4, THCON_SEC0_REG7_Unpack_out_data_format_cntx4 · 0xffef0170; write 0x00000000; cfg[92] (bank 0); THCON_SEC0_REG7_Offset_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx4 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx4 = 0
    67c: 06042a23  sw           x0, 116(x8)  # cfg[93] (bank 0) · THCON_SEC0_REG7_Offset_cntx1_address, THCON_SEC0_REG7_Unpack_data_format_cntx1, THCON_SEC0_REG7_Unpack_out_data_format_cntx1, THCON_SEC0_REG7_Unpack_data_format_cntx5, THCON_SEC0_REG7_Unpack_out_data_format_cntx5 · 0xffef0174; write 0x00000000; cfg[93] (bank 0); THCON_SEC0_REG7_Offset_cntx1_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx5 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx5 = 0
    680: d50001de  RMWCIB2      Mask=64, Data=0, CfgRegAddr=119  # cfg[119] (current thread StateID); THCON_SEC1_REG1_Unp_LF8_4b_exp = 0
    684: ffef0437  lui          x8, 0xffef0  # x8 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    688: 1c040413  addi         x8, x8, 448  # x8 = 0xffef01c0 · cfg[112] (bank 0) · THCON_SEC1_REG0_TileDescriptor
    68c: 010004b7  lui          x9, 0x01000  # x9 = 0x01000000
    690: 01548493  addi         x9, x9, 21  # x9 = 0x01000015
    694: 00942023  sw           x9, 0(x8)  # cfg[112] (bank 0) · THCON_SEC1_REG0_TileDescriptor · 0xffef01c0; write 0x01000015; cfg[112] (bank 0); THCON_SEC1_REG0_TileDescriptor = 16777237
    698: 000404b7  lui          x9, 0x00040  # x9 = 0x00040000
    69c: 00148493  addi         x9, x9, 1  # x9 = 0x00040001
    6a0: 00942223  sw           x9, 4(x8)  # cfg[113] (bank 0) (undocumented index) · 0xffef01c4; write 0x00040001; cfg[113] (bank 0) · fields not in ttsim
    6a4: 00042423  sw           x0, 8(x8)  # cfg[114] (bank 0) (undocumented index) · 0xffef01c8; write 0x00000000; cfg[114] (bank 0) · fields not in ttsim
    6a8: 00042623  sw           x0, 12(x8)  # cfg[115] (bank 0) (undocumented index) · 0xffef01cc; write 0x00000000; cfg[115] (bank 0) · fields not in ttsim
    6ac: 02500493  addi         x9, x0, 37  # x9 = 0x00000025
    6b0: 02942023  sw           x9, 32(x8)  # cfg[120] (bank 0) · THCON_SEC1_REG2_Out_data_format, THCON_SEC1_REG2_Throttle_mode, THCON_SEC1_REG2_Context_count, THCON_SEC1_REG2_Haloize_mode, THCON_SEC1_REG2_Tileize_mode, THCON_SEC1_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC1_REG2_Unpack_If_Sel, THCON_SEC1_REG2_Upsample_rate, THCON_SEC1_REG2_Ovrd_data_format, THCON_SEC1_REG2_Upsample_and_interleave, THCON_SEC1_REG2_Shift_amount_cntx0, THCON_SEC1_REG2_Shift_amount_cntx1, THCON_SEC1_REG2_Shift_amount_cntx2, THCON_SEC1_REG2_Shift_amount_cntx3 · 0xffef01e0; write 0x00000025; cfg[120] (bank 0); THCON_SEC1_REG2_Out_data_format = 5; THCON_SEC1_REG2_Throttle_mode = 2; THCON_SEC1_REG2_Context_count = 0; THCON_SEC1_REG2_Haloize_mode = 0; THCON_SEC1_REG2_Tileize_mode = 0; THCON_SEC1_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC1_REG2_Unpack_If_Sel = 0; THCON_SEC1_REG2_Upsample_rate = 0; THCON_SEC1_REG2_Ovrd_data_format = 0; THCON_SEC1_REG2_Upsample_and_interleave = 0; THCON_SEC1_REG2_Shift_amount_cntx0 = 0; THCON_SEC1_REG2_Shift_amount_cntx1 = 0; THCON_SEC1_REG2_Shift_amount_cntx2 = 0; THCON_SEC1_REG2_Shift_amount_cntx3 = 0
    6b4: 00300493  addi         x9, x0, 3  # x9 = 0x00000003
    6b8: 02942223  sw           x9, 36(x8)  # cfg[121] (bank 0) · THCON_SEC1_REG2_Disable_zero_compress_cntx0, THCON_SEC1_REG2_Disable_zero_compress_cntx1, THCON_SEC1_REG2_Disable_zero_compress_cntx2, THCON_SEC1_REG2_Disable_zero_compress_cntx3, THCON_SEC1_REG2_Unpack_if_sel_cntx0, THCON_SEC1_REG2_Unpack_if_sel_cntx1, THCON_SEC1_REG2_Unpack_if_sel_cntx2, THCON_SEC1_REG2_Unpack_if_sel_cntx3, THCON_SEC1_REG2_Force_shared_exp, THCON_SEC1_REG2_Context_count_non_log2, THCON_SEC1_REG2_Context_count_non_log2_en, THCON_SEC1_REG2_Disable_zero_compress_cntx4, THCON_SEC1_REG2_Disable_zero_compress_cntx5, THCON_SEC1_REG2_Disable_zero_compress_cntx6, THCON_SEC1_REG2_Disable_zero_compress_cntx7, THCON_SEC1_REG2_Unpack_if_sel_cntx4, THCON_SEC1_REG2_Unpack_if_sel_cntx5, THCON_SEC1_REG2_Unpack_if_sel_cntx6, THCON_SEC1_REG2_Unpack_if_sel_cntx7, THCON_SEC1_REG2_Metadata_x_end · 0xffef01e4; write 0x00000003; cfg[121] (bank 0); THCON_SEC1_REG2_Disable_zero_compress_cntx0 = 1; THCON_SEC1_REG2_Disable_zero_compress_cntx1 = 1; THCON_SEC1_REG2_Disable_zero_compress_cntx2 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx3 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx0 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx1 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx2 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx3 = 0; THCON_SEC1_REG2_Force_shared_exp = 0; THCON_SEC1_REG2_Context_count_non_log2 = 0; THCON_SEC1_REG2_Context_count_non_log2_en = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx4 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx5 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx6 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx7 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx4 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx5 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx6 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx7 = 0; THCON_SEC1_REG2_Metadata_x_end = 0
    6bc: 02042423  sw           x0, 40(x8)  # cfg[122] (bank 0) · THCON_SEC1_REG2_Unpack_limit_address · 0xffef01e8; write 0x00000000; cfg[122] (bank 0); THCON_SEC1_REG2_Unpack_limit_address = 0
    6c0: 02042623  sw           x0, 44(x8)  # cfg[123] (bank 0) · THCON_SEC1_REG2_Unpack_fifo_size · 0xffef01ec; write 0x00000000; cfg[123] (bank 0); THCON_SEC1_REG2_Unpack_fifo_size = 0
    6c4: ee042c23  sw           x0, -264(x8)  # cfg[46] (bank 0) · UNP1_ADDR_CTRL_XY_REG_0_Xstride, UNP1_ADDR_CTRL_XY_REG_0_Ystride · 0xffef00b8; write 0x00000000; cfg[46] (bank 0); UNP1_ADDR_CTRL_XY_REG_0_Xstride = 0; UNP1_ADDR_CTRL_XY_REG_0_Ystride = 0
    6c8: ee042e23  sw           x0, -260(x8)  # cfg[47] (bank 0) · UNP1_ADDR_CTRL_ZW_REG_0_Zstride, UNP1_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef00bc; write 0x00000000; cfg[47] (bank 0); UNP1_ADDR_CTRL_ZW_REG_0_Zstride = 0; UNP1_ADDR_CTRL_ZW_REG_0_Wstride = 0
    6cc: 002004b7  lui          x9, 0x00200  # x9 = 0x00200000
    6d0: 00248493  addi         x9, x9, 2  # x9 = 0x00200002
    6d4: f2942423  sw           x9, -216(x8)  # cfg[58] (bank 0) · UNP1_ADDR_CTRL_XY_REG_1_Xstride, UNP1_ADDR_CTRL_XY_REG_1_Ystride · 0xffef00e8; write 0x00200002; cfg[58] (bank 0); UNP1_ADDR_CTRL_XY_REG_1_Xstride = 2; UNP1_ADDR_CTRL_XY_REG_1_Ystride = 32
    6d8: 20000493  addi         x9, x0, 512  # x9 = 0x00000200
    6dc: f2942623  sw           x9, -212(x8)  # cfg[59] (bank 0) · UNP1_ADDR_CTRL_ZW_REG_1_Zstride, UNP1_ADDR_CTRL_ZW_REG_1_Wstride · 0xffef00ec; write 0x00000200; cfg[59] (bank 0); UNP1_ADDR_CTRL_ZW_REG_1_Zstride = 512; UNP1_ADDR_CTRL_ZW_REG_1_Wstride = 0
    6e0: f2042823  sw           x0, -208(x8)  # cfg[60] (bank 0) · UNP1_ADDR_BASE_REG_0_Base · 0xffef00f0; write 0x00000000; cfg[60] (bank 0); UNP1_ADDR_BASE_REG_0_Base = 0
    6e4: f2042a23  sw           x0, -204(x8)  # cfg[61] (bank 0) · UNP1_ADDR_BASE_REG_1_Base · 0xffef00f4; write 0x00000000; cfg[61] (bank 0); UNP1_ADDR_BASE_REG_1_Base = 0
    6e8: f2042c23  sw           x0, -200(x8)  # cfg[62] (bank 0) · UNP1_FORCED_SHARED_EXP_shared_exp, UNP1_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr · 0xffef00f8; write 0x00000000; cfg[62] (bank 0); UNP1_FORCED_SHARED_EXP_shared_exp = 0; UNP1_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr = 0
    6ec: f2042e23  sw           x0, -196(x8)  # cfg[63] (bank 0) · UNP1_NOP_REG_CLR_VAL_nop_reg_clr_val · 0xffef00fc; write 0x00000000; cfg[63] (bank 0); UNP1_NOP_REG_CLR_VAL_nop_reg_clr_val = 0
    6f0: 04042823  sw           x0, 80(x8)  # cfg[132] (bank 0) · THCON_SEC1_REG5_Dest_cntx0_address, THCON_SEC1_REG5_Dest_cntx1_address · 0xffef0210; write 0x00000000; cfg[132] (bank 0); THCON_SEC1_REG5_Dest_cntx0_address = 0; THCON_SEC1_REG5_Dest_cntx1_address = 0
    6f4: 010004b7  lui          x9, 0x01000  # x9 = 0x01000000
    6f8: 10048493  addi         x9, x9, 256  # x9 = 0x01000100
    6fc: 04942c23  sw           x9, 88(x8)  # cfg[134] (bank 0) · THCON_SEC1_REG5_Tile_x_dim_cntx0, THCON_SEC1_REG5_Tile_x_dim_cntx1 · 0xffef0218; write 0x01000100; cfg[134] (bank 0); THCON_SEC1_REG5_Tile_x_dim_cntx0 = 256; THCON_SEC1_REG5_Tile_x_dim_cntx1 = 256
    700: 06042823  sw           x0, 112(x8)  # cfg[140] (bank 0) · THCON_SEC1_REG7_Offset_address, THCON_SEC1_REG7_Unpack_data_format_cntx0, THCON_SEC1_REG7_Unpack_out_data_format_cntx0, THCON_SEC1_REG7_Unpack_data_format_cntx4, THCON_SEC1_REG7_Unpack_out_data_format_cntx4 · 0xffef0230; write 0x00000000; cfg[140] (bank 0); THCON_SEC1_REG7_Offset_address = 0; THCON_SEC1_REG7_Unpack_data_format_cntx0 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx0 = 0; THCON_SEC1_REG7_Unpack_data_format_cntx4 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx4 = 0
    704: 06042a23  sw           x0, 116(x8)  # cfg[141] (bank 0) · THCON_SEC1_REG7_Offset_cntx1_address, THCON_SEC1_REG7_Unpack_data_format_cntx1, THCON_SEC1_REG7_Unpack_out_data_format_cntx1, THCON_SEC1_REG7_Unpack_data_format_cntx5, THCON_SEC1_REG7_Unpack_out_data_format_cntx5 · 0xffef0234; write 0x00000000; cfg[141] (bank 0); THCON_SEC1_REG7_Offset_cntx1_address = 0; THCON_SEC1_REG7_Unpack_data_format_cntx1 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx1 = 0; THCON_SEC1_REG7_Unpack_data_format_cntx5 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx5 = 0
    708: 478000ef  jal          x1, 0x00000b80  # target 0x00000b80; x1 = 0x0000070c
    70c: 474000ef  jal          x1, 0x00000b80  # target 0x00000b80; x1 = 0x00000710
    710: 470000ef  jal          x1, 0x00000b80  # target 0x00000b80; x1 = 0x00000714
    714: 46c000ef  jal          x1, 0x00000b80  # target 0x00000b80; x1 = 0x00000718
    718: 00130313  addi         x6, x6, 1
    71c: 9cdff06f  jal          x0, 0x000000e8  # target 0x000000e8
loc_720:
    720: 68c0006f  jal          x0, 0x00000dac  # target 0x00000dac
loc_724:
    724: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    728: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_72c:
    72c: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    730: 0feafa93  andi         x21, x21, 254
    734: 000a8663  beq          x21, x0, 0x00000740  # target 0x00000740
    738: 0ff0000f  fence        0xf, 0xf
    73c: ff1ff06f  jal          x0, 0x0000072c  # target 0x0000072c
loc_740:
    740: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    744: d500011e  RMWCIB2      Mask=64, Data=0, CfgRegAddr=71  # cfg[71] (current thread StateID); THCON_SEC0_REG1_Unp_LF8_4b_exp = 0
    748: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    74c: 100a0a13  addi         x20, x20, 256  # x20 = 0xffef0100 · cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor
    750: 01500a93  addi         x21, x0, 21  # x21 = 0x00000015
    754: 015a2023  sw           x21, 0(x20)  # cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor · 0xffef0100; write 0x00000015; cfg[64] (bank 0); THCON_SEC0_REG0_TileDescriptor = 21
    758: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
    75c: 001a8a93  addi         x21, x21, 1  # x21 = 0x00040001
    760: 015a2223  sw           x21, 4(x20)  # cfg[65] (bank 0) (undocumented index) · 0xffef0104; write 0x00040001; cfg[65] (bank 0) · fields not in ttsim
    764: 000a2423  sw           x0, 8(x20)  # cfg[66] (bank 0) (undocumented index) · 0xffef0108; write 0x00000000; cfg[66] (bank 0) · fields not in ttsim
    768: 000a2623  sw           x0, 12(x20)  # cfg[67] (bank 0) (undocumented index) · 0xffef010c; write 0x00000000; cfg[67] (bank 0) · fields not in ttsim
    76c: 02500a93  addi         x21, x0, 37  # x21 = 0x00000025
    770: 035a2023  sw           x21, 32(x20)  # cfg[72] (bank 0) · THCON_SEC0_REG2_Out_data_format, THCON_SEC0_REG2_Throttle_mode, THCON_SEC0_REG2_Context_count, THCON_SEC0_REG2_Haloize_mode, THCON_SEC0_REG2_Tileize_mode, THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC0_REG2_Unpack_If_Sel, THCON_SEC0_REG2_Upsample_rate, THCON_SEC0_REG2_Ovrd_data_format, THCON_SEC0_REG2_Upsample_and_interleave, THCON_SEC0_REG2_Shift_amount_cntx0, THCON_SEC0_REG2_Shift_amount_cntx1, THCON_SEC0_REG2_Shift_amount_cntx2, THCON_SEC0_REG2_Shift_amount_cntx3 · 0xffef0120; write 0x00000025; cfg[72] (bank 0); THCON_SEC0_REG2_Out_data_format = 5; THCON_SEC0_REG2_Throttle_mode = 2; THCON_SEC0_REG2_Context_count = 0; THCON_SEC0_REG2_Haloize_mode = 0; THCON_SEC0_REG2_Tileize_mode = 0; THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC0_REG2_Unpack_If_Sel = 0; THCON_SEC0_REG2_Upsample_rate = 0; THCON_SEC0_REG2_Ovrd_data_format = 0; THCON_SEC0_REG2_Upsample_and_interleave = 0; THCON_SEC0_REG2_Shift_amount_cntx0 = 0; THCON_SEC0_REG2_Shift_amount_cntx1 = 0; THCON_SEC0_REG2_Shift_amount_cntx2 = 0; THCON_SEC0_REG2_Shift_amount_cntx3 = 0
    774: 00300a93  addi         x21, x0, 3  # x21 = 0x00000003
    778: 035a2223  sw           x21, 36(x20)  # cfg[73] (bank 0) · THCON_SEC0_REG2_Disable_zero_compress_cntx0, THCON_SEC0_REG2_Disable_zero_compress_cntx1, THCON_SEC0_REG2_Disable_zero_compress_cntx2, THCON_SEC0_REG2_Disable_zero_compress_cntx3, THCON_SEC0_REG2_Unpack_if_sel_cntx0, THCON_SEC0_REG2_Unpack_if_sel_cntx1, THCON_SEC0_REG2_Unpack_if_sel_cntx2, THCON_SEC0_REG2_Unpack_if_sel_cntx3, THCON_SEC0_REG2_Force_shared_exp, THCON_SEC0_REG2_Context_count_non_log2, THCON_SEC0_REG2_Context_count_non_log2_en, THCON_SEC0_REG2_Disable_zero_compress_cntx4, THCON_SEC0_REG2_Disable_zero_compress_cntx5, THCON_SEC0_REG2_Disable_zero_compress_cntx6, THCON_SEC0_REG2_Disable_zero_compress_cntx7, THCON_SEC0_REG2_Unpack_if_sel_cntx4, THCON_SEC0_REG2_Unpack_if_sel_cntx5, THCON_SEC0_REG2_Unpack_if_sel_cntx6, THCON_SEC0_REG2_Unpack_if_sel_cntx7, THCON_SEC0_REG2_Metadata_x_end · 0xffef0124; write 0x00000003; cfg[73] (bank 0); THCON_SEC0_REG2_Disable_zero_compress_cntx0 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx1 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx2 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx3 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx0 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx1 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx2 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx3 = 0; THCON_SEC0_REG2_Force_shared_exp = 0; THCON_SEC0_REG2_Context_count_non_log2 = 0; THCON_SEC0_REG2_Context_count_non_log2_en = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx4 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx5 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx6 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx7 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx4 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx5 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx6 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx7 = 0; THCON_SEC0_REG2_Metadata_x_end = 0
    77c: 020a2423  sw           x0, 40(x20)  # cfg[74] (bank 0) · THCON_SEC0_REG2_Unpack_limit_address · 0xffef0128; write 0x00000000; cfg[74] (bank 0); THCON_SEC0_REG2_Unpack_limit_address = 0
    780: 020a2623  sw           x0, 44(x20)  # cfg[75] (bank 0) · THCON_SEC0_REG2_Unpack_fifo_size · 0xffef012c; write 0x00000000; cfg[75] (bank 0); THCON_SEC0_REG2_Unpack_fifo_size = 0
    784: fa0a2823  sw           x0, -80(x20)  # cfg[44] (bank 0) · UNP0_ADDR_CTRL_XY_REG_0_Xstride, UNP0_ADDR_CTRL_XY_REG_0_Ystride · 0xffef00b0; write 0x00000000; cfg[44] (bank 0); UNP0_ADDR_CTRL_XY_REG_0_Xstride = 0; UNP0_ADDR_CTRL_XY_REG_0_Ystride = 0
    788: fa0a2a23  sw           x0, -76(x20)  # cfg[45] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_0_Zstride, UNP0_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef00b4; write 0x00000000; cfg[45] (bank 0); UNP0_ADDR_CTRL_ZW_REG_0_Zstride = 0; UNP0_ADDR_CTRL_ZW_REG_0_Wstride = 0
    78c: 00200ab7  lui          x21, 0x00200  # x21 = 0x00200000
    790: 002a8a93  addi         x21, x21, 2  # x21 = 0x00200002
    794: ff5a2023  sw           x21, -32(x20)  # cfg[56] (bank 0) · UNP0_ADDR_CTRL_XY_REG_1_Xstride, UNP0_ADDR_CTRL_XY_REG_1_Ystride · 0xffef00e0; write 0x00200002; cfg[56] (bank 0); UNP0_ADDR_CTRL_XY_REG_1_Xstride = 2; UNP0_ADDR_CTRL_XY_REG_1_Ystride = 32
    798: 20000a93  addi         x21, x0, 512  # x21 = 0x00000200
    79c: ff5a2223  sw           x21, -28(x20)  # cfg[57] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_1_Zstride, UNP0_ADDR_CTRL_ZW_REG_1_Wstride · 0xffef00e4; write 0x00000200; cfg[57] (bank 0); UNP0_ADDR_CTRL_ZW_REG_1_Zstride = 512; UNP0_ADDR_CTRL_ZW_REG_1_Wstride = 0
    7a0: fc0a2023  sw           x0, -64(x20)  # cfg[48] (bank 0) · UNP0_ADDR_BASE_REG_0_Base · 0xffef00c0; write 0x00000000; cfg[48] (bank 0); UNP0_ADDR_BASE_REG_0_Base = 0
    7a4: fc0a2223  sw           x0, -60(x20)  # cfg[49] (bank 0) · UNP0_ADDR_BASE_REG_1_Base · 0xffef00c4; write 0x00000000; cfg[49] (bank 0); UNP0_ADDR_BASE_REG_1_Base = 0
    7a8: 10000a93  addi         x21, x0, 256  # x21 = 0x00000100
    7ac: fd5a2423  sw           x21, -56(x20)  # cfg[50] (bank 0) · UNP0_FORCED_SHARED_EXP_shared_exp, UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr · 0xffef00c8; write 0x00000100; cfg[50] (bank 0); UNP0_FORCED_SHARED_EXP_shared_exp = 0; UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr = 1
    7b0: fc0a2a23  sw           x0, -44(x20)  # cfg[53] (bank 0) · UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val · 0xffef00d4; write 0x00000000; cfg[53] (bank 0); UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val = 0
    7b4: 00400ab7  lui          x21, 0x00400  # x21 = 0x00400000
    7b8: 040a8a93  addi         x21, x21, 64  # x21 = 0x00400040
    7bc: 055a2823  sw           x21, 80(x20)  # cfg[84] (bank 0) · THCON_SEC0_REG5_Dest_cntx0_address, THCON_SEC0_REG5_Dest_cntx1_address · 0xffef0150; write 0x00400040; cfg[84] (bank 0); THCON_SEC0_REG5_Dest_cntx0_address = 64; THCON_SEC0_REG5_Dest_cntx1_address = 64
    7c0: 01000ab7  lui          x21, 0x01000  # x21 = 0x01000000
    7c4: 100a8a93  addi         x21, x21, 256  # x21 = 0x01000100
    7c8: 055a2c23  sw           x21, 88(x20)  # cfg[86] (bank 0) · THCON_SEC0_REG5_Tile_x_dim_cntx0, THCON_SEC0_REG5_Tile_x_dim_cntx1 · 0xffef0158; write 0x01000100; cfg[86] (bank 0); THCON_SEC0_REG5_Tile_x_dim_cntx0 = 256; THCON_SEC0_REG5_Tile_x_dim_cntx1 = 256
    7cc: 060a2823  sw           x0, 112(x20)  # cfg[92] (bank 0) · THCON_SEC0_REG7_Offset_address, THCON_SEC0_REG7_Unpack_data_format_cntx0, THCON_SEC0_REG7_Unpack_out_data_format_cntx0, THCON_SEC0_REG7_Unpack_data_format_cntx4, THCON_SEC0_REG7_Unpack_out_data_format_cntx4 · 0xffef0170; write 0x00000000; cfg[92] (bank 0); THCON_SEC0_REG7_Offset_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx4 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx4 = 0
    7d0: 060a2a23  sw           x0, 116(x20)  # cfg[93] (bank 0) · THCON_SEC0_REG7_Offset_cntx1_address, THCON_SEC0_REG7_Unpack_data_format_cntx1, THCON_SEC0_REG7_Unpack_out_data_format_cntx1, THCON_SEC0_REG7_Unpack_data_format_cntx5, THCON_SEC0_REG7_Unpack_out_data_format_cntx5 · 0xffef0174; write 0x00000000; cfg[93] (bank 0); THCON_SEC0_REG7_Offset_cntx1_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx5 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx5 = 0
    7d4: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    7d8: 820a8a93  addi         x21, x21, -2016  # x21 = 0xffb00820 · riscv_local_mem + 0x820
    7dc: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x820 · 0xffb00820
    7e0: 004a5a13  srli         x20, x20, 4
    7e4: fffa0a13  addi         x20, x20, -1
    7e8: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    7ec: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    7f0: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    7f4: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    7f8: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    7fc: c8140012  SETC16       setc16_reg=5, setc16_value=4  # thread_cfg[5] (current thread); SRCA_SET_Base = 0; SRCA_SET_SetOvrdWithAddr = 1
    800: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    804: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    808: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    80c: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    810: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    814: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    818: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    81c: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    820: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    824: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    828: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    82c: 01507033  and          x0, x0, x21
    830: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    834: 00400a93  addi         x21, x0, 4  # x21 = 0x00000004
    838: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000004
    83c: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
    840: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000001
    844: 42008ab7  lui          x21, 0x42008  # x21 = 0x42008000
    848: 0c1a8a93  addi         x21, x21, 193  # x21 = 0x420080c1
    84c: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x420080c1; MOP template instruction · UNPACR Unpack_block_selection=0, AddrMode=1, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    850: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    854: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x02000000; MOP template instruction · NOP 
    858: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP 
    85c: 43800ab7  lui          x21, 0x43800  # x21 = 0x43800000
    860: 101a8a93  addi         x21, x21, 257  # x21 = 0x43800101
    864: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    868: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    86c: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP 
    870: 43800ab7  lui          x21, 0x43800  # x21 = 0x43800000
    874: 101a8a93  addi         x21, x21, 257  # x21 = 0x43800101
    878: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    87c: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    880: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    884: 824c0c13  addi         x24, x24, -2012  # x24 = 0xffb00824 · riscv_local_mem + 0x824
    888: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x824 · 0xffb00824
    88c: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_890:
    890: ffb4fc37  lui          x24, 0xffb4f  # x24 = 0xffb4f000
    894: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb4f028
    898: 000c5a83  lhu          x21, 0(x24)  # 0xffb4f028
    89c: 414a8b33  sub          x22, x21, x20
    8a0: 010b1b13  slli         x22, x22, 16
    8a4: 010b5b13  srli         x22, x22, 16
    8a8: 017b7663  bgeu         x22, x23, 0x000008b4  # target 0x000008b4
    8ac: 0ff0000f  fence        0xf, 0xf
    8b0: fe1ff06f  jal          x0, 0x00000890  # target 0x00000890
loc_8b4:
    8b4: 0ff0000f  fence        0xf, 0xf
    8b8: 88100082  STALLWAIT    stall_res=8, wait_res=32  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR
    8bc: 788ff001  SETADCXX     CntSetMask=1, x_end2=255, x_start=0
    8c0: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    8c4: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    8c8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    8cc: 8810000a  STALLWAIT    stall_res=8, wait_res=2  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0
    8d0: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    8d4: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    8d8: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    8dc: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    8e0: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    8e4: 01507033  and          x0, x0, x21
    8e8: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    8ec: 824a8a93  addi         x21, x21, -2012  # x21 = 0xffb00824 · riscv_local_mem + 0x824
    8f0: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x824 · 0xffb00824
    8f4: 001a0a13  addi         x20, x20, 1
    8f8: 010a1a13  slli         x20, x20, 16
    8fc: 010a5a13  srli         x20, x20, 16
    900: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    904: 824a8a93  addi         x21, x21, -2012  # x21 = 0xffb00824 · riscv_local_mem + 0x824
    908: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x824 · 0xffb00824; write runtime value
    90c: ffb4fab7  lui          x21, 0xffb4f  # x21 = 0xffb4f000
    910: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb4f020
    914: 014aa023  sw           x20, 0(x21)  # 0xffb4f020; write runtime value
    918: 0ff0000f  fence        0xf, 0xf
    91c: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    920: 820c0c13  addi         x24, x24, -2016  # x24 = 0xffb00820 · riscv_local_mem + 0x820
    924: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x820 · 0xffb00820
    928: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    92c: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    930: 015a0a33  add          x20, x20, x21
    934: 000a2b37  lui          x22, 0x000a2  # x22 = 0x000a2000
    938: 016a6663  bltu         x20, x22, 0x00000944  # target 0x00000944
    93c: 00002bb7  lui          x23, 0x00002  # x23 = 0x00002000
    940: 417a0a33  sub          x20, x20, x23
loc_944:
    944: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    948: 820c0c13  addi         x24, x24, -2016  # x24 = 0xffb00820 · riscv_local_mem + 0x820
    94c: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x820 · 0xffb00820; write runtime value
    950: 00008067  jalr         x0, 0(x1)
loc_954:
    954: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    958: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_95c:
    95c: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    960: 0feafa93  andi         x21, x21, 254
    964: 000a8663  beq          x21, x0, 0x00000970  # target 0x00000970
    968: 0ff0000f  fence        0xf, 0xf
    96c: ff1ff06f  jal          x0, 0x0000095c  # target 0x0000095c
loc_970:
    970: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    974: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    978: 828a8a93  addi         x21, x21, -2008  # x21 = 0xffb00828 · riscv_local_mem + 0x828
    97c: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x828 · 0xffb00828
    980: 004a5a13  srli         x20, x20, 4
    984: fffa0a13  addi         x20, x20, -1
    988: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    98c: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    990: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    994: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    998: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    99c: c8140012  SETC16       setc16_reg=5, setc16_value=4  # thread_cfg[5] (current thread); SRCA_SET_Base = 0; SRCA_SET_SetOvrdWithAddr = 1
    9a0: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    9a4: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_9a8:
    9a8: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    9ac: 0feafa93  andi         x21, x21, 254
    9b0: 000a8663  beq          x21, x0, 0x000009bc  # target 0x000009bc
    9b4: 0ff0000f  fence        0xf, 0xf
    9b8: ff1ff06f  jal          x0, 0x000009a8  # target 0x000009a8
loc_9bc:
    9bc: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    9c0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    9c4: 830a8a93  addi         x21, x21, -2000  # x21 = 0xffb00830 · riscv_local_mem + 0x830
    9c8: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x830 · 0xffb00830
    9cc: 004a5a13  srli         x20, x20, 4
    9d0: fffa0a13  addi         x20, x20, -1
    9d4: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    9d8: 1f0a8a93  addi         x21, x21, 496  # x21 = 0xffef01f0 · cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address
    9dc: 014aa023  sw           x20, 0(x21)  # cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address · 0xffef01f0; write runtime value; cfg[124] (bank 0); THCON_SEC1_REG3_Base_address = runtime
    9e0: 014aa223  sw           x20, 4(x21)  # cfg[125] (bank 0) · THCON_SEC1_REG3_Base_cntx1_address · 0xffef01f4; write runtime value; cfg[125] (bank 0); THCON_SEC1_REG3_Base_cntx1_address = runtime
    9e4: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    9e8: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    9ec: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    9f0: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    9f4: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    9f8: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    9fc: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    a00: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    a04: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    a08: 834c0c13  addi         x24, x24, -1996  # x24 = 0xffb00834 · riscv_local_mem + 0x834
    a0c: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x834 · 0xffb00834
    a10: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_a14:
    a14: ffb48c37  lui          x24, 0xffb48  # x24 = 0xffb48000
    a18: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb48028
    a1c: 000c5a83  lhu          x21, 0(x24)  # 0xffb48028
    a20: 414a8b33  sub          x22, x21, x20
    a24: 010b1b13  slli         x22, x22, 16
    a28: 010b5b13  srli         x22, x22, 16
    a2c: 017b7663  bgeu         x22, x23, 0x00000a38  # target 0x00000a38
    a30: 0ff0000f  fence        0xf, 0xf
    a34: fe1ff06f  jal          x0, 0x00000a14  # target 0x00000a14
loc_a38:
    a38: 0ff0000f  fence        0xf, 0xf
    a3c: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    a40: 82cc0c13  addi         x24, x24, -2004  # x24 = 0xffb0082c · riscv_local_mem + 0x82c
    a44: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x82c · 0xffb0082c
    a48: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_a4c:
    a4c: ffb49c37  lui          x24, 0xffb49  # x24 = 0xffb49000
    a50: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb49028
    a54: 000c5a83  lhu          x21, 0(x24)  # 0xffb49028
    a58: 414a8b33  sub          x22, x21, x20
    a5c: 010b1b13  slli         x22, x22, 16
    a60: 010b5b13  srli         x22, x22, 16
    a64: 017b7663  bgeu         x22, x23, 0x00000a70  # target 0x00000a70
    a68: 0ff0000f  fence        0xf, 0xf
    a6c: fe1ff06f  jal          x0, 0x00000a4c  # target 0x00000a4c
loc_a70:
    a70: 0ff0000f  fence        0xf, 0xf
    a74: 88100182  STALLWAIT    stall_res=8, wait_res=96  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR | Wait.SRCB_CLR
    a78: 78bff001  SETADCXX     CntSetMask=1, x_end2=1023, x_start=0
    a7c: 793ff001  SETADCXX     CntSetMask=2, x_end2=1023, x_start=0
    a80: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    a84: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    a88: 0a000305  UNPACR       Unpack_block_selection=1, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    a8c: 08000305  UNPACR       Unpack_block_selection=0, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    a90: 8810001a  STALLWAIT    stall_res=8, wait_res=6  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0 | Wait.UNPACK1
    a94: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    a98: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    a9c: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    aa0: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    aa4: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    aa8: 01507033  and          x0, x0, x21
    aac: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    ab0: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    ab4: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834
    ab8: 001a0a13  addi         x20, x20, 1
    abc: 010a1a13  slli         x20, x20, 16
    ac0: 010a5a13  srli         x20, x20, 16
    ac4: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    ac8: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    acc: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834; write runtime value
    ad0: ffb48ab7  lui          x21, 0xffb48  # x21 = 0xffb48000
    ad4: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb48020
    ad8: 014aa023  sw           x20, 0(x21)  # 0xffb48020; write runtime value
    adc: 0ff0000f  fence        0xf, 0xf
    ae0: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    ae4: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    ae8: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830
    aec: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    af0: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    af4: 015a0a33  add          x20, x20, x21
    af8: 00092b37  lui          x22, 0x00092  # x22 = 0x00092000
    afc: 016a6663  bltu         x20, x22, 0x00000b08  # target 0x00000b08
    b00: 00002bb7  lui          x23, 0x00002  # x23 = 0x00002000
    b04: 417a0a33  sub          x20, x20, x23
loc_b08:
    b08: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    b0c: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    b10: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830; write runtime value
    b14: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    b18: 82ca8a93  addi         x21, x21, -2004  # x21 = 0xffb0082c · riscv_local_mem + 0x82c
    b1c: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x82c · 0xffb0082c
    b20: 001a0a13  addi         x20, x20, 1
    b24: 010a1a13  slli         x20, x20, 16
    b28: 010a5a13  srli         x20, x20, 16
    b2c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    b30: 82ca8a93  addi         x21, x21, -2004  # x21 = 0xffb0082c · riscv_local_mem + 0x82c
    b34: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x82c · 0xffb0082c; write runtime value
    b38: ffb49ab7  lui          x21, 0xffb49  # x21 = 0xffb49000
    b3c: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb49020
    b40: 014aa023  sw           x20, 0(x21)  # 0xffb49020; write runtime value
    b44: 0ff0000f  fence        0xf, 0xf
    b48: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    b4c: 828c0c13  addi         x24, x24, -2008  # x24 = 0xffb00828 · riscv_local_mem + 0x828
    b50: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x828 · 0xffb00828
    b54: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    b58: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    b5c: 015a0a33  add          x20, x20, x21
    b60: 00096b37  lui          x22, 0x00096  # x22 = 0x00096000
    b64: 016a6663  bltu         x20, x22, 0x00000b70  # target 0x00000b70
    b68: 00004bb7  lui          x23, 0x00004  # x23 = 0x00004000
    b6c: 417a0a33  sub          x20, x20, x23
loc_b70:
    b70: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    b74: 828c0c13  addi         x24, x24, -2008  # x24 = 0xffb00828 · riscv_local_mem + 0x828
    b78: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x828 · 0xffb00828; write runtime value
    b7c: 00008067  jalr         x0, 0(x1)
loc_b80:
    b80: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    b84: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_b88:
    b88: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    b8c: 0feafa93  andi         x21, x21, 254
    b90: 000a8663  beq          x21, x0, 0x00000b9c  # target 0x00000b9c
    b94: 0ff0000f  fence        0xf, 0xf
    b98: ff1ff06f  jal          x0, 0x00000b88  # target 0x00000b88
loc_b9c:
    b9c: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    ba0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    ba4: 848a8a93  addi         x21, x21, -1976  # x21 = 0xffb00848 · riscv_local_mem + 0x848
    ba8: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x848 · 0xffb00848
    bac: 004a5a13  srli         x20, x20, 4
    bb0: fffa0a13  addi         x20, x20, -1
    bb4: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    bb8: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    bbc: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    bc0: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    bc4: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    bc8: c8140012  SETC16       setc16_reg=5, setc16_value=4  # thread_cfg[5] (current thread); SRCA_SET_Base = 0; SRCA_SET_SetOvrdWithAddr = 1
    bcc: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    bd0: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_bd4:
    bd4: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    bd8: 0feafa93  andi         x21, x21, 254
    bdc: 000a8663  beq          x21, x0, 0x00000be8  # target 0x00000be8
    be0: 0ff0000f  fence        0xf, 0xf
    be4: ff1ff06f  jal          x0, 0x00000bd4  # target 0x00000bd4
loc_be8:
    be8: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    bec: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    bf0: 850a8a93  addi         x21, x21, -1968  # x21 = 0xffb00850 · riscv_local_mem + 0x850
    bf4: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x850 · 0xffb00850
    bf8: 004a5a13  srli         x20, x20, 4
    bfc: fffa0a13  addi         x20, x20, -1
    c00: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    c04: 1f0a8a93  addi         x21, x21, 496  # x21 = 0xffef01f0 · cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address
    c08: 014aa023  sw           x20, 0(x21)  # cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address · 0xffef01f0; write runtime value; cfg[124] (bank 0); THCON_SEC1_REG3_Base_address = runtime
    c0c: 014aa223  sw           x20, 4(x21)  # cfg[125] (bank 0) · THCON_SEC1_REG3_Base_cntx1_address · 0xffef01f4; write runtime value; cfg[125] (bank 0); THCON_SEC1_REG3_Base_cntx1_address = runtime
    c10: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    c14: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    c18: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    c1c: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    c20: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    c24: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    c28: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    c2c: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    c30: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    c34: 854c0c13  addi         x24, x24, -1964  # x24 = 0xffb00854 · riscv_local_mem + 0x854
    c38: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x854 · 0xffb00854
    c3c: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_c40:
    c40: ffb4bc37  lui          x24, 0xffb4b  # x24 = 0xffb4b000
    c44: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb4b028
    c48: 000c5a83  lhu          x21, 0(x24)  # 0xffb4b028
    c4c: 414a8b33  sub          x22, x21, x20
    c50: 010b1b13  slli         x22, x22, 16
    c54: 010b5b13  srli         x22, x22, 16
    c58: 017b7663  bgeu         x22, x23, 0x00000c64  # target 0x00000c64
    c5c: 0ff0000f  fence        0xf, 0xf
    c60: fe1ff06f  jal          x0, 0x00000c40  # target 0x00000c40
loc_c64:
    c64: 0ff0000f  fence        0xf, 0xf
    c68: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    c6c: 84cc0c13  addi         x24, x24, -1972  # x24 = 0xffb0084c · riscv_local_mem + 0x84c
    c70: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x84c · 0xffb0084c
    c74: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_c78:
    c78: ffb4ac37  lui          x24, 0xffb4a  # x24 = 0xffb4a000
    c7c: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb4a028
    c80: 000c5a83  lhu          x21, 0(x24)  # 0xffb4a028
    c84: 414a8b33  sub          x22, x21, x20
    c88: 010b1b13  slli         x22, x22, 16
    c8c: 010b5b13  srli         x22, x22, 16
    c90: 017b7663  bgeu         x22, x23, 0x00000c9c  # target 0x00000c9c
    c94: 0ff0000f  fence        0xf, 0xf
    c98: fe1ff06f  jal          x0, 0x00000c78  # target 0x00000c78
loc_c9c:
    c9c: 0ff0000f  fence        0xf, 0xf
    ca0: 88100182  STALLWAIT    stall_res=8, wait_res=96  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR | Wait.SRCB_CLR
    ca4: 78bff001  SETADCXX     CntSetMask=1, x_end2=1023, x_start=0
    ca8: 793ff001  SETADCXX     CntSetMask=2, x_end2=1023, x_start=0
    cac: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    cb0: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    cb4: 0a000305  UNPACR       Unpack_block_selection=1, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    cb8: 08000305  UNPACR       Unpack_block_selection=0, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    cbc: 8810001a  STALLWAIT    stall_res=8, wait_res=6  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0 | Wait.UNPACK1
    cc0: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    cc4: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    cc8: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    ccc: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    cd0: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    cd4: 01507033  and          x0, x0, x21
    cd8: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    cdc: 854a8a93  addi         x21, x21, -1964  # x21 = 0xffb00854 · riscv_local_mem + 0x854
    ce0: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x854 · 0xffb00854
    ce4: 001a0a13  addi         x20, x20, 1
    ce8: 010a1a13  slli         x20, x20, 16
    cec: 010a5a13  srli         x20, x20, 16
    cf0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    cf4: 854a8a93  addi         x21, x21, -1964  # x21 = 0xffb00854 · riscv_local_mem + 0x854
    cf8: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x854 · 0xffb00854; write runtime value
    cfc: ffb4bab7  lui          x21, 0xffb4b  # x21 = 0xffb4b000
    d00: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb4b020
    d04: 014aa023  sw           x20, 0(x21)  # 0xffb4b020; write runtime value
    d08: 0ff0000f  fence        0xf, 0xf
    d0c: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    d10: 850c0c13  addi         x24, x24, -1968  # x24 = 0xffb00850 · riscv_local_mem + 0x850
    d14: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x850 · 0xffb00850
    d18: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    d1c: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    d20: 015a0a33  add          x20, x20, x21
    d24: 0009cb37  lui          x22, 0x0009c  # x22 = 0x0009c000
    d28: 016a6663  bltu         x20, x22, 0x00000d34  # target 0x00000d34
    d2c: 00002bb7  lui          x23, 0x00002  # x23 = 0x00002000
    d30: 417a0a33  sub          x20, x20, x23
loc_d34:
    d34: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    d38: 850c0c13  addi         x24, x24, -1968  # x24 = 0xffb00850 · riscv_local_mem + 0x850
    d3c: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x850 · 0xffb00850; write runtime value
    d40: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    d44: 84ca8a93  addi         x21, x21, -1972  # x21 = 0xffb0084c · riscv_local_mem + 0x84c
    d48: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x84c · 0xffb0084c
    d4c: 001a0a13  addi         x20, x20, 1
    d50: 010a1a13  slli         x20, x20, 16
    d54: 010a5a13  srli         x20, x20, 16
    d58: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    d5c: 84ca8a93  addi         x21, x21, -1972  # x21 = 0xffb0084c · riscv_local_mem + 0x84c
    d60: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x84c · 0xffb0084c; write runtime value
    d64: ffb4aab7  lui          x21, 0xffb4a  # x21 = 0xffb4a000
    d68: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb4a020
    d6c: 014aa023  sw           x20, 0(x21)  # 0xffb4a020; write runtime value
    d70: 0ff0000f  fence        0xf, 0xf
    d74: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    d78: 848c0c13  addi         x24, x24, -1976  # x24 = 0xffb00848 · riscv_local_mem + 0x848
    d7c: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x848 · 0xffb00848
    d80: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    d84: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    d88: 015a0a33  add          x20, x20, x21
    d8c: 0009ab37  lui          x22, 0x0009a  # x22 = 0x0009a000
    d90: 016a6663  bltu         x20, x22, 0x00000d9c  # target 0x00000d9c
    d94: 00004bb7  lui          x23, 0x00004  # x23 = 0x00004000
    d98: 417a0a33  sub          x20, x20, x23
loc_d9c:
    d9c: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    da0: 848c0c13  addi         x24, x24, -1976  # x24 = 0xffb00848 · riscv_local_mem + 0x848
    da4: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x848 · 0xffb00848; write runtime value
    da8: 00008067  jalr         x0, 0(x1)
    dac:           j FW_TRISC0+4   # return to firmware, linked at install
