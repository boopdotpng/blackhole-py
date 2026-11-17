# llama3 8b-fp8 decode: attention, trisc0. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (64): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=e2e_q, 0x79c=e2e_k, 0x7a0=e2e_v, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0x11900=attention_core, 0x11904=attention_phase, 0x11908=attention_merger
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
      4: 820a8a93  addi         x21, x21, -2016  # x21 = 0xffb00820 · riscv_local_mem + 0x820
      8: 00023b37  lui          x22, 0x00023  # x22 = 0x00023000
      c: 880b0b13  addi         x22, x22, -1920  # x22 = 0x00022880
     10: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x820 · 0xffb00820; write 0x00022880
     14: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     18: 824a8a93  addi         x21, x21, -2012  # x21 = 0xffb00824 · riscv_local_mem + 0x824
     1c: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x824 · 0xffb00824; write 0x00000000
     20: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
     24: 82828293  addi         x5, x5, -2008  # x5 = 0xffb00828 · riscv_local_mem + 0x828
     28: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     2c: 08030313  addi         x6, x6, 128  # x6 = 0x00012080
     30: 0062a023  sw           x6, 0(x5)  # riscv_local_mem + 0x828 · 0xffb00828; write 0x00012080
     34: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
     38: 82c28293  addi         x5, x5, -2004  # x5 = 0xffb0082c · riscv_local_mem + 0x82c
     3c: 0002a023  sw           x0, 0(x5)  # riscv_local_mem + 0x82c · 0xffb0082c; write 0x00000000
     40: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     44: 830a8a93  addi         x21, x21, -2000  # x21 = 0xffb00830 · riscv_local_mem + 0x830
     48: 00014b37  lui          x22, 0x00014  # x22 = 0x00014000
     4c: 080b0b13  addi         x22, x22, 128  # x22 = 0x00014080
     50: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x830 · 0xffb00830; write 0x00014080
     54: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     58: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
     5c: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834; write 0x00000000
     60: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     64: 838a8a93  addi         x21, x21, -1992  # x21 = 0xffb00838 · riscv_local_mem + 0x838
     68: 00018b37  lui          x22, 0x00018  # x22 = 0x00018000
     6c: 080b0b13  addi         x22, x22, 128  # x22 = 0x00018080
     70: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x838 · 0xffb00838; write 0x00018080
     74: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     78: 83ca8a93  addi         x21, x21, -1988  # x21 = 0xffb0083c · riscv_local_mem + 0x83c
     7c: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x83c · 0xffb0083c; write 0x00000000
     80: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     84: 840a8a93  addi         x21, x21, -1984  # x21 = 0xffb00840 · riscv_local_mem + 0x840
     88: 0001cb37  lui          x22, 0x0001c  # x22 = 0x0001c000
     8c: 080b0b13  addi         x22, x22, 128  # x22 = 0x0001c080
     90: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x840 · 0xffb00840; write 0x0001c080
     94: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     98: 844a8a93  addi         x21, x21, -1980  # x21 = 0xffb00844 · riscv_local_mem + 0x844
     9c: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x844 · 0xffb00844; write 0x00000000
     a0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     a4: 848a8a93  addi         x21, x21, -1976  # x21 = 0xffb00848 · riscv_local_mem + 0x848
     a8: 00026b37  lui          x22, 0x00026  # x22 = 0x00026000
     ac: 980b0b13  addi         x22, x22, -1664  # x22 = 0x00025980
     b0: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x848 · 0xffb00848; write 0x00025980
     b4: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     b8: 84ca8a93  addi         x21, x21, -1972  # x21 = 0xffb0084c · riscv_local_mem + 0x84c
     bc: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x84c · 0xffb0084c; write 0x00000000
     c0: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     c4: 90430313  addi         x6, x6, -1788  # x6 = 0x00011904
     c8: 00032203  lw           x4, 0(x6)  # param attention_phase; 0x00011904
     cc: 79000413  addi         x8, x0, 1936  # x8 = 0x00000790
     d0: 00042303  lw           x6, 0(x8)  # param kv_blocks; 0x00000790
     d4: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
     d8: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
     dc: 0063fa63  bgeu         x7, x6, 0x000000f0  # target 0x000000f0
     e0: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     e4: 05000393  addi         x7, x0, 80  # x7 = 0x00000050
     e8: 0063f463  bgeu         x7, x6, 0x000000f0  # target 0x000000f0
     ec: 00800293  addi         x5, x0, 8  # x5 = 0x00000008
loc_f0:
     f0: 30527ce3  bgeu         x4, x5, 0x00000c08  # target 0x00000c08
     f4: 319000ef  jal          x1, 0x00000c0c  # target 0x00000c0c; x1 = 0x000000f8
     f8: 315000ef  jal          x1, 0x00000c0c  # target 0x00000c0c; x1 = 0x000000fc
     fc: 311000ef  jal          x1, 0x00000c0c  # target 0x00000c0c; x1 = 0x00000100
    100: 30d000ef  jal          x1, 0x00000c0c  # target 0x00000c0c; x1 = 0x00000104
    104: 79000293  addi         x5, x0, 1936  # x5 = 0x00000790
    108: 0002a203  lw           x4, 0(x5)  # param kv_blocks; 0x00000790
    10c: 000123b7  lui          x7, 0x00012  # x7 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    110: 90438393  addi         x7, x7, -1788  # x7 = 0x00011904
    114: 0003a283  lw           x5, 0(x7)  # param attention_phase; 0x00011904
    118: 79000493  addi         x9, x0, 1936  # x9 = 0x00000790
    11c: 0004a383  lw           x7, 0(x9)  # param kv_blocks; 0x00000790
    120: 00100313  addi         x6, x0, 1  # x6 = 0x00000001
    124: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    128: 00747a63  bgeu         x8, x7, 0x0000013c  # target 0x0000013c
    12c: 00400313  addi         x6, x0, 4  # x6 = 0x00000004
    130: 05000413  addi         x8, x0, 80  # x8 = 0x00000050
    134: 00747463  bgeu         x8, x7, 0x0000013c  # target 0x0000013c
    138: 00800313  addi         x6, x0, 8  # x6 = 0x00000008
loc_13c:
    13c: 00620233  add          x4, x4, x6
    140: fff20213  addi         x4, x4, -1
    144: 40520233  sub          x4, x4, x5
    148: 02625233  divu         x4, x4, x6
    14c: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    150: 82c48493  addi         x9, x9, -2004  # x9 = 0xffb0082c · riscv_local_mem + 0x82c
    154: 0004a283  lw           x5, 0(x9)  # riscv_local_mem + 0x82c · 0xffb0082c
    158: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
loc_15c:
    15c: ffb484b7  lui          x9, 0xffb48  # x9 = 0xffb48000
    160: 02848493  addi         x9, x9, 40  # x9 = 0xffb48028
    164: 0004d303  lhu          x6, 0(x9)  # 0xffb48028
    168: 405303b3  sub          x7, x6, x5
    16c: 01039393  slli         x7, x7, 16
    170: 0103d393  srli         x7, x7, 16
    174: 0083f663  bgeu         x7, x8, 0x00000180  # target 0x00000180
    178: 0ff0000f  fence        0xf, 0xf
    17c: fe1ff06f  jal          x0, 0x0000015c  # target 0x0000015c
loc_180:
    180: 0ff0000f  fence        0xf, 0xf
    184: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    188: 00020313  addi         x6, x4, 0
loc_18c:
    18c: 7862f063  bgeu         x5, x6, 0x0000090c  # target 0x0000090c
    190: ffe803b7  lui          x7, 0xffe80  # x7 = 0xffe80000 · tensix_pc_buf + 0x0
    194: 03438393  addi         x7, x7, 52  # x7 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_198:
    198: 0003a403  lw           x8, 0(x7)  # UNPACK_CONFIG_SYNC · 0xffe80034
    19c: 0fe47413  andi         x8, x8, 254
    1a0: 00040663  beq          x8, x0, 0x000001ac  # target 0x000001ac
    1a4: 0ff0000f  fence        0xf, 0xf
    1a8: ff1ff06f  jal          x0, 0x00000198  # target 0x00000198
