
/tmp/tt-disasm-dfcgise6/out.elf:     file format elf32-littleriscv


Disassembly of section .text:

00005440 <_start>:
    5440:	ffb001b7          	lui	gp,0xffb00
    5444:	7f018193          	addi	gp,gp,2032 # ffb007f0 <__global_pointer$>
    5448:	ffb02137          	lui	sp,0xffb02
    544c:	ff010113          	addi	sp,sp,-16 # ffb01ff0 <__fw_export_ldm_end+0x1770>
    5450:	00810513          	addi	a0,sp,8
    5454:	00a12023          	sw	a0,0(sp)
    5458:	00012223          	sw	zero,4(sp)
    545c:	00912423          	sw	s1,8(sp)
    5460:	00012623          	sw	zero,12(sp)
    5464:	00100513          	li	a0,1
    5468:	00010593          	mv	a1,sp
    546c:	00000613          	li	a2,0
    5470:	008000ef          	jal	5478 <main>
    5474:	5400006f          	j	59b4 <exit>

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
    54a4:	00200313          	li	t1,2
    54a8:	7c032073          	csrs	0x7c0,t1
    54ac:	00100313          	li	t1,1
    54b0:	01231313          	slli	t1,t1,0x12
    54b4:	0ff0000f          	fence
    54b8:	7c032073          	csrs	0x7c0,t1
    54bc:	00200313          	li	t1,2
    54c0:	7c033073          	csrc	0x7c0,t1
    54c4:	0ff0000f          	fence
    54c8:	0ff0000f          	fence
    54cc:	00800313          	li	t1,8
    54d0:	7c032073          	csrs	0x7c0,t1
    54d4:	ffb007b7          	lui	a5,0xffb00
    54d8:	ffb01737          	lui	a4,0xffb01
    54dc:	01478793          	addi	a5,a5,20 # ffb00014 <noc_nonposted_writes_acked>
    54e0:	87c70713          	addi	a4,a4,-1924 # ffb0087c <__ldm_bss_end>
    54e4:	14f77263          	bgeu	a4,a5,5628 <main+0x1b0>
    54e8:	ff878693          	addi	a3,a5,-8
    54ec:	00d76863          	bltu	a4,a3,54fc <main+0x84>
    54f0:	fe07aa23          	sw	zero,-12(a5)
    54f4:	fe07a823          	sw	zero,-16(a5)
    54f8:	00078693          	mv	a3,a5
    54fc:	ffc68793          	addi	a5,a3,-4
    5500:	00f76463          	bltu	a4,a5,5508 <main+0x90>
    5504:	fe06ac23          	sw	zero,-8(a3)
    5508:	0000a5b7          	lui	a1,0xa
    550c:	81018513          	addi	a0,gp,-2032 # ffb00000 <_ZL10ncrisc_run>
    5510:	6b058593          	addi	a1,a1,1712 # a6b0 <__fw_export_text_end+0x4cf0>
    5514:	00b50c63          	beq	a0,a1,552c <main+0xb4>
    5518:	ffb00637          	lui	a2,0xffb00
    551c:	00460613          	addi	a2,a2,4 # ffb00004 <noc_reads_num_issued>
    5520:	40a60633          	sub	a2,a2,a0
    5524:	40265613          	srai	a2,a2,0x2
    5528:	440000ef          	jal	5968 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    552c:	86818413          	addi	s0,gp,-1944 # ffb00058 <dram_bank_to_noc_xy>
    5530:	000114b7          	lui	s1,0x11
    5534:	6b048593          	addi	a1,s1,1712 # 116b0 <__fw_export_text_end+0xbcf0>
    5538:	00700613          	li	a2,7
    553c:	00040513          	mv	a0,s0
    5540:	428000ef          	jal	5968 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    5544:	00001bb7          	lui	s7,0x1
    5548:	6cc48593          	addi	a1,s1,1740
    554c:	07800613          	li	a2,120
    5550:	01c40513          	addi	a0,s0,28
    5554:	414000ef          	jal	5968 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    5558:	000124b7          	lui	s1,0x12
    555c:	8ac48593          	addi	a1,s1,-1876 # 118ac <__fw_export_text_end+0xbeec>
    5560:	00700613          	li	a2,7
    5564:	1fc40513          	addi	a0,s0,508
    5568:	400000ef          	jal	5968 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    556c:	8c848593          	addi	a1,s1,-1848
    5570:	07800613          	li	a2,120
    5574:	21840513          	addi	a0,s0,536
    5578:	3f0000ef          	jal	5968 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    557c:	eb048593          	addi	a1,s1,-336
    5580:	00500613          	li	a2,5
    5584:	3f840513          	addi	a0,s0,1016
    5588:	3e0000ef          	jal	5968 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    558c:	fffb8993          	addi	s3,s7,-1 # fff <_start-0x4441>
    5590:	00300613          	li	a2,3
    5594:	ec448593          	addi	a1,s1,-316
    5598:	40c40513          	addi	a0,s0,1036
    559c:	3cc000ef          	jal	5968 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    55a0:	ffb124b7          	lui	s1,0xffb12
    55a4:	ffb207b7          	lui	a5,0xffb20
    55a8:	1487a783          	lw	a5,328(a5) # ffb20148 <__stack_top+0x1e148>
    55ac:	03f7f713          	andi	a4,a5,63
    55b0:	0067d793          	srli	a5,a5,0x6
    55b4:	84e18023          	sb	a4,-1984(gp) # ffb00030 <my_x>
    55b8:	03f7f793          	andi	a5,a5,63
    55bc:	82f18e23          	sb	a5,-1988(gp) # ffb0002c <my_y>
    55c0:	ffb307b7          	lui	a5,0xffb30
    55c4:	1487a783          	lw	a5,328(a5) # ffb30148 <__stack_top+0x2e148>
    55c8:	83c18713          	addi	a4,gp,-1988 # ffb0002c <my_y>
    55cc:	03f7f613          	andi	a2,a5,63
    55d0:	0067d793          	srli	a5,a5,0x6
    55d4:	03f7f793          	andi	a5,a5,63
    55d8:	84018693          	addi	a3,gp,-1984 # ffb00030 <my_x>
    55dc:	00c680a3          	sb	a2,1(a3)
    55e0:	00f700a3          	sb	a5,1(a4)
    55e4:	9a0bc703          	lbu	a4,-1632(s7)
    55e8:	82d71b37          	lui	s6,0x82d71
    55ec:	84e186a3          	sb	a4,-1971(gp) # ffb0003d <my_logical_x_>
    55f0:	9a1bc783          	lbu	a5,-1631(s7)
    55f4:	7ffb8b93          	addi	s7,s7,2047
    55f8:	241b8b93          	addi	s7,s7,577
    55fc:	84f18623          	sb	a5,-1972(gp) # ffb0003c <my_logical_y_>
    5600:	8101a903          	lw	s2,-2032(gp) # ffb00000 <_ZL10ncrisc_run>
    5604:	00090023          	sb	zero,0(s2)
    5608:	00094783          	lbu	a5,0(s2)
    560c:	0ff7f713          	zext.b	a4,a5
    5610:	f8078793          	addi	a5,a5,-128
    5614:	02078663          	beqz	a5,5640 <main+0x1c8>
    5618:	fff70793          	addi	a5,a4,-1
    561c:	02078263          	beqz	a5,5640 <main+0x1c8>
    5620:	0ff0000f          	fence
    5624:	fe5ff06f          	j	5608 <main+0x190>
    5628:	fe07ae23          	sw	zero,-4(a5)
    562c:	fe07ac23          	sw	zero,-8(a5)
    5630:	fe07aa23          	sw	zero,-12(a5)
    5634:	fe07a823          	sw	zero,-16(a5)
    5638:	01078793          	addi	a5,a5,16
    563c:	ea9ff06f          	j	54e4 <main+0x6c>
    5640:	22c000ef          	jal	586c <_ZN15kernel_profiler13init_profilerEttt.constprop.0>
    5644:	1f44a783          	lw	a5,500(s1) # ffb121f4 <__stack_top+0x101f4>
    5648:	06000713          	li	a4,96
    564c:	0137f7b3          	and	a5,a5,s3
    5650:	0167e7b3          	or	a5,a5,s6
    5654:	80fba823          	sw	a5,-2032(s7)
    5658:	1f04a783          	lw	a5,496(s1)
    565c:	80fbaa23          	sw	a5,-2028(s7)
    5660:	06c02583          	lw	a1,108(zero) # 6c <_start-0x53d4>
    5664:	06c02783          	lw	a5,108(zero) # 6c <_start-0x53d4>
    5668:	02e585b3          	mul	a1,a1,a4
    566c:	02e787b3          	mul	a5,a5,a4
    5670:	07058593          	addi	a1,a1,112
    5674:	00e787b3          	add	a5,a5,a4
    5678:	0107a303          	lw	t1,16(a5)
    567c:	01c7d703          	lhu	a4,28(a5)
    5680:	0147a683          	lw	a3,20(a5)
    5684:	00670733          	add	a4,a4,t1
    5688:	40e42c23          	sw	a4,1048(s0)
    568c:	01e7d703          	lhu	a4,30(a5)
    5690:	00d70733          	add	a4,a4,a3
    5694:	40e42e23          	sw	a4,1052(s0)
    5698:	0187a683          	lw	a3,24(a5)
    569c:	0207d703          	lhu	a4,32(a5)
    56a0:	00d70733          	add	a4,a4,a3
    56a4:	42e42023          	sw	a4,1056(s0)
    56a8:	02a7d703          	lhu	a4,42(a5)
    56ac:	02c7d783          	lhu	a5,44(a5)
    56b0:	0305ae03          	lw	t3,48(a1)
    56b4:	00670733          	add	a4,a4,t1
    56b8:	006787b3          	add	a5,a5,t1
    56bc:	84e1a423          	sw	a4,-1976(gp) # ffb00038 <rta_l1_base>
    56c0:	84f1a223          	sw	a5,-1980(gp) # ffb00034 <crta_l1_base>
    56c4:	0125d703          	lhu	a4,18(a1)
    56c8:	42440793          	addi	a5,s0,1060
    56cc:	0405a503          	lw	a0,64(a1)
    56d0:	00670733          	add	a4,a4,t1
    56d4:	00078e93          	mv	t4,a5
    56d8:	0580006f          	j	5730 <.NO_CB344+0xc>
    56dc:	00472683          	lw	a3,4(a4)
    56e0:	00072603          	lw	a2,0(a4)
    56e4:	00872803          	lw	a6,8(a4)
    56e8:	00c72883          	lw	a7,12(a4)
    56ec:	00155513          	srli	a0,a0,0x1
    56f0:	00157293          	andi	t0,a0,1
    56f4:	000eac23          	sw	zero,24(t4)
    56f8:	01070713          	addi	a4,a4,16
    56fc:	00dea023          	sw	a3,0(t4)
    5700:	00d606b3          	add	a3,a2,a3
    5704:	00dea223          	sw	a3,4(t4)
    5708:	00ceaa23          	sw	a2,20(t4)
    570c:	010ea623          	sw	a6,12(t4)
    5710:	00cea823          	sw	a2,16(t4)
    5714:	011ea423          	sw	a7,8(t4)
    5718:	020e8e93          	addi	t4,t4,32
    571c:	fc0290e3          	bnez	t0,56dc <main+0x264>
    5720:	00050e63          	beqz	a0,573c <.NO_CB344+0x18>

