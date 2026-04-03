
/tmp/tt-disasm-3abjr5sg/out.elf:     file format elf32-littleriscv


Disassembly of section .text:

00006a40 <_start>:
    6a40:	ffb001b7          	lui	gp,0xffb00
    6a44:	7f018193          	addi	gp,gp,2032 # ffb007f0 <__global_pointer$>
    6a48:	ffb01137          	lui	sp,0xffb01
    6a4c:	ff010113          	addi	sp,sp,-16 # ffb00ff0 <__global_pointer$+0x800>
    6a50:	00810513          	addi	a0,sp,8
    6a54:	00a12023          	sw	a0,0(sp)
    6a58:	00012223          	sw	zero,4(sp)
    6a5c:	00912423          	sw	s1,8(sp)
    6a60:	00012623          	sw	zero,12(sp)
    6a64:	00100513          	li	a0,1
    6a68:	00010593          	mv	a1,sp
    6a6c:	00000613          	li	a2,0
    6a70:	008000ef          	jal	6a78 <main>
    6a74:	5280006f          	j	6f9c <exit>

00006a78 <main>:
    6a78:	fb010113          	addi	sp,sp,-80
    6a7c:	04112623          	sw	ra,76(sp)
    6a80:	04812423          	sw	s0,72(sp)
    6a84:	04912223          	sw	s1,68(sp)
    6a88:	05212023          	sw	s2,64(sp)
    6a8c:	03312e23          	sw	s3,60(sp)
    6a90:	03412c23          	sw	s4,56(sp)
    6a94:	03512a23          	sw	s5,52(sp)
    6a98:	03612823          	sw	s6,48(sp)
    6a9c:	03712623          	sw	s7,44(sp)
    6aa0:	03812423          	sw	s8,40(sp)
    6aa4:	03912223          	sw	s9,36(sp)
    6aa8:	03a12023          	sw	s10,32(sp)
    6aac:	01b12e23          	sw	s11,28(sp)
    6ab0:	00200313          	li	t1,2
    6ab4:	7c032073          	csrs	0x7c0,t1
    6ab8:	00100313          	li	t1,1
    6abc:	01231313          	slli	t1,t1,0x12
    6ac0:	0ff0000f          	fence
    6ac4:	7c032073          	csrs	0x7c0,t1
    6ac8:	00200313          	li	t1,2
    6acc:	7c033073          	csrc	0x7c0,t1
    6ad0:	0ff0000f          	fence
    6ad4:	0ff0000f          	fence
    6ad8:	00800313          	li	t1,8
    6adc:	7c032073          	csrs	0x7c0,t1
    6ae0:	ffb007b7          	lui	a5,0xffb00
    6ae4:	ffb00737          	lui	a4,0xffb00
    6ae8:	01078793          	addi	a5,a5,16 # ffb00010 <crta_l1_base>
    6aec:	43870713          	addi	a4,a4,1080 # ffb00438 <__ldm_bss_end>
    6af0:	00f76e63          	bltu	a4,a5,6b0c <main+0x94>
    6af4:	fe07ae23          	sw	zero,-4(a5)
    6af8:	fe07ac23          	sw	zero,-8(a5)
    6afc:	fe07aa23          	sw	zero,-12(a5)
    6b00:	fe07a823          	sw	zero,-16(a5)
    6b04:	01078793          	addi	a5,a5,16
    6b08:	fef776e3          	bgeu	a4,a5,6af4 <main+0x7c>
    6b0c:	ff878693          	addi	a3,a5,-8
    6b10:	32d76663          	bltu	a4,a3,6e3c <.NO_CB319+0x174>
    6b14:	fe07aa23          	sw	zero,-12(a5)
    6b18:	fe07a823          	sw	zero,-16(a5)
    6b1c:	ffc78693          	addi	a3,a5,-4
    6b20:	00d76463          	bltu	a4,a3,6b28 <main+0xb0>
    6b24:	fe07ac23          	sw	zero,-8(a5)
    6b28:	0000e737          	lui	a4,0xe
    6b2c:	81018793          	addi	a5,gp,-2032 # ffb00000 <_ZN7ckernel14dest_offset_idE>
    6b30:	6b070713          	addi	a4,a4,1712 # e6b0 <__fw_export_text_end+0x7710>
    6b34:	06e78063          	beq	a5,a4,6b94 <main+0x11c>
    6b38:	81018613          	addi	a2,gp,-2032 # ffb00000 <_ZN7ckernel14dest_offset_idE>
    6b3c:	40f60633          	sub	a2,a2,a5
    6b40:	00800593          	li	a1,8
    6b44:	40265693          	srai	a3,a2,0x2
    6b48:	02c5d863          	bge	a1,a2,6b78 <main+0x100>
    6b4c:	00200813          	li	a6,2
    6b50:	00072503          	lw	a0,0(a4)
    6b54:	00472583          	lw	a1,4(a4)
    6b58:	00872603          	lw	a2,8(a4)
    6b5c:	00c70713          	addi	a4,a4,12
    6b60:	00c78793          	addi	a5,a5,12
    6b64:	ffd68693          	addi	a3,a3,-3
    6b68:	fea7aa23          	sw	a0,-12(a5)
    6b6c:	feb7ac23          	sw	a1,-8(a5)
    6b70:	fec7ae23          	sw	a2,-4(a5)
    6b74:	fcd84ee3          	blt	a6,a3,6b50 <main+0xd8>
    6b78:	00d05e63          	blez	a3,6b94 <main+0x11c>
    6b7c:	00072583          	lw	a1,0(a4)
    6b80:	00200613          	li	a2,2
    6b84:	00b7a023          	sw	a1,0(a5)
    6b88:	00c69663          	bne	a3,a2,6b94 <main+0x11c>
    6b8c:	00472703          	lw	a4,4(a4)
    6b90:	00e7a223          	sw	a4,4(a5)
    6b94:	ffe007b7          	lui	a5,0xffe00
    6b98:	10078713          	addi	a4,a5,256 # ffe00100 <__stack_top+0x2ff100>
    6b9c:	0007a023          	sw	zero,0(a5)
    6ba0:	00478793          	addi	a5,a5,4
    6ba4:	fee79ce3          	bne	a5,a4,6b9c <main+0x124>
    6ba8:	8201a623          	sw	zero,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    6bac:	ffef07b7          	lui	a5,0xffef0
    6bb0:	2e07a423          	sw	zero,744(a5) # ffef02e8 <__stack_top+0x3ef2e8>
    6bb4:	ffb127b7          	lui	a5,0xffb12
    6bb8:	1f07a703          	lw	a4,496(a5) # ffb121f0 <__stack_top+0x111f0>
    6bbc:	1f87a683          	lw	a3,504(a5)
    6bc0:	25870593          	addi	a1,a4,600
    6bc4:	00e5b733          	sltu	a4,a1,a4
    6bc8:	00d706b3          	add	a3,a4,a3
    6bcc:	1f07a603          	lw	a2,496(a5)
    6bd0:	1f87a703          	lw	a4,504(a5)
    6bd4:	fed76ce3          	bltu	a4,a3,6bcc <main+0x154>
    6bd8:	00e69463          	bne	a3,a4,6be0 <main+0x168>
    6bdc:	feb668e3          	bltu	a2,a1,6bcc <main+0x154>
    6be0:	00001937          	lui	s2,0x1
    6be4:	9a094703          	lbu	a4,-1632(s2) # 9a0 <_start-0x60a0>
    6be8:	00090793          	mv	a5,s2
    6bec:	00002437          	lui	s0,0x2
    6bf0:	7ff40413          	addi	s0,s0,2047 # 27ff <_start-0x4241>
    6bf4:	fff90913          	addi	s2,s2,-1
    6bf8:	24140413          	addi	s0,s0,577
    6bfc:	84818993          	addi	s3,gp,-1976 # ffb00038 <cb_interface>
    6c00:	82e184a3          	sb	a4,-2007(gp) # ffb00019 <my_logical_x_>
    6c04:	9a17c783          	lbu	a5,-1631(a5)
    6c08:	08000c93          	li	s9,128
    6c0c:	ffb124b7          	lui	s1,0xffb12
    6c10:	82f18423          	sb	a5,-2008(gp) # ffb00018 <my_logical_y_>
    6c14:	060005a3          	sb	zero,107(zero) # 6b <_start-0x69d5>
    6c18:	06b04783          	lbu	a5,107(zero) # 6b <_start-0x69d5>
    6c1c:	01978863          	beq	a5,s9,6c2c <main+0x1b4>
    6c20:	0ff0000f          	fence
    6c24:	06b04783          	lbu	a5,107(zero) # 6b <_start-0x69d5>
    6c28:	ff979ce3          	bne	a5,s9,6c20 <main+0x1a8>
    6c2c:	218000ef          	jal	6e44 <_ZN15kernel_profiler13init_profilerEttt.constprop.0>
    6c30:	1f44a783          	lw	a5,500(s1) # ffb121f4 <__stack_top+0x111f4>
    6c34:	80e98737          	lui	a4,0x80e98
    6c38:	00098593          	mv	a1,s3
    6c3c:	0127f7b3          	and	a5,a5,s2
    6c40:	00e7e7b3          	or	a5,a5,a4
    6c44:	00f42823          	sw	a5,16(s0)
    6c48:	1f04a783          	lw	a5,496(s1)
    6c4c:	00f42a23          	sw	a5,20(s0)
    6c50:	06c02783          	lw	a5,108(zero) # 6c <_start-0x69d4>
    6c54:	20f7a7b3          	sh1add	a5,a5,a5
    6c58:	00579793          	slli	a5,a5,0x5
    6c5c:	07078e93          	addi	t4,a5,112
    6c60:	0707af03          	lw	t5,112(a5)
    6c64:	012ed783          	lhu	a5,18(t4)
    6c68:	040ea703          	lw	a4,64(t4)
    6c6c:	01e787b3          	add	a5,a5,t5
    6c70:	0640006f          	j	6cd4 <.NO_CB319+0xc>
    6c74:	0047a683          	lw	a3,4(a5)
    6c78:	0007a603          	lw	a2,0(a5)
    6c7c:	0087a803          	lw	a6,8(a5)
    6c80:	00c7a883          	lw	a7,12(a5)
    6c84:	00175713          	srli	a4,a4,0x1
    6c88:	00177293          	andi	t0,a4,1
    6c8c:	0005ac23          	sw	zero,24(a1)
    6c90:	0005ae23          	sw	zero,28(a1)
    6c94:	01078793          	addi	a5,a5,16
    6c98:	0046d693          	srli	a3,a3,0x4
    6c9c:	00465613          	srli	a2,a2,0x4
    6ca0:	0048d893          	srli	a7,a7,0x4
    6ca4:	00d5a023          	sw	a3,0(a1)
    6ca8:	00d606b3          	add	a3,a2,a3
    6cac:	00d5a223          	sw	a3,4(a1)
    6cb0:	00c5aa23          	sw	a2,20(a1)
    6cb4:	0105a623          	sw	a6,12(a1)
    6cb8:	0115a423          	sw	a7,8(a1)
    6cbc:	02058593          	addi	a1,a1,32
    6cc0:	fa029ae3          	bnez	t0,6c74 <main+0x1fc>
    6cc4:	00070e63          	beqz	a4,6ce0 <.NO_CB319+0x18>