loc_1ac:
    1ac: ffef03b7  lui          x7, 0xffef0  # x7 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    1b0: 12038393  addi         x7, x7, 288  # x7 = 0xffef0120 · cfg[72] (bank 0) · THCON_SEC0_REG2_Out_data_format, THCON_SEC0_REG2_Throttle_mode, THCON_SEC0_REG2_Context_count, THCON_SEC0_REG2_Haloize_mode, THCON_SEC0_REG2_Tileize_mode, THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC0_REG2_Unpack_If_Sel, THCON_SEC0_REG2_Upsample_rate, THCON_SEC0_REG2_Ovrd_data_format, THCON_SEC0_REG2_Upsample_and_interleave, THCON_SEC0_REG2_Shift_amount_cntx0, THCON_SEC0_REG2_Shift_amount_cntx1, THCON_SEC0_REG2_Shift_amount_cntx2, THCON_SEC0_REG2_Shift_amount_cntx3
    1b4: 12500413  addi         x8, x0, 293  # x8 = 0x00000125
    1b8: 0083a023  sw           x8, 0(x7)  # cfg[72] (bank 0) · THCON_SEC0_REG2_Out_data_format, THCON_SEC0_REG2_Throttle_mode, THCON_SEC0_REG2_Context_count, THCON_SEC0_REG2_Haloize_mode, THCON_SEC0_REG2_Tileize_mode, THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC0_REG2_Unpack_If_Sel, THCON_SEC0_REG2_Upsample_rate, THCON_SEC0_REG2_Ovrd_data_format, THCON_SEC0_REG2_Upsample_and_interleave, THCON_SEC0_REG2_Shift_amount_cntx0, THCON_SEC0_REG2_Shift_amount_cntx1, THCON_SEC0_REG2_Shift_amount_cntx2, THCON_SEC0_REG2_Shift_amount_cntx3 · 0xffef0120; write 0x00000125; cfg[72] (bank 0); THCON_SEC0_REG2_Out_data_format = 5; THCON_SEC0_REG2_Throttle_mode = 2; THCON_SEC0_REG2_Context_count = 0; THCON_SEC0_REG2_Haloize_mode = 1; THCON_SEC0_REG2_Tileize_mode = 0; THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC0_REG2_Unpack_If_Sel = 0; THCON_SEC0_REG2_Upsample_rate = 0; THCON_SEC0_REG2_Ovrd_data_format = 0; THCON_SEC0_REG2_Upsample_and_interleave = 0; THCON_SEC0_REG2_Shift_amount_cntx0 = 0; THCON_SEC0_REG2_Shift_amount_cntx1 = 0; THCON_SEC0_REG2_Shift_amount_cntx2 = 0; THCON_SEC0_REG2_Shift_amount_cntx3 = 0
    1bc: d50001de  RMWCIB2      Mask=64, Data=0, CfgRegAddr=119  # cfg[119] (current thread StateID); THCON_SEC1_REG1_Unp_LF8_4b_exp = 0
    1c0: ffef03b7  lui          x7, 0xffef0  # x7 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    1c4: 1c038393  addi         x7, x7, 448  # x7 = 0xffef01c0 · cfg[112] (bank 0) · THCON_SEC1_REG0_TileDescriptor
    1c8: 01000437  lui          x8, 0x01000  # x8 = 0x01000000
    1cc: 01540413  addi         x8, x8, 21  # x8 = 0x01000015
    1d0: 0083a023  sw           x8, 0(x7)  # cfg[112] (bank 0) · THCON_SEC1_REG0_TileDescriptor · 0xffef01c0; write 0x01000015; cfg[112] (bank 0); THCON_SEC1_REG0_TileDescriptor = 16777237
    1d4: 00040437  lui          x8, 0x00040  # x8 = 0x00040000
    1d8: 00140413  addi         x8, x8, 1  # x8 = 0x00040001
    1dc: 0083a223  sw           x8, 4(x7)  # cfg[113] (bank 0) (undocumented index) · 0xffef01c4; write 0x00040001; cfg[113] (bank 0) · fields not in ttsim
    1e0: 0003a423  sw           x0, 8(x7)  # cfg[114] (bank 0) (undocumented index) · 0xffef01c8; write 0x00000000; cfg[114] (bank 0) · fields not in ttsim
    1e4: 0003a623  sw           x0, 12(x7)  # cfg[115] (bank 0) (undocumented index) · 0xffef01cc; write 0x00000000; cfg[115] (bank 0) · fields not in ttsim
    1e8: 02500413  addi         x8, x0, 37  # x8 = 0x00000025
    1ec: 0283a023  sw           x8, 32(x7)  # cfg[120] (bank 0) · THCON_SEC1_REG2_Out_data_format, THCON_SEC1_REG2_Throttle_mode, THCON_SEC1_REG2_Context_count, THCON_SEC1_REG2_Haloize_mode, THCON_SEC1_REG2_Tileize_mode, THCON_SEC1_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC1_REG2_Unpack_If_Sel, THCON_SEC1_REG2_Upsample_rate, THCON_SEC1_REG2_Ovrd_data_format, THCON_SEC1_REG2_Upsample_and_interleave, THCON_SEC1_REG2_Shift_amount_cntx0, THCON_SEC1_REG2_Shift_amount_cntx1, THCON_SEC1_REG2_Shift_amount_cntx2, THCON_SEC1_REG2_Shift_amount_cntx3 · 0xffef01e0; write 0x00000025; cfg[120] (bank 0); THCON_SEC1_REG2_Out_data_format = 5; THCON_SEC1_REG2_Throttle_mode = 2; THCON_SEC1_REG2_Context_count = 0; THCON_SEC1_REG2_Haloize_mode = 0; THCON_SEC1_REG2_Tileize_mode = 0; THCON_SEC1_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC1_REG2_Unpack_If_Sel = 0; THCON_SEC1_REG2_Upsample_rate = 0; THCON_SEC1_REG2_Ovrd_data_format = 0; THCON_SEC1_REG2_Upsample_and_interleave = 0; THCON_SEC1_REG2_Shift_amount_cntx0 = 0; THCON_SEC1_REG2_Shift_amount_cntx1 = 0; THCON_SEC1_REG2_Shift_amount_cntx2 = 0; THCON_SEC1_REG2_Shift_amount_cntx3 = 0
    1f0: 00300413  addi         x8, x0, 3  # x8 = 0x00000003
    1f4: 0283a223  sw           x8, 36(x7)  # cfg[121] (bank 0) · THCON_SEC1_REG2_Disable_zero_compress_cntx0, THCON_SEC1_REG2_Disable_zero_compress_cntx1, THCON_SEC1_REG2_Disable_zero_compress_cntx2, THCON_SEC1_REG2_Disable_zero_compress_cntx3, THCON_SEC1_REG2_Unpack_if_sel_cntx0, THCON_SEC1_REG2_Unpack_if_sel_cntx1, THCON_SEC1_REG2_Unpack_if_sel_cntx2, THCON_SEC1_REG2_Unpack_if_sel_cntx3, THCON_SEC1_REG2_Force_shared_exp, THCON_SEC1_REG2_Context_count_non_log2, THCON_SEC1_REG2_Context_count_non_log2_en, THCON_SEC1_REG2_Disable_zero_compress_cntx4, THCON_SEC1_REG2_Disable_zero_compress_cntx5, THCON_SEC1_REG2_Disable_zero_compress_cntx6, THCON_SEC1_REG2_Disable_zero_compress_cntx7, THCON_SEC1_REG2_Unpack_if_sel_cntx4, THCON_SEC1_REG2_Unpack_if_sel_cntx5, THCON_SEC1_REG2_Unpack_if_sel_cntx6, THCON_SEC1_REG2_Unpack_if_sel_cntx7, THCON_SEC1_REG2_Metadata_x_end · 0xffef01e4; write 0x00000003; cfg[121] (bank 0); THCON_SEC1_REG2_Disable_zero_compress_cntx0 = 1; THCON_SEC1_REG2_Disable_zero_compress_cntx1 = 1; THCON_SEC1_REG2_Disable_zero_compress_cntx2 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx3 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx0 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx1 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx2 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx3 = 0; THCON_SEC1_REG2_Force_shared_exp = 0; THCON_SEC1_REG2_Context_count_non_log2 = 0; THCON_SEC1_REG2_Context_count_non_log2_en = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx4 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx5 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx6 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx7 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx4 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx5 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx6 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx7 = 0; THCON_SEC1_REG2_Metadata_x_end = 0
    1f8: 0203a423  sw           x0, 40(x7)  # cfg[122] (bank 0) · THCON_SEC1_REG2_Unpack_limit_address · 0xffef01e8; write 0x00000000; cfg[122] (bank 0); THCON_SEC1_REG2_Unpack_limit_address = 0
    1fc: 0203a623  sw           x0, 44(x7)  # cfg[123] (bank 0) · THCON_SEC1_REG2_Unpack_fifo_size · 0xffef01ec; write 0x00000000; cfg[123] (bank 0); THCON_SEC1_REG2_Unpack_fifo_size = 0
    200: ee03ac23  sw           x0, -264(x7)  # cfg[46] (bank 0) · UNP1_ADDR_CTRL_XY_REG_0_Xstride, UNP1_ADDR_CTRL_XY_REG_0_Ystride · 0xffef00b8; write 0x00000000; cfg[46] (bank 0); UNP1_ADDR_CTRL_XY_REG_0_Xstride = 0; UNP1_ADDR_CTRL_XY_REG_0_Ystride = 0
    204: ee03ae23  sw           x0, -260(x7)  # cfg[47] (bank 0) · UNP1_ADDR_CTRL_ZW_REG_0_Zstride, UNP1_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef00bc; write 0x00000000; cfg[47] (bank 0); UNP1_ADDR_CTRL_ZW_REG_0_Zstride = 0; UNP1_ADDR_CTRL_ZW_REG_0_Wstride = 0
    208: 00200437  lui          x8, 0x00200  # x8 = 0x00200000
    20c: 00240413  addi         x8, x8, 2  # x8 = 0x00200002
    210: f283a423  sw           x8, -216(x7)  # cfg[58] (bank 0) · UNP1_ADDR_CTRL_XY_REG_1_Xstride, UNP1_ADDR_CTRL_XY_REG_1_Ystride · 0xffef00e8; write 0x00200002; cfg[58] (bank 0); UNP1_ADDR_CTRL_XY_REG_1_Xstride = 2; UNP1_ADDR_CTRL_XY_REG_1_Ystride = 32
    214: 20000413  addi         x8, x0, 512  # x8 = 0x00000200
    218: f283a623  sw           x8, -212(x7)  # cfg[59] (bank 0) · UNP1_ADDR_CTRL_ZW_REG_1_Zstride, UNP1_ADDR_CTRL_ZW_REG_1_Wstride · 0xffef00ec; write 0x00000200; cfg[59] (bank 0); UNP1_ADDR_CTRL_ZW_REG_1_Zstride = 512; UNP1_ADDR_CTRL_ZW_REG_1_Wstride = 0
    21c: f203a823  sw           x0, -208(x7)  # cfg[60] (bank 0) · UNP1_ADDR_BASE_REG_0_Base · 0xffef00f0; write 0x00000000; cfg[60] (bank 0); UNP1_ADDR_BASE_REG_0_Base = 0
    220: f203aa23  sw           x0, -204(x7)  # cfg[61] (bank 0) · UNP1_ADDR_BASE_REG_1_Base · 0xffef00f4; write 0x00000000; cfg[61] (bank 0); UNP1_ADDR_BASE_REG_1_Base = 0
    224: f203ac23  sw           x0, -200(x7)  # cfg[62] (bank 0) · UNP1_FORCED_SHARED_EXP_shared_exp, UNP1_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr · 0xffef00f8; write 0x00000000; cfg[62] (bank 0); UNP1_FORCED_SHARED_EXP_shared_exp = 0; UNP1_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr = 0
    228: f203ae23  sw           x0, -196(x7)  # cfg[63] (bank 0) · UNP1_NOP_REG_CLR_VAL_nop_reg_clr_val · 0xffef00fc; write 0x00000000; cfg[63] (bank 0); UNP1_NOP_REG_CLR_VAL_nop_reg_clr_val = 0
    22c: 0403a823  sw           x0, 80(x7)  # cfg[132] (bank 0) · THCON_SEC1_REG5_Dest_cntx0_address, THCON_SEC1_REG5_Dest_cntx1_address · 0xffef0210; write 0x00000000; cfg[132] (bank 0); THCON_SEC1_REG5_Dest_cntx0_address = 0; THCON_SEC1_REG5_Dest_cntx1_address = 0
    230: 01000437  lui          x8, 0x01000  # x8 = 0x01000000
    234: 10040413  addi         x8, x8, 256  # x8 = 0x01000100
    238: 0483ac23  sw           x8, 88(x7)  # cfg[134] (bank 0) · THCON_SEC1_REG5_Tile_x_dim_cntx0, THCON_SEC1_REG5_Tile_x_dim_cntx1 · 0xffef0218; write 0x01000100; cfg[134] (bank 0); THCON_SEC1_REG5_Tile_x_dim_cntx0 = 256; THCON_SEC1_REG5_Tile_x_dim_cntx1 = 256
    23c: 0603a823  sw           x0, 112(x7)  # cfg[140] (bank 0) · THCON_SEC1_REG7_Offset_address, THCON_SEC1_REG7_Unpack_data_format_cntx0, THCON_SEC1_REG7_Unpack_out_data_format_cntx0, THCON_SEC1_REG7_Unpack_data_format_cntx4, THCON_SEC1_REG7_Unpack_out_data_format_cntx4 · 0xffef0230; write 0x00000000; cfg[140] (bank 0); THCON_SEC1_REG7_Offset_address = 0; THCON_SEC1_REG7_Unpack_data_format_cntx0 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx0 = 0; THCON_SEC1_REG7_Unpack_data_format_cntx4 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx4 = 0
    240: 0603aa23  sw           x0, 116(x7)  # cfg[141] (bank 0) · THCON_SEC1_REG7_Offset_cntx1_address, THCON_SEC1_REG7_Unpack_data_format_cntx1, THCON_SEC1_REG7_Unpack_out_data_format_cntx1, THCON_SEC1_REG7_Unpack_data_format_cntx5, THCON_SEC1_REG7_Unpack_out_data_format_cntx5 · 0xffef0234; write 0x00000000; cfg[141] (bank 0); THCON_SEC1_REG7_Offset_cntx1_address = 0; THCON_SEC1_REG7_Unpack_data_format_cntx1 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx1 = 0; THCON_SEC1_REG7_Unpack_data_format_cntx5 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx5 = 0
    244: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    248: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_24c:
    24c: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    250: 0feafa93  andi         x21, x21, 254
    254: 000a8663  beq          x21, x0, 0x00000260  # target 0x00000260
    258: 0ff0000f  fence        0xf, 0xf
    25c: ff1ff06f  jal          x0, 0x0000024c  # target 0x0000024c
