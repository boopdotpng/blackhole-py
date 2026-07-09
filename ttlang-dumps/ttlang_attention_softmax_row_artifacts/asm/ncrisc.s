    lui	a5,0xffb01
    lui	a4,0xffb01
    addi	a5,a5,-976 # ffb00c30 <__stack_base>
    addi	a4,a4,-984 # ffb00c28 <__ldm_bss_end>
    bltu	a4,a5,60ec <.L2>
    sw	zero,-4(a5)
    sw	zero,-8(a5)
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a5,a5,16
    bgeu	a4,a5,60d4 <.L3>
    addi	a3,a5,-8
    bltu	a4,a3,637c <.L24>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,6108 <.L5>
    sw	zero,-8(a5)
    auipc	a4,0x0
    addi	a4,a4,636 # 6384 <__kernel_data_lma>
    addi	a5,gp,1072 # ffb00c20 <noc_reads_num_issued>
    beq	a4,a5,6174 <.L7>
    addi	a2,gp,1072 # ffb00c20 <noc_reads_num_issued>
    sub	a2,a2,a5
    li	a1,8
    srai	a3,a2,0x2
    bge	a1,a2,6158 <.L8>
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
    blt	a6,a3,6130 <.L9>
    blez	a3,6174 <.L7>
    lw	a1,0(a4)
    li	a2,2
    sw	a1,0(a5)
    bne	a3,a2,6174 <.L7>
    lw	a4,4(a4)
    sw	a4,4(a5)
    lui	a5,0xffb20
    lw	a4,520(a5) # ffb20208 <__stack_base+0x1f5d8>
    lw	a3,552(a5)
    lw	a3,516(a5)
    addi	a0,gp,1072 # ffb00c20 <noc_reads_num_issued>
    lw	a3,512(a5)
    lw	a5,556(a5)
    sw	a4,0(a0)
    lw	a4,1312(zero) # 520 <.LLST104+0x2>
    li	a3,128
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    addi	a4,a4,96
    beq	a5,a3,61b8 <.L13>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,61ac <.L11>
    lui	a2,0xffb40
    lui	a3,0xffb00
    lw	a6,40(a2) # ffb40028 <__stack_base+0x3f3f8>
    addi	a3,a3,1048 # ffb00418 <cb_interface>
    li	a1,3
    fence
    lw	a4,32(a2)
    lw	a5,12(a3)
    add	a5,a5,a4
    sub	a5,a5,a6
    zext.h	a5,a5
    bgeu	a1,a5,61cc <.L12>
    lui	a2,0xffb41
    lw	a6,40(a2) # ffb41028 <__stack_base+0x403f8>
    li	a1,3
    fence
    lw	a4,32(a2)
    lw	a5,44(a3)
    add	a5,a5,a4
    sub	a5,a5,a6
    zext.h	a5,a5
    bgeu	a1,a5,61f4 <.L14>
    lw	a5,-1980(gp) # ffb00034 <crta_l1_base>
    lw	t3,0(a5)
    addi	a1,gp,-1968 # ffb00040 <dram_bank_to_noc_xy>
    addi	t1,gp,-1500 # ffb00214 <bank_to_dram_offset>
    lw	t6,20(a3)
    mv	t5,t1
    addi	t4,a1,8
    mv	a6,a1
    lui	a4,0xffb21
    lui	t0,0x1
    li	t2,1
    lhu	a5,0(a6)
    lw	a7,0(t5)
    slli	a2,a5,0x4
    add	a7,t3,a7
    lw	a5,-1984(a4) # ffb20840 <__stack_base+0x1fc10>
    bnez	a5,624c <.L15>
    sw	t6,-2036(a4)
    sw	a7,-2048(a4)
    sw	zero,-2044(a4)
    srli	a5,a2,0x4
    sw	a5,-2040(a4)
    sw	t0,-2016(a4)
    sw	t2,-1984(a4)
    lw	a5,0(a0)
    addi	a6,a6,2
    addi	a5,a5,1
    sw	a5,0(a0)
    addi	t5,t5,4
    add	t6,t6,t0
    bne	t4,a6,623c <.L16>
    lui	a2,0xffb20
    lw	a4,520(a2) # ffb20208 <__stack_base+0x1f5d8>
    bne	a4,a5,6290 <.L17>
    fence
    lw	a7,52(a3)
    lui	a4,0xffb21
    lui	t5,0x1
    li	t6,1
    lhu	a5,0(a1)
    lw	a6,0(t1)
    slli	a2,a5,0x4
    add	a6,t3,a6
    lw	a5,-1984(a4) # ffb20840 <__stack_base+0x1fc10>
    bnez	a5,62bc <.L18>
    sw	a7,-2036(a4)
    sw	a6,-2048(a4)
    sw	zero,-2044(a4)
    srli	a5,a2,0x4
    sw	a5,-2040(a4)
    sw	t5,-2016(a4)
    sw	t6,-1984(a4)
    lw	a5,0(a0)
    addi	a1,a1,2
    addi	a5,a5,1
    sw	a5,0(a0)
    addi	t1,t1,4
    add	a7,a7,t5
    bne	t4,a1,62ac <.L19>
    lui	a2,0xffb20
    lw	a4,520(a2) # ffb20208 <__stack_base+0x1f5d8>
    bne	a4,a5,6300 <.L20>
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
    bne	a5,a1,6340 <.L21>
    lw	a4,32(a3)
    sub	a5,a5,a4
    sw	a5,52(a3)
    lui	a2,0xffb40
    lw	a4,40(a2) # ffb40028 <__stack_base+0x3f3f8>
    lw	a0,20(a3)
    lw	a5,8(a3)
    addi	a4,a4,4
    lw	a1,4(a3)
    sh2add	a5,a5,a0
    sw	a4,40(a2)
    sw	a5,20(a3)
    bne	a5,a1,6374 <.L22>
    lw	a4,0(a3)
    sub	a5,a5,a4
    sw	a5,20(a3)
    li	a0,0
    ret
    mv	a5,a3
    j	60fc <.L4>
