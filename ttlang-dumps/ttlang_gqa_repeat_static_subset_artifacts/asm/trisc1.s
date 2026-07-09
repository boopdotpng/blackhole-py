    addi	sp,sp,-16
    sw	s0,12(sp)
    sw	s1,8(sp)
    lui	a5,0xffb00
    lui	a4,0xffb00
    addi	a5,a5,56 # ffb00038 <__stack_base+0x8>
    addi	a4,a4,44 # ffb0002c <__ldm_bss_end>
    bltu	a4,a5,7268 <.L2>
    sw	zero,-4(a5)
    sw	zero,-8(a5)
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a5,a5,16
    bgeu	a4,a5,7250 <.L3>
    addi	a3,a5,-8
    bltu	a4,a3,7738 <.L20>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,7284 <.L5>
    sw	zero,-8(a5)
    auipc	a4,0x0
    addi	a4,a4,1212 # 7740 <__kernel_data_lma>
    addi	a5,gp,-2000 # ffb00020 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    beq	a4,a5,72f4 <.L7>
    lui	a2,0xffb00
    addi	a2,a2,40 # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    sub	a2,a2,a5
    li	a1,8
    srai	a3,a2,0x2
    bge	a1,a2,72d8 <.L8>
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
    blt	a6,a3,72b0 <.L9>
    blez	a3,72f4 <.L7>
    lw	a1,0(a4)
    li	a2,2
    sw	a1,0(a5)
    bne	a3,a2,72f4 <.L7>
    lw	a4,4(a4)
    sw	a4,4(a5)
    lw	a4,1312(zero) # 520 <.LLST112+0x4>
    li	a3,128
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    addi	a4,a4,96
    beq	a5,a3,7318 <.L11>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,730c <.L12>
    ttsetc16	13,0
    ttsetc16	29,0
    ttsetc16	48,0
    ttzeroacc	3,0,0,1,0
    ttsetc16	15,0
    ttsetc16	31,0
    ttsetc16	50,0
    ttsetc16	12,1
    ttsetc16	28,1
    ttsetc16	47,0
    ttsetc16	14,8
    ttsetc16	30,8
    ttsetc16	49,0
    lui	a4,0xffe80
    addi	a2,a4,8 # ffe80008 <__instrn_buffer+0x40008>
    li	a5,0
    sw	a5,0(a2)
    lw	a5,0(a2)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a2,4
    sw	a2,0(a5) # ffb80000 <__global_pointer$+0x7f810>
    li	a2,2
    sw	a2,4(a5)
    lui	a1,0x2000
    lui	a2,0x37c00
    sw	a1,8(a5)
    addi	a2,a2,3 # 37c00003 <__device_print_strings_info_end+0x31700003>
    sw	a2,12(a5)
    sw	a1,16(a5)
    lui	a2,0x1200a
    sw	a2,20(a5)
    sw	a1,24(a5)
    sw	a2,28(a5)
    sw	a2,32(a5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    li	a5,0
    addi	a3,a4,4
    sw	a5,0(a3)
    lw	a5,0(a3)
    and	zero,zero,a5
    lw	a5,36(a4)
    zext.b	a5,a5
    bnez	a5,73c0 <.L13>
    ttseminit	2,0,2
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttsetc16	1,0
    lui	a4,0xffe40
    lui	a5,0xb3080
    mv	a4,a4
    addi	a5,a5,220 # b30800dc <__device_print_strings_info_end+0xacb800dc>
    sw	a5,0(a4) # ffe40000 <__instrn_buffer>
    ttstallwait	128,16
    lui	a5,0xb6800
    addi	a5,a5,1 # b6800001 <__device_print_strings_info_end+0xb0300001>
    sw	a5,0(a4)
    lui	a5,0xb6200
    addi	a5,a5,1 # b6200001 <__device_print_strings_info_end+0xafd00001>
    sw	a5,0(a4)
    lui	a5,0xb6400
    addi	a5,a5,1 # b6400001 <__device_print_strings_info_end+0xaff00001>
    sw	a5,0(a4)
    lbu	a3,-1992(gp) # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    li	a5,1
    beq	a3,a5,7720 <.L33>
    li	a5,5
    sw	a5,-1996(gp) # ffb00024 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    sw	a5,-2000(gp) # ffb00020 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    ttstallwait	128,2064
    lui	a5,0xb3010
    addi	a5,a5,2 # b3010002 <__device_print_strings_info_end+0xacb10002>
    sw	a5,0(a4)
    li	t5,2
    sb	t5,-1992(gp) # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	128,2064
    lui	a5,0xb3010
    addi	a5,a5,258 # b3010102 <__device_print_strings_info_end+0xacb10102>
    sw	a5,0(a4)
    ttsemwait	322,2,2
    ttsetc16	15,0
    ttsetc16	31,0
    ttsetc16	50,0
    ttsetc16	12,1
    ttsetc16	28,1
    ttsetc16	47,0
    ttsetc16	14,8
    ttsetc16	30,8
    ttsetc16	49,0
    lui	a3,0xffe80
    li	a1,0
    addi	s0,a3,8 # ffe80008 <__instrn_buffer+0x40008>
    mv	a5,a1
    sw	a5,0(s0)
    lw	a5,0(s0)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	t2,4
    sw	t2,0(a5) # ffb80000 <__global_pointer$+0x7f810>
    sw	t5,4(a5)
    lui	a6,0x2000
    lui	t3,0x37c00
    sw	a6,8(a5)
    addi	t3,t3,3 # 37c00003 <__device_print_strings_info_end+0x31700003>
    sw	t3,12(a5)
    sw	a6,16(a5)
    lui	a0,0x1200a
    sw	a0,20(a5)
    sw	a6,24(a5)
    sw	a0,28(a5)
    sw	a0,32(a5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    lw	a2,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	s1,0xb2010
    snez	t1,a2
    slli	t1,t1,0x9
    add	t1,t1,s1
    sw	t1,0(a4)
    ttmop	1,0,0
    ttsetrwc	0,0,0,0,0,4
    ttstallwait	2,2064
    ttsempost	2
    li	t1,1
    sub	t1,t1,a2
    sw	t1,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttstallwait	128,2064
    addi	a2,a2,-1 # 12009fff <__device_print_strings_info_end+0xbb09fff>
    snez	a2,a2
    slli	a2,a2,0x9
    add	a2,a2,s1
    sw	a2,0(a4)
    ttsetc16	15,0
    ttsetc16	31,0
    ttsetc16	50,0
    ttsetc16	12,1
    ttsetc16	28,1
    ttsetc16	47,0
    ttsetc16	14,8
    ttsetc16	30,8
    ttsetc16	49,0
    mv	a2,a1
    sw	a2,0(s0)
    lw	a2,0(s0)
    and	zero,zero,a2
    sw	t2,0(a5)
    sw	t5,4(a5)
    sw	a6,8(a5)
    sw	t3,12(a5)
    sw	a6,16(a5)
    sw	a0,20(a5)
    sw	a6,24(a5)
    sw	a0,28(a5)
    sw	a0,32(a5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    add	a5,a3,t2
    sw	a1,0(a5)
    lw	a1,0(a5)
    and	zero,zero,a1
    lw	a5,36(a3)
    zext.b	a5,a5
    bnez	a5,7598 <.L16>
    ttseminit	2,0,2
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttsetc16	1,0
    lui	a5,0xb3080
    addi	a5,a5,220 # b30800dc <__device_print_strings_info_end+0xacb800dc>
    sw	a5,0(a4)
    ttstallwait	128,16
    lui	a5,0xb6800
    addi	a5,a5,1 # b6800001 <__device_print_strings_info_end+0xb0300001>
    sw	a5,0(a4)
    lui	a5,0xb6200
    addi	a5,a5,1 # b6200001 <__device_print_strings_info_end+0xafd00001>
    sw	a5,0(a4)
    lui	a5,0xb6400
    addi	a5,a5,1 # b6400001 <__device_print_strings_info_end+0xaff00001>
    sw	a5,0(a4)
    lbu	a3,-1992(gp) # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    li	a5,1
    beq	a3,a5,7708 <.L34>
    li	a5,5
    sw	a5,-1996(gp) # ffb00024 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    sw	a5,-2000(gp) # ffb00020 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    ttstallwait	128,2064
    lui	a5,0xb3010
    addi	a5,a5,2 # b3010002 <__device_print_strings_info_end+0xacb10002>
    sw	a5,0(a4)
    li	a2,2
    sb	a2,-1992(gp) # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	128,2064
    lui	a5,0xb3010
    addi	a5,a5,258 # b3010102 <__device_print_strings_info_end+0xacb10102>
    sw	a5,0(a4)
    ttsemwait	322,2,2
    ttsetc16	15,0
    ttsetc16	31,0
    ttsetc16	50,0
    ttsetc16	12,1
    ttsetc16	28,1
    ttsetc16	47,0
    ttsetc16	14,8
    ttsetc16	30,8
    ttsetc16	49,0
    lui	a3,0xffe80
    li	a5,0
    addi	a3,a3,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a5,0(a3)
    lw	a5,0(a3)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a3,4
    sw	a3,0(a5) # ffb80000 <__global_pointer$+0x7f810>
    sw	a2,4(a5)
    lui	a3,0x37c00
    lui	a2,0x2000
    sw	a2,8(a5)
    addi	a3,a3,3 # 37c00003 <__device_print_strings_info_end+0x31700003>
    sw	a3,12(a5)
    sw	a2,16(a5)
    lui	a3,0x1200a
    sw	a3,20(a5)
    sw	a2,24(a5)
    sw	a3,28(a5)
    sw	a3,32(a5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a2,0xb2010
    snez	a3,a5
    slli	a3,a3,0x9
    add	a3,a3,a2
    sw	a3,0(a4)
    ttmop	1,0,0
    ttsetrwc	0,0,0,0,0,4
    ttstallwait	2,2064
    ttsempost	2
    li	a3,1
    sub	a3,a3,a5
    sw	a3,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttstallwait	128,2064
    addi	a5,a5,-1
    snez	a5,a5
    slli	a5,a5,0x9
    lw	s0,12(sp)
    add	a5,a5,a2
    sw	a5,0(a4)
    lw	s1,8(sp)
    li	a0,0
    addi	sp,sp,16
    ret
    lw	a5,-1996(gp) # ffb00024 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a3,5
    bne	a5,a3,75f0 <.L17>
    lw	a3,-2000(gp) # ffb00020 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    bne	a3,a5,75f0 <.L17>
    j	760c <.L18>
    lw	a5,-1996(gp) # ffb00024 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a3,5
    bne	a5,a3,7420 <.L14>
    lw	a3,-2000(gp) # ffb00020 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    bne	a3,a5,7420 <.L14>
    j	743c <.L15>
    mv	a5,a3
    j	7278 <.L4>
