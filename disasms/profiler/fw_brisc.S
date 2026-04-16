
/tmp/tt-disasm-fw_brisc-zw3biy1e/out.elf:     file format elf32-littleriscv


Disassembly of section .text:

00003840 <_start>:
    3840:	ffb001b7          	lui	gp,0xffb00
    3844:	7f018193          	addi	gp,gp,2032 # ffb007f0 <__global_pointer$>
    3848:	ffb02137          	lui	sp,0xffb02
    384c:	ff010113          	addi	sp,sp,-16 # ffb01ff0 <__fw_export_ldm_end+0x1750>
    3850:	00810513          	addi	a0,sp,8
    3854:	00a12023          	sw	a0,0(sp)
    3858:	00012223          	sw	zero,4(sp)
    385c:	00912423          	sw	s1,8(sp)
    3860:	00012623          	sw	zero,12(sp)
    3864:	00100513          	li	a0,1
    3868:	00010593          	mv	a1,sp
    386c:	00000613          	li	a2,0
    3870:	008000ef          	jal	3878 <main>
    3874:	2b10106f          	j	5324 <exit>

00003878 <main>:
    3878:	fa010113          	addi	sp,sp,-96
    387c:	04112e23          	sw	ra,92(sp)
    3880:	04812c23          	sw	s0,88(sp)
    3884:	04912a23          	sw	s1,84(sp)
    3888:	05212823          	sw	s2,80(sp)
    388c:	05312623          	sw	s3,76(sp)
    3890:	05412423          	sw	s4,72(sp)
    3894:	05512223          	sw	s5,68(sp)
    3898:	05612023          	sw	s6,64(sp)
    389c:	03712e23          	sw	s7,60(sp)
    38a0:	03812c23          	sw	s8,56(sp)
    38a4:	03912a23          	sw	s9,52(sp)
    38a8:	03a12823          	sw	s10,48(sp)
    38ac:	03b12623          	sw	s11,44(sp)
    38b0:	00200313          	li	t1,2
    38b4:	7c032073          	csrs	0x7c0,t1
    38b8:	00100313          	li	t1,1
    38bc:	01231313          	slli	t1,t1,0x12
    38c0:	0ff0000f          	fence
    38c4:	7c032073          	csrs	0x7c0,t1
    38c8:	00200313          	li	t1,2
    38cc:	7c033073          	csrc	0x7c0,t1
    38d0:	0ff0000f          	fence
    38d4:	0ff0000f          	fence
    38d8:	00800313          	li	t1,8
    38dc:	7c032073          	csrs	0x7c0,t1
    38e0:	13d010ef          	jal	521c <_Z7do_crt1U11rvtt_l1_ptrPm.constprop.0>
    38e4:	189010ef          	jal	526c <_Z19noc_bank_table_inity.constprop.0>
    38e8:	1f1010ef          	jal	52d8 <_Z38noc_worker_logical_to_virtual_map_inity.constprop.0>
    38ec:	06002623          	sw	zero,108(zero) # 6c <_start-0x37d4>
    38f0:	84018823          	sb	zero,-1968(gp) # ffb00040 <noc_index>
    38f4:	000017b7          	lui	a5,0x1
    38f8:	9a07c703          	lbu	a4,-1632(a5) # 9a0 <_start-0x2ea0>
    38fc:	06078793          	addi	a5,a5,96
    3900:	ffb22437          	lui	s0,0xffb22
    3904:	83018a13          	addi	s4,gp,-2000 # ffb00020 <noc_reads_num_issued>
    3908:	82818a93          	addi	s5,gp,-2008 # ffb00018 <noc_nonposted_writes_num_issued>
    390c:	82018b13          	addi	s6,gp,-2016 # ffb00010 <noc_nonposted_writes_acked>
    3910:	83c18b93          	addi	s7,gp,-1988 # ffb0002c <noc_nonposted_atomics_acked>
    3914:	82e18ca3          	sb	a4,-1991(gp) # ffb00029 <my_logical_x_>
    3918:	9417c783          	lbu	a5,-1727(a5)
    391c:	84818913          	addi	s2,gp,-1976 # ffb00038 <noc_posted_writes_num_issued>
    3920:	06000d93          	li	s11,96
    3924:	82f18c23          	sb	a5,-1992(gp) # ffb00028 <my_logical_y_>
    3928:	129000ef          	jal	4250 <_Z9risc_initv>
    392c:	770010ef          	jal	509c <_Z12device_setupv>
    3930:	06002023          	sw	zero,96(zero) # 60 <_start-0x37e0>
    3934:	074010ef          	jal	49a8 <_Z21deassert_ncrisc_triscv>
    3938:	0cc010ef          	jal	4a04 <_Z17wait_ncrisc_triscv>
    393c:	360009a3          	sb	zero,883(zero) # 373 <_start-0x34cd>
    3940:	ffb20637          	lui	a2,0xffb20
    3944:	14862703          	lw	a4,328(a2) # ffb20148 <__stack_top+0x1e148>
    3948:	00062223          	sw	zero,4(a2)
    394c:	00675793          	srli	a5,a4,0x6
    3950:	03f7f793          	andi	a5,a5,63
    3954:	03f77713          	andi	a4,a4,63
    3958:	00471713          	slli	a4,a4,0x4
    395c:	00a79793          	slli	a5,a5,0xa
    3960:	00e7e7b3          	or	a5,a5,a4
    3964:	0047d793          	srli	a5,a5,0x4
    3968:	00f62423          	sw	a5,8(a2)
    396c:	ffb21737          	lui	a4,0xffb21
    3970:	00072223          	sw	zero,4(a4) # ffb21004 <__stack_top+0x1f004>
    3974:	00f72423          	sw	a5,8(a4)
    3978:	00400513          	li	a0,4
    397c:	80a42623          	sw	a0,-2036(s0) # ffb2180c <__stack_top+0x1f80c>
    3980:	80042823          	sw	zero,-2032(s0)
    3984:	000026b7          	lui	a3,0x2
    3988:	80f42a23          	sw	a5,-2028(s0)
    398c:	09068693          	addi	a3,a3,144 # 2090 <_start-0x17b0>
    3990:	80d72e23          	sw	a3,-2020(a4)
    3994:	80072823          	sw	zero,-2032(a4)
    3998:	80f72a23          	sw	a5,-2028(a4)
    399c:	ffb305b7          	lui	a1,0xffb30
    39a0:	1485a703          	lw	a4,328(a1) # ffb30148 <__stack_top+0x2e148>
    39a4:	0005a223          	sw	zero,4(a1)
    39a8:	00675793          	srli	a5,a4,0x6
    39ac:	03f7f793          	andi	a5,a5,63
    39b0:	03f77713          	andi	a4,a4,63
    39b4:	00471713          	slli	a4,a4,0x4
    39b8:	00a79793          	slli	a5,a5,0xa
    39bc:	00e7e7b3          	or	a5,a5,a4
    39c0:	0047d793          	srli	a5,a5,0x4
    39c4:	00f5a423          	sw	a5,8(a1)
    39c8:	ffb31737          	lui	a4,0xffb31
    39cc:	00072223          	sw	zero,4(a4) # ffb31004 <__stack_top+0x2f004>
    39d0:	00f72423          	sw	a5,8(a4)
    39d4:	ffb325b7          	lui	a1,0xffb32
    39d8:	80a5a623          	sw	a0,-2036(a1) # ffb3180c <__stack_top+0x2f80c>
    39dc:	8005a823          	sw	zero,-2032(a1)
    39e0:	80f5aa23          	sw	a5,-2028(a1)
    39e4:	80d72e23          	sw	a3,-2020(a4)
    39e8:	80072823          	sw	zero,-2032(a4)
    39ec:	80f72a23          	sw	a5,-2028(a4)
    39f0:	20862503          	lw	a0,520(a2)
    39f4:	22862583          	lw	a1,552(a2)
    39f8:	20462683          	lw	a3,516(a2)
    39fc:	20062703          	lw	a4,512(a2)
    3a00:	22c62783          	lw	a5,556(a2)
    3a04:	00aa2023          	sw	a0,0(s4)
    3a08:	00baa023          	sw	a1,0(s5)
    3a0c:	00db2023          	sw	a3,0(s6)
    3a10:	00eba023          	sw	a4,0(s7)
    3a14:	00f92023          	sw	a5,0(s2)
    3a18:	004010ef          	jal	4a1c <_Z26trigger_sync_register_initv>
    3a1c:	8101a783          	lw	a5,-2032(gp) # ffb00000 <_ZL16subordinate_sync>
    3a20:	8401aa23          	sw	zero,-1964(gp) # ffb00044 <_ZN15kernel_profiler10traceCountE>
    3a24:	00f12623          	sw	a5,12(sp)
    3a28:	ffb707b7          	lui	a5,0xffb70
    3a2c:	000025b7          	lui	a1,0x2
    3a30:	43878c93          	addi	s9,a5,1080 # ffb70438 <__stack_top+0x6e438>
    3a34:	84040c13          	addi	s8,s0,-1984
    3a38:	04000493          	li	s1,64
    3a3c:	81c40813          	addi	a6,s0,-2020
    3a40:	08a58593          	addi	a1,a1,138 # 208a <_start-0x17b6>
    3a44:	80040893          	addi	a7,s0,-2048
    3a48:	80440313          	addi	t1,s0,-2044
    3a4c:	80840e13          	addi	t3,s0,-2040
    3a50:	82040e93          	addi	t4,s0,-2016
    3a54:	00100f13          	li	t5,1
    3a58:	0e000f93          	li	t6,224
    3a5c:	0f000293          	li	t0,240
    3a60:	3a002783          	lw	a5,928(zero) # 3a0 <_start-0x34a0>
    3a64:	08000693          	li	a3,128
    3a68:	00279793          	slli	a5,a5,0x2
    3a6c:	37078793          	addi	a5,a5,880
    3a70:	0037c783          	lbu	a5,3(a5)
    3a74:	0ff7f713          	zext.b	a4,a5
    3a78:	02d78063          	beq	a5,a3,3a98 <main+0x220>
    3a7c:	06c02783          	lw	a5,108(zero) # 6c <_start-0x37d4>
    3a80:	00178793          	addi	a5,a5,1
    3a84:	03b787b3          	mul	a5,a5,s11
    3a88:	06078793          	addi	a5,a5,96
    3a8c:	00f7c783          	lbu	a5,15(a5)
    3a90:	60479793          	sext.b	a5,a5
    3a94:	4607d463          	bgez	a5,3efc <.NO_CB1960+0x228>
    3a98:	161000ef          	jal	43f8 <_ZN15kernel_profiler13init_profilerEttt.constprop.0>
    3a9c:	00000513          	li	a0,0
    3aa0:	235000ef          	jal	44d4 <_ZN15kernel_profiler12get_const_idEmNS_11PacketTypesE.constprop.0>
    3aa4:	00c51513          	slli	a0,a0,0xc
    3aa8:	ffb12637          	lui	a2,0xffb12
    3aac:	1f462703          	lw	a4,500(a2) # ffb121f4 <__stack_top+0x101f4>
    3ab0:	000017b7          	lui	a5,0x1
    3ab4:	fff78693          	addi	a3,a5,-1 # fff <_start-0x2841>
    3ab8:	00d77733          	and	a4,a4,a3
    3abc:	00e56533          	or	a0,a0,a4
    3ac0:	80000737          	lui	a4,0x80000
    3ac4:	00e56533          	or	a0,a0,a4
    3ac8:	a4a7a823          	sw	a0,-1456(a5)
    3acc:	1f062703          	lw	a4,496(a2)
    3ad0:	a4e7aa23          	sw	a4,-1452(a5)
    3ad4:	06c02703          	lw	a4,108(zero) # 6c <_start-0x37d4>
    3ad8:	02ed84b3          	mul	s1,s11,a4
    3adc:	00e12423          	sw	a4,8(sp)
    3ae0:	0bc4a703          	lw	a4,188(s1)
    3ae4:	07048493          	addi	s1,s1,112
    3ae8:	00173713          	seqz	a4,a4
    3aec:	a0e7a623          	sw	a4,-1524(a5)
    3af0:	0484a703          	lw	a4,72(s1)
    3af4:	a4e7a623          	sw	a4,-1460(a5)
    3af8:	24e7a623          	sw	a4,588(a5)
    3afc:	000027b7          	lui	a5,0x2
    3b00:	a4e7a623          	sw	a4,-1460(a5) # 1a4c <_start-0x1df4>
    3b04:	24e7a623          	sw	a4,588(a5)
    3b08:	000037b7          	lui	a5,0x3
    3b0c:	a4e7a623          	sw	a4,-1460(a5) # 2a4c <_start-0xdf4>
    3b10:	04c4a503          	lw	a0,76(s1)
    3b14:	00257793          	andi	a5,a0,2
    3b18:	48079c63          	bnez	a5,3fb0 <.NO_CB1960+0x2dc>
    3b1c:	06c02783          	lw	a5,108(zero) # 6c <_start-0x37d4>
    3b20:	ffb01737          	lui	a4,0xffb01
    3b24:	06870713          	addi	a4,a4,104 # ffb01068 <__fw_export_ldm_end+0x7c8>
    3b28:	03b787b3          	mul	a5,a5,s11
    3b2c:	0707ac03          	lw	s8,112(a5)
    3b30:	07c7d683          	lhu	a3,124(a5)
    3b34:	0747a603          	lw	a2,116(a5)
    3b38:	06078793          	addi	a5,a5,96
    3b3c:	018686b3          	add	a3,a3,s8
    3b40:	82d72223          	sw	a3,-2012(a4)
    3b44:	01e7d683          	lhu	a3,30(a5)
    3b48:	00c686b3          	add	a3,a3,a2
    3b4c:	82d72423          	sw	a3,-2008(a4)
    3b50:	0187a603          	lw	a2,24(a5)
    3b54:	0207d683          	lhu	a3,32(a5)
    3b58:	00c686b3          	add	a3,a3,a2
    3b5c:	82d72623          	sw	a3,-2004(a4)
    3b60:	0267d703          	lhu	a4,38(a5)
    3b64:	0287d783          	lhu	a5,40(a5)
    3b68:	01870733          	add	a4,a4,s8
    3b6c:	80e1ae23          	sw	a4,-2020(gp) # ffb0000c <rta_l1_base>
    3b70:	018787b3          	add	a5,a5,s8
    3b74:	80f1ac23          	sw	a5,-2024(gp) # ffb00008 <crta_l1_base>
    3b78:	ffef07b7          	lui	a5,0xffef0
    3b7c:	01f00713          	li	a4,31
    3b80:	2ee7a223          	sw	a4,740(a5) # ffef02e4 <__instrn_buffer+0xb02e4>
    3b84:	00a12823          	sw	a0,16(sp)
    3b88:	635000ef          	jal	49bc <_Z10run_triscsm>
    3b8c:	0444c603          	lbu	a2,68(s1)
    3b90:	8391c783          	lbu	a5,-1991(gp) # ffb00029 <my_logical_x_>
    3b94:	0454c583          	lbu	a1,69(s1)
    3b98:	05c4c703          	lbu	a4,92(s1)
    3b9c:	0ff67613          	zext.b	a2,a2
    3ba0:	40e787b3          	sub	a5,a5,a4
    3ba4:	80f18b23          	sb	a5,-2026(gp) # ffb00006 <my_relative_x_>
    3ba8:	05d4c703          	lbu	a4,93(s1)
    3bac:	8381c783          	lbu	a5,-1992(gp) # ffb00028 <my_logical_y_>
    3bb0:	40e787b3          	sub	a5,a5,a4
    3bb4:	80f18aa3          	sb	a5,-2027(gp) # ffb00005 <my_relative_y_>
    3bb8:	84c18823          	sb	a2,-1968(gp) # ffb00040 <noc_index>
    3bbc:	8141c783          	lbu	a5,-2028(gp) # ffb00004 <prev_noc_mode>
    3bc0:	01012503          	lw	a0,16(sp)
    3bc4:	0ff5fc93          	zext.b	s9,a1
    3bc8:	ffb20737          	lui	a4,0xffb20
    3bcc:	4a059263          	bnez	a1,4070 <.NO_CB1960+0x39c>
    3bd0:	3e079863          	bnez	a5,3fc0 <.NO_CB1960+0x2ec>
    3bd4:	ffb20737          	lui	a4,0xffb20
    3bd8:	01061793          	slli	a5,a2,0x10
    3bdc:	20870593          	addi	a1,a4,520 # ffb20208 <__stack_top+0x1e208>
    3be0:	00b785b3          	add	a1,a5,a1
    3be4:	0005a883          	lw	a7,0(a1)
    3be8:	22870593          	addi	a1,a4,552
    3bec:	00b785b3          	add	a1,a5,a1
    3bf0:	0005a803          	lw	a6,0(a1)
    3bf4:	20470593          	addi	a1,a4,516
    3bf8:	00b785b3          	add	a1,a5,a1
    3bfc:	0005ae03          	lw	t3,0(a1)
    3c00:	20070593          	addi	a1,a4,512
    3c04:	22c70713          	addi	a4,a4,556
    3c08:	00b785b3          	add	a1,a5,a1
    3c0c:	00e787b3          	add	a5,a5,a4
    3c10:	0005a583          	lw	a1,0(a1)
    3c14:	0007a703          	lw	a4,0(a5)
    3c18:	214647b3          	sh2add	a5,a2,s4
    3c1c:	0117a023          	sw	a7,0(a5)
    3c20:	215647b3          	sh2add	a5,a2,s5
    3c24:	0107a023          	sw	a6,0(a5)
    3c28:	216647b3          	sh2add	a5,a2,s6
    3c2c:	01c7a023          	sw	t3,0(a5)
    3c30:	217647b3          	sh2add	a5,a2,s7
    3c34:	00b7a023          	sw	a1,0(a5)
    3c38:	212647b3          	sh2add	a5,a2,s2
    3c3c:	00e7a023          	sw	a4,0(a5)
    3c40:	00300713          	li	a4,3
    3c44:	0124d783          	lhu	a5,18(s1)
    3c48:	00e12e23          	sw	a4,28(sp)
    3c4c:	0807c7b3          	zext.h	a5,a5
    3c50:	00c12c23          	sw	a2,24(sp)
    3c54:	00a12823          	sw	a0,16(sp)
    3c58:	81918a23          	sb	s9,-2028(gp) # ffb00004 <prev_noc_mode>
    3c5c:	00f12a23          	sw	a5,20(sp)
    3c60:	58d000ef          	jal	49ec <_Z29start_ncrisc_kernel_run_earlym>
    3c64:	01012503          	lw	a0,16(sp)
    3c68:	01812603          	lw	a2,24(sp)
    3c6c:	00157513          	andi	a0,a0,1
    3c70:	01c12703          	lw	a4,28(sp)
    3c74:	50050063          	beqz	a0,4174 <.NO_CB1960+0x4a0>
    3c78:	01412783          	lw	a5,20(sp)
    3c7c:	0404a583          	lw	a1,64(s1)
    3c80:	018787b3          	add	a5,a5,s8
    3c84:	87818513          	addi	a0,gp,-1928 # ffb00068 <cb_interface>
    3c88:	0580006f          	j	3ce0 <.NO_CB1960+0xc>
    3c8c:	0047a683          	lw	a3,4(a5)
    3c90:	0007a603          	lw	a2,0(a5)
    3c94:	0087a803          	lw	a6,8(a5)
    3c98:	00c7a883          	lw	a7,12(a5)
    3c9c:	0015d593          	srli	a1,a1,0x1
    3ca0:	0015f293          	andi	t0,a1,1
    3ca4:	00052c23          	sw	zero,24(a0)
    3ca8:	01078793          	addi	a5,a5,16
    3cac:	00d52023          	sw	a3,0(a0)
    3cb0:	00d606b3          	add	a3,a2,a3
    3cb4:	00d52223          	sw	a3,4(a0)
    3cb8:	00c52a23          	sw	a2,20(a0)
    3cbc:	01052623          	sw	a6,12(a0)
    3cc0:	00c52823          	sw	a2,16(a0)
    3cc4:	01152423          	sw	a7,8(a0)
    3cc8:	02050513          	addi	a0,a0,32
    3ccc:	fc0290e3          	bnez	t0,3c8c <main+0x414>
    3cd0:	00058e63          	beqz	a1,3cec <.NO_CB1960+0x18>