loc_260:
    260: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    264: 830a8a93  addi         x21, x21, -2000  # x21 = 0xffb00830 · riscv_local_mem + 0x830
    268: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x830 · 0xffb00830
    26c: 004a5a13  srli         x20, x20, 4
    270: fffa0a13  addi         x20, x20, -1
    274: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    278: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    27c: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    280: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    284: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    288: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_28c:
    28c: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    290: 0feafa93  andi         x21, x21, 254
    294: 000a8663  beq          x21, x0, 0x000002a0  # target 0x000002a0
    298: 0ff0000f  fence        0xf, 0xf
    29c: ff1ff06f  jal          x0, 0x0000028c  # target 0x0000028c
loc_2a0:
    2a0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    2a4: 828a8a93  addi         x21, x21, -2008  # x21 = 0xffb00828 · riscv_local_mem + 0x828
    2a8: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x828 · 0xffb00828
    2ac: 004a5a13  srli         x20, x20, 4
    2b0: fffa0a13  addi         x20, x20, -1
    2b4: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    2b8: 1f0a8a93  addi         x21, x21, 496  # x21 = 0xffef01f0 · cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address
    2bc: 014aa023  sw           x20, 0(x21)  # cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address · 0xffef01f0; write runtime value; cfg[124] (bank 0); THCON_SEC1_REG3_Base_address = runtime
    2c0: 014aa223  sw           x20, 4(x21)  # cfg[125] (bank 0) · THCON_SEC1_REG3_Base_cntx1_address · 0xffef01f4; write runtime value; cfg[125] (bank 0); THCON_SEC1_REG3_Base_cntx1_address = runtime
    2c4: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    2c8: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    2cc: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    2d0: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    2d4: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    2d8: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    2dc: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    2e0: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    2e4: 834c0c13  addi         x24, x24, -1996  # x24 = 0xffb00834 · riscv_local_mem + 0x834
    2e8: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x834 · 0xffb00834
    2ec: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_2f0:
    2f0: ffb49c37  lui          x24, 0xffb49  # x24 = 0xffb49000
    2f4: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb49028
    2f8: 000c5a83  lhu          x21, 0(x24)  # 0xffb49028
    2fc: 414a8b33  sub          x22, x21, x20
    300: 010b1b13  slli         x22, x22, 16
    304: 010b5b13  srli         x22, x22, 16
    308: 017b7663  bgeu         x22, x23, 0x00000314  # target 0x00000314
    30c: 0ff0000f  fence        0xf, 0xf
    310: fe1ff06f  jal          x0, 0x000002f0  # target 0x000002f0
loc_314:
    314: 0ff0000f  fence        0xf, 0xf
    318: 88100182  STALLWAIT    stall_res=8, wait_res=96  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR | Wait.SRCB_CLR
    31c: 78bff001  SETADCXX     CntSetMask=1, x_end2=1023, x_start=0
    320: 793ff001  SETADCXX     CntSetMask=2, x_end2=1023, x_start=0
    324: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    328: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    32c: 0a000305  UNPACR       Unpack_block_selection=1, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    330: 08000305  UNPACR       Unpack_block_selection=0, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    334: 8810001a  STALLWAIT    stall_res=8, wait_res=6  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0 | Wait.UNPACK1
    338: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    33c: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    340: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    344: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    348: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    34c: 01507033  and          x0, x0, x21
    350: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    354: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    358: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834
    35c: 001a0a13  addi         x20, x20, 1
    360: 010a1a13  slli         x20, x20, 16
    364: 010a5a13  srli         x20, x20, 16
    368: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834; write runtime value
    36c: ffb49ab7  lui          x21, 0xffb49  # x21 = 0xffb49000
    370: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb49020
    374: 014aa023  sw           x20, 0(x21)  # 0xffb49020; write runtime value
    378: 0ff0000f  fence        0xf, 0xf
    37c: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    380: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    384: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830
    388: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    38c: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    390: 015a0a33  add          x20, x20, x21
    394: 00018b37  lui          x22, 0x00018  # x22 = 0x00018000
    398: 080b0b13  addi         x22, x22, 128  # x22 = 0x00018080
    39c: 016a6663  bltu         x20, x22, 0x000003a8  # target 0x000003a8
    3a0: 00004bb7  lui          x23, 0x00004  # x23 = 0x00004000
    3a4: 417a0a33  sub          x20, x20, x23
loc_3a8:
    3a8: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    3ac: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    3b0: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830; write runtime value
    3b4: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    3b8: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_3bc:
    3bc: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    3c0: 0feafa93  andi         x21, x21, 254
    3c4: 000a8663  beq          x21, x0, 0x000003d0  # target 0x000003d0
    3c8: 0ff0000f  fence        0xf, 0xf
    3cc: ff1ff06f  jal          x0, 0x000003bc  # target 0x000003bc
loc_3d0:
    3d0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    3d4: 830a8a93  addi         x21, x21, -2000  # x21 = 0xffb00830 · riscv_local_mem + 0x830
    3d8: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x830 · 0xffb00830
    3dc: 004a5a13  srli         x20, x20, 4
    3e0: fffa0a13  addi         x20, x20, -1
    3e4: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    3e8: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    3ec: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    3f0: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    3f4: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    3f8: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_3fc:
    3fc: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    400: 0feafa93  andi         x21, x21, 254
    404: 000a8663  beq          x21, x0, 0x00000410  # target 0x00000410
    408: 0ff0000f  fence        0xf, 0xf
    40c: ff1ff06f  jal          x0, 0x000003fc  # target 0x000003fc
loc_410:
    410: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    414: 828a8a93  addi         x21, x21, -2008  # x21 = 0xffb00828 · riscv_local_mem + 0x828
    418: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x828 · 0xffb00828
    41c: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    420: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    424: 015a0a33  add          x20, x20, x21
    428: 00014b37  lui          x22, 0x00014  # x22 = 0x00014000
    42c: 080b0b13  addi         x22, x22, 128  # x22 = 0x00014080
    430: 016a6663  bltu         x20, x22, 0x0000043c  # target 0x0000043c
    434: 00002ab7  lui          x21, 0x00002  # x21 = 0x00002000
    438: 415a0a33  sub          x20, x20, x21
loc_43c:
    43c: 004a5a13  srli         x20, x20, 4
    440: fffa0a13  addi         x20, x20, -1
    444: ffef0bb7  lui          x23, 0xffef0  # x23 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    448: 1f0b8b93  addi         x23, x23, 496  # x23 = 0xffef01f0 · cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address
    44c: 014ba023  sw           x20, 0(x23)  # cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address · 0xffef01f0; write runtime value; cfg[124] (bank 0); THCON_SEC1_REG3_Base_address = runtime
    450: 014ba223  sw           x20, 4(x23)  # cfg[125] (bank 0) · THCON_SEC1_REG3_Base_cntx1_address · 0xffef01f4; write runtime value; cfg[125] (bank 0); THCON_SEC1_REG3_Base_cntx1_address = runtime
    454: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    458: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    45c: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    460: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    464: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    468: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    46c: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    470: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    474: 834c0c13  addi         x24, x24, -1996  # x24 = 0xffb00834 · riscv_local_mem + 0x834
    478: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x834 · 0xffb00834
    47c: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_480:
    480: ffb49c37  lui          x24, 0xffb49  # x24 = 0xffb49000
    484: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb49028
    488: 000c5a83  lhu          x21, 0(x24)  # 0xffb49028
    48c: 414a8b33  sub          x22, x21, x20
    490: 010b1b13  slli         x22, x22, 16
    494: 010b5b13  srli         x22, x22, 16
    498: 017b7663  bgeu         x22, x23, 0x000004a4  # target 0x000004a4
    49c: 0ff0000f  fence        0xf, 0xf
    4a0: fe1ff06f  jal          x0, 0x00000480  # target 0x00000480
