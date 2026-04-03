
/tmp/tt-disasm-bj0qp7oi/out.elf:     file format elf32-littleriscv


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
    6a74:	37c0006f          	j	6df0 <exit>

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
    6aec:	42070713          	addi	a4,a4,1056 # ffb00420 <__fw_export_ldm_end>
    6af0:	00f76e63          	bltu	a4,a5,6b0c <main+0x94>
    6af4:	fe07ae23          	sw	zero,-4(a5)
    6af8:	fe07ac23          	sw	zero,-8(a5)
    6afc:	fe07aa23          	sw	zero,-12(a5)
    6b00:	fe07a823          	sw	zero,-16(a5)
    6b04:	01078793          	addi	a5,a5,16
    6b08:	fef776e3          	bgeu	a4,a5,6af4 <main+0x7c>
    6b0c:	ff878693          	addi	a3,a5,-8
    6b10:	2cd76c63          	bltu	a4,a3,6de8 <.NO_CB161+0x150>
    6b14:	fe07aa23          	sw	zero,-12(a5)
    6b18:	fe07a823          	sw	zero,-16(a5)
    6b1c:	ffc78693          	addi	a3,a5,-4
    6b20:	00d76463          	bltu	a4,a3,6b28 <main+0xb0>
    6b24:	fe07ac23          	sw	zero,-8(a5)
    6b28:	0000e737          	lui	a4,0xe
    6b2c:	81018793          	addi	a5,gp,-2032 # ffb00000 <_ZN7ckernel14dest_offset_idE>
    6b30:	6b070713          	addi	a4,a4,1712 # e6b0 <__fw_export_text_end+0x78b0>
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
    6be0:	000017b7          	lui	a5,0x1
    6be4:	9a07c703          	lbu	a4,-1632(a5) # 9a0 <_start-0x60a0>
    6be8:	06078793          	addi	a5,a5,96
    6bec:	83018413          	addi	s0,gp,-2000 # ffb00020 <cb_interface>
    6bf0:	08000c13          	li	s8,128
    6bf4:	82e184a3          	sb	a4,-2007(gp) # ffb00019 <my_logical_x_>
    6bf8:	9417c783          	lbu	a5,-1727(a5)
    6bfc:	ffe80cb7          	lui	s9,0xffe80
    6c00:	82f18423          	sb	a5,-2008(gp) # ffb00018 <my_logical_y_>
    6c04:	060005a3          	sb	zero,107(zero) # 6b <_start-0x69d5>
    6c08:	06b04783          	lbu	a5,107(zero) # 6b <_start-0x69d5>
    6c0c:	01878863          	beq	a5,s8,6c1c <main+0x1a4>
    6c10:	0ff0000f          	fence
    6c14:	06b04783          	lbu	a5,107(zero) # 6b <_start-0x69d5>
    6c18:	ff879ce3          	bne	a5,s8,6c10 <main+0x198>
    6c1c:	06c02783          	lw	a5,108(zero) # 6c <_start-0x69d4>
    6c20:	00040593          	mv	a1,s0
    6c24:	20f7a7b3          	sh1add	a5,a5,a5
    6c28:	00579793          	slli	a5,a5,0x5
    6c2c:	07078e93          	addi	t4,a5,112
    6c30:	0707af03          	lw	t5,112(a5)
    6c34:	012ed783          	lhu	a5,18(t4)
    6c38:	040ea703          	lw	a4,64(t4)
    6c3c:	01e787b3          	add	a5,a5,t5
    6c40:	0640006f          	j	6ca4 <.NO_CB161+0xc>
    6c44:	0047a683          	lw	a3,4(a5)
    6c48:	0007a603          	lw	a2,0(a5)
    6c4c:	0087a803          	lw	a6,8(a5)
    6c50:	00c7a883          	lw	a7,12(a5)
    6c54:	00175713          	srli	a4,a4,0x1
    6c58:	00177293          	andi	t0,a4,1
    6c5c:	0005ac23          	sw	zero,24(a1)
    6c60:	0005ae23          	sw	zero,28(a1)
    6c64:	01078793          	addi	a5,a5,16
    6c68:	0046d693          	srli	a3,a3,0x4
    6c6c:	00465613          	srli	a2,a2,0x4
    6c70:	0048d893          	srli	a7,a7,0x4
    6c74:	00d5a023          	sw	a3,0(a1)
    6c78:	00d606b3          	add	a3,a2,a3
    6c7c:	00d5a223          	sw	a3,4(a1)
    6c80:	00c5aa23          	sw	a2,20(a1)
    6c84:	0105a623          	sw	a6,12(a1)
    6c88:	0115a423          	sw	a7,8(a1)
    6c8c:	02058593          	addi	a1,a1,32
    6c90:	fa029ae3          	bnez	t0,6c44 <main+0x1cc>
    6c94:	00070e63          	beqz	a4,6cb0 <.NO_CB161+0x18>

