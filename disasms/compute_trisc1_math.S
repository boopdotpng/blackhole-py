
/tmp/tt-disasm-1g556x35/out.elf:     file format elf32-littleriscv


Disassembly of section .text:

00006290 <_start>:
    6290:	ff010113          	addi	sp,sp,-16
    6294:	ffb007b7          	lui	a5,0xffb00
    6298:	ffb00737          	lui	a4,0xffb00
    629c:	03078793          	addi	a5,a5,48 # ffb00030 <__ldm_bss_end+0x10>
    62a0:	02070713          	addi	a4,a4,32 # ffb00020 <__ldm_bss_end>
    62a4:	00f76e63          	bltu	a4,a5,62c0 <.L4>

000062a8 <.L5>:
    62a8:	fe07ae23          	sw	zero,-4(a5)
    62ac:	fe07ac23          	sw	zero,-8(a5)
    62b0:	fe07aa23          	sw	zero,-12(a5)
    62b4:	fe07a823          	sw	zero,-16(a5)
    62b8:	01078793          	addi	a5,a5,16
    62bc:	fef776e3          	bgeu	a4,a5,62a8 <.L5>

000062c0 <.L4>:
    62c0:	ff878693          	addi	a3,a5,-8
    62c4:	30d76463          	bltu	a4,a3,65cc <.L21>
    62c8:	fe07aa23          	sw	zero,-12(a5)
    62cc:	fe07a823          	sw	zero,-16(a5)

000062d0 <.L6>:
    62d0:	ffc78693          	addi	a3,a5,-4
    62d4:	00d76463          	bltu	a4,a3,62dc <.L7>
    62d8:	fe07ac23          	sw	zero,-8(a5)

000062dc <.L7>:
    62dc:	00006737          	lui	a4,0x6
    62e0:	ffb007b7          	lui	a5,0xffb00
    62e4:	64470713          	addi	a4,a4,1604 # 6644 <__kernel_data_lma>
    62e8:	02078793          	addi	a5,a5,32 # ffb00020 <__ldm_bss_end>
    62ec:	06f70263          	beq	a4,a5,6350 <.L9>
    62f0:	ffb00637          	lui	a2,0xffb00
    62f4:	02060613          	addi	a2,a2,32 # ffb00020 <__ldm_bss_end>
    62f8:	40f60633          	sub	a2,a2,a5
    62fc:	00800593          	li	a1,8
    6300:	40265693          	srai	a3,a2,0x2
    6304:	02c5d863          	bge	a1,a2,6334 <.L10>
    6308:	00200813          	li	a6,2

0000630c <.L11>:
    630c:	00072503          	lw	a0,0(a4)
    6310:	00472583          	lw	a1,4(a4)
    6314:	00872603          	lw	a2,8(a4)
    6318:	00c70713          	addi	a4,a4,12
    631c:	00c78793          	addi	a5,a5,12
    6320:	ffd68693          	addi	a3,a3,-3
    6324:	fea7aa23          	sw	a0,-12(a5)
    6328:	feb7ac23          	sw	a1,-8(a5)
    632c:	fec7ae23          	sw	a2,-4(a5)
    6330:	fcd84ee3          	blt	a6,a3,630c <.L11>

00006334 <.L10>:
    6334:	00d05e63          	blez	a3,6350 <.L9>
    6338:	00072583          	lw	a1,0(a4)
    633c:	00200613          	li	a2,2
    6340:	00b7a023          	sw	a1,0(a5)
    6344:	00c69663          	bne	a3,a2,6350 <.L9>
    6348:	00472703          	lw	a4,4(a4)
    634c:	00e7a223          	sw	a4,4(a5)

00006350 <.L9>:
    6350:	3a002703          	lw	a4,928(zero) # 3a0 <_start-0x5ef0>
    6354:	08000693          	li	a3,128
    6358:	00271713          	slli	a4,a4,0x2
    635c:	37374783          	lbu	a5,883(a4)
    6360:	06070713          	addi	a4,a4,96
    6364:	00d78863          	beq	a5,a3,6374 <.L15>