loc_4a4:
    4a4: 0ff0000f  fence        0xf, 0xf
    4a8: 88100182  STALLWAIT    stall_res=8, wait_res=96  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR | Wait.SRCB_CLR
    4ac: 78bff001  SETADCXX     CntSetMask=1, x_end2=1023, x_start=0
    4b0: 793ff001  SETADCXX     CntSetMask=2, x_end2=1023, x_start=0
    4b4: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    4b8: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    4bc: 0a000305  UNPACR       Unpack_block_selection=1, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    4c0: 08000305  UNPACR       Unpack_block_selection=0, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    4c4: 8810001a  STALLWAIT    stall_res=8, wait_res=6  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0 | Wait.UNPACK1
    4c8: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    4cc: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    4d0: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    4d4: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    4d8: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    4dc: 01507033  and          x0, x0, x21
    4e0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    4e4: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    4e8: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834
    4ec: 001a0a13  addi         x20, x20, 1
    4f0: 010a1a13  slli         x20, x20, 16
    4f4: 010a5a13  srli         x20, x20, 16
    4f8: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834; write runtime value
    4fc: ffb49ab7  lui          x21, 0xffb49  # x21 = 0xffb49000
    500: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb49020
    504: 014aa023  sw           x20, 0(x21)  # 0xffb49020; write runtime value
    508: 0ff0000f  fence        0xf, 0xf
    50c: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    510: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    514: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830
    518: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    51c: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    520: 015a0a33  add          x20, x20, x21
    524: 00018b37  lui          x22, 0x00018  # x22 = 0x00018000
    528: 080b0b13  addi         x22, x22, 128  # x22 = 0x00018080
    52c: 016a6663  bltu         x20, x22, 0x00000538  # target 0x00000538
    530: 00004bb7  lui          x23, 0x00004  # x23 = 0x00004000
    534: 417a0a33  sub          x20, x20, x23
loc_538:
    538: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    53c: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    540: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830; write runtime value
    544: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    548: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_54c:
    54c: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    550: 0feafa93  andi         x21, x21, 254
    554: 000a8663  beq          x21, x0, 0x00000560  # target 0x00000560
    558: 0ff0000f  fence        0xf, 0xf
    55c: ff1ff06f  jal          x0, 0x0000054c  # target 0x0000054c
loc_560:
    560: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    564: 830a8a93  addi         x21, x21, -2000  # x21 = 0xffb00830 · riscv_local_mem + 0x830
    568: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x830 · 0xffb00830
    56c: 004a5a13  srli         x20, x20, 4
    570: fffa0a13  addi         x20, x20, -1
    574: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    578: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    57c: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    580: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    584: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    588: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_58c:
    58c: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    590: 0feafa93  andi         x21, x21, 254
    594: 000a8663  beq          x21, x0, 0x000005a0  # target 0x000005a0
    598: 0ff0000f  fence        0xf, 0xf
    59c: ff1ff06f  jal          x0, 0x0000058c  # target 0x0000058c
loc_5a0:
    5a0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    5a4: 828a8a93  addi         x21, x21, -2008  # x21 = 0xffb00828 · riscv_local_mem + 0x828
    5a8: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x828 · 0xffb00828
    5ac: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5b0: 015a0a33  add          x20, x20, x21
    5b4: 00014b37  lui          x22, 0x00014  # x22 = 0x00014000
    5b8: 080b0b13  addi         x22, x22, 128  # x22 = 0x00014080
    5bc: 016a6663  bltu         x20, x22, 0x000005c8  # target 0x000005c8
    5c0: 00002ab7  lui          x21, 0x00002  # x21 = 0x00002000
    5c4: 415a0a33  sub          x20, x20, x21
loc_5c8:
    5c8: 004a5a13  srli         x20, x20, 4
    5cc: fffa0a13  addi         x20, x20, -1
    5d0: ffef0bb7  lui          x23, 0xffef0  # x23 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    5d4: 1f0b8b93  addi         x23, x23, 496  # x23 = 0xffef01f0 · cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address
    5d8: 014ba023  sw           x20, 0(x23)  # cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address · 0xffef01f0; write runtime value; cfg[124] (bank 0); THCON_SEC1_REG3_Base_address = runtime
    5dc: 014ba223  sw           x20, 4(x23)  # cfg[125] (bank 0) · THCON_SEC1_REG3_Base_cntx1_address · 0xffef01f4; write runtime value; cfg[125] (bank 0); THCON_SEC1_REG3_Base_cntx1_address = runtime
    5e0: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    5e4: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    5e8: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    5ec: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    5f0: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    5f4: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    5f8: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    5fc: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    600: 834c0c13  addi         x24, x24, -1996  # x24 = 0xffb00834 · riscv_local_mem + 0x834
    604: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x834 · 0xffb00834
    608: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_60c:
    60c: ffb49c37  lui          x24, 0xffb49  # x24 = 0xffb49000
    610: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb49028
    614: 000c5a83  lhu          x21, 0(x24)  # 0xffb49028
    618: 414a8b33  sub          x22, x21, x20
    61c: 010b1b13  slli         x22, x22, 16
    620: 010b5b13  srli         x22, x22, 16
    624: 017b7663  bgeu         x22, x23, 0x00000630  # target 0x00000630
    628: 0ff0000f  fence        0xf, 0xf
    62c: fe1ff06f  jal          x0, 0x0000060c  # target 0x0000060c
loc_630:
    630: 0ff0000f  fence        0xf, 0xf
    634: 88100182  STALLWAIT    stall_res=8, wait_res=96  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR | Wait.SRCB_CLR
    638: 78bff001  SETADCXX     CntSetMask=1, x_end2=1023, x_start=0
    63c: 793ff001  SETADCXX     CntSetMask=2, x_end2=1023, x_start=0
    640: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    644: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    648: 0a000305  UNPACR       Unpack_block_selection=1, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    64c: 08000305  UNPACR       Unpack_block_selection=0, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    650: 8810001a  STALLWAIT    stall_res=8, wait_res=6  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0 | Wait.UNPACK1
    654: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    658: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    65c: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    660: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    664: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    668: 01507033  and          x0, x0, x21
    66c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    670: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    674: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834
    678: 001a0a13  addi         x20, x20, 1
    67c: 010a1a13  slli         x20, x20, 16
    680: 010a5a13  srli         x20, x20, 16
    684: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834; write runtime value
    688: ffb49ab7  lui          x21, 0xffb49  # x21 = 0xffb49000
    68c: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb49020
    690: 014aa023  sw           x20, 0(x21)  # 0xffb49020; write runtime value
    694: 0ff0000f  fence        0xf, 0xf
    698: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    69c: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    6a0: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830
    6a4: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    6a8: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    6ac: 015a0a33  add          x20, x20, x21
    6b0: 00018b37  lui          x22, 0x00018  # x22 = 0x00018000
    6b4: 080b0b13  addi         x22, x22, 128  # x22 = 0x00018080
    6b8: 016a6663  bltu         x20, x22, 0x000006c4  # target 0x000006c4
    6bc: 00004bb7  lui          x23, 0x00004  # x23 = 0x00004000
    6c0: 417a0a33  sub          x20, x20, x23
loc_6c4:
    6c4: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    6c8: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    6cc: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830; write runtime value
    6d0: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    6d4: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_6d8:
    6d8: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    6dc: 0feafa93  andi         x21, x21, 254
    6e0: 000a8663  beq          x21, x0, 0x000006ec  # target 0x000006ec
    6e4: 0ff0000f  fence        0xf, 0xf
    6e8: ff1ff06f  jal          x0, 0x000006d8  # target 0x000006d8
loc_6ec:
    6ec: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    6f0: 830a8a93  addi         x21, x21, -2000  # x21 = 0xffb00830 · riscv_local_mem + 0x830
    6f4: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x830 · 0xffb00830
    6f8: 004a5a13  srli         x20, x20, 4
    6fc: fffa0a13  addi         x20, x20, -1
    700: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    704: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    708: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    70c: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    710: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    714: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_718:
    718: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    71c: 0feafa93  andi         x21, x21, 254
    720: 000a8663  beq          x21, x0, 0x0000072c  # target 0x0000072c
    724: 0ff0000f  fence        0xf, 0xf
    728: ff1ff06f  jal          x0, 0x00000718  # target 0x00000718
loc_72c:
    72c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    730: 828a8a93  addi         x21, x21, -2008  # x21 = 0xffb00828 · riscv_local_mem + 0x828
    734: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x828 · 0xffb00828
    738: 00002ab7  lui          x21, 0x00002  # x21 = 0x00002000
    73c: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00001800
    740: 015a0a33  add          x20, x20, x21
    744: 00014b37  lui          x22, 0x00014  # x22 = 0x00014000
    748: 080b0b13  addi         x22, x22, 128  # x22 = 0x00014080
    74c: 016a6663  bltu         x20, x22, 0x00000758  # target 0x00000758
    750: 00002ab7  lui          x21, 0x00002  # x21 = 0x00002000
    754: 415a0a33  sub          x20, x20, x21
loc_758:
    758: 004a5a13  srli         x20, x20, 4
    75c: fffa0a13  addi         x20, x20, -1
    760: ffef0bb7  lui          x23, 0xffef0  # x23 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    764: 1f0b8b93  addi         x23, x23, 496  # x23 = 0xffef01f0 · cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address
    768: 014ba023  sw           x20, 0(x23)  # cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address · 0xffef01f0; write runtime value; cfg[124] (bank 0); THCON_SEC1_REG3_Base_address = runtime
    76c: 014ba223  sw           x20, 4(x23)  # cfg[125] (bank 0) · THCON_SEC1_REG3_Base_cntx1_address · 0xffef01f4; write runtime value; cfg[125] (bank 0); THCON_SEC1_REG3_Base_cntx1_address = runtime
    770: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    774: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    778: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    77c: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    780: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    784: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    788: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    78c: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    790: 834c0c13  addi         x24, x24, -1996  # x24 = 0xffb00834 · riscv_local_mem + 0x834
    794: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x834 · 0xffb00834
    798: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_79c:
    79c: ffb49c37  lui          x24, 0xffb49  # x24 = 0xffb49000
    7a0: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb49028
    7a4: 000c5a83  lhu          x21, 0(x24)  # 0xffb49028
    7a8: 414a8b33  sub          x22, x21, x20
    7ac: 010b1b13  slli         x22, x22, 16
    7b0: 010b5b13  srli         x22, x22, 16
    7b4: 017b7663  bgeu         x22, x23, 0x000007c0  # target 0x000007c0
    7b8: 0ff0000f  fence        0xf, 0xf
    7bc: fe1ff06f  jal          x0, 0x0000079c  # target 0x0000079c
