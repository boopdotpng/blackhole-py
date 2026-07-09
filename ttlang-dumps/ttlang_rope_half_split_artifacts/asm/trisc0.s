    addi	sp,sp,-16
    sw	ra,12(sp)
    lui	a5,0xffb01
    lui	a4,0xffb01
    addi	a5,a5,-2000 # ffb00830 <__stack_base>
    addi	a4,a4,-2012 # ffb00824 <__ldm_bss_end>
    bltu	a4,a5,6aa4 <.L76>
    sw	zero,-4(a5)
    sw	zero,-8(a5)
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a5,a5,16
    bgeu	a4,a5,6a8c <.L77>
    addi	a3,a5,-8
    bltu	a4,a3,6b70 <.L88>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,6ac0 <.L79>
    sw	zero,-8(a5)
    auipc	a4,0x1
    addi	a4,a4,-1012 # 76cc <__kernel_data_lma>
    addi	a5,gp,48 # ffb00820 <unp_cfg_context>
    beq	a4,a5,6b2c <.L81>
    addi	a2,gp,48 # ffb00820 <unp_cfg_context>
    sub	a2,a2,a5
    li	a1,8
    srai	a3,a2,0x2
    bge	a1,a2,6b10 <.L82>
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
    blt	a6,a3,6ae8 <.L83>
    blez	a3,6b2c <.L81>
    lw	a1,0(a4)
    li	a2,2
    sw	a1,0(a5)
    bne	a3,a2,6b2c <.L81>
    lw	a4,4(a4)
    sw	a4,4(a5)
    lui	a5,0xffb12
    sw	zero,104(a5) # ffb12068 <__stack_base+0x11838>
    lw	a4,1312(zero) # 520 <.LASF1079+0x5>
    li	a3,128
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    addi	a4,a4,96
    beq	a5,a3,6b58 <.L85>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,6b4c <.L86>
    ttzerosrc	0,0,1,3
    jal	6b78 <_Z11kernel_mainv>
    lw	ra,12(sp)
    li	a0,0
    addi	sp,sp,16
    ret
    mv	a5,a3
    j	6ab4 <.L78>
    lui	a5,0xffb00
    addi	a5,a5,32 # ffb00020 <cb_interface>
    lhu	a2,24(a5)
    addi	sp,sp,-16
    lui	a3,0xffb40
    lw	a4,40(a3) # ffb40028 <__stack_base+0x3f7f8>
    zext.h	a4,a4
    beq	a4,a2,6b8c <.L2>
    lhu	a2,56(a5)
    lui	a3,0xffb41
    lw	a4,40(a3) # ffb41028 <__stack_base+0x407f8>
    zext.h	a4,a4
    beq	a4,a2,6ba0 <.L3>
    lhu	a2,88(a5)
    lui	a3,0xffb42
    lw	a4,40(a3) # ffb42028 <__stack_base+0x417f8>
    zext.h	a4,a4
    beq	a2,a4,6bb4 <.L4>
    lhu	a2,152(a5)
    lui	a3,0xffb44
    lw	a4,40(a3) # ffb44028 <__stack_base+0x437f8>
    zext.h	a4,a4
    beq	a2,a4,6bc8 <.L5>
    lw	a0,8(a5)
    lw	a2,72(a5)
    lui	a3,0xffe80
    lw	a4,52(a3) # ffe80034 <__instrn_buffer+0x40034>
    zext.b	a4,a4
    bnez	a4,6be0 <.L6>
    ttsetadcxy	3,0,0,0,0,11
    ttsetadczw	3,0,0,0,0,15
    lw	a4,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a3,0xffef0
    beqz	a4,6c04 <.L7>
    addi	a3,a3,896 # ffef0380 <__instrn_buffer+0xb0380>
    li	a4,512
    sw	a4,228(a3)
    sw	a4,236(a3)
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
    addi	a7,a1,71 # b5400047 <__device_print_strings_info_end+0xaef00047>
    sw	a7,0(a4)
    addi	a1,a1,119
    sw	a1,0(a4)
    ttatrelm	0
    li	a1,21
    sw	a1,256(a3)
    lui	a1,0x40
    addi	a1,a1,1 # 40001 <.LASF492+0x3730c>
    lui	a7,0x1000
    sw	a1,260(a3)
    addi	t1,a7,21 # 1000015 <.LASF492+0xff7320>
    sw	t1,448(a3)
    sw	a1,452(a3)
    li	t1,37
    lui	a1,0xf0
    sw	t1,288(a3)
    addi	a1,a1,15 # f000f <.LASF492+0xe731a>
    sw	a1,292(a3)
    sw	t1,480(a3)
    lui	t1,0x400
    sw	a1,484(a3)
    addi	t1,t1,64 # 400040 <.LASF492+0x3f734b>
    sw	t1,336(a3)
    addi	t3,a7,256
    sw	t3,344(a3)
    lui	a1,0xffe00
    sw	t3,160(a1) # ffe000a0 <__stack_base+0x2ff870>
    lui	t3,0x800
    addi	t3,t3,128 # 800080 <.LASF492+0x7f738b>
    sw	t3,164(a1)
    sw	t1,168(a1)
    lui	t1,0x200
    addi	t1,t1,32 # 200020 <.LASF492+0x1f732b>
    sw	t1,172(a1)
    lui	t1,0x100
    addi	t1,t1,16 # 100010 <.LASF492+0xf731b>
    sw	t1,176(a1)
    sw	zero,8(sp)
    lw	a1,176(a1)
    sw	a1,8(sp)
    ttsetc16	5,4
    li	a1,256
    sw	a1,200(a3)
    sw	zero,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,0
    lui	t1,0x45000
    addi	a7,a7,-256
    slli	a0,a0,0x8
    and	a0,a0,a7
    slli	a3,a2,0x8
    addi	a2,t1,72 # 45000048 <__device_print_strings_info_end+0x3eb00048>
    and	a3,a3,a7
    add	a2,a0,a2
    addi	t1,t1,74
    sw	a2,0(a4)
    add	a3,a3,t1
    lui	t4,0xb4010
    sw	a3,0(a4)
    addi	t4,t4,72 # b4010048 <__device_print_strings_info_end+0xadb10048>
    sw	t4,0(a4)
    ttsetadcxx	3,255,0
    li	a0,0
    lui	t3,0xffe80
    addi	t3,t3,8 # ffe80008 <__instrn_buffer+0x40008>
    mv	a3,a0
    sw	a3,0(t3)
    lw	a3,0(t3)
    and	zero,zero,a3
    lui	a3,0xffb80
    li	a2,2
    sw	a2,0(a3) # ffb80000 <__stack_base+0x7f7d0>
    sw	a2,4(a3)
    lui	a2,0x2000
    sw	a2,8(a3)
    sw	a2,12(a3)
    lui	t1,0x42008
    sw	a2,16(a3)
    addi	t1,t1,193 # 420080c1 <__device_print_strings_info_end+0x3bb080c1>
    lui	a7,0x42808
    sw	t1,20(a3)
    addi	a7,a7,193 # 428080c1 <__device_print_strings_info_end+0x3c3080c1>
    sw	a7,24(a3)
    sw	a7,28(a3)
    sw	a7,32(a3)
    sw	t4,0(a4)
    ttsetadcxx	1,255,0
    sw	a0,0(t3)
    lw	a0,0(t3)
    and	zero,zero,a0
    li	a0,4
    sw	a0,0(a3)
    li	a0,1
    sw	a0,4(a3)
    sw	t1,8(a3)
    sw	a2,12(a3)
    lui	a0,0x43800
    sw	a2,16(a3)
    addi	a0,a0,257 # 43800101 <__device_print_strings_info_end+0x3d300101>
    sw	a0,20(a3)
    sw	a2,24(a3)
    lw	a7,48(a5)
    sw	a0,28(a3)
    sw	a0,32(a3)
    addi	a7,a7,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a3,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a0,0xffef0
    beqz	a3,76c0 <.L47>
    addi	t1,a0,1200 # ffef04b0 <__instrn_buffer+0xb04b0>
    addi	a0,a0,1204
    lui	a2,0xffe80
    lw	a3,52(a2) # ffe80034 <__instrn_buffer+0x40034>
    andi	a3,a3,254
    bnez	a3,6e14 <.L9>
    lw	a3,48(gp) # ffb00820 <unp_cfg_context>
    bnez	a3,6e2c <.L10>
    mv	a0,t1
    sw	a7,0(a0)
    lui	a3,0xffe80
    sw	zero,52(a3) # ffe80034 <__instrn_buffer+0x40034>
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    lw	a2,48(gp) # ffb00820 <unp_cfg_context>
    li	a3,1
    sub	a0,a3,a2
    sw	a0,48(gp) # ffb00820 <unp_cfg_context>
    beq	a2,a3,76b8 <.L73>
    ttsetc16	41,257
    lui	a3,0xb4010
    addi	a3,a3,72 # b4010048 <__device_print_strings_info_end+0xadb10048>
    sw	a3,0(a4)
    ttsetadcxx	1,255,0
    lui	a2,0xffe80
    li	a3,0
    addi	a2,a2,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a3,0(a2)
    lw	a3,0(a2)
    and	zero,zero,a3
    lui	a3,0xffb80
    li	a2,4
    sw	a2,0(a3) # ffb80000 <__stack_base+0x7f7d0>
    li	a2,1
    sw	a2,4(a3)
    lui	a2,0x42008
    addi	a2,a2,193 # 420080c1 <__device_print_strings_info_end+0x3bb080c1>
    sw	a2,8(a3)
    lui	a0,0x2000
    sw	a0,12(a3)
    lui	a2,0x43800
    sw	a0,16(a3)
    addi	a2,a2,257 # 43800101 <__device_print_strings_info_end+0x3d300101>
    sw	a2,20(a3)
    sw	a0,24(a3)
    lw	a7,144(a5)
    sw	a2,28(a3)
    sw	a2,32(a3)
    addi	a7,a7,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a3,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a0,0xffef0
    beqz	a3,76ac <.L48>
    addi	t1,a0,1200 # ffef04b0 <__instrn_buffer+0xb04b0>
    addi	a0,a0,1204
    lui	a2,0xffe80
    lw	a3,52(a2) # ffe80034 <__instrn_buffer+0x40034>
    andi	a3,a3,254
    bnez	a3,6eec <.L14>
    lw	a3,48(gp) # ffb00820 <unp_cfg_context>
    bnez	a3,6f04 <.L15>
    mv	a0,t1
    sw	a7,0(a0)
    lui	a3,0xffe80
    sw	zero,52(a3) # ffe80034 <__instrn_buffer+0x40034>
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    lw	a2,48(gp) # ffb00820 <unp_cfg_context>
    li	a3,1
    sub	a0,a3,a2
    sw	a0,48(gp) # ffb00820 <unp_cfg_context>
    beq	a2,a3,76a4 <.L74>
    ttsetc16	41,257
    lui	a3,0xb4010
    addi	a3,a3,72 # b4010048 <__device_print_strings_info_end+0xadb10048>
    sw	a3,0(a4)
    ttsetadcxx	3,255,0
    lui	a2,0xffe80
    li	a3,0
    addi	a2,a2,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a3,0(a2)
    lw	a3,0(a2)
    and	zero,zero,a3
    lui	a3,0xffb80
    li	a2,2
    sw	a2,0(a3) # ffb80000 <__stack_base+0x7f7d0>
    sw	a2,4(a3)
    lui	a2,0x2000
    sw	a2,8(a3)
    sw	a2,12(a3)
    sw	a2,16(a3)
    lui	a2,0x42008
    addi	a2,a2,193 # 420080c1 <__device_print_strings_info_end+0x3bb080c1>
    sw	a2,20(a3)
    lui	a2,0x42808
    addi	a2,a2,193 # 428080c1 <__device_print_strings_info_end+0x3c3080c1>
    lw	t1,16(a5)
    lw	a7,80(a5)
    sw	a2,24(a3)
    sw	a2,28(a3)
    addi	t3,t1,-1
    addi	a7,a7,-1
    sw	a2,32(a3)
    ttsetadczw	3,0,0,0,0,15
    lw	a3,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a2,0xffef0
    beqz	a3,6fc0 <.L18>
    addi	a2,a2,896 # ffef0380 <__instrn_buffer+0xb0380>
    lui	a0,0xffe80
    lw	a3,52(a0) # ffe80034 <__instrn_buffer+0x40034>
    andi	a3,a3,254
    bnez	a3,6fc4 <.L19>
    lw	a3,48(gp) # ffb00820 <unp_cfg_context>
    bnez	a3,7674 <.L20>
    sw	t3,304(a2)
    sw	a7,496(a2)
    sw	zero,52(a0)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    li	a3,1
    sw	a3,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,257
    lhu	a3,152(a5)
    lui	a7,0x45000
    addi	a3,a3,1
    zext.h	a3,a3
    addi	a7,a7,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a0,a3,0x8
    sh	a3,152(a5)
    add	a0,a0,a7
    sw	a0,0(a4)
    lw	a3,136(a5)
    ttstallwait	32,6
    lw	a7,144(a5)
    lui	a0,0x67111
    add	a3,a3,a7
    addi	a0,a0,8 # 67111008 <__device_print_strings_info_end+0x60c11008>
    lw	a7,132(a5)
    sw	a3,144(a5)
    sw	a0,0(a4)
    bltu	a3,a7,7054 <.L23>
    lw	a0,128(a5)
    sub	a3,a3,a0
    sw	a3,144(a5)
    lhu	a3,88(a5)
    lui	a7,0x45000
    addi	a3,a3,1
    zext.h	a3,a3
    addi	a7,a7,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a0,a3,0x8
    sh	a3,88(a5)
    add	a0,a0,a7
    sw	a0,0(a4)
    lw	a3,72(a5)
    ttstallwait	32,6
    lw	a7,80(a5)
    lui	a0,0x67111
    add	a3,a3,a7
    addi	a0,a0,-2040 # 67110808 <__device_print_strings_info_end+0x60c10808>
    lw	a7,68(a5)
    sw	a3,80(a5)
    sw	a0,0(a4)
    bltu	a3,a7,70ac <.L24>
    lw	a0,64(a5)
    sub	a3,a3,a0
    sw	a3,80(a5)
    lhu	a0,56(a5)
    lui	a7,0x45000
    addi	a0,a0,1
    zext.h	a0,a0
    addi	a7,a7,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a3,a0,0x8
    add	a3,a3,a7
    sw	a3,0(a4)
    lw	t3,40(a5)
    sh	a0,56(a5)
    ttstallwait	32,6
    lui	a7,0x67110
    lw	a3,48(a5)
    addi	a7,a7,1032 # 67110408 <__device_print_strings_info_end+0x60c10408>
    lw	t4,36(a5)
    add	a3,t3,a3
    sw	a7,0(a4)
    sw	a3,48(a5)
    bltu	a3,t4,7104 <.L25>
    lw	a7,32(a5)
    sub	a3,a3,a7
    sw	a3,48(a5)
    lhu	a7,24(a5)
    lui	t4,0x45000
    addi	a7,a7,1
    zext.h	a7,a7
    addi	t4,t4,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a3,a7,0x8
    add	a3,a3,t4
    sh	a7,24(a5)
    sw	a3,0(a4)
    lw	a3,8(a5)
    ttstallwait	32,6
    lui	t4,0x67110
    add	a3,a3,t1
    sw	a3,16(a5)
    addi	t1,t4,8 # 67110008 <__device_print_strings_info_end+0x60c10008>
    lw	t4,4(a5)
    sw	t1,0(a4)
    bltu	a3,t4,7158 <.L26>
    lw	t1,0(a5)
    sub	a3,a3,t1
    sw	a3,16(a5)
    lui	t1,0xffb40
    lw	a3,40(t1) # ffb40028 <__stack_base+0x3f7f8>
    zext.h	a3,a3
    beq	a3,a7,715c <.L27>
    lui	a7,0xffb41
    lw	a3,40(a7) # ffb41028 <__stack_base+0x407f8>
    zext.h	a3,a3
    beq	a3,a0,716c <.L28>
    lhu	a7,120(a5)
    lui	a0,0xffb43
    lw	a3,40(a0) # ffb43028 <__stack_base+0x427f8>
    zext.h	a3,a3
    beq	a3,a7,7180 <.L29>
    lhu	a7,184(a5)
    lui	a0,0xffb45
    lw	a3,40(a0) # ffb45028 <__stack_base+0x447f8>
    zext.h	a3,a3
    beq	a3,a7,7194 <.L30>
    lw	a7,104(a5)
    lui	a0,0xffe80
    lw	a3,52(a0) # ffe80034 <__instrn_buffer+0x40034>
    zext.b	a3,a3
    bnez	a3,71a8 <.L31>
    ttsetadcxy	3,0,0,0,0,11
    ttsetadczw	3,0,0,0,0,15
    li	t1,512
    sw	t1,228(a2)
    sw	t1,236(a2)
    ttatgetm	0
    lui	t1,0xb3ff0
    sw	t1,0(a4)
    lui	t1,0xb47f0
    sw	t1,0(a4)
    lui	t1,0xb3070
    addi	t1,t1,1 # b3070001 <__device_print_strings_info_end+0xacb70001>
    sw	t1,0(a4)
    lui	t1,0xb4800
    addi	t1,t1,1 # b4800001 <__device_print_strings_info_end+0xae300001>
    sw	t1,0(a4)
    lui	t1,0xb5010
    addi	t1,t1,1 # b5010001 <__device_print_strings_info_end+0xaeb10001>
    sw	t1,0(a4)
    lui	t1,0xb5400
    addi	t4,t1,71 # b5400047 <__device_print_strings_info_end+0xaef00047>
    sw	t4,0(a4)
    addi	t1,t1,119
    sw	t1,0(a4)
    ttatrelm	0
    li	t1,21
    lui	t4,0x40
    sw	t1,256(a2)
    addi	t4,t4,1 # 40001 <.LASF492+0x3730c>
    lui	t1,0x1000
    sw	t4,260(a2)
    addi	t5,t1,21 # 1000015 <.LASF492+0xff7320>
    sw	t5,448(a2)
    sw	t4,452(a2)
    li	t5,37
    lui	t4,0xf0
    sw	t5,288(a2)
    addi	t4,t4,15 # f000f <.LASF492+0xe731a>
    sw	t4,292(a2)
    sw	t5,480(a2)
    lui	t5,0x400
    sw	t4,484(a2)
    addi	t5,t5,64 # 400040 <.LASF492+0x3f734b>
    sw	t5,336(a2)
    addi	t0,t1,256
    sw	t0,344(a2)
    lui	t4,0xffe00
    lui	t6,0x800
    sw	t0,160(t4) # ffe000a0 <__stack_base+0x2ff870>
    addi	t6,t6,128 # 800080 <.LASF492+0x7f738b>
    sw	t6,164(t4)
    lui	t6,0x200
    sw	t5,168(t4)
    addi	t6,t6,32 # 200020 <.LASF492+0x1f732b>
    lui	t5,0x100
    sw	t6,172(t4)
    addi	t5,t5,16 # 100010 <.LASF492+0xf731b>
    sw	t5,176(t4)
    sw	zero,12(sp)
    lw	t4,176(t4)
    sw	t4,12(sp)
    ttsetc16	5,4
    li	t4,256
    sw	t4,200(a2)
    sw	zero,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,0
    lui	t4,0x45000
    addi	t1,t1,-256
    slli	t3,t3,0x8
    and	t3,t3,t1
    slli	a2,a7,0x8
    addi	a7,t4,72 # 45000048 <__device_print_strings_info_end+0x3eb00048>
    and	a2,a2,t1
    add	t3,t3,a7
    addi	t4,t4,74
    sw	t3,0(a4)
    add	a2,a2,t4
    lui	t5,0xb4010
    sw	a2,0(a4)
    addi	t5,t5,72 # b4010048 <__device_print_strings_info_end+0xadb10048>
    sw	t5,0(a4)
    ttsetadcxx	3,255,0
    addi	a0,a0,8
    mv	a2,a3
    sw	a2,0(a0)
    lw	a2,0(a0)
    and	zero,zero,a2
    lui	a2,0xffb80
    li	t4,2
    sw	t4,0(a2) # ffb80000 <__stack_base+0x7f7d0>
    sw	t4,4(a2)
    lui	t1,0x2000
    sw	t1,8(a2)
    sw	t1,12(a2)
    lui	t3,0x42008
    sw	t1,16(a2)
    addi	t3,t3,193 # 420080c1 <__device_print_strings_info_end+0x3bb080c1>
    lui	a7,0x42808
    sw	t3,20(a2)
    addi	a7,a7,193 # 428080c1 <__device_print_strings_info_end+0x3c3080c1>
    sw	a7,24(a2)
    sw	a7,28(a2)
    sw	a7,32(a2)
    sw	t5,0(a4)
    ttsetadcxx	3,255,0
    sw	a3,0(a0)
    lw	a3,0(a0)
    and	zero,zero,a3
    sw	t4,0(a2)
    sw	t4,4(a2)
    sw	t1,8(a2)
    sw	t1,12(a2)
    sw	t1,16(a2)
    sw	t3,20(a2)
    sw	a7,24(a2)
    lw	t1,48(a5)
    lw	a3,112(a5)
    sw	a7,28(a2)
    sw	a7,32(a2)
    addi	t1,t1,-1 # 1ffffff <.LASF492+0x1ff730a>
    addi	a7,a3,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a3,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a0,0xffef0
    beqz	a3,73ac <.L32>
    addi	a0,a0,896 # ffef0380 <__instrn_buffer+0xb0380>
    lui	a2,0xffe80
    lw	a3,52(a2) # ffe80034 <__instrn_buffer+0x40034>
    andi	a3,a3,254
    bnez	a3,73b0 <.L33>
    lw	a3,48(gp) # ffb00820 <unp_cfg_context>
    bnez	a3,7644 <.L34>
    sw	t1,304(a0)
    sw	a7,496(a0)
    sw	zero,52(a2)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    li	a3,1
    sw	a3,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,257
    lui	a3,0xb4010
    addi	a3,a3,72 # b4010048 <__device_print_strings_info_end+0xadb10048>
    sw	a3,0(a4)
    ttsetadcxx	3,255,0
    lui	a2,0xffe80
    li	a3,0
    addi	a2,a2,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a3,0(a2)
    lw	a3,0(a2)
    and	zero,zero,a3
    lui	a3,0xffb80
    li	a2,2
    sw	a2,0(a3) # ffb80000 <__stack_base+0x7f7d0>
    sw	a2,4(a3)
    lui	a2,0x2000
    sw	a2,8(a3)
    sw	a2,12(a3)
    sw	a2,16(a3)
    lui	a2,0x42008
    addi	a2,a2,193 # 420080c1 <__device_print_strings_info_end+0x3bb080c1>
    sw	a2,20(a3)
    lui	a2,0x42808
    addi	a2,a2,193 # 428080c1 <__device_print_strings_info_end+0x3c3080c1>
    lw	a0,16(a5)
    lw	a7,176(a5)
    sw	a2,24(a3)
    sw	a2,28(a3)
    addi	t1,a0,-1
    addi	a7,a7,-1
    sw	a2,32(a3)
    ttsetadczw	3,0,0,0,0,15
    lw	a3,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a6,0xffef0
    beqz	a3,7474 <.L37>
    addi	a6,a6,896 # ffef0380 <__instrn_buffer+0xb0380>
    lui	a2,0xffe80
    lw	a3,52(a2) # ffe80034 <__instrn_buffer+0x40034>
    andi	a3,a3,254
    bnez	a3,7478 <.L38>
    lw	a3,48(gp) # ffb00820 <unp_cfg_context>
    bnez	a3,7614 <.L39>
    sw	t1,304(a6)
    sw	a7,496(a6)
    sw	zero,52(a2)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    li	a3,1
    sw	a3,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,257
    lhu	a3,184(a5)
    lui	a1,0x45000
    addi	a3,a3,1
    zext.h	a3,a3
    addi	a1,a1,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a2,a3,0x8
    sh	a3,184(a5)
    add	a2,a2,a1
    sw	a2,0(a4)
    lw	a3,168(a5)
    ttstallwait	32,6
    lw	a1,176(a5)
    lui	a2,0x67111
    add	a3,a3,a1
    addi	a2,a2,1032 # 67111408 <__device_print_strings_info_end+0x60c11408>
    lw	a1,164(a5)
    sw	a3,176(a5)
    sw	a2,0(a4)
    bltu	a3,a1,7508 <.L42>
    lw	a2,160(a5)
    sub	a3,a3,a2
    sw	a3,176(a5)
    lhu	a3,120(a5)
    lui	a1,0x45000
    addi	a3,a3,1
    zext.h	a3,a3
    addi	a1,a1,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a2,a3,0x8
    sh	a3,120(a5)
    add	a2,a2,a1
    sw	a2,0(a4)
    lw	a3,104(a5)
    ttstallwait	32,6
    lw	a1,112(a5)
    lui	a2,0x67111
    add	a3,a3,a1
    addi	a2,a2,-1016 # 67110c08 <__device_print_strings_info_end+0x60c10c08>
    lw	a1,100(a5)
    sw	a3,112(a5)
    sw	a2,0(a4)
    bltu	a3,a1,7560 <.L43>
    lw	a2,96(a5)
    sub	a3,a3,a2
    sw	a3,112(a5)
    lhu	a3,56(a5)
    lui	a1,0x45000
    addi	a3,a3,1
    zext.h	a3,a3
    addi	a1,a1,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a2,a3,0x8
    sh	a3,56(a5)
    add	a2,a2,a1
    sw	a2,0(a4)
    lw	a3,40(a5)
    ttstallwait	32,6
    lw	a1,48(a5)
    lui	a2,0x67110
    add	a3,a3,a1
    addi	a2,a2,1032 # 67110408 <__device_print_strings_info_end+0x60c10408>
    lw	a1,36(a5)
    sw	a3,48(a5)
    sw	a2,0(a4)
    bltu	a3,a1,75b8 <.L44>
    lw	a2,32(a5)
    sub	a3,a3,a2
    sw	a3,48(a5)
    lhu	a3,24(a5)
    lui	a1,0x45000
    addi	a3,a3,1
    zext.h	a3,a3
    addi	a1,a1,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a2,a3,0x8
    sh	a3,24(a5)
    add	a2,a2,a1
    sw	a2,0(a4)
    lw	a3,8(a5)
    ttstallwait	32,6
    lui	a2,0x67110
    add	a3,a3,a0
    lw	a1,4(a5)
    addi	a2,a2,8 # 67110008 <__device_print_strings_info_end+0x60c10008>
    sw	a3,16(a5)
    sw	a2,0(a4)
    bltu	a3,a1,760c <.L1>
    lw	a4,0(a5)
    sub	a3,a3,a4
    sw	a3,16(a5)
    addi	sp,sp,16
    ret
    sw	t1,308(a6)
    sw	a7,500(a6)
    sw	zero,52(a2)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    li	a2,1
    sub	a6,a2,a3
    sw	a6,48(gp) # ffb00820 <unp_cfg_context>
    bne	a3,a2,74ac <.L40>
    ttsetc16	41,0
    j	74b0 <.L41>
    sw	t1,308(a0)
    sw	a7,500(a0)
    sw	zero,52(a2)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    li	a2,1
    sub	a0,a2,a3
    sw	a0,48(gp) # ffb00820 <unp_cfg_context>
    bne	a3,a2,73e4 <.L35>
    ttsetc16	41,0
    j	73e8 <.L36>
    sw	t3,308(a2)
    sw	a7,500(a2)
    sw	zero,52(a0)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    li	a0,1
    sub	a7,a0,a3
    sw	a7,48(gp) # ffb00820 <unp_cfg_context>
    bne	a3,a0,6ff8 <.L21>
    ttsetc16	41,0
    j	6ffc <.L22>
    ttsetc16	41,0
    j	6f34 <.L17>
    addi	t1,a0,304
    addi	a0,a0,308
    j	6ee8 <.L13>
    ttsetc16	41,0
    j	6e5c <.L12>
    addi	t1,a0,304
    addi	a0,a0,308
    j	6e10 <.L8>
