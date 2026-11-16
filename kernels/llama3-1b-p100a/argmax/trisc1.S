# llama3 1b decode: argmax, trisc1. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5 7,6 7,7 7,8 7,9 7,10 7,11 10,2 10,3 10,4 10,5 10,6 10,7 10,8 10,9 10,10 10,11 11,2 11,3 11,4 11,5 11,6 11,7 11,8 11,9
# params: 0x7c0=e2e_token_history, 0x7c4=argmax_host_address, 0x7c8=write_pos, 0x7cc=write_token, 0x81c0=e2e_logits, 0x81c4=argmax_start, 0x81c8=argmax_count, 0x81cc=argmax_core
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama3.py installs it resident in L1 at 0x12000+ per core.

      0: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
      4: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
      8: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
      c: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
     10: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
     14: cc04040a  RMWCIB0      Mask=1, Data=1, CfgRegAddr=2  # cfg[2] (current thread StateID); ALU_ACC_CTRL_Zero_Flag_disabled_src = 1
     18: c8300002  SETC16       setc16_reg=12, setc16_value=0  # thread_cfg[12] (current thread); ADDR_MOD_AB_SEC0_SrcAIncr = 0; ADDR_MOD_AB_SEC0_SrcACR = 0; ADDR_MOD_AB_SEC0_SrcAClear = 0; ADDR_MOD_AB_SEC0_SrcBIncr = 0; ADDR_MOD_AB_SEC0_SrcBCR = 0; ADDR_MOD_AB_SEC0_SrcBClear = 0
     1c: c8700002  SETC16       setc16_reg=28, setc16_value=0  # thread_cfg[28] (current thread); ADDR_MOD_DST_SEC0_DestIncr = 0; ADDR_MOD_DST_SEC0_DestCR = 0; ADDR_MOD_DST_SEC0_DestClear = 0; ADDR_MOD_DST_SEC0_DestCToCR = 0; ADDR_MOD_DST_SEC0_FidelityIncr = 0; ADDR_MOD_DST_SEC0_FidelityClear = 0
     20: c8bc0002  SETC16       setc16_reg=47, setc16_value=0  # thread_cfg[47] (current thread); ADDR_MOD_BIAS_SEC0_BiasIncr = 0; ADDR_MOD_BIAS_SEC0_BiasClear = 0
     24: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
     28: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
     2c: 90000802  SEMPOST      sem_sel=128  # sem_sel: Sem.MATH_DONE
     30: 98040046  SEMWAIT      stall_res=2, sem_sel=4, wait_sem_cond=1  # stall_res: Stall.SYNC; sem_sel: Sem.UNPACK_TO_DEST; wait_sem_cond: SemWait.ON_ZERO
     34: 94000042  SEMGET       sem_sel=4  # sem_sel: Sem.UNPACK_TO_DEST
     38: 88800602  STALLWAIT    stall_res=64, wait_res=384  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD | Wait.SRCB_VLD
     3c: 48008000  MOVA2D       dest_32b_lo=0, src=0, addr_mode=0, instr_mod=2, dst=0
     40: 48408020  MOVA2D       dest_32b_lo=0, src=8, addr_mode=0, instr_mod=2, dst=8
     44: 48808040  MOVA2D       dest_32b_lo=0, src=16, addr_mode=0, instr_mod=2, dst=16
     48: 48c08060  MOVA2D       dest_32b_lo=0, src=24, addr_mode=0, instr_mod=2, dst=24
     4c: 49008080  MOVA2D       dest_32b_lo=0, src=32, addr_mode=0, instr_mod=2, dst=32
     50: 494080a0  MOVA2D       dest_32b_lo=0, src=40, addr_mode=0, instr_mod=2, dst=40
     54: 498080c0  MOVA2D       dest_32b_lo=0, src=48, addr_mode=0, instr_mod=2, dst=48
     58: 49c080e0  MOVA2D       dest_32b_lo=0, src=56, addr_mode=0, instr_mod=2, dst=56
     5c: df00003c  SETRWC       clear_ab_vld=3, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
     60: 88040042  STALLWAIT    stall_res=2, wait_res=16  # stall_res: Stall.SYNC; wait_res: Wait.MATH
     64: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
     68: 90000802  SEMPOST      sem_sel=128  # sem_sel: Sem.MATH_DONE
     6c: 98040046  SEMWAIT      stall_res=2, sem_sel=4, wait_sem_cond=1  # stall_res: Stall.SYNC; sem_sel: Sem.UNPACK_TO_DEST; wait_sem_cond: SemWait.ON_ZERO
     70: 94000042  SEMGET       sem_sel=4  # sem_sel: Sem.UNPACK_TO_DEST
     74: 88800602  STALLWAIT    stall_res=64, wait_res=384  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD | Wait.SRCB_VLD
     78: 48008100  MOVA2D       dest_32b_lo=0, src=0, addr_mode=0, instr_mod=2, dst=64
     7c: 48408120  MOVA2D       dest_32b_lo=0, src=8, addr_mode=0, instr_mod=2, dst=72
     80: 48808140  MOVA2D       dest_32b_lo=0, src=16, addr_mode=0, instr_mod=2, dst=80
     84: 48c08160  MOVA2D       dest_32b_lo=0, src=24, addr_mode=0, instr_mod=2, dst=88
     88: 49008180  MOVA2D       dest_32b_lo=0, src=32, addr_mode=0, instr_mod=2, dst=96
     8c: 494081a0  MOVA2D       dest_32b_lo=0, src=40, addr_mode=0, instr_mod=2, dst=104
     90: 498081c0  MOVA2D       dest_32b_lo=0, src=48, addr_mode=0, instr_mod=2, dst=112
     94: 49c081e0  MOVA2D       dest_32b_lo=0, src=56, addr_mode=0, instr_mod=2, dst=120
     98: df00003c  SETRWC       clear_ab_vld=3, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
     9c: 88040042  STALLWAIT    stall_res=2, wait_res=16  # stall_res: Stall.SYNC; wait_res: Wait.MATH
     a0: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
     a4: 2800000a  SFPENCC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=2  # lreg_c: L0; lreg_dest: L0
     a8: c4080001  SFPLOADI     lreg_ind=0, instr_mod0=2, imm16=0  # lreg_ind: L0
     ac: c5080001  SFPLOADI     lreg_ind=4, instr_mod0=2, imm16=0  # lreg_ind: L4
     b0: c4e20001  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=32768  # lreg_ind: L3
     b4: c4e80001  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=0  # lreg_ind: L3
     b8: 440033c6  SFPCONFIG    imm16_math=12, config_dest=15, instr_mod1=1
     bc: c04c0001  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=0  # lreg_ind: L1
     c0: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
     c4: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
     c8: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
     cc: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
     d0: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
     d4: 3c000002  SFPNOP       
     d8: c04c0009  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=2  # lreg_ind: L1
     dc: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
     e0: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
     e4: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
     e8: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
     ec: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
     f0: 3c000002  SFPNOP       
     f4: c04c0041  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=16  # lreg_ind: L1
     f8: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
     fc: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    100: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    104: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    108: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    10c: 3c000002  SFPNOP       
    110: c04c0049  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=18  # lreg_ind: L1
    114: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    118: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    11c: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    120: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    124: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    128: 3c000002  SFPNOP       
    12c: c04c0011  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=4  # lreg_ind: L1
    130: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    134: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    138: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    13c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    140: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    144: 3c000002  SFPNOP       
    148: c04c0019  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=6  # lreg_ind: L1
    14c: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    150: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    154: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    158: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    15c: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    160: 3c000002  SFPNOP       
    164: c04c0051  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=20  # lreg_ind: L1
    168: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    16c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    170: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    174: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    178: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    17c: 3c000002  SFPNOP       
    180: c04c0059  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=22  # lreg_ind: L1
    184: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    188: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    18c: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    190: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    194: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    198: 3c000002  SFPNOP       
    19c: c04c0021  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=8  # lreg_ind: L1
    1a0: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    1a4: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    1a8: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    1ac: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    1b0: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    1b4: 3c000002  SFPNOP       
    1b8: c04c0029  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=10  # lreg_ind: L1
    1bc: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    1c0: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    1c4: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    1c8: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    1cc: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    1d0: 3c000002  SFPNOP       
    1d4: c04c0061  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=24  # lreg_ind: L1
    1d8: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    1dc: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    1e0: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    1e4: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    1e8: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    1ec: 3c000002  SFPNOP       
    1f0: c04c0069  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=26  # lreg_ind: L1
    1f4: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    1f8: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    1fc: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    200: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    204: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    208: 3c000002  SFPNOP       
    20c: c04c0031  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=12  # lreg_ind: L1
    210: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    214: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    218: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    21c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    220: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    224: 3c000002  SFPNOP       
    228: c04c0039  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=14  # lreg_ind: L1
    22c: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    230: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    234: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    238: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    23c: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    240: 3c000002  SFPNOP       
    244: c04c0071  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=28  # lreg_ind: L1
    248: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    24c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    250: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    254: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    258: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    25c: 3c000002  SFPNOP       
    260: c04c0079  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=30  # lreg_ind: L1
    264: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    268: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    26c: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    270: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    274: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    278: 3c000002  SFPNOP       
    27c: c04c0081  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=32  # lreg_ind: L1
    280: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    284: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    288: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    28c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    290: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    294: 3c000002  SFPNOP       
    298: c04c0089  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=34  # lreg_ind: L1
    29c: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    2a0: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    2a4: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    2a8: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    2ac: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    2b0: 3c000002  SFPNOP       
    2b4: c04c00c1  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=48  # lreg_ind: L1
    2b8: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    2bc: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    2c0: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    2c4: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    2c8: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    2cc: 3c000002  SFPNOP       
    2d0: c04c00c9  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=50  # lreg_ind: L1
    2d4: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    2d8: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    2dc: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    2e0: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    2e4: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    2e8: 3c000002  SFPNOP       
    2ec: c04c0091  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=36  # lreg_ind: L1
    2f0: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    2f4: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    2f8: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    2fc: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    300: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    304: 3c000002  SFPNOP       
    308: c04c0099  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=38  # lreg_ind: L1
    30c: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    310: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    314: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    318: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    31c: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    320: 3c000002  SFPNOP       
    324: c04c00d1  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=52  # lreg_ind: L1
    328: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    32c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    330: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    334: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    338: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    33c: 3c000002  SFPNOP       
    340: c04c00d9  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=54  # lreg_ind: L1
    344: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    348: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    34c: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    350: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    354: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    358: 3c000002  SFPNOP       
    35c: c04c00a1  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=40  # lreg_ind: L1
    360: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    364: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    368: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    36c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    370: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    374: 3c000002  SFPNOP       
    378: c04c00a9  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=42  # lreg_ind: L1
    37c: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    380: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    384: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    388: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    38c: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    390: 3c000002  SFPNOP       
    394: c04c00e1  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=56  # lreg_ind: L1
    398: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    39c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    3a0: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    3a4: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    3a8: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    3ac: 3c000002  SFPNOP       
    3b0: c04c00e9  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=58  # lreg_ind: L1
    3b4: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    3b8: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    3bc: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    3c0: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    3c4: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    3c8: 3c000002  SFPNOP       
    3cc: c04c00b1  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=44  # lreg_ind: L1
    3d0: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    3d4: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    3d8: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    3dc: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    3e0: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    3e4: 3c000002  SFPNOP       
    3e8: c04c00b9  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=46  # lreg_ind: L1
    3ec: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    3f0: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    3f4: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    3f8: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    3fc: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    400: 3c000002  SFPNOP       
    404: c04c00f1  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=60  # lreg_ind: L1
    408: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    40c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    410: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    414: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    418: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    41c: 3c000002  SFPNOP       
    420: c04c00f9  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=62  # lreg_ind: L1
    424: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    428: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    42c: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    430: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    434: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    438: 3c000002  SFPNOP       
    43c: c04c0101  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=64  # lreg_ind: L1
    440: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    444: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    448: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    44c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    450: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    454: 3c000002  SFPNOP       
    458: c04c0109  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=66  # lreg_ind: L1
    45c: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    460: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    464: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    468: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    46c: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    470: 3c000002  SFPNOP       
    474: c04c0141  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=80  # lreg_ind: L1
    478: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    47c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    480: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    484: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    488: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    48c: 3c000002  SFPNOP       
    490: c04c0149  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=82  # lreg_ind: L1
    494: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    498: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    49c: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    4a0: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    4a4: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    4a8: 3c000002  SFPNOP       
    4ac: c04c0111  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=68  # lreg_ind: L1
    4b0: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    4b4: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    4b8: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    4bc: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    4c0: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    4c4: 3c000002  SFPNOP       
    4c8: c04c0119  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=70  # lreg_ind: L1
    4cc: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    4d0: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    4d4: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    4d8: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    4dc: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    4e0: 3c000002  SFPNOP       
    4e4: c04c0151  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=84  # lreg_ind: L1
    4e8: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    4ec: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    4f0: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    4f4: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    4f8: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    4fc: 3c000002  SFPNOP       
    500: c04c0159  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=86  # lreg_ind: L1
    504: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    508: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    50c: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    510: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    514: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    518: 3c000002  SFPNOP       
    51c: c04c0121  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=72  # lreg_ind: L1
    520: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    524: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    528: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    52c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    530: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    534: 3c000002  SFPNOP       
    538: c04c0129  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=74  # lreg_ind: L1
    53c: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    540: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    544: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    548: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    54c: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    550: 3c000002  SFPNOP       
    554: c04c0161  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=88  # lreg_ind: L1
    558: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    55c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    560: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    564: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    568: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    56c: 3c000002  SFPNOP       
    570: c04c0169  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=90  # lreg_ind: L1
    574: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    578: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    57c: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    580: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    584: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    588: 3c000002  SFPNOP       
    58c: c04c0131  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=76  # lreg_ind: L1
    590: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    594: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    598: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    59c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    5a0: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    5a4: 3c000002  SFPNOP       
    5a8: c04c0139  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=78  # lreg_ind: L1
    5ac: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    5b0: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    5b4: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    5b8: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    5bc: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    5c0: 3c000002  SFPNOP       
    5c4: c04c0171  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=92  # lreg_ind: L1
    5c8: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    5cc: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    5d0: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    5d4: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    5d8: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    5dc: 3c000002  SFPNOP       
    5e0: c04c0179  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=94  # lreg_ind: L1
    5e4: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    5e8: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    5ec: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    5f0: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    5f4: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    5f8: 3c000002  SFPNOP       
    5fc: c04c0181  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=96  # lreg_ind: L1
    600: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    604: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    608: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    60c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    610: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    614: 3c000002  SFPNOP       
    618: c04c0189  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=98  # lreg_ind: L1
    61c: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    620: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    624: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    628: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    62c: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    630: 3c000002  SFPNOP       
    634: c04c01c1  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=112  # lreg_ind: L1
    638: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    63c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    640: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    644: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    648: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    64c: 3c000002  SFPNOP       
    650: c04c01c9  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=114  # lreg_ind: L1
    654: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    658: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    65c: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    660: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    664: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    668: 3c000002  SFPNOP       
    66c: c04c0191  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=100  # lreg_ind: L1
    670: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    674: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    678: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    67c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    680: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    684: 3c000002  SFPNOP       
    688: c04c0199  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=102  # lreg_ind: L1
    68c: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    690: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    694: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    698: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    69c: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    6a0: 3c000002  SFPNOP       
    6a4: c04c01d1  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=116  # lreg_ind: L1
    6a8: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    6ac: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    6b0: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    6b4: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    6b8: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    6bc: 3c000002  SFPNOP       
    6c0: c04c01d9  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=118  # lreg_ind: L1
    6c4: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    6c8: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    6cc: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    6d0: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    6d4: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    6d8: 3c000002  SFPNOP       
    6dc: c04c01a1  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=104  # lreg_ind: L1
    6e0: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    6e4: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    6e8: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    6ec: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    6f0: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    6f4: 3c000002  SFPNOP       
    6f8: c04c01a9  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=106  # lreg_ind: L1
    6fc: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    700: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    704: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    708: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    70c: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    710: 3c000002  SFPNOP       
    714: c04c01e1  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=120  # lreg_ind: L1
    718: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    71c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    720: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    724: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    728: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    72c: 3c000002  SFPNOP       
    730: c04c01e9  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=122  # lreg_ind: L1
    734: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    738: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    73c: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    740: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    744: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    748: 3c000002  SFPNOP       
    74c: c04c01b1  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=108  # lreg_ind: L1
    750: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    754: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    758: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    75c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    760: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    764: 3c000002  SFPNOP       
    768: c04c01b9  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=110  # lreg_ind: L1
    76c: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    770: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    774: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    778: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    77c: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    780: 3c000002  SFPNOP       
    784: c04c01f1  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=124  # lreg_ind: L1
    788: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    78c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    790: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    794: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    798: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    79c: 3c000002  SFPNOP       
    7a0: c04c01f9  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=126  # lreg_ind: L1
    7a4: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    7a8: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    7ac: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    7b0: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    7b4: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    7b8: 3c000002  SFPNOP       
    7bc: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    7c0: c8100001  SFPSTORE     lreg_ind=0, instr_mod0=4, sfpu_addr_mode=0, dest_reg_addr=0  # lreg_ind: L0
    7c4: c9100009  SFPSTORE     lreg_ind=4, instr_mod0=4, sfpu_addr_mode=0, dest_reg_addr=2  # lreg_ind: L4
    7c8: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    7cc: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    7d0:           j FW_TRISC1+4   # return to firmware, linked at install
