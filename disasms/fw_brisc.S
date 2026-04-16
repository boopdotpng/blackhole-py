
/tmp/tt-disasm-fw_brisc-mm83t578/out.elf:     file format elf32-littleriscv


Disassembly of section .text:

00003840 <_start>:
    3840:	ffb001b7          	lui	gp,0xffb00
    3844:	7f018193          	addi	gp,gp,2032 # ffb007f0 <__global_pointer$>
    3848:	ffb02137          	lui	sp,0xffb02
    384c:	ff010113          	addi	sp,sp,-16 # ffb01ff0 <__fw_export_ldm_end+0x1770>
    3850:	00810513          	addi	a0,sp,8
    3854:	00a12023          	sw	a0,0(sp)
    3858:	00012223          	sw	zero,4(sp)
    385c:	00912423          	sw	s1,8(sp)
    3860:	00012623          	sw	zero,12(sp)
    3864:	00100513          	li	a0,1
    3868:	00010593          	mv	a1,sp
    386c:	00000613          	li	a2,0
    3870:	008000ef          	jal	3878 <main>
    3874:	3840106f          	j	4bf8 <exit>

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
    38e0:	210010ef          	jal	4af0 <_Z7do_crt1U11rvtt_l1_ptrPm.constprop.0>
    38e4:	25c010ef          	jal	4b40 <_Z19noc_bank_table_inity.constprop.0>
    38e8:	2c4010ef          	jal	4bac <_Z38noc_worker_logical_to_virtual_map_inity.constprop.0>
    38ec:	06002623          	sw	zero,108(zero) # 6c <_start-0x37d4>
    38f0:	84018123          	sb	zero,-1982(gp) # ffb00032 <noc_index>
    38f4:	000017b7          	lui	a5,0x1
    38f8:	9a07c703          	lbu	a4,-1632(a5) # 9a0 <_start-0x2ea0>
    38fc:	06078793          	addi	a5,a5,96
    3900:	ffb22437          	lui	s0,0xffb22
    3904:	83818a93          	addi	s5,gp,-1992 # ffb00028 <noc_reads_num_issued>
    3908:	83018b13          	addi	s6,gp,-2000 # ffb00020 <noc_nonposted_writes_num_issued>
    390c:	82818b93          	addi	s7,gp,-2008 # ffb00018 <noc_nonposted_writes_acked>
    3910:	84418c13          	addi	s8,gp,-1980 # ffb00034 <noc_nonposted_atomics_acked>
    3914:	84e180a3          	sb	a4,-1983(gp) # ffb00031 <my_logical_x_>
    3918:	9417c783          	lbu	a5,-1727(a5)
    391c:	82018993          	addi	s3,gp,-2016 # ffb00010 <noc_posted_writes_num_issued>
    3920:	84f18023          	sb	a5,-1984(gp) # ffb00030 <my_logical_y_>
    3924:	77c000ef          	jal	40a0 <_Z9risc_initv>
    3928:	048010ef          	jal	4970 <_Z12device_setupv>
    392c:	06002023          	sw	zero,96(zero) # 60 <_start-0x37e0>
    3930:	14d000ef          	jal	427c <_Z21deassert_ncrisc_triscv>
    3934:	1a5000ef          	jal	42d8 <_Z17wait_ncrisc_triscv>
    3938:	360009a3          	sb	zero,883(zero) # 373 <_start-0x34cd>
    393c:	ffb20637          	lui	a2,0xffb20
    3940:	14862703          	lw	a4,328(a2) # ffb20148 <__stack_top+0x1e148>
    3944:	00062223          	sw	zero,4(a2)
    3948:	00675793          	srli	a5,a4,0x6
    394c:	03f7f793          	andi	a5,a5,63
    3950:	03f77713          	andi	a4,a4,63
    3954:	00471713          	slli	a4,a4,0x4
    3958:	00a79793          	slli	a5,a5,0xa
    395c:	00e7e7b3          	or	a5,a5,a4
    3960:	0047d793          	srli	a5,a5,0x4
    3964:	00f62423          	sw	a5,8(a2)
    3968:	ffb21737          	lui	a4,0xffb21
    396c:	00072223          	sw	zero,4(a4) # ffb21004 <__stack_top+0x1f004>
    3970:	00f72423          	sw	a5,8(a4)
    3974:	00400513          	li	a0,4
    3978:	80a42623          	sw	a0,-2036(s0) # ffb2180c <__stack_top+0x1f80c>
    397c:	80042823          	sw	zero,-2032(s0)
    3980:	000026b7          	lui	a3,0x2
    3984:	80f42a23          	sw	a5,-2028(s0)
    3988:	09068693          	addi	a3,a3,144 # 2090 <_start-0x17b0>
    398c:	80d72e23          	sw	a3,-2020(a4)
    3990:	80072823          	sw	zero,-2032(a4)
    3994:	80f72a23          	sw	a5,-2028(a4)
    3998:	ffb305b7          	lui	a1,0xffb30
    399c:	1485a703          	lw	a4,328(a1) # ffb30148 <__stack_top+0x2e148>
    39a0:	0005a223          	sw	zero,4(a1)
    39a4:	00675793          	srli	a5,a4,0x6
    39a8:	03f7f793          	andi	a5,a5,63
    39ac:	03f77713          	andi	a4,a4,63
    39b0:	00471713          	slli	a4,a4,0x4
    39b4:	00a79793          	slli	a5,a5,0xa
    39b8:	00e7e7b3          	or	a5,a5,a4
    39bc:	0047d793          	srli	a5,a5,0x4
    39c0:	00f5a423          	sw	a5,8(a1)
    39c4:	ffb31737          	lui	a4,0xffb31
    39c8:	00072223          	sw	zero,4(a4) # ffb31004 <__stack_top+0x2f004>
    39cc:	00f72423          	sw	a5,8(a4)
    39d0:	ffb325b7          	lui	a1,0xffb32
    39d4:	80a5a623          	sw	a0,-2036(a1) # ffb3180c <__stack_top+0x2f80c>
    39d8:	8005a823          	sw	zero,-2032(a1)
    39dc:	80f5aa23          	sw	a5,-2028(a1)
    39e0:	80d72e23          	sw	a3,-2020(a4)
    39e4:	80072823          	sw	zero,-2032(a4)
    39e8:	80f72a23          	sw	a5,-2028(a4)
    39ec:	20862503          	lw	a0,520(a2)
    39f0:	22862583          	lw	a1,552(a2)
    39f4:	20462683          	lw	a3,516(a2)
    39f8:	20062703          	lw	a4,512(a2)
    39fc:	22c62783          	lw	a5,556(a2)
    3a00:	00aaa023          	sw	a0,0(s5)
    3a04:	00bb2023          	sw	a1,0(s6)
    3a08:	00dba023          	sw	a3,0(s7)
    3a0c:	00ec2023          	sw	a4,0(s8)
    3a10:	00f9a023          	sw	a5,0(s3)
    3a14:	0dd000ef          	jal	42f0 <_Z26trigger_sync_register_initv>
    3a18:	8101a783          	lw	a5,-2032(gp) # ffb00000 <_ZL16subordinate_sync>
    3a1c:	00f12623          	sw	a5,12(sp)
    3a20:	06000c93          	li	s9,96
    3a24:	ffb707b7          	lui	a5,0xffb70
    3a28:	000025b7          	lui	a1,0x2
    3a2c:	08000d13          	li	s10,128
    3a30:	43878d93          	addi	s11,a5,1080 # ffb70438 <__stack_top+0x6e438>
    3a34:	84040813          	addi	a6,s0,-1984
    3a38:	04000893          	li	a7,64
    3a3c:	81c40313          	addi	t1,s0,-2020
    3a40:	08a58593          	addi	a1,a1,138 # 208a <_start-0x17b6>
    3a44:	80040e13          	addi	t3,s0,-2048
    3a48:	80440e93          	addi	t4,s0,-2044
    3a4c:	80840f13          	addi	t5,s0,-2040
    3a50:	82040f93          	addi	t6,s0,-2016
    3a54:	00100293          	li	t0,1
    3a58:	0e000393          	li	t2,224
    3a5c:	0f000493          	li	s1,240
    3a60:	3a002783          	lw	a5,928(zero) # 3a0 <_start-0x34a0>
    3a64:	00279793          	slli	a5,a5,0x2
    3a68:	37078793          	addi	a5,a5,880
    3a6c:	0037c783          	lbu	a5,3(a5)
    3a70:	0ff7f713          	zext.b	a4,a5
    3a74:	03a78063          	beq	a5,s10,3a94 <main+0x21c>
    3a78:	06c02783          	lw	a5,108(zero) # 6c <_start-0x37d4>
    3a7c:	00178793          	addi	a5,a5,1
    3a80:	039787b3          	mul	a5,a5,s9
    3a84:	06078793          	addi	a5,a5,96
    3a88:	00f7c783          	lbu	a5,15(a5)
    3a8c:	60479793          	sext.b	a5,a5
    3a90:	3207d263          	bgez	a5,3db4 <.NO_CB1455+0x150>
    3a94:	06c02903          	lw	s2,108(zero) # 6c <_start-0x37d4>
    3a98:	039904b3          	mul	s1,s2,s9
    3a9c:	0bc4ad83          	lw	s11,188(s1)
    3aa0:	07048493          	addi	s1,s1,112
    3aa4:	002df793          	andi	a5,s11,2
    3aa8:	3c079463          	bnez	a5,3e70 <.NO_CB1455+0x20c>
    3aac:	06c02783          	lw	a5,108(zero) # 6c <_start-0x37d4>
    3ab0:	ffb01737          	lui	a4,0xffb01
    3ab4:	04870713          	addi	a4,a4,72 # ffb01048 <__fw_export_ldm_end+0x7c8>
    3ab8:	000d8513          	mv	a0,s11
    3abc:	039787b3          	mul	a5,a5,s9
    3ac0:	0707ad03          	lw	s10,112(a5)
    3ac4:	07c7d683          	lhu	a3,124(a5)
    3ac8:	0747a603          	lw	a2,116(a5)
    3acc:	06078793          	addi	a5,a5,96
    3ad0:	01a686b3          	add	a3,a3,s10
    3ad4:	82d72223          	sw	a3,-2012(a4)
    3ad8:	01e7d683          	lhu	a3,30(a5)
    3adc:	00c686b3          	add	a3,a3,a2
    3ae0:	82d72423          	sw	a3,-2008(a4)
    3ae4:	0187a603          	lw	a2,24(a5)
    3ae8:	0207d683          	lhu	a3,32(a5)
    3aec:	00c686b3          	add	a3,a3,a2
    3af0:	82d72623          	sw	a3,-2004(a4)
    3af4:	0267d703          	lhu	a4,38(a5)
    3af8:	0287d783          	lhu	a5,40(a5)
    3afc:	01a70733          	add	a4,a4,s10
    3b00:	80e1ae23          	sw	a4,-2020(gp) # ffb0000c <rta_l1_base>
    3b04:	01a787b3          	add	a5,a5,s10
    3b08:	80f1ac23          	sw	a5,-2024(gp) # ffb00008 <crta_l1_base>
    3b0c:	ffef07b7          	lui	a5,0xffef0
    3b10:	01f00713          	li	a4,31
    3b14:	2ee7a223          	sw	a4,740(a5) # ffef02e4 <__instrn_buffer+0xb02e4>
    3b18:	778000ef          	jal	4290 <_Z10run_triscsm>
    3b1c:	0444c603          	lbu	a2,68(s1)
    3b20:	8411c783          	lbu	a5,-1983(gp) # ffb00031 <my_logical_x_>
    3b24:	0454c583          	lbu	a1,69(s1)
    3b28:	05c4c703          	lbu	a4,92(s1)
    3b2c:	0ff67613          	zext.b	a2,a2
    3b30:	40e787b3          	sub	a5,a5,a4
    3b34:	80f18b23          	sb	a5,-2026(gp) # ffb00006 <my_relative_x_>
    3b38:	05d4c703          	lbu	a4,93(s1)
    3b3c:	8401c783          	lbu	a5,-1984(gp) # ffb00030 <my_logical_y_>
    3b40:	40e787b3          	sub	a5,a5,a4
    3b44:	80f18aa3          	sb	a5,-2027(gp) # ffb00005 <my_relative_y_>
    3b48:	84c18123          	sb	a2,-1982(gp) # ffb00032 <noc_index>
    3b4c:	8141c783          	lbu	a5,-2028(gp) # ffb00004 <prev_noc_mode>
    3b50:	0ff5fe13          	zext.b	t3,a1
    3b54:	ffb20737          	lui	a4,0xffb20
    3b58:	3c059c63          	bnez	a1,3f30 <.NO_CB1455+0x2cc>
    3b5c:	32079263          	bnez	a5,3e80 <.NO_CB1455+0x21c>
    3b60:	ffb20737          	lui	a4,0xffb20
    3b64:	01061793          	slli	a5,a2,0x10
    3b68:	20870593          	addi	a1,a4,520 # ffb20208 <__stack_top+0x1e208>
    3b6c:	00b785b3          	add	a1,a5,a1
    3b70:	0005a883          	lw	a7,0(a1)
    3b74:	22870593          	addi	a1,a4,552
    3b78:	00b785b3          	add	a1,a5,a1
    3b7c:	0005a803          	lw	a6,0(a1)
    3b80:	20470593          	addi	a1,a4,516
    3b84:	00b785b3          	add	a1,a5,a1
    3b88:	0005a503          	lw	a0,0(a1)
    3b8c:	20070593          	addi	a1,a4,512
    3b90:	22c70713          	addi	a4,a4,556
    3b94:	00b785b3          	add	a1,a5,a1
    3b98:	00e787b3          	add	a5,a5,a4
    3b9c:	0005a583          	lw	a1,0(a1)
    3ba0:	0007a703          	lw	a4,0(a5)
    3ba4:	215647b3          	sh2add	a5,a2,s5
    3ba8:	0117a023          	sw	a7,0(a5)
    3bac:	216647b3          	sh2add	a5,a2,s6
    3bb0:	0107a023          	sw	a6,0(a5)
    3bb4:	217647b3          	sh2add	a5,a2,s7
    3bb8:	00a7a023          	sw	a0,0(a5)
    3bbc:	218647b3          	sh2add	a5,a2,s8
    3bc0:	00b7a023          	sw	a1,0(a5)
    3bc4:	213647b3          	sh2add	a5,a2,s3
    3bc8:	00e7a023          	sw	a4,0(a5)
    3bcc:	00300713          	li	a4,3
    3bd0:	0124d783          	lhu	a5,18(s1)
    3bd4:	000d8513          	mv	a0,s11
    3bd8:	0807c7b3          	zext.h	a5,a5
    3bdc:	00e12e23          	sw	a4,28(sp)
    3be0:	00c12c23          	sw	a2,24(sp)
    3be4:	81c18a23          	sb	t3,-2028(gp) # ffb00004 <prev_noc_mode>
    3be8:	01c12a23          	sw	t3,20(sp)
    3bec:	00f12823          	sw	a5,16(sp)
    3bf0:	6d0000ef          	jal	42c0 <_Z29start_ncrisc_kernel_run_earlym>
    3bf4:	001dfd93          	andi	s11,s11,1
    3bf8:	01412e03          	lw	t3,20(sp)
    3bfc:	01812603          	lw	a2,24(sp)
    3c00:	01c12703          	lw	a4,28(sp)
    3c04:	420d8863          	beqz	s11,4034 <.NO_CB1455+0x3d0>
    3c08:	01012783          	lw	a5,16(sp)
    3c0c:	0404a583          	lw	a1,64(s1)
    3c10:	01a787b3          	add	a5,a5,s10
    3c14:	85818513          	addi	a0,gp,-1960 # ffb00048 <cb_interface>
    3c18:	0580006f          	j	3c70 <.NO_CB1455+0xc>
    3c1c:	0047a683          	lw	a3,4(a5)
    3c20:	0007a603          	lw	a2,0(a5)
    3c24:	0087a803          	lw	a6,8(a5)
    3c28:	00c7a883          	lw	a7,12(a5)
    3c2c:	0015d593          	srli	a1,a1,0x1
    3c30:	0015f293          	andi	t0,a1,1
    3c34:	00052c23          	sw	zero,24(a0)
    3c38:	01078793          	addi	a5,a5,16
    3c3c:	00d52023          	sw	a3,0(a0)
    3c40:	00d606b3          	add	a3,a2,a3
    3c44:	00d52223          	sw	a3,4(a0)
    3c48:	00c52a23          	sw	a2,20(a0)
    3c4c:	01052623          	sw	a6,12(a0)
    3c50:	00c52823          	sw	a2,16(a0)
    3c54:	01152423          	sw	a7,8(a0)
    3c58:	02050513          	addi	a0,a0,32
    3c5c:	fc0290e3          	bnez	t0,3c1c <main+0x3a4>
    3c60:	00058e63          	beqz	a1,3c7c <.NO_CB1455+0x18>

