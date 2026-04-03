
/tmp/tt-disasm-w99w58kp/out.elf:     file format elf32-littleriscv


Disassembly of section .text:

00006660 <_start>:
    6660:	ffb007b7          	lui	a5,0xffb00
    6664:	ffb00737          	lui	a4,0xffb00
    6668:	53078793          	addi	a5,a5,1328 # ffb00530 <__ldm_bss_end+0x10>
    666c:	52070713          	addi	a4,a4,1312 # ffb00520 <__ldm_bss_end>
    6670:	00f76e63          	bltu	a4,a5,668c <.L2>

00006674 <.L3>:
    6674:	fe07ae23          	sw	zero,-4(a5)
    6678:	fe07ac23          	sw	zero,-8(a5)
    667c:	fe07aa23          	sw	zero,-12(a5)
    6680:	fe07a823          	sw	zero,-16(a5)
    6684:	01078793          	addi	a5,a5,16
    6688:	fef776e3          	bgeu	a4,a5,6674 <.L3>

0000668c <.L2>:
    668c:	ff878693          	addi	a3,a5,-8
    6690:	12d76263          	bltu	a4,a3,67b4 <.L14>
    6694:	fe07aa23          	sw	zero,-12(a5)
    6698:	fe07a823          	sw	zero,-16(a5)

0000669c <.L4>:
    669c:	ffc78693          	addi	a3,a5,-4
    66a0:	00d76463          	bltu	a4,a3,66a8 <.L5>
    66a4:	fe07ac23          	sw	zero,-8(a5)

000066a8 <.L5>:
    66a8:	00006737          	lui	a4,0x6
    66ac:	ffb007b7          	lui	a5,0xffb00
    66b0:	7bc70713          	addi	a4,a4,1980 # 67bc <__kernel_data_lma>
    66b4:	52078793          	addi	a5,a5,1312 # ffb00520 <__ldm_bss_end>
    66b8:	06f70263          	beq	a4,a5,671c <.L7>
    66bc:	ffb00637          	lui	a2,0xffb00
    66c0:	52060613          	addi	a2,a2,1312 # ffb00520 <__ldm_bss_end>
    66c4:	40f60633          	sub	a2,a2,a5
    66c8:	00800593          	li	a1,8
    66cc:	40265693          	srai	a3,a2,0x2
    66d0:	02c5d863          	bge	a1,a2,6700 <.L8>
    66d4:	00200813          	li	a6,2

000066d8 <.L9>:
    66d8:	00072503          	lw	a0,0(a4)
    66dc:	00472583          	lw	a1,4(a4)
    66e0:	00872603          	lw	a2,8(a4)
    66e4:	00c70713          	addi	a4,a4,12
    66e8:	00c78793          	addi	a5,a5,12
    66ec:	ffd68693          	addi	a3,a3,-3
    66f0:	fea7aa23          	sw	a0,-12(a5)
    66f4:	feb7ac23          	sw	a1,-8(a5)
    66f8:	fec7ae23          	sw	a2,-4(a5)
    66fc:	fcd84ee3          	blt	a6,a3,66d8 <.L9>

00006700 <.L8>:
    6700:	00d05e63          	blez	a3,671c <.L7>
    6704:	00072583          	lw	a1,0(a4)
    6708:	00200613          	li	a2,2
    670c:	00b7a023          	sw	a1,0(a5)
    6710:	00c69663          	bne	a3,a2,671c <.L7>
    6714:	00472703          	lw	a4,4(a4)
    6718:	00e7a223          	sw	a4,4(a5)

0000671c <.L7>:
    671c:	3a002703          	lw	a4,928(zero) # 3a0 <_start-0x62c0>
    6720:	08000693          	li	a3,128
    6724:	00271713          	slli	a4,a4,0x2
    6728:	37374783          	lbu	a5,883(a4)
    672c:	06070713          	addi	a4,a4,96
    6730:	00d78863          	beq	a5,a3,6740 <.L11>

00006734 <.L12>:
    6734:	0ff0000f          	fence
    6738:	31374783          	lbu	a5,787(a4)
    673c:	fed79ce3          	bne	a5,a3,6734 <.L12>

00006740 <.L11>:
    6740:	ffb126b7          	lui	a3,0xffb12
    6744:	1f46a703          	lw	a4,500(a3) # ffb121f4 <__stack_top+0x111f4>
    6748:	00001637          	lui	a2,0x1
    674c:	fff60613          	addi	a2,a2,-1 # fff <_start-0x5661>
    6750:	000027b7          	lui	a5,0x2
    6754:	7ff78793          	addi	a5,a5,2047 # 27ff <_start-0x3e61>
    6758:	00c77733          	and	a4,a4,a2
    675c:	8878f5b7          	lui	a1,0x8878f
    6760:	00b76733          	or	a4,a4,a1
    6764:	a6e7a0a3          	sw	a4,-1439(a5)
    6768:	1f06a703          	lw	a4,496(a3)
    676c:	24178793          	addi	a5,a5,577
    6770:	82e7a223          	sw	a4,-2012(a5)
    6774:	c8340002          	ttsetc16	13,0
    6778:	c8740002          	ttsetc16	29,0
    677c:	c8c00002          	ttsetc16	48,0
    6780:	ffe40737          	lui	a4,0xffe40
    6784:	00070713          	mv	a4,a4
    6788:	101845b7          	lui	a1,0x10184
    678c:	00b72023          	sw	a1,0(a4) # ffe40000 <__instrn_buffer>
    6790:	1f46a703          	lw	a4,500(a3)
    6794:	9878f5b7          	lui	a1,0x9878f
    6798:	00000513          	li	a0,0
    679c:	00c77733          	and	a4,a4,a2
    67a0:	00b76733          	or	a4,a4,a1
    67a4:	82e7a423          	sw	a4,-2008(a5)
    67a8:	1f06a703          	lw	a4,496(a3)
    67ac:	82e7a623          	sw	a4,-2004(a5)
    67b0:	00008067          	ret

000067b4 <.L14>:
    67b4:	00068793          	mv	a5,a3
    67b8:	ee5ff06f          	j	669c <.L4>