loc_7c0:
    7c0: 0ff0000f  fence        0xf, 0xf
    7c4: 88100182  STALLWAIT    stall_res=8, wait_res=96  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR | Wait.SRCB_CLR
    7c8: 78bff001  SETADCXX     CntSetMask=1, x_end2=1023, x_start=0
    7cc: 793ff001  SETADCXX     CntSetMask=2, x_end2=1023, x_start=0
    7d0: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    7d4: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    7d8: 0a000305  UNPACR       Unpack_block_selection=1, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    7dc: 08000305  UNPACR       Unpack_block_selection=0, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    7e0: 8810001a  STALLWAIT    stall_res=8, wait_res=6  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0 | Wait.UNPACK1
    7e4: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    7e8: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    7ec: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    7f0: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    7f4: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    7f8: 01507033  and          x0, x0, x21
    7fc: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    800: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    804: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834
    808: 001a0a13  addi         x20, x20, 1
    80c: 010a1a13  slli         x20, x20, 16
    810: 010a5a13  srli         x20, x20, 16
    814: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834; write runtime value
    818: ffb49ab7  lui          x21, 0xffb49  # x21 = 0xffb49000
    81c: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb49020
    820: 014aa023  sw           x20, 0(x21)  # 0xffb49020; write runtime value
    824: 0ff0000f  fence        0xf, 0xf
    828: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    82c: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    830: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830
    834: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    838: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    83c: 015a0a33  add          x20, x20, x21
    840: 00018b37  lui          x22, 0x00018  # x22 = 0x00018000
    844: 080b0b13  addi         x22, x22, 128  # x22 = 0x00018080
    848: 016a6663  bltu         x20, x22, 0x00000854  # target 0x00000854
    84c: 00004bb7  lui          x23, 0x00004  # x23 = 0x00004000
    850: 417a0a33  sub          x20, x20, x23
loc_854:
    854: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    858: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    85c: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830; write runtime value
    860: ffe803b7  lui          x7, 0xffe80  # x7 = 0xffe80000 · tensix_pc_buf + 0x0
    864: 03438393  addi         x7, x7, 52  # x7 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_868:
    868: 0003a403  lw           x8, 0(x7)  # UNPACK_CONFIG_SYNC · 0xffe80034
    86c: 0fe47413  andi         x8, x8, 254
    870: 00040663  beq          x8, x0, 0x0000087c  # target 0x0000087c
    874: 0ff0000f  fence        0xf, 0xf
    878: ff1ff06f  jal          x0, 0x00000868  # target 0x00000868
loc_87c:
    87c: ffef03b7  lui          x7, 0xffef0  # x7 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    880: 12038393  addi         x7, x7, 288  # x7 = 0xffef0120 · cfg[72] (bank 0) · THCON_SEC0_REG2_Out_data_format, THCON_SEC0_REG2_Throttle_mode, THCON_SEC0_REG2_Context_count, THCON_SEC0_REG2_Haloize_mode, THCON_SEC0_REG2_Tileize_mode, THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC0_REG2_Unpack_If_Sel, THCON_SEC0_REG2_Upsample_rate, THCON_SEC0_REG2_Ovrd_data_format, THCON_SEC0_REG2_Upsample_and_interleave, THCON_SEC0_REG2_Shift_amount_cntx0, THCON_SEC0_REG2_Shift_amount_cntx1, THCON_SEC0_REG2_Shift_amount_cntx2, THCON_SEC0_REG2_Shift_amount_cntx3
    884: 02500413  addi         x8, x0, 37  # x8 = 0x00000025
    888: 0083a023  sw           x8, 0(x7)  # cfg[72] (bank 0) · THCON_SEC0_REG2_Out_data_format, THCON_SEC0_REG2_Throttle_mode, THCON_SEC0_REG2_Context_count, THCON_SEC0_REG2_Haloize_mode, THCON_SEC0_REG2_Tileize_mode, THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC0_REG2_Unpack_If_Sel, THCON_SEC0_REG2_Upsample_rate, THCON_SEC0_REG2_Ovrd_data_format, THCON_SEC0_REG2_Upsample_and_interleave, THCON_SEC0_REG2_Shift_amount_cntx0, THCON_SEC0_REG2_Shift_amount_cntx1, THCON_SEC0_REG2_Shift_amount_cntx2, THCON_SEC0_REG2_Shift_amount_cntx3 · 0xffef0120; write 0x00000025; cfg[72] (bank 0); THCON_SEC0_REG2_Out_data_format = 5; THCON_SEC0_REG2_Throttle_mode = 2; THCON_SEC0_REG2_Context_count = 0; THCON_SEC0_REG2_Haloize_mode = 0; THCON_SEC0_REG2_Tileize_mode = 0; THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC0_REG2_Unpack_If_Sel = 0; THCON_SEC0_REG2_Upsample_rate = 0; THCON_SEC0_REG2_Ovrd_data_format = 0; THCON_SEC0_REG2_Upsample_and_interleave = 0; THCON_SEC0_REG2_Shift_amount_cntx0 = 0; THCON_SEC0_REG2_Shift_amount_cntx1 = 0; THCON_SEC0_REG2_Shift_amount_cntx2 = 0; THCON_SEC0_REG2_Shift_amount_cntx3 = 0
    88c: 5a4000ef  jal          x1, 0x00000e30  # target 0x00000e30; x1 = 0x00000890
    890: 5a0000ef  jal          x1, 0x00000e30  # target 0x00000e30; x1 = 0x00000894
    894: 59c000ef  jal          x1, 0x00000e30  # target 0x00000e30; x1 = 0x00000898
    898: 598000ef  jal          x1, 0x00000e30  # target 0x00000e30; x1 = 0x0000089c
    89c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    8a0: 84440413  addi         x8, x8, -1980  # x8 = 0xffb00844 · riscv_local_mem + 0x844
    8a4: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x844 · 0xffb00844
    8a8: 00138393  addi         x7, x7, 1
    8ac: 01039393  slli         x7, x7, 16
    8b0: 0103d393  srli         x7, x7, 16
    8b4: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x844 · 0xffb00844; write runtime value
    8b8: ffb4b437  lui          x8, 0xffb4b  # x8 = 0xffb4b000
    8bc: 02040413  addi         x8, x8, 32  # x8 = 0xffb4b020
    8c0: 00742023  sw           x7, 0(x8)  # 0xffb4b020; write runtime value
    8c4: 0ff0000f  fence        0xf, 0xf
    8c8: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    8cc: 84058593  addi         x11, x11, -1984  # x11 = 0xffb00840 · riscv_local_mem + 0x840
    8d0: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x840 · 0xffb00840
    8d4: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    8d8: 80040413  addi         x8, x8, -2048  # x8 = 0x00000800
    8dc: 008383b3  add          x7, x7, x8
    8e0: 0001d4b7  lui          x9, 0x0001d  # x9 = 0x0001d000
    8e4: 88048493  addi         x9, x9, -1920  # x9 = 0x0001c880
    8e8: 0093e863  bltu         x7, x9, 0x000008f8  # target 0x000008f8
    8ec: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    8f0: 80050513  addi         x10, x10, -2048  # x10 = 0x00000800
    8f4: 40a383b3  sub          x7, x7, x10
loc_8f8:
    8f8: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    8fc: 84058593  addi         x11, x11, -1984  # x11 = 0xffb00840 · riscv_local_mem + 0x840
    900: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x840 · 0xffb00840; write runtime value
    904: 00128293  addi         x5, x5, 1
    908: 885ff06f  jal          x0, 0x0000018c  # target 0x0000018c
loc_90c:
    90c: ffb01337  lui          x6, 0xffb01  # x6 = 0xffb01000
    910: 82c30313  addi         x6, x6, -2004  # x6 = 0xffb0082c · riscv_local_mem + 0x82c
    914: 00032283  lw           x5, 0(x6)  # riscv_local_mem + 0x82c · 0xffb0082c
    918: 00428293  addi         x5, x5, 4
    91c: 01029293  slli         x5, x5, 16
    920: 0102d293  srli         x5, x5, 16
    924: 00532023  sw           x5, 0(x6)  # riscv_local_mem + 0x82c · 0xffb0082c; write runtime value
    928: ffb48337  lui          x6, 0xffb48  # x6 = 0xffb48000
    92c: 02030313  addi         x6, x6, 32  # x6 = 0xffb48020
    930: 00532023  sw           x5, 0(x6)  # 0xffb48020; write runtime value
    934: 0ff0000f  fence        0xf, 0xf
    938: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    93c: 82848493  addi         x9, x9, -2008  # x9 = 0xffb00828 · riscv_local_mem + 0x828
    940: 0004a283  lw           x5, 0(x9)  # riscv_local_mem + 0x828 · 0xffb00828
    944: 00002337  lui          x6, 0x00002  # x6 = 0x00002000
    948: 006282b3  add          x5, x5, x6
    94c: 000143b7  lui          x7, 0x00014  # x7 = 0x00014000
    950: 08038393  addi         x7, x7, 128  # x7 = 0x00014080
    954: 0072e663  bltu         x5, x7, 0x00000960  # target 0x00000960
    958: 00002437  lui          x8, 0x00002  # x8 = 0x00002000
    95c: 408282b3  sub          x5, x5, x8
loc_960:
    960: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    964: 82848493  addi         x9, x9, -2008  # x9 = 0xffb00828 · riscv_local_mem + 0x828
    968: 0054a023  sw           x5, 0(x9)  # riscv_local_mem + 0x828 · 0xffb00828; write runtime value
    96c: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    970: 90428293  addi         x5, x5, -1788  # x5 = 0x00011904
    974: 0002a203  lw           x4, 0(x5)  # param attention_phase; 0x00011904
    978: 28021863  bne          x4, x0, 0x00000c08  # target 0x00000c08
    97c: 79000413  addi         x8, x0, 1936  # x8 = 0x00000790
    980: 00042303  lw           x6, 0(x8)  # param kv_blocks; 0x00000790
    984: 00100213  addi         x4, x0, 1  # x4 = 0x00000001
    988: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
    98c: 0063fa63  bgeu         x7, x6, 0x000009a0  # target 0x000009a0
    990: 00400213  addi         x4, x0, 4  # x4 = 0x00000004
    994: 05000393  addi         x7, x0, 80  # x7 = 0x00000050
    998: 0063f463  bgeu         x7, x6, 0x000009a0  # target 0x000009a0
    99c: 00800213  addi         x4, x0, 8  # x4 = 0x00000008