00003c64 <.NO_CB1455>:
    3c64:	01078793          	addi	a5,a5,16
    3c68:	02050513          	addi	a0,a0,32
    3c6c:	0015d593          	srli	a1,a1,0x1
    3c70:	0015f293          	andi	t0,a1,1
    3c74:	fa0294e3          	bnez	t0,3c1c <main+0x3a4>
    3c78:	fe0596e3          	bnez	a1,3c64 <.NO_CB1455>
    3c7c:	0144d503          	lhu	a0,20(s1)
    3c80:	8421cd83          	lbu	s11,-1982(gp) # ffb00032 <noc_index>
    3c84:	0464c583          	lbu	a1,70(s1)
    3c88:	000e0693          	mv	a3,t3
    3c8c:	0ff5f593          	zext.b	a1,a1
    3c90:	000d8613          	mv	a2,s11
    3c94:	01a50533          	add	a0,a0,s10
    3c98:	00b12823          	sw	a1,16(sp)
    3c9c:	698000ef          	jal	4334 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0>
    3ca0:	01012583          	lw	a1,16(sp)
    3ca4:	000d8513          	mv	a0,s11
    3ca8:	658000ef          	jal	4300 <_Z33barrier_remote_cb_interface_setuphm>
    3cac:	02c4a783          	lw	a5,44(s1)
    3cb0:	01a787b3          	add	a5,a5,s10
    3cb4:	000780e7          	jalr	a5
    3cb8:	620000ef          	jal	42d8 <_Z17wait_ncrisc_triscv>
    3cbc:	634000ef          	jal	42f0 <_Z26trigger_sync_register_initv>
    3cc0:	3a002783          	lw	a5,928(zero) # 3a0 <_start-0x34a0>
    3cc4:	00279793          	slli	a5,a5,0x2
    3cc8:	360789a3          	sb	zero,883(a5)
    3ccc:	02a4c703          	lbu	a4,42(s1)
    3cd0:	06078793          	addi	a5,a5,96
    3cd4:	d40718e3          	bnez	a4,3a24 <main+0x1ac>
    3cd8:	0404a623          	sw	zero,76(s1)
    3cdc:	8421c583          	lbu	a1,-1982(gp) # ffb00032 <noc_index>
    3ce0:	04048fa3          	sb	zero,95(s1)
    3ce4:	3107a703          	lw	a4,784(a5)
    3ce8:	84040513          	addi	a0,s0,-1984
    3cec:	01059793          	slli	a5,a1,0x10
    3cf0:	00a78533          	add	a0,a5,a0
    3cf4:	00052683          	lw	a3,0(a0)
    3cf8:	fe069ee3          	bnez	a3,3cf4 <.NO_CB1455+0x90>
    3cfc:	01075613          	srli	a2,a4,0x10
    3d00:	00875693          	srli	a3,a4,0x8
    3d04:	0ff67613          	zext.b	a2,a2
    3d08:	0ff6f693          	zext.b	a3,a3
    3d0c:	00469693          	slli	a3,a3,0x4
    3d10:	00a61613          	slli	a2,a2,0xa
    3d14:	00d66633          	or	a2,a2,a3
    3d18:	0ff77713          	zext.b	a4,a4
    3d1c:	ffb706b7          	lui	a3,0xffb70
    3d20:	43868693          	addi	a3,a3,1080 # ffb70438 <__stack_top+0x6e438>
    3d24:	00c71713          	slli	a4,a4,0xc
    3d28:	00d70733          	add	a4,a4,a3
    3d2c:	82840693          	addi	a3,s0,-2008
    3d30:	00d786b3          	add	a3,a5,a3
    3d34:	04000813          	li	a6,64
    3d38:	0106a023          	sw	a6,0(a3)
    3d3c:	81c40693          	addi	a3,s0,-2020
    3d40:	00002837          	lui	a6,0x2
    3d44:	00d786b3          	add	a3,a5,a3
    3d48:	08a80813          	addi	a6,a6,138 # 208a <_start-0x17b6>
    3d4c:	0106a023          	sw	a6,0(a3)
    3d50:	80040693          	addi	a3,s0,-2048
    3d54:	00d786b3          	add	a3,a5,a3
    3d58:	00e6a023          	sw	a4,0(a3)
    3d5c:	80440713          	addi	a4,s0,-2044
    3d60:	00e78733          	add	a4,a5,a4
    3d64:	00072023          	sw	zero,0(a4)
    3d68:	80840713          	addi	a4,s0,-2040
    3d6c:	00e78733          	add	a4,a5,a4
    3d70:	00465613          	srli	a2,a2,0x4
    3d74:	00c72023          	sw	a2,0(a4)
    3d78:	82040713          	addi	a4,s0,-2016
    3d7c:	00e787b3          	add	a5,a5,a4
    3d80:	0007a023          	sw	zero,0(a5)
    3d84:	00100793          	li	a5,1
    3d88:	00f52023          	sw	a5,0(a0)
    3d8c:	2135c7b3          	sh2add	a5,a1,s3
    3d90:	0007a703          	lw	a4,0(a5)
    3d94:	00190913          	addi	s2,s2,1
    3d98:	00170713          	addi	a4,a4,1
    3d9c:	00e7a023          	sw	a4,0(a5)
    3da0:	00797913          	andi	s2,s2,7
    3da4:	07202623          	sw	s2,108(zero) # 6c <_start-0x37d4>
    3da8:	c79ff06f          	j	3a20 <main+0x1a8>
    3dac:	06002623          	sw	zero,108(zero) # 6c <_start-0x37d4>
    3db0:	cb1ff06f          	j	3a60 <main+0x1e8>
    3db4:	0ff0000f          	fence
    3db8:	0c000793          	li	a5,192
    3dbc:	00f70663          	beq	a4,a5,3dc8 <.NO_CB1455+0x164>
    3dc0:	fe7706e3          	beq	a4,t2,3dac <.NO_CB1455+0x148>
    3dc4:	c8971ee3          	bne	a4,s1,3a60 <main+0x1e8>
    3dc8:	06002623          	sw	zero,108(zero) # 6c <_start-0x37d4>
    3dcc:	3a002783          	lw	a5,928(zero) # 3a0 <_start-0x34a0>
    3dd0:	00279713          	slli	a4,a5,0x2
    3dd4:	37072683          	lw	a3,880(a4)
    3dd8:	00279793          	slli	a5,a5,0x2
    3ddc:	0106d713          	srli	a4,a3,0x10
    3de0:	0086d613          	srli	a2,a3,0x8
    3de4:	0ff77713          	zext.b	a4,a4
    3de8:	0ff67613          	zext.b	a2,a2
    3dec:	00461613          	slli	a2,a2,0x4
    3df0:	360789a3          	sb	zero,883(a5)
    3df4:	00a71713          	slli	a4,a4,0xa
    3df8:	00c76733          	or	a4,a4,a2
    3dfc:	8421c603          	lbu	a2,-1982(gp) # ffb00032 <noc_index>
    3e00:	0ff6f693          	zext.b	a3,a3
    3e04:	00c69693          	slli	a3,a3,0xc
    3e08:	01061793          	slli	a5,a2,0x10
    3e0c:	01b686b3          	add	a3,a3,s11
    3e10:	01078533          	add	a0,a5,a6
    3e14:	00052903          	lw	s2,0(a0)
    3e18:	fe091ee3          	bnez	s2,3e14 <.NO_CB1455+0x1b0>
    3e1c:	ffb22937          	lui	s2,0xffb22
    3e20:	21364633          	sh2add	a2,a2,s3
    3e24:	82890913          	addi	s2,s2,-2008 # ffb21828 <__stack_top+0x1f828>
    3e28:	01278933          	add	s2,a5,s2
    3e2c:	01192023          	sw	a7,0(s2)
    3e30:	00678933          	add	s2,a5,t1
    3e34:	00b92023          	sw	a1,0(s2)
    3e38:	01c78933          	add	s2,a5,t3
    3e3c:	00d92023          	sw	a3,0(s2)
    3e40:	01d786b3          	add	a3,a5,t4
    3e44:	0006a023          	sw	zero,0(a3)
    3e48:	00475713          	srli	a4,a4,0x4
    3e4c:	01e786b3          	add	a3,a5,t5
    3e50:	00e6a023          	sw	a4,0(a3)
    3e54:	01f787b3          	add	a5,a5,t6
    3e58:	0007a023          	sw	zero,0(a5)
    3e5c:	00552023          	sw	t0,0(a0)
    3e60:	00062783          	lw	a5,0(a2)
    3e64:	00178793          	addi	a5,a5,1
    3e68:	00f62023          	sw	a5,0(a2)
    3e6c:	bf5ff06f          	j	3a60 <main+0x1e8>
    3e70:	00c12703          	lw	a4,12(sp)
    3e74:	00100793          	li	a5,1
    3e78:	00f70023          	sb	a5,0(a4)
    3e7c:	c31ff06f          	j	3aac <main+0x234>
    3e80:	14872583          	lw	a1,328(a4)
    3e84:	00072223          	sw	zero,4(a4)
    3e88:	0065d793          	srli	a5,a1,0x6
    3e8c:	03f7f793          	andi	a5,a5,63
    3e90:	03f5f593          	andi	a1,a1,63
    3e94:	00459593          	slli	a1,a1,0x4
    3e98:	00a79793          	slli	a5,a5,0xa
    3e9c:	00b7e7b3          	or	a5,a5,a1
    3ea0:	0047d793          	srli	a5,a5,0x4
    3ea4:	00f72423          	sw	a5,8(a4)
    3ea8:	ffb21537          	lui	a0,0xffb21
    3eac:	00052223          	sw	zero,4(a0) # ffb21004 <__stack_top+0x1f004>
    3eb0:	00f52423          	sw	a5,8(a0)
    3eb4:	00400593          	li	a1,4
    3eb8:	80b42623          	sw	a1,-2036(s0)
    3ebc:	80042823          	sw	zero,-2032(s0)
    3ec0:	00002737          	lui	a4,0x2
    3ec4:	80f42a23          	sw	a5,-2028(s0)
    3ec8:	09070713          	addi	a4,a4,144 # 2090 <_start-0x17b0>
    3ecc:	80e52e23          	sw	a4,-2020(a0)
    3ed0:	80052823          	sw	zero,-2032(a0)
    3ed4:	80f52a23          	sw	a5,-2028(a0)
    3ed8:	ffb30537          	lui	a0,0xffb30
    3edc:	14852803          	lw	a6,328(a0) # ffb30148 <__stack_top+0x2e148>
    3ee0:	00052223          	sw	zero,4(a0)
    3ee4:	00685793          	srli	a5,a6,0x6
    3ee8:	03f7f793          	andi	a5,a5,63
    3eec:	03f87813          	andi	a6,a6,63
    3ef0:	00481813          	slli	a6,a6,0x4
    3ef4:	00a79793          	slli	a5,a5,0xa
    3ef8:	0107e7b3          	or	a5,a5,a6
    3efc:	0047d793          	srli	a5,a5,0x4
    3f00:	00f52423          	sw	a5,8(a0)
    3f04:	ffb31537          	lui	a0,0xffb31
    3f08:	00052223          	sw	zero,4(a0) # ffb31004 <__stack_top+0x2f004>
    3f0c:	00f52423          	sw	a5,8(a0)
    3f10:	ffb32837          	lui	a6,0xffb32
    3f14:	80b82623          	sw	a1,-2036(a6) # ffb3180c <__stack_top+0x2f80c>
    3f18:	80082823          	sw	zero,-2032(a6)
    3f1c:	80f82a23          	sw	a5,-2028(a6)
    3f20:	80e52e23          	sw	a4,-2020(a0)
    3f24:	80052823          	sw	zero,-2032(a0)
    3f28:	80f52a23          	sw	a5,-2028(a0)
    3f2c:	c35ff06f          	j	3b60 <main+0x2e8>
    3f30:	08fe1863          	bne	t3,a5,3fc0 <.NO_CB1455+0x35c>
    3f34:	ffb20737          	lui	a4,0xffb20
    3f38:	20872383          	lw	t2,520(a4) # ffb20208 <__stack_top+0x1e208>
    3f3c:	ffb307b7          	lui	a5,0xffb30
    3f40:	2087a283          	lw	t0,520(a5) # ffb30208 <__stack_top+0x2e208>
    3f44:	22872f83          	lw	t6,552(a4)
    3f48:	2287af03          	lw	t5,552(a5)
    3f4c:	20472e83          	lw	t4,516(a4)
    3f50:	2047a883          	lw	a7,516(a5)
    3f54:	20072803          	lw	a6,512(a4)
    3f58:	2007a503          	lw	a0,512(a5)
    3f5c:	22c72583          	lw	a1,556(a4)
    3f60:	22c7a703          	lw	a4,556(a5)
    3f64:	000077b7          	lui	a5,0x7
    3f68:	0477a023          	sw	t2,64(a5) # 7040 <__fw_export_text_end+0x2440>
    3f6c:	0607a423          	sw	zero,104(a5)
    3f70:	0407aa23          	sw	zero,84(a5)
    3f74:	0657ae23          	sw	t0,124(a5)
    3f78:	05f7a223          	sw	t6,68(a5)
    3f7c:	0607a623          	sw	zero,108(a5)
    3f80:	0407ac23          	sw	zero,88(a5)
    3f84:	09e7a023          	sw	t5,128(a5)
    3f88:	05d7a423          	sw	t4,72(a5)
    3f8c:	0607a823          	sw	zero,112(a5)
    3f90:	0407ae23          	sw	zero,92(a5)
    3f94:	0917a223          	sw	a7,132(a5)
    3f98:	0507a623          	sw	a6,76(a5)
    3f9c:	0607aa23          	sw	zero,116(a5)
    3fa0:	0607a023          	sw	zero,96(a5)
    3fa4:	08a7a423          	sw	a0,136(a5)
    3fa8:	04b7a823          	sw	a1,80(a5)
    3fac:	0607ac23          	sw	zero,120(a5)
    3fb0:	0607a223          	sw	zero,100(a5)
    3fb4:	08e7a623          	sw	a4,140(a5)
    3fb8:	00100713          	li	a4,1
    3fbc:	c15ff06f          	j	3bd0 <main+0x358>
    3fc0:	14872583          	lw	a1,328(a4)
    3fc4:	0065d793          	srli	a5,a1,0x6
    3fc8:	03f7f793          	andi	a5,a5,63
    3fcc:	03f5f593          	andi	a1,a1,63
    3fd0:	00459593          	slli	a1,a1,0x4
    3fd4:	00a79793          	slli	a5,a5,0xa
    3fd8:	00b7e7b3          	or	a5,a5,a1
    3fdc:	0047d793          	srli	a5,a5,0x4
    3fe0:	ffb215b7          	lui	a1,0xffb21
    3fe4:	80f5aa23          	sw	a5,-2028(a1) # ffb20814 <__stack_top+0x1e814>
    3fe8:	00f72423          	sw	a5,8(a4)
    3fec:	80f42a23          	sw	a5,-2028(s0)
    3ff0:	00f5a423          	sw	a5,8(a1)
    3ff4:	ffb305b7          	lui	a1,0xffb30
    3ff8:	1485a703          	lw	a4,328(a1) # ffb30148 <__stack_top+0x2e148>
    3ffc:	00675793          	srli	a5,a4,0x6
    4000:	03f7f793          	andi	a5,a5,63
    4004:	03f77713          	andi	a4,a4,63
    4008:	00471713          	slli	a4,a4,0x4
    400c:	00a79793          	slli	a5,a5,0xa
    4010:	00e7e7b3          	or	a5,a5,a4
    4014:	0047d793          	srli	a5,a5,0x4
    4018:	ffb31737          	lui	a4,0xffb31
    401c:	80f72a23          	sw	a5,-2028(a4) # ffb30814 <__stack_top+0x2e814>
    4020:	00f5a423          	sw	a5,8(a1)
    4024:	ffb325b7          	lui	a1,0xffb32
    4028:	80f5aa23          	sw	a5,-2028(a1) # ffb31814 <__stack_top+0x2f814>
    402c:	00f72423          	sw	a5,8(a4)
    4030:	f05ff06f          	j	3f34 <.NO_CB1455+0x2d0>
    4034:	04c4a783          	lw	a5,76(s1)
    4038:	02078863          	beqz	a5,4068 <.NO_CB1455+0x404>
    403c:	0144d503          	lhu	a0,20(s1)
    4040:	0464c583          	lbu	a1,70(s1)
    4044:	01a50533          	add	a0,a0,s10
    4048:	0ff5f593          	zext.b	a1,a1
    404c:	000e0693          	mv	a3,t3
    4050:	00b12823          	sw	a1,16(sp)
    4054:	00c12a23          	sw	a2,20(sp)
    4058:	2dc000ef          	jal	4334 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0>
    405c:	01012583          	lw	a1,16(sp)
    4060:	01412503          	lw	a0,20(sp)
    4064:	29c000ef          	jal	4300 <_Z33barrier_remote_cb_interface_setuphm>
    4068:	3a002783          	lw	a5,928(zero) # 3a0 <_start-0x34a0>
    406c:	08000713          	li	a4,128
    4070:	00279793          	slli	a5,a5,0x2
    4074:	37078793          	addi	a5,a5,880
    4078:	0037c683          	lbu	a3,3(a5)
    407c:	c2e68ee3          	beq	a3,a4,3cb8 <.NO_CB1455+0x54>
    4080:	0ff0000f          	fence
    4084:	ff5ff06f          	j	4078 <.NO_CB1455+0x414>

