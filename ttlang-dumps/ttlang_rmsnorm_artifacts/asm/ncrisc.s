    addi	sp,sp,-48
    sw	s0,44(sp)
    sw	s1,40(sp)
    sw	s2,36(sp)
    sw	s3,32(sp)
    sw	s4,28(sp)
    sw	s5,24(sp)
    sw	s6,20(sp)
    sw	s7,16(sp)
    sw	s8,12(sp)
    lui	a5,0xffb01
    lui	a4,0xffb01
    addi	a5,a5,-976 # ffb00c30 <__stack_base>
    addi	a4,a4,-984 # ffb00c28 <__ldm_bss_end>
    bltu	a4,a5,6114 <.L2>
    sw	zero,-4(a5)
    sw	zero,-8(a5)
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a5,a5,16
    bgeu	a4,a5,60fc <.L3>
    addi	a3,a5,-8
    bltu	a4,a3,65c0 <.L32>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,6130 <.L5>
    sw	zero,-8(a5)
    auipc	a4,0x0
    addi	a4,a4,1176 # 65c8 <__kernel_data_lma>
    addi	a5,gp,1072 # ffb00c20 <noc_reads_num_issued>
    beq	a4,a5,619c <.L7>
    addi	a2,gp,1072 # ffb00c20 <noc_reads_num_issued>
    sub	a2,a2,a5
    li	a1,8
    srai	a3,a2,0x2
    bge	a1,a2,6180 <.L8>
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
    blt	a6,a3,6158 <.L9>
    blez	a3,619c <.L7>
    lw	a1,0(a4)
    li	a2,2
    sw	a1,0(a5)
    bne	a3,a2,619c <.L7>
    lw	a4,4(a4)
    sw	a4,4(a5)
    lui	a5,0xffb20
    lw	a4,520(a5) # ffb20208 <__stack_base+0x1f5d8>
    lw	a3,552(a5)
    lw	a3,516(a5)
    addi	t1,gp,1072 # ffb00c20 <noc_reads_num_issued>
    lw	a3,512(a5)
    lw	a5,556(a5)
    sw	a4,0(t1)
    lw	a4,1312(zero) # 520 <.LASF1325+0x4>
    li	a3,128
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    addi	a4,a4,96
    beq	a5,a3,61e0 <.L13>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,61d4 <.L11>
    lui	a1,0xffb42
    lw	a2,40(a1) # ffb42028 <__stack_base+0x413f8>
    lui	a4,0xffb00
    addi	a4,a4,1048 # ffb00418 <cb_interface>
    zext.h	a2,a2
    fence
    lw	a3,32(a1)
    lw	a5,76(a4)
    add	a5,a5,a3
    zext.h	a5,a5
    beq	a2,a5,61f4 <.L12>
    lw	a5,-1980(gp) # ffb00034 <crta_l1_base>
    lw	a2,0(a5)
    addi	t4,gp,-1500 # ffb00214 <bank_to_dram_offset>
    addi	t5,gp,-1968 # ffb00040 <dram_bank_to_noc_xy>
    lw	a0,0(t4)
    lhu	a3,0(t5)
    lw	a1,84(a4)
    slli	a3,a3,0x4
    lui	a5,0xffb21
    add	a2,a2,a0
    lw	t3,-1984(a5) # ffb20840 <__stack_base+0x1fc10>
    bnez	t3,6234 <.L14>
    sw	a1,-2036(a5)
    sw	a2,-2048(a5)
    sw	zero,-2044(a5)
    srli	a3,a3,0x4
    sw	a3,-2040(a5)
    lui	a3,0x1
    sw	a3,-2016(a5)
    li	a3,1
    sw	a3,-1984(a5)
    lw	a3,0(t1)
    lui	a2,0xffb20
    addi	a3,a3,1 # 1001 <.LLST371>
    sw	a3,0(t1)
    lw	a5,520(a2) # ffb20208 <__stack_base+0x1f5d8>
    bne	a5,a3,6270 <.L15>
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
    bne	a5,a1,62b0 <.L16>
    lw	a3,64(a4)
    sub	a5,a5,a3
    sw	a5,84(a4)
    lui	t2,0x92492
    lui	s0,0x1
    addi	s2,t2,1171 # 92492493 <__device_print_strings_info_end+0x8bf92493>
    addi	s0,s0,-2048 # 800 <.LASF1257+0x2>
    addi	t2,t2,1216
    li	a7,0
    li	t6,0
    lui	a0,0xffb40
    lui	a1,0xffb21
    li	s1,1
    lui	a6,0xffb20
    li	s3,36
    lw	a2,40(a0) # ffb40028 <__stack_base+0x3f3f8>
    zext.h	a2,a2
    fence
    lw	a3,32(a0)
    lw	a5,12(a4)
    add	a5,a5,a3
    zext.h	a5,a5
    beq	a2,a5,62e8 <.L17>
    lw	a3,-1980(gp) # ffb00034 <crta_l1_base>
    srli	a5,t6,0x2
    lw	s5,8(a3)
    slli	a3,a5,0x3
    sub	a3,a3,a5
    sub	a3,t3,a3
    sh2add	a2,a3,t4
    slli	a5,a5,0xb
    sh1add	a3,a3,t5
    lw	a2,0(a2)
    lhu	a3,0(a3)
    lw	s4,20(a4)
    slli	a3,a3,0x4
    add	a5,a5,s5
    add	a5,a5,a2
    lw	a2,-1984(a1) # ffb20840 <__stack_base+0x1fc10>
    bnez	a2,633c <.L18>
    sw	s4,-2036(a1)
    sw	a5,-2048(a1)
    sw	zero,-2044(a1)
    srli	a5,a3,0x4
    sw	a5,-2040(a1)
    sw	s0,-2016(a1)
    sw	s1,-1984(a1)
    lw	a3,0(t1)
    addi	a3,a3,1
    sw	a3,0(t1)
    lw	a5,520(a6) # ffb20208 <__stack_base+0x1f5d8>
    bne	a5,a3,636c <.L19>
    fence
    lw	a3,40(a0)
    lw	s4,20(a4)
    lw	a5,8(a4)
    addi	a3,a3,1
    add	a5,a5,s4
    lw	s4,4(a4)
    sw	a3,40(a0)
    sw	a5,20(a4)
    bne	a5,s4,63a8 <.L20>
    lw	a3,0(a4)
    sub	a5,a5,a3
    sw	a5,20(a4)
    add	a5,a7,s2
    sltu	a3,a5,a7
    addi	t3,t3,1
    mv	a7,a5
    add	t6,a3,t6
    bne	a5,t2,62e0 <.L50>
    bne	t6,s3,62e0 <.L50>
    lui	s1,0x92492
    lui	t2,0x1
    addi	s2,s1,1171 # 92492493 <__device_print_strings_info_end+0x8bf92493>
    addi	t2,t2,-2048 # 800 <.LASF1257+0x2>
    addi	s1,s1,1216
    li	t3,0
    li	t6,0
    lui	a7,0xffb40
    lui	a3,0xffb21
    li	s0,1
    lui	a1,0xffb20
    lui	a6,0xffb41
    li	s3,36
    lw	s4,40(a7) # ffb40028 <__stack_base+0x3f3f8>
    zext.h	s4,s4
    fence
    lw	a0,32(a7)
    lw	a5,12(a4)
    add	a5,a5,a0
    zext.h	a5,a5
    beq	s4,a5,6400 <.L22>
    lw	a5,-1980(gp) # ffb00034 <crta_l1_base>
    srli	s4,t6,0x2
    lw	s6,8(a5)
    slli	s5,s4,0x3
    sub	s5,s5,s4
    sub	s5,a2,s5
    sh2add	a0,s5,t4
    slli	s4,s4,0xb
    sh1add	a5,s5,t5
    lw	s8,0(a0)
    lhu	a5,0(a5)
    lw	s7,20(a4)
    slli	a0,a5,0x4
    add	s6,s4,s6
    add	s6,s6,s8
    lw	a5,-1984(a3) # ffb20840 <__stack_base+0x1fc10>
    bnez	a5,6454 <.L23>
    sw	s7,-2036(a3)
    sw	s6,-2048(a3)
    sw	zero,-2044(a3)
    srli	a5,a0,0x4
    sw	a5,-2040(a3)
    sw	t2,-2016(a3)
    sw	s0,-1984(a3)
    lw	a0,0(t1)
    addi	a0,a0,1
    sw	a0,0(t1)
    lw	a5,520(a1) # ffb20208 <__stack_base+0x1f5d8>
    bne	a5,a0,6484 <.L24>
    fence
    lw	a0,40(a7)
    lw	s6,20(a4)
    lw	a5,8(a4)
    addi	a0,a0,1
    add	a5,a5,s6
    lw	s6,4(a4)
    sw	a0,40(a7)
    sw	a5,20(a4)
    bne	a5,s6,64c0 <.L25>
    lw	a0,0(a4)
    sub	a5,a5,a0
    sw	a5,20(a4)
    lw	s6,40(a6) # ffb41028 <__stack_base+0x403f8>
    zext.h	s6,s6
    fence
    lw	a0,32(a6)
    lw	a5,44(a4)
    add	a5,a5,a0
    zext.h	a5,a5
    beq	s6,a5,64c8 <.L26>
    lw	a5,-1980(gp) # ffb00034 <crta_l1_base>
    sh2add	a0,s5,t4
    sh1add	s5,s5,t5
    lw	s6,0(a0)
    lw	s7,4(a5)
    lhu	a5,0(s5)
    lw	s5,52(a4)
    slli	a0,a5,0x4
    add	s4,s4,s7
    add	s4,s4,s6
    lw	a5,-1984(a3)
    bnez	a5,6508 <.L27>
    sw	s5,-2036(a3)
    sw	s4,-2048(a3)
    sw	zero,-2044(a3)
    srli	a5,a0,0x4
    sw	a5,-2040(a3)
    sw	t2,-2016(a3)
    sw	s0,-1984(a3)
    lw	a0,0(t1)
    addi	a0,a0,1
    sw	a0,0(t1)
    lw	a5,520(a1)
    bne	a5,a0,6538 <.L28>
    fence
    lw	a0,40(a6)
    lw	s4,52(a4)
    lw	a5,40(a4)
    addi	a0,a0,1
    add	a5,a5,s4
    lw	s4,36(a4)
    sw	a0,40(a6)
    sw	a5,52(a4)
    bne	a5,s4,6574 <.L29>
    lw	a0,32(a4)
    sub	a5,a5,a0
    sw	a5,52(a4)
    add	a5,t3,s2
    sltu	a0,a5,t3
    addi	a2,a2,1
    mv	t3,a5
    add	t6,a0,t6
    bne	a5,s1,63f8 <.L51>
    bne	t6,s3,63f8 <.L51>
    lw	s0,44(sp)
    lw	s1,40(sp)
    lw	s2,36(sp)
    lw	s3,32(sp)
    lw	s4,28(sp)
    lw	s5,24(sp)
    lw	s6,20(sp)
    lw	s7,16(sp)
    lw	s8,12(sp)
    li	a0,0
    addi	sp,sp,48
    ret
    mv	a5,a3
    j	6124 <.L4>