00003cd4 <.NO_CB1960>:
    3cd4:	01078793          	addi	a5,a5,16
    3cd8:	02050513          	addi	a0,a0,32
    3cdc:	0015d593          	srli	a1,a1,0x1
    3ce0:	0015f293          	andi	t0,a1,1
    3ce4:	fa0294e3          	bnez	t0,3c8c <main+0x414>
    3ce8:	fe0596e3          	bnez	a1,3cd4 <.NO_CB1960>
    3cec:	0144d503          	lhu	a0,20(s1)
    3cf0:	0464c583          	lbu	a1,70(s1)
    3cf4:	8501c603          	lbu	a2,-1968(gp) # ffb00040 <noc_index>
    3cf8:	0ff5f593          	zext.b	a1,a1
    3cfc:	000c8693          	mv	a3,s9
    3d00:	01850533          	add	a0,a0,s8
    3d04:	00c12a23          	sw	a2,20(sp)
    3d08:	00b12823          	sw	a1,16(sp)
    3d0c:	555000ef          	jal	4a60 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0>
    3d10:	01012583          	lw	a1,16(sp)
    3d14:	01412503          	lw	a0,20(sp)
    3d18:	515000ef          	jal	4a2c <_Z33barrier_remote_cb_interface_setuphm>
    3d1c:	02c4a783          	lw	a5,44(s1)
    3d20:	018787b3          	add	a5,a5,s8
    3d24:	000780e7          	jalr	a5
    3d28:	4dd000ef          	jal	4a04 <_Z17wait_ncrisc_triscv>
    3d2c:	4f1000ef          	jal	4a1c <_Z26trigger_sync_register_initv>
    3d30:	00100793          	li	a5,1
    3d34:	06fc9a63          	bne	s9,a5,3da8 <.NO_CB1960+0xd4>
    3d38:	8501c783          	lbu	a5,-1968(gp) # ffb00040 <noc_index>
    3d3c:	ffb206b7          	lui	a3,0xffb20
    3d40:	01079713          	slli	a4,a5,0x10
    3d44:	20868613          	addi	a2,a3,520 # ffb20208 <__stack_top+0x1e208>
    3d48:	00c70633          	add	a2,a4,a2
    3d4c:	00062583          	lw	a1,0(a2)
    3d50:	22868613          	addi	a2,a3,552
    3d54:	00c70633          	add	a2,a4,a2
    3d58:	00062503          	lw	a0,0(a2)
    3d5c:	20468613          	addi	a2,a3,516
    3d60:	00c70633          	add	a2,a4,a2
    3d64:	00062803          	lw	a6,0(a2)
    3d68:	20068613          	addi	a2,a3,512
    3d6c:	22c68693          	addi	a3,a3,556
    3d70:	00c70633          	add	a2,a4,a2
    3d74:	00d70733          	add	a4,a4,a3
    3d78:	2147c6b3          	sh2add	a3,a5,s4
    3d7c:	00062603          	lw	a2,0(a2)
    3d80:	00072703          	lw	a4,0(a4)
    3d84:	00b6a023          	sw	a1,0(a3)
    3d88:	2157c6b3          	sh2add	a3,a5,s5
    3d8c:	00a6a023          	sw	a0,0(a3)
    3d90:	2167c6b3          	sh2add	a3,a5,s6
    3d94:	0106a023          	sw	a6,0(a3)
    3d98:	2177c6b3          	sh2add	a3,a5,s7
    3d9c:	2127c7b3          	sh2add	a5,a5,s2
    3da0:	00c6a023          	sw	a2,0(a3)
    3da4:	00e7a023          	sw	a4,0(a5)
    3da8:	3a002783          	lw	a5,928(zero) # 3a0 <_start-0x34a0>
    3dac:	00279793          	slli	a5,a5,0x2
    3db0:	360789a3          	sb	zero,883(a5)
    3db4:	02a4c703          	lbu	a4,42(s1)
    3db8:	06078793          	addi	a5,a5,96
    3dbc:	0c071e63          	bnez	a4,3e98 <.NO_CB1960+0x1c4>
    3dc0:	0404a623          	sw	zero,76(s1)
    3dc4:	04048fa3          	sb	zero,95(s1)
    3dc8:	3107a783          	lw	a5,784(a5)
    3dcc:	8501c603          	lbu	a2,-1968(gp) # ffb00040 <noc_index>
    3dd0:	84040593          	addi	a1,s0,-1984
    3dd4:	0107d693          	srli	a3,a5,0x10
    3dd8:	0087d713          	srli	a4,a5,0x8
    3ddc:	0ff6f693          	zext.b	a3,a3
    3de0:	0ff77713          	zext.b	a4,a4
    3de4:	00471713          	slli	a4,a4,0x4
    3de8:	00a69693          	slli	a3,a3,0xa
    3dec:	00e6e6b3          	or	a3,a3,a4
    3df0:	0ff7f793          	zext.b	a5,a5
    3df4:	ffb70737          	lui	a4,0xffb70
    3df8:	00c79793          	slli	a5,a5,0xc
    3dfc:	43870713          	addi	a4,a4,1080 # ffb70438 <__stack_top+0x6e438>
    3e00:	00e78833          	add	a6,a5,a4
    3e04:	01061793          	slli	a5,a2,0x10
    3e08:	00b785b3          	add	a1,a5,a1
    3e0c:	0005a703          	lw	a4,0(a1)
    3e10:	fe071ee3          	bnez	a4,3e0c <.NO_CB1960+0x138>
    3e14:	ffb22737          	lui	a4,0xffb22
    3e18:	82870713          	addi	a4,a4,-2008 # ffb21828 <__stack_top+0x1f828>
    3e1c:	00e78733          	add	a4,a5,a4
    3e20:	04000513          	li	a0,64
    3e24:	00a72023          	sw	a0,0(a4)
    3e28:	81c40713          	addi	a4,s0,-2020
    3e2c:	00002537          	lui	a0,0x2
    3e30:	00e78733          	add	a4,a5,a4
    3e34:	08a50513          	addi	a0,a0,138 # 208a <_start-0x17b6>
    3e38:	00a72023          	sw	a0,0(a4)
    3e3c:	80040713          	addi	a4,s0,-2048
    3e40:	00e78733          	add	a4,a5,a4
    3e44:	01072023          	sw	a6,0(a4)
    3e48:	80440713          	addi	a4,s0,-2044
    3e4c:	00e78733          	add	a4,a5,a4
    3e50:	00072023          	sw	zero,0(a4)
    3e54:	80840713          	addi	a4,s0,-2040
    3e58:	00e78733          	add	a4,a5,a4
    3e5c:	0046d693          	srli	a3,a3,0x4
    3e60:	00d72023          	sw	a3,0(a4)
    3e64:	82040713          	addi	a4,s0,-2016
    3e68:	00e787b3          	add	a5,a5,a4
    3e6c:	0007a023          	sw	zero,0(a5)
    3e70:	00100793          	li	a5,1
    3e74:	00f5a023          	sw	a5,0(a1)
    3e78:	212647b3          	sh2add	a5,a2,s2
    3e7c:	0007a703          	lw	a4,0(a5)
    3e80:	00170713          	addi	a4,a4,1
    3e84:	00e7a023          	sw	a4,0(a5)
    3e88:	00812783          	lw	a5,8(sp)
    3e8c:	00178c13          	addi	s8,a5,1
    3e90:	007c7c13          	andi	s8,s8,7
    3e94:	07802623          	sw	s8,108(zero) # 6c <_start-0x37d4>
    3e98:	00100513          	li	a0,1
    3e9c:	638000ef          	jal	44d4 <_ZN15kernel_profiler12get_const_idEmNS_11PacketTypesE.constprop.0>
    3ea0:	00c51513          	slli	a0,a0,0xc
    3ea4:	ffb126b7          	lui	a3,0xffb12
    3ea8:	1f46a703          	lw	a4,500(a3) # ffb121f4 <__stack_top+0x101f4>
    3eac:	000017b7          	lui	a5,0x1
    3eb0:	fff78613          	addi	a2,a5,-1 # fff <_start-0x2841>
    3eb4:	00c77733          	and	a4,a4,a2
    3eb8:	00e56533          	or	a0,a0,a4
    3ebc:	80000737          	lui	a4,0x80000
    3ec0:	00e56533          	or	a0,a0,a4
    3ec4:	a4a7ac23          	sw	a0,-1448(a5)
    3ec8:	1f06a703          	lw	a4,496(a3)
    3ecc:	a4e7ae23          	sw	a4,-1444(a5)
    3ed0:	618000ef          	jal	44e8 <_ZN15kernel_profiler15finish_profilerEv>
    3ed4:	b55ff06f          	j	3a28 <main+0x1b0>
    3ed8:	01f70e63          	beq	a4,t6,3ef4 <.NO_CB1960+0x220>
    3edc:	b85712e3          	bne	a4,t0,3a60 <main+0x1e8>
    3ee0:	06002623          	sw	zero,108(zero) # 6c <_start-0x37d4>
    3ee4:	8541a783          	lw	a5,-1964(gp) # ffb00044 <_ZN15kernel_profiler10traceCountE>
    3ee8:	00178793          	addi	a5,a5,1
    3eec:	84f1aa23          	sw	a5,-1964(gp) # ffb00044 <_ZN15kernel_profiler10traceCountE>
    3ef0:	01c0006f          	j	3f0c <.NO_CB1960+0x238>
    3ef4:	06002623          	sw	zero,108(zero) # 6c <_start-0x37d4>
    3ef8:	b69ff06f          	j	3a60 <main+0x1e8>
    3efc:	0ff0000f          	fence
    3f00:	0c000793          	li	a5,192
    3f04:	fcf71ae3          	bne	a4,a5,3ed8 <.NO_CB1960+0x204>
    3f08:	06002623          	sw	zero,108(zero) # 6c <_start-0x37d4>
    3f0c:	3a002783          	lw	a5,928(zero) # 3a0 <_start-0x34a0>
    3f10:	00279713          	slli	a4,a5,0x2
    3f14:	37072683          	lw	a3,880(a4) # 80000370 <__fw_export_text_end+0x7fffb040>
    3f18:	00279793          	slli	a5,a5,0x2
    3f1c:	0106d713          	srli	a4,a3,0x10
    3f20:	0086d613          	srli	a2,a3,0x8
    3f24:	0ff77713          	zext.b	a4,a4
    3f28:	0ff67613          	zext.b	a2,a2
    3f2c:	00461613          	slli	a2,a2,0x4
    3f30:	360789a3          	sb	zero,883(a5)
    3f34:	00a71713          	slli	a4,a4,0xa
    3f38:	00c76733          	or	a4,a4,a2
    3f3c:	8501c603          	lbu	a2,-1968(gp) # ffb00040 <noc_index>
    3f40:	0ff6f693          	zext.b	a3,a3
    3f44:	00c69693          	slli	a3,a3,0xc
    3f48:	01061793          	slli	a5,a2,0x10
    3f4c:	019686b3          	add	a3,a3,s9
    3f50:	01878533          	add	a0,a5,s8
    3f54:	00052383          	lw	t2,0(a0)
    3f58:	fe039ee3          	bnez	t2,3f54 <.NO_CB1960+0x280>
    3f5c:	ffb223b7          	lui	t2,0xffb22
    3f60:	21264633          	sh2add	a2,a2,s2
    3f64:	82838393          	addi	t2,t2,-2008 # ffb21828 <__stack_top+0x1f828>
    3f68:	007783b3          	add	t2,a5,t2
    3f6c:	0093a023          	sw	s1,0(t2)
    3f70:	010783b3          	add	t2,a5,a6
    3f74:	00b3a023          	sw	a1,0(t2)
    3f78:	011783b3          	add	t2,a5,a7
    3f7c:	00d3a023          	sw	a3,0(t2)
    3f80:	006786b3          	add	a3,a5,t1
    3f84:	0006a023          	sw	zero,0(a3)
    3f88:	00475713          	srli	a4,a4,0x4
    3f8c:	01c786b3          	add	a3,a5,t3
    3f90:	00e6a023          	sw	a4,0(a3)
    3f94:	01d787b3          	add	a5,a5,t4
    3f98:	0007a023          	sw	zero,0(a5)
    3f9c:	01e52023          	sw	t5,0(a0)
    3fa0:	00062783          	lw	a5,0(a2)
    3fa4:	00178793          	addi	a5,a5,1
    3fa8:	00f62023          	sw	a5,0(a2)
    3fac:	ab5ff06f          	j	3a60 <main+0x1e8>
    3fb0:	00c12703          	lw	a4,12(sp)
    3fb4:	00100793          	li	a5,1
    3fb8:	00f70023          	sb	a5,0(a4)
    3fbc:	b61ff06f          	j	3b1c <main+0x2a4>
    3fc0:	14872583          	lw	a1,328(a4)
    3fc4:	00072223          	sw	zero,4(a4)
    3fc8:	0065d793          	srli	a5,a1,0x6
    3fcc:	03f7f793          	andi	a5,a5,63
    3fd0:	03f5f593          	andi	a1,a1,63
    3fd4:	00459593          	slli	a1,a1,0x4
    3fd8:	00a79793          	slli	a5,a5,0xa
    3fdc:	00b7e7b3          	or	a5,a5,a1
    3fe0:	0047d793          	srli	a5,a5,0x4
    3fe4:	00f72423          	sw	a5,8(a4)
    3fe8:	ffb21737          	lui	a4,0xffb21
    3fec:	00072223          	sw	zero,4(a4) # ffb21004 <__stack_top+0x1f004>
    3ff0:	00f72423          	sw	a5,8(a4)
    3ff4:	00400813          	li	a6,4
    3ff8:	81042623          	sw	a6,-2036(s0)
    3ffc:	80042823          	sw	zero,-2032(s0)
    4000:	000025b7          	lui	a1,0x2
    4004:	80f42a23          	sw	a5,-2028(s0)
    4008:	09058593          	addi	a1,a1,144 # 2090 <_start-0x17b0>
    400c:	80b72e23          	sw	a1,-2020(a4)
    4010:	80072823          	sw	zero,-2032(a4)
    4014:	80f72a23          	sw	a5,-2028(a4)
    4018:	ffb308b7          	lui	a7,0xffb30
    401c:	1488a703          	lw	a4,328(a7) # ffb30148 <__stack_top+0x2e148>
    4020:	0008a223          	sw	zero,4(a7)
    4024:	00675793          	srli	a5,a4,0x6
    4028:	03f7f793          	andi	a5,a5,63
    402c:	03f77713          	andi	a4,a4,63
    4030:	00471713          	slli	a4,a4,0x4
    4034:	00a79793          	slli	a5,a5,0xa
    4038:	00e7e7b3          	or	a5,a5,a4
    403c:	0047d793          	srli	a5,a5,0x4
    4040:	00f8a423          	sw	a5,8(a7)
    4044:	ffb31737          	lui	a4,0xffb31
    4048:	00072223          	sw	zero,4(a4) # ffb31004 <__stack_top+0x2f004>
    404c:	00f72423          	sw	a5,8(a4)
    4050:	ffb328b7          	lui	a7,0xffb32
    4054:	8108a623          	sw	a6,-2036(a7) # ffb3180c <__stack_top+0x2f80c>
    4058:	8008a823          	sw	zero,-2032(a7)
    405c:	80f8aa23          	sw	a5,-2028(a7)
    4060:	80b72e23          	sw	a1,-2020(a4)
    4064:	80072823          	sw	zero,-2032(a4)
    4068:	80f72a23          	sw	a5,-2028(a4)
    406c:	b69ff06f          	j	3bd4 <main+0x35c>
    4070:	08fc9863          	bne	s9,a5,4100 <.NO_CB1960+0x42c>
    4074:	ffb20737          	lui	a4,0xffb20
    4078:	20872383          	lw	t2,520(a4) # ffb20208 <__stack_top+0x1e208>
    407c:	ffb307b7          	lui	a5,0xffb30
    4080:	2087a283          	lw	t0,520(a5) # ffb30208 <__stack_top+0x2e208>
    4084:	22872f83          	lw	t6,552(a4)
    4088:	2287af03          	lw	t5,552(a5)
    408c:	20472e83          	lw	t4,516(a4)
    4090:	2047ae03          	lw	t3,516(a5)
    4094:	20072883          	lw	a7,512(a4)
    4098:	2007a803          	lw	a6,512(a5)
    409c:	22c72583          	lw	a1,556(a4)
    40a0:	22c7a703          	lw	a4,556(a5)
    40a4:	000077b7          	lui	a5,0x7
    40a8:	0477a023          	sw	t2,64(a5) # 7040 <__fw_export_text_end+0x1d10>
    40ac:	0607a423          	sw	zero,104(a5)
    40b0:	0407aa23          	sw	zero,84(a5)
    40b4:	0657ae23          	sw	t0,124(a5)
    40b8:	05f7a223          	sw	t6,68(a5)
    40bc:	0607a623          	sw	zero,108(a5)
    40c0:	0407ac23          	sw	zero,88(a5)
    40c4:	09e7a023          	sw	t5,128(a5)
    40c8:	05d7a423          	sw	t4,72(a5)
    40cc:	0607a823          	sw	zero,112(a5)
    40d0:	0407ae23          	sw	zero,92(a5)
    40d4:	09c7a223          	sw	t3,132(a5)
    40d8:	0517a623          	sw	a7,76(a5)
    40dc:	0607aa23          	sw	zero,116(a5)
    40e0:	0607a023          	sw	zero,96(a5)
    40e4:	0907a423          	sw	a6,136(a5)
    40e8:	04b7a823          	sw	a1,80(a5)
    40ec:	0607ac23          	sw	zero,120(a5)
    40f0:	0607a223          	sw	zero,100(a5)
    40f4:	08e7a623          	sw	a4,140(a5)
    40f8:	00100713          	li	a4,1
    40fc:	b49ff06f          	j	3c44 <main+0x3cc>
    4100:	14872583          	lw	a1,328(a4)
    4104:	0065d793          	srli	a5,a1,0x6
    4108:	03f7f793          	andi	a5,a5,63
    410c:	03f5f593          	andi	a1,a1,63
    4110:	00459593          	slli	a1,a1,0x4
    4114:	00a79793          	slli	a5,a5,0xa
    4118:	00b7e7b3          	or	a5,a5,a1
    411c:	0047d793          	srli	a5,a5,0x4
    4120:	ffb215b7          	lui	a1,0xffb21
    4124:	80f5aa23          	sw	a5,-2028(a1) # ffb20814 <__stack_top+0x1e814>
    4128:	00f72423          	sw	a5,8(a4)
    412c:	80f42a23          	sw	a5,-2028(s0)
    4130:	00f5a423          	sw	a5,8(a1)
    4134:	ffb305b7          	lui	a1,0xffb30
    4138:	1485a703          	lw	a4,328(a1) # ffb30148 <__stack_top+0x2e148>
    413c:	00675793          	srli	a5,a4,0x6
    4140:	03f7f793          	andi	a5,a5,63
    4144:	03f77713          	andi	a4,a4,63
    4148:	00471713          	slli	a4,a4,0x4
    414c:	00a79793          	slli	a5,a5,0xa
    4150:	00e7e7b3          	or	a5,a5,a4
    4154:	0047d793          	srli	a5,a5,0x4
    4158:	ffb31737          	lui	a4,0xffb31
    415c:	80f72a23          	sw	a5,-2028(a4) # ffb30814 <__stack_top+0x2e814>
    4160:	00f5a423          	sw	a5,8(a1)
    4164:	ffb325b7          	lui	a1,0xffb32
    4168:	80f5aa23          	sw	a5,-2028(a1) # ffb31814 <__stack_top+0x2f814>
    416c:	00f72423          	sw	a5,8(a4)
    4170:	f05ff06f          	j	4074 <.NO_CB1960+0x3a0>
    4174:	060c9863          	bnez	s9,41e4 <.NO_CB1960+0x510>
    4178:	ffb206b7          	lui	a3,0xffb20
    417c:	01061793          	slli	a5,a2,0x10
    4180:	20868593          	addi	a1,a3,520 # ffb20208 <__stack_top+0x1e208>
    4184:	00b785b3          	add	a1,a5,a1
    4188:	0005a503          	lw	a0,0(a1)
    418c:	22868593          	addi	a1,a3,552
    4190:	00b785b3          	add	a1,a5,a1
    4194:	0005a803          	lw	a6,0(a1)
    4198:	20468593          	addi	a1,a3,516
    419c:	00b785b3          	add	a1,a5,a1
    41a0:	0005a883          	lw	a7,0(a1)
    41a4:	20068593          	addi	a1,a3,512
    41a8:	22c68693          	addi	a3,a3,556
    41ac:	00b785b3          	add	a1,a5,a1
    41b0:	00d787b3          	add	a5,a5,a3
    41b4:	0005a583          	lw	a1,0(a1)
    41b8:	0007a683          	lw	a3,0(a5)
    41bc:	214647b3          	sh2add	a5,a2,s4
    41c0:	00a7a023          	sw	a0,0(a5)
    41c4:	215647b3          	sh2add	a5,a2,s5
    41c8:	0107a023          	sw	a6,0(a5)
    41cc:	216647b3          	sh2add	a5,a2,s6
    41d0:	0117a023          	sw	a7,0(a5)
    41d4:	217647b3          	sh2add	a5,a2,s7
    41d8:	00b7a023          	sw	a1,0(a5)
    41dc:	212647b3          	sh2add	a5,a2,s2
    41e0:	00d7a023          	sw	a3,0(a5)
    41e4:	04c4a783          	lw	a5,76(s1)
    41e8:	02078863          	beqz	a5,4218 <.NO_CB1960+0x544>
    41ec:	0144d503          	lhu	a0,20(s1)
    41f0:	0464c583          	lbu	a1,70(s1)
    41f4:	01850533          	add	a0,a0,s8
    41f8:	0ff5f593          	zext.b	a1,a1
    41fc:	000c8693          	mv	a3,s9
    4200:	00b12823          	sw	a1,16(sp)
    4204:	00c12a23          	sw	a2,20(sp)
    4208:	059000ef          	jal	4a60 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0>
    420c:	01012583          	lw	a1,16(sp)
    4210:	01412503          	lw	a0,20(sp)
    4214:	019000ef          	jal	4a2c <_Z33barrier_remote_cb_interface_setuphm>
    4218:	3a002783          	lw	a5,928(zero) # 3a0 <_start-0x34a0>
    421c:	08000713          	li	a4,128
    4220:	00279793          	slli	a5,a5,0x2
    4224:	37078793          	addi	a5,a5,880
    4228:	0037c683          	lbu	a3,3(a5)
    422c:	aee68ee3          	beq	a3,a4,3d28 <.NO_CB1960+0x54>
    4230:	0ff0000f          	fence
    4234:	ff5ff06f          	j	4228 <.NO_CB1960+0x554>