00006c98 <.NO_CB161>:
    6c98:	01078793          	addi	a5,a5,16
    6c9c:	02058593          	addi	a1,a1,32
    6ca0:	00175713          	srli	a4,a4,0x1
    6ca4:	00177293          	andi	t0,a4,1
    6ca8:	f8029ee3          	bnez	t0,6c44 <main+0x1cc>
    6cac:	fe0716e3          	bnez	a4,6c98 <.NO_CB161>
    6cb0:	014ed503          	lhu	a0,20(t4)
    6cb4:	046ec783          	lbu	a5,70(t4)
    6cb8:	02000693          	li	a3,32
    6cbc:	01e50533          	add	a0,a0,t5
    6cc0:	0ff7fd93          	zext.b	s11,a5
    6cc4:	c1018713          	addi	a4,gp,-1008 # ffb00400 <cb_interface+0x3e0>
    6cc8:	01f00893          	li	a7,31
    6ccc:	04d79a63          	bne	a5,a3,6d20 <.NO_CB161+0x88>
    6cd0:	0b80006f          	j	6d88 <.NO_CB161+0xf0>
    6cd4:	00d72023          	sw	a3,0(a4)
    6cd8:	00c72223          	sw	a2,4(a4)
    6cdc:	01072823          	sw	a6,16(a4)
    6ce0:	00672a23          	sw	t1,20(a4)
    6ce4:	01c72c23          	sw	t3,24(a4)
    6ce8:	01a72e23          	sw	s10,28(a4)
    6cec:	00c6a803          	lw	a6,12(a3)
    6cf0:	010606b3          	add	a3,a2,a6
    6cf4:	02b87833          	remu	a6,a6,a1
    6cf8:	410686b3          	sub	a3,a3,a6
    6cfc:	00d7f463          	bgeu	a5,a3,6d04 <.NO_CB161+0x6c>
    6d00:	00078613          	mv	a2,a5
    6d04:	00c72823          	sw	a2,16(a4)
    6d08:	00d72423          	sw	a3,8(a4)
    6d0c:	00b72623          	sw	a1,12(a4)
    6d10:	00850513          	addi	a0,a0,8
    6d14:	fe070713          	addi	a4,a4,-32
    6d18:	071d8863          	beq	s11,a7,6d88 <.NO_CB161+0xf0>
    6d1c:	fff88893          	addi	a7,a7,-1
    6d20:	00052683          	lw	a3,0(a0)
    6d24:	00452583          	lw	a1,4(a0)
    6d28:	0006af83          	lw	t6,0(a3)
    6d2c:	0046ad03          	lw	s10,4(a3)
    6d30:	0086a603          	lw	a2,8(a3)
    6d34:	00c6a783          	lw	a5,12(a3)
    6d38:	0106a803          	lw	a6,16(a3)
    6d3c:	0146a303          	lw	t1,20(a3)
    6d40:	0186ae03          	lw	t3,24(a3)
    6d44:	fff58793          	addi	a5,a1,-1
    6d48:	010787b3          	add	a5,a5,a6
    6d4c:	40c787b3          	sub	a5,a5,a2
    6d50:	02b7f2b3          	remu	t0,a5,a1
    6d54:	010e0393          	addi	t2,t3,16
    6d58:	405787b3          	sub	a5,a5,t0
    6d5c:	00c787b3          	add	a5,a5,a2
    6d60:	f60f9ae3          	bnez	t6,6cd4 <.NO_CB161+0x3c>
    6d64:	00032e03          	lw	t3,0(t1)
    6d68:	00432303          	lw	t1,4(t1)
    6d6c:	00d72023          	sw	a3,0(a4)
    6d70:	00c72223          	sw	a2,4(a4)
    6d74:	01072823          	sw	a6,16(a4)
    6d78:	00772e23          	sw	t2,28(a4)
    6d7c:	01c72a23          	sw	t3,20(a4)
    6d80:	00672c23          	sw	t1,24(a4)
    6d84:	f69ff06f          	j	6cec <.NO_CB161+0x54>
    6d88:	026ed583          	lhu	a1,38(t4)
    6d8c:	028ed603          	lhu	a2,40(t4)
    6d90:	8291c683          	lbu	a3,-2007(gp) # ffb00019 <my_logical_x_>
    6d94:	05cec803          	lbu	a6,92(t4)
    6d98:	8281c703          	lbu	a4,-2008(gp) # ffb00018 <my_logical_y_>
    6d9c:	05dec503          	lbu	a0,93(t4)
    6da0:	03cea783          	lw	a5,60(t4)
    6da4:	01e585b3          	add	a1,a1,t5
    6da8:	01e60633          	add	a2,a2,t5
    6dac:	410686b3          	sub	a3,a3,a6
    6db0:	01e787b3          	add	a5,a5,t5
    6db4:	40a70733          	sub	a4,a4,a0
    6db8:	82b1a223          	sw	a1,-2012(gp) # ffb00014 <rta_l1_base>
    6dbc:	82c1a023          	sw	a2,-2016(gp) # ffb00010 <crta_l1_base>
    6dc0:	80d18ea3          	sb	a3,-2019(gp) # ffb0000d <my_relative_x_>
    6dc4:	80e18e23          	sb	a4,-2020(gp) # ffb0000c <my_relative_y_>
    6dc8:	000780e7          	jalr	a5
    6dcc:	00012623          	sw	zero,12(sp)
    6dd0:	00c12783          	lw	a5,12(sp)
    6dd4:	00fca223          	sw	a5,4(s9) # ffe80004 <__stack_top+0x37f004>
    6dd8:	004ca783          	lw	a5,4(s9)
    6ddc:	00f12623          	sw	a5,12(sp)
    6de0:	060005a3          	sb	zero,107(zero) # 6b <_start-0x69d5>
    6de4:	e25ff06f          	j	6c08 <main+0x190>
    6de8:	00068793          	mv	a5,a3
    6dec:	d31ff06f          	j	6b1c <main+0xa4>

00006df0 <exit>:
    6df0:	0000006f          	j	6df0 <exit>