loc_9a0:
    9a0: 00600293  addi         x5, x0, 6  # x5 = 0x00000006
    9a4: 02520233  mul          x4, x4, x5
    9a8: fff20213  addi         x4, x4, -1
    9ac: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    9b0: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_9b4:
    9b4: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    9b8: 0feafa93  andi         x21, x21, 254
    9bc: 000a8663  beq          x21, x0, 0x000009c8  # target 0x000009c8
    9c0: 0ff0000f  fence        0xf, 0xf
    9c4: ff1ff06f  jal          x0, 0x000009b4  # target 0x000009b4
loc_9c8:
    9c8: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    9cc: 100a0a13  addi         x20, x20, 256  # x20 = 0xffef0100 · cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor
    9d0: 01000a93  addi         x21, x0, 16  # x21 = 0x00000010
    9d4: 015a2023  sw           x21, 0(x20)  # cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor · 0xffef0100; write 0x00000010; cfg[64] (bank 0); THCON_SEC0_REG0_TileDescriptor = 16
    9d8: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    9dc: 848a8a93  addi         x21, x21, -1976  # x21 = 0xffb00848 · riscv_local_mem + 0x848
    9e0: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x848 · 0xffb00848
    9e4: 004a5a13  srli         x20, x20, 4
    9e8: fffa0a13  addi         x20, x20, -1
    9ec: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    9f0: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    9f4: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    9f8: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    9fc: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    a00: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    a04: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    a08: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    a0c: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    a10: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    a14: 84cc0c13  addi         x24, x24, -1972  # x24 = 0xffb0084c · riscv_local_mem + 0x84c
    a18: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x84c · 0xffb0084c
    a1c: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_a20:
    a20: ffb50c37  lui          x24, 0xffb50  # x24 = 0xffb50000
    a24: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb50028
    a28: 000c5a83  lhu          x21, 0(x24)  # 0xffb50028
    a2c: 414a8b33  sub          x22, x21, x20
    a30: 010b1b13  slli         x22, x22, 16
    a34: 010b5b13  srli         x22, x22, 16
    a38: 017b7663  bgeu         x22, x23, 0x00000a44  # target 0x00000a44
    a3c: 0ff0000f  fence        0xf, 0xf
    a40: fe1ff06f  jal          x0, 0x00000a20  # target 0x00000a20
loc_a44:
    a44: 0ff0000f  fence        0xf, 0xf
    a48: 88100082  STALLWAIT    stall_res=8, wait_res=32  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR
    a4c: 788ff001  SETADCXX     CntSetMask=1, x_end2=255, x_start=0
    a50: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    a54: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    a58: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    a5c: 8810000a  STALLWAIT    stall_res=8, wait_res=2  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0
    a60: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    a64: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    a68: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    a6c: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    a70: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    a74: 01507033  and          x0, x0, x21
    a78: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    a7c: 84ca8a93  addi         x21, x21, -1972  # x21 = 0xffb0084c · riscv_local_mem + 0x84c
    a80: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x84c · 0xffb0084c
    a84: 001a0a13  addi         x20, x20, 1
    a88: 010a1a13  slli         x20, x20, 16
    a8c: 010a5a13  srli         x20, x20, 16
    a90: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x84c · 0xffb0084c; write runtime value
    a94: ffb50ab7  lui          x21, 0xffb50  # x21 = 0xffb50000
    a98: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb50020
    a9c: 014aa023  sw           x20, 0(x21)  # 0xffb50020; write runtime value
    aa0: 0ff0000f  fence        0xf, 0xf
    aa4: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    aa8: 848c0c13  addi         x24, x24, -1976  # x24 = 0xffb00848 · riscv_local_mem + 0x848
    aac: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x848 · 0xffb00848
    ab0: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    ab4: 015a0a33  add          x20, x20, x21
    ab8: 00056b37  lui          x22, 0x00056  # x22 = 0x00056000
    abc: 980b0b13  addi         x22, x22, -1664  # x22 = 0x00055980
    ac0: 016a6663  bltu         x20, x22, 0x00000acc  # target 0x00000acc
    ac4: 00030bb7  lui          x23, 0x00030  # x23 = 0x00030000 · arc_apb_reset_unit + 0x0
    ac8: 417a0a33  sub          x20, x20, x23
loc_acc:
    acc: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    ad0: 848c0c13  addi         x24, x24, -1976  # x24 = 0xffb00848 · riscv_local_mem + 0x848
    ad4: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x848 · 0xffb00848; write runtime value
    ad8: 00000313  addi         x6, x0, 0  # x6 = 0x00000000
    adc: 00020393  addi         x7, x4, 0
loc_ae0:
    ae0: 12737463  bgeu         x6, x7, 0x00000c08  # target 0x00000c08
    ae4: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    ae8: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_aec:
    aec: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    af0: 0feafa93  andi         x21, x21, 254
    af4: 000a8663  beq          x21, x0, 0x00000b00  # target 0x00000b00
    af8: 0ff0000f  fence        0xf, 0xf
    afc: ff1ff06f  jal          x0, 0x00000aec  # target 0x00000aec
loc_b00:
    b00: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    b04: 848a8a93  addi         x21, x21, -1976  # x21 = 0xffb00848 · riscv_local_mem + 0x848
    b08: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x848 · 0xffb00848
    b0c: 004a5a13  srli         x20, x20, 4
    b10: fffa0a13  addi         x20, x20, -1
    b14: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    b18: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    b1c: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    b20: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    b24: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    b28: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    b2c: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    b30: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    b34: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    b38: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    b3c: 84cc0c13  addi         x24, x24, -1972  # x24 = 0xffb0084c · riscv_local_mem + 0x84c
    b40: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x84c · 0xffb0084c
    b44: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_b48:
    b48: ffb50c37  lui          x24, 0xffb50  # x24 = 0xffb50000
    b4c: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb50028
    b50: 000c5a83  lhu          x21, 0(x24)  # 0xffb50028
    b54: 414a8b33  sub          x22, x21, x20
    b58: 010b1b13  slli         x22, x22, 16
    b5c: 010b5b13  srli         x22, x22, 16
    b60: 017b7663  bgeu         x22, x23, 0x00000b6c  # target 0x00000b6c
    b64: 0ff0000f  fence        0xf, 0xf
    b68: fe1ff06f  jal          x0, 0x00000b48  # target 0x00000b48
loc_b6c:
    b6c: 0ff0000f  fence        0xf, 0xf
    b70: 88100082  STALLWAIT    stall_res=8, wait_res=32  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR
    b74: 788ff001  SETADCXX     CntSetMask=1, x_end2=255, x_start=0
    b78: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    b7c: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    b80: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    b84: 8810000a  STALLWAIT    stall_res=8, wait_res=2  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0
    b88: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    b8c: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    b90: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    b94: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    b98: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    b9c: 01507033  and          x0, x0, x21
    ba0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    ba4: 84ca8a93  addi         x21, x21, -1972  # x21 = 0xffb0084c · riscv_local_mem + 0x84c
    ba8: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x84c · 0xffb0084c
    bac: 001a0a13  addi         x20, x20, 1
    bb0: 010a1a13  slli         x20, x20, 16
    bb4: 010a5a13  srli         x20, x20, 16
    bb8: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x84c · 0xffb0084c; write runtime value
    bbc: ffb50ab7  lui          x21, 0xffb50  # x21 = 0xffb50000
    bc0: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb50020
    bc4: 014aa023  sw           x20, 0(x21)  # 0xffb50020; write runtime value
    bc8: 0ff0000f  fence        0xf, 0xf
    bcc: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    bd0: 848c0c13  addi         x24, x24, -1976  # x24 = 0xffb00848 · riscv_local_mem + 0x848
    bd4: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x848 · 0xffb00848
    bd8: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    bdc: 015a0a33  add          x20, x20, x21
    be0: 00056b37  lui          x22, 0x00056  # x22 = 0x00056000
    be4: 980b0b13  addi         x22, x22, -1664  # x22 = 0x00055980
    be8: 016a6663  bltu         x20, x22, 0x00000bf4  # target 0x00000bf4
    bec: 00030bb7  lui          x23, 0x00030  # x23 = 0x00030000 · arc_apb_reset_unit + 0x0
    bf0: 417a0a33  sub          x20, x20, x23
loc_bf4:
    bf4: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    bf8: 848c0c13  addi         x24, x24, -1976  # x24 = 0xffb00848 · riscv_local_mem + 0x848
    bfc: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x848 · 0xffb00848; write runtime value
    c00: 00130313  addi         x6, x6, 1
    c04: eddff06f  jal          x0, 0x00000ae0  # target 0x00000ae0
loc_c08:
    c08: 3d40006f  jal          x0, 0x00000fdc  # target 0x00000fdc
loc_c0c:
    c0c: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    c10: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_c14:
    c14: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    c18: 0feafa93  andi         x21, x21, 254
    c1c: 000a8663  beq          x21, x0, 0x00000c28  # target 0x00000c28
    c20: 0ff0000f  fence        0xf, 0xf
    c24: ff1ff06f  jal          x0, 0x00000c14  # target 0x00000c14