00004238 <_Z9WRITE_REGmm>:
    4238:	00b52023          	sw	a1,0(a0)
    423c:	00008067          	ret

00004240 <_Z18deassert_all_resetv>:
    4240:	ffb12537          	lui	a0,0xffb12
    4244:	00000593          	li	a1,0
    4248:	1b050513          	addi	a0,a0,432 # ffb121b0 <__stack_top+0x101b0>
    424c:	fedff06f          	j	4238 <_Z9WRITE_REGmm>

00004250 <_Z9risc_initv>:
    4250:	ffb207b7          	lui	a5,0xffb20
    4254:	1487a783          	lw	a5,328(a5) # ffb20148 <__stack_top+0x1e148>
    4258:	03f7f713          	andi	a4,a5,63
    425c:	0067d793          	srli	a5,a5,0x6
    4260:	86e18a23          	sb	a4,-1932(gp) # ffb00064 <my_x>
    4264:	03f7f793          	andi	a5,a5,63
    4268:	86f18823          	sb	a5,-1936(gp) # ffb00060 <my_y>
    426c:	ffb307b7          	lui	a5,0xffb30
    4270:	1487a783          	lw	a5,328(a5) # ffb30148 <__stack_top+0x2e148>
    4274:	87418693          	addi	a3,gp,-1932 # ffb00064 <my_x>
    4278:	03f7f613          	andi	a2,a5,63
    427c:	0067d793          	srli	a5,a5,0x6
    4280:	87018713          	addi	a4,gp,-1936 # ffb00060 <my_y>
    4284:	03f7f793          	andi	a5,a5,63
    4288:	00c680a3          	sb	a2,1(a3)
    428c:	00f700a3          	sb	a5,1(a4)
    4290:	00008067          	ret

