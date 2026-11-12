# llama3 8b-bf16 decode: attention_merge, trisc1. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
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
     e4: c8040402  SETC16       setc16_reg=1, setc16_value=256  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 256
     e8: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
     ec: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
     f0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
     f4: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
     f8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
     fc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    100: c8040502  SETC16       setc16_reg=1, setc16_value=320  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 320
    104: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    108: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    10c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    110: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    114: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    118: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    11c: 78800393  addi         x7, x0, 1928  # x7 = 0x00000788
    120: 0003a283  lw           x5, 0(x7)  # param kv_blocks; 0x00000788
    124: 00100213  addi         x4, x0, 1  # x4 = 0x00000001
    128: 00400313  addi         x6, x0, 4  # x6 = 0x00000004
    12c: 00537a63  bgeu         x6, x5, 0x00000140  # target 0x00000140
    130: 00400213  addi         x4, x0, 4  # x4 = 0x00000004
    134: 08000313  addi         x6, x0, 128  # x6 = 0x00000080
    138: 00537463  bgeu         x6, x5, 0x00000140  # target 0x00000140
    13c: 00c00213  addi         x4, x0, 12  # x4 = 0x0000000c
loc_140:
    140: fff20213  addi         x4, x4, -1
    144: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    148: 00020313  addi         x6, x4, 0
