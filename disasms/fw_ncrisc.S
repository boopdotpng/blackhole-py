
/tmp/tt-disasm-0z85j6d9/out.elf:     file format elf32-littleriscv


Disassembly of section .text:

00005440 <_start>:
    5440:	ffb001b7          	lui	gp,0xffb00
    5444:	7f018193          	addi	gp,gp,2032 # ffb007f0 <__global_pointer$>
    5448:	ffb02137          	lui	sp,0xffb02
    544c:	ff010113          	addi	sp,sp,-16 # ffb01ff0 <__fw_export_ldm_end+0x1780>
    5450:	00810513          	addi	a0,sp,8
    5454:	00a12023          	sw	a0,0(sp)
    5458:	00012223          	sw	zero,4(sp)
    545c:	00912423          	sw	s1,8(sp)
    5460:	00012623          	sw	zero,12(sp)
    5464:	00100513          	li	a0,1
    5468:	00010593          	mv	a1,sp
    546c:	00000613          	li	a2,0
    5470:	008000ef          	jal	5478 <main>
    5474:	4000006f          	j	5874 <exit>

00005478 <main>:
    5478:	fd010113          	addi	sp,sp,-48
    547c:	02112623          	sw	ra,44(sp)
    5480:	02812423          	sw	s0,40(sp)
    5484:	02912223          	sw	s1,36(sp)
    5488:	03212023          	sw	s2,32(sp)
    548c:	01312e23          	sw	s3,28(sp)
    5490:	01412c23          	sw	s4,24(sp)
    5494:	01512a23          	sw	s5,20(sp)
    5498:	01612823          	sw	s6,16(sp)
    549c:	01712623          	sw	s7,12(sp)
    54a0:	01812423          	sw	s8,8(sp)
    54a4:	01912223          	sw	s9,4(sp)
    54a8:	00200313          	li	t1,2
    54ac:	7c032073          	csrs	0x7c0,t1
    54b0:	00100313          	li	t1,1
    54b4:	01231313          	slli	t1,t1,0x12
    54b8:	0ff0000f          	fence
    54bc:	7c032073          	csrs	0x7c0,t1
    54c0:	00200313          	li	t1,2
    54c4:	7c033073          	csrc	0x7c0,t1
    54c8:	0ff0000f          	fence
    54cc:	0ff0000f          	fence
    54d0:	00800313          	li	t1,8
    54d4:	7c032073          	csrs	0x7c0,t1
    54d8:	ffb007b7          	lui	a5,0xffb00
    54dc:	ffb01737          	lui	a4,0xffb01
    54e0:	01478793          	addi	a5,a5,20 # ffb00014 <noc_nonposted_writes_acked>
    54e4:	86470713          	addi	a4,a4,-1948 # ffb00864 <__ldm_bss_end>
    54e8:	12f77e63          	bgeu	a4,a5,5624 <main+0x1ac>
    54ec:	ff878693          	addi	a3,a5,-8
    54f0:	00d76863          	bltu	a4,a3,5500 <main+0x88>
    54f4:	fe07aa23          	sw	zero,-12(a5)
    54f8:	fe07a823          	sw	zero,-16(a5)
    54fc:	00078693          	mv	a3,a5
    5500:	ffc68793          	addi	a5,a3,-4
    5504:	00f76463          	bltu	a4,a5,550c <main+0x94>
    5508:	fe06ac23          	sw	zero,-8(a3)
    550c:	0000a5b7          	lui	a1,0xa
    5510:	81018513          	addi	a0,gp,-2032 # ffb00000 <_ZL10ncrisc_run>
    5514:	6b058593          	addi	a1,a1,1712 # a6b0 <__fw_export_text_end+0x4e30>
    5518:	00b50c63          	beq	a0,a1,5530 <main+0xb8>
    551c:	ffb00637          	lui	a2,0xffb00
    5520:	00460613          	addi	a2,a2,4 # ffb00004 <noc_reads_num_issued>
    5524:	40a60633          	sub	a2,a2,a0
    5528:	40265613          	srai	a2,a2,0x2
    552c:	2fc000ef          	jal	5828 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    5530:	85018413          	addi	s0,gp,-1968 # ffb00040 <dram_bank_to_noc_xy>
    5534:	000114b7          	lui	s1,0x11
    5538:	6b048593          	addi	a1,s1,1712 # 116b0 <__fw_export_text_end+0xbe30>
    553c:	00700613          	li	a2,7
    5540:	00040513          	mv	a0,s0
    5544:	2e4000ef          	jal	5828 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    5548:	6cc48593          	addi	a1,s1,1740
    554c:	07800613          	li	a2,120
    5550:	01c40513          	addi	a0,s0,28
    5554:	2d4000ef          	jal	5828 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    5558:	000124b7          	lui	s1,0x12
    555c:	8ac48593          	addi	a1,s1,-1876 # 118ac <__fw_export_text_end+0xc02c>
    5560:	00700613          	li	a2,7
    5564:	1fc40513          	addi	a0,s0,508
    5568:	2c0000ef          	jal	5828 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    556c:	8c848593          	addi	a1,s1,-1848
    5570:	07800613          	li	a2,120
    5574:	21840513          	addi	a0,s0,536
    5578:	2b0000ef          	jal	5828 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    557c:	06000a13          	li	s4,96
    5580:	eb048593          	addi	a1,s1,-336
    5584:	00500613          	li	a2,5
    5588:	3f840513          	addi	a0,s0,1016
    558c:	29c000ef          	jal	5828 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    5590:	00300613          	li	a2,3
    5594:	ec448593          	addi	a1,s1,-316
    5598:	40c40513          	addi	a0,s0,1036
    559c:	28c000ef          	jal	5828 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    55a0:	ffb207b7          	lui	a5,0xffb20
    55a4:	1487a783          	lw	a5,328(a5) # ffb20148 <__stack_top+0x1e148>
    55a8:	03f7f713          	andi	a4,a5,63
    55ac:	0067d793          	srli	a5,a5,0x6
    55b0:	84e18023          	sb	a4,-1984(gp) # ffb00030 <my_x>
    55b4:	03f7f793          	andi	a5,a5,63
    55b8:	82f18e23          	sb	a5,-1988(gp) # ffb0002c <my_y>
    55bc:	ffb307b7          	lui	a5,0xffb30
    55c0:	1487a783          	lw	a5,328(a5) # ffb30148 <__stack_top+0x2e148>
    55c4:	83c18713          	addi	a4,gp,-1988 # ffb0002c <my_y>
    55c8:	03f7f613          	andi	a2,a5,63
    55cc:	0067d793          	srli	a5,a5,0x6
    55d0:	03f7f793          	andi	a5,a5,63
    55d4:	84018693          	addi	a3,gp,-1984 # ffb00030 <my_x>
    55d8:	00f700a3          	sb	a5,1(a4)
    55dc:	00c680a3          	sb	a2,1(a3)
    55e0:	000017b7          	lui	a5,0x1
    55e4:	9a07c703          	lbu	a4,-1632(a5) # 9a0 <_start-0x4aa0>
    55e8:	06078793          	addi	a5,a5,96
    55ec:	42440a93          	addi	s5,s0,1060
    55f0:	84e186a3          	sb	a4,-1971(gp) # ffb0003d <my_logical_x_>
    55f4:	9417c783          	lbu	a5,-1727(a5)
    55f8:	84f18623          	sb	a5,-1972(gp) # ffb0003c <my_logical_y_>
    55fc:	8101a483          	lw	s1,-2032(gp) # ffb00000 <_ZL10ncrisc_run>
    5600:	00048023          	sb	zero,0(s1)
    5604:	0004c783          	lbu	a5,0(s1)
    5608:	0ff7f713          	zext.b	a4,a5
    560c:	f8078793          	addi	a5,a5,-128
    5610:	02078663          	beqz	a5,563c <main+0x1c4>
    5614:	fff70793          	addi	a5,a4,-1
    5618:	02078263          	beqz	a5,563c <main+0x1c4>
    561c:	0ff0000f          	fence
    5620:	fe5ff06f          	j	5604 <main+0x18c>
    5624:	fe07ae23          	sw	zero,-4(a5)
    5628:	fe07ac23          	sw	zero,-8(a5)
    562c:	fe07aa23          	sw	zero,-12(a5)
    5630:	fe07a823          	sw	zero,-16(a5)
    5634:	01078793          	addi	a5,a5,16
    5638:	eb1ff06f          	j	54e8 <main+0x70>
    563c:	06c02583          	lw	a1,108(zero) # 6c <_start-0x53d4>
    5640:	06c02783          	lw	a5,108(zero) # 6c <_start-0x53d4>
    5644:	000a8513          	mv	a0,s5
    5648:	034585b3          	mul	a1,a1,s4
    564c:	034787b3          	mul	a5,a5,s4
    5650:	07058593          	addi	a1,a1,112
    5654:	0707a303          	lw	t1,112(a5)
    5658:	07c7d703          	lhu	a4,124(a5)
    565c:	0747a683          	lw	a3,116(a5)
    5660:	06078793          	addi	a5,a5,96
    5664:	00670733          	add	a4,a4,t1
    5668:	40e42c23          	sw	a4,1048(s0)
    566c:	01e7d703          	lhu	a4,30(a5)
    5670:	00d70733          	add	a4,a4,a3
    5674:	40e42e23          	sw	a4,1052(s0)
    5678:	0187a683          	lw	a3,24(a5)
    567c:	0207d703          	lhu	a4,32(a5)
    5680:	00d70733          	add	a4,a4,a3
    5684:	42e42023          	sw	a4,1056(s0)
    5688:	02a7d703          	lhu	a4,42(a5)
    568c:	02c7d783          	lhu	a5,44(a5)
    5690:	0305ae03          	lw	t3,48(a1)
    5694:	00670733          	add	a4,a4,t1
    5698:	006787b3          	add	a5,a5,t1
    569c:	84f1a223          	sw	a5,-1980(gp) # ffb00034 <crta_l1_base>
    56a0:	0125d783          	lhu	a5,18(a1)
    56a4:	84e1a423          	sw	a4,-1976(gp) # ffb00038 <rta_l1_base>
    56a8:	006787b3          	add	a5,a5,t1
    56ac:	0405a703          	lw	a4,64(a1)
    56b0:	0580006f          	j	5708 <.NO_CB223+0xc>
    56b4:	0047a683          	lw	a3,4(a5)
    56b8:	0007a603          	lw	a2,0(a5)
    56bc:	0087a803          	lw	a6,8(a5)
    56c0:	00c7a883          	lw	a7,12(a5)
    56c4:	00175713          	srli	a4,a4,0x1
    56c8:	00177293          	andi	t0,a4,1
    56cc:	00052c23          	sw	zero,24(a0)
    56d0:	01078793          	addi	a5,a5,16
    56d4:	00d52023          	sw	a3,0(a0)
    56d8:	00d606b3          	add	a3,a2,a3
    56dc:	00d52223          	sw	a3,4(a0)
    56e0:	00c52a23          	sw	a2,20(a0)
    56e4:	01052623          	sw	a6,12(a0)
    56e8:	00c52823          	sw	a2,16(a0)
    56ec:	01152423          	sw	a7,8(a0)
    56f0:	02050513          	addi	a0,a0,32
    56f4:	fc0290e3          	bnez	t0,56b4 <main+0x23c>
    56f8:	00070e63          	beqz	a4,5714 <.NO_CB223+0x18>

