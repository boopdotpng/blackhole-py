
/tmp/tt-disasm-l7eugwh4/out.elf:     file format elf32-littleriscv


Disassembly of section .text:

00006040 <_start>:
    6040:	ffb001b7          	lui	gp,0xffb00
    6044:	7f018193          	addi	gp,gp,2032 # ffb007f0 <__global_pointer$>
    6048:	ffb01137          	lui	sp,0xffb01
    604c:	ff010113          	addi	sp,sp,-16 # ffb00ff0 <__global_pointer$+0x800>
    6050:	00810513          	addi	a0,sp,8
    6054:	00a12023          	sw	a0,0(sp)
    6058:	00012223          	sw	zero,4(sp)
    605c:	00912423          	sw	s1,8(sp)
    6060:	00012623          	sw	zero,12(sp)
    6064:	00100513          	li	a0,1
    6068:	00010593          	mv	a1,sp
    606c:	00000613          	li	a2,0
    6070:	008000ef          	jal	6078 <main>
    6074:	20c0006f          	j	6280 <exit>

00006078 <main>:
    6078:	fc010113          	addi	sp,sp,-64
    607c:	02112e23          	sw	ra,60(sp)
    6080:	02812c23          	sw	s0,56(sp)
    6084:	02912a23          	sw	s1,52(sp)
    6088:	03212823          	sw	s2,48(sp)
    608c:	03312623          	sw	s3,44(sp)
    6090:	03412423          	sw	s4,40(sp)
    6094:	03512223          	sw	s5,36(sp)
    6098:	03612023          	sw	s6,32(sp)
    609c:	01712e23          	sw	s7,28(sp)
    60a0:	00200313          	li	t1,2
    60a4:	7c032073          	csrs	0x7c0,t1
    60a8:	00100313          	li	t1,1
    60ac:	01231313          	slli	t1,t1,0x12
    60b0:	0ff0000f          	fence
    60b4:	7c032073          	csrs	0x7c0,t1
    60b8:	00200313          	li	t1,2
    60bc:	7c033073          	csrc	0x7c0,t1
    60c0:	0ff0000f          	fence
    60c4:	0ff0000f          	fence
    60c8:	00800313          	li	t1,8
    60cc:	7c032073          	csrs	0x7c0,t1
    60d0:	ffb007b7          	lui	a5,0xffb00
    60d4:	ffb00737          	lui	a4,0xffb00
    60d8:	01078793          	addi	a5,a5,16 # ffb00010 <rta_l1_base>
    60dc:	01c70713          	addi	a4,a4,28 # ffb0001c <__ldm_bss_end>
    60e0:	00f76e63          	bltu	a4,a5,60fc <main+0x84>
    60e4:	fe07ae23          	sw	zero,-4(a5)
    60e8:	fe07ac23          	sw	zero,-8(a5)
    60ec:	fe07aa23          	sw	zero,-12(a5)
    60f0:	fe07a823          	sw	zero,-16(a5)
    60f4:	01078793          	addi	a5,a5,16
    60f8:	fef776e3          	bgeu	a4,a5,60e4 <main+0x6c>
    60fc:	ff878693          	addi	a3,a5,-8
    6100:	16d76c63          	bltu	a4,a3,6278 <main+0x200>
    6104:	fe07aa23          	sw	zero,-12(a5)
    6108:	fe07a823          	sw	zero,-16(a5)
    610c:	ffc78693          	addi	a3,a5,-4
    6110:	00d76463          	bltu	a4,a3,6118 <main+0xa0>
    6114:	fe07ac23          	sw	zero,-8(a5)
    6118:	0000d737          	lui	a4,0xd
    611c:	81018793          	addi	a5,gp,-2032 # ffb00000 <_ZN7ckernel14dest_offset_idE>
    6120:	6b070713          	addi	a4,a4,1712 # d6b0 <__fw_export_text_end+0x7420>
    6124:	06e78063          	beq	a5,a4,6184 <main+0x10c>
    6128:	81018613          	addi	a2,gp,-2032 # ffb00000 <_ZN7ckernel14dest_offset_idE>
    612c:	40f60633          	sub	a2,a2,a5
    6130:	00800593          	li	a1,8
    6134:	40265693          	srai	a3,a2,0x2
    6138:	02c5d863          	bge	a1,a2,6168 <main+0xf0>
    613c:	00200813          	li	a6,2
    6140:	00072503          	lw	a0,0(a4)
    6144:	00472583          	lw	a1,4(a4)
    6148:	00872603          	lw	a2,8(a4)
    614c:	00c70713          	addi	a4,a4,12
    6150:	00c78793          	addi	a5,a5,12
    6154:	ffd68693          	addi	a3,a3,-3
    6158:	fea7aa23          	sw	a0,-12(a5)
    615c:	feb7ac23          	sw	a1,-8(a5)
    6160:	fec7ae23          	sw	a2,-4(a5)
    6164:	fcd84ee3          	blt	a6,a3,6140 <main+0xc8>
    6168:	00d05e63          	blez	a3,6184 <main+0x10c>
    616c:	00072583          	lw	a1,0(a4)
    6170:	00200613          	li	a2,2
    6174:	00b7a023          	sw	a1,0(a5)
    6178:	00c69663          	bne	a3,a2,6184 <main+0x10c>
    617c:	00472703          	lw	a4,4(a4)
    6180:	00e7a223          	sw	a4,4(a5)
    6184:	ffe007b7          	lui	a5,0xffe00
    6188:	10078713          	addi	a4,a5,256 # ffe00100 <__stack_top+0x2ff100>
    618c:	0007a023          	sw	zero,0(a5)
    6190:	00478793          	addi	a5,a5,4
    6194:	fee79ce3          	bne	a5,a4,618c <main+0x114>
    6198:	8201a423          	sw	zero,-2008(gp) # ffb00018 <_ZN7ckernel12cfg_state_idE>
    619c:	ffef07b7          	lui	a5,0xffef0
    61a0:	2e07a423          	sw	zero,744(a5) # ffef02e8 <__stack_top+0x3ef2e8>
    61a4:	ffb127b7          	lui	a5,0xffb12
    61a8:	1f07a703          	lw	a4,496(a5) # ffb121f0 <__stack_top+0x111f0>
    61ac:	1f87a683          	lw	a3,504(a5)
    61b0:	25870593          	addi	a1,a4,600
    61b4:	00e5b733          	sltu	a4,a1,a4
    61b8:	00d706b3          	add	a3,a4,a3
    61bc:	1f07a603          	lw	a2,496(a5)
    61c0:	1f87a703          	lw	a4,504(a5)
    61c4:	fed76ce3          	bltu	a4,a3,61bc <main+0x144>
    61c8:	00e69463          	bne	a3,a4,61d0 <main+0x158>
    61cc:	feb668e3          	bltu	a2,a1,61bc <main+0x144>
    61d0:	000017b7          	lui	a5,0x1
    61d4:	9a07c703          	lbu	a4,-1632(a5) # 9a0 <_start-0x56a0>
    61d8:	06078793          	addi	a5,a5,96
    61dc:	08000b13          	li	s6,128
    61e0:	ffe80bb7          	lui	s7,0xffe80
    61e4:	82e182a3          	sb	a4,-2011(gp) # ffb00015 <my_logical_x_>
    61e8:	9417c783          	lbu	a5,-1727(a5)
    61ec:	82f18223          	sb	a5,-2012(gp) # ffb00014 <my_logical_y_>
    61f0:	06000523          	sb	zero,106(zero) # 6a <_start-0x5fd6>
    61f4:	06a04783          	lbu	a5,106(zero) # 6a <_start-0x5fd6>
    61f8:	01678863          	beq	a5,s6,6208 <main+0x190>
    61fc:	0ff0000f          	fence
    6200:	06a04783          	lbu	a5,106(zero) # 6a <_start-0x5fd6>
    6204:	ff679ce3          	bne	a5,s6,61fc <main+0x184>
    6208:	06c02783          	lw	a5,108(zero) # 6c <_start-0x5fd4>
    620c:	8251c603          	lbu	a2,-2011(gp) # ffb00015 <my_logical_x_>
    6210:	8241c683          	lbu	a3,-2012(gp) # ffb00014 <my_logical_y_>
    6214:	20f7a7b3          	sh1add	a5,a5,a5
    6218:	00579793          	slli	a5,a5,0x5
    621c:	0707a583          	lw	a1,112(a5)
    6220:	0927d803          	lhu	a6,146(a5)
    6224:	0947d503          	lhu	a0,148(a5)
    6228:	0cc7c303          	lbu	t1,204(a5)
    622c:	0cd7c883          	lbu	a7,205(a5)
    6230:	0a87a783          	lw	a5,168(a5)
    6234:	00b50733          	add	a4,a0,a1
    6238:	00b80833          	add	a6,a6,a1
    623c:	80e1ae23          	sw	a4,-2020(gp) # ffb0000c <crta_l1_base>
    6240:	00b787b3          	add	a5,a5,a1
    6244:	40660633          	sub	a2,a2,t1
    6248:	41168733          	sub	a4,a3,a7
    624c:	8301a023          	sw	a6,-2016(gp) # ffb00010 <rta_l1_base>
    6250:	80c18ca3          	sb	a2,-2023(gp) # ffb00009 <my_relative_x_>
    6254:	80e18c23          	sb	a4,-2024(gp) # ffb00008 <my_relative_y_>
    6258:	000780e7          	jalr	a5
    625c:	00012623          	sw	zero,12(sp)
    6260:	00c12783          	lw	a5,12(sp)
    6264:	00fba223          	sw	a5,4(s7) # ffe80004 <__stack_top+0x37f004>
    6268:	004ba783          	lw	a5,4(s7)
    626c:	00f12623          	sw	a5,12(sp)
    6270:	06000523          	sb	zero,106(zero) # 6a <_start-0x5fd6>
    6274:	f81ff06f          	j	61f4 <main+0x17c>
    6278:	00068793          	mv	a5,a3
    627c:	e91ff06f          	j	610c <main+0x94>

00006280 <exit>:
    6280:	0000006f          	j	6280 <exit>