loc_14c:
    14c: 3c62f063  bgeu         x5, x6, 0x0000050c  # target 0x0000050c
    150: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    154: c8380022  SETC16       setc16_reg=14, setc16_value=8  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 8; ADDR_MOD_AB_SEC2_SrcACR = 0; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 0; ADDR_MOD_AB_SEC2_SrcBCR = 0; ADDR_MOD_AB_SEC2_SrcBClear = 0
    158: c8780022  SETC16       setc16_reg=30, setc16_value=8  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 8; ADDR_MOD_DST_SEC2_DestCR = 0; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 0; ADDR_MOD_DST_SEC2_FidelityClear = 0
    15c: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
    160: ffe803b7  lui          x7, 0xffe80  # x7 = 0xffe80000 · tensix_pc_buf + 0x0
    164: 00838393  addi         x7, x7, 8  # x7 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    168: 0003a023  sw           x0, 0(x7)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    16c: 0003a403  lw           x8, 0(x7)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    170: 00807033  and          x0, x0, x8
    174: ffb803b7  lui          x7, 0xffb80  # x7 = 0xffb80000 · MOP_CFG
    178: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    17c: 0083a023  sw           x8, 0(x7)  # MOP_CFG · 0xffb80000; write 0x00000004
    180: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
    184: 0083a223  sw           x8, 4(x7)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
    188: 02000437  lui          x8, 0x02000  # x8 = 0x02000000
    18c: 0083a423  sw           x8, 8(x7)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
    190: 37c00437  lui          x8, 0x37c00  # x8 = 0x37c00000
    194: 00340413  addi         x8, x8, 3  # x8 = 0x37c00003
    198: 0083a623  sw           x8, 12(x7)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37c00003; MOP template instruction · SETRWC clear_ab_vld=3, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=3
    19c: 02000437  lui          x8, 0x02000  # x8 = 0x02000000
    1a0: 0083a823  sw           x8, 16(x7)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    1a4: 1200a437  lui          x8, 0x1200a  # x8 = 0x1200a000
    1a8: 0083aa23  sw           x8, 20(x7)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
    1ac: 02000437  lui          x8, 0x02000  # x8 = 0x02000000
    1b0: 0083ac23  sw           x8, 24(x7)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    1b4: 1200a437  lui          x8, 0x1200a  # x8 = 0x1200a000
    1b8: 0083ae23  sw           x8, 28(x7)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
    1bc: 0283a023  sw           x8, 32(x7)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
    1c0: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    1c4: c8040602  SETC16       setc16_reg=1, setc16_value=384  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 384
    1c8: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    1cc: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    1d0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    1d4: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    1d8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1dc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    1e0: c8040702  SETC16       setc16_reg=1, setc16_value=448  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 448
    1e4: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    1e8: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    1ec: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    1f0: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    1f4: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1f8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    1fc: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    200: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    204: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    208: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    20c: 3c000002  SFPNOP
    210: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    214: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    218: c00f8401  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=256  # lreg_ind: L0
    21c: c04f8601  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=384  # lreg_ind: L1
    220: f0000081  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=2, instr_mod1=0  # lreg_c: L0; lreg_dest: L2
    224: f00004c1  SFPMOV       imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=0  # lreg_c: L1; lreg_dest: L3
    228: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    22c: 3c000002  SFPNOP
    230: c80f8401  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=256  # lreg_ind: L0
    234: 1002c882  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=2, lreg_dest=2, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L2; lreg_dest: L2
    238: 3c000002  SFPNOP
    23c: 1002ccc2  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=3, lreg_dest=3, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L3; lreg_dest: L3
    240: 3c000002  SFPNOP
    244: c88f8421  SFPSTORE     lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=264  # lreg_ind: L2
    248: c8cf8481  SFPSTORE     lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=288  # lreg_ind: L3
    24c: c00f8409  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=258  # lreg_ind: L0
    250: c04f8609  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=386  # lreg_ind: L1
    254: f0000081  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=2, instr_mod1=0  # lreg_c: L0; lreg_dest: L2
    258: f00004c1  SFPMOV       imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=0  # lreg_c: L1; lreg_dest: L3
    25c: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    260: 3c000002  SFPNOP
    264: c80f8409  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=258  # lreg_ind: L0
    268: 1002c882  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=2, lreg_dest=2, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L2; lreg_dest: L2
    26c: 3c000002  SFPNOP
    270: 1002ccc2  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=3, lreg_dest=3, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L3; lreg_dest: L3
    274: 3c000002  SFPNOP
    278: c88f8429  SFPSTORE     lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=266  # lreg_ind: L2
    27c: c8cf8489  SFPSTORE     lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=290  # lreg_ind: L3
    280: c00f8441  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=272  # lreg_ind: L0
    284: c04f8641  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=400  # lreg_ind: L1
    288: f0000081  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=2, instr_mod1=0  # lreg_c: L0; lreg_dest: L2
    28c: f00004c1  SFPMOV       imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=0  # lreg_c: L1; lreg_dest: L3
    290: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    294: 3c000002  SFPNOP
    298: c80f8441  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=272  # lreg_ind: L0
    29c: 1002c882  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=2, lreg_dest=2, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L2; lreg_dest: L2
    2a0: 3c000002  SFPNOP
    2a4: 1002ccc2  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=3, lreg_dest=3, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L3; lreg_dest: L3
    2a8: 3c000002  SFPNOP
    2ac: c88f8461  SFPSTORE     lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=280  # lreg_ind: L2
    2b0: c8cf84c1  SFPSTORE     lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=304  # lreg_ind: L3
    2b4: c00f8449  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=274  # lreg_ind: L0
    2b8: c04f8649  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=402  # lreg_ind: L1
    2bc: f0000081  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=2, instr_mod1=0  # lreg_c: L0; lreg_dest: L2
    2c0: f00004c1  SFPMOV       imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=0  # lreg_c: L1; lreg_dest: L3
    2c4: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    2c8: 3c000002  SFPNOP
    2cc: c80f8449  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=274  # lreg_ind: L0
    2d0: 1002c882  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=2, lreg_dest=2, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L2; lreg_dest: L2
    2d4: 3c000002  SFPNOP
    2d8: 1002ccc2  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=3, lreg_dest=3, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L3; lreg_dest: L3
    2dc: 3c000002  SFPNOP
    2e0: c88f8469  SFPSTORE     lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=282  # lreg_ind: L2
    2e4: c8cf84c9  SFPSTORE     lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=306  # lreg_ind: L3
    2e8: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    2ec: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    2f0: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    2f4: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    2f8: 3c000002  SFPNOP
    2fc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    300: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    304: 334000ef  jal          x1, 0x00000638  # target 0x00000638; x1 = 0x00000308
    308: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    30c: 32c000ef  jal          x1, 0x00000638  # target 0x00000638; x1 = 0x00000310
    310: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    314: 324000ef  jal          x1, 0x00000638  # target 0x00000638; x1 = 0x00000318
    318: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    31c: 31c000ef  jal          x1, 0x00000638  # target 0x00000638; x1 = 0x00000320
    320: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    324: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    328: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    32c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    330: 3c000002  SFPNOP
    334: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    338: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    33c: 390000ef  jal          x1, 0x000006cc  # target 0x000006cc; x1 = 0x00000340
    340: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    344: 388000ef  jal          x1, 0x000006cc  # target 0x000006cc; x1 = 0x00000348
    348: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    34c: 380000ef  jal          x1, 0x000006cc  # target 0x000006cc; x1 = 0x00000350
    350: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    354: 378000ef  jal          x1, 0x000006cc  # target 0x000006cc; x1 = 0x00000358
    358: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    35c: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    360: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    364: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    368: 3c000002  SFPNOP
    36c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    370: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    374: 3ec000ef  jal          x1, 0x00000760  # target 0x00000760; x1 = 0x00000378
    378: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    37c: 3e4000ef  jal          x1, 0x00000760  # target 0x00000760; x1 = 0x00000380
    380: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    384: 3dc000ef  jal          x1, 0x00000760  # target 0x00000760; x1 = 0x00000388
    388: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    38c: 3d4000ef  jal          x1, 0x00000760  # target 0x00000760; x1 = 0x00000390
    390: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    394: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    398: c8040602  SETC16       setc16_reg=1, setc16_value=384  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 384
    39c: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    3a0: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    3a4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    3a8: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    3ac: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    3b0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    3b4: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    3b8: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    3bc: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    3c0: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    3c4: 3c000002  SFPNOP
    3c8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    3cc: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    3d0: 3b8000ef  jal          x1, 0x00000788  # target 0x00000788; x1 = 0x000003d4
    3d4: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    3d8: 3b0000ef  jal          x1, 0x00000788  # target 0x00000788; x1 = 0x000003dc
    3dc: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    3e0: 3a8000ef  jal          x1, 0x00000788  # target 0x00000788; x1 = 0x000003e4
    3e4: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    3e8: 3a0000ef  jal          x1, 0x00000788  # target 0x00000788; x1 = 0x000003ec
    3ec: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    3f0: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    3f4: c8040602  SETC16       setc16_reg=1, setc16_value=384  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 384
    3f8: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    3fc: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    400: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    404: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    408: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    40c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    410: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    414: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    418: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    41c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    420: 3c000002  SFPNOP
    424: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    428: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    42c: 384000ef  jal          x1, 0x000007b0  # target 0x000007b0; x1 = 0x00000430
    430: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    434: 37c000ef  jal          x1, 0x000007b0  # target 0x000007b0; x1 = 0x00000438
    438: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    43c: 374000ef  jal          x1, 0x000007b0  # target 0x000007b0; x1 = 0x00000440
    440: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    444: 36c000ef  jal          x1, 0x000007b0  # target 0x000007b0; x1 = 0x00000448
    448: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    44c: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    450: c8040602  SETC16       setc16_reg=1, setc16_value=384  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 384
    454: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    458: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    45c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    460: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    464: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    468: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    46c: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    470: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    474: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    478: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    47c: 3c000002  SFPNOP
    480: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    484: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    488: 350000ef  jal          x1, 0x000007d8  # target 0x000007d8; x1 = 0x0000048c
    48c: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    490: 348000ef  jal          x1, 0x000007d8  # target 0x000007d8; x1 = 0x00000494
    494: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    498: 340000ef  jal          x1, 0x000007d8  # target 0x000007d8; x1 = 0x0000049c
    49c: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    4a0: 338000ef  jal          x1, 0x000007d8  # target 0x000007d8; x1 = 0x000004a4
    4a4: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    4a8: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    4ac: c8040602  SETC16       setc16_reg=1, setc16_value=384  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 384
    4b0: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    4b4: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    4b8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    4bc: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    4c0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    4c4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    4c8: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    4cc: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    4d0: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    4d4: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    4d8: 3c000002  SFPNOP
    4dc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    4e0: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    4e4: 31c000ef  jal          x1, 0x00000800  # target 0x00000800; x1 = 0x000004e8
    4e8: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    4ec: 314000ef  jal          x1, 0x00000800  # target 0x00000800; x1 = 0x000004f0
    4f0: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    4f4: 30c000ef  jal          x1, 0x00000800  # target 0x00000800; x1 = 0x000004f8
    4f8: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    4fc: 304000ef  jal          x1, 0x00000800  # target 0x00000800; x1 = 0x00000500
    500: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    504: 00128293  addi         x5, x5, 1
    508: c45ff06f  jal          x0, 0x0000014c  # target 0x0000014c