00006368 <.L13>:
    6368:	0ff0000f          	fence
    636c:	31374783          	lbu	a5,787(a4)
    6370:	fed79ce3          	bne	a5,a3,6368 <.L13>

00006374 <.L15>:
    6374:	c8340002          	ttsetc16	13,0
    6378:	c8740002          	ttsetc16	29,0
    637c:	c8c00002          	ttsetc16	48,0
    6380:	ffe406b7          	lui	a3,0xffe40
    6384:	ffb007b7          	lui	a5,0xffb00
    6388:	0107a783          	lw	a5,16(a5) # ffb00010 <rta_l1_base>
    638c:	00068693          	mv	a3,a3
    6390:	10184737          	lui	a4,0x10184
    6394:	00e6a023          	sw	a4,0(a3) # ffe40000 <__instrn_buffer>
    6398:	0007a803          	lw	a6,0(a5)
    639c:	c83c0002          	ttsetc16	15,0
    63a0:	c87c0002          	ttsetc16	31,0
    63a4:	c8c80002          	ttsetc16	50,0
    63a8:	c8300006          	ttsetc16	12,1
    63ac:	c8700006          	ttsetc16	28,1
    63b0:	c8bc0002          	ttsetc16	47,0
    63b4:	c8380022          	ttsetc16	14,8
    63b8:	c8780022          	ttsetc16	30,8
    63bc:	c8c40002          	ttsetc16	49,0
    63c0:	00012423          	sw	zero,8(sp)
    63c4:	00812783          	lw	a5,8(sp)
    63c8:	ffe80737          	lui	a4,0xffe80
    63cc:	00f72423          	sw	a5,8(a4) # ffe80008 <__instrn_buffer+0x40008>
    63d0:	00872503          	lw	a0,8(a4)
    63d4:	ffb807b7          	lui	a5,0xffb80
    63d8:	00400593          	li	a1,4
    63dc:	00200613          	li	a2,2
    63e0:	00a12423          	sw	a0,8(sp)
    63e4:	00b7a023          	sw	a1,0(a5) # ffb80000 <__stack_top+0x7f000>
    63e8:	00c7a223          	sw	a2,4(a5)
    63ec:	020005b7          	lui	a1,0x2000
    63f0:	37c00637          	lui	a2,0x37c00
    63f4:	00b7a423          	sw	a1,8(a5)
    63f8:	00360613          	addi	a2,a2,3 # 37c00003 <__kernel_data_lma+0x37bf99bf>
    63fc:	00c7a623          	sw	a2,12(a5)
    6400:	00b7a823          	sw	a1,16(a5)
    6404:	1200a637          	lui	a2,0x1200a
    6408:	00c7aa23          	sw	a2,20(a5)
    640c:	00b7ac23          	sw	a1,24(a5)
    6410:	00c7ae23          	sw	a2,28(a5)
    6414:	02c7a023          	sw	a2,32(a5)
    6418:	c81c0002          	ttsetc16	7,0
    641c:	dc00003c          	ttsetrwc	0,0,0,0,0,15
    6420:	00012223          	sw	zero,4(sp)
    6424:	00412783          	lw	a5,4(sp)
    6428:	00f72223          	sw	a5,4(a4)
    642c:	00472783          	lw	a5,4(a4)
    6430:	00f12223          	sw	a5,4(sp)

