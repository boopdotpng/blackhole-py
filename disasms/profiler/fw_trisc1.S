
/tmp/tt-disasm-fw_trisc1-m4o0zi9h/out.elf:     file format elf32-littleriscv


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
    6074:	5dc0006f          	j	6650 <exit>

00006078 <main>:
    6078:	fb010113          	addi	sp,sp,-80
    607c:	04112623          	sw	ra,76(sp)
    6080:	04812423          	sw	s0,72(sp)
    6084:	04912223          	sw	s1,68(sp)
    6088:	03312e23          	sw	s3,60(sp)
    608c:	03412c23          	sw	s4,56(sp)
    6090:	03512a23          	sw	s5,52(sp)
    6094:	03612823          	sw	s6,48(sp)
    6098:	03712623          	sw	s7,44(sp)
    609c:	03812423          	sw	s8,40(sp)
    60a0:	03912223          	sw	s9,36(sp)
    60a4:	03a12023          	sw	s10,32(sp)
    60a8:	01b12e23          	sw	s11,28(sp)
    60ac:	00200313          	li	t1,2
    60b0:	7c032073          	csrs	0x7c0,t1
    60b4:	00100313          	li	t1,1
    60b8:	01231313          	slli	t1,t1,0x12
    60bc:	0ff0000f          	fence
    60c0:	7c032073          	csrs	0x7c0,t1
    60c4:	00200313          	li	t1,2
    60c8:	7c033073          	csrc	0x7c0,t1
    60cc:	0ff0000f          	fence
    60d0:	0ff0000f          	fence
    60d4:	00800313          	li	t1,8
    60d8:	7c032073          	csrs	0x7c0,t1
    60dc:	ffb007b7          	lui	a5,0xffb00
    60e0:	ffb00737          	lui	a4,0xffb00
    60e4:	20878793          	addi	a5,a5,520 # ffb00208 <rta_l1_base>
    60e8:	52070713          	addi	a4,a4,1312 # ffb00520 <__fw_export_ldm_end>
    60ec:	00f76e63          	bltu	a4,a5,6108 <main+0x90>
    60f0:	fe07ae23          	sw	zero,-4(a5)
    60f4:	fe07ac23          	sw	zero,-8(a5)
    60f8:	fe07aa23          	sw	zero,-12(a5)
    60fc:	fe07a823          	sw	zero,-16(a5)
    6100:	01078793          	addi	a5,a5,16
    6104:	fef776e3          	bgeu	a4,a5,60f0 <main+0x78>
    6108:	ff878693          	addi	a3,a5,-8
    610c:	00d76863          	bltu	a4,a3,611c <main+0xa4>
    6110:	fe07aa23          	sw	zero,-12(a5)
    6114:	fe07a823          	sw	zero,-16(a5)
    6118:	00078693          	mv	a3,a5
    611c:	ffc68793          	addi	a5,a3,-4
    6120:	00f76463          	bltu	a4,a5,6128 <main+0xb0>
    6124:	fe06ac23          	sw	zero,-8(a3)
    6128:	0000d737          	lui	a4,0xd
    612c:	81018793          	addi	a5,gp,-2032 # ffb00000 <CSWTCH.148>
    6130:	6b070713          	addi	a4,a4,1712 # d6b0 <__fw_export_text_end+0x7050>
    6134:	06e78263          	beq	a5,a4,6198 <main+0x120>
    6138:	ffb00637          	lui	a2,0xffb00
    613c:	1f860613          	addi	a2,a2,504 # ffb001f8 <_ZN7ckernel14dest_offset_idE>
    6140:	40f60633          	sub	a2,a2,a5
    6144:	00800593          	li	a1,8
    6148:	40265693          	srai	a3,a2,0x2
    614c:	02c5d863          	bge	a1,a2,617c <main+0x104>
    6150:	00200613          	li	a2,2
    6154:	00072803          	lw	a6,0(a4)
    6158:	00472503          	lw	a0,4(a4)
    615c:	00872583          	lw	a1,8(a4)
    6160:	00c70713          	addi	a4,a4,12
    6164:	00c78793          	addi	a5,a5,12
    6168:	ffd68693          	addi	a3,a3,-3
    616c:	ff07aa23          	sw	a6,-12(a5)
    6170:	fea7ac23          	sw	a0,-8(a5)
    6174:	feb7ae23          	sw	a1,-4(a5)
    6178:	fcd64ee3          	blt	a2,a3,6154 <main+0xdc>
    617c:	00d05e63          	blez	a3,6198 <main+0x120>
    6180:	00072583          	lw	a1,0(a4)
    6184:	00200613          	li	a2,2
    6188:	00b7a023          	sw	a1,0(a5)
    618c:	00c69663          	bne	a3,a2,6198 <main+0x120>
    6190:	00472703          	lw	a4,4(a4)
    6194:	00e7a223          	sw	a4,4(a5)
    6198:	ffe007b7          	lui	a5,0xffe00
    619c:	10078713          	addi	a4,a5,256 # ffe00100 <__stack_top+0x2ff100>
    61a0:	0007a023          	sw	zero,0(a5)
    61a4:	00478793          	addi	a5,a5,4
    61a8:	fee79ce3          	bne	a5,a4,61a0 <main+0x128>
    61ac:	a201a023          	sw	zero,-1504(gp) # ffb00210 <_ZN7ckernel12cfg_state_idE>
    61b0:	ffef07b7          	lui	a5,0xffef0
    61b4:	2e07a423          	sw	zero,744(a5) # ffef02e8 <__stack_top+0x3ef2e8>
    61b8:	ffb12737          	lui	a4,0xffb12
    61bc:	1f072783          	lw	a5,496(a4) # ffb121f0 <__stack_top+0x111f0>
    61c0:	1f872603          	lw	a2,504(a4)
    61c4:	25878693          	addi	a3,a5,600
    61c8:	00f6b7b3          	sltu	a5,a3,a5
    61cc:	00c787b3          	add	a5,a5,a2
    61d0:	1f072583          	lw	a1,496(a4)
    61d4:	1f872603          	lw	a2,504(a4)
    61d8:	fef66ce3          	bltu	a2,a5,61d0 <main+0x158>
    61dc:	00c79463          	bne	a5,a2,61e4 <main+0x16c>
    61e0:	fed5e8e3          	bltu	a1,a3,61d0 <main+0x158>
    61e4:	00001b37          	lui	s6,0x1
    61e8:	9a0b4583          	lbu	a1,-1632(s6) # 9a0 <trisc.cc.12975e43+0x92>
    61ec:	000029b7          	lui	s3,0x2
    61f0:	010004b7          	lui	s1,0x1000
    61f4:	7ff98c13          	addi	s8,s3,2047 # 27ff <trisc.cc.12975e43+0x1ef1>
    61f8:	241c0c13          	addi	s8,s8,577
    61fc:	a0618a13          	addi	s4,gp,-1530 # ffb001f6 <_ZL19PERF_COUNTER_GROUPS+0x6>
    6200:	81018b93          	addi	s7,gp,-2032 # ffb00000 <CSWTCH.148>
    6204:	a4018d93          	addi	s11,gp,-1472 # ffb00230 <_ZN12_GLOBAL__N_1L20perf_counter_samplesE>
    6208:	a0b18ea3          	sb	a1,-1507(gp) # ffb0020d <my_logical_x_>
    620c:	9a1b4603          	lbu	a2,-1631(s6)
    6210:	fff48493          	addi	s1,s1,-1 # ffffff <__fw_export_text_end+0xff999f>
    6214:	a0c18e23          	sb	a2,-1508(gp) # ffb0020c <my_logical_y_>
    6218:	06000523          	sb	zero,106(zero) # 6a <trisc.cc.12975e43-0x8a4>
    621c:	06a04583          	lbu	a1,106(zero) # 6a <trisc.cc.12975e43-0x8a4>
    6220:	08000613          	li	a2,128
    6224:	00c58a63          	beq	a1,a2,6238 <main+0x1c0>
    6228:	0ff0000f          	fence
    622c:	06a04583          	lbu	a1,106(zero) # 6a <trisc.cc.12975e43-0x8a4>
    6230:	08000613          	li	a2,128
    6234:	fec59ae3          	bne	a1,a2,6228 <main+0x1b0>
    6238:	2c0000ef          	jal	64f8 <_ZN15kernel_profiler13init_profilerEttt.constprop.0>
    623c:	ffb12437          	lui	s0,0xffb12
    6240:	1f442603          	lw	a2,500(s0) # ffb121f4 <__stack_top+0x111f4>
    6244:	fffb0513          	addi	a0,s6,-1
    6248:	80e985b7          	lui	a1,0x80e98
    624c:	00a67633          	and	a2,a2,a0
    6250:	00b66633          	or	a2,a2,a1
    6254:	80cc2823          	sw	a2,-2032(s8)
    6258:	1f042503          	lw	a0,496(s0)
    625c:	00100a93          	li	s5,1
    6260:	80ac2a23          	sw	a0,-2028(s8)
    6264:	06c02303          	lw	t1,108(zero) # 6c <trisc.cc.12975e43-0x8a2>
    6268:	a1d1ce83          	lbu	t4,-1507(gp) # ffb0020d <my_logical_x_>
    626c:	a1c1ce03          	lbu	t3,-1508(gp) # ffb0020c <my_logical_y_>
    6270:	20632333          	sh1add	t1,t1,t1
    6274:	00531313          	slli	t1,t1,0x5
    6278:	00030513          	mv	a0,t1
    627c:	07032303          	lw	t1,112(t1)
    6280:	09255f83          	lhu	t6,146(a0)
    6284:	09455f03          	lhu	t5,148(a0)
    6288:	006f8fb3          	add	t6,t6,t1
    628c:	0cc54383          	lbu	t2,204(a0)
    6290:	a1f1ac23          	sw	t6,-1512(gp) # ffb00208 <rta_l1_base>
    6294:	0cd54283          	lbu	t0,205(a0)
    6298:	006f0f33          	add	t5,t5,t1
    629c:	a1e1aa23          	sw	t5,-1516(gp) # ffb00204 <crta_l1_base>
    62a0:	407e8eb3          	sub	t4,t4,t2
    62a4:	a1d188a3          	sb	t4,-1519(gp) # ffb00201 <my_relative_x_>
    62a8:	405e0e33          	sub	t3,t3,t0
    62ac:	a1c18823          	sb	t3,-1520(gp) # ffb00200 <my_relative_y_>
    62b0:	0a852503          	lw	a0,168(a0)
    62b4:	00042c23          	sw	zero,24(s0)
    62b8:	00042e23          	sw	zero,28(s0)
    62bc:	03542023          	sw	s5,32(s0)
    62c0:	02042023          	sw	zero,32(s0)
    62c4:	0e042823          	sw	zero,240(s0)
    62c8:	0e042a23          	sw	zero,244(s0)
    62cc:	0f542c23          	sw	s5,248(s0)
    62d0:	0e042c23          	sw	zero,248(s0)
    62d4:	00042623          	sw	zero,12(s0)
    62d8:	00042823          	sw	zero,16(s0)
    62dc:	01542a23          	sw	s5,20(s0)
    62e0:	00042a23          	sw	zero,20(s0)
    62e4:	21842e03          	lw	t3,536(s0)
    62e8:	00650533          	add	a0,a0,t1
    62ec:	fefe7313          	andi	t1,t3,-17
    62f0:	20642c23          	sw	t1,536(s0)
    62f4:	02042823          	sw	zero,48(s0)
    62f8:	02042a23          	sw	zero,52(s0)
    62fc:	03542c23          	sw	s5,56(s0)
    6300:	02042c23          	sw	zero,56(s0)
    6304:	21842303          	lw	t1,536(s0)
    6308:	01036313          	ori	t1,t1,16
    630c:	20642c23          	sw	t1,536(s0)
    6310:	02042823          	sw	zero,48(s0)
    6314:	02042a23          	sw	zero,52(s0)
    6318:	03542c23          	sw	s5,56(s0)
    631c:	02042c23          	sw	zero,56(s0)
    6320:	00042023          	sw	zero,0(s0)
    6324:	00042223          	sw	zero,4(s0)
    6328:	01542423          	sw	s5,8(s0)
    632c:	00042423          	sw	zero,8(s0)
    6330:	000500e7          	jalr	a0
    6334:	00200513          	li	a0,2
    6338:	02a42023          	sw	a0,32(s0)
    633c:	02042023          	sw	zero,32(s0)
    6340:	0ea42c23          	sw	a0,248(s0)
    6344:	0e042c23          	sw	zero,248(s0)
    6348:	00a42a23          	sw	a0,20(s0)
    634c:	00042a23          	sw	zero,20(s0)
    6350:	02a42c23          	sw	a0,56(s0)
    6354:	02042c23          	sw	zero,56(s0)
    6358:	02a42c23          	sw	a0,56(s0)
    635c:	02042c23          	sw	zero,56(s0)
    6360:	00a42423          	sw	a0,8(s0)
    6364:	00042423          	sw	zero,8(s0)
    6368:	a0018e93          	addi	t4,gp,-1536 # ffb001f0 <_ZL19PERF_COUNTER_GROUPS>
    636c:	00000293          	li	t0,0
    6370:	00500413          	li	s0,5
    6374:	00c0006f          	j	6380 <main+0x308>
    6378:	001e8e93          	addi	t4,t4,1
    637c:	0bda0263          	beq	s4,t4,6420 <main+0x3a8>
    6380:	000ec603          	lbu	a2,0(t4)
    6384:	fec46ae3          	bltu	s0,a2,6378 <main+0x300>
    6388:	217645b3          	sh2add	a1,a2,s7
    638c:	0005a583          	lw	a1,0(a1) # 80e98000 <__fw_export_text_end+0x80e919a0>
    6390:	fe0584e3          	beqz	a1,6378 <main+0x300>
    6394:	ffd60593          	addi	a1,a2,-3
    6398:	0ff5f593          	zext.b	a1,a1
    639c:	12bafc63          	bgeu	s5,a1,64d4 <main+0x45c>
    63a0:	217645b3          	sh2add	a1,a2,s7
    63a4:	0185a383          	lw	t2,24(a1)
    63a8:	fc0388e3          	beqz	t2,6378 <main+0x300>
    63ac:	0305a603          	lw	a2,48(a1)
    63b0:	21b2e833          	sh3add	a6,t0,s11
    63b4:	0485af03          	lw	t5,72(a1)
    63b8:	0605a503          	lw	a0,96(a1)
    63bc:	00000e13          	li	t3,0
    63c0:	00255303          	lhu	t1,2(a0)
    63c4:	00831313          	slli	t1,t1,0x8
    63c8:	00662223          	sw	t1,4(a2)
    63cc:	00462583          	lw	a1,4(a2)
    63d0:	feb31ee3          	bne	t1,a1,63cc <main+0x354>
    63d4:	06400593          	li	a1,100
    63d8:	00000013          	nop
    63dc:	fff58593          	addi	a1,a1,-1
    63e0:	fe059ce3          	bnez	a1,63d8 <main+0x360>
    63e4:	004f2f83          	lw	t6,4(t5)
    63e8:	000f2583          	lw	a1,0(t5)
    63ec:	00054303          	lbu	t1,0(a0)
    63f0:	001e0e13          	addi	t3,t3,1
    63f4:	01831313          	slli	t1,t1,0x18
    63f8:	0095f5b3          	and	a1,a1,s1
    63fc:	0065e5b3          	or	a1,a1,t1
    6400:	01f82023          	sw	t6,0(a6)
    6404:	00b82223          	sw	a1,4(a6)
    6408:	00450513          	addi	a0,a0,4
    640c:	00880813          	addi	a6,a6,8
    6410:	fbc398e3          	bne	t2,t3,63c0 <main+0x348>
    6414:	001e8e93          	addi	t4,t4,1
    6418:	007282b3          	add	t0,t0,t2
    641c:	f7da12e3          	bne	s4,t4,6380 <main+0x308>
    6420:	06028663          	beqz	t0,648c <main+0x414>
    6424:	a341a603          	lw	a2,-1484(gp) # ffb00224 <_ZN15kernel_profiler9stackSizeE>
    6428:	21b2e2b3          	sh3add	t0,t0,s11
    642c:	20000313          	li	t1,512
    6430:	a381a503          	lw	a0,-1480(gp) # ffb00228 <_ZN15kernel_profiler6wIndexE>
    6434:	40c30333          	sub	t1,t1,a2
    6438:	000d8593          	mv	a1,s11
    643c:	ffb12e37          	lui	t3,0xffb12
    6440:	fffb0393          	addi	t2,s6,-1
    6444:	b2382fb7          	lui	t6,0xb2382
    6448:	21354633          	sh2add	a2,a0,s3
    644c:	7ff60613          	addi	a2,a2,2047
    6450:	02657a63          	bgeu	a0,t1,6484 <main+0x40c>
    6454:	1f4e2803          	lw	a6,500(t3) # ffb121f4 <__stack_top+0x111f4>
    6458:	0005ae83          	lw	t4,0(a1)
    645c:	0045af03          	lw	t5,4(a1)
    6460:	00450513          	addi	a0,a0,4
    6464:	00787833          	and	a6,a6,t2
    6468:	01f86833          	or	a6,a6,t6
    646c:	a50620a3          	sw	a6,-1471(a2)
    6470:	1f0e2803          	lw	a6,496(t3)
    6474:	a2a1ac23          	sw	a0,-1480(gp) # ffb00228 <_ZN15kernel_profiler6wIndexE>
    6478:	a50622a3          	sw	a6,-1467(a2)
    647c:	a5e624a3          	sw	t5,-1463(a2)
    6480:	a5d626a3          	sw	t4,-1459(a2)
    6484:	00858593          	addi	a1,a1,8
    6488:	fcb290e3          	bne	t0,a1,6448 <main+0x3d0>
    648c:	00012623          	sw	zero,12(sp)
    6490:	00c12583          	lw	a1,12(sp)
    6494:	ffe80637          	lui	a2,0xffe80
    6498:	00b62223          	sw	a1,4(a2) # ffe80004 <__stack_top+0x37f004>
    649c:	00462603          	lw	a2,4(a2)
    64a0:	ffb125b7          	lui	a1,0xffb12
    64a4:	fffb0813          	addi	a6,s6,-1
    64a8:	90e98537          	lui	a0,0x90e98
    64ac:	00c12623          	sw	a2,12(sp)
    64b0:	06000523          	sb	zero,106(zero) # 6a <trisc.cc.12975e43-0x8a4>
    64b4:	1f45a603          	lw	a2,500(a1) # ffb121f4 <__stack_top+0x111f4>
    64b8:	01067633          	and	a2,a2,a6
    64bc:	00a66633          	or	a2,a2,a0
    64c0:	80cc2c23          	sw	a2,-2024(s8)
    64c4:	1f05a603          	lw	a2,496(a1)
    64c8:	80cc2e23          	sw	a2,-2020(s8)
    64cc:	054000ef          	jal	6520 <_ZN15kernel_profiler15finish_profilerEv>
    64d0:	d4dff06f          	j	621c <main+0x1a4>
    64d4:	ffb125b7          	lui	a1,0xffb12
    64d8:	2185a503          	lw	a0,536(a1) # ffb12218 <__stack_top+0x11218>
    64dc:	00300813          	li	a6,3
    64e0:	01056593          	ori	a1,a0,16
    64e4:	01061463          	bne	a2,a6,64ec <main+0x474>
    64e8:	fef57593          	andi	a1,a0,-17
    64ec:	ffb12537          	lui	a0,0xffb12
    64f0:	20b52c23          	sw	a1,536(a0) # ffb12218 <__stack_top+0x11218>
    64f4:	eadff06f          	j	63a0 <main+0x328>