00004294 <_Z12ex_push_insnPVmm>:
    4294:	00b52023          	sw	a1,0(a0)
    4298:	00008067          	ret

0000429c <_Z13rmw_cfg_valuemmmm>:
    429c:	00a61633          	sll	a2,a2,a0
    42a0:	00d64633          	xor	a2,a2,a3
    42a4:	00b67633          	and	a2,a2,a1
    42a8:	00d64533          	xor	a0,a2,a3
    42ac:	00008067          	ret

000042b0 <_Z10ex_rmw_cfgmmmmPVm.constprop.0>:
    42b0:	ff010113          	addi	sp,sp,-16
    42b4:	00812423          	sw	s0,8(sp)
    42b8:	00068413          	mv	s0,a3
    42bc:	00c6a683          	lw	a3,12(a3)
    42c0:	00112623          	sw	ra,12(sp)
    42c4:	fd9ff0ef          	jal	429c <_Z13rmw_cfg_valuemmmm>
    42c8:	00a42623          	sw	a0,12(s0)
    42cc:	00c12083          	lw	ra,12(sp)
    42d0:	00812403          	lw	s0,8(sp)
    42d4:	01010113          	addi	sp,sp,16
    42d8:	00008067          	ret

000042dc <_Z10ex_zeroaccPVmmmm.constprop.0>:
    42dc:	101805b7          	lui	a1,0x10180
    42e0:	fb5ff06f          	j	4294 <_Z12ex_push_insnPVmm>

000042e4 <_Z7ex_enccPVm>:
    42e4:	8a0035b7          	lui	a1,0x8a003
    42e8:	fe010113          	addi	sp,sp,-32
    42ec:	00a58593          	addi	a1,a1,10 # 8a00300a <__fw_export_text_end+0x89ffdcda>
    42f0:	00112e23          	sw	ra,28(sp)
    42f4:	00a12623          	sw	a0,12(sp)
    42f8:	f9dff0ef          	jal	4294 <_Z12ex_push_insnPVmm>
    42fc:	00c12503          	lw	a0,12(sp)
    4300:	01c12083          	lw	ra,28(sp)
    4304:	020005b7          	lui	a1,0x2000
    4308:	02010113          	addi	sp,sp,32
    430c:	f89ff06f          	j	4294 <_Z12ex_push_insnPVmm>

00004310 <_Z19execute_instructionPVmj>:
    4310:	f85ff06f          	j	4294 <_Z12ex_push_insnPVmm>

00004314 <_Z11ex_sem_initmmmPVm.constprop.0>:
    4314:	00250713          	addi	a4,a0,2
    4318:	00100793          	li	a5,1
    431c:	00058513          	mv	a0,a1
    4320:	00e797b3          	sll	a5,a5,a4
    4324:	a31005b7          	lui	a1,0xa3100
    4328:	00b7e5b3          	or	a1,a5,a1
    432c:	fe5ff06f          	j	4310 <_Z19execute_instructionPVmj>

00004330 <_ZN13c_tensix_core15instrn_buf_baseEm>:
    4330:	ffe407b7          	lui	a5,0xffe40
    4334:	00078793          	mv	a5,a5
    4338:	01051513          	slli	a0,a0,0x10
    433c:	00a78533          	add	a0,a5,a0
    4340:	00008067          	ret

00004344 <_ZN13c_tensix_core11pc_buf_baseEm>:
    4344:	ff010113          	addi	sp,sp,-16
    4348:	ffe807b7          	lui	a5,0xffe80
    434c:	00f12223          	sw	a5,4(sp)
    4350:	ffe907b7          	lui	a5,0xffe90
    4354:	00f12423          	sw	a5,8(sp)
    4358:	ffea07b7          	lui	a5,0xffea0
    435c:	00f12623          	sw	a5,12(sp)
    4360:	01010793          	addi	a5,sp,16
    4364:	20f54533          	sh2add	a0,a0,a5
    4368:	ff452503          	lw	a0,-12(a0)
    436c:	01010113          	addi	sp,sp,16
    4370:	00008067          	ret

00004374 <_ZN13c_tensix_core13cfg_regs_baseEm.constprop.0>:
    4374:	ffef0537          	lui	a0,0xffef0
    4378:	00008067          	ret

0000437c <_ZN13c_tensix_core10ex_rmw_cfgEhmmmm.constprop.0>:
    437c:	ffef06b7          	lui	a3,0xffef0
    4380:	f31ff06f          	j	42b0 <_Z10ex_rmw_cfgmmmmPVm.constprop.0>

00004384 <_ZN13c_tensix_core11ex_sem_initEmmmPVm.constprop.0>:
    4384:	f91ff06f          	j	4314 <_Z11ex_sem_initmmmPVm.constprop.0>

00004388 <_ZN13c_tensix_core10ex_zeroaccEPVmmmm.constprop.0>:
    4388:	f55ff06f          	j	42dc <_Z10ex_zeroaccPVmmmm.constprop.0>

0000438c <_ZN13c_tensix_core7ex_enccEPVm>:
    438c:	f59ff06f          	j	42e4 <_Z7ex_enccPVm>

00004390 <_ZN13c_tensix_core13ex_load_constEPVm>:
    4390:	7100c5b7          	lui	a1,0x7100c
    4394:	fe010113          	addi	sp,sp,-32
    4398:	f8058593          	addi	a1,a1,-128 # 7100bf80 <__fw_export_text_end+0x71006c50>
    439c:	00112e23          	sw	ra,28(sp)
    43a0:	00a12623          	sw	a0,12(sp)
    43a4:	ef1ff0ef          	jal	4294 <_Z12ex_push_insnPVmm>
    43a8:	00c12503          	lw	a0,12(sp)
    43ac:	01c12083          	lw	ra,28(sp)
    43b0:	910005b7          	lui	a1,0x91000
    43b4:	0b058593          	addi	a1,a1,176 # 910000b0 <__fw_export_text_end+0x90ffad80>
    43b8:	02010113          	addi	sp,sp,32
    43bc:	ed9ff06f          	j	4294 <_Z12ex_push_insnPVmm>

000043c0 <_ZN13c_tensix_core28initialize_tensix_semaphoresEPVm>:
    43c0:	fe010113          	addi	sp,sp,-32
    43c4:	00050593          	mv	a1,a0
    43c8:	00a12623          	sw	a0,12(sp)
    43cc:	00100513          	li	a0,1
    43d0:	00112e23          	sw	ra,28(sp)
    43d4:	fb1ff0ef          	jal	4384 <_ZN13c_tensix_core11ex_sem_initEmmmPVm.constprop.0>
    43d8:	00c12583          	lw	a1,12(sp)
    43dc:	00200513          	li	a0,2
    43e0:	fa5ff0ef          	jal	4384 <_ZN13c_tensix_core11ex_sem_initEmmmPVm.constprop.0>
    43e4:	00c12583          	lw	a1,12(sp)
    43e8:	01c12083          	lw	ra,28(sp)
    43ec:	00700513          	li	a0,7
    43f0:	02010113          	addi	sp,sp,32
    43f4:	f91ff06f          	j	4384 <_ZN13c_tensix_core11ex_sem_initEmmmPVm.constprop.0>

000043f8 <_ZN15kernel_profiler13init_profilerEttt.constprop.0>:
    43f8:	00c00713          	li	a4,12
    43fc:	86e1a623          	sw	a4,-1940(gp) # ffb0005c <_ZN15kernel_profiler6wIndexE>
    4400:	8601a423          	sw	zero,-1944(gp) # ffb00058 <_ZN15kernel_profiler9stackSizeE>
    4404:	86018713          	addi	a4,gp,-1952 # ffb00050 <_ZN15kernel_profiler6sumIDsE>
    4408:	85818793          	addi	a5,gp,-1960 # ffb00048 <_ZN15kernel_profiler4sumsE>
    440c:	0007a023          	sw	zero,0(a5) # ffea0000 <__instrn_buffer+0x60000>
    4410:	0007a223          	sw	zero,4(a5)
    4414:	00072023          	sw	zero,0(a4)
    4418:	00072223          	sw	zero,4(a4)
    441c:	00001737          	lui	a4,0x1
    4420:	9f472683          	lw	a3,-1548(a4) # 9f4 <_start-0x2e4c>
    4424:	a0072623          	sw	zero,-1524(a4)
    4428:	02069e63          	bnez	a3,4464 <_ZN15kernel_profiler13init_profilerEttt.constprop.0+0x6c>
    442c:	000036b7          	lui	a3,0x3
    4430:	a4070793          	addi	a5,a4,-1472
    4434:	24068693          	addi	a3,a3,576 # 3240 <_start-0x600>
    4438:	0007a023          	sw	zero,0(a5)
    443c:	0007a223          	sw	zero,4(a5)
    4440:	0007a423          	sw	zero,8(a5)
    4444:	0007a623          	sw	zero,12(a5)
    4448:	7ff78793          	addi	a5,a5,2047
    444c:	00178793          	addi	a5,a5,1
    4450:	fed794e3          	bne	a5,a3,4438 <_ZN15kernel_profiler13init_profilerEttt.constprop.0+0x40>
    4454:	8741c783          	lbu	a5,-1932(gp) # ffb00064 <my_x>
    4458:	9ef72c23          	sw	a5,-1544(a4)
    445c:	8701c783          	lbu	a5,-1936(gp) # ffb00060 <my_y>
    4460:	9ef72e23          	sw	a5,-1540(a4)
    4464:	8541a683          	lw	a3,-1964(gp) # ffb00044 <_ZN15kernel_profiler10traceCountE>
    4468:	080007b7          	lui	a5,0x8000
    446c:	00b69693          	slli	a3,a3,0xb
    4470:	80078793          	addi	a5,a5,-2048 # 7fff800 <__fw_export_text_end+0x7ffa4d0>
    4474:	00001537          	lui	a0,0x1
    4478:	000035b7          	lui	a1,0x3
    447c:	00f6f6b3          	and	a3,a3,a5
    4480:	a4050713          	addi	a4,a0,-1472 # a40 <_start-0x2e00>
    4484:	80000837          	lui	a6,0x80000
    4488:	00c00893          	li	a7,12
    448c:	24058593          	addi	a1,a1,576 # 3240 <_start-0x600>
    4490:	00400793          	li	a5,4
    4494:	20e7c633          	sh2add	a2,a5,a4
    4498:	00178793          	addi	a5,a5,1
    449c:	01062023          	sw	a6,0(a2)
    44a0:	ff179ae3          	bne	a5,a7,4494 <_ZN15kernel_profiler13init_profilerEttt.constprop.0+0x9c>
    44a4:	a4050793          	addi	a5,a0,-1472
    44a8:	0087a603          	lw	a2,8(a5)
    44ac:	7ff78793          	addi	a5,a5,2047
    44b0:	7ff67613          	andi	a2,a2,2047
    44b4:	00d66633          	or	a2,a2,a3
    44b8:	80c7a4a3          	sw	a2,-2039(a5)
    44bc:	00178793          	addi	a5,a5,1
    44c0:	feb794e3          	bne	a5,a1,44a8 <_ZN15kernel_profiler13init_profilerEttt.constprop.0+0xb0>
    44c4:	7ff70713          	addi	a4,a4,2047
    44c8:	00170713          	addi	a4,a4,1
    44cc:	fcf712e3          	bne	a4,a5,4490 <_ZN15kernel_profiler13init_profilerEttt.constprop.0+0x98>
    44d0:	00008067          	ret

000044d4 <_ZN15kernel_profiler12get_const_idEmNS_11PacketTypesE.constprop.0>:
    44d4:	0000e7b7          	lui	a5,0xe
    44d8:	53378793          	addi	a5,a5,1331 # e533 <__fw_export_text_end+0x9203>
    44dc:	01051513          	slli	a0,a0,0x10
    44e0:	00f56533          	or	a0,a0,a5
    44e4:	00008067          	ret

