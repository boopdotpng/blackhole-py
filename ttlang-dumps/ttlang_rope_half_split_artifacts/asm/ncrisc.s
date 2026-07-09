    addi	sp,sp,-16
    sw	ra,12(sp)
    lui	a5,0xffb01
    lui	a4,0xffb01
    addi	a5,a5,-976 # ffb00c30 <__stack_base>
    addi	a4,a4,-984 # ffb00c28 <__ldm_bss_end>
    bltu	a4,a5,60f4 <.L47>
    sw	zero,-4(a5)
    sw	zero,-8(a5)
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a5,a5,16
    bgeu	a4,a5,60dc <.L48>
    addi	a3,a5,-8
    bltu	a4,a3,61d0 <.L59>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,6110 <.L50>
    sw	zero,-8(a5)
    auipc	a4,0x0
    addi	a4,a4,1380 # 6674 <__kernel_data_lma>
    addi	a5,gp,1072 # ffb00c20 <noc_reads_num_issued>
    beq	a4,a5,617c <.L52>
    addi	a2,gp,1072 # ffb00c20 <noc_reads_num_issued>
    sub	a2,a2,a5
    li	a1,8
    srai	a3,a2,0x2
    bge	a1,a2,6160 <.L53>
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
    blt	a6,a3,6138 <.L54>
    blez	a3,617c <.L52>
    lw	a1,0(a4)
    li	a2,2
    sw	a1,0(a5)
    bne	a3,a2,617c <.L52>
    lw	a4,4(a4)
    sw	a4,4(a5)
    lui	a5,0xffb20
    lw	a3,520(a5) # ffb20208 <__stack_base+0x1f5d8>
    lw	a2,552(a5)
    lw	a2,516(a5)
    lw	a2,512(a5)
    lw	a5,556(a5)
    sw	a3,1072(gp) # ffb00c20 <noc_reads_num_issued>
    lw	a4,1312(zero) # 520 <.LASF1295+0x4>
    li	a3,128
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    addi	a4,a4,96
    beq	a5,a3,61bc <.L56>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,61b0 <.L57>
    jal	61d8 <_Z11kernel_mainv>
    lw	ra,12(sp)
    li	a0,0
    addi	sp,sp,16
    ret
    mv	a5,a3
    j	6104 <.L49>
    lui	a1,0xffb40
    lw	a2,40(a1) # ffb40028 <__stack_base+0x3f3f8>
    lui	a5,0xffb00
    addi	a5,a5,1048 # ffb00418 <cb_interface>
    zext.h	a2,a2
    fence
    lw	a3,32(a1)
    lw	a4,12(a5)
    add	a4,a4,a3
    zext.h	a4,a4
    beq	a4,a2,61ec <.L2>
    lw	a4,-1980(gp) # ffb00034 <crta_l1_base>
    lw	t3,8(a4)
    addi	a1,gp,-1500 # ffb00214 <bank_to_dram_offset>
    addi	a0,gp,-1968 # ffb00040 <dram_bank_to_noc_xy>
    lw	a7,0(a1)
    lhu	a4,0(a0)
    lw	t1,20(a5)
    slli	a2,a4,0x4
    lui	a3,0xffb21
    add	a7,t3,a7
    lw	a4,-1984(a3) # ffb20840 <__stack_base+0x1fc10>
    bnez	a4,622c <.L3>
    sw	t1,-2036(a3)
    sw	a7,-2048(a3)
    sw	zero,-2044(a3)
    srli	a4,a2,0x4
    sw	a4,-2040(a3)
    lui	a4,0x1
    addi	a4,a4,-2048 # 800 <.LASF569+0x5>
    sw	a4,-2016(a3)
    li	a4,1
    sw	a4,-1984(a3)
    addi	a2,gp,1072 # ffb00c20 <noc_reads_num_issued>
    lw	a3,0(a2)
    lui	a7,0xffb20
    add	a3,a3,a4
    sw	a3,0(a2)
    lw	a4,520(a7) # ffb20208 <__stack_base+0x1f5d8>
    bne	a4,a3,6270 <.L4>
    fence
    lui	a7,0xffb40
    lw	t1,20(a5)
    lw	a4,8(a5)
    lw	a3,40(a7) # ffb40028 <__stack_base+0x3f3f8>
    add	a4,a4,t1
    addi	a3,a3,1
    lw	t1,4(a5)
    sw	a4,20(a5)
    sw	a3,40(a7)
    bne	a4,t1,62b0 <.L5>
    lw	a3,0(a5)
    sub	a4,a4,a3
    sw	a4,20(a5)
    lui	t1,0xffb41
    lw	a7,40(t1) # ffb41028 <__stack_base+0x403f8>
    zext.h	a7,a7
    fence
    lw	a3,32(t1)
    lw	a4,44(a5)
    add	a4,a4,a3
    zext.h	a4,a4
    beq	a4,a7,62bc <.L6>
    lw	a3,4(a1)
    lhu	a4,2(a0)
    lw	t1,52(a5)
    add	t3,t3,a3
    slli	a7,a4,0x4
    lui	a3,0xffb21
    lw	a4,-1984(a3) # ffb20840 <__stack_base+0x1fc10>
    bnez	a4,62ec <.L7>
    sw	t1,-2036(a3)
    sw	t3,-2048(a3)
    sw	zero,-2044(a3)
    srli	a4,a7,0x4
    lui	a7,0x1
    sw	a4,-2040(a3)
    addi	a4,a7,-2048 # 800 <.LASF569+0x5>
    sw	a4,-2016(a3)
    li	a4,1
    sw	a4,-1984(a3)
    lw	a3,0(a2)
    lui	a7,0xffb20
    add	a3,a3,a4
    sw	a3,0(a2)
    lw	a4,520(a7) # ffb20208 <__stack_base+0x1f5d8>
    bne	a4,a3,632c <.L8>
    fence
    lui	a7,0xffb41
    lw	t1,52(a5)
    lw	a4,40(a5)
    lw	a3,40(a7) # ffb41028 <__stack_base+0x403f8>
    add	a4,a4,t1
    addi	a3,a3,1
    lw	t1,36(a5)
    sw	a4,52(a5)
    sw	a3,40(a7)
    bne	a4,t1,636c <.L9>
    lw	a3,32(a5)
    sub	a4,a4,a3
    sw	a4,52(a5)
    lui	t1,0xffb42
    lw	a7,40(t1) # ffb42028 <__stack_base+0x413f8>
    zext.h	a7,a7
    fence
    lw	a3,32(t1)
    lw	a4,76(a5)
    add	a4,a4,a3
    zext.h	a4,a4
    beq	a4,a7,6378 <.L10>
    lw	a4,-1980(gp) # ffb00034 <crta_l1_base>
    lw	t1,0(a1)
    lw	t3,0(a4)
    lhu	a4,0(a0)
    lw	t4,84(a5)
    slli	a7,a4,0x4
    lui	a3,0xffb21
    add	t1,t3,t1
    lw	a4,-1984(a3) # ffb20840 <__stack_base+0x1fc10>
    bnez	a4,63b0 <.L11>
    sw	t4,-2036(a3)
    sw	t1,-2048(a3)
    sw	zero,-2044(a3)
    srli	a4,a7,0x4
    lui	a7,0x1
    sw	a4,-2040(a3)
    addi	a4,a7,-2048 # 800 <.LASF569+0x5>
    sw	a4,-2016(a3)
    li	a4,1
    sw	a4,-1984(a3)
    lw	a3,0(a2)
    lui	a7,0xffb20
    add	a3,a3,a4
    sw	a3,0(a2)
    lw	a4,520(a7) # ffb20208 <__stack_base+0x1f5d8>
    bne	a4,a3,63f0 <.L12>
    fence
    lui	a7,0xffb42
    lw	t1,84(a5)
    lw	a4,72(a5)
    lw	a3,40(a7) # ffb42028 <__stack_base+0x413f8>
    add	a4,a4,t1
    addi	a3,a3,1
    lw	t1,68(a5)
    sw	a4,84(a5)
    sw	a3,40(a7)
    bne	a4,t1,6430 <.L13>
    lw	a3,64(a5)
    sub	a4,a4,a3
    sw	a4,84(a5)
    lui	t1,0xffb43
    lw	a7,40(t1) # ffb43028 <__stack_base+0x423f8>
    zext.h	a7,a7
    fence
    lw	a3,32(t1)
    lw	a4,108(a5)
    add	a4,a4,a3
    zext.h	a4,a4
    beq	a7,a4,643c <.L14>
    lw	a3,4(a1)
    lhu	a4,2(a0)
    lw	t1,116(a5)
    add	t3,t3,a3
    slli	a7,a4,0x4
    lui	a3,0xffb21
    lw	a4,-1984(a3) # ffb20840 <__stack_base+0x1fc10>
    bnez	a4,646c <.L15>
    sw	t1,-2036(a3)
    sw	t3,-2048(a3)
    sw	zero,-2044(a3)
    srli	a4,a7,0x4
    lui	a7,0x1
    sw	a4,-2040(a3)
    addi	a4,a7,-2048 # 800 <.LASF569+0x5>
    sw	a4,-2016(a3)
    li	a4,1
    sw	a4,-1984(a3)
    lw	a3,0(a2)
    lui	a7,0xffb20
    add	a3,a3,a4
    sw	a3,0(a2)
    lw	a4,520(a7) # ffb20208 <__stack_base+0x1f5d8>
    bne	a4,a3,64ac <.L16>
    fence
    lui	a7,0xffb43
    lw	t1,116(a5)
    lw	a4,104(a5)
    lw	a3,40(a7) # ffb43028 <__stack_base+0x423f8>
    add	a4,a4,t1
    addi	a3,a3,1
    lw	t1,100(a5)
    sw	a4,116(a5)
    sw	a3,40(a7)
    bne	a4,t1,64ec <.L17>
    lw	a3,96(a5)
    sub	a4,a4,a3
    sw	a4,116(a5)
    lui	t1,0xffb44
    lw	a7,40(t1) # ffb44028 <__stack_base+0x433f8>
    zext.h	a7,a7
    fence
    lw	a3,32(t1)
    lw	a4,140(a5)
    add	a4,a4,a3
    zext.h	a4,a4
    beq	a7,a4,64f8 <.L18>
    lw	a4,-1980(gp) # ffb00034 <crta_l1_base>
    lw	a7,0(a1)
    lw	t1,4(a4)
    lhu	a4,0(a0)
    lw	t3,148(a5)
    slli	a6,a4,0x4
    lui	a3,0xffb21
    add	a7,t1,a7
    lw	a4,-1984(a3) # ffb20840 <__stack_base+0x1fc10>
    bnez	a4,6530 <.L19>
    sw	t3,-2036(a3)
    sw	a7,-2048(a3)
    sw	zero,-2044(a3)
    srli	a4,a6,0x4
    lui	a6,0x1
    sw	a4,-2040(a3)
    addi	a4,a6,-2048 # 800 <.LASF569+0x5>
    sw	a4,-2016(a3)
    li	a4,1
    sw	a4,-1984(a3)
    lw	a3,0(a2)
    lui	a6,0xffb20
    add	a3,a3,a4
    sw	a3,0(a2)
    lw	a4,520(a6) # ffb20208 <__stack_base+0x1f5d8>
    bne	a4,a3,6570 <.L20>
    fence
    lui	a6,0xffb44
    lw	a7,148(a5)
    lw	a4,136(a5)
    lw	a3,40(a6) # ffb44028 <__stack_base+0x433f8>
    add	a4,a4,a7
    addi	a3,a3,1
    lw	a7,132(a5)
    sw	a4,148(a5)
    sw	a3,40(a6)
    bne	a4,a7,65b0 <.L21>
    lw	a3,128(a5)
    sub	a4,a4,a3
    sw	a4,148(a5)
    lui	a7,0xffb45
    lw	a6,40(a7) # ffb45028 <__stack_base+0x443f8>
    zext.h	a6,a6
    fence
    lw	a3,32(a7)
    lw	a4,172(a5)
    add	a4,a4,a3
    zext.h	a4,a4
    beq	a6,a4,65bc <.L22>
    lw	a3,4(a1)
    lhu	a4,2(a0)
    lw	a0,180(a5)
    add	t1,t1,a3
    slli	a1,a4,0x4
    lui	a3,0xffb21
    lw	a4,-1984(a3) # ffb20840 <__stack_base+0x1fc10>
    bnez	a4,65ec <.L23>
    sw	a0,-2036(a3)
    sw	t1,-2048(a3)
    sw	zero,-2044(a3)
    srli	a4,a1,0x4
    lui	a1,0x1
    sw	a4,-2040(a3)
    addi	a4,a1,-2048 # 800 <.LASF569+0x5>
    sw	a4,-2016(a3)
    li	a4,1
    sw	a4,-1984(a3)
    lw	a3,0(a2)
    lui	a1,0xffb20
    add	a3,a3,a4
    sw	a3,0(a2)
    lw	a4,520(a1) # ffb20208 <__stack_base+0x1f5d8>
    bne	a4,a3,662c <.L24>
    fence
    lui	a2,0xffb45
    lw	a1,180(a5)
    lw	a4,168(a5)
    lw	a3,40(a2) # ffb45028 <__stack_base+0x443f8>
    add	a4,a4,a1
    addi	a3,a3,1
    lw	a1,164(a5)
    sw	a4,180(a5)
    sw	a3,40(a2)
    beq	a4,a1,6664 <.L45>
    ret
    lw	a3,160(a5)
    sub	a4,a4,a3
    sw	a4,180(a5)
    ret
