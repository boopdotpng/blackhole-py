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
    bltu	a4,a3,63a8 <.L22>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,6108 <.L5>
    sw	zero,-8(a5)
    auipc	a4,0x0
    addi	a4,a4,680 # 63b0 <__kernel_data_lma>
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
    lw	a4,1312(zero) # 520 <.LASF1082+0x3>
    li	a3,128
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    addi	a4,a4,96
    beq	a5,a3,61b8 <.L13>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,61ac <.L11>
    lbu	a2,-1972(gp) # ffb0003c <my_logical_y_>
    lui	a6,0xffb40
    lw	a1,40(a6) # ffb40028 <__stack_base+0x3f3f8>
    lui	a4,0xffb00
    lbu	a7,-1971(gp) # ffb0003d <my_logical_x_>
    zext.h	a1,a1
    srli	a2,a2,0x2
    addi	a4,a4,1048 # ffb00418 <cb_interface>
    fence
    lw	a3,32(a6)
    lw	a5,12(a4)
    add	a5,a5,a3
    zext.h	a5,a5
    beq	a1,a5,61d8 <.L12>
    lw	a5,-1980(gp) # ffb00034 <crta_l1_base>
    slli	a2,a2,0x9
    lw	a6,0(a5)
    addi	a5,a7,14
    add	a2,a2,a5
    lui	a5,0x92492
    addi	a5,a5,1171 # 92492493 <__device_print_strings_info_end+0x8bf92493>
    mulhu	a5,a2,a5
    srli	a5,a5,0x2
    slli	a3,a5,0x3
    sub	a3,a3,a5
    sub	a2,a2,a3
    addi	t1,gp,-1500 # ffb00214 <bank_to_dram_offset>
    addi	t4,gp,-1968 # ffb00040 <dram_bank_to_noc_xy>
    sh2add	a3,a2,t1
    slli	a7,a5,0xb
    sh1add	a5,a2,t4
    lw	a3,0(a3)
    lhu	a5,0(a5)
    add	a6,a7,a6
    lw	t5,20(a4)
    add	a6,a6,a3
    slli	a1,a5,0x4
    lui	a3,0xffb21
    lw	a5,-1984(a3) # ffb20840 <__stack_base+0x1fc10>
    bnez	a5,6250 <.L14>
    sw	t5,-2036(a3)
    sw	a6,-2048(a3)
    sw	zero,-2044(a3)
    srli	a5,a1,0x4
    lui	a1,0x1
    sw	a5,-2040(a3)
    addi	a5,a1,-2048 # 800 <.LVUS188>
    sw	a5,-2016(a3)
    li	a5,1
    sw	a5,-1984(a3)
    lw	a3,0(a0)
    lui	a1,0xffb20
    add	a3,a3,a5
    sw	a3,0(a0)
    lw	a5,520(a1) # ffb20208 <__stack_base+0x1f5d8>
    bne	a5,a3,6290 <.L15>
    fence
    lui	a1,0xffb40
    lw	a6,20(a4)
    lw	a5,8(a4)
    lw	a3,40(a1) # ffb40028 <__stack_base+0x3f3f8>
    add	a5,a5,a6
    addi	a3,a3,1
    lw	a6,4(a4)
    sw	a5,20(a4)
    sw	a3,40(a1)
    bne	a5,a6,62d0 <.L16>
    lw	a3,0(a4)
    sub	a5,a5,a3
    sw	a5,20(a4)
    lui	a6,0xffb41
    lw	a1,40(a6) # ffb41028 <__stack_base+0x403f8>
    zext.h	a1,a1
    fence
    lw	a3,32(a6)
    lw	a5,44(a4)
    add	a5,a5,a3
    zext.h	a5,a5
    beq	a1,a5,62dc <.L17>
    lw	a5,-1980(gp) # ffb00034 <crta_l1_base>
    sh2add	t1,a2,t1
    sh1add	a2,a2,t4
    lw	a6,0(t1)
    lw	t1,4(a5)
    lhu	a5,0(a2)
    lw	a1,52(a4)
    slli	a2,a5,0x4
    lui	a3,0xffb21
    add	a7,a7,t1
    add	a7,a7,a6
    lw	a5,-1984(a3) # ffb20840 <__stack_base+0x1fc10>
    bnez	a5,6320 <.L18>
    sw	a1,-2036(a3)
    sw	a7,-2048(a3)
    sw	zero,-2044(a3)
    srli	a5,a2,0x4
    lui	a2,0x1
    sw	a5,-2040(a3)
    addi	a5,a2,-2048 # 800 <.LVUS188>
    sw	a5,-2016(a3)
    li	a5,1
    sw	a5,-1984(a3)
    lw	a3,0(a0)
    lui	a2,0xffb20
    add	a3,a3,a5
    sw	a3,0(a0)
    lw	a5,520(a2) # ffb20208 <__stack_base+0x1f5d8>
    bne	a5,a3,6360 <.L19>
    fence
    lui	a2,0xffb41
    lw	a1,52(a4)
    lw	a5,40(a4)
    lw	a3,40(a2) # ffb41028 <__stack_base+0x403f8>
    add	a5,a5,a1
    addi	a3,a3,1
    lw	a1,36(a4)
    sw	a5,52(a4)
    sw	a3,40(a2)
    bne	a5,a1,63a0 <.L20>
    lw	a3,32(a4)
    sub	a5,a5,a3
    sw	a5,52(a4)
    li	a0,0
    ret
    mv	a5,a3
    j	60fc <.L4>