000064f8 <_ZN15kernel_profiler13init_profilerEttt.constprop.0>:
    64f8:	a2c18713          	addi	a4,gp,-1492 # ffb0021c <_ZN15kernel_profiler6sumIDsE>
    64fc:	a2418793          	addi	a5,gp,-1500 # ffb00214 <_ZN15kernel_profiler4sumsE>
    6500:	00c00593          	li	a1,12
    6504:	00072023          	sw	zero,0(a4)
    6508:	00072223          	sw	zero,4(a4)
    650c:	0007a023          	sw	zero,0(a5)
    6510:	0007a223          	sw	zero,4(a5)
    6514:	a2b1ac23          	sw	a1,-1480(gp) # ffb00228 <_ZN15kernel_profiler6wIndexE>
    6518:	a201aa23          	sw	zero,-1484(gp) # ffb00224 <_ZN15kernel_profiler9stackSizeE>
    651c:	00008067          	ret

00006520 <_ZN15kernel_profiler15finish_profilerEv>:
    6520:	a2418793          	addi	a5,gp,-1500 # ffb00214 <_ZN15kernel_profiler4sumsE>
    6524:	0007a683          	lw	a3,0(a5)
    6528:	a381a703          	lw	a4,-1480(gp) # ffb00228 <_ZN15kernel_profiler6wIndexE>
    652c:	08069263          	bnez	a3,65b0 <_ZN15kernel_profiler15finish_profilerEv+0x90>
    6530:	0047a883          	lw	a7,4(a5)
    6534:	10089663          	bnez	a7,6640 <_ZN15kernel_profiler15finish_profilerEv+0x120>
    6538:	00377613          	andi	a2,a4,3
    653c:	04060c63          	beqz	a2,6594 <_ZN15kernel_profiler15finish_profilerEv+0x74>
    6540:	00000813          	li	a6,0
    6544:	00000693          	li	a3,0
    6548:	1ff00513          	li	a0,511
    654c:	000025b7          	lui	a1,0x2
    6550:	800008b7          	lui	a7,0x80000
    6554:	20b747b3          	sh2add	a5,a4,a1
    6558:	7ff78793          	addi	a5,a5,2047
    655c:	02e56663          	bltu	a0,a4,6588 <_ZN15kernel_profiler15finish_profilerEv+0x68>
    6560:	a517a0a3          	sw	a7,-1471(a5)
    6564:	00270713          	addi	a4,a4,2
    6568:	a407a2a3          	sw	zero,-1467(a5)
    656c:	00168693          	addi	a3,a3,1
    6570:	00377613          	andi	a2,a4,3
    6574:	02c6f663          	bgeu	a3,a2,65a0 <_ZN15kernel_profiler15finish_profilerEv+0x80>
    6578:	20b747b3          	sh2add	a5,a4,a1
    657c:	00100813          	li	a6,1
    6580:	7ff78793          	addi	a5,a5,2047
    6584:	fce57ee3          	bgeu	a0,a4,6560 <_ZN15kernel_profiler15finish_profilerEv+0x40>
    6588:	00168693          	addi	a3,a3,1
    658c:	fcc6e4e3          	bltu	a3,a2,6554 <_ZN15kernel_profiler15finish_profilerEv+0x34>
    6590:	00081863          	bnez	a6,65a0 <_ZN15kernel_profiler15finish_profilerEv+0x80>
    6594:	000017b7          	lui	a5,0x1
    6598:	9ee7a023          	sw	a4,-1568(a5) # 9e0 <trisc.cc.12975e43+0xd2>
    659c:	00008067          	ret
    65a0:	a2e1ac23          	sw	a4,-1480(gp) # ffb00228 <_ZN15kernel_profiler6wIndexE>
    65a4:	000017b7          	lui	a5,0x1
    65a8:	9ee7a023          	sw	a4,-1568(a5) # 9e0 <trisc.cc.12975e43+0xd2>
    65ac:	00008067          	ret
    65b0:	1ff00813          	li	a6,511
    65b4:	f8e862e3          	bltu	a6,a4,6538 <_ZN15kernel_profiler15finish_profilerEv+0x18>
    65b8:	a2c18513          	addi	a0,gp,-1492 # ffb0021c <_ZN15kernel_profiler6sumIDsE>
    65bc:	00052583          	lw	a1,0(a0)
    65c0:	00271613          	slli	a2,a4,0x2
    65c4:	0ffff8b7          	lui	a7,0xffff
    65c8:	00c59593          	slli	a1,a1,0xc
    65cc:	7ff60613          	addi	a2,a2,2047
    65d0:	0115f5b3          	and	a1,a1,a7
    65d4:	a0000e37          	lui	t3,0xa0000
    65d8:	000028b7          	lui	a7,0x2
    65dc:	24160613          	addi	a2,a2,577
    65e0:	01160633          	add	a2,a2,a7
    65e4:	01c5e5b3          	or	a1,a1,t3
    65e8:	80b62023          	sw	a1,-2048(a2)
    65ec:	0047a883          	lw	a7,4(a5)
    65f0:	80d62223          	sw	a3,-2044(a2)
    65f4:	00270713          	addi	a4,a4,2
    65f8:	04088063          	beqz	a7,6638 <_ZN15kernel_profiler15finish_profilerEv+0x118>
    65fc:	02e86e63          	bltu	a6,a4,6638 <_ZN15kernel_profiler15finish_profilerEv+0x118>
    6600:	00452683          	lw	a3,4(a0)
    6604:	00271793          	slli	a5,a4,0x2
    6608:	0ffff637          	lui	a2,0xffff
    660c:	00c69693          	slli	a3,a3,0xc
    6610:	7ff78793          	addi	a5,a5,2047
    6614:	00c6f6b3          	and	a3,a3,a2
    6618:	a00005b7          	lui	a1,0xa0000
    661c:	24178793          	addi	a5,a5,577
    6620:	00002637          	lui	a2,0x2
    6624:	00c787b3          	add	a5,a5,a2
    6628:	00b6e6b3          	or	a3,a3,a1
    662c:	80d7a023          	sw	a3,-2048(a5)
    6630:	00270713          	addi	a4,a4,2
    6634:	8117a223          	sw	a7,-2044(a5)
    6638:	a2e1ac23          	sw	a4,-1480(gp) # ffb00228 <_ZN15kernel_profiler6wIndexE>
    663c:	efdff06f          	j	6538 <_ZN15kernel_profiler15finish_profilerEv+0x18>
    6640:	1ff00793          	li	a5,511
    6644:	eee7eae3          	bltu	a5,a4,6538 <_ZN15kernel_profiler15finish_profilerEv+0x18>
    6648:	a2c18513          	addi	a0,gp,-1492 # ffb0021c <_ZN15kernel_profiler6sumIDsE>
    664c:	fb5ff06f          	j	6600 <_ZN15kernel_profiler15finish_profilerEv+0xe0>

00006650 <exit>:
    6650:	0000006f          	j	6650 <exit>