000044e8 <_ZN15kernel_profiler15finish_profilerEv>:
    44e8:	00000613          	li	a2,0
    44ec:	85818593          	addi	a1,gp,-1960 # ffb00048 <_ZN15kernel_profiler4sumsE>
    44f0:	1ff00313          	li	t1,511
    44f4:	00400893          	li	a7,4
    44f8:	00b607b3          	add	a5,a2,a1
    44fc:	0007a803          	lw	a6,0(a5)
    4500:	04080263          	beqz	a6,4544 <_ZN15kernel_profiler15finish_profilerEv+0x5c>
    4504:	86c1a683          	lw	a3,-1940(gp) # ffb0005c <_ZN15kernel_profiler6wIndexE>
    4508:	02d36e63          	bltu	t1,a3,4544 <_ZN15kernel_profiler15finish_profilerEv+0x5c>
    450c:	86018793          	addi	a5,gp,-1952 # ffb00050 <_ZN15kernel_profiler6sumIDsE>
    4510:	00f607b3          	add	a5,a2,a5
    4514:	0007a783          	lw	a5,0(a5)
    4518:	0ffff737          	lui	a4,0xffff
    451c:	00c79793          	slli	a5,a5,0xc
    4520:	00e7f7b3          	and	a5,a5,a4
    4524:	a0000737          	lui	a4,0xa0000
    4528:	00e7e7b3          	or	a5,a5,a4
    452c:	00269713          	slli	a4,a3,0x2
    4530:	7ff70713          	addi	a4,a4,2047 # a00007ff <__fw_export_text_end+0x9fffb4cf>
    4534:	24f720a3          	sw	a5,577(a4)
    4538:	00268693          	addi	a3,a3,2
    453c:	250722a3          	sw	a6,581(a4)
    4540:	86d1a623          	sw	a3,-1940(gp) # ffb0005c <_ZN15kernel_profiler6wIndexE>
    4544:	29161263          	bne	a2,a7,47c8 <_ZN15kernel_profiler15finish_profilerEv+0x2e0>
    4548:	00000693          	li	a3,0
    454c:	1ff00593          	li	a1,511
    4550:	80000537          	lui	a0,0x80000
    4554:	86c1a783          	lw	a5,-1940(gp) # ffb0005c <_ZN15kernel_profiler6wIndexE>
    4558:	0037f713          	andi	a4,a5,3
    455c:	26e6ea63          	bltu	a3,a4,47d0 <_ZN15kernel_profiler15finish_profilerEv+0x2e8>
    4560:	000016b7          	lui	a3,0x1
    4564:	9cf6aa23          	sw	a5,-1580(a3) # 9d4 <_start-0x2e6c>
    4568:	a0c6a783          	lw	a5,-1524(a3)
    456c:	00100713          	li	a4,1
    4570:	9c068813          	addi	a6,a3,-1600
    4574:	3ee78e63          	beq	a5,a4,4970 <_ZN15kernel_profiler15finish_profilerEv+0x488>
    4578:	04082603          	lw	a2,64(a6) # 80000040 <__fw_export_text_end+0x7fffad10>
    457c:	03082783          	lw	a5,48(a6)
    4580:	f9010113          	addi	sp,sp,-112
    4584:	780405b7          	lui	a1,0x78040
    4588:	fff58593          	addi	a1,a1,-1 # 7803ffff <__fw_export_text_end+0x7803accf>
    458c:	07212223          	sw	s2,100(sp)
    4590:	05a12223          	sw	s10,68(sp)
    4594:	06912423          	sw	s1,104(sp)
    4598:	05712823          	sw	s7,80(sp)
    459c:	05912423          	sw	s9,72(sp)
    45a0:	06812623          	sw	s0,108(sp)
    45a4:	07312023          	sw	s3,96(sp)
    45a8:	05412e23          	sw	s4,92(sp)
    45ac:	00f12023          	sw	a5,0(sp)
    45b0:	8501cf83          	lbu	t6,-1968(gp) # ffb00040 <noc_index>
    45b4:	ffb207b7          	lui	a5,0xffb20
    45b8:	010f9713          	slli	a4,t6,0x10
    45bc:	01c78f13          	addi	t5,a5,28 # ffb2001c <__stack_top+0x1e01c>
    45c0:	01e70f33          	add	t5,a4,t5
    45c4:	000f2503          	lw	a0,0(t5)
    45c8:	01478e93          	addi	t4,a5,20
    45cc:	00b575b3          	and	a1,a0,a1
    45d0:	01d70eb3          	add	t4,a4,t4
    45d4:	00b12623          	sw	a1,12(sp)
    45d8:	000ea583          	lw	a1,0(t4)
    45dc:	00f70933          	add	s2,a4,a5
    45e0:	00b12823          	sw	a1,16(sp)
    45e4:	00c78e13          	addi	t3,a5,12
    45e8:	00092583          	lw	a1,0(s2)
    45ec:	01c70e33          	add	t3,a4,t3
    45f0:	00b12a23          	sw	a1,20(sp)
    45f4:	02078313          	addi	t1,a5,32
    45f8:	000e2583          	lw	a1,0(t3)
    45fc:	00670333          	add	t1,a4,t1
    4600:	00b12c23          	sw	a1,24(sp)
    4604:	00032583          	lw	a1,0(t1)
    4608:	01878493          	addi	s1,a5,24
    460c:	00b12e23          	sw	a1,28(sp)
    4610:	00878593          	addi	a1,a5,8
    4614:	00b705b3          	add	a1,a4,a1
    4618:	00b12223          	sw	a1,4(sp)
    461c:	0005a583          	lw	a1,0(a1)
    4620:	009704b3          	add	s1,a4,s1
    4624:	02b12023          	sw	a1,32(sp)
    4628:	00478593          	addi	a1,a5,4
    462c:	00b70d33          	add	s10,a4,a1
    4630:	000d2583          	lw	a1,0(s10)
    4634:	05512c23          	sw	s5,88(sp)
    4638:	05612a23          	sw	s6,84(sp)
    463c:	05812623          	sw	s8,76(sp)
    4640:	05b12023          	sw	s11,64(sp)
    4644:	02b12223          	sw	a1,36(sp)
    4648:	0004a583          	lw	a1,0(s1)
    464c:	0004a023          	sw	zero,0(s1)
    4650:	02b12423          	sw	a1,40(sp)
    4654:	02878593          	addi	a1,a5,40
    4658:	00b70cb3          	add	s9,a4,a1
    465c:	000ca583          	lw	a1,0(s9)
    4660:	01078793          	addi	a5,a5,16
    4664:	00f707b3          	add	a5,a4,a5
    4668:	02b12623          	sw	a1,44(sp)
    466c:	0007a583          	lw	a1,0(a5)
    4670:	00000293          	li	t0,0
    4674:	02b12823          	sw	a1,48(sp)
    4678:	00361593          	slli	a1,a2,0x3
    467c:	7f85f593          	andi	a1,a1,2040
    4680:	00b12423          	sw	a1,8(sp)
    4684:	000505b7          	lui	a1,0x50
    4688:	02b60633          	mul	a2,a2,a1
    468c:	00012583          	lw	a1,0(sp)
    4690:	00004bb7          	lui	s7,0x4
    4694:	00b60633          	add	a2,a2,a1
    4698:	02c12a23          	sw	a2,52(sp)
    469c:	08000637          	lui	a2,0x8000
    46a0:	80060613          	addi	a2,a2,-2048 # 7fff800 <__fw_export_text_end+0x7ffa4d0>
    46a4:	9d468593          	addi	a1,a3,-1580
    46a8:	02c12c23          	sw	a2,56(sp)
    46ac:	a4068693          	addi	a3,a3,-1472
    46b0:	0086a603          	lw	a2,8(a3)
    46b4:	03812503          	lw	a0,56(sp)
    46b8:	00a67633          	and	a2,a2,a0
    46bc:	00812503          	lw	a0,8(sp)
    46c0:	00556533          	or	a0,a0,t0
    46c4:	00a66633          	or	a2,a2,a0
    46c8:	00c6a423          	sw	a2,8(a3)
    46cc:	0005a603          	lw	a2,0(a1) # 50000 <__fw_export_text_end+0x4acd0>
    46d0:	14060c63          	beqz	a2,4828 <_ZN15kernel_profiler15finish_profilerEv+0x340>
    46d4:	0005a503          	lw	a0,0(a1)
    46d8:	fec5a603          	lw	a2,-20(a1)
    46dc:	fec58393          	addi	t2,a1,-20
    46e0:	00c50533          	add	a0,a0,a2
    46e4:	fec5a603          	lw	a2,-20(a1)
    46e8:	fec5a883          	lw	a7,-20(a1)
    46ec:	10abe463          	bltu	s7,a0,47f4 <_ZN15kernel_profiler15finish_profilerEv+0x30c>
    46f0:	0005a603          	lw	a2,0(a1)
    46f4:	fea5a623          	sw	a0,-20(a1)
    46f8:	00261613          	slli	a2,a2,0x2
    46fc:	00012503          	lw	a0,0(sp)
    4700:	12050463          	beqz	a0,4828 <_ZN15kernel_profiler15finish_profilerEv+0x340>
    4704:	03412383          	lw	t2,52(sp)
    4708:	01029513          	slli	a0,t0,0x10
    470c:	00750533          	add	a0,a0,t2
    4710:	00d603b3          	add	t2,a2,a3
    4714:	20a8c8b3          	sh2add	a7,a7,a0
    4718:	02712e23          	sw	t2,60(sp)
    471c:	ffb203b7          	lui	t2,0xffb20
    4720:	10006537          	lui	a0,0x10006
    4724:	04038393          	addi	t2,t2,64 # ffb20040 <__stack_top+0x1e040>
    4728:	00002a37          	lui	s4,0x2
    472c:	10000ab7          	lui	s5,0x10000
    4730:	01000b37          	lui	s6,0x1000
    4734:	84818413          	addi	s0,gp,-1976 # ffb00038 <noc_posted_writes_num_issued>
    4738:	13050513          	addi	a0,a0,304 # 10006130 <__fw_export_text_end+0x10000e00>
    473c:	208fc433          	sh2add	s0,t6,s0
    4740:	000049b7          	lui	s3,0x4
    4744:	007703b3          	add	t2,a4,t2
    4748:	082a0a13          	addi	s4,s4,130 # 2082 <_start-0x17be>
    474c:	00fa8a93          	addi	s5,s5,15 # 1000000f <__fw_export_text_end+0xfffacdf>
    4750:	fffb0b13          	addi	s6,s6,-1 # ffffff <__fw_export_text_end+0xffaccf>
    4754:	03c12c03          	lw	s8,60(sp)
    4758:	40cc0c33          	sub	s8,s8,a2
    475c:	1ac9ee63          	bltu	s3,a2,4918 <_ZN15kernel_profiler15finish_profilerEv+0x430>
    4760:	ffb203b7          	lui	t2,0xffb20
    4764:	04038393          	addi	t2,t2,64 # ffb20040 <__stack_top+0x1e040>
    4768:	007703b3          	add	t2,a4,t2
    476c:	0003a403          	lw	s0,0(t2)
    4770:	fe041ee3          	bnez	s0,476c <_ZN15kernel_profiler15finish_profilerEv+0x284>
    4774:	00002437          	lui	s0,0x2
    4778:	08240413          	addi	s0,s0,130 # 2082 <_start-0x17be>
    477c:	008f2023          	sw	s0,0(t5)
    4780:	01892023          	sw	s8,0(s2)
    4784:	011e2023          	sw	a7,0(t3)
    4788:	100008b7          	lui	a7,0x10000
    478c:	00f88893          	addi	a7,a7,15 # 1000000f <__fw_export_text_end+0xfffacdf>
    4790:	011578b3          	and	a7,a0,a7
    4794:	0117a023          	sw	a7,0(a5)
    4798:	00451893          	slli	a7,a0,0x4
    479c:	0088d513          	srli	a0,a7,0x8
    47a0:	00aea023          	sw	a0,0(t4)
    47a4:	00c32023          	sw	a2,0(t1)
    47a8:	00100613          	li	a2,1
    47ac:	00c3a023          	sw	a2,0(t2)
    47b0:	84818613          	addi	a2,gp,-1976 # ffb00038 <noc_posted_writes_num_issued>
    47b4:	20cfc633          	sh2add	a2,t6,a2
    47b8:	00062503          	lw	a0,0(a2)
    47bc:	00150513          	addi	a0,a0,1
    47c0:	00a62023          	sw	a0,0(a2)
    47c4:	0640006f          	j	4828 <_ZN15kernel_profiler15finish_profilerEv+0x340>
    47c8:	00400613          	li	a2,4
    47cc:	d2dff06f          	j	44f8 <_ZN15kernel_profiler15finish_profilerEv+0x10>
    47d0:	00f5ee63          	bltu	a1,a5,47ec <_ZN15kernel_profiler15finish_profilerEv+0x304>
    47d4:	00279713          	slli	a4,a5,0x2
    47d8:	7ff70713          	addi	a4,a4,2047
    47dc:	24a720a3          	sw	a0,577(a4)
    47e0:	00278793          	addi	a5,a5,2
    47e4:	240722a3          	sw	zero,581(a4)
    47e8:	86f1a623          	sw	a5,-1940(gp) # ffb0005c <_ZN15kernel_profiler6wIndexE>
    47ec:	00168693          	addi	a3,a3,1
    47f0:	d65ff06f          	j	4554 <_ZN15kernel_profiler15finish_profilerEv+0x6c>
    47f4:	00100513          	li	a0,1
    47f8:	00c60613          	addi	a2,a2,12
    47fc:	00551533          	sll	a0,a0,t0
    4800:	00cbee63          	bltu	s7,a2,481c <_ZN15kernel_profiler15finish_profilerEv+0x334>
    4804:	00c3a023          	sw	a2,0(t2)
    4808:	04882603          	lw	a2,72(a6)
    480c:	00a66633          	or	a2,a2,a0
    4810:	04c82423          	sw	a2,72(a6)
    4814:	03000613          	li	a2,48
    4818:	ee5ff06f          	j	46fc <_ZN15kernel_profiler15finish_profilerEv+0x214>
    481c:	04882603          	lw	a2,72(a6)
    4820:	00a66633          	or	a2,a2,a0
    4824:	04c82423          	sw	a2,72(a6)
    4828:	7ff68693          	addi	a3,a3,2047
    482c:	00128293          	addi	t0,t0,1
    4830:	00500613          	li	a2,5
    4834:	00168693          	addi	a3,a3,1
    4838:	00458593          	addi	a1,a1,4
    483c:	e6c29ae3          	bne	t0,a2,46b0 <_ZN15kernel_profiler15finish_profilerEv+0x1c8>
    4840:	84818693          	addi	a3,gp,-1976 # ffb00038 <noc_posted_writes_num_issued>
    4844:	20dfcfb3          	sh2add	t6,t6,a3
    4848:	ffb206b7          	lui	a3,0xffb20
    484c:	22c68693          	addi	a3,a3,556 # ffb2022c <__stack_top+0x1e22c>
    4850:	000fa603          	lw	a2,0(t6)
    4854:	00d706b3          	add	a3,a4,a3
    4858:	0006a583          	lw	a1,0(a3)
    485c:	fec59ee3          	bne	a1,a2,4858 <_ZN15kernel_profiler15finish_profilerEv+0x370>
    4860:	000016b7          	lui	a3,0x1
    4864:	9f46a603          	lw	a2,-1548(a3) # 9f4 <_start-0x2e4c>
    4868:	00160613          	addi	a2,a2,1
    486c:	9ec6aa23          	sw	a2,-1548(a3)
    4870:	00100613          	li	a2,1
    4874:	a0c6a623          	sw	a2,-1524(a3)
    4878:	ffb206b7          	lui	a3,0xffb20
    487c:	04068693          	addi	a3,a3,64 # ffb20040 <__stack_top+0x1e040>
    4880:	00d70733          	add	a4,a4,a3
    4884:	00072683          	lw	a3,0(a4)
    4888:	fe069ee3          	bnez	a3,4884 <_ZN15kernel_profiler15finish_profilerEv+0x39c>
    488c:	00c12703          	lw	a4,12(sp)
    4890:	02012683          	lw	a3,32(sp)
    4894:	00ef2023          	sw	a4,0(t5)
    4898:	01012703          	lw	a4,16(sp)
    489c:	06c12403          	lw	s0,108(sp)
    48a0:	00eea023          	sw	a4,0(t4)
    48a4:	01412703          	lw	a4,20(sp)
    48a8:	06012983          	lw	s3,96(sp)
    48ac:	00e92023          	sw	a4,0(s2)
    48b0:	01812703          	lw	a4,24(sp)
    48b4:	06412903          	lw	s2,100(sp)
    48b8:	00ee2023          	sw	a4,0(t3)
    48bc:	01c12703          	lw	a4,28(sp)
    48c0:	05c12a03          	lw	s4,92(sp)
    48c4:	00e32023          	sw	a4,0(t1)
    48c8:	00412703          	lw	a4,4(sp)
    48cc:	05812a83          	lw	s5,88(sp)
    48d0:	00d72023          	sw	a3,0(a4)
    48d4:	02412703          	lw	a4,36(sp)
    48d8:	05412b03          	lw	s6,84(sp)
    48dc:	00ed2023          	sw	a4,0(s10)
    48e0:	02812703          	lw	a4,40(sp)
    48e4:	05012b83          	lw	s7,80(sp)
    48e8:	00e4a023          	sw	a4,0(s1)
    48ec:	02c12703          	lw	a4,44(sp)
    48f0:	06812483          	lw	s1,104(sp)
    48f4:	00eca023          	sw	a4,0(s9)
    48f8:	03012703          	lw	a4,48(sp)
    48fc:	04c12c03          	lw	s8,76(sp)
    4900:	04812c83          	lw	s9,72(sp)
    4904:	04412d03          	lw	s10,68(sp)
    4908:	00e7a023          	sw	a4,0(a5)
    490c:	04012d83          	lw	s11,64(sp)
    4910:	07010113          	addi	sp,sp,112
    4914:	00008067          	ret
    4918:	0003ad83          	lw	s11,0(t2)
    491c:	fe0d9ee3          	bnez	s11,4918 <_ZN15kernel_profiler15finish_profilerEv+0x430>
    4920:	014f2023          	sw	s4,0(t5)
    4924:	01892023          	sw	s8,0(s2)
    4928:	011e2023          	sw	a7,0(t3)
    492c:	01557c33          	and	s8,a0,s5
    4930:	0187a023          	sw	s8,0(a5)
    4934:	00455c13          	srli	s8,a0,0x4
    4938:	016c7c33          	and	s8,s8,s6
    493c:	018ea023          	sw	s8,0(t4)
    4940:	01332023          	sw	s3,0(t1)
    4944:	00100c13          	li	s8,1
    4948:	0183a023          	sw	s8,0(t2)
    494c:	00042c03          	lw	s8,0(s0)
    4950:	41360633          	sub	a2,a2,s3
    4954:	001c0c13          	addi	s8,s8,1
    4958:	01842023          	sw	s8,0(s0)
    495c:	01388c33          	add	s8,a7,s3
    4960:	011c3db3          	sltu	s11,s8,a7
    4964:	00ad8533          	add	a0,s11,a0
    4968:	000c0893          	mv	a7,s8
    496c:	de9ff06f          	j	4754 <_ZN15kernel_profiler15finish_profilerEv+0x26c>
    4970:	00008067          	ret