loc_c28:
    c28: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    c2c: d500011e  RMWCIB2      Mask=64, Data=0, CfgRegAddr=71  # cfg[71] (current thread StateID); THCON_SEC0_REG1_Unp_LF8_4b_exp = 0
    c30: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    c34: 100a0a13  addi         x20, x20, 256  # x20 = 0xffef0100 · cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor
    c38: 01500a93  addi         x21, x0, 21  # x21 = 0x00000015
    c3c: 015a2023  sw           x21, 0(x20)  # cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor · 0xffef0100; write 0x00000015; cfg[64] (bank 0); THCON_SEC0_REG0_TileDescriptor = 21
    c40: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
    c44: 001a8a93  addi         x21, x21, 1  # x21 = 0x00040001
    c48: 015a2223  sw           x21, 4(x20)  # cfg[65] (bank 0) (undocumented index) · 0xffef0104; write 0x00040001; cfg[65] (bank 0) · fields not in ttsim
    c4c: 000a2423  sw           x0, 8(x20)  # cfg[66] (bank 0) (undocumented index) · 0xffef0108; write 0x00000000; cfg[66] (bank 0) · fields not in ttsim
    c50: 000a2623  sw           x0, 12(x20)  # cfg[67] (bank 0) (undocumented index) · 0xffef010c; write 0x00000000; cfg[67] (bank 0) · fields not in ttsim
    c54: 02500a93  addi         x21, x0, 37  # x21 = 0x00000025
    c58: 035a2023  sw           x21, 32(x20)  # cfg[72] (bank 0) · THCON_SEC0_REG2_Out_data_format, THCON_SEC0_REG2_Throttle_mode, THCON_SEC0_REG2_Context_count, THCON_SEC0_REG2_Haloize_mode, THCON_SEC0_REG2_Tileize_mode, THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC0_REG2_Unpack_If_Sel, THCON_SEC0_REG2_Upsample_rate, THCON_SEC0_REG2_Ovrd_data_format, THCON_SEC0_REG2_Upsample_and_interleave, THCON_SEC0_REG2_Shift_amount_cntx0, THCON_SEC0_REG2_Shift_amount_cntx1, THCON_SEC0_REG2_Shift_amount_cntx2, THCON_SEC0_REG2_Shift_amount_cntx3 · 0xffef0120; write 0x00000025; cfg[72] (bank 0); THCON_SEC0_REG2_Out_data_format = 5; THCON_SEC0_REG2_Throttle_mode = 2; THCON_SEC0_REG2_Context_count = 0; THCON_SEC0_REG2_Haloize_mode = 0; THCON_SEC0_REG2_Tileize_mode = 0; THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC0_REG2_Unpack_If_Sel = 0; THCON_SEC0_REG2_Upsample_rate = 0; THCON_SEC0_REG2_Ovrd_data_format = 0; THCON_SEC0_REG2_Upsample_and_interleave = 0; THCON_SEC0_REG2_Shift_amount_cntx0 = 0; THCON_SEC0_REG2_Shift_amount_cntx1 = 0; THCON_SEC0_REG2_Shift_amount_cntx2 = 0; THCON_SEC0_REG2_Shift_amount_cntx3 = 0
    c5c: 00300a93  addi         x21, x0, 3  # x21 = 0x00000003
    c60: 035a2223  sw           x21, 36(x20)  # cfg[73] (bank 0) · THCON_SEC0_REG2_Disable_zero_compress_cntx0, THCON_SEC0_REG2_Disable_zero_compress_cntx1, THCON_SEC0_REG2_Disable_zero_compress_cntx2, THCON_SEC0_REG2_Disable_zero_compress_cntx3, THCON_SEC0_REG2_Unpack_if_sel_cntx0, THCON_SEC0_REG2_Unpack_if_sel_cntx1, THCON_SEC0_REG2_Unpack_if_sel_cntx2, THCON_SEC0_REG2_Unpack_if_sel_cntx3, THCON_SEC0_REG2_Force_shared_exp, THCON_SEC0_REG2_Context_count_non_log2, THCON_SEC0_REG2_Context_count_non_log2_en, THCON_SEC0_REG2_Disable_zero_compress_cntx4, THCON_SEC0_REG2_Disable_zero_compress_cntx5, THCON_SEC0_REG2_Disable_zero_compress_cntx6, THCON_SEC0_REG2_Disable_zero_compress_cntx7, THCON_SEC0_REG2_Unpack_if_sel_cntx4, THCON_SEC0_REG2_Unpack_if_sel_cntx5, THCON_SEC0_REG2_Unpack_if_sel_cntx6, THCON_SEC0_REG2_Unpack_if_sel_cntx7, THCON_SEC0_REG2_Metadata_x_end · 0xffef0124; write 0x00000003; cfg[73] (bank 0); THCON_SEC0_REG2_Disable_zero_compress_cntx0 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx1 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx2 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx3 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx0 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx1 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx2 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx3 = 0; THCON_SEC0_REG2_Force_shared_exp = 0; THCON_SEC0_REG2_Context_count_non_log2 = 0; THCON_SEC0_REG2_Context_count_non_log2_en = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx4 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx5 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx6 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx7 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx4 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx5 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx6 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx7 = 0; THCON_SEC0_REG2_Metadata_x_end = 0
    c64: 020a2423  sw           x0, 40(x20)  # cfg[74] (bank 0) · THCON_SEC0_REG2_Unpack_limit_address · 0xffef0128; write 0x00000000; cfg[74] (bank 0); THCON_SEC0_REG2_Unpack_limit_address = 0
    c68: 020a2623  sw           x0, 44(x20)  # cfg[75] (bank 0) · THCON_SEC0_REG2_Unpack_fifo_size · 0xffef012c; write 0x00000000; cfg[75] (bank 0); THCON_SEC0_REG2_Unpack_fifo_size = 0
    c6c: fa0a2823  sw           x0, -80(x20)  # cfg[44] (bank 0) · UNP0_ADDR_CTRL_XY_REG_0_Xstride, UNP0_ADDR_CTRL_XY_REG_0_Ystride · 0xffef00b0; write 0x00000000; cfg[44] (bank 0); UNP0_ADDR_CTRL_XY_REG_0_Xstride = 0; UNP0_ADDR_CTRL_XY_REG_0_Ystride = 0
    c70: fa0a2a23  sw           x0, -76(x20)  # cfg[45] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_0_Zstride, UNP0_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef00b4; write 0x00000000; cfg[45] (bank 0); UNP0_ADDR_CTRL_ZW_REG_0_Zstride = 0; UNP0_ADDR_CTRL_ZW_REG_0_Wstride = 0
    c74: 00200ab7  lui          x21, 0x00200  # x21 = 0x00200000
    c78: 002a8a93  addi         x21, x21, 2  # x21 = 0x00200002
    c7c: ff5a2023  sw           x21, -32(x20)  # cfg[56] (bank 0) · UNP0_ADDR_CTRL_XY_REG_1_Xstride, UNP0_ADDR_CTRL_XY_REG_1_Ystride · 0xffef00e0; write 0x00200002; cfg[56] (bank 0); UNP0_ADDR_CTRL_XY_REG_1_Xstride = 2; UNP0_ADDR_CTRL_XY_REG_1_Ystride = 32
    c80: 20000a93  addi         x21, x0, 512  # x21 = 0x00000200
    c84: ff5a2223  sw           x21, -28(x20)  # cfg[57] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_1_Zstride, UNP0_ADDR_CTRL_ZW_REG_1_Wstride · 0xffef00e4; write 0x00000200; cfg[57] (bank 0); UNP0_ADDR_CTRL_ZW_REG_1_Zstride = 512; UNP0_ADDR_CTRL_ZW_REG_1_Wstride = 0
    c88: fc0a2023  sw           x0, -64(x20)  # cfg[48] (bank 0) · UNP0_ADDR_BASE_REG_0_Base · 0xffef00c0; write 0x00000000; cfg[48] (bank 0); UNP0_ADDR_BASE_REG_0_Base = 0
    c8c: fc0a2223  sw           x0, -60(x20)  # cfg[49] (bank 0) · UNP0_ADDR_BASE_REG_1_Base · 0xffef00c4; write 0x00000000; cfg[49] (bank 0); UNP0_ADDR_BASE_REG_1_Base = 0
    c90: 10000a93  addi         x21, x0, 256  # x21 = 0x00000100
    c94: fd5a2423  sw           x21, -56(x20)  # cfg[50] (bank 0) · UNP0_FORCED_SHARED_EXP_shared_exp, UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr · 0xffef00c8; write 0x00000100; cfg[50] (bank 0); UNP0_FORCED_SHARED_EXP_shared_exp = 0; UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr = 1
    c98: fc0a2a23  sw           x0, -44(x20)  # cfg[53] (bank 0) · UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val · 0xffef00d4; write 0x00000000; cfg[53] (bank 0); UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val = 0
    c9c: 00400ab7  lui          x21, 0x00400  # x21 = 0x00400000
    ca0: 040a8a93  addi         x21, x21, 64  # x21 = 0x00400040
    ca4: 055a2823  sw           x21, 80(x20)  # cfg[84] (bank 0) · THCON_SEC0_REG5_Dest_cntx0_address, THCON_SEC0_REG5_Dest_cntx1_address · 0xffef0150; write 0x00400040; cfg[84] (bank 0); THCON_SEC0_REG5_Dest_cntx0_address = 64; THCON_SEC0_REG5_Dest_cntx1_address = 64
    ca8: 01000ab7  lui          x21, 0x01000  # x21 = 0x01000000
    cac: 100a8a93  addi         x21, x21, 256  # x21 = 0x01000100
    cb0: 055a2c23  sw           x21, 88(x20)  # cfg[86] (bank 0) · THCON_SEC0_REG5_Tile_x_dim_cntx0, THCON_SEC0_REG5_Tile_x_dim_cntx1 · 0xffef0158; write 0x01000100; cfg[86] (bank 0); THCON_SEC0_REG5_Tile_x_dim_cntx0 = 256; THCON_SEC0_REG5_Tile_x_dim_cntx1 = 256
    cb4: 060a2823  sw           x0, 112(x20)  # cfg[92] (bank 0) · THCON_SEC0_REG7_Offset_address, THCON_SEC0_REG7_Unpack_data_format_cntx0, THCON_SEC0_REG7_Unpack_out_data_format_cntx0, THCON_SEC0_REG7_Unpack_data_format_cntx4, THCON_SEC0_REG7_Unpack_out_data_format_cntx4 · 0xffef0170; write 0x00000000; cfg[92] (bank 0); THCON_SEC0_REG7_Offset_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx4 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx4 = 0
    cb8: 060a2a23  sw           x0, 116(x20)  # cfg[93] (bank 0) · THCON_SEC0_REG7_Offset_cntx1_address, THCON_SEC0_REG7_Unpack_data_format_cntx1, THCON_SEC0_REG7_Unpack_out_data_format_cntx1, THCON_SEC0_REG7_Unpack_data_format_cntx5, THCON_SEC0_REG7_Unpack_out_data_format_cntx5 · 0xffef0174; write 0x00000000; cfg[93] (bank 0); THCON_SEC0_REG7_Offset_cntx1_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx5 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx5 = 0
    cbc: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    cc0: 820a8a93  addi         x21, x21, -2016  # x21 = 0xffb00820 · riscv_local_mem + 0x820
    cc4: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x820 · 0xffb00820
    cc8: 004a5a13  srli         x20, x20, 4
    ccc: fffa0a13  addi         x20, x20, -1
    cd0: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    cd4: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    cd8: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    cdc: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    ce0: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    ce4: c8140012  SETC16       setc16_reg=5, setc16_value=4  # thread_cfg[5] (current thread); SRCA_SET_Base = 0; SRCA_SET_SetOvrdWithAddr = 1
    ce8: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    cec: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    cf0: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    cf4: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    cf8: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    cfc: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    d00: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    d04: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    d08: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    d0c: 01507033  and          x0, x0, x21
    d10: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    d14: 00400a93  addi         x21, x0, 4  # x21 = 0x00000004
    d18: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000004
    d1c: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
    d20: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000001
    d24: 42008ab7  lui          x21, 0x42008  # x21 = 0x42008000
    d28: 0c1a8a93  addi         x21, x21, 193  # x21 = 0x420080c1
    d2c: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x420080c1; MOP template instruction · UNPACR Unpack_block_selection=0, AddrMode=1, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    d30: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    d34: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x02000000; MOP template instruction · NOP
    d38: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    d3c: 43800ab7  lui          x21, 0x43800  # x21 = 0x43800000
    d40: 101a8a93  addi         x21, x21, 257  # x21 = 0x43800101
    d44: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    d48: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    d4c: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    d50: 43800ab7  lui          x21, 0x43800  # x21 = 0x43800000
    d54: 101a8a93  addi         x21, x21, 257  # x21 = 0x43800101
    d58: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    d5c: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    d60: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    d64: 824c0c13  addi         x24, x24, -2012  # x24 = 0xffb00824 · riscv_local_mem + 0x824
    d68: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x824 · 0xffb00824
    d6c: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_d70:
    d70: ffb4dc37  lui          x24, 0xffb4d  # x24 = 0xffb4d000
    d74: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb4d028
    d78: 000c5a83  lhu          x21, 0(x24)  # 0xffb4d028
    d7c: 414a8b33  sub          x22, x21, x20
    d80: 010b1b13  slli         x22, x22, 16
    d84: 010b5b13  srli         x22, x22, 16
    d88: 017b7663  bgeu         x22, x23, 0x00000d94  # target 0x00000d94
    d8c: 0ff0000f  fence        0xf, 0xf
    d90: fe1ff06f  jal          x0, 0x00000d70  # target 0x00000d70