00004088 <_Z9WRITE_REGmm>:
    4088:	00b52023          	sw	a1,0(a0)
    408c:	00008067          	ret

00004090 <_Z18deassert_all_resetv>:
    4090:	ffb12537          	lui	a0,0xffb12
    4094:	00000593          	li	a1,0
    4098:	1b050513          	addi	a0,a0,432 # ffb121b0 <__stack_top+0x101b0>
    409c:	fedff06f          	j	4088 <_Z9WRITE_REGmm>

000040a0 <_Z9risc_initv>:
    40a0:	ffb207b7          	lui	a5,0xffb20
    40a4:	1487a783          	lw	a5,328(a5) # ffb20148 <__stack_top+0x1e148>
    40a8:	03f7f713          	andi	a4,a5,63
    40ac:	0067d793          	srli	a5,a5,0x6
    40b0:	84e18a23          	sb	a4,-1964(gp) # ffb00044 <my_x>
    40b4:	03f7f793          	andi	a5,a5,63
    40b8:	84f18823          	sb	a5,-1968(gp) # ffb00040 <my_y>
    40bc:	ffb307b7          	lui	a5,0xffb30
    40c0:	1487a783          	lw	a5,328(a5) # ffb30148 <__stack_top+0x2e148>
    40c4:	85418693          	addi	a3,gp,-1964 # ffb00044 <my_x>
    40c8:	03f7f613          	andi	a2,a5,63
    40cc:	0067d793          	srli	a5,a5,0x6
    40d0:	85018713          	addi	a4,gp,-1968 # ffb00040 <my_y>
    40d4:	03f7f793          	andi	a5,a5,63
    40d8:	00c680a3          	sb	a2,1(a3)
    40dc:	00f700a3          	sb	a5,1(a4)
    40e0:	00008067          	ret