000056fc <.NO_CB223>:
    56fc:	01078793          	addi	a5,a5,16
    5700:	02050513          	addi	a0,a0,32
    5704:	00175713          	srli	a4,a4,0x1
    5708:	00177293          	andi	t0,a4,1
    570c:	fa0294e3          	bnez	t0,56b4 <main+0x23c>
    5710:	fe0716e3          	bnez	a4,56fc <.NO_CB223>
    5714:	0145d803          	lhu	a6,20(a1)
    5718:	0465cf03          	lbu	t5,70(a1)
    571c:	00680833          	add	a6,a6,t1
    5720:	ffff0f13          	addi	t5,t5,-1
    5724:	000a8793          	mv	a5,s5
    5728:	01f00e93          	li	t4,31
    572c:	05df1063          	bne	t5,t4,576c <.NO_CB223+0x70>
    5730:	05c5c703          	lbu	a4,92(a1)
    5734:	84d1c783          	lbu	a5,-1971(gp) # ffb0003d <my_logical_x_>
    5738:	40e787b3          	sub	a5,a5,a4
    573c:	84f181a3          	sb	a5,-1981(gp) # ffb00033 <my_relative_x_>
    5740:	05d5c703          	lbu	a4,93(a1)
    5744:	84c1c783          	lbu	a5,-1972(gp) # ffb0003c <my_logical_y_>
    5748:	40e787b3          	sub	a5,a5,a4
    574c:	84f18123          	sb	a5,-1982(gp) # ffb00032 <my_relative_y_>
    5750:	08000793          	li	a5,128
    5754:	0004c703          	lbu	a4,0(s1)
    5758:	0cf71463          	bne	a4,a5,5820 <.NO_CB223+0x124>
    575c:	006e0e33          	add	t3,t3,t1
    5760:	000e00e7          	jalr	t3
    5764:	00048023          	sb	zero,0(s1)
    5768:	e9dff06f          	j	5604 <main+0x18c>
    576c:	00082683          	lw	a3,0(a6)
    5770:	00482503          	lw	a0,4(a6)
    5774:	0006ac83          	lw	s9,0(a3)
    5778:	0046a383          	lw	t2,4(a3)
    577c:	0086a603          	lw	a2,8(a3)
    5780:	00c6a703          	lw	a4,12(a3)
    5784:	0106af83          	lw	t6,16(a3)
    5788:	0146a283          	lw	t0,20(a3)
    578c:	0186a883          	lw	a7,24(a3)
    5790:	fff50713          	addi	a4,a0,-1
    5794:	01f70733          	add	a4,a4,t6
    5798:	40c70733          	sub	a4,a4,a2
    579c:	02a75733          	divu	a4,a4,a0
    57a0:	02a70733          	mul	a4,a4,a0
    57a4:	00c70733          	add	a4,a4,a2
    57a8:	040c8863          	beqz	s9,57f8 <.NO_CB223+0xfc>
    57ac:	3ed7a023          	sw	a3,992(a5)
    57b0:	3ec7a223          	sw	a2,996(a5)
    57b4:	3ff7a823          	sw	t6,1008(a5)
    57b8:	3e57aa23          	sw	t0,1012(a5)
    57bc:	3f17ac23          	sw	a7,1016(a5)
    57c0:	3e77ae23          	sw	t2,1020(a5)
    57c4:	00c6a883          	lw	a7,12(a3)
    57c8:	011606b3          	add	a3,a2,a7
    57cc:	02a8f8b3          	remu	a7,a7,a0
    57d0:	411686b3          	sub	a3,a3,a7
    57d4:	00d77463          	bgeu	a4,a3,57dc <.NO_CB223+0xe0>
    57d8:	00070613          	mv	a2,a4
    57dc:	3ec7a823          	sw	a2,1008(a5)
    57e0:	3ed7a423          	sw	a3,1000(a5)
    57e4:	3ea7a623          	sw	a0,1004(a5)
    57e8:	00880813          	addi	a6,a6,8
    57ec:	fffe8e93          	addi	t4,t4,-1
    57f0:	fe078793          	addi	a5,a5,-32
    57f4:	f39ff06f          	j	572c <.NO_CB223+0x30>
    57f8:	0002a383          	lw	t2,0(t0)
    57fc:	0042a283          	lw	t0,4(t0)
    5800:	01088893          	addi	a7,a7,16
    5804:	3ed7a023          	sw	a3,992(a5)
    5808:	3ec7a223          	sw	a2,996(a5)
    580c:	3ff7a823          	sw	t6,1008(a5)
    5810:	3f17ae23          	sw	a7,1020(a5)
    5814:	3e77aa23          	sw	t2,1012(a5)
    5818:	3e57ac23          	sw	t0,1016(a5)
    581c:	fa9ff06f          	j	57c4 <.NO_CB223+0xc8>
    5820:	0ff0000f          	fence
    5824:	f31ff06f          	j	5754 <.NO_CB223+0x58>

00005828 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>:
    5828:	00200793          	li	a5,2
    582c:	02c7c063          	blt	a5,a2,584c <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x24>
    5830:	00c05c63          	blez	a2,5848 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x20>
    5834:	0005a703          	lw	a4,0(a1)
    5838:	00e52023          	sw	a4,0(a0)
    583c:	00f61663          	bne	a2,a5,5848 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x20>
    5840:	0045a783          	lw	a5,4(a1)
    5844:	00f52223          	sw	a5,4(a0)
    5848:	00008067          	ret
    584c:	0005a803          	lw	a6,0(a1)
    5850:	0045a683          	lw	a3,4(a1)
    5854:	0085a703          	lw	a4,8(a1)
    5858:	00c58593          	addi	a1,a1,12
    585c:	00c50513          	addi	a0,a0,12
    5860:	ffd60613          	addi	a2,a2,-3
    5864:	ff052a23          	sw	a6,-12(a0)
    5868:	fed52c23          	sw	a3,-8(a0)
    586c:	fee52e23          	sw	a4,-4(a0)
    5870:	fbdff06f          	j	582c <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x4>

00005874 <exit>:
    5874:	0000006f          	j	5874 <exit>