00005724 <.NO_CB344>:
    5724:	01070713          	addi	a4,a4,16
    5728:	020e8e93          	addi	t4,t4,32
    572c:	00155513          	srli	a0,a0,0x1
    5730:	00157293          	andi	t0,a0,1
    5734:	fa0294e3          	bnez	t0,56dc <main+0x264>
    5738:	fe0516e3          	bnez	a0,5724 <.NO_CB344>
    573c:	0145d803          	lhu	a6,20(a1)
    5740:	0465cf03          	lbu	t5,70(a1)
    5744:	00680833          	add	a6,a6,t1
    5748:	ffff0f13          	addi	t5,t5,-1
    574c:	01f00e93          	li	t4,31
    5750:	07df1063          	bne	t5,t4,57b0 <.NO_CB344+0x8c>
    5754:	05c5c703          	lbu	a4,92(a1)
    5758:	84d1c783          	lbu	a5,-1971(gp) # ffb0003d <my_logical_x_>
    575c:	40e787b3          	sub	a5,a5,a4
    5760:	84f181a3          	sb	a5,-1981(gp) # ffb00033 <my_relative_x_>
    5764:	05d5c703          	lbu	a4,93(a1)
    5768:	84c1c783          	lbu	a5,-1972(gp) # ffb0003c <my_logical_y_>
    576c:	40e787b3          	sub	a5,a5,a4
    5770:	84f18123          	sb	a5,-1982(gp) # ffb00032 <my_relative_y_>
    5774:	08000793          	li	a5,128
    5778:	00094703          	lbu	a4,0(s2)
    577c:	0ef71463          	bne	a4,a5,5864 <.NO_CB344+0x140>
    5780:	006e0e33          	add	t3,t3,t1
    5784:	000e00e7          	jalr	t3
    5788:	00090023          	sb	zero,0(s2)
    578c:	1f44a783          	lw	a5,500(s1)
    5790:	92d71737          	lui	a4,0x92d71
    5794:	0137f7b3          	and	a5,a5,s3
    5798:	00e7e7b3          	or	a5,a5,a4
    579c:	80fbac23          	sw	a5,-2024(s7)
    57a0:	1f04a783          	lw	a5,496(s1)
    57a4:	80fbae23          	sw	a5,-2020(s7)
    57a8:	0ec000ef          	jal	5894 <_ZN15kernel_profiler15finish_profilerEv>
    57ac:	e5dff06f          	j	5608 <main+0x190>
    57b0:	00082683          	lw	a3,0(a6)
    57b4:	00482503          	lw	a0,4(a6)
    57b8:	0006ac03          	lw	s8,0(a3)
    57bc:	0046a383          	lw	t2,4(a3)
    57c0:	0086a603          	lw	a2,8(a3)
    57c4:	00c6a703          	lw	a4,12(a3)
    57c8:	0106af83          	lw	t6,16(a3)
    57cc:	0146a283          	lw	t0,20(a3)
    57d0:	0186a883          	lw	a7,24(a3)
    57d4:	fff50713          	addi	a4,a0,-1
    57d8:	01f70733          	add	a4,a4,t6
    57dc:	40c70733          	sub	a4,a4,a2
    57e0:	02a75733          	divu	a4,a4,a0
    57e4:	02a70733          	mul	a4,a4,a0
    57e8:	00c70733          	add	a4,a4,a2
    57ec:	040c0863          	beqz	s8,583c <.NO_CB344+0x118>
    57f0:	3ed7a023          	sw	a3,992(a5)
    57f4:	3ec7a223          	sw	a2,996(a5)
    57f8:	3ff7a823          	sw	t6,1008(a5)
    57fc:	3e57aa23          	sw	t0,1012(a5)
    5800:	3f17ac23          	sw	a7,1016(a5)
    5804:	3e77ae23          	sw	t2,1020(a5)
    5808:	00c6a883          	lw	a7,12(a3)
    580c:	011606b3          	add	a3,a2,a7
    5810:	02a8f8b3          	remu	a7,a7,a0
    5814:	411686b3          	sub	a3,a3,a7
    5818:	00d77463          	bgeu	a4,a3,5820 <.NO_CB344+0xfc>
    581c:	00070613          	mv	a2,a4
    5820:	3ec7a823          	sw	a2,1008(a5)
    5824:	3ed7a423          	sw	a3,1000(a5)
    5828:	3ea7a623          	sw	a0,1004(a5)
    582c:	00880813          	addi	a6,a6,8
    5830:	fffe8e93          	addi	t4,t4,-1
    5834:	fe078793          	addi	a5,a5,-32
    5838:	f19ff06f          	j	5750 <.NO_CB344+0x2c>
    583c:	0002a383          	lw	t2,0(t0)
    5840:	0042a283          	lw	t0,4(t0)
    5844:	01088893          	addi	a7,a7,16
    5848:	3ed7a023          	sw	a3,992(a5)
    584c:	3ec7a223          	sw	a2,996(a5)
    5850:	3ff7a823          	sw	t6,1008(a5)
    5854:	3f17ae23          	sw	a7,1020(a5)
    5858:	3e77aa23          	sw	t2,1012(a5)
    585c:	3e57ac23          	sw	t0,1016(a5)
    5860:	fa9ff06f          	j	5808 <.NO_CB344+0xe4>
    5864:	0ff0000f          	fence
    5868:	f11ff06f          	j	5778 <.NO_CB344+0x54>