000040e4 <_Z12ex_push_insnPVmm>:
    40e4:	00b52023          	sw	a1,0(a0)
    40e8:	00008067          	ret

000040ec <_Z13rmw_cfg_valuemmmm>:
    40ec:	00a61633          	sll	a2,a2,a0
    40f0:	00d64633          	xor	a2,a2,a3
    40f4:	00b67633          	and	a2,a2,a1
    40f8:	00d64533          	xor	a0,a2,a3
    40fc:	00008067          	ret

00004100 <_Z10ex_rmw_cfgmmmmPVm.constprop.0>:
    4100:	ff010113          	addi	sp,sp,-16
    4104:	00812423          	sw	s0,8(sp)
    4108:	00068413          	mv	s0,a3
    410c:	00c6a683          	lw	a3,12(a3)
    4110:	00112623          	sw	ra,12(sp)
    4114:	fd9ff0ef          	jal	40ec <_Z13rmw_cfg_valuemmmm>
    4118:	00a42623          	sw	a0,12(s0)
    411c:	00c12083          	lw	ra,12(sp)
    4120:	00812403          	lw	s0,8(sp)
    4124:	01010113          	addi	sp,sp,16
    4128:	00008067          	ret

0000412c <_Z10ex_zeroaccPVmmmm.constprop.0>:
    412c:	101805b7          	lui	a1,0x10180
    4130:	fb5ff06f          	j	40e4 <_Z12ex_push_insnPVmm>

00004134 <_Z7ex_enccPVm>:
    4134:	8a0035b7          	lui	a1,0x8a003
    4138:	fe010113          	addi	sp,sp,-32
    413c:	00a58593          	addi	a1,a1,10 # 8a00300a <__fw_export_text_end+0x89ffe40a>
    4140:	00112e23          	sw	ra,28(sp)
    4144:	00a12623          	sw	a0,12(sp)
    4148:	f9dff0ef          	jal	40e4 <_Z12ex_push_insnPVmm>
    414c:	00c12503          	lw	a0,12(sp)
    4150:	01c12083          	lw	ra,28(sp)
    4154:	020005b7          	lui	a1,0x2000
    4158:	02010113          	addi	sp,sp,32
    415c:	f89ff06f          	j	40e4 <_Z12ex_push_insnPVmm>

00004160 <_Z19execute_instructionPVmj>:
    4160:	f85ff06f          	j	40e4 <_Z12ex_push_insnPVmm>

00004164 <_Z11ex_sem_initmmmPVm.constprop.0>:
    4164:	00250713          	addi	a4,a0,2
    4168:	00100793          	li	a5,1
    416c:	00058513          	mv	a0,a1
    4170:	00e797b3          	sll	a5,a5,a4
    4174:	a31005b7          	lui	a1,0xa3100
    4178:	00b7e5b3          	or	a1,a5,a1
    417c:	fe5ff06f          	j	4160 <_Z19execute_instructionPVmj>

00004180 <_ZN13c_tensix_core15instrn_buf_baseEm>:
    4180:	ffe407b7          	lui	a5,0xffe40
    4184:	00078793          	mv	a5,a5
    4188:	01051513          	slli	a0,a0,0x10
    418c:	00a78533          	add	a0,a5,a0
    4190:	00008067          	ret

00004194 <_ZN13c_tensix_core11pc_buf_baseEm>:
    4194:	ff010113          	addi	sp,sp,-16
    4198:	ffe807b7          	lui	a5,0xffe80
    419c:	00f12223          	sw	a5,4(sp)
    41a0:	ffe907b7          	lui	a5,0xffe90
    41a4:	00f12423          	sw	a5,8(sp)
    41a8:	ffea07b7          	lui	a5,0xffea0
    41ac:	00f12623          	sw	a5,12(sp)
    41b0:	01010793          	addi	a5,sp,16
    41b4:	20f54533          	sh2add	a0,a0,a5
    41b8:	ff452503          	lw	a0,-12(a0)
    41bc:	01010113          	addi	sp,sp,16
    41c0:	00008067          	ret

000041c4 <_ZN13c_tensix_core13cfg_regs_baseEm.constprop.0>:
    41c4:	ffef0537          	lui	a0,0xffef0
    41c8:	00008067          	ret

000041cc <_ZN13c_tensix_core10ex_rmw_cfgEhmmmm.constprop.0>:
    41cc:	ffef06b7          	lui	a3,0xffef0
    41d0:	f31ff06f          	j	4100 <_Z10ex_rmw_cfgmmmmPVm.constprop.0>

000041d4 <_ZN13c_tensix_core11ex_sem_initEmmmPVm.constprop.0>:
    41d4:	f91ff06f          	j	4164 <_Z11ex_sem_initmmmPVm.constprop.0>

000041d8 <_ZN13c_tensix_core10ex_zeroaccEPVmmmm.constprop.0>:
    41d8:	f55ff06f          	j	412c <_Z10ex_zeroaccPVmmmm.constprop.0>

000041dc <_ZN13c_tensix_core7ex_enccEPVm>:
    41dc:	f59ff06f          	j	4134 <_Z7ex_enccPVm>

000041e0 <_ZN13c_tensix_core13ex_load_constEPVm>:
    41e0:	7100c5b7          	lui	a1,0x7100c
    41e4:	fe010113          	addi	sp,sp,-32
    41e8:	f8058593          	addi	a1,a1,-128 # 7100bf80 <__fw_export_text_end+0x71007380>
    41ec:	00112e23          	sw	ra,28(sp)
    41f0:	00a12623          	sw	a0,12(sp)
    41f4:	ef1ff0ef          	jal	40e4 <_Z12ex_push_insnPVmm>
    41f8:	00c12503          	lw	a0,12(sp)
    41fc:	01c12083          	lw	ra,28(sp)
    4200:	910005b7          	lui	a1,0x91000
    4204:	0b058593          	addi	a1,a1,176 # 910000b0 <__fw_export_text_end+0x90ffb4b0>
    4208:	02010113          	addi	sp,sp,32
    420c:	ed9ff06f          	j	40e4 <_Z12ex_push_insnPVmm>