00006434 <.L14>:
    6434:	02472783          	lw	a5,36(a4)
    6438:	0ff7f793          	zext.b	a5,a5
    643c:	fe079ce3          	bnez	a5,6434 <.L14>
    6440:	8c800022          	ttseminit	2,0,2
    6444:	b2010537          	lui	a0,0xb2010
    6448:	b30817b7          	lui	a5,0xb3081
    644c:	00a6a023          	sw	a0,0(a3)
    6450:	8dc78793          	addi	a5,a5,-1828 # b30808dc <__kernel_data_lma+0xb307a298>
    6454:	00f6a023          	sw	a5,0(a3)
    6458:	ffb005b7          	lui	a1,0xffb00
    645c:	0005a023          	sw	zero,0(a1) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    6460:	89000042          	ttstallwait	128,16
    6464:	b68007b7          	lui	a5,0xb6800
    6468:	00178793          	addi	a5,a5,1 # b6800001 <__kernel_data_lma+0xb67f99bd>
    646c:	00f6a023          	sw	a5,0(a3)
    6470:	c83c0002          	ttsetc16	15,0
    6474:	c87c0002          	ttsetc16	31,0
    6478:	c8c80002          	ttsetc16	50,0
    647c:	c8300006          	ttsetc16	12,1
    6480:	c8700006          	ttsetc16	28,1
    6484:	c8bc0002          	ttsetc16	47,0
    6488:	c8380022          	ttsetc16	14,8
    648c:	c8780022          	ttsetc16	30,8
    6490:	c8c40002          	ttsetc16	49,0
    6494:	00012623          	sw	zero,12(sp)
    6498:	00c12603          	lw	a2,12(sp)
    649c:	ffb807b7          	lui	a5,0xffb80
    64a0:	00c72423          	sw	a2,8(a4)
    64a4:	00872303          	lw	t1,8(a4)
    64a8:	00400893          	li	a7,4
    64ac:	00200713          	li	a4,2
    64b0:	02000637          	lui	a2,0x2000
    64b4:	00612623          	sw	t1,12(sp)
    64b8:	0117a023          	sw	a7,0(a5) # ffb80000 <__stack_top+0x7f000>
    64bc:	00e7a223          	sw	a4,4(a5)
    64c0:	37c00737          	lui	a4,0x37c00
    64c4:	00c7a423          	sw	a2,8(a5)
    64c8:	00370713          	addi	a4,a4,3 # 37c00003 <__kernel_data_lma+0x37bf99bf>
    64cc:	00e7a623          	sw	a4,12(a5)
    64d0:	00c7a823          	sw	a2,16(a5)
    64d4:	1200a737          	lui	a4,0x1200a
    64d8:	00e7aa23          	sw	a4,20(a5)
    64dc:	00c7ac23          	sw	a2,24(a5)
    64e0:	00e7ae23          	sw	a4,28(a5)
    64e4:	02e7a023          	sw	a4,32(a5)
    64e8:	c81c0002          	ttsetc16	7,0
    64ec:	dc00003c          	ttsetrwc	0,0,0,0,0,15
    64f0:	c4280001          	sfploadi	L0,0,10
    64f4:	c4200001          	sfploadi	L0,0,8
    64f8:	440003c2          	sfpconfig	15,0,0
    64fc:	c84c0002          	ttsetc16	19,0
    6500:	c88c0002          	ttsetc16	35,0
    6504:	c8d80002          	ttsetc16	54,0
    6508:	dc00003c          	ttsetrwc	0,0,0,0,0,15
    650c:	0a080a63          	beqz	a6,65c0 <.L30>
    6510:	0005a703          	lw	a4,0(a1)
    6514:	00000613          	li	a2,0
    6518:	00100893          	li	a7,1

0000651c <.L18>:
    651c:	9a84002a          	ttsemwait	322,2,2
    6520:	00e03733          	snez	a4,a4
    6524:	00971713          	slli	a4,a4,0x9
    6528:	00a70733          	add	a4,a4,a0
    652c:	00e6a023          	sw	a4,0(a3)
    6530:	06000000          	ttmop	1,0,0
    6534:	dc000010          	ttsetrwc	0,0,0,0,0,4
    6538:	00e6a023          	sw	a4,0(a3)
    653c:	8a000042          	ttstallwait	256,16
    6540:	00400793          	li	a5,4

