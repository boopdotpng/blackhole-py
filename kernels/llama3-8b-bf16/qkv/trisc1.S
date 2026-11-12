# llama3 8b-bf16 decode: qkv, trisc1. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x780=e2e_x_a_decode_token, 0x784=e2e_l0_q, 0x788=e2e_l0_k, 0x78c=e2e_l0_v, 0x790=e2e_l0_input_norm, 0xe8c0=e2e_q_compact, 0xe8c4=e2e_l0_q_row_start, 0xe8c8=e2e_k_compact, 0xe8cc=e2e_l0_k_row_start, 0xe8d0=e2e_v_compact, 0xe8d4=e2e_l0_v_row_start, 0xe8d8=e2e_l0_q_rows, 0xe8dc=e2e_l0_k_rows, 0xe8e0=e2e_l0_v_rows, 0xe8e4=dram_port
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
     4c: 101000c4  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=1
     50: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0; Record replay[16]; not executed here
     54: 10029dc2  SFPMAD       lreg_src_a=0, lreg_src_b=10, lreg_src_c=7, lreg_dest=7, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L10 · constant 1 (0x3f800000); lreg_src_c: L7; lreg_dest: L7; Record replay[17]; not executed here
     58: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0  # Record replay[18]; not executed here
     5c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
     60: 3c000002  SFPNOP
     64: 18002702  SFPMUL       lreg_src_a=0, lreg_src_b=0, lreg_src_c=9, lreg_dest=12, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L0; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L12
     68: 46100106  SFPCONFIG    imm16_math=33792, config_dest=4, instr_mod1=1
     6c: 443c0206  SFPCONFIG    imm16_math=3840, config_dest=8, instr_mod1=1
     70: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
     74: c8380022  SETC16       setc16_reg=14, setc16_value=8  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 8; ADDR_MOD_AB_SEC2_SrcACR = 0; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 0; ADDR_MOD_AB_SEC2_SrcBCR = 0; ADDR_MOD_AB_SEC2_SrcBClear = 0
     78: c8780022  SETC16       setc16_reg=30, setc16_value=8  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 8; ADDR_MOD_DST_SEC2_DestCR = 0; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 0; ADDR_MOD_DST_SEC2_FidelityClear = 0
     7c: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
     80: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
     84: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
     88: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
     8c: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
     90: 00507033  and          x0, x0, x5
     94: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
     98: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     9c: 00522023  sw           x5, 0(x4)  # MOP_CFG · 0xffb80000; write 0x00000004
     a0: 00200293  addi         x5, x0, 2  # x5 = 0x00000002
     a4: 00522223  sw           x5, 4(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
     a8: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     ac: 00522423  sw           x5, 8(x4)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
     b0: 37c002b7  lui          x5, 0x37c00  # x5 = 0x37c00000
     b4: 00328293  addi         x5, x5, 3  # x5 = 0x37c00003
     b8: 00522623  sw           x5, 12(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37c00003; MOP template instruction · SETRWC clear_ab_vld=3, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=3
     bc: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     c0: 00522823  sw           x5, 16(x4)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
     c4: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
     c8: 00522a23  sw           x5, 20(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
     cc: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     d0: 00522c23  sw           x5, 24(x4)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
     d4: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
     d8: 00522e23  sw           x5, 28(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
     dc: 02522023  sw           x5, 32(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
     e0: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
     e4: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
     e8: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
     ec: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
     f0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
     f4: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
     f8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
     fc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    100: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    104: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    108: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    10c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    110: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    114: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    118: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    11c: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    120: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    124: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    128: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    12c: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    130: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    134: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    138: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    13c: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    140: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    144: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    148: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    14c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    150: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    154: c8040402  SETC16       setc16_reg=1, setc16_value=256  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 256
    158: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    15c: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    160: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    164: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    168: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    16c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    170: c8040502  SETC16       setc16_reg=1, setc16_value=320  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 320
    174: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    178: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    17c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    180: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    184: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    188: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    18c: c8040602  SETC16       setc16_reg=1, setc16_value=384  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 384
    190: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    194: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    198: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    19c: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    1a0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1a4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    1a8: c8040702  SETC16       setc16_reg=1, setc16_value=448  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 448
    1ac: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    1b0: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    1b4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    1b8: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    1bc: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1c0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    1c4: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    1c8: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    1cc: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    1d0: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    1d4: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    1d8: 3c000002  SFPNOP
    1dc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    1e0: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    1e4: c4000001  SFPLOADI     lreg_ind=0, instr_mod0=0, imm16=0  # lreg_ind: L0
    1e8: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
    1ec: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    1f0: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    1f4: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    1f8: 00507033  and          x0, x0, x5
    1fc: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
    200: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
    204: 00522023  sw           x5, 0(x4)  # MOP_CFG · 0xffb80000; write 0x00000001
    208: 00800293  addi         x5, x0, 8  # x5 = 0x00000008
    20c: 00522223  sw           x5, 4(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000008
    210: 371202b7  lui          x5, 0x37120  # x5 = 0x37120000
    214: 00428293  addi         x5, x5, 4  # x5 = 0x37120004
    218: 00522623  sw           x5, 12(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    21c: 00522823  sw           x5, 16(x4)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    220: 040002b7  lui          x5, 0x04000  # x5 = 0x04000000
    224: 03028293  addi         x5, x5, 48  # x5 = 0x04000030
    228: 00522a23  sw           x5, 20(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x04000030; MOP template instruction · REPLAY start_idx=0, len=3, execute_while_loading=0, load_mode=0
    22c: 00522e23  sw           x5, 28(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x04000030; MOP template instruction · REPLAY start_idx=0, len=3, execute_while_loading=0, load_mode=0
    230: 02522023  sw           x5, 32(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x04000030; MOP template instruction · REPLAY start_idx=0, len=3, execute_while_loading=0, load_mode=0
    234: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    238: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    23c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    240: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    244: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    248: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    24c: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    250: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    254: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    258: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    25c: 3c000002  SFPNOP
    260: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    264: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    268: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
    26c: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    270: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    274: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    278: 00507033  and          x0, x0, x5
    27c: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
    280: 01420213  addi         x4, x4, 20  # x4 = 0xffb80014 · MopCfg[5] · LoopOp / InsnA2
    284: 0400c2b7  lui          x5, 0x0400c  # x5 = 0x0400c000
    288: 03028293  addi         x5, x5, 48  # x5 = 0x0400c030
    28c: 00522023  sw           x5, 0(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x0400c030; MOP template instruction · REPLAY start_idx=3, len=3, execute_while_loading=0, load_mode=0
    290: 00522423  sw           x5, 8(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x0400c030; MOP template instruction · REPLAY start_idx=3, len=3, execute_while_loading=0, load_mode=0
    294: 00522623  sw           x5, 12(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x0400c030; MOP template instruction · REPLAY start_idx=3, len=3, execute_while_loading=0, load_mode=0
    298: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    29c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2a0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2a4: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2a8: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    2ac: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    2b0: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    2b4: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    2b8: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    2bc: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    2c0: 3c000002  SFPNOP
    2c4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    2c8: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    2cc: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2d0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2d4: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2d8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2dc: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    2e0: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    2e4: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    2e8: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    2ec: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    2f0: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    2f4: 3c000002  SFPNOP
    2f8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    2fc: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    300: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    304: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    308: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    30c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    310: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    314: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    318: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    31c: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    320: 3c000002  SFPNOP
    324: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    328: 3c000002  SFPNOP
    32c: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    330: 3c000002  SFPNOP
    334: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    338: 3c000002  SFPNOP
    33c: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    340: 3c000002  SFPNOP
    344: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    348: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    34c: 3c000002  SFPNOP
    350: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    354: 3c000002  SFPNOP
    358: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    35c: 3c000002  SFPNOP
    360: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    364: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    368: 3c000002  SFPNOP
    36c: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    370: 3c000002  SFPNOP
    374: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    378: f0000081  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=2, instr_mod1=0  # lreg_c: L0; lreg_dest: L2
    37c: f00000c1  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=3, instr_mod1=0  # lreg_c: L0; lreg_dest: L3
    380: 30000002  SFPTRANSP    imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    384: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    388: 3c000002  SFPNOP
    38c: 14280802  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=2, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L2; lreg_dest: L0
    390: 3c000002  SFPNOP
    394: 14280c02  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=3, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L3; lreg_dest: L0
    398: 3c000002  SFPNOP
    39c: c5280001  SFPLOADI     lreg_ind=4, instr_mod0=10, imm16=0  # lreg_ind: L4
    3a0: c520e601  SFPLOADI     lreg_ind=4, instr_mod0=8, imm16=14720  # lreg_ind: L4
    3a4: 18012402  SFPMUL       lreg_src_a=0, lreg_src_b=4, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    3a8: c52b16b1  SFPLOADI     lreg_ind=4, instr_mod0=10, imm16=50604  # lreg_ind: L4
    3ac: c520dc9d  SFPLOADI     lreg_ind=4, instr_mod0=8, imm16=14119  # lreg_ind: L4
    3b0: 14281002  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=4, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L4; lreg_dest: L0
    3b4: 3c000002  SFPNOP
    3b8: f0000181  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=6, instr_mod1=0  # lreg_c: L0; lreg_dest: L6
    3bc: f0001841  SFPMOV       imm12_math=0, lreg_c=6, lreg_dest=1, instr_mod1=0  # lreg_c: L6; lreg_dest: L1
    3c0: ebffe445  SFPSHFT      imm12_math=4095, lreg_c=9, lreg_dest=1, instr_mod1=1  # lreg_c: L9 · constant 0 (0x00000000); lreg_dest: L1
    3c4: c4a84281  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=4256  # lreg_ind: L2
    3c8: c4a17c45  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=24337  # lreg_ind: L2
    3cc: e4000859  SFPIADD      imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=6  # lreg_c: L2; lreg_dest: L1
    3d0: 18186482  SFPMUL       lreg_src_a=6, lreg_src_b=1, lreg_src_c=9, lreg_dest=2, instr_mod1=0  # lreg_src_a: L6; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L2
    3d4: 3c000002  SFPNOP
    3d8: 1804a486  SFPMUL       lreg_src_a=1, lreg_src_b=2, lreg_src_c=9, lreg_dest=2, instr_mod1=1  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L2
    3dc: c4e85325  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=5321  # lreg_ind: L3
    3e0: c4e10049  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=16402  # lreg_ind: L3
    3e4: c528d899  SFPLOADI     lreg_ind=4, instr_mod0=10, imm16=13862  # lreg_ind: L4
    3e8: c5210041  SFPLOADI     lreg_ind=4, instr_mod0=8, imm16=16400  # lreg_ind: L4
    3ec: 14290902  SFPADD       lreg_src_a=10, lreg_src_b=4, lreg_src_c=2, lreg_dest=4, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L4; lreg_src_c: L2; lreg_dest: L4
    3f0: 3c000002  SFPNOP
    3f4: 10090c82  SFPMAD       lreg_src_a=2, lreg_src_b=4, lreg_src_c=3, lreg_dest=2, instr_mod1=0  # lreg_src_a: L2; lreg_src_b: L4; lreg_src_c: L3; lreg_dest: L2
    3f8: 3c000002  SFPNOP
    3fc: 1804a442  SFPMUL       lreg_src_a=1, lreg_src_b=2, lreg_src_c=9, lreg_dest=1, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L1
    400: 3c000002  SFPNOP
    404: 18186482  SFPMUL       lreg_src_a=6, lreg_src_b=1, lreg_src_c=9, lreg_dest=2, instr_mod1=0  # lreg_src_a: L6; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L2
    408: 3c000002  SFPNOP
    40c: 1804a486  SFPMUL       lreg_src_a=1, lreg_src_b=2, lreg_src_c=9, lreg_dest=2, instr_mod1=1  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L2
    410: 3c000002  SFPNOP
    414: 142a8882  SFPADD       lreg_src_a=10, lreg_src_b=10, lreg_src_c=2, lreg_dest=2, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L10 · constant 1 (0x3f800000); lreg_src_c: L2; lreg_dest: L2
    418: c5680001  SFPLOADI     lreg_ind=5, instr_mod0=10, imm16=0  # lreg_ind: L5
    41c: c560fc01  SFPLOADI     lreg_ind=5, instr_mod0=8, imm16=16128  # lreg_ind: L5
    420: 18056542  SFPMUL       lreg_src_a=1, lreg_src_b=5, lreg_src_c=9, lreg_dest=5, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L5; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L5
    424: 3c000002  SFPNOP
    428: 10094402  SFPMAD       lreg_src_a=2, lreg_src_b=5, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L2; lreg_src_b: L5; lreg_src_c: L1; lreg_dest: L0
    42c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    430: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    434: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    438: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    43c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    440: 3c000002  SFPNOP
    444: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    448: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    44c: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
    450: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    454: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    458: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    45c: 00507033  and          x0, x0, x5
    460: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
    464: 00420213  addi         x4, x4, 4  # x4 = 0xffb80004 · MopCfg[1] · InnerCount / Flags
    468: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
    46c: 00522023  sw           x5, 0(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000004
    470: 040182b7  lui          x5, 0x04018  # x5 = 0x04018000
    474: 0a028293  addi         x5, x5, 160  # x5 = 0x040180a0
    478: 00522823  sw           x5, 16(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x040180a0; MOP template instruction · REPLAY start_idx=6, len=10, execute_while_loading=0, load_mode=0
    47c: 00522c23  sw           x5, 24(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x040180a0; MOP template instruction · REPLAY start_idx=6, len=10, execute_while_loading=0, load_mode=0
    480: 00522e23  sw           x5, 28(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x040180a0; MOP template instruction · REPLAY start_idx=6, len=10, execute_while_loading=0, load_mode=0
    484: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    488: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    48c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    490: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    494: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    498: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    49c: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    4a0: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    4a4: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    4a8: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    4ac: 3c000002  SFPNOP
    4b0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    4b4: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    4b8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    4bc: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    4c0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    4c4: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    4c8: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    4cc: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    4d0: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    4d4: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    4d8: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    4dc: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    4e0: 3c000002  SFPNOP
    4e4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    4e8: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    4ec: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    4f0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    4f4: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    4f8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    4fc: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    500: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    504: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    508: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    50c: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    510: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    514: 3c000002  SFPNOP
    518: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    51c: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    520: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    524: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    528: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    52c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    530: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    534: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    538: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    53c: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    540: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    544: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    548: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    54c: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    550: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    554: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    558: 3c000002  SFPNOP
    55c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    560: c8302022  SETC16       setc16_reg=12, setc16_value=2056  # thread_cfg[12] (current thread); ADDR_MOD_AB_SEC0_SrcAIncr = 8; ADDR_MOD_AB_SEC0_SrcACR = 0; ADDR_MOD_AB_SEC0_SrcAClear = 0; ADDR_MOD_AB_SEC0_SrcBIncr = 8; ADDR_MOD_AB_SEC0_SrcBCR = 0; ADDR_MOD_AB_SEC0_SrcBClear = 0
    564: c8700022  SETC16       setc16_reg=28, setc16_value=8  # thread_cfg[28] (current thread); ADDR_MOD_DST_SEC0_DestIncr = 8; ADDR_MOD_DST_SEC0_DestCR = 0; ADDR_MOD_DST_SEC0_DestClear = 0; ADDR_MOD_DST_SEC0_DestCToCR = 0; ADDR_MOD_DST_SEC0_FidelityIncr = 0; ADDR_MOD_DST_SEC0_FidelityClear = 0
    568: c8bc0002  SETC16       setc16_reg=47, setc16_value=0  # thread_cfg[47] (current thread); ADDR_MOD_BIAS_SEC0_BiasIncr = 0; ADDR_MOD_BIAS_SEC0_BiasClear = 0
    56c: c8340002  SETC16       setc16_reg=13, setc16_value=0  # thread_cfg[13] (current thread); ADDR_MOD_AB_SEC1_SrcAIncr = 0; ADDR_MOD_AB_SEC1_SrcACR = 0; ADDR_MOD_AB_SEC1_SrcAClear = 0; ADDR_MOD_AB_SEC1_SrcBIncr = 0; ADDR_MOD_AB_SEC1_SrcBCR = 0; ADDR_MOD_AB_SEC1_SrcBClear = 0
    570: c8740002  SETC16       setc16_reg=29, setc16_value=0  # thread_cfg[29] (current thread); ADDR_MOD_DST_SEC1_DestIncr = 0; ADDR_MOD_DST_SEC1_DestCR = 0; ADDR_MOD_DST_SEC1_DestClear = 0; ADDR_MOD_DST_SEC1_DestCToCR = 0; ADDR_MOD_DST_SEC1_FidelityIncr = 0; ADDR_MOD_DST_SEC1_FidelityClear = 0
    574: c8c00002  SETC16       setc16_reg=48, setc16_value=0  # thread_cfg[48] (current thread); ADDR_MOD_BIAS_SEC1_BiasIncr = 0; ADDR_MOD_BIAS_SEC1_BiasClear = 0
    578: c83a0202  SETC16       setc16_reg=14, setc16_value=32896  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 0; ADDR_MOD_AB_SEC2_SrcACR = 0; ADDR_MOD_AB_SEC2_SrcAClear = 1; ADDR_MOD_AB_SEC2_SrcBIncr = 0; ADDR_MOD_AB_SEC2_SrcBCR = 0; ADDR_MOD_AB_SEC2_SrcBClear = 1
    57c: c8789002  SETC16       setc16_reg=30, setc16_value=9216  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 0; ADDR_MOD_DST_SEC2_DestCR = 1; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 1; ADDR_MOD_DST_SEC2_FidelityClear = 0
    580: c83e0202  SETC16       setc16_reg=15, setc16_value=32896  # thread_cfg[15] (current thread); ADDR_MOD_AB_SEC3_SrcAIncr = 0; ADDR_MOD_AB_SEC3_SrcACR = 0; ADDR_MOD_AB_SEC3_SrcAClear = 1; ADDR_MOD_AB_SEC3_SrcBIncr = 0; ADDR_MOD_AB_SEC3_SrcBCR = 0; ADDR_MOD_AB_SEC3_SrcBClear = 1
    584: c87e4022  SETC16       setc16_reg=31, setc16_value=36872  # thread_cfg[31] (current thread); ADDR_MOD_DST_SEC3_DestIncr = 8; ADDR_MOD_DST_SEC3_DestCR = 0; ADDR_MOD_DST_SEC3_DestClear = 0; ADDR_MOD_DST_SEC3_DestCToCR = 1; ADDR_MOD_DST_SEC3_FidelityIncr = 0; ADDR_MOD_DST_SEC3_FidelityClear = 1
    588: c8c80002  SETC16       setc16_reg=50, setc16_value=0  # thread_cfg[50] (current thread); ADDR_MOD_BIAS_SEC3_BiasIncr = 0; ADDR_MOD_BIAS_SEC3_BiasClear = 0
    58c: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
    590: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    594: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    598: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    59c: 00507033  and          x0, x0, x5
    5a0: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
    5a4: 00200293  addi         x5, x0, 2  # x5 = 0x00000002
    5a8: 00522023  sw           x5, 0(x4)  # MOP_CFG · 0xffb80000; write 0x00000002
    5ac: 00522223  sw           x5, 4(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
    5b0: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    5b4: 00522623  sw           x5, 12(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x02000000; MOP template instruction · NOP
    5b8: 00522823  sw           x5, 16(x4)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    5bc: 270002b7  lui          x5, 0x27000  # x5 = 0x27000000
    5c0: 00522a23  sw           x5, 20(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x27000000; MOP template instruction · ELWMUL clear_dvalid=0, dest_accum_en=0, instr_mod19=0, addr_mode=0, dst=0
    5c4: 27c0c2b7  lui          x5, 0x27c0c  # x5 = 0x27c0c000
    5c8: 00522e23  sw           x5, 28(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x27c0c000; MOP template instruction · ELWMUL clear_dvalid=3, dest_accum_en=0, instr_mod19=0, addr_mode=3, dst=0
    5cc: 270082b7  lui          x5, 0x27008  # x5 = 0x27008000
    5d0: 02522023  sw           x5, 32(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x27008000; MOP template instruction · ELWMUL clear_dvalid=0, dest_accum_en=0, instr_mod19=0, addr_mode=2, dst=0
    5d4: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    5d8: 8d828293  addi         x5, x5, -1832  # x5 = 0x0000e8d8
    5dc: 0002a203  lw           x4, 0(x5)  # param e2e_l0_q_rows; 0x0000e8d8
    5e0: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    5e4: 00020313  addi         x6, x4, 0
loc_5e8:
    5e8: 0262f063  bgeu         x5, x6, 0x00000608  # target 0x00000608
    5ec: 088000ef  jal          x1, 0x00000674  # target 0x00000674; x1 = 0x000005f0
    5f0: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    5f4: 3c000002  SFPNOP
    5f8: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    5fc: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    600: 00128293  addi         x5, x5, 1
    604: fe5ff06f  jal          x0, 0x000005e8  # target 0x000005e8
loc_608:
    608: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    60c: 8dc28293  addi         x5, x5, -1828  # x5 = 0x0000e8dc
    610: 0002a203  lw           x4, 0(x5)  # param e2e_l0_k_rows; 0x0000e8dc
    614: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    618: 00020313  addi         x6, x4, 0
loc_61c:
    61c: 0262f063  bgeu         x5, x6, 0x0000063c  # target 0x0000063c
    620: 054000ef  jal          x1, 0x00000674  # target 0x00000674; x1 = 0x00000624
    624: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    628: 3c000002  SFPNOP
    62c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    630: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    634: 00128293  addi         x5, x5, 1
    638: fe5ff06f  jal          x0, 0x0000061c  # target 0x0000061c
loc_63c:
    63c: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    640: 8e028293  addi         x5, x5, -1824  # x5 = 0x0000e8e0
    644: 0002a203  lw           x4, 0(x5)  # param e2e_l0_v_rows; 0x0000e8e0
    648: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    64c: 00020313  addi         x6, x4, 0
loc_650:
    650: 0262f063  bgeu         x5, x6, 0x00000670  # target 0x00000670
    654: 020000ef  jal          x1, 0x00000674  # target 0x00000674; x1 = 0x00000658
    658: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    65c: 3c000002  SFPNOP
    660: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    664: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    668: 00128293  addi         x5, x5, 1
    66c: fe5ff06f  jal          x0, 0x00000650  # target 0x00000650
loc_670:
    670: 1880006f  jal          x0, 0x000007f8  # target 0x000007f8
loc_674:
    674: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    678: c5e80001  SFPLOADI     lreg_ind=7, instr_mod0=10, imm16=0  # lreg_ind: L7
    67c: c5e00001  SFPLOADI     lreg_ind=7, instr_mod0=8, imm16=0  # lreg_ind: L7
    680: 00000a13  addi         x20, x0, 0  # x20 = 0x00000000
    684: 00400a93  addi         x21, x0, 4  # x21 = 0x00000004
loc_688:
    688: 0f5a7263  bgeu         x20, x21, 0x0000076c  # target 0x0000076c
    68c: 40310000  ZEROACC      clear_mode=1, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=0
    690: 40310004  ZEROACC      clear_mode=1, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=1
    694: 40310008  ZEROACC      clear_mode=1, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=2
    698: 4031000c  ZEROACC      clear_mode=1, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=3
    69c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    6a0: 88800602  STALLWAIT    stall_res=64, wait_res=384  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD | Wait.SRCB_VLD
    6a4: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    6a8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    6ac: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    6b0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    6b4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    6b8: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    6bc: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6c0: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6c4: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6c8: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6cc: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6d0: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6d4: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6d8: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6dc: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    6e0: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    6e4: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6e8: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6ec: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6f0: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6f4: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6f8: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6fc: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    700: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    704: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    708: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    70c: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    710: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    714: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    718: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    71c: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    720: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    724: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    728: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    72c: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    730: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    734: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    738: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    73c: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    740: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    744: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    748: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    74c: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    750: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    754: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    758: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    75c: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    760: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    764: 001a0a13  addi         x20, x20, 1
    768: f21ff06f  jal          x0, 0x00000688  # target 0x00000688
loc_76c:
    76c: f0001c01  SFPMOV       imm12_math=0, lreg_c=7, lreg_dest=0, instr_mod1=0  # lreg_c: L7; lreg_dest: L0
    770: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    774: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    778: 3c000002  SFPNOP
    77c: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    780: 3c000002  SFPNOP
    784: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    788: 3c000002  SFPNOP
    78c: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    790: 3c000002  SFPNOP
    794: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    798: 3c000002  SFPNOP
    79c: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    7a0: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    7a4: 3c000002  SFPNOP
    7a8: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    7ac: 3c000002  SFPNOP
    7b0: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    7b4: 3c000002  SFPNOP
    7b8: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    7bc: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    7c0: 3c000002  SFPNOP
    7c4: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    7c8: 3c000002  SFPNOP
    7cc: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    7d0: f0000081  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=2, instr_mod1=0  # lreg_c: L0; lreg_dest: L2
    7d4: f00000c1  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=3, instr_mod1=0  # lreg_c: L0; lreg_dest: L3
    7d8: 30000002  SFPTRANSP    imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    7dc: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    7e0: 3c000002  SFPNOP
    7e4: 14280802  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=2, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L2; lreg_dest: L0
    7e8: 3c000002  SFPNOP
    7ec: 14280c02  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=3, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L3; lreg_dest: L0
    7f0: 3c000002  SFPNOP
    7f4: 00008067  jalr         x0, 0(x1)
    7f8:           j FW_TRISC1+4   # return to firmware, linked at install
