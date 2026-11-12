# llama3 1b decode: attention_merge, trisc1. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (8): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9
# params: 0x780=attention_partial_tiles, 0x784=e2e_context, 0x788=kv_blocks, 0xea40=merge_head
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
      4: c8380022  SETC16       setc16_reg=14, setc16_value=8  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 8; ADDR_MOD_AB_SEC2_SrcACR = 0; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 0; ADDR_MOD_AB_SEC2_SrcBCR = 0; ADDR_MOD_AB_SEC2_SrcBClear = 0
      8: c8780022  SETC16       setc16_reg=30, setc16_value=8  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 8; ADDR_MOD_DST_SEC2_DestCR = 0; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 0; ADDR_MOD_DST_SEC2_FidelityClear = 0
      c: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
     10: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
     14: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
     18: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
     1c: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
     20: 00507033  and          x0, x0, x5
     24: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
     28: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     2c: 00522023  sw           x5, 0(x4)  # MOP_CFG · 0xffb80000; write 0x00000004
     30: 00200293  addi         x5, x0, 2  # x5 = 0x00000002
     34: 00522223  sw           x5, 4(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
     38: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     3c: 00522423  sw           x5, 8(x4)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
     40: 37c002b7  lui          x5, 0x37c00  # x5 = 0x37c00000
     44: 00328293  addi         x5, x5, 3  # x5 = 0x37c00003
     48: 00522623  sw           x5, 12(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37c00003; MOP template instruction · SETRWC clear_ab_vld=3, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=3
     4c: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     50: 00522823  sw           x5, 16(x4)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
     54: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
     58: 00522a23  sw           x5, 20(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
     5c: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     60: 00522c23  sw           x5, 24(x4)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
     64: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
     68: 00522e23  sw           x5, 28(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
     6c: 02522023  sw           x5, 32(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
     70: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
     74: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
     78: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
     7c: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
     80: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
     84: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
     88: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
     8c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
     90: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
     94: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
     98: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
     9c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
     a0: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
     a4: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
     a8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
     ac: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
     b0: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
     b4: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
     b8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
     bc: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
     c0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
     c4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
     c8: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
     cc: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
     d0: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
     d4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
     d8: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
     dc: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
     e0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
     e4: 78800393  addi         x7, x0, 1928  # x7 = 0x00000788
     e8: 0003a283  lw           x5, 0(x7)  # param kv_blocks; 0x00000788
     ec: 00100213  addi         x4, x0, 1  # x4 = 0x00000001
     f0: 00400313  addi         x6, x0, 4  # x6 = 0x00000004
     f4: 00537a63  bgeu         x6, x5, 0x00000108  # target 0x00000108
     f8: 00400213  addi         x4, x0, 4  # x4 = 0x00000004
     fc: 08000313  addi         x6, x0, 128  # x6 = 0x00000080
    100: 00537463  bgeu         x6, x5, 0x00000108  # target 0x00000108
    104: 00c00213  addi         x4, x0, 12  # x4 = 0x0000000c
loc_108:
    108: fff20213  addi         x4, x4, -1
    10c: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    110: 00020313  addi         x6, x4, 0
loc_114:
    114: 3062f463  bgeu         x5, x6, 0x0000041c  # target 0x0000041c
    118: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    11c: c8380022  SETC16       setc16_reg=14, setc16_value=8  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 8; ADDR_MOD_AB_SEC2_SrcACR = 0; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 0; ADDR_MOD_AB_SEC2_SrcBCR = 0; ADDR_MOD_AB_SEC2_SrcBClear = 0
    120: c8780022  SETC16       setc16_reg=30, setc16_value=8  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 8; ADDR_MOD_DST_SEC2_DestCR = 0; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 0; ADDR_MOD_DST_SEC2_FidelityClear = 0
    124: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
    128: ffe803b7  lui          x7, 0xffe80  # x7 = 0xffe80000 · tensix_pc_buf + 0x0
    12c: 00838393  addi         x7, x7, 8  # x7 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    130: 0003a023  sw           x0, 0(x7)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    134: 0003a403  lw           x8, 0(x7)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    138: 00807033  and          x0, x0, x8
    13c: ffb803b7  lui          x7, 0xffb80  # x7 = 0xffb80000 · MOP_CFG
    140: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    144: 0083a023  sw           x8, 0(x7)  # MOP_CFG · 0xffb80000; write 0x00000004
    148: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
    14c: 0083a223  sw           x8, 4(x7)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
    150: 02000437  lui          x8, 0x02000  # x8 = 0x02000000
    154: 0083a423  sw           x8, 8(x7)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
    158: 37c00437  lui          x8, 0x37c00  # x8 = 0x37c00000
    15c: 00340413  addi         x8, x8, 3  # x8 = 0x37c00003
    160: 0083a623  sw           x8, 12(x7)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37c00003; MOP template instruction · SETRWC clear_ab_vld=3, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=3
    164: 02000437  lui          x8, 0x02000  # x8 = 0x02000000
    168: 0083a823  sw           x8, 16(x7)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    16c: 1200a437  lui          x8, 0x1200a  # x8 = 0x1200a000
    170: 0083aa23  sw           x8, 20(x7)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
    174: 02000437  lui          x8, 0x02000  # x8 = 0x02000000
    178: 0083ac23  sw           x8, 24(x7)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    17c: 1200a437  lui          x8, 0x1200a  # x8 = 0x1200a000
    180: 0083ae23  sw           x8, 28(x7)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
    184: 0283a023  sw           x8, 32(x7)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
    188: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    18c: c8040402  SETC16       setc16_reg=1, setc16_value=256  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 256
    190: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    194: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    198: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    19c: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    1a0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1a4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    1a8: c8040502  SETC16       setc16_reg=1, setc16_value=320  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 320
    1ac: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    1b0: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    1b4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    1b8: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    1bc: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1c0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    1c4: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    1c8: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    1cc: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    1d0: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    1d4: 3c000002  SFPNOP
    1d8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    1dc: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    1e0: c00f8201  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
    1e4: c04f8401  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=256  # lreg_ind: L1
    1e8: f0000081  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=2, instr_mod1=0  # lreg_c: L0; lreg_dest: L2
    1ec: f00004c1  SFPMOV       imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=0  # lreg_c: L1; lreg_dest: L3
    1f0: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    1f4: 3c000002  SFPNOP
    1f8: c80f8201  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
    1fc: 1002c882  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=2, lreg_dest=2, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L2; lreg_dest: L2
    200: 3c000002  SFPNOP
    204: 1002ccc2  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=3, lreg_dest=3, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L3; lreg_dest: L3
    208: 3c000002  SFPNOP
    20c: c88f8221  SFPSTORE     lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=136  # lreg_ind: L2
    210: c8cf8281  SFPSTORE     lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=160  # lreg_ind: L3
    214: c00f8209  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=130  # lreg_ind: L0
    218: c04f8409  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=258  # lreg_ind: L1
    21c: f0000081  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=2, instr_mod1=0  # lreg_c: L0; lreg_dest: L2
    220: f00004c1  SFPMOV       imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=0  # lreg_c: L1; lreg_dest: L3
    224: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    228: 3c000002  SFPNOP
    22c: c80f8209  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=130  # lreg_ind: L0
    230: 1002c882  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=2, lreg_dest=2, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L2; lreg_dest: L2
    234: 3c000002  SFPNOP
    238: 1002ccc2  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=3, lreg_dest=3, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L3; lreg_dest: L3
    23c: 3c000002  SFPNOP
    240: c88f8229  SFPSTORE     lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=138  # lreg_ind: L2
    244: c8cf8289  SFPSTORE     lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=162  # lreg_ind: L3
    248: c00f8241  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=144  # lreg_ind: L0
    24c: c04f8441  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=272  # lreg_ind: L1
    250: f0000081  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=2, instr_mod1=0  # lreg_c: L0; lreg_dest: L2
    254: f00004c1  SFPMOV       imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=0  # lreg_c: L1; lreg_dest: L3
    258: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    25c: 3c000002  SFPNOP
    260: c80f8241  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=144  # lreg_ind: L0
    264: 1002c882  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=2, lreg_dest=2, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L2; lreg_dest: L2
    268: 3c000002  SFPNOP
    26c: 1002ccc2  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=3, lreg_dest=3, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L3; lreg_dest: L3
    270: 3c000002  SFPNOP
    274: c88f8261  SFPSTORE     lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=152  # lreg_ind: L2
    278: c8cf82c1  SFPSTORE     lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=176  # lreg_ind: L3
    27c: c00f8249  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=146  # lreg_ind: L0
    280: c04f8449  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=274  # lreg_ind: L1
    284: f0000081  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=2, instr_mod1=0  # lreg_c: L0; lreg_dest: L2
    288: f00004c1  SFPMOV       imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=0  # lreg_c: L1; lreg_dest: L3
    28c: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    290: 3c000002  SFPNOP
    294: c80f8249  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=146  # lreg_ind: L0
    298: 1002c882  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=2, lreg_dest=2, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L2; lreg_dest: L2
    29c: 3c000002  SFPNOP
    2a0: 1002ccc2  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=3, lreg_dest=3, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L3; lreg_dest: L3
    2a4: 3c000002  SFPNOP
    2a8: c88f8269  SFPSTORE     lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=154  # lreg_ind: L2
    2ac: c8cf82c9  SFPSTORE     lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=178  # lreg_ind: L3
    2b0: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    2b4: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    2b8: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    2bc: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    2c0: 3c000002  SFPNOP
    2c4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    2c8: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    2cc: 20c000ef  jal          x1, 0x000004d8  # target 0x000004d8; x1 = 0x000002d0
    2d0: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    2d4: 204000ef  jal          x1, 0x000004d8  # target 0x000004d8; x1 = 0x000002d8
    2d8: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    2dc: 1fc000ef  jal          x1, 0x000004d8  # target 0x000004d8; x1 = 0x000002e0
    2e0: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    2e4: 1f4000ef  jal          x1, 0x000004d8  # target 0x000004d8; x1 = 0x000002e8
    2e8: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    2ec: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    2f0: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    2f4: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    2f8: 3c000002  SFPNOP
    2fc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    300: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    304: 268000ef  jal          x1, 0x0000056c  # target 0x0000056c; x1 = 0x00000308
    308: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    30c: 260000ef  jal          x1, 0x0000056c  # target 0x0000056c; x1 = 0x00000310
    310: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    314: 258000ef  jal          x1, 0x0000056c  # target 0x0000056c; x1 = 0x00000318
    318: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    31c: 250000ef  jal          x1, 0x0000056c  # target 0x0000056c; x1 = 0x00000320
    320: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    324: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    328: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    32c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    330: 3c000002  SFPNOP
    334: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    338: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    33c: 2c4000ef  jal          x1, 0x00000600  # target 0x00000600; x1 = 0x00000340
    340: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    344: 2bc000ef  jal          x1, 0x00000600  # target 0x00000600; x1 = 0x00000348
    348: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    34c: 2b4000ef  jal          x1, 0x00000600  # target 0x00000600; x1 = 0x00000350
    350: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    354: 2ac000ef  jal          x1, 0x00000600  # target 0x00000600; x1 = 0x00000358
    358: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    35c: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    360: c8040402  SETC16       setc16_reg=1, setc16_value=256  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 256
    364: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    368: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    36c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    370: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    374: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    378: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    37c: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    380: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    384: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    388: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    38c: 3c000002  SFPNOP
    390: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    394: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    398: 290000ef  jal          x1, 0x00000628  # target 0x00000628; x1 = 0x0000039c
    39c: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    3a0: 288000ef  jal          x1, 0x00000628  # target 0x00000628; x1 = 0x000003a4
    3a4: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    3a8: 280000ef  jal          x1, 0x00000628  # target 0x00000628; x1 = 0x000003ac
    3ac: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    3b0: 278000ef  jal          x1, 0x00000628  # target 0x00000628; x1 = 0x000003b4
    3b4: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    3b8: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    3bc: c8040402  SETC16       setc16_reg=1, setc16_value=256  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 256
    3c0: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    3c4: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    3c8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    3cc: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    3d0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    3d4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    3d8: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    3dc: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    3e0: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    3e4: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    3e8: 3c000002  SFPNOP
    3ec: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    3f0: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    3f4: 25c000ef  jal          x1, 0x00000650  # target 0x00000650; x1 = 0x000003f8
    3f8: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    3fc: 254000ef  jal          x1, 0x00000650  # target 0x00000650; x1 = 0x00000400
    400: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    404: 24c000ef  jal          x1, 0x00000650  # target 0x00000650; x1 = 0x00000408
    408: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    40c: 244000ef  jal          x1, 0x00000650  # target 0x00000650; x1 = 0x00000410
    410: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    414: 00128293  addi         x5, x5, 1
    418: cfdff06f  jal          x0, 0x00000114  # target 0x00000114
loc_41c:
    41c: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    420: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    424: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    428: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    42c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    430: 3c000002  SFPNOP
    434: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    438: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    43c: 23c000ef  jal          x1, 0x00000678  # target 0x00000678; x1 = 0x00000440
    440: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    444: 234000ef  jal          x1, 0x00000678  # target 0x00000678; x1 = 0x00000448
    448: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    44c: 22c000ef  jal          x1, 0x00000678  # target 0x00000678; x1 = 0x00000450
    450: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    454: 224000ef  jal          x1, 0x00000678  # target 0x00000678; x1 = 0x00000458
    458: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    45c: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    460: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    464: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    468: 3c000002  SFPNOP
    46c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    470: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    474: 240000ef  jal          x1, 0x000006b4  # target 0x000006b4; x1 = 0x00000478
    478: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    47c: 238000ef  jal          x1, 0x000006b4  # target 0x000006b4; x1 = 0x00000480
    480: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    484: 230000ef  jal          x1, 0x000006b4  # target 0x000006b4; x1 = 0x00000488
    488: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    48c: 228000ef  jal          x1, 0x000006b4  # target 0x000006b4; x1 = 0x00000490
    490: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    494: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    498: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    49c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    4a0: 3c000002  SFPNOP
    4a4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    4a8: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    4ac: 224000ef  jal          x1, 0x000006d0  # target 0x000006d0; x1 = 0x000004b0
    4b0: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    4b4: 21c000ef  jal          x1, 0x000006d0  # target 0x000006d0; x1 = 0x000004b8
    4b8: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    4bc: 214000ef  jal          x1, 0x000006d0  # target 0x000006d0; x1 = 0x000004c0
    4c0: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    4c4: 20c000ef  jal          x1, 0x000006d0  # target 0x000006d0; x1 = 0x000004c8
    4c8: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    4cc: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    4d0: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    4d4: 2180006f  jal          x0, 0x000006ec  # target 0x000006ec
loc_4d8:
    4d8: c42aa8ed  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=43579  # lreg_ind: L0
    4dc: c420fee1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=16312  # lreg_ind: L0
    4e0: 44000302  SFPCONFIG    imm16_math=0, config_dest=12, instr_mod1=0
    4e4: c42a9061  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=42008  # lreg_ind: L0
    4e8: c4209eb1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=10156  # lreg_ind: L0
    4ec: 44000342  SFPCONFIG    imm16_math=0, config_dest=13, instr_mod1=0
    4f0: c4680001  SFPLOADI     lreg_ind=1, instr_mod0=10, imm16=0  # lreg_ind: L1
    4f4: c4610bf9  SFPLOADI     lreg_ind=1, instr_mod0=8, imm16=17150  # lreg_ind: L1
    4f8: c4a96b69  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=23258  # lreg_ind: L2
    4fc: c4a0cea1  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=13224  # lreg_ind: L2
    500: c4e8e215  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=14469  # lreg_ind: L3
    504: c4e0fe01  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=16256  # lreg_ind: L3
    508: c00f8221  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=136  # lreg_ind: L0
    50c: 10030582  SFPMAD       lreg_src_a=0, lreg_src_b=12, lreg_src_c=1, lreg_dest=6, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L12 · programmable; ttsim reset 0.00195312 (0x3b000000); lreg_src_c: L1; lreg_dest: L6
    510: c5010dfd  SFPLOADI     lreg_ind=4, instr_mod0=0, imm16=17279  # lreg_ind: L4
    514: 48001186  SFPSWAP      imm12_math=0, lreg_src_c=4, lreg_dest=6, instr_mod1=1  # lreg_src_c: L4; lreg_dest: L6
    518: 3c000002  SFPNOP
    51c: dc001901  SFPEXEXP     imm12_math=0, lreg_c=6, lreg_dest=4, instr_mod1=0  # lreg_c: L6; lreg_dest: L4
    520: e0001801  SFPEXMAN     imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=0  # lreg_c: L6; lreg_dest: L0
    524: e8001001  SFPSHFT      imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=0  # lreg_c: L4; lreg_dest: L0
    528: e0000105  SFPEXMAN     imm12_math=0, lreg_c=0, lreg_dest=4, instr_mod1=1  # lreg_c: L0; lreg_dest: L4
    52c: 40001102  SFPCAST      lreg_src_c=4, lreg_dest=4, instr_mod1=0  # lreg_src_c: L4; lreg_dest: L4
    530: 10134942  SFPMAD       lreg_src_a=4, lreg_src_b=13, lreg_src_c=2, lreg_dest=5, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L13 · programmable; ttsim reset -0.674878 (0xbf2cc4c7); lreg_src_c: L2; lreg_dest: L5
    534: 5c0025a2  SFPGT        imm12_math=0, lreg_c=9, lreg_dest=6, instr_mod1=8  # lreg_c: L9 · constant 0 (0x00000000); lreg_dest: L6
    538: 10150d02  SFPMAD       lreg_src_a=5, lreg_src_b=4, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L5; lreg_src_b: L4; lreg_src_c: L3; lreg_dest: L4
    53c: f8001805  SFPAND       imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=1  # lreg_c: L6; lreg_dest: L0
    540: 0800100a  SFPSETEXP    imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=2  # lreg_c: L4; lreg_dest: L0
    544: c10f8221  SFPLOAD      lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=136  # lreg_ind: L4
    548: 24001106  SFPSETSGN    imm12_math=0, lreg_c=4, lreg_dest=4, instr_mod1=1  # lreg_c: L4; lreg_dest: L4
    54c: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    550: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
    554: ec001019  SFPSETCC     imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=6  # lreg_c: L4; lreg_dest: L0
    558: f0002801  SFPMOV       imm12_math=0, lreg_c=10, lreg_dest=0, instr_mod1=0  # lreg_c: L10 · constant 1 (0x3f800000); lreg_dest: L0
    55c: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    560: c80f8221  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=136  # lreg_ind: L0
    564: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    568: 00008067  jalr         x0, 0(x1)
loc_56c:
    56c: c42aa8ed  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=43579  # lreg_ind: L0
    570: c420fee1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=16312  # lreg_ind: L0
    574: 44000302  SFPCONFIG    imm16_math=0, config_dest=12, instr_mod1=0
    578: c42a9061  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=42008  # lreg_ind: L0
    57c: c4209eb1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=10156  # lreg_ind: L0
    580: 44000342  SFPCONFIG    imm16_math=0, config_dest=13, instr_mod1=0
    584: c4680001  SFPLOADI     lreg_ind=1, instr_mod0=10, imm16=0  # lreg_ind: L1
    588: c4610bf9  SFPLOADI     lreg_ind=1, instr_mod0=8, imm16=17150  # lreg_ind: L1
    58c: c4a96b69  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=23258  # lreg_ind: L2
    590: c4a0cea1  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=13224  # lreg_ind: L2
    594: c4e8e215  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=14469  # lreg_ind: L3
    598: c4e0fe01  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=16256  # lreg_ind: L3
    59c: c00f8281  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=160  # lreg_ind: L0
    5a0: 10030582  SFPMAD       lreg_src_a=0, lreg_src_b=12, lreg_src_c=1, lreg_dest=6, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L12 · programmable; ttsim reset 0.00195312 (0x3b000000); lreg_src_c: L1; lreg_dest: L6
    5a4: c5010dfd  SFPLOADI     lreg_ind=4, instr_mod0=0, imm16=17279  # lreg_ind: L4
    5a8: 48001186  SFPSWAP      imm12_math=0, lreg_src_c=4, lreg_dest=6, instr_mod1=1  # lreg_src_c: L4; lreg_dest: L6
    5ac: 3c000002  SFPNOP
    5b0: dc001901  SFPEXEXP     imm12_math=0, lreg_c=6, lreg_dest=4, instr_mod1=0  # lreg_c: L6; lreg_dest: L4
    5b4: e0001801  SFPEXMAN     imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=0  # lreg_c: L6; lreg_dest: L0
    5b8: e8001001  SFPSHFT      imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=0  # lreg_c: L4; lreg_dest: L0
    5bc: e0000105  SFPEXMAN     imm12_math=0, lreg_c=0, lreg_dest=4, instr_mod1=1  # lreg_c: L0; lreg_dest: L4
    5c0: 40001102  SFPCAST      lreg_src_c=4, lreg_dest=4, instr_mod1=0  # lreg_src_c: L4; lreg_dest: L4
    5c4: 10134942  SFPMAD       lreg_src_a=4, lreg_src_b=13, lreg_src_c=2, lreg_dest=5, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L13 · programmable; ttsim reset -0.674878 (0xbf2cc4c7); lreg_src_c: L2; lreg_dest: L5
    5c8: 5c0025a2  SFPGT        imm12_math=0, lreg_c=9, lreg_dest=6, instr_mod1=8  # lreg_c: L9 · constant 0 (0x00000000); lreg_dest: L6
    5cc: 10150d02  SFPMAD       lreg_src_a=5, lreg_src_b=4, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L5; lreg_src_b: L4; lreg_src_c: L3; lreg_dest: L4
    5d0: f8001805  SFPAND       imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=1  # lreg_c: L6; lreg_dest: L0
    5d4: 0800100a  SFPSETEXP    imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=2  # lreg_c: L4; lreg_dest: L0
    5d8: c10f8281  SFPLOAD      lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=160  # lreg_ind: L4
    5dc: 24001106  SFPSETSGN    imm12_math=0, lreg_c=4, lreg_dest=4, instr_mod1=1  # lreg_c: L4; lreg_dest: L4
    5e0: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    5e4: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
    5e8: ec001019  SFPSETCC     imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=6  # lreg_c: L4; lreg_dest: L0
    5ec: f0002801  SFPMOV       imm12_math=0, lreg_c=10, lreg_dest=0, instr_mod1=0  # lreg_c: L10 · constant 1 (0x3f800000); lreg_dest: L0
    5f0: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    5f4: c80f8281  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=160  # lreg_ind: L0
    5f8: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    5fc: 00008067  jalr         x0, 0(x1)
loc_600:
    600: c00f8301  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
    604: c04f8221  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=136  # lreg_ind: L1
    608: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    60c: c04f8501  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L1
    610: c08f8281  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=160  # lreg_ind: L2
    614: 10048002  SFPMAD       lreg_src_a=1, lreg_src_b=2, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L0; lreg_dest: L0
    618: 3c000002  SFPNOP
    61c: c80f8301  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
    620: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    624: 00008067  jalr         x0, 0(x1)
loc_628:
    628: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    62c: c04f8221  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=136  # lreg_ind: L1
    630: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    634: c04f8401  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=256  # lreg_ind: L1
    638: c08f8281  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=160  # lreg_ind: L2
    63c: 10048002  SFPMAD       lreg_src_a=1, lreg_src_b=2, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L0; lreg_dest: L0
    640: 3c000002  SFPNOP
    644: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    648: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    64c: 00008067  jalr         x0, 0(x1)
loc_650:
    650: c00f8101  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
    654: c04f8221  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=136  # lreg_ind: L1
    658: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    65c: c04f8401  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=256  # lreg_ind: L1
    660: c08f8281  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=160  # lreg_ind: L2
    664: 10048002  SFPMAD       lreg_src_a=1, lreg_src_b=2, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L0; lreg_dest: L0
    668: 3c000002  SFPNOP
    66c: c80f8101  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
    670: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    674: 00008067  jalr         x0, 0(x1)
loc_678:
    678: c00f8301  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
    67c: 64000042  SFPARECIP    imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    680: 10006886  SFPMAD       lreg_src_a=0, lreg_src_b=1, lreg_src_c=10, lreg_dest=2, instr_mod1=1  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L10 · constant 1 (0x3f800000); lreg_dest: L2
    684: 3c000002  SFPNOP
    688: 100888c2  SFPMAD       lreg_src_a=2, lreg_src_b=2, lreg_src_c=2, lreg_dest=3, instr_mod1=0  # lreg_src_a: L2; lreg_src_b: L2; lreg_src_c: L2; lreg_dest: L3
    68c: 3c000002  SFPNOP
    690: 100c88c2  SFPMAD       lreg_src_a=3, lreg_src_b=2, lreg_src_c=2, lreg_dest=3, instr_mod1=0  # lreg_src_a: L3; lreg_src_b: L2; lreg_src_c: L2; lreg_dest: L3
    694: 3c000002  SFPNOP
    698: 480028c6  SFPSWAP      imm12_math=0, lreg_src_c=10, lreg_dest=3, instr_mod1=1  # lreg_src_c: L10 · constant 1 (0x3f800000); lreg_dest: L3
    69c: 3c000002  SFPNOP
    6a0: 100c4402  SFPMAD       lreg_src_a=3, lreg_src_b=1, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L3; lreg_src_b: L1; lreg_src_c: L1; lreg_dest: L0
    6a4: 3c000002  SFPNOP
    6a8: c80f8301  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
    6ac: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    6b0: 00008067  jalr         x0, 0(x1)
loc_6b4:
    6b4: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    6b8: c04f8301  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L1
    6bc: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    6c0: 3c000002  SFPNOP
    6c4: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    6c8: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    6cc: 00008067  jalr         x0, 0(x1)
loc_6d0:
    6d0: c00f8101  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
    6d4: c04f8301  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L1
    6d8: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    6dc: 3c000002  SFPNOP
    6e0: c80f8101  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
    6e4: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    6e8: 00008067  jalr         x0, 0(x1)
    6ec:           j FW_TRISC1+4   # return to firmware, linked at install
