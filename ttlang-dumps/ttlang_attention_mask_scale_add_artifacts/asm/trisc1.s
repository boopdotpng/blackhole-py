    addi	sp,sp,-16
    lui	a5,0xffb00
    lui	a4,0xffb00
    addi	a5,a5,56 # ffb00038 <__stack_base+0x8>
    addi	a4,a4,44 # ffb0002c <__ldm_bss_end>
    bltu	a4,a5,7260 <.L2>
    sw	zero,-4(a5)
    sw	zero,-8(a5)
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a5,a5,16
    bgeu	a4,a5,7248 <.L3>
    addi	a3,a5,-8
    bltu	a4,a3,7cdc <.L41>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,727c <.L5>
    sw	zero,-8(a5)
    auipc	a4,0x1
    addi	a4,a4,-1432 # 7ce4 <__kernel_data_lma>
    addi	a5,gp,-2000 # ffb00020 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    beq	a4,a5,72ec <.L7>
    lui	a2,0xffb00
    addi	a2,a2,40 # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    sub	a2,a2,a5
    li	a1,8
    srai	a3,a2,0x2
    bge	a1,a2,72d0 <.L8>
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
    blt	a6,a3,72a8 <.L9>
    blez	a3,72ec <.L7>
    lw	a1,0(a4)
    li	a2,2
    sw	a1,0(a5)
    bne	a3,a2,72ec <.L7>
    lw	a4,4(a4)
    sw	a4,4(a5)
    lw	a4,1312(zero) # 520 <.LLST108+0x9>
    li	a3,128
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    addi	a4,a4,96
    beq	a5,a3,7310 <.L13>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,7304 <.L11>
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
    lui	a2,0x28008
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
    bnez	a5,73b8 <.L12>
    ttseminit	1,0,2
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
    lui	a4,0xb6202
    addi	a4,a4,1 # b6202001 <__device_print_strings_info_end+0xafd02001>
    sw	a4,0(a5)
    lui	a4,0xb6404
    addi	a4,a4,1 # b6404001 <__device_print_strings_info_end+0xaff04001>
    sw	a4,0(a5)
    lbu	a2,-1992(gp) # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    li	a4,1
    beq	a2,a4,7cc8 <.L84>
    sw	zero,-1996(gp) # ffb00024 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    sw	zero,-2000(gp) # ffb00020 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    ttstallwait	128,2064
    lui	a4,0xb3010
    addi	a4,a4,2 # b3010002 <__device_print_strings_info_end+0xacb10002>
    sw	a4,0(a5)
    li	a2,2
    sb	a2,-1992(gp) # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	128,2064
    lui	a4,0xb3010
    addi	a4,a4,258 # b3010102 <__device_print_strings_info_end+0xacb10102>
    sw	a4,0(a5)
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
    li	a4,0
    addi	a0,a3,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a4,0(a0)
    lw	a4,0(a0)
    and	zero,zero,a4
    lui	a4,0xffb80
    li	a0,4
    sw	a0,0(a4) # ffb80000 <__global_pointer$+0x7f810>
    sw	a2,4(a4)
    lui	a0,0x2000
    lui	a2,0x37c00
    sw	a0,8(a4)
    addi	a2,a2,3 # 37c00003 <__device_print_strings_info_end+0x31700003>
    sw	a2,12(a4)
    sw	a0,16(a4)
    lui	a2,0x28008
    sw	a2,20(a4)
    sw	a0,24(a4)
    sw	a2,28(a4)
    sw	a2,32(a4)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    ttsemwait	2,128,2
    ttstallwait	2,2064
    ttsempost	128
    lw	a4,60(a3)
    zext.b	a4,a4
    beqz	a4,74d8 <.L16>
    li	a4,1
    sw	a4,60(a3)
    lw	a4,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a3,0xffec1
    snez	a4,a4
    slli	a4,a4,0x9
    sw	a4,0(a3) # ffec1000 <__instrn_buffer+0x81000>
    ttsemwait	2,4,1
    ttstallwait	2,2064
    ttsemget	4
    lui	a4,0x100ec
    addi	a3,a4,4 # 100ec004 <__device_print_strings_info_end+0x9bec004>
    sw	a4,0(a5)
    addi	a4,a4,1
    bne	a4,a3,7514 <.L17>
    ttsemwait	2,128,2
    ttstallwait	2,2064
    ttsempost	128
    lui	a3,0xffe80
    lw	a4,60(a3) # ffe8003c <__instrn_buffer+0x4003c>
    zext.b	a4,a4
    beqz	a4,7530 <.L18>
    li	a4,1
    sw	a4,60(a3)
    lw	a4,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a3,0xffec1
    snez	a4,a4
    slli	a4,a4,0x9
    addi	a4,a4,128
    sw	a4,0(a3) # ffec1000 <__instrn_buffer+0x81000>
    ttsemwait	2,4,1
    ttstallwait	2,2064
    ttsemget	4
    lui	a3,0x100ec
    addi	a4,a3,8 # 100ec008 <__device_print_strings_info_end+0x9bec008>
    addi	a3,a3,12
    sw	a4,0(a5)
    addi	a4,a4,1
    bne	a4,a3,7574 <.L19>
    ttsemwait	2,128,2
    ttstallwait	2,2064
    ttsempost	128
    lui	a3,0xffe80
    lw	a4,60(a3) # ffe8003c <__instrn_buffer+0x4003c>
    zext.b	a4,a4
    beqz	a4,7590 <.L20>
    li	a4,1
    sw	a4,60(a3)
    lw	a4,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a3,0xffec1
    snez	a4,a4
    slli	a4,a4,0x9
    addi	a4,a4,256
    sw	a4,0(a3) # ffec1000 <__instrn_buffer+0x81000>
    ttsemwait	2,4,1
    ttstallwait	2,2064
    ttsemget	4
    lui	a4,0x100ec
    addi	a3,a4,4 # 100ec004 <__device_print_strings_info_end+0x9bec004>
    sw	a4,0(a5)
    addi	a4,a4,1
    bne	a4,a3,75d0 <.L21>
    ttsemwait	2,128,2
    ttstallwait	2,2064
    ttsempost	128
    lui	a2,0xffe80
    lw	a3,60(a2) # ffe8003c <__instrn_buffer+0x4003c>
    zext.b	a3,a3
    beqz	a3,75ec <.L22>
    li	a3,1
    sw	a3,60(a2)
    lw	a3,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a2,0xffec1
    snez	a3,a3
    slli	a3,a3,0x9
    addi	a3,a3,384
    sw	a3,0(a2) # ffec1000 <__instrn_buffer+0x81000>
    ttsemwait	2,4,1
    ttstallwait	2,2064
    ttsemget	4
    lui	a2,0x100ec
    addi	a3,a2,8 # 100ec008 <__device_print_strings_info_end+0x9bec008>
    addi	a2,a2,12
    sw	a3,0(a5)
    addi	a3,a3,1
    bne	a3,a2,7630 <.L23>
    ttsetc16	15,0
    ttsetc16	31,0
    ttsetc16	50,0
    ttsetc16	12,1
    ttsetc16	28,1
    ttsetc16	47,0
    ttsetc16	14,8
    ttsetc16	30,8
    ttsetc16	49,0
    lui	a0,0xffe80
    li	a2,0
    addi	a6,a0,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a2,0(a6)
    lw	a2,0(a6)
    and	zero,zero,a2
    lui	a2,0xffb80
    li	a6,4
    sw	a6,0(a2) # ffb80000 <__global_pointer$+0x7f810>
    li	a6,2
    sw	a6,4(a2)
    lui	a7,0x2000
    lui	a6,0x37c00
    sw	a7,8(a2)
    addi	a6,a6,3 # 37c00003 <__device_print_strings_info_end+0x31700003>
    sw	a6,12(a2)
    sw	a7,16(a2)
    lui	a6,0x28008
    sw	a6,20(a2)
    sw	a7,24(a2)
    sw	a6,28(a2)
    sw	a6,32(a2)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    ttsemwait	2,128,2
    ttstallwait	2,2064
    ttsempost	128
    lw	a2,60(a0)
    zext.b	a2,a2
    beqz	a2,76cc <.L24>
    li	a2,1
    sw	a2,60(a0)
    lw	a2,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a0,0xffec1
    snez	a2,a2
    slli	a2,a2,0x9
    addi	a2,a2,64
    sw	a2,0(a0) # ffec1000 <__instrn_buffer+0x81000>
    ttsemwait	2,4,1
    ttstallwait	2,2064
    ttsemget	4
    lui	a0,0x100ec
    mv	a2,a4
    addi	a0,a0,8 # 100ec008 <__device_print_strings_info_end+0x9bec008>
    sw	a2,0(a5)
    addi	a2,a2,1
    bne	a2,a0,7710 <.L25>
    ttsemwait	2,128,2
    ttstallwait	2,2064
    ttsempost	128
    lui	a0,0xffe80
    lw	a2,60(a0) # ffe8003c <__instrn_buffer+0x4003c>
    zext.b	a2,a2
    beqz	a2,772c <.L26>
    li	a2,1
    sw	a2,60(a0)
    lw	a2,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a0,0xffec1
    snez	a2,a2
    slli	a2,a2,0x9
    addi	a2,a2,192
    sw	a2,0(a0) # ffec1000 <__instrn_buffer+0x81000>
    ttsemwait	2,4,1
    ttstallwait	2,2064
    ttsemget	4
    lui	a0,0x100ec
    mv	a2,a3
    addi	a0,a0,16 # 100ec010 <__device_print_strings_info_end+0x9bec010>
    sw	a2,0(a5)
    addi	a2,a2,1
    bne	a2,a0,7770 <.L27>
    ttsemwait	2,128,2
    ttstallwait	2,2064
    ttsempost	128
    lui	a0,0xffe80
    lw	a2,60(a0) # ffe8003c <__instrn_buffer+0x4003c>
    zext.b	a2,a2
    beqz	a2,778c <.L28>
    li	a2,1
    sw	a2,60(a0)
    lw	a2,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a0,0xffec1
    snez	a2,a2
    slli	a2,a2,0x9
    addi	a2,a2,320
    sw	a2,0(a0) # ffec1000 <__instrn_buffer+0x81000>
    ttsemwait	2,4,1
    ttstallwait	2,2064
    ttsemget	4
    lui	a2,0x100ec
    addi	a2,a2,8 # 100ec008 <__device_print_strings_info_end+0x9bec008>
    sw	a4,0(a5)
    addi	a4,a4,1
    bne	a4,a2,77cc <.L29>
    ttsemwait	2,128,2
    ttstallwait	2,2064
    ttsempost	128
    lui	a2,0xffe80
    lw	a4,60(a2) # ffe8003c <__instrn_buffer+0x4003c>
    zext.b	a4,a4
    beqz	a4,77e8 <.L30>
    li	a4,1
    sw	a4,60(a2)
    lw	a4,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a2,0xffec1
    snez	a4,a4
    slli	a4,a4,0x9
    addi	a4,a4,448
    sw	a4,0(a2) # ffec1000 <__instrn_buffer+0x81000>
    ttsemwait	2,4,1
    ttstallwait	2,2064
    ttsemget	4
    lui	a4,0x100ec
    addi	a4,a4,16 # 100ec010 <__device_print_strings_info_end+0x9bec010>
    sw	a3,0(a5)
    addi	a3,a3,1
    bne	a3,a4,7828 <.L31>
    sfpconfig	15,0,1
    ttsetc16	19,0
    ttsetc16	35,0
    ttsetc16	54,0
    ttsetrwc	0,0,0,0,0,15
    lw	a4,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a3,0x3e000
    snez	a4,a4
    sw	a3,12(sp)
    slli	a4,a4,0x9
    lui	a3,0xb2010
    add	a4,a4,a3
    lw	a3,12(sp)
    sw	a4,0(a5)
    ttstallwait	256,16
    lui	a4,0x71080
    zext.h	a2,a3
    lui	a0,0x71020
    srli	a3,a3,0x10
    add	a3,a3,a4
    add	a2,a2,a0
    li	a4,4
    sw	a2,0(a5)
    sw	a3,0(a5)
    ttreplay	0,4,1,1
    sfpload	L1,0,0,7
    sfpmul	L1,L1,L0,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    sfpload	L1,0,0,7
    sfpmul	L0,L1,L0,0
    sfpstore	L0,0,0,7
    ttincrwc	0,2,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a4,a4,-1 # 7107ffff <__device_print_strings_info_end+0x6ab7ffff>
    bnez	a4,788c <.L32>
    ttsetrwc	0,0,0,0,0,4
    sfpconfig	15,0,1
    ttsetc16	19,0
    ttsetc16	35,0
    ttsetc16	54,0
    ttsetrwc	0,0,0,0,0,15
    lw	a4,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a3,0xb2010
    snez	a4,a4
    lui	a2,0x3e000
    addi	a3,a3,128 # b2010080 <__device_print_strings_info_end+0xabb10080>
    slli	a4,a4,0x9
    sw	a2,8(sp)
    add	a4,a4,a3
    lw	a3,8(sp)
    sw	a4,0(a5)
    ttstallwait	256,16
    lui	a4,0x71080
    zext.h	a2,a3
    lui	a0,0x71020
    srli	a3,a3,0x10
    add	a3,a3,a4
    add	a2,a2,a0
    li	a4,4
    sw	a2,0(a5)
    sw	a3,0(a5)
    ttreplay	0,4,1,1
    sfpload	L1,0,0,7
    sfpmul	L1,L1,L0,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    sfpload	L1,0,0,7
    sfpmul	L0,L1,L0,0
    sfpstore	L0,0,0,7
    ttincrwc	0,2,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a4,a4,-1 # 7107ffff <__device_print_strings_info_end+0x6ab7ffff>
    bnez	a4,7940 <.L33>
    ttsetrwc	0,0,0,0,0,4
    sfpconfig	15,0,1
    ttsetc16	19,0
    ttsetc16	35,0
    ttsetc16	54,0
    ttsetrwc	0,0,0,0,0,15
    lw	a4,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a3,0xb2010
    snez	a4,a4
    lui	a2,0x3e000
    addi	a3,a3,256 # b2010100 <__device_print_strings_info_end+0xabb10100>
    slli	a4,a4,0x9
    sw	a2,4(sp)
    add	a4,a4,a3
    lw	a3,4(sp)
    sw	a4,0(a5)
    ttstallwait	256,16
    lui	a4,0x71080
    zext.h	a2,a3
    lui	a0,0x71020
    srli	a3,a3,0x10
    add	a3,a3,a4
    add	a2,a2,a0
    li	a4,4
    sw	a2,0(a5)
    sw	a3,0(a5)
    ttreplay	0,4,1,1
    sfpload	L1,0,0,7
    sfpmul	L1,L1,L0,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    sfpload	L1,0,0,7
    sfpmul	L0,L1,L0,0
    sfpstore	L0,0,0,7
    ttincrwc	0,2,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a4,a4,-1 # 7107ffff <__device_print_strings_info_end+0x6ab7ffff>
    bnez	a4,79f4 <.L34>
    ttsetrwc	0,0,0,0,0,4
    sfpconfig	15,0,1
    ttsetc16	19,0
    ttsetc16	35,0
    ttsetc16	54,0
    ttsetrwc	0,0,0,0,0,15
    lw	a4,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a3,0xb2010
    snez	a4,a4
    lui	a2,0x3e000
    addi	a3,a3,384 # b2010180 <__device_print_strings_info_end+0xabb10180>
    slli	a4,a4,0x9
    sw	a2,0(sp)
    add	a4,a4,a3
    lw	a3,0(sp)
    sw	a4,0(a5)
    ttstallwait	256,16
    lui	a0,0x71020
    zext.h	a2,a3
    srli	a4,a3,0x10
    lui	a3,0x71080
    add	a3,a3,a4
    add	a2,a2,a0
    li	a4,4
    sw	a2,0(a5)
    sw	a3,0(a5)
    ttreplay	0,4,1,1
    sfpload	L1,0,0,7
    sfpmul	L1,L1,L0,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    sfpload	L1,0,0,7
    sfpmul	L0,L1,L0,0
    sfpstore	L0,0,0,7
    ttincrwc	0,2,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a4,a4,-1
    bnez	a4,7aa8 <.L35>
    ttsetrwc	0,0,0,0,0,4
    sfpconfig	15,0,1
    ttsetc16	19,0
    ttsetc16	35,0
    ttsetc16	54,0
    ttsetrwc	0,0,0,0,0,15
    lw	a4,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a3,0xb2010
    snez	a4,a4
    slli	a4,a4,0x9
    add	a4,a4,a3
    sw	a4,0(a5)
    ttstallwait	256,16
    li	a4,4
    ttreplay	0,5,1,1
    sfpload	L0,0,0,7
    sfpload	L1,64,0,7
    sfpadd	L0,L0,L1,0
    sfpstore	L0,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a4,a4,-1
    bnez	a4,7b34 <.L36>
    ttsetrwc	0,0,0,0,0,4
    lw	a4,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a3,0xb2010
    snez	a4,a4
    slli	a4,a4,0x9
    add	a4,a4,a3
    sw	a4,0(a5)
    ttstallwait	256,16
    li	a4,4
    ttreplay	0,5,1,1
    sfpload	L0,128,0,7
    sfpload	L1,192,0,7
    sfpadd	L0,L0,L1,0
    sfpstore	L0,128,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a4,a4,-1
    bnez	a4,7b9c <.L37>
    ttsetrwc	0,0,0,0,0,4
    lw	a4,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a3,0xb2010
    snez	a4,a4
    slli	a4,a4,0x9
    add	a4,a4,a3
    sw	a4,0(a5)
    ttstallwait	256,16
    li	a4,4
    ttreplay	0,5,1,1
    sfpload	L0,256,0,7
    sfpload	L1,320,0,7
    sfpadd	L0,L0,L1,0
    sfpstore	L0,256,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a4,a4,-1
    bnez	a4,7c04 <.L38>
    ttsetrwc	0,0,0,0,0,4
    lw	a4,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a3,0xb2010
    snez	a4,a4
    slli	a4,a4,0x9
    add	a4,a4,a3
    sw	a4,0(a5)
    ttstallwait	256,16
    li	a5,4
    ttreplay	0,5,1,1
    sfpload	L0,384,0,7
    sfpload	L1,448,0,7
    sfpadd	L0,L0,L1,0
    sfpstore	L0,384,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a5,a5,-1
    bnez	a5,7c6c <.L39>
    ttsetrwc	0,0,0,0,0,4
    ttstallwait	2,2064
    ttsempost	2
    li	a0,0
    addi	sp,sp,16
    ret
    lw	a0,-1996(gp) # ffb00024 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    lw	a6,-2000(gp) # ffb00020 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    or	a0,a0,a6
    bnez	a0,7418 <.L14>
    j	7430 <.L15>
    mv	a5,a3
    j	7270 <.L4>