00006cc8 <.NO_CB319>:
    6cc8:	01078793          	addi	a5,a5,16
    6ccc:	02058593          	addi	a1,a1,32
    6cd0:	00175713          	srli	a4,a4,0x1
    6cd4:	00177293          	andi	t0,a4,1
    6cd8:	f8029ee3          	bnez	t0,6c74 <main+0x1fc>
    6cdc:	fe0716e3          	bnez	a4,6cc8 <.NO_CB319>
    6ce0:	014ed503          	lhu	a0,20(t4)
    6ce4:	046ec783          	lbu	a5,70(t4)
    6ce8:	02000693          	li	a3,32
    6cec:	01e50533          	add	a0,a0,t5
    6cf0:	0ff7fd93          	zext.b	s11,a5
    6cf4:	c2818713          	addi	a4,gp,-984 # ffb00418 <cb_interface+0x3e0>
    6cf8:	01f00893          	li	a7,31
    6cfc:	04d79a63          	bne	a5,a3,6d50 <.NO_CB319+0x88>
    6d00:	0b80006f          	j	6db8 <.NO_CB319+0xf0>
    6d04:	00d72023          	sw	a3,0(a4) # 80e98000 <__fw_export_text_end+0x80e91060>
    6d08:	00c72223          	sw	a2,4(a4)
    6d0c:	01072823          	sw	a6,16(a4)
    6d10:	00672a23          	sw	t1,20(a4)
    6d14:	01c72c23          	sw	t3,24(a4)
    6d18:	01a72e23          	sw	s10,28(a4)
    6d1c:	00c6a803          	lw	a6,12(a3)
    6d20:	010606b3          	add	a3,a2,a6
    6d24:	02b87833          	remu	a6,a6,a1
    6d28:	410686b3          	sub	a3,a3,a6
    6d2c:	00d7f463          	bgeu	a5,a3,6d34 <.NO_CB319+0x6c>
    6d30:	00078613          	mv	a2,a5
    6d34:	00c72823          	sw	a2,16(a4)
    6d38:	00d72423          	sw	a3,8(a4)
    6d3c:	00b72623          	sw	a1,12(a4)
    6d40:	00850513          	addi	a0,a0,8
    6d44:	fe070713          	addi	a4,a4,-32
    6d48:	071d8863          	beq	s11,a7,6db8 <.NO_CB319+0xf0>
    6d4c:	fff88893          	addi	a7,a7,-1
    6d50:	00052683          	lw	a3,0(a0)
    6d54:	00452583          	lw	a1,4(a0)
    6d58:	0006af83          	lw	t6,0(a3)
    6d5c:	0046ad03          	lw	s10,4(a3)
    6d60:	0086a603          	lw	a2,8(a3)
    6d64:	00c6a783          	lw	a5,12(a3)
    6d68:	0106a803          	lw	a6,16(a3)
    6d6c:	0146a303          	lw	t1,20(a3)
    6d70:	0186ae03          	lw	t3,24(a3)
    6d74:	fff58793          	addi	a5,a1,-1
    6d78:	010787b3          	add	a5,a5,a6
    6d7c:	40c787b3          	sub	a5,a5,a2
    6d80:	02b7f2b3          	remu	t0,a5,a1
    6d84:	010e0393          	addi	t2,t3,16
    6d88:	405787b3          	sub	a5,a5,t0
    6d8c:	00c787b3          	add	a5,a5,a2
    6d90:	f60f9ae3          	bnez	t6,6d04 <.NO_CB319+0x3c>
    6d94:	00032e03          	lw	t3,0(t1)
    6d98:	00432303          	lw	t1,4(t1)
    6d9c:	00d72023          	sw	a3,0(a4)
    6da0:	00c72223          	sw	a2,4(a4)
    6da4:	01072823          	sw	a6,16(a4)
    6da8:	00772e23          	sw	t2,28(a4)
    6dac:	01c72a23          	sw	t3,20(a4)
    6db0:	00672c23          	sw	t1,24(a4)
    6db4:	f69ff06f          	j	6d1c <.NO_CB319+0x54>
    6db8:	026ed583          	lhu	a1,38(t4)
    6dbc:	8291c683          	lbu	a3,-2007(gp) # ffb00019 <my_logical_x_>
    6dc0:	028ed603          	lhu	a2,40(t4)
    6dc4:	05cec803          	lbu	a6,92(t4)
    6dc8:	8281c703          	lbu	a4,-2008(gp) # ffb00018 <my_logical_y_>
    6dcc:	05dec503          	lbu	a0,93(t4)
    6dd0:	03cea783          	lw	a5,60(t4)
    6dd4:	410686b3          	sub	a3,a3,a6
    6dd8:	01e585b3          	add	a1,a1,t5
    6ddc:	01e60633          	add	a2,a2,t5
    6de0:	01e787b3          	add	a5,a5,t5
    6de4:	40a70733          	sub	a4,a4,a0
    6de8:	80d18ea3          	sb	a3,-2019(gp) # ffb0000d <my_relative_x_>
    6dec:	82b1a223          	sw	a1,-2012(gp) # ffb00014 <rta_l1_base>
    6df0:	82c1a023          	sw	a2,-2016(gp) # ffb00010 <crta_l1_base>
    6df4:	80e18e23          	sb	a4,-2020(gp) # ffb0000c <my_relative_y_>
    6df8:	000780e7          	jalr	a5
    6dfc:	00012623          	sw	zero,12(sp)
    6e00:	00c12703          	lw	a4,12(sp)
    6e04:	ffe807b7          	lui	a5,0xffe80
    6e08:	00e7a223          	sw	a4,4(a5) # ffe80004 <__stack_top+0x37f004>
    6e0c:	0047a783          	lw	a5,4(a5)
    6e10:	90e98737          	lui	a4,0x90e98
    6e14:	00f12623          	sw	a5,12(sp)
    6e18:	060005a3          	sb	zero,107(zero) # 6b <_start-0x69d5>
    6e1c:	1f44a783          	lw	a5,500(s1)
    6e20:	0127f7b3          	and	a5,a5,s2
    6e24:	00e7e7b3          	or	a5,a5,a4
    6e28:	00f42c23          	sw	a5,24(s0)
    6e2c:	1f04a783          	lw	a5,496(s1)
    6e30:	00f42e23          	sw	a5,28(s0)
    6e34:	038000ef          	jal	6e6c <_ZN15kernel_profiler15finish_profilerEv>
    6e38:	de1ff06f          	j	6c18 <main+0x1a0>
    6e3c:	00068793          	mv	a5,a3
    6e40:	cddff06f          	j	6b1c <main+0xa4>