loc_50c:
    50c: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    510: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    514: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    518: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    51c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    520: 3c000002  SFPNOP
    524: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    528: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    52c: 2fc000ef  jal          x1, 0x00000828  # target 0x00000828; x1 = 0x00000530
    530: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    534: 2f4000ef  jal          x1, 0x00000828  # target 0x00000828; x1 = 0x00000538
    538: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    53c: 2ec000ef  jal          x1, 0x00000828  # target 0x00000828; x1 = 0x00000540
    540: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    544: 2e4000ef  jal          x1, 0x00000828  # target 0x00000828; x1 = 0x00000548
    548: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    54c: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    550: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    554: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    558: 3c000002  SFPNOP
    55c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    560: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    564: 300000ef  jal          x1, 0x00000864  # target 0x00000864; x1 = 0x00000568
    568: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    56c: 2f8000ef  jal          x1, 0x00000864  # target 0x00000864; x1 = 0x00000570
    570: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    574: 2f0000ef  jal          x1, 0x00000864  # target 0x00000864; x1 = 0x00000578
    578: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    57c: 2e8000ef  jal          x1, 0x00000864  # target 0x00000864; x1 = 0x00000580
    580: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    584: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    588: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    58c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    590: 3c000002  SFPNOP
    594: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    598: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    59c: 2e4000ef  jal          x1, 0x00000880  # target 0x00000880; x1 = 0x000005a0
    5a0: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    5a4: 2dc000ef  jal          x1, 0x00000880  # target 0x00000880; x1 = 0x000005a8
    5a8: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    5ac: 2d4000ef  jal          x1, 0x00000880  # target 0x00000880; x1 = 0x000005b0
    5b0: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    5b4: 2cc000ef  jal          x1, 0x00000880  # target 0x00000880; x1 = 0x000005b8
    5b8: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    5bc: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    5c0: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    5c4: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    5c8: 3c000002  SFPNOP
    5cc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    5d0: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    5d4: 2c8000ef  jal          x1, 0x0000089c  # target 0x0000089c; x1 = 0x000005d8
    5d8: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    5dc: 2c0000ef  jal          x1, 0x0000089c  # target 0x0000089c; x1 = 0x000005e0
    5e0: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    5e4: 2b8000ef  jal          x1, 0x0000089c  # target 0x0000089c; x1 = 0x000005e8
    5e8: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    5ec: 2b0000ef  jal          x1, 0x0000089c  # target 0x0000089c; x1 = 0x000005f0
    5f0: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    5f4: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    5f8: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    5fc: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    600: 3c000002  SFPNOP
    604: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    608: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    60c: 2ac000ef  jal          x1, 0x000008b8  # target 0x000008b8; x1 = 0x00000610
    610: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    614: 2a4000ef  jal          x1, 0x000008b8  # target 0x000008b8; x1 = 0x00000618
    618: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    61c: 29c000ef  jal          x1, 0x000008b8  # target 0x000008b8; x1 = 0x00000620
    620: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    624: 294000ef  jal          x1, 0x000008b8  # target 0x000008b8; x1 = 0x00000628
    628: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    62c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    630: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    634: 2a00006f  jal          x0, 0x000008d4  # target 0x000008d4
