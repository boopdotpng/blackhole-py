    addi	sp,sp,-16
    lui	a5,0xffb01
    lui	a4,0xffb01
    addi	a5,a5,-2000 # ffb00830 <__stack_base>
    addi	a4,a4,-2012 # ffb00824 <__ldm_bss_end>
    bltu	a4,a5,6aa0 <.L2>
    sw	zero,-4(a5)
    sw	zero,-8(a5)
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a5,a5,16
    bgeu	a4,a5,6a88 <.L3>
    addi	a3,a5,-8
    bltu	a4,a3,7144 <.L32>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,6abc <.L5>
    sw	zero,-8(a5)
    auipc	a4,0x0
    addi	a4,a4,1680 # 714c <__kernel_data_lma>
    addi	a5,gp,48 # ffb00820 <unp_cfg_context>
    beq	a4,a5,6b28 <.L7>
    addi	a2,gp,48 # ffb00820 <unp_cfg_context>
    sub	a2,a2,a5
    li	a1,8
    srai	a3,a2,0x2
    bge	a1,a2,6b0c <.L8>
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
    blt	a6,a3,6ae4 <.L9>
    blez	a3,6b28 <.L7>
    lw	a1,0(a4)
    li	a2,2
    sw	a1,0(a5)
    bne	a3,a2,6b28 <.L7>
    lw	a4,4(a4)
    sw	a4,4(a5)
    lui	a5,0xffb12
    sw	zero,104(a5) # ffb12068 <__stack_base+0x11838>
    lw	a4,1312(zero) # 520 <.LLST129+0x7>
    li	a3,128
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    addi	a4,a4,96
    beq	a5,a3,6b54 <.L13>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,6b48 <.L11>
    ttzerosrc	0,0,1,3
    lui	a3,0xffb00
    addi	a3,a3,32 # ffb00020 <cb_interface>
    lhu	a2,24(a3)
    lui	a4,0xffb40
    lw	a5,40(a4) # ffb40028 <__stack_base+0x3f7f8>
    zext.h	a5,a5
    beq	a5,a2,6b68 <.L12>
    lw	a2,8(a3)
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    zext.b	a5,a5
    bnez	a5,6b7c <.L14>
    ttsetadcxy	3,0,0,0,0,11
    ttsetadczw	3,0,0,0,0,15
    lw	a4,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a5,0xffef0
    beqz	a4,6ba0 <.L15>
    addi	a5,a5,896 # ffef0380 <__instrn_buffer+0xb0380>
    li	a4,512
    sw	a4,228(a5)
    sw	a4,236(a5)
    ttatgetm	0
    lui	a4,0xffe40
    mv	a4,a4
    lui	a1,0xb3ff0
    sw	a1,0(a4) # ffe40000 <__instrn_buffer>
    lui	a1,0xb47f0
    sw	a1,0(a4)
    lui	a1,0xb3070
    addi	a1,a1,1 # b3070001 <__device_print_strings_info_end+0xacb70001>
    sw	a1,0(a4)
    lui	a1,0xb4800
    addi	a1,a1,1 # b4800001 <__device_print_strings_info_end+0xae300001>
    sw	a1,0(a4)
    lui	a1,0xb5010
    addi	a1,a1,1 # b5010001 <__device_print_strings_info_end+0xaeb10001>
    sw	a1,0(a4)
    lui	a1,0xb5400
    addi	a0,a1,71 # b5400047 <__device_print_strings_info_end+0xaef00047>
    sw	a0,0(a4)
    addi	a1,a1,119
    sw	a1,0(a4)
    ttatrelm	0
    li	a1,21
    sw	a1,256(a5)
    lui	a1,0x40
    addi	a1,a1,1 # 40001 <.LASF481+0x37da5>
    lui	a7,0x1000
    sw	a1,260(a5)
    addi	a0,a7,21 # 1000015 <.LASF481+0xff7db9>
    sw	a0,448(a5)
    sw	a1,452(a5)
    li	a0,37
    lui	a1,0xf0
    sw	a0,288(a5)
    addi	a1,a1,15 # f000f <.LASF481+0xe7db3>
    sw	a1,292(a5)
    sw	a0,480(a5)
    lui	a0,0x400
    sw	a1,484(a5)
    addi	a0,a0,64 # 400040 <.LASF481+0x3f7de4>
    sw	a0,336(a5)
    addi	t1,a7,256
    sw	t1,344(a5)
    lui	a1,0xffe00
    sw	t1,160(a1) # ffe000a0 <__stack_base+0x2ff870>
    lui	t1,0x800
    addi	t1,t1,128 # 800080 <.LASF481+0x7f7e24>
    sw	t1,164(a1)
    sw	a0,168(a1)
    lui	a0,0x200
    addi	a0,a0,32 # 200020 <.LASF481+0x1f7dc4>
    sw	a0,172(a1)
    lui	a0,0x100
    addi	a0,a0,16 # 100010 <.LASF481+0xf7db4>
    sw	a0,176(a1)
    sw	zero,8(sp)
    lw	a1,176(a1)
    sw	a1,8(sp)
    ttsetc16	5,4
    li	a1,256
    sw	a1,200(a5)
    sw	zero,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,0
    lui	a1,0x45000
    slli	a5,a2,0x8
    addi	a7,a7,-256
    and	a5,a5,a7
    addi	a2,a1,72 # 45000048 <__device_print_strings_info_end+0x3eb00048>
    add	a2,a5,a2
    addi	a1,a1,74
    sw	a2,0(a4)
    add	a5,a5,a1
    lui	t4,0xb4010
    sw	a5,0(a4)
    addi	t4,t4,72 # b4010048 <__device_print_strings_info_end+0xadb10048>
    sw	t4,0(a4)
    ttsetadcxx	1,255,0
    li	a7,0
    lui	t3,0xffe80
    addi	t3,t3,8 # ffe80008 <__instrn_buffer+0x40008>
    mv	a5,a7
    sw	a5,0(t3)
    lw	a5,0(t3)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	t6,4
    sw	t6,0(a5) # ffb80000 <__stack_base+0x7f7d0>
    li	t5,1
    lui	t1,0x42008
    sw	t5,4(a5)
    addi	t1,t1,193 # 420080c1 <__device_print_strings_info_end+0x3bb080c1>
    sw	t1,8(a5)
    lui	a1,0x2000
    sw	a1,12(a5)
    lui	a2,0x43800
    sw	a1,16(a5)
    addi	a2,a2,257 # 43800101 <__device_print_strings_info_end+0x3d300101>
    sw	a2,20(a5)
    sw	a1,24(a5)
    sw	a2,28(a5)
    sw	a2,32(a5)
    sw	t4,0(a4)
    ttsetadcxx	1,255,0
    sw	a7,0(t3)
    lw	a7,0(t3)
    and	zero,zero,a7
    sw	t6,0(a5)
    sw	t5,4(a5)
    sw	t1,8(a5)
    sw	a1,12(a5)
    sw	a1,16(a5)
    sw	a2,20(a5)
    sw	a1,24(a5)
    lw	a7,16(a3)
    sw	a2,28(a5)
    sw	a2,32(a5)
    addi	a7,a7,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a1,0xffef0
    beqz	a5,7138 <.L35>
    addi	t1,a1,1200 # ffef04b0 <__instrn_buffer+0xb04b0>
    addi	a1,a1,1204
    lui	a2,0xffe80
    lw	a5,52(a2) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,6d9c <.L17>
    lw	a5,48(gp) # ffb00820 <unp_cfg_context>
    bnez	a5,6db4 <.L18>
    mv	a1,t1
    sw	a7,0(a1)
    lui	a5,0xffe80
    sw	zero,52(a5) # ffe80034 <__instrn_buffer+0x40034>
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    lw	a2,48(gp) # ffb00820 <unp_cfg_context>
    li	a5,1
    sub	a1,a5,a2
    sw	a1,48(gp) # ffb00820 <unp_cfg_context>
    beq	a2,a5,7130 <.L52>
    ttsetc16	41,257
    lhu	a5,24(a3)
    lui	a1,0x45000
    addi	a5,a5,1
    zext.h	a5,a5
    addi	a1,a1,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a2,a5,0x8
    sh	a5,24(a3)
    add	a2,a2,a1
    sw	a2,0(a4)
    lw	a5,8(a3)
    ttstallwait	32,6
    lw	a1,16(a3)
    lui	a2,0x67110
    add	a5,a5,a1
    addi	a2,a2,8 # 67110008 <__device_print_strings_info_end+0x60c10008>
    lw	a1,4(a3)
    sw	a5,16(a3)
    sw	a2,0(a4)
    bltu	a5,a1,6e3c <.L21>
    lw	a2,0(a3)
    sub	a5,a5,a2
    sw	a5,16(a3)
    lhu	a1,56(a3)
    lui	a2,0xffb41
    lw	a5,40(a2) # ffb41028 <__stack_base+0x407f8>
    zext.h	a5,a5
    beq	a5,a1,6e44 <.L22>
    lw	a1,40(a3)
    lui	a2,0xffe80
    lw	a5,52(a2) # ffe80034 <__instrn_buffer+0x40034>
    zext.b	a5,a5
    bnez	a5,6e58 <.L23>
    ttsetadcxy	3,0,0,0,0,11
    ttsetadczw	3,0,0,0,0,15
    lw	a2,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a5,0xffef0
    beqz	a2,6e7c <.L24>
    addi	a5,a5,896 # ffef0380 <__instrn_buffer+0xb0380>
    li	a2,512
    sw	a2,228(a5)
    sw	a2,236(a5)
    ttatgetm	0
    lui	a2,0xb3ff0
    sw	a2,0(a4)
    lui	a2,0xb47f0
    sw	a2,0(a4)
    lui	a2,0xb3070
    addi	a2,a2,1 # b3070001 <__device_print_strings_info_end+0xacb70001>
    sw	a2,0(a4)
    lui	a2,0xb4800
    addi	a2,a2,1 # b4800001 <__device_print_strings_info_end+0xae300001>
    sw	a2,0(a4)
    lui	a2,0xb5010
    addi	a2,a2,1 # b5010001 <__device_print_strings_info_end+0xaeb10001>
    sw	a2,0(a4)
    lui	a2,0xb5400
    addi	a7,a2,71 # b5400047 <__device_print_strings_info_end+0xaef00047>
    sw	a7,0(a4)
    addi	a2,a2,119
    sw	a2,0(a4)
    ttatrelm	0
    li	a2,21
    sw	a2,256(a5)
    lui	a2,0x40
    addi	a2,a2,1 # 40001 <.LASF481+0x37da5>
    lui	a7,0x1000
    sw	a2,260(a5)
    addi	t1,a7,21 # 1000015 <.LASF481+0xff7db9>
    sw	t1,448(a5)
    sw	a2,452(a5)
    li	t1,37
    lui	a2,0xf0
    sw	t1,288(a5)
    addi	a2,a2,15 # f000f <.LASF481+0xe7db3>
    sw	a2,292(a5)
    sw	t1,480(a5)
    lui	t1,0x400
    sw	a2,484(a5)
    addi	t1,t1,64 # 400040 <.LASF481+0x3f7de4>
    sw	t1,336(a5)
    addi	t3,a7,256
    sw	t3,344(a5)
    lui	a2,0xffe00
    sw	t3,160(a2) # ffe000a0 <__stack_base+0x2ff870>
    lui	t3,0x800
    addi	t3,t3,128 # 800080 <.LASF481+0x7f7e24>
    sw	t3,164(a2)
    sw	t1,168(a2)
    lui	t1,0x200
    addi	t1,t1,32 # 200020 <.LASF481+0x1f7dc4>
    sw	t1,172(a2)
    lui	t1,0x100
    addi	t1,t1,16 # 100010 <.LASF481+0xf7db4>
    sw	t1,176(a2)
    sw	zero,12(sp)
    lw	a2,176(a2)
    sw	a2,12(sp)
    ttsetc16	5,4
    li	a2,256
    sw	a2,200(a5)
    sw	zero,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,0
    lui	a2,0x45000
    slli	a5,a1,0x8
    addi	a7,a7,-256
    and	a5,a5,a7
    addi	a1,a2,72 # 45000048 <__device_print_strings_info_end+0x3eb00048>
    add	a1,a5,a1
    addi	a2,a2,74
    sw	a1,0(a4)
    add	a5,a5,a2
    lui	t4,0xb4010
    sw	a5,0(a4)
    addi	t4,t4,72 # b4010048 <__device_print_strings_info_end+0xadb10048>
    sw	t4,0(a4)
    ttsetadcxx	1,255,0
    li	a7,0
    lui	t3,0xffe80
    addi	t3,t3,8 # ffe80008 <__instrn_buffer+0x40008>
    mv	a5,a7
    sw	a5,0(t3)
    lw	a5,0(t3)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	t6,4
    sw	t6,0(a5) # ffb80000 <__stack_base+0x7f7d0>
    li	t5,1
    lui	t1,0x42008
    sw	t5,4(a5)
    addi	t1,t1,193 # 420080c1 <__device_print_strings_info_end+0x3bb080c1>
    sw	t1,8(a5)
    lui	a1,0x2000
    sw	a1,12(a5)
    lui	a2,0x43800
    sw	a1,16(a5)
    addi	a2,a2,257 # 43800101 <__device_print_strings_info_end+0x3d300101>
    sw	a2,20(a5)
    sw	a1,24(a5)
    sw	a2,28(a5)
    sw	a2,32(a5)
    sw	t4,0(a4)
    ttsetadcxx	1,255,0
    sw	a7,0(t3)
    lw	a7,0(t3)
    and	zero,zero,a7
    sw	t6,0(a5)
    sw	t5,4(a5)
    sw	t1,8(a5)
    sw	a1,12(a5)
    sw	a1,16(a5)
    sw	a2,20(a5)
    sw	a1,24(a5)
    lw	a7,48(a3)
    sw	a2,28(a5)
    sw	a2,32(a5)
    addi	a7,a7,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a1,0xffef0
    beqz	a5,7124 <.L37>
    addi	a6,a1,1200 # ffef04b0 <__instrn_buffer+0xb04b0>
    addi	a1,a1,1204
    lui	a2,0xffe80
    lw	a5,52(a2) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,7070 <.L26>
    lw	a5,48(gp) # ffb00820 <unp_cfg_context>
    bnez	a5,7088 <.L27>
    mv	a1,a6
    sw	a7,0(a1)
    lui	a5,0xffe80
    sw	zero,52(a5) # ffe80034 <__instrn_buffer+0x40034>
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    lw	a2,48(gp) # ffb00820 <unp_cfg_context>
    li	a5,1
    sub	a1,a5,a2
    sw	a1,48(gp) # ffb00820 <unp_cfg_context>
    beq	a2,a5,711c <.L53>
    ttsetc16	41,257
    lhu	a5,56(a3)
    lui	a1,0x45000
    addi	a5,a5,1
    zext.h	a5,a5
    addi	a1,a1,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a2,a5,0x8
    sh	a5,56(a3)
    add	a2,a2,a1
    sw	a2,0(a4)
    lw	a5,40(a3)
    ttstallwait	32,6
    lw	a1,48(a3)
    lui	a2,0x67110
    add	a5,a5,a1
    addi	a2,a2,1032 # 67110408 <__device_print_strings_info_end+0x60c10408>
    lw	a1,36(a3)
    sw	a5,48(a3)
    sw	a2,0(a4)
    bltu	a5,a1,7110 <.L30>
    lw	a4,32(a3)
    sub	a5,a5,a4
    sw	a5,48(a3)
    li	a0,0
    addi	sp,sp,16
    ret
    ttsetc16	41,0
    j	70b8 <.L29>
    addi	a6,a1,304
    addi	a1,a1,308
    j	706c <.L25>
    ttsetc16	41,0
    j	6de4 <.L20>
    addi	t1,a1,304
    addi	a1,a1,308
    j	6d98 <.L16>
    mv	a5,a3
    j	6ab0 <.L4>