00006e44 <_ZN15kernel_profiler13init_profilerEttt.constprop.0>:
    6e44:	83818713          	addi	a4,gp,-1992 # ffb00028 <_ZN15kernel_profiler6sumIDsE>
    6e48:	83018793          	addi	a5,gp,-2000 # ffb00020 <_ZN15kernel_profiler4sumsE>
    6e4c:	00c00593          	li	a1,12
    6e50:	00072023          	sw	zero,0(a4) # 90e98000 <__fw_export_text_end+0x90e91060>
    6e54:	00072223          	sw	zero,4(a4)
    6e58:	0007a023          	sw	zero,0(a5)
    6e5c:	0007a223          	sw	zero,4(a5)
    6e60:	84b1a223          	sw	a1,-1980(gp) # ffb00034 <_ZN15kernel_profiler6wIndexE>
    6e64:	8401a023          	sw	zero,-1984(gp) # ffb00030 <_ZN15kernel_profiler9stackSizeE>
    6e68:	00008067          	ret

00006e6c <_ZN15kernel_profiler15finish_profilerEv>:
    6e6c:	83018793          	addi	a5,gp,-2000 # ffb00020 <_ZN15kernel_profiler4sumsE>
    6e70:	0007a683          	lw	a3,0(a5)
    6e74:	8441a703          	lw	a4,-1980(gp) # ffb00034 <_ZN15kernel_profiler6wIndexE>
    6e78:	08069263          	bnez	a3,6efc <_ZN15kernel_profiler15finish_profilerEv+0x90>
    6e7c:	0047a883          	lw	a7,4(a5)
    6e80:	10089663          	bnez	a7,6f8c <_ZN15kernel_profiler15finish_profilerEv+0x120>
    6e84:	00377613          	andi	a2,a4,3
    6e88:	04060c63          	beqz	a2,6ee0 <_ZN15kernel_profiler15finish_profilerEv+0x74>
    6e8c:	00000813          	li	a6,0
    6e90:	00000693          	li	a3,0
    6e94:	1ff00513          	li	a0,511
    6e98:	000025b7          	lui	a1,0x2
    6e9c:	800008b7          	lui	a7,0x80000
    6ea0:	20b747b3          	sh2add	a5,a4,a1
    6ea4:	7ff78793          	addi	a5,a5,2047
    6ea8:	02e56663          	bltu	a0,a4,6ed4 <_ZN15kernel_profiler15finish_profilerEv+0x68>
    6eac:	2517a0a3          	sw	a7,577(a5)
    6eb0:	00270713          	addi	a4,a4,2
    6eb4:	2407a2a3          	sw	zero,581(a5)
    6eb8:	00168693          	addi	a3,a3,1
    6ebc:	00377613          	andi	a2,a4,3
    6ec0:	02c6f663          	bgeu	a3,a2,6eec <_ZN15kernel_profiler15finish_profilerEv+0x80>
    6ec4:	20b747b3          	sh2add	a5,a4,a1
    6ec8:	00100813          	li	a6,1
    6ecc:	7ff78793          	addi	a5,a5,2047
    6ed0:	fce57ee3          	bgeu	a0,a4,6eac <_ZN15kernel_profiler15finish_profilerEv+0x40>
    6ed4:	00168693          	addi	a3,a3,1
    6ed8:	fcc6e4e3          	bltu	a3,a2,6ea0 <_ZN15kernel_profiler15finish_profilerEv+0x34>
    6edc:	00081863          	bnez	a6,6eec <_ZN15kernel_profiler15finish_profilerEv+0x80>
    6ee0:	000017b7          	lui	a5,0x1
    6ee4:	9ee7a223          	sw	a4,-1564(a5) # 9e4 <_start-0x605c>
    6ee8:	00008067          	ret
    6eec:	84e1a223          	sw	a4,-1980(gp) # ffb00034 <_ZN15kernel_profiler6wIndexE>
    6ef0:	000017b7          	lui	a5,0x1
    6ef4:	9ee7a223          	sw	a4,-1564(a5) # 9e4 <_start-0x605c>
    6ef8:	00008067          	ret
    6efc:	1ff00813          	li	a6,511
    6f00:	f8e862e3          	bltu	a6,a4,6e84 <_ZN15kernel_profiler15finish_profilerEv+0x18>
    6f04:	83818513          	addi	a0,gp,-1992 # ffb00028 <_ZN15kernel_profiler6sumIDsE>
    6f08:	00052583          	lw	a1,0(a0)
    6f0c:	00271613          	slli	a2,a4,0x2
    6f10:	0ffff8b7          	lui	a7,0xffff
    6f14:	00c59593          	slli	a1,a1,0xc
    6f18:	7ff60613          	addi	a2,a2,2047
    6f1c:	0115f5b3          	and	a1,a1,a7
    6f20:	a0000e37          	lui	t3,0xa0000
    6f24:	000028b7          	lui	a7,0x2
    6f28:	24160613          	addi	a2,a2,577
    6f2c:	01160633          	add	a2,a2,a7
    6f30:	01c5e5b3          	or	a1,a1,t3
    6f34:	00b62023          	sw	a1,0(a2)
    6f38:	0047a883          	lw	a7,4(a5)
    6f3c:	00d62223          	sw	a3,4(a2)
    6f40:	00270713          	addi	a4,a4,2
    6f44:	04088063          	beqz	a7,6f84 <_ZN15kernel_profiler15finish_profilerEv+0x118>
    6f48:	02e86e63          	bltu	a6,a4,6f84 <_ZN15kernel_profiler15finish_profilerEv+0x118>
    6f4c:	00452683          	lw	a3,4(a0)
    6f50:	00271793          	slli	a5,a4,0x2
    6f54:	0ffff637          	lui	a2,0xffff
    6f58:	00c69693          	slli	a3,a3,0xc
    6f5c:	7ff78793          	addi	a5,a5,2047
    6f60:	00c6f6b3          	and	a3,a3,a2
    6f64:	a00005b7          	lui	a1,0xa0000
    6f68:	24178793          	addi	a5,a5,577
    6f6c:	00002637          	lui	a2,0x2
    6f70:	00c787b3          	add	a5,a5,a2
    6f74:	00b6e6b3          	or	a3,a3,a1
    6f78:	00d7a023          	sw	a3,0(a5)
    6f7c:	00270713          	addi	a4,a4,2
    6f80:	0117a223          	sw	a7,4(a5)
    6f84:	84e1a223          	sw	a4,-1980(gp) # ffb00034 <_ZN15kernel_profiler6wIndexE>
    6f88:	efdff06f          	j	6e84 <_ZN15kernel_profiler15finish_profilerEv+0x18>
    6f8c:	1ff00793          	li	a5,511
    6f90:	eee7eae3          	bltu	a5,a4,6e84 <_ZN15kernel_profiler15finish_profilerEv+0x18>
    6f94:	83818513          	addi	a0,gp,-1992 # ffb00028 <_ZN15kernel_profiler6sumIDsE>
    6f98:	fb5ff06f          	j	6f4c <_ZN15kernel_profiler15finish_profilerEv+0xe0>

00006f9c <exit>:
    6f9c:	0000006f          	j	6f9c <exit>