loc_638:
    638: c42aa8ed  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=43579  # lreg_ind: L0
    63c: c420fee1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=16312  # lreg_ind: L0
    640: 44000302  SFPCONFIG    imm16_math=0, config_dest=12, instr_mod1=0
    644: c42a9061  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=42008  # lreg_ind: L0
    648: c4209eb1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=10156  # lreg_ind: L0
    64c: 44000342  SFPCONFIG    imm16_math=0, config_dest=13, instr_mod1=0
    650: c4680001  SFPLOADI     lreg_ind=1, instr_mod0=10, imm16=0  # lreg_ind: L1
    654: c4610bf9  SFPLOADI     lreg_ind=1, instr_mod0=8, imm16=17150  # lreg_ind: L1
    658: c4a96b69  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=23258  # lreg_ind: L2
    65c: c4a0cea1  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=13224  # lreg_ind: L2
    660: c4e8e215  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=14469  # lreg_ind: L3
    664: c4e0fe01  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=16256  # lreg_ind: L3
    668: c00f8421  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=264  # lreg_ind: L0
    66c: 10030582  SFPMAD       lreg_src_a=0, lreg_src_b=12, lreg_src_c=1, lreg_dest=6, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L12 · programmable; ttsim reset 0.00195312 (0x3b000000); lreg_src_c: L1; lreg_dest: L6
    670: c5010dfd  SFPLOADI     lreg_ind=4, instr_mod0=0, imm16=17279  # lreg_ind: L4
    674: 48001186  SFPSWAP      imm12_math=0, lreg_src_c=4, lreg_dest=6, instr_mod1=1  # lreg_src_c: L4; lreg_dest: L6
    678: 3c000002  SFPNOP
    67c: dc001901  SFPEXEXP     imm12_math=0, lreg_c=6, lreg_dest=4, instr_mod1=0  # lreg_c: L6; lreg_dest: L4
    680: e0001801  SFPEXMAN     imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=0  # lreg_c: L6; lreg_dest: L0
    684: e8001001  SFPSHFT      imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=0  # lreg_c: L4; lreg_dest: L0
    688: e0000105  SFPEXMAN     imm12_math=0, lreg_c=0, lreg_dest=4, instr_mod1=1  # lreg_c: L0; lreg_dest: L4
    68c: 40001102  SFPCAST      lreg_src_c=4, lreg_dest=4, instr_mod1=0  # lreg_src_c: L4; lreg_dest: L4
    690: 10134942  SFPMAD       lreg_src_a=4, lreg_src_b=13, lreg_src_c=2, lreg_dest=5, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L13 · programmable; ttsim reset -0.674878 (0xbf2cc4c7); lreg_src_c: L2; lreg_dest: L5
    694: 5c0025a2  SFPGT        imm12_math=0, lreg_c=9, lreg_dest=6, instr_mod1=8  # lreg_c: L9 · constant 0 (0x00000000); lreg_dest: L6
    698: 10150d02  SFPMAD       lreg_src_a=5, lreg_src_b=4, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L5; lreg_src_b: L4; lreg_src_c: L3; lreg_dest: L4
    69c: f8001805  SFPAND       imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=1  # lreg_c: L6; lreg_dest: L0
    6a0: 0800100a  SFPSETEXP    imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=2  # lreg_c: L4; lreg_dest: L0
    6a4: c10f8421  SFPLOAD      lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=264  # lreg_ind: L4
    6a8: 24001106  SFPSETSGN    imm12_math=0, lreg_c=4, lreg_dest=4, instr_mod1=1  # lreg_c: L4; lreg_dest: L4
    6ac: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    6b0: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
    6b4: ec001019  SFPSETCC     imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=6  # lreg_c: L4; lreg_dest: L0
    6b8: f0002801  SFPMOV       imm12_math=0, lreg_c=10, lreg_dest=0, instr_mod1=0  # lreg_c: L10 · constant 1 (0x3f800000); lreg_dest: L0
    6bc: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    6c0: c80f8421  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=264  # lreg_ind: L0
    6c4: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    6c8: 00008067  jalr         x0, 0(x1)
