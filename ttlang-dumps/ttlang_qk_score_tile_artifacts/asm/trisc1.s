    lui	a5,0xffb00
    lui	a4,0xffb00
    addi	a5,a5,56 # ffb00038 <__stack_base+0x8>
    addi	a4,a4,44 # ffb0002c <__ldm_bss_end>
    bltu	a4,a5,725c <.L2>
    sw	zero,-4(a5)
    sw	zero,-8(a5)
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a5,a5,16
    bgeu	a4,a5,7244 <.L3>
    addi	a3,a5,-8
    bltu	a4,a3,7bc4 <.L31>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,7278 <.L5>
    sw	zero,-8(a5)
    auipc	a4,0x1
    addi	a4,a4,-1708 # 7bcc <__kernel_data_lma>
    addi	a5,gp,-2000 # ffb00020 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    beq	a4,a5,72e8 <.L7>
    lui	a2,0xffb00
    addi	a2,a2,40 # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    sub	a2,a2,a5
    li	a1,8
    srai	a3,a2,0x2
    bge	a1,a2,72cc <.L8>
    li	a6,2
    lw	a0,0(a4)
    lw	a1,4(a4)
    lw	a2,8(a4)
    addi	a4,a4,12
    addi	a5,a5,12
    addi	a3,a3,-3
    sw	a0,-12(a5)
    sw	a1,-8(a5)
    sw	a2,-4(a5)
    blt	a6,a3,72a4 <.L9>
    blez	a3,72e8 <.L7>
    lw	a1,0(a4)
    li	a2,2
    sw	a1,0(a5)
    bne	a3,a2,72e8 <.L7>
    lw	a4,4(a4)
    sw	a4,4(a5)
    lw	a4,1312(zero) # 520 <.LASF10>
    li	a3,128
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    addi	a4,a4,96
    beq	a5,a3,730c <.L13>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,7300 <.L11>
    ttsetc16	13,0
    ttsetc16	29,0
    ttsetc16	48,0
    ttzeroacc	3,0,0,1,0
    lui	a4,0xffe80
    li	a5,0
    addi	a3,a4,4 # ffe80004 <__instrn_buffer+0x40004>
    sw	a5,0(a3)
    lw	a5,0(a3)
    and	zero,zero,a5
    lw	a5,36(a4)
    zext.b	a5,a5
    bnez	a5,7334 <.L12>
    ttseminit	2,0,2
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttsetc16	1,0
    lui	a5,0xffe40
    lui	a4,0xb3080
    mv	a5,a5
    addi	a4,a4,220 # b30800dc <__device_print_strings_info_end+0xacb800dc>
    sw	a4,0(a5) # ffe40000 <__instrn_buffer>
    ttstallwait	128,16
    lui	a4,0xb6800
    addi	a4,a4,1 # b6800001 <__device_print_strings_info_end+0xb0300001>
    sw	a4,0(a5)
    lui	a4,0xb6200
    addi	a4,a4,1 # b6200001 <__device_print_strings_info_end+0xafd00001>
    sw	a4,0(a5)
    lui	a4,0xb6400
    addi	a4,a4,1 # b6400001 <__device_print_strings_info_end+0xaff00001>
    sw	a4,0(a5)
    lbu	a2,-1992(gp) # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    li	a4,1
    beq	a2,a4,7bac <.L51>
    li	a4,5
    li	a2,1
    sw	a4,-1996(gp) # ffb00024 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    sw	a4,-2000(gp) # ffb00020 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    sb	a2,-1992(gp) # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	128,2064
    lui	a4,0xb3010
    addi	a4,a4,2 # b3010002 <__device_print_strings_info_end+0xacb10002>
    sw	a4,0(a5)
    ttsemwait	322,2,2
    ttsetc16	12,2056
    ttsetc16	28,8
    ttsetc16	47,0
    ttsetc16	13,0
    ttsetc16	29,0
    ttsetc16	48,0
    ttsetc16	14,32896
    ttsetc16	30,9216
    ttsetc16	49,0
    ttsetc16	15,32896
    ttsetc16	31,36872
    ttsetc16	50,0
    lui	a2,0xffe80
    li	a4,0
    addi	a2,a2,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a4,0(a2)
    lw	a4,0(a2)
    and	zero,zero,a4
    lui	a2,0xffb80
    li	a4,4
    sw	a4,0(a2) # ffb80000 <__global_pointer$+0x7f810>
    li	a7,2
    sw	a7,4(a2)
    lui	a7,0x2000
    sw	a7,8(a2)
    sw	a7,12(a2)
    sw	a7,16(a2)
    lui	t1,0x27000
    sw	t1,20(a2)
    sw	a7,24(a2)
    lui	a7,0x27c0c
    sw	a7,28(a2)
    lui	a7,0x27008
    sw	a7,32(a2)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    lw	a2,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	t1,0xb2010
    snez	a7,a2
    slli	a7,a7,0x9
    add	t1,a7,t1
    sw	t1,0(a5)
    ttmop	1,0,0
    addi	a4,a4,-1
    bnez	a4,7464 <.L16>
    ttsetrwc	0,0,0,0,0,4
    lui	a4,0xb2010
    addi	a4,a4,64 # b2010040 <__device_print_strings_info_end+0xabb10040>
    add	a7,a7,a4
    sw	a7,0(a5)
    li	a4,4
    ttmop	1,0,0
    addi	a4,a4,-1
    bnez	a4,7488 <.L17>
    ttsetrwc	0,0,0,0,0,4
    ttstallwait	2,2064
    ttsempost	2
    li	a7,1
    sub	a7,a7,a2
    sw	a7,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttstallwait	128,2064
    addi	a2,a2,-1
    snez	a2,a2
    lui	a7,0xb2010
    slli	a2,a2,0x9
    add	a2,a2,a7
    sw	a2,0(a5)
    ttsetc16	15,0
    ttsetc16	31,0
    ttsetc16	50,0
    ttsetc16	12,1
    ttsetc16	28,1
    ttsetc16	47,0
    ttsetc16	14,8
    ttsetc16	30,8
    ttsetc16	49,0
    lui	a2,0xffe80
    mv	a7,a4
    addi	t1,a2,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a7,0(t1) # b2010000 <__device_print_strings_info_end+0xabb10000>
    lw	a7,0(t1)
    and	zero,zero,a7
    lui	a7,0xffb80
    li	t1,4
    sw	t1,0(a7) # ffb80000 <__global_pointer$+0x7f810>
    li	t1,2
    sw	t1,4(a7)
    lui	t3,0x2000
    lui	t1,0x37c00
    sw	t3,8(a7)
    addi	t1,t1,3 # 37c00003 <__device_print_strings_info_end+0x31700003>
    sw	t1,12(a7)
    sw	t3,16(a7)
    lui	t1,0x1200a
    sw	t1,20(a7)
    sw	t3,24(a7)
    sw	t1,28(a7)
    sw	t1,32(a7)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    addi	a7,a2,4
    sw	a4,0(a7)
    lw	a4,0(a7)
    and	zero,zero,a4
    lw	a4,36(a2)
    zext.b	a4,a4
    bnez	a4,755c <.L18>
    ttseminit	2,0,2
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttsetc16	1,0
    lui	a4,0xb3080
    addi	a4,a4,220 # b30800dc <__device_print_strings_info_end+0xacb800dc>
    sw	a4,0(a5)
    ttstallwait	128,16
    lui	a4,0xb6800
    addi	a4,a4,1 # b6800001 <__device_print_strings_info_end+0xb0300001>
    sw	a4,0(a5)
    lui	a4,0xb6200
    addi	a4,a4,1 # b6200001 <__device_print_strings_info_end+0xafd00001>
    sw	a4,0(a5)
    lui	a4,0xb6400
    addi	a4,a4,1 # b6400001 <__device_print_strings_info_end+0xaff00001>
    sw	a4,0(a5)
    lbu	a2,-1992(gp) # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    li	a4,1
    beq	a2,a4,7b94 <.L52>
    li	a4,5
    sw	a4,-1996(gp) # ffb00024 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    sw	a4,-2000(gp) # ffb00020 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    ttstallwait	128,2064
    lui	a4,0xb3010
    addi	a4,a4,2 # b3010002 <__device_print_strings_info_end+0xacb10002>
    sw	a4,0(a5)
    li	a4,2
    sb	a4,-1992(gp) # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	128,2064
    lui	a4,0xb3010
    addi	a4,a4,258 # b3010102 <__device_print_strings_info_end+0xacb10102>
    sw	a4,0(a5)
    ttsemwait	322,2,2
    sfpconfig	15,0,1
    ttsetc16	19,0
    ttsetc16	35,0
    ttsetc16	54,0
    ttsetrwc	0,0,0,0,0,15
    lui	a4,0xb2010
    sw	a4,0(a5)
    ttstallwait	256,16
    li	a4,4
    ttreplay	0,4,1,1
    sfpstore	L10,0,0,7
    ttincrwc	0,2,0,0
    sfpstore	L10,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a4,a4,-1 # b200ffff <__device_print_strings_info_end+0xabb0ffff>
    bnez	a4,7610 <.L21>
    ttsetrwc	0,0,0,0,0,4
    ttstallwait	2,2064
    ttsempost	2
    lw	a2,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    li	a7,1
    sub	a7,a7,a2
    sw	a7,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttstallwait	128,2064
    addi	a2,a2,-1
    snez	a2,a2
    lui	a7,0xb2010
    slli	a2,a2,0x9
    add	a2,a2,a7
    sw	a2,0(a5)
    ttsetc16	15,0
    ttsetc16	31,0
    ttsetc16	50,0
    ttsetc16	12,1
    ttsetc16	28,1
    ttsetc16	47,0
    ttsetc16	14,8
    ttsetc16	30,8
    ttsetc16	49,0
    lui	a2,0xffe80
    mv	a7,a4
    addi	t1,a2,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a7,0(t1) # 1200a000 <__device_print_strings_info_end+0xbb0a000>
    lw	a7,0(t1)
    and	zero,zero,a7
    lui	a7,0xffb80
    li	t1,4
    sw	t1,0(a7) # ffb80000 <__global_pointer$+0x7f810>
    li	t1,2
    sw	t1,4(a7)
    lui	t3,0x2000
    lui	t1,0x37c00
    sw	t3,8(a7)
    addi	t1,t1,3 # 37c00003 <__device_print_strings_info_end+0x31700003>
    sw	t1,12(a7)
    sw	t3,16(a7)
    lui	t1,0x1200a
    sw	t1,20(a7)
    sw	t3,24(a7)
    sw	t1,28(a7)
    sw	t1,32(a7)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    addi	a7,a2,4
    sw	a4,0(a7)
    lw	a4,0(a7)
    and	zero,zero,a4
    lw	a4,36(a2)
    zext.b	a4,a4
    bnez	a4,770c <.L22>
    ttseminit	2,0,2
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttsetc16	1,0
    lui	a4,0xb3080
    addi	a4,a4,220 # b30800dc <__device_print_strings_info_end+0xacb800dc>
    sw	a4,0(a5)
    ttstallwait	128,16
    lui	a4,0xb6800
    addi	a4,a4,1 # b6800001 <__device_print_strings_info_end+0xb0300001>
    sw	a4,0(a5)
    lui	a4,0xb6200
    addi	a4,a4,1 # b6200001 <__device_print_strings_info_end+0xafd00001>
    sw	a4,0(a5)
    lui	a4,0xb6400
    addi	a4,a4,1 # b6400001 <__device_print_strings_info_end+0xaff00001>
    sw	a4,0(a5)
    lbu	a2,-1992(gp) # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    li	a4,1
    beq	a2,a4,7b7c <.L53>
    li	a4,5
    sw	a4,-1996(gp) # ffb00024 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    sw	a4,-2000(gp) # ffb00020 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    ttstallwait	128,2064
    lui	a4,0xb3010
    addi	a4,a4,2 # b3010002 <__device_print_strings_info_end+0xacb10002>
    sw	a4,0(a5)
    li	a4,2
    sb	a4,-1992(gp) # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	128,2064
    lui	t3,0xb3010
    addi	t3,t3,258 # b3010102 <__device_print_strings_info_end+0xacb10102>
    sw	t3,0(a5)
    ttsemwait	322,2,2
    ttsetc16	12,0
    ttsetc16	28,32768
    ttsetc16	47,0
    ttsetc16	13,256
    ttsetc16	29,1
    ttsetc16	48,0
    ttsetc16	14,2048
    ttsetc16	30,8
    ttsetc16	49,0
    ttsetc16	15,0
    ttsetc16	31,8192
    ttsetc16	50,0
    lui	a2,0xffe80
    li	a4,0
    addi	a2,a2,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a4,0(a2)
    lw	a4,0(a2)
    and	zero,zero,a4
    lui	a4,0xffb80
    li	a2,1
    sw	a2,0(a4) # ffb80000 <__global_pointer$+0x7f810>
    li	a2,4
    sw	a2,4(a4)
    lui	a2,0x2000
    sw	a2,8(a4)
    sw	a2,12(a4)
    sw	a2,16(a4)
    lui	a7,0x34098
    sw	a7,20(a4)
    sw	a2,24(a4)
    lui	a2,0x34080
    sw	a2,28(a4)
    sw	a2,32(a4)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    lw	a2,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lw	a4,-1996(gp) # ffb00024 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    lw	a7,-2000(gp) # ffb00020 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    snez	t1,a2
    lui	t4,0xb2010
    slli	t1,t1,0x9
    add	t1,t1,t4
    addi	a4,a4,-9
    addi	a7,a7,-9 # 34097ff7 <__device_print_strings_info_end+0x2db97ff7>
    seqz	a7,a7
    sw	t1,0(a5)
    seqz	a4,a4
    lbu	t4,-1992(gp) # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    or	a4,a4,a7
    ttmop	1,0,0
    ttcleardvalid	3,0
    ttmop	1,0,0
    li	a7,3
    beq	t4,a7,787c <.L29>
    ttstallwait	128,2064
    sw	t3,0(a5)
    ttsetrwc	0,4,0,0,0,3
    ttmovd2b	0,16,0,0,0
    tttrnspsrcb
    ttmovd2b	0,16,0,0,0
    ttsetrwc	0,2,0,8,0,2
    ttsetrwc	0,2,0,8,0,2
    ttzerosrc	0,1,0,1
    ttelwadd	0,0,0,2,0
    ttelwadd	0,0,0,2,0
    ttstallwait	128,2064
    lui	a7,0xb3010
    addi	t3,a7,2 # b3010002 <__device_print_strings_info_end+0xacb10002>
    slli	a4,a4,0x8
    add	a4,a4,t3
    sw	a4,0(a5)
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	3,4,8,0,0,6
    ttmop	1,0,0
    ttcleardvalid	3,0
    ttmop	1,0,0
    ttstallwait	128,2064
    addi	a7,a7,258
    sw	a7,0(a5)
    ttsetrwc	0,4,0,0,0,3
    ttmovd2b	0,16,0,0,0
    tttrnspsrcb
    ttmovd2b	0,16,0,0,0
    ttsetrwc	0,2,0,8,0,2
    ttsetrwc	0,2,0,8,0,2
    ttzerosrc	0,1,0,1
    ttelwadd	0,0,0,2,0
    ttelwadd	0,0,0,2,0
    ttstallwait	128,2064
    sw	a4,0(a5)
    ttsetrwc	3,0,0,0,0,6
    sw	t1,0(a5)
    ttmop	1,0,0
    ttcleardvalid	3,0
    ttmop	1,0,0
    ttstallwait	128,2064
    sw	a7,0(a5)
    ttsetrwc	0,4,0,0,0,3
    ttmovd2b	0,16,0,0,0
    tttrnspsrcb
    ttmovd2b	0,16,0,0,0
    ttsetrwc	0,2,0,8,0,2
    ttsetrwc	0,2,0,8,0,2
    ttzerosrc	0,1,0,1
    ttelwadd	0,0,0,2,0
    ttelwadd	0,0,0,2,0
    ttstallwait	128,2064
    sw	a4,0(a5)
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	3,4,8,0,0,6
    ttmop	1,0,0
    ttcleardvalid	3,0
    ttmop	1,0,0
    ttstallwait	128,2064
    sw	a7,0(a5)
    ttsetrwc	0,4,0,0,0,3
    ttmovd2b	0,16,0,0,0
    tttrnspsrcb
    ttmovd2b	0,16,0,0,0
    ttsetrwc	0,2,0,8,0,2
    ttsetrwc	0,2,0,8,0,2
    ttzerosrc	0,1,0,1
    ttelwadd	0,0,0,2,0
    ttelwadd	0,0,0,2,0
    ttstallwait	128,2064
    sw	a4,0(a5)
    ttsetrwc	3,0,0,0,0,6
    li	a4,1
    sb	a4,-1992(gp) # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	2,2064
    ttsempost	2
    sub	a4,a4,a2
    sw	a4,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttstallwait	128,2064
    addi	a4,a2,-1 # 3407ffff <__device_print_strings_info_end+0x2db7ffff>
    snez	a4,a4
    lui	a2,0xb2010
    slli	a4,a4,0x9
    add	a4,a4,a2
    lui	a2,0xffe80
    sw	a4,0(a5)
    addi	a7,a2,4 # ffe80004 <__instrn_buffer+0x40004>
    li	a4,0
    sw	a4,0(a7)
    lw	a4,0(a7)
    and	zero,zero,a4
    lw	a4,36(a2)
    zext.b	a4,a4
    bnez	a4,79f4 <.L25>
    ttseminit	2,0,2
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttsetc16	1,0
    lui	a4,0xb3080
    addi	a4,a4,220 # b30800dc <__device_print_strings_info_end+0xacb800dc>
    sw	a4,0(a5)
    ttstallwait	128,16
    lui	a4,0xb6800
    addi	a4,a4,1 # b6800001 <__device_print_strings_info_end+0xb0300001>
    sw	a4,0(a5)
    lui	a4,0xb6200
    addi	a4,a4,1 # b6200001 <__device_print_strings_info_end+0xafd00001>
    sw	a4,0(a5)
    lui	a4,0xb6400
    addi	a4,a4,1 # b6400001 <__device_print_strings_info_end+0xaff00001>
    sw	a4,0(a5)
    lbu	a2,-1992(gp) # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    li	a4,1
    beq	a2,a4,7b64 <.L54>
    li	a4,5
    li	a2,1
    sw	a4,-1996(gp) # ffb00024 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    sw	a4,-2000(gp) # ffb00020 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    sb	a2,-1992(gp) # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	128,2064
    lui	a4,0xb3010
    addi	a4,a4,2 # b3010002 <__device_print_strings_info_end+0xacb10002>
    sw	a4,0(a5)
    ttsemwait	322,2,2
    ttsetc16	12,2056
    ttsetc16	28,8
    ttsetc16	47,0
    ttsetc16	13,0
    ttsetc16	29,0
    ttsetc16	48,0
    ttsetc16	14,32896
    ttsetc16	30,9216
    ttsetc16	49,0
    ttsetc16	15,32896
    ttsetc16	31,36872
    ttsetc16	50,0
    lui	a2,0xffe80
    li	a4,0
    addi	a2,a2,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a4,0(a2)
    lw	a4,0(a2)
    and	zero,zero,a4
    lui	a2,0xffb80
    li	a4,4
    sw	a4,0(a2) # ffb80000 <__global_pointer$+0x7f810>
    li	a1,2
    sw	a1,4(a2)
    lui	a1,0x2000
    sw	a1,8(a2)
    sw	a1,12(a2)
    sw	a1,16(a2)
    lui	a0,0x27000
    sw	a0,20(a2)
    sw	a1,24(a2)
    lui	a1,0x27c0c
    sw	a1,28(a2)
    lui	a1,0x27008
    sw	a1,32(a2)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    lw	a2,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a0,0xb2010
    snez	a1,a2
    slli	a1,a1,0x9
    add	a1,a1,a0
    sw	a1,0(a5)
    ttmop	1,0,0
    addi	a4,a4,-1
    bnez	a4,7b1c <.L28>
    ttsetrwc	0,0,0,0,0,4
    ttstallwait	2,2064
    ttsempost	2
    li	a4,1
    sub	a4,a4,a2
    sw	a4,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttstallwait	128,2064
    addi	a4,a2,-1
    snez	a4,a4
    lui	a3,0xb2010
    slli	a4,a4,0x9
    add	a4,a4,a3
    sw	a4,0(a5)
    li	a0,0
    ret
    lw	a4,-1996(gp) # ffb00024 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a2,5
    bne	a4,a2,7a4c <.L26>
    lw	a2,-2000(gp) # ffb00020 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    bne	a2,a4,7a4c <.L26>
    j	7a70 <.L27>
    lw	a4,-1996(gp) # ffb00024 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a2,5
    bne	a4,a2,7764 <.L23>
    lw	a2,-2000(gp) # ffb00020 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    bne	a2,a4,7764 <.L23>
    j	7780 <.L24>
    lw	a4,-1996(gp) # ffb00024 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a2,5
    bne	a4,a2,75b4 <.L19>
    lw	a2,-2000(gp) # ffb00020 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    bne	a2,a4,75b4 <.L19>
    j	75d0 <.L20>
    lw	a4,-1996(gp) # ffb00024 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a2,5
    bne	a4,a2,7394 <.L14>
    lw	a2,-2000(gp) # ffb00020 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    bne	a2,a4,7394 <.L14>
    j	73b8 <.L15>
    mv	a5,a3
    j	726c <.L4>