00006544 <.L17>:
    6544:	1000014c          	ttreplay	0,5,1,1
    6548:	c0038001          	sfpload	L0,0,0,7
    654c:	d4fe0001          	sfpaddi	L0,16256,0
    6550:	3c000002          	sfpnop
    6554:	c8038001          	sfpstore	L0,0,0,7
    6558:	e0020000          	ttincrwc	0,2,0,0
    655c:	10000140          	ttreplay	0,5,0,0
    6560:	10000140          	ttreplay	0,5,0,0
    6564:	10000140          	ttreplay	0,5,0,0
    6568:	10000140          	ttreplay	0,5,0,0
    656c:	10000140          	ttreplay	0,5,0,0
    6570:	10000140          	ttreplay	0,5,0,0
    6574:	10000140          	ttreplay	0,5,0,0
    6578:	dc480010          	ttsetrwc	0,4,8,0,0,4
    657c:	dc480010          	ttsetrwc	0,4,8,0,0,4
    6580:	fff78793          	addi	a5,a5,-1
    6584:	fc0790e3          	bnez	a5,6544 <.L17>
    6588:	dc000010          	ttsetrwc	0,0,0,0,0,4
    658c:	88042042          	ttstallwait	2,2064
    6590:	90000022          	ttsempost	2
    6594:	0005a783          	lw	a5,0(a1)
    6598:	40f88733          	sub	a4,a7,a5
    659c:	00e5a023          	sw	a4,0(a1)
    65a0:	89002042          	ttstallwait	128,2064
    65a4:	fff78793          	addi	a5,a5,-1
    65a8:	00f037b3          	snez	a5,a5
    65ac:	00979793          	slli	a5,a5,0x9
    65b0:	00a787b3          	add	a5,a5,a0
    65b4:	00f6a023          	sw	a5,0(a3)
    65b8:	00160613          	addi	a2,a2,1 # 2000001 <__kernel_data_lma+0x1ff99bd>
    65bc:	f6c810e3          	bne	a6,a2,651c <.L18>

000065c0 <.L30>:
    65c0:	00000513          	li	a0,0
    65c4:	01010113          	addi	sp,sp,16
    65c8:	00008067          	ret

000065cc <.L21>:
    65cc:	00068793          	mv	a5,a3
    65d0:	d01ff06f          	j	62d0 <.L6>

000065d4 <_ZN7ckernel4sfpu27calculate_binop_with_scalarILb0ELi0ELi8EEEvm>:
    65d4:	710a07b7          	lui	a5,0x710a0
    65d8:	080546b3          	zext.h	a3,a0
    65dc:	00f686b3          	add	a3,a3,a5
    65e0:	ffe407b7          	lui	a5,0xffe40
    65e4:	00078793          	mv	a5,a5
    65e8:	71080737          	lui	a4,0x71080
    65ec:	00d7a023          	sw	a3,0(a5) # ffe40000 <__instrn_buffer>
    65f0:	01055513          	srli	a0,a0,0x10
    65f4:	00e50533          	add	a0,a0,a4
    65f8:	00a7a023          	sw	a0,0(a5)
    65fc:	1000014c          	ttreplay	0,5,1,1
    6600:	c0438001          	sfpload	L1,0,0,7
    6604:	14284042          	sfpadd	L1,L10,L1,L0,0
    6608:	3c000002          	sfpnop
    660c:	c8438001          	sfpstore	L1,0,0,7
    6610:	e0020000          	ttincrwc	0,2,0,0
    6614:	10000140          	ttreplay	0,5,0,0
    6618:	10000140          	ttreplay	0,5,0,0
    661c:	10000140          	ttreplay	0,5,0,0
    6620:	10000140          	ttreplay	0,5,0,0
    6624:	10000140          	ttreplay	0,5,0,0
    6628:	10000140          	ttreplay	0,5,0,0
    662c:	c0438001          	sfpload	L1,0,0,7
    6630:	14284002          	sfpadd	L0,L10,L1,L0,0
    6634:	3c000002          	sfpnop
    6638:	c8038001          	sfpstore	L0,0,0,7
    663c:	e0020000          	ttincrwc	0,2,0,0
    6640:	00008067          	ret