00004210 <_ZN13c_tensix_core28initialize_tensix_semaphoresEPVm>:
    4210:	fe010113          	addi	sp,sp,-32
    4214:	00050593          	mv	a1,a0
    4218:	00a12623          	sw	a0,12(sp)
    421c:	00100513          	li	a0,1
    4220:	00112e23          	sw	ra,28(sp)
    4224:	fb1ff0ef          	jal	41d4 <_ZN13c_tensix_core11ex_sem_initEmmmPVm.constprop.0>
    4228:	00c12583          	lw	a1,12(sp)
    422c:	00200513          	li	a0,2
    4230:	fa5ff0ef          	jal	41d4 <_ZN13c_tensix_core11ex_sem_initEmmmPVm.constprop.0>
    4234:	00c12583          	lw	a1,12(sp)
    4238:	01c12083          	lw	ra,28(sp)
    423c:	00700513          	li	a0,7
    4240:	02010113          	addi	sp,sp,32
    4244:	f91ff06f          	j	41d4 <_ZN13c_tensix_core11ex_sem_initEmmmPVm.constprop.0>

00004248 <_Z22set_deassert_addressesv>:
    4248:	ff010113          	addi	sp,sp,-16
    424c:	00812423          	sw	s0,8(sp)
    4250:	ffb12437          	lui	s0,0xffb12
    4254:	23440513          	addi	a0,s0,564 # ffb12234 <__stack_top+0x10234>
    4258:	00700593          	li	a1,7
    425c:	00112623          	sw	ra,12(sp)
    4260:	e29ff0ef          	jal	4088 <_Z9WRITE_REGmm>
    4264:	23c40513          	addi	a0,s0,572
    4268:	00812403          	lw	s0,8(sp)
    426c:	00c12083          	lw	ra,12(sp)
    4270:	00100593          	li	a1,1
    4274:	01010113          	addi	sp,sp,16
    4278:	e11ff06f          	j	4088 <_Z9WRITE_REGmm>

0000427c <_Z21deassert_ncrisc_triscv>:
    427c:	8101a703          	lw	a4,-2032(gp) # ffb00000 <_ZL16subordinate_sync>
    4280:	404047b7          	lui	a5,0x40404
    4284:	04078793          	addi	a5,a5,64 # 40404040 <__fw_export_text_end+0x403ff440>
    4288:	00f72023          	sw	a5,0(a4)
    428c:	e05ff06f          	j	4090 <_Z18deassert_all_resetv>

00004290 <_Z10run_triscsm>:
    4290:	8101a783          	lw	a5,-2032(gp) # ffb00000 <_ZL16subordinate_sync>
    4294:	0017c703          	lbu	a4,1(a5)
    4298:	02071063          	bnez	a4,42b8 <_Z10run_triscsm+0x28>
    429c:	00457513          	andi	a0,a0,4
    42a0:	00050a63          	beqz	a0,42b4 <_Z10run_triscsm+0x24>
    42a4:	f8000713          	li	a4,-128
    42a8:	00e780a3          	sb	a4,1(a5)
    42ac:	00e78123          	sb	a4,2(a5)
    42b0:	00e781a3          	sb	a4,3(a5)
    42b4:	00008067          	ret
    42b8:	0ff0000f          	fence
    42bc:	fd9ff06f          	j	4294 <_Z10run_triscsm+0x4>

000042c0 <_Z29start_ncrisc_kernel_run_earlym>:
    42c0:	00257513          	andi	a0,a0,2
    42c4:	00050863          	beqz	a0,42d4 <_Z29start_ncrisc_kernel_run_earlym+0x14>
    42c8:	8101a783          	lw	a5,-2032(gp) # ffb00000 <_ZL16subordinate_sync>
    42cc:	f8000713          	li	a4,-128
    42d0:	00e78023          	sb	a4,0(a5)
    42d4:	00008067          	ret

000042d8 <_Z17wait_ncrisc_triscv>:
    42d8:	8101a703          	lw	a4,-2032(gp) # ffb00000 <_ZL16subordinate_sync>
    42dc:	00072783          	lw	a5,0(a4)
    42e0:	00079463          	bnez	a5,42e8 <_Z17wait_ncrisc_triscv+0x10>
    42e4:	00008067          	ret
    42e8:	0ff0000f          	fence
    42ec:	ff1ff06f          	j	42dc <_Z17wait_ncrisc_triscv+0x4>

000042f0 <_Z26trigger_sync_register_initv>:
    42f0:	8101a783          	lw	a5,-2032(gp) # ffb00000 <_ZL16subordinate_sync>
    42f4:	00300713          	li	a4,3
    42f8:	00e780a3          	sb	a4,1(a5)
    42fc:	00008067          	ret

00004300 <_Z33barrier_remote_cb_interface_setuphm>:
    4300:	02000793          	li	a5,32
    4304:	02f58663          	beq	a1,a5,4330 <_Z33barrier_remote_cb_interface_setuphm+0x30>
    4308:	ffb20737          	lui	a4,0xffb20
    430c:	01051793          	slli	a5,a0,0x10
    4310:	20070713          	addi	a4,a4,512 # ffb20200 <__stack_top+0x1e200>
    4314:	00e787b3          	add	a5,a5,a4
    4318:	84418713          	addi	a4,gp,-1980 # ffb00034 <noc_nonposted_atomics_acked>
    431c:	20e54533          	sh2add	a0,a0,a4
    4320:	00052703          	lw	a4,0(a0) # ffef0000 <__instrn_buffer+0xb0000>
    4324:	0007a683          	lw	a3,0(a5)
    4328:	fee69ee3          	bne	a3,a4,4324 <_Z33barrier_remote_cb_interface_setuphm+0x24>
    432c:	0ff0000f          	fence
    4330:	00008067          	ret

