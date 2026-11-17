# llama3 8b-fp8 decode: argmax, trisc1. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (96): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5 7,6 7,7 7,8 7,9 7,10 7,11 10,2 10,3 10,4 10,5 10,6 10,7 10,8 10,9 10,10 10,11 11,2 11,3 11,4 11,5 11,6 11,7 11,8 11,9 11,10 11,11 12,2 12,3 12,4 12,5 12,6 12,7
# params: 0x780=e2e_token_history, 0x784=argmax_host_address, 0x788=argmax_count, 0x78c=write_pos, 0x790=write_token, 0x11a00=e2e_logits, 0x11a04=argmax_start, 0x11a08=argmax_core
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

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
     d4: c04c0009  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=2  # lreg_ind: L1
     d8: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
     dc: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
     e0: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
     e4: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
     e8: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
     ec: c04c0041  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=16  # lreg_ind: L1
     f0: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
     f4: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
     f8: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
     fc: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    100: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    104: c04c0049  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=18  # lreg_ind: L1
    108: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    10c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    110: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    114: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    118: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    11c: c04c0011  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=4  # lreg_ind: L1
    120: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    124: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    128: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    12c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    130: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    134: c04c0019  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=6  # lreg_ind: L1
    138: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    13c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    140: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    144: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    148: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    14c: c04c0051  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=20  # lreg_ind: L1
    150: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    154: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    158: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    15c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    160: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    164: c04c0059  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=22  # lreg_ind: L1
    168: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    16c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    170: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    174: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    178: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    17c: c04c0021  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=8  # lreg_ind: L1
    180: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    184: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    188: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    18c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    190: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    194: c04c0029  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=10  # lreg_ind: L1
    198: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    19c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    1a0: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    1a4: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    1a8: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    1ac: c04c0061  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=24  # lreg_ind: L1
    1b0: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    1b4: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    1b8: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    1bc: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    1c0: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    1c4: c04c0069  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=26  # lreg_ind: L1
    1c8: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    1cc: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    1d0: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    1d4: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    1d8: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    1dc: c04c0031  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=12  # lreg_ind: L1
    1e0: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    1e4: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    1e8: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    1ec: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    1f0: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    1f4: c04c0039  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=14  # lreg_ind: L1
    1f8: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    1fc: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    200: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    204: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    208: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    20c: c04c0071  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=28  # lreg_ind: L1
    210: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    214: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    218: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    21c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    220: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    224: c04c0079  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=30  # lreg_ind: L1
    228: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    22c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    230: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    234: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    238: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    23c: c04c0081  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=32  # lreg_ind: L1
    240: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    244: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    248: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    24c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    250: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    254: c04c0089  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=34  # lreg_ind: L1
    258: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    25c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    260: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    264: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    268: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    26c: c04c00c1  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=48  # lreg_ind: L1
    270: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    274: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    278: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    27c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    280: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    284: c04c00c9  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=50  # lreg_ind: L1
    288: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    28c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    290: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    294: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    298: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    29c: c04c0091  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=36  # lreg_ind: L1
    2a0: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    2a4: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    2a8: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    2ac: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    2b0: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    2b4: c04c0099  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=38  # lreg_ind: L1
    2b8: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    2bc: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    2c0: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    2c4: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    2c8: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    2cc: c04c00d1  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=52  # lreg_ind: L1
    2d0: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    2d4: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    2d8: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    2dc: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    2e0: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    2e4: c04c00d9  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=54  # lreg_ind: L1
    2e8: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    2ec: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    2f0: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    2f4: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    2f8: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    2fc: c04c00a1  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=40  # lreg_ind: L1
    300: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    304: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    308: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    30c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    310: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    314: c04c00a9  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=42  # lreg_ind: L1
    318: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    31c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    320: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    324: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    328: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    32c: c04c00e1  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=56  # lreg_ind: L1
    330: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    334: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    338: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    33c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    340: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    344: c04c00e9  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=58  # lreg_ind: L1
    348: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    34c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    350: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    354: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    358: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    35c: c04c00b1  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=44  # lreg_ind: L1
    360: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    364: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    368: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    36c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    370: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    374: c04c00b9  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=46  # lreg_ind: L1
    378: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    37c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    380: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    384: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    388: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    38c: c04c00f1  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=60  # lreg_ind: L1
    390: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    394: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    398: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    39c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    3a0: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    3a4: c04c00f9  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=62  # lreg_ind: L1
    3a8: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    3ac: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    3b0: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    3b4: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    3b8: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    3bc: c04c0101  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=64  # lreg_ind: L1
    3c0: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    3c4: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    3c8: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    3cc: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    3d0: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    3d4: c04c0109  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=66  # lreg_ind: L1
    3d8: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    3dc: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    3e0: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    3e4: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    3e8: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    3ec: c04c0141  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=80  # lreg_ind: L1
    3f0: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    3f4: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    3f8: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    3fc: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    400: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    404: c04c0149  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=82  # lreg_ind: L1
    408: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    40c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    410: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    414: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    418: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    41c: c04c0111  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=68  # lreg_ind: L1
    420: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    424: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    428: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    42c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    430: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    434: c04c0119  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=70  # lreg_ind: L1
    438: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    43c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    440: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    444: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    448: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    44c: c04c0151  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=84  # lreg_ind: L1
    450: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    454: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    458: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    45c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    460: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    464: c04c0159  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=86  # lreg_ind: L1
    468: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    46c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    470: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    474: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    478: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    47c: c04c0121  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=72  # lreg_ind: L1
    480: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    484: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    488: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    48c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    490: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    494: c04c0129  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=74  # lreg_ind: L1
    498: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    49c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    4a0: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    4a4: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    4a8: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    4ac: c04c0161  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=88  # lreg_ind: L1
    4b0: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    4b4: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    4b8: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    4bc: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    4c0: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    4c4: c04c0169  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=90  # lreg_ind: L1
    4c8: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    4cc: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    4d0: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    4d4: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    4d8: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    4dc: c04c0131  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=76  # lreg_ind: L1
    4e0: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    4e4: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    4e8: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    4ec: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    4f0: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    4f4: c04c0139  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=78  # lreg_ind: L1
    4f8: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    4fc: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    500: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    504: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    508: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    50c: c04c0171  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=92  # lreg_ind: L1
    510: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    514: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    518: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    51c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    520: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    524: c04c0179  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=94  # lreg_ind: L1
    528: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    52c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    530: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    534: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    538: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    53c: c04c0181  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=96  # lreg_ind: L1
    540: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    544: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    548: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    54c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    550: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    554: c04c0189  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=98  # lreg_ind: L1
    558: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    55c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    560: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    564: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    568: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    56c: c04c01c1  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=112  # lreg_ind: L1
    570: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    574: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    578: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    57c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    580: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    584: c04c01c9  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=114  # lreg_ind: L1
    588: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    58c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    590: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    594: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    598: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    59c: c04c0191  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=100  # lreg_ind: L1
    5a0: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    5a4: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    5a8: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    5ac: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    5b0: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    5b4: c04c0199  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=102  # lreg_ind: L1
    5b8: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    5bc: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    5c0: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    5c4: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    5c8: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    5cc: c04c01d1  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=116  # lreg_ind: L1
    5d0: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    5d4: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    5d8: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    5dc: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    5e0: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    5e4: c04c01d9  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=118  # lreg_ind: L1
    5e8: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    5ec: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    5f0: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    5f4: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    5f8: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    5fc: c04c01a1  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=104  # lreg_ind: L1
    600: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    604: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    608: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    60c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    610: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    614: c04c01a9  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=106  # lreg_ind: L1
    618: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    61c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    620: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    624: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    628: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    62c: c04c01e1  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=120  # lreg_ind: L1
    630: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    634: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    638: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    63c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    640: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    644: c04c01e9  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=122  # lreg_ind: L1
    648: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    64c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    650: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    654: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    658: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    65c: c04c01b1  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=108  # lreg_ind: L1
    660: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    664: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    668: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    66c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    670: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    674: c04c01b9  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=110  # lreg_ind: L1
    678: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    67c: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    680: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    684: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    688: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    68c: c04c01f1  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=124  # lreg_ind: L1
    690: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    694: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    698: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    69c: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    6a0: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    6a4: c04c01f9  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=126  # lreg_ind: L1
    6a8: ebf8449d  SFPSHFT      imm12_math=4065, lreg_c=1, lreg_dest=2, instr_mod1=7  # lreg_c: L1; lreg_dest: L2
    6ac: fc000c81  SFPOR        imm12_math=0, lreg_c=3, lreg_dest=2, instr_mod1=0  # lreg_c: L3; lreg_dest: L2
    6b0: 34000842  SFPXOR       imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=0  # lreg_c: L2; lreg_dest: L1
    6b4: ebffc445  SFPSHFT      imm12_math=4095, lreg_c=1, lreg_dest=1, instr_mod1=1  # lreg_c: L1; lreg_dest: L1
    6b8: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    6bc: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    6c0: c8100001  SFPSTORE     lreg_ind=0, instr_mod0=4, sfpu_addr_mode=0, dest_reg_addr=0  # lreg_ind: L0
    6c4: c9100009  SFPSTORE     lreg_ind=4, instr_mod0=4, sfpu_addr_mode=0, dest_reg_addr=2  # lreg_ind: L4
    6c8: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    6cc: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    6d0:           j FW_TRISC1+4   # return to firmware, linked at install
