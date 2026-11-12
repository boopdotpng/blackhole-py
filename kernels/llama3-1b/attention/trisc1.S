# llama3 1b decode: attention, trisc1. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (96): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5 7,6 7,7 7,8 7,9 7,10 7,11 10,2 10,3 10,4 10,5 10,6 10,7 10,8 10,9 10,10 10,11 11,2 11,3 11,4 11,5 11,6 11,7 11,8 11,9 11,10 11,11 12,2 12,3 12,4 12,5 12,6 12,7
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=attention_e2e_q_compact, 0x79c=attention_e2e_k_compact, 0x7a0=attention_e2e_v_compact, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0xe900=e2e_attention_partials, 0xe904=attention_core, 0xe908=attention_phase
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: 100002c4  REPLAY       start_idx=0, len=11, execute_while_loading=0, load_mode=1
      4: c0038001  SFPLOAD      lreg_ind=0, instr_mod0=0, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0; Record replay[0]; not executed here
      8: c0438101  SFPLOAD      lreg_ind=1, instr_mod0=0, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L1; Record replay[1]; not executed here
      c: c0838201  SFPLOAD      lreg_ind=2, instr_mod0=0, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L2; Record replay[2]; not executed here
     10: c0c38301  SFPLOAD      lreg_ind=3, instr_mod0=0, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L3; Record replay[3]; not executed here
     14: 1800a502  SFPMUL       lreg_src_a=0, lreg_src_b=2, lreg_src_c=9, lreg_dest=4, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L2; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L4; Record replay[4]; not executed here
     18: 3c000002  SFPNOP         # Record replay[5]; not executed here
     1c: 1004d142  SFPMAD       lreg_src_a=1, lreg_src_b=3, lreg_src_c=4, lreg_dest=5, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L3; lreg_src_c: L4; lreg_dest: L5; Record replay[6]; not executed here
     20: 3c000002  SFPNOP         # Record replay[7]; not executed here
     24: 38001546  SFPSTOCHRND  rnd_mode=0, imm8_math=0, lreg_src_b=0, lreg_src_c=5, lreg_dest=5, instr_mod1=1  # lreg_src_b: L0; lreg_src_c: L5; lreg_dest: L5; Record replay[8]; not executed here
     28: c9438001  SFPSTORE     lreg_ind=5, instr_mod0=0, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L5; Record replay[9]; not executed here
     2c: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0  # Record replay[10]; not executed here
     30: 100b0104  REPLAY       start_idx=11, len=4, execute_while_loading=0, load_mode=1
     34: c4280001  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=0  # lreg_ind: L0; Record replay[11]; not executed here
     38: c4200001  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=0  # lreg_ind: L0; Record replay[12]; not executed here
     3c: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0; Record replay[13]; not executed here
     40: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0  # Record replay[14]; not executed here
     44: 0000f337  lui          x6, 0x0000f  # x6 = 0x0000f000
     48: 90830313  addi         x6, x6, -1784  # x6 = 0x0000e908
     4c: 00032203  lw           x4, 0(x6)  # param attention_phase; 0x0000e908
     50: 79000413  addi         x8, x0, 1936  # x8 = 0x00000790
     54: 00042303  lw           x6, 0(x8)  # param kv_blocks; 0x00000790
     58: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
     5c: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
     60: 0063fa63  bgeu         x7, x6, 0x00000074  # target 0x00000074
     64: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     68: 08000393  addi         x7, x0, 128  # x7 = 0x00000080
     6c: 0063f463  bgeu         x7, x6, 0x00000074  # target 0x00000074
     70: 00c00293  addi         x5, x0, 12  # x5 = 0x0000000c