00004974 <_Z22set_deassert_addressesv>:
    4974:	ff010113          	addi	sp,sp,-16
    4978:	00812423          	sw	s0,8(sp)
    497c:	ffb12437          	lui	s0,0xffb12
    4980:	23440513          	addi	a0,s0,564 # ffb12234 <__stack_top+0x10234>
    4984:	00700593          	li	a1,7
    4988:	00112623          	sw	ra,12(sp)
    498c:	8adff0ef          	jal	4238 <_Z9WRITE_REGmm>
    4990:	23c40513          	addi	a0,s0,572
    4994:	00812403          	lw	s0,8(sp)
    4998:	00c12083          	lw	ra,12(sp)
    499c:	00100593          	li	a1,1
    49a0:	01010113          	addi	sp,sp,16
    49a4:	895ff06f          	j	4238 <_Z9WRITE_REGmm>

000049a8 <_Z21deassert_ncrisc_triscv>:
    49a8:	8101a703          	lw	a4,-2032(gp) # ffb00000 <_ZL16subordinate_sync>
    49ac:	404047b7          	lui	a5,0x40404
    49b0:	04078793          	addi	a5,a5,64 # 40404040 <__fw_export_text_end+0x403fed10>
    49b4:	00f72023          	sw	a5,0(a4)
    49b8:	889ff06f          	j	4240 <_Z18deassert_all_resetv>

000049bc <_Z10run_triscsm>:
    49bc:	8101a783          	lw	a5,-2032(gp) # ffb00000 <_ZL16subordinate_sync>
    49c0:	0017c703          	lbu	a4,1(a5)
    49c4:	02071063          	bnez	a4,49e4 <_Z10run_triscsm+0x28>
    49c8:	00457513          	andi	a0,a0,4
    49cc:	00050a63          	beqz	a0,49e0 <_Z10run_triscsm+0x24>
    49d0:	f8000713          	li	a4,-128
    49d4:	00e780a3          	sb	a4,1(a5)
    49d8:	00e78123          	sb	a4,2(a5)
    49dc:	00e781a3          	sb	a4,3(a5)
    49e0:	00008067          	ret
    49e4:	0ff0000f          	fence
    49e8:	fd9ff06f          	j	49c0 <_Z10run_triscsm+0x4>

000049ec <_Z29start_ncrisc_kernel_run_earlym>:
    49ec:	00257513          	andi	a0,a0,2
    49f0:	00050863          	beqz	a0,4a00 <_Z29start_ncrisc_kernel_run_earlym+0x14>
    49f4:	8101a783          	lw	a5,-2032(gp) # ffb00000 <_ZL16subordinate_sync>
    49f8:	f8000713          	li	a4,-128
    49fc:	00e78023          	sb	a4,0(a5)
    4a00:	00008067          	ret

00004a04 <_Z17wait_ncrisc_triscv>:
    4a04:	8101a703          	lw	a4,-2032(gp) # ffb00000 <_ZL16subordinate_sync>
    4a08:	00072783          	lw	a5,0(a4)
    4a0c:	00079463          	bnez	a5,4a14 <_Z17wait_ncrisc_triscv+0x10>
    4a10:	00008067          	ret
    4a14:	0ff0000f          	fence
    4a18:	ff1ff06f          	j	4a08 <_Z17wait_ncrisc_triscv+0x4>

00004a1c <_Z26trigger_sync_register_initv>:
    4a1c:	8101a783          	lw	a5,-2032(gp) # ffb00000 <_ZL16subordinate_sync>
    4a20:	00300713          	li	a4,3
    4a24:	00e780a3          	sb	a4,1(a5)
    4a28:	00008067          	ret

00004a2c <_Z33barrier_remote_cb_interface_setuphm>:
    4a2c:	02000793          	li	a5,32
    4a30:	02f58663          	beq	a1,a5,4a5c <_Z33barrier_remote_cb_interface_setuphm+0x30>
    4a34:	ffb20737          	lui	a4,0xffb20
    4a38:	01051793          	slli	a5,a0,0x10
    4a3c:	20070713          	addi	a4,a4,512 # ffb20200 <__stack_top+0x1e200>
    4a40:	00e787b3          	add	a5,a5,a4
    4a44:	83c18713          	addi	a4,gp,-1988 # ffb0002c <noc_nonposted_atomics_acked>
    4a48:	20e54533          	sh2add	a0,a0,a4
    4a4c:	00052703          	lw	a4,0(a0)
    4a50:	0007a683          	lw	a3,0(a5)
    4a54:	fee69ee3          	bne	a3,a4,4a50 <_Z33barrier_remote_cb_interface_setuphm+0x24>
    4a58:	0ff0000f          	fence
    4a5c:	00008067          	ret