loc_d94:
    d94: 0ff0000f  fence        0xf, 0xf
    d98: 88100082  STALLWAIT    stall_res=8, wait_res=32  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR
    d9c: 788ff001  SETADCXX     CntSetMask=1, x_end2=255, x_start=0
    da0: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    da4: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    da8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    dac: 8810000a  STALLWAIT    stall_res=8, wait_res=2  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0
    db0: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    db4: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    db8: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    dbc: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    dc0: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    dc4: 01507033  and          x0, x0, x21
    dc8: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    dcc: 824a8a93  addi         x21, x21, -2012  # x21 = 0xffb00824 · riscv_local_mem + 0x824
    dd0: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x824 · 0xffb00824
    dd4: 001a0a13  addi         x20, x20, 1
    dd8: 010a1a13  slli         x20, x20, 16
    ddc: 010a5a13  srli         x20, x20, 16
    de0: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x824 · 0xffb00824; write runtime value
    de4: ffb4dab7  lui          x21, 0xffb4d  # x21 = 0xffb4d000
    de8: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb4d020
    dec: 014aa023  sw           x20, 0(x21)  # 0xffb4d020; write runtime value
    df0: 0ff0000f  fence        0xf, 0xf
    df4: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    df8: 820c0c13  addi         x24, x24, -2016  # x24 = 0xffb00820 · riscv_local_mem + 0x820
    dfc: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x820 · 0xffb00820
    e00: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    e04: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    e08: 015a0a33  add          x20, x20, x21
    e0c: 00025b37  lui          x22, 0x00025  # x22 = 0x00025000
    e10: 880b0b13  addi         x22, x22, -1920  # x22 = 0x00024880
    e14: 016a6663  bltu         x20, x22, 0x00000e20  # target 0x00000e20
    e18: 00002bb7  lui          x23, 0x00002  # x23 = 0x00002000
    e1c: 417a0a33  sub          x20, x20, x23
loc_e20:
    e20: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    e24: 820c0c13  addi         x24, x24, -2016  # x24 = 0xffb00820 · riscv_local_mem + 0x820
    e28: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x820 · 0xffb00820; write runtime value
    e2c: 00008067  jalr         x0, 0(x1)
loc_e30:
    e30: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    e34: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_e38:
    e38: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    e3c: 0feafa93  andi         x21, x21, 254
    e40: 000a8663  beq          x21, x0, 0x00000e4c  # target 0x00000e4c
    e44: 0ff0000f  fence        0xf, 0xf
    e48: ff1ff06f  jal          x0, 0x00000e38  # target 0x00000e38
loc_e4c:
    e4c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    e50: 838a8a93  addi         x21, x21, -1992  # x21 = 0xffb00838 · riscv_local_mem + 0x838
    e54: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x838 · 0xffb00838
    e58: 004a5a13  srli         x20, x20, 4
    e5c: fffa0a13  addi         x20, x20, -1
    e60: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    e64: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    e68: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    e6c: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    e70: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    e74: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_e78:
    e78: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    e7c: 0feafa93  andi         x21, x21, 254
    e80: 000a8663  beq          x21, x0, 0x00000e8c  # target 0x00000e8c
    e84: 0ff0000f  fence        0xf, 0xf
    e88: ff1ff06f  jal          x0, 0x00000e78  # target 0x00000e78
loc_e8c:
    e8c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    e90: 840a8a93  addi         x21, x21, -1984  # x21 = 0xffb00840 · riscv_local_mem + 0x840
    e94: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x840 · 0xffb00840
    e98: 004a5a13  srli         x20, x20, 4
    e9c: fffa0a13  addi         x20, x20, -1
    ea0: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    ea4: 1f0a8a93  addi         x21, x21, 496  # x21 = 0xffef01f0 · cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address
    ea8: 014aa023  sw           x20, 0(x21)  # cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address · 0xffef01f0; write runtime value; cfg[124] (bank 0); THCON_SEC1_REG3_Base_address = runtime
    eac: 014aa223  sw           x20, 4(x21)  # cfg[125] (bank 0) · THCON_SEC1_REG3_Base_cntx1_address · 0xffef01f4; write runtime value; cfg[125] (bank 0); THCON_SEC1_REG3_Base_cntx1_address = runtime
    eb0: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    eb4: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    eb8: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    ebc: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    ec0: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    ec4: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    ec8: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    ecc: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    ed0: 844c0c13  addi         x24, x24, -1980  # x24 = 0xffb00844 · riscv_local_mem + 0x844
    ed4: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x844 · 0xffb00844
    ed8: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_edc:
    edc: ffb4bc37  lui          x24, 0xffb4b  # x24 = 0xffb4b000
    ee0: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb4b028
    ee4: 000c5a83  lhu          x21, 0(x24)  # 0xffb4b028
    ee8: 414a8b33  sub          x22, x21, x20
    eec: 010b1b13  slli         x22, x22, 16
    ef0: 010b5b13  srli         x22, x22, 16
    ef4: 017b7663  bgeu         x22, x23, 0x00000f00  # target 0x00000f00
    ef8: 0ff0000f  fence        0xf, 0xf
    efc: fe1ff06f  jal          x0, 0x00000edc  # target 0x00000edc
loc_f00:
    f00: 0ff0000f  fence        0xf, 0xf
    f04: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    f08: 83cc0c13  addi         x24, x24, -1988  # x24 = 0xffb0083c · riscv_local_mem + 0x83c
    f0c: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x83c · 0xffb0083c
    f10: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_f14:
    f14: ffb4ac37  lui          x24, 0xffb4a  # x24 = 0xffb4a000
    f18: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb4a028
    f1c: 000c5a83  lhu          x21, 0(x24)  # 0xffb4a028
    f20: 414a8b33  sub          x22, x21, x20
    f24: 010b1b13  slli         x22, x22, 16
    f28: 010b5b13  srli         x22, x22, 16
    f2c: 017b7663  bgeu         x22, x23, 0x00000f38  # target 0x00000f38
    f30: 0ff0000f  fence        0xf, 0xf
    f34: fe1ff06f  jal          x0, 0x00000f14  # target 0x00000f14
loc_f38:
    f38: 0ff0000f  fence        0xf, 0xf
    f3c: 88100182  STALLWAIT    stall_res=8, wait_res=96  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR | Wait.SRCB_CLR
    f40: 78bff001  SETADCXX     CntSetMask=1, x_end2=1023, x_start=0
    f44: 793ff001  SETADCXX     CntSetMask=2, x_end2=1023, x_start=0
    f48: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    f4c: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    f50: 0a000305  UNPACR       Unpack_block_selection=1, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    f54: 08000305  UNPACR       Unpack_block_selection=0, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    f58: 8810001a  STALLWAIT    stall_res=8, wait_res=6  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0 | Wait.UNPACK1
    f5c: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    f60: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    f64: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    f68: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    f6c: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    f70: 01507033  and          x0, x0, x21
    f74: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    f78: 83ca8a93  addi         x21, x21, -1988  # x21 = 0xffb0083c · riscv_local_mem + 0x83c
    f7c: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x83c · 0xffb0083c
    f80: 001a0a13  addi         x20, x20, 1
    f84: 010a1a13  slli         x20, x20, 16
    f88: 010a5a13  srli         x20, x20, 16
    f8c: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x83c · 0xffb0083c; write runtime value
    f90: ffb4aab7  lui          x21, 0xffb4a  # x21 = 0xffb4a000
    f94: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb4a020
    f98: 014aa023  sw           x20, 0(x21)  # 0xffb4a020; write runtime value
    f9c: 0ff0000f  fence        0xf, 0xf
    fa0: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    fa4: 838c0c13  addi         x24, x24, -1992  # x24 = 0xffb00838 · riscv_local_mem + 0x838
    fa8: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x838 · 0xffb00838
    fac: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    fb0: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    fb4: 015a0a33  add          x20, x20, x21
    fb8: 0001cb37  lui          x22, 0x0001c  # x22 = 0x0001c000
    fbc: 080b0b13  addi         x22, x22, 128  # x22 = 0x0001c080
    fc0: 016a6663  bltu         x20, x22, 0x00000fcc  # target 0x00000fcc
    fc4: 00004bb7  lui          x23, 0x00004  # x23 = 0x00004000
    fc8: 417a0a33  sub          x20, x20, x23
loc_fcc:
    fcc: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    fd0: 838c0c13  addi         x24, x24, -1992  # x24 = 0xffb00838 · riscv_local_mem + 0x838
    fd4: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x838 · 0xffb00838; write runtime value
    fd8: 00008067  jalr         x0, 0(x1)
    fdc:           j FW_TRISC0+4   # return to firmware, linked at install