00004334 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0>:
    4334:	fa010113          	addi	sp,sp,-96
    4338:	fff58793          	addi	a5,a1,-1
    433c:	00f12823          	sw	a5,16(sp)
    4340:	100007b7          	lui	a5,0x10000
    4344:	00f78793          	addi	a5,a5,15 # 1000000f <__fw_export_text_end+0xfffb40f>
    4348:	00f12423          	sw	a5,8(sp)
    434c:	010007b7          	lui	a5,0x1000
    4350:	ffb20337          	lui	t1,0xffb20
    4354:	fff78793          	addi	a5,a5,-1 # ffffff <__fw_export_text_end+0xffb3ff>
    4358:	03b12823          	sw	s11,48(sp)
    435c:	00b71813          	slli	a6,a4,0xb
    4360:	01061d93          	slli	s11,a2,0x10
    4364:	01b80833          	add	a6,a6,s11
    4368:	00f12623          	sw	a5,12(sp)
    436c:	00430793          	addi	a5,t1,4 # ffb20004 <__stack_top+0x1e004>
    4370:	04030293          	addi	t0,t1,64
    4374:	00f807b3          	add	a5,a6,a5
    4378:	04812e23          	sw	s0,92(sp)
    437c:	05612223          	sw	s6,68(sp)
    4380:	84418393          	addi	t2,gp,-1980 # ffb00034 <noc_nonposted_atomics_acked>
    4384:	04912c23          	sw	s1,88(sp)
    4388:	207643b3          	sh2add	t2,a2,t2
    438c:	05212a23          	sw	s2,84(sp)
    4390:	05312823          	sw	s3,80(sp)
    4394:	05412623          	sw	s4,76(sp)
    4398:	05512423          	sw	s5,72(sp)
    439c:	05712023          	sw	s7,64(sp)
    43a0:	03812e23          	sw	s8,60(sp)
    43a4:	03912c23          	sw	s9,56(sp)
    43a8:	03a12a23          	sw	s10,52(sp)
    43ac:	00050413          	mv	s0,a0
    43b0:	85818593          	addi	a1,gp,-1960 # ffb00048 <cb_interface>
    43b4:	01f00b13          	li	s6,31
    43b8:	005802b3          	add	t0,a6,t0
    43bc:	02f12623          	sw	a5,44(sp)
    43c0:	01012783          	lw	a5,16(sp)
    43c4:	03679e63          	bne	a5,s6,4400 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0xcc>
    43c8:	05c12403          	lw	s0,92(sp)
    43cc:	05812483          	lw	s1,88(sp)
    43d0:	05412903          	lw	s2,84(sp)
    43d4:	05012983          	lw	s3,80(sp)
    43d8:	04c12a03          	lw	s4,76(sp)
    43dc:	04812a83          	lw	s5,72(sp)
    43e0:	04412b03          	lw	s6,68(sp)
    43e4:	04012b83          	lw	s7,64(sp)
    43e8:	03c12c03          	lw	s8,60(sp)
    43ec:	03812c83          	lw	s9,56(sp)
    43f0:	03412d03          	lw	s10,52(sp)
    43f4:	03012d83          	lw	s11,48(sp)
    43f8:	06010113          	addi	sp,sp,96
    43fc:	00008067          	ret
    4400:	00042f03          	lw	t5,0(s0)
    4404:	00442503          	lw	a0,4(s0)
    4408:	000f2f83          	lw	t6,0(t5)
    440c:	004f2b83          	lw	s7,4(t5)
    4410:	008f2e03          	lw	t3,8(t5)
    4414:	00cf2783          	lw	a5,12(t5)
    4418:	010f2783          	lw	a5,16(t5)
    441c:	014f2903          	lw	s2,20(t5)
    4420:	018f2883          	lw	a7,24(t5)
    4424:	fff50e93          	addi	t4,a0,-1
    4428:	00fe8eb3          	add	t4,t4,a5
    442c:	41ce8eb3          	sub	t4,t4,t3
    4430:	02aedeb3          	divu	t4,t4,a0
    4434:	02ae8eb3          	mul	t4,t4,a0
    4438:	01ce8eb3          	add	t4,t4,t3
    443c:	280f8663          	beqz	t6,46c8 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x394>
    4440:	3fe5a023          	sw	t5,992(a1)
    4444:	3fc5a223          	sw	t3,996(a1)
    4448:	3ef5a823          	sw	a5,1008(a1)
    444c:	3f25aa23          	sw	s2,1012(a1)
    4450:	3f15ac23          	sw	a7,1016(a1)
    4454:	3f75ae23          	sw	s7,1020(a1)
    4458:	00cf2f03          	lw	t5,12(t5)
    445c:	01ee09b3          	add	s3,t3,t5
    4460:	02af7fb3          	remu	t6,t5,a0
    4464:	41f989b3          	sub	s3,s3,t6
    4468:	0f3ee063          	bltu	t4,s3,4548 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x214>
    446c:	40ff0f33          	sub	t5,t5,a5
    4470:	01cf0f33          	add	t5,t5,t3
    4474:	004f5793          	srli	a5,t5,0x4
    4478:	16078463          	beqz	a5,45e0 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x2ac>
    447c:	00100e93          	li	t4,1
    4480:	00000f13          	li	t5,0
    4484:	0dd68c63          	beq	a3,t4,455c <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x228>
    4488:	00830f93          	addi	t6,t1,8
    448c:	01c30493          	addi	s1,t1,28
    4490:	00680ab3          	add	s5,a6,t1
    4494:	01f80fb3          	add	t6,a6,t6
    4498:	009804b3          	add	s1,a6,s1
    449c:	15eb8263          	beq	s7,t5,45e0 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x2ac>
    44a0:	212f6a33          	sh3add	s4,t5,s2
    44a4:	004a2e83          	lw	t4,4(s4)
    44a8:	000a2c03          	lw	s8,0(s4)
    44ac:	0008aa03          	lw	s4,0(a7)
    44b0:	006e9e93          	slli	t4,t4,0x6
    44b4:	018eeeb3          	or	t4,t4,s8
    44b8:	01478a33          	add	s4,a5,s4
    44bc:	0148a023          	sw	s4,0(a7)
    44c0:	004e9e93          	slli	t4,t4,0x4
    44c4:	0002aa03          	lw	s4,0(t0)
    44c8:	fe0a1ee3          	bnez	s4,44c4 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x190>
    44cc:	00812a03          	lw	s4,8(sp)
    44d0:	02c12c03          	lw	s8,44(sp)
    44d4:	011aa023          	sw	a7,0(s5)
    44d8:	014efa33          	and	s4,t4,s4
    44dc:	014c2023          	sw	s4,0(s8)
    44e0:	00c12a03          	lw	s4,12(sp)
    44e4:	004ede93          	srli	t4,t4,0x4
    44e8:	014efeb3          	and	t4,t4,s4
    44ec:	01dfa023          	sw	t4,0(t6)
    44f0:	00002eb7          	lui	t4,0x2
    44f4:	091e8e93          	addi	t4,t4,145 # 2091 <_start-0x17af>
    44f8:	01d4a023          	sw	t4,0(s1)
    44fc:	00001a37          	lui	s4,0x1
    4500:	0028de93          	srli	t4,a7,0x2
    4504:	07ca0a13          	addi	s4,s4,124 # 107c <_start-0x27c4>
    4508:	003efe93          	andi	t4,t4,3
    450c:	014eeeb3          	or	t4,t4,s4
    4510:	02030a13          	addi	s4,t1,32
    4514:	01480a33          	add	s4,a6,s4
    4518:	01da2023          	sw	t4,0(s4)
    451c:	02830e93          	addi	t4,t1,40
    4520:	01d80eb3          	add	t4,a6,t4
    4524:	00fea023          	sw	a5,0(t4)
    4528:	00100e93          	li	t4,1
    452c:	01d2a023          	sw	t4,0(t0)
    4530:	0003ae83          	lw	t4,0(t2)
    4534:	02088893          	addi	a7,a7,32
    4538:	001e8e93          	addi	t4,t4,1
    453c:	01d3a023          	sw	t4,0(t2)
    4540:	001f0f13          	addi	t5,t5,1
    4544:	f59ff06f          	j	449c <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x168>
    4548:	09d78e63          	beq	a5,t4,45e4 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x2b0>
    454c:	40fe87b3          	sub	a5,t4,a5
    4550:	0047d793          	srli	a5,a5,0x4
    4554:	000e8e13          	mv	t3,t4
    4558:	f21ff06f          	j	4478 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x144>
    455c:	02800493          	li	s1,40
    4560:	00007eb7          	lui	t4,0x7
    4564:	029604b3          	mul	s1,a2,s1
    4568:	ffb20fb7          	lui	t6,0xffb20
    456c:	04ce8e93          	addi	t4,t4,76 # 704c <__fw_export_text_end+0x244c>
    4570:	044f8c13          	addi	s8,t6,68 # ffb20044 <__stack_top+0x1e044>
    4574:	01d484b3          	add	s1,s1,t4
    4578:	00b71f13          	slli	t5,a4,0xb
    457c:	01061e93          	slli	t4,a2,0x10
    4580:	01df0f33          	add	t5,t5,t4
    4584:	018e8eb3          	add	t4,t4,s8
    4588:	01d12a23          	sw	t4,20(sp)
    458c:	00cf8e93          	addi	t4,t6,12
    4590:	01df0eb3          	add	t4,t5,t4
    4594:	01d12c23          	sw	t4,24(sp)
    4598:	10000eb7          	lui	t4,0x10000
    459c:	00fe8e93          	addi	t4,t4,15 # 1000000f <__fw_export_text_end+0xfffb40f>
    45a0:	01d12e23          	sw	t4,28(sp)
    45a4:	004f8e93          	addi	t4,t6,4
    45a8:	01df0eb3          	add	t4,t5,t4
    45ac:	03d12023          	sw	t4,32(sp)
    45b0:	01000eb7          	lui	t4,0x1000
    45b4:	fffe8e93          	addi	t4,t4,-1 # ffffff <__fw_export_text_end+0xffb3ff>
    45b8:	008f8c13          	addi	s8,t6,8
    45bc:	040f8a93          	addi	s5,t6,64
    45c0:	03d12223          	sw	t4,36(sp)
    45c4:	01cf8c93          	addi	s9,t6,28
    45c8:	018f0eb3          	add	t4,t5,s8
    45cc:	00000a13          	li	s4,0
    45d0:	015f0ab3          	add	s5,t5,s5
    45d4:	03d12423          	sw	t4,40(sp)
    45d8:	019f0cb3          	add	s9,t5,s9
    45dc:	034b9263          	bne	s7,s4,4600 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x2cc>
    45e0:	000e0e93          	mv	t4,t3
    45e4:	3fd5a823          	sw	t4,1008(a1)
    45e8:	3f35a423          	sw	s3,1000(a1)
    45ec:	3ea5a623          	sw	a0,1004(a1)
    45f0:	00840413          	addi	s0,s0,8
    45f4:	fffb0b13          	addi	s6,s6,-1
    45f8:	fe058593          	addi	a1,a1,-32
    45fc:	dc5ff06f          	j	43c0 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x8c>
    4600:	212a6d33          	sh3add	s10,s4,s2
    4604:	004d2e83          	lw	t4,4(s10)
    4608:	000d2d03          	lw	s10,0(s10)
    460c:	006e9e93          	slli	t4,t4,0x6
    4610:	000d0c13          	mv	s8,s10
    4614:	0008ad03          	lw	s10,0(a7)
    4618:	018eeeb3          	or	t4,t4,s8
    461c:	004e9e93          	slli	t4,t4,0x4
    4620:	01a78d33          	add	s10,a5,s10
    4624:	01a8a023          	sw	s10,0(a7)
    4628:	0004ad03          	lw	s10,0(s1)
    462c:	001d0d13          	addi	s10,s10,1
    4630:	01a4a023          	sw	s10,0(s1)
    4634:	000aad03          	lw	s10,0(s5)
    4638:	fe0d1ee3          	bnez	s10,4634 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x300>
    463c:	01412d03          	lw	s10,20(sp)
    4640:	00400c13          	li	s8,4
    4644:	000d2d03          	lw	s10,0(s10)
    4648:	01812d03          	lw	s10,24(sp)
    464c:	018d2023          	sw	s8,0(s10)
    4650:	01c12c03          	lw	s8,28(sp)
    4654:	01ff0d33          	add	s10,t5,t6
    4658:	011d2023          	sw	a7,0(s10)
    465c:	018efd33          	and	s10,t4,s8
    4660:	02012c03          	lw	s8,32(sp)
    4664:	004ede93          	srli	t4,t4,0x4
    4668:	01ac2023          	sw	s10,0(s8)
    466c:	02412c03          	lw	s8,36(sp)
    4670:	00001d37          	lui	s10,0x1
    4674:	018efeb3          	and	t4,t4,s8
    4678:	02812c03          	lw	s8,40(sp)
    467c:	07cd0d13          	addi	s10,s10,124 # 107c <_start-0x27c4>
    4680:	01dc2023          	sw	t4,0(s8)
    4684:	00002eb7          	lui	t4,0x2
    4688:	091e8e93          	addi	t4,t4,145 # 2091 <_start-0x17af>
    468c:	01dca023          	sw	t4,0(s9)
    4690:	0028de93          	srli	t4,a7,0x2
    4694:	003efe93          	andi	t4,t4,3
    4698:	01aeeeb3          	or	t4,t4,s10
    469c:	020f8d13          	addi	s10,t6,32
    46a0:	01af0d33          	add	s10,t5,s10
    46a4:	01dd2023          	sw	t4,0(s10)
    46a8:	028f8e93          	addi	t4,t6,40
    46ac:	01df0eb3          	add	t4,t5,t4
    46b0:	00fea023          	sw	a5,0(t4)
    46b4:	00100e93          	li	t4,1
    46b8:	01daa023          	sw	t4,0(s5)
    46bc:	02088893          	addi	a7,a7,32
    46c0:	01da0a33          	add	s4,s4,t4
    46c4:	f19ff06f          	j	45dc <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x2a8>
    46c8:	00092983          	lw	s3,0(s2)
    46cc:	00492f83          	lw	t6,4(s2)
    46d0:	01088493          	addi	s1,a7,16
    46d4:	3fe5a023          	sw	t5,992(a1)
    46d8:	3fc5a223          	sw	t3,996(a1)
    46dc:	3ef5a823          	sw	a5,1008(a1)
    46e0:	3e95ae23          	sw	s1,1020(a1)
    46e4:	3f35aa23          	sw	s3,1012(a1)
    46e8:	3ff5ac23          	sw	t6,1016(a1)
    46ec:	00cf2f03          	lw	t5,12(t5)
    46f0:	01ee0fb3          	add	t6,t3,t5
    46f4:	02af7933          	remu	s2,t5,a0
    46f8:	412f8fb3          	sub	t6,t6,s2
    46fc:	13fee263          	bltu	t4,t6,4820 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x4ec>
    4700:	40ff0f33          	sub	t5,t5,a5
    4704:	01cf0f33          	add	t5,t5,t3
    4708:	004f5793          	srli	a5,t5,0x4
    470c:	10078263          	beqz	a5,4810 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x4dc>
    4710:	0ff0000f          	fence
    4714:	0004af03          	lw	t5,0(s1)
    4718:	0008ae83          	lw	t4,0(a7)
    471c:	41ee8eb3          	sub	t4,t4,t5
    4720:	fefee8e3          	bltu	t4,a5,4710 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x3dc>
    4724:	3f85ae83          	lw	t4,1016(a1)
    4728:	3f45af03          	lw	t5,1012(a1)
    472c:	00ae9e93          	slli	t4,t4,0xa
    4730:	004f1f13          	slli	t5,t5,0x4
    4734:	01eeeeb3          	or	t4,t4,t5
    4738:	00100f13          	li	t5,1
    473c:	3fc5a883          	lw	a7,1020(a1)
    4740:	0fe69a63          	bne	a3,t5,4834 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x500>
    4744:	0008af03          	lw	t5,0(a7)
    4748:	000074b7          	lui	s1,0x7
    474c:	01e78f33          	add	t5,a5,t5
    4750:	01e8a023          	sw	t5,0(a7)
    4754:	02800f13          	li	t5,40
    4758:	04c48493          	addi	s1,s1,76 # 704c <__fw_export_text_end+0x244c>
    475c:	03e60f33          	mul	t5,a2,t5
    4760:	009f0f33          	add	t5,t5,s1
    4764:	000f2483          	lw	s1,0(t5)
    4768:	00d484b3          	add	s1,s1,a3
    476c:	009f2023          	sw	s1,0(t5)
    4770:	0002af03          	lw	t5,0(t0)
    4774:	fe0f1ee3          	bnez	t5,4770 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x43c>
    4778:	ffb20f37          	lui	t5,0xffb20
    477c:	044f0493          	addi	s1,t5,68 # ffb20044 <__stack_top+0x1e044>
    4780:	009d84b3          	add	s1,s11,s1
    4784:	0004a483          	lw	s1,0(s1)
    4788:	00cf0493          	addi	s1,t5,12
    478c:	009804b3          	add	s1,a6,s1
    4790:	00400913          	li	s2,4
    4794:	0124a023          	sw	s2,0(s1)
    4798:	01e804b3          	add	s1,a6,t5
    479c:	0114a023          	sw	a7,0(s1)
    47a0:	10000937          	lui	s2,0x10000
    47a4:	004f0493          	addi	s1,t5,4
    47a8:	012ef933          	and	s2,t4,s2
    47ac:	009804b3          	add	s1,a6,s1
    47b0:	0124a023          	sw	s2,0(s1)
    47b4:	004e9e93          	slli	t4,t4,0x4
    47b8:	008f0493          	addi	s1,t5,8
    47bc:	008ede93          	srli	t4,t4,0x8
    47c0:	009804b3          	add	s1,a6,s1
    47c4:	01d4a023          	sw	t4,0(s1)
    47c8:	01cf0e93          	addi	t4,t5,28
    47cc:	000024b7          	lui	s1,0x2
    47d0:	01d80eb3          	add	t4,a6,t4
    47d4:	09148493          	addi	s1,s1,145 # 2091 <_start-0x17af>
    47d8:	009ea023          	sw	s1,0(t4)
    47dc:	0028d893          	srli	a7,a7,0x2
    47e0:	00001eb7          	lui	t4,0x1
    47e4:	07ce8e93          	addi	t4,t4,124 # 107c <_start-0x27c4>
    47e8:	0038f893          	andi	a7,a7,3
    47ec:	01d8e8b3          	or	a7,a7,t4
    47f0:	020f0e93          	addi	t4,t5,32
    47f4:	01d80eb3          	add	t4,a6,t4
    47f8:	028f0f13          	addi	t5,t5,40
    47fc:	011ea023          	sw	a7,0(t4)
    4800:	01e80f33          	add	t5,a6,t5
    4804:	00ff2023          	sw	a5,0(t5)
    4808:	00100793          	li	a5,1
    480c:	00f2a023          	sw	a5,0(t0)
    4810:	000e0e93          	mv	t4,t3
    4814:	3fd5a823          	sw	t4,1008(a1)
    4818:	3ff5a423          	sw	t6,1000(a1)
    481c:	dd1ff06f          	j	45ec <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x2b8>
    4820:	ffd78ae3          	beq	a5,t4,4814 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x4e0>
    4824:	40fe87b3          	sub	a5,t4,a5
    4828:	0047d793          	srli	a5,a5,0x4
    482c:	000e8e13          	mv	t3,t4
    4830:	eddff06f          	j	470c <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x3d8>
    4834:	0008af03          	lw	t5,0(a7)
    4838:	01e78f33          	add	t5,a5,t5
    483c:	01e8a023          	sw	t5,0(a7)
    4840:	0002af03          	lw	t5,0(t0)
    4844:	fe0f1ee3          	bnez	t5,4840 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x50c>
    4848:	00680f33          	add	t5,a6,t1
    484c:	011f2023          	sw	a7,0(t5)
    4850:	00812f03          	lw	t5,8(sp)
    4854:	0028d893          	srli	a7,a7,0x2
    4858:	01eef4b3          	and	s1,t4,t5
    485c:	00430f13          	addi	t5,t1,4
    4860:	01e80f33          	add	t5,a6,t5
    4864:	009f2023          	sw	s1,0(t5)
    4868:	00c12f03          	lw	t5,12(sp)
    486c:	004ede93          	srli	t4,t4,0x4
    4870:	01eefeb3          	and	t4,t4,t5
    4874:	00830f13          	addi	t5,t1,8
    4878:	01e80f33          	add	t5,a6,t5
    487c:	01df2023          	sw	t4,0(t5)
    4880:	01c30e93          	addi	t4,t1,28
    4884:	00002f37          	lui	t5,0x2
    4888:	01d80eb3          	add	t4,a6,t4
    488c:	091f0f13          	addi	t5,t5,145 # 2091 <_start-0x17af>
    4890:	01eea023          	sw	t5,0(t4)
    4894:	00001eb7          	lui	t4,0x1
    4898:	07ce8e93          	addi	t4,t4,124 # 107c <_start-0x27c4>
    489c:	0038f893          	andi	a7,a7,3
    48a0:	01d8e8b3          	or	a7,a7,t4
    48a4:	02030e93          	addi	t4,t1,32
    48a8:	01d80eb3          	add	t4,a6,t4
    48ac:	011ea023          	sw	a7,0(t4)
    48b0:	02830893          	addi	a7,t1,40
    48b4:	011808b3          	add	a7,a6,a7
    48b8:	00f8a023          	sw	a5,0(a7)
    48bc:	00100793          	li	a5,1
    48c0:	00f2a023          	sw	a5,0(t0)
    48c4:	0003a783          	lw	a5,0(t2)
    48c8:	00178793          	addi	a5,a5,1
    48cc:	00f3a023          	sw	a5,0(t2)
    48d0:	f41ff06f          	j	4810 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x4dc>

