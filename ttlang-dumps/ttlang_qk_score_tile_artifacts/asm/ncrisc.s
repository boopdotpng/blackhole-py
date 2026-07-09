    addi	sp,sp,-16
    sw	s0,12(sp)
    sw	s1,8(sp)
    sw	s2,4(sp)
    lui	a5,0xffb01
    lui	a4,0xffb01
    addi	a5,a5,-976 # ffb00c30 <__stack_base>
    addi	a4,a4,-984 # ffb00c28 <__ldm_bss_end>
    bltu	a4,a5,60fc <.L2>
    sw	zero,-4(a5)
    sw	zero,-8(a5)
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a5,a5,16
    bgeu	a4,a5,60e4 <.L3>
    addi	a3,a5,-8
    bltu	a4,a3,647c <.L28>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,6118 <.L5>
    sw	zero,-8(a5)
    auipc	a4,0x0
    addi	a4,a4,876 # 6484 <__kernel_data_lma>
    addi	a5,gp,1072 # ffb00c20 <noc_reads_num_issued>
    beq	a4,a5,6184 <.L7>
    addi	a2,gp,1072 # ffb00c20 <noc_reads_num_issued>
    sub	a2,a2,a5
    li	a1,8
    srai	a3,a2,0x2
    bge	a1,a2,6168 <.L8>
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
    blt	a6,a3,6140 <.L9>
    blez	a3,6184 <.L7>
    lw	a1,0(a4)
    li	a2,2
    sw	a1,0(a5)
    bne	a3,a2,6184 <.L7>
    lw	a4,4(a4)
    sw	a4,4(a5)
    lui	a5,0xffb20
    lw	a4,520(a5) # ffb20208 <__stack_base+0x1f5d8>
    lw	a3,552(a5)
    lw	a3,516(a5)
    addi	a1,gp,1072 # ffb00c20 <noc_reads_num_issued>
    lw	a3,512(a5)
    lw	a5,556(a5)
    sw	a4,0(a1)
    lw	a4,1312(zero) # 520 <.LASF1289+0x4>
    li	a3,128
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    addi	a4,a4,96
    beq	a5,a3,61c8 <.L13>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,61bc <.L11>
    lui	a2,0xffb40
    lui	a4,0xffb00
    lw	a6,40(a2) # ffb40028 <__stack_base+0x3f3f8>
    addi	a4,a4,1048 # ffb00418 <cb_interface>
    li	a0,1
    fence
    lw	a3,32(a2)
    lw	a5,12(a4)
    add	a5,a5,a3
    sub	a5,a5,a6
    zext.h	a5,a5
    bgeu	a0,a5,61dc <.L12>
    lw	a5,-1980(gp) # ffb00034 <crta_l1_base>
    lw	a0,20(a4)
    lw	s2,4(a5)
    lui	t2,0x1
    addi	t3,gp,-1500 # ffb00214 <bank_to_dram_offset>
    addi	t4,gp,-1968 # ffb00040 <dram_bank_to_noc_xy>
    add	s1,a0,t2
    mv	t0,t3
    addi	t2,t2,-2048 # 800 <.LLST150>
    mv	t6,t4
    lui	a3,0xffb21
    li	s0,1
    lhu	a5,0(t6)
    lw	t5,0(t0)
    slli	a2,a5,0x4
    add	t5,s2,t5
    lw	a5,-1984(a3) # ffb20840 <__stack_base+0x1fc10>
    bnez	a5,6238 <.L14>
    sw	a0,-2036(a3)
    sw	t5,-2048(a3)
    sw	zero,-2044(a3)
    srli	a5,a2,0x4
    sw	a5,-2040(a3)
    sw	t2,-2016(a3)
    sw	s0,-1984(a3)
    lw	a2,0(a1)
    addi	a0,a0,2047
    addi	a2,a2,1
    addi	a0,a0,1
    sw	a2,0(a1)
    addi	t0,t0,4
    addi	t6,t6,2
    bne	a0,s1,6228 <.L15>
    lui	a3,0xffb20
    lw	a5,520(a3) # ffb20208 <__stack_base+0x1f5d8>
    bne	a5,a2,6280 <.L16>
    fence
    lui	a2,0xffb40
    lw	a3,40(a2) # ffb40028 <__stack_base+0x3f3f8>
    lw	t5,20(a4)
    lw	a5,8(a4)
    addi	a3,a3,2
    lw	a0,4(a4)
    sh1add	a5,a5,t5
    sw	a3,40(a2)
    sw	a5,20(a4)
    bne	a5,a0,62c0 <.L17>
    lw	a3,0(a4)
    sub	a5,a5,a3
    sw	a5,20(a4)
    lui	a2,0xffb41
    lw	t5,40(a2) # ffb41028 <__stack_base+0x403f8>
    li	a0,1
    fence
    lw	a3,32(a2)
    lw	a5,44(a4)
    add	a5,a5,a3
    sub	a5,a5,t5
    zext.h	a5,a5
    bgeu	a0,a5,62cc <.L18>
    lw	a5,-1980(gp) # ffb00034 <crta_l1_base>
    lw	a0,52(a4)
    lw	s0,0(a5)
    lui	t6,0x1
    add	t2,a0,t6
    lui	a3,0xffb21
    addi	t6,t6,-2048 # 800 <.LLST150>
    li	t0,1
    lhu	a5,0(t4)
    lw	t5,0(t3)
    slli	a2,a5,0x4
    add	t5,s0,t5
    lw	a5,-1984(a3) # ffb20840 <__stack_base+0x1fc10>
    bnez	a5,6318 <.L19>
    sw	a0,-2036(a3)
    sw	t5,-2048(a3)
    sw	zero,-2044(a3)
    srli	a5,a2,0x4
    sw	a5,-2040(a3)
    sw	t6,-2016(a3)
    sw	t0,-1984(a3)
    lw	a2,0(a1)
    addi	a0,a0,2047
    addi	a2,a2,1
    addi	a0,a0,1
    sw	a2,0(a1)
    addi	t3,t3,4
    addi	t4,t4,2
    bne	t2,a0,6308 <.L20>
    lui	a3,0xffb20
    lw	a5,520(a3) # ffb20208 <__stack_base+0x1f5d8>
    bne	a5,a2,6360 <.L21>
    fence
    lui	a2,0xffb41
    lw	a3,40(a2) # ffb41028 <__stack_base+0x403f8>
    lw	t3,52(a4)
    lw	a5,40(a4)
    addi	a3,a3,2
    lw	a0,36(a4)
    sh1add	a5,a5,t3
    sw	a3,40(a2)
    sw	a5,52(a4)
    bne	a5,a0,63a0 <.L22>
    lw	a3,32(a4)
    sub	a5,a5,a3
    sw	a5,52(a4)
    lui	a0,0xffb42
    lw	a2,40(a0) # ffb42028 <__stack_base+0x413f8>
    zext.h	a2,a2
    fence
    lw	a3,32(a0)
    lw	a5,76(a4)
    add	a5,a5,a3
    zext.h	a5,a5
    beq	a2,a5,63ac <.L23>
    lw	a5,-1980(gp) # ffb00034 <crta_l1_base>
    lw	a7,-1500(gp) # ffb00214 <bank_to_dram_offset>
    lw	a0,8(a5)
    lhu	a5,-1968(gp) # ffb00040 <dram_bank_to_noc_xy>
    lw	a6,84(a4)
    slli	a2,a5,0x4
    lui	a3,0xffb21
    add	a0,a0,a7
    lw	a5,-1984(a3) # ffb20840 <__stack_base+0x1fc10>
    bnez	a5,63e4 <.L24>
    sw	a6,-2036(a3)
    sw	a0,-2048(a3)
    sw	zero,-2044(a3)
    srli	a5,a2,0x4
    lui	a2,0x1
    sw	a5,-2040(a3)
    addi	a5,a2,-2048 # 800 <.LLST150>
    sw	a5,-2016(a3)
    li	a5,1
    sw	a5,-1984(a3)
    lw	a3,0(a1)
    lui	a2,0xffb20
    add	a3,a3,a5
    sw	a3,0(a1)
    lw	a5,520(a2) # ffb20208 <__stack_base+0x1f5d8>
    bne	a5,a3,6424 <.L25>
    fence
    lui	a2,0xffb42
    lw	a1,84(a4)
    lw	a5,72(a4)
    lw	a3,40(a2) # ffb42028 <__stack_base+0x413f8>
    add	a5,a5,a1
    addi	a3,a3,1
    lw	a1,68(a4)
    sw	a5,84(a4)
    sw	a3,40(a2)
    bne	a5,a1,6464 <.L26>
    lw	a3,64(a4)
    sub	a5,a5,a3
    sw	a5,84(a4)
    lw	s0,12(sp)
    lw	s1,8(sp)
    lw	s2,4(sp)
    li	a0,0
    addi	sp,sp,16
    ret
    mv	a5,a3
    j	610c <.L4>
