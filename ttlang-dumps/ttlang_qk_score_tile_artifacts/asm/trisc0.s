    addi	sp,sp,-16
    sw	ra,12(sp)
    lui	a5,0xffb01
    lui	a4,0xffb01
    addi	a5,a5,-2000 # ffb00830 <__stack_base>
    addi	a4,a4,-2012 # ffb00824 <__ldm_bss_end>
    bltu	a4,a5,6aa4 <.L72>
    sw	zero,-4(a5)
    sw	zero,-8(a5)
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a5,a5,16
    bgeu	a4,a5,6a8c <.L73>
    addi	a3,a5,-8
    bltu	a4,a3,6b70 <.L84>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,6ac0 <.L75>
    sw	zero,-8(a5)
    auipc	a4,0x1
    addi	a4,a4,-660 # 782c <__kernel_data_lma>
    addi	a5,gp,48 # ffb00820 <unp_cfg_context>
    beq	a4,a5,6b2c <.L77>
    addi	a2,gp,48 # ffb00820 <unp_cfg_context>
    sub	a2,a2,a5
    li	a1,8
    srai	a3,a2,0x2
    bge	a1,a2,6b10 <.L78>
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
    blt	a6,a3,6ae8 <.L79>
    blez	a3,6b2c <.L77>
    lw	a1,0(a4)
    li	a2,2
    sw	a1,0(a5)
    bne	a3,a2,6b2c <.L77>
    lw	a4,4(a4)
    sw	a4,4(a5)
    lui	a5,0xffb12
    sw	zero,104(a5) # ffb12068 <__stack_base+0x11838>
    lw	a4,1312(zero) # 520 <.LLRL902+0x3>
    li	a3,128
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    addi	a4,a4,96
    beq	a5,a3,6b58 <.L81>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,6b4c <.L82>
    ttzerosrc	0,0,1,3
    jal	6b78 <_Z11kernel_mainv>
    lw	ra,12(sp)
    li	a0,0
    addi	sp,sp,16
    ret
    mv	a5,a3
    j	6ab4 <.L74>
    lui	a4,0xffb00
    addi	a4,a4,32 # ffb00020 <cb_interface>
    lhu	a1,24(a4)
    addi	sp,sp,-16
    lui	a2,0xffb40
    li	a3,1
    lw	a5,40(a2) # ffb40028 <__stack_base+0x3f7f8>
    sub	a5,a5,a1
    zext.h	a5,a5
    bgeu	a3,a5,6b90 <.L2>
    lhu	a1,56(a4)
    lui	a2,0xffb41
    li	a3,1
    lw	a5,40(a2) # ffb41028 <__stack_base+0x407f8>
    sub	a5,a5,a1
    zext.h	a5,a5
    bgeu	a3,a5,6bac <.L3>
    lhu	a2,88(a4)
    lui	a3,0xffb42
    lw	a5,40(a3) # ffb42028 <__stack_base+0x417f8>
    zext.h	a5,a5
    beq	a2,a5,6bc4 <.L4>
    lw	a1,8(a4)
    lw	a2,40(a4)
    lui	a3,0xffe80
    lw	a5,52(a3) # ffe80034 <__instrn_buffer+0x40034>
    zext.b	a5,a5
    bnez	a5,6bdc <.L5>
    ttsetadcxy	3,0,0,0,0,11
    ttsetadczw	3,0,0,0,0,15
    lw	a3,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a5,0xffef0
    beqz	a3,6c00 <.L6>
    addi	a5,a5,896 # ffef0380 <__instrn_buffer+0xb0380>
    li	a3,512
    sw	a3,228(a5)
    sw	a3,236(a5)
    ttatgetm	0
    lui	a3,0xffe40
    mv	a3,a3
    lui	a0,0xb3ff0
    sw	a0,0(a3) # ffe40000 <__instrn_buffer>
    lui	a0,0xb47f0
    sw	a0,0(a3)
    lui	a0,0xb3070
    addi	a0,a0,1 # b3070001 <__device_print_strings_info_end+0xacb70001>
    sw	a0,0(a3)
    lui	a0,0xb4800
    addi	a0,a0,1 # b4800001 <__device_print_strings_info_end+0xae300001>
    sw	a0,0(a3)
    lui	a0,0xb5010
    addi	a0,a0,1 # b5010001 <__device_print_strings_info_end+0xaeb10001>
    sw	a0,0(a3)
    lui	a0,0xb5400
    addi	a7,a0,71 # b5400047 <__device_print_strings_info_end+0xaef00047>
    sw	a7,0(a3)
    addi	a0,a0,119
    sw	a0,0(a3)
    ttatrelm	0
    li	a0,21
    sw	a0,256(a5)
    lui	a0,0x40
    addi	a0,a0,1 # 40001 <.LASF492+0x371cd>
    lui	a7,0x1000
    sw	a0,260(a5)
    addi	t1,a7,21 # 1000015 <.LASF492+0xff71e1>
    sw	t1,448(a5)
    sw	a0,452(a5)
    li	t1,37
    lui	a0,0xf0
    sw	t1,288(a5)
    addi	a0,a0,15 # f000f <.LASF492+0xe71db>
    sw	a0,292(a5)
    sw	t1,480(a5)
    lui	t1,0x400
    sw	a0,484(a5)
    addi	t1,t1,64 # 400040 <.LASF492+0x3f720c>
    sw	t1,336(a5)
    addi	t3,a7,256
    sw	t3,344(a5)
    lui	a0,0xffe00
    sw	t3,160(a0) # ffe000a0 <__stack_base+0x2ff870>
    lui	t3,0x800
    addi	t3,t3,128 # 800080 <.LASF492+0x7f724c>
    sw	t3,164(a0)
    sw	t1,168(a0)
    lui	t1,0x200
    addi	t1,t1,32 # 200020 <.LASF492+0x1f71ec>
    sw	t1,172(a0)
    lui	t1,0x100
    addi	t1,t1,16 # 100010 <.LASF492+0xf71dc>
    sw	t1,176(a0)
    sw	zero,0(sp)
    lw	a0,176(a0)
    sw	a0,0(sp)
    ttsetc16	5,4
    li	a0,256
    sw	a0,200(a5)
    sw	zero,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,0
    lui	t1,0x45000
    addi	a7,a7,-256
    slli	a1,a1,0x8
    and	a1,a1,a7
    slli	a5,a2,0x8
    addi	a2,t1,72 # 45000048 <__device_print_strings_info_end+0x3eb00048>
    and	a5,a5,a7
    add	a2,a1,a2
    addi	t1,t1,74
    sw	a2,0(a3)
    add	a5,a5,t1
    lui	t5,0xb4010
    sw	a5,0(a3)
    addi	t5,t5,72 # b4010048 <__device_print_strings_info_end+0xadb10048>
    sw	t5,0(a3)
    ttsetadcxx	3,255,0
    li	a7,0
    lui	t4,0xffe80
    addi	t4,t4,8 # ffe80008 <__instrn_buffer+0x40008>
    mv	a5,a7
    sw	a5,0(t4)
    lw	a5,0(t4)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	t3,2
    sw	t3,0(a5) # ffb80000 <__stack_base+0x7f7d0>
    sw	t3,4(a5)
    lui	a1,0x2000
    sw	a1,8(a5)
    sw	a1,12(a5)
    lui	t1,0x42008
    sw	a1,16(a5)
    addi	t1,t1,193 # 420080c1 <__device_print_strings_info_end+0x3bb080c1>
    lui	a2,0x42808
    sw	t1,20(a5)
    addi	a2,a2,193 # 428080c1 <__device_print_strings_info_end+0x3c3080c1>
    sw	a2,24(a5)
    sw	a2,28(a5)
    sw	a2,32(a5)
    sw	t5,0(a3)
    ttsetadcxx	3,255,0
    sw	a7,0(t4)
    lw	a7,0(t4)
    and	zero,zero,a7
    sw	t3,0(a5)
    sw	t3,4(a5)
    sw	a1,8(a5)
    sw	a1,12(a5)
    sw	a1,16(a5)
    sw	t1,20(a5)
    sw	a2,24(a5)
    lw	t1,16(a4)
    lw	a7,48(a4)
    sw	a2,28(a5)
    sw	a2,32(a5)
    addi	t1,t1,-1
    addi	a7,a7,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a1,0xffef0
    beqz	a5,6e00 <.L7>
    addi	a1,a1,896 # ffef0380 <__instrn_buffer+0xb0380>
    lui	a2,0xffe80
    lw	a5,52(a2) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,6e04 <.L8>
    lw	t3,48(gp) # ffb00820 <unp_cfg_context>
    bnez	t3,77fc <.L9>
    sw	t1,304(a1)
    sw	a7,496(a1)
    sw	zero,52(a2)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    ttsetc16	41,257
    lw	a2,8(a4)
    lw	a5,40(a4)
    add	t1,t1,a2
    add	a7,a7,a5
    ttsetadczw	3,0,0,0,0,15
    lui	a5,0xffe80
    lw	a2,52(a5) # ffe80034 <__instrn_buffer+0x40034>
    andi	a2,a2,254
    bnez	a2,6e4c <.L12>
    li	t4,1
    bne	t3,t4,77d8 <.L13>
    sw	t1,304(a1)
    sw	a7,496(a1)
    sw	zero,52(a5)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    sw	t3,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,257
    lhu	t3,152(a4)
    lui	t1,0xffb44
    li	a7,1
    lw	a5,40(t1) # ffb44028 <__stack_base+0x437f8>
    sub	a5,a5,t3
    zext.h	a5,a5
    bgeu	a7,a5,6e8c <.L16>
    lw	t1,168(a4)
    lui	a7,0xffe80
    lw	a5,52(a7) # ffe80034 <__instrn_buffer+0x40034>
    zext.b	a5,a5
    bnez	a5,6ea4 <.L17>
    ttsetadcxy	3,0,0,0,0,11
    ttsetadczw	3,0,0,0,0,15
    li	t3,512
    sw	t3,228(a1)
    sw	t3,236(a1)
    ttatgetm	0
    lui	t3,0xb3ff0
    sw	t3,0(a3)
    lui	t3,0xb47f0
    sw	t3,0(a3)
    lui	t3,0xb3070
    addi	t3,t3,1 # b3070001 <__device_print_strings_info_end+0xacb70001>
    sw	t3,0(a3)
    lui	t3,0xb4800
    addi	t3,t3,1 # b4800001 <__device_print_strings_info_end+0xae300001>
    sw	t3,0(a3)
    lui	t3,0xb5010
    addi	t3,t3,1 # b5010001 <__device_print_strings_info_end+0xaeb10001>
    sw	t3,0(a3)
    lui	t3,0xb5400
    addi	t4,t3,71 # b5400047 <__device_print_strings_info_end+0xaef00047>
    sw	t4,0(a3)
    addi	t3,t3,119
    sw	t3,0(a3)
    ttatrelm	0
    li	t3,21
    sw	t3,256(a1)
    lui	t3,0x40
    addi	t3,t3,1 # 40001 <.LASF492+0x371cd>
    lui	t4,0x1000
    sw	t3,260(a1)
    addi	t5,t4,21 # 1000015 <.LASF492+0xff71e1>
    sw	t5,448(a1)
    sw	t3,452(a1)
    li	t5,37
    lui	t3,0xf0
    sw	t5,288(a1)
    addi	t3,t3,15 # f000f <.LASF492+0xe71db>
    sw	t3,292(a1)
    sw	t5,480(a1)
    lui	t5,0x400
    sw	t3,484(a1)
    addi	t5,t5,64 # 400040 <.LASF492+0x3f720c>
    sw	t5,336(a1)
    addi	t0,t4,256
    sw	t0,344(a1)
    lui	t3,0xffe00
    lui	t6,0x800
    sw	t0,160(t3) # ffe000a0 <__stack_base+0x2ff870>
    addi	t6,t6,128 # 800080 <.LASF492+0x7f724c>
    sw	t6,164(t3)
    lui	t6,0x200
    sw	t5,168(t3)
    addi	t6,t6,32 # 200020 <.LASF492+0x1f71ec>
    lui	t5,0x100
    sw	t6,172(t3)
    addi	t5,t5,16 # 100010 <.LASF492+0xf71dc>
    sw	t5,176(t3)
    sw	zero,4(sp)
    lw	t3,176(t3)
    sw	t3,4(sp)
    ttsetc16	5,4
    li	t3,256
    sw	zero,48(gp) # ffb00820 <unp_cfg_context>
    sw	t3,200(a1)
    ttsetc16	41,0
    lui	t3,0x45000
    slli	a1,t1,0x8
    addi	t4,t4,-256
    and	a1,a1,t4
    addi	t1,t3,72 # 45000048 <__device_print_strings_info_end+0x3eb00048>
    add	t1,a1,t1
    addi	t3,t3,74
    sw	t1,0(a3)
    add	a1,a1,t3
    sw	a1,0(a3)
    lui	a1,0xb4010
    addi	a1,a1,72 # b4010048 <__device_print_strings_info_end+0xadb10048>
    sw	a1,0(a3)
    ttsetadcxx	1,255,0
    addi	a7,a7,8
    sw	a5,0(a7)
    lw	a5,0(a7)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a1,4
    sw	a1,0(a5) # ffb80000 <__stack_base+0x7f7d0>
    li	a1,1
    sw	a1,4(a5)
    lui	a1,0x42008
    addi	a1,a1,193 # 420080c1 <__device_print_strings_info_end+0x3bb080c1>
    sw	a1,8(a5)
    lui	a7,0x2000
    sw	a7,12(a5)
    lui	a1,0x43800
    sw	a7,16(a5)
    addi	a1,a1,257 # 43800101 <__device_print_strings_info_end+0x3d300101>
    sw	a1,20(a5)
    sw	a7,24(a5)
    lhu	a7,184(a4)
    sw	a1,28(a5)
    sw	a1,32(a5)
    lui	a1,0xffb45
    lw	a5,40(a1) # ffb45028 <__stack_base+0x447f8>
    zext.h	a5,a5
    beq	a5,a7,704c <.L18>
    lw	a7,136(a4)
    lui	a1,0xffe80
    lw	a5,52(a1) # ffe80034 <__instrn_buffer+0x40034>
    zext.b	a5,a5
    bnez	a5,7060 <.L19>
    ttsetadcxy	3,0,0,0,0,11
    ttsetadczw	3,0,0,0,0,15
    lw	a1,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a5,0xffef0
    beqz	a1,7084 <.L20>
    addi	a5,a5,896 # ffef0380 <__instrn_buffer+0xb0380>
    li	a1,512
    sw	a1,228(a5)
    sw	a1,236(a5)
    ttatgetm	0
    lui	a1,0xb3ff0
    sw	a1,0(a3)
    lui	a1,0xb47f0
    sw	a1,0(a3)
    lui	a1,0xb3070
    addi	a1,a1,1 # b3070001 <__device_print_strings_info_end+0xacb70001>
    sw	a1,0(a3)
    lui	a1,0xb4800
    addi	a1,a1,1 # b4800001 <__device_print_strings_info_end+0xae300001>
    sw	a1,0(a3)
    lui	a1,0xb5010
    addi	a1,a1,1 # b5010001 <__device_print_strings_info_end+0xaeb10001>
    sw	a1,0(a3)
    lui	a1,0xb5400
    addi	t1,a1,71 # b5400047 <__device_print_strings_info_end+0xaef00047>
    sw	t1,0(a3)
    addi	a1,a1,119
    sw	a1,0(a3)
    ttatrelm	0
    li	a1,21
    sw	a1,256(a5)
    lui	a1,0x40
    addi	a1,a1,1 # 40001 <.LASF492+0x371cd>
    lui	t1,0x1000
    sw	a1,260(a5)
    addi	t3,t1,21 # 1000015 <.LASF492+0xff71e1>
    sw	t3,448(a5)
    sw	a1,452(a5)
    li	t3,37
    lui	a1,0xf0
    sw	t3,288(a5)
    addi	a1,a1,15 # f000f <.LASF492+0xe71db>
    sw	a1,292(a5)
    sw	t3,480(a5)
    lui	t3,0x400
    sw	a1,484(a5)
    addi	t3,t3,64 # 400040 <.LASF492+0x3f720c>
    sw	t3,336(a5)
    addi	t4,t1,256
    sw	t4,344(a5)
    lui	a1,0xffe00
    sw	t4,160(a1) # ffe000a0 <__stack_base+0x2ff870>
    lui	t4,0x800
    addi	t4,t4,128 # 800080 <.LASF492+0x7f724c>
    sw	t4,164(a1)
    sw	t3,168(a1)
    lui	t3,0x200
    addi	t3,t3,32 # 200020 <.LASF492+0x1f71ec>
    sw	t3,172(a1)
    lui	t3,0x100
    addi	t3,t3,16 # 100010 <.LASF492+0xf71dc>
    sw	t3,176(a1)
    sw	zero,8(sp)
    lw	a1,176(a1)
    sw	a1,8(sp)
    ttsetc16	5,4
    li	a1,256
    sw	a1,200(a5)
    sw	zero,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,0
    lui	a1,0x45000
    slli	a5,a7,0x8
    addi	t1,t1,-256
    and	a5,a5,t1
    addi	a7,a1,72 # 45000048 <__device_print_strings_info_end+0x3eb00048>
    add	a7,a5,a7
    addi	a1,a1,74
    sw	a7,0(a3)
    add	a5,a5,a1
    lui	t4,0xb4010
    sw	a5,0(a3)
    addi	a5,t4,72 # b4010048 <__device_print_strings_info_end+0xadb10048>
    sw	a5,0(a3)
    ttsetadcxx	1,255,0
    li	a7,0
    lui	t3,0xffe80
    addi	t3,t3,8 # ffe80008 <__instrn_buffer+0x40008>
    mv	a5,a7
    sw	a5,0(t3)
    lw	a5,0(t3)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	t5,4
    sw	t5,0(a5) # ffb80000 <__stack_base+0x7f7d0>
    li	t6,1
    lui	a1,0x42008
    sw	t6,4(a5)
    addi	a1,a1,193 # 420080c1 <__device_print_strings_info_end+0x3bb080c1>
    sw	a1,8(a5)
    lui	a1,0x2000
    sw	a1,12(a5)
    lui	t1,0x43800
    sw	a1,16(a5)
    addi	t1,t1,257 # 43800101 <__device_print_strings_info_end+0x3d300101>
    sw	t1,20(a5)
    sw	a1,24(a5)
    sw	t1,28(a5)
    addi	t4,t4,328
    sw	t1,32(a5)
    sw	t4,0(a3)
    ttsetadcxx	1,255,0
    ttsetadcxx	2,15,0
    ttreplay	0,2,0,1
    ttunpacr	0,1,0,0,0,1,1,0,0,0,0,0,1
    ttunpacr	1,1,0,0,0,1,1,0,0,0,0,0,1
    sw	a7,0(t3)
    lw	a7,0(t3)
    and	zero,zero,a7
    sw	t6,0(a5)
    sw	t5,4(a5)
    sw	a1,8(a5)
    sw	a1,12(a5)
    lui	a7,0x4000
    sw	a1,16(a5)
    addi	a7,a7,32 # 4000020 <.LASF492+0x3ff71ec>
    sw	a7,20(a5)
    sw	a1,24(a5)
    sw	a7,28(a5)
    sw	a7,32(a5)
    lw	t4,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a5,0xffef0
    addi	t5,a5,896 # ffef0380 <__instrn_buffer+0xb0380>
    bnez	t4,7284 <.L22>
    mv	t5,a5
    lw	t3,48(gp) # ffb00820 <unp_cfg_context>
    lui	a1,0xffe80
    li	t0,1
    li	t6,2
    lw	a7,144(a4)
    lw	a5,136(a4)
    lw	t1,176(a4)
    mul	a5,a2,a5
    addi	a7,a7,-1
    add	a7,a7,a5
    addi	t1,t1,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a5,52(a1) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,72b4 <.L23>
    bnez	t3,7780 <.L24>
    sw	a7,304(t5)
    sw	t1,496(t5)
    sw	zero,52(a1)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    li	t3,1
    ttsetc16	41,257
    addi	a5,a2,1
    li	a2,1
    bne	a5,t6,7294 <.L28>
    lhu	a5,184(a4)
    lui	a1,0x45000
    add	a5,a5,a2
    zext.h	a5,a5
    addi	a1,a1,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a2,a5,0x8
    sh	a5,184(a4)
    sw	t3,48(gp) # ffb00820 <unp_cfg_context>
    add	a2,a2,a1
    sw	a2,0(a3)
    lw	a5,168(a4)
    ttstallwait	32,6
    lw	a1,176(a4)
    lui	a2,0x67111
    add	a5,a5,a1
    addi	a2,a2,1032 # 67111408 <__device_print_strings_info_end+0x60c11408>
    lw	a1,164(a4)
    sw	a5,176(a4)
    sw	a2,0(a3)
    bltu	a5,a1,734c <.L29>
    lw	a2,160(a4)
    sub	a5,a5,a2
    sw	a5,176(a4)
    lhu	a5,152(a4)
    lui	a1,0x45000
    addi	a5,a5,2
    zext.h	a5,a5
    addi	a1,a1,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a2,a5,0x8
    sh	a5,152(a4)
    add	a2,a2,a1
    sw	a2,0(a3)
    lw	a5,136(a4)
    ttstallwait	32,6
    lui	a2,0x67111
    lw	a7,144(a4)
    addi	a2,a2,8 # 67111008 <__device_print_strings_info_end+0x60c11008>
    lw	a1,132(a4)
    sh1add	a5,a5,a7
    sw	a2,0(a3)
    sw	a5,144(a4)
    bltu	a5,a1,73a4 <.L30>
    lw	a2,128(a4)
    sub	a5,a5,a2
    sw	a5,144(a4)
    lhu	a1,216(a4)
    lui	a2,0xffb46
    lw	a5,40(a2) # ffb46028 <__stack_base+0x457f8>
    zext.h	a5,a5
    beq	a5,a1,73ac <.L31>
    lw	a7,200(a4)
    lw	a1,72(a4)
    lui	a2,0xffe80
    lw	a5,52(a2) # ffe80034 <__instrn_buffer+0x40034>
    zext.b	a5,a5
    bnez	a5,73c4 <.L32>
    ttsetadcxy	3,0,0,0,0,11
    ttsetadczw	3,0,0,0,0,15
    lui	a5,0xffef0
    beqz	t4,73e4 <.L33>
    addi	a5,a5,896 # ffef0380 <__instrn_buffer+0xb0380>
    li	a2,512
    sw	a2,228(a5)
    sw	a2,236(a5)
    ttatgetm	0
    lui	a2,0xb3ff0
    sw	a2,0(a3)
    lui	a2,0xb47f0
    sw	a2,0(a3)
    lui	a2,0xb3070
    addi	a2,a2,1 # b3070001 <__device_print_strings_info_end+0xacb70001>
    sw	a2,0(a3)
    lui	a2,0xb4800
    addi	a2,a2,1 # b4800001 <__device_print_strings_info_end+0xae300001>
    sw	a2,0(a3)
    lui	a2,0xb5010
    addi	a2,a2,1 # b5010001 <__device_print_strings_info_end+0xaeb10001>
    sw	a2,0(a3)
    lui	a2,0xb5400
    addi	t1,a2,71 # b5400047 <__device_print_strings_info_end+0xaef00047>
    sw	t1,0(a3)
    addi	a2,a2,119
    sw	a2,0(a3)
    ttatrelm	0
    li	a2,21
    sw	a2,256(a5)
    lui	a2,0x40
    addi	a2,a2,1 # 40001 <.LASF492+0x371cd>
    lui	t1,0x1000
    sw	a2,260(a5)
    addi	t3,t1,21 # 1000015 <.LASF492+0xff71e1>
    sw	t3,448(a5)
    sw	a2,452(a5)
    li	t3,37
    lui	a2,0xf0
    sw	t3,288(a5)
    addi	a2,a2,15 # f000f <.LASF492+0xe71db>
    sw	a2,292(a5)
    sw	t3,480(a5)
    lui	t3,0x400
    sw	a2,484(a5)
    addi	t3,t3,64 # 400040 <.LASF492+0x3f720c>
    sw	t3,336(a5)
    addi	t4,t1,256
    sw	t4,344(a5)
    lui	a2,0xffe00
    sw	t4,160(a2) # ffe000a0 <__stack_base+0x2ff870>
    lui	t4,0x800
    addi	t4,t4,128 # 800080 <.LASF492+0x7f724c>
    sw	t4,164(a2)
    sw	t3,168(a2)
    lui	t3,0x200
    addi	t3,t3,32 # 200020 <.LASF492+0x1f71ec>
    sw	t3,172(a2)
    lui	t3,0x100
    addi	t3,t3,16 # 100010 <.LASF492+0xf71dc>
    sw	t3,176(a2)
    sw	zero,12(sp)
    lw	a2,176(a2)
    sw	a2,12(sp)
    ttsetc16	5,4
    li	a2,256
    sw	a2,200(a5)
    sw	zero,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,0
    lui	t3,0x45000
    addi	t1,t1,-256
    slli	a2,a7,0x8
    and	a2,a2,t1
    slli	a5,a1,0x8
    addi	a1,t3,72 # 45000048 <__device_print_strings_info_end+0x3eb00048>
    and	a5,a5,t1
    add	a2,a2,a1
    addi	t3,t3,74
    sw	a2,0(a3)
    add	a5,a5,t3
    lui	t5,0xb4010
    sw	a5,0(a3)
    addi	t5,t5,72 # b4010048 <__device_print_strings_info_end+0xadb10048>
    sw	t5,0(a3)
    ttsetadcxx	3,255,0
    li	a7,0
    lui	t4,0xffe80
    addi	t4,t4,8 # ffe80008 <__instrn_buffer+0x40008>
    mv	a5,a7
    sw	a5,0(t4)
    lw	a5,0(t4)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	t3,2
    sw	t3,0(a5) # ffb80000 <__stack_base+0x7f7d0>
    sw	t3,4(a5)
    lui	a1,0x2000
    sw	a1,8(a5)
    sw	a1,12(a5)
    lui	t1,0x42008
    sw	a1,16(a5)
    addi	t1,t1,193 # 420080c1 <__device_print_strings_info_end+0x3bb080c1>
    lui	a2,0x42808
    sw	t1,20(a5)
    addi	a2,a2,193 # 428080c1 <__device_print_strings_info_end+0x3c3080c1>
    sw	a2,24(a5)
    sw	a2,28(a5)
    sw	a2,32(a5)
    sw	t5,0(a3)
    ttsetadcxx	3,255,0
    sw	a7,0(t4)
    lw	a7,0(t4)
    and	zero,zero,a7
    sw	t3,0(a5)
    sw	t3,4(a5)
    sw	a1,8(a5)
    sw	a1,12(a5)
    sw	a1,16(a5)
    sw	t1,20(a5)
    sw	a2,24(a5)
    lw	a7,208(a4)
    lw	a1,80(a4)
    sw	a2,28(a5)
    addi	t1,a7,-1
    sw	a2,32(a5)
    addi	a7,a1,-1 # 1ffffff <.LASF492+0x1ff71cb>
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a1,0xffef0
    beqz	a5,75dc <.L34>
    addi	a1,a1,896 # ffef0380 <__instrn_buffer+0xb0380>
    lui	a2,0xffe80
    lw	a5,52(a2) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,75e0 <.L35>
    lw	a5,48(gp) # ffb00820 <unp_cfg_context>
    bnez	a5,77a8 <.L36>
    sw	t1,304(a1)
    sw	a7,496(a1)
    sw	zero,52(a2)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    li	a5,1
    sw	a5,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,257
    lhu	a5,216(a4)
    lui	a1,0x45000
    addi	a5,a5,1
    zext.h	a5,a5
    addi	a1,a1,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a2,a5,0x8
    sh	a5,216(a4)
    add	a2,a2,a1
    sw	a2,0(a3)
    lw	a5,200(a4)
    ttstallwait	32,6
    lw	a1,208(a4)
    lui	a2,0x67112
    add	a5,a5,a1
    addi	a2,a2,-2040 # 67111808 <__device_print_strings_info_end+0x60c11808>
    lw	a1,196(a4)
    sw	a5,208(a4)
    sw	a2,0(a3)
    bltu	a5,a1,7670 <.L39>
    lw	a2,192(a4)
    sub	a5,a5,a2
    sw	a5,208(a4)
    lhu	a5,88(a4)
    lui	a1,0x45000
    addi	a5,a5,1
    zext.h	a5,a5
    addi	a1,a1,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a2,a5,0x8
    sh	a5,88(a4)
    add	a2,a2,a1
    sw	a2,0(a3)
    lw	a5,72(a4)
    ttstallwait	32,6
    lw	a1,80(a4)
    lui	a2,0x67111
    add	a5,a5,a1
    addi	a2,a2,-2040 # 67110808 <__device_print_strings_info_end+0x60c10808>
    lw	a1,68(a4)
    sw	a5,80(a4)
    sw	a2,0(a3)
    bltu	a5,a1,76c8 <.L40>
    lw	a2,64(a4)
    sub	a5,a5,a2
    sw	a5,80(a4)
    lhu	a5,56(a4)
    lui	a1,0x45000
    addi	a5,a5,2
    zext.h	a5,a5
    addi	a1,a1,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a2,a5,0x8
    sh	a5,56(a4)
    add	a2,a2,a1
    sw	a2,0(a3)
    lw	a5,40(a4)
    ttstallwait	32,6
    lui	a2,0x67110
    lw	a0,48(a4)
    addi	a2,a2,1032 # 67110408 <__device_print_strings_info_end+0x60c10408>
    lw	a1,36(a4)
    sh1add	a5,a5,a0
    sw	a2,0(a3)
    sw	a5,48(a4)
    bltu	a5,a1,7720 <.L41>
    lw	a2,32(a4)
    sub	a5,a5,a2
    sw	a5,48(a4)
    lhu	a5,24(a4)
    lui	a1,0x45000
    addi	a5,a5,2
    zext.h	a5,a5
    addi	a1,a1,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a2,a5,0x8
    sh	a5,24(a4)
    add	a2,a2,a1
    sw	a2,0(a3)
    lw	a5,8(a4)
    ttstallwait	32,6
    lui	a2,0x67110
    lw	a0,16(a4)
    addi	a2,a2,8 # 67110008 <__device_print_strings_info_end+0x60c10008>
    lw	a1,4(a4)
    sh1add	a5,a5,a0
    sw	a2,0(a3)
    sw	a5,16(a4)
    bltu	a5,a1,7778 <.L1>
    lw	a3,0(a4)
    sub	a5,a5,a3
    sw	a5,16(a4)
    addi	sp,sp,16
    ret
    sw	a7,308(t5)
    sw	t1,500(t5)
    sw	zero,52(a1)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    bne	t3,t0,7824 <.L26>
    ttsetc16	41,0
    li	t3,0
    j	72e4 <.L27>
    sw	t1,308(a1)
    sw	a7,500(a1)
    sw	zero,52(a2)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    li	a2,1
    sub	a1,a2,a5
    sw	a1,48(gp) # ffb00820 <unp_cfg_context>
    bne	a5,a2,7614 <.L37>
    ttsetc16	41,0
    j	7618 <.L38>
    sw	t1,308(a1)
    sw	a7,500(a1)
    sw	zero,52(a5)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    bnez	t3,6e7c <.L14>
    ttsetc16	41,0
    j	6e80 <.L15>
    sw	t1,308(a1)
    sw	a7,500(a1)
    sw	zero,52(a2)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    li	a5,1
    bne	t3,a5,6e30 <.L10>
    ttsetc16	41,0
    j	6e34 <.L11>
    sub	t3,t0,t3
    j	72e0 <.L25>