00004a60 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0>:
    4a60:	fa010113          	addi	sp,sp,-96
    4a64:	fff58793          	addi	a5,a1,-1
    4a68:	00f12823          	sw	a5,16(sp)
    4a6c:	100007b7          	lui	a5,0x10000
    4a70:	00f78793          	addi	a5,a5,15 # 1000000f <__fw_export_text_end+0xfffacdf>
    4a74:	00f12423          	sw	a5,8(sp)
    4a78:	010007b7          	lui	a5,0x1000
    4a7c:	ffb20337          	lui	t1,0xffb20
    4a80:	fff78793          	addi	a5,a5,-1 # ffffff <__fw_export_text_end+0xffaccf>
    4a84:	03b12823          	sw	s11,48(sp)
    4a88:	00b71813          	slli	a6,a4,0xb
    4a8c:	01061d93          	slli	s11,a2,0x10
    4a90:	01b80833          	add	a6,a6,s11
    4a94:	00f12623          	sw	a5,12(sp)
    4a98:	00430793          	addi	a5,t1,4 # ffb20004 <__stack_top+0x1e004>
    4a9c:	04030293          	addi	t0,t1,64
    4aa0:	00f807b3          	add	a5,a6,a5
    4aa4:	04812e23          	sw	s0,92(sp)
    4aa8:	05612223          	sw	s6,68(sp)
    4aac:	83c18393          	addi	t2,gp,-1988 # ffb0002c <noc_nonposted_atomics_acked>
    4ab0:	04912c23          	sw	s1,88(sp)
    4ab4:	207643b3          	sh2add	t2,a2,t2
    4ab8:	05212a23          	sw	s2,84(sp)
    4abc:	05312823          	sw	s3,80(sp)
    4ac0:	05412623          	sw	s4,76(sp)
    4ac4:	05512423          	sw	s5,72(sp)
    4ac8:	05712023          	sw	s7,64(sp)
    4acc:	03812e23          	sw	s8,60(sp)
    4ad0:	03912c23          	sw	s9,56(sp)
    4ad4:	03a12a23          	sw	s10,52(sp)
    4ad8:	00050413          	mv	s0,a0
    4adc:	87818593          	addi	a1,gp,-1928 # ffb00068 <cb_interface>
    4ae0:	01f00b13          	li	s6,31
    4ae4:	005802b3          	add	t0,a6,t0
    4ae8:	02f12623          	sw	a5,44(sp)
    4aec:	01012783          	lw	a5,16(sp)
    4af0:	03679e63          	bne	a5,s6,4b2c <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0xcc>
    4af4:	05c12403          	lw	s0,92(sp)
    4af8:	05812483          	lw	s1,88(sp)
    4afc:	05412903          	lw	s2,84(sp)
    4b00:	05012983          	lw	s3,80(sp)
    4b04:	04c12a03          	lw	s4,76(sp)
    4b08:	04812a83          	lw	s5,72(sp)
    4b0c:	04412b03          	lw	s6,68(sp)
    4b10:	04012b83          	lw	s7,64(sp)
    4b14:	03c12c03          	lw	s8,60(sp)
    4b18:	03812c83          	lw	s9,56(sp)
    4b1c:	03412d03          	lw	s10,52(sp)
    4b20:	03012d83          	lw	s11,48(sp)
    4b24:	06010113          	addi	sp,sp,96
    4b28:	00008067          	ret
    4b2c:	00042f03          	lw	t5,0(s0)
    4b30:	00442503          	lw	a0,4(s0)
    4b34:	000f2f83          	lw	t6,0(t5)
    4b38:	004f2b83          	lw	s7,4(t5)
    4b3c:	008f2e03          	lw	t3,8(t5)
    4b40:	00cf2783          	lw	a5,12(t5)
    4b44:	010f2783          	lw	a5,16(t5)
    4b48:	014f2903          	lw	s2,20(t5)
    4b4c:	018f2883          	lw	a7,24(t5)
    4b50:	fff50e93          	addi	t4,a0,-1
    4b54:	00fe8eb3          	add	t4,t4,a5
    4b58:	41ce8eb3          	sub	t4,t4,t3
    4b5c:	02aedeb3          	divu	t4,t4,a0
    4b60:	02ae8eb3          	mul	t4,t4,a0
    4b64:	01ce8eb3          	add	t4,t4,t3
    4b68:	280f8663          	beqz	t6,4df4 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x394>
    4b6c:	3fe5a023          	sw	t5,992(a1)
    4b70:	3fc5a223          	sw	t3,996(a1)
    4b74:	3ef5a823          	sw	a5,1008(a1)
    4b78:	3f25aa23          	sw	s2,1012(a1)
    4b7c:	3f15ac23          	sw	a7,1016(a1)
    4b80:	3f75ae23          	sw	s7,1020(a1)
    4b84:	00cf2f03          	lw	t5,12(t5)
    4b88:	01ee09b3          	add	s3,t3,t5
    4b8c:	02af7fb3          	remu	t6,t5,a0
    4b90:	41f989b3          	sub	s3,s3,t6
    4b94:	0f3ee063          	bltu	t4,s3,4c74 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x214>
    4b98:	40ff0f33          	sub	t5,t5,a5
    4b9c:	01cf0f33          	add	t5,t5,t3
    4ba0:	004f5793          	srli	a5,t5,0x4
    4ba4:	16078463          	beqz	a5,4d0c <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x2ac>
    4ba8:	00100e93          	li	t4,1
    4bac:	00000f13          	li	t5,0
    4bb0:	0dd68c63          	beq	a3,t4,4c88 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x228>
    4bb4:	00830f93          	addi	t6,t1,8
    4bb8:	01c30493          	addi	s1,t1,28
    4bbc:	00680ab3          	add	s5,a6,t1
    4bc0:	01f80fb3          	add	t6,a6,t6
    4bc4:	009804b3          	add	s1,a6,s1
    4bc8:	15eb8263          	beq	s7,t5,4d0c <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x2ac>
    4bcc:	212f6a33          	sh3add	s4,t5,s2
    4bd0:	004a2e83          	lw	t4,4(s4)
    4bd4:	000a2c03          	lw	s8,0(s4)
    4bd8:	0008aa03          	lw	s4,0(a7)
    4bdc:	006e9e93          	slli	t4,t4,0x6
    4be0:	018eeeb3          	or	t4,t4,s8
    4be4:	01478a33          	add	s4,a5,s4
    4be8:	0148a023          	sw	s4,0(a7)
    4bec:	004e9e93          	slli	t4,t4,0x4
    4bf0:	0002aa03          	lw	s4,0(t0)
    4bf4:	fe0a1ee3          	bnez	s4,4bf0 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x190>
    4bf8:	00812a03          	lw	s4,8(sp)
    4bfc:	02c12c03          	lw	s8,44(sp)
    4c00:	011aa023          	sw	a7,0(s5)
    4c04:	014efa33          	and	s4,t4,s4
    4c08:	014c2023          	sw	s4,0(s8)
    4c0c:	00c12a03          	lw	s4,12(sp)
    4c10:	004ede93          	srli	t4,t4,0x4
    4c14:	014efeb3          	and	t4,t4,s4
    4c18:	01dfa023          	sw	t4,0(t6)
    4c1c:	00002eb7          	lui	t4,0x2
    4c20:	091e8e93          	addi	t4,t4,145 # 2091 <_start-0x17af>
    4c24:	01d4a023          	sw	t4,0(s1)
    4c28:	00001a37          	lui	s4,0x1
    4c2c:	0028de93          	srli	t4,a7,0x2
    4c30:	07ca0a13          	addi	s4,s4,124 # 107c <_start-0x27c4>
    4c34:	003efe93          	andi	t4,t4,3
    4c38:	014eeeb3          	or	t4,t4,s4
    4c3c:	02030a13          	addi	s4,t1,32
    4c40:	01480a33          	add	s4,a6,s4
    4c44:	01da2023          	sw	t4,0(s4)
    4c48:	02830e93          	addi	t4,t1,40
    4c4c:	01d80eb3          	add	t4,a6,t4
    4c50:	00fea023          	sw	a5,0(t4)
    4c54:	00100e93          	li	t4,1
    4c58:	01d2a023          	sw	t4,0(t0)
    4c5c:	0003ae83          	lw	t4,0(t2)
    4c60:	02088893          	addi	a7,a7,32
    4c64:	001e8e93          	addi	t4,t4,1
    4c68:	01d3a023          	sw	t4,0(t2)
    4c6c:	001f0f13          	addi	t5,t5,1
    4c70:	f59ff06f          	j	4bc8 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x168>
    4c74:	09d78e63          	beq	a5,t4,4d10 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x2b0>
    4c78:	40fe87b3          	sub	a5,t4,a5
    4c7c:	0047d793          	srli	a5,a5,0x4
    4c80:	000e8e13          	mv	t3,t4
    4c84:	f21ff06f          	j	4ba4 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x144>
    4c88:	02800493          	li	s1,40
    4c8c:	00007eb7          	lui	t4,0x7
    4c90:	029604b3          	mul	s1,a2,s1
    4c94:	ffb20fb7          	lui	t6,0xffb20
    4c98:	04ce8e93          	addi	t4,t4,76 # 704c <__fw_export_text_end+0x1d1c>
    4c9c:	044f8c13          	addi	s8,t6,68 # ffb20044 <__stack_top+0x1e044>
    4ca0:	01d484b3          	add	s1,s1,t4
    4ca4:	00b71f13          	slli	t5,a4,0xb
    4ca8:	01061e93          	slli	t4,a2,0x10
    4cac:	01df0f33          	add	t5,t5,t4
    4cb0:	018e8eb3          	add	t4,t4,s8
    4cb4:	01d12a23          	sw	t4,20(sp)
    4cb8:	00cf8e93          	addi	t4,t6,12
    4cbc:	01df0eb3          	add	t4,t5,t4
    4cc0:	01d12c23          	sw	t4,24(sp)
    4cc4:	10000eb7          	lui	t4,0x10000
    4cc8:	00fe8e93          	addi	t4,t4,15 # 1000000f <__fw_export_text_end+0xfffacdf>
    4ccc:	01d12e23          	sw	t4,28(sp)
    4cd0:	004f8e93          	addi	t4,t6,4
    4cd4:	01df0eb3          	add	t4,t5,t4
    4cd8:	03d12023          	sw	t4,32(sp)
    4cdc:	01000eb7          	lui	t4,0x1000
    4ce0:	fffe8e93          	addi	t4,t4,-1 # ffffff <__fw_export_text_end+0xffaccf>
    4ce4:	008f8c13          	addi	s8,t6,8
    4ce8:	040f8a93          	addi	s5,t6,64
    4cec:	03d12223          	sw	t4,36(sp)
    4cf0:	01cf8c93          	addi	s9,t6,28
    4cf4:	018f0eb3          	add	t4,t5,s8
    4cf8:	00000a13          	li	s4,0
    4cfc:	015f0ab3          	add	s5,t5,s5
    4d00:	03d12423          	sw	t4,40(sp)
    4d04:	019f0cb3          	add	s9,t5,s9
    4d08:	034b9263          	bne	s7,s4,4d2c <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x2cc>
    4d0c:	000e0e93          	mv	t4,t3
    4d10:	3fd5a823          	sw	t4,1008(a1)
    4d14:	3f35a423          	sw	s3,1000(a1)
    4d18:	3ea5a623          	sw	a0,1004(a1)
    4d1c:	00840413          	addi	s0,s0,8
    4d20:	fffb0b13          	addi	s6,s6,-1
    4d24:	fe058593          	addi	a1,a1,-32
    4d28:	dc5ff06f          	j	4aec <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x8c>
    4d2c:	212a6d33          	sh3add	s10,s4,s2
    4d30:	004d2e83          	lw	t4,4(s10)
    4d34:	000d2d03          	lw	s10,0(s10)
    4d38:	006e9e93          	slli	t4,t4,0x6
    4d3c:	000d0c13          	mv	s8,s10
    4d40:	0008ad03          	lw	s10,0(a7)
    4d44:	018eeeb3          	or	t4,t4,s8
    4d48:	004e9e93          	slli	t4,t4,0x4
    4d4c:	01a78d33          	add	s10,a5,s10
    4d50:	01a8a023          	sw	s10,0(a7)
    4d54:	0004ad03          	lw	s10,0(s1)
    4d58:	001d0d13          	addi	s10,s10,1
    4d5c:	01a4a023          	sw	s10,0(s1)
    4d60:	000aad03          	lw	s10,0(s5)
    4d64:	fe0d1ee3          	bnez	s10,4d60 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x300>
    4d68:	01412d03          	lw	s10,20(sp)
    4d6c:	00400c13          	li	s8,4
    4d70:	000d2d03          	lw	s10,0(s10)
    4d74:	01812d03          	lw	s10,24(sp)
    4d78:	018d2023          	sw	s8,0(s10)
    4d7c:	01c12c03          	lw	s8,28(sp)
    4d80:	01ff0d33          	add	s10,t5,t6
    4d84:	011d2023          	sw	a7,0(s10)
    4d88:	018efd33          	and	s10,t4,s8
    4d8c:	02012c03          	lw	s8,32(sp)
    4d90:	004ede93          	srli	t4,t4,0x4
    4d94:	01ac2023          	sw	s10,0(s8)
    4d98:	02412c03          	lw	s8,36(sp)
    4d9c:	00001d37          	lui	s10,0x1
    4da0:	018efeb3          	and	t4,t4,s8
    4da4:	02812c03          	lw	s8,40(sp)
    4da8:	07cd0d13          	addi	s10,s10,124 # 107c <_start-0x27c4>
    4dac:	01dc2023          	sw	t4,0(s8)
    4db0:	00002eb7          	lui	t4,0x2
    4db4:	091e8e93          	addi	t4,t4,145 # 2091 <_start-0x17af>
    4db8:	01dca023          	sw	t4,0(s9)
    4dbc:	0028de93          	srli	t4,a7,0x2
    4dc0:	003efe93          	andi	t4,t4,3
    4dc4:	01aeeeb3          	or	t4,t4,s10
    4dc8:	020f8d13          	addi	s10,t6,32
    4dcc:	01af0d33          	add	s10,t5,s10
    4dd0:	01dd2023          	sw	t4,0(s10)
    4dd4:	028f8e93          	addi	t4,t6,40
    4dd8:	01df0eb3          	add	t4,t5,t4
    4ddc:	00fea023          	sw	a5,0(t4)
    4de0:	00100e93          	li	t4,1
    4de4:	01daa023          	sw	t4,0(s5)
    4de8:	02088893          	addi	a7,a7,32
    4dec:	01da0a33          	add	s4,s4,t4
    4df0:	f19ff06f          	j	4d08 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x2a8>
    4df4:	00092983          	lw	s3,0(s2)
    4df8:	00492f83          	lw	t6,4(s2)
    4dfc:	01088493          	addi	s1,a7,16
    4e00:	3fe5a023          	sw	t5,992(a1)
    4e04:	3fc5a223          	sw	t3,996(a1)
    4e08:	3ef5a823          	sw	a5,1008(a1)
    4e0c:	3e95ae23          	sw	s1,1020(a1)
    4e10:	3f35aa23          	sw	s3,1012(a1)
    4e14:	3ff5ac23          	sw	t6,1016(a1)
    4e18:	00cf2f03          	lw	t5,12(t5)
    4e1c:	01ee0fb3          	add	t6,t3,t5
    4e20:	02af7933          	remu	s2,t5,a0
    4e24:	412f8fb3          	sub	t6,t6,s2
    4e28:	13fee263          	bltu	t4,t6,4f4c <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x4ec>
    4e2c:	40ff0f33          	sub	t5,t5,a5
    4e30:	01cf0f33          	add	t5,t5,t3
    4e34:	004f5793          	srli	a5,t5,0x4
    4e38:	10078263          	beqz	a5,4f3c <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x4dc>
    4e3c:	0ff0000f          	fence
    4e40:	0004af03          	lw	t5,0(s1)
    4e44:	0008ae83          	lw	t4,0(a7)
    4e48:	41ee8eb3          	sub	t4,t4,t5
    4e4c:	fefee8e3          	bltu	t4,a5,4e3c <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x3dc>
    4e50:	3f85ae83          	lw	t4,1016(a1)
    4e54:	3f45af03          	lw	t5,1012(a1)
    4e58:	00ae9e93          	slli	t4,t4,0xa
    4e5c:	004f1f13          	slli	t5,t5,0x4
    4e60:	01eeeeb3          	or	t4,t4,t5
    4e64:	00100f13          	li	t5,1
    4e68:	3fc5a883          	lw	a7,1020(a1)
    4e6c:	0fe69a63          	bne	a3,t5,4f60 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x500>
    4e70:	0008af03          	lw	t5,0(a7)
    4e74:	000074b7          	lui	s1,0x7
    4e78:	01e78f33          	add	t5,a5,t5
    4e7c:	01e8a023          	sw	t5,0(a7)
    4e80:	02800f13          	li	t5,40
    4e84:	04c48493          	addi	s1,s1,76 # 704c <__fw_export_text_end+0x1d1c>
    4e88:	03e60f33          	mul	t5,a2,t5
    4e8c:	009f0f33          	add	t5,t5,s1
    4e90:	000f2483          	lw	s1,0(t5)
    4e94:	00d484b3          	add	s1,s1,a3
    4e98:	009f2023          	sw	s1,0(t5)
    4e9c:	0002af03          	lw	t5,0(t0)
    4ea0:	fe0f1ee3          	bnez	t5,4e9c <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x43c>
    4ea4:	ffb20f37          	lui	t5,0xffb20
    4ea8:	044f0493          	addi	s1,t5,68 # ffb20044 <__stack_top+0x1e044>
    4eac:	009d84b3          	add	s1,s11,s1
    4eb0:	0004a483          	lw	s1,0(s1)
    4eb4:	00cf0493          	addi	s1,t5,12
    4eb8:	009804b3          	add	s1,a6,s1
    4ebc:	00400913          	li	s2,4
    4ec0:	0124a023          	sw	s2,0(s1)
    4ec4:	01e804b3          	add	s1,a6,t5
    4ec8:	0114a023          	sw	a7,0(s1)
    4ecc:	10000937          	lui	s2,0x10000
    4ed0:	004f0493          	addi	s1,t5,4
    4ed4:	012ef933          	and	s2,t4,s2
    4ed8:	009804b3          	add	s1,a6,s1
    4edc:	0124a023          	sw	s2,0(s1)
    4ee0:	004e9e93          	slli	t4,t4,0x4
    4ee4:	008f0493          	addi	s1,t5,8
    4ee8:	008ede93          	srli	t4,t4,0x8
    4eec:	009804b3          	add	s1,a6,s1
    4ef0:	01d4a023          	sw	t4,0(s1)
    4ef4:	01cf0e93          	addi	t4,t5,28
    4ef8:	000024b7          	lui	s1,0x2
    4efc:	01d80eb3          	add	t4,a6,t4
    4f00:	09148493          	addi	s1,s1,145 # 2091 <_start-0x17af>
    4f04:	009ea023          	sw	s1,0(t4)
    4f08:	0028d893          	srli	a7,a7,0x2
    4f0c:	00001eb7          	lui	t4,0x1
    4f10:	07ce8e93          	addi	t4,t4,124 # 107c <_start-0x27c4>
    4f14:	0038f893          	andi	a7,a7,3
    4f18:	01d8e8b3          	or	a7,a7,t4
    4f1c:	020f0e93          	addi	t4,t5,32
    4f20:	01d80eb3          	add	t4,a6,t4
    4f24:	028f0f13          	addi	t5,t5,40
    4f28:	011ea023          	sw	a7,0(t4)
    4f2c:	01e80f33          	add	t5,a6,t5
    4f30:	00ff2023          	sw	a5,0(t5)
    4f34:	00100793          	li	a5,1
    4f38:	00f2a023          	sw	a5,0(t0)
    4f3c:	000e0e93          	mv	t4,t3
    4f40:	3fd5a823          	sw	t4,1008(a1)
    4f44:	3ff5a423          	sw	t6,1000(a1)
    4f48:	dd1ff06f          	j	4d18 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x2b8>
    4f4c:	ffd78ae3          	beq	a5,t4,4f40 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x4e0>
    4f50:	40fe87b3          	sub	a5,t4,a5
    4f54:	0047d793          	srli	a5,a5,0x4
    4f58:	000e8e13          	mv	t3,t4
    4f5c:	eddff06f          	j	4e38 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x3d8>
    4f60:	0008af03          	lw	t5,0(a7)
    4f64:	01e78f33          	add	t5,a5,t5
    4f68:	01e8a023          	sw	t5,0(a7)
    4f6c:	0002af03          	lw	t5,0(t0)
    4f70:	fe0f1ee3          	bnez	t5,4f6c <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x50c>
    4f74:	00680f33          	add	t5,a6,t1
    4f78:	011f2023          	sw	a7,0(t5)
    4f7c:	00812f03          	lw	t5,8(sp)
    4f80:	0028d893          	srli	a7,a7,0x2
    4f84:	01eef4b3          	and	s1,t4,t5
    4f88:	00430f13          	addi	t5,t1,4
    4f8c:	01e80f33          	add	t5,a6,t5
    4f90:	009f2023          	sw	s1,0(t5)
    4f94:	00c12f03          	lw	t5,12(sp)
    4f98:	004ede93          	srli	t4,t4,0x4
    4f9c:	01eefeb3          	and	t4,t4,t5
    4fa0:	00830f13          	addi	t5,t1,8
    4fa4:	01e80f33          	add	t5,a6,t5
    4fa8:	01df2023          	sw	t4,0(t5)
    4fac:	01c30e93          	addi	t4,t1,28
    4fb0:	00002f37          	lui	t5,0x2
    4fb4:	01d80eb3          	add	t4,a6,t4
    4fb8:	091f0f13          	addi	t5,t5,145 # 2091 <_start-0x17af>
    4fbc:	01eea023          	sw	t5,0(t4)
    4fc0:	00001eb7          	lui	t4,0x1
    4fc4:	07ce8e93          	addi	t4,t4,124 # 107c <_start-0x27c4>
    4fc8:	0038f893          	andi	a7,a7,3
    4fcc:	01d8e8b3          	or	a7,a7,t4
    4fd0:	02030e93          	addi	t4,t1,32
    4fd4:	01d80eb3          	add	t4,a6,t4
    4fd8:	011ea023          	sw	a7,0(t4)
    4fdc:	02830893          	addi	a7,t1,40
    4fe0:	011808b3          	add	a7,a6,a7
    4fe4:	00f8a023          	sw	a5,0(a7)
    4fe8:	00100793          	li	a5,1
    4fec:	00f2a023          	sw	a5,0(t0)
    4ff0:	0003a783          	lw	a5,0(t2)
    4ff4:	00178793          	addi	a5,a5,1
    4ff8:	00f3a023          	sw	a5,0(t2)
    4ffc:	f41ff06f          	j	4f3c <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x4dc>