loc_74:
     74: 165270e3  bgeu         x4, x5, 0x000009d4  # target 0x000009d4
     78: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
     7c: c8380022  SETC16       setc16_reg=14, setc16_value=8  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 8; ADDR_MOD_AB_SEC2_SrcACR = 0; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 0; ADDR_MOD_AB_SEC2_SrcBCR = 0; ADDR_MOD_AB_SEC2_SrcBClear = 0
     80: c8780022  SETC16       setc16_reg=30, setc16_value=8  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 8; ADDR_MOD_DST_SEC2_DestCR = 0; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 0; ADDR_MOD_DST_SEC2_FidelityClear = 0
     84: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
     88: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
     8c: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
     90: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
     94: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
     98: 00507033  and          x0, x0, x5
     9c: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
     a0: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     a4: 00522023  sw           x5, 0(x4)  # MOP_CFG · 0xffb80000; write 0x00000004
     a8: 00200293  addi         x5, x0, 2  # x5 = 0x00000002
     ac: 00522223  sw           x5, 4(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
     b0: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     b4: 00522423  sw           x5, 8(x4)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
     b8: 37c002b7  lui          x5, 0x37c00  # x5 = 0x37c00000
     bc: 00328293  addi         x5, x5, 3  # x5 = 0x37c00003
     c0: 00522623  sw           x5, 12(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37c00003; MOP template instruction · SETRWC clear_ab_vld=3, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=3
     c4: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     c8: 00522823  sw           x5, 16(x4)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
     cc: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
     d0: 00522a23  sw           x5, 20(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
     d4: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     d8: 00522c23  sw           x5, 24(x4)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
     dc: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
     e0: 00522e23  sw           x5, 28(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
     e4: 02522023  sw           x5, 32(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
     e8: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
     ec: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
     f0: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
     f4: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
     f8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
     fc: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    100: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    104: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    108: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    10c: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    110: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    114: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    118: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    11c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    120: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    124: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    128: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    12c: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    130: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    134: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    138: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    13c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    140: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    144: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    148: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    14c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    150: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    154: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    158: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    15c: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    160: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    164: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    168: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    16c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    170: 3c000002  SFPNOP
    174: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    178: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    17c: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    180: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    184: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    188: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    18c: 01507033  and          x0, x0, x21
    190: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    194: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
    198: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000001
    19c: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    1a0: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000008
    1a4: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    1a8: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
    1ac: 37120ab7  lui          x21, 0x37120  # x21 = 0x37120000
    1b0: 004a8a93  addi         x21, x21, 4  # x21 = 0x37120004
    1b4: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    1b8: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    1bc: 04000ab7  lui          x21, 0x04000  # x21 = 0x04000000
    1c0: 0b0a8a93  addi         x21, x21, 176  # x21 = 0x040000b0
    1c4: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x040000b0; MOP template instruction · REPLAY start_idx=0, len=11, execute_while_loading=0, load_mode=0
    1c8: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    1cc: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    1d0: 04000ab7  lui          x21, 0x04000  # x21 = 0x04000000
    1d4: 0b0a8a93  addi         x21, x21, 176  # x21 = 0x040000b0
    1d8: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x040000b0; MOP template instruction · REPLAY start_idx=0, len=11, execute_while_loading=0, load_mode=0
    1dc: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x040000b0; MOP template instruction · REPLAY start_idx=0, len=11, execute_while_loading=0, load_mode=0
    1e0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1e4: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1e8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1ec: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1f0: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    1f4: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    1f8: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    1fc: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    200: 79000313  addi         x6, x0, 1936  # x6 = 0x00000790
    204: 00032203  lw           x4, 0(x6)  # param kv_blocks; 0x00000790
    208: fff20293  addi         x5, x4, -1
    20c: 0000f437  lui          x8, 0x0000f  # x8 = 0x0000f000
    210: 90840413  addi         x8, x8, -1784  # x8 = 0x0000e908
    214: 00042303  lw           x6, 0(x8)  # param attention_phase; 0x0000e908
    218: 79000513  addi         x10, x0, 1936  # x10 = 0x00000790
    21c: 00052403  lw           x8, 0(x10)  # param kv_blocks; 0x00000790
    220: 00100393  addi         x7, x0, 1  # x7 = 0x00000001
    224: 00400493  addi         x9, x0, 4  # x9 = 0x00000004
    228: 0084fa63  bgeu         x9, x8, 0x0000023c  # target 0x0000023c
    22c: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
    230: 08000493  addi         x9, x0, 128  # x9 = 0x00000080
    234: 0084f463  bgeu         x9, x8, 0x0000023c  # target 0x0000023c
    238: 00c00393  addi         x7, x0, 12  # x7 = 0x0000000c
loc_23c:
    23c: 0272f433  remu         x8, x5, x7
    240: 0272d2b3  divu         x5, x5, x7
    244: 00640463  beq          x8, x6, 0x0000024c  # target 0x0000024c
    248: fff00293  addi         x5, x0, -1  # x5 = 0xffffffff
loc_24c:
    24c: 00720233  add          x4, x4, x7
    250: fff20213  addi         x4, x4, -1
    254: 40620233  sub          x4, x4, x6
    258: 02725233  divu         x4, x4, x7
    25c: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    260: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    264: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    268: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    26c: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    270: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    274: 3c000002  SFPNOP
    278: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    27c: 75c000ef  jal          x1, 0x000009d8  # target 0x000009d8; x1 = 0x00000280
    280: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    284: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    288: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    28c: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    290: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    294: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    298: 3c000002  SFPNOP
    29c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    2a0: 738000ef  jal          x1, 0x000009d8  # target 0x000009d8; x1 = 0x000002a4
    2a4: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    2a8: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    2ac: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    2b0: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    2b4: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    2b8: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    2bc: 3c000002  SFPNOP
    2c0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    2c4: 714000ef  jal          x1, 0x000009d8  # target 0x000009d8; x1 = 0x000002c8
    2c8: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    2cc: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    2d0: c8040502  SETC16       setc16_reg=1, setc16_value=320  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 320
    2d4: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    2d8: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    2dc: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    2e0: 3c000002  SFPNOP
    2e4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    2e8: 6f0000ef  jal          x1, 0x000009d8  # target 0x000009d8; x1 = 0x000002ec
    2ec: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    2f0: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    2f4: c8040402  SETC16       setc16_reg=1, setc16_value=256  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 256
    2f8: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    2fc: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    300: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    304: 3c000002  SFPNOP
    308: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    30c: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    310: 00400a13  addi         x20, x0, 4  # x20 = 0x00000004
loc_314:
    314: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
loc_318:
    318: c4280001  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=0  # lreg_ind: L0
    31c: c420fe01  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=16256  # lreg_ind: L0
    320: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    324: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    328: fffa8a93  addi         x21, x21, -1
    32c: fe0a96e3  bne          x21, x0, 0x00000318  # target 0x00000318
    330: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    334: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    338: fffa0a13  addi         x20, x20, -1
    33c: fc0a1ce3  bne          x20, x0, 0x00000314  # target 0x00000314
    340: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    344: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    348: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    34c: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    350: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    354: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    358: 3c000002  SFPNOP
    35c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    360: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    364: c4280001  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=0  # lreg_ind: L0
    368: c423fe01  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=65408  # lreg_ind: L0
    36c: c80f8301  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
    370: c80f8309  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=194  # lreg_ind: L0
    374: c80f8341  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=208  # lreg_ind: L0
    378: c80f8349  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=210  # lreg_ind: L0
    37c: c4280001  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=0  # lreg_ind: L0
    380: c4200001  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=0  # lreg_ind: L0
    384: c80f8401  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=256  # lreg_ind: L0
    388: c80f8409  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=258  # lreg_ind: L0
    38c: c80f8441  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=272  # lreg_ind: L0
    390: c80f8449  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=274  # lreg_ind: L0
    394: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    398: 00000313  addi         x6, x0, 0  # x6 = 0x00000000
    39c: 00020393  addi         x7, x4, 0
loc_3a0:
    3a0: 60737663  bgeu         x6, x7, 0x000009ac  # target 0x000009ac
    3a4: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    3a8: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    3ac: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    3b0: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    3b4: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    3b8: c8302002  SETC16       setc16_reg=12, setc16_value=2048  # thread_cfg[12] (current thread); ADDR_MOD_AB_SEC0_SrcAIncr = 0; ADDR_MOD_AB_SEC0_SrcACR = 0; ADDR_MOD_AB_SEC0_SrcAClear = 0; ADDR_MOD_AB_SEC0_SrcBIncr = 8; ADDR_MOD_AB_SEC0_SrcBCR = 0; ADDR_MOD_AB_SEC0_SrcBClear = 0
    3bc: c8700022  SETC16       setc16_reg=28, setc16_value=8  # thread_cfg[28] (current thread); ADDR_MOD_DST_SEC0_DestIncr = 8; ADDR_MOD_DST_SEC0_DestCR = 0; ADDR_MOD_DST_SEC0_DestClear = 0; ADDR_MOD_DST_SEC0_DestCToCR = 0; ADDR_MOD_DST_SEC0_FidelityIncr = 0; ADDR_MOD_DST_SEC0_FidelityClear = 0
    3c0: c8bc0002  SETC16       setc16_reg=47, setc16_value=0  # thread_cfg[47] (current thread); ADDR_MOD_BIAS_SEC0_BiasIncr = 0; ADDR_MOD_BIAS_SEC0_BiasClear = 0
    3c4: c8350082  SETC16       setc16_reg=13, setc16_value=16416  # thread_cfg[13] (current thread); ADDR_MOD_AB_SEC1_SrcAIncr = 32; ADDR_MOD_AB_SEC1_SrcACR = 0; ADDR_MOD_AB_SEC1_SrcAClear = 0; ADDR_MOD_AB_SEC1_SrcBIncr = 0; ADDR_MOD_AB_SEC1_SrcBCR = 1; ADDR_MOD_AB_SEC1_SrcBClear = 0
    3c8: c8740022  SETC16       setc16_reg=29, setc16_value=8  # thread_cfg[29] (current thread); ADDR_MOD_DST_SEC1_DestIncr = 8; ADDR_MOD_DST_SEC1_DestCR = 0; ADDR_MOD_DST_SEC1_DestClear = 0; ADDR_MOD_DST_SEC1_DestCToCR = 0; ADDR_MOD_DST_SEC1_FidelityIncr = 0; ADDR_MOD_DST_SEC1_FidelityClear = 0
    3cc: c8c00002  SETC16       setc16_reg=48, setc16_value=0  # thread_cfg[48] (current thread); ADDR_MOD_BIAS_SEC1_BiasIncr = 0; ADDR_MOD_BIAS_SEC1_BiasClear = 0
    3d0: c8398102  SETC16       setc16_reg=14, setc16_value=24640  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 0; ADDR_MOD_AB_SEC2_SrcACR = 1; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 32; ADDR_MOD_AB_SEC2_SrcBCR = 1; ADDR_MOD_AB_SEC2_SrcBClear = 0
    3d4: c8780022  SETC16       setc16_reg=30, setc16_value=8  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 8; ADDR_MOD_DST_SEC2_DestCR = 0; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 0; ADDR_MOD_DST_SEC2_FidelityClear = 0
    3d8: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
    3dc: c841c142  SETC16       setc16_reg=16, setc16_value=28752  # thread_cfg[16] (current thread); ADDR_MOD_AB_SEC4_SrcAIncr = 16; ADDR_MOD_AB_SEC4_SrcACR = 1; ADDR_MOD_AB_SEC4_SrcAClear = 0; ADDR_MOD_AB_SEC4_SrcBIncr = 48; ADDR_MOD_AB_SEC4_SrcBCR = 1; ADDR_MOD_AB_SEC4_SrcBClear = 0
    3e0: c8801002  SETC16       setc16_reg=32, setc16_value=1024  # thread_cfg[32] (current thread); ADDR_MOD_DST_SEC4_DestIncr = 0; ADDR_MOD_DST_SEC4_DestCR = 1; ADDR_MOD_DST_SEC4_DestClear = 0; ADDR_MOD_DST_SEC4_DestCToCR = 0; ADDR_MOD_DST_SEC4_FidelityIncr = 0; ADDR_MOD_DST_SEC4_FidelityClear = 0
    3e4: c8cc0002  SETC16       setc16_reg=51, setc16_value=0  # thread_cfg[51] (current thread); ADDR_MOD_BIAS_SEC4_BiasIncr = 0; ADDR_MOD_BIAS_SEC4_BiasClear = 0
    3e8: c8470302  SETC16       setc16_reg=17, setc16_value=49344  # thread_cfg[17] (current thread); ADDR_MOD_AB_SEC5_SrcAIncr = 0; ADDR_MOD_AB_SEC5_SrcACR = 1; ADDR_MOD_AB_SEC5_SrcAClear = 1; ADDR_MOD_AB_SEC5_SrcBIncr = 0; ADDR_MOD_AB_SEC5_SrcBCR = 1; ADDR_MOD_AB_SEC5_SrcBClear = 1
    3ec: c884b002  SETC16       setc16_reg=33, setc16_value=11264  # thread_cfg[33] (current thread); ADDR_MOD_DST_SEC5_DestIncr = 0; ADDR_MOD_DST_SEC5_DestCR = 1; ADDR_MOD_DST_SEC5_DestClear = 1; ADDR_MOD_DST_SEC5_DestCToCR = 0; ADDR_MOD_DST_SEC5_FidelityIncr = 1; ADDR_MOD_DST_SEC5_FidelityClear = 0
    3f0: c8d00002  SETC16       setc16_reg=52, setc16_value=0  # thread_cfg[52] (current thread); ADDR_MOD_BIAS_SEC5_BiasIncr = 0; ADDR_MOD_BIAS_SEC5_BiasClear = 0
    3f4: 40710000  ZEROACC      clear_mode=3, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=0
    3f8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    3fc: 10100204  REPLAY       start_idx=16, len=8, execute_while_loading=0, load_mode=1
    400: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[16]; not executed here
    404: 98010000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=1, dst=0  # Record replay[17]; not executed here
    408: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[18]; not executed here
    40c: 98020000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=2, dst=0  # Record replay[19]; not executed here
    410: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[20]; not executed here
    414: 98010000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=1, dst=0  # Record replay[21]; not executed here
    418: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[22]; not executed here
    41c: 98040000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=4, dst=0  # Record replay[23]; not executed here
    420: 10180204  REPLAY       start_idx=24, len=8, execute_while_loading=0, load_mode=1
    424: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[24]; not executed here
    428: 98010000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=1, dst=0  # Record replay[25]; not executed here
    42c: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[26]; not executed here
    430: 98020000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=2, dst=0  # Record replay[27]; not executed here
    434: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[28]; not executed here
    438: 98010000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=1, dst=0  # Record replay[29]; not executed here
    43c: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[30]; not executed here
    440: 98050000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=5, dst=0  # Record replay[31]; not executed here
    444: ffe80437  lui          x8, 0xffe80  # x8 = 0xffe80000 · tensix_pc_buf + 0x0
    448: 00440413  addi         x8, x8, 4  # x8 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    44c: 00042023  sw           x0, 0(x8)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    450: 00042483  lw           x9, 0(x8)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    454: 00907033  and          x0, x0, x9
    458: ffe80437  lui          x8, 0xffe80  # x8 = 0xffe80000 · tensix_pc_buf + 0x0
    45c: 00840413  addi         x8, x8, 8  # x8 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    460: 00042023  sw           x0, 0(x8)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    464: 00042483  lw           x9, 0(x8)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    468: 00907033  and          x0, x0, x9
    46c: ffb80437  lui          x8, 0xffb80  # x8 = 0xffb80000 · MOP_CFG
    470: 00100493  addi         x9, x0, 1  # x9 = 0x00000001
    474: 00942023  sw           x9, 0(x8)  # MOP_CFG · 0xffb80000; write 0x00000001
    478: 00200493  addi         x9, x0, 2  # x9 = 0x00000002
    47c: 00942223  sw           x9, 4(x8)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
    480: 020004b7  lui          x9, 0x02000  # x9 = 0x02000000
    484: 00942423  sw           x9, 8(x8)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
    488: 374004b7  lui          x9, 0x37400  # x9 = 0x37400000
    48c: 00f48493  addi         x9, x9, 15  # x9 = 0x3740000f
    490: 00942623  sw           x9, 12(x8)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x3740000f; MOP template instruction · SETRWC clear_ab_vld=1, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    494: 020004b7  lui          x9, 0x02000  # x9 = 0x02000000
    498: 00942823  sw           x9, 16(x8)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    49c: 040404b7  lui          x9, 0x04040  # x9 = 0x04040000
    4a0: 08048493  addi         x9, x9, 128  # x9 = 0x04040080
    4a4: 00942a23  sw           x9, 20(x8)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x04040080; MOP template instruction · REPLAY start_idx=16, len=8, execute_while_loading=0, load_mode=0
    4a8: 040604b7  lui          x9, 0x04060  # x9 = 0x04060000
    4ac: 08048493  addi         x9, x9, 128  # x9 = 0x04060080
    4b0: 00942c23  sw           x9, 24(x8)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    4b4: 00942e23  sw           x9, 28(x8)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    4b8: 02942023  sw           x9, 32(x8)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    4bc: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    4c0: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    4c4: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    4c8: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    4cc: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    4d0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    4d4: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    4d8: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    4dc: 0c531463  bne          x6, x5, 0x000005a4  # target 0x000005a4
    4e0: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    4e4: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    4e8: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    4ec: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    4f0: 3c000002  SFPNOP
    4f4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    4f8: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    4fc: 79400513  addi         x10, x0, 1940  # x10 = 0x00000794
    500: 00052403  lw           x8, 0(x10)  # param valid_columns; 0x00000794
    504: 712204b7  lui          x9, 0x71220  # x9 = 0x71220000
    508: 0084e4b3  or           x9, x9, x8
    50c: ffe40537  lui          x10, 0xffe40  # x10 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    510: 00952023  sw           x9, 0(x10)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    514: c5280001  SFPLOADI     lreg_ind=4, instr_mod0=10, imm16=0  # lreg_ind: L4
    518: c523fe01  SFPLOADI     lreg_ind=4, instr_mod0=8, imm16=65408  # lreg_ind: L4
    51c: c548003d  SFPLOADI     lreg_ind=5, instr_mod0=2, imm16=15  # lreg_ind: L5
    520: f8017c45  SFPAND       imm12_math=5, lreg_c=15, lreg_dest=1, instr_mod1=1  # lreg_c: L15 · lane ID (ttsim reset lane << 1); lreg_dest: L1
    524: e4000455  SFPIADD      imm12_math=0, lreg_c=1, lreg_dest=1, instr_mod1=5  # lreg_c: L1; lreg_dest: L1
    528: f00008c1  SFPMOV       imm12_math=0, lreg_c=2, lreg_dest=3, instr_mod1=0  # lreg_c: L2; lreg_dest: L3
    52c: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    530: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
    534: e40004e9  SFPIADD      imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=10  # lreg_c: L1; lreg_dest: L3
    538: c90f8001  SFPSTORE     lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L4
    53c: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    540: f8017c45  SFPAND       imm12_math=5, lreg_c=15, lreg_dest=1, instr_mod1=1  # lreg_c: L15 · lane ID (ttsim reset lane << 1); lreg_dest: L1
    544: e4004455  SFPIADD      imm12_math=1, lreg_c=1, lreg_dest=1, instr_mod1=5  # lreg_c: L1; lreg_dest: L1
    548: f00008c1  SFPMOV       imm12_math=0, lreg_c=2, lreg_dest=3, instr_mod1=0  # lreg_c: L2; lreg_dest: L3
    54c: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    550: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
    554: e40004e9  SFPIADD      imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=10  # lreg_c: L1; lreg_dest: L3
    558: c90f8009  SFPSTORE     lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L4
    55c: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    560: f8017c45  SFPAND       imm12_math=5, lreg_c=15, lreg_dest=1, instr_mod1=1  # lreg_c: L15 · lane ID (ttsim reset lane << 1); lreg_dest: L1
    564: e4040455  SFPIADD      imm12_math=16, lreg_c=1, lreg_dest=1, instr_mod1=5  # lreg_c: L1; lreg_dest: L1
    568: f00008c1  SFPMOV       imm12_math=0, lreg_c=2, lreg_dest=3, instr_mod1=0  # lreg_c: L2; lreg_dest: L3
    56c: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    570: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
    574: e40004e9  SFPIADD      imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=10  # lreg_c: L1; lreg_dest: L3
    578: c90f8041  SFPSTORE     lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L4
    57c: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    580: f8017c45  SFPAND       imm12_math=5, lreg_c=15, lreg_dest=1, instr_mod1=1  # lreg_c: L15 · lane ID (ttsim reset lane << 1); lreg_dest: L1
    584: e4044455  SFPIADD      imm12_math=17, lreg_c=1, lreg_dest=1, instr_mod1=5  # lreg_c: L1; lreg_dest: L1
    588: f00008c1  SFPMOV       imm12_math=0, lreg_c=2, lreg_dest=3, instr_mod1=0  # lreg_c: L2; lreg_dest: L3
    58c: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    590: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
    594: e40004e9  SFPIADD      imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=10  # lreg_c: L1; lreg_dest: L3
    598: c90f8049  SFPSTORE     lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L4
    59c: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    5a0: 88042002  STALLWAIT    stall_res=2, wait_res=2048  # stall_res: Stall.SYNC; wait_res: Wait.SFPU
loc_5a4:
    5a4: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    5a8: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    5ac: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    5b0: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    5b4: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    5b8: 3c000002  SFPNOP
    5bc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    5c0: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    5c4: c5280001  SFPLOADI     lreg_ind=4, instr_mod0=10, imm16=0  # lreg_ind: L4
    5c8: c520f801  SFPLOADI     lreg_ind=4, instr_mod0=8, imm16=15872  # lreg_ind: L4
    5cc: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    5d0: 18012402  SFPMUL       lreg_src_a=0, lreg_src_b=4, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    5d4: 3c000002  SFPNOP
    5d8: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    5dc: c04f8009  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L1
    5e0: 18052442  SFPMUL       lreg_src_a=1, lreg_src_b=4, lreg_src_c=9, lreg_dest=1, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L1
    5e4: 3c000002  SFPNOP
    5e8: c84f8009  SFPSTORE     lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L1
    5ec: c08f8041  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L2
    5f0: 18092482  SFPMUL       lreg_src_a=2, lreg_src_b=4, lreg_src_c=9, lreg_dest=2, instr_mod1=0  # lreg_src_a: L2; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L2
    5f4: 3c000002  SFPNOP
    5f8: c88f8041  SFPSTORE     lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L2
    5fc: c0cf8049  SFPLOAD      lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L3
    600: 180d24c2  SFPMUL       lreg_src_a=3, lreg_src_b=4, lreg_src_c=9, lreg_dest=3, instr_mod1=0  # lreg_src_a: L3; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L3
    604: 3c000002  SFPNOP
    608: c8cf8049  SFPSTORE     lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L3
    60c: 48000086  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=2, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L2
    610: 3c000002  SFPNOP
    614: 480004c6  SFPSWAP      imm12_math=0, lreg_src_c=1, lreg_dest=3, instr_mod1=1  # lreg_src_c: L1; lreg_dest: L3
    618: 3c000002  SFPNOP
    61c: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    620: 3c000002  SFPNOP
    624: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    628: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    62c: 3c000002  SFPNOP
    630: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    634: 3c000002  SFPNOP
    638: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    63c: 3c000002  SFPNOP
    640: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    644: 3c000002  SFPNOP
    648: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    64c: 3c000002  SFPNOP
    650: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    654: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    658: 3c000002  SFPNOP
    65c: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    660: 3c000002  SFPNOP
    664: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    668: 3c000002  SFPNOP
    66c: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    670: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    674: 3c000002  SFPNOP
    678: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    67c: 3c000002  SFPNOP
    680: c08f8301  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L2
    684: f00008c1  SFPMOV       imm12_math=0, lreg_c=2, lreg_dest=3, instr_mod1=0  # lreg_c: L2; lreg_dest: L3
    688: 48000086  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=2, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L2
    68c: 3c000002  SFPNOP
    690: c80f8301  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
    694: c80f8309  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=194  # lreg_ind: L0
    698: c80f8341  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=208  # lreg_ind: L0
    69c: c80f8349  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=210  # lreg_ind: L0
    6a0: 1002cd42  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=3, lreg_dest=5, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L3; lreg_dest: L5
    6a4: 3c000002  SFPNOP
    6a8: c94f8501  SFPSTORE     lreg_ind=5, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L5
    6ac: c94f8509  SFPSTORE     lreg_ind=5, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=322  # lreg_ind: L5
    6b0: c94f8541  SFPSTORE     lreg_ind=5, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=336  # lreg_ind: L5
    6b4: c94f8549  SFPSTORE     lreg_ind=5, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=338  # lreg_ind: L5
    6b8: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    6bc: c04f8301  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L1
    6c0: 1006c002  SFPMAD       lreg_src_a=1, lreg_src_b=11, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L0; lreg_dest: L0
    6c4: 3c000002  SFPNOP
    6c8: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    6cc: c00f8009  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L0
    6d0: c04f8309  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=194  # lreg_ind: L1
    6d4: 1006c002  SFPMAD       lreg_src_a=1, lreg_src_b=11, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L0; lreg_dest: L0
    6d8: 3c000002  SFPNOP
    6dc: c80f8009  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L0
    6e0: c00f8041  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L0
    6e4: c04f8341  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=208  # lreg_ind: L1
    6e8: 1006c002  SFPMAD       lreg_src_a=1, lreg_src_b=11, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L0; lreg_dest: L0
    6ec: 3c000002  SFPNOP
    6f0: c80f8041  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L0
    6f4: c00f8049  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L0
    6f8: c04f8349  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=210  # lreg_ind: L1
    6fc: 1006c002  SFPMAD       lreg_src_a=1, lreg_src_b=11, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L0; lreg_dest: L0
    700: 3c000002  SFPNOP
    704: c80f8049  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L0
    708: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    70c: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    710: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    714: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    718: 3c000002  SFPNOP
    71c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    720: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    724: 338000ef  jal          x1, 0x00000a5c  # target 0x00000a5c; x1 = 0x00000728
    728: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    72c: 330000ef  jal          x1, 0x00000a5c  # target 0x00000a5c; x1 = 0x00000730
    730: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    734: 328000ef  jal          x1, 0x00000a5c  # target 0x00000a5c; x1 = 0x00000738
    738: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    73c: 320000ef  jal          x1, 0x00000a5c  # target 0x00000a5c; x1 = 0x00000740
    740: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    744: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    748: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    74c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    750: 3c000002  SFPNOP
    754: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    758: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    75c: 394000ef  jal          x1, 0x00000af0  # target 0x00000af0; x1 = 0x00000760
    760: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    764: 38c000ef  jal          x1, 0x00000af0  # target 0x00000af0; x1 = 0x00000768
    768: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    76c: 384000ef  jal          x1, 0x00000af0  # target 0x00000af0; x1 = 0x00000770
    770: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    774: 37c000ef  jal          x1, 0x00000af0  # target 0x00000af0; x1 = 0x00000778
    778: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    77c: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    780: c04f8009  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L1
    784: c08f8041  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L2
    788: c0cf8049  SFPLOAD      lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L3
    78c: 14280802  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=2, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L2; lreg_dest: L0
    790: 3c000002  SFPNOP
    794: 14284c42  SFPADD       lreg_src_a=10, lreg_src_b=1, lreg_src_c=3, lreg_dest=1, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L1; lreg_src_c: L3; lreg_dest: L1
    798: 3c000002  SFPNOP
    79c: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    7a0: 3c000002  SFPNOP
    7a4: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    7a8: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    7ac: 3c000002  SFPNOP
    7b0: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    7b4: 3c000002  SFPNOP
    7b8: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    7bc: 3c000002  SFPNOP
    7c0: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    7c4: 3c000002  SFPNOP
    7c8: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    7cc: 3c000002  SFPNOP
    7d0: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    7d4: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    7d8: 3c000002  SFPNOP
    7dc: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    7e0: 3c000002  SFPNOP
    7e4: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    7e8: 3c000002  SFPNOP
    7ec: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    7f0: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    7f4: 3c000002  SFPNOP
    7f8: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    7fc: 3c000002  SFPNOP
    800: c08f8401  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=256  # lreg_ind: L2
    804: c0cf8501  SFPLOAD      lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L3
    808: 1008c002  SFPMAD       lreg_src_a=2, lreg_src_b=3, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L2; lreg_src_b: L3; lreg_src_c: L0; lreg_dest: L0
    80c: 3c000002  SFPNOP
    810: c80f8401  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=256  # lreg_ind: L0
    814: c80f8409  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=258  # lreg_ind: L0
    818: c80f8441  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=272  # lreg_ind: L0
    81c: c80f8449  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=274  # lreg_ind: L0
    820: c00f8101  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
    824: c04f8501  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L1
    828: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    82c: 3c000002  SFPNOP
    830: c80f8101  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
    834: c00f8109  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=66  # lreg_ind: L0
    838: c04f8509  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=322  # lreg_ind: L1
    83c: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    840: 3c000002  SFPNOP
    844: c80f8109  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=66  # lreg_ind: L0
    848: c00f8141  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=80  # lreg_ind: L0
    84c: c04f8541  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=336  # lreg_ind: L1
    850: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    854: 3c000002  SFPNOP
    858: c80f8141  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=80  # lreg_ind: L0
    85c: c00f8149  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=82  # lreg_ind: L0
    860: c04f8549  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=338  # lreg_ind: L1
    864: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    868: 3c000002  SFPNOP
    86c: c80f8149  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=82  # lreg_ind: L0
    870: c00f8201  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
    874: c04f8501  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L1
    878: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    87c: 3c000002  SFPNOP
    880: c80f8201  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
    884: c00f8209  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=130  # lreg_ind: L0
    888: c04f8509  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=322  # lreg_ind: L1
    88c: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    890: 3c000002  SFPNOP
    894: c80f8209  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=130  # lreg_ind: L0
    898: c00f8241  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=144  # lreg_ind: L0
    89c: c04f8541  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=336  # lreg_ind: L1
    8a0: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    8a4: 3c000002  SFPNOP
    8a8: c80f8241  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=144  # lreg_ind: L0
    8ac: c00f8249  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=146  # lreg_ind: L0
    8b0: c04f8549  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=338  # lreg_ind: L1
    8b4: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    8b8: 3c000002  SFPNOP
    8bc: c80f8249  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=146  # lreg_ind: L0
    8c0: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    8c4: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    8c8: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    8cc: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    8d0: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    8d4: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    8d8: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    8dc: c8302002  SETC16       setc16_reg=12, setc16_value=2048  # thread_cfg[12] (current thread); ADDR_MOD_AB_SEC0_SrcAIncr = 0; ADDR_MOD_AB_SEC0_SrcACR = 0; ADDR_MOD_AB_SEC0_SrcAClear = 0; ADDR_MOD_AB_SEC0_SrcBIncr = 8; ADDR_MOD_AB_SEC0_SrcBCR = 0; ADDR_MOD_AB_SEC0_SrcBClear = 0
    8e0: c8700022  SETC16       setc16_reg=28, setc16_value=8  # thread_cfg[28] (current thread); ADDR_MOD_DST_SEC0_DestIncr = 8; ADDR_MOD_DST_SEC0_DestCR = 0; ADDR_MOD_DST_SEC0_DestClear = 0; ADDR_MOD_DST_SEC0_DestCToCR = 0; ADDR_MOD_DST_SEC0_FidelityIncr = 0; ADDR_MOD_DST_SEC0_FidelityClear = 0
    8e4: c8bc0002  SETC16       setc16_reg=47, setc16_value=0  # thread_cfg[47] (current thread); ADDR_MOD_BIAS_SEC0_BiasIncr = 0; ADDR_MOD_BIAS_SEC0_BiasClear = 0
    8e8: c8350042  SETC16       setc16_reg=13, setc16_value=16400  # thread_cfg[13] (current thread); ADDR_MOD_AB_SEC1_SrcAIncr = 16; ADDR_MOD_AB_SEC1_SrcACR = 0; ADDR_MOD_AB_SEC1_SrcAClear = 0; ADDR_MOD_AB_SEC1_SrcBIncr = 0; ADDR_MOD_AB_SEC1_SrcBCR = 1; ADDR_MOD_AB_SEC1_SrcBClear = 0
    8ec: c8740022  SETC16       setc16_reg=29, setc16_value=8  # thread_cfg[29] (current thread); ADDR_MOD_DST_SEC1_DestIncr = 8; ADDR_MOD_DST_SEC1_DestCR = 0; ADDR_MOD_DST_SEC1_DestClear = 0; ADDR_MOD_DST_SEC1_DestCToCR = 0; ADDR_MOD_DST_SEC1_FidelityIncr = 0; ADDR_MOD_DST_SEC1_FidelityClear = 0
    8f0: c8c00002  SETC16       setc16_reg=48, setc16_value=0  # thread_cfg[48] (current thread); ADDR_MOD_BIAS_SEC1_BiasIncr = 0; ADDR_MOD_BIAS_SEC1_BiasClear = 0
    8f4: c8398102  SETC16       setc16_reg=14, setc16_value=24640  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 0; ADDR_MOD_AB_SEC2_SrcACR = 1; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 32; ADDR_MOD_AB_SEC2_SrcBCR = 1; ADDR_MOD_AB_SEC2_SrcBClear = 0
    8f8: c8780022  SETC16       setc16_reg=30, setc16_value=8  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 8; ADDR_MOD_DST_SEC2_DestCR = 0; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 0; ADDR_MOD_DST_SEC2_FidelityClear = 0
    8fc: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
    900: c841c182  SETC16       setc16_reg=16, setc16_value=28768  # thread_cfg[16] (current thread); ADDR_MOD_AB_SEC4_SrcAIncr = 32; ADDR_MOD_AB_SEC4_SrcACR = 1; ADDR_MOD_AB_SEC4_SrcAClear = 0; ADDR_MOD_AB_SEC4_SrcBIncr = 48; ADDR_MOD_AB_SEC4_SrcBCR = 1; ADDR_MOD_AB_SEC4_SrcBClear = 0
    904: c8801002  SETC16       setc16_reg=32, setc16_value=1024  # thread_cfg[32] (current thread); ADDR_MOD_DST_SEC4_DestIncr = 0; ADDR_MOD_DST_SEC4_DestCR = 1; ADDR_MOD_DST_SEC4_DestClear = 0; ADDR_MOD_DST_SEC4_DestCToCR = 0; ADDR_MOD_DST_SEC4_FidelityIncr = 0; ADDR_MOD_DST_SEC4_FidelityClear = 0
    908: c8cc0002  SETC16       setc16_reg=51, setc16_value=0  # thread_cfg[51] (current thread); ADDR_MOD_BIAS_SEC4_BiasIncr = 0; ADDR_MOD_BIAS_SEC4_BiasClear = 0
    90c: c8470302  SETC16       setc16_reg=17, setc16_value=49344  # thread_cfg[17] (current thread); ADDR_MOD_AB_SEC5_SrcAIncr = 0; ADDR_MOD_AB_SEC5_SrcACR = 1; ADDR_MOD_AB_SEC5_SrcAClear = 1; ADDR_MOD_AB_SEC5_SrcBIncr = 0; ADDR_MOD_AB_SEC5_SrcBCR = 1; ADDR_MOD_AB_SEC5_SrcBClear = 1
    910: c884b002  SETC16       setc16_reg=33, setc16_value=11264  # thread_cfg[33] (current thread); ADDR_MOD_DST_SEC5_DestIncr = 0; ADDR_MOD_DST_SEC5_DestCR = 1; ADDR_MOD_DST_SEC5_DestClear = 1; ADDR_MOD_DST_SEC5_DestCToCR = 0; ADDR_MOD_DST_SEC5_FidelityIncr = 1; ADDR_MOD_DST_SEC5_FidelityClear = 0
    914: c8d00002  SETC16       setc16_reg=52, setc16_value=0  # thread_cfg[52] (current thread); ADDR_MOD_BIAS_SEC5_BiasIncr = 0; ADDR_MOD_BIAS_SEC5_BiasClear = 0
    918: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    91c: ffe80437  lui          x8, 0xffe80  # x8 = 0xffe80000 · tensix_pc_buf + 0x0
    920: 00840413  addi         x8, x8, 8  # x8 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    924: 00042023  sw           x0, 0(x8)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    928: 00042483  lw           x9, 0(x8)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    92c: 00907033  and          x0, x0, x9
    930: ffb80437  lui          x8, 0xffb80  # x8 = 0xffb80000 · MOP_CFG
    934: 00100493  addi         x9, x0, 1  # x9 = 0x00000001
    938: 00942023  sw           x9, 0(x8)  # MOP_CFG · 0xffb80000; write 0x00000001
    93c: 00200493  addi         x9, x0, 2  # x9 = 0x00000002
    940: 00942223  sw           x9, 4(x8)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
    944: 020004b7  lui          x9, 0x02000  # x9 = 0x02000000
    948: 00942423  sw           x9, 8(x8)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
    94c: 374004b7  lui          x9, 0x37400  # x9 = 0x37400000
    950: 00f48493  addi         x9, x9, 15  # x9 = 0x3740000f
    954: 00942623  sw           x9, 12(x8)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x3740000f; MOP template instruction · SETRWC clear_ab_vld=1, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    958: 020004b7  lui          x9, 0x02000  # x9 = 0x02000000
    95c: 00942823  sw           x9, 16(x8)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    960: 040404b7  lui          x9, 0x04040  # x9 = 0x04040000
    964: 08048493  addi         x9, x9, 128  # x9 = 0x04040080
    968: 00942a23  sw           x9, 20(x8)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x04040080; MOP template instruction · REPLAY start_idx=16, len=8, execute_while_loading=0, load_mode=0
    96c: 040604b7  lui          x9, 0x04060  # x9 = 0x04060000
    970: 08048493  addi         x9, x9, 128  # x9 = 0x04060080
    974: 00942c23  sw           x9, 24(x8)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    978: 00942e23  sw           x9, 28(x8)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    97c: 02942023  sw           x9, 32(x8)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    980: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    984: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    988: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    98c: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    990: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    994: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    998: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    99c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    9a0: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    9a4: 00130313  addi         x6, x6, 1
    9a8: 9f9ff06f  jal          x0, 0x000003a0  # target 0x000003a0
loc_9ac:
    9ac: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    9b0: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    9b4: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    9b8: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    9bc: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    9c0: 3c000002  SFPNOP
    9c4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    9c8: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    9cc: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    9d0: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
loc_9d4:
    9d4: 1940006f  jal          x0, 0x00000b68  # target 0x00000b68
loc_9d8:
    9d8: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    9dc: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    9e0: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    9e4: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    9e8: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    9ec: 01507033  and          x0, x0, x21
    9f0: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    9f4: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
    9f8: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000001
    9fc: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    a00: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000008
    a04: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    a08: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
    a0c: 37120ab7  lui          x21, 0x37120  # x21 = 0x37120000
    a10: 004a8a93  addi         x21, x21, 4  # x21 = 0x37120004
    a14: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    a18: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    a1c: 0402cab7  lui          x21, 0x0402c  # x21 = 0x0402c000
    a20: 040a8a93  addi         x21, x21, 64  # x21 = 0x0402c040
    a24: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x0402c040; MOP template instruction · REPLAY start_idx=11, len=4, execute_while_loading=0, load_mode=0
    a28: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    a2c: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    a30: 0402cab7  lui          x21, 0x0402c  # x21 = 0x0402c000
    a34: 040a8a93  addi         x21, x21, 64  # x21 = 0x0402c040
    a38: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x0402c040; MOP template instruction · REPLAY start_idx=11, len=4, execute_while_loading=0, load_mode=0
    a3c: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x0402c040; MOP template instruction · REPLAY start_idx=11, len=4, execute_while_loading=0, load_mode=0
    a40: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    a44: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    a48: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    a4c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    a50: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    a54: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    a58: 00008067  jalr         x0, 0(x1)
loc_a5c:
    a5c: c42aa8ed  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=43579  # lreg_ind: L0
    a60: c420fee1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=16312  # lreg_ind: L0
    a64: 44000302  SFPCONFIG    imm16_math=0, config_dest=12, instr_mod1=0
    a68: c42a9061  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=42008  # lreg_ind: L0
    a6c: c4209eb1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=10156  # lreg_ind: L0
    a70: 44000342  SFPCONFIG    imm16_math=0, config_dest=13, instr_mod1=0
    a74: c4680001  SFPLOADI     lreg_ind=1, instr_mod0=10, imm16=0  # lreg_ind: L1
    a78: c4610bf9  SFPLOADI     lreg_ind=1, instr_mod0=8, imm16=17150  # lreg_ind: L1
    a7c: c4a96b69  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=23258  # lreg_ind: L2
    a80: c4a0cea1  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=13224  # lreg_ind: L2
    a84: c4e8e215  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=14469  # lreg_ind: L3
    a88: c4e0fe01  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=16256  # lreg_ind: L3
    a8c: c00f8501  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L0
    a90: 10030582  SFPMAD       lreg_src_a=0, lreg_src_b=12, lreg_src_c=1, lreg_dest=6, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L12 · programmable; ttsim reset 0.00195312 (0x3b000000); lreg_src_c: L1; lreg_dest: L6
    a94: c5010dfd  SFPLOADI     lreg_ind=4, instr_mod0=0, imm16=17279  # lreg_ind: L4
    a98: 48001186  SFPSWAP      imm12_math=0, lreg_src_c=4, lreg_dest=6, instr_mod1=1  # lreg_src_c: L4; lreg_dest: L6
    a9c: 3c000002  SFPNOP
    aa0: dc001901  SFPEXEXP     imm12_math=0, lreg_c=6, lreg_dest=4, instr_mod1=0  # lreg_c: L6; lreg_dest: L4
    aa4: e0001801  SFPEXMAN     imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=0  # lreg_c: L6; lreg_dest: L0
    aa8: e8001001  SFPSHFT      imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=0  # lreg_c: L4; lreg_dest: L0
    aac: e0000105  SFPEXMAN     imm12_math=0, lreg_c=0, lreg_dest=4, instr_mod1=1  # lreg_c: L0; lreg_dest: L4
    ab0: 40001102  SFPCAST      lreg_src_c=4, lreg_dest=4, instr_mod1=0  # lreg_src_c: L4; lreg_dest: L4
    ab4: 10134942  SFPMAD       lreg_src_a=4, lreg_src_b=13, lreg_src_c=2, lreg_dest=5, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L13 · programmable; ttsim reset -0.674878 (0xbf2cc4c7); lreg_src_c: L2; lreg_dest: L5
    ab8: 5c0025a2  SFPGT        imm12_math=0, lreg_c=9, lreg_dest=6, instr_mod1=8  # lreg_c: L9 · constant 0 (0x00000000); lreg_dest: L6
    abc: 10150d02  SFPMAD       lreg_src_a=5, lreg_src_b=4, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L5; lreg_src_b: L4; lreg_src_c: L3; lreg_dest: L4
    ac0: f8001805  SFPAND       imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=1  # lreg_c: L6; lreg_dest: L0
    ac4: 0800100a  SFPSETEXP    imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=2  # lreg_c: L4; lreg_dest: L0
    ac8: c10f8501  SFPLOAD      lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L4
    acc: 24001106  SFPSETSGN    imm12_math=0, lreg_c=4, lreg_dest=4, instr_mod1=1  # lreg_c: L4; lreg_dest: L4
    ad0: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    ad4: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
    ad8: ec001019  SFPSETCC     imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=6  # lreg_c: L4; lreg_dest: L0
    adc: f0002801  SFPMOV       imm12_math=0, lreg_c=10, lreg_dest=0, instr_mod1=0  # lreg_c: L10 · constant 1 (0x3f800000); lreg_dest: L0
    ae0: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    ae4: c80f8501  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L0
    ae8: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    aec: 00008067  jalr         x0, 0(x1)
loc_af0:
    af0: c42aa8ed  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=43579  # lreg_ind: L0
    af4: c420fee1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=16312  # lreg_ind: L0
    af8: 44000302  SFPCONFIG    imm16_math=0, config_dest=12, instr_mod1=0
    afc: c42a9061  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=42008  # lreg_ind: L0
    b00: c4209eb1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=10156  # lreg_ind: L0
    b04: 44000342  SFPCONFIG    imm16_math=0, config_dest=13, instr_mod1=0
    b08: c4680001  SFPLOADI     lreg_ind=1, instr_mod0=10, imm16=0  # lreg_ind: L1
    b0c: c4610bf9  SFPLOADI     lreg_ind=1, instr_mod0=8, imm16=17150  # lreg_ind: L1
    b10: c4a96b69  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=23258  # lreg_ind: L2
    b14: c4a0cea1  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=13224  # lreg_ind: L2
    b18: c4e8e215  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=14469  # lreg_ind: L3
    b1c: c4e0fe01  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=16256  # lreg_ind: L3
    b20: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    b24: 10030582  SFPMAD       lreg_src_a=0, lreg_src_b=12, lreg_src_c=1, lreg_dest=6, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L12 · programmable; ttsim reset 0.00195312 (0x3b000000); lreg_src_c: L1; lreg_dest: L6
    b28: c5010dfd  SFPLOADI     lreg_ind=4, instr_mod0=0, imm16=17279  # lreg_ind: L4
    b2c: 48001186  SFPSWAP      imm12_math=0, lreg_src_c=4, lreg_dest=6, instr_mod1=1  # lreg_src_c: L4; lreg_dest: L6
    b30: 3c000002  SFPNOP
    b34: dc001901  SFPEXEXP     imm12_math=0, lreg_c=6, lreg_dest=4, instr_mod1=0  # lreg_c: L6; lreg_dest: L4
    b38: e0001801  SFPEXMAN     imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=0  # lreg_c: L6; lreg_dest: L0
    b3c: e8001001  SFPSHFT      imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=0  # lreg_c: L4; lreg_dest: L0
    b40: e0000105  SFPEXMAN     imm12_math=0, lreg_c=0, lreg_dest=4, instr_mod1=1  # lreg_c: L0; lreg_dest: L4
    b44: 40001102  SFPCAST      lreg_src_c=4, lreg_dest=4, instr_mod1=0  # lreg_src_c: L4; lreg_dest: L4
    b48: 10134942  SFPMAD       lreg_src_a=4, lreg_src_b=13, lreg_src_c=2, lreg_dest=5, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L13 · programmable; ttsim reset -0.674878 (0xbf2cc4c7); lreg_src_c: L2; lreg_dest: L5
    b4c: 5c0025a2  SFPGT        imm12_math=0, lreg_c=9, lreg_dest=6, instr_mod1=8  # lreg_c: L9 · constant 0 (0x00000000); lreg_dest: L6
    b50: 10150d02  SFPMAD       lreg_src_a=5, lreg_src_b=4, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L5; lreg_src_b: L4; lreg_src_c: L3; lreg_dest: L4
    b54: f8001805  SFPAND       imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=1  # lreg_c: L6; lreg_dest: L0
    b58: 0800100a  SFPSETEXP    imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=2  # lreg_c: L4; lreg_dest: L0
    b5c: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    b60: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    b64: 00008067  jalr         x0, 0(x1)
    b68:           j FW_TRISC1+4   # return to firmware, linked at install
