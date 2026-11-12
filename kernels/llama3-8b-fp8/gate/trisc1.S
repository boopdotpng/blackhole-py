# llama3 8b-fp8 decode: gate, trisc1. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (96): 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 14,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 14,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 14,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 14,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 14,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9 14,9 1,10 2,10 3,10 4,10 5,10 6,10 7,10 10,10 11,10 12,10 13,10 14,10 1,11 2,11 3,11 4,11 5,11 6,11 7,11 10,11 11,11 12,11 13,11 14,11
# params: 0x780=e2e_x_b_decode_token, 0x784=e2e_l0_gate, 0x788=e2e_l0_up, 0x78c=input_scale_0, 0x790=input_scale_1, 0x794=output_scale_0_0, 0x798=output_scale_0_1, 0x79c=output_scale_1_0, 0x7a0=output_scale_1_1, 0x7a4=e2e_hidden_dense, 0x7a8=e2e_l0_post_norm, 0xe940=e2e_gate, 0xe944=e2e_l0_gate_row_start, 0xe948=e2e_up, 0xe94c=e2e_l0_up_row_start, 0xe950=dense_start, 0xe954=e2e_l0_gate_rows, 0xe958=e2e_l0_up_rows, 0xe95c=dram_port
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: 100000c4  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=1
      4: c04f8001  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L1; Record replay[0]; not executed here
      8: 10044002  SFPMAD       lreg_src_a=1, lreg_src_b=1, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L1; lreg_src_c: L0; lreg_dest: L0; Record replay[1]; not executed here
      c: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0  # Record replay[2]; not executed here
     10: 100300c4  REPLAY       start_idx=3, len=3, execute_while_loading=0, load_mode=1
     14: c04f8001  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L1; Record replay[3]; not executed here
     18: 10044002  SFPMAD       lreg_src_a=1, lreg_src_b=1, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L1; lreg_src_c: L0; lreg_dest: L0; Record replay[4]; not executed here
     1c: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0  # Record replay[5]; not executed here
     20: 10060284  REPLAY       start_idx=6, len=10, execute_while_loading=0, load_mode=1
     24: 4c438002  SFPLOADMACRO lreg_ind=1, instr_mod0=0, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L1; Record replay[6]; not executed here
     28: c08f8401  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=256  # lreg_ind: L2; Record replay[7]; not executed here
     2c: 4cc3800a  SFPLOADMACRO lreg_ind=3, instr_mod0=0, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L3; Record replay[8]; not executed here
     30: c10f8409  SFPLOAD      lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=258  # lreg_ind: L4; Record replay[9]; not executed here
     34: 1804a442  SFPMUL       lreg_src_a=1, lreg_src_b=2, lreg_src_c=9, lreg_dest=1, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L1; Record replay[10]; not executed here
     38: 180d24c2  SFPMUL       lreg_src_a=3, lreg_src_b=4, lreg_src_c=9, lreg_dest=3, instr_mod1=0  # lreg_src_a: L3; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L3; Record replay[11]; not executed here
     3c: c84f8001  SFPSTORE     lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L1; Record replay[12]; not executed here
     40: c8cf8009  SFPSTORE     lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L3; Record replay[13]; not executed here
     44: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0  # Record replay[14]; not executed here
     48: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0  # Record replay[15]; not executed here
     4c: 10100144  REPLAY       start_idx=16, len=5, execute_while_loading=0, load_mode=1
     50: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0; Record replay[16]; not executed here
     54: 1801a402  SFPMUL       lreg_src_a=0, lreg_src_b=6, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L6; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0; Record replay[17]; not executed here
     58: 3c000002  SFPNOP         # Record replay[18]; not executed here
     5c: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0; Record replay[19]; not executed here
     60: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0  # Record replay[20]; not executed here
     64: 101500c4  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=1
     68: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0; Record replay[21]; not executed here
     6c: 10029dc2  SFPMAD       lreg_src_a=0, lreg_src_b=10, lreg_src_c=7, lreg_dest=7, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L10 · constant 1 (0x3f800000); lreg_src_c: L7; lreg_dest: L7; Record replay[22]; not executed here
     70: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0  # Record replay[23]; not executed here
     74: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
     78: 3c000002  SFPNOP
     7c: 18002702  SFPMUL       lreg_src_a=0, lreg_src_b=0, lreg_src_c=9, lreg_dest=12, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L0; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L12
     80: 46100106  SFPCONFIG    imm16_math=33792, config_dest=4, instr_mod1=1
     84: 443c0206  SFPCONFIG    imm16_math=3840, config_dest=8, instr_mod1=1
     88: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
     8c: c8380022  SETC16       setc16_reg=14, setc16_value=8  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 8; ADDR_MOD_AB_SEC2_SrcACR = 0; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 0; ADDR_MOD_AB_SEC2_SrcBCR = 0; ADDR_MOD_AB_SEC2_SrcBClear = 0
     90: c8780022  SETC16       setc16_reg=30, setc16_value=8  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 8; ADDR_MOD_DST_SEC2_DestCR = 0; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 0; ADDR_MOD_DST_SEC2_FidelityClear = 0
     94: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
     98: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
     9c: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
     a0: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
     a4: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
     a8: 00507033  and          x0, x0, x5
     ac: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
     b0: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     b4: 00522023  sw           x5, 0(x4)  # MOP_CFG · 0xffb80000; write 0x00000004
     b8: 00200293  addi         x5, x0, 2  # x5 = 0x00000002
     bc: 00522223  sw           x5, 4(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
     c0: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     c4: 00522423  sw           x5, 8(x4)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
     c8: 37c002b7  lui          x5, 0x37c00  # x5 = 0x37c00000
     cc: 00328293  addi         x5, x5, 3  # x5 = 0x37c00003
     d0: 00522623  sw           x5, 12(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37c00003; MOP template instruction · SETRWC clear_ab_vld=3, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=3
     d4: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     d8: 00522823  sw           x5, 16(x4)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
     dc: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
     e0: 00522a23  sw           x5, 20(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
     e4: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     e8: 00522c23  sw           x5, 24(x4)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
     ec: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
     f0: 00522e23  sw           x5, 28(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
     f4: 02522023  sw           x5, 32(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
     f8: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
     fc: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    100: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    104: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    108: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    10c: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    110: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    114: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    118: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    11c: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    120: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    124: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    128: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    12c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    130: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    134: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    138: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    13c: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    140: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    144: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    148: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    14c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    150: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    154: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    158: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    15c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    160: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    164: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    168: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    16c: c8040402  SETC16       setc16_reg=1, setc16_value=256  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 256
    170: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    174: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    178: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    17c: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    180: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    184: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    188: c8040502  SETC16       setc16_reg=1, setc16_value=320  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 320
    18c: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    190: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    194: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    198: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    19c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1a0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    1a4: c8040602  SETC16       setc16_reg=1, setc16_value=384  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 384
    1a8: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    1ac: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    1b0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    1b4: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    1b8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1bc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    1c0: c8040702  SETC16       setc16_reg=1, setc16_value=448  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 448
    1c4: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    1c8: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    1cc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    1d0: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    1d4: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1d8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    1dc: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    1e0: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    1e4: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    1e8: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    1ec: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    1f0: 3c000002  SFPNOP
    1f4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    1f8: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    1fc: c4000001  SFPLOADI     lreg_ind=0, instr_mod0=0, imm16=0  # lreg_ind: L0
    200: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
    204: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    208: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    20c: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    210: 00507033  and          x0, x0, x5
    214: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
    218: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
    21c: 00522023  sw           x5, 0(x4)  # MOP_CFG · 0xffb80000; write 0x00000001
    220: 00800293  addi         x5, x0, 8  # x5 = 0x00000008
    224: 00522223  sw           x5, 4(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000008
    228: 371202b7  lui          x5, 0x37120  # x5 = 0x37120000
    22c: 00428293  addi         x5, x5, 4  # x5 = 0x37120004
    230: 00522623  sw           x5, 12(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    234: 00522823  sw           x5, 16(x4)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    238: 040002b7  lui          x5, 0x04000  # x5 = 0x04000000
    23c: 03028293  addi         x5, x5, 48  # x5 = 0x04000030
    240: 00522a23  sw           x5, 20(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x04000030; MOP template instruction · REPLAY start_idx=0, len=3, execute_while_loading=0, load_mode=0
    244: 00522e23  sw           x5, 28(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x04000030; MOP template instruction · REPLAY start_idx=0, len=3, execute_while_loading=0, load_mode=0
    248: 02522023  sw           x5, 32(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x04000030; MOP template instruction · REPLAY start_idx=0, len=3, execute_while_loading=0, load_mode=0
    24c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    250: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    254: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    258: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    25c: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    260: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    264: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    268: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    26c: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    270: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    274: 3c000002  SFPNOP
    278: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    27c: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    280: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
    284: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    288: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    28c: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    290: 00507033  and          x0, x0, x5
    294: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
    298: 01420213  addi         x4, x4, 20  # x4 = 0xffb80014 · MopCfg[5] · LoopOp / InsnA2
    29c: 0400c2b7  lui          x5, 0x0400c  # x5 = 0x0400c000
    2a0: 03028293  addi         x5, x5, 48  # x5 = 0x0400c030
    2a4: 00522023  sw           x5, 0(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x0400c030; MOP template instruction · REPLAY start_idx=3, len=3, execute_while_loading=0, load_mode=0
    2a8: 00522423  sw           x5, 8(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x0400c030; MOP template instruction · REPLAY start_idx=3, len=3, execute_while_loading=0, load_mode=0
    2ac: 00522623  sw           x5, 12(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x0400c030; MOP template instruction · REPLAY start_idx=3, len=3, execute_while_loading=0, load_mode=0
    2b0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2b4: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2b8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2bc: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2c0: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    2c4: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    2c8: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    2cc: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    2d0: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    2d4: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    2d8: 3c000002  SFPNOP
    2dc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    2e0: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    2e4: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2e8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2ec: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2f0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2f4: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    2f8: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    2fc: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    300: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    304: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    308: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    30c: 3c000002  SFPNOP
    310: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    314: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    318: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    31c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    320: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    324: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    328: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    32c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    330: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    334: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    338: 3c000002  SFPNOP
    33c: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    340: 3c000002  SFPNOP
    344: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    348: 3c000002  SFPNOP
    34c: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    350: 3c000002  SFPNOP
    354: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    358: 3c000002  SFPNOP
    35c: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    360: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    364: 3c000002  SFPNOP
    368: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    36c: 3c000002  SFPNOP
    370: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    374: 3c000002  SFPNOP
    378: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    37c: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    380: 3c000002  SFPNOP
    384: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    388: 3c000002  SFPNOP
    38c: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    390: f0000081  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=2, instr_mod1=0  # lreg_c: L0; lreg_dest: L2
    394: f00000c1  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=3, instr_mod1=0  # lreg_c: L0; lreg_dest: L3
    398: 30000002  SFPTRANSP    imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    39c: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    3a0: 3c000002  SFPNOP
    3a4: 14280802  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=2, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L2; lreg_dest: L0
    3a8: 3c000002  SFPNOP
    3ac: 14280c02  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=3, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L3; lreg_dest: L0
    3b0: 3c000002  SFPNOP
    3b4: c5280001  SFPLOADI     lreg_ind=4, instr_mod0=10, imm16=0  # lreg_ind: L4
    3b8: c520e601  SFPLOADI     lreg_ind=4, instr_mod0=8, imm16=14720  # lreg_ind: L4
    3bc: 18012402  SFPMUL       lreg_src_a=0, lreg_src_b=4, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    3c0: c52b16b1  SFPLOADI     lreg_ind=4, instr_mod0=10, imm16=50604  # lreg_ind: L4
    3c4: c520dc9d  SFPLOADI     lreg_ind=4, instr_mod0=8, imm16=14119  # lreg_ind: L4
    3c8: 14281002  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=4, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L4; lreg_dest: L0
    3cc: 3c000002  SFPNOP
    3d0: f0000181  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=6, instr_mod1=0  # lreg_c: L0; lreg_dest: L6
    3d4: f0001841  SFPMOV       imm12_math=0, lreg_c=6, lreg_dest=1, instr_mod1=0  # lreg_c: L6; lreg_dest: L1
    3d8: ebffe445  SFPSHFT      imm12_math=4095, lreg_c=9, lreg_dest=1, instr_mod1=1  # lreg_c: L9 · constant 0 (0x00000000); lreg_dest: L1
    3dc: c4a84281  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=4256  # lreg_ind: L2
    3e0: c4a17c45  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=24337  # lreg_ind: L2
    3e4: e4000859  SFPIADD      imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=6  # lreg_c: L2; lreg_dest: L1
    3e8: 18186482  SFPMUL       lreg_src_a=6, lreg_src_b=1, lreg_src_c=9, lreg_dest=2, instr_mod1=0  # lreg_src_a: L6; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L2
    3ec: 3c000002  SFPNOP
    3f0: 1804a486  SFPMUL       lreg_src_a=1, lreg_src_b=2, lreg_src_c=9, lreg_dest=2, instr_mod1=1  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L2
    3f4: c4e85325  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=5321  # lreg_ind: L3
    3f8: c4e10049  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=16402  # lreg_ind: L3
    3fc: c528d899  SFPLOADI     lreg_ind=4, instr_mod0=10, imm16=13862  # lreg_ind: L4
    400: c5210041  SFPLOADI     lreg_ind=4, instr_mod0=8, imm16=16400  # lreg_ind: L4
    404: 14290902  SFPADD       lreg_src_a=10, lreg_src_b=4, lreg_src_c=2, lreg_dest=4, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L4; lreg_src_c: L2; lreg_dest: L4
    408: 3c000002  SFPNOP
    40c: 10090c82  SFPMAD       lreg_src_a=2, lreg_src_b=4, lreg_src_c=3, lreg_dest=2, instr_mod1=0  # lreg_src_a: L2; lreg_src_b: L4; lreg_src_c: L3; lreg_dest: L2
    410: 3c000002  SFPNOP
    414: 1804a442  SFPMUL       lreg_src_a=1, lreg_src_b=2, lreg_src_c=9, lreg_dest=1, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L1
    418: 3c000002  SFPNOP
    41c: 18186482  SFPMUL       lreg_src_a=6, lreg_src_b=1, lreg_src_c=9, lreg_dest=2, instr_mod1=0  # lreg_src_a: L6; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L2
    420: 3c000002  SFPNOP
    424: 1804a486  SFPMUL       lreg_src_a=1, lreg_src_b=2, lreg_src_c=9, lreg_dest=2, instr_mod1=1  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L2
    428: 3c000002  SFPNOP
    42c: 142a8882  SFPADD       lreg_src_a=10, lreg_src_b=10, lreg_src_c=2, lreg_dest=2, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L10 · constant 1 (0x3f800000); lreg_src_c: L2; lreg_dest: L2
    430: c5680001  SFPLOADI     lreg_ind=5, instr_mod0=10, imm16=0  # lreg_ind: L5
    434: c560fc01  SFPLOADI     lreg_ind=5, instr_mod0=8, imm16=16128  # lreg_ind: L5
    438: 18056542  SFPMUL       lreg_src_a=1, lreg_src_b=5, lreg_src_c=9, lreg_dest=5, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L5; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L5
    43c: 3c000002  SFPNOP
    440: 10094402  SFPMAD       lreg_src_a=2, lreg_src_b=5, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L2; lreg_src_b: L5; lreg_src_c: L1; lreg_dest: L0
    444: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    448: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    44c: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    450: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    454: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    458: 3c000002  SFPNOP
    45c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    460: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    464: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
    468: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    46c: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    470: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    474: 00507033  and          x0, x0, x5
    478: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
    47c: 00420213  addi         x4, x4, 4  # x4 = 0xffb80004 · MopCfg[1] · InnerCount / Flags
    480: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
    484: 00522023  sw           x5, 0(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000004
    488: 040182b7  lui          x5, 0x04018  # x5 = 0x04018000
    48c: 0a028293  addi         x5, x5, 160  # x5 = 0x040180a0
    490: 00522823  sw           x5, 16(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x040180a0; MOP template instruction · REPLAY start_idx=6, len=10, execute_while_loading=0, load_mode=0
    494: 00522c23  sw           x5, 24(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x040180a0; MOP template instruction · REPLAY start_idx=6, len=10, execute_while_loading=0, load_mode=0
    498: 00522e23  sw           x5, 28(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x040180a0; MOP template instruction · REPLAY start_idx=6, len=10, execute_while_loading=0, load_mode=0
    49c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    4a0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    4a4: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    4a8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    4ac: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    4b0: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    4b4: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    4b8: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    4bc: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    4c0: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    4c4: 3c000002  SFPNOP
    4c8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    4cc: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    4d0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    4d4: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    4d8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    4dc: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    4e0: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    4e4: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    4e8: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    4ec: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    4f0: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    4f4: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    4f8: 3c000002  SFPNOP
    4fc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    500: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    504: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    508: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    50c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    510: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    514: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    518: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    51c: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    520: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    524: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    528: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    52c: 3c000002  SFPNOP
    530: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    534: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    538: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    53c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    540: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    544: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    548: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    54c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    550: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    554: 78c00293  addi         x5, x0, 1932  # x5 = 0x0000078c
    558: 0002a203  lw           x4, 0(x5)  # param input_scale_0; 0x0000078c
    55c: ffe402b7  lui          x5, 0xffe40  # x5 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    560: 0042a023  sw           x4, 0(x5)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    564: 79000293  addi         x5, x0, 1936  # x5 = 0x00000790
    568: 0002a203  lw           x4, 0(x5)  # param input_scale_1; 0x00000790
    56c: ffe402b7  lui          x5, 0xffe40  # x5 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    570: 0042a023  sw           x4, 0(x5)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    574: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    578: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    57c: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    580: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    584: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    588: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    58c: 3c000002  SFPNOP
    590: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    594: 47c000ef  jal          x1, 0x00000a10  # target 0x00000a10; x1 = 0x00000598
    598: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    59c: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    5a0: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    5a4: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    5a8: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    5ac: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    5b0: 3c000002  SFPNOP
    5b4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    5b8: 458000ef  jal          x1, 0x00000a10  # target 0x00000a10; x1 = 0x000005bc
    5bc: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    5c0: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    5c4: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    5c8: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    5cc: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    5d0: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    5d4: 3c000002  SFPNOP
    5d8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    5dc: 434000ef  jal          x1, 0x00000a10  # target 0x00000a10; x1 = 0x000005e0
    5e0: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    5e4: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    5e8: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    5ec: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    5f0: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    5f4: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    5f8: 3c000002  SFPNOP
    5fc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    600: 410000ef  jal          x1, 0x00000a10  # target 0x00000a10; x1 = 0x00000604
    604: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    608: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    60c: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    610: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    614: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    618: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    61c: 3c000002  SFPNOP
    620: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    624: 470000ef  jal          x1, 0x00000a94  # target 0x00000a94; x1 = 0x00000628
    628: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    62c: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    630: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    634: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    638: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    63c: 3c000002  SFPNOP
    640: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    644: 450000ef  jal          x1, 0x00000a94  # target 0x00000a94; x1 = 0x00000648
    648: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    64c: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    650: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    654: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    658: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    65c: 3c000002  SFPNOP
    660: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    664: 430000ef  jal          x1, 0x00000a94  # target 0x00000a94; x1 = 0x00000668
    668: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    66c: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    670: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    674: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    678: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    67c: 3c000002  SFPNOP
    680: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    684: 410000ef  jal          x1, 0x00000a94  # target 0x00000a94; x1 = 0x00000688
    688: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    68c: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    690: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    694: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    698: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    69c: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    6a0: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    6a4: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    6a8: 3c000002  SFPNOP
    6ac: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    6b0: c8302022  SETC16       setc16_reg=12, setc16_value=2056  # thread_cfg[12] (current thread); ADDR_MOD_AB_SEC0_SrcAIncr = 8; ADDR_MOD_AB_SEC0_SrcACR = 0; ADDR_MOD_AB_SEC0_SrcAClear = 0; ADDR_MOD_AB_SEC0_SrcBIncr = 8; ADDR_MOD_AB_SEC0_SrcBCR = 0; ADDR_MOD_AB_SEC0_SrcBClear = 0
    6b4: c8700022  SETC16       setc16_reg=28, setc16_value=8  # thread_cfg[28] (current thread); ADDR_MOD_DST_SEC0_DestIncr = 8; ADDR_MOD_DST_SEC0_DestCR = 0; ADDR_MOD_DST_SEC0_DestClear = 0; ADDR_MOD_DST_SEC0_DestCToCR = 0; ADDR_MOD_DST_SEC0_FidelityIncr = 0; ADDR_MOD_DST_SEC0_FidelityClear = 0
    6b8: c8bc0002  SETC16       setc16_reg=47, setc16_value=0  # thread_cfg[47] (current thread); ADDR_MOD_BIAS_SEC0_BiasIncr = 0; ADDR_MOD_BIAS_SEC0_BiasClear = 0
    6bc: c8340002  SETC16       setc16_reg=13, setc16_value=0  # thread_cfg[13] (current thread); ADDR_MOD_AB_SEC1_SrcAIncr = 0; ADDR_MOD_AB_SEC1_SrcACR = 0; ADDR_MOD_AB_SEC1_SrcAClear = 0; ADDR_MOD_AB_SEC1_SrcBIncr = 0; ADDR_MOD_AB_SEC1_SrcBCR = 0; ADDR_MOD_AB_SEC1_SrcBClear = 0
    6c0: c8740002  SETC16       setc16_reg=29, setc16_value=0  # thread_cfg[29] (current thread); ADDR_MOD_DST_SEC1_DestIncr = 0; ADDR_MOD_DST_SEC1_DestCR = 0; ADDR_MOD_DST_SEC1_DestClear = 0; ADDR_MOD_DST_SEC1_DestCToCR = 0; ADDR_MOD_DST_SEC1_FidelityIncr = 0; ADDR_MOD_DST_SEC1_FidelityClear = 0
    6c4: c8c00002  SETC16       setc16_reg=48, setc16_value=0  # thread_cfg[48] (current thread); ADDR_MOD_BIAS_SEC1_BiasIncr = 0; ADDR_MOD_BIAS_SEC1_BiasClear = 0
    6c8: c83a0202  SETC16       setc16_reg=14, setc16_value=32896  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 0; ADDR_MOD_AB_SEC2_SrcACR = 0; ADDR_MOD_AB_SEC2_SrcAClear = 1; ADDR_MOD_AB_SEC2_SrcBIncr = 0; ADDR_MOD_AB_SEC2_SrcBCR = 0; ADDR_MOD_AB_SEC2_SrcBClear = 1
    6cc: c8789002  SETC16       setc16_reg=30, setc16_value=9216  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 0; ADDR_MOD_DST_SEC2_DestCR = 1; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 1; ADDR_MOD_DST_SEC2_FidelityClear = 0
    6d0: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
    6d4: c83e0202  SETC16       setc16_reg=15, setc16_value=32896  # thread_cfg[15] (current thread); ADDR_MOD_AB_SEC3_SrcAIncr = 0; ADDR_MOD_AB_SEC3_SrcACR = 0; ADDR_MOD_AB_SEC3_SrcAClear = 1; ADDR_MOD_AB_SEC3_SrcBIncr = 0; ADDR_MOD_AB_SEC3_SrcBCR = 0; ADDR_MOD_AB_SEC3_SrcBClear = 1
    6d8: c87e4022  SETC16       setc16_reg=31, setc16_value=36872  # thread_cfg[31] (current thread); ADDR_MOD_DST_SEC3_DestIncr = 8; ADDR_MOD_DST_SEC3_DestCR = 0; ADDR_MOD_DST_SEC3_DestClear = 0; ADDR_MOD_DST_SEC3_DestCToCR = 1; ADDR_MOD_DST_SEC3_FidelityIncr = 0; ADDR_MOD_DST_SEC3_FidelityClear = 1
    6dc: c8c80002  SETC16       setc16_reg=50, setc16_value=0  # thread_cfg[50] (current thread); ADDR_MOD_BIAS_SEC3_BiasIncr = 0; ADDR_MOD_BIAS_SEC3_BiasClear = 0
    6e0: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
    6e4: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    6e8: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    6ec: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    6f0: 00507033  and          x0, x0, x5
    6f4: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
    6f8: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
    6fc: 00522023  sw           x5, 0(x4)  # MOP_CFG · 0xffb80000; write 0x00000001
    700: 00200293  addi         x5, x0, 2  # x5 = 0x00000002
    704: 00522223  sw           x5, 4(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
    708: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    70c: 00522423  sw           x5, 8(x4)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
    710: 00522623  sw           x5, 12(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x02000000; MOP template instruction · NOP
    714: 00522823  sw           x5, 16(x4)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    718: 270002b7  lui          x5, 0x27000  # x5 = 0x27000000
    71c: 00522a23  sw           x5, 20(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x27000000; MOP template instruction · ELWMUL clear_dvalid=0, dest_accum_en=0, instr_mod19=0, addr_mode=0, dst=0
    720: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    724: 00522c23  sw           x5, 24(x4)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    728: 27c0c2b7  lui          x5, 0x27c0c  # x5 = 0x27c0c000
    72c: 00522e23  sw           x5, 28(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x27c0c000; MOP template instruction · ELWMUL clear_dvalid=3, dest_accum_en=0, instr_mod19=0, addr_mode=3, dst=0
    730: 270082b7  lui          x5, 0x27008  # x5 = 0x27008000
    734: 02522023  sw           x5, 32(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x27008000; MOP template instruction · ELWMUL clear_dvalid=0, dest_accum_en=0, instr_mod19=0, addr_mode=2, dst=0
    738: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    73c: 95428293  addi         x5, x5, -1708  # x5 = 0x0000e954
    740: 0002a203  lw           x4, 0(x5)  # param e2e_l0_gate_rows; 0x0000e954
    744: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    748: 00020313  addi         x6, x4, 0
loc_74c:
    74c: 0462f663  bgeu         x5, x6, 0x00000798  # target 0x00000798
    750: 3f4000ef  jal          x1, 0x00000b44  # target 0x00000b44; x1 = 0x00000754
    754: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    758: 79400413  addi         x8, x0, 1940  # x8 = 0x00000794
    75c: 00042383  lw           x7, 0(x8)  # param output_scale_0_0; 0x00000794
    760: ffe40437  lui          x8, 0xffe40  # x8 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    764: 00742023  sw           x7, 0(x8)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    768: 79800413  addi         x8, x0, 1944  # x8 = 0x00000798
    76c: 00042383  lw           x7, 0(x8)  # param output_scale_0_1; 0x00000798
    770: ffe40437  lui          x8, 0xffe40  # x8 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    774: 00742023  sw           x7, 0(x8)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    778: 1801a402  SFPMUL       lreg_src_a=0, lreg_src_b=6, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L6; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    77c: 3c000002  SFPNOP
    780: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    784: 3c000002  SFPNOP
    788: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    78c: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    790: 00128293  addi         x5, x5, 1
    794: fb9ff06f  jal          x0, 0x0000074c  # target 0x0000074c
loc_798:
    798: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    79c: 95828293  addi         x5, x5, -1704  # x5 = 0x0000e958
    7a0: 0002a203  lw           x4, 0(x5)  # param e2e_l0_up_rows; 0x0000e958
    7a4: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    7a8: 00020313  addi         x6, x4, 0
loc_7ac:
    7ac: 0462f663  bgeu         x5, x6, 0x000007f8  # target 0x000007f8
    7b0: 394000ef  jal          x1, 0x00000b44  # target 0x00000b44; x1 = 0x000007b4
    7b4: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    7b8: 79c00413  addi         x8, x0, 1948  # x8 = 0x0000079c
    7bc: 00042383  lw           x7, 0(x8)  # param output_scale_1_0; 0x0000079c
    7c0: ffe40437  lui          x8, 0xffe40  # x8 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    7c4: 00742023  sw           x7, 0(x8)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    7c8: 7a000413  addi         x8, x0, 1952  # x8 = 0x000007a0
    7cc: 00042383  lw           x7, 0(x8)  # param output_scale_1_1; 0x000007a0
    7d0: ffe40437  lui          x8, 0xffe40  # x8 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    7d4: 00742023  sw           x7, 0(x8)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    7d8: 1801a402  SFPMUL       lreg_src_a=0, lreg_src_b=6, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L6; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    7dc: 3c000002  SFPNOP
    7e0: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    7e4: 3c000002  SFPNOP
    7e8: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    7ec: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    7f0: 00128293  addi         x5, x5, 1
    7f4: fb9ff06f  jal          x0, 0x000007ac  # target 0x000007ac
loc_7f8:
    7f8: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    7fc: c8380022  SETC16       setc16_reg=14, setc16_value=8  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 8; ADDR_MOD_AB_SEC2_SrcACR = 0; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 0; ADDR_MOD_AB_SEC2_SrcBCR = 0; ADDR_MOD_AB_SEC2_SrcBClear = 0
    800: c8780022  SETC16       setc16_reg=30, setc16_value=8  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 8; ADDR_MOD_DST_SEC2_DestCR = 0; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 0; ADDR_MOD_DST_SEC2_FidelityClear = 0
    804: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
    808: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
    80c: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    810: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    814: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    818: 00507033  and          x0, x0, x5
    81c: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
    820: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
    824: 00522023  sw           x5, 0(x4)  # MOP_CFG · 0xffb80000; write 0x00000004
    828: 00200293  addi         x5, x0, 2  # x5 = 0x00000002
    82c: 00522223  sw           x5, 4(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
    830: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    834: 00522423  sw           x5, 8(x4)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
    838: 37c002b7  lui          x5, 0x37c00  # x5 = 0x37c00000
    83c: 00328293  addi         x5, x5, 3  # x5 = 0x37c00003
    840: 00522623  sw           x5, 12(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37c00003; MOP template instruction · SETRWC clear_ab_vld=3, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=3
    844: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    848: 00522823  sw           x5, 16(x4)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    84c: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
    850: 00522a23  sw           x5, 20(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
    854: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    858: 00522c23  sw           x5, 24(x4)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    85c: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
    860: 00522e23  sw           x5, 28(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
    864: 02522023  sw           x5, 32(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
    868: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    86c: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    870: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    874: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    878: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    87c: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    880: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    884: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    888: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    88c: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    890: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    894: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    898: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    89c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    8a0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    8a4: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    8a8: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    8ac: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    8b0: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    8b4: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    8b8: 3c000002  SFPNOP
    8bc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    8c0: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    8c4: c42aa8ed  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=43579  # lreg_ind: L0
    8c8: c420fee1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=16312  # lreg_ind: L0
    8cc: 44000302  SFPCONFIG    imm16_math=0, config_dest=12, instr_mod1=0
    8d0: c42a9061  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=42008  # lreg_ind: L0
    8d4: c4209eb1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=10156  # lreg_ind: L0
    8d8: 44000342  SFPCONFIG    imm16_math=0, config_dest=13, instr_mod1=0
    8dc: c4680001  SFPLOADI     lreg_ind=1, instr_mod0=10, imm16=0  # lreg_ind: L1
    8e0: c4610bf9  SFPLOADI     lreg_ind=1, instr_mod0=8, imm16=17150  # lreg_ind: L1
    8e4: c4a96b69  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=23258  # lreg_ind: L2
    8e8: c4a0cea1  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=13224  # lreg_ind: L2
    8ec: c4e8e215  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=14469  # lreg_ind: L3
    8f0: c4e0fe01  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=16256  # lreg_ind: L3
    8f4: 00400a13  addi         x20, x0, 4  # x20 = 0x00000004
loc_8f8:
    8f8: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
loc_8fc:
    8fc: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    900: c80f8201  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
    904: 1802e402  SFPMUL       lreg_src_a=0, lreg_src_b=11, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    908: 3c000002  SFPNOP
    90c: 10030582  SFPMAD       lreg_src_a=0, lreg_src_b=12, lreg_src_c=1, lreg_dest=6, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L12 · programmable; ttsim reset 0.00195312 (0x3b000000); lreg_src_c: L1; lreg_dest: L6
    910: c5010dfd  SFPLOADI     lreg_ind=4, instr_mod0=0, imm16=17279  # lreg_ind: L4
    914: 48001186  SFPSWAP      imm12_math=0, lreg_src_c=4, lreg_dest=6, instr_mod1=1  # lreg_src_c: L4; lreg_dest: L6
    918: 3c000002  SFPNOP
    91c: dc001901  SFPEXEXP     imm12_math=0, lreg_c=6, lreg_dest=4, instr_mod1=0  # lreg_c: L6; lreg_dest: L4
    920: e0001801  SFPEXMAN     imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=0  # lreg_c: L6; lreg_dest: L0
    924: e8001001  SFPSHFT      imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=0  # lreg_c: L4; lreg_dest: L0
    928: e0000105  SFPEXMAN     imm12_math=0, lreg_c=0, lreg_dest=4, instr_mod1=1  # lreg_c: L0; lreg_dest: L4
    92c: 40001102  SFPCAST      lreg_src_c=4, lreg_dest=4, instr_mod1=0  # lreg_src_c: L4; lreg_dest: L4
    930: 10134942  SFPMAD       lreg_src_a=4, lreg_src_b=13, lreg_src_c=2, lreg_dest=5, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L13 · programmable; ttsim reset -0.674878 (0xbf2cc4c7); lreg_src_c: L2; lreg_dest: L5
    934: 5c0025a2  SFPGT        imm12_math=0, lreg_c=9, lreg_dest=6, instr_mod1=8  # lreg_c: L9 · constant 0 (0x00000000); lreg_dest: L6
    938: 10150d02  SFPMAD       lreg_src_a=5, lreg_src_b=4, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L5; lreg_src_b: L4; lreg_src_c: L3; lreg_dest: L4
    93c: f8001805  SFPAND       imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=1  # lreg_c: L6; lreg_dest: L0
    940: 0800100a  SFPSETEXP    imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=2  # lreg_c: L4; lreg_dest: L0
    944: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    948: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    94c: fffa8a93  addi         x21, x21, -1
    950: fa0a96e3  bne          x21, x0, 0x000008fc  # target 0x000008fc
    954: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    958: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    95c: fffa0a13  addi         x20, x20, -1
    960: f80a1ce3  bne          x20, x0, 0x000008f8  # target 0x000008f8
    964: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    968: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    96c: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    970: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    974: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    978: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    97c: 3c000002  SFPNOP
    980: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    984: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    988: 00400a13  addi         x20, x0, 4  # x20 = 0x00000004
loc_98c:
    98c: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
loc_990:
    990: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    994: d4fe0001  SFPADDI      imm16_math=16256, lreg_dest=0, instr_mod1=0  # lreg_dest: L0
    998: 3c000002  SFPNOP
    99c: 64000042  SFPARECIP    imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    9a0: 10006886  SFPMAD       lreg_src_a=0, lreg_src_b=1, lreg_src_c=10, lreg_dest=2, instr_mod1=1  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L10 · constant 1 (0x3f800000); lreg_dest: L2
    9a4: 3c000002  SFPNOP
    9a8: 100888c2  SFPMAD       lreg_src_a=2, lreg_src_b=2, lreg_src_c=2, lreg_dest=3, instr_mod1=0  # lreg_src_a: L2; lreg_src_b: L2; lreg_src_c: L2; lreg_dest: L3
    9ac: 3c000002  SFPNOP
    9b0: 100c88c2  SFPMAD       lreg_src_a=3, lreg_src_b=2, lreg_src_c=2, lreg_dest=3, instr_mod1=0  # lreg_src_a: L3; lreg_src_b: L2; lreg_src_c: L2; lreg_dest: L3
    9b4: 3c000002  SFPNOP
    9b8: 480028c6  SFPSWAP      imm12_math=0, lreg_src_c=10, lreg_dest=3, instr_mod1=1  # lreg_src_c: L10 · constant 1 (0x3f800000); lreg_dest: L3
    9bc: 3c000002  SFPNOP
    9c0: 100c4402  SFPMAD       lreg_src_a=3, lreg_src_b=1, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L3; lreg_src_b: L1; lreg_src_c: L1; lreg_dest: L0
    9c4: c04f8201  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L1
    9c8: c08f8101  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L2
    9cc: 18042442  SFPMUL       lreg_src_a=1, lreg_src_b=0, lreg_src_c=9, lreg_dest=1, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L0; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L1
    9d0: 3c000002  SFPNOP
    9d4: 1804a442  SFPMUL       lreg_src_a=1, lreg_src_b=2, lreg_src_c=9, lreg_dest=1, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L1
    9d8: 3c000002  SFPNOP
    9dc: c84f8001  SFPSTORE     lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L1
    9e0: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    9e4: fffa8a93  addi         x21, x21, -1
    9e8: fa0a94e3  bne          x21, x0, 0x00000990  # target 0x00000990
    9ec: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    9f0: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    9f4: fffa0a13  addi         x20, x20, -1
    9f8: f80a1ae3  bne          x20, x0, 0x0000098c  # target 0x0000098c
    9fc: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    a00: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    a04: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    a08: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    a0c: 2bc0006f  jal          x0, 0x00000cc8  # target 0x00000cc8
loc_a10:
    a10: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    a14: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    a18: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    a1c: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    a20: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    a24: 01507033  and          x0, x0, x21
    a28: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    a2c: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
    a30: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000001
    a34: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    a38: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000008
    a3c: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    a40: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
    a44: 37120ab7  lui          x21, 0x37120  # x21 = 0x37120000
    a48: 004a8a93  addi         x21, x21, 4  # x21 = 0x37120004
    a4c: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    a50: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    a54: 04040ab7  lui          x21, 0x04040  # x21 = 0x04040000
    a58: 050a8a93  addi         x21, x21, 80  # x21 = 0x04040050
    a5c: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x04040050; MOP template instruction · REPLAY start_idx=16, len=5, execute_while_loading=0, load_mode=0
    a60: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    a64: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    a68: 04040ab7  lui          x21, 0x04040  # x21 = 0x04040000
    a6c: 050a8a93  addi         x21, x21, 80  # x21 = 0x04040050
    a70: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x04040050; MOP template instruction · REPLAY start_idx=16, len=5, execute_while_loading=0, load_mode=0
    a74: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x04040050; MOP template instruction · REPLAY start_idx=16, len=5, execute_while_loading=0, load_mode=0
    a78: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    a7c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    a80: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    a84: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    a88: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    a8c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    a90: 00008067  jalr         x0, 0(x1)
loc_a94:
    a94: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    a98: c46bfffd  SFPLOADI     lreg_ind=1, instr_mod0=10, imm16=65535  # lreg_ind: L1
    a9c: c460001d  SFPLOADI     lreg_ind=1, instr_mod0=8, imm16=7  # lreg_ind: L1
    aa0: c4a80005  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=1  # lreg_ind: L2
    aa4: c4a00001  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=0  # lreg_ind: L2
    aa8: c4e80001  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=0  # lreg_ind: L3
    aac: c4e3ffc1  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=65520  # lreg_ind: L3
    ab0: c5680001  SFPLOADI     lreg_ind=5, instr_mod0=10, imm16=0  # lreg_ind: L5
    ab4: c5610f81  SFPLOADI     lreg_ind=5, instr_mod0=8, imm16=17376  # lreg_ind: L5
    ab8: c5a80001  SFPLOADI     lreg_ind=6, instr_mod0=10, imm16=0  # lreg_ind: L6
    abc: c5a30f81  SFPLOADI     lreg_ind=6, instr_mod0=8, imm16=50144  # lreg_ind: L6
    ac0: 00400a13  addi         x20, x0, 4  # x20 = 0x00000004
loc_ac4:
    ac4: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
loc_ac8:
    ac8: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    acc: f0000101  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=4, instr_mod1=0  # lreg_c: L0; lreg_dest: L4
    ad0: ebfb0105  SFPSHFT      imm12_math=4076, lreg_c=0, lreg_dest=4, instr_mod1=1  # lreg_c: L0; lreg_dest: L4
    ad4: f8000901  SFPAND       imm12_math=0, lreg_c=2, lreg_dest=4, instr_mod1=0  # lreg_c: L2; lreg_dest: L4
    ad8: e4000511  SFPIADD      imm12_math=0, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4
    adc: e4001011  SFPIADD      imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=4  # lreg_c: L4; lreg_dest: L0
    ae0: f8000c01  SFPAND       imm12_math=0, lreg_c=3, lreg_dest=0, instr_mod1=0  # lreg_c: L3; lreg_dest: L0
    ae4: f00015c1  SFPMOV       imm12_math=0, lreg_c=5, lreg_dest=7, instr_mod1=0  # lreg_c: L5; lreg_dest: L7
    ae8: 48001c06  SFPSWAP      imm12_math=0, lreg_src_c=7, lreg_dest=0, instr_mod1=1  # lreg_src_c: L7; lreg_dest: L0
    aec: 3c000002  SFPNOP
    af0: f00019c1  SFPMOV       imm12_math=0, lreg_c=6, lreg_dest=7, instr_mod1=0  # lreg_c: L6; lreg_dest: L7
    af4: 480001c6  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=7, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L7
    af8: 3c000002  SFPNOP
    afc: f4000105  SFPABS       imm12_math=0, lreg_c=0, lreg_dest=4, instr_mod1=1  # lreg_c: L0; lreg_dest: L4
    b00: c5e80001  SFPLOADI     lreg_ind=7, instr_mod0=10, imm16=0  # lreg_ind: L7
    b04: c5e0f201  SFPLOADI     lreg_ind=7, instr_mod0=8, imm16=15488  # lreg_ind: L7
    b08: e40011d9  SFPIADD      imm12_math=0, lreg_c=4, lreg_dest=7, instr_mod1=6  # lreg_c: L4; lreg_dest: L7
    b0c: ebf841c5  SFPSHFT      imm12_math=4065, lreg_c=0, lreg_dest=7, instr_mod1=1  # lreg_c: L0; lreg_dest: L7
    b10: e7ffddd5  SFPIADD      imm12_math=4095, lreg_c=7, lreg_dest=7, instr_mod1=5  # lreg_c: L7; lreg_dest: L7
    b14: f8001c01  SFPAND       imm12_math=0, lreg_c=7, lreg_dest=0, instr_mod1=0  # lreg_c: L7; lreg_dest: L0
    b18: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    b1c: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    b20: fffa8a93  addi         x21, x21, -1
    b24: fa0a92e3  bne          x21, x0, 0x00000ac8  # target 0x00000ac8
    b28: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    b2c: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    b30: fffa0a13  addi         x20, x20, -1
    b34: f80a18e3  bne          x20, x0, 0x00000ac4  # target 0x00000ac4
    b38: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    b3c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    b40: 00008067  jalr         x0, 0(x1)
loc_b44:
    b44: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    b48: c5e80001  SFPLOADI     lreg_ind=7, instr_mod0=10, imm16=0  # lreg_ind: L7
    b4c: c5e00001  SFPLOADI     lreg_ind=7, instr_mod0=8, imm16=0  # lreg_ind: L7
    b50: 00000a13  addi         x20, x0, 0  # x20 = 0x00000000
    b54: 00400a93  addi         x21, x0, 4  # x21 = 0x00000004
loc_b58:
    b58: 0f5a7263  bgeu         x20, x21, 0x00000c3c  # target 0x00000c3c
    b5c: 40310000  ZEROACC      clear_mode=1, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=0
    b60: 40310004  ZEROACC      clear_mode=1, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=1
    b64: 40310008  ZEROACC      clear_mode=1, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=2
    b68: 4031000c  ZEROACC      clear_mode=1, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=3
    b6c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    b70: 88800602  STALLWAIT    stall_res=64, wait_res=384  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD | Wait.SRCB_VLD
    b74: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    b78: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    b7c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    b80: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    b84: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    b88: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    b8c: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    b90: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    b94: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    b98: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    b9c: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    ba0: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    ba4: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    ba8: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    bac: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    bb0: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    bb4: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    bb8: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    bbc: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    bc0: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    bc4: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    bc8: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    bcc: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    bd0: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    bd4: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    bd8: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    bdc: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    be0: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    be4: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    be8: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    bec: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    bf0: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    bf4: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    bf8: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    bfc: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    c00: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    c04: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    c08: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    c0c: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    c10: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    c14: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    c18: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    c1c: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    c20: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    c24: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    c28: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    c2c: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    c30: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    c34: 001a0a13  addi         x20, x20, 1
    c38: f21ff06f  jal          x0, 0x00000b58  # target 0x00000b58
loc_c3c:
    c3c: f0001c01  SFPMOV       imm12_math=0, lreg_c=7, lreg_dest=0, instr_mod1=0  # lreg_c: L7; lreg_dest: L0
    c40: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    c44: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    c48: 3c000002  SFPNOP
    c4c: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    c50: 3c000002  SFPNOP
    c54: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    c58: 3c000002  SFPNOP
    c5c: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    c60: 3c000002  SFPNOP
    c64: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    c68: 3c000002  SFPNOP
    c6c: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    c70: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    c74: 3c000002  SFPNOP
    c78: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    c7c: 3c000002  SFPNOP
    c80: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    c84: 3c000002  SFPNOP
    c88: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    c8c: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    c90: 3c000002  SFPNOP
    c94: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    c98: 3c000002  SFPNOP
    c9c: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    ca0: f0000081  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=2, instr_mod1=0  # lreg_c: L0; lreg_dest: L2
    ca4: f00000c1  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=3, instr_mod1=0  # lreg_c: L0; lreg_dest: L3
    ca8: 30000002  SFPTRANSP    imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    cac: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    cb0: 3c000002  SFPNOP
    cb4: 14280802  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=2, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L2; lreg_dest: L0
    cb8: 3c000002  SFPNOP
    cbc: 14280c02  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=3, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L3; lreg_dest: L0
    cc0: 3c000002  SFPNOP
    cc4: 00008067  jalr         x0, 0(x1)
    cc8:           j FW_TRISC1+4   # return to firmware, linked at install
