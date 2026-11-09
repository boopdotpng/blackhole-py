# llama3 1B decode: down, trisc1. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama1b.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x7c0=e2e_hidden_dense_decode_token, 0x7c4=e2e_l0_down, 0x7c8=e2e_x_a, 0x7cc=e2e_x_b, 0x8140=e2e_q_compact, 0x8144=e2e_l0_down_row_start, 0x8148=dense_start, 0x814c=e2e_l0_down_rows
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama1b.py installs it resident in L1 at 0x12000+ per core.

      0: 100000c4  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=1
      4: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0; Record replay[0]; not executed here
      8: 10029dc2  SFPMAD       lreg_src_a=0, lreg_src_b=10, lreg_src_c=7, lreg_dest=7, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L10 · constant 1 (0x3f800000); lreg_src_c: L7; lreg_dest: L7; Record replay[1]; not executed here
      c: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0  # Record replay[2]; not executed here
     10: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
     14: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
     18: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
     1c: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
     20: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
     24: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
     28: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
     2c: 3c000002  SFPNOP       
     30: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
     34: c8302022  SETC16       setc16_reg=12, setc16_value=2056  # thread_cfg[12] (current thread); ADDR_MOD_AB_SEC0_SrcAIncr = 8; ADDR_MOD_AB_SEC0_SrcACR = 0; ADDR_MOD_AB_SEC0_SrcAClear = 0; ADDR_MOD_AB_SEC0_SrcBIncr = 8; ADDR_MOD_AB_SEC0_SrcBCR = 0; ADDR_MOD_AB_SEC0_SrcBClear = 0
     38: c8700022  SETC16       setc16_reg=28, setc16_value=8  # thread_cfg[28] (current thread); ADDR_MOD_DST_SEC0_DestIncr = 8; ADDR_MOD_DST_SEC0_DestCR = 0; ADDR_MOD_DST_SEC0_DestClear = 0; ADDR_MOD_DST_SEC0_DestCToCR = 0; ADDR_MOD_DST_SEC0_FidelityIncr = 0; ADDR_MOD_DST_SEC0_FidelityClear = 0
     3c: c8bc0002  SETC16       setc16_reg=47, setc16_value=0  # thread_cfg[47] (current thread); ADDR_MOD_BIAS_SEC0_BiasIncr = 0; ADDR_MOD_BIAS_SEC0_BiasClear = 0
     40: c8340002  SETC16       setc16_reg=13, setc16_value=0  # thread_cfg[13] (current thread); ADDR_MOD_AB_SEC1_SrcAIncr = 0; ADDR_MOD_AB_SEC1_SrcACR = 0; ADDR_MOD_AB_SEC1_SrcAClear = 0; ADDR_MOD_AB_SEC1_SrcBIncr = 0; ADDR_MOD_AB_SEC1_SrcBCR = 0; ADDR_MOD_AB_SEC1_SrcBClear = 0
     44: c8740002  SETC16       setc16_reg=29, setc16_value=0  # thread_cfg[29] (current thread); ADDR_MOD_DST_SEC1_DestIncr = 0; ADDR_MOD_DST_SEC1_DestCR = 0; ADDR_MOD_DST_SEC1_DestClear = 0; ADDR_MOD_DST_SEC1_DestCToCR = 0; ADDR_MOD_DST_SEC1_FidelityIncr = 0; ADDR_MOD_DST_SEC1_FidelityClear = 0
     48: c8c00002  SETC16       setc16_reg=48, setc16_value=0  # thread_cfg[48] (current thread); ADDR_MOD_BIAS_SEC1_BiasIncr = 0; ADDR_MOD_BIAS_SEC1_BiasClear = 0
     4c: c83a0202  SETC16       setc16_reg=14, setc16_value=32896  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 0; ADDR_MOD_AB_SEC2_SrcACR = 0; ADDR_MOD_AB_SEC2_SrcAClear = 1; ADDR_MOD_AB_SEC2_SrcBIncr = 0; ADDR_MOD_AB_SEC2_SrcBCR = 0; ADDR_MOD_AB_SEC2_SrcBClear = 1
     50: c8789002  SETC16       setc16_reg=30, setc16_value=9216  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 0; ADDR_MOD_DST_SEC2_DestCR = 1; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 1; ADDR_MOD_DST_SEC2_FidelityClear = 0
     54: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
     58: c83e0202  SETC16       setc16_reg=15, setc16_value=32896  # thread_cfg[15] (current thread); ADDR_MOD_AB_SEC3_SrcAIncr = 0; ADDR_MOD_AB_SEC3_SrcACR = 0; ADDR_MOD_AB_SEC3_SrcAClear = 1; ADDR_MOD_AB_SEC3_SrcBIncr = 0; ADDR_MOD_AB_SEC3_SrcBCR = 0; ADDR_MOD_AB_SEC3_SrcBClear = 1
     5c: c87e4022  SETC16       setc16_reg=31, setc16_value=36872  # thread_cfg[31] (current thread); ADDR_MOD_DST_SEC3_DestIncr = 8; ADDR_MOD_DST_SEC3_DestCR = 0; ADDR_MOD_DST_SEC3_DestClear = 0; ADDR_MOD_DST_SEC3_DestCToCR = 1; ADDR_MOD_DST_SEC3_FidelityIncr = 0; ADDR_MOD_DST_SEC3_FidelityClear = 1
     60: c8c80002  SETC16       setc16_reg=50, setc16_value=0  # thread_cfg[50] (current thread); ADDR_MOD_BIAS_SEC3_BiasIncr = 0; ADDR_MOD_BIAS_SEC3_BiasClear = 0
     64: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
     68: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
     6c: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
     70: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
     74: 00507033  and          x0, x0, x5
     78: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
     7c: 00200293  addi         x5, x0, 2  # x5 = 0x00000002
     80: 00522023  sw           x5, 0(x4)  # MOP_CFG · 0xffb80000; write 0x00000002
     84: 00522223  sw           x5, 4(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
     88: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     8c: 00522423  sw           x5, 8(x4)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP 
     90: 00522623  sw           x5, 12(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x02000000; MOP template instruction · NOP 
     94: 00522823  sw           x5, 16(x4)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP 
     98: 270002b7  lui          x5, 0x27000  # x5 = 0x27000000
     9c: 00522a23  sw           x5, 20(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x27000000; MOP template instruction · ELWMUL clear_dvalid=0, dest_accum_en=0, instr_mod19=0, addr_mode=0, dst=0
     a0: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     a4: 00522c23  sw           x5, 24(x4)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP 
     a8: 27c0c2b7  lui          x5, 0x27c0c  # x5 = 0x27c0c000
     ac: 00522e23  sw           x5, 28(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x27c0c000; MOP template instruction · ELWMUL clear_dvalid=3, dest_accum_en=0, instr_mod19=0, addr_mode=3, dst=0
     b0: 270082b7  lui          x5, 0x27008  # x5 = 0x27008000
     b4: 02522023  sw           x5, 32(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x27008000; MOP template instruction · ELWMUL clear_dvalid=0, dest_accum_en=0, instr_mod19=0, addr_mode=2, dst=0
     b8: 000082b7  lui          x5, 0x00008  # x5 = 0x00008000
     bc: 14c28293  addi         x5, x5, 332  # x5 = 0x0000814c
     c0: 0002a203  lw           x4, 0(x5)  # param e2e_l0_down_rows; 0x0000814c
     c4: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
     c8: 00020313  addi         x6, x4, 0
loc_cc:
     cc: 1862fe63  bgeu         x5, x6, 0x00000268  # target 0x00000268
     d0: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
     d4: c5e80001  SFPLOADI     lreg_ind=7, instr_mod0=10, imm16=0  # lreg_ind: L7
     d8: c5e00001  SFPLOADI     lreg_ind=7, instr_mod0=8, imm16=0  # lreg_ind: L7
     dc: 00000a13  addi         x20, x0, 0  # x20 = 0x00000000
     e0: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
loc_e4:
     e4: 0f5a7263  bgeu         x20, x21, 0x000001c8  # target 0x000001c8
     e8: 40310000  ZEROACC      clear_mode=1, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=0
     ec: 40310004  ZEROACC      clear_mode=1, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=1
     f0: 40310008  ZEROACC      clear_mode=1, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=2
     f4: 4031000c  ZEROACC      clear_mode=1, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=3
     f8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
     fc: 88800602  STALLWAIT    stall_res=64, wait_res=384  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD | Wait.SRCB_VLD
    100: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    104: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    108: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    10c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    110: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    114: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    118: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    11c: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    120: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    124: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    128: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    12c: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    130: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    134: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    138: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    13c: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    140: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    144: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    148: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    14c: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    150: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    154: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    158: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    15c: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    160: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    164: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    168: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    16c: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    170: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    174: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    178: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    17c: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    180: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    184: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    188: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    18c: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    190: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    194: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    198: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    19c: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    1a0: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    1a4: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    1a8: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    1ac: 100000c0  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=0
    1b0: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    1b4: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    1b8: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    1bc: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    1c0: 001a0a13  addi         x20, x20, 1
    1c4: f21ff06f  jal          x0, 0x000000e4  # target 0x000000e4
loc_1c8:
    1c8: f0001c01  SFPMOV       imm12_math=0, lreg_c=7, lreg_dest=0, instr_mod1=0  # lreg_c: L7; lreg_dest: L0
    1cc: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    1d0: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    1d4: 3c000002  SFPNOP       
    1d8: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    1dc: 3c000002  SFPNOP       
    1e0: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    1e4: 3c000002  SFPNOP       
    1e8: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    1ec: 3c000002  SFPNOP       
    1f0: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    1f4: 3c000002  SFPNOP       
    1f8: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    1fc: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    200: 3c000002  SFPNOP       
    204: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    208: 3c000002  SFPNOP       
    20c: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    210: 3c000002  SFPNOP       
    214: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    218: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    21c: 3c000002  SFPNOP       
    220: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    224: 3c000002  SFPNOP       
    228: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    22c: f0000081  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=2, instr_mod1=0  # lreg_c: L0; lreg_dest: L2
    230: f00000c1  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=3, instr_mod1=0  # lreg_c: L0; lreg_dest: L3
    234: 30000002  SFPTRANSP    imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    238: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    23c: 3c000002  SFPNOP       
    240: 14280802  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=2, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L2; lreg_dest: L0
    244: 3c000002  SFPNOP       
    248: 14280c02  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=3, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L3; lreg_dest: L0
    24c: 3c000002  SFPNOP       
    250: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    254: 3c000002  SFPNOP       
    258: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    25c: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    260: 00128293  addi         x5, x5, 1
    264: e69ff06f  jal          x0, 0x000000cc  # target 0x000000cc
loc_268:
    268: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    26c: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    270: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    274: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    278: d8800006  RMWCIB3      Mask=32, Data=0, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 0
    27c: c8382022  SETC16       setc16_reg=14, setc16_value=2056  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 8; ADDR_MOD_AB_SEC2_SrcACR = 0; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 8; ADDR_MOD_AB_SEC2_SrcBCR = 0; ADDR_MOD_AB_SEC2_SrcBClear = 0
    280: c8780022  SETC16       setc16_reg=30, setc16_value=8  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 8; ADDR_MOD_DST_SEC2_DestCR = 0; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 0; ADDR_MOD_DST_SEC2_FidelityClear = 0
    284: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
    288: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    28c: 88800602  STALLWAIT    stall_res=64, wait_res=384  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD | Wait.SRCB_VLD
    290: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
    294: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    298: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    29c: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    2a0: 00507033  and          x0, x0, x5
    2a4: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
    2a8: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
    2ac: 00522023  sw           x5, 0(x4)  # MOP_CFG · 0xffb80000; write 0x00000004
    2b0: 00200293  addi         x5, x0, 2  # x5 = 0x00000002
    2b4: 00522223  sw           x5, 4(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
    2b8: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    2bc: 00522423  sw           x5, 8(x4)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP 
    2c0: 37c002b7  lui          x5, 0x37c00  # x5 = 0x37c00000
    2c4: 00328293  addi         x5, x5, 3  # x5 = 0x37c00003
    2c8: 00522623  sw           x5, 12(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37c00003; MOP template instruction · SETRWC clear_ab_vld=3, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=3
    2cc: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    2d0: 00522823  sw           x5, 16(x4)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP 
    2d4: 280082b7  lui          x5, 0x28008  # x5 = 0x28008000
    2d8: 00522a23  sw           x5, 20(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x28008000; MOP template instruction · ELWADD clear_dvalid=0, dest_accum_en=0, instr_mod19=0, addr_mode=2, dst=0
    2dc: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    2e0: 00522c23  sw           x5, 24(x4)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP 
    2e4: 280082b7  lui          x5, 0x28008  # x5 = 0x28008000
    2e8: 00522e23  sw           x5, 28(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x28008000; MOP template instruction · ELWADD clear_dvalid=0, dest_accum_en=0, instr_mod19=0, addr_mode=2, dst=0
    2ec: 02522023  sw           x5, 32(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x28008000; MOP template instruction · ELWADD clear_dvalid=0, dest_accum_en=0, instr_mod19=0, addr_mode=2, dst=0
    2f0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2f4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    2f8: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    2fc: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    300:           j FW_TRISC1+4   # return to firmware, linked at install
