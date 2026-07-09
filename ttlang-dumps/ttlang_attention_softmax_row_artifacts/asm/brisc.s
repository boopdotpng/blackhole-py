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
    bltu	a4,a3,4ee4 <.L19>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,4d24 <.L5>
    sw	zero,-8(a5)
    auipc	a4,0x0
    addi	a4,a4,456 # 4eec <__kernel_data_lma>
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
    lw	a6,552(a5)
    lw	a0,516(a5)
    lw	a1,512(a5)
    lw	a2,556(a5)
    lw	a4,1312(zero) # 520 <.LLST112+0x5>
    sw	a1,-1996(gp) # ffb00024 <noc_nonposted_atomics_acked+0x4>
    addi	t1,gp,-1984 # ffb00030 <noc_nonposted_writes_num_issued>
    addi	a7,gp,-1992 # ffb00028 <noc_nonposted_writes_acked>
    sw	a2,-2004(gp) # ffb0001c <noc_posted_writes_num_issued+0x4>
    sw	t4,-1972(gp) # ffb0003c <noc_reads_num_issued+0x4>
    sw	a6,4(t1)
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    sw	a0,4(a7)
    li	a3,128
    addi	a4,a4,96
    beq	a5,a3,4de8 <.L13>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,4ddc <.L11>
    lui	a4,0xffb42
    lw	a2,32(a4) # ffb42020 <__fw_export_ldm_end+0x413f0>
    li	a3,3
    lw	a5,40(a4)
    sub	a5,a5,a2
    zext.h	a5,a5
    bgeu	a3,a5,4df4 <.L12>
    lw	a5,-2016(gp) # ffb00010 <crta_l1_base>
    lui	t4,0xffb00
    lw	t2,0(a5)
    addi	t4,t4,1068 # ffb0042c <cb_interface>
    addi	a2,gp,-1960 # ffb00048 <dram_bank_to_noc_xy>
    lui	t5,0x2
    lw	a6,80(t4)
    addi	t0,a2,8
    addi	a0,gp,-1492 # ffb0021c <bank_to_dram_offset>
    addi	t5,t5,146 # 2092 <.LASF1008+0x2b>
    lui	a4,0xffb30
    lui	t3,0x1
    li	t6,1
    lhu	a3,14(a2)
    lw	a1,0(a0)
    slli	a3,a3,0x4
    add	a1,t2,a1
    lw	a5,64(a4) # ffb30040 <__fw_export_ldm_end+0x2f410>
    bnez	a5,4e48 <.L14>
    sw	t5,28(a4)
    sw	a6,0(a4)
    sw	a1,12(a4)
    sw	zero,16(a4)
    srli	a3,a3,0x4
    lw	a1,4(t1)
    lw	a5,4(a7)
    sw	a3,20(a4)
    sw	t3,32(a4)
    sw	t6,64(a4)
    addi	a3,a1,1
    addi	a5,a5,1
    addi	a2,a2,2
    sw	a3,4(t1)
    sw	a5,4(a7)
    addi	a0,a0,4
    add	a6,a6,t3
    bne	t0,a2,4e38 <.L15>
    lui	a3,0xffb30
    lw	a4,516(a3) # ffb30204 <__fw_export_ldm_end+0x2f5d4>
    bne	a4,a5,4e9c <.L16>
    fence
    lui	a3,0xffb42
    lw	a4,32(a3) # ffb42020 <__fw_export_ldm_end+0x413f0>
    lw	a1,80(t4)
    lw	a5,72(t4)
    addi	a4,a4,4
    lw	a2,68(t4)
    sh2add	a5,a5,a1
    sw	a4,32(a3)
    sw	a5,80(t4)
    bne	a5,a2,4edc <.L17>
    lw	a4,64(t4)
    sub	a5,a5,a4
    sw	a5,80(t4)
    li	a0,0
    ret
    mv	a5,a3
    j	4d18 <.L4>