loc_6cc:
    6cc: c42aa8ed  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=43579  # lreg_ind: L0
    6d0: c420fee1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=16312  # lreg_ind: L0
    6d4: 44000302  SFPCONFIG    imm16_math=0, config_dest=12, instr_mod1=0
    6d8: c42a9061  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=42008  # lreg_ind: L0
    6dc: c4209eb1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=10156  # lreg_ind: L0
    6e0: 44000342  SFPCONFIG    imm16_math=0, config_dest=13, instr_mod1=0
    6e4: c4680001  SFPLOADI     lreg_ind=1, instr_mod0=10, imm16=0  # lreg_ind: L1
    6e8: c4610bf9  SFPLOADI     lreg_ind=1, instr_mod0=8, imm16=17150  # lreg_ind: L1
    6ec: c4a96b69  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=23258  # lreg_ind: L2
    6f0: c4a0cea1  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=13224  # lreg_ind: L2
    6f4: c4e8e215  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=14469  # lreg_ind: L3
    6f8: c4e0fe01  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=16256  # lreg_ind: L3
    6fc: c00f8481  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=288  # lreg_ind: L0
    700: 10030582  SFPMAD       lreg_src_a=0, lreg_src_b=12, lreg_src_c=1, lreg_dest=6, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L12 · programmable; ttsim reset 0.00195312 (0x3b000000); lreg_src_c: L1; lreg_dest: L6
    704: c5010dfd  SFPLOADI     lreg_ind=4, instr_mod0=0, imm16=17279  # lreg_ind: L4
    708: 48001186  SFPSWAP      imm12_math=0, lreg_src_c=4, lreg_dest=6, instr_mod1=1  # lreg_src_c: L4; lreg_dest: L6
    70c: 3c000002  SFPNOP
    710: dc001901  SFPEXEXP     imm12_math=0, lreg_c=6, lreg_dest=4, instr_mod1=0  # lreg_c: L6; lreg_dest: L4
    714: e0001801  SFPEXMAN     imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=0  # lreg_c: L6; lreg_dest: L0
    718: e8001001  SFPSHFT      imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=0  # lreg_c: L4; lreg_dest: L0
    71c: e0000105  SFPEXMAN     imm12_math=0, lreg_c=0, lreg_dest=4, instr_mod1=1  # lreg_c: L0; lreg_dest: L4
    720: 40001102  SFPCAST      lreg_src_c=4, lreg_dest=4, instr_mod1=0  # lreg_src_c: L4; lreg_dest: L4
    724: 10134942  SFPMAD       lreg_src_a=4, lreg_src_b=13, lreg_src_c=2, lreg_dest=5, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L13 · programmable; ttsim reset -0.674878 (0xbf2cc4c7); lreg_src_c: L2; lreg_dest: L5
    728: 5c0025a2  SFPGT        imm12_math=0, lreg_c=9, lreg_dest=6, instr_mod1=8  # lreg_c: L9 · constant 0 (0x00000000); lreg_dest: L6
    72c: 10150d02  SFPMAD       lreg_src_a=5, lreg_src_b=4, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L5; lreg_src_b: L4; lreg_src_c: L3; lreg_dest: L4
    730: f8001805  SFPAND       imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=1  # lreg_c: L6; lreg_dest: L0
    734: 0800100a  SFPSETEXP    imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=2  # lreg_c: L4; lreg_dest: L0
    738: c10f8481  SFPLOAD      lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=288  # lreg_ind: L4
    73c: 24001106  SFPSETSGN    imm12_math=0, lreg_c=4, lreg_dest=4, instr_mod1=1  # lreg_c: L4; lreg_dest: L4
    740: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    744: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
    748: ec001019  SFPSETCC     imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=6  # lreg_c: L4; lreg_dest: L0
    74c: f0002801  SFPMOV       imm12_math=0, lreg_c=10, lreg_dest=0, instr_mod1=0  # lreg_c: L10 · constant 1 (0x3f800000); lreg_dest: L0
    750: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    754: c80f8481  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=288  # lreg_ind: L0
    758: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    75c: 00008067  jalr         x0, 0(x1)