000048d4 <_Z15noc_set_cfg_regmm>:
    48d4:	84c1a783          	lw	a5,-1972(gp) # ffb0003c <_ZL19active_noc_instance>
    48d8:	ffec8737          	lui	a4,0xffec8
    48dc:	00e79793          	slli	a5,a5,0xe
    48e0:	04070713          	addi	a4,a4,64 # ffec8040 <__instrn_buffer+0x88040>
    48e4:	00e787b3          	add	a5,a5,a4
    48e8:	00a787b3          	add	a5,a5,a0
    48ec:	00279793          	slli	a5,a5,0x2
    48f0:	00b7a023          	sw	a1,0(a5)
    48f4:	00008067          	ret

000048f8 <_Z15noc_get_cfg_regm>:
    48f8:	84c1a783          	lw	a5,-1972(gp) # ffb0003c <_ZL19active_noc_instance>
    48fc:	ffec8737          	lui	a4,0xffec8
    4900:	04070713          	addi	a4,a4,64 # ffec8040 <__instrn_buffer+0x88040>
    4904:	00e79793          	slli	a5,a5,0xe
    4908:	00e787b3          	add	a5,a5,a4
    490c:	00a787b3          	add	a5,a5,a0
    4910:	00279793          	slli	a5,a5,0x2
    4914:	0007a503          	lw	a0,0(a5)
    4918:	00008067          	ret

0000491c <wzerorange>:
    491c:	01050513          	addi	a0,a0,16
    4920:	02a5f463          	bgeu	a1,a0,4948 <wzerorange+0x2c>
    4924:	ff850793          	addi	a5,a0,-8
    4928:	00f5e863          	bltu	a1,a5,4938 <wzerorange+0x1c>
    492c:	fe052a23          	sw	zero,-12(a0)
    4930:	fe052823          	sw	zero,-16(a0)
    4934:	00050793          	mv	a5,a0
    4938:	ffc78713          	addi	a4,a5,-4
    493c:	00e5e463          	bltu	a1,a4,4944 <wzerorange+0x28>
    4940:	fe07ac23          	sw	zero,-8(a5)
    4944:	00008067          	ret
    4948:	fe052e23          	sw	zero,-4(a0)
    494c:	fe052c23          	sw	zero,-8(a0)
    4950:	fe052a23          	sw	zero,-12(a0)
    4954:	fe052823          	sw	zero,-16(a0)
    4958:	01050513          	addi	a0,a0,16
    495c:	fc5ff06f          	j	4920 <wzerorange+0x4>

00004960 <_Z8wzeromemjm.constprop.0>:
    4960:	00003537          	lui	a0,0x3
    4964:	44050593          	addi	a1,a0,1088 # 3440 <_start-0x400>
    4968:	24050513          	addi	a0,a0,576
    496c:	fb1ff06f          	j	491c <wzerorange>