0000586c <_ZN15kernel_profiler13init_profilerEttt.constprop.0>:
    586c:	00c00713          	li	a4,12
    5870:	86e1a223          	sw	a4,-1948(gp) # ffb00054 <_ZN15kernel_profiler6wIndexE>
    5874:	8601a023          	sw	zero,-1952(gp) # ffb00050 <_ZN15kernel_profiler9stackSizeE>
    5878:	85818713          	addi	a4,gp,-1960 # ffb00048 <_ZN15kernel_profiler6sumIDsE>
    587c:	85018793          	addi	a5,gp,-1968 # ffb00040 <_ZN15kernel_profiler4sumsE>
    5880:	00072023          	sw	zero,0(a4) # 92d71000 <__fw_export_text_end+0x92d6b640>
    5884:	0007a023          	sw	zero,0(a5)
    5888:	00072223          	sw	zero,4(a4)
    588c:	0007a223          	sw	zero,4(a5)
    5890:	00008067          	ret

00005894 <_ZN15kernel_profiler15finish_profilerEv>:
    5894:	8641a783          	lw	a5,-1948(gp) # ffb00054 <_ZN15kernel_profiler6wIndexE>
    5898:	00078693          	mv	a3,a5
    589c:	00000593          	li	a1,0
    58a0:	00000713          	li	a4,0
    58a4:	85018813          	addi	a6,gp,-1968 # ffb00040 <_ZN15kernel_profiler4sumsE>
    58a8:	1ff00e93          	li	t4,511
    58ac:	00400e13          	li	t3,4
    58b0:	01058633          	add	a2,a1,a6
    58b4:	00062883          	lw	a7,0(a2)
    58b8:	04088463          	beqz	a7,5900 <_ZN15kernel_profiler15finish_profilerEv+0x6c>
    58bc:	04dee263          	bltu	t4,a3,5900 <_ZN15kernel_profiler15finish_profilerEv+0x6c>
    58c0:	85818713          	addi	a4,gp,-1960 # ffb00048 <_ZN15kernel_profiler6sumIDsE>
    58c4:	00e58733          	add	a4,a1,a4
    58c8:	00072703          	lw	a4,0(a4)
    58cc:	0ffff637          	lui	a2,0xffff
    58d0:	00c71713          	slli	a4,a4,0xc
    58d4:	00c77733          	and	a4,a4,a2
    58d8:	00001337          	lui	t1,0x1
    58dc:	a0000637          	lui	a2,0xa0000
    58e0:	00c76733          	or	a4,a4,a2
    58e4:	a4030613          	addi	a2,t1,-1472 # a40 <_start-0x4a00>
    58e8:	20c6c633          	sh2add	a2,a3,a2
    58ec:	00660633          	add	a2,a2,t1
    58f0:	80e62023          	sw	a4,-2048(a2) # 9ffff800 <__fw_export_text_end+0x9fff9e40>
    58f4:	81162223          	sw	a7,-2044(a2)
    58f8:	00268693          	addi	a3,a3,2
    58fc:	00100713          	li	a4,1
    5900:	05c59063          	bne	a1,t3,5940 <_ZN15kernel_profiler15finish_profilerEv+0xac>
    5904:	00070663          	beqz	a4,5910 <_ZN15kernel_profiler15finish_profilerEv+0x7c>
    5908:	86d1a223          	sw	a3,-1948(gp) # ffb00054 <_ZN15kernel_profiler6wIndexE>
    590c:	00068793          	mv	a5,a3
    5910:	00000713          	li	a4,0
    5914:	00000693          	li	a3,0
    5918:	1ff00593          	li	a1,511
    591c:	00001837          	lui	a6,0x1
    5920:	800008b7          	lui	a7,0x80000
    5924:	0037f613          	andi	a2,a5,3
    5928:	02c6e063          	bltu	a3,a2,5948 <_ZN15kernel_profiler15finish_profilerEv+0xb4>
    592c:	00070463          	beqz	a4,5934 <_ZN15kernel_profiler15finish_profilerEv+0xa0>
    5930:	86f1a223          	sw	a5,-1948(gp) # ffb00054 <_ZN15kernel_profiler6wIndexE>
    5934:	00001737          	lui	a4,0x1
    5938:	9cf72c23          	sw	a5,-1576(a4) # 9d8 <_start-0x4a68>
    593c:	00008067          	ret
    5940:	00400593          	li	a1,4
    5944:	f6dff06f          	j	58b0 <_ZN15kernel_profiler15finish_profilerEv+0x1c>
    5948:	00f5ec63          	bltu	a1,a5,5960 <_ZN15kernel_profiler15finish_profilerEv+0xcc>
    594c:	2107c733          	sh2add	a4,a5,a6
    5950:	25172023          	sw	a7,576(a4)
    5954:	24072223          	sw	zero,580(a4)
    5958:	00278793          	addi	a5,a5,2
    595c:	00100713          	li	a4,1
    5960:	00168693          	addi	a3,a3,1
    5964:	fc1ff06f          	j	5924 <_ZN15kernel_profiler15finish_profilerEv+0x90>

00005968 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>:
    5968:	00200793          	li	a5,2
    596c:	02c7c063          	blt	a5,a2,598c <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x24>
    5970:	00c05c63          	blez	a2,5988 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x20>
    5974:	0005a703          	lw	a4,0(a1)
    5978:	00e52023          	sw	a4,0(a0)
    597c:	00f61663          	bne	a2,a5,5988 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x20>
    5980:	0045a783          	lw	a5,4(a1)
    5984:	00f52223          	sw	a5,4(a0)
    5988:	00008067          	ret
    598c:	0005a803          	lw	a6,0(a1)
    5990:	0045a683          	lw	a3,4(a1)
    5994:	0085a703          	lw	a4,8(a1)
    5998:	00c58593          	addi	a1,a1,12
    599c:	00c50513          	addi	a0,a0,12
    59a0:	ffd60613          	addi	a2,a2,-3
    59a4:	ff052a23          	sw	a6,-12(a0)
    59a8:	fed52c23          	sw	a3,-8(a0)
    59ac:	fee52e23          	sw	a4,-4(a0)
    59b0:	fbdff06f          	j	596c <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x4>

000059b4 <exit>:
    59b4:	0000006f          	j	59b4 <exit>