loc_760:
    760: c00f8501  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L0
    764: c04f8421  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=264  # lreg_ind: L1
    768: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    76c: c04f8701  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L1
    770: c08f8481  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=288  # lreg_ind: L2
    774: 10048002  SFPMAD       lreg_src_a=1, lreg_src_b=2, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L0; lreg_dest: L0
    778: 3c000002  SFPNOP
    77c: c80f8501  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L0
    780: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    784: 00008067  jalr         x0, 0(x1)
loc_788:
    788: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    78c: c04f8421  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=264  # lreg_ind: L1
    790: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    794: c04f8601  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=384  # lreg_ind: L1
    798: c08f8481  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=288  # lreg_ind: L2
    79c: 10048002  SFPMAD       lreg_src_a=1, lreg_src_b=2, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L0; lreg_dest: L0
    7a0: 3c000002  SFPNOP
    7a4: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    7a8: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    7ac: 00008067  jalr         x0, 0(x1)
loc_7b0:
    7b0: c00f8101  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
    7b4: c04f8421  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=264  # lreg_ind: L1
    7b8: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    7bc: c04f8601  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=384  # lreg_ind: L1
    7c0: c08f8481  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=288  # lreg_ind: L2
    7c4: 10048002  SFPMAD       lreg_src_a=1, lreg_src_b=2, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L0; lreg_dest: L0
    7c8: 3c000002  SFPNOP
    7cc: c80f8101  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
    7d0: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    7d4: 00008067  jalr         x0, 0(x1)