00004970 <_Z12device_setupv>:
    4970:	ff010113          	addi	sp,sp,-16
    4974:	00812423          	sw	s0,8(sp)
    4978:	00000513          	li	a0,0
    497c:	00112623          	sw	ra,12(sp)
    4980:	00912223          	sw	s1,4(sp)
    4984:	01212023          	sw	s2,0(sp)
    4988:	ff8ff0ef          	jal	4180 <_ZN13c_tensix_core15instrn_buf_baseEm>
    498c:	85818413          	addi	s0,gp,-1960 # ffb00048 <cb_interface>
    4990:	00050913          	mv	s2,a0
    4994:	40a42023          	sw	a0,1024(s0)
    4998:	00100513          	li	a0,1
    499c:	fe4ff0ef          	jal	4180 <_ZN13c_tensix_core15instrn_buf_baseEm>
    49a0:	40a42223          	sw	a0,1028(s0)
    49a4:	00200513          	li	a0,2
    49a8:	fd8ff0ef          	jal	4180 <_ZN13c_tensix_core15instrn_buf_baseEm>
    49ac:	40a42423          	sw	a0,1032(s0)
    49b0:	ffb127b7          	lui	a5,0xffb12
    49b4:	ffb11537          	lui	a0,0xffb11
    49b8:	2407a023          	sw	zero,576(a5) # ffb12240 <__stack_top+0x10240>
    49bc:	03f00593          	li	a1,63
    49c0:	02450513          	addi	a0,a0,36 # ffb11024 <__stack_top+0xf024>
    49c4:	ec4ff0ef          	jal	4088 <_Z9WRITE_REGmm>
    49c8:	00000513          	li	a0,0
    49cc:	8401a623          	sw	zero,-1972(gp) # ffb0003c <_ZL19active_noc_instance>
    49d0:	f29ff0ef          	jal	48f8 <_Z15noc_get_cfg_regm>
    49d4:	00156593          	ori	a1,a0,1
    49d8:	00000513          	li	a0,0
    49dc:	ef9ff0ef          	jal	48d4 <_Z15noc_set_cfg_regmm>
    49e0:	00100413          	li	s0,1
    49e4:	00100513          	li	a0,1
    49e8:	f11ff0ef          	jal	48f8 <_Z15noc_get_cfg_regm>
    49ec:	00156593          	ori	a1,a0,1
    49f0:	00100513          	li	a0,1
    49f4:	ee1ff0ef          	jal	48d4 <_Z15noc_set_cfg_regmm>
    49f8:	8481a623          	sw	s0,-1972(gp) # ffb0003c <_ZL19active_noc_instance>
    49fc:	00000513          	li	a0,0
    4a00:	ef9ff0ef          	jal	48f8 <_Z15noc_get_cfg_regm>
    4a04:	008565b3          	or	a1,a0,s0
    4a08:	00000513          	li	a0,0
    4a0c:	ec9ff0ef          	jal	48d4 <_Z15noc_set_cfg_regmm>
    4a10:	00040513          	mv	a0,s0
    4a14:	ee5ff0ef          	jal	48f8 <_Z15noc_get_cfg_regm>
    4a18:	008565b3          	or	a1,a0,s0
    4a1c:	00040513          	mv	a0,s0
    4a20:	eb5ff0ef          	jal	48d4 <_Z15noc_set_cfg_regmm>
    4a24:	8401a623          	sw	zero,-1972(gp) # ffb0003c <_ZL19active_noc_instance>
    4a28:	821ff0ef          	jal	4248 <_Z22set_deassert_addressesv>
    4a2c:	f35ff0ef          	jal	4960 <_Z8wzeromemjm.constprop.0>
    4a30:	ffef07b7          	lui	a5,0xffef0
    4a34:	01f00713          	li	a4,31
    4a38:	2ee7a223          	sw	a4,740(a5) # ffef02e4 <__instrn_buffer+0xb02e4>
    4a3c:	00090513          	mv	a0,s2
    4a40:	f98ff0ef          	jal	41d8 <_ZN13c_tensix_core10ex_zeroaccEPVmmmm.constprop.0>
    4a44:	00090513          	mv	a0,s2
    4a48:	f94ff0ef          	jal	41dc <_ZN13c_tensix_core7ex_enccEPVm>
    4a4c:	00090513          	mv	a0,s2
    4a50:	f90ff0ef          	jal	41e0 <_ZN13c_tensix_core13ex_load_constEPVm>
    4a54:	00040613          	mv	a2,s0
    4a58:	00040593          	mv	a1,s0
    4a5c:	00000513          	li	a0,0
    4a60:	f6cff0ef          	jal	41cc <_ZN13c_tensix_core10ex_rmw_cfgEhmmmm.constprop.0>
    4a64:	00040613          	mv	a2,s0
    4a68:	00040513          	mv	a0,s0
    4a6c:	00200593          	li	a1,2
    4a70:	f5cff0ef          	jal	41cc <_ZN13c_tensix_core10ex_rmw_cfgEhmmmm.constprop.0>
    4a74:	000045b7          	lui	a1,0x4
    4a78:	00300513          	li	a0,3
    4a7c:	10000613          	li	a2,256
    4a80:	ff858593          	addi	a1,a1,-8 # 3ff8 <.NO_CB1455+0x394>
    4a84:	f48ff0ef          	jal	41cc <_ZN13c_tensix_core10ex_rmw_cfgEhmmmm.constprop.0>
    4a88:	00812403          	lw	s0,8(sp)
    4a8c:	00c12083          	lw	ra,12(sp)
    4a90:	00412483          	lw	s1,4(sp)
    4a94:	00090513          	mv	a0,s2
    4a98:	00012903          	lw	s2,0(sp)
    4a9c:	01010113          	addi	sp,sp,16
    4aa0:	f70ff06f          	j	4210 <_ZN13c_tensix_core28initialize_tensix_semaphoresEPVm>

00004aa4 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>:
    4aa4:	00200793          	li	a5,2
    4aa8:	02c7c063          	blt	a5,a2,4ac8 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x24>
    4aac:	00c05c63          	blez	a2,4ac4 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x20>
    4ab0:	0005a703          	lw	a4,0(a1)
    4ab4:	00e52023          	sw	a4,0(a0)
    4ab8:	00f61663          	bne	a2,a5,4ac4 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x20>
    4abc:	0045a783          	lw	a5,4(a1)
    4ac0:	00f52223          	sw	a5,4(a0)
    4ac4:	00008067          	ret
    4ac8:	0005a803          	lw	a6,0(a1)
    4acc:	0045a683          	lw	a3,4(a1)
    4ad0:	0085a703          	lw	a4,8(a1)
    4ad4:	00c58593          	addi	a1,a1,12
    4ad8:	00c50513          	addi	a0,a0,12
    4adc:	ffd60613          	addi	a2,a2,-3
    4ae0:	ff052a23          	sw	a6,-12(a0)
    4ae4:	fed52c23          	sw	a3,-8(a0)
    4ae8:	fee52e23          	sw	a4,-4(a0)
    4aec:	fbdff06f          	j	4aa8 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x4>

00004af0 <_Z7do_crt1U11rvtt_l1_ptrPm.constprop.0>:
    4af0:	ffb015b7          	lui	a1,0xffb01
    4af4:	ff010113          	addi	sp,sp,-16
    4af8:	87858593          	addi	a1,a1,-1928 # ffb00878 <__ldm_bss_end>
    4afc:	81418513          	addi	a0,gp,-2028 # ffb00004 <prev_noc_mode>
    4b00:	00112623          	sw	ra,12(sp)
    4b04:	e19ff0ef          	jal	491c <wzerorange>
    4b08:	000085b7          	lui	a1,0x8
    4b0c:	81018513          	addi	a0,gp,-2032 # ffb00000 <_ZL16subordinate_sync>
    4b10:	6b058593          	addi	a1,a1,1712 # 86b0 <__fw_export_text_end+0x3ab0>
    4b14:	02b50063          	beq	a0,a1,4b34 <_Z7do_crt1U11rvtt_l1_ptrPm.constprop.0+0x44>
    4b18:	ffb00637          	lui	a2,0xffb00
    4b1c:	00460613          	addi	a2,a2,4 # ffb00004 <prev_noc_mode>
    4b20:	00c12083          	lw	ra,12(sp)
    4b24:	40a60633          	sub	a2,a2,a0
    4b28:	40265613          	srai	a2,a2,0x2
    4b2c:	01010113          	addi	sp,sp,16
    4b30:	f75ff06f          	j	4aa4 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    4b34:	00c12083          	lw	ra,12(sp)
    4b38:	01010113          	addi	sp,sp,16
    4b3c:	00008067          	ret

00004b40 <_Z19noc_bank_table_inity.constprop.0>:
    4b40:	ff010113          	addi	sp,sp,-16
    4b44:	00812423          	sw	s0,8(sp)
    4b48:	00912223          	sw	s1,4(sp)
    4b4c:	85818413          	addi	s0,gp,-1960 # ffb00048 <cb_interface>
    4b50:	000114b7          	lui	s1,0x11
    4b54:	6b048593          	addi	a1,s1,1712 # 116b0 <__fw_export_text_end+0xcab0>
    4b58:	40c40513          	addi	a0,s0,1036
    4b5c:	00700613          	li	a2,7
    4b60:	00112623          	sw	ra,12(sp)
    4b64:	f41ff0ef          	jal	4aa4 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    4b68:	6cc48593          	addi	a1,s1,1740
    4b6c:	42840513          	addi	a0,s0,1064
    4b70:	07800613          	li	a2,120
    4b74:	f31ff0ef          	jal	4aa4 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    4b78:	000124b7          	lui	s1,0x12
    4b7c:	8ac48593          	addi	a1,s1,-1876 # 118ac <__fw_export_text_end+0xccac>
    4b80:	60840513          	addi	a0,s0,1544
    4b84:	00700613          	li	a2,7
    4b88:	f1dff0ef          	jal	4aa4 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    4b8c:	62440513          	addi	a0,s0,1572
    4b90:	00812403          	lw	s0,8(sp)
    4b94:	00c12083          	lw	ra,12(sp)
    4b98:	8c848593          	addi	a1,s1,-1848
    4b9c:	00412483          	lw	s1,4(sp)
    4ba0:	07800613          	li	a2,120
    4ba4:	01010113          	addi	sp,sp,16
    4ba8:	efdff06f          	j	4aa4 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>

00004bac <_Z38noc_worker_logical_to_virtual_map_inity.constprop.0>:
    4bac:	ff010113          	addi	sp,sp,-16
    4bb0:	00812423          	sw	s0,8(sp)
    4bb4:	ffb01437          	lui	s0,0xffb01
    4bb8:	00912223          	sw	s1,4(sp)
    4bbc:	04840413          	addi	s0,s0,72 # ffb01048 <__fw_export_ldm_end+0x7c8>
    4bc0:	000124b7          	lui	s1,0x12
    4bc4:	eb048593          	addi	a1,s1,-336 # 11eb0 <__fw_export_text_end+0xd2b0>
    4bc8:	80440513          	addi	a0,s0,-2044
    4bcc:	00500613          	li	a2,5
    4bd0:	00112623          	sw	ra,12(sp)
    4bd4:	ed1ff0ef          	jal	4aa4 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    4bd8:	81840513          	addi	a0,s0,-2024
    4bdc:	00812403          	lw	s0,8(sp)
    4be0:	00c12083          	lw	ra,12(sp)
    4be4:	ec448593          	addi	a1,s1,-316
    4be8:	00412483          	lw	s1,4(sp)
    4bec:	00300613          	li	a2,3
    4bf0:	01010113          	addi	sp,sp,16
    4bf4:	eb1ff06f          	j	4aa4 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>

00004bf8 <exit>:
    4bf8:	0000006f          	j	4bf8 <exit>
