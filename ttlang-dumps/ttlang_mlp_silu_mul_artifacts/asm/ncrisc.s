    addi	sp,sp,-16
    sw	s0,12(sp)
    lui	a5,0xffb01
    lui	a4,0xffb01
    addi	a5,a5,-976 # ffb00c30 <__stack_base>
    addi	a4,a4,-984 # ffb00c28 <__ldm_bss_end>
    bltu	a4,a5,60f4 <.L2>
    sw	zero,-4(a5)
    sw	zero,-8(a5)
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a5,a5,16
    bgeu	a4,a5,60dc <.L3>
    addi	a3,a5,-8
    bltu	a4,a3,63a4 <.L24>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,6110 <.L5>
    sw	zero,-8(a5)
    auipc	a4,0x0
    addi	a4,a4,668 # 63ac <__kernel_data_lma>
    addi	a5,gp,1072 # ffb00c20 <noc_reads_num_issued>
    beq	a4,a5,617c <.L7>
    addi	a2,gp,1072 # ffb00c20 <noc_reads_num_issued>
    sub	a2,a2,a5
    li	a1,8
    srai	a3,a2,0x2
    bge	a1,a2,6160 <.L8>
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
    blt	a6,a3,6138 <.L9>
    blez	a3,617c <.L7>
    lw	a1,0(a4)
    li	a2,2
    sw	a1,0(a5)
    bne	a3,a2,617c <.L7>
    lw	a4,4(a4)
    sw	a4,4(a5)
    lui	a5,0xffb20
    lw	a4,520(a5) # ffb20208 <__stack_base+0x1f5d8>
    lw	a3,552(a5)
    lw	a3,516(a5)
    addi	a6,gp,1072 # ffb00c20 <noc_reads_num_issued>
    lw	a3,512(a5)
    lw	a5,556(a5)
    sw	a4,0(a6)
    lw	a4,1312(zero) # 520 <.LLST95+0x2>
    li	a3,128
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    addi	a4,a4,96
    beq	a5,a3,61c0 <.L13>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,61b4 <.L11>
    lui	a2,0xffb40
    lui	a3,0xffb00
    lw	a0,40(a2) # ffb40028 <__stack_base+0x3f3f8>
    addi	a3,a3,1048 # ffb00418 <cb_interface>
    li	a1,3
    fence
    lw	a4,32(a2)
    lw	a5,12(a3)
    add	a5,a5,a4
    sub	a5,a5,a0
    zext.h	a5,a5
    bgeu	a1,a5,61d4 <.L12>
    lw	a5,-1980(gp) # ffb00034 <crta_l1_base>
    lw	s0,0(a5)
    addi	a0,gp,-1968 # ffb00040 <dram_bank_to_noc_xy>
    addi	a7,gp,-1500 # ffb00214 <bank_to_dram_offset>
    lui	t0,0x1
    lw	a1,20(a3)
    mv	t5,a7
    addi	t1,a0,8
    mv	t3,a0
    addi	t0,t0,-2048 # 800 <.LLST162+0x5>
    lui	a4,0xffb21
    li	t2,1
    lhu	a5,0(t3)
    lw	t4,0(t5)
    slli	a2,a5,0x4
    add	t4,s0,t4
    lw	a5,-1984(a4) # ffb20840 <__stack_base+0x1fc10>
    bnez	a5,6230 <.L14>
    sw	a1,-2036(a4)
    sw	t4,-2048(a4)
    sw	zero,-2044(a4)
    srli	a5,a2,0x4
    sw	a5,-2040(a4)
    sw	t0,-2016(a4)
    sw	t2,-1984(a4)
    lw	a5,0(a6)
    addi	a1,a1,2047
    addi	a5,a5,1
    addi	t3,t3,2
    sw	a5,0(a6)
    addi	a1,a1,1
    addi	t5,t5,4
    bne	t1,t3,6220 <.L15>
    lui	a2,0xffb20
    lw	a4,520(a2) # ffb20208 <__stack_base+0x1f5d8>
    bne	a4,a5,6278 <.L16>
    fence
    lui	a2,0xffb40
    lw	a4,40(a2) # ffb40028 <__stack_base+0x3f3f8>
    lw	t3,20(a3)
    lw	a5,8(a3)
    addi	a4,a4,4
    lw	a1,4(a3)
    sh2add	a5,a5,t3
    sw	a4,40(a2)
    sw	a5,20(a3)
    bne	a5,a1,62b8 <.L17>
    lw	a4,0(a3)
    sub	a5,a5,a4
    sw	a5,20(a3)
    lui	a2,0xffb41
    lw	t3,40(a2) # ffb41028 <__stack_base+0x403f8>
    li	a1,3
    fence
    lw	a4,32(a2)
    lw	a5,44(a3)
    add	a5,a5,a4
    sub	a5,a5,t3
    zext.h	a5,a5
    bgeu	a1,a5,62c4 <.L18>
    lw	a5,-1980(gp) # ffb00034 <crta_l1_base>
    lui	t4,0x1
    lw	t6,4(a5)
    lw	a1,52(a3)
    addi	t4,t4,-2048 # 800 <.LLST162+0x5>
    lui	a4,0xffb21
    li	t5,1
    lhu	a5,0(a0)
    lw	t3,0(a7)
    slli	a2,a5,0x4
    add	t3,t6,t3
    lw	a5,-1984(a4) # ffb20840 <__stack_base+0x1fc10>
    bnez	a5,630c <.L19>
    sw	a1,-2036(a4)
    sw	t3,-2048(a4)
    sw	zero,-2044(a4)
    srli	a5,a2,0x4
    sw	a5,-2040(a4)
    sw	t4,-2016(a4)
    sw	t5,-1984(a4)
    lw	a5,0(a6)
    addi	a1,a1,2047
    addi	a5,a5,1
    addi	a0,a0,2
    sw	a5,0(a6)
    addi	a1,a1,1
    addi	a7,a7,4
    bne	t1,a0,62fc <.L20>
    lui	a2,0xffb20
    lw	a4,520(a2) # ffb20208 <__stack_base+0x1f5d8>
    bne	a4,a5,6354 <.L21>
    fence
    lui	a2,0xffb41
    lw	a4,40(a2) # ffb41028 <__stack_base+0x403f8>
    lw	a0,52(a3)
    lw	a5,40(a3)
    addi	a4,a4,4
    lw	a1,36(a3)
    sh2add	a5,a5,a0
    sw	a4,40(a2)
    sw	a5,52(a3)
    bne	a5,a1,6394 <.L22>
    lw	a4,32(a3)
    sub	a5,a5,a4
    sw	a5,52(a3)
    lw	s0,12(sp)
    li	a0,0
    addi	sp,sp,16
    ret
    mv	a5,a3
    j	6104 <.L4>