loc_7d8:
    7d8: c00f8201  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
    7dc: c04f8421  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=264  # lreg_ind: L1
    7e0: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    7e4: c04f8601  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=384  # lreg_ind: L1
    7e8: c08f8481  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=288  # lreg_ind: L2
    7ec: 10048002  SFPMAD       lreg_src_a=1, lreg_src_b=2, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L0; lreg_dest: L0
    7f0: 3c000002  SFPNOP
    7f4: c80f8201  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
    7f8: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    7fc: 00008067  jalr         x0, 0(x1)
loc_800:
    800: c00f8301  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
    804: c04f8421  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=264  # lreg_ind: L1
    808: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    80c: c04f8601  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=384  # lreg_ind: L1
    810: c08f8481  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=288  # lreg_ind: L2
    814: 10048002  SFPMAD       lreg_src_a=1, lreg_src_b=2, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L0; lreg_dest: L0
    818: 3c000002  SFPNOP
    81c: c80f8301  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
    820: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    824: 00008067  jalr         x0, 0(x1)
loc_828:
    828: c00f8501  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L0
    82c: 64000042  SFPARECIP    imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    830: 10006886  SFPMAD       lreg_src_a=0, lreg_src_b=1, lreg_src_c=10, lreg_dest=2, instr_mod1=1  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L10 · constant 1 (0x3f800000); lreg_dest: L2
    834: 3c000002  SFPNOP
    838: 100888c2  SFPMAD       lreg_src_a=2, lreg_src_b=2, lreg_src_c=2, lreg_dest=3, instr_mod1=0  # lreg_src_a: L2; lreg_src_b: L2; lreg_src_c: L2; lreg_dest: L3
    83c: 3c000002  SFPNOP
    840: 100c88c2  SFPMAD       lreg_src_a=3, lreg_src_b=2, lreg_src_c=2, lreg_dest=3, instr_mod1=0  # lreg_src_a: L3; lreg_src_b: L2; lreg_src_c: L2; lreg_dest: L3
    844: 3c000002  SFPNOP
    848: 480028c6  SFPSWAP      imm12_math=0, lreg_src_c=10, lreg_dest=3, instr_mod1=1  # lreg_src_c: L10 · constant 1 (0x3f800000); lreg_dest: L3
    84c: 3c000002  SFPNOP
    850: 100c4402  SFPMAD       lreg_src_a=3, lreg_src_b=1, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L3; lreg_src_b: L1; lreg_src_c: L1; lreg_dest: L0
    854: 3c000002  SFPNOP
    858: c80f8501  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L0
    85c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    860: 00008067  jalr         x0, 0(x1)
loc_864:
    864: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    868: c04f8501  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L1
    86c: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    870: 3c000002  SFPNOP
    874: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    878: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    87c: 00008067  jalr         x0, 0(x1)
loc_880:
    880: c00f8101  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
    884: c04f8501  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L1
    888: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    88c: 3c000002  SFPNOP
    890: c80f8101  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
    894: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    898: 00008067  jalr         x0, 0(x1)
loc_89c:
    89c: c00f8201  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
    8a0: c04f8501  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L1
    8a4: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    8a8: 3c000002  SFPNOP
    8ac: c80f8201  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
    8b0: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    8b4: 00008067  jalr         x0, 0(x1)
loc_8b8:
    8b8: c00f8301  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
    8bc: c04f8501  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L1
    8c0: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    8c4: 3c000002  SFPNOP
    8c8: c80f8301  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
    8cc: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    8d0: 00008067  jalr         x0, 0(x1)
    8d4:           j FW_TRISC1+4   # return to firmware, linked at install
