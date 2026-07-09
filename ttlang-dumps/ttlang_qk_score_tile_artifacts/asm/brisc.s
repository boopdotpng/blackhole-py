    lui	a5,0xffb01
    addi	a5,a5,-960 # ffb00c40 <__fw_export_ldm_end+0x10>
    addi	a4,gp,1088 # ffb00c30 <__fw_export_ldm_end>
    bltu	a4,a5,4d08 <.L2>
    sw	zero,-4(a5)
    sw	zero,-8(a5)
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a5,a5,16
    bgeu	a4,a5,4cf0 <.L3>
    addi	a3,a5,-8
    bltu	a4,a3,4ec8 <.L18>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,4d24 <.L5>
    sw	zero,-8(a5)
    auipc	a4,0x0
    addi	a4,a4,428 # 4ed0 <__kernel_data_lma>
    addi	a5,gp,1088 # ffb00c30 <__fw_export_ldm_end>
    beq	a4,a5,4d90 <.L7>
    addi	a2,gp,1088 # ffb00c30 <__fw_export_ldm_end>
    sub	a2,a2,a5
    li	a1,8
    srai	a3,a2,0x2
    bge	a1,a2,4d74 <.L8>
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
    blt	a6,a3,4d4c <.L9>
    blez	a3,4d90 <.L7>
    lw	a1,0(a4)
    li	a2,2
    sw	a1,0(a5)
    bne	a3,a2,4d90 <.L7>
    lw	a4,4(a4)
    sw	a4,4(a5)
    lui	a5,0xffb30
    lw	t4,520(a5) # ffb30208 <__fw_export_ldm_end+0x2f5d8>
    lw	t1,552(a5)
    lw	a7,516(a5)
    lw	a6,512(a5)
    lw	a2,556(a5)
    lw	a4,1312(zero) # 520 <.LLST127+0x5>
    sw	a6,-1996(gp) # ffb00024 <noc_nonposted_atomics_acked+0x4>
    addi	a0,gp,-1984 # ffb00030 <noc_nonposted_writes_num_issued>
    addi	a1,gp,-1992 # ffb00028 <noc_nonposted_writes_acked>
    sw	a2,-2004(gp) # ffb0001c <noc_posted_writes_num_issued+0x4>
    sw	t4,-1972(gp) # ffb0003c <noc_reads_num_issued+0x4>
    sw	t1,4(a0)
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    sw	a7,4(a1)
    li	a3,128
    addi	a4,a4,96
    beq	a5,a3,4de8 <.L13>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,4ddc <.L11>
    lui	a3,0xffb43
    lw	a4,32(a3) # ffb43020 <__fw_export_ldm_end+0x423f0>
    zext.h	a4,a4
    lw	a5,40(a3)
    zext.h	a5,a5
    beq	a4,a5,4df4 <.L12>
    lw	a5,-2016(gp) # ffb00010 <crta_l1_base>
    lw	a6,0(a5)
    lui	a2,0xffb00
    lw	t1,-1492(gp) # ffb0021c <bank_to_dram_offset>
    lhu	a5,-1946(gp) # ffb00056 <dram_bank_to_noc_xy+0xe>
    addi	a2,a2,1068 # ffb0042c <cb_interface>
    lw	a7,112(a2)
    slli	a3,a5,0x4
    lui	a4,0xffb30
    add	a6,a6,t1
    lw	a5,64(a4) # ffb30040 <__fw_export_ldm_end+0x2f410>
    bnez	a5,4e28 <.L14>
    lui	a5,0x2
    addi	a5,a5,146 # 2092 <.LASF743+0x3>
    sw	a5,28(a4)
    sw	a7,0(a4)
    sw	a6,12(a4)
    sw	zero,16(a4)
    lw	a6,4(a0)
    srli	a5,a3,0x4
    lui	a7,0x1
    lw	a3,4(a1)
    sw	a5,20(a4)
    addi	a5,a7,-2048 # 800 <.LLST184+0x51>
    sw	a5,32(a4)
    addi	a3,a3,1
    addi	a5,a6,1
    sw	a5,4(a0)
    li	a6,1
    sw	a3,4(a1)
    sw	a6,64(a4)
    lui	a4,0xffb30
    lw	a5,516(a4) # ffb30204 <__fw_export_ldm_end+0x2f5d4>
    bne	a5,a3,4e80 <.L15>
    fence
    lui	a3,0xffb43
    lw	a1,112(a2)
    lw	a5,104(a2)
    lw	a4,32(a3) # ffb43020 <__fw_export_ldm_end+0x423f0>
    add	a5,a5,a1
    addi	a4,a4,1
    lw	a1,100(a2)
    sw	a5,112(a2)
    sw	a4,32(a3)
    bne	a5,a1,4ec0 <.L16>
    lw	a4,96(a2)
    sub	a5,a5,a4
    sw	a5,112(a2)
    li	a0,0
    ret
    mv	a5,a3
    j	4d18 <.L4>