00005000 <_Z15noc_set_cfg_regmm>:
    5000:	8441a783          	lw	a5,-1980(gp) # ffb00034 <_ZL19active_noc_instance>
    5004:	ffec8737          	lui	a4,0xffec8
    5008:	00e79793          	slli	a5,a5,0xe
    500c:	04070713          	addi	a4,a4,64 # ffec8040 <__instrn_buffer+0x88040>
    5010:	00e787b3          	add	a5,a5,a4
    5014:	00a787b3          	add	a5,a5,a0
    5018:	00279793          	slli	a5,a5,0x2
    501c:	00b7a023          	sw	a1,0(a5)
    5020:	00008067          	ret

00005024 <_Z15noc_get_cfg_regm>:
    5024:	8441a783          	lw	a5,-1980(gp) # ffb00034 <_ZL19active_noc_instance>
    5028:	ffec8737          	lui	a4,0xffec8
    502c:	04070713          	addi	a4,a4,64 # ffec8040 <__instrn_buffer+0x88040>
    5030:	00e79793          	slli	a5,a5,0xe
    5034:	00e787b3          	add	a5,a5,a4
    5038:	00a787b3          	add	a5,a5,a0
    503c:	00279793          	slli	a5,a5,0x2
    5040:	0007a503          	lw	a0,0(a5)
    5044:	00008067          	ret

00005048 <wzerorange>:
    5048:	01050513          	addi	a0,a0,16
    504c:	02a5f463          	bgeu	a1,a0,5074 <wzerorange+0x2c>
    5050:	ff850793          	addi	a5,a0,-8
    5054:	00f5e863          	bltu	a1,a5,5064 <wzerorange+0x1c>
    5058:	fe052a23          	sw	zero,-12(a0)
    505c:	fe052823          	sw	zero,-16(a0)
    5060:	00050793          	mv	a5,a0
    5064:	ffc78713          	addi	a4,a5,-4
    5068:	00e5e463          	bltu	a1,a4,5070 <wzerorange+0x28>
    506c:	fe07ac23          	sw	zero,-8(a5)
    5070:	00008067          	ret
    5074:	fe052e23          	sw	zero,-4(a0)
    5078:	fe052c23          	sw	zero,-8(a0)
    507c:	fe052a23          	sw	zero,-12(a0)
    5080:	fe052823          	sw	zero,-16(a0)
    5084:	01050513          	addi	a0,a0,16
    5088:	fc5ff06f          	j	504c <wzerorange+0x4>

0000508c <_Z8wzeromemjm.constprop.0>:
    508c:	00003537          	lui	a0,0x3
    5090:	44050593          	addi	a1,a0,1088 # 3440 <_start-0x400>
    5094:	24050513          	addi	a0,a0,576
    5098:	fb1ff06f          	j	5048 <wzerorange>

0000509c <_Z12device_setupv>:
    509c:	ff010113          	addi	sp,sp,-16
    50a0:	00812423          	sw	s0,8(sp)
    50a4:	00000513          	li	a0,0
    50a8:	00112623          	sw	ra,12(sp)
    50ac:	00912223          	sw	s1,4(sp)
    50b0:	01212023          	sw	s2,0(sp)
    50b4:	a7cff0ef          	jal	4330 <_ZN13c_tensix_core15instrn_buf_baseEm>
    50b8:	87818413          	addi	s0,gp,-1928 # ffb00068 <cb_interface>
    50bc:	00050913          	mv	s2,a0
    50c0:	40a42023          	sw	a0,1024(s0)
    50c4:	00100513          	li	a0,1
    50c8:	a68ff0ef          	jal	4330 <_ZN13c_tensix_core15instrn_buf_baseEm>
    50cc:	40a42223          	sw	a0,1028(s0)
    50d0:	00200513          	li	a0,2
    50d4:	a5cff0ef          	jal	4330 <_ZN13c_tensix_core15instrn_buf_baseEm>
    50d8:	40a42423          	sw	a0,1032(s0)
    50dc:	ffb127b7          	lui	a5,0xffb12
    50e0:	ffb11537          	lui	a0,0xffb11
    50e4:	2407a023          	sw	zero,576(a5) # ffb12240 <__stack_top+0x10240>
    50e8:	03f00593          	li	a1,63
    50ec:	02450513          	addi	a0,a0,36 # ffb11024 <__stack_top+0xf024>
    50f0:	948ff0ef          	jal	4238 <_Z9WRITE_REGmm>
    50f4:	00000513          	li	a0,0
    50f8:	8401a223          	sw	zero,-1980(gp) # ffb00034 <_ZL19active_noc_instance>
    50fc:	f29ff0ef          	jal	5024 <_Z15noc_get_cfg_regm>
    5100:	00156593          	ori	a1,a0,1
    5104:	00000513          	li	a0,0
    5108:	ef9ff0ef          	jal	5000 <_Z15noc_set_cfg_regmm>
    510c:	00100413          	li	s0,1
    5110:	00100513          	li	a0,1
    5114:	f11ff0ef          	jal	5024 <_Z15noc_get_cfg_regm>
    5118:	00156593          	ori	a1,a0,1
    511c:	00100513          	li	a0,1
    5120:	ee1ff0ef          	jal	5000 <_Z15noc_set_cfg_regmm>
    5124:	8481a223          	sw	s0,-1980(gp) # ffb00034 <_ZL19active_noc_instance>
    5128:	00000513          	li	a0,0
    512c:	ef9ff0ef          	jal	5024 <_Z15noc_get_cfg_regm>
    5130:	008565b3          	or	a1,a0,s0
    5134:	00000513          	li	a0,0
    5138:	ec9ff0ef          	jal	5000 <_Z15noc_set_cfg_regmm>
    513c:	00040513          	mv	a0,s0
    5140:	ee5ff0ef          	jal	5024 <_Z15noc_get_cfg_regm>
    5144:	008565b3          	or	a1,a0,s0
    5148:	00040513          	mv	a0,s0
    514c:	eb5ff0ef          	jal	5000 <_Z15noc_set_cfg_regmm>
    5150:	8401a223          	sw	zero,-1980(gp) # ffb00034 <_ZL19active_noc_instance>
    5154:	821ff0ef          	jal	4974 <_Z22set_deassert_addressesv>
    5158:	f35ff0ef          	jal	508c <_Z8wzeromemjm.constprop.0>
    515c:	ffef07b7          	lui	a5,0xffef0
    5160:	01f00713          	li	a4,31
    5164:	2ee7a223          	sw	a4,740(a5) # ffef02e4 <__instrn_buffer+0xb02e4>
    5168:	00090513          	mv	a0,s2
    516c:	a1cff0ef          	jal	4388 <_ZN13c_tensix_core10ex_zeroaccEPVmmmm.constprop.0>
    5170:	00090513          	mv	a0,s2
    5174:	a18ff0ef          	jal	438c <_ZN13c_tensix_core7ex_enccEPVm>
    5178:	00090513          	mv	a0,s2
    517c:	a14ff0ef          	jal	4390 <_ZN13c_tensix_core13ex_load_constEPVm>
    5180:	00040613          	mv	a2,s0
    5184:	00040593          	mv	a1,s0
    5188:	00000513          	li	a0,0
    518c:	9f0ff0ef          	jal	437c <_ZN13c_tensix_core10ex_rmw_cfgEhmmmm.constprop.0>
    5190:	00040613          	mv	a2,s0
    5194:	00040513          	mv	a0,s0
    5198:	00200593          	li	a1,2
    519c:	9e0ff0ef          	jal	437c <_ZN13c_tensix_core10ex_rmw_cfgEhmmmm.constprop.0>
    51a0:	000045b7          	lui	a1,0x4
    51a4:	00300513          	li	a0,3
    51a8:	10000613          	li	a2,256
    51ac:	ff858593          	addi	a1,a1,-8 # 3ff8 <.NO_CB1960+0x324>
    51b0:	9ccff0ef          	jal	437c <_ZN13c_tensix_core10ex_rmw_cfgEhmmmm.constprop.0>
    51b4:	00812403          	lw	s0,8(sp)
    51b8:	00c12083          	lw	ra,12(sp)
    51bc:	00412483          	lw	s1,4(sp)
    51c0:	00090513          	mv	a0,s2
    51c4:	00012903          	lw	s2,0(sp)
    51c8:	01010113          	addi	sp,sp,16
    51cc:	9f4ff06f          	j	43c0 <_ZN13c_tensix_core28initialize_tensix_semaphoresEPVm>

000051d0 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>:
    51d0:	00200793          	li	a5,2
    51d4:	02c7c063          	blt	a5,a2,51f4 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x24>
    51d8:	00c05c63          	blez	a2,51f0 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x20>
    51dc:	0005a703          	lw	a4,0(a1)
    51e0:	00e52023          	sw	a4,0(a0)
    51e4:	00f61663          	bne	a2,a5,51f0 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x20>
    51e8:	0045a783          	lw	a5,4(a1)
    51ec:	00f52223          	sw	a5,4(a0)
    51f0:	00008067          	ret
    51f4:	0005a803          	lw	a6,0(a1)
    51f8:	0045a683          	lw	a3,4(a1)
    51fc:	0085a703          	lw	a4,8(a1)
    5200:	00c58593          	addi	a1,a1,12
    5204:	00c50513          	addi	a0,a0,12
    5208:	ffd60613          	addi	a2,a2,-3
    520c:	ff052a23          	sw	a6,-12(a0)
    5210:	fed52c23          	sw	a3,-8(a0)
    5214:	fee52e23          	sw	a4,-4(a0)
    5218:	fbdff06f          	j	51d4 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x4>

0000521c <_Z7do_crt1U11rvtt_l1_ptrPm.constprop.0>:
    521c:	ffb015b7          	lui	a1,0xffb01
    5220:	ff010113          	addi	sp,sp,-16
    5224:	89858593          	addi	a1,a1,-1896 # ffb00898 <__ldm_bss_end>
    5228:	81418513          	addi	a0,gp,-2028 # ffb00004 <prev_noc_mode>
    522c:	00112623          	sw	ra,12(sp)
    5230:	e19ff0ef          	jal	5048 <wzerorange>
    5234:	000085b7          	lui	a1,0x8
    5238:	81018513          	addi	a0,gp,-2032 # ffb00000 <_ZL16subordinate_sync>
    523c:	6b058593          	addi	a1,a1,1712 # 86b0 <__fw_export_text_end+0x3380>
    5240:	02b50063          	beq	a0,a1,5260 <_Z7do_crt1U11rvtt_l1_ptrPm.constprop.0+0x44>
    5244:	ffb00637          	lui	a2,0xffb00
    5248:	00460613          	addi	a2,a2,4 # ffb00004 <prev_noc_mode>
    524c:	00c12083          	lw	ra,12(sp)
    5250:	40a60633          	sub	a2,a2,a0
    5254:	40265613          	srai	a2,a2,0x2
    5258:	01010113          	addi	sp,sp,16
    525c:	f75ff06f          	j	51d0 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    5260:	00c12083          	lw	ra,12(sp)
    5264:	01010113          	addi	sp,sp,16
    5268:	00008067          	ret

0000526c <_Z19noc_bank_table_inity.constprop.0>:
    526c:	ff010113          	addi	sp,sp,-16
    5270:	00812423          	sw	s0,8(sp)
    5274:	00912223          	sw	s1,4(sp)
    5278:	87818413          	addi	s0,gp,-1928 # ffb00068 <cb_interface>
    527c:	000114b7          	lui	s1,0x11
    5280:	6b048593          	addi	a1,s1,1712 # 116b0 <__fw_export_text_end+0xc380>
    5284:	40c40513          	addi	a0,s0,1036
    5288:	00700613          	li	a2,7
    528c:	00112623          	sw	ra,12(sp)
    5290:	f41ff0ef          	jal	51d0 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    5294:	6cc48593          	addi	a1,s1,1740
    5298:	42840513          	addi	a0,s0,1064
    529c:	07800613          	li	a2,120
    52a0:	f31ff0ef          	jal	51d0 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    52a4:	000124b7          	lui	s1,0x12
    52a8:	8ac48593          	addi	a1,s1,-1876 # 118ac <__fw_export_text_end+0xc57c>
    52ac:	60840513          	addi	a0,s0,1544
    52b0:	00700613          	li	a2,7
    52b4:	f1dff0ef          	jal	51d0 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    52b8:	62440513          	addi	a0,s0,1572
    52bc:	00812403          	lw	s0,8(sp)
    52c0:	00c12083          	lw	ra,12(sp)
    52c4:	8c848593          	addi	a1,s1,-1848
    52c8:	00412483          	lw	s1,4(sp)
    52cc:	07800613          	li	a2,120
    52d0:	01010113          	addi	sp,sp,16
    52d4:	efdff06f          	j	51d0 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>

000052d8 <_Z38noc_worker_logical_to_virtual_map_inity.constprop.0>:
    52d8:	ff010113          	addi	sp,sp,-16
    52dc:	00812423          	sw	s0,8(sp)
    52e0:	ffb01437          	lui	s0,0xffb01
    52e4:	00912223          	sw	s1,4(sp)
    52e8:	06840413          	addi	s0,s0,104 # ffb01068 <__fw_export_ldm_end+0x7c8>
    52ec:	000124b7          	lui	s1,0x12
    52f0:	eb048593          	addi	a1,s1,-336 # 11eb0 <__fw_export_text_end+0xcb80>
    52f4:	80440513          	addi	a0,s0,-2044
    52f8:	00500613          	li	a2,5
    52fc:	00112623          	sw	ra,12(sp)
    5300:	ed1ff0ef          	jal	51d0 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    5304:	81840513          	addi	a0,s0,-2024
    5308:	00812403          	lw	s0,8(sp)
    530c:	00c12083          	lw	ra,12(sp)
    5310:	ec448593          	addi	a1,s1,-316
    5314:	00412483          	lw	s1,4(sp)
    5318:	00300613          	li	a2,3
    531c:	01010113          	addi	sp,sp,16
    5320:	eb1ff06f          	j	51d0 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>

00005324 <exit>:
    5324:	0000006f          	j	5324 <exit>
